"""
Real-Time Telemetry Service for SVGX Engine

This module provides real-time telemetry capabilities specifically designed for SVGX operations:
- Real-time SVGX operation monitoring
- SVGX-specific alerting and anomaly detection
- Live dashboard for SVGX performance metrics
- WebSocket and HTTP endpoints for SVGX telemetry ingestion
- SVGX behavior and physics monitoring
- Real-time SVGX compilation and validation tracking
"""

import asyncio
import json
import logging
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable, Set
from dataclasses import dataclass, field
from queue import Queue, Empty
import websockets
from websockets.server import serve
import aiohttp
from aiohttp import web
import numpy as np

from structlog import get_logger

from svgx_engine.services.telemetry import (
    SVGXTelemetryBuffer, SVGXTelemetryRecord, SVGXTelemetryIngestor,
    SVGXTelemetryType, SVGXTelemetrySeverity
)

logger = get_logger(__name__)


@dataclass
class SVGXTelemetryConfig:
    """Configuration for SVGX telemetry processing"""
    buffer_size: int = 10000
    processing_interval: float = 1.0  # seconds
    alert_threshold: float = 0.8
    max_history_size: int = 100000
    enable_websocket: bool = True
    websocket_port: int = 8765
    enable_http: bool = True
    http_port: int = 8080
    enable_dashboard: bool = True
    dashboard_port: int = 8081
    svgx_specific_metrics: bool = True


@dataclass
class SVGXTelemetryEvent:
    """Represents an SVGX telemetry event with metadata"""
    record: SVGXTelemetryRecord
    timestamp: datetime
    source_id: str
    event_type: str
    svgx_operation: str = "unknown"
    svgx_element_type: str = "unknown"
    severity: str = "info"
    processed: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SVGXAlertRule:
    """Defines alert rules for SVGX telemetry data"""
    rule_id: str
    name: str
    condition: str  # "threshold", "trend", "pattern", "anomaly", "svgx_specific"
    parameters: Dict[str, Any]
    severity: str = "warning"
    enabled: bool = True
    actions: List[str] = field(default_factory=list)
    svgx_operation: str = "all"  # Specific SVGX operation to monitor


class SVGXTelemetryProcessor:
    """Processes SVGX telemetry data in real-time"""
    
    def __init__(self, config: SVGXTelemetryConfig):
        self.config = config
        self.buffer = SVGXTelemetryBuffer(max_size=config.buffer_size)
        self.ingestor = SVGXTelemetryIngestor(self.buffer)
        
        # Event tracking
        self.events: List[SVGXTelemetryEvent] = []
        self.alerts: List[Dict[str, Any]] = []
        self.dashboard_data: Dict[str, Any] = {
            'last_update': datetime.now().isoformat(),
            'total_svgx_events': 0,
            'active_alerts': 0,
            'svgx_system_status': 'healthy',
            'svgx_operations': {
                'compilation': {'count': 0, 'avg_time': 0.0, 'errors': 0},
                'validation': {'count': 0, 'avg_time': 0.0, 'errors': 0},
                'behavior_execution': {'count': 0, 'avg_time': 0.0, 'errors': 0},
                'physics_simulation': {'count': 0, 'avg_time': 0.0, 'errors': 0},
                'export': {'count': 0, 'avg_time': 0.0, 'errors': 0}
            }
        }
        
        # Processing state
        self.running = False
        self.processing_thread = None
        self.alert_rules: Dict[str, SVGXAlertRule] = {}
        self.action_handlers: Dict[str, Callable] = {}
        
        # SVGX-specific data storage
        self.svgx_data_history: Dict[str, List[SVGXTelemetryRecord]] = {}
        self.svgx_operation_metrics: Dict[str, Dict[str, Any]] = {}
        self.svgx_error_patterns: List[Dict[str, Any]] = []
        
        # Subscribers for real-time updates
        self.subscribers: Set[Callable] = set()
        
        # SVGX-specific analytics
        self.svgx_analytics_results: Dict[str, Dict[str, Any]] = {}
        
        # Initialize default SVGX alert rules
        self._initialize_svgx_default_rules()
        self._initialize_svgx_action_handlers()
    
    def _initialize_svgx_default_rules(self):
        """Initialize default SVGX-specific alert rules"""
        self.add_svgx_alert_rule(SVGXAlertRule(
            rule_id="svgx_compilation_timeout",
            name="SVGX Compilation Timeout Alert",
            condition="threshold",
            parameters={"field": "compilation_time", "operator": ">", "value": 5000.0},  # 5 seconds
            severity="critical",
            actions=["log_alert", "send_notification"],
            svgx_operation="compilation"
        ))
        
        self.add_svgx_alert_rule(SVGXAlertRule(
            rule_id="svgx_validation_errors",
            name="SVGX Validation Error Alert",
            condition="threshold",
            parameters={"field": "validation_errors", "operator": ">", "value": 10},
            severity="warning",
            actions=["log_alert", "trigger_inspection"],
            svgx_operation="validation"
        ))
        
        self.add_svgx_alert_rule(SVGXAlertRule(
            rule_id="svgx_behavior_execution_failure",
            name="SVGX Behavior Execution Failure Alert",
            condition="pattern",
            parameters={"pattern": "behavior_execution_failed", "window": 5},
            severity="critical",
            actions=["log_alert", "send_notification", "trigger_inspection"],
            svgx_operation="behavior_execution"
        ))
        
        self.add_svgx_alert_rule(SVGXAlertRule(
            rule_id="svgx_physics_simulation_anomaly",
            name="SVGX Physics Simulation Anomaly Alert",
            condition="anomaly",
            parameters={"field": "physics_simulation_time", "sensitivity": 0.8},
            severity="warning",
            actions=["log_alert"],
            svgx_operation="physics_simulation"
        ))
    
    def _initialize_svgx_action_handlers(self):
        """Initialize SVGX-specific action handlers"""
        self.register_svgx_action("log_alert", self._log_svgx_alert)
        self.register_svgx_action("send_notification", self._send_svgx_notification)
        self.register_svgx_action("trigger_inspection", self._trigger_svgx_inspection)
        self.register_svgx_action("update_svgx_dashboard", self._update_svgx_dashboard)
        self.register_svgx_action("restart_svgx_service", self._restart_svgx_service)
    
    def start(self):
        """Start the SVGX telemetry processor"""
        if self.running:
            logger.warning("SVGX telemetry processor is already running")
            return
        
        self.running = True
        self.buffer.start()
        
        # Start processing thread
        self.processing_thread = threading.Thread(target=self._svgx_processing_loop, daemon=True)
        self.processing_thread.start()
        
        # Add buffer listener
        self.buffer.add_listener(self._on_svgx_telemetry_received)
        
        logger.info("SVGX telemetry processor started")
    
    def stop(self):
        """Stop the SVGX telemetry processor"""
        if not self.running:
            return
        
        self.running = False
        self.buffer.stop()
        
        if self.processing_thread:
            self.processing_thread.join()
        
        logger.info("SVGX telemetry processor stopped")
    
    def _on_svgx_telemetry_received(self, record: SVGXTelemetryRecord):
        """Handle incoming SVGX telemetry data"""
        try:
            # Create SVGX-specific event
            event = SVGXTelemetryEvent(
                record=record,
                timestamp=datetime.now(),
                source_id=record.source_id,
                event_type=record.telemetry_type.value,
                svgx_operation=record.metadata.get('svgx_operation', 'unknown'),
                svgx_element_type=record.metadata.get('svgx_element_type', 'unknown'),
                severity=record.severity.value,
                metadata=record.metadata
            )
            
            self.events.append(event)
            
            # Update SVGX operation metrics
            self._update_svgx_operation_metrics(event)
            
            # Check for alerts
            self._check_svgx_alert_rules(event)
            
            # Notify subscribers
            self._notify_svgx_subscribers(event)
            
        except Exception as e:
            logger.error(f"Error processing SVGX telemetry: {e}")
    
    def _svgx_processing_loop(self):
        """Main processing loop for SVGX telemetry"""
        while self.running:
            try:
                self._process_svgx_events()
                self._run_svgx_analytics()
                self._update_svgx_dashboard_data()
                time.sleep(self.config.processing_interval)
            except Exception as e:
                logger.error(f"Error in SVGX processing loop: {e}")
                time.sleep(1.0)
    
    def _process_svgx_events(self):
        """Process accumulated SVGX events"""
        current_time = datetime.now()
        
        # Process recent events
        recent_events = [e for e in self.events if not e.processed]
        
        for event in recent_events:
            event.processed = True
            
            # Update SVGX-specific metrics
            self._update_svgx_operation_metrics(event)
            
            # Run SVGX-specific analytics
            self._analyze_svgx_source_data(event.source_id, [event.record])
        
        # Clean up old events
        cutoff_time = current_time - timedelta(hours=1)
        self.events = [e for e in self.events if e.timestamp > cutoff_time]
    
    def _update_svgx_operation_metrics(self, event: SVGXTelemetryEvent):
        """Update SVGX operation-specific metrics"""
        operation = event.svgx_operation
        if operation not in self.svgx_operation_metrics:
            self.svgx_operation_metrics[operation] = {
                'count': 0,
                'total_time': 0.0,
                'errors': 0,
                'last_update': datetime.now()
            }
        
        metrics = self.svgx_operation_metrics[operation]
        metrics['count'] += 1
        metrics['last_update'] = datetime.now()
        
        # Update timing metrics if available
        if 'execution_time' in event.metadata:
            metrics['total_time'] += event.metadata['execution_time']
        
        # Update error count if applicable
        if event.severity in ['error', 'critical']:
            metrics['errors'] += 1
        
        # Update dashboard data
        if operation in self.dashboard_data['svgx_operations']:
            dashboard_op = self.dashboard_data['svgx_operations'][operation]
            dashboard_op['count'] = metrics['count']
            dashboard_op['errors'] = metrics['errors']
            if metrics['count'] > 0:
                dashboard_op['avg_time'] = metrics['total_time'] / metrics['count']
    
    def _analyze_svgx_source_data(self, source_id: str, records: List[SVGXTelemetryRecord]):
        """Analyze SVGX-specific data patterns"""
        if not records:
            return
        
        # Convert records to data for analysis
        data = self._svgx_records_to_data(records)
        
        # Analyze SVGX-specific patterns
        self._analyze_svgx_patterns(source_id, data)
        
        # Update analytics results
        self.svgx_analytics_results[source_id] = {
            'last_analysis': datetime.now().isoformat(),
            'record_count': len(records),
            'patterns': self._extract_svgx_patterns(data)
        }
    
    def _svgx_records_to_data(self, records: List[SVGXTelemetryRecord]) -> Dict[str, Any]:
        """Convert SVGX telemetry records to analysis data"""
        data = {
            'timestamps': [],
            'execution_times': [],
            'error_counts': [],
            'svgx_operations': [],
            'svgx_element_types': []
        }
        
        for record in records:
            data['timestamps'].append(record.timestamp)
            data['execution_times'].append(record.metadata.get('execution_time', 0.0))
            data['error_counts'].append(1 if record.severity in ['error', 'critical'] else 0)
            data['svgx_operations'].append(record.metadata.get('svgx_operation', 'unknown'))
            data['svgx_element_types'].append(record.metadata.get('svgx_element_type', 'unknown'))
        
        return data
    
    def _analyze_svgx_patterns(self, source_id: str, data: Dict[str, Any]):
        """Analyze SVGX-specific patterns in the data"""
        # Analyze error patterns
        error_rate = sum(data['error_counts']) / len(data['error_counts']) if data['error_counts'] else 0
        
        # Analyze performance patterns
        avg_execution_time = np.mean(data['execution_times']) if data['execution_times'] else 0.0
        
        # Analyze operation distribution
        operation_counts = {}
        for op in data['svgx_operations']:
            operation_counts[op] = operation_counts.get(op, 0) + 1
        
        # Store analysis results
        self.svgx_analytics_results[source_id] = {
            'error_rate': error_rate,
            'avg_execution_time': avg_execution_time,
            'operation_distribution': operation_counts,
            'last_analysis': datetime.now().isoformat()
        }
    
    def _extract_svgx_patterns(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract SVGX-specific patterns from data"""
        patterns = []
        
        # Error pattern detection
        if data['error_counts']:
            error_rate = sum(data['error_counts']) / len(data['error_counts'])
            if error_rate > 0.1:  # More than 10% errors
                patterns.append({
                    'type': 'high_error_rate',
                    'value': error_rate,
                    'severity': 'warning' if error_rate < 0.3 else 'critical'
                })
        
        # Performance pattern detection
        if data['execution_times']:
            avg_time = np.mean(data['execution_times'])
            if avg_time > 1000:  # More than 1 second average
                patterns.append({
                    'type': 'slow_execution',
                    'value': avg_time,
                    'severity': 'warning'
                })
        
        return patterns
    
    def _check_svgx_alert_rules(self, event: SVGXTelemetryEvent):
        """Check SVGX-specific alert rules"""
        for rule in self.alert_rules.values():
            if not rule.enabled:
                continue
            
            # Check if rule applies to this SVGX operation
            if rule.svgx_operation != "all" and rule.svgx_operation != event.svgx_operation:
                continue
            
            if self._evaluate_svgx_rule(rule, event):
                alert = {
                    'rule_id': rule.rule_id,
                    'rule_name': rule.name,
                    'severity': rule.severity,
                    'timestamp': datetime.now().isoformat(),
                    'event': {
                        'source_id': event.source_id,
                        'svgx_operation': event.svgx_operation,
                        'svgx_element_type': event.svgx_element_type,
                        'severity': event.severity,
                        'metadata': event.metadata
                    }
                }
                
                self.alerts.append(alert)
                self._trigger_svgx_actions(alert, rule.actions)
    
    def _evaluate_svgx_rule(self, rule: SVGXAlertRule, event: SVGXTelemetryEvent) -> bool:
        """Evaluate SVGX-specific alert rule"""
        if rule.condition == "threshold":
            return self._evaluate_svgx_threshold_rule(rule, event)
        elif rule.condition == "trend":
            return self._evaluate_svgx_trend_rule(rule, event)
        elif rule.condition == "pattern":
            return self._evaluate_svgx_pattern_rule(rule, event)
        elif rule.condition == "anomaly":
            return self._evaluate_svgx_anomaly_rule(rule, event)
        elif rule.condition == "svgx_specific":
            return self._evaluate_svgx_specific_rule(rule, event)
        
        return False
    
    def _evaluate_svgx_threshold_rule(self, rule: SVGXAlertRule, event: SVGXTelemetryEvent) -> bool:
        """Evaluate threshold-based SVGX rule"""
        field = rule.parameters.get("field")
        operator = rule.parameters.get("operator")
        value = rule.parameters.get("value")
        
        if field not in event.metadata:
            return False
        
        actual_value = event.metadata[field]
        
        if operator == ">":
            return actual_value > value
        elif operator == "<":
            return actual_value < value
        elif operator == ">=":
            return actual_value >= value
        elif operator == "<=":
            return actual_value <= value
        elif operator == "==":
            return actual_value == value
        
        return False
    
    def _evaluate_svgx_trend_rule(self, rule: SVGXAlertRule, event: SVGXTelemetryEvent) -> bool:
        """Evaluate trend-based SVGX rule"""
        field = rule.parameters.get("field")
        window = rule.parameters.get("window", 10)
        threshold = rule.parameters.get("threshold", 0.5)
        
        # Get recent events for this source
        recent_events = [e for e in self.events[-window:] if e.source_id == event.source_id]
        
        if len(recent_events) < window:
            return False
        
        values = [e.metadata.get(field, 0) for e in recent_events]
        
        # Calculate trend (simple linear regression)
        if len(values) >= 2:
            x = np.arange(len(values))
            slope = np.polyfit(x, values, 1)[0]
            return abs(slope) > threshold
        
        return False
    
    def _evaluate_svgx_pattern_rule(self, rule: SVGXAlertRule, event: SVGXTelemetryEvent) -> bool:
        """Evaluate pattern-based SVGX rule"""
        pattern = rule.parameters.get("pattern")
        window = rule.parameters.get("window", 5)
        
        # Get recent events for this source
        recent_events = [e for e in self.events[-window:] if e.source_id == event.source_id]
        
        # Check if pattern matches
        pattern_matches = sum(1 for e in recent_events if pattern in str(e.metadata))
        return pattern_matches >= window * 0.8  # 80% of events match pattern
    
    def _evaluate_svgx_anomaly_rule(self, rule: SVGXAlertRule, event: SVGXTelemetryEvent) -> bool:
        """Evaluate anomaly-based SVGX rule"""
        field = rule.parameters.get("field")
        sensitivity = rule.parameters.get("sensitivity", 0.8)
        
        if field not in event.metadata:
            return False
        
        # Get historical data for this field
        historical_values = [e.metadata.get(field, 0) for e in self.events if field in e.metadata]
        
        if len(historical_values) < 10:
            return False
        
        # Simple anomaly detection using z-score
        mean_val = np.mean(historical_values)
        std_val = np.std(historical_values)
        
        if std_val == 0:
            return False
        
        current_value = event.metadata[field]
        z_score = abs((current_value - mean_val) / std_val)
        
        return z_score > (2.0 / sensitivity)  # Adjust threshold based on sensitivity
    
    def _evaluate_svgx_specific_rule(self, rule: SVGXAlertRule, event: SVGXTelemetryEvent) -> bool:
        """Evaluate SVGX-specific rule"""
        # Custom SVGX-specific logic
        if rule.rule_id == "svgx_compilation_timeout":
            return event.svgx_operation == "compilation" and event.metadata.get('execution_time', 0) > 5000
        
        elif rule.rule_id == "svgx_validation_errors":
            return event.svgx_operation == "validation" and event.metadata.get('validation_errors', 0) > 10
        
        elif rule.rule_id == "svgx_behavior_execution_failure":
            return event.svgx_operation == "behavior_execution" and event.severity in ['error', 'critical']
        
        return False
    
    def _trigger_svgx_actions(self, alert: Dict[str, Any], actions: List[str] = None):
        """Trigger SVGX-specific actions"""
        if actions is None:
            actions = alert.get('actions', [])
        
        for action_name in actions:
            if action_name in self.action_handlers:
                try:
                    self.action_handlers[action_name](alert)
                except Exception as e:
                    logger.error(f"Error executing SVGX action {action_name}: {e}")
    
    def _log_svgx_alert(self, alert: Dict[str, Any]):
        """Log SVGX-specific alert"""
        logger.warning(f"SVGX Alert: {alert['rule_name']} - {alert['event']['svgx_operation']}")
    
    def _send_svgx_notification(self, alert: Dict[str, Any]):
        """Send SVGX-specific notification"""
        # Implementation would integrate with notification system
        logger.info(f"SVGX Notification sent for: {alert['rule_name']}")
    
    def _trigger_svgx_inspection(self, alert: Dict[str, Any]):
        """Trigger SVGX-specific inspection"""
        logger.info(f"SVGX Inspection triggered for: {alert['event']['svgx_operation']}")
    
    def _update_svgx_dashboard(self, alert: Dict[str, Any]):
        """Update SVGX dashboard with alert"""
        self.dashboard_data['active_alerts'] = len(self.alerts)
        self.dashboard_data['last_update'] = datetime.now().isoformat()
    
    def _restart_svgx_service(self, alert: Dict[str, Any]):
        """Restart SVGX service if needed"""
        logger.warning(f"SVGX Service restart triggered for: {alert['rule_name']}")
    
    def _run_svgx_analytics(self):
        """Run SVGX-specific analytics"""
        for source_id in self.svgx_data_history:
            records = self.svgx_data_history[source_id]
            if records:
                self._analyze_svgx_source_data(source_id, records)
    
    def _update_svgx_dashboard_data(self):
        """Update SVGX dashboard data"""
        self.dashboard_data['total_svgx_events'] = len(self.events)
        self.dashboard_data['active_alerts'] = len(self.alerts)
        self.dashboard_data['last_update'] = datetime.now().isoformat()
        
        # Update system status based on alerts
        critical_alerts = [a for a in self.alerts if a['severity'] == 'critical']
        if critical_alerts:
            self.dashboard_data['svgx_system_status'] = 'critical'
        elif self.alerts:
            self.dashboard_data['svgx_system_status'] = 'warning'
        else:
            self.dashboard_data['svgx_system_status'] = 'healthy'
    
    def _notify_svgx_subscribers(self, event: SVGXTelemetryEvent):
        """Notify SVGX subscribers of new events"""
        for subscriber in self.subscribers:
            try:
                subscriber(event)
            except Exception as e:
                logger.error(f"Error notifying SVGX subscriber: {e}")
    
    def add_svgx_alert_rule(self, rule: SVGXAlertRule):
        """Add SVGX-specific alert rule"""
        self.alert_rules[rule.rule_id] = rule
        logger.info(f"Added SVGX alert rule: {rule.name}")
    
    def remove_svgx_alert_rule(self, rule_id: str):
        """Remove SVGX-specific alert rule"""
        if rule_id in self.alert_rules:
            del self.alert_rules[rule_id]
            logger.info(f"Removed SVGX alert rule: {rule_id}")
    
    def register_svgx_action(self, action_name: str, handler: Callable):
        """Register SVGX-specific action handler"""
        self.action_handlers[action_name] = handler
        logger.info(f"Registered SVGX action: {action_name}")
    
    def subscribe(self, callback: Callable):
        """Subscribe to SVGX telemetry updates"""
        self.subscribers.add(callback)
    
    def unsubscribe(self, callback: Callable):
        """Unsubscribe from SVGX telemetry updates"""
        self.subscribers.discard(callback)
    
    def get_svgx_dashboard_data(self) -> Dict[str, Any]:
        """Get SVGX dashboard data"""
        return self.dashboard_data.copy()
    
    def get_svgx_alerts(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get SVGX alerts"""
        return self.alerts[-limit:] if self.alerts else []
    
    def get_svgx_analytics_results(self, source_id: str = None) -> Dict[str, Any]:
        """Get SVGX analytics results"""
        if source_id:
            return self.svgx_analytics_results.get(source_id, {})
        return self.svgx_analytics_results.copy()
    
    def ingest_svgx_data(self, data: Dict[str, Any]):
        """Ingest SVGX-specific telemetry data"""
        try:
            record = SVGXTelemetryRecord(
                source_id=data.get('source_id', 'unknown'),
                telemetry_type=SVGXTelemetryType(data.get('type', 'info')),
                severity=SVGXTelemetrySeverity(data.get('severity', 'info')),
                metadata=data.get('metadata', {}),
                timestamp=datetime.now()
            )
            
            self.buffer.add_record(record)
            logger.debug(f"Ingested SVGX telemetry data from {record.source_id}")
            
        except Exception as e:
            logger.error(f"Error ingesting SVGX data: {e}")


class SVGXRealtimeTelemetryServer:
    """WebSocket and HTTP server for SVGX telemetry"""
    
    def __init__(self, processor: SVGXTelemetryProcessor, config: SVGXTelemetryConfig):
        self.processor = processor
        self.config = config
        self.app = web.Application()
        self.setup_routes()
        self.websocket_clients = set()
    
    def setup_routes(self):
        """Setup HTTP routes for SVGX telemetry"""
        self.app.router.add_post('/svgx/telemetry', self.handle_svgx_telemetry)
        self.app.router.add_get('/svgx/dashboard', self.handle_svgx_dashboard)
        self.app.router.add_get('/svgx/alerts', self.handle_svgx_alerts)
        self.app.router.add_get('/svgx/analytics', self.handle_svgx_analytics)
        self.app.router.add_get('/svgx/health', self.handle_svgx_health)
    
    async def handle_svgx_telemetry(self, request):
        """Handle SVGX telemetry data ingestion"""
        try:
            data = await request.json()
            self.processor.ingest_svgx_data(data)
            return web.json_response({'status': 'success'})
        except Exception as e:
            logger.error(f"Error handling SVGX telemetry: {e}")
            return web.json_response({'status': 'error', 'message': str(e)}, status=400)
    
    async def handle_svgx_dashboard(self, request):
        """Handle SVGX dashboard data requests"""
        dashboard_data = self.processor.get_svgx_dashboard_data()
        return web.json_response(dashboard_data)
    
    async def handle_svgx_alerts(self, request):
        """Handle SVGX alerts requests"""
        limit = int(request.query.get('limit', 100))
        alerts = self.processor.get_svgx_alerts(limit)
        return web.json_response(alerts)
    
    async def handle_svgx_analytics(self, request):
        """Handle SVGX analytics requests"""
        source_id = request.query.get('source_id')
        analytics = self.processor.get_svgx_analytics_results(source_id)
        return web.json_response(analytics)
    
    async def handle_svgx_health(self, request):
        """Handle SVGX health check"""
        return web.json_response({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'processor_running': self.processor.running
        })
    
    async def svgx_websocket_handler(self, websocket, path):
        """Handle SVGX WebSocket connections"""
        self.websocket_clients.add(websocket)
        try:
            async for message in websocket:
                try:
                    data = json.loads(message)
                    self.processor.ingest_svgx_data(data)
                except json.JSONDecodeError:
                    logger.warning("Invalid JSON received via WebSocket")
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            self.websocket_clients.discard(websocket)
    
    async def broadcast_svgx_update(self, data: Dict[str, Any]):
        """Broadcast SVGX update to all WebSocket clients"""
        if self.websocket_clients:
            message = json.dumps(data)
            await asyncio.gather(
                *[client.send(message) for client in self.websocket_clients],
                return_exceptions=True
            )
    
    async def start_svgx_websocket_server(self):
        """Start SVGX WebSocket server"""
        if self.config.enable_websocket:
            server = await serve(self.svgx_websocket_handler, "localhost", self.config.websocket_port)
            logger.info(f"SVGX WebSocket server started on port {self.config.websocket_port}")
            return server
        return None
    
    async def start_svgx_http_server(self):
        """Start SVGX HTTP server"""
        if self.config.enable_http:
            runner = web.AppRunner(self.app)
            await runner.setup()
            site = web.TCPSite(runner, "localhost", self.config.http_port)
            await site.start()
            logger.info(f"SVGX HTTP server started on port {self.config.http_port}")
            return runner
        return None
    
    async def start(self):
        """Start the SVGX telemetry server"""
        websocket_server = await self.start_svgx_websocket_server()
        http_runner = await self.start_svgx_http_server()
        
        logger.info("SVGX Realtime Telemetry Server started")
        
        # Keep the server running
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            logger.info("Shutting down SVGX telemetry server")


def create_svgx_telemetry_processor(config: SVGXTelemetryConfig = None) -> SVGXTelemetryProcessor:
    """Create SVGX telemetry processor"""
    if config is None:
        config = SVGXTelemetryConfig()
    
    return SVGXTelemetryProcessor(config)


def start_svgx_realtime_telemetry(config: SVGXTelemetryConfig = None):
    """Start SVGX realtime telemetry system"""
    processor = create_svgx_telemetry_processor(config)
    server = SVGXRealtimeTelemetryServer(processor, config or SVGXTelemetryConfig())
    
    processor.start()
    
    # Start server in background
    asyncio.create_task(server.start())
    
    return processor, server 