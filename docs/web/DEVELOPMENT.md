# ArxOS Web Development Guide

The PWA replaces the archived native shells and delivers the ArxOS experience through WebAssembly and a desktop companion agent. This guide documents the day-to-day workflow.

## Prerequisites

- Rust toolchain (`rustup`)
- `wasm-pack` (`cargo install wasm-pack --locked`)
- Node.js 20+ with npm
- Optional: `cargo install cargo-watch` for auto-rebuilds

## Building the WASM Package

```bash
# From repo root
wasm-pack build crates/arxos-wasm --target web --out-dir pkg
```

The output lives in `crates/arxos-wasm/pkg/` and is consumed by Vite via the `@arxos-wasm` import alias. Re-run this command before running `npm run typecheck` so TypeScript can resolve the generated bindings.

## Running the PWA

```bash
cd pwa
npm install
npm run dev
```

When the dev server starts you can open `http://localhost:5173` to use the command palette, Floor Plan Studio, collaboration queue, and AR preview components.

### Helpful Scripts

- `npm run build` — production bundle (published to GitHub Pages / IPFS)
- `npm run typecheck` — TypeScript checks (requires the WASM package above)
- `npm run preview` — serve the production build locally

## Desktop Agent (Loopback Bridge)

`crates/arxos-agent` exposes Git and filesystem primitives over a secure WebSocket.

```bash
cargo run -p arxos-agent -- --host 127.0.0.1 --port 8787 --token did:key:zexample
```

- Tokens **must** be DID:key strings. The agent will generate an ephemeral token if one is not provided.
- The PWA stores the token locally and appends it to the WebSocket query string (`/ws?token=did:key:...`).
- Current capabilities:
  - Health + capability discovery (`/health`, `/capabilities`)
  - WebSocket `ping`, `version`, `capabilities` actions
  - Offline collaboration queue flush (prototype) — messages are acknowledged via `ping` responses
- Planned: Git status/commit plumbing, IFC import/export, file streaming.

## Offline & Collaboration Flow

1. Users compose messages in the collaboration panel. Messages are queued in IndexedDB via Zustand persistence.
2. When the agent connection succeeds, the queue flushes over the DID-authenticated WebSocket.
3. Failures mark the message as `error` and leave it in history for manual retry.

## AR Preview

- The AR preview card checks `navigator.xr.isSessionSupported('immersive-ar')`.
- When available, users can trigger a short-lived session to confirm browser support.
- WebXR overlays consume the same `WasmArScanData` structures used by the Floor Plan Studio.
- Safari (iOS 17+) and Chrome (Android) require experimental flags; browser guidance is shown in the UI.

## Deployment

- **Primary:** GitHub Pages builds via `.github/workflows/pwa.yml` (`npm run build`).
- **Mirror:** IPFS snapshot published alongside releases (`ipfs add pwa/dist`).
- Service worker (`public/sw.js`) caches `index.html`, WASM bundles, and command metadata for offline launch.

## Repository Layout

```
arxos/
├─ crates/
│  ├─ arxos-wasm/      # wasm-bindgen bindings + wasm tests
│  └─ arxos-agent/     # desktop companion (loopback WebSocket)
├─ pwa/                # React/Zustand PWA shell
│  └─ src/
│     ├─ components/   # Command palette, floor studio, collaboration, AR preview
│     ├─ lib/          # WASM loader + agent helpers
│     └─ state/        # Zustand stores
└─ docs/web/           # Web-specific documentation (this file)
```

## Troubleshooting

- **TypeScript cannot find `arxos_wasm.js`** — re-run `wasm-pack build` before `npm run typecheck`.
- **Agent authentication failures** — ensure the DID token matches the agent console output; tokens are case sensitive.
- **WebXR unsupported** — verify browser version and enable experimental flags (`chrome://flags/#webxr-incubations` or Safari Developer Settings).

Happy building! Update this guide as new agent capabilities or PWA surfaces land.
