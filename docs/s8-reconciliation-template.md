# S8 post-sprint reconciliation template

**When:** End of HB0–HB2 sprint (after S1–S7 attempt)  
**Owner:** Eng drafts · field confirms evidence paths  
**Authority:** [`arxos_manifest.md`](../arxos_manifest.md) §1.6 · [horizon-b-roadmap.md](./horizon-b-roadmap.md) §7  

Copy this section into a private pilot note or a PR description. **Do not mark R\* Done without evidence path.**

---

## 1. Sprint outcomes

| Task | Status | Evidence path (file, share, or checklist) |
| :---: | :---: | :--- |
| S1 Charter signed | [ ] Y / [ ] N / [ ] draft only | |
| S2 Data class + private remote | [ ] Y / [ ] N | |
| S3 Pin install + smoke | [ ] Y / [ ] N | SHA: ________ · smoke: ________ |
| S4 Second-person | [ ] Pass / [ ] Conditional / [ ] Fail / [ ] not run | |
| S5 Real IFC + LossReport A2 | [ ] Y / [ ] N | field-truth: ________ |
| S6 LiDAR (optional) | [ ] Y / [ ] N / [ ] N/A out of scope | |
| S7 Eng blockers | [ ] none / [ ] list: ________ | PR/issue: ________ |

**Pin used:** `v2.0.0-pilot.4` @ `659bbd9f` [ ] confirmed · [ ] drifted (explain)

---

## 2. R\* close format (paste into manifest §1.6 Status cell)

Use **exactly** one of these patterns:

```text
# Still open
Open

# Eng/lab partial only
Partial — <what eng did>; field evidence still open

# Pilot-mitigated (allowed to relegate for L1)
Partial — pilot-mitigated: <evidence path or private ref> · <date> · <operator>

# Fully closed (rare this early)
Done — <evidence path> · <date>
```

| ID | Proposed new Status text | Evidence |
| :---: | :--- | :--- |
| R10 | | signed charter |
| R9 | | pin in charter + S3 |
| R7 | | data-classification + remote |
| R5 | | second-person checklist path |
| R2 | | field-truth §A+A2 (not buildingsmart alone) |
| R1 | | §B or charter LiDAR out of scope |
| R6 | | §C filled or still eng-defaults only |

**field-truth-log close lines (append under Sign-off):**

```text
R2: [ ] pilot-mitigated — matrix rows: __ · A2 filled: [ ] · date:
R1: [ ] pilot-mitigated / [ ] out of scope — date:
R6: [ ] pilot-mitigated — §C rows: __ · date:
```

---

## 3. Scorecard delta (manifest §2.1)

| Link | Before | After (honest) | Why |
| :--- | :---: | :---: | :--- |
| District L1 readiness | ~4/10 | | |
| IFC native | 8/10 | | |
| LiDAR | 6.5/10 | | |
| PWA / WASM | 4/10 | 4/10 unless HB6 | |

---

## 4. Horizon B phase board

| Phase | Status after sprint |
| :---: | :--- |
| HB0 | [ ] open / [ ] partial / [ ] done |
| HB1 | [ ] open / [ ] partial / [ ] done |
| HB2 | [ ] open / [ ] partial / [ ] done |
| HB3+ | leave open unless S6 complete |

Update [horizon-b-roadmap.md](./horizon-b-roadmap.md) §10 status log with one row dated today.

---

## 5. Next-week proposal (check one primary)

- [ ] Clear Conditional R5 stuck-list only  
- [ ] Second IFC / deepen R2  
- [ ] HB3 first real LiDAR room  
- [ ] HB4 site loop (only if S1+S4+S5 green)  
- [ ] Approved E1–E3 only  
- [ ] Other: ________  

**Forbidden without explicit go:** Horizon C · wall mapping · PWA productization (unless Q6 override).

---

## 6. Commit checklist (eng)

- [ ] No R\* Done without path  
- [ ] No public facility models  
- [ ] `cargo clippy --all-targets -- -D warnings` if code  
- [ ] Pin not moved unless install-breaking fix + new pilot.N  

**Related:** [field-truth-log.md](./field-truth-log.md) · [field-day-1-runbook.md](./field-day-1-runbook.md) · [eng-blocker-queue.md](./eng-blocker-queue.md)
