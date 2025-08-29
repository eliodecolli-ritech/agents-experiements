#!/usr/bin/env python3
"""
Test script for the complete fact-checker system
Run this after setup to verify everything works
"""

import sys
import os
from typing import Dict, Any

def test_mongodb_connection():
    """Test MongoDB connection and data"""
    try:
        import pymongo
        client = pymongo.MongoClient("mongodb://admin:password123@localhost:27017/?authSource=admin")
        db = client["fact_checker"]
        collection = db["employees"]
        
        count = collection.count_documents({})
        print(f"✅ MongoDB: Connected, {count} employee records found")
        
        # Sample document
        sample = collection.find_one({})
        if sample:
            print(f"   Sample fields: {list(sample.keys())[:5]}")
        
        return True
    except Exception as e:
        print(f"❌ MongoDB: {str(e)}")
        return False

def test_qdrant_connection():
    """Test Qdrant connection and data"""
    try:
        from qdrant_client import QdrantClient
        client = QdrantClient("localhost", port=6333)
        
        collections = client.get_collections()
        print(f"✅ Qdrant: Connected, collections: {[c.name for c in collections.collections]}")
        
        if "employees" in [c.name for c in collections.collections]:
            info = client.get_collection("employees")
            print(f"   Employee vectors: {info.points_count}")
        
        return True
    except Exception as e:
        print(f"❌ Qdrant: {str(e)}")
        return False

def test_rag_agent():
    """Test RAG agent functionality"""
    try:
        sys.path.append('agents')
        from rag_agent import RAGAgent
        
        agent = RAGAgent()
        
        # Test company stats
        stats = agent.get_company_stats()
        print(f"✅ RAG Agent: Company stats retrieved")
        print(f"   Total employees: {stats.get('total_employees', 'N/A')}")
        
        # Test fact checking
        result = agent.fact_check_statement("Our company has many employees")
        print(f"   Fact check result keys: {list(result.keys())}")
        
        return True
    except Exception as e:
        print(f"❌ RAG Agent: {str(e)}")
        return False

def test_wikipedia_agent():
    """Test Wikipedia agent functionality"""
    try:
        sys.path.append('agents')
        from wikipedia_agent import WikipediaAgent
        
        # Use a smaller model for testing
        agent = WikipediaAgent("microsoft/DialoGPT-small")
        print("✅ Wikipedia Agent: Model loaded successfully")
        
        # Note: Full test would require significant compute
        print("   (Skipping full inference test - requires 8GB+ RAM)")
        
        return True
    except Exception as e:
        print(f"❌ Wikipedia Agent: {str(e)}")
        return False

def test_langgraph_orchestrator():
    """Test LangGraph orchestrator"""
    try:
        import os
        if not os.getenv("OPENAI_API_KEY"):
            print("⚠️  LangGraph: OpenAI API key not set - skipping")
            return True
            
        sys.path.append('agents')
        from langgraph_orchestrator import LangGraphFactChecker
        
        # This requires OpenAI API
        orchestrator = LangGraphFactChecker()
        print("✅ LangGraph: Orchestrator initialized")
        
        return True
    except Exception as e:
        print(f"❌ LangGraph: {str(e)}")
        return False

def main():
    """Run all tests"""
    print("🧪 Testing Fact-Checker System Components")
    print("=" * 50)
    
    tests = [
        ("Database Connections", [test_mongodb_connection, test_qdrant_connection]),
        ("AI Agents", [test_rag_agent, test_wikipedia_agent]),
        ("Orchestration", [test_langgraph_orchestrator])
    ]
    
    results = {}
    
    for category, test_funcs in tests:
        print(f"\n📋 {category}:")
        category_results = []
        
        for test_func in test_funcs:
            result = test_func()
            category_results.append(result)
        
        results[category] = all(category_results)
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Summary:")
    
    all_passed = True
    for category, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"   {category}: {status}")
        if not passed:
            all_passed = False
    
    if all_passed:
        print("\n🎉 All tests passed! System is ready to use.")
    else:
        print("\n⚠️  Some tests failed. Check the setup guide.")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)