# AI Conversion Architecture

## Overview

The Arxos AI Conversion System transforms building plans (PDFs, images, CAD files) into intelligent ArxObject models using confidence-aware processing and strategic validation. This architecture prioritizes **data intelligence over geometric perfection**, creating self-aware building components that understand their relationships and context.

## Core Philosophy

### Data-First Approach
ArxObjects are intelligent data entities that render themselves, not geometric primitives. Building knowledge emerges from ArxObject relationships and patterns rather than manual modeling.

### Progressive Accuracy Model
- Initial AI approximations with honest confidence assessment
- Strategic field validation focusing on high-impact verifications
- Continuous improvement through human feedback integration
- Pattern learning that propagates across similar buildings

### Confidence-Aware Processing
Every extraction, classification, and relationship includes multi-dimensional confidence scoring, enabling the system to communicate uncertainties and prioritize validations strategically.

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Frontend (HTMX + Canvas)                 │
│  • Upload Interface  • Validation Dashboard  • 3D Viewer     │
└────────────────────┬────────────────────────────────────────┘
                     │ REST API / SSE
┌────────────────────┴────────────────────────────────────────┐
│                    Go Backend (Chi Framework)                │
│  • ArxObject Service  • Validation Service  • AI Gateway    │
└────────────────────┬────────────────────────────────────────┘
                     │ gRPC / REST
┌────────────────────┴────────────────────────────────────────┐
│                  Python AI Conversion Service                │
│  • PDF Processing  • Computer Vision  • Pattern Recognition  │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────┴────────────────────────────────────────┐
│                    PostGIS Spatial Database                  │
│  • ArxObjects  • Relationships  • Confidence  • Validation   │
└─────────────────────────────────────────────────────────────┘
```

## AI Conversion Pipeline

### Stage 1: PDF Quality Assessment
```python
class PDFQualityAssessor:
    def assess(self, pdf_path):
        return {
            'extractability': 0.0-1.0,  # How well can we extract data
            'vector_content': 0.0-1.0,  # Ratio of vector vs raster
            'text_quality': 0.0-1.0,    # OCR potential
            'scale_detection': bool,     # Can we determine scale
            'complexity': 'low/medium/high'
        }
```

### Stage 2: Multi-Modal Extraction
- **Vector Extraction**: Direct path and line data from PDF
- **Text/OCR Processing**: Room labels, dimensions, annotations
- **Computer Vision**: Pattern recognition for symbols and equipment
- **Hybrid Approach**: Combining all methods with confidence weighting

### Stage 3: Pattern Recognition
```python
class PatternRecognizer:
    def recognize(self, extracted_data):
        return {
            'walls': self.detect_walls(extracted_data),
            'rooms': self.detect_rooms(extracted_data),
            'doors': self.detect_doors(extracted_data),
            'equipment': self.detect_equipment(extracted_data),
            'text_labels': self.extract_labels(extracted_data)
        }
```

### Stage 4: ArxObject Factory
Creates intelligent objects with appropriate confidence levels:
```python
def create_arxobject(element, context):
    return ArxObject(
        id=generate_uuid(),
        type=classify_element(element),
        data=extract_properties(element),
        confidence=ConfidenceScore(
            classification=calculate_classification_confidence(element),
            position=calculate_position_confidence(element),
            properties=calculate_property_confidence(element),
            relationships=0.5  # Initial relationship confidence
        ),
        relationships=infer_relationships(element, context),
        metadata=Metadata(source='ai_conversion', created=now())
    )
```

### Stage 5: Strategic Validation Planning
AI generates prioritized validation tasks based on impact analysis:
```python
def generate_validation_strategy(arxobjects):
    return ValidationStrategy(
        critical_validations=[  # Must verify
            establish_scale(),
            verify_main_systems(),
            confirm_critical_equipment()
        ],
        high_impact_validations=[  # High ROI
            validate_typical_floor(),
            measure_key_dimensions(),
            verify_room_functions()
        ],
        optional_validations=[  # Nice to have
            confirm_minor_details(),
            validate_aesthetic_elements()
        ]
    )
```

## Integration Architecture

### Go Backend Integration

```go
// AI Conversion Service Interface
type AIConversionService interface {
    ConvertPDF(path string, metadata BuildingMetadata) (*ConversionResult, error)
    GenerateValidationStrategy(objects []ArxObject) (*ValidationStrategy, error)
    ProcessValidation(validation *FieldValidation) (*ValidationImpact, error)
}

// Conversion Result Structure
type ConversionResult struct {
    ArxObjects         []ArxObject         `json:"arxobjects"`
    OverallConfidence  float64            `json:"overall_confidence"`
    Uncertainties      []Uncertainty      `json:"uncertainties"`
    ValidationStrategy *ValidationStrategy `json:"validation_strategy"`
    ProcessingMetrics  ProcessingMetrics  `json:"metrics"`
}
```

### Real-time Updates
```go
// Server-Sent Events for live validation feedback
func (h *ValidationHandler) StreamValidationUpdates(w http.ResponseWriter, r *http.Request) {
    flusher, ok := w.(http.Flusher)
    if !ok {
        http.Error(w, "SSE not supported", http.StatusInternalServerError)
        return
    }
    
    w.Header().Set("Content-Type", "text/event-stream")
    w.Header().Set("Cache-Control", "no-cache")
    
    updates := h.validationService.Subscribe(buildingID)
    for update := range updates {
        fmt.Fprintf(w, "data: %s\n\n", jsonMarshal(update))
        flusher.Flush()
    }
}
```

### Database Schema
```sql
-- ArxObjects with confidence metadata
CREATE TABLE arxobjects (
    id UUID PRIMARY KEY,
    building_id UUID REFERENCES buildings(id),
    type VARCHAR(50) NOT NULL,
    data JSONB NOT NULL,
    render_hints JSONB,
    confidence JSONB NOT NULL,  -- Multi-dimensional confidence
    relationships JSONB[],
    metadata JSONB NOT NULL,
    geometry GEOMETRY(GEOMETRY, 4326),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Validation tracking
CREATE TABLE validations (
    id UUID PRIMARY KEY,
    arxobject_id UUID REFERENCES arxobjects(id),
    validation_type VARCHAR(50),
    old_confidence JSONB,
    new_confidence JSONB,
    impact_score FLOAT,
    validated_by VARCHAR(100),
    validated_at TIMESTAMP DEFAULT NOW()
);
```

## Performance Optimizations

### Batch Processing
- Process multiple PDFs in parallel
- Batch ArxObject insertions (1000+ objects at once)
- Cached pattern recognition for common symbols

### Spatial Indexing
```sql
CREATE INDEX idx_arxobjects_spatial ON arxobjects USING GIST (geometry);
CREATE INDEX idx_arxobjects_confidence ON arxobjects ((confidence->>'overall'));
CREATE INDEX idx_arxobjects_type ON arxobjects (type);
```

### Caching Strategy
- Redis for frequently accessed ArxObjects
- Tile-based caching for rendered floor plans
- Pattern library caching for symbol recognition

## Monitoring & Analytics

### Key Metrics
- **Conversion Speed**: PDFs processed per minute
- **Confidence Distribution**: Average confidence by object type
- **Validation Impact**: Confidence improvement per validation
- **Pattern Learning Rate**: Accuracy improvement over time

### Quality Assurance
```python
class QualityMonitor:
    def track_metrics(self, conversion_result):
        metrics = {
            'total_objects': len(conversion_result.arxobjects),
            'avg_confidence': calculate_average_confidence(),
            'low_confidence_objects': count_low_confidence(),
            'validation_coverage': calculate_validation_coverage(),
            'processing_time': conversion_result.metrics.duration
        }
        self.publish_metrics(metrics)
```

## Security Considerations

### Input Validation
- PDF size limits (max 100MB)
- Malware scanning for uploaded files
- Rate limiting per user/organization

### Data Privacy
- Tenant isolation for multi-tenant deployments
- Encryption of sensitive building data
- Audit logging for all conversions and validations

## Future Enhancements

### Phase 1: Current Implementation
- Basic PDF to ArxObject conversion
- Manual validation interface
- Confidence visualization

### Phase 2: Intelligence Layer
- Pattern learning from validations
- Building type templates
- Automated confidence improvement

### Phase 3: Mobile Integration
- iPhone AR validation app
- Real-time 3D model assembly
- Offline validation capability

### Phase 4: Enterprise Features
- Multi-building batch processing
- Cross-building pattern learning
- Integration with existing BIM systems

## Conclusion

This AI conversion architecture represents a paradigm shift in building digitization, moving from perfect geometric modeling to intelligent, confidence-aware data entities that improve through strategic human validation. The system's strength lies in its honest assessment of AI limitations while maximizing human productivity through targeted validation efforts.