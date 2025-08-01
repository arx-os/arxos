#!/bin/bash

# Arxos Local Development Setup Script
# This script automates the setup of the entire Arxos product locally

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check if port is in use
port_in_use() {
    lsof -i :$1 >/dev/null 2>&1
}

# Function to wait for service to be ready
wait_for_service() {
    local host=$1
    local port=$2
    local service_name=$3
    local max_attempts=30
    local attempt=1
    
    print_status "Waiting for $service_name to be ready..."
    
    while [ $attempt -le $max_attempts ]; do
        if nc -z $host $port 2>/dev/null; then
            print_success "$service_name is ready!"
            return 0
        fi
        
        echo -n "."
        sleep 2
        attempt=$((attempt + 1))
    done
    
    print_error "$service_name failed to start within expected time"
    return 1
}

# Main setup function
main() {
    print_status "Starting Arxos Local Development Setup..."
    
    # Check if we're in the right directory
    if [ ! -f "docker-compose.yml" ]; then
        print_error "Please run this script from the arxos directory"
        exit 1
    fi
    
    # Check prerequisites
    print_status "Checking prerequisites..."
    
    local missing_deps=()
    
    if ! command_exists docker; then
        missing_deps+=("docker")
    fi
    
    if ! command_exists docker-compose; then
        missing_deps+=("docker-compose")
    fi
    
    if ! command_exists python3; then
        missing_deps+=("python3")
    fi
    
    if ! command_exists go; then
        missing_deps+=("go")
    fi
    
    if [ ${#missing_deps[@]} -ne 0 ]; then
        print_error "Missing required dependencies: ${missing_deps[*]}"
        print_status "Please install the missing dependencies and try again"
        exit 1
    fi
    
    print_success "All prerequisites are installed"
    
    # Create necessary directories
    print_status "Creating necessary directories..."
    mkdir -p logs data cache
    
    # Set up environment file
    if [ ! -f ".env" ]; then
        print_status "Creating .env file..."
        cat > .env << EOF
# Arxos Environment Configuration
DATABASE_URL=postgresql://arxos:password@localhost:5432/arxos
REDIS_URL=redis://localhost:6379
JWT_SECRET=your-super-secret-jwt-key-change-this-in-production
API_HOST=0.0.0.0
API_PORT=8000
SVGX_API_PORT=8001
WEB_PORT=3000
BACKEND_PORT=8080

# Development settings
DEBUG=true
LOG_LEVEL=INFO
ENVIRONMENT=development

# Database settings
POSTGRES_DB=arxos
POSTGRES_USER=arxos
POSTGRES_PASSWORD=password

# Redis settings
REDIS_HOST=localhost
REDIS_PORT=6379

# Monitoring
PROMETHEUS_PORT=9090
GRAFANA_PORT=3001
EOF
        print_success "Created .env file"
    else
        print_warning ".env file already exists, skipping creation"
    fi
    
    # Check if Docker is running
    if ! docker info >/dev/null 2>&1; then
        print_error "Docker is not running. Please start Docker and try again."
        exit 1
    fi
    
    # Check for port conflicts
    print_status "Checking for port conflicts..."
    local ports_to_check=(5432 6379 8000 8001 8080 3000 9090 3001)
    local conflicting_ports=()
    
    for port in "${ports_to_check[@]}"; do
        if port_in_use $port; then
            conflicting_ports+=($port)
        fi
    done
    
    if [ ${#conflicting_ports[@]} -ne 0 ]; then
        print_warning "The following ports are already in use: ${conflicting_ports[*]}"
        print_status "Please stop the services using these ports or modify the configuration"
        read -p "Continue anyway? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
    
    # Start services with Docker Compose
    print_status "Starting services with Docker Compose..."
    
    # Pull latest images
    docker-compose pull
    
    # Start services
    docker-compose up -d
    
    # Wait for services to be ready
    print_status "Waiting for services to start..."
    
    # Wait for PostgreSQL
    wait_for_service localhost 5432 "PostgreSQL"
    
    # Wait for Redis
    wait_for_service localhost 6379 "Redis"
    
    # Wait for SVG Parser
    wait_for_service localhost 8000 "SVG Parser"
    
    # Wait for Backend
    wait_for_service localhost 8080 "Backend"
    
    # Wait for SVGX Engine
    wait_for_service localhost 8001 "SVGX Engine"
    
    # Wait for Web Frontend
    wait_for_service localhost 3000 "Web Frontend"
    
    # Run database migrations
    print_status "Running database migrations..."
    docker-compose exec svg-parser alembic upgrade head || {
        print_warning "Database migrations failed, but continuing..."
    }
    
    # Create test data
    print_status "Creating test data..."
    create_test_data
    
    # Health checks
    print_status "Performing health checks..."
    perform_health_checks
    
    # Final status
    print_success "Arxos local development environment is ready!"
    print_status ""
    print_status "Services are running on:"
    print_status "  - Web Interface: http://localhost:3000"
    print_status "  - SVG Parser API: http://localhost:8000"
    print_status "  - Backend API: http://localhost:8080"
    print_status "  - SVGX Engine: http://localhost:8001"
    print_status "  - Grafana Dashboard: http://localhost:3001"
    print_status ""
    print_status "API Documentation:"
    print_status "  - SVG Parser: http://localhost:8000/docs"
    print_status "  - Backend: http://localhost:8080/docs"
    print_status "  - SVGX Engine: http://localhost:8001/docs"
    print_status ""
    print_status "To stop all services: docker-compose down"
    print_status "To view logs: docker-compose logs -f"
    print_status "To restart: docker-compose restart"
}

# Function to create test data
create_test_data() {
    print_status "Creating test data..."
    
    # Create test user
    curl -s -X POST http://localhost:8080/api/register \
        -H "Content-Type: application/json" \
        -d '{
            "username": "testuser",
            "email": "test@arxos.com",
            "password": "password123"
        }' > /dev/null || print_warning "Failed to create test user"
    
    # Create test building
    curl -s -X POST http://localhost:8080/api/buildings \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer $(get_test_token)" \
        -d '{
            "name": "Test Building",
            "address": "123 Test Street",
            "description": "Test building for development"
        }' > /dev/null || print_warning "Failed to create test building"
    
    print_success "Test data created"
}

# Function to get test token
get_test_token() {
    local response=$(curl -s -X POST http://localhost:8080/api/login \
        -H "Content-Type: application/json" \
        -d '{
            "username": "testuser",
            "password": "password123"
        }')
    
    echo $response | grep -o '"token":"[^"]*"' | cut -d'"' -f4 || echo ""
}

# Function to perform health checks
perform_health_checks() {
    local checks_passed=0
    local total_checks=0
    
    # Check SVG Parser
    total_checks=$((total_checks + 1))
    if curl -s http://localhost:8000/health > /dev/null; then
        print_success "SVG Parser health check passed"
        checks_passed=$((checks_passed + 1))
    else
        print_error "SVG Parser health check failed"
    fi
    
    # Check Backend
    total_checks=$((total_checks + 1))
    if curl -s http://localhost:8080/api/health > /dev/null; then
        print_success "Backend health check passed"
        checks_passed=$((checks_passed + 1))
    else
        print_error "Backend health check failed"
    fi
    
    # Check SVGX Engine
    total_checks=$((total_checks + 1))
    if curl -s http://localhost:8001/health > /dev/null; then
        print_success "SVGX Engine health check passed"
        checks_passed=$((checks_passed + 1))
    else
        print_error "SVGX Engine health check failed"
    fi
    
    # Check Web Interface
    total_checks=$((total_checks + 1))
    if curl -s http://localhost:3000 > /dev/null; then
        print_success "Web Interface health check passed"
        checks_passed=$((checks_passed + 1))
    else
        print_error "Web Interface health check failed"
    fi
    
    if [ $checks_passed -eq $total_checks ]; then
        print_success "All health checks passed ($checks_passed/$total_checks)"
    else
        print_warning "Some health checks failed ($checks_passed/$total_checks)"
    fi
}

# Function to show usage
usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -h, --help     Show this help message"
    echo "  --clean         Clean up existing containers and data"
    echo "  --logs          Show logs after setup"
    echo ""
    echo "This script sets up the complete Arxos local development environment."
}

# Function to clean up
cleanup() {
    print_status "Cleaning up existing containers and data..."
    docker-compose down -v
    docker system prune -f
    print_success "Cleanup completed"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            usage
            exit 0
            ;;
        --clean)
            cleanup
            ;;
        --logs)
            SHOW_LOGS=true
            ;;
        *)
            print_error "Unknown option: $1"
            usage
            exit 1
            ;;
    esac
    shift
done

# Run main function
main

# Show logs if requested
if [ "$SHOW_LOGS" = true ]; then
    print_status "Showing logs (press Ctrl+C to exit)..."
    docker-compose logs -f
fi 