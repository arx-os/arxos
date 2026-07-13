# IFC interop limitations table (Track B3)

Authoritative for what ArxOS claims to preserve. Update when adding fixtures.

## Checked-in fixtures

| Fixture | Source / toolchain | Schema | In CI | Preserve (typical) | Drop / weak |
| :--- | :--- | :---: | :---: | :--- | :--- |
| `test_data/sample_building.ifc` | ArxOS test suite | IFC2X3 | Yes | Hierarchy, names, L0–L2 box path when present | Full CAD materials/openings |
| `tests/fixtures/ifc/simple.ifc` | ArxOS minimal | IFC2X3 | Yes | Smoke parse | Geometry-rich models |
| `test_data/Building-Architecture.ifc` | SketchUp + IFC-manager 5.3 | IFC4 | Yes (non-panic + optional persist) | Spatial structure if mapped; no crash | Vendor quirks, materials, openings, systems |
| `test_data/Building-Hvac.ifc` | Project HVAC sample | IFC4-ish | Yes (non-panic + optional persist) | Equipment-ish entities when mapped | Full MEP systems, types not in Arx enum |
| Revit / ArchiCAD anonymized | **Not yet checked in** | — | Pending real licenses | — | Provide under `tests/fixtures/ifc/vendor/` |

## Fidelity contract (reminder)

| Tier | Content | Status |
| :--- | :--- | :--- |
| L0 | Hierarchy, names, types, product GlobalIds | Strong on Arx-shaped data |
| L1 | `Pset_ArxIdentity`, `Pset_ArxLidarEnrichment`, clean free-form keys | Strong on Arx round-trip |
| L2 | Position / dims / mesh subset | Box + placement; mesh partial |
| L3+ | Materials, openings, full systems | **Out of pilot scope** |

## Policy

1. **Native STEP only** — do not revive `ifc_rs` for one more vendor file.
2. A fixture is “supported” only if a **named test** exercises it (`tests/vendor_ifc_test.rs`, spine tests).
3. “No panic” is the minimum bar for third-party files; semantic round-trip is required only when validation is clean.
4. Real Revit/ArchiCAD files: anonymize, license notes in `tests/fixtures/ifc/vendor/README.md`, then add rows here.

## Adding a vendor fixture

```text
tests/fixtures/ifc/vendor/
  README.md          # license + origin
  revit_anon_01.ifc  # stripped personal data
```

Then extend `tests/vendor_ifc_test.rs` with a non-panic (+ structure) case and list the file in this table.
