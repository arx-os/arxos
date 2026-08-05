# arxos-core

The core library for the Arxos spatial data repository system (data plane).

## Responsibilities

- **Content Addressing**: Canonical CBOR serialization and BLAKE3 CID generation.
- **Object Schema**: Implements core types (Space, Surface, Equipment, BoundingVolume) and signature verification.
- **Root Management**: Handles delta roots, materialization walks, checkpoint policies, and sync closures.
- **Spatial Index**: Implements incremental R-tree index builds, query logic, and reachability garbage collection.
- **Repository**: Manages local BuildingRecord instances, WorkingSet staging, and memory-cached active object sets.
- **Scoring**: Deterministic contributor points reports (`scoring` module). Diagnostic only until multi-signal policy + control-plane ledger; never embeds fiat or accounts.

Money, KYC, billing, and entitlements live outside this crate (control plane). See ADR-001.

## Verification

Run the core unit and integration test suites:
```bash
cargo test -p arxos-core
```
