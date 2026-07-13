# LiDAR confidence scores — honesty policy

ArxOS **does not** claim calibrated probabilistic confidence from LiDAR auto-structure.

## What the numbers mean today

| Source | Typical score | Meaning |
| :--- | :---: | :--- |
| Room occupancy-grid detector | `0.90` | Fixed **rule tier**: component passed density/size gates |
| Equipment geometric filter | `0.75` / `0.90` | Fixed **rule tier** by classification branch |

These are **feature flags / tiers**, not Bayesian posteriors and not survey-grade accuracy estimates.

## Product rules

1. Do not surface scores as “% sure” in pilot UX without this caveat.
2. Human review (`review_status`) is the pilot truth gate — not the float.
3. Prefer documenting failure modes (missed floors, split rooms, noise) over inventing precision — [field-truth-log.md](./field-truth-log.md).

## Related

- `review_status=proposed|accepted|rejected` on room/equipment properties
- `arx export --format ifc` warns on proposed; `--approved-only` strips proposed/rejected auto entities
- [l1-supported-workflow.md](./l1-supported-workflow.md)
