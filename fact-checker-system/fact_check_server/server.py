#!/usr/bin/env python3
"""
MCP Server for Fact-Checking System

Exposes the LangGraph fact-checking orchestrator via Model Context Protocol.
This server wraps the existing fact_check method and makes it accessible
to external clients like Spring AI.
"""

import asyncio
import json
import sys
import os
from typing import Any, Dict, List, Optional

# Add parent directory to path to import agents
parent_dir = os.path.join(os.path.dirname(__file__), '..')
sys.path.insert(0, parent_dir)

try:
    from mcp.server import FastMCP
    from mcp.types import Tool, Resource, TextContent
    from pydantic import AnyUrl
except ImportError:
    print("❌ MCP library not found. Install with: pip install mcp")
    sys.exit(1)

from agents.langgraph_orchestrator import LangGraphFactChecker
from agents.fact_check_state import FactCheckResult, FactCheckState

class FactCheckMCPServer:
    """MCP Server that exposes fact-checking capabilities"""
    
    def __init__(self):
        # Create FastMCP app
        self.app = FastMCP(
            name="Fact-Checker MCP Server",
            instructions="Fact-checking server using LangGraph orchestrator with RAG and Wikipedia agents"
        )
        self.orchestrator = None
        
        # Setup tools and resources
        self._setup_server()
    
    def _setup_server(self):
        """Setup MCP server with tools and resources"""
        
        # Register fact-checking tool
        @self.app.tool()
        def fact_check(statement: str, use_openai: bool = True) -> str:
            """
            Fact-check a statement using RAG (company data) and Wikipedia agents
            
            Args:
                statement: The statement to fact-check
                use_openai: Whether to use OpenAI for analysis (default: True)
            
            Returns:
                JSON string with fact-check results
            """
            try:
                # Ensure orchestrator is initialized
                if self.orchestrator is None:
                    self.orchestrator = LangGraphFactChecker(use_openai=use_openai)
                    print(f"✅ Initialized LangGraph orchestrator (OpenAI: {use_openai})")
                
                # Perform fact-checking using the existing method
                result: FactCheckResult = self.orchestrator.fact_check(statement)
                
                # Format result for MCP response
                response_data = {
                    "statement": result.statement,
                    "verdict": result.verdict,
                    "confidence": result.confidence,
                    "reasoning": result.reasoning,
                    "agent_used": result.agent_used,
                    "evidence": [
                        {
                            "source": ev.source,
                            "content": ev.content[:500] + "..." if len(ev.content) > 500 else ev.content,
                            "confidence": ev.confidence,
                            "metadata": ev.metadata
                        }
                        for ev in result.evidence
                    ],
                    "timestamp": str(getattr(result, 'timestamp', None))
                }
                
                return json.dumps(response_data, indent=2)
                
            except Exception as e:
                error_response = {
                    "error": f"Fact-checking failed: {str(e)}",
                    "statement": statement,
                    "verdict": "ERROR",
                    "confidence": 0.0
                }
                return json.dumps(error_response, indent=2)
        
        # Register classification tool
        @self.app.tool()
        def classify_statement(statement: str) -> str:
            """
            Classify a statement type (private_data, public_knowledge, mixed)
            
            Args:
                statement: The statement to classify
                
            Returns:
                JSON string with classification result
            """
            try:
                if self.orchestrator is None:
                    self.orchestrator = LangGraphFactChecker(use_openai=True)
                
                # Use the orchestrator's classification logic
                initial_state = FactCheckState(statement=statement)
                classified_state = self.orchestrator._classify_statement(initial_state)
                
                response_data = {
                    "statement": statement,
                    "statement_type": classified_state["statement_type"],
                    "classification_method": "openai" if self.orchestrator.use_openai else "rule_based"
                }
                
                return json.dumps(response_data, indent=2)
                
            except Exception as e:
                error_response = {
                    "error": f"Classification failed: {str(e)}",
                    "statement": statement
                }
                return json.dumps(error_response, indent=2)
        
        # Register training data tool
        @self.app.tool()
        def get_training_data(limit: int = 10) -> str:
            """
            Get collected training data for fine-tuning
            
            Args:
                limit: Maximum number of samples to return
                
            Returns:
                JSON string with training data
            """
            try:
                if self.orchestrator is None:
                    self.orchestrator = LangGraphFactChecker(use_openai=True)
                
                training_data = self.orchestrator.training_data[-limit:] if self.orchestrator.training_data else []
                
                response_data = {
                    "total_samples": len(self.orchestrator.training_data) if self.orchestrator.training_data else 0,
                    "returned_samples": len(training_data),
                    "samples": training_data
                }
                
                return json.dumps(response_data, indent=2)
                
            except Exception as e:
                error_response = {
                    "error": f"Failed to retrieve training data: {str(e)}"
                }
                return json.dumps(error_response, indent=2)
        
        # Register server status resource
        @self.app.resource("fact-checker://status")
        def get_server_status() -> str:
            """Get current server status"""
            
            status_data = {
                "server": "running",
                "orchestrator_initialized": self.orchestrator is not None,
                "openai_enabled": self.orchestrator.use_openai if self.orchestrator else None,
                "training_samples_collected": len(self.orchestrator.training_data) if self.orchestrator and self.orchestrator.training_data else 0,
                "available_agents": ["rag_agent", "wikipedia_agent", "langgraph_orchestrator"]
            }
            
            return json.dumps(status_data, indent=2)
        
        # Register evidence sources resource
        @self.app.resource("fact-checker://evidence-sources")
        def get_evidence_sources() -> str:
            """Get available evidence sources"""
            
            sources_data = {
                "rag_database": {
                    "type": "company_data",
                    "description": "MongoDB with employee/company information",
                    "vector_store": "Qdrant"
                },
                "wikipedia": {
                    "type": "public_knowledge", 
                    "description": "Wikipedia search for general facts",
                    "agent": "wikipedia_agent"
                },
                "classification": {
                    "types": ["private_data", "public_knowledge", "mixed"],
                    "method": "rule_based_or_openai"
                }
            }
            
            return json.dumps(sources_data, indent=2)
    
    def run(self, host: str = "localhost", port: int = 8001):
        """Run the MCP server"""
        
        print("🚀 Starting Fact-Checker MCP Server...")
        print(f"📍 Server will be available at: {host}:{port}")
        print("🔧 Available tools: fact_check, classify_statement, get_training_data")
        print("📚 Available resources: fact-checker://status, fact-checker://evidence-sources")
        print("-" * 60)
        
        try:
            # Configure FastMCP for HTTP transport
            self.app.host = host
            self.app.port = port
            
            # Run the FastMCP server with SSE transport for HTTP access
            self.app.run(transport="sse")
        except KeyboardInterrupt:
            print("\n🛑 Server stopped by user")
        except Exception as e:
            print(f"❌ Server error: {str(e)}")

# Main entry point
def main():
    """Main entry point for the MCP server"""
    
    server = FactCheckMCPServer()
    
    # Get host and port from environment or use defaults
    host = os.getenv("MCP_HOST", "localhost")
    port = int(os.getenv("MCP_PORT", "8001"))
    
    server.run(host=host, port=port)

if __name__ == "__main__":
    # Run the server
    main()