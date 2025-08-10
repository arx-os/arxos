#!/usr/bin/env python3
"""
Phase 2: Constraint System Demo.

Demonstrates the complete constraint validation system including:
- Spatial relationship constraints
- Building code compliance validation
- System interdependency checks
- Real-time constraint evaluation
- Integrated conflict and constraint validation
- Comprehensive reporting and analytics
"""

import asyncio
import time
import json
import sys
from pathlib import Path

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

from core.spatial import (
    SpatialConflictEngine, ArxObject, ArxObjectType, ArxObjectPrecision, 
    ArxObjectGeometry, ArxObjectMetadata, BoundingBox3D
)
from core.constraints import (
    IntegratedValidator, ConstraintEngine, ConstraintReporter,
    DistanceConstraint, ClearanceConstraint, AlignmentConstraint,
    FireSafetyConstraint, ElectricalCodeConstraint,
    InterdependencyConstraint, CapacityConstraint
)

print("🏗️ Arxos Phase 2: Constraint System Demo")
print("=" * 50)


def create_complex_building_model():
    """Create complex building model for constraint validation."""
    
    print("\n📦 Creating complex building model...")
    
    # Initialize spatial engine
    world_bounds = BoundingBox3D(-200.0, -200.0, -20.0, 200.0, 200.0, 50.0)
    spatial_engine = SpatialConflictEngine(world_bounds)
    
    # Create diverse building components
    building_objects = []
    
    # Structural system
    structural_objects = []
    for i in range(8):
        beam_geometry = ArxObjectGeometry(
            x=i * 25.0, y=10.0, z=12.0,
            length=20.0, width=1.0, height=2.0,
            shape_type="rectangular"
        )
        beam_metadata = ArxObjectMetadata(
            name=f"Steel Beam {i+1}",
            material="steel",
            manufacturer="SteelCorp",
            custom_attributes={
                "load_capacity": f"{8000 + i * 500} lbs",
                "fire_rating": "2hr"
            }
        )
        beam = ArxObject(
            arxobject_type=ArxObjectType.STRUCTURAL_BEAM,
            geometry=beam_geometry,
            metadata=beam_metadata,
            precision=ArxObjectPrecision.COARSE
        )
        beam.id = f"beam_{i}"
        structural_objects.append(beam)
    
    building_objects.extend(structural_objects)
    
    # Electrical system
    electrical_objects = []
    
    # Electrical panels
    for i in range(2):
        panel_geometry = ArxObjectGeometry(
            x=20.0 + i * 100.0, y=5.0, z=4.0,
            length=2.0, width=0.5, height=3.0,
            shape_type="rectangular"
        )
        panel_metadata = ArxObjectMetadata(
            name=f"Main Panel {i+1}",
            material="steel",
            manufacturer="ElectricCorp",
            custom_attributes={
                "capacity": "200A",
                "voltage": "480V",
                "phases": "3"
            }
        )
        panel = ArxObject(
            arxobject_type=ArxObjectType.ELECTRICAL_PANEL,
            geometry=panel_geometry,
            metadata=panel_metadata,
            precision=ArxObjectPrecision.FINE
        )
        panel.id = f"panel_{i}"
        electrical_objects.append(panel)
    
    # Electrical outlets (some with alignment issues)
    outlet_positions = [
        (15.0, 15.0, 1.0),  # Normal
        (35.0, 15.2, 1.0),  # Slightly misaligned
        (55.0, 14.8, 1.0),  # Slightly misaligned
        (75.0, 15.0, 1.0),  # Normal
        (95.0, 15.0, 1.0),  # Normal
        (115.0, 14.5, 1.0), # Misaligned
        (135.0, 15.0, 1.0), # Normal
        (155.0, 15.0, 1.0)  # Normal
    ]
    
    for i, (x, y, z) in enumerate(outlet_positions):
        outlet_geometry = ArxObjectGeometry(
            x=x, y=y, z=z,
            length=0.3, width=0.1, height=0.2,
            shape_type="rectangular"
        )
        outlet_metadata = ArxObjectMetadata(
            name=f"Outlet {i+1}",
            material="plastic",
            manufacturer="ElectricCorp",
            custom_attributes={
                "voltage": "120V",
                "amperage": "20A",
                "circuit": f"Panel-{i//4 + 1}-{i%4 + 1}"
            }
        )
        outlet = ArxObject(
            arxobject_type=ArxObjectType.ELECTRICAL_OUTLET,
            geometry=outlet_geometry,
            metadata=outlet_metadata,
            precision=ArxObjectPrecision.FINE
        )
        outlet.id = f"outlet_{i}"
        electrical_objects.append(outlet)
    
    building_objects.extend(electrical_objects)
    
    # HVAC system
    hvac_objects = []
    
    # HVAC units
    for i in range(2):
        unit_geometry = ArxObjectGeometry(
            x=50.0 + i * 80.0, y=30.0, z=15.0,
            length=6.0, width=4.0, height=3.0,
            shape_type="rectangular"
        )
        unit_metadata = ArxObjectMetadata(
            name=f"HVAC Unit {i+1}",
            material="aluminum",
            manufacturer="HVAC Corp",
            custom_attributes={
                "capacity": "60000 BTU/hr",
                "type": "rooftop_unit",
                "refrigerant": "R410A"
            }
        )
        unit = ArxObject(
            arxobject_type=ArxObjectType.HVAC_UNIT,
            geometry=unit_geometry,
            metadata=unit_metadata,
            precision=ArxObjectPrecision.STANDARD
        )
        unit.id = f"hvac_{i}"
        hvac_objects.append(unit)
    
    # HVAC ducts (some with potential conflicts)
    duct_positions = [
        (25.0, 20.0, 12.5),  # Near beam - potential conflict
        (50.0, 25.0, 11.0),  # Normal
        (75.0, 20.0, 12.8),  # Near beam - potential conflict
        (100.0, 25.0, 11.0), # Normal
        (125.0, 20.0, 12.0), # Near beam - potential conflict
        (150.0, 25.0, 11.0)  # Normal
    ]
    
    for i, (x, y, z) in enumerate(duct_positions):
        duct_geometry = ArxObjectGeometry(
            x=x, y=y, z=z,
            length=15.0, width=1.0, height=1.0,
            shape_type="rectangular"
        )
        duct_metadata = ArxObjectMetadata(
            name=f"Supply Duct {i+1}",
            material="galvanized_steel",
            custom_attributes={
                "airflow_cfm": f"{1200 + i * 200}",
                "insulation": "R6",
                "pressure_class": "2_inch_wc"
            }
        )
        duct = ArxObject(
            arxobject_type=ArxObjectType.HVAC_DUCT,
            geometry=duct_geometry,
            metadata=duct_metadata,
            precision=ArxObjectPrecision.STANDARD
        )
        duct.id = f"duct_{i}"
        hvac_objects.append(duct)
    
    building_objects.extend(hvac_objects)
    
    # Fire safety system
    fire_objects = []
    
    # Fire sprinklers (some with spacing violations)
    sprinkler_positions = [
        (20.0, 20.0, 9.0),   # Normal
        (40.0, 20.0, 9.0),   # 20ft spacing - violation (should be <15ft)
        (55.0, 20.0, 9.0),   # Normal
        (70.0, 20.0, 9.0),   # Normal  
        (90.0, 20.0, 9.0),   # 20ft spacing - violation
        (105.0, 20.0, 9.0),  # Normal
        (120.0, 20.0, 9.0),  # Normal
        (140.0, 20.0, 9.0)   # 20ft spacing - violation
    ]
    
    for i, (x, y, z) in enumerate(sprinkler_positions):
        sprinkler_geometry = ArxObjectGeometry(
            x=x, y=y, z=z,
            length=0.2, width=0.2, height=0.3,
            shape_type="cylindrical"
        )
        sprinkler_metadata = ArxObjectMetadata(
            name=f"Fire Sprinkler {i+1}",
            material="brass",
            manufacturer="FireSafety Corp",
            custom_attributes={
                "coverage_area": "225 sq ft",
                "temperature_rating": "165F",
                "response": "quick"
            }
        )
        sprinkler = ArxObject(
            arxobject_type=ArxObjectType.FIRE_SPRINKLER,
            geometry=sprinkler_geometry,
            metadata=sprinkler_metadata,
            precision=ArxObjectPrecision.FINE
        )
        sprinkler.id = f"sprinkler_{i}"
        fire_objects.append(sprinkler)
    
    building_objects.extend(fire_objects)
    
    print(f"📊 Created {len(building_objects)} building objects:")
    print(f"   • {len(structural_objects)} structural elements")
    print(f"   • {len(electrical_objects)} electrical components")
    print(f"   • {len(hvac_objects)} HVAC components")
    print(f"   • {len(fire_objects)} fire safety components")
    
    # Add all objects to spatial engine
    for obj in building_objects:
        spatial_engine.add_arxobject(obj)
    
    return spatial_engine, building_objects


async def demo_spatial_constraints():
    """Demonstrate spatial constraint validation."""
    
    print("\n📐 Spatial Constraints Demo")
    print("-" * 30)
    
    spatial_engine, objects = create_complex_building_model()
    constraint_engine = ConstraintEngine(spatial_engine)
    
    # Test distance constraint
    distance_constraint = DistanceConstraint(
        name="Fire Sprinkler Maximum Spacing",
        distance_type="maximum",
        required_distance=15.0,  # 15ft max spacing
        measurement_method="center_to_center"
    )
    distance_constraint.set_parameter('source_types', {ArxObjectType.FIRE_SPRINKLER})
    distance_constraint.set_parameter('target_types', {ArxObjectType.FIRE_SPRINKLER})
    
    constraint_engine.register_constraint(distance_constraint)
    
    # Test clearance constraint
    clearance_constraint = ClearanceConstraint(
        name="Electrical Panel Working Clearance",
        required_clearance=3.0,  # 3ft clearance
        clearance_direction="front"
    )
    constraint_engine.register_constraint(clearance_constraint)
    
    # Test alignment constraint
    alignment_constraint = AlignmentConstraint(
        name="Electrical Outlet Alignment",
        alignment_type="horizontal",
        alignment_tolerance=0.3  # 3.6 inch tolerance
    )
    constraint_engine.register_constraint(alignment_constraint)
    
    print("🔍 Evaluating spatial constraints...")
    
    # Get fire sprinklers for distance check
    sprinklers = [obj for obj in objects if obj.type == ArxObjectType.FIRE_SPRINKLER]
    sprinkler_results = []
    
    for sprinkler in sprinklers[:4]:  # Test first 4 sprinklers
        results = constraint_engine.evaluate_object_constraints(sprinkler)
        sprinkler_results.extend(results)
    
    # Get outlets for alignment check
    outlets = [obj for obj in objects if obj.type == ArxObjectType.ELECTRICAL_OUTLET]
    outlet_results = constraint_engine.evaluate_object_constraints(outlets[0])  # Test alignment on first outlet
    
    # Get panels for clearance check
    panels = [obj for obj in objects if obj.type == ArxObjectType.ELECTRICAL_PANEL]
    panel_results = []
    for panel in panels:
        results = constraint_engine.evaluate_object_constraints(panel)
        panel_results.extend(results)
    
    all_results = sprinkler_results + outlet_results + panel_results
    
    # Report results
    total_violations = sum(len(result.violations) for result in all_results)
    print(f"📋 Spatial constraint evaluation complete:")
    print(f"   • {len(all_results)} constraints evaluated")
    print(f"   • {total_violations} violations found")
    
    for result in all_results:
        if result.violations:
            print(f"   ⚠️ {result.constraint_name}: {len(result.violations)} violations")
            for violation in result.violations[:2]:  # Show first 2
                print(f"      - {violation.description}")


async def demo_building_code_constraints():
    """Demonstrate building code compliance validation."""
    
    print("\n📋 Building Code Constraints Demo")
    print("-" * 35)
    
    spatial_engine, objects = create_complex_building_model()
    constraint_engine = ConstraintEngine(spatial_engine)
    
    # Fire safety constraint
    fire_constraint = FireSafetyConstraint(
        name="NFPA 13 Sprinkler Spacing",
        safety_requirement="sprinkler_spacing"
    )
    constraint_engine.register_constraint(fire_constraint)
    
    # Electrical code constraint
    electrical_constraint = ElectricalCodeConstraint(
        name="NEC Panel Working Space",
        electrical_requirement="panel_clearance"  
    )
    constraint_engine.register_constraint(electrical_constraint)
    
    print("🔍 Evaluating building code compliance...")
    
    # Test fire safety
    sprinklers = [obj for obj in objects if obj.type == ArxObjectType.FIRE_SPRINKLER]
    fire_results = []
    
    for sprinkler in sprinklers:
        results = constraint_engine.evaluate_object_constraints(sprinkler)
        fire_results.extend(results)
    
    # Test electrical code
    panels = [obj for obj in objects if obj.type == ArxObjectType.ELECTRICAL_PANEL]
    electrical_results = []
    
    for panel in panels:
        results = constraint_engine.evaluate_object_constraints(panel)
        electrical_results.extend(results)
    
    all_results = fire_results + electrical_results
    
    # Report code compliance
    critical_violations = sum(
        len([v for v in result.violations if v.severity.value == "critical"])
        for result in all_results
    )
    
    error_violations = sum(
        len([v for v in result.violations if v.severity.value == "error"])
        for result in all_results
    )
    
    print(f"📋 Building code evaluation complete:")
    print(f"   • {len(all_results)} code constraints evaluated")
    print(f"   • {critical_violations} critical violations (safety)")
    print(f"   • {error_violations} code violations (compliance)")
    
    for result in all_results:
        if result.violations:
            print(f"   🔴 {result.constraint_name}:")
            for violation in result.violations[:2]:
                print(f"      - {violation.get_display_message()}")


async def demo_system_constraints():
    """Demonstrate system interdependency and capacity constraints."""
    
    print("\n⚡ System Constraints Demo")
    print("-" * 25)
    
    spatial_engine, objects = create_complex_building_model()
    constraint_engine = ConstraintEngine(spatial_engine)
    
    # Electrical interdependency constraint
    electrical_interdep = InterdependencyConstraint(
        name="Electrical Circuit Dependencies",
        dependency_type="electrical_circuit"
    )
    constraint_engine.register_constraint(electrical_interdep)
    
    # Electrical capacity constraint  
    electrical_capacity = CapacityConstraint(
        name="Electrical Panel Load Analysis",
        capacity_type="electrical_load"
    )
    constraint_engine.register_constraint(electrical_capacity)
    
    print("🔍 Evaluating system constraints...")
    
    # Test electrical system
    electrical_objects = [obj for obj in objects 
                         if obj.type in {ArxObjectType.ELECTRICAL_PANEL, ArxObjectType.ELECTRICAL_OUTLET}]
    
    system_results = []
    for obj in electrical_objects:
        results = constraint_engine.evaluate_object_constraints(obj)
        system_results.extend(results)
    
    # Report system analysis
    interdep_violations = sum(
        len(result.violations) for result in system_results
        if "interdependency" in result.constraint_name.lower()
    )
    
    capacity_violations = sum(
        len(result.violations) for result in system_results
        if "capacity" in result.constraint_name.lower()
    )
    
    print(f"📋 System constraint evaluation complete:")
    print(f"   • {len(system_results)} system constraints evaluated")
    print(f"   • {interdep_violations} interdependency issues")
    print(f"   • {capacity_violations} capacity issues")
    
    for result in system_results:
        if result.violations:
            print(f"   ⚡ {result.constraint_name}:")
            for violation in result.violations[:1]:
                print(f"      - {violation.description}")


async def demo_integrated_validation():
    """Demonstrate integrated conflict and constraint validation."""
    
    print("\n🔄 Integrated Validation Demo")
    print("-" * 30)
    
    spatial_engine, objects = create_complex_building_model()
    validator = IntegratedValidator(spatial_engine, "Arxos Constraint Demo Project")
    
    print("🔍 Running comprehensive validation...")
    
    # Run comprehensive validation
    validation_result = await validator.validate_comprehensive(
        include_conflicts=True,
        include_constraints=True
    )
    
    print(f"📊 Comprehensive validation complete:")
    print(f"   • Total objects: {validation_result.total_objects}")
    print(f"   • Objects with issues: {validation_result.objects_with_issues}")
    print(f"   • Spatial conflicts: {validation_result.conflict_count}")
    print(f"   • Constraint violations: {validation_result.constraint_violations}")
    print(f"   • Critical issues: {validation_result.critical_issues_count}")
    print(f"   • Overall compliance: {validation_result.overall_compliance_score:.1%}")
    print(f"   • Validation time: {validation_result.validation_time_ms:.1f}ms")
    
    # Show immediate actions
    if validation_result.immediate_actions:
        print("\n🚨 Immediate Actions Required:")
        for action in validation_result.immediate_actions:
            print(f"   • {action}")
    
    # Show optimization opportunities
    if validation_result.optimization_opportunities:
        print("\n💡 Optimization Opportunities:")
        for opportunity in validation_result.optimization_opportunities[:3]:
            print(f"   • {opportunity}")
    
    return validation_result


async def demo_comprehensive_reporting():
    """Demonstrate comprehensive constraint reporting."""
    
    print("\n📄 Comprehensive Reporting Demo") 
    print("-" * 33)
    
    spatial_engine, objects = create_complex_building_model()
    validator = IntegratedValidator(spatial_engine, "Arxos Demo Project")
    
    # Run validation
    validation_result = await validator.validate_comprehensive()
    
    # Generate unified report
    report = validator.generate_unified_report(validation_result)
    
    print("📊 Generating comprehensive report...")
    
    # Print summary
    validator.constraint_reporter.print_summary(report)
    
    return report


async def demo_system_specific_validation():
    """Demonstrate system-specific validation."""
    
    print("\n🏢 System-Specific Validation Demo")
    print("-" * 35)
    
    spatial_engine, objects = create_complex_building_model()
    validator = IntegratedValidator(spatial_engine, "System Analysis Project")
    
    # Test different building systems
    systems_to_test = [
        ArxObjectType.ELECTRICAL_OUTLET,
        ArxObjectType.HVAC_DUCT,
        ArxObjectType.FIRE_SPRINKLER
    ]
    
    for system_type in systems_to_test:
        system_name = system_type.value.replace('_', ' ').title()
        print(f"\n🔍 Validating {system_name} System:")
        
        system_result = validator.validate_system(system_type)
        
        print(f"   • Objects: {system_result.total_objects}")
        print(f"   • Conflicts: {system_result.conflict_count}")
        print(f"   • Violations: {system_result.constraint_violations}")
        print(f"   • Compliance: {system_result.overall_compliance_score:.1%}")
        
        if system_result.immediate_actions:
            print(f"   • Actions needed: {len(system_result.immediate_actions)}")


async def main():
    """Run comprehensive constraint system demo."""
    
    print("🎬 Starting comprehensive constraint system demo...")
    
    # Run all demos
    await demo_spatial_constraints()
    await demo_building_code_constraints()
    await demo_system_constraints()
    validation_result = await demo_integrated_validation()
    await demo_comprehensive_reporting()
    await demo_system_specific_validation()
    
    print("\n🎉 Phase 2 Constraint System Demo Completed!")
    print("\n📋 Summary of Constraint System Features:")
    print("   ✅ Spatial relationship constraints (distance, clearance, alignment)")
    print("   ✅ Building code compliance validation (fire, electrical, accessibility)")
    print("   ✅ System interdependency and capacity analysis")  
    print("   ✅ Real-time constraint evaluation with performance metrics")
    print("   ✅ Integrated conflict and constraint validation")
    print("   ✅ Comprehensive reporting and analytics")
    print("   ✅ System-specific validation and health scoring")
    
    print(f"\n🚀 Phase 2: Constraint System successfully demonstrated!")
    print(f"   Overall project compliance: {validation_result.overall_compliance_score:.1%}")
    print(f"   Issues identified and actionable recommendations provided")


if __name__ == "__main__":
    asyncio.run(main())