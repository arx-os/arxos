# Arxos Test Architecture

## Overview

This document defines the testing strategy for Arxos, designed to scale with a large development team and complex feature set.

## Test Philosophy

### Testing Pyramid
```
         /\
        /E2E\        (5%)  - Critical user journeys
       /------\
      /  API   \     (15%) - Service integration
     /----------\
    / Integration\   (30%) - Component integration  
   /--------------\
  /   Unit Tests   \ (50%) - Business logic
 /------------------\
```

## Directory Structure

```
tests/
├── unit/                    # Fast, isolated tests
│   ├── backend/            # Go unit tests
│   │   ├── models/
│   │   ├── services/
│   │   ├── handlers/
│   │   └── utils/
│   ├── frontend/           # Vanilla JS tests (if needed)
│   │   └── basic/          # Simple JS function tests
│   └── ai-service/         # Python unit tests
│       ├── extractors/
│       └── processors/
│
├── integration/            # Component integration tests
│   ├── api/               # API endpoint tests
│   │   ├── rest/
│   │   └── graphql/
│   ├── database/          # Database integration
│   │   ├── migrations/
│   │   └── queries/
│   ├── services/          # Service integration
│   │   ├── pdf-processing/
│   │   ├── auth/
│   │   └── spatial/
│   └── messaging/         # Event/queue tests
│
├── e2e/                   # End-to-end tests
│   ├── web/              # Browser-based tests
│   │   ├── auth/
│   │   ├── workflows/
│   │   └── mobile/
│   ├── api/              # API workflow tests
│   └── scenarios/        # Business scenarios
│
├── performance/          # Performance testing
│   ├── load/            # Load tests (K6)
│   ├── stress/          # Stress tests
│   ├── soak/            # Endurance tests
│   └── benchmarks/      # Go benchmarks
│
├── security/            # Security testing
│   ├── fuzzing/        # Fuzz tests
│   ├── penetration/    # Pen test scripts
│   └── compliance/     # Compliance checks
│
├── contracts/          # Contract testing
│   ├── api/           # API contracts
│   └── events/        # Event contracts
│
├── fixtures/          # Test data
│   ├── data/         # JSON/YAML fixtures
│   ├── files/        # Binary test files
│   │   ├── pdfs/
│   │   ├── images/
│   │   └── ifc/
│   └── seeds/        # Database seeds
│
├── mocks/            # Mock services
│   ├── services/    # Service mocks
│   └── external/    # External API mocks
│
├── helpers/         # Test utilities
│   ├── builders/   # Test data builders
│   ├── assertions/ # Custom assertions
│   └── utils/      # Common utilities
│
├── configs/        # Test configurations
│   ├── env/       # Environment configs
│   ├── ci/        # CI/CD configs
│   └── tools/     # Tool configurations
│
└── reports/       # Test reports (gitignored)
    ├── coverage/
    ├── performance/
    └── security/
```

## Test Types and Tools

### Unit Tests
- **Backend (Go)**: `go test` + `testify` + `mockery`
- **Frontend (Vanilla JS)**: Simple HTML validation, manual testing
- **AI Service (Python)**: `pytest` + `pytest-mock`
- **Coverage Target**: 80%

### Integration Tests
- **API Testing**: `go test` with real database
- **Database**: `testcontainers-go` for isolated DB
- **Services**: Docker Compose for service dependencies
- **Coverage Target**: 60%

### E2E Tests
- **Web**: Simple browser checks, manual testing
- **API**: Go tests with httptest
- **Mobile**: `Appium` or `Detox`
- **Coverage Target**: Critical paths only

### Performance Tests
- **Load Testing**: `K6` with JavaScript
- **Benchmarks**: Go `testing.B`
- **Monitoring**: `Prometheus` + `Grafana`
- **Targets**: Define SLAs per endpoint

### Security Tests
- **SAST**: `gosec`, `semgrep`
- **DAST**: `OWASP ZAP`
- **Dependencies**: `dependabot`, `snyk`
- **Compliance**: Custom scripts

## Test Execution Strategy

### Local Development
```bash
# Fast feedback loop
make test-unit          # < 30 seconds
make test-integration   # < 2 minutes
make test-e2e-smoke    # < 5 minutes
```

### Pull Request
```yaml
# Automated on every PR
- unit-tests           # Required
- integration-tests    # Required
- api-contract-tests   # Required
- e2e-smoke-tests     # Required
- security-scan       # Required
```

### Main Branch
```yaml
# After merge to main
- full-test-suite     # All tests
- performance-tests   # Baseline comparison
- e2e-full           # Complete scenarios
- security-audit     # Deep scan
```

### Release
```yaml
# Before production release
- regression-suite    # Full regression
- load-tests         # Production-like load
- security-pentest   # Manual + automated
- chaos-tests        # Resilience testing
```

## Test Data Management

### Fixtures
- **Deterministic**: Use fixed seeds for reproducibility
- **Isolated**: Each test creates its own data
- **Cleanup**: Automatic cleanup after tests
- **Realistic**: Production-like test data

### Test Databases
```yaml
# Docker Compose for test databases
postgres-unit:       # Fast, in-memory
postgres-integration: # Full PostGIS
postgres-e2e:        # Production-like
```

### External Services
- **Mocked in Unit Tests**: No external calls
- **Containerized in Integration**: Docker services
- **Staging in E2E**: Real staging services
- **Production-like in Load**: Scaled environment

## CI/CD Pipeline

### GitHub Actions Workflow
```yaml
name: Test Pipeline

on: [push, pull_request]

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        service: [backend, frontend, ai-service]
    steps:
      - uses: actions/checkout@v3
      - name: Run Unit Tests
        run: make test-unit-${{ matrix.service }}
      - name: Upload Coverage
        uses: codecov/codecov-action@v3

  integration-tests:
    needs: unit-tests
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgis/postgis:15-3.3
      redis:
        image: redis:7
    steps:
      - name: Run Integration Tests
        run: make test-integration

  e2e-tests:
    needs: integration-tests
    runs-on: ubuntu-latest
    steps:
      - name: Run E2E Tests
        run: make test-e2e-smoke

  performance-tests:
    if: github.ref == 'refs/heads/main'
    needs: e2e-tests
    runs-on: ubuntu-latest
    steps:
      - name: Run Performance Tests
        run: make test-performance
      - name: Compare Baseline
        run: make performance-compare
```

## Test Standards

### Naming Conventions
```go
// Unit test
func TestArxObject_Validate(t *testing.T)

// Integration test  
func TestAPI_CreateBuilding_Integration(t *testing.T)

// E2E test
func TestE2E_UserCanUploadAndProcessPDF(t *testing.T)
```

### Test Structure
```go
func TestExample(t *testing.T) {
    // Arrange
    fixture := setupTestData(t)
    defer cleanup(t)
    
    // Act
    result := performAction()
    
    // Assert
    assert.Equal(t, expected, result)
}
```

### Best Practices
1. **Isolated**: Tests don't depend on each other
2. **Repeatable**: Same result every run
3. **Fast**: Optimize for quick feedback
4. **Clear**: Descriptive names and assertions
5. **Maintained**: Update tests with code changes

## Monitoring and Reporting

### Metrics to Track
- **Coverage**: Overall and per-component
- **Execution Time**: Track test duration trends
- **Flakiness**: Identify and fix flaky tests
- **Failure Rate**: Monitor test health

### Dashboards
- **Test Results**: Real-time test status
- **Coverage Trends**: Coverage over time
- **Performance**: API response times
- **Quality Gates**: Release readiness

## Scaling Considerations

### Parallel Execution
- **Unit Tests**: Fully parallel
- **Integration**: Parallel with isolated databases
- **E2E**: Sequential or dedicated environments

### Test Sharding
```yaml
# Split tests across multiple runners
test-shard-1: [tests/unit/backend/models/...]
test-shard-2: [tests/unit/backend/services/...]
test-shard-3: [tests/unit/backend/handlers/...]
```

### Environment Management
```
Development: Local Docker
Staging:     Kubernetes namespace
Production:  Production-like cluster
```

## Migration Path

### Phase 1: Foundation (Week 1-2)
- Set up directory structure
- Configure test databases
- Implement basic CI/CD

### Phase 2: Migration (Week 3-4)
- Move existing tests
- Add missing unit tests
- Set up integration tests

### Phase 3: Enhancement (Week 5-6)
- Add E2E tests
- Implement performance tests
- Set up monitoring

### Phase 4: Optimization (Ongoing)
- Improve test speed
- Reduce flakiness
- Enhance coverage

## Team Guidelines

### Code Review Checklist
- [ ] Tests added for new features
- [ ] Tests updated for changes
- [ ] All tests passing
- [ ] Coverage maintained/improved
- [ ] No flaky tests introduced

### Test Writing Guidelines
- Write tests first (TDD) when possible
- One assertion per test method
- Use descriptive test names
- Mock external dependencies
- Clean up test data

## Tools and Dependencies

### Required Tools
```bash
# Backend
go install github.com/vektra/mockery/v2
go install github.com/golangci/golangci-lint

# Frontend
# No npm dependencies - vanilla JS only

# Performance
brew install k6

# Security
go install github.com/securego/gosec/v2/cmd/gosec
```

### Docker Images
```yaml
postgres: postgis/postgis:15-3.3-alpine
redis: redis:7-alpine
testcontainers: testcontainers/ryuk:0.5.1
```

## Cost Optimization

### Resource Management
- **Cleanup**: Automatic resource cleanup
- **Timeouts**: Prevent hanging tests
- **Caching**: Cache dependencies and builds
- **Selective**: Run only affected tests

### CI/CD Optimization
- **Matrix builds**: Parallel job execution
- **Conditional runs**: Skip unnecessary tests
- **Incremental**: Test only changed code
- **Scheduled**: Run expensive tests off-peak

## Success Metrics

### Quality Metrics
- Unit test coverage > 80%
- Integration test coverage > 60%
- Zero critical bugs in production
- < 1% test flakiness

### Performance Metrics
- Unit tests < 30 seconds
- Integration tests < 5 minutes
- E2E smoke tests < 10 minutes
- Full suite < 30 minutes

### Team Metrics
- Tests written with code
- PR blocked without tests
- Test failures fixed immediately
- Regular test review and cleanup