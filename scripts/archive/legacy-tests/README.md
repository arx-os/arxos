# Legacy Test Scripts (Archived)

**Date Archived:** October 19, 2025
**Reason:** Replaced by proper Go testing infrastructure

---

## Why These Were Archived

These shell scripts were used during **early ArxOS development** (Sept-Oct 2025) before comprehensive Go integration tests were implemented.

### What Replaced Them

**Modern Testing Infrastructure:**
- ✅ `go test ./...` - Standard Go test runner
- ✅ `make test` - Makefile test targets
- ✅ `test/integration/api/` - Integration tests (100% pass rate)
- ✅ GitHub Actions CI/CD - Automated testing

### Problems with Legacy Scripts

1. **Outdated paths** - Reference old architecture (`internal/infra/`, `internal/app/di/`)
2. **Superseded** - Go tests are more comprehensive and reliable
3. **Maintenance burden** - Scripts drift from codebase reality
4. **Confusing** - New developers might run outdated tests

---

## Archived Scripts

### Testing Scripts
- `run_tests.sh` (396 lines) - Comprehensive test runner (outdated paths)
- `run_tests.ps1` (368 lines) - Windows test runner (outdated paths)
- `run_integration_tests.sh` (207 lines) - Integration tests (replaced)
- `test-end-to-end.sh` - End-to-end workflow tests
- `test-phase1-complete.sh` (235 lines) - Phase 1 completion tests
- `QUICK_TEST.sh` (184 lines) - Quick manual test commands

### Feature-Specific Tests
- `test_api_endpoint_completion.sh` (188 lines) - API endpoint tests
- `test_frontend_integration.sh` (230 lines) - Frontend tests
- `test_mobile_router.sh` - Mobile API router tests
- `test_mobile_services.sh` (176 lines) - Mobile service tests
- `test_mvp_workflow.sh` - MVP workflow validation
- `test_path_queries.sh` (179 lines) - Path query tests
- `test_postgis_integration.sh` (284 lines) - PostGIS integration
- `test_tui_spatial.sh` - TUI spatial feature tests
- `test_vc_endpoints.sh` - Version control endpoint tests

### Test Utilities
- `test/test_converter_accuracy.sh` - Converter accuracy tests

---

## Current Testing Approach

### Unit Tests
```bash
# Run all tests
go test ./...

# With coverage
go test -coverprofile=coverage.out ./...
go tool cover -html=coverage.out
```

### Integration Tests
```bash
# Run integration tests
go test ./test/integration/... -v -count=1

# Specific test suites
go test ./test/integration/api/building_api_test.go -v
go test ./test/integration/api/ifc_import_integration_test.go -v
go test ./test/integration/api/bas_import_integration_test.go -v
```

### Using Makefile
```bash
make test                    # Run all tests
make test-integration        # Run integration tests
make test-coverage           # Generate coverage report
make test-race               # Run with race detection
```

---

## Historical Value

These scripts remain in the archive for:
- **Reference** - Understanding early testing approach
- **Git history** - Part of development evolution
- **Documentation** - Shows what features were tested
- **Learning** - Examples of shell-based testing (avoid this!)

---

## Migration Notes

**If you need to understand what a script tested:**
1. Check `test/integration/` for equivalent Go tests
2. Review git history: `git log -- scripts/test-*.sh`
3. See archived script for feature coverage

**Modern equivalent:**
- Old: `./scripts/test_postgis_integration.sh`
- New: `go test ./test/integration/api/... -v`

---

**Status:** 📚 Historical reference only - DO NOT USE for testing
**Replacement:** Use Go tests in `test/integration/` directory
**Archived By:** Cleanup session on October 19, 2025

