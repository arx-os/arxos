# Arxos SVG-BIM Code Documentation

## Overview
This document provides comprehensive documentation for all major classes, methods, and modules in the Arxos SVG-BIM system.

## Table of Contents
1. [Models](#models)
2. [Services](#services)
3. [API Layer](#api-layer)
4. [Utilities](#utilities)
5. [Testing](#testing)

## Models

### BIM Models

#### BIMModel
```python
class BIMModel:
    """
    Represents a complete Building Information Model (BIM).
    
    A BIM model contains all building elements, systems, spaces, and their relationships.
    It serves as the central data structure for the entire SVG-BIM system.
    
    Attributes:
        id (str): Unique identifier for the BIM model
        name (str): Human-readable name for the model
        description (str): Detailed description of the model
        version (str): Version identifier for the model
        created_at (datetime): Timestamp when the model was created
        updated_at (datetime): Timestamp when the model was last updated
        elements (List[BIMElement]): All BIM elements in the model
        systems (List[BIMSystem]): Building systems (HVAC, electrical, etc.)
        spaces (List[BIMSpace]): Spatial elements (rooms, floors, etc.)
        relationships (List[BIMRelationship]): Relationships between elements
        metadata (Dict[str, Any]): Additional model metadata
        properties (Dict[str, Any]): Model-level properties
        
    Example:
        >>> model = BIMModel(name="Office Building")
        >>> room = Room(name="Office 101", geometry=room_geom)
        >>> model.add_element(room)
        >>> model.get_elements_by_type("room")
        [<Room: Office 101>]
    """
```

#### BIMElement
```python
class BIMElement:
    """
    Base class for all BIM elements.
    
    Represents individual building elements such as walls, doors, windows,
    devices, and other architectural or MEP components.
    
    Attributes:
        id (str): Unique element identifier
        name (str): Human-readable element name
        element_type (str): Type of BIM element (wall, door, device, etc.)
        geometry (Geometry): Geometric representation of the element
        properties (Dict[str, Any]): Element-specific properties
        metadata (Dict[str, Any]): Additional element metadata
        tags (List[str]): Categorization tags
        status (ElementStatus): Current status of the element
        
    Example:
        >>> wall = Wall(
        ...     name="Interior Wall",
        ...     geometry=wall_geom,
        ...     wall_type="interior",
        ...     thickness=0.2
        ... )
        >>> wall.properties
        {'wall_type': 'interior', 'thickness': 0.2}
    """
```

#### Room
```python
class Room(BIMElement):
    """
    Represents a room or space within a building.
    
    Rooms are spatial elements that contain other building elements
    and define functional areas within the building.
    
    Attributes:
        room_type (str): Type of room (office, conference, bathroom, etc.)
        room_number (str): Room number or identifier
        floor_number (int): Floor level where the room is located
        area (float): Room area in square meters
        height (float): Room height in meters
        occupancy (int): Maximum occupancy capacity
        function (str): Primary function of the room
        
    Example:
        >>> room = Room(
        ...     name="Conference Room A",
        ...     geometry=room_geom,
        ...     room_type="conference",
        ...     room_number="101",
        ...     area=50.0,
        ...     height=3.0
        ... )
        >>> room.calculate_area()
        50.0
    """
```

#### Wall
```python
class Wall(BIMElement):
    """
    Represents a wall element in the building.
    
    Walls are structural elements that define spaces and provide
    separation between different areas of the building.
    
    Attributes:
        wall_type (str): Type of wall (interior, exterior, partition)
        thickness (float): Wall thickness in meters
        height (float): Wall height in meters
        material (str): Primary wall material
        insulation (Dict[str, Any]): Insulation properties
        fire_rating (str): Fire resistance rating
        
    Example:
        >>> wall = Wall(
        ...     name="Exterior Wall",
        ...     geometry=wall_geom,
        ...     wall_type="exterior",
        ...     thickness=0.3,
        ...     height=3.0,
        ...     material="concrete"
        ... )
        >>> wall.calculate_area()
        30.0
    """
```

#### Device
```python
class Device(BIMElement):
    """
    Represents a device or equipment element.
    
    Devices include mechanical, electrical, and plumbing equipment
    such as HVAC units, electrical panels, and plumbing fixtures.
    
    Attributes:
        device_type (str): Type of device (hvac, electrical, plumbing)
        manufacturer (str): Device manufacturer
        model (str): Device model number
        capacity (float): Device capacity or rating
        power_consumption (float): Power consumption in watts
        maintenance_schedule (Dict[str, Any]): Maintenance requirements
        
    Example:
        >>> hvac = Device(
        ...     name="HVAC Unit 1",
        ...     geometry=device_geom,
        ...     device_type="hvac",
        ...     manufacturer="Carrier",
        ...     model="48TC",
        ...     capacity=5000.0
        ... )
        >>> hvac.get_system_type()
        'hvac'
    """
```

### Geometry Models

#### Geometry
```python
class Geometry:
    """
    Represents geometric data for BIM elements.
    
    Supports various geometry types including points, lines, polygons,
    and 3D geometries with coordinate transformations.
    
    Attributes:
        type (GeometryType): Type of geometry (point, line, polygon, etc.)
        coordinates (List[List[float]]): Coordinate data
        properties (Dict[str, Any]): Geometric properties
        bounding_box (List[float]): Bounding box coordinates
        centroid (List[float]): Geometric centroid
        
    Example:
        >>> point_geom = Geometry(
        ...     type=GeometryType.POINT,
        ...     coordinates=[[100, 200]]
        ... )
        >>> polygon_geom = Geometry(
        ...     type=GeometryType.POLYGON,
        ...     coordinates=[[[0, 0], [10, 0], [10, 10], [0, 10], [0, 0]]]
        ... )
        >>> polygon_geom.calculate_area()
        100.0
    """
```

#### GeometryType
```python
class GeometryType(Enum):
    """
    Enumeration of supported geometry types.
    
    Defines the various geometric representations supported
    by the BIM system.
    
    Values:
        POINT: Single point geometry
        LINESTRING: Line or polyline geometry
        POLYGON: Closed polygon geometry
        MULTIPOINT: Multiple points
        MULTILINESTRING: Multiple lines
        MULTIPOLYGON: Multiple polygons
        GEOMETRYCOLLECTION: Collection of different geometry types
    """
```

### Relationship Models

#### BIMRelationship
```python
class BIMRelationship:
    """
    Represents relationships between BIM elements.
    
    Relationships define how elements are connected, contained,
    or related to each other in the building model.
    
    Attributes:
        id (str): Unique relationship identifier
        source_id (str): ID of the source element
        target_id (str): ID of the target element
        relationship_type (RelationshipType): Type of relationship
        properties (Dict[str, Any]): Relationship-specific properties
        metadata (Dict[str, Any]): Additional relationship metadata
        
    Example:
        >>> relationship = BIMRelationship(
        ...     source_id="room_1",
        ...     target_id="wall_1",
        ...     relationship_type=RelationshipType.CONTAINS,
        ...     properties={"containment_type": "boundary"}
        ... )
        >>> relationship.is_valid()
        True
    """
```

#### RelationshipType
```python
class RelationshipType(Enum):
    """
    Enumeration of BIM relationship types.
    
    Defines the various types of relationships that can exist
    between BIM elements.
    
    Values:
        CONTAINS: One element contains another
        CONNECTS_TO: Elements are connected
        SERVES: One element serves another
        SUPPORTS: One element supports another
        ADJACENT_TO: Elements are adjacent
        PART_OF: One element is part of another
        DEPENDS_ON: One element depends on another
    """
```

## Services

### BIM Assembly Pipeline

#### BIMAssemblyPipeline
```python
class BIMAssemblyPipeline:
    """
    Main pipeline for assembling BIM models from SVG data.
    
    Coordinates the entire process of converting SVG drawings
    into structured BIM models with proper relationships and validation.
    
    Attributes:
        svg_parser (SVGParser): SVG parsing service
        geometry_processor (GeometryProcessor): Geometry processing service
        relationship_manager (RelationshipManager): Relationship management
        validator (BIMValidator): Model validation service
        error_handler (ErrorHandler): Error handling and recovery
        
    Example:
        >>> pipeline = BIMAssemblyPipeline()
        >>> result = pipeline.assemble_bim({
        ...     "svg": svg_data,
        ...     "user_id": "user123",
        ...     "project_id": "project456"
        ... })
        >>> print(f"Success: {result.success}")
        >>> print(f"Elements: {len(result.elements)}")
    """
    
    def assemble_bim(self, data: Dict[str, Any]) -> BIMAssemblyResult:
        """
        Assemble a BIM model from SVG data.
        
        This is the main entry point for converting SVG drawings to BIM models.
        The method coordinates all stages of the assembly process including
        parsing, extraction, processing, and validation.
        
        Args:
            data: Input data containing SVG and metadata
                - svg (str): SVG data to process
                - user_id (str): User identifier
                - project_id (str): Project identifier
                - metadata (Dict[str, Any], optional): Additional metadata
                - options (Dict[str, Any], optional): Processing options
                
        Returns:
            BIMAssemblyResult: Result containing the assembled model and metadata
            
        Raises:
            AssemblyError: If assembly fails
            ValidationError: If model validation fails
            ProcessingError: If processing encounters errors
            
        Example:
            >>> result = pipeline.assemble_bim({
            ...     "svg": "<svg>...</svg>",
            ...     "user_id": "user123",
            ...     "project_id": "project456",
            ...     "metadata": {"building_name": "Office Building"},
            ...     "options": {"validate_geometry": True}
            ... })
            >>> if result.success:
            ...     model = result.model
            ...     print(f"Created {len(model.elements)} elements")
        """
```

#### BIMAssemblyResult
```python
class BIMAssemblyResult:
    """
    Result of BIM assembly operation.
    
    Contains the assembled BIM model, processing metadata,
    warnings, and error information.
    
    Attributes:
        success (bool): Whether assembly was successful
        model (BIMModel): Assembled BIM model
        elements (List[BIMElement]): All created elements
        systems (List[BIMSystem]): All created systems
        spaces (List[BIMSpace]): All created spaces
        relationships (List[BIMRelationship]): All created relationships
        warnings (List[str]): Warning messages
        errors (List[str]): Error messages
        processing_time (float): Processing time in seconds
        metadata (Dict[str, Any]): Additional result metadata
        
    Example:
        >>> result = pipeline.assemble_bim(data)
        >>> if result.success:
        ...     print(f"Assembly completed in {result.processing_time:.2f}s")
        ...     print(f"Created {len(result.elements)} elements")
        ... else:
        ...     print(f"Assembly failed: {result.errors}")
    """
```

### SVG Parser

#### SVGParser
```python
class SVGParser:
    """
    Parser for SVG files and data.
    
    Extracts geometric elements, attributes, and metadata from SVG
    content for conversion to BIM elements.
    
    Attributes:
        parser_config (Dict[str, Any]): Parser configuration
        element_handlers (Dict[str, Callable]): Element-specific handlers
        attribute_processors (Dict[str, Callable]): Attribute processors
        
    Example:
        >>> parser = SVGParser()
        >>> elements = parser.parse(svg_data)
        >>> for element in elements:
        ...     print(f"Found {element.tag} at {element.position}")
    """
    
    def parse(self, svg_data: str) -> SVGParsingResult:
        """
        Parse SVG data and extract elements.
        
        Processes SVG content to extract geometric elements,
        attributes, and metadata for BIM conversion.
        
        Args:
            svg_data: SVG content as string
            
        Returns:
            SVGParsingResult: Parsed elements and metadata
            
        Raises:
            ParsingError: If SVG parsing fails
            ValidationError: If SVG validation fails
            
        Example:
            >>> result = parser.parse(svg_data)
            >>> print(f"Found {len(result.elements)} elements")
            >>> for element in result.elements:
            ...     print(f"Element: {element.tag}, Type: {element.bim_type}")
        """
```

### Geometry Processing

#### GeometryProcessor
```python
class GeometryProcessor:
    """
    Processes and transforms geometric data.
    
    Handles coordinate transformations, geometry validation,
    and conversion between different geometric representations.
    
    Attributes:
        coordinate_system (CoordinateSystem): Coordinate system configuration
        transformation_matrix (List[List[float]]): Transformation matrix
        validation_rules (Dict[str, Any]): Geometry validation rules
        
    Example:
        >>> processor = GeometryProcessor()
        >>> transformed_geom = processor.transform_geometry(
        ...     geometry, target_system="bim_coordinates"
        ... )
        >>> if processor.validate_geometry(transformed_geom):
        ...     print("Geometry is valid")
    """
    
    def transform_geometry(self, geometry: Geometry, 
                          target_system: str) -> Geometry:
        """
        Transform geometry to target coordinate system.
        
        Converts geometry from SVG coordinates to BIM coordinate system,
        applying necessary transformations and scaling.
        
        Args:
            geometry: Source geometry to transform
            target_system: Target coordinate system identifier
            
        Returns:
            Geometry: Transformed geometry
            
        Raises:
            TransformationError: If transformation fails
            ValidationError: If resulting geometry is invalid
            
        Example:
            >>> svg_geom = Geometry(type=GeometryType.POLYGON, ...)
            >>> bim_geom = processor.transform_geometry(
            ...     svg_geom, target_system="bim_coordinates"
            ... )
            >>> print(f"Transformed to {bim_geom.coordinates}")
        """
```

### Error Handling

#### ErrorHandler
```python
class ErrorHandler:
    """
    Centralized error handling and recovery.
    
    Provides consistent error handling, recovery strategies,
    and user-friendly error reporting across the system.
    
    Attributes:
        error_collector (ErrorCollector): Collects and categorizes errors
        recovery_manager (RecoveryManager): Manages recovery strategies
        error_reporter (ErrorReporter): Generates error reports
        
    Example:
        >>> handler = create_error_handler()
        >>> try:
        ...     result = process_data(data)
        ... except ProcessingError as e:
        ...     recovery = handler.handle_processing_error(e)
        ...     if recovery.success:
        ...         result = recovery.result
    """
    
    def handle_missing_geometry(self, element_id: str, 
                               element_type: str) -> RecoveryResult:
        """
        Handle missing geometry errors.
        
        Attempts to recover or generate geometry for elements
        that are missing geometric data.
        
        Args:
            element_id: ID of the element with missing geometry
            element_type: Type of the element
            
        Returns:
            RecoveryResult: Recovery attempt result
            
        Example:
            >>> result = handler.handle_missing_geometry("wall_1", "wall")
            >>> if result.success:
            ...     print(f"Recovered geometry: {result.geometry}")
            ... else:
            ...     print(f"Recovery failed: {result.error}")
        """
```

## API Layer

### FastAPI Application

#### API Endpoints
```python
@app.post("/bim/assemble")
async def assemble_bim(request: BIMAssemblyRequest) -> BIMAssemblyResponse:
    """
    Assemble BIM model from SVG data.
    
    Main endpoint for converting SVG drawings to BIM models.
    Supports various input formats and processing options.
    
    Args:
        request: Assembly request containing SVG data and options
        
    Returns:
        BIMAssemblyResponse: Assembly result with model ID and metadata
        
    Raises:
        HTTPException: For validation or processing errors
        
    Example:
        POST /bim/assemble
        {
            "svg_data": "<svg>...</svg>",
            "user_id": "user123",
            "project_id": "project456",
            "metadata": {"building_name": "Office Building"}
        }
        
        Response:
        {
            "success": true,
            "model_id": "model_123",
            "elements_count": 25,
            "processing_time": 1.23
        }
    """
```

#### Request/Response Models
```python
class BIMAssemblyRequest(BaseModel):
    """
    Request model for BIM assembly endpoint.
    
    Defines the structure and validation rules for BIM assembly requests.
    
    Attributes:
        svg_data (str): SVG content to process
        user_id (str): User identifier
        project_id (str): Project identifier
        metadata (Dict[str, Any], optional): Additional metadata
        options (Dict[str, Any], optional): Processing options
        
    Example:
        >>> request = BIMAssemblyRequest(
        ...     svg_data="<svg>...</svg>",
        ...     user_id="user123",
        ...     project_id="project456",
        ...     metadata={"building_name": "Office Building"}
        ... )
    """
    
    svg_data: str = Field(..., description="SVG content to process")
    user_id: str = Field(..., description="User identifier")
    project_id: str = Field(..., description="Project identifier")
    metadata: Optional[Dict[str, Any]] = Field(
        default=None, description="Additional metadata"
    )
    options: Optional[Dict[str, Any]] = Field(
        default=None, description="Processing options"
    )
    
    class Config:
        schema_extra = {
            "example": {
                "svg_data": "<svg width='800' height='600'>...</svg>",
                "user_id": "user123",
                "project_id": "project456",
                "metadata": {"building_name": "Office Building"},
                "options": {"validate_geometry": True}
            }
        }
```

## Utilities

### Performance Optimization

#### PerformanceOptimizer
```python
class PerformanceOptimizer:
    """
    Performance optimization and monitoring.
    
    Provides tools for profiling, caching, and optimizing
    system performance across all components.
    
    Attributes:
        profiler (Profiler): Performance profiling tools
        cache_manager (CacheManager): Caching system
        resource_monitor (ResourceMonitor): Resource usage monitoring
        
    Example:
        >>> optimizer = PerformanceOptimizer()
        >>> with optimizer.profile("assembly_operation"):
        ...     result = pipeline.assemble_bim(data)
        >>> metrics = optimizer.get_metrics()
        >>> print(f"Processing time: {metrics['processing_time']:.2f}s")
    """
    
    def profile(self, operation_name: str) -> ProfilerContext:
        """
        Profile a specific operation.
        
        Creates a profiling context for measuring performance
        of specific operations or code blocks.
        
        Args:
            operation_name: Name of the operation to profile
            
        Returns:
            ProfilerContext: Profiling context manager
            
        Example:
            >>> with optimizer.profile("svg_parsing"):
            ...     elements = parser.parse(svg_data)
            >>> profile_data = optimizer.get_profile_data("svg_parsing")
            >>> print(f"Parsing took {profile_data['duration']:.2f}s")
        """
```

### Testing Utilities

#### TestFixtures
```python
class TestFixtures:
    """
    Test fixtures and utilities.
    
    Provides common test data, fixtures, and utilities
    for comprehensive testing across the system.
    
    Example:
        >>> fixtures = TestFixtures()
        >>> svg_data = fixtures.get_sample_svg("office_building")
        >>> expected_elements = fixtures.get_expected_elements("office_building")
        >>> result = pipeline.assemble_bim({"svg": svg_data})
        >>> assert len(result.elements) == len(expected_elements)
    """
    
    def get_sample_svg(self, building_type: str) -> str:
        """
        Get sample SVG data for testing.
        
        Args:
            building_type: Type of building (office, residential, etc.)
            
        Returns:
            str: Sample SVG content
            
        Example:
            >>> svg = fixtures.get_sample_svg("office_building")
            >>> assert "<svg" in svg
            >>> assert "rect" in svg
        """
```

## Testing

### Unit Tests

#### TestBIMAssembly
```python
class TestBIMAssembly:
    """
    Unit tests for BIM assembly functionality.
    
    Tests the core assembly pipeline, error handling,
    and validation features.
    
    Example:
        >>> def test_basic_assembly():
        ...     pipeline = BIMAssemblyPipeline()
        ...     result = pipeline.assemble_bim({"svg": sample_svg})
        ...     assert result.success
        ...     assert len(result.elements) > 0
    """
    
    def test_svg_to_bim_conversion(self):
        """
        Test basic SVG to BIM conversion.
        
        Verifies that SVG data is correctly converted to
        structured BIM elements with proper relationships.
        """
        # Test implementation
        pass
    
    def test_error_handling(self):
        """
        Test error handling and recovery.
        
        Verifies that various error conditions are handled
        gracefully with appropriate recovery strategies.
        """
        # Test implementation
        pass
```

### Integration Tests

#### TestEndToEndWorkflow
```python
class TestEndToEndWorkflow:
    """
    End-to-end integration tests.
    
    Tests complete workflows from SVG input to BIM output,
    including API endpoints and data persistence.
    
    Example:
        >>> def test_complete_workflow():
        ...     # Test complete SVG to BIM to export workflow
        ...     result = test_svg_to_bim_pipeline()
        ...     assert result.success
        ...     export = test_bim_export(result.model_id)
        ...     assert export is not None
    """
    
    def test_svg_to_bim_pipeline(self):
        """
        Test complete SVG to BIM pipeline.
        
        Tests the entire process from SVG parsing through
        BIM assembly and validation.
        """
        # Test implementation
        pass
    
    def test_api_workflow(self):
        """
        Test API-based workflow.
        
        Tests complete workflow using REST API endpoints
        for assembly, querying, and export.
        """
        # Test implementation
        pass
```

This comprehensive code documentation provides detailed information about all major components of the Arxos SVG-BIM system, including usage examples, type hints, and best practices for development. 