# ArxOS WASM PWA Architecture Concept

This document captures the envisioned approach for building a WebAssembly-powered Progressive Web App that replaces the native mobile clients while keeping the ArxOS experience focused and maintainable for a solo founder.

---

## 1. Architectural Overview

- **Rust-first workspace**  
  - Core logic stays in existing crates (`crates/arx`, `crates/arxos`).  
  - `crates/arxos-wasm` exposes Web bindings via `wasm-bindgen`/`serde_wasm_bindgen`.  
  - PWA implemented with React + Vite + Zustand; Rust focuses on business logic, the TypeScript shell on UX.

- **Service worker & offline-first**  
  - Installable PWA with caching of static assets, WASM bundles, and command metadata.  
  - Offline edits stored in IndexedDB; sync back to Git via the desktop agent when online.

- **Module boundaries**
  1. `wasm-core`: wraps core functionality for the browser (IFC parsing, YAML ops, command catalog).  
  2. `ui-shell`: React components (command palette, floor studio, collaboration, AR preview).  
  3. `interop`: Desktop agent bridge (WebSocket over loopback, DID:key authentication).

---

## 2. Key Experiences

### A. 2D Floor Plan Studio
- WebGPU/Canvas-based editor for drawing, annotating, and validating spaces.  
- Constraint engine leverages core Rust logic; diff overlay vs. repo baseline.

### B. AR View & Edit
- Near-term: WebXR “immersive-ar” overlays for inspection on supported devices (Chrome/Android, Safari/iOS 17+).  
- In-flight (Phase 5): streamed overlays rendered from captured anchor/point data.  
- Future: revisit in-browser scanning once LiDAR-quality WebXR capture lands.

### C. CLI Command Palette
- Command palette UI wrapping core CLI operations (`arx diff`, `arx docs`, etc.).  
- Heavy commands proxied through optional backend (Docker runtime or local agent).

### D. Messaging & Collaboration
- WebRTC or WebSocket channels for building-specific rooms.  
- Attach references to floor plan selections or IFC elements.  
- Offline queue synced on reconnect.

---

## 3. Technology Choices

| Capability | Option | Notes |
|------------|--------|-------|
| UI Shell | React + Vite + Zustand | Mirrors CLI workflow, minimal runtime overhead. |
| Rendering | Canvas2D today; WebGPU/WebGL roadmap | Floor Studio prototype uses Canvas2D. |
| State | Zustand + immer (optional) | Browser state mirrored from WASM DTOs. |
| Storage | IndexedDB via idb-keyval | Offline queue + cached commands. |
| CLI Bridge | Rust desktop agent (`crates/arxos-agent`) | DID:key token passed over loopback WebSocket. |
| Tooling | `wasm-pack` + Vite build | GitHub Pages deploy + IPFS mirror.

---

## 4. Interaction Modes

1. **Pure Browser**  
   - Read-only exploration using WASM bindings.  
   - Git operations limited to hosted APIs; no filesystem access.

2. **Desktop Companion**  
   - Rust “agent” binary exposes local filesystem/Git through WebSocket API secured by DID:key.  
   - Required for commits, IFC import/export, and collaboration sync.

3. **Field Tablet / Kiosk**  
   - Install PWA on iPadOS/Android with WebXR enabled.  
   - Offline caches and scheduled syncs via the agent when docked.

---

## 5. Developer Workflow

- `wasm-pack build crates/arxos-wasm --target web --out-dir pkg` before running the PWA.  
- `npm install && npm run dev` inside `pwa/` for local development.  
- Integration tests with `wasm-pack test --headless --chrome`.  
- E2E tests using Playwright (planned) to ensure cross-browser behavior.  
- GitHub Pages publishes the static bundle; IPFS snapshot mirrors each release.

---

## 6. Roadmap Sketch

1. **MVP (2D & data workflows)**  
   - ✅ View/import IFC-derived geometry from AR scans, render 2D plans.  
   - ✅ Command palette hydrated from Rust command catalog + Zustand history.  
   - ⚙️ Git sync flows via desktop agent (in progress as actions/Git commands come online).

2. **Visualization Enhancements**  
- ✅ WebGL 3D viewer for existing point clouds.  
- ✅ Collaboration panel backed by agent WebSocket → Git issue/comment pipeline.

3. **AR Overlay (no new capture)**  
   - ✅ WebXR capability detection and session bootstrap.  
   - ✅ Phase 5 pilot: streamed overlays via WebXR + desktop agent bridge.
   - ❌ Use simulated anchors until browser capture stabilises.

4. **WebXR Scanning (future)**  
   - When browsers expose LiDAR-quality scanning, integrate capture flow.  
   - Monitor WebXR Device API roadmap (Apple Vision Pro, Chrome origin trials) quarterly.  
   - Reevaluate need for reviving native apps.

---

## 7. UX Ideas

- **Command-centric UI** replicating the terminal-first feel; keyboard shortcuts and fuzzy search.  
- **Layered views** toggling between blueprint, IFC metadata, sensor overlays.  
- **Replay mode** leveraging ArxOS history to animate change timelines.  
- **Remote CLI control** hooking into Dockerized runtimes for heavy operations.

---

## 8. Native App Handling

- Keep `ios/` and `android/` directories archived with “paused” README notes; no active maintenance.  
- Document fallback scanning options (existing iOS prototype, third-party hardware).  
- Monitor WebXR progress quarterly to decide when to resume native scanning work.

---

## 9. Action Items (Initial)

1. ✅ Select WASM UI framework and scaffolding tools (Vite + React + Zustand).  
2. ✅ Create `crates/arxos-wasm` crate with bindings to core logic.  
3. ✅ Prototype 2D plan editor UI + AR scan rendering through WASM.  
4. ✅ Design command palette and backend interface (local agent with DID:key auth).  
5. ✅ Draft documentation (`docs/web/DEVELOPMENT.md`) and update roadmap for WASM-first delivery.

---

This plan lets ArxOS focus on a single, Rust-powered application surface today while leaving room to reintroduce native LiDAR capture when WebXR is ready. It balances simplicity for a solo founder with the “cool” experience you’re aiming for: a terminal-era command feel, modern 2D/AR visuals, and seamless automation hooks.

