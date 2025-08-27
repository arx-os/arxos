# Arxos Technical Architecture & Development Guide

## 1. System Overview

The Arxos platform is a multi-layered Building Information Modeling (BIM) system that democratizes building intelligence through tokenized contributions. The architecture prioritizes performance, progressive enhancement, and submicron precision data handling across six distinct user interaction layers.

### Core Philosophy
- **Server-heavy, client-light**: All computation and data processing occurs server-side
- **Progressive enhancement**: Multiple interaction layers serving the same underlying data
- **Submicron precision**: Support nanometer-level accuracy with adaptive Level of Detail (LOD)
- **Universal accessibility**: From high-end 3D rendering to pure text CLI access
- **Real-time intelligence**: Live building data updates through WebSocket connections

## 2. Multi-Layered Architecture

### 2.1 Core Engine (C)
**Purpose**: High-performance computational backbone for geometry processing

**Responsibilities**:
- LiDAR Point Cloud Processing with submicron precision
- Geometric Primitives Generation (points, lines, planes, volumes)
- Physics-aware ArxObject model generation
- Submicron-precision data serialization
- Real-time spatial calculations for AR correlation

**Key Requirements**:
- Support IEEE 754 double precision (15-17 decimal digits)
- Implement hierarchical spatial indexing for multi-resolution access
- Delta compression for submicron coordinate storage
- Memory-mapped file I/O for large point cloud datasets

```c
typedef struct ArxObject {
    uint64_t id;
    double base_coordinates[3];     // Base position in meters
    int64_t submicron_offset[3];    // Nanometer-level precision offset
    GeometryType type;
    PhysicsProperties physics;
    uint8_t precision_level;        // 0=submicron, 1=micrometer, etc.
} ArxObject;
```

### 2.2 Services Layer (Go)
**Purpose**: API gateway, service orchestrator, and real-time communication hub

**Responsibilities**:
- WebSocket server for real-time multi-layer client communication
- RESTful API endpoints for file uploads and data access
- Adaptive Level of Detail (LOD) selection based on client layer
- Data orchestration between C Core Engine and Python AI Services
- BILT token contribution tracking and reward calculation
- Multi-tenant data access control and privacy obfuscation

**Key APIs**:
```go
// Layer-aware rendering service
type RenderRequest struct {
    Layer         LayerType `json:"layer"`          // 3d, ar, ascii, cli
    Viewport      Bounds    `json:"viewport"`       
    ZoomLevel     float64   `json:"zoom_level"`     
    Precision     string    `json:"precision"`      // submicron, micrometer, etc.
    UserID        string    `json:"user_id"`        
    BuildingID    string    `json:"building_id"`    
}

// WebSocket message types
type WSMessage struct {
    Type      string      `json:"type"`      // geometry, terminal, bilt_reward
    Layer     LayerType   `json:"layer"`     
    Data      interface{} `json:"data"`      
    Precision string      `json:"precision"` 
}
```

**Performance Requirements**:
- Handle 1000+ concurrent WebSocket connections per instance
- Sub-100ms latency for LOD switching
- Horizontal scaling through load balancing

### 2.3 AI Services (Python)
**Purpose**: Machine learning and image processing for building intelligence extraction

**Responsibilities**:
- Floor plan image to ASCII art conversion
- Image analysis for geometric feature extraction
- ArxObject classification and property prediction
- Data quality assessment for BILT reward calculation
- Building intelligence enhancement (energy modeling, structural analysis)

**Key Components**:
```python
class ArxObjectProcessor:
    def extract_geometry(self, image_data: bytes) -> GeometryData:
        """Extract geometric primitives from floor plan images"""
        pass
    
    def calculate_bilt_reward(self, contribution: ContributionData) -> float:
        """Assess data quality and calculate BILT token reward"""
        pass
    
    def generate_ascii_representation(self, geometry: GeometryData) -> str:
        """Create ASCII art BIM representation"""
        pass
```

### 2.4 Frontend Progressive Web App (PWA)
**Purpose**: Multi-layer client interface with adaptive rendering

**Technology Stack**: Vanilla JavaScript, HTMX, Three.js
**Key Requirement**: No localStorage/sessionStorage usage (not supported in Claude.ai environment)

**Layer Implementation**:
```javascript
class ArxosRenderer {
    constructor(layer, precision = 'millimeter') {
        this.layer = layer;
        this.precision = precision;
        this.ws = new WebSocket('ws://arxos.com/ws');
    }
    
    switchPrecision(newPrecision) {
        this.precision = newPrecision;
        this.requestUpdate();
    }
    
    requestUpdate() {
        const request = {
            layer: this.layer,
            precision: this.precision,
            viewport: this.getCurrentViewport(),
            zoom_level: this.getZoomLevel()
        };
        this.ws.send(JSON.stringify(request));
    }
}
```

## 3. Six-Layer User Interface Architecture

### Layer 1: Full 3D Rendering (Heaviest)
- **Technology**: Three.js WebGL with PerspectiveCamera
- **Precision**: Millimeter to micrometer (pixel-limited)
- **Features**: Full 3D manipulation, material rendering, lighting
- **Target**: Architects, engineers with high-end devices

### Layer 2: AR Field Overlay (Heavy)
- **Technology**: ARKit/ARCore with spatial correlation
- **Precision**: Millimeter (AR tracking limited)
- **Features**: Real-time ArxObject overlay on physical space
- **Target**: Field workers, inspectors, technicians
- **Special Requirements**: Offline mode support, GPS correlation

### Layer 3: 2D Rendering (Medium-Heavy)
- **Technology**: Three.js with OrthographicCamera
- **Precision**: Centimeter to millimeter
- **Features**: Traditional floor plan view with interactive elements
- **Target**: Contractors, facility managers

### Layer 4: ASCII Art BIM in PWA/Mobile (Medium)
- **Technology**: HTML/CSS grid-based rendering
- **Precision**: Decimeter to meter (character grid limited)
- **Features**: Text-based building visualization with navigation
- **Target**: Low-bandwidth users, accessibility needs

### Layer 5: Pure Terminal ASCII (Light)
- **Technology**: Native terminal application
- **Precision**: Decimeter to meter
- **Features**: SSH-accessible, scriptable interface
- **Target**: System administrators, remote access

### Layer 6: CLI + AQL (Lightest)
- **Technology**: Command-line interface with Arxos Query Language
- **Precision**: **Full submicron access** (no rendering limitations)
- **Features**: Database-like queries, automation, raw data access
- **Target**: Power users, automated systems, API integrations

## 4. Submicron Precision Architecture

### 4.1 Data Storage Strategy
```json
{
  "arxobject_id": "hvac_unit_001",
  "base_coordinate": [10.0, 5.0, 2.0],
  "submicron_offset": [123, 456, 789],
  "precision_metadata": {
    "measurement_method": "laser_scanning",
    "accuracy_tolerance": 1e-9,
    "timestamp": "2025-08-27T10:30:00Z"
  },
  "lod_variants": {
    "submicron": "full_precision_data",
    "micrometer": "compressed_data",
    "millimeter": "simplified_geometry"
  }
}
```

### 4.2 Adaptive Level of Detail (LOD)
```go
func (r *RenderService) GetLODData(request RenderRequest) (*GeometryData, error) {
    switch request.Layer {
    case Layer3D, LayerAR:
        return r.getMillimeterPrecision(request)
    case Layer2D:
        return r.getCentimeterPrecision(request)
    case LayerASCII:
        return r.getMeterPrecision(request)
    case LayerCLI:
        return r.getSubmicronPrecision(request) // Full precision access
    }
}
```

### 4.3 Progressive Data Loading
- **Viewport Culling**: Only load ArxObjects in current view
- **Coarse-to-Fine**: Start with low precision, upgrade as user zooms
- **Predictive Caching**: Pre-load likely next precision levels

## 5. Real-Time Communication Architecture

### 5.1 WebSocket Protocol
```javascript
// Message structure for all layers
const wsMessage = {
    type: 'geometry_update',     // geometry_update, terminal_output, bilt_reward
    layer: '3d',                 // 3d, ar, 2d, ascii, terminal, cli
    precision: 'submicron',      // submicron, micrometer, millimeter, etc.
    data: {
        arxobjects: [...],
        metadata: {...},
        ascii_representation: "..." // for ascii layers
    }
};
```

### 5.2 Layer Switching Protocol
Users can dynamically switch between layers without losing session state:
```javascript
function switchLayer(newLayer) {
    const switchMessage = {
        type: 'layer_switch',
        from_layer: currentLayer,
        to_layer: newLayer,
        maintain_viewport: true,
        maintain_precision: false // reset to layer default
    };
    websocket.send(JSON.stringify(switchMessage));
}
```

## 6. BILT Token Integration

### 6.1 Contribution Tracking
```go
type Contribution struct {
    UserID       string    `json:"user_id"`
    ArxObjectID  string    `json:"arxobject_id"`
    DataType     string    `json:"data_type"`    // geometry, metadata, verification
    Precision    string    `json:"precision"`    // affects reward multiplier
    Quality      float64   `json:"quality"`      // 0.0-1.0 quality score
    BILTReward   float64   `json:"bilt_reward"`  // calculated tokens earned
    Timestamp    time.Time `json:"timestamp"`
}
```

### 6.2 Quality Assessment Pipeline
```python
def assess_contribution_quality(contribution: ContributionData) -> float:
    """
    Multi-factor quality assessment:
    - Geometric accuracy (laser scanning vs manual measurement)
    - Data completeness (all required fields populated)
    - Verification consistency (multiple user confirmation)
    - Precision level (submicron = higher reward multiplier)
    """
    base_score = calculate_geometric_accuracy(contribution)
    precision_multiplier = get_precision_multiplier(contribution.precision)
    verification_bonus = calculate_verification_bonus(contribution)
    
    return base_score * precision_multiplier + verification_bonus
```

## 7. Development Guidelines

### 7.1 Performance Standards
- **WebSocket latency**: < 100ms for layer switching
- **3D rendering**: Maintain 60fps for Layer 1
- **Memory usage**: < 512MB per concurrent user session
- **Precision calculations**: Use fixed-point arithmetic for financial calculations

### 7.2 Data Consistency Rules
- All coordinate systems must use consistent origin points
- Submicron precision must be maintained through entire pipeline
- Layer switching must preserve spatial relationships
- ArxObject IDs must remain constant across all layers

### 7.3 Testing Requirements
- **Unit tests**: Each layer rendering engine
- **Integration tests**: Cross-layer data consistency
- **Performance tests**: Concurrent user load testing
- **Precision tests**: Submicron accuracy validation
- **Mobile tests**: PWA performance on low-end devices

### 7.4 Security Considerations
- Implement rate limiting on file uploads
- Validate all user-contributed geometric data
- Encrypt sensitive building data at rest
- Use JWT tokens for API authentication
- Implement CORS policies for WebSocket connections

## 8. Deployment Architecture

### 8.1 Microservices Structure
```
├── core-engine/          (C binary, Docker container)
├── api-gateway/          (Go service, Kubernetes deployment)
├── ai-services/          (Python FastAPI, separate scaling)
├── websocket-service/    (Go service, sticky session load balancer)
├── pwa-frontend/         (Static files, CDN distribution)
└── cli-tools/           (Distributed binaries, package managers)
```

### 8.2 Scaling Strategy
- **Horizontal**: Load balance Go services behind nginx
- **Vertical**: Scale C engine based on computational demand
- **Geographic**: CDN distribution for PWA assets
- **Database**: Read replicas for data buyer API access

## 9. Future Considerations

### 9.1 Native Mobile Development
- iOS ARKit integration for enhanced Layer 2 experience
- Android ARCore support with cross-platform data synchronization
- Offline-first architecture for field usage

### 9.2 Data Monetization APIs
- Tiered access control for different data buyer categories
- Real-time data streaming for utility companies
- Batch export capabilities for insurance risk assessment
- Compliance reporting automation for regulatory bodies

### 9.3 Advanced Features
- Machine learning-driven ArxObject classification
- Predictive maintenance algorithms
- Energy simulation integration
- Structural analysis API endpoints

This architecture provides a scalable, performant foundation for the Arxos ecosystem while maintaining the flexibility to serve users across the complete spectrum of technical capability and hardware resources.
