# ArxOS Engineering Manifest, Design, and Implementation Plan

| Property | Details |
| :--- | :--- |
| **Document type** | Engineering design + implementation plan (source of truth for build priority) |
| **Product name** | ArxOS (“Git for Buildings”) |
| **Primary goal** | A working local-first **building compiler**: field/BIM inputs → canonical model → YAML/Git → IFC (and back) |
| **Engine** | Rust (native CLI/agent) + optional WASM (PWA) |
| **Design philosophy** | Local-first, database-less, Git-native, single domain model |
| **Document status** | Living plan — updated to match codebase reality as of post-ingest unification |
| **Audience** | Core maintainers and external development teams |

---

## 0. Purpose of this document

This file replaces an earlier high-level product manifesto with:

1. **What ArxOS is trying to be** (final goal).
2. **What exists today** (honest maturity).
3. **Engineering design** of the target system.
4. **A phased implementation plan** to reach a working product suitable for a real pilot.
5. **Handoff criteria**, risks, and non-goals.

It is intentionally blunt. Marketing claims are secondary to engineering truth.

---

## 1. Final goal (definition of “ArxOS working”)

### 1.1 Product mission

ArxOS treats a building as **versioned structured state**, not a row in a cloud database.

**Working** means a field or facilities team can:

1. Ingest reality (LiDAR and/or existing IFC) on local hardware.
2. Hold a single **canonical building model** in memory.
3. Persist it as **Git-diffable YAML**.
4. Export/import **IFC** without losing Arx identity, structure, or LiDAR metadata (within a defined fidelity contract).
5. Correct the model via **text/AR command scripts** (and later richer AR UI).
6. Review losses/warnings; commit; hand IFC or YAML to other tools or teammates.

### 1.2 Success criteria (MVP “works”)

| ID | Criterion | Measurable exit |
| :--- | :--- | :--- |
| G1 | Single ingest spine | All supported inputs end in `finalize_ingest` → validate → YAML write |
| G2 | Canonical model freeze | YAML + envelope schema versioned; breaking changes require bump |
| G3 | IFC L0–L2 for Arx-authored data | Automated golden tests pass (identity, LiDAR Psets, box geometry, props) |
| G4 | LiDAR → YAML → IFC → YAML | One documented CLI workflow; CI golden on synthetic + 1 real mid-size scan |
| G5 | Text/AR edits | `arx edit` scripts apply, validate, save; WASM can apply script to envelope |
| G6 | Human-in-the-loop | LiDAR structure can be reviewed/corrected before IFC export is “approved” |
| G7 | Pilot scale path | Documented limits + profiled path for ~250k ft² (may be edge agent, not phone) |
| G8 | One supported IFC stack | Native STEP parser is the only *supported* production path |

### 1.3 Success criteria (later: “network works”)

Deferred until G1–G8 hold:

- Oracle / proof-of-labor verification.
- P2P multi-node consensus.
- $AXD token economy and consumer buy-and-burn.

These remain **strategic layers**, not prerequisites for a working compiler.

### 1.4 Explicit non-goals (MVP)

- Full BIM CAD parity (materials, openings, full MEP systems, every IFC class).
- Survey-grade automatic reconstruction without human review.
- Natural-language “chat to edit building” as a primary interface.
- Browser-only processing of full campus LiDAR.
- Multi-device CRDT collaboration in v1.
- Shipping tokenomics as part of pilot software.

---

## 2. Current state assessment (honest)

### 2.1 Scorecard

| Link | Score | Truth |
| :--- | :---: | :--- |
| Domain model | 7/10 | Usable SSOT; still evolving |
| YAML persistence | 8/10 | Right format; multi-file discovery is ops-rough |
| IFC native adapter | 7.5/10 | Strong for Arx-shaped data; not vendor-complete |
| LiDAR pipeline | 6/10 | Works synthetically; heuristics unproven in field |
| Text/AR DSL | 7/10 | Real protocol; not NL |
| PWA / WASM | 4/10 | IFC import + cache; not full field stack |
| Merge + validation | 7.5/10 | Shared layer exists; not enforced on every path |
| Agent / WS | 4/10 | Git/status style RPC; not full model sync product |
| Contracts / token | n/a | Parallel track; not compiler MVP |
| **Compiler spine overall** | **~6.5/10** | Foundation, not finished product |
| **Field pilot readiness** | **~4/10** | Needs human review + golden fixtures + scope cut |

### 2.2 What is solid (do not rewrite)

- **Canonical `Building` graph** (Building → Floor → Wing → Room → Equipment).
- **`src/ingest/`**: `finalize_ingest`, IFC/LiDAR import helpers, text script path, sync envelope.
- **`src/ifc/mapping/`**: identity, LiDAR Psets, property normalization, geometry L2 helpers, merge policies, loss reports.
- **Native IFC export** (`src/export/ifc.rs`) with stable product GlobalIds and Arx Psets.
- **LiDAR pipeline** (parse → downsample → detect → enrich) + shared merge via `MergePolicy::lidar()`.
- **Automated tests**: bidirectional IFC suite, LiDAR suite, ingest/text/sync unit tests.

### 2.3 What is weak or missing (plan must close these)

| Gap | Why it blocks “working” |
| :--- | :--- |
| Dual IFC stacks (native + legacy `BimParser`/`ifc_rs`) | Split behavior; support burden |
| No golden **vendor** IFC fixtures | False confidence from Arx-authored IFC only |
| LiDAR heuristics without ground truth | Cannot trust auto rooms/equipment |
| PWA cannot run LiDAR end-to-end | “Field user” story incomplete |
| YAML schema not versioned on the building document | Integration churn |
| Validation not a hard write gate everywhere | Bad data still lands on disk |
| Orphan policy differs (IFC drops vs LiDAR keeps) | Surprises without product copy |
| Scope sprawl (TUI, Bevy, chain, hardware) | Dilutes MVP delivery |

### 2.4 Target workflow (end state)

```text
┌──────────────────────────────────────────────────────────────────────────┐
│                         FIELD / EDGE DEVICE                                │
│  LiDAR files │ AR app (DSL) │ text script │ IFC from BIM                    │
└───────────────────────────────┬────────────────────────────────────────────┘
                                │
                                v
┌──────────────────────────────────────────────────────────────────────────┐
│  COMPILER (Rust)                                                           │
│  adapters → Building → merge_building_with_policy → validate_building      │
│            → BuildingSyncEnvelope / YAML → Git commit                      │
└───────────────────────────────┬────────────────────────────────────────────┘
                                │
              ┌─────────────────┼─────────────────┐
              v                 v                 v
         YAML/Git            IFC export      PWA review UI
         (source of truth)   (interchange)   (envelope cache)
              │                 │
              └────────┬────────┘
                       v
              re-import / merge / correct
                       │
                       v
              [LATER] Oracle / DePIN / $AXD
```

---

## 3. System design

### 3.1 Principles

1. **One canonical model.** `Building` in memory is the only source of truth for application logic.
2. **Adapters at the edge.** IFC, LiDAR, text, WASM are projections/sources—not parallel databases.
3. **YAML is durable SSOT for Git.** IFC is interchange; envelope JSON is portable cache/sync.
4. **Loss is explicit.** Never silently drop identity, enrichment, or structure without a report.
5. **Fidelity is tiered.** Round-trips are semantic, not byte-identical.
6. **MVP before network.** Compiler correctness before oracle/token.

### 3.2 Canonical data model

#### Hierarchy

```text
Building
  ├── id, ifc_global_id?, metadata?, coordinate_systems
  └── floors[]
        ├── id, name, level, elevation?, ifc_global_id?
        ├── equipment[]          # common areas
        └── wings[]
              ├── name
              ├── equipment[]
              └── rooms[]
                    ├── id, name, room_type, spatial_properties
                    ├── properties (clean free-form keys)
                    ├── lidar_enrichment?
                    ├── ifc_global_id?
                    └── equipment[]
```

#### Identity

| ID | Storage | Role |
| :--- | :--- | :--- |
| Arx `id` (UUID string) | Always | Merge key inside Arx; YAML primary key |
| `ifc_global_id` | Optional | Stable IFC product GlobalId (22-char compressed) |

Rules (implemented; must remain):

- Import GlobalId → `ifc_global_id`; restore Arx id from `Pset_ArxIdentity:ArxId` when present.
- Export: reuse `ifc_global_id` or derive deterministically from Arx UUID.
- Never treat STEP express ids (`#42`) as durable identity.

#### LiDAR enrichment (typed)

```text
LidarEnrichment {
  point_count, confidence_score, last_scan_timestamp?, classification_heuristic?
}
```

Mapped to IFC as `Pset_ArxLidarEnrichment` (not free-form bag after import).

#### Geometry contract (L2)

- Coordinate system: `building_local`, meters.
- Room position: footprint center X/Y, volume bottom Z.
- Room body: extruded WxDxH box and/or local mesh.
- Equipment: position; optional mesh; no synthetic 1×1×1 body on export.
- Compare with `GEOMETRY_EPSILON` (1e-3 m).

### 3.3 Persistence formats

| Format | Role | Schema versioning |
| :--- | :--- | :--- |
| **YAML** | Durable Git SSOT | **Required:** `schema_version` on building document (plan item) |
| **BuildingSyncEnvelope JSON** | PWA/agent portable cache | `schema_version: 1` today (`src/ingest/sync.rs`) |
| **IFC4 STEP** | Industry interchange | Fidelity contract, not full schema |

Envelope shape:

```json
{
  "schema_version": 1,
  "source": "ifc|lidar|text|merge|wasm",
  "updated_at": "ISO-8601",
  "building": { },
  "report": ["Fidelity: L2", "..."]
}
```

### 3.4 Ingest spine (mandatory architecture)

All production inputs must terminate here:

```text
source adapter
    → Building (incoming)
    → optional merge_building_with_policy(existing, incoming, policy)
    → validate_building
    → LossReport / BuildingValidationReport
    → write YAML and/or BuildingSyncEnvelope
```

Key modules:

| Module | Path | Responsibility |
| :--- | :--- | :--- |
| Ingest orchestration | `src/ingest/` | finalize, IFC/LiDAR import, text, sync |
| IFC mapping | `src/ifc/mapping/` | identity, Psets, geometry, merge, reports |
| IFC native parse | `src/ifc/parser/` | STEP lexer/registry/resolver |
| IFC export | `src/export/ifc.rs` | STEP writer |
| LiDAR | `src/spatial/lidar/` | parse, downsample, detect, merge adapter |
| Validation | `src/validation/building.rs` | post-ingest invariants |
| Domain | `src/core/` | Building graph |

#### Merge policies

| Policy | Hierarchy base | Match | Use |
| :--- | :--- | :--- | :--- |
| `MergePolicy::ifc()` | **Incoming** | GlobalId → Arx id → path | Full IFC re-import |
| `MergePolicy::lidar()` | **Existing** | + spatial radius (room 2 m, equip 1.5 m + type) | Re-scan incremental |

**Product rule:** IFC re-import may omit existing entities not present in the file (counted as warnings). LiDAR re-scan keeps unmatched existing. Document this in UX/CLI copy.

### 3.5 IFC fidelity contract

| Tier | Content | Status |
| :--- | :--- | :--- |
| L0 | Hierarchy, names, types, stable product IDs | Done |
| L1 | LiDAR enrichment Psets, Arx free-form Psets | Done |
| L1b | Clean property keys (no double prefix) | Done |
| L2 | Position/dims/mesh subset | Done (box + placement strong) |
| Ops | Merge + loss reports | Done |
| L3+ | Materials, openings, systems, vendor edge cases | **Planned / limited** |

Detail: `docs/ifc-mapping.md`.

### 3.6 Field roles (MVP operational design)

Do **not** require full campus LiDAR inside the phone browser.

| Role | Device | Responsibilities |
| :--- | :--- | :--- |
| **Capture node** | Laptop / Mini / Pi with storage | Run LiDAR pipeline; write YAML; Git commit |
| **Review tablet (PWA)** | Browser WASM | Import IFC, view model, apply text corrections, show reports |
| **BIM exchange** | CLI or agent | Export IFC for facilities / consultants |
| **Agent (optional)** | Always-on edge | Later: pull envelope, merge, commit |

MVP field loop:

```text
1. Capture node: arx import lidar scan.ply --merge
2. Human: arx edit corrections.txt  (or PWA text later)
3. Capture node: arx export --format ifc -o building.ifc
4. Review: re-import IFC or open YAML; read loss/validation report
5. Git commit when approved
```

### 3.7 Technology stack (locked for MVP)

| Layer | Choice | Notes |
| :--- | :--- | :--- |
| Language | Rust 2021 | Single binary `arx` + lib |
| Persistence | YAML + Git | `git2` |
| IFC | Native STEP parser + exporter | Deprecate legacy as unsupported |
| LiDAR | PLY/LAS/XYZ stream + voxel filter | |
| Web | Leptos/WASM (optional feature) | Review UI, not full capture |
| Validation | In-process rules | Expand + hard-gate writes |
| Token/contracts | Solidity/Foundry under `contracts/` | **Phase Network only** |

### 3.8 Target hardware (benchmarks, not blockers)

| Profile | Role | MVP expectation |
| :--- | :--- | :--- |
| Raspberry Pi 4B | Edge agent / light LiDAR | Documented max points; may require aggressive voxel |
| OptiPlex / Mac Mini | Heavy parse + IFC | Primary capture node for pilot |
| Tablet browser | Review only | No full-cloud process in WASM for pilot |

### 3.9 DePIN / Oracle / $AXD (deferred design)

Preserved as the **long-term economic layer**, not MVP:

```text
Compiler produces signed state deltas
        → Oracle verifies labor / integrity
        → Consumers pay; burn $AXD
```

**Implementation rule:** No pilot feature depends on chain liveness. Contracts may evolve in parallel under `contracts/` without blocking G1–G8.

---

## 4. Implementation plan

### 4.1 Phase overview

| Phase | Name | Outcome | Depends on |
| :---: | :--- | :--- | :--- |
| **0** | Contract freeze & hygiene | Clear supported surface; schema versions | — |
| **1** | Single spine enforcement | Every write goes through ingest+validate | 0 |
| **2** | Golden fixtures & CI gates | Real IFC + scan regression suite | 0–1 |
| **3** | LiDAR pilot quality | Human review workflow + known limits | 1–2 |
| **4** | Field ops packaging | Documented pilot runbook; agent optional | 1–3 |
| **5** | PWA review productization | Envelope-first UI; text edit in browser | 1, 4 |
| **6** | IFC L3 / vendor expansion | Controlled BIM interoperability matrix | 2 |
| **7** | Network (Oracle / token) | DePIN layer on trusted compiler | 1–4 |

### 4.2 Phase 0 — Contract freeze and hygiene

**Goal:** Stop thrash before feature work.

#### Design

- Publish **Supported surfaces** matrix (production vs experimental).
- Add `schema_version` to YAML building document (integer, default `1`).
- Document merge orphan policies in CLI help and `docs/`.
- Mark legacy IFC path experimental.

#### Work items

| ID | Task | Owner skill | Done when |
| :--- | :--- | :--- | :--- |
| 0.1 | Add `schema_version` to `Building` / YAML DTO with serde default | Rust | Old YAML loads; new writes emit version |
| 0.2 | Write `docs/supported-surfaces.md` from this manifest §2–3 | Eng | Linked from README |
| 0.3 | `IFCProcessor`: log warning when legacy path used; feature-flag or compile-time deprecate plan | Rust | Native is default; legacy gated |
| 0.4 | Inventory CLI commands; tag MVP vs experimental in help | CLI | `arx --help` is navigable |
| 0.5 | Remove or quarantine dead dual code paths that confuse handoff | Rust | Grep list of “do not use” modules |

#### Exit criteria

- New contributor can answer “what is production?” from docs alone.
- Schema version present on new YAML files.

---

### 4.3 Phase 1 — Single spine enforcement

**Goal:** No supported write bypasses merge/validate discipline.

#### Design

```text
All writers → ingest::finalize_ingest (or ingest_text_script / import_*_path)
Validation errors: configurable --strict fails write
```

#### Work items

| ID | Task | Done when |
| :--- | :--- | :--- |
| 1.1 | Audit every YAML write (CLI, agent, lidar, edit); route through ingest finalize | Checklist complete; no raw write without validate option |
| 1.2 | `--strict` on import/edit: fail if `validation.has_errors()` | Tests cover fail path |
| 1.3 | Always print `summary_lines()` on import/export/edit | Consistent UX |
| 1.4 | Agent IFC already uses import path; extend agent for lidar/text if exposed | Agent docs match |
| 1.5 | Centralize YAML path resolution (one module) | No “first yaml in cwd” surprises without flag |

#### Exit criteria

- Grep shows production writers call ingest/validation.
- Strict mode tested.

---

### 4.4 Phase 2 — Golden fixtures and CI gates

**Goal:** Prove round-trips on data that is not self-authored only.

#### Design

```text
tests/fixtures/
  ifc/vendor/     # anonymized Revit/ArchiCAD exports (small)
  ifc/arx/        # Arx-exported goldens
  lidar/          # mid-size synthetic + 1 real snippet
  yaml/           # expected structure snapshots
```

CI job: `cargo test` + optional `cargo test --features agent` + fixture-based round-trips.

#### Work items

| ID | Task | Done when |
| :--- | :--- | :--- |
| 2.1 | Add ≥2 vendor IFC fixtures (minimal building + multi-storey if possible) | Checked in with license notes |
| 2.2 | Golden: IFC → model → IFC → model for vendor files (structure counts, no panic) | CI green |
| 2.3 | Golden: Arx model → IFC → model (identity, enrichment, dims) already mostly present; keep | Stable |
| 2.4 | Golden: LiDAR synthetic → merge rescan → YAML | CI green |
| 2.5 | Integration test: full CLI workflow via `assert_cmd` or scripted `arx` | One e2e script in CI |
| 2.6 | Performance smoke: time/memory bound on fixture scan | Numbers recorded in docs |

#### Exit criteria

- CI fails if identity/enrichment/geometry L2 regressions return.
- Vendor IFC does not crash; known limitations listed per fixture.

---

### 4.5 Phase 3 — LiDAR pilot quality

**Goal:** LiDAR output is **useful with human review**, not claimed as survey truth.

#### Design

- Detector remains heuristic.
- Add **review state**: rooms/equipment can be `proposed` vs `accepted` (property or enum).
- Export IFC “approved” only includes accepted entities (or warns).
- Confidence scores must be derived or clearly labeled “placeholder.”

#### Work items

| ID | Task | Done when |
| :--- | :--- | :--- |
| 3.1 | Replace hardcoded confidence with feature-based score or document as non-probabilistic | Code + docs |
| 3.2 | `arx edit` / properties: `review_status=proposed\|accepted\|rejected` | Text DSL supports it |
| 3.3 | Export filter or warning for non-accepted entities | CLI flag `--approved-only` |
| 3.4 | Profile detector on pilot sample; document failure modes | Runbook section |
| 3.5 | Fix any remaining enrichment/geometry dual storage (`point_count` in props vs typed) | Single SSOT |

#### Exit criteria

- Pilot team can reject bad rooms in text/CLI before IFC handoff.
- Detector limits written for operators.

---

### 4.6 Phase 4 — Field ops packaging

**Goal:** A second team can run the 250k pilot without reverse-engineering.

#### Design

Capture node runbook + optional agent:

```text
capture-node:
  arx import lidar ... --merge
  arx edit corrections.txt
  arx export --format ifc
  git commit
```

#### Work items

| ID | Task | Done when |
| :--- | :--- | :--- |
| 4.1 | `docs/pilot-runbook.md`: hardware, voxel sizes, memory, workflow | Complete |
| 4.2 | Dockerfile / release binary for capture node | Documented install |
| 4.3 | Resource limits: max points, voxel defaults by “light” mode | Validated on Pi or documented as unsupported |
| 4.4 | Sample pilot project template (`arx init` + example scripts) | Repo template |
| 4.5 | Observability: structured logs for ingest summary | Operators can debug |

#### Exit criteria

- Cold-start: new engineer completes sample workflow in &lt; 1 day from docs.

---

### 4.7 Phase 5 — PWA review productization

**Goal:** Tablet is a **review and correct** surface, not a fake scanner.

#### Design

- Envelope is the only stored form (`store_active_building` / `load_active_building`).
- UI: import IFC, show report, list floors/rooms, apply text script, export JSON envelope.
- Optional: connect agent WS to push envelope for commit (later).

#### Work items

| ID | Task | Done when |
| :--- | :--- | :--- |
| 5.1 | Import page already envelope-aware; add report panel polish | UX usable |
| 5.2 | Text edit UI (textarea → `apply_text_script_json`) | Works offline |
| 5.3 | Building detail always loads envelope | No dual-key bugs |
| 5.4 | “Download YAML/JSON” for handoff to capture node | File export |
| 5.5 | Do **not** port full LiDAR to WASM in this phase | Explicit non-goal |

#### Exit criteria

- Reviewer can import IFC, correct via text, re-export envelope without desktop IDE.

---

### 4.8 Phase 6 — IFC vendor expansion (controlled)

**Goal:** Interop matrix, not infinite schema.

#### Work items

| ID | Task | Done when |
| :--- | :--- | :--- |
| 6.1 | Matrix: Revit / ArchiCAD / FreeCAD × what we preserve | Doc table |
| 6.2 | Improve placement/units for common vendor quirks | Fixture tests |
| 6.3 | Optional: mesh round-trip quality tests | Known epsilon |
| 6.4 | Deprecate legacy parser entirely | Single stack |

---

### 4.9 Phase 7 — Network layer (Oracle / $AXD)

**Goal:** Only after compiler trust.

#### Design reminders

- Oracle verifies **state transitions** and labor proofs—not raw geometry recompute on-chain.
- Token burn on consumer purchase is economic policy, not ingest correctness.
- Smart contracts under `contracts/` stay isolated from MVP CLI path.

#### Work items (outline only)

| ID | Task |
| :--- | :--- |
| 7.1 | Define signed contribution payload from YAML delta / merkle (existing experiments) |
| 7.2 | Oracle rules for acceptance |
| 7.3 | Minimal consumer payment → burn flow |
| 7.4 | Threat model and audit before mainnet |

---

## 5. Detailed design: critical subsystems

### 5.1 IFC adapter

**Import path:** STEP → native lexer/registry → resolver → mapping (identity, lidar, properties, geometry) → Building + LossReport.

**Export path:** Building → assign/reuse GlobalIds → products + Psets → STEP.

**Must not regress:**

- Product GlobalId stability across double export.
- `Pset_ArxIdentity`, `Pset_ArxLidarEnrichment`.
- Clean free-form keys on domain bags.

**Implementation files:** `src/ifc/parser/*`, `src/ifc/mapping/*`, `src/export/ifc.rs`.

### 5.2 LiDAR adapter

**Path:** file → stream points → voxel filter → floor/room/equipment detect → enrichment → Building → `MergePolicy::lidar()` merge.

**Implementation files:** `src/spatial/lidar/*`, merger delegates to `merge_building_with_policy`.

### 5.3 Text / AR adapter

**Path:** DSL script → `apply_text_script` → `ingest_text_script` → finalize + validate.

**Grammar (v1):** see `src/ingest/text.rs` and CLI `arx edit`.

AR devices should emit this DSL (or JSON of the same ops later)—not free-form NL in MVP.

### 5.4 Sync / PWA

**Path:** Building → `BuildingSyncEnvelope` → localStorage / file.

**WASM exports:** parse IFC envelope, store/load, merge envelopes, apply text (`src/web/wasm_bridge.rs`).

### 5.5 Validation

**Invariants (expand over time):**

- Non-empty building/floor/room names as required.
- Unique room/equipment ids.
- Non-negative dimensions; valid bboxes.
- LiDAR confidence in \[0, 1\].
- No double-prefixed Arx property keys.
- Optional: require `schema_version`.

**Hard gate:** Phase 1 `--strict`.

---

## 6. Testing strategy

| Layer | What | Where |
| :--- | :--- | :--- |
| Unit | Identity, Psets, property normalize, geometry helpers, text parse, merge policies | `src/**/tests`, `ifc/mapping` |
| Integration | Bidirectional IFC, LiDAR pipeline, backbone YAML↔IFC↔merge | `tests/bidirectional_tests.rs`, `tests/lidar_tests.rs` |
| Golden | Vendor IFC + scan fixtures | Phase 2 |
| E2E | CLI scripted workflows | Phase 2–4 |
| Manual pilot | School campus sample | Phase 4 |

**Rule:** No claim of “round-trip works” without a named test or fixture.

---

## 7. Delivery plan for an external team

### 7.1 Recommended team shape (MVP)

| Role | Focus |
| :--- | :--- |
| Rust systems engineer | Ingest spine, IFC/LiDAR, performance |
| BIM/interop engineer | Vendor fixtures, IFC edge cases |
| Edge/DevOps | Capture node packaging, pilot runbook |
| Light frontend | PWA review UI only |
| (Optional later) | Protocol/token |

### 7.2 Suggested milestone timeline (indicative)

| Milestone | Calendar (order-of-magnitude) | Delivers |
| :--- | :--- | :--- |
| M0 | 1–2 weeks | Phase 0 freeze |
| M1 | 2–3 weeks | Phase 1 spine enforcement |
| M2 | 3–4 weeks | Phase 2 goldens + CI |
| M3 | 3–5 weeks | Phase 3 LiDAR review quality |
| M4 | 2–3 weeks | Phase 4 pilot packaging |
| M5 | 2–4 weeks | Phase 5 PWA review |
| **MVP pilot-ready** | **~3–4 months** | G1–G8 with human review |
| Network | After pilot learnings | Phase 7 |

Adjust for team size; sequence matters more than calendar.

### 7.3 Handoff package checklist

- [ ] This manifest (`arxos_manifest.md`)
- [ ] `docs/ifc-mapping.md`
- [ ] `docs/supported-surfaces.md` (to write in Phase 0)
- [ ] `docs/pilot-runbook.md` (Phase 4)
- [ ] Green `cargo test` + bidirectional + lidar suites
- [ ] List of experimental modules (agent, chain, heavy render3d)
- [ ] Known IFC/LiDAR limitations table

---

## 8. Risk register

| Risk | Severity | Mitigation |
| :--- | :---: | :--- |
| Vendor IFC breaks native path | High | Phase 2 fixtures; interop matrix |
| LiDAR false structure trusted | High | Human review status; no auto-trust |
| Scope creep (token, full CAD, full PWA scan) | High | Enforce phases; this document |
| Dual parsers | Medium | Phase 0–6 deprecation |
| Edge hardware insufficient | Medium | Light mode; capture node class machine |
| Schema churn during handoff | Medium | `schema_version`; freeze windows |
| Multi-user sync conflicts | Medium | Last-write-wins envelope only until Phase 7+ |
| Security of agent tokens / PWA storage | Medium | Separate security review before pilot network exposure |

---

## 9. Repository map (implementation anchors)

```text
src/core/           Canonical Building model
src/ingest/         finalize_ingest, IFC/LiDAR import, text, sync envelope
src/ifc/            Native IFC parse + mapping
src/export/ifc.rs   IFC export
src/spatial/lidar/  Point cloud pipeline
src/validation/     Post-ingest validation
src/cli/            arx import|edit|export|...
src/web/            PWA (review)
src/agent/          Optional remote agent
contracts/          Token/oracle (Phase 7)
tests/              Integration / bidirectional / lidar
docs/               ifc-mapping and operational docs
```

---

## 10. Immediate next actions (start here)

1. **Phase 0.1–0.3:** schema_version + supported-surfaces + native-only policy.
2. **Phase 1.1–1.2:** force all writers through validate; add `--strict`.
3. **Phase 2.1–2.2:** check in first vendor IFC fixtures and CI.
4. Freeze feature work outside Phases 0–2 until green.

---

## 11. Document history

| Version | Notes |
| :--- | :--- |
| Pre-rewrite | Product manifesto (DePIN/compiler/oracle/token overview) |
| This version | Full engineering assessment + design + phased implementation plan for a working ArxOS compiler MVP; network/token deferred |

---

## 12. Closing statement

ArxOS works when the **compiler spine** is boringly reliable:

**LiDAR / text / IFC → one model → YAML/Git → IFC → back**, with explicit loss reports and human review of automated structure.

Everything else—PWA polish, DePIN, token, advanced CAD—is multiplier **after** that spine is trusted.

This document is the plan to get there without lying about readiness.
