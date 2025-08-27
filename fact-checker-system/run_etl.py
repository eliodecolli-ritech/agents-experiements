#!/usr/bin/env python3
"""
Simple ETL command: CSV → MongoDB
Usage: python run_etl.py
"""

import sys
import os

def run_etl():
    """Run the ETL pipeline: CSV → MongoDB"""
    print("🔄 Starting ETL Pipeline: CSV → MongoDB")
    print("=" * 50)
    
    try:
        # Import the ZenML pipeline
        from pipelines.employee_data_etl import employee_data_etl
        
        print("🔄 Running ZenML ETL Pipeline...")
        print("   This will show up in ZenML dashboard!")
        
        # Run the actual ZenML pipeline
        result = employee_data_etl()
        
        print("\n🎉 ETL Pipeline Complete!")
        print(f"✅ Pipeline run ID: {result}")
        print("💡 Check ZenML dashboard: http://localhost:8237")
        return True
        
    except FileNotFoundError as e:
        print(f"❌ File Error: {str(e)}")
        print("💡 Make sure HRDataset_v14.csv is in the data/ folder")
        return False
        
    except Exception as e:
        print(f"❌ ETL Failed: {str(e)}")
        return False

if __name__ == "__main__":
    success = run_etl()
    if success:
        print("\n🚀 Ready for next step: python run_rag.py")
    sys.exit(0 if success else 1)