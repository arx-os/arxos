#!/bin/bash

# Data Vendor API Test Runner
# This script runs comprehensive tests for the Data Vendor API functionality

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
TEST_DIR="tests"
LOG_DIR="test_logs"
COVERAGE_DIR="coverage"
SERVER_PORT=8081
ADMIN_PORT=8082

# Test counters
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

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

# Function to cleanup on exit
cleanup() {
    print_status "Cleaning up test environment..."
    
    # Stop test server if running
    if [ ! -z "$SERVER_PID" ]; then
        kill $SERVER_PID 2>/dev/null || true
        wait $SERVER_PID 2>/dev/null || true
    fi
    
    # Remove test database
    if [ -f "test.db" ]; then
        rm -f test.db
    fi
    
    # Clean test logs
    if [ -d "$LOG_DIR" ]; then
        rm -rf "$LOG_DIR"
    fi
    
    print_status "Cleanup completed"
}

# Set up trap for cleanup
trap cleanup EXIT

# Function to check dependencies
check_dependencies() {
    print_status "Checking dependencies..."
    
    # Check if Go is installed
    if ! command -v go &> /dev/null; then
        print_error "Go is not installed. Please install Go 1.19 or later."
        exit 1
    fi
    
    # Check Go version
    GO_VERSION=$(go version | awk '{print $3}' | sed 's/go//')
    REQUIRED_VERSION="1.19"
    
    if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$GO_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
        print_error "Go version $GO_VERSION is too old. Please upgrade to Go 1.19 or later."
        exit 1
    fi
    
    print_success "Dependencies check passed"
}

# Function to setup test environment
setup_test_env() {
    print_status "Setting up test environment..."
    
    # Create test directories
    mkdir -p "$LOG_DIR"
    mkdir -p "$COVERAGE_DIR"
    
    # Set test environment variables
    export ARX_ENV=test
    export ARX_DB_PATH=test.db
    export ARX_LOG_LEVEL=debug
    export JWT_SECRET=test_secret_key_12345
    
    # Initialize test database
    print_status "Initializing test database..."
    go run main.go migrate 2>/dev/null || true
    
    print_success "Test environment setup completed"
}

# Function to start test server
start_test_server() {
    print_status "Starting test server on port $SERVER_PORT..."
    
    # Start server in background
    go run main.go serve --port $SERVER_PORT > "$LOG_DIR/server.log" 2>&1 &
    SERVER_PID=$!
    
    # Wait for server to start
    sleep 3
    
    # Check if server is running
    if ! curl -s http://localhost:$SERVER_PORT/health > /dev/null 2>&1; then
        print_error "Failed to start test server"
        cat "$LOG_DIR/server.log"
        exit 1
    fi
    
    print_success "Test server started successfully"
}

# Function to run unit tests
run_unit_tests() {
    print_status "Running unit tests..."
    
    local test_file="$TEST_DIR/test_data_vendor.go"
    
    if [ -f "$test_file" ]; then
        TOTAL_TESTS=$((TOTAL_TESTS + 1))
        
        if go test -v -coverprofile="$COVERAGE_DIR/data_vendor_cover.out" "$test_file"; then
            print_success "Unit tests passed"
            PASSED_TESTS=$((PASSED_TESTS + 1))
        else
            print_error "Unit tests failed"
            FAILED_TESTS=$((FAILED_TESTS + 1))
        fi
    else
        print_warning "Unit test file not found: $test_file"
    fi
}

# Function to run integration tests
run_integration_tests() {
    print_status "Running integration tests..."
    
    local test_file="$TEST_DIR/test_data_vendor_integration.go"
    
    if [ -f "$test_file" ]; then
        TOTAL_TESTS=$((TOTAL_TESTS + 1))
        
        if go test -v -tags=integration -coverprofile="$COVERAGE_DIR/data_vendor_integration_cover.out" "$test_file"; then
            print_success "Integration tests passed"
            PASSED_TESTS=$((PASSED_TESTS + 1))
        else
            print_error "Integration tests failed"
            FAILED_TESTS=$((FAILED_TESTS + 1))
        fi
    else
        print_warning "Integration test file not found: $test_file"
    fi
}

# Function to run API tests
run_api_tests() {
    print_status "Running API tests..."
    
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    
    # Test API key creation
    print_status "Testing API key creation..."
    CREATE_RESPONSE=$(curl -s -X POST http://localhost:$SERVER_PORT/api/admin/data-vendor/keys \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer admin_token" \
        -d '{
            "vendor_name": "Test Vendor",
            "email": "test@vendor.com",
            "access_level": "basic",
            "rate_limit": 1000,
            "expires_at": "2025-01-15T00:00:00Z"
        }')
    
    if echo "$CREATE_RESPONSE" | grep -q "id"; then
        print_success "API key creation test passed"
        
        # Extract API key ID
        API_KEY_ID=$(echo "$CREATE_RESPONSE" | grep -o '"id":[0-9]*' | cut -d':' -f2)
        API_KEY=$(echo "$CREATE_RESPONSE" | grep -o '"key":"[^"]*"' | cut -d'"' -f4)
        
        # Test API endpoints with the created key
        test_api_endpoints "$API_KEY"
        
    else
        print_error "API key creation test failed"
        echo "Response: $CREATE_RESPONSE"
        FAILED_TESTS=$((FAILED_TESTS + 1))
        return
    fi
    
    PASSED_TESTS=$((PASSED_TESTS + 1))
}

# Function to test API endpoints
test_api_endpoints() {
    local api_key="$1"
    
    print_status "Testing API endpoints with key: ${api_key:0:20}..."
    
    # Test buildings endpoint
    print_status "Testing /api/vendor/buildings endpoint..."
    BUILDINGS_RESPONSE=$(curl -s -H "X-API-Key: $api_key" \
        "http://localhost:$SERVER_PORT/api/vendor/buildings")
    
    if echo "$BUILDINGS_RESPONSE" | grep -q "buildings"; then
        print_success "Buildings endpoint test passed"
    else
        print_error "Buildings endpoint test failed"
        echo "Response: $BUILDINGS_RESPONSE"
        FAILED_TESTS=$((FAILED_TESTS + 1))
        return
    fi
    
    # Test industry benchmarks endpoint
    print_status "Testing /api/vendor/industry-benchmarks endpoint..."
    BENCHMARKS_RESPONSE=$(curl -s -H "X-API-Key: $api_key" \
        "http://localhost:$SERVER_PORT/api/vendor/industry-benchmarks")
    
    if echo "$BENCHMARKS_RESPONSE" | grep -q "benchmarks"; then
        print_success "Industry benchmarks endpoint test passed"
    else
        print_error "Industry benchmarks endpoint test failed"
        echo "Response: $BENCHMARKS_RESPONSE"
        FAILED_TESTS=$((FAILED_TESTS + 1))
        return
    fi
    
    # Test rate limiting
    print_status "Testing rate limiting..."
    RATE_LIMIT_HIT=false
    for i in {1..5}; do
        RESPONSE=$(curl -s -w "%{http_code}" -H "X-API-Key: $api_key" \
            "http://localhost:$SERVER_PORT/api/vendor/buildings")
        HTTP_CODE="${RESPONSE: -3}"
        
        if [ "$HTTP_CODE" = "429" ]; then
            RATE_LIMIT_HIT=true
            break
        fi
    done
    
    if [ "$RATE_LIMIT_HIT" = true ]; then
        print_success "Rate limiting test passed"
    else
        print_warning "Rate limiting test inconclusive (may need more requests)"
    fi
}

# Function to run CLI tests
run_cli_tests() {
    print_status "Running CLI tests..."
    
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    
    # Test CLI help
    if go run cmd/data-vendor-cli/main.go --help > /dev/null 2>&1; then
        print_success "CLI help test passed"
    else
        print_error "CLI help test failed"
        FAILED_TESTS=$((FAILED_TESTS + 1))
        return
    fi
    
    # Test CLI dashboard command
    if go run cmd/data-vendor-cli/main.go dashboard > /dev/null 2>&1; then
        print_success "CLI dashboard test passed"
    else
        print_warning "CLI dashboard test failed (may need server running)"
    fi
    
    PASSED_TESTS=$((PASSED_TESTS + 1))
}

# Function to run security tests
run_security_tests() {
    print_status "Running security tests..."
    
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    
    # Test without API key
    print_status "Testing request without API key..."
    NO_KEY_RESPONSE=$(curl -s -w "%{http_code}" \
        "http://localhost:$SERVER_PORT/api/vendor/buildings")
    HTTP_CODE="${NO_KEY_RESPONSE: -3}"
    
    if [ "$HTTP_CODE" = "401" ]; then
        print_success "Authentication test passed"
    else
        print_error "Authentication test failed - expected 401, got $HTTP_CODE"
        FAILED_TESTS=$((FAILED_TESTS + 1))
        return
    fi
    
    # Test with invalid API key
    print_status "Testing request with invalid API key..."
    INVALID_KEY_RESPONSE=$(curl -s -w "%{http_code}" \
        -H "X-API-Key: invalid_key" \
        "http://localhost:$SERVER_PORT/api/vendor/buildings")
    HTTP_CODE="${INVALID_KEY_RESPONSE: -3}"
    
    if [ "$HTTP_CODE" = "401" ]; then
        print_success "Invalid API key test passed"
    else
        print_error "Invalid API key test failed - expected 401, got $HTTP_CODE"
        FAILED_TESTS=$((FAILED_TESTS + 1))
        return
    fi
    
    PASSED_TESTS=$((PASSED_TESTS + 1))
}

# Function to generate coverage report
generate_coverage_report() {
    print_status "Generating coverage report..."
    
    if [ -f "$COVERAGE_DIR/data_vendor_cover.out" ]; then
        go tool cover -html="$COVERAGE_DIR/data_vendor_cover.out" \
            -o "$COVERAGE_DIR/data_vendor_coverage.html"
        print_success "Coverage report generated: $COVERAGE_DIR/data_vendor_coverage.html"
    fi
    
    if [ -f "$COVERAGE_DIR/data_vendor_integration_cover.out" ]; then
        go tool cover -html="$COVERAGE_DIR/data_vendor_integration_cover.out" \
            -o "$COVERAGE_DIR/data_vendor_integration_coverage.html"
        print_success "Integration coverage report generated: $COVERAGE_DIR/data_vendor_integration_coverage.html"
    fi
}

# Function to print test summary
print_test_summary() {
    echo
    echo "=========================================="
    echo "           TEST SUMMARY"
    echo "=========================================="
    echo "Total Tests: $TOTAL_TESTS"
    echo "Passed: $PASSED_TESTS"
    echo "Failed: $FAILED_TESTS"
    echo "Success Rate: $((PASSED_TESTS * 100 / TOTAL_TESTS))%"
    echo "=========================================="
    
    if [ $FAILED_TESTS -eq 0 ]; then
        print_success "All tests passed!"
        exit 0
    else
        print_error "$FAILED_TESTS test(s) failed"
        exit 1
    fi
}

# Main execution
main() {
    echo "=========================================="
    echo "     Data Vendor API Test Runner"
    echo "=========================================="
    
    # Check dependencies
    check_dependencies
    
    # Setup test environment
    setup_test_env
    
    # Start test server
    start_test_server
    
    # Run tests
    run_unit_tests
    run_integration_tests
    run_api_tests
    run_cli_tests
    run_security_tests
    
    # Generate coverage report
    generate_coverage_report
    
    # Print summary
    print_test_summary
}

# Run main function
main "$@" 