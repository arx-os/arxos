# LiDAR confidence scores — honesty policy (Track C3)

ArxOS **does not** claim calibrated probabilistic confidence from LiDAR auto-structure.

## What the numbers mean today

| Source | Typical score | Meaning |
| :--- | :---: | :--- |
| Room occupancy-grid detector | `0.90` | Fixed **rule tier**: component passed density/size gates |
| Equipment geometric filter | `0.75` / `0.90` | Fixed **rule tier** by classification branch (furniture vs MEP-ish) |

These are **feature flags / tiers**, not Bayesian posteriors and not survey-grade accuracy estimates.

## Product rules

1. Do not surface scores as “% sure” in pilot UX without this caveat.
2. Human review (`review_status`) is the pilot truth gate — not the float.
3. Prefer documenting failure modes (missed floors, split rooms, noise) over inventing precision.

## Related

- Track C1: `review_status=proposed|accepted|rejected` on room/equipment properties
- Track C2: `arx export --format ifc` warns on proposed; `--approved-only` strips proposed/rejected auto entities
- `docs/pilot-runbook.md`
