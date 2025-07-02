from fastapi import Depends, HTTPException, status
from typing import Optional

def get_current_user():
    """
    Dummy authentication dependency for development/testing.
    Returns a mock user object.
    """
    return {"user_id": "dummy_user", "username": "testuser"}

def get_current_user_optional():
    """
    Optional authentication dependency that returns None if no user is authenticated.
    Returns a mock user object or None.
    """
    return {"user_id": "dummy_user", "username": "testuser"} 