#!/usr/bin/env python3
"""
Test script to verify imports work correctly
"""

import sys
import os

# Add current directory to path (same as MCP server does)
sys.path.insert(0, os.getcwd())

try:
    print("🔍 Testing imports...")
    
    # Test basic imports
    from agents.fact_check_state import FactCheckState, Evidence, FactCheckResult
    print("✅ fact_check_state imported successfully")
    
    from agents.rag_agent import RAGAgent
    print("✅ rag_agent imported successfully")
    
    from agents.wikipedia_agent import WikipediaAgent
    print("✅ wikipedia_agent imported successfully")
    
    # Test orchestrator import
    from agents.langgraph_orchestrator import LangGraphFactChecker
    print("✅ langgraph_orchestrator imported successfully")
    
    print("\n🎉 All imports successful!")
    print("✅ MCP server should be able to start now")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("\n🔧 To fix this, please install the required dependencies:")
    print("1. Create and activate virtual environment:")
    print("   python -m venv venv")
    print("   source venv/bin/activate")
    print("2. Install all requirements:")
    print("   pip install -r requirements.txt")
    print("3. Try running this test again")
    print("\nAlternatively, use the startup script which handles this:")
    print("   ./start-mcp-server.sh")
    sys.exit(1)
except Exception as e:
    print(f"❌ Other error: {e}")
    sys.exit(1)