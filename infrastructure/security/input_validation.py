"""
Input Validation and Sanitization Security Layer.

Provides comprehensive input validation, sanitization, and security checks
to prevent injection attacks and data corruption.
"""

import re
import html
import json
import ipaddress
from typing import Any, Dict, List, Optional, Union, Tuple, Callable
from dataclasses import dataclass
from enum import Enum
from urllib.parse import urlparse, quote, unquote
import bleach
from email_validator import validate_email, EmailNotValidError

from infrastructure.logging.structured_logging import get_logger, security_logger
from infrastructure.error_handling import ValidationError


logger = get_logger(__name__)


class ValidationSeverity(Enum):
    """Validation severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ValidationRule:
    """Validation rule definition."""
    name: str
    description: str
    pattern: Optional[str] = None
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    allowed_chars: Optional[str] = None
    forbidden_chars: Optional[str] = None
    custom_validator: Optional[Callable] = None
    severity: ValidationSeverity = ValidationSeverity.MEDIUM
    
    def validate(self, value: str) -> Tuple[bool, List[str]]:
        """Validate value against this rule."""
        errors = []
        
        if not isinstance(value, str):
            value = str(value)
        
        # Length checks
        if self.min_length is not None and len(value) < self.min_length:
            errors.append(f"Minimum length is {self.min_length} characters")
        
        if self.max_length is not None and len(value) > self.max_length:
            errors.append(f"Maximum length is {self.max_length} characters")
        
        # Pattern check
        if self.pattern and not re.match(self.pattern, value):
            errors.append(f"Does not match required pattern: {self.description}")
        
        # Character restrictions
        if self.allowed_chars:
            allowed_set = set(self.allowed_chars)
            if not all(char in allowed_set for char in value):
                errors.append(f"Contains invalid characters. Allowed: {self.allowed_chars}")
        
        if self.forbidden_chars:
            forbidden_set = set(self.forbidden_chars)
            if any(char in forbidden_set for char in value):
                errors.append(f"Contains forbidden characters: {self.forbidden_chars}")
        
        # Custom validation
        if self.custom_validator:
            try:
                custom_valid = self.custom_validator(value)
                if not custom_valid:
                    errors.append(f"Failed custom validation: {self.description}")
            except Exception as e:
                errors.append(f"Custom validation error: {str(e)}")
        
        return len(errors) == 0, errors


class SecurityPatterns:
    """Security-focused validation patterns."""
    
    # SQL Injection patterns
    SQL_INJECTION_PATTERNS = [
        r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|EXECUTE)\b)",
        r"(--|#|/\*|\*/)",
        r"(\bunion\b.*\bselect\b)",
        r"(\bor\b.*=.*\bor\b)",
        r"(;.*\b(SELECT|INSERT|UPDATE|DELETE)\b)",
        r"(\bxp_cmdshell\b|\bsp_executesql\b)"
    ]
    
    # XSS patterns
    XSS_PATTERNS = [
        r"<script[^>]*>.*?</script>",
        r"javascript:",
        r"on\w+\s*=",
        r"<iframe[^>]*>.*?</iframe>",
        r"<object[^>]*>.*?</object>",
        r"<embed[^>]*>",
        r"<applet[^>]*>.*?</applet>"
    ]
    
    # Command injection patterns
    COMMAND_INJECTION_PATTERNS = [
        r"[;&|`$(){}[\]<>]",
        r"(cat|ls|dir|type|more|less|head|tail|grep|find|locate)\b",
        r"(wget|curl|nc|netcat|telnet|ssh)\b",
        r"(rm|del|rmdir|rd|format|fdisk)\b"
    ]
    
    # Path traversal patterns
    PATH_TRAVERSAL_PATTERNS = [
        r"\.\./",
        r"\.\.\\",
        r"/%2e%2e/",
        r"\\%2e%2e\\",
        r"/etc/passwd",
        r"\\windows\\system32"
    ]


class InputSanitizer:
    """Input sanitization utilities."""
    
    @staticmethod
    def sanitize_html(input_text: str, allowed_tags: Optional[List[str]] = None) -> str:
        """Sanitize HTML input to prevent XSS."""
        if allowed_tags is None:
            allowed_tags = ['b', 'i', 'u', 'em', 'strong', 'p', 'br']
        
        allowed_attributes = {}
        
        # Use bleach library for safe HTML sanitization
        sanitized = bleach.clean(
            input_text,
            tags=allowed_tags,
            attributes=allowed_attributes,
            strip=True
        )
        
        security_logger.log_security_event(
            event_type="html_sanitized",
            details={
                "original_length": len(input_text),
                "sanitized_length": len(sanitized),
                "allowed_tags": allowed_tags
            }
        )
        
        return sanitized
    
    @staticmethod
    def escape_sql(input_text: str) -> str:
        """Escape SQL special characters."""
        # Replace single quotes with double quotes
        escaped = input_text.replace("'", "''")
        
        # Remove or escape other dangerous characters
        dangerous_chars = {';': '', '--': '', '/*': '', '*/': '', 'xp_': 'xp[_]'}
        
        for char, replacement in dangerous_chars.items():
            escaped = escaped.replace(char, replacement)
        
        return escaped
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Sanitize filename to prevent path traversal."""
        # Remove path components
        filename = filename.split('/')[-1].split('\\')[-1]
        
        # Remove dangerous characters
        dangerous_chars = '<>:"|?*'
        for char in dangerous_chars:
            filename = filename.replace(char, '')
        
        # Limit length
        if len(filename) > 255:
            name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
            filename = name[:255-len(ext)-1] + '.' + ext if ext else name[:255]
        
        # Prevent reserved names (Windows)
        reserved_names = ['CON', 'PRN', 'AUX', 'NUL', 'COM1', 'COM2', 'COM3', 'COM4',
                         'COM5', 'COM6', 'COM7', 'COM8', 'COM9', 'LPT1', 'LPT2', 'LPT3',
                         'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9']
        
        if filename.upper() in reserved_names:
            filename = f"file_{filename}"
        
        return filename
    
    @staticmethod
    def sanitize_url(url: str) -> str:
        """Sanitize URL input."""
        try:
            parsed = urlparse(url)
            
            # Only allow specific schemes
            allowed_schemes = ['http', 'https', 'ftp', 'ftps']
            if parsed.scheme.lower() not in allowed_schemes:
                raise ValidationError(f"URL scheme '{parsed.scheme}' not allowed")
            
            # Prevent localhost/internal addresses in production
            if parsed.hostname in ['localhost', '127.0.0.1', '::1']:
                security_logger.log_security_event(
                    event_type="suspicious_url_detected",
                    details={"url": url, "reason": "localhost_access"}
                )
            
            # Reconstruct URL to normalize it
            sanitized_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
            if parsed.query:
                sanitized_url += f"?{quote(parsed.query, safe='=&')}"
            
            return sanitized_url
            
        except Exception as e:
            raise ValidationError(f"Invalid URL format: {str(e)}")


class InputValidator:
    """Comprehensive input validation system."""
    
    def __init__(self):
        self.rules = self._initialize_default_rules()
        self.sanitizer = InputSanitizer()
        self.security_patterns = SecurityPatterns()
    
    def _initialize_default_rules(self) -> Dict[str, ValidationRule]:
        """Initialize default validation rules."""
        return {
            "username": ValidationRule(
                name="username",
                description="Username (alphanumeric and underscore only)",
                pattern=r"^[a-zA-Z0-9_]{3,30}$",
                min_length=3,
                max_length=30,
                forbidden_chars="<>\"';&|`$(){}[]",
                severity=ValidationSeverity.HIGH
            ),
            "email": ValidationRule(
                name="email",
                description="Valid email address",
                max_length=254,
                custom_validator=self._validate_email,
                severity=ValidationSeverity.HIGH
            ),
            "password": ValidationRule(
                name="password",
                description="Secure password",
                min_length=8,
                max_length=128,
                custom_validator=self._validate_password_strength,
                severity=ValidationSeverity.CRITICAL
            ),
            "building_name": ValidationRule(
                name="building_name",
                description="Building name",
                pattern=r"^[a-zA-Z0-9\s\-_.()]{1,100}$",
                min_length=1,
                max_length=100,
                forbidden_chars="<>\"';&|`${}[]",
                severity=ValidationSeverity.MEDIUM
            ),
            "address": ValidationRule(
                name="address",
                description="Street address",
                pattern=r"^[a-zA-Z0-9\s\-.,#/()]{1,200}$",
                min_length=1,
                max_length=200,
                forbidden_chars="<>\"';|`${}[]",
                severity=ValidationSeverity.MEDIUM
            ),
            "phone_number": ValidationRule(
                name="phone_number",
                description="Phone number",
                pattern=r"^[\+]?[1-9][\d\-\(\)\s]{7,15}$",
                max_length=20,
                allowed_chars="0123456789+-() ",
                severity=ValidationSeverity.LOW
            ),
            "device_id": ValidationRule(
                name="device_id",
                description="Device identifier",
                pattern=r"^[A-Z0-9_]{3,50}$",
                min_length=3,
                max_length=50,
                allowed_chars="ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_",
                severity=ValidationSeverity.HIGH
            )
        }
    
    def validate_field(self, field_name: str, value: Any, 
                      custom_rule: Optional[ValidationRule] = None) -> Tuple[bool, List[str]]:
        """Validate a single field."""
        if value is None:
            return True, []  # Allow None values (handle required validation separately)
        
        # Convert to string for validation
        str_value = str(value).strip()
        
        # Use custom rule or lookup default rule
        rule = custom_rule or self.rules.get(field_name)
        
        if not rule:
            # No specific rule, perform basic security checks
            return self._basic_security_validation(str_value)
        
        # Apply rule validation
        is_valid, errors = rule.validate(str_value)
        
        # Additional security checks
        security_valid, security_errors = self._security_validation(str_value, rule.severity)
        
        all_errors = errors + security_errors
        return len(all_errors) == 0, all_errors
    
    def validate_object(self, data: Dict[str, Any], 
                       field_rules: Optional[Dict[str, ValidationRule]] = None) -> Dict[str, List[str]]:
        """Validate multiple fields in an object."""
        validation_errors = {}
        
        for field_name, value in data.items():
            custom_rule = field_rules.get(field_name) if field_rules else None
            is_valid, errors = self.validate_field(field_name, value, custom_rule)
            
            if not is_valid:
                validation_errors[field_name] = errors
        
        return validation_errors
    
    def _basic_security_validation(self, value: str) -> Tuple[bool, List[str]]:
        """Basic security validation for unknown fields."""
        errors = []
        
        # Check for basic injection patterns
        if self._contains_sql_injection(value):
            errors.append("Potentially malicious SQL patterns detected")
        
        if self._contains_xss(value):
            errors.append("Potentially malicious script content detected")
        
        if self._contains_command_injection(value):
            errors.append("Potentially malicious command patterns detected")
        
        if len(value) > 10000:  # Prevent DoS through large inputs
            errors.append("Input too long (max 10000 characters)")
        
        return len(errors) == 0, errors
    
    def _security_validation(self, value: str, severity: ValidationSeverity) -> Tuple[bool, List[str]]:
        """Advanced security validation based on severity."""
        errors = []
        
        # High and critical severity fields get extra security checks
        if severity in [ValidationSeverity.HIGH, ValidationSeverity.CRITICAL]:
            # Check for injection attacks
            if self._contains_sql_injection(value):
                errors.append("SQL injection patterns detected")
                security_logger.log_security_event(
                    event_type="sql_injection_attempt",
                    details={"input_length": len(value), "severity": severity.value}
                )
            
            if self._contains_xss(value):
                errors.append("XSS patterns detected")
                security_logger.log_security_event(
                    event_type="xss_attempt",
                    details={"input_length": len(value), "severity": severity.value}
                )
            
            if self._contains_command_injection(value):
                errors.append("Command injection patterns detected")
                security_logger.log_security_event(
                    event_type="command_injection_attempt",
                    details={"input_length": len(value), "severity": severity.value}
                )
            
            if self._contains_path_traversal(value):
                errors.append("Path traversal patterns detected")
                security_logger.log_security_event(
                    event_type="path_traversal_attempt",
                    details={"input_length": len(value), "severity": severity.value}
                )
        
        return len(errors) == 0, errors
    
    def _contains_sql_injection(self, value: str) -> bool:
        """Check for SQL injection patterns."""
        value_lower = value.lower()
        for pattern in self.security_patterns.SQL_INJECTION_PATTERNS:
            if re.search(pattern, value_lower, re.IGNORECASE):
                return True
        return False
    
    def _contains_xss(self, value: str) -> bool:
        """Check for XSS patterns."""
        for pattern in self.security_patterns.XSS_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE):
                return True
        return False
    
    def _contains_command_injection(self, value: str) -> bool:
        """Check for command injection patterns."""
        for pattern in self.security_patterns.COMMAND_INJECTION_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE):
                return True
        return False
    
    def _contains_path_traversal(self, value: str) -> bool:
        """Check for path traversal patterns."""
        for pattern in self.security_patterns.PATH_TRAVERSAL_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE):
                return True
        return False
    
    def _validate_email(self, email: str) -> bool:
        """Validate email address."""
        try:
            # Use email-validator library for comprehensive validation
            validation = validate_email(email)
            return validation.email is not None
        except EmailNotValidError:
            return False
    
    def _validate_password_strength(self, password: str) -> bool:
        """Validate password strength."""
        if len(password) < 8:
            return False
        
        # Check for character diversity
        has_lower = any(c.islower() for c in password)
        has_upper = any(c.isupper() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_special = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password)
        
        return sum([has_lower, has_upper, has_digit, has_special]) >= 3
    
    def sanitize_input(self, value: str, input_type: str = "text") -> str:
        """Sanitize input based on type."""
        if input_type == "html":
            return self.sanitizer.sanitize_html(value)
        elif input_type == "sql":
            return self.sanitizer.escape_sql(value)
        elif input_type == "filename":
            return self.sanitizer.sanitize_filename(value)
        elif input_type == "url":
            return self.sanitizer.sanitize_url(value)
        else:
            # Default text sanitization
            return html.escape(value)
    
    def add_custom_rule(self, name: str, rule: ValidationRule) -> None:
        """Add custom validation rule."""
        self.rules[name] = rule
        logger.info(f"Added custom validation rule: {name}")


class SecurityValidationMiddleware:
    """Middleware for automatic input validation and sanitization."""
    
    def __init__(self, validator: InputValidator):
        self.validator = validator
        self.auto_sanitize = True
        self.strict_mode = True
    
    def validate_request_data(self, data: Dict[str, Any], 
                            required_fields: List[str] = None,
                            field_rules: Dict[str, ValidationRule] = None) -> Dict[str, Any]:
        """Validate and sanitize request data."""
        validated_data = {}
        validation_errors = {}
        
        # Check required fields
        if required_fields:
            missing_fields = [field for field in required_fields if field not in data]
            if missing_fields:
                validation_errors["_required"] = f"Missing required fields: {', '.join(missing_fields)}"
        
        # Validate each field
        field_errors = self.validator.validate_object(data, field_rules)
        validation_errors.update(field_errors)
        
        # If validation passed, sanitize data
        if not validation_errors:
            for field_name, value in data.items():
                if isinstance(value, str):
                    # Determine sanitization type based on field name
                    sanitize_type = self._get_sanitization_type(field_name)
                    validated_data[field_name] = self.validator.sanitize_input(value, sanitize_type)
                else:
                    validated_data[field_name] = value
        
        if validation_errors:
            security_logger.log_security_event(
                event_type="input_validation_failed",
                details={
                    "validation_errors": validation_errors,
                    "field_count": len(data),
                    "strict_mode": self.strict_mode
                }
            )
            
            if self.strict_mode:
                raise ValidationError("Input validation failed", validation_errors)
        
        return validated_data
    
    def _get_sanitization_type(self, field_name: str) -> str:
        """Determine sanitization type based on field name."""
        if "html" in field_name.lower() or "content" in field_name.lower():
            return "html"
        elif "filename" in field_name.lower() or "file" in field_name.lower():
            return "filename"
        elif "url" in field_name.lower() or "link" in field_name.lower():
            return "url"
        else:
            return "text"


# Pre-configured validator instance
input_validator = InputValidator()
validation_middleware = SecurityValidationMiddleware(input_validator)