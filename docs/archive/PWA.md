# ArxOS Progressive Web App (PWA)

## Overview

ArxOS is a **Progressive Web App** that provides native app-like functionality without requiring app store installation. It works offline, can be installed on any device, and provides full access to building intelligence features through the browser.

## Why PWA Instead of Native Apps?

### Advantages
- **No App Store**: Direct installation from browser
- **Cross-Platform**: Single codebase for iOS, Android, Desktop
- **Auto-Updates**: Always latest version, no manual updates
- **Smaller Size**: ~2MB vs 50MB+ native apps
- **No Permissions Hassle**: Progressive permission requests
- **Web Standards**: Future-proof, standards-based
- **SEO Friendly**: Discoverable via search engines
- **Linkable**: Share specific queries/views via URL

### Feature Parity with Native

| Feature | PWA Support | Implementation |
|---------|------------|----------------|
| Offline Mode | ✅ | Service Worker + IndexedDB |
| Camera Access | ✅ | MediaDevices API |
| File Upload | ✅ | File API + Drag/Drop |
| Push Notifications | ✅ | Push API |
| Background Sync | ✅ | Background Sync API |
| Install to Home | ✅ | Web App Manifest |
| Share Target | ✅ | Web Share Target API |
| File Handling | ✅ | File Handling API |
| Protocol Handler | ✅ | `arxos://` URLs |
| Clipboard | ✅ | Clipboard API |
| Geolocation | ✅ | Geolocation API |
| Bluetooth | ⚠️ | Web Bluetooth (Chrome only) |
| NFC | ⚠️ | Web NFC (Chrome Android) |

## Installation

### Desktop (Chrome, Edge, Safari)
1. Visit https://arxos.app
2. Click install icon in address bar
3. Or: Menu → "Install ArxOS"

### iOS (Safari)
1. Visit https://arxos.app
2. Tap Share button
3. Select "Add to Home Screen"
4. Name it and tap "Add"

### Android (Any Browser)
1. Visit https://arxos.app
2. Tap "Add to Home" banner
3. Or: Menu → "Add to Home screen"

## PWA Features

### 1. Offline-First Architecture

```javascript
// All data cached locally
IndexedDB: Building objects (unlimited storage)
Cache API: Static assets, API responses
LocalStorage: User preferences, history
```

### 2. Camera Capture for Floor Plans

```javascript
// Direct camera access for scanning
navigator.mediaDevices.getUserMedia({ video: true })

// Or file upload
<input type="file" accept="image/*" capture="environment">
```

### 3. Progressive Enhancement

```javascript
// Features enable as available
if ('serviceWorker' in navigator) // Offline support
if ('mediaDevices' in navigator) // Camera access
if ('share' in navigator) // Native sharing
```

### 4. Responsive Design

- **Mobile**: Touch-optimized terminal
- **Tablet**: Split view with visualization
- **Desktop**: Full terminal + D3.js maps
- **Watch**: Query shortcuts

### 5. Installation Prompts

```javascript
// Custom install experience
let deferredPrompt;
window.addEventListener('beforeinstallprompt', (e) => {
  deferredPrompt = e;
  showInstallButton();
});
```

## Offline Capabilities

### What Works Offline

✅ **Full Terminal**
- Execute queries against cached data
- Parse ASCII descriptions
- View command history
- Local object storage

✅ **Data Capture**
- Camera capture queued for sync
- Parse floor plans locally
- Create ArxObjects offline

✅ **Visualization**
- D3.js renders from local data
- Pan/zoom cached floor plans
- Export SVG/PNG

### Sync Strategy

```javascript
// Automatic sync when online
navigator.onLine // Check connection
BackgroundSync API // Queue changes
Periodic Sync // Refresh data
```

## Performance

### Load Times
- **First Load**: < 2 seconds
- **Subsequent**: < 200ms (from cache)
- **Offline**: Instant

### Storage Usage
- **App Shell**: ~500KB
- **D3.js Library**: ~300KB
- **10,000 Objects**: ~127KB
- **Total**: < 2MB

### Battery Impact
- **CPU**: Minimal (no background processes)
- **Network**: On-demand only
- **GPS**: Not used
- **Camera**: Only when capturing

## Security

### HTTPS Required
- Service Workers require HTTPS
- Ensures data integrity
- Prevents MITM attacks

### Permissions
- **Camera**: Only when capturing floor plans
- **Storage**: Automatic for offline
- **Notifications**: Optional, on request
- **No Background Tracking**

### Data Storage
- **Local Only**: Building data stays on device
- **Encrypted**: IndexedDB encrypted by OS
- **User Control**: Clear data anytime

## Development

### Testing PWA Features

```bash
# Serve with HTTPS locally
npm run dev -- --https

# Test offline
1. Open DevTools
2. Network tab
3. Set to "Offline"

# Test installation
1. Open chrome://flags
2. Enable "Desktop PWAs"
3. Reload and install
```

### Lighthouse Audit

```bash
# Run PWA audit
1. Open DevTools
2. Lighthouse tab
3. Check "Progressive Web App"
4. Run audit

Target scores:
- Performance: 90+
- PWA: 100
- Accessibility: 90+
- Best Practices: 90+
```

## Browser Compatibility

| Feature | Chrome | Safari | Firefox | Edge |
|---------|--------|--------|---------|------|
| Install | ✅ | ✅ iOS 11.3+ | ⚠️ Android | ✅ |
| Offline | ✅ | ✅ | ✅ | ✅ |
| Camera | ✅ | ✅ | ✅ | ✅ |
| Push | ✅ | ⚠️ iOS 16.4+ | ✅ | ✅ |
| Share | ✅ | ✅ | ⚠️ | ✅ |
| File | ✅ | ⚠️ | ⚠️ | ✅ |

## Deployment

### Static Hosting
```nginx
# nginx config for PWA
location / {
  try_files $uri $uri/ /index.html;
}

# Cache static assets
location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
  expires 1y;
  add_header Cache-Control "public, immutable";
}

# Don't cache service worker
location = /service-worker.js {
  expires off;
  add_header Cache-Control "no-cache";
}
```

### CDN Configuration
- CloudFlare Pages (recommended)
- Vercel
- Netlify
- AWS CloudFront

## User Experience

### App-Like Feel
- **Fullscreen**: No browser chrome
- **Splash Screen**: Custom loading screen
- **Smooth Animations**: 60fps transitions
- **Touch Gestures**: Swipe, pinch, zoom
- **Native Widgets**: Date pickers, etc.

### Desktop Integration
- **Taskbar/Dock Icon**
- **Alt+Tab Switching**
- **File Associations**
- **Protocol Handler**: `arxos://query/...`

### Mobile Integration
- **Home Screen Icon**
- **App Switcher**
- **Share Menu**
- **Widget Support** (Android 12+)

## Marketing Benefits

### Discovery
- **SEO**: Full indexing by search engines
- **Social Sharing**: Rich previews
- **QR Codes**: Direct to specific views
- **Deep Links**: arxos://building/42

### Adoption
- **Try Before Install**: Use in browser first
- **Instant Access**: No download wait
- **Low Friction**: One-tap install
- **Cross-Sell**: Web users → PWA users

## Future PWA Features

### Coming Soon (Web Standards)
- **File System Access**: Direct file editing
- **WebGPU**: Advanced visualizations
- **WebAssembly**: Rust in browser
- **WebXR**: AR/VR support
- **Web Bluetooth**: Direct device connection
- **Badging API**: Notification badges

### Planned Enhancements
- [ ] 3D visualization with Three.js
- [ ] Voice commands via Web Speech
- [ ] Barcode scanning for equipment
- [ ] Handwriting recognition
- [ ] Multi-window support

## Conclusion

ArxOS as a PWA provides the best of both worlds:
- **Native performance and features**
- **Web distribution and updates**
- **No app store gatekeepers**
- **Single codebase to maintain**
- **Progressive enhancement for all devices**

The PWA approach aligns perfectly with ArxOS's philosophy of being **accessible, offline-first, and user-controlled**.