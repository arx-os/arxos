"""
Configuration Manager - Centralized configuration management
Handles environment variables, config files, and service settings
"""

import logging
import os
from typing import Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class ConfigManager:
    """
    Centralized configuration management for the AI service
    Handles environment variables, config files, and defaults
    """
    
    def __init__(self):
        self.config = {}
        self.load_config()
    
    def load_config(self):
        """Load configuration from environment and defaults"""
        # Service configuration
        self.config['service'] = {
            'name': os.getenv('SERVICE_NAME', 'Arxos AI Service'),
            'version': os.getenv('SERVICE_VERSION', '1.0.0'),
            'debug': os.getenv('DEBUG', 'false').lower() == 'true',
            'log_level': os.getenv('LOG_LEVEL', 'INFO')
        }
        
        # Server configuration
        self.config['server'] = {
            'host': os.getenv('HOST', '0.0.0.0'),
            'port': int(os.getenv('PORT', '8000')),
            'workers': int(os.getenv('WORKERS', '1')),
            'reload': os.getenv('RELOAD', 'true').lower() == 'true'
        }
        
        # Database configuration
        self.config['database'] = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': int(os.getenv('DB_PORT', '5432')),
            'name': os.getenv('DB_NAME', 'arxos'),
            'user': os.getenv('DB_USER', 'arxos'),
            'password': os.getenv('DB_PASSWORD', ''),
            'ssl_mode': os.getenv('DB_SSL_MODE', 'prefer')
        }
        
        # AI service configuration
        self.config['ai_service'] = {
            'max_file_size': int(os.getenv('MAX_FILE_SIZE_MB', '100')) * 1024 * 1024,
            'processing_timeout': int(os.getenv('PROCESSING_TIMEOUT_SEC', '300')),
            'memory_limit_mb': int(os.getenv('MEMORY_LIMIT_MB', '500')),
            'enable_caching': os.getenv('ENABLE_CACHING', 'true').lower() == 'true'
        }
        
        # Field worker assistance configuration
        self.config['field_assistance'] = {
            'validation_timeout_ms': int(os.getenv('VALIDATION_TIMEOUT_MS', '100')),
            'suggestion_timeout_ms': int(os.getenv('SUGGESTION_TIMEOUT_MS', '200')),
            'quality_scoring_timeout_ms': int(os.getenv('QUALITY_TIMEOUT_MS', '500')),
            'max_suggestions': int(os.getenv('MAX_SUGGESTIONS', '5'))
        }
        
        # Ingestion configuration
        self.config['ingestion'] = {
            'supported_formats': ['pdf', 'ifc', 'dwg', 'heic', 'jpg', 'jpeg', 'png'],
            'temp_directory': os.getenv('TEMP_DIR', '/tmp'),
            'max_concurrent_parsers': int(os.getenv('MAX_CONCURRENT_PARSERS', '3')),
            'parser_timeout_sec': int(os.getenv('PARSER_TIMEOUT_SEC', '60'))
        }
        
        logger.info("Configuration loaded successfully")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key"""
        keys = key.split('.')
        value = self.config
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def get_service_config(self) -> Dict[str, Any]:
        """Get service configuration"""
        return self.config.get('service', {})
    
    def get_server_config(self) -> Dict[str, Any]:
        """Get server configuration"""
        return self.config.get('server', {})
    
    def get_database_config(self) -> Dict[str, Any]:
        """Get database configuration"""
        return self.config.get('database', {})
    
    def get_ai_service_config(self) -> Dict[str, Any]:
        """Get AI service configuration"""
        return self.config.get('ai_service', {})
    
    def get_field_assistance_config(self) -> Dict[str, Any]:
        """Get field assistance configuration"""
        return self.config.get('field_assistance', {})
    
    def get_ingestion_config(self) -> Dict[str, Any]:
        """Get ingestion configuration"""
        return self.config.get('ingestion', {})
    
    def is_debug_mode(self) -> bool:
        """Check if debug mode is enabled"""
        return self.config.get('service', {}).get('debug', False)
    
    def get_log_level(self) -> str:
        """Get configured log level"""
        return self.config.get('service', {}).get('log_level', 'INFO')
