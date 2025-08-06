#!/bin/bash

# MCP-Engineering Production Deployment Script
# This script deploys the MCP-Engineering integration to production

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_NAME="mcp-engineering"
NAMESPACE="arxos"
REGISTRY="arxos"
IMAGE_TAG="latest"

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check if Docker is running
    if ! docker info > /dev/null 2>&1; then
        log_error "Docker is not running. Please start Docker and try again."
        exit 1
    fi
    
    # Check if kubectl is available (for Kubernetes deployment)
    if command -v kubectl &> /dev/null; then
        KUBERNETES_AVAILABLE=true
        log_info "Kubernetes (kubectl) is available"
    else
        KUBERNETES_AVAILABLE=false
        log_warning "Kubernetes (kubectl) not found. Will use Docker Compose deployment."
    fi
    
    # Check if docker-compose is available
    if ! command -v docker-compose &> /dev/null; then
        log_error "docker-compose is not installed. Please install it and try again."
        exit 1
    fi
    
    log_success "Prerequisites check completed"
}

generate_secrets() {
    log_info "Generating production secrets..."
    
    # Generate JWT secret
    JWT_SECRET=$(openssl rand -base64 32)
    echo "JWT_SECRET=$JWT_SECRET" >> .env.production
    
    # Generate database password
    DB_PASSWORD=$(openssl rand -base64 16)
    echo "PROD_DB_PASSWORD=$DB_PASSWORD" >> .env.production
    
    # Generate Grafana password
    GRAFANA_PASSWORD=$(openssl rand -base64 16)
    echo "GRAFANA_PASSWORD=$GRAFANA_PASSWORD" >> .env.production
    
    log_success "Production secrets generated"
}

build_image() {
    log_info "Building production Docker image..."
    
    # Build the image
    docker build -t $REGISTRY/$PROJECT_NAME:$IMAGE_TAG .
    
    # Tag for production
    docker tag $REGISTRY/$PROJECT_NAME:$IMAGE_TAG $REGISTRY/$PROJECT_NAME:prod-$(date +%Y%m%d-%H%M%S)
    
    log_success "Docker image built successfully"
}

deploy_docker_compose() {
    log_info "Deploying with Docker Compose..."
    
    # Stop existing services
    docker-compose -f docker-compose.prod.yml down --remove-orphans
    
    # Start services
    docker-compose -f docker-compose.prod.yml up -d
    
    # Wait for services to be ready
    log_info "Waiting for services to be ready..."
    sleep 30
    
    # Check service health
    if curl -f http://localhost:8001/health > /dev/null 2>&1; then
        log_success "MCP Service is healthy"
    else
        log_error "MCP Service health check failed"
        exit 1
    fi
    
    log_success "Docker Compose deployment completed"
}

deploy_kubernetes() {
    log_info "Deploying to Kubernetes..."
    
    # Create namespace if it doesn't exist
    kubectl create namespace $NAMESPACE --dry-run=client -o yaml | kubectl apply -f -
    
    # Apply secrets
    kubectl apply -f k8s/mcp-deployment.yaml
    
    # Wait for deployment to be ready
    log_info "Waiting for deployment to be ready..."
    kubectl wait --for=condition=available --timeout=300s deployment/mcp-service -n $NAMESPACE
    
    # Check service health
    if kubectl get pods -n $NAMESPACE -l app=mcp-service | grep -q Running; then
        log_success "Kubernetes deployment completed"
    else
        log_error "Kubernetes deployment failed"
        exit 1
    fi
}

run_migrations() {
    log_info "Running database migrations..."
    
    # Run migrations
    docker-compose -f docker-compose.prod.yml exec mcp-service python -m alembic upgrade head
    
    # Initialize knowledge base
    docker-compose -f docker-compose.prod.yml exec mcp-service python -c "
from knowledge.knowledge_base import KnowledgeBase
kb = KnowledgeBase()
kb.initialize_database()
print('✅ Knowledge base initialized')
"
    
    # Initialize ML models
    docker-compose -f docker-compose.prod.yml exec mcp-service python -c "
from ml.model_manager import ModelManager
mm = ModelManager()
mm.initialize_models()
print('✅ ML models initialized')
"
    
    log_success "Database migrations completed"
}

run_tests() {
    log_info "Running production tests..."
    
    # Test health endpoint
    if curl -f http://localhost:8001/health > /dev/null 2>&1; then
        log_success "Health check passed"
    else
        log_error "Health check failed"
        exit 1
    fi
    
    # Test API endpoints
    TOKEN=$(curl -s -X POST http://localhost:8001/api/v1/auth/login \
        -H "Content-Type: application/json" \
        -d '{"username": "admin", "password": "admin123"}' | jq -r '.access_token')
    
    if [ "$TOKEN" != "null" ] && [ "$TOKEN" != "" ]; then
        log_success "Authentication test passed"
    else
        log_error "Authentication test failed"
        exit 1
    fi
    
    # Test validation endpoint
    VALIDATION_RESPONSE=$(curl -s -X POST http://localhost:8001/api/v1/validate \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer $TOKEN" \
        -d '{
            "building_data": {
                "area": 8000,
                "height": 25,
                "type": "commercial"
            },
            "validation_type": "structural"
        }')
    
    if echo "$VALIDATION_RESPONSE" | jq -e '.validation_result' > /dev/null 2>&1; then
        log_success "Validation endpoint test passed"
    else
        log_error "Validation endpoint test failed"
        exit 1
    fi
    
    log_success "Production tests completed"
}

setup_monitoring() {
    log_info "Setting up monitoring..."
    
    # Check Prometheus
    if curl -f http://localhost:9090/api/v1/query?query=up > /dev/null 2>&1; then
        log_success "Prometheus is running"
    else
        log_warning "Prometheus is not accessible"
    fi
    
    # Check Grafana
    if curl -f http://localhost:3000/api/health > /dev/null 2>&1; then
        log_success "Grafana is running"
    else
        log_warning "Grafana is not accessible"
    fi
    
    log_success "Monitoring setup completed"
}

show_deployment_info() {
    log_info "Deployment Information:"
    echo ""
    echo "🌐 Service URLs:"
    echo "   - MCP Service: http://localhost:8001"
    echo "   - API Documentation: http://localhost:8001/docs"
    echo "   - Health Check: http://localhost:8001/health"
    echo "   - Metrics: http://localhost:8001/metrics"
    echo ""
    echo "📊 Monitoring:"
    echo "   - Prometheus: http://localhost:9090"
    echo "   - Grafana: http://localhost:3000 (admin/admin)"
    echo "   - MLflow: http://localhost:5000"
    echo ""
    echo "🗄️  Databases:"
    echo "   - PostgreSQL: localhost:5432"
    echo "   - Redis: localhost:6379"
    echo ""
    echo "🔧 Management:"
    echo "   - View logs: docker-compose -f docker-compose.prod.yml logs -f"
    echo "   - Stop services: docker-compose -f docker-compose.prod.yml down"
    echo "   - Restart services: docker-compose -f docker-compose.prod.yml restart"
    echo ""
    echo "📋 Next Steps:"
    echo "   1. Configure your domain (mcp.arxos.com) to point to your server"
    echo "   2. Set up SSL certificates"
    echo "   3. Configure email settings for report delivery"
    echo "   4. Set up AWS S3 for report storage"
    echo "   5. Configure monitoring alerts"
    echo ""
}

main() {
    echo "🚀 MCP-Engineering Production Deployment"
    echo "======================================"
    echo ""
    
    # Check prerequisites
    check_prerequisites
    
    # Generate secrets if .env.production doesn't exist
    if [ ! -f .env.production ]; then
        generate_secrets
    else
        log_info "Using existing .env.production file"
    fi
    
    # Build Docker image
    build_image
    
    # Deploy based on available tools
    if [ "$KUBERNETES_AVAILABLE" = true ] && [ "$1" = "k8s" ]; then
        deploy_kubernetes
    else
        deploy_docker_compose
    fi
    
    # Run migrations
    run_migrations
    
    # Run tests
    run_tests
    
    # Setup monitoring
    setup_monitoring
    
    # Show deployment information
    show_deployment_info
    
    log_success "🎉 MCP-Engineering deployment completed successfully!"
    log_info "Your production-ready engineering validation system is now running!"
}

# Handle command line arguments
case "${1:-}" in
    "k8s")
        log_info "Using Kubernetes deployment"
        ;;
    "docker")
        log_info "Using Docker Compose deployment"
        KUBERNETES_AVAILABLE=false
        ;;
    "help"|"-h"|"--help")
        echo "Usage: $0 [k8s|docker]"
        echo ""
        echo "Options:"
        echo "  k8s     Deploy to Kubernetes (requires kubectl)"
        echo "  docker  Deploy with Docker Compose (default)"
        echo "  help    Show this help message"
        exit 0
        ;;
    *)
        log_info "Using Docker Compose deployment (default)"
        KUBERNETES_AVAILABLE=false
        ;;
esac

# Run main function
main "$@" 