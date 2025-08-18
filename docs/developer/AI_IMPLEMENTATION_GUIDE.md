# AI Implementation Guide

## Overview

This guide provides step-by-step instructions for implementing the Arxos AI conversion system. The implementation follows a phased approach, starting with basic PDF extraction and progressively adding intelligence layers.

## Prerequisites

### Environment Setup
```bash
# Python environment (AI Service)
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Go environment (Backend)
go mod download
go mod verify

# PostgreSQL with PostGIS
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

# Redis (Optional, for caching)
redis-server --daemonize yes
```

### Required Libraries

#### Python (AI Service)
```python
# requirements.txt
pymupdf==1.23.8          # PDF processing
opencv-python==4.8.1     # Computer vision
numpy==1.24.3           # Numerical operations
scipy==1.11.4           # Scientific computing
pillow==10.1.0          # Image processing
tesseract==5.3.3        # OCR
scikit-learn==1.3.2     # Pattern recognition
shapely==2.0.2          # Geometric operations
```

#### Go (Backend)
```go
// go.mod
require (
    github.com/go-chi/chi/v5 v5.0.10
    github.com/lib/pq v1.10.9
    github.com/jmoiron/sqlx v1.3.5
    github.com/go-redis/redis/v8 v8.11.5
    github.com/gorilla/websocket v1.5.1
)
```

## Phase 1: Basic PDF Extraction (Week 1-2)

### Step 1.1: PDF Vector Extraction
```python
# pdf_extractor.py
import fitz  # PyMuPDF
import json

class PDFExtractor:
    def __init__(self):
        self.confidence_base = 0.95  # Vector data is highly reliable
    
    def extract_vectors(self, pdf_path):
        """Extract vector graphics from PDF"""
        doc = fitz.open(pdf_path)
        vectors = []
        
        for page_num, page in enumerate(doc):
            # Get page dimensions
            rect = page.rect
            width, height = rect.width, rect.height
            
            # Extract vector paths
            paths = page.get_drawings()
            
            for path in paths:
                vector = {
                    'type': 'path',
                    'points': path['items'],
                    'stroke': path.get('stroke'),
                    'fill': path.get('fill'),
                    'width': path.get('width', 1),
                    'page': page_num,
                    'confidence': self.confidence_base
                }
                vectors.append(vector)
        
        return vectors
```

### Step 1.2: Line Detection & Grouping
```python
# line_detector.py
import cv2
import numpy as np

class LineDetector:
    def __init__(self):
        self.min_line_length = 10
        self.max_line_gap = 5
    
    def detect_lines(self, image):
        """Detect lines using Hough transform"""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 50, 150, apertureSize=3)
        
        lines = cv2.HoughLinesP(
            edges,
            rho=1,
            theta=np.pi/180,
            threshold=100,
            minLineLength=self.min_line_length,
            maxLineGap=self.max_line_gap
        )
        
        return self.group_lines(lines)
    
    def group_lines(self, lines):
        """Group collinear lines into walls"""
        if lines is None:
            return []
        
        grouped = []
        for line in lines:
            x1, y1, x2, y2 = line[0]
            
            # Check if line belongs to existing group
            added = False
            for group in grouped:
                if self.is_collinear(group, line):
                    group['lines'].append(line)
                    added = True
                    break
            
            if not added:
                grouped.append({
                    'lines': [line],
                    'type': 'wall_candidate',
                    'confidence': 0.7
                })
        
        return grouped
```

### Step 1.3: Basic ArxObject Creation
```python
# arxobject_factory.py
import uuid
from datetime import datetime

class ArxObjectFactory:
    def __init__(self):
        self.default_confidence = 0.5
    
    def create_from_line(self, line_group):
        """Create ArxObject from detected line"""
        return {
            'id': f"arx_{uuid.uuid4().hex[:8]}",
            'type': self.classify_line(line_group),
            'data': {
                'points': line_group['lines'],
                'length': self.calculate_length(line_group),
                'thickness': self.estimate_thickness(line_group)
            },
            'confidence': {
                'classification': line_group.get('confidence', self.default_confidence),
                'position': 0.8,  # Vector data has good position confidence
                'properties': 0.5,  # Properties are estimated
                'relationships': 0.3,  # Relationships not yet established
                'overall': 0.65
            },
            'relationships': [],
            'metadata': {
                'source': 'pdf_extraction',
                'created': datetime.now().isoformat(),
                'validated': False
            }
        }
    
    def classify_line(self, line_group):
        """Classify line as wall, door, window, etc."""
        # Simple classification based on length and pattern
        length = self.calculate_length(line_group)
        
        if length > 100:  # Long lines are likely walls
            return 'wall'
        elif length < 30:  # Short lines might be doors
            return 'door_candidate'
        else:
            return 'unknown_line'
```

## Phase 2: Pattern Recognition (Week 3-4)

### Step 2.1: Symbol Detection
```python
# symbol_detector.py
import cv2
import numpy as np

class SymbolDetector:
    def __init__(self):
        self.load_symbol_library()
    
    def load_symbol_library(self):
        """Load standard architectural symbols"""
        self.symbols = {
            'door': cv2.imread('symbols/door.png', 0),
            'window': cv2.imread('symbols/window.png', 0),
            'toilet': cv2.imread('symbols/toilet.png', 0),
            'sink': cv2.imread('symbols/sink.png', 0),
            'stairs': cv2.imread('symbols/stairs.png', 0)
        }
    
    def detect_symbols(self, image):
        """Detect architectural symbols using template matching"""
        detected = []
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        for symbol_type, template in self.symbols.items():
            # Multi-scale template matching
            for scale in [0.8, 1.0, 1.2]:
                scaled_template = cv2.resize(
                    template, 
                    None, 
                    fx=scale, 
                    fy=scale
                )
                
                result = cv2.matchTemplate(
                    gray, 
                    scaled_template, 
                    cv2.TM_CCOEFF_NORMED
                )
                
                threshold = 0.8
                locations = np.where(result >= threshold)
                
                for pt in zip(*locations[::-1]):
                    detected.append({
                        'type': symbol_type,
                        'position': pt,
                        'scale': scale,
                        'confidence': result[pt[1], pt[0]]
                    })
        
        return self.non_max_suppression(detected)
```

### Step 2.2: Room Detection
```python
# room_detector.py
from shapely.geometry import Polygon, Point

class RoomDetector:
    def __init__(self):
        self.min_room_area = 100  # Minimum area to be considered a room
    
    def detect_rooms(self, walls):
        """Detect rooms from wall segments"""
        rooms = []
        
        # Find closed polygons formed by walls
        polygons = self.find_closed_polygons(walls)
        
        for polygon in polygons:
            if polygon.area > self.min_room_area:
                room = {
                    'id': f"room_{uuid.uuid4().hex[:8]}",
                    'type': 'room',
                    'boundary': polygon,
                    'area': polygon.area,
                    'perimeter': polygon.length,
                    'confidence': self.calculate_room_confidence(polygon)
                }
                rooms.append(room)
        
        return rooms
    
    def find_closed_polygons(self, walls):
        """Find closed polygons from wall segments"""
        # Implementation of polygon detection algorithm
        # This is simplified - real implementation would be more complex
        polygons = []
        
        # Group connected walls
        wall_groups = self.group_connected_walls(walls)
        
        for group in wall_groups:
            if self.forms_closed_loop(group):
                points = self.extract_points(group)
                polygon = Polygon(points)
                if polygon.is_valid:
                    polygons.append(polygon)
        
        return polygons
```

### Step 2.3: Text Extraction & OCR
```python
# text_extractor.py
import pytesseract
from PIL import Image

class TextExtractor:
    def __init__(self):
        self.confidence_threshold = 0.6
    
    def extract_text(self, image, regions=None):
        """Extract text from image using OCR"""
        text_elements = []
        
        if regions:
            # Extract text from specific regions
            for region in regions:
                cropped = self.crop_region(image, region)
                text_data = self.ocr_region(cropped)
                if text_data['confidence'] > self.confidence_threshold:
                    text_elements.append({
                        'text': text_data['text'],
                        'position': region,
                        'confidence': text_data['confidence'],
                        'type': self.classify_text(text_data['text'])
                    })
        else:
            # Extract all text from image
            text_data = pytesseract.image_to_data(
                image, 
                output_type=pytesseract.Output.DICT
            )
            text_elements = self.process_ocr_data(text_data)
        
        return text_elements
    
    def classify_text(self, text):
        """Classify text as room label, dimension, etc."""
        text = text.upper()
        
        # Room labels
        if any(room_type in text for room_type in ['BEDROOM', 'BATHROOM', 'KITCHEN', 'OFFICE']):
            return 'room_label'
        
        # Dimensions
        if any(unit in text for unit in ['MM', 'CM', 'M', 'FT', 'IN']):
            return 'dimension'
        
        # Room numbers
        if text.isdigit() or (len(text) < 5 and any(c.isdigit() for c in text)):
            return 'room_number'
        
        return 'annotation'
```

## Phase 3: Relationship Building (Week 5-6)

### Step 3.1: Spatial Relationships
```python
# relationship_builder.py
from scipy.spatial import distance

class RelationshipBuilder:
    def __init__(self):
        self.proximity_threshold = 10  # pixels
    
    def build_relationships(self, arxobjects):
        """Build relationships between ArxObjects"""
        for i, obj1 in enumerate(arxobjects):
            for obj2 in arxobjects[i+1:]:
                relationships = self.detect_relationships(obj1, obj2)
                
                for rel in relationships:
                    obj1['relationships'].append({
                        'type': rel['type'],
                        'target_id': obj2['id'],
                        'confidence': rel['confidence']
                    })
                    
                    # Add inverse relationship
                    obj2['relationships'].append({
                        'type': self.get_inverse_relationship(rel['type']),
                        'target_id': obj1['id'],
                        'confidence': rel['confidence']
                    })
    
    def detect_relationships(self, obj1, obj2):
        """Detect relationships between two objects"""
        relationships = []
        
        # Check adjacency
        if self.are_adjacent(obj1, obj2):
            relationships.append({
                'type': 'adjacent_to',
                'confidence': 0.9
            })
        
        # Check containment
        if self.contains(obj1, obj2):
            relationships.append({
                'type': 'contains',
                'confidence': 0.85
            })
        
        # Check connection
        if self.are_connected(obj1, obj2):
            relationships.append({
                'type': 'connected_to',
                'confidence': 0.8
            })
        
        return relationships
```

### Step 3.2: System Topology
```python
# topology_builder.py
class TopologyBuilder:
    def __init__(self):
        self.system_patterns = self.load_system_patterns()
    
    def build_system_topology(self, arxobjects):
        """Build system topology from objects"""
        systems = {
            'electrical': [],
            'hvac': [],
            'plumbing': [],
            'structural': []
        }
        
        # Classify objects into systems
        for obj in arxobjects:
            system = self.identify_system(obj)
            if system:
                systems[system].append(obj)
        
        # Build topology for each system
        for system_name, system_objects in systems.items():
            self.build_system_connections(system_objects, system_name)
    
    def build_system_connections(self, objects, system_type):
        """Build connections within a system"""
        # Sort objects by position for logical flow
        sorted_objects = self.sort_by_flow(objects, system_type)
        
        for i, obj in enumerate(sorted_objects[:-1]):
            next_obj = sorted_objects[i + 1]
            
            # Create system connection
            obj['relationships'].append({
                'type': 'downstream',
                'target_id': next_obj['id'],
                'system': system_type,
                'confidence': 0.7
            })
            
            next_obj['relationships'].append({
                'type': 'upstream',
                'target_id': obj['id'],
                'system': system_type,
                'confidence': 0.7
            })
```

## Phase 4: Confidence & Validation (Week 7-8)

### Step 4.1: Confidence Calculation
```python
# confidence_calculator.py
class ConfidenceCalculator:
    def __init__(self):
        self.weights = {
            'classification': 0.35,
            'position': 0.30,
            'properties': 0.20,
            'relationships': 0.15
        }
    
    def calculate_confidence(self, arxobject):
        """Calculate multi-dimensional confidence"""
        confidence = arxobject.get('confidence', {})
        
        # Calculate individual dimensions
        confidence['classification'] = self.calculate_classification_confidence(arxobject)
        confidence['position'] = self.calculate_position_confidence(arxobject)
        confidence['properties'] = self.calculate_properties_confidence(arxobject)
        confidence['relationships'] = self.calculate_relationship_confidence(arxobject)
        
        # Calculate overall confidence
        confidence['overall'] = sum(
            confidence[key] * self.weights[key] 
            for key in self.weights
        )
        
        arxobject['confidence'] = confidence
        return confidence
    
    def calculate_classification_confidence(self, obj):
        """Calculate classification confidence"""
        # Based on detection method and pattern matching
        if obj['metadata']['source'] == 'vector':
            base = 0.9
        elif obj['metadata']['source'] == 'ocr':
            base = 0.7
        else:
            base = 0.5
        
        # Adjust based on validation
        if obj['metadata'].get('validated'):
            base = min(1.0, base + 0.2)
        
        return base
```

### Step 4.2: Validation Strategy Generation
```python
# validation_strategy.py
class ValidationStrategyGenerator:
    def __init__(self):
        self.critical_types = ['wall', 'room', 'floor']
        self.system_critical = ['electrical_panel', 'hvac_unit']
    
    def generate_strategy(self, arxobjects, building_type):
        """Generate strategic validation plan"""
        strategy = {
            'critical': [],
            'high_impact': [],
            'normal': [],
            'optional': []
        }
        
        # Identify critical validations
        scale_validation = self.find_scale_validation(arxobjects)
        if scale_validation:
            strategy['critical'].append(scale_validation)
        
        # Find pattern validations
        patterns = self.identify_patterns(arxobjects)
        for pattern in patterns[:5]:  # Top 5 patterns
            strategy['high_impact'].append({
                'type': 'pattern_validation',
                'pattern': pattern,
                'impact': self.calculate_pattern_impact(pattern),
                'objects': pattern['instances']
            })
        
        # System validations
        for system in self.system_critical:
            system_objects = [o for o in arxobjects if o['type'] == system]
            if system_objects:
                strategy['high_impact'].append({
                    'type': 'system_validation',
                    'system': system,
                    'objects': system_objects[:3]  # Validate first 3
                })
        
        return strategy
```

## Phase 5: Integration (Week 9-10)

### Step 5.1: Go Backend Integration
```go
// ai_service.go
package services

import (
    "bytes"
    "encoding/json"
    "fmt"
    "io"
    "mime/multipart"
    "net/http"
)

type AIConversionService struct {
    pythonServiceURL string
    httpClient      *http.Client
}

func NewAIConversionService(pythonURL string) *AIConversionService {
    return &AIConversionService{
        pythonServiceURL: pythonURL,
        httpClient: &http.Client{
            Timeout: 60 * time.Second,
        },
    }
}

func (s *AIConversionService) ConvertPDF(pdfPath string, metadata BuildingMetadata) (*ConversionResult, error) {
    // Create multipart form
    var buf bytes.Buffer
    writer := multipart.NewWriter(&buf)
    
    // Add PDF file
    file, err := os.Open(pdfPath)
    if err != nil {
        return nil, err
    }
    defer file.Close()
    
    part, err := writer.CreateFormFile("pdf", filepath.Base(pdfPath))
    if err != nil {
        return nil, err
    }
    io.Copy(part, file)
    
    // Add metadata
    metadataJSON, _ := json.Marshal(metadata)
    writer.WriteField("metadata", string(metadataJSON))
    writer.Close()
    
    // Send request to Python service
    req, err := http.NewRequest("POST", 
        fmt.Sprintf("%s/convert", s.pythonServiceURL), 
        &buf)
    if err != nil {
        return nil, err
    }
    req.Header.Set("Content-Type", writer.FormDataContentType())
    
    resp, err := s.httpClient.Do(req)
    if err != nil {
        return nil, err
    }
    defer resp.Body.Close()
    
    // Parse response
    var result ConversionResult
    if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
        return nil, err
    }
    
    return &result, nil
}
```

### Step 5.2: Database Storage
```go
// arxobject_store.go
package database

import (
    "database/sql"
    "encoding/json"
    "github.com/jmoiron/sqlx"
)

type ArxObjectStore struct {
    db *sqlx.DB
}

func (s *ArxObjectStore) BatchInsert(buildingID string, objects []ArxObject) error {
    tx, err := s.db.Beginx()
    if err != nil {
        return err
    }
    defer tx.Rollback()
    
    query := `
        INSERT INTO arxobjects (
            id, building_id, type, data, confidence, 
            relationships, metadata, geometry
        ) VALUES (
            :id, :building_id, :type, :data::jsonb, 
            :confidence::jsonb, :relationships::jsonb[], 
            :metadata::jsonb, ST_GeomFromGeoJSON(:geometry)
        )`
    
    for _, obj := range objects {
        params := map[string]interface{}{
            "id":           obj.ID,
            "building_id":  buildingID,
            "type":         obj.Type,
            "data":         jsonMarshal(obj.Data),
            "confidence":   jsonMarshal(obj.Confidence),
            "relationships": jsonMarshal(obj.Relationships),
            "metadata":     jsonMarshal(obj.Metadata),
            "geometry":     obj.GeometryGeoJSON(),
        }
        
        if _, err := tx.NamedExec(query, params); err != nil {
            return err
        }
    }
    
    return tx.Commit()
}
```

### Step 5.3: Real-time Updates
```go
// validation_stream.go
package handlers

import (
    "encoding/json"
    "fmt"
    "net/http"
)

func (h *ValidationHandler) StreamUpdates(w http.ResponseWriter, r *http.Request) {
    // Set SSE headers
    w.Header().Set("Content-Type", "text/event-stream")
    w.Header().Set("Cache-Control", "no-cache")
    w.Header().Set("Connection", "keep-alive")
    
    buildingID := chi.URLParam(r, "buildingID")
    updates := h.validationService.Subscribe(buildingID)
    
    flusher, ok := w.(http.Flusher)
    if !ok {
        http.Error(w, "SSE not supported", http.StatusInternalServerError)
        return
    }
    
    for update := range updates {
        data, _ := json.Marshal(update)
        fmt.Fprintf(w, "data: %s\n\n", data)
        flusher.Flush()
    }
}
```

## Phase 6: Optimization (Week 11-12)

### Step 6.1: Performance Optimization
```python
# optimizer.py
import multiprocessing
from concurrent.futures import ThreadPoolExecutor

class PDFOptimizer:
    def __init__(self):
        self.num_workers = multiprocessing.cpu_count()
    
    def process_parallel(self, pdf_path):
        """Process PDF pages in parallel"""
        doc = fitz.open(pdf_path)
        num_pages = len(doc)
        
        with ThreadPoolExecutor(max_workers=self.num_workers) as executor:
            # Process pages in parallel
            futures = []
            for page_num in range(num_pages):
                future = executor.submit(
                    self.process_page, 
                    pdf_path, 
                    page_num
                )
                futures.append(future)
            
            # Collect results
            results = []
            for future in futures:
                results.append(future.result())
        
        return self.merge_results(results)
```

### Step 6.2: Caching Strategy
```python
# cache_manager.py
import redis
import hashlib
import pickle

class CacheManager:
    def __init__(self):
        self.redis_client = redis.Redis(
            host='localhost',
            port=6379,
            decode_responses=False
        )
        self.ttl = 3600  # 1 hour
    
    def get_or_compute(self, key, compute_func, *args, **kwargs):
        """Get from cache or compute and cache"""
        # Generate cache key
        cache_key = self.generate_key(key, args, kwargs)
        
        # Try to get from cache
        cached = self.redis_client.get(cache_key)
        if cached:
            return pickle.loads(cached)
        
        # Compute and cache
        result = compute_func(*args, **kwargs)
        self.redis_client.setex(
            cache_key, 
            self.ttl, 
            pickle.dumps(result)
        )
        
        return result
```

## Testing & Validation

### Unit Tests
```python
# test_arxobject_factory.py
import unittest
from arxobject_factory import ArxObjectFactory

class TestArxObjectFactory(unittest.TestCase):
    def setUp(self):
        self.factory = ArxObjectFactory()
    
    def test_create_wall_object(self):
        line_group = {
            'lines': [[[0, 0, 100, 0]]],
            'confidence': 0.8
        }
        
        obj = self.factory.create_from_line(line_group)
        
        self.assertEqual(obj['type'], 'wall')
        self.assertGreater(obj['confidence']['overall'], 0.5)
        self.assertIn('id', obj)
```

### Integration Tests
```go
// ai_service_test.go
package services

import (
    "testing"
    "github.com/stretchr/testify/assert"
)

func TestAIConversionService(t *testing.T) {
    service := NewAIConversionService("http://localhost:5000")
    
    result, err := service.ConvertPDF(
        "test_data/sample_floor_plan.pdf",
        BuildingMetadata{
            Type: "office",
            Size: "medium",
        },
    )
    
    assert.NoError(t, err)
    assert.NotNil(t, result)
    assert.Greater(t, len(result.ArxObjects), 0)
    assert.Greater(t, result.OverallConfidence, 0.5)
}
```

## Deployment

### Docker Configuration
```dockerfile
# Dockerfile.ai
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY ai_service/ .

# Run service
CMD ["python", "main.py"]
```

### Docker Compose
```yaml
# docker-compose.yml
version: '3.8'

services:
  postgres:
    image: postgis/postgis:15-3.3
    environment:
      POSTGRES_DB: arxos
      POSTGRES_USER: arxos
      POSTGRES_PASSWORD: arxos
    volumes:
      - postgres_data:/var/lib/postgresql/data
    
  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
  
  ai_service:
    build:
      context: .
      dockerfile: Dockerfile.ai
    ports:
      - "5000:5000"
    environment:
      REDIS_URL: redis://redis:6379
      DATABASE_URL: postgresql://arxos:arxos@postgres/arxos
    depends_on:
      - postgres
      - redis
  
  backend:
    build:
      context: .
      dockerfile: Dockerfile.backend
    ports:
      - "8080:8080"
    environment:
      DATABASE_URL: postgresql://arxos:arxos@postgres/arxos
      REDIS_URL: redis://redis:6379
      AI_SERVICE_URL: http://ai_service:5000
    depends_on:
      - postgres
      - redis
      - ai_service

volumes:
  postgres_data:
  redis_data:
```

## Monitoring & Debugging

### Logging Configuration
```python
# logging_config.py
import logging
import json

class StructuredLogger:
    def __init__(self, name):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)
        
        handler = logging.StreamHandler()
        handler.setFormatter(self.JsonFormatter())
        self.logger.addHandler(handler)
    
    class JsonFormatter(logging.Formatter):
        def format(self, record):
            log_obj = {
                'timestamp': self.formatTime(record),
                'level': record.levelname,
                'logger': record.name,
                'message': record.getMessage(),
                'metadata': getattr(record, 'metadata', {})
            }
            return json.dumps(log_obj)
    
    def log_conversion(self, pdf_path, result):
        self.logger.info(
            'PDF conversion completed',
            extra={
                'metadata': {
                    'pdf': pdf_path,
                    'objects_created': len(result.arxobjects),
                    'confidence': result.overall_confidence,
                    'duration': result.processing_time
                }
            }
        )
```

### Performance Monitoring
```go
// metrics.go
package monitoring

import (
    "github.com/prometheus/client_golang/prometheus"
)

var (
    ConversionDuration = prometheus.NewHistogramVec(
        prometheus.HistogramOpts{
            Name: "arxos_conversion_duration_seconds",
            Help: "PDF conversion duration in seconds",
        },
        []string{"building_type"},
    )
    
    ObjectsCreated = prometheus.NewCounterVec(
        prometheus.CounterOpts{
            Name: "arxos_objects_created_total",
            Help: "Total number of ArxObjects created",
        },
        []string{"type"},
    )
    
    ConfidenceDistribution = prometheus.NewHistogramVec(
        prometheus.HistogramOpts{
            Name: "arxos_confidence_distribution",
            Help: "Distribution of confidence scores",
            Buckets: []float64{0.1, 0.3, 0.5, 0.7, 0.85, 0.95, 1.0},
        },
        []string{"object_type"},
    )
)

func init() {
    prometheus.MustRegister(ConversionDuration)
    prometheus.MustRegister(ObjectsCreated)
    prometheus.MustRegister(ConfidenceDistribution)
}
```

## Troubleshooting

### Common Issues

1. **Low Confidence Scores**
   - Check PDF quality (vector vs raster)
   - Verify symbol library completeness
   - Adjust detection thresholds

2. **Missing Relationships**
   - Increase proximity threshold
   - Check polygon closure detection
   - Verify coordinate transformations

3. **Performance Issues**
   - Enable parallel processing
   - Implement caching
   - Optimize database queries

4. **Memory Issues**
   - Process large PDFs in chunks
   - Implement streaming for results
   - Use memory profiling tools

## Next Steps

1. **Implement Pattern Learning**
   - Store validated patterns
   - Apply patterns to new buildings
   - Improve confidence through learning

2. **Add Mobile Validation**
   - Build mobile-friendly UI
   - Implement AR visualization
   - Enable offline validation

3. **Enhance AI Intelligence**
   - Train custom models
   - Implement building-type templates
   - Add semantic understanding

4. **Scale for Production**
   - Implement queue-based processing
   - Add horizontal scaling
   - Optimize for cloud deployment