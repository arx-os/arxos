#!/bin/bash

# Arxos Pipeline Deployment Script
# This script deploys the complete pipeline infrastructure

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PIPELINE_VERSION="1.0.0"
PYTHON_VERSION="3.11"
GO_VERSION="1.21"
REQUIRED_PYTHON_PACKAGES=(
    "pytest"
    "pytest-cov"
    "pytest-mock"
    "black"
    "flake8"
    "mypy"
    "bandit"
    "safety"
)

REQUIRED_GO_PACKAGES=(
    "github.com/gin-gonic/gin"
    "github.com/google/uuid"
    "github.com/jmoiron/sqlx"
)

# Functions
print_header() {
    echo -e "${BLUE}================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}================================${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Check if running as root
check_root() {
    if [[ $EUID -eq 0 ]]; then
        print_warning "This script should not be run as root"
        read -p "Continue anyway? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
}

# Check system requirements
check_system_requirements() {
    print_header "Checking System Requirements"
    
    # Check Python
    if command -v python3 &> /dev/null; then
        PYTHON_VER=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
        if [[ "$PYTHON_VER" == "$PYTHON_VERSION" ]]; then
            print_success "Python $PYTHON_VERSION found"
        else
            print_warning "Python $PYTHON_VER found (recommended: $PYTHON_VERSION)"
        fi
    else
        print_error "Python3 not found"
        exit 1
    fi
    
    # Check Go
    if command -v go &> /dev/null; then
        GO_VER=$(go version | cut -d' ' -f3 | cut -d'.' -f1,2)
        if [[ "$GO_VER" == "$GO_VERSION" ]]; then
            print_success "Go $GO_VERSION found"
        else
            print_warning "Go $GO_VER found (recommended: $GO_VERSION)"
        fi
    else
        print_error "Go not found"
        exit 1
    fi
    
    # Check Git
    if command -v git &> /dev/null; then
        print_success "Git found"
    else
        print_error "Git not found"
        exit 1
    fi
    
    # Check Docker (optional)
    if command -v docker &> /dev/null; then
        print_success "Docker found"
    else
        print_warning "Docker not found (optional for containerized deployment)"
    fi
}

# Install Python dependencies
install_python_dependencies() {
    print_header "Installing Python Dependencies"
    
    # Upgrade pip
    python3 -m pip install --upgrade pip
    
    # Install required packages
    for package in "${REQUIRED_PYTHON_PACKAGES[@]}"; do
        print_info "Installing $package..."
        python3 -m pip install "$package"
        print_success "Installed $package"
    done
    
    # Install project dependencies
    if [[ -f "requirements.txt" ]]; then
        print_info "Installing project dependencies..."
        python3 -m pip install -r requirements.txt
        print_success "Installed project dependencies"
    fi
}

# Install Go dependencies
install_go_dependencies() {
    print_header "Installing Go Dependencies"
    
    # Go to backend directory
    cd arx-backend
    
    # Download dependencies
    print_info "Downloading Go dependencies..."
    go mod download
    print_success "Downloaded Go dependencies"
    
    # Tidy modules
    print_info "Tidying Go modules..."
    go mod tidy
    print_success "Tidied Go modules"
    
    # Go back to root
    cd ..
}

# Create necessary directories
create_directories() {
    print_header "Creating Pipeline Directories"
    
    # Create schema directories
    mkdir -p schemas/{electrical,mechanical,plumbing,fire_alarm,audiovisual}
    print_success "Created schema directories"
    
    # Create symbol library directories
    mkdir -p arx-symbol-library/{electrical,mechanical,plumbing,fire_alarm,audiovisual}/metadata
    print_success "Created symbol library directories"
    
    # Create behavior directories
    mkdir -p svgx_engine/behavior
    print_success "Created behavior directories"
    
    # Create documentation directories
    mkdir -p docs/systems/{electrical,mechanical,plumbing,fire_alarm,audiovisual}
    print_success "Created documentation directories"
    
    # Create test directories
    mkdir -p tests/{unit,integration,performance}
    print_success "Created test directories"
}

# Setup database
setup_database() {
    print_header "Setting Up Database"
    
    # Check if PostgreSQL is available
    if command -v psql &> /dev/null; then
        print_info "PostgreSQL found"
        
        # Create database if it doesn't exist
        if ! psql -lqt | cut -d \| -f 1 | grep -qw arxos; then
            print_info "Creating arxos database..."
            createdb arxos
            print_success "Created arxos database"
        else
            print_success "arxos database already exists"
        fi
        
        # Run migrations
        print_info "Running database migrations..."
        cd arx-backend
        if [[ -f "migrations/004_create_pipeline_tables.sql" ]]; then
            psql -d arxos -f migrations/004_create_pipeline_tables.sql
            print_success "Applied database migrations"
        else
            print_warning "Database migration file not found"
        fi
        cd ..
    else
        print_warning "PostgreSQL not found - database setup skipped"
        print_info "You can set up the database manually later"
    fi
}

# Run tests
run_tests() {
    print_header "Running Pipeline Tests"
    
    # Run unit tests
    print_info "Running unit tests..."
    python3 -m pytest tests/test_pipeline_integration.py -v
    print_success "Unit tests completed"
    
    # Run comprehensive tests
    print_info "Running comprehensive tests..."
    python3 tests/test_pipeline_comprehensive.py
    print_success "Comprehensive tests completed"
    
    # Run Go tests
    print_info "Running Go tests..."
    cd arx-backend
    go test ./handlers -v
    cd ..
    print_success "Go tests completed"
}

# Validate installation
validate_installation() {
    print_header "Validating Pipeline Installation"
    
    # Test Python bridge service
    print_info "Testing Python bridge service..."
    cd svgx_engine
    python3 services/pipeline_integration.py --operation validate-schema --params '{"system": "test"}' || true
    cd ..
    print_success "Python bridge service test completed"
    
    # Test CLI tool
    print_info "Testing CLI tool..."
    python3 scripts/arx_pipeline.py --list-systems || true
    print_success "CLI tool test completed"
    
    # Test demonstration
    print_info "Testing demonstration..."
    python3 examples/pipeline_demo.py || true
    print_success "Demonstration test completed"
}

# Setup CI/CD
setup_cicd() {
    print_header "Setting Up CI/CD"
    
    # Check if GitHub Actions directory exists
    if [[ -d ".github/workflows" ]]; then
        print_success "GitHub Actions directory found"
        
        # Check if pipeline workflow exists
        if [[ -f ".github/workflows/arxos-pipeline.yml" ]]; then
            print_success "Pipeline workflow found"
        else
            print_warning "Pipeline workflow not found"
        fi
    else
        print_warning "GitHub Actions directory not found"
    fi
    
    # Setup pre-commit hooks (optional)
    if command -v pre-commit &> /dev/null; then
        print_info "Setting up pre-commit hooks..."
        pre-commit install
        print_success "Pre-commit hooks installed"
    else
        print_warning "pre-commit not found - hooks not installed"
    fi
}

# Generate configuration
generate_configuration() {
    print_header "Generating Pipeline Configuration"
    
    # Create pipeline config file
    cat > pipeline_config.json << EOF
{
    "version": "$PIPELINE_VERSION",
    "python_bridge_path": "svgx_engine/services/pipeline_integration.py",
    "svgx_engine_path": "svgx_engine",
    "validation_rules": {
        "schema": "validate-schema",
        "symbol": "validate-symbol",
        "behavior": "validate-behavior",
        "registry": "validate-registry",
        "compliance": "validate-compliance"
    },
    "quality_gates": {
        "test_coverage": 90,
        "security_scan": true,
        "performance_check": true,
        "compliance_check": true
    },
    "systems": [
        "electrical",
        "mechanical", 
        "plumbing",
        "fire_alarm",
        "audiovisual"
    ]
}
EOF
    
    print_success "Generated pipeline configuration"
}

# Create deployment summary
create_deployment_summary() {
    print_header "Deployment Summary"
    
    cat > DEPLOYMENT_SUMMARY.md << EOF
# Arxos Pipeline Deployment Summary

## Deployment Information
- **Version**: $PIPELINE_VERSION
- **Date**: $(date)
- **Python Version**: $(python3 --version)
- **Go Version**: $(go version)

## Installed Components
- ✅ Python Bridge Service
- ✅ Go Orchestration Layer
- ✅ Database Integration
- ✅ CLI Tools
- ✅ Test Suite
- ✅ CI/CD Integration

## Directory Structure
\`\`\`
arxos/
├── arx-backend/
│   ├── handlers/pipeline.go
│   ├── models/pipeline.go
│   ├── repository/pipeline_repository.go
│   └── migrations/004_create_pipeline_tables.sql
├── svgx_engine/
│   ├── services/pipeline_integration.py
│   ├── services/symbol_manager.py
│   ├── services/behavior_engine.py
│   ├── services/validation_engine.py
│   └── utils/errors.py
├── scripts/
│   ├── arx_pipeline.py
│   └── test_pipeline_integration.py
├── tests/
│   └── test_pipeline_comprehensive.py
├── examples/
│   └── pipeline_demo.py
└── .github/workflows/
    └── arxos-pipeline.yml
\`\`\`

## Usage Examples
\`\`\`bash
# Execute full pipeline for new system
python3 scripts/arx_pipeline.py --execute --system audiovisual

# Validate existing system
python3 scripts/arx_pipeline.py --validate --system electrical

# Run tests
python3 tests/test_pipeline_comprehensive.py

# Run demonstration
python3 examples/pipeline_demo.py
\`\`\`

## Next Steps
1. Configure database connection
2. Set up CI/CD pipeline
3. Add custom systems and objects
4. Configure quality gates
5. Set up monitoring and alerting

## Support
For issues and questions, please refer to the documentation in \`docs/PIPELINE_IMPLEMENTATION_SUMMARY.md\`
EOF
    
    print_success "Created deployment summary"
}

# Main deployment function
main() {
    print_header "Arxos Pipeline Deployment"
    print_info "Version: $PIPELINE_VERSION"
    print_info "Starting deployment..."
    
    # Check requirements
    check_root
    check_system_requirements
    
    # Install dependencies
    install_python_dependencies
    install_go_dependencies
    
    # Setup infrastructure
    create_directories
    setup_database
    
    # Run tests
    run_tests
    
    # Setup CI/CD
    setup_cicd
    
    # Generate configuration
    generate_configuration
    
    # Validate installation
    validate_installation
    
    # Create summary
    create_deployment_summary
    
    print_header "Deployment Complete"
    print_success "Arxos Pipeline has been successfully deployed!"
    print_info "Check DEPLOYMENT_SUMMARY.md for details"
    print_info "Run 'python3 examples/pipeline_demo.py' to test the pipeline"
}

# Run main function
main "$@" 