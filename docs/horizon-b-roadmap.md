# Horizon B — Living development plan (site capture → L1 exit)

**Authority:** [`arxos_manifest.md`](../arxos_manifest.md) §1.1a · §1.5–1.6 · §10.2  
**Field packet (policy order):** [field-handoff.md](./field-handoff.md)  
**Preferred pin:** `v2.0.0-pilot.4` @ `659bbd9f` — [pilot-release.md](./pilot-release.md)  
**Last updated:** 2026-07-13 (Day 1 runbook + S8 template + eng queue)  

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

## 5. Sprint execution plan (HB0–HB2 focus) — 1–2 weeks

**Theme:** Policy + transfer + first real IFC evidence. **Not** PWA rebuild, wall mapping, or Horizon C.  
**Pin:** `v2.0.0-pilot.4` @ `659bbd9f369c0b942f150983b204ea054fc595a0`  
**Code changes:** **none** unless S7 stuck-list item is approved.

### 5.0 Sprint calendar (suggested)

| Day | Focus | Exit |
| :---: | :--- | :--- |
| D1 | S1 charter draft + pin line; name Q5/Q8 people | Draft charter exists |
| D1–D2 | S2 data class; S3 pin install on pilot laptop | Smoke PASS |
| D2–D3 | S4 second-person dry-run | Checklist pass/conditional |
| D3–D7 | S5 real IFC (access may dominate) | ≥1 field-truth matrix row |
| D5–D10 | S6 optional if hardware ready | R1 section started or N/A |
| Rolling | S7 eng blockers only | Green re-run of failing step |
| End | S8 reconcile docs/manifest | Status log entry |

### 5.1 Task detail (S1–S8)

#### S1 — Pilot charter (HB0 / R10)

| | |
| :--- | :--- |
| **Owner** | Pilot owner + leadership |
| **Template** | [pilot-charter.md](./pilot-charter.md) |
| **Steps** | 1) Fill parties (§1) incl. second person + reviewer. 2) Scope (§2): site name, inputs IFC [x], LiDAR [ ] or [x], pin **exactly** `v2.0.0-pilot.4` + full SHA. 3) Initial safety §3. 4) Data class ticks when S2 ready. 5) **Sign**. |
| **Verify** | Pin SHA matches [pilot-release.md](./pilot-release.md); go level L1 only; chain off unless §5 names demo |
| **Acceptance** | Signed charter on file (PDF or wet); pin recorded; building name non-empty |
| **Eng** | None |

#### S2 — Data classification + private remote (HB0 / R7)

| | |
| :--- | :--- |
| **Owner** | Field IT + security |
| **Template** | [data-classification.md](./data-classification.md) |
| **Steps** | 1) Complete classification (internal default). 2) Name private Git host/path. 3) Who may clone/export. 4) No student PII rule. 5) Tick charter §4. |
| **Verify** | Remote is **not** public GitHub by default; export path matches class |
| **Acceptance** | Classification complete; charter §4 ticked; remote URL recorded (may be private-only) |
| **Eng** | None (unless docs wrong — then S7) |

#### S3 — Pin install + smoke (HB0–HB1 / R9)

| | |
| :--- | :--- |
| **Owner** | Field capture tech |
| **Steps** | See commands below; use only [l1-supported-workflow.md](./l1-supported-workflow.md) |
| **Verify** | `git rev-parse HEAD` = `659bbd9f…`; `arx --version` works; smoke PASS |
| **Acceptance** | Install on pilot machine succeeds; smoke PASS logged (date/machine) |
| **Eng subtasks (if fail)** | See §5.3 — approval before code |

```bash
git clone <approved-remote> arxos && cd arxos
git checkout v2.0.0-pilot.4
git rev-parse HEAD   # 659bbd9f369c0b942f150983b204ea054fc595a0
cargo install --path . --locked
arx --version
# From repo root (needs cargo build of pin tree):
./scripts/l1_smoke.sh
```

If smoke script path awkward after `cargo install`, run smoke from the pin checkout after `cargo build`.

#### S4 — Second-person dry-run (HB1 / R5)

| | |
| :--- | :--- |
| **Owner** | Named second person (**not** doc author) |
| **Template** | [second-person-checklist.md](./second-person-checklist.md) |
| **Steps** | Timed run steps 1–10; include **5b** (note LossReport warnings); owner observes only |
| **Verify** | Pin SHA on form matches charter; no blockchain/agent/CAD; stuck >10m written |
| **Acceptance** | Pass **or** Conditional with ≤3 stuck points filed as backlog; Fail → eng S7 + re-walk |
| **Eng** | Only for stuck-list items that are software/doc defects |

#### S5 — One real IFC + LossReport (HB2 / R2 field)

| | |
| :--- | :--- |
| **Owner** | Field provides file · eng standby |
| **Template** | [field-truth-log.md](./field-truth-log.md) §A + §A2 |
| **Gate** | S2 data class before sharing facility IFC off-prem |
| **Steps** | 1) Obtain clean IFC from vendor BIM (no plugins). 2) Init pilot repo. 3) Import. 4) **Copy warnings** to A2. 5) Validate. 6) Export IFC. 7) Optional re-import. 8) Fill matrix row (floors/rooms/GIDs/`unmapped_products`). 9) Performance notes → §C if large. |
| **Verify** | No panic; LossReport not ignored; matrix not empty |
| **Acceptance** | ≥1 district-class (or real site) IFC row + A2 filled. **Does not** require perfect wall mapping. |
| **Eng** | Crash / refuse-without-message / wrong pin docs only |

```bash
mkdir -p ~/arx-pilots/SITE && cd ~/arx-pilots/SITE
arx init --name "SITE"
arx import ifc /path/to/vendor.ifc    # capture full stdout
arx validate
arx export --format ifc --output exports/out.ifc
# paste warnings into field-truth-log A2
```

#### S6 — Optional first LiDAR room/wing (HB3 start / R1)

| | |
| :--- | :--- |
| **Owner** | Field (if hardware + Q2 answered) |
| **Template** | field-truth-log §B |
| **Gate** | Charter marks LiDAR in scope for official claims; else lab-only practice |
| **Steps** | Import scan → list `proposed` → accept/reject ≥1 → export `--approved-only` → log false +/− |
| **Acceptance** | §B started **or** charter LiDAR **out of scope** (IFC-only pilot) |
| **Skip OK** | If no hardware this sprint — log “deferred to next sprint” |

#### S7 — Eng blocker fixes only

| | |
| :--- | :--- |
| **Owner** | Eng |
| **Gate** | Each fix has stuck-list ID + **approval before apply** if code change |
| **In scope** | Pin install fails; import panic; confusing error on refuse; checklist/doc wrong path; smoke regression |
| **Out of scope** | PWA features, wall mapping, new optional rings, spine rewrite |
| **Acceptance** | Failing S3–S6 step re-runs green; clippy `-D warnings` if code touched |

#### S8 — Reconcile living plan

| | |
| :--- | :--- |
| **Owner** | Eng (+ field for evidence paths) |
| **Steps** | Update this file §7 status log; if R5/R2/R7/R10 evidence exists, update manifest §1.6 status cells with **path to evidence** (not “Done” without path) |
| **Acceptance** | Commit on `main`; no fake closures |

### 5.2 Field checklist pack (print)

- [ ] [pilot-charter.md](./pilot-charter.md)  
- [ ] [data-classification.md](./data-classification.md)  
- [ ] [pilot-release.md](./pilot-release.md) (pin table)  
- [ ] [l1-supported-workflow.md](./l1-supported-workflow.md)  
- [ ] [second-person-checklist.md](./second-person-checklist.md)  
- [ ] [field-truth-log.md](./field-truth-log.md)  
- [ ] [ifc-limitations.md](./ifc-limitations.md) (read once)  
- [ ] [resource-limits.md](./resource-limits.md)  

### 5.3 Proposed eng improvements (approval required — not applied)

Spine-safe, small, only if sprint pain appears. **Default: implement none until approved.**

| ID | Proposal | Why | Risk | LOC sense |
| :---: | :--- | :--- | :--- | :---: |
| E1 | Ensure `arx import ifc` always prints warning **codes** (incl. `unmapped_products`) clearly | S4 5b / S5 A2 | Low | Tiny |
| E2 | On resource refuse, print limit value + env var name + link path `docs/resource-limits.md` | S3/S5 large files | Low | Tiny |
| E3 | `arx import ifc --help` one-line: “vendor BIM → clean IFC only; no plugins” | R5 transfer | Low | Tiny |
| E4 | Document-only: copy-paste “import capture” snippet into field-truth-log (done in templates) | Evidence | None | Docs |
| E5 | **Defer:** PWA bridge stability, camera LiDAR | HB6 | Medium | Skip |
| E6 | **Defer:** wall/slab domain mapping | Product | High scope | Skip |

**No proposed diffs applied in this reconcile.** Paste stuck-list → approve E* → then implement.

### 5.4 Explicitly deferred this sprint

HB6 PWA productization · wall class mapping · Horizon C · hardware BACnet · 3D viz · multi-building campus · new pins unless install-breaking bug.

---

## 6. Risk & dependency management

| # | Risk | Likelihood | Impact | Mitigation |
| :---: | :--- | :---: | :---: | :--- |
| K1 | Leadership delay on charter/signatures | H | Blocks “official” | Dry-run (S4) may use draft charter; no official export language until signed |
| K2 | No second person named | M | R5 fails | Q5 default: name by D2 or pilot pauses |
| K3 | Facility IFC not available / wrong class | H | R2 stuck | Redacted extract; or smaller non-public sample with same schema; escalate Q7 |
| K4 | Import “OK” culture ignores LossReport | M | False BIM confidence | Checklist 5b + field-truth A2 required |
| K5 | Scope creep to walls/PWA mid-sprint | M | LOC / delay evidence | Kill list §4; S7 gate |
| K6 | Large IFC hits default 50 MiB refuse | M | Panic-as-failure | Use env raise + log §C; never disable validation |
| K7 | Floating `main` install | M | R9 regression | Charter pin only; smoke from tag |
| K8 | Public Git with facility model | L/H | R7 / legal | S2 before S5 share |
| K9 | Single hero continues | H | Pilot dies | S4 hard gate before HB4 |
| K10 | Premature HB6 eng | M | Distraction | Q6 default **No** |

**Dependencies:** S5 → S2 (data class) · S4 → S3 (install) · official export claims → S1 · R2 close → S5 evidence · R5 close → S4 pass/conditional.

---

## 7. Evidence-driven guardrails (when R\* may close)

| Obligation | May mark **Partial** | May mark **Done / pilot-mitigated** | Never mark Done if |
| :--- | :--- | :--- | :--- |
| **R10** | Template exists | Signed charter path cited | Unsigned |
| **R9** | Pin cut | Charter records pin + R5 used that pin | “Just use main” |
| **R7** | Template | Classification + private remote evidence | Public facility model |
| **R5** | Checklist template | Completed checklist (pass/conditional) path | Author walked themselves only |
| **R2** | Lab fixtures + LossReport eng | ≥1 real site/district IFC matrix + A2 | buildingSMART only |
| **R1** | Synthetic CI | Real scan §B **or** charter LiDAR out-of-scope | Fake false +/− |
| **R6** | Eng defaults | §C filled for site hardware | Defaults alone |
| **R8** | L1 off-chain default | Leadership go/no-go written | Mainnet without go |
| **R3/R4** | Lab E2E | Not required for L1 exit | Claiming L3 |

**Logging rules:**
1. Prefer private copy of field-truth-log if models are sensitive; cite path in manifest status cell.
2. Every eng “close” PR must link evidence path in commit message.
3. Scores in manifest §2.1 update only in S8-style reconcile after evidence.

---

## 8. Open questions (recommendations if unanswered)

| ID | Question | Recommendation (default until you override) |
| :---: | :--- | :--- |
| **Q1** | L1 site #1 (name, ~sqft, window)? | Start with **one wing / floor** of the 250k building if full access is slow; name the parent building in charter |
| **Q2** | LiDAR hardware + format? | Prefer formats already accepted by `arx import lidar`; if unknown, **IFC-only sprint** (skip S6) |
| **Q3** | Capture node? | **Laptop/Mac Mini**; not Pi for first real IFC |
| **Q4** | IFC-first vs scan-first? | **IFC-first** this sprint (HB2); LiDAR room next if hardware ready |
| **Q5** | Second person name? | **Required by D2**; without name, S4 blocked |
| **Q6** | PWA eng parallel? | **No** until S5 has one matrix row **and** Q1–Q2 answered |
| **Q7** | Vendor IFC contact? | Facilities/BIM coordinator; export IFC4 with spaces if possible |
| **Q8** | Charter + data-class signers? | Pilot owner + security/IT named on D1 |

---

## 9. After this sprint (next actions)

| Priority | Action | Phase |
| :---: | :--- | :---: |
| 1 | Close any Conditional R5 stuck-list (eng) | HB1 |
| 2 | Second real IFC or second vendor if first was thin | HB2 |
| 3 | First real LiDAR room if S6 skipped | HB3 |
| 4 | Begin HB4 site loop only if S1+S4+S5 green | HB4 |
| 5 | HB5 profile when large model available | HB5 |
| 6 | HB6 PWA review slice **only** after gate or override | HB6 |
| 7 | Never Horizon C until HB7 once | — |

---

## 10. Status log

| Date | Note |
| :--- | :--- |
| 2026-07-13 | Plan created post–pilot.4. Package A closed. HB0–HB7 defined. |
| 2026-07-13 | Reconcile: field-truth A2 LossReport, checklist 5b, sprint S1–S8 detail, risks K1–K10, evidence guardrails, eng E1–E6 (not applied). Cross-links INDEX/README/pilot docs. |
| 2026-07-13 | Field Day 1 runbook (S3+S5); eng-blocker-queue (E1–E3 diffs, not applied); S8 reconciliation template; sprint readiness confirm. |

**Related:** [INDEX.md](./INDEX.md) · [l1-supported-workflow.md](./l1-supported-workflow.md) · [ifc-limitations.md](./ifc-limitations.md) · [field-truth-log.md](./field-truth-log.md) · [resource-limits.md](./resource-limits.md) · [field-handoff.md](./field-handoff.md)
