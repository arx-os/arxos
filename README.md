# Arxos

Local-first content-addressed repository for as-built building data.

Arxos stores building geometry and annotations as immutable objects in a local
content-addressed store (CAS). Each object is addressed by a BLAKE3 CID over
canonical CBOR. Version history is recorded as signed **Roots** (commits) for a
building. Devices capture offline, then exchange state by pulling root closures
over the network. There is no required cloud service.

## Core concepts

**Objects.** Typed records (buildings, spaces, surfaces, equipment, annotations,
point clouds, meshes, and others) with a header and body. Cross-references are
CIDs. Physical entities may also carry a stable `EntityId`; updates create new
object versions, and commit/merge keep at most one version per entity in the
active set.

**Roots.** A Root is a signed commit for one building. Most commits are deltas
(`added` / `removed` CIDs); a full-set checkpoint is written periodically so
history walks stay bounded. Only keys listed in `Building.controller_keys` may
sign Roots that advance the head (fail closed).

**Local store.** Objects live under a directory of content-addressed files. A
small metadata file holds each building’s head pointer. A single-writer lock
guards concurrent repository writes on the same path. Who may read or write the
CAS is defined in the [store contract](core/README.md#store-contract).

**Sync.** Peers advertise and pull root closures (Iroh QUIC, optional mDNS on
the LAN). Bytes are verified by CID; adopting a remote head reuses the same
authorization rules as local commit.

**Interop.** Optional gateways project a building head to OpenUSD (USDA) or a
limited IFC4 STEP subset, preserving Arxos identity metadata.

## Quick start

Requires Rust 1.75+ and Cargo.

```bash
export ARXOS_STORE=/tmp/arxos-store

# Create a building (prints building_id)
BID=$(cargo run -q -p arxos-cli -- --store "$ARXOS_STORE" building init --name "Main Hall" --quiet)

# Simulated capture and commit
cargo run -q -p arxos-cli -- --store "$ARXOS_STORE" capture simulate "$BID" --commit

# Inspect
cargo run -q -p arxos-cli -- --store "$ARXOS_STORE" building status "$BID"
cargo run -q -p arxos-cli -- --store "$ARXOS_STORE" entity list "$BID"
cargo run -q -p arxos-cli -- --store "$ARXOS_STORE" building near "$BID" --x 1 --y 1 --z 1 --radius 5
```

Useful `arx` commands (full list: `cargo run -p arxos-cli -- --help`):

- **Building:** `building init`, `list`, `show`, `status`, `commit`, `near`
- **Capture:** `capture simulate`, `annotation`, `space`, `point-cloud`
- **Entities:** `entity list`, `show`, `remove`
- **Merge / roots:** `merge plan`, `merge apply`, `root show`
- **Export:** `export usd`, `export ifc`
- **Network:** `net serve`, `net fetch --peer <ticket> --root <cid>`, `net peers`
- **Checks:** `verify`, `score`

Default store path is `.arxos/store` (or `ARXOS_STORE`). Store layout:

```text
$ARXOS_STORE/
  objects/…              # CAS (fan-out by CID hex)
  meta/buildings/…       # head pointers
  keys/device.seed       # local ed25519 seed
  store.lock             # exclusive writer lock
```

Serve a store for peers (holds the writer lock until Ctrl-C):

```bash
cargo run -p arxos-cli -- --store "$ARXOS_STORE" net serve
# or: cargo run -p arxos-edge -- --store "$ARXOS_STORE" serve
```

## Repository layout

```text
core/           # CAS, objects, roots, spatial index, capture helpers, scoring
cli/            # arx command-line tool
networking/     # Iroh + mDNS pull sync
edge/           # long-running edge serve helper
gateways/       # OpenUSD and IFC projections
ffi/            # UniFFI surface for iOS
ios/            # iPhone capture app
archive/        # historical material (not built)
```

## Building and testing

```bash
cargo build --release
cargo test --workspace
```

## iOS capture

The `ios/` tree is a RoomPlan capture client that writes into the same CAS via
UniFFI. It needs full Xcode, a LiDAR iPhone, and iOS 17+. From the repo root:

```bash
./ios/scripts/prep.sh
open ios/ArxosApp/ArxosApp.xcodeproj
```

After a scan, the store under the app’s Documents folder can be copied to a Mac
and inspected with `arx --store … building status` / `entity list`. See
[ios/README.md](ios/README.md) for details.

## License

Licensed under either of:

- [Apache License, Version 2.0](http://www.apache.org/licenses/LICENSE-2.0)
- [MIT license](http://opensource.org/licenses/MIT)

at your option.
