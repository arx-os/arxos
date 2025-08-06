"""
SVGX Engine - Go Notification API Client

This module provides a Python client for the Go notification API, enabling
seamless integration between Python services and the Go notification system.

Features:
- HTTP client for Go notification API
- Async notification sending
- Error handling and retry logic
- Template variable substitution
- Backward compatibility with existing Python notification services

Author: Arxos Engineering Team
Date: 2024-12-19
Version: 1.0.0
"""

import asyncio
import json
import logging
import time
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum
import aiohttp
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)


class NotificationChannelType(str, Enum):
    """Notification channel types supported by Go API"""

    EMAIL = "email"
    SLACK = "slack"
    SMS = "sms"
    WEBHOOK = "webhook"
    PUSH = "push"
    IN_APP = "in_app"


class NotificationPriority(str, Enum):
    """Notification priority levels"""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class NotificationType(str, Enum):
    """Notification types"""

    SYSTEM = "system"
    USER = "user"
    MAINTENANCE = "maintenance"
    ALERT = "alert"
    REMINDER = "reminder"
    UPDATE = "update"
    SECURITY = "security"


class NotificationStatus(str, Enum):
    """Notification status values"""

    PENDING = "pending"
    SENDING = "sending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    RATE_LIMITED = "rate_limited"
    CANCELLED = "cancelled"


@dataclass
class NotificationRequest:
    """Request structure for sending notifications via Go API"""

    title: str
    message: str
    type: NotificationType
    channels: List[NotificationChannelType]
    priority: NotificationPriority = NotificationPriority.NORMAL
    recipient_id: int
    sender_id: Optional[int] = None
    config_id: Optional[int] = None
    template_id: Optional[int] = None
    template_data: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
    building_id: Optional[int] = None
    asset_id: Optional[str] = None
    related_object_id: Optional[str] = None
    related_object_type: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API request"""
        data = asdict(self)
        # Convert enums to strings
        data["type"] = self.type.value
        data["channels"] = [channel.value for channel in self.channels]
        data["priority"] = self.priority.value
        return data


@dataclass
class NotificationResponse:
    """Response structure from Go notification API"""

    success: bool
    notification_id: Optional[int] = None
    message: Optional[str] = None
    created_at: Optional[str] = None
    error: Optional[str] = None


@dataclass
class NotificationHistoryRequest:
    """Request structure for retrieving notification history"""

    user_id: Optional[int] = None
    recipient_id: Optional[int] = None
    sender_id: Optional[int] = None
    type: Optional[NotificationType] = None
    status: Optional[NotificationStatus] = None
    priority: Optional[NotificationPriority] = None
    channel: Optional[NotificationChannelType] = None
    building_id: Optional[int] = None
    asset_id: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    page: int = 1
    page_size: int = 20

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API request"""
        data = asdict(self)
        # Convert enums to strings
        if self.type:
            data["type"] = self.type.value
        if self.status:
            data["status"] = self.status.value
        if self.priority:
            data["priority"] = self.priority.value
        if self.channel:
            data["channel"] = self.channel.value
        return data


@dataclass
class NotificationStatistics:
    """Statistics response from Go notification API"""

    total_sent: int
    total_delivered: int
    total_failed: int
    success_rate: float
    avg_delivery_time: float
    period: str
    generated_at: str


class GoNotificationClient:
    """
    Python client for Go notification API

    Provides seamless integration between Python services and the Go notification system
    with comprehensive error handling, retry logic, and template support.
    """

    def __init__(
        self,
        base_url: str = "http://localhost:8080",
        timeout: int = 30,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        session: Optional[aiohttp.ClientSession] = None,
    ):
        """
        Initialize the Go notification client

        Args:
            base_url: Base URL for the Go notification API
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
            retry_delay: Delay between retries in seconds
            session: Optional aiohttp session for async operations
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.session = session

        # Configure synchronous HTTP client with retry logic
        self.http_client = requests.Session()
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=retry_delay,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.http_client.mount("http://", adapter)
        self.http_client.mount("https://", adapter)

    async def __aenter__(self):
        """Async context manager entry"""
        if not self.session:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.timeout)
            )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session and not self.session.closed:
            await self.session.close()

    def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> requests.Response:
        """
        Make HTTP request to Go notification API

        Args:
            method: HTTP method
            endpoint: API endpoint
            data: Request data
            params: Query parameters

        Returns:
            HTTP response

        Raises:
            requests.RequestException: On HTTP errors
        """
        url = f"{self.base_url}{endpoint}"

        try:
            response = self.http_client.request(
                method=method, url=url, json=data, params=params, timeout=self.timeout
            )
            response.raise_for_status()
            return response
        except requests.RequestException as e:
            logger.error(f"HTTP request failed: {e}")
            raise

    async def _make_async_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> aiohttp.ClientResponse:
        """
        Make async HTTP request to Go notification API

        Args:
            method: HTTP method
            endpoint: API endpoint
            data: Request data
            params: Query parameters

        Returns:
            HTTP response

        Raises:
            aiohttp.ClientError: On HTTP errors
        """
        if not self.session:
            raise RuntimeError("No active session. Use async context manager.")

        url = f"{self.base_url}{endpoint}"

        try:
            async with self.session.request(
                method=method, url=url, json=data, params=params
            ) as response:
                response.raise_for_status()
                return response
        except aiohttp.ClientError as e:
            logger.error(f"Async HTTP request failed: {e}")
            raise

    def send_notification(self, request: NotificationRequest) -> NotificationResponse:
        """
        Send notification synchronously

        Args:
            request: Notification request

        Returns:
            Notification response
        """
        try:
            response = self._make_request(
                method="POST",
                endpoint="/api/notifications/send",
                data=request.to_dict(),
            )

            response_data = response.json()
            return NotificationResponse(**response_data)

        except Exception as e:
            logger.error(f"Failed to send notification: {e}")
            return NotificationResponse(success=False, error=str(e))

    async def send_notification_async(
        self, request: NotificationRequest
    ) -> NotificationResponse:
        """
        Send notification asynchronously

        Args:
            request: Notification request

        Returns:
            Notification response
        """
        try:
            response = await self._make_async_request(
                method="POST",
                endpoint="/api/notifications/send",
                data=request.to_dict(),
            )

            response_data = await response.json()
            return NotificationResponse(**response_data)

        except Exception as e:
            logger.error(f"Failed to send notification async: {e}")
            return NotificationResponse(success=False, error=str(e))

    def get_notification_history(
        self, request: NotificationHistoryRequest
    ) -> Dict[str, Any]:
        """
        Get notification history

        Args:
            request: History request parameters

        Returns:
            Notification history data
        """
        try:
            response = self._make_request(
                method="GET",
                endpoint="/api/notifications/history",
                params=request.to_dict(),
            )

            return response.json()

        except Exception as e:
            logger.error(f"Failed to get notification history: {e}")
            return {"error": str(e)}

    async def get_notification_history_async(
        self, request: NotificationHistoryRequest
    ) -> Dict[str, Any]:
        """
        Get notification history asynchronously

        Args:
            request: History request parameters

        Returns:
            Notification history data
        """
        try:
            response = await self._make_async_request(
                method="GET",
                endpoint="/api/notifications/history",
                params=request.to_dict(),
            )

            return await response.json()

        except Exception as e:
            logger.error(f"Failed to get notification history async: {e}")
            return {"error": str(e)}

    def get_notification_statistics(
        self, period: str = "7d"
    ) -> Optional[NotificationStatistics]:
        """
        Get notification statistics

        Args:
            period: Statistics period (e.g., "7d", "30d")

        Returns:
            Notification statistics
        """
        try:
            response = self._make_request(
                method="GET",
                endpoint="/api/notifications/statistics",
                params={"period": period},
            )

            data = response.json()
            return NotificationStatistics(**data)

        except Exception as e:
            logger.error(f"Failed to get notification statistics: {e}")
            return None

    async def get_notification_statistics_async(
        self, period: str = "7d"
    ) -> Optional[NotificationStatistics]:
        """
        Get notification statistics asynchronously

        Args:
            period: Statistics period (e.g., "7d", "30d")

        Returns:
            Notification statistics
        """
        try:
            response = await self._make_async_request(
                method="GET",
                endpoint="/api/notifications/statistics",
                params={"period": period},
            )

            data = await response.json()
            return NotificationStatistics(**data)

        except Exception as e:
            logger.error(f"Failed to get notification statistics async: {e}")
            return None

    def health_check(self) -> Dict[str, Any]:
        """
        Check Go notification service health

        Returns:
            Health status
        """
        try:
            response = self._make_request(
                method="GET", endpoint="/api/notifications/health"
            )

            return response.json()

        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {"status": "unhealthy", "error": str(e)}

    async def health_check_async(self) -> Dict[str, Any]:
        """
        Check Go notification service health asynchronously

        Returns:
            Health status
        """
        try:
            response = await self._make_async_request(
                method="GET", endpoint="/api/notifications/health"
            )

            return await response.json()

        except Exception as e:
            logger.error(f"Health check failed async: {e}")
            return {"status": "unhealthy", "error": str(e)}

    def substitute_template_variables(
        self, template: str, variables: Dict[str, Any]
    ) -> str:
        """
        Substitute variables in notification template

        Args:
            template: Template string with {{variable}} placeholders
            variables: Dictionary of variables to substitute

        Returns:
            Template with substituted variables
        """
        try:
            result = template
            for key, value in variables.items():
                placeholder = f"{{{{{key}}}}}"
                result = result.replace(placeholder, str(value))
            return result
        except Exception as e:
            logger.error(f"Template variable substitution failed: {e}")
            return template

    def create_notification_request(
        self,
        title: str,
        message: str,
        notification_type: NotificationType,
        channels: List[NotificationChannelType],
        recipient_id: int,
        priority: NotificationPriority = NotificationPriority.NORMAL,
        template_data: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> NotificationRequest:
        """
        Create a notification request with template support

        Args:
            title: Notification title
            message: Notification message (can contain template variables)
            notification_type: Type of notification
            channels: List of channels to send to
            recipient_id: ID of the recipient
            priority: Notification priority
            template_data: Variables for template substitution
            **kwargs: Additional notification parameters

        Returns:
            Notification request
        """
        # Substitute template variables if provided
        if template_data:
            title = self.substitute_template_variables(title, template_data)
            message = self.substitute_template_variables(message, template_data)

        return NotificationRequest(
            title=title,
            message=message,
            type=notification_type,
            channels=channels,
            priority=priority,
            recipient_id=recipient_id,
            template_data=template_data,
            **kwargs,
        )

    def send_simple_notification(
        self,
        title: str,
        message: str,
        recipient_id: int,
        channels: Optional[List[NotificationChannelType]] = None,
        priority: NotificationPriority = NotificationPriority.NORMAL,
        **kwargs,
    ) -> NotificationResponse:
        """
        Send a simple notification (convenience method)

        Args:
            title: Notification title
            message: Notification message
            recipient_id: ID of the recipient
            channels: List of channels (defaults to email)
            priority: Notification priority
            **kwargs: Additional parameters

        Returns:
            Notification response
        """
        if channels is None:
            channels = [NotificationChannelType.EMAIL]

        request = self.create_notification_request(
            title=title,
            message=message,
            notification_type=NotificationType.SYSTEM,
            channels=channels,
            recipient_id=recipient_id,
            priority=priority,
            **kwargs,
        )

        return self.send_notification(request)

    async def send_simple_notification_async(
        self,
        title: str,
        message: str,
        recipient_id: int,
        channels: Optional[List[NotificationChannelType]] = None,
        priority: NotificationPriority = NotificationPriority.NORMAL,
        **kwargs,
    ) -> NotificationResponse:
        """
        Send a simple notification asynchronously (convenience method)

        Args:
            title: Notification title
            message: Notification message
            recipient_id: ID of the recipient
            channels: List of channels (defaults to email)
            priority: Notification priority
            **kwargs: Additional parameters

        Returns:
            Notification response
        """
        if channels is None:
            channels = [NotificationChannelType.EMAIL]

        request = self.create_notification_request(
            title=title,
            message=message,
            notification_type=NotificationType.SYSTEM,
            channels=channels,
            recipient_id=recipient_id,
            priority=priority,
            **kwargs,
        )

        return await self.send_notification_async(request)


# Backward compatibility wrapper for existing Python notification services
class GoNotificationWrapper:
    """
    Wrapper class to maintain backward compatibility with existing Python notification services
    """

    def __init__(self, go_client: GoNotificationClient):
        """
        Initialize wrapper with Go notification client

        Args:
            go_client: Go notification client instance
        """
        self.go_client = go_client

    def send_email(
        self,
        to_email: str,
        subject: str,
        body: str,
        html_body: Optional[str] = None,
        priority: str = "normal",
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Send email notification (backward compatibility)

        Args:
            to_email: Recipient email
            subject: Email subject
            body: Email body
            html_body: HTML email body
            priority: Email priority
            **kwargs: Additional parameters

        Returns:
            Response dictionary
        """
        # Convert priority string to enum
        priority_enum = NotificationPriority(priority.lower())

        # Create notification request
        request = self.go_client.create_notification_request(
            title=subject,
            message=body,
            notification_type=NotificationType.USER,
            channels=[NotificationChannelType.EMAIL],
            recipient_id=kwargs.get("recipient_id", 1),  # Default recipient ID
            priority=priority_enum,
            metadata={"to_email": to_email, "html_body": html_body, **kwargs},
        )

        response = self.go_client.send_notification(request)
        return {
            "success": response.success,
            "notification_id": response.notification_id,
            "message": response.message,
            "error": response.error,
        }

    def send_slack(
        self, channel: str, message: str, message_type: str = "info", **kwargs
    ) -> Dict[str, Any]:
        """
        Send Slack notification (backward compatibility)

        Args:
            channel: Slack channel
            message: Slack message
            message_type: Type of message
            **kwargs: Additional parameters

        Returns:
            Response dictionary
        """
        # Create notification request
        request = self.go_client.create_notification_request(
            title=f"Slack {message_type.title()}",
            message=message,
            notification_type=NotificationType.SYSTEM,
            channels=[NotificationChannelType.SLACK],
            recipient_id=kwargs.get("recipient_id", 1),  # Default recipient ID
            priority=NotificationPriority.NORMAL,
            metadata={"slack_channel": channel, "message_type": message_type, **kwargs},
        )

        response = self.go_client.send_notification(request)
        return {
            "success": response.success,
            "notification_id": response.notification_id,
            "message": response.message,
            "error": response.error,
        }

    def send_sms(self, phone_number: str, message: str, **kwargs) -> Dict[str, Any]:
        """
        Send SMS notification (backward compatibility)

        Args:
            phone_number: Recipient phone number
            message: SMS message
            **kwargs: Additional parameters

        Returns:
            Response dictionary
        """
        # Create notification request
        request = self.go_client.create_notification_request(
            title="SMS Notification",
            message=message,
            notification_type=NotificationType.ALERT,
            channels=[NotificationChannelType.SMS],
            recipient_id=kwargs.get("recipient_id", 1),  # Default recipient ID
            priority=NotificationPriority.HIGH,
            metadata={"phone_number": phone_number, **kwargs},
        )

        response = self.go_client.send_notification(request)
        return {
            "success": response.success,
            "notification_id": response.notification_id,
            "message": response.message,
            "error": response.error,
        }

    def send_webhook(
        self, url: str, payload: Dict[str, Any], method: str = "POST", **kwargs
    ) -> Dict[str, Any]:
        """
        Send webhook notification (backward compatibility)

        Args:
            url: Webhook URL
            payload: Webhook payload
            method: HTTP method
            **kwargs: Additional parameters

        Returns:
            Response dictionary
        """
        # Create notification request
        request = self.go_client.create_notification_request(
            title="Webhook Notification",
            message=json.dumps(payload),
            notification_type=NotificationType.SYSTEM,
            channels=[NotificationChannelType.WEBHOOK],
            recipient_id=kwargs.get("recipient_id", 1),  # Default recipient ID
            priority=NotificationPriority.NORMAL,
            metadata={
                "webhook_url": url,
                "method": method,
                "payload": payload,
                **kwargs,
            },
        )

        response = self.go_client.send_notification(request)
        return {
            "success": response.success,
            "notification_id": response.notification_id,
            "message": response.message,
            "error": response.error,
        }


# Factory functions for easy instantiation
def create_go_notification_client(
    base_url: str = "http://localhost:8080",
    timeout: int = 30,
    max_retries: int = 3,
    retry_delay: float = 1.0,
) -> GoNotificationClient:
    """
    Create a Go notification client

    Args:
        base_url: Base URL for the Go notification API
        timeout: Request timeout in seconds
        max_retries: Maximum number of retry attempts
        retry_delay: Delay between retries in seconds

    Returns:
        Go notification client
    """
    return GoNotificationClient(
        base_url=base_url,
        timeout=timeout,
        max_retries=max_retries,
        retry_delay=retry_delay,
    )


def create_go_notification_wrapper(
    base_url: str = "http://localhost:8080",
    timeout: int = 30,
    max_retries: int = 3,
    retry_delay: float = 1.0,
) -> GoNotificationWrapper:
    """
    Create a Go notification wrapper for backward compatibility

    Args:
        base_url: Base URL for the Go notification API
        timeout: Request timeout in seconds
        max_retries: Maximum number of retry attempts
        retry_delay: Delay between retries in seconds

    Returns:
        Go notification wrapper
    """
    go_client = create_go_notification_client(
        base_url=base_url,
        timeout=timeout,
        max_retries=max_retries,
        retry_delay=retry_delay,
    )
    return GoNotificationWrapper(go_client)


# Export main classes and functions
__all__ = [
    "GoNotificationClient",
    "GoNotificationWrapper",
    "NotificationRequest",
    "NotificationResponse",
    "NotificationHistoryRequest",
    "NotificationStatistics",
    "NotificationChannelType",
    "NotificationPriority",
    "NotificationType",
    "NotificationStatus",
    "create_go_notification_client",
    "create_go_notification_wrapper",
]
