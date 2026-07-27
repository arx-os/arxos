# Arxos iOS Client

Lived-experience capture client: ARKit / RoomPlan → content-addressed objects → signed Root.

## Phase 1 capabilities

* Init / open / list building repositories (local CAS)
* Capture **Space**, **PointCloudChunk**, **Annotation** at camera pose
* **Mock / simulate** scan without LiDAR (Simulator + macOS demo)
* **RoomPlan** path on device (iOS 16+, non-Simulator)
* Commit pending captures → new signed Root; reload same building
* AR overlay of **annotation labels only** (no general 3D model viewer)

## Layout

```
ios/Arxos/
├── Package.swift
├── Scripts/generate_bindings.sh
└── Sources/
    ├── ArxosCore/       # UniFFI façade + local shim
    ├── ArxosApp/        # SwiftUI + AR + capture session
    └── ArxosDemo/       # CLI smoke test for capture loop
```

## Quick check (no device)

```bash
cd ios/Arxos
swift run ArxosDemo
# → Phase 1 demo OK
```

## Device (LiDAR)

1. Create an Xcode iOS App target that depends on `ArxosApp` + `ArxosCore`.
2. Build Rust with UniFFI and link the static library / XCFramework:

   ```bash
   cargo build -p arxos-core --features uniffi --release
   ./ios/Arxos/Scripts/generate_bindings.sh
   ```

3. Run on a LiDAR-capable iPhone. Use **Simulate RoomPlan scan** when hardware capture is unavailable.

## Architecture notes

* Production path: Swift → UniFFI → `arxos-core` (`BuildingRepository`).
* Shim path: pure-Swift `LocalStore` for UI compile / demo without native lib (not BLAKE3-identical).
* Geometry from RoomPlan is stored as data (`PointCloudChunk`); visualization of full meshes is out of scope (USD in Phase 4).
