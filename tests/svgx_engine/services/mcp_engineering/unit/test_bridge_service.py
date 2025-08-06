#!/usr/bin/env python3
"""
Unit Tests for MCP-Engineering Bridge Service

Comprehensive unit tests for the MCP-Engineering Bridge Service that orchestrates
the integration between MCP intelligence and engineering logic engines.

Author: Arxos Engineering Team
Date: 2024-12-19
Version: 1.0.0
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from svgx_engine.services.mcp_engineering.bridge.bridge_service import (
    MCPEngineeringBridge,
    BridgeConfig,
)
from svgx_engine.models.domain.engineering_result import MCPEngineeringResult


class TestMCPEngineeringBridge:
    """Unit tests for MCP-Engineering Bridge Service."""

    @pytest.fixture
    def bridge_config(self):
        """Create bridge configuration for testing."""
        return BridgeConfig(
            enable_caching=True,
            cache_ttl=3600,
            enable_metrics=True,
            enable_logging=True,
            timeout_seconds=30,
        )

    @pytest.fixture
    def bridge_service(self, bridge_config):
        """Create bridge service instance for testing."""
        with patch(
            "svgx_engine.services.mcp_engineering.bridge.bridge_service.MCPIntelligenceService"
        ), patch(
            "svgx_engine.services.mcp_engineering.bridge.bridge_service.EngineeringIntegrationService"
        ), patch(
            "svgx_engine.services.mcp_engineering.bridge.bridge_service.EngineeringValidationService"
        ), patch(
            "svgx_engine.services.mcp_engineering.bridge.bridge_service.CodeComplianceChecker"
        ), patch(
            "svgx_engine.services.mcp_engineering.bridge.bridge_service.CrossSystemAnalyzer"
        ), patch(
            "svgx_engine.services.mcp_engineering.bridge.bridge_service.EngineeringSuggestionEngine"
        ):

            bridge = MCPEngineeringBridge(bridge_config)
            return bridge

    @pytest.fixture
    def sample_electrical_element(self):
        """Create sample electrical design element for testing."""
        return {
            "id": "panel_001",
            "type": "electrical_panel",
            "voltage": 480,
            "phase": 3,
            "capacity": 400,
            "loads": [
                {"type": "lighting", "power": 50, "voltage": 277},
                {"type": "receptacles", "power": 30, "voltage": 120},
                {"type": "equipment", "power": 100, "voltage": 480},
            ],
        }

    @pytest.fixture
    def sample_hvac_element(self):
        """Create sample HVAC design element for testing."""
        return {
            "id": "hvac_001",
            "type": "air_handling_unit",
            "capacity": 5000,  # CFM
            "static_pressure": 2.5,  # inches WC
            "temperature": 72,  # °F
            "humidity": 50,  # %
            "ductwork": [
                {"type": "supply", "diameter": 12, "length": 50},
                {"type": "return", "diameter": 14, "length": 40},
            ],
        }

    @pytest.fixture
    def sample_plumbing_element(self):
        """Create sample plumbing design element for testing."""
        return {
            "id": "plumbing_001",
            "type": "water_supply_system",
            "flow_rate": 50,  # GPM
            "pressure": 60,  # PSI
            "pipes": [
                {"type": "main", "diameter": 2, "length": 100, "material": "copper"},
                {"type": "branch", "diameter": 1, "length": 50, "material": "copper"},
            ],
            "fixtures": [
                {"type": "sink", "flow_rate": 2.5, "count": 4},
                {"type": "toilet", "flow_rate": 1.6, "count": 6},
            ],
        }

    @pytest.fixture
    def sample_structural_element(self):
        """Create sample structural design element for testing."""
        return {
            "id": "beam_001",
            "type": "beam",
            "material": "A36_Steel",
            "geometry": {"length": 6.0, "width": 0.2, "height": 0.3},  # m  # m  # m
            "nodes": [(0, 0, 0), (6, 0, 0)],
            "supports": [
                {"type": "pinned", "location": (0, 0, 0)},
                {"type": "pinned", "location": (6, 0, 0)},
            ],
            "loads": [
                {
                    "category": "live_load",
                    "magnitude": 2.4,  # kN/m²
                    "location": [3, 0, 0],
                    "direction": [0, 0, -1],
                    "duration": 0.0,
                    "area_factor": 1.0,
                }
            ],
        }

    def test_bridge_initialization(self, bridge_service):
        """Test bridge service initialization."""
        assert bridge_service is not None
        assert bridge_service.config is not None
        assert bridge_service.intelligence_service is not None
        assert bridge_service.engineering_service is not None
        assert bridge_service.validation_service is not None
        assert bridge_service.compliance_checker is not None
        assert bridge_service.cross_system_analyzer is not None
        assert bridge_service.suggestion_engine is not None

    @pytest.mark.asyncio
    async def test_process_electrical_element_success(
        self, bridge_service, sample_electrical_element
    ):
        """Test successful processing of electrical design element."""
        # Mock all service responses
        bridge_service.intelligence_service.analyze_context = AsyncMock(
            return_value={
                "confidence_score": 0.9,
                "context_analysis": {"user_intent": "electrical_design"},
            }
        )

        bridge_service.validation_service.validate_element = AsyncMock(
            return_value={
                "system_type": "electrical",
                "confidence_score": 0.95,
                "calculations": {"voltage": 480, "current": 100},
                "safety_checks": {"overload_protection": True},
            }
        )

        bridge_service.compliance_checker.check_compliance = AsyncMock(
            return_value={
                "overall_compliance": True,
                "confidence_score": 0.98,
                "system_compliance": {"electrical": {"nec_compliance": True}},
            }
        )

        bridge_service.cross_system_analyzer.analyze_cross_system_impacts = AsyncMock(
            return_value={
                "system_impacts": {"electrical": {"hvac_impact": "minimal"}},
                "conflicts": [],
                "optimizations": ["optimize_panel_sizing"],
            }
        )

        bridge_service.suggestion_engine.generate_suggestions = AsyncMock(
            return_value=[
                {"type": "optimization", "message": "Consider upgrading panel capacity"}
            ]
        )

        # Process the element
        result = await bridge_service.process_design_element(sample_electrical_element)

        # Verify result structure
        assert isinstance(result, MCPEngineeringResult)
        assert result.element_id == "panel_001"
        assert result.processing_time > 0
        assert result.confidence_score > 0
        assert result.timestamp is not None
        assert result.intelligence_analysis is not None
        assert result.engineering_validation is not None
        assert result.code_compliance is not None
        assert result.cross_system_analysis is not None
        assert len(result.suggestions) > 0
        assert result.errors == []

    @pytest.mark.asyncio
    async def test_process_hvac_element_success(
        self, bridge_service, sample_hvac_element
    ):
        """Test successful processing of HVAC design element."""
        # Mock service responses
        bridge_service.intelligence_service.analyze_context = AsyncMock(
            return_value={
                "confidence_score": 0.85,
                "context_analysis": {"user_intent": "hvac_design"},
            }
        )

        bridge_service.validation_service.validate_element = AsyncMock(
            return_value={
                "system_type": "hvac",
                "confidence_score": 0.92,
                "calculations": {"airflow": 5000, "pressure": 2.5},
                "safety_checks": {"temperature_control": True},
            }
        )

        bridge_service.compliance_checker.check_compliance = AsyncMock(
            return_value={
                "overall_compliance": True,
                "confidence_score": 0.96,
                "system_compliance": {"hvac": {"ashrae_compliance": True}},
            }
        )

        bridge_service.cross_system_analyzer.analyze_cross_system_impacts = AsyncMock(
            return_value={
                "system_impacts": {"hvac": {"electrical_impact": "moderate"}},
                "conflicts": [],
                "optimizations": ["optimize_duct_sizing"],
            }
        )

        bridge_service.suggestion_engine.generate_suggestions = AsyncMock(
            return_value=[
                {
                    "type": "optimization",
                    "message": "Consider energy-efficient equipment",
                }
            ]
        )

        # Process the element
        result = await bridge_service.process_design_element(sample_hvac_element)

        # Verify result
        assert result.element_id == "hvac_001"
        assert result.engineering_validation["system_type"] == "hvac"
        assert result.code_compliance["overall_compliance"] is True
        assert len(result.suggestions) > 0

    @pytest.mark.asyncio
    async def test_process_plumbing_element_success(
        self, bridge_service, sample_plumbing_element
    ):
        """Test successful processing of plumbing design element."""
        # Mock service responses
        bridge_service.intelligence_service.analyze_context = AsyncMock(
            return_value={
                "confidence_score": 0.88,
                "context_analysis": {"user_intent": "plumbing_design"},
            }
        )

        bridge_service.validation_service.validate_element = AsyncMock(
            return_value={
                "system_type": "plumbing",
                "confidence_score": 0.94,
                "calculations": {"flow_rate": 50, "pressure": 60},
                "safety_checks": {"backflow_prevention": True},
            }
        )

        bridge_service.compliance_checker.check_compliance = AsyncMock(
            return_value={
                "overall_compliance": True,
                "confidence_score": 0.97,
                "system_compliance": {"plumbing": {"ipc_compliance": True}},
            }
        )

        bridge_service.cross_system_analyzer.analyze_cross_system_impacts = AsyncMock(
            return_value={
                "system_impacts": {"plumbing": {"structural_impact": "minimal"}},
                "conflicts": [],
                "optimizations": ["optimize_pipe_sizing"],
            }
        )

        bridge_service.suggestion_engine.generate_suggestions = AsyncMock(
            return_value=[
                {"type": "optimization", "message": "Consider water-efficient fixtures"}
            ]
        )

        # Process the element
        result = await bridge_service.process_design_element(sample_plumbing_element)

        # Verify result
        assert result.element_id == "plumbing_001"
        assert result.engineering_validation["system_type"] == "plumbing"
        assert result.code_compliance["overall_compliance"] is True
        assert len(result.suggestions) > 0

    @pytest.mark.asyncio
    async def test_process_structural_element_success(
        self, bridge_service, sample_structural_element
    ):
        """Test successful processing of structural design element."""
        # Mock service responses
        bridge_service.intelligence_service.analyze_context = AsyncMock(
            return_value={
                "confidence_score": 0.87,
                "context_analysis": {"user_intent": "structural_design"},
            }
        )

        bridge_service.validation_service.validate_element = AsyncMock(
            return_value={
                "system_type": "structural",
                "confidence_score": 0.93,
                "calculations": {"stress": 150, "deflection": 0.02},
                "safety_checks": {"buckling_stability": True},
            }
        )

        bridge_service.compliance_checker.check_compliance = AsyncMock(
            return_value={
                "overall_compliance": True,
                "confidence_score": 0.99,
                "system_compliance": {"structural": {"ibc_compliance": True}},
            }
        )

        bridge_service.cross_system_analyzer.analyze_cross_system_impacts = AsyncMock(
            return_value={
                "system_impacts": {"structural": {"electrical_impact": "significant"}},
                "conflicts": [],
                "optimizations": ["optimize_beam_sizing"],
            }
        )

        bridge_service.suggestion_engine.generate_suggestions = AsyncMock(
            return_value=[
                {"type": "optimization", "message": "Consider composite construction"}
            ]
        )

        # Process the element
        result = await bridge_service.process_design_element(sample_structural_element)

        # Verify result
        assert result.element_id == "beam_001"
        assert result.engineering_validation["system_type"] == "structural"
        assert result.code_compliance["overall_compliance"] is True
        assert len(result.suggestions) > 0

    @pytest.mark.asyncio
    async def test_process_element_with_service_failure(
        self, bridge_service, sample_electrical_element
    ):
        """Test processing when one or more services fail."""
        # Mock intelligence service failure
        bridge_service.intelligence_service.analyze_context = AsyncMock(
            side_effect=Exception("Service unavailable")
        )

        # Mock other services to succeed
        bridge_service.validation_service.validate_element = AsyncMock(
            return_value={
                "system_type": "electrical",
                "confidence_score": 0.95,
                "calculations": {"voltage": 480, "current": 100},
            }
        )

        bridge_service.compliance_checker.check_compliance = AsyncMock(
            return_value={"overall_compliance": True, "confidence_score": 0.98}
        )

        bridge_service.cross_system_analyzer.analyze_cross_system_impacts = AsyncMock(
            return_value={"system_impacts": {}, "conflicts": [], "optimizations": []}
        )

        bridge_service.suggestion_engine.generate_suggestions = AsyncMock(
            return_value=[]
        )

        # Process the element
        result = await bridge_service.process_design_element(sample_electrical_element)

        # Verify result still succeeds but with partial data
        assert result.element_id == "panel_001"
        assert result.intelligence_analysis is None
        assert result.engineering_validation is not None
        assert result.code_compliance is not None
        assert result.confidence_score > 0

    @pytest.mark.asyncio
    async def test_process_element_complete_failure(
        self, bridge_service, sample_electrical_element
    ):
        """Test processing when all services fail."""
        # Mock all services to fail
        bridge_service.intelligence_service.analyze_context = AsyncMock(
            side_effect=Exception("Service unavailable")
        )
        bridge_service.validation_service.validate_element = AsyncMock(
            side_effect=Exception("Validation failed")
        )
        bridge_service.compliance_checker.check_compliance = AsyncMock(
            side_effect=Exception("Compliance failed")
        )
        bridge_service.cross_system_analyzer.analyze_cross_system_impacts = AsyncMock(
            side_effect=Exception("Analysis failed")
        )
        bridge_service.suggestion_engine.generate_suggestions = AsyncMock(
            side_effect=Exception("Suggestions failed")
        )

        # Process the element
        result = await bridge_service.process_design_element(sample_electrical_element)

        # Verify error result
        assert result.element_id == "panel_001"
        assert result.intelligence_analysis is None
        assert result.engineering_validation is None
        assert result.code_compliance is None
        assert result.cross_system_analysis is None
        assert result.suggestions == []
        assert result.confidence_score == 0.0
        assert len(result.errors) > 0

    def test_calculate_confidence_score(self, bridge_service):
        """Test confidence score calculation."""
        # Test with all services returning results
        intelligence_result = MagicMock()
        intelligence_result.confidence_score = 0.8

        engineering_result = MagicMock()
        engineering_result.confidence_score = 0.9

        compliance_result = MagicMock()
        compliance_result.confidence_score = 0.95

        score = bridge_service._calculate_confidence_score(
            intelligence_result, engineering_result, compliance_result
        )

        expected_score = (0.8 + 0.9 + 0.95) / 3
        assert score == expected_score

        # Test with missing results
        score = bridge_service._calculate_confidence_score(
            None, engineering_result, compliance_result
        )
        expected_score = (0.9 + 0.95) / 2
        assert score == expected_score

        # Test with no results
        score = bridge_service._calculate_confidence_score(None, None, None)
        assert score == 0.0

    def test_get_health_status(self, bridge_service):
        """Test health status retrieval."""
        # Mock service health checks
        bridge_service.intelligence_service.is_healthy = MagicMock(return_value=True)
        bridge_service.engineering_service.is_healthy = MagicMock(return_value=True)
        bridge_service.validation_service.is_healthy = MagicMock(return_value=True)
        bridge_service.compliance_checker.is_healthy = MagicMock(return_value=True)
        bridge_service.cross_system_analyzer.is_healthy = MagicMock(return_value=True)
        bridge_service.suggestion_engine.is_healthy = MagicMock(return_value=True)

        status = bridge_service.get_health_status()

        assert status["status"] == "healthy"
        assert all(status["services"].values())
        assert status["config"]["enable_caching"] is True
        assert status["config"]["enable_metrics"] is True
        assert status["config"]["timeout_seconds"] == 30

    @pytest.mark.asyncio
    async def test_validate_electrical_element(
        self, bridge_service, sample_electrical_element
    ):
        """Test electrical element validation."""
        # Mock the process_design_element method
        bridge_service.process_design_element = AsyncMock(return_value=MagicMock())

        result = await bridge_service.validate_electrical_element(
            sample_electrical_element
        )

        # Verify system type was set
        assert sample_electrical_element["system_type"] == "electrical"
        bridge_service.process_design_element.assert_called_once()

    @pytest.mark.asyncio
    async def test_validate_hvac_element(self, bridge_service, sample_hvac_element):
        """Test HVAC element validation."""
        bridge_service.process_design_element = AsyncMock(return_value=MagicMock())

        result = await bridge_service.validate_hvac_element(sample_hvac_element)

        assert sample_hvac_element["system_type"] == "hvac"
        bridge_service.process_design_element.assert_called_once()

    @pytest.mark.asyncio
    async def test_validate_plumbing_element(
        self, bridge_service, sample_plumbing_element
    ):
        """Test plumbing element validation."""
        bridge_service.process_design_element = AsyncMock(return_value=MagicMock())

        result = await bridge_service.validate_plumbing_element(sample_plumbing_element)

        assert sample_plumbing_element["system_type"] == "plumbing"
        bridge_service.process_design_element.assert_called_once()

    @pytest.mark.asyncio
    async def test_validate_structural_element(
        self, bridge_service, sample_structural_element
    ):
        """Test structural element validation."""
        bridge_service.process_design_element = AsyncMock(return_value=MagicMock())

        result = await bridge_service.validate_structural_element(
            sample_structural_element
        )

        assert sample_structural_element["system_type"] == "structural"
        bridge_service.process_design_element.assert_called_once()

    @pytest.mark.asyncio
    async def test_validate_multi_system_element(
        self, bridge_service, sample_electrical_element
    ):
        """Test multi-system element validation."""
        bridge_service.process_design_element = AsyncMock(return_value=MagicMock())

        result = await bridge_service.validate_multi_system_element(
            sample_electrical_element
        )

        assert sample_electrical_element["system_type"] == "multi_system"
        bridge_service.process_design_element.assert_called_once()


class TestBridgeConfig:
    """Unit tests for BridgeConfig."""

    def test_bridge_config_defaults(self):
        """Test bridge configuration defaults."""
        config = BridgeConfig()

        assert config.enable_caching is True
        assert config.cache_ttl == 3600
        assert config.enable_metrics is True
        assert config.enable_logging is True
        assert config.timeout_seconds == 30

    def test_bridge_config_custom(self):
        """Test bridge configuration with custom values."""
        config = BridgeConfig(
            enable_caching=False,
            cache_ttl=1800,
            enable_metrics=False,
            enable_logging=False,
            timeout_seconds=60,
        )

        assert config.enable_caching is False
        assert config.cache_ttl == 1800
        assert config.enable_metrics is False
        assert config.enable_logging is False
        assert config.timeout_seconds == 60
