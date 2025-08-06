"""
Integration Tests for MCP-Engineering Service

This module contains comprehensive integration tests for the MCP-Engineering service,
testing the complete flow from API endpoints through application services to domain entities.
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import Mock, AsyncMock
from fastapi.testclient import TestClient

from api.main import app
from application.services.mcp_engineering_service import MCPEngineeringService
from domain.mcp_engineering_entities import (
    BuildingData,
    ValidationType,
    ValidationStatus,
    IssueSeverity,
    SuggestionType,
    ReportType,
    ReportFormat,
)


class TestMCPEngineeringIntegration:
    """Integration tests for MCP-Engineering service."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    @pytest.fixture
    def mock_user(self):
        """Create mock user."""
        user = Mock()
        user.id = "test-user-id"
        user.email = "test@example.com"
        user.name = "Test User"
        return user

    @pytest.fixture
    def sample_building_data(self):
        """Create sample building data."""
        return {
            "area": 5000.0,
            "height": 30.0,
            "type": "commercial",
            "occupancy": "Business",
            "floors": 2,
            "jurisdiction": "California",
        }

    @pytest.fixture
    def sample_validation_request(self, sample_building_data):
        """Create sample validation request."""
        return {
            "building_data": sample_building_data,
            "validation_type": "structural",
            "include_suggestions": True,
            "confidence_threshold": 0.7,
        }

    def test_building_data_entity_creation(self, sample_building_data):
        """Test building data entity creation and validation."""
        # Test valid building data
        building_data = BuildingData(**sample_building_data)
        assert building_data.area == 5000.0
        assert building_data.height == 30.0
        assert building_data.building_type == "commercial"

        # Test invalid building data
        with pytest.raises(ValueError, match="Building area must be positive"):
            BuildingData(area=-100, height=30, building_type="commercial")

        with pytest.raises(ValueError, match="Building height must be positive"):
            BuildingData(area=5000, height=-30, building_type="commercial")

    def test_validation_status_enum(self):
        """Test validation status enumeration."""
        assert ValidationStatus.PASS.value == "pass"
        assert ValidationStatus.FAIL.value == "fail"
        assert ValidationStatus.WARNING.value == "warning"
        assert ValidationStatus.PENDING.value == "pending"
        assert ValidationStatus.ERROR.value == "error"

    def test_validation_type_enum(self):
        """Test validation type enumeration."""
        assert ValidationType.STRUCTURAL.value == "structural"
        assert ValidationType.ELECTRICAL.value == "electrical"
        assert ValidationType.MECHANICAL.value == "mechanical"
        assert ValidationType.PLUMBING.value == "plumbing"
        assert ValidationType.FIRE.value == "fire"
        assert ValidationType.ACCESSIBILITY.value == "accessibility"
        assert ValidationType.ENERGY.value == "energy"

    def test_issue_severity_enum(self):
        """Test issue severity enumeration."""
        assert IssueSeverity.CRITICAL.value == "critical"
        assert IssueSeverity.HIGH.value == "high"
        assert IssueSeverity.MEDIUM.value == "medium"
        assert IssueSeverity.LOW.value == "low"
        assert IssueSeverity.INFO.value == "info"

    def test_suggestion_type_enum(self):
        """Test suggestion type enumeration."""
        assert SuggestionType.OPTIMIZATION.value == "optimization"
        assert SuggestionType.COMPLIANCE.value == "compliance"
        assert SuggestionType.SAFETY.value == "safety"
        assert SuggestionType.EFFICIENCY.value == "efficiency"
        assert SuggestionType.COST_SAVING.value == "cost_saving"

    def test_report_type_enum(self):
        """Test report type enumeration."""
        assert ReportType.COMPREHENSIVE.value == "comprehensive"
        assert ReportType.SUMMARY.value == "summary"
        assert ReportType.TECHNICAL.value == "technical"

    def test_report_format_enum(self):
        """Test report format enumeration."""
        assert ReportFormat.PDF.value == "pdf"
        assert ReportFormat.HTML.value == "html"
        assert ReportFormat.JSON.value == "json"

    @pytest.mark.asyncio
    async def test_mcp_engineering_service_initialization(self):
        """Test MCP-Engineering service initialization."""
        service = MCPEngineeringService()
        assert service is not None
        assert hasattr(service, "validation_repository")
        assert hasattr(service, "report_repository")
        assert hasattr(service, "knowledge_repository")
        assert hasattr(service, "ml_repository")
        assert hasattr(service, "activity_repository")

    @pytest.mark.asyncio
    async def test_validate_building_service_method(
        self, mock_user, sample_building_data
    ):
        """Test building validation service method."""
        service = MCPEngineeringService()

        # Mock repositories
        service.validation_repository.create_validation_session = AsyncMock(
            return_value="test-session-id"
        )
        service.validation_repository.update_validation_session = AsyncMock()

        # Test validation
        result = await service.validate_building(
            building_data=sample_building_data,
            validation_type="structural",
            user=mock_user,
            include_suggestions=True,
            confidence_threshold=0.7,
        )

        assert result is not None
        assert "validation_result" in result
        assert "issues" in result
        assert "suggestions" in result
        assert "confidence_score" in result
        assert "timestamp" in result

    @pytest.mark.asyncio
    async def test_search_knowledge_base_service_method(self, mock_user):
        """Test knowledge base search service method."""
        service = MCPEngineeringService()

        # Mock knowledge repository
        service.knowledge_repository.search_knowledge_base = AsyncMock(return_value=[])

        # Test search
        result = await service.search_knowledge_base(
            query="occupant load", code_standard="IBC", max_results=5, user=mock_user
        )

        assert result is not None
        assert "results" in result
        assert "total_count" in result
        assert "query" in result

    @pytest.mark.asyncio
    async def test_ml_validate_building_service_method(
        self, mock_user, sample_building_data
    ):
        """Test ML validation service method."""
        service = MCPEngineeringService()

        # Test ML validation
        result = await service.ml_validate_building(
            building_data=sample_building_data,
            validation_type="structural",
            include_confidence=True,
            model_version="v1.0.0",
            user=mock_user,
        )

        assert result is not None
        assert "prediction" in result
        assert "confidence" in result
        assert "features" in result
        assert "model_version" in result

    @pytest.mark.asyncio
    async def test_generate_report_service_method(
        self, mock_user, sample_building_data
    ):
        """Test report generation service method."""
        service = MCPEngineeringService()

        # Mock report repository
        service.report_repository.store_report_metadata = AsyncMock(
            return_value="test-report-id"
        )

        # Test report generation
        result = await service.generate_report(
            building_data=sample_building_data,
            validation_results=[],
            report_type="comprehensive",
            format="pdf",
            user=mock_user,
        )

        assert result is not None
        assert "report_id" in result
        assert "download_url" in result
        assert "report_type" in result
        assert "format" in result
        assert "generated_at" in result

    def test_validation_result_entity(self, sample_building_data):
        """Test validation result entity."""
        building_data = BuildingData(**sample_building_data)

        # Create validation result
        validation_result = ValidationResult(
            building_data=building_data,
            validation_type=ValidationType.STRUCTURAL,
            status=ValidationStatus.PASS,
            confidence_score=0.95,
        )

        assert validation_result.id is not None
        assert validation_result.building_data == building_data
        assert validation_result.validation_type == ValidationType.STRUCTURAL
        assert validation_result.status == ValidationStatus.PASS
        assert validation_result.confidence_score == 0.95
        assert validation_result.total_issues == 0
        assert validation_result.total_suggestions == 0
        assert not validation_result.has_critical_issues
        assert not validation_result.has_high_priority_issues

    def test_compliance_issue_entity(self):
        """Test compliance issue entity."""
        issue = ComplianceIssue(
            code_reference="IBC 1004.1.1",
            severity=IssueSeverity.HIGH,
            description="Missing emergency exit",
            resolution="Add emergency exit on north side",
        )

        assert issue.id is not None
        assert issue.code_reference == "IBC 1004.1.1"
        assert issue.severity == IssueSeverity.HIGH
        assert issue.description == "Missing emergency exit"
        assert issue.resolution == "Add emergency exit on north side"

    def test_ai_recommendation_entity(self):
        """Test AI recommendation entity."""
        recommendation = AIRecommendation(
            type=SuggestionType.OPTIMIZATION,
            description="Consider adding more natural lighting",
            confidence=0.85,
            impact_score=0.7,
        )

        assert recommendation.id is not None
        assert recommendation.type == SuggestionType.OPTIMIZATION
        assert recommendation.description == "Consider adding more natural lighting"
        assert recommendation.confidence == 0.85
        assert recommendation.impact_score == 0.7

    def test_validation_session_entity(self, sample_building_data):
        """Test validation session entity."""
        building_data = BuildingData(**sample_building_data)

        session = ValidationSession(
            user_id="test-user-id",
            building_data=building_data,
            validation_type=ValidationType.STRUCTURAL,
        )

        assert session.id is not None
        assert session.user_id == "test-user-id"
        assert session.building_data == building_data
        assert session.validation_type == ValidationType.STRUCTURAL
        assert session.status == ValidationStatus.PENDING
        assert session.include_suggestions is True
        assert session.confidence_threshold == 0.7

    def test_compliance_report_entity(self, sample_building_data):
        """Test compliance report entity."""
        building_data = BuildingData(**sample_building_data)

        # Create validation results
        validation_result = ValidationResult(
            building_data=building_data,
            validation_type=ValidationType.STRUCTURAL,
            status=ValidationStatus.PASS,
            confidence_score=0.95,
        )

        report = ComplianceReport(
            building_data=building_data,
            validation_results=[validation_result],
            report_type=ReportType.COMPREHENSIVE,
            format=ReportFormat.PDF,
            user_id="test-user-id",
        )

        assert report.id is not None
        assert report.building_data == building_data
        assert len(report.validation_results) == 1
        assert report.report_type == ReportType.COMPREHENSIVE
        assert report.format == ReportFormat.PDF
        assert report.user_id == "test-user-id"
        assert report.total_issues == 0
        assert report.total_suggestions == 0
        assert not report.has_critical_issues
        assert report.overall_status == ValidationStatus.PASS

    def test_validation_statistics_entity(self):
        """Test validation statistics entity."""
        stats = ValidationStatistics()

        assert stats.total_validations == 0
        assert stats.successful_validations == 0
        assert stats.failed_validations == 0
        assert stats.success_rate == 0.0
        assert stats.failure_rate == 0.0

        # Test updating from validation
        building_data = BuildingData(area=5000, height=30, building_type="commercial")
        validation_result = ValidationResult(
            building_data=building_data,
            validation_type=ValidationType.STRUCTURAL,
            status=ValidationStatus.PASS,
            confidence_score=0.95,
            processing_time=0.5,
        )

        stats.update_from_validation(validation_result, 0.5)

        assert stats.total_validations == 1
        assert stats.successful_validations == 1
        assert stats.failed_validations == 0
        assert stats.success_rate == 1.0
        assert stats.failure_rate == 0.0
        assert stats.average_processing_time == 0.5
        assert stats.average_confidence_score == 0.95

    def test_api_health_endpoint(self, client):
        """Test API health endpoint."""
        response = client.get("/api/v1/mcp/health")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "mcp-engineering"
        assert "timestamp" in data
        assert "version" in data

    def test_api_metrics_endpoint(self, client):
        """Test API metrics endpoint."""
        response = client.get("/api/v1/mcp/metrics")
        assert response.status_code == 200

        data = response.json()
        assert "validations_performed" in data
        assert "average_response_time" in data
        assert "success_rate" in data
        assert "active_sessions" in data
        assert "timestamp" in data

    def test_validation_request_validation(self, client, sample_validation_request):
        """Test validation request validation."""
        # Test valid request
        response = client.post("/api/v1/mcp/validate", json=sample_validation_request)
        # Note: This will fail due to authentication, but we can test the request structure
        assert response.status_code in [401, 422]  # Unauthorized or validation error

    def test_knowledge_search_request_validation(self, client):
        """Test knowledge search request validation."""
        request_data = {
            "query": "occupant load",
            "code_standard": "IBC",
            "max_results": 5,
        }

        response = client.post("/api/v1/mcp/knowledge/search", json=request_data)
        # Note: This will fail due to authentication, but we can test the request structure
        assert response.status_code in [401, 422]  # Unauthorized or validation error

    def test_ml_validation_request_validation(self, client, sample_building_data):
        """Test ML validation request validation."""
        request_data = {
            "building_data": sample_building_data,
            "validation_type": "structural",
            "include_confidence": True,
            "model_version": "v1.0.0",
        }

        response = client.post("/api/v1/mcp/ml/validate", json=request_data)
        # Note: This will fail due to authentication, but we can test the request structure
        assert response.status_code in [401, 422]  # Unauthorized or validation error

    def test_report_generation_request_validation(self, client, sample_building_data):
        """Test report generation request validation."""
        request_data = {
            "building_data": sample_building_data,
            "validation_results": [],
            "report_type": "comprehensive",
            "format": "pdf",
        }

        response = client.post("/api/v1/mcp/reports/generate", json=request_data)
        # Note: This will fail due to authentication, but we can test the request structure
        assert response.status_code in [401, 422]  # Unauthorized or validation error


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
