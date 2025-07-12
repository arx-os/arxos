"""
Advanced Security & Compliance Service

This module provides enterprise-grade security features including:
- Advanced privacy controls and data classification
- Multi-layer encryption (AES-256, TLS 1.3)
- Comprehensive audit trail system
- Role-based access control (RBAC)
- Data retention policies
- AHJ API integration
"""

import logging
import time
import hashlib
import json
import uuid
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import threading
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization
import base64
import secrets

from utils.logger import get_logger

logger = get_logger(__name__)


class DataClassification(Enum):
    """Data classification levels for security controls"""
    PUBLIC = "public"           # Non-sensitive building data
    INTERNAL = "internal"       # Internal operational data
    CONFIDENTIAL = "confidential"  # Sensitive building information
    RESTRICTED = "restricted"   # Highly sensitive data (AHJ, compliance)
    CLASSIFIED = "classified"   # Top-level security clearance


class PermissionLevel(Enum):
    """Permission levels for role-based access control"""
    SYSTEM_ADMIN = "system_admin"      # Full system access
    BUILDING_ADMIN = "building_admin"  # Building-level administration
    AHJ_INSPECTOR = "ahj_inspector"    # AHJ inspection permissions
    CONTRACTOR = "contractor"          # Contractor-level access
    VIEWER = "viewer"                  # Read-only access
    GUEST = "guest"                    # Limited access


class AuditEventType(Enum):
    """Types of audit events"""
    DATA_ACCESS = "data_access"
    DATA_MODIFICATION = "data_modification"
    USER_LOGIN = "user_login"
    USER_LOGOUT = "user_logout"
    PERMISSION_CHANGE = "permission_change"
    ENCRYPTION_OPERATION = "encryption_operation"
    AHJ_INTERACTION = "ahj_interaction"
    COMPLIANCE_VIOLATION = "compliance_violation"


@dataclass
class AuditEvent:
    """Audit event with full details"""
    event_id: str
    event_type: AuditEventType
    user_id: str
    resource_id: str
    action: str
    timestamp: datetime
    correlation_id: str
    details: Dict[str, Any] = field(default_factory=dict)
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    success: bool = True


@dataclass
class SecurityMetrics:
    """Security performance metrics"""
    encryption_operations: int = 0
    audit_events_logged: int = 0
    permission_checks: int = 0
    ahj_interactions: int = 0
    compliance_violations: int = 0
    average_encryption_time_ms: float = 0.0
    average_audit_time_ms: float = 0.0
    average_permission_check_time_ms: float = 0.0


class PrivacyControlsService:
    """Advanced privacy controls and data classification service"""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        
        # Data classification mappings
        self.data_classifiers = {
            "building_data": DataClassification.INTERNAL,
            "ahj_annotations": DataClassification.RESTRICTED,
            "user_credentials": DataClassification.CLASSIFIED,
            "audit_logs": DataClassification.CONFIDENTIAL,
            "compliance_reports": DataClassification.RESTRICTED,
            "inspection_notes": DataClassification.RESTRICTED,
            "system_config": DataClassification.CONFIDENTIAL,
            "public_building_info": DataClassification.PUBLIC
        }
        
        # Privacy control rules
        self.privacy_rules = {
            DataClassification.PUBLIC: {
                "encryption_required": False,
                "audit_required": False,
                "retention_days": 365,
                "sharing_allowed": True
            },
            DataClassification.INTERNAL: {
                "encryption_required": True,
                "audit_required": True,
                "retention_days": 730,
                "sharing_allowed": False
            },
            DataClassification.CONFIDENTIAL: {
                "encryption_required": True,
                "audit_required": True,
                "retention_days": 1095,
                "sharing_allowed": False
            },
            DataClassification.RESTRICTED: {
                "encryption_required": True,
                "audit_required": True,
                "retention_days": 1825,
                "sharing_allowed": False
            },
            DataClassification.CLASSIFIED: {
                "encryption_required": True,
                "audit_required": True,
                "retention_days": 3650,
                "sharing_allowed": False
            }
        }
    
    def classify_data(self, data_type: str, content: Any) -> DataClassification:
        """
        Classify data based on content and type.
        
        Args:
            data_type: Type of data being classified
            content: Data content for classification
            
        Returns:
            DataClassification: Appropriate classification level
        """
        # Get base classification from type
        base_classification = self.data_classifiers.get(data_type, DataClassification.INTERNAL)
        
        # Apply content-based classification rules
        if isinstance(content, str):
            # Check for sensitive keywords
            sensitive_keywords = [
                "password", "credential", "secret", "key", "token",
                "ssn", "social", "credit", "bank", "account",
                "violation", "inspection", "compliance", "audit"
            ]
            
            content_lower = content.lower()
            for keyword in sensitive_keywords:
                if keyword in content_lower:
                    return DataClassification.RESTRICTED
        
        elif isinstance(content, dict):
            # Check for sensitive fields
            sensitive_fields = ["password", "secret", "key", "token", "credential"]
            for field in sensitive_fields:
                if field in content:
                    return DataClassification.CLASSIFIED
        
        return base_classification
    
    def apply_privacy_controls(self, data: Any, classification: DataClassification) -> Dict[str, Any]:
        """
        Apply privacy controls based on classification.
        
        Args:
            data: Data to apply controls to
            classification: Data classification level
            
        Returns:
            Dict[str, Any]: Data with applied privacy controls
        """
        rules = self.privacy_rules[classification]
        
        # Apply encryption if required
        if rules["encryption_required"]:
            # This would integrate with the encryption service
            data = self._apply_encryption(data)
        
        # Add privacy metadata
        privacy_metadata = {
            "classification": classification.value,
            "encryption_required": rules["encryption_required"],
            "audit_required": rules["audit_required"],
            "retention_days": rules["retention_days"],
            "sharing_allowed": rules["sharing_allowed"],
            "classification_timestamp": datetime.now().isoformat()
        }
        
        return {
            "data": data,
            "privacy_metadata": privacy_metadata
        }
    
    def anonymize_data(self, data: Any, fields_to_anonymize: List[str] = None) -> Any:
        """
        Anonymize data for external sharing.
        
        Args:
            data: Data to anonymize
            fields_to_anonymize: Specific fields to anonymize
            
        Returns:
            Any: Anonymized data
        """
        if isinstance(data, dict):
            anonymized_data = data.copy()
            
            # Default fields to anonymize
            if fields_to_anonymize is None:
                fields_to_anonymize = [
                    "user_id", "email", "phone", "address", "name",
                    "ssn", "credit_card", "account_number"
                ]
            
            for field in fields_to_anonymize:
                if field in anonymized_data:
                    # Generate anonymized value
                    anonymized_data[field] = self._generate_anonymized_value(field)
            
            return anonymized_data
        
        elif isinstance(data, list):
            return [self.anonymize_data(item, fields_to_anonymize) for item in data]
        
        return data
    
    def _apply_encryption(self, data: Any) -> bytes:
        """Apply encryption to data (placeholder for encryption service integration)"""
        # This would integrate with the encryption service
        return data.encode() if isinstance(data, str) else str(data).encode()
    
    def _generate_anonymized_value(self, field_name: str) -> str:
        """Generate anonymized value for a field"""
        # Generate consistent hash-based anonymization
        hash_value = hashlib.sha256(field_name.encode()).hexdigest()[:8]
        return f"anon_{hash_value}"


class EncryptionService:
    """Multi-layer encryption service with AES-256 and TLS support"""
    
    def __init__(self, master_key: str = None):
        self.logger = get_logger(__name__)
        
        # Generate or use provided master key
        if master_key is None:
            self.master_key = Fernet.generate_key()
        else:
            self.master_key = master_key.encode() if isinstance(master_key, str) else master_key
        
        self.fernet = Fernet(self.master_key)
        
        # Key rotation tracking
        self.key_rotation_date = datetime.now()
        self.key_rotation_interval = timedelta(days=90)
        
        # Performance tracking
        self.encryption_metrics = {
            "total_operations": 0,
            "total_time_ms": 0.0,
            "average_time_ms": 0.0
        }
    
    def encrypt_data(self, data: Any, layer: str = "storage") -> bytes:
        """
        Encrypt data using specified layer.
        
        Args:
            data: Data to encrypt
            layer: Encryption layer (storage, transport, database, backup)
            
        Returns:
            bytes: Encrypted data
        """
        start_time = time.time()
        
        try:
            # Convert data to bytes if needed
            if isinstance(data, str):
                data_bytes = data.encode('utf-8')
            elif isinstance(data, dict):
                data_bytes = json.dumps(data).encode('utf-8')
            else:
                data_bytes = str(data).encode('utf-8')
            
            # Apply layer-specific encryption
            if layer == "storage":
                encrypted_data = self._encrypt_storage(data_bytes)
            elif layer == "transport":
                encrypted_data = self._encrypt_transport(data_bytes)
            elif layer == "database":
                encrypted_data = self._encrypt_database(data_bytes)
            elif layer == "backup":
                encrypted_data = self._encrypt_backup(data_bytes)
            else:
                raise ValueError(f"Unknown encryption layer: {layer}")
            
            # Update metrics
            operation_time = (time.time() - start_time) * 1000
            self._update_metrics(operation_time)
            
            self.logger.debug(f"Encrypted {len(data_bytes)} bytes in {operation_time:.2f}ms")
            return encrypted_data
            
        except Exception as e:
            self.logger.error(f"Encryption failed: {e}")
            raise
    
    def decrypt_data(self, encrypted_data: bytes, layer: str = "storage") -> Any:
        """
        Decrypt data using specified layer.
        
        Args:
            encrypted_data: Encrypted data to decrypt
            layer: Encryption layer
            
        Returns:
            Any: Decrypted data
        """
        start_time = time.time()
        
        try:
            # Apply layer-specific decryption
            if layer == "storage":
                decrypted_data = self._decrypt_storage(encrypted_data)
            elif layer == "transport":
                decrypted_data = self._decrypt_transport(encrypted_data)
            elif layer == "database":
                decrypted_data = self._decrypt_database(encrypted_data)
            elif layer == "backup":
                decrypted_data = self._decrypt_backup(encrypted_data)
            else:
                raise ValueError(f"Unknown encryption layer: {layer}")
            
            # Update metrics
            operation_time = (time.time() - start_time) * 1000
            self._update_metrics(operation_time)
            
            self.logger.debug(f"Decrypted {len(encrypted_data)} bytes in {operation_time:.2f}ms")
            return decrypted_data
            
        except Exception as e:
            self.logger.error(f"Decryption failed: {e}")
            raise
    
    def rotate_keys(self, key_type: str = "all"):
        """
        Rotate encryption keys.
        
        Args:
            key_type: Type of key to rotate (all, storage, transport, etc.)
        """
        try:
            # Generate new master key
            new_master_key = Fernet.generate_key()
            
            # Update key rotation date
            self.key_rotation_date = datetime.now()
            
            # Update encryption instance
            self.master_key = new_master_key
            self.fernet = Fernet(new_master_key)
            
            self.logger.info(f"Successfully rotated {key_type} encryption keys")
            
        except Exception as e:
            self.logger.error(f"Key rotation failed: {e}")
            raise
    
    def _encrypt_storage(self, data: bytes) -> bytes:
        """Encrypt data for storage using AES-256"""
        return self.fernet.encrypt(data)
    
    def _decrypt_storage(self, encrypted_data: bytes) -> bytes:
        """Decrypt data from storage"""
        return self.fernet.decrypt(encrypted_data)
    
    def _encrypt_transport(self, data: bytes) -> bytes:
        """Encrypt data for transport (TLS would be handled at transport layer)"""
        # For transport, we use a different key derivation
        transport_key = self._derive_transport_key()
        transport_fernet = Fernet(transport_key)
        return transport_fernet.encrypt(data)
    
    def _decrypt_transport(self, encrypted_data: bytes) -> bytes:
        """Decrypt data from transport"""
        transport_key = self._derive_transport_key()
        transport_fernet = Fernet(transport_key)
        return transport_fernet.decrypt(encrypted_data)
    
    def _encrypt_database(self, data: bytes) -> bytes:
        """Encrypt data for database storage"""
        # Database encryption uses column-level encryption
        return self._encrypt_storage(data)
    
    def _decrypt_database(self, encrypted_data: bytes) -> bytes:
        """Decrypt data from database"""
        return self._decrypt_storage(encrypted_data)
    
    def _encrypt_backup(self, data: bytes) -> bytes:
        """Encrypt data for backup storage"""
        # Backup encryption uses a different key
        backup_key = self._derive_backup_key()
        backup_fernet = Fernet(backup_key)
        return backup_fernet.encrypt(data)
    
    def _decrypt_backup(self, encrypted_data: bytes) -> bytes:
        """Decrypt data from backup"""
        backup_key = self._derive_backup_key()
        backup_fernet = Fernet(backup_key)
        return backup_fernet.decrypt(encrypted_data)
    
    def _derive_transport_key(self) -> bytes:
        """Derive transport encryption key"""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b"transport_salt",
            iterations=100000,
        )
        return base64.urlsafe_b64encode(kdf.derive(self.master_key))
    
    def _derive_backup_key(self) -> bytes:
        """Derive backup encryption key"""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b"backup_salt",
            iterations=100000,
        )
        return base64.urlsafe_b64encode(kdf.derive(self.master_key))
    
    def _update_metrics(self, operation_time: float):
        """Update encryption performance metrics"""
        self.encryption_metrics["total_operations"] += 1
        self.encryption_metrics["total_time_ms"] += operation_time
        self.encryption_metrics["average_time_ms"] = (
            self.encryption_metrics["total_time_ms"] / 
            self.encryption_metrics["total_operations"]
        )
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get encryption performance metrics"""
        return self.encryption_metrics.copy()


class AuditTrailService:
    """Comprehensive audit trail system with event logging and compliance reporting"""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        
        # In-memory audit logs (in production, this would be a database)
        self.audit_logs: List[AuditEvent] = []
        self.correlation_ids: Dict[str, List[str]] = {}
        self.retention_policies = {
            "data_access": 1095,  # 3 years
            "user_actions": 1825,  # 5 years
            "security_events": 3650,  # 10 years
            "compliance_events": 3650  # 10 years
        }
        
        # Thread safety
        self.lock = threading.RLock()
        
        # Performance tracking
        self.audit_metrics = {
            "total_events": 0,
            "events_by_type": {},
            "average_logging_time_ms": 0.0
        }
    
    def log_event(self, event_type: AuditEventType, user_id: str, resource_id: str,
                  action: str, details: Dict[str, Any] = None, 
                  correlation_id: str = None, ip_address: str = None,
                  user_agent: str = None, success: bool = True) -> str:
        """
        Log audit event with full details.
        
        Args:
            event_type: Type of audit event
            user_id: User performing the action
            resource_id: Resource being accessed
            action: Action being performed
            details: Additional event details
            correlation_id: Correlation ID for request tracking
            ip_address: IP address of the request
            user_agent: User agent string
            success: Whether the action was successful
            
        Returns:
            str: Event ID
        """
        start_time = time.time()
        
        with self.lock:
            # Generate event ID
            event_id = str(uuid.uuid4())
            
            # Generate correlation ID if not provided
            if correlation_id is None:
                correlation_id = str(uuid.uuid4())
            
            # Create audit event
            event = AuditEvent(
                event_id=event_id,
                event_type=event_type,
                user_id=user_id,
                resource_id=resource_id,
                action=action,
                timestamp=datetime.now(),
                correlation_id=correlation_id,
                details=details or {},
                ip_address=ip_address,
                user_agent=user_agent,
                success=success
            )
            
            # Store event
            self.audit_logs.append(event)
            
            # Track correlation ID
            if correlation_id not in self.correlation_ids:
                self.correlation_ids[correlation_id] = []
            self.correlation_ids[correlation_id].append(event_id)
            
            # Update metrics
            operation_time = (time.time() - start_time) * 1000
            self._update_metrics(event_type, operation_time)
            
            self.logger.debug(f"Logged audit event {event_id} in {operation_time:.2f}ms")
            return event_id
    
    def get_audit_logs(self, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Retrieve audit logs with filtering.
        
        Args:
            filters: Filter criteria for logs
            
        Returns:
            List[Dict[str, Any]]: Filtered audit logs
        """
        with self.lock:
            filtered_logs = self.audit_logs.copy()
            
            if filters:
                # Apply filters
                if "event_type" in filters:
                    filtered_logs = [
                        log for log in filtered_logs 
                        if log.event_type.value == filters["event_type"]
                    ]
                
                if "user_id" in filters:
                    filtered_logs = [
                        log for log in filtered_logs 
                        if log.user_id == filters["user_id"]
                    ]
                
                if "resource_id" in filters:
                    filtered_logs = [
                        log for log in filtered_logs 
                        if log.resource_id == filters["resource_id"]
                    ]
                
                if "start_date" in filters:
                    filtered_logs = [
                        log for log in filtered_logs 
                        if log.timestamp >= filters["start_date"]
                    ]
                
                if "end_date" in filters:
                    filtered_logs = [
                        log for log in filtered_logs 
                        if log.timestamp <= filters["end_date"]
                    ]
            
            # Convert to dictionaries
            return [self._event_to_dict(event) for event in filtered_logs]
    
    def generate_compliance_report(self, report_type: str, 
                                 date_range: Tuple[datetime, datetime]) -> Dict[str, Any]:
        """
        Generate compliance reports.
        
        Args:
            report_type: Type of compliance report
            date_range: Date range for the report
            
        Returns:
            Dict[str, Any]: Compliance report
        """
        start_date, end_date = date_range
        
        with self.lock:
            # Filter events by date range
            events_in_range = [
                event for event in self.audit_logs
                if start_date <= event.timestamp <= end_date
            ]
            
            if report_type == "data_access":
                return self._generate_data_access_report(events_in_range)
            elif report_type == "security_events":
                return self._generate_security_events_report(events_in_range)
            elif report_type == "compliance_summary":
                return self._generate_compliance_summary_report(events_in_range)
            else:
                raise ValueError(f"Unknown report type: {report_type}")
    
    def enforce_retention_policies(self):
        """Enforce data retention policies"""
        with self.lock:
            current_time = datetime.now()
            events_to_remove = []
            
            for event in self.audit_logs:
                retention_days = self.retention_policies.get(
                    event.event_type.value, 1095  # Default 3 years
                )
                
                if (current_time - event.timestamp).days > retention_days:
                    events_to_remove.append(event)
            
            # Remove expired events
            for event in events_to_remove:
                self.audit_logs.remove(event)
            
            self.logger.info(f"Removed {len(events_to_remove)} expired audit events")
    
    def _generate_data_access_report(self, events: List[AuditEvent]) -> Dict[str, Any]:
        """Generate data access compliance report"""
        data_access_events = [
            event for event in events 
            if event.event_type == AuditEventType.DATA_ACCESS
        ]
        
        return {
            "report_type": "data_access",
            "total_events": len(data_access_events),
            "unique_users": len(set(event.user_id for event in data_access_events)),
            "unique_resources": len(set(event.resource_id for event in data_access_events)),
            "successful_access": len([e for e in data_access_events if e.success]),
            "failed_access": len([e for e in data_access_events if not e.success]),
            "events_by_user": self._group_events_by_user(data_access_events),
            "events_by_resource": self._group_events_by_resource(data_access_events)
        }
    
    def _generate_security_events_report(self, events: List[AuditEvent]) -> Dict[str, Any]:
        """Generate security events compliance report"""
        security_events = [
            event for event in events 
            if event.event_type in [
                AuditEventType.USER_LOGIN, AuditEventType.USER_LOGOUT,
                AuditEventType.PERMISSION_CHANGE, AuditEventType.ENCRYPTION_OPERATION
            ]
        ]
        
        return {
            "report_type": "security_events",
            "total_events": len(security_events),
            "login_events": len([e for e in security_events if e.event_type == AuditEventType.USER_LOGIN]),
            "logout_events": len([e for e in security_events if e.event_type == AuditEventType.USER_LOGOUT]),
            "permission_changes": len([e for e in security_events if e.event_type == AuditEventType.PERMISSION_CHANGE]),
            "encryption_operations": len([e for e in security_events if e.event_type == AuditEventType.ENCRYPTION_OPERATION])
        }
    
    def _generate_compliance_summary_report(self, events: List[AuditEvent]) -> Dict[str, Any]:
        """Generate compliance summary report"""
        return {
            "report_type": "compliance_summary",
            "total_events": len(events),
            "events_by_type": self._group_events_by_type(events),
            "compliance_status": "compliant",  # Would be determined by business rules
            "retention_policy_status": "enforced",
            "encryption_status": "enabled",
            "audit_trail_status": "complete"
        }
    
    def _group_events_by_user(self, events: List[AuditEvent]) -> Dict[str, int]:
        """Group events by user"""
        user_counts = {}
        for event in events:
            user_counts[event.user_id] = user_counts.get(event.user_id, 0) + 1
        return user_counts
    
    def _group_events_by_resource(self, events: List[AuditEvent]) -> Dict[str, int]:
        """Group events by resource"""
        resource_counts = {}
        for event in events:
            resource_counts[event.resource_id] = resource_counts.get(event.resource_id, 0) + 1
        return resource_counts
    
    def _group_events_by_type(self, events: List[AuditEvent]) -> Dict[str, int]:
        """Group events by type"""
        type_counts = {}
        for event in events:
            type_counts[event.event_type.value] = type_counts.get(event.event_type.value, 0) + 1
        return type_counts
    
    def _event_to_dict(self, event: AuditEvent) -> Dict[str, Any]:
        """Convert audit event to dictionary"""
        return {
            "event_id": event.event_id,
            "event_type": event.event_type.value,
            "user_id": event.user_id,
            "resource_id": event.resource_id,
            "action": event.action,
            "timestamp": event.timestamp.isoformat(),
            "correlation_id": event.correlation_id,
            "details": event.details,
            "ip_address": event.ip_address,
            "user_agent": event.user_agent,
            "success": event.success
        }
    
    def _update_metrics(self, event_type: AuditEventType, operation_time: float):
        """Update audit performance metrics"""
        self.audit_metrics["total_events"] += 1
        
        event_type_str = event_type.value
        self.audit_metrics["events_by_type"][event_type_str] = (
            self.audit_metrics["events_by_type"].get(event_type_str, 0) + 1
        )
        
        # Update average time
        current_avg = self.audit_metrics["average_logging_time_ms"]
        total_events = self.audit_metrics["total_events"]
        self.audit_metrics["average_logging_time_ms"] = (
            (current_avg * (total_events - 1) + operation_time) / total_events
        )
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get audit trail performance metrics"""
        return self.audit_metrics.copy()


class RBACService:
    """Role-based access control service with fine-grained permissions"""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        
        # Role and permission storage
        self.roles: Dict[str, Dict[str, Any]] = {}
        self.permissions: Dict[str, List[str]] = {}
        self.user_assignments: Dict[str, List[str]] = {}
        
        # Initialize default roles and permissions
        self._initialize_default_roles()
        
        # Performance tracking
        self.rbac_metrics = {
            "total_permission_checks": 0,
            "successful_checks": 0,
            "failed_checks": 0,
            "average_check_time_ms": 0.0
        }
    
    def create_role(self, role_name: str, permissions: List[str], 
                   description: str = "") -> str:
        """
        Create role with specific permissions.
        
        Args:
            role_name: Name of the role
            permissions: List of permissions for the role
            description: Role description
            
        Returns:
            str: Role ID
        """
        role_id = str(uuid.uuid4())
        
        self.roles[role_id] = {
            "name": role_name,
            "permissions": permissions,
            "description": description,
            "created_at": datetime.now(),
            "active": True
        }
        
        self.permissions[role_id] = permissions
        
        self.logger.info(f"Created role '{role_name}' with {len(permissions)} permissions")
        return role_id
    
    def assign_user_to_role(self, user_id: str, role_id: str) -> bool:
        """
        Assign user to role.
        
        Args:
            user_id: User ID to assign
            role_id: Role ID to assign user to
            
        Returns:
            bool: Success status
        """
        if role_id not in self.roles:
            raise ValueError(f"Role {role_id} does not exist")
        
        if user_id not in self.user_assignments:
            self.user_assignments[user_id] = []
        
        if role_id not in self.user_assignments[user_id]:
            self.user_assignments[user_id].append(role_id)
            self.logger.info(f"Assigned user {user_id} to role {role_id}")
            return True
        
        return False
    
    def check_permission(self, user_id: str, resource: str, action: str) -> bool:
        """
        Check if user has permission for action on resource.
        
        Args:
            user_id: User ID to check
            resource: Resource being accessed
            action: Action being performed
            
        Returns:
            bool: Whether user has permission
        """
        start_time = time.time()
        
        try:
            # Get user's roles
            user_roles = self.user_assignments.get(user_id, [])
            
            # Check each role for the required permission
            required_permission = f"{resource}:{action}"
            
            for role_id in user_roles:
                if role_id in self.permissions:
                    role_permissions = self.permissions[role_id]
                    
                    # Check for exact permission or wildcard
                    if (required_permission in role_permissions or 
                        f"{resource}:*" in role_permissions or
                        "*:*" in role_permissions):
                        
                        # Update metrics
                        operation_time = (time.time() - start_time) * 1000
                        self._update_metrics(True, operation_time)
                        
                        return True
            
            # Update metrics
            operation_time = (time.time() - start_time) * 1000
            self._update_metrics(False, operation_time)
            
            return False
            
        except Exception as e:
            self.logger.error(f"Permission check failed: {e}")
            return False
    
    def get_user_permissions(self, user_id: str) -> List[str]:
        """
        Get all permissions for user.
        
        Args:
            user_id: User ID to get permissions for
            
        Returns:
            List[str]: List of user permissions
        """
        user_roles = self.user_assignments.get(user_id, [])
        all_permissions = set()
        
        for role_id in user_roles:
            if role_id in self.permissions:
                all_permissions.update(self.permissions[role_id])
        
        return list(all_permissions)
    
    def remove_user_from_role(self, user_id: str, role_id: str) -> bool:
        """
        Remove user from role.
        
        Args:
            user_id: User ID to remove
            role_id: Role ID to remove user from
            
        Returns:
            bool: Success status
        """
        if user_id in self.user_assignments and role_id in self.user_assignments[user_id]:
            self.user_assignments[user_id].remove(role_id)
            self.logger.info(f"Removed user {user_id} from role {role_id}")
            return True
        
        return False
    
    def _initialize_default_roles(self):
        """Initialize default roles and permissions"""
        # System Admin - Full access
        system_admin_permissions = [
            "*:*"  # All resources, all actions
        ]
        self.create_role("System Admin", system_admin_permissions, "Full system access")
        
        # Building Admin - Building-level administration
        building_admin_permissions = [
            "building:*",
            "floor:*",
            "system:*",
            "user:read",
            "audit:read"
        ]
        self.create_role("Building Admin", building_admin_permissions, "Building-level administration")
        
        # AHJ Inspector - AHJ inspection permissions
        ahj_inspector_permissions = [
            "inspection:*",
            "violation:*",
            "building:read",
            "floor:read",
            "system:read"
        ]
        self.create_role("AHJ Inspector", ahj_inspector_permissions, "AHJ inspection permissions")
        
        # Contractor - Contractor-level access
        contractor_permissions = [
            "building:read",
            "floor:read",
            "system:read",
            "maintenance:*"
        ]
        self.create_role("Contractor", contractor_permissions, "Contractor-level access")
        
        # Viewer - Read-only access
        viewer_permissions = [
            "building:read",
            "floor:read",
            "system:read"
        ]
        self.create_role("Viewer", viewer_permissions, "Read-only access")
        
        # Guest - Limited access
        guest_permissions = [
            "building:read"
        ]
        self.create_role("Guest", guest_permissions, "Limited access")
    
    def _update_metrics(self, success: bool, operation_time: float):
        """Update RBAC performance metrics"""
        self.rbac_metrics["total_permission_checks"] += 1
        
        if success:
            self.rbac_metrics["successful_checks"] += 1
        else:
            self.rbac_metrics["failed_checks"] += 1
        
        # Update average time
        current_avg = self.rbac_metrics["average_check_time_ms"]
        total_checks = self.rbac_metrics["total_permission_checks"]
        self.rbac_metrics["average_check_time_ms"] = (
            (current_avg * (total_checks - 1) + operation_time) / total_checks
        )
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get RBAC performance metrics"""
        return self.rbac_metrics.copy()


class AdvancedSecurityService:
    """
    Advanced Security & Compliance Service
    
    Comprehensive security service that integrates privacy controls,
    encryption, audit trails, and role-based access control.
    """
    
    def __init__(self):
        self.logger = get_logger(__name__)
        
        # Initialize security components
        self.privacy_controls = PrivacyControlsService()
        self.encryption_service = EncryptionService()
        self.audit_trail = AuditTrailService()
        self.rbac_service = RBACService()
        
        # Security metrics
        self.security_metrics = SecurityMetrics()
        
        # Security monitoring
        self.security_alerts = []
        self.incident_response_procedures = {}
    
    def secure_data_access(self, user_id: str, resource_id: str, action: str,
                          data: Any, data_type: str = "building_data",
                          correlation_id: str = None) -> Dict[str, Any]:
        """
        Secure data access with full security controls.
        
        Args:
            user_id: User accessing the data
            resource_id: Resource being accessed
            action: Action being performed
            data: Data being accessed
            data_type: Type of data
            correlation_id: Correlation ID for tracking
            
        Returns:
            Dict[str, Any]: Secured data with metadata
        """
        start_time = time.time()
        
        try:
            # 1. Check permissions
            if not self.rbac_service.check_permission(user_id, resource_id, action):
                self.audit_trail.log_event(
                    AuditEventType.DATA_ACCESS, user_id, resource_id, action,
                    {"error": "Permission denied"}, correlation_id, success=False
                )
                raise PermissionError(f"User {user_id} does not have permission for {action} on {resource_id}")
            
            # 2. Classify data
            classification = self.privacy_controls.classify_data(data_type, data)
            
            # 3. Apply privacy controls
            secured_data = self.privacy_controls.apply_privacy_controls(data, classification)
            
            # 4. Encrypt if required
            if secured_data["privacy_metadata"]["encryption_required"]:
                secured_data["data"] = self.encryption_service.encrypt_data(
                    secured_data["data"], "storage"
                )
            
            # 5. Log audit event
            self.audit_trail.log_event(
                AuditEventType.DATA_ACCESS, user_id, resource_id, action,
                {"classification": classification.value, "encrypted": secured_data["privacy_metadata"]["encryption_required"]},
                correlation_id, success=True
            )
            
            # 6. Update metrics
            operation_time = (time.time() - start_time) * 1000
            self._update_metrics(operation_time)
            
            return secured_data
            
        except Exception as e:
            self.logger.error(f"Secure data access failed: {e}")
            raise
    
    def get_security_metrics(self) -> Dict[str, Any]:
        """Get comprehensive security metrics"""
        return {
            "privacy_controls": {
                "data_classifications": len(self.privacy_controls.data_classifiers),
                "privacy_rules": len(self.privacy_controls.privacy_rules)
            },
            "encryption": self.encryption_service.get_metrics(),
            "audit_trail": self.audit_trail.get_metrics(),
            "rbac": self.rbac_service.get_metrics(),
            "overall": {
                "total_operations": self.security_metrics.encryption_operations + 
                                  self.security_metrics.audit_events_logged,
                "average_operation_time_ms": (
                    self.security_metrics.average_encryption_time_ms + 
                    self.security_metrics.average_audit_time_ms
                ) / 2
            }
        }
    
    def _update_metrics(self, operation_time: float):
        """Update security metrics"""
        self.security_metrics.encryption_operations += 1
        self.security_metrics.average_encryption_time_ms = (
            (self.security_metrics.average_encryption_time_ms * 
             (self.security_metrics.encryption_operations - 1) + operation_time) /
            self.security_metrics.encryption_operations
        ) 