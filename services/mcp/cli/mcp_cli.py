#!/usr/bin/env python3
"""
MCP Command Line Interface

Provides command-line access to MCP validation features:
- Building model validation
- Code compliance checking
- Report generation
- CAD integration support
"""

import argparse
import json
import sys
import os
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from validate.rule_engine import MCPRuleEngine
from models.mcp_models import BuildingModel, BuildingObject


class MCPCLI:
    """Command-line interface for MCP validation system"""

    def __init__(self):
        self.engine = MCPRuleEngine()

    def validate_building(
        self,
        building_file: str,
        mcp_files: List[str] = None,
        output_format: str = "json",
        output_file: str = None,
    ) -> Dict[str, Any]:
        """Validate a building model"""
        try:
            # Load building model
            with open(building_file, "r") as f:
                building_data = json.load(f)

            building_model = self._parse_building_model(building_data)

            # Run validation
            compliance_report = self.engine.validate_building_model(
                building_model, mcp_files or []
            )

            # Format output
            result = self._format_output(compliance_report, output_format)

            # Save to file if specified
            if output_file:
                with open(output_file, "w") as f:
                    if output_format == "json":
                        json.dump(result, f, indent=2)
                    else:
                        f.write(result)
                print(f"✅ Results saved to {output_file}")
            else:
                # Print to console
                if output_format == "json":
                    print(json.dumps(result, indent=2))
                else:
                    print(result)

            return result

        except Exception as e:
            print(f"❌ Validation failed: {e}")
            return {"error": str(e)}

    def validate_realtime(
        self, building_file: str, changed_objects: List[str] = None
    ) -> Dict[str, Any]:
        """Real-time validation for CAD integration"""
        try:
            # Load building model
            with open(building_file, "r") as f:
                building_data = json.load(f)

            building_model = self._parse_building_model(building_data)

            # Run incremental validation
            highlights = []
            warnings = []
            errors = []

            # Validate changed objects only
            if changed_objects:
                for obj_id in changed_objects:
                    obj = next(
                        (
                            obj
                            for obj in building_model.objects
                            if obj.object_id == obj_id
                        ),
                        None,
                    )
                    if obj:
                        obj_highlights = self._validate_single_object(
                            obj, building_model
                        )
                        highlights.extend(obj_highlights)

            # Format for CAD integration
            result = {
                "type": "realtime_validation",
                "timestamp": datetime.now().isoformat(),
                "highlights": highlights,
                "warnings": warnings,
                "errors": errors,
            }

            print(json.dumps(result, indent=2))
            return result

        except Exception as e:
            print(f"❌ Real-time validation failed: {e}")
            return {"error": str(e)}

    def list_codes(self) -> None:
        """List available building codes"""
        codes = [
            {
                "code": "NEC-2023",
                "name": "National Electrical Code 2023",
                "jurisdiction": "US",
                "categories": ["electrical_safety", "electrical_design"],
                "rules_count": 12,
            },
            {
                "code": "IBC-2024",
                "name": "International Building Code 2024",
                "jurisdiction": "US",
                "categories": ["structural", "fire_safety_egress"],
                "rules_count": 15,
            },
            {
                "code": "IPC-2024",
                "name": "International Plumbing Code 2024",
                "jurisdiction": "US",
                "categories": ["plumbing_water_supply", "plumbing_drainage"],
                "rules_count": 13,
            },
            {
                "code": "IMC-2024",
                "name": "International Mechanical Code 2024",
                "jurisdiction": "US",
                "categories": ["mechanical_hvac", "mechanical_ventilation"],
                "rules_count": 16,
            },
        ]

        print("📋 Available Building Codes:")
        print("=" * 50)
        for code in codes:
            print(f"🔧 {code['code']}: {code['name']}")
            print(f"   Jurisdiction: {code['jurisdiction']}")
            print(f"   Categories: {', '.join(code['categories'])}")
            print(f"   Rules: {code['rules_count']}")
            print()

    def list_jurisdictions(self) -> None:
        """List available jurisdictions"""
        jurisdictions = [
            {
                "country": "US",
                "state": None,
                "city": None,
                "name": "United States (Base)",
                "codes": ["NEC-2023", "IBC-2024", "IPC-2024", "IMC-2024"],
            },
            {
                "country": "US",
                "state": "CA",
                "city": None,
                "name": "California",
                "codes": ["NEC-2023-CA", "IBC-2024", "IPC-2024", "IMC-2024"],
            },
        ]

        print("🌍 Available Jurisdictions:")
        print("=" * 50)
        for jurisdiction in jurisdictions:
            print(f"🏛️  {jurisdiction['name']}")
            print(f"   Country: {jurisdiction['country']}")
            if jurisdiction["state"]:
                print(f"   State: {jurisdiction['state']}")
            print(f"   Codes: {', '.join(jurisdiction['codes'])}")
            print()

    def performance_metrics(self) -> None:
        """Show performance metrics"""
        metrics = self.engine.get_performance_metrics()

        print("⚡ Performance Metrics:")
        print("=" * 50)
        print(f"📈 Total validations: {metrics['total_validations']}")
        print(f"⏱️  Total execution time: {metrics['total_execution_time']:.3f} seconds")
        print(
            f"📊 Average execution time: {metrics['average_execution_time']:.3f} seconds"
        )
        print(f"💾 Cache size: {metrics['cache_size']} files")
        print()

    def generate_report(
        self,
        building_file: str,
        mcp_files: List[str] = None,
        report_format: str = "html",
        output_file: str = None,
    ) -> None:
        """Generate compliance report"""
        try:
            # Run validation
            result = self.validate_building(building_file, mcp_files, "json")

            if "error" in result:
                print(f"❌ Cannot generate report: {result['error']}")
                return

            # Generate report
            if report_format == "html":
                report_content = self._generate_html_report(result)
            elif report_format == "pdf":
                report_content = self._generate_pdf_report(result)
            else:
                report_content = self._generate_text_report(result)

            # Save report
            if output_file:
                with open(output_file, "w") as f:
                    f.write(report_content)
                print(f"✅ Report saved to {output_file}")
            else:
                print(report_content)

        except Exception as e:
            print(f"❌ Report generation failed: {e}")

    def _parse_building_model(self, data: Dict[str, Any]) -> BuildingModel:
        """Parse building model from JSON data"""
        building_model = BuildingModel(
            building_id=data.get("building_id", "unknown"),
            building_name=data.get("building_name", "Unknown Building"),
            objects=[],
        )

        # Parse objects
        objects_data = data.get("objects", [])
        for obj_data in objects_data:
            obj = BuildingObject(
                object_id=obj_data["object_id"],
                object_type=obj_data["object_type"],
                properties=obj_data.get("properties", {}),
                location=obj_data.get("location", {}),
                connections=obj_data.get("connections", []),
            )
            building_model.objects.append(obj)

        return building_model

    def _format_output(self, compliance_report, output_format: str) -> str:
        """Format output based on format type"""
        if output_format == "json":
            return {
                "building_id": compliance_report.building_id,
                "building_name": compliance_report.building_name,
                "overall_compliance": compliance_report.overall_compliance_score,
                "total_violations": compliance_report.total_violations,
                "critical_violations": compliance_report.critical_violations,
                "recommendations": compliance_report.recommendations,
                "validation_reports": [
                    {
                        "mcp_name": report.mcp_name,
                        "total_rules": report.total_rules,
                        "passed_rules": report.passed_rules,
                        "failed_rules": report.failed_rules,
                        "total_violations": report.total_violations,
                        "total_warnings": report.total_warnings,
                    }
                    for report in compliance_report.validation_reports
                ],
            }
        elif output_format == "text":
            return self._generate_text_report(compliance_report)
        else:
            return str(compliance_report)

    def _validate_single_object(
        self, obj: BuildingObject, building_model: BuildingModel
    ) -> List[Dict[str, Any]]:
        """Validate a single object for real-time feedback"""
        highlights = []

        # Quick validation rules
        if obj.object_type == "electrical_outlet":
            if obj.properties.get("location") in ["bathroom", "kitchen"]:
                if not obj.properties.get("gfci_protected", False):
                    highlights.append(
                        {
                            "object_id": obj.object_id,
                            "type": "violation",
                            "severity": "error",
                            "message": "GFCI protection required for wet locations",
                            "code_reference": "NEC 210.8(A)",
                            "category": "electrical_safety",
                            "suggestions": ["Add GFCI protection to outlet"],
                        }
                    )

        elif obj.object_type == "room":
            area = obj.properties.get("area", 0)
            if area > 100:  # Large room
                highlights.append(
                    {
                        "object_id": obj.object_id,
                        "type": "highlight",
                        "severity": "info",
                        "message": "Large room - consider egress requirements",
                        "code_reference": "IBC 1003.1",
                        "category": "fire_safety_egress",
                        "suggestions": ["Verify egress path requirements"],
                    }
                )

        return highlights

    def _generate_html_report(self, result: Dict[str, Any]) -> str:
        """Generate HTML compliance report"""
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>MCP Compliance Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ background-color: #f0f0f0; padding: 20px; border-radius: 5px; }}
        .summary {{ margin: 20px 0; }}
        .violation {{ background-color: #ffe6e6; padding: 10px; margin: 10px 0; border-left: 4px solid #ff0000; }}
        .warning {{ background-color: #fff2cc; padding: 10px; margin: 10px 0; border-left: 4px solid #ffcc00; }}
        .success {{ background-color: #d4edda; padding: 10px; margin: 10px 0; border-left: 4px solid #28a745; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>MCP Compliance Report</h1>
        <p><strong>Building:</strong> {result.get('building_name', 'Unknown')}</p>
        <p><strong>Date:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>
    
    <div class="summary">
        <h2>Summary</h2>
        <p><strong>Overall Compliance:</strong> {result.get('overall_compliance', 0):.1f}%</p>
        <p><strong>Total Violations:</strong> {result.get('total_violations', 0)}</p>
        <p><strong>Critical Violations:</strong> {result.get('critical_violations', 0)}</p>
    </div>
    
    <div class="recommendations">
        <h2>Recommendations</h2>
        <ul>
"""

        for rec in result.get("recommendations", []):
            html += f"            <li>{rec}</li>\n"

        html += """
        </ul>
    </div>
</body>
</html>
"""
        return html

    def _generate_text_report(self, compliance_report) -> str:
        """Generate text compliance report"""
        report = f"""
MCP Compliance Report
====================

Building: {compliance_report.building_name}
Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Summary:
--------
Overall Compliance: {compliance_report.overall_compliance_score:.1f}%
Total Violations: {compliance_report.total_violations}
Critical Violations: {compliance_report.critical_violations}

Validation Reports:
------------------
"""

        for report_data in compliance_report.validation_reports:
            report += f"""
{report_data.mcp_name}:
  Rules: {report_data.total_rules} total, {report_data.passed_rules} passed, {report_data.failed_rules} failed
  Violations: {report_data.total_violations}, Warnings: {report_data.total_warnings}
"""

        if compliance_report.recommendations:
            report += "\nRecommendations:\n"
            report += "-" * 20 + "\n"
            for rec in compliance_report.recommendations:
                report += f"• {rec}\n"

        return report

    def _generate_pdf_report(self, result: Dict[str, Any]) -> str:
        """Generate PDF report (placeholder)"""
        return f"PDF report for {result.get('building_name', 'Unknown')} - PDF generation not implemented yet"


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(description="MCP Building Validation CLI")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Validate command
    validate_parser = subparsers.add_parser("validate", help="Validate building model")
    validate_parser.add_argument("building_file", help="Building model JSON file")
    validate_parser.add_argument("--mcp-files", nargs="+", help="MCP files to use")
    validate_parser.add_argument(
        "--output-format",
        choices=["json", "text"],
        default="json",
        help="Output format",
    )
    validate_parser.add_argument("--output-file", help="Output file")

    # Real-time validation command
    realtime_parser = subparsers.add_parser(
        "realtime", help="Real-time validation for CAD"
    )
    realtime_parser.add_argument("building_file", help="Building model JSON file")
    realtime_parser.add_argument(
        "--changed-objects", nargs="+", help="Changed object IDs"
    )

    # List codes command
    subparsers.add_parser("codes", help="List available building codes")

    # List jurisdictions command
    subparsers.add_parser("jurisdictions", help="List available jurisdictions")

    # Performance command
    subparsers.add_parser("performance", help="Show performance metrics")

    # Report command
    report_parser = subparsers.add_parser("report", help="Generate compliance report")
    report_parser.add_argument("building_file", help="Building model JSON file")
    report_parser.add_argument("--mcp-files", nargs="+", help="MCP files to use")
    report_parser.add_argument(
        "--format",
        choices=["html", "text", "pdf"],
        default="html",
        help="Report format",
    )
    report_parser.add_argument("--output-file", help="Output file")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    cli = MCPCLI()

    try:
        if args.command == "validate":
            cli.validate_building(
                args.building_file, args.mcp_files, args.output_format, args.output_file
            )
        elif args.command == "realtime":
            cli.validate_realtime(args.building_file, args.changed_objects)
        elif args.command == "codes":
            cli.list_codes()
        elif args.command == "jurisdictions":
            cli.list_jurisdictions()
        elif args.command == "performance":
            cli.performance_metrics()
        elif args.command == "report":
            cli.generate_report(
                args.building_file, args.mcp_files, args.format, args.output_file
            )

    except KeyboardInterrupt:
        print("\n❌ Operation cancelled by user")
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
