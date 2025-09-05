# Feature Flags Overview

ArxOS uses compile-time feature flags to enforce an offline, RF-only posture and to gate optional functionality.

## Flags
- `rf_only` (default)
  - Enforces local-only operation; disables outbound network code paths.
  - Terminal shows an RF-only banner at startup.
- `internet_touchpoints`
  - Gates optional modules that interact with the internet (e.g., SMS onboarding).
  - Off by default.
- `mobile_offline`
  - Enables local device bindings (USB/BLE) via the `mobile_offline` binder.
  - No network permissions required; local link only.

## Usage
```
cargo build --features "std,rf_only"
cargo build --features "std,rf_only,mobile_offline"
# Optional (explicit):
cargo build --features "std,rf_only,internet_touchpoints"
```

See also:
- `docs/02-ARCHITECTURE.md`
- `docs/ONBOARDING_WORKFLOW.md`
