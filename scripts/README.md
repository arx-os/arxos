# ArxOS Build Scripts

This directory now hosts scripts aligned with the Rust-first + WASM PWA direction. Native mobile build tooling has been archived along with the `/ios` and `/android` projects.

## Current Scripts

- `build-workspace.sh` / `build-workspace.bat` – build the full Rust workspace for CLI/TUI and core services.
- `setup-security-hooks.sh` – install and run pre-commit hooks.
- `setup-android-cargo.sh` – retained for legacy contributors who need archived Android builds; see the note below.

If you are looking for the removed iOS/Android builders (`build-mobile-ios.sh`, `build-mobile-android.sh`, `build-android-mac.sh`) or `link-framework.sh`, they now live in the mobile archive referenced from `docs/mobile/STATUS.md`.

## WASM-First Direction

ArxOS is transitioning to a single Progressive Web App powered by WebAssembly. The new `crates/arxos-wasm` (in progress) will expose the same Rust logic the native apps used, but directly in the browser. Follow the architecture and roadmap in `WEB_PWA_PLAN.md` for implementation details.

## Legacy Mobile Tooling

- The archived scripts remain available for emergency builds; clone the mobile archive repository or check your local `archive/mobile-clients` folder if you kept a copy.
- `setup-android-cargo.sh` is still provided to help developers reproduce historic Android builds against the archive. Expect it to be removed once the WebXR capture story reaches parity.

## Adding New Scripts

1. Prefer Rust-based tooling or WASM-friendly automation.
2. Use `set -euo pipefail` in shell scripts.
3. Document prerequisites in the script header and update this README.
4. Keep scripts idempotent and safe to run repeatedly.

## Related Documentation

- `WEB_PWA_PLAN.md` – WASM PWA architecture overview.
- `docs/CHANGELOG_NOVEMBER_2025.md` – Contains the pivot announcement and archive links.
- `docs/mobile/STATUS.md` – Status of the archived native apps and how to retrieve old tooling.

