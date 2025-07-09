"""
Unit tests for Real-Time Telemetry Integration System

Tests cover:
- Telemetry processor functionality
- Alert rule evaluation
- Data ingestion and processing
- WebSocket and HTTP server functionality
- Integration with failure detection
"""

import unittest
import tempfile
import json
import time
import asyncio
from datetime import datetime
from unittest.mock import patch, MagicMock, AsyncMock

# Add parent directory to path for imports
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from services.realtime_telemetry import (
    TelemetryProcessor, TelemetryConfig, TelemetryEvent, AlertRule,
    RealtimeTelemetryServer, create_telemetry_processor
)
from ..services.telemetry import TelemetryRecord
from ..services.analytics import ZScoreAnomalyDetector


class TestTelemetryConfig(unittest.TestCase):
    """Test TelemetryConfig class"""
    
    def test_config_creation(self):
        """Test configuration creation"""
        config = TelemetryConfig()
        
        self.assertEqual(config.buffer_size, 10000)
        self.assertEqual(config.processing_interval, 1.0)
        self.assertEqual(config.alert_threshold, 0.8)
        self.assertTrue(config.enable_websocket)
        self.assertTrue(config.enable_http)
    
    def test_custom_config(self):
        """Test custom configuration"""
        config = TelemetryConfig(
            buffer_size=5000,
            processing_interval=0.5,
            alert_threshold=0.7,
            websocket_port=9000,
            http_port=9001
        )
        
        self.assertEqual(config.buffer_size, 5000)
        self.assertEqual(config.processing_interval, 0.5)
        self.assertEqual(config.alert_threshold, 0.7)
        self.assertEqual(config.websocket_port, 9000)
        self.assertEqual(config.http_port, 9001)


class TestAlertRule(unittest.TestCase):
    """Test AlertRule class"""
    
    def test_alert_rule_creation(self):
        """Test alert rule creation"""
        rule = AlertRule(
            rule_id="test_rule",
            name="Test Rule",
            condition="threshold",
            parameters={"field": "temperature", "operator": ">", "value": 80.0},
            severity="warning",
            actions=["log_alert"]
        )
        
        self.assertEqual(rule.rule_id, "test_rule")
        self.assertEqual(rule.name, "Test Rule")
        self.assertEqual(rule.condition, "threshold")
        self.assertEqual(rule.severity, "warning")
        self.assertEqual(rule.enabled, True)
        self.assertIn("log_alert", rule.actions)


class TestTelemetryEvent(unittest.TestCase):
    """Test TelemetryEvent class"""
    
    def test_event_creation(self):
        """Test telemetry event creation"""
        record = TelemetryRecord(
            timestamp=time.time(),
            source="test_sensor",
            type="temperature",
            value=75.0
        )
        
        event = TelemetryEvent(
            record=record,
            timestamp=datetime.now(),
            source_id="test_sensor",
            event_type="telemetry"
        )
        
        self.assertEqual(event.source_id, "test_sensor")
        self.assertEqual(event.event_type, "telemetry")
        self.assertFalse(event.processed)
        self.assertEqual(event.record.value, 75.0)


class TestTelemetryProcessor(unittest.TestCase):
    """Test TelemetryProcessor class"""
    
    def setUp(self):
        """Set up test processor"""
        self.config = TelemetryConfig(
            buffer_size=1000,
            processing_interval=0.1,
            alert_threshold=0.8
        )
        self.processor = TelemetryProcessor(self.config)
    
    def test_processor_creation(self):
        """Test processor creation"""
        self.assertIsNotNone(self.processor.buffer)
        self.assertIsNotNone(self.processor.failure_detector)
        self.assertIsNotNone(self.processor.ingestor)
        self.assertFalse(self.processor.running)
    
    def test_add_alert_rule(self):
        """Test adding alert rules"""
        rule = AlertRule(
            rule_id="test_rule",
            name="Test Rule",
            condition="threshold",
            parameters={"field": "temperature", "operator": ">", "value": 80.0},
            severity="warning"
        )
        
        self.processor.add_alert_rule(rule)
        self.assertIn("test_rule", self.processor.alert_rules)
        self.assertEqual(self.processor.alert_rules["test_rule"].name, "Test Rule")
    
    def test_remove_alert_rule(self):
        """Test removing alert rules"""
        rule = AlertRule(
            rule_id="test_rule",
            name="Test Rule",
            condition="threshold",
            parameters={"field": "temperature", "operator": ">", "value": 80.0}
        )
        
        self.processor.add_alert_rule(rule)
        self.assertIn("test_rule", self.processor.alert_rules)
        
        self.processor.remove_alert_rule("test_rule")
        self.assertNotIn("test_rule", self.processor.alert_rules)
    
    def test_register_action(self):
        """Test registering action handlers"""
        def test_handler(alert):
            pass
        
        self.processor.register_action("test_action", test_handler)
        self.assertIn("test_action", self.processor.action_handlers)
    
    def test_subscribe_unsubscribe(self):
        """Test subscriber management"""
        def test_callback(data):
            pass
        
        self.processor.subscribe(test_callback)
        self.assertIn(test_callback, self.processor.subscribers)
        
        self.processor.unsubscribe(test_callback)
        self.assertNotIn(test_callback, self.processor.subscribers)
    
    def test_ingest_data(self):
        """Test data ingestion"""
        # Start processor first
        self.processor.start()
        
        data = {
            "timestamp": time.time(),
            "source": "test_sensor",
            "type": "temperature",
            "value": 75.0,
            "status": "OK"
        }
        
        self.processor.ingest_data(data)
        
        # Wait a bit for processing
        time.sleep(0.1)
        
        # Data should be in the buffer
        self.assertGreater(len(self.processor.events), 0)
        
        # Stop processor
        self.processor.stop()
    
    def test_get_dashboard_data(self):
        """Test dashboard data retrieval"""
        data = self.processor.get_dashboard_data()
        
        self.assertIn('last_update', data)
        self.assertIn('total_events', data)
        self.assertIn('active_alerts', data)
        self.assertIn('system_status', data)
    
    def test_get_alerts(self):
        """Test alert retrieval"""
        alerts = self.processor.get_alerts(limit=10)
        self.assertIsInstance(alerts, list)
    
    def test_get_patterns(self):
        """Test pattern retrieval"""
        patterns = self.processor.get_patterns(limit=10)
        self.assertIsInstance(patterns, list)
    
    def test_threshold_rule_evaluation(self):
        """Test threshold-based rule evaluation"""
        rule = AlertRule(
            rule_id="temp_rule",
            name="Temperature Rule",
            condition="threshold",
            parameters={"field": "temperature", "operator": ">", "value": 80.0},
            severity="warning"
        )
        
        # Create event with high temperature
        record = TelemetryRecord(
            timestamp=time.time(),
            source="test_sensor",
            type="temperature",
            value=85.0
        )
        
        event = TelemetryEvent(
            record=record,
            timestamp=datetime.now(),
            source_id="test_sensor",
            event_type="telemetry"
        )
        
        # Should trigger alert
        result = self.processor._evaluate_threshold_rule(rule, event)
        self.assertTrue(result)
        
        # Create event with low temperature
        record2 = TelemetryRecord(
            timestamp=time.time(),
            source="test_sensor",
            type="temperature",
            value=75.0
        )
        
        event2 = TelemetryEvent(
            record=record2,
            timestamp=datetime.now(),
            source_id="test_sensor",
            event_type="telemetry"
        )
        
        # Should not trigger alert
        result2 = self.processor._evaluate_threshold_rule(rule, event2)
        self.assertFalse(result2)
    
    def test_trend_rule_evaluation(self):
        """Test trend-based rule evaluation"""
        rule = AlertRule(
            rule_id="trend_rule",
            name="Trend Rule",
            condition="trend",
            parameters={"field": "pressure", "window": 5, "threshold": 0.1},
            severity="warning"
        )
        
        # Add some events with increasing trend
        for i in range(10):
            record = TelemetryRecord(
                timestamp=time.time(),
                source="test_sensor",
                type="pressure",
                value=100 + i * 2  # Increasing trend
            )
            
            event = TelemetryEvent(
                record=record,
                timestamp=datetime.now(),
                source_id="test_sensor",
                event_type="telemetry"
            )
            
            self.processor.events.append(event)
        
        # Test with last event
        last_event = self.processor.events[-1]
        result = self.processor._evaluate_trend_rule(rule, last_event)
        self.assertTrue(result)
    
    def test_records_to_data(self):
        """Test conversion of records to data format"""
        records = [
            TelemetryRecord(timestamp=time.time(), source="sensor1", type="temperature", value=75.0),
            TelemetryRecord(timestamp=time.time(), source="sensor1", type="temperature", value=76.0),
            TelemetryRecord(timestamp=time.time(), source="sensor1", type="pressure", value=100.0),
            TelemetryRecord(timestamp=time.time(), source="sensor1", type="pressure", value=101.0)
        ]
        
        data = self.processor._records_to_data(records)
        
        self.assertIn('temperature', data)
        self.assertIn('pressure', data)
        self.assertEqual(len(data['temperature']), 2)
        self.assertEqual(len(data['pressure']), 2)
    
    def test_start_stop(self):
        """Test processor start and stop"""
        self.assertFalse(self.processor.running)
        
        # Start processor
        self.processor.start()
        self.assertTrue(self.processor.running)
        
        # Stop processor
        self.processor.stop()
        self.assertFalse(self.processor.running)

    def test_analytics_integration(self):
        """Test analytics integration in telemetry processor"""
        self.processor.start()
        # Ingest temperature data: 14 normal, 1 strong outlier
        for i in range(15):
            data = {
                "timestamp": time.time(),
                "source": "test_sensor",
                "type": "temperature",
                "value": 70.0 if i < 14 else 1000.0,  # Only last is outlier
                "status": "OK"
            }
            self.processor.ingest_data(data)
        time.sleep(0.2)
        # Print the values used for analytics
        values = []
        for events in self.processor.data_history.values():
            for rec in events:
                if rec.type == 'temperature':
                    values.append(rec.value)
        print("VALUES FOR ANOMALY DETECTION:", values)
        # Force analytics with high sensitivity
        self.processor._run_analytics('temperature', sensitivity=1.0)
        analytics = self.processor.get_analytics_results('temperature')
        print("ANOMALY RESULTS:", analytics.get('anomalies', {}))
        self.assertIn('anomalies', analytics)
        self.assertIn('forecasts', analytics)
        found = False
        for name, anom_list in analytics['anomalies'].items():
            if anom_list[-1]:
                found = True
        self.assertTrue(found)
        self.assertTrue(all(len(forecast) == 5 for forecast in analytics['forecasts'].values()))
        self.processor.stop()


class TestRealtimeTelemetryServer(unittest.TestCase):
    """Test RealtimeTelemetryServer class"""
    
    def setUp(self):
        """Set up test server"""
        self.config = TelemetryConfig(
            websocket_port=8766,
            http_port=8082
        )
        self.processor = TelemetryProcessor(self.config)
        self.server = RealtimeTelemetryServer(self.processor, self.config)
    
    def test_server_creation(self):
        """Test server creation"""
        self.assertIsNotNone(self.server.processor)
        self.assertIsNotNone(self.server.config)
        self.assertIsNotNone(self.server.http_app)
    
    def test_route_setup(self):
        """Test HTTP route setup"""
        routes = [route.resource.canonical for route in self.server.http_app.router.routes()]
        
        self.assertIn('/telemetry', routes)
        self.assertIn('/dashboard', routes)
        self.assertIn('/alerts', routes)
        self.assertIn('/patterns', routes)
        self.assertIn('/health', routes)
    
    def test_handle_telemetry(self):
        """Test telemetry handling"""
        # Create mock request
        request = MagicMock()
        request.json = AsyncMock(return_value={
            "timestamp": time.time(),
            "source": "test_sensor",
            "type": "temperature",
            "value": 75.0
        })
        
        # Test the handler
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            response = loop.run_until_complete(self.server.handle_telemetry(request))
            self.assertIsNotNone(response)
        finally:
            loop.close()
    
    def test_handle_dashboard(self):
        """Test dashboard handling"""
        request = MagicMock()
        
        # Test the handler
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            response = loop.run_until_complete(self.server.handle_dashboard(request))
            self.assertIsNotNone(response)
        finally:
            loop.close()
    
    def test_handle_alerts(self):
        """Test alerts handling"""
        request = MagicMock()
        request.query = {'limit': '10'}
        
        # Test the handler
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            response = loop.run_until_complete(self.server.handle_alerts(request))
            self.assertIsNotNone(response)
        finally:
            loop.close()
    
    def test_handle_health(self):
        """Test health check handling"""
        request = MagicMock()
        
        # Test the handler
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            response = loop.run_until_complete(self.server.handle_health(request))
            self.assertIsNotNone(response)
        finally:
            loop.close()


class TestIntegration(unittest.TestCase):
    """Test integration scenarios"""
    
    def setUp(self):
        """Set up integration test"""
        self.config = TelemetryConfig(
            buffer_size=1000,
            processing_interval=0.1
        )
        self.processor = TelemetryProcessor(self.config)
    
    def test_end_to_end_telemetry_processing(self):
        """Test end-to-end telemetry processing"""
        # Start processor
        self.processor.start()
        
        # Ingest some data
        for i in range(10):
            data = {
                "timestamp": time.time(),
                "source": f"sensor_{i}",
                "type": "temperature",
                "value": 70.0 + i,
                "status": "OK"
            }
            self.processor.ingest_data(data)
        
        # Wait for processing
        time.sleep(0.5)
        
        # Check results
        dashboard_data = self.processor.get_dashboard_data()
        self.assertGreater(dashboard_data['total_events'], 0)
        
        # Stop processor
        self.processor.stop()
    
    def test_alert_rule_processing(self):
        """Test alert rule processing"""
        # Add alert rule
        rule = AlertRule(
            rule_id="test_rule",
            name="Test Rule",
            condition="threshold",
            parameters={"field": "temperature", "operator": ">", "value": 80.0},
            severity="warning"
        )
        self.processor.add_alert_rule(rule)
        
        # Start processor
        self.processor.start()
        
        # Ingest data that should trigger alert
        data = {
            "timestamp": time.time(),
            "source": "test_sensor",
            "type": "temperature",
            "value": 85.0,
            "status": "OK"
        }
        self.processor.ingest_data(data)
        
        # Wait for processing
        time.sleep(0.5)
        
        # Check for alerts
        alerts = self.processor.get_alerts()
        self.assertGreater(len(alerts), 0)
        
        # Stop processor
        self.processor.stop()
    
    def test_data_persistence(self):
        """Test data persistence and history"""
        # Start processor
        self.processor.start()
        
        # Ingest data
        for i in range(5):
            data = {
                "timestamp": time.time(),
                "source": "test_sensor",
                "type": "temperature",
                "value": 70.0 + i,
                "status": "OK"
            }
            self.processor.ingest_data(data)
        
        # Wait for processing
        time.sleep(0.5)
        
        # Check data history
        self.assertIn("test_sensor", self.processor.data_history)
        self.assertEqual(len(self.processor.data_history["test_sensor"]), 5)
        
        # Stop processor
        self.processor.stop()


class TestUtilityFunctions(unittest.TestCase):
    """Test utility functions"""
    
    def test_create_telemetry_processor(self):
        """Test processor creation utility"""
        config = TelemetryConfig(buffer_size=5000)
        processor = create_telemetry_processor(config)
        
        self.assertIsInstance(processor, TelemetryProcessor)
        self.assertEqual(processor.config.buffer_size, 5000)
    
    def test_create_telemetry_processor_default(self):
        """Test processor creation with default config"""
        processor = create_telemetry_processor()
        
        self.assertIsInstance(processor, TelemetryProcessor)
        self.assertEqual(processor.config.buffer_size, 10000)


class TestAnalyticsDetectors(unittest.TestCase):
    def test_zscore_anomaly_detector(self):
        detector = ZScoreAnomalyDetector()
        # 10 normal values, 1 strong outlier
        values = [10, 11, 10, 12, 11, 10, 11, 10, 12, 11, 100]
        anomalies = detector.detect(values, sensitivity=1.0)
        # The last value should be flagged as anomaly
        self.assertTrue(anomalies[-1])
        self.assertFalse(any(anomalies[:-1]))


if __name__ == '__main__':
    unittest.main() 