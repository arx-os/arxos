# Arxos

A local-first record of the built world.

Contributors commit **Facts** (tiny signed geometric claims). The official building is a state map \(S\) from names to primitives; owners fuse rescans, realize solids, and project IFC / USD / ASCII. Arxos is not a renderer and does not store a scan file as the building.

Walk a site with a LiDAR iPhone. The phone is a camera that mints Facts into a local CAS. Copy that store to a machine to inspect it, export IFC or USD, or pull it onto another replica. There is no cloud in the loop.

## How it works

Field contributors write the as-built record at the wall.

1. **Capture.** A phone, laptop, or edge node mints Facts (walls, openings, equipment, notes). Point clouds and meshes may be evidence; they are not \(B = R(S)\).
2. **Commit / fuse.** Each object is an immutable file named by a hash of its contents. A second walk of the same `EntityId` fuses into one live version. Controllers — keys on the Building object — commit, adopt, and merge.
3. **Replicate.** Another machine pulls a Root over the LAN (Iroh + mDNS) or receives the store folder. Official history is whoever those controller keys accept.
4. **Realize / project.** \(B = R(S)\) is oriented boxes. Export IFC or USD, or `arx building slice` for an ASCII floor plan. There is no product 3D viewport.

One process writes a given store at a time. Extra work is just another Root CID. There is no proposal type.

## DePIN and rewards

Arxos is the data plane for a physical network: people and devices in the field writing as-built truth, not a token mint.

- **Field contributors** capture and sign what they see. Attribution follows the key on the object or Root.
- **Scoring** (`arx score`) is deterministic. Given the same store, Root, and policy, everyone gets the same points report. Points measure contribution; they are not money.
- **Settlement is fiat, off-band.** Ops can pay contributors from those scores. This repo never embeds currency in CIDs and does not mint a token.

Today scoring is diagnostic (type-count weights plus a signed-object bonus). Do not treat it as a payroll number until multi-signal quality scoring is intentional product work.

## What works today

- Capture on a LiDAR iPhone (RoomPlan) or with `arx capture simulate` (wall Facts, σ = 40 mm)
- Inspect the head, list entities (extent / σ / support), diagnostic scoring (`arx score`)
- Fuse on commit: same Apple UUID / `EntityId` updates the wall instead of stacking walls
- Realize solids and project IFC (`IFCWALL`), USD (cube prims), ASCII (`arx building slice`)
- LAN pull over Iroh (`arxos/sync/1`) and mDNS (no public relays by default); long-running `arxos-edge serve`
- Merge concurrent controller tips (entity conflicts fuse)

Not built: accounts, an HTTP site, a public directory, or an inbox for
non-controllers. A non-controller cannot commit official history
(`arx building add-controller`).

## Quick start

Rust 1.91+ and Cargo.

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

Init a building, start a RoomPlan scan, stop. Facts are ingested and
auto-committed into Application Support (`arxos-store`, excluded from backup).
Use **Export store…** to AirDrop a snapshot to a Mac and point `arx` at it with
`--store`. The app is a camera that mints Facts, not a scan-file folder as the
happy path. Details: [ios/README.md](ios/README.md).

## Pull and merge

Serve prints a ticket and advertised heads, and holds `store.lock`:

```bash
cargo run -q -p arxos-cli -- --store "$ARXOS_STORE" net serve
```

Default fetch adopts the pulled Root (first contact is TOFU unless you pin
`--trust-controllers`; later pulls must fast-forward from this replica’s head):

```bash
cargo run -q -p arxos-cli -- --store "$OTHER" net fetch --peer "$TICKET" --root "$CID"
# pin a second replica: --trust-controllers "$ALICE_PK"
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

`arx import usd` / `arx import ifc` write a new signed Root and adopt it as head
(requires `keys/device.seed`).

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

Apache-2.0 or MIT, at your option (`LICENSE` and `LICENSE-APACHE`).
