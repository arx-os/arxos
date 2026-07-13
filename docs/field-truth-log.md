# Field-truth log template (R1 / R2 / R6 / P-Field-truth)

**Purpose:** Evidence to relegate “lab only” claims. One file per pilot building (or attach privately if data cannot live in git).

**Pin under test:** ________________  
**Site / building:** ________________  
**Date:** ________________  
**Operator:** ________________  

---

## A. Vendor IFC interop matrix (R2)

| Source file (redacted name) | Tool / version | Import OK? | Floors in | Floors out | Rooms in | Rooms out | Notes (drops, panics, units) |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| | | [ ] | | | | | |
| | | [ ] | | | | | |
| | | [ ] | | | | | |

Commands used:

```text
arx import <file>
arx validate
arx export --format ifc --output roundtrip.ifc
arx import roundtrip.ifc   # optional re-import check
```

**R2 pilot-mitigated when:** ≥1 real district-class IFC imported without panic; preserve/drop list written above.

---

## B. LiDAR failure modes (R1)

| Scan (redacted) | Environment | False rooms | Missed rooms | Split/merge issues | Review actions | Notes |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| | | | | | accepted/rejected | |

**Policy check:** No unreviewed `proposed` used as official? [ ] Yes

**R1 pilot-mitigated when:** Either (1) LiDAR in scope and failure log filled + review enforced, or (2) pilot charter marks LiDAR **out of scope** (IFC-only).

---

## C. Performance profile (R6)

| Hardware | OS | Input | Wall time | Peak RAM (approx) | Light mode? | Result |
| :--- | :--- | :--- | :--- | :---: | :---: | :--- |
| | | | | | [ ] | |

Limits adopted for this pilot:

- Max points / file size: ________________  
- Prefer light mode when: ________________  

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

**Related:** `docs/l1-supported-workflow.md` · `docs/ifc-limitations.md` · `arxos_manifest.md` §1.6
