#!/usr/bin/env python3
"""
Jurisdiction Matching Demonstration

This script demonstrates how the MCP system automatically determines
which building codes apply based on building location data.
"""

import sys
import json
from pathlib import Path

# Add the current directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent))

from validate.rule_engine import MCPRuleEngine
from models.mcp_models import BuildingModel, BuildingObject


def create_building_with_location(building_id: str, building_name: str, location_data: dict) -> BuildingModel:
    """Create a building model with location data"""
    # Create some sample building objects
    objects = [
        BuildingObject(
            object_id="panel_main",
            object_type="electrical_panel",
            properties={
                "voltage": 120,
                "amperage": 200,
                "circuit_count": 20
            }
        ),
        BuildingObject(
            object_id="outlet_bathroom_1",
            object_type="electrical_outlet",
            properties={
                "voltage": 120,
                "amperage": 15,
                "location": "bathroom"
            }
        ),
        BuildingObject(
            object_id="outlet_kitchen_1",
            object_type="electrical_outlet",
            properties={
                "voltage": 120,
                "amperage": 20,
                "location": "kitchen"
            }
        )
    ]
    
    return BuildingModel(
        building_id=building_id,
        building_name=building_name,
        objects=objects,
        metadata={"location": location_data}
    )


def demonstrate_jurisdiction_matching():
    """Demonstrate jurisdiction matching with different building locations"""
    
    print("🏗️ Jurisdiction Matching Demonstration")
    print("=" * 50)
    
    # Initialize the rule engine
    engine = MCPRuleEngine()
    
    # Test buildings with different locations
    test_buildings = [
        {
            "id": "building_nyc",
            "name": "New York City Office Building",
            "location": {
                "country": "US",
                "state": "NY",
                "city": "New York",
                "county": "New York"
            }
        },
        {
            "id": "building_ca",
            "name": "California Residential Building",
            "location": {
                "country": "US",
                "state": "CA",
                "city": "San Francisco",
                "county": "San Francisco"
            }
        },
        {
            "id": "building_tx",
            "name": "Texas Commercial Building",
            "location": {
                "country": "US",
                "state": "TX",
                "city": "Houston",
                "county": "Harris"
            }
        },
        {
            "id": "building_fl",
            "name": "Florida Hotel Building",
            "location": {
                "country": "US",
                "state": "FL",
                "city": "Miami",
                "county": "Miami-Dade"
            }
        },
        {
            "id": "building_eu",
            "name": "European Office Building",
            "location": {
                "country": "EU",
                "state": "Germany",
                "city": "Berlin"
            }
        },
        {
            "id": "building_ca_int",
            "name": "Canadian Residential Building",
            "location": {
                "country": "CA",
                "state": "Ontario",
                "city": "Toronto"
            }
        },
        {
            "id": "building_au",
            "name": "Australian Commercial Building",
            "location": {
                "country": "AU",
                "state": "New South Wales",
                "city": "Sydney"
            }
        },
        {
            "id": "building_no_location",
            "name": "Building Without Location Data",
            "location": None
        }
    ]
    
    print("\n📍 Testing Jurisdiction Matching for Different Buildings:")
    print("-" * 60)
    
    for building_info in test_buildings:
        print(f"\n🏢 {building_info['name']}")
        print(f"   ID: {building_info['id']}")
        
        if building_info['location']:
            print(f"   Location: {building_info['location']}")
        else:
            print("   Location: None (will use fallback codes)")
        
        # Create building model
        building_model = create_building_with_location(
            building_info['id'],
            building_info['name'],
            building_info['location'] or {}
        )
        
        # Get jurisdiction information
        jurisdiction_info = engine.get_jurisdiction_info(building_model)
        
        if "error" in jurisdiction_info:
            print(f"   ❌ Error: {jurisdiction_info['error']}")
        else:
            print(f"   ✅ Location Found: {jurisdiction_info['location_found']}")
            print(f"   🎯 Jurisdiction Level: {jurisdiction_info['jurisdiction_level']}")
            print(f"   📋 Applicable Codes: {len(jurisdiction_info['applicable_codes'])}")
            
            for code in jurisdiction_info['applicable_codes']:
                print(f"      • {code}")
            
            # Show detailed matches
            if jurisdiction_info.get('matches'):
                print(f"   📊 Detailed Matches:")
                for match in jurisdiction_info['matches']:
                    print(f"      • {match['name']} ({match['match_level']}) - {match['reasoning']}")
        
        print()
    
    print("\n🔍 Testing Automatic Code Detection:")
    print("-" * 40)
    
    # Test automatic validation for a California building
    ca_building = create_building_with_location(
        "ca_test_building",
        "California Test Building",
        {
            "country": "US",
            "state": "CA",
            "city": "Los Angeles",
            "county": "Los Angeles"
        }
    )
    
    print(f"🏢 Building: {ca_building.building_name}")
    print(f"📍 Location: California, US")
    
    # Run validation with automatic code detection
    try:
        report = engine.validate_building_model(ca_building)
        print(f"✅ Validation completed successfully!")
        print(f"📊 Overall Compliance: {report.overall_compliance_score:.1f}%")
        print(f"🚨 Total Violations: {report.total_violations}")
        print(f"⚠️  Total Warnings: {report.total_warnings}")
        
        # Show which codes were applied
        print(f"📋 Applied Building Codes:")
        for validation_report in report.validation_reports:
            print(f"   • {validation_report.mcp_name} ({validation_report.mcp_id})")
            print(f"     - Rules: {validation_report.total_rules}")
            print(f"     - Violations: {validation_report.total_violations}")
        
    except Exception as e:
        print(f"❌ Validation failed: {e}")
    
    print("\n🎯 Key Features Demonstrated:")
    print("-" * 40)
    print("✅ Automatic jurisdiction detection from building location")
    print("✅ Multi-level jurisdiction matching (country, state, city)")
    print("✅ Fallback to base codes when specific amendments aren't available")
    print("✅ Support for international building codes")
    print("✅ Automatic code selection for validation")
    print("✅ Detailed jurisdiction information and reasoning")


if __name__ == "__main__":
    demonstrate_jurisdiction_matching() 