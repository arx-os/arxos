# LiDAR confidence scores — honesty policy

ArxOS **does not** claim calibrated probabilistic confidence from LiDAR auto-structure.

## What the numbers mean today

| Source | Typical score | Meaning |
| :--- | :---: | :--- |
| Room occupancy-grid detector | `0.90` | Fixed **rule tier**: enclosed free-space component passed density/size gates |
| BBox floor fallback (no closed rooms) | `0.55` | Fixed **lower tier**: footprint from point extent only |
| Equipment geometric filter | `0.75` / `0.90` | Fixed **rule tier** by classification branch |

These are **feature flags / tiers**, not Bayesian posteriors and not survey-grade accuracy estimates.

**Provenance (file LiDAR path):** rooms carry `capture_source=lidar_file`, `capture_heuristic` (`occupancy_grid` | `bbox_fallback`), and `review_status=proposed`. Building metadata records voxel size, light mode, and point counts.

## Product rules

1. Do not surface scores as “% sure” in pilot UX without this caveat.
2. Human review (`review_status`) is the pilot truth gate — not the float.
3. Prefer documenting failure modes (missed floors, split rooms, noise) over inventing precision — [field-truth-log.md](./field-truth-log.md).
4. Open/incomplete room scans often cannot close free-space walls → **bbox fallback** room (still proposed). That is intentional assist, not false certainty.
5. Dense clouds are **not** stored as product (Decision 10 — [adr-capture-model.md](./adr-capture-model.md)).

## Operator tips (file path)

```bash
# Prefer light mode on laptops for large PLY/LAS
arx import lidar scan.ply --merge --light --voxel-size 0.25
arx validate
# Expect LossReport lines: lidar_room_fallback / lidar_proposed_only / …
```

If import yields zero usable structure after fallback, check units (meters), empty/corrupt files, or raise limits per [resource-limits.md](./resource-limits.md).

## Related

- `review_status=proposed|accepted|rejected` on room/equipment properties
- `arx export --format ifc` warns on proposed; `--approved-only` strips proposed/rejected auto entities
- [l1-supported-workflow.md](./l1-supported-workflow.md)
- [adr-capture-model.md](./adr-capture-model.md)
