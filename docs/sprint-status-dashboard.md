# HB0–HB2 sprint status dashboard (weekly)

**Pin:** `v2.0.0-pilot.5` @ `latest`  
**Living plan:** [horizon-b-roadmap.md](./horizon-b-roadmap.md)  
**Update:** once per week (or after each S* closes). Copy this file privately per pilot if needed.

| Field | Value |
| :--- | :--- |
| **Site** | ________________ |
| **Week of** | ________________ |
| **Pilot owner** | ________________ |
| **Last update** | ________________ |
| **Overall** | [ ] Not started · [ ] In progress · [ ] Blocked · [ ] Sprint green |

---

## S1–S8 status

| ID | Task | Owner | Status | Evidence path / note | Updated |
| :---: | :--- | :--- | :---: | :--- | :--- |
| S1 | Charter signed + pin recorded | Field/leadership | ⬜ | | |
| S2 | Data class + private remote | Field IT | ⬜ | | |
| S3 | Pin install + `l1_smoke` PASS | Capture tech | ⬜ | SHA: | |
| S4 | Second-person checklist | Non-author | ⬜ | Pass/Cond/Fail: | |
| S5 | Real IFC + LossReport (field-truth A/A2) | Capture + eng standby | ⬜ | | |
| S6 | LiDAR room/wing (optional) | Capture | ⬜ / N/A | | |
| S7 | Eng blockers only | Eng | ⬜ / none | Issues: | |
| S8 | Reconcile R\* + roadmap | Eng + field | ⬜ | [s8 template](./s8-reconciliation-template.md) | |

**Status key:** ⬜ not started · 🟡 in progress · 🟢 done · 🔴 blocked · N/A skipped with reason

---

## R\* close checklist (L1)

| ID | Obligation | Target this sprint | Status | Evidence |
| :---: | :--- | :--- | :---: | :--- |
| R10 | Signed charter | S1 | ⬜ | |
| R9 | Pin + supported workflow | S3 (+ S4 uses pin) | ⬜ | |
| R7 | Data class + private remote | S2 | ⬜ | |
| R5 | Second-person cold start | S4 | ⬜ | |
| R2 | Real IFC + LossReport | S5 | ⬜ | field-truth §A+A2 |
| R1 | LiDAR truth or out of scope | S6 or charter | ⬜ | §B or OOS |
| R6 | Site performance log | S5/S6 large run | ⬜ | §C |
| R8 | Chain off by default | Charter §5 | ⬜ | |
| R3/R4 | Chain/host production | **Not L1** | — | leave open |

**Manifest §1.6 wording when pilot-mitigated:**

```text
Partial — pilot-mitigated: <path or private ref> · <YYYY-MM-DD> · <name>
```

Never mark **Done** without evidence path. Lab buildingSMART ≠ R2 closed.

---

## Blockers this week

| # | Description | Blocks | Owner | ETA |
| :---: | :--- | :--- | :--- | :--- |
| 1 | | | | |
| 2 | | | | |

**Eng E1–E3:** optional polish only — see [eng-blocker-queue.md](./eng-blocker-queue.md). Default: **do not implement**.

---

## Open questions (owner)

| ID | Answered? | Answer |
| :---: | :---: | :--- |
| Q1 Site name / window | [ ] | |
| Q5 Second person name | [ ] | |
| Q8 Charter / data signers | [ ] | |
| Q2 LiDAR hardware | [ ] / N/A | |
| Q3 Capture node | [ ] | |
| Q4 IFC- vs scan-first | [ ] | |
| Q6 PWA parallel | [ ] default No | |
| Q7 BIM / IFC contact | [ ] | |

---

## Weekly narrative (3–5 lines)

```text
This week:
Next week:
Risks:
```

---

## After sprint green → next

- [ ] Run [s8-reconciliation-template.md](./s8-reconciliation-template.md)
- [ ] If S1+S4+S5 green → start [hb3-lidar-plan.md](./hb3-lidar-plan.md)
- [ ] No Horizon C · no PWA productization without Q6

**Related:** [pilot-starter-pack.md](./pilot-starter-pack.md) · [field-day-1-runbook.md](./field-day-1-runbook.md) · [field-truth-log.md](./field-truth-log.md)
