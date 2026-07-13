# HB3 proposal — first real LiDAR + review loop

**Status:** Outline only. **Start only after S1 + S4 + S5 green** (or charter marks practice scan non-official).  
**Pin:** `v2.0.0-pilot.4` @ `659bbd9f`  
**Maps to:** Horizon B phase HB3 · R1 · G4/G6 field · sprint S6 expanded  
**CLI-first:** capture node runs `arx import lidar`; PWA capture is **out of scope** until Q6 + HB6.

---

## 1. Goal

Prove on **real geometry** (one room or wing):

```text
scan file → arx import lidar → proposed entities
  → human accept/reject → validate → Git
  → arx export --format ifc --approved-only
  → field-truth §B (+ §C timing)
```

Honesty: confidence floats are **not** probability ([lidar-confidence.md](./lidar-confidence.md)).  
No unreviewed `proposed` as official.

---

## 2. Gates (all required before “R1 pilot-mitigated”)

| # | Gate | Check |
| :---: | :--- | :--- |
| G0 | S1 charter: LiDAR **in scope** | Checkbox on charter |
| G1 | S5 complete (or IFC base optional) | field-truth §A if IFC used |
| G2 | S4 pass/conditional | Second person not blocked forever |
| G3 | Hardware + format known (Q2) | File opens with `import lidar` |
| G4 | Capture node not Pi-class for large clouds | [resource-limits.md](./resource-limits.md) |
| G5 | Reviewer named | Accept/reject owner |

If LiDAR remains unavailable: mark charter **LiDAR out of scope** and skip HB3 (IFC-only L1 path).

---

## 3. Effort & roles

| Role | Work |
| :--- | :--- |
| Capture tech | Scan export, import, logs |
| Reviewer | Accept/reject `proposed` rooms/equip |
| Eng | Only import crash / format / OOM stuck-list |
| Pilot owner | Sign that no proposed went official |

**Effort:** 1–3 site sessions + half-day log/writeup.

---

## 4. Verification commands (capture node)

```bash
cd ~/arx-pilots/SITE_NAME
# optional IFC base already imported from S5

# Prefer light mode on first real scan
arx import lidar /secure/path/to/scan.ply --light --voxel-size 0.20 2>&1 | tee import-lidar.log
# or --merge if merging into existing building.yaml (see --help)

arx validate 2>&1 | tee validate-lidar.log

# Human review: set review_status via arx edit / TUI / room|equipment commands
# (exact edit keys: l1-supported-workflow + lidar-confidence)
# Accept good autos; reject false rooms.

arx export --format ifc --approved-only --output exports/approved.ifc 2>&1 | tee export-approved.log
ls -la exports/approved.ifc

# optional local git
arx stage
arx commit -m "lidar room/wing: reviewed proposed"
```

| If… | Action |
| :--- | :--- |
| Point / file limit refuse | Log §C; raise `ARX_MAX_*` only with headroom; or more aggressive `--light` |
| Many false rooms | Reject + log §B false (+); do not lower validation |
| Import panic | Stop → eng S7 stuck-list |
| Tempted to export without review | **Forbidden** for official |

---

## 5. Evidence (field-truth §B)

Fill [field-truth-log.md](./field-truth-log.md) **§B S6 template**:

- Scan redacted name, environment, hardware  
- False (+), missed (−), split/merge  
- Review actions counts  
- LossReport / warnings from lidar import log  
- Confirm: no unreviewed proposed as official  
- §C wall time / RAM / light mode  

**R1 pilot-mitigated when:** §B filled + review enforced **or** charter LiDAR OOS.

---

## 6. Success criteria

| Criterion | Pass |
| :--- | :---: |
| ≥1 real scan imported without panic | [ ] |
| ≥1 entity accepted and ≥0 rejected (or all rejected with reason) | [ ] |
| `--approved-only` export succeeds | [ ] |
| field-truth §B + sign-off | [ ] |
| No confidence marketed as % accuracy | [ ] |

---

## 7. Explicit non-goals (HB3)

- Full-floor or 250k capture (→ HB4/HB5)  
- PWA in-browser LiDAR  
- Detector “accuracy product” without logs  
- Wall/slab IFC mapping  
- Horizon C  

---

## 8. After HB3

| Next | When |
| :--- | :--- |
| **HB4** multi-room/wing site loop | §B green + S1/S4/S5 still green |
| **HB5** scale profile | Large scan or large IFC available |
| **HB6** device review UX | Q6 + field evidence |

**Related:** [field-truth-log.md](./field-truth-log.md) · [l1-supported-workflow.md](./l1-supported-workflow.md) · [resource-limits.md](./resource-limits.md) · [lidar-confidence.md](./lidar-confidence.md)
