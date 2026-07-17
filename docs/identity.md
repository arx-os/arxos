# Identity model: Arx UUID · IFC GlobalId · ArxAddress

**Code:** `src/core/`, `src/ifc/mapping/identity.rs`, `src/export/ifc.rs`, `src/core/domain/address.rs`  
**Manifest:** §3.2 Identity

ArxOS keeps **three complementary identities**. Do not collapse them.

## Summary

| Layer | Storage | Format | Role |
| :--- | :--- | :--- | :--- |
| **Arx UUID** | entity `id` (always) | UUID string | Merge key inside Arx; YAML primary key; registry `buildingId` |
| **IFC GlobalId** | `ifc_global_id` (optional) | 22-char IFC compressed GUID | Stable product id in STEP interchange |
| **ArxAddress** | equipment `address` (optional, durable when set) | `/country/state/city/building/floor/room/fixture` | Human/ops query path; file-tree style navigation |

**Never** treat STEP express ids (`#42`) as durable identity.

## How they work together

```text
                    ┌─────────────────┐
   YAML SSOT        │  Arx UUID (id)  │  ← always present
                    └────────┬────────┘
                             │ export: prefer stored ifc_global_id
                             │ else derive GlobalId from UUID (deterministic)
                             ▼
                    ┌─────────────────┐
   IFC STEP         │  GlobalId (22)  │  + Pset_ArxIdentity.ArxId
                    └────────┬────────┘
                             │ import: GlobalId → ifc_global_id
                             │         Pset ArxId → restore Arx id when present
                             ▼
                    ┌─────────────────┐
   Ops / query      │  ArxAddress     │  ← equipment only; backfill via `arx migrate`
                    └─────────────────┘
```

### Suitability for engineering / file-tree navigation

| Use case | Prefer |
| :--- | :--- |
| Merge, Git, contribution package, building registry | **Arx UUID** |
| Round-trip with Revit/ArchiCAD/other IFC tools | **IFC GlobalId** |
| Ops query, crew language, hierarchical paths | **ArxAddress** |

ArxAddress is intentionally **path-like** (filesystem / URL mental model) with
14 reserved system room segments (`hvac`, `electrical`, …). It is **not** a
substitute for UUID or GlobalId.

- **Lenient Naming Rules:** Syntax structure is validated strictly (lowercase, valid characters, leading slash, segment count). However, system prefix mismatches (e.g. placing a non-prefixed fixture under a reserved system category like `hvac`) trigger warnings by default rather than hard validation errors, allowing initial saves. Pass the `--strict-addresses` CLI flag during QA to enforce strict prefix rules.


`ArxAddress::guid()` (SHA-256 of path) is a **helper for stable fixture-derived
tokens only**. It is **not** the product GlobalId used by the IFC exporter
(`resolve_product_global_id` / `ifc_global_id_from_uuid`).

## Sync rules (must not regress)

### Import (`apply_identity_on_import`)

1. IFC product GlobalId (when present) → entity `ifc_global_id`.
2. If property set `Pset_ArxIdentity` contains `ArxId` → **overwrite** entity `id` with that Arx UUID.
3. Missing ArxId → keep newly generated Arx UUID; still store GlobalId if present.
4. STEP `#expressId` is never stored as durable id.

### Export (`resolve_product_global_id` + `assign_missing_global_ids`)

1. Prefer existing `ifc_global_id` if non-empty.
2. Else if Arx `id` parses as UUID → **deterministic** 22-char GlobalId via `ifc_global_id_from_uuid`.
3. Else mint new UUID-based GlobalId (should be rare after assign pass).
4. Write `Pset_ArxIdentity` with `ArxId` = Arx UUID and entity kind.
5. Assign missing GlobalIds before export so subsequent exports stay stable when YAML is re-saved.

### Round-trip contract (L0 identity)

**Arx-authored path:**

```text
Building (UUID) → export IFC → import IFC → same Arx UUID (via Pset) + same GlobalId
```

**Vendor IFC without Arx Psets:**

```text
import → new Arx UUIDs + store vendor GlobalIds → export → preserve GlobalIds
```

Double export without model change must not churn GlobalIds once `ifc_global_id` is populated.

## CLI / pilot guidance

```bash
arx migrate              # backfill missing ArxAddress on equipment
arx query "/…/*/*/boiler-*"
arx export --format ifc  # identity via export::ifc only
```

## Tests that guard this

| Test area | What it proves |
| :--- | :--- |
| `src/ifc/mapping/identity.rs` unit tests | 22-char length, deterministic UUID→GlobalId, prefer stored, restore ArxId |
| `tests/bidirectional_tests.rs` / `ifc_compiler_path_test` | Identity/enrichment on compiler path |
| `tests/compiler_spine_test.rs` | Persist + query address after migrate |
| Double-export GlobalId stability | Integration coverage in bidirectional / export path |

## Non-goals

- Byte-identical STEP
- Using ArxAddress as IFC GlobalId
- CAD plugin sync of identities (no plugins — see [ifc-limitations.md](./ifc-limitations.md))
