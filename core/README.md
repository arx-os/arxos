# arxos-core

The core library for the Arxos spatial data repository system.

## Responsibilities

- **Content Addressing**: Canonical CBOR serialization and BLAKE3 CID generation.
- **Object Schema**: Implements core types (Space, Surface, Equipment, BoundingVolume) and signature verification.
- **Root Management**: Handles delta roots, materialization walks, checkpoint policies, and sync closures.
- **Spatial Index**: Implements incremental R-tree index builds, query logic, and reachability garbage collection.
- **Repository**: Manages local BuildingRecord instances, WorkingSet staging, and memory-cached active object sets.

## Verification

Run the core unit and integration test suites:
```bash
cargo test -p arxos-core
```
