# iPhone + laptop agent field loop (Batch A)

**Pin / features:** build from `main` with `--features agent` (laptop) and `--features web` (PWA).  
**L1 pin** `v2.0.0-pilot.4` does not yet include Batch A phone connect — use a post–Batch A `main` SHA until pilot.5.  
**Plan:** [iphone-pwa-acceleration.md](./iphone-pwa-acceleration.md)

---

## Setup (same Wi-Fi or personal hotspot)

### Laptop (capture node)

```bash
cd /path/to/arxos   # or pilot project parent
# Prefer running agent from a pilot project that has building.yaml
cd ~/arx-pilots/SITE_NAME   # if agent detects repo root from cwd

# From arxos checkout:
cargo run --features agent --bin arx --  # if CLI exposes agent
# or invoke the library entry your tree uses for agent start
```

When the agent starts you should see:

```text
📡 Server listening on http://0.0.0.0:8787
┌─ iPhone / PWA connect …
│    Agent host: <LAN_IP>:8787
│ Token (copy once): did:key:…
```

Copy **Agent host** and **ROOT TOKEN**.

### Serve PWA over HTTP (required)

Safari blocks `ws://` from **https** pages. Serve the WASM app over **http://** on the LAN, e.g.:

```bash
# From arxos checkout (adjust to your trunk/wasm workflow)
cargo build --features web --bin arx-web
# serve dist/ with any static HTTP server bound to 0.0.0.0, e.g.:
# python3 -m http.server 8080 --bind 0.0.0.0
```

On iPhone open: `http://<LAPTOP_LAN_IP>:8080/` (not https).

### iPhone

1. Join the **same** Wi-Fi or the laptop’s **Personal Hotspot**.  
2. Open the PWA URL above.  
3. Header fields:
   - **Agent host:** `192.168.x.x:8787` (from agent console — **not** `127.0.0.1`)  
   - **Agent token:** paste `did:key:…`  
4. Tap **Connect**.  
5. Expect **● Online** and status `Connected → <host>`.  
6. Home page status card should show the same host and Online.

---

## Pass A verification

| Check | Pass |
| :--- | :---: |
| Agent console prints iPhone connect box + token | [ ] |
| PWA host field accepts `IP` or `IP:8787` (port defaulted) | [ ] |
| iPhone **● Online** with host ≠ `127.0.0.1` | [ ] |
| Wrong token → Offline + clear error text | [ ] |
| Reopen PWA → auto-connect with saved host/token | [ ] |
| Home status card matches header | [ ] |

**Fail if:** only works with `127.0.0.1` on the phone, or Online with no agent running.

---

## Troubleshooting

| Symptom | Fix |
| :--- | :--- |
| Stays Offline | Confirm same network; laptop firewall allows 8787; use LAN IP not localhost |
| Works on laptop Safari, not iPhone | You used `127.0.0.1` — use laptop LAN IP on phone |
| Connect fails after https:// PWA | Reserve **http://** origin |
| No LAN IP in agent log | Run `ipconfig getifaddr en0` (macOS) and type it manually |
| Token empty | Copy full `did:key:…` from agent boot |

---

## After Pass A → Batch B readiness

Batch A only proves **connect**. **B1–B3 (read-only Review)** is on `main` after approval.

### Pass B read-only (B1–B3)

**Laptop**

```bash
# Pilot project with building.yaml (optionally mark a room proposed for badges)
cd ~/arx-pilots/SITE
# ensure building.yaml exists; agent detects repo root from cwd / walk-up
# start agent with --features agent
```

**iPhone**

1. Pass A: header **● Online** (LAN host, not 127.0.0.1).  
2. Open **Review** (nav or Home → Review).  
3. Tap **Refresh** (or auto-load).  
4. Expect building name, floor/room/equip counts, hierarchy rows (≥48px).  
5. Toggle **Proposed only** — list filters to `proposed` badges.  
6. If any proposed/rejected LiDAR autos: **Review warnings** section lists them.  
7. **Export (soon)** stays disabled until B7.

| Pass B (read-only) | |
| :--- | :---: |
| `building.get` succeeds from phone | [ ] |
| Hierarchy shows rooms/equip from laptop YAML | [ ] |
| Proposed badges visible when status set | [ ] |
| Proposed-only filter works | [ ] |
| Offline → clear error, no fake data | [ ] |

**Not yet (B4–B7):** Accept/Reject, durable edit, approved export button.

**Related:** [iphone-pwa-acceleration.md](./iphone-pwa-acceleration.md) · [batch-b-proposal.md](./batch-b-proposal.md) · [field-day-1-runbook.md](./field-day-1-runbook.md)
