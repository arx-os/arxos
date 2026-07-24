# ADR: Repository structure — core vs native iOS companion

| Property | Value |
| :--- | :--- |
| **Status** | **Accepted** (2026-07-24) |
| **Decision** | **12** |
| **Type** | Repository / org architecture |
| **Complements** | Decision 9 (web) · 10 (capture model) · 11 (native↔agent interface) |
| **Related** | [`agent-client-interface.md`](./agent-client-interface.md) · [`adr-native-capture-interface.md`](./adr-native-capture-interface.md) |

---

## Decision

| Repository | Contents | Role |
| :--- | :--- | :--- |
| **`arx-os/arxos`** (this repo) | Rust compiler, domain model, ingest, validation, YAML SSOT, Git, IFC, TUI, CLI, **agent** | Core system / capture node / durable authority |
| **`arx-os/ios`** (separate) | Native iOS companion (SwiftUI, Xcode, RoomPlan/ARKit, signing, TestFlight) | Peripheral field client only |

- The two repos **do not** share a monorepo.  
- They communicate **only** through an **explicit, versioned interface** (agent JSON-RPC + file LiDAR hand-off — Decision 11).  
- No shared Cargo+Xcode tree, no iOS binary artifacts or App Store secrets in core.

**Recommended remote:** `https://github.com/arx-os/ios` (same org as core).

---

## Rationale

1. **Keeps core tight** — Rust system stays focused on building truth, not Xcode noise.  
2. **Independent release cycles** — pin core for pilots; ship iOS via TestFlight separately.  
3. **Clean Apple workflow** — signing, capabilities, privacy manifests, App Store live in the iOS repo.  
4. **Obvious authority boundary** — iOS is a peripheral; **agent alone** performs durable writes.  
5. **Tooling isolation** — Cargo vs Xcode, `target/` vs `DerivedData/`, tokens vs distribution certs stay separated.

---

## Authority rule (restated)

| Actor | May | Must not |
| :--- | :--- | :--- |
| **iOS companion** | Capture geometry; send files / proposed candidates; call agent RPCs | Write `building.yaml` or replace SSOT offline |
| **Core agent** | `finalize_ingest` → validate → `building.yaml`; Git; IFC export | Treat client as second export authority |

See Decision 10–11 for capture model and wire contract details. Living summary: [`agent-client-interface.md`](./agent-client-interface.md).

---

## What lives where

### Core (`arxos`)

- `src/core`, `ingest`, `validation`, `ifc`, `spatial/lidar`, `git`, `persistence`, `yaml`  
- `src/agent` (WebSocket/SSH capture node)  
- `src/cli`, `src/tui`  
- Pilot docs, ADRs, static web landing  
- **Interface contract docs** (versioned for companion consumers)

### Companion (`ios`)

- Xcode project / SwiftUI terminal field client  
- RoomPlan / ARKit / camera / local network UX  
- App signing, TestFlight, App Store metadata  
- Client-side only; depends on a running core **agent**

### Not in either as product

- Interactive WASM field PWA (Decision 9)  
- Horizon C / mainnet rewards (frozen unless explicitly opened)

---

## Bootstrap / migration notes

1. Core monorepo **must not** carry a full iOS app tree after this decision.  
2. Companion remote: **https://github.com/arx-os/ios** (local clone often `~/repos/arxos-ios` or `~/repos/ios`).
3. Interface breakage requires a **version bump** note in `agent-client-interface.md` and a matching companion release.

---

## Consequences

| Area | Effect |
| :--- | :--- |
| **Core CI** | No iOS jobs required |
| **Companion CI** | Xcode cloud / macOS runners in `ios` only |
| **Developers** | Clone both repos for full walk-in lab loop |
| **Pilots** | Pin **core** tag; install **iOS** build that targets that agent protocol version |

---

## Alternatives considered

| Option | Why rejected |
| :--- | :--- |
| Monorepo with `ios/` | Mixes tooling, release, and secrets; blurs authority |
| CocoaPods/SPM package inside core | Still couples Xcode lifecycle to Rust releases |
| iOS-only product without agent | Violates durable-write authority |

---

## One-sentence summary

**Core stays Rust in `arxos`; native iOS lives in `ios`; they only talk over the versioned agent interface, and only the agent writes the building model.**
