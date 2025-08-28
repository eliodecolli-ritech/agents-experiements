#!/usr/bin/env python3
"""
Test script to verify Wikipedia agent works with wikipediaapi
"""

import sys
sys.path.append('agents')

def test_wikipedia_library():
    """Test wikipediaapi library directly"""
    print("🧪 Testing wikipediaapi Library")
    print("=" * 50)
    
    try:
        from wikipediaapi import Wikipedia, ExtractFormat
        
        wikipedia = Wikipedia(
            user_agent="WikipediaFactChecker/1.0", 
            language="en", 
            extract_format=ExtractFormat.WIKI
        )
        
        # Test basic functionality
        page = wikipedia.page("Tesla, Inc.")
        
        if page.exists():
            content = page.text[:500]  # First 500 chars
            print(f"✅ Wikipedia page found: Tesla, Inc.")
            print(f"   Content preview: {content}...")
            print(f"   Full length: {len(page.text)} characters")
            return True
        else:
            print("❌ Wikipedia page not found")
            return False
            
    except Exception as e:
        print(f"❌ Wikipedia library error: {str(e)}")
        return False

def test_wikipedia_agent():
    """Test the Wikipedia agent tool"""
    print("\n🤖 Testing Wikipedia Agent")
    print("=" * 50)
    
    try:
        from wikipedia_agent import WikipediaAgent
        
        # Use a smaller model for testing to avoid memory issues
        agent = WikipediaAgent("microsoft/DialoGPT-small")
        
        # Test the tool directly
        tool = agent._content_downloader()
        result = tool("Tesla, Inc.")
        
        if "Wikipedia error" not in result and "not found" not in result:
            print(f"✅ Wikipedia tool working")
            print(f"   Content preview: {result[:200]}...")
            print(f"   Full length: {len(result)} characters")
            return True
        else:
            print(f"❌ Wikipedia tool failed: {result}")
            return False
            
    except Exception as e:
        print(f"❌ Wikipedia agent error: {str(e)}")
        return False

if __name__ == "__main__":
    print("🔍 Testing Wikipedia Integration After Library Switch")
    print("=" * 70)
    
    # Test library first
    lib_success = test_wikipedia_library()
    
    # Test agent if library works
    agent_success = test_wikipedia_agent() if lib_success else False
    
    print("\n" + "=" * 70)
    print("📊 Test Results:")
    print(f"   Wikipedia Library: {'✅ PASS' if lib_success else '❌ FAIL'}")
    print(f"   Wikipedia Agent: {'✅ PASS' if agent_success else '❌ FAIL'}")
    
    if lib_success and agent_success:
        print("\n🎉 SUCCESS: Wikipedia integration is working with wikipediaapi!")
        print("💡 Ready to run: python agents/langgraph_orchestrator.py")
    else:
        print("\n⚠️ ISSUES FOUND: Check the error messages above")
    
    sys.exit(0 if (lib_success and agent_success) else 1)