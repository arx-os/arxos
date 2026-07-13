# iPhone PWA + agent acceleration plan

**Status:** **Batch A implemented** (P0.1–P0.5) — confirm Pass A on devices before Batch B  
**North star (accelerated HB6):** Open ArxOS PWA on iPhone on-site → connect to laptop agent (hotspot/LAN) → import LiDAR/files → label/review `proposed` → see LossReport → trigger validated export (`--approved-only`) with human gates.  
**Pin baseline:** `v2.0.0-pilot.4` @ `659bbd9f` (runtime). Work lands on `main` behind features `web` + `agent`.  
**Spine rules:** Agent remains **bridge only**; durable write = validate + `building.yaml`; official IFC = same `export::ifc` path; honesty (LossReport) never skipped.

**Related:** [horizon-b-roadmap.md](./horizon-b-roadmap.md) · eng queue later · [field-day-1-runbook.md](./field-day-1-runbook.md)

---

## 1. Current state audit (iPhone viability)

| Area | Today | iPhone gap |
| :--- | :--- | :--- |
| **PWA shell** | Leptos CSR (`arx-web`), routes: Home / Import IFC / Buildings / Detail | Desktop-ish header; not touch-first; no Install/PWA manifest audit |
| **Agent connect** | Header token → `ws://127.0.0.1:8787/ws?token=…` | **Hardcoded loopback** — iPhone **cannot** reach laptop agent |
| **Agent bind** | Agent listens `0.0.0.0:8787` ✅ | Host URL must be configurable on phone (LAN IP / hostname) |
| **HTTPS / mixed content** | Dev typically `http` trunk serve | If PWA is HTTPS, browser **blocks** `ws://` — must serve PWA over **HTTP on LAN** or use secure tunnel carefully |
| **Auth** | DID token + capabilities (git/ifc) | Need print of connect URL + token on agent boot for field |
| **IFC import (WASM)** | In-browser native parse + envelope + LossReport store | Works offline for **small** IFC; large IFC may OOM phone — prefer agent path for site files |
| **IFC import (agent)** | `ifc.import` base64 → `import_ifc_path` spine | PWA Import page does **not** call agent; no progress for large uploads |
| **LiDAR import** | CLI only (`arx import lidar`) | **No** `lidar.import` RPC · **no** PWA UI · binary PLY via base64 is heavy but viable for **one room** |
| **Building hierarchy** | Detail page: counts + ASCII render | No collapsible floor/room list; no filter `proposed` |
| **review_status** | CLI/text DSL (`set room X review_status=accepted`) | **No** accept/reject buttons in PWA; WASM has `apply_text_script_json` but no UI |
| **Labeling** | `apply_text_script_json` in wasm_bridge | No simple form; no agent `edit.apply` |
| **LossReport** | Import page tries to show report lines; envelope has `report` summary lines | Not first-class panel; agent import result may not return full warnings |
| **Export** | Agent `ifc.export` + `approved_only` ✅ | **No** PWA button; auto-export watcher is convenience only (not official UX) |
| **Git** | `git.status` / `git.commit` from detail page | Usable once connected; needs large touch targets |
| **Offline** | localStorage envelope | Offline review of last building OK; capture/export needs agent online |
| **Files / Photos** | `<input type=file accept=.ifc>` | iOS Files OK for IFC/PLY if accept expanded; Photos LiDAR not ARKit mesh export without extra work |
| **ARKit / RoomPlan** | **None** | **Defer** (P2+): export USDZ/PLY offline → agent import; no in-app AR this sprint |
| **Touch UX** | Small 12px token field | Need mobile CSS, sticky connect bar, 44px targets |
| **Spine safety** | Agent IFC import/export uses ingest/export spine | Keep; do not add second export path |

### Architecture target (iPhone loop)

```text
iPhone Safari/PWA  ──ws://LAPTOP_IP:8787──►  Agent (laptop, pilot project dir)
   review / label / trigger                    import lidar|ifc → validate
   show LossReport / hierarchy                 building.yaml + Git
                                               export --approved-only → file on laptop
```

**Capture node of record = laptop.** Phone is controller + light local cache, not sole durable store for pilot.

---

## 2. High-impact backlog (prioritized)

### P0 — Unblock iPhone ↔ agent (must ship first)

| ID | Item | Why | Est. |
| :---: | :--- | :--- | :---: |
| **P0.1** | Configurable agent **host:port** in PWA (not only 127.0.0.1); persist localStorage | Without this, phone never connects | S |
| **P0.2** | Agent boot prints **LAN connect hint** (IP candidates + `ws://…/ws?token=` + PWA field help) | Field discoverability | S |
| **P0.3** | Mobile-first **Connect** strip (host, token, status); large touch targets | Usable one-handed | S |
| **P0.4** | **Field status page**: connected?, repo root name, last error, “open hierarchy” | Orientation on site | S |
| **P0.5** | Docs: iPhone+laptop hotspot runbook (HTTP PWA + agent, no HTTPS trap) | Avoid day-1 failures | S |

### P0 — Review loop (human gates)

| ID | Item | Why | Est. |
| :---: | :--- | :--- | :---: |
| **P0.6** | Agent `building.get` → return `building.yaml` as JSON (+ optional report stub) | Phone sees live SSOT from laptop | M |
| **P0.7** | Hierarchy UI: floors → rooms/equip; badge `proposed` / `accepted` / `rejected` | Core review | M |
| **P0.8** | Accept / Reject buttons → agent `edit.apply` text script **or** wasm apply + push | Human gate | M |
| **P0.9** | LossReport panel (codes + messages) from last import / envelope | Honesty on phone | S |
| **P0.10** | Agent export button: `ifc.export` with `approved_only: true` + status path | Close loop | S |

### P1 — Lightweight capture from phone

| ID | Item | Why | Est. |
| :---: | :--- | :--- | :---: |
| **P1.1** | Agent `lidar.import` (base64 or path-under-inbox) → `import_lidar_path` spine | One-room scan path | M |
| **P1.2** | PWA file picker: `.ply/.las/.csv` + IFC → upload to agent (not parse LiDAR in WASM) | Files app share | M |
| **P1.3** | Progress / size refuse messaging (`ARX_MAX_*`) on phone | Honesty under load | S |
| **P1.4** | Simple label form: rename room / set property via text script | Corrections | S |
| **P1.5** | Agent `inbox/` drop watcher already partial — document “AirDrop to laptop” fallback | Zero-code capture path | Docs |

### P2 — Polish / later (not blocking one-room test)

| ID | Item | Notes |
| :---: | :--- | :--- |
| **P2.1** | ARKit / RoomPlan / RealityScan integration | Export file → same P1.1; no native Swift app in-tree yet |
| **P2.2** | Full offline PWA service worker cache | Optional |
| **P2.3** | QR code on agent console encoding host+token | Nice field UX |
| **P2.4** | WSS / mTLS | Overkill for hotspot pilot |
| **P2.5** | In-browser LiDAR meshing | Non-goal; keep on capture node |
| **P2.6** | E1–E3 CLI tips | Still optional; lower than P0 phone |

---

## 3. Implementation plan (incremental, reversible)

### Principles

1. Feature-gated: `web` + `agent` only; default CLI/TUI pin unchanged.  
2. No spine rewrite; new RPC thin wrappers over `import_*` / `export::ifc` / text edit.  
3. Each step: compile + manual iPhone test or agent unit smoke.  
4. **Approval gate** before each merge batch.

### Batches

| Batch | Scope | Approval gate | Exit |
| :---: | :--- | :--- | :--- |
| **A** | P0.1–P0.5 connect + docs | **Approve A** | Phone shows Online to laptop agent |
| **B** | P0.6–P0.10 hierarchy + review + export | Approve B | Accept/reject + approved export from phone |
| **C** | P1.1–P1.4 lidar upload + labels | Approve C | One-room scan file → proposed → review → export |
| **D** | P2 as needed | Explicit | ARKit/QR only if C green |

### First-step proposed diffs (Batch A only — **not applied**)

#### A1 — `ws_client.rs`: configurable host

```diff
--- a/src/web/ws_client.rs
+++ b/src/web/ws_client.rs
@@
-    let url = format!("ws://127.0.0.1:8787/ws?token={}", token);
+    let host = get_saved_agent_host().unwrap_or_else(|| "127.0.0.1:8787".to_string());
+    let url = format!("ws://{}/ws?token={}", host, token);
```

Add:

```rust
pub fn get_saved_agent_host() -> Option<String> { /* localStorage "agent_host" */ }
pub fn save_agent_host(host: &str) { /* set_item agent_host */ }
```

#### A2 — `app.rs` Header: host input + touch styles

- Inputs: **Agent host** (`192.168.x.x:8787`) + **Token**  
- Stack vertically on narrow screens (`flex-wrap`, `min-height: 44px`)  
- Status: Online / Offline / last error  

#### A3 — `agent/server.rs`: print LAN hint

On boot after token:

```text
iPhone connect:
  1) Join same Wi-Fi/hotspot as this laptop
  2) PWA Agent host: <best-effort LAN IP>:8787
  3) Token: <root token>
  4) Serve PWA over http:// (not https) for ws:// cleartext
```

(Best-effort IP via `if_addrs` or `std`/`ipconfig` — keep optional dep minimal; even printing “run ipconfig/ifconfig” is OK for v1.)

#### A4 — Docs only: `docs/iphone-field-loop.md` (can land without code)

Hotspot steps, Safari constraints, success criteria (below).

**Batch B sketch (after A green):**

- `building.get` → `load_building_at` + JSON  
- `edit.apply` `{ "script": "set room X review_status=accepted\n" }` → text ingest + `persist_building`  
- PWA Review page: list proposed, buttons call `edit.apply`  
- Export button: `ifc.export` `{ "approved_only": true }`  
- Return LossReport summary lines on import RPCs  

---

## 4. Test & verification (one-room loop)

### Hardware setup

| Device | Role |
| :--- | :--- |
| Laptop | Pilot project dir; `cargo run --features agent --bin arx -- agent` (or current agent entry); same Wi-Fi/hotspot |
| iPhone | Safari (or Add to Home Screen); open **http://** PWA origin on LAN |

### Success criteria — Connect (Batch A)

- [ ] Agent Online badge on phone with host ≠ 127.0.0.1  
- [ ] Token wrong → clear error; token right → Online  
- [ ] Laptop shows WS activity / no crash  

### Success criteria — One-room capture/review (Batch B+C)

- [ ] Laptop (or phone upload): import small PLY/IFC into project  
- [ ] Phone loads hierarchy; sees `proposed` if LiDAR  
- [ ] Accept ≥1 / reject ≥1  
- [ ] LossReport or import warnings visible for last import  
- [ ] Phone triggers `approved_only` export; file exists on laptop  
- [ ] `building.yaml` validates on laptop CLI  

### Explicit non-pass

- Full building scan on phone CPU  
- ARKit live mesh in WASM  
- Agent as “official” without charter pin  
- Silent drop of LossReport  

---

## 5. Roadmap impact

| Before | After (this acceleration) |
| :--- | :--- |
| HB6 gated behind HB3–HB4 evidence | **HB6-accel** parallel **now** for **review + light capture**; full site still needs HB0–HB5 |
| Field Day 1 = CLI only | CLI remains pin path; **iPhone loop** is accelerated companion |
| Q6 default No | **Override: Yes for P0–P1 phone loop** (vision holder acceleration) |

L1 pin `v2.0.0-pilot.4` **unchanged** until a later pilot.5 if field needs the phone loop as supported install.

---

## 6. Approval checklist (you)

| Decision | Choice |
| :--- | :--- |
| Proceed Batch A (connect host + mobile UI + docs)? | [ ] yes / [ ] no |
| Proceed Batch B after A green? | [ ] yes / [ ] auto after A |
| Include P1 lidar RPC in first week? | [ ] yes / [ ] after B |
| ARKit (P2.1) in scope this month? | [ ] no (recommended) / [ ] research only |

**Batch A:** merged (host config, mobile header, agent hints, field status, `docs/iphone-field-loop.md`).  
**Next approval:** Batch B (review UI + export) after Pass A.
