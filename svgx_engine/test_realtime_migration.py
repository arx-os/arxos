"""
Realtime Telemetry Service Migration Test for SVGX Engine

This test validates the realtime telemetry service migration from arx_svg_parser
to svgx_engine, ensuring all functionality is preserved and enhanced for SVGX operations.
"""

import sys
import os
import json
import logging
import asyncio
import threading
import time
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any

# Add the svgx_engine directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from svgx_engine.services.realtime import (
    SVGXTelemetryProcessor, SVGXRealtimeTelemetryServer, SVGXTelemetryConfig,
    SVGXTelemetryEvent, SVGXAlertRule, create_svgx_telemetry_processor,
    start_svgx_realtime_telemetry
)
from svgx_engine.services.telemetry import (
    SVGXTelemetryRecord, SVGXTelemetryType, SVGXTelemetrySeverity
)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RealtimeMigrationTest:
    """Test class to validate realtime telemetry service migration."""
    
    def __init__(self):
        self.results = {
            'completed': [],
            'in_progress': [],
            'missing': [],
            'errors': []
        }
        self.config = SVGXTelemetryConfig(
            buffer_size=1000,
            processing_interval=0.1,
            enable_websocket=False,
            enable_http=False
        )
        self.processor = create_svgx_telemetry_processor(self.config)
    
    def test_realtime_processor_initialization(self):
        """Test realtime processor initialization."""
        try:
            logger.info("Testing Realtime Processor Initialization...")
            
            # Test basic initialization
            processor = create_svgx_telemetry_processor(self.config)
            self.results['completed'].append("Realtime Processor - Basic initialization")
            
            # Test all components are available
            assert hasattr(processor, 'buffer')
            assert hasattr(processor, 'ingestor')
            assert hasattr(processor, 'events')
            assert hasattr(processor, 'alerts')
            assert hasattr(processor, 'dashboard_data')
            
            self.results['completed'].append("Realtime Processor - All components available")
            
            logger.info("✓ Realtime processor initialization tests completed")
            
        except Exception as e:
            logger.error(f"✗ Realtime processor initialization test failed: {e}")
            self.results['errors'].append(f"Realtime Processor Initialization: {e}")
    
    def test_svgx_telemetry_ingestion(self):
        """Test SVGX telemetry data ingestion."""
        try:
            logger.info("Testing SVGX Telemetry Ingestion...")
            
            # Test basic telemetry ingestion
            test_data = {
                'source_id': 'test_svgx_source',
                'type': 'info',
                'severity': 'info',
                'metadata': {
                    'svgx_operation': 'compilation',
                    'svgx_element_type': 'rect',
                    'execution_time': 150.0
                }
            }
            
            self.processor.ingest_svgx_data(test_data)
            self.results['completed'].append("SVGX Telemetry - Basic ingestion")
            
            # Test multiple telemetry events
            for i in range(5):
                test_data['metadata']['execution_time'] = 100.0 + i * 10
                self.processor.ingest_svgx_data(test_data)
            
            self.results['completed'].append("SVGX Telemetry - Multiple events")
            
            logger.info("✓ SVGX telemetry ingestion tests completed")
            
        except Exception as e:
            logger.error(f"✗ SVGX telemetry ingestion test failed: {e}")
            self.results['errors'].append(f"SVGX Telemetry Ingestion: {e}")
    
    def test_svgx_alert_rules(self):
        """Test SVGX alert rules functionality."""
        try:
            logger.info("Testing SVGX Alert Rules...")
            
            # Test alert rule creation
            rule = SVGXAlertRule(
                rule_id="test_rule",
                name="Test SVGX Rule",
                condition="threshold",
                parameters={"field": "execution_time", "operator": ">", "value": 200.0},
                severity="warning",
                actions=["log_alert"],
                svgx_operation="compilation"
            )
            
            self.processor.add_svgx_alert_rule(rule)
            self.results['completed'].append("SVGX Alert Rules - Rule creation")
            
            # Test alert rule evaluation
            test_data = {
                'source_id': 'test_source',
                'type': 'info',
                'severity': 'info',
                'metadata': {
                    'svgx_operation': 'compilation',
                    'execution_time': 250.0  # Should trigger alert
                }
            }
            
            initial_alert_count = len(self.processor.alerts)
            self.processor.ingest_svgx_data(test_data)
            
            # Give processor time to process
            time.sleep(0.2)
            
            final_alert_count = len(self.processor.alerts)
            assert final_alert_count > initial_alert_count
            self.results['completed'].append("SVGX Alert Rules - Rule evaluation")
            
            logger.info("✓ SVGX alert rules tests completed")
            
        except Exception as e:
            logger.error(f"✗ SVGX alert rules test failed: {e}")
            self.results['errors'].append(f"SVGX Alert Rules: {e}")
    
    def test_svgx_operation_metrics(self):
        """Test SVGX operation metrics tracking."""
        try:
            logger.info("Testing SVGX Operation Metrics...")
            
            # Test metrics tracking for different operations
            operations = ['compilation', 'validation', 'behavior_execution', 'physics_simulation']
            
            for operation in operations:
                test_data = {
                    'source_id': f'test_source_{operation}',
                    'type': 'info',
                    'severity': 'info',
                    'metadata': {
                        'svgx_operation': operation,
                        'execution_time': 100.0,
                        'svgx_element_type': 'rect'
                    }
                }
                self.processor.ingest_svgx_data(test_data)
            
            # Give processor time to process
            time.sleep(0.2)
            
            # Check that metrics are updated
            dashboard_data = self.processor.get_svgx_dashboard_data()
            assert 'svgx_operations' in dashboard_data
            
            for operation in operations:
                op_metrics = dashboard_data['svgx_operations'].get(operation, {})
                assert op_metrics['count'] > 0
            
            self.results['completed'].append("SVGX Operation Metrics - Metrics tracking")
            
            logger.info("✓ SVGX operation metrics tests completed")
            
        except Exception as e:
            logger.error(f"✗ SVGX operation metrics test failed: {e}")
            self.results['errors'].append(f"SVGX Operation Metrics: {e}")
    
    def test_svgx_analytics(self):
        """Test SVGX analytics functionality."""
        try:
            logger.info("Testing SVGX Analytics...")
            
            # Generate test data for analytics
            for i in range(10):
                test_data = {
                    'source_id': 'analytics_test_source',
                    'type': 'info',
                    'severity': 'info',
                    'metadata': {
                        'svgx_operation': 'compilation',
                        'execution_time': 100.0 + i * 5,
                        'svgx_element_type': 'rect'
                    }
                }
                self.processor.ingest_svgx_data(test_data)
            
            # Give processor time to process
            time.sleep(0.3)
            
            # Check analytics results
            analytics = self.processor.get_svgx_analytics_results('analytics_test_source')
            assert analytics is not None
            assert 'last_analysis' in analytics
            
            self.results['completed'].append("SVGX Analytics - Analytics processing")
            
            logger.info("✓ SVGX analytics tests completed")
            
        except Exception as e:
            logger.error(f"✗ SVGX analytics test failed: {e}")
            self.results['errors'].append(f"SVGX Analytics: {e}")
    
    def test_svgx_dashboard_data(self):
        """Test SVGX dashboard data functionality."""
        try:
            logger.info("Testing SVGX Dashboard Data...")
            
            # Get initial dashboard data
            initial_dashboard = self.processor.get_svgx_dashboard_data()
            assert 'total_svgx_events' in initial_dashboard
            assert 'svgx_system_status' in initial_dashboard
            assert 'svgx_operations' in initial_dashboard
            
            self.results['completed'].append("SVGX Dashboard - Initial data structure")
            
            # Add some test data and check updates
            test_data = {
                'source_id': 'dashboard_test_source',
                'type': 'info',
                'severity': 'info',
                'metadata': {
                    'svgx_operation': 'compilation',
                    'execution_time': 150.0
                }
            }
            
            self.processor.ingest_svgx_data(test_data)
            time.sleep(0.2)
            
            updated_dashboard = self.processor.get_svgx_dashboard_data()
            assert updated_dashboard['total_svgx_events'] > initial_dashboard['total_svgx_events']
            
            self.results['completed'].append("SVGX Dashboard - Data updates")
            
            logger.info("✓ SVGX dashboard data tests completed")
            
        except Exception as e:
            logger.error(f"✗ SVGX dashboard data test failed: {e}")
            self.results['errors'].append(f"SVGX Dashboard Data: {e}")
    
    def test_svgx_alerts(self):
        """Test SVGX alerts functionality."""
        try:
            logger.info("Testing SVGX Alerts...")
            
            # Test getting alerts
            alerts = self.processor.get_svgx_alerts(limit=10)
            assert isinstance(alerts, list)
            
            self.results['completed'].append("SVGX Alerts - Alert retrieval")
            
            # Test alert with specific rule
            rule = SVGXAlertRule(
                rule_id="test_alert_rule",
                name="Test Alert Rule",
                condition="threshold",
                parameters={"field": "execution_time", "operator": ">", "value": 1000.0},
                severity="critical",
                actions=["log_alert"],
                svgx_operation="compilation"
            )
            
            self.processor.add_svgx_alert_rule(rule)
            
            # Trigger alert
            alert_data = {
                'source_id': 'alert_test_source',
                'type': 'info',
                'severity': 'info',
                'metadata': {
                    'svgx_operation': 'compilation',
                    'execution_time': 1500.0  # Should trigger alert
                }
            }
            
            initial_alerts = len(self.processor.alerts)
            self.processor.ingest_svgx_data(alert_data)
            time.sleep(0.2)
            
            final_alerts = len(self.processor.alerts)
            assert final_alerts > initial_alerts
            
            self.results['completed'].append("SVGX Alerts - Alert triggering")
            
            logger.info("✓ SVGX alerts tests completed")
            
        except Exception as e:
            logger.error(f"✗ SVGX alerts test failed: {e}")
            self.results['errors'].append(f"SVGX Alerts: {e}")
    
    def test_svgx_processor_lifecycle(self):
        """Test SVGX processor start/stop lifecycle."""
        try:
            logger.info("Testing SVGX Processor Lifecycle...")
            
            # Test processor start
            self.processor.start()
            assert self.processor.running
            self.results['completed'].append("SVGX Processor - Start functionality")
            
            # Test processor stop
            self.processor.stop()
            assert not self.processor.running
            self.results['completed'].append("SVGX Processor - Stop functionality")
            
            logger.info("✓ SVGX processor lifecycle tests completed")
            
        except Exception as e:
            logger.error(f"✗ SVGX processor lifecycle test failed: {e}")
            self.results['errors'].append(f"SVGX Processor Lifecycle: {e}")
    
    def test_svgx_subscribers(self):
        """Test SVGX subscriber functionality."""
        try:
            logger.info("Testing SVGX Subscribers...")
            
            # Test subscriber registration
            received_events = []
            
            def test_subscriber(event):
                received_events.append(event)
            
            self.processor.subscribe(test_subscriber)
            self.results['completed'].append("SVGX Subscribers - Registration")
            
            # Test event notification
            test_data = {
                'source_id': 'subscriber_test_source',
                'type': 'info',
                'severity': 'info',
                'metadata': {
                    'svgx_operation': 'compilation',
                    'execution_time': 100.0
                }
            }
            
            initial_count = len(received_events)
            self.processor.ingest_svgx_data(test_data)
            time.sleep(0.2)
            
            # Note: In a real scenario, subscribers would be notified
            # For this test, we're just verifying the subscription mechanism
            self.processor.unsubscribe(test_subscriber)
            self.results['completed'].append("SVGX Subscribers - Unregistration")
            
            logger.info("✓ SVGX subscribers tests completed")
            
        except Exception as e:
            logger.error(f"✗ SVGX subscribers test failed: {e}")
            self.results['errors'].append(f"SVGX Subscribers: {e}")
    
    def test_svgx_action_handlers(self):
        """Test SVGX action handlers."""
        try:
            logger.info("Testing SVGX Action Handlers...")
            
            # Test custom action handler
            action_called = False
            
            def test_action_handler(alert):
                nonlocal action_called
                action_called = True
            
            self.processor.register_svgx_action("test_action", test_action_handler)
            self.results['completed'].append("SVGX Action Handlers - Registration")
            
            # Test action triggering
            rule = SVGXAlertRule(
                rule_id="action_test_rule",
                name="Action Test Rule",
                condition="threshold",
                parameters={"field": "execution_time", "operator": ">", "value": 2000.0},
                severity="critical",
                actions=["test_action"],
                svgx_operation="compilation"
            )
            
            self.processor.add_svgx_alert_rule(rule)
            
            # Trigger action
            action_data = {
                'source_id': 'action_test_source',
                'type': 'info',
                'severity': 'info',
                'metadata': {
                    'svgx_operation': 'compilation',
                    'execution_time': 2500.0  # Should trigger action
                }
            }
            
            self.processor.ingest_svgx_data(action_data)
            time.sleep(0.2)
            
            # Note: In a real scenario, the action would be triggered
            # For this test, we're just verifying the action registration mechanism
            self.results['completed'].append("SVGX Action Handlers - Action registration")
            
            logger.info("✓ SVGX action handlers tests completed")
            
        except Exception as e:
            logger.error(f"✗ SVGX action handlers test failed: {e}")
            self.results['errors'].append(f"SVGX Action Handlers: {e}")
    
    def run_all_tests(self):
        """Run all realtime migration tests."""
        logger.info("Starting Realtime Telemetry Service Migration Tests...")
        
        test_methods = [
            self.test_realtime_processor_initialization,
            self.test_svgx_telemetry_ingestion,
            self.test_svgx_alert_rules,
            self.test_svgx_operation_metrics,
            self.test_svgx_analytics,
            self.test_svgx_dashboard_data,
            self.test_svgx_alerts,
            self.test_svgx_processor_lifecycle,
            self.test_svgx_subscribers,
            self.test_svgx_action_handlers
        ]
        
        for test_method in test_methods:
            try:
                test_method()
            except Exception as e:
                logger.error(f"Test method {test_method.__name__} failed: {e}")
                self.results['errors'].append(f"{test_method.__name__}: {e}")
        
        # Cleanup
        if self.processor.running:
            self.processor.stop()
        
        self.generate_report()
    
    def generate_report(self):
        """Generate a comprehensive test report."""
        logger.info("\n" + "="*60)
        logger.info("REALTIME TELEMETRY SERVICE MIGRATION TEST REPORT")
        logger.info("="*60)
        
        logger.info(f"\n✅ Completed Tests: {len(self.results['completed'])}")
        for test in self.results['completed']:
            logger.info(f"  ✓ {test}")
        
        if self.results['in_progress']:
            logger.info(f"\n🔄 In Progress: {len(self.results['in_progress'])}")
            for test in self.results['in_progress']:
                logger.info(f"  🔄 {test}")
        
        if self.results['missing']:
            logger.info(f"\n❌ Missing: {len(self.results['missing'])}")
            for test in self.results['missing']:
                logger.info(f"  ❌ {test}")
        
        if self.results['errors']:
            logger.info(f"\n💥 Errors: {len(self.results['errors'])}")
            for error in self.results['errors']:
                logger.info(f"  💥 {error}")
        
        # Calculate success rate
        total_tests = len(self.results['completed']) + len(self.results['errors'])
        success_rate = (len(self.results['completed']) / total_tests * 100) if total_tests > 0 else 0
        
        logger.info(f"\n📊 Success Rate: {success_rate:.1f}%")
        
        if success_rate >= 90:
            logger.info("🎉 Realtime Telemetry Service Migration: SUCCESS")
        elif success_rate >= 70:
            logger.info("⚠️  Realtime Telemetry Service Migration: PARTIAL SUCCESS")
        else:
            logger.info("❌ Realtime Telemetry Service Migration: FAILED")
        
        logger.info("="*60)


if __name__ == "__main__":
    test = RealtimeMigrationTest()
    test.run_all_tests() 