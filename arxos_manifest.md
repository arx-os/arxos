# ArxOS Engineering Manifest, Design, and Implementation Plan

| Property | Details |
| :--- | :--- |
| **Document type** | Engineering design + implementation plan (source of truth for build priority) |
| **Product name** | ArxOS (“Git for Buildings” / version control for the built world) |
| **Version (crate)** | 2.0.0 (`arx` binary / `arxos` lib) |
| **Primary goal** | **Full product:** free local software to map buildings as code + peer review + **$AXD rewards** for verified as-built data + **buyer market** for data access |
| **Engine** | Rust 2021 (CLI + lib) · native IFC · Git SSOT · Foundry contracts · optional WASM/agent/render3d/`blockchain` |
| **Design philosophy** | Local-first · single `Building` model · Git-native · free to use · pay only for data access |
| **Document status** | Living plan — full vision locked; compiler + economy spine **lab-complete** (N1–N5); path to live loop is Horizon A–C (§1.5, §10) |
| **Last reconciled** | 2026-07-13 (deployment obligations §1.6 — school/district pilot bar) |
| **Audience** | Vision holder, field IT pilots, core maintainers, external builders |

---

## 0. Purpose of this document

This file is the engineering source of truth for:

1. **What ArxOS is** (vision + definition of working).
2. **What exists today** (honest maturity — lab vs field).
3. **System design** (compiler + contribution + oracle + payment).
4. **Phased plan** to a live closed loop (not feature sprawl).
5. **Handoff criteria**, risks, non-goals, integrity ledger (§2.6).

It is intentionally blunt. Marketing is secondary to engineering truth.

---

## 0.1 Product vision (locked)

**One sentence:** Version control for the built world — free to use; peer built, reviewed, and rewarded.

### Why buildings

Most buildings are **as-built black holes**. That kills and injures workers (e.g. live electrical work without circuit truth), forces contractors to price **unknowns**, and leaves infrastructure builders underpaid for documenting reality. ArxOS makes as-built data a durable **open ledger** of “A Building’s Life,” and **financially rewards** those who map it.

### Principles → engineering

| Principle | Engineering consequence |
| :--- | :--- |
| Free software | Compiler/CLI is not paywalled |
| Peer built + reviewed | Capture + `review_status` + validation hard gates |
| Rewarded labor | Verified **building data** → package → oracle mint **$AXD** |
| Data market | Buyers pay **$AXD** for access; demand supports token |
| Local-first / edge | World runs capture nodes; maintainers cannot host every building |
| Git collaboration | Any Git host; GitHub is convenience, not lock-in |
| Standard ambition | As standard as building code for representing the building itself |

### Locked architect defaults

1. **Primary labor unit:** validated `Building` / `building.yaml` (optional Git commit). Not sensor `DeviceState` as primary.
2. **`buildingId`:** building UUID (= Registry `buildingId`).
3. **Quality:** validation + LiDAR review coverage (`src/contribution/quality.rs`).
4. **Chain bring-up:** Foundry E2E green → Anvil/live env script → public testnet → Base.
5. **Oracles v1:** 2-of-3; ArxOS keys for bring-up, external stakers later.
6. **Peripherals:** ask before expanding PWA / hardware / 3D / multi-building campus layouts.

### Full-product spine

```text
FIELD (free software)
  LiDAR / IFC / text → Building → review → building.yaml + Git
           │
           ▼ arx contribute
  contribution.json (merkle + quality + building UUID)
           │
           ▼ EIP-712 + oracles (2-of-3) + delay
  mint $AXD  (70 worker / 10 building / 10 maintainers / 10 treasury)
           │
BUYER MARKET
  arx access quote → pay $AXD → AccessPaid → host gates data delivery
```

| Segment | Lab status | Live / field status |
| :--- | :---: | :---: |
| Compiler (G1–G8 core) | **Done** (synthetic CI) | Field unproven |
| Contribute package (N1) | **Done** | Needs deploy env |
| Sign / propose (N2–N3) | **Done** (Foundry + CLI) | Needs live addresses + ops |
| Registry UUID (N4) | **Done** (Foundry E2E) | Needs register helpers |
| Buyer access (N5) | **Done** (Foundry + CLI) | Needs host gate on `AccessPaid` |
| Multi-peer Git (N6) | Partial (docs) | Process only |

See `docs/contribution-path.md`, `docs/data-access.md`.

---

## 1. Final goal (definition of “ArxOS working”)

### 1.1 Product mission

ArxOS treats a building as **versioned structured state** — an open ledger of as-built truth — not a row in a cloud database.

**Working (full product)** means all of the following can happen for a real building:

1. **Map** — ingest LiDAR and/or IFC on local hardware into one canonical model.
2. **Persist** — durable `building.yaml` + Git (any host).
3. **Interchange** — export/import IFC within the fidelity contract (identity, structure, LiDAR metadata).
4. **Correct & review** — text/AR edits; LiDAR autos start `proposed`; humans accept/reject before approved export.
5. **Reward** — verified model labor becomes a contribution commitment; oracles mint **$AXD**.
6. **Transact** — a data buyer pays **$AXD** for access; data is only released after payment proof.

Compiler without reward is incomplete for the vision. Reward without trusted as-built data is hollow.

### 1.2 Success criteria — compiler (trust root)

| ID | Criterion | Measurable exit | Status (2026-07) |
| :--- | :--- | :--- | :---: |
| G1 | Single ingest spine | Writers use finalize / validate / save gates | **Done** |
| G2 | YAML schema versioned | `schema_version: 1` on building document | **Done** |
| G3 | IFC L0–L2 Arx-authored | Automated identity/enrichment/geometry tests | **Done** |
| G4 | LiDAR → YAML → IFC path | Synthetic CI + CLI workflow | **Partial** (field unproven) |
| G5 | Text/AR edits | `arx edit` + validate/save | **Done** (CLI); WASM partial |
| G6 | Human-in-the-loop LiDAR | `review_status` + export warn / `--approved-only` | **Done** (lab) |
| G7 | Pilot scale path | Runbook + profiled ~250k ft² | **Open** (docs partial) |
| G8 | One IFC stack | Native STEP only | **Done** |

### 1.3 Success criteria — economy / network

| ID | Criterion | Status |
| :--- | :--- | :---: |
| N1 | Building commitment package from validated model | **Done** |
| N2 | EIP-712 `ContributionProof` from package | **Done** |
| N3 | 2-of-3 propose → finalize mint (quality-scaled 70/10/10/10) | **Done** (Foundry) |
| N4 | Registry: worker + building UUID | **Done** (Foundry); live CLI env open |
| N5 | Buyer `payForAccess` $AXD path | **Done** (Foundry + `arx access`) |
| N6 | Multi-peer via Git remotes (not CRDT-first) | **Partial** |
| N7 | **Host gates data on `AccessPaid`** | **Done** (lab: `export --commercial` + receipt) |
| N8 | **One-command local deploy env** (addresses + register helpers) | **Done** (`horizon_a_deploy_env.sh`) |
| N9 | **One real-building closed loop** (field) | **Open** — Horizon B |

### 1.4 Explicit non-goals (near term)

- Full BIM CAD parity (materials, openings, every IFC class).
- Survey-grade auto reconstruction without human review.
- NL “chat to edit building” as primary interface.
- Browser-only full campus LiDAR.
- Multi-device CRDT collaboration before Git multi-remote is boring.
- Expanding peripherals (PWA/hardware/3D) before Horizon A–B exit.

### 1.5 Path to “it works” (horizons)

```text
HORIZON A — Lab → live local (current priority)
  Deploy env script → .env.arx addresses
  Register worker + building UUID from building.yaml
  contribute --sign/--submit + second oracle + finalize (test warp or real delay)
  access pay; document host must check AccessPaid
  Exit: cold engineer completes mint + pay without reading Solidity

HORIZON B — First real building (vision holder field test)
  One site, real as-built pain, capture node + reviewer (+ buyer if possible)
  Measure: unknowns reduced? mint/pay understandable?
  Exit: one successful closed loop on messy real data; fix only blockers

HORIZON C — Network scale (after B works ≥1–2 times)
  External oracles, public testnet → Base
  Host product that enforces payment before data
  Optional: own forge; more vendor IFC; multi-building later
```

**Rule:** Do not start Horizon C feature work until Horizon B has succeeded at least once.

### 1.6 Deployment obligations (reservations → work)

**Hard truth:** Lab-complete (N1–N5, Horizon A tooling) is **not** “absolutely ready for district production.”  
This section is the **obligation register**: each reservation must be **relegated** (reduced or closed) by named work before the corresponding go-level is claimed.

#### Go levels (do not skip)

| Level | Allowed claim | Requires |
| :---: | :--- | :--- |
| **L0 — Lab** | “CI / Foundry / local Anvil path works” | Current default |
| **L1 — Controlled field pilot** | “We may run free as-built software on **one** building under policy” | **R1, R2, R5, R7, R8, R9, R10** at least *pilot-mitigated* |
| **L2 — Multi-building program** | “Repeatable district process” | L1 + **R3, R6** closed for profiled sites; second-person walkthrough repeated |
| **L3 — Full vision (reward + market)** | “Mint/pay as production path” | L2 + **R3 (ops), R4 (enforced host), R8 (token policy)** closed |

**Default for a public school district first use:** target **L1 only**. Keep **$AXD mainnet and paid market off** the critical path until L3 criteria are met.

#### Obligation register

| ID | Reservation (what is wrong / incomplete) | Why it matters (district / field) | Work to relegate | Exit criteria | Owner | Status |
| :---: | :--- | :--- | :--- | :--- | :---: | :---: |
| **R1** | **Field LiDAR quality unproven** | Auto rooms/equip can be wrong; false certainty is dangerous near electrical / life safety | Run 1–2 real scans; mandatory human review; log false +/−; document site failure modes | Written failure-mode note for pilot site; no “official” use of unreviewed `proposed` entities | Field + eng | **Open** |
| **R2** | **Vendor BIM/IFC incomplete** | District Revit/etc. exports may drop structure/IDs | Import 2–3 **real** anonymized district IFCs; round-trip matrix | Local interop matrix (preserve/drop) checked in or attached to pilot | Field + eng | **Open** |
| **R3** | **Live chain/mint ops not turnkey** | 2-of-3, stake, 24h finalize, keys ≠ “install and forget” | Keep L1 **off-chain**; for L3: ops runbook with two oracles + finalize; testnet only until policy OK | L1: chain optional/demo. L3: documented mint with named operators | Eng + ops | **Open** (lab E2E done) |
| **R4** | **Host payment gate is local-file only** | `export --commercial` + receipt is bypassable; free export still works by design | Process: commercial deliveries **must** use `--commercial`. Product: host that checks `AccessPaid` / receipt server-side (L3) | L1: written process. L3: non-bypassable download path | Eng + field IT | **Partial** (CLI gate done; enforcement open) |
| **R5** | **No second-person cold start on district env** | Hero dependency; program dies if only one tech can run it | Timed walkthrough by non-author on district laptop/network | Checklist signed; stuck points filed as backlog | Field IT | **Open** — template: `docs/second-person-checklist.md` |
| **R6** | **Scale/performance unprofiled** | Large school models may OOM/hang; people skip validation | Profile worst-case IFC/scan on pilot hardware; set limits | Written max points/time; light-mode guidance | Eng + field | **Open** |
| **R7** | **Security / compliance / classification** | Facility plans sensitive; Git remotes, exports, backups | Data class policy (internal-only default); who can clone/export; no student PII in properties | Security/IT sign-off for pilot repo location | Field IT + security | **Partial** — `docs/data-classification.md` + charter §4 (needs sign-off) |
| **R8** | **Mainnet token / institutional fit** | Public entity crypto, custody, procurement, reputation | L1/L2: **no production token**. L3 only with Legal/Finance | Written go/no-go from leadership for any chain use | Vision + Legal | **Partial** — L1 default off-chain in charter §5 |
| **R9** | **Support / ownership / change control** | No vendor SLA; `main` moves | Pin release tag/hash; one supported workflow page; escalation path | Pinned install + “supported loop” doc used in R5 | Eng + field IT | **Partial** — tag `v2.0.0-pilot.1` @ `ba33e6ba`; charter must record pin; R5 must walk that pin |
| **R10** | **Safety / professional liability framing** | Model must not replace LOTO, licensed drawings, or code docs | Pilot disclaimer policy; culture: human + licensed docs win | Signed pilot charter with disclaimer language | Field IT + leadership | **Partial** — template `docs/pilot-charter.md` (needs signature) |

#### Work packages to relegate obligations (ordered)

| Package | Obligations hit | Deliverables | Status |
| :---: | :--- | :--- | :---: |
| **P-Safety** | R10, R1 (process) | `docs/pilot-charter.md`; no unreviewed `proposed` as official | **Template done** — sign to close R10 |
| **P-Transfer** | R5, R9 | `docs/l1-supported-workflow.md`; `docs/second-person-checklist.md`; `docs/pilot-release.md`; `docs/field-handoff.md`; `scripts/pin_pilot_release.sh` | **Pin cut** (`v2.0.0-pilot.1`) — second-person walkthrough still open for R5 |
| **P-Data** | R7 | Classification + private Git; export approval same class as CAD | **Template done** — `docs/data-classification.md` (sign to close) |
| **P-Field-truth** | R1, R2, R6 | Real scan + real IFC matrix + one performance profile on pilot hardware | **Template done** — `docs/field-truth-log.md`; **site evidence open** |
| **P-Chain-optional** | R3, R8 | Explicit “compiler pilot = off-chain”; testnet demo only if requested | **Partial** (charter §5 + L1 workflow) |
| **P-Market-enforcement** | R4 | L1 process; L3 host service that gates download on payment | **Partial** (CLI gate; process in charter optional) |

**Relegation rule:** Do not mark an obligation **Done** without exit criteria evidence (doc path, test name, or signed checklist). Update this table when evidence lands.

#### Mapping to horizons

| Horizon | Primary obligations to attack |
| :--- | :--- |
| **A** (tooling) | R3 lab ops, R4 CLI gate — **mostly done** |
| **B** (first building) | **P-Safety, P-Transfer, P-Data, P-Field-truth** (R1,R2,R5,R6,R7,R9,R10) |
| **C** (network scale) | R3 production ops, R4 enforced host, R8 institutional token go |

---

## 2. Current state assessment (honest)

### 2.1 Scorecard (2026-07-13 — lab vs field)

| Link | Score | Truth |
| :--- | :---: | :--- |
| Domain model | **8/10** | Building hierarchy; durable `ArxAddress`; review_status |
| YAML + Git SSOT | **8.5/10** | Single `building.yaml`; `schema_version: 1`; validated saves |
| IFC native | **8/10** | Only stack; Arx goldens + SketchUp/HVAC non-panic samples |
| LiDAR | **6.5/10** | Synthetic CI + proposed review; **field unproven (R1)** |
| Text/AR DSL | **8/10** | `arx edit` + review_status keys |
| Contribution / reward | **7.5/10** | Package + EIP-712 + Foundry mint E2E; **live ops still hard (R3)** |
| Buyer access market | **7.5/10** | Router E2E + `arx access` + commercial export gate; **not server-enforced (R4)** |
| PWA / WASM | **4/10** | Optional; not L1 blocker |
| Contracts ($AXD) | **8/10** | Foundry suite green; oracle proof lock fixed |
| CLI surface | **8/10** | Compiler + contribute + access; spatial honesty |
| CI | **8/10** | Compiler CI + forge; clippy green (unwrap allow-listed) |
| **Lab closed-loop** | **~8/10** | N1–N8 tooling present |
| **District pilot (L1) readiness** | **~4/10** | Blocked on §1.6 obligations R1,R2,R5,R7,R9,R10 |
| **Full vision (L3) readiness** | **~2/10** | Needs L1+L2 + R3/R4/R8 production |

**Audit rule:** Scores reflect what a second engineer experiences **today** (CI, CLI, forge)—not aspiration. **§1.6 overrides optimistic claims.**

### 2.2 Architecture convergence completed (do not re-open without cause)

The following dual authorities were **eliminated** in the 2026-07 convergence work (residuals called out; owned by §2.6):

| Former dual | Canonical now |
| :--- | :--- |
| Native IFC + `BimParser` / `ifc_rs` | **Native STEP only** (`IFCProcessor::parse_native*`) |
| Multi-file Git export tree + single YAML | **`building.yaml` only** |
| Many YAML load/write paths | **`PersistenceManager` / `load_building_at` / `save_building_at`** (save still serialize-only — **I4**) |
| Working `BuildingData` vs `Building` | **Intent:** `core::Building` only; DTO in `yaml.rs`. **Residual I5:** spatial ops still use `BuildingData` |
| Soft validation on CRUD/TUI | **`ingest::persist_building`** for room/equipment mutators. **Residual I4:** public `save_*` unvalidated |
| Name-only `arx query` | **Durable `ArxAddress` globs** |
| `#[serde(skip)]` addresses | **Addresses round-trip in YAML** |
| Hollow clap surface (economy, sensors, game, …) | **Compiler-oriented CLI**. **Residuals I3/I7/I8:** spatial theater; unused `--delta`; interactive stubs |
| Orphan nested test trees | **`tests/*.rs` targets + fixtures only** |
| Bloated multi-OS / tarpaulin PR CI | **`compiler-ci.yml` is intended source of truth**. **Residual I1:** not green under clippy deny-warnings |

### 2.3 What is solid (do not rewrite)

- **Canonical `Building` graph** (Building → Floor → Wing → Room → Equipment).
- **`src/ingest/`**: `finalize_ingest`, `persist_building`, `import_ifc_path`, `import_lidar_path`, text scripts, sync envelope.
- **`src/ifc/mapping/`**: identity, LiDAR Psets, property normalization, geometry L2 helpers, merge policies, loss reports.
- **Native IFC only**: parser under `src/ifc/parser/`; export under `src/export/ifc.rs`.
- **LiDAR pipeline**: parse → downsample → detect → enrich → Building; merge via `MergePolicy::lidar()` (no separate `ModelMerger` type).
- **Persistence**: `{base}/building.yaml` via `BuildingYamlSerializer`; Git via `BuildingGitManager`.
- **Addressing**: `ArxAddress` on equipment; `arx migrate` backfill; `arx query` glob match.
- **Automated spine tests**: `compiler_spine_test`, `ifc_compiler_path_test`, `bidirectional_tests`, `lidar_tests`, `ifc_native_tests`.
- **Compiler + economy CLI** — import/edit/export/contribute/access (see §9.2); Foundry mint + pay E2E.
- **Integrity close-out** — §2.6 I1–I11 done; residual process I12.

### 2.4 What is still weak or missing

| Gap | Obligation | Horizon |
| :--- | :---: | :---: |
| Field LiDAR truth unknown | **R1** | B |
| District vendor IFC unproven | **R2** | B |
| Live mint ops / institutional token | **R3, R8** | B off-chain; C for L3 |
| Payment gate bypassable / no portal | **R4** | B process; C product |
| Second-person district cold start | **R5** | B |
| Scale unprofiled | **R6** | B |
| Data classification / security | **R7** | B (before multi-user) |
| Support pin + ownership | **R9** | B |
| Safety / liability framing | **R10** | B (before any “official” use) |
| Real-building closed loop (N9) | R1–R2, R5, R10 | B |
| Optional rings (PWA, hardware, 3D) | freeze | — |

Full obligation register and exit criteria: **§1.6**.

### 2.5 Target workflow (current + end state)

```text
┌──────────────────────── FIELD (free software) ───────────────────────────┐
│  LiDAR │ IFC │ text/AR edit │ human review_status                        │
└───────────────────────────────┬──────────────────────────────────────────┘
                                v
┌──────────────────────── COMPILER (lab done) ─────────────────────────────┐
│  adapters → Building → merge? → validate → building.yaml → Git           │
│  export IFC (warn / --approved-only) · query · migrate                     │
└───────────────────────────────┬──────────────────────────────────────────┘
                                v
┌────────────────── ECONOMY (lab done; live open) ─────────────────────────┐
│  arx contribute → package → EIP-712 → oracles → mint $AXD                │
│  arx access quote/pay → $AXD → AccessPaid → [N7 host must gate data]     │
└──────────────────────────────────────────────────────────────────────────┘
```

### 2.6 Integrity debt inventory (brutal review — must stay closed)

This section is the **complete ledger** of honesty/integrity findings from the post-convergence brutal audit. Strategic tracks A–F alone did **not** cover these; **Track I** owns close-out. **Do not delete a row until its Done criteria are met and scorecard is updated.**

| ID | Finding | Evidence / resolution | Severity | Done when | Owner |
| :---: | :--- | :--- | :---: | :--- | :---: |
| **I1** | **Compiler CI is red under its own policy** | **Done:** `cargo clippy --all-targets -- -D warnings` green. Historical unwrap/expect/panic allow-listed in `Cargo.toml` with comment (not silent weaken) | **Done** | Clippy green under CI flags | I1 |
| **I2** | **Uncommitted mega-diff / process risk** | **Done:** convergence + integrity baseline committed | **Done** | Recoverable baseline | I2 |
| **I3** | **CLI theater: `arx spatial`** | **Done:** Query/Transform/Validate wire real ops; Grid/Relate hard-error (no fake ✅) | **Done** | No fake success | I3 |
| **I4** | **Public unvalidated save bypass** | **Done:** `save_building_at` validates; `save_building_unchecked` for post-gate writers | **Done** | Production paths gated | I4 |
| **I5** | **`BuildingData` residual dual** | **Done:** spatial ops take `core::Building` only | **Done** | DTO ser/de only | I5 |
| **I6** | **`arx init` weak template** | **Done:** init generates UUID + Ground Floor via validated save | **Done** | Init validates clean | I6 |
| **I7** | **`arx interactive` / render3d stubs** | **Done (doc):** §9.2 + pilot-runbook non-surface; feature-gated | **Done** | Documented | I7 |
| **I8** | **`export --delta` placeholder** | **Done:** `--delta` hard-errors (no silent ignore) | **Done** | No silent ignore | I8 |
| **I9** | **Hardware / MQTT / BACnet stubs** | **Done (doc):** §9.3 + pilot-runbook non-MVP; do not expand | **Done** | Documented quarantine | I9 |
| **I10** | **`arx migrate` chdir footgun** | **Done:** `persist_building_at`; migrate path-aware | **Done** | No cwd mutation | I10 |
| **I11** | **Multi-building single-file limit** | **Done (doc):** §3.3 + `docs/pilot-runbook.md` | **Done** | Documented | I11 |
| **I12** | **Optional-ring cognitive load** | **Open process:** refuse list + feature gates | **Low** | Hold freeze | I12 |
| **I13** | **Scorecard honesty** | **Ongoing** biweekly reconcile | **Process** | Keep honest | I13 |

**Integrity exit rule:** Pilot gate (§7.4) **cannot go** while any **Blocker** row (I1–I4) is open. **I1–I4 closed 2026-07.**

If this ledger conflicts with an optimistic sentence elsewhere in the document, **this table wins** until the row is closed.

---

## 3. System design

### 3.1 Principles

1. **One canonical model.** `Building` in memory is the only source of truth for application logic.
2. **Adapters at the edge.** IFC, LiDAR, text, WASM are projections/sources—not parallel databases.
3. **YAML is durable SSOT for Git.** Single file: `building.yaml`. IFC is interchange; envelope JSON is portable cache.
4. **Loss is explicit.** Never silently drop identity, enrichment, or structure without a report.
5. **Fidelity is tiered.** Round-trips are semantic, not byte-identical.
6. **MVP before network.** Compiler correctness before oracle/token.
7. **Hard validation on durable writes.** Production mutators refuse to write when `validation.has_errors()`. Serialize-only public saves are **integrity debt (I4)**, not an accepted dual path.
8. **Honest CLI.** Exit success only when the command did real work or correctly reported a no-op with no false claims (I3).

### 3.2 Canonical data model

#### Hierarchy

```text
Building
  ├── id, name, path, ifc_global_id?, metadata?, coordinate_systems
  └── floors[]
        ├── id, name, level, equipment[]   # common areas
        └── wings[]
              ├── name, equipment[]
              └── rooms[]
                    ├── id, name, room_type, spatial_properties
                    ├── properties
                    ├── lidar_enrichment?
                    ├── ifc_global_id?
                    └── equipment[]
                          ├── id, name, equipment_type, position
                          ├── address?   # durable ArxAddress (7-part path)
                          ├── path?      # legacy string; prefer address
                          ├── properties, lidar_enrichment?, ifc_global_id?
```

#### Identity

| ID | Storage | Role |
| :--- | :--- | :--- |
| Arx `id` (UUID string) | Always | Merge key inside Arx; YAML primary key |
| `ifc_global_id` | Optional | Stable IFC product GlobalId (22-char compressed) |
| `ArxAddress.path` | Optional on equipment; durable when set | Hierarchical ops query / migrate |

Rules (implemented; must remain):

- Import GlobalId → `ifc_global_id`; restore Arx id from `Pset_ArxIdentity:ArxId` when present.
- Export: reuse `ifc_global_id` or derive deterministically from Arx UUID.
- Never treat STEP express ids (`#42`) as durable identity.
- Address format: `/country/state/city/building/floor/room/fixture` (14 reserved system names for room segment when used).

#### LiDAR enrichment (typed)

```text
LidarEnrichment {
  point_count, confidence_score, last_scan_timestamp?, classification_heuristic?
}
```

Mapped to IFC as `Pset_ArxLidarEnrichment`.

#### Geometry contract (L2)

- Coordinate system: `building_local`, meters (primary).
- Room position: footprint center X/Y, volume bottom Z.
- Equipment: position; optional mesh.
- Compare with `GEOMETRY_EPSILON` (1e-3 m).

### 3.3 Persistence formats

| Format | Role | Schema versioning |
| :--- | :--- | :--- |
| **`building.yaml`** | Durable Git SSOT (**one building per repo root** — multi-building campus is **not** a durable layout; I11) | **`schema_version: 1`** on document (`BuildingData`; A1 done) |
| **BuildingSyncEnvelope JSON** | PWA/agent portable cache | `schema_version: 1` (`src/ingest/sync.rs`) |
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

All production mutators terminate here:

```text
source adapter or in-memory edit
    → Building
    → optional merge_building_with_policy(existing, incoming, policy)
    → validate_building
    → if errors: refuse durable write
    → LossReport / BuildingValidationReport (printed)
    → serialize building.yaml
    → optional Git (BuildingGitManager)
```

Key entry points:

| API | Path | Use |
| :--- | :--- | :--- |
| `finalize_ingest` | `src/ingest/import.rs` | Core completion (merge + validate + report) |
| `persist_building` | `src/ingest/mod.rs` | Mutators: finalize Text source + hard gate + save |
| `import_ifc_path` / `import_lidar_path` | `src/ingest/import.rs` | File adapters |
| `ingest_text_script` | `src/ingest/mod.rs` | Text/AR scripts |
| `load_building_at` | `src/persistence/` | Disk SSOT load (read path) |
| `save_building_at` / `save_building_data` | `src/persistence/` | Disk SSOT write — **serialize only today** (Track **I4**: must not remain a silent bypass for production writers) |
| `BuildingGitManager` | `src/git/` | Version control only |

**Write-path contract (target after I4):** CLI, agent, TUI, and room/equipment ops must not call serialize-only saves for “approved” durable state. Tests may use unchecked helpers if clearly named.

#### Merge policies

| Policy | Hierarchy base | Match | Use |
| :--- | :--- | :--- | :--- |
| `MergePolicy::ifc()` | **Incoming** | GlobalId → Arx id → path | Full IFC re-import |
| `MergePolicy::lidar()` | **Existing** | + spatial radius (room ~2 m, equip ~1.5 m + type) | Re-scan incremental |

**Product rule:** IFC re-import may omit existing entities not present in the file (counted as warnings). LiDAR re-scan keeps unmatched existing.

### 3.5 IFC fidelity contract

| Tier | Content | Status |
| :--- | :--- | :--- |
| L0 | Hierarchy, names, types, stable product IDs | Done |
| L1 | LiDAR enrichment Psets, Arx free-form Psets | Done |
| L1b | Clean property keys (no double prefix) | Done |
| L2 | Position/dims/mesh subset | Done (box + placement strong) |
| Ops | Merge + loss reports | Done |
| L3+ | Materials, openings, systems, vendor edge cases | **Limited / planned** |

Detail: `docs/ifc-mapping.md`.

### 3.6 Field roles (MVP operational design)

Do **not** require full campus LiDAR inside the phone browser.

| Role | Device | Responsibilities |
| :--- | :--- | :--- |
| **Capture node** | Laptop / Mini / Pi with storage | Run LiDAR pipeline; write YAML; Git commit |
| **Review tablet (PWA)** | Browser WASM | Import IFC, view model, apply text corrections, show reports |
| **BIM exchange** | CLI or agent | Export IFC for facilities / consultants |
| **Agent (optional)** | Always-on edge | IFC import/export + git RPC today; fuller sync later |

MVP field loop (implemented CLI):

```text
1. Capture node: arx import lidar scan.ply --merge
2. Human: arx edit corrections.txt
3. Optional: arx migrate   # backfill missing addresses
4. Capture node: arx export --format ifc -o building.ifc
5. Review: arx validate; arx query "/…/…"
6. arx stage && arx commit -m "approved model"
```

### 3.7 Technology stack (locked for MVP)

| Layer | Choice | Notes |
| :--- | :--- | :--- |
| Language | Rust 2021 | Single crate: lib `arxos` + bin `arx` |
| Persistence | YAML + Git | `building.yaml`, `git2`, `BuildingGitManager` |
| IFC | Native STEP only | Legacy `ifc_rs` path **removed** |
| LiDAR | PLY/LAS/XYZ + voxel filter | |
| Web | Leptos/WASM (optional `web`) | Review UI, not full capture |
| Validation | In-process rules | Hard-gated on **`persist_building` path**; full surface still open (I4) |
| Token/contracts | Solidity/Foundry under `contracts/` | **Phase Network only** |
| CI | `compiler-ci.yml` | Intended authoritative PR gate (default features); **must be green** (I1 open until clippy clean) |

### 3.8 Feature gates

| Feature | Default | Role |
| :--- | :---: | :--- |
| `tui` | **yes** | Terminal UI rings (spreadsheet, merge tool, palette) |
| `render3d` | no | Bevy / interactive visualization |
| `agent` | no | WebSocket/SSH edge agent |
| `web` | no | WASM PWA |
| `blockchain` | no | ethers clients |
| `full` | no | All of the above |

### 3.9 Target hardware (benchmarks, not blockers)

| Profile | Role | MVP expectation |
| :--- | :--- | :--- |
| Raspberry Pi 4B | Edge agent / light LiDAR | Documented max points; may require aggressive voxel |
| OptiPlex / Mac Mini | Heavy parse + IFC | Primary capture node for pilot |
| Tablet browser | Review only | No full-cloud process in WASM for pilot |

### 3.10 Economy: Oracle / $AXD / access (implemented in lab)

```text
Compiler produces verified Building SSOT
        → contribution package (merkle + quality + building UUID)
        → worker EIP-712 proof → oracles 2-of-3 → finalize → mint $AXD
        → buyers pay $AXD via PaymentRouter for data access
```

| Path | Split (lab) |
| :--- | :--- |
| **Mint (labor)** | 70% worker · 10% building · 10% maintainers · 10% treasury (quality-scaled) |
| **Access payment** | 70% building · 10% maintainers · 20% treasury (remainder) |

**Rules:**

- Software remains free; chain rewards **verified building data**, not CLI licenses.
- Multi-oracle consensus requires the **same** proof (hash locked on first propose).
- Live ops still need N7 (host gate) + N8 (deploy env). Contracts must not regress G1–G8.

---

## 4. Implementation plan (remaining work)

### 4.0 Program operating rules (senior chief)

The architecture fight is **over**. Remaining work is **integrity honesty, trust packaging, and pilot usability**—not another rewrite of dual models, dual IFC stacks, or a kitchen-sink CLI.

#### North star

A capture node can run:

```text
import (IFC|LiDAR) → edit/migrate → validate → query → export IFC → git commit
```

…with **one** `Building`, **one** `building.yaml`, **hard validation on write**, **no fake CLI success**, and **explicit loss reports**. Everything else is optional or Phase Network.

#### Guiding rules

1. **Spine is frozen.** No second persistence layout, no second IFC parser, no parallel Building DTO as a working model (close residual duals via Track **I5**).
2. **Integrity before packaging.** Close §2.6 blockers (I1–I4) before claiming pilot packaging complete.
3. **Pilot before polish.** Prefer runbook + fixtures over new product surfaces.
4. **One vertical slice per milestone.** Ship something a second engineer can run—not three half-done tracks.
5. **Optional rings stay gated.** Agent, web, render3d, blockchain, hardware do not block G1–G8.
6. **CI truth is `compiler-ci.yml` and it must be green.** Do not reintroduce multi-OS / `--all-features` / hard coverage thresholds as PR gates. Do not claim green while I1 is open.
7. **No CLI theater.** Commands either do the work, or fail loudly as unimplemented—never print success for no-ops.

#### Refuse list (do not accept in review)

| Refusal | Why |
| :--- | :--- |
| New multi-file building layout / “UniversalPath” experiments | Reopens dual durable SSOT (I11) |
| Second IFC library “for compatibility” | Reopens dual construction semantics |
| Expanding clap with economy / sensors / game / hardware before pilot | Scope creep; dilutes compiler (I9, I12) |
| Softening validation gates “for convenience” | Bad data becomes durable truth (I4) |
| New public serialize-only save used by CLI/agent | Silent validation bypass (I4) |
| PR CI that reintroduces multi-OS matrix + hard coverage as blockers | Slows convergence; not pilot-critical |
| Fake success / ✅ for unimplemented subcommands | Lies to operators (I3, I7, I8) |
| “CI is green” / pilot-ready marketing while §2.6 blockers open | Process dishonesty (I13) |
| Expanding process cwd chdir patterns for path selection | Fragility (I10) |

#### PR checklist (spine + integrity)

Every PR that mutates durable Building state must answer **yes**:

- [ ] Load path uses `building.yaml` / `load_building_at` (or equivalent PersistenceManager API)?
- [ ] Write path goes through `persist_building` or `import_*_path` / `ingest_text_script` (not raw serialize-only for production paths)?
- [ ] Validation errors refuse write (`has_errors()` hard gate)?
- [ ] No new dual authority (second loader, second merge engine, second layout, new `BuildingData` working API)?
- [ ] No new CLI theater (success implies real work or explicit non-zero unimplemented)?
- [ ] `compiler-ci` / spine tests still meaningful for the change?
- [ ] If touching CI policy: clippy/test flags still match what maintainers run locally?

#### Cadence

| Cadence | Practice |
| :--- | :--- |
| **Weekly** | One vertical deliverable (integrity close-out, fixture, schema field, runbook section)—not five parallel refactors |
| **Every PR** | Spine + integrity checklist above; Compiler CI green (or PR is the I1 fix) |
| **Biweekly** | Reconcile G1–G8 **and** §2.6 integrity rows + §2.1 scorecard in this manifest (one PR) |

#### Critical path (do not reorder casually)

```text
     Track I (integrity blockers I1–I4) ──────────┐
              \                                    │
     Track A (schema) ───────────────────────────┤
              \                                    │
               Track B (vendor IFC) ───────────────┼──► Track D (runbook/package) ──► Pilot gate
              /                                    │
     Track C (LiDAR review) ──────────────────────┘
                                                   Track E (PWA) optional alongside D
                                                   Track F (network) blocked until pilot learnings
                                                   Track I residual (I5–I12) parallel / before gate as marked
```

**Critical path to pilot:** **I (blockers)** → A → B → D, with **C required** for any LiDAR-heavy site.  
**PWA (E)** is optional if tablet is not in pilot scope.  
**Network (F)** has no calendar commitment until the compiler has been used on real buildings.

#### Trust pipeline (one-line program)

```text
Stop lying (CI/CLI/save)  →  Version the contract  →  Prove interop  →  Make LiDAR reviewable  →  Package for a second team
```

Success is measured by **pilot gate criteria** (§7.4), **§2.6 blockers closed**, and **Compiler CI green**—not by LOC, feature count, or optional rings.

### 4.1 Phase overview (maps to tracks I, A–F)

| Phase | Track | Name | Outcome | Status |
| :---: | :---: | :--- | :--- | :---: |
| **−1** | **I** | Integrity honesty | CI green; no CLI theater; no silent save bypass; committed baseline | **Done** (I1–I11; I12 process hold) |
| **0** | **A** | Contract freeze & hygiene | Clear supported surface; schema versions | **Done** (A1 schema_version) |
| **1** | — | Single spine enforcement | Every write through finalize/validate | **Partial** — production mutators **Done**; public save APIs still open (I4) |
| **2** | **B** | Golden fixtures & CI gates | Spine CI + IFC/LiDAR goldens | **Partial** (vendor_ifc_test + limitations; Revit/ArchiCAD slots open) |
| **3** | **C** | LiDAR pilot quality | Human review workflow + known limits | **Partial** (C1/C2/C3 code+docs; field profile open) |
| **4** | **D** | Field ops packaging | Pilot runbook; capture node packaging | **Partial** (runbook+install outline; walkthrough open) |
| **5** | **E** | PWA review productization | Envelope-first UI polish | **Open** (optional if no tablet pilot) |
| **6** | **B/F** | IFC L3 / vendor expansion | Interop matrix | **Open** |
| **7** | **F** | Network (Oracle / token) | DePIN on trusted compiler | **Deferred** |

#### Program tracks (execution labels)

| Track | Maps to | Focus | Owner skill |
| :---: | :--- | :--- | :--- |
| **I** | Phase −1 | Clippy/CI green, commit baseline, CLI honesty, save gates, residual duals, init template, stubs | Rust systems + lead |
| **A** | Phase 0 residual | `schema_version`, surface freeze, PR checklist | Rust systems |
| **B** | Phase 2 residual (+ 6) | Vendor IFC fixtures, non-panic goldens, limitations table | BIM/interop + Rust |
| **C** | Phase 3 | Review status, export policy, confidence honesty, failure modes | Rust + domain reviewer |
| **D** | Phase 4 | Pilot runbook, install path, resource bounds, sample project (includes I11 limit docs) | Edge/DevOps + lead |
| **E** | Phase 5 | Tablet review UI only (no LiDAR-in-WASM) | Light frontend |
| **F** | Phase 7 | Network/token — **frozen** until after pilot | Protocol (later) |

### 4.1.1 Track I — integrity honesty (before packaging claims)

**Why zeroeth:** A green scorecard and pilot runbook are worthless if Compiler CI fails, CLI lies, or unvalidated YAML can be written. Full inventory: **§2.6**.

| ID | Task | Severity | Done when |
| :--- | :--- | :---: | :--- |
| **I1** | Make Compiler CI match reality: fix clippy `unwrap_used` (and related) until `cargo clippy --all-targets -- -D warnings` is green **or** adopt a documented, minimal allow-list that still keeps a hard PR gate | Blocker | Same command as `compiler-ci.yml` passes on default features |
| **I2** | Land convergence work: ordered commit series (or written recovery branch procedure); leave a clean baseline | Blocker | Working tree is a known commit sequence; handoff can bisect |
| **I3** | Kill `arx spatial` theater: implement or hard-error unimplemented; **no** ✅ on no-op Relate/Transform/Validate | Blocker | CLI tests or manual: success implies real work; stubs exit non-zero |
| **I4** | Close unvalidated public save: route production writes through validate+hard-fail; rename/restrict `save_building_data` / `save_building_at` if kept for tests | Blocker | Grep: no CLI/agent/TUI path saves without gate; docs match |
| **I5** | Eliminate `BuildingData` from `core::operations::spatial` (and tests); ops take `Building` | High | DTO only in `yaml.rs` ser/de path |
| **I6** | Fix `arx init` / `templates/building.yaml`: non-empty id (generate UUID), usable floors or explicit empty-project contract + post-init validate | High | Init → validate is a supported cold-start story |
| **I7** | Label `interactive` / render3d as experimental non-pilot; fail clearly when feature off; no implied pilot support in README/CLI map | Med | §9.2 + help text honest |
| **I8** | `export --delta`: remove unused flag **or** implement+test; until then error if `--delta` set | Med | No silent ignore of delta flag |
| **I9** | Hardware / MQTT / BACnet / simulated peripheral: document non-MVP; do not expand; gate or quarantine from compiler help | Med | §9.3 + refuse list; no new hardware CLI surface pre-pilot |
| **I10** | Remove migrate `set_current_dir` footgun: path-aware `persist_building` / save API | Med | migrate works with `--path` without changing process cwd |
| **I11** | Document single-building / single-file SSOT as hard pilot limit (runbook + this manifest) | Low | Written; no multi-building layout experiments pre-gate |
| **I12** | Hold optional-ring surface freeze (TUI/agent/render3d/chain cognitive load) | Low | PR checklist refuses new rings |
| **I13** | Biweekly scorecard honesty pass (§2.1 + §2.6) | Process | Manifest not re-inflated while blockers open |

**Ordering hint:** I2 early (so work is recoverable) → I1 + I3 + I4 in parallel → I5/I6 → I7–I12 as capacity allows before pilot gate.

### 4.2 Track A / Phase 0 residual — schema freeze (1–2 weeks)

**Why after integrity blockers (or overlapping I1):** Without a versioned YAML document, every later fixture and handoff is fragile. Do not claim A complete while I1/I4 still allow false confidence.

| ID | Task | Done when |
| :--- | :--- | :--- |
| 0.1 / **A1** | Add `schema_version` to Building YAML document (default `1`) | **Done** — old YAML loads; new writes emit version; tests green |
| 0.2 / **A2** | Supported-surfaces doc: short `docs/supported-surfaces.md` **or** this manifest §9.3 + README as linked SSOT | Linked from README |
| 0.3 | ~~Native-only IFC~~ | **Done** — legacy removed |
| 0.4 | ~~Slim CLI to MVP~~ | **Done** — compiler surface + honesty (I3/I8) |
| 0.5 | ~~Remove dual authorities~~ | **Done** — I4/I5 closed |
| **A3** | Freeze surface policy in review (PR checklist §4.0) | Enforced in code review |

**Risk if skipped:** Silent schema drift during pilot.

### 4.3 Phase 1 residual — spine (mostly complete; integrity residuals)

| ID | Task | Status |
| :--- | :--- | :---: |
| 1.1 | Route production writers through finalize / `persist_building` | **Done** (room/equipment/edit/migrate path) |
| 1.2 | Hard-fail durable write when `validation.has_errors()` | **Done** on `persist_building` and public `save_building_at` |
| 1.3 | Print `summary_lines()` on import/export/edit | **Done** (import/edit) |
| 1.4 | Agent IFC via ingest | **Done** |
| 1.5 | Centralize YAML path (`building.yaml`) | **Done** |
| 1.6 | Close serialize-only public save bypass | **Open** → Track **I4** |
| 1.7 | No CLI fake-success for unfinished commands | **Open** → Track **I3** |

### 4.4 Track B / Phase 2 residual — goldens & CI (2–4 weeks; parallelizable with A tail)

**Why second:** G3 is strong for Arx-shaped data; G8 is done; **vendor IFC is still the hole**.

| ID | Task | Status |
| :--- | :--- | :---: |
| 2.1 / **B1** | Vendor IFC fixtures (≥2 anonymized) + license notes under `tests/fixtures/ifc/vendor/` or `test_data/vendor/` | **Partial** — SketchUp/HVAC samples in CI; Revit/ArchiCAD slots open |
| 2.2 / **B2** | Golden: vendor IFC → model → IFC → model (no panic; structure counts); add to Compiler CI | **Done** (`tests/vendor_ifc_test.rs` in Compiler CI) |
| 2.3 | Arx-authored IFC identity/enrichment/geometry tests | **Done** |
| 2.4 | LiDAR synthetic → merge rescan | **Done** (`lidar_tests`) |
| 2.5 | Compiler spine integration tests | **Done** (`compiler_spine_test`, `ifc_compiler_path_test`) |
| 2.6 | Authoritative CI workflow | **Done** (`compiler-ci.yml`) |
| 2.7 | Soften/retire bloated multi-OS / tarpaulin PR gates | **Done** |
| **B3** | Per-fixture limitations table (what we preserve / drop) | **Done** (`docs/ifc-limitations.md`) |

**Do not:** Revive `ifc_rs` for “just one more vendor file.” Fix native path or document unsupported.

### 4.5 Track C / Phase 3 — LiDAR pilot quality (3–5 weeks)

**Why third:** Synthetic pipeline is CI-green; pilot risk is **false structure trusted as truth**. LiDAR is assistive, not survey truth.

| ID | Task | Done when |
| :--- | :--- | :--- |
| 3.1 / **C3** | Confidence scores: feature-based or documented non-probabilistic (no fake precision) | **Done** (`docs/lidar-confidence.md` + detector comments) |
| 3.2 / **C1** | Review state: `proposed` / `accepted` / `rejected` via text DSL or properties | **Done** (`review_status` + LiDAR marks proposed; `arx edit`) |
| 3.3 / **C2** | Export warning by default; optional `--approved-only` (or equivalent) | **Done** (`arx export --approved-only` + export warnings) |
| 3.4 / **C4** | Profile detector on pilot sample; document failure modes (missed floors, split rooms, noise) | Runbook section |
| 3.5 | Ensure enrichment not dual-stored (typed field is SSOT) | Grep clean |

**Success metric:** Pilot team can reject bad auto-rooms **before** IFC leaves the site.

### 4.6 Track D / Phase 4 — Field ops packaging (2–3 weeks; after A+B, overlaps C)

**Why fourth:** A second team must cold-start without reverse-engineering the repo.

| ID | Task | Done when |
| :--- | :--- | :--- |
| 4.1 / **D1** | `docs/pilot-runbook.md` (hardware, voxel defaults, light mode, full CLI loop, git, **single-building limit I11**, known stubs) | **Partial** — written; non-author walkthrough open |
| 4.2 / **D2** | Release binary path: documented `cargo install` / release artifact; optional Dockerfile | **Partial** — `docs/install.md` |
| 4.3 / **D3** | Resource limits: max points, voxel defaults, light mode (Pi vs Mini) | Written + smoke profile once |
| 4.4 / **D4** | Sample pilot project: `arx init` + example edit script + sample IFC path | **Partial** — `examples/pilot-corrections.txt` + fixtures |
| 4.5 | Structured ingest summary logs | Operators can debug |
| **D5** | Document pilot **non-surfaces**: `spatial` (until I3), `interactive`/3D, hardware, `--delta`, multi-building | Operators not misled |

**Success metric:** Cold-start sample workflow in **&lt; 1 day**.

### 4.7 Track E / Phase 5 — PWA review productization (optional; after D starts)

**Why last among MVP tracks:** Tablet is **review/correct**, not capture. **Skip Track E** if tablet is not in pilot scope.

| ID | Task | Done when |
| :--- | :--- | :--- |
| 5.1 / **E1** | Report panel for loss/validation on import | UX usable |
| 5.2 / **E2** | Text edit UI → `apply_text_script_json` | Works offline |
| 5.3 / **E3** | Envelope-only active storage + download JSON for capture node | No dual-key bugs; file export |
| 5.4 | Download YAML/JSON for handoff to capture node | File export |
| 5.5 / **E4** | Do **not** port full LiDAR to WASM | Explicit non-goal |

Cap scope ruthlessly.

### 4.8 Phase 6 — IFC vendor expansion

| ID | Task | Done when |
| :--- | :--- | :--- |
| 6.1 | Matrix: Revit / ArchiCAD / FreeCAD × preserved fields | Doc table |
| 6.2 | Placement/units for common vendor quirks | Fixture tests |
| 6.3 | Mesh round-trip quality tests | Known epsilon |
| 6.4 | ~~Deprecate legacy parser~~ | **Done** |

### 4.9 Track F / Economy layer (active — lab done; live open)

Contracts under `contracts/`; Rust under `src/contribution`, `src/access`, `src/blockchain` (feature-gated).

| ID | Task | Status |
| :--- | :--- | :---: |
| F1 / N1 | Building commitment package | **Done** |
| F2 / N2 | EIP-712 from package | **Done** |
| F3 / N3 | Oracle propose + finalize mint E2E | **Done** (Foundry) |
| F4 / N4 | Registry building UUID + worker | **Done** (Foundry) |
| F5 / N5 | Buyer payForAccess | **Done** (Foundry + CLI) |
| F6 / N8 | Deploy-and-env script → `.env.arx` + register helpers | **Open** (Horizon A) |
| F7 / N7 | Host gate: only release data after `AccessPaid` | **Open** (Horizon A) |
| F8 | Public testnet + external oracles | **Open** (Horizon C) |
| F9 | Threat model / audit before mainnet | **Open** (Horizon C) |

---

## 5. Detailed design: critical subsystems

### 5.1 IFC adapter

**Import:** STEP → native lexer/registry/resolver → mapping (identity, lidar, properties, geometry) → Building + LossReport → finalize.

**Export:** Building → assign/reuse GlobalIds → products + Psets → STEP.

**Must not regress:**

- Product GlobalId stability across double export.
- `Pset_ArxIdentity`, `Pset_ArxLidarEnrichment`.
- Clean free-form keys on domain bags.

**Files:** `src/ifc/parser/*`, `src/ifc/mapping/*`, `src/export/ifc.rs`.  
**Removed:** `bim_parser`, `ifc_rs_converter`, `ifc_rs` dependency.

### 5.2 LiDAR adapter

**Path:** file → stream points → voxel filter → floor/room/equipment detect → enrichment → Building → `MergePolicy::lidar()` via mapping merge.

**Files:** `src/spatial/lidar/*` (parser, downsampler, detector).  
**Removed:** standalone `ModelMerger` wrapper (call mapping merge directly).

### 5.3 Text / AR adapter

**Path:** DSL script → `apply_text_script` → `ingest_text_script` → finalize + validate → write.

**CLI:** `arx edit`, `arx import text`.

AR devices should emit this DSL—not free-form NL—in MVP.

### 5.4 Sync / PWA

**Path:** Building → `BuildingSyncEnvelope` → localStorage / file.

**WASM:** parse IFC envelope, store/load, merge, apply text (`src/web/wasm_bridge.rs`).

### 5.5 Validation + durable write

**Invariants (current):** non-empty names/ids where required; unique room/equipment ids; dimension/bbox sanity; LiDAR confidence in \[0, 1\]; property key hygiene.

**Hard gate (implemented on preferred path):** `persist_building` and import/edit/agent writers that use it refuse write when `has_errors()`.

**Known hole (Track I4):** `PersistenceManager::save_building_data` and free `save_building_at` still write YAML **without** validation. Prefer fixing those APIs over documenting the bypass forever.

### 5.6 Addressing

**Type:** `core::domain::ArxAddress` (7-part path, reserved systems, SHA-256 guid helper, `matches_glob`).

**Durable:** equipment.address serializes in YAML.

**Ops:**

- `arx query "/…/*…"` — glob match on durable addresses.
- `arx migrate` — backfill missing addresses from hierarchy (`core::operations::address::backfill_equipment_addresses`).

### 5.7 Git

**Role:** version `building.yaml` (and related project files)—not a second model layout.

**API:** `BuildingGitManager` for stage/commit/diff/history/export-to-repo (single-file export).

---

## 6. Testing strategy

| Layer | What | Where |
| :--- | :--- | :--- |
| Unit | Identity, Psets, merge policies, address globs, text parse, validation | `src/**` `#[cfg(test)]` |
| Spine integration | Seed → backfill → persist → query → IFC export | `tests/compiler_spine_test.rs` |
| IFC golden path | Sample fixture → SSOT → validate → export → re-import | `tests/ifc_compiler_path_test.rs` |
| Bidirectional | Building ↔ IFC semantic round-trip | `tests/bidirectional_tests.rs` |
| LiDAR | Pipeline + lidar merge policy | `tests/lidar_tests.rs` |
| Native IFC | Geometry, strict mode, export Psets | `tests/ifc_native_tests.rs` |
| Security / config / property | Path safety, config, proptest | top-level `tests/*.rs` |
| Fixtures | Minimal IFC + golden samples | `tests/fixtures/`, `test_data/` |
| Vendor IFC | Anonymized Revit/ArchiCAD | **Phase 2 residual** |

**Rule:** No claim of “round-trip works” without a named test or fixture.

**CI:** `.github/workflows/compiler-ci.yml` is the authoritative PR gate (default features): `fmt` + **clippy `-D warnings`** + spine tests + full default suite. Extended multi-OS / hard coverage workflows are optional/scheduled only.

**Honesty note:** As of the brutal audit, **clippy fails** (~400 `unwrap_used` in lib tests under deny-warnings). Track **I1** must close before any “CI green” claim.

---

## 7. Delivery plan for an external team

### 7.1 Recommended team shape (pilot)

| Role | Allocation | Focus |
| :--- | :--- | :--- |
| Rust lead (+ optional second) | Core | **Track I first**, then A, spine regressions, Track C, half of B |
| BIM/interop | 1, part-time OK | Track B fixtures + limitations table |
| Ops | 1, part-time | Track D runbook + packaging (incl. I11/D5 honesty) |
| Frontend | 0–1 | Track E only if tablet is in pilot scope |
| Protocol | Later | Track F only after pilot |

### 7.1.1 Solo-engineer reorder

If staffing is **one person**, do **not** try full parallel tracks. Order:

```text
I2 (commit/recovery baseline) → I1 (clippy/CI) + I3 (spatial honesty) + I4 (save gate)
  → I5/I6 as needed → A1 (schema) → B1–B2 (first vendor fixture + CI)
  → D1 (runbook outline/content) → C2 (export warning only) → C1 (review status) → rest of C/D
```

Defer **E** (PWA) and full detector scoring until after pilot gate or a second person joins.

### 7.2 Milestone timeline (indicative, post-convergence)

| Milestone | Track | Focus | Delivers |
| :--- | :---: | :--- | :--- |
| **M−1** | **I** | Integrity blockers I1–I4 (+ I5/I6 preferred) | Honest CI/CLI/save baseline |
| M0 residual | A | `schema_version` + supported-surfaces | Frozen YAML contract |
| M2 residual | B | Vendor IFC fixtures + CI | Interop confidence |
| M3 | C | LiDAR review quality | Human-in-the-loop pilot structure |
| M4 | D | Pilot packaging | Runbook + install + non-surface honesty |
| M5 | E | PWA review (optional) | Tablet correct-and-handoff |
| **MVP pilot-ready** | **I** + A–D (+C) | G1–G8 with human review + integrity closed | Field trial go/no-go |
| Network | F | After pilot learnings | Phase 7 |

### 7.2.1 Ninety-day sketch (order-of-magnitude)

Adjust calendar; **do not** claim vendor/interop success while CI is red (I1), or ship packaging before integrity blockers close.

| Weeks | Focus | Outcome |
| :---: | :--- | :--- |
| 0–2 | Track **I** (I1–I4, I2 first) | CI green; no CLI theater; save gate; committed baseline |
| 1–3 | Track A (+ I5/I6) | Versioned YAML contract; honest init |
| 2–5 | Track B | Vendor fixtures in CI |
| 4–8 | Track C | Review/export policy |
| 7–10 | Track D | Runbook + install + D5 non-surfaces |
| 9–12 | Track E (if needed) | Tablet review slice |
| 12 | Pilot gate review | Go / no-go on field trial (§7.4) |

### 7.3 Handoff package checklist

- [x] This manifest (`arxos_manifest.md`) — reconciled 2026-07; operating rules §4.0; **§2.6 integrity debt inventory**
- [x] `docs/ifc-mapping.md` (existing)
- [x] README aligned to compiler CLI + CI table
- [x] **Compiler CI actually green** under documented flags (Track **I1**)
- [x] Experimental modules feature-gated (agent, chain, render3d, web)
- [x] Convergence work committed / recoverable (Track **I2**)
- [x] No CLI fake-success on unfinished commands (Track **I3**)
- [x] No public unvalidated durable save for production paths (Track **I4**)
- [x] `BuildingData` residual dual closed (Track **I5**)
- [x] Honest `arx init` template (Track **I6**)
- [x] Stubs labeled: interactive/3D, `--delta`, hardware (Tracks **I7–I9**)
- [x] Migrate path-safe (Track **I10**)
- [x] Single-building limit documented (Track **I11** / D5)
- [x] `schema_version` on YAML Building (Track A1)
- [ ] Vendor IFC limitations table (Track B)
- [x] `docs/pilot-runbook.md` outline (Track D1 partial — needs non-author walkthrough)

### 7.4 Pilot gate — definition of “remaining items complete”

Field pilot readiness target is **~7/10**, not 10/10. Pilot is **learning**, not certification.

All of the following must be true:

0. **Integrity blockers:** §2.6 rows **I1–I4** closed (CI green under policy; committed baseline; no spatial theater; no unvalidated production save). Prefer **I5–I6** closed; **I7–I11** documented if not fully coded.
1. ~~**G2 residual:** `schema_version` on new YAML~~ **Done (A1)**; bump policy: increment `BUILDING_YAML_SCHEMA_VERSION` on breaking doc changes.
2. **G4 residual:** At least one real-ish scan path profiled; limits written.
3. **G6 residual:** Auto entities can be rejected/accepted before approved IFC (or export clearly warns).
4. **G7:** Pilot runbook + install path exists; walked by a non-author; includes D5 non-surfaces and I11 limit.
5. **Vendor IFC:** ≥2 fixtures in CI; no panics; limitations listed.
6. **G1–G5, G8:** Remain green on Compiler CI (no spine regressions) — **includes clippy gate as written in `compiler-ci.yml`**.

**Go:** Proceed to field trial with named site and capture-node owner.  
**No-go:** Any of **I1–I4**, A1, B1–B2, D1, or C2 missing; or Compiler CI red (tests **or** clippy as configured).

### 7.5 What leadership will refuse

See §4.0 refuse list. Additionally:

- Scheduling Track F (token/oracle) as a pilot dependency.
- Claiming “round-trip works” without a named test or fixture (§6).
- Expanding production CLI surface before pilot gate without updating §9.2.
- Claiming pilot readiness while any §2.6 **Blocker** is open.
- Shipping `arx spatial` (or similar) success banners without real work.

---

## 8. Risk register

| Risk | Severity | Mitigation |
| :--- | :---: | :--- |
| **Compiler CI red / clippy debt blocks merge** (I1) | **High** | Track I1; do not weaken deny-warnings without documented allow-list |
| **Uncommitted mega-diff / lost work** (I2) | **High** | Ordered commits; recovery procedure; never accumulate another silent rewrite |
| **CLI theater trains operators to trust lies** (I3) | **High** | Hard-error stubs; refuse list; D5 runbook |
| **Unvalidated YAML becomes SSOT** (I4) | **High** | Close public save bypass; PR checklist |
| Vendor IFC breaks native path | High | Phase 2 vendor fixtures; interop matrix |
| LiDAR false structure trusted | High | Human review status; edit before export |
| Scope creep (token, full CAD, full PWA scan, hardware) | High | Enforce phases; feature gates; slim CLI; refuse list §4.0; I9/I12 |
| Residual `BuildingData` dual confuses contributors (I5) | Medium | I5; keep DTO private to ser/de |
| Weak init template confuses cold-start (I6) | Medium | I6 + D4 sample project |
| Edge hardware insufficient | Medium | Light mode; capture-node class machine |
| Schema churn during handoff | Medium | Add `schema_version`; freeze windows |
| Migrate chdir races / wrong repo (I10) | Medium | Path-aware persist; no process cwd mutation |
| Multi-building expected but unsupported (I11) | Medium | Document single-file SSOT limit in runbook |
| Multi-user sync conflicts | Medium | Last-write-wins envelope until later |
| Agent token / PWA storage security | Medium | Security review before network exposure |
| CI drift (multiple workflows) | Medium | Compiler CI authoritative; others optional |
| Scorecard re-inflation (I13) | Medium | Biweekly reconcile §2.1 + §2.6 only with evidence |

---

## 9. Repository map

### 9.1 Implementation anchors

```text
src/core/              Canonical Building model + operations + ArxAddress
src/ingest/            finalize_ingest, persist_building, import_*, text, sync
src/ifc/               Native IFC parse + mapping (no legacy stack)
src/export/ifc.rs      IFC export
src/spatial/lidar/     Point cloud pipeline
src/validation/        Post-ingest validation
src/persistence/       building.yaml load/save
src/git/               BuildingGitManager (single-file SSOT)
src/yaml.rs            Serializer + BuildingData DTO (internal)
src/cli/               Compiler CLI surface
src/web/               PWA (optional feature)
src/agent/             Edge agent (optional feature)
src/tui/               Terminal UI rings (default feature)
src/render3d/          Visualization (optional feature)
src/blockchain/        Chain clients (optional feature)
contracts/             Token/oracle (Phase 7)
tests/*.rs             Integration targets only
tests/fixtures/        Golden samples
test_data/             Mid-size IFC samples
.github/workflows/compiler-ci.yml   Authoritative CI
```

### 9.2 CLI surface (`arx`)

| Command | Role | Status |
| :--- | :--- | :--- |
| `init` | Seed validated `building.yaml` (UUID + floor) | Production |
| `import ifc\|lidar\|text` | Adapters → finalize → SSOT | Production |
| `edit` | Text/AR script (incl. `review_status`) | Production |
| `export` | IFC/yaml/json; warn on proposed LiDAR; `--approved-only` | Production |
| `validate` / `migrate` / `query` | Trust + address tools | Production |
| `room` / `equipment` | CRUD via `persist_building` | Production |
| `contribute` | Building labor → `contribution.json` (+ `--sign`/`--submit` w/ blockchain) | Production (economy) |
| `access quote` / `access pay` | Buyer request + $AXD payForAccess | Production (economy) |
| Git: `status` / `stage` / `commit` / … | Version SSOT | Production |
| `spatial` | Query/transform/validate real; grid/relate hard-error | Partial |
| `render` / `interactive` | Visualization | Experimental (`render3d`) |
| `merge` / `dashboard` / `remote` | Optional rings | Feature-gated |

**Supported loops:**

```text
Compiler:  init → import → edit (review) → migrate → validate → export → git
Labor:     contribute [--sign] [--submit]
Buyer:     access quote → access pay  (hosts must honor AccessPaid — N7 open)
```

### 9.3 Supported surfaces matrix

| Surface | Production | Notes |
| :--- | :---: | :--- |
| CLI compiler spine | **Yes** | Free software |
| Contribute / access economy CLI | **Yes** | Chain calls need `blockchain` + live addresses |
| Native IFC | **Yes** | L0–L2; vendor matrix limited |
| LiDAR import | **Yes** | Synthetic proven; field TBD |
| Foundry contracts | **Yes** (lab) | Mint + pay E2E green |
| Host gate on payment | **Partial** | CLI `--commercial` + receipt (**R4** process; not server enforcement) |
| Multi-building layout | **No** | One `building.yaml` per repo (I11) |
| PWA / agent / 3D / hardware | Optional | Frozen until Horizon A–B unless approved |

---

## 10. Immediate next actions (start here)

**Goal:** One closed loop that is easy to run, then a real building.

### 10.1 Horizon A — Lab → live local

| Order | Work | Status |
| :---: | :--- | :---: |
| **A1** | `scripts/horizon_a_deploy_env.sh` → `.env.arx` | **Done** |
| **A2** | `Register.s.sol` + script `--register` (YAML UUID) | **Done** |
| **A3** | `docs/horizon-a-ops.md` mint/pay ops | **Done** |
| **A4** | Host gate: `export --commercial` + `access-receipt.json` | **Done** (R4 partial) |
| **A5** | `docs/field-trial.md` | **Done** |

Horizon A **does not** close §1.6 district pilot obligations. It only enables lab/live-local tooling.

### 10.2 Horizon B — Relegate pilot obligations (L1) — **current priority**

| Order | Package | Status | Your next action |
| :---: | :--- | :---: | :--- |
| **B0** | **P-Safety** | Template **done** | Fill/sign `docs/pilot-charter.md` |
| **B1** | **P-Transfer** | **Pin cut** | Field: record pin in charter; second person + `docs/second-person-checklist.md` on `v2.0.0-pilot.1` |
| **B2** | **P-Data** | Template done | Complete `docs/data-classification.md` + charter §4; private Git remote |
| **B3** | **P-Field-truth** | Template done | Fill `docs/field-truth-log.md` with real IFC/scan; eng fixes only blockers |
| **B4** | **P-Chain-optional** | Partial | Keep L1 off-chain unless leadership requests demo |
| **B5** | Scorecard | Open | After B0–B3 evidence, update §1.6 statuses |

**L1 exit:** R1,R2,R5,R7,R8,R9,R10 pilot-mitigated; free software loop valuable on one site; **no mainnet token dependency**.

**Field packet (ordered):** `docs/field-handoff.md`

### 10.3 Horizon C — Relegate L2/L3 obligations (only after L1)

| Order | Work | Obligations |
| :---: | :--- | :---: |
| **C1** | Server-side host gate on `AccessPaid` | R4 → Done |
| **C2** | Testnet/production oracle ops (2+ operators) | R3 |
| **C3** | Legal/Finance go for any token path | R8 |
| **C4** | Multi-building program + vendor matrix + scale | R2, R6 at program scale |

### 10.4 Next actions (field + eng)

```text
You:    docs/field-handoff.md — sign charter + data-classification · record pin · R5 checklist
        fill field-truth-log on real IFC/scan
Eng:    clean tree · ./scripts/l1_smoke.sh · pin_pilot_release.sh · fix field blockers only
Never:  L3 mainnet until L1 exit · fake R5/R1 evidence · public facility models
```

**Automated smoke (eng):** `./scripts/l1_smoke.sh` — does not close R5.

---

## 11. Document history

| Version | Notes |
| :--- | :--- |
| Pre-rewrite | Product manifesto (DePIN/compiler/oracle/token overview) |
| **2026-07 reconciliation** | Architecture convergence: single IFC, single YAML SSOT, hard write gate, slim CLI, Compiler CI |
| **2026-07 integrity** | Brutal audit ledger §2.6; Track I; honesty on CLI/CI/save |
| **2026-07 integrity + A1 + B/C** | Close-out I1–I11; schema_version; vendor goldens; review/export policy |
| **2026-07 full product N1–N5** | Vision locked; contribute → EIP-712 → mint E2E; access pay E2E; economy CLI |
| **2026-07-13 vision status rewrite** | Manifest primary goal = full product; scorecard lab vs field; horizons A–C; N7–N9; §10 = path to live closed loop |
| **2026-07-13 deployment obligations** | §1.6 R1–R10 reservation register + work packages + L0–L3 go levels; Horizon B = relegate pilot obligations |
| **2026-07-13 P-Safety + P-Transfer** | `pilot-charter`, `l1-supported-workflow`, `second-person-checklist`, `pilot-release`, `pin_pilot_release.sh`; R8–R10 partial |
| **2026-07-13 P-Data + P-Field templates + L1 smoke** | `data-classification.md`, `field-truth-log.md`, `scripts/l1_smoke.sh`; R7 partial |
| **2026-07-13 eng B1 closeout** | `contracts/out` gitignored; `docs/field-handoff.md`; pin path ready |
| **2026-07-13 pilot pin** | Annotated tag `v2.0.0-pilot.1` @ `ba33e6ba`; lib 514 + spine green; l1_smoke PASS |

---

## 12. Closing statement

ArxOS is **version control for the built world**: free software so peers can map as-built truth; peer review so the ledger is trustworthy; **$AXD** so labor is rewarded and buyers can pay for data.

**Lab status:** Compiler + economy spine (N1–N8 tooling) are **implemented and test-proven**.

**District / field status:** **Not** production-ready by default. Readiness is gated by **§1.6 obligations** (LiDAR/IFC truth, transfer, safety, data class, support pin, chain policy). Horizon A tooling does not clear those obligations.

```text
L0 lab → L1 controlled pilot (relegate R1,R2,R5,R7–R10)
      → L2 multi-building program
      → L3 full vision economy (R3,R4,R8 production)
```

Measure success by **closed loops with evidence**, and by **obligation exit criteria**—not by LOC or optional rings.

This document is the engineering design, the vision lock, the obligation register, and the ordered plan to relegate reservations without lying about readiness.
