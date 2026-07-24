# iOS lab loop — system acceptance (pre-field)

**Goal:** Prove **core agent** + **iOS companion** end-to-end **in lab** before real-building field testing.  
**Not** a district L1 pilot; not Horizon C.

## Repositories (Decision 12)

| Repo | Path / remote |
| :--- | :--- |
| **Core** | this repo — `arx-os/arxos` |
| **iOS companion** | [arx-os/ios](https://github.com/arx-os/ios) (clone next to core) |

Interface: [agent-client-interface.md](./agent-client-interface.md) (protocol v1).

## Prerequisites

- Laptop: Rust, `cargo build --features agent --bin arx` (core)  
- iPhone or Simulator: **Xcode** project from **`ios`**  
- Same Wi‑Fi/hotspot (device) or Mac LAN IP (Simulator)

## Steps

1. **Laptop pilot dir (core)**
   ```bash
   mkdir -p ~/arx-pilots/ios-lab && cd ~/arx-pilots/ios-lab
   arx init --name "iOS Lab"
   arx agent
   ```
2. **Copy** ROOT TOKEN + `IP:8787`  
3. **iOS companion** ([arx-os/ios](https://github.com/arx-os/ios)): open `ArxOS/ArxOS.xcodeproj` → Run → Connect
4. **Scan file** with XYZ/PLY (or fixture from companion `fixtures/lab-room.xyz`)  
5. **Label** → **Accept room** (optional) → **Commit** → **Export IFC**  
6. **Laptop:** `git log -1` and open `exports/*.ifc`

## Pass criteria

| Check | Pass |
| :--- | :---: |
| Connect shows Online | [ ] |
| lidar.import returns rooms ≥ 1, proposed_rooms ≥ 1 | [ ] |
| Commit returns commit_id | [ ] |
| IFC file exists under pilot `exports/` | [ ] |
| Desktop IFC viewer opens the file | [ ] |

## Related

[agent-client-interface.md](./agent-client-interface.md) · [native-file-handoff.md](./native-file-handoff.md) · Decision 11–12
