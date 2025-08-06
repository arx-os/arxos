"""
BAS & IoT Device Registry

Central registry for Building Automation System (BAS) and IoT device management.
Supports device registration, discovery, telemetry collection, and driver abstraction
for plug-in style expansion with third-party device compatibility.
"""

import asyncio
import json
import logging
import time
import uuid
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from pathlib import Path
import sqlite3
import threading
from concurrent.futures import ThreadPoolExecutor
import aiohttp
import yaml

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DeviceType(Enum):
    """Supported device types."""

    SENSOR = "sensor"
    ACTUATOR = "actuator"
    CONTROLLER = "controller"
    GATEWAY = "gateway"
    CAMERA = "camera"
    DISPLAY = "display"
    ALARM = "alarm"
    HVAC = "hvac"
    LIGHTING = "lighting"
    SECURITY = "security"
    ACCESS_CONTROL = "access_control"
    FIRE_ALARM = "fire_alarm"
    PLUMBING = "plumbing"
    ELECTRICAL = "electrical"
    CUSTOM = "custom"


class DeviceStatus(Enum):
    """Device operational status."""

    ONLINE = "online"
    OFFLINE = "offline"
    ERROR = "error"
    MAINTENANCE = "maintenance"
    DISCOVERING = "discovering"
    CONFIGURING = "configuring"


class CommunicationProtocol(Enum):
    """Supported communication protocols."""

    BACNET = "bacnet"
    MODBUS = "modbus"
    LONWORKS = "lonworks"
    KNX = "knx"
    ZIGBEE = "zigbee"
    ZWAVE = "zwave"
    WIFI = "wifi"
    ETHERNET = "ethernet"
    RS485 = "rs485"
    RS232 = "rs232"
    MQTT = "mqtt"
    HTTP = "http"
    HTTPS = "https"
    COAP = "coap"
    CUSTOM = "custom"


@dataclass
class DeviceCapability:
    """Device capability definition."""

    name: str
    type: str  # read, write, both
    data_type: str  # boolean, integer, float, string, json
    unit: Optional[str] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    description: Optional[str] = None


@dataclass
class DeviceLocation:
    """Device physical location."""

    building_id: str
    floor_id: str
    room_id: Optional[str] = None
    x_coordinate: Optional[float] = None
    y_coordinate: Optional[float] = None
    z_coordinate: Optional[float] = None
    description: Optional[str] = None


@dataclass
class DeviceMetadata:
    """Device metadata and configuration."""

    manufacturer: str
    model: str
    serial_number: str
    firmware_version: Optional[str] = None
    hardware_version: Optional[str] = None
    installation_date: Optional[datetime] = None
    last_maintenance: Optional[datetime] = None
    warranty_expiry: Optional[datetime] = None
    tags: List[str] = None
    notes: Optional[str] = None


@dataclass
class DeviceConnection:
    """Device communication connection details."""

    protocol: CommunicationProtocol
    address: str
    port: Optional[int] = None
    credentials: Optional[Dict[str, str]] = None
    encryption: Optional[str] = None
    timeout: Optional[int] = None
    retry_count: Optional[int] = None


@dataclass
class Device:
    """Complete device representation."""

    id: str
    name: str
    device_type: DeviceType
    status: DeviceStatus
    location: DeviceLocation
    metadata: DeviceMetadata
    connection: DeviceConnection
    capabilities: List[DeviceCapability]
    last_seen: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    driver_name: Optional[str] = None
    driver_config: Optional[Dict[str, Any]] = None


class DeviceRegistry:
    """Central device registry for BAS and IoT device management."""

    def __init__(self, db_path: str = "device_registry.db"):
        """Initialize device registry."""
        self.db_path = db_path
        self.devices: Dict[str, Device] = {}
        self.drivers: Dict[str, Any] = {}
        self.discovery_handlers: List[callable] = []
        self.telemetry_handlers: List[callable] = []
        self.lock = threading.RLock()
        self.executor = ThreadPoolExecutor(max_workers=10)

        # Initialize database
        self._init_database()

        # Load existing devices
        self._load_devices()

        # Start background tasks
        self._start_background_tasks()

    def _init_database(self):
        """Initialize SQLite database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS devices (
                        id TEXT PRIMARY KEY,
                        name TEXT NOT NULL,
                        device_type TEXT NOT NULL,
                        status TEXT NOT NULL,
                        location_json TEXT NOT NULL,
                        metadata_json TEXT NOT NULL,
                        connection_json TEXT NOT NULL,
                        capabilities_json TEXT NOT NULL,
                        last_seen TEXT,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL,
                        driver_name TEXT,
                        driver_config_json TEXT
                    )
                """
                )

                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS device_telemetry (
                        device_id TEXT NOT NULL,
                        capability_name TEXT NOT NULL,
                        value TEXT NOT NULL,
                        timestamp TEXT NOT NULL,
                        FOREIGN KEY (device_id) REFERENCES devices (id)
                    )
                """
                )

                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS device_events (
                        device_id TEXT NOT NULL,
                        event_type TEXT NOT NULL,
                        event_data TEXT NOT NULL,
                        timestamp TEXT NOT NULL,
                        FOREIGN KEY (device_id) REFERENCES devices (id)
                    )
                """
                )

                conn.commit()
                logger.info("Device registry database initialized")

        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise

    def _load_devices(self):
        """Load devices from database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("SELECT * FROM devices")
                for row in cursor.fetchall():
                    device = self._row_to_device(row)
                    self.devices[device.id] = device

            logger.info(f"Loaded {len(self.devices)} devices from database")

        except Exception as e:
            logger.error(f"Failed to load devices: {e}")

    def _row_to_device(self, row) -> Device:
        """Convert database row to Device object."""
        return Device(
            id=row[0],
            name=row[1],
            device_type=DeviceType(row[2]),
            status=DeviceStatus(row[3]),
            location=DeviceLocation(**json.loads(row[4])),
            metadata=DeviceMetadata(**json.loads(row[5])),
            connection=DeviceConnection(**json.loads(row[6])),
            capabilities=[DeviceCapability(**cap) for cap in json.loads(row[7])],
            last_seen=datetime.fromisoformat(row[8]) if row[8] else None,
            created_at=datetime.fromisoformat(row[9]),
            updated_at=datetime.fromisoformat(row[10]),
            driver_name=row[11],
            driver_config=json.loads(row[12]) if row[12] else None,
        )

    def _device_to_row(self, device: Device) -> tuple:
        """Convert Device object to database row."""
        return (
            device.id,
            device.name,
            device.device_type.value,
            device.status.value,
            json.dumps(asdict(device.location)),
            json.dumps(asdict(device.metadata)),
            json.dumps(asdict(device.connection)),
            json.dumps([asdict(cap) for cap in device.capabilities]),
            device.last_seen.isoformat() if device.last_seen else None,
            device.created_at.isoformat(),
            device.updated_at.isoformat(),
            device.driver_name,
            json.dumps(device.driver_config) if device.driver_config else None,
        )

    def register_device(self, device: Device) -> bool:
        """Register a new device."""
        try:
            with self.lock:
                # Check if device already exists
                if device.id in self.devices:
                    logger.warning(f"Device {device.id} already registered")
                    return False

                # Validate device
                if not self._validate_device(device):
                    logger.error(f"Device {device.id} validation failed")
                    return False

                # Save to database
                with sqlite3.connect(self.db_path) as conn:
                    conn.execute(
                        """
                        INSERT INTO devices VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                        self._device_to_row(device),
                    )
                    conn.commit()

                # Add to memory
                self.devices[device.id] = device

                # Notify handlers
                self._notify_discovery_handlers(device, "registered")

                logger.info(f"Device {device.id} registered successfully")
                return True

        except Exception as e:
            logger.error(f"Failed to register device {device.id}: {e}")
            return False

    def update_device(self, device_id: str, updates: Dict[str, Any]) -> bool:
        """Update device information."""
        try:
            with self.lock:
                if device_id not in self.devices:
                    logger.error(f"Device {device_id} not found")
                    return False

                device = self.devices[device_id]

                # Apply updates
                for key, value in updates.items():
                    if hasattr(device, key):
                        setattr(device, key, value)

                device.updated_at = datetime.utcnow()

                # Update database
                with sqlite3.connect(self.db_path) as conn:
                    conn.execute(
                        """
                        UPDATE devices SET 
                            name = ?, device_type = ?, status = ?, location_json = ?,
                            metadata_json = ?, connection_json = ?, capabilities_json = ?,
                            last_seen = ?, updated_at = ?, driver_name = ?, driver_config_json = ?
                        WHERE id = ?
                    """,
                        self._device_to_row(device)[1:] + (device_id,),
                    )
                    conn.commit()

                # Notify handlers
                self._notify_discovery_handlers(device, "updated")

                logger.info(f"Device {device_id} updated successfully")
                return True

        except Exception as e:
            logger.error(f"Failed to update device {device_id}: {e}")
            return False

    def unregister_device(self, device_id: str) -> bool:
        """Unregister a device."""
        try:
            with self.lock:
                if device_id not in self.devices:
                    logger.error(f"Device {device_id} not found")
                    return False

                device = self.devices[device_id]

                # Remove from database
                with sqlite3.connect(self.db_path) as conn:
                    conn.execute("DELETE FROM devices WHERE id = ?", (device_id,))
                    conn.execute(
                        "DELETE FROM device_telemetry WHERE device_id = ?", (device_id,)
                    )
                    conn.execute(
                        "DELETE FROM device_events WHERE device_id = ?", (device_id,)
                    )
                    conn.commit()

                # Remove from memory
                del self.devices[device_id]

                # Notify handlers
                self._notify_discovery_handlers(device, "unregistered")

                logger.info(f"Device {device_id} unregistered successfully")
                return True

        except Exception as e:
            logger.error(f"Failed to unregister device {device_id}: {e}")
            return False

    def get_device(self, device_id: str) -> Optional[Device]:
        """Get device by ID."""
        return self.devices.get(device_id)

    def get_devices(
        self,
        device_type: Optional[DeviceType] = None,
        status: Optional[DeviceStatus] = None,
        location: Optional[Dict[str, str]] = None,
    ) -> List[Device]:
        """Get devices with optional filtering."""
        devices = list(self.devices.values())

        if device_type:
            devices = [d for d in devices if d.device_type == device_type]

        if status:
            devices = [d for d in devices if d.status == status]

        if location:
            devices = [
                d for d in devices if self._location_matches(d.location, location)
            ]

        return devices

    def _location_matches(
        self, device_location: DeviceLocation, filter_location: Dict[str, str]
    ) -> bool:
        """Check if device location matches filter."""
        for key, value in filter_location.items():
            if hasattr(device_location, key):
                if getattr(device_location, key) != value:
                    return False
        return True

    def discover_devices(
        self, protocol: CommunicationProtocol, address_range: Optional[str] = None
    ) -> List[Device]:
        """Discover devices on the network."""
        discovered_devices = []

        try:
            # Get appropriate driver for protocol
            driver = self._get_driver_for_protocol(protocol)
            if not driver:
                logger.error(f"No driver available for protocol {protocol}")
                return discovered_devices

            # Perform discovery
            discovered = driver.discover(address_range)

            for device_info in discovered:
                # Create device object
                device = self._create_device_from_discovery(device_info, protocol)

                # Register if not already registered
                if device.id not in self.devices:
                    if self.register_device(device):
                        discovered_devices.append(device)
                else:
                    # Update existing device
                    self.update_device(device.id, {"last_seen": datetime.utcnow()})
                    discovered_devices.append(self.devices[device.id])

            logger.info(
                f"Discovered {len(discovered_devices)} devices using {protocol}"
            )

        except Exception as e:
            logger.error(f"Device discovery failed: {e}")

        return discovered_devices

    def _get_driver_for_protocol(
        self, protocol: CommunicationProtocol
    ) -> Optional[Any]:
        """Get driver for communication protocol."""
        driver_name = f"{protocol.value}_driver"
        return self.drivers.get(driver_name)

    def _create_device_from_discovery(
        self, device_info: Dict[str, Any], protocol: CommunicationProtocol
    ) -> Device:
        """Create Device object from discovery information."""
        device_id = device_info.get("id", str(uuid.uuid4()))

        return Device(
            id=device_id,
            name=device_info.get("name", f"Unknown Device {device_id}"),
            device_type=DeviceType(device_info.get("type", "sensor")),
            status=DeviceStatus.ONLINE,
            location=DeviceLocation(
                building_id=device_info.get("building_id", "unknown"),
                floor_id=device_info.get("floor_id", "unknown"),
                room_id=device_info.get("room_id"),
                x_coordinate=device_info.get("x"),
                y_coordinate=device_info.get("y"),
                z_coordinate=device_info.get("z"),
            ),
            metadata=DeviceMetadata(
                manufacturer=device_info.get("manufacturer", "Unknown"),
                model=device_info.get("model", "Unknown"),
                serial_number=device_info.get("serial_number", device_id),
                firmware_version=device_info.get("firmware_version"),
                tags=device_info.get("tags", []),
            ),
            connection=DeviceConnection(
                protocol=protocol,
                address=device_info.get("address", ""),
                port=device_info.get("port"),
                credentials=device_info.get("credentials"),
                timeout=device_info.get("timeout", 30),
            ),
            capabilities=[
                DeviceCapability(**cap) for cap in device_info.get("capabilities", [])
            ],
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            driver_name=f"{protocol.value}_driver",
        )

    def register_driver(self, protocol: CommunicationProtocol, driver: Any) -> bool:
        """Register a driver for a communication protocol."""
        try:
            driver_name = f"{protocol.value}_driver"
            self.drivers[driver_name] = driver
            logger.info(f"Driver registered for protocol {protocol}")
            return True
        except Exception as e:
            logger.error(f"Failed to register driver for {protocol}: {e}")
            return False

    def add_discovery_handler(self, handler: callable) -> None:
        """Add a discovery event handler."""
        self.discovery_handlers.append(handler)

    def add_telemetry_handler(self, handler: callable) -> None:
        """Add a telemetry event handler."""
        self.telemetry_handlers.append(handler)

    def _notify_discovery_handlers(self, device: Device, event_type: str) -> None:
        """Notify discovery handlers of events."""
        for handler in self.discovery_handlers:
            try:
                handler(device, event_type)
            except Exception as e:
                logger.error(f"Discovery handler error: {e}")

    def _notify_telemetry_handlers(
        self, device_id: str, capability: str, value: Any, timestamp: datetime
    ) -> None:
        """Notify telemetry handlers of events."""
        for handler in self.telemetry_handlers:
            try:
                handler(device_id, capability, value, timestamp)
            except Exception as e:
                logger.error(f"Telemetry handler error: {e}")

    def _validate_device(self, device: Device) -> bool:
        """Validate device information."""
        if not device.id or not device.name:
            return False

        if not device.location.building_id or not device.location.floor_id:
            return False

        if not device.connection.address:
            return False

        return True

    def _start_background_tasks(self):
        """Start background tasks."""
        # Start device health monitoring
        asyncio.create_task(self._monitor_device_health())

        # Start telemetry collection
        asyncio.create_task(self._collect_telemetry())

    async def _monitor_device_health(self):
        """Monitor device health and update status."""
        while True:
            try:
                for device in self.devices.values():
                    # Check if device is responding
                    is_online = await self._check_device_health(device)

                    new_status = (
                        DeviceStatus.ONLINE if is_online else DeviceStatus.OFFLINE
                    )
                    if device.status != new_status:
                        self.update_device(device.id, {"status": new_status})

                await asyncio.sleep(60)  # Check every minute

            except Exception as e:
                logger.error(f"Device health monitoring error: {e}")
                await asyncio.sleep(60)

    async def _check_device_health(self, device: Device) -> bool:
        """Check if device is responding."""
        try:
            driver = self._get_driver_for_protocol(device.connection.protocol)
            if driver and hasattr(driver, "ping"):
                return await driver.ping(device.connection.address)
            return True  # Assume online if no ping method
        except Exception:
            return False

    async def _collect_telemetry(self):
        """Collect telemetry data from devices."""
        while True:
            try:
                for device in self.devices.values():
                    if device.status == DeviceStatus.ONLINE:
                        await self._collect_device_telemetry(device)

                await asyncio.sleep(30)  # Collect every 30 seconds

            except Exception as e:
                logger.error(f"Telemetry collection error: {e}")
                await asyncio.sleep(30)

    async def _collect_device_telemetry(self, device: Device):
        """Collect telemetry from a specific device."""
        try:
            driver = self._get_driver_for_protocol(device.connection.protocol)
            if not driver or not hasattr(driver, "read_capabilities"):
                return

            # Read all capabilities
            telemetry_data = await driver.read_capabilities(device.connection.address)

            # Store telemetry data
            timestamp = datetime.utcnow()
            for capability_name, value in telemetry_data.items():
                self._store_telemetry(device.id, capability_name, value, timestamp)

                # Notify handlers
                self._notify_telemetry_handlers(
                    device.id, capability_name, value, timestamp
                )

            # Update last seen
            self.update_device(device.id, {"last_seen": timestamp})

        except Exception as e:
            logger.error(f"Failed to collect telemetry from {device.id}: {e}")

    def _store_telemetry(
        self, device_id: str, capability_name: str, value: Any, timestamp: datetime
    ):
        """Store telemetry data in database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """
                    INSERT INTO device_telemetry (device_id, capability_name, value, timestamp)
                    VALUES (?, ?, ?, ?)
                """,
                    (
                        device_id,
                        capability_name,
                        json.dumps(value),
                        timestamp.isoformat(),
                    ),
                )
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to store telemetry: {e}")

    def get_telemetry(
        self,
        device_id: str,
        capability_name: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> List[Dict[str, Any]]:
        """Get telemetry data for a device."""
        try:
            query = "SELECT * FROM device_telemetry WHERE device_id = ?"
            params = [device_id]

            if capability_name:
                query += " AND capability_name = ?"
                params.append(capability_name)

            if start_time:
                query += " AND timestamp >= ?"
                params.append(start_time.isoformat())

            if end_time:
                query += " AND timestamp <= ?"
                params.append(end_time.isoformat())

            query += " ORDER BY timestamp DESC LIMIT 1000"

            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(query, params)
                return [
                    {
                        "device_id": row[0],
                        "capability_name": row[1],
                        "value": json.loads(row[2]),
                        "timestamp": datetime.fromisoformat(row[3]),
                    }
                    for row in cursor.fetchall()
                ]

        except Exception as e:
            logger.error(f"Failed to get telemetry: {e}")
            return []

    def export_devices(self, format: str = "json") -> str:
        """Export device registry."""
        try:
            devices_data = [asdict(device) for device in self.devices.values()]

            if format.lower() == "json":
                return json.dumps(devices_data, indent=2, default=str)
            elif format.lower() == "yaml":
                return yaml.dump(devices_data, default_flow_style=False)
            else:
                raise ValueError(f"Unsupported format: {format}")

        except Exception as e:
            logger.error(f"Failed to export devices: {e}")
            return ""

    def import_devices(self, data: str, format: str = "json") -> int:
        """Import devices from data."""
        try:
            if format.lower() == "json":
                devices_data = json.loads(data)
            elif format.lower() == "yaml":
                devices_data = yaml.safe_load(data)
            else:
                raise ValueError(f"Unsupported format: {format}")

            imported_count = 0
            for device_data in devices_data:
                # Convert datetime strings back to datetime objects
                for key in ["created_at", "updated_at", "last_seen"]:
                    if key in device_data and device_data[key]:
                        device_data[key] = datetime.fromisoformat(device_data[key])

                # Create device object
                device = Device(**device_data)

                # Register device
                if self.register_device(device):
                    imported_count += 1

            logger.info(f"Imported {imported_count} devices")
            return imported_count

        except Exception as e:
            logger.error(f"Failed to import devices: {e}")
            return 0


# Example driver interface
class BaseDriver:
    """Base class for device drivers."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config

    async def discover(
        self, address_range: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Discover devices on the network."""
        raise NotImplementedError

    async def ping(self, address: str) -> bool:
        """Ping device to check if it's online."""
        raise NotImplementedError

    async def read_capabilities(self, address: str) -> Dict[str, Any]:
        """Read all capabilities from device."""
        raise NotImplementedError

    async def write_capability(self, address: str, capability: str, value: Any) -> bool:
        """Write value to device capability."""
        raise NotImplementedError


# Example BACnet driver
class BACnetDriver(BaseDriver):
    """BACnet protocol driver."""

    async def discover(
        self, address_range: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Discover BACnet devices."""
        # Implementation would use BACnet library
        return []

    async def ping(self, address: str) -> bool:
        """Ping BACnet device."""
        # Implementation would use BACnet library
        return True

    async def read_capabilities(self, address: str) -> Dict[str, Any]:
        """Read BACnet device capabilities."""
        # Implementation would use BACnet library
        return {}


# Example Modbus driver
class ModbusDriver(BaseDriver):
    """Modbus protocol driver."""

    async def discover(
        self, address_range: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Discover Modbus devices."""
        # Implementation would use Modbus library
        return []

    async def ping(self, address: str) -> bool:
        """Ping Modbus device."""
        # Implementation would use Modbus library
        return True

    async def read_capabilities(self, address: str) -> Dict[str, Any]:
        """Read Modbus device capabilities."""
        # Implementation would use Modbus library
        return {}


if __name__ == "__main__":
    # Example usage
    registry = DeviceRegistry()

    # Register drivers
    registry.register_driver(CommunicationProtocol.BACNET, BACnetDriver({}))
    registry.register_driver(CommunicationProtocol.MODBUS, ModbusDriver({}))

    # Discover devices
    discovered = registry.discover_devices(CommunicationProtocol.BACNET)
    print(f"Discovered {len(discovered)} devices")

    # Get all devices
    devices = registry.get_devices()
    print(f"Total devices: {len(devices)}")

    # Export devices
    export_data = registry.export_devices("json")
    print(f"Exported {len(export_data)} characters of data")
