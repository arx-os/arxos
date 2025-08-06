"""
Email Integration Service for Arxos

This module provides Python integration with the Go email notification service.
It handles email sending, template processing, and delivery tracking.
"""

import json
import logging
import asyncio
import aiohttp
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
import re

logger = logging.getLogger(__name__)


@dataclass
class EmailRequest:
    """Email notification request data structure."""

    to: str
    subject: str
    body: Optional[str] = None
    html_body: Optional[str] = None
    from_address: Optional[str] = None
    priority: str = "normal"
    template_id: Optional[str] = None
    template_data: Optional[Dict[str, Any]] = None
    max_retries: int = 3


@dataclass
class EmailResponse:
    """Email notification response data structure."""

    id: int
    status: str
    message: str
    estimated_delivery_time: Optional[datetime] = None


@dataclass
class EmailTemplate:
    """Email template data structure."""

    id: int
    name: str
    subject: str
    body: Optional[str] = None
    html_body: Optional[str] = None
    variables: Optional[Dict[str, Any]] = None
    is_active: bool = True


class EmailIntegrationService:
    """
    Email Integration Service for communicating with Go email service.

    This service provides a Python interface to the Go email notification
    service, handling email sending, template management, and delivery tracking.
    """

    def __init__(self, base_url: str = "http://localhost:8080", timeout: int = 30):
        """
        Initialize the email integration service.

        Args:
            base_url: Base URL of the Go email service
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.timeout)
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()

    def _validate_email(self, email: str) -> bool:
        """
        Validate email address format.

        Args:
            email: Email address to validate

        Returns:
            True if valid, False otherwise
        """
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        return bool(re.match(pattern, email))

    def _validate_request(self, request: EmailRequest) -> None:
        """
        Validate email request.

        Args:
            request: Email request to validate

        Raises:
            ValueError: If request is invalid
        """
        if not request.to:
            raise ValueError("Email address is required")

        if not self._validate_email(request.to):
            raise ValueError("Invalid email address format")

        if not request.subject:
            raise ValueError("Subject is required")

        if request.priority not in ["low", "normal", "high", "urgent"]:
            raise ValueError("Invalid priority level")

    async def send_email(self, request: EmailRequest) -> EmailResponse:
        """
        Send an email notification.

        Args:
            request: Email request

        Returns:
            Email response with delivery status

        Raises:
            ValueError: If request is invalid
            aiohttp.ClientError: If HTTP request fails
        """
        self._validate_request(request)

        if not self.session:
            raise RuntimeError("Service not initialized. Use async context manager.")

        # Prepare request payload
        payload = {
            "to": request.to,
            "subject": request.subject,
            "priority": request.priority,
            "max_retries": request.max_retries,
        }

        if request.body:
            payload["body"] = request.body

        if request.html_body:
            payload["html_body"] = request.html_body

        if request.from_address:
            payload["from"] = request.from_address

        if request.template_id:
            payload["template_id"] = request.template_id

        if request.template_data:
            payload["template_data"] = request.template_data

        try:
            async with self.session.post(
                f"{self.base_url}/api/notifications/email/send",
                json=payload,
                headers={"Content-Type": "application/json"},
            ) as response:
                if response.status == 201:
                    data = await response.json()
                    return EmailResponse(
                        id=data["id"],
                        status=data["status"],
                        message=data["message"],
                        estimated_delivery_time=(
                            datetime.fromisoformat(data["estimated_delivery_time"])
                            if data.get("estimated_delivery_time")
                            else None
                        ),
                    )
                else:
                    error_text = await response.text()
                    logger.error(
                        f"Email service error: {response.status} - {error_text}"
                    )
                    raise aiohttp.ClientError(f"Email service error: {response.status}")

        except aiohttp.ClientError as e:
            logger.error(f"Failed to send email: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error sending email: {e}")
            raise

    async def get_email_notifications(
        self,
        page: int = 1,
        limit: int = 20,
        status: Optional[str] = None,
        priority: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get email notifications with pagination and filtering.

        Args:
            page: Page number (1-based)
            limit: Number of items per page
            status: Filter by status
            priority: Filter by priority

        Returns:
            Dictionary with notifications and pagination info
        """
        if not self.session:
            raise RuntimeError("Service not initialized. Use async context manager.")

        params = {"page": page, "limit": limit}

        if status:
            params["status"] = status

        if priority:
            params["priority"] = priority

        try:
            async with self.session.get(
                f"{self.base_url}/api/notifications/email", params=params
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_text = await response.text()
                    logger.error(
                        f"Failed to get email notifications: {response.status} - {error_text}"
                    )
                    raise aiohttp.ClientError(
                        f"Failed to get email notifications: {response.status}"
                    )

        except aiohttp.ClientError as e:
            logger.error(f"Failed to get email notifications: {e}")
            raise

    async def get_email_notification(self, email_id: int) -> Dict[str, Any]:
        """
        Get a specific email notification.

        Args:
            email_id: Email notification ID

        Returns:
            Email notification data
        """
        if not self.session:
            raise RuntimeError("Service not initialized. Use async context manager.")

        try:
            async with self.session.get(
                f"{self.base_url}/api/notifications/email/{email_id}"
            ) as response:
                if response.status == 200:
                    return await response.json()
                elif response.status == 404:
                    raise ValueError("Email notification not found")
                else:
                    error_text = await response.text()
                    logger.error(
                        f"Failed to get email notification: {response.status} - {error_text}"
                    )
                    raise aiohttp.ClientError(
                        f"Failed to get email notification: {response.status}"
                    )

        except aiohttp.ClientError as e:
            logger.error(f"Failed to get email notification: {e}")
            raise

    async def get_delivery_history(self, email_id: int) -> Dict[str, Any]:
        """
        Get delivery history for an email notification.

        Args:
            email_id: Email notification ID

        Returns:
            Delivery history data
        """
        if not self.session:
            raise RuntimeError("Service not initialized. Use async context manager.")

        try:
            async with self.session.get(
                f"{self.base_url}/api/notifications/email/{email_id}/delivery"
            ) as response:
                if response.status == 200:
                    return await response.json()
                elif response.status == 404:
                    raise ValueError("Email notification not found")
                else:
                    error_text = await response.text()
                    logger.error(
                        f"Failed to get delivery history: {response.status} - {error_text}"
                    )
                    raise aiohttp.ClientError(
                        f"Failed to get delivery history: {response.status}"
                    )

        except aiohttp.ClientError as e:
            logger.error(f"Failed to get delivery history: {e}")
            raise

    async def create_email_template(self, template: EmailTemplate) -> Dict[str, Any]:
        """
        Create an email template.

        Args:
            template: Email template data

        Returns:
            Template creation response
        """
        if not self.session:
            raise RuntimeError("Service not initialized. Use async context manager.")

        payload = {
            "name": template.name,
            "subject": template.subject,
            "is_active": template.is_active,
        }

        if template.body:
            payload["body"] = template.body

        if template.html_body:
            payload["html_body"] = template.html_body

        if template.variables:
            payload["variables"] = template.variables

        try:
            async with self.session.post(
                f"{self.base_url}/api/notifications/email/templates",
                json=payload,
                headers={"Content-Type": "application/json"},
            ) as response:
                if response.status == 201:
                    return await response.json()
                else:
                    error_text = await response.text()
                    logger.error(
                        f"Failed to create email template: {response.status} - {error_text}"
                    )
                    raise aiohttp.ClientError(
                        f"Failed to create email template: {response.status}"
                    )

        except aiohttp.ClientError as e:
            logger.error(f"Failed to create email template: {e}")
            raise

    async def get_email_templates(
        self, active_only: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Get email templates.

        Args:
            active_only: Only return active templates

        Returns:
            List of email templates
        """
        if not self.session:
            raise RuntimeError("Service not initialized. Use async context manager.")

        params = {"active": str(active_only).lower()} if active_only else {}

        try:
            async with self.session.get(
                f"{self.base_url}/api/notifications/email/templates", params=params
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("templates", [])
                else:
                    error_text = await response.text()
                    logger.error(
                        f"Failed to get email templates: {response.status} - {error_text}"
                    )
                    raise aiohttp.ClientError(
                        f"Failed to get email templates: {response.status}"
                    )

        except aiohttp.ClientError as e:
            logger.error(f"Failed to get email templates: {e}")
            raise

    async def update_email_template(
        self, template_id: int, template: EmailTemplate
    ) -> Dict[str, Any]:
        """
        Update an email template.

        Args:
            template_id: Template ID to update
            template: Updated template data

        Returns:
            Update response
        """
        if not self.session:
            raise RuntimeError("Service not initialized. Use async context manager.")

        payload = {
            "name": template.name,
            "subject": template.subject,
            "is_active": template.is_active,
        }

        if template.body:
            payload["body"] = template.body

        if template.html_body:
            payload["html_body"] = template.html_body

        if template.variables:
            payload["variables"] = template.variables

        try:
            async with self.session.put(
                f"{self.base_url}/api/notifications/email/templates/{template_id}",
                json=payload,
                headers={"Content-Type": "application/json"},
            ) as response:
                if response.status == 200:
                    return await response.json()
                elif response.status == 404:
                    raise ValueError("Email template not found")
                else:
                    error_text = await response.text()
                    logger.error(
                        f"Failed to update email template: {response.status} - {error_text}"
                    )
                    raise aiohttp.ClientError(
                        f"Failed to update email template: {response.status}"
                    )

        except aiohttp.ClientError as e:
            logger.error(f"Failed to update email template: {e}")
            raise

    async def delete_email_template(self, template_id: int) -> Dict[str, Any]:
        """
        Delete an email template.

        Args:
            template_id: Template ID to delete

        Returns:
            Delete response
        """
        if not self.session:
            raise RuntimeError("Service not initialized. Use async context manager.")

        try:
            async with self.session.delete(
                f"{self.base_url}/api/notifications/email/templates/{template_id}"
            ) as response:
                if response.status == 200:
                    return await response.json()
                elif response.status == 404:
                    raise ValueError("Email template not found")
                elif response.status == 409:
                    raise ValueError("Cannot delete template that is in use")
                else:
                    error_text = await response.text()
                    logger.error(
                        f"Failed to delete email template: {response.status} - {error_text}"
                    )
                    raise aiohttp.ClientError(
                        f"Failed to delete email template: {response.status}"
                    )

        except aiohttp.ClientError as e:
            logger.error(f"Failed to delete email template: {e}")
            raise

    async def get_email_statistics(
        self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get email delivery statistics.

        Args:
            start_date: Start date for statistics
            end_date: End date for statistics

        Returns:
            Email statistics data
        """
        if not self.session:
            raise RuntimeError("Service not initialized. Use async context manager.")

        params = {}

        if start_date:
            params["start_date"] = start_date.strftime("%Y-%m-%d")

        if end_date:
            params["end_date"] = end_date.strftime("%Y-%m-%d")

        try:
            async with self.session.get(
                f"{self.base_url}/api/notifications/email/statistics", params=params
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_text = await response.text()
                    logger.error(
                        f"Failed to get email statistics: {response.status} - {error_text}"
                    )
                    raise aiohttp.ClientError(
                        f"Failed to get email statistics: {response.status}"
                    )

        except aiohttp.ClientError as e:
            logger.error(f"Failed to get email statistics: {e}")
            raise

    async def test_email_config(self, test_email: str) -> Dict[str, Any]:
        """
        Test email configuration by sending a test email.

        Args:
            test_email: Email address to send test to

        Returns:
            Test response
        """
        if not self.session:
            raise RuntimeError("Service not initialized. Use async context manager.")

        if not self._validate_email(test_email):
            raise ValueError("Invalid test email address")

        payload = {
            "to": test_email,
            "subject": "Test Email from Arxos System",
            "body": "This is a test email to verify your email configuration.",
        }

        try:
            async with self.session.post(
                f"{self.base_url}/api/notifications/email/config/test",
                json=payload,
                headers={"Content-Type": "application/json"},
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_text = await response.text()
                    logger.error(
                        f"Failed to test email config: {response.status} - {error_text}"
                    )
                    raise aiohttp.ClientError(
                        f"Failed to test email config: {response.status}"
                    )

        except aiohttp.ClientError as e:
            logger.error(f"Failed to test email config: {e}")
            raise


# Convenience functions for synchronous usage
def send_email_sync(
    request: EmailRequest, base_url: str = "http://localhost:8080", timeout: int = 30
) -> EmailResponse:
    """
    Send email synchronously.

    Args:
        request: Email request
        base_url: Base URL of the Go email service
        timeout: Request timeout in seconds

    Returns:
        Email response
    """

    async def _send():
        async with EmailIntegrationService(base_url, timeout) as service:
            return await service.send_email(request)

    return asyncio.run(_send())


def get_email_notifications_sync(
    page: int = 1,
    limit: int = 20,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    base_url: str = "http://localhost:8080",
    timeout: int = 30,
) -> Dict[str, Any]:
    """
    Get email notifications synchronously.

    Args:
        page: Page number
        limit: Number of items per page
        status: Filter by status
        priority: Filter by priority
        base_url: Base URL of the Go email service
        timeout: Request timeout in seconds

    Returns:
        Email notifications data
    """

    async def _get():
        async with EmailIntegrationService(base_url, timeout) as service:
            return await service.get_email_notifications(page, limit, status, priority)

    return asyncio.run(_get())


def get_email_statistics_sync(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    base_url: str = "http://localhost:8080",
    timeout: int = 30,
) -> Dict[str, Any]:
    """
    Get email statistics synchronously.

    Args:
        start_date: Start date for statistics
        end_date: End date for statistics
        base_url: Base URL of the Go email service
        timeout: Request timeout in seconds

    Returns:
        Email statistics data
    """

    async def _get():
        async with EmailIntegrationService(base_url, timeout) as service:
            return await service.get_email_statistics(start_date, end_date)

    return asyncio.run(_get())
