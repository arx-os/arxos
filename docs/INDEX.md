# ArxOS documentation

Map of **authority**, **audience**, and **where files live**.  
Do not treat every markdown file under `docs/` as equally current.

---

## Authority (conflict resolution)

| Priority | Source | Wins on |
| :---: | :--- | :--- |
| **1** | [`adr/`](./adr/) (accepted ADRs) | Architecture and product-surface **decisions** for their stated scope |
| **2** | [`../arxos_manifest.md`](../arxos_manifest.md) | Maturity, obligations R1–R10, plan/horizons, refuse list, integrity ledger |
| **3** | [`reference/`](./reference/) | Design detail + **implementation maps** (must track ADRs; do not invent features) |
| **4** | [`pilot/`](./pilot/) | L1 operator packet (how to run a district pilot on a **pin**) |
| **5** | [`process/`](./process/) | Living sprint/roadmap tooling (status, not product claims) |
| **6** | [`lab/`](./lab/) | Economy / chain lab loops (**not** L1 success criteria) |
| **—** | [`_archive/`](./_archive/) | Historical only — **do not use** as current design |

**ADR 0001** (identity & addressing) is binding for operational identity, GlobalId provenance, and address-native CLI.  
**Manifest** remains the engineering plan SSOT for maturity scores and L1 obligations.  
If a pilot doc and a pin’s behavior disagree, **trust the pin + code**, then file a doc bug.

---

## Maturity (honest)

| Claim | Score |
| :--- | :---: |
| Lab closed loop (compiler + Foundry) | ~8.5/10 |
| District L1 pilot readiness | ~5/10 |
| Full reward/market (L3) | ~2/10 |

L1 is blocked on **process + field evidence**, not missing framework code.  
See manifest §1.5–1.6.

**Preferred field pin:** `v2.0.0-pilot.5` @ `ad5213dca08cef52cc90d9b80037f0dbaaa14a8d` — [pilot/release.md](./pilot/release.md).  
**ADR 0001 identity work** landed on `main` after that pin; field pilots still prefer the pin until a new pilot tag is cut.

```bash
git checkout v2.0.0-pilot.5 && cargo install --path . --locked
```

---

## Directory layout

| Folder | Audience | Contents |
| :--- | :--- | :--- |
| **[adr/](./adr/)** | Maintainers | Accepted architecture decisions |
| **[reference/](./reference/)** | Engineers | Identity, IFC limits, agent contract, capture hand-off |
| **[pilot/](./pilot/)** | Field / IT | Ordered L1 packet (charter → evidence) |
| **[process/](./process/)** | Pilot owner + eng | Horizon B roadmap, sprint status, optional eng queue |
| **[lab/](./lab/)** | Lab eng | Contribute / access / Anvil (not L1 exit) |
| **[_archive/](./_archive/)** | Historians | Pre-convergence + retired PWA guides |

---

## Start here by role

| Role | Start |
| :--- | :--- |
| **New engineer** | Root [`README.md`](../README.md) → [reference/identity.md](./reference/identity.md) → [adr/0001-identity-and-addressing.md](./adr/0001-identity-and-addressing.md) |
| **District pilot** | [pilot/](./pilot/) in order (see [pilot/README.md](./pilot/README.md)) |
| **iOS / agent client** | [reference/agent-client-interface.md](./reference/agent-client-interface.md) · [adr/repo-structure.md](./adr/repo-structure.md) |
| **Roadmap / sprint** | [process/horizon-b-roadmap.md](./process/horizon-b-roadmap.md) |
| **Chain lab** | [lab/README.md](./lab/README.md) |

---

## Product surfaces (locked)

| Surface | Role |
| :--- | :--- |
| **CLI + TUI** | Primary operator UI (`show` / `ls` / `tree` / `add` address-native) |
| **Agent** | Capture node / bridge → `building.yaml` |
| **File IFC + LiDAR** | Current honest spatial/BIM ingest |
| **Web** | Static landing only (`index.html`) — not capture/review |
| **Native iOS** | Lab shell in `arx-os/ios` — file LiDAR path; no RoomPlan UI yet |

**Non-claims:** no browser LiDAR · no ARKit/RoomPlan in Safari · no walk-in PWA as product · no live camera in companion yet.

ADRs: [web-demotion](./adr/web-demotion.md) · [capture-model](./adr/capture-model.md) · [native-capture-interface](./adr/native-capture-interface.md) · [repo-structure](./adr/repo-structure.md) · [identity ADR 0001](./adr/0001-identity-and-addressing.md)

---

## Hard policies (summary)

- **IFC only** for BIM interchange — no Revit/ArchiCAD plugins.
- **Single** `building.yaml` per repo (manifest I11).
- **Export spine:** `arx export --format ifc` only (review-gated).
- **No unreviewed `proposed` LiDAR** as official (R1/R10).
- **Horizon C frozen** until L1 exit once.
- **Identity:** hierarchical `address` primary ops · `ifc_global_id` provenance · UUID internal ([ADR 0001](./adr/0001-identity-and-addressing.md)).
- **Single public error type:** `arxos::error::ArxError`.

---

## Lab IFC honesty

| Item | Status |
| :--- | :---: |
| Non-panic import on buildingSMART ISO + PCERT samples | Yes |
| `unmapped_products` LossReport (MEP & structural) | Yes (dynamic scan; pilot.5+) |
| District Revit/ArchiCAD anonymized evidence | **Open** (R2 field) |

Details: [reference/ifc-limitations.md](./reference/ifc-limitations.md) · [`tests/ifc_buildingsmart_report.md`](../tests/ifc_buildingsmart_report.md)
