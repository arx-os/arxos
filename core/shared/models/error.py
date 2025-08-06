from typing import Optional, Dict
from pydantic import BaseModel


class ErrorResponse(BaseModel):
    error: str
    code: str
    details: Optional[Dict] = None
