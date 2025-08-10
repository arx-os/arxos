"""
Enterprise Security Infrastructure Module.

Provides comprehensive security services including authentication, authorization,
encryption, input validation, and audit logging for the Arxos platform.
"""

from .authentication import (
    AuthenticationService,
    AuthenticationToken,
    UserRole,
    Permission,
    RoleBasedAccessControl,
    PasswordPolicy,
    JWTTokenManager,
    require_permission,
    require_role
)

from .encryption import (
    EncryptionService,
    DataEncryption,
    SecureKeyManager,
    AsymmetricEncryption,
    SecureHasher,
    FieldLevelEncryption,
    EncryptionAlgorithm,
    EncryptionMetadata
)

from .input_validation import (
    InputValidator,
    ValidationRule,
    ValidationSeverity,
    InputSanitizer,
    SecurityValidationMiddleware,
    input_validator,
    validation_middleware
)

from .audit_logging import (
    AuditLogger,
    AuditEvent,
    AuditEventType,
    AuditSeverity,
    ComplianceStandard,
    audit_logger,
    audit_event
)


__all__ = [
    # Authentication & Authorization
    "AuthenticationService",
    "AuthenticationToken", 
    "UserRole",
    "Permission",
    "RoleBasedAccessControl",
    "PasswordPolicy",
    "JWTTokenManager",
    "require_permission",
    "require_role",
    
    # Encryption & Key Management
    "EncryptionService",
    "DataEncryption",
    "SecureKeyManager", 
    "AsymmetricEncryption",
    "SecureHasher",
    "FieldLevelEncryption",
    "EncryptionAlgorithm",
    "EncryptionMetadata",
    
    # Input Validation & Sanitization
    "InputValidator",
    "ValidationRule",
    "ValidationSeverity",
    "InputSanitizer",
    "SecurityValidationMiddleware",
    "input_validator",
    "validation_middleware",
    
    # Audit Logging & Compliance
    "AuditLogger",
    "AuditEvent",
    "AuditEventType",
    "AuditSeverity", 
    "ComplianceStandard",
    "audit_logger",
    "audit_event"
]


# Security configuration and initialization
def initialize_security_services(config: dict = None) -> dict:
    """Initialize all security services with configuration."""
    config = config or {}
    
    services = {
        "authentication": AuthenticationService(
            jwt_secret=config.get("jwt_secret", "default_secret_change_in_production")
        ),
        "encryption": EncryptionService(
            master_key=config.get("encryption_master_key")
        ),
        "input_validator": input_validator,
        "audit_logger": audit_logger
    }
    
    return services


def get_security_status() -> dict:
    """Get status of all security services."""
    return {
        "audit_logger": audit_logger.get_audit_statistics(),
        "validation_middleware": {
            "auto_sanitize": validation_middleware.auto_sanitize,
            "strict_mode": validation_middleware.strict_mode
        }
    }