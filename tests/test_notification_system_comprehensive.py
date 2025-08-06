"""
Comprehensive Test Suite for Notification System

This test suite provides comprehensive testing for all notification channels
including email, Slack, SMS, and webhook notifications with enterprise-grade features.

Author: Arxos Engineering Team
Date: 2024-12-19
Version: 1.0.0
"""

import unittest
import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Any, List
from unittest.mock import Mock, patch, AsyncMock

# Import notification services
from svgx_engine.services.notifications.email_notification_service import (
    EmailNotificationService,
    SMTPConfig,
    EmailMessage,
    EmailPriority,
    EmailStatus,
)
from svgx_engine.services.notifications.slack_notification_service import (
    SlackNotificationService,
    SlackWebhookConfig,
    SlackMessage,
    SlackMessageType,
    SlackMessageStatus,
)
from svgx_engine.services.notifications.sms_notification_service import (
    SMSNotificationService,
    SMSProviderConfig,
    SMSMessage,
    SMSProvider,
    SMSMessageStatus,
)
from svgx_engine.services.notifications.webhook_notification_service import (
    WebhookNotificationService,
    WebhookConfig,
    WebhookMessage,
    WebhookMethod,
    WebhookStatus,
)
from svgx_engine.services.notifications.notification_system import (
    UnifiedNotificationSystem,
    NotificationChannel,
    NotificationPriority,
    NotificationConfig,
    NotificationResult,
    UnifiedNotification,
)

# Configure logging for tests
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestEmailNotificationService(unittest.TestCase):
    """Test cases for Email Notification Service."""

    def setUp(self):
        """Set up test fixtures."""
        self.email_service = EmailNotificationService()
        self.smtp_config = SMTPConfig(
            host="smtp.gmail.com",
            port=587,
            username="test@arxos.com",
            password="test_password",
            use_tls=True,
            timeout=30,
            max_retries=3,
        )

    def test_email_service_initialization(self):
        """Test email service initialization."""
        self.assertIsNotNone(self.email_service)
        self.assertEqual(self.email_service.statistics["total_emails"], 0)
        self.assertEqual(self.email_service.statistics["successful_emails"], 0)
        self.assertEqual(self.email_service.statistics["failed_emails"], 0)

    def test_smtp_configuration(self):
        """Test SMTP configuration."""
        self.email_service.configure_smtp(self.smtp_config)
        self.assertEqual(self.email_service.smtp_config.host, "smtp.gmail.com")
        self.assertEqual(self.email_service.smtp_config.port, 587)
        self.assertEqual(self.email_service.smtp_config.username, "test@arxos.com")

    def test_create_email_message(self):
        """Test email message creation."""
        message_id = self.email_service.create_email_message(
            to="recipient@example.com",
            subject="Test Subject",
            body="Test Body",
            priority=EmailPriority.HIGH,
        )

        self.assertIsNotNone(message_id)
        self.assertIn(message_id, self.email_service.messages)

        message = self.email_service.messages[message_id]
        self.assertEqual(message.to, "recipient@example.com")
        self.assertEqual(message.subject, "Test Subject")
        self.assertEqual(message.body, "Test Body")
        self.assertEqual(message.priority, EmailPriority.HIGH)

    def test_create_email_template(self):
        """Test email template creation."""
        self.email_service.create_template(
            template_id="test_template",
            name="Test Template",
            subject_template="Subject: {{title}}",
            body_template="Body: {{message}}",
            html_template="<h1>{{title}}</h1><p>{{message}}</p>",
            variables=["title", "message"],
        )

        template = self.email_service.get_template("test_template")
        self.assertIsNotNone(template)
        self.assertEqual(template.name, "Test Template")
        self.assertEqual(template.subject_template, "Subject: {{title}}")
        self.assertEqual(template.variables, ["title", "message"])

    @patch("smtplib.SMTP")
    async def test_send_email_success(self, mock_smtp):
        """Test successful email sending."""
        # Configure mock SMTP
        mock_server = Mock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        # Configure service
        self.email_service.configure_smtp(self.smtp_config)

        # Send email
        result = await self.email_service.send_email(
            to="recipient@example.com", subject="Test Subject", body="Test Body"
        )

        # Verify result
        self.assertTrue(result.success)
        self.assertEqual(result.status, EmailStatus.SENT)
        self.assertIsNotNone(result.sent_at)
        self.assertEqual(self.email_service.statistics["successful_emails"], 1)

    @patch("smtplib.SMTP")
    async def test_send_email_failure(self, mock_smtp):
        """Test email sending failure."""
        # Configure mock SMTP to raise exception
        mock_smtp.side_effect = Exception("SMTP connection failed")

        # Configure service
        self.email_service.configure_smtp(self.smtp_config)

        # Send email
        result = await self.email_service.send_email(
            to="recipient@example.com", subject="Test Subject", body="Test Body"
        )

        # Verify result
        self.assertFalse(result.success)
        self.assertEqual(result.status, EmailStatus.FAILED)
        self.assertIsNotNone(result.error_message)
        self.assertEqual(self.email_service.statistics["failed_emails"], 1)

    def test_email_statistics(self):
        """Test email statistics."""
        stats = self.email_service.get_email_statistics()
        self.assertIn("total_emails", stats)
        self.assertIn("successful_emails", stats)
        self.assertIn("failed_emails", stats)
        self.assertIn("average_delivery_time", stats)

    def test_supported_priorities(self):
        """Test supported email priorities."""
        priorities = self.email_service.get_supported_priorities()
        self.assertIn(EmailPriority.LOW, priorities)
        self.assertIn(EmailPriority.NORMAL, priorities)
        self.assertIn(EmailPriority.HIGH, priorities)
        self.assertIn(EmailPriority.URGENT, priorities)


class TestSlackNotificationService(unittest.TestCase):
    """Test cases for Slack Notification Service."""

    def setUp(self):
        """Set up test fixtures."""
        self.slack_service = SlackNotificationService()
        self.webhook_config = SlackWebhookConfig(
            webhook_url="https://hooks.slack.com/services/test",
            username="Test Bot",
            icon_emoji=":test:",
            channel="#test",
            timeout=30,
            max_retries=3,
            rate_limit_delay=1,
        )

    def test_slack_service_initialization(self):
        """Test Slack service initialization."""
        self.assertIsNotNone(self.slack_service)
        self.assertEqual(self.slack_service.statistics["total_messages"], 0)
        self.assertEqual(self.slack_service.statistics["successful_messages"], 0)
        self.assertEqual(self.slack_service.statistics["failed_messages"], 0)

    def test_webhook_configuration(self):
        """Test webhook configuration."""
        self.slack_service.configure_webhook(self.webhook_config)
        self.assertEqual(
            self.slack_service.webhook_config.webhook_url,
            "https://hooks.slack.com/services/test",
        )
        self.assertEqual(self.slack_service.webhook_config.username, "Test Bot")
        self.assertEqual(self.slack_service.webhook_config.channel, "#test")

    def test_create_slack_message(self):
        """Test Slack message creation."""
        message_id = self.slack_service.create_message(
            text="Test message",
            channel="#test",
            username="Test Bot",
            icon_emoji=":test:",
        )

        self.assertIsNotNone(message_id)
        self.assertIn(message_id, self.slack_service.messages)

        message = self.slack_service.messages[message_id]
        self.assertEqual(message.text, "Test message")
        self.assertEqual(message.channel, "#test")
        self.assertEqual(message.username, "Test Bot")

    def test_create_slack_attachment(self):
        """Test Slack attachment creation."""
        attachment = self.slack_service.create_attachment(
            title="Test Title",
            text="Test Text",
            color="good",
            fields=[{"title": "Field", "value": "Value", "short": True}],
            footer="Test Footer",
        )

        self.assertEqual(attachment["title"], "Test Title")
        self.assertEqual(attachment["text"], "Test Text")
        self.assertEqual(attachment["color"], "good")
        self.assertIn("fields", attachment)
        self.assertEqual(attachment["footer"], "Test Footer")

    def test_create_slack_block_section(self):
        """Test Slack block section creation."""
        block = self.slack_service.create_block_section(
            text="Test section text",
            accessory={
                "type": "button",
                "text": {"type": "plain_text", "text": "Click me"},
            },
        )

        self.assertEqual(block["type"], "section")
        self.assertEqual(block["text"]["type"], "mrkdwn")
        self.assertEqual(block["text"]["text"], "Test section text")
        self.assertIn("accessory", block)

    @patch("aiohttp.ClientSession")
    async def test_send_slack_message_success(self, mock_session):
        """Test successful Slack message sending."""
        # Configure mock session
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.__aenter__.return_value = mock_response
        mock_response.__aexit__.return_value = None

        mock_session.return_value.__aenter__.return_value = mock_session.return_value
        mock_session.return_value.post.return_value = mock_response

        # Configure service
        self.slack_service.configure_webhook(self.webhook_config)

        # Send message
        result = await self.slack_service.send_message(
            text="Test message", channel="#test"
        )

        # Verify result
        self.assertTrue(result.success)
        self.assertEqual(result.status, SlackMessageStatus.SENT)
        self.assertIsNotNone(result.sent_at)
        self.assertEqual(self.slack_service.statistics["successful_messages"], 1)

    @patch("aiohttp.ClientSession")
    async def test_send_slack_message_failure(self, mock_session):
        """Test Slack message sending failure."""
        # Configure mock session to raise exception
        mock_session.side_effect = Exception("Network error")

        # Configure service
        self.slack_service.configure_webhook(self.webhook_config)

        # Send message
        result = await self.slack_service.send_message(
            text="Test message", channel="#test"
        )

        # Verify result
        self.assertFalse(result.success)
        self.assertEqual(result.status, SlackMessageStatus.FAILED)
        self.assertIsNotNone(result.error_message)
        self.assertEqual(self.slack_service.statistics["failed_messages"], 1)

    def test_slack_statistics(self):
        """Test Slack statistics."""
        stats = self.slack_service.get_slack_statistics()
        self.assertIn("total_messages", stats)
        self.assertIn("successful_messages", stats)
        self.assertIn("failed_messages", stats)
        self.assertIn("average_delivery_time", stats)

    def test_supported_message_types(self):
        """Test supported Slack message types."""
        message_types = self.slack_service.get_supported_message_types()
        self.assertIn(SlackMessageType.TEXT, message_types)
        self.assertIn(SlackMessageType.ATTACHMENT, message_types)
        self.assertIn(SlackMessageType.BLOCK, message_types)


class TestSMSNotificationService(unittest.TestCase):
    """Test cases for SMS Notification Service."""

    def setUp(self):
        """Set up test fixtures."""
        self.sms_service = SMSNotificationService()
        self.provider_config = SMSProviderConfig(
            provider=SMSProvider.TWILIO,
            api_key="test_account_sid",
            api_secret="test_auth_token",
            from_number="+1234567890",
            timeout=30,
            max_retries=3,
            rate_limit_delay=1,
        )

    def test_sms_service_initialization(self):
        """Test SMS service initialization."""
        self.assertIsNotNone(self.sms_service)
        self.assertEqual(self.sms_service.statistics["total_messages"], 0)
        self.assertEqual(self.sms_service.statistics["successful_messages"], 0)
        self.assertEqual(self.sms_service.statistics["failed_messages"], 0)

    def test_provider_configuration(self):
        """Test provider configuration."""
        self.sms_service.configure_provider(self.provider_config)
        self.assertEqual(self.sms_service.provider_config.provider, SMSProvider.TWILIO)
        self.assertEqual(self.sms_service.provider_config.api_key, "test_account_sid")
        self.assertEqual(self.sms_service.provider_config.from_number, "+1234567890")

    def test_create_sms_message(self):
        """Test SMS message creation."""
        message_id = self.sms_service.create_message(
            to="+1987654321", body="Test SMS message", from_number="+1234567890"
        )

        self.assertIsNotNone(message_id)
        self.assertIn(message_id, self.sms_service.messages)

        message = self.sms_service.messages[message_id]
        self.assertEqual(message.to, "+1987654321")
        self.assertEqual(message.body, "Test SMS message")
        self.assertEqual(message.from_number, "+1234567890")

    @patch("aiohttp.ClientSession")
    async def test_send_sms_twilio_success(self, mock_session):
        """Test successful SMS sending via Twilio."""
        # Configure mock session
        mock_response = AsyncMock()
        mock_response.status = 201
        mock_response.json.return_value = {"sid": "test_sid"}
        mock_response.__aenter__.return_value = mock_response
        mock_response.__aexit__.return_value = None

        mock_session.return_value.__aenter__.return_value = mock_session.return_value
        mock_session.return_value.post.return_value = mock_response

        # Configure service
        self.sms_service.configure_provider(self.provider_config)

        # Send message
        result = await self.sms_service.send_message(
            to="+1987654321", body="Test SMS message"
        )

        # Verify result
        self.assertTrue(result.success)
        self.assertEqual(result.status, SMSMessageStatus.SENT)
        self.assertIsNotNone(result.sent_at)
        self.assertEqual(self.sms_service.statistics["successful_messages"], 1)

    @patch("aiohttp.ClientSession")
    async def test_send_sms_aws_sns_success(self, mock_session):
        """Test successful SMS sending via AWS SNS."""
        # Configure mock session
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.__aenter__.return_value = mock_response
        mock_response.__aexit__.return_value = None

        mock_session.return_value.__aenter__.return_value = mock_session.return_value
        mock_session.return_value.post.return_value = mock_response

        # Configure service for AWS SNS
        aws_config = SMSProviderConfig(
            provider=SMSProvider.AWS_SNS,
            api_key="test_access_key",
            api_secret="test_secret_key",
            from_number="+1234567890",
            timeout=30,
            max_retries=3,
            rate_limit_delay=1,
        )
        self.sms_service.configure_provider(aws_config)

        # Send message
        result = await self.sms_service.send_message(
            to="+1987654321", body="Test SMS message"
        )

        # Verify result
        self.assertTrue(result.success)
        self.assertEqual(result.status, SMSMessageStatus.SENT)
        self.assertIsNotNone(result.sent_at)

    @patch("aiohttp.ClientSession")
    async def test_send_sms_custom_success(self, mock_session):
        """Test successful SMS sending via custom provider."""
        # Configure mock session
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.__aenter__.return_value = mock_response
        mock_response.__aexit__.return_value = None

        mock_session.return_value.__aenter__.return_value = mock_session.return_value
        mock_session.return_value.post.return_value = mock_response

        # Configure service for custom provider
        custom_config = SMSProviderConfig(
            provider=SMSProvider.CUSTOM,
            api_key="test_key",
            api_secret="test_secret",
            from_number="+1234567890",
            webhook_url="https://api.custom-sms.com/send",
            timeout=30,
            max_retries=3,
            rate_limit_delay=1,
        )
        self.sms_service.configure_provider(custom_config)

        # Send message
        result = await self.sms_service.send_message(
            to="+1987654321", body="Test SMS message"
        )

        # Verify result
        self.assertTrue(result.success)
        self.assertEqual(result.status, SMSMessageStatus.SENT)
        self.assertIsNotNone(result.sent_at)

    def test_sms_statistics(self):
        """Test SMS statistics."""
        stats = self.sms_service.get_sms_statistics()
        self.assertIn("total_messages", stats)
        self.assertIn("successful_messages", stats)
        self.assertIn("failed_messages", stats)
        self.assertIn("average_delivery_time", stats)

    def test_supported_providers(self):
        """Test supported SMS providers."""
        providers = self.sms_service.get_supported_providers()
        self.assertIn(SMSProvider.TWILIO, providers)
        self.assertIn(SMSProvider.AWS_SNS, providers)
        self.assertIn(SMSProvider.CUSTOM, providers)


class TestWebhookNotificationService(unittest.TestCase):
    """Test cases for Webhook Notification Service."""

    def setUp(self):
        """Set up test fixtures."""
        self.webhook_service = WebhookNotificationService()
        self.webhook_config = WebhookConfig(
            url="https://api.example.com/webhook",
            method=WebhookMethod.POST,
            headers={"Content-Type": "application/json"},
            timeout=30,
            max_retries=3,
            rate_limit_delay=1,
            auth_token="test_token",
        )

    def test_webhook_service_initialization(self):
        """Test webhook service initialization."""
        self.assertIsNotNone(self.webhook_service)
        self.assertEqual(self.webhook_service.statistics["total_webhooks"], 0)
        self.assertEqual(self.webhook_service.statistics["successful_webhooks"], 0)
        self.assertEqual(self.webhook_service.statistics["failed_webhooks"], 0)

    def test_webhook_configuration(self):
        """Test webhook configuration."""
        self.webhook_service.configure_webhook(self.webhook_config)
        self.assertEqual(
            self.webhook_service.webhook_config.url, "https://api.example.com/webhook"
        )
        self.assertEqual(self.webhook_service.webhook_config.method, WebhookMethod.POST)
        self.assertEqual(self.webhook_service.webhook_config.auth_token, "test_token")

    def test_create_webhook_message(self):
        """Test webhook message creation."""
        payload = {"message": "Test webhook", "timestamp": "2024-12-19T10:00:00Z"}
        message_id = self.webhook_service.create_webhook_message(
            url="https://api.example.com/webhook",
            payload=payload,
            method=WebhookMethod.POST,
            headers={"Content-Type": "application/json"},
        )

        self.assertIsNotNone(message_id)
        self.assertIn(message_id, self.webhook_service.messages)

        message = self.webhook_service.messages[message_id]
        self.assertEqual(message.url, "https://api.example.com/webhook")
        self.assertEqual(message.method, WebhookMethod.POST)
        self.assertEqual(message.payload, payload)

    def test_create_notification_payload(self):
        """Test notification payload creation."""
        payload = self.webhook_service.create_notification_payload(
            title="Test Title",
            message="Test Message",
            priority="high",
            timestamp=datetime.now(),
        )

        self.assertEqual(payload["title"], "Test Title")
        self.assertEqual(payload["message"], "Test Message")
        self.assertEqual(payload["priority"], "high")
        self.assertIn("timestamp", payload)
        self.assertEqual(payload["source"], "arxos")
        self.assertEqual(payload["version"], "1.0")

    @patch("aiohttp.ClientSession")
    async def test_send_webhook_post_success(self, mock_session):
        """Test successful webhook sending via POST."""
        # Configure mock session
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.__aenter__.return_value = mock_response
        mock_response.__aexit__.return_value = None

        mock_session.return_value.__aenter__.return_value = mock_session.return_value
        mock_session.return_value.post.return_value = mock_response

        # Configure service
        self.webhook_service.configure_webhook(self.webhook_config)

        # Send webhook
        payload = {"message": "Test webhook"}
        result = await self.webhook_service.send_webhook(
            url="https://api.example.com/webhook",
            payload=payload,
            method=WebhookMethod.POST,
        )

        # Verify result
        self.assertTrue(result.success)
        self.assertEqual(result.status, WebhookStatus.SENT)
        self.assertIsNotNone(result.sent_at)
        self.assertEqual(self.webhook_service.statistics["successful_webhooks"], 1)

    @patch("aiohttp.ClientSession")
    async def test_send_webhook_get_success(self, mock_session):
        """Test successful webhook sending via GET."""
        # Configure mock session
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.__aenter__.return_value = mock_response
        mock_response.__aexit__.return_value = None

        mock_session.return_value.__aenter__.return_value = mock_session.return_value
        mock_session.return_value.get.return_value = mock_response

        # Configure service
        self.webhook_service.configure_webhook(self.webhook_config)

        # Send webhook
        payload = {"message": "Test webhook"}
        result = await self.webhook_service.send_webhook(
            url="https://api.example.com/webhook",
            payload=payload,
            method=WebhookMethod.GET,
        )

        # Verify result
        self.assertTrue(result.success)
        self.assertEqual(result.status, WebhookStatus.SENT)
        self.assertIsNotNone(result.sent_at)

    @patch("aiohttp.ClientSession")
    async def test_send_webhook_failure(self, mock_session):
        """Test webhook sending failure."""
        # Configure mock session to raise exception
        mock_session.side_effect = Exception("Network error")

        # Configure service
        self.webhook_service.configure_webhook(self.webhook_config)

        # Send webhook
        payload = {"message": "Test webhook"}
        result = await self.webhook_service.send_webhook(
            url="https://api.example.com/webhook",
            payload=payload,
            method=WebhookMethod.POST,
        )

        # Verify result
        self.assertFalse(result.success)
        self.assertEqual(result.status, WebhookStatus.FAILED)
        self.assertIsNotNone(result.error_message)
        self.assertEqual(self.webhook_service.statistics["failed_webhooks"], 1)

    def test_webhook_statistics(self):
        """Test webhook statistics."""
        stats = self.webhook_service.get_webhook_statistics()
        self.assertIn("total_webhooks", stats)
        self.assertIn("successful_webhooks", stats)
        self.assertIn("failed_webhooks", stats)
        self.assertIn("average_delivery_time", stats)

    def test_supported_methods(self):
        """Test supported webhook HTTP methods."""
        methods = self.webhook_service.get_supported_methods()
        self.assertIn(WebhookMethod.GET, methods)
        self.assertIn(WebhookMethod.POST, methods)
        self.assertIn(WebhookMethod.PUT, methods)
        self.assertIn(WebhookMethod.PATCH, methods)


class TestUnifiedNotificationSystem(unittest.TestCase):
    """Test cases for Unified Notification System."""

    def setUp(self):
        """Set up test fixtures."""
        self.unified_system = UnifiedNotificationSystem()

    def test_unified_system_initialization(self):
        """Test unified system initialization."""
        self.assertIsNotNone(self.unified_system)
        self.assertEqual(self.unified_system.statistics["total_notifications"], 0)
        self.assertEqual(self.unified_system.statistics["successful_notifications"], 0)
        self.assertEqual(self.unified_system.statistics["failed_notifications"], 0)

    def test_create_notification(self):
        """Test notification creation."""
        notification = self.unified_system.create_notification(
            title="Test Title",
            message="Test Message",
            channels=[NotificationChannel.EMAIL, NotificationChannel.SLACK],
            priority=NotificationPriority.HIGH,
            template_data={"key": "value"},
        )

        self.assertIsNotNone(notification)
        self.assertEqual(notification.title, "Test Title")
        self.assertEqual(notification.message, "Test Message")
        self.assertEqual(len(notification.channels), 2)
        self.assertEqual(notification.priority, NotificationPriority.HIGH)
        self.assertEqual(notification.template_data["key"], "value")

    @patch.object(UnifiedNotificationSystem, "_send_email")
    @patch.object(UnifiedNotificationSystem, "_send_slack")
    async def test_send_notification_success(self, mock_send_slack, mock_send_email):
        """Test successful notification sending."""
        # Configure mocks
        mock_send_email.return_value = NotificationResult(
            success=True,
            notification_id="test_id",
            channel=NotificationChannel.EMAIL,
            status=NotificationStatus.SENT,
            sent_at=datetime.now(),
        )
        mock_send_slack.return_value = NotificationResult(
            success=True,
            notification_id="test_id",
            channel=NotificationChannel.SLACK,
            status=NotificationStatus.SENT,
            sent_at=datetime.now(),
        )

        # Create and send notification
        notification = self.unified_system.create_notification(
            title="Test Title",
            message="Test Message",
            channels=[NotificationChannel.EMAIL, NotificationChannel.SLACK],
            priority=NotificationPriority.HIGH,
        )

        results = await self.unified_system.send_notification(
            notification.notification_id
        )

        # Verify results
        self.assertEqual(len(results), 2)
        self.assertTrue(all(result.success for result in results))
        self.assertEqual(self.unified_system.statistics["successful_notifications"], 2)

    def test_unified_statistics(self):
        """Test unified notification statistics."""
        stats = self.unified_system.get_statistics()
        self.assertIn("total_notifications", stats)
        self.assertIn("successful_notifications", stats)
        self.assertIn("failed_notifications", stats)
        self.assertIn("channel_usage", stats)
        self.assertIn("priority_usage", stats)


class TestNotificationSystemIntegration(unittest.TestCase):
    """Integration tests for the complete notification system."""

    def setUp(self):
        """Set up test fixtures."""
        self.email_service = EmailNotificationService()
        self.slack_service = SlackNotificationService()
        self.sms_service = SMSNotificationService()
        self.webhook_service = WebhookNotificationService()
        self.unified_system = UnifiedNotificationSystem()

    def test_service_integration(self):
        """Test integration between all notification services."""
        # Configure all services
        smtp_config = SMTPConfig(
            host="smtp.gmail.com",
            port=587,
            username="test@arxos.com",
            password="test_password",
            use_tls=True,
        )
        self.email_service.configure_smtp(smtp_config)

        webhook_config = SlackWebhookConfig(
            webhook_url="https://hooks.slack.com/services/test",
            username="Test Bot",
            channel="#test",
        )
        self.slack_service.configure_webhook(webhook_config)

        provider_config = SMSProviderConfig(
            provider=SMSProvider.TWILIO,
            api_key="test_sid",
            api_secret="test_token",
            from_number="+1234567890",
        )
        self.sms_service.configure_provider(provider_config)

        webhook_config_webhook = WebhookConfig(
            url="https://api.example.com/webhook", method=WebhookMethod.POST
        )
        self.webhook_service.configure_webhook(webhook_config_webhook)

        # Verify all services are configured
        self.assertIsNotNone(self.email_service.smtp_config)
        self.assertIsNotNone(self.slack_service.webhook_config)
        self.assertIsNotNone(self.sms_service.provider_config)
        self.assertIsNotNone(self.webhook_service.webhook_config)

    def test_notification_workflow(self):
        """Test complete notification workflow."""
        # Create notification
        notification = self.unified_system.create_notification(
            title="Integration Test",
            message="This is an integration test",
            channels=[NotificationChannel.EMAIL, NotificationChannel.SLACK],
            priority=NotificationPriority.NORMAL,
        )

        # Verify notification creation
        self.assertIsNotNone(notification)
        self.assertEqual(notification.title, "Integration Test")
        self.assertEqual(notification.message, "This is an integration test")
        self.assertEqual(len(notification.channels), 2)

        # Verify notification is stored
        self.assertIn(notification.notification_id, self.unified_system.notifications)

    def test_error_handling(self):
        """Test error handling across all services."""
        # Test email service error handling
        with self.assertRaises(ValueError):
            self.email_service.send_message_by_id("nonexistent_id")

        # Test Slack service error handling
        with self.assertRaises(ValueError):
            self.slack_service.send_message_by_id("nonexistent_id")

        # Test SMS service error handling
        with self.assertRaises(ValueError):
            self.sms_service.send_message_by_id("nonexistent_id")

        # Test webhook service error handling
        with self.assertRaises(ValueError):
            self.webhook_service.send_webhook_by_id("nonexistent_id")

    def test_statistics_aggregation(self):
        """Test statistics aggregation across all services."""
        # Create test messages in all services
        self.email_service.create_email_message(
            to="test@example.com", subject="Test", body="Test"
        )

        self.slack_service.create_message(text="Test message", channel="#test")

        self.sms_service.create_message(to="+1234567890", body="Test SMS")

        self.webhook_service.create_webhook_message(
            url="https://api.example.com/webhook", payload={"test": "data"}
        )

        # Verify statistics
        email_stats = self.email_service.get_email_statistics()
        slack_stats = self.slack_service.get_slack_statistics()
        sms_stats = self.sms_service.get_sms_statistics()
        webhook_stats = self.webhook_service.get_webhook_statistics()

        self.assertEqual(email_stats["total_emails"], 1)
        self.assertEqual(slack_stats["total_messages"], 1)
        self.assertEqual(sms_stats["total_messages"], 1)
        self.assertEqual(webhook_stats["total_webhooks"], 1)


def run_notification_tests():
    """Run all notification system tests."""
    # Create test suite
    test_suite = unittest.TestSuite()

    # Add test classes
    test_classes = [
        TestEmailNotificationService,
        TestSlackNotificationService,
        TestSMSNotificationService,
        TestWebhookNotificationService,
        TestUnifiedNotificationSystem,
        TestNotificationSystemIntegration,
    ]

    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)

    # Print summary
    print(f"\n{'='*60}")
    print(f"NOTIFICATION SYSTEM TEST SUMMARY")
    print(f"{'='*60}")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(
        f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%"
    )

    if result.failures:
        print(f"\nFAILURES:")
        for test, traceback in result.failures:
            print(f"- {test}: {traceback}")

    if result.errors:
        print(f"\nERRORS:")
        for test, traceback in result.errors:
            print(f"- {test}: {traceback}")

    return result.wasSuccessful()


if __name__ == "__main__":
    # Run tests
    success = run_notification_tests()

    # Exit with appropriate code
    exit(0 if success else 1)
