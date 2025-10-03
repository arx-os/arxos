#!/bin/bash
# Integration Test Environment Setup Script
# Sets up the complete test environment for integration testing

set -e

echo "🚀 Setting up ArxOS Integration Test Environment"

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

# Check if Docker is installed
check_docker() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    print_success "Docker and Docker Compose are installed"
}

# Check if Go is installed
check_go() {
    if ! command -v go &> /dev/null; then
        print_error "Go is not installed. Please install Go first."
        exit 1
    fi
    
    GO_VERSION=$(go version | awk '{print $3}')
    print_success "Go is installed: $GO_VERSION"
}

# Check if Node.js is installed (for mobile tests)
check_node() {
    if ! command -v node &> /dev/null; then
        print_warning "Node.js is not installed. Mobile tests will be skipped."
        return 1
    fi
    
    NODE_VERSION=$(node --version)
    print_success "Node.js is installed: $NODE_VERSION"
    return 0
}

# Create test directories
create_test_directories() {
    print_status "Creating test directories..."
    
    mkdir -p test/fixtures/buildings
    mkdir -p test/fixtures/equipment
    mkdir -p test/fixtures/ifc_files
    mkdir -p test/fixtures/spatial_data
    mkdir -p test/helpers
    mkdir -p test/results
    mkdir -p test/logs
    
    print_success "Test directories created"
}

# Generate test data
generate_test_data() {
    print_status "Generating test data..."
    
    # Create sample IFC files
    cat > test/fixtures/ifc_files/simple_building.ifc << 'EOF'
ISO-10303-21;
HEADER;
FILE_DESCRIPTION(('IFC4'),'2;1');
FILE_NAME('simple_building.ifc','2024-01-01T00:00:00',('Test User'),('Test Organization'),'Test Software','Test Software Version','Test Identifier');
FILE_SCHEMA(('IFC4'));
ENDSEC;

DATA;
#1=IFCPROJECT('1','Test Project','Test Project Description',$,$,$,$,$,#2);
#2=IFCGEOMETRICREPRESENTATIONCONTEXT($,'Model',3,0.01,$,$);
ENDSEC;

END-ISO-10303-21;
EOF

    # Create sample building data
    cat > test/fixtures/buildings/sample_building.json << 'EOF'
{
  "id": "test-building-1",
  "name": "Sample Test Building",
  "address": "123 Test Street, Test City",
  "coordinates": {
    "x": 40.7128,
    "y": -74.0060,
    "z": 0
  },
  "floors": [
    {
      "id": "floor-1",
      "name": "Ground Floor",
      "level": 0,
      "rooms": [
        {
          "id": "room-1",
          "name": "Lobby",
          "bounds": {
            "min": {"x": 0, "y": 0, "z": 0},
            "max": {"x": 10, "y": 10, "z": 3}
          }
        }
      ]
    }
  ]
}
EOF

    # Create sample equipment data
    cat > test/fixtures/equipment/sample_equipment.json << 'EOF'
[
  {
    "id": "test-equipment-1",
    "name": "Sample HVAC Unit",
    "type": "HVAC",
    "model": "Test Model 1000",
    "status": "operational",
    "building_id": "test-building-1",
    "floor_id": "floor-1",
    "room_id": "room-1",
    "location": {
      "x": 5,
      "y": 5,
      "z": 1.5
    },
    "criticality": "medium",
    "installation_date": "2024-01-01T00:00:00Z",
    "last_maintenance": "2024-01-01T00:00:00Z",
    "next_maintenance": "2024-07-01T00:00:00Z"
  }
]
EOF

    print_success "Test data generated"
}

# Build test Docker images
build_test_images() {
    print_status "Building test Docker images..."
    
    # Build main test image
    docker build -f Dockerfile.test -t arxos-test:latest .
    
    # Build mobile test image
    if check_node; then
        docker build -f mobile/Dockerfile.test -t arxos-mobile-test:latest mobile/
    fi
    
    print_success "Test Docker images built"
}

# Start test services
start_test_services() {
    print_status "Starting test services..."
    
    # Start services with Docker Compose
    docker-compose -f test/config/docker-compose.test.yml up -d
    
    # Wait for services to be healthy
    print_status "Waiting for services to be healthy..."
    
    # Wait for PostgreSQL
    timeout 60 bash -c 'until docker-compose -f test/config/docker-compose.test.yml exec postgres-test pg_isready -U arxos_test -d arxos_test; do sleep 2; done'
    
    # Wait for Redis
    timeout 60 bash -c 'until docker-compose -f test/config/docker-compose.test.yml exec redis-test redis-cli ping; do sleep 2; done'
    
    # Wait for API server
    timeout 120 bash -c 'until curl -f http://localhost:8080/health; do sleep 5; done'
    
    print_success "All test services are healthy"
}

# Run database migrations
run_migrations() {
    print_status "Running database migrations..."
    
    # Run migrations
    docker-compose -f test/config/docker-compose.test.yml exec arxos-api-test go run cmd/migrate/main.go up
    
    print_success "Database migrations completed"
}

# Generate test data in database
seed_test_data() {
    print_status "Seeding test data..."
    
    # Run test data generator
    docker-compose -f test/config/docker-compose.test.yml exec test-data-generator
    
    print_success "Test data seeded"
}

# Run integration tests
run_integration_tests() {
    print_status "Running integration tests..."
    
    # Run service integration tests
    print_status "Running service integration tests..."
    docker-compose -f test/config/docker-compose.test.yml exec arxos-api-test go test -v ./test/integration/services/...
    
    # Run API integration tests
    print_status "Running API integration tests..."
    docker-compose -f test/config/docker-compose.test.yml exec arxos-api-test go test -v ./test/integration/api/...
    
    # Run database integration tests
    print_status "Running database integration tests..."
    docker-compose -f test/config/docker-compose.test.yml exec arxos-api-test go test -v ./test/integration/database/...
    
    # Run cross-platform integration tests
    print_status "Running cross-platform integration tests..."
    docker-compose -f test/config/docker-compose.test.yml exec arxos-api-test go test -v ./test/integration/cross_platform/...
    
    # Run performance tests
    print_status "Running performance tests..."
    docker-compose -f test/config/docker-compose.test.yml exec performance-test
    
    # Run mobile AR integration tests
    if check_node; then
        print_status "Running mobile AR integration tests..."
        docker-compose -f test/config/docker-compose.test.yml exec mobile-app-test npm test
    fi
    
    print_success "All integration tests completed"
}

# Generate test report
generate_test_report() {
    print_status "Generating test report..."
    
    # Collect test results
    docker-compose -f test/config/docker-compose.test.yml exec arxos-api-test go test -v ./test/integration/... -json > test/results/integration_test_results.json
    
    # Generate HTML report
    cat > test/results/test_report.html << 'EOF'
<!DOCTYPE html>
<html>
<head>
    <title>ArxOS Integration Test Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .header { background-color: #f0f0f0; padding: 20px; border-radius: 5px; }
        .test-result { margin: 10px 0; padding: 10px; border-radius: 5px; }
        .pass { background-color: #d4edda; border-left: 5px solid #28a745; }
        .fail { background-color: #f8d7da; border-left: 5px solid #dc3545; }
        .summary { background-color: #e2e3e5; padding: 15px; border-radius: 5px; margin: 20px 0; }
    </style>
</head>
<body>
    <div class="header">
        <h1>ArxOS Integration Test Report</h1>
        <p>Generated on: $(date)</p>
    </div>
    
    <div class="summary">
        <h2>Test Summary</h2>
        <p>Total Tests: <span id="total-tests">-</span></p>
        <p>Passed: <span id="passed-tests">-</span></p>
        <p>Failed: <span id="failed-tests">-</span></p>
        <p>Success Rate: <span id="success-rate">-</span></p>
    </div>
    
    <div id="test-results">
        <!-- Test results will be populated here -->
    </div>
    
    <script>
        // Parse test results and populate report
        // This would be implemented to read the JSON results and generate the report
    </script>
</body>
</html>
EOF
    
    print_success "Test report generated"
}

# Cleanup function
cleanup() {
    print_status "Cleaning up test environment..."
    
    # Stop services
    docker-compose -f test/config/docker-compose.test.yml down -v
    
    # Remove test images
    docker rmi arxos-test:latest 2>/dev/null || true
    docker rmi arxos-mobile-test:latest 2>/dev/null || true
    
    print_success "Test environment cleaned up"
}

# Main execution
main() {
    echo "ArxOS Integration Test Environment Setup"
    echo "========================================"
    
    # Check prerequisites
    check_docker
    check_go
    check_node || true
    
    # Setup test environment
    create_test_directories
    generate_test_data
    build_test_images
    start_test_services
    run_migrations
    seed_test_data
    
    # Run tests
    run_integration_tests
    generate_test_report
    
    print_success "Integration test environment setup completed successfully!"
    print_status "Test results are available in test/results/"
    print_status "Test report is available at test/results/test_report.html"
    
    # Ask if user wants to cleanup
    read -p "Do you want to cleanup the test environment? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        cleanup
    else
        print_status "Test environment is still running. Use 'docker-compose -f test/config/docker-compose.test.yml down' to stop it."
    fi
}

# Handle script interruption
trap cleanup EXIT

# Run main function
main "$@"
