# Agent ↔ client interface (versioned)

**Protocol version:** `1`  
**Status:** Living contract for peripheral clients (iOS companion, tooling)  
**Authority:** Decision 11 · Decision 12 · Decision 10  

This document is the **only** supported integration surface between **core** (`arx-os/arxos`) and **external clients** (especially `arx-os/arxos-ios`). Clients must not open or write `building.yaml` as SSOT.

---

## Roles

| Side | Repo | Responsibility |
| :--- | :--- | :--- |
| **Agent (host)** | `arxos` | Durable write: finalize → validate → `building.yaml`; Git; IFC export |
| **Client** | e.g. `arxos-ios` | Capture geometry / labels; call RPCs; show status |

---

## Transport

| Item | Spec |
| :--- | :--- |
| Protocol | JSON-RPC 2.0 over WebSocket |
| URL | `ws://<host>:8787/ws?token=<ROOT_TOKEN>` |
| Auth | Token query param; capability-scoped on agent |
| Also | `POST /rpc` exists; WS is primary for field |

Default agent bind: `0.0.0.0:8787` (LAN/hotspot).

---

## Methods used by field companion (v1)

| Method | Params (summary) | Purpose |
| :--- | :--- | :--- |
| `building.get` | `{}` | Read snapshot / counts |
| `building.validate` | `{}` | Validate SSOT without free-form write |
| `lidar.import` | `filename`, `data` (base64), `merge?`, `light_mode?`, `voxel_size?`, `provenance?` | Geometry file → proposed structure |
| `edit.apply` | `script` (text DSL) | Label / review_status / room-equip edits |
| `git.status` | `{}` | Dirty/commit state |
| `git.commit` | `message`, `stageAll?` (bool, prefer true) | Commit `building.yaml` (+ staged) |
| `ifc.export` | `filename?`, `approved_only?` | Export IFC to capture-node `exports/` |
| `capture.from_camera` | `frames[]` base64 JPEG | Optional evidence frames only (not LiDAR) |

### Provenance object (`lidar.import`)

```json
{
  "client": "ios_native",
  "client_version": "0.1.0",
  "captured_at": "2026-07-24T00:00:00Z",
  "device_model": "iPhone15,2",
  "note": "RoomPlan → XYZ"
}
```

Stamped on building metadata / rooms as `capture_client*` fields. Pipeline keeps `capture_source=lidar_file` and **`review_status=proposed`**.

---

## Rules clients must obey

1. **No direct durable store writes** — no client-authored `building.yaml` as SSOT.  
2. **Field structure is proposed** until human accept via `edit.apply`.  
3. **Geometry is input** — not a long-term product blob in the companion.  
4. **IFC for desktop** is produced on the **capture node** (`ifc.export` or CLI).  
5. **Protocol version:** if core breaks a method/param, bump this document’s version and tag companion release notes.

---

## Out of band

| Concern | Where |
| :--- | :--- |
| Compiler / TUI / IFC fidelity | Core only |
| App Store / signing / TestFlight | `arxos-ios` only |
| Horizon C / mainnet rewards | Frozen unless opened |

---

## Lab references

- Core operator: [native-file-handoff.md](./native-file-handoff.md)  
- Companion bootstrap: sibling repo `arxos-ios` (see Decision 12)  
- Design: [adr-native-capture-interface.md](./adr-native-capture-interface.md)
