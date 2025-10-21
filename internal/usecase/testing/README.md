# Testing Package

Test utilities for the ArxOS use case layer.

## Overview

This package provides mock repositories, test fixtures, and helpers for writing clean, maintainable tests across the ArxOS use case layer.

## Quick Start

```go
package mypackage

import (
	"testing"

	"github.com/arx-os/arxos/internal/domain"
	utesting "github.com/arx-os/arxos/internal/usecase/testing"
	"github.com/stretchr/testify/mock"
	"github.com/stretchr/testify/require"
)

func TestMyUseCase(t *testing.T) {
	// Create mocks
	mockRepo := new(utesting.MockBuildingRepository)
	mockLogger := utesting.CreatePermissiveMockLogger()

	// Create test data
	building := utesting.CreateTestBuilding()

	// Set expectations
	mockRepo.On("GetByID", mock.Anything, building.ID.String()).
		Return(building, nil)

	// Test your use case
	uc := NewMyUseCase(mockRepo, mockLogger)
	result, err := uc.DoSomething(context.Background(), building.ID.String())

	// Assert
	require.NoError(t, err)
	mockRepo.AssertExpectations(t)
}
```

## Package Structure

```
internal/usecase/testing/
├── doc.go                      - Package documentation
├── README.md                   - This file
├── mocks_core.go               - Core domain mocks (Building, User, Org, etc.)
├── mocks_integration.go        - Integration mocks (BAS, IFC, Spatial)
├── mocks_infrastructure.go     - Infrastructure mocks (Cache, Logger)
├── fixtures.go                 - Test data creators
└── (future) mocks_versioncontrol.go - Version control mocks
```

## Available Mocks

### Core Domain Mocks (`mocks_core.go`)
- `MockBuildingRepository` - Building CRUD and queries
- `MockEquipmentRepository` - Equipment operations
- `MockUserRepository` - User management
- `MockOrganizationRepository` - Organization management (including GetByName, AddUser, RemoveUser)
- `MockFloorRepository` - Floor operations (including GetByBuilding)
- `MockRoomRepository` - Room operations (including GetByFloor)

### Integration Mocks (`mocks_integration.go`)
- `MockBASPointRepository` - BAS point operations (including BulkCreate, MapToRoom)
- `MockBASSystemRepository` - BAS system management

### Infrastructure Mocks (`mocks_infrastructure.go`)
- `MockLogger` - Logging operations

## Test Fixtures

### Simple Fixtures

```go
// Create with defaults
building := utesting.CreateTestBuilding()
user := utesting.CreateTestUser()
org := utesting.CreateTestOrganization()
```

### Customized Fixtures (Functional Options)

```go
// Create with custom properties
building := utesting.CreateTestBuildingWith(
	utesting.WithBuildingName("Empire State Building"),
	utesting.WithBuildingID(specificID),
	utesting.WithBuildingAddress("350 5th Ave, New York, NY 10118"),
)

user := utesting.CreateTestUserWith(
	utesting.WithUserEmail("admin@example.com"),
	utesting.WithUserRole("admin"),
)

org := utesting.CreateTestOrganizationWith(
	utesting.WithOrgName("Acme Corp"),
	utesting.WithOrgPlan("enterprise"),
)
```

## Best Practices

### 1. Import Alias

Always use an alias to avoid conflict with stdlib `testing`:

```go
import (
	"testing"  // stdlib
	utesting "github.com/arx-os/arxos/internal/usecase/testing"  // our package
)
```

### 2. Mock Expectations

Use `mock.Anything` for context parameters unless testing specific contexts:

```go
mockRepo.On("GetByID", mock.Anything, "id-123").Return(building, nil)
```

### 3. Assert Expectations

Always verify mock calls at the end of your test:

```go
mockRepo.AssertExpectations(t)
```

### 4. Permissive Loggers

For most tests, use a permissive logger that doesn't require expectations:

```go
mockLogger := utesting.CreatePermissiveMockLogger()
```

## Common Patterns

### Table-Driven Tests

```go
tests := []struct {
	name     string
	input    *domain.Building
	wantErr  bool
}{
	{
		name:    "valid building",
		input:   utesting.CreateTestBuilding(),
		wantErr: false,
	},
	{
		name:    "custom building",
		input:   utesting.CreateTestBuildingWith(utesting.WithBuildingName("Custom")),
		wantErr: false,
	},
}

for _, tt := range tests {
	t.Run(tt.name, func(t *testing.T) {
		// Test logic
	})
}
```

### Error Cases

```go
mockRepo.On("GetByID", mock.Anything, "nonexistent").
	Return(nil, errors.New("not found"))
```

## Adding New Mocks

When you need to mock a new repository:

1. Identify the domain area (core, versioncontrol, integration, infrastructure)
2. Add the mock to the appropriate `mocks_*.go` file
3. Implement ALL methods of the interface
4. Use consistent patterns from existing mocks

## Phase 2 Enhancements

### Builders - Fluent API for Complex Test Data

Builders provide a clean, chainable interface for creating test entities:

```go
// Create a building with floors and rooms
building := utesting.NewBuildingBuilder().
    WithName("Empire State Building").
    WithAddress("350 5th Ave, New York, NY 10118").
    WithCoordinates(40.748817, -73.985428).
    WithFloor(
        utesting.NewFloorBuilder().
            WithName("Ground Floor").
            WithLevel(0).
            WithRoom(
                utesting.NewRoomBuilder().
                    WithName("Lobby").
                    WithNumber("G-001").
                    WithDimensions(50.0, 15.0).
                    Build(),
            ).
            Build(),
    ).
    Build()

// Create an admin user
admin := utesting.NewUserBuilder().
    WithEmail("admin@example.com").
    AsAdmin().
    Build()

// Create an enterprise organization
org := utesting.NewOrganizationBuilder().
    WithName("Acme Corp").
    AsEnterprise().
    Build()
```

**Available Builders:**
- `NewBuildingBuilder()` - Buildings with floors, equipment, coordinates
- `NewFloorBuilder()` - Floors with rooms and equipment
- `NewRoomBuilder()` - Rooms with location and dimensions
- `NewEquipmentBuilder()` - Equipment with type, status, location
- `NewUserBuilder()` - Users with roles and status
- `NewOrganizationBuilder()` - Organizations with plans and status

### Test Helpers - Common Patterns

Reduce boilerplate with pre-configured scenarios:

```go
// Create a building with 5 floors
building := utesting.SetupBuildingWithFloors(5)

// Create a building with 3 floors, each with 10 rooms
building := utesting.SetupBuildingWithFloorsAndRooms(3, 10)

// Create a user with organization
user, org := utesting.SetupUserWithOrg()

// Create an admin user
admin := utesting.SetupAdminUser()

// Context helpers
ctx := utesting.WithTestContext()
authCtx := utesting.WithAuthContext("user-123")
```

### Custom Assertions - Better Error Messages

Domain-specific assertions with detailed failure reports:

```go
// Assert buildings are equal (with detailed diff)
utesting.AssertBuildingEqual(t, expected, actual)

// Assert locations are near (with tolerance)
utesting.AssertLocationNear(t, expected.Coordinates, actual.Coordinates, 0.0001)

// Assert floor count
utesting.AssertFloorCount(t, building, 5)

// Assert user equality
utesting.AssertUserEqual(t, expected, actual)

// Validation helpers
utesting.AssertValidID(t, building.ID)
utesting.AssertValidTimestamp(t, building.CreatedAt)
```

**Benefits of Custom Assertions:**
- Detailed, readable error messages
- Domain-aware comparisons (e.g., spatial tolerance)
- Highlights exactly what differs
- Reduces test code

### Example: Before & After Phase 2

**Before (Verbose):**
```go
func TestBuildingCreation(t *testing.T) {
    mockRepo := new(utesting.MockBuildingRepository)
    mockLogger := utesting.CreatePermissiveMockLogger()

    building := &domain.Building{
        ID: types.NewID(),
        Name: "Test Building",
        Address: "123 Main St",
        Coordinates: &domain.Location{X: 40.0, Y: -73.0, Z: 0},
        Floors: []*domain.Floor{
            {
                ID: types.NewID(),
                Name: "Ground Floor",
                Level: 0,
                CreatedAt: time.Now(),
                UpdatedAt: time.Now(),
            },
        },
        CreatedAt: time.Now(),
        UpdatedAt: time.Now(),
    }

    mockRepo.On("Create", mock.Anything, mock.MatchedBy(func(b *domain.Building) bool {
        return b.Name == "Test Building" && b.Address != ""
    })).Return(nil)

    uc := NewBuildingUseCase(mockRepo, mockLogger)
    result, err := uc.CreateBuilding(context.Background(), building)

    require.NoError(t, err)
    assert.Equal(t, building.Name, result.Name)
    assert.Equal(t, building.Address, result.Address)
    assert.NotNil(t, result.Coordinates)
    assert.Equal(t, 1, len(result.Floors))
}
```

**After (Clean & Expressive):**
```go
func TestBuildingCreation(t *testing.T) {
    mockRepo := new(utesting.MockBuildingRepository)
    mockLogger := utesting.CreatePermissiveMockLogger()

    building := utesting.NewBuildingBuilder().
        WithName("Test Building").
        WithAddress("123 Main St").
        WithCoordinates(40.0, -73.0).
        WithFloor(utesting.NewFloorBuilder().WithLevel(0).Build()).
        Build()

    mockRepo.On("Create", mock.Anything, mock.Anything).Return(nil)

    uc := NewBuildingUseCase(mockRepo, mockLogger)
    result, err := uc.CreateBuilding(context.Background(), building)

    require.NoError(t, err)
    utesting.AssertBuildingEqual(t, building, result)
    utesting.AssertFloorCount(t, result, 1)
}
```

**Result**: 60% less code, more readable, easier to maintain!

## Phase 3: Automated Mock Generation (Optional)

ArxOS now supports **automatic mock generation** using mockery. This provides an alternative to manual mocks with auto-sync capabilities.

### Quick Start

```bash
# Install mockery (one-time)
make install-mockery

# Generate mocks from interfaces
make mocks

# Verify generated mocks
make mocks-verify
```

### Generated vs Manual Mocks

**Manual Mocks (This Package)**:
- ✅ Curated and documented
- ✅ Integrated with builders, fixtures, and assertions
- ✅ Perfect for day-to-day testing
- Location: `internal/usecase/testing/`

**Generated Mocks (Phase 3)**:
- ✅ Auto-sync with interface changes
- ✅ 100% interface coverage
- ✅ Good for comprehensive testing
- Location: `internal/mocks/`

**Use whichever fits your needs!** They complement each other.

### Documentation

See `MOCK_GENERATION.md` in the project root for complete Phase 3 documentation.

## Questions?

See `doc.go` for package-level documentation and examples.

