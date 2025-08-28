#!/usr/bin/env python3
"""
Initialize pipelines in Docker environment
Runs ETL and RAG pipelines automatically on container startup
"""

import sys
import os
import time
import pymongo
from qdrant_client import QdrantClient

# Add app directory to path
sys.path.insert(0, '/app')

def wait_for_services():
    """Wait for MongoDB and Qdrant to be ready"""
    print("⏳ Waiting for services to be ready...")
    
    # Wait for MongoDB
    max_retries = 30
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            client = pymongo.MongoClient("mongodb://admin:password123@mongodb:27017/?authSource=admin", serverSelectionTimeoutMS=5000)
            client.admin.command('ping')
            print("✅ MongoDB is ready!")
            break
        except Exception as e:
            retry_count += 1
            print(f"   MongoDB not ready yet ({retry_count}/{max_retries}): {e}")
            time.sleep(2)
    else:
        print("❌ MongoDB failed to start")
        return False
    
    # Wait for Qdrant
    retry_count = 0
    while retry_count < max_retries:
        try:
            qdrant = QdrantClient("qdrant", port=6333, timeout=5)
            qdrant.get_collections()
            print("✅ Qdrant is ready!")
            break
        except Exception as e:
            retry_count += 1
            print(f"   Qdrant not ready yet ({retry_count}/{max_retries}): {e}")
            time.sleep(2)
    else:
        print("❌ Qdrant failed to start")
        return False
    
    return True

def check_data_exists():
    """Check if data already exists"""
    try:
        client = pymongo.MongoClient("mongodb://admin:password123@mongodb:27017/?authSource=admin")
        db = client["fact_checker"]
        collection = db["employees"]
        count = collection.count_documents({})
        
        if count > 0:
            print(f"📊 Found {count} existing employee records")
            return True
        else:
            print("📊 No existing data found")
            return False
    except Exception as e:
        print(f"❌ Error checking data: {e}")
        return False

def run_etl_pipeline():
    """Run ETL pipeline: CSV → MongoDB"""
    print("\n🔄 Running ETL Pipeline (CSV → MongoDB)")
    print("-" * 40)
    
    try:
        # Check if HR dataset exists
        dataset_path = "/app/data/HRDataset_v14.csv"
        if not os.path.exists(dataset_path):
            print("⚠️  HR dataset not found at /app/data/HRDataset_v14.csv")
            print("💡 Please mount the dataset or add it to the image")
            return False
        
        # Import and run ETL
        os.environ['OBJC_DISABLE_INITIALIZE_FORK_SAFETY'] = 'YES'
        
        from pipelines.employee_data_etl import employee_data_etl
        
        print("🚀 Starting ETL pipeline...")
        result = employee_data_etl()
        print(f"✅ ETL Pipeline completed: {result}")
        return True
        
    except Exception as e:
        print(f"❌ ETL Pipeline failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def run_rag_pipeline():
    """Run RAG pipeline: MongoDB → Qdrant"""
    print("\n🔄 Running RAG Pipeline (MongoDB → Qdrant)")
    print("-" * 40)
    
    try:
        from pipelines.feature_engineering import feature_engineering
        
        print("🚀 Starting RAG pipeline...")
        result = feature_engineering()
        print(f"✅ RAG Pipeline completed: {result}")
        return True
        
    except Exception as e:
        print(f"❌ RAG Pipeline failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def initialize_zenml():
    """Initialize ZenML for pipeline tracking"""
    try:
        print("🔧 Initializing ZenML...")
        import subprocess
        
        # Initialize ZenML
        print("   Running: zenml init")
        result = subprocess.run('zenml init', shell=True, capture_output=True, text=True, cwd='/app')
        if result.returncode == 0:
            print("✅ ZenML initialized successfully")
        else:
            print(f"⚠️  ZenML init output: {result.stderr}")
        
        # Start ZenML server (bind to 0.0.0.0 for Docker access)
        print("   Running: zenml up --port 8237")
        result = subprocess.run('zenml up --port 8237 --ip-address 0.0.0.0', shell=True, capture_output=True, text=True, cwd='/app')
        if result.returncode == 0:
            print("✅ ZenML dashboard started successfully")
            print("📊 Dashboard available at: http://localhost:8237")
        else:
            print(f"⚠️  ZenML up output: {result.stderr}")
            print("💡 Dashboard may already be running")
        
        # Give ZenML a moment to start up
        import time
        time.sleep(2)
        
        return True
    except Exception as e:
        print(f"⚠️  ZenML initialization failed: {e}")
        print("💡 Continuing without dashboard - pipelines will still run")
        return False

def main():
    """Main initialization process"""
    print("🚀 Initializing Fact-Checker System")
    print("=" * 50)
    
    # Wait for ZenML server and configure connection
    print("🔗 Waiting for ZenML server...")
    zenml_ready = False
    max_retries = 30
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            import requests
            response = requests.get('http://zenml-server:8237/api/v1/info', timeout=5)
            if response.status_code == 200:
                print("✅ ZenML server is ready!")
                zenml_ready = True
                break
        except Exception:
            pass
        
        retry_count += 1
        time.sleep(2)
        if retry_count % 5 == 0:
            print(f"   Still waiting for ZenML server... ({retry_count}/{max_retries})")
    
    if not zenml_ready:
        print("⚠️  ZenML server not ready, pipelines will run locally")
    else:
        # Configure ZenML to use the server
        try:
            import os
            os.environ['ZENML_CONFIG_PATH'] = '/app/.zenml'
            # Configure ZenML client to connect to server
            import subprocess
            result = subprocess.run('zenml login --local', shell=True, capture_output=True, text=True, cwd='/app')
            print("✅ ZenML configured for pipeline tracking")
        except Exception as e:
            print(f"⚠️  ZenML configuration warning: {e}")
            print("💡 Pipelines will still run")
    
    # Wait for services
    if not wait_for_services():
        sys.exit(1)
    
    # Check if data already exists or if force flag is set
    force_run = os.getenv('FORCE_PIPELINE_RUN', 'false').lower() == 'true'
    
    if check_data_exists() and not force_run:
        print("✅ Data already exists, skipping pipeline execution")
        print("💡 To force re-run, set FORCE_PIPELINE_RUN=true or delete MongoDB data volume")
    else:
        if force_run:
            print("🔄 Force re-run enabled, executing pipelines...")
        else:
            print("📊 No existing data found, running fresh pipelines...")
        # Run ETL pipeline
        if not run_etl_pipeline():
            print("❌ ETL pipeline failed, aborting")
            sys.exit(1)
        
        # Run RAG pipeline
        if not run_rag_pipeline():
            print("❌ RAG pipeline failed, aborting")  
            sys.exit(1)
    
    print("\n🎉 Pipeline initialization completed successfully!")
    print("🌐 System is ready for fact-checking")
    print("📍 Web UI will be available at: http://localhost:8080")

if __name__ == "__main__":
    main()