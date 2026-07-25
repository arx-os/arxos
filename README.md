# ArxOS

**Git for Buildings** — a local-first **building compiler** with a terminal-first UI.

Field/BIM inputs become an in-memory `Building` graph, validated and stored as
Git-diffable YAML (`building.yaml`), with **IFC as industry interchange**.

**Maturity (honest):** lab closed loop ~8.5/10 · district L1 pilot ~5/10  
(blocked on field evidence + process — see `arxos_manifest.md` §1.1a · §1.6).  
**Living plan:** `docs/horizon-b-roadmap.md` · **Preferred pin:** `v2.0.0-pilot.5` @ `ad5213dca08cef52cc90d9b80037f0dbaaa14a8d`  
**Device policy:** [`docs/adr-web-demotion.md`](docs/adr-web-demotion.md) — web is a **static landing page only**; phone path = **native iOS lab shell** ([`arx-os/ios`](https://github.com/arx-os/ios)) over agent HTTP/RPC (file LiDAR path A; RoomPlan UI not started). See [`docs/field-language.md`](docs/field-language.md).

## What it does

```text
IFC / LiDAR file / text script / arx add
        │
        ▼
  finalize_ingest + validation
        │
        ▼
   building.yaml  (SSOT)  ── Git ──► versioned history
        │
        ├── arx show / ls / tree / add   (address-native CLI)
        ├── arx query / room / equipment / TUI
        └── arx export --format ifc      (GlobalId preserve + assign)
```

**Honest capture paths today:** file-based IFC + LiDAR + **CLI/TUI** + optional **agent** (capture node).  
**Not product:** browser LiDAR, ARKit/RoomPlan in Safari, walk-in pure PWA capture.

## IFC-only BIM policy

ArxOS is an **IFC compiler**, not a CAD host.

- **No** Revit / ArchiCAD plugins or direct CAD integrations.
- District path: **Vendor BIM → clean IFC export → `arx import ifc`**.
- Official export: **`arx export --format ifc`** only (review-gated).
- Optional `agent` feature is edge bridging (WebSocket/SSH) — not a second export authority.

Details: `docs/ifc-limitations.md`, `docs/adr-0001-identity-and-addressing.md`, `docs/identity-and-addressing.md`.

## Install

```bash
git clone https://github.com/arx-os/arxos.git
cd arxos
# Default features = compiler + TUI (primary UI)
cargo build --release
cargo install --path .
```

**District pilot:** install a **pinned** release only — see `docs/pilot-release.md`.  
Do not run pilots on floating `main`.

## Quick start

```bash
# Optional postal root (ADR 0001): fully-qualified bldg.us.… path
arx init --name "My Building" \
  --postal "143677 N. Dale Mabry Hwy, Suite 2, Tampa, FL, 33622"
arx import ifc path/to/building.ifc   # or: --postal "…" to re-root import
arx import lidar scan.ply --merge     # optional as-built assist (file)
arx edit corrections.txt              # text / review_status

# Address-native browse + mutate (no internal UUID as primary id)
ROOT=$(grep -E '^  address:' building.yaml | head -1 | awk '{print $2}')
arx show "$ROOT"
arx ls "${ROOT}/fl.1"
arx tree "$ROOT/elec" --depth 4
arx add "$ROOT" panel --name L1
arx add "${ROOT}/elec/panel.l1" ckt --name 14
arx add "${ROOT}/elec/panel.l1/ckt.14" outlet

arx validate
arx export --format ifc --output building.ifc   # assigns GlobalIds to arx-add entities
arx status && arx stage && arx commit -m "Import and label first model"
```

## Compiler + TUI surface (default)

| Command | Role |
|---|---|
| `init` | Seed `building.yaml` (+ optional Git, optional `--postal`) |
| `import ifc\|lidar\|text` | Adapters → finalize → SSOT (`import ifc --postal` for postal root) |
| `edit` | Apply text/AR script → finalize → SSOT (`arx edit help` for grammar) |
| `show` / `ls` / `tree` | Address-native inspection (ADR 0001) |
| `add` | Create equipment under a parent address (Arxos-native; GlobalId on export) |
| `export` | Building → IFC / yaml / json (**IFC spine**; GlobalId preserve + assign) |
| `validate` | Load SSOT → validation rules (`--strict-addresses`) |
| `migrate` | Backfill / postal re-root addresses |
| `room` / `equipment` / `query` / `search` / `spatial` | Domain ops |
| `status` / `stage` / `commit` / `diff` / `history` | Git |
| `render` / `merge` | TUI helpers (hierarchy text; merge tool) |
| `contribute` / `access` | Lab economy package / receipt (not L1-required) |

### Feature flags

| Feature | Default | Role |
|---|---|---|
| `tui` | **yes** | Primary UI (spreadsheet, merge, help, hierarchy render) |
| `agent` | no | Edge capture node — WebSocket/SSH (git + IFC/LiDAR import; no BACnet) |
| `blockchain` | no | ethers clients |
| `full` | no | tui + agent + blockchain |

**Web:** static `index.html` landing only (no Cargo feature; no interactive client).  
**Removed:** interactive WASM/PWA field client (Decision 9).  
**Removed for now (revisit later):** open-source hardware (BACnet/Modbus/MQTT), Bevy / LiDAR point-cloud 3D viz.

## Architecture (short)

- **Runtime SSOT:** `core::Building` (Building → Floor → Wing → Room → Equipment)
- **Durable SSOT:** `building.yaml` via `BuildingYamlSerializer` (`schema_version: 1`)
- **Completion:** `ingest::finalize_ingest` / `persist_building` (merge + validate)
- **IFC:** native STEP only; export via `export::ifc`
- **LiDAR ingest:** PLY/LAS/XYZ **files** → structure assist (`proposed`); not browser sensors
- **Identity (ADR 0001):** hierarchical `address` primary ops · `ifc_global_id` provenance · UUID internal — [`docs/adr-0001-identity-and-addressing.md`](docs/adr-0001-identity-and-addressing.md) · [`docs/identity.md`](docs/identity.md)
- **Agent:** capture node / bridge only — durable writes still through the spine

## iOS companion (separate repository)

Native field client lives in **`arx-os/ios`** (not this monorepo) — Decision 12.  
This core repo provides the **agent** and the versioned contract: [`docs/agent-client-interface.md`](./docs/agent-client-interface.md).  
Lab loop: [`docs/ios-lab-loop.md`](./docs/ios-lab-loop.md).

## Documentation

| Doc | Role |
|---|---|
| [`arxos_manifest.md`](./arxos_manifest.md) | **Engineering source of truth** |
| [`docs/adr-repo-structure.md`](./docs/adr-repo-structure.md) | Core vs `ios` repos |
| [`docs/agent-client-interface.md`](./docs/agent-client-interface.md) | Versioned agent JSON-RPC for clients |
| [`docs/INDEX.md`](./docs/INDEX.md) | Pilot doc map |
| [`docs/adr-0001-identity-and-addressing.md`](./docs/adr-0001-identity-and-addressing.md) | **Binding** identity decisions (ADR 0001) |
| [`docs/identity.md`](./docs/identity.md) | Identity code map + GlobalId / CLI surface |
| [`docs/l1-supported-workflow.md`](./docs/l1-supported-workflow.md) | Only L1 supported loop |
| [`docs/field-handoff.md`](./docs/field-handoff.md) | Ordered pilot packet |
| [`docs/resource-limits.md`](./docs/resource-limits.md) | Import size/point ceilings |

## Development

```bash
cargo test
cargo test --test compiler_spine_test \
           --test ifc_compiler_path_test \
           --test ifc_native_tests \
           --test lidar_tests \
           --test bidirectional_tests \
           --test postal_root_test \
           --test address_add_test \
           --test export_identity_test
cargo clippy --all-targets -- -D warnings
./scripts/l1_smoke.sh
```

**CI:** `compiler-ci.yml` is the authoritative PR gate (default = tui + compiler).

## License

MIT
