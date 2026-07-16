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
