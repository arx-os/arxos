#!/usr/bin/env python3
"""
Test organization script for Arxos platform.
Moves test files into proper directories based on the project architecture.
"""
import os
import shutil
import sys
from pathlib import Path
from typing import List, Dict


class TestOrganizer:
    """Organize test files into proper directories."""

    def __init__(self):
        self.tests_dir = Path("tests")
        self.test_mappings = {
            # Unit tests - test individual components
            "unit": [
                "test_basic.py",
                "test_application_layer.py",
                "test_domain_layer.py",
                "test_infrastructure_layer.py",
                "test_api_layer.py",
                "test_clean_architecture.py",
                "test_use_cases_simple.py",
                "test_dev_plan_simple.py",
                "test_bim_behavior_simple.py",
                "test_enhanced_physics_integration_simple.py"
            ],
            # Integration tests - test component interactions
            "integration": [
                "test_basic_integration.py",
                "test_service_layer_integration.py",
                "test_pipeline_integration.py",
                "test_physics_integration.py",
                "test_enhanced_physics_integration.py",
                "test_ai_integration.py",
                "test_building_service_integration.py",
                "test_av_system_integration.py",
                "test_cad_system_comprehensive.py",
                "test_cmms_integration_comprehensive.py",
                "test_bim_behavior_comprehensive.py",
                "test_cad_components_comprehensive.py",
                "test_plugin_system_comprehensive.py",
                "test_notification_system_comprehensive.py",
                "test_performance_monitoring_comprehensive.py",
                "test_ai_integration_comprehensive.py",
                "test_cad_system_comprehensive.py",
                "test_bim_behavior_engine.py",
                "test_advanced_export_features.py",
                "test_advanced_thermal_analysis.py",
                "test_pdf_analysis_integration.py",
                "test_pdf_to_svgx_transformation.py",
                "test_phase2_data_persistence.py",
                "test_phase2_implementation.py",
                "test_phase3_enhancements.py",
                "test_phase3_physics_simulation.py",
                "test_dev_plan_implementation.py",
                "test_phase1_critical_fixes.py",
                "test_phase2_enhancements.py",
                "test_phase3_enhancements.py",
                "test_elite_parser.py",
                "test_browser_cad_completion.py",
                "cad_ai_integration_test.py",
                "cad_api_integration_test.py",
                "cad_collaboration_test.py",
                "cad_system_test.py",
                "cad_test_report.py"
            ],
            # Performance tests - test system performance
            "performance": [
                "test_production_performance.py",
                "test_performance_monitoring_comprehensive.py"
            ],
            # Security tests - test security features
            "security": [
                "test_security_hardening_comprehensive.py"
            ],
            # Validation tests - test validation logic
            "validation": [
                "test_precision_math.py",
                "test_precision_validation_integration.py",
                "test_precision_validator.py",
                "test_precision_coordinate.py",
                "test_precision_input.py",
                "test_geometric_calculations_precision.py",
                "test_coordinate_transformations_precision.py",
                "test_constraint_system_precision.py",
                "test_import_compliance.py",
                "test_signal_propagation.py"
            ],
            # E2E tests - end-to-end testing
            "e2e": [
                "test_pipeline_comprehensive.py",
                "test_enhanced_physics_integration.py"
            ],
            # SVGX specific tests
            "svgx_engine": [
                # These should stay in svgx_engine directory
            ],
            # Health tests - health check tests
            "health": [
                # These should stay in health directory
            ],
            # Smoke tests - basic functionality tests
            "smoke": [
                # These should stay in smoke directory
            ]
        }

    def create_directories(self):
        """Create test directories if they don't exist."""
        for directory in self.test_mappings.keys():
            dir_path = self.tests_dir / directory
            dir_path.mkdir(exist_ok=True)
            print(f"Created directory: {dir_path}")

    def move_test_files(self):
        """Move test files to appropriate directories."""
        moved_count = 0

        for directory, test_files in self.test_mappings.items():
            target_dir = self.tests_dir / directory

            for test_file in test_files:
                source_path = self.tests_dir / test_file
                target_path = target_dir / test_file

                if source_path.exists():
                    try:
                        shutil.move(str(source_path), str(target_path))
                        print(f"Moved {test_file} to {directory}/")
                        moved_count += 1
                    except Exception as e:
                        print(f"Error moving {test_file}: {e}")
                else:
                    print(f"Warning: {test_file} not found in tests directory")

        return moved_count

    def create_init_files(self):
        """Create __init__.py files in test directories."""
        for directory in self.test_mappings.keys():
            init_file = self.tests_dir / directory / "__init__.py"
            if not init_file.exists():
                init_file.write_text('"""Test package for {}."""\n'.format(directory))
                print(f"Created {init_file}")

    def update_pytest_config(self):
        """Update pytest configuration to include new test directories."""
        pytest_ini = Path("pyproject.toml")

        if pytest_ini.exists():
            # Read current content
            content = pytest_ini.read_text()

            # Update testpaths if needed
            if "testpaths" in content:
                # Already configured, no need to update
                print("pytest configuration already exists in pyproject.toml")
            else:
                print("Note: Consider updating pyproject.toml testpaths to include new directories")

    def create_test_summary(self):
        """Create a summary of test organization."""
        summary = []
        summary.append("# Test Organization Summary")
        summary.append("")
        summary.append("## Directory Structure")
        summary.append("")

        for directory, test_files in self.test_mappings.items():
            summary.append(f"### {directory.title()} Tests")
            summary.append(f"Location: `tests/{directory}/`")
            summary.append("")
            summary.append("**Purpose:** " + self.get_directory_purpose(directory))
            summary.append("")
            summary.append("**Test Files:**")
            for test_file in test_files:
                summary.append(f"- {test_file}")
            summary.append("")

        summary.append("## Running Tests")
        summary.append("")
        summary.append("```bash")
        summary.append("# Run all tests")
        summary.append("pytest tests/")
        summary.append("")
        summary.append("# Run specific test types")
        summary.append("pytest tests/unit/     # Unit tests")
        summary.append("pytest tests/integration/  # Integration tests")
        summary.append("pytest tests/performance/  # Performance tests")
        summary.append("pytest tests/security/     # Security tests")
        summary.append("pytest tests/validation/   # Validation tests")
        summary.append("pytest tests/e2e/          # End-to-end tests")
        summary.append("```")

        # Write summary to file
        summary_file = Path("tests/TEST_ORGANIZATION.md")
        summary_file.write_text("\n".join(summary))
        print(f"Created test organization summary: {summary_file}")

    def get_directory_purpose(self, directory: str) -> str:
        """Get the purpose description for a test directory."""
        purposes = {
            "unit": "Test individual components and functions in isolation",
            "integration": "Test interactions between components and services",
            "performance": "Test system performance, load, and scalability",
            "security": "Test security features, vulnerabilities, and hardening",
            "validation": "Test data validation, precision, and compliance",
            "e2e": "Test complete user workflows and system behavior",
            "svgx_engine": "Test SVGX engine specific functionality",
            "health": "Test system health checks and monitoring",
            "smoke": "Test basic functionality and critical paths"
        }
        return purposes.get(directory, "Test specific functionality")

    def organize(self):
        """Main method to organize tests."""
        print("Organizing test files...")

        # Create directories
        self.create_directories()

        # Move test files
        moved_count = self.move_test_files()
        print(f"Moved {moved_count} test files")

        # Create __init__.py files
        self.create_init_files()

        # Update pytest config
        self.update_pytest_config()

        # Create summary
        self.create_test_summary()

        print("Test organization completed!")


def main():
    """Main function."""
    organizer = TestOrganizer()
    organizer.organize()


if __name__ == "__main__":
    main()
