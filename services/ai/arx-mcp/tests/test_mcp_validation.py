"""
Comprehensive Test Suite for MCP Validation System

This test suite demonstrates the complete MCP validation workflow including:
- MCP file loading and validation
- Building model creation and validation
- Rule execution and violation detection
- Report generation (JSON and PDF)
- Performance testing and optimization
"""

import json
import tempfile
import os
from pathlib import Path
from datetime import datetime
import pytest

from arx_mcp import MCPRuleEngine, ReportGenerator
from arx_mcp.models import (
    BuildingModel, BuildingObject, MCPFile, MCPRule, RuleCondition, RuleAction,
    Jurisdiction, RuleSeverity, RuleCategory, ConditionType, ActionType
)


class TestMCPValidation:
    """Comprehensive test suite for MCP validation system"""

    def setup_method(self):
        """Set up test fixtures"""
        self.engine = MCPRuleEngine()
        self.report_generator = ReportGenerator()

        # Create sample building model
        self.building_model = self._create_sample_building_model()

        # Create sample MCP files
        self.mcp_files = self._create_sample_mcp_files()

    def _create_sample_building_model(self) -> BuildingModel:
        """Create a sample building model for testing"""
        return BuildingModel(
            building_id="test_building_001",
            building_name="Test Office Building",
            objects=[
                # Electrical outlets
                BuildingObject(
                    object_id="outlet_001",
                    object_type="electrical_outlet",
                    properties={
                        "location": "bathroom",
                        "load": 15.0,
                        "gfci_protected": False,
                        "voltage": 120
                    },
                    location={"x": 100, "y": 200, "width": 10, "height": 10}
                ),
                BuildingObject(
                    object_id="outlet_002",
                    object_type="electrical_outlet",
                    properties={
                        "location": "kitchen",
                        "load": 20.0,
                        "gfci_protected": True,
                        "voltage": 120
                    },
                    location={"x": 150, "y": 250, "width": 10, "height": 10}
                ),
                BuildingObject(
                    object_id="outlet_003",
                    object_type="electrical_outlet",
                    properties={
                        "location": "office",
                        "load": 10.0,
                        "gfci_protected": False,
                        "voltage": 120
                    },
                    location={"x": 200, "y": 300, "width": 10, "height": 10}
                ),

                # Rooms
                BuildingObject(
                    object_id="room_001",
                    object_type="room",
                    properties={
                        "type": "bathroom",
                        "area": 80.0,
                        "occupancy": 2,
                        "height": 8.0
                    },
                    location={"x": 50, "y": 150, "width": 100, "height": 80}
                ),
                BuildingObject(
                    object_id="room_002",
                    object_type="room",
                    properties={
                        "type": "kitchen",
                        "area": 120.0,
                        "occupancy": 4,
                        "height": 8.0
                    },
                    location={"x": 150, "y": 200, "width": 120, "height": 100}
                ),
                BuildingObject(
                    object_id="room_003",
                    object_type="room",
                    properties={
                        "type": "office",
                        "area": 200.0,
                        "occupancy": 6,
                        "height": 9.0
                    },
                    location={"x": 200, "y": 300, "width": 150, "height": 120}
                ),

                # HVAC units
                BuildingObject(
                    object_id="hvac_001",
                    object_type="hvac_unit",
                    properties={
                        "type": "air_handler",
                        "capacity": 5000.0,
                        "efficiency": 0.85,
                        "location": "mechanical_room"
                    },
                    location={"x": 400, "y": 100, "width": 60, "height": 40}
                ),

                # Plumbing fixtures
                BuildingObject(
                    object_id="sink_001",
                    object_type="sink",
                    properties={
                        "type": "bathroom_sink",
                        "flow_rate": 2.0,
                        "location": "bathroom"
                    },
                    location={"x": 80, "y": 180, "width": 20, "height": 15}
                ),
                BuildingObject(
                    object_id="toilet_001",
                    object_type="toilet",
                    properties={
                        "type": "water_closet",
                        "flow_rate": 1.6,
                        "location": "bathroom"
                    },
                    location={"x": 90, "y": 200, "width": 18, "height": 25}
                )
            ]
        )

    def _create_sample_mcp_files(self) -> list:
        """Create sample MCP files for testing"""
        mcp_files = []

        # NEC 2020 MCP file
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
                }
            ],
            "metadata": {
                "source": "National Fire Protection Association",
                "website": "https://www.nfpa.org/nec",
                "contact": "NFPA Customer Service"
            }
        }

        # IPC 2021 MCP file
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
                }
            ],
            "metadata": {
                "source": "International Code Council",
                "website": "https://www.iccsafe.org/ipc",
                "contact": "ICC Customer Service"
            }
        }

        # Create temporary files
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(nec_mcp, f)
            mcp_files.append(f.name)

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(ipc_mcp, f)
            mcp_files.append(f.name)

        return mcp_files

    def test_mcp_file_loading(self):
        """Test MCP file loading functionality"""
        # Test loading MCP file
        mcp_file = self.engine.load_mcp_file(self.mcp_files[0])

        assert mcp_file.mcp_id == "us_fl_nec_2020"
        assert mcp_file.name == "Florida NEC 2020"
        assert len(mcp_file.rules) == 2
        assert mcp_file.jurisdiction.country == "US"
        assert mcp_file.jurisdiction.state == "FL"

    def test_mcp_file_validation(self):
        """Test MCP file validation"""
        # Test valid MCP file
        errors = self.engine.validate_mcp_file(self.mcp_files[0])
        assert len(errors) == 0, f"Validation errors: {errors}"

        # Test invalid MCP file
        invalid_mcp = {
            "mcp_id": "invalid_mcp",
            "name": "Invalid MCP",
            "rules": []  # Missing required fields
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(invalid_mcp, f)
            invalid_file = f.name

        errors = self.engine.validate_mcp_file(invalid_file)
        assert len(errors) > 0, "Should have validation errors"

        # Cleanup
        os.unlink(invalid_file)

    def test_building_model_validation(self):
        """Test building model validation against MCP files"""
        # Validate building model
        compliance_report = self.engine.validate_building_model(
            self.building_model,
            self.mcp_files
        )

        # Verify report structure
        assert compliance_report.building_id == "test_building_001"
        assert compliance_report.building_name == "Test Office Building"
        assert len(compliance_report.validation_reports) == 2

        # Check for expected violations (GFCI protection missing)
        total_violations = compliance_report.total_violations
        assert total_violations > 0, "Should have violations for non-GFCI outlets"

        # Check compliance score
        assert 0 <= compliance_report.overall_compliance_score <= 100

    def test_rule_execution(self):
        """Test individual rule execution"""
        # Load MCP file
        mcp_file = self.engine.load_mcp_file(self.mcp_files[0])

        # Test GFCI rule
        gfci_rule = next(r for r in mcp_file.rules if r.rule_id == "nec_210_8")

        # Execute rule
        result = self.engine._execute_rule(gfci_rule, self.building_model)

        # Verify results
        assert result.rule_id == "nec_210_8"
        assert result.category == RuleCategory.ELECTRICAL_SAFETY
        assert not result.passed, "Should fail due to missing GFCI protection"
        assert len(result.violations) > 0, "Should have violations"

    def test_condition_evaluation(self):
        """Test condition evaluation"""
        from arx_mcp.validate.rule_engine import ConditionEvaluator

        evaluator = ConditionEvaluator()

        # Test property condition
        condition = RuleCondition(
            type=ConditionType.PROPERTY,
            element_type="electrical_outlet",
            property="location",
            operator="in",
            value=["bathroom", "kitchen"]
        )

        matched_objects = evaluator.evaluate_condition(condition, self.building_model.objects)

        # Should match bathroom and kitchen outlets
        assert len(matched_objects) == 2
        assert any(obj.object_id == "outlet_001" for obj in matched_objects)
        assert any(obj.object_id == "outlet_002" for obj in matched_objects)

    def test_json_report_generation(self):
        """Test JSON report generation"""
        # Generate compliance report
        compliance_report = self.engine.validate_building_model(
            self.building_model,
            self.mcp_files
        )

        # Generate JSON report
        json_content = self.report_generator.generate_json_report(compliance_report)

        # Parse JSON and verify structure
        report_data = json.loads(json_content)

        assert "report_metadata" in report_data
        assert "building_information" in report_data
        assert "compliance_summary" in report_data
        assert "mcp_validation_reports" in report_data
        assert "violation_analysis" in report_data
        assert "recommendations" in report_data

        # Verify compliance summary
        summary = report_data["compliance_summary"]
        assert "overall_compliance_score" in summary
        assert "critical_violations" in summary
        assert "total_violations" in summary

    def test_pdf_report_generation(self):
        """Test PDF report generation"""
        # Generate compliance report
        compliance_report = self.engine.validate_building_model(
            self.building_model,
            self.mcp_files
        )

        # Generate PDF report
        with tempfile.NamedTemporaryFile(suffix='.html', delete=False) as f:
            pdf_path = f.name

        try:
            pdf_content = self.report_generator.generate_pdf_report(
                compliance_report,
                pdf_path
            )

            # Verify file was created
            assert os.path.exists(pdf_path)

            # Check content
            with open(pdf_path, 'r') as f:
                content = f.read()
                assert "MCP Compliance Report" in content
                assert "Test Office Building" in content
                assert "Executive Summary" in content

        finally:
            os.unlink(pdf_path)

    def test_summary_report_generation(self):
        """Test summary report generation"""
        # Generate compliance report
        compliance_report = self.engine.validate_building_model(
            self.building_model,
            self.mcp_files
        )

        # Generate summary report
        summary = self.report_generator.generate_summary_report(compliance_report)

        # Verify summary structure
        assert "building_info" in summary
        assert "compliance_overview" in summary
        assert "violation_summary" in summary
        assert "recommendations" in summary
        assert "priority_actions" in summary

        # Verify building info
        building_info = summary["building_info"]
        assert building_info["building_id"] == "test_building_001"
        assert building_info["building_name"] == "Test Office Building"

        # Verify compliance overview
        overview = summary["compliance_overview"]
        assert "overall_score" in overview
        assert "critical_violations" in overview
        assert "total_violations" in overview

    def test_performance_metrics(self):
        """Test performance metrics tracking"""
        # Run validation
        compliance_report = self.engine.validate_building_model(
            self.building_model,
            self.mcp_files
        )

        # Get performance metrics
        metrics = self.engine.get_performance_metrics()

        # Verify metrics
        assert "total_validations" in metrics
        assert "total_execution_time" in metrics
        assert "average_execution_time" in metrics
        assert "cache_size" in metrics

        assert metrics["total_validations"] > 0
        assert metrics["total_execution_time"] > 0
        assert metrics["average_execution_time"] > 0

    def test_cache_functionality(self):
        """Test caching functionality"""
        # Load MCP file (should cache it)
        mcp_file1 = self.engine.load_mcp_file(self.mcp_files[0])

        # Load same file again (should use cache)
        mcp_file2 = self.engine.load_mcp_file(self.mcp_files[0])

        # Verify same object returned
        assert mcp_file1 is mcp_file2

        # Clear cache
        self.engine.clear_cache()

        # Load again (should not use cache)
        mcp_file3 = self.engine.load_mcp_file(self.mcp_files[0])
        assert mcp_file1 is not mcp_file3

    def test_violation_analysis(self):
        """Test violation analysis and categorization"""
        # Generate compliance report
        compliance_report = self.engine.validate_building_model(
            self.building_model,
            self.mcp_files
        )

        # Test violation summary
        summary = self.report_generator.generate_summary_report(compliance_report)
        violation_summary = summary["violation_summary"]

        assert "total_violations" in violation_summary
        assert "by_severity" in violation_summary
        assert "by_category" in violation_summary
        assert "most_common" in violation_summary

        # Verify severity breakdown
        by_severity = violation_summary["by_severity"]
        assert "critical" in by_severity
        assert "warning" in by_severity
        assert "info" in by_severity

    def test_recommendations_generation(self):
        """Test recommendations generation"""
        # Generate compliance report
        compliance_report = self.engine.validate_building_model(
            self.building_model,
            self.mcp_files
        )

        # Verify recommendations
        assert len(compliance_report.recommendations) > 0

        # Check for specific recommendations
        recommendation_text = " ".join(compliance_report.recommendations).lower()
        assert "gfci" in recommendation_text or "electrical" in recommendation_text

    def test_priority_actions(self):
        """Test priority actions identification"""
        # Generate compliance report
        compliance_report = self.engine.validate_building_model(
            self.building_model,
            self.mcp_files
        )

        # Generate summary
        summary = self.report_generator.generate_summary_report(compliance_report)
        priority_actions = summary["priority_actions"]

        # Verify priority actions
        assert len(priority_actions) > 0

        for action in priority_actions:
            assert "priority" in action
            assert "category" in action
            assert "action" in action
            assert "violations" in action
            assert "estimated_effort" in action

    def test_comprehensive_workflow(self):
        """Test complete MCP validation workflow"""
        # Step 1: Load and validate MCP files
        for mcp_file in self.mcp_files:
            errors = self.engine.validate_mcp_file(mcp_file)
            assert len(errors) == 0, f"Validation errors for {mcp_file}: {errors}"

        # Step 2: Validate building model
        compliance_report = self.engine.validate_building_model(
            self.building_model,
            self.mcp_files
        )

        # Step 3: Generate reports
        json_report = self.report_generator.generate_json_report(compliance_report)
        summary_report = self.report_generator.generate_summary_report(compliance_report)

        # Step 4: Verify results
        assert compliance_report.total_violations > 0
        assert compliance_report.overall_compliance_score < 100
        assert len(compliance_report.recommendations) > 0

        # Step 5: Check performance
        metrics = self.engine.get_performance_metrics()
        assert metrics["total_validations"] > 0
        assert metrics["average_execution_time"] < 1.0  # Should be fast

    def teardown_method(self):
        """Clean up test files"""
        # Clean up temporary MCP files
        for mcp_file in self.mcp_files:
            if os.path.exists(mcp_file):
                os.unlink(mcp_file)


if __name__ == "__main__":
    # Run the test suite
    pytest.main([__file__, "-v"])
