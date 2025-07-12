"""
MCP Validation System Demo

This script demonstrates the complete MCP validation workflow including:
- Creating building models with various objects
- Loading and validating MCP files
- Running compliance checks
- Generating comprehensive reports
- Analyzing violations and recommendations

Usage:
    python mcp_validation_demo.py
"""

import json
import os
import tempfile
from pathlib import Path
from datetime import datetime

from arx_mcp import MCPRuleEngine, ReportGenerator
from arx_mcp.models import (
    BuildingModel, BuildingObject, MCPFile, MCPRule, RuleCondition, RuleAction,
    Jurisdiction, RuleSeverity, RuleCategory, ConditionType, ActionType
)


def create_sample_building_model() -> BuildingModel:
    """Create a comprehensive sample building model"""
    print("🏗️  Creating sample building model...")
    
    return BuildingModel(
        building_id="office_building_001",
        building_name="Downtown Office Building",
        objects=[
            # Electrical System
            BuildingObject(
                object_id="panel_001",
                object_type="electrical_panel",
                properties={
                    "type": "main_panel",
                    "capacity": 200.0,
                    "voltage": 120,
                    "phases": 3,
                    "location": "electrical_room"
                },
                location={"x": 500, "y": 100, "width": 40, "height": 60}
            ),
            BuildingObject(
                object_id="outlet_bathroom_001",
                object_type="electrical_outlet",
                properties={
                    "location": "bathroom",
                    "load": 15.0,
                    "gfci_protected": False,
                    "voltage": 120,
                    "circuit": "circuit_001"
                },
                location={"x": 100, "y": 200, "width": 8, "height": 8}
            ),
            BuildingObject(
                object_id="outlet_kitchen_001",
                object_type="electrical_outlet",
                properties={
                    "location": "kitchen",
                    "load": 20.0,
                    "gfci_protected": True,
                    "voltage": 120,
                    "circuit": "circuit_002"
                },
                location={"x": 150, "y": 250, "width": 8, "height": 8}
            ),
            BuildingObject(
                object_id="outlet_office_001",
                object_type="electrical_outlet",
                properties={
                    "location": "office",
                    "load": 10.0,
                    "gfci_protected": False,
                    "voltage": 120,
                    "circuit": "circuit_003"
                },
                location={"x": 200, "y": 300, "width": 8, "height": 8}
            ),
            BuildingObject(
                object_id="light_emergency_001",
                object_type="emergency_light",
                properties={
                    "type": "exit_light",
                    "battery_backup": True,
                    "location": "exit_path",
                    "illuminance": 1.0
                },
                location={"x": 50, "y": 400, "width": 12, "height": 6}
            ),
            
            # HVAC System
            BuildingObject(
                object_id="hvac_air_handler_001",
                object_type="hvac_unit",
                properties={
                    "type": "air_handler",
                    "capacity": 8000.0,
                    "efficiency": 0.85,
                    "location": "mechanical_room",
                    "cooling_capacity": 8000.0,
                    "heating_capacity": 6000.0
                },
                location={"x": 600, "y": 150, "width": 80, "height": 60}
            ),
            BuildingObject(
                object_id="hvac_thermostat_001",
                object_type="thermostat",
                properties={
                    "type": "programmable",
                    "location": "office_area",
                    "temperature_range": [60, 85],
                    "humidity_control": True
                },
                location={"x": 250, "y": 350, "width": 6, "height": 4}
            ),
            
            # Plumbing System
            BuildingObject(
                object_id="sink_bathroom_001",
                object_type="sink",
                properties={
                    "type": "bathroom_sink",
                    "flow_rate": 2.0,
                    "location": "bathroom",
                    "hot_water": True,
                    "cold_water": True
                },
                location={"x": 80, "y": 180, "width": 20, "height": 15}
            ),
            BuildingObject(
                object_id="toilet_001",
                object_type="toilet",
                properties={
                    "type": "water_closet",
                    "flow_rate": 1.6,
                    "location": "bathroom",
                    "tankless": False,
                    "water_saving": True
                },
                location={"x": 90, "y": 200, "width": 18, "height": 25}
            ),
            BuildingObject(
                object_id="water_heater_001",
                object_type="water_heater",
                properties={
                    "type": "tank",
                    "capacity": 50.0,
                    "efficiency": 0.90,
                    "location": "mechanical_room",
                    "fuel_type": "electric"
                },
                location={"x": 550, "y": 200, "width": 30, "height": 40}
            ),
            
            # Fire Safety
            BuildingObject(
                object_id="smoke_detector_001",
                object_type="smoke_detector",
                properties={
                    "type": "ionization",
                    "location": "office_area",
                    "battery_backup": True,
                    "interconnected": True
                },
                location={"x": 180, "y": 280, "width": 6, "height": 6}
            ),
            BuildingObject(
                object_id="fire_extinguisher_001",
                object_type="fire_extinguisher",
                properties={
                    "type": "abc",
                    "location": "kitchen",
                    "capacity": 10.0,
                    "expiry_date": "2025-12-31"
                },
                location={"x": 160, "y": 240, "width": 12, "height": 20}
            ),
            
            # Rooms and Spaces
            BuildingObject(
                object_id="room_bathroom_001",
                object_type="room",
                properties={
                    "type": "bathroom",
                    "area": 80.0,
                    "occupancy": 2,
                    "height": 8.0,
                    "exit_doors": 1
                },
                location={"x": 50, "y": 150, "width": 100, "height": 80}
            ),
            BuildingObject(
                object_id="room_kitchen_001",
                object_type="room",
                properties={
                    "type": "kitchen",
                    "area": 150.0,
                    "occupancy": 4,
                    "height": 9.0,
                    "exit_doors": 2
                },
                location={"x": 150, "y": 200, "width": 120, "height": 120}
            ),
            BuildingObject(
                object_id="room_office_001",
                object_type="room",
                properties={
                    "type": "office",
                    "area": 300.0,
                    "occupancy": 8,
                    "height": 9.0,
                    "exit_doors": 2
                },
                location={"x": 200, "y": 300, "width": 200, "height": 150}
            ),
            BuildingObject(
                object_id="room_mechanical_001",
                object_type="room",
                properties={
                    "type": "mechanical_room",
                    "area": 200.0,
                    "occupancy": 0,
                    "height": 10.0,
                    "exit_doors": 1
                },
                location={"x": 500, "y": 100, "width": 150, "height": 100}
            )
        ]
    )


def create_sample_mcp_files() -> list:
    """Create sample MCP files for different jurisdictions and codes"""
    print("📋 Creating sample MCP files...")
    
    mcp_files = []
    
    # NEC 2020 - Electrical Code
    nec_mcp = {
        "mcp_id": "us_fl_nec_2020",
        "name": "Florida NEC 2020",
        "description": "National Electrical Code 2020 for Florida",
        "jurisdiction": {
            "country": "US",
            "state": "FL",
            "city": None
        },
        "version": "2020",
        "effective_date": "2020-01-01",
        "rules": [
            {
                "rule_id": "nec_210_8",
                "name": "GFCI Protection",
                "description": "Ground-fault circuit interrupter protection for personnel",
                "category": "electrical_safety",
                "priority": 1,
                "conditions": [
                    {
                        "type": "property",
                        "element_type": "electrical_outlet",
                        "property": "location",
                        "operator": "in",
                        "value": ["bathroom", "kitchen", "outdoor"]
                    }
                ],
                "actions": [
                    {
                        "type": "validation",
                        "message": "GFCI protection required for outlets in wet locations",
                        "severity": "error",
                        "code_reference": "NEC 210.8"
                    }
                ]
            },
            {
                "rule_id": "nec_220_12",
                "name": "Branch Circuit Load Calculations",
                "description": "General lighting load calculations",
                "category": "electrical_design",
                "priority": 2,
                "conditions": [
                    {
                        "type": "spatial",
                        "element_type": "room",
                        "property": "area",
                        "operator": ">",
                        "value": 0
                    }
                ],
                "actions": [
                    {
                        "type": "calculation",
                        "formula": "area * 3.0",
                        "unit": "VA",
                        "description": "General lighting load calculation"
                    }
                ]
            },
            {
                "rule_id": "nec_700_12",
                "name": "Emergency Lighting",
                "description": "Emergency lighting requirements for exit paths",
                "category": "electrical_safety",
                "priority": 1,
                "conditions": [
                    {
                        "type": "property",
                        "element_type": "room",
                        "property": "type",
                        "operator": "in",
                        "value": ["office", "kitchen", "bathroom"]
                    }
                ],
                "actions": [
                    {
                        "type": "validation",
                        "message": "Emergency lighting required for occupied spaces",
                        "severity": "error",
                        "code_reference": "NEC 700.12"
                    }
                ]
            }
        ],
        "metadata": {
            "source": "National Fire Protection Association",
            "website": "https://www.nfpa.org/nec",
            "contact": "NFPA Customer Service"
        }
    }
    
    # IPC 2021 - Plumbing Code
    ipc_mcp = {
        "mcp_id": "us_fl_ipc_2021",
        "name": "Florida IPC 2021",
        "description": "International Plumbing Code 2021 for Florida",
        "jurisdiction": {
            "country": "US",
            "state": "FL",
            "city": None
        },
        "version": "2021",
        "effective_date": "2021-01-01",
        "rules": [
            {
                "rule_id": "ipc_709_1",
                "name": "Fixture Unit Calculations",
                "description": "Calculate fixture units for plumbing design",
                "category": "plumbing_water_supply",
                "priority": 1,
                "conditions": [
                    {
                        "type": "property",
                        "element_type": "sink",
                        "property": "type",
                        "operator": "==",
                        "value": "bathroom_sink"
                    }
                ],
                "actions": [
                    {
                        "type": "calculation",
                        "formula": "1.0",
                        "unit": "fixture_units",
                        "description": "Bathroom sink fixture unit calculation"
                    }
                ]
            },
            {
                "rule_id": "ipc_403_1",
                "name": "Water Heater Requirements",
                "description": "Water heater installation and safety requirements",
                "category": "plumbing_water_supply",
                "priority": 1,
                "conditions": [
                    {
                        "type": "property",
                        "element_type": "water_heater",
                        "property": "type",
                        "operator": "==",
                        "value": "tank"
                    }
                ],
                "actions": [
                    {
                        "type": "validation",
                        "message": "Water heater must have temperature and pressure relief valve",
                        "severity": "error",
                        "code_reference": "IPC 403.1"
                    }
                ]
            }
        ],
        "metadata": {
            "source": "International Code Council",
            "website": "https://www.iccsafe.org/ipc",
            "contact": "ICC Customer Service"
        }
    }
    
    # IMC 2021 - Mechanical Code
    imc_mcp = {
        "mcp_id": "us_fl_imc_2021",
        "name": "Florida IMC 2021",
        "description": "International Mechanical Code 2021 for Florida",
        "jurisdiction": {
            "country": "US",
            "state": "FL",
            "city": None
        },
        "version": "2021",
        "effective_date": "2021-01-01",
        "rules": [
            {
                "rule_id": "imc_401_1",
                "name": "Ventilation Requirements",
                "description": "Minimum ventilation requirements for occupied spaces",
                "category": "mechanical_ventilation",
                "priority": 1,
                "conditions": [
                    {
                        "type": "property",
                        "element_type": "room",
                        "property": "type",
                        "operator": "in",
                        "value": ["office", "kitchen", "bathroom"]
                    }
                ],
                "actions": [
                    {
                        "type": "validation",
                        "message": "Mechanical ventilation required for occupied spaces",
                        "severity": "error",
                        "code_reference": "IMC 401.1"
                    }
                ]
            },
            {
                "rule_id": "imc_502_1",
                "name": "HVAC System Sizing",
                "description": "HVAC system capacity requirements",
                "category": "mechanical_hvac",
                "priority": 2,
                "conditions": [
                    {
                        "type": "property",
                        "element_type": "hvac_unit",
                        "property": "type",
                        "operator": "==",
                        "value": "air_handler"
                    }
                ],
                "actions": [
                    {
                        "type": "calculation",
                        "formula": "capacity * 0.85",
                        "unit": "BTU/hr",
                        "description": "Effective cooling capacity calculation"
                    }
                ]
            }
        ],
        "metadata": {
            "source": "International Code Council",
            "website": "https://www.iccsafe.org/imc",
            "contact": "ICC Customer Service"
        }
    }
    
    # Create temporary files
    for mcp_data, filename in [(nec_mcp, "nec_2020.json"), (ipc_mcp, "ipc_2021.json"), (imc_mcp, "imc_2021.json")]:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(mcp_data, f, indent=2)
            mcp_files.append(f.name)
    
    return mcp_files


def run_validation_demo():
    """Run the complete MCP validation demo"""
    print("🚀 Starting MCP Validation Demo")
    print("=" * 50)
    
    # Initialize components
    engine = MCPRuleEngine()
    report_generator = ReportGenerator()
    
    # Create building model
    building_model = create_sample_building_model()
    print(f"✅ Created building model with {len(building_model.objects)} objects")
    
    # Create MCP files
    mcp_files = create_sample_mcp_files()
    print(f"✅ Created {len(mcp_files)} MCP files")
    
    # Validate MCP files
    print("\n🔍 Validating MCP files...")
    for mcp_file in mcp_files:
        errors = engine.validate_mcp_file(mcp_file)
        if errors:
            print(f"❌ Validation errors in {mcp_file}: {errors}")
        else:
            print(f"✅ {mcp_file} is valid")
    
    # Run validation
    print("\n🏗️  Running building validation...")
    start_time = datetime.now()
    
    compliance_report = engine.validate_building_model(building_model, mcp_files)
    
    end_time = datetime.now()
    validation_time = (end_time - start_time).total_seconds()
    
    print(f"✅ Validation completed in {validation_time:.2f} seconds")
    
    # Display results
    print("\n📊 Validation Results:")
    print(f"   Overall Compliance Score: {compliance_report.overall_compliance_score:.1f}%")
    print(f"   Critical Violations: {compliance_report.critical_violations}")
    print(f"   Total Violations: {compliance_report.total_violations}")
    print(f"   Total Warnings: {compliance_report.total_warnings}")
    print(f"   MCPs Evaluated: {len(compliance_report.validation_reports)}")
    
    # Display violations by category
    print("\n🚨 Violations by Category:")
    for report in compliance_report.validation_reports:
        print(f"   {report.mcp_name}:")
        for result in report.results:
            if result.violations:
                print(f"     - {result.rule_name}: {len(result.violations)} violations")
    
    # Generate reports
    print("\n📄 Generating reports...")
    
    # Create reports directory
    reports_dir = Path("reports")
    reports_dir.mkdir(exist_ok=True)
    
    # JSON report
    json_path = reports_dir / "compliance_report.json"
    json_content = report_generator.generate_json_report(compliance_report, str(json_path))
    print(f"✅ JSON report saved to: {json_path}")
    
    # PDF report
    pdf_path = reports_dir / "compliance_report.html"
    pdf_content = report_generator.generate_pdf_report(compliance_report, str(pdf_path))
    print(f"✅ PDF report saved to: {pdf_path}")
    
    # Summary report
    summary = report_generator.generate_summary_report(compliance_report)
    print(f"✅ Summary report generated")
    
    # Display recommendations
    print("\n💡 Recommendations:")
    for i, recommendation in enumerate(compliance_report.recommendations, 1):
        print(f"   {i}. {recommendation}")
    
    # Display priority actions
    print("\n🎯 Priority Actions:")
    priority_actions = summary["priority_actions"]
    for i, action in enumerate(priority_actions[:5], 1):  # Show top 5
        print(f"   {i}. {action['action']} (Priority: {action['priority']})")
    
    # Performance metrics
    print("\n⚡ Performance Metrics:")
    metrics = engine.get_performance_metrics()
    print(f"   Total Validations: {metrics['total_validations']}")
    print(f"   Average Execution Time: {metrics['average_execution_time']:.3f}s")
    print(f"   Cache Size: {metrics['cache_size']} files")
    
    # Cleanup
    print("\n🧹 Cleaning up temporary files...")
    for mcp_file in mcp_files:
        if os.path.exists(mcp_file):
            os.unlink(mcp_file)
    
    print("\n✅ Demo completed successfully!")
    print(f"📁 Reports available in: {reports_dir.absolute()}")


def demonstrate_advanced_features():
    """Demonstrate advanced MCP features"""
    print("\n🔬 Advanced Features Demo")
    print("=" * 30)
    
    engine = MCPRuleEngine()
    
    # Demonstrate rule execution
    print("📋 Rule Execution Examples:")
    
    # Create a simple building model
    simple_building = BuildingModel(
        building_id="demo_building",
        building_name="Demo Building",
        objects=[
            BuildingObject(
                object_id="demo_outlet",
                object_type="electrical_outlet",
                properties={
                    "location": "bathroom",
                    "gfci_protected": False
                }
            )
        ]
    )
    
    # Create a simple MCP rule
    simple_rule = MCPRule(
        rule_id="demo_rule",
        name="Demo GFCI Rule",
        description="Demo rule for testing",
        category=RuleCategory.ELECTRICAL_SAFETY,
        conditions=[
            RuleCondition(
                type=ConditionType.PROPERTY,
                element_type="electrical_outlet",
                property="location",
                operator="in",
                value=["bathroom", "kitchen"]
            )
        ],
        actions=[
            RuleAction(
                type=ActionType.VALIDATION,
                message="GFCI protection required",
                severity=RuleSeverity.ERROR,
                code_reference="DEMO-001"
            )
        ]
    )
    
    # Execute rule
    result = engine._execute_rule(simple_rule, simple_building)
    print(f"   Rule '{result.rule_name}' executed:")
    print(f"     Passed: {result.passed}")
    print(f"     Violations: {len(result.violations)}")
    print(f"     Execution time: {result.execution_time:.3f}s")
    
    if result.violations:
        for violation in result.violations:
            print(f"     - {violation.message}")


if __name__ == "__main__":
    try:
        # Run main demo
        run_validation_demo()
        
        # Run advanced features demo
        demonstrate_advanced_features()
        
    except Exception as e:
        print(f"❌ Demo failed with error: {e}")
        import traceback
        traceback.print_exc() 