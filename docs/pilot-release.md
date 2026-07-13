# Pilot release pinning (R9)

**Obligation:** R9 — support / change control  
**Goal:** District installs a **known** ArxOS revision, not floating `main`.

---

## Why pin

`main` moves. A pilot that “worked last Tuesday” must be reproducible for:

- second-person walkthrough (R5),  
- incident review,  
- comparing before/after a bugfix.

## Active pin log

| Tag | Commit SHA | Date | Notes |
| :--- | :--- | :--- | :--- |
| `v2.0.0-pilot.3` | `5449838a565b43efc9c9c9185a3389c9895e791c` | 2026-07-12 | **Preferred pin** |
| `v2.0.0-pilot.2` | `d6a4567f98c74d324041d1461c7a310b706ecc1b` | 2026-07-12 | R5 friction fixes |
| `v2.0.0-pilot.1` | `ba33e6ba7ebad55a61a54a9dae68d4508dbdd9d7` | 2026-07-12 | Superseded |

Update this table in a **follow-up commit after** a new tag is cut.

## How to install a pin (field)

```bash
git clone <approved-remote> arxos
cd arxos
git checkout v2.0.0-pilot.3
cargo install --path . --locked
arx --version
```

If `cargo install --locked` fails on the target machine, still checkout the tag
and install without `--locked`, but **record the commit SHA** in the charter.

## How to cut a pilot tag (engineering)

```bash
./scripts/pin_pilot_release.sh v2.0.0-pilot.N --dry-run
./scripts/pin_pilot_release.sh v2.0.0-pilot.N
```

Record tag **and** full SHA in the pilot charter.

## What not to do

| Don’t | Do instead |
| :--- | :--- |
| `git pull` mid-pilot without re-charter | Stay on pin until pilot review |
| “Just use latest main” for district image | Pin + re-walkthrough if you must upgrade |
| Mix pins across techs | One pin per pilot charter |

## Upgrade path mid-pilot

1. Document why upgrade is required.  
2. Cut a new `v2.0.0-pilot.N` from a fixed commit.  
3. Re-run **second-person checklist** on the new pin (abbreviated OK if only bugfix).  
4. Amend charter pin field.

**Related:** [field-handoff.md](./field-handoff.md) · [l1-supported-workflow.md](./l1-supported-workflow.md) · [second-person-checklist.md](./second-person-checklist.md)
