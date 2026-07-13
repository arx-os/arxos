# IFC limitations & policy

**Policy (hard):** ArxOS is an **IFC compiler / interchange** tool only.  
There are **no Revit, ArchiCAD, or other CAD plugins** and none planned for L1.

**Supported BIM path for districts:**

```text
Vendor BIM (Revit / ArchiCAD / …)
        → clean IFC export from that tool
        → arx import ifc
        → review / edit / validate
        → arx export --format ifc
        → re-import to vendor tools if needed
```

If the vendor IFC is incomplete, fix **export settings in the BIM tool** — not by
embedding Arx inside CAD.

**Export spine:** Only `arx export --format ifc` (or the same
`export::ifc::IFCExporter` path). Agent/daemon may bridge files over the network;
it must **not** invent alternate IFC semantics. Official pilot handoffs use the CLI.

Identity rules: [identity.md](./identity.md).

## Fidelity tiers

| Tier | Content | Status |
| :--- | :--- | :---: |
| L0 | Hierarchy, names, types, product GlobalIds | Strong on Arx-shaped data |
| L1 | `Pset_ArxIdentity`, `Pset_ArxLidarEnrichment`, clean free-form keys | Strong on Arx round-trip |
| L2 | Position / dims / mesh subset | Box + placement; mesh partial |
| L3+ | Materials, openings, full MEP systems, type catalogs | **Out of pilot scope** |

## Checked-in fixtures

| Fixture | Source | In CI | Notes |
| :--- | :--- | :---: | :--- |
| `test_data/sample_building.ifc` | ArxOS | Yes | Hierarchy / L0–L2 path |
| `tests/fixtures/ifc/simple.ifc` | Minimal | Yes | Smoke |
| `test_data/Building-Architecture.ifc` | SketchUp | Yes | Non-panic + optional persist |
| `test_data/Building-Hvac.ifc` | HVAC sample | Yes | Equipment-ish mapping partial |
| Revit / ArchiCAD anonymized | **Not checked in** | Open (**R2**) | Provide under `tests/fixtures/ifc/vendor/` with license note |

“No panic” ≠ semantic completeness. District pilots must log preserve/drop in
[field-truth-log.md](./field-truth-log.md).

## Merge policy (import)

| Source | Policy | Meaning |
| :--- | :--- | :--- |
| IFC re-import | `MergePolicy::ifc()` | Hierarchy base = **incoming** (entities missing from file may drop) |
| LiDAR re-scan | `MergePolicy::lidar()` | Hierarchy base = **existing** + spatial match |

## Explicit non-support

- Direct RVT / PLN open
- Live CAD plugin bidirectional sync
- Full CoordinationView / reference-view certification
- Survey-grade geometry from IFC alone
- Agent/daemon as official pilot export authority

**Manifest:** §3.5, obligation **R2**.
