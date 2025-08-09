"""
Test cases for the Arxos BAS & IoT Device Registry.

This module contains comprehensive tests for device registration,
management, and status tracking functionality.
"""

import pytest
import tempfile
import os
import json
from datetime import datetime, timezone
from unittest.mock import Mock, patch

# Import the device registry module
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from device_registry import DeviceRegistry, DeviceStatus, DeviceType


class TestDeviceRegistry:
    """Test cases for DeviceRegistry class."""

    @pytest.fixture
def temp_db(self):
        """Create a temporary database for testing."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name

        yield db_path

        # Cleanup
        if os.path.exists(db_path):
            os.unlink(db_path)

    @pytest.fixture
def registry(self, temp_db):
        """Create a DeviceRegistry instance with temporary database."""
        registry = DeviceRegistry(database_url=f"sqlite:///{temp_db}")
        registry.initialize_database()
        return registry

    def test_initialize_database(self, temp_db):
        """Test database initialization."""
        registry = DeviceRegistry(database_url=f"sqlite:///{temp_db}")
        registry.initialize_database()

        # Verify tables were created
        assert os.path.exists(temp_db)

    def test_register_device(self, registry):
        """Test device registration."""
        device_data = {
            "device_id": "test_sensor_001",
            "device_type": DeviceType.TEMPERATURE_SENSOR,
            "manufacturer": "Arxos",
            "model": "TEMP-100",
            "location": "Building A, Floor 1, Room 101",
            "capabilities": ["temperature", "humidity"],
            "coordinates": {"x": 10.5, "y": 20.3, "z": 2.1}
        }

        device = registry.register_device(**device_data)

        assert device["device_id"] == "test_sensor_001"
        assert device["device_type"] == DeviceType.TEMPERATURE_SENSOR
        assert device["manufacturer"] == "Arxos"
        assert device["status"] == DeviceStatus.REGISTERED

    def test_register_duplicate_device(self, registry):
        """Test registering a device with duplicate ID."""
        device_data = {
            "device_id": "duplicate_sensor",
            "device_type": DeviceType.TEMPERATURE_SENSOR,
            "manufacturer": "Arxos",
            "model": "TEMP-100"
        }

        # Register first time
        registry.register_device(**device_data)

        # Try to register again
        with pytest.raises(ValueError, match="Device already exists"):
            registry.register_device(**device_data)

    def test_get_device(self, registry):
        """Test retrieving device information."""
        device_data = {
            "device_id": "test_sensor_002",
            "device_type": DeviceType.TEMPERATURE_SENSOR,
            "manufacturer": "Arxos",
            "model": "TEMP-100"
        }

        registry.register_device(**device_data)
        device = registry.get_device("test_sensor_002")

        assert device["device_id"] == "test_sensor_002"
        assert device["device_type"] == DeviceType.TEMPERATURE_SENSOR

    def test_get_nonexistent_device(self, registry):
        """Test retrieving non-existent device."""
        with pytest.raises(ValueError, match="Device not found"):
            registry.get_device("nonexistent_device")

    def test_update_device_status(self, registry):
        """Test updating device status."""
        device_data = {
            "device_id": "status_test_sensor",
            "device_type": DeviceType.TEMPERATURE_SENSOR,
            "manufacturer": "Arxos",
            "model": "TEMP-100"
        }

        registry.register_device(**device_data)

        # Update status
        registry.update_device_status(
            "status_test_sensor",
            DeviceStatus.ONLINE,
            {"last_seen": "2024-01-15T10:30:00Z"}
        )

        device = registry.get_device("status_test_sensor")
        assert device["status"] == DeviceStatus.ONLINE
        assert "last_seen" in device["status_data"]

    def test_list_devices(self, registry):
        """Test listing all devices."""
        # Register multiple devices
        devices = [
            {"device_id": "sensor_001", "device_type": DeviceType.TEMPERATURE_SENSOR, "manufacturer": "Arxos"},
            {"device_id": "sensor_002", "device_type": DeviceType.HUMIDITY_SENSOR, "manufacturer": "Arxos"},
            {"device_id": "controller_001", "device_type": DeviceType.HVAC_CONTROLLER, "manufacturer": "Arxos"}
        ]

        for device_data in devices:
            registry.register_device(**device_data)

        all_devices = registry.list_devices()
        assert len(all_devices) == 3

        device_ids = [device["device_id"] for device in all_devices]
        assert "sensor_001" in device_ids
        assert "sensor_002" in device_ids
        assert "controller_001" in device_ids

    def test_list_devices_by_type(self, registry):
        """Test listing devices filtered by type."""
        # Register devices of different types
        devices = [
            {"device_id": "temp_sensor", "device_type": DeviceType.TEMPERATURE_SENSOR, "manufacturer": "Arxos"},
            {"device_id": "humidity_sensor", "device_type": DeviceType.HUMIDITY_SENSOR, "manufacturer": "Arxos"},
            {"device_id": "hvac_controller", "device_type": DeviceType.HVAC_CONTROLLER, "manufacturer": "Arxos"}
        ]

        for device_data in devices:
            registry.register_device(**device_data)

        # Filter by temperature sensors
        temp_sensors = registry.list_devices(device_type=DeviceType.TEMPERATURE_SENSOR)
        assert len(temp_sensors) == 1
        assert temp_sensors[0]["device_id"] == "temp_sensor"

    def test_delete_device(self, registry):
        """Test device deletion."""
        device_data = {
            "device_id": "delete_test_sensor",
            "device_type": DeviceType.TEMPERATURE_SENSOR,
            "manufacturer": "Arxos",
            "model": "TEMP-100"
        }

        registry.register_device(**device_data)

        # Verify device exists
        device = registry.get_device("delete_test_sensor")
        assert device is not None

        # Delete device
        registry.delete_device("delete_test_sensor")

        # Verify device is deleted
        with pytest.raises(ValueError, match="Device not found"):
            registry.get_device("delete_test_sensor")

    def test_device_discovery(self, registry):
        """Test automatic device discovery."""
        # Mock network discovery
        mock_devices = [
            {"device_id": "discovered_001", "device_type": DeviceType.TEMPERATURE_SENSOR, "manufacturer": "Arxos"},
            {"device_id": "discovered_002", "device_type": DeviceType.HUMIDITY_SENSOR, "manufacturer": "Arxos"}
        ]

        with patch.object(registry, '_discover_devices', return_value=mock_devices):
            discovered = registry.discover_devices()

        assert len(discovered) == 2
        assert discovered[0]["device_id"] == "discovered_001"
        assert discovered[1]["device_id"] == "discovered_002"

    def test_device_health_check(self, registry):
        """Test device health monitoring."""
        device_data = {
            "device_id": "health_test_sensor",
            "device_type": DeviceType.TEMPERATURE_SENSOR,
            "manufacturer": "Arxos",
            "model": "TEMP-100"
        }

        registry.register_device(**device_data)

        # Update health status
        health_data = {
            "battery_level": 85,
            "signal_strength": -45,
            "last_communication": "2024-01-15T10:30:00Z"
        }

        registry.update_device_health("health_test_sensor", health_data)

        device = registry.get_device("health_test_sensor")
        assert "health_data" in device
        assert device["health_data"]["battery_level"] == 85

    def test_device_configuration(self, registry):
        """Test device configuration management."""
        device_data = {
            "device_id": "config_test_sensor",
            "device_type": DeviceType.TEMPERATURE_SENSOR,
            "manufacturer": "Arxos",
            "model": "TEMP-100"
        }

        registry.register_device(**device_data)

        # Set configuration
        config = {
            "sampling_interval": 30,
            "alert_thresholds": {"min": 15, "max": 30},
            "calibration_offset": 0.5
        }

        registry.set_device_configuration("config_test_sensor", config)

        device = registry.get_device("config_test_sensor")
        assert "configuration" in device
        assert device["configuration"]["sampling_interval"] == 30

    def test_device_statistics(self, registry):
        """Test device statistics and analytics."""
        # Register multiple devices
        devices = [
            {"device_id": "stats_sensor_001", "device_type": DeviceType.TEMPERATURE_SENSOR, "manufacturer": "Arxos"},
            {"device_id": "stats_sensor_002", "device_type": DeviceType.TEMPERATURE_SENSOR, "manufacturer": "Arxos"},
            {"device_id": "stats_controller", "device_type": DeviceType.HVAC_CONTROLLER, "manufacturer": "Arxos"}
        ]

        for device_data in devices:
            registry.register_device(**device_data)

        # Get statistics
        stats = registry.get_device_statistics()

        assert "total_devices" in stats
        assert "devices_by_type" in stats
        assert "devices_by_manufacturer" in stats
        assert stats["total_devices"] == 3
        assert stats["devices_by_type"]["temperature_sensor"] == 2
        assert stats["devices_by_manufacturer"]["Arxos"] == 3


if __name__ == "__main__":
    pytest.main([__file__])
