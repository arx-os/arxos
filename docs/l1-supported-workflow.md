# L1 supported workflow (free software only)

**Obligation:** R9 (supported surface), R8 (no chain required)  
**Audience:** District pilot capture tech  
**Install:** Pinned release only — see `docs/pilot-release.md`

This is the **only** workflow supported for L1 pilot success.  
Do **not** require `blockchain`, mint, or access pay for L1 exit.

---

## Supported loop

```text
install (pinned) → init → import → edit/review → validate → git → export (internal)
```

Optional later (not L1 success criteria): `contribute`, `access`, `--commercial`, Anvil.

---

## 1. Install (pinned)

```bash
# Preferred: from tagged release (example)
git clone <internal-or-approved-remote> arxos
cd arxos
git checkout v2.0.0-pilot.3   # use the pin in the pilot charter

# Build CLI (default features OK; blockchain not required)
cargo install --path . --locked
arx --version
```

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
# Creates building.yaml + Git repo on branch main (opt out: --no-git)
# Record building id from output or building.yaml → pilot charter
```

## 3. Import

```bash
# IFC
arx import ifc path/to/model.ifc

# LiDAR (if in scope)
arx import lidar path/to/scan.ply
# or with merge into existing model:
# arx import lidar path/to/scan.ply --merge
```

If import fails: stop, capture error + file type/version, do not “force” bad YAML.

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

**Policy:** Do not hand contractors an “official” IFC that still has unreviewed `proposed` LiDAR entities. Prefer:

```bash
arx export --format ifc --approved-only --output site-approved.ifc
```

## 5. Validate

```bash
arx validate
# fix errors before treating model as pilot SSOT
```

## 6. Git

```bash
arx status
arx stage
arx commit -m "pilot: import and review SITE"
# equivalent: arx commit "pilot: import and review SITE"
# push only to approved internal remote
```

## 7. Internal export

```bash
arx export --format ifc --output exports/internal.ifc
# free software path — no access receipt required
```

Commercial / paid delivery (`--commercial`) is **out of L1 success path** unless leadership adds it under a separate demo.

---

## Explicitly unsupported for L1 success

| Action | Why |
| :--- | :--- |
| `arx contribute --submit` / mainnet mint | R3/R8 — not required for L1 |
| Public GitHub for facility models | R7 |
| Trusting `proposed` LiDAR without review | R1/R10 |
| Floating `main` without pin | R9 |
| Multi-building campus layout | I11 / product limit |
| `export --delta` | Not implemented |

---

## Automated smoke (does not replace R5)

From repo root, after `cargo build`:

```bash
./scripts/l1_smoke.sh
# optional path: ./scripts/l1_smoke.sh /path/to/file.ifc
```

This checks init → import sample IFC → validate → export → contribute → commercial gate.  
It does **not** close second-person district transfer (R5).

## Escalation

1. Reproduce with pinned version.  
2. Note OS, `arx --version`, command, error text.  
3. File issue or pilot log entry.  
4. Do not invent parallel tools mid-pilot.

**Related:** `docs/pilot-charter.md` · `docs/second-person-checklist.md` · `docs/install.md` · `docs/field-truth-log.md` · `docs/data-classification.md`
