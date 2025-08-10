"""
Advanced Device Domain Entity for IoT Management.

Provides comprehensive device lifecycle management, sensor data handling,
and intelligent device behavior modeling following DDD principles.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Union, Set
from enum import Enum
import json
from decimal import Decimal

from domain.value_objects import DeviceId, RoomId, UserId
from domain.events import DomainEvent
from domain.exceptions import InvalidDeviceError, DeviceOperationError, BusinessRuleViolationError


class DeviceType(Enum):
    """IoT device types with capabilities."""
    # Environmental Sensors
    TEMPERATURE_SENSOR = "temperature_sensor"
    HUMIDITY_SENSOR = "humidity_sensor"
    AIR_QUALITY_SENSOR = "air_quality_sensor"
    LIGHT_SENSOR = "light_sensor"
    MOTION_SENSOR = "motion_sensor"
    OCCUPANCY_SENSOR = "occupancy_sensor"
    NOISE_SENSOR = "noise_sensor"
    
    # HVAC Systems
    THERMOSTAT = "thermostat"
    AIR_HANDLER = "air_handler"
    VENTILATION_UNIT = "ventilation_unit"
    
    # Lighting Systems
    SMART_LIGHT = "smart_light"
    LIGHTING_CONTROLLER = "lighting_controller"
    DAYLIGHT_SENSOR = "daylight_sensor"
    
    # Security Systems
    ACCESS_CONTROLLER = "access_controller"
    SECURITY_CAMERA = "security_camera"
    DOOR_SENSOR = "door_sensor"
    WINDOW_SENSOR = "window_sensor"
    
    # Energy Management
    POWER_METER = "power_meter"
    ENERGY_MONITOR = "energy_monitor"
    SMART_OUTLET = "smart_outlet"
    
    # Safety Systems
    SMOKE_DETECTOR = "smoke_detector"
    CO_DETECTOR = "co_detector"
    FIRE_ALARM = "fire_alarm"
    EMERGENCY_LIGHT = "emergency_light"
    
    # Communication & Control
    GATEWAY = "gateway"
    REPEATER = "repeater"
    CONTROLLER = "controller"
    
    # Custom Devices
    CUSTOM = "custom"


class DeviceStatus(Enum):
    """Device operational status."""
    ONLINE = "online"
    OFFLINE = "offline"
    ERROR = "error"
    MAINTENANCE = "maintenance"
    COMMISSIONING = "commissioning"
    DECOMMISSIONED = "decommissioned"
    UNKNOWN = "unknown"


class DeviceCapability(Enum):
    """Device functional capabilities."""
    # Data Collection
    READ_SENSOR = "read_sensor"
    READ_MULTIPLE_SENSORS = "read_multiple_sensors"
    HISTORICAL_DATA = "historical_data"
    
    # Control & Actuation
    BINARY_CONTROL = "binary_control"     # On/Off
    ANALOG_CONTROL = "analog_control"     # Variable control
    MULTI_POINT_CONTROL = "multi_point_control"  # Multiple setpoints
    
    # Communication
    BIDIRECTIONAL_COMM = "bidirectional_comm"
    MESH_NETWORKING = "mesh_networking"
    GATEWAY_FUNCTION = "gateway_function"
    
    # Advanced Features
    SCHEDULING = "scheduling"
    AUTOMATION = "automation"
    LEARNING = "learning"
    PREDICTIVE_MAINTENANCE = "predictive_maintenance"
    
    # Integration
    BMS_INTEGRATION = "bms_integration"
    CLOUD_CONNECTIVITY = "cloud_connectivity"
    API_ACCESS = "api_access"


class DataType(Enum):
    """Sensor data types with units."""
    # Environmental
    TEMPERATURE = "temperature"           # Celsius, Fahrenheit
    HUMIDITY = "humidity"                # Percentage
    PRESSURE = "pressure"                # kPa, PSI
    AIR_QUALITY = "air_quality"          # AQI, PPM
    CO2_LEVEL = "co2_level"              # PPM
    LIGHT_LEVEL = "light_level"          # Lux
    UV_INDEX = "uv_index"                # Index
    
    # Motion & Presence
    MOTION = "motion"                    # Boolean
    OCCUPANCY = "occupancy"              # Count, Boolean
    PRESENCE = "presence"                # Boolean
    
    # Energy & Power
    POWER_CONSUMPTION = "power_consumption"  # Watts
    ENERGY_USAGE = "energy_usage"        # kWh
    VOLTAGE = "voltage"                  # Volts
    CURRENT = "current"                  # Amperes
    
    # Audio & Visual
    NOISE_LEVEL = "noise_level"          # Decibels
    LIGHT_COLOR = "light_color"          # RGB, HSV
    BRIGHTNESS = "brightness"            # Percentage
    
    # Security & Safety
    DOOR_STATUS = "door_status"          # Open, Closed
    WINDOW_STATUS = "window_status"      # Open, Closed
    ALARM_STATUS = "alarm_status"        # Boolean
    SMOKE_LEVEL = "smoke_level"          # PPM
    
    # System
    BATTERY_LEVEL = "battery_level"      # Percentage
    SIGNAL_STRENGTH = "signal_strength"  # dBm, Percentage
    UPTIME = "uptime"                    # Seconds
    ERROR_COUNT = "error_count"          # Count
    
    # Custom
    CUSTOM = "custom"


@dataclass
class SensorReading:
    """Individual sensor reading with metadata."""
    data_type: DataType
    value: Union[float, int, bool, str]
    unit: str
    timestamp: datetime
    quality: float = 1.0  # Quality indicator 0.0-1.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def is_valid(self) -> bool:
        """Check if reading is valid."""
        return 0.0 <= self.quality <= 1.0 and self.timestamp is not None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "data_type": self.data_type.value,
            "value": self.value,
            "unit": self.unit,
            "timestamp": self.timestamp.isoformat(),
            "quality": self.quality,
            "metadata": self.metadata
        }


@dataclass
class DeviceConfiguration:
    """Device configuration settings."""
    sampling_interval: int = 60  # seconds
    reporting_interval: int = 300  # seconds
    alert_thresholds: Dict[str, Dict[str, float]] = field(default_factory=dict)
    automation_rules: List[Dict[str, Any]] = field(default_factory=list)
    communication_settings: Dict[str, Any] = field(default_factory=dict)
    power_settings: Dict[str, Any] = field(default_factory=dict)
    
    def validate(self) -> bool:
        """Validate configuration settings."""
        return (self.sampling_interval > 0 and 
                self.reporting_interval >= self.sampling_interval)


@dataclass
class DeviceHealthMetrics:
    """Device health and performance metrics."""
    uptime_percentage: float = 0.0
    error_rate: float = 0.0
    communication_quality: float = 1.0
    battery_level: Optional[float] = None
    signal_strength: Optional[float] = None
    last_maintenance: Optional[datetime] = None
    maintenance_due: Optional[datetime] = None
    firmware_version: Optional[str] = None
    
    def calculate_health_score(self) -> float:
        """Calculate overall device health score (0.0-1.0)."""
        factors = []
        
        # Uptime factor
        factors.append(self.uptime_percentage / 100.0)
        
        # Error rate factor (inverted)
        factors.append(max(0.0, 1.0 - self.error_rate))
        
        # Communication quality
        factors.append(self.communication_quality)
        
        # Battery factor (if applicable)
        if self.battery_level is not None:
            factors.append(max(0.0, self.battery_level / 100.0))
        
        # Signal strength factor (if applicable)
        if self.signal_strength is not None:
            # Assume signal strength is in dBm (-100 to -30)
            if self.signal_strength < 0:
                normalized_signal = max(0.0, (self.signal_strength + 100) / 70.0)
            else:
                # If percentage
                normalized_signal = self.signal_strength / 100.0
            factors.append(normalized_signal)
        
        return sum(factors) / len(factors) if factors else 0.0


# Domain Events
@dataclass
class DeviceInstalled(DomainEvent):
    """Device installed event."""
    device_id: str
    device_type: str
    room_id: str
    installed_by: str
    installation_date: datetime
    configuration: Dict[str, Any]


@dataclass
class DeviceStatusChanged(DomainEvent):
    """Device status changed event."""
    device_id: str
    old_status: str
    new_status: str
    changed_by: str
    change_reason: str
    timestamp: datetime


@dataclass
class SensorDataReceived(DomainEvent):
    """Sensor data received event."""
    device_id: str
    readings: List[Dict[str, Any]]
    timestamp: datetime
    data_quality: float


@dataclass
class DeviceAlertTriggered(DomainEvent):
    """Device alert triggered event."""
    device_id: str
    alert_type: str
    severity: str
    message: str
    data: Dict[str, Any]
    timestamp: datetime


@dataclass
class DeviceMaintenanceScheduled(DomainEvent):
    """Device maintenance scheduled event."""
    device_id: str
    maintenance_type: str
    scheduled_date: datetime
    scheduled_by: str
    priority: str
    details: str


class IoTDevice:
    """Advanced IoT device entity with comprehensive capabilities."""
    
    def __init__(self, id: DeviceId, room_id: RoomId, name: str, device_id: str,
                 device_type: DeviceType, manufacturer: str, model: str,
                 capabilities: Set[DeviceCapability], created_by: str):
        # Core Identity
        self.id = id
        self.room_id = room_id
        self.name = self._validate_name(name)
        self.device_id = self._validate_device_id(device_id)
        self.device_type = device_type
        
        # Device Information
        self.manufacturer = manufacturer
        self.model = model
        self.capabilities = capabilities
        self.firmware_version: Optional[str] = None
        self.hardware_version: Optional[str] = None
        
        # Status & Health
        self.status = DeviceStatus.COMMISSIONING
        self.health_metrics = DeviceHealthMetrics()
        self.configuration = DeviceConfiguration()
        
        # Data Management
        self.sensor_readings: List[SensorReading] = []
        self.max_readings_history = 1000  # Configurable
        
        # Lifecycle Information
        self.created_at = datetime.now(timezone.utc)
        self.updated_at = self.created_at
        self.created_by = created_by
        self.installed_at: Optional[datetime] = None
        self.commissioned_at: Optional[datetime] = None
        self.last_seen: Optional[datetime] = None
        
        # Relationships
        self.parent_device_id: Optional[DeviceId] = None
        self.child_devices: List[DeviceId] = []
        
        # Metadata & Tags
        self.metadata: Dict[str, Any] = {}
        self.tags: Set[str] = set()
        
        # Domain Events
        self._domain_events: List[DomainEvent] = []
        
        # Add device installed event
        self._add_domain_event(DeviceInstalled(
            device_id=str(self.id),
            device_type=device_type.value,
            room_id=str(room_id),
            installed_by=created_by,
            installation_date=self.created_at,
            configuration={}
        ))
    
    def _validate_name(self, name: str) -> str:
        """Validate device name."""
        if not name or not name.strip():
            raise InvalidDeviceError("Device name cannot be empty")
        
        name = name.strip()
        if len(name) > 200:
            raise InvalidDeviceError("Device name cannot exceed 200 characters")
        
        return name
    
    def _validate_device_id(self, device_id: str) -> str:
        """Validate device identifier."""
        if not device_id or not device_id.strip():
            raise InvalidDeviceError("Device ID cannot be empty")
        
        device_id = device_id.strip().upper()
        if len(device_id) > 50:
            raise InvalidDeviceError("Device ID cannot exceed 50 characters")
        
        # Allow alphanumeric, underscore, and dash
        if not all(c.isalnum() or c in ['_', '-'] for c in device_id):
            raise InvalidDeviceError("Device ID can only contain alphanumeric characters, underscore, and dash")
        
        return device_id
    
    def update_status(self, new_status: DeviceStatus, changed_by: str, reason: str = "") -> None:
        """Update device status with business rules validation."""
        if new_status == self.status:
            return  # No change needed
        
        # Validate status transitions
        valid_transitions = self._get_valid_status_transitions()
        if new_status not in valid_transitions.get(self.status, []):
            raise BusinessRuleViolationError(
                f"Invalid status transition from {self.status.value} to {new_status.value}"
            )
        
        old_status = self.status
        self.status = new_status
        self.updated_at = datetime.now(timezone.utc)
        
        # Update last seen for online status
        if new_status == DeviceStatus.ONLINE:
            self.last_seen = self.updated_at
            if not self.commissioned_at and old_status == DeviceStatus.COMMISSIONING:
                self.commissioned_at = self.updated_at
        
        # Add domain event
        self._add_domain_event(DeviceStatusChanged(
            device_id=str(self.id),
            old_status=old_status.value,
            new_status=new_status.value,
            changed_by=changed_by,
            change_reason=reason,
            timestamp=self.updated_at
        ))
    
    def _get_valid_status_transitions(self) -> Dict[DeviceStatus, List[DeviceStatus]]:
        """Get valid status transitions based on device lifecycle."""
        return {
            DeviceStatus.COMMISSIONING: [DeviceStatus.ONLINE, DeviceStatus.ERROR, DeviceStatus.OFFLINE],
            DeviceStatus.ONLINE: [DeviceStatus.OFFLINE, DeviceStatus.ERROR, DeviceStatus.MAINTENANCE],
            DeviceStatus.OFFLINE: [DeviceStatus.ONLINE, DeviceStatus.ERROR, DeviceStatus.MAINTENANCE, DeviceStatus.DECOMMISSIONED],
            DeviceStatus.ERROR: [DeviceStatus.ONLINE, DeviceStatus.OFFLINE, DeviceStatus.MAINTENANCE],
            DeviceStatus.MAINTENANCE: [DeviceStatus.ONLINE, DeviceStatus.OFFLINE, DeviceStatus.ERROR],
            DeviceStatus.DECOMMISSIONED: [],  # Terminal state
            DeviceStatus.UNKNOWN: [DeviceStatus.ONLINE, DeviceStatus.OFFLINE, DeviceStatus.ERROR]
        }
    
    def add_sensor_reading(self, reading: SensorReading) -> None:
        """Add sensor reading with validation and processing."""
        if not reading.is_valid():
            raise InvalidDeviceError("Invalid sensor reading provided")
        
        # Validate reading is from supported data type
        supported_data_types = self._get_supported_data_types()
        if reading.data_type not in supported_data_types:
            raise InvalidDeviceError(f"Device type {self.device_type.value} does not support {reading.data_type.value} readings")
        
        # Add reading to history
        self.sensor_readings.append(reading)
        
        # Maintain reading history limit
        if len(self.sensor_readings) > self.max_readings_history:
            self.sensor_readings = self.sensor_readings[-self.max_readings_history:]
        
        # Update last seen timestamp
        self.last_seen = reading.timestamp
        self.updated_at = datetime.now(timezone.utc)
        
        # Check for alerts
        self._check_alert_thresholds(reading)
        
        # Add domain event
        self._add_domain_event(SensorDataReceived(
            device_id=str(self.id),
            readings=[reading.to_dict()],
            timestamp=reading.timestamp,
            data_quality=reading.quality
        ))
    
    def add_bulk_sensor_readings(self, readings: List[SensorReading]) -> None:
        """Add multiple sensor readings efficiently."""
        if not readings:
            return
        
        valid_readings = []
        supported_data_types = self._get_supported_data_types()
        
        for reading in readings:
            if reading.is_valid() and reading.data_type in supported_data_types:
                valid_readings.append(reading)
        
        if not valid_readings:
            return
        
        # Add readings
        self.sensor_readings.extend(valid_readings)
        
        # Maintain history limit
        if len(self.sensor_readings) > self.max_readings_history:
            self.sensor_readings = self.sensor_readings[-self.max_readings_history:]
        
        # Update timestamps
        latest_reading = max(valid_readings, key=lambda r: r.timestamp)
        self.last_seen = latest_reading.timestamp
        self.updated_at = datetime.now(timezone.utc)
        
        # Check alerts for all readings
        for reading in valid_readings:
            self._check_alert_thresholds(reading)
        
        # Add domain event
        average_quality = sum(r.quality for r in valid_readings) / len(valid_readings)
        self._add_domain_event(SensorDataReceived(
            device_id=str(self.id),
            readings=[r.to_dict() for r in valid_readings],
            timestamp=latest_reading.timestamp,
            data_quality=average_quality
        ))
    
    def _get_supported_data_types(self) -> Set[DataType]:
        """Get supported data types based on device type."""
        type_mappings = {
            DeviceType.TEMPERATURE_SENSOR: {DataType.TEMPERATURE},
            DeviceType.HUMIDITY_SENSOR: {DataType.HUMIDITY},
            DeviceType.AIR_QUALITY_SENSOR: {DataType.AIR_QUALITY, DataType.CO2_LEVEL},
            DeviceType.LIGHT_SENSOR: {DataType.LIGHT_LEVEL, DataType.UV_INDEX},
            DeviceType.MOTION_SENSOR: {DataType.MOTION, DataType.PRESENCE},
            DeviceType.OCCUPANCY_SENSOR: {DataType.OCCUPANCY, DataType.PRESENCE},
            DeviceType.NOISE_SENSOR: {DataType.NOISE_LEVEL},
            DeviceType.THERMOSTAT: {DataType.TEMPERATURE, DataType.HUMIDITY},
            DeviceType.SMART_LIGHT: {DataType.BRIGHTNESS, DataType.LIGHT_COLOR, DataType.POWER_CONSUMPTION},
            DeviceType.POWER_METER: {DataType.POWER_CONSUMPTION, DataType.VOLTAGE, DataType.CURRENT},
            DeviceType.ENERGY_MONITOR: {DataType.ENERGY_USAGE, DataType.POWER_CONSUMPTION},
            DeviceType.SMOKE_DETECTOR: {DataType.SMOKE_LEVEL, DataType.ALARM_STATUS},
            DeviceType.CO_DETECTOR: {DataType.CO2_LEVEL, DataType.ALARM_STATUS},
            DeviceType.DOOR_SENSOR: {DataType.DOOR_STATUS},
            DeviceType.WINDOW_SENSOR: {DataType.WINDOW_STATUS},
        }
        
        return type_mappings.get(self.device_type, {DataType.CUSTOM})
    
    def _check_alert_thresholds(self, reading: SensorReading) -> None:
        """Check if reading triggers any alerts."""
        data_type_key = reading.data_type.value
        if data_type_key not in self.configuration.alert_thresholds:
            return
        
        thresholds = self.configuration.alert_thresholds[data_type_key]
        
        # Check various threshold types
        for threshold_type, threshold_value in thresholds.items():
            alert_triggered = False
            severity = "info"
            
            if threshold_type == "max" and isinstance(reading.value, (int, float)):
                if reading.value > threshold_value:
                    alert_triggered = True
                    severity = "warning"
            elif threshold_type == "min" and isinstance(reading.value, (int, float)):
                if reading.value < threshold_value:
                    alert_triggered = True
                    severity = "warning"
            elif threshold_type == "critical_max" and isinstance(reading.value, (int, float)):
                if reading.value > threshold_value:
                    alert_triggered = True
                    severity = "critical"
            elif threshold_type == "critical_min" and isinstance(reading.value, (int, float)):
                if reading.value < threshold_value:
                    alert_triggered = True
                    severity = "critical"
            
            if alert_triggered:
                self._trigger_alert(
                    alert_type=f"{data_type_key}_{threshold_type}",
                    severity=severity,
                    message=f"{data_type_key} {threshold_type} threshold exceeded: {reading.value} {reading.unit}",
                    data={
                        "reading": reading.to_dict(),
                        "threshold": threshold_value,
                        "threshold_type": threshold_type
                    }
                )
    
    def _trigger_alert(self, alert_type: str, severity: str, message: str, data: Dict[str, Any]) -> None:
        """Trigger device alert."""
        self._add_domain_event(DeviceAlertTriggered(
            device_id=str(self.id),
            alert_type=alert_type,
            severity=severity,
            message=message,
            data=data,
            timestamp=datetime.now(timezone.utc)
        ))
    
    def update_configuration(self, new_config: DeviceConfiguration, updated_by: str) -> None:
        """Update device configuration with validation."""
        if not new_config.validate():
            raise InvalidDeviceError("Invalid device configuration")
        
        self.configuration = new_config
        self.updated_at = datetime.now(timezone.utc)
    
    def schedule_maintenance(self, maintenance_type: str, scheduled_date: datetime,
                           scheduled_by: str, priority: str = "medium", details: str = "") -> None:
        """Schedule device maintenance."""
        if scheduled_date <= datetime.now(timezone.utc):
            raise BusinessRuleViolationError("Maintenance cannot be scheduled in the past")
        
        self.health_metrics.maintenance_due = scheduled_date
        self.updated_at = datetime.now(timezone.utc)
        
        self._add_domain_event(DeviceMaintenanceScheduled(
            device_id=str(self.id),
            maintenance_type=maintenance_type,
            scheduled_date=scheduled_date,
            scheduled_by=scheduled_by,
            priority=priority,
            details=details
        ))
    
    def get_latest_reading(self, data_type: DataType) -> Optional[SensorReading]:
        """Get latest reading for specific data type."""
        readings = [r for r in self.sensor_readings if r.data_type == data_type]
        return max(readings, key=lambda r: r.timestamp) if readings else None
    
    def get_readings_in_range(self, start_time: datetime, end_time: datetime,
                            data_type: Optional[DataType] = None) -> List[SensorReading]:
        """Get readings within time range."""
        readings = self.sensor_readings
        
        if data_type:
            readings = [r for r in readings if r.data_type == data_type]
        
        return [r for r in readings if start_time <= r.timestamp <= end_time]
    
    def calculate_uptime(self, period_hours: int = 24) -> float:
        """Calculate device uptime percentage for given period."""
        if not self.last_seen:
            return 0.0
        
        period_start = datetime.now(timezone.utc) - timedelta(hours=period_hours)
        
        # Simple uptime calculation based on readings frequency
        recent_readings = self.get_readings_in_range(period_start, datetime.now(timezone.utc))
        
        if not recent_readings:
            return 0.0
        
        # Calculate expected readings based on sampling interval
        expected_readings = (period_hours * 3600) // self.configuration.sampling_interval
        actual_readings = len(recent_readings)
        
        uptime = min(100.0, (actual_readings / expected_readings) * 100.0) if expected_readings > 0 else 0.0
        
        # Update health metrics
        self.health_metrics.uptime_percentage = uptime
        
        return uptime
    
    def is_healthy(self) -> bool:
        """Check if device is healthy based on various factors."""
        health_score = self.health_metrics.calculate_health_score()
        return health_score >= 0.7  # 70% threshold
    
    def add_child_device(self, child_device_id: DeviceId) -> None:
        """Add child device (for gateway/controller devices)."""
        if DeviceCapability.GATEWAY_FUNCTION not in self.capabilities:
            raise BusinessRuleViolationError("Device does not support child devices")
        
        if child_device_id not in self.child_devices:
            self.child_devices.append(child_device_id)
            self.updated_at = datetime.now(timezone.utc)
    
    def remove_child_device(self, child_device_id: DeviceId) -> None:
        """Remove child device."""
        if child_device_id in self.child_devices:
            self.child_devices.remove(child_device_id)
            self.updated_at = datetime.now(timezone.utc)
    
    def add_tag(self, tag: str) -> None:
        """Add tag to device."""
        self.tags.add(tag.lower().strip())
        self.updated_at = datetime.now(timezone.utc)
    
    def remove_tag(self, tag: str) -> None:
        """Remove tag from device."""
        self.tags.discard(tag.lower().strip())
        self.updated_at = datetime.now(timezone.utc)
    
    def update_metadata(self, key: str, value: Any, updated_by: str) -> None:
        """Update device metadata."""
        self.metadata[key] = value
        self.updated_at = datetime.now(timezone.utc)
    
    def get_domain_events(self) -> List[DomainEvent]:
        """Get domain events."""
        return self._domain_events.copy()
    
    def clear_domain_events(self) -> None:
        """Clear domain events."""
        self._domain_events.clear()
    
    def _add_domain_event(self, event: DomainEvent) -> None:
        """Add domain event."""
        self._domain_events.append(event)
    
    def __str__(self) -> str:
        """String representation."""
        return f"IoTDevice(id={self.id}, name={self.name}, type={self.device_type.value}, status={self.status.value})"
    
    def __eq__(self, other) -> bool:
        """Equality based on ID."""
        if not isinstance(other, IoTDevice):
            return False
        return self.id == other.id
    
    def __hash__(self) -> int:
        """Hash based on ID."""
        return hash(self.id)