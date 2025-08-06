"""
MCP-Engineering Configuration Module

This module provides configuration management for the MCP-Engineering service integration.
It reads configuration from a YAML file and provides type-safe access to settings.
"""

import os
import yaml
from typing import Dict, Any, Optional
from enum import Enum
from dataclasses import dataclass
from pathlib import Path


class Environment(Enum):
    """Environment enumeration."""

    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


@dataclass
class APIConfig:
    """API configuration settings."""

    base_url: str
    api_key: str
    timeout: int
    max_retries: int


@dataclass
class GRPCConfig:
    """gRPC configuration settings."""

    host: str
    port: int
    timeout: int
    max_reconnect_attempts: int


@dataclass
class SecurityConfig:
    """Security configuration settings."""

    api_key_encryption: bool
    ssl_verify: bool
    certificate_path: Optional[str]
    private_key_path: Optional[str]


@dataclass
class MonitoringConfig:
    """Monitoring configuration settings."""

    enabled: bool
    metrics_interval: int
    health_check_interval: int
    log_level: str


@dataclass
class CircuitBreakerConfig:
    """Circuit breaker configuration settings."""

    failure_threshold: int
    timeout: int
    max_retries: int
    retry_delay: float


@dataclass
class MCPEngineeringConfig:
    """Main MCP-Engineering configuration."""

    environment: Environment
    api_keys: Dict[str, str]
    service_endpoints: Dict[str, str]
    grpc_services: Dict[str, str]
    rate_limits: Dict[str, int]
    monitoring: MonitoringConfig
    security: SecurityConfig
    circuit_breaker: CircuitBreakerConfig
    http_client: Dict[str, Any]
    grpc_client: Dict[str, Any]
    caching: Dict[str, Any]
    logging: Dict[str, Any]
    performance: Dict[str, Any]
    error_handling: Dict[str, Any]
    metrics: Dict[str, Any]
    development: Dict[str, Any]
    staging: Dict[str, Any]
    production: Dict[str, Any]


class ConfigManager:
    """Configuration manager for MCP-Engineering settings."""

    def __init__(self):
        self.config = None
        self.config_file = None

    def _get_default_config_path(self) -> str:
        """Get the default configuration file path."""
        # Look for config file in the config directory
        config_dir = Path(__file__).parent
        config_file = config_dir / "mcp_engineering.yaml"

        if not config_file.exists():
            # Create a default config file
            self._create_default_config(config_file)

        return str(config_file)

    def _create_default_config(self, config_path: Path) -> None:
        """Create a default configuration file."""
        default_config = {
            "mcp_engineering": {
                "environment": "development",
                "api_keys": {
                    "building_validation": "${MCP_BUILDING_VALIDATION_API_KEY}",
                    "compliance_checking": "${MCP_COMPLIANCE_CHECKING_API_KEY}",
                    "ai_recommendations": "${MCP_AI_RECOMMENDATIONS_API_KEY}",
                    "knowledge_base": "${MCP_KNOWLEDGE_BASE_API_KEY}",
                    "ml_predictions": "${MCP_ML_PREDICTIONS_API_KEY}",
                },
                "service_endpoints": {
                    "building_validation": "https://api.mcp-engineering.com/v1/validation",
                    "compliance_checking": "https://api.mcp-engineering.com/v1/compliance",
                    "ai_recommendations": "https://api.mcp-engineering.com/v1/ai",
                    "knowledge_base": "https://api.mcp-engineering.com/v1/knowledge",
                    "ml_predictions": "https://api.mcp-engineering.com/v1/ml",
                },
                "grpc_services": {
                    "validation_streaming": "grpc://mcp-engineering-streaming:50051",
                    "real_time_updates": "grpc://mcp-engineering-realtime:50051",
                },
                "rate_limits": {"requests_per_minute": 100, "burst_limit": 20},
                "monitoring": {
                    "enabled": True,
                    "metrics_interval": 60,
                    "health_check_interval": 30,
                    "log_level": "INFO",
                },
                "security": {
                    "api_key_encryption": True,
                    "ssl_verify": True,
                    "certificate_path": None,
                    "private_key_path": None,
                },
                "circuit_breaker": {
                    "failure_threshold": 5,
                    "timeout": 60,
                    "max_retries": 3,
                    "retry_delay": 1.0,
                },
                "http_client": {
                    "timeout": 30,
                    "max_retries": 3,
                    "retry_delay": 1.0,
                    "keepalive_timeout": 30,
                },
                "grpc_client": {
                    "timeout": 30,
                    "max_reconnect_attempts": 5,
                    "reconnect_delay": 1.0,
                    "keepalive_time": 30,
                    "keepalive_timeout": 10,
                },
                "caching": {
                    "enabled": True,
                    "ttl": 3600,
                    "max_size": 1000,
                    "redis_host": "localhost",
                    "redis_port": 6379,
                    "redis_db": 0,
                },
                "logging": {
                    "level": "INFO",
                    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                    "file_enabled": False,
                    "file_path": "logs/mcp_engineering.log",
                    "max_file_size": 10485760,
                    "backup_count": 5,
                },
                "performance": {
                    "max_concurrent_requests": 100,
                    "connection_pool_size": 20,
                    "request_timeout": 30,
                    "response_timeout": 60,
                },
                "error_handling": {
                    "retry_on_failure": True,
                    "max_retry_attempts": 3,
                    "exponential_backoff": True,
                    "circuit_breaker_enabled": True,
                },
                "metrics": {
                    "prometheus_enabled": True,
                    "prometheus_port": 9090,
                    "custom_metrics_enabled": True,
                    "performance_tracking": True,
                },
                "development": {
                    "mock_services_enabled": True,
                    "mock_response_delay": 0.5,
                    "debug_mode": True,
                    "verbose_logging": True,
                },
                "staging": {
                    "mock_services_enabled": False,
                    "debug_mode": False,
                    "verbose_logging": False,
                },
                "production": {
                    "mock_services_enabled": False,
                    "debug_mode": False,
                    "verbose_logging": False,
                    "strict_ssl_verification": True,
                    "enhanced_security": True,
                },
            }
        }

        with open(config_path, "w") as f:
            yaml.dump(default_config, f, default_flow_style=False)

    def load_config(self, config_file: Optional[str] = None) -> MCPEngineeringConfig:
        """Load configuration from file."""
        if config_file is None:
            config_file = self._get_default_config_path()

        self.config_file = config_file

        try:
            with open(config_file, "r") as f:
                config_data = yaml.safe_load(f)

            mcp_config = config_data.get("mcp_engineering", {})

            # Create configuration objects
            environment = Environment(mcp_config.get("environment", "development"))

            monitoring = MonitoringConfig(
                enabled=mcp_config.get("monitoring", {}).get("enabled", True),
                metrics_interval=mcp_config.get("monitoring", {}).get(
                    "metrics_interval", 60
                ),
                health_check_interval=mcp_config.get("monitoring", {}).get(
                    "health_check_interval", 30
                ),
                log_level=mcp_config.get("monitoring", {}).get("log_level", "INFO"),
            )

            security = SecurityConfig(
                api_key_encryption=mcp_config.get("security", {}).get(
                    "api_key_encryption", True
                ),
                ssl_verify=mcp_config.get("security", {}).get("ssl_verify", True),
                certificate_path=mcp_config.get("security", {}).get("certificate_path"),
                private_key_path=mcp_config.get("security", {}).get("private_key_path"),
            )

            circuit_breaker = CircuitBreakerConfig(
                failure_threshold=mcp_config.get("circuit_breaker", {}).get(
                    "failure_threshold", 5
                ),
                timeout=mcp_config.get("circuit_breaker", {}).get("timeout", 60),
                max_retries=mcp_config.get("circuit_breaker", {}).get("max_retries", 3),
                retry_delay=mcp_config.get("circuit_breaker", {}).get(
                    "retry_delay", 1.0
                ),
            )

            self.config = MCPEngineeringConfig(
                environment=environment,
                api_keys=mcp_config.get("api_keys", {}),
                service_endpoints=mcp_config.get("service_endpoints", {}),
                grpc_services=mcp_config.get("grpc_services", {}),
                rate_limits=mcp_config.get("rate_limits", {}),
                monitoring=monitoring,
                security=security,
                circuit_breaker=circuit_breaker,
                http_client=mcp_config.get("http_client", {}),
                grpc_client=mcp_config.get("grpc_client", {}),
                caching=mcp_config.get("caching", {}),
                logging=mcp_config.get("logging", {}),
                performance=mcp_config.get("performance", {}),
                error_handling=mcp_config.get("error_handling", {}),
                metrics=mcp_config.get("metrics", {}),
                development=mcp_config.get("development", {}),
                staging=mcp_config.get("staging", {}),
                production=mcp_config.get("production", {}),
            )

            return self.config

        except Exception as e:
            raise Exception(f"Failed to load MCP-Engineering configuration: {e}")

    def get_config(self) -> MCPEngineeringConfig:
        """Get the current configuration."""
        if self.config is None:
            self.config = self.load_config()
        return self.config

    def get_config_summary(self) -> Dict[str, Any]:
        """Get configuration summary for testing."""
        config = self.get_config()
        return {
            "environment": config.environment.value,
            "api_keys_count": len(config.api_keys),
            "service_endpoints_count": len(config.service_endpoints),
            "grpc_services_count": len(config.grpc_services),
            "monitoring_enabled": config.monitoring.enabled,
            "security_ssl_verify": config.security.ssl_verify,
            "circuit_breaker_failure_threshold": config.circuit_breaker.failure_threshold,
        }


# Global configuration manager instance
_config_manager = ConfigManager()


def get_config() -> MCPEngineeringConfig:
    """Get the MCP-Engineering configuration instance."""
    return _config_manager.get_config()


def load_config(config_file: Optional[str] = None) -> MCPEngineeringConfig:
    """Load MCP-Engineering configuration from file."""
    return _config_manager.load_config(config_file)
