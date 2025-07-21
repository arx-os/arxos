"""
Input Validation and Security Validation Services for Arxos.

This module provides comprehensive input validation and security validation
to prevent OWASP Top 10 vulnerabilities and ensure data integrity.
"""

import re
import html
import json
import urllib.parse
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from enum import Enum
import sqlite3
from pathlib import Path


class ValidationError(Exception):
    """Exception raised for validation errors."""
    pass


class SecurityError(Exception):
    """Exception raised for security violations."""
    pass


class InputType(Enum):
    """Types of input validation."""
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    EMAIL = "email"
    URL = "url"
    IP_ADDRESS = "ip_address"
    JSON = "json"
    SQL = "sql"
    HTML = "html"
    FILE_PATH = "file_path"


@dataclass
class ValidationRule:
    """Validation rule configuration."""
    field_name: str
    input_type: InputType
    required: bool = True
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    pattern: Optional[str] = None
    allowed_values: Optional[List[Any]] = None
    custom_validator: Optional[callable] = None


class InputValidator:
    """Comprehensive input validation service."""
    
    def __init__(self):
        self.validation_patterns = {
            'email': r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
            'url': r'^https?://[^\s/$.?#].[^\s]*$',
            'ip_address': r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$',
            'strong_password': r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$'
        }
        
        self.sanitization_patterns = {
            'html': re.compile(r'<[^>]*>'),
            'sql_injection': re.compile(r'(\b(union|select|insert|update|delete|drop|create|alter)\b)', re.IGNORECASE),
            'xss': re.compile(r'<script[^>]*>.*?</script>', re.IGNORECASE),
            'path_traversal': re.compile(r'\.\./|\.\.\\'),
        }
    
    def validate_input(self, data: Any, rule: ValidationRule) -> Any:
        """Validate input according to rule."""
        # Check if required
        if rule.required and (data is None or data == ""):
            raise ValidationError(f"Field '{rule.field_name}' is required")
        
        # Type validation
        validated_data = self._validate_type(data, rule.input_type)
        
        # Length validation
        if rule.min_length is not None and len(str(validated_data)) < rule.min_length:
            raise ValidationError(f"Field '{rule.field_name}' must be at least {rule.min_length} characters")
        
        if rule.max_length is not None and len(str(validated_data)) > rule.max_length:
            raise ValidationError(f"Field '{rule.field_name}' must be no more than {rule.max_length} characters")
        
        # Pattern validation
        if rule.pattern and not re.match(rule.pattern, str(validated_data)):
            raise ValidationError(f"Field '{rule.field_name}' does not match required pattern")
        
        # Allowed values validation
        if rule.allowed_values and validated_data not in rule.allowed_values:
            raise ValidationError(f"Field '{rule.field_name}' must be one of: {rule.allowed_values}")
        
        # Custom validation
        if rule.custom_validator:
            try:
                validated_data = rule.custom_validator(validated_data)
            except Exception as e:
                raise ValidationError(f"Custom validation failed for '{rule.field_name}': {str(e)}")
        
        return validated_data
    
    def _validate_type(self, data: Any, input_type: InputType) -> Any:
        """Validate and convert data type."""
        if data is None:
            return None
        
        try:
            if input_type == InputType.STRING:
                return str(data)
            elif input_type == InputType.INTEGER:
                return int(data)
            elif input_type == InputType.FLOAT:
                return float(data)
            elif input_type == InputType.BOOLEAN:
                if isinstance(data, bool):
                    return data
                elif isinstance(data, str):
                    return data.lower() in ('true', '1', 'yes', 'on')
                else:
                    return bool(data)
            elif input_type == InputType.EMAIL:
                email = str(data)
                if not re.match(self.validation_patterns['email'], email):
                    raise ValidationError("Invalid email format")
                return email
            elif input_type == InputType.URL:
                url = str(data)
                if not re.match(self.validation_patterns['url'], url):
                    raise ValidationError("Invalid URL format")
                return url
            elif input_type == InputType.IP_ADDRESS:
                ip = str(data)
                if not re.match(self.validation_patterns['ip_address'], ip):
                    raise ValidationError("Invalid IP address format")
                return ip
            elif input_type == InputType.JSON:
                if isinstance(data, str):
                    return json.loads(data)
                elif isinstance(data, dict):
                    return data
                else:
                    raise ValidationError("Invalid JSON format")
            elif input_type == InputType.SQL:
                # Basic SQL injection prevention
                sql = str(data)
                if self.sanitization_patterns['sql_injection'].search(sql):
                    raise SecurityError("Potential SQL injection detected")
                return sql
            elif input_type == InputType.HTML:
                # Basic HTML sanitization
                html_content = str(data)
                if self.sanitization_patterns['xss'].search(html_content):
                    raise SecurityError("Potential XSS attack detected")
                return html.escape(html_content)
            elif input_type == InputType.FILE_PATH:
                path = str(data)
                if self.sanitization_patterns['path_traversal'].search(path):
                    raise SecurityError("Path traversal attack detected")
                return Path(path).resolve()
            else:
                return data
        except (ValueError, TypeError) as e:
            raise ValidationError(f"Invalid data type for {input_type.value}: {str(e)}")
    
    def sanitize_input(self, data: str, sanitization_type: str = "html") -> str:
        """Sanitize input to prevent security vulnerabilities."""
        if sanitization_type == "html":
            return html.escape(data)
        elif sanitization_type == "sql":
            # Basic SQL sanitization
            return data.replace("'", "''").replace(";", "")
        elif sanitization_type == "url":
            return urllib.parse.quote(data)
        elif sanitization_type == "filename":
            # Remove dangerous characters from filenames
            return re.sub(r'[<>:"/\\|?*]', '', data)
        else:
            return data
    
    def validate_json_schema(self, data: Dict[str, Any], schema: Dict[str, Any]) -> bool:
        """Validate JSON data against schema."""
        try:
            # Basic JSON schema validation
            for field, rules in schema.items():
                if field not in data and rules.get('required', False):
                    raise ValidationError(f"Required field '{field}' is missing")
                
                if field in data:
                    value = data[field]
                    if 'type' in rules:
                        if rules['type'] == 'string' and not isinstance(value, str):
                            raise ValidationError(f"Field '{field}' must be a string")
                        elif rules['type'] == 'integer' and not isinstance(value, int):
                            raise ValidationError(f"Field '{field}' must be an integer")
                        elif rules['type'] == 'number' and not isinstance(value, (int, float)):
                            raise ValidationError(f"Field '{field}' must be a number")
                    
                    if 'min_length' in rules and len(str(value)) < rules['min_length']:
                        raise ValidationError(f"Field '{field}' is too short")
                    
                    if 'max_length' in rules and len(str(value)) > rules['max_length']:
                        raise ValidationError(f"Field '{field}' is too long")
                    
                    if 'pattern' in rules and not re.match(rules['pattern'], str(value)):
                        raise ValidationError(f"Field '{field}' does not match pattern")
            
            return True
        except Exception as e:
            raise ValidationError(f"JSON schema validation failed: {str(e)}")


class SecurityValidator:
    """Enhanced security validation service for comprehensive OWASP Top 10 threat detection."""
    
    def __init__(self):
        self.threat_patterns = {
            # OWASP Top 10 2021 - A01:2021 Broken Access Control
            'broken_access_control': [
                r'(\b(admin|root|superuser)\b)',
                r'(\b(bypass|override|skip)\b)',
                r'(\b(unauthorized|unrestricted)\b)',
                r'(\b(privilege|escalation)\b)',
            ],
            
            # OWASP Top 10 2021 - A02:2021 Cryptographic Failures
            'cryptographic_failures': [
                r'(\b(md5|sha1|des|rc4)\b)',
                r'(\b(weak|insecure|broken)\b.*\b(crypto|encryption|hash)\b)',
                r'(\b(plaintext|cleartext)\b)',
                r'(\b(base64|hex)\b.*\b(password|secret|key)\b)',
            ],
            
            # OWASP Top 10 2021 - A03:2021 Injection
            'sql_injection': [
                r'(\b(union|select|insert|update|delete|drop|create|alter)\b)',
                r'(\b(exec|execute|xp_|sp_)\b)',
                r'(\b(script|javascript|vbscript)\b)',
                r'(\b(1=1|1\'=1\'|1"=1")\b)',
                r'(\b(or|and)\b.*\b(1=1|true|false)\b)',
                r'(\b(union|select)\b.*\b(from|where)\b)',
            ],
            'nosql_injection': [
                r'(\b(\$where|\$ne|\$gt|\$lt|\$regex)\b)',
                r'(\b(\$or|\$and|\$not)\b)',
                r'(\b(\$exists|\$type|\$in)\b)',
                r'(\b(\$text|\$search)\b)',
            ],
            'command_injection': [
                r'(\b(cmd|command|exec|system|eval)\b)',
                r'(\b(ping|nslookup|traceroute|netstat)\b)',
                r'(\b(cat|ls|dir|type|more)\b)',
                r'(\b(rm|del|erase|format)\b)',
                r'(\b(&&|\|\||;)\b)',
                r'(\b(\$\(|`)\b)',
            ],
            'ldap_injection': [
                r'(\b(uid|cn|ou|dc)\b)',
                r'(\b(and|or|not)\b)',
                r'(\b(|&)\b)',
                r'(\b(\*|\(|\))\b)',
                r'(\b(ldap|bind)\b)',
            ],
            
            # OWASP Top 10 2021 - A04:2021 Insecure Design
            'insecure_design': [
                r'(\b(trust|assume|believe)\b)',
                r'(\b(bypass|circumvent|override)\b)',
                r'(\b(weak|insecure|vulnerable)\b.*\b(design|architecture)\b)',
                r'(\b(no|missing)\b.*\b(validation|check)\b)',
            ],
            
            # OWASP Top 10 2021 - A05:2021 Security Misconfiguration
            'security_misconfiguration': [
                r'(\b(default|admin|root|password)\b)',
                r'(\b(debug|test|dev|development)\b)',
                r'(\b(verbose|detailed|trace)\b)',
                r'(\b(allow|permit|enable)\b.*\b(all|any|every)\b)',
                r'(\b(open|public)\b.*\b(access|permission)\b)',
            ],
            
            # OWASP Top 10 2021 - A06:2021 Vulnerable Components
            'vulnerable_components': [
                r'(\b(outdated|deprecated|unsupported)\b)',
                r'(\b(vulnerable|exploitable|weak)\b.*\b(version|component|library)\b)',
                r'(\b(known|public|disclosed)\b.*\b(vulnerability|exploit|cve)\b)',
                r'(\b(version|release)\b.*\b(old|ancient|legacy)\b)',
            ],
            
            # OWASP Top 10 2021 - A07:2021 Authentication Failures
            'authentication_failures': [
                r'(\b(weak|simple|common)\b.*\b(password|passwd|pwd)\b)',
                r'(\b(no|missing|disabled)\b.*\b(auth|authentication|login)\b)',
                r'(\b(plaintext|cleartext)\b.*\b(password|credential|secret)\b)',
                r'(\b(session|token)\b.*\b(expired|invalid|stolen)\b)',
                r'(\b(no|missing)\b.*\b(mfa|2fa|totp)\b)',
            ],
            
            # OWASP Top 10 2021 - A08:2021 Software and Data Integrity
            'integrity_failures': [
                r'(\b(tamper|modify|alter)\b)',
                r'(\b(unverified|unsigned|untrusted)\b)',
                r'(\b(integrity|checksum|hash)\b.*\b(fail|error|invalid)\b)',
                r'(\b(supply|chain)\b.*\b(attack|compromise)\b)',
                r'(\b(no|missing)\b.*\b(signature|verification)\b)',
            ],
            
            # OWASP Top 10 2021 - A09:2021 Security Logging Failures
            'logging_failures': [
                r'(\b(no|missing|disabled)\b.*\b(log|logging|audit)\b)',
                r'(\b(log|audit)\b.*\b(fail|error|exception)\b)',
                r'(\b(sensitive|confidential)\b.*\b(log|logfile)\b)',
                r'(\b(log|audit)\b.*\b(clear|delete|remove)\b)',
                r'(\b(no|missing)\b.*\b(monitoring|alerting)\b)',
            ],
            
            # OWASP Top 10 2021 - A10:2021 Server-Side Request Forgery
            'ssrf': [
                r'https?://[^\s]*',
                r'ftp://[^\s]*',
                r'file://[^\s]*',
                r'gopher://[^\s]*',
                r'ldap://[^\s]*',
                r'(\b(url|uri)\b.*\b(fetch|request|get|post)\b)',
                r'(\b(proxy|forward|redirect)\b)',
                r'(\b(127\.0\.0\.1|localhost|0\.0\.0\.0)\b)',
            ],
            
            # Additional security patterns
            'xss': [
                r'<script[^>]*>.*?</script>',
                r'javascript:',
                r'vbscript:',
                r'on\w+\s*=',
                r'<iframe[^>]*>',
                r'<object[^>]*>',
                r'<embed[^>]*>',
                r'(\b(alert|confirm|prompt)\b)',
                r'(\b(document|window|location)\b)',
                r'(\b(eval|setTimeout|setInterval)\b)',
            ],
            'path_traversal': [
                r'\.\./',
                r'\.\.\\',
                r'%2e%2e%2f',
                r'%2e%2e%5c',
                r'\.\.%2f',
                r'\.\.%5c',
                r'(\b(..|%2e%2e)\b)',
                r'(\b(\.\.|%2e%2e)\b)',
            ],
            'xml_injection': [
                r'<!\[CDATA\[',
                r'<!DOCTYPE',
                r'<!ENTITY',
                r'<\!\[CDATA\[',
                r'(\b(xml|xslt)\b.*\b(injection|attack)\b)',
            ],
            'xxe': [
                r'<!ENTITY',
                r'<!DOCTYPE',
                r'(\b(xml|external)\b.*\b(entity|reference)\b)',
                r'(\b(<!ENTITY|<!DOCTYPE)\b)',
            ],
            'deserialization': [
                r'(\b(pickle|yaml|json)\b.*\b(load|loads|deserialize)\b)',
                r'(\b(serialize|deserialize)\b)',
                r'(\b(marshal|unmarshal)\b)',
                r'(\b(php|java)\b.*\b(unserialize)\b)',
            ],
            'template_injection': [
                r'(\b(template|jinja|django|flask)\b.*\b(render|template)\b)',
                r'(\b(\{\{|\}\})\b)',
                r'(\b(\{%|%\})\b)',
            ],
        }
        
        self.compiled_patterns = {}
        for threat_type, patterns in self.threat_patterns.items():
            self.compiled_patterns[threat_type] = [
                re.compile(pattern, re.IGNORECASE) for pattern in patterns
            ]
        
        # OWASP Top 10 severity mapping
        self.severity_levels = {
            'critical': [
                'sql_injection', 'command_injection', 'xss', 'broken_access_control',
                'cryptographic_failures', 'integrity_failures', 'xxe'
            ],
            'high': [
                'path_traversal', 'ldap_injection', 'xml_injection', 'ssrf',
                'authentication_failures', 'deserialization', 'template_injection',
                'nosql_injection'
            ],
            'medium': [
                'security_misconfiguration', 'vulnerable_components',
                'logging_failures', 'insecure_design'
            ],
            'low': []
        }
    
    def detect_threats(self, data: str) -> List[Dict[str, Any]]:
        """Detect security threats in input data."""
        threats = []
        
        for threat_type, patterns in self.compiled_patterns.items():
            for pattern in patterns:
                matches = pattern.findall(data)
                if matches:
                    threats.append({
                        'type': threat_type,
                        'pattern': pattern.pattern,
                        'matches': matches,
                        'severity': self._get_threat_severity(threat_type)
                    })
        
        return threats
    
    def _get_threat_severity(self, threat_type: str) -> str:
        """Get severity level for threat type."""
        severity_map = {
            'sql_injection': 'critical',
            'xss': 'high',
            'path_traversal': 'high',
            'command_injection': 'critical',
            'ldap_injection': 'high'
        }
        return severity_map.get(threat_type, 'medium')
    
    def validate_file_upload(self, file_path: str, allowed_extensions: List[str], max_size: int) -> bool:
        """Validate file upload for security."""
        try:
            # Check file extension
            file_ext = Path(file_path).suffix.lower()
            if file_ext not in allowed_extensions:
                raise SecurityError(f"File extension '{file_ext}' is not allowed")
            
            # Check file size
            file_size = Path(file_path).stat().st_size
            if file_size > max_size:
                raise SecurityError(f"File size {file_size} exceeds maximum allowed size {max_size}")
            
            # Check for executable content
            with open(file_path, 'rb') as f:
                content = f.read(1024)  # Read first 1KB
                if b'\x7fELF' in content or b'MZ' in content:
                    raise SecurityError("Executable file detected")
            
            return True
        except Exception as e:
            raise SecurityError(f"File validation failed: {str(e)}")
    
    def validate_url(self, url: str, allowed_domains: List[str] = None) -> bool:
        """Validate URL for security."""
        try:
            parsed_url = urllib.parse.urlparse(url)
            
            # Check protocol
            if parsed_url.scheme not in ['http', 'https']:
                raise SecurityError("Only HTTP and HTTPS protocols are allowed")
            
            # Check domain if specified
            if allowed_domains and parsed_url.netloc not in allowed_domains:
                raise SecurityError(f"Domain '{parsed_url.netloc}' is not allowed")
            
            # Check for suspicious patterns
            suspicious_patterns = [
                r'javascript:',
                r'data:',
                r'file:',
                r'vbscript:'
            ]
            
            for pattern in suspicious_patterns:
                if re.search(pattern, url, re.IGNORECASE):
                    raise SecurityError(f"Suspicious URL pattern detected: {pattern}")
            
            return True
        except Exception as e:
            raise SecurityError(f"URL validation failed: {str(e)}")
    
    def validate_json_payload(self, json_data: Dict[str, Any], max_depth: int = 10) -> bool:
        """Validate JSON payload for security."""
        try:
            # Check for circular references
            def check_depth(obj, depth=0):
                if depth > max_depth:
                    raise SecurityError("JSON payload too deep")
                
                if isinstance(obj, dict):
                    for value in obj.values():
                        check_depth(value, depth + 1)
                elif isinstance(obj, list):
                    for item in obj:
                        check_depth(item, depth + 1)
            
            check_depth(json_data)
            
            # Check for suspicious keys
            suspicious_keys = ['__proto__', 'constructor', 'prototype']
            def check_keys(obj):
                if isinstance(obj, dict):
                    for key in obj.keys():
                        if key in suspicious_keys:
                            raise SecurityError(f"Suspicious key detected: {key}")
                        check_keys(obj[key])
                elif isinstance(obj, list):
                    for item in obj:
                        check_keys(item)
            
            check_keys(json_data)
            
            return True
        except Exception as e:
            raise SecurityError(f"JSON payload validation failed: {str(e)}")


class ContentSecurityPolicy:
    """Content Security Policy implementation."""
    
    def __init__(self):
        self.default_policy = {
            'default-src': ["'self'"],
            'script-src': ["'self'", "'unsafe-inline'"],
            'style-src': ["'self'", "'unsafe-inline'"],
            'img-src': ["'self'", "data:", "https:"],
            'font-src': ["'self'"],
            'connect-src': ["'self'"],
            'frame-src': ["'none'"],
            'object-src': ["'none'"],
            'base-uri': ["'self'"],
            'form-action': ["'self'"]
        }
    
    def generate_policy_header(self, custom_policy: Dict[str, List[str]] = None) -> str:
        """Generate CSP header string."""
        policy = custom_policy or self.default_policy
        
        header_parts = []
        for directive, sources in policy.items():
            header_parts.append(f"{directive} {' '.join(sources)}")
        
        return "; ".join(header_parts)
    
    def validate_policy(self, policy: Dict[str, List[str]]) -> bool:
        """Validate CSP policy configuration."""
        required_directives = ['default-src']
        
        for directive in required_directives:
            if directive not in policy:
                return False
        
        return True 