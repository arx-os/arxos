# Identity & Addressing Architecture

**Status:** Canonical design reference  
**Binding decisions:** [`adr-0001-identity-and-addressing.md`](./adr-0001-identity-and-addressing.md) (Accepted 2026-07-25)  
**Applies to:** Arxos domain model, IFC ingestion, CLI, validation, export, and proofs  
**Last updated:** 2026-07-25  
**Code map:** [`identity.md`](./identity.md)

This document defines how every entity in an Arxos model receives identity, how hierarchical addresses are formed, how IFC provenance is preserved, and how the `arx` CLI language is built on top of that identity system.

**Implementation status (2026-07 — main):**

| Capability | Status |
| :--- | :---: |
| Hierarchical `address` on Building / Floor / Room / Equipment | **Landed** |
| Dots in segments; postal + lab building roots | **Landed** |
| CLI `show` / `ls` / `tree` / `add` | **Landed** |
| Electrical tree (`/elec/...`) + honest IFC assignment | **Landed** |
| Export: preserve IFC GlobalIds; assign + write-back for Arxos-native | **Landed** |
| YAML field name still `address` (not `arx_address`) | Intentional (rename deferred) |
| Other system trees (hvac, plumb, fire, …) | **Not started** |
| `arx link` / relationship graph | **Not started** |
| Scoped `validate <address>` | **Not started** |

---

## 1. Design Goals

1. **Human-first operational identity** — Field technicians, facility managers, and the CLI must be able to name and navigate every significant object using a stable, hierarchical path that mirrors how the physical systems are actually built and maintained.
2. **Faithful provenance** — Original IFC `GlobalId` values are never discarded. They remain available for audit, round-trip, and proof-of-origin.
3. **Determinism** — The same source data + the same rules must produce the same addresses on every import.
4. **Honesty over completeness** — Prefer an explicit entry in the LossReport over inventing hierarchy or identity that the source data does not support.
5. **Separation of concerns** — Provenance identity and operational identity are distinct layers and must never be collapsed.

---

## 2. The Three Identity Layers

Every domain entity carries up to three identifiers:

| Layer            | Field             | Purpose                                                                 | Primary consumer          | Human readable |
|------------------|-------------------|-------------------------------------------------------------------------|---------------------------|----------------|
| Provenance       | `ifc_global_id`   | Original 22-character IFC GlobalId from the authoring tool             | Audit, export, round-trip | No             |
| Operational      | `arx_address`     | Hierarchical path that is the canonical identity inside Arxos          | Humans, CLI, Git, proofs  | Yes            |
| Implementation   | `internal_id`     | Optional machine UUID/ULID used only for internal linking if required  | Runtime only              | No             |

### Rules

- `arx_address` is the primary key for all human and CLI interaction.
- `ifc_global_id` is mandatory for any entity that originated from an IFC product. It is never used as the primary key.
- `internal_id` is an implementation detail and must remain invisible to users and the CLI.
- An entity may exist without an `ifc_global_id` (purely Arxos-native entities). It may never exist without an `arx_address`.

---

## 3. ArxAddress Syntax

An ArxAddress is a slash-separated hierarchical path.

```
segment/segment/segment/...
```

### 3.1 Segment Rules

- Lowercase.
- Use kebab-case or short mnemonic codes (`panel.L1`, `ckt.14`, `rm.215`).
- **Dots (`.`) are legal** inside segments (ADR 0001 §3).
- No spaces; prefer hyphens over underscores in new addresses (legacy underscores may be normalized on read).
- Segments are ordered from most general (left) to most specific (right).
- The building root is a **fully qualified multi-part** root (ADR 0001 §4), not a short `bldg.1` token alone:

```text
bldg.<country>.<region>.<city>.<street>-<number>.<unit>
# example:
bldg.us.fl.tampa.dale-mabry.143677.s2
```

### 3.2 Stability Rules

- Address assignment must be deterministic.
- Re-importing the same IFC file with the same rules must produce identical addresses for the same logical entities.
- Matching on re-import prefers `ifc_global_id` first, then stable spatial/system keys.
- Changing an address is a deliberate, reviewable model change and will appear in Git history.

---

## 4. Core Spatial Hierarchy

Every building model begins with the spatial tree. This hierarchy is mandatory and is derived from IfcBuilding → IfcBuildingStorey → IfcSpace (and equivalent).

Let `ROOT` stand for the fully qualified building root (ADR 0001 §4), e.g. `bldg.us.fl.tampa.dale-mabry.143677.s2`.

```
ROOT
ROOT/fl.<n>
ROOT/fl.<n>/rm.<id>
ROOT/fl.<n>/rm.<id>/<element>
```

Examples:

```
bldg.us.fl.tampa.dale-mabry.143677.s2
bldg.us.fl.tampa.dale-mabry.143677.s2/fl.2
bldg.us.fl.tampa.dale-mabry.143677.s2/fl.2/rm.215
bldg.us.fl.tampa.dale-mabry.143677.s2/fl.2/rm.215/door.north
bldg.us.fl.tampa.dale-mabry.143677.s2/fl.2/rm.215/win.east.1
```

For lab fixtures without a real postal address, a deterministic lab root may be used temporarily (e.g. `bldg.lab.local.sample.duplex.1`) and later rewritten via migrate/edit — it must still use the `bldg.…` multi-segment form, not geo `/country/state/city` paths.

Floor numbers and room identifiers should be taken from the source data when present and stable; otherwise a deterministic sequential or coordinate-derived scheme is used and recorded.

---

## 5. System Hierarchies

Spatial hierarchy alone is insufficient for real facility work. Arxos therefore supports parallel system trees that mirror how each trade actually installs, maintains, and troubleshoots the building.

An entity may appear in the spatial tree, in one or more system trees, or in both. Cross-links are expressed with explicit relationships; the address itself remains a single canonical path (usually the most specific system or spatial path that best identifies the object for field use).

### 5.1 Electrical

**Status (implementation):** First system tree landed. Root segment `elec`; import assigns `/elec/...` for clear electrical IFC classes (outlets, lights, switches, panels) when properties supply panel/circuit IDs, otherwise a shallow `…/elec/<leaf>.<slug>` path. Intermediate nodes (`…/elec`, `…/elec/panel.l1`) are virtual for `show`/`ls`/`tree`. Other system trees remain design-only.

The electrical hierarchy is the reference design for all other systems. It follows the real power distribution path.

```
ROOT/elec
ROOT/elec/xfmr.<id>                    # Utility or site transformer
ROOT/elec/xfmr.<id>/mdp                 # Main distribution panel / switchgear
ROOT/elec/xfmr.<id>/mdp/panel.<id>      # Distribution or branch panel
ROOT/elec/xfmr.<id>/mdp/panel.<id>/ckt.<n>
ROOT/elec/xfmr.<id>/mdp/panel.<id>/ckt.<n>/jbox.<id>
ROOT/elec/xfmr.<id>/mdp/panel.<id>/ckt.<n>/jbox.<id>/rec.<id>   # Receptacle
ROOT/elec/xfmr.<id>/mdp/panel.<id>/ckt.<n>/jbox.<id>/ltg.<id>   # Lighting outlet
ROOT/elec/xfmr.<id>/mdp/panel.<id>/ckt.<n>/jbox.<id>/sw.<id>    # Switch
```

Shorter **relative** forms are legal in CLI UX when a building context is already selected; durable SSOT paths use the full `ROOT`.

```
# with building context already set:
elec/panel.L1/ckt.14/rec.7
```

Full durable example:

```
bldg.us.fl.tampa.dale-mabry.143677.s2/elec/xfmr.1/mdp/panel.L1/ckt.14/jbox.3/rec.7
```

### 5.2 HVAC

```
bldg.<id>/hvac
bldg.<id>/hvac/ahu.<id>                      # Air handling unit
bldg.<id>/hvac/ahu.<id>/vav.<id>             # Variable air volume box
bldg.<id>/hvac/ahu.<id>/vav.<id>/diff.<id>   # Diffuser / grille
bldg.<id>/hvac/ahu.<id>/coil.<id>
bldg.<id>/hvac/ahu.<id>/fan.<id>
bldg.<id>/hvac/chiller.<id>
bldg.<id>/hvac/boiler.<id>
bldg.<id>/hvac/pump.<id>
bldg.<id>/hvac/exhaust.<id>
```

### 5.3 Plumbing

```
bldg.<id>/plumb
bldg.<id>/plumb/main
bldg.<id>/plumb/main/ris.<id>
bldg.<id>/plumb/main/ris.<id>/branch.<id>
bldg.<id>/plumb/main/ris.<id>/branch.<id>/fix.<type>.<id>
bldg.<id>/plumb/water-heater.<id>
bldg.<id>/plumb/backflow.<id>
bldg.<id>/plumb/sump.<id>
```

Fixture types use short codes: `sink`, `wc`, `urinal`, `shower`, `floor-drain`, `hose-bib`, etc.

### 5.4 Fire Protection

```
bldg.<id>/fire
bldg.<id>/fire/riser.<id>
bldg.<id>/fire/riser.<id>/branch.<id>
bldg.<id>/fire/riser.<id>/branch.<id>/head.<id>
bldg.<id>/fire/panel.<id>
bldg.<id>/fire/panel.<id>/zone.<id>
bldg.<id>/fire/panel.<id>/zone.<id>/device.<id>   # smoke, pull, horn/strobe, etc.
```

### 5.5 Vertical Transportation

```
bldg.<id>/vert
bldg.<id>/vert/elev.<id>
bldg.<id>/vert/elev.<id>/car.<id>
bldg.<id>/vert/escalator.<id>
bldg.<id>/vert/stair.<id>          # only when modeled as equipment / pressurization, etc.
```

### 5.6 Structure & Envelope (when first-class)

```
bldg.<id>/struct
bldg.<id>/struct/col.<id>
bldg.<id>/struct/beam.<id>
bldg.<id>/struct/slab.<id>
bldg.<id>/envelope
bldg.<id>/envelope/wall.<id>
bldg.<id>/envelope/win.<id>
bldg.<id>/envelope/door.<id>
bldg.<id>/envelope/roof.<id>
```

Note: In the current L2 domain model many of these remain unmapped by design and appear in the LossReport. When they are promoted to first-class entities they receive addresses in this tree.

### 5.7 Low-Voltage / Special Systems

```
bldg.<id>/lv
bldg.<id>/lv/telecom
bldg.<id>/lv/telecom/rack.<id>
bldg.<id>/lv/security
bldg.<id>/lv/security/panel.<id>
bldg.<id>/lv/avs                        # audiovisual
bldg.<id>/lv/bms                        # building management
bldg.<id>/lv/bms/controller.<id>
```

### 5.8 Site & Civil (when in scope)

```
site.<id>
site.<id>/parking
site.<id>/parking/level.<n>
site.<id>/util                          # site utilities
site.<id>/util/elec
site.<id>/util/water
site.<id>/util/sewer
site.<id>/util/gas
```

---

## 6. IFC Ingestion Contract

When an IFC file is processed the importer must obey the following contract:

1. **Preserve every GlobalId**  
   Any IFC product that becomes an Arxos entity writes its original `GlobalId` into `ifc_global_id`.

2. **Assign a deterministic ArxAddress**  
   Address construction uses, in order of preference:
   - Explicit spatial containment (Building → Storey → Space)
   - System relationships present in the IFC (IfcRelConnects*, flow control, assignment relationships)
   - Stable name / tag / type attributes
   - Deterministic fallbacks (ordered enumeration, coordinate hashing, etc.) only when higher-quality keys are absent

3. **Never**  
   - Use the IFC GlobalId as the ArxAddress  
   - Emit a random UUID as the address  
   - Drop the original GlobalId  
   - Invent system hierarchy that the source data does not support

4. **Record limitations**  
   Incomplete hierarchy or unmapped classes are reported through the LossReport. “Validate OK” means only that the entities that *were* created are internally consistent.

5. **Re-import matching**  
   On subsequent imports the matcher first attempts to locate existing entities by `ifc_global_id`. Only when that fails does it fall back to spatial/system key matching.

---

## 7. CLI Language

The `arx` CLI treats hierarchical `address` as the native language of the model.

### Implemented

```bash
# Init / import with postal root
arx init --name SITE --postal "143677 N. Dale Mabry Hwy, Suite 2, Tampa, FL, 33622"
arx import ifc model.ifc --postal "…"

# Inspection (leading / optional)
arx show   bldg.us.fl.tampa.dale-mabry.143677.s2/fl.1/rm.a101
arx ls     bldg.us.fl.tampa.dale-mabry.143677.s2/elec
arx tree   bldg.us.fl.tampa.dale-mabry.143677.s2/elec --depth 4

# Mutation (Arxos-native — no GlobalId until export)
arx add    bldg…/elec/panel.l1/ckt.14  outlet
arx add    bldg…/elec                  panel --name L1
arx add    bldg…/fl.1/rm.a101          light --name Hall

# Whole-building validate + export (GlobalId assign + write-back)
arx validate [--strict-addresses]
arx export --format ifc --output out.ifc
```

### Designed, not yet implemented

```bash
arx validate bldg…/fl.2          # scoped validate
arx link     …/ckt.14  …/rm.a101/rec.7
arx export   bldg…/fl.2 --format ifc   # address-scoped export
arx proof    bldg…/elec
```

Raw UUIDs and IFC GlobalIds are never the primary addressing mechanism in browse/`add` output.

---

## 8. Determinism, Git, and Proofs

- ArxAddresses are part of the serialized domain model and therefore appear in Git history.
- A change of address is a first-class, reviewable change.
- Merkle proofs and labor proofs operate over the addressable structure; stable addresses are a prerequisite for meaningful proofs across time.
- Export of IFC must prefer the stored `ifc_global_id` for any entity that possesses one. Fresh UUIDs are permitted only for pure helper / non-product entities that never had an IFC origin.

---

## 9. Interaction with LossReport & Validation

- Entities that cannot be admitted to the domain model at all are listed as unmapped products.
- Entities admitted with only partial hierarchy (spatial but no system path, or vice versa) are still created; the missing dimension is noted.
- `arx validate` checks internal consistency of the entities that exist. It does **not** assert that the model is a complete representation of the source IFC.
- `--strict-addresses` elevates address-related warnings to errors for QA and pilot gates.

---

## 10. Extensibility

New system trees may be added by:

1. Defining a clear root segment under the building (`bldg.<id>/<system>`).
2. Documenting the segment vocabulary and ordering rules in this file.
3. Supplying deterministic extraction logic in the importer.
4. Ensuring the CLI `ls` / `tree` / `show` paths work without special cases.

No system tree is allowed to break the global rules in Sections 2–3 and 6.

---

## 11. Non-Goals

- Using IFC GlobalId as a human or CLI identifier.
- Generating non-deterministic addresses.
- Silently inventing hierarchy not supported by source data.
- Making `internal_id` visible in normal CLI output or YAML that humans edit.
- Treating “Validate OK” as evidence of complete BIM fidelity.

---

## 12. Summary Table of Major System Roots

| Root segment     | System                     | Typical deepest leaves          |
|------------------|----------------------------|---------------------------------|
| `bldg.<country>.…` (full root) | Spatial            | `.../rm.<id>/<element>`         |
| `.../elec`       | Electrical distribution    | `.../ckt.<n>/.../rec\|ltg\|sw`  |
| `.../hvac`       | HVAC                       | `.../vav.<id>/diff.<id>`        |
| `.../plumb`      | Plumbing                   | `.../fixture.<type>.<id>`       |
| `.../fire`       | Fire protection            | `.../head.<id>`, `.../device`   |
| `.../vert`       | Vertical transportation    | `.../elev.<id>/car.<id>`        |
| `.../struct`     | Structure                  | `.../col\|beam\|slab.<id>`      |
| `.../envelope`   | Building envelope          | `.../wall\|win\|door\|roof`     |
| `.../lv`         | Low-voltage / special      | `.../rack`, `.../controller`    |
| `site.<…>`       | Site & civil               | `.../util/...`                  |

---

**This document plus ADR 0001 is the source of truth for identity and addressing in Arxos.**  
On conflict, **ADR 0001 wins**. All importers, validators, CLI commands, serializers, and proof systems must conform.