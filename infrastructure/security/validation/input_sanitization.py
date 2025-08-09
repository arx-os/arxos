"""
Input Sanitization - Security Validation Utilities

This module provides comprehensive input sanitization utilities to prevent
security vulnerabilities like XSS, SQL injection, and other injection attacks.
"""

import re
import html
import urllib.parse
from typing import Any, Dict, List, Optional, Union
import logging

logger = logging.getLogger(__name__)


class InputSanitizer:
    """
    Comprehensive input sanitization utility.

    This class provides methods to sanitize various types of input data
    to prevent security vulnerabilities.
    """

    def __init__(self):
        """Initialize input sanitizer with security patterns."""
        # XSS patterns
        self.xss_patterns = [
            r'<script[^>]*>.*?</script>',
            r'<iframe[^>]*>.*?</iframe>',
            r'<object[^>]*>.*?</object>',
            r'<embed[^>]*>',
            r'<form[^>]*>.*?</form>',
            r'<input[^>]*>',
            r'<textarea[^>]*>.*?</textarea>',
            r'<select[^>]*>.*?</select>',
            r'<button[^>]*>.*?</button>',
            r'<link[^>]*>',
            r'<meta[^>]*>',
            r'<style[^>]*>.*?</style>',
            r'<link[^>]*>',
            r'javascript:',
            r'vbscript:',
            r'onload=',
            r'onerror=',
            r'onclick=',
            r'onmouseover=',
            r'onfocus=',
            r'onblur=',
            r'onchange=',
            r'onsubmit=',
            r'onreset=',
            r'onselect=',
            r'onunload=',
            r'onabort=',
            r'onbeforeunload=',
            r'onerror=',
            r'onhashchange=',
            r'onmessage=',
            r'onoffline=',
            r'ononline=',
            r'onpagehide=',
            r'onpageshow=',
            r'onpopstate=',
            r'onresize=',
            r'onstorage=',
            r'oncontextmenu=',
            r'oninput=',
            r'oninvalid=',
            r'onkeydown=',
            r'onkeypress=',
            r'onkeyup=',
            r'onmousedown=',
            r'onmousemove=',
            r'onmouseout=',
            r'onmouseup=',
            r'onwheel=',
            r'ondrag=',
            r'ondragend=',
            r'ondragenter=',
            r'ondragleave=',
            r'ondragover=',
            r'ondragstart=',
            r'ondrop=',
            r'oncopy=',
            r'oncut=',
            r'onpaste=',
            r'onselectstart=',
            r'onselectionchange=',
            r'ontouchcancel=',
            r'ontouchend=',
            r'ontouchmove=',
            r'ontouchstart=',
            r'onvolumechange=',
            r'onratechange=',
            r'onseeked=',
            r'onseeking=',
            r'onstalled=',
            r'onsuspend=',
            r'ontimeupdate=',
            r'onwaiting=',
            r'oncanplay=',
            r'oncanplaythrough=',
            r'ondurationchange=',
            r'onloadeddata=',
            r'onloadedmetadata=',
            r'onloadstart=',
            r'onprogress=',
            r'onreadystatechange=',
            r'onabort=',
            r'onbeforeunload=',
            r'onerror=',
            r'onhashchange=',
            r'onmessage=',
            r'onoffline=',
            r'ononline=',
            r'onpagehide=',
            r'onpageshow=',
            r'onpopstate=',
            r'onresize=',
            r'onstorage=',
            r'oncontextmenu=',
            r'oninput=',
            r'oninvalid=',
            r'onkeydown=',
            r'onkeypress=',
            r'onkeyup=',
            r'onmousedown=',
            r'onmousemove=',
            r'onmouseout=',
            r'onmouseup=',
            r'onwheel=',
            r'ondrag=',
            r'ondragend=',
            r'ondragenter=',
            r'ondragleave=',
            r'ondragover=',
            r'ondragstart=',
            r'ondrop=',
            r'oncopy=',
            r'oncut=',
            r'onpaste=',
            r'onselectstart=',
            r'onselectionchange=',
            r'ontouchcancel=',
            r'ontouchend=',
            r'ontouchmove=',
            r'ontouchstart=',
            r'onvolumechange=',
            r'onratechange=',
            r'onseeked=',
            r'onseeking=',
            r'onstalled=',
            r'onsuspend=',
            r'ontimeupdate=',
            r'onwaiting=',
            r'oncanplay=',
            r'oncanplaythrough=',
            r'ondurationchange=',
            r'onloadeddata=',
            r'onloadedmetadata=',
            r'onloadstart=',
            r'onprogress=',
            r'onreadystatechange='
        ]

        # SQL injection patterns
        self.sql_patterns = [
            r'(\b(union|select|insert|update|delete|drop|create|alter|exec|execute|declare|cast|convert|truncate|backup|restore)\b)',
            r'(\b(and|or)\b\s+\d+\s*=\s*\d+)',
            r'(\b(and|or)\b\s+\'[^\']*\'\s*=\s*\'[^\']*\')',
            r'(\b(and|or)\b\s+\"[^\"]*\"\s*=\s*\"[^\"]*\"\s*--\s*$)',
            r'(\b(and|or)\b\s+\'[^\']*\'\s*=\s*\'[^\']*\'\s*--\s*$)',
            r'(\b(and|or)\b\s+\"[^\"]*\"\s*=\s*\"[^\"]*\"\s*#\s*$)',
            r'(\b(and|or)\b\s+\'[^\']*\'\s*=\s*\'[^\']*\'\s*#\s*$)',
            r'(\b(and|or)\b\s+\"[^\"]*\"\s*=\s*\"[^\"]*\"\s*/\*\s*$)',
            r'(\b(and|or)\b\s+\'[^\']*\'\s*=\s*\'[^\']*\'\s*/\*\s*$)',
            r'(\b(and|or)\b\s+\"[^\"]*\"\s*=\s*\"[^\"]*\"\s*\*\s*$)',
            r'(\b(and|or)\b\s+\'[^\']*\'\s*=\s*\'[^\']*\'\s*\*\s*$)',
            r'(\b(and|or)\b\s+\"[^\"]*\"\s*=\s*\"[^\"]*\"\s*;\s*$)',
            r'(\b(and|or)\b\s+\'[^\']*\'\s*=\s*\'[^\']*\'\s*;\s*$)
        ]

        # Path traversal patterns
        self.path_patterns = [
            r'\.\./',
            r'\.\.\\',
            r'%2e%2e%2f',
            r'%2e%2e%5c',
            r'%252e%252e%252f',
            r'%252e%252e%255c',
            r'%c0%ae%c0%ae%c0%af',
            r'%c0%ae%c0%ae%c0%5c',
            r'%c1%9c%c1%9c%c1%af',
            r'%c1%9c%c1%9c%c1%5c'
        ]

        # Compile patterns for efficiency
        self.xss_regex = re.compile('|'.join(self.xss_patterns), re.IGNORECASE)
        self.sql_regex = re.compile('|'.join(self.sql_patterns), re.IGNORECASE)
        self.path_regex = re.compile('|'.join(self.path_patterns), re.IGNORECASE)

    def sanitize_text(self, text: str, max_length: Optional[int] = None) -> str:
        """
        Sanitize text input to prevent XSS and other attacks.

        Args:
            text: Text to sanitize
            max_length: Maximum length allowed

        Returns:
            Sanitized text
        """
        if not text:
            return ""

        # Convert to string if needed
        text = str(text)

        # Check length
        if max_length and len(text) > max_length:
            text = text[:max_length]

        # Remove XSS patterns
        text = self.xss_regex.sub('', text)

        # HTML encode special characters
        text = html.escape(text)

        # Remove null bytes
        text = text.replace('\x00', '')

        # Normalize whitespace
        text = ' '.join(text.split()
        return text.strip()

    def sanitize_html(self, html_content: str, allowed_tags: Optional[List[str]] = None) -> str:
        """
        Sanitize HTML content while preserving allowed tags.

        Args:
            html_content: HTML content to sanitize
            allowed_tags: List of allowed HTML tags

        Returns:
            Sanitized HTML content
        """
        if not html_content:
            return ""

        # Default allowed tags
        if allowed_tags is None:
            allowed_tags = ['p', 'br', 'strong', 'em', 'u', 'ol', 'ul', 'li', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']

        # Remove all script tags and event handlers
        html_content = self.xss_regex.sub('', html_content)

        # Only allow specified tags
        import re
        pattern = r'<(?!\/?(?:' + '|'.join(allowed_tags) + r')\b)[^>]+>'
        html_content = re.sub(pattern, '', html_content)

        return html_content

    def sanitize_url(self, url: str) -> str:
        """
        Sanitize URL to prevent open redirect and other attacks.

        Args:
            url: URL to sanitize

        Returns:
            Sanitized URL
        """
        if not url:
            return ""

        # Remove dangerous protocols
        dangerous_protocols = ['javascript:', 'vbscript:', 'data:', 'file:']
        url_lower = url.lower()

        for protocol in dangerous_protocols:
            if url_lower.startswith(protocol):
                return ""

        # URL encode to prevent injection
        try:
            parsed = urllib.parse.urlparse(url)
            if parsed.scheme not in ['http', 'https', 'ftp']:
                return ""

            # Reconstruct URL with encoded components
            sanitized_url = urllib.parse.urlunparse((
                parsed.scheme,
                parsed.netloc,
                urllib.parse.quote(parsed.path),
                parsed.params,
                parsed.query,
                parsed.fragment
            ))

            return sanitized_url

        except Exception as e:
            logger.warning(f"Error sanitizing URL {url}: {e}")
            return ""

    def sanitize_filename(self, filename: str) -> str:
        """
        Sanitize filename to prevent path traversal attacks.

        Args:
            filename: Filename to sanitize

        Returns:
            Sanitized filename
        """
        if not filename:
            return ""

        # Remove path traversal patterns
        filename = self.path_regex.sub('', filename)

        # Remove dangerous characters
        dangerous_chars = ['<', '>', ':', '"', '|', '?', '*', '\\', '/']"
        for char in dangerous_chars:
            filename = filename.replace(char, '_')

        # Remove null bytes
        filename = filename.replace('\x00', '')

        # Limit length
        if len(filename) > 255:
            name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
            filename = name[:255-len(ext)-1] + '.' + ext if ext else name[:255]

        return filename.strip()

    def sanitize_sql_input(self, sql_input: str) -> str:
        """
        Sanitize SQL input to prevent SQL injection.

        Args:
            sql_input: SQL input to sanitize

        Returns:
            Sanitized SQL input
        """
        if not sql_input:
            return ""

        # Remove SQL injection patterns
        sql_input = self.sql_regex.sub('', sql_input)

        # Remove dangerous characters
        dangerous_chars = [';', '--', '/*', '*/', 'xp_', 'sp_']
        for char in dangerous_chars:
            sql_input = sql_input.replace(char, '')

        # HTML encode
        sql_input = html.escape(sql_input)

        return sql_input.strip()

    def sanitize_json(self, json_data: Union[Dict, List, str]) -> Union[Dict, List, str]:
        """
        Sanitize JSON data recursively.

        Args:
            json_data: JSON data to sanitize

        Returns:
            Sanitized JSON data
        """
        if isinstance(json_data, dict):
            return {self.sanitize_text(k): self.sanitize_json(v) for k, v in json_data.items()}
        elif isinstance(json_data, list):
            return [self.sanitize_json(item) for item in json_data]
        elif isinstance(json_data, str):
            return self.sanitize_text(json_data)
        else:
            return json_data

    def validate_email(self, email: str) -> bool:
        """
        Validate email address format.

        Args:
            email: Email address to validate

        Returns:
            True if email is valid
        """
        if not email:
            return False

        # Basic email validation pattern
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(email_pattern, email)
    def validate_phone(self, phone: str) -> bool:
        """
        Validate phone number format.

        Args:
            phone: Phone number to validate

        Returns:
            True if phone number is valid
        """
        if not phone:
            return False

        # Remove all non-digit characters
        digits_only = re.sub(r'\D', '', phone)

        # Check if it's a reasonable length (7-15 digits)
        return 7 <= len(digits_only) <= 15

    def sanitize_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sanitize dictionary data recursively.

        Args:
            data: Dictionary to sanitize

        Returns:
            Sanitized dictionary
        """
        sanitized = {}

        for key, value in data.items():
            # Sanitize key
            sanitized_key = self.sanitize_text(str(key)
            # Sanitize value based on type
            if isinstance(value, str):
                sanitized_value = self.sanitize_text(value)
            elif isinstance(value, dict):
                sanitized_value = self.sanitize_dict(value)
            elif isinstance(value, list):
                sanitized_value = [self.sanitize_text(str(item)) if isinstance(item, str) else item for item in value]
            else:
                sanitized_value = value

            sanitized[sanitized_key] = sanitized_value

        return sanitized

    def check_for_malicious_content(self, content: str) -> bool:
        """
        Check if content contains malicious patterns.

        Args:
            content: Content to check

        Returns:
            True if malicious content detected
        """
        if not content:
            return False

        # Check for XSS patterns
        if self.xss_regex.search(content):
            return True

        # Check for SQL injection patterns
        if self.sql_regex.search(content):
            return True

        # Check for path traversal patterns
        if self.path_regex.search(content):
            return True

        return False
