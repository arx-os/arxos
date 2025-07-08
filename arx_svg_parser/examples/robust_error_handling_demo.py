"""
Robust Error Handling & Reporting Demo

This script demonstrates the comprehensive error handling features:
- Assembly warnings collection and reporting
- Recovery strategies for partial/incomplete data
- Structured error/warning output for UI/API consumption
- Fallback mechanisms for unknown types and missing data
"""

import time
import json
from typing import Dict, List, Any

from services.robust_error_handling import (
    RobustErrorHandler, WarningLevel, RecoveryStrategy,
    create_error_handler, handle_assembly_warning, handle_recovery_action,
    generate_error_report
)


def print_header(title: str):
    """Print a formatted header."""
    print("\n" + "="*60)
    print(f"DEMO: {title}")
    print("="*60)


def print_section(title: str):
    """Print a formatted section."""
    print(f"\n--- {title} ---")


def demo_assembly_warnings():
    """Demonstrate assembly warnings collection."""
    print_header("Assembly Warnings Collection")
    
    handler = create_error_handler()
    
    print_section("Missing Geometry Warnings")
    
    # Simulate missing geometry scenarios
    missing_geometry_elements = [
        ("wall_1", "wall"),
        ("door_1", "door"),
        ("window_1", "window"),
        ("hvac_1", "hvac")
    ]
    
    for element_id, element_type in missing_geometry_elements:
        handler.handle_missing_geometry(element_id, element_type)
        print(f"  Added missing geometry warning for {element_type} ({element_id})")
    
    print_section("Unknown Type Warnings")
    
    # Simulate unknown type scenarios
    unknown_types = [
        ("custom_fixture_1", "custom_fixture"),
        ("special_equipment_1", "special_equipment"),
        ("legacy_system_1", "legacy_system")
    ]
    
    for element_id, unknown_type in unknown_types:
        handler.handle_unknown_type(element_id, unknown_type)
        print(f"  Added unknown type warning for {unknown_type} ({element_id})")
    
    print_section("Ambiguous Type Warnings")
    
    # Simulate ambiguous type scenarios
    ambiguous_types = [
        ("element_1", ["wall", "partition", "barrier"]),
        ("element_2", ["door", "opening", "passage"]),
        ("element_3", ["window", "opening", "fenestration"])
    ]
    
    for element_id, detected_types in ambiguous_types:
        handler.handle_ambiguous_type(element_id, detected_types)
        print(f"  Added ambiguous type warning for {element_id}: {detected_types}")
    
    print_section("Property Conflict Warnings")
    
    # Simulate property conflict scenarios
    property_conflicts = [
        ("door_1", "height", 2.1, 2.4),
        ("window_1", "width", 1.2, 1.5),
        ("wall_1", "thickness", 0.2, 0.3)
    ]
    
    for element_id, property_name, expected_value, actual_value in property_conflicts:
        handler.handle_property_conflict(element_id, property_name, expected_value, actual_value)
        print(f"  Added property conflict warning for {element_id}.{property_name}")
    
    print_section("Validation Error Warnings")
    
    # Simulate validation error scenarios
    validation_errors = [
        ("window_1", ["Invalid coordinates", "Missing required property"]),
        ("door_1", ["Invalid dimensions", "Missing material specification"]),
        ("wall_1", ["Invalid geometry", "Missing structural properties"])
    ]
    
    for element_id, errors in validation_errors:
        handler.handle_validation_error(element_id, errors)
        print(f"  Added validation error warning for {element_id}: {len(errors)} errors")
    
    return handler


def demo_recovery_strategies():
    """Demonstrate recovery strategies."""
    print_header("Recovery Strategies")
    
    handler = create_error_handler()
    
    print_section("Missing Geometry Recovery")
    
    # Demonstrate geometry recovery
    recovered_geometry = handler.handle_missing_geometry("wall_1", "wall")
    print(f"  Recovered geometry for wall_1:")
    print(f"    Type: {recovered_geometry['type']}")
    print(f"    Element ID: {recovered_geometry['element_id']}")
    print(f"    Element Type: {recovered_geometry['element_type']}")
    
    print_section("Unknown Type Recovery")
    
    # Demonstrate type recovery
    recovered_type = handler.handle_unknown_type("custom_fixture_1", "custom_fixture")
    print(f"  Recovered type for custom_fixture_1: {recovered_type}")
    
    print_section("Ambiguous Type Recovery")
    
    # Demonstrate ambiguous type recovery
    detected_types = ["wall", "partition", "barrier"]
    recovered_type = handler.handle_ambiguous_type("element_1", detected_types)
    print(f"  Recovered type for element_1: {recovered_type} (from {detected_types})")
    
    print_section("Property Conflict Recovery")
    
    # Demonstrate property conflict recovery
    recovered_value = handler.handle_property_conflict("door_1", "height", 2.1, 2.4)
    print(f"  Recovered property for door_1.height: {recovered_value} (expected value)")
    
    print_section("Validation Error Recovery")
    
    # Demonstrate validation error recovery
    validation_errors = ["Invalid coordinates", "Missing required property"]
    recovered_properties = handler.handle_validation_error("window_1", validation_errors)
    print(f"  Recovered properties for window_1:")
    print(f"    Valid: {recovered_properties['valid']}")
    print(f"    Recovered: {recovered_properties['recovered']}")
    print(f"    Errors: {recovered_properties['validation_errors']}")
    
    return handler


def demo_structured_output():
    """Demonstrate structured output for UI/API consumption."""
    print_header("Structured Output for UI/API")
    
    handler = create_error_handler()
    
    # Add various warnings and errors
    print_section("Adding Sample Data")
    
    handler.handle_missing_geometry("wall_1", "wall")
    handler.handle_unknown_type("custom_fixture_1", "custom_fixture")
    handler.handle_ambiguous_type("element_1", ["wall", "partition"])
    handler.handle_property_conflict("door_1", "height", 2.1, 2.4)
    handler.handle_validation_error("window_1", ["Invalid coordinates"])
    handler.handle_exception(ValueError("Test error"), "Test context")
    
    print("  Added various warnings and errors")
    
    print_section("JSON Output")
    
    # Generate JSON output
    json_output = handler.get_report_json(success=True, metadata={"operation": "demo"})
    
    print("  Generated JSON output:")
    print(f"    Length: {len(json_output)} characters")
    
    # Parse and show structure
    parsed = json.loads(json_output)
    print(f"    Report ID: {parsed['report_id']}")
    print(f"    Success: {parsed['success']}")
    print(f"    Warnings: {len(parsed['warnings'])}")
    print(f"    Recovery Actions: {len(parsed['recovery_actions'])}")
    print(f"    Errors: {len(parsed['errors'])}")
    print(f"    Recommendations: {len(parsed['recommendations'])}")
    
    print_section("Dictionary Output")
    
    # Generate dictionary output
    report_dict = handler.get_report_dict(success=True, metadata={"operation": "demo"})
    
    print("  Generated dictionary output:")
    print(f"    Report ID: {report_dict['report_id']}")
    print(f"    Success: {report_dict['success']}")
    print(f"    Summary: {report_dict['summary']}")
    
    return handler


def demo_warning_categories():
    """Demonstrate warning categorization and analysis."""
    print_header("Warning Categories and Analysis")
    
    handler = create_error_handler()
    
    print_section("Adding Categorized Warnings")
    
    # Add warnings in different categories
    categories = {
        "missing_geometry": [
            ("wall_1", "wall"),
            ("door_1", "door"),
            ("window_1", "window")
        ],
        "unknown_type": [
            ("custom_1", "custom_fixture"),
            ("special_1", "special_equipment")
        ],
        "ambiguous_type": [
            ("element_1", ["wall", "partition"]),
            ("element_2", ["door", "opening"])
        ],
        "property_conflict": [
            ("door_1", "height", 2.1, 2.4),
            ("window_1", "width", 1.2, 1.5)
        ],
        "validation_error": [
            ("window_1", ["Invalid coordinates"]),
            ("door_1", ["Invalid dimensions"])
        ]
    }
    
    for category, items in categories.items():
        print(f"  Adding {category} warnings...")
        for item in items:
            if category == "missing_geometry":
                handler.handle_missing_geometry(item[0], item[1])
            elif category == "unknown_type":
                handler.handle_unknown_type(item[0], item[1])
            elif category == "ambiguous_type":
                handler.handle_ambiguous_type(item[0], item[1])
            elif category == "property_conflict":
                handler.handle_property_conflict(item[0], item[1], item[2], item[3])
            elif category == "validation_error":
                handler.handle_validation_error(item[0], item[1])
    
    print_section("Warning Analysis")
    
    # Get warning summary
    warning_summary = handler.warning_collector.get_warning_summary()
    
    print("  Warning Summary:")
    print(f"    Total Warnings: {warning_summary['total_warnings']}")
    print(f"    Critical: {warning_summary['critical_count']}")
    print(f"    Errors: {warning_summary['error_count']}")
    print(f"    Warnings: {warning_summary['warning_count']}")
    print(f"    Info: {warning_summary['info_count']}")
    
    print("  By Category:")
    for category, count in warning_summary['by_category'].items():
        print(f"    {category}: {count}")
    
    print_section("Recovery Analysis")
    
    # Get recovery summary
    recovery_summary = handler.recovery_manager.get_recovery_summary()
    
    print("  Recovery Summary:")
    print(f"    Total Actions: {recovery_summary['total_actions']}")
    print(f"    Successful: {recovery_summary['successful_recoveries']}")
    print(f"    Failed: {recovery_summary['failed_recoveries']}")
    
    print("  By Strategy:")
    for strategy, count in recovery_summary['by_strategy'].items():
        print(f"    {strategy}: {count}")
    
    return handler


def demo_recommendations():
    """Demonstrate recommendation generation."""
    print_header("Recommendation Generation")
    
    handler = create_error_handler()
    
    print_section("Adding Various Issues")
    
    # Add different types of issues to trigger recommendations
    handler.handle_missing_geometry("wall_1", "wall")
    handler.handle_unknown_type("custom_1", "custom_fixture")
    handler.handle_ambiguous_type("element_1", ["wall", "partition"])
    handler.handle_property_conflict("door_1", "height", 2.1, 2.4)
    handler.handle_validation_error("window_1", ["Invalid coordinates"])
    handler.handle_exception(ValueError("Critical error"), "Critical context")
    
    print("  Added various issues")
    
    print_section("Generated Recommendations")
    
    # Generate report with recommendations
    report = handler.generate_report(success=True)
    
    print("  Recommendations:")
    for i, recommendation in enumerate(report.recommendations, 1):
        print(f"    {i}. {recommendation}")
    
    return handler


def demo_error_report_structure():
    """Demonstrate error report structure for UI consumption."""
    print_header("Error Report Structure for UI")
    
    handler = create_error_handler()
    
    # Add sample data
    handler.handle_missing_geometry("wall_1", "wall")
    handler.handle_unknown_type("custom_1", "custom_fixture")
    handler.handle_exception(ValueError("Test error"), "Test context")
    
    print_section("Complete Report Structure")
    
    # Generate complete report
    report = handler.generate_report(success=True, metadata={"operation": "demo"})
    
    print("  Report Structure:")
    print(f"    Report ID: {report.report_id}")
    print(f"    Timestamp: {report.timestamp}")
    print(f"    Success: {report.success}")
    print(f"    Warnings: {len(report.warnings)}")
    print(f"    Recovery Actions: {len(report.recovery_actions)}")
    print(f"    Errors: {len(report.errors)}")
    print(f"    Recommendations: {len(report.recommendations)}")
    print(f"    Metadata: {report.metadata}")
    
    print_section("Warning Details")
    
    for i, warning in enumerate(report.warnings, 1):
        print(f"  Warning {i}:")
        print(f"    ID: {warning.id}")
        print(f"    Level: {warning.level.value}")
        print(f"    Category: {warning.category}")
        print(f"    Message: {warning.message}")
        print(f"    Element ID: {warning.element_id}")
        print(f"    Recommendation: {warning.recommendation}")
    
    print_section("Recovery Action Details")
    
    for i, action in enumerate(report.recovery_actions, 1):
        print(f"  Recovery Action {i}:")
        print(f"    ID: {action.id}")
        print(f"    Strategy: {action.strategy.value}")
        print(f"    Original Error: {action.original_error}")
        print(f"    Recovery Method: {action.recovery_method}")
        print(f"    Success: {action.success}")
    
    print_section("JSON Structure for API")
    
    # Show JSON structure
    json_output = handler.get_report_json(success=True)
    parsed = json.loads(json_output)
    
    print("  JSON Structure Keys:")
    for key in parsed.keys():
        print(f"    - {key}")
    
    return handler


def demo_integration_with_bim_assembly():
    """Demonstrate integration with BIM assembly process."""
    print_header("Integration with BIM Assembly")
    
    handler = create_error_handler()
    
    print_section("Simulating BIM Assembly Process")
    
    # Simulate SVG elements with various issues
    svg_elements = [
        {
            "id": "wall_1",
            "type": "wall",
            "geometry": None,  # Missing geometry
            "properties": {"height": 3.0, "thickness": 0.2}
        },
        {
            "id": "custom_fixture_1",
            "type": "custom_fixture",  # Unknown type
            "geometry": {"type": "rect", "x": 100, "y": 100, "width": 50, "height": 30},
            "properties": {"custom_prop": "value"}
        },
        {
            "id": "element_1",
            "type": None,  # Ambiguous type
            "geometry": {"type": "rect", "x": 200, "y": 200, "width": 100, "height": 20},
            "properties": {"height": 2.4}  # Property conflict
        },
        {
            "id": "window_1",
            "type": "window",
            "geometry": {"type": "rect", "x": 300, "y": 300, "width": 80, "height": 120},
            "properties": {"width": 1.5}  # Property conflict
        }
    ]
    
    print("  Processing SVG elements...")
    
    processed_elements = []
    
    for element in svg_elements:
        element_id = element["id"]
        element_type = element["type"]
        
        # Handle missing geometry
        if element["geometry"] is None:
            recovered_geometry = handler.handle_missing_geometry(element_id, element_type or "unknown")
            element["geometry"] = recovered_geometry
            print(f"    Recovered geometry for {element_id}")
        
        # Handle unknown type
        if element_type == "custom_fixture":
            recovered_type = handler.handle_unknown_type(element_id, element_type)
            element["type"] = recovered_type
            print(f"    Recovered type for {element_id}: {recovered_type}")
        
        # Handle ambiguous type
        if element_type is None:
            detected_types = ["wall", "partition", "barrier"]
            recovered_type = handler.handle_ambiguous_type(element_id, detected_types)
            element["type"] = recovered_type
            print(f"    Recovered ambiguous type for {element_id}: {recovered_type}")
        
        # Handle property conflicts
        if element_id == "element_1" and element["properties"].get("height") == 2.4:
            expected_height = 2.1
            recovered_height = handler.handle_property_conflict(
                element_id, "height", expected_height, 2.4
            )
            element["properties"]["height"] = recovered_height
            print(f"    Recovered property conflict for {element_id}.height")
        
        if element_id == "window_1" and element["properties"].get("width") == 1.5:
            expected_width = 1.2
            recovered_width = handler.handle_property_conflict(
                element_id, "width", expected_width, 1.5
            )
            element["properties"]["width"] = recovered_width
            print(f"    Recovered property conflict for {element_id}.width")
        
        processed_elements.append(element)
    
    print_section("Assembly Results")
    
    print(f"  Successfully processed {len(processed_elements)} elements")
    
    for element in processed_elements:
        print(f"    {element['id']}: {element['type']} - Geometry: {element['geometry']['type']}")
    
    print_section("Error Report")
    
    # Generate final report
    report = handler.generate_report(success=True, metadata={
        "operation": "bim_assembly",
        "elements_processed": len(processed_elements),
        "assembly_time": time.time()
    })
    
    print("  Final Report:")
    print(f"    Success: {report.success}")
    print(f"    Warnings: {len(report.warnings)}")
    print(f"    Recovery Actions: {len(report.recovery_actions)}")
    print(f"    Errors: {len(report.errors)}")
    print(f"    Recommendations: {len(report.recommendations)}")
    
    return handler


def main():
    """Run all error handling demos."""
    print("Robust Error Handling & Reporting System Demo")
    print("=" * 60)
    
    try:
        # Run all demos
        demo_assembly_warnings()
        demo_recovery_strategies()
        demo_structured_output()
        demo_warning_categories()
        demo_recommendations()
        demo_error_report_structure()
        demo_integration_with_bim_assembly()
        
        print("\n" + "="*60)
        print("ALL DEMOS COMPLETED SUCCESSFULLY!")
        print("="*60)
        
    except Exception as e:
        print(f"\nDemo failed with error: {e}")
        raise


if __name__ == "__main__":
    main() 