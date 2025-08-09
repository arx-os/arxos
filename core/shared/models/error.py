from typing import Optional, Dict
from pydantic import BaseModel

class ErrorResponse(BaseModel):
    """
    Class for ErrorResponse functionality

Attributes:
        None

Methods:
        None

Example:
        instance = ErrorResponse()
        result = instance.method()
        print(result)
    """
    error: str
    code: str
    details: Optional[Dict] = None
