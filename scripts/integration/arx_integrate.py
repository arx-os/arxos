#!/usr/bin/env python3
"""
Arxos Building Service Integration CLI

This CLI tool provides an easy way to integrate new building services into the Arxos ecosystem
using the comprehensive integration pipeline.

Usage:
    python arx_integrate.py --service-type hvac --name "Smart HVAC System" --level advanced
    python arx_integrate.py --config hvac_config.json
    python arx_integrate.py --list-templates
    python arx_integrate.py --validate-config config.json
"""

import sys
import os
import json
import argparse
import logging
from pathlib import Path
from typing import Dict, Any, Optional

# Add the parent directory to the path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from scripts.building_service_integration import BuildingServiceIntegrationPipeline


class ArxIntegrationCLI:
    """
    CLI tool for integrating building services into the Arxos ecosystem.
    """

    def __init__(self):
        self.pipeline = BuildingServiceIntegrationPipeline()
        self.logger = logging.getLogger(__name__)

        # Predefined service templates
        self.service_templates = {
            "hvac": {
                "name": "HVAC System",
                "service_type": "hvac_system",
                "integration_level": "advanced",
                "data_format": "json",
                "authentication_method": "oauth2",
                "api_endpoints": [
                    "/api/v1/buildings/{building_id}/hvac",
                    "/api/v1/buildings/{building_id}/hvac/systems",
                    "/api/v1/buildings/{building_id}/hvac/sensors",
                    "/api/v1/buildings/{building_id}/hvac/equipment",
                    "/api/v1/buildings/{building_id}/hvac/events",
                    "/api/v1/buildings/{building_id}/hvac/energy",
                    "/api/v1/buildings/{building_id}/hvac/maintenance",
                ],
                "compliance_requirements": [
                    "data_privacy",
                    "security",
                    "industry",
                    "energy_efficiency",
                    "air_quality",
                ],
                "performance_requirements": {
                    "response_time": "< 1 second",
                    "throughput": "5000+ requests/minute",
                    "availability": "99.95%",
                },
            },
            "lighting": {
                "name": "Lighting Control System",
                "service_type": "lighting_system",
                "integration_level": "intermediate",
                "data_format": "json",
                "authentication_method": "api_key",
                "api_endpoints": [
                    "/api/v1/buildings/{building_id}/lighting",
                    "/api/v1/buildings/{building_id}/lighting/zones",
                    "/api/v1/buildings/{building_id}/lighting/schedules",
                    "/api/v1/buildings/{building_id}/lighting/energy",
                ],
                "compliance_requirements": [
                    "data_privacy",
                    "security",
                    "industry",
                    "energy_efficiency",
                ],
                "performance_requirements": {
                    "response_time": "< 2 seconds",
                    "throughput": "2000+ requests/minute",
                    "availability": "99.9%",
                },
            },
            "security": {
                "name": "Security System",
                "service_type": "security_system",
                "integration_level": "advanced",
                "data_format": "json",
                "authentication_method": "certificate",
                "api_endpoints": [
                    "/api/v1/buildings/{building_id}/security",
                    "/api/v1/buildings/{building_id}/security/access",
                    "/api/v1/buildings/{building_id}/security/cameras",
                    "/api/v1/buildings/{building_id}/security/alarms",
                    "/api/v1/buildings/{building_id}/security/events",
                ],
                "compliance_requirements": [
                    "data_privacy",
                    "security",
                    "industry",
                    "access_control",
                ],
                "performance_requirements": {
                    "response_time": "< 500ms",
                    "throughput": "10000+ requests/minute",
                    "availability": "99.99%",
                },
            },
            "fire_alarm": {
                "name": "Fire Alarm System",
                "service_type": "fire_alarm_system",
                "integration_level": "advanced",
                "data_format": "json",
                "authentication_method": "certificate",
                "api_endpoints": [
                    "/api/v1/buildings/{building_id}/fire_alarm",
                    "/api/v1/buildings/{building_id}/fire_alarm/sensors",
                    "/api/v1/buildings/{building_id}/fire_alarm/panels",
                    "/api/v1/buildings/{building_id}/fire_alarm/events",
                ],
                "compliance_requirements": [
                    "data_privacy",
                    "security",
                    "industry",
                    "fire_safety",
                ],
                "performance_requirements": {
                    "response_time": "< 100ms",
                    "throughput": "5000+ requests/minute",
                    "availability": "99.99%",
                },
            },
            "energy": {
                "name": "Energy Management System",
                "service_type": "energy_management",
                "integration_level": "intermediate",
                "data_format": "json",
                "authentication_method": "oauth2",
                "api_endpoints": [
                    "/api/v1/buildings/{building_id}/energy",
                    "/api/v1/buildings/{building_id}/energy/meters",
                    "/api/v1/buildings/{building_id}/energy/consumption",
                    "/api/v1/buildings/{building_id}/energy/efficiency",
                ],
                "compliance_requirements": [
                    "data_privacy",
                    "security",
                    "industry",
                    "energy_efficiency",
                ],
                "performance_requirements": {
                    "response_time": "< 2 seconds",
                    "throughput": "3000+ requests/minute",
                    "availability": "99.9%",
                },
            },
        }

    def list_templates(self):
        """List available service templates"""
        print("📋 Available Service Templates:")
        print("=" * 50)

        for template_id, template in self.service_templates.items():
            print(f"\n🔧 {template['name']} ({template_id})")
            print(f"   Type: {template['service_type']}")
            print(f"   Integration Level: {template['integration_level']}")
            print(f"   Data Format: {template['data_format']}")
            print(f"   Authentication: {template['authentication_method']}")
            print(f"   API Endpoints: {len(template['api_endpoints'])}")
            print(f"   Compliance: {', '.join(template['compliance_requirements'])}")

    def create_template_config(
        self, template_id: str, custom_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create configuration from a template"""
        if template_id not in self.service_templates:
            raise ValueError(f"Template '{template_id}' not found")

        template = self.service_templates[template_id].copy()

        if custom_name:
            template["name"] = custom_name

        # Add version and description
        template["version"] = "1.0.0"
        template["description"] = f"Integration for {template['name']}"

        return template

    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate a service configuration"""
        required_fields = [
            "name",
            "version",
            "description",
            "service_type",
            "integration_level",
            "data_format",
            "authentication_method",
        ]

        missing_fields = []
        for field in required_fields:
            if field not in config:
                missing_fields.append(field)

        if missing_fields:
            print(f"❌ Missing required fields: {', '.join(missing_fields)}")
            return False

        # Validate integration level
        valid_levels = ["basic", "intermediate", "advanced"]
        if config["integration_level"] not in valid_levels:
            print(f"❌ Invalid integration level: {config['integration_level']}")
            print(f"   Valid levels: {', '.join(valid_levels)}")
            return False

        # Validate service type
        valid_types = [
            "building_management_system",
            "hvac_system",
            "lighting_system",
            "security_system",
            "fire_alarm_system",
            "energy_management",
            "iot_platform",
            "custom",
        ]
        if config["service_type"] not in valid_types:
            print(f"❌ Invalid service type: {config['service_type']}")
            print(f"   Valid types: {', '.join(valid_types)}")
            return False

        print("✅ Configuration is valid")
        return True

    def run_integration(
        self, config: Dict[str, Any], output_file: Optional[str] = None
    ) -> Dict[str, Any]:
        """Run the integration pipeline"""
        print(f"🚀 Starting integration for: {config['name']}")
        print("=" * 60)

        try:
            # Run the pipeline
            results = self.pipeline.run_complete_pipeline(config)

            # Save results if output file specified
            if output_file:
                with open(output_file, "w") as f:
                    json.dump(results, f, indent=2)
                print(f"📊 Results saved to: {output_file}")

            # Display summary
            self._display_integration_summary(results)

            return results

        except Exception as e:
            print(f"❌ Integration failed: {e}")
            raise

    def _display_integration_summary(self, results: Dict[str, Any]):
        """Display integration summary"""
        print("\n📊 Integration Summary")
        print("=" * 40)

        service_name = results.get("service_name", "Unknown")
        integration_level = results.get("integration_level", "Unknown")
        overall_status = results.get("overall_status", "Unknown")

        print(f"Service: {service_name}")
        print(f"Integration Level: {integration_level}")
        print(f"Overall Status: {overall_status}")

        # Phase status
        phases = results.get("phases", {})
        for phase_name, phase_result in phases.items():
            if isinstance(phase_result, dict):
                status = (
                    "✅" if phase_result.get("status", "unknown") == "success" else "❌"
                )
                print(f"{phase_name}: {status}")

        # Next steps
        next_steps = results.get("next_steps", [])
        if next_steps:
            print(f"\n📋 Next Steps:")
            for i, step in enumerate(next_steps, 1):
                print(f"   {i}. {step}")


def main():
    """Main CLI function"""
    parser = argparse.ArgumentParser(
        description="Arxos Building Service Integration CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # List available templates
  python arx_integrate.py --list-templates
  
  # Integrate HVAC system using template
  python arx_integrate.py --template hvac --name "Smart HVAC v2.1" --output results.json
  
  # Integrate custom service from config file
  python arx_integrate.py --config custom_service.json --output results.json
  
  # Validate configuration
  python arx_integrate.py --validate-config config.json
        """,
    )

    # Template-based integration
    parser.add_argument(
        "--template",
        "-t",
        choices=["hvac", "lighting", "security", "fire_alarm", "energy"],
        help="Use predefined service template",
    )

    # Custom configuration
    parser.add_argument(
        "--config", "-c", type=str, help="Path to custom configuration JSON file"
    )

    # Service parameters
    parser.add_argument("--name", "-n", type=str, help="Custom name for the service")

    parser.add_argument(
        "--level",
        "-l",
        choices=["basic", "intermediate", "advanced"],
        default="intermediate",
        help="Integration level (default: intermediate)",
    )

    # Output
    parser.add_argument(
        "--output", "-o", type=str, help="Output file for integration results"
    )

    # Utility commands
    parser.add_argument(
        "--list-templates", action="store_true", help="List available service templates"
    )

    parser.add_argument(
        "--validate-config", type=str, help="Validate a configuration file"
    )

    # Parse arguments
    args = parser.parse_args()

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Create CLI instance
    cli = ArxIntegrationCLI()

    try:
        # Handle different commands
        if args.list_templates:
            cli.list_templates()
            return

        elif args.validate_config:
            with open(args.validate_config, "r") as f:
                config = json.load(f)
            cli.validate_config(config)
            return

        elif args.template:
            # Use template-based integration
            config = cli.create_template_config(args.template, args.name)
            config["integration_level"] = args.level

            # Validate config
            if not cli.validate_config(config):
                sys.exit(1)

            # Run integration
            cli.run_integration(config, args.output)

        elif args.config:
            # Use custom configuration
            with open(args.config, "r") as f:
                config = json.load(f)

            # Validate config
            if not cli.validate_config(config):
                sys.exit(1)

            # Run integration
            cli.run_integration(config, args.output)

        else:
            parser.print_help()
            print(
                "\n❌ Please specify either --template, --config, --list-templates, or --validate-config"
            )
            sys.exit(1)

    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
