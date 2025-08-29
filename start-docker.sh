#!/bin/bash

# Complete Docker Deployment Script for Fact-Checker System
# Single command to start everything: infrastructure + pipelines + applications

set -e

echo "🚀 Starting Complete Fact-Checker System with Docker"
echo "====================================================="

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    echo "💡 On Mac: Start Docker Desktop"
    echo "💡 On Linux: sudo systemctl start docker"
    exit 1
fi

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    echo "❌ docker-compose not found. Please install Docker Compose."
    exit 1
fi

echo "✅ Docker is running"

# Check if HR dataset exists
if [ ! -f "fact-checker-system/data/HRDataset_v14.csv" ]; then
    echo "⚠️  HR dataset not found at fact-checker-system/data/HRDataset_v14.csv"
    echo ""
    echo "📥 Please download the HR dataset:"
    echo "   1. Go to: https://www.kaggle.com/datasets/rhuebner/human-resources-data-set"
    echo "   2. Download HRDataset_v14.csv"
    echo "   3. Place it in: fact-checker-system/data/"
    echo ""
    read -p "Do you want to continue without the dataset? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Exiting. Please add the dataset and try again."
        exit 1
    fi
    echo "⚠️  Continuing without dataset - pipelines will fail but infrastructure will start"
fi

echo ""
echo "🔧 Starting infrastructure services..."
echo "--------------------------------------"

# Start infrastructure first
docker-compose up -d mongodb qdrant mongo-express zenml-server

echo "⏳ Waiting for infrastructure to be ready..."
echo "   This may take a few minutes on first run..."

# Wait for services without timeout
while true; do
    if docker-compose ps | grep -q "mongodb.*Up.*healthy" && docker-compose ps | grep -q "qdrant.*Up" && docker-compose ps | grep -q "zenml.*Up"; then
        echo "✅ Infrastructure is ready!"
        break
    fi
    sleep 5
    echo "   Still waiting for MongoDB, Qdrant, and ZenML..."
done

echo ""
echo "🔄 Running data pipelines..."
echo "----------------------------"

# Run pipeline initialization
docker-compose run --rm pipeline-init

echo ""
echo "🌐 Starting application services..."
echo "-----------------------------------"

# Start application services
docker-compose up -d fact-check-server spring-client

echo ""
echo "⏳ Waiting for applications to be ready..."
timeout=90
elapsed=0
while [ $elapsed -lt $timeout ]; do
    if curl -s http://localhost:8001/health > /dev/null 2>&1 && curl -s http://localhost:8080/status > /dev/null 2>&1; then
        echo "✅ Applications are ready!"
        break
    fi
    sleep 5
    elapsed=$((elapsed + 5))
    echo "   Still waiting... ($elapsed/${timeout}s)"
done

if [ $elapsed -ge $timeout ]; then
    echo "⚠️  Applications may still be starting..."
    echo "🔍 Check service logs:"
    echo "   docker-compose logs fact-check-server"
    echo "   docker-compose logs spring-client"
fi

echo ""
echo "🎉 Fact-Checker System is now running!"
echo "======================================"
echo ""
echo "📍 Available services:"
echo "   🌐 Web UI:           http://localhost:8080"
echo "   🔧 Fact-Check API:   http://localhost:8001"
echo "   📊 ZenML Dashboard:  http://localhost:8237"
echo "   📊 MongoDB Admin:    http://localhost:8081 (admin/password123)"
echo "   🔍 Qdrant UI:        http://localhost:6333/dashboard"
echo ""
echo "🧪 Test statements:"
echo "   • Our company has more females than males"
echo "   • Production department average salary is \$65000"
echo "   • IT department has exactly 45 employees"
echo ""
echo "🛑 To stop all services:"
echo "   docker-compose down"
echo ""
echo "📊 To view service status:"
echo "   docker-compose ps"
echo ""
echo "📋 To view logs:"
echo "   docker-compose logs [service-name]"