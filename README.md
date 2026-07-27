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
├── cli/            # arxos CLI
├── networking/     # Iroh (Phase 2)
├── ios/            # SwiftUI + ARKit client
├── edge/           # Edge node binary
├── gateways/       # USD / IFC projections (Phase 4)
├── contracts/      # Minimal L2 registry (Phase 5)
└── docs/
    ├── architecture/
    └── schema/
```

## Phase 0 status

| Deliverable | Status |
|-------------|--------|
| Monorepo structure | Done |
| Object + CBOR + BLAKE3 CID | Done |
| Local CAS store | Done |
| Root + ed25519 signing | Done |
| CLI: `object put`, `root create`, `root show` | Done |
| UniFFI skeleton + Swift hello | Done |
| Initial object schema docs | Done |

## Build & test

```bash
# Unit + integration tests
cargo test --workspace

# CLI
cargo run -p arxos-cli -- version
```

### CLI quickstart

```bash
export ARXOS_STORE=/tmp/arxos-demo

# Keys
cargo run -p arxos-cli -- key generate
# → seed=...  public_key=ed25519:...

# Put objects
cargo run -p arxos-cli -- --store "$ARXOS_STORE" object put --type blob --text "hello"
cargo run -p arxos-cli -- --store "$ARXOS_STORE" object put --type annotation --text "valve behind panel"
cargo run -p arxos-cli -- --store "$ARXOS_STORE" object put --type building --name "Demo Hall" --sign-seed "$SEED"

# Create signed root
cargo run -p arxos-cli -- --store "$ARXOS_STORE" root create \
  --building-id "$BUILDING_ID" \
  --all \
  --seed "$SEED" \
  --message "initial"

# Show root
cargo run -p arxos-cli -- --store "$ARXOS_STORE" root show "$ROOT_CID"
```

## iOS (Phase 0)

Open `ios/Arxos/Arxos.xcodeproj` (or the Swift package under `ios/`) for a blank SwiftUI app that calls the UniFFI `hello` binding once the XCFramework is built.

See [`ios/README.md`](ios/README.md).

## Phases

0. **Foundation** (current)  
1. Mobile capture loop  
2. Multi-device + Iroh  
3. Spatial index & scale  
4. USD / IFC interop  
5. DePIN & hardening  

## License

MIT OR Apache-2.0
