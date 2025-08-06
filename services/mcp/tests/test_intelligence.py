#!/usr/bin/env python3
"""
Tests for MCP Intelligence Layer

Comprehensive tests for the intelligence service, context analyzer,
suggestion engine, and proactive monitor.
"""

import pytest
import asyncio
from typing import Dict, Any
from datetime import datetime

from intelligence.intelligence_service import MCPIntelligenceService
from intelligence.context_analyzer import ContextAnalyzer
from intelligence.suggestion_engine import SuggestionEngine
from intelligence.proactive_monitor import ProactiveMonitor
from intelligence.models import (
    UserIntent,
    ModelContext,
    Suggestion,
    Alert,
    Improvement,
    Conflict,
    ValidationResult,
    CodeReference,
    SuggestionType,
    AlertSeverity,
    ValidationStatus,
)


class TestIntelligenceService:
    """Test the main intelligence service"""

    @pytest.fixture
    def intelligence_service(self):
        """Create intelligence service instance"""
        return MCPIntelligenceService()

    @pytest.fixture
    def sample_model_state(self):
        """Sample model state for testing"""
        return {
            "building_type": "office",
            "jurisdiction": "IFC_2018",
            "floor_count": 2,
            "total_area": 5000.0,
            "occupancy_type": "business",
            "elements": [
                {"id": "wall_1", "type": "wall", "location": {"x": 0, "y": 0}},
                {"id": "door_1", "type": "door", "location": {"x": 10, "y": 0}},
            ],
            "systems": [
                {"id": "electrical_1", "type": "electrical"},
                {"id": "hvac_1", "type": "hvac"},
            ],
            "violations": [],
        }

    @pytest.mark.asyncio
    async def test_provide_context(self, intelligence_service, sample_model_state):
        """Test providing context for object placement"""
        context = await intelligence_service.provide_context(
            object_type="fire_extinguisher",
            location={"x": 5, "y": 5, "floor": 1},
            model_state=sample_model_state,
        )

        assert context is not None
        assert context.user_intent is not None
        assert context.model_context is not None
        assert len(context.suggestions) > 0
        assert context.validation_result is not None

    @pytest.mark.asyncio
    async def test_generate_suggestions(self, intelligence_service, sample_model_state):
        """Test generating suggestions"""
        suggestions = await intelligence_service.generate_suggestions(
            action="add_fire_extinguisher", model_state=sample_model_state
        )

        assert len(suggestions) > 0
        assert all(isinstance(s, Suggestion) for s in suggestions)

    @pytest.mark.asyncio
    async def test_validate_realtime(self, intelligence_service, sample_model_state):
        """Test real-time validation"""
        changes = {
            "elements": [
                {
                    "id": "fire_ext_1",
                    "type": "fire_extinguisher",
                    "location": {"x": 5, "y": 5},
                }
            ]
        }

        result = await intelligence_service.validate_realtime(
            model_changes=changes, model_state=sample_model_state
        )

        assert isinstance(result, ValidationResult)
        assert result.status in [
            ValidationStatus.PASS,
            ValidationStatus.FAIL,
            ValidationStatus.WARNING,
        ]

    @pytest.mark.asyncio
    async def test_get_code_reference(self, intelligence_service):
        """Test getting code reference"""
        code_ref = await intelligence_service.get_code_reference(
            requirement="906.1", jurisdiction="IFC_2018"
        )

        assert isinstance(code_ref, CodeReference)
        assert code_ref.code == "IFC 2018"
        assert code_ref.section == "906.1"

    @pytest.mark.asyncio
    async def test_monitor_proactive(self, intelligence_service, sample_model_state):
        """Test proactive monitoring"""
        alerts = await intelligence_service.monitor_proactive(sample_model_state)

        assert isinstance(alerts, list)
        assert all(isinstance(alert, Alert) for alert in alerts)

    @pytest.mark.asyncio
    async def test_suggest_improvements(self, intelligence_service, sample_model_state):
        """Test suggesting improvements"""
        improvements = await intelligence_service.suggest_improvements(
            sample_model_state
        )

        assert isinstance(improvements, list)
        assert all(isinstance(improvement, Improvement) for improvement in improvements)


class TestContextAnalyzer:
    """Test the context analyzer"""

    @pytest.fixture
    def context_analyzer(self):
        """Create context analyzer instance"""
        return ContextAnalyzer()

    @pytest.mark.asyncio
    async def test_analyze_user_intent(self, context_analyzer):
        """Test user intent analysis"""
        intent = await context_analyzer.analyze_user_intent(
            action="add_fire_extinguisher",
            object_type="fire_extinguisher",
            location={"x": 5, "y": 5},
        )

        assert isinstance(intent, UserIntent)
        assert intent.action == "add_fire_extinguisher"
        assert intent.object_type == "fire_extinguisher"
        assert intent.confidence > 0.0

    @pytest.mark.asyncio
    async def test_analyze_model_context(self, context_analyzer, sample_model_state):
        """Test model context analysis"""
        context = await context_analyzer.analyze_model_context(sample_model_state)

        assert isinstance(context, ModelContext)
        assert context.building_type == "office"
        assert context.jurisdiction == "IFC_2018"
        assert len(context.elements) == 2

    @pytest.mark.asyncio
    async def test_analyze_changes(self, context_analyzer):
        """Test change analysis"""
        changes = {"elements": [{"id": "new_element", "type": "fire_extinguisher"}]}

        analysis = await context_analyzer.analyze_changes(changes)

        assert isinstance(analysis, dict)
        assert "change_type" in analysis
        assert "affected_elements" in analysis
        assert "impact_level" in analysis

    @pytest.mark.asyncio
    async def test_predict_user_needs(self, context_analyzer, sample_model_state):
        """Test user need prediction"""
        model_context = await context_analyzer.analyze_model_context(sample_model_state)
        recent_actions = ["add_fire_extinguisher", "add_door"]

        predictions = await context_analyzer.predict_user_needs(
            model_context, recent_actions
        )

        assert isinstance(predictions, list)
        assert len(predictions) > 0


class TestSuggestionEngine:
    """Test the suggestion engine"""

    @pytest.fixture
    def suggestion_engine(self):
        """Create suggestion engine instance"""
        return SuggestionEngine()

    @pytest.fixture
    def sample_model_context(self):
        """Sample model context for testing"""
        return ModelContext(
            building_type="office",
            jurisdiction="IFC_2018",
            floor_count=2,
            total_area=5000.0,
            occupancy_type="business",
            elements=[],
            systems=[],
            violations=[],
        )

    @pytest.mark.asyncio
    async def test_generate_suggestions(self, suggestion_engine, sample_model_context):
        """Test generating suggestions"""
        suggestions = await suggestion_engine.generate_suggestions(
            object_type="fire_extinguisher",
            location={"x": 5, "y": 5},
            model_context=sample_model_context,
        )

        assert len(suggestions) > 0
        assert all(isinstance(s, Suggestion) for s in suggestions)

    @pytest.mark.asyncio
    async def test_generate_fix_suggestions(self, suggestion_engine):
        """Test generating fix suggestions"""
        validation_result = ValidationResult(
            status=ValidationStatus.FAIL,
            message="Fire extinguisher placement violates code",
            violations=[
                {
                    "code": "IFC 2018",
                    "section": "906.1",
                    "description": "Placement issue",
                }
            ],
            warnings=[],
            confidence=0.9,
        )

        suggestions = await suggestion_engine.generate_fix_suggestions(
            validation_result=validation_result
        )

        assert len(suggestions) > 0
        assert all(isinstance(s, Suggestion) for s in suggestions)

    @pytest.mark.asyncio
    async def test_generate_improvements(self, suggestion_engine, sample_model_context):
        """Test generating improvements"""
        improvements = await suggestion_engine.generate_improvements(
            sample_model_context
        )

        assert isinstance(improvements, list)
        assert all(isinstance(improvement, Improvement) for improvement in improvements)


class TestProactiveMonitor:
    """Test the proactive monitor"""

    @pytest.fixture
    def proactive_monitor(self):
        """Create proactive monitor instance"""
        return ProactiveMonitor()

    @pytest.fixture
    def sample_model_context(self):
        """Sample model context for testing"""
        return ModelContext(
            building_type="office",
            jurisdiction="IFC_2018",
            floor_count=2,
            total_area=5000.0,
            occupancy_type="business",
            elements=[],
            systems=[],
            violations=[],
        )

    @pytest.mark.asyncio
    async def test_generate_alerts(self, proactive_monitor, sample_model_context):
        """Test generating alerts"""
        alerts = await proactive_monitor.generate_alerts(
            object_type="fire_extinguisher",
            location={"x": 5, "y": 5},
            model_context=sample_model_context,
        )

        assert isinstance(alerts, list)
        assert all(isinstance(alert, Alert) for alert in alerts)

    @pytest.mark.asyncio
    async def test_detect_conflicts(self, proactive_monitor, sample_model_context):
        """Test detecting conflicts"""
        conflicts = await proactive_monitor.detect_conflicts(
            object_type="fire_extinguisher",
            location={"x": 5, "y": 5},
            model_context=sample_model_context,
        )

        assert isinstance(conflicts, list)
        assert all(isinstance(conflict, Conflict) for conflict in conflicts)

    @pytest.mark.asyncio
    async def test_monitor_changes(self, proactive_monitor, sample_model_context):
        """Test monitoring changes"""
        changes = {"elements": [{"id": "new_element", "type": "fire_extinguisher"}]}

        alerts = await proactive_monitor.monitor_changes(changes, sample_model_context)

        assert isinstance(alerts, list)
        assert all(isinstance(alert, Alert) for alert in alerts)


class TestIntelligenceModels:
    """Test the intelligence data models"""

    def test_suggestion_model(self):
        """Test suggestion model"""
        suggestion = Suggestion(
            type=SuggestionType.PLACEMENT,
            title="Test Suggestion",
            description="Test description",
            confidence=0.9,
            priority=1,
        )

        assert suggestion.type == SuggestionType.PLACEMENT
        assert suggestion.title == "Test Suggestion"
        assert suggestion.confidence == 0.9

    def test_alert_model(self):
        """Test alert model"""
        alert = Alert(
            severity=AlertSeverity.WARNING,
            title="Test Alert",
            description="Test description",
            category="Safety",
        )

        assert alert.severity == AlertSeverity.WARNING
        assert alert.title == "Test Alert"

    def test_validation_result_model(self):
        """Test validation result model"""
        result = ValidationResult(
            status=ValidationStatus.PASS, message="Test validation", confidence=0.9
        )

        assert result.status == ValidationStatus.PASS
        assert result.message == "Test validation"
        assert result.confidence == 0.9

    def test_code_reference_model(self):
        """Test code reference model"""
        code_ref = CodeReference(
            code="IFC 2018",
            section="906.1",
            title="Fire Extinguishers",
            description="Requirements for fire extinguisher placement",
            requirements=["Requirement 1", "Requirement 2"],
            jurisdiction="International",
        )

        assert code_ref.code == "IFC 2018"
        assert code_ref.section == "906.1"
        assert len(code_ref.requirements) == 2


if __name__ == "__main__":
    pytest.main([__file__])
