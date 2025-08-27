# Fine-Tuning Opportunities

## Overview
The LangGraph orchestrator collects rich training data during each fact-check run. Here are the key fine-tuning opportunities:

## 1. Statement Classification (SFT)
**What to fine-tune:** Small classification model (BERT/RoBERTa)
**Training data:** Statement → Classification pairs
**Goal:** Better routing decisions between RAG/Wikipedia agents

```
Input: "Our sales team exceeded targets by 25%"
Output: "private_data"

Input: "Tesla was founded in 2003" 
Output: "public_knowledge"
```

## 2. Evidence Confidence Scoring (SFT)
**What to fine-tune:** Embedding model or classifier
**Training data:** Evidence → Confidence score pairs  
**Goal:** Better evidence reliability assessment

## 3. Verdict Reasoning (SFT/DPO)
**What to fine-tune:** LLM (Llama, Mistral) with LoRA
**Training data:** Statement + Evidence → Verdict + Reasoning
**Goal:** More accurate and consistent fact-checking decisions

**SFT:** Train on correct reasoning patterns
**DPO:** Prefer better reasoning over worse reasoning

## 4. Agent Routing Optimization (RL)
**What to fine-tune:** Routing decision model
**Training data:** Success/failure rates of agent combinations
**Goal:** Optimal agent selection for different statement types

## 5. RAG Query Enhancement (SFT)
**What to fine-tune:** Query rewriting model
**Training data:** Original statement → Optimized RAG query
**Goal:** Better retrieval from company database

## Data Collection Points in LangGraph

The orchestrator automatically collects:
- ✅ Statement classification decisions
- ✅ Agent routing choices  
- ✅ Evidence retrieval results
- ✅ Final verdicts and confidence scores
- ✅ Error cases and retries
- ✅ User feedback (can be added)

## Training Data Export
```python
orchestrator.export_training_data("training_data.json")
```

## Recommended Fine-Tuning Priority

1. **Start with Statement Classification** - Highest ROI, simple SFT
2. **Then Verdict Reasoning** - Core fact-checking quality  
3. **Finally Agent Routing** - Performance optimization

This approach allows iterative improvement while maintaining the flexible LangGraph framework.