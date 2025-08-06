#!/usr/bin/env python3
"""
Arxos Pipeline CLI

Command-line interface for the Arxos pipeline system.
Supports system integration, validation, and execution.
"""

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Dict, Any, List, Optional

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from svgx_engine.services.pipeline_integration import PipelineIntegrationService


class ArxPipelineCLI:
    """Command-line interface for the Arxos pipeline"""

    def __init__(self):
        """Initialize the CLI"""
        self.service = PipelineIntegrationService()
        self.supported_systems = [
            "electrical",
            "mechanical",
            "plumbing",
            "fire_alarm",
            "security",
            "network",
            "audiovisual",  # Added AV system
        ]

    def list_systems(self):
        """List all supported systems"""
        print("🏢 Supported Building Systems:")
        print("=" * 40)

        for system in self.supported_systems:
            status = (
                "✅ Available"
                if self._check_system_availability(system)
                else "⚠️  Not configured"
            )
            print(f"  • {system.title()}: {status}")

        print(f"\nTotal Systems: {len(self.supported_systems)}")

    def _check_system_availability(self, system: str) -> bool:
        """Check if a system is available"""
        schema_file = Path(f"schemas/{system}/schema.json")
        return schema_file.exists()

    def validate_system(self, system: str, verbose: bool = False):
        """Validate a specific system"""
        print(f"🔍 Validating {system.title()} System...")

        if system not in self.supported_systems:
            print(f"❌ Error: {system} is not a supported system")
            return False

        # Validate schema
        schema_result = self.service.handle_operation(
            "validate-schema", {"system": system}
        )
        if verbose:
            print(
                f"Schema Validation: {'✅ PASS' if schema_result.get('success') else '❌ FAIL'}"
            )

        # Validate symbols
        symbols_result = self.service.handle_operation(
            "validate-symbols", {"system": system}
        )
        if verbose:
            print(
                f"Symbol Validation: {'✅ PASS' if symbols_result.get('success') else '❌ FAIL'}"
            )

        # Validate behaviors
        behaviors_result = self.service.handle_operation(
            "validate-behavior", {"system": system}
        )
        if verbose:
            print(
                f"Behavior Validation: {'✅ PASS' if behaviors_result.get('success') else '❌ FAIL'}"
            )

        # Overall result
        all_passed = (
            schema_result.get("success", False)
            and symbols_result.get("success", False)
            and behaviors_result.get("success", False)
        )

        if all_passed:
            print(f"✅ {system.title()} system validation PASSED")
        else:
            print(f"❌ {system.title()} system validation FAILED")

        return all_passed

    def execute_pipeline(
        self, system: str, object_type: Optional[str] = None, dry_run: bool = False
    ):
        """Execute pipeline for a system"""
        print(f"🚀 Executing Pipeline for {system.title()} System...")

        if system not in self.supported_systems:
            print(f"❌ Error: {system} is not a supported system")
            return False

        # Build execution parameters
        params = {"system": system, "dry_run": dry_run}

        if object_type:
            params["object_type"] = object_type

        # Execute pipeline
        start_time = time.time()
        result = self.service.handle_operation("execute-pipeline", params)
        end_time = time.time()

        execution_time = end_time - start_time

        if result.get("success"):
            print(
                f"✅ Pipeline execution completed successfully in {execution_time:.2f}s"
            )
            if dry_run:
                print("📋 This was a dry run - no changes were made")
        else:
            print(f"❌ Pipeline execution failed after {execution_time:.2f}s")
            print(f"Error: {result.get('error', 'Unknown error')}")

        return result.get("success", False)

    def get_status(self, system: Optional[str] = None):
        """Get pipeline status"""
        if system:
            print(f"📊 Pipeline Status for {system.title()} System...")
            result = self.service.handle_operation("get-status", {"system": system})
        else:
            print("📊 Overall Pipeline Status...")
            result = self.service.handle_operation("get-status", {})

        if result.get("success"):
            status_data = result.get("data", {})
            print(f"Status: {status_data.get('status', 'Unknown')}")
            print(f"Last Updated: {status_data.get('last_updated', 'Unknown')}")
            print(f"Active Executions: {status_data.get('active_executions', 0)}")
        else:
            print(f"❌ Failed to get status: {result.get('error', 'Unknown error')}")

    def list_executions(self, system: Optional[str] = None, limit: int = 10):
        """List recent pipeline executions"""
        params = {"limit": limit}
        if system:
            params["system"] = system
            print(f"📋 Recent Executions for {system.title()} System...")
        else:
            print("📋 Recent Pipeline Executions...")

        result = self.service.handle_operation("list-executions", params)

        if result.get("success"):
            executions = result.get("data", [])
            if executions:
                for execution in executions[:limit]:
                    status_icon = (
                        "✅"
                        if execution.get("status") == "completed"
                        else "🔄" if execution.get("status") == "running" else "❌"
                    )
                    print(
                        f"  {status_icon} {execution.get('id', 'Unknown')} - {execution.get('status', 'Unknown')} - {execution.get('created_at', 'Unknown')}"
                    )
            else:
                print("  No executions found")
        else:
            print(
                f"❌ Failed to list executions: {result.get('error', 'Unknown error')}"
            )

    def get_metrics(self, system: Optional[str] = None):
        """Get pipeline metrics"""
        params = {}
        if system:
            params["system"] = system
            print(f"📈 Metrics for {system.title()} System...")
        else:
            print("📈 Overall Pipeline Metrics...")

        result = self.service.handle_operation("get-metrics", params)

        if result.get("success"):
            metrics = result.get("data", {})
            print(f"Total Executions: {metrics.get('total_executions', 0)}")
            print(f"Success Rate: {metrics.get('success_rate', 0):.1f}%")
            print(
                f"Average Execution Time: {metrics.get('avg_execution_time', 0):.2f}s"
            )
            print(f"Active Executions: {metrics.get('active_executions', 0)}")
        else:
            print(f"❌ Failed to get metrics: {result.get('error', 'Unknown error')}")


def main():
    """Main CLI function"""
    parser = argparse.ArgumentParser(description="Arxos Pipeline CLI")
    parser.add_argument(
        "--list-systems", action="store_true", help="List all supported systems"
    )
    parser.add_argument("--validate", action="store_true", help="Validate a system")
    parser.add_argument(
        "--execute", action="store_true", help="Execute pipeline for a system"
    )
    parser.add_argument("--status", action="store_true", help="Get pipeline status")
    parser.add_argument(
        "--list-executions", action="store_true", help="List recent executions"
    )
    parser.add_argument("--metrics", action="store_true", help="Get pipeline metrics")

    parser.add_argument("--system", type=str, help="Target system")
    parser.add_argument("--object-type", type=str, help="Specific object type")
    parser.add_argument(
        "--dry-run", action="store_true", help="Execute in dry-run mode"
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument(
        "--limit", type=int, default=10, help="Limit for list operations"
    )

    args = parser.parse_args()

    cli = ArxPipelineCLI()

    try:
        if args.list_systems:
            cli.list_systems()

        elif args.validate:
            if not args.system:
                print("❌ Error: --system is required for validation")
                sys.exit(1)
            success = cli.validate_system(args.system, args.verbose)
            sys.exit(0 if success else 1)

        elif args.execute:
            if not args.system:
                print("❌ Error: --system is required for execution")
                sys.exit(1)
            success = cli.execute_pipeline(args.system, args.object_type, args.dry_run)
            sys.exit(0 if success else 1)

        elif args.status:
            cli.get_status(args.system)

        elif args.list_executions:
            cli.list_executions(args.system, args.limit)

        elif args.metrics:
            cli.get_metrics(args.system)

        else:
            parser.print_help()

    except KeyboardInterrupt:
        print("\n⚠️  Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
