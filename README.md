# Arxos

A local-first store for as-built building data.

Walk a room with a LiDAR iPhone. Arxos writes what you captured to a folder on
the device. Copy that folder to a Mac to inspect it, export IFC or USD, or pull
it onto another machine. There is no cloud in the loop.

## How it is stored

Each object is an immutable file named by a hash of its contents. A building’s
history is a chain of signed Roots. Each replica has one official head
(`BuildingRecord.head_root`). Controllers — keys on the Building object — may
commit, adopt, and merge. Extra work is a Root CID. There is no proposal type.

One process writes a given store at a time.

## What works today

- Capture on a LiDAR iPhone (RoomPlan) or with `arx capture`
- Inspect the head, list entities, diagnostic scoring (`arx score`)
- LAN pull over Iroh (`arxos/sync/1`) and mDNS; long-running `arxos-edge serve`
- Merge concurrent controller tips
- USD and IFC export from the current head; import writes a new commit

Not built: accounts, an HTTP site, a public directory, or an inbox for
non-controllers. A non-controller cannot commit official history
(`arx building add-controller`).

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
cargo build --release && cargo test --workspace
```

## iPhone

LiDAR iPhone, iOS 17+, full Xcode (not Command Line Tools).

```bash
./ios/scripts/prep.sh
open ios/ArxosApp/ArxosApp.xcodeproj
```

Init a building, start a RoomPlan scan, stop. The app commits into
`Documents/arxos-store`. AirDrop or copy that folder to a Mac and point `arx`
at it with `--store`. The app is a replica with a camera, not a browser;
network pull is not wired in the UI. Details: [ios/README.md](ios/README.md).

## Pull and merge

Serve prints a ticket and advertised heads, and holds `store.lock`:

```bash
cargo run -q -p arxos-cli -- --store "$ARXOS_STORE" net serve
```

Default fetch adopts the pulled Root (first contact is TOFU; later pulls must
fast-forward from this replica’s head):

```bash
cargo run -q -p arxos-cli -- --store "$OTHER" net fetch --peer "$TICKET" --root "$CID"
```

`--no-set-head` stores the objects and leaves `head_root` unchanged. Merge the
printed CID by hand:

```bash
cargo run -q -p arxos-cli -- --store "$OTHER" net fetch --peer "$TICKET" --root "$CID" --no-set-head
cargo run -q -p arxos-cli -- --store "$OTHER" merge apply "$BID" "$CID"
```

Long-running: `arxos-edge --store /var/lib/arxos/store serve`
([edge/README.md](edge/README.md)).

## Export

Exports project the current head. USD is the geometry export. IFC is a narrow
building / floor / space / notes file with identity metadata, not a certified
CoordinationView.

```bash
cargo run -q -p arxos-cli -- --store "$ARXOS_STORE" export usd "$BID" -o building.usda
cargo run -q -p arxos-cli -- --store "$ARXOS_STORE" export ifc "$BID" -o building.ifc
```

`arx import usd` / `arx import ifc` write a new Root and adopt it as head.

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

## Store contract

Writes, adopt, and ingest: [core/README.md](core/README.md).

## License

Apache-2.0 or MIT, at your option.
