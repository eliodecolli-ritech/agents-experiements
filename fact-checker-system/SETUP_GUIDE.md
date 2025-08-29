# Step-by-Step Setup Guide

## 📋 Prerequisites
- Python 3.9+
- Docker & Docker Compose
- OpenAI API key (for LangGraph orchestrator)
- At least 8GB RAM (for Gemma model)

## 🚀 Step 1: Environment Setup

```bash
cd /Users/eltonhoxha/ritech_ai_training/agents-experiements/fact-checker-system

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Mac/Linux

# Install dependencies
pip install -r requirements.txt
```

## 🗄️ Step 2: Start Databases

```bash
# Start MongoDB + Qdrant with Docker
docker-compose up -d

# Verify services are running
docker-compose ps

# Check logs if needed
docker-compose logs mongodb
docker-compose logs qdrant
```

**Expected output:**
- MongoDB: running on port 27017
- Qdrant: running on port 6333  
- Mongo Express: running on port 8081

## 📊 Step 3: Download HR Dataset

1. Go to Kaggle: https://www.kaggle.com/datasets/rhuebner/human-resources-data-set
2. Download `HRDataset_v14.csv`
3. Place it in the `data/` folder:

```bash
mkdir -p data
# Copy your downloaded CSV file here
mv ~/Downloads/HRDataset_v14.csv data/
```

## 🔧 Step 4: Set Environment Variables

```bash
# Copy environment template
cp .env.example .env

# Edit .env file and add your OpenAI API key or HUGGINGFACE_TOKEN
echo "OPENAI_API_KEY=your-key-here" >> .env
echo "HUGGINGFACE_TOKEN=your-key-here" >> .env

```

## 🔄 Step 5: Run ETL Pipeline

### Option A: Simple Commands with ZenML Dashboard (Recommended)
```bash
# Initialize ZenML and start dashboard
export OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES
zenml init --local
zenml up

# Step 1: Run ETL Pipeline (CSV → MongoDB)
python run_etl.py

# Step 2: Run RAG Pipeline (MongoDB → Qdrant)
python run_rag.py

# View pipelines in dashboard
open http://localhost:8237
```

### Option B: With ZenML
```bash
# Initialize ZenML in local mode
export OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES # this is for Mac M1/M2
zenml init --local
zenml up

# Run data pipeline: CSV → MongoDB
python -c "from pipelines.employee_data_etl import employee_data_etl; employee_data_etl()"

# Run feature engineering: MongoDB → Qdrant  
python -c "from pipelines.feature_engineering import feature_engineering; feature_engineering()"
```

**Expected output:**
- ✅ Loaded 311 employee records from data/HRDataset_v14.csv
- ✅ Cleaned data: 311 records with 36 columns
- ✅ Saved 311 records to MongoDB
- ✅ Created searchable text for 311 employees  
- ✅ Created embeddings for 311 employees
- ✅ Loaded 311 employee records to Qdrant

## 🧪 Step 6: Test Individual Components

### Test RAG Agent
```bash
cd agents
python -c "
from rag_agent import RAGAgent
agent = RAGAgent()
result = agent.get_company_stats()
print(result)
"
```

### Test Wikipedia Agent
```bash
python -c "
from wikipedia_agent import WikipediaAgent
agent = WikipediaAgent()
result = agent.process_fact_check('Tesla was founded in 2003')
print(f'Verdict: {result.verdict}')
"
```

## 🎯 Step 7: Test Complete LangGraph System

```bash
python agents/langgraph_orchestrator.py
```

**This will test:**
- "Our company has 200 employees in the sales department" (RAG)
- "Neanderthals used electric vehicles" (Wikipedia)  
- "Tesla was founded in 2003 and our company partnered with them" (Mixed)

## 🔍 Step 8: Verify Results

### Check MongoDB Data
```bash
# Access Mongo Express UI
open http://localhost:8081
# basic auth: admin/pass
# Login: admin/password123
# Database: fact_checker
# Collection: employees
```

### Check Qdrant Data  
```bash
curl http://localhost:6333/collections/employees/points/scroll \
  -H "Content-Type: application/json" \
  -d '{"limit": 5}'
```

### Check Training Data Collection
```bash
# After running tests, check for training data
ls -la *.json
cat training_data.json | head -20
```

## ⚠️ Troubleshooting

### Model Loading Issues
```bash
# If Gemma model fails to load:
# 1. Check available memory
free -h

# 2. Try smaller model
# Edit wikipedia_agent.py, line 38:
# model_name: str = "microsoft/DialoGPT-small"
```

### Database Connection Issues
```bash
# Check Docker services
docker-compose ps
docker-compose logs

# Restart if needed
docker-compose down
docker-compose up -d
```

### ZenML Issues
```bash
# Reset ZenML if needed
zenml clean
zenml init
```

## 🎉 Success Indicators

✅ **Databases running**: MongoDB + Qdrant accessible
✅ **Data loaded**: HR dataset in MongoDB, embeddings in Qdrant  
✅ **RAG working**: Company stats queries return data
✅ **Wikipedia working**: Public fact-checks return verdicts
✅ **LangGraph working**: Orchestrator routes correctly
✅ **Training data**: JSON file with collected samples

## 📝 Next Steps

Once everything is working:
1. Create MCP Server integration
2. Build Spring AI client
3. Add UI for fact-checking
4. Collect more training data
5. Fine-tune models