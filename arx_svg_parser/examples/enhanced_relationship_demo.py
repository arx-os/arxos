#!/usr/bin/env python3
"""
Enhanced Relationship Management Demo

This script demonstrates the enhanced relationship management features:
- Bidirectional relationships
- Reference integrity validation and repair
- New relationship types (flow, control, adjacency, connectivity)
- Advanced relationship features
"""

import sys
import os
import logging
from datetime import datetime, timezone

# Add the parent directory to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.relationship_manager import (
    RelationshipManager, BIMRelationship, RelationshipType, 
    RelationshipDirection, RelationshipStrength, RelationshipConstraint
)
from models.bim import (
    BIMModel, Room, Device, SystemType, DeviceCategory,
    Geometry, GeometryType, HVACZone, ElectricalPanel
)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def create_sample_bim_model():
    """Create a sample BIM model for demonstration."""
    logger.info("Creating sample BIM model...")
    
    model = BIMModel()
    
    # Add rooms
    room1 = Room(
        id="conference-room-1",
        name="Conference Room 1",
        geometry=Geometry(
            type=GeometryType.POLYGON,
            coordinates=[[0, 0], [20, 0], [20, 15], [0, 15], [0, 0]]
        ),
        room_type="conference",
        room_number="101"
    )
    model.add_element(room1)
    
    room2 = Room(
        id="conference-room-2",
        name="Conference Room 2",
        geometry=Geometry(
            type=GeometryType.POLYGON,
            coordinates=[[25, 0], [45, 0], [45, 15], [25, 15], [25, 0]]
        ),
        room_type="conference",
        room_number="102"
    )
    model.add_element(room2)
    
    # Add HVAC system
    ahu = Device(
        id="ahu-main",
        name="Main Air Handler Unit",
        geometry=Geometry(
            type=GeometryType.POINT,
            coordinates=[10, 7.5]
        ),
        system_type=SystemType.HVAC,
        category=DeviceCategory.AHU
    )
    model.add_element(ahu)
    
    vav1 = Device(
        id="vav-room-1",
        name="VAV Box - Room 1",
        geometry=Geometry(
            type=GeometryType.POINT,
            coordinates=[5, 5]
        ),
        system_type=SystemType.HVAC,
        category=DeviceCategory.VAV
    )
    model.add_element(vav1)
    
    vav2 = Device(
        id="vav-room-2",
        name="VAV Box - Room 2",
        geometry=Geometry(
            type=GeometryType.POINT,
            coordinates=[35, 5]
        ),
        system_type=SystemType.HVAC,
        category=DeviceCategory.VAV
    )
    model.add_element(vav2)
    
    # Add electrical system
    panel = Device(
        id="electrical-panel-main",
        name="Main Electrical Panel",
        geometry=Geometry(
            type=GeometryType.POINT,
            coordinates=[15, 12]
        ),
        system_type=SystemType.ELECTRICAL,
        category=DeviceCategory.PANEL
    )
    model.add_element(panel)
    
    outlet1 = Device(
        id="outlet-room-1-1",
        name="Electrical Outlet - Room 1",
        geometry=Geometry(
            type=GeometryType.POINT,
            coordinates=[2, 2]
        ),
        system_type=SystemType.ELECTRICAL,
        category=DeviceCategory.OUTLET
    )
    model.add_element(outlet1)
    
    outlet2 = Device(
        id="outlet-room-2-1",
        name="Electrical Outlet - Room 2",
        geometry=Geometry(
            type=GeometryType.POINT,
            coordinates=[27, 2]
        ),
        system_type=SystemType.ELECTRICAL,
        category=DeviceCategory.OUTLET
    )
    model.add_element(outlet2)
    
    logger.info(f"Created BIM model with {len(model.get_all_elements())} elements")
    return model


def demonstrate_bidirectional_relationships(relationship_manager):
    """Demonstrate bidirectional relationships."""
    logger.info("\n=== Bidirectional Relationships Demo ===")
    
    # Create bidirectional containment relationship
    contains_rel = BIMRelationship(
        relationship_type=RelationshipType.CONTAINS,
        source_id="conference-room-1",
        target_id="ahu-main",
        direction=RelationshipDirection.BIDIRECTIONAL,
        strength=RelationshipStrength.IMPORTANT,
        properties={"containment_type": "spatial"}
    )
    
    result = relationship_manager.add_relationship(contains_rel)
    logger.info(f"Added bidirectional containment relationship: {result}")
    
    # Check that both relationships were created
    total_relationships = len(relationship_manager.relationships)
    logger.info(f"Total relationships after bidirectional creation: {total_relationships}")
    
    # Find the reverse relationship
    reverse_relationships = [
        rel for rel in relationship_manager.relationships.values()
        if rel.relationship_type == RelationshipType.INSIDE
    ]
    
    if reverse_relationships:
        reverse_rel = reverse_relationships[0]
        logger.info(f"Reverse relationship found: {reverse_rel.relationship_type}")
        logger.info(f"  Source: {reverse_rel.source_id}")
        logger.info(f"  Target: {reverse_rel.target_id}")
        logger.info(f"  Linked to: {reverse_rel.reverse_relationship_id}")
    
    # Test bidirectional navigation
    connected_to_room = relationship_manager.get_connected_elements("conference-room-1")
    logger.info(f"Elements connected to room: {[elem.id for elem in connected_to_room]}")
    
    connected_to_ahu = relationship_manager.get_connected_elements("ahu-main")
    logger.info(f"Elements connected to AHU: {[elem.id for elem in connected_to_ahu]}")


def demonstrate_new_relationship_types(relationship_manager):
    """Demonstrate new relationship types."""
    logger.info("\n=== New Relationship Types Demo ===")
    
    # FLOW relationship (air flow)
    flow_rel = BIMRelationship(
        relationship_type=RelationshipType.FLOW,
        source_id="ahu-main",
        target_id="vav-room-1",
        properties={
            "flow_type": "air",
            "flow_rate": 1000,  # CFM
            "temperature": 55,   # °F
            "pressure": 2.5,     # inches WC
            "direction": "supply"
        }
    )
    relationship_manager.add_relationship(flow_rel)
    logger.info("Added FLOW relationship (air flow)")
    
    # CONTROL relationship (electrical control)
    control_rel = BIMRelationship(
        relationship_type=RelationshipType.CONTROL,
        source_id="electrical-panel-main",
        target_id="ahu-main",
        properties={
            "control_type": "electrical",
            "voltage": 480,
            "amperage": 50,
            "control_method": "direct"
        }
    )
    relationship_manager.add_relationship(control_rel)
    logger.info("Added CONTROL relationship (electrical control)")
    
    # ADJACENCY relationship (spatial)
    adjacency_rel = BIMRelationship(
        relationship_type=RelationshipType.ADJACENCY,
        source_id="conference-room-1",
        target_id="conference-room-2",
        properties={
            "adjacency_type": "wall_shared",
            "wall_length": 15,
            "sound_transmission": "STC-45"
        }
    )
    relationship_manager.add_relationship(adjacency_rel)
    logger.info("Added ADJACENCY relationship (spatial)")
    
    # CONNECTIVITY relationship (electrical)
    connectivity_rel = BIMRelationship(
        relationship_type=RelationshipType.CONNECTIVITY,
        source_id="electrical-panel-main",
        target_id="outlet-room-1-1",
        properties={
            "connection_type": "electrical",
            "wire_type": "THHN",
            "circuit_number": "A1",
            "voltage": 120,
            "amperage": 20
        }
    )
    relationship_manager.add_relationship(connectivity_rel)
    logger.info("Added CONNECTIVITY relationship (electrical)")
    
    # Test querying by relationship type
    flow_relationships = relationship_manager.get_relationships(relationship_type=RelationshipType.FLOW)
    control_relationships = relationship_manager.get_relationships(relationship_type=RelationshipType.CONTROL)
    adjacency_relationships = relationship_manager.get_relationships(relationship_type=RelationshipType.ADJACENCY)
    
    logger.info(f"Flow relationships: {len(flow_relationships)}")
    logger.info(f"Control relationships: {len(control_relationships)}")
    logger.info(f"Adjacency relationships: {len(adjacency_relationships)}")


def demonstrate_reference_integrity(relationship_manager):
    """Demonstrate reference integrity validation and repair."""
    logger.info("\n=== Reference Integrity Demo ===")
    
    # Add a valid relationship
    valid_rel = BIMRelationship(
        relationship_type=RelationshipType.CONTAINS,
        source_id="conference-room-1",
        target_id="vav-room-1"
    )
    relationship_manager.add_relationship(valid_rel)
    logger.info("Added valid relationship")
    
    # Add invalid relationships (non-existent elements)
    invalid_rel1 = BIMRelationship(
        relationship_type=RelationshipType.CONTAINS,
        source_id="conference-room-1",
        target_id="non-existent-element-1"
    )
    invalid_rel2 = BIMRelationship(
        relationship_type=RelationshipType.CONNECTS_TO,
        source_id="non-existent-element-2",
        target_id="ahu-main"
    )
    
    # Force add these relationships (bypass validation)
    relationship_manager.relationships[invalid_rel1.relationship_id] = invalid_rel1
    relationship_manager.relationships[invalid_rel2.relationship_id] = invalid_rel2
    relationship_manager.stats['total_relationships'] += 2
    relationship_manager.stats['invalid_relationships'] += 2
    logger.info("Added invalid relationships (for demonstration)")
    
    # Validate reference integrity
    integrity_report = relationship_manager.validate_reference_integrity()
    logger.info("Reference integrity validation results:")
    logger.info(f"  Total relationships: {integrity_report['total_relationships']}")
    logger.info(f"  Valid references: {integrity_report['valid_references']}")
    logger.info(f"  Invalid references: {integrity_report['invalid_references']}")
    logger.info(f"  Missing elements: {list(integrity_report['missing_elements'])}")
    logger.info(f"  Orphaned relationships: {len(integrity_report['orphaned_relationships'])}")
    
    # Repair reference integrity
    repair_report = relationship_manager.repair_reference_integrity(auto_repair=True)
    logger.info("Reference integrity repair results:")
    logger.info(f"  Relationships removed: {repair_report['relationships_removed']}")
    logger.info(f"  Errors fixed: {repair_report['errors_fixed']}")
    logger.info(f"  Repair actions: {repair_report['repair_actions']}")
    
    # Check final state
    final_integrity = relationship_manager.validate_reference_integrity()
    logger.info(f"Final state - Valid relationships: {final_integrity['valid_references']}")


def demonstrate_enhanced_path_finding(relationship_manager):
    """Demonstrate enhanced path finding with new relationship types."""
    logger.info("\n=== Enhanced Path Finding Demo ===")
    
    # Add more relationships to create a complex network
    rel1 = BIMRelationship(
        relationship_type=RelationshipType.CONTAINS,
        source_id="conference-room-1",
        target_id="vav-room-1"
    )
    rel2 = BIMRelationship(
        relationship_type=RelationshipType.FLOW,
        source_id="ahu-main",
        target_id="vav-room-1"
    )
    rel3 = BIMRelationship(
        relationship_type=RelationshipType.CONTROL,
        source_id="electrical-panel-main",
        target_id="ahu-main"
    )
    rel4 = BIMRelationship(
        relationship_type=RelationshipType.CONNECTIVITY,
        source_id="electrical-panel-main",
        target_id="outlet-room-1-1"
    )
    
    relationship_manager.add_relationship(rel1)
    relationship_manager.add_relationship(rel2)
    relationship_manager.add_relationship(rel3)
    relationship_manager.add_relationship(rel4)
    
    # Test path finding with specific relationship types
    logger.info("Path finding examples:")
    
    # Flow path
    flow_path = relationship_manager.find_path(
        "ahu-main", "vav-room-1", 
        relationship_types=[RelationshipType.FLOW]
    )
    logger.info(f"Flow path (AHU -> VAV): {len(flow_path)} relationships")
    
    # Control path
    control_path = relationship_manager.find_path(
        "electrical-panel-main", "ahu-main",
        relationship_types=[RelationshipType.CONTROL]
    )
    logger.info(f"Control path (Panel -> AHU): {len(control_path)} relationships")
    
    # Mixed path
    mixed_path = relationship_manager.find_path(
        "conference-room-1", "vav-room-1",
        relationship_types=[RelationshipType.CONTAINS, RelationshipType.FLOW]
    )
    logger.info(f"Mixed path (Room -> VAV): {len(mixed_path)} relationships")
    
    # Complex path
    complex_path = relationship_manager.find_path(
        "electrical-panel-main", "vav-room-1"
    )
    logger.info(f"Complex path (Panel -> VAV): {len(complex_path)} relationships")


def demonstrate_relationship_statistics(relationship_manager):
    """Demonstrate relationship statistics and reporting."""
    logger.info("\n=== Relationship Statistics Demo ===")
    
    # Display current statistics
    stats = relationship_manager.stats
    logger.info("Current relationship statistics:")
    logger.info(f"  Total relationships: {stats['total_relationships']}")
    logger.info(f"  Valid relationships: {stats['valid_relationships']}")
    logger.info(f"  Invalid relationships: {stats['invalid_relationships']}")
    logger.info(f"  Bidirectional relationships: {stats['bidirectional_relationships']}")
    logger.info(f"  Reference errors fixed: {stats['reference_errors_fixed']}")
    
    # Count relationships by type
    relationship_types = {}
    for rel in relationship_manager.relationships.values():
        rel_type = rel.relationship_type.value
        relationship_types[rel_type] = relationship_types.get(rel_type, 0) + 1
    
    logger.info("Relationships by type:")
    for rel_type, count in relationship_types.items():
        logger.info(f"  {rel_type}: {count}")
    
    # Export relationships
    export_data = relationship_manager.export_relationships('json')
    logger.info(f"Exported relationships data length: {len(export_data)} characters")


def main():
    """Main demonstration function."""
    logger.info("Enhanced Relationship Management Demo")
    logger.info("=" * 50)
    
    # Create sample BIM model
    bim_model = create_sample_bim_model()
    
    # Create relationship manager
    relationship_manager = RelationshipManager(bim_model)
    logger.info("Created relationship manager")
    
    # Run demonstrations
    demonstrate_bidirectional_relationships(relationship_manager)
    demonstrate_new_relationship_types(relationship_manager)
    demonstrate_reference_integrity(relationship_manager)
    demonstrate_enhanced_path_finding(relationship_manager)
    demonstrate_relationship_statistics(relationship_manager)
    
    logger.info("\n" + "=" * 50)
    logger.info("Enhanced Relationship Management Demo Complete!")
    logger.info("Key features demonstrated:")
    logger.info("  ✓ Bidirectional relationships with automatic reverse creation")
    logger.info("  ✓ New relationship types: FLOW, CONTROL, ADJACENCY, CONNECTIVITY")
    logger.info("  ✓ Reference integrity validation and repair")
    logger.info("  ✓ Enhanced path finding with relationship type filtering")
    logger.info("  ✓ Comprehensive relationship statistics and reporting")


if __name__ == "__main__":
    main() 