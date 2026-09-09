# iOS field loop (RoomPlan → commit → Mac CLI)

30-day field test against the store contract: [field-test-runbook.md](field-test-runbook.md). PR review gates: [store-contract-pr-checklist.md](store-contract-pr-checklist.md).

## Success path

1. `./ios/scripts/build-ios-lib.sh` → `Vendor/libarxos_core.a` (aarch64-apple-ios)
2. Open `ios/ArxosApp/ArxosApp.xcodeproj`, sign, run on LiDAR iPhone iOS 17+
3. Init building → Start RoomPlan → Stop → ingest + auto-commit
4. Force-quit → reopen restores last building id (UserDefaults)
5. Export store / Files app → Mac `arx --store …`

## Implementation notes

- Xcode single target compiles App + Core + generated UniFFI sources together
  (`import ArxosCore` is `#if canImport` so SPM multi-module still works).
- RoomPlan pauses ARCaptureView (`isRoomPlanActive`) to avoid dual camera sessions.
- `ingestRoomPlan(..., autoCommit: true)` commits immediately after stage.
- Store: `Documents/arxos-store` with file sharing enabled.
- RoomPlan floors require iOS 17 API; deployment target is 17.0.
- No dense point cloud from RoomPlan mesh in this pass (surfaces + objects only).

## Build environment

Must use full Xcode SDK:

```bash
export DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer
```

Command Line Tools alone cannot find `iphoneos` SDK.
