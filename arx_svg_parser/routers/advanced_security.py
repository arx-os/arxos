"""
Advanced Security & Compliance API Router

RESTful API endpoints for enterprise-grade security features including:
- Privacy controls and data classification
- Multi-layer encryption
- Comprehensive audit trail
- Role-based access control (RBAC)
- AHJ API integration
- Data retention policies
"""

from fastapi import APIRouter, HTTPException, Depends, Query, Body
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import json

from services.advanced_security import (
    PrivacyControlsService, EncryptionService, AuditTrailService,
    RBACService, AdvancedSecurityService, DataClassification,
    AuditEventType, PermissionLevel
)

from services.ahj_api_integration import (
    AHJAPIIntegration, InspectionStatus, ViolationSeverity
)

from services.data_retention import (
    DataRetentionService, RetentionPolicyType, DeletionStrategy, DataType
)

from utils.logger import get_logger

logger = get_logger(__name__)

# Initialize router
router = APIRouter(prefix="/security", tags=["Advanced Security & Compliance"])

# Initialize services
privacy_service = PrivacyControlsService()
encryption_service = EncryptionService()
audit_service = AuditTrailService()
rbac_service = RBACService()
ahj_service = AHJAPIIntegration()
retention_service = DataRetentionService()
security_service = AdvancedSecurityService()


# Privacy Controls Endpoints
@router.post("/privacy/classify")
async def classify_data(
    data_type: str = Body(..., description="Type of data"),
    content: Any = Body(..., description="Data content for classification")
) -> Dict[str, Any]:
    """Classify data based on content and type"""
    try:
        classification = privacy_service.classify_data(data_type, content)
        return {
            "data_type": data_type,
            "classification": classification.value,
            "classification_level": classification.name
        }
    except Exception as e:
        logger.error(f"Data classification failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/privacy/controls")
async def apply_privacy_controls(
    data: Any = Body(..., description="Data to apply controls to"),
    classification: str = Body(..., description="Data classification level")
) -> Dict[str, Any]:
    """Apply privacy controls to data"""
    try:
        classification_enum = DataClassification(classification)
        result = privacy_service.apply_privacy_controls(data, classification_enum)
        return result
    except Exception as e:
        logger.error(f"Privacy controls application failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/privacy/anonymize")
async def anonymize_data(
    data: Dict[str, Any] = Body(..., description="Data to anonymize"),
    fields_to_anonymize: Optional[List[str]] = Body(None, description="Fields to anonymize")
) -> Dict[str, Any]:
    """Anonymize data for external sharing"""
    try:
        anonymized_data = privacy_service.anonymize_data(data, fields_to_anonymize)
        return {"anonymized_data": anonymized_data}
    except Exception as e:
        logger.error(f"Data anonymization failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Encryption Endpoints
@router.post("/encryption/encrypt")
async def encrypt_data(
    data: Any = Body(..., description="Data to encrypt"),
    layer: str = Body("storage", description="Encryption layer")
) -> Dict[str, Any]:
    """Encrypt data using specified layer"""
    try:
        encrypted_data = encryption_service.encrypt_data(data, layer)
        return {
            "encrypted_data": encrypted_data.hex(),
            "layer": layer,
            "data_size": len(encrypted_data)
        }
    except Exception as e:
        logger.error(f"Encryption failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/encryption/decrypt")
async def decrypt_data(
    encrypted_data: str = Body(..., description="Encrypted data (hex string)"),
    layer: str = Body("storage", description="Encryption layer")
) -> Dict[str, Any]:
    """Decrypt data using specified layer"""
    try:
        # Convert hex string back to bytes
        encrypted_bytes = bytes.fromhex(encrypted_data)
        decrypted_data = encryption_service.decrypt_data(encrypted_bytes, layer)
        return {
            "decrypted_data": decrypted_data.decode() if isinstance(decrypted_data, bytes) else decrypted_data,
            "layer": layer
        }
    except Exception as e:
        logger.error(f"Decryption failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/encryption/rotate-keys")
async def rotate_encryption_keys(
    key_type: str = Body("all", description="Type of key to rotate")
) -> Dict[str, Any]:
    """Rotate encryption keys"""
    try:
        encryption_service.rotate_keys(key_type)
        return {
            "message": f"Successfully rotated {key_type} encryption keys",
            "rotation_timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Key rotation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/encryption/metrics")
async def get_encryption_metrics() -> Dict[str, Any]:
    """Get encryption performance metrics"""
    try:
        metrics = encryption_service.get_metrics()
        return metrics
    except Exception as e:
        logger.error(f"Failed to get encryption metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Audit Trail Endpoints
@router.post("/audit/log")
async def log_audit_event(
    event_type: str = Body(..., description="Type of audit event"),
    user_id: str = Body(..., description="User ID"),
    resource_id: str = Body(..., description="Resource ID"),
    action: str = Body(..., description="Action performed"),
    details: Optional[Dict[str, Any]] = Body(None, description="Additional details"),
    correlation_id: Optional[str] = Body(None, description="Correlation ID"),
    ip_address: Optional[str] = Body(None, description="IP address"),
    user_agent: Optional[str] = Body(None, description="User agent"),
    success: bool = Body(True, description="Whether action was successful")
) -> Dict[str, Any]:
    """Log audit event"""
    try:
        event_type_enum = AuditEventType(event_type)
        event_id = audit_service.log_event(
            event_type_enum, user_id, resource_id, action,
            details, correlation_id, ip_address, user_agent, success
        )
        return {
            "event_id": event_id,
            "timestamp": datetime.now().isoformat(),
            "status": "logged"
        }
    except Exception as e:
        logger.error(f"Audit event logging failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/audit/logs")
async def get_audit_logs(
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    resource_id: Optional[str] = Query(None, description="Filter by resource ID"),
    start_date: Optional[str] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[str] = Query(None, description="End date (ISO format)")
) -> Dict[str, Any]:
    """Get audit logs with filtering"""
    try:
        filters = {}
        if event_type:
            filters["event_type"] = event_type
        if user_id:
            filters["user_id"] = user_id
        if resource_id:
            filters["resource_id"] = resource_id
        if start_date:
            filters["start_date"] = datetime.fromisoformat(start_date)
        if end_date:
            filters["end_date"] = datetime.fromisoformat(end_date)
        
        logs = audit_service.get_audit_logs(filters)
        return {
            "logs": logs,
            "total_count": len(logs),
            "filters_applied": filters
        }
    except Exception as e:
        logger.error(f"Failed to get audit logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/audit/compliance-report")
async def generate_compliance_report(
    report_type: str = Body(..., description="Type of compliance report"),
    start_date: str = Body(..., description="Start date (ISO format)"),
    end_date: str = Body(..., description="End date (ISO format)")
) -> Dict[str, Any]:
    """Generate compliance report"""
    try:
        date_range = (
            datetime.fromisoformat(start_date),
            datetime.fromisoformat(end_date)
        )
        report = audit_service.generate_compliance_report(report_type, date_range)
        return report
    except Exception as e:
        logger.error(f"Compliance report generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/audit/enforce-retention")
async def enforce_retention_policies() -> Dict[str, Any]:
    """Enforce data retention policies"""
    try:
        audit_service.enforce_retention_policies()
        return {
            "message": "Retention policies enforced successfully",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Retention policy enforcement failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/audit/metrics")
async def get_audit_metrics() -> Dict[str, Any]:
    """Get audit trail performance metrics"""
    try:
        metrics = audit_service.get_metrics()
        return metrics
    except Exception as e:
        logger.error(f"Failed to get audit metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# RBAC Endpoints
@router.post("/rbac/roles")
async def create_role(
    role_name: str = Body(..., description="Role name"),
    permissions: List[str] = Body(..., description="List of permissions"),
    description: str = Body("", description="Role description")
) -> Dict[str, Any]:
    """Create role with specific permissions"""
    try:
        role_id = rbac_service.create_role(role_name, permissions, description)
        return {
            "role_id": role_id,
            "role_name": role_name,
            "permissions": permissions,
            "description": description
        }
    except Exception as e:
        logger.error(f"Role creation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/rbac/assign")
async def assign_user_to_role(
    user_id: str = Body(..., description="User ID"),
    role_id: str = Body(..., description="Role ID")
) -> Dict[str, Any]:
    """Assign user to role"""
    try:
        success = rbac_service.assign_user_to_role(user_id, role_id)
        if success:
            return {
                "message": f"User {user_id} assigned to role {role_id}",
                "user_id": user_id,
                "role_id": role_id
            }
        else:
            raise HTTPException(status_code=400, detail="User already assigned to role")
    except Exception as e:
        logger.error(f"User role assignment failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/rbac/check-permission")
async def check_permission(
    user_id: str = Body(..., description="User ID"),
    resource: str = Body(..., description="Resource"),
    action: str = Body(..., description="Action")
) -> Dict[str, Any]:
    """Check if user has permission for action on resource"""
    try:
        has_permission = rbac_service.check_permission(user_id, resource, action)
        return {
            "user_id": user_id,
            "resource": resource,
            "action": action,
            "has_permission": has_permission
        }
    except Exception as e:
        logger.error(f"Permission check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/rbac/users/{user_id}/permissions")
async def get_user_permissions(user_id: str) -> Dict[str, Any]:
    """Get all permissions for user"""
    try:
        permissions = rbac_service.get_user_permissions(user_id)
        return {
            "user_id": user_id,
            "permissions": permissions,
            "permission_count": len(permissions)
        }
    except Exception as e:
        logger.error(f"Failed to get user permissions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/rbac/assign")
async def remove_user_from_role(
    user_id: str = Body(..., description="User ID"),
    role_id: str = Body(..., description="Role ID")
) -> Dict[str, Any]:
    """Remove user from role"""
    try:
        success = rbac_service.remove_user_from_role(user_id, role_id)
        if success:
            return {
                "message": f"User {user_id} removed from role {role_id}",
                "user_id": user_id,
                "role_id": role_id
            }
        else:
            raise HTTPException(status_code=400, detail="User not assigned to role")
    except Exception as e:
        logger.error(f"User role removal failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/rbac/metrics")
async def get_rbac_metrics() -> Dict[str, Any]:
    """Get RBAC performance metrics"""
    try:
        metrics = rbac_service.get_metrics()
        return metrics
    except Exception as e:
        logger.error(f"Failed to get RBAC metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# AHJ API Endpoints
@router.post("/ahj/inspections")
async def create_inspection_layer(
    building_id: str = Body(..., description="Building ID"),
    ahj_id: str = Body(..., description="AHJ ID"),
    inspector_id: str = Body(..., description="Inspector ID"),
    metadata: Optional[Dict[str, Any]] = Body(None, description="Additional metadata")
) -> Dict[str, Any]:
    """Create AHJ inspection layer"""
    try:
        layer_id = ahj_service.create_inspection_layer(
            building_id, ahj_id, inspector_id, metadata
        )
        return {
            "layer_id": layer_id,
            "building_id": building_id,
            "ahj_id": ahj_id,
            "inspector_id": inspector_id,
            "created_at": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Inspection layer creation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ahj/annotations")
async def add_inspection_annotation(
    layer_id: str = Body(..., description="Inspection layer ID"),
    inspector_id: str = Body(..., description="Inspector ID"),
    location: Dict[str, Any] = Body(..., description="Annotation location"),
    annotation_type: str = Body(..., description="Type of annotation"),
    description: str = Body(..., description="Annotation description"),
    severity: str = Body(..., description="Violation severity"),
    code_reference: str = Body(..., description="Building code reference"),
    image_attachments: Optional[List[str]] = Body(None, description="Image attachments"),
    metadata: Optional[Dict[str, Any]] = Body(None, description="Additional metadata")
) -> Dict[str, Any]:
    """Add inspection annotation"""
    try:
        severity_enum = ViolationSeverity(severity)
        annotation_id = ahj_service.add_inspection_annotation(
            layer_id, inspector_id, location, annotation_type,
            description, severity_enum, code_reference,
            image_attachments, metadata
        )
        return {
            "annotation_id": annotation_id,
            "layer_id": layer_id,
            "annotation_type": annotation_type,
            "severity": severity,
            "created_at": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Inspection annotation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ahj/violations")
async def add_code_violation(
    layer_id: str = Body(..., description="Inspection layer ID"),
    inspector_id: str = Body(..., description="Inspector ID"),
    code_section: str = Body(..., description="Building code section"),
    description: str = Body(..., description="Violation description"),
    severity: str = Body(..., description="Violation severity"),
    location: Dict[str, Any] = Body(..., description="Violation location"),
    required_action: str = Body(..., description="Required corrective action"),
    deadline: Optional[str] = Body(None, description="Compliance deadline (ISO format)"),
    metadata: Optional[Dict[str, Any]] = Body(None, description="Additional metadata")
) -> Dict[str, Any]:
    """Add building code violation"""
    try:
        severity_enum = ViolationSeverity(severity)
        deadline_date = datetime.fromisoformat(deadline) if deadline else None
        
        violation_id = ahj_service.add_code_violation(
            layer_id, inspector_id, code_section, description,
            severity_enum, location, required_action, deadline_date, metadata
        )
        return {
            "violation_id": violation_id,
            "layer_id": layer_id,
            "code_section": code_section,
            "severity": severity,
            "created_at": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Code violation creation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ahj/inspections/{layer_id}")
async def get_inspection_history(layer_id: str) -> Dict[str, Any]:
    """Get complete inspection history"""
    try:
        history = ahj_service.get_inspection_history(layer_id)
        return history
    except Exception as e:
        logger.error(f"Failed to get inspection history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ahj/jurisdictions")
async def get_ahj_jurisdictions() -> Dict[str, Any]:
    """Get all supported AHJ jurisdictions"""
    try:
        jurisdictions = ahj_service.get_ahj_jurisdictions()
        return {
            "jurisdictions": jurisdictions,
            "total_count": len(jurisdictions)
        }
    except Exception as e:
        logger.error(f"Failed to get AHJ jurisdictions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ahj/buildings/{building_id}/inspections")
async def get_building_inspections(building_id: str) -> Dict[str, Any]:
    """Get all inspections for a building"""
    try:
        inspections = ahj_service.get_building_inspections(building_id)
        return {
            "building_id": building_id,
            "inspections": inspections,
            "total_count": len(inspections)
        }
    except Exception as e:
        logger.error(f"Failed to get building inspections: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/ahj/violations/{violation_id}")
async def update_violation_status(
    violation_id: str,
    status: str = Body(..., description="New status"),
    notes: Optional[str] = Body(None, description="Additional notes")
) -> Dict[str, Any]:
    """Update violation status"""
    try:
        success = ahj_service.update_violation_status(violation_id, status, notes)
        if success:
            return {
                "violation_id": violation_id,
                "status": status,
                "updated_at": datetime.now().isoformat()
            }
        else:
            raise HTTPException(status_code=404, detail="Violation not found")
    except Exception as e:
        logger.error(f"Violation status update failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ahj/compliance-report")
async def generate_ahj_compliance_report(
    building_id: str = Body(..., description="Building ID"),
    start_date: Optional[str] = Body(None, description="Start date (ISO format)"),
    end_date: Optional[str] = Body(None, description="End date (ISO format)")
) -> Dict[str, Any]:
    """Generate compliance report for building"""
    try:
        date_range = None
        if start_date and end_date:
            date_range = (
                datetime.fromisoformat(start_date),
                datetime.fromisoformat(end_date)
            )
        
        report = ahj_service.generate_compliance_report(building_id, date_range)
        return report
    except Exception as e:
        logger.error(f"AHJ compliance report generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ahj/metrics")
async def get_ahj_metrics() -> Dict[str, Any]:
    """Get AHJ API performance metrics"""
    try:
        metrics = ahj_service.get_metrics()
        return metrics
    except Exception as e:
        logger.error(f"Failed to get AHJ metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Data Retention Endpoints
@router.post("/retention/policies")
async def create_retention_policy(
    data_type: str = Body(..., description="Data type"),
    retention_period_days: int = Body(..., description="Retention period in days"),
    deletion_strategy: str = Body(..., description="Deletion strategy"),
    description: str = Body("", description="Policy description"),
    metadata: Optional[Dict[str, Any]] = Body(None, description="Additional metadata")
) -> Dict[str, Any]:
    """Create data retention policy"""
    try:
        data_type_enum = DataType(data_type)
        deletion_strategy_enum = DeletionStrategy(deletion_strategy)
        
        policy_id = retention_service.create_retention_policy(
            data_type_enum, retention_period_days, deletion_strategy_enum,
            description, metadata
        )
        return {
            "policy_id": policy_id,
            "data_type": data_type,
            "retention_period_days": retention_period_days,
            "deletion_strategy": deletion_strategy,
            "description": description
        }
    except Exception as e:
        logger.error(f"Retention policy creation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/retention/apply")
async def apply_retention_policy(
    data_id: str = Body(..., description="Data ID"),
    policy_id: str = Body(..., description="Policy ID"),
    data_type: Optional[str] = Body(None, description="Data type override")
) -> Dict[str, Any]:
    """Apply retention policy to data"""
    try:
        data_type_enum = DataType(data_type) if data_type else None
        success = retention_service.apply_retention_policy(data_id, policy_id, data_type_enum)
        
        if success:
            return {
                "data_id": data_id,
                "policy_id": policy_id,
                "applied_at": datetime.now().isoformat()
            }
        else:
            raise HTTPException(status_code=400, detail="Failed to apply retention policy")
    except Exception as e:
        logger.error(f"Retention policy application failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/retention/schedule-deletion")
async def schedule_data_deletion(
    data_id: str = Body(..., description="Data ID"),
    deletion_date: Optional[str] = Body(None, description="Deletion date (ISO format)"),
    deletion_strategy: Optional[str] = Body(None, description="Deletion strategy")
) -> Dict[str, Any]:
    """Schedule data for deletion"""
    try:
        deletion_strategy_enum = DeletionStrategy(deletion_strategy) if deletion_strategy else None
        deletion_date_obj = datetime.fromisoformat(deletion_date) if deletion_date else None
        
        job_id = retention_service.schedule_data_deletion(
            data_id, deletion_date_obj, deletion_strategy_enum
        )
        return {
            "job_id": job_id,
            "data_id": data_id,
            "scheduled_at": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Data deletion scheduling failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/retention/execute")
async def execute_retention_policies() -> Dict[str, Any]:
    """Execute scheduled retention policies"""
    try:
        results = retention_service.execute_retention_policies()
        return results
    except Exception as e:
        logger.error(f"Retention policy execution failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/retention/archive")
async def archive_data(
    data_id: str = Body(..., description="Data ID"),
    archive_path: Optional[str] = Body(None, description="Custom archive path")
) -> Dict[str, Any]:
    """Archive data for long-term storage"""
    try:
        success = retention_service.archive_data(data_id, archive_path)
        if success:
            return {
                "data_id": data_id,
                "archived_at": datetime.now().isoformat(),
                "success": True
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to archive data")
    except Exception as e:
        logger.error(f"Data archiving failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/retention/policies")
async def get_retention_policies() -> Dict[str, Any]:
    """Get all retention policies"""
    try:
        policies = retention_service.get_retention_policies()
        return {
            "policies": policies,
            "total_count": len(policies)
        }
    except Exception as e:
        logger.error(f"Failed to get retention policies: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/retention/lifecycle")
async def get_data_lifecycle(
    data_id: Optional[str] = Query(None, description="Specific data ID")
) -> Dict[str, Any]:
    """Get data lifecycle information"""
    try:
        lifecycle = retention_service.get_data_lifecycle(data_id)
        return {
            "lifecycle": lifecycle,
            "total_count": len(lifecycle)
        }
    except Exception as e:
        logger.error(f"Failed to get data lifecycle: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/retention/compliance-report")
async def generate_retention_compliance_report(
    start_date: Optional[str] = Body(None, description="Start date (ISO format)"),
    end_date: Optional[str] = Body(None, description="End date (ISO format)")
) -> Dict[str, Any]:
    """Generate compliance report for data retention"""
    try:
        date_range = None
        if start_date and end_date:
            date_range = (
                datetime.fromisoformat(start_date),
                datetime.fromisoformat(end_date)
            )
        
        report = retention_service.generate_compliance_report(date_range)
        return report
    except Exception as e:
        logger.error(f"Retention compliance report generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/retention/metrics")
async def get_retention_metrics() -> Dict[str, Any]:
    """Get data retention performance metrics"""
    try:
        metrics = retention_service.get_metrics()
        return metrics
    except Exception as e:
        logger.error(f"Failed to get retention metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Integrated Security Endpoints
@router.post("/secure-access")
async def secure_data_access(
    user_id: str = Body(..., description="User ID"),
    resource_id: str = Body(..., description="Resource ID"),
    action: str = Body(..., description="Action"),
    data: Any = Body(..., description="Data to access"),
    data_type: str = Body("building_data", description="Data type"),
    correlation_id: Optional[str] = Body(None, description="Correlation ID")
) -> Dict[str, Any]:
    """Secure data access with full security controls"""
    try:
        result = security_service.secure_data_access(
            user_id, resource_id, action, data, data_type, correlation_id
        )
        return result
    except Exception as e:
        logger.error(f"Secure data access failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics")
async def get_security_metrics() -> Dict[str, Any]:
    """Get comprehensive security metrics"""
    try:
        metrics = security_service.get_security_metrics()
        return metrics
    except Exception as e:
        logger.error(f"Failed to get security metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Health Check Endpoint
@router.get("/health")
async def security_health_check() -> Dict[str, Any]:
    """Health check for security services"""
    try:
        return {
            "status": "healthy",
            "services": {
                "privacy_controls": "operational",
                "encryption": "operational",
                "audit_trail": "operational",
                "rbac": "operational",
                "ahj_api": "operational",
                "data_retention": "operational"
            },
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Security health check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 