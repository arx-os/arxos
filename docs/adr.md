# Architecture Decision Record (ADR)

This document records the key architectural decisions made in the ArxOS project.

---

## Decision 1: EquipmentStatus and Health Semantic Unification
- **Context:** The core type system (`src/core/`) tracked operational status (Active, Inactive, Maintenance, OutOfOrder), while the YAML persistence formats (`src/yaml/`) tracked health status (Healthy, Warning, Critical). Mapping between these caused loss of precision.
- **Decision:** Decouple operational status from health status. Keep `status` as operational status and add a separate, optional `health_status` field on `Equipment` to capture health status cleanly in both core and YAML structures.
- **Consequences:** Semantics are preserved. Better compatibility with vendor IFC models.
- **Alternatives considered:** Mapping enums programmatically (rejected due to semantic loss).

---

## Decision 2: Separation of Spatial Coordinate Types
- **Context:** Core spatial calculations use a rich `Position` struct (which includes local/global coordinate frame context), whereas simple text storage uses a raw `Point3D` (x, y, z floats).
- **Decision:** Keep the types separate in the respective layers. Use custom Serde serialization helpers (`#[serde(with = "...")]`) to perform the conversion directly during save/load cycles without exposing string-based DTOs to core spatial operations.
- **Consequences:** Core spatial calculations remain type-safe and fast. YAML stays clean.

---

## Decision 3: Room Equipment Hierarchy Mapping
- **Context:** Core representation nests equipment within rooms (`Room.equipment: Vec<Equipment>`), whereas YAML representation structures equipment flatly under floors to facilitate easier Git merges and keep file sizes small.
- **Decision:** Use custom serialization/deserialization logic in `yaml.rs` to flatten the structure on save and rebuild the core hierarchical graph on load, keeping the core nested hierarchy intact.
- **Consequences:** Domain logic can traverse hierarchy naturally. Git history remains clean.

---

## Decision 4: Incremental Type Migration Strategy
- **Context:** Unifying core and YAML type structures risks breaking working compiler and contract verification code.
- **Decision:** Adopt an incremental refactoring strategy. Keep the older YAML conversion structures as temporary type aliases, write golden test suites, and migrate modules one by one.
- **Consequences:** Safe and progressive cleanup without blocking CI/CD pipelines.

---

## Decision 5: Web Owner Staging Review Dashboard
- **Context:** CLI-only review is insufficient for building owners. Field contributions land in a provisional/grace-period state and must be reviewable by the building owner before promotion to `main` and reward distribution.
- **Decision:** Implement a first-class Leptos page at `/owner/staging` that lists pending grace-period claims, shows high-signal diffs/change summaries, and allows Approve/Reject actions that call the existing agent claim pipeline.
- **Consequences:** Owner experience becomes usable; the local agent claim service must expose clean list + action APIs; on-chain reward path remains the source of truth for distribution.
- **Alternatives considered:** Keep CLI-only (rejected), full admin portal (deferred).

> [!NOTE]
> **TODO (Future Enhancement):** Once the basic staging review flow is fully stable, investigate gas sponsorship and account abstraction paymasters to hide transaction costs from the owner dashboard entirely.

---

## Decision 6: Agent Observability & Status Endpoints
- **Context:** After implementing the web owner dashboard, operators and owners need better runtime visibility into claim state, reward distribution, and agent health without relying solely on terminal logs or the dashboard.
- **Decision:** Introduce structured logging via the `tracing` and `tracing-subscriber` crates supporting configurable stdout formats (standard text and JSON via `LOG_FORMAT=json`). Expose new HTTP endpoints under `/api/status`, `/api/claims/status`, and a Prometheus-style `/metrics` endpoint, secured by the same token auth as the staging APIs. Provide dynamic, runtime log level reconfiguration (e.g. via environment or file-based updates) without requiring an agent restart.
- **Consequences:** Provides better operational visibility, request tracing (via trace correlation IDs in spans), and easier integration with external log collectors (like FluentBit, Prometheus, or Grafana). Minimal performance overhead on hot paths.
- **Alternatives considered:** Heavy OpenTelemetry exporter setup (rejected for L1 pilot; keep it local-first and lightweight).

> [!NOTE]
> > **TODO (Future Enhancement):** Future iterations can integrate OpenTelemetry collectors once multi-node P2P clusters are deployed, or load agent status directly into Grafana cloud dashboards.

---

## Decision 7: Text AR Overlay Polish Improvements
- **Context:** Field-workers mapping buildings require stable, readable labels on mobile screens. Noisy device gyroscope/compass sensors cause overlays to jitter rapidly. In dense spaces (like electrical rooms), labels overlap and become unreadable.
- **Decision:** Enhance the existing text overlay system with:
  1. Circular exponential smoothing (decomposing heading into sine/cosine components) to eliminate jitter and 0/360° wrapping jumps.
  2. An O(N log N) greedy vertical stacking and collision avoidance algorithm that sorts labels horizontally and offsets overlapping labels vertically.
  3. A cluster count badge (`+X`) that collapses overlapping labels when they exceed vertical screen space constraints.
  4. An interactive settings UI drawer in the PWA displaying sliders for FOV, smoothing factor, clustering threshold, and max labels.
- **Consequences:** More stable and readable labels under heavy motion or dense layouts; maintains a lightweight footprint without requiring WebGL or complex 3D math.
- **Alternatives considered:** Native ARKit/RoomPlan overlay application (deferred for P2+).

> [!NOTE]
> **Default Configuration Parameters:**
> - Field of View (FOV): `60.0°` (approximates typical phone camera horizontal viewing angle)
> - Smoothing Factor ($\alpha$): `0.8` (balances latency with high noise rejection)
> - Cluster Threshold: `15.0` (percentage horizontal collision window)
> - Max Labels: `20` (prevents screen clutter and maintains excellent frame rates on constrained devices)

---

## Decision 8: Reward Distribution Production Hardening
- **Context:** The `OnChainDistributor` needs to be production-ready, supporting configurable gas estimation multipliers, optional gas sponsorship via paymasters, robust format validation for loaded keys, and error recovery from transient RPC glitches.
- **Decision:** Implement:
  1. Hex-format validations on private keys loaded via `PrivateKeyLoader`.
  2. Configuration options in `DistributorConfig` for gas multipliers, paymaster addresses, networks, and max gas limit caps.
  3. A 3-attempt retry loop with exponential backoff on transient RPC providers/network errors.
  4. Sponsored gas simulation and estimation if a paymaster is set, falling back to direct signing on failure.
- **Consequences:** Payout releases are highly resilient to transient network glitches. Paymaster support allows gas-free payout execution for operators. Improper configurations are caught early before gas estimation runs.
- **Alternatives considered:** Offload all keys and signing logic to an external custody vault service (deferred for pilot stage).

> [!NOTE]
> **Example hard-payout configuration file (`.arx/config/payout.json`):**
> ```json
> {
>   "rpc_url": "https://rpc.phase.network",
>   "private_key": "0x0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
>   "gas_limit_multiplier": 1.15,
>   "paymaster_address": "0x9560f772421234567890abcdef1234567890abcd",
>   "network": "phase-mainnet",
>   "max_gas_limit": 500000
> }
> ```

