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
| `tests/fixtures/ifc/buildingsmart/*.ifc` | buildingSMART ISO RV | Yes | Non-panic + `unmapped_products` honesty |
| Revit / ArchiCAD anonymized | **Not checked in** | Open (**R2**) | Provide under `tests/fixtures/ifc/vendor/` |

“No panic” ≠ semantic completeness. District pilots must log preserve/drop in
[field-truth-log.md](./field-truth-log.md).

## buildingSMART Sample-Test-Files (2026-07 assessment)

**Source:** https://github.com/buildingSMART/Sample-Test-Files  
**Report:** [`tests/ifc_buildingsmart_report.md`](../tests/ifc_buildingsmart_report.md)

| Sample class | Import crash? | Domain extract | GID round-trip (kept entities) |
| :--- | :---: | :--- | :---: |
| ISO RV micro (tessellation) | No | Often empty floors + warnings | Weak (few entities) |
| ISO wall+opening+window | No | Storey only; wall/window not domain | Yes for kept IDs |
| PCERT Building-Architecture IFC4/4.3 | No | Storey + spaces (+ sparse products) | Yes |
| PCERT Building-Hvac IFC4/4.3 | No | Storey + few terminals | Yes |
| PCERT Building-Structural | No | Storey shell only | Yes |
| PCERT Infra-Bridge | No | Multiple levels; no rooms | Yes |

**Takeaway:** Non-panic and GlobalId stability on **mapped** entities are strong.  
Walls/slabs/doors/windows are typically **not** first-class Arx entities; import now emits  
`unmapped_products` LossReport warnings with class counts (do not treat “validate OK” as full BIM).  
**District readiness** still needs real Revit (or similar) exports in the field-truth log (**R2**).

## What is mapped today (domain)

| IFC concept | Arx domain | Notes |
| :--- | :--- | :--- |
| Project / Site / Building / Storey | Building + Floor | Spatial structure |
| Space / Room / Zone | Room | When present |
| Selected MEP / furniture classes | Equipment | See `resolve_equipment_under` |
| Wall / slab / door / window / column / beam / roof / … | **Not mapped** | Counted in LossReport `unmapped_products` |

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
