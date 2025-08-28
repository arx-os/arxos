# ArxOS Layer 4 ASCII-BIM Progressive Web Application

A browser-based ASCII interface that extends ArxOS's terminal ASCII success to web users with offline capability and responsive design.

## Features

### 🎯 Core Capabilities
- **Browser-Based ASCII Rendering** - High-performance ASCII visualization in any modern browser
- **Real-Time WebSocket Communication** - Live updates from ArxOS backend
- **Progressive Web App** - Installable, offline-capable web application
- **Responsive Design** - Works on desktop, tablet, and mobile devices
- **Layer 4 Integration** - Seamless integration with ArxOS's layered architecture

### 📱 Progressive Web App Features
- **Offline Mode** - Cached building data works without internet connection
- **App Installation** - Install directly from browser to home screen/desktop
- **Background Sync** - Automatic data sync when connection is restored
- **Push Notifications** - Real-time building updates (future feature)
- **Native App Feel** - Full-screen, app-like experience

### 🎨 ASCII Visualization
- **High-Performance Rendering** - 60fps ASCII canvas with viewport management
- **Building Element Support** - Rooms, walls, doors, windows, electrical equipment
- **Interactive Navigation** - Pan, zoom, and select building objects
- **Real-Time Updates** - Live object updates via WebSocket
- **Mobile Optimized** - Touch-friendly interaction on mobile devices

### 🔧 Technical Features
- **Service Worker Caching** - Smart caching strategies for optimal performance
- **IndexedDB Storage** - Persistent offline storage for building data
- **Viewport Optimization** - Only renders visible objects for better performance
- **Layer-Aware Messaging** - Communicates with ArxOS using Layer 4 context
- **Error Handling** - Graceful degradation and error recovery

## Architecture

```
┌─────────────────────┐    ┌─────────────────────┐    ┌─────────────────────┐
│    Browser PWA      │    │   ArxOS Backend     │    │   Building Data     │
│  ┌───────────────┐  │    │  ┌───────────────┐  │    │  ┌───────────────┐  │
│  │ ASCII Renderer│  │    │  │   WebSocket   │  │    │  │   ArxObjects   │  │
│  └───────────────┘  │◄───┤  │    Server     │  │◄───┤  │   Database    │  │
│  ┌───────────────┐  │    │  └───────────────┘  │    │  └───────────────┘  │
│  │Service Worker │  │    │  ┌───────────────┐  │    │  ┌───────────────┐  │
│  └───────────────┘  │    │  │ Layer Context │  │    │  │  Cache Layer  │  │
│  ┌───────────────┐  │    │  └───────────────┘  │    │  └───────────────┘  │
│  │  IndexedDB    │  │    └─────────────────────┘    └─────────────────────┘
│  └───────────────┘  │
└─────────────────────┘
```

## Getting Started

### Prerequisites
- Go 1.21+ (for development server)
- Modern web browser with PWA support
- ArxOS backend (optional - demo mode available)

### Quick Start

1. **Clone and Setup**
   ```bash
   cd cmd/ascii-pwa
   go mod tidy
   ```

2. **Start Development Server**
   ```bash
   go run server.go
   ```

3. **Open PWA**
   ```
   http://localhost:8080
   ```

4. **Install PWA** (Optional)
   - Click the install button in the browser
   - Or use browser's "Install App" option

### Production Deployment

1. **Build for Production**
   ```bash
   # Build Go server
   go build -o ascii-pwa-server server.go
   
   # Or serve static files with any web server
   # nginx, Apache, or cloud hosting
   ```

2. **Configure WebSocket**
   - Update WebSocket URLs in `websocket-client.js`
   - Configure CORS settings for production domain
   - Set up SSL/TLS for secure WebSocket (WSS)

3. **Deploy Service Worker**
   - Ensure `sw.js` is served from root domain
   - Configure cache policies for your deployment
   - Test offline functionality

## Usage

### Basic Navigation
- **Pan**: Click and drag to move around the building
- **Zoom**: Use mouse wheel or zoom slider
- **Select**: Click on objects to view details
- **Fit**: Press 'F' to fit all objects in view
- **Refresh**: Press 'R' or click refresh button

### Mobile/Touch
- **Pan**: Touch and drag
- **Zoom**: Pinch gestures
- **Menu**: Tap hamburger menu to show/hide sidebar
- **Select**: Tap on objects

### Sidebar Features
- **Objects Tab**: Browse all building objects by type
- **Properties Tab**: View detailed properties of selected objects  
- **Layers Tab**: Toggle visibility of object types

### Keyboard Shortcuts
- `F` - Fit all objects to viewport
- `R` - Refresh building data
- `1/2/3` - Switch sidebar tabs (Objects/Properties/Layers)
- `Escape` - Close mobile sidebar

### Offline Mode
- Buildings are automatically cached for offline viewing
- Offline indicator appears when disconnected
- Cached data is synchronized when connection returns
- Install as PWA for best offline experience

## Development

### Project Structure
```
cmd/ascii-pwa/
├── index.html          # Main PWA interface
├── manifest.json       # PWA manifest
├── sw.js              # Service worker
├── ascii-renderer.js   # ASCII rendering engine
├── websocket-client.js # WebSocket communication
├── pwa-manager.js     # PWA functionality
├── app.js             # Main application logic
├── server.go          # Development server
├── go.mod             # Go dependencies
├── icons/             # PWA icons
└── README.md          # This file
```

### Key Components

#### ASCII Renderer (`ascii-renderer.js`)
- Canvas-based ASCII rendering with viewport management
- Z-buffered drawing for proper object layering  
- Touch and mouse interaction handling
- Performance optimizations for 60fps rendering

#### WebSocket Client (`websocket-client.js`)
- Layer 4 ASCII context communication
- Automatic reconnection with exponential backoff
- Message queuing for offline scenarios
- ArxObject transformation for renderer compatibility

#### PWA Manager (`pwa-manager.js`)
- Service worker registration and updates
- Offline storage using IndexedDB
- Background sync coordination
- Install prompt management

#### Service Worker (`sw.js`)
- Cache-first strategy for static assets
- Network-first strategy for dynamic data
- Background sync for building updates
- Push notification handling (future)

### Extending the PWA

#### Adding New Object Types
1. Update `ascii-renderer.js` character mappings
2. Add rendering logic in `renderObject()` method
3. Update WebSocket message handling
4. Test with real ArxObject data

#### Custom Cache Strategies
1. Modify `sw.js` cache patterns
2. Update cache names and versions
3. Add new caching strategies as needed
4. Test offline functionality

#### New UI Features
1. Add HTML elements to `index.html`
2. Update CSS for styling and responsive design
3. Add JavaScript event handlers in `app.js`
4. Test across device types

## Integration with ArxOS

### WebSocket Protocol
The PWA communicates with ArxOS using Layer 4 ASCII context:

```javascript
// Layer context message
{
  type: 'layer_context',
  context: {
    layer: 'LayerASCII',
    precision: 'medium',
    viewport: { minX, minY, maxX, maxY }
  }
}

// Object update message
{
  type: 'object_update',
  payload: [ArxObject, ...],
  layer: 'LayerASCII'
}
```

### ArxObject Compatibility
The PWA transforms standard ArxObjects to internal format:
- Supports both camelCase and PascalCase properties
- Creates bounding boxes for objects without geometry
- Maintains confidence scores and metadata
- Preserves all original properties

### Performance Optimization
- Only renders objects within viewport bounds
- Uses viewport-based server filtering
- Implements object culling for large buildings
- Caches transformed objects for reuse

## Browser Compatibility

### Supported Browsers
- ✅ Chrome 88+ (Desktop/Mobile)
- ✅ Firefox 85+ (Desktop/Mobile)  
- ✅ Safari 14+ (Desktop/Mobile/iOS)
- ✅ Edge 88+ (Desktop/Mobile)

### PWA Features by Browser
| Feature | Chrome | Firefox | Safari | Edge |
|---------|--------|---------|--------|------|
| Install | ✅ | ✅ | ✅ | ✅ |
| Offline | ✅ | ✅ | ✅ | ✅ |
| Notifications | ✅ | ✅ | ❌ | ✅ |
| Background Sync | ✅ | ❌ | ❌ | ✅ |

## Performance Metrics

### Target Performance
- **First Contentful Paint**: < 1.5s
- **Time to Interactive**: < 2.5s  
- **Render Rate**: 60 FPS ASCII
- **Memory Usage**: < 50MB for typical building
- **Cache Size**: < 10MB offline storage

### Optimization Techniques
- Service worker pre-caching
- IndexedDB for persistent storage
- Viewport culling for large datasets
- Debounced WebSocket updates
- Compressed ASCII character sets

## Troubleshooting

### Common Issues

**PWA Won't Install**
- Check manifest.json is valid
- Ensure HTTPS (required for PWA)
- Verify service worker registration
- Clear browser cache and try again

**ASCII Not Rendering**
- Check browser console for errors
- Verify WebSocket connection status
- Test with demo data first
- Check viewport coordinates

**Offline Mode Not Working**
- Ensure service worker is active
- Check cache storage in DevTools
- Verify IndexedDB permissions
- Test network disconnection scenario

**WebSocket Connection Fails**
- Check server is running and accessible
- Verify CORS settings for cross-origin
- Test WebSocket URL directly
- Check firewall/proxy settings

### Debug Mode
Enable debug logging:
```javascript
localStorage.setItem('arxos-debug', 'true');
// Reload page to see debug messages
```

## Future Enhancements

### Planned Features
- **Push Notifications** - Real-time building change alerts
- **Advanced Caching** - Predictive pre-loading of related buildings
- **Collaboration** - Multi-user viewing with cursors
- **Export Features** - Save ASCII art as images/text
- **Accessibility** - Screen reader support and keyboard navigation

### Performance Improvements
- **Web Workers** - Background processing for large datasets
- **WASM Rendering** - Native-speed ASCII rendering engine
- **Streaming Updates** - Partial object updates over WebSocket
- **Advanced Culling** - Spatial indexing for viewport optimization

## Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/ascii-enhancement`)
3. Test across browsers and devices
4. Submit pull request with PWA performance metrics

## License

Part of the ArxOS project - see main repository for license details.

---

**ArxOS Layer 4 ASCII-BIM PWA** - Bringing building intelligence to every browser, everywhere.