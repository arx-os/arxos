# Archived Mobile FFI Headers

The native mobile bindings were retired in November 2025 as part of the WASM PWA transition. No active header files are shipped in this directory anymore.

## Where Did The Headers Go?

- The final `arxos_mobile.h` and related UniFFI scaffolding live in the `archive/mobile-clients` bundle referenced from `docs/mobile/STATUS.md`.
- Use that archive only if you need to reproduce historic builds; the maintained path forward is the WebAssembly PWA (`WEB_PWA_PLAN.md`).

## Current Status

- ✅ WASM-first workflow (browser + optional desktop agent)
- ⚠️ Native Swift/Kotlin shells **paused** and no longer built in this repository
- 🔄 WebXR progress reviewed quarterly to decide whether native capture should be revived

## Related Documentation

- `docs/mobile/STATUS.md` – mobile archive notes
- `docs/CHANGELOG_NOVEMBER_2025.md` – announcement of the strategy change
- `WEB_PWA_PLAN.md` – updated architecture plan
