# Phase 0 — Foundation (complete)

**Date:** 2026-07-27

## Deliverables

| Item | Location |
|------|----------|
| Monorepo structure | repo root |
| Object + Header + CBOR + BLAKE3 CID | `core/src/{object,canonical,cid}.rs` |
| Local CAS store | `core/src/store/` |
| Root + ed25519 sign/verify | `core/src/{root,crypto}/` |
| UniFFI skeleton | `core/src/arxos.udl`, feature `uniffi` |
| SwiftUI shell + hello | `ios/Arxos/` |
| CLI | `cli/` → binary `arx` |
| Object schema docs | `docs/schema/` |

## Verify

```bash
cargo test --workspace
cargo build -p arxos-core --features uniffi
cargo run -p arxos-cli -- version

# CLI vertical slice
export ARXOS_STORE=/tmp/arxos-demo
SEED=$(cargo run -q -p arxos-cli -- key generate | sed -n 's/^seed=//p')
cargo run -q -p arxos-cli -- --store "$ARXOS_STORE" object put --type annotation --text "note" --sign-seed "$SEED"
cargo run -q -p arxos-cli -- --store "$ARXOS_STORE" root create --building-id 01DEMO --all --seed "$SEED" --message init

cd ios/Arxos && swift run ArxosDemo
# → Hello, iOS — Arxos core 0.1.0
```

## Out of scope (later phases)

- ARKit / RoomPlan / LiDAR (Phase 1)
- Iroh networking (Phase 2)
- Spatial index construction (Phase 3)
- USD / IFC (Phase 4)
- DePIN registry (Phase 5)
