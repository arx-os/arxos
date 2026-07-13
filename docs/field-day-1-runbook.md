# Field Day 1 Runbook (S3 + S5)

**Audience:** Non-author capture tech (or second person after S4)  
**Pin:** `v2.0.0-pilot.4` @ `659bbd9f369c0b942f150983b204ea054fc595a0`  
**Maps to:** Sprint **S3** (install + smoke) then **S5** (real IFC + LossReport log)  
**Living plan:** [horizon-b-roadmap.md](./horizon-b-roadmap.md) · Packet: [field-handoff.md](./field-handoff.md)

**Before you start**
- [ ] S2 data class done (or IFC is approved non-sensitive lab file only)
- [ ] Charter draft has pin line (S1 can finish after if not “official” yet)
- [ ] You have the IFC file path (USB / secure share — not public GitHub)
- [ ] Laptop/Mini with Rust toolchain (or prebuilt `arx` from pin — prefer install from pin)

**Rules:** No CAD plugins · Agent is **bridge only** (export spine still `arx export` / agent `ifc.export` same exporter) · Do not ignore import warnings · Do not use floating `main`.

**iPhone PWA (accelerated HB6):** Optional same-day companion once agent runs on the laptop — see [iphone-pwa-acceleration.md](./iphone-pwa-acceleration.md). CLI S3+S5 remains the **pin/evidence** path; phone loop is for review/capture UX once Batch A+ ships.

---

## Part A — Pin install + smoke (S3) ≈ 30–60 min

### A1. Get the pin

```bash
git clone <approved-arxos-remote> arxos
cd arxos
git checkout v2.0.0-pilot.4
git rev-parse HEAD
# MUST print: 659bbd9f369c0b942f150983b204ea054fc595a0
```

| Evidence | What to capture |
| :--- | :--- |
| Screenshot or paste | `git rev-parse HEAD` output |
| Note | Machine OS + date |

### A2. Install

```bash
cargo install --path . --locked
arx --version
# expect: arx 2.0.0 (or similar version string from crate)
```

If `--locked` fails: `cargo install --path .` then **record full SHA** in charter (still on tag).

### A3. Smoke (from pin checkout)

```bash
# still in arxos repo root after cargo build if needed:
cargo build -q
./scripts/l1_smoke.sh
```

| Expected | Failure → |
| :--- | :--- |
| Ends with `L1 smoke PASS` | File stuck note; eng S7 — do not “fix” with unpinned main |

| Evidence | What to capture |
| :--- | :--- |
| Screenshot/log | Last 20 lines of smoke including PASS |
| Note | Wall-clock minutes |

**S3 done when:** SHA matches pin + smoke PASS on this machine.

---

## Part B — Real IFC import + LossReport (S5) ≈ 30–90 min

Work in a **pilot project directory** (not the arxos source tree).

### B1. Init pilot project

```bash
mkdir -p ~/arx-pilots/SITE_NAME
cd ~/arx-pilots/SITE_NAME
arx init --name "SITE_NAME"
# Record Building UUID from output or building.yaml → charter §2
```

| Expected | Evidence |
| :--- | :--- |
| `building.yaml` created; Git on `main` (unless `--no-git`) | Paste building id |

### B2. Import IFC (compiler spine)

```bash
# Prefer full path to IFC. Optional: tee a log for the field-truth pack.
arx import ifc /secure/path/to/vendor.ifc 2>&1 | tee import-ifc.log
```

**Expected shape (example from lab wall sample — your counts will differ):**

```text
Importing IFC (compiler spine): /path/to/file.ifc
  Policy: vendor BIM → clean IFC export → arx (no CAD plugins)
Imported successfully to building.yaml
  Fidelity: L2
  Merge: rooms … / …, equipment … / …
  Warnings (N):
    - [unmapped_products] … IFCWALL×…, IFCWINDOW×…   # common — NOT a failure
    - [other_code] …
  Validation: ok
```

| If you see… | Meaning | Action |
| :--- | :--- | :--- |
| `Imported successfully` + `Validation: ok` | Write succeeded | Continue |
| `[unmapped_products]` | Walls/etc. present but not Arx domain | **Log in A2** — honesty, not crash |
| `file too large` / `ARX_MAX_IFC_BYTES` | R6 refuse | See [resource-limits.md](./resource-limits.md); raise env only with headroom; log §C |
| `IFC import failed` / panic | Blocker | Stop; eng S7 + stuck-list |
| `Validation failed; refusing to write` | Hard gate worked | Fix model or file eng; do not bypass |

### B3. Validate + export

```bash
arx validate 2>&1 | tee validate.log
mkdir -p exports
arx export --format ifc --output exports/out.ifc 2>&1 | tee export.log
ls -la exports/out.ifc
```

| Expected | Evidence |
| :--- | :--- |
| Validate completes (0 errors preferred; warnings OK) | `validate.log` |
| `Export successful` + non-zero `out.ifc` | `export.log` + file size |

Optional re-import round-trip:

```bash
arx import ifc exports/out.ifc 2>&1 | tee reimport.log
```

### B4. Fill field-truth-log (required evidence)

Open [field-truth-log.md](./field-truth-log.md) (copy privately if models are sensitive).

1. Header: pin SHA, site, date, operator.  
2. **§A** matrix row: floors/rooms in→out, GlobalIds, notes.  
3. **§A2** paste warning codes from `import-ifc.log` (especially `unmapped_products`).  
4. **§C** if file was large or slow (time, RAM, env overrides).  
5. **§D** any bugs.  
6. Sign-off when pilot owner reviews.

| Evidence pack (zip or private share) | |
| :--- | :--- |
| `import-ifc.log` | Required |
| `validate.log` / `export.log` | Required |
| Filled field-truth §A + §A2 | Required |
| Screenshot of `git rev-parse HEAD` from Part A | Required |
| Redacted IFC name/tool/version | Required in matrix |

**Do not** commit facility IFC to public remotes.

**S5 done when:** ≥1 real IFC matrix row + A2 filled + export exists.  
Incomplete wall mapping is **expected** — do not block on full BIM.

---

## Part C — Optional same day (not required for S5)

| Task | When |
| :--- | :--- |
| `arx stage` + `arx commit -m "import vendor ifc"` | If Git remote approved |
| Second-person checklist ([second-person-checklist.md](./second-person-checklist.md)) | S4 — different person |
| LiDAR room scan | S6 only if hardware + charter allows |
| iPhone ↔ agent connect smoke | After eng Batch A (configurable host); same Wi-Fi/hotspot as laptop |

---

## Stuck >10 minutes

Write: step letter, exact command, full error text, OS, `arx --version`, pin SHA.  
Send to eng as **S7 stuck-list** — do not switch to `main` or disable validation.

**Related:** [l1-supported-workflow.md](./l1-supported-workflow.md) · [resource-limits.md](./resource-limits.md) · [ifc-limitations.md](./ifc-limitations.md)
