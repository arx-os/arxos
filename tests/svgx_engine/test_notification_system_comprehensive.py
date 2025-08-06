"""
Comprehensive Test Suite for SVGX Engine Notification System

This test suite covers:
- Go notification API integration
- Python notification client functionality
- Monitoring service integration
- Backward compatibility with existing Python services
- Error handling and retry logic
- Template variable substitution
- Async notification sending

Author: Arxos Engineering Team
Date: 2024-12-19
Version: 2.0.0
"""

import asyncio
import json
import time
import unittest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta
import pytest
import aiohttp
import requests

from svgx_engine.services.notifications.go_client import (
    GoNotificationClient,
    GoNotificationWrapper,
    NotificationRequest,
    NotificationResponse,
    NotificationHistoryRequest,
    NotificationStatistics,
    NotificationChannelType,
    NotificationPriority,
    NotificationType,
    NotificationStatus,
    create_go_notification_client,
    create_go_notification_wrapper,
)

from svgx_engine.services.advanced_monitoring import (
    AdvancedMonitoringService,
    MonitoringLevel,
    MetricType,
    MonitoringMetric,
    AlertRule,
    AlertEvent,
    create_advanced_monitoring_service,
)


class TestGoNotificationClient(unittest.TestCase):
    """Test suite for Go notification client"""

    def setUp(self):
        """Set up test fixtures"""
        self.client = GoNotificationClient(
            base_url="http://localhost:8080", timeout=5, max_retries=2, retry_delay=0.1
        )
        self.test_user_id = 1
        self.test_recipient_id = 2

    def test_create_notification_request(self):
        """Test creating notification requests"""
        request = self.client.create_notification_request(
            title="Test Notification",
            message="This is a test notification",
            notification_type=NotificationType.SYSTEM,
            channels=[NotificationChannelType.EMAIL],
            recipient_id=self.test_recipient_id,
            priority=NotificationPriority.NORMAL,
        )

        self.assertEqual(request.title, "Test Notification")
        self.assertEqual(request.message, "This is a test notification")
        self.assertEqual(request.type, NotificationType.SYSTEM)
        self.assertEqual(request.channels, [NotificationChannelType.EMAIL])
        self.assertEqual(request.recipient_id, self.test_recipient_id)
        self.assertEqual(request.priority, NotificationPriority.NORMAL)

    def test_create_notification_request_with_template(self):
        """Test creating notification requests with template variables"""
        template_data = {"user_name": "John Doe", "company": "Arxos"}

        request = self.client.create_notification_request(
            title="Welcome {{user_name}}",
            message="Hello {{user_name}}, welcome to {{company}}!",
            notification_type=NotificationType.USER,
            channels=[NotificationChannelType.EMAIL],
            recipient_id=self.test_recipient_id,
            template_data=template_data,
        )

        self.assertEqual(request.title, "Welcome John Doe")
        self.assertEqual(request.message, "Hello John Doe, welcome to Arxos!")
        self.assertEqual(request.template_data, template_data)

    def test_substitute_template_variables(self):
        """Test template variable substitution"""
        template = "Hello {{name}}, your order {{order_id}} is ready."
        variables = {"name": "Alice", "order_id": "12345"}

        result = self.client.substitute_template_variables(template, variables)
        expected = "Hello Alice, your order 12345 is ready."
        self.assertEqual(result, expected)

    def test_substitute_template_variables_missing_variables(self):
        """Test template variable substitution with missing variables"""
        template = "Hello {{name}}, your order {{order_id}} is ready."
        variables = {
            "name": "Alice"
            # order_id is missing
        }

        result = self.client.substitute_template_variables(template, variables)
        expected = "Hello Alice, your order {{order_id}} is ready."
        self.assertEqual(result, expected)

    @patch("requests.Session.request")
    def test_send_notification_success(self, mock_request):
        """Test successful notification sending"""
        # Mock successful response
        mock_response = Mock()
        mock_response.json.return_value = {
            "success": True,
            "notification_id": 123,
            "message": "Notification sent successfully",
            "created_at": "2024-12-19T10:00:00Z",
        }
        mock_response.raise_for_status.return_value = None
        mock_request.return_value = mock_response

        request = NotificationRequest(
            title="Test Notification",
            message="This is a test",
            type=NotificationType.SYSTEM,
            channels=[NotificationChannelType.EMAIL],
            recipient_id=self.test_recipient_id,
        )

        response = self.client.send_notification(request)

        self.assertTrue(response.success)
        self.assertEqual(response.notification_id, 123)
        self.assertEqual(response.message, "Notification sent successfully")

    @patch("requests.Session.request")
    def test_send_notification_failure(self, mock_request):
        """Test notification sending failure"""
        # Mock failed response
        mock_request.side_effect = requests.RequestException("Network error")

        request = NotificationRequest(
            title="Test Notification",
            message="This is a test",
            type=NotificationType.SYSTEM,
            channels=[NotificationChannelType.EMAIL],
            recipient_id=self.test_recipient_id,
        )

        response = self.client.send_notification(request)

        self.assertFalse(response.success)
        self.assertIsNotNone(response.error)

    @patch("requests.Session.request")
    def test_get_notification_history(self, mock_request):
        """Test getting notification history"""
        # Mock successful response
        mock_response = Mock()
        mock_response.json.return_value = {
            "notifications": [
                {
                    "id": 1,
                    "title": "Test Notification",
                    "message": "This is a test",
                    "type": "system",
                    "status": "sent",
                    "created_at": "2024-12-19T10:00:00Z",
                }
            ],
            "total": 1,
            "page": 1,
            "page_size": 20,
        }
        mock_response.raise_for_status.return_value = None
        mock_request.return_value = mock_response

        request = NotificationHistoryRequest(
            recipient_id=self.test_recipient_id, page=1, page_size=20
        )

        response = self.client.get_notification_history(request)

        self.assertIn("notifications", response)
        self.assertEqual(response["total"], 1)
        self.assertEqual(len(response["notifications"]), 1)

    @patch("requests.Session.request")
    def test_get_notification_statistics(self, mock_request):
        """Test getting notification statistics"""
        # Mock successful response
        mock_response = Mock()
        mock_response.json.return_value = {
            "total_sent": 100,
            "total_delivered": 95,
            "total_failed": 5,
            "success_rate": 95.0,
            "avg_delivery_time": 2.5,
            "period": "7d",
            "generated_at": "2024-12-19T10:00:00Z",
        }
        mock_response.raise_for_status.return_value = None
        mock_request.return_value = mock_response

        stats = self.client.get_notification_statistics(period="7d")

        self.assertIsNotNone(stats)
        self.assertEqual(stats.total_sent, 100)
        self.assertEqual(stats.total_delivered, 95)
        self.assertEqual(stats.success_rate, 95.0)

    @patch("requests.Session.request")
    def test_health_check(self, mock_request):
        """Test health check functionality"""
        # Mock successful response
        mock_response = Mock()
        mock_response.json.return_value = {
            "status": "healthy",
            "timestamp": "2024-12-19T10:00:00Z",
        }
        mock_response.raise_for_status.return_value = None
        mock_request.return_value = mock_response

        health = self.client.health_check()

        self.assertEqual(health["status"], "healthy")

    def test_send_simple_notification(self):
        """Test simple notification sending convenience method"""
        with patch.object(self.client, "send_notification") as mock_send:
            mock_send.return_value = NotificationResponse(
                success=True, notification_id=123, message="Sent successfully"
            )

            response = self.client.send_simple_notification(
                title="Simple Test",
                message="This is a simple test",
                recipient_id=self.test_recipient_id,
            )

            self.assertTrue(response.success)
            mock_send.assert_called_once()


class TestGoNotificationWrapper(unittest.TestCase):
    """Test suite for Go notification wrapper (backward compatibility)"""

    def setUp(self):
        """Set up test fixtures"""
        self.mock_client = Mock()
        self.wrapper = GoNotificationWrapper(self.mock_client)

    def test_send_email(self):
        """Test email sending via wrapper"""
        self.mock_client.send_notification.return_value = NotificationResponse(
            success=True, notification_id=123
        )

        result = self.wrapper.send_email(
            to_email="test@example.com",
            subject="Test Subject",
            body="Test Body",
            recipient_id=1,
        )

        self.assertTrue(result["success"])
        self.assertEqual(result["notification_id"], 123)
        self.mock_client.send_notification.assert_called_once()

    def test_send_slack(self):
        """Test Slack sending via wrapper"""
        self.mock_client.send_notification.return_value = NotificationResponse(
            success=True, notification_id=124
        )

        result = self.wrapper.send_slack(
            channel="#test", message="Test Slack message", recipient_id=1
        )

        self.assertTrue(result["success"])
        self.assertEqual(result["notification_id"], 124)
        self.mock_client.send_notification.assert_called_once()

    def test_send_sms(self):
        """Test SMS sending via wrapper"""
        self.mock_client.send_notification.return_value = NotificationResponse(
            success=True, notification_id=125
        )

        result = self.wrapper.send_sms(
            phone_number="+1234567890", message="Test SMS", recipient_id=1
        )

        self.assertTrue(result["success"])
        self.assertEqual(result["notification_id"], 125)
        self.mock_client.send_notification.assert_called_once()

    def test_send_webhook(self):
        """Test webhook sending via wrapper"""
        self.mock_client.send_notification.return_value = NotificationResponse(
            success=True, notification_id=126
        )

        result = self.wrapper.send_webhook(
            url="https://example.com/webhook", payload={"test": "data"}, recipient_id=1
        )

        self.assertTrue(result["success"])
        self.assertEqual(result["notification_id"], 126)
        self.mock_client.send_notification.assert_called_once()


class TestAdvancedMonitoringService(unittest.TestCase):
    """Test suite for advanced monitoring service"""

    def setUp(self):
        """Set up test fixtures"""
        self.mock_go_client = Mock()
        self.monitoring_service = AdvancedMonitoringService(
            go_notification_client=self.mock_go_client,
            monitoring_interval=1,
            alert_cooldown=60,
            enable_system_metrics=False,  # Disable for testing
            enable_custom_metrics=False,
        )

    def test_add_alert_rule(self):
        """Test adding alert rules"""
        rule = AlertRule(
            name="test_rule",
            metric_type=MetricType.CPU_USAGE,
            threshold=80.0,
            operator=">",
            duration=60,
            level=MonitoringLevel.WARNING,
            channels=[NotificationChannelType.EMAIL],
            recipients=[1, 2],
            message_template="CPU usage is {{current_value}}%",
        )

        self.monitoring_service.add_alert_rule(rule)
        self.assertIn("test_rule", self.monitoring_service.alert_rules)
        self.assertEqual(self.monitoring_service.alert_rules["test_rule"], rule)

    def test_remove_alert_rule(self):
        """Test removing alert rules"""
        rule = AlertRule(
            name="test_rule",
            metric_type=MetricType.CPU_USAGE,
            threshold=80.0,
            operator=">",
            duration=60,
            level=MonitoringLevel.WARNING,
            channels=[NotificationChannelType.EMAIL],
            recipients=[1],
            message_template="CPU usage is {{current_value}}%",
        )

        self.monitoring_service.add_alert_rule(rule)
        self.assertIn("test_rule", self.monitoring_service.alert_rules)

        self.monitoring_service.remove_alert_rule("test_rule")
        self.assertNotIn("test_rule", self.monitoring_service.alert_rules)

    def test_add_custom_metric(self):
        """Test adding custom metrics"""

        def custom_metric():
            return 42.0

        self.monitoring_service.add_custom_metric("test_metric", custom_metric)
        self.assertIn("test_metric", self.monitoring_service.custom_metrics)

    def test_remove_custom_metric(self):
        """Test removing custom metrics"""

        def custom_metric():
            return 42.0

        self.monitoring_service.add_custom_metric("test_metric", custom_metric)
        self.assertIn("test_metric", self.monitoring_service.custom_metrics)

        self.monitoring_service.remove_custom_metric("test_metric")
        self.assertNotIn("test_metric", self.monitoring_service.custom_metrics)

    def test_get_metrics_summary(self):
        """Test getting metrics summary"""
        # Add some test metrics
        metric1 = MonitoringMetric(
            name="test_metric_1",
            value=50.0,
            unit="%",
            timestamp=datetime.now(),
            metric_type=MetricType.CPU_USAGE,
        )
        metric2 = MonitoringMetric(
            name="test_metric_2",
            value=75.0,
            unit="%",
            timestamp=datetime.now(),
            metric_type=MetricType.MEMORY_USAGE,
        )

        self.monitoring_service.metrics_history = [metric1, metric2]

        summary = self.monitoring_service.get_metrics_summary()

        self.assertIn("timestamp", summary)
        self.assertIn("metrics", summary)
        self.assertEqual(summary["total_metrics"], 2)
        self.assertEqual(len(summary["metrics"]), 2)

    def test_get_alert_history(self):
        """Test getting alert history"""
        # Add some test alerts
        alert1 = AlertEvent(
            rule_name="test_rule",
            metric_name="cpu_usage",
            current_value=85.0,
            threshold=80.0,
            level=MonitoringLevel.WARNING,
            timestamp=datetime.now(),
            message="CPU usage is high",
        )
        alert2 = AlertEvent(
            rule_name="test_rule",
            metric_name="memory_usage",
            current_value=90.0,
            threshold=85.0,
            level=MonitoringLevel.ERROR,
            timestamp=datetime.now() - timedelta(hours=2),
            message="Memory usage is critical",
        )

        self.monitoring_service.alert_history = [alert1, alert2]

        # Get alerts from last hour
        history = self.monitoring_service.get_alert_history(hours=1)

        self.assertEqual(len(history), 1)  # Only alert1 should be included

    def test_health_check(self):
        """Test health check functionality"""
        # Mock Go client health check
        self.mock_go_client.health_check.return_value = {
            "status": "healthy",
            "timestamp": "2024-12-19T10:00:00Z",
        }

        health = self.monitoring_service.health_check()

        self.assertIn("status", health)
        self.assertIn("monitoring_running", health)
        self.assertIn("metrics_count", health)
        self.assertIn("alerts_count", health)
        self.assertIn("rules_count", health)
        self.assertIn("go_client_health", health)

    def test_set_thresholds(self):
        """Test setting monitoring thresholds"""
        self.monitoring_service.set_thresholds(
            cpu_threshold=90.0, memory_threshold=95.0, disk_threshold=85.0
        )

        self.assertEqual(self.monitoring_service.cpu_threshold, 90.0)
        self.assertEqual(self.monitoring_service.memory_threshold, 95.0)
        self.assertEqual(self.monitoring_service.disk_threshold, 85.0)

    def test_check_threshold_exceeded(self):
        """Test threshold checking logic"""
        metrics = [
            MonitoringMetric(
                name="cpu_usage",
                value=85.0,
                unit="%",
                timestamp=datetime.now(),
                metric_type=MetricType.CPU_USAGE,
            ),
            MonitoringMetric(
                name="cpu_usage",
                value=90.0,
                unit="%",
                timestamp=datetime.now(),
                metric_type=MetricType.CPU_USAGE,
            ),
        ]

        # Test greater than operator
        exceeded = self.monitoring_service._check_threshold_exceeded(metrics, 80.0, ">")
        self.assertTrue(exceeded)

        # Test less than operator
        exceeded = self.monitoring_service._check_threshold_exceeded(metrics, 95.0, "<")
        self.assertTrue(exceeded)

        # Test not exceeded
        exceeded = self.monitoring_service._check_threshold_exceeded(metrics, 95.0, ">")
        self.assertFalse(exceeded)


class TestNotificationIntegration(unittest.TestCase):
    """Integration tests for notification system"""

    def setUp(self):
        """Set up test fixtures"""
        self.go_client = GoNotificationClient(
            base_url="http://localhost:8080", timeout=5
        )
        self.monitoring_service = AdvancedMonitoringService(
            go_notification_client=self.go_client
        )

    @patch("requests.Session.request")
    def test_monitoring_service_with_go_notifications(self, mock_request):
        """Test monitoring service integration with Go notifications"""
        # Mock successful Go API response
        mock_response = Mock()
        mock_response.json.return_value = {
            "success": True,
            "notification_id": 123,
            "message": "Alert sent successfully",
        }
        mock_response.raise_for_status.return_value = None
        mock_request.return_value = mock_response

        # Add alert rule
        rule = AlertRule(
            name="test_alert",
            metric_type=MetricType.CPU_USAGE,
            threshold=80.0,
            operator=">",
            duration=60,
            level=MonitoringLevel.WARNING,
            channels=[NotificationChannelType.EMAIL],
            recipients=[1],
            message_template="CPU usage is {{current_value}}%",
        )
        self.monitoring_service.add_alert_rule(rule)

        # Add metric that exceeds threshold
        metric = MonitoringMetric(
            name="cpu_usage",
            value=85.0,
            unit="%",
            timestamp=datetime.now(),
            metric_type=MetricType.CPU_USAGE,
        )
        self.monitoring_service.metrics_history = [metric]

        # Trigger alert check
        self.monitoring_service._check_alert_rules()

        # Verify notification was sent
        mock_request.assert_called()
        call_args = mock_request.call_args
        self.assertEqual(call_args[0][0], "POST")
        self.assertIn("/api/notifications/send", call_args[0][1])

    def test_template_variable_substitution_integration(self):
        """Test template variable substitution in integration"""
        template_data = {
            "user_name": "Alice",
            "system_name": "SVGX Engine",
            "error_count": 5,
        }

        request = self.go_client.create_notification_request(
            title="Alert: {{system_name}} - {{error_count}} errors",
            message="Hello {{user_name}}, {{system_name}} has {{error_count}} errors.",
            notification_type=NotificationType.ALERT,
            channels=[NotificationChannelType.EMAIL, NotificationChannelType.SLACK],
            recipient_id=1,
            template_data=template_data,
        )

        expected_title = "Alert: SVGX Engine - 5 errors"
        expected_message = "Hello Alice, SVGX Engine has 5 errors."

        self.assertEqual(request.title, expected_title)
        self.assertEqual(request.message, expected_message)
        self.assertEqual(request.template_data, template_data)

    def test_multi_channel_notification_integration(self):
        """Test multi-channel notification integration"""
        request = self.go_client.create_notification_request(
            title="Multi-Channel Test",
            message="This notification should be sent to multiple channels",
            notification_type=NotificationType.ALERT,
            channels=[
                NotificationChannelType.EMAIL,
                NotificationChannelType.SLACK,
                NotificationChannelType.SMS,
            ],
            recipient_id=1,
            priority=NotificationPriority.HIGH,
        )

        self.assertEqual(len(request.channels), 3)
        self.assertIn(NotificationChannelType.EMAIL, request.channels)
        self.assertIn(NotificationChannelType.SLACK, request.channels)
        self.assertIn(NotificationChannelType.SMS, request.channels)
        self.assertEqual(request.priority, NotificationPriority.HIGH)


class TestNotificationErrorHandling(unittest.TestCase):
    """Test error handling scenarios"""

    def setUp(self):
        """Set up test fixtures"""
        self.client = GoNotificationClient(
            base_url="http://localhost:8080", timeout=1, max_retries=1, retry_delay=0.1
        )

    @patch("requests.Session.request")
    def test_network_timeout(self, mock_request):
        """Test handling of network timeouts"""
        mock_request.side_effect = requests.Timeout("Request timeout")

        request = NotificationRequest(
            title="Test",
            message="Test",
            type=NotificationType.SYSTEM,
            channels=[NotificationChannelType.EMAIL],
            recipient_id=1,
        )

        response = self.client.send_notification(request)

        self.assertFalse(response.success)
        self.assertIsNotNone(response.error)
        self.assertIn("timeout", response.error.lower())

    @patch("requests.Session.request")
    def test_server_error(self, mock_request):
        """Test handling of server errors"""
        mock_request.side_effect = requests.HTTPError("500 Internal Server Error")

        request = NotificationRequest(
            title="Test",
            message="Test",
            type=NotificationType.SYSTEM,
            channels=[NotificationChannelType.EMAIL],
            recipient_id=1,
        )

        response = self.client.send_notification(request)

        self.assertFalse(response.success)
        self.assertIsNotNone(response.error)

    def test_invalid_template_variables(self):
        """Test handling of invalid template variables"""
        template = "Hello {{name}}, your order {{order_id}} is ready."
        variables = None  # Invalid variables

        result = self.client.substitute_template_variables(template, variables)

        # Should return original template when variables are invalid
        self.assertEqual(result, template)

    def test_empty_notification_request(self):
        """Test handling of empty notification requests"""
        request = NotificationRequest(
            title="",
            message="",
            type=NotificationType.SYSTEM,
            channels=[],
            recipient_id=0,
        )

        # Should not raise an exception
        self.assertIsNotNone(request)
        self.assertEqual(request.title, "")
        self.assertEqual(request.message, "")
        self.assertEqual(len(request.channels), 0)


class TestNotificationPerformance(unittest.TestCase):
    """Performance tests for notification system"""

    def setUp(self):
        """Set up test fixtures"""
        self.client = GoNotificationClient(base_url="http://localhost:8080", timeout=5)

    def test_bulk_notification_creation(self):
        """Test creating multiple notifications efficiently"""
        start_time = time.time()

        requests = []
        for i in range(100):
            request = NotificationRequest(
                title=f"Bulk Test {i}",
                message=f"This is bulk test notification {i}",
                type=NotificationType.SYSTEM,
                channels=[NotificationChannelType.EMAIL],
                recipient_id=1,
            )
            requests.append(request)

        creation_time = time.time() - start_time

        # Should create 100 requests quickly
        self.assertLess(creation_time, 1.0)
        self.assertEqual(len(requests), 100)

    def test_template_substitution_performance(self):
        """Test template substitution performance"""
        template = "Hello {{name}}, your order {{order_id}} is ready. Total: {{total}}."
        variables = {"name": "Alice", "order_id": "12345", "total": "$99.99"}

        start_time = time.time()

        for _ in range(1000):
            result = self.client.substitute_template_variables(template, variables)

        substitution_time = time.time() - start_time

        # Should handle 1000 substitutions quickly
        self.assertLess(substitution_time, 1.0)
        self.assertEqual(
            result, "Hello Alice, your order 12345 is ready. Total: $99.99."
        )

    def test_large_template_variables(self):
        """Test performance with large template variables"""
        template = "Hello {{name}}, here is your data: {{data}}"
        variables = {"name": "User", "data": "x" * 10000}  # Large data

        start_time = time.time()

        for _ in range(100):
            result = self.client.substitute_template_variables(template, variables)

        substitution_time = time.time() - start_time

        # Should handle large variables efficiently
        self.assertLess(substitution_time, 1.0)
        self.assertIn("User", result)
        self.assertIn("x" * 10000, result)


if __name__ == "__main__":
    # Run all tests
    unittest.main(verbosity=2)
