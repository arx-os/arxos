"""
Maintenance Scheduling Service for CMMS Integration

This module provides comprehensive maintenance scheduling capabilities including:
- Automated maintenance workflows
- Calendar management and scheduling
- Notification integration
- Maintenance history tracking
- Resource allocation and optimization
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


class MaintenanceType(str, Enum):
    """Types of maintenance activities"""
    PREVENTIVE = "preventive"
    CORRECTIVE = "corrective"
    PREDICTIVE = "predictive"
    EMERGENCY = "emergency"
    INSPECTION = "inspection"
    CALIBRATION = "calibration"
    CLEANING = "cleaning"
    LUBRICATION = "lubrication"


class MaintenancePriority(str, Enum):
    """Priority levels for maintenance tasks"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class MaintenanceStatus(str, Enum):
    """Status of maintenance tasks"""
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    OVERDUE = "overdue"
    ON_HOLD = "on_hold"


class MaintenanceFrequency(str, Enum):
    """Frequency types for recurring maintenance"""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    SEMI_ANNUAL = "semi_annual"
    ANNUAL = "annual"
    CUSTOM = "custom"


class MaintenanceTrigger(str, Enum):
    """Trigger types for maintenance tasks"""
    TIME_BASED = "time_based"
    USAGE_BASED = "usage_based"
    CONDITION_BASED = "condition_based"
    MANUAL = "manual"
    EVENT_BASED = "event_based"


class MaintenanceStep(BaseModel):
    """Individual step in a maintenance procedure"""
    id: UUID = Field(default_factory=uuid4)
    name: str = Field(..., description="Name of the maintenance step")
    description: str = Field(..., description="Detailed description of the step")
    estimated_duration: int = Field(..., description="Estimated duration in minutes")
    actual_duration: Optional[int] = Field(None, description="Actual duration in minutes")
    status: MaintenanceStatus = Field(default=MaintenanceStatus.SCHEDULED)
    sequence_order: int = Field(..., description="Order of execution")
    required_skills: List[str] = Field(default_factory=list)
    required_tools: List[str] = Field(default_factory=list)
    required_parts: List[str] = Field(default_factory=list)
    notes: Optional[str] = None
    completed_at: Optional[datetime] = None
    completed_by: Optional[str] = None


class MaintenanceSchedule(BaseModel):
    """Maintenance schedule configuration"""
    id: UUID = Field(default_factory=uuid4)
    name: str = Field(..., description="Name of the maintenance schedule")
    description: str = Field(..., description="Description of the maintenance schedule")
    maintenance_type: MaintenanceType = Field(..., description="Type of maintenance")
    priority: MaintenancePriority = Field(..., description="Priority level")
    frequency: MaintenanceFrequency = Field(..., description="Frequency of maintenance")
    trigger_type: MaintenanceTrigger = Field(..., description="Trigger type")
    trigger_value: Union[int, float, str] = Field(..., description="Trigger value (hours, days, etc.)")
    estimated_duration: int = Field(..., description="Estimated duration in minutes")
    estimated_cost: Decimal = Field(..., description="Estimated cost")
    required_skills: List[str] = Field(default_factory=list)
    required_tools: List[str] = Field(default_factory=list)
    required_parts: List[str] = Field(default_factory=list)
    steps: List[MaintenanceStep] = Field(default_factory=list)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_executed: Optional[datetime] = None
    next_scheduled: Optional[datetime] = None


class MaintenanceTask(BaseModel):
    """Individual maintenance task instance"""
    id: UUID = Field(default_factory=uuid4)
    schedule_id: UUID = Field(..., description="Reference to maintenance schedule")
    asset_id: str = Field(..., description="Asset identifier")
    status: MaintenanceStatus = Field(default=MaintenanceStatus.SCHEDULED)
    priority: MaintenancePriority = Field(..., description="Priority level")
    scheduled_start: datetime = Field(..., description="Scheduled start time")
    scheduled_end: datetime = Field(..., description="Scheduled end time")
    actual_start: Optional[datetime] = None
    actual_end: Optional[datetime] = None
    estimated_duration: int = Field(..., description="Estimated duration in minutes")
    actual_duration: Optional[int] = None
    estimated_cost: Decimal = Field(..., description="Estimated cost")
    actual_cost: Optional[Decimal] = None
    assigned_to: Optional[str] = None
    assigned_team: Optional[str] = None
    location: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    completed_steps: List[MaintenanceStep] = Field(default_factory=list)
    remaining_steps: List[MaintenanceStep] = Field(default_factory=list)


class MaintenanceHistory(BaseModel):
    """Maintenance history record"""
    id: UUID = Field(default_factory=uuid4)
    task_id: UUID = Field(..., description="Reference to maintenance task")
    schedule_id: UUID = Field(..., description="Reference to maintenance schedule")
    asset_id: str = Field(..., description="Asset identifier")
    maintenance_type: MaintenanceType = Field(..., description="Type of maintenance")
    status: MaintenanceStatus = Field(..., description="Final status")
    scheduled_start: datetime = Field(..., description="Originally scheduled start")
    actual_start: Optional[datetime] = None
    actual_end: Optional[datetime] = None
    duration: Optional[int] = None
    cost: Optional[Decimal] = None
    performed_by: Optional[str] = None
    notes: Optional[str] = None
    findings: Optional[str] = None
    recommendations: Optional[str] = None
    parts_used: List[str] = Field(default_factory=list)
    tools_used: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class MaintenanceCalendar(BaseModel):
    """Calendar view of maintenance activities"""
    id: UUID = Field(default_factory=uuid4)
    name: str = Field(..., description="Calendar name")
    description: Optional[str] = None
    timezone: str = Field(default="UTC", description="Timezone for calendar")
    working_hours_start: int = Field(default=8, description="Working hours start (24h)")
    working_hours_end: int = Field(default=17, description="Working hours end (24h)")
    working_days: Set[int] = Field(default={0, 1, 2, 3, 4}, description="Working days (0=Monday)")
    holidays: List[datetime] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class MaintenanceSchedulingService:
    """Service for managing maintenance scheduling and workflows"""

    def __init__(self):
        pass
    """
    Perform __init__ operation

Args:
        None

Returns:
        Description of return value

Raises:
        Exception: Description of exception

Example:
        result = __init__(param)
        print(result)
    """
        self.schedules: Dict[UUID, MaintenanceSchedule] = {}
        self.tasks: Dict[UUID, MaintenanceTask] = {}
        self.history: Dict[UUID, MaintenanceHistory] = {}
        self.calendars: Dict[UUID, MaintenanceCalendar] = {}
        self.notification_system = UnifiedNotificationSystem()

        # Initialize default calendar
        default_calendar = MaintenanceCalendar(
            name="Default Maintenance Calendar",
            description="Default calendar for maintenance scheduling"
        )
        self.calendars[default_calendar.id] = default_calendar

        logger.info("MaintenanceSchedulingService initialized")

    async def create_maintenance_schedule(
        self,
        name: str,
        description: str,
        maintenance_type: MaintenanceType,
        priority: MaintenancePriority,
        frequency: MaintenanceFrequency,
        trigger_type: MaintenanceTrigger,
        trigger_value: Union[int, float, str],
        estimated_duration: int,
        estimated_cost: Decimal,
        required_skills: List[str] = None,
        required_tools: List[str] = None,
        required_parts: List[str] = None,
        steps: List[MaintenanceStep] = None
    ) -> MaintenanceSchedule:
        """Create a new maintenance schedule"""
        schedule = MaintenanceSchedule(
            name=name,
            description=description,
            maintenance_type=maintenance_type,
            priority=priority,
            frequency=frequency,
            trigger_type=trigger_type,
            trigger_value=trigger_value,
            estimated_duration=estimated_duration,
            estimated_cost=estimated_cost,
            required_skills=required_skills or [],
            required_tools=required_tools or [],
            required_parts=required_parts or [],
            steps=steps or []
        )

        self.schedules[schedule.id] = schedule
        logger.info(f"Created maintenance schedule: {schedule.id}")
        return schedule

    async def update_maintenance_schedule(
        self,
        schedule_id: UUID,
        **kwargs
    ) -> Optional[MaintenanceSchedule]:
        """Update an existing maintenance schedule"""
        if schedule_id not in self.schedules:
            logger.warning(f"Schedule not found: {schedule_id}")
            return None

        schedule = self.schedules[schedule_id]
        for key, value in kwargs.items():
            if hasattr(schedule, key):
                setattr(schedule, key, value)

        schedule.updated_at = datetime.utcnow()
        logger.info(f"Updated maintenance schedule: {schedule_id}")
        return schedule

    async def delete_maintenance_schedule(self, schedule_id: UUID) -> bool:
        """Delete a maintenance schedule"""
        if schedule_id not in self.schedules:
            logger.warning(f"Schedule not found: {schedule_id}")
            return False

        del self.schedules[schedule_id]
        logger.info(f"Deleted maintenance schedule: {schedule_id}")
        return True

    async def get_maintenance_schedule(self, schedule_id: UUID) -> Optional[MaintenanceSchedule]:
        """Get a maintenance schedule by ID"""
        return self.schedules.get(schedule_id)

    async def get_all_maintenance_schedules(self) -> List[MaintenanceSchedule]:
        """Get all maintenance schedules"""
        return list(self.schedules.values()
    async def create_maintenance_task(
        self,
        schedule_id: UUID,
        asset_id: str,
        scheduled_start: datetime,
        priority: Optional[MaintenancePriority] = None,
        assigned_to: Optional[str] = None,
        assigned_team: Optional[str] = None,
        location: Optional[str] = None,
        notes: Optional[str] = None
    ) -> Optional[MaintenanceTask]:
        """Create a new maintenance task"""
        if schedule_id not in self.schedules:
            logger.warning(f"Schedule not found: {schedule_id}")
            return None

        schedule = self.schedules[schedule_id]
        scheduled_end = scheduled_start + timedelta(minutes=schedule.estimated_duration)

        task = MaintenanceTask(
            schedule_id=schedule_id,
            asset_id=asset_id,
            priority=priority or schedule.priority,
            scheduled_start=scheduled_start,
            scheduled_end=scheduled_end,
            estimated_duration=schedule.estimated_duration,
            estimated_cost=schedule.estimated_cost,
            assigned_to=assigned_to,
            assigned_team=assigned_team,
            location=location,
            notes=notes,
            remaining_steps=schedule.steps.copy()
        self.tasks[task.id] = task
        logger.info(f"Created maintenance task: {task.id}")

        # Send notification for new task
        await self._send_task_notification(task, "created")

        return task

    async def update_maintenance_task(
        self,
        task_id: UUID,
        **kwargs
    ) -> Optional[MaintenanceTask]:
        """Update a maintenance task"""
        if task_id not in self.tasks:
            logger.warning(f"Task not found: {task_id}")
            return None

        task = self.tasks[task_id]
        old_status = task.status

        for key, value in kwargs.items():
            if hasattr(task, key):
                setattr(task, key, value)

        task.updated_at = datetime.utcnow()

        # Handle status changes
        if 'status' in kwargs and kwargs['status'] != old_status:
            await self._handle_status_change(task, old_status, kwargs['status'])

        logger.info(f"Updated maintenance task: {task_id}")
        return task

    async def start_maintenance_task(self, task_id: UUID, performer: str) -> Optional[MaintenanceTask]:
        """Start a maintenance task"""
        task = await self.get_maintenance_task(task_id)
        if not task:
            return None

        if task.status != MaintenanceStatus.SCHEDULED:
            logger.warning(f"Cannot start task {task_id}: status is {task.status}")
            return None

        task.status = MaintenanceStatus.IN_PROGRESS
        task.actual_start = datetime.utcnow()
        task.assigned_to = performer

        await self._send_task_notification(task, "started")
        logger.info(f"Started maintenance task: {task_id}")
        return task

    async def complete_maintenance_task(
        self,
        task_id: UUID,
        actual_duration: Optional[int] = None,
        actual_cost: Optional[Decimal] = None,
        notes: Optional[str] = None,
        findings: Optional[str] = None,
        recommendations: Optional[str] = None
    ) -> Optional[MaintenanceTask]:
        """Complete a maintenance task"""
        task = await self.get_maintenance_task(task_id)
        if not task:
            return None

        if task.status != MaintenanceStatus.IN_PROGRESS:
            logger.warning(f"Cannot complete task {task_id}: status is {task.status}")
            return None

        task.status = MaintenanceStatus.COMPLETED
        task.actual_end = datetime.utcnow()
        task.actual_duration = actual_duration
        task.actual_cost = actual_cost
        task.notes = notes

        # Create history record
        history = MaintenanceHistory(
            task_id=task.id,
            schedule_id=task.schedule_id,
            asset_id=task.asset_id,
            maintenance_type=self.schedules[task.schedule_id].maintenance_type,
            status=task.status,
            scheduled_start=task.scheduled_start,
            actual_start=task.actual_start,
            actual_end=task.actual_end,
            duration=task.actual_duration,
            cost=task.actual_cost,
            performed_by=task.assigned_to,
            notes=notes,
            findings=findings,
            recommendations=recommendations
        )

        self.history[history.id] = history

        # Update schedule last executed
        schedule = self.schedules[task.schedule_id]
        schedule.last_executed = datetime.utcnow()
        schedule.next_scheduled = await self._calculate_next_schedule(schedule)

        await self._send_task_notification(task, "completed")
        logger.info(f"Completed maintenance task: {task_id}")
        return task

    async def get_maintenance_task(self, task_id: UUID) -> Optional[MaintenanceTask]:
        """Get a maintenance task by ID"""
        return self.tasks.get(task_id)

    async def get_maintenance_tasks(
        self,
        status: Optional[MaintenanceStatus] = None,
        asset_id: Optional[str] = None,
        assigned_to: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[MaintenanceTask]:
        """Get maintenance tasks with optional filters"""
        tasks = list(self.tasks.values()
        if status:
            tasks = [t for t in tasks if t.status == status]
        if asset_id:
            tasks = [t for t in tasks if t.asset_id == asset_id]
        if assigned_to:
            tasks = [t for t in tasks if t.assigned_to == assigned_to]
        if start_date:
            tasks = [t for t in tasks if t.scheduled_start >= start_date]
        if end_date:
            tasks = [t for t in tasks if t.scheduled_start <= end_date]

        return tasks

    async def get_maintenance_history(
        self,
        asset_id: Optional[str] = None,
        maintenance_type: Optional[MaintenanceType] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[MaintenanceHistory]:
        """Get maintenance history with optional filters"""
        history = list(self.history.values()
        if asset_id:
            history = [h for h in history if h.asset_id == asset_id]
        if maintenance_type:
            history = [h for h in history if h.maintenance_type == maintenance_type]
        if start_date:
            history = [h for h in history if h.actual_start >= start_date]
        if end_date:
            history = [h for h in history if h.actual_start <= end_date]

        return history

    async def schedule_recurring_maintenance(self) -> List[MaintenanceTask]:
        """Schedule recurring maintenance tasks based on schedules"""
        new_tasks = []
        current_time = datetime.utcnow()

        for schedule in self.schedules.values():
            if not schedule.is_active:
                continue

            # Check if it's time to schedule next maintenance'
            if schedule.next_scheduled and schedule.next_scheduled <= current_time:
                # Find assets that need this maintenance
                assets = await self._get_assets_for_maintenance(schedule)

                for asset_id in assets:
                    task = await self.create_maintenance_task(
                        schedule_id=schedule.id,
                        asset_id=asset_id,
                        scheduled_start=schedule.next_scheduled,
                        priority=schedule.priority
                    )
                    if task:
                        new_tasks.append(task)

                # Update next scheduled time
                schedule.next_scheduled = await self._calculate_next_schedule(schedule)

        logger.info(f"Scheduled {len(new_tasks)} new maintenance tasks")
        return new_tasks

    async def get_maintenance_calendar(
        self,
        calendar_id: UUID,
        start_date: datetime,
        end_date: datetime
    ) -> List[MaintenanceTask]:
        """Get maintenance tasks for calendar view"""
        if calendar_id not in self.calendars:
            logger.warning(f"Calendar not found: {calendar_id}")
            return []

        tasks = await self.get_maintenance_tasks(
            start_date=start_date,
            end_date=end_date
        )

        return tasks

    async def create_maintenance_calendar(
        self,
        name: str,
        description: Optional[str] = None,
        timezone: str = "UTC",
        working_hours_start: int = 8,
        working_hours_end: int = 17,
        working_days: Set[int] = None,
        holidays: List[datetime] = None
    ) -> MaintenanceCalendar:
        """Create a new maintenance calendar"""
        calendar = MaintenanceCalendar(
            name=name,
            description=description,
            timezone=timezone,
            working_hours_start=working_hours_start,
            working_hours_end=working_hours_end,
            working_days=working_days or {0, 1, 2, 3, 4},
            holidays=holidays or []
        )

        self.calendars[calendar.id] = calendar
        logger.info(f"Created maintenance calendar: {calendar.id}")
        return calendar

    async def _calculate_next_schedule(self, schedule: MaintenanceSchedule) -> datetime:
        """Calculate next scheduled maintenance time"""
        base_time = schedule.last_executed or datetime.utcnow()

        if schedule.frequency == MaintenanceFrequency.DAILY:
            return base_time + timedelta(days=1)
        elif schedule.frequency == MaintenanceFrequency.WEEKLY:
            return base_time + timedelta(weeks=1)
        elif schedule.frequency == MaintenanceFrequency.MONTHLY:
            return base_time + timedelta(days=30)
        elif schedule.frequency == MaintenanceFrequency.QUARTERLY:
            return base_time + timedelta(days=90)
        elif schedule.frequency == MaintenanceFrequency.SEMI_ANNUAL:
            return base_time + timedelta(days=180)
        elif schedule.frequency == MaintenanceFrequency.ANNUAL:
            return base_time + timedelta(days=365)
        else:
            # Custom frequency based on trigger_value
            if isinstance(schedule.trigger_value, (int, float)):
                return base_time + timedelta(days=schedule.trigger_value)
            else:
                return base_time + timedelta(days=30)  # Default to monthly

    async def _get_assets_for_maintenance(self, schedule: MaintenanceSchedule) -> List[str]:
        """Get assets that need maintenance based on schedule"""
        # This would typically query the asset management system
        # For now, return a mock list of assets
        return [f"asset_{i}" for i in range(1, 6)]

    async def _handle_status_change(
        self,
        task: MaintenanceTask,
        old_status: MaintenanceStatus,
        new_status: MaintenanceStatus
    ):
        """Handle status changes and trigger appropriate actions"""
        if new_status == MaintenanceStatus.OVERDUE:
            await self._send_task_notification(task, "overdue")
        elif new_status == MaintenanceStatus.IN_PROGRESS:
            await self._send_task_notification(task, "started")
        elif new_status == MaintenanceStatus.COMPLETED:
            await self._send_task_notification(task, "completed")

    async def _send_task_notification(self, task: MaintenanceTask, event_type: str):
        """Send notification for task events"""
        try:
            schedule = self.schedules[task.schedule_id]
            subject = f"Maintenance Task {event_type.title()}: {schedule.name}"
            message = f"""
            Maintenance Task {event_type.title()}

            Task ID: {task.id}
            Asset: {task.asset_id}
            Type: {schedule.maintenance_type.value}
            Priority: {task.priority.value}
            Status: {task.status.value}
            Scheduled: {task.scheduled_start}

            {task.notes or ''}
            """

            # Send to assigned person if available
            if task.assigned_to:
                await self.notification_system.send_email_notification(
                    to_email=task.assigned_to,
                    subject=subject,
                    message=message
                )

            # Send to team if assigned
            if task.assigned_team:
                await self.notification_system.send_slack_notification(
                    channel=task.assigned_team,
                    message=f"Maintenance task {event_type}: {schedule.name} for asset {task.asset_id}"
                )

        except Exception as e:
            logger.error(f"Failed to send notification for task {task.id}: {e}")

    async def get_maintenance_statistics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict:
        """Get maintenance statistics"""
        tasks = await self.get_maintenance_tasks(start_date=start_date, end_date=end_date)
        history = await self.get_maintenance_history(start_date=start_date, end_date=end_date)

        total_tasks = len(tasks)
        completed_tasks = len([t for t in tasks if t.status == MaintenanceStatus.COMPLETED])
        overdue_tasks = len([t for t in tasks if t.status == MaintenanceStatus.OVERDUE])
        in_progress_tasks = len([t for t in tasks if t.status == MaintenanceStatus.IN_PROGRESS])

        total_cost = sum(h.cost or Decimal(0) for h in history)
        total_duration = sum(h.duration or 0 for h in history)

        return {
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "overdue_tasks": overdue_tasks,
            "in_progress_tasks": in_progress_tasks,
            "completion_rate": (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0,
            "total_cost": float(total_cost),
            "total_duration_hours": total_duration / 60 if total_duration else 0,
            "average_cost_per_task": float(total_cost / len(history)) if history else 0,
            "average_duration_per_task": (total_duration / len(history)) if history else 0
        }
