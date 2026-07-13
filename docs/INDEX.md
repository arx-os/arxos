# ArxOS documentation (pilot-focused)

**Engineering source of truth:** [`../arxos_manifest.md`](../arxos_manifest.md)  
(maturity, obligations R1–R10, integrity ledger, refuse list, horizons)

This folder is **operator documentation** for L1 field pilot.  
If a doc here conflicts with the manifest, **the manifest wins**.

## Maturity (honest)

| Claim | Score |
| :--- | :---: |
| Lab closed loop (compiler + Foundry) | ~8/10 |
| District L1 pilot readiness | ~4/10 |
| Full reward/market (L3) | ~2/10 |

L1 is blocked on **process + field evidence**, not missing framework code.  
See manifest §1.5–1.6.

**Preferred pin:** `v2.0.0-pilot.4` @ `659bbd9f` — [pilot-release.md](./pilot-release.md).  
**Install:** `git checkout v2.0.0-pilot.4 && cargo install --path . --locked` (default = compiler + TUI).

### Lab IFC honesty (Package A, 2026-07)

| Item | Status |
| :--- | :---: |
| Non-panic import on buildingSMART ISO + PCERT samples | Yes |
| `unmapped_products` LossReport (walls/slabs/doors/…) | Yes (pilot.4) |
| District Revit/ArchiCAD anonymized evidence | **Open** (R2 field) |

Details: [ifc-limitations.md](./ifc-limitations.md) · report: [`tests/ifc_buildingsmart_report.md`](../tests/ifc_buildingsmart_report.md)

## Living plan (Horizon B)

| Doc | Role |
| :--- | :--- |
| [horizon-b-roadmap.md](./horizon-b-roadmap.md) | **Living** phases HB0–HB7 → site capture + L1 exit (~250k / PWA north star) |
| [pilot-starter-pack.md](./pilot-starter-pack.md) | **Zip-ready** checklist of all site-team docs |
| [field-day-1-runbook.md](./field-day-1-runbook.md) | **S3+S5** non-author Day 1: pin install → real IFC → LossReport evidence |
| [sprint-status-dashboard.md](./sprint-status-dashboard.md) | Weekly S1–S8 + R\* status table |
| [s8-reconciliation-template.md](./s8-reconciliation-template.md) | Post-sprint R\* / scorecard reconcile |
| [hb3-lidar-plan.md](./hb3-lidar-plan.md) | After S1–S8: first real LiDAR + review (outline) |
| [iphone-pwa-acceleration.md](./iphone-pwa-acceleration.md) | **HB6-accel:** iPhone PWA + agent audit, P0 backlog, test plan |
| [iphone-field-loop.md](./iphone-field-loop.md) | **Batch A** iPhone + laptop connect / Pass A verification |
| [eng-blocker-queue.md](./eng-blocker-queue.md) | E1–E3 optional polish (approval before code) |
| [`../arxos_manifest.md`](../arxos_manifest.md) §1.1a · §10.2 | Authority: Definition of Working + phase summary |

## L1 pilot packet (do in order)

0. [pilot-starter-pack.md](./pilot-starter-pack.md) — assemble zip for site team  
1. [pilot-charter.md](./pilot-charter.md) — sign (R10, R8)  
2. [pilot-release.md](./pilot-release.md) — pin install (R9)  
3. [data-classification.md](./data-classification.md) — private remote (R7)  
4. [l1-supported-workflow.md](./l1-supported-workflow.md) — only supported loop  
5. [second-person-checklist.md](./second-person-checklist.md) — cold start (R5)  
6. [field-day-1-runbook.md](./field-day-1-runbook.md) — S3+S5 execution  
7. [field-truth-log.md](./field-truth-log.md) — real IFC/LiDAR evidence (R1/R2/R6)  
8. [field-handoff.md](./field-handoff.md) — ordered packet checklist

## Compiler reference

| Doc | Topic |
| :--- | :--- |
| [identity.md](./identity.md) | Arx UUID · IFC GlobalId · ArxAddress |
| [ifc-limitations.md](./ifc-limitations.md) | IFC-only policy, L0–L2 fidelity, unmapped products, vendors |
| [lidar-confidence.md](./lidar-confidence.md) | Non-probabilistic confidence honesty |
| [resource-limits.md](./resource-limits.md) | R6 pilot import ceilings (IFC/LiDAR) |

## Hard policies

- **IFC only for BIM interchange.** No Revit/ArchiCAD plugins.  
  Vendor BIM → clean IFC export → `arx import ifc`.
- **Single building / single `building.yaml`** per repo (manifest I11).
- **Export spine:** `arx export --format ifc` only (review-gated).  
  Agent/daemon is edge bridging — not a second export authority.
- **No unreviewed `proposed` LiDAR as official** (R1/R10).
- **Horizon C (network scale) is frozen** until L1 exit once.
- **Default features:** `tui` (primary UI) + compiler spine. No hardware drivers
  or LiDAR point-cloud 3D (removed for now). See [pilot-release.md](./pilot-release.md).
- **WASM PWA (`web`):** terminal-style interaction; camera/AR LiDAR capture later —
  not a full CAD viewer.
- **Single public error type:** `arxos::error::ArxError`.

## Lab / economy (not L1 success)

See [lab/](./lab/) for mint/pay/Anvil loops. L1 exit does **not** require chain.

## Do not use

[`_archive/`](./_archive/) holds pre-convergence material. Do not treat as current design.
