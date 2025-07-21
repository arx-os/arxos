"""
Advanced Relationship Management Demo

This example demonstrates the comprehensive relationship management capabilities
including spatial relationships, system connections, conflict detection, and resolution.
"""

import logging
import json
from datetime import datetime, timezone
from typing import Dict, List, Any

from ..models.bim import (
    BIMModel, Room, Device, SystemType, DeviceCategory, Geometry, GeometryType,
    RoomType, Wall, Door, Window
)
from core.services.relationship_manager
    RelationshipManager, BIMRelationship, RelationshipType, RelationshipDirection,
    RelationshipStrength, RelationshipConstraint
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_sample_building_model() -> BIMModel:
    """Create a sample building model for demonstration."""
    model = BIMModel(name="Sample Office Building", description="Demo building for relationship management")
    
    # Create rooms
    lobby = Room(
        id="lobby",
        name="Main Lobby",
        geometry=Geometry(
            type=GeometryType.POLYGON,
            coordinates=[[0, 0], [20, 0], [20, 15], [0, 15], [0, 0]]
        ),
        room_type=RoomType.LOBBY,
        room_number="100",
        area=300.0
    )
    model.add_element(lobby)
    
    office1 = Room(
        id="office-1",
        name="Office 101",
        geometry=Geometry(
            type=GeometryType.POLYGON,
            coordinates=[[0, 15], [10, 15], [10, 25], [0, 25], [0, 15]]
        ),
        room_type=RoomType.OFFICE,
        room_number="101",
        area=100.0
    )
    model.add_element(office1)
    
    office2 = Room(
        id="office-2",
        name="Office 102",
        geometry=Geometry(
            type=GeometryType.POLYGON,
            coordinates=[[10, 15], [20, 15], [20, 25], [10, 25], [10, 15]]
        ),
        room_type=RoomType.OFFICE,
        room_number="102",
        area=100.0
    )
    model.add_element(office2)
    
    mechanical_room = Room(
        id="mechanical-room",
        name="Mechanical Room",
        geometry=Geometry(
            type=GeometryType.POLYGON,
            coordinates=[[20, 0], [30, 0], [30, 15], [20, 15], [20, 0]]
        ),
        room_type=RoomType.MECHANICAL,
        room_number="MECH",
        area=150.0
    )
    model.add_element(mechanical_room)
    
    # Create HVAC devices
    ahu = Device(
        id="ahu-1",
        name="Air Handler Unit 1",
        geometry=Geometry(
            type=GeometryType.POINT,
            coordinates=[25, 7.5]
        ),
        system_type=SystemType.HVAC,
        category=DeviceCategory.AHU,
        manufacturer="Carrier",
        model="48TC"
    )
    model.add_element(ahu)
    
    vav1 = Device(
        id="vav-1",
        name="VAV Box 1",
        geometry=Geometry(
            type=GeometryType.POINT,
            coordinates=[5, 20]
        ),
        system_type=SystemType.HVAC,
        category=DeviceCategory.VAV,
        manufacturer="Titus",
        model="TSS"
    )
    model.add_element(vav1)
    
    vav2 = Device(
        id="vav-2",
        name="VAV Box 2",
        geometry=Geometry(
            type=GeometryType.POINT,
            coordinates=[15, 20]
        ),
        system_type=SystemType.HVAC,
        category=DeviceCategory.VAV,
        manufacturer="Titus",
        model="TSS"
    )
    model.add_element(vav2)
    
    # Create electrical devices
    panel = Device(
        id="panel-1",
        name="Electrical Panel 1",
        geometry=Geometry(
            type=GeometryType.POINT,
            coordinates=[25, 12]
        ),
        system_type=SystemType.ELECTRICAL,
        category=DeviceCategory.PANEL,
        manufacturer="Square D",
        model="QO"
    )
    model.add_element(panel)
    
    outlet1 = Device(
        id="outlet-1",
        name="Electrical Outlet 1",
        geometry=Geometry(
            type=GeometryType.POINT,
            coordinates=[5, 22]
        ),
        system_type=SystemType.ELECTRICAL,
        category=DeviceCategory.OUTLET
    )
    model.add_element(outlet1)
    
    outlet2 = Device(
        id="outlet-2",
        name="Electrical Outlet 2",
        geometry=Geometry(
            type=GeometryType.POINT,
            coordinates=[15, 22]
        ),
        system_type=SystemType.ELECTRICAL,
        category=DeviceCategory.OUTLET
    )
    model.add_element(outlet2)
    
    # Create walls
    wall1 = Wall(
        id="wall-1",
        name="Wall 1",
        geometry=Geometry(
            type=GeometryType.LINESTRING,
            coordinates=[[0, 15], [20, 15]]
        ),
        wall_type="interior",
        thickness=0.2
    )
    model.add_element(wall1)
    
    wall2 = Wall(
        id="wall-2",
        name="Wall 2",
        geometry=Geometry(
            type=GeometryType.LINESTRING,
            coordinates=[[10, 15], [10, 25]]
        ),
        wall_type="interior",
        thickness=0.2
    )
    model.add_element(wall2)
    
    return model

def demonstrate_spatial_relationships(relationship_manager: RelationshipManager):
    """Demonstrate spatial relationships."""
    logger.info("=== Spatial Relationships Demo ===")
    
    # Room contains devices
    contains_rel1 = BIMRelationship(
        relationship_type=RelationshipType.CONTAINS,
        source_id="office-1",
        target_id="vav-1",
        strength=RelationshipStrength.IMPORTANT
    )
    relationship_manager.add_relationship(contains_rel1)
    
    contains_rel2 = BIMRelationship(
        relationship_type=RelationshipType.CONTAINS,
        source_id="office-2",
        target_id="vav-2",
        strength=RelationshipStrength.IMPORTANT
    )
    relationship_manager.add_relationship(contains_rel2)
    
    contains_rel3 = BIMRelationship(
        relationship_type=RelationshipType.CONTAINS,
        source_id="mechanical-room",
        target_id="ahu-1",
        strength=RelationshipStrength.CRITICAL
    )
    relationship_manager.add_relationship(contains_rel3)
    
    contains_rel4 = BIMRelationship(
        relationship_type=RelationshipType.CONTAINS,
        source_id="mechanical-room",
        target_id="panel-1",
        strength=RelationshipStrength.CRITICAL
    )
    relationship_manager.add_relationship(contains_rel4)
    
    # Rooms are adjacent (share a wall)
    adjacent_rel = BIMRelationship(
        relationship_type=RelationshipType.ADJACENT,
        source_id="office-1",
        target_id="office-2",
        direction=RelationshipDirection.BIDIRECTIONAL,
        strength=RelationshipStrength.MODERATE
    )
    relationship_manager.add_relationship(adjacent_rel)
    
    logger.info(f"Added {len(relationship_manager.relationships)} spatial relationships")

def demonstrate_system_relationships(relationship_manager: RelationshipManager):
    """Demonstrate system relationships."""
    logger.info("=== System Relationships Demo ===")
    
    # HVAC system connections
    hvac_rel1 = BIMRelationship(
        relationship_type=RelationshipType.SUPPLIES,
        source_id="ahu-1",
        target_id="vav-1",
        strength=RelationshipStrength.CRITICAL
    )
    relationship_manager.add_relationship(hvac_rel1)
    
    hvac_rel2 = BIMRelationship(
        relationship_type=RelationshipType.SUPPLIES,
        source_id="ahu-1",
        target_id="vav-2",
        strength=RelationshipStrength.CRITICAL
    )
    relationship_manager.add_relationship(hvac_rel2)
    
    # Electrical system connections
    electrical_rel1 = BIMRelationship(
        relationship_type=RelationshipType.SUPPLIES,
        source_id="panel-1",
        target_id="outlet-1",
        strength=RelationshipStrength.IMPORTANT
    )
    relationship_manager.add_relationship(electrical_rel1)
    
    electrical_rel2 = BIMRelationship(
        relationship_type=RelationshipType.SUPPLIES,
        source_id="panel-1",
        target_id="outlet-2",
        strength=RelationshipStrength.IMPORTANT
    )
    relationship_manager.add_relationship(electrical_rel2)
    
    # Control relationships
    control_rel1 = BIMRelationship(
        relationship_type=RelationshipType.CONTROLS,
        source_id="vav-1",
        target_id="outlet-1",
        strength=RelationshipStrength.MODERATE
    )
    relationship_manager.add_relationship(control_rel1)
    
    control_rel2 = BIMRelationship(
        relationship_type=RelationshipType.CONTROLS,
        source_id="vav-2",
        target_id="outlet-2",
        strength=RelationshipStrength.MODERATE
    )
    relationship_manager.add_relationship(control_rel2)
    
    logger.info(f"Added {len(relationship_manager.relationships)} system relationships")

def demonstrate_conflict_detection_and_resolution(relationship_manager: RelationshipManager):
    """Demonstrate conflict detection and resolution."""
    logger.info("=== Conflict Detection and Resolution Demo ===")
    
    # Add conflicting relationships
    conflict_rel1 = BIMRelationship(
        relationship_type=RelationshipType.CONTAINS,
        source_id="office-1",
        target_id="vav-1",
        strength=RelationshipStrength.IMPORTANT
    )
    relationship_manager.add_relationship(conflict_rel1)
    
    conflict_rel2 = BIMRelationship(
        relationship_type=RelationshipType.CONNECTS_TO,
        source_id="office-1",
        target_id="vav-1",
        strength=RelationshipStrength.MINOR
    )
    relationship_manager.add_relationship(conflict_rel2)
    
    # Detect conflicts
    conflicts = relationship_manager.detect_conflicts()
    logger.info(f"Detected {len(conflicts)} conflicts:")
    for conflict in conflicts:
        logger.info(f"  - {conflict['type']}: {conflict.get('relationship_ids', [])}")
    
    # Resolve conflicts
    resolution = relationship_manager.resolve_conflicts(conflicts)
    logger.info(f"Resolution results: {resolution}")
    
    # Validate all relationships
    validation = relationship_manager.validate_all_relationships()
    logger.info(f"Validation results: {validation}")

def demonstrate_advanced_queries(relationship_manager: RelationshipManager):
    """Demonstrate advanced relationship queries."""
    logger.info("=== Advanced Queries Demo ===")
    
    # Find all HVAC relationships
    hvac_rels = relationship_manager.get_relationships(system_type=SystemType.HVAC)
    logger.info(f"Found {len(hvac_rels)} HVAC relationships")
    
    # Find all electrical relationships
    electrical_rels = relationship_manager.get_relationships(system_type=SystemType.ELECTRICAL)
    logger.info(f"Found {len(electrical_rels)} electrical relationships")
    
    # Find path from AHU to outlets
    path_to_outlet1 = relationship_manager.find_path("ahu-1", "outlet-1")
    logger.info(f"Path from AHU to Outlet 1: {len(path_to_outlet1)} relationships")
    
    path_to_outlet2 = relationship_manager.find_path("ahu-1", "outlet-2")
    logger.info(f"Path from AHU to Outlet 2: {len(path_to_outlet2)} relationships")
    
    # Get all elements connected to the AHU
    connected_to_ahu = relationship_manager.get_connected_elements("ahu-1")
    logger.info(f"Elements connected to AHU: {[elem.name for elem in connected_to_ahu]}")

def demonstrate_export_import(relationship_manager: RelationshipManager):
    """Demonstrate export and import functionality."""
    logger.info("=== Export/Import Demo ===")
    
    # Export relationships
    exported_data = relationship_manager.export_relationships('json')
    logger.info(f"Exported {len(relationship_manager.relationships)} relationships")
    
    # Create a new relationship manager for import demo
    new_model = create_sample_building_model()
    new_manager = RelationshipManager(new_model)
    
    # Import relationships
    import_results = new_manager.import_relationships(exported_data, 'json')
    logger.info(f"Import results: {import_results}")
    
    logger.info(f"New manager has {len(new_manager.relationships)} relationships")

def main():
    """Main demonstration function."""
    logger.info("Starting Advanced Relationship Management Demo")
    
    # Create building model
    model = create_sample_building_model()
    logger.info(f"Created building model with {len(model.rooms)} rooms and {len(model.devices)} devices")
    
    # Create relationship manager
    relationship_manager = RelationshipManager(model)
    logger.info("Created relationship manager")
    
    # Demonstrate different types of relationships
    demonstrate_spatial_relationships(relationship_manager)
    demonstrate_system_relationships(relationship_manager)
    
    # Demonstrate conflict detection and resolution
    demonstrate_conflict_detection_and_resolution(relationship_manager)
    
    # Demonstrate advanced queries
    demonstrate_advanced_queries(relationship_manager)
    
    # Demonstrate export/import
    demonstrate_export_import(relationship_manager)
    
    # Final statistics
    logger.info("=== Final Statistics ===")
    logger.info(f"Total relationships: {relationship_manager.stats['total_relationships']}")
    logger.info(f"Valid relationships: {relationship_manager.stats['valid_relationships']}")
    logger.info(f"Invalid relationships: {relationship_manager.stats['invalid_relationships']}")
    
    logger.info("Demo completed successfully!")

if __name__ == "__main__":
    main() 