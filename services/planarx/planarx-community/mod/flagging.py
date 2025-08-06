"""
Enhanced Flagging System
Category-based flagging with violation tracking and response time management
"""

import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, asdict
from enum import Enum
import logging
import json

logger = logging.getLogger(__name__)


class FlagCategory(Enum):
    """Flag categories for different types of violations"""

    SAFETY_VIOLATION = "safety_violation"
    HARASSMENT_ABUSE = "harassment_abuse"
    SPAM_MISINFORMATION = "spam_misinformation"
    PROFESSIONAL_MISCONDUCT = "professional_misconduct"
    MINOR_VIOLATION = "minor_violation"
    COPYRIGHT_VIOLATION = "copyright_violation"
    IMPERSONATION = "impersonation"
    INAPPROPRIATE_CONTENT = "inappropriate_content"
    OFF_TOPIC = "off_topic"
    DUPLICATE_CONTENT = "duplicate_content"


class FlagStatus(Enum):
    """Flag status"""

    PENDING = "pending"
    UNDER_REVIEW = "under_review"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"
    ESCALATED = "escalated"


class FlagPriority(Enum):
    """Flag priority levels"""

    CRITICAL = "critical"  # Safety violations
    HIGH = "high"  # Harassment, abuse
    MEDIUM = "medium"  # Spam, misconduct
    LOW = "low"  # Minor violations


@dataclass
class Flag:
    """Flag record"""

    id: str
    reporter_id: str
    target_user_id: str
    content_id: str  # ID of flagged content (draft, comment, etc.)
    content_type: str  # Type of content (draft, comment, collaboration, etc.)
    category: FlagCategory
    priority: FlagPriority
    status: FlagStatus
    description: str
    evidence: List[str]  # URLs, screenshots, etc.
    created_at: datetime
    updated_at: datetime
    assigned_moderator_id: Optional[str]
    reviewed_at: Optional[datetime]
    resolution: Optional[str]
    response_time_hours: Optional[float]
    metadata: Dict

    def __post_init__(self):
        if self.evidence is None:
            self.evidence = []
        if self.metadata is None:
            self.metadata = {}


@dataclass
class FlagResponse:
    """Moderator response to flag"""

    id: str
    flag_id: str
    moderator_id: str
    action_taken: str
    reasoning: str
    user_notified: bool
    created_at: datetime
    metadata: Dict

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class UserViolationHistory:
    """User's violation history"""

    user_id: str
    total_flags: int
    resolved_flags: int
    dismissed_flags: int
    escalated_flags: int
    violation_categories: Dict[str, int]
    last_violation: Optional[datetime]
    current_restrictions: List[str]
    warning_count: int
    ban_status: Optional[str]

    def __post_init__(self):
        if self.violation_categories is None:
            self.violation_categories = {}
        if self.current_restrictions is None:
            self.current_restrictions = []
        if self.ban_status is None:
            self.ban_status = None


class FlaggingSystem:
    """Enhanced flagging system with category management"""

    def __init__(self):
        self.flags: Dict[str, Flag] = {}
        self.flag_responses: Dict[str, List[FlagResponse]] = {}
        self.user_violations: Dict[str, UserViolationHistory] = {}
        self.category_configs: Dict[FlagCategory, Dict] = {}
        self.response_time_targets: Dict[FlagPriority, int] = {}

        self.logger = logging.getLogger(__name__)

        self._initialize_category_configs()
        self._initialize_response_targets()

    def _initialize_category_configs(self):
        """Initialize flag category configurations"""

        self.category_configs = {
            FlagCategory.SAFETY_VIOLATION: {
                "priority": FlagPriority.CRITICAL,
                "response_target_hours": 24,
                "auto_escalation_hours": 48,
                "restrictions": ["cannot_submit_drafts", "cannot_comment"],
                "requires_expert_review": True,
                "notification_required": True,
            },
            FlagCategory.HARASSMENT_ABUSE: {
                "priority": FlagPriority.HIGH,
                "response_target_hours": 48,
                "auto_escalation_hours": 72,
                "restrictions": ["cannot_comment", "limited_profile"],
                "requires_expert_review": True,
                "notification_required": True,
            },
            FlagCategory.SPAM_MISINFORMATION: {
                "priority": FlagPriority.MEDIUM,
                "response_target_hours": 72,
                "auto_escalation_hours": 120,
                "restrictions": ["cannot_submit_drafts"],
                "requires_expert_review": False,
                "notification_required": False,
            },
            FlagCategory.PROFESSIONAL_MISCONDUCT: {
                "priority": FlagPriority.MEDIUM,
                "response_target_hours": 72,
                "auto_escalation_hours": 120,
                "restrictions": ["cannot_fund_projects"],
                "requires_expert_review": True,
                "notification_required": True,
            },
            FlagCategory.MINOR_VIOLATION: {
                "priority": FlagPriority.LOW,
                "response_target_hours": 168,  # 7 days
                "auto_escalation_hours": 336,  # 14 days
                "restrictions": [],
                "requires_expert_review": False,
                "notification_required": False,
            },
            FlagCategory.COPYRIGHT_VIOLATION: {
                "priority": FlagPriority.HIGH,
                "response_target_hours": 48,
                "auto_escalation_hours": 72,
                "restrictions": ["cannot_submit_drafts"],
                "requires_expert_review": True,
                "notification_required": True,
            },
            FlagCategory.IMPERSONATION: {
                "priority": FlagPriority.HIGH,
                "response_target_hours": 48,
                "auto_escalation_hours": 72,
                "restrictions": ["cannot_comment", "cannot_submit_drafts"],
                "requires_expert_review": True,
                "notification_required": True,
            },
            FlagCategory.INAPPROPRIATE_CONTENT: {
                "priority": FlagPriority.MEDIUM,
                "response_target_hours": 72,
                "auto_escalation_hours": 120,
                "restrictions": ["cannot_submit_drafts"],
                "requires_expert_review": False,
                "notification_required": False,
            },
            FlagCategory.OFF_TOPIC: {
                "priority": FlagPriority.LOW,
                "response_target_hours": 168,
                "auto_escalation_hours": 336,
                "restrictions": [],
                "requires_expert_review": False,
                "notification_required": False,
            },
            FlagCategory.DUPLICATE_CONTENT: {
                "priority": FlagPriority.LOW,
                "response_target_hours": 168,
                "auto_escalation_hours": 336,
                "restrictions": [],
                "requires_expert_review": False,
                "notification_required": False,
            },
        }

    def _initialize_response_targets(self):
        """Initialize response time targets by priority"""

        self.response_time_targets = {
            FlagPriority.CRITICAL: 24,  # 24 hours
            FlagPriority.HIGH: 48,  # 48 hours
            FlagPriority.MEDIUM: 72,  # 72 hours
            FlagPriority.LOW: 168,  # 7 days
        }

    def create_flag(
        self,
        reporter_id: str,
        target_user_id: str,
        content_id: str,
        content_type: str,
        category: FlagCategory,
        description: str,
        evidence: List[str] = None,
        metadata: Dict = None,
    ) -> Flag:
        """Create a new flag"""

        # Get category configuration
        category_config = self.category_configs.get(category)
        if not category_config:
            raise ValueError(f"Unknown flag category: {category}")

        # Create flag
        flag = Flag(
            id=str(uuid.uuid4()),
            reporter_id=reporter_id,
            target_user_id=target_user_id,
            content_id=content_id,
            content_type=content_type,
            category=category,
            priority=category_config["priority"],
            status=FlagStatus.PENDING,
            description=description,
            evidence=evidence or [],
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            assigned_moderator_id=None,
            reviewed_at=None,
            resolution=None,
            response_time_hours=None,
            metadata=metadata or {},
        )

        # Store flag
        self.flags[flag.id] = flag

        # Update user violation history
        self._update_user_violations(target_user_id, flag)

        # Check for auto-escalation
        self._check_auto_escalation(flag)

        self.logger.info(
            f"Created flag {flag.id} for user {target_user_id}, category {category.value}"
        )
        return flag

    def _update_user_violations(self, user_id: str, flag: Flag):
        """Update user's violation history"""

        if user_id not in self.user_violations:
            self.user_violations[user_id] = UserViolationHistory(
                user_id=user_id,
                total_flags=0,
                resolved_flags=0,
                dismissed_flags=0,
                escalated_flags=0,
                violation_categories={},
                last_violation=None,
                current_restrictions=[],
                warning_count=0,
                ban_status=None,
            )

        violations = self.user_violations[user_id]
        violations.total_flags += 1
        violations.last_violation = datetime.utcnow()

        # Update category counts
        category_name = flag.category.value
        violations.violation_categories[category_name] = (
            violations.violation_categories.get(category_name, 0) + 1
        )

    def _check_auto_escalation(self, flag: Flag):
        """Check if flag should be auto-escalated based on response time"""

        category_config = self.category_configs.get(flag.category)
        if not category_config:
            return

        auto_escalation_hours = category_config.get("auto_escalation_hours", 72)
        time_since_creation = datetime.utcnow() - flag.created_at

        if time_since_creation.total_seconds() > (auto_escalation_hours * 3600):
            flag.status = FlagStatus.ESCALATED
            flag.updated_at = datetime.utcnow()

            self.logger.warning(
                f"Auto-escalated flag {flag.id} after {auto_escalation_hours} hours"
            )

    def assign_moderator(self, flag_id: str, moderator_id: str) -> Flag:
        """Assign a moderator to review a flag"""

        flag = self.flags.get(flag_id)
        if not flag:
            raise ValueError(f"Flag {flag_id} not found")

        flag.assigned_moderator_id = moderator_id
        flag.status = FlagStatus.UNDER_REVIEW
        flag.updated_at = datetime.utcnow()

        self.logger.info(f"Assigned moderator {moderator_id} to flag {flag_id}")
        return flag

    def resolve_flag(
        self,
        flag_id: str,
        moderator_id: str,
        action_taken: str,
        reasoning: str,
        user_notified: bool = True,
    ) -> FlagResponse:
        """Resolve a flag with moderator response"""

        flag = self.flags.get(flag_id)
        if not flag:
            raise ValueError(f"Flag {flag_id} not found")

        # Calculate response time
        response_time = datetime.utcnow() - flag.created_at
        flag.response_time_hours = response_time.total_seconds() / 3600

        # Update flag status
        flag.status = FlagStatus.RESOLVED
        flag.reviewed_at = datetime.utcnow()
        flag.updated_at = datetime.utcnow()
        flag.resolution = action_taken

        # Create response record
        response = FlagResponse(
            id=str(uuid.uuid4()),
            flag_id=flag_id,
            moderator_id=moderator_id,
            action_taken=action_taken,
            reasoning=reasoning,
            user_notified=user_notified,
            created_at=datetime.utcnow(),
            metadata={},
        )

        # Store response
        if flag_id not in self.flag_responses:
            self.flag_responses[flag_id] = []
        self.flag_responses[flag_id].append(response)

        # Update user violations
        violations = self.user_violations.get(flag.target_user_id)
        if violations:
            violations.resolved_flags += 1

        self.logger.info(f"Resolved flag {flag_id} with action: {action_taken}")
        return response

    def dismiss_flag(
        self,
        flag_id: str,
        moderator_id: str,
        reasoning: str,
        user_notified: bool = False,
    ) -> FlagResponse:
        """Dismiss a flag as invalid"""

        flag = self.flags.get(flag_id)
        if not flag:
            raise ValueError(f"Flag {flag_id} not found")

        # Calculate response time
        response_time = datetime.utcnow() - flag.created_at
        flag.response_time_hours = response_time.total_seconds() / 3600

        # Update flag status
        flag.status = FlagStatus.DISMISSED
        flag.reviewed_at = datetime.utcnow()
        flag.updated_at = datetime.utcnow()
        flag.resolution = "dismissed"

        # Create response record
        response = FlagResponse(
            id=str(uuid.uuid4()),
            flag_id=flag_id,
            moderator_id=moderator_id,
            action_taken="dismissed",
            reasoning=reasoning,
            user_notified=user_notified,
            created_at=datetime.utcnow(),
            metadata={},
        )

        # Store response
        if flag_id not in self.flag_responses:
            self.flag_responses[flag_id] = []
        self.flag_responses[flag_id].append(response)

        # Update user violations
        violations = self.user_violations.get(flag.target_user_id)
        if violations:
            violations.dismissed_flags += 1

        self.logger.info(f"Dismissed flag {flag_id}")
        return response

    def escalate_flag(
        self, flag_id: str, moderator_id: str, reason: str
    ) -> FlagResponse:
        """Escalate a flag to senior moderator"""

        flag = self.flags.get(flag_id)
        if not flag:
            raise ValueError(f"Flag {flag_id} not found")

        # Update flag status
        flag.status = FlagStatus.ESCALATED
        flag.updated_at = datetime.utcnow()

        # Create response record
        response = FlagResponse(
            id=str(uuid.uuid4()),
            flag_id=flag_id,
            moderator_id=moderator_id,
            action_taken="escalated",
            reasoning=reason,
            user_notified=False,
            created_at=datetime.utcnow(),
            metadata={},
        )

        # Store response
        if flag_id not in self.flag_responses:
            self.flag_responses[flag_id] = []
        self.flag_responses[flag_id].append(response)

        # Update user violations
        violations = self.user_violations.get(flag.target_user_id)
        if violations:
            violations.escalated_flags += 1

        self.logger.info(f"Escalated flag {flag_id}")
        return response

    def get_moderation_queue(
        self,
        priority: FlagPriority = None,
        category: FlagCategory = None,
        status: FlagStatus = None,
        limit: int = 50,
    ) -> List[Flag]:
        """Get moderation queue with filtering options"""

        flags = list(self.flags.values())

        # Apply filters
        if priority:
            flags = [f for f in flags if f.priority == priority]
        if category:
            flags = [f for f in flags if f.category == category]
        if status:
            flags = [f for f in flags if f.status == status]

        # Sort by priority and creation time
        priority_order = {
            FlagPriority.CRITICAL: 0,
            FlagPriority.HIGH: 1,
            FlagPriority.MEDIUM: 2,
            FlagPriority.LOW: 3,
        }

        flags.sort(key=lambda f: (priority_order[f.priority], f.created_at))

        return flags[:limit]

    def get_overdue_flags(self, hours_threshold: int = 24) -> List[Flag]:
        """Get flags that are overdue for response"""

        overdue_flags = []
        threshold_time = datetime.utcnow() - timedelta(hours=hours_threshold)

        for flag in self.flags.values():
            if (
                flag.status in [FlagStatus.PENDING, FlagStatus.UNDER_REVIEW]
                and flag.created_at < threshold_time
            ):
                overdue_flags.append(flag)

        return overdue_flags

    def get_user_violation_history(
        self, user_id: str
    ) -> Optional[UserViolationHistory]:
        """Get user's violation history"""

        return self.user_violations.get(user_id)

    def get_flag_responses(self, flag_id: str) -> List[FlagResponse]:
        """Get all responses for a flag"""

        return self.flag_responses.get(flag_id, [])

    def get_flag_statistics(self) -> Dict:
        """Get flagging system statistics"""

        total_flags = len(self.flags)
        flags_by_status = {}
        flags_by_category = {}
        flags_by_priority = {}

        for flag in self.flags.values():
            # Status counts
            status = flag.status.value
            flags_by_status[status] = flags_by_status.get(status, 0) + 1

            # Category counts
            category = flag.category.value
            flags_by_category[category] = flags_by_category.get(category, 0) + 1

            # Priority counts
            priority = flag.priority.value
            flags_by_priority[priority] = flags_by_priority.get(priority, 0) + 1

        # Calculate average response times
        resolved_flags = [f for f in self.flags.values() if f.response_time_hours]
        avg_response_time = (
            sum(f.response_time_hours for f in resolved_flags) / len(resolved_flags)
            if resolved_flags
            else 0
        )

        return {
            "total_flags": total_flags,
            "flags_by_status": flags_by_status,
            "flags_by_category": flags_by_category,
            "flags_by_priority": flags_by_priority,
            "average_response_time_hours": round(avg_response_time, 2),
            "overdue_flags": len(self.get_overdue_flags()),
        }

    def get_category_config(self, category: FlagCategory) -> Dict:
        """Get configuration for a flag category"""

        return self.category_configs.get(category, {})

    def update_category_config(self, category: FlagCategory, new_config: Dict):
        """Update configuration for a flag category"""

        if category not in self.category_configs:
            raise ValueError(f"Unknown category: {category}")

        self.category_configs[category].update(new_config)
        self.logger.info(f"Updated configuration for category {category.value}")

    def cleanup_old_flags(self, days_old: int = 90):
        """Clean up old resolved/dismissed flags"""

        cutoff_date = datetime.utcnow() - timedelta(days=days_old)
        old_flags = []

        for flag_id, flag in self.flags.items():
            if (
                flag.status in [FlagStatus.RESOLVED, FlagStatus.DISMISSED]
                and flag.reviewed_at
                and flag.reviewed_at < cutoff_date
            ):
                old_flags.append(flag_id)

        for flag_id in old_flags:
            del self.flags[flag_id]
            if flag_id in self.flag_responses:
                del self.flag_responses[flag_id]

        if old_flags:
            self.logger.info(f"Cleaned up {len(old_flags)} old flags")


# Global flagging system instance
flagging_system = FlaggingSystem()
