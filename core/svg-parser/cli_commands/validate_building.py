#!/usr/bin/env python3
"""
Validate Building CLI Tool

This tool provides a command-line interface for validating building design JSON files against building codes.

Usage examples:
  python -m arx_svg_parser.cmd.validate_building my_building.json
  python -m arx_svg_parser.cmd.validate_building my_building.json --db custom_regulations.db --report compliance_report.json

Options can also be set via environment variables (e.g., ARXOS_VALIDATOR_DB) if config support is added.
"""

import argparse
import json
import sys
import os
from pathlib import Path

# Use relative imports for package context
from ..services.building_code_validator import BuildingCodeValidator

try:
    import yaml
except ImportError:
    yaml = None

def load_config(args) -> dict:
    config = {}
    config_file = getattr(args, 'config', None) or os.environ.get('ARXOS_VALIDATE_BUILDING_CONFIG')
    if config_file:
        ext = Path(config_file).suffix.lower()
        try:
            with open(config_file, 'r') as f:
                if ext in ['.yaml', '.yml'] and yaml:
                    config = yaml.safe_load(f)
                elif ext == '.json':
                    config = json.load(f)
        except Exception as e:
            print(f"Warning: Failed to load config file: {e}", file=sys.stderr)
    else:
        for default in [Path.cwd() / 'arxos_cli_config.yaml', Path.home() / 'arxos_cli_config.yaml']:
            if default.exists() and yaml:
                with open(default, 'r') as f:
                    config = yaml.safe_load(f)
                break
    for key, value in os.environ.items():
        if key.startswith('ARXOS_VALIDATE_BUILDING_'):
            config[key[len('ARXOS_VALIDATE_BUILDING_'):].lower()] = value
    for k, v in vars(args).items():
        if v is not None:
            config[k] = v
    return config

def main():
    parser = argparse.ArgumentParser(
        description="Validate a building design JSON against building codes.",
        epilog="""
Examples:
  python -m arx_svg_parser.cmd.validate_building my_building.json
  python -m arx_svg_parser.cmd.validate_building my_building.json --db custom_regulations.db --report compliance_report.json
  python -m arx_svg_parser.cmd.validate_building my_building.json --config arxos_cli_config.yaml
        """
    )
    parser.add_argument("design", help="Path to building design JSON file")
    parser.add_argument("--db", default="building_regulations.db", help="Path to regulations SQLite database (default: building_regulations.db)")
    parser.add_argument("--report", help="Path to output compliance report JSON file")
    parser.add_argument("--config", help="Path to YAML/JSON config file")
    args = parser.parse_args()
    config = load_config(args)
    if not os.path.exists(config['design']):
        print(f"Error: Design file not found: {config['design']}", file=sys.stderr)
        sys.exit(1)
    with open(config['design'], "r", encoding="utf-8") as f:
        building_design = json.load(f)
    validator = BuildingCodeValidator(config.get('db', 'building_regulations.db'))
    results = validator.validate_design(building_design)
    report = validator.get_compliance_report(building_id=building_design.get('building_id', 'unknown'), validation_results=results)
    validator.close()
    print(f"\nCompliance Report for Building: {report['building_id']}")
    print(f"Validation Date: {report['validation_date']}")
    print(f"Overall Status: {report['overall_status']}")
    print(f"Overall Score: {report['overall_score']:.1f}%")
    print(f"Total Regulations: {report['total_regulations']}")
    print(f"Passed: {report['passed_regulations']}, Failed: {report['failed_regulations']}, Partial: {report['partial_regulations']}")
    print(f"Total Violations: {report['total_violations']}, Total Warnings: {report['total_warnings']}")
    for detail in report['regulation_details']:
        print(f"\nRegulation: {detail['regulation_code']} - {detail['regulation_title']}")
        print(f"Status: {detail['status']}, Score: {detail['score']:.1f}%")
        print(f"Rules: {detail['passed_rules']}/{detail['total_rules']} passed")
        if detail['violations']:
            print(f"Violations: {len(detail['violations'])}")
        if detail['warnings']:
            print(f"Warnings: {detail['warnings']}")
    if config.get('report'):
        with open(config['report'], "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)
        print(f"\nCompliance report written to: {config['report']}")

if __name__ == "__main__":
    main() 