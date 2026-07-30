# Arxos

Arxos is a local-first, content-addressed spatial data repository system designed for the built environment. It enables versioned, verifiable, and databaseless representation of building geometry and annotations, mapping physical space captures directly to signed cryptographically linked state graphs.

---

## 1. Project Status

Arxos is foundation-complete for the core pipeline (local content-addressed store, RoomPlan geometry ingestion, delta root materialization, spatial query, multi-device synchronization, and gateway format export). It is an experimental codebase and is **not** a production-ready CAD platform, a finished consumer mobile app, or a deployed DePIN network.

### 1.1 Recently landed (integrity & structure)

| Area | Status |
|------|--------|
| Root **authorization** (`Building.controller_keys`) | Fail-closed on commit / adopt / merge; CLI uses the same verify path |
| **UniFFI** error surface (`ArxosError`) | Throwing APIs; no panics on ordinary store failures |
| **Fail-closed sync closures** | Incomplete object/index closures rejected unless `allow_partial` |
| CAS **index off put hot path** | Optional `index.cbor` rebuild-on-demand only |
| **Merge parents** on `RootBody` | Concurrent tips recorded; linear `previous_root` for materialization |
| **iOS real store only** | LocalStore / shim / `ALLOW_SHIM` removed; UniFFI → Rust CAS only |
| Module splits | `root/{auth,checkpoint,closure}`, `repository/{meta,commit,adopt,query}`, `spatial/index/{build,incremental,query}` |

Details: [`docs/architecture/ARCHITECTURE.md`](docs/architecture/ARCHITECTURE.md) §9 (status & roadmap pointers).

### 1.2 Sensible next increments (not started)

These are the highest-leverage follow-ons if you continue from this tree:

1. **Blob tiering** — externalize point-cloud / mesh bytes from object envelopes for mobile and edge sync.
2. **Spatial index hardening** — higher fanout / better splits; keep query-equivalence tests; optional index-root CID determinism if required for consensus.
3. **Store concurrency** — single-writer flock or local daemon so CLI + app + edge cannot corrupt head meta.
4. **Structured errors** — replace stringly `Error` payloads with typed variants for cleaner UniFFI mapping.
5. **Controller rotation & multi-device policy** — signed controller-set updates; bind Iroh identity to authors.
6. **On-chain / off-chain alignment** — clarify or bridge `BuildingRegistry` (EVM addresses) vs ed25519 controllers.
7. **CLI modularization** — split the monofile CLI into subcommand modules (structure only; behavior unchanged).

---

## 2. Core Concepts

- **Content-Addressed Objects**: Every piece of data is immutable and identified by a BLAKE3-256 content identifier (CID) computed over its canonical CBOR serialization.
- **Signed Delta Roots with Checkpoints**: Repository state transitions are defined by root commits. Intermediate commits serialize only delta additions and removals. A full-set checkpoint root is emitted every `CHECKPOINT_INTERVAL` (50) commits via a single policy module (`root::checkpoint`).
- **Authorized roots**: Every root author must be in `Building.controller_keys` (signatures alone are not enough).
- **Incremental Spatial Indexing**: A versioned binary spatial index is stored as content-addressed nodes. Day-to-day commits use path-copying inserts; full rebuild is used for merge/empty index. Refined queries are equivalent across paths; index node CIDs may differ.
- **Local-First, Databaseless Path**: Critical capture and query pathways run locally off content-addressed files, preventing dependencies on centralized database servers.
- **GATEWAY Projections**: Arxos acts as the canonical source of truth, projecting its object graph to standardized external formats (OpenUSD and IFC) while preserving object identities.

---

## 3. Repository Layout

```
arxos/
├── core/           # arxos-core (Rust): Object schema, CAS store, roots, and spatial index
├── ffi/            # arxos-ffi (Rust/UniFFI): Static FFI bindings and iOS RoomPlan bridge
├── gateways/       # Interoperability translators
│   ├── usd/        # arxos-usd: OpenUSD (USDA) ASCII gateway
│   └── ifc/        # arxos-ifc: IFC4 STEP gateway
├── networking/     # arxos-networking (Rust): QUIC-based sync protocol via Iroh nodes
├── cli/            # arx CLI: Administration, inspect, and local capture commands
├── ios/            # SwiftUI iOS app client: AR session & RoomPlan capture
├── edge/           # Edge node daemon and multi-arch Docker deployment packaging
└── contracts/      # BuildingRegistry EVM smart contract (Base L2)
```

---

## 4. Quick Start

### Build & Workspace Test
Build the workspace and run all automated test suites:
```bash
cargo build --release
cargo test --workspace --release
```

### CLI Ingestion & Query
Use the `arx` CLI to initialize a local repository, capture annotations, and query:
```bash
export ARXOS_STORE=/tmp/arxos-store

# Initialize a new building repository
BID=$(cargo run -q -p arxos-cli -- --store "$ARXOS_STORE" building init --name "Main Hall" --quiet)

# Simulate RoomPlan-like capture (Space, Point Cloud, and Annotations) and commit
cargo run -q -p arxos-cli -- --store "$ARXOS_STORE" capture simulate "$BID" --commit

# Query annotations near local camera coordinates [1.2, 1.4, 1.1]
cargo run -q -p arxos-cli -- --store "$ARXOS_STORE" building near "$BID" --x 1.2 --y 1.4 --z 1.1 --radius 5
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

---

## 6. Documentation Map

- **Architecture Overview**: [`docs/architecture/ARCHITECTURE.md`](docs/architecture/ARCHITECTURE.md)
  - Full details on data layouts, R-tree indexing, caching mechanisms, RoomPlan coordinate conversion, and sync protocols.
- **Object Schema Spec**: [`docs/schema/object-schema.md`](docs/schema/object-schema.md)
  - Structure of headers, envelope types, and JSON Schemas.
- **JSON Schemas**:
  - Object envelope: [`docs/schema/object-envelope.schema.json`](docs/schema/object-envelope.schema.json)
  - Root body envelope: [`docs/schema/root-body.schema.json`](docs/schema/root-body.schema.json)

---

## 7. License

Licensed under either of:
- Apache License, Version 2.0 (http://www.apache.org/licenses/LICENSE-2.0)
- MIT license (http://opensource.org/licenses/MIT)

at your option.
