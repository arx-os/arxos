"""
Security Service for SVGX Engine

This module provides a clean interface to the advanced security features for SVGX.
It wraps the advanced_security.py functionality and provides a simplified API
for common security operations.
"""

from typing import Dict, List, Any, Optional, Tuple, Union
from datetime import datetime, timedelta
import logging

from structlog import get_logger

from .advanced_security import (
    AdvancedSecurityService,
    PrivacyControlsService,
    EncryptionService,
    AuditTrailService,
    RBACService,
    DataClassification,
    PermissionLevel,
    AuditEventType,
    SecurityError
)

logger = get_logger(__name__)


class SVGXSecurityService:
    """
    Clean security service interface for SVGX operations.
    
    This service provides simplified access to advanced security features
    while maintaining the full functionality of the underlying security system.
    """
    
    def __init__(self):
        """Initialize the security service with all required components."""
        self.logger = logger
        self.advanced_security = AdvancedSecurityService()
        self.privacy_controls = PrivacyControlsService()
        self.encryption = EncryptionService()
        self.audit_trail = AuditTrailService()
        self.rbac = RBACService()
        
        self.logger.info("Security service initialized successfully")
    
    def secure_svgx_operation(self, user_id: str, resource_id: str, action: str,
                             data: Any = None, data_type: str = "svgx_content",
                             correlation_id: str = None) -> Dict[str, Any]:
        """
        Secure an SVGX operation with full security controls.
        
        Args:
            user_id: User performing the operation
            resource_id: Resource being accessed
            action: Action being performed
            data: Data involved in the operation
            data_type: Type of SVGX data
            correlation_id: Correlation ID for tracking
            
        Returns:
            Dict containing operation result and security metadata
            
        Raises:
            SecurityError: If security validation fails
        """
        try:
            # Check permissions first
            if not self.rbac.check_svgx_permission(user_id, resource_id, action):
                self.audit_trail.log_svgx_event(
                    AuditEventType.SVGX_SECURITY_VIOLATION,
                    user_id, resource_id, action,
                    {"error": "Permission denied"},
                    correlation_id,
                    success=False
                )
                raise SecurityError(f"Permission denied for {action} on {resource_id}")
            
            # Classify data if provided
            classification = None
            if data is not None:
                classification = self.privacy_controls.classify_svgx_data(data_type, data)
                
                # Apply privacy controls
                data = self.privacy_controls.apply_privacy_controls(data, classification)
            
            # Perform the secure operation
            result = self.advanced_security.secure_svgx_data_access(
                user_id, resource_id, action, data, data_type, correlation_id
            )
            
            # Log successful operation
            self.audit_trail.log_svgx_event(
                AuditEventType.SVGX_ACCESS,
                user_id, resource_id, action,
                {"classification": classification.value if classification else None},
                correlation_id,
                success=True
            )
            
            return result
            
        except Exception as e:
            self.logger.error(f"Security operation failed: {e}")
            self.audit_trail.log_svgx_event(
                AuditEventType.SVGX_SECURITY_VIOLATION,
                user_id, resource_id, action,
                {"error": str(e)},
                correlation_id,
                success=False
            )
            raise SecurityError(f"Security operation failed: {e}")
    
    def encrypt_svgx_data(self, data: Any, layer: str = "storage") -> bytes:
        """
        Encrypt SVGX data using the appropriate encryption layer.
        
        Args:
            data: Data to encrypt
            layer: Encryption layer (storage, transport, database, backup)
            
        Returns:
            Encrypted data as bytes
        """
        return self.encryption.encrypt_svgx_data(data, layer)
    
    def decrypt_svgx_data(self, encrypted_data: bytes, layer: str = "storage") -> Any:
        """
        Decrypt SVGX data using the appropriate encryption layer.
        
        Args:
            encrypted_data: Encrypted data as bytes
            layer: Encryption layer (storage, transport, database, backup)
            
        Returns:
            Decrypted data
        """
        return self.encryption.decrypt_svgx_data(encrypted_data, layer)
    
    def validate_svgx_content(self, content: str) -> Tuple[bool, List[str]]:
        """
        Validate SVGX content for security compliance.
        
        Args:
            content: SVGX content to validate
            
        Returns:
            Tuple of (is_valid, list_of_issues)
        """
        return self.privacy_controls.validate_svgx_content(content)
    
    def create_user_role(self, user_id: str, role_name: str, 
                        permissions: List[str], description: str = "") -> str:
        """
        Create a role for a user with specific permissions.
        
        Args:
            user_id: User ID
            role_name: Name of the role
            permissions: List of permissions
            description: Role description
            
        Returns:
            Role ID
        """
        role_id = self.rbac.create_svgx_role(role_name, permissions, description)
        self.rbac.assign_user_to_svgx_role(user_id, role_id)
        return role_id
    
    def check_permission(self, user_id: str, resource: str, action: str) -> bool:
        """
        Check if a user has permission for a specific action on a resource.
        
        Args:
            user_id: User ID
            resource: Resource identifier
            action: Action to perform
            
        Returns:
            True if permission granted, False otherwise
        """
        return self.rbac.check_svgx_permission(user_id, resource, action)
    
    def get_user_permissions(self, user_id: str) -> List[str]:
        """
        Get all permissions for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            List of permission strings
        """
        return self.rbac.get_user_svgx_permissions(user_id)
    
    def log_event(self, event_type: str, user_id: str, resource_id: str,
                  action: str, details: Dict[str, Any] = None,
                  correlation_id: str = None) -> str:
        """
        Log a security event.
        
        Args:
            event_type: Type of event
            user_id: User ID
            resource_id: Resource ID
            action: Action performed
            details: Additional details
            correlation_id: Correlation ID
            
        Returns:
            Event ID
        """
        audit_event_type = getattr(AuditEventType, event_type.upper(), AuditEventType.SVGX_ACCESS)
        return self.audit_trail.log_svgx_event(
            audit_event_type, user_id, resource_id, action, details, correlation_id
        )
    
    def get_audit_logs(self, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Get audit logs with optional filtering.
        
        Args:
            filters: Optional filters for the logs
            
        Returns:
            List of audit log entries
        """
        return self.audit_trail.get_svgx_audit_logs(filters)
    
    def generate_compliance_report(self, report_type: str,
                                 date_range: Tuple[datetime, datetime]) -> Dict[str, Any]:
        """
        Generate a compliance report.
        
        Args:
            report_type: Type of report to generate
            date_range: Date range for the report
            
        Returns:
            Compliance report data
        """
        return self.audit_trail.generate_svgx_compliance_report(report_type, date_range)
    
    def get_security_metrics(self) -> Dict[str, Any]:
        """
        Get comprehensive security metrics.
        
        Returns:
            Dictionary containing security metrics
        """
        return self.advanced_security.get_svgx_security_metrics()
    
    def rotate_encryption_keys(self, key_type: str = "all"):
        """
        Rotate encryption keys for enhanced security.
        
        Args:
            key_type: Type of keys to rotate (all, storage, transport, etc.)
        """
        self.encryption.rotate_svgx_keys(key_type)
        self.logger.info(f"Rotated encryption keys: {key_type}")
    
    def anonymize_data(self, data: Any, fields_to_anonymize: List[str] = None) -> Any:
        """
        Anonymize sensitive data.
        
        Args:
            data: Data to anonymize
            fields_to_anonymize: Specific fields to anonymize
            
        Returns:
            Anonymized data
        """
        return self.privacy_controls.anonymize_svgx_data(data, fields_to_anonymize)
    
    def classify_data(self, data_type: str, content: Any) -> str:
        """
        Classify data based on content and type.
        
        Args:
            data_type: Type of data
            content: Data content
            
        Returns:
            Classification level as string
        """
        classification = self.privacy_controls.classify_svgx_data(data_type, content)
        return classification.value 