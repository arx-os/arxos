<!--
ARCHIVED — not living product documentation.
Reason: Decision 9 (docs/adr/web-demotion.md) — interactive WASM/PWA field client abandoned.
Web = static landing only. Phone LiDAR = future native iOS. Capture = file IFC/LiDAR + agent + TUI.
Do not treat this file as current design or supported workflow.
-->

> **ARCHIVED (2026-07-24).** Historical only. Interactive PWA/device guides are no longer product truth. See [`docs/adr/web-demotion.md`](../adr/web-demotion.md) and [`docs/INDEX.md`](../INDEX.md).

# Create New — camera capture (PWA + agent)

**Acceptance:** The PWA primary action **Create New** opens the device camera (`getUserMedia`), shows a live preview, captures one or more JPEG frames, sends them to the agent, and creates a **proposed** room on the durable Building so Label / Review can continue.

**Features:** `web` (PWA) + `agent` (laptop bridge)  
**Spine:** frames land under `imports/captures/`; room is written only after validate/finalize → `building.yaml`. Official IFC export path unchanged.

---

## What capture produces today (honest)

| Produced | Not produced |
| :--- | :--- |
| 1–8 JPEG frames on disk (`imports/captures/<timestamp>/frame_XX.jpg`); UI default 1, optional burst of 3 | LiDAR depth / RoomPlan mesh |
| `manifest.json` (`source: pwa_getUserMedia`, frame list, geometry/depth/mesh flags all false) | Point cloud / PLY |
| A **placeholder** room (optional name or `Room-YYYYMMDD-HHMMSS`) | Accurate room dimensions or walls |
| Room props: `review_status=proposed`, `capture_source=camera`, `capture_frames`, `capture_dir`, `capture_note` | Automatic equipment detection |
| Ingest summary lines on the agent result (not a full IFC LossReport) | Full ARKit geometry |
| Durable write only after `finalize_ingest` + validation → `building.yaml` | Agent-side IFC export (export remains Review / `arx export`) |

Browser APIs cannot access iOS RoomPlan or LiDAR mesh. This path is evidence frames + a room node for labeling — nothing more.

**Spine:** agent RPC is a bridge only. Frames → disk; room mutation → `finalize_ingest(validate)` → refuse write on errors → `save_building_at` → `building.yaml`.

---

## HTTPS / secure-context requirement (camera)

`getUserMedia` requires a **secure context**:

| How you open the PWA | Camera? | Agent WebSocket |
| :--- | :---: | :--- |
| `http://127.0.0.1:8080` or `http://localhost:8080` | Yes (localhost exception) | `ws://` |
| `http://192.168.x.x:8080` (phone → laptop LAN) | **No** (insecure) | `ws://` works, camera blocked |
| `https://…` (LAN or tunnel) | Yes | Page uses **`wss://`** automatically — agent must be TLS-terminated or reverse-proxied |

**iOS Safari on a phone will not open the camera over plain HTTP to a LAN IP.**  
Serve the PWA over **HTTPS** for field phone tests.

The agent itself still listens plain HTTP/WS on `:8787` by default. For HTTPS PWA + phone:

1. Terminate TLS in front of both static files and the agent WebSocket, **or**
2. Develop camera on laptop `localhost` (secure) with agent `127.0.0.1:8787`.

---

## Builds

```bash
# From arxos checkout
cargo build --features agent --bin arx

# PWA (needs trunk: cargo install trunk)
trunk serve --features web   # http://0.0.0.0:8080 — camera only on localhost
```

---

## Laptop — pilot project + agent

```bash
mkdir -p ~/arx-pilots/create-new && cd ~/arx-pilots/create-new
ARX=/path/to/arxos/target/debug/arx   # adjust

$ARX init --name "Create New Pilot"
$ARX agent
```

Copy from console:

- `ROOT TOKEN: did:key:…`
- Agent host: laptop LAN IP `:8787` (or `127.0.0.1:8787` on same machine)

---

## Option A — Laptop browser (fastest end-to-end)

Camera works without mkcert because **localhost is a secure context**.

1. `trunk serve --features web` → open **`http://127.0.0.1:8080/`** (not the LAN IP).
2. Header: Agent host `127.0.0.1:8787`, paste token → **Connect** → ● Online.
3. Home → **Create New (camera)** (or nav **Create New**).
4. Optional room name → **Create New — Open camera** → allow permission.
5. Live preview should show rear/environment camera when available.
6. **Capture & send to agent** (optional: Burst 3 frames).
7. Status shows created room; **What this capture produced** lists frames + proposed room.
8. **Review hierarchy** → room appears with `proposed` → Label / Accept as before.

Laptop confirm:

```bash
cd ~/arx-pilots/create-new
ls -la imports/captures/*/
grep -E 'capture_source|review_status|Room-' building.yaml | head -40
```

---

## Option B — iPhone over LAN (HTTPS required)

### B1. mkcert + Caddy reverse proxy (recommended field recipe)

On the **laptop**:

```bash
# Install once: mkcert, caddy
mkcert -install
cd /tmp
mkcert laptop.local 192.168.x.x localhost 127.0.0.1   # use your real LAN IP + hostname

# Example Caddyfile (adjust paths, IP, ports)
# - :8443 HTTPS → trunk PWA on 8080
# - /ws → agent on 8787 (WebSocket)
```

Example `Caddyfile`:

```caddy
{
    auto_https off
}

https://192.168.x.x:8443 {
    tls /tmp/192.168.x.x+3.pem /tmp/192.168.x.x+3-key.pem

    @ws path /ws*
    reverse_proxy @ws 127.0.0.1:8787

    reverse_proxy 127.0.0.1:8080
}
```

Then:

```bash
# Terminal 1 — PWA
trunk serve --features web

# Terminal 2 — agent in pilot dir
arx agent

# Terminal 3 — TLS front door
caddy run --config /path/to/Caddyfile
```

**iPhone:**

1. Trust the mkcert root CA on the phone (install `rootCA.pem` from `mkcert -CAROOT`, Settings → General → About → Certificate Trust Settings on iOS).
2. Join same Wi‑Fi/hotspot as the laptop.
3. Open **`https://<laptop-ip>:8443/`**.
4. Agent host: **same host:8443** (WSS is same origin via Caddy `/ws`)  
   *If you point agent host at `:8787` while the page is HTTPS, the client will try `wss://IP:8787` which fails unless the agent has TLS. Prefer same-origin `/ws` via the proxy — host field should be `IP:8443` with path handled by normalize? Wait - our client always appends `/ws` on the agent host. So agent host = `192.168.x.x:8443` works if Caddy proxies `/ws` to agent.*
5. Paste token → Connect → Create New → Open camera → Capture.

### B2. Desktop-only fallback

If CA install is blocked on the phone, run Create New on laptop Safari/Chrome at `http://127.0.0.1:8080` (Option A). Phone can still Label/Review if you only need camera once on laptop.

---

## Exact phone/desktop test checklist

- [ ] Agent Online in header  
- [ ] **Create New — Open camera** prompts for camera permission  
- [ ] Live preview fills the black panel  
- [ ] **Capture & send** returns building name + room name  
- [ ] Review page **Refresh** shows the new room (`proposed`)  
- [ ] Laptop: `imports/captures/<stamp>/frame_01.jpg` exists  
- [ ] Laptop: room has `capture_source: camera` in `building.yaml`  
- [ ] Label flow still works for that room name  

---

## RPC contract (agent)

```text
method: capture.from_camera
params:
  frames: string[]     # base64 JPEG (with or without data: URL prefix); 1..=8
  room_name?: string   # collision → "Name-<stamp-suffix>"
  floor?: string       # default "Ground Floor" (created if missing)
result:
  building_name, room_name, yaml_path, capture_dir, frame_count,
  floors, rooms, equipment, report_summary, produced[], validation_ok
errors (examples):
  empty frames · >8 frames · base64 decode · frame >4 MiB · validation failed
```

Capability: `capture.from_camera` (included on agent root token).

**Limits (server):** max 8 frames/request; ~4 MiB decoded bytes per frame.

---

## Failure modes

| Symptom | Likely cause |
| :--- | :--- |
| “Camera requires a secure context…” | HTTP to LAN IP — use HTTPS or localhost |
| getUserMedia permission denied | User denied; iOS Settings → Safari → Camera |
| Capture OK but agent fails | Offline / wrong token / missing capability |
| Online on phone but WS fails on HTTPS page | Mixed content: need WSS / reverse proxy (Option B1) |
| Preview black, capture “dimensions 0” | Wait until preview is live; re-open camera |

---

## Out of scope (this sprint)

- ARKit / RoomPlan / LiDAR depth or mesh reconstruction  
- Automatic wall / equipment detection from frames  
- Fancy 3D preview of the room  
- File picker as the **primary** Create New path (still available under section 3)  
- Treating the agent as an official IFC export authority  
- Owner / claims / blockchain  

## Unit tests (agent feature)

```bash
cargo test --features agent --lib capture
```

Covers: proposed room + frames, YAML round-trip provenance, empty/too-many/bad-base64/oversized frames, data-URL prefix, name collision rename, bootstrap without `building.yaml`.

Related: [bedroom-loop.md](./bedroom-loop.md) · [iphone-pwa-acceleration.md](./iphone-pwa-acceleration.md)
