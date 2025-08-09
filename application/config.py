"""
Custom Configuration System for Arxos

Custom configuration management implementation built specifically for Arxos
without external dependencies. Handles environment variables, settings,
and configuration validation.
"""

import os
import logging
from typing import Dict, Any, Optional, Union
from dataclasses import dataclass


@dataclass
class DatabaseConfig:
    """Database configuration"""
    host: str
    port: int
    database: str
    username: str
    password: str
    pool_size: int = 10
    max_overflow: int = 20


@dataclass
class ServiceConfig:
    """Service configuration"""
    host: str
    port: int
    debug: bool
    workers: int


@dataclass
class PDFAnalysisConfig:
    """PDF analysis configuration"""
    max_file_size: int
    timeout: int
    confidence_threshold: float
    supported_formats: list[str]
    processing_workers: int


@dataclass
class SecurityConfig:
    """Security configuration"""
    secret_key: str
    algorithm: str
    access_token_expire_minutes: int
    refresh_token_expire_days: int


class ConfigManager:
    """
    Custom Configuration Manager for Arxos

    Handles all configuration management including environment variables,
    settings validation, and configuration access. Built without external
    dependencies.
    """

    def __init__(self):
        """Initialize configuration manager"""
        self.logger = logging.getLogger(__name__)

        # Configuration cache
        self._config_cache: Dict[str, Any] = {}

        # Configuration validation rules
        self._validation_rules = {
            'required_env_vars': [
                'ARXOS_ENV',
                'GUS_SERVICE_URL',
                'DATABASE_URL'
            ],
            'optional_env_vars': [
                'PDF_MAX_FILE_SIZE',
                'PDF_TIMEOUT',
                'PDF_CONFIDENCE_THRESHOLD',
                'SECRET_KEY',
                'DEBUG_MODE'
            ]
        }

        self.logger.info("Custom Configuration Manager initialized")

    def get_config(self) -> Dict[str, Any]:
        """
        Get complete configuration

        Returns:
            Dict containing all configuration settings
        """
        if not self._config_cache:
            self._load_configuration()

        return self._config_cache.copy()

    def get_database_config(self) -> DatabaseConfig:
        """Get database configuration"""
        config = self.get_config()
        db_config = config.get('database', {})

        return DatabaseConfig(
            host=db_config.get('host', 'localhost'),
            port=db_config.get('port', 5432),
            database=db_config.get('database', 'arxos'),
            username=db_config.get('username', 'arxos'),
            password=db_config.get('password', ''),
            pool_size=db_config.get('pool_size', 10),
            max_overflow=db_config.get('max_overflow', 20)
        )

    def get_service_config(self) -> ServiceConfig:
        """Get service configuration"""
        config = self.get_config()
        service_config = config.get('service', {})

        return ServiceConfig(
            host=service_config.get('host', '0.0.0.0'),
            port=service_config.get('port', 8000),
            debug=service_config.get('debug', False),
            workers=service_config.get('workers', 1)
        )

    def get_pdf_analysis_config(self) -> PDFAnalysisConfig:
        """Get PDF analysis configuration"""
        config = self.get_config()
        pdf_config = config.get('pdf_analysis', {})

        return PDFAnalysisConfig(
            max_file_size=pdf_config.get('max_file_size', 50 * 1024 * 1024),  # 50MB
            timeout=pdf_config.get('timeout', 300),  # 5 minutes
            confidence_threshold=pdf_config.get('confidence_threshold', 0.7),
            supported_formats=pdf_config.get('supported_formats', ['pdf']),
            processing_workers=pdf_config.get('processing_workers', 4)
        )

    def get_security_config(self) -> SecurityConfig:
        """Get security configuration"""
        config = self.get_config()
        security_config = config.get('security', {})

        return SecurityConfig(
            secret_key=security_config.get('secret_key', 'default-secret-key'),
            algorithm=security_config.get('algorithm', 'HS256'),
            access_token_expire_minutes=security_config.get('access_token_expire_minutes', 30),
            refresh_token_expire_days=security_config.get('refresh_token_expire_days', 7)
        )

    def _load_configuration(self):
        """Load configuration from environment variables"""
        try:
            # Environment configuration
            self._config_cache['environment'] = self._load_environment_config()

            # Database configuration
            self._config_cache['database'] = self._load_database_config()

            # Service configuration
            self._config_cache['service'] = self._load_service_config()

            # PDF analysis configuration
            self._config_cache['pdf_analysis'] = self._load_pdf_analysis_config()

            # Security configuration
            self._config_cache['security'] = self._load_security_config()

            # GUS service configuration
            self._config_cache['gus_service'] = self._load_gus_service_config()

            # Feature flags
            self._config_cache['features'] = self._load_features_config()

            # Validation
            self._validate_configuration()

            self.logger.info("Configuration loaded successfully")

        except Exception as e:
            self.logger.error(f"Error loading configuration: {e}")
            raise ValueError(f"Configuration loading failed: {str(e)}")

    def _load_features_config(self) -> Dict[str, Any]:
        """Load feature flags configuration"""
        return {
            'use_unified_api': self._parse_bool(os.getenv('USE_UNIFIED_API', 'false'))
        }

    def _load_environment_config(self) -> Dict[str, Any]:
        """Load environment configuration"""
        return {
            'environment': os.getenv('ARXOS_ENV', 'development'),
            'debug': self._parse_bool(os.getenv('DEBUG_MODE', 'false')),
            'log_level': os.getenv('LOG_LEVEL', 'INFO'),
            'timezone': os.getenv('TIMEZONE', 'UTC')
        }

    def _load_database_config(self) -> Dict[str, Any]:
        """Load database configuration"""
        database_url = os.getenv('DATABASE_URL', '')

        if database_url:
            # Parse database URL
            return self._parse_database_url(database_url)
        else:
            # Individual database settings
            return {
                'host': os.getenv('DATABASE_HOST', 'localhost'),
                'port': int(os.getenv('DATABASE_PORT', '5432')),
                'database': os.getenv('DATABASE_NAME', 'arxos'),
                'username': os.getenv('DATABASE_USER', 'arxos'),
                'password': os.getenv('DATABASE_PASSWORD', ''),
                'pool_size': int(os.getenv('DATABASE_POOL_SIZE', '10')),
                'max_overflow': int(os.getenv('DATABASE_MAX_OVERFLOW', '20'))
            }

    def _load_service_config(self) -> Dict[str, Any]:
        """Load service configuration"""
        return {
            'host': os.getenv('SERVICE_HOST', '0.0.0.0'),
            'port': int(os.getenv('SERVICE_PORT', '8000')),
            'debug': self._parse_bool(os.getenv('DEBUG_MODE', 'false')),
            'workers': int(os.getenv('SERVICE_WORKERS', '1')),
            'reload': self._parse_bool(os.getenv('SERVICE_RELOAD', 'true'))
        }

    def _load_pdf_analysis_config(self) -> Dict[str, Any]:
        """Load PDF analysis configuration"""
        return {
            'max_file_size': int(os.getenv('PDF_MAX_FILE_SIZE', str(50 * 1024 * 1024))),  # 50MB
            'timeout': int(os.getenv('PDF_TIMEOUT', '300')),  # 5 minutes
            'confidence_threshold': float(os.getenv('PDF_CONFIDENCE_THRESHOLD', '0.7')),
            'supported_formats': os.getenv('PDF_SUPPORTED_FORMATS', 'pdf').split(','),
            'processing_workers': int(os.getenv('PDF_PROCESSING_WORKERS', '4')),
            'temp_directory': os.getenv('PDF_TEMP_DIRECTORY', '/tmp/arxos_pdf'),
            'cleanup_interval': int(os.getenv('PDF_CLEANUP_INTERVAL', '3600'))  # 1 hour
        }

    def _load_security_config(self) -> Dict[str, Any]:
        """Load security configuration"""
        return {
            'secret_key': os.getenv('SECRET_KEY', 'default-secret-key-change-in-production'),
            'algorithm': os.getenv('JWT_ALGORITHM', 'HS256'),
            'access_token_expire_minutes': int(os.getenv('ACCESS_TOKEN_EXPIRE_MINUTES', '30')),
            'refresh_token_expire_days': int(os.getenv('REFRESH_TOKEN_EXPIRE_DAYS', '7')),
            'password_min_length': int(os.getenv('PASSWORD_MIN_LENGTH', '8')),
            'max_login_attempts': int(os.getenv('MAX_LOGIN_ATTEMPTS', '5')),
            'lockout_duration': int(os.getenv('LOCKOUT_DURATION', '900'))  # 15 minutes
        }

    def _load_gus_service_config(self) -> Dict[str, Any]:
        """Load GUS service configuration"""
        return {
            'url': os.getenv('GUS_SERVICE_URL', 'http://localhost:8000'),
            'timeout': int(os.getenv('GUS_TIMEOUT', '300')),
            'retry_attempts': int(os.getenv('GUS_RETRY_ATTEMPTS', '3')),
            'retry_delay': int(os.getenv('GUS_RETRY_DELAY', '1')),
            'health_check_interval': int(os.getenv('GUS_HEALTH_CHECK_INTERVAL', '60'))
        }

    def _parse_database_url(self, database_url: str) -> Dict[str, Any]:
        """Parse database URL into components"""
        try:
            # Simple database URL parsing
            if database_url.startswith('postgresql://'):
                # Remove protocol
                url_without_protocol = database_url[13:]

                # Split into user:pass@host:port/database
                if '@' in url_without_protocol:
                    auth_part, rest = url_without_protocol.split('@', 1)
                    host_part, database = rest.split('/', 1)

                    # Parse authentication
                    if ':' in auth_part:
                        username, password = auth_part.split(':', 1)
                    else:
                        username, password = auth_part, ''

                    # Parse host and port
                    if ':' in host_part:
                        host, port = host_part.split(':', 1)
                        port = int(port)
                    else:
                        host, port = host_part, 5432

                    return {
                        'host': host,
                        'port': port,
                        'database': database,
                        'username': username,
                        'password': password,
                        'pool_size': 10,
                        'max_overflow': 20
                    }
                else:
                    # No authentication
                    host_part, database = url_without_protocol.split('/', 1)

                    if ':' in host_part:
                        host, port = host_part.split(':', 1)
                        port = int(port)
                    else:
                        host, port = host_part, 5432

                    return {
                        'host': host,
                        'port': port,
                        'database': database,
                        'username': '',
                        'password': '',
                        'pool_size': 10,
                        'max_overflow': 20
                    }
            else:
                raise ValueError(f"Unsupported database URL format: {database_url}")

        except Exception as e:
            self.logger.error(f"Error parsing database URL: {e}")
            raise ValueError(f"Invalid database URL: {database_url}")

    def _parse_bool(self, value: str) -> bool:
        """Parse boolean string value"""
        return value.lower() in ('true', '1', 'yes', 'on')

    def _validate_configuration(self):
        """Validate configuration settings"""
        errors = []

        # Check required environment variables
        for env_var in self._validation_rules['required_env_vars']:
            if not os.getenv(env_var):
                errors.append(f"Required environment variable not set: {env_var}")

        # Validate database configuration
        db_config = self._config_cache.get('database', {})
        if not db_config.get('host'):
            errors.append("Database host not configured")

        # Validate PDF analysis configuration
        pdf_config = self._config_cache.get('pdf_analysis', {})
        if pdf_config.get('max_file_size', 0) <= 0:
            errors.append("PDF max file size must be positive")

        if pdf_config.get('timeout', 0) <= 0:
            errors.append("PDF timeout must be positive")

        if not 0 <= pdf_config.get('confidence_threshold', 0) <= 1:
            errors.append("PDF confidence threshold must be between 0 and 1")

        # Validate security configuration
        security_config = self._config_cache.get('security', {})
        if security_config.get('secret_key') == 'default-secret-key-change-in-production':
            self.logger.warning("Using default secret key - change in production")

        # Report errors
        if errors:
            error_message = "Configuration validation failed:\n" + "\n".join(f"- {error}" for error in errors)
            self.logger.error(error_message)
            raise ValueError(error_message)

    def get_setting(self, key: str, default: Any = None) -> Any:
        """Get specific configuration setting"""
        config = self.get_config()

        # Support dot notation for nested keys
        keys = key.split('.')
        value = config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def set_setting(self, key: str, value: Any) -> bool:
        """Set configuration setting"""
        try:
            keys = key.split('.')
            config = self._config_cache

            # Navigate to the parent of the target key
            for k in keys[:-1]:
                if k not in config:
                    config[k] = {}
                config = config[k]

            # Set the value
            config[keys[-1]] = value

            self.logger.info(f"Configuration setting updated: {key}")
            return True

        except Exception as e:
            self.logger.error(f"Error setting configuration: {e}")
            return False

    def reload_configuration(self) -> bool:
        """Reload configuration from environment"""
        try:
            self._config_cache.clear()
            self._load_configuration()
            self.logger.info("Configuration reloaded successfully")
            return True
        except Exception as e:
            self.logger.error(f"Error reloading configuration: {e}")
            return False

    def get_config_summary(self) -> Dict[str, Any]:
        """Get configuration summary"""
        config = self.get_config()

        return {
            'environment': config.get('environment', {}).get('environment', 'unknown'),
            'debug_mode': config.get('service', {}).get('debug', False),
            'database_configured': bool(config.get('database', {}).get('host')),
            'pdf_analysis_configured': bool(config.get('pdf_analysis')),
            'security_configured': bool(config.get('security', {}).get('secret_key')),
            'gus_service_configured': bool(config.get('gus_service', {}).get('url')),
            'use_unified_api_enabled': config.get('features', {}).get('use_unified_api', False)
        }


# Global configuration instance
_config_manager = ConfigManager()


def get_config() -> Dict[str, Any]:
    """Get configuration dictionary"""
    return _config_manager.get_config()


def get_database_config() -> DatabaseConfig:
    """Get database configuration"""
    return _config_manager.get_database_config()


def get_service_config() -> ServiceConfig:
    """Get service configuration"""
    return _config_manager.get_service_config()


def get_pdf_analysis_config() -> PDFAnalysisConfig:
    """Get PDF analysis configuration"""
    return _config_manager.get_pdf_analysis_config()


def get_security_config() -> SecurityConfig:
    """Get security configuration"""
    return _config_manager.get_security_config()


def get_setting(key: str, default: Any = None) -> Any:
    """Get specific configuration setting"""
    return _config_manager.get_setting(key, default)


def set_setting(key: str, value: Any) -> bool:
    """Set configuration setting"""
    return _config_manager.set_setting(key, value)


def reload_config() -> bool:
    """Reload configuration"""
    return _config_manager.reload_configuration()
