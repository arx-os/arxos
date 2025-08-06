#!/usr/bin/env python3
"""
Rate Limiting System for MCP API

This module provides advanced rate limiting capabilities including:
- Multiple rate limiting strategies (fixed window, sliding window, token bucket)
- Adaptive rate limiting based on user behavior
- Rate limiting per endpoint, user, and IP
- Rate limiting with burst handling
- Integration with monitoring and alerting
"""

import asyncio
import time
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from collections import defaultdict, deque
import threading
import hashlib

from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


class RateLimitStrategy(str, Enum):
    """Rate limiting strategy enumeration"""

    FIXED_WINDOW = "fixed_window"
    SLIDING_WINDOW = "sliding_window"
    TOKEN_BUCKET = "token_bucket"
    LEAKY_BUCKET = "leaky_bucket"
    ADAPTIVE = "adaptive"


@dataclass
class RateLimitConfig:
    """Rate limit configuration"""

    requests_per_minute: int = 60
    requests_per_hour: int = 1000
    requests_per_day: int = 10000
    burst_limit: int = 10
    strategy: RateLimitStrategy = RateLimitStrategy.SLIDING_WINDOW
    adaptive_threshold: float = 0.8  # 80% of normal rate
    cooldown_period: int = 300  # 5 minutes


@dataclass
class RateLimitState:
    """Rate limit state for a client"""

    client_id: str
    requests: deque = field(default_factory=lambda: deque(maxlen=1000))
    tokens: float = 10.0
    last_token_refill: float = field(default_factory=time.time)
    burst_count: int = 0
    last_burst_reset: float = field(default_factory=time.time)
    is_limited: bool = False
    limited_until: Optional[float] = None
    adaptive_multiplier: float = 1.0


class SlidingWindowRateLimiter:
    """Sliding window rate limiter implementation"""

    def __init__(self, window_size: int = 60):
        self.window_size = window_size
        self.requests: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.lock = threading.RLock()

    def is_allowed(self, client_id: str, current_time: float = None) -> bool:
        """Check if request is allowed"""
        if current_time is None:
            current_time = time.time()

        with self.lock:
            client_requests = self.requests[client_id]

            # Remove old requests outside the window
            cutoff_time = current_time - self.window_size
            while client_requests and client_requests[0] < cutoff_time:
                client_requests.popleft()

            # Check if under limit
            return len(client_requests) < self.window_size

    def record_request(self, client_id: str, current_time: float = None):
        """Record a request"""
        if current_time is None:
            current_time = time.time()

        with self.lock:
            self.requests[client_id].append(current_time)


class TokenBucketRateLimiter:
    """Token bucket rate limiter implementation"""

    def __init__(self, capacity: int = 10, refill_rate: float = 1.0):
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.tokens: Dict[str, float] = defaultdict(lambda: capacity)
        self.last_refill: Dict[str, float] = defaultdict(time.time)
        self.lock = threading.RLock()

    def is_allowed(self, client_id: str, current_time: float = None) -> bool:
        """Check if request is allowed"""
        if current_time is None:
            current_time = time.time()

        with self.lock:
            # Refill tokens
            time_passed = current_time - self.last_refill[client_id]
            tokens_to_add = time_passed * self.refill_rate
            self.tokens[client_id] = min(
                self.capacity, self.tokens[client_id] + tokens_to_add
            )
            self.last_refill[client_id] = current_time

            # Check if we have tokens
            if self.tokens[client_id] >= 1.0:
                self.tokens[client_id] -= 1.0
                return True
            return False


class AdaptiveRateLimiter:
    """Adaptive rate limiter that adjusts based on system load and user behavior"""

    def __init__(self, base_config: RateLimitConfig):
        self.base_config = base_config
        self.client_states: Dict[str, RateLimitState] = {}
        self.system_load: float = 0.0
        self.error_rate: float = 0.0
        self.lock = threading.RLock()

        # Start background monitoring
        self._start_monitoring()

    def _start_monitoring(self):
        """Start background monitoring tasks"""

        def monitor():
            while True:
                try:
                    time.sleep(60)  # Monitor every minute
                    self._update_adaptive_limits()
                except Exception as e:
                    logger.error(f"Error in adaptive rate limiter monitoring: {e}")

        thread = threading.Thread(target=monitor, daemon=True)
        thread.start()

    def _update_adaptive_limits(self):
        """Update adaptive limits based on system metrics"""
        with self.lock:
            # Adjust based on system load
            if self.system_load > 0.8:
                # High load - reduce limits
                for state in self.client_states.values():
                    state.adaptive_multiplier = max(
                        0.5, state.adaptive_multiplier * 0.9
                    )
            elif self.system_load < 0.3:
                # Low load - increase limits
                for state in self.client_states.values():
                    state.adaptive_multiplier = min(
                        2.0, state.adaptive_multiplier * 1.1
                    )

            # Adjust based on error rate
            if self.error_rate > 0.05:  # 5% error rate
                for state in self.client_states.values():
                    state.adaptive_multiplier = max(
                        0.3, state.adaptive_multiplier * 0.8
                    )

    def update_system_metrics(self, load: float, error_rate: float):
        """Update system metrics for adaptive limiting"""
        with self.lock:
            self.system_load = load
            self.error_rate = error_rate

    def is_allowed(
        self, client_id: str, endpoint: str = None
    ) -> Tuple[bool, Dict[str, Any]]:
        """Check if request is allowed with adaptive limits"""
        current_time = time.time()

        with self.lock:
            if client_id not in self.client_states:
                self.client_states[client_id] = RateLimitState(client_id=client_id)

            state = self.client_states[client_id]

            # Check if currently limited
            if (
                state.is_limited
                and state.limited_until
                and current_time < state.limited_until
            ):
                return False, {
                    "limited": True,
                    "retry_after": int(state.limited_until - current_time),
                    "reason": "Rate limit exceeded",
                }

            # Calculate adaptive limits
            adaptive_limit = int(
                self.base_config.requests_per_minute * state.adaptive_multiplier
            )

            # Check burst limit
            if state.burst_count >= self.base_config.burst_limit:
                if (
                    current_time - state.last_burst_reset > 60
                ):  # Reset burst count every minute
                    state.burst_count = 0
                    state.last_burst_reset = current_time
                else:
                    return False, {
                        "limited": True,
                        "retry_after": 60,
                        "reason": "Burst limit exceeded",
                    }

            # Check rate limit
            recent_requests = [req for req in state.requests if current_time - req < 60]
            if len(recent_requests) >= adaptive_limit:
                # Apply cooldown
                state.is_limited = True
                state.limited_until = current_time + self.base_config.cooldown_period
                return False, {
                    "limited": True,
                    "retry_after": self.base_config.cooldown_period,
                    "reason": "Rate limit exceeded",
                }

            # Allow request
            state.requests.append(current_time)
            state.burst_count += 1
            state.is_limited = False
            state.limited_until = None

            return True, {
                "limited": False,
                "remaining": adaptive_limit - len(recent_requests) - 1,
                "reset_time": current_time + 60,
            }


class RateLimiterMiddleware:
    """FastAPI middleware for rate limiting"""

    def __init__(self, config: RateLimitConfig = None):
        self.config = config or RateLimitConfig()
        self.limiters: Dict[str, Any] = {}
        self.client_identifiers: Dict[str, str] = {}

        # Initialize limiters based on strategy
        self._initialize_limiters()

    def _initialize_limiters(self):
        """Initialize rate limiters based on strategy"""
        if self.config.strategy == RateLimitStrategy.SLIDING_WINDOW:
            self.limiters["sliding"] = SlidingWindowRateLimiter(60)
        elif self.config.strategy == RateLimitStrategy.TOKEN_BUCKET:
            self.limiters["token"] = TokenBucketRateLimiter(
                capacity=self.config.burst_limit,
                refill_rate=self.config.requests_per_minute / 60,
            )
        elif self.config.strategy == RateLimitStrategy.ADAPTIVE:
            self.limiters["adaptive"] = AdaptiveRateLimiter(self.config)

    def _get_client_id(self, request: Request) -> str:
        """Get client identifier from request"""
        # Try to get from headers first
        client_id = request.headers.get("X-Client-ID")
        if client_id:
            return client_id

        # Try to get from query parameters
        client_id = request.query_params.get("client_id")
        if client_id:
            return client_id

        # Use IP address as fallback
        client_ip = request.client.host
        return f"ip:{client_ip}"

    def _get_endpoint_key(self, request: Request) -> str:
        """Get endpoint key for rate limiting"""
        return f"{request.method}:{request.url.path}"

    async def __call__(self, request: Request, call_next):
        """Rate limiting middleware"""
        client_id = self._get_client_id(request)
        endpoint_key = self._get_endpoint_key(request)

        # Check rate limits
        allowed, details = await self._check_rate_limits(client_id, endpoint_key)

        if not allowed:
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": "Rate limit exceeded",
                    "details": details,
                    "retry_after": details.get("retry_after", 60),
                },
                headers={
                    "Retry-After": str(details.get("retry_after", 60)),
                    "X-RateLimit-Limit": str(self.config.requests_per_minute),
                    "X-RateLimit-Remaining": str(details.get("remaining", 0)),
                    "X-RateLimit-Reset": str(
                        details.get("reset_time", int(time.time()) + 60)
                    ),
                },
            )

        # Add rate limit headers to response
        response = await call_next(request)

        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(self.config.requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(details.get("remaining", 0))
        response.headers["X-RateLimit-Reset"] = str(
            details.get("reset_time", int(time.time()) + 60)
        )

        return response

    async def _check_rate_limits(
        self, client_id: str, endpoint_key: str
    ) -> Tuple[bool, Dict[str, Any]]:
        """Check rate limits for client and endpoint"""
        current_time = time.time()

        # Check different rate limiting strategies
        for strategy, limiter in self.limiters.items():
            if strategy == "sliding":
                if not limiter.is_allowed(client_id, current_time):
                    return False, {
                        "limited": True,
                        "retry_after": 60,
                        "reason": "Sliding window limit exceeded",
                    }
                limiter.record_request(client_id, current_time)

            elif strategy == "token":
                if not limiter.is_allowed(client_id, current_time):
                    return False, {
                        "limited": True,
                        "retry_after": 60,
                        "reason": "Token bucket limit exceeded",
                    }

            elif strategy == "adaptive":
                allowed, details = limiter.is_allowed(client_id, endpoint_key)
                if not allowed:
                    return False, details

        return True, {
            "limited": False,
            "remaining": self.config.requests_per_minute - 1,
            "reset_time": current_time + 60,
        }


class RateLimitManager:
    """Central rate limit manager"""

    def __init__(self):
        self.configs: Dict[str, RateLimitConfig] = {}
        self.middleware: Dict[str, RateLimiterMiddleware] = {}
        self.metrics: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))

        # Initialize default configurations
        self._initialize_default_configs()

    def _initialize_default_configs(self):
        """Initialize default rate limit configurations"""
        # Default configuration
        self.configs["default"] = RateLimitConfig(
            requests_per_minute=60,
            requests_per_hour=1000,
            requests_per_day=10000,
            burst_limit=10,
            strategy=RateLimitStrategy.SLIDING_WINDOW,
        )

        # Strict configuration for sensitive endpoints
        self.configs["strict"] = RateLimitConfig(
            requests_per_minute=30,
            requests_per_hour=500,
            requests_per_day=5000,
            burst_limit=5,
            strategy=RateLimitStrategy.TOKEN_BUCKET,
        )

        # Relaxed configuration for public endpoints
        self.configs["relaxed"] = RateLimitConfig(
            requests_per_minute=120,
            requests_per_hour=2000,
            requests_per_day=20000,
            burst_limit=20,
            strategy=RateLimitStrategy.ADAPTIVE,
        )

        # Create middleware for each configuration
        for name, config in self.configs.items():
            self.middleware[name] = RateLimiterMiddleware(config)

    def get_middleware(self, config_name: str = "default") -> RateLimiterMiddleware:
        """Get rate limiter middleware by configuration name"""
        return self.middleware.get(config_name, self.middleware["default"])

    def update_config(self, config_name: str, config: RateLimitConfig):
        """Update rate limit configuration"""
        self.configs[config_name] = config
        self.middleware[config_name] = RateLimiterMiddleware(config)
        logger.info(f"Updated rate limit configuration: {config_name}")

    def record_metric(self, client_id: str, endpoint: str, allowed: bool):
        """Record rate limiting metric"""
        self.metrics[client_id][
            f"{endpoint}:{'allowed' if allowed else 'blocked'}"
        ] += 1

    def get_metrics(self) -> Dict[str, Any]:
        """Get rate limiting metrics"""
        total_allowed = sum(
            count
            for client_metrics in self.metrics.values()
            for metric, count in client_metrics.items()
            if metric.endswith(":allowed")
        )

        total_blocked = sum(
            count
            for client_metrics in self.metrics.values()
            for metric, count in client_metrics.items()
            if metric.endswith(":blocked")
        )

        return {
            "total_requests": total_allowed + total_blocked,
            "allowed_requests": total_allowed,
            "blocked_requests": total_blocked,
            "block_rate": (
                (total_blocked / (total_allowed + total_blocked) * 100)
                if (total_allowed + total_blocked) > 0
                else 0
            ),
            "client_metrics": dict(self.metrics),
        }


# Global rate limit manager
rate_limit_manager = RateLimitManager()


def get_rate_limiter(config_name: str = "default") -> RateLimiterMiddleware:
    """Get rate limiter middleware"""
    return rate_limit_manager.get_middleware(config_name)


def require_rate_limit(config_name: str = "default"):
    """Dependency to require rate limiting"""
    return get_rate_limiter(config_name)
