# ADR: Near-term field capture model (proposed-first, geometry as input)

| Property | Value |
| :--- | :--- |
| **Status** | **Accepted** (2026-07-24) |
| **Decision** | **10** |
| **Type** | Architecture / product capture model |
| **Scope** | Field contribution · LiDAR/geometry ingest · agent write gate · device path |
| **Complements** | Decision 9 ([`adr-web-demotion.md`](web-demotion.md)) — web landing only; native iOS future |
| **Does not supersede** | IFC-only BIM · agent as bridge · TUI default · L1 field packet · Horizon C freeze |
| **Related** | [`adr.md`](README.md) Decision 10 · [`../arxos_manifest.md`](../../arxos_manifest.md) §1.1a · `review_status` / LiDAR proposed gates |

---

## Context

ArxOS is a **pathway and protocol for building truth**, not a 3D viewer or mesh editor. Contributors (e.g. electricians on site) need to:

1. Capture what is in front of them.  
2. Receive **structured proposed entities** they can use immediately (including personal AR on a future device).  
3. Treat contributions like open-source **PRs** — land as proposed first; formal ownership / municipal acceptance later.

Constraints already locked:

- Interactive browser capture is **abandoned** (Decision 9). Safari cannot do ARKit/RoomPlan/LiDAR depth.  
- Durable product state is the **`Building` graph** in **`building.yaml`**, not dense geometry.  
- File LiDAR (PLY/LAS/XYZ → structure assist → `proposed`) exists today but files are large.  
- Horizon C and reward/ownership productization stay **frozen**.

This ADR freezes the **near-term capture model** so native clients, file paths, and the agent share one set of rules.

---

## Decision

### 1. Goal of near-term capture

**Field contributor captures geometry → ArxOS returns proposed structured entities → contributor can use them immediately.**

- “Use immediately” means local proposed structure for work planning, labeling, personal AR, and further edits — **not** municipal acceptance or official ownership.  
- Official ownership, multi-party review programs, and institutional acceptance are **later** work.

### 2. Authority and write rules

| Rule | Detail |
| :--- | :--- |
| **Sole durable write path** | Agent (or CLI on the capture node) → **`finalize_ingest` → validation → `building.yaml`** |
| **No direct YAML writes** | No client (native, script, or future UI) writes or patches `building.yaml` outside the spine |
| **Client payload** | Geometry and/or **proposed domain candidates** only — not “approved” official truth |
| **Default status** | All entities created from field capture start as **`review_status=proposed`** |
| **Export** | Official IFC remains `arx export --format ifc` (prefer `--approved-only` when LiDAR/proposed material was used). Agent may trigger the same spine; agent is **not** a second export authority |

### 3. Role of geometry

- Geometry (point cloud, mesh, RoomPlan output, etc.) is **temporary input**.  
- It is **consumed** to produce **domain structure** (floors, rooms, equipment candidates, anchors as needed).  
- ArxOS does **not** become a long-term point-cloud or mesh store. Prefer **early reduction** to domain entities.  
- Dense blobs may land under project `imports/` as evidence artifacts for operators; they are **not** the SSOT and must not replace `building.yaml`.

### 4. Device path

| Path | Status |
| :--- | :--- |
| **File LiDAR + IFC + agent + CLI/TUI** | **Current honest** capture / ingest |
| **Native iOS** (RoomPlan / ARKit-class) | **Future** — only path for real phone LiDAR (not started; Decision 9) |
| **Browser / Safari PWA capture** | **Non-claim** — no LiDAR, no RoomPlan/ARKit, no interactive field client |

### 5. Contribution model (near-term)

- Anyone with access to the capture node / agent may **contribute proposed data** (PR-like).  
- Human review (`accepted` / `rejected`), formal ownership, and municipal flows are **out of scope** for this decision’s success criteria.  
- Existing `review_status` and export gates remain the honesty mechanism for proposed LiDAR structure.

### 6. Interface thinness

Prefer the **thinnest honest interface**:

```text
geometry (or RoomPlan / file LiDAR / IFC)
        │
        ▼  structure extraction (existing or future adapter)
domain candidates (rooms / equipment / …)  — all proposed
        │
        ▼  agent / CLI write gate
finalize_ingest → validate → building.yaml
```

- Prefer **extending existing ingest** (`import lidar`, `import ifc`, text/edit scripts, narrow agent RPCs) over a heavy new package format.  
- If a payload is needed, keep it **domain-shaped** (entities + provenance + honesty flags), not a second geometry database.  
- Do **not** introduce a new multi-file mesh product format unless a later decision proves it strictly necessary.

### 7. Out of scope (this ADR)

- Implementing the **native iOS app** (rules only).  
- **Ownership / municipal** acceptance workflows.  
- **3D viewing** or mesh editing product inside ArxOS.  
- **Horizon C** / production rewards / mainnet.  
- Any return of **interactive PWA** capture.

---

## Consequences

| Area | Consequence |
| :--- | :--- |
| **Native iOS (when started)** | Must speak to the agent with geometry or proposed candidates; must not write `building.yaml` directly; all new entities proposed first |
| **File LiDAR path** | Remains the honest path today; optimize for size/workflow later without changing authority rules |
| **Product identity** | ArxOS stays a compiler/protocol for structured building truth — not a CAD host or cloud mesh vault |
| **L1 pilot** | Still file IFC/LiDAR + CLI/TUI + process packet; native capture not required for L1 exit |
| **Personal AR** | May run on the contributor’s device using proposed structure; ArxOS is not required to host AR rendering |

---

## Alternatives considered

| Alternative | Why rejected |
| :--- | :--- |
| Store dense clouds as primary SSOT | Wrong product; non-diffable; not “Git for Buildings” |
| Client writes `building.yaml` for speed | Dual authority; breaks validation honesty |
| Field entities land as accepted by default | Unsafe near life-safety work; violates proposed-first |
| Wait for browser LiDAR | Impossible on iOS Safari; already rejected in Decision 9 |
| Heavy proprietary capture package as first step | Premature; existing ingest + thin domain payloads suffice |

---

## One-sentence summary

**Capture produces proposed structure through the agent spine; geometry is disposable input; phone LiDAR is native later; ArxOS stays a protocol for building.yaml, not a mesh product.**
