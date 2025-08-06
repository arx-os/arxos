"""
Moderation Queue System
Sortable moderation queue with response timer alerting and efficient flag management
"""

import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import logging
import json
from collections import defaultdict, Counter

logger = logging.getLogger(__name__)


class QueueSortOption(Enum):
    """Moderation queue sorting options"""

    PRIORITY_TIME = "priority_time"  # Priority then creation time
    CREATION_TIME = "creation_time"  # Oldest first
    RESPONSE_TIME = "response_time"  # Most overdue first
    CATEGORY = "category"  # By violation category
    TARGET_USER = "target_user"  # By flagged user
    REPORTER = "reporter"  # By reporting user


class QueueFilterOption(Enum):
    """Moderation queue filtering options"""

    ALL = "all"
    PENDING = "pending"
    UNDER_REVIEW = "under_review"
    OVERDUE = "overdue"
    CRITICAL = "critical"
    HIGH_PRIORITY = "high_priority"
    ASSIGNED_TO_ME = "assigned_to_me"
    UNASSIGNED = "unassigned"


@dataclass
class ModerationTask:
    """Moderation task with priority and timing"""

    flag_id: str
    priority: str
    category: str
    created_at: datetime
    overdue_hours: float
    assigned_moderator: Optional[str]
    target_user: str
    reporter: str
    content_type: str
    description: str
    evidence_count: int
    response_target_hours: int
    is_escalated: bool


@dataclass
class ModeratorWorkload:
    """Moderator workload statistics"""

    moderator_id: str
    total_assigned: int
    pending_review: int
    overdue_count: int
    avg_response_time: float
    categories_handled: List[str]
    last_activity: datetime


@dataclass
class QueueAlert:
    """Queue alert for overdue or critical flags"""

    id: str
    alert_type: str  # "overdue", "critical", "escalation"
    flag_id: str
    message: str
    created_at: datetime
    acknowledged: bool
    acknowledged_by: Optional[str]
    acknowledged_at: Optional[datetime]

    def __post_init__(self):
        if self.acknowledged_at is None:
            self.acknowledged_at = None


class ModerationQueue:
    """Enhanced moderation queue with sorting and alerting"""

    def __init__(self):
        self.queue_alerts: Dict[str, QueueAlert] = {}
        self.moderator_workloads: Dict[str, ModeratorWorkload] = {}
        self.alert_configs: Dict[str, Dict] = {}
        self.auto_assign_enabled: bool = True
        self.escalation_threshold_hours: int = 72

        self.logger = logging.getLogger(__name__)

        self._initialize_alert_configs()

    def _initialize_alert_configs(self):
        """Initialize alert configurations"""

        self.alert_configs = {
            "overdue": {
                "enabled": True,
                "threshold_hours": 24,
                "repeat_interval_hours": 12,
                "priority": "medium",
            },
            "critical": {
                "enabled": True,
                "threshold_hours": 12,
                "repeat_interval_hours": 6,
                "priority": "high",
            },
            "escalation": {
                "enabled": True,
                "threshold_hours": 72,
                "repeat_interval_hours": 24,
                "priority": "high",
            },
            "workload": {"enabled": True, "max_assigned": 10, "priority": "medium"},
        }

    def get_sorted_queue(
        self,
        sort_by: QueueSortOption = QueueSortOption.PRIORITY_TIME,
        filter_by: QueueFilterOption = QueueFilterOption.ALL,
        moderator_id: str = None,
        limit: int = 50,
    ) -> List[ModerationTask]:
        """Get sorted and filtered moderation queue"""

        from services.planarx.planarx_community.mod.flagging import flagging_system

        # Get all flags
        flags = list(flagging_system.flags.values())

        # Apply filters
        flags = self._apply_queue_filters(flags, filter_by, moderator_id)

        # Convert to tasks
        tasks = [self._flag_to_task(flag) for flag in flags]

        # Sort tasks
        tasks = self._sort_tasks(tasks, sort_by)

        return tasks[:limit]

    def _apply_queue_filters(
        self, flags: List, filter_by: QueueFilterOption, moderator_id: str = None
    ) -> List:
        """Apply queue filters"""

        if filter_by == QueueFilterOption.ALL:
            return flags

        elif filter_by == QueueFilterOption.PENDING:
            return [f for f in flags if f.status.value == "pending"]

        elif filter_by == QueueFilterOption.UNDER_REVIEW:
            return [f for f in flags if f.status.value == "under_review"]

        elif filter_by == QueueFilterOption.OVERDUE:
            return [f for f in flags if self._is_flag_overdue(f)]

        elif filter_by == QueueFilterOption.CRITICAL:
            return [f for f in flags if f.priority.value == "critical"]

        elif filter_by == QueueFilterOption.HIGH_PRIORITY:
            return [f for f in flags if f.priority.value in ["critical", "high"]]

        elif filter_by == QueueFilterOption.ASSIGNED_TO_ME:
            if not moderator_id:
                return []
            return [f for f in flags if f.assigned_moderator_id == moderator_id]

        elif filter_by == QueueFilterOption.UNASSIGNED:
            return [f for f in flags if not f.assigned_moderator_id]

        return flags

    def _sort_tasks(
        self, tasks: List[ModerationTask], sort_by: QueueSortOption
    ) -> List[ModerationTask]:
        """Sort moderation tasks"""

        if sort_by == QueueSortOption.PRIORITY_TIME:
            # Sort by priority (critical, high, medium, low) then creation time
            priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
            return sorted(
                tasks, key=lambda t: (priority_order.get(t.priority, 4), t.created_at)
            )

        elif sort_by == QueueSortOption.CREATION_TIME:
            return sorted(tasks, key=lambda t: t.created_at)

        elif sort_by == QueueSortOption.RESPONSE_TIME:
            return sorted(tasks, key=lambda t: t.overdue_hours, reverse=True)

        elif sort_by == QueueSortOption.CATEGORY:
            return sorted(tasks, key=lambda t: t.category)

        elif sort_by == QueueSortOption.TARGET_USER:
            return sorted(tasks, key=lambda t: t.target_user)

        elif sort_by == QueueSortOption.REPORTER:
            return sorted(tasks, key=lambda t: t.reporter)

        return tasks

    def _flag_to_task(self, flag) -> ModerationTask:
        """Convert flag to moderation task"""

        # Calculate overdue hours
        response_target = flagging_system.response_time_targets.get(flag.priority, 72)
        time_since_creation = datetime.utcnow() - flag.created_at
        overdue_hours = max(
            0, (time_since_creation.total_seconds() / 3600) - response_target
        )

        return ModerationTask(
            flag_id=flag.id,
            priority=flag.priority.value,
            category=flag.category.value,
            created_at=flag.created_at,
            overdue_hours=overdue_hours,
            assigned_moderator=flag.assigned_moderator_id,
            target_user=flag.target_user_id,
            reporter=flag.reporter_id,
            content_type=flag.content_type,
            description=flag.description,
            evidence_count=len(flag.evidence),
            response_target_hours=response_target,
            is_escalated=flag.status.value == "escalated",
        )

    def _is_flag_overdue(self, flag) -> bool:
        """Check if flag is overdue for response"""

        response_target = flagging_system.response_time_targets.get(flag.priority, 72)
        time_since_creation = datetime.utcnow() - flag.created_at
        return time_since_creation.total_seconds() > (response_target * 3600)

    def get_queue_statistics(self) -> Dict:
        """Get moderation queue statistics"""

        from services.planarx.planarx_community.mod.flagging import flagging_system

        flags = list(flagging_system.flags.values())

        # Status counts
        status_counts = Counter(f.status.value for f in flags)

        # Priority counts
        priority_counts = Counter(f.priority.value for f in flags)

        # Category counts
        category_counts = Counter(f.category.value for f in flags)

        # Overdue counts
        overdue_count = len([f for f in flags if self._is_flag_overdue(f)])

        # Average response time
        resolved_flags = [f for f in flags if f.response_time_hours]
        avg_response_time = (
            sum(f.response_time_hours for f in resolved_flags) / len(resolved_flags)
            if resolved_flags
            else 0
        )

        return {
            "total_flags": len(flags),
            "status_counts": dict(status_counts),
            "priority_counts": dict(priority_counts),
            "category_counts": dict(category_counts),
            "overdue_count": overdue_count,
            "average_response_time_hours": round(avg_response_time, 2),
            "unassigned_count": len([f for f in flags if not f.assigned_moderator_id]),
        }

    def get_moderator_workload(self, moderator_id: str) -> ModeratorWorkload:
        """Get moderator workload statistics"""

        from services.planarx.planarx_community.mod.flagging import flagging_system

        assigned_flags = [
            f
            for f in flagging_system.flags.values()
            if f.assigned_moderator_id == moderator_id
        ]

        pending_review = len(
            [f for f in assigned_flags if f.status.value in ["pending", "under_review"]]
        )

        overdue_count = len([f for f in assigned_flags if self._is_flag_overdue(f)])

        # Calculate average response time
        resolved_flags = [f for f in assigned_flags if f.response_time_hours]
        avg_response_time = (
            sum(f.response_time_hours for f in resolved_flags) / len(resolved_flags)
            if resolved_flags
            else 0
        )

        # Get categories handled
        categories_handled = list(set(f.category.value for f in assigned_flags))

        # Get last activity
        last_activity = max(
            (f.updated_at for f in assigned_flags), default=datetime.utcnow()
        )

        workload = ModeratorWorkload(
            moderator_id=moderator_id,
            total_assigned=len(assigned_flags),
            pending_review=pending_review,
            overdue_count=overdue_count,
            avg_response_time=round(avg_response_time, 2),
            categories_handled=categories_handled,
            last_activity=last_activity,
        )

        self.moderator_workloads[moderator_id] = workload
        return workload

    def get_all_moderator_workloads(self) -> List[ModeratorWorkload]:
        """Get workload statistics for all moderators"""

        from services.planarx.planarx_community.mod.flagging import flagging_system

        moderator_ids = set()
        for flag in flagging_system.flags.values():
            if flag.assigned_moderator_id:
                moderator_ids.add(flag.assigned_moderator_id)

        workloads = []
        for moderator_id in moderator_ids:
            workloads.append(self.get_moderator_workload(moderator_id))

        return workloads

    def auto_assign_flags(self, available_moderators: List[str]):
        """Automatically assign unassigned flags to available moderators"""

        if not self.auto_assign_enabled:
            return

        from services.planarx.planarx_community.mod.flagging import flagging_system

        unassigned_flags = [
            f
            for f in flagging_system.flags.values()
            if not f.assigned_moderator_id and f.status.value == "pending"
        ]

        if not unassigned_flags or not available_moderators:
            return

        # Sort flags by priority
        priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        unassigned_flags.sort(key=lambda f: priority_order.get(f.priority.value, 4))

        # Get moderator workloads
        moderator_loads = {}
        for moderator_id in available_moderators:
            workload = self.get_moderator_workload(moderator_id)
            moderator_loads[moderator_id] = workload.total_assigned

        # Assign flags to least loaded moderators
        for flag in unassigned_flags:
            if not available_moderators:
                break

            # Find moderator with lowest load
            least_loaded_moderator = min(
                available_moderators, key=lambda m: moderator_loads.get(m, 0)
            )

            # Assign flag
            flag.assigned_moderator_id = least_loaded_moderator
            flag.status.value = "under_review"
            flag.updated_at = datetime.utcnow()

            # Update load count
            moderator_loads[least_loaded_moderator] = (
                moderator_loads.get(least_loaded_moderator, 0) + 1
            )

            self.logger.info(
                f"Auto-assigned flag {flag.id} to moderator {least_loaded_moderator}"
            )

    def check_and_create_alerts(self):
        """Check for conditions that require alerts and create them"""

        from services.planarx.planarx_community.mod.flagging import flagging_system

        # Check for overdue flags
        if self.alert_configs["overdue"]["enabled"]:
            self._check_overdue_alerts()

        # Check for critical flags
        if self.alert_configs["critical"]["enabled"]:
            self._check_critical_alerts()

        # Check for escalation needs
        if self.alert_configs["escalation"]["enabled"]:
            self._check_escalation_alerts()

        # Check for workload issues
        if self.alert_configs["workload"]["enabled"]:
            self._check_workload_alerts()

    def _check_overdue_alerts(self):
        """Check for overdue flags and create alerts"""

        from services.planarx.planarx_community.mod.flagging import flagging_system

        threshold_hours = self.alert_configs["overdue"]["threshold_hours"]
        overdue_flags = [
            f
            for f in flagging_system.flags.values()
            if self._is_flag_overdue(f)
            and f.status.value in ["pending", "under_review"]
        ]

        for flag in overdue_flags:
            alert_id = f"overdue_{flag.id}"
            if alert_id not in self.queue_alerts:
                alert = QueueAlert(
                    id=alert_id,
                    alert_type="overdue",
                    flag_id=flag.id,
                    message=f"Flag {flag.id} is overdue for response ({threshold_hours}h threshold)",
                    created_at=datetime.utcnow(),
                    acknowledged=False,
                    acknowledged_by=None,
                    acknowledged_at=None,
                )
                self.queue_alerts[alert_id] = alert

    def _check_critical_alerts(self):
        """Check for critical flags and create alerts"""

        from services.planarx.planarx_community.mod.flagging import flagging_system

        threshold_hours = self.alert_configs["critical"]["threshold_hours"]
        critical_flags = [
            f
            for f in flagging_system.flags.values()
            if f.priority.value == "critical"
            and f.status.value in ["pending", "under_review"]
        ]

        for flag in critical_flags:
            time_since_creation = datetime.utcnow() - flag.created_at
            if time_since_creation.total_seconds() > (threshold_hours * 3600):
                alert_id = f"critical_{flag.id}"
                if alert_id not in self.queue_alerts:
                    alert = QueueAlert(
                        id=alert_id,
                        alert_type="critical",
                        flag_id=flag.id,
                        message=f"Critical flag {flag.id} requires immediate attention",
                        created_at=datetime.utcnow(),
                        acknowledged=False,
                        acknowledged_by=None,
                        acknowledged_at=None,
                    )
                    self.queue_alerts[alert_id] = alert

    def _check_escalation_alerts(self):
        """Check for flags that need escalation"""

        from services.planarx.planarx_community.mod.flagging import flagging_system

        threshold_hours = self.alert_configs["escalation"]["threshold_hours"]
        escalation_candidates = [
            f
            for f in flagging_system.flags.values()
            if f.status.value in ["pending", "under_review"]
        ]

        for flag in escalation_candidates:
            time_since_creation = datetime.utcnow() - flag.created_at
            if time_since_creation.total_seconds() > (threshold_hours * 3600):
                alert_id = f"escalation_{flag.id}"
                if alert_id not in self.queue_alerts:
                    alert = QueueAlert(
                        id=alert_id,
                        alert_type="escalation",
                        flag_id=flag.id,
                        message=f"Flag {flag.id} should be escalated to senior moderator",
                        created_at=datetime.utcnow(),
                        acknowledged=False,
                        acknowledged_by=None,
                        acknowledged_at=None,
                    )
                    self.queue_alerts[alert_id] = alert

    def _check_workload_alerts(self):
        """Check for moderator workload issues"""

        max_assigned = self.alert_configs["workload"]["max_assigned"]

        for moderator_id, workload in self.moderator_workloads.items():
            if workload.total_assigned > max_assigned:
                alert_id = f"workload_{moderator_id}"
                if alert_id not in self.queue_alerts:
                    alert = QueueAlert(
                        id=alert_id,
                        alert_type="workload",
                        flag_id="",  # Not specific to one flag
                        message=f"Moderator {moderator_id} has high workload ({workload.total_assigned} assigned)",
                        created_at=datetime.utcnow(),
                        acknowledged=False,
                        acknowledged_by=None,
                        acknowledged_at=None,
                    )
                    self.queue_alerts[alert_id] = alert

    def get_active_alerts(self, alert_type: str = None) -> List[QueueAlert]:
        """Get active (unacknowledged) alerts"""

        alerts = [
            alert for alert in self.queue_alerts.values() if not alert.acknowledged
        ]

        if alert_type:
            alerts = [alert for alert in alerts if alert.alert_type == alert_type]

        return sorted(alerts, key=lambda a: a.created_at, reverse=True)

    def acknowledge_alert(self, alert_id: str, moderator_id: str):
        """Acknowledge an alert"""

        if alert_id in self.queue_alerts:
            alert = self.queue_alerts[alert_id]
            alert.acknowledged = True
            alert.acknowledged_by = moderator_id
            alert.acknowledged_at = datetime.utcnow()

            self.logger.info(f"Alert {alert_id} acknowledged by {moderator_id}")

    def get_queue_dashboard_data(self) -> Dict:
        """Get comprehensive dashboard data for moderation queue"""

        from services.planarx.planarx_community.mod.flagging import flagging_system

        # Get queue statistics
        queue_stats = self.get_queue_statistics()

        # Get moderator workloads
        moderator_workloads = self.get_all_moderator_workloads()

        # Get active alerts
        active_alerts = self.get_active_alerts()

        # Get recent flags
        recent_flags = sorted(
            flagging_system.flags.values(), key=lambda f: f.created_at, reverse=True
        )[:10]

        # Get overdue flags
        overdue_flags = [
            f for f in flagging_system.flags.values() if self._is_flag_overdue(f)
        ]

        return {
            "queue_statistics": queue_stats,
            "moderator_workloads": [asdict(w) for w in moderator_workloads],
            "active_alerts": [asdict(a) for a in active_alerts],
            "recent_flags": [
                {
                    "id": f.id,
                    "category": f.category.value,
                    "priority": f.priority.value,
                    "status": f.status.value,
                    "created_at": f.created_at.isoformat(),
                    "target_user": f.target_user_id,
                    "assigned_moderator": f.assigned_moderator_id,
                }
                for f in recent_flags
            ],
            "overdue_flags_count": len(overdue_flags),
            "unassigned_flags_count": len(
                [
                    f
                    for f in flagging_system.flags.values()
                    if not f.assigned_moderator_id
                ]
            ),
        }


# Global moderation queue instance
moderation_queue = ModerationQueue()
