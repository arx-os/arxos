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

## 1. Prepare iOS artifacts (required before Xcode)

From the **repo root**, run the single prep script:

```bash
./ios/scripts/prep.sh
```

This:

1. Builds `arxos-ffi` (host)
2. Regenerates UniFFI Swift bindings (`ios/Arxos/Sources/ArxosCore/Generated/`)
3. Cross-compiles `ios/ArxosApp/Vendor/libarxos_core.a` (`aarch64-apple-ios`)
4. Writes `ios/ArxosApp/Vendor/BUILD_ID` (git rev + UDL hash)

**Xcode fails closed** if generated Swift is missing or older than `ffi/src/arxos.udl`
(Run Script phase → `ios/scripts/check-bindings.sh`). Bindings stay gitignored
(generated-only); always run `prep.sh` on a fresh clone or after UDL changes.

Lower-level scripts (usually unnecessary):

```bash
./ios/Arxos/Scripts/generate_bindings.sh   # bindings only
./ios/scripts/build-ios-lib.sh             # staticlib only
./ios/scripts/check-bindings.sh            # verify freshness
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
├── scripts/
│   ├── prep.sh                  # one-shot: bindings + lib + BUILD_ID
│   ├── check-bindings.sh        # fail closed if bindings stale (Xcode)
│   └── build-ios-lib.sh         # cross-compile aarch64-apple-ios only
├── ArxosApp/                    # Xcode iOS application
│   ├── ArxosApp.xcodeproj
│   ├── Info.plist
│   └── Vendor/libarxos_core.a   # gitignored; rebuild with prep.sh
└── Arxos/                       # Shared Swift sources + UniFFI façade
    ├── Package.swift            # macOS demo / library only
    └── Sources/
        ├── ArxosApp/            # UI + RoomPlan
        ├── ArxosCore/           # UniFFI façade + Generated/ (gitignored)
        └── CArxosCoreFFI/       # C header + modulemap
```

## Notes

- **Simulate** is under Advanced — not the real RoomPlan path.
- RoomPlan owns the camera while scanning (AR overlay is paused).
- Dense mesh/point-cloud export from RoomPlan is out of scope for this loop; surfaces + objects become stable entities via `ingestRoomPlan`.
