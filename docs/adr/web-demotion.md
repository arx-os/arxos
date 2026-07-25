# ADR: Demotion of interactive WASM/PWA (web landing only)

| Property | Value |
| :--- | :--- |
| **Status** | **Accepted** (2026-07-24) |
| **Type** | Architecture / product-surface decision |
| **Scope** | Device capture UX · optional `web` feature · HB6 device path |
| **Supersedes (product role)** | Interactive Leptos/WASM client as field capture/review/label surface; prior HB6 “iPhone PWA acceleration” as product north star |
| **Does not supersede** | Agent as edge bridge · compiler spine · IFC-only BIM · TUI as default UI · L1 field packet obligations |
| **Related** | [`adr.md`](README.md) Decision 9 · [`../arxos_manifest.md`](../../arxos_manifest.md) §1.1a / device path (to be reconciled after purge) · Phase 0 inventory (session 2026-07-24) |

---

## Context

ArxOS explored a pure **WASM Progressive Web App** (Leptos, Trunk, browser WebSocket client) as a field device surface: connect to the laptop agent, Create New via `getUserMedia`, label/review hierarchy, and (aspirationally) support walk-in LiDAR/AR corrections under Horizon B / HB6.

That path hit a **platform ceiling**, not a temporary eng gap:

1. **iOS Safari does not expose ARKit, RoomPlan, or LiDAR depth** to web content. There is no honest way for a pure PWA to perform spatial LiDAR capture on iPhone.
2. **WebXR AR is not a substitute** for RoomPlan/ARKit on mobile Safari for this product class.
3. Continuing to market “walk-in with PWA + LiDAR,” browser RoomPlan, or Create New as spatial capture **damages honesty** (L1 scorecard, pilot trust, and §1.1a claims).
4. RGB-only `getUserMedia` frames can create a **placeholder proposed room** for labeling demos, but that is **not** LiDAR and must not be sold as as-built geometry.

Field testing and further vertical product slices on the interactive PWA are **paused** until the foundation matches reality.

---

## Decision

### 1. Pure PWA spatial path is abandoned

The interactive WASM/PWA client is **not** a spatial capture product, not a primary field client, and not the walk-in device path for §1.1a.

### 2. Role of “web” going forward

**Web = static landing page only:**

- Marketing / product one-liner  
- Status / maturity honesty pointers  
- Links to docs and install/download guidance  
- **No** capture, Create New, label, review hierarchy, owner staging UI, camera, AR overlays, or agent WebSocket spatial workflow in the browser  

Implementation of that landing reduction is a follow-on engineering purge (separate from this ADR). This document locks the **product role**.

### 3. Future capture surface: native iOS companion

Real phone LiDAR / RoomPlan / ARKit-class capture requires a **native iOS companion app** (foundation **not** started by this decision). That companion will talk to the existing **agent** (or equivalent bridge) and must not become a second durable authority.

### 4. Durable authority (unchanged)

| Layer | Authority |
| :--- | :--- |
| **Durable SSOT** | `building.yaml` (schema-versioned), written only after validation / finalize |
| **Runtime model** | `core::Building` |
| **Capture node / bridge** | **Agent** (WebSocket/SSH edge) + CLI/TUI on the host |
| **Official IFC export** | `arx export --format ifc` (agent may trigger the same spine; agent is **not** a second export authority) |
| **Current honest spatial ingest** | **File-based** LiDAR (PLY/LAS/…) and IFC via CLI/agent import — not browser sensors |

### 5. Explicit non-claims (going forward)

Do **not** claim, document, or demo as product truth:

- Browser / Safari **LiDAR depth** or mesh reconstruction  
- **RoomPlan** or **ARKit** inside a PWA  
- “Walk-in with the **PWA**,” “PWA + LiDAR,” or §1.1a satisfied by WASM alone  
- In-browser full-building scan for ~250k sqft  
- That `getUserMedia` JPEG capture is as-built geometry (it is evidence frames / placeholder structure only, if retained at all on non-web surfaces)

---

## Consequences

| Area | Consequence |
| :--- | :--- |
| **Code** | Interactive Leptos/WASM app **removed** (2026-07-24); residual web = static `index.html` landing. |
| **Agent** | **Kept.** Remains capture node / bridge for CLI, future native, and file workflows (including existing RPCs such as import/edit/export and `capture.from_camera` until a later decision retires them). |
| **Compiler / TUI / IFC / file LiDAR / Git** | **Unchanged** product spine. |
| **Docs** | Living SoT rewritten to match this ADR (Phase 3). HB6 PWA guides in `docs/_archive/` with banners. |
| **G10 / device path** | Reinterpreted as **native iOS + agent**, not WASM PWA. Native scaffolding is **out of scope** of the purge session. |
| **Horizon C / rewards / CAD** | **Not** affected by this ADR. |

---

## Alternatives considered

| Alternative | Why rejected |
| :--- | :--- |
| Keep PWA as RGB-only “capture” product | Confuses operators; not LiDAR; still blocks honest §1.1a language |
| Wait for Safari WebXR/ARKit-in-browser | Uncertain timeline; product cannot depend on it for L1 foundation |
| Abandon phone capture entirely | Too strong; native iOS remains the correct long-term path |
| Delete the agent with the PWA | Wrong blast radius — agent is the durable bridge for all clients |

---

## Follow-on work

1. ~~**Code purge**~~ — done (`refactor!(web)` 2026-07-24).  
2. ~~**Docs purge**~~ — done (Phase 3, 2026-07-24).  
3. ~~**Verification**~~ — default + agent builds/tests/clippy green (Phase 2).  
4. **Later:** native iOS companion scaffolding (new decision when started).

---

## One-sentence summary

**Safari cannot do real iPhone LiDAR; the interactive PWA is demoted to a static landing page; future phone capture is native iOS; agent + `building.yaml` remain the only durable authority.**
