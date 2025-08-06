#!/usr/bin/env python3
"""
Development Environment Setup Script

This script sets up the development environment with proper configuration,
logging, dependency injection, and validates all components are working
correctly.
"""

import os
import sys
import logging
from pathlib import Path
from typing import Dict, Any

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from application.logging_config import setup_logging, get_logger
from application.container import container
from application.config import load_config
from application.exceptions import ApplicationError, ConfigurationError


class DevelopmentEnvironmentSetup:
    """Setup and validate the development environment."""

    def __init__(self):
        """Initialize the development environment setup."""
        self.logger = get_logger("dev_setup")
        self.config = {}
        self.setup_complete = False

    def setup_logging(self) -> None:
        """Setup logging for development environment."""
        try:
            # Create logs directory
            logs_dir = project_root / "logs"
            logs_dir.mkdir(exist_ok=True)

            # Setup logging with development configuration
            setup_logging(
                environment="development",
                log_level="DEBUG",
                log_file=str(logs_dir / "arxos_dev.log"),
                enable_console=True,
            )

            self.logger.info("Logging setup completed successfully")

        except Exception as e:
            print(f"Failed to setup logging: {e}")
            raise

    def load_configuration(self) -> None:
        """Load application configuration."""
        try:
            # Load configuration from environment or default
            self.config = {
                "database": {
                    "host": os.getenv("DB_HOST", "localhost"),
                    "port": int(os.getenv("DB_PORT", "5432")),
                    "database": os.getenv("DB_NAME", "arxos_dev"),
                    "username": os.getenv("DB_USER", "arxos_user"),
                    "password": os.getenv("DB_PASSWORD", "arxos_password"),
                    "pool_size": int(os.getenv("DB_POOL_SIZE", "5")),
                    "max_overflow": int(os.getenv("DB_MAX_OVERFLOW", "10")),
                },
                "cache": {
                    "host": os.getenv("REDIS_HOST", "localhost"),
                    "port": int(os.getenv("REDIS_PORT", "6379")),
                    "db": int(os.getenv("REDIS_DB", "0")),
                    "password": os.getenv("REDIS_PASSWORD"),
                    "max_connections": int(os.getenv("REDIS_MAX_CONNECTIONS", "10")),
                },
                "message_queue": {
                    "host": os.getenv("MQ_HOST", "localhost"),
                    "port": int(os.getenv("MQ_PORT", "5672")),
                    "username": os.getenv("MQ_USERNAME"),
                    "password": os.getenv("MQ_PASSWORD"),
                },
                "logging": {
                    "level": os.getenv("LOG_LEVEL", "DEBUG"),
                    "file": str(project_root / "logs" / "arxos_dev.log"),
                },
            }

            self.logger.info("Configuration loaded successfully")

        except Exception as e:
            self.logger.error(f"Failed to load configuration: {e}")
            raise ConfigurationError(
                "config_loading", f"Failed to load configuration: {e}"
            )

    def initialize_container(self) -> None:
        """Initialize the dependency injection container."""
        try:
            # Initialize the application container
            container.initialize(self.config)

            self.logger.info("Dependency injection container initialized successfully")

        except Exception as e:
            self.logger.error(f"Failed to initialize container: {e}")
            raise ApplicationError(
                message="Failed to initialize dependency injection container",
                error_code="CONTAINER_INIT_ERROR",
                details={"original_error": str(e)},
            )

    def validate_database_connection(self) -> None:
        """Validate database connection."""
        try:
            # Get database session
            session = container.get_database_session()

            # Test connection
            with session.get_session() as db_session:
                # Simple query to test connection
                result = db_session.execute("SELECT 1")
                result.fetchone()

            self.logger.info("Database connection validated successfully")

        except Exception as e:
            self.logger.error(f"Database connection validation failed: {e}")
            raise ApplicationError(
                message="Database connection validation failed",
                error_code="DB_CONNECTION_ERROR",
                details={"original_error": str(e)},
            )

    def validate_cache_connection(self) -> None:
        """Validate cache connection."""
        try:
            # Get cache service
            cache_service = container.get_cache_service()

            # Test cache operations
            test_key = "dev_setup_test"
            test_value = "test_value"

            # Set and get a test value
            cache_service.set(test_key, test_value, ttl=60)
            retrieved_value = cache_service.get(test_key)

            if retrieved_value != test_value:
                raise ValueError("Cache test failed - retrieved value doesn't match")

            # Clean up test key
            cache_service.delete(test_key)

            self.logger.info("Cache connection validated successfully")

        except Exception as e:
            self.logger.warning(f"Cache connection validation failed: {e}")
            # Cache is optional, so we just log a warning

    def validate_repositories(self) -> None:
        """Validate all repositories are accessible."""
        try:
            # Test repository creation
            repositories = [
                ("Building", container.get_building_repository),
                ("Floor", container.get_floor_repository),
                ("Room", container.get_room_repository),
                ("Device", container.get_device_repository),
                ("User", container.get_user_repository),
                ("Project", container.get_project_repository),
            ]

            for repo_name, repo_factory in repositories:
                try:
                    repo = repo_factory()
                    self.logger.info(f"Repository {repo_name} validated successfully")
                except Exception as e:
                    self.logger.error(f"Repository {repo_name} validation failed: {e}")
                    raise

            self.logger.info("All repositories validated successfully")

        except Exception as e:
            self.logger.error(f"Repository validation failed: {e}")
            raise ApplicationError(
                message="Repository validation failed",
                error_code="REPOSITORY_VALIDATION_ERROR",
                details={"original_error": str(e)},
            )

    def validate_application_services(self) -> None:
        """Validate application services can be created."""
        try:
            from application.factory import (
                get_building_service,
                get_device_service,
                get_room_service,
                get_user_service,
                get_project_service,
            )

            # Test service creation
            services = [
                ("Building", get_building_service),
                ("Device", get_device_service),
                ("Room", get_room_service),
                ("User", get_user_service),
                ("Project", get_project_service),
            ]

            for service_name, service_factory in services:
                try:
                    service = service_factory()
                    self.logger.info(
                        f"Application service {service_name} created successfully"
                    )
                except Exception as e:
                    self.logger.error(
                        f"Application service {service_name} creation failed: {e}"
                    )
                    raise

            self.logger.info("All application services validated successfully")

        except Exception as e:
            self.logger.error(f"Application service validation failed: {e}")
            raise ApplicationError(
                message="Application service validation failed",
                error_code="SERVICE_VALIDATION_ERROR",
                details={"original_error": str(e)},
            )

    def validate_health_checks(self) -> None:
        """Validate health check service."""
        try:
            # Get health check service
            health_check = container.get_health_check()

            # Run health checks
            health_status = health_check.run_all_checks()

            if health_status.get("status") == "healthy":
                self.logger.info("Health checks passed successfully")
            else:
                self.logger.warning(f"Health checks returned: {health_status}")

        except Exception as e:
            self.logger.warning(f"Health check validation failed: {e}")
            # Health checks are optional in development

    def create_development_directories(self) -> None:
        """Create necessary directories for development."""
        try:
            directories = [
                project_root / "logs",
                project_root / "temp",
                project_root / "data",
                project_root / "reports",
            ]

            for directory in directories:
                directory.mkdir(exist_ok=True)
                self.logger.info(f"Created directory: {directory}")

            self.logger.info("Development directories created successfully")

        except Exception as e:
            self.logger.error(f"Failed to create development directories: {e}")
            raise

    def setup_environment_variables(self) -> None:
        """Setup default environment variables if not set."""
        try:
            env_vars = {
                "ARXOS_ENV": "development",
                "LOG_LEVEL": "DEBUG",
                "DB_HOST": "localhost",
                "DB_PORT": "5432",
                "DB_NAME": "arxos_dev",
                "REDIS_HOST": "localhost",
                "REDIS_PORT": "6379",
            }

            for var_name, default_value in env_vars.items():
                if not os.getenv(var_name):
                    os.environ[var_name] = default_value
                    self.logger.info(
                        f"Set environment variable: {var_name}={default_value}"
                    )

            self.logger.info("Environment variables setup completed")

        except Exception as e:
            self.logger.error(f"Failed to setup environment variables: {e}")
            raise

    def run_setup(self) -> None:
        """Run the complete development environment setup."""
        try:
            self.logger.info("Starting development environment setup...")

            # Setup steps
            self.setup_environment_variables()
            self.setup_logging()
            self.create_development_directories()
            self.load_configuration()
            self.initialize_container()

            # Validation steps
            self.validate_database_connection()
            self.validate_cache_connection()
            self.validate_repositories()
            self.validate_application_services()
            self.validate_health_checks()

            self.setup_complete = True
            self.logger.info("Development environment setup completed successfully!")

        except Exception as e:
            self.logger.error(f"Development environment setup failed: {e}")
            raise

    def print_summary(self) -> None:
        """Print a summary of the setup."""
        if self.setup_complete:
            print("\n" + "=" * 60)
            print("🎉 DEVELOPMENT ENVIRONMENT SETUP COMPLETE")
            print("=" * 60)
            print(f"📁 Project Root: {project_root}")
            print(f"📝 Logs: {project_root}/logs/arxos_dev.log")
            print(f"🔧 Environment: {os.getenv('ARXOS_ENV', 'development')}")
            print(f"📊 Log Level: {os.getenv('LOG_LEVEL', 'DEBUG')}")
            print("\n✅ All components validated and ready for development!")
            print("=" * 60)
        else:
            print("\n❌ Development environment setup failed!")
            print("Please check the logs for details.")


def main():
    """Main entry point for the development environment setup."""
    try:
        setup = DevelopmentEnvironmentSetup()
        setup.run_setup()
        setup.print_summary()

    except Exception as e:
        print(f"\n❌ Setup failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
