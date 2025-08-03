#!/bin/bash

echo "🔍 Testing Arxos DevContainer Configuration"
echo "=========================================="

# Check if we're in a devcontainer
if [ -n "$REMOTE_CONTAINERS" ]; then
    echo "✅ Running inside a devcontainer"
else
    echo "⚠️  Not running inside a devcontainer"
fi

# Check Docker
echo ""
echo "🐳 Docker Status:"
if command -v docker &> /dev/null; then
    echo "✅ Docker is installed"
    docker --version
    if docker info &> /dev/null; then
        echo "✅ Docker daemon is running"
    else
        echo "❌ Docker daemon is not running"
    fi
else
    echo "❌ Docker is not installed"
fi

# Check required tools
echo ""
echo "🛠️  Required Tools:"
tools=("go" "python3" "node" "npm" "rustc" "cargo" "git")
for tool in "${tools[@]}"; do
    if command -v "$tool" &> /dev/null; then
        echo "✅ $tool is installed"
        "$tool" --version | head -1
    else
        echo "❌ $tool is not installed"
    fi
done

# Check data directory
echo ""
echo "📁 Data Directory:"
if [ -d "/workspaces/data" ]; then
    echo "✅ Data directory exists"
    ls -la /workspaces/data/
else
    echo "❌ Data directory does not exist"
fi

# Check environment file
echo ""
echo "📝 Environment File:"
if [ -f "/workspaces/.env" ]; then
    echo "✅ Environment file exists"
    echo "Contents:"
    cat /workspaces/.env
else
    echo "❌ Environment file does not exist"
fi

# Check ports
echo ""
echo "🌐 Port Availability:"
ports=(3000 3001 8080 8000 5432 6379)
for port in "${ports[@]}"; do
    if netstat -tuln 2>/dev/null | grep ":$port " > /dev/null; then
        echo "✅ Port $port is in use"
    else
        echo "⚠️  Port $port is not in use"
    fi
done

echo ""
echo "✅ Configuration test complete!" 