#!/bin/bash

# Docker Cleanup Script for Fact-Checker System
# Only removes fact-checker specific containers, volumes, and images

echo "🧹 Fact-Checker Docker Cleanup"
echo "==============================="

echo "🛑 Stopping fact-checker services..."
docker-compose down

echo "🗑️  Removing fact-checker containers..."
#docker-compose rm -f

echo ""
echo "Choose cleanup level:"
echo "1) Basic cleanup (containers only)"
echo "2) Include data volumes (removes database data)"
echo "3) Include custom images (forces rebuild)"

read -p "Select option (1-3): " choice

case $choice in
    1)
        echo "✅ Basic cleanup complete!"
        echo "💡 Data and images preserved"
        ;;
    2)
        echo "💾 Removing fact-checker data volumes..."
        docker-compose down -v
        echo "✅ Containers and volumes removed!"
        echo "💡 Images preserved"
        ;;
    3)
        echo "💾 Removing fact-checker data volumes..."
        docker-compose down -v
        echo "🏗️  Removing fact-checker images..."
        docker-compose down --rmi local
        echo "✅ Full cleanup complete!"
        echo "💡 Will rebuild images on next start"
        ;;
    *)
        echo "❌ Invalid option"
        exit 1
        ;;
esac

echo ""
echo "🚀 To start again:"
echo "   ./start-docker.sh"