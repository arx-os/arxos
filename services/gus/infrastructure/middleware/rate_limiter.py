"""
Rate Limiting Middleware

This module provides rate limiting functionality for the Gus AI service
to prevent abuse and ensure fair usage.
"""

import time
import asyncio
from typing import Dict, Optional, Callable
from collections import defaultdict, deque
from datetime import datetime, timedelta
import structlog
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

logger = structlog.get_logger()


class RateLimitExceeded(Exception):
    """Exception raised when rate limit is exceeded"""
    pass


class TokenBucket:
    """
    Token bucket algorithm for rate limiting.
    
    This implementation allows burst traffic while maintaining
    a sustainable rate over time.
    """
    
    def __init__(self, capacity: int, refill_rate: float, refill_period: float = 1.0):
        """
        Initialize token bucket.
        
        Args:
            capacity: Maximum number of tokens in bucket
            refill_rate: Number of tokens added per refill period
            refill_period: Time period in seconds for refill
        """
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.refill_period = refill_period
        self.tokens = capacity
        self.last_refill = time.time()
        self.lock = asyncio.Lock()
    
    async def consume(self, tokens: int = 1) -> bool:
        """
        Attempt to consume tokens from bucket.
        
        Args:
            tokens: Number of tokens to consume
            
        Returns:
            True if tokens were consumed, False if not enough tokens
        """
        async with self.lock:
            await self._refill()
            
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False
    
    async def _refill(self):
        """Refill tokens based on elapsed time"""
        now = time.time()
        elapsed = now - self.last_refill
        
        if elapsed >= self.refill_period:
            tokens_to_add = int(elapsed / self.refill_period) * self.refill_rate
            self.tokens = min(self.capacity, self.tokens + tokens_to_add)
            self.last_refill = now


class SlidingWindowCounter:
    """
    Sliding window counter for rate limiting.
    
    This implementation provides more accurate rate limiting
    over a sliding time window.
    """
    
    def __init__(self, window_size: int, max_requests: int):
        """
        Initialize sliding window counter.
        
        Args:
            window_size: Size of sliding window in seconds
            max_requests: Maximum requests allowed in window
        """
        self.window_size = window_size
        self.max_requests = max_requests
        self.requests = deque()
        self.lock = asyncio.Lock()
    
    async def is_allowed(self) -> bool:
        """
        Check if request is allowed within rate limit.
        
        Returns:
            True if request is allowed, False otherwise
        """
        async with self.lock:
            now = time.time()
            
            # Remove old requests outside window
            while self.requests and self.requests[0] < now - self.window_size:
                self.requests.popleft()
            
            # Check if under limit
            if len(self.requests) < self.max_requests:
                self.requests.append(now)
                return True
            
            return False
    
    async def get_reset_time(self) -> float:
        """Get time when the rate limit will reset"""
        async with self.lock:
            if not self.requests:
                return 0
            return self.requests[0] + self.window_size


class RateLimiter:
    """
    Rate limiter for API endpoints.
    
    Supports multiple rate limiting strategies and user-specific limits.
    """
    
    def __init__(
        self,
        default_limit: int = 100,
        window_size: int = 3600,
        burst_capacity: int = 10,
        strategy: str = "sliding_window"
    ):
        """
        Initialize rate limiter.
        
        Args:
            default_limit: Default request limit per window
            window_size: Time window in seconds
            burst_capacity: Burst capacity for token bucket
            strategy: Rate limiting strategy ("sliding_window" or "token_bucket")
        """
        self.default_limit = default_limit
        self.window_size = window_size
        self.burst_capacity = burst_capacity
        self.strategy = strategy
        
        # User-specific limiters
        self.user_limiters: Dict[str, any] = {}
        
        # IP-based limiters for anonymous users
        self.ip_limiters: Dict[str, any] = {}
        
        # Custom limits for specific users/roles
        self.custom_limits = {
            'premium': default_limit * 2,
            'enterprise': default_limit * 5,
            'admin': float('inf')
        }
        
        logger.info(f"Initialized RateLimiter: {strategy}, limit={default_limit}, window={window_size}s")
    
    def get_limiter(self, identifier: str, limit: Optional[int] = None):
        """Get or create limiter for identifier"""
        if limit is None:
            limit = self.default_limit
        
        if self.strategy == "token_bucket":
            return TokenBucket(
                capacity=self.burst_capacity,
                refill_rate=limit / self.window_size,
                refill_period=1.0
            )
        else:  # sliding_window
            return SlidingWindowCounter(
                window_size=self.window_size,
                max_requests=limit
            )
    
    async def check_rate_limit(
        self,
        identifier: str,
        user_role: Optional[str] = None,
        tokens: int = 1
    ) -> Dict[str, any]:
        """
        Check if request is within rate limit.
        
        Args:
            identifier: User ID or IP address
            user_role: Optional user role for custom limits
            tokens: Number of tokens to consume (for token bucket)
            
        Returns:
            Dictionary with rate limit status and headers
            
        Raises:
            RateLimitExceeded if limit is exceeded
        """
        # Determine limit based on role
        limit = self.custom_limits.get(user_role, self.default_limit)
        
        # Get or create limiter for user
        if identifier not in self.user_limiters:
            self.user_limiters[identifier] = self.get_limiter(identifier, limit)
        
        limiter = self.user_limiters[identifier]
        
        # Check rate limit
        if self.strategy == "token_bucket":
            allowed = await limiter.consume(tokens)
            remaining = int(limiter.tokens)
        else:  # sliding_window
            allowed = await limiter.is_allowed()
            remaining = limit - len(limiter.requests)
        
        # Prepare response headers
        headers = {
            'X-RateLimit-Limit': str(limit),
            'X-RateLimit-Remaining': str(max(0, remaining)),
            'X-RateLimit-Reset': str(int(time.time() + self.window_size))
        }
        
        if not allowed:
            retry_after = self.window_size if self.strategy == "token_bucket" else \
                         await limiter.get_reset_time() - time.time()
            
            headers['Retry-After'] = str(int(retry_after))
            
            raise RateLimitExceeded(f"Rate limit exceeded for {identifier}")
        
        return {
            'allowed': allowed,
            'remaining': remaining,
            'headers': headers
        }
    
    async def reset_limits(self, identifier: Optional[str] = None):
        """Reset rate limits for specific user or all users"""
        if identifier:
            if identifier in self.user_limiters:
                del self.user_limiters[identifier]
            if identifier in self.ip_limiters:
                del self.ip_limiters[identifier]
            logger.info(f"Reset rate limits for {identifier}")
        else:
            self.user_limiters.clear()
            self.ip_limiters.clear()
            logger.info("Reset all rate limits")


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    FastAPI middleware for rate limiting.
    
    This middleware automatically applies rate limiting to all API endpoints.
    """
    
    def __init__(
        self,
        app,
        rate_limiter: RateLimiter,
        exclude_paths: Optional[list] = None
    ):
        """
        Initialize middleware.
        
        Args:
            app: FastAPI application
            rate_limiter: RateLimiter instance
            exclude_paths: Paths to exclude from rate limiting
        """
        super().__init__(app)
        self.rate_limiter = rate_limiter
        self.exclude_paths = exclude_paths or ['/health', '/docs', '/openapi.json']
    
    async def dispatch(self, request: Request, call_next):
        """Process request with rate limiting"""
        # Skip rate limiting for excluded paths
        if request.url.path in self.exclude_paths:
            return await call_next(request)
        
        # Get identifier (user ID from auth or IP address)
        identifier = None
        user_role = None
        
        # Try to get user from request state (set by auth middleware)
        if hasattr(request.state, 'user'):
            identifier = request.state.user.id
            user_role = request.state.user.role
        else:
            # Fall back to IP address
            identifier = request.client.host
        
        try:
            # Check rate limit
            result = await self.rate_limiter.check_rate_limit(
                identifier=identifier,
                user_role=user_role
            )
            
            # Add rate limit headers to response
            response = await call_next(request)
            for header, value in result['headers'].items():
                response.headers[header] = value
            
            return response
            
        except RateLimitExceeded as e:
            logger.warning(f"Rate limit exceeded: {e}")
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Rate limit exceeded",
                    "message": "Too many requests. Please try again later.",
                    "retry_after": result['headers'].get('Retry-After', self.rate_limiter.window_size)
                },
                headers=result['headers']
            )
        except Exception as e:
            logger.error(f"Rate limiting error: {e}")
            # Don't block request on rate limiting errors
            return await call_next(request)


# Decorator for rate limiting specific endpoints
def rate_limit(
    max_requests: int = 10,
    window_size: int = 60,
    key_func: Optional[Callable] = None
):
    """
    Decorator for rate limiting specific endpoints.
    
    Args:
        max_requests: Maximum requests allowed
        window_size: Time window in seconds
        key_func: Function to extract rate limit key from request
    """
    def decorator(func):
        limiter = SlidingWindowCounter(window_size, max_requests)
        
        async def wrapper(*args, **kwargs):
            # Extract key for rate limiting
            if key_func:
                key = key_func(*args, **kwargs)
            else:
                key = "default"
            
            # Check rate limit
            if not await limiter.is_allowed():
                raise HTTPException(
                    status_code=429,
                    detail="Rate limit exceeded",
                    headers={
                        'Retry-After': str(window_size),
                        'X-RateLimit-Limit': str(max_requests),
                        'X-RateLimit-Remaining': '0'
                    }
                )
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator