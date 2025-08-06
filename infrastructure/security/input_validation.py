"""
Input Validation for MCP Engineering

This module provides comprehensive input validation for the MCP Engineering API,
including data sanitization, type validation, and security hardening.
"""

import re
import json
import html
import logging
from typing import Any, Dict, List, Optional, Union, Type
from dataclasses import dataclass
from datetime import datetime, date
from enum import Enum
import ipaddress
from urllib.parse import urlparse, quote

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Custom validation error."""

    pass


class SecurityLevel(Enum):
    """Security validation levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ValidationRule:
    """Validation rule configuration."""

    field_name: str
    field_type: Type
    required: bool = True
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    pattern: Optional[str] = None
    allowed_values: Optional[List[Any]] = None
    security_level: SecurityLevel = SecurityLevel.MEDIUM
    sanitize: bool = True


class InputValidator:
    """Comprehensive input validation system."""

    def __init__(self):
        """Initialize input validator."""
        # Common patterns
        self.patterns = {
            "email": r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$",
            "phone": r"^\+?1?\d{9,15}$",
            "uuid": r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
            "ip_address": r"^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$",
            "url": r"^https?://(?:[-\w.])+(?:[:\d]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:#(?:[\w.])*)?)?$",
            "postal_code": r"^\d{5}(-\d{4})?$",
            "credit_card": r"^\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}$",
            "ssn": r"^\d{3}-\d{2}-\d{4}$",
        }

        # Dangerous patterns
        self.dangerous_patterns = [
            r"<script[^>]*>.*?</script>",
            r"javascript:",
            r"vbscript:",
            r"on\w+\s*=",
            r"<iframe[^>]*>",
            r"<object[^>]*>",
            r"<embed[^>]*>",
            r"<form[^>]*>",
            r"<input[^>]*>",
            r"<textarea[^>]*>",
            r"<select[^>]*>",
            r"<button[^>]*>",
            r"<link[^>]*>",
            r"<meta[^>]*>",
            r"<style[^>]*>",
            r"<base[^>]*>",
            r"<bgsound[^>]*>",
            r"<marquee[^>]*>",
            r"<applet[^>]*>",
            r"<xmp[^>]*>",
            r"<plaintext[^>]*>",
            r"<listing[^>]*>",
            r"<comment[^>]*>",
            r"<isindex[^>]*>",
            r"<keygen[^>]*>",
            r"<menu[^>]*>",
            r"<nobr[^>]*>",
            r"<noembed[^>]*>",
            r"<noframes[^>]*>",
            r"<noscript[^>]*>",
            r"<wbr[^>]*>",
            r"<xmp[^>]*>",
            r"<plaintext[^>]*>",
            r"<listing[^>]*>",
            r"<comment[^>]*>",
            r"<isindex[^>]*>",
            r"<keygen[^>]*>",
            r"<menu[^>]*>",
            r"<nobr[^>]*>",
            r"<noembed[^>]*>",
            r"<noframes[^>]*>",
            r"<noscript[^>]*>",
            r"<wbr[^>]*>",
        ]

        # SQL injection patterns
        self.sql_injection_patterns = [
            r"(\b(union|select|insert|update|delete|drop|create|alter|exec|execute|declare|cast|convert|truncate|backup|restore)\b)",
            r"(--|#|/\*|\*/)",
            r"(\b(and|or)\b\s+\d+\s*[=<>])",
            r"(\b(and|or)\b\s+['\"])",
            r"(\b(and|or)\b\s+\w+\s*[=<>])",
            r"(\b(and|or)\b\s+\w+\s*like)",
            r"(\b(and|or)\b\s+\w+\s*in)",
            r"(\b(and|or)\b\s+\w+\s*between)",
            r"(\b(and|or)\b\s+\w+\s*exists)",
            r"(\b(and|or)\b\s+\w+\s*not\s+exists)",
            r"(\b(and|or)\b\s+\w+\s*is\s+null)",
            r"(\b(and|or)\b\s+\w+\s*is\s+not\s+null)",
            r"(\b(and|or)\b\s+\w+\s*like\s+['\"])",
            r"(\b(and|or)\b\s+\w+\s*in\s*\()",
            r"(\b(and|or)\b\s+\w+\s*between\s+\w+\s+and)",
            r"(\b(and|or)\b\s+\w+\s*exists\s*\()",
            r"(\b(and|or)\b\s+\w+\s*not\s+exists\s*\()",
            r"(\b(and|or)\b\s+\w+\s*is\s+null)",
            r"(\b(and|or)\b\s+\w+\s*is\s+not\s+null)",
        ]

        # XSS patterns
        self.xss_patterns = [
            r"<script[^>]*>.*?</script>",
            r"javascript:",
            r"vbscript:",
            r"on\w+\s*=",
            r"<iframe[^>]*>",
            r"<object[^>]*>",
            r"<embed[^>]*>",
            r"<form[^>]*>",
            r"<input[^>]*>",
            r"<textarea[^>]*>",
            r"<select[^>]*>",
            r"<button[^>]*>",
            r"<link[^>]*>",
            r"<meta[^>]*>",
            r"<style[^>]*>",
            r"<base[^>]*>",
            r"<bgsound[^>]*>",
            r"<marquee[^>]*>",
            r"<applet[^>]*>",
            r"<xmp[^>]*>",
            r"<plaintext[^>]*>",
            r"<listing[^>]*>",
            r"<comment[^>]*>",
            r"<isindex[^>]*>",
            r"<keygen[^>]*>",
            r"<menu[^>]*>",
            r"<nobr[^>]*>",
            r"<noembed[^>]*>",
            r"<noframes[^>]*>",
            r"<noscript[^>]*>",
            r"<wbr[^>]*>",
        ]

    def sanitize_string(
        self, value: str, security_level: SecurityLevel = SecurityLevel.MEDIUM
    ) -> str:
        """
        Sanitize a string value.

        Args:
            value: String value to sanitize
            security_level: Security level for sanitization

        Returns:
            Sanitized string
        """
        if not isinstance(value, str):
            raise ValidationError(f"Expected string, got {type(value)}")

        # HTML encode
        sanitized = html.escape(value)

        # Remove dangerous patterns based on security level
        if security_level in [SecurityLevel.HIGH, SecurityLevel.CRITICAL]:
            for pattern in self.dangerous_patterns:
                sanitized = re.sub(pattern, "", sanitized, flags=re.IGNORECASE)

        if security_level == SecurityLevel.CRITICAL:
            # Additional critical level sanitization
            sanitized = re.sub(r"[<>\"']", "", sanitized)
            sanitized = re.sub(r"javascript:", "", sanitized, flags=re.IGNORECASE)
            sanitized = re.sub(r"vbscript:", "", sanitized, flags=re.IGNORECASE)

        return sanitized.strip()

    def validate_email(self, email: str) -> str:
        """
        Validate and sanitize email address.

        Args:
            email: Email address to validate

        Returns:
            Validated email address

        Raises:
            ValidationError: If email is invalid
        """
        if not email:
            raise ValidationError("Email is required")

        email = email.strip().lower()

        if not re.match(self.patterns["email"], email):
            raise ValidationError("Invalid email format")

        # Check for dangerous patterns
        if any(
            re.search(pattern, email, re.IGNORECASE)
            for pattern in self.dangerous_patterns
        ):
            raise ValidationError("Email contains dangerous patterns")

        return email

    def validate_phone(self, phone: str) -> str:
        """
        Validate and sanitize phone number.

        Args:
            phone: Phone number to validate

        Returns:
            Validated phone number

        Raises:
            ValidationError: If phone number is invalid
        """
        if not phone:
            raise ValidationError("Phone number is required")

        phone = re.sub(r"[^\d+]", "", phone)

        if not re.match(self.patterns["phone"], phone):
            raise ValidationError("Invalid phone number format")

        return phone

    def validate_url(self, url: str) -> str:
        """
        Validate and sanitize URL.

        Args:
            url: URL to validate

        Returns:
            Validated URL

        Raises:
            ValidationError: If URL is invalid
        """
        if not url:
            raise ValidationError("URL is required")

        url = url.strip()

        try:
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                raise ValidationError("Invalid URL format")

            # Check for dangerous protocols
            if parsed.scheme.lower() in ["javascript", "vbscript", "data"]:
                raise ValidationError("Dangerous URL protocol")

            return url
        except Exception as e:
            raise ValidationError(f"Invalid URL: {e}")

    def validate_ip_address(self, ip: str) -> str:
        """
        Validate IP address.

        Args:
            ip: IP address to validate

        Returns:
            Validated IP address

        Raises:
            ValidationError: If IP address is invalid
        """
        if not ip:
            raise ValidationError("IP address is required")

        try:
            ipaddress.ip_address(ip)
            return ip
        except ValueError:
            raise ValidationError("Invalid IP address format")

    def validate_uuid(self, uuid_str: str) -> str:
        """
        Validate UUID.

        Args:
            uuid_str: UUID string to validate

        Returns:
            Validated UUID

        Raises:
            ValidationError: If UUID is invalid
        """
        if not uuid_str:
            raise ValidationError("UUID is required")

        uuid_str = uuid_str.strip()

        if not re.match(self.patterns["uuid"], uuid_str, re.IGNORECASE):
            raise ValidationError("Invalid UUID format")

        return uuid_str.lower()

    def validate_length(
        self,
        value: str,
        min_length: Optional[int] = None,
        max_length: Optional[int] = None,
    ) -> str:
        """
        Validate string length.

        Args:
            value: String value to validate
            min_length: Minimum length
            max_length: Maximum length

        Returns:
            Validated string

        Raises:
            ValidationError: If length constraints are not met
        """
        if not isinstance(value, str):
            raise ValidationError(f"Expected string, got {type(value)}")

        if min_length is not None and len(value) < min_length:
            raise ValidationError(f"String too short. Minimum length: {min_length}")

        if max_length is not None and len(value) > max_length:
            raise ValidationError(f"String too long. Maximum length: {max_length}")

        return value

    def validate_pattern(
        self, value: str, pattern: str, field_name: str = "field"
    ) -> str:
        """
        Validate string against pattern.

        Args:
            value: String value to validate
            pattern: Regex pattern to match
            field_name: Name of the field for error messages

        Returns:
            Validated string

        Raises:
            ValidationError: If pattern doesn't match
        """
        if not isinstance(value, str):
            raise ValidationError(f"Expected string, got {type(value)}")

        if not re.match(pattern, value):
            raise ValidationError(f"Invalid {field_name} format")

        return value

    def validate_enum(
        self, value: Any, allowed_values: List[Any], field_name: str = "field"
    ) -> Any:
        """
        Validate enum value.

        Args:
            value: Value to validate
            allowed_values: List of allowed values
            field_name: Name of the field for error messages

        Returns:
            Validated value

        Raises:
            ValidationError: If value is not in allowed values
        """
        if value not in allowed_values:
            raise ValidationError(
                f"Invalid {field_name}. Allowed values: {allowed_values}"
            )

        return value

    def validate_type(
        self, value: Any, expected_type: Type, field_name: str = "field"
    ) -> Any:
        """
        Validate value type.

        Args:
            value: Value to validate
            expected_type: Expected type
            field_name: Name of the field for error messages

        Returns:
            Validated value

        Raises:
            ValidationError: If type doesn't match
        """
        if not isinstance(value, expected_type):
            raise ValidationError(
                f"Invalid {field_name} type. Expected {expected_type}, got {type(value)}"
            )

        return value

    def validate_json(self, value: str) -> Dict[str, Any]:
        """
        Validate and parse JSON.

        Args:
            value: JSON string to validate

        Returns:
            Parsed JSON object

        Raises:
            ValidationError: If JSON is invalid
        """
        if not isinstance(value, str):
            raise ValidationError("Expected JSON string")

        try:
            return json.loads(value)
        except json.JSONDecodeError as e:
            raise ValidationError(f"Invalid JSON: {e}")

    def validate_date(self, date_str: str, format: str = "%Y-%m-%d") -> date:
        """
        Validate and parse date.

        Args:
            date_str: Date string to validate
            format: Date format

        Returns:
            Parsed date object

        Raises:
            ValidationError: If date is invalid
        """
        if not isinstance(date_str, str):
            raise ValidationError("Expected date string")

        try:
            return datetime.strptime(date_str, format).date()
        except ValueError as e:
            raise ValidationError(f"Invalid date format: {e}")

    def validate_datetime(
        self, datetime_str: str, format: str = "%Y-%m-%d %H:%M:%S"
    ) -> datetime:
        """
        Validate and parse datetime.

        Args:
            datetime_str: Datetime string to validate
            format: Datetime format

        Returns:
            Parsed datetime object

        Raises:
            ValidationError: If datetime is invalid
        """
        if not isinstance(datetime_str, str):
            raise ValidationError("Expected datetime string")

        try:
            return datetime.strptime(datetime_str, format)
        except ValueError as e:
            raise ValidationError(f"Invalid datetime format: {e}")

    def check_sql_injection(self, value: str) -> bool:
        """
        Check for SQL injection patterns.

        Args:
            value: String to check

        Returns:
            True if SQL injection pattern detected
        """
        value_lower = value.lower()
        for pattern in self.sql_injection_patterns:
            if re.search(pattern, value_lower, re.IGNORECASE):
                return True
        return False

    def check_xss(self, value: str) -> bool:
        """
        Check for XSS patterns.

        Args:
            value: String to check

        Returns:
            True if XSS pattern detected
        """
        value_lower = value.lower()
        for pattern in self.xss_patterns:
            if re.search(pattern, value_lower, re.IGNORECASE):
                return True
        return False

    def validate_object(
        self, data: Dict[str, Any], rules: List[ValidationRule]
    ) -> Dict[str, Any]:
        """
        Validate object against rules.

        Args:
            data: Data to validate
            rules: List of validation rules

        Returns:
            Validated data

        Raises:
            ValidationError: If validation fails
        """
        if not isinstance(data, dict):
            raise ValidationError("Expected dictionary")

        validated_data = {}

        for rule in rules:
            value = data.get(rule.field_name)

            # Check if required
            if rule.required and value is None:
                raise ValidationError(f"Field '{rule.field_name}' is required")

            if value is not None:
                # Type validation
                value = self.validate_type(value, rule.field_type, rule.field_name)

                # String-specific validations
                if isinstance(value, str):
                    # Length validation
                    if rule.min_length is not None or rule.max_length is not None:
                        value = self.validate_length(
                            value, rule.min_length, rule.max_length
                        )

                    # Pattern validation
                    if rule.pattern is not None:
                        value = self.validate_pattern(
                            value, rule.pattern, rule.field_name
                        )

                    # Security checks
                    if rule.security_level in [
                        SecurityLevel.HIGH,
                        SecurityLevel.CRITICAL,
                    ]:
                        if self.check_sql_injection(value):
                            raise ValidationError(
                                f"SQL injection detected in field '{rule.field_name}'"
                            )
                        if self.check_xss(value):
                            raise ValidationError(
                                f"XSS detected in field '{rule.field_name}'"
                            )

                    # Sanitization
                    if rule.sanitize:
                        value = self.sanitize_string(value, rule.security_level)

                # Allowed values validation
                if rule.allowed_values is not None:
                    value = self.validate_enum(
                        value, rule.allowed_values, rule.field_name
                    )

                validated_data[rule.field_name] = value

        return validated_data


# Global validator instance
validator = InputValidator()
