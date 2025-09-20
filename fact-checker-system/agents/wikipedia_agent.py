"""
Wikipedia fact-checking agent extracted from fact-check.ipynb
"""

import torch
from transformers import AutoModelForCausalLM, AutoProcessor
import re
import json
from typing import List, Dict, Any, Optional, Tuple
from wikipediaapi import Wikipedia, ExtractFormat
from dataclasses import dataclass
from google.genai.types import (
    ContentDict,
    PartDict,
    GenerateContentConfig
)
from google.genai.client import Client
from utils.ducksearch import DuckSearch

@dataclass(kw_only=True)
class ToolCall:
    name: str | None = None
    parameters: dict | None = None

@dataclass(kw_only=True)
class WikipediaEvidence:
    source: str
    findings: str

@dataclass(kw_only=True)
class WikipediaVerificationResult:
    investigation_plan: str
    claim: str
    verdict: str  # TRUE/FALSE/MISLEADING/UNVERIFIED/NEEDS_CONTEXT
    confidence: str  # High/Medium/Low
    evidence: List[WikipediaEvidence]
    decision_process: str
    explanation: str
    context: str

class FactCheckLLM:
    """Wrapper for LLM model operations - supports multiple models"""
    
    def __init__(self):
        # Authenticate with HuggingFace
        import os
        from dotenv import load_dotenv
        load_dotenv()
        
        gemini_key = os.getenv("GEMINI_API_KEY")
        print(" -> Using Gemini Token:", gemini_key)

        self.client = Client(api_key=gemini_key)
    
    def generate_initial_input(self, user_prompt: str) -> List[ContentDict]:
        """Generate initial chat input"""
        return [
            ContentDict(role="user", parts=[PartDict(text=user_prompt)]),
        ]
    
    def generate_followup_input(self, current_chat: List[ContentDict], agent_response: str, new_prompt: str) -> List[ContentDict]:
        """Generate follow-up chat input"""
        followup = [
            ContentDict(role="model", parts=[PartDict(text=agent_response)]),
            ContentDict(role="user", parts=[PartDict(text=new_prompt)]),
        ]
        
        return current_chat + followup
    
    def ask_llm(self, user_prompt: str, current_chat: List[Dict] = None, 
                agent_response: str = None, system_prompt: str = "") -> Tuple[str, List[ContentDict]]:
        """Ask Gemma model for response"""
        
        if not current_chat:
            prompt = self.generate_initial_input(user_prompt)
        else:
            prompt = self.generate_followup_input(current_chat, agent_response, user_prompt)
        
        llm_resp = self.client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=GenerateContentConfig(system_instruction=system_prompt, temperature=0.2)
        )
        response = llm_resp.text

        return response, prompt

class WikipediaAgent:
    """Wikipedia fact-checking agent"""
    
    def __init__(self):
        self.tools = {}
        self.current_chat = []
        # Configure Wikipedia library (matching original notebook)
        self.wikipedia = Wikipedia(
            user_agent="WikipediaFactChecker/1.0", 
            language="en", 
            extract_format=ExtractFormat.WIKI
        )
        
        # Load system prompt
        self.system_prompt = self._load_system_prompt()
        
        # Initialize tools
        self.initialize()

        self.llm = FactCheckLLM()
    
    def _load_system_prompt(self) -> str:
        """Load system prompt from markdown file"""
        import os
        
        # Get the current file's directory and build relative paths
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_dir)
        
        # Try the improved dynamic prompt first
        dynamic_prompt_path = os.path.join(current_dir, "dynamic_fact_check_prompt.md")
        original_prompt_path = os.path.join(project_root, "..", "fact-checker", "fact-check-prompt.md")
        
        try:
            with open(dynamic_prompt_path, 'r') as f:
                return f.read()
        except FileNotFoundError:
            try:
                with open(original_prompt_path, 'r') as f:
                    return f.read()
            except FileNotFoundError:
                # Fallback system prompt
                return """You are a fact-checking AI. Use Wikipedia to verify claims. 
                Identify relevant Wikipedia topics and search them to verify the claim.
                Respond with structured JSON results containing verdict, confidence, and evidence."""
    
    def register_tool(self, tool_name: str, tool_method):
        """Register a tool for the agent"""
        self.tools[tool_name] = tool_method
    
    def _make_tool_result(self, result: str) -> str:
        """Format tool result"""
        return f"<tool_result>{result}</tool_result>"
    
    def _content_downloader(self):
        """Wikipedia content downloader tool (matching original notebook)"""
        def inner_downloader(title: str) -> str:
            try:
                wiki_page = self.wikipedia.page(title=title)
                if wiki_page.exists():
                    return wiki_page.text
                else:
                    return f"Wikipedia page '{title}' not found"
            except Exception as e:
                return f"Wikipedia error for '{title}': {str(e)}"
        return inner_downloader
    
    def _web_search(self):
        def inner_web_search(query):
            google_search = DuckSearch()
            top = next((item for item in google_search.search(query + " wiki") if "wikipedia" in item["url"]), None)
            if not top:
                return "Nothing found on the web. Try with a different query; formulate the query with the intention to get a wikipedia article from the web search."
            return top["title"]
            

        return inner_web_search
    
    def initialize(self):
        """Initialize agent tools"""
        self.register_tool("wiki_retrieval", self._content_downloader())
        self.register_tool("websearch", self._web_search())
    
    def tool_call(self, tool_name: str, **kwargs) -> str:
        """Execute a tool call"""
        print(f"TOOL CALL: {tool_name}, ARGS: {kwargs}")
        
        if tool_name in self.tools:
            result = self.tools[tool_name](**kwargs)
            print(f"TOOL RESULT: {result[:300]}... ({len(result)} chars)")
            return self._make_tool_result(result)
        
        return self._make_tool_result(f"Tool {tool_name} not found")
    
    def is_final_result(self, response_text: str) -> Optional[WikipediaVerificationResult]:
        """Check if response contains final result"""
        pattern = r'<result>\s*(\{.*?\})\s*</result>'
        
        match = re.search(pattern, response_text, re.DOTALL)
        
        if match:
            json_string = match.group(1)
            try:
                data = json.loads(json_string)
                
                # Parse evidence list
                evidence_list = []
                for evidence_data in data.get('evidence', []):
                    evidence_list.append(WikipediaEvidence(
                        source=evidence_data.get('source', ''),
                        findings=evidence_data.get('findings', '')
                    ))
                
                return WikipediaVerificationResult(
                    investigation_plan=data.get('investigation_plan', ''),
                    claim=data.get('claim', ''),
                    verdict=data.get('verdict', ''),
                    confidence=data.get('confidence', ''),
                    evidence=evidence_list,
                    decision_process=data.get('decision_process', ''),
                    explanation=data.get('explanation', ''),
                    context=data.get('context', '')
                )
            except (json.JSONDecodeError, KeyError, TypeError) as e:
                print(f"Error parsing final result: {e}")
                return None
        
        return None
    
    def is_thought(self, response_text: str) -> Optional[str]:
        """Check if response contains thought"""
        pattern = r'<think>\s*(\{.*?\})\s*</think>'
        
        match = re.search(pattern, response_text, re.DOTALL)
        
        if match:
            return match.group(1)
        
        return None
    
    def is_tool_call(self, response_text: str) -> Optional[ToolCall]:
        """Check if response contains tool call"""
        pattern = r'<tool_call>\s*(\{.*?\})\s*</tool_call>'
        
        match = re.search(pattern, response_text, re.DOTALL)
        
        if match:
            json_string = match.group(1)
            try:
                tool_call_dict = json.loads(json_string)
                return ToolCall(**tool_call_dict)
            except json.JSONDecodeError:
                return None
        
        return None
    
    def process_fact_check(self, statement: str) -> WikipediaVerificationResult:
        """Main fact-checking process"""
        print(f"Processing fact-check for: {statement}")
        
        # Reset state for new fact-check
        self.current_chat = []
        
        # Initial query to LLM
        response, chat = self.llm.ask_llm(
            user_prompt=statement,
            current_chat=self.current_chat,
            system_prompt=self.system_prompt
        )
        self.current_chat = chat
        
        # Process until final result
        max_iterations = 50
        iteration = 0

        if not response:
            print("Got nothing from LLM")
            return
        
        while not (final := self.is_final_result(response)) and iteration < max_iterations:
            iteration += 1
            result = response
            
            # Handle tool calls
            if tool_call := self.is_tool_call(response):
                result = self.tool_call(tool_name=tool_call.name, **tool_call.parameters)
            
            # Get next response
            response, _chat = self.llm.ask_llm(
                user_prompt=result,
                current_chat=self.current_chat,
                agent_response=response,
                system_prompt=self.system_prompt
            )
            
            self.current_chat = _chat
        
        if final:
            return final
        else:
            # Fallback result if max iterations reached
            return WikipediaVerificationResult(
                investigation_plan="Investigation incomplete",
                claim=statement,
                verdict="UNVERIFIED", 
                confidence="Low",
                evidence=[],
                decision_process="Max iterations reached",
                explanation="Could not complete fact-check within iteration limit",
                context=""
            )

# Example usage
if __name__ == "__main__":
    agent = WikipediaAgent()
    result = agent.process_fact_check("Mozart could beat Bethoveen in a fist fight")
    
    print("------------")
    print(f"Verdict: {result.verdict}")
    print(f"Confidence: {result.confidence}")
    print(f"Explanation: {result.context}")