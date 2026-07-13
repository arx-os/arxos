# Resource limits (R6 pilot defaults)

**Obligation:** R6 — avoid OOM/hang on capture nodes; make failures explicit.  
**Code:** `src/resource_limits.rs` · enforced on `arx import ifc|lidar` (and agent IFC upload).

These are **pilot defaults**, not survey-grade ceilings. Field teams should log real
timings in [field-truth-log.md](./field-truth-log.md) §C and may raise limits on
adequately provisioned hardware.

## Defaults

| Limit | Default | Env override |
| :--- | ---: | :--- |
| IFC file size | 50 MiB | `ARX_MAX_IFC_BYTES` |
| LiDAR file size | 512 MiB | `ARX_MAX_LIDAR_BYTES` |
| LiDAR input points (streamed) | 20_000_000 | `ARX_MAX_LIDAR_INPUT_POINTS` |

LiDAR voxel memory is also bounded inside the downsampler:

| Mode | Max voxels before flush |
| :--- | ---: |
| Normal | 500_000 |
| `--light` | 100_000 (and voxel size ≥ 0.20 m) |

## Operator guidance

```bash
# Prefer light mode on laptops / constrained RAM
arx import lidar scan.ply --light --voxel-size 0.25

# Intentionally larger IFC (capture Mini with plenty of RAM)
export ARX_MAX_IFC_BYTES=$((200 * 1024 * 1024))
arx import ifc big.ifc
```

If import refuses with “too large” or “exceeded pilot point limit”:

1. Do **not** disable validation to “make it work.”  
2. Decimate the scan / re-export a lighter IFC from the BIM tool.  
3. Use a stronger capture node (Mini/laptop, not Pi) for that site.  
4. Only then raise env limits and re-run; record values in field-truth-log §C.

## Hardware expectations (MVP)

| Profile | Guidance |
| :--- | :--- |
| Raspberry Pi class | LiDAR only with aggressive `--light` + large voxel; prefer IFC-only pilots |
| OptiPlex / Mac Mini | Primary capture node for school-scale IFC + moderate scans |
| Tablet / WASM | Review only — no full LiDAR in browser |

## What this does **not** close

R6 is only **pilot-mitigated** after one real site run is logged (time, RAM, limits used).  
These defaults are the eng half of the obligation.

**Related:** [l1-supported-workflow.md](./l1-supported-workflow.md) · [field-truth-log.md](./field-truth-log.md) · manifest §1.6 R6
