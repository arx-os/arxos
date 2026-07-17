# Pilot Starter Pack (zip-ready checklist)

**Pin:** `v2.0.0-pilot.5` @ `latest`  
**Audience:** Site team (pilot owner, capture tech, second person)  
**Authority:** [`arxos_manifest.md`](../arxos_manifest.md) §1.1a · §1.6 · [horizon-b-roadmap.md](./horizon-b-roadmap.md)

Use this list to assemble a **private** share (zip, USB, or internal drive).  
**Do not** put facility IFC / scans in a public repo.

---

## 1. Pack contents (required)

Copy these files from the pin checkout (`docs/` unless noted):

| # | File | Why |
| :---: | :--- | :--- |
| 1 | [pilot-charter.md](./pilot-charter.md) | S1 · R10 sign |
| 2 | [data-classification.md](./data-classification.md) | S2 · R7 |
| 3 | [pilot-release.md](./pilot-release.md) | Pin table + install |
| 4 | [field-day-1-runbook.md](./field-day-1-runbook.md) | **S3 + S5** commands |
| 5 | [l1-supported-workflow.md](./l1-supported-workflow.md) | Only supported loop |
| 6 | [second-person-checklist.md](./second-person-checklist.md) | S4 · R5 |
| 7 | [field-truth-log.md](./field-truth-log.md) | S5/S6 evidence template |
| 8 | [ifc-limitations.md](./ifc-limitations.md) | Honesty / unmapped products |
| 9 | [resource-limits.md](./resource-limits.md) | R6 refuse / env overrides |
| 10 | [lidar-confidence.md](./lidar-confidence.md) | Scores ≠ probability |
| 11 | [field-handoff.md](./field-handoff.md) | Ordered B0–B3 packet |
| 12 | [INDEX.md](./INDEX.md) | Doc map |

### Optional (eng / later)

| File | When |
| :--- | :--- |
| [horizon-b-roadmap.md](./horizon-b-roadmap.md) | Pilot owner / eng |
| [s8-reconciliation-template.md](./s8-reconciliation-template.md) | End of sprint |
| [sprint-status-dashboard.md](./sprint-status-dashboard.md) | Weekly status |
| [eng-blocker-queue.md](./eng-blocker-queue.md) | If software stuck |
| [hb3-lidar-plan.md](./hb3-lidar-plan.md) | After S1–S8 green |
| `scripts/l1_smoke.sh` | From pin tree (S3) |
| `test_data/sample_building.ifc` | Dry-run only (not R2) |

---

## 2. Build the zip (from pin checkout)

```bash
git checkout v2.0.0-pilot.5
git rev-parse HEAD   # latest pilot.5 commit SHA

mkdir -p /tmp/arxos-pilot-starter-pack
cp docs/pilot-charter.md \
   docs/data-classification.md \
   docs/pilot-release.md \
   docs/field-day-1-runbook.md \
   docs/l1-supported-workflow.md \
   docs/second-person-checklist.md \
   docs/field-truth-log.md \
   docs/ifc-limitations.md \
   docs/resource-limits.md \
   docs/lidar-confidence.md \
   docs/field-handoff.md \
   docs/INDEX.md \
   docs/pilot-starter-pack.md \
   /tmp/arxos-pilot-starter-pack/

# optional:
cp docs/horizon-b-roadmap.md docs/s8-reconciliation-template.md \
   docs/sprint-status-dashboard.md docs/hb3-lidar-plan.md \
   /tmp/arxos-pilot-starter-pack/ 2>/dev/null || true

printf '%s\n' \
  "ArxOS Pilot Starter Pack" \
  "Pin: v2.0.0-pilot.5 @ latest" \
  "Built: $(date -u +%Y-%m-%dT%H:%MZ)" \
  "Start: field-day-1-runbook.md after charter/data-class" \
  > /tmp/arxos-pilot-starter-pack/README-PACK.txt

cd /tmp && zip -r arxos-pilot-starter-pack-pilot.5.zip arxos-pilot-starter-pack
# share arxos-pilot-starter-pack-pilot.5.zip on internal channel only
```

---

## 3. Site team roles (who opens what)

| Role | Open first | Complete |
| :--- | :--- | :--- |
| Pilot owner | charter · data-classification · field-handoff | S1, S2 sign-off |
| Capture tech | field-day-1-runbook · resource-limits · ifc-limitations | S3, S5 (+ S6 later) |
| Second person | second-person-checklist · l1-supported-workflow · pilot-release | S4 only |
| Reviewer (LiDAR) | lidar-confidence · field-truth §B | accept/reject `proposed` |

---

## 4. Day-0 readiness checklist

- [ ] Pack unzipped on internal share (not public GitHub)
- [ ] Pin SHA written on charter draft
- [ ] Capture node named (laptop/Mini preferred)
- [ ] IFC path secured (or scheduled with BIM contact)
- [ ] Second person **named** (Q5)
- [ ] Signers named for charter + data class (Q8)
- [ ] Site name / window known (Q1)
- [ ] No plan to use CAD plugins or agent as export authority

---

## 5. Execution order (do not skip)

```text
S1 charter → S2 data class → S3 pin smoke → S4 second person
  → S5 real IFC + field-truth → (optional S6 LiDAR)
  → S7 eng blockers only → S8 reconcile
```

**Primary path for Day 1 capture:** [field-day-1-runbook.md](./field-day-1-runbook.md)

---

## 6. What is *not* in the pack

| Excluded | Why |
| :--- | :--- |
| Facility IFC / point clouds | Sensitive; supply separately under data class |
| Blockchain / mint docs | Not L1 success |
| PWA / agent field guide | HB6 later; CLI-first |
| CAD plugins | Unsupported forever for L1 |

**Related:** [field-handoff.md](./field-handoff.md) · [sprint-status-dashboard.md](./sprint-status-dashboard.md)
