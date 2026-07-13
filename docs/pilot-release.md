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
| **`v2.0.0-pilot.4`** | `659bbd9f369c0b942f150983b204ea054fc595a0` | 2026-07-13 | **Preferred** — TUI default, no hardware/render3d, resource limits, `unmapped_products` LossReport, buildingSMART fixtures |
| `v2.0.0-pilot.3` | `5449838a565b43efc9c9c9185a3389c9895e791c` | 2026-07-12 | Superseded for new pilots (last pin before compiler-core packaging) |
| `v2.0.0-pilot.2` | `d6a4567f98c74d324041d1461c7a310b706ecc1b` | 2026-07-12 | R5 friction fixes |
| `v2.0.0-pilot.1` | `ba33e6ba7ebad55a61a54a9dae68d4508dbdd9d7` | 2026-07-12 | Superseded |

**Next pin** (only after material eng change field must see):

```bash
# clean tree required
./scripts/pin_pilot_release.sh v2.0.0-pilot.N --dry-run
./scripts/pin_pilot_release.sh v2.0.0-pilot.N
# then: git push origin v2.0.0-pilot.N  (when policy allows)
# update this table + pilot charter §2 with tag + full SHA
```

## How to install a pin (field)

**Current preferred pin:** `v2.0.0-pilot.4` @ `659bbd9f369c0b942f150983b204ea054fc595a0`  
**L1 recommended install:** default features = **compiler + TUI** (primary UI). Slim surface: no hardware drivers, no LiDAR point-cloud 3D.

```bash
git clone <approved-remote> arxos
cd arxos
git checkout v2.0.0-pilot.4   # must match charter §2
git rev-parse HEAD            # expect 659bbd9f369c0b942f150983b204ea054fc595a0
cargo install --path . --locked
arx --version
# optional sanity:
./scripts/l1_smoke.sh
```

If `cargo install --locked` fails on the target machine, still checkout the tag
and install without `--locked`, but **record the commit SHA** in the charter.

### Optional rings (not L1 success criteria)

| Need | Build | Notes |
| :--- | :--- | :--- |
| Edge agent (SSH/WebSocket git+IFC) | `--features agent` | No BACnet/hardware drivers |
| WASM terminal PWA | `--features web` | Camera/AR later; hierarchy text now |
| On-chain contribute/pay | `--features blockchain` | EIP-712 sign/submit |
| Everything current | `--features full` | tui+agent+web+blockchain |

**Not in tree for now:** hardware (BACnet/Modbus/MQTT), Bevy/LiDAR point-cloud 3D.

`contribute` / `access` remain available for lab packaging (not L1-required).

Resource defaults: [resource-limits.md](./resource-limits.md).

## How to cut a pilot tag (engineering)

```bash
./scripts/pin_pilot_release.sh v2.0.0-pilot.N --dry-run
./scripts/pin_pilot_release.sh v2.0.0-pilot.N
```

Script runs: clean tree check → clippy → lib + spine tests → L1 smoke → annotated tag.  
Skip smoke with `PIN_SKIP_L1_SMOKE=1` only if offline.

Record tag **and** full SHA in the pilot charter.

## What not to do

| Don’t | Do instead |
| :--- | :--- |
| `git pull` mid-pilot without re-charter | Stay on pin until pilot review |
| “Just use latest main” for district image | Pin + re-walkthrough if you must upgrade |
| Mix pins across techs | One pin per pilot charter |
| New pilot on pilot.3 after compiler-core merges | Cut pilot.4+ so install matches docs |

## Upgrade path mid-pilot

1. Document why upgrade is required.  
2. Cut a new `v2.0.0-pilot.N` from a fixed commit.  
3. Re-run **second-person checklist** on the new pin (abbreviated OK if only bugfix).  
4. Amend charter pin field.

**Related:** [field-handoff.md](./field-handoff.md) · [l1-supported-workflow.md](./l1-supported-workflow.md) · [second-person-checklist.md](./second-person-checklist.md) · [resource-limits.md](./resource-limits.md)
