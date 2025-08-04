"""
Test suite for CAD Primitives and Constraints functionality

Tests the integration of CAD primitives (Line, Arc, Circle, Rectangle, Polyline)
and constraints (Parallel, Perpendicular, Equal, Fixed) with the infrastructure
as code system.

Author: Arxos Engineering Team
Date: 2024-12-19
Version: 1.0.0
"""

import pytest
import json
from decimal import Decimal
from datetime import datetime

from svgx_engine.core.primitives import Line, Arc, Circle, Rectangle, Polyline
from svgx_engine.core.constraints import (
    Constraint, ParallelConstraint, PerpendicularConstraint, 
    EqualConstraint, FixedConstraint, ConstraintType
)
from svgx_engine.core.precision import PrecisionLevel
from svgx_engine.services.infrastructure_as_code import (
    infrastructure_service,
    DigitalElement,
    ElementType,
    MeasurementUnit
)

class TestCADPrimitives:
    """Test CAD primitive creation and serialization."""
    
    def test_line_creation(self):
        """Test Line primitive creation with micron precision."""
        line = Line(
            start_x=Decimal("10.001"),
            start_y=Decimal("20.002"),
            end_x=Decimal("30.003"),
            end_y=Decimal("40.004")
        )
        
        assert line.start_x == Decimal("10.001")
        assert line.start_y == Decimal("20.002")
        assert line.end_x == Decimal("30.003")
        assert line.end_y == Decimal("40.004")
        assert line.precision_level == PrecisionLevel.MICRON
    
    def test_circle_creation(self):
        """Test Circle primitive creation."""
        circle = Circle(
            center_x=Decimal("50.0"),
            center_y=Decimal("60.0"),
            radius=Decimal("25.5")
        )
        
        assert circle.center_x == Decimal("50.0")
        assert circle.center_y == Decimal("60.0")
        assert circle.radius == Decimal("25.5")
    
    def test_rectangle_creation(self):
        """Test Rectangle primitive creation."""
        rect = Rectangle(
            x=Decimal("0.0"),
            y=Decimal("0.0"),
            width=Decimal("100.0"),
            height=Decimal("50.0")
        )
        
        assert rect.x == Decimal("0.0")
        assert rect.y == Decimal("0.0")
        assert rect.width == Decimal("100.0")
        assert rect.height == Decimal("50.0")
    
    def test_arc_creation(self):
        """Test Arc primitive creation."""
        arc = Arc(
            center_x=Decimal("100.0"),
            center_y=Decimal("100.0"),
            radius=Decimal("30.0"),
            start_angle=Decimal("0.0"),
            end_angle=Decimal("90.0")
        )
        
        assert arc.center_x == Decimal("100.0")
        assert arc.center_y == Decimal("100.0")
        assert arc.radius == Decimal("30.0")
        assert arc.start_angle == Decimal("0.0")
        assert arc.end_angle == Decimal("90.0")
    
    def test_polyline_creation(self):
        """Test Polyline primitive creation."""
        points = [
            {"x": Decimal("0.0"), "y": Decimal("0.0")},
            {"x": Decimal("10.0"), "y": Decimal("0.0")},
            {"x": Decimal("10.0"), "y": Decimal("10.0")},
            {"x": Decimal("0.0"), "y": Decimal("10.0")}
        ]
        
        polyline = Polyline(points=points, closed=True)
        
        assert len(polyline.points) == 4
        assert polyline.closed == True
        assert polyline.points[0]["x"] == Decimal("0.0")
    
    def test_line_svgx_serialization(self):
        """Test Line serialization to SVGX XML."""
        line = Line(
            start_x=Decimal("10.0"),
            start_y=Decimal("20.0"),
            end_x=Decimal("30.0"),
            end_y=Decimal("40.0")
        )
        
        svgx_element = line.to_svgx()
        
        assert svgx_element.tag == "line"
        assert svgx_element.get("start_x") == "10.0"
        assert svgx_element.get("start_y") == "20.0"
        assert svgx_element.get("end_x") == "30.0"
        assert svgx_element.get("end_y") == "40.0"
        assert svgx_element.get("precision_level") == "MICRON"
    
    def test_circle_svgx_serialization(self):
        """Test Circle serialization to SVGX XML."""
        circle = Circle(
            center_x=Decimal("50.0"),
            center_y=Decimal("60.0"),
            radius=Decimal("25.5")
        )
        
        svgx_element = circle.to_svgx()
        
        assert svgx_element.tag == "circle"
        assert svgx_element.get("center_x") == "50.0"
        assert svgx_element.get("center_y") == "60.0"
        assert svgx_element.get("radius") == "25.5"

class TestConstraints:
    """Test constraint creation and validation."""
    
    def test_parallel_constraint_creation(self):
        """Test ParallelConstraint creation."""
        constraint = ParallelConstraint(
            target_ids=["line1", "line2"],
            parameters={"tolerance": 0.001}
        )
        
        assert constraint.constraint_type == ConstraintType.PARALLEL
        assert constraint.target_ids == ["line1", "line2"]
        assert constraint.parameters == {"tolerance": 0.001}
        assert constraint.enabled == True
    
    def test_perpendicular_constraint_creation(self):
        """Test PerpendicularConstraint creation."""
        constraint = PerpendicularConstraint(
            target_ids=["line1", "line2"],
            parameters={"angle": 90.0}
        )
        
        assert constraint.constraint_type == ConstraintType.PERPENDICULAR
        assert constraint.target_ids == ["line1", "line2"]
        assert constraint.parameters == {"angle": 90.0}
    
    def test_equal_constraint_creation(self):
        """Test EqualConstraint creation."""
        constraint = EqualConstraint(
            target_ids=["circle1", "circle2"],
            parameters={"property": "radius"}
        )
        
        assert constraint.constraint_type == ConstraintType.EQUAL
        assert constraint.target_ids == ["circle1", "circle2"]
        assert constraint.parameters == {"property": "radius"}
    
    def test_fixed_constraint_creation(self):
        """Test FixedConstraint creation."""
        constraint = FixedConstraint(
            target_ids=["point1"],
            parameters={"x": 10.0, "y": 20.0}
        )
        
        assert constraint.constraint_type == ConstraintType.FIXED
        assert constraint.target_ids == ["point1"]
        assert constraint.parameters == {"x": 10.0, "y": 20.0}
    
    def test_constraint_validation(self):
        """Test constraint validation."""
        constraint = ParallelConstraint(
            target_ids=["line1", "line2"],
            parameters={"tolerance": 0.001}
        )
        
        # Mock elements for validation
        elements = {
            "line1": {"type": "line", "data": "mock"},
            "line2": {"type": "line", "data": "mock"}
        }
        
        # Should return True for now (placeholder validation)
        assert constraint.validate(elements) == True
    
    def test_disabled_constraint(self):
        """Test disabled constraint always validates."""
        constraint = ParallelConstraint(
            target_ids=["line1", "line2"],
            parameters={"tolerance": 0.001}
        )
        constraint.enabled = False
        
        elements = {"line1": "mock", "line2": "mock"}
        assert constraint.validate(elements) == True

class TestInfrastructureIntegration:
    """Test integration of CAD primitives and constraints with infrastructure."""
    
    def setup_method(self):
        """Clear infrastructure service before each test."""
        infrastructure_service.elements.clear()
    
    def test_create_cad_element(self):
        """Test creating a digital element with CAD primitives."""
        # Create CAD primitives
        line = Line(
            start_x=Decimal("0.0"),
            start_y=Decimal("0.0"),
            end_x=Decimal("100.0"),
            end_y=Decimal("0.0")
        )
        
        circle = Circle(
            center_x=Decimal("50.0"),
            center_y=Decimal("50.0"),
            radius=Decimal("25.0")
        )
        
        # Create element with CAD primitives
        element = infrastructure_service.create_cad_element(
            element_type=ElementType.WALL,
            primitives=[line, circle],
            position_x=Decimal("0.0"),
            position_y=Decimal("0.0"),
            position_z=Decimal("0.0"),
            width=Decimal("100.0"),
            height=Decimal("100.0"),
            depth=Decimal("10.0")
        )
        
        assert len(element.cad_primitives) == 2
        assert isinstance(element.cad_primitives[0], Line)
        assert isinstance(element.cad_primitives[1], Circle)
        assert element.element_type == ElementType.WALL
    
    def test_add_constraint_to_element(self):
        """Test adding constraints to digital elements."""
        # Create element
        element = infrastructure_service.create_element(
            element_type=ElementType.WALL,
            position_x=Decimal("0.0"),
            position_y=Decimal("0.0"),
            position_z=Decimal("0.0"),
            width=Decimal("100.0"),
            height=Decimal("100.0"),
            depth=Decimal("10.0")
        )
        
        # Add constraint
        constraint = ParallelConstraint(
            target_ids=["line1", "line2"],
            parameters={"tolerance": 0.001}
        )
        
        success = infrastructure_service.add_constraint_to_element(element.id, constraint)
        assert success == True
        
        # Verify constraint was added
        updated_element = infrastructure_service.get_element(element.id)
        assert len(updated_element.constraints) == 1
        assert updated_element.constraints[0].constraint_type == ConstraintType.PARALLEL
    
    def test_element_with_cad_and_constraints(self):
        """Test element with both CAD primitives and constraints."""
        # Create CAD primitives
        line = Line(
            start_x=Decimal("0.0"),
            start_y=Decimal("0.0"),
            end_x=Decimal("100.0"),
            end_y=Decimal("0.0")
        )
        
        # Create element with CAD primitives
        element = infrastructure_service.create_cad_element(
            element_type=ElementType.WALL,
            primitives=[line],
            position_x=Decimal("0.0"),
            position_y=Decimal("0.0"),
            position_z=Decimal("0.0"),
            width=Decimal("100.0"),
            height=Decimal("100.0"),
            depth=Decimal("10.0")
        )
        
        # Add constraint
        constraint = FixedConstraint(
            target_ids=["point1"],
            parameters={"x": 0.0, "y": 0.0}
        )
        
        infrastructure_service.add_constraint_to_element(element.id, constraint)
        
        # Verify both CAD primitives and constraints
        updated_element = infrastructure_service.get_element(element.id)
        assert len(updated_element.cad_primitives) == 1
        assert len(updated_element.constraints) == 1
        assert isinstance(updated_element.cad_primitives[0], Line)
        assert updated_element.constraints[0].constraint_type == ConstraintType.FIXED
    
    def test_svgx_serialization_with_cad_and_constraints(self):
        """Test SVGX serialization with CAD primitives and constraints."""
        # Create element with CAD primitives
        line = Line(
            start_x=Decimal("0.0"),
            start_y=Decimal("0.0"),
            end_x=Decimal("100.0"),
            end_y=Decimal("0.0")
        )
        
        element = infrastructure_service.create_cad_element(
            element_type=ElementType.WALL,
            primitives=[line],
            position_x=Decimal("0.0"),
            position_y=Decimal("0.0"),
            position_z=Decimal("0.0"),
            width=Decimal("100.0"),
            height=Decimal("100.0"),
            depth=Decimal("10.0")
        )
        
        # Add constraint
        constraint = EqualConstraint(
            target_ids=["line1", "line2"],
            parameters={"property": "length"}
        )
        
        infrastructure_service.add_constraint_to_element(element.id, constraint)
        
        # Serialize to SVGX
        svgx_element = element.to_svgx_element()
        
        # Verify CAD primitives
        cad_primitives_el = svgx_element.find("cad_primitives")
        assert cad_primitives_el is not None
        assert len(cad_primitives_el.findall("line")) == 1
        
        # Verify constraints
        constraints_el = svgx_element.find("constraints")
        assert constraints_el is not None
        assert len(constraints_el.findall("constraint")) == 1
        
        constraint_el = constraints_el.find("constraint")
        assert constraint_el.get("type") == "equal"
        assert constraint_el.get("enabled") == "True"
    
    def test_gus_instruction_with_cad_and_constraints(self):
        """Test GUS instruction generation with CAD primitives and constraints."""
        # Create element with CAD primitives
        line = Line(
            start_x=Decimal("0.0"),
            start_y=Decimal("0.0"),
            end_x=Decimal("100.0"),
            end_y=Decimal("0.0")
        )
        
        element = infrastructure_service.create_cad_element(
            element_type=ElementType.WALL,
            primitives=[line],
            position_x=Decimal("0.0"),
            position_y=Decimal("0.0"),
            position_z=Decimal("0.0"),
            width=Decimal("100.0"),
            height=Decimal("100.0"),
            depth=Decimal("10.0")
        )
        
        # Add constraint
        constraint = ParallelConstraint(
            target_ids=["line1", "line2"],
            parameters={"tolerance": 0.001}
        )
        
        infrastructure_service.add_constraint_to_element(element.id, constraint)
        
        # Generate GUS instruction
        instruction = element.to_gus_instruction()
        
        assert "wall" in instruction.lower()
        assert "1 CAD primitives" in instruction
        assert "1 constraints" in instruction
        assert "position" in instruction
        assert "dimensions" in instruction

class TestPrecisionIntegration:
    """Test micron precision integration with CAD primitives and constraints."""
    
    def test_micron_precision_in_primitives(self):
        """Test that CAD primitives maintain micron precision."""
        # Create line with micron precision
        line = Line(
            start_x=Decimal("10.001"),
            start_y=Decimal("20.002"),
            end_x=Decimal("30.003"),
            end_y=Decimal("40.004")
        )
        
        # Verify precision is maintained
        assert line.start_x == Decimal("10.001")
        assert line.start_y == Decimal("20.002")
        assert line.end_x == Decimal("30.003")
        assert line.end_y == Decimal("40.004")
        
        # Verify precision level
        assert line.precision_level == PrecisionLevel.MICRON
    
    def test_micron_precision_in_elements(self):
        """Test that digital elements maintain micron precision with CAD primitives."""
        # Create CAD primitive with micron precision
        circle = Circle(
            center_x=Decimal("50.001"),
            center_y=Decimal("60.002"),
            radius=Decimal("25.003")
        )
        
        # Create element with micron precision
        element = infrastructure_service.create_cad_element(
            element_type=ElementType.WALL,
            primitives=[circle],
            position_x=Decimal("0.001"),
            position_y=Decimal("0.002"),
            position_z=Decimal("0.003"),
            width=Decimal("100.001"),
            height=Decimal("100.002"),
            depth=Decimal("10.003")
        )
        
        # Verify precision is maintained
        assert element.position_x == Decimal("0.001")
        assert element.position_y == Decimal("0.002")
        assert element.position_z == Decimal("0.003")
        assert element.width == Decimal("100.001")
        assert element.height == Decimal("100.002")
        assert element.depth == Decimal("10.003")
        
        # Verify CAD primitive precision
        assert len(element.cad_primitives) == 1
        circle_primitive = element.cad_primitives[0]
        assert circle_primitive.center_x == Decimal("50.001")
        assert circle_primitive.center_y == Decimal("60.002")
        assert circle_primitive.radius == Decimal("25.003")

if __name__ == "__main__":
    pytest.main([__file__]) 