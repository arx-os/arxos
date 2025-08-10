from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class UserDTO:
    id: str
    roles: Optional[List[str]] = None
    permissions: Optional[List[str]] = None
