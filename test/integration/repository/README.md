# Repository Integration Tests

Tests for database repository operations (PostGIS implementations).

## Test Files

- `building_test.go` - Building repository CRUD
- `equipment_test.go` - Equipment repository with path queries
- `floor_test.go` - Floor repository
- `room_test.go` - Room repository with geometry
- `bas_test.go` - BAS point and system repositories

## Running

```bash
# Run all repository tests
go test ./test/integration/repository/... -v

# Run specific repository
go test ./test/integration/repository -run TestEquipment -v
```

## Prerequisites

- Test database available
- Migrations run
- Transaction isolation enabled

