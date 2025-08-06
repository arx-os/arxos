"""
Work Order Processing Service for Arxos SVG-BIM Integration

This service provides comprehensive work order processing including
automated workflows, status management, resource allocation, and
integration with maintenance schedules and asset tracking.

Author: Arxos Engineering Team
Date: 2024-12-19
Version: 1.0.0
"""

import json
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field
from enum import Enum
import uuid

logger = logging.getLogger(__name__)


class WorkOrderStatus(Enum):
    """Work order status."""

    DRAFT = "draft"
    OPEN = "open"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    ON_HOLD = "on_hold"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    CLOSED = "closed"


class WorkOrderPriority(Enum):
    """Work order priority."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


class WorkOrderType(Enum):
    """Work order type."""

    PREVENTIVE = "preventive"
    PREDICTIVE = "predictive"
    CORRECTIVE = "corrective"
    EMERGENCY = "emergency"
    INSPECTION = "inspection"
    CALIBRATION = "calibration"


class WorkOrderSource(Enum):
    """Work order source."""

    MANUAL = "manual"
    SCHEDULE = "schedule"
    ASSET_FAILURE = "asset_failure"
    INSPECTION = "inspection"
    CMMS_SYNC = "cmms_sync"


@dataclass
class WorkOrderStep:
    """Work order step."""

    step_id: str
    work_order_id: str
    title: str
    description: Optional[str] = None
    sequence: int = 0
    estimated_duration: float = 0.0  # hours
    actual_duration: float = 0.0  # hours
    status: str = "pending"  # pending, in_progress, completed, skipped
    assigned_to: Optional[str] = None
    completed_by: Optional[str] = None
    completed_at: Optional[datetime] = None
    notes: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class WorkOrderPart:
    """Work order part."""

    part_id: str
    work_order_id: str
    part_number: str
    description: str
    quantity: float = 1.0
    unit_cost: float = 0.0
    total_cost: float = 0.0
    location: Optional[str] = None
    status: str = "required"  # required, issued, used, returned
    issued_at: Optional[datetime] = None
    used_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class WorkOrder:
    """Work order data model."""

    work_order_id: str
    work_order_number: str
    title: str
    description: Optional[str] = None
    work_order_type: WorkOrderType
    priority: WorkOrderPriority
    status: WorkOrderStatus
    source: WorkOrderSource
    asset_id: Optional[str] = None
    location: Optional[str] = None
    assigned_to: Optional[str] = None
    requested_by: Optional[str] = None
    estimated_hours: float = 0.0
    actual_hours: float = 0.0
    estimated_cost: float = 0.0
    actual_cost: float = 0.0
    scheduled_date: Optional[datetime] = None
    started_date: Optional[datetime] = None
    completed_date: Optional[datetime] = None
    due_date: Optional[datetime] = None
    safety_requirements: Optional[str] = None
    special_instructions: Optional[str] = None
    attachments: Optional[List[Dict[str, Any]]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class WorkOrderTemplate:
    """Work order template."""

    template_id: str
    name: str
    description: Optional[str] = None
    work_order_type: WorkOrderType
    asset_type: Optional[str] = None
    steps: List[Dict[str, Any]] = field(default_factory=list)
    estimated_hours: float = 0.0
    estimated_cost: float = 0.0
    safety_requirements: Optional[str] = None
    special_instructions: Optional[str] = None
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


class WorkOrderProcessingService:
    """
    Work Order Processing Service with enterprise-grade features.

    Provides:
    - Work order creation and management
    - Automated workflow processing
    - Status tracking and transitions
    - Resource allocation and scheduling
    - Integration with maintenance schedules
    - Cost tracking and reporting
    - Safety and compliance management
    """

    def __init__(self):
        """Initialize the work order processing service."""
        self.work_orders: Dict[str, WorkOrder] = {}
        self.work_order_steps: Dict[str, List[WorkOrderStep]] = {}
        self.work_order_parts: Dict[str, List[WorkOrderPart]] = {}
        self.templates: Dict[str, WorkOrderTemplate] = {}
        self.statistics = {
            "total_work_orders": 0,
            "open_work_orders": 0,
            "completed_work_orders": 0,
            "overdue_work_orders": 0,
            "average_completion_time": 0.0,
            "total_cost": 0.0,
            "total_hours": 0.0,
        }

        logger.info("Work Order Processing Service initialized")

    def create_work_order(
        self,
        title: str,
        description: Optional[str] = None,
        work_order_type: WorkOrderType = WorkOrderType.CORRECTIVE,
        priority: WorkOrderPriority = WorkOrderPriority.MEDIUM,
        source: WorkOrderSource = WorkOrderSource.MANUAL,
        asset_id: Optional[str] = None,
        location: Optional[str] = None,
        assigned_to: Optional[str] = None,
        requested_by: Optional[str] = None,
        estimated_hours: float = 0.0,
        scheduled_date: Optional[datetime] = None,
        due_date: Optional[datetime] = None,
        safety_requirements: Optional[str] = None,
        special_instructions: Optional[str] = None,
    ) -> str:
        """
        Create a new work order.

        Args:
            title: Work order title
            description: Work order description
            work_order_type: Type of work order
            priority: Work order priority
            source: Source of work order
            asset_id: Associated asset ID
            location: Work location
            assigned_to: Assigned technician
            requested_by: Person who requested the work
            estimated_hours: Estimated hours to complete
            scheduled_date: Scheduled start date
            due_date: Due date
            safety_requirements: Safety requirements
            special_instructions: Special instructions

        Returns:
            Work order ID
        """
        work_order_id = str(uuid.uuid4())
        work_order_number = self._generate_work_order_number()

        work_order = WorkOrder(
            work_order_id=work_order_id,
            work_order_number=work_order_number,
            title=title,
            description=description,
            work_order_type=work_order_type,
            priority=priority,
            status=WorkOrderStatus.DRAFT,
            source=source,
            asset_id=asset_id,
            location=location,
            assigned_to=assigned_to,
            requested_by=requested_by,
            estimated_hours=estimated_hours,
            scheduled_date=scheduled_date,
            due_date=due_date,
            safety_requirements=safety_requirements,
            special_instructions=special_instructions,
        )

        self.work_orders[work_order_id] = work_order
        self.work_order_steps[work_order_id] = []
        self.work_order_parts[work_order_id] = []

        self.statistics["total_work_orders"] += 1

        logger.info(f"Created work order: {work_order_number} - {title}")
        return work_order_id

    def create_work_order_from_template(
        self,
        template_id: str,
        title: str,
        asset_id: Optional[str] = None,
        location: Optional[str] = None,
        assigned_to: Optional[str] = None,
        scheduled_date: Optional[datetime] = None,
        due_date: Optional[datetime] = None,
    ) -> str:
        """
        Create a work order from template.

        Args:
            template_id: Template ID
            title: Work order title
            asset_id: Associated asset ID
            location: Work location
            assigned_to: Assigned technician
            scheduled_date: Scheduled start date
            due_date: Due date

        Returns:
            Work order ID
        """
        template = self.templates.get(template_id)
        if not template:
            raise ValueError(f"Template not found: {template_id}")

        work_order_id = self.create_work_order(
            title=title,
            description=template.description,
            work_order_type=template.work_order_type,
            priority=WorkOrderPriority.MEDIUM,
            source=WorkOrderSource.SCHEDULE,
            asset_id=asset_id,
            location=location,
            assigned_to=assigned_to,
            scheduled_date=scheduled_date,
            due_date=due_date,
            safety_requirements=template.safety_requirements,
            special_instructions=template.special_instructions,
        )

        # Create steps from template
        for step_data in template.steps:
            self.add_work_order_step(
                work_order_id=work_order_id,
                title=step_data["title"],
                description=step_data.get("description"),
                sequence=step_data.get("sequence", 0),
                estimated_duration=step_data.get("estimated_duration", 0.0),
            )

        return work_order_id

    def add_work_order_step(
        self,
        work_order_id: str,
        title: str,
        description: Optional[str] = None,
        sequence: int = 0,
        estimated_duration: float = 0.0,
        assigned_to: Optional[str] = None,
    ) -> str:
        """
        Add a step to a work order.

        Args:
            work_order_id: Work order ID
            title: Step title
            description: Step description
            sequence: Step sequence number
            estimated_duration: Estimated duration in hours
            assigned_to: Assigned technician

        Returns:
            Step ID
        """
        if work_order_id not in self.work_orders:
            raise ValueError(f"Work order not found: {work_order_id}")

        step_id = str(uuid.uuid4())
        step = WorkOrderStep(
            step_id=step_id,
            work_order_id=work_order_id,
            title=title,
            description=description,
            sequence=sequence,
            estimated_duration=estimated_duration,
            assigned_to=assigned_to,
        )

        if work_order_id not in self.work_order_steps:
            self.work_order_steps[work_order_id] = []

        self.work_order_steps[work_order_id].append(step)

        # Update work order estimated hours
        work_order = self.work_orders[work_order_id]
        work_order.estimated_hours += estimated_duration

        logger.info(f"Added step to work order {work_order.work_order_number}: {title}")
        return step_id

    def add_work_order_part(
        self,
        work_order_id: str,
        part_number: str,
        description: str,
        quantity: float = 1.0,
        unit_cost: float = 0.0,
        location: Optional[str] = None,
    ) -> str:
        """
        Add a part to a work order.

        Args:
            work_order_id: Work order ID
            part_number: Part number
            description: Part description
            quantity: Quantity needed
            unit_cost: Unit cost
            location: Part location

        Returns:
            Part ID
        """
        if work_order_id not in self.work_orders:
            raise ValueError(f"Work order not found: {work_order_id}")

        part_id = str(uuid.uuid4())
        total_cost = quantity * unit_cost

        part = WorkOrderPart(
            part_id=part_id,
            work_order_id=work_order_id,
            part_number=part_number,
            description=description,
            quantity=quantity,
            unit_cost=unit_cost,
            total_cost=total_cost,
            location=location,
        )

        if work_order_id not in self.work_order_parts:
            self.work_order_parts[work_order_id] = []

        self.work_order_parts[work_order_id].append(part)

        # Update work order estimated cost
        work_order = self.work_orders[work_order_id]
        work_order.estimated_cost += total_cost

        logger.info(
            f"Added part to work order {work_order.work_order_number}: {part_number}"
        )
        return part_id

    def update_work_order_status(
        self,
        work_order_id: str,
        status: WorkOrderStatus,
        updated_by: Optional[str] = None,
    ) -> None:
        """
        Update work order status.

        Args:
            work_order_id: Work order ID
            status: New status
            updated_by: User who updated the status
        """
        if work_order_id not in self.work_orders:
            raise ValueError(f"Work order not found: {work_order_id}")

        work_order = self.work_orders[work_order_id]
        old_status = work_order.status
        work_order.status = status
        work_order.updated_at = datetime.now()

        # Update timestamps based on status
        if status == WorkOrderStatus.IN_PROGRESS and not work_order.started_date:
            work_order.started_date = datetime.now()
        elif status == WorkOrderStatus.COMPLETED and not work_order.completed_date:
            work_order.completed_date = datetime.now()
            self._calculate_actual_hours_and_cost(work_order_id)

        # Update statistics
        self._update_statistics_for_status_change(old_status, status)

        logger.info(
            f"Updated work order {work_order.work_order_number} status: {old_status.value} -> {status.value}"
        )

    def assign_work_order(self, work_order_id: str, assigned_to: str) -> None:
        """
        Assign work order to technician.

        Args:
            work_order_id: Work order ID
            assigned_to: Technician ID
        """
        if work_order_id not in self.work_orders:
            raise ValueError(f"Work order not found: {work_order_id}")

        work_order = self.work_orders[work_order_id]
        work_order.assigned_to = assigned_to
        work_order.status = WorkOrderStatus.ASSIGNED
        work_order.updated_at = datetime.now()

        logger.info(
            f"Assigned work order {work_order.work_order_number} to {assigned_to}"
        )

    def complete_work_order_step(
        self,
        step_id: str,
        completed_by: str,
        actual_duration: float = 0.0,
        notes: Optional[str] = None,
    ) -> None:
        """
        Complete a work order step.

        Args:
            step_id: Step ID
            completed_by: User who completed the step
            actual_duration: Actual duration in hours
            notes: Completion notes
        """
        work_order_id = None
        step = None

        # Find the step
        for wo_id, steps in self.work_order_steps.items():
            for s in steps:
                if s.step_id == step_id:
                    step = s
                    work_order_id = wo_id
                    break
            if step:
                break

        if not step:
            raise ValueError(f"Step not found: {step_id}")

        step.status = "completed"
        step.completed_by = completed_by
        step.completed_at = datetime.now()
        step.actual_duration = actual_duration
        step.notes = notes
        step.updated_at = datetime.now()

        # Update work order actual hours
        work_order = self.work_orders[work_order_id]
        work_order.actual_hours += actual_duration

        logger.info(f"Completed step: {step.title}")

    def issue_work_order_part(self, part_id: str, issued_by: str) -> None:
        """
        Issue a work order part.

        Args:
            part_id: Part ID
            issued_by: User who issued the part
        """
        part = self._find_part(part_id)
        if not part:
            raise ValueError(f"Part not found: {part_id}")

        part.status = "issued"
        part.issued_at = datetime.now()
        part.updated_at = datetime.now()

        logger.info(f"Issued part: {part.part_number}")

    def use_work_order_part(self, part_id: str, used_by: str) -> None:
        """
        Mark a work order part as used.

        Args:
            part_id: Part ID
            used_by: User who used the part
        """
        part = self._find_part(part_id)
        if not part:
            raise ValueError(f"Part not found: {part_id}")

        part.status = "used"
        part.used_at = datetime.now()
        part.updated_at = datetime.now()

        # Update work order actual cost
        work_order = self.work_orders[part.work_order_id]
        work_order.actual_cost += part.total_cost

        logger.info(f"Used part: {part.part_number}")

    def get_work_order(self, work_order_id: str) -> Optional[WorkOrder]:
        """Get work order by ID."""
        return self.work_orders.get(work_order_id)

    def get_work_orders(
        self,
        status: Optional[WorkOrderStatus] = None,
        assigned_to: Optional[str] = None,
        asset_id: Optional[str] = None,
    ) -> List[WorkOrder]:
        """
        Get work orders with optional filtering.

        Args:
            status: Filter by status
            assigned_to: Filter by assigned technician
            asset_id: Filter by asset ID

        Returns:
            List of work orders
        """
        work_orders = list(self.work_orders.values())

        if status:
            work_orders = [wo for wo in work_orders if wo.status == status]

        if assigned_to:
            work_orders = [wo for wo in work_orders if wo.assigned_to == assigned_to]

        if asset_id:
            work_orders = [wo for wo in work_orders if wo.asset_id == asset_id]

        return work_orders

    def get_overdue_work_orders(self) -> List[WorkOrder]:
        """Get overdue work orders."""
        overdue = []
        now = datetime.now()

        for work_order in self.work_orders.values():
            if (
                work_order.due_date
                and work_order.due_date < now
                and work_order.status
                not in [
                    WorkOrderStatus.COMPLETED,
                    WorkOrderStatus.CANCELLED,
                    WorkOrderStatus.CLOSED,
                ]
            ):
                overdue.append(work_order)

        return overdue

    def get_work_order_steps(self, work_order_id: str) -> List[WorkOrderStep]:
        """Get work order steps."""
        return self.work_order_steps.get(work_order_id, [])

    def get_work_order_parts(self, work_order_id: str) -> List[WorkOrderPart]:
        """Get work order parts."""
        return self.work_order_parts.get(work_order_id, [])

    def create_template(
        self,
        name: str,
        description: Optional[str] = None,
        work_order_type: WorkOrderType = WorkOrderType.PREVENTIVE,
        asset_type: Optional[str] = None,
        steps: Optional[List[Dict[str, Any]]] = None,
        estimated_hours: float = 0.0,
        estimated_cost: float = 0.0,
        safety_requirements: Optional[str] = None,
        special_instructions: Optional[str] = None,
    ) -> str:
        """
        Create a work order template.

        Args:
            name: Template name
            description: Template description
            work_order_type: Work order type
            asset_type: Asset type
            steps: List of step definitions
            estimated_hours: Estimated hours
            estimated_cost: Estimated cost
            safety_requirements: Safety requirements
            special_instructions: Special instructions

        Returns:
            Template ID
        """
        template_id = str(uuid.uuid4())

        template = WorkOrderTemplate(
            template_id=template_id,
            name=name,
            description=description,
            work_order_type=work_order_type,
            asset_type=asset_type,
            steps=steps or [],
            estimated_hours=estimated_hours,
            estimated_cost=estimated_cost,
            safety_requirements=safety_requirements,
            special_instructions=special_instructions,
        )

        self.templates[template_id] = template

        logger.info(f"Created work order template: {name}")
        return template_id

    def get_template(self, template_id: str) -> Optional[WorkOrderTemplate]:
        """Get template by ID."""
        return self.templates.get(template_id)

    def get_templates(
        self,
        work_order_type: Optional[WorkOrderType] = None,
        asset_type: Optional[str] = None,
    ) -> List[WorkOrderTemplate]:
        """
        Get templates with optional filtering.

        Args:
            work_order_type: Filter by work order type
            asset_type: Filter by asset type

        Returns:
            List of templates
        """
        templates = list(self.templates.values())

        if work_order_type:
            templates = [t for t in templates if t.work_order_type == work_order_type]

        if asset_type:
            templates = [t for t in templates if t.asset_type == asset_type]

        return templates

    def _generate_work_order_number(self) -> str:
        """Generate unique work order number."""
        timestamp = datetime.now().strftime("%Y%m%d")
        count = (
            len(
                [
                    wo
                    for wo in self.work_orders.values()
                    if wo.created_at.date() == datetime.now().date()
                ]
            )
            + 1
        )
        return f"WO-{timestamp}-{count:04d}"

    def _find_part(self, part_id: str) -> Optional[WorkOrderPart]:
        """Find part by ID."""
        for parts in self.work_order_parts.values():
            for part in parts:
                if part.part_id == part_id:
                    return part
        return None

    def _calculate_actual_hours_and_cost(self, work_order_id: str) -> None:
        """Calculate actual hours and cost for completed work order."""
        work_order = self.work_orders[work_order_id]

        # Calculate actual hours from steps
        steps = self.work_order_steps.get(work_order_id, [])
        actual_hours = sum(
            step.actual_duration for step in steps if step.status == "completed"
        )
        work_order.actual_hours = actual_hours

        # Calculate actual cost from parts
        parts = self.work_order_parts.get(work_order_id, [])
        actual_cost = sum(part.total_cost for part in parts if part.status == "used")
        work_order.actual_cost = actual_cost

        # Update statistics
        self.statistics["total_hours"] += actual_hours
        self.statistics["total_cost"] += actual_cost

    def _update_statistics_for_status_change(
        self, old_status: WorkOrderStatus, new_status: WorkOrderStatus
    ) -> None:
        """Update statistics when work order status changes."""
        if old_status == WorkOrderStatus.OPEN and new_status != WorkOrderStatus.OPEN:
            self.statistics["open_work_orders"] -= 1
        elif new_status == WorkOrderStatus.OPEN and old_status != WorkOrderStatus.OPEN:
            self.statistics["open_work_orders"] += 1
        elif new_status == WorkOrderStatus.COMPLETED:
            self.statistics["completed_work_orders"] += 1

    def get_work_order_statistics(self) -> Dict[str, Any]:
        """Get work order statistics."""
        # Calculate overdue work orders
        overdue_count = len(self.get_overdue_work_orders())
        self.statistics["overdue_work_orders"] = overdue_count

        # Calculate average completion time
        completed_work_orders = [
            wo
            for wo in self.work_orders.values()
            if wo.status == WorkOrderStatus.COMPLETED and wo.completed_date
        ]

        if completed_work_orders:
            total_completion_time = sum(
                (wo.completed_date - wo.created_at).total_seconds()
                / 3600  # Convert to hours
                for wo in completed_work_orders
            )
            self.statistics["average_completion_time"] = total_completion_time / len(
                completed_work_orders
            )

        return self.statistics.copy()


# Factory function
def create_work_order_processing_service() -> WorkOrderProcessingService:
    """Create a work order processing service instance."""
    return WorkOrderProcessingService()
