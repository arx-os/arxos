from pydantic import BaseModel
from typing import Optional, Dict

class ErrorResponse(BaseModel):
    error: str
    code: str
    details: Optional[Dict] = None 