# Arxos

A local store for as-built buildings.

Walk a room with a LiDAR iPhone. Arxos writes what you captured to a folder on
the device. Copy that folder to a Mac to inspect it, export IFC or USD, or pull
it onto another machine. There is no cloud in the loop.

Each object is an immutable file named by a hash of its contents. A building’s
history is a chain of signed commits. One process writes a given store at a
time.

## Quick start

Rust 1.75+ and Cargo.

```bash
export ARXOS_STORE=/tmp/arxos-store

BID=$(cargo run -q -p arxos-cli -- --store "$ARXOS_STORE" building init --name "Main Hall" --quiet)

cargo run -q -p arxos-cli -- --store "$ARXOS_STORE" capture simulate "$BID" --commit
cargo run -q -p arxos-cli -- --store "$ARXOS_STORE" building status "$BID"
cargo run -q -p arxos-cli -- --store "$ARXOS_STORE" entity list "$BID"
```

Default store path is `.arxos/store`. `cargo run -p arxos-cli -- --help` lists
the rest of `arx`.

```bash
cargo build --release
cargo test --workspace
```

The store contract lives in [core/README.md](core/README.md).

## iPhone capture

LiDAR iPhone, iOS 17+, full Xcode (not Command Line Tools).

```bash
./ios/scripts/prep.sh
open ios/ArxosApp/ArxosApp.xcodeproj
```

Init a building, start a RoomPlan scan, stop. The app commits into
`Documents/arxos-store`. AirDrop or copy that folder to a Mac and point `arx`
at it with `--store`. Details: [ios/README.md](ios/README.md).

## Layout

```text
core/         store, objects, commits
cli/          arx
ios/          iPhone capture app
ffi/          UniFFI bindings
networking/   LAN pull (Iroh)
edge/         long-running serve
gateways/     IFC and USD export
```

## License

Apache-2.0 or MIT, at your option.
