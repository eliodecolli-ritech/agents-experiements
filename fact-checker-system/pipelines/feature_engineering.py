from zenml import pipeline
from zenml.steps import step
import pandas as pd
import pymongo
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from sentence_transformers import SentenceTransformer
import uuid
from typing import List, Dict, Any

@step
def query_employee_data() -> List[Dict[str, Any]]:
    """Query employee data from MongoDB"""
    import json
    from bson import ObjectId
    
    client = pymongo.MongoClient("mongodb://admin:password123@localhost:27017/?authSource=admin")
    db = client["fact_checker"]
    collection = db["employees"]
    
    # Convert ObjectId to string to make it JSON serializable
    documents = []
    for doc in collection.find({}):
        # Convert ObjectId to string
        doc['_id'] = str(doc['_id'])
        documents.append(doc)
    
    print(f"✅ Retrieved {len(documents)} employee records")
    return documents

@step 
def create_searchable_text(employee_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Create searchable text descriptions for each employee based on actual CSV columns"""
    processed_data = []
    
    for emp in employee_data:
        # Create searchable text combining key fields from actual CSV
        text_parts = []
        
        # Use actual column names from the CSV (after cleaning)
        if 'employee_name' in emp:
            text_parts.append(f"Employee: {emp['employee_name']}")
        if 'department' in emp:
            text_parts.append(f"Department: {emp['department']}")
        if 'position' in emp:
            text_parts.append(f"Position: {emp['position']}")
        if 'performancescore' in emp:
            text_parts.append(f"Performance: {emp['performancescore']}")
        if 'salary' in emp:
            text_parts.append(f"Salary: {emp['salary']}")
        if 'engagementsurvey' in emp:
            text_parts.append(f"Engagement: {emp['engagementsurvey']}")
        if 'employmentstatus' in emp:
            text_parts.append(f"Status: {emp['employmentstatus']}")
        if 'managername' in emp:
            text_parts.append(f"Manager: {emp['managername']}")
        if 'sex' in emp:
            text_parts.append(f"Gender: {emp['sex']}")
        
        searchable_text = ". ".join(text_parts)
        
        processed_data.append({
            **emp,
            'searchable_text': searchable_text
        })
    
    print(f"Created searchable text for {len(processed_data)} employees")
    return processed_data

@step
def embed_employee_data(processed_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Create embeddings for employee data"""
    model = SentenceTransformer('all-MiniLM-L6-v2')
    
    embedded_data = []
    for emp in processed_data:
        embedding = model.encode(emp['searchable_text'])
        
        # Ensure embedding is JSON serializable
        if hasattr(embedding, 'tolist'):
            embedding_list = embedding.tolist()
        else:
            embedding_list = list(embedding)
        
        # Create clean dict without any MongoDB objects
        clean_emp = {}
        for key, value in emp.items():
            if key != '_id':  # Skip MongoDB ObjectId
                clean_emp[key] = value
        
        embedded_data.append({
            **clean_emp,
            'embedding': embedding_list
        })
    
    print(f"✅ Created embeddings for {len(embedded_data)} employees")
    return embedded_data

@step
def load_to_qdrant(embedded_data: List[Dict[str, Any]]) -> str:
    """Load embedded employee data to Qdrant vector database"""
    client = QdrantClient("localhost", port=6333)
    
    collection_name = "employees"
    
    # Recreate collection
    try:
        client.delete_collection(collection_name)
    except:
        pass
    
    client.create_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(size=384, distance=Distance.COSINE)
    )
    
    # Convert to Qdrant points
    points = []
    for i, emp in enumerate(embedded_data):
        point = PointStruct(
            id=str(uuid.uuid4()),
            vector=emp['embedding'],
            payload={k: v for k, v in emp.items() if k != 'embedding'}
        )
        points.append(point)
    
    # Upload to Qdrant
    client.upsert(collection_name=collection_name, points=points)
    
    print(f"Loaded {len(points)} employee records to Qdrant")
    return f"Successfully loaded {len(points)} records to Qdrant"

@pipeline
def feature_engineering(wait_for: str = None) -> str:
    """Feature engineering pipeline: MongoDB -> Embeddings -> Qdrant"""
    employee_data = query_employee_data()
    processed_data = create_searchable_text(employee_data)
    embedded_data = embed_employee_data(processed_data)
    result = load_to_qdrant(embedded_data)
    return result