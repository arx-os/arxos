"""
MCP-Engineering HTTP Client

This module provides HTTP client functionality for communicating with external
MCP-Engineering services. It implements best practices for:
- Async HTTP communication
- Error handling and retry logic
- Rate limiting
- Circuit breaker pattern
- Request/response logging
- Type safety
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

import aiohttp
from aiohttp import ClientSession, ClientTimeout
from aiohttp.client_exceptions import ClientError, ClientResponseError

from domain.mcp_engineering_entities import (
    BuildingData,
    ValidationResult,
    ValidationType,
    ValidationStatus,
    ComplianceIssue,
    AIRecommendation,
    KnowledgeSearchResult,
    MLPrediction,
)


class ServiceEndpoint(Enum):
    """MCP-Engineering service endpoints."""

    BUILDING_VALIDATION = "building_validation"
    COMPLIANCE_CHECKING = "compliance_checking"
    AI_RECOMMENDATIONS = "ai_recommendations"
    KNOWLEDGE_BASE = "knowledge_base"
    ML_PREDICTIONS = "ml_predictions"


@dataclass
class APIConfig:
    """Configuration for MCP-Engineering API."""

    base_url: str
    api_key: str
    timeout: int = 30
    max_retries: int = 3
    retry_delay: float = 1.0
    rate_limit_per_minute: int = 100


@dataclass
class APIResponse:
    """Standardized API response."""

    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    status_code: Optional[int] = None
    response_time: Optional[float] = None


class CircuitBreaker:
    """Circuit breaker pattern implementation for fault tolerance."""

    def __init__(self, failure_threshold: int = 5, timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN

    def can_execute(self) -> bool:
        """Check if the circuit breaker allows execution."""
        if self.state == "CLOSED":
            return True
        elif self.state == "OPEN":
            if datetime.now() - self.last_failure_time > timedelta(
                seconds=self.timeout
            ):
                self.state = "HALF_OPEN"
                return True
            return False
        else:  # HALF_OPEN
            return True

    def on_success(self):
        """Handle successful execution."""
        self.failure_count = 0
        self.state = "CLOSED"

    def on_failure(self):
        """Handle failed execution."""
        self.failure_count += 1
        self.last_failure_time = datetime.now()

        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"


class RateLimiter:
    """Rate limiting implementation."""

    def __init__(self, requests_per_minute: int):
        self.requests_per_minute = requests_per_minute
        self.requests = []

    async def acquire(self) -> bool:
        """Acquire permission to make a request."""
        now = datetime.now()

        # Remove old requests
        self.requests = [
            req_time
            for req_time in self.requests
            if now - req_time < timedelta(minutes=1)
        ]

        if len(self.requests) < self.requests_per_minute:
            self.requests.append(now)
            return True

        return False


class MCPEngineeringHTTPClient:
    """
    HTTP client for MCP-Engineering external services.

    Implements best practices for:
    - Async HTTP communication
    - Error handling and retry logic
    - Rate limiting
    - Circuit breaker pattern
    - Request/response logging
    - Type safety
    """

    def __init__(self, config: APIConfig):
        """Initialize the HTTP client."""
        self.config = config
        self.session: Optional[ClientSession] = None
        self.circuit_breaker = CircuitBreaker()
        self.rate_limiter = RateLimiter(config.rate_limit_per_minute)
        self.logger = logging.getLogger(__name__)

        # Headers for all requests
        self.default_headers = {
            "Authorization": f"Bearer {config.api_key}",
            "Content-Type": "application/json",
            "User-Agent": "Arxos-MCP-Engineering-Client/1.0",
        }

    async def __aenter__(self):
        """Async context manager entry."""
        timeout = ClientTimeout(total=self.config.timeout)
        self.session = ClientSession(timeout=timeout, headers=self.default_headers)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        retry_count: int = 0,
    ) -> APIResponse:
        """
        Make an HTTP request with retry logic and error handling.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint
            data: Request data
            retry_count: Current retry attempt

        Returns:
            APIResponse with standardized response format
        """
        if not self.circuit_breaker.can_execute():
            return APIResponse(
                success=False, error="Circuit breaker is open", status_code=503
            )

        if not await self.rate_limiter.acquire():
            return APIResponse(
                success=False, error="Rate limit exceeded", status_code=429
            )

        if not self.session:
            raise RuntimeError("Client session not initialized")

        url = f"{self.config.base_url}/{endpoint}"
        start_time = datetime.now()

        try:
            self.logger.info(f"Making {method} request to {endpoint}")

            async with self.session.request(method, url, json=data) as response:
                response_time = (datetime.now() - start_time).total_seconds()

                if response.status < 400:
                    self.circuit_breaker.on_success()
                    response_data = await response.json()

                    self.logger.info(
                        f"Request successful: {method} {endpoint} "
                        f"({response.status}) in {response_time:.2f}s"
                    )

                    return APIResponse(
                        success=True,
                        data=response_data,
                        status_code=response.status,
                        response_time=response_time,
                    )
                else:
                    error_text = await response.text()
                    self.logger.error(
                        f"Request failed: {method} {endpoint} "
                        f"({response.status}): {error_text}"
                    )

                    # Retry logic for 5xx errors
                    if response.status >= 500 and retry_count < self.config.max_retries:
                        await asyncio.sleep(self.config.retry_delay * (2**retry_count))
                        return await self._make_request(
                            method, endpoint, data, retry_count + 1
                        )

                    self.circuit_breaker.on_failure()
                    return APIResponse(
                        success=False,
                        error=error_text,
                        status_code=response.status,
                        response_time=response_time,
                    )

        except ClientError as e:
            self.logger.error(f"HTTP client error: {e}")
            self.circuit_breaker.on_failure()

            # Retry logic for network errors
            if retry_count < self.config.max_retries:
                await asyncio.sleep(self.config.retry_delay * (2**retry_count))
                return await self._make_request(method, endpoint, data, retry_count + 1)

            return APIResponse(
                success=False,
                error=str(e),
                response_time=(datetime.now() - start_time).total_seconds(),
            )

        except Exception as e:
            self.logger.error(f"Unexpected error: {e}")
            self.circuit_breaker.on_failure()
            return APIResponse(
                success=False,
                error=str(e),
                response_time=(datetime.now() - start_time).total_seconds(),
            )

    async def validate_building(
        self, building_data: BuildingData, validation_type: ValidationType
    ) -> ValidationResult:
        """
        Validate building data with external MCP-Engineering service.

        Args:
            building_data: Building data to validate
            validation_type: Type of validation to perform

        Returns:
            ValidationResult with validation results
        """
        endpoint = ServiceEndpoint.BUILDING_VALIDATION.value

        request_data = {
            "building_data": {
                "area": building_data.area,
                "height": building_data.height,
                "building_type": building_data.building_type,
                "occupancy": building_data.occupancy,
                "floors": building_data.floors,
                "jurisdiction": building_data.jurisdiction,
                "address": building_data.address,
                "construction_type": building_data.construction_type,
                "year_built": building_data.year_built,
                "renovation_year": building_data.renovation_year,
            },
            "validation_type": validation_type.value,
        }

        response = await self._make_request("POST", endpoint, request_data)

        if not response.success:
            # Return a failed validation result
            return ValidationResult(
                building_data=building_data,
                validation_type=validation_type,
                status=ValidationStatus.ERROR,
                confidence_score=0.0,
                issues=[],
                suggestions=[],
                error_message=response.error,
            )

        # Parse successful response
        data = response.data
        return ValidationResult(
            building_data=building_data,
            validation_type=validation_type,
            status=ValidationStatus(data.get("status", "error")),
            confidence_score=data.get("confidence_score", 0.0),
            issues=[
                ComplianceIssue(
                    code_reference=issue.get("code_reference"),
                    severity=issue.get("severity"),
                    description=issue.get("description"),
                    resolution=issue.get("resolution"),
                )
                for issue in data.get("issues", [])
            ],
            suggestions=[
                AIRecommendation(
                    type=rec.get("type"),
                    description=rec.get("description"),
                    confidence=rec.get("confidence"),
                    impact_score=rec.get("impact_score"),
                )
                for rec in data.get("suggestions", [])
            ],
        )

    async def search_knowledge_base(
        self, query: str, limit: int = 10
    ) -> List[KnowledgeSearchResult]:
        """
        Search the knowledge base for relevant information.

        Args:
            query: Search query
            limit: Maximum number of results

        Returns:
            List of KnowledgeResult objects
        """
        endpoint = ServiceEndpoint.KNOWLEDGE_BASE.value

        request_data = {"query": query, "limit": limit}

        response = await self._make_request("POST", endpoint, request_data)

        if not response.success:
            self.logger.error(f"Knowledge base search failed: {response.error}")
            return []

        # Parse successful response
        data = response.data
        return [
            KnowledgeResult(
                code_reference=result.get("code_reference"),
                title=result.get("title"),
                content=result.get("content"),
                code_standard=result.get("code_standard"),
                relevance_score=result.get("relevance_score", 0.0),
                section_number=result.get("section_number"),
                subsection=result.get("subsection"),
                jurisdiction=result.get("jurisdiction"),
                effective_date=result.get("effective_date"),
            )
            for result in data.get("results", [])
        ]

    async def get_ai_recommendations(
        self, building_data: BuildingData
    ) -> List[AIRecommendation]:
        """
        Get AI-powered recommendations for building improvements.

        Args:
            building_data: Building data to analyze

        Returns:
            List of AIRecommendation objects
        """
        endpoint = ServiceEndpoint.AI_RECOMMENDATIONS.value

        request_data = {
            "building_data": {
                "area": building_data.area,
                "height": building_data.height,
                "building_type": building_data.building_type,
                "occupancy": building_data.occupancy,
                "floors": building_data.floors,
                "jurisdiction": building_data.jurisdiction,
            }
        }

        response = await self._make_request("POST", endpoint, request_data)

        if not response.success:
            self.logger.error(f"AI recommendations failed: {response.error}")
            return []

        # Parse successful response
        data = response.data
        return [
            AIRecommendation(
                type=rec.get("type"),
                description=rec.get("description"),
                confidence=rec.get("confidence", 0.0),
                impact_score=rec.get("impact_score", 0.0),
                implementation_cost=rec.get("implementation_cost"),
                estimated_savings=rec.get("estimated_savings"),
                affected_systems=rec.get("affected_systems"),
            )
            for rec in data.get("recommendations", [])
        ]

    async def get_ml_predictions(
        self, building_data: BuildingData
    ) -> List[MLPrediction]:
        """
        Get ML predictions for building performance and compliance.

        Args:
            building_data: Building data to analyze

        Returns:
            List of MLPrediction objects
        """
        endpoint = ServiceEndpoint.ML_PREDICTIONS.value

        request_data = {
            "building_data": {
                "area": building_data.area,
                "height": building_data.height,
                "building_type": building_data.building_type,
                "occupancy": building_data.occupancy,
                "floors": building_data.floors,
                "jurisdiction": building_data.jurisdiction,
            }
        }

        response = await self._make_request("POST", endpoint, request_data)

        if not response.success:
            self.logger.error(f"ML predictions failed: {response.error}")
            return []

        # Parse successful response
        data = response.data
        return [
            MLPrediction(
                prediction_type=pred.get("prediction_type"),
                prediction_value=pred.get("prediction_value"),
                confidence=pred.get("confidence", 0.0),
                model_version=pred.get("model_version"),
                model_name=pred.get("model_name"),
                features=pred.get("features"),
                processing_time=pred.get("processing_time", 0.0),
            )
            for pred in data.get("predictions", [])
        ]

    async def health_check(self) -> bool:
        """
        Check the health of the MCP-Engineering service.

        Returns:
            True if service is healthy, False otherwise
        """
        response = await self._make_request("GET", "health")
        return response.success and response.status_code == 200

    def get_metrics(self) -> Dict[str, Any]:
        """
        Get client metrics for monitoring.

        Returns:
            Dictionary with client metrics
        """
        return {
            "circuit_breaker_state": self.circuit_breaker.state,
            "failure_count": self.circuit_breaker.failure_count,
            "rate_limit_remaining": (
                self.config.rate_limit_per_minute - len(self.rate_limiter.requests)
            ),
            "last_failure_time": (
                self.circuit_breaker.last_failure_time.isoformat()
                if self.circuit_breaker.last_failure_time
                else None
            ),
        }
