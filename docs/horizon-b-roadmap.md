# Horizon B — Living development plan (site capture → L1 exit)

**Authority:** [`arxos_manifest.md`](../arxos_manifest.md) §1.1a · §1.5–1.6 · §10.2  
**Field packet (policy order):** [field-handoff.md](./field-handoff.md)  
**Preferred pin:** `v2.0.0-pilot.4` @ `659bbd9f` — [pilot-release.md](./pilot-release.md)  
**Last updated:** 2026-07-13  

This file is the **living** Horizon B plan. Update status/dates when evidence lands; reconcile scores in the manifest.  
Do **not** start Horizon C work until L1 exit criteria here are met once.

---

## 0. Definition of Working (site target)

**North star (~250k sqft class building):**

Walk in with a device running the **WASM PWA** (and/or **edge agent**), perform **LiDAR scanning + labeling / AR corrections**, produce a **validated `Building`**, **export usable IFC**, with **human review gates**, **clear LossReport**, and **Git versioning** — reliable enough for **controlled L1 pilot under a signed charter**.

| Must have | Must not fake |
| :--- | :--- |
| `review_status` gates; `--approved-only` when LiDAR used | Survey-grade auto reconstruction |
| LossReport + `unmapped_products` honesty | “Validate OK” = full BIM |
| Pin install + private Git | Floating `main` as pilot image |
| IFC-only vendor BIM path | CAD plugins |
| CLI/TUI as durable export spine | Agent as second IFC authority |

**Principles:** compiler spine + honesty first · field evidence before features · LOC discipline · optional-ring minimization · L1 before Horizon C.

---

## 1. Ground truth (post–pilot.4)

| Area | Lab | Field |
| :--- | :---: | :---: |
| IFC import/export + identity | Strong | District evidence **open** (R2) |
| LossReport / `unmapped_products` | Done | Must appear on real files |
| buildingSMART + vendor non-panic | Done | Not district IFC |
| LiDAR heuristics + `proposed` | Synthetic CI | **Unproven** (R1) |
| YAML + Git + validate gates | Strong | Needs private remote + R5 |
| Resource refuse defaults | Done | Site profile **open** (R6) |
| TUI + CLI capture node | Ready | Second-person open (R5) |
| WASM PWA / agent | ~4/10 terminal/bridge | Walk-in capture **not** proven |
| Charter / data class | Templates | **Unsigned** (R7/R10) |

**Scorecard (honest):** Lab closed loop ~8–8.5/10 · District L1 ~4/10 · Full vision L3 ~2/10.

---

## 2. Integration architecture (do not fork)

```text
                    ┌─────────────────────────────────────┐
  Device            │  WASM PWA (review / label / AR)     │
  (tablet/phone)    │  optional: agent file/WS bridge     │
                    └──────────────┬──────────────────────┘
                                   │ files / envelope / git pull
                                   ▼
                    ┌─────────────────────────────────────┐
  Capture node      │  arx CLI + TUI  (pin install)        │
  (laptop/Mini)     │  import lidar | import ifc            │
                    │  edit / review_status                 │
                    │  validate → building.yaml → Git       │
                    │  export --format ifc [--approved-only]│
                    │  LossReport on every ingest           │
                    └─────────────────────────────────────┘
                                   │
                                   ▼
                         usable IFC + version history
```

| Integration point | Current surface | Pilot rule |
| :--- | :--- | :--- |
| LiDAR ingest | `arx import lidar` · `import_lidar_path` · `MergePolicy::lidar()` | Autos = `proposed` |
| Labeling / corrections | `arx edit` · review keys · TUI; WASM partial | Human gate before official export |
| IFC base model | `arx import ifc` · `MergePolicy::ifc()` | Vendor clean export only |
| Validation | `finalize_ingest` / `persist_building` / `arx validate` | Hard fail on errors |
| Loss reporting | Mapping `LossReport` · `unmapped_products` | Surface in CLI + field log |
| Export | `export::ifc` / `arx export --format ifc` | Only official spine |
| Versioning | Git via `arx stage` / `arx commit` | Internal remote (R7) |
| Device bridge | `web` PWA · `agent` WS/SSH | Optional rings; not export authority |

**Scale note:** Full ~250k point clouds stay on the **capture node** (`--light`, voxel, env limits). PWA is **review/label first**; in-browser full-building LiDAR is a later, evidence-gated claim (manifest non-goal until proven).

---

## 3. Phased roadmap

Phases are sequential **gates**. Later phases may **prep** (docs, dry lab) but do not claim exit without prior success criteria.

### Phase HB0 — Policy gate

| | |
| :--- | :--- |
| **Goal** | Legal/process cover before treating any export as official |
| **Maps to** | field-handoff B0–B2 · R7, R9, R10 |
| **Owner** | Field / leadership (eng supports pin only) |
| **Effort** | 0.5–2 days wall-clock (signatures dominate) |
| **Depends on** | Pin `v2.0.0-pilot.4` (done) |
| **Success** | Charter signed; pin + SHA in charter §2; data-classification complete; private remote named |
| **Risks** | Leadership delay; public Git by mistake |
| **Status** | Templates done · **signatures open** |

### Phase HB1 — Controlled dry-run (second person)

| | |
| :--- | :--- |
| **Goal** | Non-author can run the supported loop on the pin |
| **Maps to** | R5 · field-handoff B1 |
| **Owner** | Field IT (not doc author) |
| **Effort** | 0.5–1 day + stuck-list triage |
| **Depends on** | HB0 pin recorded (charter can be draft if dry-run is non-official) |
| **Success** | [second-person-checklist.md](./second-person-checklist.md) signed; stuck points filed as backlog only |
| **Risks** | Hero dependency remains if skipped |
| **Status** | **Open** |

### Phase HB2 — Real IFC field truth

| | |
| :--- | :--- |
| **Goal** | Prove vendor IFC path on **district** (or real site) files |
| **Maps to** | R2 field half · G3 honesty |
| **Owner** | Field provides files · eng fixes true import blockers only |
| **Effort** | 2–5 days (access + matrix) |
| **Depends on** | HB0 data class (no public facility models) |
| **Success** | Preserve/drop matrix in [field-truth-log.md](./field-truth-log.md); LossReport reviewed; export re-import notes |
| **Risks** | Incomplete vendor exports; wall drop surprise (mitigated by `unmapped_products`) |
| **Status** | Lab (buildingSMART) **done** · district **open** |

### Phase HB3 — Real LiDAR field truth (room → wing)

| | |
| :--- | :--- |
| **Goal** | Prove scan → `proposed` → human accept/reject → export path on real geometry |
| **Maps to** | R1 · G4/G6 field |
| **Owner** | Field capture · eng detector blockers only |
| **Effort** | 3–8 days (hardware + walks) |
| **Depends on** | HB1 recommended; HB0 for official claims |
| **Success** | ≥1 real scan session logged: false +/−, review actions, `--approved-only` export used; confidence caveats respected ([lidar-confidence.md](./lidar-confidence.md)) |
| **Risks** | Detector over-split rooms; tablet LiDAR format friction; false certainty culture |
| **Status** | **Open** |

### Phase HB4 — Site capture loop (G9)

| | |
| :--- | :--- |
| **Goal** | End-to-end free-software loop on **one** real building (messy data) |
| **Maps to** | N9 · G9 · §1.1a without requiring full PWA polish |
| **Owner** | Field lead + eng on-call |
| **Effort** | 1–2 weeks continuous on site access |
| **Depends on** | HB2 and HB3 at least partial; HB0 for “official” |
| **Success** | Documented loop: (IFC base optional) → LiDAR merge → label/edit → validate → Git → usable IFC; LossReport attached; charter rules followed |
| **Risks** | Scope creep to full BIM; multi-floor fatigue; Git remote policy |
| **Status** | **Open** |
| **Default capture path** | CLI/TUI on laptop/Mini first — **not** blocked on PWA |

### Phase HB5 — Scale profile ~250k sqft (R6 / G7)

| | |
| :--- | :--- |
| **Goal** | Know limits on pilot hardware for school-scale models |
| **Maps to** | R6 · G7 · [resource-limits.md](./resource-limits.md) |
| **Owner** | Field runs · eng tunes defaults only if refuse is wrong |
| **Effort** | 2–4 days once site model available |
| **Depends on** | HB2 and/or HB4 assets at scale |
| **Success** | field-truth-log §C: time, RAM, limits used, light-mode outcomes; written guidance for that site |
| **Risks** | OOM hidden by skipping validation (forbidden); Pi-class underpowered |
| **Status** | Eng defaults **done** · site profile **open** |

### Phase HB6 — Device UX (PWA / agent) for walk-in scenario (G10)

| | |
| :--- | :--- |
| **Goal** | Device is **field-usable** for review/label (and optional bridge), not a lab demo |
| **Maps to** | G5/G10 · §1.1a device clause |
| **Owner** | Eng primary · field UAT |
| **Effort** | 1–3 weeks eng after HB3–HB4 evidence (or explicit early approval) |
| **Depends on** | **Gate:** HB3 or HB4 evidence **or** vision-holder approval to parallelize |
| **Success** | Second person completes review/label handoff on tablet; files land on capture node; export still CLI spine; no dual write path |
| **Risks** | Premature PWA rebuild; browser LiDAR overpromise; LOC / ring bloat |
| **Status** | Lab WASM ~4/10 · **gated** |
| **In scope (incremental)** | Envelope load/save, hierarchy, review_status actions, LossReport visibility, clear “export happens on capture node” UX |
| **Out of scope until proven** | Full building LiDAR meshing in-browser; CAD-like 3D; hardware BACnet restore |

### Phase HB7 — L1 exit scorecard

| | |
| :--- | :--- |
| **Goal** | Declare controlled pilot ready (or list remaining gaps honestly) |
| **Maps to** | §1.6 R1,R2,R5,R7–R10 pilot-mitigated |
| **Owner** | Both |
| **Effort** | 1 day reconciliation |
| **Depends on** | HB0–HB4 (HB5 recommended; HB6 preferred for §1.1a full wording) |
| **Success** | Manifest §1.6 statuses updated from evidence paths; district L1 score ≥6/10 with caveats; **no** Horizon C start without explicit go |
| **Status** | **Open** |

### Parallel (optional, non-blocking for L1)

| Track | Rule |
| :--- | :--- |
| **HB-chain** | Off-chain L1 default; Anvil/testnet only if charter §5 names requester |
| **Wall mapping** | Product feature — only after HB2 shows walls matter for pilot value; never instead of honesty |
| **Horizon C** | Frozen until HB7 L1 exit once |

---

## 4. Effort / risk summary

| Phase | Effort (order-of-magnitude) | Highest risk |
| :---: | :--- | :--- |
| HB0 | Days (people) | Signature lag |
| HB1 | ≤1 day | Skipped → single hero |
| HB2 | Days | No site IFC access |
| HB3 | Days–1.5 wk | Scan quality / detector culture |
| HB4 | 1–2 wk | Scope creep to CAD |
| HB5 | Days | Untested large files |
| HB6 | 1–3 wk eng | Premature device work |
| HB7 | Day | Optimistic scoring |

**Kill criteria for any eng feature PR in Horizon B:**
- Weakens validation or LossReport
- Adds optional ring without approval
- Requires CAD plugin
- Claims field evidence without log entry
- Rewrites ingest/YAML/IFC spine without integrity cause

---

## 5. Immediate next sprint (1–2 weeks)

**Theme:** Policy + transfer + first real evidence — **not** PWA rebuild.

| # | Task | Owner | Gate / approval | Done when |
| :---: | :--- | :---: | :--- | :--- |
| S1 | Fill + **sign** pilot charter (site, pin `v2.0.0-pilot.4` @ `659bbd9f`) | Field / leadership | Leadership | Signature on charter |
| S2 | Complete data-classification + name private Git remote | Field IT | Security/IT | Charter §4 ticked |
| S3 | Install pin on pilot laptop; `arx --version` + `./scripts/l1_smoke.sh` | Field | Eng if install fails | Smoke PASS on pin |
| S4 | Second-person checklist (non-author) | Field | — | Checklist signed or stuck-list filed |
| S5 | Obtain **1 real IFC** (anonymized if needed); import → LossReport → export | Field + eng standby | Data class before share | Matrix row in field-truth-log |
| S6 | If LiDAR hardware available: **1 room/wing** scan → proposed → accept/reject → approved export | Field | Charter before “official” | R1 log section started |
| S7 | Eng: fix **only** S3–S6 blockers (import crash, pin install, doc error) | Eng | Stuck-list ID | Green re-run |
| S8 | Update this file + manifest §1.6 statuses for any closed row | Eng | Evidence path | Commit |

**Explicitly deferred this sprint:** HB6 PWA productization, wall class mapping, Horizon C, hardware BACnet, 3D viz restore, multi-building campus.

**Approval gates for vision holder:**
1. Confirm **target building** (~250k class or smaller first site).
2. Confirm **capture hardware** path (device LiDAR → which file format? capture node model?).
3. Approve whether HB6 may **overlap** HB3/HB4 or must wait for evidence.

---

## 6. Open questions / blockers (need owner input)

| ID | Question | Blocks | Suggested default |
| :---: | :--- | :--- | :--- |
| Q1 | Which building is L1 site #1 (name, ~sqft, access window)? | HB2–HB5 | Smaller wing first if 250k access is slow |
| Q2 | LiDAR hardware + export format (iPad Pro PLY/E57? Matterport? BLK?) | HB3 | Prefer formats `import lidar` already accepts; log gaps |
| Q3 | Capture node hardware (Mac Mini / Windows laptop / Pi)? | R6 | Mini/laptop; Pi only IFC-light |
| Q4 | Is first pilot **IFC-first** or **scan-first**? | HB2 vs HB3 order | IFC-first if BIM exists; else scan-first room |
| Q5 | Who is second person for R5 (named)? | HB1 | Name before sprint mid-point |
| Q6 | May eng start **minimal PWA review** (HB6 slice) in parallel with HB3? | LOC / focus | **No** until Q1–Q2 answered + one field log row — unless you override |
| Q7 | Vendor IFC available under data class (Revit export settings owner)? | HB2 | Facilities BIM contact |
| Q8 | Charter signer + data-class approver (named)? | HB0 | Required for “official” export language |

---

## 7. Status log

| Date | Note |
| :--- | :--- |
| 2026-07-13 | Plan created post–pilot.4. Package A (LossReport, buildingSMART) closed. HB0–HB7 defined. Sprint = field policy + first evidence. |

**Related:** [INDEX.md](./INDEX.md) · [l1-supported-workflow.md](./l1-supported-workflow.md) · [ifc-limitations.md](./ifc-limitations.md) · [field-truth-log.md](./field-truth-log.md) · [resource-limits.md](./resource-limits.md)
