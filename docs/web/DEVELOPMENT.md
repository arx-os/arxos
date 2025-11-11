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

When the dev server starts you can open `http://localhost:5173` to use the command palette, Floor Plan Studio, collaboration queue, Git workspace panel, IFC import/export panel, and AR preview components.

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
  - WebSocket actions: `ping`, `version`, `capabilities`
  - Git automation: `git.status`, `git.diff`, `git.commit` (DID-key attributed)
  - IFC workflows: `ifc.import` (base64 upload → YAML) and `ifc.export` (full/delta IFC back to browser)
  - Auth controls: `auth.rotate` to refresh DID tokens, `auth.negotiate` to scope capabilities per session
  - Secure file access: `files.read` with repository-scoped path safety
- Collaboration bridge: `collab.config.get|set` to persist GitHub targets and `collab.sync` to post queue items as
  issue/PR comments
- Planned: IFC import/export streaming, file write APIs, token rotation & structured logging.

### GitHub Comment Sync & Release Automation

- Provide a personal access token (PAT) with `repo` scope via `ARXOS_GITHUB_TOKEN` before launching the agent.
- Configure the target repository/issue from the PWA collaboration panel. Settings are written to
  `~/.config/arxos/collab.toml` (override with `ARXOS_AGENT_CONFIG_DIR`).
- Successful syncs attach the GitHub comment URL to each message; failures stay in history with a retry option.

## Offline & Collaboration Flow

1. Users compose messages in the collaboration panel. Messages are queued in IndexedDB via Zustand persistence.
2. When the agent connection succeeds, the queue flushes to GitHub (issue/PR comments) through the
   `collab.sync` action.
3. Successes include a deep link to the posted comment. Failures mark the message as `error`, capture the agent’s
   error message, and surface a retry button.

## AR Preview & WebXR Pilot

- The AR preview card checks `navigator.xr.isSessionSupported('immersive-ar')`.
- When available, users can preload a demo overlay (`/offline-demo/ar-overlay.json`) and trigger a short-lived session to confirm browser support.
- Demo overlays consume the same `WasmArScanData` structures used by the Floor Plan Studio; anchors stream via the desktop agent in the pilot setup.
- Safari (iOS 17+) and Chrome (Android) require experimental flags; browser guidance is shown in the UI.
- Phase 5 focuses on streamed overlays—no in-browser scanning yet. Known issues (fetched with the demo payload) are surfaced to the user, which helps QA track Chrome/Safari regressions.

## Deployment

- **Primary:** GitHub Pages builds via `.github/workflows/pwa.yml`. On merges to `main` the workflow:
  1. Runs `wasm-pack build`, `cargo test -p arx-command-catalog`, `npm run typecheck`, `npm run test:unit -- --run`, and `npm run test:e2e`.
  2. Uploads `pwa/dist` as the Pages artifact and deploys through `actions/deploy-pages@v4`.
- **Mirror:** The same job packs `pwa/dist.car` using `ipfs-car pack` and uploads it as a CI artifact for pinning to IPFS.
- Release automation (`node scripts/release.mjs --version <x.y.z>`) performs Cargo/Node version bumps, regenerates `CHANGELOG.md`, rebuilds the WASM bindings, and creates annotated `v<version>` and `wasm/v<version>` tags. Use `--dry-run` to preview changes.
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
