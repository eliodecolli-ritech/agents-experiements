#!/bin/bash

# Start HTTP Server for Fact-Checker System
# This script starts the Python HTTP server that exposes the LangGraph orchestrator

set -e

echo "🚀 Starting Fact-Checker HTTP Server..."
echo "========================================="

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Please run setup first:"
    echo "   python -m venv venv"
    echo "   source venv/bin/activate"
    echo "   pip install -r requirements.txt"
    exit 1
fi

# Activate virtual environment
echo "📦 Activating virtual environment..."
source venv/bin/activate

# Check if required dependencies are installed
echo "🔍 Checking dependencies..."
python -c "import mcp; print('✅ MCP library found')" || {
    echo "❌ MCP library not found. Installing..."
    pip install mcp
}

# Check other critical dependencies
python -c "import pymongo; print('✅ PyMongo found')" || {
    echo "❌ PyMongo not found. Please install requirements:"
    echo "   pip install -r requirements.txt"
    exit 1
}

python -c "import langgraph; print('✅ LangGraph found')" || {
    echo "❌ LangGraph not found. Please install requirements:"
    echo "   pip install -r requirements.txt"
    exit 1
}

# Check if databases are running
echo "🗄️ Checking database connections..."
python -c "
import pymongo
try:
    client = pymongo.MongoClient('mongodb://localhost:27017')
    client.admin.command('ping')
    print('✅ MongoDB is running')
except:
    print('❌ MongoDB is not running. Please start with: docker-compose up -d')
    exit(1)
"

# Set environment variables if not set
export FACTCHECK_HOST=${FACTCHECK_HOST:-localhost}
export FACTCHECK_PORT=${FACTCHECK_PORT:-8001}
export PYTHONPATH="$(pwd):${PYTHONPATH}"

echo "🌐 HTTP Server will start on: $FACTCHECK_HOST:$FACTCHECK_PORT"
echo "🔧 Available endpoints: /fact-check, /classify, /training-data"
echo "📚 Available resources: /status, /evidence-sources"
echo ""
echo "Press Ctrl+C to stop the server"
echo "========================================="

# Start the HTTP server
cd fact_check_server
python http_server.py