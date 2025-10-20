#!/bin/bash

# ArxOS Test Runner
# Runs comprehensive tests for the Clean Architecture implementation

set -e

echo "🚀 Starting ArxOS Test Suite"
echo "=============================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test configuration
TEST_TIMEOUT="10m"
COVERAGE_THRESHOLD=80
VERBOSE=false
RACE_DETECTION=true
BENCHMARK=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -b|--benchmark)
            BENCHMARK=true
            shift
            ;;
        -r|--race)
            RACE_DETECTION=true
            shift
            ;;
        -c|--coverage)
            COVERAGE_THRESHOLD="$2"
            shift 2
            ;;
        -t|--timeout)
            TEST_TIMEOUT="$2"
            shift 2
            ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo "Options:"
            echo "  -v, --verbose     Enable verbose output"
            echo "  -b, --benchmark   Run benchmarks"
            echo "  -r, --race        Enable race detection"
            echo "  -c, --coverage    Set coverage threshold (default: 80)"
            echo "  -t, --timeout     Set test timeout (default: 10m)"
            echo "  -h, --help        Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Function to print colored output
print_status() {
    local status=$1
    local message=$2
    case $status in
        "INFO")
            echo -e "${BLUE}ℹ️  $message${NC}"
            ;;
        "SUCCESS")
            echo -e "${GREEN}✅ $message${NC}"
            ;;
        "WARNING")
            echo -e "${YELLOW}⚠️  $message${NC}"
            ;;
        "ERROR")
            echo -e "${RED}❌ $message${NC}"
            ;;
    esac
}

# Function to run tests with proper flags
run_tests() {
    local package=$1
    local test_name=$2
    local flags=""
    
    if [ "$VERBOSE" = true ]; then
        flags="$flags -v"
    fi
    
    if [ "$RACE_DETECTION" = true ]; then
        flags="$flags -race"
    fi
    
    if [ "$BENCHMARK" = true ]; then
        flags="$flags -bench=."
    fi
    
    print_status "INFO" "Running tests for $test_name..."
    
    if go test $flags -timeout="$TEST_TIMEOUT" "$package"; then
        print_status "SUCCESS" "$test_name tests passed"
        return 0
    else
        print_status "ERROR" "$test_name tests failed"
        return 1
    fi
}

# Function to run tests with coverage
run_tests_with_coverage() {
    local package=$1
    local test_name=$2
    local coverage_file="coverage_${test_name}.out"
    
    print_status "INFO" "Running tests with coverage for $test_name..."
    
    if go test -race -coverprofile="$coverage_file" -covermode=atomic -timeout="$TEST_TIMEOUT" "$package"; then
        local coverage=$(go tool cover -func="$coverage_file" | grep total | awk '{print $3}' | sed 's/%//')
        print_status "SUCCESS" "$test_name tests passed with ${coverage}% coverage"
        
        if (( $(echo "$coverage < $COVERAGE_THRESHOLD" | bc -l) )); then
            print_status "WARNING" "Coverage ${coverage}% is below threshold ${COVERAGE_THRESHOLD}%"
        fi
        
        return 0
    else
        print_status "ERROR" "$test_name tests failed"
        return 1
    fi
}

# Check if Go is installed
if ! command -v go &> /dev/null; then
    print_status "ERROR" "Go is not installed or not in PATH"
    exit 1
fi

# Check Go version
GO_VERSION=$(go version | awk '{print $3}' | sed 's/go//')
print_status "INFO" "Using Go version $GO_VERSION"

# Check if bc is installed for coverage comparison
if ! command -v bc &> /dev/null; then
    print_status "WARNING" "bc is not installed, coverage threshold checking will be skipped"
fi

# Create coverage directory
mkdir -p coverage

# Change to project root
cd "$(dirname "$0")/.."

# Run tests for each package
print_status "INFO" "Starting test execution..."

# 1. Dependency Injection Tests
run_tests_with_coverage "./internal/app/di" "Dependency Injection"

# 2. WebSocket Tests
run_tests_with_coverage "./internal/infra/messaging" "WebSocket"

# 3. Domain Tests
run_tests_with_coverage "./internal/domain/building" "Building Domain"
run_tests_with_coverage "./internal/domain/equipment" "Equipment Domain"
run_tests_with_coverage "./internal/domain/spatial" "Spatial Domain"
run_tests_with_coverage "./internal/domain/analytics" "Analytics Domain"
run_tests_with_coverage "./internal/domain/workflow" "Workflow Domain"
run_tests_with_coverage "./internal/domain/messaging" "Messaging Domain"

# 4. Application Tests
run_tests_with_coverage "./internal/app/handlers" "HTTP Handlers"
run_tests_with_coverage "./internal/app/middleware" "Middleware"
run_tests_with_coverage "./internal/app/routes" "Routes"

# 5. Infrastructure Tests
run_tests_with_coverage "./internal/infra/database" "Database"
run_tests_with_coverage "./internal/infra/cache" "Cache"
run_tests_with_coverage "./internal/infra/storage" "Storage"

# 6. Integration Tests
run_tests_with_coverage "./internal/app" "Integration"

# 7. Command Tests
run_tests_with_coverage "./cmd/arx" "CLI Commands"

# 8. Package Tests
run_tests_with_coverage "./pkg/models" "Models"
run_tests_with_coverage "./pkg/errors" "Errors"
run_tests_with_coverage "./pkg/sync" "Sync"

# 9. Common Tests
run_tests_with_coverage "./internal/common/logger" "Logger"
run_tests_with_coverage "./internal/common/progress" "Progress"
run_tests_with_coverage "./internal/common/resources" "Resources"
run_tests_with_coverage "./internal/common/retry" "Retry"
run_tests_with_coverage "./internal/common/state" "State"

# 10. Configuration Tests
run_tests_with_coverage "./internal/config" "Configuration"

# 11. Validation Tests
run_tests_with_coverage "./internal/validation" "Validation"

# 12. BIM Tests
run_tests_with_coverage "./internal/bim" "BIM"

# 13. Cache Tests
run_tests_with_coverage "./internal/cache" "Cache Implementation"

# 14. Analytics Tests
run_tests_with_coverage "./internal/analytics" "Analytics Implementation"

# 15. Workflow Tests
run_tests_with_coverage "./internal/workflow" "Workflow Implementation"

# 16. Hardware Tests
run_tests_with_coverage "./internal/hardware" "Hardware"

# 17. Facility Tests
run_tests_with_coverage "./internal/facility" "Facility"

# 18. Integration Tests
run_tests_with_coverage "./internal/integration" "Integration Implementation"

# 19. Services Tests
run_tests_with_coverage "./internal/services" "Services"

# 20. API Tests
run_tests_with_coverage "./internal/api" "API"

# 21. Daemon Tests
run_tests_with_coverage "./internal/daemon" "Daemon"

# 22. Telemetry Tests
run_tests_with_coverage "./internal/telemetry" "Telemetry"

# 23. Simulation Tests
run_tests_with_coverage "./internal/simulation" "Simulation"

# 24. Rendering Tests
run_tests_with_coverage "./internal/rendering" "Rendering"

# 25. Search Tests
run_tests_with_coverage "./internal/search" "Search"

# 26. Security Tests
run_tests_with_coverage "./internal/security" "Security"

# 27. Notifications Tests
run_tests_with_coverage "./internal/notifications" "Notifications"

# 28. Email Tests
run_tests_with_coverage "./internal/email" "Email"

# 29. Ecosystem Tests
run_tests_with_coverage "./internal/ecosystem" "Ecosystem"

# 30. Core Tests
run_tests_with_coverage "./internal/core" "Core"

# 31. Interfaces Tests
run_tests_with_coverage "./internal/interfaces" "Interfaces"

# 32. IT Tests
run_tests_with_coverage "./internal/it" "IT"

# 33. Metrics Tests
run_tests_with_coverage "./internal/metrics" "Metrics"

# 34. Spatial Tests
run_tests_with_coverage "./internal/spatial" "Spatial"

# 35. Storage Tests
run_tests_with_coverage "./internal/storage" "Storage Implementation"

# 36. Database Tests
run_tests_with_coverage "./internal/database" "Database Implementation"

# 37. Adapters Tests
run_tests_with_coverage "./internal/adapters" "Adapters"

# 38. Auth Tests
run_tests_with_coverage "./internal/auth" "Authentication"

# 39. Compliance Tests
run_tests_with_coverage "./internal/compliance" "Compliance"

# 40. Connections Tests
run_tests_with_coverage "./internal/connections" "Connections"

# 41. Converter Tests
run_tests_with_coverage "./internal/converter" "Converter"

# 42. Exporter Tests
run_tests_with_coverage "./internal/exporter" "Exporter"

# 43. Importer Tests
run_tests_with_coverage "./internal/importer" "Importer"

# 44. Handlers Tests
run_tests_with_coverage "./internal/handlers" "Handlers"

# 45. Migration Tests
run_tests_with_coverage "./internal/migration" "Migration"

# 46. Visualization Tests
run_tests_with_coverage "./internal/visualization" "Visualization"

# 47. Test Tests
run_tests_with_coverage "./test" "Test Utilities"

# Generate overall coverage report
print_status "INFO" "Generating overall coverage report..."

# Combine all coverage files
echo "mode: atomic" > coverage/coverage.out
for file in coverage_*.out; do
    if [ -f "$file" ]; then
        tail -n +2 "$file" >> coverage/coverage.out
    fi
done

# Generate HTML coverage report
go tool cover -html=coverage/coverage.out -o coverage/coverage.html

# Generate coverage summary
go tool cover -func=coverage/coverage.out > coverage/coverage.txt

# Display coverage summary
print_status "INFO" "Coverage Summary:"
cat coverage/coverage.txt | grep total

# Clean up individual coverage files
rm -f coverage_*.out

# Run benchmarks if requested
if [ "$BENCHMARK" = true ]; then
    print_status "INFO" "Running benchmarks..."
    go test -bench=. -benchmem ./...
fi

# Run race detection tests
if [ "$RACE_DETECTION" = true ]; then
    print_status "INFO" "Running race detection tests..."
    go test -race ./...
fi

# Run vet
print_status "INFO" "Running go vet..."
go vet ./...

# Run fmt check
print_status "INFO" "Checking code formatting..."
if go fmt ./... | grep -q .; then
    print_status "WARNING" "Code formatting issues found. Run 'go fmt ./...' to fix."
else
    print_status "SUCCESS" "Code formatting is correct"
fi

# Run mod tidy check
print_status "INFO" "Checking go.mod..."
if go mod tidy -v 2>&1 | grep -q "go: downloading\|go: extracting"; then
    print_status "WARNING" "go.mod needs tidying. Run 'go mod tidy' to fix."
else
    print_status "SUCCESS" "go.mod is tidy"
fi

# Run security check if gosec is available
if command -v gosec &> /dev/null; then
    print_status "INFO" "Running security scan..."
    gosec ./...
else
    print_status "WARNING" "gosec is not installed. Install it for security scanning."
fi

# Run static analysis if staticcheck is available
if command -v staticcheck &> /dev/null; then
    print_status "INFO" "Running static analysis..."
    staticcheck ./...
else
    print_status "WARNING" "staticcheck is not installed. Install it for static analysis."
fi

print_status "SUCCESS" "All tests completed successfully!"
print_status "INFO" "Coverage report available at: coverage/coverage.html"
print_status "INFO" "Coverage summary available at: coverage/coverage.txt"

echo ""
echo "🎉 Test Suite Complete!"
echo "========================"
