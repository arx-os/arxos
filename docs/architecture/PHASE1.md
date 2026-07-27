# Phase 1 — Mobile Capture Loop

**Status:** Implemented (2026-07-27)

## Goals

* iOS AR session + LiDAR / RoomPlan ingestion path
* Create `PointCloudChunk` + `Space` + `Annotation` objects on device
* Local working set + commit → new Root
* Persist and reload a building on the same device
* Simple AR overlay of annotations (not a general 3D viewer)

## Design decisions

1. **Rust owns the capture → object boundary.**  
   `capture/`, `working_set/`, `repository/` in `arxos-core` are pure and unit-tested without a phone.

2. **Building head is not a database.**  
   `<store>/meta/buildings/<id>.cbor` stores `head_root`, `pending` CIDs, and name only.

3. **Pending survives process boundaries.**  
   UniFFI is call-oriented; each capture appends to durable `pending` so a later `commit` works after reopen.

4. **Partial materialization.**  
   `WorkingSet` caches staged + pinned objects with a soft cap; AR queries only annotations near the camera.

5. **No general 3D rendering.**  
   RoomPlan/mesh data becomes `PointCloudChunk` / future USD export. AR shows annotation billboards only.

6. **Simulator / CI path.**  
   `arx capture simulate` and Swift `ArxosDemo` exercise the full loop without LiDAR.

## Commands

```bash
export ARXOS_STORE=/tmp/arxos-p1
cargo run -q -p arxos-cli -- --store "$ARXOS_STORE" building init --name "Hall"
# → building_id=...

cargo run -q -p arxos-cli -- --store "$ARXOS_STORE" capture simulate "$BID" --commit
cargo run -q -p arxos-cli -- --store "$ARXOS_STORE" building show "$BID"
cargo run -q -p arxos-cli -- --store "$ARXOS_STORE" building near "$BID" --x 1.2 --y 1.4 --z 1.1
```

## iOS

```bash
cd ios/Arxos && swift run ArxosDemo
```

Device: open `Sources/ArxosApp` in Xcode, link UniFFI XCFramework (`cargo build -p arxos-core --features uniffi` + bindgen), run on LiDAR hardware. Use **Simulate RoomPlan scan** without hardware.

## Tests

* `repository::tests::init_capture_commit_reload`
* `working_set::tests::stage_and_near_query`
* `capture::tests::*`
* CLI vertical slice (manual / CI script)
* `swift run ArxosDemo`

## Next (Phase 2)

Iroh publish/fetch of Root + objects; multi-device pull; mDNS.
