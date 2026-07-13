# ArxOS

**Git for Buildings** — a local-first **building compiler**.

Field/BIM inputs become an in-memory `Building` graph, validated and stored as
Git-diffable YAML (`building.yaml`), with IFC as industry interchange.

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
        ├── arx query / room / equipment
        └── arx export --format ifc
```

## Install

```bash
git clone https://github.com/arx-os/arxos.git
cd arxos
cargo build --release
cargo install --path .
```

## Quick start

```bash
# New project (creates building.yaml)
arx init --name "My Building"

# Import IFC into the canonical Building model
arx import ifc path/to/building.ifc

# Or LiDAR (PLY/LAS/XYZ)
arx import lidar scan.ply --merge

# Text / AR command script
arx edit corrections.txt

# Validate SSOT
arx validate

# Query equipment by durable ArxAddress
arx query "/local/local/local/*/*/*/*"

# Export IFC interchange
arx export --format ifc --output building.ifc

# Git workflow on the YAML SSOT
arx status
arx stage
arx commit -m "Import first model"
```

Backfill missing equipment addresses:

```bash
arx migrate
arx migrate --dry-run
```

## Compiler CLI surface

| Command | Role |
|---|---|
| `init` | Seed `building.yaml` (+ optional Git) |
| `import ifc\|lidar\|text` | Adapters → finalize → SSOT |
| `edit` | Apply text/AR script → finalize → SSOT |
| `export` | Building → IFC / yaml / json |
| `validate` | Load SSOT → validation rules |
| `migrate` | Backfill missing `ArxAddress` fields |
| `room` / `equipment` / `spatial` | Domain operations on Building |
| `query` / `search` | Address globs / name search |
| `status` / `stage` / `commit` / `diff` / `history` | Git |
| `render` / `interactive` | Visualization (feature-dependent) |

Optional features at build time: `tui` (default), `agent`, `render3d`, `web`, `blockchain`.

```bash
cargo build --release --features agent
```

## Architecture (short)

- **Runtime SSOT:** `core::Building` (Building → Floor → Wing → Room → Equipment)
- **Durable SSOT:** `building.yaml` via `BuildingYamlSerializer`
- **Completion:** `ingest::finalize_ingest` / `persist_building` (merge + validate)
- **IFC:** native STEP parser only; export via `export::ifc`
- **Identity:** Arx UUID + optional `ifc_global_id` + durable `ArxAddress` on equipment

See `arxos_manifest.md` for engineering maturity and non-goals.

## Layout

| Path | Role |
|---|---|
| `src/` | Library + `arx` binary |
| `templates/` | `arx init` scaffolds |
| `test_data/` | IFC fixtures |
| `tests/` | Integration tests (compiler spine, IFC, LiDAR) |
| `contracts/` | Optional tokenomics (Foundry; not required for compiler) |

## Development

```bash
# Full suite (default features)
cargo test

# Compiler spine (CI-critical)
cargo test --test compiler_spine_test \
           --test ifc_compiler_path_test \
           --test ifc_native_tests \
           --test lidar_tests \
           --test bidirectional_tests

RUST_LOG=debug cargo run -- validate
```

### CI

| Workflow | Role |
|---|---|
| **`compiler-ci.yml`** | **Authoritative PR gate** — fmt, clippy (default features), lib + spine + full `cargo test` |
| `rust-ci.yml` | Optional extended / soft coverage (weekly + manual) |
| `ci.yml` | Optional security audit (push/schedule; non-blocking) |
| `quality.yml` | Optional clippy/doc/bench (weekly + manual) |

Release binaries remain on tag pushes via `release.yml`.

## License

MIT
