"""
Comprehensive Tests for CMMS Integration

This module provides comprehensive tests for all CMMS integration components:
- Data synchronization
- Work order processing
- Maintenance scheduling
- Asset tracking
"""

import asyncio
import json
import logging
import unittest
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List
from unittest.mock import AsyncMock, MagicMock, patch

from svgx_engine.services.cmms.data_synchronization import (
    CMMSDataSynchronizationService,
    CMMSConnection,
    FieldMapping,
    WorkOrder,
    MaintenanceSchedule,
    Asset,
    SyncResult,
)
from svgx_engine.services.cmms.work_order_processing import (
    WorkOrderProcessingService,
    WorkOrderStep,
    WorkOrderPart,
    WorkOrderTemplate,
)
from svgx_engine.services.cmms.maintenance_scheduling import (
    MaintenanceSchedulingService,
    MaintenanceType,
    MaintenancePriority,
    MaintenanceStatus,
    MaintenanceFrequency,
    MaintenanceTrigger,
    MaintenanceStep,
    MaintenanceTask,
    MaintenanceHistory,
    MaintenanceCalendar,
)
from svgx_engine.services.cmms.asset_tracking import (
    AssetTrackingService,
    AssetStatus,
    AssetCondition,
    AssetType,
    AssetLocation,
    AssetPerformance,
    AssetAlert,
)

logger = logging.getLogger(__name__)


class TestCMMSDataSynchronization(unittest.TestCase):
    """Test cases for CMMS data synchronization"""

    def setUp(self):
        """Set up test fixtures"""
        self.service = CMMSDataSynchronizationService()
        self.test_connection = CMMSConnection(
            cmms_type="test_cmms",
            api_url="https://api.testcmms.com",
            api_key="test_api_key",
            connection_name="Test CMMS Connection",
        )

    async def test_add_cmms_connection(self):
        """Test adding a CMMS connection"""
        connection = await self.service.add_cmms_connection(
            cmms_type="test_cmms",
            api_url="https://api.testcmms.com",
            api_key="test_api_key",
            connection_name="Test Connection",
        )

        self.assertIsNotNone(connection)
        self.assertEqual(connection.cmms_type, "test_cmms")
        self.assertEqual(connection.api_url, "https://api.testcmms.com")
        self.assertEqual(connection.connection_name, "Test Connection")
        self.assertIsNotNone(connection.id)

    async def test_add_field_mapping(self):
        """Test adding a field mapping"""
        # First add a connection
        connection = await self.service.add_cmms_connection(
            cmms_type="test_cmms",
            api_url="https://api.testcmms.com",
            api_key="test_api_key",
            connection_name="Test Connection",
        )

        # Add field mapping
        mapping = await self.service.add_field_mapping(
            cmms_connection_id=connection.id,
            source_field="work_order_id",
            target_field="id",
            transformation_rule="uppercase",
            is_required=True,
        )

        self.assertIsNotNone(mapping)
        self.assertEqual(mapping.source_field, "work_order_id")
        self.assertEqual(mapping.target_field, "id")
        self.assertEqual(mapping.transformation_rule, "uppercase")
        self.assertTrue(mapping.is_required)

    async def test_sync_work_orders(self):
        """Test synchronizing work orders"""
        # First add a connection
        connection = await self.service.add_cmms_connection(
            cmms_type="test_cmms",
            api_url="https://api.testcmms.com",
            api_key="test_api_key",
            connection_name="Test Connection",
        )

        # Sync work orders
        result = await self.service.sync_work_orders(
            cmms_connection_id=connection.id, force_sync=False
        )

        self.assertIsNotNone(result)
        self.assertIsInstance(result.synced_count, int)
        self.assertIsInstance(result.errors, list)

    async def test_sync_maintenance_schedules(self):
        """Test synchronizing maintenance schedules"""
        # First add a connection
        connection = await self.service.add_cmms_connection(
            cmms_type="test_cmms",
            api_url="https://api.testcmms.com",
            api_key="test_api_key",
            connection_name="Test Connection",
        )

        # Sync maintenance schedules
        result = await self.service.sync_maintenance_schedules(
            cmms_connection_id=connection.id, force_sync=False
        )

        self.assertIsNotNone(result)
        self.assertIsInstance(result.synced_count, int)
        self.assertIsInstance(result.errors, list)

    async def test_sync_assets(self):
        """Test synchronizing assets"""
        # First add a connection
        connection = await self.service.add_cmms_connection(
            cmms_type="test_cmms",
            api_url="https://api.testcmms.com",
            api_key="test_api_key",
            connection_name="Test Connection",
        )

        # Sync assets
        result = await self.service.sync_assets(
            cmms_connection_id=connection.id, force_sync=False
        )

        self.assertIsNotNone(result)
        self.assertIsInstance(result.synced_count, int)
        self.assertIsInstance(result.errors, list)

    async def test_sync_all_data(self):
        """Test synchronizing all data"""
        # First add a connection
        connection = await self.service.add_cmms_connection(
            cmms_type="test_cmms",
            api_url="https://api.testcmms.com",
            api_key="test_api_key",
            connection_name="Test Connection",
        )

        # Sync all data
        result = await self.service.sync_all(
            cmms_connection_id=connection.id, force_sync=False
        )

        self.assertIsNotNone(result)
        self.assertIsInstance(result.work_orders_synced, int)
        self.assertIsInstance(result.schedules_synced, int)
        self.assertIsInstance(result.assets_synced, int)
        self.assertIsInstance(result.errors, list)


class TestWorkOrderProcessing(unittest.TestCase):
    """Test cases for work order processing"""

    def setUp(self):
        """Set up test fixtures"""
        self.service = WorkOrderProcessingService()
        self.test_asset_id = "asset_001"

    async def test_create_work_order(self):
        """Test creating a work order"""
        work_order = await self.service.create_work_order(
            asset_id=self.test_asset_id,
            title="Test Work Order",
            description="Test work order description",
            priority="high",
            estimated_hours=4.0,
            assigned_to="technician_001",
        )

        self.assertIsNotNone(work_order)
        self.assertEqual(work_order.asset_id, self.test_asset_id)
        self.assertEqual(work_order.title, "Test Work Order")
        self.assertEqual(work_order.priority, "high")
        self.assertEqual(work_order.estimated_hours, 4.0)
        self.assertEqual(work_order.assigned_to, "technician_001")
        self.assertIsNotNone(work_order.work_order_number)

    async def test_create_work_order_from_template(self):
        """Test creating a work order from template"""
        # First create a template
        template = await self.service.create_work_order_template(
            name="Preventive Maintenance",
            description="Standard preventive maintenance template",
            steps=[
                WorkOrderStep(
                    name="Inspect equipment",
                    description="Visual inspection of equipment",
                    estimated_duration=30,
                    sequence_order=1,
                ),
                WorkOrderStep(
                    name="Lubricate moving parts",
                    description="Apply lubrication to moving parts",
                    estimated_duration=45,
                    sequence_order=2,
                ),
            ],
            estimated_hours=1.25,
            estimated_cost=Decimal("150.00"),
        )

        # Create work order from template
        work_order = await self.service.create_work_order_from_template(
            template_id=template.id,
            asset_id=self.test_asset_id,
            assigned_to="technician_001",
        )

        self.assertIsNotNone(work_order)
        self.assertEqual(work_order.asset_id, self.test_asset_id)
        self.assertEqual(work_order.assigned_to, "technician_001")
        self.assertEqual(len(work_order.steps), 2)

    async def test_update_work_order_status(self):
        """Test updating work order status"""
        # First create a work order
        work_order = await self.service.create_work_order(
            asset_id=self.test_asset_id,
            title="Test Work Order",
            description="Test work order description",
            priority="high",
            estimated_hours=4.0,
        )

        # Update status
        updated_work_order = await self.service.update_work_order_status(
            work_order_id=work_order.id, status="in_progress"
        )

        self.assertIsNotNone(updated_work_order)
        self.assertEqual(updated_work_order.status, "in_progress")

    async def test_add_work_order_step(self):
        """Test adding a step to a work order"""
        # First create a work order
        work_order = await self.service.create_work_order(
            asset_id=self.test_asset_id,
            title="Test Work Order",
            description="Test work order description",
            priority="high",
            estimated_hours=4.0,
        )

        # Add a step
        step = await self.service.add_work_order_step(
            work_order_id=work_order.id,
            name="Test Step",
            description="Test step description",
            estimated_duration=30,
            sequence_order=1,
        )

        self.assertIsNotNone(step)
        self.assertEqual(step.name, "Test Step")
        self.assertEqual(step.sequence_order, 1)

    async def test_get_work_orders(self):
        """Test getting work orders with filters"""
        # Create multiple work orders
        work_order1 = await self.service.create_work_order(
            asset_id=self.test_asset_id,
            title="Work Order 1",
            description="First work order",
            priority="high",
            estimated_hours=4.0,
        )

        work_order2 = await self.service.create_work_order(
            asset_id="asset_002",
            title="Work Order 2",
            description="Second work order",
            priority="medium",
            estimated_hours=2.0,
        )

        # Get work orders with filters
        work_orders = await self.service.get_work_orders(
            status="scheduled", asset_id=self.test_asset_id
        )

        self.assertIsInstance(work_orders, list)
        self.assertTrue(len(work_orders) > 0)

        # Check that filtered results are correct
        for wo in work_orders:
            self.assertEqual(wo.status, "scheduled")
            self.assertEqual(wo.asset_id, self.test_asset_id)


class TestMaintenanceScheduling(unittest.TestCase):
    """Test cases for maintenance scheduling"""

    def setUp(self):
        """Set up test fixtures"""
        self.service = MaintenanceSchedulingService()

    async def test_create_maintenance_schedule(self):
        """Test creating a maintenance schedule"""
        schedule = await self.service.create_maintenance_schedule(
            name="Monthly Equipment Check",
            description="Monthly preventive maintenance for equipment",
            maintenance_type=MaintenanceType.PREVENTIVE,
            priority=MaintenancePriority.MEDIUM,
            frequency=MaintenanceFrequency.MONTHLY,
            trigger_type=MaintenanceTrigger.TIME_BASED,
            trigger_value=30,
            estimated_duration=120,
            estimated_cost=Decimal("200.00"),
            required_skills=["electrical", "mechanical"],
            required_tools=["multimeter", "wrenches"],
            required_parts=["filters", "lubricant"],
        )

        self.assertIsNotNone(schedule)
        self.assertEqual(schedule.name, "Monthly Equipment Check")
        self.assertEqual(schedule.maintenance_type, MaintenanceType.PREVENTIVE)
        self.assertEqual(schedule.priority, MaintenancePriority.MEDIUM)
        self.assertEqual(schedule.frequency, MaintenanceFrequency.MONTHLY)
        self.assertEqual(len(schedule.required_skills), 2)
        self.assertEqual(len(schedule.required_tools), 2)
        self.assertEqual(len(schedule.required_parts), 2)

    async def test_create_maintenance_task(self):
        """Test creating a maintenance task"""
        # First create a schedule
        schedule = await self.service.create_maintenance_schedule(
            name="Test Schedule",
            description="Test maintenance schedule",
            maintenance_type=MaintenanceType.PREVENTIVE,
            priority=MaintenancePriority.MEDIUM,
            frequency=MaintenanceFrequency.MONTHLY,
            trigger_type=MaintenanceTrigger.TIME_BASED,
            trigger_value=30,
            estimated_duration=120,
            estimated_cost=Decimal("200.00"),
        )

        # Create a task
        scheduled_start = datetime.utcnow() + timedelta(days=7)
        task = await self.service.create_maintenance_task(
            schedule_id=schedule.id,
            asset_id="asset_001",
            scheduled_start=scheduled_start,
            priority=MaintenancePriority.HIGH,
            assigned_to="technician_001",
        )

        self.assertIsNotNone(task)
        self.assertEqual(task.schedule_id, schedule.id)
        self.assertEqual(task.asset_id, "asset_001")
        self.assertEqual(task.priority, MaintenancePriority.HIGH)
        self.assertEqual(task.assigned_to, "technician_001")

    async def test_start_maintenance_task(self):
        """Test starting a maintenance task"""
        # First create a schedule and task
        schedule = await self.service.create_maintenance_schedule(
            name="Test Schedule",
            description="Test maintenance schedule",
            maintenance_type=MaintenanceType.PREVENTIVE,
            priority=MaintenancePriority.MEDIUM,
            frequency=MaintenanceFrequency.MONTHLY,
            trigger_type=MaintenanceTrigger.TIME_BASED,
            trigger_value=30,
            estimated_duration=120,
            estimated_cost=Decimal("200.00"),
        )

        scheduled_start = datetime.utcnow() + timedelta(days=7)
        task = await self.service.create_maintenance_task(
            schedule_id=schedule.id,
            asset_id="asset_001",
            scheduled_start=scheduled_start,
        )

        # Start the task
        started_task = await self.service.start_maintenance_task(
            task_id=task.id, performer="technician_001"
        )

        self.assertIsNotNone(started_task)
        self.assertEqual(started_task.status, MaintenanceStatus.IN_PROGRESS)
        self.assertIsNotNone(started_task.actual_start)
        self.assertEqual(started_task.assigned_to, "technician_001")

    async def test_complete_maintenance_task(self):
        """Test completing a maintenance task"""
        # First create a schedule and task
        schedule = await self.service.create_maintenance_schedule(
            name="Test Schedule",
            description="Test maintenance schedule",
            maintenance_type=MaintenanceType.PREVENTIVE,
            priority=MaintenancePriority.MEDIUM,
            frequency=MaintenanceFrequency.MONTHLY,
            trigger_type=MaintenanceTrigger.TIME_BASED,
            trigger_value=30,
            estimated_duration=120,
            estimated_cost=Decimal("200.00"),
        )

        scheduled_start = datetime.utcnow() + timedelta(days=7)
        task = await self.service.create_maintenance_task(
            schedule_id=schedule.id,
            asset_id="asset_001",
            scheduled_start=scheduled_start,
        )

        # Start the task
        task = await self.service.start_maintenance_task(
            task_id=task.id, performer="technician_001"
        )

        # Complete the task
        completed_task = await self.service.complete_maintenance_task(
            task_id=task.id,
            actual_duration=110,
            actual_cost=Decimal("180.00"),
            notes="Task completed successfully",
            findings="Equipment in good condition",
            recommendations="Continue with current maintenance schedule",
        )

        self.assertIsNotNone(completed_task)
        self.assertEqual(completed_task.status, MaintenanceStatus.COMPLETED)
        self.assertIsNotNone(completed_task.actual_end)
        self.assertEqual(completed_task.actual_duration, 110)
        self.assertEqual(completed_task.actual_cost, Decimal("180.00"))

    async def test_get_maintenance_statistics(self):
        """Test getting maintenance statistics"""
        # Create some maintenance tasks
        schedule = await self.service.create_maintenance_schedule(
            name="Test Schedule",
            description="Test maintenance schedule",
            maintenance_type=MaintenanceType.PREVENTIVE,
            priority=MaintenancePriority.MEDIUM,
            frequency=MaintenanceFrequency.MONTHLY,
            trigger_type=MaintenanceTrigger.TIME_BASED,
            trigger_value=30,
            estimated_duration=120,
            estimated_cost=Decimal("200.00"),
        )

        scheduled_start = datetime.utcnow() + timedelta(days=7)
        task = await self.service.create_maintenance_task(
            schedule_id=schedule.id,
            asset_id="asset_001",
            scheduled_start=scheduled_start,
        )

        # Get statistics
        stats = await self.service.get_maintenance_statistics()

        self.assertIsInstance(stats, dict)
        self.assertIn("total_tasks", stats)
        self.assertIn("completed_tasks", stats)
        self.assertIn("overdue_tasks", stats)
        self.assertIn("in_progress_tasks", stats)
        self.assertIn("completion_rate", stats)
        self.assertIn("total_cost", stats)
        self.assertIn("total_duration_hours", stats)


class TestAssetTracking(unittest.TestCase):
    """Test cases for asset tracking"""

    def setUp(self):
        """Set up test fixtures"""
        self.service = AssetTrackingService()
        self.test_asset_id = "asset_001"

    async def test_register_asset(self):
        """Test registering an asset"""
        asset = await self.service.register_asset(
            asset_id=self.test_asset_id,
            name="Test Equipment",
            asset_type=AssetType.EQUIPMENT,
            description="Test equipment for tracking",
            manufacturer="Test Manufacturer",
            model="Test Model",
            serial_number="SN123456",
            department="Engineering",
            responsible_person="engineer_001",
            tags=["critical", "maintenance"],
            specifications={
                "power_rating": "100kW",
                "voltage": "480V",
                "frequency": "60Hz",
            },
        )

        self.assertIsNotNone(asset)
        self.assertEqual(asset.id, self.test_asset_id)
        self.assertEqual(asset.name, "Test Equipment")
        self.assertEqual(asset.asset_type, AssetType.EQUIPMENT)
        self.assertEqual(asset.manufacturer, "Test Manufacturer")
        self.assertEqual(asset.department, "Engineering")
        self.assertEqual(len(asset.tags), 2)
        self.assertIn("power_rating", asset.specifications)

    async def test_update_asset_location(self):
        """Test updating asset location"""
        # First register an asset
        asset = await self.service.register_asset(
            asset_id=self.test_asset_id,
            name="Test Equipment",
            asset_type=AssetType.EQUIPMENT,
        )

        # Update location
        location = await self.service.update_asset_location(
            asset_id=self.test_asset_id,
            location_name="Building A",
            building="Main Building",
            floor="2nd Floor",
            room="Room 201",
            coordinates=(40.7128, -74.0060),
            department="Engineering",
            updated_by="operator_001",
        )

        self.assertIsNotNone(location)
        self.assertEqual(location.asset_id, self.test_asset_id)
        self.assertEqual(location.location_name, "Building A")
        self.assertEqual(location.building, "Main Building")
        self.assertEqual(location.floor, "2nd Floor")
        self.assertEqual(location.room, "Room 201")
        self.assertEqual(location.coordinates, (40.7128, -74.0060))

    async def test_assess_asset_condition(self):
        """Test assessing asset condition"""
        # First register an asset
        asset = await self.service.register_asset(
            asset_id=self.test_asset_id,
            name="Test Equipment",
            asset_type=AssetType.EQUIPMENT,
        )

        # Assess condition
        condition = await self.service.assess_asset_condition(
            asset_id=self.test_asset_id,
            condition=AssetCondition.GOOD,
            assessed_by="inspector_001",
            notes="Equipment in good working condition",
            visual_inspection="No visible damage or wear",
            functional_test="All functions operating normally",
            performance_metrics={
                "efficiency": 95.5,
                "temperature": 65.2,
                "vibration": 0.8,
            },
            recommendations="Continue with current maintenance schedule",
            next_assessment_date=datetime.utcnow() + timedelta(days=30),
        )

        self.assertIsNotNone(condition)
        self.assertEqual(condition.asset_id, self.test_asset_id)
        self.assertEqual(condition.condition, AssetCondition.GOOD)
        self.assertEqual(condition.assessed_by, "inspector_001")
        self.assertIn("efficiency", condition.performance_metrics)

    async def test_record_performance_data(self):
        """Test recording performance data"""
        # First register an asset
        asset = await self.service.register_asset(
            asset_id=self.test_asset_id,
            name="Test Equipment",
            asset_type=AssetType.EQUIPMENT,
        )

        # Record performance data
        performance = await self.service.record_performance_data(
            asset_id=self.test_asset_id,
            uptime_percentage=95.5,
            efficiency_rating=92.3,
            throughput=150.0,
            energy_consumption=85.2,
            temperature=65.5,
            vibration=0.8,
            pressure=100.0,
            speed=1200.0,
            load_percentage=75.0,
            error_count=2,
            warning_count=1,
            maintenance_hours=4.5,
            cost_per_hour=25.0,
        )

        self.assertIsNotNone(performance)
        self.assertEqual(performance.asset_id, self.test_asset_id)
        self.assertEqual(performance.uptime_percentage, 95.5)
        self.assertEqual(performance.efficiency_rating, 92.3)
        self.assertEqual(performance.throughput, 150.0)
        self.assertEqual(performance.error_count, 2)
        self.assertEqual(performance.warning_count, 1)

    async def test_get_asset_performance_history(self):
        """Test getting asset performance history"""
        # First register an asset and record performance data
        asset = await self.service.register_asset(
            asset_id=self.test_asset_id,
            name="Test Equipment",
            asset_type=AssetType.EQUIPMENT,
        )

        # Record multiple performance data points
        await self.service.record_performance_data(
            asset_id=self.test_asset_id, uptime_percentage=95.5, efficiency_rating=92.3
        )

        await self.service.record_performance_data(
            asset_id=self.test_asset_id, uptime_percentage=97.2, efficiency_rating=94.1
        )

        # Get performance history
        history = await self.service.get_asset_performance_history(
            asset_id=self.test_asset_id
        )

        self.assertIsInstance(history, list)
        self.assertEqual(len(history), 2)

        # Check that data is sorted by timestamp
        for i in range(1, len(history)):
            self.assertGreaterEqual(history[i].timestamp, history[i - 1].timestamp)

    async def test_get_asset_alerts(self):
        """Test getting asset alerts"""
        # First register an asset
        asset = await self.service.register_asset(
            asset_id=self.test_asset_id,
            name="Test Equipment",
            asset_type=AssetType.EQUIPMENT,
        )

        # Record performance data that should trigger alerts
        await self.service.record_performance_data(
            asset_id=self.test_asset_id,
            uptime_percentage=75.0,  # Low uptime
            efficiency_rating=65.0,  # Low efficiency
            temperature=85.0,  # High temperature
            error_count=8,  # High error count
        )

        # Get alerts
        alerts = await self.service.get_asset_alerts(asset_id=self.test_asset_id)

        self.assertIsInstance(alerts, list)
        # Should have alerts for low uptime, low efficiency, high temperature, and high error count
        self.assertGreater(len(alerts), 0)

        # Check alert types
        alert_types = [alert.alert_type for alert in alerts]
        self.assertIn("low_uptime", alert_types)
        self.assertIn("low_efficiency", alert_types)
        self.assertIn("high_temperature", alert_types)
        self.assertIn("high_error_count", alert_types)

    async def test_acknowledge_and_resolve_alerts(self):
        """Test acknowledging and resolving alerts"""
        # First register an asset and create alerts
        asset = await self.service.register_asset(
            asset_id=self.test_asset_id,
            name="Test Equipment",
            asset_type=AssetType.EQUIPMENT,
        )

        await self.service.record_performance_data(
            asset_id=self.test_asset_id, uptime_percentage=75.0, efficiency_rating=65.0
        )

        # Get alerts
        alerts = await self.service.get_asset_alerts(asset_id=self.test_asset_id)

        if alerts:
            alert = alerts[0]

            # Acknowledge alert
            acknowledged_alert = await self.service.acknowledge_alert(
                alert_id=alert.id, acknowledged_by="operator_001"
            )

            self.assertIsNotNone(acknowledged_alert)
            self.assertTrue(acknowledged_alert.is_acknowledged)
            self.assertEqual(acknowledged_alert.acknowledged_by, "operator_001")
            self.assertIsNotNone(acknowledged_alert.acknowledged_at)

            # Resolve alert
            resolved_alert = await self.service.resolve_alert(
                alert_id=alert.id,
                resolved_by="technician_001",
                resolution_notes="Issue resolved by replacing faulty component",
            )

            self.assertIsNotNone(resolved_alert)
            self.assertTrue(resolved_alert.is_resolved)
            self.assertEqual(resolved_alert.resolved_by, "technician_001")
            self.assertIsNotNone(resolved_alert.resolved_at)
            self.assertEqual(
                resolved_alert.resolution_notes,
                "Issue resolved by replacing faulty component",
            )

    async def test_get_asset_statistics(self):
        """Test getting asset statistics"""
        # First register an asset and record performance data
        asset = await self.service.register_asset(
            asset_id=self.test_asset_id,
            name="Test Equipment",
            asset_type=AssetType.EQUIPMENT,
        )

        await self.service.record_performance_data(
            asset_id=self.test_asset_id, uptime_percentage=95.5, efficiency_rating=92.3
        )

        # Get statistics
        stats = await self.service.get_asset_statistics(asset_id=self.test_asset_id)

        self.assertIsInstance(stats, dict)
        self.assertIn("total_assets", stats)
        self.assertIn("operational_assets", stats)
        self.assertIn("maintenance_assets", stats)
        self.assertIn("repair_assets", stats)
        self.assertIn("operational_rate", stats)
        self.assertIn("average_uptime", stats)
        self.assertIn("average_efficiency", stats)
        self.assertIn("total_errors", stats)
        self.assertIn("total_warnings", stats)
        self.assertIn("total_alerts", stats)
        self.assertIn("unacknowledged_alerts", stats)
        self.assertIn("unresolved_alerts", stats)


class TestCMMSIntegration(unittest.TestCase):
    """Integration tests for CMMS components"""

    def setUp(self):
        """Set up test fixtures"""
        self.data_sync_service = CMMSDataSynchronizationService()
        self.work_order_service = WorkOrderProcessingService()
        self.maintenance_service = MaintenanceSchedulingService()
        self.asset_tracking_service = AssetTrackingService()

    async def test_end_to_end_workflow(self):
        """Test end-to-end CMMS workflow"""
        # 1. Register an asset
        asset = await self.asset_tracking_service.register_asset(
            asset_id="asset_001",
            name="Production Machine",
            asset_type=AssetType.EQUIPMENT,
            department="Manufacturing",
        )

        # 2. Create maintenance schedule
        schedule = await self.maintenance_service.create_maintenance_schedule(
            name="Monthly Machine Maintenance",
            description="Monthly preventive maintenance for production machine",
            maintenance_type=MaintenanceType.PREVENTIVE,
            priority=MaintenancePriority.MEDIUM,
            frequency=MaintenanceFrequency.MONTHLY,
            trigger_type=MaintenanceTrigger.TIME_BASED,
            trigger_value=30,
            estimated_duration=180,
            estimated_cost=Decimal("300.00"),
        )

        # 3. Create maintenance task
        scheduled_start = datetime.utcnow() + timedelta(days=7)
        task = await self.maintenance_service.create_maintenance_task(
            schedule_id=schedule.id,
            asset_id=asset.id,
            scheduled_start=scheduled_start,
            assigned_to="technician_001",
        )

        # 4. Create work order for the task
        work_order = await self.work_order_service.create_work_order(
            asset_id=asset.id,
            title="Monthly Maintenance - Production Machine",
            description="Monthly preventive maintenance tasks",
            priority="medium",
            estimated_hours=3.0,
            assigned_to="technician_001",
            scheduled_start=scheduled_start,
            scheduled_end=scheduled_start + timedelta(hours=3),
        )

        # 5. Record performance data
        performance = await self.asset_tracking_service.record_performance_data(
            asset_id=asset.id,
            uptime_percentage=92.5,
            efficiency_rating=88.7,
            temperature=68.2,
            vibration=1.2,
            error_count=3,
            warning_count=1,
        )

        # 6. Start maintenance task
        started_task = await self.maintenance_service.start_maintenance_task(
            task_id=task.id, performer="technician_001"
        )

        # 7. Complete maintenance task
        completed_task = await self.maintenance_service.complete_maintenance_task(
            task_id=task.id,
            actual_duration=175,
            actual_cost=Decimal("285.00"),
            notes="Maintenance completed successfully",
            findings="Machine operating within normal parameters",
            recommendations="Continue with current maintenance schedule",
        )

        # 8. Update work order status
        updated_work_order = await self.work_order_service.update_work_order_status(
            work_order_id=work_order.id, status="completed"
        )

        # 9. Update asset maintenance history
        success = await self.asset_tracking_service.update_maintenance_history(
            asset_id=asset.id,
            maintenance_date=datetime.utcnow(),
            maintenance_type="preventive",
            performed_by="technician_001",
            duration_hours=2.9,
            cost=Decimal("285.00"),
            notes="Monthly preventive maintenance completed",
        )

        # Verify all components worked together
        self.assertIsNotNone(asset)
        self.assertIsNotNone(schedule)
        self.assertIsNotNone(task)
        self.assertIsNotNone(work_order)
        self.assertIsNotNone(performance)
        self.assertEqual(started_task.status, MaintenanceStatus.IN_PROGRESS)
        self.assertEqual(completed_task.status, MaintenanceStatus.COMPLETED)
        self.assertEqual(updated_work_order.status, "completed")
        self.assertTrue(success)

        # Verify asset has updated information
        updated_asset = await self.asset_tracking_service.get_asset(asset.id)
        self.assertIsNotNone(updated_asset.last_maintenance)
        self.assertIsNotNone(updated_asset.total_operating_hours)
        self.assertIsNotNone(updated_asset.total_cost)


def run_tests():
    """Run all CMMS integration tests"""
    # Create test suite
    test_suite = unittest.TestSuite()

    # Add test classes
    test_classes = [
        TestCMMSDataSynchronization,
        TestWorkOrderProcessing,
        TestMaintenanceScheduling,
        TestAssetTracking,
        TestCMMSIntegration,
    ]

    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)

    return result.wasSuccessful()


if __name__ == "__main__":
    # Run async tests
    success = asyncio.run(run_tests())

    if success:
        print("\n✅ All CMMS integration tests passed!")
    else:
        print("\n❌ Some CMMS integration tests failed!")

    exit(0 if success else 1)
