# Batch B proposal — iPhone review + approved export (await approval)

**Status:** Proposal only — **do not merge until vision holder approves**  
**Depends on:** Batch A Pass A green ✅  
**Goal:** Phone views laptop model, reviews `proposed`, triggers `approved_only` IFC export on capture node.  
**Constraint:** Thin agent RPC wrappers only; **no** IFC/YAML/validate spine rewrite. Reversible feature-gated work (`agent` + `web`).

---

## 1. Prioritized implementation order

| Step | ID | Work | Unblocks | Est. |
| :---: | :---: | :--- | :--- | :---: |
| **1** | **B1** | Agent `building.get` → load `building.yaml` + review summary JSON | Phone sees live SSOT | S |
| **2** | **B2** | PWA **Review** page: connect-gated load via `building.get` | Hierarchy source of truth | S |
| **3** | **B3** | Hierarchy list + **proposed** badges (rooms/equip) | Review targets visible | M |
| **4** | **B4** | Agent `edit.apply` `{script}` → text DSL + `persist_building_at` | Accept/reject durable | M |
| **5** | **B5** | Accept / Reject buttons (44px) → `set … review_status=…` | Human gate | S |
| **6** | **B6** | LossReport / review panel (from get + last export warnings) | Honesty on phone | S |
| **7** | **B7** | **Export approved-only** button → existing `ifc.export` | Close loop | S |
| **8** | **B8** | Docs: Pass B test plan in `iphone-field-loop.md` | Field UAT | S |

**Ship gate after 1–3:** can load + see proposed (read-only).  
**Ship gate after 1–7:** full Pass B.  
**Out of Batch B:** `lidar.import` (Batch C), ARKit, git redesign, wall mapping.

### Capability model (thin)

| RPC | Capability (reuse or add) |
| :--- | :--- |
| `building.get` | `building.get` (new) **or** reuse `files.read` |
| `edit.apply` | `edit.apply` (new) |
| `ifc.export` | already `ifc.export` |

Recommendation: **new caps** on root token only (same as other caps), listed at agent boot.

### Alternative without new RPC (not recommended)

- `files.read` path `building.yaml` — works for **get** only.  
- Accept/reject still needs a **write** path → `edit.apply` (or unsafe free-form write). Prefer explicit `edit.apply` + validate via `persist_building_at`.

---

## 2. Concrete diffs — first 3 items (B1–B3)

### B1 — `src/agent/building.rs` (new, thin)

```rust
//! Read-only building snapshot for PWA review (Batch B).
use std::path::Path;
use anyhow::{anyhow, Result};
use serde::Serialize;
use crate::core::{room_review_status, equipment_review_status, summarize_review, ReviewStatus};
use crate::persistence::{load_building_at, BUILDING_YAML};

#[derive(Serialize)]
pub struct BuildingGetResult {
    pub building: crate::core::Building,
    pub yaml_path: String,
    pub review_warnings: Vec<String>,
    pub proposed_rooms: usize,
    pub proposed_equipment: usize,
}

pub fn get_building(repo_root: &Path) -> Result<BuildingGetResult> {
    let building = load_building_at(repo_root)
        .map_err(|e| anyhow!("Failed to load {}: {}", BUILDING_YAML, e))?;
    let summary = summarize_review(&building);
    let proposed_rooms = building
        .get_all_rooms()
        .iter()
        .filter(|r| room_review_status(r) == Some(ReviewStatus::Proposed))
        .count();
    // get_all_equipment if available; else walk floors
    let proposed_equipment = building
        .get_all_equipment()
        .iter()
        .filter(|e| equipment_review_status(e) == Some(ReviewStatus::Proposed))
        .count();
    Ok(BuildingGetResult {
        review_warnings: summary.warning_lines(),
        building,
        yaml_path: BUILDING_YAML.to_string(),
        proposed_rooms,
        proposed_equipment,
    })
}
```

*(Adjust `get_all_rooms` / `get_all_equipment` to match real Building API — use existing helpers from `Building`.)*

### B1 — `dispatcher.rs` + `auth.rs` + root caps

```diff
// dispatcher match:
+        "building.get" => handle_building_get(&state.repo_root),

// auth:
+        "building.get" => Some("building.get"),

// server root capabilities:
+        "building.get".to_string(),
```

```rust
fn handle_building_get(root: &Path) -> Result<Value> {
    let result = crate::agent::building::get_building(root)?;
    Ok(serde_json::to_value(result)?)
}
```

### B2+B3 — PWA page sketch `src/web/pages/review.rs`

- Route `/review` in `app.rs`  
- On mount (if Online): `send_rpc("building.get", {})`  
- Render:
  - Status strip: Online + host + `# proposed rooms/equip`  
  - Flat list (mobile): floor › room / equip name + badge color  
  - Badge: proposed=amber, accepted=green, rejected=gray, none=slate  
- Touch: row min-height 48px; later B5 adds Accept/Reject per row  

```rust
// pseudocode load
spawn_local(async move {
  match send_rpc("building.get", json!({})).await {
    Ok(v) => { /* set building + review_warnings signals */ }
    Err(e) => set_status(e),
  }
});
```

**B4–B5 (preview, not in first 3 apply):**

```rust
// edit.apply
// params: { "script": "set room Kitchen review_status=accepted\n" }
// load → apply_text_script → persist_building_at(root, building, false, None)
```

```diff
+        "edit.apply" => handle_edit_apply(&state.repo_root, params),
```

**B7 (preview):** already have RPC:

```js
send_rpc("ifc.export", { approved_only: true, filename: "approved.ifc" })
// show result.filename + size_bytes; file on laptop exports/
```

---

## 3. Mobile UI polish (within Batch B)

| Polish | Where |
| :--- | :--- |
| Sticky action bar: Refresh · Export approved | Review page bottom |
| Toast/status line for every RPC (busy / ok / err) | Shared pattern from Batch A header |
| 44–48px buttons; full-width primary actions | Accept/Reject/Export |
| Single-column layout (drop 2-col grid on detail) | review + detail |
| Proposed filter toggle: All / Proposed only | Hierarchy |
| Disable Export when Offline | Clear message: “Connect agent” |

---

## 4. Pass B test instructions (iPhone)

### Preconditions

- Pass A green (Online with LAN host)  
- Laptop agent running in pilot dir with `building.yaml` that has **some** `review_status=proposed` entities (or LiDAR import on laptop first)  
- Same Wi-Fi/hotspot  

### Steps

1. Connect (Batch A).  
2. Open **Review** (or Buildings → load from agent).  
3. Tap **Refresh** → hierarchy appears; proposed count matches laptop.  
4. Accept one room → Refresh → badge accepted.  
5. Reject one entity → badge rejected.  
6. Open LossReport / review warnings panel → non-empty if proposed remain or import warnings cached.  
7. Tap **Export approved-only** → status shows path/size; on laptop `exports/*.ifc` exists.  
8. Laptop: `arx validate` still OK.  

### Pass B criteria

| Check | |
| :--- | :---: |
| Phone loads building from agent (not only localStorage IFC) | [ ] |
| Proposed entities visible with badges | [ ] |
| Accept/Reject persists (reload shows change) | [ ] |
| Export approved_only creates file on laptop | [ ] |
| Offline shows errors; no silent success | [ ] |

---

## 5. Risk notes

| Risk | Mitigation |
| :--- | :--- |
| Large building JSON over WS | OK for one school floor; later paginate |
| Concurrent edit vs auto-export watcher | Review still validates on persist |
| “Agent core” concern | Only new thin modules + match arms; no IFC parser changes |

---

## 6. Approval checklist

| Decision | |
| :--- | :--- |
| Approve B1–B3 (get + hierarchy UI) first PR? | [ ] yes / [ ] no |
| Include B4–B7 in same PR after B1–B3 green? | [ ] yes / [ ] split |
| Cap names `building.get` / `edit.apply` OK? | [ ] yes |

**Next message from you:** `Approve B1–B3` or `Approve full Batch B` to implement.
