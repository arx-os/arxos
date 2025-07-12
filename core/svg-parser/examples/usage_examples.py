"""
Usage Examples for Arxos SVG-BIM System

This module provides comprehensive examples for common use cases:
- SVG to BIM assembly
- API usage
- Export operations
- Database operations
- Error handling
- Performance optimization
"""

import json
import tempfile
from pathlib import Path
from typing import Dict, Any

from services.bim_assembly import BIMAssemblyPipeline
from services.persistence_export_interoperability import (
    BIMExporter, ExportFormat, ExportOptions, create_persistence_manager,
    save_bim_model_to_database, load_bim_model_from_database
)
from services.robust_error_handling import create_error_handler
from models.bim import BIMModel, Room, Wall, Device, Geometry, GeometryType


def example_svg_to_bim_assembly():
    """Example: Basic SVG to BIM assembly."""
    print("=== SVG to BIM Assembly Example ===")
    
    # Sample SVG data
    svg_data = """
    <svg width="800" height="600" xmlns="http://www.w3.org/2000/svg">
        <rect x="100" y="100" width="200" height="20" fill="gray" data-bim-type="wall"/>
        <rect x="300" y="100" width="100" height="20" fill="gray" data-bim-type="wall"/>
        <rect x="150" y="200" width="50" height="50" fill="blue" data-bim-type="room"/>
        <circle cx="400" cy="300" r="30" fill="red" data-bim-type="device"/>
    </svg>
    """
    
    # Create assembly pipeline
    pipeline = BIMAssemblyPipeline()
    
    # Assemble BIM
    result = pipeline.assemble_bim({"svg": svg_data})
    
    print(f"Assembly successful: {result.success}")
    print(f"Elements created: {len(result.elements)}")
    print(f"Systems created: {len(result.systems)}")
    print(f"Spaces created: {len(result.spaces)}")
    print(f"Relationships created: {len(result.relationships)}")
    
    return result


def example_api_usage():
    """Example: Using the REST API."""
    print("\n=== API Usage Example ===")
    
    # This would be used with the FastAPI server running
    import requests
    
    # Sample API calls (assuming server is running on localhost:8000)
    base_url = "http://localhost:8000"
    
    # 1. Assemble BIM via API
    svg_data = """
    <svg width="800" height="600" xmlns="http://www.w3.org/2000/svg">
        <rect x="100" y="100" width="200" height="20" fill="gray" data-bim-type="wall"/>
        <rect x="150" y="200" width="50" height="50" fill="blue" data-bim-type="room"/>
    </svg>
    """
    
    assembly_request = {
        "svg_data": svg_data,
        "user_id": "user123",
        "project_id": "project456",
        "metadata": {"building_name": "Example Building"}
    }
    
    # response = requests.post(f"{base_url}/bim/assemble", json=assembly_request)
    # model_id = response.json()["model_id"]
    print("API assembly request prepared (server not running)")
    
    # 2. Query BIM model
    query_request = {
        "model_id": "example_model_id",
        "user_id": "user123",
        "project_id": "project456",
        "query": {"type": "room"}
    }
    
    # response = requests.post(f"{base_url}/bim/query", json=query_request)
    print("API query request prepared")
    
    # 3. Export BIM model
    export_request = {
        "model_id": "example_model_id",
        "user_id": "user123",
        "project_id": "project456",
        "format": "json"
    }
    
    # response = requests.post(f"{base_url}/bim/export", json=export_request)
    print("API export request prepared")


def example_export_operations():
    """Example: Exporting BIM models in various formats."""
    print("\n=== Export Operations Example ===")
    
    # Create a sample BIM model
    bim_model = BIMModel(name="Example Building")
    
    # Add a room
    room_geom = Geometry(
        type=GeometryType.POLYGON,
        coordinates=[[[0, 0], [10, 0], [10, 10], [0, 10], [0, 0]]]
    )
    room = Room(
        name="Office 101",
        geometry=room_geom,
        room_type="office",
        room_number="101",
        area=100.0
    )
    bim_model.add_element(room)
    
    # Add a wall
    wall_geom = Geometry(
        type=GeometryType.LINESTRING,
        coordinates=[[0, 0], [10, 0]]
    )
    wall = Wall(
        name="Interior Wall",
        geometry=wall_geom,
        wall_type="interior",
        thickness=0.2,
        height=3.0
    )
    bim_model.add_element(wall)
    
    # Export to different formats
    exporter = BIMExporter()
    
    # JSON export
    json_options = ExportOptions(format=ExportFormat.JSON, pretty_print=True)
    json_export = exporter.export_bim_model(bim_model, json_options)
    print(f"JSON export length: {len(json_export)} characters")
    
    # CSV export
    csv_options = ExportOptions(format=ExportFormat.CSV)
    csv_export = exporter.export_bim_model(bim_model, csv_options)
    print(f"CSV export length: {len(csv_export)} characters")
    
    # XML export
    xml_options = ExportOptions(format=ExportFormat.XML)
    xml_export = exporter.export_bim_model(bim_model, xml_options)
    print(f"XML export length: {len(xml_export)} characters")
    
    # IFC export (simplified)
    ifc_options = ExportOptions(format=ExportFormat.IFC)
    ifc_export = exporter.export_bim_model(bim_model, ifc_options)
    print(f"IFC export length: {len(ifc_export)} characters")
    
    return {
        "json": json_export,
        "csv": csv_export,
        "xml": xml_export,
        "ifc": ifc_export
    }


def example_database_operations():
    """Example: Database operations for BIM models."""
    print("\n=== Database Operations Example ===")
    
    # Create a sample BIM model
    bim_model = BIMModel(name="Database Example Building")
    
    # Add some elements
    room_geom = Geometry(
        type=GeometryType.POLYGON,
        coordinates=[[[0, 0], [10, 0], [10, 10], [0, 10], [0, 0]]]
    )
    room = Room(name="Test Room", geometry=room_geom, room_type="office")
    bim_model.add_element(room)
    
    # Save to database
    model_id = "example_model_123"
    save_bim_model_to_database(
        bim_model,
        model_id,
        connection_string=":memory:"  # In-memory SQLite for demo
    )
    print(f"Saved BIM model with ID: {model_id}")
    
    # Load from database
    loaded_model = load_bim_model_from_database(
        model_id,
        connection_string=":memory:"
    )
    print(f"Loaded BIM model: {loaded_model.name}")
    print(f"Number of rooms: {len(loaded_model.rooms)}")
    
    return loaded_model


def example_error_handling():
    """Example: Error handling and recovery."""
    print("\n=== Error Handling Example ===")
    
    # Create error handler
    handler = create_error_handler()
    
    # Simulate various error scenarios
    print("Handling missing geometry...")
    recovered_geometry = handler.handle_missing_geometry("wall_1", "wall")
    print(f"Recovered geometry: {recovered_geometry['type']}")
    
    print("Handling unknown type...")
    recovered_type = handler.handle_unknown_type("custom_1", "custom_fixture")
    print(f"Recovered type: {recovered_type}")
    
    print("Handling ambiguous type...")
    detected_types = ["wall", "partition", "barrier"]
    recovered_ambiguous = handler.handle_ambiguous_type("element_1", detected_types)
    print(f"Recovered ambiguous type: {recovered_ambiguous}")
    
    print("Handling property conflict...")
    recovered_value = handler.handle_property_conflict("door_1", "height", 2.1, 2.4)
    print(f"Recovered property value: {recovered_value}")
    
    # Generate error report
    report = handler.generate_report(success=True, metadata={"operation": "example"})
    print(f"Error report generated with {len(report.warnings)} warnings")
    
    return report


def example_performance_optimization():
    """Example: Performance optimization features."""
    print("\n=== Performance Optimization Example ===")
    
    from services.enhanced_performance import (
        EnhancedPerformanceOptimizer, OptimizationLevel
    )
    
    # Create performance optimizer
    optimizer = EnhancedPerformanceOptimizer()
    
    # Configure optimization
    optimizer.configure_optimization(
        batch_size=1000,
        max_workers=4,
        cache_size=1000,
        memory_limit="1GB"
    )
    
    # Simulate batch processing
    sample_data = [{"id": f"item_{i}", "data": f"data_{i}"} for i in range(100)]
    
    print(f"Processing {len(sample_data)} items...")
    
    # Process with optimization
    result = optimizer.process_batch(
        sample_data,
        operation="test_processing",
        optimization_level=OptimizationLevel.HIGH
    )
    
    print(f"Processing completed: {result.success}")
    print(f"Processing time: {result.processing_time:.2f} seconds")
    print(f"Memory usage: {result.memory_usage:.2f} MB")
    
    # Get performance metrics
    metrics = optimizer.get_performance_metrics()
    print(f"Average processing time: {metrics.get('avg_processing_time', 0):.2f} seconds")
    print(f"Cache hit rate: {metrics.get('cache_hit_rate', 0):.2f}%")
    
    return result


def example_spatial_reasoning():
    """Example: Spatial reasoning and analysis."""
    print("\n=== Spatial Reasoning Example ===")
    
    from services.enhanced_spatial_reasoning import (
        EnhancedSpatialReasoningEngine
    )
    
    # Create spatial reasoning engine
    engine = EnhancedSpatialReasoningEngine()
    
    # Create sample spatial elements
    room_geom = Geometry(
        type=GeometryType.POLYGON,
        coordinates=[[[0, 0], [10, 0], [10, 10], [0, 10], [0, 0]]]
    )
    
    wall_geom = Geometry(
        type=GeometryType.LINESTRING,
        coordinates=[[0, 0], [10, 0]]
    )
    
    device_geom = Geometry(
        type=GeometryType.POINT,
        coordinates=[5, 5]
    )
    
    # Analyze spatial relationships
    relationships = engine.analyze_spatial_relationships([
        {"id": "room_1", "geometry": room_geom, "type": "room"},
        {"id": "wall_1", "geometry": wall_geom, "type": "wall"},
        {"id": "device_1", "geometry": device_geom, "type": "device"}
    ])
    
    print(f"Found {len(relationships)} spatial relationships")
    
    # Check for collisions
    collisions = engine.detect_collisions([
        {"id": "room_1", "geometry": room_geom},
        {"id": "room_2", "geometry": room_geom}  # Overlapping room
    ])
    
    print(f"Detected {len(collisions)} collisions")
    
    # Calculate areas
    areas = engine.calculate_areas([
        {"id": "room_1", "geometry": room_geom}
    ])
    
    print(f"Calculated areas: {areas}")
    
    return {
        "relationships": relationships,
        "collisions": collisions,
        "areas": areas
    }


def example_relationship_management():
    """Example: Advanced relationship management."""
    print("\n=== Relationship Management Example ===")
    
    from services.enhanced_relationship_manager import (
        EnhancedRelationshipManager, RelationshipType
    )
    
    # Create relationship manager
    manager = EnhancedRelationshipManager()
    
    # Create sample elements
    elements = [
        {"id": "room_1", "type": "room", "name": "Office 101"},
        {"id": "wall_1", "type": "wall", "name": "Interior Wall"},
        {"id": "door_1", "type": "door", "name": "Office Door"},
        {"id": "device_1", "type": "device", "name": "HVAC Unit"}
    ]
    
    # Add relationships
    manager.add_relationship(
        source_id="room_1",
        target_id="wall_1",
        relationship_type=RelationshipType.CONTAINS,
        properties={"containment_type": "boundary"}
    )
    
    manager.add_relationship(
        source_id="wall_1",
        target_id="door_1",
        relationship_type=RelationshipType.CONTAINS,
        properties={"containment_type": "opening"}
    )
    
    manager.add_relationship(
        source_id="room_1",
        target_id="device_1",
        relationship_type=RelationshipType.SERVES,
        properties={"service_type": "hvac"}
    )
    
    # Query relationships
    room_relationships = manager.get_relationships("room_1")
    print(f"Room 1 has {len(room_relationships)} relationships")
    
    # Find connected elements
    connected = manager.find_connected_elements("room_1")
    print(f"Elements connected to room_1: {connected}")
    
    # Validate relationships
    validation = manager.validate_relationships()
    print(f"Relationship validation: {validation.valid}")
    if not validation.valid:
        print(f"Validation errors: {validation.errors}")
    
    return manager


def example_complete_workflow():
    """Example: Complete end-to-end workflow."""
    print("\n=== Complete Workflow Example ===")
    
    # 1. Parse SVG and assemble BIM
    print("Step 1: Assembling BIM from SVG...")
    assembly_result = example_svg_to_bim_assembly()
    
    # 2. Handle any errors
    print("Step 2: Error handling...")
    error_report = example_error_handling()
    
    # 3. Export in multiple formats
    print("Step 3: Exporting in multiple formats...")
    exports = example_export_operations()
    
    # 4. Save to database
    print("Step 4: Saving to database...")
    saved_model = example_database_operations()
    
    # 5. Spatial analysis
    print("Step 5: Spatial analysis...")
    spatial_results = example_spatial_reasoning()
    
    # 6. Relationship management
    print("Step 6: Relationship management...")
    relationship_manager = example_relationship_management()
    
    # 7. Performance optimization
    print("Step 7: Performance optimization...")
    perf_results = example_performance_optimization()
    
    print("\n=== Workflow Complete ===")
    print(f"Assembly successful: {assembly_result.success}")
    print(f"Error warnings: {len(error_report.warnings)}")
    print(f"Export formats: {len(exports)}")
    print(f"Database model: {saved_model.name}")
    print(f"Spatial relationships: {len(spatial_results['relationships'])}")
    print(f"Performance time: {perf_results.processing_time:.2f}s")
    
    return {
        "assembly": assembly_result,
        "errors": error_report,
        "exports": exports,
        "database": saved_model,
        "spatial": spatial_results,
        "relationships": relationship_manager,
        "performance": perf_results
    }


def main():
    """Run all usage examples."""
    print("Arxos SVG-BIM System Usage Examples")
    print("=" * 50)
    
    try:
        # Run individual examples
        example_svg_to_bim_assembly()
        example_api_usage()
        example_export_operations()
        example_database_operations()
        example_error_handling()
        example_performance_optimization()
        example_spatial_reasoning()
        example_relationship_management()
        
        # Run complete workflow
        print("\n" + "=" * 50)
        print("Running Complete Workflow Example")
        print("=" * 50)
        complete_results = example_complete_workflow()
        
        print("\n" + "=" * 50)
        print("All Examples Completed Successfully!")
        print("=" * 50)
        
        return complete_results
        
    except Exception as e:
        print(f"Example failed: {e}")
        raise


if __name__ == "__main__":
    main() 