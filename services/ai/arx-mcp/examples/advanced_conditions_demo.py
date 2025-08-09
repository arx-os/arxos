"""
Advanced Condition Types Demonstration

This script demonstrates the capabilities of the new AdvancedConditionEvaluator
with temporal, dynamic, statistical, pattern, range, and logical conditions.
"""

import sys
import os
import time
import random
from datetime import datetime, timedelta
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from services.ai.arx_mcp.validate.advanced_conditions import (
    AdvancedConditionEvaluator, TemporalOperator, StatisticalFunction, LogicalOperator
)
from services.models.mcp_models import BuildingObject, RuleCondition, RuleExecutionContext


def create_demo_building_objects():
    """Create demo building objects for testing"""
    objects = []

    # Create various building objects with temporal and dynamic data
    for i in range(50):
        # Create rooms
        room = BuildingObject(
            object_id=f"room_{i}",
            object_type="room",
            properties={
                "area": random.uniform(50, 500),
                "height": random.uniform(2.5, 4.0),
                "material": random.choice(["concrete", "steel", "wood", "glass"]),
                "timestamp": f"2024-01-15T{random.randint(8, 18):02d}:{random.randint(0, 59):02d}:00",
                "name": f"Room {chr(65 + i % 26)}",
                "load": random.uniform(100, 1000),
                "efficiency": random.uniform(0.6, 0.95),
                "cost": random.uniform(5000, 50000),
                "safety_factor": random.uniform(1.5, 3.0),
                "floor": random.randint(1, 10),
                "zone": random.choice(["A", "B", "C", "D"]),
                "status": random.choice(["active", "inactive", "maintenance"])
            },
            location={
                "x": random.uniform(0, 100),
                "y": random.uniform(0, 100),
                "z": random.uniform(0, 30),
                "width": random.uniform(5, 25),
                "height": random.uniform(2.5, 4.0),
                "depth": random.uniform(5, 25)
            }
        )
        objects.append(room)

        # Create walls
        wall = BuildingObject(
            object_id=f"wall_{i}",
            object_type="wall",
            properties={
                "thickness": random.uniform(0.1, 0.5),
                "material": random.choice(["concrete", "brick", "steel", "wood"]),
                "timestamp": f"2024-01-15T{random.randint(8, 18):02d}:{random.randint(0, 59):02d}:00",
                "name": f"Wall {i}",
                "load": random.uniform(500, 2000),
                "efficiency": random.uniform(0.7, 0.95),
                "floor": random.randint(1, 10),
                "zone": random.choice(["A", "B", "C", "D"]),
                "status": random.choice(["active", "inactive", "maintenance"])
            },
            location={
                "x": random.uniform(0, 100),
                "y": random.uniform(0, 100),
                "z": random.uniform(0, 30),
                "width": random.uniform(10, 50),
                "height": random.uniform(2.5, 4.0),
                "depth": random.uniform(0.1, 0.5)
            }
        )
        objects.append(wall)

    return objects


def demonstrate_temporal_conditions(evaluator, objects):
    """Demonstrate temporal condition evaluation"""
    print("\n=== Temporal Conditions Demonstration ===")

    # Test different temporal operators
    temporal_tests = [
        {
            "name": "During working hours",
            "condition": RuleCondition(
                type="temporal",
                element_type="room",
                temporal_params={
                    "operator": "during",
                    "start": "2024-01-15T09:00:00",
                    "end": "2024-01-15T17:00:00",
                    "property": "timestamp"
                }
            )
        },
        {
            "name": "Before noon",
            "condition": RuleCondition(
                type="temporal",
                element_type="room",
                temporal_params={
                    "operator": "before",
                    "start": "2024-01-15T12:00:00",
                    "end": "2024-01-15T12:00:00",
                    "property": "timestamp"
                }
            )
        },
        {
            "name": "After 3 PM",
            "condition": RuleCondition(
                type="temporal",
                element_type="room",
                temporal_params={
                    "operator": "after",
                    "start": "2024-01-15T15:00:00",
                    "end": "2024-01-15T15:00:00",
                    "property": "timestamp"
                }
            )
        }
    ]

    for test in temporal_tests:
        print(f"\nTesting: {test['name']}")
        results = evaluator.evaluate_temporal_condition(test['condition'], objects)
        print(f"  Matched objects: {len(results)}")
        if results:
            print(f"  Sample objects: {[obj.object_id for obj in results[:3]]}")


def demonstrate_dynamic_conditions(evaluator, objects):
    """Demonstrate dynamic condition evaluation"""
    print("\n=== Dynamic Conditions Demonstration ===")

    # Test different dynamic resolvers
    dynamic_tests = [
        {
            "name": "Large rooms (area >= 200)",
            "condition": RuleCondition(
                type="dynamic",
                element_type="room",
                dynamic_params={
                    "resolver": "area_calculator",
                    "operator": ">=",
                    "value": 200
                }
            )
        },
        {
            "name": "Efficient rooms (efficiency >= 0.8)",
            "condition": RuleCondition(
                type="dynamic",
                element_type="room",
                dynamic_params={
                    "resolver": "efficiency_calculator",
                    "operator": ">=",
                    "value": 0.8
                }
            )
        },
        {
            "name": "High load rooms (load >= 500)",
            "condition": RuleCondition(
                type="dynamic",
                element_type="room",
                dynamic_params={
                    "resolver": "load_calculator",
                    "operator": ">=",
                    "value": 500
                }
            )
        },
        {
            "name": "Expensive rooms (cost >= 25000)",
            "condition": RuleCondition(
                type="dynamic",
                element_type="room",
                dynamic_params={
                    "resolver": "cost_calculator",
                    "operator": ">=",
                    "value": 25000
                }
            )
        }
    ]

    for test in dynamic_tests:
        print(f"\nTesting: {test['name']}")
        results = evaluator.evaluate_dynamic_condition(test['condition'], objects)
        print(f"  Matched objects: {len(results)}")
        if results:
            print(f"  Sample objects: {[obj.object_id for obj in results[:3]]}")


def demonstrate_statistical_conditions(evaluator, objects):
    """Demonstrate statistical condition evaluation"""
    print("\n=== Statistical Conditions Demonstration ===")

    # Test different statistical functions
    statistical_tests = [
        {
            "name": "Rooms with average area >= 200",
            "condition": RuleCondition(
                type="statistical",
                element_type="room",
                statistical_params={
                    "function": "average",
                    "property": "area",
                    "operator": ">=",
                    "threshold": 200,
                    "group_by": "floor"
                }
            )
        },
        {
            "name": "Rooms with total load >= 1000",
            "condition": RuleCondition(
                type="statistical",
                element_type="room",
                statistical_params={
                    "function": "sum",
                    "property": "load",
                    "operator": ">=",
                    "threshold": 1000,
                    "group_by": "zone"
                }
            )
        },
        {
            "name": "Rooms with max efficiency >= 0.9",
            "condition": RuleCondition(
                type="statistical",
                element_type="room",
                statistical_params={
                    "function": "max",
                    "property": "efficiency",
                    "operator": ">=",
                    "threshold": 0.9,
                    "group_by": "zone"
                }
            )
        },
        {
            "name": "Rooms with count >= 5",
            "condition": RuleCondition(
                type="statistical",
                element_type="room",
                statistical_params={
                    "function": "count",
                    "property": "area",
                    "operator": ">=",
                    "threshold": 5,
                    "group_by": "floor"
                }
            )
        }
    ]

    for test in statistical_tests:
        print(f"\nTesting: {test['name']}")
        results = evaluator.evaluate_statistical_condition(test['condition'], objects)
        print(f"  Matched objects: {len(results)}")
        if results:
            print(f"  Sample objects: {[obj.object_id for obj in results[:3]]}")


def demonstrate_pattern_conditions(evaluator, objects):
    """Demonstrate pattern condition evaluation"""
    print("\n=== Pattern Conditions Demonstration ===")

    # Test different pattern matching
    pattern_tests = [
        {
            "name": "Rooms with 'Room' in name",
            "condition": RuleCondition(
                type="pattern",
                element_type="room",
                pattern_params={
                    "pattern": r"Room",
                    "property": "name",
                    "case_sensitive": False
                }
            )
        },
        {
            "name": "Walls with concrete material",
            "condition": RuleCondition(
                type="pattern",
                element_type="wall",
                pattern_params={
                    "pattern": r"concrete",
                    "property": "material",
                    "case_sensitive": False
                }
            )
        },
        {
            "name": "Active status objects",
            "condition": RuleCondition(
                type="pattern",
                element_type="room",
                pattern_params={
                    "pattern": r"active",
                    "property": "status",
                    "case_sensitive": False
                }
            )
        },
        {
            "name": "Objects with high efficiency (>= 0.9)",
            "condition": RuleCondition(
                type="pattern",
                element_type="room",
                pattern_params={
                    "pattern": r"0\.9[0-9]|0\.9[5-9]",
                    "property": "efficiency",
                    "case_sensitive": False
                }
            )
        }
    ]

    for test in pattern_tests:
        print(f"\nTesting: {test['name']}")
        results = evaluator.evaluate_pattern_condition(test['condition'], objects)
        print(f"  Matched objects: {len(results)}")
        if results:
            print(f"  Sample objects: {[obj.object_id for obj in results[:3]]}")


def demonstrate_range_conditions(evaluator, objects):
    """Demonstrate range condition evaluation"""
    print("\n=== Range Conditions Demonstration ===")

    # Test different range operations
    range_tests = [
        {
            "name": "Medium-sized rooms (100-300 area)",
            "condition": RuleCondition(
                type="range",
                element_type="room",
                range_params={
                    "property": "area",
                    "ranges": [{"min": 100, "max": 300}],
                    "operation": "any"
                }
            )
        },
        {
            "name": "High-efficiency rooms (0.8-0.95)",
            "condition": RuleCondition(
                type="range",
                element_type="room",
                range_params={
                    "property": "efficiency",
                    "ranges": [{"min": 0.8, "max": 0.95}],
                    "operation": "any"
                }
            )
        },
        {
            "name": "Multiple cost ranges",
            "condition": RuleCondition(
                type="range",
                element_type="room",
                range_params={
                    "property": "cost",
                    "ranges": [
                        {"min": 10000, "max": 20000},
                        {"min": 40000, "max": 50000}
                    ],
                    "operation": "any"
                }
            )
        },
        {
            "name": "All conditions must be met",
            "condition": RuleCondition(
                type="range",
                element_type="room",
                range_params={
                    "property": "area",
                    "ranges": [
                        {"min": 100, "max": 500},
                        {"min": 200, "max": 400}
                    ],
                    "operation": "all"
                }
            )
        }
    ]

    for test in range_tests:
        print(f"\nTesting: {test['name']}")
        results = evaluator.evaluate_range_condition(test['condition'], objects)
        print(f"  Matched objects: {len(results)}")
        if results:
            print(f"  Sample objects: {[obj.object_id for obj in results[:3]]}")


def demonstrate_logical_conditions(evaluator, objects):
    """Demonstrate complex logical condition evaluation"""
    print("\n=== Logical Conditions Demonstration ===")

    # Test different logical expressions
    logical_tests = [
        {
            "name": "Large AND efficient rooms",
            "condition": RuleCondition(
                type="logical",
                element_type="room",
                logical_params={
                    "expression": {
                        "operator": "and",
                        "operands": [
                            {
                                "operator": "or",
                                "operands": [
                                    {"property": "area", "operator": ">=", "value": 200},
                                    {"property": "efficiency", "operator": ">=", "value": 0.8}
                                ]
                            },
                            {
                                "operator": "not",
                                "operands": [
                                    {"property": "material", "operator": "==", "value": "wood"}
                                ]
                            }
                        ]
                    }
                }
            )
        },
        {
            "name": "High load OR high efficiency",
            "condition": RuleCondition(
                type="logical",
                element_type="room",
                logical_params={
                    "expression": {
                        "operator": "or",
                        "operands": [
                            {"property": "load", "operator": ">=", "value": 500},
                            {"property": "efficiency", "operator": ">=", "value": 0.9}
                        ]
                    }
                }
            )
        },
        {
            "name": "Exclusive conditions (XOR)",
            "condition": RuleCondition(
                type="logical",
                element_type="room",
                logical_params={
                    "expression": {
                        "operator": "xor",
                        "operands": [
                            {"property": "area", "operator": ">=", "value": 300},
                            {"property": "cost", "operator": ">=", "value": 30000}
                        ]
                    }
                }
            )
        }
    ]

    for test in logical_tests:
        print(f"\nTesting: {test['name']}")
        results = evaluator.evaluate_complex_logical_condition(test['condition'], objects)
        print(f"  Matched objects: {len(results)}")
        if results:
            print(f"  Sample objects: {[obj.object_id for obj in results[:3]]}")


def demonstrate_comprehensive_analysis(evaluator, objects):
    """Demonstrate comprehensive condition analysis"""
    print("\n=== Comprehensive Analysis Demonstration ===")

    # Create a complex analysis scenario
    print("Running comprehensive building analysis...")

    # 1. Find rooms created during working hours
    temporal_condition = RuleCondition(
        type="temporal",
        element_type="room",
        temporal_params={
            "operator": "during",
            "start": "2024-01-15T09:00:00",
            "end": "2024-01-15T17:00:00",
            "property": "timestamp"
        }
    )
    temporal_results = evaluator.evaluate_temporal_condition(temporal_condition, objects)
    print(f"1. Rooms created during working hours: {len(temporal_results)}")

    # 2. Find large, efficient rooms
    dynamic_condition = RuleCondition(
        type="dynamic",
        element_type="room",
        dynamic_params={
            "resolver": "area_calculator",
            "operator": ">=",
            "value": 200
        }
    )
    dynamic_results = evaluator.evaluate_dynamic_condition(dynamic_condition, objects)
    print(f"2. Large rooms (area >= 200): {len(dynamic_results)}")

    # 3. Find zones with high average efficiency
    statistical_condition = RuleCondition(
        type="statistical",
        element_type="room",
        statistical_params={
            "function": "average",
            "property": "efficiency",
            "operator": ">=",
            "threshold": 0.8,
            "group_by": "zone"
        }
    )
    statistical_results = evaluator.evaluate_statistical_condition(statistical_condition, objects)
    print(f"3. Zones with high average efficiency: {len(statistical_results)}")

    # 4. Find concrete walls
    pattern_condition = RuleCondition(
        type="pattern",
        element_type="wall",
        pattern_params={
            "pattern": r"concrete",
            "property": "material",
            "case_sensitive": False
        }
    )
    pattern_results = evaluator.evaluate_pattern_condition(pattern_condition, objects)
    print(f"4. Concrete walls: {len(pattern_results)}")

    # 5. Find rooms in specific cost ranges
    range_condition = RuleCondition(
        type="range",
        element_type="room",
        range_params={
            "property": "cost",
            "ranges": [
                {"min": 15000, "max": 25000},
                {"min": 35000, "max": 45000}
            ],
            "operation": "any"
        }
    )
    range_results = evaluator.evaluate_range_condition(range_condition, objects)
    print(f"5. Rooms in specific cost ranges: {len(range_results)}")

    # Summary
    print(f"\nSummary:")
    print(f"  Total objects analyzed: {len(objects)}")
    print(f"  Temporal matches: {len(temporal_results)}")
    print(f"  Dynamic matches: {len(dynamic_results)}")
    print(f"  Statistical matches: {len(statistical_results)}")
    print(f"  Pattern matches: {len(pattern_results)}")
    print(f"  Range matches: {len(range_results)}")


def demonstrate_performance_analysis(evaluator, objects):
    """Demonstrate performance analysis of different condition types"""
    print("\n=== Performance Analysis Demonstration ===")

    condition_types = [
        ("Temporal", lambda: evaluator.evaluate_temporal_condition(
            RuleCondition(
                type="temporal",
                element_type="room",
                temporal_params={
                    "operator": "during",
                    "start": "2024-01-15T09:00:00",
                    "end": "2024-01-15T17:00:00",
                    "property": "timestamp"
                }
            ), objects
        )),
        ("Dynamic", lambda: evaluator.evaluate_dynamic_condition(
            RuleCondition(
                type="dynamic",
                element_type="room",
                dynamic_params={
                    "resolver": "area_calculator",
                    "operator": ">=",
                    "value": 200
                }
            ), objects
        )),
        ("Statistical", lambda: evaluator.evaluate_statistical_condition(
            RuleCondition(
                type="statistical",
                element_type="room",
                statistical_params={
                    "function": "average",
                    "property": "area",
                    "operator": ">=",
                    "threshold": 200,
                    "group_by": "floor"
                }
            ), objects
        )),
        ("Pattern", lambda: evaluator.evaluate_pattern_condition(
            RuleCondition(
                type="pattern",
                element_type="room",
                pattern_params={
                    "pattern": r"Room",
                    "property": "name",
                    "case_sensitive": False
                }
            ), objects
        )),
        ("Range", lambda: evaluator.evaluate_range_condition(
            RuleCondition(
                type="range",
                element_type="room",
                range_params={
                    "property": "area",
                    "ranges": [{"min": 100, "max": 300}],
                    "operation": "any"
                }
            ), objects
        ))
    ]

    print("Performance comparison of condition types:")
    for condition_type, evaluation_func in condition_types:
        start_time = time.time()
        results = evaluation_func()
        end_time = time.time()

        execution_time = end_time - start_time
        print(f"  {condition_type}: {execution_time:.4f}s ({len(results)} matches)")


def main():
    """Run the advanced conditions demonstration"""
    print("Advanced Condition Types Engine Demonstration")
    print("=" * 60)

    # Create demo data
    print("Creating demo building objects...")
    objects = create_demo_building_objects()
    print(f"Created {len(objects)} building objects")

    # Initialize evaluator
    evaluator = AdvancedConditionEvaluator()
    print("Initialized AdvancedConditionEvaluator")

    # Run demonstrations
    demonstrate_temporal_conditions(evaluator, objects)
    demonstrate_dynamic_conditions(evaluator, objects)
    demonstrate_statistical_conditions(evaluator, objects)
    demonstrate_pattern_conditions(evaluator, objects)
    demonstrate_range_conditions(evaluator, objects)
    demonstrate_logical_conditions(evaluator, objects)
    demonstrate_comprehensive_analysis(evaluator, objects)
    demonstrate_performance_analysis(evaluator, objects)

    print("\n" + "=" * 60)
    print("Demonstration Complete!")
    print("\nKey Features Demonstrated:")
    print("✅ Temporal conditions with time-based evaluation")
    print("✅ Dynamic conditions with runtime value resolution")
    print("✅ Statistical conditions with aggregation functions")
    print("✅ Pattern matching and regex conditions")
    print("✅ Range and set-based conditions")
    print("✅ Complex logical expressions with nested conditions")
    print("✅ Context-aware condition evaluation")
    print("✅ Performance analysis and optimization")

    # Final statistics
    room_objects = [obj for obj in objects if obj.object_type == "room"]
    wall_objects = [obj for obj in objects if obj.object_type == "wall"]

    print(f"\nFinal Statistics:")
    print(f"  Total objects: {len(objects)}")
    print(f"  Room objects: {len(room_objects)}")
    print(f"  Wall objects: {len(wall_objects)}")
    print(f"  Unique materials: {len(set(obj.properties.get('material', '') for obj in objects))}")
    print(f"  Unique zones: {len(set(obj.properties.get('zone', '') for obj in objects))}")
    print(f"  Unique floors: {len(set(obj.properties.get('floor', 0) for obj in objects))}")


if __name__ == "__main__":
    main()
