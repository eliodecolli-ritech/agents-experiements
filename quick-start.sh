#!/bin/bash

# Quick Start - One Command Deployment
# Usage: ./quick-start.sh

echo "🚀 Quick Start - Fact-Checker System"
echo "===================================="

# Check for dataset
if [ ! -f "fact-checker-system/data/HRDataset_v14.csv" ]; then
    echo "📥 Please add HR dataset to: fact-checker-system/data/HRDataset_v14.csv"
    echo "   Download from: https://www.kaggle.com/datasets/rhuebner/human-resources-data-set"
    echo ""
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo "🔄 Starting all services..."

# Start everything at once
docker-compose up -d

# Run pipelines
echo "⏳ Initializing data pipelines..."
docker-compose run --rm pipeline-init

echo ""
echo "🎉 System ready!"
echo "📍 Web UI: http://localhost:8080"
echo "🛑 Stop: docker-compose down"