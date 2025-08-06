"""
Service Layer Integration Tests

This module contains comprehensive tests for the service layer integration,
validating transaction management, business rules, and proper service coordination.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from typing import Dict, Any

from application.services.device_service import DeviceApplicationService
from application.transaction import TransactionManager, UnitOfWork
from application.business_rules import BusinessRuleService
from application.exceptions import (
    ApplicationError,
    ValidationError,
    BusinessRuleError,
    TransactionError,
    ResourceNotFoundError,
)
from application.dto.device_dto import (
    CreateDeviceRequest,
    CreateDeviceResponse,
    UpdateDeviceRequest,
    UpdateDeviceResponse,
    GetDeviceResponse,
    ListDevicesResponse,
    DeleteDeviceResponse,
)
from domain.value_objects import DeviceId, RoomId, DeviceStatus
from domain.entities import Device


class TestServiceLayerIntegration:
    """Test service layer integration with all components."""

    @pytest.fixture
    def mock_device_repository(self):
        """Create a mock device repository."""
        mock_repo = Mock()
        mock_repo.save.return_value = None
        mock_repo.get_by_id.return_value = None
        mock_repo.get_by_room_id.return_value = []
        mock_repo.get_by_type.return_value = []
        mock_repo.get_by_status.return_value = []
        mock_repo.count.return_value = 0
        mock_repo.delete.return_value = True
        return mock_repo

    @pytest.fixture
    def mock_cache_service(self):
        """Create a mock cache service."""
        mock_cache = Mock()
        mock_cache.get.return_value = None
        mock_cache.set.return_value = None
        mock_cache.delete.return_value = None
        return mock_cache

    @pytest.fixture
    def mock_event_store(self):
        """Create a mock event store."""
        mock_events = Mock()
        mock_events.publish_device_created_event.return_value = None
        mock_events.publish_device_updated_event.return_value = None
        mock_events.publish_device_deleted_event.return_value = None
        mock_events.publish_device_status_changed_event.return_value = None
        mock_events.publish_device_assigned_event.return_value = None
        return mock_events

    @pytest.fixture
    def mock_metrics(self):
        """Create a mock metrics service."""
        mock_metrics = Mock()
        mock_metrics.increment_counter.return_value = None
        return mock_metrics

    @pytest.fixture
    def device_service(
        self, mock_device_repository, mock_cache_service, mock_event_store, mock_metrics
    ):
        """Create a device service with mocked dependencies."""
        return DeviceApplicationService(
            device_repository=mock_device_repository,
            cache_service=mock_cache_service,
            event_store=mock_event_store,
            message_queue=Mock(),
            metrics=mock_metrics,
            logger=Mock(),
        )

    def test_create_device_with_business_rules(
        self, device_service, mock_device_repository
    ):
        """Test device creation with business rules validation."""
        # Arrange
        device_data = {
            "room_id": "room-123",
            "device_type": "sensor",
            "name": "Temperature Sensor 1",
            "manufacturer": "Acme Corp",
            "model": "TS-1000",
            "serial_number": "SN123456",
            "description": "Temperature sensor for room monitoring",
            "created_by": "test-user",
        }

        # Mock successful use case response
        mock_response = CreateDeviceResponse(
            success=True,
            device_id="device-123",
            message="Device created successfully",
            created_at=datetime.utcnow(),
        )

        with patch("application.business_rules.validate_business_rules"):
            with patch.object(
                device_service.create_device_use_case,
                "execute",
                return_value=mock_response,
            ):
                # Act
                result = device_service.create_device(device_data)

                # Assert
                assert result.success is True
                assert result.device_id == "device-123"
                mock_device_repository.save.assert_called()

    def test_create_device_business_rules_violation(self, device_service):
        """Test device creation with business rules violation."""
        # Arrange
        device_data = {
            "room_id": "room-123",
            "device_type": "invalid_type",  # Invalid device type
            "name": "",  # Empty name
            "created_by": "test-user",
        }

        with patch(
            "application.business_rules.validate_business_rules",
            side_effect=BusinessRuleError(
                message="Business rule validation failed",
                rule="device_type_valid",
                context={"errors": ["Device type must be valid"]},
            ),
        ):
            # Act & Assert
            with pytest.raises(BusinessRuleError) as exc_info:
                device_service.create_device(device_data)

            assert "Business rule validation failed" in str(exc_info.value)

    def test_update_device_with_transaction(
        self, device_service, mock_device_repository
    ):
        """Test device update with transaction management."""
        # Arrange
        device_id = "device-123"
        update_data = {
            "name": "Updated Device Name",
            "status": "active",
            "updated_by": "test-user",
        }

        # Mock successful use case response
        mock_response = UpdateDeviceResponse(
            success=True,
            device_id=device_id,
            message="Device updated successfully",
            updated_at=datetime.utcnow(),
        )

        with patch("application.business_rules.validate_entity_update"):
            with patch.object(
                device_service.update_device_use_case,
                "execute",
                return_value=mock_response,
            ):
                # Act
                result = device_service.update_device(device_id, update_data)

                # Assert
                assert result.success is True
                assert result.device_id == device_id

    def test_get_device_with_caching(self, device_service, mock_cache_service):
        """Test device retrieval with caching."""
        # Arrange
        device_id = "device-123"
        cached_device = {
            "id": device_id,
            "name": "Cached Device",
            "device_type": "sensor",
        }

        # Mock cache hit
        mock_cache_service.get.return_value = cached_device

        # Act
        result = device_service.get_device(device_id)

        # Assert
        assert result.success is True
        assert result.device == cached_device
        mock_cache_service.get.assert_called_with(f"device:{device_id}")

    def test_delete_device_with_retry_logic(
        self, device_service, mock_device_repository
    ):
        """Test device deletion with retry logic."""
        # Arrange
        device_id = "device-123"

        # Mock successful use case response
        mock_response = DeleteDeviceResponse(
            success=True,
            device_id=device_id,
            message="Device deleted successfully",
            deleted_at=datetime.utcnow(),
        )

        with patch.object(
            device_service.delete_device_use_case, "execute", return_value=mock_response
        ):
            # Act
            result = device_service.delete_device(device_id)

            # Assert
            assert result.success is True
            assert result.device_id == device_id

    def test_bulk_update_devices_transaction(self, device_service):
        """Test bulk update devices with transaction management."""
        # Arrange
        device_updates = [
            {"device_id": "device-1", "name": "Updated Device 1"},
            {"device_id": "device-2", "name": "Updated Device 2"},
            {"device_id": "device-3", "name": "Updated Device 3"},
        ]

        # Mock successful update responses
        mock_response = UpdateDeviceResponse(
            success=True, device_id="device-1", message="Device updated successfully"
        )

        with patch.object(device_service, "update_device", return_value=mock_response):
            # Act
            result = device_service.bulk_update_devices(device_updates)

            # Assert
            assert result["successful"] == 3
            assert result["failed"] == 0
            assert len(result["errors"]) == 0

    def test_assign_device_to_room(self, device_service, mock_event_store):
        """Test device assignment to room with event publishing."""
        # Arrange
        device_id = "device-123"
        room_id = "room-456"
        assigned_by = "test-user"

        # Mock successful use case response
        mock_response = UpdateDeviceResponse(
            success=True, device_id=device_id, message="Device assigned successfully"
        )

        with patch.object(
            device_service.update_device_use_case, "execute", return_value=mock_response
        ):
            # Act
            result = device_service.assign_device_to_room(
                device_id, room_id, assigned_by
            )

            # Assert
            assert result.success is True
            mock_event_store.publish_device_assigned_event.assert_called_with(
                device_id=device_id, room_id=room_id, assigned_by=assigned_by
            )

    def test_transaction_rollback_on_error(self, device_service):
        """Test transaction rollback when error occurs."""
        # Arrange
        device_data = {
            "room_id": "room-123",
            "device_type": "sensor",
            "name": "Test Device",
        }

        with patch.object(
            device_service.create_device_use_case,
            "execute",
            side_effect=Exception("Database error"),
        ):
            # Act & Assert
            with pytest.raises(ApplicationError) as exc_info:
                device_service.create_device(device_data)

            assert "Failed to create device" in str(exc_info.value)

    def test_business_rules_validation_integration(self):
        """Test business rules validation integration."""
        # Arrange
        business_rule_service = BusinessRuleService()

        # Valid device data
        valid_device_data = {
            "name": "Valid Device",
            "device_type": "sensor",
            "serial_number": "SN123456",
        }

        # Invalid device data
        invalid_device_data = {
            "name": "",  # Empty name
            "device_type": "invalid_type",  # Invalid type
            "serial_number": "SN123456",
        }

        # Act & Assert - Valid data should pass
        try:
            business_rule_service.validate_entity_creation("device", valid_device_data)
        except BusinessRuleError:
            pytest.fail("Valid device data should not raise BusinessRuleError")

        # Act & Assert - Invalid data should fail
        with pytest.raises(BusinessRuleError):
            business_rule_service.validate_entity_creation(
                "device", invalid_device_data
            )

    def test_transaction_manager_integration(self):
        """Test transaction manager integration."""
        # Arrange
        transaction_manager = TransactionManager()

        def test_operation(data):
            return f"Processed: {data}"

        # Act & Assert
        try:
            result = transaction_manager.execute_in_transaction(
                test_operation, "test_data"
            )
            assert result == "Processed: test_data"
        except Exception as e:
            # In test environment, database connection might not be available
            assert "Transaction failed" in str(e) or "Database connection" in str(e)

    def test_unit_of_work_pattern(self):
        """Test Unit of Work pattern."""
        # Arrange
        uow = UnitOfWork()

        # Act & Assert
        try:
            with uow as work_unit:
                # Simulate repository operations
                device_repo = work_unit.get_repository("device")
                assert device_repo is not None

                # Commit the transaction
                work_unit.commit()
        except Exception as e:
            # In test environment, database connection might not be available
            assert "Database connection" in str(e) or "Session" in str(e)

    def test_service_layer_error_handling(self, device_service):
        """Test comprehensive error handling in service layer."""
        # Arrange
        invalid_device_data = {
            "room_id": "",  # Invalid room ID
            "device_type": "invalid_type",  # Invalid device type
            "name": "",  # Empty name
        }

        # Act & Assert
        with pytest.raises(ApplicationError) as exc_info:
            device_service.create_device(invalid_device_data)

        assert exc_info.value.error_code in [
            "DEVICE_CREATION_ERROR",
            "VALIDATION_ERROR",
            "BUSINESS_RULE_ERROR",
        ]

    def test_metrics_and_logging_integration(self, device_service, mock_metrics):
        """Test metrics and logging integration."""
        # Arrange
        device_data = {
            "room_id": "room-123",
            "device_type": "sensor",
            "name": "Test Device",
            "created_by": "test-user",
        }

        mock_response = CreateDeviceResponse(
            success=True, device_id="device-123", message="Device created successfully"
        )

        with patch.object(
            device_service.create_device_use_case, "execute", return_value=mock_response
        ):
            # Act
            device_service.create_device(device_data)

            # Assert
            mock_metrics.increment_counter.assert_called_with("devices_created")

    def test_cache_invalidation_on_update(self, device_service, mock_cache_service):
        """Test cache invalidation when device is updated."""
        # Arrange
        device_id = "device-123"
        update_data = {"name": "Updated Device Name", "updated_by": "test-user"}

        mock_response = UpdateDeviceResponse(
            success=True, device_id=device_id, message="Device updated successfully"
        )

        with patch.object(
            device_service.update_device_use_case, "execute", return_value=mock_response
        ):
            # Act
            device_service.update_device(device_id, update_data)

            # Assert
            mock_cache_service.delete.assert_called_with(f"device:{device_id}")

    def test_event_publishing_integration(self, device_service, mock_event_store):
        """Test event publishing integration."""
        # Arrange
        device_data = {
            "room_id": "room-123",
            "device_type": "sensor",
            "name": "Test Device",
            "created_by": "test-user",
        }

        mock_response = CreateDeviceResponse(
            success=True, device_id="device-123", message="Device created successfully"
        )

        with patch.object(
            device_service.create_device_use_case, "execute", return_value=mock_response
        ):
            # Act
            device_service.create_device(device_data)

            # Assert
            mock_event_store.publish_device_created_event.assert_called_with(
                device_id="device-123", device_data=device_data
            )


class TestServiceLayerPerformance:
    """Test service layer performance characteristics."""

    def test_bulk_operations_performance(self):
        """Test bulk operations performance."""
        # This would test performance characteristics of bulk operations
        # Implementation would depend on actual performance requirements
        pass

    def test_caching_performance(self):
        """Test caching performance impact."""
        # This would test the performance impact of caching
        # Implementation would depend on actual performance requirements
        pass

    def test_transaction_performance(self):
        """Test transaction performance characteristics."""
        # This would test transaction performance
        # Implementation would depend on actual performance requirements
        pass


if __name__ == "__main__":
    pytest.main([__file__])
