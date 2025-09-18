# Contributing to ArxOS

## Getting Started

### Prerequisites
- Go 1.24+
- PostgreSQL 14+ with PostGIS 3.4+ (for spatial features)
- Docker and Docker Compose (for development environment)
- Git

### Development Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/arx-os/arxos.git
   cd arxos
   ```

2. **Set up development environment:**
   ```bash
   # Start PostgreSQL with PostGIS
   docker-compose -f docker/docker-compose.dev.yml up -d postgis

   # Install dependencies
   go mod download

   # Set up environment variables
   cp .env.example .env
   # Edit .env with your local settings
   ```

3. **Run tests:**
   ```bash
   # Unit tests
   go test ./...

   # Integration tests (requires PostGIS)
   go test ./internal/integration/...

   # Performance benchmarks
   go test -bench=. ./internal/integration/
   ```

4. **Build and run:**
   ```bash
   go build ./cmd/arx
   ./arx version
   ```

## Development Guidelines

### Code Style

We follow standard Go conventions:

- **gofmt**: All code must be formatted with `gofmt`
- **golint**: Address all linting warnings
- **go vet**: Fix all vet issues
- **godoc**: Public APIs must have comprehensive documentation

#### Naming Conventions
- **Packages**: lowercase, single word when possible
- **Types**: PascalCase
- **Functions**: PascalCase for exported, camelCase for private
- **Constants**: UPPER_SNAKE_CASE for package constants
- **Variables**: camelCase

#### File Organization
```go
// Package declaration and documentation
package spatial

// Standard library imports
import (
    "context"
    "fmt"
)

// Third-party imports
import (
    "github.com/stretchr/testify/assert"
)

// Local imports
import (
    "github.com/arx-os/arxos/internal/database"
)

// Package constants
const (
    DefaultPrecision = 1.0 // millimeters
)

// Package variables
var (
    ErrInvalidCoordinate = errors.New("invalid coordinate")
)

// Type definitions
type Point3D struct { ... }

// Constructor functions
func NewPoint3D(x, y, z float64) Point3D { ... }

// Methods on types
func (p Point3D) DistanceTo(other Point3D) float64 { ... }

// Package functions
func CalculateDistance(p1, p2 Point3D) float64 { ... }
```

### Error Handling

Use the ArxOS error framework for consistent error handling:

```go
import "github.com/arx-os/arxos/internal/errors"

// Create typed errors
func ValidateCoordinate(x, y, z float64) error {
    if math.IsNaN(x) || math.IsNaN(y) || math.IsNaN(z) {
        return errors.New(
            errors.ErrorTypeValidation,
            "INVALID_COORDINATE",
            "Coordinate values cannot be NaN",
            "spatial.ValidateCoordinate",
            "coordinate_validation",
            map[string]interface{}{
                "x": x, "y": y, "z": z,
            },
        )
    }
    return nil
}

// Wrap external errors
func ImportIFC(filename string) error {
    file, err := os.Open(filename)
    if err != nil {
        return errors.Wrap(err,
            errors.ErrorTypeFileIO,
            "IFC_IMPORT_FAILED",
            fmt.Sprintf("Failed to open IFC file: %s", filename),
            "converter.ImportIFC",
            "file_open",
            map[string]interface{}{
                "filename": filename,
            },
        )
    }
    defer file.Close()

    // ... rest of import logic
}
```

### Testing Standards

#### Test File Structure
```go
package spatial_test

import (
    "testing"
    "github.com/stretchr/testify/assert"
    "github.com/stretchr/testify/require"

    "github.com/arx-os/arxos/internal/spatial"
)

func TestPoint3D_DistanceTo(t *testing.T) {
    tests := []struct {
        name     string
        p1       spatial.Point3D
        p2       spatial.Point3D
        expected float64
    }{
        {
            name: "origin to unit point",
            p1: spatial.NewPoint3D(0, 0, 0),
            p2: spatial.NewPoint3D(1, 0, 0),
            expected: 1.0,
        },
        // ... more test cases
    }

    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            result := tt.p1.DistanceTo(tt.p2)
            assert.InDelta(t, tt.expected, result, 0.001)
        })
    }
}
```

#### Test Categories

1. **Unit Tests**: Test individual functions and methods
2. **Integration Tests**: Test component interactions
3. **Performance Tests**: Benchmark critical paths
4. **End-to-End Tests**: Test complete workflows

#### Test Data

Use the `test_data/` directory for test fixtures:
- `test_data/inputs/`: Sample input files
- `test_data/expected/`: Expected output files
- `test_data/spatial_test_scenarios.json`: Spatial test configurations

### Git Workflow

1. **Create feature branch:**
   ```bash
   git checkout -b feature/spatial-optimization
   ```

2. **Make focused commits:**
   ```bash
   git add -A
   git commit -m "feat: optimize spatial proximity queries

   - Add spatial indexing for Point3D queries
   - Improve query performance by 40%
   - Add benchmarks for spatial operations

   Closes #123"
   ```

3. **Keep branch up to date:**
   ```bash
   git fetch origin
   git rebase origin/main
   ```

4. **Push and create PR:**
   ```bash
   git push origin feature/spatial-optimization
   # Create PR through GitHub
   ```

#### Commit Message Format

```
<type>(<scope>): <description>

<body>

<footer>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

**Scopes:**
- `spatial`: Spatial data operations
- `database`: Database layer changes
- `api`: REST API changes
- `converter`: Format conversion
- `config`: Configuration management

### Code Review Process

#### Before Submitting PR
- [ ] All tests pass locally
- [ ] Code is properly formatted (`gofmt`)
- [ ] No linting warnings (`golint`)
- [ ] No vet issues (`go vet`)
- [ ] Documentation updated
- [ ] Changelog entry added (if applicable)

#### PR Requirements
- [ ] Clear description of changes
- [ ] Link to related issues
- [ ] Test coverage for new code
- [ ] Performance impact assessment
- [ ] Breaking changes documented

#### Review Checklist
- [ ] Code follows project conventions
- [ ] Error handling is appropriate
- [ ] Tests are comprehensive
- [ ] Documentation is clear
- [ ] Performance considerations addressed
- [ ] Security implications reviewed

### Performance Guidelines

#### Database Operations
- Use prepared statements for repeated queries
- Minimize database round trips
- Use spatial indexes for geometric queries
- Implement proper connection pooling

#### Memory Management
- Avoid unnecessary allocations in hot paths
- Use object pooling for expensive objects
- Stream large files rather than loading into memory
- Profile memory usage for critical operations

#### Spatial Operations
- Use appropriate spatial data structures
- Implement efficient spatial indexing
- Optimize coordinate transformations
- Cache expensive geometric calculations

### Documentation Standards

#### Code Documentation
```go
// Point3D represents a point in 3D space with millimeter precision.
//
// All coordinates are stored as float64 values representing millimeters
// from the building origin. This provides sub-millimeter precision for
// typical building-scale measurements.
//
// Example:
//   origin := spatial.NewPoint3D(0, 0, 0)
//   corner := spatial.NewPoint3D(5000, 3000, 2700) // 5m x 3m x 2.7m
//   distance := origin.DistanceTo(corner)
type Point3D struct {
    X float64 `json:"x"` // X coordinate in millimeters
    Y float64 `json:"y"` // Y coordinate in millimeters
    Z float64 `json:"z"` // Z coordinate in millimeters
}
```

#### API Documentation
- All public APIs must have godoc comments
- Include usage examples
- Document error conditions
- Specify units for measurements

### Security Considerations

#### Input Validation
- Validate all user inputs
- Sanitize file paths and names
- Check coordinate bounds and validity
- Implement rate limiting for APIs

#### SQL Injection Prevention
- Use parameterized queries exclusively
- Validate SQL identifiers separately
- Escape special characters in dynamic queries
- Use query builders when appropriate

#### File System Security
- Validate file extensions and types
- Check file sizes before processing
- Use temporary directories with appropriate permissions
- Clean up temporary files after processing

### Release Process

#### Version Numbering
We follow Semantic Versioning (SemVer):
- `MAJOR.MINOR.PATCH`
- Major: Breaking changes
- Minor: New features, backward compatible
- Patch: Bug fixes, backward compatible

#### Release Checklist
- [ ] All tests pass
- [ ] Performance benchmarks meet targets
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
- [ ] Version bumped in appropriate files
- [ ] Security review completed
- [ ] Docker images built and tested

## Getting Help

- **GitHub Issues**: Bug reports and feature requests
- **GitHub Discussions**: General questions and discussions
- **Code Review**: Request review from maintainers
- **Documentation**: Check README.md and ARCHITECTURE.md

Thank you for contributing to ArxOS!