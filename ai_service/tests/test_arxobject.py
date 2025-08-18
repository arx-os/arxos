"""
Unit tests for ArxObject models and confidence scoring
"""

import pytest
from models.arxobject import (
    ConfidenceScore, ArxObject, ArxObjectType,
    ValidationState, Relationship, RelationshipType,
    ConversionResult, ValidationData, ValidationImpact
)


class TestConfidenceScore:
    """Test confidence score calculations"""
    
    def test_confidence_score_creation(self):
        """Test creating a confidence score with automatic overall calculation"""
        cs = ConfidenceScore(
            classification=0.8,
            position=0.9,
            properties=0.7,
            relationships=0.6,
            overall=0.0
        )
        
        # Overall should be calculated automatically
        expected_overall = (0.8 * 0.35 + 0.9 * 0.30 + 0.7 * 0.20 + 0.6 * 0.15)
        assert abs(cs.overall - expected_overall) < 0.01
    
    def test_confidence_clamping(self):
        """Test that confidence values are clamped between 0 and 1"""
        cs = ConfidenceScore(
            classification=1.5,  # Should be clamped to 1.0
            position=-0.1,       # Should be clamped to 0.0
            properties=0.5,
            relationships=0.5,
            overall=0.0
        )
        
        assert cs.classification <= 1.0
        assert cs.position >= 0.0
    
    def test_is_high_confidence(self, sample_confidence_score):
        """Test high confidence detection"""
        sample_confidence_score.overall = 0.90
        assert sample_confidence_score.overall > 0.85
        
        sample_confidence_score.overall = 0.80
        assert not (sample_confidence_score.overall > 0.85)
    
    def test_is_low_confidence(self, sample_confidence_score):
        """Test low confidence detection"""
        sample_confidence_score.overall = 0.50
        assert sample_confidence_score.overall < 0.6
        
        sample_confidence_score.overall = 0.70
        assert not (sample_confidence_score.overall < 0.6)


class TestArxObject:
    """Test ArxObject model"""
    
    def test_arxobject_creation(self, sample_arxobject):
        """Test creating an ArxObject"""
        assert sample_arxobject.id == "test_wall_001"
        assert sample_arxobject.type == ArxObjectType.WALL
        assert sample_arxobject.validation_state == ValidationState.PENDING
        assert len(sample_arxobject.relationships) == 1
    
    def test_arxobject_serialization(self, sample_arxobject):
        """Test ArxObject JSON serialization"""
        json_data = sample_arxobject.model_dump_json()
        assert "test_wall_001" in json_data
        assert "wall" in json_data
        assert "confidence" in json_data
    
    def test_arxobject_validation_state(self):
        """Test validation state enum"""
        assert ValidationState.PENDING == "pending"
        assert ValidationState.COMPLETE == "complete"
        assert ValidationState.PARTIAL == "partial"
        assert ValidationState.CONFLICT == "conflict"


class TestRelationships:
    """Test ArxObject relationships"""
    
    def test_relationship_types(self):
        """Test relationship type enum values"""
        assert RelationshipType.ADJACENT_TO == "adjacent_to"
        assert RelationshipType.CONTAINS == "contains"
        assert RelationshipType.POWERS == "powers"
        assert RelationshipType.UPSTREAM == "upstream"
    
    def test_relationship_creation(self):
        """Test creating a relationship"""
        rel = Relationship(
            type=RelationshipType.ADJACENT_TO,
            target_id="test_room_001",
            confidence=0.85,
            properties={"distance": 0.0}
        )
        
        assert rel.type == RelationshipType.ADJACENT_TO
        assert rel.target_id == "test_room_001"
        assert rel.confidence == 0.85
        assert rel.properties["distance"] == 0.0


class TestConversionResult:
    """Test conversion result model"""
    
    def test_conversion_result_confidence_calculation(self, sample_arxobject):
        """Test automatic overall confidence calculation from ArxObjects"""
        result = ConversionResult(
            arxobjects=[sample_arxobject, sample_arxobject],
            overall_confidence=0.0,
            uncertainties=[],
            processing_time=1.5
        )
        
        # Overall confidence should be average of object confidences
        expected = sample_arxobject.confidence.overall
        assert abs(result.overall_confidence - expected) < 0.01
    
    def test_empty_conversion_result(self):
        """Test conversion result with no objects"""
        result = ConversionResult(
            arxobjects=[],
            overall_confidence=0.0,
            uncertainties=[],
            processing_time=0.1
        )
        
        assert result.overall_confidence == 0.0
        assert len(result.arxobjects) == 0


class TestValidation:
    """Test validation models"""
    
    def test_validation_data_creation(self):
        """Test creating validation data"""
        validation = ValidationData(
            object_id="test_wall_001",
            validation_type="dimension",
            measured_value=10.5,
            units="meters",
            validator="field_tech_01",
            confidence=0.95
        )
        
        assert validation.object_id == "test_wall_001"
        assert validation.validation_type == "dimension"
        assert validation.measured_value == 10.5
        assert validation.confidence == 0.95
    
    def test_validation_impact(self):
        """Test validation impact model"""
        impact = ValidationImpact(
            object_id="test_wall_001",
            old_confidence=0.60,
            new_confidence=0.85,
            confidence_improvement=0.25,
            cascaded_objects=["test_wall_002", "test_wall_003"],
            cascaded_count=2,
            pattern_learned=True,
            total_confidence_gain=0.75,
            time_saved=15.0
        )
        
        assert impact.confidence_improvement == 0.25
        assert impact.cascaded_count == 2
        assert impact.pattern_learned is True
        assert impact.time_saved == 15.0


class TestArxObjectTypes:
    """Test ArxObject type enum"""
    
    def test_structural_types(self):
        """Test structural element types"""
        assert ArxObjectType.WALL == "wall"
        assert ArxObjectType.COLUMN == "column"
        assert ArxObjectType.BEAM == "beam"
        assert ArxObjectType.FOUNDATION == "foundation"
    
    def test_mep_types(self):
        """Test MEP system types"""
        assert ArxObjectType.ELECTRICAL_PANEL == "electrical_panel"
        assert ArxObjectType.HVAC_UNIT == "hvac_unit"
        assert ArxObjectType.PLUMBING_FIXTURE == "plumbing_fixture"
    
    def test_spatial_types(self):
        """Test spatial element types"""
        assert ArxObjectType.BUILDING == "building"
        assert ArxObjectType.FLOOR == "floor"
        assert ArxObjectType.ROOM == "room"
        assert ArxObjectType.CORRIDOR == "corridor"