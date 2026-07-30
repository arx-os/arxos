# Arxos iOS Client

Capture client for iOS: ARKit / RoomPlan scans into signed content-addressed repositories via UniFFI → Rust `arxos-core`.

## Single data path

There is **no** Swift-side fake CAS. All store operations go through UniFFI to the real Rust core and throw `ArxosError` on failure (authorization, missing building, validation, …).

## Layout

```
ios/Arxos/
├── Package.swift
├── Scripts/generate_bindings.sh
└── Sources/
    ├── CArxosCoreFFI/   # UniFFI C header + module map
    ├── ArxosCore/       # Generated bindings + throwing Swift façade
    ├── ArxosApp/        # SwiftUI / ARKit / RoomPlan
    └── ArxosDemo/       # CLI smoke test (requires linked libarxos_core)
```

## Build the native library + bindings

```bash
# From repo root
cargo build -p arxos-ffi --release
./ios/Arxos/Scripts/generate_bindings.sh
```

## Run the demo (macOS, real store)

```bash
cargo build -p arxos-ffi   # produces target/debug/libarxos_core.a
cd ios/Arxos
swift run ArxosDemo
```

`Package.swift` links `libarxos_core` from `../../target/release` or `../../target/debug`.

## Production device builds

1. `cargo build -p arxos-ffi --release` (iOS target triple as needed)
2. `./ios/Arxos/Scripts/generate_bindings.sh`
3. Link the static library into the Xcode app target and run on a LiDAR-capable device.

## Error handling

Swift call sites must use `do/catch` (or `try`). Ordinary core failures surface as `ArxosError` — they must not crash the process.
