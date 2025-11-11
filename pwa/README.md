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

- Command palette UI hydrated from WASM bindings
- Floor plan canvas prototype using `extract_equipment` output
- Collaboration panel with offline queue persisted via Zustand (mirrors agent sync)

## WASM Integration

`src/lib/wasm.ts` dynamically loads the generated WASM package. The current bindings expose:

- `arxos_version()` – runtime version string
- `parse_ar_scan(json)` / `extract_equipment(json)` – AR helpers for Floor Studio
- `validate_ar_scan(json)` – lightweight schema check
- `command_palette()` / `command_categories()` – command metadata for the Zustand store
- `command_details(name)` – fetch extended metadata for a specific command

Future bindings will add Git/IFC operations that proxy through the desktop agent using a DID:key loopback handshake.

## Deployment Targets

- Primary: GitHub Pages (static hosting via `npm run build`)
- Mirror: IPFS snapshot published alongside releases for decentralized access

## Service Worker

A minimal service worker (`public/sw.js`) caches core assets to enable offline command palette usage.
Expand this to precache WASM bundles and larger assets as the PWA grows.

