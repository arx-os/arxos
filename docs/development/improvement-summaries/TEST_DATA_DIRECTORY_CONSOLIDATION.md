# Test Data Directory Consolidation

**Date:** January 2025  
**Status:** ✅ Complete

---

## Problem

The repository had **two test data directories** with confusing naming:
- `test_data/` (underscore) - contained actual test fixtures
- `test-data/` (hyphen) - newly created, contained only one file

This caused:
- Confusion about which directory to use
- Duplication and redundancy
- `.gitignore` complexity trying to handle both
- Test fixtures in `test_data/` were being ignored by Git

---

## Solution

### Consolidation
- **Single directory**: `test_data/` (underscore version)
- **Reason**: Already extensively referenced in codebase via `include_str!("../../test_data/...")`
- **Moved**: `test-data/test_building.yaml` → `test_data/test_building.yaml`
- **Removed**: Empty `test-data/` directory

### Git Tracking
- **Fixed `.gitignore`**: Simplified to ignore only build artifacts (`.tmp`, `.bak`, `~`)
- **Added fixtures to Git**: All test fixtures now properly tracked:
  - IFC files: `Building-Architecture.ifc`, `Building-Hvac.ifc`, `sample_building.ifc`
  - AR samples: `sample-ar-scan.json`
  - Sensor data: `sensor-data/sample_temperature_reading.yaml`, `sensor-data/sample_air_quality.json`
  - Building fixtures: `test_building.yaml`

---

## Directory Structure

### Before
```
/
├── test_data/          (ignored by .gitignore, but contains fixtures!)
│   ├── Building-Architecture.ifc
│   ├── Building-Hvac.ifc
│   ├── sample-ar-scan.json
│   ├── sample_building.ifc
│   └── sensor-data/
│       ├── sample_temperature_reading.yaml
│       └── sample_air_quality.json
└── test-data/          (newly created, barely used)
    └── test_building.yaml
```

### After
```
/
└── test_data/          (single source of truth, all fixtures tracked)
    ├── Building-Architecture.ifc ✅ (now tracked)
    ├── Building-Hvac.ifc ✅ (now tracked)
    ├── sample-ar-scan.json ✅ (now tracked)
    ├── sample_building.ifc ✅ (now tracked)
    ├── test_building.yaml ✅ (moved from test-data/)
    └── sensor-data/ ✅ (now tracked)
        ├── sample_temperature_reading.yaml
        └── sample_air_quality.json
```

---

## Code References

Tests reference `test_data/` using `include_str!()`:

```rust
// tests/integration_tests.rs
let json_data = include_str!("../test_data/sample-ar-scan.json");

// tests/commands/sensors_tests.rs
let yaml_content = include_str!("../../test_data/sensor-data/sample_temperature_reading.yaml");

// tests/commands/ar_tests.rs
let ar_scan_data = include_str!("../../test_data/sample-ar-scan.json");
```

**No code changes needed** - all references already use `test_data/` (underscore).

---

## .gitignore Changes

### Before
```gitignore
# Test data directories (but allow tracked fixtures)
test-data/*
!test-data/.gitkeep
!test-data/*.yaml
!test-data/*.yml
!test-data/*.md
test_data/  # ❌ This ignored ALL fixtures!
```

### After
```gitignore
# Test data directories (ignore build artifacts, but track fixtures)
# test_data/ contains tracked test fixtures (IFC files, samples, etc.)
test_data/*.tmp
test_data/*.bak
test_data/*~
# Allow all fixture files in test_data/ to be tracked
```

**Result**: Only temporary/backup files are ignored; all fixtures are tracked.

---

## Benefits

1. **✅ Single Source of Truth**: One directory, clear purpose
2. **✅ Proper Git Tracking**: Test fixtures now version-controlled
3. **✅ Simpler `.gitignore`**: No complex negation patterns
4. **✅ No Code Changes**: Existing test references already correct
5. **✅ Better Organization**: All fixtures in one logical location

---

## Verification

```bash
# Verify single directory exists
$ find . -type d -name "*test*data*" | grep -v ".git" | grep -v "target"
./test_data

# Verify fixtures are tracked
$ git ls-files test_data/
test_data/Building-Architecture.ifc
test_data/Building-Hvac.ifc
test_data/sample-ar-scan.json
test_data/sample_building.ifc
test_data/sensor-data/sample_air_quality.json
test_data/sensor-data/sample_temperature_reading.yaml
test_data/test_building.yaml

# Verify tests can find fixtures
$ cargo test --test integration_tests test_ar_scan_parsing
✅ test_ar_scan_parsing ... ok
```

---

## Related Files

- **`.gitignore`**: Updated test data patterns
- **`test_data/`**: Consolidated fixture directory
- **Tests**: All use `include_str!("../../test_data/...")` (no changes needed)

---

**Status:** ✅ Complete  
**Impact:** Low (organizational cleanup, no functional changes)  
**Breaking Changes:** None
