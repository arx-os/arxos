# ArxOS pilot runbook (outline)

> Living ops doc for a second engineer cold-start. Track **D1**.  
> Integrity notes (I7, I9, I11) are authoritative here and in `arxos_manifest.md`.

## Hard pilot limits

| Limit | Rule |
| :--- | :--- |
| **Single building per repo** | One `building.yaml` at the project root. Multi-building / campus layouts are **not** supported in pilot (I11). Use one Git repo (or worktree) per building. |
| **SSOT** | Durable state is `building.yaml` only. IFC is interchange; envelope JSON is portable cache. |
| **CLI pilot loop** | `init` → `import` → `edit` → `migrate` → `validate` → `query` → `export` → git. |

## Non-surfaces (do not rely on for pilot)

| Surface | Status |
| :--- | :--- |
| `arx spatial grid-to-real` / `real-to-grid` / `relate` | **Not implemented** (hard error; no fake success) |
| `arx spatial query` / `transform` / `validate` | Implemented against `building.yaml` |
| `export --delta` | **Not implemented** (hard error if set) |
| `arx interactive` / Bevy 3D | Experimental; requires `--features render3d`; **not** pilot product |
| Hardware / MQTT / BACnet / simulated I/O | **Non-MVP stubs** — do not expand for pilot (I9) |
| Agent / blockchain / full PWA capture | Feature-gated / deferred |

## Cold-start (capture node)

```bash
# 1. Install (dev)
cargo install --path .   # or use a release binary when published

# 2. Init project (writes validated building.yaml: UUID + Ground Floor)
mkdir my-site && cd my-site
arx init --name "Pilot Site"

# 3. Import reality
arx import path/to/model.ifc
# or: arx import lidar path/to/scan.ply --merge

# 4. Correct
arx edit corrections.txt
arx migrate              # backfill equipment ArxAddress
arx validate
arx query "/…/*…"

# 5. Export + version
arx export --format ifc -o building.ifc
arx stage && arx commit -m "pilot model"
```

## Resource defaults (fill in during Track D3)

| Profile | Max points (TBD) | Voxel default (TBD) | Notes |
| :--- | :--- | :--- | :--- |
| Pi / light | | | Light mode |
| Mini / laptop | | | Primary capture node |

## Known failure modes (LiDAR — Track C)

- Missed floors, split rooms, noise → human edit before export.
- Export should warn on unreviewed auto structure (C2 open).

## Install checklist (Track D2)

- [ ] `arx --help` / `arx --version`
- [ ] `arx init` then `arx validate` succeeds
- [ ] Import sample IFC from fixtures
- [ ] Git commit of `building.yaml`

## Walkthrough sign-off

| Role | Name | Date | Notes |
| :--- | :--- | :--- | :--- |
| Non-author operator | | | Must complete cold-start without reverse-engineering the repo |
