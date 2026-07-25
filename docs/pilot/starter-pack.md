# Pilot Starter Pack (zip-ready checklist)

**Pin:** `v2.0.0-pilot.5` @ `ad5213dca08cef52cc90d9b80037f0dbaaa14a8d`  
**Audience:** Site team (pilot owner, capture tech, second person)  
**Authority:** [`arxos_manifest.md`](../../arxos_manifest.md) §1.1a · §1.6 · [horizon-b-roadmap.md](../process/horizon-b-roadmap.md)

Use this list to assemble a **private** share (zip, USB, or internal drive).  
**Do not** put facility IFC / scans in a public repo.

---

## 1. Pack contents (required)

Copy these files from the pin checkout (`docs/` unless noted):

| # | File | Why |
| :---: | :--- | :--- |
| 1 | [charter.md](./charter.md) | S1 · R10 sign |
| 2 | [data-classification.md](./data-classification.md) | S2 · R7 |
| 3 | [release.md](./release.md) | Pin table + install |
| 4 | [day-1-runbook.md](./day-1-runbook.md) | **S3 + S5** commands |
| 5 | [supported-workflow.md](./supported-workflow.md) | Only supported loop |
| 6 | [second-person-checklist.md](./second-person-checklist.md) | S4 · R5 |
| 7 | [field-truth-log.md](./field-truth-log.md) | S5/S6 evidence template |
| 8 | [ifc-limitations.md](../reference/ifc-limitations.md) | Honesty / unmapped products |
| 9 | [resource-limits.md](../reference/resource-limits.md) | R6 refuse / env overrides |
| 10 | [lidar-confidence.md](../reference/lidar-confidence.md) | Scores ≠ probability |
| 11 | [field-handoff.md](./field-handoff.md) | Ordered B0–B3 packet |
| 12 | [INDEX.md](../INDEX.md) | Doc map |

### Optional (eng / later)

| File | When |
| :--- | :--- |
| [horizon-b-roadmap.md](../process/horizon-b-roadmap.md) | Pilot owner / eng |
| [s8-reconciliation-template.md](../process/s8-reconciliation-template.md) | End of sprint |
| [sprint-status-dashboard.md](../process/sprint-status-dashboard.md) | Weekly status |
| [eng-blocker-queue.md](../process/eng-blocker-queue.md) | If software stuck |
| [hb3-lidar-plan.md](../process/hb3-lidar-plan.md) | After S1–S8 green |
| `scripts/l1_smoke.sh` | From pin tree (S3) |
| `test_data/sample_building.ifc` | Dry-run only (not R2) |

---

## 2. Build the zip (from pin checkout)

```bash
git checkout v2.0.0-pilot.5
git rev-parse HEAD   # must be ad5213dca08cef52cc90d9b80037f0dbaaa14a8d

mkdir -p /tmp/arxos-pilot-starter-pack
cp docs/pilot/charter.md \
   docs/pilot/data-classification.md \
   docs/pilot/release.md \
   docs/pilot/day-1-runbook.md \
   docs/pilot/supported-workflow.md \
   docs/pilot/second-person-checklist.md \
   docs/pilot/field-truth-log.md \
   docs/reference/ifc-limitations.md \
   docs/reference/resource-limits.md \
   docs/reference/lidar-confidence.md \
   docs/pilot/field-handoff.md \
   docs/INDEX.md \
   docs/pilot/starter-pack.md \
   /tmp/arxos-pilot-starter-pack/

# optional:
cp docs/process/horizon-b-roadmap.md docs/process/s8-reconciliation-template.md \
   docs/process/sprint-status-dashboard.md docs/process/hb3-lidar-plan.md \
   /tmp/arxos-pilot-starter-pack/ 2>/dev/null || true

printf '%s\n' \
  "ArxOS Pilot Starter Pack" \
  "Pin: v2.0.0-pilot.5 @ ad5213dca08cef52cc90d9b80037f0dbaaa14a8d" \
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

**Primary path for Day 1 capture:** [day-1-runbook.md](./day-1-runbook.md)

---

## 6. What is *not* in the pack

| Excluded | Why |
| :--- | :--- |
| Facility IFC / point clouds | Sensitive; supply separately under data class |
| Blockchain / mint docs | Not L1 success |
| Native iOS companion | Future only; CLI-first for L1 |
| CAD plugins | Unsupported forever for L1 |

**Related:** [field-handoff.md](./field-handoff.md) · [sprint-status-dashboard.md](../process/sprint-status-dashboard.md)
