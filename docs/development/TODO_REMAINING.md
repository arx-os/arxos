# Remaining TODOs for ArxOS

## High Priority Production Tasks

### 1. Configuration Management Consolidation ⚠️ **PENDING**
**Status**: Partially implemented, needs consolidation  
**Priority**: High  
**Estimated Effort**: 1-2 days

**Tasks**:
- [ ] Consolidate configuration sources with clear precedence hierarchy
  - Environment variables (highest priority)
  - User config file (`~/.arxos/config.toml`)
  - Project config file (`.arxos/config.toml`)
  - Default configuration (lowest priority)
- [ ] Add comprehensive configuration validation
  - Validate all configuration values on load
  - Provide clear error messages for invalid config
  - Document all configuration options
- [ ] Create configuration schema/documentation
  - List all available config keys
  - Document defaults and acceptable values
  - Provide examples for common configurations

**Files to modify**:
- `src/config/mod.rs` - Add validation and precedence logic
- `docs/API_REFERENCE.md` - Document configuration options (create)

**Current State**: Configuration exists but lacks clear hierarchy and validation.

---

### 2. Mobile CI/CD Workflows ✅ **COMPLETED**
**Status**: Implemented  
**Priority**: High  
**Completed**: December 2024

**Tasks**:
- [x] Create iOS build workflow ✅ **COMPLETED**
  - [x] Build XCFramework for iOS
  - [x] Create iOS app archive
  - [ ] Run iOS unit tests (placeholder - requires Xcode project test config)
  - [ ] Distribute to TestFlight or App Store (requires code signing setup)
- [x] Create Android build workflow ✅ **COMPLETED**
  - [x] Build native libraries (.so files) for Android (all architectures)
  - [x] Run Android unit tests (conditional - requires Gradle test config)
  - [x] Create APK/AAB builds
  - [ ] Distribute to internal testing or Play Store (requires signing keys)
- [x] Add mobile-specific test workflows ✅ **COMPLETED**
  - [x] iOS simulator tests (conditional/placeholder)
  - [x] Android emulator tests (conditional)
  - [x] Mobile FFI integration tests

**Files created**:
- ✅ `.github/workflows/ios-build.yml` - **CREATED**
- ✅ `.github/workflows/android-build.yml` - **CREATED**
- ✅ `.github/workflows/mobile-tests.yml` - **CREATED**
- ✅ `docs/MOBILE_CI_CD.md` - **CREATED**

**Current State**: ✅ Mobile CI/CD workflows fully implemented. Core functionality complete:
- Automatic builds on push/PR
- XCFramework creation for iOS
- Native library builds for all Android architectures
- APK/AAB generation
- Mobile FFI test automation
- Artifact management and retention

**Remaining (Optional/Advanced)**:
- Code signing setup for iOS (TestFlight/App Store)
- Code signing setup for Android (Play Store)
- Enhanced unit test integration (requires project config)

---

### 3. Comprehensive API Reference ⚠️ **PENDING**
**Status**: Partially complete (rustdoc exists, needs compilation)  
**Priority**: Medium  
**Estimated Effort**: 2-3 days

**Tasks**:
- [ ] Create `docs/API_REFERENCE.md` with:
  - All CLI commands with examples
  - All configuration options
  - All FFI functions (C and JNI)
  - All core API types and methods
  - Request/response formats
  - Error codes and handling
- [ ] Generate and publish rustdoc documentation
  - Host on docs.rs or GitHub Pages
  - Include searchable API reference
  - Link from main README
- [ ] Add usage examples for each API
  - CLI command examples
  - FFI usage examples
  - Integration code snippets

**Files to create**:
- `docs/API_REFERENCE.md`
- Configure rustdoc generation
- Set up documentation hosting

**Current State**: Rustdoc comments exist in code, but not compiled into published docs.

**Note:** Building documentation generation (similar concept to rustdoc but for building data) is being explored in `docs/BUILDING_DOCS_CONCEPT.md`. This would allow users to generate HTML documentation from their building data using `arx doc --building "Name"`.

---

### 4. Integration Examples ⚠️ **PENDING**
**Status**: Not created  
**Priority**: Medium  
**Estimated Effort**: 1-2 days

**Tasks**:
- [ ] Create `docs/INTEGRATION_EXAMPLES.md` with:
  - Complete IFC import workflow example
  - AR scan integration workflow
  - Sensor data processing workflow
  - Equipment management workflow
  - Building data export/import
  - Git workflow examples
- [ ] Add code examples for common integrations
  - Mobile app integration
  - Sensor data pipeline
  - CI/CD integration
  - Custom tooling integration
- [ ] Create sample data files for examples
  - Sample IFC files
  - Sample AR scan data
  - Sample sensor data

**Files to create**:
- `docs/INTEGRATION_EXAMPLES.md`
- `examples/` directory with sample workflows

**Current State**: Documentation exists but lacks complete end-to-end examples.

---

### 5. Troubleshooting Guide ⚠️ **PENDING**
**Status**: Partially covered in OPERATIONS.md  
**Priority**: Medium  
**Estimated Effort**: 1 day

**Tasks**:
- [ ] Create `docs/TROUBLESHOOTING.md` with:
  - Common error messages and solutions
  - Performance issues and fixes
  - Git integration problems
  - Mobile FFI issues
  - Configuration problems
  - IFC import issues
  - Build and compilation errors
- [ ] Add diagnostic commands
  - Enhance `arx health` with more diagnostics
  - Add verbose error reporting
  - Add system information collection
- [ ] Create troubleshooting flowchart
  - Decision tree for common problems
  - Quick reference for error codes

**Files to create**:
- `docs/TROUBLESHOOTING.md`

**Current State**: Some troubleshooting info in OPERATIONS.md, but needs dedicated guide.

---

## Lower Priority / Future Improvements

### 6. Data Model Consolidation 🔄 **DEFERRED**
**Status**: Partially addressed (removed legacy fields)  
**Priority**: Low  
**Estimated Effort**: 1 week

**Tasks**:
- [ ] Add `serde` derives to core types
- [ ] Remove `src/yaml/` module (use core types directly)
- [ ] Remove `src/core/conversions.rs`
- [ ] Update all serialization code to use core types
- [ ] Migrate any metadata handling to core types

**Note**: Deferred because `src/yaml/` serves as metadata adapter. Full removal requires larger refactor.

---

### 7. Structured Logging Migration 🔄 **DEFERRED**
**Status**: Cancelled (complexity vs. benefit)  
**Priority**: Low  
**Estimated Effort**: 1 week

**Tasks**:
- [ ] Replace `log::` with `tracing::` throughout codebase
- [ ] Add structured logging with context
- [ ] Configure log levels and filtering
- [ ] Add log aggregation support

**Note**: Deferred due to complexity. Current `log` crate works fine for current needs.

---

### 8. Enhanced Test Coverage 📊 **ONGOING**
**Status**: Good coverage, some gaps remain  
**Priority**: Medium  
**Estimated Effort**: Ongoing

**Tasks**:
- [ ] Add integration tests for complete workflows
- [ ] Add property-based tests for data structures
- [ ] Add performance regression tests
- [ ] Fix test isolation issues (partially addressed)
- [ ] Add mobile FFI integration tests on real devices

**Current State**: ~90% coverage, some edge cases need tests.

---

### 9. Documentation Improvements 📚 **ONGOING**
**Status**: Good foundation, needs expansion  
**Priority**: Low-Medium  
**Estimated Effort**: Ongoing

**Tasks**:
- [ ] Add more code examples to existing docs
- [ ] Create video tutorials
- [ ] Add diagrams for complex workflows
- [ ] Translate documentation to other languages
- [ ] Create quick-start guides for different use cases

---

## Immediate Next Steps (Recommended Order)

1. **Configuration Management** - Consolidates existing functionality
2. **Mobile CI/CD** - Enables automated mobile builds
3. **API Reference** - Completes documentation suite
4. **Integration Examples** - Helps users adopt the system
5. **Troubleshooting Guide** - Improves user experience

---

## Completed Tasks ✅

- ✅ Performance benchmarks and capacity planning (`docs/BENCHMARKS.md`)
- ✅ Error recovery (retry logic, dry-run flags, rollback via Git)
- ✅ Operational runbooks (`docs/OPERATIONS.md`)
- ✅ Health check command (`arx health`)
- ✅ API documentation (comprehensive rustdoc comments)
- ✅ Release automation (GitHub Actions for binaries)
- ✅ Test infrastructure improvements (RAII guards, isolation)
- ✅ Code quality improvements (clippy warnings, refactoring)

---

## Notes

- Most critical functionality is complete
- Remaining items focus on polish, documentation, and automation
- Mobile CI/CD and config consolidation are highest priority for production readiness
- Documentation tasks can be done incrementally

