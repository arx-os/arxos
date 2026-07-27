# Arxos iOS Client (Phase 0)

SwiftUI shell that exercises the Rust core via UniFFI.

## Phase 0 scope

* Blank SwiftUI app
* Call `ArxosCore.hello(name:)` from the Rust core
* No AR / LiDAR yet (Phase 1)

## Layout

```
ios/
├── README.md
├── Arxos/
│   ├── Package.swift          # local Swift package (bindings + UI target)
│   ├── Sources/
│   │   ├── ArxosApp/          # SwiftUI app
│   │   └── ArxosCore/         # UniFFI-generated (or hand shim) Swift
│   └── Scripts/
│       └── generate_bindings.sh
```

## Generate UniFFI Swift bindings

From the monorepo root (requires Rust toolchain):

```bash
# Build core with UniFFI feature
cargo build -p arxos-core --features uniffi

# Generate Swift bindings into ios package
./ios/Arxos/Scripts/generate_bindings.sh
```

## Run (SwiftPM)

```bash
cd ios/Arxos
swift build
# On macOS, the demo executable prints the hello string:
swift run ArxosDemo
```

For a full Xcode + device AR workflow, Phase 1 will add an `.xcodeproj` / XcodeGen spec and XCFramework packaging of `arxos_core`.

## Expected Phase 0 output

```
Hello, iOS — Arxos core 0.1.0
```
