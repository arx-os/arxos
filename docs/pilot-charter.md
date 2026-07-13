# ArxOS L1 pilot charter (template)

**Obligation:** R10 (safety/liability), R1 process, R8 (chain off by default)  
**Go level:** L1 — controlled free-software pilot on **one** building  
**Fill in blanks · print or PDF · sign before pilot start**

---

## 1. Parties

| Role | Name | Contact |
| :--- | :--- | :--- |
| Pilot owner (authority to run software) | | |
| Capture / ops tech | | |
| Second-person walkthrough partner | | |
| Reviewer (accept/reject auto structure) | | |
| Engineering contact (if any) | | |

## 2. Scope

| Item | Value |
| :--- | :--- |
| **Go level** | **L1 only** (not multi-building program, not production token economy) |
| Building name / site | |
| Building ID (Arx UUID after `arx init`) | |
| Allowed inputs | [ ] IFC  [ ] LiDAR  [ ] text edits |
| Git remote location (must be internal) | |
| Pinned Arx install (tag or commit) | `v2.0.0-pilot.__` / commit ________ |
| Pilot start date | |
| Pilot end / review date | |

**In scope:** Local map → review → validate → Git → internal IFC/YAML export for the named building.  
**Out of scope for L1:** Mainnet $AXD, multi-oracle production mint, public data market, campus multi-building layout, PWA capture, safety sign-off of models.

## 3. Safety and professional liability (required)

**ArxOS is assistive software and a versioned as-built ledger. It is not:**

- a substitute for licensed architectural/engineering drawings or stamped documents;
- a substitute for lockout/tagout (LOTO), live-work policy, or trade licensing;
- a guarantee of completeness, accuracy, or code compliance;
- authority to energize, dig, cut, or work on systems without independent verification.

**Human and licensed documentation always win** over the Arx model when they conflict.

**LiDAR / auto-detected structure:**

- Auto entities start as `review_status=proposed`.
- **Unreviewed `proposed` entities must not be treated as official** for work planning, bidding, or safety decisions.
- Reviewer must `accepted` or `rejected` before any “official” export or contractor handoff that claims Arx as source.

Initials — Pilot owner: ______  Reviewer: ______

## 4. Data classification (R7)

| Rule | Agreed |
| :--- | :---: |
| Pilot repo and exports are **internal-only** (not public GitHub by default) | [ ] |
| No student PII or confidential personnel data in properties/names | [ ] |
| Facility sensitivity treated at least as strictly as CAD/as-built drawings | [ ] |
| Who may clone the repo: ________________ | [ ] |
| Who may export IFC/YAML off the capture node: ________________ | [ ] |

## 5. Chain / token (R8)

| Rule | Agreed |
| :--- | :---: |
| L1 success **does not** require $AXD mint or payment | [ ] |
| No mainnet token use in this pilot | [ ] |
| Anvil/testnet demo only if explicitly requested by: ________________ | [ ] |

## 6. Support and change control (R9)

| Rule | Agreed |
| :--- | :---: |
| Install only from **pinned tag/commit** (not floating `main`) | [ ] |
| Supported workflow is only `docs/l1-supported-workflow.md` | [ ] |
| Escalation: file issue / note blocker; no silent “force” of bad data | [ ] |
| Pilot owner is operational owner for district side | [ ] |

## 7. Success criteria (L1)

Mark at end of pilot:

| Criterion | Y/N |
| :--- | :---: |
| Second person completed walkthrough (`docs/second-person-checklist.md`) | |
| At least one useful as-built task improved (describe): ________ | |
| Failure modes for this site written down (IFC and/or LiDAR) | |
| No unreviewed `proposed` used as official | |
| Charter still accurate (or amended in writing) | |

## 8. Sign-off

| Role | Signature | Date |
| :--- | :--- | :--- |
| Pilot owner | | |
| Capture tech | | |
| Reviewer | | |
| Security/IT (if required) | | |

---

**Related:** `docs/l1-supported-workflow.md` · `docs/second-person-checklist.md` · `docs/field-trial.md` · `arxos_manifest.md` §1.6
