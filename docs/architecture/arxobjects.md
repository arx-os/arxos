# ArxObject System

## 🎯 **Overview**

ArxObjects are the fundamental building blocks of the ARXOS system - intelligent, self-aware data entities that represent every element in a building from entire campuses down to individual circuit traces. Unlike traditional geometric models, ArxObjects are **data-first entities** that understand their context, relationships, and confidence levels.

## 🏗️ **Core Philosophy**

### **Intelligence Over Geometry**
ArxObjects prioritize semantic understanding and relationships over geometric precision. They are self-aware entities that:
- **Know what they represent** in the building context
- **Understand their relationships** to other objects
- **Communicate their confidence levels** for data quality
- **Improve through validation** and learning from field data

### **Fractal Hierarchy**
ArxObjects operate across 10 scale levels, from continental infrastructure to nanometer-precision circuit traces:

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

## 📊 **Data Structure**

### **Core ArxObject Model**

```go
type ArxObject struct {
    // Identity
    ID            string                 `json:"id" db:"id"`
    Type          string                 `json:"type" db:"type"`
    Name          string                 `json:"name" db:"name"`
    
    // Intelligent Data
    Data          map[string]interface{} `json:"data" db:"data"`
    RenderHints   *RenderHints          `json:"renderHints,omitempty" db:"render_hints"`
    
    // Confidence & Quality
    Confidence    ConfidenceScore       `json:"confidence" db:"confidence"`
    
    // Relationships & Context
    Relationships []Relationship        `json:"relationships" db:"relationships"`
    
    // Metadata & Provenance
    Metadata      Metadata              `json:"metadata" db:"metadata"`
    
    // Spatial Representation (Optional)
    Geometry      *Geometry             `json:"geometry,omitempty" db:"geometry"`
    
    // System Classification
    System        string                `json:"system" db:"system"`
    DetailLevel   int                   `json:"detailLevel" db:"detail_level"`
}
```

### **Confidence Score Structure**

```go
type ConfidenceScore struct {
    Classification float64 `json:"classification"` // How certain about object type (0-1)
    Position       float64 `json:"position"`      // Spatial accuracy confidence (0-1)
    Properties     float64 `json:"properties"`    // Data accuracy confidence (0-1)
    Relationships  float64 `json:"relationships"` // Connection validity (0-1)
    Overall        float64 `json:"overall"`       // Weighted average (0-1)
}
```

### **Relationship Model**

```go
type Relationship struct {
    Type       string                 `json:"type"`       // Nature of relationship
    TargetID   string                 `json:"targetId"`   // Related ArxObject ID
    Confidence float64                `json:"confidence"` // Relationship certainty (0-1)
    Properties map[string]interface{} `json:"properties"` // Relationship-specific data
    Metadata   RelationshipMetadata   `json:"metadata"`   // Source and validation info
}
```

### **Metadata Structure**

```go
type Metadata struct {
    Source       string    `json:"source"`       // Origin (pdf, field, inference, etc.)
    SourceDetail string    `json:"sourceDetail"` // Specific source info
    Created      time.Time `json:"created"`      // Creation timestamp
    LastModified time.Time `json:"lastModified"` // Last update
    ModifiedBy   string    `json:"modifiedBy"`   // User/system that modified
    Version      int       `json:"version"`      // Version number
    Validated    bool      `json:"validated"`    // Field validation status
    ValidatedBy  string    `json:"validatedBy"`  // Validator identity
    ValidatedAt  time.Time `json:"validatedAt"`  // Validation timestamp
}
```

## 🏷️ **System Classification**

### **Building Systems**
ArxObjects are classified by the building system they belong to:

- **`structural`** - Walls, beams, columns, foundations
- **`electrical`** - Outlets, switches, panels, wiring
- **`mechanical`** - HVAC, plumbing, fire protection
- **`architectural`** - Doors, windows, finishes, furniture
- **`telecommunications`** - Data, phone, security systems
- **`specialty`** - Medical, laboratory, industrial equipment

### **Detail Level Classification**
Objects have a detail level that determines rendering complexity:

- **`0`** - Basic shape (simple geometry)
- **`1`** - Standard detail (typical equipment)
- **`2`** - High detail (complex components)
- **`3`** - Component level (internal parts)
- **`4`** - Molecular level (individual components)

## 🔗 **Relationship Types**

### **Physical Connections**
- **`feeds`** - Power, data, or fluid flow
- **`contains`** - Enclosure relationships
- **`supports`** - Structural support
- **`adjacent`** - Spatial proximity
- **`parallel`** - Similar orientation

### **Functional Relationships**
- **`controls`** - Control system relationships
- **`monitors`** - Sensing and monitoring
- **`maintains`** - Maintenance dependencies
- **`replaces`** - Alternative components

### **Example Relationships**
```json
{
  "type": "feeds",
  "targetId": "panel-001",
  "confidence": 0.95,
  "properties": {
    "voltage": "120V",
    "amperage": "20A",
    "circuit": "A1"
  }
}
```

## 🎨 **Rendering & Visualization**

### **Render Hints**
ArxObjects include hints for optimal visualization:

```go
type RenderHints struct {
    Color         string  `json:"color"`         // Primary color
    Opacity       float64 `json:"opacity"`       // Transparency (0-1)
    Scale         float64 `json:"scale"`         // Size multiplier
    Rotation      []float64 `json:"rotation"`    // 3D rotation
    Visible       bool    `json:"visible"`       // Show/hide
    Highlight     bool    `json:"highlight"`     // Highlight state
    Icon          string  `json:"icon"`          // Icon identifier
}
```

### **Geometry Representation**
Spatial data can be represented in multiple formats:

- **`point`** - Single coordinate location
- **`line`** - Linear features (walls, pipes)
- **`polygon`** - Area features (rooms, equipment)
- **`mesh`** - 3D geometry for complex objects
- **`pointcloud`** - LiDAR or scan data

## 🔍 **Confidence Assessment**

### **Confidence Factors**

#### **Classification Confidence**
- **High (0.8-1.0)**: Clear symbol recognition, multiple confirmations
- **Medium (0.5-0.8)**: Probable identification, some uncertainty
- **Low (0.0-0.5)**: Uncertain classification, needs validation

#### **Position Confidence**
- **High (0.8-1.0)**: Precise coordinates, multiple reference points
- **Medium (0.5-0.8)**: Approximate location, some uncertainty
- **Low (0.0-0.5)**: Rough estimate, needs field validation

#### **Property Confidence**
- **High (0.8-1.0)**: Clear specifications, manufacturer data
- **Medium (0.5-0.8)**: Estimated values, typical specifications
- **Low (0.0-0.5)**: Unknown properties, needs investigation

### **Confidence Calculation**
```go
func (c *ConfidenceScore) CalculateOverall() float64 {
    weights := map[string]float64{
        "classification": 0.3,
        "position":       0.3,
        "properties":     0.2,
        "relationships":  0.2,
    }
    
    overall := c.Classification * weights["classification"] +
               c.Position * weights["position"] +
               c.Properties * weights["properties"] +
               c.Relationships * weights["relationships"]
    
    c.Overall = overall
    return overall
}
```

## 📈 **Validation & Learning**

### **Field Validation Process**
1. **Field worker** identifies ArxObject in AR/3D view
2. **Validation data** collected (photos, measurements, notes)
3. **Confidence scores** updated based on field data
4. **Relationships** verified and corrected
5. **Metadata** updated with validation source

### **Learning from Validation**
- **Symbol recognition** improves with more examples
- **Coordinate accuracy** refines with field measurements
- **Property confidence** increases with manufacturer data
- **Relationship patterns** emerge from validated connections

### **Validation Workflow**
```
Field Discovery → AR Validation → Data Update → Confidence Boost → System Learning
```

## 🚀 **Performance Optimization**

### **Lazy Loading Strategy**
- **Viewport-based loading** - Only load visible ArxObjects
- **Detail level scaling** - Show appropriate detail for zoom level
- **Relationship caching** - Cache frequently accessed connections
- **Spatial indexing** - Use PostGIS for efficient spatial queries

### **Rendering Optimization**
- **Level of Detail (LOD)** - Different detail for different distances
- **Frustum culling** - Only render visible objects
- **Instance rendering** - Batch similar objects
- **Texture atlasing** - Combine multiple textures

## 🔧 **API Operations**

### **CRUD Operations**
```go
// Create new ArxObject
POST /api/v1/arxobjects
{
  "type": "electrical_outlet",
  "name": "Receptacle A1",
  "system": "electrical",
  "data": {...},
  "geometry": {...}
}

// Retrieve ArxObject
GET /api/v1/arxobjects/{id}

// Update ArxObject
PUT /api/v1/arxobjects/{id}

// Delete ArxObject
DELETE /api/v1/arxobjects/{id}
```

### **Query Operations**
```go
// Spatial queries
GET /api/v1/arxobjects?bbox={x1,y1,x2,y2}

// System filtering
GET /api/v1/arxobjects?system=electrical

// Confidence filtering
GET /api/v1/arxobjects?min_confidence=0.8

// Relationship queries
GET /api/v1/arxobjects/{id}/relationships
```

---

**Next Steps**:
- **Explore Components**: See [System Components](components.md)
- **Understand API**: Check [API Reference](../api/README.md)
- **Start Developing**: Follow [Development Guide](../development/guide.md)
