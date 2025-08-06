"""
Collaboration Notification System
Handles notifications for collaborative events like draft updates, comments, and assignments
"""

import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, asdict
from enum import Enum
import logging
import asyncio
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
import json

logger = logging.getLogger(__name__)


class NotificationType(Enum):
    """Types of collaboration notifications"""

    DRAFT_UPDATED = "draft_updated"
    COMMENT_ADDED = "comment_added"
    COMMENT_REPLY = "comment_reply"
    THREAD_ASSIGNED = "thread_assigned"
    THREAD_RESOLVED = "thread_resolved"
    MENTION = "mention"
    DRAFT_SUBMITTED = "draft_submitted"
    DRAFT_APPROVED = "draft_approved"
    DRAFT_REJECTED = "draft_rejected"
    COLLABORATOR_JOINED = "collaborator_joined"
    COLLABORATOR_LEFT = "collaborator_left"
    MILESTONE_REACHED = "milestone_reached"
    FUNDING_UPDATE = "funding_update"


class NotificationPriority(Enum):
    """Notification priority levels"""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class NotificationStatus(Enum):
    """Notification status"""

    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    FAILED = "failed"


@dataclass
class Notification:
    """Individual notification"""

    id: str
    user_id: str
    notification_type: NotificationType
    priority: NotificationPriority
    status: NotificationStatus
    title: str
    message: str
    created_at: datetime
    sent_at: Optional[datetime]
    read_at: Optional[datetime]
    metadata: Dict
    actions: List[Dict]

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        if self.actions is None:
            self.actions = []


@dataclass
class NotificationTemplate:
    """Template for generating notifications"""

    type: NotificationType
    title_template: str
    message_template: str
    priority: NotificationPriority
    actions: List[Dict]
    email_template: Optional[str]

    def __post_init__(self):
        if self.actions is None:
            self.actions = []


class CollaborationNotificationService:
    """Service for handling collaboration notifications"""

    def __init__(self):
        self.notifications: Dict[str, Notification] = {}
        self.user_notifications: Dict[str, List[str]] = {}
        self.templates: Dict[NotificationType, NotificationTemplate] = {}
        self.email_config: Dict = {}
        self.websocket_connections: Dict[str, Set] = {}
        self.logger = logging.getLogger(__name__)

        self._initialize_templates()

    def _initialize_templates(self):
        """Initialize notification templates"""

        self.templates = {
            NotificationType.DRAFT_UPDATED: NotificationTemplate(
                type=NotificationType.DRAFT_UPDATED,
                title_template="Draft '{draft_title}' has been updated",
                message_template="The draft '{draft_title}' has been updated by {updater_name}. Click to view changes.",
                priority=NotificationPriority.NORMAL,
                actions=[
                    {
                        "label": "View Draft",
                        "action": "view_draft",
                        "url": "/drafts/{draft_id}",
                    },
                    {
                        "label": "View Changes",
                        "action": "view_changes",
                        "url": "/drafts/{draft_id}/changes",
                    },
                ],
                email_template="draft_updated.html",
            ),
            NotificationType.COMMENT_ADDED: NotificationTemplate(
                type=NotificationType.COMMENT_ADDED,
                title_template="New comment on '{draft_title}'",
                message_template="{author_name} added a comment: '{comment_preview}'",
                priority=NotificationPriority.NORMAL,
                actions=[
                    {
                        "label": "View Comment",
                        "action": "view_comment",
                        "url": "/drafts/{draft_id}#comment-{comment_id}",
                    },
                    {
                        "label": "Reply",
                        "action": "reply_comment",
                        "url": "/drafts/{draft_id}/comments/{comment_id}/reply",
                    },
                ],
                email_template="comment_added.html",
            ),
            NotificationType.COMMENT_REPLY: NotificationTemplate(
                type=NotificationType.COMMENT_REPLY,
                title_template="Reply to your comment",
                message_template="{author_name} replied to your comment: '{reply_preview}'",
                priority=NotificationPriority.HIGH,
                actions=[
                    {
                        "label": "View Reply",
                        "action": "view_reply",
                        "url": "/drafts/{draft_id}#comment-{comment_id}",
                    },
                    {
                        "label": "Reply",
                        "action": "reply_comment",
                        "url": "/drafts/{draft_id}/comments/{comment_id}/reply",
                    },
                ],
                email_template="comment_reply.html",
            ),
            NotificationType.THREAD_ASSIGNED: NotificationTemplate(
                type=NotificationType.THREAD_ASSIGNED,
                title_template="Thread assigned to you",
                message_template="You have been assigned to the thread '{thread_title}' by {assigner_name}",
                priority=NotificationPriority.HIGH,
                actions=[
                    {
                        "label": "View Thread",
                        "action": "view_thread",
                        "url": "/threads/{thread_id}",
                    },
                    {
                        "label": "Mark Resolved",
                        "action": "resolve_thread",
                        "url": "/threads/{thread_id}/resolve",
                    },
                ],
                email_template="thread_assigned.html",
            ),
            NotificationType.THREAD_RESOLVED: NotificationTemplate(
                type=NotificationType.THREAD_RESOLVED,
                title_template="Thread resolved",
                message_template="The thread '{thread_title}' has been resolved by {resolver_name}",
                priority=NotificationPriority.NORMAL,
                actions=[
                    {
                        "label": "View Thread",
                        "action": "view_thread",
                        "url": "/threads/{thread_id}",
                    }
                ],
                email_template="thread_resolved.html",
            ),
            NotificationType.MENTION: NotificationTemplate(
                type=NotificationType.MENTION,
                title_template="You were mentioned",
                message_template="{author_name} mentioned you in a comment: '{mention_preview}'",
                priority=NotificationPriority.HIGH,
                actions=[
                    {
                        "label": "View Mention",
                        "action": "view_mention",
                        "url": "/drafts/{draft_id}#comment-{comment_id}",
                    },
                    {
                        "label": "Reply",
                        "action": "reply_comment",
                        "url": "/drafts/{draft_id}/comments/{comment_id}/reply",
                    },
                ],
                email_template="mention.html",
            ),
            NotificationType.DRAFT_SUBMITTED: NotificationTemplate(
                type=NotificationType.DRAFT_SUBMITTED,
                title_template="Draft submitted for review",
                message_template="The draft '{draft_title}' has been submitted for review by {submitter_name}",
                priority=NotificationPriority.HIGH,
                actions=[
                    {
                        "label": "Review Draft",
                        "action": "review_draft",
                        "url": "/admin/review/{draft_id}",
                    },
                    {
                        "label": "View Draft",
                        "action": "view_draft",
                        "url": "/drafts/{draft_id}",
                    },
                ],
                email_template="draft_submitted.html",
            ),
            NotificationType.DRAFT_APPROVED: NotificationTemplate(
                type=NotificationType.DRAFT_APPROVED,
                title_template="Draft approved",
                message_template="Your draft '{draft_title}' has been approved by {approver_name}",
                priority=NotificationPriority.HIGH,
                actions=[
                    {
                        "label": "View Draft",
                        "action": "view_draft",
                        "url": "/drafts/{draft_id}",
                    },
                    {
                        "label": "Publish",
                        "action": "publish_draft",
                        "url": "/drafts/{draft_id}/publish",
                    },
                ],
                email_template="draft_approved.html",
            ),
            NotificationType.DRAFT_REJECTED: NotificationTemplate(
                type=NotificationType.DRAFT_REJECTED,
                title_template="Draft needs revision",
                message_template="Your draft '{draft_title}' needs revision. Reason: {rejection_reason}",
                priority=NotificationPriority.HIGH,
                actions=[
                    {
                        "label": "View Feedback",
                        "action": "view_feedback",
                        "url": "/drafts/{draft_id}/feedback",
                    },
                    {
                        "label": "Edit Draft",
                        "action": "edit_draft",
                        "url": "/drafts/{draft_id}/edit",
                    },
                ],
                email_template="draft_rejected.html",
            ),
            NotificationType.COLLABORATOR_JOINED: NotificationTemplate(
                type=NotificationType.COLLABORATOR_JOINED,
                title_template="New collaborator joined",
                message_template="{collaborator_name} has joined the draft '{draft_title}'",
                priority=NotificationPriority.NORMAL,
                actions=[
                    {
                        "label": "View Collaborators",
                        "action": "view_collaborators",
                        "url": "/drafts/{draft_id}/collaborators",
                    }
                ],
                email_template="collaborator_joined.html",
            ),
            NotificationType.COLLABORATOR_LEFT: NotificationTemplate(
                type=NotificationType.COLLABORATOR_LEFT,
                title_template="Collaborator left",
                message_template="{collaborator_name} has left the draft '{draft_title}'",
                priority=NotificationPriority.LOW,
                actions=[
                    {
                        "label": "View Collaborators",
                        "action": "view_collaborators",
                        "url": "/drafts/{draft_id}/collaborators",
                    }
                ],
                email_template="collaborator_left.html",
            ),
            NotificationType.MILESTONE_REACHED: NotificationTemplate(
                type=NotificationType.MILESTONE_REACHED,
                title_template="Milestone reached",
                message_template="The milestone '{milestone_name}' has been reached for '{draft_title}'",
                priority=NotificationPriority.HIGH,
                actions=[
                    {
                        "label": "View Milestone",
                        "action": "view_milestone",
                        "url": "/drafts/{draft_id}/milestones",
                    },
                    {
                        "label": "Release Funds",
                        "action": "release_funds",
                        "url": "/escrow/{draft_id}/release",
                    },
                ],
                email_template="milestone_reached.html",
            ),
            NotificationType.FUNDING_UPDATE: NotificationTemplate(
                type=NotificationType.FUNDING_UPDATE,
                title_template="Funding update",
                message_template="Funding status updated for '{draft_title}': {funding_message}",
                priority=NotificationPriority.NORMAL,
                actions=[
                    {
                        "label": "View Funding",
                        "action": "view_funding",
                        "url": "/drafts/{draft_id}/funding",
                    }
                ],
                email_template="funding_update.html",
            ),
        }

    def create_notification(
        self,
        user_id: str,
        notification_type: NotificationType,
        title: str,
        message: str,
        priority: NotificationPriority = NotificationPriority.NORMAL,
        metadata: Dict = None,
        actions: List[Dict] = None,
    ) -> Notification:
        """Create a new notification"""

        notification_id = str(uuid.uuid4())
        now = datetime.utcnow()

        notification = Notification(
            id=notification_id,
            user_id=user_id,
            notification_type=notification_type,
            priority=priority,
            status=NotificationStatus.PENDING,
            title=title,
            message=message,
            created_at=now,
            sent_at=None,
            read_at=None,
            metadata=metadata or {},
            actions=actions or [],
        )

        # Store notification
        self.notifications[notification_id] = notification

        # Add to user's notification list
        if user_id not in self.user_notifications:
            self.user_notifications[user_id] = []
        self.user_notifications[user_id].append(notification_id)

        self.logger.info(f"Created notification {notification_id} for user {user_id}")
        return notification

    def create_notification_from_template(
        self,
        user_id: str,
        notification_type: NotificationType,
        template_data: Dict,
        metadata: Dict = None,
    ) -> Notification:
        """Create notification using a template"""

        if notification_type not in self.templates:
            raise ValueError(
                f"No template found for notification type {notification_type}"
            )

        template = self.templates[notification_type]

        # Format title and message
        title = template.title_template.format(**template_data)
        message = template.message_template.format(**template_data)

        # Format actions with template data
        actions = []
        for action in template.actions:
            formatted_action = action.copy()
            if "url" in formatted_action:
                formatted_action["url"] = formatted_action["url"].format(
                    **template_data
                )
            actions.append(formatted_action)

        return self.create_notification(
            user_id=user_id,
            notification_type=notification_type,
            title=title,
            message=message,
            priority=template.priority,
            metadata=metadata or {},
            actions=actions,
        )

    def notify_draft_updated(
        self,
        draft_id: str,
        draft_title: str,
        updater_id: str,
        updater_name: str,
        subscribers: List[str],
    ):
        """Notify subscribers about draft updates"""

        template_data = {
            "draft_id": draft_id,
            "draft_title": draft_title,
            "updater_id": updater_id,
            "updater_name": updater_name,
        }

        for user_id in subscribers:
            if user_id != updater_id:  # Don't notify the updater
                self.create_notification_from_template(
                    user_id=user_id,
                    notification_type=NotificationType.DRAFT_UPDATED,
                    template_data=template_data,
                )

    def notify_comment_added(
        self,
        draft_id: str,
        draft_title: str,
        comment_id: str,
        author_id: str,
        author_name: str,
        comment_preview: str,
        subscribers: List[str],
    ):
        """Notify subscribers about new comments"""

        template_data = {
            "draft_id": draft_id,
            "draft_title": draft_title,
            "comment_id": comment_id,
            "author_id": author_id,
            "author_name": author_name,
            "comment_preview": (
                comment_preview[:100] + "..."
                if len(comment_preview) > 100
                else comment_preview
            ),
        }

        for user_id in subscribers:
            if user_id != author_id:  # Don't notify the author
                self.create_notification_from_template(
                    user_id=user_id,
                    notification_type=NotificationType.COMMENT_ADDED,
                    template_data=template_data,
                )

    def notify_comment_reply(
        self,
        draft_id: str,
        draft_title: str,
        comment_id: str,
        parent_author_id: str,
        author_id: str,
        author_name: str,
        reply_preview: str,
    ):
        """Notify parent comment author about replies"""

        template_data = {
            "draft_id": draft_id,
            "draft_title": draft_title,
            "comment_id": comment_id,
            "author_id": author_id,
            "author_name": author_name,
            "reply_preview": (
                reply_preview[:100] + "..."
                if len(reply_preview) > 100
                else reply_preview
            ),
        }

        self.create_notification_from_template(
            user_id=parent_author_id,
            notification_type=NotificationType.COMMENT_REPLY,
            template_data=template_data,
        )

    def notify_mention(
        self,
        draft_id: str,
        draft_title: str,
        comment_id: str,
        mentioned_user_id: str,
        author_id: str,
        author_name: str,
        mention_preview: str,
    ):
        """Notify mentioned users"""

        template_data = {
            "draft_id": draft_id,
            "draft_title": draft_title,
            "comment_id": comment_id,
            "author_id": author_id,
            "author_name": author_name,
            "mention_preview": (
                mention_preview[:100] + "..."
                if len(mention_preview) > 100
                else mention_preview
            ),
        }

        self.create_notification_from_template(
            user_id=mentioned_user_id,
            notification_type=NotificationType.MENTION,
            template_data=template_data,
        )

    def notify_thread_assigned(
        self,
        thread_id: str,
        thread_title: str,
        assignee_id: str,
        assigner_id: str,
        assigner_name: str,
    ):
        """Notify user about thread assignment"""

        template_data = {
            "thread_id": thread_id,
            "thread_title": thread_title,
            "assignee_id": assignee_id,
            "assigner_id": assigner_id,
            "assigner_name": assigner_name,
        }

        self.create_notification_from_template(
            user_id=assignee_id,
            notification_type=NotificationType.THREAD_ASSIGNED,
            template_data=template_data,
        )

    def notify_thread_resolved(
        self,
        thread_id: str,
        thread_title: str,
        resolver_id: str,
        resolver_name: str,
        subscribers: List[str],
    ):
        """Notify subscribers about thread resolution"""

        template_data = {
            "thread_id": thread_id,
            "thread_title": thread_title,
            "resolver_id": resolver_id,
            "resolver_name": resolver_name,
        }

        for user_id in subscribers:
            if user_id != resolver_id:  # Don't notify the resolver
                self.create_notification_from_template(
                    user_id=user_id,
                    notification_type=NotificationType.THREAD_RESOLVED,
                    template_data=template_data,
                )

    def notify_draft_submitted(
        self,
        draft_id: str,
        draft_title: str,
        submitter_id: str,
        submitter_name: str,
        moderators: List[str],
    ):
        """Notify moderators about draft submission"""

        template_data = {
            "draft_id": draft_id,
            "draft_title": draft_title,
            "submitter_id": submitter_id,
            "submitter_name": submitter_name,
        }

        for moderator_id in moderators:
            self.create_notification_from_template(
                user_id=moderator_id,
                notification_type=NotificationType.DRAFT_SUBMITTED,
                template_data=template_data,
            )

    def notify_draft_approved(
        self,
        draft_id: str,
        draft_title: str,
        approver_id: str,
        approver_name: str,
        author_id: str,
    ):
        """Notify author about draft approval"""

        template_data = {
            "draft_id": draft_id,
            "draft_title": draft_title,
            "approver_id": approver_id,
            "approver_name": approver_name,
        }

        self.create_notification_from_template(
            user_id=author_id,
            notification_type=NotificationType.DRAFT_APPROVED,
            template_data=template_data,
        )

    def notify_draft_rejected(
        self,
        draft_id: str,
        draft_title: str,
        rejector_id: str,
        rejector_name: str,
        rejection_reason: str,
        author_id: str,
    ):
        """Notify author about draft rejection"""

        template_data = {
            "draft_id": draft_id,
            "draft_title": draft_title,
            "rejector_id": rejector_id,
            "rejector_name": rejector_name,
            "rejection_reason": rejection_reason,
        }

        self.create_notification_from_template(
            user_id=author_id,
            notification_type=NotificationType.DRAFT_REJECTED,
            template_data=template_data,
        )

    def notify_collaborator_joined(
        self,
        draft_id: str,
        draft_title: str,
        collaborator_id: str,
        collaborator_name: str,
        subscribers: List[str],
    ):
        """Notify subscribers about new collaborator"""

        template_data = {
            "draft_id": draft_id,
            "draft_title": draft_title,
            "collaborator_id": collaborator_id,
            "collaborator_name": collaborator_name,
        }

        for user_id in subscribers:
            if user_id != collaborator_id:  # Don't notify the new collaborator
                self.create_notification_from_template(
                    user_id=user_id,
                    notification_type=NotificationType.COLLABORATOR_JOINED,
                    template_data=template_data,
                )

    def notify_collaborator_left(
        self,
        draft_id: str,
        draft_title: str,
        collaborator_id: str,
        collaborator_name: str,
        subscribers: List[str],
    ):
        """Notify subscribers about collaborator leaving"""

        template_data = {
            "draft_id": draft_id,
            "draft_title": draft_title,
            "collaborator_id": collaborator_id,
            "collaborator_name": collaborator_name,
        }

        for user_id in subscribers:
            if user_id != collaborator_id:  # Don't notify the leaving collaborator
                self.create_notification_from_template(
                    user_id=user_id,
                    notification_type=NotificationType.COLLABORATOR_LEFT,
                    template_data=template_data,
                )

    def notify_milestone_reached(
        self,
        draft_id: str,
        draft_title: str,
        milestone_name: str,
        subscribers: List[str],
    ):
        """Notify subscribers about milestone reached"""

        template_data = {
            "draft_id": draft_id,
            "draft_title": draft_title,
            "milestone_name": milestone_name,
        }

        for user_id in subscribers:
            self.create_notification_from_template(
                user_id=user_id,
                notification_type=NotificationType.MILESTONE_REACHED,
                template_data=template_data,
            )

    def notify_funding_update(
        self,
        draft_id: str,
        draft_title: str,
        funding_message: str,
        subscribers: List[str],
    ):
        """Notify subscribers about funding updates"""

        template_data = {
            "draft_id": draft_id,
            "draft_title": draft_title,
            "funding_message": funding_message,
        }

        for user_id in subscribers:
            self.create_notification_from_template(
                user_id=user_id,
                notification_type=NotificationType.FUNDING_UPDATE,
                template_data=template_data,
            )

    def mark_notification_read(self, notification_id: str, user_id: str) -> bool:
        """Mark a notification as read"""

        if notification_id not in self.notifications:
            return False

        notification = self.notifications[notification_id]
        if notification.user_id != user_id:
            return False

        notification.status = NotificationStatus.READ
        notification.read_at = datetime.utcnow()

        self.logger.info(f"Marked notification {notification_id} as read")
        return True

    def mark_all_notifications_read(self, user_id: str) -> int:
        """Mark all notifications for a user as read"""

        count = 0
        for notification in self.notifications.values():
            if (
                notification.user_id == user_id
                and notification.status != NotificationStatus.READ
            ):
                notification.status = NotificationStatus.READ
                notification.read_at = datetime.utcnow()
                count += 1

        self.logger.info(f"Marked {count} notifications as read for user {user_id}")
        return count

    def delete_notification(self, notification_id: str, user_id: str) -> bool:
        """Delete a notification"""

        if notification_id not in self.notifications:
            return False

        notification = self.notifications[notification_id]
        if notification.user_id != user_id:
            return False

        # Remove from storage
        del self.notifications[notification_id]

        # Remove from user's list
        if user_id in self.user_notifications:
            if notification_id in self.user_notifications[user_id]:
                self.user_notifications[user_id].remove(notification_id)

        self.logger.info(f"Deleted notification {notification_id}")
        return True

    def get_user_notifications(
        self,
        user_id: str,
        status: Optional[NotificationStatus] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Notification]:
        """Get notifications for a user"""

        if user_id not in self.user_notifications:
            return []

        user_notification_ids = self.user_notifications[user_id]
        notifications = []

        for notification_id in user_notification_ids[offset : offset + limit]:
            if notification_id in self.notifications:
                notification = self.notifications[notification_id]
                if status is None or notification.status == status:
                    notifications.append(notification)

        # Sort by creation date (newest first)
        notifications.sort(key=lambda x: x.created_at, reverse=True)
        return notifications

    def get_unread_count(self, user_id: str) -> int:
        """Get count of unread notifications for a user"""

        count = 0
        for notification in self.notifications.values():
            if (
                notification.user_id == user_id
                and notification.status != NotificationStatus.READ
            ):
                count += 1

        return count

    def get_notification_stats(self, user_id: str) -> Dict:
        """Get notification statistics for a user"""

        total_count = 0
        unread_count = 0
        type_counts = {}

        for notification in self.notifications.values():
            if notification.user_id == user_id:
                total_count += 1

                if notification.status != NotificationStatus.READ:
                    unread_count += 1

                notification_type = notification.notification_type.value
                type_counts[notification_type] = (
                    type_counts.get(notification_type, 0) + 1
                )

        return {
            "total_count": total_count,
            "unread_count": unread_count,
            "type_counts": type_counts,
        }

    def configure_email(
        self, smtp_host: str, smtp_port: int, username: str, password: str
    ):
        """Configure email settings"""

        self.email_config = {
            "smtp_host": smtp_host,
            "smtp_port": smtp_port,
            "username": username,
            "password": password,
        }

    async def send_email_notification(
        self, notification: Notification, user_email: str
    ):
        """Send email notification"""

        if not self.email_config:
            self.logger.warning("Email not configured, skipping email notification")
            return

        try:
            # Create email message
            msg = MIMEMultipart()
            msg["From"] = self.email_config["username"]
            msg["To"] = user_email
            msg["Subject"] = notification.title

            # Add body
            body = f"""
            {notification.message}
            
            Actions:
            """
            for action in notification.actions:
                body += f"- {action['label']}: {action['url']}\n"

            msg.attach(MIMEText(body, "plain"))

            # Send email
            with smtplib.SMTP(
                self.email_config["smtp_host"], self.email_config["smtp_port"]
            ) as server:
                server.starttls()
                server.login(
                    self.email_config["username"], self.email_config["password"]
                )
                server.send_message(msg)

            notification.status = NotificationStatus.SENT
            notification.sent_at = datetime.utcnow()

            self.logger.info(
                f"Sent email notification {notification.id} to {user_email}"
            )

        except Exception as e:
            notification.status = NotificationStatus.FAILED
            self.logger.error(
                f"Failed to send email notification {notification.id}: {e}"
            )

    def add_websocket_connection(self, user_id: str, websocket):
        """Add WebSocket connection for real-time notifications"""

        if user_id not in self.websocket_connections:
            self.websocket_connections[user_id] = set()

        self.websocket_connections[user_id].add(websocket)

    def remove_websocket_connection(self, user_id: str, websocket):
        """Remove WebSocket connection"""

        if user_id in self.websocket_connections:
            self.websocket_connections[user_id].discard(websocket)

            if not self.websocket_connections[user_id]:
                del self.websocket_connections[user_id]

    async def send_realtime_notification(
        self, user_id: str, notification: Notification
    ):
        """Send real-time notification via WebSocket"""

        if user_id not in self.websocket_connections:
            return

        notification_data = {
            "type": "notification",
            "notification": asdict(notification),
        }

        for websocket in self.websocket_connections[user_id]:
            try:
                await websocket.send(json.dumps(notification_data))
            except Exception as e:
                self.logger.error(f"Failed to send WebSocket notification: {e}")
                self.remove_websocket_connection(user_id, websocket)


# Global notification service instance
collab_notification_service = CollaborationNotificationService()
