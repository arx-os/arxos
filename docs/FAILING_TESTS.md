# Failing Tests - Complete Inventory

**Last Updated:** October 17, 2025
**Test Pass Rate:** 59% (16 packages pass, 11 packages fail)
**Total Failing Packages:** 11

---

## Critical Summary

**Cannot deploy with this many failing tests.** This document catalogs every failing test package and test case to provide a clear action plan for fixing them.

---

## Failing Test Packages

### 1. `internal/cli/commands` (1 failing test)
**Package Status:** FAIL

#### Failing Tests:
- `TestInitCommandWithInvalidMode`

#### Priority: MEDIUM
Init command is not critical path for basic CRUD operations.

---

### 2. `internal/config` (14 failing tests) ⚠️ CRITICAL
**Package Status:** FAIL

#### Failing Tests:
1. `TestMigrateConfig`
2. `TestMigrateConfig_SourceNotFound`
3. `TestMigrateConfig_InvalidYAML`
4. `TestGetServiceConfigValue`
5. `TestConfigTemplates`
   - Subtest: `cloud`
   - Subtest: `hybrid`
   - Subtest: `production`
6. `TestCreateConfigFromTemplate`
   - Subtest: `production_template`
7. `TestConfigSaveAndLoad`
8. `TestConfigSaveJSON`
9. `TestConfigCloudValidation`
   - Subtest: `valid_cloud_config`
   - Subtest: `cloud_enabled_but_no_URL`
   - Subtest: `invalid_URL`
   - Subtest: `sync_enabled_but_no_interval`
10. `TestConfigFeatureValidation`
    - Subtest: `cloud_sync_without_cloud`
    - Subtest: `offline_mode_with_cloud_sync`
11. `TestConfigTUIValidation`
12. `TestConfigInstallationValidation`
13. `TestConfigValidationIntegration`

#### Priority: HIGH
Config system affects entire application. All config tests failing suggests fundamental issue.

---

### 3. `internal/infrastructure/ifc` (5 failing tests) ⚠️ CRITICAL
**Package Status:** FAIL

#### Failing Tests:
1. `TestNativeParser_ParseIFC`
2. `TestIFCService_ParseIFC`
3. `TestIfcOpenShellClient_Integration`
4. `TestIfcOpenShellClient_ErrorHandling` (2 second timeout)
5. `TestIFCService_Integration`

#### Priority: HIGH
IFC import is a claimed "core feature." All IFC tests failing means feature is broken.

---

### 4. `internal/infrastructure/postgis` (7 failing tests) ⚠️ CRITICAL
**Package Status:** FAIL

#### Failing Tests:
1. `TestObjectRepository_StoreAndLoad_SmallObject`
2. `TestObjectRepository_StoreAndLoad_MediumObject`
3. `TestObjectRepository_StoreAndLoad_LargeObject`
4. `TestObjectRepository_IncrementRef`
5. `TestObjectRepository_DecrementRef`
6. `TestObjectRepository_Deduplication`
7. `TestBuildingRepository_CoordinateParsing`

#### Priority: HIGH
PostGIS is core database layer. Object storage and coordinate parsing failures mean spatial features don't work.

---

### 5. `pkg/auth` (1 failing test)
**Package Status:** FAIL

#### Failing Tests:
- `TestJWTManager`

#### Priority: MEDIUM
Auth is important but isolated. Single test failure might be fixable quickly.

---

### 6. `test/integration/api` (10 failing tests)
**Package Status:** FAIL

#### Failing Tests:
1. `TestBuildingAPI`
2. `TestEquipmentAPI`
3. `TestBASAPI`
4. `TestErrorHandling`
5. `TestFloorRoomRESTAPI`
6. `TestHTTPAPI`
7. `TestGraphQLAPI`
8. `TestWebSocketAPI`
9. `TestAuthenticationAPI`
10. `TestIFCImportEndpoint`

#### Priority: HIGH
These are integration tests proving API actually works. All failing means HTTP API is untested.

---

### 7. `test/integration/cross_platform` (5 failing tests)
**Package Status:** FAIL

#### Failing Tests:
1. `TestIntegration_CompleteWorkflow`
2. `TestCLIToWebIntegration` (2 second timeout)
3. `TestWebToCLIIntegration` (2 second timeout)
4. `TestMobileToBackendIntegration` (2 second timeout)
5. `TestRealTimeSyncIntegration` (2 second timeout)
6. `TestDataConsistencyIntegration` (2 second timeout)

#### Priority: MEDIUM
Cross-platform integration is ambitious. These tests might be testing non-existent mobile app.

---

### 8. `test/integration/performance` (3 failing tests)
**Package Status:** FAIL

#### Failing Tests:
1. `TestLoadTesting` (2 second timeout)
2. `TestStressTesting` (2 second timeout)
3. `TestMemoryUsage` (20 second timeout)

#### Priority: LOW
Performance testing is premature when basic features don't work. Can defer.

---

### 9. `test/integration/repository` (BUILD FAILED) ⚠️
**Package Status:** FAIL TO BUILD

#### Status:
Package won't even compile. Likely missing imports or syntax errors.

#### Priority: HIGH
Must fix build errors before can run any tests.

---

### 10. `test/integration/services` (8 failing tests)
**Package Status:** FAIL

#### Failing Tests:
1. `TestBuildingServiceIntegration` (2 second timeout)
2. `TestEquipmentServiceIntegration` (2 second timeout)
3. `TestIFCServiceIntegration` (2 second timeout)
4. `TestSyncServiceIntegration` (2 second timeout)
5. `TestDatabaseIntegration` (2 second timeout)
6. `TestVersionControl_CompleteWorkflow`
7. `TestVersionControl_SnapshotPerformance`
8. `TestVersionControl_DiffPerformance`
9. `TestVersionControl_ContentDeduplication`

#### Priority: HIGH
Service integration tests prove services work together. All timeouts suggest database not connected.

---

### 11. `test/integration/workflow` (BUILD FAILED) ⚠️
**Package Status:** FAIL TO BUILD

#### Status:
Package won't even compile. Likely missing imports or syntax errors.

#### Priority: HIGH
Must fix build errors before can run any tests.

---

## Summary by Priority

### Must Fix First (Build Failures)
1. `test/integration/repository` - won't build
2. `test/integration/workflow` - won't build

### Critical (Blocking Deployment)
1. `internal/config` - 14 tests failing (affects entire system)
2. `internal/infrastructure/ifc` - 5 tests failing (core feature broken)
3. `internal/infrastructure/postgis` - 7 tests failing (database layer broken)
4. `test/integration/api` - 10 tests failing (HTTP API untested)
5. `test/integration/services` - 8 tests failing (services don't integrate)

### Medium Priority
1. `internal/cli/commands` - 1 test failing
2. `pkg/auth` - 1 test failing
3. `test/integration/cross_platform` - 5 tests (might be testing mobile app that doesn't exist)

### Low Priority (Defer)
1. `test/integration/performance` - 3 tests (premature optimization)

---

## Recommended Action Plan

### Week 1: Fix Build Errors
1. Fix `test/integration/repository` build failure
2. Fix `test/integration/workflow` build failure
3. **Goal:** All packages compile

### Week 2: Fix Core Infrastructure
1. Fix all 14 `internal/config` tests
2. Fix 7 `internal/infrastructure/postgis` tests
3. **Goal:** Config and database layers work

### Week 3: Fix Feature Tests
1. Fix all 5 `internal/infrastructure/ifc` tests
2. Fix 10 `test/integration/api` tests
3. **Goal:** Core features validated

### Week 4: Fix Integration Tests
1. Fix 8 `test/integration/services` tests
2. Fix remaining CLI/auth tests
3. **Goal:** 100% test pass rate

### After All Tests Pass
Only then:
- Add new features
- Write end-to-end workflow
- Deploy to workplace

---

## Test Output Location

Full test output can be generated with:
```bash
cd /Users/joelpate/repos/arxos
go test ./... -v 2>&1 | tee test-results.txt
```

---

## Notes

**Timeout Pattern:** Many integration tests fail with 2-second timeouts. This suggests:
- Database not connected during tests
- Test setup/teardown broken
- Missing test fixtures
- Tests trying to connect to non-existent services

**Build Failures:** Two test packages won't compile. Fix these first before worrying about test logic.

**Config Tests:** All 14 config tests failing suggests the config validation logic doesn't match the test expectations. Either:
- Fix the config code, or
- Fix the tests, or
- Delete the tests and document what config actually does

---

**Reality:** You can't deploy code where 41% of tests fail. Fix the tests or remove them.

