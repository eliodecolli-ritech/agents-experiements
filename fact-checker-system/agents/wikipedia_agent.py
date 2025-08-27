"""
Wikipedia fact-checking agent extracted from fact-check.ipynb
"""

import torch
from transformers import AutoModelForCausalLM, AutoProcessor
import re
import json
from typing import List, Dict, Any, Optional, Tuple
import wikipedia
from dataclasses import dataclass
import os

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
    
    def __init__(self, model_name: str = "google/gemma-3-4b-it"):
        self.model_name = model_name
        self.device = torch.device("mps") if torch.backends.mps.is_available() else torch.device("cpu")
        
        # Authenticate with HuggingFace
        import os
        from dotenv import load_dotenv
        load_dotenv()
        
        hf_token = os.getenv('HUGGINGFACE_TOKEN')
        if not hf_token or hf_token == 'hf_your_token_here':
            print("⚠️  WARNING: Set your HUGGINGFACE_TOKEN in .env file")
            print("   Get token from: https://huggingface.co/settings/tokens")
            print("   Request access: https://huggingface.co/google/gemma-3-4b-it")
        
        # Load Gemma model and processor
        self.model = AutoModelForCausalLM.from_pretrained(
            model_name,
            token=hf_token,
            device_map="auto" if torch.cuda.is_available() else None
        )
        self.processor = AutoProcessor.from_pretrained(model_name, token=hf_token)
        
        if not torch.cuda.is_available():
            self.model.to(self.device)
    
    def generate_initial_input(self, user_prompt: str, system_prompt: str) -> List[Dict[str, Any]]:
        """Generate initial chat input"""
        return [
            {
                "role": "system",
                "content": [{
                    "type": "text",
                    "text": system_prompt,
                }]
            },
            {
                "role": "user", 
                "content": [{
                    "type": "text",
                    "text": user_prompt
                }]
            }
        ]
    
    def generate_followup_input(self, current_chat: List[Dict], agent_response: str, new_prompt: str) -> List[Dict]:
        """Generate follow-up chat input"""
        followup = [
            {
                "role": "model",
                "content": [{
                    "type": "text",
                    "text": agent_response,
                }],
            },
            {
                "role": "user",
                "content": [{
                    "type": "text", 
                    "text": new_prompt,
                }],
            },
        ]
        
        return current_chat + followup
    
    def ask_llm(self, user_prompt: str, current_chat: List[Dict] = None, 
                agent_response: str = None, system_prompt: str = "") -> Tuple[str, List[Dict]]:
        """Ask Gemma model for response"""
        
        if not current_chat:
            prompt = self.generate_initial_input(user_prompt, system_prompt)
        else:
            prompt = self.generate_followup_input(current_chat, agent_response, user_prompt)
        
        inputs = self.processor.apply_chat_template(
            prompt, add_generation_prompt=True, tokenize=True,
            return_dict=True, return_tensors="pt"
        ).to(self.device)
        
        input_len = inputs["input_ids"].shape[-1]
        
        with torch.inference_mode():
            output = self.model.generate(**inputs, max_new_tokens=1024, do_sample=False)
            response = self.processor.decode(output[0][input_len:], skip_special_tokens=True)
            
        return response, prompt

class WikipediaAgent:
    """Wikipedia fact-checking agent"""
    
    def __init__(self, model_name: str = "google/gemma-3-4b-it"):
        self.tools = {}
        self.current_chat = []
        # Configure Wikipedia library
        wikipedia.set_lang("en")
        wikipedia.set_user_agent("WikipediaFactChecker/1.0")
        
        # Initialize LLM
        self.llm = FactCheckLLM(model_name)
        
        # Load system prompt
        self.system_prompt = self._load_system_prompt()
        
        # Initialize tools
        self.initialize()
    
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
        """Wikipedia content downloader tool"""
        def inner_downloader(title: str) -> str:
            try:
                # Get Wikipedia page content
                content = wikipedia.page(title).content
                return content
            except wikipedia.exceptions.DisambiguationError as e:
                # If multiple pages, try the first option
                try:
                    content = wikipedia.page(e.options[0]).content
                    return content
                except:
                    return f"Wikipedia disambiguation error for '{title}'"
            except wikipedia.exceptions.PageError:
                return f"Wikipedia page '{title}' not found"
            except Exception as e:
                return f"Wikipedia error: {str(e)}"
        return inner_downloader
    
    def initialize(self):
        """Initialize agent tools"""
        self.register_tool("wiki_retrieval", self._content_downloader())
    
    def tool_call(self, tool_name: str, **kwargs) -> str:
        """Execute a tool call"""
        print(f"TOOL CALL: {tool_name}, ARGS: {kwargs}")
        
        if tool_name in self.tools:
            result = self.tools[tool_name](**kwargs)
            print(f"TOOL RESULT: {result[:100]}... ({len(result)} chars)")
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
        max_iterations = 10
        iteration = 0
        
        while not (final := self.is_final_result(response)) and iteration < max_iterations:
            iteration += 1
            result = response
            
            # Handle tool calls
            if tool_call := self.is_tool_call(response):
                result = self.tool_call(tool_name=tool_call.name, **tool_call.parameters)
            elif thought := self.is_thought(response):
                print(f"THINK: {thought}")
                result = thought
            
            # Get next response
            response, _chat = self.llm.ask_llm(
                user_prompt=result,
                current_chat=self.current_chat,
                agent_response=response,
                system_prompt=self.system_prompt
            )
            
            print(f"LLM RESPONSE: {response[:200]}...")
            print("-" * 50)
            
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
    result = agent.process_fact_check("Neanderthals used to drive around in EVs")
    
    print("Final Result:")
    print(f"Verdict: {result.verdict}")
    print(f"Confidence: {result.confidence}")
    print(f"Explanation: {result.explanation}")