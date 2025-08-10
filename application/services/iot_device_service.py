"""
Advanced IoT Device Application Service.

Orchestrates IoT device management operations including device lifecycle,
sensor data processing, and intelligent device automation.
"""

import asyncio
from typing import Dict, Any, List, Optional, Set, Union
from datetime import datetime, timezone, timedelta
from dataclasses import asdict
import json

from application.services.base_service import BaseApplicationService
from application.dto.device_dto import (
    CreateDeviceRequest, CreateDeviceResponse,
    DeviceResponse, ListDevicesResponse,
    UpdateDeviceRequest, UpdateDeviceResponse,
    SensorDataRequest, SensorDataResponse,
    DeviceHealthResponse, DeviceControlRequest, DeviceControlResponse
)
from domain.entities.device_entity import (
    IoTDevice, DeviceType, DeviceStatus, DeviceCapability, 
    SensorReading, DataType, DeviceConfiguration
)
from domain.value_objects import DeviceId, RoomId
from domain.repositories import DeviceRepository, RoomRepository, UnitOfWork
from domain.exceptions import DeviceNotFoundError, InvalidDeviceError, BusinessRuleViolationError
from application.exceptions import ApplicationError, ResourceNotFoundError, ValidationError
from infrastructure.services.iot_gateway import IoTGatewayService
from infrastructure.services.device_automation import DeviceAutomationEngine
from infrastructure.services.predictive_maintenance import PredictiveMaintenanceService
from infrastructure.logging.structured_logging import get_logger, log_context
from infrastructure.performance.monitoring import performance_monitor, monitor_performance
from infrastructure.security import require_permission, Permission


logger = get_logger(__name__)


class IoTDeviceApplicationService(BaseApplicationService):
    """Advanced IoT device management service."""
    
    def __init__(self, unit_of_work: UnitOfWork, 
                 iot_gateway: IoTGatewayService,
                 automation_engine: DeviceAutomationEngine,
                 predictive_maintenance: PredictiveMaintenanceService,
                 cache_service=None, event_store=None, message_queue=None, metrics=None):
        super().__init__(unit_of_work, cache_service, event_store, message_queue, metrics)
        
        self.device_repository = unit_of_work.device_repository
        self.room_repository = unit_of_work.room_repository
        self.iot_gateway = iot_gateway
        self.automation_engine = automation_engine
        self.predictive_maintenance = predictive_maintenance
    
    @monitor_performance("device_creation")
    @require_permission(Permission.CREATE_DEVICE)
    def create_device(self, name: str, device_id: str, device_type: DeviceType,
                     room_id: str, manufacturer: str, model: str,
                     capabilities: Set[DeviceCapability], created_by: str,
                     configuration: Optional[Dict[str, Any]] = None) -> CreateDeviceResponse:
        """Create and register new IoT device."""
        with log_context(operation="create_device", device_type=device_type.value):
            try:
                # Validate room exists
                room = self.room_repository.get_by_id(RoomId(room_id))
                if not room:
                    return CreateDeviceResponse(
                        success=False,
                        message=f"Room {room_id} not found",
                        device_id=None
                    )
                
                # Check for duplicate device ID
                existing_device = self.device_repository.get_by_device_id(device_id)
                if existing_device:
                    return CreateDeviceResponse(
                        success=False,
                        message=f"Device with ID {device_id} already exists",
                        device_id=None
                    )
                
                # Create device entity
                device = IoTDevice(
                    id=DeviceId(),
                    room_id=RoomId(room_id),
                    name=name,
                    device_id=device_id,
                    device_type=device_type,
                    manufacturer=manufacturer,
                    model=model,
                    capabilities=capabilities,
                    created_by=created_by
                )
                
                # Apply configuration if provided
                if configuration:
                    device_config = DeviceConfiguration(**configuration)
                    device.update_configuration(device_config, created_by)
                
                # Save device
                with self.unit_of_work:
                    saved_device = self.device_repository.save(device)
                    self.unit_of_work.commit()
                
                # Register with IoT gateway
                self._register_device_with_gateway(saved_device)
                
                # Set up automation rules
                self._setup_device_automation(saved_device)
                
                # Cache device data
                if self.cache_service:
                    self._cache_device(saved_device)
                
                # Publish events
                self._publish_device_events(saved_device)
                
                # Record metrics
                if self.metrics:
                    self.metrics.increment_counter(
                        "devices_created_total",
                        {"device_type": device_type.value, "manufacturer": manufacturer}
                    )
                
                logger.info("IoT device created successfully", extra={
                    "device_id": str(saved_device.id),
                    "device_type": device_type.value,
                    "room_id": room_id
                })
                
                return CreateDeviceResponse(
                    success=True,
                    message="Device created successfully",
                    device_id=str(saved_device.id),
                    device=self._device_to_dict(saved_device)
                )
                
            except InvalidDeviceError as e:
                logger.warning(f"Invalid device data: {e}")
                return CreateDeviceResponse(
                    success=False,
                    message=f"Invalid device data: {str(e)}",
                    device_id=None
                )
            except Exception as e:
                logger.error(f"Device creation failed: {e}")
                return CreateDeviceResponse(
                    success=False,
                    message="Device creation failed due to internal error",
                    device_id=None
                )
    
    @monitor_performance("device_retrieval")
    @require_permission(Permission.READ_DEVICE)
    def get_device(self, device_id: str, include_readings: bool = False,
                  reading_limit: int = 100) -> DeviceResponse:
        """Retrieve device information with optional sensor readings."""
        with log_context(operation="get_device", device_id=device_id):
            try:
                # Try cache first
                if self.cache_service:
                    cached_device = self.cache_service.get(f"device:{device_id}")
                    if cached_device:
                        device_data = json.loads(cached_device)
                        
                        if include_readings:
                            # Get recent readings from database
                            device = self.device_repository.get_by_id(DeviceId(device_id))
                            if device:
                                recent_readings = device.sensor_readings[-reading_limit:] if device.sensor_readings else []
                                device_data["recent_readings"] = [r.to_dict() for r in recent_readings]
                        
                        return DeviceResponse(
                            success=True,
                            device=device_data
                        )
                
                # Get from database
                device = self.device_repository.get_by_id(DeviceId(device_id))
                if not device:
                    return DeviceResponse(
                        success=False,
                        message=f"Device {device_id} not found",
                        device=None
                    )
                
                device_data = self._device_to_dict(device)
                
                if include_readings:
                    recent_readings = device.sensor_readings[-reading_limit:] if device.sensor_readings else []
                    device_data["recent_readings"] = [r.to_dict() for r in recent_readings]
                
                # Cache the result
                if self.cache_service:
                    self.cache_service.set(
                        f"device:{device_id}", 
                        json.dumps(device_data), 
                        ttl=1800  # 30 minutes
                    )
                
                return DeviceResponse(
                    success=True,
                    device=device_data
                )
                
            except Exception as e:
                logger.error(f"Device retrieval failed: {e}")
                return DeviceResponse(
                    success=False,
                    message="Device retrieval failed",
                    device=None
                )
    
    @monitor_performance("device_listing")
    @require_permission(Permission.READ_DEVICE)
    def list_devices(self, room_id: Optional[str] = None, device_type: Optional[DeviceType] = None,
                    status: Optional[DeviceStatus] = None, page: int = 1, page_size: int = 50,
                    include_health: bool = False) -> ListDevicesResponse:
        """List devices with filtering and pagination."""
        with log_context(operation="list_devices"):
            try:
                # Build filters
                filters = {}
                if room_id:
                    filters['room_id'] = RoomId(room_id)
                if device_type:
                    filters['device_type'] = device_type
                if status:
                    filters['status'] = status
                
                # Get devices from repository
                devices = self.device_repository.find_by_criteria(filters, page, page_size)
                total_count = self.device_repository.count_by_criteria(filters)
                
                # Convert to response format
                device_list = []
                for device in devices:
                    device_data = self._device_to_dict(device)
                    
                    if include_health:
                        device_data["health_score"] = device.health_metrics.calculate_health_score()
                        device_data["uptime_percentage"] = device.calculate_uptime()
                        device_data["is_healthy"] = device.is_healthy()
                    
                    device_list.append(device_data)
                
                # Calculate pagination
                total_pages = (total_count + page_size - 1) // page_size
                has_next = page < total_pages
                has_prev = page > 1
                
                return ListDevicesResponse(
                    success=True,
                    devices=device_list,
                    total_count=total_count,
                    page=page,
                    page_size=page_size,
                    total_pages=total_pages,
                    has_next=has_next,
                    has_prev=has_prev
                )
                
            except Exception as e:
                logger.error(f"Device listing failed: {e}")
                return ListDevicesResponse(
                    success=False,
                    message="Device listing failed",
                    devices=[],
                    total_count=0,
                    page=page,
                    page_size=page_size
                )
    
    @monitor_performance("device_update")
    @require_permission(Permission.UPDATE_DEVICE)
    def update_device(self, device_id: str, updates: Dict[str, Any], 
                     updated_by: str) -> UpdateDeviceResponse:
        """Update device information and configuration."""
        with log_context(operation="update_device", device_id=device_id):
            try:
                device = self.device_repository.get_by_id(DeviceId(device_id))
                if not device:
                    return UpdateDeviceResponse(
                        success=False,
                        message=f"Device {device_id} not found"
                    )
                
                # Apply updates
                if "name" in updates:
                    device.name = device._validate_name(updates["name"])
                
                if "configuration" in updates:
                    new_config = DeviceConfiguration(**updates["configuration"])
                    device.update_configuration(new_config, updated_by)
                
                if "metadata" in updates:
                    for key, value in updates["metadata"].items():
                        device.update_metadata(key, value, updated_by)
                
                if "tags" in updates:
                    # Replace tags
                    device.tags = set(tag.lower().strip() for tag in updates["tags"])
                
                # Save changes
                with self.unit_of_work:
                    updated_device = self.device_repository.save(device)
                    self.unit_of_work.commit()
                
                # Update IoT gateway configuration
                self._update_gateway_configuration(updated_device)
                
                # Invalidate cache
                if self.cache_service:
                    self.cache_service.delete(f"device:{device_id}")
                
                # Publish events
                self._publish_device_events(updated_device)
                
                return UpdateDeviceResponse(
                    success=True,
                    message="Device updated successfully"
                )
                
            except (InvalidDeviceError, BusinessRuleViolationError) as e:
                logger.warning(f"Device update validation failed: {e}")
                return UpdateDeviceResponse(
                    success=False,
                    message=str(e)
                )
            except Exception as e:
                logger.error(f"Device update failed: {e}")
                return UpdateDeviceResponse(
                    success=False,
                    message="Device update failed"
                )
    
    @monitor_performance("sensor_data_processing")
    @require_permission(Permission.UPDATE_DEVICE)
    def process_sensor_data(self, device_id: str, sensor_data: List[Dict[str, Any]]) -> SensorDataResponse:
        """Process incoming sensor data from IoT device."""
        with log_context(operation="process_sensor_data", device_id=device_id):
            try:
                device = self.device_repository.get_by_id(DeviceId(device_id))
                if not device:
                    return SensorDataResponse(
                        success=False,
                        message=f"Device {device_id} not found",
                        readings_processed=0
                    )
                
                # Convert data to sensor readings
                readings = []
                for data in sensor_data:
                    try:
                        reading = SensorReading(
                            data_type=DataType(data["data_type"]),
                            value=data["value"],
                            unit=data.get("unit", ""),
                            timestamp=datetime.fromisoformat(data["timestamp"]) if isinstance(data["timestamp"], str) else data["timestamp"],
                            quality=data.get("quality", 1.0),
                            metadata=data.get("metadata", {})
                        )
                        readings.append(reading)
                    except (ValueError, KeyError) as e:
                        logger.warning(f"Invalid sensor reading format: {e}")
                        continue
                
                if not readings:
                    return SensorDataResponse(
                        success=False,
                        message="No valid sensor readings provided",
                        readings_processed=0
                    )
                
                # Add readings to device
                device.add_bulk_sensor_readings(readings)
                
                # Update device status if it was offline
                if device.status == DeviceStatus.OFFLINE:
                    device.update_status(DeviceStatus.ONLINE, "system", "Sensor data received")
                
                # Save device
                with self.unit_of_work:
                    updated_device = self.device_repository.save(device)
                    self.unit_of_work.commit()
                
                # Process automation rules
                self._process_automation_rules(updated_device, readings)
                
                # Run predictive maintenance analysis
                self._analyze_predictive_maintenance(updated_device, readings)
                
                # Update cache
                if self.cache_service:
                    self.cache_service.delete(f"device:{device_id}")
                
                # Publish events
                self._publish_device_events(updated_device)
                
                # Record metrics
                if self.metrics:
                    self.metrics.increment_counter(
                        "sensor_readings_processed_total",
                        {"device_type": device.device_type.value},
                        len(readings)
                    )
                
                return SensorDataResponse(
                    success=True,
                    message="Sensor data processed successfully",
                    readings_processed=len(readings)
                )
                
            except Exception as e:
                logger.error(f"Sensor data processing failed: {e}")
                return SensorDataResponse(
                    success=False,
                    message="Sensor data processing failed",
                    readings_processed=0
                )
    
    @monitor_performance("device_control")
    @require_permission(Permission.CONTROL_DEVICE)
    def control_device(self, device_id: str, control_command: Dict[str, Any],
                      controlled_by: str) -> DeviceControlResponse:
        """Send control command to IoT device."""
        with log_context(operation="control_device", device_id=device_id):
            try:
                device = self.device_repository.get_by_id(DeviceId(device_id))
                if not device:
                    return DeviceControlResponse(
                        success=False,
                        message=f"Device {device_id} not found"
                    )
                
                # Check if device supports control
                if not any(cap in device.capabilities for cap in [
                    DeviceCapability.BINARY_CONTROL,
                    DeviceCapability.ANALOG_CONTROL,
                    DeviceCapability.MULTI_POINT_CONTROL
                ]):
                    return DeviceControlResponse(
                        success=False,
                        message="Device does not support control operations"
                    )
                
                # Check device status
                if device.status not in [DeviceStatus.ONLINE, DeviceStatus.MAINTENANCE]:
                    return DeviceControlResponse(
                        success=False,
                        message=f"Device is {device.status.value} and cannot be controlled"
                    )
                
                # Send control command via IoT gateway
                control_result = await self._send_control_command(device, control_command)
                
                if control_result["success"]:
                    # Log control action
                    device.update_metadata("last_control_command", {
                        "command": control_command,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "controlled_by": controlled_by,
                        "result": control_result
                    }, controlled_by)
                    
                    # Save device
                    with self.unit_of_work:
                        self.device_repository.save(device)
                        self.unit_of_work.commit()
                    
                    # Record metrics
                    if self.metrics:
                        self.metrics.increment_counter(
                            "device_control_commands_total",
                            {"device_type": device.device_type.value, "status": "success"}
                        )
                    
                    return DeviceControlResponse(
                        success=True,
                        message="Control command executed successfully",
                        result=control_result.get("data")
                    )
                else:
                    # Record failed control attempt
                    if self.metrics:
                        self.metrics.increment_counter(
                            "device_control_commands_total",
                            {"device_type": device.device_type.value, "status": "failed"}
                        )
                    
                    return DeviceControlResponse(
                        success=False,
                        message=f"Control command failed: {control_result.get('error', 'Unknown error')}"
                    )
                
            except Exception as e:
                logger.error(f"Device control failed: {e}")
                return DeviceControlResponse(
                    success=False,
                    message="Device control failed"
                )
    
    @monitor_performance("device_health_check")
    @require_permission(Permission.READ_DEVICE)
    def get_device_health(self, device_id: str) -> DeviceHealthResponse:
        """Get comprehensive device health information."""
        with log_context(operation="get_device_health", device_id=device_id):
            try:
                device = self.device_repository.get_by_id(DeviceId(device_id))
                if not device:
                    return DeviceHealthResponse(
                        success=False,
                        message=f"Device {device_id} not found",
                        health_data=None
                    )
                
                # Calculate current health metrics
                health_score = device.health_metrics.calculate_health_score()
                uptime_percentage = device.calculate_uptime()
                
                # Get recent readings for data quality analysis
                recent_readings = device.get_readings_in_range(
                    datetime.now(timezone.utc) - timedelta(hours=24),
                    datetime.now(timezone.utc)
                )
                
                # Calculate data quality metrics
                avg_data_quality = (
                    sum(r.quality for r in recent_readings) / len(recent_readings)
                    if recent_readings else 0.0
                )
                
                # Get predictive maintenance insights
                maintenance_insights = self.predictive_maintenance.analyze_device(device)
                
                health_data = {
                    "device_id": device_id,
                    "overall_health_score": health_score,
                    "health_status": "healthy" if health_score >= 0.7 else "degraded" if health_score >= 0.4 else "unhealthy",
                    "uptime_percentage": uptime_percentage,
                    "data_quality_score": avg_data_quality,
                    "last_seen": device.last_seen.isoformat() if device.last_seen else None,
                    "status": device.status.value,
                    "metrics": {
                        "uptime_percentage": device.health_metrics.uptime_percentage,
                        "error_rate": device.health_metrics.error_rate,
                        "communication_quality": device.health_metrics.communication_quality,
                        "battery_level": device.health_metrics.battery_level,
                        "signal_strength": device.health_metrics.signal_strength,
                        "firmware_version": device.health_metrics.firmware_version
                    },
                    "recent_readings_count": len(recent_readings),
                    "maintenance_insights": maintenance_insights,
                    "alerts": self._get_active_alerts(device),
                    "recommendations": self._get_health_recommendations(device, health_score, uptime_percentage)
                }
                
                return DeviceHealthResponse(
                    success=True,
                    health_data=health_data
                )
                
            except Exception as e:
                logger.error(f"Device health check failed: {e}")
                return DeviceHealthResponse(
                    success=False,
                    message="Device health check failed",
                    health_data=None
                )
    
    async def _send_control_command(self, device: IoTDevice, command: Dict[str, Any]) -> Dict[str, Any]:
        """Send control command to device via IoT gateway."""
        try:
            result = await self.iot_gateway.send_command(
                device_id=device.device_id,
                command=command,
                timeout=30
            )
            return result
        except Exception as e:
            logger.error(f"IoT gateway command failed: {e}")
            return {"success": False, "error": str(e)}
    
    def _register_device_with_gateway(self, device: IoTDevice) -> None:
        """Register device with IoT gateway."""
        try:
            asyncio.create_task(self.iot_gateway.register_device(
                device_id=device.device_id,
                device_type=device.device_type.value,
                capabilities=list(device.capabilities),
                configuration=asdict(device.configuration)
            ))
        except Exception as e:
            logger.warning(f"Failed to register device with gateway: {e}")
    
    def _update_gateway_configuration(self, device: IoTDevice) -> None:
        """Update device configuration in IoT gateway."""
        try:
            asyncio.create_task(self.iot_gateway.update_device_configuration(
                device_id=device.device_id,
                configuration=asdict(device.configuration)
            ))
        except Exception as e:
            logger.warning(f"Failed to update gateway configuration: {e}")
    
    def _setup_device_automation(self, device: IoTDevice) -> None:
        """Set up automation rules for device."""
        try:
            self.automation_engine.setup_device_rules(device)
        except Exception as e:
            logger.warning(f"Failed to setup device automation: {e}")
    
    def _process_automation_rules(self, device: IoTDevice, readings: List[SensorReading]) -> None:
        """Process automation rules based on sensor readings."""
        try:
            self.automation_engine.process_readings(device, readings)
        except Exception as e:
            logger.warning(f"Failed to process automation rules: {e}")
    
    def _analyze_predictive_maintenance(self, device: IoTDevice, readings: List[SensorReading]) -> None:
        """Analyze device for predictive maintenance."""
        try:
            self.predictive_maintenance.analyze_readings(device, readings)
        except Exception as e:
            logger.warning(f"Failed to analyze predictive maintenance: {e}")
    
    def _get_active_alerts(self, device: IoTDevice) -> List[Dict[str, Any]]:
        """Get active alerts for device."""
        # This would typically query an alerts system
        # For now, return placeholder data
        return []
    
    def _get_health_recommendations(self, device: IoTDevice, health_score: float, uptime: float) -> List[str]:
        """Get health improvement recommendations."""
        recommendations = []
        
        if health_score < 0.7:
            recommendations.append("Overall device health is poor - consider maintenance")
        
        if uptime < 90.0:
            recommendations.append("Device uptime is low - check connectivity and power")
        
        if device.health_metrics.battery_level and device.health_metrics.battery_level < 20:
            recommendations.append("Battery level is low - schedule battery replacement")
        
        if device.health_metrics.signal_strength and device.health_metrics.signal_strength < -80:
            recommendations.append("Signal strength is weak - check network connectivity")
        
        if device.health_metrics.error_rate > 0.1:
            recommendations.append("Error rate is high - investigate device issues")
        
        return recommendations
    
    def _device_to_dict(self, device: IoTDevice) -> Dict[str, Any]:
        """Convert device entity to dictionary."""
        return {
            "id": str(device.id),
            "room_id": str(device.room_id),
            "name": device.name,
            "device_id": device.device_id,
            "device_type": device.device_type.value,
            "manufacturer": device.manufacturer,
            "model": device.model,
            "status": device.status.value,
            "capabilities": [cap.value for cap in device.capabilities],
            "firmware_version": device.firmware_version,
            "hardware_version": device.hardware_version,
            "configuration": asdict(device.configuration),
            "health_metrics": asdict(device.health_metrics),
            "created_at": device.created_at.isoformat(),
            "updated_at": device.updated_at.isoformat(),
            "installed_at": device.installed_at.isoformat() if device.installed_at else None,
            "commissioned_at": device.commissioned_at.isoformat() if device.commissioned_at else None,
            "last_seen": device.last_seen.isoformat() if device.last_seen else None,
            "created_by": device.created_by,
            "tags": list(device.tags),
            "metadata": device.metadata,
            "parent_device_id": str(device.parent_device_id) if device.parent_device_id else None,
            "child_devices": [str(child_id) for child_id in device.child_devices],
            "reading_count": len(device.sensor_readings)
        }
    
    def _cache_device(self, device: IoTDevice) -> None:
        """Cache device data."""
        if self.cache_service:
            device_data = self._device_to_dict(device)
            cache_key = f"device:{device.id}"
            self.cache_service.set(cache_key, json.dumps(device_data), ttl=1800)