# Arxos

Arxos is a **DePIN for the built environment**: a local-first, content-addressed spatial data repository for capturing, versioning, verifying, and scoring real-world building geometry and annotations. Physical space captures map to signed, cryptographically linked state graphs.

---

## 1. Project Status

Arxos is foundation-complete for the core pipeline (local content-addressed store, RoomPlan geometry ingestion, delta root materialization, spatial query, multi-device synchronization, and gateway format export). It is an experimental codebase and is **not** a production-ready CAD platform or finished consumer mobile app.

### 1.1 Economic model (DePIN, fiat settlement)

The technical architecture remains contribution → verification → **scoring**. The economic settlement layer is **fiat**, not tokens:

| Role | Economics |
|------|-----------|
| **Data buyers** | Pay **fiat** for access to data and derived products. |
| **Contributors** | Submit real-world building/spatial data; scoring produces **points** / reputation signals. |
| **Rewards** | Contributors are paid in **fiat** according to scored value (ops-controlled; off-band). |
| **Tokens / chain** | **None.** No minting, wallets, or blockchain settlement of rewards. |

See [`docs/architecture/ADR-001-fiat-settled-depin.md`](docs/architecture/ADR-001-fiat-settled-depin.md).

**Scoring today is diagnostic only** (`arx score`). Do not treat type-count scores as a payment basis.

### 1.2 Recently landed (integrity & structure)

| Area | Status |
|------|--------|
| Root **authorization** (`Building.controller_keys`) | Fail-closed on commit / adopt / merge |
| **UniFFI** error surface (`ArxosError`) | Throwing APIs; no panics on ordinary store failures |
| **Fail-closed sync closures** | Incomplete closures rejected unless `allow_partial` |
| CAS **index off put hot path** | Optional `index.cbor` rebuild-on-demand only |
| **Merge parents** on `RootBody` | Concurrent tips recorded |
| **iOS real store only** | UniFFI → Rust CAS only |
| **P0 crypto→fiat course correction** | EVM contracts archived; `depin` → `scoring`; CLI `score` / `verify` / `attest` |

Details: [`docs/architecture/ARCHITECTURE.md`](docs/architecture/ARCHITECTURE.md) §9.

### 1.3 Sensible next increments

1. **Multi-signal scoring** — depth, coverage, attestation, review (still points/reputation in core).  
2. **Blob tiering** — externalize point-cloud / mesh bytes for mobile and edge sync.  
3. **Spatial index hardening** — higher fanout / better splits; keep query-equivalence tests.  
4. **Store concurrency** — single-writer flock or local daemon.  
5. **Structured errors** — typed variants for cleaner UniFFI mapping.  
6. **Controller rotation & multi-device policy** — signed controller-set updates.  
7. **CLI modularization** — split the monofile CLI into subcommand modules.

---

## 2. Core Concepts

- **Content-Addressed Objects**: Immutable data identified by BLAKE3-256 CIDs over canonical CBOR.
- **Signed Delta Roots with Checkpoints**: Repository commits with delta adds/removes; full-set checkpoints every `CHECKPOINT_INTERVAL` (50).
- **Authorized roots**: Authors must be in `Building.controller_keys`.
- **Incremental Spatial Indexing**: Versioned R-tree as content-addressed nodes.
- **Local-First, Databaseless Path**: Capture and query run on local CAS files.
- **Gateway Projections**: OpenUSD and IFC export/import with identity preserved.
- **Contributor scoring**: Deterministic points reports (`arxos_core::scoring`) for DePIN contribution attribution; fiat settlement is off-band.

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

```bash
cargo build --release
cargo test --workspace --release
```

```bash
export ARXOS_STORE=/tmp/arxos-store

BID=$(cargo run -q -p arxos-cli -- --store "$ARXOS_STORE" building init --name "Main Hall" --quiet)
cargo run -q -p arxos-cli -- --store "$ARXOS_STORE" capture simulate "$BID" --commit
cargo run -q -p arxos-cli -- --store "$ARXOS_STORE" building near "$BID" --x 1.2 --y 1.4 --z 1.1 --radius 5
cargo run -q -p arxos-cli -- --store "$ARXOS_STORE" score "$BID"
```

---

## 5. Capabilities & Limitations

| Capability | Technical Guarantee | Limitation / Out-of-Scope |
|------------|---------------------|---------------------------|
| **Data Integrity** | BLAKE3 CIDs; fail-closed root auth | Key recovery/rotation out of scope |
| **Commit Scalability** | Delta roots + N=50 checkpoints; O(log N) index updates | Multi-building distributed spatial index out of scope |
| **Synchronization** | Bounded pull to nearest checkpoint | Global DHT gossip out of scope |
| **Geometry Ingestion** | RoomPlan matrices → pose / AABB | No built-in 3D renderer |
| **Interoperability** | USDA / IFC4 with CID identity | Full MEP IFC / native C++ USD out of scope |
| **Settlement** | Scores support fiat rewards (off-band) | No token mint; no in-repo billing product |

---

## 6. Documentation Map

- **ADR-001 (fiat-settled DePIN)**: [`docs/architecture/ADR-001-fiat-settled-depin.md`](docs/architecture/ADR-001-fiat-settled-depin.md)
- **Architecture Overview**: [`docs/architecture/ARCHITECTURE.md`](docs/architecture/ARCHITECTURE.md)
- **Object Schema Spec**: [`docs/schema/object-schema.md`](docs/schema/object-schema.md)
- **Changelog**: [`CHANGELOG.md`](CHANGELOG.md)

---

## 7. License

Licensed under either of:
- Apache License, Version 2.0 (http://www.apache.org/licenses/LICENSE-2.0)
- MIT license (http://opensource.org/licenses/MIT)

at your option.
