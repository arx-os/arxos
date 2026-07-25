# ADR 0001: Identity & Addressing — Final Decisions

**Status:** Accepted  
**Date:** 2026-07-25  
**Deciders:** Founder / Project Lead  
**Related:** [`../reference/identity-and-addressing.md`](../reference/identity-and-addressing.md) (detailed design) · [`../reference/identity.md`](../reference/identity.md) (code map)

---

## Context

Arxos needs a clear, long-term identity model that serves three distinct needs:

1. **Provenance** — Track where an object originally came from in an IFC file.
2. **Operational identity** — Give humans and the CLI a stable, hierarchical way to name and navigate every significant object.
3. **Round-tripping** — Allow changes made through the Arxos model (including new objects) to be written back into IFC.

The previous model used a random UUID as the primary key and an optional geo-style address. That approach conflicted with the goal of a human-meaningful, hierarchical, CLI-native identity system.

This ADR records the final decisions that resolve the open questions from the architecture compliance review.

---

## Decisions

### 1. Primary Operational Identity

**Decision:** `arx_address` is the primary operational identity.

- Humans and the CLI address entities exclusively through hierarchical ArxAddresses.
- The internal UUID (`id`) is demoted to an implementation detail. It may remain for merge stability and internal linking but must not be the primary way users or the CLI refer to entities.
- Every significant domain entity (Building, Floor, Room, Equipment, and system objects) should ultimately carry an `arx_address`.

**Consequence:**  
Import, validation, CLI, and serialization must treat `arx_address` as the main identity surface. Missing addresses on core entities become a first-class concern (initially warnings, later optionally errors under strict mode).

### 2. IFC GlobalId (Provenance)

**Decision:** IFC `GlobalId` is always preserved when present.

- Stored in the field `ifc_global_id`.
- Never used as the primary operational identity.
- Used for:
  - Re-import matching (GlobalId-first).
  - Provenance and audit.
  - Round-trip export of objects that originated in IFC.

**New objects created inside Arxos** (for example, an outlet added via the CLI) have no original GlobalId. On IFC export they receive a newly generated, valid IFC GlobalId.

**Consequence:**  
The two identity systems remain cleanly separated. Editing through ArxAddress does not destroy provenance. Export must support both “update existing IFC entity” and “create new IFC entity” paths.

### 3. Address Syntax — Dots Allowed

**Decision:** Dots (`.`) are legal inside address segments.

Examples that must be valid:

```text
fl.2
rm.215
panel.L1
ckt.14
rec.7
```

**Consequence:**  
The address parser and validator must be updated. The previous charset rule that rejected `.` is revoked. Segment rules remain: lowercase, kebab-case or short mnemonics, no spaces.

### 4. Building Root Format (Worldwide Safe from Day 0)

**Decision:** Building roots use a fully qualified, hierarchical form from Day 0.

Format:

```text
bldg.<country>.<region>.<city>.<street>.<number>[.<unit>]
```

All segments are **dot-separated** (street and number are separate segments). Concrete example:

```text
bldg.us.fl.tampa.dale-mabry.143677.s2
```

Derived from the postal address:

```text
143677 N. Dale Mabry Hwy, Suite 2, Tampa, FL, 33622
```

**Rules for derivation:**

- Country and region use stable short codes (`us`, `fl`).
- City is lowercase, hyphenated if needed.
- Street name is simplified (drop directional prefixes and suffixes such as N., Hwy, St, Ave).
- Street number is included.
- Unit/suite is included when present (`s2`, `u4`, etc.).
- Entire root is lowercase and deterministic.

**Consequence:**  
This form is unique enough for worldwide use while remaining human-readable. Shorter forms are not used for new buildings. The parser must accept multi-segment building roots.

### 5. Timing and Scope

**Decision:** These decisions are effective immediately and guide current implementation work.

- This is not deferred to a future pilot tag.
- Implementation may be incremental, but new code and migrations must move toward this model rather than the old UUID-primary + geo-address model.
- Manual assignment or correction of addresses is acceptable in the short term while automatic derivation matures.

---

## Round-Trip Requirement (Explicit)

Changes made through the ArxAddress hierarchy must be representable on IFC export:

- Existing IFC-origin objects keep their `ifc_global_id` and are updated in place when possible.
- New Arxos-native objects are emitted as new IFC entities with freshly generated GlobalIds.
- Loss of information on export must remain visible through the existing honesty mechanisms (LossReport / export warnings).

This requirement is part of the identity architecture, not a separate future feature.

---

## Rejected Alternatives

| Alternative | Reason for rejection |
|-------------|----------------------|
| Keep UUID as primary operational identity | Conflicts with human/CLI hierarchical navigation goals |
| Use IFC GlobalId as the primary address | Opaque, not hierarchical, not human-friendly |
| Geo-style addresses (`/country/state/city/...`) | Poor fit for building-system hierarchy; collisions and verbosity |
| Short building roots only (`bldg.dale-mabry-143677`) | Insufficient uniqueness at worldwide scale |
| Disallow dots in segments | Prevents natural mnemonics (`panel.L1`, `fl.2`) |
| Defer entire redesign to pilot.6 | Leaves the project with two conflicting identity stories |

---

## Implementation Implications (Non-Exhaustive)

1. ~~Update address parser/validator to allow `.` and multi-segment `bldg.` roots.~~ **Done**
2. ~~Ensure import writes addresses onto Building, Floor, and Room (not only Equipment).~~ **Done**
3. ~~Keep `ifc_global_id` population and GlobalId-first merge behavior.~~ **Done** (+ export assign/write-back for native)
4. Evolve CLI toward address-native commands — **`show` / `ls` / `tree` / `add` done**; scoped validate / `link` still open.
5. Treat export as a real mapping layer that can both update and create IFC entities — **identity path done** (GlobalId preserve + mint); geometric fidelity still L2.
6. ~~Retire or clearly supersede older identity documentation that declares UUID the YAML primary key.~~ **Done** (`identity.md` rewritten as code map).

**Living status:** [`identity-and-addressing.md`](../reference/identity-and-addressing.md) · [`identity.md`](../reference/identity.md)

---

## Status of Related Documents

- [`identity-and-addressing.md`](../reference/identity-and-addressing.md) remains the detailed design reference (keep in sync with this ADR).
- This ADR is the binding record of the decisions that resolve prior open questions.
- Any older document that contradicts these decisions (including prior statements that UUID is the primary operational key) is superseded on the points of conflict — especially [`identity.md`](../reference/identity.md).

---

## Confirmation

These decisions are accepted and govern subsequent design and implementation work on identity, addressing, CLI language, and IFC round-tripping.
