"""
Enhanced Relationship Manager Tests

This module tests the enhanced relationship management system including:
- Bidirectional relationships
- Reference integrity validation and repair
- New relationship types (flow, control, adjacency, connectivity, etc.)
- Advanced relationship features
"""

import pytest
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Any

from services.relationship_manager import (
    RelationshipManager, BIMRelationship, RelationshipType, 
    RelationshipDirection, RelationshipStrength, RelationshipConstraint
)
from ..models.bim import (
    BIMModel, Room, Device, SystemType, DeviceCategory,
    Geometry, GeometryType, HVACZone, ElectricalPanel
)


class TestEnhancedRelationshipManager:
    """Test enhanced relationship management features."""
    
    @pytest.fixture
    def sample_bim_model(self):
        """Create a sample BIM model for testing."""
        model = BIMModel()
        
        # Add rooms
        room1 = Room(
            id="room-1",
            name="Conference Room 1",
            geometry=Geometry(
                type=GeometryType.POLYGON,
                coordinates=[[0, 0], [10, 0], [10, 8], [0, 8], [0, 0]]
            ),
            room_type="conference",
            room_number="101"
        )
        model.add_element(room1)
        
        room2 = Room(
            id="room-2",
            name="Conference Room 2",
            geometry=Geometry(
                type=GeometryType.POLYGON,
                coordinates=[[12, 0], [22, 0], [22, 8], [12, 8], [12, 0]]
            ),
            room_type="conference",
            room_number="102"
        )
        model.add_element(room2)
        
        # Add HVAC devices
        ahu = Device(
            id="ahu-1",
            name="Air Handler Unit 1",
            geometry=Geometry(
                type=GeometryType.POINT,
                coordinates=[5, 4]
            ),
            system_type=SystemType.HVAC,
            category=DeviceCategory.AHU
        )
        model.add_element(ahu)
        
        vav = Device(
            id="vav-1",
            name="VAV Box 1",
            geometry=Geometry(
                type=GeometryType.POINT,
                coordinates=[3, 2]
            ),
            system_type=SystemType.HVAC,
            category=DeviceCategory.VAV
        )
        model.add_element(vav)
        
        # Add electrical devices
        panel = Device(
            id="panel-1",
            name="Electrical Panel 1",
            geometry=Geometry(
                type=GeometryType.POINT,
                coordinates=[8, 6]
            ),
            system_type=SystemType.ELECTRICAL,
            category=DeviceCategory.PANEL
        )
        model.add_element(panel)
        
        outlet = Device(
            id="outlet-1",
            name="Electrical Outlet 1",
            geometry=Geometry(
                type=GeometryType.POINT,
                coordinates=[2, 2]
            ),
            system_type=SystemType.ELECTRICAL,
            category=DeviceCategory.OUTLET
        )
        model.add_element(outlet)
        
        return model
    
    @pytest.fixture
    def relationship_manager(self, sample_bim_model):
        """Create a relationship manager with the sample BIM model."""
        return RelationshipManager(sample_bim_model)
    
    def test_bidirectional_relationships(self, relationship_manager):
        """Test bidirectional relationship creation and navigation."""
        # Create a bidirectional relationship
        relationship = BIMRelationship(
            relationship_type=RelationshipType.CONTAINS,
            source_id="room-1",
            target_id="ahu-1",
            direction=RelationshipDirection.BIDIRECTIONAL,
            strength=RelationshipStrength.IMPORTANT
        )
        
        result = relationship_manager.add_relationship(relationship)
        assert result is True
        
        # Check that both relationships were created
        assert len(relationship_manager.relationships) == 2
        
        # Find the reverse relationship
        reverse_relationships = [
            rel for rel in relationship_manager.relationships.values()
            if rel.relationship_type == RelationshipType.INSIDE
        ]
        assert len(reverse_relationships) == 1
        
        reverse_rel = reverse_relationships[0]
        assert reverse_rel.source_id == "ahu-1"
        assert reverse_rel.target_id == "room-1"
        assert reverse_rel.reverse_relationship_id == relationship.relationship_id
        assert relationship.reverse_relationship_id == reverse_rel.relationship_id
    
    def test_bidirectional_navigation(self, relationship_manager):
        """Test navigation in both directions."""
        # Create bidirectional relationships
        rel1 = BIMRelationship(
            relationship_type=RelationshipType.CONTAINS,
            source_id="room-1",
            target_id="ahu-1",
            direction=RelationshipDirection.BIDIRECTIONAL
        )
        rel2 = BIMRelationship(
            relationship_type=RelationshipType.CONNECTS_TO,
            source_id="ahu-1",
            target_id="vav-1",
            direction=RelationshipDirection.BIDIRECTIONAL
        )
        
        relationship_manager.add_relationship(rel1)
        relationship_manager.add_relationship(rel2)
        
        # Test navigation from room to vav
        connected_to_room = relationship_manager.get_connected_elements("room-1")
        assert len(connected_to_room) == 1
        assert connected_to_room[0].id == "ahu-1"
        
        # Test navigation from vav to room (through ahu)
        connected_to_vav = relationship_manager.get_connected_elements("vav-1")
        assert len(connected_to_vav) == 1
        assert connected_to_vav[0].id == "ahu-1"
        
        # Test path finding
        path = relationship_manager.find_path("room-1", "vav-1")
        assert len(path) == 2  # room-1 -> ahu-1 -> vav-1
    
    def test_new_relationship_types(self, relationship_manager):
        """Test new relationship types (flow, control, adjacency, connectivity)."""
        # Test FLOW relationship
        flow_rel = BIMRelationship(
            relationship_type=RelationshipType.FLOW,
            source_id="ahu-1",
            target_id="vav-1",
            properties={"flow_type": "air", "flow_rate": 1000}
        )
        result = relationship_manager.add_relationship(flow_rel)
        assert result is True
        
        # Test CONTROL relationship
        control_rel = BIMRelationship(
            relationship_type=RelationshipType.CONTROL,
            source_id="panel-1",
            target_id="ahu-1",
            properties={"control_type": "electrical", "voltage": 480}
        )
        result = relationship_manager.add_relationship(control_rel)
        assert result is True
        
        # Test ADJACENCY relationship
        adjacency_rel = BIMRelationship(
            relationship_type=RelationshipType.ADJACENCY,
            source_id="room-1",
            target_id="room-2",
            properties={"adjacency_type": "wall_shared"}
        )
        result = relationship_manager.add_relationship(adjacency_rel)
        assert result is True
        
        # Test CONNECTIVITY relationship
        connectivity_rel = BIMRelationship(
            relationship_type=RelationshipType.CONNECTIVITY,
            source_id="panel-1",
            target_id="outlet-1",
            properties={"connection_type": "electrical", "wire_type": "THHN"}
        )
        result = relationship_manager.add_relationship(connectivity_rel)
        assert result is True
        
        # Verify all relationships were added
        assert len(relationship_manager.relationships) == 4
        
        # Test querying by relationship type
        flow_relationships = relationship_manager.get_relationships(relationship_type=RelationshipType.FLOW)
        assert len(flow_relationships) == 1
        assert flow_relationships[0].properties["flow_type"] == "air"
    
    def test_reference_integrity_validation(self, relationship_manager):
        """Test reference integrity validation."""
        # Add a valid relationship
        valid_rel = BIMRelationship(
            relationship_type=RelationshipType.CONTAINS,
            source_id="room-1",
            target_id="ahu-1"
        )
        relationship_manager.add_relationship(valid_rel)
        
        # Add an invalid relationship (non-existent element)
        invalid_rel = BIMRelationship(
            relationship_type=RelationshipType.CONTAINS,
            source_id="room-1",
            target_id="non-existent-element"
        )
        relationship_manager.add_relationship(invalid_rel)
        
        # Validate reference integrity
        integrity_report = relationship_manager.validate_reference_integrity()
        
        assert integrity_report['total_relationships'] == 2
        assert integrity_report['valid_references'] == 1
        assert integrity_report['invalid_references'] == 1
        assert "non-existent-element" in integrity_report['missing_elements']
        assert len(integrity_report['orphaned_relationships']) == 1
    
    def test_reference_integrity_repair(self, relationship_manager):
        """Test reference integrity repair."""
        # Add relationships with invalid references
        invalid_rel1 = BIMRelationship(
            relationship_type=RelationshipType.CONTAINS,
            source_id="room-1",
            target_id="non-existent-1"
        )
        invalid_rel2 = BIMRelationship(
            relationship_type=RelationshipType.CONNECTS_TO,
            source_id="non-existent-2",
            target_id="ahu-1"
        )
        
        # Force add these relationships (bypass validation)
        relationship_manager.relationships[invalid_rel1.relationship_id] = invalid_rel1
        relationship_manager.relationships[invalid_rel2.relationship_id] = invalid_rel2
        relationship_manager.stats['total_relationships'] += 2
        relationship_manager.stats['invalid_relationships'] += 2
        
        # Repair reference integrity
        repair_report = relationship_manager.repair_reference_integrity(auto_repair=True)
        
        assert repair_report['relationships_removed'] == 2
        assert repair_report['errors_fixed'] == 2
        assert len(relationship_manager.relationships) == 0
    
    def test_reference_integrity_repair_with_logging(self, relationship_manager):
        """Test reference integrity repair with logging."""
        # Add an invalid relationship
        invalid_rel = BIMRelationship(
            relationship_type=RelationshipType.CONTAINS,
            source_id="room-1",
            target_id="non-existent-element"
        )
        
        # Force add the relationship
        relationship_manager.relationships[invalid_rel.relationship_id] = invalid_rel
        relationship_manager.stats['total_relationships'] += 1
        relationship_manager.stats['invalid_relationships'] += 1
        
        # Repair with logging
        repair_report = relationship_manager.repair_reference_integrity(auto_repair=True)
        
        assert repair_report['relationships_removed'] == 1
        assert len(relationship_manager.repair_log) == 1
        
        log_entry = relationship_manager.repair_log[0]
        assert log_entry['action'] == 'remove_orphaned_relationship'
        assert log_entry['reason'] == 'missing_elements'
        assert 'timestamp' in log_entry
    
    def test_relationship_constraints(self, relationship_manager):
        """Test relationship constraints with new relationship types."""
        # Create constraint for flow relationship
        flow_constraint = RelationshipConstraint(
            max_distance=50.0,
            min_distance=1.0,
            system_compatibility=[SystemType.HVAC],
            device_compatibility=[DeviceCategory.AHU, DeviceCategory.VAV]
        )
        
        flow_rel = BIMRelationship(
            relationship_type=RelationshipType.FLOW,
            source_id="ahu-1",
            target_id="vav-1",
            constraints=flow_constraint,
            properties={"flow_type": "air", "flow_rate": 1000}
        )
        
        result = relationship_manager.add_relationship(flow_rel)
        assert result is True
        
        # Test constraint validation
        flow_rel.validate_against_model(relationship_manager.bim_model)
        assert flow_rel.is_valid is True
    
    def test_enhanced_relationship_properties(self, relationship_manager):
        """Test enhanced relationship properties for new types."""
        # Create relationship with rich properties
        flow_rel = BIMRelationship(
            relationship_type=RelationshipType.FLOW,
            source_id="ahu-1",
            target_id="vav-1",
            properties={
                "flow_type": "air",
                "flow_rate": 1000,
                "temperature": 55,
                "pressure": 2.5,
                "direction": "supply"
            }
        )
        
        relationship_manager.add_relationship(flow_rel)
        
        # Test property access
        assert flow_rel.get_property("flow_type") == "air"
        assert flow_rel.get_property("flow_rate") == 1000
        assert flow_rel.get_property("non_existent", "default") == "default"
        
        # Test property modification
        flow_rel.add_property("efficiency", 0.85)
        assert flow_rel.get_property("efficiency") == 0.85
    
    def test_relationship_strength_hierarchy(self, relationship_manager):
        """Test relationship strength hierarchy with new types."""
        # Create relationships with different strengths
        critical_flow = BIMRelationship(
            relationship_type=RelationshipType.FLOW,
            source_id="ahu-1",
            target_id="vav-1",
            strength=RelationshipStrength.CRITICAL
        )
        
        moderate_control = BIMRelationship(
            relationship_type=RelationshipType.CONTROL,
            source_id="panel-1",
            target_id="ahu-1",
            strength=RelationshipStrength.MODERATE
        )
        
        relationship_manager.add_relationship(critical_flow)
        relationship_manager.add_relationship(moderate_control)
        
        # Test strength-based queries
        critical_relationships = [
            rel for rel in relationship_manager.relationships.values()
            if rel.strength == RelationshipStrength.CRITICAL
        ]
        assert len(critical_relationships) == 1
        assert critical_relationships[0].relationship_type == RelationshipType.FLOW
    
    def test_relationship_type_compatibility(self, relationship_manager):
        """Test relationship type compatibility with new types."""
        # Test compatible flow relationship
        compatible_flow = BIMRelationship(
            relationship_type=RelationshipType.FLOW,
            source_id="ahu-1",  # HVAC device
            target_id="vav-1"   # HVAC device
        )
        result = relationship_manager.add_relationship(compatible_flow)
        assert result is True
        
        # Test incompatible relationship (should fail validation)
        incompatible_flow = BIMRelationship(
            relationship_type=RelationshipType.FLOW,
            source_id="room-1",  # Room (not HVAC device)
            target_id="ahu-1"    # HVAC device
        )
        
        # This should fail validation due to type incompatibility
        is_valid = incompatible_flow.validate_against_model(relationship_manager.bim_model)
        assert is_valid is False
        assert len(incompatible_flow.validation_errors) > 0
    
    def test_enhanced_path_finding(self, relationship_manager):
        """Test enhanced path finding with new relationship types."""
        # Create a complex network
        rel1 = BIMRelationship(
            relationship_type=RelationshipType.CONTAINS,
            source_id="room-1",
            target_id="ahu-1"
        )
        rel2 = BIMRelationship(
            relationship_type=RelationshipType.FLOW,
            source_id="ahu-1",
            target_id="vav-1"
        )
        rel3 = BIMRelationship(
            relationship_type=RelationshipType.CONTROL,
            source_id="panel-1",
            target_id="ahu-1"
        )
        rel4 = BIMRelationship(
            relationship_type=RelationshipType.CONNECTIVITY,
            source_id="panel-1",
            target_id="outlet-1"
        )
        
        relationship_manager.add_relationship(rel1)
        relationship_manager.add_relationship(rel2)
        relationship_manager.add_relationship(rel3)
        relationship_manager.add_relationship(rel4)
        
        # Test path finding with specific relationship types
        flow_path = relationship_manager.find_path(
            "ahu-1", "vav-1", 
            relationship_types=[RelationshipType.FLOW]
        )
        assert len(flow_path) == 1
        assert flow_path[0].relationship_type == RelationshipType.FLOW
        
        # Test path finding with multiple relationship types
        mixed_path = relationship_manager.find_path(
            "room-1", "vav-1",
            relationship_types=[RelationshipType.CONTAINS, RelationshipType.FLOW]
        )
        assert len(mixed_path) == 2
    
    def test_relationship_export_import_with_new_types(self, relationship_manager):
        """Test export/import with new relationship types."""
        # Create relationships with new types
        flow_rel = BIMRelationship(
            relationship_type=RelationshipType.FLOW,
            source_id="ahu-1",
            target_id="vav-1",
            properties={"flow_type": "air", "flow_rate": 1000}
        )
        
        control_rel = BIMRelationship(
            relationship_type=RelationshipType.CONTROL,
            source_id="panel-1",
            target_id="ahu-1",
            properties={"control_type": "electrical"}
        )
        
        relationship_manager.add_relationship(flow_rel)
        relationship_manager.add_relationship(control_rel)
        
        # Export relationships
        export_data = relationship_manager.export_relationships('json')
        
        # Create new manager and import
        new_model = BIMModel()
        new_manager = RelationshipManager(new_model)
        
        # Add the same elements to the new model
        for element in relationship_manager.bim_model.elements.values():
            new_model.add_element(element)
        
        # Import relationships
        import_result = new_manager.import_relationships(export_data, 'json')
        
        assert import_result['imported'] == 2
        assert import_result['failed'] == 0
        assert len(new_manager.relationships) == 2
        
        # Verify new relationship types are preserved
        flow_relationships = new_manager.get_relationships(relationship_type=RelationshipType.FLOW)
        assert len(flow_relationships) == 1
        assert flow_relationships[0].properties["flow_type"] == "air"
    
    def test_relationship_statistics(self, relationship_manager):
        """Test relationship statistics with new types."""
        # Add various relationship types
        relationships = [
            BIMRelationship(relationship_type=RelationshipType.CONTAINS, source_id="room-1", target_id="ahu-1"),
            BIMRelationship(relationship_type=RelationshipType.FLOW, source_id="ahu-1", target_id="vav-1"),
            BIMRelationship(relationship_type=RelationshipType.CONTROL, source_id="panel-1", target_id="ahu-1"),
            BIMRelationship(relationship_type=RelationshipType.ADJACENCY, source_id="room-1", target_id="room-2"),
            BIMRelationship(relationship_type=RelationshipType.CONNECTIVITY, source_id="panel-1", target_id="outlet-1")
        ]
        
        for rel in relationships:
            relationship_manager.add_relationship(rel)
        
        # Check statistics
        assert relationship_manager.stats['total_relationships'] == 5
        assert relationship_manager.stats['valid_relationships'] == 5
        assert relationship_manager.stats['bidirectional_relationships'] == 0  # None were bidirectional
        
        # Test relationship type distribution
        flow_rels = relationship_manager.get_relationships(relationship_type=RelationshipType.FLOW)
        control_rels = relationship_manager.get_relationships(relationship_type=RelationshipType.CONTROL)
        adjacency_rels = relationship_manager.get_relationships(relationship_type=RelationshipType.ADJACENCY)
        
        assert len(flow_rels) == 1
        assert len(control_rels) == 1
        assert len(adjacency_rels) == 1


if __name__ == "__main__":
    pytest.main([__file__]) 