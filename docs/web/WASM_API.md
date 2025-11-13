# WASM API Reference

**Version:** 2.0
**Last Updated:** 2025-11-12
**Status:** Design Phase

---

## Overview

This document defines the complete interface between the Rust core (`crates/arx`, `crates/arxos`) and the Progressive Web Application via WebAssembly bindings (`crates/arxos-wasm`). All exports use `wasm-bindgen` with JSON serialization for complex types.

**Design Principles:**
- Keep WASM exports minimal and focused
- Use JSON for complex data structures (leverage serde)
- Return `Result<T, E>` types for error handling
- Avoid large data transfers (use pagination where needed)
- Document TypeScript types alongside Rust exports

---

## Table of Contents

1. [Command Module](#command-module)
2. [Geometry Module](#geometry-module)
3. [Validation Module](#validation-module)
4. [AR Module](#ar-module)
5. [Export Module](#export-module)
6. [Utility Module](#utility-module)
7. [TypeScript Type Definitions](#typescript-type-definitions)
8. [Error Handling](#error-handling)
9. [Implementation Status](#implementation-status)

---

## Command Module

**Purpose:** Expose command catalog and local command execution for M02.

### Rust Exports

```rust
// crates/arxos-wasm/src/commands.rs

use wasm_bindgen::prelude::*;

/// Get the full command catalog metadata
/// Returns: JSON array of CommandMetadata
#[wasm_bindgen]
pub fn get_command_catalog() -> Result<String, JsValue>;

/// Execute a command locally (stub implementation for M02)
/// Returns: JSON CommandResult
#[wasm_bindgen]
pub fn execute_command_local(name: &str, args: &str) -> Result<String, JsValue>;

/// Get help text for a specific command
#[wasm_bindgen]
pub fn get_command_help(name: &str) -> Result<String, JsValue>;
```

### TypeScript Interface

```typescript
// pwa/src/lib/wasm/commands.ts

export interface CommandMetadata {
  name: string;
  description: string;
  category: string; // "building" | "floor" | "equipment" | "git" | "ar" | "system"
  aliases?: string[];
  args: CommandArg[];
  examples: string[];
  requiresAgent: boolean; // true if needs desktop agent
}

export interface CommandArg {
  name: string;
  description: string;
  required: boolean;
  type: "string" | "number" | "boolean" | "path";
  default?: string;
}

export interface CommandResult {
  success: boolean;
  output: string;
  error?: string;
  duration_ms: number;
}

export async function getCommandCatalog(): Promise<CommandMetadata[]>;
export async function executeCommandLocal(name: string, args: Record<string, any>): Promise<CommandResult>;
export async function getCommandHelp(name: string): Promise<string>;
```

### Implementation Status

| Function | Status | Milestone | Notes |
|----------|--------|-----------|-------|
| `get_command_catalog` | ⬜ Not Started | M02 | Load from `arx-command-catalog` |
| `execute_command_local` | ⬜ Not Started | M02 | Mock implementation initially |
| `get_command_help` | ⬜ Not Started | M02 | Extract from catalog metadata |

---

## Geometry Module

**Purpose:** Expose building spatial data for M03 floor viewer and M04 editing.

### Rust Exports

```rust
// crates/arxos-wasm/src/geometry.rs

use wasm_bindgen::prelude::*;

/// Get building hierarchy (buildings only)
/// Returns: JSON array of BuildingSummary
#[wasm_bindgen]
pub fn get_buildings() -> Result<String, JsValue>;

/// Get full building data including all floors
/// Returns: JSON Building
#[wasm_bindgen]
pub fn get_building(arxos_path: &str) -> Result<String, JsValue>;

/// Get specific floor with rooms and equipment
/// Returns: JSON Floor
#[wasm_bindgen]
pub fn get_floor(building_path: &str, floor_id: &str) -> Result<String, JsValue>;

/// Get rooms for a specific floor
/// Returns: JSON array of Room
#[wasm_bindgen]
pub fn get_rooms(floor_id: &str) -> Result<String, JsValue>;

/// Get equipment for a specific room
/// Returns: JSON array of Equipment
#[wasm_bindgen]
pub fn get_equipment(room_id: &str) -> Result<String, JsValue>;

/// Get bounding box for a floor (for viewport calculation)
/// Returns: JSON BoundingBox
#[wasm_bindgen]
pub fn get_floor_bounds(floor_id: &str) -> Result<String, JsValue>;
```

### TypeScript Interface

```typescript
// pwa/src/lib/wasm/geometry.ts

export interface BuildingSummary {
  path: string; // ArxAddress path
  name: string;
  floor_count: number;
  last_modified: string; // ISO 8601
}

export interface Building {
  path: string;
  name: string;
  address?: string;
  floors: Floor[];
  metadata: Record<string, any>;
}

export interface Floor {
  id: string;
  name: string;
  level: number;
  elevation: number; // meters
  height: number; // floor-to-ceiling height
  rooms: Room[];
  bounds: BoundingBox;
}

export interface Room {
  id: string;
  name: string;
  room_type: string; // "mech" | "elec" | "plumb" | "office" | etc.
  bounds: BoundingBox;
  polygon?: Coordinate[]; // 2D outline
  equipment: Equipment[];
}

export interface Equipment {
  id: string;
  name: string;
  equipment_type: string;
  position: Coordinate;
  bounds?: BoundingBox;
  properties: Record<string, any>;
}

export interface Coordinate {
  x: number;
  y: number;
  z?: number;
}

export interface BoundingBox {
  min: Coordinate;
  max: Coordinate;
}

export async function getBuildings(): Promise<BuildingSummary[]>;
export async function getBuilding(path: string): Promise<Building>;
export async function getFloor(buildingPath: string, floorId: string): Promise<Floor>;
export async function getRooms(floorId: string): Promise<Room[]>;
export async function getEquipment(roomId: string): Promise<Equipment[]>;
export async function getFloorBounds(floorId: string): Promise<BoundingBox>;
```

### Implementation Status

| Function | Status | Milestone | Notes |
|----------|--------|-----------|-------|
| `get_buildings` | ⬜ Not Started | M03 | List from current repo |
| `get_building` | ⬜ Not Started | M03 | Load from YAML |
| `get_floor` | ⬜ Not Started | M03 | Core M03 functionality |
| `get_rooms` | ⬜ Not Started | M03 | For rendering |
| `get_equipment` | ⬜ Not Started | M03 | For rendering |
| `get_floor_bounds` | ⬜ Not Started | M03 | Viewport initialization |

---

## Validation Module

**Purpose:** Validate edits client-side before sending to agent (M04).

### Rust Exports

```rust
// crates/arxos-wasm/src/validation.rs

use wasm_bindgen::prelude::*;

/// Validate room edit (bounds, overlaps, constraints)
/// Returns: JSON ValidationResult
#[wasm_bindgen]
pub fn validate_room_edit(room_json: &str) -> Result<String, JsValue>;

/// Validate equipment placement (constraints, spatial rules)
/// Returns: JSON ValidationResult
#[wasm_bindgen]
pub fn validate_equipment_placement(equipment_json: &str, room_id: &str) -> Result<String, JsValue>;

/// Check for room overlaps on a floor
/// Returns: JSON array of Overlap
#[wasm_bindgen]
pub fn check_room_overlaps(floor_id: &str, room_json: &str) -> Result<String, JsValue>;

/// Validate batch of edits together
/// Returns: JSON BatchValidationResult
#[wasm_bindgen]
pub fn validate_batch_edits(edits_json: &str) -> Result<String, JsValue>;
```

### TypeScript Interface

```typescript
// pwa/src/lib/wasm/validation.ts

export interface ValidationResult {
  valid: boolean;
  errors: ValidationError[];
  warnings: ValidationWarning[];
}

export interface ValidationError {
  code: string;
  message: string;
  field?: string;
  suggestion?: string;
}

export interface ValidationWarning {
  code: string;
  message: string;
  field?: string;
}

export interface Overlap {
  room_a: string;
  room_b: string;
  overlap_area: number;
  severity: "warning" | "error";
}

export interface BatchValidationResult {
  valid: boolean;
  results: Record<string, ValidationResult>; // edit_id -> result
  global_errors: ValidationError[]; // cross-edit errors
}

export async function validateRoomEdit(room: Room): Promise<ValidationResult>;
export async function validateEquipmentPlacement(equipment: Equipment, roomId: string): Promise<ValidationResult>;
export async function checkRoomOverlaps(floorId: string, room: Room): Promise<Overlap[]>;
export async function validateBatchEdits(edits: Edit[]): Promise<BatchValidationResult>;
```

### Implementation Status

| Function | Status | Milestone | Notes |
|----------|--------|-----------|-------|
| `validate_room_edit` | ⬜ Not Started | M04 | Real-time validation |
| `validate_equipment_placement` | ⬜ Not Started | M04 | Game constraints |
| `check_room_overlaps` | ⬜ Not Started | M04 | Spatial checks |
| `validate_batch_edits` | ⬜ Not Started | M04 | Before commit |

---

## AR Module

**Purpose:** Expose AR scan data for M07 3D visualization and WebXR.

### Rust Exports

```rust
// crates/arxos-wasm/src/ar.rs

use wasm_bindgen::prelude::*;

/// Get AR scan metadata for a building
/// Returns: JSON array of ARScanSummary
#[wasm_bindgen]
pub fn get_ar_scans(building_path: &str) -> Result<String, JsValue>;

/// Get AR anchors from a specific scan
/// Returns: JSON array of ARAnchor
#[wasm_bindgen]
pub fn get_scan_anchors(scan_id: &str) -> Result<String, JsValue>;

/// Project equipment to AR overlay format
/// Returns: JSON AROverlay
#[wasm_bindgen]
pub fn project_equipment_to_ar(equipment_id: &str, scan_id: &str) -> Result<String, JsValue>;

/// Get pending equipment from AR workflow
/// Returns: JSON array of PendingEquipment
#[wasm_bindgen]
pub fn get_pending_equipment(building_path: &str) -> Result<String, JsValue>;
```

### TypeScript Interface

```typescript
// pwa/src/lib/wasm/ar.ts

export interface ARScanSummary {
  id: string;
  building_path: string;
  floor_id?: string;
  timestamp: string;
  anchor_count: number;
  status: "pending" | "processed" | "approved";
}

export interface ARAnchor {
  id: string;
  position: Coordinate;
  rotation?: { x: number; y: number; z: number; w: number }; // quaternion
  plane_id?: string;
  confidence: number; // 0-1
}

export interface AROverlay {
  equipment_id: string;
  anchor: ARAnchor;
  visualization: {
    type: "box" | "model";
    color?: string;
    size?: { width: number; height: number; depth: number };
    model_url?: string;
  };
  label: string;
}

export interface PendingEquipment {
  id: string;
  name: string;
  equipment_type: string;
  scan_id: string;
  anchor: ARAnchor;
  status: "pending" | "approved" | "rejected";
}

export async function getARScans(buildingPath: string): Promise<ARScanSummary[]>;
export async function getScanAnchors(scanId: string): Promise<ARAnchor[]>;
export async function projectEquipmentToAR(equipmentId: string, scanId: string): Promise<AROverlay>;
export async function getPendingEquipment(buildingPath: string): Promise<PendingEquipment[]>;
```

### Implementation Status

| Function | Status | Milestone | Notes |
|----------|--------|-----------|-------|
| `get_ar_scans` | ⬜ Not Started | M07 | Load from `.arxos/scans` |
| `get_scan_anchors` | ⬜ Not Started | M07 | Parse scan data |
| `project_equipment_to_ar` | ⬜ Not Started | M07 | Coordinate transform |
| `get_pending_equipment` | ⬜ Not Started | M07 | AR workflow integration |

---

## Export Module

**Purpose:** Generate export formats (glTF, USDZ) for M04 and M07.

### Rust Exports

```rust
// crates/arxos-wasm/src/export.rs

use wasm_bindgen::prelude::*;

/// Export floor to glTF binary
/// Returns: Uint8Array
#[wasm_bindgen]
pub fn export_floor_to_gltf(floor_id: &str) -> Result<Vec<u8>, JsValue>;

/// Export floor to USDZ binary (for iOS AR Quick Look)
/// Returns: Uint8Array
#[wasm_bindgen]
pub fn export_floor_to_usdz(floor_id: &str) -> Result<Vec<u8>, JsValue>;

/// Export building to JSON (ArxOS native format)
/// Returns: JSON string
#[wasm_bindgen]
pub fn export_building_to_json(building_path: &str) -> Result<String, JsValue>;

/// Generate CSV export for spreadsheet view
/// Returns: CSV string
#[wasm_bindgen]
pub fn export_equipment_to_csv(floor_id: &str) -> Result<String, JsValue>;
```

### TypeScript Interface

```typescript
// pwa/src/lib/wasm/export.ts

export async function exportFloorToGLTF(floorId: string): Promise<Uint8Array>;
export async function exportFloorToUSDZ(floorId: string): Promise<Uint8Array>;
export async function exportBuildingToJSON(buildingPath: string): Promise<string>;
export async function exportEquipmentToCSV(floorId: string): Promise<string>;

// Helper to trigger browser download
export function downloadFile(data: Uint8Array | string, filename: string, mimeType: string): void;
```

### Implementation Status

| Function | Status | Milestone | Notes |
|----------|--------|-----------|-------|
| `export_floor_to_gltf` | ⬜ Not Started | M04 | Leverage existing export code |
| `export_floor_to_usdz` | ⬜ Not Started | M07 | iOS AR Quick Look |
| `export_building_to_json` | ⬜ Not Started | M04 | Backup/sharing |
| `export_equipment_to_csv` | ⬜ Not Started | M04 | Spreadsheet import |

---

## Utility Module

**Purpose:** General-purpose utilities and configuration.

### Rust Exports

```rust
// crates/arxos-wasm/src/utils.rs

use wasm_bindgen::prelude::*;

/// Initialize WASM module (call once on load)
#[wasm_bindgen]
pub fn init_arxos_wasm() -> Result<(), JsValue>;

/// Get WASM module version
#[wasm_bindgen]
pub fn get_version() -> String;

/// Parse ArxAddress and return components
/// Returns: JSON ArxAddressParts
#[wasm_bindgen]
pub fn parse_arx_address(address: &str) -> Result<String, JsValue>;

/// Validate ArxAddress format
#[wasm_bindgen]
pub fn validate_arx_address(address: &str) -> bool;

/// Convert coordinates between systems (if needed)
/// Returns: JSON Coordinate
#[wasm_bindgen]
pub fn convert_coordinates(coord_json: &str, from_system: &str, to_system: &str) -> Result<String, JsValue>;
```

### TypeScript Interface

```typescript
// pwa/src/lib/wasm/utils.ts

export interface ArxAddressParts {
  country: string;
  state: string;
  city: string;
  building: string;
  floor?: string;
  room?: string;
  fixture?: string;
}

export async function initArxosWasm(): Promise<void>;
export function getVersion(): string;
export async function parseArxAddress(address: string): Promise<ArxAddressParts>;
export function validateArxAddress(address: string): boolean;
export async function convertCoordinates(
  coord: Coordinate,
  fromSystem: string,
  toSystem: string
): Promise<Coordinate>;
```

### Implementation Status

| Function | Status | Milestone | Notes |
|----------|--------|-----------|-------|
| `init_arxos_wasm` | ⬜ Not Started | M01 | Setup logging, etc. |
| `get_version` | ⬜ Not Started | M01 | From Cargo.toml |
| `parse_arx_address` | ⬜ Not Started | M02 | Utility for UI |
| `validate_arx_address` | ⬜ Not Started | M02 | Input validation |
| `convert_coordinates` | ⬜ Not Started | M03 | If multiple systems |

---

## TypeScript Type Definitions

**Location:** `pwa/src/lib/wasm/types.ts`

```typescript
// Re-export all types from individual modules for convenience
export * from './commands';
export * from './geometry';
export * from './validation';
export * from './ar';
export * from './export';
export * from './utils';

// Common error type
export interface WasmError {
  code: string;
  message: string;
  details?: any;
}

// Common result type wrapper
export type WasmResult<T> = {
  ok: true;
  value: T;
} | {
  ok: false;
  error: WasmError;
};
```

---

## Error Handling

### Rust Error Handling

All WASM exports should use `Result<T, JsValue>` for error handling:

```rust
use wasm_bindgen::prelude::*;
use serde_json;

#[wasm_bindgen]
pub fn example_function(input: &str) -> Result<String, JsValue> {
    // Parse input
    let data: SomeType = serde_json::from_str(input)
        .map_err(|e| JsValue::from_str(&format!("Invalid JSON: {}", e)))?;

    // Process
    let result = process(data)
        .map_err(|e| JsValue::from_str(&e.to_string()))?;

    // Serialize output
    serde_json::to_string(&result)
        .map_err(|e| JsValue::from_str(&format!("Serialization error: {}", e)))
}
```

### TypeScript Error Handling

All WASM wrapper functions should catch and transform errors:

```typescript
import { WasmError } from './types';

export async function exampleFunction(input: any): Promise<any> {
  try {
    const inputJson = JSON.stringify(input);
    const resultJson = await wasm.example_function(inputJson);
    return JSON.parse(resultJson);
  } catch (error) {
    const wasmError: WasmError = {
      code: 'WASM_ERROR',
      message: error instanceof Error ? error.message : String(error),
    };
    throw wasmError;
  }
}
```

---

## Implementation Status

### Overall Progress

| Module | M01 | M02 | M03 | M04 | M05 | M06 | M07 |
|--------|-----|-----|-----|-----|-----|-----|-----|
| Command | - | ⬜ | - | - | - | - | - |
| Geometry | - | - | ⬜ | ⬜ | - | - | - |
| Validation | - | - | - | ⬜ | - | - | - |
| AR | - | - | - | - | - | - | ⬜ |
| Export | - | - | - | ⬜ | - | - | ⬜ |
| Utility | ⬜ | ⬜ | - | - | - | - | - |

**Legend:**
- ⬜ Not Started
- 🟡 In Progress
- ✅ Complete
- `-` Not needed for this milestone

### Next Steps

1. **M01:** Implement `init_arxos_wasm()` and `get_version()`
2. **M02:** Implement Command module (catalog, local execution)
3. **M03:** Implement Geometry module (read-only data)
4. **M04:** Implement Validation module + extend Geometry for edits
5. **M07:** Implement AR and Export modules

---

## Performance Considerations

### WASM Bundle Size

- **Target:** <2MB compressed
- **Strategies:**
  - Use feature flags to exclude unused modules
  - Strip debug symbols in release builds
  - Use `wasm-opt` with `-Oz` flag
  - Lazy-load modules where possible

### Data Transfer

- **Minimize transfers:** Don't load all buildings at once
- **Pagination:** Return max 100 items per query
- **Caching:** Cache geometry on TypeScript side
- **Compression:** Use GZIP for large JSON payloads (if browser supports)

### Serialization Overhead

- **Measure:** Profile serde_json serialization times
- **Optimize:** Use `#[serde(skip_serializing_if = "Option::is_none")]` to reduce payload
- **Alternative:** Consider MessagePack for binary formats (glTF, USDZ)

---

## Testing Strategy

### Rust WASM Tests

```rust
#[cfg(test)]
mod tests {
    use super::*;
    use wasm_bindgen_test::*;

    #[wasm_bindgen_test]
    fn test_get_command_catalog() {
        let result = get_command_catalog().unwrap();
        let catalog: Vec<CommandMetadata> = serde_json::from_str(&result).unwrap();
        assert!(catalog.len() > 0);
    }
}
```

Run with: `wasm-pack test --headless --chrome`

### TypeScript Integration Tests

```typescript
import { getCommandCatalog } from '@/lib/wasm/commands';

describe('WASM Commands', () => {
  it('should load command catalog', async () => {
    const catalog = await getCommandCatalog();
    expect(catalog).toBeDefined();
    expect(catalog.length).toBeGreaterThan(0);
  });
});
```

---

## Changelog

### Version 2.0 (2025-11-12)
- Initial WASM API design document
- Defined all module interfaces (Commands, Geometry, Validation, AR, Export, Utility)
- Mapped functions to milestones
- Added TypeScript type definitions
- Documented error handling patterns

---

## References

- [wasm-bindgen Guide](https://rustwasm.github.io/wasm-bindgen/)
- [serde JSON Documentation](https://docs.serde.rs/serde_json/)
- [WebAssembly Binary Format](https://webassembly.github.io/spec/core/binary/)
- [ArxOS Core Documentation](../core/ARCHITECTURE.md)
