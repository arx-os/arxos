# Go Module Standards

## Overview

This document outlines the standards for Go module management in the Arxos project.

## Go Version Standards

### Use Go 1.21 or Later

We use Go 1.21 or later for all Go modules to ensure:
- Latest security updates
- Performance improvements
- Modern language features
- Long-term support

**✅ Good:**
```go
// go.mod
go 1.21
```

**❌ Bad:**
```go
// go.mod
go 1.18
```

### Rationale

1. **Security**: Latest security patches and vulnerability fixes
2. **Performance**: Improved compiler and runtime performance
3. **Features**: Access to modern Go language features
4. **Support**: Long-term support and maintenance
5. **Compatibility**: Better compatibility with modern dependencies

## Module Structure

### Standard Module Layout
```
module-name/
├── go.mod          # Module definition
├── go.sum          # Dependency checksums
├── main.go         # Main application entry point
├── cmd/            # Command-line tools
├── internal/       # Private application code
├── pkg/            # Public library code
├── api/            # API definitions
├── docs/           # Documentation
└── tests/          # Test files
```

### Module Naming
- Use lowercase with hyphens: `arx-backend`
- Include organization prefix: `github.com/arxos/arx-svg-engine`
- Be descriptive and specific

## Dependency Management

### Version Constraints

Use semantic versioning for dependencies:

```go
require (
    github.com/go-chi/chi/v5 v5.0.10
    github.com/google/uuid v1.6.0
    gorm.io/gorm v1.25.4
)
```

### Dependency Updates

Regular dependency updates:

```bash
# Update all dependencies
go get -u ./...

# Update specific dependency
go get -u github.com/go-chi/chi/v5

# Clean up unused dependencies
go mod tidy
```

### Security Scanning

Regular security audits:

```bash
# Install gosec
go install github.com/securecodewarrior/gosec/v2/cmd/gosec@latest

# Run security scan
gosec ./...
```

## Testing Standards

### Unit Tests

Write comprehensive unit tests:

```go
package main

import (
    "testing"
    "github.com/stretchr/testify/assert"
)

func TestExample(t *testing.T) {
    result := ExampleFunction()
    assert.Equal(t, expected, result)
}
```

### Integration Tests

Test module integration:

```go
func TestIntegration(t *testing.T) {
    // Setup test environment
    // Run integration test
    // Cleanup
}
```

### Test Coverage

Maintain high test coverage:

```bash
# Run tests with coverage
go test -cover ./...

# Generate coverage report
go test -coverprofile=coverage.out ./...
go tool cover -html=coverage.out
```

## Build Standards

### Build Commands

Standard build commands:

```bash
# Build all packages
go build ./...

# Build specific package
go build ./cmd/server

# Build for specific platform
GOOS=linux GOARCH=amd64 go build ./...
```

### Binary Naming

Use descriptive binary names:

```bash
# Good
go build -o arx-backend ./cmd/server
go build -o arx-cli ./cmd/cli

# Bad
go build -o main ./cmd/server
```

## CI/CD Integration

### GitHub Actions

Standard Go CI workflow:

```yaml
name: Go Testing & Validation

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]

jobs:
  go-testing:
    runs-on: ubuntu-latest
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v4
      
    - name: Set up Go
      uses: actions/setup-go@v4
      with:
        go-version: '1.21'
        
    - name: Verify Go version
      run: go version
      
    - name: Validate modules
      run: |
        go mod verify
        go mod tidy
        
    - name: Build
      run: go build ./...
      
    - name: Test
      run: go test ./... -v
      
    - name: Security scan
      run: |
        go install github.com/securecodewarrior/gosec/v2/cmd/gosec@latest
        gosec ./...
```

### Build Validation

CI should validate:

1. **Go version compliance** (1.21+)
2. **Module validation** (`go mod verify`)
3. **Dependency cleanup** (`go mod tidy`)
4. **Build success** (`go build ./...`)
5. **Test success** (`go test ./...`)
6. **Security scanning** (`gosec`)

## Code Quality

### Linting

Use golangci-lint for comprehensive linting:

```bash
# Install golangci-lint
go install github.com/golangci/golangci-lint/cmd/golangci-lint@latest

# Run linting
golangci-lint run
```

### Formatting

Use gofmt for code formatting:

```bash
# Format code
gofmt -w .

# Check formatting
gofmt -d .
```

### Documentation

Write comprehensive documentation:

```go
// Package example provides example functionality
package example

// ExampleFunction demonstrates example usage
func ExampleFunction() string {
    return "example"
}
```

## Security Best Practices

### Dependency Security

1. **Regular updates**: Update dependencies monthly
2. **Security scanning**: Use gosec for security analysis
3. **Vulnerability monitoring**: Monitor for known vulnerabilities
4. **Minimal dependencies**: Only include necessary dependencies

### Code Security

1. **Input validation**: Validate all inputs
2. **Error handling**: Handle errors appropriately
3. **Secure defaults**: Use secure default configurations
4. **Logging**: Log security-relevant events

## Performance Standards

### Build Performance

1. **Module caching**: Use Go module cache
2. **Parallel builds**: Use `-p` flag for parallel builds
3. **Incremental builds**: Leverage Go's incremental compilation

### Runtime Performance

1. **Memory profiling**: Use pprof for memory analysis
2. **CPU profiling**: Profile CPU usage
3. **Goroutine management**: Manage goroutines properly
4. **Resource cleanup**: Clean up resources appropriately

## Troubleshooting

### Common Issues

1. **Module not found**
   ```bash
   go mod download
   go mod tidy
   ```

2. **Version conflicts**
   ```bash
   go mod why github.com/package/name
   go mod graph
   ```

3. **Build failures**
   ```bash
   go clean -cache
   go mod download
   go build ./...
   ```

### Debugging

1. **Module information**
   ```bash
   go list -m all
   go mod graph
   ```

2. **Build information**
   ```bash
   go build -x ./...
   go test -v ./...
   ```

## Maintenance

### Regular Tasks

1. **Monthly**: Update dependencies
2. **Quarterly**: Review Go version upgrades
3. **Annually**: Major dependency review
4. **As needed**: Security updates

### Update Process

1. **Check current versions**
   ```bash
   go list -m all
   ```

2. **Update dependencies**
   ```bash
   go get -u ./...
   go mod tidy
   ```

3. **Test thoroughly**
   ```bash
   go test ./...
   go build ./...
   ```

4. **Update documentation**

## Examples

### Complete go.mod Example

```go
module arx-backend

go 1.21

require (
    github.com/go-chi/chi/v5 v5.0.10
    github.com/google/uuid v1.6.0
    github.com/joho/godotenv v1.5.1
    github.com/prometheus/client_golang v1.19.1
    github.com/rs/cors v1.11.1
    github.com/spf13/viper v1.20.1
    go.uber.org/zap v1.27.0
    golang.org/x/crypto v0.32.0
    gorm.io/datatypes v1.2.5
    gorm.io/driver/postgres v1.6.0
    gorm.io/gorm v1.30.0
)

require (
    github.com/stretchr/testify v1.10.0
    github.com/urfave/cli/v2 v2.27.7
)
```

### Test Example

```go
package main

import (
    "testing"
    "github.com/stretchr/testify/assert"
    "github.com/stretchr/testify/require"
)

func TestMainFunction(t *testing.T) {
    // Arrange
    input := "test"
    
    // Act
    result := MainFunction(input)
    
    // Assert
    require.NotNil(t, result)
    assert.Equal(t, "expected", result)
}

func TestMainFunction_EdgeCases(t *testing.T) {
    tests := []struct {
        name     string
        input    string
        expected string
    }{
        {"empty string", "", ""},
        {"nil input", "", ""},
    }
    
    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            result := MainFunction(tt.input)
            assert.Equal(t, tt.expected, result)
        })
    }
}
```

## Compliance Checklist

- [ ] All modules use Go 1.21+
- [ ] Dependencies are up to date
- [ ] Tests pass with good coverage
- [ ] Security scanning completed
- [ ] Code is properly formatted
- [ ] Documentation is current
- [ ] CI/CD integration working
- [ ] Build process validated

## Support

For questions about Go module management:
1. Check this documentation
2. Review existing examples
3. Run validation scripts
4. Contact the development team 