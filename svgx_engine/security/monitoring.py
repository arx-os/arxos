"""
Security Monitoring and Audit Logging for Arxos.

This module provides comprehensive security monitoring including:
- Real-time security event monitoring
- Audit logging and compliance reporting
- Security metrics and analytics
- Incident detection and alerting
"""

import json
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
import logging
from enum import Enum


class SecurityLevel(Enum):
    """Security event severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class EventType(Enum):
    """Security event types."""
    AUTHENTICATION_SUCCESS = "authentication_success"
    AUTHENTICATION_FAILURE = "authentication_failure"
    AUTHORIZATION_SUCCESS = "authorization_success"
    AUTHORIZATION_FAILURE = "authorization_failure"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    THREAT_DETECTED = "threat_detected"
    SECURITY_ERROR = "security_error"
    DATA_ACCESS = "data_access"
    DATA_MODIFICATION = "data_modification"
    CONFIGURATION_CHANGE = "configuration_change"
    SYSTEM_STARTUP = "system_startup"
    SYSTEM_SHUTDOWN = "system_shutdown"


@dataclass
class SecurityEvent:
    """Security event for monitoring and auditing."""
    event_id: str
    event_type: EventType
    severity: SecurityLevel
    timestamp: datetime
    user_id: Optional[str]
    ip_address: str
    session_id: Optional[str]
    resource_type: Optional[str]
    action: Optional[str]
    details: Dict[str, Any]
    threat_indicators: List[str] = None
    correlation_id: Optional[str] = None


@dataclass
class SecurityAlert:
    """Security alert for incident response."""
    alert_id: str
    event_id: str
    alert_type: str
    severity: SecurityLevel
    timestamp: datetime
    description: str
    affected_users: List[str]
    affected_resources: List[str]
    recommended_actions: List[str]
    status: str = "open"


class SecurityMonitor:
    """Real-time security monitoring service."""
    
    def __init__(self, alert_thresholds: Dict[str, int] = None):
        self.alert_thresholds = alert_thresholds or {
            'failed_logins_per_minute': 5,
            'threats_per_minute': 3,
            'rate_limit_violations_per_minute': 10,
            'authorization_failures_per_minute': 5
        }
        
        self.events = deque(maxlen=10000)  # Keep last 10k events
        self.alerts = deque(maxlen=1000)   # Keep last 1k alerts
        self.metrics = defaultdict(int)
        self.alert_handlers = []
        self.lock = threading.Lock()
        
        # Start monitoring thread
        self.monitoring_active = True
        self.monitor_thread = threading.Thread(target=self._monitor_events, daemon=True)
        self.monitor_thread.start()
    
    def log_event(self, event: SecurityEvent):
        """Log a security event."""
        with self.lock:
            self.events.append(event)
            
            # Update metrics
            metric_key = f"{event.event_type.value}_{event.severity.value}"
            self.metrics[metric_key] += 1
            self.metrics[f"total_{event.severity.value}"] += 1
        
        # Check for immediate alerts
        self._check_immediate_alerts(event)
    
    def _check_immediate_alerts(self, event: SecurityEvent):
        """Check for immediate security alerts."""
        if event.severity in [SecurityLevel.HIGH, SecurityLevel.CRITICAL]:
            alert = SecurityAlert(
                alert_id=f"alert_{int(time.time())}",
                event_id=event.event_id,
                alert_type="immediate",
                severity=event.severity,
                timestamp=datetime.utcnow(),
                description=f"High severity security event: {event.event_type.value}",
                affected_users=[event.user_id] if event.user_id else [],
                affected_resources=[event.resource_type] if event.resource_type else [],
                recommended_actions=self._get_recommended_actions(event)
            )
            
            with self.lock:
                self.alerts.append(alert)
            
            # Trigger alert handlers
            self._trigger_alert_handlers(alert)
    
    def _get_recommended_actions(self, event: SecurityEvent) -> List[str]:
        """Get recommended actions for security event."""
        actions = []
        
        if event.event_type == EventType.AUTHENTICATION_FAILURE:
            actions.extend([
                "Review failed login attempts",
                "Check for brute force attacks",
                "Consider implementing account lockout"
            ])
        
        elif event.event_type == EventType.THREAT_DETECTED:
            actions.extend([
                "Block suspicious IP addresses",
                "Review security logs",
                "Update threat detection rules"
            ])
        
        elif event.event_type == EventType.AUTHORIZATION_FAILURE:
            actions.extend([
                "Review user permissions",
                "Check for privilege escalation attempts",
                "Audit access control policies"
            ])
        
        return actions
    
    def _monitor_events(self):
        """Background monitoring thread."""
        while self.monitoring_active:
            try:
                self._check_threshold_alerts()
                time.sleep(60)  # Check every minute
            except Exception as e:
                logging.error(f"Error in security monitoring: {e}")
    
    def _check_threshold_alerts(self):
        """Check for threshold-based alerts."""
        current_time = datetime.utcnow()
        one_minute_ago = current_time - timedelta(minutes=1)
        
        # Count recent events
        recent_events = [
            event for event in self.events
            if event.timestamp >= one_minute_ago
        ]
        
        # Group by event type
        event_counts = defaultdict(int)
        for event in recent_events:
            event_counts[event.event_type.value] += 1
        
        # Check thresholds
        for threshold_name, threshold_value in self.alert_thresholds.items():
            if threshold_name in event_counts:
                if event_counts[threshold_name] >= threshold_value:
                    alert = SecurityAlert(
                        alert_id=f"threshold_{int(time.time())}",
                        event_id="",
                        alert_type="threshold_exceeded",
                        severity=SecurityLevel.MEDIUM,
                        timestamp=current_time,
                        description=f"Threshold exceeded: {threshold_name}",
                        affected_users=[],
                        affected_resources=[],
                        recommended_actions=[
                            "Review recent security events",
                            "Adjust threshold if necessary",
                            "Investigate root cause"
                        ]
                    )
                    
                    with self.lock:
                        self.alerts.append(alert)
                    
                    self._trigger_alert_handlers(alert)
    
    def add_alert_handler(self, handler: Callable[[SecurityAlert], None]):
        """Add alert handler for custom alert processing."""
        self.alert_handlers.append(handler)
    
    def _trigger_alert_handlers(self, alert: SecurityAlert):
        """Trigger all alert handlers."""
        for handler in self.alert_handlers:
            try:
                handler(alert)
            except Exception as e:
                logging.error(f"Error in alert handler: {e}")
    
    def get_security_metrics(self, time_window: timedelta = timedelta(hours=1)) -> Dict[str, Any]:
        """Get security metrics for the specified time window."""
        cutoff_time = datetime.utcnow() - time_window
        
        with self.lock:
            recent_events = [
                event for event in self.events
                if event.timestamp >= cutoff_time
            ]
        
        metrics = {
            'total_events': len(recent_events),
            'events_by_type': defaultdict(int),
            'events_by_severity': defaultdict(int),
            'unique_users': set(),
            'unique_ips': set(),
            'threat_indicators': defaultdict(int)
        }
        
        for event in recent_events:
            metrics['events_by_type'][event.event_type.value] += 1
            metrics['events_by_severity'][event.severity.value] += 1
            
            if event.user_id:
                metrics['unique_users'].add(event.user_id)
            
            metrics['unique_ips'].add(event.ip_address)
            
            if event.threat_indicators:
                for indicator in event.threat_indicators:
                    metrics['threat_indicators'][indicator] += 1
        
        # Convert sets to counts
        metrics['unique_users'] = len(metrics['unique_users'])
        metrics['unique_ips'] = len(metrics['unique_ips'])
        metrics['events_by_type'] = dict(metrics['events_by_type'])
        metrics['events_by_severity'] = dict(metrics['events_by_severity'])
        metrics['threat_indicators'] = dict(metrics['threat_indicators'])
        
        return metrics
    
    def get_recent_alerts(self, limit: int = 100) -> List[SecurityAlert]:
        """Get recent security alerts."""
        with self.lock:
            return list(self.alerts)[-limit:]
    
    def stop_monitoring(self):
        """Stop the monitoring thread."""
        self.monitoring_active = False
        if self.monitor_thread.is_alive():
            self.monitor_thread.join()


class AuditLogger:
    """Comprehensive audit logging for compliance."""
    
    def __init__(self, log_file: str = "audit.log"):
        self.log_file = log_file
        self.logger = logging.getLogger('audit')
        self.logger.setLevel(logging.INFO)
        
        # Create file handler
        handler = logging.FileHandler(log_file)
        handler.setFormatter(logging.Formatter(
            '%(asctime)s | %(levelname)s | %(message)s'
        ))
        self.logger.addHandler(handler)
    
    def log_authentication(self, user_id: str, success: bool, ip_address: str, 
                          details: Dict[str, Any] = None):
        """Log authentication events."""
        event_type = "AUTH_SUCCESS" if success else "AUTH_FAILURE"
        message = f"{event_type} | User: {user_id} | IP: {ip_address}"
        
        if details:
            message += f" | Details: {json.dumps(details)}"
        
        self.logger.info(message)
    
    def log_authorization(self, user_id: str, resource: str, action: str, 
                         success: bool, details: Dict[str, Any] = None):
        """Log authorization events."""
        event_type = "AUTHZ_SUCCESS" if success else "AUTHZ_FAILURE"
        message = f"{event_type} | User: {user_id} | Resource: {resource} | Action: {action}"
        
        if details:
            message += f" | Details: {json.dumps(details)}"
        
        self.logger.info(message)
    
    def log_data_access(self, user_id: str, data_type: str, action: str, 
                       record_count: int = None, details: Dict[str, Any] = None):
        """Log data access events."""
        message = f"DATA_ACCESS | User: {user_id} | Type: {data_type} | Action: {action}"
        
        if record_count is not None:
            message += f" | Records: {record_count}"
        
        if details:
            message += f" | Details: {json.dumps(details)}"
        
        self.logger.info(message)
    
    def log_configuration_change(self, user_id: str, component: str, 
                                change_type: str, details: Dict[str, Any] = None):
        """Log configuration change events."""
        message = f"CONFIG_CHANGE | User: {user_id} | Component: {component} | Type: {change_type}"
        
        if details:
            message += f" | Details: {json.dumps(details)}"
        
        self.logger.info(message)
    
    def log_system_event(self, event_type: str, details: Dict[str, Any] = None):
        """Log system events."""
        message = f"SYSTEM_EVENT | Type: {event_type}"
        
        if details:
            message += f" | Details: {json.dumps(details)}"
        
        self.logger.info(message)
    
    def get_audit_trail(self, start_time: datetime, end_time: datetime, 
                        user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get audit trail for compliance reporting."""
        audit_entries = []
        
        try:
            with open(self.log_file, 'r') as f:
                for line in f:
                    try:
                        # Parse log entry
                        parts = line.strip().split(' | ')
                        if len(parts) >= 3:
                            timestamp_str = parts[0]
                            level = parts[1]
                            message = ' | '.join(parts[2:])
                            
                            timestamp = datetime.fromisoformat(timestamp_str.replace(',', '.'))
                            
                            # Filter by time range
                            if start_time <= timestamp <= end_time:
                                # Filter by user if specified
                                if user_id is None or user_id in message:
                                    audit_entries.append({
                                        'timestamp': timestamp,
                                        'level': level,
                                        'message': message
                                    })
                    except Exception:
                        continue
        except FileNotFoundError:
            pass
        
        return audit_entries


class ComplianceReporter:
    """Compliance reporting for regulatory requirements."""
    
    def __init__(self, audit_logger: AuditLogger):
        self.audit_logger = audit_logger
    
    def generate_gdpr_report(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Generate GDPR compliance report."""
        audit_trail = self.audit_logger.get_audit_trail(start_date, end_date)
        
        report = {
            'report_type': 'GDPR_Compliance',
            'period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat()
            },
            'data_access_events': [],
            'data_modification_events': [],
            'user_consent_events': [],
            'data_deletion_events': [],
            'summary': {
                'total_events': len(audit_trail),
                'unique_users': set(),
                'data_access_count': 0,
                'data_modification_count': 0
            }
        }
        
        for entry in audit_trail:
            if 'DATA_ACCESS' in entry['message']:
                report['data_access_events'].append(entry)
                report['summary']['data_access_count'] += 1
            elif 'DATA_MODIFICATION' in entry['message']:
                report['data_modification_events'].append(entry)
                report['summary']['data_modification_count'] += 1
            
            # Extract user ID from message
            if 'User:' in entry['message']:
                user_id = entry['message'].split('User:')[1].split('|')[0].strip()
                report['summary']['unique_users'].add(user_id)
        
        report['summary']['unique_users'] = len(report['summary']['unique_users'])
        
        return report
    
    def generate_hipaa_report(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Generate HIPAA compliance report."""
        audit_trail = self.audit_logger.get_audit_trail(start_date, end_date)
        
        report = {
            'report_type': 'HIPAA_Compliance',
            'period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat()
            },
            'phi_access_events': [],
            'authentication_events': [],
            'authorization_events': [],
            'summary': {
                'total_events': len(audit_trail),
                'phi_access_count': 0,
                'failed_authentications': 0,
                'failed_authorizations': 0
            }
        }
        
        for entry in audit_trail:
            if 'PHI' in entry['message'] or 'health' in entry['message'].lower():
                report['phi_access_events'].append(entry)
                report['summary']['phi_access_count'] += 1
            elif 'AUTH_FAILURE' in entry['message']:
                report['authentication_events'].append(entry)
                report['summary']['failed_authentications'] += 1
            elif 'AUTHZ_FAILURE' in entry['message']:
                report['authorization_events'].append(entry)
                report['summary']['failed_authorizations'] += 1
        
        return report
    
    def generate_soc2_report(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Generate SOC2 compliance report."""
        audit_trail = self.audit_logger.get_audit_trail(start_date, end_date)
        
        report = {
            'report_type': 'SOC2_Compliance',
            'period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat()
            },
            'security_events': [],
            'access_control_events': [],
            'system_events': [],
            'summary': {
                'total_events': len(audit_trail),
                'security_incidents': 0,
                'access_violations': 0,
                'system_changes': 0
            }
        }
        
        for entry in audit_trail:
            if 'SECURITY' in entry['message'] or 'THREAT' in entry['message']:
                report['security_events'].append(entry)
                report['summary']['security_incidents'] += 1
            elif 'AUTHZ_FAILURE' in entry['message']:
                report['access_control_events'].append(entry)
                report['summary']['access_violations'] += 1
            elif 'CONFIG_CHANGE' in entry['message'] or 'SYSTEM_EVENT' in entry['message']:
                report['system_events'].append(entry)
                report['summary']['system_changes'] += 1
        
        return report 