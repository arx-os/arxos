# Field-truth log (R1 / R2 / R6 / P-Field-truth)

**Purpose:** Evidence to relegate “lab only” claims. One file per pilot building
(or attach privately if data cannot live in git).

**Authority:** [`arxos_manifest.md`](../arxos_manifest.md) §1.6 · living plan [horizon-b-roadmap.md](./horizon-b-roadmap.md)  
**Pin under test:** `v2.0.0-pilot.4` @ `659bbd9f` (or charter pin): ________________  
**Site / building:** ________________  
**Date:** ________________  
**Operator:** ________________  

**BIM path used:** Vendor BIM → clean IFC export → `arx import ifc`  
**No CAD plugins:** [ ] Confirmed  

**How to close R\*:** Only with filled rows below + sign-off. Eng must not mark
R1/R2/R5/R6/R7/R10 **Done** without a path to this log (or private redacted
copy) and the matching checklist/charter. See roadmap § evidence guardrails.

---

## A. Vendor IFC interop matrix (R2)

| Source file (redacted name) | Tool / version | Import OK? | Floors in | Floors out | Rooms in | Rooms out | GlobalIds preserved? | `unmapped_products`? | Notes (drops, panics, units) |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| | | [ ] | | | | | [ ] | [ ] | |
| | | [ ] | | | | | [ ] | [ ] | |
| | | [ ] | | | | | [ ] | [ ] | |

### A2. LossReport capture (required per import)

Paste or summarize CLI warnings after import (codes + counts).  
Expect `unmapped_products` when walls/slabs/doors/windows exist in file.

```text
# from arx import ifc output:
# Warnings (N):
#   - [unmapped_products] …
#   - [other codes] …
```

| Import # | Codes seen | Total unmapped (if any) | Surprised? (Y/N) | Action |
| :---: | :--- | :--- | :---: | :--- |
| 1 | | | | |
| 2 | | | | |

Commands used:

```text
arx import ifc <file>
arx validate
arx export --format ifc --output roundtrip.ifc
# optional:
arx import ifc roundtrip.ifc
```

**R2 pilot-mitigated when:** ≥1 real district-class IFC imported without panic;
preserve/drop list written above **and** LossReport/A2 filled. Revit/ArchiCAD
slots remain open until real files are logged (see [ifc-limitations.md](./ifc-limitations.md)).  
Lab buildingSMART alone does **not** close R2.

---

## B. LiDAR failure modes (R1)

| Scan (redacted) | Environment | False rooms (+) | Missed rooms (−) | Split/merge issues | Review actions | Notes |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| | | | | | accepted/rejected | |

**Policy check:** No unreviewed `proposed` used as official? [ ] Yes  
Confidence scores are **not** probabilistic — see [lidar-confidence.md](./lidar-confidence.md).

**R1 pilot-mitigated when:** Either (1) LiDAR in scope and failure log filled +
review enforced, or (2) pilot charter marks LiDAR **out of scope** (IFC-only).

---

## C. Performance profile (R6)

| Hardware | OS | Input | Wall time | Peak RAM (approx) | Light mode? | Result |
| :--- | :--- | :--- | :--- | :---: | :---: | :--- |
| | | | | | [ ] | |

Limits adopted for this pilot (defaults: [resource-limits.md](./resource-limits.md)):

- Max points / file size: ________________  
  (defaults: 20M points / 512 MiB LiDAR / 50 MiB IFC unless env raised)  
- Prefer light mode when: ________________  
- Prefer Mini/laptop over Pi when: ________________  
- Env overrides used (`ARX_MAX_*`): ________________  

**R6 pilot-mitigated when:** One worst-case (or representative) run is logged and limits are written.

---

## D. Product bugs to file

| # | Symptom | Command | Severity | Issue link |
| :---: | :--- | :--- | :---: | :--- |
| 1 | | | | |
| 2 | | | | |

---

## Sign-off

| Role | Name | Date |
| :--- | :--- | :--- |
| Operator | | |
| Pilot owner | | |

### R\* pilot-mitigation ticks (for S8 / manifest)

Use with [s8-reconciliation-template.md](./s8-reconciliation-template.md).  
Manifest §1.6 Status example: `Partial — pilot-mitigated: <this file path or private ref> · <date>`.

```text
R2: [ ] pilot-mitigated — §A rows: __ · §A2 filled: [ ] · date: ____
R1: [ ] pilot-mitigated / [ ] LiDAR out of scope in charter — date: ____
R6: [ ] pilot-mitigated — §C rows: __ · date: ____
R5: see second-person-checklist (not this file)
R7/R10: see charter + data-classification (not this file)
```

**Related:** [horizon-b-roadmap.md](./horizon-b-roadmap.md) · [field-day-1-runbook.md](./field-day-1-runbook.md) · [l1-supported-workflow.md](./l1-supported-workflow.md) · [ifc-limitations.md](./ifc-limitations.md) · [`arxos_manifest.md`](../arxos_manifest.md) §1.6
