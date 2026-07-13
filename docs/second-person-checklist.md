# Second-person cold-start checklist (R5)

**Obligation:** R5 (transfer), R9 (pin)  
**Who:** Someone who did **not** write the pilot docs or invent the workflow  
**Machine:** District laptop or equivalent (VPN, AV, path policies as production)

**Pin under test:** tag/commit ________________  `arx --version`: ________________  
**Confirm SHA matches charter / [pilot-release.md](./pilot-release.md):** [ ] Yes

---

## Rules

- Use only [l1-supported-workflow.md](./l1-supported-workflow.md) and [pilot-release.md](./pilot-release.md) (no tribal knowledge from the pilot owner).  
- Time each phase.  
- On stuck >10 minutes: write the stuck point; do not skip ahead without noting it.  
- Do **not** use blockchain/mint/pay unless the charter says demo.  
- Do **not** use `agent` / auto-export as the official path.  
- Do **not** install CAD plugins; IFC files only.

---

## Timed run

| # | Step | Target | Actual (min) | Pass? | Stuck notes |
| :---: | :--- | :---: | :---: | :---: | :--- |
| 1 | Install from **pinned** tag/commit | 30 | | [ ] | |
| 2 | `arx --version` / `arx --help` | 2 | | [ ] | |
| 3 | `arx init --name "…"` in a new directory | 5 | | [ ] | |
| 4 | `arx validate` on fresh init | 2 | | [ ] | |
| 5 | Import **sample or pilot IFC** (`test_data/sample_building.ifc` from the pin checkout is OK) | 15 | | [ ] | |
| 5b | Note import **warnings** (any `unmapped_products` or other codes) — do not ignore | 5 | | [ ] | |
| 6 | `arx validate` after import | 5 | | [ ] | |
| 7 | If LiDAR in scope: import + set one `review_status` | 20 | | [ ] | |
| 8 | `arx export --format ifc --output out.ifc` | 10 | | [ ] | |
| 9 | Git stage + commit (local is enough) | 10 | | [ ] | |
| 10 | Could you repeat steps 3–9 next week without help? | — | | [ ] | |

**Total time:** ______ min  

## Environment

| Item | Value |
| :--- | :--- |
| OS | |
| Rust version (`rustc -V`) | |
| Network restrictions (proxy, no cargo, etc.) | |
| Antivirus / path issues | |

## Result

| Outcome | Mark |
| :--- | :---: |
| **Pass** — completed 1–9 without owner sitting at keyboard | [ ] |
| **Conditional** — completed with documented stuck points to fix | [ ] |
| **Fail** — could not complete; pilot not transferable | [ ] |

**Top 3 blockers to file as issues:**

1. ________________________________  
2. ________________________________  
3. ________________________________  

## Sign-off

| Role | Name | Signature | Date |
| :--- | :--- | :--- | :--- |
| Second person (walker) | | | |
| Pilot owner (observer only) | | | |

---

After pass/conditional: update `arxos_manifest.md` §1.6 **R5** status and link this completed checklist path (even if stored outside git for privacy).  
Living plan: [horizon-b-roadmap.md](./horizon-b-roadmap.md) phase **HB1**.

**Related:** [l1-supported-workflow.md](./l1-supported-workflow.md) · [pilot-charter.md](./pilot-charter.md) · [pilot-release.md](./pilot-release.md)
