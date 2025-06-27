#!/bin/bash

# Arxos Data Library Test Runner
# This script runs all tests for the Arxos platform

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test configuration
TEST_DB_NAME="arxos_test"
TEST_DB_HOST="localhost"
TEST_DB_PORT="5432"
TEST_DB_USER="postgres"

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

# Function to setup test database
setup_test_db() {
    print_status "Setting up test database..."
    
    # Check if PostgreSQL is running
    if ! pg_isready -h $TEST_DB_HOST -p $TEST_DB_PORT >/dev/null 2>&1; then
        print_error "PostgreSQL is not running on $TEST_DB_HOST:$TEST_DB_PORT"
        exit 1
    fi
    
    # Create test database if it doesn't exist
    if ! psql -h $TEST_DB_HOST -p $TEST_DB_PORT -U $TEST_DB_USER -lqt | cut -d \| -f 1 | grep -qw $TEST_DB_NAME; then
        print_status "Creating test database: $TEST_DB_NAME"
        createdb -h $TEST_DB_HOST -p $TEST_DB_PORT -U $TEST_DB_USER $TEST_DB_NAME
    else
        print_status "Test database already exists: $TEST_DB_NAME"
    fi
    
    # Set test database environment variable
    export DATABASE_URL="postgres://$TEST_DB_USER@$TEST_DB_HOST:$TEST_DB_PORT/$TEST_DB_NAME?sslmode=disable"
    export TESTING=true
    
    print_success "Test database setup complete"
}

# Function to run Go tests
run_go_tests() {
    print_status "Running Go unit and integration tests..."
    
    # Check if Go is installed
    if ! command_exists go; then
        print_error "Go is not installed"
        exit 1
    fi
    
    # Install test dependencies
    print_status "Installing test dependencies..."
    go mod tidy
    go get github.com/stretchr/testify/assert
    go get golang.org/x/crypto/bcrypt
    
    # Run tests with coverage
    print_status "Running tests with coverage..."
    go test -v -coverprofile=coverage.out -covermode=atomic ./tests/...
    
    # Generate coverage report
    if command_exists go tool cover; then
        print_status "Generating coverage report..."
        go tool cover -html=coverage.out -o coverage.html
        print_success "Coverage report generated: coverage.html"
    fi
    
    # Show coverage summary
    go tool cover -func=coverage.out
    
    print_success "Go tests completed"
}

# Function to run security tests
run_security_tests() {
    print_status "Running security-specific tests..."
    
    # Run security middleware tests
    go test -v ./tests/test_security.go
    
    # Run security integration tests
    go test -v ./tests/test_integration.go -run TestSecurity
    
    print_success "Security tests completed"
}

# Function to run compliance tests
run_compliance_tests() {
    print_status "Running compliance-specific tests..."
    
    # Run compliance integration tests
    go test -v ./tests/test_integration.go -run TestCompliance
    
    print_success "Compliance tests completed"
}

# Function to run export tests
run_export_tests() {
    print_status "Running export functionality tests..."
    
    # Run export integration tests
    go test -v ./tests/test_integration.go -run TestExport
    
    print_success "Export tests completed"
}

# Function to run model tests
run_model_tests() {
    print_status "Running model tests..."
    
    # Run model unit tests
    go test -v ./tests/test_models.go
    
    print_success "Model tests completed"
}

# Function to run E2E tests
run_e2e_tests() {
    print_status "Running E2E tests..."
    
    # Check if Node.js is installed for E2E tests
    if ! command_exists node; then
        print_warning "Node.js not found, skipping E2E tests"
        return
    fi
    
    # Check if npm is installed
    if ! command_exists npm; then
        print_warning "npm not found, skipping E2E tests"
        return
    fi
    
    # Install E2E test dependencies
    print_status "Installing E2E test dependencies..."
    cd ../arx-web-frontend
    npm install --silent
    
    # Run E2E tests
    print_status "Running E2E tests..."
    node tests/e2e_tests.js
    
    cd ../arx-backend
    print_success "E2E tests completed"
}

# Function to run performance tests
run_performance_tests() {
    print_status "Running performance tests..."
    
    # Check if Apache Bench is installed
    if ! command_exists ab; then
        print_warning "Apache Bench not found, skipping performance tests"
        return
    fi
    
    # Start the server in background for testing
    print_status "Starting server for performance testing..."
    go run main.go &
    SERVER_PID=$!
    
    # Wait for server to start
    sleep 5
    
    # Run performance tests
    print_status "Running API performance tests..."
    
    # Test rate limiting
    ab -n 100 -c 10 http://localhost:8080/api/export-activities
    
    # Test authentication endpoints
    ab -n 50 -c 5 -p test_data/login.json -T application/json http://localhost:8080/api/login
    
    # Stop server
    kill $SERVER_PID
    
    print_success "Performance tests completed"
}

# Function to run linting
run_linting() {
    print_status "Running code linting..."
    
    # Check if golangci-lint is installed
    if ! command_exists golangci-lint; then
        print_warning "golangci-lint not found, skipping linting"
        return
    fi
    
    # Run linting
    golangci-lint run
    
    print_success "Linting completed"
}

# Function to run security scanning
run_security_scan() {
    print_status "Running security scanning..."
    
    # Check if gosec is installed
    if ! command_exists gosec; then
        print_warning "gosec not found, skipping security scanning"
        return
    fi
    
    # Run security scanning
    gosec ./...
    
    print_success "Security scanning completed"
}

# Function to cleanup
cleanup() {
    print_status "Cleaning up test artifacts..."
    
    # Remove coverage files
    rm -f coverage.out coverage.html
    
    # Clean test database
    if [ "$CLEANUP_DB" = "true" ]; then
        print_status "Cleaning up test database..."
        dropdb -h $TEST_DB_HOST -p $TEST_DB_PORT -U $TEST_DB_USER $TEST_DB_NAME 2>/dev/null || true
    fi
    
    print_success "Cleanup completed"
}

# Function to show help
show_help() {
    echo "Arxos Data Library Test Runner"
    echo ""
    echo "Usage: $0 [OPTIONS] [TEST_TYPES]"
    echo ""
    echo "Options:"
    echo "  -h, --help              Show this help message"
    echo "  -v, --verbose           Enable verbose output"
    echo "  -c, --cleanup           Clean up test database after tests"
    echo "  --db-host HOST          Database host (default: localhost)"
    echo "  --db-port PORT          Database port (default: 5432)"
    echo "  --db-user USER          Database user (default: postgres)"
    echo ""
    echo "Test Types:"
    echo "  all                     Run all tests (default)"
    echo "  unit                    Run unit tests only"
    echo "  integration             Run integration tests only"
    echo "  e2e                     Run E2E tests only"
    echo "  security                Run security tests only"
    echo "  compliance              Run compliance tests only"
    echo "  export                  Run export tests only"
    echo "  models                  Run model tests only"
    echo "  performance             Run performance tests only"
    echo "  lint                    Run linting only"
    echo "  scan                    Run security scanning only"
    echo ""
    echo "Examples:"
    echo "  $0                      Run all tests"
    echo "  $0 unit integration     Run unit and integration tests"
    echo "  $0 -c security          Run security tests and cleanup"
    echo "  $0 --verbose all        Run all tests with verbose output"
}

# Parse command line arguments
VERBOSE=false
CLEANUP_DB=false
TEST_TYPES="all"

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -c|--cleanup)
            CLEANUP_DB=true
            shift
            ;;
        --db-host)
            TEST_DB_HOST="$2"
            shift 2
            ;;
        --db-port)
            TEST_DB_PORT="$2"
            shift 2
            ;;
        --db-user)
            TEST_DB_USER="$2"
            shift 2
            ;;
        all|unit|integration|e2e|security|compliance|export|models|performance|lint|scan)
            TEST_TYPES="$1"
            shift
            ;;
        *)
            print_error "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Set verbose flag for Go tests
if [ "$VERBOSE" = "true" ]; then
    export GO_TEST_VERBOSE=true
fi

# Main execution
main() {
    print_status "Starting Arxos Data Library Test Suite..."
    print_status "Test types: $TEST_TYPES"
    print_status "Database: $TEST_DB_HOST:$TEST_DB_PORT/$TEST_DB_NAME"
    
    # Setup test environment
    setup_test_db
    
    # Run tests based on type
    case $TEST_TYPES in
        all)
            run_linting
            run_security_scan
            run_model_tests
            run_go_tests
            run_security_tests
            run_compliance_tests
            run_export_tests
            run_performance_tests
            run_e2e_tests
            ;;
        unit)
            run_model_tests
            run_go_tests
            ;;
        integration)
            run_go_tests
            ;;
        e2e)
            run_e2e_tests
            ;;
        security)
            run_security_tests
            ;;
        compliance)
            run_compliance_tests
            ;;
        export)
            run_export_tests
            ;;
        models)
            run_model_tests
            ;;
        performance)
            run_performance_tests
            ;;
        lint)
            run_linting
            ;;
        scan)
            run_security_scan
            ;;
        *)
            print_error "Unknown test type: $TEST_TYPES"
            exit 1
            ;;
    esac
    
    # Cleanup
    cleanup
    
    print_success "All tests completed successfully!"
}

# Run main function
main "$@" 