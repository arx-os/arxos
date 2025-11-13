# ArxOS Web PWA

This directory hosts the browser application that replaces the native iOS and Android shells. It
consumes core ArxOS logic compiled to WebAssembly (`crates/arxos-wasm`) and mirrors the
command-centric workflow from the CLI.

## Getting Started

```bash
# 1. Build the WASM bindings
wasm-pack build ../crates/arxos-wasm --target web --out-dir pkg

# 2. Install dependencies
cd pwa
npm install

# 3. Run the dev server
npm run dev
```

## Stack

- React + TypeScript
- Zustand for state management
- TailwindCSS for styling
- Vite for bundling & dev server
- Service worker (manual cache-first strategy)

## Implemented Features

### M01: Foundational PWA Setup
- Command palette UI hydrated from WASM bindings
- Service worker with cache-first strategy
- TailwindCSS styling system
- Zustand state management

### M02: Command-Centric Shell
- Command console with execution logging
- Collaboration panel with offline queue persisted via Zustand
- Git status panel (agent-ready)
- IFC panel for BIM data

### M03: Floor Plan Viewer (NEW)
- Interactive 2D floor plan visualization with Canvas2D
- Pan, zoom, and navigation controls
- Layer-based rendering (grid, rooms, equipment)
- Selection and hover states with details panel
- Building/floor selector with mock data from WASM
- Modular architecture (`src/modules/floor/`)
  - Renderer engine (Camera, SceneGraph, Layers)
  - React components (FloorViewer, FloorCanvas, FloorControls)
  - TypeScript geometry adapters with runtime validation
- Keyboard shortcut (Cmd/Ctrl+F) to toggle floor viewer

## WASM Integration

`src/lib/wasm.ts` dynamically loads the generated WASM package. The current bindings expose:

- `arxos_version()` – runtime version string
- `parse_ar_scan(json)` / `extract_equipment(json)` – AR helpers for Floor Studio
- `validate_ar_scan(json)` – lightweight schema check
- `command_palette()` / `command_categories()` – command metadata for the Zustand store
- `command_details(name)` – fetch extended metadata for a specific command

**M03 Geometry Exports:**
- `get_buildings()` – returns list of building summaries
- `get_building(path)` – returns full building data with floors
- `get_floor(buildingPath, floorId)` – returns single floor with rooms and equipment
- `get_floor_bounds(buildingPath, floorId)` – returns bounding box for a floor

TypeScript adapters in `src/lib/wasm/geometry.ts` provide runtime type validation for all WASM responses.

Future bindings will add Git/IFC operations that proxy through the desktop agent using a DID:key loopback handshake.

## Deployment Targets

- Primary: GitHub Pages (static hosting via `npm run build`)
- Mirror: IPFS snapshot published alongside releases for decentralized access

## Service Worker

A minimal service worker (`public/sw.js`) caches core assets to enable offline command palette usage.
Expand this to precache WASM bundles and larger assets as the PWA grows.

