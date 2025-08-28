#!/bin/bash

# Start Spring AI HTTP Client
# This script starts the Spring Boot web application with Thymeleaf UI

set -e

echo "🌸 Starting Spring AI HTTP Client..."
echo "=================================="

# Check if Java is available
java_version=$(java -version 2>&1 | awk -F '"' '/version/ {print $2}')
echo "☕ Java version: $java_version"

if ! java -version 2>&1 | grep -q "17\|18\|19\|20\|21"; then
    echo "⚠️  Warning: Java 17+ is recommended for Spring Boot 3.x"
    echo "   Current Java version: $java_version"
fi

# Check if Maven wrapper exists
if [ ! -f "./mvnw" ]; then
    echo "❌ Maven wrapper (mvnw) not found. Please ensure you're in the spring-mcp-client directory"
    exit 1
fi

# Make maven wrapper executable
chmod +x ./mvnw

# Set environment variables
export FACTCHECK_SERVER_URL=${FACTCHECK_SERVER_URL:-http://localhost:8001}
export SERVER_PORT=${SERVER_PORT:-8080}

echo "🔗 Fact-Check Server URL: $FACTCHECK_SERVER_URL"
echo "🌐 Web UI will be available at: http://localhost:$SERVER_PORT"
echo ""

# Check if HTTP server is running
echo "🔍 Checking HTTP server availability..."
if curl -s --connect-timeout 5 "$FACTCHECK_SERVER_URL/status" > /dev/null 2>&1; then
    echo "✅ HTTP server is running at $FACTCHECK_SERVER_URL"
else
    echo "⚠️  HTTP server not responding at $FACTCHECK_SERVER_URL"
    echo "   Make sure to start the Python HTTP server first:"
    echo "   cd ../fact-checker-system && ./start-http-server.sh"
    echo ""
    echo "   Continuing anyway - you can start the HTTP server later..."
fi

echo ""
echo "🚀 Starting Spring Boot application..."
echo "📱 Open http://localhost:$SERVER_PORT in your browser"
echo "Press Ctrl+C to stop the server"
echo "=================================="

# Start Spring Boot application
./mvnw spring-boot:run -Dspring-boot.run.profiles=dev