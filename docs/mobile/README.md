# Mobile Documentation (Archived)

Native mobile development for ArxOS is on hold while we build the WASM-powered PWA.

## Current Status

- ✅ Active surface: Terminal/TUI and WebAssembly PWA (`WEB_PWA_PLAN.md`)
- ⚠️ Archived surface: Native iOS & Android clients (see `docs/mobile/STATUS.md`)
- 🔄 Mobile scanning revisit: Quarterly review of WebXR capabilities

## Legacy References

The documents in this directory are preserved for historical purposes. They describe the old FFI pipeline, build steps, and CI/CD workflows. Use them only if you need to spin up the archived clients from the `mobile-apps-final` tag.

- [STATUS.md](./STATUS.md) – archive pointers and revival criteria
- [MOBILE_FFI_INTEGRATION.md](./MOBILE_FFI_INTEGRATION.md) – legacy FFI guide (no longer maintained)
- [IOS_FFI_STATUS.md](./IOS_FFI_STATUS.md) – historical integration notes
- [ANDROID.md](./ANDROID.md) – previous Android build checklist
- [MOBILE_CI_CD.md](./MOBILE_CI_CD.md) – deprecated pipelines
- [MOBILE_SIGNUP_WORKFLOW.md](./MOBILE_SIGNUP_WORKFLOW.md) – historical UX plan

For the roadmap ahead, focus on `WEB_PWA_PLAN.md` and the new `crates/arxos-wasm` workstream.

