"""
Rate Limiting for MCP Engineering

This module provides rate limiting functionality for the MCP Engineering API,
including sliding window implementation and IP-based rate limiting.
"""

import time
import logging
from typing import Dict, Optional, Any
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta
import asyncio

logger = logging.getLogger(__name__)


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting."""

    max_requests: int = 100
    window_seconds: int = 60
    burst_size: int = 10
    enable_sliding_window: bool = True
    enable_ip_based_limiting: bool = True
    enable_user_based_limiting: bool = True


class RateLimiter:
    """Rate limiting implementation with sliding window."""

    def __init__(self, config: Optional[RateLimitConfig] = None):
        """
        Initialize rate limiter.

        Args:
            config: Rate limiting configuration
        """
        self.config = config or RateLimitConfig()
        self.requests: Dict[str, list] = defaultdict(list)
        self.blocked_ips: Dict[str, datetime] = {}
        self.blocked_users: Dict[str, datetime] = {}
        self._lock = asyncio.Lock()

    def _cleanup_old_requests(self, key: str):
        """Remove old requests outside the time window."""
        current_time = time.time()
        window_start = current_time - self.config.window_seconds

        # Remove requests older than the window
        self.requests[key] = [
            req_time for req_time in self.requests[key] if req_time > window_start
        ]

    def _is_blocked(self, key: str, blocked_dict: Dict[str, datetime]) -> bool:
        """Check if a key is currently blocked."""
        if key in blocked_dict:
            block_until = blocked_dict[key]
            if datetime.utcnow() < block_until:
                return True
            else:
                # Remove expired block
                del blocked_dict[key]
        return False

    async def is_allowed(self, identifier: str, request_type: str = "api") -> bool:
        """
        Check if a request is allowed based on rate limiting.

        Args:
            identifier: IP address or user ID
            request_type: Type of request (api, auth, etc.)

        Returns:
            True if request is allowed, False otherwise
        """
        async with self._lock:
            # Check if IP is blocked
            if self.config.enable_ip_based_limiting and request_type == "api":
                if self._is_blocked(identifier, self.blocked_ips):
                    logger.warning(f"Rate limit exceeded for IP: {identifier}")
                    return False

            # Check if user is blocked
            if self.config.enable_user_based_limiting and request_type == "auth":
                if self._is_blocked(identifier, self.blocked_users):
                    logger.warning(f"Rate limit exceeded for user: {identifier}")
                    return False

            # Clean up old requests
            self._cleanup_old_requests(identifier)

            # Check current request count
            current_requests = len(self.requests[identifier])

            if current_requests >= self.config.max_requests:
                # Block the identifier for a period
                block_duration = timedelta(minutes=5)
                if request_type == "api":
                    self.blocked_ips[identifier] = datetime.utcnow() + block_duration
                else:
                    self.blocked_users[identifier] = datetime.utcnow() + block_duration

                logger.warning(
                    f"Rate limit exceeded for {identifier}, blocking for 5 minutes"
                )
                return False

            # Record the request
            self.requests[identifier].append(time.time())
            return True

    def get_remaining_requests(self, identifier: str) -> int:
        """
        Get remaining requests for an identifier.

        Args:
            identifier: IP address or user ID

        Returns:
            Number of remaining requests
        """
        self._cleanup_old_requests(identifier)
        current_requests = len(self.requests[identifier])
        return max(0, self.config.max_requests - current_requests)

    def get_reset_time(self, identifier: str) -> Optional[datetime]:
        """
        Get the time when rate limit resets for an identifier.

        Args:
            identifier: IP address or user ID

        Returns:
            Reset time or None if no requests
        """
        if not self.requests[identifier]:
            return None

        oldest_request = min(self.requests[identifier])
        reset_time = datetime.fromtimestamp(oldest_request + self.config.window_seconds)
        return reset_time

    def get_stats(self, identifier: str) -> Dict[str, Any]:
        """
        Get rate limiting statistics for an identifier.

        Args:
            identifier: IP address or user ID

        Returns:
            Rate limiting statistics
        """
        self._cleanup_old_requests(identifier)

        return {
            "identifier": identifier,
            "current_requests": len(self.requests[identifier]),
            "max_requests": self.config.max_requests,
            "remaining_requests": self.get_remaining_requests(identifier),
            "reset_time": self.get_reset_time(identifier),
            "is_blocked": (
                self._is_blocked(identifier, self.blocked_ips)
                or self._is_blocked(identifier, self.blocked_users)
            ),
        }

    def clear_limits(self, identifier: str):
        """
        Clear rate limiting for an identifier.

        Args:
            identifier: IP address or user ID
        """
        if identifier in self.requests:
            del self.requests[identifier]

        if identifier in self.blocked_ips:
            del self.blocked_ips[identifier]

        if identifier in self.blocked_users:
            del self.blocked_users[identifier]

    def get_global_stats(self) -> Dict[str, Any]:
        """
        Get global rate limiting statistics.

        Returns:
            Global statistics
        """
        total_requests = sum(len(requests) for requests in self.requests.values())
        total_blocked_ips = len(self.blocked_ips)
        total_blocked_users = len(self.blocked_users)

        return {
            "total_identifiers": len(self.requests),
            "total_requests": total_requests,
            "blocked_ips": total_blocked_ips,
            "blocked_users": total_blocked_users,
            "config": {
                "max_requests": self.config.max_requests,
                "window_seconds": self.config.window_seconds,
                "burst_size": self.config.burst_size,
            },
        }


class RateLimitMiddleware:
    """FastAPI middleware for rate limiting."""

    def __init__(self, rate_limiter: RateLimiter):
        """
        Initialize rate limiting middleware.

        Args:
            rate_limiter: Rate limiter instance
        """
        self.rate_limiter = rate_limiter

    async def __call__(self, request, call_next):
        """Process request with rate limiting."""
        # Get client IP
        client_ip = request.client.host if request.client else "unknown"

        # Check rate limit
        is_allowed = await self.rate_limiter.is_allowed(client_ip, "api")

        if not is_allowed:
            # Return rate limit exceeded response
            from fastapi import HTTPException

            raise HTTPException(
                status_code=429,
                detail={
                    "error": "Rate limit exceeded",
                    "retry_after": 60,
                    "remaining_requests": 0,
                },
            )

        # Add rate limit headers to response
        response = await call_next(request)

        stats = self.rate_limiter.get_stats(client_ip)
        response.headers["X-RateLimit-Limit"] = str(
            self.rate_limiter.config.max_requests
        )
        response.headers["X-RateLimit-Remaining"] = str(stats["remaining_requests"])

        if stats["reset_time"]:
            response.headers["X-RateLimit-Reset"] = stats["reset_time"].isoformat()

        return response


# Global rate limiter instance
rate_limiter = RateLimiter(RateLimitConfig())
