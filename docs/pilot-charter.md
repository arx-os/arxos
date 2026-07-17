# ArxOS L1 pilot charter (template)

**Obligation:** R10 (safety/liability), R1 process, R8 (chain off by default)  
**Go level:** L1 — controlled free-software pilot on **one** building  
**Fill in blanks · print or PDF · sign before pilot start**

**Maturity:** Lab compiler ~8.5/10; district L1 readiness ~5/10 until process +
field evidence close obligations in `arxos_manifest.md` §1.6.  
**Site north star (full §1.1a):** see `docs/horizon-b-roadmap.md` — this charter
gates **controlled L1**. CLI/TUI remains the pin + evidence path; **iPhone PWA + laptop agent**
is under **HB6 acceleration** (`docs/iphone-pwa-acceleration.md`) for on-site review/capture UX,
still with human gates and the same IFC export spine.

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
| Pinned Arx install (tag or commit) | Prefer `v2.0.0-pilot.5` @ `latest` (or exact pin from `docs/pilot-release.md`) |
| Pilot start date | |
| Pilot end / review date | |

**In scope:** Local map → review → validate → Git → internal IFC/YAML export for the named building.  
**Out of scope for L1:** Mainnet $AXD, multi-oracle production mint, public data market, campus multi-building layout, PWA capture, agent-as-export-authority, safety sign-off of models as licensed drawings.

### 2b. BIM / interchange policy (required)

- Vendor models enter Arx **only** as **IFC** files exported from the authoring tool.
- **No** Revit, ArchiCAD, or other CAD plugin, add-in, or direct CAD integration is supported or authorized.
- Official IFC leaving the pilot uses: `arx export --format ifc` (prefer `--approved-only` when LiDAR was used).
- Optional `agent` feature is **edge bridging only** (WebSocket/SSH / file watch). It is **not** required for L1 and is **not** a second IFC export authority.
- **Lenient Validation:** By default, validation permits pragmatic naming of fixtures under reserved systems (errors mapped to warnings). Enforce strict rules via `--strict-addresses` during final QA validation. Unmapped IFC products (including MEP segment classes) are reported dynamically in the `LossReport`.
- Identity rules: `docs/identity.md`. Limitations: `docs/ifc-limitations.md`.

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
- Reviewer must set `accepted` or `rejected` before any “official” export or contractor handoff that claims Arx as source.

Initials — Pilot owner: ______  Reviewer: ______

## 4. Data classification (R7)

Complete **`docs/data-classification.md`** and summarize here:

| Rule | Agreed |
| :--- | :---: |
| Pilot repo and exports are **internal-only** (not public GitHub by default) | [ ] |
| No student PII or confidential personnel data in properties/names | [ ] |
| Facility sensitivity treated at least as strictly as CAD/as-built drawings | [ ] |
| Who may clone the repo: ________________ | [ ] |
| Who may export IFC/YAML off the capture node: ________________ | [ ] |
| Classification form completed (`docs/data-classification.md`) | [ ] |

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

**Related:** [l1-supported-workflow.md](./l1-supported-workflow.md) · [second-person-checklist.md](./second-person-checklist.md) · [field-handoff.md](./field-handoff.md) · [`arxos_manifest.md`](../arxos_manifest.md) §1.6
