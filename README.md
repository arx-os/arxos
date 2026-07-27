# Arxos

**Lived-experience building repository** — content-addressed objects, signed Merkle roots, iOS-first capture, databaseless by design.

> Greenfield rebuild (2026-07-27). Previous database / YAML / Git-centric architectures are discarded.

## Architecture (non-negotiable)

- **Databaseless**: no general-purpose DB in the critical path
- **Source of truth**: content-addressed objects + signed Merkle roots
- **Building = repository**: `BuildingId` + current Root CID
- **Partial materialization** by default
- **iOS-first** lived experience (LiDAR, text, AR registration)
- **No general 3D rendering** in Arxos (geometry is data only)
- **Rust core**, UniFFI → Swift, Iroh networking, OpenUSD preferred, strong IFC
- **DePIN-ready**: signed contributions, attribution, proofs

Full design: [`docs/architecture/ARCHITECTURE.md`](docs/architecture/ARCHITECTURE.md)

## Repository layout

```
arxos/
├── core/           # arxos-core (Rust): objects, CID, CAS, roots, crypto
├── cli/            # arx CLI
├── networking/     # Iroh (Phase 2)
├── ios/            # SwiftUI + ARKit client
├── edge/           # Edge node binary
├── gateways/       # USD / IFC projections (Phase 4)
├── contracts/      # Minimal L2 registry (Phase 5)
└── docs/
    ├── architecture/
    └── schema/
```

## Phase status

| Phase | Focus | Status |
|-------|--------|--------|
| **0** | Object, CAS, Root, UniFFI, CLI | Done |
| **1** | Mobile capture loop (Space / PointCloud / Annotation → commit) | Done |
| **2** | Multi-device + Iroh + mDNS | Done |
| **3** | Spatial index, partial load, merge | Done |
| **4** | USD / IFC interop | Done |
| **5** | DePIN & hardening | Done (foundation) |

## Build & test

```bash
# Unit + integration tests
cargo test --workspace

# CLI
cargo run -p arxos-cli -- version
```

### CLI quickstart (Phase 1 capture loop)

```bash
export ARXOS_STORE=/tmp/arxos-demo

# New building repository (CAS + head + device key)
BID=$(cargo run -q -p arxos-cli -- --store "$ARXOS_STORE" building init --name "Demo Hall" --quiet)

# Simulate RoomPlan-like capture (space + point cloud + annotation) and commit
cargo run -q -p arxos-cli -- --store "$ARXOS_STORE" capture simulate "$BID" --commit

# Reload + spatial-ish annotation query
cargo run -q -p arxos-cli -- --store "$ARXOS_STORE" building show "$BID"
cargo run -q -p arxos-cli -- --store "$ARXOS_STORE" building near "$BID" --x 1.2 --y 1.4 --z 1.1 --radius 5
```

Low-level object/root commands remain available (`object put`, `root create`, …).

### Multi-device sync (Phase 2)

```bash
# Device A — serve CAS over Iroh
export ARXOS_STORE=/tmp/device-a
arx net serve                 # prints ticket=…  (add --no-mdns to skip LAN ads)

# Device B — pull root + objects, adopt head
export ARXOS_STORE=/tmp/device-b
arx net fetch --peer "$TICKET" --root "$ROOT_CID" --building-id "$BID" --set-head
arx building near "$BID" --x 1.2 --y 1.4 --z 1.1

arx net peers --timeout 3     # mDNS browse on site Wi‑Fi
arx net status
```

See [`docs/architecture/PHASE2.md`](docs/architecture/PHASE2.md).

### Spatial index & merge (Phase 3)

```bash
# After capture commits (index is built automatically on commit):
arx spatial query "$BID" --min-x 0 --min-y 0 --min-z 0 --max-x 5 --max-y 3 --max-z 5
arx spatial load  "$BID" --min-x 0 --min-y 0 --min-z 0 --max-x 5 --max-y 3 --max-z 5
arx spatial build "$BID" --commit   # rebuild + attach index on a new root

# Concurrent scans:
arx merge plan  "$ROOT_A" "$ROOT_B"
arx merge apply "$BID" "$OTHER_ROOT"
```

See [`docs/architecture/PHASE3.md`](docs/architecture/PHASE3.md).

### Interop — USD & IFC (Phase 4)

```bash
arx export usd "$BID" -o building.usda
arx export ifc "$BID" -o building.ifc
arx import usd building.usda
arx import ifc building.ifc

# Edge node
arxos-edge export-usd "$BID" -o building.usda
arxos-edge export-ifc "$BID" -o building.ifc
```

Projections preserve identity (`arxos:cid` / `Pset_ArxosIdentity`).  
See [`docs/architecture/PHASE4.md`](docs/architecture/PHASE4.md).

### DePIN & hardening (Phase 5)

```bash
arx depin score "$BID"
arx depin verify "$ROOT_CID"
arx depin attest "$ROOT_CID" --device-id field-phone-1
arx depin registry "$BID" --abi

# Edge packaging
docker build -f edge/Dockerfile -t arxos-edge .
# or: sudo INSTALL_SYSTEMD=1 ./edge/scripts/install-edge.sh
```

On-chain: `contracts/BuildingRegistry.sol` (Base L2).  
See [`docs/architecture/PHASE5.md`](docs/architecture/PHASE5.md).

## iOS (Phase 1)

```bash
cd ios/Arxos && swift run ArxosDemo
```

SwiftUI app sources: `ios/Arxos/Sources/ArxosApp/` — init/open building, simulate or RoomPlan capture, pin annotations, commit root, AR annotation overlay. See [`ios/README.md`](ios/README.md) and [`docs/architecture/PHASE1.md`](docs/architecture/PHASE1.md).

## License

MIT OR Apache-2.0
