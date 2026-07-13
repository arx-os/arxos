# buildingSMART Sample-Test-Files — IFC interop assessment

**Date:** 2026-07-13  
**Arx binary:** local `target/debug/arx` (main)  
**Sample source:** [buildingSMART/Sample-Test-Files](https://github.com/buildingSMART/Sample-Test-Files.git) (cloned to sibling repo)  
**Method:** `arx init --no-git` → `arx import ifc` → `validate` → `export --format ifc` → re-import → second import (merge) → `export --approved-only`  

**Fidelity contract (manifest §3.5):** L0 hierarchy/IDs · L1 Arx Psets · L2 box/placement subset. **Not** full BIM parity.

Raw machine results: `tests/ifc_buildingsmart_results.json`.

---

## 1. Inventory (23 `.ifc` files)

| Schema | Set | Files | Size range | Notes |
| :--- | :--- | ---: | :--- | :--- |
| **IFC4** | ISO Spec ReferenceView V1.2 | 5 | 2.5–12 KB | Tessellation / single product micro-models |
| **IFC4** | PCERT-Sample-Scene | 9 | 180 KB – 3 MB | Single-family house domains + infra |
| **IFC4X3_ADD2** | PCERT-Sample-Scene | 9 | ~same | IFC 4.3.2.0 twins of PCERT set |

### IFC4 PCERT domains (representative)

| File | ~Size | Domain | In-file structure (STEP counts) |
| :--- | ---: | :--- | :--- |
| Building-Architecture.ifc | 226 KB | Arch | 1 storey, 2 spaces, 4 walls, 3 slabs, 5 proxies, 1 roof |
| Building-Hvac.ifc | 180 KB | MEP | 1 storey, flow terminals (air) |
| Building-Structural.ifc | 297 KB | Structure | 1 storey, structural members (not Arx rooms) |
| Building-Landscaping.ifc | 1.4 MB | Landscape | Heavy geometry, weak spatial building |
| Infra-Bridge / Road / Rail / Plumbing / Landscaping | 0.2–3 MB | Infra | Bridge/road products; not school buildings |

### ISO ReferenceView micro-files

| File | Focus |
| :--- | :--- |
| basin-tessellation.ifc | Tessellated basin (no storey) |
| wall-with-opening-and-window.ifc | Wall + opening + window + storey |
| column-straight-rectangle-tessellation.ifc | Column tessellation |
| tessellated-item.ifc / tessellation-with-individual-colors.ifc | Mesh / color samples |

---

## 2. Summary table (10-file battery)

| # | Sample | Schema | Import | Validate | Export | Re-import | Merge×2 | Approved-only | Floors | Rooms* | Equip* | GIDs kept† | Pset_Arx on export |
| :---: | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| 1 | ISO basin-tessellation | IFC4 | OK | warn empty floors | OK | OK | OK | OK | 0 | 0 | 0 | 1 | Yes |
| 2 | ISO wall+opening+window | IFC4 | OK | OK | OK | OK | OK | OK | 1 | 0 | 0 | 2 | Yes |
| 3 | ISO column tessellation | IFC4 | OK | warn empty floors | OK | OK | OK | OK | 0 | 0 | 0 | 0→1‡ | Yes |
| 4 | ISO tessellated-item | IFC4 | OK | warn empty floors | OK | OK | OK | OK | 0 | 0 | 0 | 1 | Yes |
| 5 | IFC4 Building-Architecture | IFC4 | OK | OK | OK | OK | OK | OK | 1 | 2 | 1 | 5 | Yes |
| 6 | IFC4 Building-Hvac | IFC4 | OK | OK | OK | OK | OK | OK | 1 | 0 | 2 | 4 | Yes |
| 7 | IFC4 Building-Structural | IFC4 | OK | OK | OK | OK | OK | OK | 1 | 0 | 0 | 2 | Yes |
| 8 | IFC4.3 Building-Architecture | IFC4X3 | OK | OK | OK | OK | OK | OK | 1 | 2 | 1 | 5 | Yes |
| 9 | IFC4.3 Building-Hvac | IFC4X3 | OK | OK | OK | OK | OK | OK | 1 | 0 | 2 | 4 | Yes |
| 10 | IFC4 Infra-Bridge | IFC4 | OK | OK | OK | OK | OK | OK | 5 | 0 | 0 | 6 | Yes |

\* Arx domain counts (spaces → rooms; selected products → equipment). **Not** IFC wall/slab counts.  
† `ifc_global_id` values on Building/Floor/Room/Equipment in YAML after import.  
‡ Column-only model: no product GIDs on domain entities until export assigns missing.

### Headline metrics

| Metric | Result |
| :--- | :--- |
| **Crash / panic** | **None** on 10/10 |
| **Import success** | 10/10 |
| **Export success** | 10/10 |
| **GlobalId set equality import → re-import** | **Yes** (Architecture, HVAC, Structural, wall, bridge, IFC4.3 arch) |
| **Pset_ArxIdentity on export** | **Yes** on all exports checked |
| **Semantic completeness vs STEP** | **Poor–partial** (walls/slabs/openings largely **not** first-class) |
| **IFC4 vs IFC4.3 PCERT** | Same domain outcomes (good non-regression) |

---

## 3. Findings by area

### 3.1 Identity (GlobalId ↔ Arx UUID)

**Strengths**

- Imported products that **do** enter the domain keep `ifc_global_id`.
- Round-trip re-import preserves the **same GID set** for architecture/HVAC/structural/wall/bridge cases.
- Export emits `Pset_ArxIdentity` / ArxId consistently (Arx-authored path ready).
- `assign_missing_global_ids` fills holes on export so double-export stays stable.

**Gaps**

- ISO product-only files often yield **empty floors** with only building-level or zero GIDs — identity surface is tiny because hierarchy mapping is empty.
- Walls/slabs/doors/windows with GlobalIds in STEP **never get domain rows**, so their GIDs are **not** round-tripped as durable Arx entities (only spatial structure + mapped products).
- No automated assertion that **building/floor GIDs** match STEP `IFCBUILDING` / `IFCBUILDINGSTOREY` GlobalIds (manual check: storey `1Ano2ZUxnEIvVQ_beukl8b` preserved on architecture).

**Verdict:** L0 identity for **mapped** entities is solid. L0 for **unmapped** products is N/A (dropped, often without LossReport detail).

### 3.2 Hierarchy (Project → Site → Building → Storey → Space)

**Strengths**

- PCERT house models resolve **storey + building** names (`00 groundfloor`, `Single-family house`).
- Spaces map to rooms when present (architecture: kitchen + second space → 2 rooms in import summary).
- IFC4 and IFC4.3 architecture behave the same (no schema crash).
- Infra bridge resolves **multiple storey-like levels** (approach/deck/superstructure).

**Gaps**

- ISO micro-models without full spatial structure correctly warn (`no_storeys`, `no_building`) but still “validate” with empty floors — pilot UX may look “green” when model is empty.
- **Walls, slabs, roof, openings, windows** are not represented as rooms/equipment (by design of current mapper, but **LossReport is silent** — import tail often `Warnings: none` while 4 walls disappear).
- Structural domain (beams/columns) → **zero equipment**, only empty storey — same silent drop.
- HVAC: only 2 air terminals as equipment; no systems graph (acceptable non-goal, but completeness is low).

### 3.3 Geometry (L2)

**Strengths**

- Parser does not crash on tessellation ReferenceView files.
- Export produces loadable STEP.

**Gaps**

- Tessellation-centric ISO samples do not produce meaningful room footprints in Arx.
- Openings/windows in `wall-with-opening-and-window.ifc` not modeled as openings (L3+ / out of scope, but wall itself also not imported).
- No quantitative mesh epsilon comparison in this battery (not instrumented).

### 3.4 Properties

**Strengths**

- Free-form / Arx Psets round-trip on Arx export path.
- Equipment typed as `Other` with IFC class string for HVAC terminals (`IFCAIRTERMINAL`).

**Gaps**

- Vendor property sets from STEP not audited for drop rate in this pass.
- Classification / materials / quantities dropped (expected L3+).

### 3.5 Validation, review, merge, YAML

| Concern | Observation |
| :--- | :--- |
| Hard validation | Empty-floor models = **warnings**, not errors — import still writes YAML |
| `review_status` | N/A for pure IFC (no LiDAR); `--approved-only` export still succeeds |
| Merge IFC×2 | No crash; structure stable (did not measure entity-count churn in detail) |
| Deterministic YAML | Not diff-tested file-to-file; re-import GID sets stable |

---

## 4. Gap analysis (honest)

### What “PASS” means here

**Operational PASS** = no panic, import writes SSOT, validate non-fatal, export+reimport works, GIDs of **kept** entities stable.

**Semantic PASS for district architecture** = **not claimed**.  
buildingSMART Architecture has 4 walls + 3 slabs + 2 spaces; Arx keeps spatial structure + spaces/select products, **not** the wall shell.

### Root causes (mapping, not lexer crashes)

| Gap | Likely location | Severity for school pilots |
| :--- | :--- | :---: |
| Walls/slabs/doors/windows not domain entities | `hierarchy/builder.rs` product filter | **High** for “as-built floor plan” |
| Silent loss (no LossReport for dropped products) | `resolver` / hierarchy extract | **High** (false confidence) |
| Empty models validate with warning only | `validation/building.rs` | Med |
| Tessellation-only models → empty hierarchy | hierarchy expects Building/Storey | Low (samples) |
| Structural members ignored | equipment type map | Med for structure pilots |
| Infra models semi-mapped | storeys as floors | Low for school L1 |

### Not a crash problem

Lexer/registry/resolver survived IFC4 + IFC4X3_ADD2 PCERT and ISO RV files. **Robustness against panic is good; fidelity of domain extraction is the pilot risk.**

---

## 5. Concrete proposals (approval required — not applied)

### P0 — Honesty / pilot safety

1. **LossReport: count dropped products by IFC class**  
   When `IFCWALL*` / `IFCSLAB` / `IFCDOOR` / `IFCWINDOW` exist in registry but are not mapped, emit  
   `warn("unmapped_product", "IFCWALL ×4 not imported into Arx domain")`.  
   *Files:* `src/ifc/parser/resolver.rs`, `src/ifc/hierarchy/builder.rs`, `src/ifc/mapping/report.rs`.

2. **Optional validation error (strict) for empty floors**  
   `arx import ifc --strict` already fails on zero spatial entities; extend or document that empty floors after resolve = hard fail under strict.  
   *Files:* `src/ifc/mod.rs`, `src/cli` import strict path.

3. **CI: non-panic + structure golden on 2–3 licensed samples**  
   Copy **small** ISO RV files (license: buildingSMART samples) into `tests/fixtures/ifc/buildingsmart/` with README attribution, extend `vendor_ifc_test.rs`.  
   Do **not** check in multi-MB PCERT files without size/license review.

### P1 — Fidelity (still L0, not full BIM)

4. **Map `IfcWall` / `IfcWallStandardCase` as equipment or typed “structure” equipment under storey**  
   Minimal: floor-level equipment with `equipment_type: Other("IFCWALL")` + GlobalId + name.  
   Preserves identity for shell without full topology.

5. **Map `IfcDoor` / `IfcWindow` similarly** (optional under P1).

6. **Space containment:** ensure both architecture spaces land as rooms with names (verify kitchen + second space names in golden assert).

### P2 — Tooling / docs

7. **Script** `scripts/ifc_sample_battery.sh` wrapping this battery (env `ARX_MAX_IFC_BYTES`, summary table).

8. **Update `docs/ifc-limitations.md`** with buildingSMART table (draft below).

9. **Do not** promise Revit parity from these samples — PCERT is a small house, not a district school.

### Explicit non-goals (remain)

- Opening voids / window geometry L3  
- Full tessellation mesh round-trip  
- Infra alignment / linear placement  
- Materials / classifications  

---

## 6. Draft `docs/ifc-limitations.md` additions (proposal)

```markdown
## buildingSMART Sample-Test-Files (2026-07 assessment)

Source: https://github.com/buildingSMART/Sample-Test-Files  
Report: `tests/ifc_buildingsmart_report.md`

| Sample class | Import crash? | Domain extract | GID round-trip (kept entities) |
| :--- | :---: | :--- | :---: |
| ISO RV micro (tessellation) | No | Often empty floors + warnings | Weak (few entities) |
| ISO wall+opening+window | No | Storey only; wall/window not domain | Yes for kept IDs |
| PCERT Building-Architecture IFC4/4.3 | No | Storey + spaces (+ sparse products) | Yes |
| PCERT Building-Hvac IFC4/4.3 | No | Storey + few terminals | Yes |
| PCERT Building-Structural | No | Storey shell only | Yes |
| PCERT Infra-Bridge | No | Multiple levels; no rooms | Yes |

**Takeaway:** Non-panic and ID stability on mapped entities are strong.
**District readiness still requires** real Revit exports (R2) and honest loss reporting for unmapped walls/MEP.
```

---

## 7. Suggested verification commands

```bash
# Clone samples (once)
git clone --depth 1 https://github.com/buildingSMART/Sample-Test-Files.git \
  ../Sample-Test-Files

cd /path/to/arxos
cargo build

# Single-file smoke
WORKDIR=$(mktemp -d) && cd "$WORKDIR"
arx init --name BS --no-git
export ARX_MAX_IFC_BYTES=$((100*1024*1024))
arx import ifc "$OLDPWD/../Sample-Test-Files/IFC 4.0.2.1 (IFC 4)/PCERT-Sample-Scene/Building-Architecture.ifc"
arx validate
arx export --format ifc --output out.ifc
arx export --format ifc --approved-only --output approved.ifc
# reimport
mkdir re && cd re && arx init --name R --no-git
arx import ifc ../out.ifc && arx validate

# Existing CI goldens
cargo test --test vendor_ifc_test --test bidirectional_tests --test ifc_native_tests
```

---

## 8. Prioritized backlog (before physical pilots)

| Pri | Item | Rationale |
| :---: | :--- | :--- |
| **P0** | LossReport unmapped product counts | Stop silent wall/slab disappearance |
| **P0** | Document buildingSMART results (this report) | Evidence for R2 process |
| **P0** | Optional: CI non-panic on 1–2 small ISO files with attribution | Cheap regression |
| **P1** | Map walls (and doors/windows) as typed equipment under storey | Identity shell for schools |
| **P1** | Golden assert on Architecture: ≥1 storey, ≥2 rooms, GID set non-empty | Prevent regression |
| **P2** | Battery script + CI optional job | Ongoing vendor sample health |
| **P2** | Real district Revit IFC matrix (still **R2**) | buildingSMART ≠ district |

---

## 9. Bottom line

| Claim | Honest status |
| :--- | :--- |
| “Parser doesn’t explode on buildingSMART IFC4/4.3 samples” | **Supported** by this battery |
| “We preserve GlobalIds for everything in the file” | **False** — only mapped domain entities |
| “Architecture import is a usable as-built shell” | **Weak** — spaces yes; walls/slabs largely dropped **silently** |
| “Ready for district Revit without field matrix” | **No** — still need R2 real exports |
| “Round-trip of what we keep is stable” | **Yes** — strong for pilot confidence on mapped subset |

**No production code changes were applied in this pass** (assessment + report only). Approve P0 LossReport / golden tests to implement next.
