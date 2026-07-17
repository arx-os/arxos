# Field-truth log (R1 / R2 / R6 / P-Field-truth)

**Purpose:** Evidence to relegate “lab only” claims. One file per pilot building  
(or attach privately if data cannot live in git).

**Authority:** [`arxos_manifest.md`](../arxos_manifest.md) §1.6 · [horizon-b-roadmap.md](./horizon-b-roadmap.md)  
**Day-1 commands:** [field-day-1-runbook.md](./field-day-1-runbook.md)  
**HB3 LiDAR plan:** [hb3-lidar-plan.md](./hb3-lidar-plan.md)

| Header | Value |
| :--- | :--- |
| **Pin under test** | `v2.0.0-pilot.5` @ `latest` (or charter): ________ |
| **Site / building** | ________ |
| **Operator** | ________ |
| **Date opened** | ________ |
| **BIM path** | Vendor BIM → clean IFC → `arx import ifc` |
| **No CAD plugins** | [ ] Confirmed |

**How to close R\*:** Filled rows + sign-off. Eng must not mark R1/R2/R6 **Done** without  
a path to this log (or private redacted copy). Lab buildingSMART alone ≠ R2 closed.

---

## A. S5 — Real IFC import row (R2)

Use **one row per distinct source IFC**. Prefer district/vendor files (not repo samples).

### A1. Preservation matrix

| Field | Row 1 | Row 2 (optional) |
| :--- | :--- | :--- |
| Source file (redacted name) | | |
| Tool / version (Revit, etc.) | | |
| Schema if known (IFC4/…) | | |
| File size (approx) | | |
| Import OK? (no panic) | [ ] Y / [ ] N | [ ] Y / [ ] N |
| Floors in file (approx) | | |
| Floors in Arx after import | | |
| Rooms/spaces in → out | | |
| Equipment in → out (approx) | | |
| GlobalIds preserved on kept entities? | [ ] Y / [ ] N / [ ] partial | |
| Export OK? (`arx export --format ifc`) | [ ] Y / [ ] N | |
| Re-import OK? (optional) | [ ] Y / [ ] N / [ ] skip | |
| Wall time import (min) | | |
| Notes (units, drops, surprises) | | |

### A2. LossReport summary (required)

From `arx import ifc` stdout (or `import-ifc.log`). Codes look like `[unmapped_products]`.

| Import # | Warning codes (list) | `unmapped_products` detail (classes×counts) | Other codes | Surprised? | Action taken |
| :---: | :--- | :--- | :--- | :---: | :--- |
| 1 | | | | Y/N | |
| 2 | | | | Y/N | |

**Paste block (optional, redacted):**

```text
Warnings (N):
  - [code] message…
```

| Honesty check | |
| :--- | :---: |
| Operator read warnings (did not assume “validate OK” = full BIM) | [ ] |
| `unmapped_products` expected if walls/doors present | [ ] understood |

### A3. Commands used

```text
arx import ifc <file> 2>&1 | tee import-ifc.log
# Lenient address validation is default. Add --strict-addresses for strict QA gating:
arx validate --strict-addresses 2>&1 | tee validate.log
arx export --format ifc --output exports/out.ifc 2>&1 | tee export.log
# optional: arx import ifc exports/out.ifc
```

**R2 pilot-mitigated when:** ≥1 real site/district IFC row in A1 **and** A2 filled.  
See [ifc-limitations.md](./ifc-limitations.md).

---

## B. S6 / HB3 — Real LiDAR row (R1)

Skip if charter marks LiDAR **out of scope**. Otherwise one row per scan session.

### B1. Capture + review matrix

| Field | Session 1 | Session 2 (optional) |
| :--- | :--- | :--- |
| Scan file (redacted) | | |
| Format (PLY/LAS/…) | | |
| Hardware / device | | |
| Environment (room/wing/floor) | | |
| Import OK? | [ ] Y / [ ] N | |
| Light mode / voxel size | | |
| Auto rooms created (approx) | | |
| False rooms (+) | | |
| Missed rooms (−) | | |
| Split/merge issues | | |
| Auto equipment (+) / false | | |
| Review: accepted count | | |
| Review: rejected count | | |
| Still `proposed` at export? | [ ] none official | |
| `--approved-only` export OK? | [ ] Y / [ ] N | |
| Notes | | |

### B2. LiDAR LossReport / warnings

| Session | Codes / messages from import log | Action |
| :---: | :--- | :--- |
| 1 | | |
| 2 | | |

### B3. Policy

| Check | |
| :--- | :---: |
| No unreviewed `proposed` used as official | [ ] |
| Confidence not presented as calibrated % accuracy | [ ] |
| Reviewer name | ________ |

Confidence policy: [lidar-confidence.md](./lidar-confidence.md).  
Commands: [hb3-lidar-plan.md](./hb3-lidar-plan.md).

**R1 pilot-mitigated when:** B1 filled + review enforced **or** charter LiDAR out of scope.

---

## C. Performance profile (R6)

| Hardware | OS | Input (IFC/scan) | Wall time | Peak RAM (approx) | Light mode? | Result |
| :--- | :--- | :--- | :--- | :--- | :---: | :--- |
| | | | | | [ ] | |
| | | | | | [ ] | |

**Limits for this pilot** ([resource-limits.md](./resource-limits.md)):

| Setting | Value used |
| :--- | :--- |
| Max IFC / LiDAR / points | |
| Env overrides (`ARX_MAX_*`) | |
| Prefer light mode when | |
| Prefer Mini/laptop over Pi when | |

**R6 pilot-mitigated when:** ≥1 representative run logged above.

---

## D. Product bugs to file

| # | Symptom | Command | Severity | Stuck-list / issue |
| :---: | :--- | :--- | :---: | :--- |
| 1 | | | | |
| 2 | | | | |

---

## Sign-off

| Role | Name | Date | Signature / initials |
| :--- | :--- | :--- | :--- |
| Operator | | | |
| Pilot owner | | | |
| Reviewer (if LiDAR) | | | |

### R\* pilot-mitigation ticks (S8 / manifest)

Use [s8-reconciliation-template.md](./s8-reconciliation-template.md).  
Manifest example: `Partial — pilot-mitigated: <path or private ref> · <date> · <name>`

```text
R2: [ ] pilot-mitigated — A1 rows: __ · A2 filled: [ ] · date: ____
R1: [ ] pilot-mitigated / [ ] LiDAR out of scope — date: ____
R6: [ ] pilot-mitigated — C rows: __ · date: ____
R5: second-person-checklist path: ________
R7/R10: charter + data-classification paths: ________
```

**Evidence pack (private):** `import-*.log` · `validate*.log` · `export*.log` · this form · pin SHA screenshot.

**Related:** [pilot-starter-pack.md](./pilot-starter-pack.md) · [field-day-1-runbook.md](./field-day-1-runbook.md) · [sprint-status-dashboard.md](./sprint-status-dashboard.md) · [ifc-limitations.md](./ifc-limitations.md)
