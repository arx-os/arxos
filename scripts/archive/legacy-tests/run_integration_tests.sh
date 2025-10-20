#!/bin/bash

# Integration Test Runner for ArxOS
# This script runs integration tests with proper environment setup

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
POSTGIS_HOST=${POSTGIS_HOST:-"localhost"}
POSTGIS_PORT=${POSTGIS_PORT:-"5432"}
POSTGIS_DB=${POSTGIS_DB:-"arxos_test"}
POSTGIS_USER=${POSTGIS_USER:-"postgres"}
POSTGIS_PASSWORD=${POSTGIS_PASSWORD:-""}
TEST_TIMEOUT=${TEST_TIMEOUT:-"10m"}
VERBOSE=${VERBOSE:-"false"}

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

# Function to check if PostGIS is available
check_postgis() {
    print_status "Checking PostGIS connection..."
    
    if [ -z "$POSTGIS_PASSWORD" ]; then
        print_error "POSTGIS_PASSWORD environment variable is required"
        print_status "Please set POSTGIS_PASSWORD and try again"
        print_status "Example: POSTGIS_PASSWORD=yourpassword $0"
        exit 1
    fi
    
    # Test connection
    if ! PGPASSWORD="$POSTGIS_PASSWORD" psql -h "$POSTGIS_HOST" -p "$POSTGIS_PORT" -U "$POSTGIS_USER" -d "$POSTGIS_DB" -c "SELECT 1;" > /dev/null 2>&1; then
        print_error "Cannot connect to PostGIS database"
        print_status "Please check your PostGIS connection settings:"
        print_status "  Host: $POSTGIS_HOST"
        print_status "  Port: $POSTGIS_PORT"
        print_status "  Database: $POSTGIS_DB"
        print_status "  User: $POSTGIS_USER"
        exit 1
    fi
    
    print_success "PostGIS connection successful"
}

# Function to setup test database
setup_test_database() {
    print_status "Setting up test database..."
    
    # Create test database if it doesn't exist
    PGPASSWORD="$POSTGIS_PASSWORD" psql -h "$POSTGIS_HOST" -p "$POSTGIS_PORT" -U "$POSTGIS_USER" -d postgres -c "CREATE DATABASE $POSTGIS_DB;" 2>/dev/null || true
    
    # Enable PostGIS extension
    PGPASSWORD="$POSTGIS_PASSWORD" psql -h "$POSTGIS_HOST" -p "$POSTGIS_PORT" -U "$POSTGIS_USER" -d "$POSTGIS_DB" -c "CREATE EXTENSION IF NOT EXISTS postgis;" > /dev/null 2>&1 || true
    
    print_success "Test database setup complete"
}

# Function to run integration tests
run_tests() {
    print_status "Running integration tests..."
    
    # Set environment variables
    export POSTGIS_HOST
    export POSTGIS_PORT
    export POSTGIS_DB
    export POSTGIS_USER
    export POSTGIS_PASSWORD
    
    # Build test command
    TEST_CMD="go test -tags=integration -timeout=$TEST_TIMEOUT"
    
    if [ "$VERBOSE" = "true" ]; then
        TEST_CMD="$TEST_CMD -v"
    fi
    
    # Add test packages
    TEST_CMD="$TEST_CMD ./internal/integration/..."
    
    print_status "Running: $TEST_CMD"
    
    # Run tests
    if eval $TEST_CMD; then
        print_success "All integration tests passed!"
    else
        print_error "Some integration tests failed"
        exit 1
    fi
}

# Function to cleanup test database
cleanup_test_database() {
    print_status "Cleaning up test database..."
    
    # Drop test database
    PGPASSWORD="$POSTGIS_PASSWORD" psql -h "$POSTGIS_HOST" -p "$POSTGIS_PORT" -U "$POSTGIS_USER" -d postgres -c "DROP DATABASE IF EXISTS $POSTGIS_DB;" > /dev/null 2>&1 || true
    
    print_success "Test database cleanup complete"
}

# Function to show help
show_help() {
    echo "ArxOS Integration Test Runner"
    echo ""
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -h, --help              Show this help message"
    echo "  -v, --verbose           Run tests in verbose mode"
    echo "  --cleanup               Cleanup test database after tests"
    echo "  --no-setup              Skip database setup"
    echo "  --timeout TIMEOUT       Set test timeout (default: 10m)"
    echo ""
    echo "Environment Variables:"
    echo "  POSTGIS_HOST            PostGIS host (default: localhost)"
    echo "  POSTGIS_PORT            PostGIS port (default: 5432)"
    echo "  POSTGIS_DB              Test database name (default: arxos_test)"
    echo "  POSTGIS_USER            PostGIS user (default: postgres)"
    echo "  POSTGIS_PASSWORD        PostGIS password (required)"
    echo ""
    echo "Examples:"
    echo "  $0                                    # Run tests with default settings"
    echo "  $0 -v                                 # Run tests in verbose mode"
    echo "  $0 --cleanup                          # Run tests and cleanup database"
    echo "  POSTGIS_PASSWORD=mypass $0            # Run tests with custom password"
}

# Parse command line arguments
CLEANUP=false
NO_SETUP=false

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
        --cleanup)
            CLEANUP=true
            shift
            ;;
        --no-setup)
            NO_SETUP=true
            shift
            ;;
        --timeout)
            TEST_TIMEOUT="$2"
            shift 2
            ;;
        *)
            print_error "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Main execution
main() {
    print_status "Starting ArxOS Integration Tests"
    print_status "================================="
    
    # Check PostGIS connection
    check_postgis
    
    # Setup test database
    if [ "$NO_SETUP" = "false" ]; then
        setup_test_database
    fi
    
    # Run tests
    run_tests
    
    # Cleanup if requested
    if [ "$CLEANUP" = "true" ]; then
        cleanup_test_database
    fi
    
    print_success "Integration test run completed successfully!"
}

# Run main function
main
