#!/usr/bin/env python3
"""
Comprehensive tests for the Building Service Integration Pipeline.

This test suite validates all aspects of the integration pipeline including:
- Service discovery and requirements analysis
- SVGX schema generation
- BIM integration
- Multi-system integration
- Workflow automation
- Testing and validation
- Deployment and monitoring

Author: Arxos Engineering Team
Date: 2024
"""

import pytest
import sys
import os
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any, List

# Add the parent directory to the path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from scripts.building_service_integration import (
    BuildingServiceIntegrationPipeline,
    ServiceRequirements,
    IntegrationLevel,
    ServiceType,
)
from scripts.arx_integrate import ArxIntegrationCLI


class TestBuildingServiceIntegrationPipeline:
    """Test suite for the Building Service Integration Pipeline."""

    @pytest.fixture
    def pipeline(self):
        """Create a pipeline instance for testing."""
        return BuildingServiceIntegrationPipeline()

    @pytest.fixture
    def sample_service_config(self):
        """Create a sample service configuration for testing."""
        return {
            "name": "Test HVAC System",
            "version": "1.0.0",
            "description": "Test HVAC system for integration testing",
            "service_type": "hvac_system",
            "integration_level": "intermediate",
            "data_format": "json",
            "authentication_method": "oauth2",
            "api_endpoints": [
                "/api/v1/buildings/{building_id}/hvac",
                "/api/v1/buildings/{building_id}/hvac/systems",
            ],
            "compliance_requirements": ["data_privacy", "security", "industry"],
            "performance_requirements": {
                "response_time": "< 2 seconds",
                "throughput": "1000+ requests/minute",
                "availability": "99.9%",
            },
        }

    def test_pipeline_initialization(self, pipeline):
        """Test pipeline initialization."""
        assert pipeline is not None
        assert hasattr(pipeline, "pipeline")
        assert hasattr(pipeline, "requirements")
        assert hasattr(pipeline, "results")

    def test_phase1_service_discovery(self, pipeline, sample_service_config):
        """Test Phase 1: Service Discovery & Requirements Analysis."""
        result = pipeline.phase1_service_discovery(sample_service_config)

        assert result is not None
        assert "service_name" in result
        assert "service_type" in result
        assert "integration_level" in result
        assert "capabilities" in result
        assert "complexity_assessment" in result
        assert "estimated_effort" in result
        assert "risk_assessment" in result
        assert "compliance_gaps" in result

        # Verify requirements are set
        assert pipeline.requirements is not None
        assert pipeline.requirements.name == "Test HVAC System"
        assert pipeline.requirements.service_type == ServiceType.HVAC
        assert pipeline.requirements.integration_level == IntegrationLevel.INTERMEDIATE

    def test_phase2_svgx_schema_generation(self, pipeline, sample_service_config):
        """Test Phase 2: SVGX Schema Generation."""
        # First run phase 1 to set up requirements
        pipeline.phase1_service_discovery(sample_service_config)

        result = pipeline.phase2_svgx_schema_generation()

        assert result is not None
        assert "base_schema" in result
        assert "behavior_profiles" in result
        assert "validation_rules" in result
        assert "svgx_schema" in result
        assert "schema_validation" in result

    def test_phase3_bim_integration(self, pipeline, sample_service_config):
        """Test Phase 3: BIM Integration."""
        # Run previous phases
        pipeline.phase1_service_discovery(sample_service_config)
        pipeline.phase2_svgx_schema_generation()

        result = pipeline.phase3_bim_integration()

        assert result is not None
        assert "bim_mappings" in result
        assert "property_sets" in result
        assert "integration_mappings" in result
        assert "ifc_config" in result
        assert "bim_validation" in result

    def test_phase4_multi_system_integration(self, pipeline, sample_service_config):
        """Test Phase 4: Multi-System Integration."""
        # Run previous phases
        pipeline.phase1_service_discovery(sample_service_config)
        pipeline.phase2_svgx_schema_generation()
        pipeline.phase3_bim_integration()

        result = pipeline.phase4_multi_system_integration()

        assert result is not None
        assert "integration_config" in result
        assert "transformation_rules" in result
        assert "sync_mechanisms" in result
        assert "integration" in result
        assert "integration_validation" in result

    def test_phase5_workflow_automation(self, pipeline, sample_service_config):
        """Test Phase 5: Workflow Automation."""
        # Run previous phases
        pipeline.phase1_service_discovery(sample_service_config)
        pipeline.phase2_svgx_schema_generation()
        pipeline.phase3_bim_integration()
        pipeline.phase4_multi_system_integration()

        result = pipeline.phase5_workflow_automation()

        assert result is not None
        assert "workflows" in result
        assert "triggers" in result
        assert "error_handling" in result
        assert "automation_workflows" in result
        assert "automation_validation" in result

    def test_phase6_testing_validation(self, pipeline, sample_service_config):
        """Test Phase 6: Testing & Validation."""
        # Run previous phases
        pipeline.phase1_service_discovery(sample_service_config)
        pipeline.phase2_svgx_schema_generation()
        pipeline.phase3_bim_integration()
        pipeline.phase4_multi_system_integration()
        pipeline.phase5_workflow_automation()

        result = pipeline.phase6_testing_validation()

        assert result is not None
        assert "integration_tests" in result
        assert "performance_tests" in result
        assert "compliance_tests" in result
        assert "e2e_validation" in result
        assert "overall_status" in result

    def test_phase7_deployment_monitoring(self, pipeline, sample_service_config):
        """Test Phase 7: Deployment & Monitoring."""
        # Run previous phases
        pipeline.phase1_service_discovery(sample_service_config)
        pipeline.phase2_svgx_schema_generation()
        pipeline.phase3_bim_integration()
        pipeline.phase4_multi_system_integration()
        pipeline.phase5_workflow_automation()
        pipeline.phase6_testing_validation()

        result = pipeline.phase7_deployment_monitoring()

        assert result is not None
        assert "deployment_config" in result
        assert "monitoring_config" in result
        assert "alerting_rules" in result
        assert "deployment_artifacts" in result
        assert "deployment_validation" in result

    def test_complete_pipeline(self, pipeline, sample_service_config):
        """Test the complete pipeline execution."""
        result = pipeline.run_complete_pipeline(sample_service_config)

        assert result is not None
        assert "pipeline_status" in result
        assert "service_name" in result
        assert "integration_level" in result
        assert "phases" in result
        assert "overall_status" in result
        assert "next_steps" in result
        assert "completion_timestamp" in result

        # Verify all phases are present
        phases = result["phases"]
        assert "phase1" in phases
        assert "phase2" in phases
        assert "phase3" in phases
        assert "phase4" in phases
        assert "phase5" in phases
        assert "phase6" in phases
        assert "phase7" in phases

    def test_error_handling_invalid_config(self, pipeline):
        """Test error handling with invalid configuration."""
        invalid_config = {
            "name": "Test Service",
            # Missing required fields
        }

        with pytest.raises(Exception):
            pipeline.phase1_service_discovery(invalid_config)

    def test_error_handling_missing_requirements(self, pipeline):
        """Test error handling when requirements are not set."""
        with pytest.raises(Exception):
            pipeline.phase2_svgx_schema_generation()


class TestArxIntegrationCLI:
    """Test suite for the Arx Integration CLI."""

    @pytest.fixture
    def cli(self):
        """Create a CLI instance for testing."""
        return ArxIntegrationCLI()

    def test_cli_initialization(self, cli):
        """Test CLI initialization."""
        assert cli is not None
        assert hasattr(cli, "pipeline")
        assert hasattr(cli, "service_templates")
        assert len(cli.service_templates) > 0

    def test_list_templates(self, cli, capsys):
        """Test listing available templates."""
        cli.list_templates()
        captured = capsys.readouterr()

        assert "Available Service Templates" in captured.out
        assert "HVAC System" in captured.out
        assert "Lighting Control System" in captured.out
        assert "Security System" in captured.out

    def test_create_template_config(self, cli):
        """Test creating configuration from template."""
        config = cli.create_template_config("hvac", "Custom HVAC System")

        assert config is not None
        assert config["name"] == "Custom HVAC System"
        assert config["service_type"] == "hvac_system"
        assert config["integration_level"] == "advanced"
        assert "api_endpoints" in config
        assert "compliance_requirements" in config
        assert "performance_requirements" in config

    def test_create_template_config_invalid_template(self, cli):
        """Test creating configuration with invalid template."""
        with pytest.raises(ValueError):
            cli.create_template_config("invalid_template")

    def test_validate_config_valid(self, cli):
        """Test configuration validation with valid config."""
        valid_config = {
            "name": "Test Service",
            "version": "1.0.0",
            "description": "Test service",
            "service_type": "hvac_system",
            "integration_level": "intermediate",
            "data_format": "json",
            "authentication_method": "oauth2",
        }

        assert cli.validate_config(valid_config) is True

    def test_validate_config_invalid(self, cli):
        """Test configuration validation with invalid config."""
        invalid_config = {
            "name": "Test Service",
            # Missing required fields
        }

        assert cli.validate_config(invalid_config) is False

    def test_validate_config_invalid_integration_level(self, cli):
        """Test configuration validation with invalid integration level."""
        invalid_config = {
            "name": "Test Service",
            "version": "1.0.0",
            "description": "Test service",
            "service_type": "hvac_system",
            "integration_level": "invalid_level",
            "data_format": "json",
            "authentication_method": "oauth2",
        }

        assert cli.validate_config(invalid_config) is False

    def test_validate_config_invalid_service_type(self, cli):
        """Test configuration validation with invalid service type."""
        invalid_config = {
            "name": "Test Service",
            "version": "1.0.0",
            "description": "Test service",
            "service_type": "invalid_type",
            "integration_level": "intermediate",
            "data_format": "json",
            "authentication_method": "oauth2",
        }

        assert cli.validate_config(invalid_config) is False

    @patch("scripts.building_service_integration.BuildingServiceIntegrationPipeline")
    def test_run_integration(self, mock_pipeline_class, cli):
        """Test running integration."""
        # Mock the pipeline
        mock_pipeline = Mock()
        mock_pipeline.run_complete_pipeline.return_value = {
            "pipeline_status": "completed",
            "service_name": "Test Service",
            "integration_level": "intermediate",
            "overall_status": "success",
        }
        mock_pipeline_class.return_value = mock_pipeline

        config = {
            "name": "Test Service",
            "version": "1.0.0",
            "description": "Test service",
            "service_type": "hvac_system",
            "integration_level": "intermediate",
            "data_format": "json",
            "authentication_method": "oauth2",
        }

        result = cli.run_integration(config)

        assert result is not None
        assert result["pipeline_status"] == "completed"
        assert result["service_name"] == "Test Service"
        assert result["overall_status"] == "success"

    def test_run_integration_with_output_file(self, cli, tmp_path):
        """Test running integration with output file."""
        # Mock the pipeline
        with patch(
            "scripts.building_service_integration.BuildingServiceIntegrationPipeline"
        ) as mock_pipeline_class:
            mock_pipeline = Mock()
            mock_pipeline.run_complete_pipeline.return_value = {
                "pipeline_status": "completed",
                "service_name": "Test Service",
                "overall_status": "success",
            }
            mock_pipeline_class.return_value = mock_pipeline

            config = {
                "name": "Test Service",
                "version": "1.0.0",
                "description": "Test service",
                "service_type": "hvac_system",
                "integration_level": "intermediate",
                "data_format": "json",
                "authentication_method": "oauth2",
            }

            output_file = tmp_path / "test_results.json"
            cli.run_integration(config, str(output_file))

            # Verify output file was created
            assert output_file.exists()

            # Verify content
            with open(output_file, "r") as f:
                result = json.load(f)
                assert result["pipeline_status"] == "completed"
                assert result["service_name"] == "Test Service"


class TestIntegrationExamples:
    """Test suite for integration examples."""

    def test_hvac_integration_example(self):
        """Test HVAC integration example."""
        from examples.building_service_integration_example import HVACSystemIntegration

        hvac_integration = HVACSystemIntegration()

        # Test configuration creation
        config = hvac_integration.hvac_config
        assert config["name"] == "Smart HVAC System v2.1"
        assert config["service_type"] == "hvac_system"
        assert config["integration_level"] == "advanced"

        # Test SVGX schema creation
        schema = hvac_integration.create_hvac_svgx_schema()
        assert schema is not None
        assert "properties" in schema
        assert "hvac_system" in schema["properties"]

        # Test behavior profiles
        behaviors = hvac_integration.create_hvac_behavior_profiles()
        assert behaviors is not None
        assert "hvac_system" in behaviors
        assert "behaviors" in behaviors["hvac_system"]

        # Test workflows
        workflows = hvac_integration.create_hvac_workflows()
        assert workflows is not None
        assert "hvac_daily_optimization" in workflows
        assert "hvac_maintenance_alert" in workflows
        assert "hvac_energy_optimization" in workflows
        assert "hvac_air_quality_management" in workflows


class TestEnterpriseCompliance:
    """Test suite for enterprise compliance features."""

    def test_compliance_requirements_validation(self):
        """Test compliance requirements validation."""
        pipeline = BuildingServiceIntegrationPipeline()

        # Test with comprehensive compliance requirements
        config_with_compliance = {
            "name": "Enterprise HVAC System",
            "version": "1.0.0",
            "description": "Enterprise-grade HVAC system",
            "service_type": "hvac_system",
            "integration_level": "advanced",
            "data_format": "json",
            "authentication_method": "certificate",
            "api_endpoints": ["/api/v1/hvac"],
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
        }

        result = pipeline.phase1_service_discovery(config_with_compliance)

        # Verify compliance gaps are identified
        compliance_gaps = result.get("compliance_gaps", [])
        assert isinstance(compliance_gaps, list)

        # Verify risk assessment
        risk_assessment = result.get("risk_assessment", [])
        assert isinstance(risk_assessment, list)

    def test_security_compliance_validation(self):
        """Test security compliance validation."""
        pipeline = BuildingServiceIntegrationPipeline()

        # Test with security-focused configuration
        security_config = {
            "name": "Security System",
            "version": "1.0.0",
            "description": "Security system integration",
            "service_type": "security_system",
            "integration_level": "advanced",
            "data_format": "json",
            "authentication_method": "certificate",
            "api_endpoints": ["/api/v1/security"],
            "compliance_requirements": ["data_privacy", "security", "access_control"],
            "performance_requirements": {
                "response_time": "< 500ms",
                "throughput": "10000+ requests/minute",
                "availability": "99.99%",
            },
        }

        result = pipeline.phase1_service_discovery(security_config)

        # Verify security requirements are properly assessed
        complexity = result.get("complexity_assessment", {})
        assert complexity.get("complexity_level") in ["low", "medium", "high"]

        # Verify security-specific risks are identified
        risk_assessment = result.get("risk_assessment", [])
        security_risks = [
            risk
            for risk in risk_assessment
            if "security" in risk.get("risk", "").lower()
        ]
        assert len(security_risks) > 0


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
