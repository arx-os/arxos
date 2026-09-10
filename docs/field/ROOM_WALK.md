# Room walk — two stops, fused walls

Operator checklist for a real LiDAR walk. Simulate-on-laptop is not this test.

**Goal:** two RoomPlan stops in the same room, same Apple UUIDs, one wall in \(S\), `support=2`, pose pulled toward the tighter \(\sigma\). Unresolved openings stay unhosted.

Arxos does not invent Apple identifiers. If RoomPlan issues a new UUID on the second stop, fuse will not collapse those walls — that is Apple, not an Arxos bug.

There is no product 3D viewer. Debug with `entity list`, `building slice`, and `export ifc`. Folder copy of the store is disaster recovery, not this loop.

---

## 1. Edge: init, serve, print URI

Laptop / site box. One writer. Do not enable public Iroh relays.

```bash
export ARXOS_STORE="$HOME/arxos-store"   # directory that will contain objects/ and meta/
mkdir -p "$ARXOS_STORE"

BID=$(cargo run -q -p arxos-cli -- --store "$ARXOS_STORE" building init --name "Site Walk" --quiet)
PK=$(cargo run -q -p arxos-cli -- --store "$ARXOS_STORE" building controllers "$BID" | awk '/^  /{print $1; exit}')

# Leave this running. Apply goes through $ARXOS_STORE/meta/serve.sock — do not restart serve.
cargo run -q -p arxos-cli -- --store "$ARXOS_STORE" net serve
```

Serve prints `ticket=…` (Iroh dial ticket) and `ctl_sock=…`. Build the join URI (name is discovery; trust is the pinned controller key, not DNS/IP):

```text
arx://bldg/<BID>?controllers=<PK>&inbox=<TICKET>
```

Copy that string to the phone.

---

## 2. Phone: prep, join, first scan

LiDAR iPhone, iOS 17+, full Xcode (not Command Line Tools).

```bash
export DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer
sudo xcode-select -s /Applications/Xcode.app/Contents/Developer
./ios/scripts/prep.sh
open ios/ArxosApp/ArxosApp.xcodeproj
```

On device:

1. Init is **not** required if you joined the edge building. Paste the `arx://` URI (or the raw ticket) into **Join**. Pins persist across force-quit.
2. Start RoomPlan. Walk the room slowly. Stop.
3. Status should read **facts pushed, pending apply** when a ticket is saved. **local only (no ticket)** means the phone committed locally for force-quit safety — that is not this loop. **Export store…** is Advanced/debug.

---

## 3. Edge: apply while serve stays up

Do not Ctrl-C serve. In a second terminal:

```bash
cargo run -q -p arxos-cli -- --store "$ARXOS_STORE" inbox list "$BID"
cargo run -q -p arxos-cli -- --store "$ARXOS_STORE" inbox apply "$BID"
```

Apply is a controller commit through the serve socket. `head_root` moves here, not on push.

---

## 4. Note EntityIds and support

```bash
cargo run -q -p arxos-cli -- --store "$ARXOS_STORE" entity list "$BID"
```

Record `rp:<uuid>` ids and `support=` (first walk is `support=1`). Openings with `host=unresolved` were farther than 0.35 m from a wall plane, or projected outside the wall face padded by 0.15 m. They are not glued to a random wall. Realize / IFC skip the void relationship until a later ingest hosts them.

---

## 5. Phone: second walk, same room

Same building, same join. Scan the same walls. Stop. Expect another push (pending apply).

---

## 6. Apply again

```bash
cargo run -q -p arxos-cli -- --store "$ARXOS_STORE" inbox list "$BID"
cargo run -q -p arxos-cli -- --store "$ARXOS_STORE" inbox apply "$BID"
```

Serve still running.

---

## 7. Expect `support=2` where RoomPlan reused ids

```bash
cargo run -q -p arxos-cli -- --store "$ARXOS_STORE" entity list "$BID"
```

Walls whose Apple UUID matched the first stop fuse: one `EntityId`, `support=2`, pose moved toward the tighter \(\sigma\). If every wall is still `support=1` with **new** `rp:` ids, RoomPlan churned UUIDs — file that as an Apple limitation, not a hosting bug. Hosting bugs look like: same `rp:` ids, but a door attached to the wrong wall, or a door 2 m from both walls glued to one of them.

---

## 8. Slice + IFC

```bash
cargo run -q -p arxos-cli -- --store "$ARXOS_STORE" building slice "$BID" --z 1.2
cargo run -q -p arxos-cli -- --store "$ARXOS_STORE" export ifc "$BID" -o walk.ifc
```

ASCII slice is a diagnostic projector, not a product renderer. `walk.ifc` should contain `IFCWALL`. Void relationships appear only for hosted openings.

---

## Failure modes

| What you see | What it is | What to do |
|---|---|---|
| Second walk mints new `rp:` ids, `support` stays 1 | RoomPlan issued a new UUID | Not an Arxos bug. Keep fuse ready for ids that *do* match. Log Apple UUID strings from both stops. |
| Door / window `host=unresolved` | Plane distance `> 0.35 m`, or projection outside wall extent + `0.15 m`, or no wall in the batch | Leave it. Do not attach to the nearest centroid. Re-walk if the opening sits on a captured wall. |
| Door hosted on the opposite wall | Host miss | Bug in `resolve_opening_host` (plane / extent / CID). Capture the two wall poses + opening pose. |
| Inbox stays empty after Stop | Push miss (no ticket, LAN, or serve down) | Confirm Join URI, `net serve` still up, status is not “local only”. |
| `realize_skipped_high_sigma=N` | \(\sigma > 500\) mm | Facts stay in \(S\); they are omitted from solids. Not a fuse failure. |
| Dead zone / missing wall | RoomPlan did not emit that surface | Walk slower; do not invent a wall in Arxos. |
| `store.lock` / second flock | Another writer on the store | Serve is the only writer while it runs. Apply via the socket. |
| Want a 3D preview to “debug” the scan | Out of scope | Use `entity list` + slice. Do not add a viewer. |

Laptop-only `arx capture simulate` can prove CLI plumbing. It is **not** field proof. Do not start realize v2 (clip + voids CSG) on simulate-only evidence.
