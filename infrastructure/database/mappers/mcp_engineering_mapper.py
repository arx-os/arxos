"""
MCP-Engineering Database Mappers

This module contains mappers for converting between MCP-Engineering domain entities
and SQLAlchemy database models.
"""

from typing import List, Optional
from datetime import datetime
import uuid

from domain.mcp_engineering_entities import (
    BuildingData,
    ComplianceIssue,
    AIRecommendation,
    ValidationResult,
    ValidationSession,
    KnowledgeSearchResult,
    MLPrediction,
    ComplianceReport,
    ValidationStatistics,
    ValidationStatus,
    ValidationType,
    IssueSeverity,
    SuggestionType,
    ReportType,
    ReportFormat,
)
from infrastructure.database.models.mcp_engineering import (
    MCPBuildingData,
    MCPComplianceIssue,
    MCPAIRecommendation,
    MCPValidationResult,
    MCPValidationSession,
    MCPKnowledgeSearchResult,
    MCPMLPrediction,
    MCPComplianceReport,
    MCPValidationStatistics,
)


class MCPEngineeringMapper:
    """Mapper for MCP-Engineering entities and database models."""

    @staticmethod
    def building_data_to_model(building_data: BuildingData) -> MCPBuildingData:
        """Convert BuildingData domain entity to database model."""
        return MCPBuildingData(
            id=uuid.UUID(building_data.id) if building_data.id else None,
            area=building_data.area,
            height=building_data.height,
            building_type=building_data.building_type,
            occupancy=building_data.occupancy,
            floors=building_data.floors,
            jurisdiction=building_data.jurisdiction,
            address=building_data.address,
            construction_type=building_data.construction_type,
            year_built=building_data.year_built,
            renovation_year=building_data.renovation_year,
            created_at=building_data.created_at,
            updated_at=building_data.updated_at,
        )

    @staticmethod
    def building_data_to_entity(model: MCPBuildingData) -> BuildingData:
        """Convert database model to BuildingData domain entity."""
        return BuildingData(
            id=str(model.id),
            area=model.area,
            height=model.height,
            building_type=model.building_type,
            occupancy=model.occupancy,
            floors=model.floors,
            jurisdiction=model.jurisdiction,
            address=model.address,
            construction_type=model.construction_type,
            year_built=model.year_built,
            renovation_year=model.renovation_year,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    @staticmethod
    def compliance_issue_to_model(
        issue: ComplianceIssue, validation_result_id: Optional[str] = None
    ) -> MCPComplianceIssue:
        """Convert ComplianceIssue domain entity to database model."""
        return MCPComplianceIssue(
            id=uuid.UUID(issue.id) if issue.id else None,
            code_reference=issue.code_reference,
            severity=issue.severity.value,
            description=issue.description,
            resolution=issue.resolution,
            affected_systems=issue.affected_systems,
            estimated_cost=issue.estimated_cost,
            created_at=issue.created_at,
            updated_at=issue.updated_at,
            validation_result_id=(
                uuid.UUID(validation_result_id) if validation_result_id else None
            ),
        )

    @staticmethod
    def compliance_issue_to_entity(model: MCPComplianceIssue) -> ComplianceIssue:
        """Convert database model to ComplianceIssue domain entity."""
        return ComplianceIssue(
            id=str(model.id),
            code_reference=model.code_reference,
            severity=IssueSeverity(model.severity),
            description=model.description,
            resolution=model.resolution,
            affected_systems=model.affected_systems or [],
            estimated_cost=model.estimated_cost,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    @staticmethod
    def ai_recommendation_to_model(
        recommendation: AIRecommendation, validation_result_id: Optional[str] = None
    ) -> MCPAIRecommendation:
        """Convert AIRecommendation domain entity to database model."""
        return MCPAIRecommendation(
            id=uuid.UUID(recommendation.id) if recommendation.id else None,
            type=recommendation.type.value,
            description=recommendation.description,
            confidence=recommendation.confidence,
            impact_score=recommendation.impact_score,
            implementation_cost=recommendation.implementation_cost,
            estimated_savings=recommendation.estimated_savings,
            affected_systems=recommendation.affected_systems,
            created_at=recommendation.created_at,
            updated_at=recommendation.updated_at,
            validation_result_id=(
                uuid.UUID(validation_result_id) if validation_result_id else None
            ),
        )

    @staticmethod
    def ai_recommendation_to_entity(model: MCPAIRecommendation) -> AIRecommendation:
        """Convert database model to AIRecommendation domain entity."""
        return AIRecommendation(
            id=str(model.id),
            type=SuggestionType(model.type),
            description=model.description,
            confidence=model.confidence,
            impact_score=model.impact_score,
            implementation_cost=model.implementation_cost,
            estimated_savings=model.estimated_savings,
            affected_systems=model.affected_systems or [],
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    @staticmethod
    def validation_result_to_model(
        result: ValidationResult,
        building_data_id: str,
        validation_session_id: Optional[str] = None,
    ) -> MCPValidationResult:
        """Convert ValidationResult domain entity to database model."""
        return MCPValidationResult(
            id=uuid.UUID(result.id) if result.id else None,
            validation_type=result.validation_type.value,
            status=result.status.value,
            confidence_score=result.confidence_score,
            processing_time=result.processing_time,
            model_version=result.model_version,
            created_at=result.created_at,
            completed_at=result.completed_at,
            building_data_id=uuid.UUID(building_data_id),
            validation_session_id=(
                uuid.UUID(validation_session_id) if validation_session_id else None
            ),
        )

    @staticmethod
    def validation_result_to_entity(
        model: MCPValidationResult,
        building_data: BuildingData,
        issues: List[ComplianceIssue],
        suggestions: List[AIRecommendation],
    ) -> ValidationResult:
        """Convert database model to ValidationResult domain entity."""
        return ValidationResult(
            id=str(model.id),
            building_data=building_data,
            validation_type=ValidationType(model.validation_type),
            status=ValidationStatus(model.status),
            issues=issues,
            suggestions=suggestions,
            confidence_score=model.confidence_score,
            processing_time=model.processing_time,
            model_version=model.model_version,
            created_at=model.created_at,
            completed_at=model.completed_at,
        )

    @staticmethod
    def validation_session_to_model(
        session: ValidationSession, building_data_id: str
    ) -> MCPValidationSession:
        """Convert ValidationSession domain entity to database model."""
        return MCPValidationSession(
            id=uuid.UUID(session.id) if session.id else None,
            user_id=session.user_id,
            validation_type=session.validation_type.value,
            project_id=session.project_id,
            status=session.status.value,
            include_suggestions=session.include_suggestions,
            confidence_threshold=session.confidence_threshold,
            started_at=session.started_at,
            completed_at=session.completed_at,
            processing_time=session.processing_time,
            building_data_id=uuid.UUID(building_data_id),
        )

    @staticmethod
    def validation_session_to_entity(
        model: MCPValidationSession,
        building_data: BuildingData,
        validation_result: Optional[ValidationResult] = None,
    ) -> ValidationSession:
        """Convert database model to ValidationSession domain entity."""
        return ValidationSession(
            id=str(model.id),
            user_id=model.user_id,
            building_data=building_data,
            validation_type=ValidationType(model.validation_type),
            project_id=model.project_id,
            status=ValidationStatus(model.status),
            validation_result=validation_result,
            include_suggestions=model.include_suggestions,
            confidence_threshold=model.confidence_threshold,
            started_at=model.started_at,
            completed_at=model.completed_at,
            processing_time=model.processing_time,
        )

    @staticmethod
    def knowledge_search_result_to_model(
        result: KnowledgeSearchResult,
    ) -> MCPKnowledgeSearchResult:
        """Convert KnowledgeSearchResult domain entity to database model."""
        return MCPKnowledgeSearchResult(
            id=uuid.UUID(result.id) if result.id else None,
            code_reference=result.code_reference,
            title=result.title,
            content=result.content,
            code_standard=result.code_standard,
            relevance_score=result.relevance_score,
            section_number=result.section_number,
            subsection=result.subsection,
            jurisdiction=result.jurisdiction,
            effective_date=result.effective_date,
            created_at=result.created_at,
        )

    @staticmethod
    def knowledge_search_result_to_entity(
        model: MCPKnowledgeSearchResult,
    ) -> KnowledgeSearchResult:
        """Convert database model to KnowledgeSearchResult domain entity."""
        return KnowledgeSearchResult(
            id=str(model.id),
            code_reference=model.code_reference,
            title=model.title,
            content=model.content,
            code_standard=model.code_standard,
            relevance_score=model.relevance_score,
            section_number=model.section_number,
            subsection=model.subsection,
            jurisdiction=model.jurisdiction,
            effective_date=model.effective_date,
            created_at=model.created_at,
        )

    @staticmethod
    def ml_prediction_to_model(prediction: MLPrediction) -> MCPMLPrediction:
        """Convert MLPrediction domain entity to database model."""
        return MCPMLPrediction(
            id=uuid.UUID(prediction.id) if prediction.id else None,
            prediction_type=prediction.prediction_type,
            prediction_value=prediction.prediction_value,
            confidence=prediction.confidence,
            model_version=prediction.model_version,
            model_name=prediction.model_name,
            features=prediction.features,
            processing_time=prediction.processing_time,
            created_at=prediction.created_at,
        )

    @staticmethod
    def ml_prediction_to_entity(model: MCPMLPrediction) -> MLPrediction:
        """Convert database model to MLPrediction domain entity."""
        return MLPrediction(
            id=str(model.id),
            prediction_type=model.prediction_type,
            prediction_value=model.prediction_value,
            confidence=model.confidence,
            model_version=model.model_version,
            model_name=model.model_name,
            features=model.features or [],
            processing_time=model.processing_time,
            created_at=model.created_at,
        )

    @staticmethod
    def compliance_report_to_model(
        report: ComplianceReport, building_data_id: str
    ) -> MCPComplianceReport:
        """Convert ComplianceReport domain entity to database model."""
        return MCPComplianceReport(
            id=uuid.UUID(report.id) if report.id else None,
            report_type=report.report_type.value,
            format=report.format.value,
            user_id=report.user_id,
            project_id=report.project_id,
            generated_at=report.generated_at,
            download_url=report.download_url,
            file_size=report.file_size,
            checksum=report.checksum,
            building_data_id=uuid.UUID(building_data_id),
        )

    @staticmethod
    def compliance_report_to_entity(
        model: MCPComplianceReport,
        building_data: BuildingData,
        validation_results: List[ValidationResult],
    ) -> ComplianceReport:
        """Convert database model to ComplianceReport domain entity."""
        return ComplianceReport(
            id=str(model.id),
            building_data=building_data,
            validation_results=validation_results,
            report_type=ReportType(model.report_type),
            format=ReportFormat(model.format),
            user_id=model.user_id,
            project_id=model.project_id,
            generated_at=model.generated_at,
            download_url=model.download_url,
            file_size=model.file_size,
            checksum=model.checksum,
        )

    @staticmethod
    def validation_statistics_to_model(
        stats: ValidationStatistics,
    ) -> MCPValidationStatistics:
        """Convert ValidationStatistics domain entity to database model."""
        return MCPValidationStatistics(
            id=uuid.UUID(stats.id) if stats.id else None,
            total_validations=stats.total_validations,
            successful_validations=stats.successful_validations,
            failed_validations=stats.failed_validations,
            average_processing_time=stats.average_processing_time,
            total_processing_time=stats.total_processing_time,
            average_confidence_score=stats.average_confidence_score,
            total_issues_found=stats.total_issues_found,
            total_suggestions_generated=stats.total_suggestions_generated,
            most_common_validation_type=stats.most_common_validation_type,
            last_validation_at=stats.last_validation_at,
            created_at=stats.created_at,
            updated_at=stats.updated_at,
        )

    @staticmethod
    def validation_statistics_to_entity(
        model: MCPValidationStatistics,
    ) -> ValidationStatistics:
        """Convert database model to ValidationStatistics domain entity."""
        return ValidationStatistics(
            id=str(model.id),
            total_validations=model.total_validations,
            successful_validations=model.successful_validations,
            failed_validations=model.failed_validations,
            average_processing_time=model.average_processing_time,
            total_processing_time=model.total_processing_time,
            average_confidence_score=model.average_confidence_score,
            total_issues_found=model.total_issues_found,
            total_suggestions_generated=model.total_suggestions_generated,
            most_common_validation_type=model.most_common_validation_type,
            last_validation_at=model.last_validation_at,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
