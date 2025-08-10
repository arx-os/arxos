"""
Test configuration for integration tests.

This file configures the test environment, database setup, and common fixtures
for all integration tests.
"""

import os
import pytest
from typing import Generator
from fastapi.testclient import TestClient

# Set test environment variables before importing the app
os.environ["ARXOS_ENV"] = "test"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["USE_UNIFIED_API"] = "true"
os.environ["GUS_SERVICE_URL"] = "http://localhost:8000"  # Required env var
os.environ["SECRET_KEY"] = "test-secret-key-for-testing-only"
os.environ["DEBUG_MODE"] = "true"

# Import after setting environment variables
from api.main import app


class MockAuthMiddleware:
    """Mock authentication middleware for testing."""

    async def authenticate(self, request):
        """Mock authentication that always succeeds."""
        class MockUser:
            id = "test-user-id"
            username = "testuser"
            email = "test@example.com"
            roles = ["user"]
            permissions = ["read", "write"]

        request.state.user = MockUser()
        return MockUser()

    async def authorize(self, request, required_roles=None, required_permissions=None):
        """Mock authorization that always succeeds."""
        return True


@pytest.fixture(scope="session")
def test_app():
    """Create a test app instance with test configuration."""
    # Override authentication middleware to bypass JWT validation
    from api.unified.routes import dependencies as dep
    app.dependency_overrides[dep.get_auth_middleware] = lambda: MockAuthMiddleware()

    yield app

    # Cleanup overrides
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def client(test_app) -> Generator[TestClient, None, None]:
    """Create a test client for each test function."""
    with TestClient(test_app) as test_client:
        yield test_client


@pytest.fixture(autouse=True)
def setup_test_database():
    """Setup test database and ensure tables are created."""
    # The database connection will auto-create tables for SQLite in-memory
    # This happens automatically in the DatabaseConnection._initialize_engine method
    # when using SQLite in-memory database
    pass


@pytest.fixture(autouse=True)
def cleanup_test_database():
    """Cleanup test database after each test."""
    yield
    # SQLite in-memory database is automatically cleaned up when connection closes
