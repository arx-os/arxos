#!/usr/bin/env python3
"""
Enterprise Security System for MCP

This module provides enterprise-grade security features including:
- Advanced authentication and authorization
- Data encryption and key management
- Audit logging and compliance
- Security monitoring and threat detection
- Input validation and sanitization
- Session management and security headers
"""

import os
import logging
import hashlib
import hmac
import secrets
import time
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization
import jwt
from fastapi import Request, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, validator

logger = logging.getLogger(__name__)


class SecurityLevel(str, Enum):
    """Security level enumeration"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AuditEventType(str, Enum):
    """Audit event types"""

    LOGIN = "login"
    LOGOUT = "logout"
    DATA_ACCESS = "data_access"
    DATA_MODIFICATION = "data_modification"
    CONFIGURATION_CHANGE = "configuration_change"
    SECURITY_EVENT = "security_event"
    SYSTEM_EVENT = "system_event"


@dataclass
class AuditEvent:
    """Audit event structure"""

    id: str
    event_type: AuditEventType
    user_id: str
    resource: str
    action: str
    details: Dict[str, Any]
    ip_address: str
    user_agent: str
    timestamp: datetime = field(default_factory=datetime.now)
    session_id: Optional[str] = None
    success: bool = True


@dataclass
class SecurityConfig:
    """Security configuration"""

    encryption_key: str
    jwt_secret: str
    session_timeout: int = 3600  # 1 hour
    max_login_attempts: int = 5
    lockout_duration: int = 900  # 15 minutes
    password_min_length: int = 12
    require_special_chars: bool = True
    require_numbers: bool = True
    require_uppercase: bool = True
    require_lowercase: bool = True
    max_session_age: int = 86400  # 24 hours
    security_headers: Dict[str, str] = field(default_factory=dict)


class EncryptionManager:
    """Manages data encryption and key management"""

    def __init__(self, master_key: str):
        self.master_key = master_key.encode()
        self.fernet = Fernet(
            base64.urlsafe_b64encode(hashlib.sha256(self.master_key).digest())
        )

        # Generate RSA key pair for asymmetric encryption
        self.private_key = rsa.generate_private_key(
            public_exponent=65537, key_size=2048
        )
        self.public_key = self.private_key.public_key()

    def encrypt_data(self, data: str) -> str:
        """Encrypt sensitive data"""
        return self.fernet.encrypt(data.encode()).decode()

    def decrypt_data(self, encrypted_data: str) -> str:
        """Decrypt sensitive data"""
        return self.fernet.decrypt(encrypted_data.encode()).decode()

    def encrypt_file(self, file_path: str, output_path: str) -> bool:
        """Encrypt a file"""
        try:
            with open(file_path, "rb") as f:
                data = f.read()

            encrypted_data = self.fernet.encrypt(data)

            with open(output_path, "wb") as f:
                f.write(encrypted_data)

            return True
        except Exception as e:
            logger.error(f"Error encrypting file: {e}")
            return False

    def decrypt_file(self, encrypted_file_path: str, output_path: str) -> bool:
        """Decrypt a file"""
        try:
            with open(encrypted_file_path, "rb") as f:
                encrypted_data = f.read()

            decrypted_data = self.fernet.decrypt(encrypted_data)

            with open(output_path, "wb") as f:
                f.write(decrypted_data)

            return True
        except Exception as e:
            logger.error(f"Error decrypting file: {e}")
            return False

    def get_public_key_pem(self) -> str:
        """Get public key in PEM format"""
        return self.public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        ).decode()


class AuditLogger:
    """Comprehensive audit logging system"""

    def __init__(self, log_file: str = "audit.log"):
        self.log_file = log_file
        self.events: List[AuditEvent] = []
        self.sensitive_fields = {"password", "secret", "token", "key"}

    def log_event(self, event: AuditEvent):
        """Log an audit event"""
        # Sanitize sensitive data
        sanitized_details = self._sanitize_data(event.details)
        event.details = sanitized_details

        # Store event
        self.events.append(event)

        # Write to log file
        log_entry = {
            "id": event.id,
            "event_type": event.event_type.value,
            "user_id": event.user_id,
            "resource": event.resource,
            "action": event.action,
            "details": event.details,
            "ip_address": event.ip_address,
            "user_agent": event.user_agent,
            "timestamp": event.timestamp.isoformat(),
            "session_id": event.session_id,
            "success": event.success,
        }

        with open(self.log_file, "a") as f:
            f.write(json.dumps(log_entry) + "\n")

        logger.info(f"Audit event logged: {event.event_type.value} by {event.user_id}")

    def _sanitize_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize sensitive data in audit logs"""
        sanitized = {}
        for key, value in data.items():
            if key.lower() in self.sensitive_fields:
                sanitized[key] = "***REDACTED***"
            elif isinstance(value, dict):
                sanitized[key] = self._sanitize_data(value)
            else:
                sanitized[key] = value
        return sanitized

    def get_events(
        self,
        user_id: Optional[str] = None,
        event_type: Optional[AuditEventType] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> List[AuditEvent]:
        """Get filtered audit events"""
        events = self.events

        if user_id:
            events = [e for e in events if e.user_id == user_id]

        if event_type:
            events = [e for e in events if e.event_type == event_type]

        if start_time:
            events = [e for e in events if e.timestamp >= start_time]

        if end_time:
            events = [e for e in events if e.timestamp <= end_time]

        return events

    def get_security_report(self) -> Dict[str, Any]:
        """Generate security audit report"""
        total_events = len(self.events)
        failed_events = len([e for e in self.events if not e.success])

        # Event type distribution
        event_counts = {}
        for event in self.events:
            event_type = event.event_type.value
            event_counts[event_type] = event_counts.get(event_type, 0) + 1

        # Recent activity
        recent_events = [
            e for e in self.events if e.timestamp > datetime.now() - timedelta(hours=24)
        ]

        return {
            "total_events": total_events,
            "failed_events": failed_events,
            "success_rate": (
                ((total_events - failed_events) / total_events * 100)
                if total_events > 0
                else 0
            ),
            "event_type_distribution": event_counts,
            "recent_activity": len(recent_events),
            "last_event": (
                self.events[-1].timestamp.isoformat() if self.events else None
            ),
        }


class SecurityMonitor:
    """Real-time security monitoring and threat detection"""

    def __init__(self):
        self.suspicious_activities: List[Dict[str, Any]] = []
        self.blocked_ips: Dict[str, datetime] = {}
        self.rate_limits: Dict[str, List[datetime]] = {}
        self.threat_patterns: Dict[str, Any] = self._load_threat_patterns()

    def _load_threat_patterns(self) -> Dict[str, Any]:
        """Load threat detection patterns"""
        return {
            "sql_injection": [
                "SELECT",
                "INSERT",
                "UPDATE",
                "DELETE",
                "DROP",
                "UNION",
                "OR 1=1",
                "OR '1'='1'",
                "'; DROP TABLE",
                "/*",
                "*/",
            ],
            "xss": [
                "<script>",
                "javascript:",
                "onload=",
                "onerror=",
                "onclick=",
                "alert(",
                "confirm(",
                "prompt(",
                "eval(",
            ],
            "path_traversal": ["../", "..\\", "/etc/", "C:\\", "..%2f", "..%5c"],
            "command_injection": ["|", "&", ";", "`", "$(", "eval(", "exec("],
        }

    def analyze_request(self, request: Request, user_id: str) -> Dict[str, Any]:
        """Analyze request for security threats"""
        analysis = {"threats_detected": [], "risk_score": 0, "recommendations": []}

        # Check for suspicious patterns in URL and headers
        url = str(request.url)
        headers = dict(request.headers)

        # Check for SQL injection
        for pattern in self.threat_patterns["sql_injection"]:
            if pattern.lower() in url.lower():
                analysis["threats_detected"].append("sql_injection")
                analysis["risk_score"] += 50

        # Check for XSS
        for pattern in self.threat_patterns["xss"]:
            if pattern.lower() in url.lower():
                analysis["threats_detected"].append("xss")
                analysis["risk_score"] += 40

        # Check for path traversal
        for pattern in self.threat_patterns["path_traversal"]:
            if pattern.lower() in url.lower():
                analysis["threats_detected"].append("path_traversal")
                analysis["risk_score"] += 60

        # Check for command injection
        for pattern in self.threat_patterns["command_injection"]:
            if pattern.lower() in url.lower():
                analysis["threats_detected"].append("command_injection")
                analysis["risk_score"] += 70

        # Check rate limiting
        client_ip = request.client.host
        if self._is_rate_limited(client_ip):
            analysis["threats_detected"].append("rate_limit_exceeded")
            analysis["risk_score"] += 30

        # Generate recommendations
        if analysis["risk_score"] > 50:
            analysis["recommendations"].append("Block this request")
        if analysis["risk_score"] > 30:
            analysis["recommendations"].append("Log this activity")
        if analysis["risk_score"] > 20:
            analysis["recommendations"].append("Monitor this user")

        return analysis

    def _is_rate_limited(self, client_ip: str) -> bool:
        """Check if IP is rate limited"""
        now = datetime.now()

        # Clean old entries
        self.rate_limits = {
            ip: times
            for ip, times in self.rate_limits.items()
            if any(now - time < timedelta(minutes=5) for time in times)
        }

        # Check current IP
        if client_ip in self.rate_limits:
            recent_requests = [
                time
                for time in self.rate_limits[client_ip]
                if now - time < timedelta(minutes=1)
            ]
            if len(recent_requests) > 100:  # 100 requests per minute
                return True

        return False

    def record_request(self, client_ip: str):
        """Record a request for rate limiting"""
        if client_ip not in self.rate_limits:
            self.rate_limits[client_ip] = []

        self.rate_limits[client_ip].append(datetime.now())

    def block_ip(self, client_ip: str, duration: int = 3600):
        """Block an IP address"""
        self.blocked_ips[client_ip] = datetime.now() + timedelta(seconds=duration)
        logger.warning(f"Blocked IP address: {client_ip} for {duration} seconds")

    def is_ip_blocked(self, client_ip: str) -> bool:
        """Check if IP is blocked"""
        if client_ip in self.blocked_ips:
            if datetime.now() < self.blocked_ips[client_ip]:
                return True
            else:
                del self.blocked_ips[client_ip]
        return False


class InputValidator:
    """Input validation and sanitization"""

    def __init__(self):
        self.max_lengths = {
            "username": 50,
            "email": 254,
            "password": 128,
            "building_id": 100,
            "description": 1000,
        }

        self.allowed_patterns = {
            "username": r"^[a-zA-Z0-9_-]{3,50}$",
            "email": r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$",
            "building_id": r"^[a-zA-Z0-9_-]{1,100}$",
        }

    def validate_input(self, field: str, value: str) -> Tuple[bool, str]:
        """Validate input field"""
        import re

        # Check length
        if len(value) > self.max_lengths.get(field, 1000):
            return False, f"Field {field} exceeds maximum length"

        # Check pattern
        if field in self.allowed_patterns:
            if not re.match(self.allowed_patterns[field], value):
                return False, f"Field {field} contains invalid characters"

        # Check for dangerous content
        dangerous_patterns = [
            r"<script",
            r"javascript:",
            r"on\w+\s*=",
            r"union\s+select",
            r"drop\s+table",
            r"exec\s*\(",
        ]

        for pattern in dangerous_patterns:
            if re.search(pattern, value, re.IGNORECASE):
                return False, f"Field {field} contains potentially dangerous content"

        return True, "Valid"

    def sanitize_input(self, value: str) -> str:
        """Sanitize input value"""
        import html

        # HTML escape
        sanitized = html.escape(value)

        # Remove null bytes
        sanitized = sanitized.replace("\x00", "")

        # Normalize whitespace
        sanitized = " ".join(sanitized.split())

        return sanitized


class SecurityHeaders:
    """Security headers management"""

    def __init__(self):
        self.headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Content-Security-Policy": "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
        }

    def get_headers(self) -> Dict[str, str]:
        """Get security headers"""
        return self.headers.copy()

    def add_header(self, name: str, value: str):
        """Add custom security header"""
        self.headers[name] = value

    def remove_header(self, name: str):
        """Remove security header"""
        if name in self.headers:
            del self.headers[name]


# Global security components
security_config = SecurityConfig(
    encryption_key=os.getenv("ENCRYPTION_KEY", secrets.token_urlsafe(32)),
    jwt_secret=os.getenv("JWT_SECRET", secrets.token_urlsafe(32)),
)

encryption_manager = EncryptionManager(security_config.encryption_key)
audit_logger = AuditLogger()
security_monitor = SecurityMonitor()
input_validator = InputValidator()
security_headers = SecurityHeaders()


def require_security_audit(event_type: AuditEventType, resource: str, action: str):
    """Decorator to require security auditing"""

    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Get request from kwargs or args
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break

            if not request:
                for value in kwargs.values():
                    if isinstance(value, Request):
                        request = value
                        break

            if request:
                # Create audit event
                event = AuditEvent(
                    id=f"audit_{int(time.time())}",
                    event_type=event_type,
                    user_id="system",  # Will be updated with actual user
                    resource=resource,
                    action=action,
                    details={"function": func.__name__},
                    ip_address=request.client.host,
                    user_agent=request.headers.get("user-agent", ""),
                )

                # Log the event
                audit_logger.log_event(event)

            return await func(*args, **kwargs)

        return wrapper

    return decorator


def validate_and_sanitize_input(field: str):
    """Decorator to validate and sanitize input"""

    def decorator(func):
        async def wrapper(*args, **kwargs):
            if field in kwargs:
                value = kwargs[field]
                if isinstance(value, str):
                    # Validate
                    is_valid, error_msg = input_validator.validate_input(field, value)
                    if not is_valid:
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Invalid input: {error_msg}",
                        )

                    # Sanitize
                    kwargs[field] = input_validator.sanitize_input(value)

            return await func(*args, **kwargs)

        return wrapper

    return decorator
