#!/usr/bin/env python3
"""
Arxos Pipeline Demonstration

This script demonstrates how to use the Arxos pipeline for integrating new building systems.
"""

import json
import sys
import time
from pathlib import Path
from typing import Dict, Any

# Add the svgx_engine to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "svgx_engine"))

from svgx_engine.services.pipeline_integration import PipelineIntegrationService


def demo_audiovisual_integration():
    """Demonstrate integrating an Audiovisual (AV) system."""
    print("🎬 Arxos Pipeline Demo: Audiovisual System Integration")
    print("=" * 60)

    service = PipelineIntegrationService()
    system = "audiovisual"

    print(f"\n1. Defining Schema for {system} system...")
    result = service.handle_operation("validate-schema", {"system": system})
    print(f"   Result: {'✓ Success' if result.get('success') else '✗ Failed'}")
    if result.get("error"):
        print(f"   Error: {result['error']}")

    print(f"\n2. Adding AV Symbols...")
    symbols = ["display", "projector", "audio_system", "control_panel"]
    result = service.handle_operation(
        "add-symbols", {"system": system, "symbols": symbols}
    )
    print(f"   Result: {'✓ Success' if result.get('success') else '✗ Failed'}")
    if result.get("created_symbols"):
        print(f"   Created: {len(result['created_symbols'])} symbols")

    print(f"\n3. Implementing AV Behavior Profiles...")
    result = service.handle_operation("implement-behavior", {"system": system})
    print(f"   Result: {'✓ Success' if result.get('success') else '✗ Failed'}")
    if result.get("behavior_path"):
        print(f"   Behavior file: {result['behavior_path']}")

    print(f"\n4. Running Compliance Check...")
    result = service.handle_operation("compliance", {"system": system})
    print(f"   Result: {'✓ Success' if result.get('success') else '✗ Failed'}")
    if result.get("compliance_details"):
        details = result["compliance_details"]
        print(f"   Status: {details.get('compliance_status', 'unknown')}")
        print(f"   Checks passed: {details.get('checks_passed', 0)}")
        print(f"   Checks failed: {details.get('checks_failed', 0)}")

    print(f"\n✅ AV System Integration Demo Completed!")


def demo_electrical_extension():
    """Demonstrate extending an existing Electrical system."""
    print("\n⚡ Arxos Pipeline Demo: Electrical System Extension")
    print("=" * 60)

    service = PipelineIntegrationService()
    system = "electrical"
    new_object = "smart_switch"

    print(f"\n1. Validating existing {system} system...")
    result = service.handle_operation("validate-schema", {"system": system})
    print(f"   Result: {'✓ Success' if result.get('success') else '✗ Failed'}")

    print(f"\n2. Adding new {new_object} to {system} system...")
    result = service.handle_operation(
        "add-symbols", {"system": system, "symbols": [new_object]}
    )
    print(f"   Result: {'✓ Success' if result.get('success') else '✗ Failed'}")

    print(f"\n3. Validating behavior profiles...")
    result = service.handle_operation("validate-behavior", {"system": system})
    print(f"   Result: {'✓ Success' if result.get('success') else '✗ Failed'}")

    print(f"\n✅ Electrical System Extension Demo Completed!")


def demo_pipeline_workflow():
    """Demonstrate the complete pipeline workflow."""
    print("\n🔄 Arxos Pipeline Demo: Complete Workflow")
    print("=" * 60)

    # Simulate the complete pipeline workflow
    steps = [
        ("Define Schema", "validate-schema"),
        ("Add Symbols", "add-symbols"),
        ("Implement Behavior", "implement-behavior"),
        ("Update Registry", "update-registry"),
        ("Documentation", "documentation"),
        ("Compliance Check", "compliance"),
    ]

    service = PipelineIntegrationService()
    system = "demo_system"

    print(f"Executing complete pipeline for system: {system}")
    print("-" * 40)

    for i, (step_name, step_operation) in enumerate(steps, 1):
        print(f"\n{i}. {step_name}...")

        # Prepare parameters based on step
        if step_operation == "add-symbols":
            params = {"system": system, "symbols": ["demo_symbol"]}
        elif step_operation == "compliance":
            params = {"system": system}
        else:
            params = {"system": system}

        # Execute step
        result = service.handle_operation(step_operation, params)

        if result.get("success"):
            print(f"   ✓ {step_name} completed")
            if "message" in result:
                print(f"   {result['message']}")
        else:
            print(f"   ✗ {step_name} failed")
            if "error" in result:
                print(f"   Error: {result['error']}")

        # Simulate processing time
        time.sleep(0.5)

    print(f"\n✅ Complete Pipeline Workflow Demo Completed!")


def demo_error_handling():
    """Demonstrate error handling in the pipeline."""
    print("\n⚠️  Arxos Pipeline Demo: Error Handling")
    print("=" * 60)

    service = PipelineIntegrationService()

    # Test various error scenarios
    error_scenarios = [
        {
            "name": "Missing System Parameter",
            "operation": "validate-schema",
            "params": {},
        },
        {
            "name": "Unknown Operation",
            "operation": "unknown-operation",
            "params": {"system": "test"},
        },
        {
            "name": "Invalid Symbol",
            "operation": "validate-symbol",
            "params": {"symbol": "invalid_symbol"},
        },
    ]

    for scenario in error_scenarios:
        print(f"\nTesting: {scenario['name']}")
        print("-" * 30)

        result = service.handle_operation(scenario["operation"], scenario["params"])

        if result.get("success"):
            print(f"   ✓ Unexpected success")
        else:
            print(f"   ✗ Expected failure: {result.get('error', 'Unknown error')}")

    print(f"\n✅ Error Handling Demo Completed!")


def main():
    """Main demonstration function."""
    print("🚀 Arxos Pipeline Integration Demonstration")
    print("=" * 60)
    print("This demo shows how to use the Arxos pipeline for integrating")
    print("new building systems and extending existing ones.")
    print()

    try:
        # Run demonstrations
        demo_audiovisual_integration()
        demo_electrical_extension()
        demo_pipeline_workflow()
        demo_error_handling()

        print("\n" + "=" * 60)
        print("🎉 All Pipeline Demonstrations Completed Successfully!")
        print("\nNext Steps:")
        print("1. Review the generated files and directories")
        print("2. Customize the behavior profiles for your specific needs")
        print("3. Add more symbols and objects to the systems")
        print("4. Integrate with the Go orchestration layer")
        print("5. Deploy to production with full CI/CD pipeline")

    except KeyboardInterrupt:
        print("\n\n⚠️  Demo interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Demo failed with error: {str(e)}")
        print(
            "This might be expected if the supporting services aren't fully implemented yet."
        )


if __name__ == "__main__":
    main()
