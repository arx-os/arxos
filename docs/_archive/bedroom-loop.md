<!--
ARCHIVED — not living product documentation.
Reason: Decision 9 (docs/adr/web-demotion.md) — interactive WASM/PWA field client abandoned.
Web = static landing only. Phone LiDAR = future native iOS. Capture = file IFC/LiDAR + agent + TUI.
Do not treat this file as current design or supported workflow.
-->

> **ARCHIVED (2026-07-24).** Historical only. Interactive PWA/device guides are no longer product truth. See [`docs/adr/web-demotion.md`](../adr/web-demotion.md) and [`docs/INDEX.md`](../INDEX.md).

# Bedroom loop — PWA + agent (end-to-end)

**Goal:** In one session, capture a bedroom structure, label **Ceiling Fan** + **Light Switch**, validate, export IFC (`approved_only`), and confirm `building.yaml` on the laptop.

**Features:** laptop `--features agent` · browser `--features web`  
**Spine:** agent is bridge only; durable writes go through ingest/validate → `building.yaml` → `export::ifc`.

**Platform honesty:** Pure WASM/PWA **cannot** access iOS ARKit/RoomPlan LiDAR. Capture is:
1. **Create New (camera)** — `getUserMedia` → JPEG frames → agent `capture.from_camera` → proposed room ([create-new-camera.md](./create-new-camera.md)), and/or  
2. **Create Bedroom room** (structure-only form), and/or  
3. **File upload** `.ply` / `.las` / `.xyz` / `.ifc` → agent `lidar.import` / `ifc.import`.

**Camera + HTTPS:** Phone LAN HTTP cannot open the camera. Prefer `http://127.0.0.1` for laptop tests, or HTTPS reverse proxy for iPhone — see [create-new-camera.md](./create-new-camera.md).

---

## 0. One-time builds

```bash
# From arxos checkout
cargo build --features agent --bin arx
# PWA (needs trunk: cargo install trunk)
trunk serve --features web   # serves http://0.0.0.0:8080  (see Trunk.toml)
# Or: cargo build --features web --bin arx-web  then serve dist via trunk
```

Serve the PWA over **http://** (not https) so `ws://` to the agent is allowed.

---

## 1. Laptop — pilot project + agent

```bash
mkdir -p ~/arx-pilots/bedroom-loop && cd ~/arx-pilots/bedroom-loop
# Use built binary (adjust path)
ARX=/path/to/arxos/target/debug/arx

$ARX init --name "Bedroom Pilot"
$ARX validate

# Start agent bound to this project (Git root = cwd after init)
$ARX agent
# Or: ARXOS_REPO_ROOT=$PWD $ARX agent --path "$PWD"
```

**Copy from agent console:**
- `ROOT TOKEN: did:key:…`
- `Agent host: <LAN-IP>:8787` (on same machine browser use `127.0.0.1:8787`)

---

## 2. Browser / phone — connect

1. Open `http://<laptop-ip>:8080/` (or `http://127.0.0.1:8080/` on laptop).  
2. Header: **Agent host** = LAN IP:8787 (or 127.0.0.1:8787).  
3. Paste **token** → **Connect** → header shows **● Online**.

---

## 3. Capture

1. Nav → **Create New** (or Home → **Create New (camera)**).  
2. Preferred: **Create New — Open camera** → **Capture & send to agent** (proposed room appears).  
3. Or structure-only: **Create / ensure Bedroom room**.  
4. Optional secondary: **Choose scan or IFC file** (`.ply`/`.xyz`/`.ifc`) — LossReport panel fills.  
5. Proceed to Label (use the new room name if camera path).

---

## 4. Label (exactly two objects)

1. Nav → **Label**.  
2. Room = `Bedroom` (default).  
3. Tap **Add Ceiling Fan + Light Switch (proposed)**.  
4. Tap **Accept both (review_status=accepted)**  
   *or* open Review and Accept each row.

---

## 5. Review → Validate → Export

1. Nav → **Review** → **Refresh**.  
2. Confirm hierarchy shows:
   - room **Bedroom**
   - equip **Ceiling Fan** (accepted)
   - equip **Light Switch** (accepted)
3. **Validate** — expect OK (or honest error lines).  
4. Leave **Export approved_only** checked → **Export IFC**.  
5. Agent writes `exports/bedroom-approved.ifc` under the pilot dir.

---

## 6. Laptop confirm

```bash
cd ~/arx-pilots/bedroom-loop
grep -E 'Ceiling Fan|Light Switch|review_status' building.yaml
ls -la exports/
# Optional CLI parity:
$ARX validate
$ARX export --format ifc --approved-only --output exports/cli-approved.ifc
```

---

## Acceptance checklist

| Step | Pass? |
| :--- | :---: |
| Agent starts, prints token + LAN hints | [ ] |
| PWA Connect → Online | [ ] |
| Bedroom room in model | [ ] |
| Ceiling Fan + Light Switch equipment | [ ] |
| review_status proposed → accepted | [ ] |
| Validate summary shown | [ ] |
| Export IFC path reported | [ ] |
| building.yaml contains both names | [ ] |

---

## Known failure modes

| Symptom | Fix |
| :--- | :--- |
| Connect fails on iPhone with 127.0.0.1 | Use laptop LAN IP; same Wi-Fi/hotspot |
| PWA is https, ws blocked | Serve trunk over **http** |
| Agent: not inside Git repo | Run `arx init` first (creates Git) or `arx agent --path …` |
| edit.apply “already exists” | Refresh Review; Accept existing; or rename |
| LiDAR sparse PLY creates no rooms | Use **Create Bedroom** then Label (expected) |
| Export empty of fan/switch | Accept them first if using approved_only |
| Large upload fails | Raise `ARX_MAX_LIDAR_BYTES` / `ARX_MAX_IFC_BYTES` |

---

## Agent RPCs used

| Method | Role |
| :--- | :--- |
| `building.get` | Hierarchy + proposed counts |
| `building.validate` | Validation summary |
| `edit.apply` | Text DSL mutations (label / review_status) |
| `lidar.import` | Base64 scan → import spine |
| `ifc.import` | Base64 IFC → import spine |
| `ifc.export` | `approved_only` supported |

**Related:** [iphone-field-loop.md](./iphone-field-loop.md) · [l1-supported-workflow.md](../pilot/supported-workflow.md)
