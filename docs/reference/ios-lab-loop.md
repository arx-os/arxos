# iOS lab loop — system acceptance (pre-field)

**Goal:** Prove **core agent** + **iOS companion** end-to-end **in lab** before real-building field testing.  
**Not** a district L1 pilot; not Horizon C.  
**Updated:** 2026-07-24

## Status snapshot

| Item | State |
| :--- | :--- |
| Agent + HTTP `/rpc` connect | **Working in lab** |
| ROOT TOKEN from `arx agent` stdout | Required (not in app bundle) |
| Companion UI | Terminal shell (no camera / RoomPlan yet) |
| Capture | Decision 11 path A — **file** PLY/XYZ/LAS only |
| Structured labels | Prefer agent `field.label` / `field.accept_room` |
| Full scan→commit→IFC green checklist | **In progress** (connect alone is not pass) |

## Repositories (Decision 12)

| Repo | Path / remote |
| :--- | :--- |
| **Core** | this repo — `arx-os/arxos` |
| **iOS companion** | [arx-os/ios](https://github.com/arx-os/ios) (clone next to core) |

Interface: [agent-client-interface.md](agent-client-interface.md) (protocol v1) · language: [field-language.md](field-language.md)

## Prerequisites

- Laptop: `cargo build --features agent --bin arx` (core)  
- iPhone or Simulator: **Xcode** project from **`ios`**  
- Same Wi‑Fi/hotspot (device) or **`127.0.0.1`** (Simulator)

## Steps

1. **Laptop pilot dir (core)**
   ```bash
   mkdir -p ~/arx-pilots/ios-lab && cd ~/arx-pilots/ios-lab
   arx init --name "iOS Lab"   # if empty
   cargo run --features agent --bin arx -- agent
   # or: /path/to/arx agent
   ```
2. **Leave that Terminal open.** Copy **ROOT TOKEN** + host:
   - Simulator: `127.0.0.1:8787`
   - Device: `LAN_IP:8787` (e.g. from agent connect card)
3. **iOS companion:** open `ArxOS/ArxOS.xcodeproj` → select a **Simulator** (not “Any iOS Device”) → Run → paste host/token → **Connect**
4. **Scan file** with XYZ/PLY (companion `fixtures/lab-room.xyz` or AirDrop)  
5. **Label** → **Accept room** (optional) → **Commit** (confirm banner) → **Export IFC**  
6. **Laptop:** `git log -1` and open `exports/*.ifc`

### Stop lab agent

```bash
# free port 8787 (example)
lsof -nP -iTCP:8787 -sTCP:LISTEN -t | xargs kill
```

## Pass criteria

| Check | Pass |
| :--- | :---: |
| Connect shows Online (building.get or git.status) | [x] lab 2026-07-24 |
| `session.hello` returns protocol_version ≥ 1 | [ ] |
| lidar.import returns rooms ≥ 1, proposed_rooms ≥ 1 | [ ] |
| field.label / Label button succeeds with multi-word names | [ ] |
| Commit returns commit_id | [ ] |
| IFC file exists under pilot `exports/` | [ ] |
| Desktop IFC viewer opens the file | [ ] |

## Explicit non-goals for this loop

- No RoomPlan / live camera UI yet  
- No browser capture  
- No Horizon C / rewards  
- Not “field ready” until pass criteria above + real-building evidence process

## Related

[agent-client-interface.md](agent-client-interface.md) · [field-language.md](field-language.md) · [native-file-handoff.md](native-file-handoff.md) · Decision 11–12
