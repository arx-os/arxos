"""
Test suite for Infrastructure as Code functionality

Tests precision management, digital elements, and GUS integration.

Author: Arxos Engineering Team
Date: 2024-12-19
Version: 1.0.0
"""

import pytest
import json
from decimal import Decimal
from datetime import datetime

from svgx_engine.core.precision import (
    precision_manager,
    PrecisionLevel,
    PrecisionDisplayMode,
    PrecisionConfig
)
from svgx_engine.services.infrastructure_as_code import (
    infrastructure_service,
    DigitalElement,
    ElementType,
    MeasurementUnit
)


class TestPrecisionManagement:
    """Test precision management functionality."""
    
    def test_create_precise_value(self):
        """Test creating precise decimal values."""
        # Test basic value creation
        value = precision_manager.create_precise_value(100.5)
        assert isinstance(value, Decimal)
        assert value == Decimal('100.5')
        
        # Test with unit conversion
        micron_value = precision_manager.create_precise_value(1, "μm")
        assert micron_value == Decimal('0.001')  # 1 micron = 0.001mm
        
        # Test with string input
        string_value = precision_manager.create_precise_value("50.25 mm")
        assert string_value == Decimal('50.25')
    
    def test_format_for_display(self):
        """Test formatting values for display."""
        value = Decimal('100.001')
        
        # Test decimal format
        decimal_str = precision_manager.format_for_display(value, PrecisionDisplayMode.DECIMAL)
        assert "100.001 mm" in decimal_str
        
        # Test scientific format
        scientific_str = precision_manager.format_for_display(value, PrecisionDisplayMode.SCIENTIFIC)
        assert "100001 μm" in scientific_str
        
        # Test micron format
        micron_str = precision_manager.format_for_display(value, PrecisionDisplayMode.MICRON)
        assert "100001.000 μm" in micron_str
    
    def test_precision_validation(self):
        """Test precision validation."""
        # Valid micron precision
        valid_value = Decimal('100.001')
        assert precision_manager.validate_precision(valid_value, PrecisionLevel.MICRON)
        
        # Invalid precision (too few decimal places)
        invalid_value = Decimal('100.1')
        assert not precision_manager.validate_precision(invalid_value, PrecisionLevel.MICRON)
    
    def test_precision_config(self):
        """Test precision configuration."""
        config = PrecisionConfig(
            internal_precision=12,
            display_mode=PrecisionDisplayMode.MICRON,
            display_decimal_places=3
        )
        
        manager = precision_manager.__class__(config)
        info = manager.get_precision_info()
        
        assert info["internal_precision"] == 12
        assert info["display_mode"] == "micron"
        assert info["display_decimal_places"] == 3


class TestDigitalElement:
    """Test digital element functionality."""
    
    def test_create_element(self):
        """Test creating a digital element."""
        element = DigitalElement(
            name="Test Wall",
            element_type=ElementType.WALL,
            position_x=Decimal('100.001'),
            position_y=Decimal('200.002'),
            position_z=Decimal('0.000'),
            width=Decimal('300.000'),
            height=Decimal('2500.000'),
            depth=Decimal('200.000'),
            properties={"material": "concrete", "fire_rating": "2h"},
            precision_level=PrecisionLevel.MICRON
        )
        
        assert element.name == "Test Wall"
        assert element.element_type == ElementType.WALL
        assert element.position_x == Decimal('100.001')
        assert element.position_y == Decimal('200.002')
        assert element.position_z == Decimal('0.000')
        assert element.width == Decimal('300.000')
        assert element.height == Decimal('2500.000')
        assert element.depth == Decimal('200.000')
        assert element.properties["material"] == "concrete"
        assert element.precision_level == PrecisionLevel.MICRON
    
    def test_element_volume_calculation(self):
        """Test volume calculation."""
        element = DigitalElement(
            width=Decimal('100.000'),
            height=Decimal('200.000'),
            depth=Decimal('50.000')
        )
        
        volume = element.get_volume()
        expected_volume = Decimal('100.000') * Decimal('200.000') * Decimal('50.000')
        assert volume == expected_volume
    
    def test_element_surface_area_calculation(self):
        """Test surface area calculation."""
        element = DigitalElement(
            width=Decimal('100.000'),
            height=Decimal('200.000'),
            depth=Decimal('50.000')
        )
        
        surface_area = element.get_surface_area()
        # 2 * (w*h + w*d + h*d)
        expected_area = Decimal('2') * (
            Decimal('100.000') * Decimal('200.000') +
            Decimal('100.000') * Decimal('50.000') +
            Decimal('200.000') * Decimal('50.000')
        )
        assert surface_area == expected_area
    
    def test_element_connections(self):
        """Test element connection management."""
        element = DigitalElement(name="Test Element")
        
        # Add connections
        element.add_connection("element_1")
        element.add_connection("element_2")
        
        assert "element_1" in element.connections
        assert "element_2" in element.connections
        assert len(element.connections) == 2
        
        # Test duplicate prevention
        element.add_connection("element_1")
        assert len(element.connections) == 2  # No duplicate added
    
    def test_element_constraints(self):
        """Test element constraint management."""
        element = DigitalElement(name="Test Element")
        
        # Add constraints
        element.add_constraint("parallel", target_id="element_1", tolerance=Decimal('0.001'))
        element.add_constraint("perpendicular", target_id="element_2", tolerance=Decimal('0.001'))
        
        assert len(element.constraints) == 2
        assert element.constraints[0]["type"] == "parallel"
        assert element.constraints[1]["type"] == "perpendicular"
    
    def test_element_properties(self):
        """Test element property management."""
        element = DigitalElement(name="Test Element")
        
        # Update properties
        element.update_property("material", "steel")
        element.update_property("color", "red")
        
        assert element.properties["material"] == "steel"
        assert element.properties["color"] == "red"
    
    def test_svgx_element_conversion(self):
        """Test conversion to SVGX XML element."""
        element = DigitalElement(
            name="Test Element",
            element_type=ElementType.WALL,
            position_x=Decimal('100.000'),
            position_y=Decimal('200.000'),
            position_z=Decimal('0.000'),
            width=Decimal('300.000'),
            height=Decimal('2500.000'),
            depth=Decimal('200.000'),
            properties={"material": "concrete"},
            connections=["element_1", "element_2"],
            precision_level=PrecisionLevel.MICRON
        )
        
        svgx_element = element.to_svgx_element()
        
        assert svgx_element.tag == "digital_element"
        assert svgx_element.get("name") == "Test Element"
        assert svgx_element.get("type") == "wall"
        assert svgx_element.get("precision_level") == "MICRON"
        
        # Check position
        position = svgx_element.find("position")
        assert position.get("x") == "100.000"
        assert position.get("y") == "200.000"
        assert position.get("z") == "0.000"
        
        # Check dimensions
        dimensions = svgx_element.find("dimensions")
        assert dimensions.get("width") == "300.000"
        assert dimensions.get("height") == "2500.000"
        assert dimensions.get("depth") == "200.000"
    
    def test_gus_instruction_generation(self):
        """Test natural language instruction generation."""
        element = DigitalElement(
            name="Test Wall",
            element_type=ElementType.WALL,
            position_x=Decimal('100.000'),
            position_y=Decimal('200.000'),
            position_z=Decimal('0.000'),
            width=Decimal('300.000'),
            height=Decimal('2500.000'),
            depth=Decimal('200.000'),
            properties={"material": "concrete"},
            connections=["element_1"]
        )
        
        instruction = element.to_gus_instruction()
        
        assert "wall element" in instruction.lower()
        assert "positioned at" in instruction.lower()
        assert "width" in instruction.lower()
        assert "height" in instruction.lower()
        assert "depth" in instruction.lower()
        assert "material" in instruction.lower()
        assert "connected to" in instruction.lower()


class TestInfrastructureAsCodeService:
    """Test infrastructure as code service functionality."""
    
    def setup_method(self):
        """Setup test method."""
        # Clear existing elements
        infrastructure_service.elements.clear()
    
    def test_create_element(self):
        """Test creating elements through service."""
        element = infrastructure_service.create_element(
            element_type=ElementType.WALL,
            name="Test Wall",
            position_x=Decimal('100.000'),
            position_y=Decimal('200.000'),
            position_z=Decimal('0.000'),
            width=Decimal('300.000'),
            height=Decimal('2500.000'),
            depth=Decimal('200.000')
        )
        
        assert element.id in infrastructure_service.elements
        assert infrastructure_service.elements[element.id] == element
        assert element.name == "Test Wall"
        assert element.element_type == ElementType.WALL
    
    def test_get_element(self):
        """Test retrieving elements."""
        element = infrastructure_service.create_element(
            element_type=ElementType.WALL,
            name="Test Wall"
        )
        
        retrieved = infrastructure_service.get_element(element.id)
        assert retrieved == element
        
        # Test non-existent element
        assert infrastructure_service.get_element("non_existent") is None
    
    def test_update_element(self):
        """Test updating elements."""
        element = infrastructure_service.create_element(
            element_type=ElementType.WALL,
            name="Original Name"
        )
        
        # Update element
        success = infrastructure_service.update_element(
            element.id,
            name="Updated Name",
            position_x=Decimal('150.000')
        )
        
        assert success
        updated_element = infrastructure_service.get_element(element.id)
        assert updated_element.name == "Updated Name"
        assert updated_element.position_x == Decimal('150.000')
    
    def test_delete_element(self):
        """Test deleting elements."""
        element = infrastructure_service.create_element(
            element_type=ElementType.WALL,
            name="Test Wall"
        )
        
        # Delete element
        success = infrastructure_service.delete_element(element.id)
        assert success
        assert element.id not in infrastructure_service.elements
        
        # Test deleting non-existent element
        assert not infrastructure_service.delete_element("non_existent")
    
    def test_svgx_document_generation(self):
        """Test SVGX document generation."""
        # Create test elements
        infrastructure_service.create_element(
            element_type=ElementType.WALL,
            name="Wall 1",
            position_x=Decimal('100.000'),
            position_y=Decimal('200.000'),
            position_z=Decimal('0.000'),
            width=Decimal('300.000'),
            height=Decimal('2500.000'),
            depth=Decimal('200.000')
        )
        
        infrastructure_service.create_element(
            element_type=ElementType.DOOR,
            name="Door 1",
            position_x=Decimal('150.000'),
            position_y=Decimal('200.000'),
            position_z=Decimal('0.000'),
            width=Decimal('100.000'),
            height=Decimal('2100.000'),
            depth=Decimal('50.000')
        )
        
        # Generate SVGX document
        svgx_content = infrastructure_service.to_svgx_document()
        
        assert "<?xml" in svgx_content
        assert "svgx_infrastructure" in svgx_content
        assert "digital_element" in svgx_content
        assert "Wall 1" in svgx_content
        assert "Door 1" in svgx_content
    
    def test_gus_instructions_generation(self):
        """Test GUS instructions generation."""
        # Create test elements
        infrastructure_service.create_element(
            element_type=ElementType.WALL,
            name="Wall 1"
        )
        
        infrastructure_service.create_element(
            element_type=ElementType.DOOR,
            name="Door 1"
        )
        
        # Generate instructions
        instructions = infrastructure_service.to_gus_instructions()
        
        assert len(instructions) > 0
        assert any("wall" in instruction.lower() for instruction in instructions)
        assert any("door" in instruction.lower() for instruction in instructions)
    
    def test_export_for_gus(self):
        """Test export for GUS processing."""
        # Create test element
        infrastructure_service.create_element(
            element_type=ElementType.WALL,
            name="Test Wall"
        )
        
        # Test SVGX export
        svgx_export = infrastructure_service.export_for_gus("svgx")
        assert "<?xml" in svgx_export
        
        # Test instructions export
        instructions_export = infrastructure_service.export_for_gus("instructions")
        assert "wall" in instructions_export.lower()
        
        # Test JSON export
        json_export = infrastructure_service.export_for_gus("json")
        json_data = json.loads(json_export)
        assert "elements" in json_data
        assert len(json_data["elements"]) == 1
    
    def test_import_from_svgx(self):
        """Test importing from SVGX content."""
        # Create test SVGX content
        test_svgx = '''<?xml version="1.0" ?>
<svgx_infrastructure version="1.0" created="2024-12-19T10:00:00" precision_level="MICRON">
  <precision_info internal_precision="12" display_mode="decimal" display_decimal_places="3" unit_system="metric" min_precision_mm="0.000000000001" min_precision_micron="0.000000001" supported_modes="['decimal', 'scientific', 'engineering', 'micron', 'millimeter', 'inch']" supported_levels="['MICRON', 'SUB_MICRON', 'NANOMETER', 'ULTRA_PRECISE']"/>
  <elements>
    <digital_element id="test-id" name="Test Wall" type="wall" precision_level="MICRON">
      <position x="100.000" y="200.000" z="0.000"/>
      <dimensions width="300.000" height="2500.000" depth="200.000"/>
      <properties>
        <property key="material" value="concrete"/>
      </properties>
      <connections/>
      <constraints/>
      <metadata/>
      <timestamps created="2024-12-19T10:00:00" updated="2024-12-19T10:00:00"/>
    </digital_element>
  </elements>
</svgx_infrastructure>'''
        
        # Import SVGX content
        infrastructure_service.import_from_svgx(test_svgx)
        
        # Verify import
        assert len(infrastructure_service.elements) == 1
        element = list(infrastructure_service.elements.values())[0]
        assert element.name == "Test Wall"
        assert element.element_type == ElementType.WALL
        assert element.position_x == Decimal('100.000')
    
    def test_statistics(self):
        """Test statistics generation."""
        # Create test elements
        infrastructure_service.create_element(
            element_type=ElementType.WALL,
            name="Wall 1",
            width=Decimal('100.000'),
            height=Decimal('200.000'),
            depth=Decimal('50.000')
        )
        
        infrastructure_service.create_element(
            element_type=ElementType.DOOR,
            name="Door 1",
            width=Decimal('50.000'),
            height=Decimal('100.000'),
            depth=Decimal('25.000')
        )
        
        # Get statistics
        stats = infrastructure_service.get_statistics()
        
        assert stats["total_elements"] == 2
        assert stats["elements_by_type"]["wall"] == 1
        assert stats["elements_by_type"]["door"] == 1
        assert stats["precision_level"] == "MICRON"
        assert "precision_info" in stats


class TestPrecisionIntegration:
    """Test precision integration with infrastructure."""
    
    def test_micron_precision_handling(self):
        """Test handling of micron-level precision."""
        # Create element with micron precision
        element = infrastructure_service.create_element(
            element_type=ElementType.WALL,
            name="Precise Wall",
            position_x=precision_manager.create_precise_value("100.001 μm"),
            position_y=precision_manager.create_precise_value("200.002 μm"),
            position_z=precision_manager.create_precise_value("0.000 μm"),
            width=precision_manager.create_precise_value("300.000 μm"),
            height=precision_manager.create_precise_value("2500.000 μm"),
            depth=precision_manager.create_precise_value("200.000 μm"),
            precision_level=PrecisionLevel.MICRON
        )
        
        # Verify precision
        assert precision_manager.validate_precision(element.position_x, PrecisionLevel.MICRON)
        assert precision_manager.validate_precision(element.position_y, PrecisionLevel.MICRON)
        assert precision_manager.validate_precision(element.width, PrecisionLevel.MICRON)
        
        # Test display formatting
        display_x = precision_manager.format_for_display(element.position_x, PrecisionDisplayMode.MICRON)
        assert "100.001 μm" in display_x
    
    def test_engineering_compliance(self):
        """Test engineering compliance validation."""
        from svgx_engine.core.precision import PrecisionValidator
        
        # Test ISO standard compliance
        valid_value = Decimal('100.000')  # 100mm
        assert PrecisionValidator.validate_engineering_compliance(valid_value, "ISO")
        
        # Test ASME standard compliance
        valid_inch_value = Decimal('4.000')  # 4 inches
        assert PrecisionValidator.validate_engineering_compliance(valid_inch_value, "ASME")


if __name__ == "__main__":
    pytest.main([__file__]) 