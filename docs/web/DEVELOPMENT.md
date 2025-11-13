# ArxOS Web Development Guide

The PWA replaces the archived native shells and delivers the ArxOS experience through WebAssembly and a desktop companion agent. This guide documents the day-to-day workflow.

## Prerequisites

**Required:**
- Rust toolchain 1.70+ (`rustup`) with `wasm32-unknown-unknown` target
  ```bash
  rustup target add wasm32-unknown-unknown
  ```
- `wasm-pack` (`cargo install wasm-pack --locked`)
- Node.js 18+ (20+ recommended) with npm
- Git 2.30+

**Optional:**
- `cargo install cargo-watch` for auto-rebuilds
- VS Code with extensions: ESLint, Prettier, Rust Analyzer, Tailwind CSS IntelliSense

**Verify Installation:**
```bash
rustc --version    # Should be 1.70+
node --version     # Should be 18+
wasm-pack --version
```

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

**Build & Development:**
- `npm run dev` — start Vite development server (localhost:5173)
- `npm run build` — production bundle (published to GitHub Pages / IPFS)
- `npm run preview` — serve the production build locally
- `npm run build:wasm` — rebuild WASM bindings from Rust

**Type Checking & Linting:**
- `npm run typecheck` — TypeScript checks (requires the WASM package above)
- `npm run lint` — run ESLint on source code
- `npm run lint:fix` — auto-fix ESLint issues
- `npm run format` — format code with Prettier
- `npm run format:check` — check code formatting without changes

**Testing:**
- `npm run test` — run unit tests (Vitest, watch mode)
- `npm run test:unit` — run unit tests (same as `test`)
- `npm run test:unit -- --run` — run unit tests once (no watch)
- `npm run test:coverage` — generate coverage report
- `npm run test:e2e` — run Playwright E2E tests

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

## Command-Centric Shell (M02)

ArxOS PWA provides a keyboard-driven command interface powered by WASM command metadata, mirroring the terminal-first experience in the browser.

### Command Palette

- **Trigger:** Press `Cmd/Ctrl+K` to open the command palette modal
- **Fuzzy Search:** Uses fuse.js for weighted search across command titles, descriptions, commands, tags, and categories
- **Keyboard Navigation:**
  - `↑/↓` arrow keys to navigate through filtered results
  - `Enter` to execute the selected command
  - `Esc` to close the palette
- **Command History:** Recently used commands appear at the top when the palette opens (sorted by last used timestamp)
- **Command Availability:** Commands display availability badges (CLI, PWA, Agent) to indicate where they can run

### Command Console

- **Location:** Fixed panel at the bottom of the screen (resizable by dragging the top edge)
- **Output Display:** Shows command execution logs with timestamps, log levels (INFO, WARN, ERROR, OK), and colored formatting
- **Auto-scroll:** Automatically scrolls to the latest output as commands execute
- **Clear Function:** Clear button to remove all console history
- **Log Levels:**
  - `INFO` (slate) - general information and execution status
  - `WARN` (yellow) - warnings about unavailable features
  - `ERROR` (red) - command failures and errors
  - `OK` (green) - successful command output

### Command Execution

- **Current Commands:**
  - `version` - Display ArxOS WASM version (2.0.0)
  - `help` - Show available commands and usage
  - `clear` - Clear console output
  - Other commands return mock output with M04 agent message
- **Execution Pipeline:**
  - Commands are parsed and routed through `commandExecutor.ts`
  - Execution state tracked (idle → running → complete/error)
  - Results logged to console with duration measurement
- **Future (M04):** Agent commands will route through WebSocket to desktop agent for Git, IFC, and file operations

### Architecture

```
src/
├── components/
│   ├── CommandPalette.tsx    # Modal with fuzzy search + keyboard nav
│   └── CommandConsole.tsx     # Resizable bottom panel for output
├── state/
│   ├── commandPalette.ts      # Command catalog + search state
│   └── commandExecution.ts    # Execution logs + state tracking
└── lib/
    └── commandExecutor.ts     # Command parsing + execution routing
```

### Testing

- **Unit Tests:**
  - `commandExecutor.test.ts` - command execution, parsing, error handling
  - `commandExecution.test.ts` - log management, state updates
  - `commandPaletteStore.test.tsx` - search filtering, history tracking
- **E2E Tests:**
  - `command-workflow.spec.ts` - full workflow (open → search → navigate → execute → verify console)
  - Keyboard navigation tests (arrow keys, Enter, Escape)
  - Console clear functionality tests

### Dependencies

- **fuse.js** - Fuzzy search with weighted keys and configurable threshold
- **nanoid** - Unique log entry IDs
- **zustand** - State management for palette and execution stores

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

## Code Style & Quality

### ESLint Configuration

ESLint is configured in `.eslintrc.cjs` with:
- `eslint:recommended` + `@typescript-eslint/recommended`
- React best practices (`eslint-plugin-react`, `eslint-plugin-react-hooks`)
- Warns on unused variables (except `_` prefixed)
- Warns on `any` types
- Warns on console statements (except `warn` and `error`)

### Prettier Configuration

Prettier is configured in `.prettierrc.json` with:
- 2 spaces indentation
- Semicolons required
- Double quotes
- 100 character line width
- ES5 trailing commas

### Pre-commit Workflow

Before committing, run:
```bash
npm run lint && npm run format && npm run typecheck && npm run test:unit -- --run
```

### Conventional Commits

Follow [Conventional Commits](https://www.conventionalcommits.org/) format:
- `feat:` — New feature
- `fix:` — Bug fix
- `docs:` — Documentation changes
- `style:` — Code style changes (formatting)
- `refactor:` — Code refactoring
- `test:` — Adding or updating tests
- `chore:` — Build process or auxiliary tool changes

## Testing

### Unit Tests (Vitest)

Tests are located in `src/__tests__/` and use Vitest with jsdom environment.

```bash
npm run test:unit          # Watch mode
npm run test:unit -- --run # Single run
npm run test:coverage      # With coverage
```

**Example test:**
```typescript
import { describe, it, expect } from "vitest";
import { initWasm } from "../lib/wasm";

describe("WASM Integration", () => {
  it("should load successfully", async () => {
    const module = await initWasm();
    expect(module).toBeDefined();
  });
});
```

### E2E Tests (Playwright)

End-to-end tests are in `tests/e2e/` and use Playwright.

```bash
npm run test:e2e             # Run all E2E tests
npx playwright test --ui     # Interactive UI mode
npx playwright test --debug  # Debug mode
```

### Test Coverage

Coverage reports are generated in `coverage/` directory. Aim for 80%+ coverage on new code.

## WASM Development

### Adding New WASM Exports

1. Add Rust function in `/crates/arxos-wasm/src/lib.rs`:
   ```rust
   #[wasm_bindgen]
   pub fn my_function(input: &str) -> Result<String, JsValue> {
       // Implementation
   }
   ```

2. Update TypeScript types in `/pwa/src/types/arxos-wasm.d.ts`:
   ```typescript
   export function my_function(input: string): string;
   ```

3. Rebuild WASM:
   ```bash
   npm run build:wasm
   ```

4. Update [WASM_API.md](./WASM_API.md) documentation

### WASM Testing

Run Rust tests for WASM:
```bash
cd crates/arxos-wasm
wasm-pack test --headless --chrome
```

## Troubleshooting

**TypeScript cannot find `arxos_wasm.js`**
- Solution: Run `npm run build:wasm` before `npm run typecheck`

**Agent authentication failures**
- Solution: Ensure the DID token matches the agent console output (case sensitive)

**WebXR unsupported**
- Solution: Verify browser version and enable experimental flags
  - Chrome: `chrome://flags/#webxr-incubations`
  - Safari: Developer Settings → WebXR Device API

**Port 5173 already in use**
- Solution: `npx kill-port 5173` or use `npm run dev -- --port 5174`

**WASM build fails**
- Solution: Update Rust toolchain with `rustup update` and re-run `npm run build:wasm`

**Tests failing after dependency update**
- Solution: Clear cache with `rm -rf node_modules package-lock.json && npm install`

**ESLint errors on existing code**
- Solution: Run `npm run lint:fix` to auto-fix, then manually fix remaining issues

## Contributing

1. Fork the repository (external contributors)
2. Create a feature branch from `main`
3. Make your changes following the style guide
4. Add tests for new functionality
5. Run full test suite:
   ```bash
   npm run lint
   npm run format
   npm run typecheck
   npm run test:unit -- --run
   npm run build
   ```
6. Commit with conventional commit message
7. Open a Pull Request targeting `main`

## Resources

- **Architecture:** [../core/ARCHITECTURE.md](../core/ARCHITECTURE.md)
- **WASM API:** [WASM_API.md](./WASM_API.md)
- **Roadmap:** [../../PWA_ROADMAP.md](../../PWA_ROADMAP.md)
- **User Guide:** [../core/USER_GUIDE.md](../core/USER_GUIDE.md)

---

Happy building! Update this guide as new agent capabilities or PWA surfaces land.
