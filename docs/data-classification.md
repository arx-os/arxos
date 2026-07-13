# Pilot data classification (R7 / P-Data)

**Obligation:** R7 — security / compliance / where models live  
**Use with:** `docs/pilot-charter.md` §4  
**Default for public school districts:** **internal-only**

---

## Classification levels (pick one for the pilot)

| Level | Meaning | Typical placement |
| :--- | :--- | :--- |
| **Internal** | Staff only; not public | Private district Git, restricted file share |
| **Restricted** | Need-to-know (security, MDF, electrical detail) | Same as internal + tighter ACL / no personal laptops |
| **Public** | Open distribution | **Not recommended** for school as-built |

**L1 default:** Internal. Do not use public GitHub for facility models unless Security explicitly approves.

## What may go in the Arx model

| Allowed | Not allowed (without separate approval) |
| :--- | :--- |
| Room names, floor labels used operationally | Student names, IDs, grades (FERPA) |
| Equipment tags, panel IDs as used by facilities | Camera coverage maps labeled for adversaries |
| Generic properties for ops | Passwords, lock codes, alarm PINs |
| IFC geometry / structure | Unredacted security vulnerability notes |

When in doubt: treat like CAD / as-built drawings.

## Access control checklist

| Rule | Owner | Done |
| :--- | :--- | :---: |
| Pilot Git remote URL recorded in charter | Pilot owner | [ ] |
| Remote is **not** public | Pilot owner | [ ] |
| Who may `git clone` (names/roles) | Pilot owner | [ ] |
| Who may export IFC/YAML off capture node | Pilot owner | [ ] |
| Backup location classified same or higher | Pilot owner | [ ] |
| Personal cloud sync (OneDrive/Dropbox) disallowed for pilot tree | Pilot owner | [ ] |

## Export policy (L1)

| Export type | Policy |
| :--- | :--- |
| Internal (`arx export` without `--commercial`) | Same class as model; only approved people |
| `--approved-only` | Prefer for LiDAR-reviewed handoffs |
| `--commercial` | Only with `access-receipt.json` **and** same class rules |

## Sign-off

| Role | Name | Date |
| :--- | :--- | :--- |
| Pilot owner | | |
| Security / IT (if required) | | |

**Related:** `docs/pilot-charter.md` · `arxos_manifest.md` §1.6 R7
