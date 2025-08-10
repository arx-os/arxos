"""
Comprehensive Security Audit Logging System.

Provides detailed audit trails, security event logging, and compliance
reporting for security-sensitive operations.
"""

import json
import time
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from enum import Enum
import threading
from queue import Queue
import hashlib
import hmac

from infrastructure.logging.structured_logging import get_logger
from infrastructure.error_handling import SecurityError


logger = get_logger(__name__)


class AuditEventType(Enum):
    """Types of audit events."""
    # Authentication events
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILED = "login_failed"
    LOGOUT = "logout"
    PASSWORD_CHANGED = "password_changed"
    TOKEN_ISSUED = "token_issued"
    TOKEN_REVOKED = "token_revoked"
    
    # Authorization events
    ACCESS_GRANTED = "access_granted"
    ACCESS_DENIED = "access_denied"
    PERMISSION_CHANGED = "permission_changed"
    ROLE_ASSIGNED = "role_assigned"
    ROLE_REVOKED = "role_revoked"
    
    # Data events
    DATA_CREATED = "data_created"
    DATA_READ = "data_read"
    DATA_UPDATED = "data_updated"
    DATA_DELETED = "data_deleted"
    DATA_EXPORTED = "data_exported"
    DATA_IMPORTED = "data_imported"
    
    # Security events
    SECURITY_VIOLATION = "security_violation"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    BRUTE_FORCE_ATTEMPT = "brute_force_attempt"
    INJECTION_ATTEMPT = "injection_attempt"
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    
    # System events
    SYSTEM_STARTUP = "system_startup"
    SYSTEM_SHUTDOWN = "system_shutdown"
    CONFIGURATION_CHANGED = "configuration_changed"
    BACKUP_CREATED = "backup_created"
    BACKUP_RESTORED = "backup_restored"
    
    # Administrative events
    USER_CREATED = "user_created"
    USER_DELETED = "user_deleted"
    USER_SUSPENDED = "user_suspended"
    USER_ACTIVATED = "user_activated"
    ADMIN_ACTION = "admin_action"


class AuditSeverity(Enum):
    """Severity levels for audit events."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ComplianceStandard(Enum):
    """Compliance standards for audit requirements."""
    SOX = "sarbanes_oxley"
    HIPAA = "hipaa"
    GDPR = "gdpr"
    PCI_DSS = "pci_dss"
    SOC2 = "soc2"
    ISO27001 = "iso27001"


@dataclass
class AuditEvent:
    """Structured audit event."""
    event_id: str
    event_type: AuditEventType
    timestamp: datetime
    user_id: Optional[str]
    session_id: Optional[str]
    source_ip: Optional[str]
    user_agent: Optional[str]
    resource_type: Optional[str]
    resource_id: Optional[str]
    action: str
    result: str  # SUCCESS, FAILURE, ERROR
    severity: AuditSeverity
    details: Dict[str, Any]
    compliance_tags: List[ComplianceStandard]
    
    # Security fields
    checksum: Optional[str] = None
    signature: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = asdict(self)
        
        # Convert enums to values
        data['event_type'] = self.event_type.value
        data['severity'] = self.severity.value
        data['compliance_tags'] = [tag.value for tag in self.compliance_tags]
        data['timestamp'] = self.timestamp.isoformat()
        
        return data
    
    def calculate_checksum(self, secret_key: bytes) -> str:
        """Calculate integrity checksum for tamper detection."""
        # Create deterministic string representation
        checksum_data = {
            'event_id': self.event_id,
            'event_type': self.event_type.value,
            'timestamp': self.timestamp.isoformat(),
            'user_id': self.user_id,
            'action': self.action,
            'result': self.result,
            'details': json.dumps(self.details, sort_keys=True)
        }
        
        data_string = json.dumps(checksum_data, sort_keys=True)
        
        # Calculate HMAC-SHA256
        signature = hmac.new(
            secret_key,
            data_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        return signature


class AuditLogger:
    """Main audit logging system."""
    
    def __init__(self, secret_key: Optional[bytes] = None, 
                 integrity_check: bool = True):
        self.secret_key = secret_key or self._generate_secret_key()
        self.integrity_check = integrity_check
        self.event_queue = Queue()
        self.background_processor = None
        self.is_running = False
        
        # Event counters for monitoring
        self.event_counters = {event_type: 0 for event_type in AuditEventType}
        self.severity_counters = {severity: 0 for severity in AuditSeverity}
        
        # Compliance mapping
        self.compliance_mapping = self._initialize_compliance_mapping()
        
        self.start_background_processing()
    
    def _generate_secret_key(self) -> bytes:
        """Generate secret key for integrity checking."""
        import secrets
        return secrets.token_bytes(32)
    
    def _initialize_compliance_mapping(self) -> Dict[AuditEventType, List[ComplianceStandard]]:
        """Initialize compliance standard mappings for event types."""
        return {
            # Authentication events - required by most standards
            AuditEventType.LOGIN_SUCCESS: [ComplianceStandard.SOX, ComplianceStandard.HIPAA, 
                                         ComplianceStandard.PCI_DSS, ComplianceStandard.SOC2],
            AuditEventType.LOGIN_FAILED: [ComplianceStandard.SOX, ComplianceStandard.HIPAA,
                                        ComplianceStandard.PCI_DSS, ComplianceStandard.SOC2],
            AuditEventType.PASSWORD_CHANGED: [ComplianceStandard.SOX, ComplianceStandard.HIPAA,
                                            ComplianceStandard.PCI_DSS],
            
            # Data access events - critical for GDPR and HIPAA
            AuditEventType.DATA_READ: [ComplianceStandard.GDPR, ComplianceStandard.HIPAA],
            AuditEventType.DATA_UPDATED: [ComplianceStandard.SOX, ComplianceStandard.GDPR,
                                        ComplianceStandard.HIPAA, ComplianceStandard.SOC2],
            AuditEventType.DATA_DELETED: [ComplianceStandard.SOX, ComplianceStandard.GDPR,
                                        ComplianceStandard.HIPAA, ComplianceStandard.SOC2],
            AuditEventType.DATA_EXPORTED: [ComplianceStandard.GDPR, ComplianceStandard.HIPAA,
                                         ComplianceStandard.SOC2],
            
            # Administrative events
            AuditEventType.USER_CREATED: [ComplianceStandard.SOX, ComplianceStandard.SOC2],
            AuditEventType.USER_DELETED: [ComplianceStandard.SOX, ComplianceStandard.SOC2],
            AuditEventType.PERMISSION_CHANGED: [ComplianceStandard.SOX, ComplianceStandard.SOC2,
                                              ComplianceStandard.PCI_DSS],
            
            # Security events - required by all standards
            AuditEventType.SECURITY_VIOLATION: list(ComplianceStandard),
            AuditEventType.UNAUTHORIZED_ACCESS: list(ComplianceStandard),
            AuditEventType.BRUTE_FORCE_ATTEMPT: [ComplianceStandard.PCI_DSS, ComplianceStandard.SOC2],
        }
    
    def log_event(self, event_type: AuditEventType, 
                 user_id: Optional[str] = None,
                 session_id: Optional[str] = None,
                 source_ip: Optional[str] = None,
                 user_agent: Optional[str] = None,
                 resource_type: Optional[str] = None,
                 resource_id: Optional[str] = None,
                 action: str = "",
                 result: str = "SUCCESS",
                 severity: AuditSeverity = AuditSeverity.INFO,
                 details: Optional[Dict[str, Any]] = None) -> str:
        """Log an audit event."""
        
        import uuid
        event_id = str(uuid.uuid4())
        
        # Get compliance tags for this event type
        compliance_tags = self.compliance_mapping.get(event_type, [])
        
        # Create audit event
        audit_event = AuditEvent(
            event_id=event_id,
            event_type=event_type,
            timestamp=datetime.now(timezone.utc),
            user_id=user_id,
            session_id=session_id,
            source_ip=source_ip,
            user_agent=user_agent,
            resource_type=resource_type,
            resource_id=resource_id,
            action=action,
            result=result,
            severity=severity,
            details=details or {},
            compliance_tags=compliance_tags
        )
        
        # Add integrity checking
        if self.integrity_check:
            audit_event.checksum = audit_event.calculate_checksum(self.secret_key)
        
        # Update counters
        self.event_counters[event_type] += 1
        self.severity_counters[severity] += 1
        
        # Queue for background processing
        self.event_queue.put(audit_event)
        
        # Also log immediately to standard logger for real-time monitoring
        logger.info("Audit event", extra={
            "audit_event_id": event_id,
            "audit_event_type": event_type.value,
            "audit_user_id": user_id,
            "audit_action": action,
            "audit_result": result,
            "audit_severity": severity.value
        })
        
        return event_id
    
    def log_authentication_event(self, event_type: AuditEventType, user_id: str,
                               source_ip: str, user_agent: str, result: str,
                               details: Optional[Dict[str, Any]] = None) -> str:
        """Log authentication-specific event."""
        severity = AuditSeverity.INFO if result == "SUCCESS" else AuditSeverity.WARNING
        
        return self.log_event(
            event_type=event_type,
            user_id=user_id,
            source_ip=source_ip,
            user_agent=user_agent,
            action=f"authenticate_{event_type.value}",
            result=result,
            severity=severity,
            details=details
        )
    
    def log_data_access_event(self, event_type: AuditEventType, user_id: str,
                            resource_type: str, resource_id: str, action: str,
                            result: str = "SUCCESS",
                            details: Optional[Dict[str, Any]] = None) -> str:
        """Log data access event."""
        severity = AuditSeverity.INFO
        
        # Elevate severity for sensitive operations
        if event_type in [AuditEventType.DATA_DELETED, AuditEventType.DATA_EXPORTED]:
            severity = AuditSeverity.WARNING
        
        if result != "SUCCESS":
            severity = AuditSeverity.ERROR
        
        return self.log_event(
            event_type=event_type,
            user_id=user_id,
            resource_type=resource_type,
            resource_id=resource_id,
            action=action,
            result=result,
            severity=severity,
            details=details
        )
    
    def log_security_event(self, event_type: AuditEventType, 
                         source_ip: Optional[str] = None,
                         user_id: Optional[str] = None,
                         details: Optional[Dict[str, Any]] = None) -> str:
        """Log security-related event."""
        return self.log_event(
            event_type=event_type,
            user_id=user_id,
            source_ip=source_ip,
            action=f"security_{event_type.value}",
            result="DETECTED",
            severity=AuditSeverity.CRITICAL,
            details=details
        )
    
    def log_administrative_event(self, event_type: AuditEventType, admin_user_id: str,
                               target_user_id: Optional[str] = None,
                               action: str = "", result: str = "SUCCESS",
                               details: Optional[Dict[str, Any]] = None) -> str:
        """Log administrative action."""
        audit_details = details or {}
        if target_user_id:
            audit_details["target_user_id"] = target_user_id
        
        severity = AuditSeverity.WARNING  # Admin actions are always notable
        
        return self.log_event(
            event_type=event_type,
            user_id=admin_user_id,
            action=action,
            result=result,
            severity=severity,
            details=audit_details
        )
    
    def start_background_processing(self) -> None:
        """Start background thread for processing audit events."""
        if self.background_processor is None or not self.background_processor.is_alive():
            self.is_running = True
            self.background_processor = threading.Thread(
                target=self._process_audit_events,
                daemon=True
            )
            self.background_processor.start()
            logger.info("Audit log background processor started")
    
    def stop_background_processing(self) -> None:
        """Stop background processing and flush remaining events."""
        self.is_running = False
        if self.background_processor and self.background_processor.is_alive():
            self.background_processor.join(timeout=5)
        
        # Process remaining events
        while not self.event_queue.empty():
            try:
                event = self.event_queue.get_nowait()
                self._write_audit_event(event)
            except:
                break
        
        logger.info("Audit log background processor stopped")
    
    def _process_audit_events(self) -> None:
        """Background processing of audit events."""
        while self.is_running:
            try:
                # Get event from queue (blocks with timeout)
                event = self.event_queue.get(timeout=1)
                self._write_audit_event(event)
                self.event_queue.task_done()
                
            except:
                continue  # Timeout or other error, continue processing
    
    def _write_audit_event(self, event: AuditEvent) -> None:
        """Write audit event to persistent storage."""
        try:
            # Convert to JSON for storage
            event_data = event.to_dict()
            
            # In production, this would write to:
            # - Secure audit database
            # - SIEM system
            # - Compliance logging system
            # - Immutable audit trail
            
            # For now, log to structured logger
            logger.info("AUDIT_EVENT", extra={
                "audit_data": event_data,
                "compliance_tags": [tag.value for tag in event.compliance_tags]
            })
            
            # Also write to dedicated audit log file
            self._write_to_audit_file(event_data)
            
        except Exception as e:
            logger.error(f"Failed to write audit event {event.event_id}: {str(e)}")
    
    def _write_to_audit_file(self, event_data: Dict[str, Any]) -> None:
        """Write audit event to dedicated audit file."""
        import os
        
        # Create audit log directory if it doesn't exist
        audit_dir = "logs/audit"
        os.makedirs(audit_dir, exist_ok=True)
        
        # Write to daily audit file
        date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        audit_file = os.path.join(audit_dir, f"audit_{date_str}.jsonl")
        
        try:
            with open(audit_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(event_data) + "\n")
        except Exception as e:
            logger.error(f"Failed to write to audit file: {str(e)}")
    
    def get_audit_statistics(self) -> Dict[str, Any]:
        """Get audit logging statistics."""
        return {
            "event_counts_by_type": {
                event_type.value: count 
                for event_type, count in self.event_counters.items() 
                if count > 0
            },
            "event_counts_by_severity": {
                severity.value: count 
                for severity, count in self.severity_counters.items() 
                if count > 0
            },
            "total_events": sum(self.event_counters.values()),
            "queue_size": self.event_queue.qsize(),
            "processor_running": self.is_running
        }
    
    def verify_event_integrity(self, event: AuditEvent) -> bool:
        """Verify the integrity of an audit event."""
        if not event.checksum:
            return True  # No checksum to verify
        
        expected_checksum = event.calculate_checksum(self.secret_key)
        return hmac.compare_digest(event.checksum, expected_checksum)
    
    def search_audit_events(self, 
                          event_type: Optional[AuditEventType] = None,
                          user_id: Optional[str] = None,
                          start_time: Optional[datetime] = None,
                          end_time: Optional[datetime] = None,
                          severity: Optional[AuditSeverity] = None,
                          compliance_standard: Optional[ComplianceStandard] = None,
                          limit: int = 1000) -> List[Dict[str, Any]]:
        """Search audit events (mock implementation for interface)."""
        # In production, this would query the audit database
        # with the specified filters and return matching events
        
        logger.info("Audit event search requested", extra={
            "event_type": event_type.value if event_type else None,
            "user_id": user_id,
            "start_time": start_time.isoformat() if start_time else None,
            "end_time": end_time.isoformat() if end_time else None,
            "severity": severity.value if severity else None,
            "compliance_standard": compliance_standard.value if compliance_standard else None,
            "limit": limit
        })
        
        return []  # Mock empty result
    
    def generate_compliance_report(self, 
                                 compliance_standard: ComplianceStandard,
                                 start_time: datetime,
                                 end_time: datetime) -> Dict[str, Any]:
        """Generate compliance report for specified standard and time period."""
        # Get relevant event types for this compliance standard
        relevant_events = [
            event_type for event_type, standards in self.compliance_mapping.items()
            if compliance_standard in standards
        ]
        
        report = {
            "compliance_standard": compliance_standard.value,
            "report_period": {
                "start": start_time.isoformat(),
                "end": end_time.isoformat()
            },
            "relevant_event_types": [event_type.value for event_type in relevant_events],
            "summary": {
                "total_events": sum(
                    self.event_counters[event_type] 
                    for event_type in relevant_events
                ),
                "critical_events": 0,  # Would be calculated from actual data
                "failed_events": 0,    # Would be calculated from actual data
            },
            "generated_at": datetime.now(timezone.utc).isoformat()
        }
        
        logger.info("Compliance report generated", extra={
            "compliance_standard": compliance_standard.value,
            "report_data": report
        })
        
        return report


# Global audit logger instance
audit_logger = AuditLogger()


def audit_event(event_type: AuditEventType):
    """Decorator to automatically log audit events for functions."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Extract user context from kwargs or function attributes
            user_id = kwargs.get('user_id') or getattr(func, 'current_user_id', None)
            resource_type = kwargs.get('resource_type', func.__name__)
            resource_id = kwargs.get('resource_id', str(kwargs.get('id', '')))
            
            try:
                result = func(*args, **kwargs)
                
                # Log successful event
                audit_logger.log_event(
                    event_type=event_type,
                    user_id=user_id,
                    resource_type=resource_type,
                    resource_id=resource_id,
                    action=func.__name__,
                    result="SUCCESS",
                    details={"function": func.__name__, "args_count": len(args)}
                )
                
                return result
                
            except Exception as e:
                # Log failed event
                audit_logger.log_event(
                    event_type=event_type,
                    user_id=user_id,
                    resource_type=resource_type,
                    resource_id=resource_id,
                    action=func.__name__,
                    result="FAILURE",
                    severity=AuditSeverity.ERROR,
                    details={
                        "function": func.__name__, 
                        "error": str(e),
                        "args_count": len(args)
                    }
                )
                raise
        
        return wrapper
    return decorator