# 🔍 Fact-Checker System

A comprehensive AI-powered fact-checking system with hybrid verification using company data (RAG) and public knowledge (Wikipedia). Built with Python, LangGraph orchestration, and Spring AI web interface.

## ✨ Features

- 🎯 **Precise Claim Verification**: Verify specific numerical and demographic claims
- 👥 **Gender Analysis**: "Our company has more females than males"
- 💰 **Salary Verification**: "Average salary is $70,000" 
- 📊 **Employee Count Claims**: "IT department has 45 employees"
- 🏢 **Department Analysis**: Cross-department comparisons
- 🌐 **Modern Web UI**: Responsive interface with real-time classification
- 🔄 **Hybrid Intelligence**: RAG for private data + Wikipedia for public facts

## 🚀 Quick Start (Docker - Recommended)

### Prerequisites
- Docker & Docker Compose
- HR Dataset (see below)

### 1. Get the Data
Download the HR dataset from [Kaggle](https://www.kaggle.com/datasets/rhuebner/human-resources-data-set):
```bash
# Place HRDataset_v14.csv in:
fact-checker-system/data/HRDataset_v14.csv
```

### 2. Start Everything
```bash
# Option 1: Full guided setup
./start-docker.sh

# Option 2: Quick one-liner
./quick-start.sh

# Option 3: Manual Docker Compose
docker-compose up -d
docker-compose run --rm pipeline-init
```

### 3. Access the System
- **🌐 Web UI**: http://localhost:8080
- **🔧 API**: http://localhost:8001  
- **📊 Database**: http://localhost:8081 (admin/password123)

## 🎯 Test Statements

Try these fact-checkable claims:

### Gender Analysis
```
"Our company has more females than males"
"Production department is mostly male"
"IT department has equal gender representation"
```

### Salary Verification  
```
"Our company average salary is $70,000"
"Production department average salary exceeds $65,000"
"IT team salaries are under $80,000"
```

### Employee Counts
```
"Our company has exactly 311 employees"  
"Sales department has more than 50 employees"
"HR department has less than 30 people"
```

## 🛠️ Manual Setup (Developers)

### Prerequisites
- Python 3.9+
- Java 17+
- Docker (for databases)
- Maven

### 1. Infrastructure
```bash
cd fact-checker-system
docker-compose up -d mongodb qdrant mongo-express
```

### 2. Python Environment
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\\Scripts\\activate
pip install -r requirements.txt
```

### 3. Data Pipeline
```bash
python run_etl.py    # CSV → MongoDB
python run_rag.py    # MongoDB → Qdrant (embeddings)
```

### 4. Start Services
```bash
# Terminal 1: Python HTTP Server
./start-http-server.sh

# Terminal 2: Spring Web UI
cd ../spring-http-client
./start-client.sh
```

## 🏗️ Architecture

```
Browser → Spring Boot UI → HTTP API → Python Server → LangGraph Orchestrator
                                                           ├── RAG Agent (MongoDB + Qdrant)
                                                           └── Wikipedia Agent
```

### Components
- **Frontend**: Spring Boot + Thymeleaf + Bootstrap
- **Backend**: Python HTTP server
- **Orchestration**: LangGraph workflow
- **Data**: MongoDB (structured) + Qdrant (embeddings)
- **AI**: Sentence transformers + Optional OpenAI

## 📊 Data Processing

### ETL Pipeline
1. **Extract**: Load HR dataset (CSV)
2. **Transform**: Clean, standardize fields
3. **Load**: Store in MongoDB

### RAG Pipeline  
1. **Embed**: Create semantic embeddings
2. **Index**: Store vectors in Qdrant
3. **Search**: Enable similarity queries

## 🎮 Usage Examples

### Web Interface
1. Navigate to http://localhost:8080
2. Enter factual claims in the form
3. See real-time classification
4. Get detailed verification results

### API Usage
```bash
# Direct API calls
curl -X POST http://localhost:8001/fact-check \\
  -H "Content-Type: application/json" \\
  -d '{
    "statement": "Our company has more females than males",
    "use_openai": true
  }'
```

## 🐳 Docker Services

| Service | Port | Purpose |
|---------|------|---------|
| Web UI | 8080 | User interface |
| Python API | 8001 | Fact-checking server |
| MongoDB | 27017 | Employee database |
| Mongo Express | 8081 | Database admin |
| Qdrant | 6333 | Vector database |

## 🔧 Configuration

### Environment Variables
```bash
# Python Server
FACTCHECK_HOST=localhost
FACTCHECK_PORT=8001

# Spring Client  
FACTCHECK_SERVER_URL=http://localhost:8001
SERVER_PORT=8080
```

### OpenAI Integration (Optional)
```bash
export OPENAI_API_KEY=your-key-here
# Enables better classification and analysis
```

## 📁 Project Structure

```
agents-experiements/
├── docker-compose.yml                 # Complete Docker setup
├── start-docker.sh                    # Guided Docker deployment
├── quick-start.sh                     # One-command start
│
├── fact-checker-system/               # Python backend
│   ├── agents/                        # AI agents
│   │   ├── enhanced_rag_agent.py      # 🔧 Enhanced fact verification
│   │   ├── langgraph_orchestrator.py  # 🎭 Main orchestrator  
│   │   └── wikipedia_agent.py         # 🌍 Public knowledge
│   ├── pipelines/                     # Data processing
│   ├── fact_check_server/             # HTTP server
│   └── Dockerfile                     # Python container
│
└── spring-http-client/                # Java frontend
    ├── src/main/                      # Spring Boot application
    └── Dockerfile                     # Java container
```

## 🧪 Testing

### Enhanced Capabilities Test
```bash
python fact-checker-system/test_enhanced_factcheck.py
```

### Manual Testing Scripts
```bash
# Test individual components
python agents/enhanced_rag_agent.py
python agents/langgraph_orchestrator.py
```

## 🚀 Production Deployment

### Docker Compose Production
```yaml
# Use production profiles
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### Scaling
- Load balance multiple Python server instances
- Use external MongoDB cluster  
- Redis for session management
- Nginx for reverse proxy

## 🔍 Troubleshooting

### Common Issues

**Pipeline Failures:**
```bash
# Check database connectivity
docker-compose logs mongodb qdrant

# Reset data
docker-compose down -v
docker-compose up -d
```

**Application Errors:**
```bash
# Check service logs
docker-compose logs fact-check-server
docker-compose logs spring-client

# Health checks
curl http://localhost:8001/health
curl http://localhost:8080/status
```

### Performance Tips
- Allocate 8GB+ RAM for optimal performance
- SSD storage for faster database operations
- Use OpenAI API key for better analysis quality

## 📝 Development

### Adding New Fact-Check Types
1. Extend `enhanced_rag_agent.py` with new parsing logic
2. Add test cases to verification methods
3. Update UI with new statement examples

### Custom Datasets
1. Replace HR dataset with your data
2. Update ETL pipeline field mappings
3. Modify searchable text generation

## 🤝 Contributing

1. Fork the repository
2. Create feature branch
3. Add tests for new functionality
4. Submit pull request

## 📄 License

This project is licensed under the MIT License.

## 🙏 Acknowledgments

- **HR Dataset**: Dr. Rich Huebner (Kaggle)
- **LangGraph**: LangChain framework
- **Spring AI**: Spring ecosystem
- **Qdrant**: Vector database
- **Sentence Transformers**: Hugging Face

---

**🎯 Ready to fact-check? Start with `./start-docker.sh` and visit http://localhost:8080**