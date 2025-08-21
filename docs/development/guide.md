# Development Guide

## 🎯 **Overview**

This guide provides comprehensive information for developers working on the ARXOS platform. It covers coding standards, development practices, testing strategies, and deployment procedures.

---

## 🏗️ **Architecture Principles**

### **Core Design Philosophy**
- **Simplicity First** - Prefer standard library over external packages
- **No Over-Engineering** - Avoid unnecessary abstractions
- **Explicit Over Implicit** - Clear, readable code
- **Minimal Dependencies** - Only add what's absolutely necessary

### **Technology Constraints**
- **Backend**: Go with Chi router only - no additional web frameworks
- **Frontend**: Vanilla JavaScript only - no React, Vue, Angular
- **Database**: PostgreSQL + PostGIS, Redis, SQLite
- **AI Service**: Python with OpenAI API integration

---

## 🔧 **Go Backend Development**

### **Code Organization**
```
core/backend/
├── main.go              # Application entry point
├── handlers/            # HTTP request handlers
├── models/              # Data models and database schema
├── services/            # Business logic layer
├── middleware/          # HTTP middleware (auth, CORS, etc.)
├── database/            # Database connection and migrations
├── utils/               # Utility functions and helpers
└── tests/               # Test files
```

### **Coding Standards**

#### **File Structure**
```go
// Package declaration
package handlers

// Imports (standard library first, then external)
import (
    "encoding/json"
    "net/http"
    "time"
    
    "github.com/go-chi/chi/v5"
    "github.com/your-org/arxos/models"
)

// Handler struct
type ArxObjectHandler struct {
    service *services.ArxObjectService
    logger  *log.Logger
}

// Handler methods
func (h *ArxObjectHandler) Create(w http.ResponseWriter, r *http.Request) {
    // Implementation
}
```

#### **Naming Conventions**
- **Packages**: lowercase, single word (e.g., `handlers`, `models`)
- **Functions**: PascalCase for exported, camelCase for private
- **Variables**: camelCase
- **Constants**: UPPER_SNAKE_CASE
- **Interfaces**: PascalCase with descriptive names

#### **Error Handling**
```go
// Always check errors
if err != nil {
    h.logger.Printf("Failed to create ArxObject: %v", err)
    http.Error(w, "Internal server error", http.StatusInternalServerError)
    return
}

// Use custom error types for specific errors
type ValidationError struct {
    Field   string `json:"field"`
    Message string `json:"message"`
}

// Return appropriate HTTP status codes
switch err.(type) {
case *ValidationError:
    http.Error(w, err.Error(), http.StatusBadRequest)
case *NotFoundError:
    http.Error(w, err.Error(), http.StatusNotFound)
default:
    http.Error(w, "Internal server error", http.StatusInternalServerError)
}
```

### **Database Operations**

#### **Using GORM**
```go
// Models
type ArxObject struct {
    ID        string                 `json:"id" gorm:"primaryKey"`
    Type      string                 `json:"type" gorm:"not null"`
    Data      map[string]interface{} `json:"data" gorm:"type:jsonb"`
    CreatedAt time.Time              `json:"created_at"`
    UpdatedAt time.Time              `json:"updated_at"`
}

// Queries
func (s *ArxObjectService) GetByID(id string) (*ArxObject, error) {
    var arxObject ArxObject
    result := s.db.Where("id = ?", id).First(&arxObject)
    if result.Error != nil {
        return nil, result.Error
    }
    return &arxObject, nil
}

// Spatial queries with PostGIS
func (s *ArxObjectService) GetInBoundingBox(bbox []float64) ([]ArxObject, error) {
    var arxObjects []ArxObject
    query := `SELECT * FROM arxobjects 
              WHERE ST_Intersects(geometry, ST_MakeEnvelope(?, ?, ?, ?, 4326))`
    
    result := s.db.Raw(query, bbox[0], bbox[1], bbox[2], bbox[3]).Scan(&arxObjects)
    return arxObjects, result.Error
}
```

### **API Design**

#### **RESTful Endpoints**
```go
// Chi router setup
func (h *ArxObjectHandler) Routes() chi.Router {
    r := chi.NewRouter()
    
    r.Get("/", h.List)           // GET /api/v1/arxobjects
    r.Post("/", h.Create)         // POST /api/v1/arxobjects
    r.Get("/{id}", h.GetByID)     // GET /api/v1/arxobjects/{id}
    r.Put("/{id}", h.Update)      // PUT /api/v1/arxobjects/{id}
    r.Delete("/{id}", h.Delete)   // DELETE /api/v1/arxobjects/{id}
    
    return r
}
```

#### **Request/Response Handling**
```go
func (h *ArxObjectHandler) Create(w http.ResponseWriter, r *http.Request) {
    // Parse request
    var req CreateArxObjectRequest
    if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
        http.Error(w, "Invalid request body", http.StatusBadRequest)
        return
    }
    
    // Validate request
    if err := req.Validate(); err != nil {
        http.Error(w, err.Error(), http.StatusBadRequest)
        return
    }
    
    // Business logic
    arxObject, err := h.service.Create(r.Context(), req)
    if err != nil {
        h.logger.Printf("Failed to create ArxObject: %v", err)
        http.Error(w, "Internal server error", http.StatusInternalServerError)
        return
    }
    
    // Response
    w.Header().Set("Content-Type", "application/json")
    w.WriteHeader(http.StatusCreated)
    json.NewEncoder(w).Encode(arxObject)
}
```

---

## 🎨 **Frontend Development**

### **Code Organization**
```
frontend/
├── index.html           # Main HTML file
├── css/                 # Stylesheets
│   ├── main.css        # Main styles
│   ├── components.css  # Component styles
│   └── themes.css      # Theme variations
├── js/                  # JavaScript files
│   ├── main.js         # Main application logic
│   ├── api.js          # API client
│   ├── three.js        # Three.js integration
│   ├── ar.js           # AR features
│   └── utils.js        # Utility functions
└── assets/              # Images, icons, 3D models
```

### **Coding Standards**

#### **JavaScript Structure**
```javascript
// Use ES6+ features
class ArxosApp {
    constructor() {
        this.api = new ArxosAPI();
        this.viewer = new ThreeJSViewer();
        this.ar = new ARManager();
        this.init();
    }
    
    async init() {
        try {
            await this.loadConfiguration();
            this.setupEventListeners();
            this.startViewer();
        } catch (error) {
            console.error('Failed to initialize app:', error);
        }
    }
    
    // Event handling
    setupEventListeners() {
        document.getElementById('upload-btn').addEventListener('click', 
            this.handleFileUpload.bind(this));
        
        window.addEventListener('resize', 
            this.handleResize.bind(this));
    }
}
```

#### **CSS Organization**
```css
/* Use CSS custom properties for theming */
:root {
    --primary-color: #2563eb;
    --secondary-color: #64748b;
    --background-color: #ffffff;
    --text-color: #1e293b;
    --border-color: #e2e8f0;
}

/* Component-based CSS */
.arxobject-card {
    background: var(--background-color);
    border: 1px solid var(--border-color);
    border-radius: 8px;
    padding: 16px;
    margin: 8px 0;
}

.arxobject-card:hover {
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
    transform: translateY(-2px);
    transition: all 0.2s ease;
}
```

### **Three.js Integration**

#### **3D Scene Management**
```javascript
class ThreeJSViewer {
    constructor(container) {
        this.container = container;
        this.scene = new THREE.Scene();
        this.camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
        this.renderer = new THREE.WebGLRenderer({ antialias: true });
        
        this.setupScene();
        this.setupLights();
        this.setupControls();
    }
    
    setupScene() {
        this.renderer.setSize(this.container.clientWidth, this.container.clientHeight);
        this.container.appendChild(this.renderer.domElement);
        
        // Add grid helper
        const gridHelper = new THREE.GridHelper(100, 100);
        this.scene.add(gridHelper);
        
        // Set camera position
        this.camera.position.set(50, 50, 50);
        this.camera.lookAt(0, 0, 0);
    }
    
    addArxObject(arxObject) {
        const geometry = this.createGeometry(arxObject);
        const material = this.createMaterial(arxObject);
        const mesh = new THREE.Mesh(geometry, material);
        
        // Set position from ArxObject coordinates
        mesh.position.set(arxObject.geometry.coordinates[0], 
                         arxObject.geometry.coordinates[1], 
                         arxObject.geometry.coordinates[2]);
        
        this.scene.add(mesh);
        return mesh;
    }
}
```

---

## 🐍 **Python AI Service Development**

### **Code Organization**
```
ai_service/
├── main.py              # FastAPI application entry point
├── models/              # Data models and schemas
├── processors/          # PDF/IFC processing logic
├── services/            # AI and external service integrations
├── utils/               # Utility functions
└── tests/               # Test files
```

### **Coding Standards**

#### **FastAPI Structure**
```python
from fastapi import FastAPI, HTTPException, UploadFile
from pydantic import BaseModel
from typing import List, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="ARXOS AI Service", version="1.0.0")

class IngestionRequest(BaseModel):
    building_id: str
    extract_symbols: bool = True
    confidence_threshold: float = 0.7

@app.post("/ingest")
async def ingest_document(
    file: UploadFile,
    request: IngestionRequest
):
    try:
        # Process file
        result = await process_document(file, request)
        return {"status": "success", "result": result}
    except Exception as e:
        logger.error(f"Failed to process document: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

#### **PDF Processing**
```python
class PDFProcessor:
    def __init__(self):
        self.ocr = self.setup_ocr()
        self.symbol_detector = self.setup_symbol_detector()
    
    async def process_pdf(self, file_path: str, options: dict) -> List[ArxObject]:
        # Extract text and images
        text_content = await self.extract_text(file_path)
        images = await self.extract_images(file_path)
        
        # Process content
        arx_objects = []
        
        # Extract symbols
        if options.get("extract_symbols", True):
            symbols = await self.detect_symbols(images)
            arx_objects.extend(self.create_symbol_objects(symbols))
        
        # Extract text-based objects
        text_objects = await self.extract_text_objects(text_content)
        arx_objects.extend(text_objects)
        
        return arx_objects
    
    async def detect_symbols(self, images: List[str]) -> List[Symbol]:
        symbols = []
        for image in images:
            # Use AI model for symbol detection
            detected = await self.symbol_detector.detect(image)
            symbols.extend(detected)
        return symbols
```

---

## 🧪 **Testing Strategy**

### **Go Testing**

#### **Unit Tests**
```go
// handlers/arxobject_test.go
package handlers

import (
    "testing"
    "net/http"
    "net/http/httptest"
    "strings"
)

func TestArxObjectHandler_Create(t *testing.T) {
    // Setup
    handler := &ArxObjectHandler{
        service: &mockArxObjectService{},
    }
    
    // Test data
    requestBody := `{"type":"electrical_outlet","name":"Test Outlet"}`
    req := httptest.NewRequest("POST", "/", strings.NewReader(requestBody))
    req.Header.Set("Content-Type", "application/json")
    w := httptest.NewRecorder()
    
    // Execute
    handler.Create(w, req)
    
    // Assert
    if w.Code != http.StatusCreated {
        t.Errorf("Expected status %d, got %d", http.StatusCreated, w.Code)
    }
    
    // Check response body
    var response ArxObject
    if err := json.NewDecoder(w.Body).Decode(&response); err != nil {
        t.Fatalf("Failed to decode response: %v", err)
    }
    
    if response.Type != "electrical_outlet" {
        t.Errorf("Expected type 'electrical_outlet', got '%s'", response.Type)
    }
}
```

#### **Integration Tests**
```go
func TestArxObjectAPI_Integration(t *testing.T) {
    // Setup test database
    db := setupTestDatabase(t)
    defer cleanupTestDatabase(t, db)
    
    // Create handler with test database
    handler := &ArxObjectHandler{
        service: services.NewArxObjectService(db),
    }
    
    // Test full CRUD cycle
    // ... implementation
}
```

### **Python Testing**

#### **Unit Tests**
```python
import pytest
from unittest.mock import Mock, patch
from processors.pdf_processor import PDFProcessor

class TestPDFProcessor:
    @pytest.fixture
    def processor(self):
        return PDFProcessor()
    
    @pytest.mark.asyncio
    async def test_symbol_detection(self, processor):
        # Mock AI service
        with patch.object(processor.symbol_detector, 'detect') as mock_detect:
            mock_detect.return_value = [
                Symbol(type="electrical_outlet", confidence=0.9)
            ]
            
            # Test symbol detection
            symbols = await processor.detect_symbols(["test_image.jpg"])
            
            assert len(symbols) == 1
            assert symbols[0].type == "electrical_outlet"
            assert symbols[0].confidence == 0.9
```

---

## 🚀 **Deployment**

### **Development Deployment**
```bash
# Backend
cd core/backend
go run main.go

# AI Service
cd ai_service
uvicorn main:app --reload --port 5000
```

### **Production Deployment**
```bash
# Build Go binary
cd core/backend
go build -o arxos-server

# Run with environment variables
export DB_URL="postgres://user:pass@localhost/arxos"
export REDIS_URL="redis://localhost:6379"
export AI_SERVICE_URL="http://localhost:5000"
export JWT_SECRET="your-secret-key"

./arxos-server
```

### **Environment Configuration**
```bash
# .env file
DB_URL=postgres://user:pass@localhost/arxos
REDIS_URL=redis://localhost:6379
AI_SERVICE_URL=http://localhost:5000
JWT_SECRET=your-secret-key
PORT=8080
LOG_LEVEL=info
CORS_ORIGINS=http://localhost:3000,https://yourdomain.com
```

---

## 📚 **Best Practices**

### **Code Quality**
- **Write tests** for all new functionality
- **Use linters** (gofmt, golint for Go; flake8, black for Python)
- **Document functions** with clear comments
- **Follow naming conventions** consistently

### **Performance**
- **Use connection pooling** for database connections
- **Implement caching** for frequently accessed data
- **Optimize queries** with proper indexing
- **Use lazy loading** for large datasets

### **Security**
- **Validate all inputs** from external sources
- **Use prepared statements** to prevent SQL injection
- **Implement proper authentication** and authorization
- **Sanitize user data** before rendering

### **Monitoring**
- **Log important events** with appropriate levels
- **Monitor performance metrics** (response times, error rates)
- **Set up health checks** for all services
- **Track user activity** for analytics

---

## 🔗 **Related Documentation**

- **Setup**: See [Development Setup](setup.md)
- **Architecture**: Review [Architecture Overview](../architecture/overview.md)
- **API**: Check [API Reference](../api/README.md)
- **Quick Start**: Get started with [Quick Start](../quick-start.md)

---

## 🆘 **Getting Help**

- **Code Reviews**: Submit pull requests for review
- **Architecture Questions**: Review [Architecture Overview](../architecture/overview.md)
- **API Issues**: Check [API Reference](../api/README.md)
- **Development Problems**: Use [Development Setup](setup.md)

**Happy coding! 🚀**
