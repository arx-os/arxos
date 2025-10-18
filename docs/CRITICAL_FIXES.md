# Critical Test Fixes - Priority Order

**Date:** October 17, 2025
**Engineer:** Following best practices - fix one at a time, verify, move on

---

## Top 5 Critical Issues (In Order)

### 1. Build Error: `test/integration/repository` 🔴 BLOCKING
**Priority:** CRITICAL (must fix first - prevents all repository tests from running)

**Error:**
```
test/integration/repository/crud_test.go:22:15: undefined: setupTestContainer
```

**Files affected:**
- `test/integration/repository/crud_test.go` (4 references)

**Root cause:** Missing test helper function `setupTestContainer`

**Fix:**
- Check if `setupTestContainer` exists in other test files
- Either create it or fix the imports

**Estimated time:** 15-30 minutes

---

### 2. Build Error: `test/integration/workflow` 🔴 BLOCKING
**Priority:** CRITICAL (must fix second - prevents all workflow tests from running)

**Error:**
```
test/integration/workflow/complete_workflows_test.go:25:15: undefined: setupTestContainer
test/integration/workflow/ifc_import_test.go:23:15: undefined: setupTestContainer
```

**Files affected:**
- `test/integration/workflow/complete_workflows_test.go` (5 references)
- `test/integration/workflow/ifc_import_test.go` (2 references)

**Root cause:** Same as #1 - missing test helper function

**Fix:** Same as #1

**Estimated time:** 5-10 minutes (after #1 is fixed)

---

### 3. Panic: `TestInitCommandWithInvalidMode` 🔴 CRITICAL
**Priority:** CRITICAL (nil pointer dereference panic)

**Error:**
```
panic: runtime error: invalid memory address or nil pointer dereference
Location: /Users/joelpate/repos/arxos/internal/cli/commands/init_test.go:66
```

**Root cause:** Test expects error but got nil, then tries to dereference nil

**Fix:**
- Test expects init command to fail with invalid mode
- Command is succeeding when it should fail
- Either fix the command validation or fix the test expectation

**Estimated time:** 15-20 minutes

---

### 4. Config Tests: All Failing (14 tests) ⚠️ HIGH
**Priority:** HIGH (affects entire config system)

**Key failures:**
```
TestMigrateConfig - version string format mismatch
TestMigrateConfig_SourceNotFound - unexpected error on expected error
TestMigrateConfig_InvalidYAML - unexpected error on expected error
TestGetServiceConfigValue - key not found
```

**Pattern:** Tests expect certain error handling but getting different errors

**Root cause:** Test expectations don't match actual config behavior

**Fix:** Review each test, understand what config system actually does, update tests to match

**Estimated time:** 2-3 hours

---

### 5. IFC Client Tests: All Failing (5 tests) ⚠️ HIGH
**Priority:** HIGH (core feature)

**Expected failures:**
```
TestNativeParser_ParseIFC
TestIFCService_ParseIFC
TestIfcOpenShellClient_Integration (2s timeout)
TestIfcOpenShellClient_ErrorHandling (2s timeout)
TestIFCService_Integration
```

**Pattern:** Timeouts suggest service not running or not reachable

**Root cause:** Tests trying to connect to IfcOpenShell Python service that's not running

**Fix:**
- Either mock the service for unit tests
- Or ensure service is running for integration tests
- Or skip tests if service unavailable

**Estimated time:** 1-2 hours

---

## Fix Strategy (Best Engineering Practice)

### Phase 1: Fix Build Errors (1 hour)
✅ **Why first:** Can't run tests if code doesn't compile

1. Fix `test/integration/repository` build error
2. Fix `test/integration/workflow` build error
3. Verify both packages now compile (even if tests fail)

### Phase 2: Fix Panic (30 minutes)
✅ **Why second:** Panics are critical bugs

1. Fix `TestInitCommandWithInvalidMode` nil pointer dereference
2. Verify test either passes or fails gracefully (no panic)

### Phase 3: Fix Config Tests (2-3 hours)
✅ **Why third:** Config affects entire system

1. Fix one test at a time
2. Run test after each fix
3. Ensure each passes before moving to next

### Phase 4: Fix IFC Tests (1-2 hours)
✅ **Why fourth:** Core feature, but isolated

1. Determine if IfcOpenShell service should be mocked or real
2. Fix tests accordingly
3. Document service requirements

---

## Engineering Principles

1. **Fix one thing at a time** - Don't try to fix everything at once
2. **Verify after each fix** - Run the specific test to ensure it passes
3. **Commit after each fix** - Keep changes isolated and reversible
4. **Don't skip understanding** - If you don't know why it failed, investigate
5. **Update docs as you go** - Keep FAILING_TESTS.md updated

---

## Commands to Use

```bash
# Fix build errors first
go build ./test/integration/repository/...
go build ./test/integration/workflow/...

# Test specific package
go test ./internal/cli/commands -v -run TestInitCommandWithInvalidMode

# Test specific config test
go test ./internal/config -v -run TestMigrateConfig

# Test all config tests
go test ./internal/config -v

# Test IFC
go test ./internal/infrastructure/ifc -v

# Full test run (only after all fixes)
go test ./...
```

---

## Success Criteria

- [ ] `test/integration/repository` compiles
- [ ] `test/integration/workflow` compiles
- [ ] `TestInitCommandWithInvalidMode` passes (or fails gracefully)
- [ ] All 14 config tests pass
- [ ] All 5 IFC tests pass
- [ ] Overall test pass rate: 100%

---

**Current Status:** Ready to start fixing
**Next Action:** Investigate and fix `setupTestContainer` missing function

