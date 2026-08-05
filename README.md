# Arxos

Arxos is a local-first, content-addressed spatial data repository system designed for the built environment. It enables versioned, verifiable, and databaseless representation of building geometry and annotations, mapping physical space captures directly to signed, cryptographically linked state graphs.

---

## 1. Project Status

Arxos is foundation-complete for the core pipeline (local content-addressed store, RoomPlan geometry ingestion, delta root materialization, spatial query, multi-device synchronization, and gateway format export). It is an experimental codebase and is **not** a production-ready CAD platform, finished consumer mobile app, or commercial billing platform.

### 1.1 Economic model (pure fiat)

| Role | Economics |
|------|-----------|
| **Data buyers** | Pay **fiat** for stream/API access, certified datasets, and enterprise features (subscription, usage, contracts). |
| **Contributors** | Submit real-world building/spatial data; the scoring engine produces **points**. |
| **Payouts** | Points convert to **fiat** later via ops-controlled rate tables and explicit payout batches in the **control plane**. |
| **Tokens / chain** | **None.** No minting, wallets, or blockchain settlement. |

Architecture: data plane (this repo’s CAS + scoring) vs control plane (accounts, money, access) — see [`docs/architecture/ADR-001-data-plane-vs-control-plane.md`](docs/architecture/ADR-001-data-plane-vs-control-plane.md).  
Full audit: [`docs/architecture/FIAT_MODEL_AUDIT.md`](docs/architecture/FIAT_MODEL_AUDIT.md).

**Scoring today is diagnostic only** (`arx score`). Do not treat scores as a payment basis until multi-signal policy and a control-plane points ledger exist.

### 1.2 Recently landed (integrity & structure)

| Area | Status |
|------|--------|
| Root **authorization** (`Building.controller_keys`) | Fail-closed on commit / adopt / merge; CLI uses the same verify path |
| **UniFFI** error surface (`ArxosError`) | Throwing APIs; no panics on ordinary store failures |
| **Fail-closed sync closures** | Incomplete object/index closures rejected unless `allow_partial` |
| CAS **index off put hot path** | Optional `index.cbor` rebuild-on-demand only |
| **Merge parents** on `RootBody` | Concurrent tips recorded; linear `previous_root` for materialization |
| **iOS real store only** | LocalStore / shim / `ALLOW_SHIM` removed; UniFFI → Rust CAS only |
| Module splits | `root/{auth,checkpoint,closure}`, `repository/{meta,commit,adopt,query}`, `spatial/index/{build,incremental,query}` |
| **P0 pure-fiat course correction** | EVM contracts archived; `depin` → `scoring`; CLI `score` / `verify` / `attest` |

Details: [`docs/architecture/ARCHITECTURE.md`](docs/architecture/ARCHITECTURE.md) §9.

### 1.3 Sensible next increments

1. **Control plane (P1)** — accounts, entitlements, metering, buyer fiat billing, points ledger, payout batches.
2. **Multi-signal scoring** — depth, coverage, attestation, review; versioned policy (still points-only in core).
3. **Blob tiering** — externalize point-cloud / mesh bytes for mobile and edge sync.
4. **Spatial index hardening** — higher fanout / better splits; keep query-equivalence tests.
5. **Store concurrency** — single-writer flock or local daemon.
6. **Structured errors** — typed variants for cleaner UniFFI mapping.
7. **Controller rotation & multi-device policy** — signed controller-set updates.
8. **CLI modularization** — split the monofile CLI into subcommand modules.

---

## 2. Core Concepts

- **Content-Addressed Objects**: Every piece of data is immutable and identified by a BLAKE3-256 content identifier (CID) computed over its canonical CBOR serialization.
- **Signed Delta Roots with Checkpoints**: Repository state transitions are defined by root commits. Intermediate commits serialize only delta additions and removals. A full-set checkpoint root is emitted every `CHECKPOINT_INTERVAL` (50) commits via a single policy module (`root::checkpoint`).
- **Authorized roots**: Every root author must be in `Building.controller_keys` (signatures alone are not enough).
- **Incremental Spatial Indexing**: A versioned binary spatial index is stored as content-addressed nodes. Day-to-day commits use path-copying inserts; full rebuild is used for merge/empty index. Refined queries are equivalent across paths; index node CIDs may differ.
- **Local-First, Databaseless Path**: Critical capture and query pathways run locally off content-addressed files, preventing dependencies on centralized database servers.
- **Gateway Projections**: Arxos acts as the canonical source of truth, projecting its object graph to standardized external formats (OpenUSD and IFC) while preserving object identities.
- **Contributor scoring**: Deterministic points reports from the data plane (`arxos_core::scoring`); fiat conversion is control-plane only.

---

## 3. Repository Layout

```
arxos/
├── core/           # arxos-core: CAS, roots, spatial index, scoring
├── ffi/            # UniFFI bindings (iOS RoomPlan bridge)
├── gateways/       # Interop translators
│   ├── usd/        # OpenUSD (USDA) ASCII
│   └── ifc/        # IFC4 STEP
├── networking/     # QUIC sync via Iroh
├── cli/            # arx CLI
├── ios/            # SwiftUI capture client
├── edge/           # Edge node packaging
├── archive/        # Historical material (not built)
│   └── contracts-evm-deprecated/
└── docs/           # Architecture, ADR, schema
```

---

## 4. Quick Start

### Build & Workspace Test

```bash
cargo build --release
cargo test --workspace --release
```

### CLI Ingestion & Query

```bash
export ARXOS_STORE=/tmp/arxos-store

# Initialize a new building repository
BID=$(cargo run -q -p arxos-cli -- --store "$ARXOS_STORE" building init --name "Main Hall" --quiet)

# Simulate RoomPlan-like capture and commit
cargo run -q -p arxos-cli -- --store "$ARXOS_STORE" capture simulate "$BID" --commit

# Query annotations near coordinates
cargo run -q -p arxos-cli -- --store "$ARXOS_STORE" building near "$BID" --x 1.2 --y 1.4 --z 1.1 --radius 5

# Diagnostic contributor scoring (not payment-grade)
cargo run -q -p arxos-cli -- --store "$ARXOS_STORE" score "$BID"
```

---

## 5. Capabilities & Limitations

| Capability | Technical Guarantee | Limitation / Out-of-Scope |
|------------|---------------------|---------------------------|
| **Data Integrity** | Content hashing (BLAKE3) guarantees tamper-evident storage. Roots fail closed on invalid signatures **and** unauthorized authors. | Signature key management is local; key recovery and rotation are out of scope. |
| **Commit Scalability** | Delta roots and $N=50$ checkpoints prevent linear root size growth. Incremental R-tree indexing updates in $O(\log N)$ time. | Distributed spatial indexing across multiple nodes is out of scope; queries are single-building local. |
| **Synchronization** | QUIC-based synchronization bounds payload transfer to the nearest checkpoint history. | Continual peer-to-peer data gossip or network-wide DHT queries are out of scope. |
| **Geometry Ingestion** | Decomposes RoomPlan matrices into normalized Pose vectors and projects tight World AABBs. | No general-purpose 3D rendering pipeline is provided; visual rendering belongs to external viewers. |
| **Interoperability** | USDA ASCII and IFC4 STEP text files are exported with deterministic global identity mapping from CIDs. | Complete IFC4 MEP schema support and native C++ OpenUSD bindings are out of scope. |
| **Commercial access / billing** | Designed as a separate control plane (ADR-001). | Not implemented in this repository yet. |

---

## 6. Documentation Map

- **ADR-001 (data vs control plane)**: [`docs/architecture/ADR-001-data-plane-vs-control-plane.md`](docs/architecture/ADR-001-data-plane-vs-control-plane.md)
- **Fiat-model audit**: [`docs/architecture/FIAT_MODEL_AUDIT.md`](docs/architecture/FIAT_MODEL_AUDIT.md)
- **Architecture Overview**: [`docs/architecture/ARCHITECTURE.md`](docs/architecture/ARCHITECTURE.md)
- **Object Schema Spec**: [`docs/schema/object-schema.md`](docs/schema/object-schema.md)
- **JSON Schemas**: [`docs/schema/`](docs/schema/)
- **Changelog**: [`CHANGELOG.md`](CHANGELOG.md)

---

## 7. License

Licensed under either of:
- Apache License, Version 2.0 (http://www.apache.org/licenses/LICENSE-2.0)
- MIT license (http://opensource.org/licenses/MIT)

at your option.
