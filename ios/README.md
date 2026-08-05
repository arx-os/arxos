# Arxos iOS client

Physical iPhone capture client: **RoomPlan → ingest → auto-commit → CAS in Documents**.

## Requirements

- Full **Xcode** (not Command Line Tools only)
- Physical **LiDAR iPhone**, **iOS 17+**
- Rust with target: `rustup target add aarch64-apple-ios`

Point Xcode at the app install:

```bash
sudo xcode-select -s /Applications/Xcode.app/Contents/Developer
```

## 1. Build the iOS Rust library

From the **repo root**:

```bash
./ios/scripts/build-ios-lib.sh
```

Produces:

```text
ios/ArxosApp/Vendor/libarxos_core.a   # aarch64-apple-ios release staticlib
```

Also regenerate Swift bindings if the UniFFI surface changed:

```bash
cargo build -p arxos-ffi
./ios/Arxos/Scripts/generate_bindings.sh
```

## 2. Open and run the app

```bash
open ios/ArxosApp/ArxosApp.xcodeproj
```

In Xcode:

1. Select the **ArxosApp** target and your physical iPhone.
2. Set your **Team** under Signing & Capabilities (Automatic).
3. Build & Run (⌘R).

### Field loop

1. **Init** a building (or reopen last — restored automatically after force-quit).
2. **Start RoomPlan scan** → walk the room → **Stop**.
3. Ingest + **auto-commit** runs (status shows committed root).
4. Force-quit → reopen → same building and head.
5. **Export store…** (or Files → On My iPhone → Arxos → `arxos-store`) to a Mac.

## 3. Inspect on Mac CLI

After AirDrop / Files copy of the store folder (name may be `arxos-store-…`):

```bash
export ARXOS_STORE=/path/to/arxos-store   # directory that contains objects/ and meta/

cargo run -q -p arxos-cli -- --store "$ARXOS_STORE" building list
BID=…   # from list or from the phone UI

cargo run -q -p arxos-cli -- --store "$ARXOS_STORE" building status "$BID"
cargo run -q -p arxos-cli -- --store "$ARXOS_STORE" entity list "$BID"
cargo run -q -p arxos-cli -- --store "$ARXOS_STORE" entity show "$BID" <entity-id>
```

The store path on device is:

```text
Documents/arxos-store
```

(`UIFileSharingEnabled` is on so Finder can show it when the phone is connected.)

## Layout

```text
ios/
├── scripts/build-ios-lib.sh     # cross-compile aarch64-apple-ios
├── ArxosApp/                    # Xcode iOS application
│   ├── ArxosApp.xcodeproj
│   ├── Info.plist
│   └── Vendor/libarxos_core.a   # gitignored; rebuild with script
└── Arxos/                       # Shared Swift sources + UniFFI façade
    ├── Package.swift            # macOS demo / library only
    └── Sources/
        ├── ArxosApp/            # UI + RoomPlan
        ├── ArxosCore/           # UniFFI façade
        └── CArxosCoreFFI/       # C header + modulemap
```

## Notes

- **Simulate** is under Advanced — not the real RoomPlan path.
- RoomPlan owns the camera while scanning (AR overlay is paused).
- Dense mesh/point-cloud export from RoomPlan is out of scope for this loop; surfaces + objects become stable entities via `ingestRoomPlan`.
