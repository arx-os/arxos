"""
Tests for Advanced Relationship Management System

This module tests the comprehensive relationship management capabilities including
spatial relationships, system connections, validation, conflict detection, and resolution.
"""

import pytest
import json
from datetime import datetime, timezone
from typing import Dict, List, Any

from ..models.bim import (
    BIMModel, Room, Device, SystemType, DeviceCategory, Geometry, GeometryType,
    RoomType
)
from ..services.relationship_manager import (
    RelationshipManager, BIMRelationship, RelationshipType, RelationshipDirection,
    RelationshipStrength, RelationshipConstraint
)

class TestRelationshipManager:
    """Test cases for the RelationshipManager class."""
    
    @pytest.fixture
    def sample_bim_model(self):
        """Create a sample BIM model for testing."""
        model = BIMModel()
        
        # Add a room
        room = Room(
            id="room-1",
            name="Test Room",
            geometry=Geometry(
                type=GeometryType.POLYGON,
                coordinates=[[0, 0], [10, 0], [10, 10], [0, 10], [0, 0]]
            ),
            room_type=RoomType.OFFICE,
            room_number="101"
        )
        model.add_element(room)
        
        # Add some devices
        ahu = Device(
            id="ahu-1",
            name="Air Handler 1",
            geometry=Geometry(
                type=GeometryType.POINT,
                coordinates=[5, 5]
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
                coordinates=[3, 3]
            ),
            system_type=SystemType.HVAC,
            category=DeviceCategory.VAV
        )
        model.add_element(vav)
        
        panel = Device(
            id="panel-1",
            name="Electrical Panel 1",
            geometry=Geometry(
                type=GeometryType.POINT,
                coordinates=[8, 8]
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
    
    def test_create_relationship_manager(self, relationship_manager):
        """Test creating a relationship manager."""
        assert relationship_manager is not None
        assert len(relationship_manager.relationships) == 0
        assert relationship_manager.stats['total_relationships'] == 0
    
    def test_add_valid_relationship(self, relationship_manager):
        """Test adding a valid relationship."""
        relationship = BIMRelationship(
            relationship_type=RelationshipType.CONTAINS,
            source_id="room-1",
            target_id="ahu-1",
            strength=RelationshipStrength.IMPORTANT
        )
        
        result = relationship_manager.add_relationship(relationship)
        assert result is True
        assert len(relationship_manager.relationships) == 1
        assert relationship_manager.stats['valid_relationships'] == 1
    
    def test_add_invalid_relationship(self, relationship_manager):
        """Test adding an invalid relationship."""
        # Try to create relationship with non-existent element
        relationship = BIMRelationship(
            relationship_type=RelationshipType.CONTAINS,
            source_id="room-1",
            target_id="non-existent",
            strength=RelationshipStrength.IMPORTANT
        )
        
        result = relationship_manager.add_relationship(relationship)
        assert result is False
        assert len(relationship_manager.relationships) == 0
        assert relationship_manager.stats['invalid_relationships'] == 1
    
    def test_remove_relationship(self, relationship_manager):
        """Test removing a relationship."""
        # Add a relationship first
        relationship = BIMRelationship(
            relationship_type=RelationshipType.CONTAINS,
            source_id="room-1",
            target_id="ahu-1"
        )
        relationship_manager.add_relationship(relationship)
        
        # Remove it
        result = relationship_manager.remove_relationship(relationship.relationship_id)
        assert result is True
        assert len(relationship_manager.relationships) == 0
    
    def test_get_relationships_by_source(self, relationship_manager):
        """Test getting relationships by source ID."""
        # Add multiple relationships
        rel1 = BIMRelationship(
            relationship_type=RelationshipType.CONTAINS,
            source_id="room-1",
            target_id="ahu-1"
        )
        rel2 = BIMRelationship(
            relationship_type=RelationshipType.CONTAINS,
            source_id="room-1",
            target_id="vav-1"
        )
        rel3 = BIMRelationship(
            relationship_type=RelationshipType.CONNECTS_TO,
            source_id="ahu-1",
            target_id="vav-1"
        )
        
        relationship_manager.add_relationship(rel1)
        relationship_manager.add_relationship(rel2)
        relationship_manager.add_relationship(rel3)
        
        # Get relationships for room-1
        relationships = relationship_manager.get_relationships(source_id="room-1")
        assert len(relationships) == 2
        assert all(r.source_id == "room-1" for r in relationships)
    
    def test_get_relationships_by_type(self, relationship_manager):
        """Test getting relationships by type."""
        # Add relationships of different types
        rel1 = BIMRelationship(
            relationship_type=RelationshipType.CONTAINS,
            source_id="room-1",
            target_id="ahu-1"
        )
        rel2 = BIMRelationship(
            relationship_type=RelationshipType.CONNECTS_TO,
            source_id="ahu-1",
            target_id="vav-1"
        )
        rel3 = BIMRelationship(
            relationship_type=RelationshipType.SUPPLIES,
            source_id="ahu-1",
            target_id="vav-1"
        )
        
        relationship_manager.add_relationship(rel1)
        relationship_manager.add_relationship(rel2)
        relationship_manager.add_relationship(rel3)
        
        # Get CONTAINS relationships
        contains_rels = relationship_manager.get_relationships(relationship_type=RelationshipType.CONTAINS)
        assert len(contains_rels) == 1
        assert contains_rels[0].relationship_type == RelationshipType.CONTAINS
    
    def test_get_connected_elements(self, relationship_manager):
        """Test getting connected elements."""
        # Add relationships
        rel1 = BIMRelationship(
            relationship_type=RelationshipType.CONTAINS,
            source_id="room-1",
            target_id="ahu-1"
        )
        rel2 = BIMRelationship(
            relationship_type=RelationshipType.CONNECTS_TO,
            source_id="ahu-1",
            target_id="vav-1"
        )
        
        relationship_manager.add_relationship(rel1)
        relationship_manager.add_relationship(rel2)
        
        # Get elements connected to room-1
        connected = relationship_manager.get_connected_elements("room-1")
        assert len(connected) == 1
        assert connected[0].id == "ahu-1"
        
        # Get elements connected to ahu-1
        connected = relationship_manager.get_connected_elements("ahu-1")
        assert len(connected) == 2  # room-1 and vav-1
        connected_ids = [elem.id for elem in connected]
        assert "room-1" in connected_ids
        assert "vav-1" in connected_ids
    
    def test_find_path(self, relationship_manager):
        """Test finding paths between elements."""
        # Create a chain of relationships
        rel1 = BIMRelationship(
            relationship_type=RelationshipType.CONTAINS,
            source_id="room-1",
            target_id="ahu-1"
        )
        rel2 = BIMRelationship(
            relationship_type=RelationshipType.CONNECTS_TO,
            source_id="ahu-1",
            target_id="vav-1"
        )
        rel3 = BIMRelationship(
            relationship_type=RelationshipType.CONNECTS_TO,
            source_id="vav-1",
            target_id="outlet-1"
        )
        
        relationship_manager.add_relationship(rel1)
        relationship_manager.add_relationship(rel2)
        relationship_manager.add_relationship(rel3)
        
        # Find path from room-1 to outlet-1
        path = relationship_manager.find_path("room-1", "outlet-1")
        assert len(path) == 3
        assert path[0].source_id == "room-1"
        assert path[0].target_id == "ahu-1"
        assert path[1].source_id == "ahu-1"
        assert path[1].target_id == "vav-1"
        assert path[2].source_id == "vav-1"
        assert path[2].target_id == "outlet-1"
    
    def test_detect_conflicts(self, relationship_manager):
        """Test conflict detection."""
        # Add conflicting relationships (same source/target, different types)
        rel1 = BIMRelationship(
            relationship_type=RelationshipType.CONTAINS,
            source_id="room-1",
            target_id="ahu-1"
        )
        rel2 = BIMRelationship(
            relationship_type=RelationshipType.CONNECTS_TO,
            source_id="room-1",
            target_id="ahu-1"
        )
        
        relationship_manager.add_relationship(rel1)
        relationship_manager.add_relationship(rel2)
        
        # Detect conflicts
        conflicts = relationship_manager.detect_conflicts()
        assert len(conflicts) == 1
        assert conflicts[0]['type'] == 'conflicting_relationships'
    
    def test_resolve_conflicts(self, relationship_manager):
        """Test conflict resolution."""
        # Add conflicting relationships with different strengths
        rel1 = BIMRelationship(
            relationship_type=RelationshipType.CONTAINS,
            source_id="room-1",
            target_id="ahu-1",
            strength=RelationshipStrength.IMPORTANT
        )
        rel2 = BIMRelationship(
            relationship_type=RelationshipType.CONNECTS_TO,
            source_id="room-1",
            target_id="ahu-1",
            strength=RelationshipStrength.MINOR
        )
        
        relationship_manager.add_relationship(rel1)
        relationship_manager.add_relationship(rel2)
        
        # Detect and resolve conflicts
        conflicts = relationship_manager.detect_conflicts()
        resolution = relationship_manager.resolve_conflicts(conflicts)
        
        assert resolution['resolved'] == 1
        assert len(relationship_manager.relationships) == 1  # Weaker relationship removed
    
    def test_validate_all_relationships(self, relationship_manager):
        """Test validation of all relationships."""
        # Add valid and invalid relationships
        valid_rel = BIMRelationship(
            relationship_type=RelationshipType.CONTAINS,
            source_id="room-1",
            target_id="ahu-1"
        )
        invalid_rel = BIMRelationship(
            relationship_type=RelationshipType.CONTAINS,
            source_id="room-1",
            target_id="non-existent"
        )
        
        relationship_manager.add_relationship(valid_rel)
        relationship_manager.add_relationship(invalid_rel)
        
        # Validate all relationships
        results = relationship_manager.validate_all_relationships()
        assert results['total'] == 2
        assert results['valid'] == 1
        assert results['invalid'] == 1
        assert len(results['errors']) > 0
    
    def test_export_relationships(self, relationship_manager):
        """Test exporting relationships."""
        # Add a relationship
        relationship = BIMRelationship(
            relationship_type=RelationshipType.CONTAINS,
            source_id="room-1",
            target_id="ahu-1"
        )
        relationship_manager.add_relationship(relationship)
        
        # Export
        exported = relationship_manager.export_relationships('json')
        data = json.loads(exported)
        
        assert 'relationships' in data
        assert 'stats' in data
        assert len(data['relationships']) == 1
    
    def test_import_relationships(self, relationship_manager):
        """Test importing relationships."""
        # Create export data
        export_data = {
            'relationships': [
                {
                    'relationship_type': 'contains',
                    'source_id': 'room-1',
                    'target_id': 'ahu-1',
                    'strength': 'important'
                }
            ],
            'stats': {'total_relationships': 1},
            'exported_at': datetime.now(timezone.utc).isoformat()
        }
        
        # Import
        result = relationship_manager.import_relationships(json.dumps(export_data))
        assert result['imported'] == 1
        assert result['failed'] == 0
        assert len(relationship_manager.relationships) == 1
    
    def test_relationship_constraints(self, relationship_manager):
        """Test relationship constraints."""
        # Create relationship with distance constraint
        constraint = RelationshipConstraint(
            max_distance=10.0,
            min_distance=1.0,
            system_compatibility=[SystemType.HVAC]
        )
        
        relationship = BIMRelationship(
            relationship_type=RelationshipType.CONNECTS_TO,
            source_id="ahu-1",
            target_id="vav-1",
            constraints=constraint
        )
        
        result = relationship_manager.add_relationship(relationship)
        assert result is True  # Should be valid based on geometry
    
    def test_relationship_strength_hierarchy(self, relationship_manager):
        """Test relationship strength hierarchy."""
        # Create relationships with different strengths
        critical_rel = BIMRelationship(
            relationship_type=RelationshipType.CONTAINS,
            source_id="room-1",
            target_id="ahu-1",
            strength=RelationshipStrength.CRITICAL
        )
        moderate_rel = BIMRelationship(
            relationship_type=RelationshipType.CONNECTS_TO,
            source_id="room-1",
            target_id="ahu-1",
            strength=RelationshipStrength.MODERATE
        )
        
        relationship_manager.add_relationship(critical_rel)
        relationship_manager.add_relationship(moderate_rel)
        
        # Resolve conflicts - critical should win
        conflicts = relationship_manager.detect_conflicts()
        resolution = relationship_manager.resolve_conflicts(conflicts)
        
        assert resolution['resolved'] == 1
        remaining_rel = list(relationship_manager.relationships.values())[0]
        assert remaining_rel.strength == RelationshipStrength.CRITICAL
    
    def test_bidirectional_relationships(self, relationship_manager):
        """Test bidirectional relationships."""
        relationship = BIMRelationship(
            relationship_type=RelationshipType.ADJACENT,
            source_id="room-1",
            target_id="ahu-1",
            direction=RelationshipDirection.BIDIRECTIONAL
        )
        
        relationship_manager.add_relationship(relationship)
        
        # Should be able to find path in both directions
        path1 = relationship_manager.find_path("room-1", "ahu-1")
        path2 = relationship_manager.find_path("ahu-1", "room-1")
        
        assert len(path1) == 1
        assert len(path2) == 1
    
    def test_system_specific_relationships(self, relationship_manager):
        """Test system-specific relationship filtering."""
        # Add relationships for different systems
        hvac_rel = BIMRelationship(
            relationship_type=RelationshipType.CONNECTS_TO,
            source_id="ahu-1",
            target_id="vav-1"
        )
        electrical_rel = BIMRelationship(
            relationship_type=RelationshipType.CONNECTS_TO,
            source_id="panel-1",
            target_id="outlet-1"
        )
        
        relationship_manager.add_relationship(hvac_rel)
        relationship_manager.add_relationship(electrical_rel)
        
        # Get HVAC relationships
        hvac_rels = relationship_manager.get_relationships(system_type=SystemType.HVAC)
        assert len(hvac_rels) == 1
        assert hvac_rels[0].source_id == "ahu-1"
        
        # Get electrical relationships
        electrical_rels = relationship_manager.get_relationships(system_type=SystemType.ELECTRICAL)
        assert len(electrical_rels) == 1
        assert electrical_rels[0].source_id == "panel-1"

class TestBIMRelationship:
    """Test cases for the BIMRelationship class."""
    
    def test_create_relationship(self):
        """Test creating a basic relationship."""
        relationship = BIMRelationship(
            relationship_type=RelationshipType.CONTAINS,
            source_id="room-1",
            target_id="device-1"
        )
        
        assert relationship.relationship_type == RelationshipType.CONTAINS
        assert relationship.source_id == "room-1"
        assert relationship.target_id == "device-1"
        assert relationship.is_valid is True
    
    def test_relationship_validation(self):
        """Test relationship validation."""
        relationship = BIMRelationship(
            relationship_type=RelationshipType.CONTAINS,
            source_id="room-1",
            target_id="device-1"
        )
        
        # Create a simple BIM model for validation
        model = BIMModel()
        room = Room(
            id="room-1",
            name="Test Room",
            geometry=Geometry(type=GeometryType.POLYGON, coordinates=[[0, 0], [10, 10]])
        )
        device = Device(
            id="device-1",
            name="Test Device",
            geometry=Geometry(type=GeometryType.POINT, coordinates=[5, 5]),
            system_type=SystemType.HVAC,
            category=DeviceCategory.AHU
        )
        model.add_element(room)
        model.add_element(device)
        
        # Validate relationship
        result = relationship.validate_against_model(model)
        assert result is True
        assert relationship.is_valid is True
    
    def test_relationship_properties(self):
        """Test relationship property management."""
        relationship = BIMRelationship(
            relationship_type=RelationshipType.CONNECTS_TO,
            source_id="device-1",
            target_id="device-2"
        )
        
        # Add properties
        relationship.add_property("connection_type", "electrical")
        relationship.add_property("voltage", 120)
        
        # Get properties
        assert relationship.get_property("connection_type") == "electrical"
        assert relationship.get_property("voltage") == 120
        assert relationship.get_property("non_existent", "default") == "default"
    
    def test_relationship_constraints(self):
        """Test relationship constraints."""
        constraint = RelationshipConstraint(
            max_distance=10.0,
            min_distance=1.0,
            system_compatibility=[SystemType.HVAC]
        )
        
        relationship = BIMRelationship(
            relationship_type=RelationshipType.CONNECTS_TO,
            source_id="device-1",
            target_id="device-2",
            constraints=constraint
        )
        
        assert relationship.constraints == constraint
        assert relationship.constraints.max_distance == 10.0
        assert relationship.constraints.min_distance == 1.0
    
    def test_invalid_relationship(self):
        """Test creating invalid relationships."""
        # Same source and target
        with pytest.raises(ValueError):
            BIMRelationship(
                relationship_type=RelationshipType.CONTAINS,
                source_id="room-1",
                target_id="room-1"
            )
        
        # Invalid IDs
        with pytest.raises(ValueError):
            BIMRelationship(
                relationship_type=RelationshipType.CONTAINS,
                source_id="",
                target_id="device-1"
            )

if __name__ == "__main__":
    pytest.main([__file__]) 