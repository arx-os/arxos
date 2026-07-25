# L1 supported workflow (free software only)

**Obligation:** R9 (supported surface), R8 (no chain required)  
**Audience:** District pilot capture tech  
**Install:** Pinned release only — see [pilot-release.md](./pilot-release.md)

This is the **only** workflow supported for L1 pilot success.  
Do **not** require `blockchain`, mint, access pay, or agent for L1 exit.

**Map:** [INDEX.md](./INDEX.md) · **Authority:** [`arxos_manifest.md`](../arxos_manifest.md) §1.1a · §1.6  
**Living plan:** [horizon-b-roadmap.md](./horizon-b-roadmap.md) · **Packet:** [field-handoff.md](./field-handoff.md)

---

## Supported loop

```text
install (pinned) → init → import → edit/review → validate → git → export (internal)
```

Read **import warnings** (LossReport). `unmapped_products` means walls/slabs/doors/…
were present but not mapped into Arx rooms/equipment — not a silent success.

Optional later (not L1 success criteria): `contribute`, `access`, `--commercial`, Anvil — see [lab/](./lab/).  
Optional agent (`--features agent`) is a capture-node bridge — **not** required for L1 exit.  
**Not product:** browser LiDAR, Safari RoomPlan/ARKit, walk-in pure PWA capture  
([adr-web-demotion.md](./adr-web-demotion.md)). Honest spatial path today = **file** IFC/LiDAR + CLI/TUI.

---

## BIM path (only)

```text
Vendor BIM (Revit / ArchiCAD / …)
  → clean IFC export from that tool
  → arx import ifc
```

**No plugins. No direct RVT/PLN open.**  
If IFC is incomplete, fix vendor export settings. See [ifc-limitations.md](./ifc-limitations.md).

---

## 1. Install (pinned)

```bash
git clone <internal-or-approved-remote> arxos
cd arxos
git checkout v2.0.0-pilot.5   # or exact pin recorded in the pilot charter
git rev-parse HEAD            # expect latest pilot.5 commit SHA

# Default = compiler + TUI (primary UI). blockchain/agent not required for L1
cargo install --path . --locked
arx --version
```

Import size/point ceilings: [resource-limits.md](./resource-limits.md) (raise only with hardware headroom).

If `--locked` fails, still pin the commit hash in the charter and record it.

Smoke:

```bash
mkdir /tmp/arx-l1-smoke && cd /tmp/arx-l1-smoke
arx init --name "Smoke"
arx validate
# expect success
```

## 2. Project init

```bash
mkdir -p ~/arx-pilots/SITE_NAME && cd ~/arx-pilots/SITE_NAME
arx init --name "SITE_NAME"
# Optional ADR postal root (recommended when site address is known):
# arx init --name "SITE_NAME" \
#   --postal "143677 N. Dale Mabry Hwy, Suite 2, Tampa, FL, 33622"
# Creates building.yaml + Git repo on branch main (opt out: --no-git)
# Record building id / address from output or building.yaml → pilot charter
```

**Limit:** one building / one `building.yaml` per repo root.  
**Identity:** hierarchical `address` is the operational identity — see [identity.md](./identity.md).

## 3. Import

```bash
# IFC (primary district path)
arx import ifc path/to/model.ifc
# Optional: re-root all addresses under a postal building root:
# arx import ifc path/to/model.ifc --postal "…"

# LiDAR (if in charter scope)
arx import lidar path/to/scan.ply
# merge into existing model:
# arx import lidar path/to/scan.ply --merge
```

If import fails: stop, capture error + file type/version, do not “force” bad YAML.

**After import (optional navigation):**

```bash
ROOT=$(grep -E '^  address:' building.yaml | head -1 | awk '{print $2}')
arx show "$ROOT"
arx ls "${ROOT}/fl.1"
arx tree "$ROOT" --depth 2
# Label electrical (Arxos-native; GlobalId assigned on export):
# arx add "$ROOT" panel --name L1
# arx add "${ROOT}/elec/panel.l1" ckt --name 14
# arx add "${ROOT}/elec/panel.l1/ckt.14" outlet
```

## 4. Review (mandatory for LiDAR autos)

Auto-detected structure is `review_status=proposed` until changed.

Example edit script:

```text
# reviews.txt
set room SomeAutoRoom review_status=accepted
set room BadBlob review_status=rejected
```

```bash
arx edit reviews.txt
```

**Policy:** Do not hand contractors an “official” IFC that still has unreviewed
`proposed` LiDAR entities. Prefer:

```bash
arx export --format ifc --approved-only --output site-approved.ifc
```

## 5. Validate

```bash
# Lenient address validations by default (address mismatches trigger warnings only):
arx validate

# Pass --strict-addresses to escalate system prefix mismatches into hard errors for final QA checks:
arx validate --strict-addresses
```

## 6. Git

```bash
arx status
arx stage
arx commit -m "pilot: import and review SITE"
# push only to approved internal remote
```

## 7. Internal export (compiler spine)

```bash
arx export --format ifc --output exports/internal.ifc
# free software path — no access receipt required
# Identity: preserves IFC GlobalIds; assigns + writes back GlobalIds for arx-add entities
```

**Export authority:** This CLI command (and `export::ifc`) is the only official
IFC export path. Do **not** treat agent auto-export as pilot handoff.

Commercial / paid delivery (`--commercial`) is **out of L1 success path** unless
leadership adds it under a separate demo.

Identity after export/import: [identity.md](./identity.md).

---

## Explicitly unsupported for L1 success

| Action | Why |
| :--- | :--- |
| Revit/ArchiCAD plugins or direct CAD integration | IFC-only policy |
| `arx contribute --submit` / mainnet mint | R3/R8 — not required for L1 |
| Public GitHub for facility models | R7 |
| Trusting `proposed` LiDAR without review | R1/R10 |
| Floating `main` without pin | R9 |
| Multi-building campus layout | I11 / product limit |
| `export --delta` | Not implemented (hard-error) |
| Agent auto-export as official IFC | Edge convenience only |
| TUI / 3D / dashboard without explicit features | Compiler-core default has no rings |

`arx contribute` / `arx access` remain available in compiler-core for lab smoke and
optional demos; they are **not** L1 exit criteria.

---

## Automated smoke (does not replace R5)

From repo root, after `cargo build`:

```bash
./scripts/l1_smoke.sh
# optional path: ./scripts/l1_smoke.sh /path/to/file.ifc
```

This checks init → import sample IFC → validate → export (and lab extras if present).  
It does **not** close second-person district transfer (R5).

## Escalation

1. Reproduce with pinned version.  
2. Note OS, `arx --version`, command, error text.  
3. File issue or pilot log entry.  
4. Do not invent parallel tools mid-pilot.

**Related:** [pilot-charter.md](./pilot-charter.md) · [second-person-checklist.md](./second-person-checklist.md) · [field-truth-log.md](./field-truth-log.md) · [data-classification.md](./data-classification.md)
