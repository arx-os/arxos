# Workflow Integration Tests

End-to-end workflow tests validating complete user scenarios.

## Test Files

- `ifc_import_test.go` - IFC import → query → export workflow
- `bas_integration_test.go` - BAS + IFC integration workflow
- `version_control_test.go` - Branch → commit → merge workflow
- `path_query_test.go` - Path query comprehensive tests
- `complete_lifecycle_test.go` - Full building lifecycle

## Running

```bash
# Run all workflow tests
go test ./test/integration/workflow/... -v

# Run specific workflow
go test ./test/integration/workflow -run TestIFCImport -v
```

## Prerequisites

- Test database available
- IfcOpenShell service (for IFC tests)
- Sample test files in fixtures/

