"""
Unified Auth Service

Lightweight JWT validation and user resolution for unified middleware.
Uses configuration from application.config and avoids external deps.
"""

from __future__ import annotations

from typing import Optional, Dict, Any
import base64
import hmac
import hashlib
import json
from time import time

from application.config import get_security_config


class AuthService:
    def __init__(self) -> None:
        self.security = get_security_config()

    async def validate_token(self, token: str) -> Optional[Dict[str, Any]]:
        if token.startswith('Bearer '):
            token = token[7:]
        parts = token.split('.')
        if len(parts) != 3:
            return None

        def _b64url_decode(data: str) -> bytes:
            padding = '=' * (-len(data) % 4)
            return base64.urlsafe_b64decode(data + padding)

        try:
            header = json.loads(_b64url_decode(parts[0]).decode('utf-8'))
            payload = json.loads(_b64url_decode(parts[1]).decode('utf-8'))
        except Exception:
            return None

        if header.get('alg') != self.security.algorithm:
            return None

        signing_input = f"{parts[0]}.{parts[1]}".encode('utf-8')
        digest = hmac.new(self.security.secret_key.encode('utf-8'), signing_input, hashlib.sha256).digest()
        expected_sig = base64.urlsafe_b64encode(digest).decode('utf-8').rstrip('=')
        if not hmac.compare_digest(parts[2], expected_sig):
            return None

        exp = payload.get('exp')
        if exp is not None and time() > float(exp):
            return None

        return payload

    async def get_user_by_id(self, user_id: str):
        # Minimal user DTO to avoid new dependencies
        from application.unified.dto.user_dto import UserDTO
        return UserDTO(id=user_id, roles=["user"], permissions=["buildings:read"])  # type: ignore[arg-type]

    async def refresh_token(self, refresh_token: str) -> Optional[str]:
        return None

    async def logout(self, user_id: str) -> bool:
        return True
