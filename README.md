# ArxOS

**Git for Buildings** — a local-first **building compiler** with a terminal-first UI.

Field/BIM inputs become an in-memory `Building` graph, validated and stored as
Git-diffable YAML (`building.yaml`), with **IFC as industry interchange**.

**Maturity (honest):** lab closed loop ~8/10 · district L1 pilot ~4/10  
(blocked on field evidence + process — see `arxos_manifest.md` §1.6).

## What it does

```text
IFC / LiDAR / text script
        │
        ▼
  finalize_ingest + validation
        │
        ▼
   building.yaml  (SSOT)  ── Git ──► versioned history
        │
        ├── arx query / room / equipment / TUI
        └── arx export --format ifc
```

## IFC-only BIM policy

ArxOS is an **IFC compiler**, not a CAD host.

- **No** Revit / ArchiCAD plugins or direct CAD integrations.
- District path: **Vendor BIM → clean IFC export → `arx import ifc`**.
- Official export: **`arx export --format ifc`** only (review-gated).
- Optional `agent` feature is edge bridging (WebSocket/SSH) — not a second export authority.

Details: `docs/ifc-limitations.md`, `docs/identity.md`.

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
arx init --name "My Building"
arx import ifc path/to/building.ifc
arx import lidar scan.ply --merge          # optional as-built assist
arx edit corrections.txt                   # text / review_status
arx validate
arx query "/local/local/local/*/*/*/*"
arx export --format ifc --output building.ifc
arx status && arx stage && arx commit -m "Import first model"
arx render --building "My Building"        # hierarchy text (TUI feature)
```

## Compiler + TUI surface (default)

| Command | Role |
|---|---|
| `init` | Seed `building.yaml` (+ optional Git) |
| `import ifc\|lidar\|text` | Adapters → finalize → SSOT |
| `edit` | Apply text/AR script → finalize → SSOT |
| `export` | Building → IFC / yaml / json (**IFC spine**) |
| `validate` | Load SSOT → validation rules |
| `migrate` | Backfill missing `ArxAddress` fields |
| `room` / `equipment` / `query` / `search` / `spatial` | Domain ops |
| `status` / `stage` / `commit` / `diff` / `history` | Git |
| `render` / `merge` | TUI helpers (hierarchy text; merge tool) |
| `contribute` / `access` | Lab economy package / receipt (not L1-required) |

### Feature flags

| Feature | Default | Role |
|---|---|---|
| `tui` | **yes** | Primary UI (spreadsheet, merge, help, hierarchy render) |
| `agent` | no | Edge WebSocket/SSH (git + IFC; no BACnet/hardware) |
| `web` | no | WASM PWA — terminal-style pane (+ camera/AR later) |
| `blockchain` | no | ethers clients |
| `full` | no | tui + agent + web + blockchain |

**Removed for now (revisit later):** open-source hardware (BACnet/Modbus/MQTT), Bevy / LiDAR point-cloud 3D viz.

## Architecture (short)

- **Runtime SSOT:** `core::Building` (Building → Floor → Wing → Room → Equipment)
- **Durable SSOT:** `building.yaml` via `BuildingYamlSerializer` (`schema_version: 1`)
- **Completion:** `ingest::finalize_ingest` / `persist_building` (merge + validate)
- **IFC:** native STEP only; export via `export::ifc`
- **LiDAR ingest:** PLY/LAS/XYZ → structure assist (`proposed`); not TUI point-cloud render
- **Identity:** Arx UUID + optional `ifc_global_id` + durable `ArxAddress` on equipment

## Documentation

| Doc | Role |
|---|---|
| [`arxos_manifest.md`](./arxos_manifest.md) | **Engineering source of truth** |
| [`docs/INDEX.md`](./docs/INDEX.md) | Pilot doc map |
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
           --test bidirectional_tests
cargo clippy --all-targets -- -D warnings
./scripts/l1_smoke.sh
```

**CI:** `compiler-ci.yml` is the authoritative PR gate (default = tui + compiler).

## License

MIT
