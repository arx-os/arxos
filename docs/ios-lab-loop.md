# iOS lab loop — system acceptance (pre-field)

**Goal:** Prove host + agent + iOS client end-to-end **in lab** before real-building field testing.  
**Not** a district L1 pilot; not Horizon C.

## Prerequisites

- Laptop: Rust, `cargo build --features agent --bin arx`  
- iPhone or Simulator: Xcode project `ios/ArxOS/ArxOS.xcodeproj`  
- Same Wi‑Fi/hotspot (device) or Mac LAN IP (Simulator)

## Steps

1. **Laptop pilot dir**
   ```bash
   mkdir -p ~/arx-pilots/ios-lab && cd ~/arx-pilots/ios-lab
   arx init --name "iOS Lab"
   arx agent
   ```
2. **Copy** ROOT TOKEN + `IP:8787`  
3. **Run iOS app** → Connect  
4. **Scan file** with a small XYZ/PLY (or export from a scan app)  
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

[ios/README.md](../ios/README.md) · [native-file-handoff.md](./native-file-handoff.md) · Decision 11
