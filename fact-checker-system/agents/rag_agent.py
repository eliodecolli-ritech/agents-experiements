import pymongo
from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any
import statistics

class RAGAgent:
    """Agent for fact-checking using private employee/company data"""
    
    def __init__(self):
        self.mongo_client = pymongo.MongoClient("mongodb://admin:password123@localhost:27017/?authSource=admin")
        self.qdrant_client = QdrantClient("localhost", port=6333)
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        self.db = self.mongo_client["fact_checker"]
    
    def search_similar_employees(self, query: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """Search for employees similar to query using vector search"""
        query_embedding = self.embedding_model.encode(query)
        
        search_result = self.qdrant_client.search(
            collection_name="employees",
            query_vector=query_embedding,
            limit=top_k
        )
        
        return [hit.payload for hit in search_result]
    
    def get_department_stats(self, department: str) -> Dict[str, Any]:
        """Get statistics for a specific department"""
        collection = self.db["employees"] 
        
        # Find employees in department
        employees = list(collection.find({"department": {"$regex": department, "$options": "i"}}))
        
        if not employees:
            return {"error": f"No employees found in {department} department"}
        
        stats = {
            "total_employees": len(employees),
            "department": department,
        }
        
        # Performance scores
        perf_scores = [emp.get('performance_score', 0) for emp in employees if emp.get('performance_score')]
        if perf_scores:
            stats["avg_performance"] = statistics.mean(perf_scores) if all(isinstance(x, (int, float)) for x in perf_scores) else "Mixed ratings"
        
        # Engagement scores  
        engagement_scores = [emp.get('engagement_score', 0) for emp in employees if isinstance(emp.get('engagement_score'), (int, float))]
        if engagement_scores:
            stats["avg_engagement"] = statistics.mean(engagement_scores)
        
        # Salaries
        salaries = [emp.get('salary', 0) for emp in employees if isinstance(emp.get('salary'), (int, float))]
        if salaries:
            stats["avg_salary"] = statistics.mean(salaries)
            
        return stats
    
    def get_company_stats(self) -> Dict[str, Any]:
        """Get overall company statistics"""
        collection = self.db["employees"]
        
        total_employees = collection.count_documents({})
        
        # Gender distribution
        pipeline = [
            {"$group": {"_id": "$gender", "count": {"$sum": 1}}}
        ]
        gender_stats = list(collection.aggregate(pipeline))
        
        # Department distribution
        pipeline = [
            {"$group": {"_id": "$department", "count": {"$sum": 1}}}
        ]
        dept_stats = list(collection.aggregate(pipeline))
        
        # Average age
        pipeline = [
            {"$group": {"_id": None, "avg_age": {"$avg": "$age"}}}
        ]
        age_result = list(collection.aggregate(pipeline))
        avg_age = age_result[0]["avg_age"] if age_result else None
        
        return {
            "total_employees": total_employees,
            "gender_distribution": {item["_id"]: item["count"] for item in gender_stats},
            "department_distribution": {item["_id"]: item["count"] for item in dept_stats},
            "average_age": round(avg_age, 1) if avg_age else None
        }
    
    def fact_check_statement(self, statement: str) -> Dict[str, Any]:
        """Fact-check a statement about company/employee data"""
        statement_lower = statement.lower()
        
        # Route to appropriate analysis
        if "department" in statement_lower:
            # Extract department name (simple approach)
            words = statement.split()
            dept_word = None
            for i, word in enumerate(words):
                if word.lower() == "department" and i > 0:
                    dept_word = words[i-1]
                    break
            
            if dept_word:
                return self.get_department_stats(dept_word)
        
        # For general company statements
        if any(keyword in statement_lower for keyword in ["company", "employees", "workforce", "average"]):
            return self.get_company_stats()
        
        # Fallback: semantic search
        similar_data = self.search_similar_employees(statement, top_k=5)
        return {
            "search_results": similar_data,
            "analysis": "Found similar employee records for analysis"
        }