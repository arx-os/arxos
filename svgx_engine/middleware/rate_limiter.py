"""
SVGX Engine - Rate Limiting Middleware

Provides comprehensive rate limiting for SVGX Engine with:
- Token bucket algorithm
- Sliding window algorithm
- Per-user and per-endpoint limits
- Configurable rate limits
- Rate limit headers
"""

import time
import threading
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json

from svgx_engine.logging.structured_logger import get_logger

logger = get_logger(__name__)


class RateLimitAlgorithm(Enum):
    """Rate limiting algorithms."""

    TOKEN_BUCKET = "token_bucket"
    SLIDING_WINDOW = "sliding_window"
    FIXED_WINDOW = "fixed_window"


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting."""

    requests_per_minute: int = 60
    requests_per_hour: int = 1000
    requests_per_day: int = 10000
    burst_limit: int = 10
    algorithm: RateLimitAlgorithm = RateLimitAlgorithm.TOKEN_BUCKET
    enable_headers: bool = True
    enable_logging: bool = True


@dataclass
class RateLimitResult:
    """Result of rate limit check."""

    allowed: bool
    remaining: int
    reset_time: float
    retry_after: Optional[int] = None
    limit_exceeded: bool = False
    rate_limit_type: Optional[str] = None


class TokenBucket:
    """Token bucket rate limiter implementation."""

    def __init__(self, capacity: int, refill_rate: float):
        """Initialize token bucket."""
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.tokens = capacity
        self.last_refill = time.time()
        self.lock = threading.Lock()

    def consume(self, tokens: int = 1) -> bool:
        """Consume tokens from bucket."""
        with self.lock:
            self._refill()

            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False

    def _refill(self):
        """Refill tokens based on time passed."""
        now = time.time()
        time_passed = now - self.last_refill
        tokens_to_add = time_passed * self.refill_rate

        self.tokens = min(self.capacity, self.tokens + tokens_to_add)
        self.last_refill = now

    def get_remaining(self) -> int:
        """Get remaining tokens."""
        with self.lock:
            self._refill()
            return int(self.tokens)


class SlidingWindow:
    """Sliding window rate limiter implementation."""

    def __init__(self, window_size: int, max_requests: int):
        """Initialize sliding window."""
        self.window_size = window_size
        self.max_requests = max_requests
        self.requests = []
        self.lock = threading.Lock()

    def is_allowed(self) -> bool:
        """Check if request is allowed."""
        with self.lock:
            now = time.time()

            # Remove old requests outside the window
            self.requests = [
                req_time
                for req_time in self.requests
                if now - req_time < self.window_size
            ]

            if len(self.requests) < self.max_requests:
                self.requests.append(now)
                return True

            return False

    def get_remaining(self) -> int:
        """Get remaining requests allowed."""
        with self.lock:
            now = time.time()
            self.requests = [
                req_time
                for req_time in self.requests
                if now - req_time < self.window_size
            ]
            return max(0, self.max_requests - len(self.requests))

    def get_reset_time(self) -> float:
        """Get time when rate limit resets."""
        if not self.requests:
            return time.time()

        with self.lock:
            oldest_request = min(self.requests)
            return oldest_request + self.window_size


class SVGXRateLimiter:
    """
    Comprehensive rate limiter for SVGX Engine.

    Features:
    - Multiple rate limiting algorithms (Token Bucket, Sliding Window, Fixed Window)
    - Per-user and per-endpoint rate limiting
    - Configurable rate limits
    - Rate limit headers
    - Comprehensive logging and monitoring
    """

    def __init__(self, config: Optional[RateLimitConfig] = None):
        """Initialize the rate limiter."""
        self.config = config or RateLimitConfig()
        self.limiters: Dict[str, Any] = {}
        self.user_limits: Dict[str, Dict[str, Any]] = {}
        self.endpoint_limits: Dict[str, Dict[str, Any]] = {}
        self.stats = {
            "total_requests": 0,
            "rate_limited_requests": 0,
            "allowed_requests": 0,
            "unique_users": 0,
            "unique_endpoints": 0,
        }

        self._setup_default_limits()

        logger.info(
            "Rate limiter initialized",
            algorithm=self.config.algorithm.value,
            requests_per_minute=self.config.requests_per_minute,
        )

    def _setup_default_limits(self):
        """Setup default rate limits."""
        # Default user limits
        self.user_limits["default"] = {
            "requests_per_minute": 60,
            "requests_per_hour": 1000,
            "requests_per_day": 10000,
            "burst_limit": 10,
        }

        # Default endpoint limits
        self.endpoint_limits["default"] = {
            "requests_per_minute": 120,
            "requests_per_hour": 2000,
            "requests_per_day": 20000,
            "burst_limit": 20,
        }

        # Specific endpoint limits
        self.endpoint_limits["/api/v1/svgx/parse"] = {
            "requests_per_minute": 30,
            "requests_per_hour": 500,
            "requests_per_day": 5000,
            "burst_limit": 5,
        }

        self.endpoint_limits["/api/v1/svgx/render"] = {
            "requests_per_minute": 20,
            "requests_per_hour": 300,
            "requests_per_day": 3000,
            "burst_limit": 3,
        }

    def check_rate_limit(
        self, user_id: str, endpoint: str, request_id: Optional[str] = None
    ) -> RateLimitResult:
        """
        Check if request is allowed based on rate limits.

        Args:
            user_id: User identifier
            endpoint: API endpoint
            request_id: Optional request identifier

        Returns:
            RateLimitResult: Rate limit check result
        """
        start_time = time.time()

        try:
            # Get limits for user and endpoint
            user_limit = self._get_user_limit(user_id)
            endpoint_limit = self._get_endpoint_limit(endpoint)

            # Check user rate limit
            user_result = self._check_user_limit(user_id, user_limit)
            if not user_result.allowed:
                self._log_rate_limit_exceeded(user_id, endpoint, "user", request_id)
                return user_result

            # Check endpoint rate limit
            endpoint_result = self._check_endpoint_limit(endpoint, endpoint_limit)
            if not endpoint_result.allowed:
                self._log_rate_limit_exceeded(user_id, endpoint, "endpoint", request_id)
                return endpoint_result

            # Request is allowed
            self._update_stats(True)

            # Combine results
            combined_result = RateLimitResult(
                allowed=True,
                remaining=min(user_result.remaining, endpoint_result.remaining),
                reset_time=min(user_result.reset_time, endpoint_result.reset_time),
                rate_limit_type="combined",
            )

            self._log_rate_limit_check(user_id, endpoint, combined_result, request_id)
            return combined_result

        except Exception as e:
            logger.error(
                "Rate limit check failed",
                error=str(e),
                user_id=user_id,
                endpoint=endpoint,
            )
            # Allow request if rate limiting fails
            return RateLimitResult(
                allowed=True,
                remaining=999,
                reset_time=time.time() + 3600,
                rate_limit_type="fallback",
            )

    def _get_user_limit(self, user_id: str) -> Dict[str, Any]:
        """Get rate limit configuration for user."""
        return self.user_limits.get(user_id, self.user_limits["default"])

    def _get_endpoint_limit(self, endpoint: str) -> Dict[str, Any]:
        """Get rate limit configuration for endpoint."""
        return self.endpoint_limits.get(endpoint, self.endpoint_limits["default"])

    def _check_user_limit(
        self, user_id: str, limit_config: Dict[str, Any]
    ) -> RateLimitResult:
        """Check user-specific rate limit."""
        limiter_key = f"user:{user_id}"

        if self.config.algorithm == RateLimitAlgorithm.TOKEN_BUCKET:
            return self._check_token_bucket_limit(limiter_key, limit_config)
        elif self.config.algorithm == RateLimitAlgorithm.SLIDING_WINDOW:
            return self._check_sliding_window_limit(limiter_key, limit_config)
        else:
            return self._check_fixed_window_limit(limiter_key, limit_config)

    def _check_endpoint_limit(
        self, endpoint: str, limit_config: Dict[str, Any]
    ) -> RateLimitResult:
        """Check endpoint-specific rate limit."""
        limiter_key = f"endpoint:{endpoint}"

        if self.config.algorithm == RateLimitAlgorithm.TOKEN_BUCKET:
            return self._check_token_bucket_limit(limiter_key, limit_config)
        elif self.config.algorithm == RateLimitAlgorithm.SLIDING_WINDOW:
            return self._check_sliding_window_limit(limiter_key, limit_config)
        else:
            return self._check_fixed_window_limit(limiter_key, limit_config)

    def _check_token_bucket_limit(
        self, limiter_key: str, limit_config: Dict[str, Any]
    ) -> RateLimitResult:
        """Check rate limit using token bucket algorithm."""
        if limiter_key not in self.limiters:
            # Create new token bucket
            capacity = limit_config["burst_limit"]
            refill_rate = limit_config["requests_per_minute"] / 60.0
            self.limiters[limiter_key] = TokenBucket(capacity, refill_rate)

        bucket = self.limiters[limiter_key]
        allowed = bucket.consume(1)

        return RateLimitResult(
            allowed=allowed,
            remaining=bucket.get_remaining(),
            reset_time=time.time() + 60,  # Approximate reset time
            rate_limit_type="token_bucket",
        )

    def _check_sliding_window_limit(
        self, limiter_key: str, limit_config: Dict[str, Any]
    ) -> RateLimitResult:
        """Check rate limit using sliding window algorithm."""
        if limiter_key not in self.limiters:
            # Create new sliding window
            window_size = 60  # 1 minute window
            max_requests = limit_config["requests_per_minute"]
            self.limiters[limiter_key] = SlidingWindow(window_size, max_requests)

        window = self.limiters[limiter_key]
        allowed = window.is_allowed()

        return RateLimitResult(
            allowed=allowed,
            remaining=window.get_remaining(),
            reset_time=window.get_reset_time(),
            rate_limit_type="sliding_window",
        )

    def _check_fixed_window_limit(
        self, limiter_key: str, limit_config: Dict[str, Any]
    ) -> RateLimitResult:
        """Check rate limit using fixed window algorithm."""
        current_window = int(time.time() / 60)  # 1-minute windows
        window_key = f"{limiter_key}:{current_window}"

        if window_key not in self.limiters:
            self.limiters[window_key] = 0

        current_requests = self.limiters[window_key]
        max_requests = limit_config["requests_per_minute"]

        if current_requests < max_requests:
            self.limiters[window_key] += 1
            allowed = True
        else:
            allowed = False

        return RateLimitResult(
            allowed=allowed,
            remaining=max(0, max_requests - current_requests),
            reset_time=(current_window + 1) * 60,
            rate_limit_type="fixed_window",
        )

    def _log_rate_limit_check(
        self,
        user_id: str,
        endpoint: str,
        result: RateLimitResult,
        request_id: Optional[str] = None,
    ):
        """Log rate limit check result."""
        if self.config.enable_logging:
            logger.info(
                "Rate limit check",
                user_id=user_id,
                endpoint=endpoint,
                allowed=result.allowed,
                remaining=result.remaining,
                rate_limit_type=result.rate_limit_type,
                request_id=request_id,
            )

    def _log_rate_limit_exceeded(
        self,
        user_id: str,
        endpoint: str,
        limit_type: str,
        request_id: Optional[str] = None,
    ):
        """Log rate limit exceeded event."""
        if self.config.enable_logging:
            logger.warning(
                "Rate limit exceeded",
                user_id=user_id,
                endpoint=endpoint,
                limit_type=limit_type,
                request_id=request_id,
            )

    def _update_stats(self, allowed: bool):
        """Update rate limiter statistics."""
        self.stats["total_requests"] += 1
        if allowed:
            self.stats["allowed_requests"] += 1
        else:
            self.stats["rate_limited_requests"] += 1

    def set_user_limit(self, user_id: str, limits: Dict[str, Any]):
        """Set custom rate limits for a user."""
        self.user_limits[user_id] = limits
        logger.info("User rate limits updated", user_id=user_id, limits=limits)

    def set_endpoint_limit(self, endpoint: str, limits: Dict[str, Any]):
        """Set custom rate limits for an endpoint."""
        self.endpoint_limits[endpoint] = limits
        logger.info("Endpoint rate limits updated", endpoint=endpoint, limits=limits)

    def get_rate_limit_headers(self, result: RateLimitResult) -> Dict[str, str]:
        """Generate rate limit headers for HTTP response."""
        if not self.config.enable_headers:
            return {}

        headers = {
            "X-RateLimit-Remaining": str(result.remaining),
            "X-RateLimit-Reset": str(int(result.reset_time)),
        }

        if result.retry_after:
            headers["Retry-After"] = str(result.retry_after)

        return headers

    def get_rate_limit_statistics(self) -> Dict[str, Any]:
        """Get rate limiter statistics."""
        return {
            "stats": self.stats,
            "algorithm": self.config.algorithm.value,
            "active_limiters": len(self.limiters),
            "user_limits": len(self.user_limits),
            "endpoint_limits": len(self.endpoint_limits),
            "rate_limit_config": {
                "requests_per_minute": self.config.requests_per_minute,
                "requests_per_hour": self.config.requests_per_hour,
                "requests_per_day": self.config.requests_per_day,
                "burst_limit": self.config.burst_limit,
            },
        }

    def clear_rate_limits(
        self, user_id: Optional[str] = None, endpoint: Optional[str] = None
    ):
        """Clear rate limits for specific user or endpoint."""
        if user_id:
            # Clear user-specific limiters
            keys_to_remove = [
                key for key in self.limiters.keys() if key.startswith(f"user:{user_id}")
            ]
            for key in keys_to_remove:
                del self.limiters[key]
            logger.info("User rate limits cleared", user_id=user_id)

        if endpoint:
            # Clear endpoint-specific limiters
            keys_to_remove = [
                key
                for key in self.limiters.keys()
                if key.startswith(f"endpoint:{endpoint}")
            ]
            for key in keys_to_remove:
                del self.limiters[key]
            logger.info("Endpoint rate limits cleared", endpoint=endpoint)

    def reset_statistics(self):
        """Reset rate limiter statistics."""
        self.stats = {
            "total_requests": 0,
            "rate_limited_requests": 0,
            "allowed_requests": 0,
            "unique_users": 0,
            "unique_endpoints": 0,
        }
        logger.info("Rate limiter statistics reset")


# Global rate limiter instance
_rate_limiter = None


def get_rate_limiter() -> SVGXRateLimiter:
    """Get the global rate limiter instance."""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = SVGXRateLimiter()
    return _rate_limiter


def check_rate_limit(
    user_id: str, endpoint: str, request_id: Optional[str] = None
) -> RateLimitResult:
    """Check rate limit using the global rate limiter."""
    limiter = get_rate_limiter()
    return limiter.check_rate_limit(user_id, endpoint, request_id)


def get_rate_limit_headers(result: RateLimitResult) -> Dict[str, str]:
    """Get rate limit headers using the global rate limiter."""
    limiter = get_rate_limiter()
    return limiter.get_rate_limit_headers(result)
