
# Example of Secure Coding Practices

import html
import hashlib
import json
import secrets
import bcrypt
from fastapi import HTTPException
import logging

logger = logging.getLogger(__name__)

# XSS Prevention
def safe_render_content(content: str) -> str:
    """Safely render user content to prevent XSS"""
    return html.escape(content)

# Secure Hashing
def secure_hash(data: str) -> str:
    """Generate secure hash using SHA-256"""
    return hashlib.sha256(data.encode()).hexdigest()

def hash_password(password: str) -> str:
    """Hash password securely using bcrypt"""
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

# Secure Deserialization
def safe_deserialize(data: str) -> dict:
    """Safely deserialize data using JSON"""
    try:
        return json.loads(data)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON data: {e}")

# Secure Error Handling
def handle_errors(func):
    """Decorator to handle errors securely"""
def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ValueError as e:
            logger.error(f"Value error: {e}")
            raise HTTPException(status_code=400, detail="Invalid input")
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")
    return wrapper

# Usage Examples
@handle_errors
def process_user_input(user_input: str) -> str:
    """Process user input securely"""
    # Prevent XSS
    safe_input = safe_render_content(user_input)

    # Hash sensitive data
    input_hash = secure_hash(safe_input)

    return f"Processed: {safe_input} (hash: {input_hash})
@handle_errors
def authenticate_user(username: str, password: str) -> bool:
    """Authenticate user securely"""
    # Hash password for comparison
    hashed_password = hash_password(password)

    # Compare with stored hash (in real app)
    stored_hash = "stored_hash_here"
    return hashed_password == stored_hash
