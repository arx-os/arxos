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

## Install

See **`docs/install.md`**. Dev path: `cargo install --path .` then `arx --version`.

## Cold-start (capture node)

```bash
# 1. Install (dev)
cargo install --path .   # see docs/install.md

# 2. Init project (writes validated building.yaml: UUID + Ground Floor)
mkdir my-site && cd my-site
arx init --name "Pilot Site"
arx validate

# 3. Import reality
arx import path/to/model.ifc
# or: arx import lidar path/to/scan.ply --merge

# 4. Review auto LiDAR structure (Track C1)
#    Auto rooms/equipment start as review_status=proposed
#    Accept or reject before pilot handoff:
# arx edit corrections.txt   # contains e.g.:
#   set room AutoRoom-1 review_status=accepted
#   set equipment HVAC Item 1 review_status=rejected

# 5. Correct + address
arx edit corrections.txt
arx migrate              # backfill equipment ArxAddress
arx validate
arx query "/…/*…"

# 6. Export + version
# Default: full export + warnings for proposed LiDAR entities
arx export --format ifc -o building.ifc
# Pilot-approved: strip proposed + rejected auto entities
arx export --format ifc -o building-approved.ifc --approved-only
arx stage && arx commit -m "pilot model"
# or: arx commit "pilot model"
```

## Sample edit script

```text
# examples/pilot-corrections.txt (copy into project)
set room Ground Floor review_status=accepted
# set room BadAutoRoom review_status=rejected
```

## Resource defaults (Track D3 — starting guidance)

| Profile | Guidance | Notes |
| :--- | :--- | :--- |
| Pi / light | Prefer aggressive voxel; cap point cloud size; avoid full campus PLY | Light mode TBD in detector flags |
| Mini / laptop | Primary capture node for pilot | IFC + mid-size LiDAR OK |
| Tablet / WASM | **Review only** — no full LiDAR in browser | Track E optional |

## Known failure modes (LiDAR — Track C)

| Mode | Mitigation |
| :--- | :--- |
| Missed floors / split rooms / noise | Human edit; `review_status=rejected` on bad autos |
| Trusting auto structure as survey truth | Export **warns** on `proposed`; use `--approved-only` for handoff IFC |
| Over-reading confidence floats | See `docs/lidar-confidence.md` — scores are **rule tiers**, not probabilities |

## IFC interop notes

- Checked-in third-party-ish samples: `test_data/Building-Architecture.ifc`, `Building-Hvac.ifc`
- Limitations: `docs/ifc-limitations.md`
- Native STEP only; no second IFC stack

## Install checklist (Track D2)

- [ ] `arx --help` / `arx --version`
- [ ] `arx init` then `arx validate` succeeds
- [ ] Import `test_data/sample_building.ifc` (or site IFC)
- [ ] Git commit of `building.yaml`
- [ ] Export IFC with and without `--approved-only` (if LiDAR used)

## Walkthrough sign-off

| Role | Name | Date | Notes |
| :--- | :--- | :--- | :--- |
| Non-author operator | | | Must complete cold-start without reverse-engineering the repo |
