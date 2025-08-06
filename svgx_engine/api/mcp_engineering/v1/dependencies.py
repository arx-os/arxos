#!/usr/bin/env python3
"""
Dependencies for MCP-Engineering API

Dependency injection and service management for the MCP-Engineering integration API.

Author: Arxos Engineering Team
Date: 2024-12-19
Version: 1.0.0
"""

import logging
from typing import Optional
from functools import lru_cache

from svgx_engine.services.mcp_engineering.bridge.bridge_service import (
    MCPEngineeringBridge,
    BridgeConfig,
)

logger = logging.getLogger(__name__)


@lru_cache()
def get_bridge_config() -> BridgeConfig:
    """Get bridge service configuration."""
    return BridgeConfig(
        enable_caching=True,
        cache_ttl=3600,
        enable_metrics=True,
        enable_logging=True,
        timeout_seconds=30,
    )


@lru_cache()
def get_bridge_service() -> MCPEngineeringBridge:
    """Get MCP-Engineering bridge service instance."""
    try:
        config = get_bridge_config()
        bridge_service = MCPEngineeringBridge(config)
        logger.info("MCP-Engineering Bridge service initialized")
        return bridge_service
    except Exception as e:
        logger.error(f"Failed to initialize bridge service: {e}")
        raise


def get_validation_service():
    """Get validation service instance."""
    try:
        from svgx_engine.services.mcp_engineering.validation.validation_service import (
            EngineeringValidationService,
        )

        return EngineeringValidationService()
    except Exception as e:
        logger.error(f"Failed to initialize validation service: {e}")
        raise


def get_compliance_checker():
    """Get compliance checker instance."""
    try:
        from svgx_engine.services.mcp_engineering.compliance.compliance_checker import (
            CodeComplianceChecker,
        )

        return CodeComplianceChecker()
    except Exception as e:
        logger.error(f"Failed to initialize compliance checker: {e}")
        raise


def get_cross_system_analyzer():
    """Get cross-system analyzer instance."""
    try:
        from svgx_engine.services.mcp_engineering.analysis.cross_system_analyzer import (
            CrossSystemAnalyzer,
        )

        return CrossSystemAnalyzer()
    except Exception as e:
        logger.error(f"Failed to initialize cross-system analyzer: {e}")
        raise


def get_suggestion_engine():
    """Get suggestion engine instance."""
    try:
        from svgx_engine.services.mcp_engineering.suggestions.suggestion_engine import (
            EngineeringSuggestionEngine,
        )

        return EngineeringSuggestionEngine()
    except Exception as e:
        logger.error(f"Failed to initialize suggestion engine: {e}")
        raise


def validate_service_health(service_name: str, service_instance) -> bool:
    """Validate service health."""
    try:
        if hasattr(service_instance, "is_healthy"):
            return service_instance.is_healthy()
        else:
            # If no health check method, assume healthy
            return True
    except Exception as e:
        logger.error(f"Health check failed for {service_name}: {e}")
        return False


def get_service_health_status() -> dict:
    """Get comprehensive service health status."""
    try:
        bridge_service = get_bridge_service()
        validation_service = get_validation_service()
        compliance_checker = get_compliance_checker()
        cross_system_analyzer = get_cross_system_analyzer()
        suggestion_engine = get_suggestion_engine()

        health_status = {
            "bridge_service": validate_service_health("bridge_service", bridge_service),
            "validation_service": validate_service_health(
                "validation_service", validation_service
            ),
            "compliance_checker": validate_service_health(
                "compliance_checker", compliance_checker
            ),
            "cross_system_analyzer": validate_service_health(
                "cross_system_analyzer", cross_system_analyzer
            ),
            "suggestion_engine": validate_service_health(
                "suggestion_engine", suggestion_engine
            ),
        }

        overall_health = all(health_status.values())

        return {
            "overall_health": overall_health,
            "services": health_status,
            "timestamp": "2024-12-19T00:00:00Z",
        }

    except Exception as e:
        logger.error(f"Failed to get service health status: {e}")
        return {
            "overall_health": False,
            "services": {},
            "error": str(e),
            "timestamp": "2024-12-19T00:00:00Z",
        }
