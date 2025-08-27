from typing import TypedDict, List, Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class Evidence:
    source: str
    content: str
    confidence: float
    metadata: Dict[str, Any]

@dataclass
class FactCheckResult:
    statement: str
    verdict: str  # TRUE/FALSE/MISLEADING/UNVERIFIED/NEEDS_CONTEXT
    confidence: float
    evidence: List[Evidence]
    reasoning: str
    agent_used: str

class FactCheckState(TypedDict):
    """State for the fact-checking agent workflow"""
    
    # Input
    statement: str
    
    # Classification
    statement_type: Optional[str]  # 'private_data', 'public_knowledge', 'mixed'
    
    # Agent routing
    should_use_rag: bool
    should_use_wikipedia: bool
    should_use_llm: bool
    
    # Evidence collection
    rag_evidence: Optional[List[Evidence]]
    wikipedia_evidence: Optional[List[Evidence]]
    
    # Analysis
    fact_check_result: Optional[FactCheckResult]
    
    # Fine-tuning data collection
    collect_for_training: bool
    training_metadata: Optional[Dict[str, Any]]
    
    # Error handling
    errors: List[str]
    retry_count: int