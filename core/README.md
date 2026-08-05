# arxos-core

Core library for Arxos: local-first content-addressed as-built repository.

## Responsibilities

- **Content addressing**: Canonical CBOR + BLAKE3 CIDs
- **Object schema**: Building, Floor, Space, Equipment, Annotation, … + signatures
- **Roots**: Delta commits, checkpoints, materialization, sync closures, controller auth
- **Spatial index**: Versioned R-tree as ordinary CAS objects
- **Repository**: Building head, working set, capture/commit
- **Scoring**: Deterministic contributor points (diagnostic; fiat settlement is off-band)

See the root [README](../README.md) for product identity, architecture, and Phase-0 boundaries.

## Verification

```bash
cargo test -p arxos-core
```
