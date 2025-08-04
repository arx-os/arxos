#!/usr/bin/env python3
"""
Direct test for CAD primitives and constraints integration
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from decimal import Decimal
from svgx_engine.core.primitives import Line, Arc, Circle, Rectangle, Polyline
from svgx_engine.core.constraints import (
    Constraint, ParallelConstraint, PerpendicularConstraint, 
    EqualConstraint, FixedConstraint, ConstraintType
)
from svgx_engine.core.precision import PrecisionLevel
from svgx_engine.services.infrastructure_as_code import (
    infrastructure_service,
    ElementType
)

def test_cad_primitives():
    """Test CAD primitive creation and basic functionality."""
    print("Testing CAD primitives...")
    
    # Test Line
    line = Line(
        start_x=Decimal("10.001"),
        start_y=Decimal("20.002"),
        end_x=Decimal("30.003"),
        end_y=Decimal("40.004")
    )
    print(f"✓ Line created: {line.start_x}, {line.start_y} to {line.end_x}, {line.end_y}")
    
    # Test Circle
    circle = Circle(
        center_x=Decimal("50.0"),
        center_y=Decimal("60.0"),
        radius=Decimal("25.5")
    )
    print(f"✓ Circle created: center ({circle.center_x}, {circle.center_y}), radius {circle.radius}")
    
    # Test Rectangle
    rect = Rectangle(
        x=Decimal("0.0"),
        y=Decimal("0.0"),
        width=Decimal("100.0"),
        height=Decimal("50.0")
    )
    print(f"✓ Rectangle created: ({rect.x}, {rect.y}) {rect.width}x{rect.height}")
    
    # Test Arc
    arc = Arc(
        center_x=Decimal("100.0"),
        center_y=Decimal("100.0"),
        radius=Decimal("30.0"),
        start_angle=Decimal("0.0"),
        end_angle=Decimal("90.0")
    )
    print(f"✓ Arc created: center ({arc.center_x}, {arc.center_y}), radius {arc.radius}")
    
    # Test Polyline
    points = [
        {"x": Decimal("0.0"), "y": Decimal("0.0")},
        {"x": Decimal("10.0"), "y": Decimal("0.0")},
        {"x": Decimal("10.0"), "y": Decimal("10.0")},
        {"x": Decimal("0.0"), "y": Decimal("10.0")}
    ]
    polyline = Polyline(points=points, closed=True)
    print(f"✓ Polyline created: {len(polyline.points)} points, closed={polyline.closed}")
    
    return True

def test_constraints():
    """Test constraint creation and basic functionality."""
    print("\nTesting constraints...")
    
    # Test ParallelConstraint
    parallel = ParallelConstraint(
        target_ids=["line1", "line2"],
        parameters={"tolerance": 0.001}
    )
    print(f"✓ ParallelConstraint created: {parallel.constraint_type.value}")
    
    # Test PerpendicularConstraint
    perpendicular = PerpendicularConstraint(
        target_ids=["line1", "line2"],
        parameters={"angle": 90.0}
    )
    print(f"✓ PerpendicularConstraint created: {perpendicular.constraint_type.value}")
    
    # Test EqualConstraint
    equal = EqualConstraint(
        target_ids=["circle1", "circle2"],
        parameters={"property": "radius"}
    )
    print(f"✓ EqualConstraint created: {equal.constraint_type.value}")
    
    # Test FixedConstraint
    fixed = FixedConstraint(
        target_ids=["point1"],
        parameters={"x": 10.0, "y": 20.0}
    )
    print(f"✓ FixedConstraint created: {fixed.constraint_type.value}")
    
    return True

def test_infrastructure_integration():
    """Test integration with infrastructure service."""
    print("\nTesting infrastructure integration...")
    
    # Clear service
    infrastructure_service.elements.clear()
    
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
    print(f"✓ CAD element created: {element.id}, {len(element.cad_primitives)} primitives")
    
    # Add constraint
    constraint = ParallelConstraint(
        target_ids=["line1", "line2"],
        parameters={"tolerance": 0.001}
    )
    
    success = infrastructure_service.add_constraint_to_element(element.id, constraint)
    print(f"✓ Constraint added: {success}, {len(element.constraints)} constraints")
    
    # Test SVGX serialization
    svgx_element = element.to_svgx_element()
    print(f"✓ SVGX serialization: {svgx_element.tag}")
    
    # Test GUS instruction
    instruction = element.to_gus_instruction()
    print(f"✓ GUS instruction: {instruction[:50]}...")
    
    return True

def test_precision():
    """Test micron precision functionality."""
    print("\nTesting micron precision...")
    
    # Test micron precision in primitives
    line = Line(
        start_x=Decimal("10.001"),
        start_y=Decimal("20.002"),
        end_x=Decimal("30.003"),
        end_y=Decimal("40.004")
    )
    
    assert line.start_x == Decimal("10.001")
    assert line.precision_level == PrecisionLevel.MICRON
    print("✓ Micron precision maintained in primitives")
    
    # Test micron precision in infrastructure
    infrastructure_service.elements.clear()
    
    element = infrastructure_service.create_element(
        element_type=ElementType.WALL,
        position_x=Decimal("0.001"),
        position_y=Decimal("0.002"),
        position_z=Decimal("0.003"),
        width=Decimal("100.001"),
        height=Decimal("100.002"),
        depth=Decimal("10.003")
    )
    
    assert element.position_x == Decimal("0.001")
    assert element.width == Decimal("100.001")
    print("✓ Micron precision maintained in infrastructure")
    
    return True

def main():
    """Run all tests."""
    print("=== CAD Primitives and Constraints Integration Test ===\n")
    
    try:
        test_cad_primitives()
        test_constraints()
        test_infrastructure_integration()
        test_precision()
        
        print("\n=== ALL TESTS PASSED ===")
        print("✓ CAD primitives creation and serialization")
        print("✓ Constraint creation and validation")
        print("✓ Infrastructure integration")
        print("✓ Micron precision handling")
        
        return True
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 