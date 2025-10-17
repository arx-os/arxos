# HTTP API Integration Tests

Tests for REST API endpoints.

## Test Files

- `auth_test.go` - Authentication and authorization
- `building_test.go` - Building CRUD endpoints
- `equipment_test.go` - Equipment CRUD and path query endpoints
- `floor_room_test.go` - Floor and room endpoints
- `ifc_import_test.go` - IFC import HTTP endpoints

## Running

```bash
# Run all API tests
go test ./test/integration/api/... -v

# Run specific test
go test ./test/integration/api -run TestEquipment -v
```

## Prerequisites

- Test HTTP server started
- JWT authentication configured
- Test database available

