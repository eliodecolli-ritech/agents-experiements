# Fact-Checker System

A hybrid fact-checking system that routes statements to appropriate verification sources:
- **Private company data**: Uses RAG with MongoDB + Qdrant  
- **Public knowledge**: Uses Wikipedia via existing fact-check.ipynb

## Dataset
**HR Dataset by Dr. Rich Huebner** from Kaggle
- Employee demographics, performance, salaries, departments
- Perfect for statements like "Our sales team has high performance scores"

## Architecture

```
Statement → Orchestrator → Private Data? → RAG Agent (MongoDB/Qdrant)
                      → Public Claim? → Wikipedia Agent (fact-check.ipynb)
```

## Setup

1. **Install dependencies:**
```bash
pip install -r requirements.txt
```

2. **Download HR dataset:**
   - Get HRDataset_v14.csv from Kaggle
   - Place in `data/` folder

3. **Start services:**
```bash
# Start MongoDB + Qdrant with Docker Compose
docker-compose up -d

# Check services are running
docker-compose ps
```

4. **Run ETL pipeline:**
```bash
# ETL: CSV → MongoDB
python -m zenml.cli pipeline run pipelines/employee_data_etl.py

# Feature Engineering: MongoDB → Qdrant  
python -m zenml.cli pipeline run pipelines/feature_engineering.py
```

5. **Test fact checking:**
```bash
python agents/orchestrator.py
```

## Example Statements

**Private (uses RAG):**
- "Our company has 200+ employees"
- "Sales department performance is above average"  
- "Average employee engagement is 4.2"

**Public (uses Wikipedia):**
- "Neanderthals used electric vehicles"
- "Tesla was founded in 2003"

## Next Steps
- [ ] MCP Server integration
- [ ] Spring AI client + UI
- [ ] Integration with existing fact-check.ipynb