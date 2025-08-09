"""
Planarx Community - Moderator Dashboard

Moderator tools and dashboard for managing the Planarx community including:
- User management and moderation
- Content review and approval
- Featured content selection
- Community engagement tools
- Notification management
- Onboarding flow management
"""

import uuid
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from enum import Enum
from dataclasses import dataclass, asdict
import logging

logger = logging.getLogger(__name__)


class ModAction(str, Enum):
    """Moderator action types."""
    WARN = "warn"
    SUSPEND = "suspend"
    BAN = "ban"
    RESTORE = "restore"
    FEATURE = "feature"
    UNFEATURE = "unfeature"
    APPROVE = "approve"
    REJECT = "reject"
    DELETE = "delete"


class UserStatus(str, Enum):
    """User status enumeration."""
    ACTIVE = "active"
    WARNED = "warned"
    SUSPENDED = "suspended"
    BANNED = "banned"
    PENDING = "pending"


class ContentStatus(str, Enum):
    """Content status enumeration."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    FEATURED = "featured"
    DELETED = "deleted"


@dataclass
class ModActionLog:
    """Log of moderator actions."""
    action_id: str
    moderator_id: str
    moderator_name: str
    action_type: ModAction
    target_type: str  # user, project, comment, etc.
    target_id: str
    reason: str
    duration: Optional[int] = None  # For suspensions/bans
    created_at: datetime = None
    metadata: Dict[str, Any] = None


@dataclass
class UserReport:
    """User-generated report."""
    report_id: str
    reporter_id: str
    reporter_name: str
    target_type: str
    target_id: str
    reason: str
    description: str
    status: str  # pending, reviewed, resolved, dismissed
    created_at: datetime
    reviewed_at: Optional[datetime] = None
    reviewed_by: Optional[str] = None


@dataclass
class FeaturedContent:
    """Featured content entry."""
    content_id: str
    content_type: str  # project, user, comment
    title: str
    description: str
    featured_by: str
    featured_at: datetime
    expires_at: Optional[datetime] = None
    priority: int = 1  # 1-10, higher is more prominent


@dataclass
class NotificationTemplate:
    """Notification template for automated messages."""
    template_id: str
    name: str
    subject: str
    body: str
    variables: List[str]  # List of variable names used in template
    created_at: datetime
    updated_at: datetime


class ModDashboardService:
    """Service for moderator dashboard functionality."""

    def __init__(self):
        """Initialize the moderator dashboard service."""
        self.mod_actions: List[ModActionLog] = []
        self.user_reports: List[UserReport] = []
        self.featured_content: List[FeaturedContent] = []
        self.notification_templates: List[NotificationTemplate] = []

    async def get_dashboard_overview(self) -> Dict[str, Any]:
        """Get overview statistics for moderator dashboard."""
        try:
            # Get various statistics
            stats = {
                "total_users": await self._get_total_users(),
                "pending_reports": await self._get_pending_reports_count(),
                "pending_reviews": await self._get_pending_reviews_count(),
                "featured_content": len(self.featured_content),
                "recent_actions": len([a for a in self.mod_actions if
                                     datetime.now() - a.created_at < timedelta(days=7)]),
                "user_growth": await self._get_user_growth_stats(),
                "content_metrics": await self._get_content_metrics(),
                "moderation_queue": await self._get_moderation_queue_stats()
            }

            return stats

        except Exception as e:
            logger.error(f"Error getting dashboard overview: {e}")
            return {}

    async def get_pending_reports(self, limit: int = 50) -> List[UserReport]:
        """Get pending user reports for review."""
        try:
            pending_reports = [
                report for report in self.user_reports
                if report.status == "pending"
            ]

            # Sort by creation date (oldest first)
            pending_reports.sort(key=lambda x: x.created_at)

            return pending_reports[:limit]

        except Exception as e:
            logger.error(f"Error getting pending reports: {e}")
            return []

    async def review_report(self, report_id: str, moderator_id: str,
                           action: str, reason: str) -> bool:
        """Review and take action on a user report."""
        try:
            report = next((r for r in self.user_reports if r.report_id == report_id), None)
            if not report:
                return False

            # Update report status
            report.status = "reviewed"
            report.reviewed_at = datetime.now()
            report.reviewed_by = moderator_id

            # Take action based on review
            if action in ["warn", "suspend", "ban"]:
                await self._take_mod_action(
                    moderator_id=moderator_id,
                    action_type=ModAction(action),
                    target_type=report.target_type,
                    target_id=report.target_id,
                    reason=reason
                )

            logger.info(f"Report {report_id} reviewed by moderator {moderator_id}")
            return True

        except Exception as e:
            logger.error(f"Error reviewing report {report_id}: {e}")
            return False

    async def take_mod_action(self, moderator_id: str, moderator_name: str,
                             action_type: ModAction, target_type: str, target_id: str,
                             reason: str, duration: Optional[int] = None) -> bool:
        """Take a moderator action on a user or content."""
        try:
            # Create action log
            action_log = ModActionLog(
                action_id=str(uuid.uuid4()),
                moderator_id=moderator_id,
                moderator_name=moderator_name,
                action_type=action_type,
                target_type=target_type,
                target_id=target_id,
                reason=reason,
                duration=duration,
                created_at=datetime.now(),
                metadata={}
            )

            self.mod_actions.append(action_log)

            # Apply the action
            await self._apply_mod_action(action_type, target_type, target_id, duration)

            # Send notification
            await self._send_mod_action_notification(action_log)

            logger.info(f"Mod action {action_type} taken on {target_type} {target_id}")
            return True

        except Exception as e:
            logger.error(f"Error taking mod action: {e}")
            return False

    async def feature_content(self, content_id: str, content_type: str,
                             title: str, description: str, featured_by: str,
                             priority: int = 1, duration_days: int = 7) -> bool:
        """Feature content on the platform."""
        try:
            # Check if content is already featured
            existing = next((fc for fc in self.featured_content
                           if fc.content_id == content_id), None)
            if existing:
                return False

            featured_content = FeaturedContent(
                content_id=content_id,
                content_type=content_type,
                title=title,
                description=description,
                featured_by=featured_by,
                featured_at=datetime.now(),
                expires_at=datetime.now() + timedelta(days=duration_days),
                priority=priority
            )

            self.featured_content.append(featured_content)

            logger.info(f"Content {content_id} featured by {featured_by}")
            return True

        except Exception as e:
            logger.error(f"Error featuring content {content_id}: {e}")
            return False

    async def unfeature_content(self, content_id: str, moderator_id: str) -> bool:
        """Remove content from featured list."""
        try:
            # Find and remove featured content
            self.featured_content = [
                fc for fc in self.featured_content
                if fc.content_id != content_id
            ]

            # Log the action
            await self.take_mod_action(
                moderator_id=moderator_id,
                moderator_name="Moderator",
                action_type=ModAction.UNFEATURE,
                target_type="content",
                target_id=content_id,
                reason="Removed from featured content"
            )

            logger.info(f"Content {content_id} unfeatured by {moderator_id}")
            return True

        except Exception as e:
            logger.error(f"Error unfeaturing content {content_id}: {e}")
            return False

    async def get_featured_content(self) -> List[FeaturedContent]:
        """Get currently featured content."""
        try:
            # Filter out expired content
            current_time = datetime.now()
            active_content = [
                fc for fc in self.featured_content
                if not fc.expires_at or fc.expires_at > current_time
            ]

            # Sort by priority (highest first)
            active_content.sort(key=lambda x: x.priority, reverse=True)

            return active_content

        except Exception as e:
            logger.error(f"Error getting featured content: {e}")
            return []

    async def send_notification(self, template_name: str, user_ids: List[str],
                               variables: Dict[str, Any] = None) -> bool:
        """Send notification to users using a template."""
        try:
            template = next((t for t in self.notification_templates
                           if t.name == template_name), None)
            if not template:
                return False

            # Replace variables in template
            subject = template.subject
            body = template.body

            if variables:
                for var_name, var_value in variables.items():
                    subject = subject.replace(f"{{{var_name}}}", str(var_value))
                    body = body.replace(f"{{{var_name}}}", str(var_value))

            # Send notifications (in real implementation, this would use a notification service)
            for user_id in user_ids:
                await self._send_notification_to_user(user_id, subject, body)

            logger.info(f"Sent {template_name} notification to {len(user_ids)} users")
            return True

        except Exception as e:
            logger.error(f"Error sending notification: {e}")
            return False

    async def create_notification_template(self, name: str, subject: str, body: str,
                                         variables: List[str] = None) -> bool:
        """Create a new notification template."""
        try:
            template = NotificationTemplate(
                template_id=str(uuid.uuid4()),
                name=name,
                subject=subject,
                body=body,
                variables=variables or [],
                created_at=datetime.now(),
                updated_at=datetime.now()
            )

            self.notification_templates.append(template)

            logger.info(f"Created notification template: {name}")
            return True

        except Exception as e:
            logger.error(f"Error creating notification template: {e}")
            return False

    async def get_mod_action_logs(self, moderator_id: Optional[str] = None,
                                 action_type: Optional[ModAction] = None,
                                 limit: int = 100) -> List[ModActionLog]:
        """Get moderator action logs with optional filtering."""
        try:
            logs = self.mod_actions.copy()

            # Apply filters
            if moderator_id:
                logs = [log for log in logs if log.moderator_id == moderator_id]
            if action_type:
                logs = [log for log in logs if log.action_type == action_type]

            # Sort by creation date (newest first)
            logs.sort(key=lambda x: x.created_at, reverse=True)

            return logs[:limit]

        except Exception as e:
            logger.error(f"Error getting mod action logs: {e}")
            return []

    async def get_user_statistics(self) -> Dict[str, Any]:
        """Get user statistics for moderation."""
        try:
            stats = {
                "total_users": await self._get_total_users(),
                "active_users": await self._get_active_users_count(),
                "suspended_users": await self._get_suspended_users_count(),
                "banned_users": await self._get_banned_users_count(),
                "new_users_today": await self._get_new_users_count(days=1),
                "new_users_week": await self._get_new_users_count(days=7),
                "user_growth_rate": await self._calculate_user_growth_rate(),
                "top_contributors": await self._get_top_contributors(),
                "problem_users": await self._get_problem_users()
            }

            return stats

        except Exception as e:
            logger.error(f"Error getting user statistics: {e}")
            return {}

    async def get_content_statistics(self) -> Dict[str, Any]:
        """Get content statistics for moderation."""
        try:
            stats = {
                "total_projects": await self._get_total_projects(),
                "pending_reviews": await self._get_pending_reviews_count(),
                "approved_projects": await self._get_approved_projects_count(),
                "rejected_projects": await self._get_rejected_projects_count(),
                "featured_content": len(self.featured_content),
                "reported_content": await self._get_reported_content_count(),
                "content_growth_rate": await self._calculate_content_growth_rate(),
                "top_categories": await self._get_top_categories(),
                "content_quality_metrics": await self._get_content_quality_metrics()
            }

            return stats

        except Exception as e:
            logger.error(f"Error getting content statistics: {e}")
            return {}

    async def manage_onboarding_flow(self, user_id: str, step: str,
                                    completed: bool = True) -> bool:
        """Manage user onboarding flow."""
        try:
            # Update user onboarding progress
            await self._update_onboarding_progress(user_id, step, completed)

            # Send appropriate notifications based on step
            if completed:
                await self._send_onboarding_notification(user_id, step)

            logger.info(f"Updated onboarding progress for user {user_id}: {step}")
            return True

        except Exception as e:
            logger.error(f"Error managing onboarding flow: {e}")
            return False

    async def get_onboarding_statistics(self) -> Dict[str, Any]:
        """Get onboarding flow statistics."""
        try:
            stats = {
                "total_new_users": await self._get_new_users_count(days=30),
                "onboarding_completion_rate": await self._get_onboarding_completion_rate(),
                "step_completion_rates": await self._get_step_completion_rates(),
                "dropoff_points": await self._get_onboarding_dropoff_points(),
                "average_completion_time": await self._get_average_completion_time()
            }

            return stats

        except Exception as e:
            logger.error(f"Error getting onboarding statistics: {e}")
            return {}

    # Helper methods

    async def _get_total_users(self) -> int:
        """Get total number of users."""
        # In real implementation, this would query the database
        return 1250

    async def _get_active_users_count(self) -> int:
        """Get count of active users."""
        return 980

    async def _get_suspended_users_count(self) -> int:
        """Get count of suspended users."""
        return 15

    async def _get_banned_users_count(self) -> int:
        """Get count of banned users."""
        return 8

    async def _get_new_users_count(self, days: int) -> int:
        """Get count of new users in the last N days."""
        return 45 if days == 1 else 320

    async def _get_pending_reports_count(self) -> int:
        """Get count of pending reports."""
        return len([r for r in self.user_reports if r.status == "pending"])

    async def _get_pending_reviews_count(self) -> int:
        """Get count of pending content reviews."""
        return 23

    async def _get_total_projects(self) -> int:
        """Get total number of projects."""
        return 456

    async def _get_approved_projects_count(self) -> int:
        """Get count of approved projects."""
        return 398

    async def _get_rejected_projects_count(self) -> int:
        """Get count of rejected projects."""
        return 35

    async def _get_reported_content_count(self) -> int:
        """Get count of reported content."""
        return len(self.user_reports)

    async def _get_user_growth_stats(self) -> Dict[str, Any]:
        """Get user growth statistics."""
        return {
            "daily_growth": 12,
            "weekly_growth": 85,
            "monthly_growth": 320,
            "retention_rate": 0.78
        }

    async def _get_content_metrics(self) -> Dict[str, Any]:
        """Get content metrics."""
        return {
            "projects_created_today": 8,
            "projects_approved_today": 6,
            "projects_rejected_today": 2,
            "average_review_time": "2.5 hours"
        }

    async def _get_moderation_queue_stats(self) -> Dict[str, Any]:
        """Get moderation queue statistics."""
        return {
            "pending_reports": await self._get_pending_reports_count(),
            "pending_reviews": await self._get_pending_reviews_count(),
            "suspended_users": await self._get_suspended_users_count(),
            "banned_users": await self._get_banned_users_count()
        }

    async def _apply_mod_action(self, action_type: ModAction, target_type: str,
                               target_id: str, duration: Optional[int] = None) -> bool:
        """Apply a moderator action to the target."""
        try:
            if target_type == "user":
                if action_type == ModAction.SUSPEND:
                    await self._suspend_user(target_id, duration)
                elif action_type == ModAction.BAN:
                    await self._ban_user(target_id)
                elif action_type == ModAction.WARN:
                    await self._warn_user(target_id)
                elif action_type == ModAction.RESTORE:
                    await self._restore_user(target_id)
            elif target_type == "content":
                if action_type == ModAction.DELETE:
                    await self._delete_content(target_id)
                elif action_type == ModAction.APPROVE:
                    await self._approve_content(target_id)
                elif action_type == ModAction.REJECT:
                    await self._reject_content(target_id)

            return True

        except Exception as e:
            logger.error(f"Error applying mod action: {e}")
            return False

    async def _send_mod_action_notification(self, action_log: ModActionLog) -> bool:
        """Send notification about moderator action."""
        try:
            # In real implementation, this would send notifications
            logger.info(f"Sent notification about mod action {action_log.action_type}")
            return True
        except Exception as e:
            logger.error(f"Error sending mod action notification: {e}")
            return False

    async def _send_notification_to_user(self, user_id: str, subject: str, body: str) -> bool:
        """Send notification to a specific user."""
        try:
            # In real implementation, this would send via email, push notification, etc.
            logger.info(f"Sent notification to user {user_id}: {subject}")
            return True
        except Exception as e:
            logger.error(f"Error sending notification to user {user_id}: {e}")
            return False

    async def _suspend_user(self, user_id: str, duration: int) -> bool:
        """Suspend a user for a specified duration."""
        # Implementation would update user status in database
        return True

    async def _ban_user(self, user_id: str) -> bool:
        """Ban a user permanently."""
        # Implementation would update user status in database
        return True

    async def _warn_user(self, user_id: str) -> bool:
        """Warn a user."""
        # Implementation would send warning notification
        return True

    async def _restore_user(self, user_id: str) -> bool:
        """Restore a suspended/banned user."""
        # Implementation would restore user status
        return True

    async def _delete_content(self, content_id: str) -> bool:
        """Delete content."""
        # Implementation would mark content as deleted
        return True

    async def _approve_content(self, content_id: str) -> bool:
        """Approve content."""
        # Implementation would mark content as approved
        return True

    async def _reject_content(self, content_id: str) -> bool:
        """Reject content."""
        # Implementation would mark content as rejected
        return True

    async def _calculate_user_growth_rate(self) -> float:
        """Calculate user growth rate."""
        return 0.15  # 15% growth

    async def _calculate_content_growth_rate(self) -> float:
        """Calculate content growth rate."""
        return 0.25  # 25% growth

    async def _get_top_contributors(self) -> List[Dict[str, Any]]:
        """Get top contributors."""
        return [
            {"user_id": "user1", "username": "DesignMaster", "contributions": 45},
            {"user_id": "user2", "username": "ArchitectPro", "contributions": 38},
            {"user_id": "user3", "username": "BuildInnovator", "contributions": 32}
        ]

    async def _get_problem_users(self) -> List[Dict[str, Any]]:
        """Get users with moderation issues."""
        return [
            {"user_id": "user4", "username": "TroubleMaker", "warnings": 3},
            {"user_id": "user5", "username": "SpamBot", "warnings": 2}
        ]

    async def _get_top_categories(self) -> List[Dict[str, Any]]:
        """Get top content categories."""
        return [
            {"category": "residential", "count": 156},
            {"category": "commercial", "count": 98},
            {"category": "industrial", "count": 67}
        ]

    async def _get_content_quality_metrics(self) -> Dict[str, Any]:
        """Get content quality metrics."""
        return {
            "average_rating": 4.2,
            "completion_rate": 0.85,
            "community_score": 8.7
        }

    async def _update_onboarding_progress(self, user_id: str, step: str, completed: bool) -> bool:
        """Update user onboarding progress."""
        # Implementation would update user onboarding data
        return True

    async def _send_onboarding_notification(self, user_id: str, step: str) -> bool:
        """Send onboarding notification."""
        # Implementation would send appropriate notification
        return True

    async def _get_onboarding_completion_rate(self) -> float:
        """Get onboarding completion rate."""
        return 0.72  # 72% completion rate

    async def _get_step_completion_rates(self) -> Dict[str, float]:
        """Get completion rates for each onboarding step."""
        return {
            "welcome": 0.95,
            "profile_setup": 0.88,
            "first_project": 0.65,
            "community_guidelines": 0.78,
            "final": 0.72
        }

    async def _get_onboarding_dropoff_points(self) -> List[Dict[str, Any]]:
        """Get onboarding dropoff points."""
        return [
            {"step": "first_project", "dropoff_rate": 0.23},
            {"step": "community_guidelines", "dropoff_rate": 0.13},
            {"step": "final", "dropoff_rate": 0.06}
        ]

    async def _get_average_completion_time(self) -> str:
        """Get average onboarding completion time."""
        return "3.2 days"


# Global moderator dashboard service instance
mod_dashboard_service = ModDashboardService()
