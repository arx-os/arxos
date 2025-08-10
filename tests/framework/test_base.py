"""
Comprehensive Test Framework Base Classes

Provides standardized test base classes with common utilities, fixtures,
and patterns for unit, integration, and end-to-end testing.
"""

import unittest
import pytest
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any, Optional, List, Type, TypeVar
from datetime import datetime, timezone
import tempfile
import os
import json
from contextlib import contextmanager
from dataclasses import dataclass

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

# Import our domain and infrastructure
from domain.entities import Building, Floor, Room, Device, User, Project
from domain.value_objects import BuildingId, FloorId, RoomId, DeviceId, UserId, ProjectId
from domain.value_objects import Address, Coordinates, Dimensions, Email, PhoneNumber
from domain.exceptions import DomainException
from application.exceptions import ApplicationError
from infrastructure.database.models import Base
from infrastructure.logging.structured_logging import get_logger, log_context

T = TypeVar('T')

logger = get_logger(__name__)


@dataclass
class TestConfig:
    """Test configuration with environment-specific settings."""
    use_in_memory_db: bool = True
    enable_logging: bool = False
    log_level: str = "DEBUG"
    test_data_dir: Optional[str] = None
    cache_enabled: bool = False
    mock_external_services: bool = True


class TestDataFactory:
    """Factory for creating test data objects."""
    
    @staticmethod
    def create_test_address(**kwargs) -> Address:
        """Create a test address with default values."""
        defaults = {
            "street": "123 Test Street",
            "city": "Test City", 
            "state": "TS",
            "postal_code": "12345",
            "country": "USA"
        }
        defaults.update(kwargs)
        return Address(**defaults)
    
    @staticmethod 
    def create_test_coordinates(**kwargs) -> Coordinates:
        """Create test coordinates with default values."""
        defaults = {
            "latitude": 40.7128,
            "longitude": -74.0060,
            "elevation": 10.0
        }
        defaults.update(kwargs)
        return Coordinates(**defaults)
    
    @staticmethod
    def create_test_dimensions(**kwargs) -> Dimensions:
        """Create test dimensions with default values."""
        defaults = {
            "width": 10.0,
            "length": 15.0,
            "height": 3.0,
            "unit": "meters"
        }
        defaults.update(kwargs)
        return Dimensions(**defaults)
    
    @staticmethod
    def create_test_building(**kwargs) -> Building:
        """Create a test building with default values."""
        defaults = {
            "id": BuildingId(),
            "name": "Test Building",
            "address": TestDataFactory.create_test_address(),
            "description": "A test building for unit testing",
            "created_by": "test_user"
        }
        
        # Handle nested objects
        if 'coordinates' not in kwargs:
            defaults['coordinates'] = TestDataFactory.create_test_coordinates()
        if 'dimensions' not in kwargs:
            defaults['dimensions'] = TestDataFactory.create_test_dimensions()
        
        defaults.update(kwargs)
        return Building(**defaults)
    
    @staticmethod
    def create_test_floor(**kwargs) -> Floor:
        """Create a test floor with default values."""
        defaults = {
            "id": FloorId(),
            "building_id": BuildingId(),
            "name": "Test Floor",
            "floor_number": 1,
            "description": "A test floor for unit testing",
            "created_by": "test_user"
        }
        defaults.update(kwargs)
        return Floor(**defaults)
    
    @staticmethod
    def create_test_room(**kwargs) -> Room:
        """Create a test room with default values."""
        defaults = {
            "id": RoomId(),
            "floor_id": FloorId(),
            "name": "Test Room",
            "room_number": "101",
            "room_type": "office",
            "description": "A test room for unit testing",
            "area": 100.0,
            "created_by": "test_user"
        }
        defaults.update(kwargs)
        return Room(**defaults)
    
    @staticmethod
    def create_test_device(**kwargs) -> Device:
        """Create a test device with default values."""
        defaults = {
            "id": DeviceId(),
            "room_id": RoomId(),
            "name": "Test Device",
            "device_id": "TEST_001",
            "device_type": "sensor",
            "manufacturer": "TestCorp",
            "model": "TestModel-v1",
            "created_by": "test_user"
        }
        defaults.update(kwargs)
        return Device(**defaults)
    
    @staticmethod
    def create_test_user(**kwargs) -> User:
        """Create a test user with default values."""
        defaults = {
            "id": UserId(),
            "username": "testuser",
            "email": Email("test@example.com"),
            "first_name": "Test",
            "last_name": "User",
            "created_by": "system"
        }
        
        if 'phone_number' not in kwargs:
            defaults['phone_number'] = PhoneNumber("555-0123")
        
        defaults.update(kwargs)
        return User(**defaults)


class BaseTestCase(unittest.TestCase):
    """Base test case with common utilities and setup."""
    
    def setUp(self) -> None:
        """Set up test case with common configuration."""
        self.config = TestConfig()
        self.test_data = TestDataFactory()
        self.maxDiff = None  # Show full diff for failed assertions
        
        # Set up test context
        self.test_context = {
            "test_name": self._testMethodName,
            "test_class": self.__class__.__name__,
            "test_id": f"{self.__class__.__name__}.{self._testMethodName}"
        }
        
        # Mock logger if logging is disabled
        if not self.config.enable_logging:
            self.mock_logger = Mock()
            self.logger_patcher = patch('infrastructure.logging.structured_logging.get_logger', 
                                      return_value=self.mock_logger)
            self.logger_patcher.start()
        else:
            self.logger = get_logger(f"test.{self.__class__.__name__}")
    
    def tearDown(self) -> None:
        """Clean up after test case."""
        if hasattr(self, 'logger_patcher'):
            self.logger_patcher.stop()
    
    def assertRaisesWithMessage(self, exception_class: Type[Exception], 
                               expected_message: str, callable_obj, *args, **kwargs):
        """Assert that an exception is raised with a specific message."""
        with self.assertRaises(exception_class) as context:
            callable_obj(*args, **kwargs)
        
        self.assertIn(expected_message, str(context.exception))
    
    def assertDomainEvent(self, entity, event_type: Type, **expected_fields):
        """Assert that a domain event was raised on an entity."""
        events = entity.get_domain_events() if hasattr(entity, 'get_domain_events') else []
        matching_events = [e for e in events if isinstance(e, event_type)]
        
        self.assertGreater(len(matching_events), 0, 
                          f"No {event_type.__name__} event found in {events}")
        
        event = matching_events[-1]  # Get the most recent event
        for field, expected_value in expected_fields.items():
            self.assertEqual(getattr(event, field), expected_value,
                           f"Event field {field} did not match expected value")
    
    def create_mock_repository(self, repository_class: Type[T]) -> Mock:
        """Create a mock repository with common methods."""
        mock_repo = Mock(spec=repository_class)
        mock_repo.save.return_value = None
        mock_repo.get_by_id.return_value = None
        mock_repo.get_all.return_value = []
        mock_repo.delete.return_value = True
        mock_repo.exists.return_value = False
        return mock_repo
    
    def create_test_data_batch(self, entity_factory: callable, count: int, **kwargs) -> List[Any]:
        """Create a batch of test entities."""
        return [entity_factory(**kwargs) for _ in range(count)]


class DatabaseTestCase(BaseTestCase):
    """Base test case for database-related tests."""
    
    def setUp(self) -> None:
        """Set up database test case with in-memory database."""
        super().setUp()
        
        # Create in-memory SQLite database
        self.engine = create_engine(
            "sqlite:///:memory:",
            poolclass=StaticPool,
            connect_args={'check_same_thread': False},
            echo=self.config.enable_logging and self.config.log_level == "DEBUG"
        )
        
        # Create all tables
        Base.metadata.create_all(self.engine)
        
        # Create session factory
        self.SessionFactory = sessionmaker(bind=self.engine)
        self.session = self.SessionFactory()
        
        logger.debug("In-memory database created for testing")
    
    def tearDown(self) -> None:
        """Clean up database test case."""
        if hasattr(self, 'session'):
            self.session.close()
        if hasattr(self, 'engine'):
            self.engine.dispose()
        super().tearDown()
    
    @contextmanager
    def database_transaction(self):
        """Context manager for database transactions in tests."""
        session = self.SessionFactory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    
    def assertDatabaseState(self, model_class, expected_count: int):
        """Assert the expected count of records in database."""
        actual_count = self.session.query(model_class).count()
        self.assertEqual(actual_count, expected_count,
                        f"Expected {expected_count} {model_class.__name__} records, "
                        f"but found {actual_count}")


class ServiceTestCase(BaseTestCase):
    """Base test case for service layer tests."""
    
    def setUp(self) -> None:
        """Set up service test case with mocked dependencies."""
        super().setUp()
        
        # Create mock unit of work
        self.mock_unit_of_work = Mock()
        self.mock_unit_of_work.__enter__ = Mock(return_value=self.mock_unit_of_work)
        self.mock_unit_of_work.__exit__ = Mock(return_value=None)
        
        # Create mock repositories
        self.mock_building_repository = self.create_mock_repository(object)
        self.mock_floor_repository = self.create_mock_repository(object)
        self.mock_room_repository = self.create_mock_repository(object)
        self.mock_device_repository = self.create_mock_repository(object)
        self.mock_user_repository = self.create_mock_repository(object)
        self.mock_project_repository = self.create_mock_repository(object)
        
        # Attach repositories to unit of work
        self.mock_unit_of_work.building_repository = self.mock_building_repository
        self.mock_unit_of_work.floor_repository = self.mock_floor_repository
        self.mock_unit_of_work.room_repository = self.mock_room_repository
        self.mock_unit_of_work.device_repository = self.mock_device_repository
        self.mock_unit_of_work.user_repository = self.mock_user_repository
        self.mock_unit_of_work.project_repository = self.mock_project_repository
        
        # Create mock infrastructure services
        self.mock_cache_service = Mock()
        self.mock_event_store = Mock()
        self.mock_message_queue = Mock()
        self.mock_metrics = Mock()
    
    def assertRepositoryMethod(self, repository: Mock, method_name: str, 
                              call_count: int = 1, **expected_kwargs):
        """Assert that a repository method was called with expected parameters."""
        method = getattr(repository, method_name)
        self.assertEqual(method.call_count, call_count,
                        f"Expected {method_name} to be called {call_count} times, "
                        f"but was called {method.call_count} times")
        
        if expected_kwargs:
            method.assert_called_with(**expected_kwargs)


class IntegrationTestCase(DatabaseTestCase):
    """Base test case for integration tests."""
    
    def setUp(self) -> None:
        """Set up integration test case with real database and services."""
        super().setUp()
        
        # Set up real services with test database
        from infrastructure.repositories.building_repository import SQLAlchemyBuildingRepository
        from infrastructure.repositories.floor_repository import SQLAlchemyFloorRepository
        from infrastructure.repositories.room_repository import SQLAlchemyRoomRepository
        
        self.building_repository = SQLAlchemyBuildingRepository(self.session)
        self.floor_repository = SQLAlchemyFloorRepository(self.session) 
        self.room_repository = SQLAlchemyRoomRepository(self.session)
        
        # Create real unit of work for integration tests
        from domain.repositories import UnitOfWork
        self.unit_of_work = UnitOfWork(
            session=self.session,
            building_repository=self.building_repository,
            floor_repository=self.floor_repository,
            room_repository=self.room_repository
        )
    
    def create_test_building_hierarchy(self) -> Dict[str, Any]:
        """Create a complete building hierarchy for testing."""
        # Create building
        building = self.test_data.create_test_building()
        saved_building = self.building_repository.save(building)
        
        # Create floor
        floor = self.test_data.create_test_floor(building_id=saved_building.id)
        saved_floor = self.floor_repository.save(floor)
        
        # Create rooms
        rooms = []
        for i in range(3):
            room = self.test_data.create_test_room(
                floor_id=saved_floor.id,
                name=f"Test Room {i+1}",
                room_number=f"10{i+1}"
            )
            saved_room = self.room_repository.save(room)
            rooms.append(saved_room)
        
        self.session.commit()
        
        return {
            "building": saved_building,
            "floor": saved_floor,
            "rooms": rooms
        }


@pytest.fixture
def test_config():
    """Pytest fixture for test configuration."""
    return TestConfig()


@pytest.fixture
def test_data_factory():
    """Pytest fixture for test data factory."""
    return TestDataFactory()


@pytest.fixture
def in_memory_database():
    """Pytest fixture for in-memory database."""
    engine = create_engine(
        "sqlite:///:memory:",
        poolclass=StaticPool,
        connect_args={'check_same_thread': False}
    )
    
    Base.metadata.create_all(engine)
    
    SessionFactory = sessionmaker(bind=engine)
    session = SessionFactory()
    
    yield session
    
    session.close()
    engine.dispose()


class TestRunner:
    """Utility class for running different types of tests."""
    
    @staticmethod
    def run_unit_tests(test_dir: str = "tests/unit") -> Dict[str, Any]:
        """Run unit tests and return results."""
        import subprocess
        import sys
        
        cmd = [sys.executable, "-m", "pytest", test_dir, "-v", "--tb=short"]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        return {
            "exit_code": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "success": result.returncode == 0
        }
    
    @staticmethod
    def run_integration_tests(test_dir: str = "tests/integration") -> Dict[str, Any]:
        """Run integration tests and return results."""
        import subprocess
        import sys
        
        cmd = [sys.executable, "-m", "pytest", test_dir, "-v", "--tb=short"]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        return {
            "exit_code": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "success": result.returncode == 0
        }
    
    @staticmethod
    def generate_coverage_report() -> Dict[str, Any]:
        """Generate test coverage report."""
        import subprocess
        import sys
        
        # Run tests with coverage
        cmd = [
            sys.executable, "-m", "pytest", 
            "--cov=domain", "--cov=application", "--cov=infrastructure",
            "--cov-report=term-missing", "--cov-report=json"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        coverage_data = {}
        try:
            with open("coverage.json", "r") as f:
                coverage_data = json.load(f)
        except FileNotFoundError:
            pass
        
        return {
            "exit_code": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "success": result.returncode == 0,
            "coverage_data": coverage_data
        }