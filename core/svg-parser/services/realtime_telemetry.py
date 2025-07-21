"""
Real-Time Telemetry Integration System

This module provides:
- Real-time telemetry ingestion and processing
- Integration with failure detection system
- Live monitoring and alerting
- Automated response triggers
- WebSocket and HTTP endpoints for data ingestion
- Dashboard data streaming
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

# Import our existing services
from core.telemetry
from core.failure_detection
from core.analytics
    ZScoreAnomalyDetector, IsolationForestAnomalyDetector, MovingAverageForecaster, ARIMAForecaster, compute_correlation
)

logger = logging.getLogger(__name__)


@dataclass
class TelemetryConfig:
    """Configuration for telemetry processing"""
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


@dataclass
class TelemetryEvent:
    """Represents a telemetry event with metadata"""
    record: TelemetryRecord
    timestamp: datetime
    source_id: str
    event_type: str
    severity: str = "info"
    processed: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AlertRule:
    """Defines alert rules for telemetry data"""
    rule_id: str
    name: str
    condition: str  # "threshold", "trend", "pattern", "anomaly"
    parameters: Dict[str, Any]
    severity: str = "warning"
    enabled: bool = True
    actions: List[str] = field(default_factory=list)  # List of action names to trigger


class TelemetryProcessor:
    """Processes telemetry data in real-time"""
    
    def __init__(self, config: TelemetryConfig):
        self.config = config
        self.buffer = TelemetryBuffer(max_size=config.buffer_size)
        self.failure_detector = FailureDetectionSystem()
        self.ingestor = TelemetryIngestor(self.buffer)
        
        # Event tracking
        self.events: List[TelemetryEvent] = []
        self.alerts: List[Dict[str, Any]] = []
        self.dashboard_data: Dict[str, Any] = {
            'last_update': datetime.now().isoformat(),
            'total_events': 0,
            'active_alerts': 0,
            'system_status': 'healthy'
        }
        
        # Processing state
        self.running = False
        self.processing_thread = None
        self.alert_rules: Dict[str, AlertRule] = {}
        self.action_handlers: Dict[str, Callable] = {}
        
        # Data storage
        self.data_history: Dict[str, List[TelemetryRecord]] = {}
        self.pattern_history: List[FailurePattern] = []
        self.risk_history: List[RiskAssessment] = []
        
        # Subscribers for real-time updates
        self.subscribers: Set[Callable] = set()
        
        # Analytics modules
        self.anomaly_detectors = {
            'zscore': ZScoreAnomalyDetector(),
        }
        if IsolationForestAnomalyDetector.__name__ in globals():
            try:
                self.anomaly_detectors['isolation_forest'] = IsolationForestAnomalyDetector()
            except Exception:
                pass
        self.forecasters = {
            'moving_average': MovingAverageForecaster(),
        }
        if ARIMAForecaster.__name__ in globals():
            try:
                self.forecasters['arima'] = ARIMAForecaster()
            except Exception:
                pass
        # Analytics results
        self.analytics_results: Dict[str, Dict[str, Any]] = {}
        
        # Initialize default alert rules
        self._initialize_default_rules()
        self._initialize_action_handlers()
    
    def _initialize_default_rules(self):
        """Initialize default alert rules"""
        self.add_alert_rule(AlertRule(
            rule_id="high_temperature",
            name="High Temperature Alert",
            condition="threshold",
            parameters={"field": "temperature", "operator": ">", "value": 80.0},
            severity="critical",
            actions=["log_alert", "send_notification"]
        ))
        
        self.add_alert_rule(AlertRule(
            rule_id="pressure_spike",
            name="Pressure Spike Alert",
            condition="trend",
            parameters={"field": "pressure", "window": 10, "threshold": 0.5},
            severity="warning",
            actions=["log_alert"]
        ))
        
        self.add_alert_rule(AlertRule(
            rule_id="vibration_anomaly",
            name="Vibration Anomaly Alert",
            condition="anomaly",
            parameters={"field": "vibration", "sensitivity": 0.8},
            severity="warning",
            actions=["log_alert", "trigger_inspection"]
        ))
    
    def _initialize_action_handlers(self):
        """Initialize default action handlers"""
        self.register_action("log_alert", self._log_alert)
        self.register_action("send_notification", self._send_notification)
        self.register_action("trigger_inspection", self._trigger_inspection)
        self.register_action("update_dashboard", self._update_dashboard)
    
    def start(self):
        """Start the telemetry processor"""
        if self.running:
            logger.warning("Telemetry processor is already running")
            return
        
        self.running = True
        self.buffer.start()
        
        # Start processing thread
        self.processing_thread = threading.Thread(target=self._processing_loop, daemon=True)
        self.processing_thread.start()
        
        # Add buffer listener
        self.buffer.add_listener(self._on_telemetry_received)
        
        logger.info("Telemetry processor started")
    
    def stop(self):
        """Stop the telemetry processor"""
        if not self.running:
            return
        
        self.running = False
        self.buffer.stop()
        
        if self.processing_thread:
            self.processing_thread.join()
        
        logger.info("Telemetry processor stopped")
    
    def _processing_loop(self):
        """Main processing loop"""
        while self.running:
            try:
                # Process pending events
                self._process_events()
                
                # Update dashboard data
                self._update_dashboard_data()
                
                # Notify subscribers
                self._notify_subscribers()
                
                time.sleep(self.config.processing_interval)
            
            except Exception as e:
                logger.error(f"Error in processing loop: {e}")
                time.sleep(1.0)
    
    def _on_telemetry_received(self, record: TelemetryRecord):
        """Handle incoming telemetry data"""
        try:
            # Create telemetry event
            event = TelemetryEvent(
                record=record,
                timestamp=datetime.now(),
                source_id=record.source,
                event_type="telemetry"
            )
            
            # Add to events list
            self.events.append(event)
            
            # Store in data history
            if record.source not in self.data_history:
                self.data_history[record.source] = []
            self.data_history[record.source].append(record)
            
            # Limit history size
            if len(self.data_history[record.source]) > self.config.max_history_size:
                self.data_history[record.source] = self.data_history[record.source][-self.config.max_history_size:]
            
            # Check alert rules
            self._check_alert_rules(event)
            
            # Run analytics for this type
            self._run_analytics(record.type)
            
            # Mark as processed
            event.processed = True
            
        except Exception as e:
            logger.error(f"Error processing telemetry record: {e}")
    
    def _process_events(self):
        """Process pending events"""
        # Process recent events for pattern detection
        recent_events = [e for e in self.events if not e.processed]
        
        if recent_events:
            # Group by source
            events_by_source = {}
            for event in recent_events:
                if event.source_id not in events_by_source:
                    events_by_source[event.source_id] = []
                events_by_source[event.source_id].append(event.record)
            
            # Process each source
            for source_id, records in events_by_source.items():
                if len(records) >= 10:  # Need sufficient data for analysis
                    self._analyze_source_data(source_id, records)
    
    def _analyze_source_data(self, source_id: str, records: List[TelemetryRecord]):
        """Analyze data for a specific source"""
        try:
            # Convert records to data format for failure detection
            data = self._records_to_data(records)
            
            # Run failure detection analysis
            patterns = self.failure_detector.process_telemetry_data(data, source_id)
            
            # Store patterns
            self.pattern_history.extend(patterns)
            
            # Generate alerts for significant patterns
            for pattern in patterns:
                if pattern.confidence > self.config.alert_threshold:
                    alert = {
                        'id': f"pattern_{pattern.pattern_id}",
                        'type': 'pattern_detected',
                        'source': source_id,
                        'pattern_type': pattern.failure_type.value,
                        'confidence': pattern.confidence,
                        'severity': pattern.severity,
                        'description': pattern.description,
                        'timestamp': datetime.now().isoformat()
                    }
                    self.alerts.append(alert)
                    
                    # Trigger actions
                    self._trigger_actions(alert)
        
        except Exception as e:
            logger.error(f"Error analyzing source data for {source_id}: {e}")
    
    def _records_to_data(self, records: List[TelemetryRecord]):
        """Convert telemetry records to data format for analysis"""
        # Group by type
        data_by_type = {}
        for record in records:
            if record.type not in data_by_type:
                data_by_type[record.type] = []
            data_by_type[record.type].append(record.value)
        
        # Create simple data structure
        data = {}
        for data_type, values in data_by_type.items():
            data[data_type] = values
        
        return data
    
    def _check_alert_rules(self, event: TelemetryEvent):
        """Check alert rules against telemetry event"""
        for rule in self.alert_rules.values():
            if not rule.enabled:
                continue
            
            try:
                if self._evaluate_rule(rule, event):
                    alert = {
                        'id': f"rule_{rule.rule_id}_{int(time.time())}",
                        'type': 'rule_triggered',
                        'rule_name': rule.name,
                        'source': event.source_id,
                        'severity': rule.severity,
                        'description': f"Alert rule '{rule.name}' triggered",
                        'timestamp': datetime.now().isoformat(),
                        'event_data': {
                            'type': event.record.type,
                            'value': event.record.value,
                            'status': event.record.status
                        }
                    }
                    
                    self.alerts.append(alert)
                    
                    # Trigger actions
                    self._trigger_actions(alert, rule.actions)
            
            except Exception as e:
                logger.error(f"Error checking alert rule {rule.rule_id}: {e}")
    
    def _evaluate_rule(self, rule: AlertRule, event: TelemetryEvent) -> bool:
        """Evaluate if an alert rule is triggered"""
        if rule.condition == "threshold":
            return self._evaluate_threshold_rule(rule, event)
        elif rule.condition == "trend":
            return self._evaluate_trend_rule(rule, event)
        elif rule.condition == "anomaly":
            return self._evaluate_anomaly_rule(rule, event)
        else:
            return False
    
    def _evaluate_threshold_rule(self, rule: AlertRule, event: TelemetryEvent) -> bool:
        """Evaluate threshold-based rule"""
        field = rule.parameters.get("field")
        operator = rule.parameters.get("operator")
        value = rule.parameters.get("value")
        
        if event.record.type != field:
            return False
        
        if operator == ">":
            return event.record.value > value
        elif operator == "<":
            return event.record.value < value
        elif operator == ">=":
            return event.record.value >= value
        elif operator == "<=":
            return event.record.value <= value
        elif operator == "==":
            return event.record.value == value
        else:
            return False
    
    def _evaluate_trend_rule(self, rule: AlertRule, event: TelemetryEvent) -> bool:
        """Evaluate trend-based rule"""
        field = rule.parameters.get("field")
        window = rule.parameters.get("window", 10)
        threshold = rule.parameters.get("threshold", 0.5)
        
        if event.record.type != field:
            return False
        
        # Get recent data for this field
        recent_data = []
        for e in self.events[-window:]:
            if e.record.type == field:
                recent_data.append(e.record.value)
        
        if len(recent_data) < window:
            return False
        
        # Calculate trend
        x = np.arange(len(recent_data))
        y = np.array(recent_data)
        slope = np.polyfit(x, y, 1)[0]
        
        return abs(slope) > threshold
    
    def _evaluate_anomaly_rule(self, rule: AlertRule, event: TelemetryEvent) -> bool:
        """Evaluate anomaly-based rule"""
        field = rule.parameters.get("field")
        sensitivity = rule.parameters.get("sensitivity", 0.8)
        
        if event.record.type != field:
            return False
        
        # Simple anomaly detection based on statistical outliers
        recent_data = []
        for e in self.events[-100:]:  # Use last 100 events
            if e.record.type == field:
                recent_data.append(e.record.value)
        
        if len(recent_data) < 10:
            return False
        
        mean = np.mean(recent_data)
        std = np.std(recent_data)
        
        if std == 0:
            return False
        
        z_score = abs(event.record.value - mean) / std
        return z_score > (2.0 / sensitivity)  # Adjust threshold based on sensitivity
    
    def _trigger_actions(self, alert: Dict[str, Any], actions: List[str] = None):
        """Trigger actions for an alert"""
        if actions is None:
            actions = ["log_alert", "update_dashboard"]
        
        for action_name in actions:
            if action_name in self.action_handlers:
                try:
                    self.action_handlers[action_name](alert)
                except Exception as e:
                    logger.error(f"Error executing action {action_name}: {e}")
    
    def _log_alert(self, alert: Dict[str, Any]):
        """Log alert action"""
        logger.warning(f"ALERT: {alert['description']} - {alert['severity'].upper()}")
    
    def _send_notification(self, alert: Dict[str, Any]):
        """Send notification action"""
        # Placeholder for notification system
        logger.info(f"NOTIFICATION: {alert['description']}")
    
    def _trigger_inspection(self, alert: Dict[str, Any]):
        """Trigger inspection action"""
        logger.info(f"INSPECTION TRIGGERED: {alert['description']}")
    
    def _update_dashboard(self, alert: Dict[str, Any]):
        """Update dashboard action"""
        # Dashboard updates are handled in the main processing loop
        pass
    
    def _run_analytics(self, data_type: str, sensitivity: float = 0.8):
        """Run analytics (anomaly detection, forecasting) for a given data type"""
        # Gather recent data
        values = []
        for events in self.data_history.values():
            for rec in events:
                if rec.type == data_type:
                    values.append(rec.value)
        if not values:
            return
        # Anomaly detection
        anomalies = {}
        for name, detector in self.anomaly_detectors.items():
            try:
                anomalies[name] = detector.detect(values, sensitivity=sensitivity)
            except Exception:
                anomalies[name] = []
        # Forecasting
        forecasts = {}
        for name, forecaster in self.forecasters.items():
            try:
                forecasts[name] = forecaster.forecast(values, steps=5)
            except Exception:
                forecasts[name] = []
        # Store results
        self.analytics_results[data_type] = {
            'anomalies': anomalies,
            'forecasts': forecasts,
            'last_run': datetime.now().isoformat(),
        }
    
    def _update_dashboard_data(self):
        """Update dashboard data"""
        self.dashboard_data.update({
            'last_update': datetime.now().isoformat(),
            'total_events': len(self.events),
            'active_alerts': len([a for a in self.alerts if a.get('severity') in ['critical', 'warning']]),
            'system_status': 'healthy' if len(self.alerts) == 0 else 'warning',
            'recent_alerts': self.alerts[-10:],  # Last 10 alerts
            'pattern_count': len(self.pattern_history),
            'risk_assessments': len(self.risk_history),
            'analytics': self.analytics_results
        })
    
    def _notify_subscribers(self):
        """Notify subscribers of updates"""
        for subscriber in self.subscribers:
            try:
                subscriber(self.dashboard_data)
            except Exception as e:
                logger.error(f"Error notifying subscriber: {e}")
    
    def add_alert_rule(self, rule: AlertRule):
        """Add an alert rule"""
        self.alert_rules[rule.rule_id] = rule
        logger.info(f"Added alert rule: {rule.name}")
    
    def remove_alert_rule(self, rule_id: str):
        """Remove an alert rule"""
        if rule_id in self.alert_rules:
            del self.alert_rules[rule_id]
            logger.info(f"Removed alert rule: {rule_id}")
    
    def register_action(self, action_name: str, handler: Callable):
        """Register an action handler"""
        self.action_handlers[action_name] = handler
        logger.info(f"Registered action handler: {action_name}")
    
    def subscribe(self, callback: Callable):
        """Subscribe to real-time updates"""
        self.subscribers.add(callback)
    
    def unsubscribe(self, callback: Callable):
        """Unsubscribe from real-time updates"""
        self.subscribers.discard(callback)
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get current dashboard data"""
        return self.dashboard_data.copy()
    
    def get_alerts(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent alerts"""
        return self.alerts[-limit:]
    
    def get_patterns(self, limit: int = 100) -> List[FailurePattern]:
        """Get recent patterns"""
        return self.pattern_history[-limit:]
    
    def get_analytics_results(self, data_type: str = None) -> Dict[str, Any]:
        """Get analytics results for a data type or all types"""
        if data_type:
            return self.analytics_results.get(data_type, {})
        return self.analytics_results.copy()
    
    def ingest_data(self, data: Dict[str, Any]):
        """Ingest data from external sources"""
        try:
            record = TelemetryRecord(**data)
            self.buffer.ingest(record)
        except Exception as e:
            logger.error(f"Error ingesting data: {e}")


class RealtimeTelemetryServer:
    """WebSocket and HTTP server for real-time telemetry"""
    
    def __init__(self, processor: TelemetryProcessor, config: TelemetryConfig):
        self.processor = processor
        self.config = config
        self.websocket_clients: Set[websockets.WebSocketServerProtocol] = set()
        self.http_app = web.Application()
        self.setup_routes()
    
    def setup_routes(self):
        """Setup HTTP routes"""
        self.http_app.router.add_post('/telemetry', self.handle_telemetry)
        self.http_app.router.add_get('/dashboard', self.handle_dashboard)
        self.http_app.router.add_get('/alerts', self.handle_alerts)
        self.http_app.router.add_get('/patterns', self.handle_patterns)
        self.http_app.router.add_get('/health', self.handle_health)
    
    async def handle_telemetry(self, request):
        """Handle telemetry data ingestion"""
        try:
            data = await request.json()
            self.processor.ingest_data(data)
            return web.json_response({'status': 'success'})
        except Exception as e:
            logger.error(f"Error handling telemetry: {e}")
            return web.json_response({'status': 'error', 'message': str(e)}, status=500)
    
    async def handle_dashboard(self, request):
        """Handle dashboard data requests"""
        try:
            data = self.processor.get_dashboard_data()
            return web.json_response(data)
        except Exception as e:
            logger.error(f"Error handling dashboard request: {e}")
            return web.json_response({'status': 'error', 'message': str(e)}, status=500)
    
    async def handle_alerts(self, request):
        """Handle alerts requests"""
        try:
            limit = int(request.query.get('limit', 100))
            alerts = self.processor.get_alerts(limit)
            return web.json_response(alerts)
        except Exception as e:
            logger.error(f"Error handling alerts request: {e}")
            return web.json_response({'status': 'error', 'message': str(e)}, status=500)
    
    async def handle_patterns(self, request):
        """Handle patterns requests"""
        try:
            limit = int(request.query.get('limit', 100))
            patterns = self.processor.get_patterns(limit)
            return web.json_response([p.__dict__ for p in patterns])
        except Exception as e:
            logger.error(f"Error handling patterns request: {e}")
            return web.json_response({'status': 'error', 'message': str(e)}, status=500)
    
    async def handle_health(self, request):
        """Handle health check requests"""
        return web.json_response({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'processor_running': self.processor.running
        })
    
    async def websocket_handler(self, websocket, path):
        """Handle WebSocket connections"""
        self.websocket_clients.add(websocket)
        try:
            async for message in websocket:
                try:
                    data = json.loads(message)
                    if data.get('type') == 'telemetry':
                        self.processor.ingest_data(data.get('data', {}))
                    elif data.get('type') == 'subscribe':
                        # Subscribe to updates
                        pass
                except json.JSONDecodeError:
                    logger.warning("Invalid JSON received via WebSocket")
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            self.websocket_clients.discard(websocket)
    
    async def broadcast_update(self, data: Dict[str, Any]):
        """Broadcast update to all WebSocket clients"""
        if not self.websocket_clients:
            return
        
        message = json.dumps(data)
        await asyncio.gather(
            *[client.send(message) for client in self.websocket_clients],
            return_exceptions=True
        )
    
    async def start_websocket_server(self):
        """Start WebSocket server"""
        if not self.config.enable_websocket:
            return
        
        async with serve(self.websocket_handler, "localhost", self.config.websocket_port):
            logger.info(f"WebSocket server started on port {self.config.websocket_port}")
            await asyncio.Future()  # run forever
    
    async def start_http_server(self):
        """Start HTTP server"""
        if not self.config.enable_http:
            return
        
        runner = web.AppRunner(self.http_app)
        await runner.setup()
        site = web.TCPSite(runner, "localhost", self.config.http_port)
        await site.start()
        logger.info(f"HTTP server started on port {self.config.http_port}")
        
        # Keep server running
        await asyncio.Future()  # run forever
    
    async def start(self):
        """Start all servers"""
        await asyncio.gather(
            self.start_websocket_server(),
            self.start_http_server()
        )


# Utility functions
def create_telemetry_processor(config: TelemetryConfig = None) -> TelemetryProcessor:
    """Create and configure a telemetry processor"""
    if config is None:
        config = TelemetryConfig()
    
    processor = TelemetryProcessor(config)
    return processor


def start_realtime_telemetry(config: TelemetryConfig = None):
    """Start the real-time telemetry system"""
    if config is None:
        config = TelemetryConfig()
    
    processor = create_telemetry_processor(config)
    server = RealtimeTelemetryServer(processor, config)
    
    # Start processor
    processor.start()
    
    # Start servers
    try:
        asyncio.run(server.start())
    except KeyboardInterrupt:
        logger.info("Shutting down real-time telemetry system...")
        processor.stop()


if __name__ == "__main__":
    # Example usage
    config = TelemetryConfig(
        buffer_size=5000,
        processing_interval=0.5,
        alert_threshold=0.7,
        enable_websocket=True,
        websocket_port=8765,
        enable_http=True,
        http_port=8080
    )
    
    start_realtime_telemetry(config) 