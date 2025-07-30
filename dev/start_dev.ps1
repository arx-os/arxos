# Arxos Development Environment Startup Script (PowerShell)
# This script starts the complete development environment with all services

param(
    [switch]$SkipChecks,
    [switch]$NoBrowser
)

Write-Host "🚀 Starting Arxos Development Environment..." -ForegroundColor Green

# Check if Docker is running
if (-not $SkipChecks) {
    try {
        docker info | Out-Null
        Write-Host "✅ Docker is running" -ForegroundColor Green
    }
    catch {
        Write-Host "❌ Docker is not running. Please start Docker and try again." -ForegroundColor Red
        exit 1
    }

    # Check if Docker Compose is available
    try {
        docker-compose --version | Out-Null
        Write-Host "✅ Docker Compose is available" -ForegroundColor Green
    }
    catch {
        Write-Host "❌ Docker Compose is not installed. Please install Docker Compose and try again." -ForegroundColor Red
        exit 1
    }
}

# Set environment variables
$env:ARXOS_ENV = "development"
$env:COMPOSE_PROJECT_NAME = "arxos"

# Create necessary directories
Write-Host "📁 Creating development directories..." -ForegroundColor Yellow
$directories = @(
    "../services/gus/data/knowledge/building_codes",
    "../services/gus/data/knowledge/standards", 
    "../services/gus/data/knowledge/arxos",
    "../services/gus/data/vector_store",
    "../services/gus/logs"
)

foreach ($dir in $directories) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
        Write-Host "  Created: $dir" -ForegroundColor Gray
    }
}

# Build and start services
Write-Host "🔨 Building and starting services..." -ForegroundColor Yellow
docker-compose up --build -d

# Wait for services to be healthy
Write-Host "⏳ Waiting for services to be ready..." -ForegroundColor Yellow
$timeout = 300
$elapsed = 0
$interval = 10

while ($elapsed -lt $timeout) {
    $status = docker-compose ps
    if ($status -match "healthy") {
        Write-Host "✅ All services are healthy!" -ForegroundColor Green
        break
    }
    
    Write-Host "⏳ Waiting for services... ($elapsed/$timeout seconds)" -ForegroundColor Yellow
    Start-Sleep -Seconds $interval
    $elapsed += $interval
}

if ($elapsed -ge $timeout) {
    Write-Host "❌ Timeout waiting for services to be ready" -ForegroundColor Red
    Write-Host "📋 Service status:" -ForegroundColor Yellow
    docker-compose ps
    exit 1
}

# Display service information
Write-Host ""
Write-Host "🎉 Arxos Development Environment is ready!" -ForegroundColor Green
Write-Host ""
Write-Host "📊 Service Status:" -ForegroundColor Cyan
docker-compose ps
Write-Host ""
Write-Host "🌐 Service URLs:" -ForegroundColor Cyan
Write-Host "  - GUS Agent:     http://localhost:9001" -ForegroundColor White
Write-Host "  - Browser CAD:    http://localhost:3000" -ForegroundColor White
Write-Host "  - ArxIDE:         http://localhost:8080" -ForegroundColor White
Write-Host "  - Backend API:    http://localhost:4000" -ForegroundColor White
Write-Host "  - PostgreSQL:     localhost:5432" -ForegroundColor White
Write-Host "  - Redis:          localhost:6379" -ForegroundColor White
Write-Host ""
Write-Host "🔧 CLI Commands:" -ForegroundColor Cyan
Write-Host "  - View logs:      docker-compose logs -f" -ForegroundColor White
Write-Host "  - Stop services:  docker-compose down" -ForegroundColor White
Write-Host "  - Restart:        docker-compose restart" -ForegroundColor White
Write-Host ""
Write-Host "🧠 GUS Agent Commands:" -ForegroundColor Cyan
Write-Host "  - Health check:   arx gus health" -ForegroundColor White
Write-Host "  - Query GUS:      arx gus query 'help me create a wall'" -ForegroundColor White
Write-Host "  - Knowledge:      arx gus knowledge electrical_outlets" -ForegroundColor White
Write-Host "  - Topics:         arx gus help-topics" -ForegroundColor White
Write-Host ""
Write-Host "📚 Documentation:" -ForegroundColor Cyan
Write-Host "  - API Docs:       http://localhost:9001/docs" -ForegroundColor White
Write-Host "  - Health Check:   http://localhost:9001/health" -ForegroundColor White
Write-Host ""

# Optional: Open browser to main services
if (-not $NoBrowser) {
    Write-Host "🌐 Opening services in browser..." -ForegroundColor Yellow
    try {
        Start-Process "http://localhost:9001/docs" -ErrorAction SilentlyContinue
        Start-Process "http://localhost:3000" -ErrorAction SilentlyContinue
    }
    catch {
        Write-Host "⚠️  Could not open browser automatically" -ForegroundColor Yellow
    }
}

Write-Host "✅ Development environment started successfully!" -ForegroundColor Green
Write-Host "💡 Tip: Use 'docker-compose logs -f' to view real-time logs" -ForegroundColor Cyan 