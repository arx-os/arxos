# PDF to 3D Workflow

This document describes the PDF to 3D conversion workflow, where PDF floor plans, architectural drawings, and building documentation are processed to create accurate 3D building models and ArxObjects.

## Overview

The PDF to 3D workflow transforms 2D building documentation into intelligent 3D models through progressive reality construction. This process combines computer vision, machine learning, and spatial reasoning to extract building elements and create a hierarchical ArxObject structure.

## Workflow Stages

### 1. Document Ingestion

#### Supported Formats
```yaml
supported_formats:
  pdf:
    - "Floor plans"
    - "Architectural drawings"
    - "MEP schematics"
    - "Site plans"
    
  image:
    - "PNG (high resolution)"
    - "JPEG (high quality)"
    - "TIFF (uncompressed)"
    - "HEIC (iOS photos)"
    
  cad:
    - "DWG (AutoCAD)"
    - "DXF (Drawing Exchange)"
    - "IFC (Industry Foundation Classes)"
    
  point_cloud:
    - "LAS/LAZ (LiDAR)"
    - "E57 (ASTM standard)"
    - "PTS (Point cloud)"
```

#### Ingestion Process
```bash
# Ingest PDF floor plan
arx ingest pdf --file "floor_plan.pdf" --building "main" --floor "1"

# Ingest with metadata
arx ingest pdf --file "electrical_plan.pdf" \
  --building "main" \
  --floor "1" \
  --system "electrical" \
  --confidence "high" \
  --source "architect"

# Batch ingestion
arx ingest batch --directory "building_plans/" --building "main"
```

### 2. Document Analysis

#### Computer Vision Pipeline
```python
# Document analysis pipeline
class DocumentAnalyzer:
    def __init__(self):
        self.ocr_engine = OCREngine()
        self.layout_analyzer = LayoutAnalyzer()
        self.element_detector = ElementDetector()
        self.text_extractor = TextExtractor()
    
    def analyze_document(self, document_path: str) -> DocumentAnalysis:
        # Load document
        document = self.load_document(document_path)
        
        # Extract text and layout
        text_data = self.ocr_engine.extract_text(document)
        layout_data = self.layout_analyzer.analyze_layout(document)
        
        # Detect building elements
        elements = self.element_detector.detect_elements(document)
        
        # Extract metadata
        metadata = self.extract_metadata(document, text_data)
        
        return DocumentAnalysis(
            text=text_data,
            layout=layout_data,
            elements=elements,
            metadata=metadata
        )
```

#### Layout Recognition
```python
# Layout analysis for floor plans
class LayoutAnalyzer:
    def analyze_layout(self, document: Document) -> LayoutData:
        # Detect page structure
        page_structure = self.detect_page_structure(document)
        
        # Identify drawing areas
        drawing_areas = self.identify_drawing_areas(document)
        
        # Detect grid systems
        grid_system = self.detect_grid_system(document)
        
        # Identify scale indicators
        scale_info = self.detect_scale_indicators(document)
        
        # Detect north arrow and orientation
        orientation = self.detect_orientation(document)
        
        return LayoutData(
            page_structure=page_structure,
            drawing_areas=drawing_areas,
            grid_system=grid_system,
            scale_info=scale_info,
            orientation=orientation
        )
```

### 3. Element Detection

#### Building Element Recognition
```python
# Building element detection
class ElementDetector:
    def __init__(self):
        self.wall_detector = WallDetector()
        self.door_detector = DoorDetector()
        self.window_detector = WindowDetector()
        self.room_detector = RoomDetector()
        self.system_detector = SystemDetector()
    
    def detect_elements(self, document: Document) -> List[DetectedElement]:
        elements = []
        
        # Detect structural elements
        walls = self.wall_detector.detect(document)
        elements.extend(walls)
        
        doors = self.door_detector.detect(document)
        elements.extend(doors)
        
        windows = self.window_detector.detect(document)
        elements.extend(windows)
        
        # Detect spatial elements
        rooms = self.room_detector.detect(document, walls)
        elements.extend(rooms)
        
        # Detect system elements
        electrical = self.system_detector.detect_electrical(document)
        elements.extend(electrical)
        
        hvac = self.system_detector.detect_hvac(document)
        elements.extend(hvac)
        
        plumbing = self.system_detector.detect_plumbing(document)
        elements.extend(plumbing)
        
        return elements
```

#### Wall Detection Algorithm
```python
# Wall detection using computer vision
class WallDetector:
    def detect(self, document: Document) -> List[DetectedWall]:
        # Convert to grayscale
        gray = cv2.cvtColor(document.image, cv2.COLOR_BGR2GRAY)
        
        # Edge detection
        edges = cv2.Canny(gray, 50, 150)
        
        # Line detection using Hough transform
        lines = cv2.HoughLinesP(edges, 1, np.pi/180, 100, 
                               minLineLength=50, maxLineGap=10)
        
        # Group lines into walls
        walls = self.group_lines_into_walls(lines)
        
        # Validate wall properties
        validated_walls = self.validate_walls(walls, document)
        
        return validated_walls
    
    def group_lines_into_walls(self, lines: np.ndarray) -> List[Wall]:
        walls = []
        
        for line in lines:
            x1, y1, x2, y2 = line[0]
            
            # Calculate wall properties
            length = np.sqrt((x2-x1)**2 + (y2-y1)**2)
            angle = np.arctan2(y2-y1, x2-x1)
            
            # Group parallel lines
            wall = self.find_parallel_wall(walls, angle, tolerance=0.1)
            
            if wall:
                wall.add_line_segment((x1, y1), (x2, y2))
            else:
                wall = Wall(
                    start_point=(x1, y1),
                    end_point=(x2, y2),
                    length=length,
                    angle=angle
                )
                walls.append(wall)
        
        return walls
```

### 4. Spatial Reconstruction

#### 2D to 3D Conversion
```python
# 2D to 3D spatial reconstruction
class SpatialReconstructor:
    def __init__(self):
        self.coordinate_converter = CoordinateConverter()
        self.height_extractor = HeightExtractor()
        self.volume_calculator = VolumeCalculator()
    
    def reconstruct_3d(self, elements: List[DetectedElement], 
                       scale_info: ScaleInfo) -> List[ArxObject]:
        arx_objects = []
        
        for element in elements:
            # Convert 2D coordinates to 3D world coordinates
            world_position = self.coordinate_converter.convert_to_3d(
                element.position_2d, scale_info
            )
            
            # Extract height information
            height = self.height_extractor.extract_height(element)
            
            # Calculate 3D bounds
            bounds_3d = self.calculate_3d_bounds(element, height)
            
            # Create ArxObject
            arx_object = ArxObject(
                id=element.id,
                type=element.type,
                name=element.name,
                position=world_position,
                bounds=bounds_3d,
                properties=element.properties
            )
            
            arx_objects.append(arx_object)
        
        return arx_objects
```

#### Coordinate System Conversion
```python
# Coordinate system conversion
class CoordinateConverter:
    def __init__(self):
        self.scale_factor = 1.0
        self.origin_offset = (0, 0, 0)
        self.rotation_matrix = np.eye(3)
    
    def convert_to_3d(self, position_2d: Tuple[float, float], 
                      scale_info: ScaleInfo) -> Point3D:
        # Apply scale factor
        x = position_2d[0] * scale_info.scale_factor
        y = position_2d[1] * scale_info.scale_factor
        
        # Apply origin offset
        x += scale_info.origin_offset[0]
        y += scale_info.origin_offset[1]
        
        # Convert to millimeters (internal precision)
        x_mm = int(x * 1000)
        y_mm = int(y * 1000)
        z_mm = 0  # Ground level
        
        return Point3D(x=x_mm, y=y_mm, z=z_mm)
    
    def set_scale_factor(self, scale_factor: float):
        self.scale_factor = scale_factor
    
    def set_origin_offset(self, offset: Tuple[float, float, float]):
        self.origin_offset = offset
```

### 5. ArxObject Creation

#### Object Hierarchy Construction
```python
# Build ArxObject hierarchy
class HierarchyBuilder:
    def build_hierarchy(self, arx_objects: List[ArxObject]) -> ArxObject:
        # Create root building object
        building = ArxObject(
            id="building_main",
            type=ArxObjectType.ARX_TYPE_BUILDING,
            name="Main Building",
            description="Building reconstructed from PDF plans"
        )
        
        # Group objects by floor
        floors = self.group_by_floor(arx_objects)
        
        for floor_num, floor_objects in floors.items():
            # Create floor object
            floor = ArxObject(
                id=f"floor_{floor_num}",
                type=ArxObjectType.ARX_TYPE_FLOOR,
                name=f"Floor {floor_num}",
                description=f"Floor {floor_num} of building"
            )
            
            # Group objects by room
            rooms = self.group_by_room(floor_objects)
            
            for room_id, room_objects in rooms.items():
                # Create room object
                room = ArxObject(
                    id=room_id,
                    type=ArxObjectType.ARX_TYPE_ROOM,
                    name=f"Room {room_id}",
                    description=f"Room {room_id} on floor {floor_num}"
                )
                
                # Add room elements
                for element in room_objects:
                    arxobject_add_child(room, element)
                
                # Add room to floor
                arxobject_add_child(floor, room)
            
            # Add floor to building
            arxobject_add_child(building, floor)
        
        return building
```

#### Property Extraction
```python
# Extract properties from detected elements
class PropertyExtractor:
    def extract_properties(self, element: DetectedElement, 
                          document: Document) -> Dict[str, Any]:
        properties = {}
        
        # Extract text-based properties
        text_properties = self.extract_text_properties(element, document)
        properties.update(text_properties)
        
        # Extract geometric properties
        geometric_properties = self.extract_geometric_properties(element)
        properties.update(geometric_properties)
        
        # Extract system properties
        system_properties = self.extract_system_properties(element)
        properties.update(system_properties)
        
        # Extract confidence scores
        confidence_properties = self.calculate_confidence_scores(element)
        properties.update(confidence_properties)
        
        return properties
    
    def extract_text_properties(self, element: DetectedElement, 
                               document: Document) -> Dict[str, Any]:
        properties = {}
        
        # Extract text near the element
        nearby_text = self.find_nearby_text(element, document)
        
        # Parse text for properties
        for text in nearby_text:
            if "dim" in text.lower() or "size" in text.lower():
                properties["dimensions"] = self.parse_dimensions(text)
            elif "material" in text.lower():
                properties["material"] = self.parse_material(text)
            elif "type" in text.lower():
                properties["type"] = self.parse_type(text)
        
        return properties
```

### 6. Quality Assurance

#### Validation Pipeline
```python
# Quality assurance and validation
class QualityAssurance:
    def __init__(self):
        self.geometry_validator = GeometryValidator()
        self.property_validator = PropertyValidator()
        self.relationship_validator = RelationshipValidator()
    
    def validate_reconstruction(self, building: ArxObject) -> ValidationReport:
        report = ValidationReport()
        
        # Validate geometry
        geometry_issues = self.geometry_validator.validate(building)
        report.add_issues(geometry_issues)
        
        # Validate properties
        property_issues = self.property_validator.validate(building)
        report.add_issues(property_issues)
        
        # Validate relationships
        relationship_issues = self.relationship_validator.validate(building)
        report.add_issues(relationship_issues)
        
        # Calculate overall confidence
        report.calculate_confidence()
        
        return report
    
    def auto_correct_issues(self, building: ArxObject, 
                           issues: List[ValidationIssue]) -> ArxObject:
        corrected_building = building.copy()
        
        for issue in issues:
            if issue.auto_correctable:
                corrected_building = self.apply_correction(
                    corrected_building, issue
                )
        
        return corrected_building
```

#### Confidence Scoring
```python
# Confidence scoring system
class ConfidenceScorer:
    def calculate_element_confidence(self, element: ArxObject) -> float:
        confidence_factors = []
        
        # Detection confidence
        detection_confidence = element.properties.get("detection_confidence", 0.5)
        confidence_factors.append(detection_confidence * 0.3)
        
        # Text extraction confidence
        text_confidence = element.properties.get("text_confidence", 0.5)
        confidence_factors.append(text_confidence * 0.2)
        
        # Geometric consistency
        geometric_confidence = self.calculate_geometric_confidence(element)
        confidence_factors.append(geometric_confidence * 0.3)
        
        # Property completeness
        property_confidence = self.calculate_property_confidence(element)
        confidence_factors.append(property_confidence * 0.2)
        
        return sum(confidence_factors)
    
    def calculate_geometric_confidence(self, element: ArxObject) -> float:
        # Check for geometric anomalies
        bounds = element.bounds
        
        # Validate dimensions
        if bounds.max.x <= bounds.min.x or bounds.max.y <= bounds.min.y:
            return 0.1
        
        # Check aspect ratios
        width = bounds.max.x - bounds.min.x
        height = bounds.max.y - bounds.min.y
        
        if width == 0 or height == 0:
            return 0.1
        
        aspect_ratio = max(width, height) / min(width, height)
        if aspect_ratio > 100:  # Unrealistic aspect ratio
            return 0.3
        
        return 1.0
```

## CLI Integration

### 1. Ingestion Commands

```bash
# Basic PDF ingestion
arx ingest pdf --file "floor_plan.pdf"

# Ingest with specific parameters
arx ingest pdf --file "electrical_plan.pdf" \
  --building "main" \
  --floor "1" \
  --system "electrical" \
  --confidence "high"

# Batch ingestion from directory
arx ingest batch --directory "building_plans/" \
  --building "main" \
  --output "reconstructed_building"

# Ingest with custom scale
arx ingest pdf --file "site_plan.pdf" \
  --scale "1:100" \
  --units "meters"
```

### 2. Processing Commands

```bash
# Process ingested documents
arx process --building "main" --stage "analysis"

# Run specific processing stage
arx process --building "main" --stage "element_detection"

# Process with custom parameters
arx process --building "main" \
  --detection_confidence 0.8 \
  --min_element_size 100 \
  --enable_auto_correction

# View processing status
arx process status --building "main"
```

### 3. Validation Commands

```bash
# Validate reconstruction quality
arx validate --building "main"

# Validate specific aspects
arx validate --building "main" --aspects "geometry,properties,relationships"

# Auto-correct validation issues
arx validate --building "main" --auto-correct

# Export validation report
arx validate --building "main" --export "validation_report.json"
```

## Advanced Features

### 1. Multi-Document Fusion

```python
# Combine multiple documents for better reconstruction
class DocumentFusion:
    def fuse_documents(self, documents: List[Document]) -> FusedDocument:
        # Align documents spatially
        aligned_docs = self.align_documents(documents)
        
        # Merge element detections
        merged_elements = self.merge_elements(aligned_docs)
        
        # Resolve conflicts
        resolved_elements = self.resolve_conflicts(merged_elements)
        
        # Create fused document
        return FusedDocument(
            elements=resolved_elements,
            confidence=self.calculate_fusion_confidence(aligned_docs)
        )
```

### 2. Machine Learning Enhancement

```python
# ML-enhanced element detection
class MLElementDetector:
    def __init__(self):
        self.model = self.load_pretrained_model()
        self.feature_extractor = FeatureExtractor()
    
    def detect_elements(self, document: Document) -> List[DetectedElement]:
        # Extract features
        features = self.feature_extractor.extract(document)
        
        # Run ML model
        predictions = self.model.predict(features)
        
        # Post-process predictions
        elements = self.post_process_predictions(predictions, document)
        
        return elements
    
    def load_pretrained_model(self):
        # Load model trained on building plan dataset
        return load_model("building_element_detection.h5")
```

### 3. Progressive Refinement

```python
# Progressive refinement of reconstruction
class ProgressiveRefiner:
    def refine_reconstruction(self, building: ArxObject, 
                            new_data: Document) -> ArxObject:
        # Identify areas for improvement
        improvement_areas = self.identify_improvement_areas(building)
        
        # Extract new information
        new_elements = self.extract_new_elements(new_data, improvement_areas)
        
        # Merge with existing model
        refined_building = self.merge_new_elements(building, new_elements)
        
        # Validate refinement
        validation = self.validate_refinement(refined_building)
        
        if validation.is_improved:
            return refined_building
        else:
            return building  # Keep original if no improvement
```

## Output Formats

### 1. ArxObject Database

```bash
# Export to ArxObject database
arx export --building "main" --format "arxobject" --output "building.db"

# Export specific systems
arx export --building "main" --system "electrical" --format "arxobject"
```

### 2. Standard Formats

```bash
# Export to IFC format
arx export --building "main" --format "ifc" --output "building.ifc"

# Export to DWG format
arx export --building "main" --format "dwg" --output "building.dwg"

# Export to 3D model formats
arx export --building "main" --format "obj" --output "building.obj"
arx export --building "main" --format "gltf" --output "building.gltf"
```

### 3. ASCII Rendering

```bash
# Generate ASCII rendering
arx render --building "main" --format "ascii" --output "building.txt"

# Render specific floor
arx render --building "main" --floor "1" --format "ascii"

# Render with custom zoom level
arx render --building "main" --zoom "room" --format "ascii"
```

## Performance Optimization

### 1. Parallel Processing

```python
# Parallel document processing
class ParallelProcessor:
    def __init__(self, max_workers: int = 4):
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
    
    def process_documents_parallel(self, documents: List[Document]) -> List[DocumentAnalysis]:
        # Submit tasks to thread pool
        futures = [
            self.executor.submit(self.process_document, doc)
            for doc in documents
        ]
        
        # Collect results
        results = []
        for future in as_completed(futures):
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                logger.error(f"Document processing failed: {e}")
        
        return results
```

### 2. Caching and Optimization

```python
# Caching for repeated operations
class ProcessingCache:
    def __init__(self):
        self.cache = {}
        self.max_size = 1000
    
    def get_cached_result(self, document_hash: str, operation: str):
        key = f"{document_hash}:{operation}"
        return self.cache.get(key)
    
    def cache_result(self, document_hash: str, operation: str, result: Any):
        key = f"{document_hash}:{operation}"
        
        if len(self.cache) >= self.max_size:
            # Remove oldest entries
            oldest_key = next(iter(self.cache))
            del self.cache[oldest_key]
        
        self.cache[key] = result
```

## Next Steps

1. **Document Analysis Engine**: Implement computer vision pipeline
2. **Element Detection**: Build ML-based element recognition
3. **Spatial Reconstruction**: Develop 2D to 3D conversion
4. **Quality Assurance**: Implement validation and correction
5. **CLI Integration**: Connect with Arxos command system

## Resources

- [ArxObject Development](../development/arxobject-dev.md)
- [ASCII-BIM System](../architecture/ascii-bim.md)
- [Field Validation Workflow](field-validation.md)
- [Building IAC Workflow](building-iac.md)
- [CLI Commands Reference](../cli/commands.md)
