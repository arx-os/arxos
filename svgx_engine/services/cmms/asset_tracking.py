"""
Asset Tracking Service for CMMS Integration

This module provides comprehensive asset tracking capabilities including:
- Real-time asset monitoring
- Location tracking and management
- Condition monitoring and assessment
- Performance tracking and analytics
- Maintenance history integration
- Asset lifecycle management
"""

import asyncio
import logging
from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple, Union
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, validator

from svgx_engine.services.notifications import UnifiedNotificationSystem

logger = logging.getLogger(__name__)


class AssetStatus(str, Enum):
    """Asset operational status"""

    OPERATIONAL = "operational"
    MAINTENANCE = "maintenance"
    REPAIR = "repair"
    RETIRED = "retired"
    SPARE = "spare"
    DECOMMISSIONED = "decommissioned"
    TESTING = "testing"
    STANDBY = "standby"


class AssetCondition(str, Enum):
    """Asset condition assessment"""

    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"
    CRITICAL = "critical"


class AssetType(str, Enum):
    """Types of assets"""

    EQUIPMENT = "equipment"
    MACHINERY = "machinery"
    VEHICLE = "vehicle"
    BUILDING = "building"
    INFRASTRUCTURE = "infrastructure"
    TOOL = "tool"
    INSTRUMENT = "instrument"
    SYSTEM = "system"
    COMPONENT = "component"


class AssetLocation(BaseModel):
    """Asset location information"""

    id: UUID = Field(default_factory=uuid4)
    asset_id: str = Field(..., description="Asset identifier")
    location_name: str = Field(..., description="Location name")
    building: Optional[str] = None
    floor: Optional[str] = None
    room: Optional[str] = None
    coordinates: Optional[Tuple[float, float]] = None
    address: Optional[str] = None
    zone: Optional[str] = None
    department: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    updated_by: Optional[str] = None


class AssetCondition(BaseModel):
    """Asset condition assessment"""

    id: UUID = Field(default_factory=uuid4)
    asset_id: str = Field(..., description="Asset identifier")
    condition: AssetCondition = Field(..., description="Overall condition")
    assessment_date: datetime = Field(default_factory=datetime.utcnow)
    assessed_by: str = Field(..., description="Person who assessed")
    notes: Optional[str] = None
    visual_inspection: Optional[str] = None
    functional_test: Optional[str] = None
    performance_metrics: Dict[str, Union[int, float, str]] = Field(default_factory=dict)
    recommendations: Optional[str] = None
    next_assessment_date: Optional[datetime] = None


class AssetPerformance(BaseModel):
    """Asset performance metrics"""

    id: UUID = Field(default_factory=uuid4)
    asset_id: str = Field(..., description="Asset identifier")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    uptime_percentage: float = Field(..., description="Uptime percentage")
    efficiency_rating: float = Field(..., description="Efficiency rating (0-100)")
    throughput: Optional[float] = None
    energy_consumption: Optional[float] = None
    temperature: Optional[float] = None
    vibration: Optional[float] = None
    pressure: Optional[float] = None
    speed: Optional[float] = None
    load_percentage: Optional[float] = None
    error_count: int = Field(default=0)
    warning_count: int = Field(default=0)
    maintenance_hours: Optional[float] = None
    cost_per_hour: Optional[Decimal] = None


class AssetAlert(BaseModel):
    """Asset alert/notification"""

    id: UUID = Field(default_factory=uuid4)
    asset_id: str = Field(..., description="Asset identifier")
    alert_type: str = Field(..., description="Type of alert")
    severity: str = Field(..., description="Alert severity")
    message: str = Field(..., description="Alert message")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    is_acknowledged: bool = Field(default=False)
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None
    is_resolved: bool = Field(default=False)
    resolved_by: Optional[str] = None
    resolved_at: Optional[datetime] = None
    resolution_notes: Optional[str] = None


class Asset(BaseModel):
    """Asset information"""

    id: str = Field(..., description="Asset identifier")
    name: str = Field(..., description="Asset name")
    description: Optional[str] = None
    asset_type: AssetType = Field(..., description="Type of asset")
    status: AssetStatus = Field(default=AssetStatus.OPERATIONAL)
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    serial_number: Optional[str] = None
    installation_date: Optional[datetime] = None
    warranty_expiry: Optional[datetime] = None
    expected_lifespan: Optional[int] = None
    current_location: Optional[AssetLocation] = None
    current_condition: Optional[AssetCondition] = None
    last_maintenance: Optional[datetime] = None
    next_maintenance: Optional[datetime] = None
    total_operating_hours: Optional[float] = None
    total_cost: Optional[Decimal] = None
    department: Optional[str] = None
    responsible_person: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    specifications: Dict[str, Union[str, int, float, bool]] = Field(
        default_factory=dict
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class AssetTrackingService:
    """Service for managing asset tracking and monitoring"""

    def __init__(self):
        self.assets: Dict[str, Asset] = {}
        self.locations: Dict[UUID, AssetLocation] = {}
        self.conditions: Dict[UUID, AssetCondition] = {}
        self.performance_data: Dict[UUID, AssetPerformance] = {}
        self.alerts: Dict[UUID, AssetAlert] = {}
        self.notification_system = UnifiedNotificationSystem()

        logger.info("AssetTrackingService initialized")

    async def register_asset(
        self,
        asset_id: str,
        name: str,
        asset_type: AssetType,
        description: Optional[str] = None,
        manufacturer: Optional[str] = None,
        model: Optional[str] = None,
        serial_number: Optional[str] = None,
        installation_date: Optional[datetime] = None,
        warranty_expiry: Optional[datetime] = None,
        expected_lifespan: Optional[int] = None,
        department: Optional[str] = None,
        responsible_person: Optional[str] = None,
        tags: List[str] = None,
        specifications: Dict[str, Union[str, int, float, bool]] = None,
    ) -> Asset:
        """Register a new asset"""
        asset = Asset(
            id=asset_id,
            name=name,
            description=description,
            asset_type=asset_type,
            manufacturer=manufacturer,
            model=model,
            serial_number=serial_number,
            installation_date=installation_date,
            warranty_expiry=warranty_expiry,
            expected_lifespan=expected_lifespan,
            department=department,
            responsible_person=responsible_person,
            tags=tags or [],
            specifications=specifications or {},
        )

        self.assets[asset_id] = asset
        logger.info(f"Registered asset: {asset_id}")
        return asset

    async def update_asset(self, asset_id: str, **kwargs) -> Optional[Asset]:
        """Update asset information"""
        if asset_id not in self.assets:
            logger.warning(f"Asset not found: {asset_id}")
            return None

        asset = self.assets[asset_id]
        for key, value in kwargs.items():
            if hasattr(asset, key):
                setattr(asset, key, value)

        asset.updated_at = datetime.utcnow()
        logger.info(f"Updated asset: {asset_id}")
        return asset

    async def get_asset(self, asset_id: str) -> Optional[Asset]:
        """Get asset by ID"""
        return self.assets.get(asset_id)

    async def get_all_assets(
        self,
        asset_type: Optional[AssetType] = None,
        status: Optional[AssetStatus] = None,
        department: Optional[str] = None,
    ) -> List[Asset]:
        """Get all assets with optional filters"""
        assets = list(self.assets.values())

        if asset_type:
            assets = [a for a in assets if a.asset_type == asset_type]
        if status:
            assets = [a for a in assets if a.status == status]
        if department:
            assets = [a for a in assets if a.department == department]

        return assets

    async def update_asset_location(
        self,
        asset_id: str,
        location_name: str,
        building: Optional[str] = None,
        floor: Optional[str] = None,
        room: Optional[str] = None,
        coordinates: Optional[Tuple[float, float]] = None,
        address: Optional[str] = None,
        zone: Optional[str] = None,
        department: Optional[str] = None,
        updated_by: Optional[str] = None,
    ) -> Optional[AssetLocation]:
        """Update asset location"""
        if asset_id not in self.assets:
            logger.warning(f"Asset not found: {asset_id}")
            return None

        location = AssetLocation(
            asset_id=asset_id,
            location_name=location_name,
            building=building,
            floor=floor,
            room=room,
            coordinates=coordinates,
            address=address,
            zone=zone,
            department=department,
            updated_by=updated_by,
        )

        self.locations[location.id] = location

        # Update asset's current location
        asset = self.assets[asset_id]
        asset.current_location = location
        asset.updated_at = datetime.utcnow()

        logger.info(f"Updated location for asset: {asset_id}")
        return location

    async def assess_asset_condition(
        self,
        asset_id: str,
        condition: AssetCondition,
        assessed_by: str,
        notes: Optional[str] = None,
        visual_inspection: Optional[str] = None,
        functional_test: Optional[str] = None,
        performance_metrics: Dict[str, Union[int, float, str]] = None,
        recommendations: Optional[str] = None,
        next_assessment_date: Optional[datetime] = None,
    ) -> Optional[AssetCondition]:
        """Assess asset condition"""
        if asset_id not in self.assets:
            logger.warning(f"Asset not found: {asset_id}")
            return None

        condition_assessment = AssetCondition(
            asset_id=asset_id,
            condition=condition,
            assessed_by=assessed_by,
            notes=notes,
            visual_inspection=visual_inspection,
            functional_test=functional_test,
            performance_metrics=performance_metrics or {},
            recommendations=recommendations,
            next_assessment_date=next_assessment_date,
        )

        self.conditions[condition_assessment.id] = condition_assessment

        # Update asset's current condition
        asset = self.assets[asset_id]
        asset.current_condition = condition_assessment
        asset.updated_at = datetime.utcnow()

        # Send alert if condition is poor or critical
        if condition in [AssetCondition.POOR, AssetCondition.CRITICAL]:
            await self._create_asset_alert(
                asset_id=asset_id,
                alert_type="condition_warning",
                severity="high" if condition == AssetCondition.CRITICAL else "medium",
                message=f"Asset {asset.name} condition assessed as {condition.value}",
            )

        logger.info(f"Assessed condition for asset: {asset_id}")
        return condition_assessment

    async def record_performance_data(
        self,
        asset_id: str,
        uptime_percentage: float,
        efficiency_rating: float,
        throughput: Optional[float] = None,
        energy_consumption: Optional[float] = None,
        temperature: Optional[float] = None,
        vibration: Optional[float] = None,
        pressure: Optional[float] = None,
        speed: Optional[float] = None,
        load_percentage: Optional[float] = None,
        error_count: int = 0,
        warning_count: int = 0,
        maintenance_hours: Optional[float] = None,
        cost_per_hour: Optional[Decimal] = None,
    ) -> Optional[AssetPerformance]:
        """Record performance data for an asset"""
        if asset_id not in self.assets:
            logger.warning(f"Asset not found: {asset_id}")
            return None

        performance = AssetPerformance(
            asset_id=asset_id,
            uptime_percentage=uptime_percentage,
            efficiency_rating=efficiency_rating,
            throughput=throughput,
            energy_consumption=energy_consumption,
            temperature=temperature,
            vibration=vibration,
            pressure=pressure,
            speed=speed,
            load_percentage=load_percentage,
            error_count=error_count,
            warning_count=warning_count,
            maintenance_hours=maintenance_hours,
            cost_per_hour=cost_per_hour,
        )

        self.performance_data[performance.id] = performance

        # Update asset's total operating hours
        asset = self.assets[asset_id]
        if maintenance_hours:
            asset.total_operating_hours = (
                asset.total_operating_hours or 0
            ) + maintenance_hours

        # Check for performance alerts
        await self._check_performance_alerts(asset_id, performance)

        logger.info(f"Recorded performance data for asset: {asset_id}")
        return performance

    async def get_asset_performance_history(
        self,
        asset_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[AssetPerformance]:
        """Get performance history for an asset"""
        if asset_id not in self.assets:
            return []

        performance_data = [
            p for p in self.performance_data.values() if p.asset_id == asset_id
        ]

        if start_date:
            performance_data = [
                p for p in performance_data if p.timestamp >= start_date
            ]
        if end_date:
            performance_data = [p for p in performance_data if p.timestamp <= end_date]

        return sorted(performance_data, key=lambda x: x.timestamp)

    async def get_asset_location_history(
        self,
        asset_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[AssetLocation]:
        """Get location history for an asset"""
        if asset_id not in self.assets:
            return []

        locations = [l for l in self.locations.values() if l.asset_id == asset_id]

        if start_date:
            locations = [l for l in locations if l.timestamp >= start_date]
        if end_date:
            locations = [l for l in locations if l.timestamp <= end_date]

        return sorted(locations, key=lambda x: x.timestamp)

    async def get_asset_condition_history(
        self,
        asset_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[AssetCondition]:
        """Get condition history for an asset"""
        if asset_id not in self.assets:
            return []

        conditions = [c for c in self.conditions.values() if c.asset_id == asset_id]

        if start_date:
            conditions = [c for c in conditions if c.assessment_date >= start_date]
        if end_date:
            conditions = [c for c in conditions if c.assessment_date <= end_date]

        return sorted(conditions, key=lambda x: x.assessment_date)

    async def _create_asset_alert(
        self, asset_id: str, alert_type: str, severity: str, message: str
    ) -> AssetAlert:
        """Create an asset alert"""
        alert = AssetAlert(
            asset_id=asset_id, alert_type=alert_type, severity=severity, message=message
        )

        self.alerts[alert.id] = alert

        # Send notification
        asset = self.assets[asset_id]
        await self._send_alert_notification(alert, asset)

        logger.info(f"Created alert for asset {asset_id}: {alert_type}")
        return alert

    async def _check_performance_alerts(
        self, asset_id: str, performance: AssetPerformance
    ):
        """Check for performance-based alerts"""
        asset = self.assets[asset_id]

        # Check uptime
        if performance.uptime_percentage < 80:
            await self._create_asset_alert(
                asset_id=asset_id,
                alert_type="low_uptime",
                severity="medium",
                message=f"Asset {asset.name} uptime is {performance.uptime_percentage}%",
            )

        # Check efficiency
        if performance.efficiency_rating < 70:
            await self._create_asset_alert(
                asset_id=asset_id,
                alert_type="low_efficiency",
                severity="medium",
                message=f"Asset {asset.name} efficiency is {performance.efficiency_rating}%",
            )

        # Check temperature
        if performance.temperature and performance.temperature > 80:
            await self._create_asset_alert(
                asset_id=asset_id,
                alert_type="high_temperature",
                severity="high",
                message=f"Asset {asset.name} temperature is {performance.temperature}°C",
            )

        # Check vibration
        if performance.vibration and performance.vibration > 10:
            await self._create_asset_alert(
                asset_id=asset_id,
                alert_type="high_vibration",
                severity="high",
                message=f"Asset {asset.name} vibration is {performance.vibration} units",
            )

        # Check error count
        if performance.error_count > 5:
            await self._create_asset_alert(
                asset_id=asset_id,
                alert_type="high_error_count",
                severity="high",
                message=f"Asset {asset.name} has {performance.error_count} errors",
            )

    async def _send_alert_notification(self, alert: AssetAlert, asset: Asset):
        """Send notification for asset alerts"""
        try:
            subject = f"Asset Alert: {alert.alert_type.replace('_', ' ').title()}"
            message = f"""
            Asset Alert
            
            Asset: {asset.name} ({asset.id})
            Type: {alert.alert_type}
            Severity: {alert.severity}
            Message: {alert.message}
            Time: {alert.timestamp}
            """

            # Send to responsible person if available
            if asset.responsible_person:
                await self.notification_system.send_email_notification(
                    to_email=asset.responsible_person, subject=subject, message=message
                )

            # Send to department if available
            if asset.department:
                await self.notification_system.send_slack_notification(
                    channel=asset.department,
                    message=f"Asset alert for {asset.name}: {alert.message}",
                )

        except Exception as e:
            logger.error(f"Failed to send alert notification for asset {asset.id}: {e}")

    async def acknowledge_alert(
        self, alert_id: UUID, acknowledged_by: str
    ) -> Optional[AssetAlert]:
        """Acknowledge an asset alert"""
        if alert_id not in self.alerts:
            logger.warning(f"Alert not found: {alert_id}")
            return None

        alert = self.alerts[alert_id]
        alert.is_acknowledged = True
        alert.acknowledged_by = acknowledged_by
        alert.acknowledged_at = datetime.utcnow()

        logger.info(f"Acknowledged alert: {alert_id}")
        return alert

    async def resolve_alert(
        self, alert_id: UUID, resolved_by: str, resolution_notes: Optional[str] = None
    ) -> Optional[AssetAlert]:
        """Resolve an asset alert"""
        if alert_id not in self.alerts:
            logger.warning(f"Alert not found: {alert_id}")
            return None

        alert = self.alerts[alert_id]
        alert.is_resolved = True
        alert.resolved_by = resolved_by
        alert.resolved_at = datetime.utcnow()
        alert.resolution_notes = resolution_notes

        logger.info(f"Resolved alert: {alert_id}")
        return alert

    async def get_asset_alerts(
        self,
        asset_id: Optional[str] = None,
        alert_type: Optional[str] = None,
        severity: Optional[str] = None,
        is_acknowledged: Optional[bool] = None,
        is_resolved: Optional[bool] = None,
    ) -> List[AssetAlert]:
        """Get asset alerts with optional filters"""
        alerts = list(self.alerts.values())

        if asset_id:
            alerts = [a for a in alerts if a.asset_id == asset_id]
        if alert_type:
            alerts = [a for a in alerts if a.alert_type == alert_type]
        if severity:
            alerts = [a for a in alerts if a.severity == severity]
        if is_acknowledged is not None:
            alerts = [a for a in alerts if a.is_acknowledged == is_acknowledged]
        if is_resolved is not None:
            alerts = [a for a in alerts if a.is_resolved == is_resolved]

        return sorted(alerts, key=lambda x: x.timestamp, reverse=True)

    async def get_asset_statistics(
        self,
        asset_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict:
        """Get asset statistics"""
        if asset_id:
            assets = [self.assets[asset_id]] if asset_id in self.assets else []
        else:
            assets = list(self.assets.values())

        total_assets = len(assets)
        operational_assets = len(
            [a for a in assets if a.status == AssetStatus.OPERATIONAL]
        )
        maintenance_assets = len(
            [a for a in assets if a.status == AssetStatus.MAINTENANCE]
        )
        repair_assets = len([a for a in assets if a.status == AssetStatus.REPAIR])

        # Get performance data for the period
        performance_data = []
        for asset in assets:
            asset_performance = await self.get_asset_performance_history(
                asset_id=asset.id, start_date=start_date, end_date=end_date
            )
            performance_data.extend(asset_performance)

        if performance_data:
            avg_uptime = sum(p.uptime_percentage for p in performance_data) / len(
                performance_data
            )
            avg_efficiency = sum(p.efficiency_rating for p in performance_data) / len(
                performance_data
            )
            total_errors = sum(p.error_count for p in performance_data)
            total_warnings = sum(p.warning_count for p in performance_data)
        else:
            avg_uptime = 0
            avg_efficiency = 0
            total_errors = 0
            total_warnings = 0

        # Get alerts for the period
        alerts = await self.get_asset_alerts()
        if start_date:
            alerts = [a for a in alerts if a.timestamp >= start_date]
        if end_date:
            alerts = [a for a in alerts if a.timestamp <= end_date]

        total_alerts = len(alerts)
        unacknowledged_alerts = len([a for a in alerts if not a.is_acknowledged])
        unresolved_alerts = len([a for a in alerts if not a.is_resolved])

        return {
            "total_assets": total_assets,
            "operational_assets": operational_assets,
            "maintenance_assets": maintenance_assets,
            "repair_assets": repair_assets,
            "operational_rate": (
                (operational_assets / total_assets * 100) if total_assets > 0 else 0
            ),
            "average_uptime": avg_uptime,
            "average_efficiency": avg_efficiency,
            "total_errors": total_errors,
            "total_warnings": total_warnings,
            "total_alerts": total_alerts,
            "unacknowledged_alerts": unacknowledged_alerts,
            "unresolved_alerts": unresolved_alerts,
        }

    async def update_maintenance_history(
        self,
        asset_id: str,
        maintenance_date: datetime,
        maintenance_type: str,
        performed_by: str,
        duration_hours: Optional[float] = None,
        cost: Optional[Decimal] = None,
        notes: Optional[str] = None,
    ) -> bool:
        """Update asset maintenance history"""
        if asset_id not in self.assets:
            logger.warning(f"Asset not found: {asset_id}")
            return False

        asset = self.assets[asset_id]
        asset.last_maintenance = maintenance_date

        # Update total operating hours
        if duration_hours:
            asset.total_operating_hours = (
                asset.total_operating_hours or 0
            ) + duration_hours

        # Update total cost
        if cost:
            asset.total_cost = (asset.total_cost or Decimal(0)) + cost

        asset.updated_at = datetime.utcnow()

        logger.info(f"Updated maintenance history for asset: {asset_id}")
        return True
