import pymongo
from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any, Tuple, Optional
import statistics
import re

class EnhancedRAGAgent:
    """Enhanced RAG Agent for fact-checking specific numerical and demographic claims"""
    
    def __init__(self):
        self.mongo_client = pymongo.MongoClient("mongodb://admin:password123@mongodb:27017/?authSource=admin")
        self.qdrant_client = QdrantClient("qdrant", port=6333)
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        self.db = self.mongo_client["fact_checker"]
    
    def get_gender_distribution(self, department: Optional[str] = None) -> Dict[str, Any]:
        """Get gender distribution for company or specific department"""
        collection = self.db["employees"]
        
        # Build query filter
        filter_query = {}
        if department:
            filter_query = {"department": {"$regex": department, "$options": "i"}}
        
        # Get gender distribution (using 'sex' field from CSV)
        pipeline = [
            {"$match": filter_query},
            {"$group": {"_id": "$sex", "count": {"$sum": 1}}}
        ]
        gender_stats = list(collection.aggregate(pipeline))
        
        # Convert to readable format
        gender_counts = {}
        for stat in gender_stats:
            gender = stat["_id"]
            count = stat["count"]
            if gender == "M":
                gender_counts["male"] = count
                gender_counts["males"] = count
            elif gender == "F":
                gender_counts["female"] = count  
                gender_counts["females"] = count
            elif gender:  # Handle any other values
                gender_counts[gender.lower()] = count
        
        total = sum(gender_counts.values())
        
        result = {
            "scope": f"{department} department" if department else "company",
            "total_employees": total,
            "gender_counts": gender_counts,
            "gender_percentages": {k: round((v/total)*100, 1) if total > 0 else 0 for k, v in gender_counts.items()}
        }
        
        # Add comparison info
        male_count = gender_counts.get("male", 0)
        female_count = gender_counts.get("female", 0)
        
        result["more_males_than_females"] = male_count > female_count
        result["more_females_than_males"] = female_count > male_count
        result["gender_ratio"] = f"{male_count}M:{female_count}F"
        
        return result
    
    def get_salary_stats(self, department: Optional[str] = None, gender: Optional[str] = None) -> Dict[str, Any]:
        """Get salary statistics with optional filters"""
        collection = self.db["employees"]
        
        # Build query filter
        filter_query = {}
        if department:
            filter_query["department"] = {"$regex": department, "$options": "i"}
        if gender:
            # Map gender terms to database values
            if gender.lower() in ["male", "males", "m"]:
                filter_query["sex"] = "M"
            elif gender.lower() in ["female", "females", "f"]:
                filter_query["sex"] = "F"
        
        # Get salary data
        employees = list(collection.find(filter_query))
        
        # Extract valid salaries
        salaries = []
        for emp in employees:
            salary = emp.get("salary")
            if salary and isinstance(salary, (int, float)) and salary > 0:
                salaries.append(salary)
        
        if not salaries:
            return {
                "error": f"No salary data found",
                "scope": f"{department} department" if department else "company",
                "filter": f"{gender}" if gender else "all employees"
            }
        
        avg_salary = statistics.mean(salaries)
        median_salary = statistics.median(salaries)
        
        return {
            "scope": f"{department} department" if department else "company",
            "filter": f"{gender} employees" if gender else "all employees",
            "employee_count": len(salaries),
            "average_salary": round(avg_salary, 2),
            "median_salary": round(median_salary, 2),
            "min_salary": min(salaries),
            "max_salary": max(salaries),
            "salary_range": f"${min(salaries):,} - ${max(salaries):,}",
            "avg_salary_formatted": f"${avg_salary:,.2f}"
        }
    
    def get_department_stats(self, department: str) -> Dict[str, Any]:
        """Get comprehensive department statistics"""
        collection = self.db["employees"]
        
        employees = list(collection.find({"department": {"$regex": department, "$options": "i"}}))
        
        if not employees:
            return {"error": f"No employees found in {department} department"}
        
        # Basic stats
        stats = {
            "department": department,
            "total_employees": len(employees),
        }
        
        # Gender distribution
        gender_dist = self.get_gender_distribution(department)
        stats.update(gender_dist)
        
        # Salary stats
        salary_stats = self.get_salary_stats(department)
        if "error" not in salary_stats:
            stats["salary_info"] = salary_stats
        
        # Performance scores
        perf_scores = []
        for emp in employees:
            perf = emp.get('performancescore')
            if perf and isinstance(perf, str) and perf != 'Not Rated':
                perf_scores.append(perf)
        
        if perf_scores:
            stats["performance_ratings"] = {
                "total_rated": len(perf_scores),
                "ratings": dict(collections.Counter(perf_scores))
            }
        
        return stats
    
    def extract_numerical_claim(self, statement: str) -> Optional[Tuple[str, float]]:
        """Extract numerical claims from statements"""
        patterns = [
            # "average salary is $50000" or "average salary is 50000"
            (r'average salary is \$?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)', 'average_salary'),
            # "more than 100 employees"
            (r'more than (\d+) employees?', 'employee_count_more'),
            # "less than 200 employees"  
            (r'(?:less|fewer) than (\d+) employees?', 'employee_count_less'),
            # "exactly 311 employees"
            (r'exactly (\d+) employees?', 'employee_count_exact'),
            # "has 200 employees"
            (r'has (\d+) employees?', 'employee_count_exact'),
            # "over $60000 average salary"
            (r'over \$(\d{1,3}(?:,\d{3})*(?:\.\d{2})?) average salary', 'average_salary_more'),
        ]
        
        statement_lower = statement.lower().replace(',', '')
        
        for pattern, claim_type in patterns:
            match = re.search(pattern, statement_lower)
            if match:
                try:
                    number = float(match.group(1).replace(',', ''))
                    return claim_type, number
                except:
                    continue
        
        return None
    
    def extract_department(self, statement: str) -> Optional[str]:
        """Extract department name from statement"""
        statement_lower = statement.lower()
        
        # Common department names in the dataset
        departments = [
            'production', 'it', 'information technology', 'sales', 'marketing', 
            'hr', 'human resources', 'finance', 'engineering', 'admin', 
            'administration', 'software engineering'
        ]
        
        for dept in departments:
            if dept in statement_lower:
                return dept
        
        # Try to extract from "X department" pattern
        words = statement.split()
        for i, word in enumerate(words):
            if word.lower() == "department" and i > 0:
                return words[i-1].lower()
        
        return None
    
    def fact_check_statement(self, statement: str) -> Dict[str, Any]:
        """Main fact-checking method with enhanced claim verification"""
        statement_lower = statement.lower()
        
        # Extract components
        department = self.extract_department(statement)
        numerical_claim = self.extract_numerical_claim(statement)
        
        result = {
            "statement": statement,
            "analysis_type": "unknown",
            "department": department,
            "numerical_claim": numerical_claim
        }
        
        # 1. Handle gender comparison claims
        if any(phrase in statement_lower for phrase in ["more males than females", "more females than males", "mostly male", "mostly female"]):
            gender_data = self.get_gender_distribution(department)
            result["analysis_type"] = "gender_comparison"
            result["data"] = gender_data
            
            if "more males than females" in statement_lower:
                result["claim_verified"] = gender_data.get("more_males_than_females", False)
                result["verification_details"] = f"Males: {gender_data['gender_counts'].get('male', 0)}, Females: {gender_data['gender_counts'].get('female', 0)}"
            elif "more females than males" in statement_lower:
                result["claim_verified"] = gender_data.get("more_females_than_males", False)
                result["verification_details"] = f"Females: {gender_data['gender_counts'].get('female', 0)}, Males: {gender_data['gender_counts'].get('male', 0)}"
            
            return result
        
        # 2. Handle salary claims
        if numerical_claim and "salary" in numerical_claim[0]:
            salary_data = self.get_salary_stats(department)
            result["analysis_type"] = "salary_verification"
            result["data"] = salary_data
            
            if "error" not in salary_data:
                claim_type, claimed_value = numerical_claim
                actual_avg = salary_data["average_salary"]
                
                if claim_type == "average_salary":
                    tolerance = 1000  # $1000 tolerance
                    result["claim_verified"] = abs(actual_avg - claimed_value) <= tolerance
                    result["verification_details"] = f"Claimed: ${claimed_value:,.2f}, Actual: ${actual_avg:,.2f}"
                elif claim_type == "average_salary_more":
                    result["claim_verified"] = actual_avg > claimed_value
                    result["verification_details"] = f"Claimed > ${claimed_value:,.2f}, Actual: ${actual_avg:,.2f}"
            
            return result
        
        # 3. Handle employee count claims
        if numerical_claim and "employee_count" in numerical_claim[0]:
            if department:
                stats = self.get_department_stats(department)
                actual_count = stats.get("total_employees", 0)
            else:
                collection = self.db["employees"]
                actual_count = collection.count_documents({})
            
            result["analysis_type"] = "employee_count_verification"
            result["data"] = {"actual_employee_count": actual_count}
            
            claim_type, claimed_count = numerical_claim
            
            if claim_type == "employee_count_exact":
                result["claim_verified"] = actual_count == claimed_count
                result["verification_details"] = f"Claimed: {claimed_count}, Actual: {actual_count}"
            elif claim_type == "employee_count_more":
                result["claim_verified"] = actual_count > claimed_count
                result["verification_details"] = f"Claimed > {claimed_count}, Actual: {actual_count}"
            elif claim_type == "employee_count_less":
                result["claim_verified"] = actual_count < claimed_count
                result["verification_details"] = f"Claimed < {claimed_count}, Actual: {actual_count}"
            
            return result
        
        # 4. General department analysis
        if department and not numerical_claim:
            result["analysis_type"] = "department_overview"
            result["data"] = self.get_department_stats(department)
            result["claim_verified"] = "error" not in result["data"]
            return result
        
        # 5. General company statistics
        if any(keyword in statement_lower for keyword in ["company", "workforce", "organization"]):
            collection = self.db["employees"]
            total_employees = collection.count_documents({})
            gender_data = self.get_gender_distribution()
            salary_data = self.get_salary_stats()
            
            result["analysis_type"] = "company_overview"
            result["data"] = {
                "total_employees": total_employees,
                "gender_distribution": gender_data,
                "salary_stats": salary_data
            }
            result["claim_verified"] = True
            return result
        
        # 6. Fallback: semantic search
        similar_data = self.search_similar_employees(statement, top_k=5)
        result["analysis_type"] = "semantic_search"
        result["data"] = {
            "search_results": similar_data,
            "analysis": "Found similar employee records but no specific claim to verify"
        }
        
        return result
    
    def search_similar_employees(self, query: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """Search for employees similar to query using vector search"""
        try:
            query_embedding = self.embedding_model.encode(query)
            
            search_result = self.qdrant_client.search(
                collection_name="employees",
                query_vector=query_embedding,
                limit=top_k
            )
            
            return [hit.payload for hit in search_result]
        except Exception as e:
            return [{"error": f"Vector search failed: {str(e)}"}]

# Import collections for Counter
import collections