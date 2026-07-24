# ArxOS iOS field client (terminal)

**Peripheral only.** Durable writes go through the **laptop agent** → `building.yaml` + Git + IFC export.  
Decisions 9–11 apply: no browser capture; proposed-first; geometry is disposable input.

## Why Xcode?

We **write and version the app in this repo**. Apple still requires **Xcode** (or a CI Mac with the iOS SDK) to:

- Compile for iPhone / Simulator  
- Sign and install on your device  
- Use camera / local network entitlements  

**Command Line Tools alone are not enough** for iOS builds. If `xcodebuild` says it needs Xcode:

```bash
sudo xcode-select -s /Applications/Xcode.app/Contents/Developer
sudo xcodebuild -license accept   # once
```

Then open the project (or build from CLI).

## Lab loop (definition of done)

### Laptop

```bash
cd /path/to/arxos
cargo build --features agent --bin arx

mkdir -p ~/arx-pilots/ios-lab && cd ~/arx-pilots/ios-lab
/path/to/arxos/target/debug/arx init --name "iOS Lab"
/path/to/arxos/target/debug/arx agent
# Copy: ROOT TOKEN and LAN IP:8787 (Simulator → use Mac LAN IP or 127.0.0.1 with care)
```

Simulator note: `127.0.0.1` on the Simulator is the **Simulator itself**, not your Mac agent. Prefer your Mac’s LAN IP (e.g. `192.168.x.x:8787`) for both device and Simulator, with agent bound to `0.0.0.0:8787`.

### Phone / Simulator

1. Open `ios/ArxOS/ArxOS.xcodeproj` in Xcode  
2. Select your Team for signing (Signing & Capabilities)  
3. Run on Simulator or device  
4. Paste **Agent host** + **ROOT TOKEN** → **Connect**  
5. **Scan file** → pick PLY/XYZ (AirDrop scan into Files, or share from a scan app)  
6. **Label** equipment on a room name  
7. **Accept room** (optional for full IFC visibility of accepted entities)  
8. **Commit** → **Export IFC**  

### Desktop verification

```bash
cd ~/arx-pilots/ios-lab
arx history          # or: git log --oneline
ls exports/
# Open exports/*.ifc in any IFC viewer
```

## App commands

| UI | Agent RPC |
| :--- | :--- |
| Building | `building.get` |
| Validate | `building.validate` |
| Scan file | `lidar.import` + provenance |
| Label | `edit.apply` (add equipment / room) |
| Accept room | `edit.apply` (`review_status=accepted`) |
| Commit | `git.commit` (`stageAll: true`) |
| Export IFC | `ifc.export` → `exports/` on laptop |

## Honesty

- File scan structure is **proposed** (including bbox fallback).  
- Official pilot IFC still prefers human accept + `--approved-only` when ready.  
- RoomPlan live mesh in-app is a **later** enhancement; v1 is Decision 11 **file hand-off**.

## Related

- [docs/adr-native-capture-interface.md](../docs/adr-native-capture-interface.md)  
- [docs/native-file-handoff.md](../docs/native-file-handoff.md)  
- [docs/ios-lab-loop.md](../docs/ios-lab-loop.md)  
