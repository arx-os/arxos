# ArxOS WASM PWA Architecture Concept

This document captures the envisioned approach for building a WebAssembly-powered Progressive Web App that replaces the native mobile clients while keeping the ArxOS experience focused and maintainable for a solo founder.

---

## 1. Architectural Overview

- **Rust-first workspace**  
  - Core logic stays in existing crates (`crates/arx`, `crates/arxos`).  
  - New `crates/arxos-wasm` crate exposes Web bindings via `wasm-bindgen`/`web-sys`.  
  - Optional UI layer in Rust (Leptos, Yew, Dioxus) or a thin TypeScript shell that talks to the WASM module.

- **Service worker & offline-first**  
  - Installable PWA with caching of static assets, CLI bundles, and local datasets.  
  - Offline edits stored in IndexedDB; sync back to Git when online.

- **Module boundaries**
  1. `wasm-core`: wraps core functionality for the browser (IFC parsing, YAML ops).  
  2. `ui-shell`: components for the floor plan editor, dashboards, messaging.  
  3. `interop`: pathways to host services (Git, messaging, optional backend APIs).

---

## 2. Key Experiences

### A. 2D Floor Plan Studio
- WebGPU/Canvas-based editor for drawing, annotating, and validating spaces.  
- Constraint engine leverages core Rust logic; diff overlay vs. repo baseline.

### B. AR View & Edit
- Near-term: WebXR “immersive-ar” overlays for inspection on supported devices.  
- Future: enable in-browser scanning once LiDAR-quality WebXR lands (targeted for Q4 2026).  
- Until then, rely on imported scans or third-party capture tools.

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
| UI Shell | Leptos / Dioxus (Rust) or TS shell + `wasm-bindgen` | Entirely Rust or hybrid UI. |
| Rendering | `wgpu` (via WASM) or Canvas2D/WebGL | High-fidelity overlays, zoom, pan. |
| State | `serde` + `serde_wasm_bindgen` | Shared structs across Rust/JS. |
| Storage | `indexed_db` crate or `idb-keyval` bindings | Offline model and history. |
| CLI Bridge | WebWorker or local agent (WebSocket) | Heavy commands run off-thread or on desktop daemon. |
| Tooling | `trunk` or Vite + `wasm-pack` | Choose based on front-end preference. |

---

## 4. Interaction Modes

1. **Pure Browser**  
   - Entire flow runs inside WASM sandbox.  
   - Git operations via HTTPS PATs or hosted API.

2. **Desktop Companion**  
   - Optional Rust “agent” binary exposes local filesystem/Git through WebSocket API.  
   - PWA connects securely to execute commands with local privileges.

3. **Field Tablet / Kiosk**  
   - Install PWA as app on Android tablets, iPads (Safari).  
   - Offline caches and scheduled syncs for facility visits.

---

## 5. Developer Workflow

- `cargo watch` for core crates; `trunk serve` or `npm run dev` for WASM build with live reload.  
- Integration tests with `wasm-pack test --headless --chrome`.  
- E2E tests using Playwright/Selenium to ensure cross-browser behavior.

---

## 6. Roadmap Sketch

1. **MVP (2D & data workflows)**  
   - View/import IFC, edit metadata, render 2D plans.  
   - Command palette and Git sync with backend helper.

2. **Visualization Enhancements**  
   - WebGL 3D viewer for existing point clouds.  
   - Messaging + collaboration panel.

3. **AR Overlay (no new capture)**  
   - WebXR viewer for alignment/inspection on supported devices.  
   - Offer guidance on third-party capture tools or archived native apps.

4. **WebXR Scanning (future)**  
   - When browsers expose LiDAR-quality scanning, integrate capture flow.  
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

1. Select WASM UI framework and scaffolding tools.  
2. Create `crates/arxos-wasm` crate with bindings to core logic.  
3. Prototype 2D plan editor UI + IFC import/export through WASM.  
4. Design command palette and backend interface (local agent or hosted API).  
5. Draft documentation for the new platform direction and update roadmap.

---

This plan lets ArxOS focus on a single, Rust-powered application surface today while leaving room to reintroduce native LiDAR capture when WebXR is ready. It balances simplicity for a solo founder with the “cool” experience you’re aiming for: a terminal-era command feel, modern 2D/AR visuals, and seamless automation hooks.

