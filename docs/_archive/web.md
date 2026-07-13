# Web Interface

ArxOS Progressive Web App (PWA) for browser-based building management.

---

## Overview

The ArxOS web interface is a **Progressive Web App** built with:

- **Rust + WASM** – Compiled to WebAssembly for performance
- **Leptos** – Reactive web framework
- **Offline-first** – Works without network connection
- **Responsive** – Desktop and mobile layouts

**URL:** `http://localhost:8080` (default)

---

## Quick Start

### Launch Web Interface

```bash
# Start web server
arx web

# Browser opens automatically at http://localhost:8080
```

### Build from Source

```bash
# Install Trunk (WASM bundler)
cargo install trunk

# Navigate to web directory
cd src/web

# Development server (hot reload)
trunk serve

# Production build
trunk build --release
```

---

## Features

### Home Dashboard

- Overview of all buildings
- Quick access to recent changes
- Git status indicators
- Search functionality

### Building Explorer

- View building hierarchy (floors, rooms)
- Equipment list with status
- 3D visualization (WebGPU)
- Filter and search

### Import Interface

- Upload IFC files via drag-and-drop
- Preview import results
- Validate before committing
- Git integration

### Data Editor

- Edit building properties
- Add/update equipment
- Modify room assignments
- Live validation

---

## Architecture

### WASM Bridge

The web app communicates with core ArxOS functionality via WASM:

```
Browser (JavaScript)
  ↓
Leptos Components (Rust)
  ↓
WASM Bridge (src/web/wasm_bridge.rs)
  ↓
ArxOS Core (Rust)
  ↓
Building Data (YAML + Git)
```

### Storage

**LocalStorage:**
- User preferences
- Recent files
- Cached building lists

**IndexedDB:**
- Building data (full copy)
- Offline functionality
- Git commits (metadata)

---

## Development

### File Structure

```
src/web/
├── app.rs              # Main app component
├── lib.rs              # WASM entry point
├── wasm_bridge.rs      # Core functionality bridge
├── pages/              # Page components
│   ├── home.rs         # Dashboard
│   ├── import.rs       # IFC import
│   ├── buildings.rs    # Building list
│   └── building_detail.rs  # Building view
├── components/         # Reusable components
│   ├── equipment_list.rs
│   ├── floor_view.rs
│   └── search_bar.rs
└── styles/
    └── app.css         # Styles
```

### Development Server

```bash
cd src/web
trunk serve

# Opens http://localhost:8080
# Hot reload on file changes
# WASM compilation automatic
```

### Production Build

```bash
cd src/web
trunk build --release

# Output to dist/
# Optimized WASM bundle
# Minified assets
```

---

## Configuration

### Trunk.toml

```toml
[[build]]
target = "web"
release = true

[watch]
ignore = ["dist"]

[serve]
address = "127.0.0.1"
port = 8080
open = false

[clean]
dist = "dist"
cargo = false
```

### Custom Port

```bash
# Edit Trunk.toml
[serve]
port = 3000

# Or use environment variable
PORT=3000 trunk serve
```

---

## Deployment

### Static Hosting

The PWA is a static site that can be deployed to:

- **GitHub Pages**
- **Netlify**
- **Vercel**
- **AWS S3 + CloudFront**
- **Firebase Hosting**
- Any static web host

### GitHub Pages

```bash
# Build production bundle
cd src/web
trunk build --release --public-url /arxos/

# Copy dist/ to GitHub Pages branch
cp -r dist/* ../../gh-pages/

# Push to gh-pages branch
cd ../../gh-pages
git add .
git commit -m "Deploy PWA"
git push origin gh-pages
```

### Docker

```dockerfile
FROM rust:1.75 as builder

# Install trunk
RUN cargo install trunk

# Copy source
WORKDIR /app
COPY . .

# Build WASM
WORKDIR /app/src/web
RUN trunk build --release

# Production image
FROM nginx:alpine
COPY --from=builder /app/src/web/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

**Run:**
```bash
docker build -t arxos-web .
docker run -p 8080:80 arxos-web
```

---

## Offline Support

### Service Worker

The PWA includes a service worker for offline functionality:

**Features:**
- Cache building data
- Offline page views
- Background sync
- Push notifications (future)

**Configuration:**

```javascript
// Cached resources
const CACHE_NAME = 'arxos-v1';
const CACHE_URLS = [
  '/',
  '/index.html',
  '/pkg/arxos.js',
  '/pkg/arxos_bg.wasm',
  '/styles/app.css'
];
```

### Usage

```bash
# First visit: Downloads and caches assets
# Subsequent visits: Works offline
# Background: Syncs when online
```

---

## API Integration

### Desktop Agent Bridge

The web app can connect to a local ArxOS instance:

```typescript
// Connect to local agent
const agent = new ArxOSAgent('http://localhost:3000');

// Execute commands
await agent.execute('arx status');
await agent.execute('arx import building.ifc');

// Get building data
const building = await agent.getBuilding('office-tower');
```

**Setup:**

```bash
# Start agent on desktop
arx remote start --port 3000

# Web app connects automatically
# CORS headers configured
```

---

## Performance

### WASM Optimization

```bash
# Enable LTO (Link Time Optimization)
[profile.release]
lto = true
opt-level = 'z'  # Optimize for size

# Strip symbols
strip = true

# Result: ~500KB WASM bundle (gzipped)
```

### Lazy Loading

Components load on demand:

```rust
// Code splitting
#[component]
fn BuildingDetail() -> impl IntoView {
    let (building, set_building) = create_signal(None);
    
    // Load building data asynchronously
    create_effect(move |_| {
        spawn_local(async move {
            let data = fetch_building().await;
            set_building(Some(data));
        });
    });
    
    view! { /* render */ }
}
```

---

## Browser Support

### Supported Browsers

**Desktop:**
- ✅ Chrome 90+
- ✅ Firefox 88+
- ✅ Safari 14+
- ✅ Edge 90+

**Mobile:**
- ✅ Chrome Mobile (Android)
- ✅ Safari Mobile (iOS 14+)
- ✅ Samsung Internet
- ✅ Firefox Mobile

### Required Features

- **WebAssembly** (all modern browsers)
- **IndexedDB** (for offline storage)
- **Service Workers** (for PWA features)
- **WebGPU** (optional, for 3D rendering)

---

## Troubleshooting

### WASM Compilation Fails

```bash
# Ensure wasm target installed
rustup target add wasm32-unknown-unknown

# Clear build cache
trunk clean
cargo clean

# Rebuild
trunk build --release
```

### Page Not Loading

```bash
# Check browser console for errors
# Common issues:

# 1. CORS errors
# Solution: Run local agent with CORS enabled

# 2. WASM module load failure
# Solution: Check Content-Type headers (should be application/wasm)

# 3. Service worker registration failure
# Solution: Ensure HTTPS or localhost
```

### Slow Performance

```bash
# Use release build
trunk build --release

# Enable WASM optimization
# Add to Cargo.toml:
[profile.release]
lto = true
opt-level = 'z'
```

---

## Security

### Content Security Policy

```html
<meta http-equiv="Content-Security-Policy" 
      content="default-src 'self'; 
               script-src 'self' 'wasm-unsafe-eval'; 
               style-src 'self' 'unsafe-inline';">
```

### HTTPS Requirement

PWA features require HTTPS (except localhost):

```bash
# Development: localhost works
trunk serve

# Production: Use HTTPS
# - Let's Encrypt for free certificates
# - Cloudflare for automatic HTTPS
```

---

## Advanced

### Custom Styling

Edit `src/web/styles/app.css`:

```css
:root {
  --primary-color: #2563eb;
  --secondary-color: #7c3aed;
  --background: #ffffff;
  --text: #1f2937;
}

.app-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
}
```

### Add New Page

1. Create component in `src/web/pages/`:

```rust
// src/web/pages/sensors.rs
use leptos::*;

#[component]
pub fn Sensors() -> impl IntoView {
    view! {
        <div class="sensors-page">
            <h2>"Sensor Dashboard"</h2>
            // Component content
        </div>
    }
}
```

2. Add route in `src/web/app.rs`:

```rust
<Route path="/sensors" view=Sensors/>
```

3. Add navigation link:

```rust
<A href="/sensors" class="nav-link">"Sensors"</A>
```

---

## Examples

### Complete Development Workflow

```bash
# 1. Install dependencies
cargo install trunk
rustup target add wasm32-unknown-unknown

# 2. Start development server
cd src/web
trunk serve

# 3. Edit code (auto-reloads)
# - Modify pages in src/web/pages/
# - Edit components in src/web/components/
# - Update styles in styles/app.css

# 4. Test in browser
# http://localhost:8080

# 5. Build for production
trunk build --release

# 6. Deploy dist/ to static host
```

### Connecting to Local Desktop Agent

```bash
# Terminal 1: Start desktop agent
arx remote start --port 3000

# Terminal 2: Start web interface
cd src/web
trunk serve

# Browser: Web app connects to localhost:3000
# Full desktop functionality in browser
```

---

**See Also:**
- [Getting Started](./getting-started.md) – Basic ArxOS usage
- [Architecture](./architecture.md) – System design
- [CLI Reference](./cli-reference.md) – Command documentation
