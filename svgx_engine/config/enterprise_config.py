"""
Enterprise-grade configuration system for SVGX Engine.

This module provides comprehensive configuration management following enterprise
best practices including validation, security, monitoring, and compliance.
"""

import os
import json
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass, field
from enum import Enum
import logging
from datetime import datetime, timedelta
import hashlib
import secrets

from pydantic import BaseModel, Field, validator
from structlog import get_logger

logger = get_logger(__name__)


class EnvironmentType(Enum):
    """Environment types for configuration"""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TESTING = "testing"


class SecurityLevel(Enum):
    """Security levels for configuration"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ComplianceFramework(Enum):
    """Compliance frameworks"""
    SOC2 = "soc2"
    ISO27001 = "iso27001"
    GDPR = "gdpr"
    HIPAA = "hipaa"
    PCI_DSS = "pci_dss"


@dataclass
class DatabaseConfig:
    """Database configuration with enterprise security"""
    host: str = "localhost"
    port: int = 5432
    database: str = "svgx_engine"
    username: str = "svgx_user"
    password: str = field(default_factory=lambda: secrets.token_urlsafe(32))
    ssl_mode: str = "require"
    max_connections: int = 20
    connection_timeout: int = 30
    pool_timeout: int = 30
    pool_recycle: int = 3600

    def __post_init__(self):
        """Validate database configuration"""
        if not self.host:
            raise ValueError("Database host is required")
        if not 1 <= self.port <= 65535:
            raise ValueError("Database port must be between 1 and 65535")
        if not self.database:
            raise ValueError("Database name is required")
        if not self.username:
            raise ValueError("Database username is required")


@dataclass
class SecurityConfig:
    """Security configuration with enterprise standards"""
    encryption_key: str = field(default_factory=lambda: secrets.token_urlsafe(64))
    jwt_secret: str = field(default_factory=lambda: secrets.token_urlsafe(64))
    session_timeout: int = 3600  # 1 hour
    max_login_attempts: int = 5
    password_min_length: int = 12
    require_special_chars: bool = True
    require_numbers: bool = True
    require_uppercase: bool = True
    require_lowercase: bool = True
    password_history_count: int = 5
    mfa_required: bool = True
    audit_logging: bool = True
    data_encryption_at_rest: bool = True
    data_encryption_in_transit: bool = True

    def __post_init__(self):
        """Validate security configuration"""
        if len(self.encryption_key) < 32:
            raise ValueError("Encryption key must be at least 32 characters")
        if len(self.jwt_secret) < 32:
            raise ValueError("JWT secret must be at least 32 characters")
        if self.session_timeout < 300:  # 5 minutes minimum
            raise ValueError("Session timeout must be at least 5 minutes")
        if self.max_login_attempts < 1:
            raise ValueError("Max login attempts must be at least 1")


@dataclass
class PerformanceConfig:
    """Performance configuration with monitoring"""
    max_concurrent_operations: int = 100
    operation_timeout: int = 300  # 5 minutes
    cache_size: int = 1000
    cache_ttl: int = 3600  # 1 hour
    memory_limit_mb: int = 2048
    cpu_limit_percent: int = 80
    enable_profiling: bool = True
    enable_metrics: bool = True
    metrics_interval: int = 60  # 1 minute
    log_performance: bool = True

    def __post_init__(self):
        """Validate performance configuration"""
        if self.max_concurrent_operations < 1:
            raise ValueError("Max concurrent operations must be at least 1")
        if self.operation_timeout < 30:
            raise ValueError("Operation timeout must be at least 30 seconds")
        if self.cache_size < 100:
            raise ValueError("Cache size must be at least 100")
        if self.memory_limit_mb < 512:
            raise ValueError("Memory limit must be at least 512MB")


@dataclass
class MonitoringConfig:
    """Monitoring and observability configuration"""
    enable_logging: bool = True
    log_level: str = "INFO"
    log_format: str = "json"
    enable_metrics: bool = True
    metrics_endpoint: str = "/metrics"
    enable_tracing: bool = True
    tracing_sampler_rate: float = 0.1
    enable_health_checks: bool = True
    health_check_interval: int = 30
    enable_alerting: bool = True
    alert_webhook_url: Optional[str] = None
    enable_dashboard: bool = True
    dashboard_port: int = 8080

    def __post_init__(self):
        """Validate monitoring configuration"""
        valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if self.log_level not in valid_log_levels:
            raise ValueError(f"Log level must be one of {valid_log_levels}")
        if not 0.0 <= self.tracing_sampler_rate <= 1.0:
            raise ValueError("Tracing sampler rate must be between 0.0 and 1.0")


@dataclass
class ComplianceConfig:
    """Compliance and audit configuration"""
    frameworks: List[ComplianceFramework] = field(default_factory=list)
    audit_logging: bool = True
    audit_retention_days: int = 2555  # 7 years
    data_retention_days: int = 1095  # 3 years
    enable_data_anonymization: bool = True
    enable_encryption: bool = True
    enable_backup: bool = True
    backup_interval_hours: int = 24
    enable_disaster_recovery: bool = True
    dr_recovery_time_objective: int = 4  # hours
    dr_recovery_point_objective: int = 1  # hour

    def __post_init__(self):
        """Validate compliance configuration"""
        if self.audit_retention_days < 365:
            raise ValueError("Audit retention must be at least 1 year")
        if self.data_retention_days < 90:
            raise ValueError("Data retention must be at least 90 days")
        if self.backup_interval_hours < 1:
            raise ValueError("Backup interval must be at least 1 hour")


class SVGXEnterpriseConfig(BaseModel):
    """
    Enterprise-grade configuration for SVGX Engine.

    This configuration follows enterprise best practices including:
    - Comprehensive validation
    - Security by design
    - Performance monitoring
    - Compliance frameworks
    - Audit logging
    """

    # Basic configuration
    environment: EnvironmentType = EnvironmentType.DEVELOPMENT
    security_level: SecurityLevel = SecurityLevel.HIGH
    version: str = "1.0.0"
    debug: bool = False

    # Component configurations
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    security: SecurityConfig = Field(default_factory=SecurityConfig)
    performance: PerformanceConfig = Field(default_factory=PerformanceConfig)
    monitoring: MonitoringConfig = Field(default_factory=MonitoringConfig)
    compliance: ComplianceConfig = Field(default_factory=ComplianceConfig)

    # Service-specific configurations
    svgx_services: Dict[str, Any] = Field(default_factory=dict)
    api_config: Dict[str, Any] = Field(default_factory=dict)
    cache_config: Dict[str, Any] = Field(default_factory=dict)

    # Validation
    @validator('environment')
    def validate_environment(cls, v):
        """Validate environment configuration"""
        if v == EnvironmentType.PRODUCTION:
            # security_level is a field on the instance; cannot access via cls here
            pass
        return v

    @validator('svgx_services')
    def validate_svgx_services(cls, v):
        """Validate SVGX service configurations"""
        required_services = [
            'access_control', 'security', 'telemetry', 'performance',
            'bim_assembly', 'symbol_recognition', 'export_integration'
        ]

        for service in required_services:
            if service not in v:
                v[service] = {}

        return v

    class Config:
        """Pydantic configuration"""
        validate_assignment = True
        extra = "forbid"
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            EnvironmentType: lambda v: v.value,
            SecurityLevel: lambda v: v.value,
            ComplianceFramework: lambda v: v.value,
        }


class EnterpriseConfigManager:
    """
    Enterprise-grade configuration manager for SVGX Engine.

    This class provides comprehensive configuration management with:
    - Multiple configuration sources (file, environment, secrets)
    - Validation and security checks
    - Hot reloading capabilities
    - Audit logging
    - Compliance monitoring
    """

    def __init__(self, config_path: Optional[str] = None):
        self.logger = logger
        self.config_path = config_path or self._get_default_config_path()
        self.config: Optional[SVGXEnterpriseConfig] = None
        self.config_hash: Optional[str] = None
        self.last_loaded: Optional[datetime] = None
        self.validation_errors: List[str] = []

        # Load initial configuration
        self.load_configuration()

    def _get_default_config_path(self) -> str:
        """Get default configuration path"""
        return str(Path(__file__).parent / "enterprise_config.yaml")

    def load_configuration(self) -> SVGXEnterpriseConfig:
        """
        Load configuration from multiple sources with enterprise validation.

        Returns:
            SVGXEnterpriseConfig: Loaded and validated configuration

        Raises:
            ValueError: If configuration validation fails
        """
        self.logger.info("Loading enterprise configuration")

        # Load from file import file
        file_config = self._load_from_file()

        # Load from environment import environment
        env_config = self._load_from_environment()

        # Load from secrets import secrets
        secrets_config = self._load_from_secrets()

        # Merge configurations (secrets > environment > file)
        merged_config = self._merge_configurations(file_config, env_config, secrets_config)

        # Validate configuration
        try:
            self.config = SVGXEnterpriseConfig(**merged_config)
            self._validate_enterprise_requirements()

            # Calculate configuration hash for change detection
            self.config_hash = self._calculate_config_hash()
            self.last_loaded = datetime.now()

            self.logger.info("Enterprise configuration loaded successfully")
            return self.config

        except Exception as e:
            self.logger.error(f"Configuration validation failed: {str(e)}")
            self.validation_errors.append(str(e))
            raise ValueError(f"Configuration validation failed: {str(e)}")

    def _load_from_file(self) -> Dict[str, Any]:
        """Load configuration from file"""
        if not Path(self.config_path).exists():
            self.logger.warning(f"Configuration file not found: {self.config_path}")
            return {}

        try:
            with open(self.config_path, 'r') as f:
                if self.config_path.endswith('.yaml') or self.config_path.endswith('.yml'):
                    return yaml.safe_load(f)
                else:
                    return json.load(f)
        except Exception as e:
            self.logger.error(f"Failed to load configuration file: {str(e)}")
            return {}

    def _load_from_environment(self) -> Dict[str, Any]:
        """Load configuration from environment variables"""
        config = {}

        # Map environment variables to configuration
        env_mapping = {
            'SVGX_ENVIRONMENT': 'environment',
            'SVGX_SECURITY_LEVEL': 'security_level',
            'SVGX_DEBUG': 'debug',
            'SVGX_DB_HOST': 'database.host',
            'SVGX_DB_PORT': 'database.port',
            'SVGX_DB_NAME': 'database.database',
            'SVGX_DB_USER': 'database.username',
            'SVGX_DB_PASSWORD': 'database.password',
            'SVGX_ENCRYPTION_KEY': 'security.encryption_key',
            'SVGX_JWT_SECRET': 'security.jwt_secret',
            'SVGX_SESSION_TIMEOUT': 'security.session_timeout',
            'SVGX_MAX_CONCURRENT_OPS': 'performance.max_concurrent_operations',
            'SVGX_CACHE_SIZE': 'performance.cache_size',
            'SVGX_LOG_LEVEL': 'monitoring.log_level',
            'SVGX_METRICS_ENABLED': 'monitoring.enable_metrics',
        }

        for env_var, config_path in env_mapping.items():
            value = os.getenv(env_var)
            if value is not None:
                self._set_nested_config(config, config_path, value)

        return config

    def _load_from_secrets(self) -> Dict[str, Any]:
        """Load configuration from secrets management"""
        config = {}

        # In a real enterprise environment, this would integrate with:
        # - AWS Secrets Manager
        # - Azure Key Vault
        # - HashiCorp Vault
        # - Kubernetes Secrets

        # For now, we'll use environment variables with SECRET_ prefix'
        secret_mapping = {
            'SECRET_SVGX_ENCRYPTION_KEY': 'security.encryption_key',
            'SECRET_SVGX_JWT_SECRET': 'security.jwt_secret',
            'SECRET_SVGX_DB_PASSWORD': 'database.password',
        }

        for env_var, config_path in secret_mapping.items():
            value = os.getenv(env_var)
            if value is not None:
                self._set_nested_config(config, config_path, value)

        return config

    def _set_nested_config(self, config: Dict[str, Any], path: str, value: Any):
        """Set nested configuration value"""
        keys = path.split('.')
        current = config

        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]

        # Convert value based on expected type
        if 'port' in path or 'timeout' in path or 'size' in path:
            current[keys[-1]] = int(value)
        elif 'debug' in path or 'enabled' in path:
            current[keys[-1]] = value.lower() in ('true', '1', 'yes')
        else:
            current[keys[-1]] = value

    def _merge_configurations(self, *configs: Dict[str, Any]) -> Dict[str, Any]:
        """Merge multiple configuration dictionaries"""
        merged = {}

        for config in configs:
            self._deep_merge(merged, config)

        return merged

    def _deep_merge(self, target: Dict[str, Any], source: Dict[str, Any]):
        """Deep merge two dictionaries"""
        for key, value in source.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                self._deep_merge(target[key], value)
            else:
                target[key] = value

    def _validate_enterprise_requirements(self):
        """Validate enterprise-specific requirements"""
        if not self.config:
            return

        # Security requirements
        if self.config.environment == EnvironmentType.PRODUCTION:
            if self.config.security_level in [SecurityLevel.LOW, SecurityLevel.MEDIUM]:
                raise ValueError("Production environment requires HIGH or CRITICAL security level")

            if not self.config.security.mfa_required:
                raise ValueError("Production environment requires MFA")

            if not self.config.security.audit_logging:
                raise ValueError("Production environment requires audit logging")

        # Performance requirements
        if self.config.performance.max_concurrent_operations < 10:
            raise ValueError("Minimum concurrent operations is 10")

        # Compliance requirements
        if self.config.compliance.frameworks:
            if ComplianceFramework.SOC2 in self.config.compliance.frameworks:
                if not self.config.compliance.audit_logging:
                    raise ValueError("SOC2 compliance requires audit logging")
                if not self.config.compliance.enable_encryption:
                    raise ValueError("SOC2 compliance requires encryption")

    def _calculate_config_hash(self) -> str:
        """Calculate hash of current configuration for change detection"""
        if not self.config:
            return ""

        config_json = self.config.json()
        return hashlib.sha256(config_json.encode()).hexdigest()

    def get_config(self) -> SVGXEnterpriseConfig:
        """Get current configuration"""
        if not self.config:
            self.load_configuration()
        return self.config

    def reload_configuration(self) -> bool:
        """Reload configuration if changed"""
        if not self.config:
            self.load_configuration()
            return True

        # Check if configuration file has changed
        if Path(self.config_path).exists():
            current_hash = self._calculate_config_hash()
            if current_hash != self.config_hash:
                self.logger.info("Configuration changed, reloading...")
                self.load_configuration()
                return True

        return False

    def validate_configuration(self) -> List[str]:
        """Validate current configuration and return errors"""
        try:
            self.load_configuration()
            return []
        except Exception as e:
            return [str(e)]

    def get_configuration_summary(self) -> Dict[str, Any]:
        """Get configuration summary for monitoring"""
        if not self.config:
            return {}

        return {
            "environment": self.config.environment.value,
            "security_level": self.config.security_level.value,
            "version": self.config.version,
            "debug": self.config.debug,
            "last_loaded": self.last_loaded.isoformat() if self.last_loaded else None,
            "validation_errors": self.validation_errors,
            "compliance_frameworks": [f.value for f in self.config.compliance.frameworks],
            "monitoring_enabled": self.config.monitoring.enable_logging,
            "audit_logging": self.config.compliance.audit_logging,
            "encryption_enabled": self.config.compliance.enable_encryption,
        }


# Global configuration instance
_config_manager: Optional[EnterpriseConfigManager] = None


def get_enterprise_config() -> SVGXEnterpriseConfig:
    """Get enterprise configuration instance"""
    global _config_manager

    if _config_manager is None:
        _config_manager = EnterpriseConfigManager()

    return _config_manager.get_config()


def reload_enterprise_config() -> bool:
    """Reload enterprise configuration"""
    global _config_manager

    if _config_manager is None:
        _config_manager = EnterpriseConfigManager()

    return _config_manager.reload_configuration()


def validate_enterprise_config() -> List[str]:
    """Validate enterprise configuration"""
    global _config_manager

    if _config_manager is None:
        _config_manager = EnterpriseConfigManager()

    return _config_manager.validate_configuration()


def get_configuration_summary() -> Dict[str, Any]:
    """Get configuration summary"""
    global _config_manager

    if _config_manager is None:
        _config_manager = EnterpriseConfigManager()

    return _config_manager.get_configuration_summary()
