#!/bin/bash

# Quick Setup Script for Fact-Checker MCP System
# This script handles the basic setup steps before starting the MCP server

set -e

echo "🚀 Setting up Fact-Checker MCP System..."
echo "======================================="

# Check if we're in the right directory
if [ ! -f "requirements.txt" ]; then
    echo "❌ requirements.txt not found. Please run this from the fact-checker-system directory"
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python -m venv venv
else
    echo "✅ Virtual environment already exists"
fi

# Activate virtual environment
echo "📦 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install requirements
echo "📥 Installing Python dependencies..."
pip install -r requirements.txt

# Test imports
echo "🔍 Testing imports..."
python test_imports.py

echo ""
echo "✅ Setup complete!"
echo ""
echo "🔧 Next steps:"
echo "1. Make sure Docker is running: docker --version"
echo "2. Start databases: docker-compose up -d"  
echo "3. Download HR dataset to data/ folder (see SETUP_GUIDE.md)"
echo "4. Run ETL pipeline: python run_etl.py"
echo "5. Start MCP server: ./start-mcp-server.sh"
echo ""
echo "For full setup instructions, see SETUP_GUIDE.md"