"""
Database Configuration

This module contains the database configuration class that manages
database connection settings and environment-specific configurations.
"""

from dataclasses import dataclass
from typing import Optional
import os


@dataclass
class DatabaseConfig:
    """Database configuration settings."""

    # Connection settings
    host: str = "localhost"
    port: int = 5432
    database: str = "arxos"
    username: str = "arxos_user"
    password: str = ""

    # Connection pool settings
    pool_size: int = 10
    max_overflow: int = 20
    pool_timeout: int = 30
    pool_recycle: int = 3600

    # SSL settings
    ssl_mode: str = "prefer"
    ssl_cert: Optional[str] = None
    ssl_key: Optional[str] = None
    ssl_ca: Optional[str] = None

    # Performance settings
    echo: bool = False  # SQL logging
    echo_pool: bool = False  # Connection pool logging

    @classmethod
    def from_environment(cls) -> 'DatabaseConfig':
        """Create configuration from environment variables."""
        return cls(
            host=os.getenv('DB_HOST', 'localhost'),
            port=int(os.getenv('DB_PORT', '5432')),
            database=os.getenv('DB_NAME', 'arxos'),
            username=os.getenv('DB_USER', 'arxos_user'),
            password=os.getenv('DB_PASSWORD', ''),
            pool_size=int(os.getenv('DB_POOL_SIZE', '10')),
            max_overflow=int(os.getenv('DB_MAX_OVERFLOW', '20')),
            pool_timeout=int(os.getenv('DB_POOL_TIMEOUT', '30')),
            pool_recycle=int(os.getenv('DB_POOL_RECYCLE', '3600')),
            ssl_mode=os.getenv('DB_SSL_MODE', 'prefer'),
            echo=os.getenv('DB_ECHO', 'false').lower() == 'true',
            echo_pool=os.getenv('DB_ECHO_POOL', 'false').lower() == 'true'
        )

    @property
    def connection_string(self) -> str:
        """Generate SQLAlchemy connection string."""
        # Handle SQLite databases
        if self.database.startswith('/:memory:'):
            return f"sqlite://{self.database}"

        # Handle PostgreSQL databases
        ssl_params = []
        if self.ssl_mode != "disable":
            ssl_params.append(f"sslmode={self.ssl_mode}")
        if self.ssl_cert:
            ssl_params.append(f"sslcert={self.ssl_cert}")
        if self.ssl_key:
            ssl_params.append(f"sslkey={self.ssl_key}")
        if self.ssl_ca:
            ssl_params.append(f"sslrootcert={self.ssl_ca}")

        ssl_string = "&".join(ssl_params) if ssl_params else ""

        base_url = f"postgresql://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"

        if ssl_string:
            base_url += f"?{ssl_string}"

        return base_url

    def validate(self) -> None:
        """Validate configuration settings."""
        if not self.database:
            raise ValueError("Database name is required")

        # For SQLite, username is not required
        if not self.username and not self.database.startswith('/:memory:'):
            raise ValueError("Database username is required")

        # Port validation only applies to non-SQLite databases
        if self.port > 0 and (self.port < 1 or self.port > 65535):
            raise ValueError("Port must be between 1 and 65535")

        if self.pool_size < 1:
            raise ValueError("Pool size must be at least 1")

        if self.max_overflow < 0:
            raise ValueError("Max overflow must be non-negative")

        if self.pool_timeout < 1:
            raise ValueError("Pool timeout must be at least 1 second")

        if self.pool_recycle < 0:
            raise ValueError("Pool recycle must be non-negative")
