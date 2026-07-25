# ArxOS documentation (pilot-focused)

**Engineering source of truth:** [`../arxos_manifest.md`](../arxos_manifest.md)  
(maturity, obligations R1–R10, integrity ledger, refuse list, horizons)

This folder is **operator documentation** for L1 field pilot.  
If a doc here conflicts with the manifest, **the manifest wins**.

## Maturity (honest)

| Claim | Score |
| :--- | :---: |
| Lab closed loop (compiler + Foundry) | ~8.5/10 |
| District L1 pilot readiness | ~5/10 |
| Full reward/market (L3) | ~2/10 |

L1 is blocked on **process + field evidence**, not missing framework code.  
See manifest §1.5–1.6.

**Preferred pin:** `v2.0.0-pilot.5` @ `ad5213dca08cef52cc90d9b80037f0dbaaa14a8d` — [pilot-release.md](./pilot-release.md).  
**Install:** `git checkout v2.0.0-pilot.5 && cargo install --path . --locked` (default = compiler + TUI).

### Product surfaces (Decision 9)

| Surface | Role |
| :--- | :--- |
| **CLI + TUI** | Primary operator UI |
| **Agent** | Capture node / bridge → `building.yaml` |
| **File IFC + LiDAR** | Current honest spatial/BIM ingest |
| **Web** | **Static landing only** (`index.html`) — not capture/review |
| **Native iOS** | **Lab shell** in `arx-os/ios` — connect + file scan + label/commit (no RoomPlan UI yet) |

**Non-claims:** no browser LiDAR · no ARKit/RoomPlan in Safari · no walk-in PWA as product · no live camera in companion yet.  
**ADRs:** [adr-web-demotion.md](./adr-web-demotion.md) (Decision 9) · [adr-capture-model.md](./adr-capture-model.md) (Decision 10 — proposed-first capture)

### Lab IFC honesty (Package A, 2026-07)

| Item | Status |
| :--- | :---: |
| Non-panic import on buildingSMART ISO + PCERT samples | Yes |
| `unmapped_products` LossReport (MEP & structural) | Yes (pilot.5 dynamic scan) |
| District Revit/ArchiCAD anonymized evidence | **Open** (R2 field) |

Details: [ifc-limitations.md](./ifc-limitations.md) · report: [`tests/ifc_buildingsmart_report.md`](../tests/ifc_buildingsmart_report.md)

## Living plan (Horizon B)

| Doc | Role |
| :--- | :--- |
| [horizon-b-roadmap.md](./horizon-b-roadmap.md) | **Living** phases HB0–HB7 → site capture + L1 exit |
| [adr.md](./adr.md) | Architecture Decision Record index — Decisions 1–13 |
| [adr-0001-identity-and-addressing.md](./adr-0001-identity-and-addressing.md) | **ADR 0001 / Decision 13:** identity & addressing final |
| [adr-web-demotion.md](./adr-web-demotion.md) | **Decision 9:** PWA abandoned; web = landing only |
| [adr-capture-model.md](./adr-capture-model.md) | **Decision 10:** near-term capture — proposed-first, geometry as input |
| [adr-native-capture-interface.md](./adr-native-capture-interface.md) | **Decision 11:** native ↔ agent thin hand-off (v1 = file LiDAR) |
| [adr-repo-structure.md](./adr-repo-structure.md) | **Decision 12:** core vs **`ios`** separate repos |
| [agent-client-interface.md](./agent-client-interface.md) | **Versioned** agent JSON-RPC contract for peripheral clients |
| [field-language.md](./field-language.md) | Shared CLI/agent/iOS vocabulary; `field.*` vs text DSL |
| [native-file-handoff.md](./native-file-handoff.md) | Operator: scan file → CLI or agent `lidar.import` + provenance |
| [ios-lab-loop.md](./ios-lab-loop.md) | Lab E2E status: companion ↔ agent ↔ commit ↔ IFC |
| [pilot-starter-pack.md](./pilot-starter-pack.md) | **Zip-ready** checklist of all site-team docs |
| [field-day-1-runbook.md](./field-day-1-runbook.md) | **S3+S5** non-author Day 1: pin install → real IFC → LossReport evidence |
| [sprint-status-dashboard.md](./sprint-status-dashboard.md) | Weekly S1–S8 + R\* status table |
| [s8-reconciliation-template.md](./s8-reconciliation-template.md) | Post-sprint R\* / scorecard reconcile |
| [hb3-lidar-plan.md](./hb3-lidar-plan.md) | After S1–S8: first real **file** LiDAR + review (outline) |
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
| **[adr-0001-identity-and-addressing.md](./adr-0001-identity-and-addressing.md)** | **Binding** identity decisions (ADR 0001) |
| [identity-and-addressing.md](./identity-and-addressing.md) | Address trees + CLI language (design + impl status) |
| [identity.md](./identity.md) | **Implementation map** — roots, elec tree, show/ls/tree/add, GlobalId export rules |
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
- **Web:** static landing only — **not** a capture, review, or Create New client  
  ([adr-web-demotion.md](./adr-web-demotion.md)).
- **Phone LiDAR:** future **native iOS** companion — not Safari/PWA.
- **Single public error type:** `arxos::error::ArxError`.

## Lab / economy (not L1 success)

See [lab/](./lab/) for mint/pay/Anvil loops. L1 exit does **not** require chain.

## Do not use (archived / historical)

[`_archive/`](./_archive/) holds pre-convergence material **and** retired interactive-PWA guides
(create-new-camera, bedroom-loop, iphone-pwa-*, batch-b-proposal).  
**Do not** treat archive as current design or supported workflow.
