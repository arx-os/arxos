# ADR 006: TUI Data Integration Architecture

## Status
✅ **Accepted and Implemented**

## Context

The Terminal User Interface (TUI) needed to display real building data from the PostgreSQL/PostGIS database. The initial implementation had the TUI data service holding a `domain.Database` interface with TODO comments and mock data, preventing it from actually querying the database.

### Problem

```go
// BEFORE - Broken Architecture
type DataService struct {
    db domain.Database  // Only has Connect(), Close(), Health()
                        // Cannot query - no Query() or Exec() methods
}

// Methods had TODOs like this:
func (ds *DataService) getBuilding(ctx context.Context, buildingID string) {
    // TODO: Implement PostGIS spatial query for building bounds
    // SELECT b.*, ST_XMin(ST_Extent(e.position)) ...

    // Simulate realistic building data
    return &building.BuildingModel{
        ID:   buildingID,
        Name: "ArxOS Demo Building",  // MOCK DATA
    }, nil
}
```

**Issues**:
1. `domain.Database` interface had no query methods
2. 7 TODO comments with commented SQL queries
3. 100% mock data throughout TUI
4. Violated Clean Architecture (TUI couldn't access real data)
5. No integration with tested repository layer

## Decision

**Refactor TUI DataService to use repositories instead of raw database access.**

This follows Clean Architecture principles by:
- Depending on domain interfaces (repositories)
- Reusing tested code (53 repository integration tests)
- Proper separation of concerns
- Type-safe domain models

### New Architecture

```go
// AFTER - Clean Architecture
type DataService struct {
    buildingRepo  domain.BuildingRepository
    equipmentRepo domain.EquipmentRepository
    floorRepo     domain.FloorRepository
}

func (ds *DataService) getBuilding(ctx context.Context, buildingID string) {
    // Use repository to get building data
    bldg, err := ds.buildingRepo.GetByID(ctx, buildingID)
    if err != nil {
        return nil, fmt.Errorf("failed to get building: %w", err)
    }

    // Convert domain.Building to TUI model
    return &building.BuildingModel{
        ID:      bldg.ID.String(),
        Name:    bldg.Name,        // REAL DATA
        Address: bldg.Address,     // REAL DATA
        ...
    }, nil
}
```

## Consequences

### Positive ✅

1. **Reuses Tested Code**
   - Leverages 53 existing repository integration tests
   - No need to re-test data access logic
   - Single source of truth for queries

2. **Clean Architecture Compliance**
   - TUI layer depends on domain interfaces
   - No infrastructure details leaked to presentation
   - Proper dependency direction: TUI → Domain ← Infrastructure

3. **Type Safety**
   - Uses domain models, not raw SQL result types
   - Compile-time checking of data access
   - No SQL injection risks

4. **Maintainability**
   - Changes to data access logic in one place
   - TUI automatically benefits from repository improvements
   - Easier to understand and modify

5. **Testability**
   - Can mock repositories for TUI unit tests
   - Integration tests reuse repository infrastructure
   - Clear separation enables focused testing

### Negative ❌

1. **Slight Performance Overhead**
   - Repository layer adds minimal abstraction cost
   - **Mitigation**: Negligible for TUI use case (human interaction speed)

2. **Cannot Use Custom SQL**
   - Limited to repository methods
   - **Mitigation**: Add methods to repositories as needed
   - **Benefit**: Encourages consistent data access patterns

### Neutral ~

1. **Additional Dependency Injection**
   - Need to pass 3 repositories instead of 1 database
   - **Tradeoff**: More explicit dependencies, better testability

## Implementation

### Files Modified:

1. **`internal/tui/services/data_service.go`** - Core refactoring
   - Changed constructor signature
   - Implemented 7 methods with real repository calls
   - Removed all mock data and TODOs

2. **`internal/tui/main.go`** - Repository injection
   - Added `getRepositories()` helper
   - Updated all TUI run methods
   - Proper repository instantiation

3. **`internal/infrastructure/database.go`** - Helper method
   - Added `GetDB()` to expose underlying connection
   - Enables repository creation from Database instance

4. **`internal/tui/models/spatial_query.go`** - Cleanup
   - Removed deprecated PostGISClient dependency
   - Uses DataService directly

5. **`internal/tui/demo.go`** - Demo mode support
   - Updated to handle nil repositories
   - Graceful degradation for demo mode

### Methods Implemented (7 total):

- `getBuilding()` - Repository-based building retrieval
- `getFloors()` - Floor retrieval with dynamic confidence
- `getEquipment()` - Equipment with 3D positions
- `getAlerts()` - Dynamic alert generation from status
- `calculateSpatialMetrics()` - Real metric calculations
- `GetEquipmentByFloor()` - Floor-specific queries
- `GetSpatialData()` - Dynamic bounds calculation

### Code Quality:

- ✅ All tests pass (usecase + TUI)
- ✅ Full project compiles
- ✅ 0 TODO comments remain (was 7)
- ✅ 0% mock data (was 100%)
- ✅ Follows Go best practices
- ✅ Clean Architecture compliant

## Alternatives Considered

### Alternative 1: Add Query Methods to domain.Database

```go
type Database interface {
    Connect() error
    Close() error
    Query(ctx context.Context, sql string, args ...any) (*sql.Rows, error)
    Exec(ctx context.Context, sql string, args ...any) (sql.Result, error)
}
```

**Rejected because**:
- Violates Clean Architecture (infrastructure details in domain)
- Requires SQL knowledge in presentation layer
- No type safety
- Duplicates repository logic
- Hard to test

### Alternative 2: Create TUI-Specific Repositories

```go
type TUIBuildingRepository interface {
    GetBuildingForDisplay(ctx, id) (*TUIBuildingModel, error)
}
```

**Rejected because**:
- Creates duplicate repositories
- Violates DRY principle
- More code to maintain
- Conversion can happen in service layer

### Alternative 3: Direct SQL in TUI

```go
func (ds *DataService) getBuilding(ctx, id) {
    db.Query("SELECT * FROM buildings WHERE id = $1", id)
}
```

**Rejected because**:
- Violates Clean Architecture
- Bypasses tested repositories
- SQL injection risks
- No transaction support
- Hard to mock for tests

## Lessons Learned

1. **Clean Architecture isn't just theory** - Following it properly makes code more maintainable
2. **Reuse tested code** - Don't duplicate data access logic
3. **Type safety matters** - Domain models prevent runtime errors
4. **Graceful degradation** - Demo mode with nil repositories works fine

## References

- Clean Architecture (Robert C. Martin)
- Go Project Layout Standards
- ArxOS Clean Architecture Documentation
- Repository Pattern Implementation

---

**Author**: ArxOS Engineering Team
**Date**: October 8, 2025
**Supersedes**: N/A
**Related**: ADR-001 (Clean Architecture), ADR-002 (PostGIS Integration)

