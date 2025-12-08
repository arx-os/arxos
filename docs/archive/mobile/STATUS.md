# Mobile Client Status (November 2025)

- Native iOS (SwiftUI) and Android (Jetpack Compose) shells are **archived**. Retrieve them from `archive/mobile-clients/` or check out the `mobile-apps-final` tag.
- FFI bindings (`crates/arxos/src/mobile_ffi`, `include/arxos_mobile.h`, UniFFI scaffolding) were removed. The WASM PWA consumes Rust logic via the new `ar_integration::wasm` helpers and the desktop agent (`crates/arxos-agent`).
- Build scripts, Dockerfiles, and CI jobs targeting mobile have been deleted. The only supported surface is the terminal/TUI and the WASM PWA described in `WEB_PWA_PLAN.md` and `docs/web/DEVELOPMENT.md`.
- WebXR capture is not yet production-ready; we’ll reassess native scanning quarterly. If LiDAR-grade APIs stabilize, the archived clients can be restored from the tag `mobile-apps-final`.
- To restore the archive locally:
  - `git fetch origin --tags`
  - `git checkout mobile-apps-final`
  - or download the Mobile Clients Archive release zip
- See `archive/mobile-clients/README.md` for directory layout and support policy. No active maintenance is planned.

