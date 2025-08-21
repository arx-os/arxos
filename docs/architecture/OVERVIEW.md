# ARXOS Architecture Overview

## 🎯 **System Vision**

ARXOS is **"Google Maps for Buildings"** - a building information model (BIM) system that enables infinite zoom from campus-level down to individual circuit traces. The system transforms various building data formats (PDF, IFC, DWG, HEIC, LiDAR) into intelligent, self-aware building components called **ArxObjects**.

## 🏗️ **High-Level Architecture**

```
┌─────────────────────────────────────────────────────────────┐
│                    ARXOS System                            │
├─────────────────────────────────────────────────────────────┤
│  Frontend Layer (Vanilla JS + Three.js + 8th Wall)        │
│  ├── HTML5 + CSS3 + Vanilla JavaScript                    │
│  ├── HTMX for dynamic updates                             │
│  ├── Three.js for 3D visualization                        │
│  └── 8th Wall for web-based AR                            │
├─────────────────────────────────────────────────────────────┤
│  Backend Layer (Go + Chi Router)                          │
│  ├── REST API endpoints                                   │
│  ├── WebSocket server for real-time updates               │
│  ├── JWT authentication                                   │
│  ├── Database operations (PostgreSQL + Redis)             │
│  └── ArxObject management                                 │
├─────────────────────────────────────────────────────────────┤
│  AI Service Layer (Python)                                │
│  ├── PDF/IFC/DWG/HEIC/LiDAR processing                    │
│  ├── Symbol recognition and classification                 │
│  ├── Coordinate system transformation                      │
│  └── ArxObject generation                                 │
├─────────────────────────────────────────────────────────────┤
│  Data Layer                                               │
│  ├── PostgreSQL + PostGIS (spatial data)                  │
│  ├── Redis (sessions + cache)                             │
│  └── SQLite (local/offline storage)                       │
└─────────────────────────────────────────────────────────────┘
```

## 🔧 **Technology Stack**

### **Backend (Go)**
- **Language**: Go 1.21+
- **Router**: Chi (github.com/go-chi/chi/v5)
- **Database**: PostgreSQL 13+ with PostGIS extension
- **Cache**: Redis 6+
- **ORM**: GORM for database operations
- **Authentication**: JWT with golang.org/x/crypto

### **Frontend (Vanilla JavaScript)**
- **Framework**: No frameworks - pure vanilla JS
- **3D Graphics**: Three.js for 3D visualization
- **AR Framework**: 8th Wall for web-based AR
- **Dynamic Updates**: HTMX for server-side rendering
- **Styling**: Pure CSS3, no preprocessors
- **Graphics**: SVG for vector graphics, Canvas API for 2D

### **AI Service (Python)**
- **Language**: Python 3.9+
- **AI Integration**: OpenAI API
- **Image Processing**: OpenCV, PIL
- **PDF Processing**: PyPDF2, pdf2image
- **OCR**: Tesseract integration
- **Communication**: REST API with Go backend

## 🏛️ **Core Components**

### **1. ArxObject Engine**
The heart of ARXOS - intelligent, self-aware building components that:
- Understand their context and relationships
- Maintain confidence scores for data quality
- Support fractal scaling (10^7 to 10^-4 scale levels)
- Enable real-time collaboration and validation

### **2. PDF Ingestion Pipeline**
AI-powered conversion of building plans:
- Symbol recognition and classification
- Coordinate system transformation
- ArxObject generation with confidence scoring
- Real-time processing feedback

### **3. 3D/AR Visualization**
Interactive building exploration:
- Three.js-based 3D rendering
- 8th Wall AR integration
- Lazy loading for performance
- Multi-scale navigation

### **4. Real-time Collaboration**
Live building data updates:
- WebSocket connections
- Real-time ArxObject updates
- Field validation integration
- Multi-user collaboration

## 📊 **Data Flow**

### **PDF Ingestion Flow**
```
PDF Upload → AI Service → Symbol Recognition → Coordinate Transform → ArxObject Creation → Database Storage → Frontend Update
```

### **Real-time Updates**
```
Field Changes → AR App → Backend API → Database Update → WebSocket Broadcast → Frontend Update → 3D/AR Refresh
```

### **User Interaction**
```
User Action → Frontend → Backend API → ArxObject Engine → Database → Response → Frontend Update
```

## 🎯 **Key Design Principles**

### **1. Simplicity First**
- **Single binary deployment** for Go backend
- **No containerization complexity** (no Kubernetes, Docker Compose)
- **Minimal dependencies** - prefer standard library
- **Direct deployment** with minimal moving parts

### **2. Performance Focus**
- **Lazy loading** for large building models
- **Spatial indexing** with PostGIS
- **Redis caching** for hot data
- **WebSocket optimization** for real-time updates

### **3. Scalability Strategy**
- **Horizontal scaling** via multiple Go instances
- **Database read replicas** for heavy queries
- **CDN integration** for static assets
- **Load balancing** for high availability

### **4. Security & Compliance**
- **JWT authentication** with dual account types
- **Environment-based configuration** (no hardcoded secrets)
- **CORS configuration** for API access
- **Secure WebSocket connections**

## 🗺️ **Fractal Scaling System**

ARXOS supports 10 levels of zoom, from continental infrastructure to nanometer precision:

```
Scale Level    Range           Example Objects
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
10^7          GLOBAL          Power grids, pipelines
10^6          REGIONAL        State infrastructure  
10^5          MUNICIPAL       City utilities
10^4          CAMPUS          Multi-building sites
10^3          BUILDING        Individual structures
10^2          FLOOR           Floor plates
10^1          ROOM            Individual spaces
10^0          COMPONENT       Equipment, fixtures
10^-3         CIRCUIT         PCB boards
10^-4         TRACE           Copper paths
```

## 🔄 **System Integration Points**

### **External Services**
- **OpenAI API** - AI-powered symbol recognition
- **8th Wall** - AR framework integration
- **CMMS Systems** - Maintenance management integration
- **Email Services** - Notification delivery

### **Data Formats**
- **Input**: PDF, IFC, DWG, HEIC, LiDAR point clouds
- **Output**: ArxObjects, 3D models, AR overlays, reports
- **Exchange**: JSON APIs, WebSocket events, file exports

## 🚀 **Deployment Architecture**

### **Production Setup**
```
┌─────────────────┐
│   Web Client    │
│  (Browser/AR)   │
└────────┬────────┘
         │ HTTPS
┌────────▼────────┐
│   Go Backend    │
│ (Single Binary) │
└────┬──────┬─────┘
     │      │
┌────▼──┐ ┌▼──────┐
│ Redis │ │ PostgreSQL │
└───────┘ └────────┘
```

### **Development Setup**
- **Local Go binary** with hot reload
- **Local PostgreSQL + PostGIS**
- **Local Redis instance**
- **Python AI service** with auto-restart
- **Frontend hot reload** for rapid development

## 📈 **Performance Characteristics**

### **Target Metrics**
- **PDF Processing**: < 30 seconds for typical floor plans
- **3D Rendering**: 60 FPS with 1000+ ArxObjects
- **API Response**: < 100ms for 95% of requests
- **Real-time Updates**: < 50ms latency for WebSocket events

### **Optimization Strategies**
- **Spatial indexing** for building queries
- **Lazy loading** for large models
- **Connection pooling** for database access
- **Asset compression** for frontend delivery

---

**Next Steps**: 
- **Understand ArxObjects**: Read [ArxObject System](arxobjects.md)
- **Explore Components**: See [System Components](components.md)
- **Start Developing**: Follow [Development Setup](../development/setup.md)
