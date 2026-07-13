# Eng blocker queue (Horizon B sprint) — approval required

**Status:** Proposals only. **Do not merge** until vision holder / pilot owner says go.  
**Pin baseline:** `v2.0.0-pilot.4` @ `659bbd9f`  
**Rule:** Field evidence before features · CLI honesty · no spine rewrite · LOC minimal.

---

## Field readiness (no code needed)

CLI already prints LossReport codes on import, e.g.:

```text
  Warnings (1):
    - [unmapped_products] 2 product entity(ies) present in IFC but not imported into Arx domain (IFCWALL×1, IFCWINDOW×1)
```

Resource refuse already names `ARX_MAX_*` and `docs/resource-limits.md`.  
**Day-1 field can proceed without E1–E3.**

---

## Proposal table

| ID | Priority | Unblocks | Recommendation | Apply? |
| :---: | :---: | :--- | :--- | :---: |
| **E1** | P3 | S4 5b / S5 A2 discipline | One tip line after warnings | Optional |
| **E2** | P3 | Large-IFC confusion | Name **specific** env var from `kind` | Optional |
| **E3** | P2 | R5 BIM path | Longer `import ifc --help` | Optional (docs-in-CLI) |
| **E4** | — | Evidence | Templates/runbook (docs) | **Done** in docs |
| **E5** | — | HB6 | PWA bridge | **Defer** (need Q6) |
| **E6** | — | Product | Wall mapping | **Defer** |

---

## E1 — Tip after LossReport warnings (optional)

**File:** `src/cli/commands/import.rs`  
**Intent:** Remind field to copy codes into field-truth-log A2 without changing mapping.

```diff
         println!("Imported successfully to {}", BUILDING_YAML);
         for line in result.summary_lines() {
             println!("  {}", line);
         }
+        if !result.report.warnings.is_empty() {
+            println!(
+                "  Tip: copy warning [codes] into docs/field-truth-log.md §A2 (LossReport evidence)."
+            );
+        }
 
         Ok(())
```

Also add the same tip on dry-run success path (after its `summary_lines` loop) for symmetry.  
**Risk:** Low. **LOC:** ~6.

---

## E2 — Resource refuse names the right env var (optional)

**File:** `src/resource_limits.rs`  
**Intent:** `kind` is already `"IFC"` / `"LiDAR"` — print the matching override.

```diff
     if len > max_bytes {
         bail!(
-            "{kind} file too large for pilot defaults: {} ({} bytes) exceeds limit {} bytes. \
-             Re-export a lighter model, use a capture node with more RAM, or raise the limit via \
-             env (ARX_MAX_IFC_BYTES / ARX_MAX_LIDAR_BYTES). See docs/resource-limits.md.",
+            "{kind} file too large for pilot defaults: {} ({} bytes) exceeds limit {} bytes. \
+             Re-export a lighter model, use a stronger capture node, or raise {} (see docs/resource-limits.md).",
             path.display(),
             len,
-            max_bytes
+            max_bytes,
+            if kind.eq_ignore_ascii_case("IFC") {
+                "ARX_MAX_IFC_BYTES"
+            } else if kind.eq_ignore_ascii_case("LiDAR") {
+                "ARX_MAX_LIDAR_BYTES"
+            } else {
+                "ARX_MAX_IFC_BYTES / ARX_MAX_LIDAR_BYTES"
+            }
         );
     }
```

Update unit test assert if it keys on full string.  
**Risk:** Low. **LOC:** ~15.

---

## E3 — Richer `arx import ifc --help` (optional)

**File:** `src/cli/spec.rs` on `ImportSubcommand::Ifc`  
**Intent:** Transfer (R5) without reading long docs.

```diff
     /// Import IFC (vendor BIM → clean IFC export → arx)
+    #[command(long_about = "\
+Import a vendor-exported IFC into building.yaml (compiler spine).
+
+BIM policy: Vendor BIM (Revit/ArchiCAD/…) → clean IFC export from that tool → this command.
+No CAD plugins. Incomplete IFC → fix export settings in the BIM tool, not Arx.
+
+Honesty: import prints LossReport warnings (e.g. [unmapped_products] for walls/doors not
+mapped into Arx rooms/equipment). Copy codes into docs/field-truth-log.md §A2.
+
+Size: pilot default max IFC size is ARX_MAX_IFC_BYTES (see docs/resource-limits.md).
+
+Official export later: arx export --format ifc (not agent).")]
     Ifc {
         /// Path to IFC file
         ifc_file: String,
```

**Risk:** Low. **LOC:** ~15.

---

## Do not queue without field stuck-list

| Idea | Why not now |
| :--- | :--- |
| PWA capture / camera LiDAR | HB6; needs Q6 override |
| Wall/slab domain mapping | Product; honesty already landed |
| Auto-upload field-truth | Scope |
| Raise default 50 MiB globally | Hide R6; use env per site instead |

---

## Approval line (fill when deciding)

| ID | Decision | Date | Approver |
| :---: | :--- | :--- | :--- |
| E1 | [ ] yes / [ ] no / [ ] later | | |
| E2 | [ ] yes / [ ] no / [ ] later | | |
| E3 | [ ] yes / [ ] no / [ ] later | | |

After approval: implement on branch off `main`, clippy `-D warnings`, no pin retag unless install-breaking.
