#!/usr/bin/env python3
"""
Simple RAG setup command: MongoDB → Embeddings → Qdrant
Usage: python run_rag.py
"""

import sys
import os

def run_rag():
    """Run the RAG pipeline: MongoDB → Embeddings → Qdrant"""
    print("🔄 Starting RAG Pipeline: MongoDB → Embeddings → Qdrant")
    print("=" * 50)
    
    try:
        # Import the ZenML pipeline
        from pipelines.feature_engineering import feature_engineering
        
        print("🔄 Running ZenML Feature Engineering Pipeline...")
        print("   This will show up in ZenML dashboard!")
        
        # Run the actual ZenML pipeline
        result = feature_engineering()
        
        print("\n🎉 RAG Pipeline Complete!")
        print(f"✅ Pipeline run IDs: {result}")
        print("💡 Check ZenML dashboard: http://localhost:8237")
        return True
        
    except Exception as e:
        print(f"❌ RAG Pipeline Failed: {str(e)}")
        print("\n💡 Troubleshooting:")
        print("   - Make sure MongoDB is running: docker-compose ps")
        print("   - Make sure Qdrant is running: curl http://localhost:6333/collections")
        print("   - Make sure ETL ran first: python run_etl.py")
        return False

if __name__ == "__main__":
    success = run_rag()
    if success:
        print("\n🚀 Ready to test: python test_system.py")
        print("🚀 Or try the agents: python agents/langgraph_orchestrator.py")
    sys.exit(0 if success else 1)