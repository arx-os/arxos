# Agent ↔ client interface (versioned)

**Protocol version:** `1` (additive methods; no breaking change)  
**Status:** Living contract — **lab companion connected** (2026-07-24)  
**Authority:** Decision 11 · Decision 12 · Decision 10 · [field-language.md](field-language.md)

This document is the **only** supported integration surface between **core** (`arx-os/arxos`) and **external clients** (especially `arx-os/ios`). Clients must not open or write `building.yaml` as SSOT.

---

## Roles

| Side | Repo | Responsibility |
| :--- | :--- | :--- |
| **Agent (host)** | `arxos` | Durable write: finalize → validate → `building.yaml`; Git; IFC export |
| **Client** | e.g. `ios` | Capture geometry / labels; call RPCs; show status |

---

## Transport

| Item | Spec | Lab note (2026-07) |
| :--- | :--- | :--- |
| **HTTP JSON-RPC** | `POST http://<host>:8787/rpc?token=<ROOT_TOKEN>` | **Recommended for iOS lab** (stable request/response) |
| **WebSocket** | `ws://<host>:8787/ws?token=<ROOT_TOKEN>` | Supported; URLSession WS was flaky on iOS — use HTTP for now |
| Auth | Prefer `Authorization: Bearer <token>`; `?token=` also accepted | ROOT TOKEN printed once at `arx agent` start — never broadcast |
| Body | JSON-RPC 2.0 (`jsonrpc`, `id`, `method`, `params`) | |

Default agent bind: `0.0.0.0:8787` (LAN/hotspot). Override with `ARX_AGENT_BIND` / `ARX_AGENT_PORT` (e.g. `127.0.0.1` for local-only).  
UDP LAN discovery is **off** by default; set `ARX_AGENT_DISCOVERY=1` only on trusted networks (broadcasts a **non-secret** peer id — never the root token).

**Simulator:** host `127.0.0.1:8787`.  
**Physical device:** laptop LAN IP `:8787`, same Wi‑Fi, Local Network permission.

Discover capabilities:

```json
{ "jsonrpc": "2.0", "id": 1, "method": "session.hello", "params": {} }
```

---

## Methods used by field companion (v1)

### Reachability / meta

| Method | Params | Purpose |
| :--- | :--- | :--- |
| `session.hello` | `{}` | Protocol version, transports, method list |

### Read / validate

| Method | Params | Purpose |
| :--- | :--- | :--- |
| `building.get` | `{}` | Read snapshot / counts |
| `building.validate` | `{}` | Validate SSOT without free-form write |
| `git.status` | `{}` | Dirty/commit state |

### Capture (Decision 11 path A)

| Method | Params | Purpose |
| :--- | :--- | :--- |
| `lidar.import` | `filename`, `data` (base64), `merge?`, `light_mode?`, `voxel_size?`, `provenance?` | Geometry file → **proposed** structure |

### Structured field language (**prefer for clients**)

| Method | Params | Purpose |
| :--- | :--- | :--- |
| `field.label` | `room` (string), `equipment` (string) | Proposed equipment; create proposed room if missing |
| `field.accept_room` | `room` (string) | Accept room for approved export path |

### Power / escape hatch

| Method | Params | Purpose |
| :--- | :--- | :--- |
| `edit.apply` | `script` (text DSL) | Raw DSL; client must quote correctly — see [field-language.md](field-language.md) |

### Commit / export (capture node)

| Method | Params | Purpose |
| :--- | :--- | :--- |
| `git.commit` | `message`, `stageAll?` (bool) | Commit `building.yaml` (+ staged) |
| `ifc.export` | `filename?`, `approved_only?` | Export IFC to capture-node `exports/` |
| `capture.from_camera` | `frames[]` base64 JPEG | Optional evidence frames only (**not** LiDAR) |

### Provenance object (`lidar.import`)

```json
{
  "client": "ios_native",
  "client_version": "0.1.0",
  "captured_at": "2026-07-24T00:00:00Z",
  "device_model": "iPhone15,2",
  "note": "file hand-off Decision 11 path A"
}
```

Stamped on building metadata / rooms as `capture_client*` fields. Pipeline keeps `capture_source=lidar_file` and **`review_status=proposed`**.

---

## Companion implementation status (honest)

| Capability | Status |
| :--- | :--- |
| Connect + auth + building/git RPC | **Lab working** (HTTP `/rpc`) |
| File scan upload (`lidar.import`) | Implemented in companion; full E2E pass not claimed |
| Structured label / accept | **Core `field.*` landed**; companion should call these |
| Commit with status confirm | Companion UX |
| Live camera / RoomPlan view | **Not started** |
| Browser / PWA capture | **Abandoned** (Decision 9) |

---

## Rules clients must obey

1. **No direct durable store writes** — no client-authored `building.yaml` as SSOT.  
2. **Field structure is proposed** until human accept (`field.accept_room` or `edit.apply`).  
3. **Geometry is input** — not a long-term product blob in the companion.  
4. **IFC for desktop** is produced on the **capture node** (`ifc.export` or CLI).  
5. **Prefer `field.*`** over free-form scripts from mobile.  
6. **Protocol version:** breaking method/param changes bump this document and companion release notes.

---

## Out of band

| Concern | Where |
| :--- | :--- |
| Compiler / TUI / IFC fidelity | Core only |
| App Store / signing / TestFlight | `ios` only |
| Horizon C / mainnet rewards | Frozen unless opened |

---

## Lab references

- Field language: [field-language.md](field-language.md)  
- Operator file hand-off: [native-file-handoff.md](native-file-handoff.md)  
- Lab loop: [ios-lab-loop.md](ios-lab-loop.md)  
- Companion repo: [arx-os/ios](https://github.com/arx-os/ios) (Decision 12)  
- Design: [adr-native-capture-interface.md](../adr/native-capture-interface.md)
