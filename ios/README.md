# Arxos iOS Client

The capture client façade for iOS, bridging ARKit / RoomPlan scans to signed content-addressed repositories.

## Capabilities

* Create, open, and list building repositories locally.
* Capture Spaces, PointCloudChunks, and Annotations at the device's camera pose.
* **Simulator Integration**: Ingest mock scans for development on macOS or Xcode Simulator.
* **RoomPlan Ingestion**: Convert wall, floor, ceiling, and object dimensions to canonical domain models using matrix transformations.
* Commit working-set changes to local signed Roots.
* Render AR annotation overlays relative to real-world coordinate frames.

## Layout

```
ios/Arxos/
├── Package.swift
├── Scripts/generate_bindings.sh
└── Sources/
    ├── ArxosCore/       # Swift UniFFI gateway and gated debug shim
    ├── ArxosApp/        # SwiftUI, ARKit, and RoomPlan capture pipelines
    └── ArxosDemo/       # CLI verification tool for the capture loop
```

## Quick Check (macOS / Simulator)

Run the local façade smoke test:
```bash
cd ios/Arxos
swift run -Xswiftc -DALLOW_SHIM ArxosDemo
```

## Production Device Builds

1. Compile the Rust static library FFI gateway:
   ```bash
   cargo build -p arxos-ffi --release
   ```
2. Generate the Swift bindings:
   ```bash
   ./ios/Arxos/Scripts/generate_bindings.sh
   ```
3. Open `ios/Arxos` or embed it in an iOS App project, linking the compiled static library, and run on a LiDAR-capable iOS device.
