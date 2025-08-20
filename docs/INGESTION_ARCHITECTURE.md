# Arxos Ingestion Pipeline Architecture

## Overview
Convert any building data format into confidence-scored ArxObjects.

## Core Principle
Each format has different confidence levels and data richness:
- **IFC/Revit**: High confidence (95%), rich metadata
- **DWG/DXF**: High confidence (90%), good geometry
- **PDF**: Medium confidence (60-80%), requires interpretation
- **Images**: Low confidence (40-60%), requires AI/ML
- **Excel/CSV**: High confidence for data, no geometry

## Ingestion Pipeline

```
Input File → Format Detector → Parser → ArxObject Generator → Confidence Scorer → Database
                                  ↓
                            Validation Queue
```

## Format-Specific Strategies

### 1. PDF Ingestion
**Current State**: Using PyMuPDF + OpenCV
**Improvements Needed**:
- Vector extraction for precise walls
- Text extraction for room labels
- Symbol recognition for doors/windows
- Layer separation (electrical, plumbing, etc.)

**Confidence Factors**:
- Vector drawings: 80% base confidence
- Raster/scanned: 60% base confidence
- Text labels found: +10%
- Consistent scale: +10%

### 2. DWG/DXF (AutoCAD)
**Strategy**: Use ODA (Open Design Alliance) or LibreDWG
**Data Available**:
- Precise geometry
- Layer information (crucial!)
- Block definitions (reusable components)
- Attributes and metadata

**ArxObject Mapping**:
```python
LAYER_MAPPING = {
    'A-WALL': ArxObjectType.WALL,
    'A-DOOR': ArxObjectType.DOOR,
    'E-LITE': ArxObjectType.LIGHT_FIXTURE,
    'E-POWR': ArxObjectType.OUTLET,
    'P-FIXT': ArxObjectType.PLUMBING_FIXTURE,
    'M-HVAC': ArxObjectType.HVAC_UNIT,
}
```

### 3. IFC (Industry Foundation Classes)
**Strategy**: Use IfcOpenShell
**Data Available**:
- Complete building hierarchy
- Rich property sets
- Relationships already defined
- Material information

**ArxObject Mapping**:
```python
IFC_MAPPING = {
    'IfcWall': ArxObjectType.WALL,
    'IfcDoor': ArxObjectType.DOOR,
    'IfcWindow': ArxObjectType.WINDOW,
    'IfcSpace': ArxObjectType.ROOM,
    'IfcBuildingElementProxy': ArxObjectType.EQUIPMENT,
}
```

### 4. Images (HEIC/JPEG/PNG)
**Strategy**: Multi-stage processing
1. **Perspective Correction**: Fix skewed photos
2. **OCR**: Extract text labels
3. **Line Detection**: Find walls
4. **Symbol Recognition**: Identify doors, windows
5. **Scale Detection**: Find dimension lines

**Confidence Boosters**:
- Multiple photos of same area: Cross-validate
- GPS metadata: Confirm building location
- Timestamp: Track construction progress

### 5. Excel/CSV
**Strategy**: Template matching
**Common Templates**:
- Asset registers
- Equipment lists
- Room schedules
- Maintenance logs

**ArxObject Generation**:
```python
def process_asset_list(csv_data):
    for row in csv_data:
        arx_obj = ArxObject(
            type=map_asset_type(row['Category']),
            data={
                'manufacturer': row['Manufacturer'],
                'model': row['Model'],
                'serial': row['Serial Number'],
                'location': row['Location'],
            },
            confidence=ConfidenceScore(
                classification=0.95,  # Explicit data
                position=0.3,  # Only room-level
                properties=0.95,  # Direct from source
            )
        )
```

### 6. Point Cloud (LAS/LAZ/E57)
**Strategy**: Clustering and classification
1. Ground/floor detection
2. Wall plane extraction
3. Ceiling detection
4. MEP element clustering

**Challenges**:
- Huge file sizes
- Occlusion (hidden elements)
- Noise reduction

## Unified Ingestion API

```python
class UnifiedIngester:
    def ingest(self, file_path: str) -> ConversionResult:
        # Detect format
        format_type = self.detect_format(file_path)
        
        # Select appropriate processor
        processor = self.get_processor(format_type)
        
        # Process file
        raw_data = processor.extract(file_path)
        
        # Convert to ArxObjects
        arx_objects = processor.to_arxobjects(raw_data)
        
        # Score confidence
        arx_objects = self.score_confidence(arx_objects, format_type)
        
        # Identify validation needs
        validation_queue = self.identify_validation_needs(arx_objects)
        
        return ConversionResult(
            objects=arx_objects,
            validation_needed=validation_queue,
            format=format_type,
            confidence_summary=self.summarize_confidence(arx_objects)
        )
```

## Confidence Scoring by Format

| Format | Base Confidence | Geometry Precision | Metadata Richness | Relationship Detection |
|--------|----------------|-------------------|-------------------|----------------------|
| IFC    | 95%            | Exact             | Complete          | Explicit             |
| Revit  | 95%            | Exact             | Complete          | Explicit             |
| DWG    | 90%            | Exact             | Good              | Layer-based          |
| DXF    | 85%            | Exact             | Limited           | Layer-based          |
| PDF    | 60-80%         | Good-Fair         | Limited           | Inferred             |
| Image  | 40-60%         | Approximate       | OCR-dependent     | None                 |
| Excel  | 95% (data)     | None              | Excellent         | Explicit (if present)|
| LiDAR  | 70-90%         | Excellent         | None              | Spatial only         |

## Validation Priority Algorithm

```python
def calculate_validation_priority(obj: ArxObject) -> float:
    priority = 0.0
    
    # Critical systems get higher priority
    if obj.type in [ELECTRICAL_PANEL, FIRE_ALARM, EMERGENCY_EXIT]:
        priority += 0.5
    
    # Low confidence increases priority
    priority += (1.0 - obj.confidence.overall) * 0.3
    
    # High query frequency increases priority
    priority += obj.metadata.query_count * 0.1
    
    # Connected to many objects increases priority
    priority += min(len(obj.relationships) * 0.02, 0.2)
    
    return priority
```

## Implementation Phases

### Phase 1: Core Formats (Current Sprint)
- [x] PDF (basic implementation exists)
- [ ] Improve PDF with vector extraction
- [ ] DWG/DXF support
- [ ] IFC support
- [ ] Image with AI/OCR

### Phase 2: Enhanced Processing
- [ ] Multi-file correlation (same building, different formats)
- [ ] Automatic scale detection
- [ ] Symbol library learning
- [ ] Pattern recognition across buildings

### Phase 3: Advanced Formats
- [ ] Revit native files
- [ ] Point cloud processing
- [ ] COBie spreadsheets
- [ ] Energy models (gbXML)

### Phase 4: Intelligence Layer
- [ ] Format quality assessment
- [ ] Automatic format selection (best available)
- [ ] Hybrid processing (combine multiple formats)
- [ ] Confidence improvement through correlation

## Success Metrics

1. **Extraction Rate**: Objects found vs. manual count
2. **Confidence Distribution**: % of objects > 70% confidence
3. **Processing Speed**: Files per minute
4. **Validation Reduction**: % needing field validation
5. **Format Coverage**: % of customer files processable

## Next Steps

1. Improve PDF vector extraction
2. Add DWG/DXF parser
3. Integrate IFC library
4. Build unified API
5. Create test suite with real building files