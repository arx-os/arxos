# Mobile Game Integration

**Last Updated:** November 2025

---

## Overview

The mobile game integration allows mobile apps (iOS/Android) to interact with the game system for PR review and planning workflows. Mobile apps can load PRs, validate constraints, and retrieve game plans.

---

## FFI Functions

### `arxos_load_pr`

Load a PR for review from mobile app.

**Function Signature:**
```rust
#[no_mangle]
pub unsafe extern "C" fn arxos_load_pr(
    pr_id: *const c_char,
    pr_dir: *const c_char,
    building_name: *const c_char
) -> *mut c_char
```

**Parameters:**
- `pr_id` - PR identifier string
- `pr_dir` - PR directory path (can be NULL for default)
- `building_name` - Building name string

**Returns:**
JSON string with PR summary:
```json
{
  "pr_id": "pr_001",
  "total_items": 5,
  "valid_items": 4,
  "violations": 1,
  "critical_violations": 0,
  "equipment": [...]
}
```

### `arxos_validate_constraints`

Validate equipment placement against constraints.

**Function Signature:**
```rust
#[no_mangle]
pub unsafe extern "C" fn arxos_validate_constraints(
    equipment_json: *const c_char,
    constraints_json: *const c_char
) -> *mut c_char
```

**Parameters:**
- `equipment_json` - Equipment data as JSON
- `constraints_json` - Constraints data as JSON

**Returns:**
JSON validation result:
```json
{
  "is_valid": false,
  "violations": [
    {
      "constraint_id": "spatial_1",
      "type": "Spatial",
      "severity": "Warning",
      "message": "Insufficient clearance: 0.3m (minimum: 0.5m)",
      "suggestion": "Increase spacing between equipment"
    }
  ],
  "warnings": []
}
```

### `arxos_get_game_plan`

Retrieve game plan data from planning session.

**Function Signature:**
```rust
#[no_mangle]
pub unsafe extern "C" fn arxos_get_game_plan(
    session_id: *const c_char,
    building_name: *const c_char
) -> *mut c_char
```

**Returns:**
JSON game plan:
```json
{
  "session_id": "planning_abc123",
  "placements": [...],
  "validation_summary": {
    "total_placements": 10,
    "valid_placements": 9,
    "violations": 2
  },
  "score": 250
}
```

---

## Mobile Workflow Integration

### Mobile → Terminal Workflow

1. **Mobile AR Scan** - Contractor scans room with mobile app
2. **Submit as PR** - Mobile app creates PR with scan data
3. **Terminal Review** - Power user reviews in terminal game:
   ```bash
   arx game review --pr-id mobile_pr_001 --building "Building" --interactive
   ```
4. **Approve/Reject** - Decision made in terminal
5. **Mobile Notification** - Contractor receives feedback in mobile app

### Terminal → Mobile Workflow

1. **Plan in Terminal** - Power user plans equipment placement:
   ```bash
   arx game plan --building "Building" --interactive
   ```
2. **Export Plan** - Export as PR or IFC
3. **Mobile Validation** - Contractor validates plan in field via mobile AR
4. **Confirm/Correct** - Mobile app allows field corrections
5. **Update Plan** - Corrections sync back to terminal

---

## Implementation Status

**Current:** Core game system complete  
**Pending:** Mobile FFI extensions (next phase)

The game system is ready for mobile integration. FFI functions will be added to `src/mobile_ffi/ffi.rs` and wrapped in Swift/Kotlin.

---

## Related Documentation

- **[Mobile FFI Integration](./MOBILE_FFI_INTEGRATION.md)** - General FFI guide
- **[AR Terminal Design](../ar/AR_TERMINAL_DESIGN.md)** - AR + Terminal design

