from zenml import pipeline
from zenml.steps import step
import pandas as pd
import pymongo
from typing import Dict, Any

@step
def download_hr_dataset() -> pd.DataFrame:
    """Load HR dataset from CSV file"""
    import os
    
    # Try different possible paths
    possible_paths = [
        "data/HRDataset_v14.csv",
        "../data/HRDataset_v14.csv", 
        "./data/HRDataset_v14.csv"
    ]
    
    df = None
    for path in possible_paths:
        if os.path.exists(path):
            df = pd.read_csv(path)
            print(f"✅ Loaded {len(df)} employee records from {path}")
            break
    
    if df is None:
        raise FileNotFoundError("HR dataset not found. Please ensure HRDataset_v14.csv is in the data/ folder")
    
    return df

@step 
def clean_employee_data(df: pd.DataFrame) -> pd.DataFrame:
    """Clean and standardize employee data based on actual CSV structure"""
    # Remove duplicates
    df = df.drop_duplicates()
    
    # Standardize column names - convert to lowercase and replace spaces
    df.columns = df.columns.str.lower().str.replace(' ', '_').str.replace('/', '_')
    
    # Handle missing values based on actual columns
    if 'performancescore' in df.columns:
        df['performancescore'] = df['performancescore'].fillna('Not Rated')
    
    if 'engagementsurvey' in df.columns:
        df['engagementsurvey'] = df['engagementsurvey'].fillna(0)
    
    # Convert salary to numeric if it exists
    if 'salary' in df.columns:
        df['salary'] = pd.to_numeric(df['salary'], errors='coerce')
    
    # Clean up text fields
    text_columns = ['employee_name', 'department', 'position', 'managername']
    for col in text_columns:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()
    
    print(f"✅ Cleaned data: {len(df)} records with {len(df.columns)} columns")
    print(f"   Key columns: {[col for col in ['employee_name', 'department', 'salary', 'performancescore'] if col in df.columns]}")
    
    return df

@step
def save_to_mongodb(df: pd.DataFrame) -> str:
    """Save cleaned data to MongoDB"""
    # Use authentication for Docker setup
    client = pymongo.MongoClient("mongodb://admin:password123@mongodb:27017/?authSource=admin")
    db = client["fact_checker"]
    collection = db["employees"]
    
    # Convert DataFrame to dict records
    records = df.to_dict('records')
    
    # Clear existing data and insert new
    collection.delete_many({})
    collection.insert_many(records)
    
    print(f"Saved {len(records)} records to MongoDB")
    return f"Inserted {len(records)} employee records"

@pipeline
def employee_data_etl() -> str:
    """ETL pipeline for HR employee dataset"""
    raw_data = download_hr_dataset()
    cleaned_data = clean_employee_data(raw_data)
    result = save_to_mongodb(cleaned_data)
    return result