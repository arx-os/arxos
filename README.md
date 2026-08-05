# Arxos

**Arxos is a local-first content-addressed as-built repository.**

It stores signed, versioned building state as a content-addressed graph of
objects, supports multi-device offline capture and sync, and produces
offline-replayable contribution scores that can drive **fiat** rewards for
real-world data contribution.

| Arxos **is** | Arxos **is not** |
|--------------|------------------|
| A local CAS of immutable building objects (BLAKE3 CIDs over canonical CBOR) | A Git repository of YAML files |
| Signed delta roots with controller authorization | A blockchain or token mint |
| Multi-device offline capture + P2P pull sync | A mandatory cloud service |
| Deterministic scoring for fiat ops (off-band) | An on-chain reward / `$AXD` economy |

---

## Status

Foundation-complete for the core data plane: local CAS, RoomPlan geometry
ingestion, delta root materialization, spatial query, multi-device pull sync
(Iroh QUIC + mDNS), and gateway export (OpenUSD / IFC subset).

This is an experimental codebase — **not** a production CAD platform or
finished consumer mobile app. Scoring is **diagnostic only** today; do not use
type-count scores as a payment basis.

---

## Architecture (what actually exists)

```
┌─────────────────────────────────────────────────────────────┐
│              Capture clients (iOS RoomPlan / CLI)           │
│                            │                                │
│                            ▼                                │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │                   arxos-core (Rust)                     │ │
│ │  Objects · CIDs · signed Roots · R-tree · scoring       │ │
│ └──────┬──────────────────────────────┬───────────────────┘ │
│        │                              │                     │
│        ▼                              ▼                     │
│ ┌──────────────┐              ┌──────────────────────┐      │
│ │ Local Object │              │  Networking fabric   │      │
│ │ Store (CAS)  │◄────────────►│  Iroh QUIC + mDNS    │      │
│ └──────────────┘              └──────────────────────┘      │
└─────────────────────────────────────────────────────────────┘
```

### Data model

Every record is an **immutable object**: header + typed body, serialized as
canonical CBOR. Its **CID** is `b3:` + hex(BLAKE3-256 of those bytes).

Important types include: `Building`, `Floor`, `Space`, `Surface`, `Opening`,
`Equipment`, `Annotation`, `PointCloudChunk`, `Mesh`, `SpatialIndexNode`,
`Root`, `Provenance`, `Blob`.

Cross-object references are CIDs. Physical entities (Floor, Space, Surface,
Opening, Equipment, Sensor, Fixture, System, Circuit) also carry an optional
stable **`EntityId`** (ULID). Each update produces a **new version object**
(new CID); commit and merge **collapse** the active set so at most one version
per `EntityId` remains. Legacy objects without `entity_id` never collapse
with peers (pure-CID identity).

### Roots (version control)

A **Root** is a signed commit for one building:

- **Delta commits** carry `added` / `removed` CID sets relative to the parent
  (removes include superseded entity versions and explicit `remove_object` /
  `remove_entity` operations).
- **Checkpoints** (every 50 commits, and on the first commit) store the full
  active object set so materialization stays bounded.
- **Authors** must present valid ed25519 signatures **and** be listed in
  `Building.controller_keys` (fail closed on commit, adopt, and merge).
- Concurrent tips can be merged; both parents are recorded in `merge_parents`.

The head pointer for each building lives in a small metadata file under the
store (`meta/buildings/<building_id>.cbor`). The object graph itself is pure CAS.

### Controllers & integrity

- Device keys are ed25519 keypairs (seed stored at `keys/device.seed`, mode
  `0600` on Unix).
- Only keys in `Building.controller_keys` may advance the building head.
- Controllers can be **added and removed** without re-init (current controller
  must sign the change). Removing the last controller is rejected. Losing all
  controller seeds requires offline recovery (`allow_untrusted` adopt) — not
  automated.
- Object gets recompute the CID on read; mismatched bytes fail.
- Sync closures fail closed if active objects or the spatial index root are
  missing (unless an explicit partial option is set).

### Sync

- **Transport:** Iroh QUIC (ALPN `arxos/sync/1`), length-prefixed CBOR messages.
- **Discovery:** LAN mDNS (`_arxos._udp.local.`).
- **Operation:** pull a root closure (history back to the nearest checkpoint +
  active objects + spatial index nodes), verify CIDs on the wire, adopt head.
- **Metadata-first:** `arx net fetch … --metadata-only` pulls domain objects
  without `Blob` payloads (point-cloud / mesh bytes). Default remains a full
  pull including blobs. Blobs can be fetched later by CID when needed.
- Source of truth remains the local CAS; networking only moves bytes.

### Scoring (DePIN data plane, fiat settlement)

Contribution → verification → **scoring** → fiat payout **outside this repo**.

- `arxos_core::scoring` attributes signed objects under a root and produces a
  deterministic `ScoreReport` (points / reputation signals).
- Settlement is **fiat**, ops-controlled, and never stored in CIDs or objects.
- No native token, mint path, wallet settlement, or chain rewards.
- Current weights are type-count heuristics — diagnostic only.

### Capture

iOS RoomPlan / ARKit transforms are converted in pure Rust
(`pose_from_column_major_matrix`, world AABB from local extents) into Space,
PointCloudChunk, and Annotation objects. There is no general 3D renderer in
Arxos; geometry is data for query, export, and scoring.

### Gateways

| Gateway | Role |
|---------|------|
| **OpenUSD** (`arxos-usd`) | USDA ASCII export/import; identity via `arxos:cid` metadata |
| **IFC** (`arxos-ifc`) | IFC4 STEP subset (Project/Site/Storey/Space); `Pset_ArxosIdentity` |

---

## Repository layout

```
arxos/
├── core/           # arxos-core: CAS, roots, spatial index, scoring
├── ffi/            # UniFFI bindings (iOS)
├── gateways/       # usd, ifc interop
├── networking/     # Iroh + mDNS sync
├── cli/            # arx CLI
├── ios/            # SwiftUI capture client
├── edge/           # Edge node packaging / tools
└── archive/        # Historical material (not built), e.g. deprecated EVM
```

Deep design notes and ADRs live in a **local-only** `docs/` tree (gitignored).
The public documentation surface is this README.

---

## Build & test

Requirements: Rust 1.75+, cargo. Optional: iOS toolchain for mobile bindings.

```bash
cargo build --release
cargo test --workspace --release
```

iOS bindings (optional):

```bash
cargo build -p arxos-ffi
./ios/Arxos/Scripts/generate_bindings.sh
```

---

## Quick start

```bash
export ARXOS_STORE=/tmp/arxos-store

# Initialize a building (prints building id)
BID=$(cargo run -q -p arxos-cli -- --store "$ARXOS_STORE" building init --name "Main Hall" --quiet)

# Simulated capture + commit
cargo run -q -p arxos-cli -- --store "$ARXOS_STORE" capture simulate "$BID" --commit

# Spatial query near a point
cargo run -q -p arxos-cli -- --store "$ARXOS_STORE" building near "$BID" \
  --x 1.2 --y 1.4 --z 1.1 --radius 5

# Diagnostic contribution score
cargo run -q -p arxos-cli -- --store "$ARXOS_STORE" score "$BID"

# Verify head integrity
cargo run -q -p arxos-cli -- --store "$ARXOS_STORE" verify "$BID"
```

Common commands (see `cargo run -p arxos-cli -- --help` for the full surface):

| Area | Examples |
|------|----------|
| Building | `building init`, `building list`, `building show`, `building near` |
| Controllers | `building add-controller`, `building remove-controller`, `building controllers` |
| Entities | `entity list`, `entity remove` (commits by default; `--no-commit` to stage only) |
| Capture | `capture simulate`, `capture annotation`, `capture point-cloud` |
| Roots | `root show`, `merge plan` / `merge apply` |
| Integrity | `verify`, `attest` |
| Economy (data plane) | `score` |
| Export | `export usd`, `export ifc` |
| Net | `net serve`, `net fetch --peer … --root … [--metadata-only]`, `net peers` |

CLI source layout: `cli/src/main.rs` (entry), `cli/src/args.rs` (clap),
`cli/src/commands/` (handlers), `cli/src/util.rs` (helpers).

Store layout:

```text
$ARXOS_STORE/
  objects/ab/cdef…     # CAS fan-out by CID hex
  meta/buildings/…     # head pointers (BuildingRecord)
  keys/device.seed     # ed25519 seed (0600)
  index.cbor           # optional thin catalog (rebuild-on-demand)
```

---

## Capabilities & Phase-0 boundaries

| Area | Guaranteed today | Explicit non-goals (Phase 0) |
|------|------------------|------------------------------|
| Integrity | BLAKE3 CIDs; fail-closed root auth | Full key recovery UX |
| Commits | Delta roots + N=50 checkpoints | Multi-building distributed spatial index |
| Sync | Bounded pull to nearest checkpoint | Global DHT / gossip mesh |
| Capture | RoomPlan matrices → pose / AABB | Dense LiDAR ML segmentation pipeline |
| Interop | USDA / IFC4 subset with CID identity | Full MEP IFC; native C++ OpenUSD |
| Settlement | Offline scores for fiat ops | Tokens, minting, in-repo billing |
| Rendering | Spatial query + file export | Built-in 3D viewer / game engine |
| Edge | Local store + export tools | Full Pi image product (in progress) |

### Storage policy

- Single object max size: **4 MiB** (`MAX_OBJECT_BYTES`). Oversized puts fail closed.
- New point-cloud and mesh captures **tier** raw bytes into separate `Blob`
  objects; domain objects stay skinny (`points_blob` / `vertices_blob` /
  `indices_blob`). Legacy inline payloads still deserialize.
- Root closures support metadata-first pulls (`ClosureOptions::include_blobs =
  false`) that omit Blob payloads while still transferring domain objects.
- **Single-writer lock**: `BuildingRepository` takes an exclusive flock on
  `store.lock`. Concurrent writers fail closed. Read-only CAS opens do not lock.

### Edge serve

```bash
cargo run -p arxos-edge -- --store "$ARXOS_STORE" serve
# holds store.lock, binds Iroh QUIC, optional mDNS; Ctrl-C releases the lock
```

Head metadata survives process restart on disk. Only one edge/writer process
per store path.

### Known hardening targets (not promises)

- Multi-sig / delayed controller rotation policy
- On-demand blob fetch CLI convenience (raw object get already works by CID)
- Multi-signal scoring (still points only; still offline-replayable)

---

## Economic model

| Role | Economics |
|------|-----------|
| **Data buyers** | Pay **fiat** for access to data and derived products (off-band) |
| **Contributors** | Submit real-world building / spatial data |
| **Scoring** | Deterministic points for attribution (`arx score`) |
| **Rewards** | Fiat, ops-controlled; never written into the object graph |
| **Tokens / chain** | **None** |

Archived EVM material under `archive/contracts-evm-deprecated/` is historical
reference only and is not built or shipped.

---

## Contributing

1. **Keep it tight.** Prefer deleting surface area over adding it. No renderers,
   drivers, token layers, or SaaS control planes without a clear need.
2. **Preserve determinism.** CIDs must be pure functions of object bytes. Do not
   put wall-clock or non-deterministic data into hashed content unless the path
   is explicitly gated and tested.
3. **Fail closed.** Authorization, signature, and closure completeness checks
   stay mandatory defaults.
4. **Offline-first.** Features must work without a cloud dependency. Prefer pure
   functions for scoring and validation.
5. **Public docs = this README.** Design notes and ADRs stay local (`docs/` is
   gitignored). If a change alters public behavior, update this README in the
   same change.

### Workflow

```bash
# Branch from main
git checkout -b feat/your-change

# Develop with tests
cargo test --workspace

# Open a PR with a short description of intent and any README updates
```

### Code map (where to start)

| Concern | Location |
|---------|----------|
| Object schema / CID / crypto | `core/src/object`, `canonical`, `cid`, `crypto` |
| Entity identity / collapse | `core/src/entity.rs` |
| Roots, auth, checkpoints, closures | `core/src/root/` |
| Commit / adopt / query / controllers | `core/src/repository/` |
| Spatial index | `core/src/spatial/` |
| Capture conversion (incl. blob tiering) | `core/src/capture/` |
| Merge | `core/src/merge/` |
| Scoring | `core/src/scoring/` |
| Sync protocol | `networking/` |
| CLI | `cli/src/{main,args,util,commands}.rs` |

---

## License

Licensed under either of:

- Apache License, Version 2.0 (http://www.apache.org/licenses/LICENSE-2.0)
- MIT license (http://opensource.org/licenses/MIT)

at your option.
