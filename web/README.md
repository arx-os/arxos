# ArxOS Web 3D Visualization

## Overview

Modern web-based 3D building information model visualization using D3.js, Three.js, and Svelte.

## Technology Stack

- **Svelte** - Reactive UI framework
- **Three.js** - 3D graphics rendering
- **D3.js** - Data visualization and layouts
- **WebGL** - Hardware-accelerated 3D graphics
- **WebSockets** - Real-time updates from ArxOS server

## Architecture

```
┌─────────────────────────────────────────┐
│          Svelte Application             │
├─────────────────────────────────────────┤
│                                         │
│  ┌──────────┐  ┌──────────┐           │
│  │  Three.js│  │  D3.js   │           │
│  │  3D View │  │  2D View │           │
│  └──────────┘  └──────────┘           │
│                                         │
│  ┌─────────────────────────┐          │
│  │   Building Data Store    │          │
│  └─────────────────────────┘          │
│                                         │
└─────────────────────────────────────────┘
                    │
                    ▼
        ┌──────────────────────┐
        │  ArxOS API Server    │
        │  (WebSocket + REST)  │
        └──────────────────────┘
```

## Features (Planned)

### 3D Visualization
- Interactive 3D building models
- Floor-by-floor navigation
- Equipment location markers
- Real-time status updates
- Energy flow visualization
- Heat map overlays

### User Interface
- Split view (3D + 2D floor plan)
- Equipment search and filtering
- Timeline scrubber for historical data
- Annotation and markup tools
- Export to various formats

### Data Integration
- Real-time WebSocket updates
- BIM file parsing and rendering
- Equipment telemetry display
- Maintenance schedule overlay
- Alarm and alert visualization

## Development Setup

```bash
cd web
npm install
npm run dev
```

## API Integration

```javascript
// Connect to ArxOS WebSocket
import { ArxOSClient } from './lib/arxos-client';

const client = new ArxOSClient({
  url: 'ws://localhost:8080/ws',
  building: 'ARXOS-NA-US-NY-NYC-0001'
});

client.on('equipment.update', (data) => {
  // Update 3D model with new equipment status
  updateEquipmentStatus(data.equipmentId, data.status);
});
```

## Component Structure

```
web/
├── src/
│   ├── components/
│   │   ├── ThreeJSViewer.svelte    # 3D visualization
│   │   ├── FloorPlan2D.svelte      # D3.js floor plan
│   │   ├── EquipmentPanel.svelte   # Equipment details
│   │   └── Timeline.svelte         # Historical view
│   ├── lib/
│   │   ├── arxos-client.js         # API client
│   │   ├── three-helpers.js        # Three.js utilities
│   │   └── d3-helpers.js           # D3.js utilities
│   └── stores/
│       ├── building.js             # Building data store
│       └── equipment.js            # Equipment state store
└── public/
    └── models/                     # 3D model assets
```

## Future Enhancements

- VR support via WebXR
- Collaborative editing
- Advanced physics simulation
- Machine learning predictions
- Photorealistic rendering