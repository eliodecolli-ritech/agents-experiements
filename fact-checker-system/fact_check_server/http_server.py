#!/usr/bin/env python3
"""
HTTP Server for Fact-Checking System

A HTTP-based server that exposes the fact-checking functionality
for Spring AI client integration. Provides REST API endpoints
for fact-checking, classification, and status information.
"""

import json
import sys
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import threading
import traceback

# Add parent directory to path to import agents
parent_dir = os.path.join(os.path.dirname(__file__), '..')
sys.path.insert(0, parent_dir)

from agents.langgraph_orchestrator import LangGraphFactChecker
from agents.fact_check_state import FactCheckResult, FactCheckState

class FactCheckHTTPHandler(BaseHTTPRequestHandler):
    """HTTP request handler for fact-checking endpoints"""
    
    def __init__(self, *args, **kwargs):
        # Initialize orchestrator as class variable (shared across requests)
        if not hasattr(FactCheckHTTPHandler, '_orchestrator'):
            FactCheckHTTPHandler._orchestrator = None
        super().__init__(*args, **kwargs)
    
    def _ensure_orchestrator(self, use_openai=True):
        """Lazy initialization of orchestrator"""
        if FactCheckHTTPHandler._orchestrator is None:
            FactCheckHTTPHandler._orchestrator = LangGraphFactChecker(use_openai=use_openai)
            print(f"✅ Initialized LangGraph orchestrator (OpenAI: {use_openai})")
    
    def _send_cors_headers(self):
        """Send CORS headers for cross-origin requests"""
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
    
    def _send_json_response(self, data, status_code=200):
        """Send JSON response with proper headers"""
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self._send_cors_headers()
        self.end_headers()
        
        json_data = json.dumps(data, indent=2)
        self.wfile.write(json_data.encode('utf-8'))
    
    def _send_error_response(self, message, status_code=500):
        """Send error response"""
        error_data = {
            "error": message,
            "status": "error"
        }
        self._send_json_response(error_data, status_code)
    
    def do_OPTIONS(self):
        """Handle CORS preflight requests"""
        self.send_response(200)
        self._send_cors_headers()
        self.end_headers()
    
    def do_GET(self):
        """Handle GET requests"""
        path = urlparse(self.path).path
        
        try:
            if path == '/status':
                self._handle_status()
            elif path == '/evidence-sources':
                self._handle_evidence_sources()
            elif path == '/health':
                self._send_json_response({"status": "healthy", "message": "Server is running"})
            else:
                self._send_error_response("Not found", 404)
                
        except Exception as e:
            print(f"❌ GET error: {str(e)}")
            traceback.print_exc()
            self._send_error_response(f"Server error: {str(e)}")
    
    def do_POST(self):
        """Handle POST requests"""
        path = urlparse(self.path).path
        
        try:
            # Read request body
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length).decode('utf-8')
            
            try:
                request_data = json.loads(post_data) if post_data else {}
            except json.JSONDecodeError:
                self._send_error_response("Invalid JSON in request body", 400)
                return
            
            if path == '/fact-check':
                self._handle_fact_check(request_data)
            elif path == '/classify':
                self._handle_classify(request_data)
            elif path == '/training-data':
                self._handle_training_data(request_data)
            else:
                self._send_error_response("Not found", 404)
                
        except Exception as e:
            print(f"❌ POST error: {str(e)}")
            traceback.print_exc()
            self._send_error_response(f"Server error: {str(e)}")
    
    def _handle_fact_check(self, request_data):
        """Handle fact-checking requests"""
        statement = request_data.get('statement', '').strip()
        use_openai = request_data.get('use_openai', True)
        
        if not statement:
            self._send_error_response("Statement is required", 400)
            return
        
        try:
            self._ensure_orchestrator(use_openai)
            
            # Perform fact-checking
            result: FactCheckResult = FactCheckHTTPHandler._orchestrator.fact_check(statement)
            
            # Format response
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
            
            self._send_json_response(response_data)
            print(f"✅ Fact-check completed: {result.verdict} (confidence: {result.confidence:.2f})")
            
        except Exception as e:
            error_response = {
                "error": f"Fact-checking failed: {str(e)}",
                "statement": statement,
                "verdict": "ERROR",
                "confidence": 0.0
            }
            self._send_json_response(error_response)
    
    def _handle_classify(self, request_data):
        """Handle statement classification requests"""
        statement = request_data.get('statement', '').strip()
        
        if not statement:
            self._send_error_response("Statement is required", 400)
            return
        
        try:
            self._ensure_orchestrator()
            
            # Use orchestrator's classification logic
            initial_state = FactCheckState(statement=statement)
            classified_state = FactCheckHTTPHandler._orchestrator._classify_statement(initial_state)
            
            response_data = {
                "statement": statement,
                "statement_type": classified_state["statement_type"],
                "classification_method": "openai" if FactCheckHTTPHandler._orchestrator.use_openai else "rule_based"
            }
            
            self._send_json_response(response_data)
            print(f"✅ Classification: {classified_state['statement_type']}")
            
        except Exception as e:
            error_response = {
                "error": f"Classification failed: {str(e)}",
                "statement": statement
            }
            self._send_json_response(error_response)
    
    def _handle_training_data(self, request_data):
        """Handle training data retrieval"""
        limit = request_data.get('limit', 10)
        
        try:
            self._ensure_orchestrator()
            
            training_data = FactCheckHTTPHandler._orchestrator.training_data[-limit:] if FactCheckHTTPHandler._orchestrator.training_data else []
            
            response_data = {
                "total_samples": len(FactCheckHTTPHandler._orchestrator.training_data) if FactCheckHTTPHandler._orchestrator.training_data else 0,
                "returned_samples": len(training_data),
                "samples": training_data
            }
            
            self._send_json_response(response_data)
            
        except Exception as e:
            error_response = {
                "error": f"Failed to retrieve training data: {str(e)}"
            }
            self._send_json_response(error_response)
    
    def _handle_status(self):
        """Handle server status requests"""
        status_data = {
            "server": "running",
            "orchestrator_initialized": FactCheckHTTPHandler._orchestrator is not None,
            "openai_enabled": FactCheckHTTPHandler._orchestrator.use_openai if FactCheckHTTPHandler._orchestrator else None,
            "training_samples_collected": len(FactCheckHTTPHandler._orchestrator.training_data) if FactCheckHTTPHandler._orchestrator and FactCheckHTTPHandler._orchestrator.training_data else 0,
            "available_agents": ["rag_agent", "wikipedia_agent", "langgraph_orchestrator"],
            "endpoints": [
                "GET /status",
                "GET /evidence-sources", 
                "GET /health",
                "POST /fact-check",
                "POST /classify",
                "POST /training-data"
            ]
        }
        
        self._send_json_response(status_data)
    
    def _handle_evidence_sources(self):
        """Handle evidence sources requests"""
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
        
        self._send_json_response(sources_data)
    
    def log_message(self, format, *args):
        """Override to reduce logging noise"""
        return  # Suppress default logging

def run_server(host='localhost', port=8001):
    """Run the HTTP server"""
    
    print("🚀 Starting Fact-Checker HTTP Server...")
    print(f"📍 Server will be available at: http://{host}:{port}")
    print("🔧 Available endpoints:")
    print("   POST /fact-check         - Fact-check a statement")
    print("   POST /classify           - Classify statement type")
    print("   POST /training-data      - Get training data")
    print("   GET  /status             - Server status")
    print("   GET  /evidence-sources   - Available evidence sources")
    print("   GET  /health             - Health check")
    print("-" * 60)
    
    server = HTTPServer((host, port), FactCheckHTTPHandler)
    
    try:
        print(f"✅ Server started successfully on http://{host}:{port}")
        print("Press Ctrl+C to stop the server")
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
        server.shutdown()
    except Exception as e:
        print(f"❌ Server error: {str(e)}")
        traceback.print_exc()

if __name__ == "__main__":
    # Get host and port from environment or use defaults
    host = os.getenv("FACTCHECK_HOST", "localhost")
    port = int(os.getenv("FACTCHECK_PORT", "8001"))
    
    run_server(host, port)