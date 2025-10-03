# ArxOS Integration Testing Suite

## Overview

The ArxOS Integration Testing Suite provides comprehensive testing across all platform components - CLI, Web API, Mobile AR, and Backend Services. This suite ensures that the "Git of Buildings" platform functions as a cohesive system with proper data consistency, real-time synchronization, and cross-platform compatibility.

## 🏗️ **Integration Testing Architecture**

### **Testing Pyramid**
```
┌─────────────────────────────────────────────────────────────┐
│                    E2E Tests (10%)                         │
│  • Full user workflows • Cross-platform scenarios         │
├─────────────────────────────────────────────────────────────┤
│                 Integration Tests (30%)                     │
│  • Service-to-service • API integration • Database ops     │
├─────────────────────────────────────────────────────────────┤
│                   Unit Tests (60%)                          │
│  • Component isolation • Business logic • Edge cases      │
└─────────────────────────────────────────────────────────────┘
```

### **Test Categories**

1. **Service Integration Tests** - Backend service interactions
2. **API Integration Tests** - HTTP/GraphQL/WebSocket endpoints  
3. **Database Integration Tests** - PostGIS operations and transactions
4. **Mobile Integration Tests** - React Native app functionality
5. **AR Integration Tests** - ARKit/ARCore with backend sync
6. **Cross-Platform Tests** - CLI ↔ Web ↔ Mobile interactions
7. **Performance Integration Tests** - Load testing and bottlenecks
8. **Security Integration Tests** - Authentication and authorization flows

## 📁 **Directory Structure**

```
test/
├── integration/
│   ├── services/           # Service-to-service integration
│   │   ├── building_service_test.go
│   │   ├── equipment_service_test.go
│   │   ├── ifc_service_test.go
│   │   └── sync_service_test.go
│   ├── api/                # API endpoint integration
│   │   ├── http_api_test.go
│   │   ├── graphql_api_test.go
│   │   ├── websocket_test.go
│   │   └── auth_api_test.go
│   ├── database/           # Database integration
│   │   ├── postgis_test.go
│   │   ├── spatial_queries_test.go
│   │   ├── transactions_test.go
│   │   └── migrations_test.go
│   ├── mobile/             # Mobile app integration
│   │   ├── ar_integration_test.ts
│   │   ├── offline_sync_test.ts
│   │   ├── navigation_test.ts
│   │   └── equipment_management_test.ts
│   ├── cross_platform/     # Cross-platform workflows
│   │   ├── cli_to_web_test.go
│   │   ├── mobile_to_backend_test.ts
│   │   └── real_time_sync_test.go
│   ├── performance/        # Performance integration
│   │   ├── load_test.go
│   │   ├── stress_test.go
│   │   └── benchmark_test.go
│   └── security/           # Security integration
│       ├── auth_flow_test.go
│       ├── rbac_test.go
│       └── data_encryption_test.go
├── fixtures/               # Test data and fixtures
│   ├── buildings/
│   ├── equipment/
│   ├── ifc_files/
│   └── spatial_data/
├── helpers/                # Test utilities and helpers
│   ├── test_server.go
│   ├── mock_services.go
│   ├── test_data_builder.go
│   └── assertions.go
├── config/                 # Test configuration
│   ├── test_config.yaml
│   ├── docker-compose.test.yml
│   └── test_environment.sh
└── integration_test_runner.go
```

## 🚀 **Quick Start**

### **Prerequisites**
- Docker and Docker Compose
- Go 1.21+
- Node.js 18+ (for mobile tests)
- PostgreSQL with PostGIS extension

### **Setup Test Environment**
```bash
# Clone the repository
git clone https://github.com/arx-os/arxos.git
cd arxos

# Make test environment script executable
chmod +x test/config/test_environment.sh

# Run the test environment setup
./test/config/test_environment.sh
```

### **Run All Integration Tests**
```bash
# Run all integration tests
go run test/integration_test_runner.go

# Run with verbose output
go run test/integration_test_runner.go -verbose

# Run specific test categories
go run test/integration_test_runner.go -only=api,services

# Skip specific test categories
go run test/integration_test_runner.go -skip=performance,security
```

### **Run Individual Test Categories**
```bash
# Service integration tests
go test -v ./test/integration/services/...

# API integration tests
go test -v ./test/integration/api/...

# Database integration tests
go test -v ./test/integration/database/...

# Cross-platform integration tests
go test -v ./test/integration/cross_platform/...

# Performance tests
go test -v ./test/integration/performance/...

# Mobile AR integration tests
cd mobile && npm test
```

## 🔧 **Configuration**

### **Test Configuration (`test/config/test_config.yaml`)**
```yaml
# Server Configuration
server:
  host: "localhost"
  port: 8080
  read_timeout: 30s
  write_timeout: 30s
  idle_timeout: 120s

# Database Configuration
database:
  host: "localhost"
  port: 5432
  name: "arxos_test"
  user: "arxos_test"
  password: "test_password"
  ssl_mode: "disable"
  max_open_conns: 25
  max_idle_conns: 5
  conn_max_lifetime: 5m

# Feature Flags for Testing
features:
  enable_graphql: true
  enable_websocket: true
  enable_ar_integration: true
  enable_offline_sync: true
  enable_performance_monitoring: true

# Performance Testing Configuration
performance:
  max_concurrent_requests: 100
  request_timeout: 30s
  memory_limit_mb: 512
  cpu_limit_percent: 80
```

### **Docker Compose (`test/config/docker-compose.test.yml`)**
The Docker Compose configuration provides isolated test environments with:
- PostgreSQL with PostGIS
- Redis cache
- IFC OpenShell service
- ArxOS API server
- Mobile app test environment
- Performance testing tools

## 📊 **Test Categories Details**

### **1. Service Integration Tests**
Tests the interaction between different backend services:
- Building service ↔ Equipment service
- IFC service ↔ Component service
- Sync service ↔ All services
- Authentication service ↔ All services

**Key Test Scenarios:**
- Create building → Create equipment → Update status
- Import IFC → Extract components → Update building
- Real-time sync between services
- Error handling and recovery

### **2. API Integration Tests**
Tests HTTP, GraphQL, and WebSocket APIs:
- REST API endpoints
- GraphQL queries and mutations
- WebSocket real-time updates
- Authentication flows
- Error handling and validation

**Key Test Scenarios:**
- CRUD operations via REST API
- Complex queries via GraphQL
- Real-time updates via WebSocket
- Authentication and authorization
- Rate limiting and security

### **3. Database Integration Tests**
Tests PostGIS database operations:
- Spatial queries and indexing
- Transaction handling
- Data consistency
- Migration testing
- Performance under load

**Key Test Scenarios:**
- Spatial queries with PostGIS
- Transaction rollback scenarios
- Data consistency across operations
- Migration up/down testing
- Connection pooling and performance

### **4. Mobile Integration Tests**
Tests React Native mobile app functionality:
- AR engine integration
- Offline data synchronization
- Equipment management
- Navigation and pathfinding
- Cross-platform data sync

**Key Test Scenarios:**
- AR equipment identification
- Offline data caching and sync
- Equipment status updates via AR
- Spatial data collection
- Navigation path calculation

### **5. Cross-Platform Integration Tests**
Tests interactions between CLI, Web, and Mobile:
- CLI → Web API → Database
- Mobile AR → Backend → Web interface
- Real-time sync across platforms
- Data consistency validation

**Key Test Scenarios:**
- CLI creates building → Web displays it
- Mobile updates equipment → CLI sees change
- Real-time sync across all platforms
- Data consistency validation

### **6. Performance Integration Tests**
Tests system performance under load:
- Load testing with concurrent requests
- Stress testing with extreme load
- Memory usage and leak detection
- Database performance under load
- API response time validation

**Key Test Scenarios:**
- Concurrent building creation
- High-volume equipment queries
- Spatial query performance
- Memory leak detection
- Response time validation

### **7. Security Integration Tests**
Tests security features:
- Authentication flows
- Authorization and RBAC
- Data encryption
- API security
- Cross-platform security

**Key Test Scenarios:**
- JWT authentication flow
- Role-based access control
- Data encryption validation
- API security headers
- Cross-platform security

## 🛠️ **Test Utilities**

### **Test Data Builder**
```go
// Create test data
builder := helpers.NewTestDataBuilder(buildingUC, equipmentUC, userUC, organizationUC, componentUC, ifcUC)

// Build test organization
org, err := builder.BuildTestOrganization(ctx)

// Build test building with equipment
buildings, err := builder.BuildTestBuildingsWithEquipment(ctx, 10, 5)
```

### **Test Server Helper**
```go
// Create test server
server, err := helpers.NewTestServer(cfg)

// Start server
err = server.Start()
defer server.Close()

// Get HTTP client
client := server.GetHTTPClient()
```

### **Custom Assertions**
```go
// Custom assertions for domain objects
helpers.AssertBuildingEqual(t, expectedBuilding, actualBuilding)
helpers.AssertEquipmentEqual(t, expectedEquipment, actualEquipment)
helpers.AssertSpatialAnchorEqual(t, expectedAnchor, actualAnchor)
helpers.AssertAREquipmentOverlayEqual(t, expectedOverlay, actualOverlay)
```

## 📈 **Test Reports**

### **Report Formats**
- **JSON**: Machine-readable format for CI/CD integration
- **HTML**: Human-readable format with detailed results
- **JUnit**: Standard format for CI/CD systems

### **Report Contents**
- Test execution summary
- Category-wise breakdown
- Performance metrics
- Error details and stack traces
- Coverage information (if enabled)

### **Report Location**
Reports are generated in the `test/results/` directory:
- `integration_test_report.json`
- `integration_test_report.html`
- `integration_test_report.xml`

## 🔍 **Debugging and Troubleshooting**

### **Common Issues**

1. **Database Connection Issues**
   ```bash
   # Check PostgreSQL status
   docker-compose -f test/config/docker-compose.test.yml exec postgres-test pg_isready
   
   # Check database logs
   docker-compose -f test/config/docker-compose.test.yml logs postgres-test
   ```

2. **Service Startup Issues**
   ```bash
   # Check service health
   curl http://localhost:8080/health
   
   # Check service logs
   docker-compose -f test/config/docker-compose.test.yml logs arxos-api-test
   ```

3. **Mobile Test Issues**
   ```bash
   # Check mobile app logs
   docker-compose -f test/config/docker-compose.test.yml logs mobile-app-test
   
   # Restart mobile services
   docker-compose -f test/config/docker-compose.test.yml restart mobile-app-test
   ```

### **Debug Mode**
```bash
# Run tests with debug logging
go run test/integration_test_runner.go -verbose -timeout=60m
```

### **Test Data Cleanup**
```bash
# Clean up test data
docker-compose -f test/config/docker-compose.test.yml exec arxos-api-test go run test/helpers/cleanup_test_data.go
```

## 🚀 **CI/CD Integration**

### **GitHub Actions**
```yaml
name: Integration Tests
on: [push, pull_request]

jobs:
  integration-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-go@v3
        with:
          go-version: '1.21'
      - uses: actions/setup-node@v3
        with:
          node-version: '18'
      - name: Run Integration Tests
        run: |
          chmod +x test/config/test_environment.sh
          ./test/config/test_environment.sh
      - name: Upload Test Results
        uses: actions/upload-artifact@v3
        with:
          name: test-results
          path: test/results/
```

### **Jenkins Pipeline**
```groovy
pipeline {
    agent any
    stages {
        stage('Setup') {
            steps {
                sh 'chmod +x test/config/test_environment.sh'
            }
        }
        stage('Integration Tests') {
            steps {
                sh './test/config/test_environment.sh'
            }
        }
        stage('Publish Results') {
            steps {
                publishTestResults testResultsPattern: 'test/results/*.xml'
            }
        }
    }
}
```

## 📚 **Best Practices**

### **Test Organization**
- Group related tests in the same file
- Use descriptive test names
- Follow the Arrange-Act-Assert pattern
- Keep tests independent and isolated

### **Test Data Management**
- Use the TestDataBuilder for consistent test data
- Clean up test data after each test
- Use realistic test data that matches production scenarios
- Avoid hardcoded values in tests

### **Performance Testing**
- Set realistic performance thresholds
- Test under various load conditions
- Monitor memory usage and leaks
- Validate response times and throughput

### **Error Handling**
- Test both success and failure scenarios
- Validate error messages and codes
- Test error recovery mechanisms
- Ensure proper cleanup on errors

## 🤝 **Contributing**

### **Adding New Tests**
1. Create test file in appropriate category directory
2. Follow existing naming conventions
3. Use test utilities and helpers
4. Add test data to fixtures if needed
5. Update documentation

### **Test Standards**
- All tests must be deterministic
- Tests should clean up after themselves
- Use meaningful assertions
- Include proper error handling
- Follow Go testing conventions

### **Code Review**
- Ensure tests cover edge cases
- Validate test data is realistic
- Check for proper cleanup
- Verify error handling
- Ensure tests are maintainable

## 📞 **Support**

For questions or issues with the integration testing suite:
- Create an issue in the GitHub repository
- Check the troubleshooting section
- Review existing test examples
- Consult the ArxOS documentation

---

**Happy Testing! 🧪✨**
