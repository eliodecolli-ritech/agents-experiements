#!/usr/bin/env python3
"""
Test script to verify mixed statement routing works correctly
"""

import sys
sys.path.append('agents')

from langgraph_orchestrator import LangGraphFactChecker

def test_mixed_routing():
    """Test that mixed statements collect evidence from both agents"""
    print("🧪 Testing Mixed Statement Routing")
    print("=" * 50)
    
    orchestrator = LangGraphFactChecker(use_openai=False)
    
    # Test mixed statement
    mixed_statement = "Tesla was founded in 2003 and our company partnered with them last year"
    
    print(f"🔍 Testing: {mixed_statement}")
    
    try:
        result = orchestrator.fact_check(mixed_statement)
        
        print(f"\n📊 Results:")
        print(f"   Classification: {result.agent_used}")
        print(f"   Verdict: {result.verdict}")
        print(f"   Confidence: {result.confidence}")
        print(f"   Evidence Sources: {len(result.evidence)}")
        
        # Check evidence sources
        sources = [ev.source for ev in result.evidence]
        has_rag = any("company" in source for source in sources)
        has_wikipedia = any("wikipedia" in source for source in sources)
        
        print(f"\n🔍 Evidence Analysis:")
        print(f"   RAG Evidence: {'✅' if has_rag else '❌'}")
        print(f"   Wikipedia Evidence: {'✅' if has_wikipedia else '❌'}")
        print(f"   Total Evidence: {len(result.evidence)} pieces")
        
        if has_rag and has_wikipedia:
            print("\n🎉 SUCCESS: Mixed statement collected evidence from both agents!")
            return True
        else:
            print(f"\n❌ FAILED: Missing evidence from {'Wikipedia' if not has_wikipedia else 'RAG'}")
            return False
            
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_mixed_routing()
    sys.exit(0 if success else 1)