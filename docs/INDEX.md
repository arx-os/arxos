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

## L1 pilot packet (do in order)

1. [pilot-charter.md](./pilot-charter.md) — sign (R10, R8)
2. [pilot-release.md](./pilot-release.md) — pin install (R9)
3. [data-classification.md](./data-classification.md) — private remote (R7)
4. [l1-supported-workflow.md](./l1-supported-workflow.md) — only supported loop
5. [second-person-checklist.md](./second-person-checklist.md) — cold start (R5)
6. [field-truth-log.md](./field-truth-log.md) — real IFC/LiDAR evidence (R1/R2/R6)
7. [field-handoff.md](./field-handoff.md) — ordered packet checklist

## Compiler reference

| Doc | Topic |
| :--- | :--- |
| [identity.md](./identity.md) | Arx UUID · IFC GlobalId · ArxAddress |
| [ifc-limitations.md](./ifc-limitations.md) | IFC-only policy, L0–L2 fidelity, vendors |
| [lidar-confidence.md](./lidar-confidence.md) | Non-probabilistic confidence honesty |

## Hard policies

- **IFC only for BIM interchange.** No Revit/ArchiCAD plugins.  
  Vendor BIM → clean IFC export → `arx import ifc`.
- **Single building / single `building.yaml`** per repo (manifest I11).
- **Export spine:** `arx export --format ifc` only (review-gated).  
  Agent/daemon is edge bridging — not a second export authority.
- **No unreviewed `proposed` LiDAR as official** (R1/R10).
- **Horizon C (network scale) is frozen** until L1 exit once.

## Lab / economy (not L1 success)

See [lab/](./lab/) for mint/pay/Anvil loops. L1 exit does **not** require chain.

## Do not use

[`_archive/`](./_archive/) holds pre-convergence material. Do not treat as current design.
