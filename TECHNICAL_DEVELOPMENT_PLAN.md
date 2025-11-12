# Technical Engineering Development Plan

## Overview

ArxOS now solidly normalizes building names and canonical slugs during IFC import, unblocking ArxAddress lookups and stabilizing YAML export paths. However, the broader IFC processing pipeline still relies on placeholder geometry and heuristic hierarchy mapping, limiting the usefulness of spatial queries, renderers, AR exports, and downstream services. This plan prioritizes the remaining work required to transform the current prototype-grade pipeline into production-ready infrastructure.

## Current Status

- **Resolved recently**
  - Shared string utilities (`normalize_label`, `slugify`) added and covered by unit tests.
  - Fallback and hierarchy parsers derive `Building::name` and `Building::path` from canonical identifiers.
  - Import CLI writes YAML using the canonical slug instead of IFC GUIDs.
- **Still outstanding**
  - Geometry (coordinates, dimensions, bounding boxes) is fabricated via hash-based fallbacks.
  - Room/floor/equipment relationships are inferred via string prefixes instead of IFC references.
  - Integration tests only assert that parsing runs; they do not validate resulting geometry or hierarchy.
  - AR / 3D / spatial features inherit the synthetic data and cannot reflect real-world structures.

## Objectives

1. Parse real IFC placement data to generate accurate coordinates, bounding boxes, and spatial relationships.
2. Produce deterministic floor/room/equipment hierarchies using IFC relational graph traversal rather than heuristics.
3. Establish regression safeguards (fixtures + assertions) for the entire import pipeline.
4. Validate downstream consumers (renderers, exports, services) against the corrected data model.

## Workstreams & Deliverables

### 1. Accurate IFC Geometry Extraction
- Implement placement chain traversal:
  - Resolve `IfcLocalPlacement` → `IfcAxis2Placement3D` → `IfcCartesianPoint`.
  - Handle nested placements (relative vs absolute).
  - Support orientation via axis vectors (rotation matrices).
- Populate `Room.spatial_properties.bounding_box` and equipment bounding boxes from actual geometry (`IfcProductDefinitionShape`, `IfcShapeRepresentation`, `IfcExtrudedAreaSolid`).
- Replace `generate_fallback_coordinates` and other deterministic hashes with real data; emit explicit warnings or errors when geometry is missing.

### 2. Deterministic Hierarchy Mapping
- Use IFC relationship entities (`IfcRelContainedInSpatialStructure`, `IfcRelAggregates`, `IfcRelAssignsToGroup`) to map:
  - Building → floor → room relationships.
  - Equipment to containing rooms/floors (`room_id` should be set consistently).
- Populate `Floor` metadata (elevation, absolute coordinates) from IFC attributes instead of defaults.
- Validate that each imported entity has a unique, canonical path conforming to ArxAddress semantics.

### 3. Robust Regression Test Suite
- Introduce fixture IFC files (small, well-understood) with golden YAML/JSON outputs for diff-based verification.
- Extend `tests/ifc/` to assert:
  - Building/floor/room/equipment counts.
  - Precise coordinates and bounding boxes.
  - Presence of `room_id` on equipment and proper floor assignments.
  - Stable slug and path generation (existing unit tests already cover helper functions).
- Add property tests or fuzzers for slug/label utilities if additional edge cases emerge.

### 4. Downstream Feature Validation
- Re-test:
  - `render3d` visualizations (validate projections against expected coordinates).
  - GLTF/USDZ exporters (ensure geometry and transformations align with the new data).
  - Spatial queries (`within_radius`, `nearest`) using known fixture coordinates.
  - Hardware ingestion pathways (equipment lookups should succeed with new identifiers).
- Update documentation (CLI reference, architecture docs) to reflect the new canonical slugging behaviour and improved spatial fidelity.

## Testing Strategy

- **Unit tests:** Continue covering string utilities and new geometry parsing helpers.
- **Integration tests:** Run end-to-end imports on fixture IFCs, compare outputs, and execute verification commands (`arx list`, `arx spatial_query`, export commands).
- **Manual verification:** Visual inspection using `render3d` and PWA once geometry is trustworthy.
- **Continuous Integration:** Incorporate fixture-based diff checks into CI to catch regressions automatically.

## Risks & Mitigations

| Risk | Impact | Mitigation |
| --- | --- | --- |
| IFC variation across vendors | High | Develop fixture library covering common variants; add robust error handling with clear diagnostics. |
| Performance regression from deeper parsing | Medium | Profile geometry extraction; consider caching or lazy evaluation when parsing large models. |
| Breaking downstream assumptions | Medium | Coordinate with teams owning renderers/exports to verify expectations during rollout. |

## Delivery Milestones (Indicative)

1. **Week 1–2:** Implement placement traversal and accurate geometry extraction; add targeted unit tests.
2. **Week 3:** Replace hierarchy heuristics with IFC relationship mapping; populate metadata.
3. **Week 4:** Build fixture-based regression suite; integrate into CI; fix regressions uncovered by tests.
4. **Week 5:** Validate downstream consumers; update documentation; plan rollout checklist.

## Definition of Done

- Importing any supported IFC produces:
  - Human-readable names and canonical slugs (already achieved).
  - Real-world coordinates, bounding boxes, and equipment/room relationships traced from IFC.
- All regression tests (unit + integration) pass in CI.
- Renderers, exporters, and spatial services demonstrate correct behaviour against fixture data.
- Documentation reflects the new behaviour and includes guidance for verifying imports.


