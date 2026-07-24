# File hand-off: external scan → agent (Decision 11 path A)

**Status:** Living operator note for the **thin v1 interface** (no native app required yet).  
**Authority:** [adr-native-capture-interface.md](./adr-native-capture-interface.md) · [adr-capture-model.md](./adr-capture-model.md)

ArxOS does not store dense clouds as product. You deliver a **file**; the **agent** (or CLI) runs structure assist, marks everything **`proposed`**, and writes **`building.yaml`**.

---

## What you need

| Piece | Role |
| :--- | :--- |
| Capture node | Laptop/Mini with pilot project + pin or `main` agent build |
| Scan file | PLY / LAS / LAZ / XYZ (meters preferred) |
| Optional | Future native iOS app — same RPC as below |

---

## Path 1 — CLI on the capture node (works today)

```bash
cd /path/to/pilot-project   # has building.yaml or arx init first
arx import lidar ./scan.ply --merge --light --voxel-size 0.25
arx validate
# Review proposed rooms; accept via text DSL when ready
# arx edit corrections.txt
arx export --format ifc --approved-only --output exports/approved.ifc
```

Copy scan to the laptop via AirDrop, USB, or Files share — **not** through a browser capture UI.

---

## Path 2 — Agent RPC `lidar.import` (native / tooling)

Agent must be running in the pilot project:

```bash
arx agent   # --features agent build
# ROOT TOKEN + ws://LAN:8787/ws?token=…
```

### Request (JSON-RPC params)

```json
{
  "filename": "room-scan.xyz",
  "data": "<base64 file bytes>",
  "merge": true,
  "light_mode": true,
  "voxel_size": 0.25,
  "provenance": {
    "client": "ios_native",
    "client_version": "0.1.0",
    "captured_at": "2026-07-24T16:00:00Z",
    "device_model": "iPhone15,2",
    "note": "RoomPlan mesh exported to XYZ"
  }
}
```

| Field | Required | Default |
| :--- | :---: | :--- |
| `filename` | yes | — |
| `data` | yes | base64 |
| `merge` | no | `true` |
| `light_mode` | no | `true` |
| `voxel_size` | no | `0.25` m |
| `provenance` | no | optional object |

### Response (shape)

```text
building_name, yaml_path, floors, rooms, equipment,
proposed_rooms, proposed_equipment, report_summary[], provenance?
```

Hard validation errors → **no** `building.yaml` write.

### Provenance stamped on SSOT

When `provenance` is present:

- Building metadata: `capture_client`, `capture_client_version`, `client_captured_at`, `capture_device_model`, …
- Rooms/equipment: `capture_client=…`
- Pipeline still sets `capture_source=lidar_file` and `review_status=proposed`

---

## Honesty reminders

| Do | Do not |
| :--- | :--- |
| Expect `proposed` rooms (including bbox fallback) | Treat auto structure as official |
| Read LossReport / `report_summary` | Skip validation to “make it fit” |
| Use `--approved-only` for official IFC after human accept | Write `building.yaml` from the phone |
| Prefer light mode on field laptops | Send multi-GB clouds over base64 without limits |

Limits: [resource-limits.md](./resource-limits.md) · Confidence tiers: [lidar-confidence.md](./lidar-confidence.md)

---

## Out of scope here

- Swift / Xcode native scaffold  
- Domain-only structure RPC (Decision 11 path B — deferred)  
- Browser capture (Decision 9)  
- Ownership / municipal flows  

**Related:** [field-handoff.md](./field-handoff.md) · [l1-supported-workflow.md](./l1-supported-workflow.md)
