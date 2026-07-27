# Phase 4 — Interop (USD + IFC)

**Status:** Implemented (2026-07-27)

## Goals

* OpenUSD exporter (priority) — USDA projection
* IFC bidirectional translator (identity-preserving)
* Round-trip tests
* CLI and edge node export commands

## Design principles

1. **Object graph is canonical.** USD and IFC are **projections**, not sources of truth.
2. **Narrow but correct subset.** Expand coverage deliberately (architecture risk mitigation).
3. **Identity preservation.**  
   - USD: `arxos:cid`, `arxos:buildingId`, layer metadata  
   - IFC: `Pset_ArxosIdentity` + deterministic GlobalId from CID  
4. **No rendering.** Geometry is data for export/import only.
5. **USDA first.** Human-readable OpenUSD ASCII avoids C++ OpenUSD dependency in Phase 4; binary USDC/crate can wrap later.

## Crates

| Crate | Path | Role |
|-------|------|------|
| `arxos-usd` | `gateways/usd` | USDA export/import |
| `arxos-ifc` | `gateways/ifc` | IFC4 STEP export/import |

## CLI

```bash
arxos export usd $BID -o out.usda
arxos export ifc $BID -o out.ifc [--project-name Name]
arxos import usd out.usda
arxos import ifc out.ifc
```

## Edge

```bash
arxos-edge export-usd $BID -o out.usda
arxos-edge export-ifc $BID -o out.ifc
arxos-edge buildings
```

## Tests

* `arxos-usd` / `arxos-ifc` round-trip identity tests
* GlobalId stability unit test

## Out of scope (later)

* Full OpenUSD C++/Rust bindings and USDC
* Complete IFC4 schema (MEP systems, detailed BREP)
* Native CAD plugins (Revit, etc.)
