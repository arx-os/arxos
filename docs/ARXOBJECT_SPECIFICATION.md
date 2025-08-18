# ArxObject Specification

## Overview

ArxObjects are the fundamental building blocks of the Arxos system - intelligent, self-aware data entities that represent every element in a building from entire campuses down to individual circuit traces. Unlike traditional geometric models, ArxObjects are **data-first entities** that understand their context, relationships, and confidence levels.

## Core Philosophy

### Intelligence Over Geometry
ArxObjects prioritize semantic understanding and relationships over geometric precision. They are self-aware entities that:
- Know what they represent in the building context
- Understand their relationships to other objects
- Communicate their confidence levels
- Improve through validation and learning

### Fractal Hierarchy
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

## Data Structure

### Core ArxObject Model

```go
type ArxObject struct {
    // Identity
    ID            string                 `json:"id" db:"id"`
    Type          string                 `json:"type" db:"type"`
    
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
}
```

### Confidence Score Structure

```go
type ConfidenceScore struct {
    Classification float64 `json:"classification"` // How certain about object type (0-1)
    Position       float64 `json:"position"`      // Spatial accuracy confidence (0-1)
    Properties     float64 `json:"properties"`    // Data accuracy confidence (0-1)
    Relationships  float64 `json:"relationships"` // Connection validity (0-1)
    Overall        float64 `json:"overall"`       // Weighted average (0-1)
}
```

### Relationship Model

```go
type Relationship struct {
    Type       string                 `json:"type"`       // Nature of relationship
    TargetID   string                 `json:"targetId"`   // Related ArxObject ID
    Confidence float64                `json:"confidence"` // Relationship certainty (0-1)
    Properties map[string]interface{} `json:"properties"` // Relationship-specific data
    Metadata   RelationshipMetadata   `json:"metadata"`   // Source and validation info
}
```

### Metadata Structure

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

## Object Types

### Structural Elements
```go
const (
    // Primary Structure
    TypeWall           = "wall"
    TypeColumn         = "column"
    TypeBeam           = "beam"
    TypeSlab           = "slab"
    TypeFoundation     = "foundation"
    TypeRoof           = "roof"
    
    // Openings
    TypeDoor           = "door"
    TypeWindow         = "window"
    TypeOpening        = "opening"
)
```

### Spatial Elements
```go
const (
    TypeBuilding       = "building"
    TypeFloor          = "floor"
    TypeRoom           = "room"
    TypeZone           = "zone"
    TypeArea           = "area"
    TypeCorridor       = "corridor"
    TypeStairwell      = "stairwell"
    TypeElevatorShaft  = "elevator_shaft"
)
```

### MEP Systems
```go
const (
    // Electrical
    TypeOutlet         = "electrical_outlet"
    TypeSwitch         = "electrical_switch"
    TypePanel          = "electrical_panel"
    TypeConduit        = "electrical_conduit"
    TypeLightFixture   = "light_fixture"
    
    // HVAC
    TypeDuct           = "hvac_duct"
    TypeVent           = "hvac_vent"
    TypeUnit           = "hvac_unit"
    TypeThermostat     = "thermostat"
    
    // Plumbing
    TypePipe           = "plumbing_pipe"
    TypeFixture        = "plumbing_fixture"
    TypeValve          = "valve"
    TypePump           = "pump"
)
```

### Equipment & Devices
```go
const (
    TypeEquipment      = "equipment"
    TypeSensor         = "sensor"
    TypeActuator       = "actuator"
    TypeController     = "controller"
    TypeNetworkDevice  = "network_device"
    TypeFireAlarm      = "fire_alarm"
    TypeSprinkler      = "sprinkler"
)
```

## Relationship Types

### Spatial Relationships
- `contains`: Object contains another (room contains outlet)
- `contained_by`: Object is contained by another
- `adjacent_to`: Objects share a boundary
- `above`: Object is above another
- `below`: Object is below another
- `connected_to`: Physical connection exists

### Functional Relationships
- `powers`: Electrical power relationship
- `controls`: Control system relationship
- `serves`: Service relationship (HVAC serves room)
- `monitors`: Monitoring relationship
- `part_of`: Component of larger system

### System Relationships
- `upstream`: Earlier in system flow
- `downstream`: Later in system flow
- `primary`: Primary connection
- `backup`: Backup/redundant connection
- `grouped_with`: Part of same logical group

## Data Properties

### Common Properties
```json
{
    "name": "Conference Room 201",
    "description": "Main conference room",
    "manufacturer": "Carrier",
    "model": "38YCC060",
    "serialNumber": "CN123456789",
    "installDate": "2023-06-15",
    "dimensions": {
        "length": 10.5,
        "width": 8.2,
        "height": 3.0,
        "units": "meters"
    },
    "capacity": {
        "value": 5.0,
        "units": "tons"
    },
    "status": "active",
    "condition": 0.85
}
```

### System-Specific Properties

#### Electrical
```json
{
    "voltage": 120,
    "amperage": 20,
    "phase": "single",
    "circuitNumber": "A-14",
    "panelID": "EP-2A"
}
```

#### HVAC
```json
{
    "airflow": {
        "value": 500,
        "units": "cfm"
    },
    "temperature": {
        "setpoint": 72,
        "units": "fahrenheit"
    },
    "zone": "Zone-2A"
}
```

#### Plumbing
```json
{
    "pipeSize": {
        "value": 2,
        "units": "inches"
    },
    "material": "copper",
    "pressure": {
        "value": 60,
        "units": "psi"
    },
    "flowRate": {
        "value": 10,
        "units": "gpm"
    }
}
```

## Render Hints

```go
type RenderHints struct {
    Style          RenderStyle           `json:"style"`
    Visibility     VisibilityRules       `json:"visibility"`
    Interactions   InteractionRules      `json:"interactions"`
    Annotations    []Annotation          `json:"annotations"`
}

type RenderStyle struct {
    Color          string   `json:"color"`           // Hex color
    Opacity        float64  `json:"opacity"`         // 0-1
    LineWidth      float64  `json:"lineWidth"`       // Pixels
    LineStyle      string   `json:"lineStyle"`       // solid, dashed, dotted
    FillPattern    string   `json:"fillPattern"`     // solid, hatch, none
    Icon           string   `json:"icon"`            // Icon identifier
    Label          string   `json:"label"`           // Display label
    LabelPosition  string   `json:"labelPosition"`   // top, bottom, center
}

type VisibilityRules struct {
    MinScale       float64  `json:"minScale"`        // Minimum zoom to show
    MaxScale       float64  `json:"maxScale"`        // Maximum zoom to show
    SystemFilter   []string `json:"systemFilter"`    // Show for these systems
    ConfidenceMin  float64  `json:"confidenceMin"`   // Min confidence to show
}
```

## Validation States

```go
type ValidationState string

const (
    ValidationPending   ValidationState = "pending"    // Needs validation
    ValidationPartial   ValidationState = "partial"    // Partially validated
    ValidationComplete  ValidationState = "complete"   // Fully validated
    ValidationConflict  ValidationState = "conflict"   // Conflicting data
)
```

## Quality Indicators

### Confidence Thresholds
- **High Confidence**: > 0.85 - Green indicators, minimal validation needed
- **Medium Confidence**: 0.60 - 0.85 - Yellow indicators, selective validation
- **Low Confidence**: < 0.60 - Red indicators, validation required

### Data Quality Metrics
```go
type DataQuality struct {
    Completeness   float64 `json:"completeness"`   // Required fields filled
    Consistency    float64 `json:"consistency"`    // Data consistency score
    Accuracy       float64 `json:"accuracy"`       // Validation accuracy
    Timeliness     float64 `json:"timeliness"`     // Data freshness
    Overall        float64 `json:"overall"`        // Weighted average
}
```

## Persistence & Storage

### Database Schema
```sql
CREATE TABLE arxobjects (
    id UUID PRIMARY KEY,
    building_id UUID REFERENCES buildings(id),
    parent_id UUID REFERENCES arxobjects(id),
    type VARCHAR(50) NOT NULL,
    data JSONB NOT NULL,
    render_hints JSONB,
    confidence JSONB NOT NULL,
    relationships JSONB[],
    metadata JSONB NOT NULL,
    geometry GEOMETRY(GEOMETRY, 4326),
    validation_state VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    -- Indexes for performance
    INDEX idx_type (type),
    INDEX idx_confidence ((confidence->>'overall')),
    INDEX idx_validation (validation_state),
    INDEX idx_spatial USING GIST (geometry)
);
```

### Serialization Formats

#### JSON Representation
```json
{
    "id": "arx_wall_001",
    "type": "wall",
    "data": {
        "material": "drywall",
        "thickness": 0.15,
        "height": 3.0,
        "fireRating": "1-hour"
    },
    "confidence": {
        "classification": 0.95,
        "position": 0.88,
        "properties": 0.75,
        "relationships": 0.82,
        "overall": 0.85
    },
    "relationships": [
        {
            "type": "adjacent_to",
            "targetId": "arx_room_101",
            "confidence": 0.90
        }
    ],
    "metadata": {
        "source": "pdf_extraction",
        "created": "2024-01-15T10:30:00Z",
        "validated": false
    }
}
```

## API Operations

### CRUD Operations
```go
// Create
POST /api/arxobjects
Body: ArxObject

// Read
GET /api/arxobjects/{id}
GET /api/arxobjects?building_id={id}&type={type}&min_confidence={0.7}

// Update
PUT /api/arxobjects/{id}
PATCH /api/arxobjects/{id}

// Delete
DELETE /api/arxobjects/{id}

// Bulk Operations
POST /api/arxobjects/batch
PUT /api/arxobjects/batch
```

### Validation Operations
```go
// Submit validation
POST /api/arxobjects/{id}/validate
Body: ValidationData

// Get validation history
GET /api/arxobjects/{id}/validations

// Propagate validation
POST /api/arxobjects/{id}/propagate
```

### Relationship Operations
```go
// Add relationship
POST /api/arxobjects/{id}/relationships
Body: Relationship

// Update relationship
PUT /api/arxobjects/{id}/relationships/{relationshipId}

// Remove relationship
DELETE /api/arxobjects/{id}/relationships/{relationshipId}
```

## Best Practices

### Creating ArxObjects
1. Always include confidence scores
2. Specify data source in metadata
3. Include relevant relationships
4. Use appropriate type classification
5. Provide render hints for visualization

### Validation Strategy
1. Focus on low-confidence objects first
2. Validate relationships alongside objects
3. Propagate validations to similar objects
4. Track validation history
5. Update confidence scores after validation

### Performance Optimization
1. Use batch operations for bulk creation
2. Index frequently queried properties
3. Implement spatial queries for geometric operations
4. Cache high-confidence objects
5. Use appropriate confidence thresholds for filtering

## Future Enhancements

### Planned Features
- Machine learning-based confidence improvement
- Automatic relationship inference
- Pattern-based validation propagation
- Real-time collaborative validation
- AR visualization support

### Research Areas
- Semantic understanding enhancement
- Cross-building pattern learning
- Automated quality assessment
- Predictive maintenance integration
- Digital twin synchronization