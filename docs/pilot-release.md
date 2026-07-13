# Pilot release pinning (R9)

**Obligation:** R9 — support / change control  
**Goal:** District installs a **known** ArxOS revision, not floating `main`.

---

## Why pin

`main` moves. A pilot that “worked last Tuesday” must be reproducible for:

- second-person walkthrough (R5),  
- incident review,  
- comparing before/after a bugfix.

## How to cut a pilot tag (engineering)

**Preferred:** script enforces clean tree, runs lib + spine tests, creates annotated tag:

```bash
./scripts/pin_pilot_release.sh v2.0.0-pilot.1 --dry-run   # preview
./scripts/pin_pilot_release.sh v2.0.0-pilot.1             # create tag
```

Manual equivalent if needed:

```bash
cargo test --lib
cargo test --test compiler_spine_test
# optional: cd contracts && forge test
git tag -a v2.0.0-pilot.1 -m "L1 pilot pin"
# git push origin v2.0.0-pilot.1   # only if remote policy allows
```

Record in the pilot charter:

- tag name, **and**  
- full commit SHA (`git rev-list -n1 v2.0.0-pilot.1`).

### Active pin log

| Tag | Commit SHA | Date | Notes |
| :--- | :--- | :--- | :--- |
| `v2.0.0-pilot.1` | _(after cut: `git rev-list -n1 v2.0.0-pilot.1`)_ | | First L1 eng pin — also record in charter |

Update this table in a **follow-up commit after** the tag is cut (do not retag to include the table row).

## How to install a pin (field)

```bash
git clone <approved-remote> arxos
cd arxos
git checkout v2.0.0-pilot.1
cargo install --path . --locked
arx --version
```

If `cargo install --locked` fails on the target machine, still checkout the tag and install without `--locked`, but **record the commit SHA** in the charter.

## What not to do

| Don’t | Do instead |
| :--- | :--- |
| `git pull` mid-pilot without re-charter | Stay on pin until pilot review |
| “Just use latest main” for district image | Pin + re-walkthrough if you must upgrade |
| Mix pins across techs | One pin per pilot charter |

## Upgrade path mid-pilot

1. Document why upgrade is required.  
2. Cut `v2.0.0-pilot.2` from fixed commit.  
3. Re-run **second-person checklist** on the new pin (abbreviated OK if only bugfix).  
4. Amend charter pin field.

**Related:** `docs/field-handoff.md` · `docs/l1-supported-workflow.md` · `docs/second-person-checklist.md` · `docs/install.md`
