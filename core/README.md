# arxos-core

Core library for the Arxos DePIN spatial data repository.

## Responsibilities

- **Content Addressing**: Canonical CBOR serialization and BLAKE3 CID generation.
- **Object Schema**: Space, Surface, Equipment, BoundingVolume, and signature verification.
- **Root Management**: Delta roots, materialization walks, checkpoint policies, sync closures.
- **Spatial Index**: Incremental R-tree builds, query, and related policies.
- **Repository**: BuildingRecord, WorkingSet, active object cache.
- **Scoring**: Deterministic contributor points reports (`scoring` module). Diagnostic type-count
  weights today — not a payment basis; never embeds fiat amounts in objects.

Settlement (buyers and contributors in **fiat**) is an economic layer outside this crate; see
[`docs/architecture/ADR-001-fiat-settled-depin.md`](../docs/architecture/ADR-001-fiat-settled-depin.md).

## Verification

```bash
cargo test -p arxos-core
```
