"""
SVGX Engine - IoT Integration System

This service provides comprehensive IoT integration capabilities for BIM behavior
systems, enabling real-time sensor data processing, actuator control, and automated
system management.

🎯 **Core IoT Features:**
- Real-time Sensor Data Integration
- Actuator Control and Automation
- IoT Device Management
- Data Streaming and Processing
- Automated Control Systems
- IoT Security and Compliance
- Edge Computing Integration
- Cloud IoT Platform Integration

🏗️ **Enterprise Features:**
- Scalable IoT data pipeline with real-time processing
- Comprehensive device management and monitoring
- Integration with BIM behavior engine
- Advanced security and compliance features
- Performance monitoring and optimization
- Enterprise-grade reliability and fault tolerance
"""

import logging
import asyncio
import time
import uuid
from typing import Dict, List, Any, Optional, Union, Tuple, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import threading
from collections import defaultdict, deque
import json
import ssl
import paho.mqtt.client as mqtt
import websockets
from websockets.server import WebSocketServerProtocol
import hashlib
import hmac

from svgx_engine.utils.performance import PerformanceMonitor
from svgx_engine.utils.errors import BehaviorError, ValidationError

logger = logging.getLogger(__name__)


class IoTDeviceType(Enum):
    """Types of IoT devices supported."""
    SENSOR = "sensor"
    ACTUATOR = "actuator"
    CONTROLLER = "controller"
    GATEWAY = "gateway"
    CAMERA = "camera"
    DISPLAY = "display"


class SensorType(Enum):
    """Types of sensors supported."""
    TEMPERATURE = "temperature"
    HUMIDITY = "humidity"
    PRESSURE = "pressure"
    MOTION = "motion"
    LIGHT = "light"
    SOUND = "sound"
    VIBRATION = "vibration"
    AIR_QUALITY = "air_quality"
    POWER = "power"
    FLOW = "flow"


class ActuatorType(Enum):
    """Types of actuators supported."""
    HVAC = "hvac"
    LIGHTING = "lighting"
    SECURITY = "security"
    ACCESS_CONTROL = "access_control"
    FIRE_SUPPRESSION = "fire_suppression"
    WATER_CONTROL = "water_control"
    ELECTRICAL = "electrical"


class DataQuality(Enum):
    """Data quality levels."""
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"
    UNRELIABLE = "unreliable"


class ControlMode(Enum):
    """Control modes for actuators."""
    MANUAL = "manual"
    AUTOMATIC = "automatic"
    SCHEDULED = "scheduled"
    AI_OPTIMIZED = "ai_optimized"
    EMERGENCY = "emergency"


@dataclass
class IoTDevice:
    """IoT device information."""
    device_id: str
    device_type: IoTDeviceType
    name: str
    location: str
    manufacturer: str
    model: str
    firmware_version: str
    ip_address: str
    mac_address: str
    status: str = "online"
    last_seen: datetime = field(default_factory=datetime.now)
    capabilities: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SensorData:
    """Sensor data point."""
    sensor_id: str
    sensor_type: SensorType
    timestamp: datetime
    value: float
    unit: str
    quality: DataQuality
    location: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ActuatorCommand:
    """Actuator control command."""
    actuator_id: str
    actuator_type: ActuatorType
    command: str
    parameters: Dict[str, Any]
    timestamp: datetime
    priority: int = 1
    mode: ControlMode = ControlMode.AUTOMATIC
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class IoTConfig:
    """Configuration for IoT integration system."""
    # MQTT settings
    mqtt_broker: str = "localhost"
    mqtt_port: int = 1883
    mqtt_username: str = ""
    mqtt_password: str = ""
    mqtt_ssl: bool = False
    
    # WebSocket settings
    websocket_host: str = "localhost"
    websocket_port: int = 8768
    websocket_ssl: bool = False
    
    # Data processing settings
    data_buffer_size: int = 10000
    processing_interval: float = 1.0  # seconds
    data_retention_hours: int = 24
    
    # Security settings
    device_authentication: bool = True
    data_encryption: bool = True
    access_control: bool = True
    
    # Performance settings
    max_concurrent_devices: int = 1000
    max_data_rate: int = 10000  # messages per second
    connection_timeout: int = 30  # seconds


class SensorManager:
    """Manages IoT sensors and sensor data."""
    
    def __init__(self, config: IoTConfig):
        self.config = config
        self.sensors: Dict[str, IoTDevice] = {}
        self.sensor_data: Dict[str, deque] = defaultdict(lambda: deque(maxlen=config.data_buffer_size))
        self.data_processors: Dict[str, Callable] = {}
        self.alert_thresholds: Dict[str, Dict[str, float]] = {}
        
    def register_sensor(self, device: IoTDevice) -> bool:
        """Register a new sensor device."""
        try:
            if device.device_type != IoTDeviceType.SENSOR:
                raise ValueError("Device must be a sensor")
            
            self.sensors[device.device_id] = device
            logger.info(f"Registered sensor: {device.name} ({device.device_id})")
            return True
            
        except Exception as e:
            logger.error(f"Error registering sensor {device.device_id}: {e}")
            return False
    
    def add_sensor_data(self, sensor_id: str, data: SensorData) -> bool:
        """Add sensor data point."""
        try:
            if sensor_id not in self.sensors:
                logger.warning(f"Unknown sensor: {sensor_id}")
                return False
            
            # Store data
            self.sensor_data[sensor_id].append(data)
            
            # Process data if processor exists
            if sensor_id in self.data_processors:
                self.data_processors[sensor_id](data)
            
            # Check alert thresholds
            self._check_alert_thresholds(sensor_id, data)
            
            return True
            
        except Exception as e:
            logger.error(f"Error adding sensor data for {sensor_id}: {e}")
            return False
    
    def get_sensor_data(self, sensor_id: str, hours: int = 24) -> List[SensorData]:
        """Get sensor data for the specified time period."""
        try:
            if sensor_id not in self.sensor_data:
                return []
            
            cutoff_time = datetime.now() - timedelta(hours=hours)
            data = list(self.sensor_data[sensor_id])
            
            # Filter by time
            recent_data = [d for d in data if d.timestamp >= cutoff_time]
            
            return recent_data
            
        except Exception as e:
            logger.error(f"Error getting sensor data for {sensor_id}: {e}")
            return []
    
    def set_data_processor(self, sensor_id: str, processor: Callable):
        """Set a data processor for a sensor."""
        self.data_processors[sensor_id] = processor
        logger.info(f"Set data processor for sensor {sensor_id}")
    
    def set_alert_thresholds(self, sensor_id: str, thresholds: Dict[str, float]):
        """Set alert thresholds for a sensor."""
        self.alert_thresholds[sensor_id] = thresholds
        logger.info(f"Set alert thresholds for sensor {sensor_id}")
    
    def _check_alert_thresholds(self, sensor_id: str, data: SensorData):
        """Check if sensor data exceeds alert thresholds."""
        if sensor_id not in self.alert_thresholds:
            return
        
        thresholds = self.alert_thresholds[sensor_id]
        
        for threshold_name, threshold_value in thresholds.items():
            if data.value > threshold_value:
                logger.warning(f"Alert: {sensor_id} {threshold_name} threshold exceeded: {data.value} > {threshold_value}")
                # In a real implementation, this would trigger alerts/notifications


class ActuatorManager:
    """Manages IoT actuators and control commands."""
    
    def __init__(self, config: IoTConfig):
        self.config = config
        self.actuators: Dict[str, IoTDevice] = {}
        self.control_commands: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.control_handlers: Dict[str, Callable] = {}
        self.actuator_states: Dict[str, Dict[str, Any]] = {}
        
    def register_actuator(self, device: IoTDevice) -> bool:
        """Register a new actuator device."""
        try:
            if device.device_type != IoTDeviceType.ACTUATOR:
                raise ValueError("Device must be an actuator")
            
            self.actuators[device.device_id] = device
            self.actuator_states[device.device_id] = {
                'status': 'idle',
                'last_command': None,
                'current_value': None,
                'target_value': None
            }
            
            logger.info(f"Registered actuator: {device.name} ({device.device_id})")
            return True
            
        except Exception as e:
            logger.error(f"Error registering actuator {device.device_id}: {e}")
            return False
    
    def send_command(self, command: ActuatorCommand) -> bool:
        """Send control command to actuator."""
        try:
            if command.actuator_id not in self.actuators:
                logger.warning(f"Unknown actuator: {command.actuator_id}")
                return False
            
            # Store command
            self.control_commands[command.actuator_id].append(command)
            
            # Execute command if handler exists
            if command.actuator_id in self.control_handlers:
                success = self.control_handlers[command.actuator_id](command)
                if success:
                    self._update_actuator_state(command)
                return success
            
            # Default command execution
            self._update_actuator_state(command)
            logger.info(f"Sent command to actuator {command.actuator_id}: {command.command}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending command to actuator {command.actuator_id}: {e}")
            return False
    
    def get_actuator_state(self, actuator_id: str) -> Optional[Dict[str, Any]]:
        """Get current state of an actuator."""
        return self.actuator_states.get(actuator_id)
    
    def set_control_handler(self, actuator_id: str, handler: Callable):
        """Set a control handler for an actuator."""
        self.control_handlers[actuator_id] = handler
        logger.info(f"Set control handler for actuator {actuator_id}")
    
    def _update_actuator_state(self, command: ActuatorCommand):
        """Update actuator state based on command."""
        if command.actuator_id in self.actuator_states:
            state = self.actuator_states[command.actuator_id]
            state['status'] = 'active'
            state['last_command'] = command
            state['target_value'] = command.parameters.get('target_value')


class MQTTClient:
    """MQTT client for IoT device communication."""
    
    def __init__(self, config: IoTConfig, message_handler: Callable):
        self.config = config
        self.message_handler = message_handler
        self.client = mqtt.Client()
        self.connected = False
        
        # Set up authentication if provided
        if config.mqtt_username and config.mqtt_password:
            self.client.username_pw_set(config.mqtt_username, config.mqtt_password)
        
        # Set up SSL if enabled
        if config.mqtt_ssl:
            self.client.tls_set()
        
        # Set up callbacks
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        self.client.on_disconnect = self._on_disconnect
        
    def connect(self) -> bool:
        """Connect to MQTT broker."""
        try:
            self.client.connect(self.config.mqtt_broker, self.config.mqtt_port, 60)
            self.client.loop_start()
            return True
            
        except Exception as e:
            logger.error(f"Error connecting to MQTT broker: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from MQTT broker."""
        try:
            self.client.loop_stop()
            self.client.disconnect()
            
        except Exception as e:
            logger.error(f"Error disconnecting from MQTT broker: {e}")
    
    def subscribe(self, topic: str):
        """Subscribe to MQTT topic."""
        try:
            self.client.subscribe(topic)
            logger.info(f"Subscribed to topic: {topic}")
            
        except Exception as e:
            logger.error(f"Error subscribing to topic {topic}: {e}")
    
    def publish(self, topic: str, message: str):
        """Publish message to MQTT topic."""
        try:
            self.client.publish(topic, message)
            logger.debug(f"Published to topic {topic}: {message}")
            
        except Exception as e:
            logger.error(f"Error publishing to topic {topic}: {e}")
    
    def _on_connect(self, client, userdata, flags, rc):
        """Handle MQTT connection."""
        if rc == 0:
            self.connected = True
            logger.info("Connected to MQTT broker")
        else:
            logger.error(f"Failed to connect to MQTT broker: {rc}")
    
    def _on_message(self, client, userdata, msg):
        """Handle MQTT message."""
        try:
            topic = msg.topic
            payload = msg.payload.decode('utf-8')
            
            # Parse message
            data = json.loads(payload)
            
            # Forward to message handler
            self.message_handler(topic, data)
            
        except Exception as e:
            logger.error(f"Error handling MQTT message: {e}")
    
    def _on_disconnect(self, client, userdata, rc):
        """Handle MQTT disconnection."""
        self.connected = False
        logger.warning(f"Disconnected from MQTT broker: {rc}")


class IoTIntegrationSystem:
    """
    Comprehensive IoT integration system for BIM behavior systems
    with real-time sensor data processing, actuator control, and automation.
    """
    
    def __init__(self, config: Optional[IoTConfig] = None):
        self.config = config or IoTConfig()
        self.performance_monitor = PerformanceMonitor()
        
        # Initialize managers
        self.sensor_manager = SensorManager(self.config)
        self.actuator_manager = ActuatorManager(self.config)
        
        # MQTT client
        self.mqtt_client = None
        self.websocket_server = None
        
        # Device registry
        self.devices: Dict[str, IoTDevice] = {}
        self.device_status: Dict[str, str] = {}
        
        # Data processing
        self.data_processors: Dict[str, Callable] = {}
        self.alert_handlers: Dict[str, Callable] = {}
        
        # Processing state
        self.running = False
        self.processing_thread = None
        
        # Statistics
        self.iot_stats = {
            'total_devices': 0,
            'online_devices': 0,
            'total_sensor_readings': 0,
            'total_actuator_commands': 0,
            'alerts_generated': 0,
            'data_processing_time': 0.0
        }
        
        logger.info("IoT integration system initialized")
    
    async def start_system(self):
        """Start the IoT integration system."""
        try:
            # Start MQTT client
            self.mqtt_client = MQTTClient(self.config, self._handle_mqtt_message)
            if not self.mqtt_client.connect():
                raise Exception("Failed to connect to MQTT broker")
            
            # Start WebSocket server
            self.websocket_server = await websockets.serve(
                self._handle_websocket,
                self.config.websocket_host,
                self.config.websocket_port
            )
            
            # Start processing
            self.running = True
            self.processing_thread = threading.Thread(target=self._processing_loop)
            self.processing_thread.start()
            
            logger.info("IoT integration system started")
            
        except Exception as e:
            logger.error(f"Error starting IoT integration system: {e}")
    
    async def stop_system(self):
        """Stop the IoT integration system."""
        try:
            self.running = False
            
            if self.mqtt_client:
                self.mqtt_client.disconnect()
            
            if self.websocket_server:
                self.websocket_server.close()
                await self.websocket_server.wait_closed()
            
            if self.processing_thread:
                self.processing_thread.join()
            
            logger.info("IoT integration system stopped")
            
        except Exception as e:
            logger.error(f"Error stopping IoT integration system: {e}")
    
    def register_device(self, device: IoTDevice) -> bool:
        """Register an IoT device."""
        try:
            self.devices[device.device_id] = device
            self.device_status[device.device_id] = "online"
            
            # Register with appropriate manager
            if device.device_type == IoTDeviceType.SENSOR:
                self.sensor_manager.register_sensor(device)
            elif device.device_type == IoTDeviceType.ACTUATOR:
                self.actuator_manager.register_actuator(device)
            
            self.iot_stats['total_devices'] += 1
            self.iot_stats['online_devices'] += 1
            
            # Subscribe to device topics
            if self.mqtt_client:
                self.mqtt_client.subscribe(f"device/{device.device_id}/data")
                self.mqtt_client.subscribe(f"device/{device.device_id}/status")
            
            logger.info(f"Registered device: {device.name} ({device.device_id})")
            return True
            
        except Exception as e:
            logger.error(f"Error registering device {device.device_id}: {e}")
            return False
    
    def add_sensor_data(self, sensor_id: str, data: SensorData) -> bool:
        """Add sensor data."""
        try:
            success = self.sensor_manager.add_sensor_data(sensor_id, data)
            if success:
                self.iot_stats['total_sensor_readings'] += 1
            
            return success
            
        except Exception as e:
            logger.error(f"Error adding sensor data: {e}")
            return False
    
    def send_actuator_command(self, command: ActuatorCommand) -> bool:
        """Send actuator command."""
        try:
            success = self.actuator_manager.send_command(command)
            if success:
                self.iot_stats['total_actuator_commands'] += 1
                
                # Publish command to MQTT
                if self.mqtt_client:
                    topic = f"device/{command.actuator_id}/command"
                    message = json.dumps({
                        'command': command.command,
                        'parameters': command.parameters,
                        'timestamp': command.timestamp.isoformat(),
                        'priority': command.priority,
                        'mode': command.mode.value
                    })
                    self.mqtt_client.publish(topic, message)
            
            return success
            
        except Exception as e:
            logger.error(f"Error sending actuator command: {e}")
            return False
    
    def set_data_processor(self, device_id: str, processor: Callable):
        """Set data processor for a device."""
        self.data_processors[device_id] = processor
        
        if device_id in self.sensor_manager.sensors:
            self.sensor_manager.set_data_processor(device_id, processor)
        
        logger.info(f"Set data processor for device {device_id}")
    
    def set_alert_handler(self, alert_type: str, handler: Callable):
        """Set alert handler for a specific alert type."""
        self.alert_handlers[alert_type] = handler
        logger.info(f"Set alert handler for {alert_type}")
    
    def get_device_status(self, device_id: str) -> Optional[str]:
        """Get status of a device."""
        return self.device_status.get(device_id)
    
    def get_sensor_data(self, sensor_id: str, hours: int = 24) -> List[SensorData]:
        """Get sensor data."""
        return self.sensor_manager.get_sensor_data(sensor_id, hours)
    
    def get_actuator_state(self, actuator_id: str) -> Optional[Dict[str, Any]]:
        """Get actuator state."""
        return self.actuator_manager.get_actuator_state(actuator_id)
    
    def _handle_mqtt_message(self, topic: str, data: Dict[str, Any]):
        """Handle incoming MQTT messages."""
        try:
            # Parse topic to get device ID and message type
            parts = topic.split('/')
            if len(parts) >= 3:
                device_id = parts[1]
                message_type = parts[2]
                
                if message_type == "data" and device_id in self.sensor_manager.sensors:
                    # Handle sensor data
                    sensor_data = SensorData(
                        sensor_id=device_id,
                        sensor_type=SensorType(data.get('type', 'unknown')),
                        timestamp=datetime.fromisoformat(data.get('timestamp', datetime.now().isoformat())),
                        value=data.get('value', 0.0),
                        unit=data.get('unit', ''),
                        quality=DataQuality(data.get('quality', 'good')),
                        location=data.get('location', ''),
                        metadata=data.get('metadata', {})
                    )
                    self.add_sensor_data(device_id, sensor_data)
                
                elif message_type == "status":
                    # Handle device status update
                    self.device_status[device_id] = data.get('status', 'unknown')
                    
                    if data.get('status') == 'online':
                        self.iot_stats['online_devices'] += 1
                    elif data.get('status') == 'offline':
                        self.iot_stats['online_devices'] = max(0, self.iot_stats['online_devices'] - 1)
            
        except Exception as e:
            logger.error(f"Error handling MQTT message: {e}")
    
    async def _handle_websocket(self, websocket: WebSocketServerProtocol, path: str):
        """Handle WebSocket connections."""
        try:
            async for message in websocket:
                await self._process_websocket_message(websocket, message)
                
        except websockets.exceptions.ConnectionClosed:
            logger.info("WebSocket client disconnected")
        except Exception as e:
            logger.error(f"Error handling WebSocket connection: {e}")
    
    async def _process_websocket_message(self, websocket: WebSocketServerProtocol, message: str):
        """Process WebSocket messages."""
        try:
            data = json.loads(message)
            message_type = data.get('type')
            
            if message_type == 'get_device_status':
                device_id = data.get('device_id')
                status = self.get_device_status(device_id)
                await websocket.send(json.dumps({
                    'type': 'device_status',
                    'device_id': device_id,
                    'status': status
                }))
            
            elif message_type == 'get_sensor_data':
                sensor_id = data.get('sensor_id')
                hours = data.get('hours', 24)
                sensor_data = self.get_sensor_data(sensor_id, hours)
                
                await websocket.send(json.dumps({
                    'type': 'sensor_data',
                    'sensor_id': sensor_id,
                    'data': [
                        {
                            'timestamp': d.timestamp.isoformat(),
                            'value': d.value,
                            'unit': d.unit,
                            'quality': d.quality.value
                        }
                        for d in sensor_data
                    ]
                }))
            
            elif message_type == 'send_command':
                command_data = data.get('command', {})
                command = ActuatorCommand(
                    actuator_id=command_data.get('actuator_id'),
                    actuator_type=ActuatorType(command_data.get('actuator_type')),
                    command=command_data.get('command'),
                    parameters=command_data.get('parameters', {}),
                    timestamp=datetime.now(),
                    priority=command_data.get('priority', 1),
                    mode=ControlMode(command_data.get('mode', 'automatic'))
                )
                
                success = self.send_actuator_command(command)
                await websocket.send(json.dumps({
                    'type': 'command_result',
                    'success': success,
                    'actuator_id': command.actuator_id
                }))
            
        except json.JSONDecodeError:
            logger.error("Invalid JSON message received")
        except Exception as e:
            logger.error(f"Error processing WebSocket message: {e}")
    
    def _processing_loop(self):
        """Main processing loop for IoT system."""
        while self.running:
            try:
                # Process device data
                self._process_device_data()
                
                # Update statistics
                self._update_statistics()
                
                # Check device health
                self._check_device_health()
                
                time.sleep(self.config.processing_interval)
                
            except Exception as e:
                logger.error(f"Error in IoT processing loop: {e}")
                time.sleep(5)
    
    def _process_device_data(self):
        """Process device data."""
        try:
            # Process sensor data
            for sensor_id in self.sensor_manager.sensors:
                if sensor_id in self.data_processors:
                    recent_data = self.sensor_manager.get_sensor_data(sensor_id, hours=1)
                    if recent_data:
                        self.data_processors[sensor_id](recent_data)
            
        except Exception as e:
            logger.error(f"Error processing device data: {e}")
    
    def _update_statistics(self):
        """Update IoT statistics."""
        try:
            # Update online devices count
            online_count = sum(1 for status in self.device_status.values() if status == 'online')
            self.iot_stats['online_devices'] = online_count
            
        except Exception as e:
            logger.error(f"Error updating statistics: {e}")
    
    def _check_device_health(self):
        """Check health of IoT devices."""
        try:
            current_time = datetime.now()
            
            for device_id, device in self.devices.items():
                # Check if device is responding
                if device.last_seen:
                    time_since_last_seen = (current_time - device.last_seen).total_seconds()
                    
                    if time_since_last_seen > self.config.connection_timeout:
                        if self.device_status.get(device_id) == 'online':
                            self.device_status[device_id] = 'offline'
                            logger.warning(f"Device {device_id} marked as offline")
            
        except Exception as e:
            logger.error(f"Error checking device health: {e}")
    
    def get_iot_stats(self) -> Dict[str, Any]:
        """Get IoT system statistics."""
        return {
            'iot_stats': self.iot_stats,
            'total_devices': len(self.devices),
            'online_devices': self.iot_stats['online_devices'],
            'total_sensors': len(self.sensor_manager.sensors),
            'total_actuators': len(self.actuator_manager.actuators),
            'mqtt_connected': self.mqtt_client.connected if self.mqtt_client else False
        }
    
    def clear_device_data(self):
        """Clear device data."""
        for sensor_id in self.sensor_manager.sensor_data:
            self.sensor_manager.sensor_data[sensor_id].clear()
        
        for actuator_id in self.actuator_manager.control_commands:
            self.actuator_manager.control_commands[actuator_id].clear()
        
        logger.info("IoT device data cleared")
    
    def reset_statistics(self):
        """Reset IoT statistics."""
        self.iot_stats = {
            'total_devices': 0,
            'online_devices': 0,
            'total_sensor_readings': 0,
            'total_actuator_commands': 0,
            'alerts_generated': 0,
            'data_processing_time': 0.0
        }
        logger.info("IoT statistics reset") 