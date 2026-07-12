# IFC ↔ Core Data Model Mapping

ArxOS treats the in-memory **`Building` graph as the single source of truth**.
IFC is a projection of that graph (and an ingestion source for third-party BIM files).
YAML is the durable, Git-native serialization of the same graph.

## Fidelity tiers

| Tier | Must survive | Status |
|------|----------------|--------|
| **L0 — Identity & structure** | Hierarchy, names, types, stable product IDs | Phase 1 done |
| **L1 — Arx semantics** | Typed enrichments (`lidar_enrichment`), Arx property sets | Phase 2 done |
| **L1b — Property bags** | Clean free-form keys; no double-prefix on re-export | Phase 3 done |
| **L2 — Geometry** | Position, dimensions, mesh (supported subset) | Phase 4 done |
| **Ops** | Unified merge + loss reports on import/export | Phase 5 done |

Round-trips are **not** required to be byte-identical IFC. Success means L0/L1
domain state is preserved for Arx-authored data.

## Identity model

| ID | Role |
|----|------|
| **`id` (Arx UUID string)** | Canonical entity id in YAML / Git / merge |
| **`ifc_global_id` (optional)** | IFC product `GlobalId` (22-char compressed GUID) |

### Rules

1. **Import:** Read product `GlobalId` (attribute 0) → `ifc_global_id`.
   If `Pset_ArxIdentity.ArxId` is present, use it as Arx `id`.
2. **Export:** Prefer stored `ifc_global_id`. If missing, assign a GlobalId
   derived deterministically from the Arx UUID and write it back on the model
   so subsequent exports stay stable.
3. **Never** use STEP express ids (`#42`) as durable identity.
4. Relationship entities (aggregates, containment, pset links) may use fresh GUIDs.

### Property set: `Pset_ArxIdentity`

| Property | Meaning |
|----------|---------|
| `ArxId` | Arx UUID (`Room.id`, `Equipment.id`, …) |
| `EntityKind` | `Building` \| `Floor` \| `Room` \| `Equipment` |

### Property set: `Pset_ArxLidarEnrichment` (L1)

Typed `LidarEnrichment` on rooms and equipment maps to this Pset. It is **not**
dumped into free-form `properties` after import.

| Property | Domain field | Notes |
|----------|--------------|--------|
| `PointCount` | `point_count` | Integer as string |
| `ConfidenceScore` | `confidence_score` | Float as string |
| `LastScanTimestamp` | `last_scan_timestamp` | RFC3339 when present |
| `ClassificationHeuristic` | `classification_heuristic` | Optional string |

**Import:** when any of these keys appear (as `Pset_ArxLidarEnrichment:…`),
populate `lidar_enrichment` and remove them from the properties bag.

**Export:** write the Pset only when `lidar_enrichment` is `Some`.

**Re-import merge:** if the incoming IFC has no LiDAR Pset, keep existing
enrichment on the YAML-backed model (`prefer_existing_lidar`).

### Free-form property normalization (Phase 3)

The native IFC resolver materializes every Pset as `PsetName:PropertyName`.
Domain bags (and YAML) should store **clean** keys for Arx free-form Psets.

| On import | On export |
|-----------|-----------|
| Strip `Pset_ArxRoomProperties:`, `Pset_ArxEquipmentProperties:`, `Pset_ArxFloorProperties:`, `Pset_ArxBuildingMetadata:` | Write clean names into those Psets via `properties_for_export` |
| Drop leftovers from `Pset_ArxIdentity` / `Pset_ArxLidarEnrichment` | Identity & LiDAR use dedicated Psets only |
| Collapse stacked prefixes from older re-exports | Never re-emit identity/LiDAR keys from the free-form bag |
| Keep third-party `Pset_*:…` keys prefixed | Third-party keys stay as-is until a future foreign-Pset policy |

Helpers: `normalize_imported_properties`, `properties_for_export`,
`wing_name_from_properties` in `src/ifc/mapping/properties.rs`.

### Geometry / placement (Phase 4 / L2)

| Rule | Detail |
|------|--------|
| Coordinate system | `building_local`, meters |
| Product placement | Absolute (no parent placement chain on Arx export) |
| Room position | Footprint center X/Y; volume bottom Z (`SpatialProperties::new`) |
| Room body | Mesh in local frame, **or** extruded rectangle (width×depth×height) |
| Equipment body | Optional mesh in local frame; **no** synthetic 1×1×1 box |
| Floor elevation | `Floor.elevation` → `IfcBuildingStorey` elevation; room Z remains absolute |
| Comparison epsilon | `GEOMETRY_EPSILON` (1e-3 m) for tests / merge helpers |

Import order for rooms:

1. Read placement origin → position  
2. If extruded rectangle → set dimensions, leave `mesh = None`  
3. Else if tessellated body → local mesh + AABB dimensions  

Helpers: `src/ifc/mapping/geometry.rs`.

## Product entity mapping (structure)

| Domain | IFC class |
|--------|-----------|
| Building | `IfcBuilding` |
| Floor | `IfcBuildingStorey` |
| Wing | `IfcZone` + group assignment |
| Room | `IfcSpace` |
| Equipment | Type table (`IfcFurniture`, `IfcFlowTerminal`, …) |

### Unified merge & loss reports (Phase 5+)

**`merge_building` / `merge_building_with_policy`** — shared ingest merge (`MergePolicy::ifc()`
vs `MergePolicy::lidar()`). Used by CLI, agent, LiDAR `ModelMerger`, and `ingest::*`.

Match order for rooms / equipment: `ifc_global_id` → Arx `id` → name path →
optional spatial radius (LiDAR).

| Field | On match |
|-------|----------|
| Geometry | Incoming (IFC) |
| `lidar_enrichment` | Prefer existing when incoming is `None` |
| `status` / sensors | Existing |
| Properties | Incoming wins on collision; fill gaps from existing |
| Arx `id` / `created_at` | Existing |

Existing entities absent from the incoming IFC are **not** appended; they are counted in
`MergeStats.existing_*_not_in_incoming` and warned.

**`LossReport`** — fidelity level, warnings, optional merge stats. Printed by CLI import/export;
attached to agent import as `report_summary`. Native parse fills warnings (no storey, equipment
fallback floor, etc.).

## Non-goals (current)

- Full IFC schema coverage
- Materials / openings / MEP connectivity
- Delta / incremental IFC export
- Advanced merge conflict UI (interactive resolve)
- Promoting arbitrary third-party Psets into typed domain fields
- Full CSG / boolean geometry fidelity
- Relative storey placement chains (rooms stay absolute in building_local)
- Automatically retaining IFC-orphaned rooms/equipment without an explicit policy flag

## Implementation

Constants and helpers live in `src/ifc/mapping/` (`identity`, `lidar`, `properties`, `geometry`,
`merge`, `report`).
Export: `src/export/ifc.rs`. Import: `src/ifc/parser/resolver.rs` (native path).

Shared multi-source orchestration: `src/ingest/` (`import`, `text`, `sync`).

### Text / AR edits

DSL applied via `ingest::apply_text_script` then `finalize_ingest(IngestSource::Text)`.

```bash
arx edit script.txt --building building.yaml
# or
arx import text script.txt
```

### PWA sync envelope

`BuildingSyncEnvelope` JSON (`schema_version`, `source`, `updated_at`, `building`, `report`).
WASM: `parse_ifc_data_with_report`, `store_active_building`, `load_active_building`,
`merge_building_sync_json`, `apply_text_script_json`.
