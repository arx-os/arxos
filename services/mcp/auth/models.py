"""
Security Models for Authentication and Authorization

Pydantic models for MFA, OAuth, audit logging, and data protection
with proper validation and security practices.
"""

from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field, validator, EmailStr


class MFAMethod(str, Enum):
    """MFA methods supported by the system"""

    TOTP = "totp"
    SMS = "sms"
    EMAIL = "email"
    HARDWARE_TOKEN = "hardware_token"
    BACKUP_CODE = "backup_code"


class OAuthProvider(str, Enum):
    """OAuth providers supported by the system"""

    GOOGLE = "google"
    MICROSOFT = "microsoft"
    GITHUB = "github"
    FACEBOOK = "facebook"
    LINKEDIN = "linkedin"
    CUSTOM = "custom"


class AuditEventType(str, Enum):
    """Types of audit events"""

    LOGIN = "login"
    LOGOUT = "logout"
    MFA_SETUP = "mfa_setup"
    MFA_VERIFY = "mfa_verify"
    PASSWORD_CHANGE = "password_change"
    ROLE_CHANGE = "role_change"
    PERMISSION_CHANGE = "permission_change"
    DATA_ACCESS = "data_access"
    DATA_MODIFICATION = "data_modification"
    SYSTEM_CONFIG = "system_config"
    SECURITY_EVENT = "security_event"


class SecurityLevel(str, Enum):
    """Security levels for data protection"""

    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"
    SECRET = "secret"


class MFAConfig(BaseModel):
    """MFA configuration for a user"""

    user_id: str = Field(..., description="User ID")
    method: MFAMethod = Field(..., description="MFA method")
    secret: Optional[str] = Field(None, description="TOTP secret (for TOTP method)")
    backup_codes: List[str] = Field(
        default_factory=list, description="Hashed backup codes"
    )
    is_enabled: bool = Field(False, description="Whether MFA is enabled")
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="Creation timestamp"
    )
    enabled_at: Optional[datetime] = Field(None, description="When MFA was enabled")
    last_used: Optional[datetime] = Field(None, description="Last time MFA was used")


class MFAStatus(BaseModel):
    """MFA status for a user"""

    user_id: str = Field(..., description="User ID")
    method: MFAMethod = Field(..., description="MFA method")
    is_enabled: bool = Field(..., description="Whether MFA is enabled")
    is_configured: bool = Field(..., description="Whether MFA is configured")
    backup_codes_remaining: int = Field(
        ..., description="Number of backup codes remaining"
    )
    created_at: Optional[datetime] = Field(None, description="When MFA was created")
    enabled_at: Optional[datetime] = Field(None, description="When MFA was enabled")


class MFAToken(BaseModel):
    """MFA token for verification"""

    user_id: str = Field(..., description="User ID")
    method: MFAMethod = Field(..., description="MFA method")
    token: str = Field(..., description="Token to verify")
    ip_address: Optional[str] = Field(None, description="IP address of the request")
    user_agent: Optional[str] = Field(None, description="User agent string")


class MFAAuditLog(BaseModel):
    """MFA audit log entry"""

    user_id: str = Field(..., description="User ID")
    method: MFAMethod = Field(..., description="MFA method used")
    success: bool = Field(..., description="Whether the attempt was successful")
    ip_address: Optional[str] = Field(None, description="IP address")
    user_agent: Optional[str] = Field(None, description="User agent string")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Event timestamp"
    )


class OAuthConfig(BaseModel):
    """OAuth configuration"""

    provider: OAuthProvider = Field(..., description="OAuth provider")
    client_id: str = Field(..., description="OAuth client ID")
    client_secret: str = Field(..., description="OAuth client secret")
    redirect_uri: str = Field(..., description="OAuth redirect URI")
    scopes: List[str] = Field(default_factory=list, description="OAuth scopes")
    is_enabled: bool = Field(True, description="Whether OAuth is enabled")
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="Creation timestamp"
    )


class OAuthToken(BaseModel):
    """OAuth token information"""

    user_id: str = Field(..., description="User ID")
    provider: OAuthProvider = Field(..., description="OAuth provider")
    access_token: str = Field(..., description="OAuth access token")
    refresh_token: Optional[str] = Field(None, description="OAuth refresh token")
    token_type: str = Field("Bearer", description="Token type")
    expires_at: Optional[datetime] = Field(None, description="Token expiration")
    scopes: List[str] = Field(default_factory=list, description="Token scopes")
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="Creation timestamp"
    )


class OAuthUserInfo(BaseModel):
    """OAuth user information"""

    user_id: str = Field(..., description="User ID")
    provider: OAuthProvider = Field(..., description="OAuth provider")
    provider_user_id: str = Field(..., description="Provider user ID")
    email: EmailStr = Field(..., description="User email")
    name: Optional[str] = Field(None, description="User name")
    picture: Optional[str] = Field(None, description="User picture URL")
    locale: Optional[str] = Field(None, description="User locale")
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="Creation timestamp"
    )


class AuditLogEntry(BaseModel):
    """Audit log entry"""

    event_id: str = Field(..., description="Unique event ID")
    user_id: Optional[str] = Field(None, description="User ID")
    event_type: AuditEventType = Field(..., description="Event type")
    description: str = Field(..., description="Event description")
    ip_address: Optional[str] = Field(None, description="IP address")
    user_agent: Optional[str] = Field(None, description="User agent string")
    resource_type: Optional[str] = Field(None, description="Resource type")
    resource_id: Optional[str] = Field(None, description="Resource ID")
    old_value: Optional[Dict[str, Any]] = Field(
        None, description="Old value (for modifications)"
    )
    new_value: Optional[Dict[str, Any]] = Field(
        None, description="New value (for modifications)"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Event timestamp"
    )
    session_id: Optional[str] = Field(None, description="Session ID")


class SecurityEvent(BaseModel):
    """Security event for monitoring"""

    event_id: str = Field(..., description="Unique event ID")
    event_type: str = Field(..., description="Event type")
    severity: str = Field(
        ..., description="Event severity (low, medium, high, critical)"
    )
    description: str = Field(..., description="Event description")
    user_id: Optional[str] = Field(None, description="User ID")
    ip_address: Optional[str] = Field(None, description="IP address")
    user_agent: Optional[str] = Field(None, description="User agent string")
    source: str = Field(..., description="Event source")
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Event timestamp"
    )
    resolved: bool = Field(False, description="Whether the event is resolved")
    resolved_at: Optional[datetime] = Field(
        None, description="When the event was resolved"
    )
    resolved_by: Optional[str] = Field(None, description="Who resolved the event")


class DataProtectionConfig(BaseModel):
    """Data protection configuration"""

    encryption_enabled: bool = Field(True, description="Whether encryption is enabled")
    encryption_algorithm: str = Field("AES-256-GCM", description="Encryption algorithm")
    key_rotation_days: int = Field(90, description="Key rotation period in days")
    data_retention_days: int = Field(2555, description="Data retention period in days")
    backup_encryption: bool = Field(True, description="Whether backups are encrypted")
    audit_log_retention_days: int = Field(365, description="Audit log retention period")
    pii_detection: bool = Field(True, description="Whether PII detection is enabled")
    data_classification: bool = Field(
        True, description="Whether data classification is enabled"
    )


class DataClassification(BaseModel):
    """Data classification information"""

    resource_id: str = Field(..., description="Resource ID")
    resource_type: str = Field(..., description="Resource type")
    security_level: SecurityLevel = Field(..., description="Security level")
    classification_reason: str = Field(..., description="Reason for classification")
    classified_by: str = Field(..., description="Who classified the data")
    classified_at: datetime = Field(
        default_factory=datetime.utcnow, description="Classification timestamp"
    )
    pii_fields: List[str] = Field(
        default_factory=list, description="PII fields identified"
    )
    retention_policy: Optional[str] = Field(None, description="Retention policy")
    access_controls: List[str] = Field(
        default_factory=list, description="Access controls"
    )


class PrivacyConsent(BaseModel):
    """Privacy consent information"""

    user_id: str = Field(..., description="User ID")
    consent_type: str = Field(..., description="Type of consent")
    consent_version: str = Field(..., description="Consent version")
    granted: bool = Field(..., description="Whether consent was granted")
    granted_at: datetime = Field(
        default_factory=datetime.utcnow, description="When consent was granted"
    )
    revoked_at: Optional[datetime] = Field(None, description="When consent was revoked")
    ip_address: Optional[str] = Field(
        None, description="IP address when consent was given"
    )
    user_agent: Optional[str] = Field(
        None, description="User agent when consent was given"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )


class SecurityPolicy(BaseModel):
    """Security policy configuration"""

    policy_id: str = Field(..., description="Policy ID")
    policy_name: str = Field(..., description="Policy name")
    policy_type: str = Field(..., description="Policy type")
    description: str = Field(..., description="Policy description")
    enabled: bool = Field(True, description="Whether the policy is enabled")
    rules: List[Dict[str, Any]] = Field(
        default_factory=list, description="Policy rules"
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="Creation timestamp"
    )
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")
    created_by: str = Field(..., description="Who created the policy")


class ComplianceReport(BaseModel):
    """Compliance report"""

    report_id: str = Field(..., description="Report ID")
    report_type: str = Field(..., description="Report type")
    report_period: str = Field(..., description="Report period")
    generated_at: datetime = Field(
        default_factory=datetime.utcnow, description="Generation timestamp"
    )
    generated_by: str = Field(..., description="Who generated the report")
    summary: Dict[str, Any] = Field(default_factory=dict, description="Report summary")
    details: List[Dict[str, Any]] = Field(
        default_factory=list, description="Report details"
    )
    compliance_score: float = Field(
        ..., ge=0.0, le=100.0, description="Compliance score"
    )
    recommendations: List[str] = Field(
        default_factory=list, description="Recommendations"
    )


class SecurityMetrics(BaseModel):
    """Security metrics"""

    total_users: int = Field(..., description="Total number of users")
    mfa_enabled_users: int = Field(..., description="Users with MFA enabled")
    mfa_enabled_percentage: float = Field(
        ..., ge=0.0, le=100.0, description="MFA enabled percentage"
    )
    failed_login_attempts: int = Field(
        ..., description="Failed login attempts in period"
    )
    successful_logins: int = Field(..., description="Successful logins in period")
    security_events: int = Field(..., description="Security events in period")
    critical_events: int = Field(..., description="Critical security events in period")
    average_session_duration: float = Field(
        ..., description="Average session duration in minutes"
    )
    active_sessions: int = Field(..., description="Currently active sessions")
    data_breach_incidents: int = Field(
        ..., description="Data breach incidents in period"
    )
    compliance_score: float = Field(
        ..., ge=0.0, le=100.0, description="Overall compliance score"
    )
    last_updated: datetime = Field(
        default_factory=datetime.utcnow, description="Last update timestamp"
    )


class MFARequest(BaseModel):
    """MFA setup request"""

    user_id: str = Field(..., description="User ID")
    method: MFAMethod = Field(..., description="MFA method")
    username: str = Field(..., description="Username for setup")


class MFAVerificationRequest(BaseModel):
    """MFA verification request"""

    user_id: str = Field(..., description="User ID")
    method: MFAMethod = Field(..., description="MFA method")
    token: str = Field(..., description="Token to verify")
    ip_address: Optional[str] = Field(None, description="IP address")
    user_agent: Optional[str] = Field(None, description="User agent string")


class OAuthRequest(BaseModel):
    """OAuth authentication request"""

    provider: OAuthProvider = Field(..., description="OAuth provider")
    redirect_uri: str = Field(..., description="Redirect URI")
    state: Optional[str] = Field(None, description="OAuth state parameter")
    scopes: List[str] = Field(default_factory=list, description="Requested scopes")


class OAuthCallback(BaseModel):
    """OAuth callback data"""

    provider: OAuthProvider = Field(..., description="OAuth provider")
    code: str = Field(..., description="Authorization code")
    state: Optional[str] = Field(None, description="OAuth state parameter")
    error: Optional[str] = Field(None, description="OAuth error")
    error_description: Optional[str] = Field(
        None, description="OAuth error description"
    )


class AuditLogRequest(BaseModel):
    """Audit log query request"""

    user_id: Optional[str] = Field(None, description="Filter by user ID")
    event_type: Optional[AuditEventType] = Field(
        None, description="Filter by event type"
    )
    start_date: Optional[datetime] = Field(None, description="Start date")
    end_date: Optional[datetime] = Field(None, description="End date")
    resource_type: Optional[str] = Field(None, description="Filter by resource type")
    resource_id: Optional[str] = Field(None, description="Filter by resource ID")
    limit: int = Field(100, ge=1, le=1000, description="Maximum number of results")
    offset: int = Field(0, ge=0, description="Result offset")


class SecurityEventRequest(BaseModel):
    """Security event query request"""

    event_type: Optional[str] = Field(None, description="Filter by event type")
    severity: Optional[str] = Field(None, description="Filter by severity")
    source: Optional[str] = Field(None, description="Filter by source")
    resolved: Optional[bool] = Field(None, description="Filter by resolved status")
    start_date: Optional[datetime] = Field(None, description="Start date")
    end_date: Optional[datetime] = Field(None, description="End date")
    limit: int = Field(100, ge=1, le=1000, description="Maximum number of results")
    offset: int = Field(0, ge=0, description="Result offset")
