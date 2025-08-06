"""
MCP-Engineering Application Service

This service orchestrates MCP-Engineering business logic and coordinates with the domain layer.
It provides the application layer interface for engineering validation, compliance checking,
and AI-powered recommendations.
"""

import asyncio
import logging
from typing import List, Dict, Optional, Any
from datetime import datetime
from uuid import uuid4

from application.logging_config import get_logger
from application.exceptions import ApplicationError, ValidationError, BusinessRuleError
from domain.entities import Building, User, Project
from infrastructure.repository_factory import get_repository_factory

logger = get_logger("application.services.mcp_engineering_service")


class MCPEngineeringService:
    """
    Application service for MCP-Engineering operations.

    This service orchestrates:
    - Building validation against building codes
    - Knowledge base searches
    - ML-powered validation and predictions
    - Professional report generation
    - Real-time validation updates
    """

    def __init__(self):
        """Initialize the MCP-Engineering service."""
        self.repository_factory = get_repository_factory()
        self.building_repository = self.repository_factory.create_building_repository()
        self.validation_repository = (
            self.repository_factory.create_validation_repository()
        )
        self.report_repository = self.repository_factory.create_report_repository()
        self.knowledge_repository = (
            self.repository_factory.create_knowledge_repository()
        )
        self.ml_repository = self.repository_factory.create_ml_repository()
        self.activity_repository = self.repository_factory.create_activity_repository()

        # Service statistics
        self.stats = {
            "validations_performed": 0,
            "total_processing_time": 0.0,
            "average_response_time": 0.0,
            "success_rate": 0.0,
        }

        logger.info("MCP-Engineering service initialized")

    async def validate_building(
        self,
        building_data: Dict[str, Any],
        validation_type: str,
        user: User,
        project: Optional[Project] = None,
        include_suggestions: bool = True,
        confidence_threshold: float = 0.7,
    ) -> Dict[str, Any]:
        """
        Validate building against building codes.

        Args:
            building_data: Building information for validation
            validation_type: Type of validation (structural, electrical, etc.)
            user: User performing the validation
            project: Associated project (optional)
            include_suggestions: Include AI-powered suggestions
            confidence_threshold: Minimum confidence for suggestions

        Returns:
            Validation result with issues, suggestions, and confidence score
        """
        start_time = datetime.utcnow()

        try:
            # Validate input data
            self._validate_building_data(building_data)
            self._validate_validation_type(validation_type)

            # Create validation session
            validation_id = str(uuid4())
            session_data = {
                "validation_id": validation_id,
                "building_data": building_data,
                "validation_type": validation_type,
                "user_id": user.id,
                "project_id": project.id if project else None,
                "started_at": start_time,
                "include_suggestions": include_suggestions,
                "confidence_threshold": confidence_threshold,
            }

            # Store validation session
            await self.validation_repository.create_validation_session(session_data)

            # Perform validation
            validation_result = await self._perform_validation(
                building_data,
                validation_type,
                include_suggestions,
                confidence_threshold,
            )

            # Update session with results
            session_data.update(
                {
                    "completed_at": datetime.utcnow(),
                    "validation_result": validation_result["validation_result"],
                    "issues_count": len(validation_result["issues"]),
                    "suggestions_count": len(validation_result["suggestions"]),
                    "confidence_score": validation_result["confidence_score"],
                }
            )

            await self.validation_repository.update_validation_session(
                validation_id, session_data
            )

            # Update statistics
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            self._update_statistics(
                processing_time, validation_result["validation_result"] == "pass"
            )

            logger.info(f"Building validation completed: {validation_id}")
            return validation_result

        except Exception as e:
            logger.error(f"Building validation failed: {e}")
            raise ApplicationError(f"Building validation failed: {str(e)}")

    async def search_knowledge_base(
        self,
        query: str,
        code_standard: Optional[str] = None,
        max_results: int = 5,
        user: User = None,
    ) -> Dict[str, Any]:
        """
        Search building codes knowledge base.

        Args:
            query: Search query
            code_standard: Specific building code standard to search
            max_results: Maximum number of results to return
            user: User performing the search

        Returns:
            Search results with relevance scores
        """
        try:
            # Validate input
            if not query or len(query.strip()) < 2:
                raise ValidationError("Search query must be at least 2 characters")

            # Perform knowledge base search
            search_results = await self._perform_knowledge_search(
                query, code_standard, max_results
            )

            # Log search activity
            if user:
                await self._log_search_activity(
                    user.id, query, len(search_results["results"])
                )

            logger.info(f"Knowledge base search completed: {query}")
            return search_results

        except Exception as e:
            logger.error(f"Knowledge base search failed: {e}")
            raise ApplicationError(f"Knowledge base search failed: {str(e)}")

    async def ml_validate_building(
        self,
        building_data: Dict[str, Any],
        validation_type: str,
        include_confidence: bool = True,
        model_version: Optional[str] = None,
        user: User = None,
    ) -> Dict[str, Any]:
        """
        Perform ML-powered building validation.

        Args:
            building_data: Building information for ML validation
            validation_type: Type of ML validation
            include_confidence: Include confidence scores
            model_version: Specific ML model version to use
            user: User performing the validation

        Returns:
            ML validation result with predictions and confidence
        """
        try:
            # Validate input
            self._validate_building_data(building_data)
            self._validate_validation_type(validation_type)

            # Perform ML validation
            ml_result = await self._perform_ml_validation(
                building_data, validation_type, include_confidence, model_version
            )

            # Log ML validation activity
            if user:
                await self._log_ml_validation_activity(
                    user.id, validation_type, ml_result["confidence"]
                )

            logger.info(f"ML validation completed: {validation_type}")
            return ml_result

        except Exception as e:
            logger.error(f"ML validation failed: {e}")
            raise ApplicationError(f"ML validation failed: {str(e)}")

    async def generate_report(
        self,
        building_data: Dict[str, Any],
        validation_results: List[Dict[str, Any]],
        report_type: str = "comprehensive",
        format: str = "pdf",
        user: User = None,
        project: Optional[Project] = None,
    ) -> Dict[str, Any]:
        """
        Generate professional compliance report.

        Args:
            building_data: Building information for report
            validation_results: Validation results to include
            report_type: Type of report (comprehensive, summary, technical)
            format: Report format (pdf, html, json)
            user: User generating the report
            project: Associated project (optional)

        Returns:
            Report generation result with download URL
        """
        try:
            # Validate input
            self._validate_report_type(report_type)
            self._validate_report_format(format)

            # Generate report
            report_result = await self._generate_compliance_report(
                building_data, validation_results, report_type, format
            )

            # Store report metadata
            report_metadata = {
                "report_id": report_result["report_id"],
                "building_data": building_data,
                "validation_results": validation_results,
                "report_type": report_type,
                "format": format,
                "user_id": user.id if user else None,
                "project_id": project.id if project else None,
                "generated_at": datetime.utcnow(),
                "download_url": report_result["download_url"],
            }

            await self.report_repository.store_report_metadata(report_metadata)

            # Log report generation
            if user:
                await self._log_report_generation_activity(user.id, report_type, format)

            logger.info(f"Report generation completed: {report_result['report_id']}")
            return report_result

        except Exception as e:
            logger.error(f"Report generation failed: {e}")
            raise ApplicationError(f"Report generation failed: {str(e)}")

    async def get_validation_history(
        self, user: User, project: Optional[Project] = None, limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get validation history for user/project.

        Args:
            user: User to get history for
            project: Associated project (optional)
            limit: Maximum number of results

        Returns:
            List of validation history entries
        """
        try:
            history = await self.validation_repository.get_validation_history(
                user_id=user.id, project_id=project.id if project else None, limit=limit
            )

            return history

        except Exception as e:
            logger.error(f"Failed to get validation history: {e}")
            raise ApplicationError(f"Failed to get validation history: {str(e)}")

    async def get_service_statistics(self) -> Dict[str, Any]:
        """Get MCP-Engineering service statistics."""
        return {
            **self.stats,
            "timestamp": datetime.utcnow().isoformat(),
            "service": "mcp-engineering",
        }

    # Private methods for business logic

    def _validate_building_data(self, building_data: Dict[str, Any]) -> None:
        """Validate building data structure."""
        required_fields = ["area", "height", "type"]
        for field in required_fields:
            if field not in building_data:
                raise ValidationError(f"Missing required field: {field}")

        if building_data["area"] <= 0:
            raise ValidationError("Building area must be positive")

        if building_data["height"] <= 0:
            raise ValidationError("Building height must be positive")

    def _validate_validation_type(self, validation_type: str) -> None:
        """Validate validation type."""
        valid_types = [
            "structural",
            "electrical",
            "mechanical",
            "plumbing",
            "fire",
            "accessibility",
            "energy",
        ]

        if validation_type not in valid_types:
            raise ValidationError(f"Invalid validation type: {validation_type}")

    def _validate_report_type(self, report_type: str) -> None:
        """Validate report type."""
        valid_types = ["comprehensive", "summary", "technical"]

        if report_type not in valid_types:
            raise ValidationError(f"Invalid report type: {report_type}")

    def _validate_report_format(self, format: str) -> None:
        """Validate report format."""
        valid_formats = ["pdf", "html", "json"]

        if format not in valid_formats:
            raise ValidationError(f"Invalid report format: {format}")

    async def _perform_validation(
        self,
        building_data: Dict[str, Any],
        validation_type: str,
        include_suggestions: bool,
        confidence_threshold: float,
    ) -> Dict[str, Any]:
        """Perform the actual validation logic."""
        # TODO: Integrate with MCP-Engineering service
        # For now, return mock validation result

        issues = []
        suggestions = []

        # Mock validation logic
        if building_data["area"] > 10000 and building_data["type"] == "residential":
            issues.append(
                {
                    "code": "IBC 1004.1.1",
                    "severity": "warning",
                    "description": "Large residential building may require additional exits",
                    "resolution": "Consider adding additional exit routes",
                }
            )

        if include_suggestions:
            suggestions.append(
                {
                    "type": "optimization",
                    "description": "Consider adding more natural lighting",
                    "confidence": 0.85,
                }
            )

        return {
            "validation_result": "pass" if not issues else "warning",
            "issues": issues,
            "suggestions": suggestions,
            "confidence_score": 0.92,
            "timestamp": datetime.utcnow().isoformat(),
        }

    async def _perform_knowledge_search(
        self, query: str, code_standard: Optional[str], max_results: int
    ) -> Dict[str, Any]:
        """Perform knowledge base search."""
        # Use knowledge repository to search
        search_results = await self.knowledge_repository.search_knowledge_base(
            query, code_standard, max_results
        )

        # Convert to response format
        return {
            "results": [
                {
                    "code": result.code_reference,
                    "title": result.title,
                    "content": result.content,
                    "relevance_score": result.relevance_score,
                    "code_standard": result.code_standard,
                }
                for result in search_results
            ],
            "total_count": len(search_results),
            "query": query,
        }

    async def _perform_ml_validation(
        self,
        building_data: Dict[str, Any],
        validation_type: str,
        include_confidence: bool,
        model_version: Optional[str],
    ) -> Dict[str, Any]:
        """Perform ML-powered validation."""
        # TODO: Integrate with MCP-Engineering ML service
        # For now, return mock ML result

        return {
            "prediction": "low_risk",
            "confidence": 0.87,
            "features": [
                {"name": "building_area", "importance": 0.45},
                {"name": "occupancy_type", "importance": 0.32},
            ],
            "model_version": model_version or "v1.0.0",
        }

    async def _generate_compliance_report(
        self,
        building_data: Dict[str, Any],
        validation_results: List[Dict[str, Any]],
        report_type: str,
        format: str,
    ) -> Dict[str, Any]:
        """Generate compliance report."""
        # TODO: Integrate with MCP-Engineering report service
        # For now, return mock report result

        report_id = str(uuid4())

        return {
            "report_id": report_id,
            "download_url": f"/api/v1/mcp/reports/{report_id}/download",
            "report_type": report_type,
            "format": format,
            "generated_at": datetime.utcnow().isoformat(),
        }

    def _update_statistics(self, processing_time: float, success: bool) -> None:
        """Update service statistics."""
        self.stats["validations_performed"] += 1
        self.stats["total_processing_time"] += processing_time
        self.stats["average_response_time"] = (
            self.stats["total_processing_time"] / self.stats["validations_performed"]
        )

        if success:
            self.stats["success_rate"] = (
                self.stats["success_rate"] * (self.stats["validations_performed"] - 1)
                + 1
            ) / self.stats["validations_performed"]
        else:
            self.stats["success_rate"] = (
                self.stats["success_rate"] * (self.stats["validations_performed"] - 1)
            ) / self.stats["validations_performed"]

    async def _log_search_activity(
        self, user_id: str, query: str, result_count: int
    ) -> None:
        """Log search activity for analytics."""
        await self.activity_repository.log_search_activity(user_id, query, result_count)

    async def _log_ml_validation_activity(
        self, user_id: str, validation_type: str, confidence: float
    ) -> None:
        """Log ML validation activity for analytics."""
        await self.activity_repository.log_ml_validation_activity(
            user_id, validation_type, confidence
        )

    async def _log_report_generation_activity(
        self, user_id: str, report_type: str, format: str
    ) -> None:
        """Log report generation activity for analytics."""
        await self.activity_repository.log_report_generation_activity(
            user_id, report_type, format
        )
