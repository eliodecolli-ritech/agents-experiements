#!/usr/bin/env python3
"""
Simplified ETL script that runs without ZenML server
"""

import sys
import os
sys.path.append('..')

def run_employee_etl():
    """Run employee data ETL without ZenML orchestration"""
    print("🔄 Starting Employee Data ETL...")
    
    try:
        # Import the steps directly
        from pipelines.employee_data_etl import download_hr_dataset, clean_employee_data, save_to_mongodb
        
        print("1. Downloading HR dataset...")
        raw_data = download_hr_dataset()
        
        print("2. Cleaning employee data...")
        cleaned_data = clean_employee_data(raw_data)
        
        print("3. Saving to MongoDB...")
        result = save_to_mongodb(cleaned_data)
        
        print(f"✅ ETL Complete: {result}")
        return True
        
    except Exception as e:
        print(f"❌ ETL Failed: {str(e)}")
        return False

def run_feature_engineering():
    """Run feature engineering without ZenML orchestration"""
    print("🔄 Starting Feature Engineering...")
    
    try:
        from pipelines.feature_engineering import (
            query_employee_data, 
            create_searchable_text, 
            embed_employee_data,
            load_to_qdrant
        )
        
        print("1. Querying employee data from MongoDB...")
        employee_data = query_employee_data()
        
        print("2. Creating searchable text...")
        processed_data = create_searchable_text(employee_data)
        
        print("3. Creating embeddings...")
        embedded_data = embed_employee_data(processed_data)
        
        print("4. Loading to Qdrant...")
        result = load_to_qdrant(embedded_data)
        
        print(f"✅ Feature Engineering Complete: {result}")
        return True
        
    except Exception as e:
        print(f"❌ Feature Engineering Failed: {str(e)}")
        return False

def main():
    """Run complete ETL pipeline"""
    print("🚀 Running Complete ETL Pipeline")
    print("=" * 50)
    
    # Run ETL
    etl_success = run_employee_etl()
    if not etl_success:
        return False
    
    print("\n" + "=" * 50)
    
    # Run Feature Engineering
    fe_success = run_feature_engineering()
    if not fe_success:
        return False
    
    print("\n🎉 Complete ETL Pipeline Finished Successfully!")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)