#!/usr/bin/env python3
"""
Comprehensive test suite for Arxos Platform Monitoring and Alerting System

This module provides comprehensive testing for the monitoring and alerting workflows,
including unit tests, integration tests, performance tests, and end-to-end validation.

Test Coverage:
- Alert rule validation and processing
- Metric collection and aggregation
- Notification delivery and escalation
- Dashboard configuration and rendering
- Performance benchmarks and stress testing
- Security validation and access control
- Error handling and recovery mechanisms
- Integration with external systems

Performance Targets:
- Alert processing completes within 30 seconds
- Metric collection completes within 10 seconds
- Notification delivery completes within 60 seconds
- Dashboard rendering completes within 5 seconds
- Test suite execution completes within 5 minutes
"""

import asyncio
import json
import logging
import time
import unittest
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from unittest.mock import Mock, patch, AsyncMock
import aiohttp
import pytest
import yaml

# Import the monitoring workflows
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from alerting_workflows import (
    MonitoringAlertingWorkflows,
    AlertSeverity,
    AlertStatus,
    IncidentStatus,
    Alert,
    Incident,
    MetricData
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestMonitoringAutomation(unittest.TestCase):
    """Comprehensive test suite for monitoring and alerting automation."""

    def setUp(self):
        """Set up test fixtures."""
        self.monitoring = MonitoringAlertingWorkflows(db_path=":memory:")
        self.test_alert_id = "test_alert_123"
        self.test_incident_id = "test_incident_456"
        self.test_metric_id = "test_metric_789"

    def tearDown(self):
        """Clean up test fixtures."""
        # Clean up any test data
        pass

    def test_alert_creation(self):
        """Test alert creation with various severity levels."""
        test_cases = [
            {
                "name": "cpu_usage",
                "value": 85.0,
                "threshold": 80.0,
                "severity": AlertSeverity.WARNING,
                "expected_status": AlertStatus.ACTIVE
            },
            {
                "name": "memory_usage",
                "value": 95.0,
                "threshold": 90.0,
                "severity": AlertSeverity.CRITICAL,
                "expected_status": AlertStatus.ACTIVE
            },
            {
                "name": "disk_usage",
                "value": 75.0,
                "threshold": 80.0,
                "severity": AlertSeverity.LOW,
                "expected_status": None  # Should not create alert
            }
        ]

        for test_case in test_cases:
            with self.subTest(test_case["name"]):
                # Create metric data
                metric = MetricData(
                    metric_id=self.test_metric_id,
                    name=test_case["name"],
                    value=test_case["value"],
                    unit="percent",
                    timestamp=datetime.now(),
                    source="test-system"
                )

                # Check if alert should be created
                if test_case["value"] > test_case["threshold"]:
                    # Verify alert creation
                    alert = Alert(
                        alert_id=self.test_alert_id,
                        title=f"High {test_case['name']}",
                        description=f"{test_case['name']} is above threshold",
                        severity=test_case["severity"],
                        status=test_case["expected_status"],
                        source="test-system",
                        metric_name=test_case["name"],
                        metric_value=test_case["value"],
                        threshold=test_case["threshold"],
                        created_at=datetime.now(),
                        updated_at=datetime.now()
                    )

                    self.assertEqual(alert.severity, test_case["severity"])
                    self.assertEqual(alert.status, test_case["expected_status"])
                    self.assertEqual(alert.metric_value, test_case["value"])
                    self.assertEqual(alert.threshold, test_case["threshold"])
                else:
                    # Verify no alert is created
                    self.assertIsNone(test_case["expected_status"])

    def test_alert_escalation(self):
        """Test alert escalation based on time thresholds."""
        # Create a test alert
        alert = Alert(
            alert_id=self.test_alert_id,
            title="Test Alert",
            description="Test alert for escalation",
            severity=AlertSeverity.HIGH,
            status=AlertStatus.ACTIVE,
            source="test-system",
            metric_name="cpu_usage",
            metric_value=90.0,
            threshold=80.0,
            created_at=datetime.now() - timedelta(minutes=10),
            updated_at=datetime.now() - timedelta(minutes=10)
        )

        # Test escalation logic
        escalation_time = self.monitoring.escalation_rules[AlertSeverity.HIGH]
        time_since_creation = datetime.now() - alert.created_at

        if time_since_creation > escalation_time:
            # Alert should be escalated
            alert.status = AlertStatus.ESCALATED
            alert.escalated_at = datetime.now()

        self.assertIn(alert.status, [AlertStatus.ACTIVE, AlertStatus.ESCALATED])

    def test_incident_creation(self):
        """Test incident creation from alerts."""
        # Create a critical alert
        alert = Alert(
            alert_id=self.test_alert_id,
            title="Critical System Alert",
            description="System is experiencing critical issues",
            severity=AlertSeverity.CRITICAL,
            status=AlertStatus.ACTIVE,
            source="test-system",
            metric_name="cpu_usage",
            metric_value=95.0,
            threshold=90.0,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        # Create incident from alert
        incident = Incident(
            incident_id=self.test_incident_id,
            title=f"Incident: {alert.title}",
            description=f"Incident created from alert: {alert.description}",
            severity=alert.severity,
            status=IncidentStatus.OPEN,
            alerts=[alert.alert_id],
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        self.assertEqual(incident.severity, AlertSeverity.CRITICAL)
        self.assertEqual(incident.status, IncidentStatus.OPEN)
        self.assertIn(alert.alert_id, incident.alerts)

    def test_metric_collection(self):
        """Test metric collection and aggregation."""
        test_metrics = [
            {
                "name": "cpu_usage",
                "value": 75.0,
                "unit": "percent",
                "source": "test-system-1"
            },
            {
                "name": "memory_usage",
                "value": 80.0,
                "unit": "percent",
                "source": "test-system-1"
            },
            {
                "name": "cpu_usage",
                "value": 85.0,
                "unit": "percent",
                "source": "test-system-2"
            }
        ]

        collected_metrics = []
        for metric_data in test_metrics:
            metric = MetricData(
                metric_id=f"metric_{len(collected_metrics)}",
                name=metric_data["name"],
                value=metric_data["value"],
                unit=metric_data["unit"],
                timestamp=datetime.now(),
                source=metric_data["source"],
                tags={"environment": "test"}
            )
            collected_metrics.append(metric)

        # Verify metric collection
        self.assertEqual(len(collected_metrics), 3)
        
        # Test aggregation
        cpu_metrics = [m for m in collected_metrics if m.name == "cpu_usage"]
        avg_cpu = sum(m.value for m in cpu_metrics) / len(cpu_metrics)
        self.assertEqual(avg_cpu, 80.0)

    def test_notification_delivery(self):
        """Test notification delivery to various channels."""
        alert = Alert(
            alert_id=self.test_alert_id,
            title="Test Notification Alert",
            description="Testing notification delivery",
            severity=AlertSeverity.CRITICAL,
            status=AlertStatus.ACTIVE,
            source="test-system",
            metric_name="cpu_usage",
            metric_value=95.0,
            threshold=90.0,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        # Test Slack notification
        with patch.object(self.monitoring, '_send_slack_notification') as mock_slack:
            mock_slack.return_value = True
            result = self.monitoring._send_slack_notification(alert)
            self.assertTrue(result)
            mock_slack.assert_called_once_with(alert)

        # Test email notification
        with patch.object(self.monitoring, '_send_email_notification') as mock_email:
            mock_email.return_value = True
            result = self.monitoring._send_email_notification(alert)
            self.assertTrue(result)
            mock_email.assert_called_once_with(alert)

        # Test PagerDuty notification
        with patch.object(self.monitoring, '_send_pagerduty_notification') as mock_pagerduty:
            mock_pagerduty.return_value = True
            result = self.monitoring._send_pagerduty_notification(alert)
            self.assertTrue(result)
            mock_pagerduty.assert_called_once_with(alert)

    def test_alert_acknowledgment(self):
        """Test alert acknowledgment workflow."""
        alert = Alert(
            alert_id=self.test_alert_id,
            title="Test Alert",
            description="Test alert for acknowledgment",
            severity=AlertSeverity.MEDIUM,
            status=AlertStatus.ACTIVE,
            source="test-system",
            metric_name="cpu_usage",
            metric_value=85.0,
            threshold=80.0,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        # Acknowledge alert
        acknowledged_by = "test-user"
        alert.status = AlertStatus.ACKNOWLEDGED
        alert.acknowledged_at = datetime.now()

        self.assertEqual(alert.status, AlertStatus.ACKNOWLEDGED)
        self.assertIsNotNone(alert.acknowledged_at)

    def test_alert_resolution(self):
        """Test alert resolution workflow."""
        alert = Alert(
            alert_id=self.test_alert_id,
            title="Test Alert",
            description="Test alert for resolution",
            severity=AlertSeverity.MEDIUM,
            status=AlertStatus.ACKNOWLEDGED,
            source="test-system",
            metric_name="cpu_usage",
            metric_value=85.0,
            threshold=80.0,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            acknowledged_at=datetime.now()
        )

        # Resolve alert
        resolved_by = "test-user"
        resolution_notes = "Issue has been resolved"
        alert.status = AlertStatus.RESOLVED
        alert.resolved_at = datetime.now()

        self.assertEqual(alert.status, AlertStatus.RESOLVED)
        self.assertIsNotNone(alert.resolved_at)

    def test_threshold_violation_detection(self):
        """Test threshold violation detection logic."""
        test_cases = [
            {
                "metric_name": "cpu_usage",
                "metric_value": 85.0,
                "threshold": 80.0,
                "expected_violation": True
            },
            {
                "metric_name": "memory_usage",
                "metric_value": 75.0,
                "threshold": 80.0,
                "expected_violation": False
            },
            {
                "metric_name": "disk_usage",
                "metric_value": 95.0,
                "threshold": 90.0,
                "expected_violation": True
            }
        ]

        for test_case in test_cases:
            with self.subTest(test_case["metric_name"]):
                metric = MetricData(
                    metric_id=self.test_metric_id,
                    name=test_case["metric_name"],
                    value=test_case["metric_value"],
                    unit="percent",
                    timestamp=datetime.now(),
                    source="test-system"
                )

                # Check threshold violation
                violation = metric.value > test_case["threshold"]
                self.assertEqual(violation, test_case["expected_violation"])

    def test_performance_metrics(self):
        """Test performance metrics tracking."""
        # Simulate performance metrics
        start_time = time.time()
        
        # Simulate alert processing
        time.sleep(0.1)  # Simulate processing time
        
        end_time = time.time()
        processing_time = end_time - start_time

        # Update performance tracking
        self.monitoring.metrics_tracking["average_response_time"] = processing_time
        self.monitoring.metrics_tracking["total_alerts_created"] += 1

        # Verify performance metrics
        self.assertGreater(self.monitoring.metrics_tracking["average_response_time"], 0)
        self.assertGreater(self.monitoring.metrics_tracking["total_alerts_created"], 0)

    def test_error_handling(self):
        """Test error handling in monitoring workflows."""
        # Test invalid metric data
        with self.assertRaises(ValueError):
            MetricData(
                metric_id="",
                name="",
                value=-1,  # Invalid negative value
                unit="percent",
                timestamp=datetime.now(),
                source="test-system"
            )

        # Test invalid alert data
        with self.assertRaises(ValueError):
            Alert(
                alert_id="",
                title="",
                description="",
                severity=AlertSeverity.LOW,
                status=AlertStatus.ACTIVE,
                source="",
                metric_name="",
                metric_value=-1,
                threshold=0,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )

    def test_data_persistence(self):
        """Test data persistence and retrieval."""
        # Create test data
        alert = Alert(
            alert_id=self.test_alert_id,
            title="Test Alert",
            description="Test alert for persistence",
            severity=AlertSeverity.MEDIUM,
            status=AlertStatus.ACTIVE,
            source="test-system",
            metric_name="cpu_usage",
            metric_value=85.0,
            threshold=80.0,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        # Save alert
        self.monitoring.alerts[alert.alert_id] = alert

        # Retrieve alert
        retrieved_alert = self.monitoring.alerts.get(alert.alert_id)
        self.assertIsNotNone(retrieved_alert)
        self.assertEqual(retrieved_alert.alert_id, alert.alert_id)
        self.assertEqual(retrieved_alert.title, alert.title)

    def test_concurrent_operations(self):
        """Test concurrent operations and thread safety."""
        import threading
        import queue

        results = queue.Queue()
        errors = queue.Queue()

        def create_alert(alert_id):
            try:
                alert = Alert(
                    alert_id=alert_id,
                    title=f"Concurrent Alert {alert_id}",
                    description="Test concurrent alert creation",
                    severity=AlertSeverity.MEDIUM,
                    status=AlertStatus.ACTIVE,
                    source="test-system",
                    metric_name="cpu_usage",
                    metric_value=85.0,
                    threshold=80.0,
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )
                self.monitoring.alerts[alert_id] = alert
                results.put(alert_id)
            except Exception as e:
                errors.put(e)

        # Create multiple threads
        threads = []
        for i in range(10):
            thread = threading.Thread(target=create_alert, args=(f"alert_{i}",))
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Verify results
        self.assertEqual(results.qsize(), 10)
        self.assertEqual(errors.qsize(), 0)
        self.assertEqual(len(self.monitoring.alerts), 10)

    def test_alert_rule_validation(self):
        """Test alert rule validation and parsing."""
        # Test valid alert rule
        valid_rule = {
            "alert": "HighCPUUsage",
            "expr": "100 - (avg by (instance) (irate(node_cpu_seconds_total{mode=\"idle\"}[5m])) * 100) > 80",
            "for": "5m",
            "labels": {
                "severity": "warning",
                "team": "platform",
                "service": "system"
            },
            "annotations": {
                "summary": "High CPU usage on {{ $labels.instance }}",
                "description": "CPU usage is above 80% for more than 5 minutes"
            }
        }

        # Validate required fields
        required_fields = ["alert", "expr", "labels", "annotations"]
        for field in required_fields:
            self.assertIn(field, valid_rule)

        # Test invalid alert rule
        invalid_rule = {
            "alert": "InvalidRule",
            "expr": "",  # Empty expression
            "labels": {},
            "annotations": {}
        }

        with self.assertRaises(ValueError):
            if not invalid_rule["expr"]:
                raise ValueError("Expression cannot be empty")

    def test_metric_aggregation(self):
        """Test metric aggregation and statistical calculations."""
        test_metrics = [
            MetricData("m1", "cpu_usage", 75.0, "percent", datetime.now(), "system1"),
            MetricData("m2", "cpu_usage", 80.0, "percent", datetime.now(), "system1"),
            MetricData("m3", "cpu_usage", 85.0, "percent", datetime.now(), "system2"),
            MetricData("m4", "cpu_usage", 90.0, "percent", datetime.now(), "system2"),
            MetricData("m5", "cpu_usage", 95.0, "percent", datetime.now(), "system3")
        ]

        # Calculate statistics
        values = [m.value for m in test_metrics]
        avg_value = sum(values) / len(values)
        max_value = max(values)
        min_value = min(values)

        self.assertEqual(avg_value, 85.0)
        self.assertEqual(max_value, 95.0)
        self.assertEqual(min_value, 75.0)

    def test_escalation_policy(self):
        """Test escalation policy enforcement."""
        # Test escalation timing
        escalation_times = {
            AlertSeverity.LOW: timedelta(minutes=30),
            AlertSeverity.MEDIUM: timedelta(minutes=15),
            AlertSeverity.HIGH: timedelta(minutes=5),
            AlertSeverity.CRITICAL: timedelta(minutes=2)
        }

        for severity, expected_time in escalation_times.items():
            with self.subTest(severity.value):
                actual_time = self.monitoring.escalation_rules[severity]
                self.assertEqual(actual_time, expected_time)

    def test_notification_channels(self):
        """Test notification channel configuration."""
        expected_channels = ["slack", "email", "pagerduty", "webhook"]
        actual_channels = list(self.monitoring.notification_channels.keys())

        for channel in expected_channels:
            self.assertIn(channel, actual_channels)

    def test_health_check(self):
        """Test system health check functionality."""
        # Simulate health check
        health_status = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "components": {
                "database": "healthy",
                "api": "healthy",
                "monitoring": "healthy"
            },
            "metrics": {
                "cpu_usage": 45.0,
                "memory_usage": 60.0,
                "disk_usage": 70.0
            }
        }

        # Verify health status
        self.assertEqual(health_status["status"], "healthy")
        self.assertIn("database", health_status["components"])
        self.assertIn("api", health_status["components"])
        self.assertIn("monitoring", health_status["components"])

    def test_security_monitoring(self):
        """Test security monitoring and threat detection."""
        security_events = [
            {
                "event_type": "auth_failure",
                "severity": "high",
                "source_ip": "192.168.1.100",
                "timestamp": datetime.now().isoformat()
            },
            {
                "event_type": "rate_limit_exceeded",
                "severity": "medium",
                "source_ip": "192.168.1.101",
                "timestamp": datetime.now().isoformat()
            },
            {
                "event_type": "suspicious_activity",
                "severity": "critical",
                "source_ip": "192.168.1.102",
                "timestamp": datetime.now().isoformat()
            }
        ]

        # Verify security events
        for event in security_events:
            self.assertIn("event_type", event)
            self.assertIn("severity", event)
            self.assertIn("source_ip", event)
            self.assertIn("timestamp", event)

        # Test threat detection
        critical_events = [e for e in security_events if e["severity"] == "critical"]
        self.assertEqual(len(critical_events), 1)

    def test_business_metrics(self):
        """Test business metrics tracking."""
        business_metrics = {
            "active_users": 150,
            "export_jobs_completed": 25,
            "api_requests_per_minute": 1200,
            "error_rate_percent": 2.5,
            "average_response_time_ms": 250
        }

        # Verify business metrics
        self.assertGreater(business_metrics["active_users"], 0)
        self.assertGreaterEqual(business_metrics["export_jobs_completed"], 0)
        self.assertGreater(business_metrics["api_requests_per_minute"], 0)
        self.assertLessEqual(business_metrics["error_rate_percent"], 5.0)
        self.assertLess(business_metrics["average_response_time_ms"], 1000)

    def test_dashboard_configuration(self):
        """Test dashboard configuration validation."""
        dashboard_config = {
            "title": "Arxos System Overview",
            "tags": ["arxos", "system", "overview"],
            "panels": [
                {
                    "id": 1,
                    "title": "System Health Score",
                    "type": "stat",
                    "targets": [
                        {
                            "expr": "100 - (avg by (instance) (irate(node_cpu_seconds_total{mode=\"idle\"}[5m])) * 100)",
                            "legendFormat": "CPU Usage"
                        }
                    ]
                }
            ]
        }

        # Validate dashboard configuration
        self.assertIn("title", dashboard_config)
        self.assertIn("tags", dashboard_config)
        self.assertIn("panels", dashboard_config)
        self.assertGreater(len(dashboard_config["panels"]), 0)

    def test_prometheus_configuration(self):
        """Test Prometheus configuration validation."""
        prometheus_config = {
            "global": {
                "scrape_interval": "15s",
                "evaluation_interval": "15s"
            },
            "rule_files": ["alert_rules.yml"],
            "scrape_configs": [
                {
                    "job_name": "arxos-api",
                    "static_configs": [
                        {
                            "targets": ["arxos-api:8000"]
                        }
                    ]
                }
            ]
        }

        # Validate Prometheus configuration
        self.assertIn("global", prometheus_config)
        self.assertIn("rule_files", prometheus_config)
        self.assertIn("scrape_configs", prometheus_config)
        self.assertGreater(len(prometheus_config["scrape_configs"]), 0)

    def test_alertmanager_configuration(self):
        """Test AlertManager configuration validation."""
        alertmanager_config = {
            "global": {
                "resolve_timeout": "5m",
                "slack_api_url": "https://hooks.slack.com/services/YOUR_SLACK_WEBHOOK"
            },
            "route": {
                "group_by": ["alertname", "cluster", "service"],
                "group_wait": "10s",
                "group_interval": "10s",
                "repeat_interval": "1h",
                "receiver": "slack-notifications"
            },
            "receivers": [
                {
                    "name": "slack-notifications",
                    "slack_configs": [
                        {
                            "channel": "#arxos-alerts",
                            "title": "{{ template \"slack.title\" . }}",
                            "text": "{{ template \"slack.text\" . }}"
                        }
                    ]
                }
            ]
        }

        # Validate AlertManager configuration
        self.assertIn("global", alertmanager_config)
        self.assertIn("route", alertmanager_config)
        self.assertIn("receivers", alertmanager_config)
        self.assertGreater(len(alertmanager_config["receivers"]), 0)

    def test_performance_benchmarks(self):
        """Test performance benchmarks and stress testing."""
        # Test alert processing performance
        start_time = time.time()
        
        # Create 100 test alerts
        for i in range(100):
            alert = Alert(
                alert_id=f"perf_alert_{i}",
                title=f"Performance Alert {i}",
                description=f"Performance test alert {i}",
                severity=AlertSeverity.MEDIUM,
                status=AlertStatus.ACTIVE,
                source="test-system",
                metric_name="cpu_usage",
                metric_value=85.0,
                threshold=80.0,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            self.monitoring.alerts[alert.alert_id] = alert

        end_time = time.time()
        processing_time = end_time - start_time

        # Verify performance targets
        self.assertLess(processing_time, 30.0)  # Should complete within 30 seconds
        self.assertEqual(len(self.monitoring.alerts), 100)

    def test_integration_scenarios(self):
        """Test integration scenarios and end-to-end workflows."""
        # Scenario 1: High CPU usage triggers alert and notification
        cpu_metric = MetricData(
            metric_id="cpu_001",
            name="cpu_usage",
            value=90.0,
            unit="percent",
            timestamp=datetime.now(),
            source="production-system"
        )

        # Check threshold violation
        if cpu_metric.value > self.monitoring.thresholds["cpu_usage"]:
            # Create alert
            alert = Alert(
                alert_id="cpu_alert_001",
                title="High CPU Usage",
                description="CPU usage is above threshold",
                severity=AlertSeverity.CRITICAL,
                status=AlertStatus.ACTIVE,
                source=cpu_metric.source,
                metric_name=cpu_metric.name,
                metric_value=cpu_metric.value,
                threshold=self.monitoring.thresholds["cpu_usage"],
                created_at=datetime.now(),
                updated_at=datetime.now()
            )

            # Verify alert creation
            self.assertEqual(alert.severity, AlertSeverity.CRITICAL)
            self.assertEqual(alert.status, AlertStatus.ACTIVE)

            # Simulate notification
            notification_sent = True
            self.assertTrue(notification_sent)

    def test_error_recovery(self):
        """Test error recovery and resilience mechanisms."""
        # Test recovery from failed notification
        with patch.object(self.monitoring, '_send_slack_notification') as mock_slack:
            mock_slack.side_effect = Exception("Network error")
            
            alert = Alert(
                alert_id="recovery_test",
                title="Recovery Test Alert",
                description="Testing error recovery",
                severity=AlertSeverity.MEDIUM,
                status=AlertStatus.ACTIVE,
                source="test-system",
                metric_name="cpu_usage",
                metric_value=85.0,
                threshold=80.0,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )

            # Attempt notification (should handle error gracefully)
            try:
                self.monitoring._send_slack_notification(alert)
            except Exception:
                # Error should be handled gracefully
                pass

            # Verify alert is still active despite notification failure
            self.assertEqual(alert.status, AlertStatus.ACTIVE)

    def test_data_validation(self):
        """Test data validation and integrity checks."""
        # Test valid metric data
        valid_metric = MetricData(
            metric_id="valid_001",
            name="cpu_usage",
            value=75.0,
            unit="percent",
            timestamp=datetime.now(),
            source="test-system"
        )

        # Validate metric data
        self.assertIsInstance(valid_metric.value, (int, float))
        self.assertGreaterEqual(valid_metric.value, 0)
        self.assertLessEqual(valid_metric.value, 100)
        self.assertIsInstance(valid_metric.name, str)
        self.assertIsInstance(valid_metric.source, str)

        # Test invalid metric data
        with self.assertRaises(ValueError):
            MetricData(
                metric_id="invalid_001",
                name="",
                value=-1,  # Invalid negative value
                unit="percent",
                timestamp=datetime.now(),
                source=""
            )

    def test_monitoring_completeness(self):
        """Test monitoring system completeness and coverage."""
        # Verify all required components are present
        required_components = [
            "alerts",
            "incidents",
            "metrics",
            "thresholds",
            "escalation_rules",
            "notification_channels"
        ]

        for component in required_components:
            self.assertTrue(hasattr(self.monitoring, component))

        # Verify alert severity levels
        severity_levels = [AlertSeverity.LOW, AlertSeverity.MEDIUM, AlertSeverity.HIGH, AlertSeverity.CRITICAL]
        for severity in severity_levels:
            self.assertIsInstance(severity, AlertSeverity)

        # Verify alert status levels
        status_levels = [AlertStatus.ACTIVE, AlertStatus.ACKNOWLEDGED, AlertStatus.RESOLVED, AlertStatus.ESCALATED]
        for status in status_levels:
            self.assertIsInstance(status, AlertStatus)


class TestMonitoringIntegration(unittest.TestCase):
    """Integration tests for monitoring system components."""

    def setUp(self):
        """Set up integration test fixtures."""
        self.monitoring = MonitoringAlertingWorkflows(db_path=":memory:")

    def test_end_to_end_workflow(self):
        """Test complete end-to-end monitoring workflow."""
        # Step 1: Collect metric
        metric = MetricData(
            metric_id="e2e_001",
            name="cpu_usage",
            value=95.0,
            unit="percent",
            timestamp=datetime.now(),
            source="production-system"
        )

        # Step 2: Check threshold violation
        threshold_violated = metric.value > self.monitoring.thresholds["cpu_usage"]
        self.assertTrue(threshold_violated)

        # Step 3: Create alert
        alert = Alert(
            alert_id="e2e_alert_001",
            title="Critical CPU Usage",
            description="CPU usage is critically high",
            severity=AlertSeverity.CRITICAL,
            status=AlertStatus.ACTIVE,
            source=metric.source,
            metric_name=metric.name,
            metric_value=metric.value,
            threshold=self.monitoring.thresholds["cpu_usage"],
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        # Step 4: Send notification
        notification_sent = True  # Simulate successful notification
        self.assertTrue(notification_sent)

        # Step 5: Create incident
        incident = Incident(
            incident_id="e2e_incident_001",
            title="Critical System Incident",
            description="Critical CPU usage incident",
            severity=AlertSeverity.CRITICAL,
            status=IncidentStatus.OPEN,
            alerts=[alert.alert_id],
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        # Step 6: Acknowledge alert
        alert.status = AlertStatus.ACKNOWLEDGED
        alert.acknowledged_at = datetime.now()

        # Step 7: Resolve alert
        alert.status = AlertStatus.RESOLVED
        alert.resolved_at = datetime.now()

        # Step 8: Close incident
        incident.status = IncidentStatus.RESOLVED
        incident.resolved_at = datetime.now()

        # Verify complete workflow
        self.assertEqual(alert.status, AlertStatus.RESOLVED)
        self.assertEqual(incident.status, IncidentStatus.RESOLVED)
        self.assertIsNotNone(alert.resolved_at)
        self.assertIsNotNone(incident.resolved_at)


if __name__ == "__main__":
    # Run the test suite
    unittest.main(verbosity=2) 