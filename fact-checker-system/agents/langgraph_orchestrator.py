from langgraph.graph import StateGraph, END
from langchain_community.llms import HuggingFacePipeline
from typing import Dict, Any
import json
import os
from dotenv import load_dotenv
from google.genai.client import Client
from google.genai.types import (
    ContentDict,
    PartDict,
    GenerateContentConfig
)

from agents.fact_check_state import FactCheckState, Evidence, FactCheckResult
from agents.enhanced_rag_agent import EnhancedRAGAgent
from agents.wikipedia_agent import WikipediaAgent

class LangGraphFactChecker:
    """LangGraph-based fact-checking orchestrator with fine-tuning support"""
    
    def __init__(self, use_openai: bool = False):
        # Option 1: Use Gemini (requires API key, costs money)
        # Option 2: Use simple rules (free, but limited)

        if use_openai:
            # Load environment variables
            load_dotenv()
            gemini_key = os.getenv("GEMINI_API_KEY")
            if not gemini_key:
                raise ValueError("GEMINI_API_KEY not found in environment variables")

            self.gemini_client = Client(api_key=gemini_key)
            self.llm = "gemini"  # Flag to indicate we're using Gemini
            self.wikipedia_agent = WikipediaAgent()
        else:
            # Use simple rule-based classification instead of LLM for now
            self.gemini_client = None
            self.llm = None  # We'll use simple rules
            self.wikipedia_agent = WikipediaAgent()

        self.rag_agent = EnhancedRAGAgent()
        self.use_openai = use_openai
        
        # Fine-tuning data collection
        self.training_data = []
        
        # Build the graph
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow"""
        graph = StateGraph(FactCheckState)
        
        # Add nodes
        graph.add_node("classify_statement", self._classify_statement)
        graph.add_node("route_decision", self._route_decision)
        graph.add_node("rag_search", self._rag_search)
        graph.add_node("wikipedia_search", self._wikipedia_search)
        graph.add_node("llm_analysis", self._llm_analysis)
        graph.add_node("synthesize_result", self._synthesize_result)
        graph.add_node("collect_training_data", self._collect_training_data)
        
        # Set entry point
        graph.set_entry_point("classify_statement")
        
        # Add edges with conditions
        graph.add_edge("classify_statement", "route_decision")
        
        graph.add_conditional_edges(
            "route_decision",
            self._should_use_agents,
            {
                "rag": "rag_search",
                "wikipedia": "wikipedia_search", 
                "both": "rag_search",
                "llm_only": "llm_analysis"
            }
        )
        
        # Add conditional edge from rag_search to decide next step
        graph.add_conditional_edges(
            "rag_search",
            self._after_rag_decision,
            {
                "wikipedia": "wikipedia_search",
                "llm": "llm_analysis"
            }
        )
        
        graph.add_edge("wikipedia_search", "llm_analysis")
        graph.add_edge("llm_analysis", "synthesize_result")
        graph.add_edge("synthesize_result", "collect_training_data")
        graph.add_edge("collect_training_data", END)
        
        return graph.compile()
    
    def _classify_statement(self, state: FactCheckState) -> FactCheckState:
        """Classify the type of statement using rules or LLM"""

        if self.use_openai and self.gemini_client:
            # Use Gemini for classification
            classification_prompt = f"""
            Classify this statement for fact-checking routing:

            Statement: {state["statement"]}

            Classify as one of:
            - 'private_data': About company/employee internal data (e.g., "Our sales team performance", "Company has 200 employees")
            - 'public_knowledge': About general/historical facts (e.g., "Neanderthals used EVs", "Tesla founded in 2003")
            - 'mixed': Requires both private and public data

            Respond with just the classification.
            """

            # Create Gemini request
            contents = [ContentDict(role="user", parts=[PartDict(text=classification_prompt)])]

            response = self.gemini_client.models.generate_content(
                model="gemini-2.0-flash-exp",
                contents=contents,
                config=GenerateContentConfig(temperature=0.1)
            )

            state["statement_type"] = response.text.strip().lower()
        else:
            raise ValueError("No LLM configured")
        
        state["errors"] = []
        state["retry_count"] = 0
        state["collect_for_training"] = True
        
        return state
    
    def _route_decision(self, state: FactCheckState) -> FactCheckState:
        """Make routing decisions based on classification"""
        
        statement_type = state["statement_type"]
        
        if statement_type == "private_data":
            state["should_use_rag"] = True
            state["should_use_wikipedia"] = False
            state["should_use_llm"] = True
        elif statement_type == "public_knowledge":
            state["should_use_rag"] = False
            state["should_use_wikipedia"] = True
            state["should_use_llm"] = True
        elif statement_type == "mixed":
            # Use both agents for mixed statements
            state["should_use_rag"] = True
            state["should_use_wikipedia"] = True
            state["should_use_llm"] = True
        else:
            # Default: use both to be safe
            state["should_use_rag"] = True
            state["should_use_wikipedia"] = True
            state["should_use_llm"] = True
        
        return state
    
    def _should_use_agents(self, state: FactCheckState) -> str:
        """Conditional logic for agent routing"""
        
        if state["should_use_rag"] and state["should_use_wikipedia"]:
            return "both"
        elif state["should_use_rag"]:
            return "rag"
        elif state["should_use_wikipedia"]:
            return "wikipedia"
        else:
            return "llm_only"

    # For "mixed" statements, we do RAG first, then Wikipedia, then analysis.
    def _after_rag_decision(self, state: FactCheckState) -> str:
        """Decide what to do after RAG search"""
        
        if state["should_use_wikipedia"]:
            return "wikipedia"
        else:
            return "llm"
    
    def _rag_search(self, state: FactCheckState) -> FactCheckState:
        """Search private company data using RAG"""
        
        try:
            rag_result = self.rag_agent.fact_check_statement(state["statement"])
            
            evidence = Evidence(
                source="company_database",
                content=json.dumps(rag_result),
                confidence=0.8,  # Could be learned from fine-tuning
                metadata={"agent": "rag", "data_type": "private"}
            )
            
            state["rag_evidence"] = [evidence]
            
        except Exception as e:
            state["errors"].append(f"RAG search failed: {str(e)}")
            state["rag_evidence"] = []
        
        return state
    
    def _wikipedia_search(self, state: FactCheckState) -> FactCheckState:
        """Search Wikipedia for public knowledge using extracted fact-check.ipynb agent"""
        
        try:
            # Use the extracted Wikipedia agent
            wiki_result = self.wikipedia_agent.process_fact_check(state["statement"])
            
            # Convert Wikipedia evidence to our Evidence format
            evidence_list = []
            for wiki_ev in wiki_result.evidence:
                evidence = Evidence(
                    source=f"wikipedia:{wiki_ev.source}",
                    content=wiki_ev.findings,
                    confidence=0.8 if wiki_result.confidence == "High" else 0.6 if wiki_result.confidence == "Medium" else 0.4,
                    metadata={
                        "agent": "wikipedia",
                        "data_type": "public",
                        "verdict": wiki_result.verdict,
                        "investigation_plan": wiki_result.investigation_plan
                    }
                )
                evidence_list.append(evidence)
            
            state["wikipedia_evidence"] = evidence_list
            
        except Exception as e:
            state["errors"].append(f"Wikipedia search failed: {str(e)}")
            state["wikipedia_evidence"] = []
        
        return state
    
    def _llm_analysis(self, state: FactCheckState) -> FactCheckState:
        """Analyze evidence and make verdict (with or without LLM)"""
        
        rag_ev = state.get("rag_evidence", [])
        wiki_ev = state.get("wikipedia_evidence", [])
        
        if self.use_openai and self.gemini_client:
            # Use Gemini for analysis
            analysis_prompt = f"""
            Analyze this statement for fact-checking:

            Statement: {state["statement"]}

            Evidence collected:
            RAG Evidence: {[ev.content for ev in rag_ev] if rag_ev else ["No RAG evidence found"]}
            Wikipedia Evidence: {[ev.content for ev in wiki_ev] if wiki_ev else ["No Wikipedia evidence found"]}

            Provide a verdict (TRUE/FALSE/MISLEADING/UNVERIFIED/NEEDS_CONTEXT) and confidence score (0-1).
            Explain your reasoning based on the evidence.

            IMPORTANT: Respond ONLY with valid JSON in this exact format (no additional text or markdown):
            {{
                "verdict": "TRUE|FALSE|MISLEADING|UNVERIFIED|NEEDS_CONTEXT",
                "confidence": 0.0,
                "reasoning": "your explanation here"
            }}
            """

            # Create Gemini request
            contents = [ContentDict(role="user", parts=[PartDict(text=analysis_prompt)])]

            response = self.gemini_client.models.generate_content(
                model="gemini-2.0-flash-exp",
                contents=contents,
                config=GenerateContentConfig(
                    temperature=0.1,
                    system_instruction="You are a fact-checking AI. Always respond with valid JSON only, no additional text."
                )
            )

            try:
                # Extract JSON from Gemini response (might be wrapped in markdown)
                response_text = response.text.strip()

                # Try to extract JSON from code blocks if present
                if "```json" in response_text:
                    start = response_text.find("```json") + 7
                    end = response_text.find("```", start)
                    if end != -1:
                        response_text = response_text[start:end].strip()
                elif "```" in response_text:
                    start = response_text.find("```") + 3
                    end = response_text.find("```", start)
                    if end != -1:
                        response_text = response_text[start:end].strip()

                # Try to find JSON object in the text
                if "{" in response_text and "}" in response_text:
                    start = response_text.find("{")
                    end = response_text.rfind("}") + 1
                    response_text = response_text[start:end]

                analysis = json.loads(response_text)
                verdict = analysis.get("verdict", "NEEDS_CONTEXT")
                confidence = analysis.get("confidence", 0.5)
                reasoning = analysis.get("reasoning", "Gemini analysis completed")

            except Exception as e:
                print(f"Gemini JSON parsing error: {e}")
                print(f"Raw response: {response.text[:500]}...")
                verdict = "NEEDS_CONTEXT"
                confidence = 0.5
                reasoning = f"Gemini analysis failed (JSON parse error): {str(e)[:100]}"
        else:
            # Simple rule-based analysis
            if rag_ev and wiki_ev:
                verdict = "NEEDS_CONTEXT"
                confidence = 0.7
                reasoning = "Found both company and public data - requires context"
            elif rag_ev:
                verdict = "NEEDS_CONTEXT"
                confidence = 0.6
                reasoning = "Found company data for analysis"
            elif wiki_ev:
                # Check Wikipedia verdict if available
                wiki_verdict = None
                for ev in wiki_ev:
                    if hasattr(ev, 'metadata') and ev.metadata.get('verdict'):
                        wiki_verdict = ev.metadata['verdict']
                        break
                
                if wiki_verdict:
                    verdict = wiki_verdict
                    confidence = 0.7
                    reasoning = f"Wikipedia analysis suggests: {wiki_verdict}"
                else:
                    verdict = "NEEDS_CONTEXT"
                    confidence = 0.5
                    reasoning = "Found Wikipedia data but no clear verdict"
            else:
                verdict = "UNVERIFIED"
                confidence = 0.3
                reasoning = "No relevant evidence found"
        
        # Collect all evidence
        all_evidence = rag_ev + wiki_ev
        
        fact_result = FactCheckResult(
            statement=state["statement"],
            verdict=verdict,
            confidence=confidence,
            evidence=all_evidence,
            reasoning=reasoning,
            agent_used="langgraph_orchestrator"
        )
        
        state["fact_check_result"] = fact_result
        
        return state
    
    def _synthesize_result(self, state: FactCheckState) -> FactCheckState:
        """Final synthesis and validation"""
        
        if not state.get("fact_check_result"):
            # Fallback result
            state["fact_check_result"] = FactCheckResult(
                statement=state["statement"],
                verdict="UNVERIFIED",
                confidence=0.1,
                evidence=[],
                reasoning="Analysis failed due to errors",
                agent_used="langgraph_orchestrator"
            )
        
        return state
    
    def _collect_training_data(self, state: FactCheckState) -> FactCheckState:
        """Collect data for fine-tuning (SFT/DPO)"""
        
        if state["collect_for_training"] and state.get("fact_check_result"):
            training_sample = {
                "statement": state["statement"],
                "statement_type": state["statement_type"],
                "routing_decisions": {
                    "use_rag": state["should_use_rag"],
                    "use_wikipedia": state["should_use_wikipedia"]
                },
                "evidence": [
                    {
                        "source": ev.source,
                        "confidence": ev.confidence,
                        "metadata": ev.metadata
                    } for ev in state["fact_check_result"].evidence
                ],
                "verdict": state["fact_check_result"].verdict,
                "confidence": state["fact_check_result"].confidence,
                "reasoning": state["fact_check_result"].reasoning,
                "errors": state["errors"]
            }
            
            self.training_data.append(training_sample)
            
            state["training_metadata"] = {
                "collected": True,
                "sample_id": len(self.training_data)
            }
        
        return state
    
    def fact_check(self, statement: str) -> FactCheckResult:
        """Main entry point for fact-checking"""
        
        initial_state = FactCheckState(statement=statement)
        final_state = self.graph.invoke(initial_state)
        
        return final_state["fact_check_result"]
    
    def export_training_data(self, filepath: str):
        """Export collected training data for SFT/DPO"""
        with open(filepath, 'w') as f:
            json.dump(self.training_data, f, indent=2)
        
        print(f"Exported {len(self.training_data)} training samples to {filepath}")

# Example usage
if __name__ == "__main__":
    print("🤖 LangGraph Fact-Checker")
    print("=" * 50)
    
    # Choose your setup:
    print("💡 Choose setup:")
    print("1. Local only (free, uses rule-based)")
    print("2. With Gemini (costs money, needs API key)")

    # For now, default to local
    use_openai = True  # Change to True if you want Gemini

    if use_openai:
        print("🌐 Using Gemini 2.0 Flash + lighter local model")
    else:
        print("🏠 Using local models only (rule-based classification)")
    
    orchestrator = LangGraphFactChecker(use_openai=use_openai)
    
    # Test statements  
    statements = [
        "Our company has 200 employees in the sales department",  # Should be private_data
        "Neanderthals used electric vehicles for transportation",  # Should be public_knowledge  
        "Tesla was founded in 2003 and our company partnered with them last year"  # Should be mixed
    ]
    
    for stmt in statements:
        print(f"\n🔍 Testing: {stmt}")
        try:
            result = orchestrator.fact_check(stmt)
            print(f"   Verdict: {result.verdict}")
            print(f"   Confidence: {result.confidence}")
            print(f"   Agent: {result.agent_used}")
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
        print("-" * 50)
    
    # Export training data
    orchestrator.export_training_data("training_data.json")