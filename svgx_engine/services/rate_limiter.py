import time
import threading
from typing import Dict, Optional, Tuple
from fastapi import Request, HTTPException
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)

class TokenBucket:
    """Token bucket implementation for rate limiting."""
    
    def __init__(self, capacity: int, refill_rate: float):
        """
        Initialize token bucket.
        
        Args:
            capacity: Maximum number of tokens
            refill_rate: Tokens per second to refill
        """
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.tokens = capacity
        self.last_refill = time.time()
        self.lock = threading.Lock()
    
    def consume(self, tokens: int = 1) -> bool:
        """
        Try to consume tokens from the bucket.
        
        Args:
            tokens: Number of tokens to consume
            
        Returns:
            True if tokens were consumed, False otherwise
        """
        with self.lock:
            now = time.time()
            time_passed = now - self.last_refill
            tokens_to_add = time_passed * self.refill_rate
            
            self.tokens = min(self.capacity, self.tokens + tokens_to_add)
            self.last_refill = now
            
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False
    
    def get_tokens_remaining(self) -> int:
        """Get number of tokens remaining."""
        with self.lock:
            now = time.time()
            time_passed = now - self.last_refill
            tokens_to_add = time_passed * self.refill_rate
            
            self.tokens = min(self.capacity, self.tokens + tokens_to_add)
            self.last_refill = now
            
            return int(self.tokens)

class RateLimiter:
    """Rate limiter using token bucket algorithm."""
    
    def __init__(self):
        # Default rate limits (requests per minute)
        self.default_limits = {
            "GET": 60,      # 60 requests per minute for GET
            "POST": 30,     # 30 requests per minute for POST
            "PUT": 20,      # 20 requests per minute for PUT
            "DELETE": 10,   # 10 requests per minute for DELETE
            "PATCH": 20,    # 20 requests per minute for PATCH
            "websocket": 100  # 100 messages per minute for WebSocket
        }
        
        # Custom limits for specific endpoints
        self.endpoint_limits = {
            "POST /runtime/ui-event/": 100,  # Higher limit for UI events
            "POST /runtime/undo/": 20,       # Lower limit for undo/redo
            "POST /runtime/redo/": 20,
            "POST /runtime/lock/": 30,       # Moderate limit for locks
            "POST /runtime/unlock/": 30,
            "GET /metrics/": 10,             # Lower limit for metrics
            "GET /health/": 30,              # Moderate limit for health checks
        }
        
        # Rate limit buckets per user/session
        self.buckets: Dict[str, Dict[str, TokenBucket]] = defaultdict(dict)
        self.buckets_lock = threading.Lock()
        
        # Cleanup interval for expired buckets
        self.cleanup_interval = 3600  # 1 hour
        self.last_cleanup = time.time()
        self.cleanup_lock = threading.Lock()
    
    def get_client_identifier(self, request: Request) -> str:
        """
        Get unique identifier for the client.
        
        Priority:
        1. User ID from authentication
        2. Session ID
        3. IP address
        """
        # Try to get user ID from authentication
        user_id = getattr(request.state, 'user_id', None)
        if user_id:
            return f"user:{user_id}"
        
        # Try to get session ID
        session_id = getattr(request.state, 'session_id', None)
        if session_id:
            return f"session:{session_id}"
        
        # Fall back to IP address
        client_ip = request.client.host if request.client else "unknown"
        return f"ip:{client_ip}"
    
    def get_rate_limit(self, method: str, path: str) -> int:
        """Get rate limit for the endpoint."""
        endpoint_key = f"{method} {path}"
        
        # Check custom endpoint limits first
        if endpoint_key in self.endpoint_limits:
            return self.endpoint_limits[endpoint_key]
        
        # Return default limit for method
        return self.default_limits.get(method, 60)
    
    def get_or_create_bucket(self, client_id: str, method: str, path: str) -> TokenBucket:
        """Get or create a token bucket for the client and endpoint."""
        endpoint_key = f"{method}:{path}"
        
        with self.buckets_lock:
            if client_id not in self.buckets:
                self.buckets[client_id] = {}
            
            if endpoint_key not in self.buckets[client_id]:
                rate_limit = self.get_rate_limit(method, path)
                # Convert requests per minute to tokens per second
                refill_rate = rate_limit / 60.0
                self.buckets[client_id][endpoint_key] = TokenBucket(
                    capacity=rate_limit,
                    refill_rate=refill_rate
                )
            
            return self.buckets[client_id][endpoint_key]
    
    def check_rate_limit(self, request: Request) -> Tuple[bool, Dict]:
        """
        Check if request is within rate limits.
        
        Returns:
            Tuple of (allowed, response_data)
        """
        client_id = self.get_client_identifier(request)
        method = request.method
        path = request.url.path
        
        bucket = self.get_or_create_bucket(client_id, method, path)
        
        # Try to consume a token
        if bucket.consume(1):
            # Request allowed
            return True, {
                "status": "allowed",
                "tokens_remaining": bucket.get_tokens_remaining(),
                "rate_limit": self.get_rate_limit(method, path)
            }
        else:
            # Request blocked
            return False, {
                "status": "rate_limited",
                "tokens_remaining": bucket.get_tokens_remaining(),
                "rate_limit": self.get_rate_limit(method, path),
                "retry_after": self._calculate_retry_after(bucket)
            }
    
    def _calculate_retry_after(self, bucket: TokenBucket) -> int:
        """Calculate retry-after seconds."""
        tokens_needed = 1
        tokens_remaining = bucket.get_tokens_remaining()
        
        if tokens_remaining >= tokens_needed:
            return 0
        
        tokens_missing = tokens_needed - tokens_remaining
        seconds_needed = tokens_missing / bucket.refill_rate
        
        return max(1, int(seconds_needed))
    
    def cleanup_expired_buckets(self):
        """Clean up old buckets to prevent memory leaks."""
        with self.cleanup_lock:
            now = time.time()
            if now - self.last_cleanup < self.cleanup_interval:
                return
            
            with self.buckets_lock:
                # Remove buckets older than 1 hour
                cutoff_time = now - 3600
                buckets_to_remove = []
                
                for client_id, endpoint_buckets in self.buckets.items():
                    # For now, we'll keep all buckets
                    # In a more sophisticated implementation, we could track last access
                    pass
                
                self.last_cleanup = now
                logger.debug(f"Rate limiter cleanup completed")
    
    def get_rate_limit_info(self, request: Request) -> Dict:
        """Get rate limit information for the request."""
        client_id = self.get_client_identifier(request)
        method = request.method
        path = request.url.path
        
        bucket = self.get_or_create_bucket(client_id, method, path)
        
        return {
            "client_id": client_id,
            "method": method,
            "path": path,
            "rate_limit": self.get_rate_limit(method, path),
            "tokens_remaining": bucket.get_tokens_remaining(),
            "tokens_capacity": bucket.capacity,
            "refill_rate": bucket.refill_rate
        }

# Global rate limiter instance
rate_limiter = RateLimiter()

def rate_limit_middleware(request: Request, call_next):
    """FastAPI middleware for rate limiting."""
    # Skip rate limiting for certain paths
    skip_paths = ["/docs", "/openapi.json", "/favicon.ico"]
    if any(request.url.path.startswith(path) for path in skip_paths):
        return call_next(request)
    
    # Check rate limit
    allowed, rate_limit_info = rate_limiter.check_rate_limit(request)
    
    if not allowed:
        # Return rate limit exceeded response
        retry_after = rate_limit_info.get("retry_after", 60)
        
        response_data = {
            "status": "error",
            "error_code": "RATE_LIMIT_EXCEEDED",
            "message": "Rate limit exceeded. Please try again later.",
            "rate_limit_info": rate_limit_info,
            "retry_after_seconds": retry_after
        }
        
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=429,
            content=response_data,
            headers={
                "Retry-After": str(retry_after),
                "X-RateLimit-Limit": str(rate_limit_info["rate_limit"]),
                "X-RateLimit-Remaining": str(rate_limit_info["tokens_remaining"]),
                "X-RateLimit-Reset": str(int(time.time() + retry_after))
            }
        )
    
    # Add rate limit headers to response
    response = call_next(request)
    
    response.headers["X-RateLimit-Limit"] = str(rate_limit_info["rate_limit"])
    response.headers["X-RateLimit-Remaining"] = str(rate_limit_info["tokens_remaining"])
    
    return response

def websocket_rate_limit_middleware(websocket, message_count: int = 1):
    """Rate limiting for WebSocket connections."""
    # Create a mock request object for rate limiting
    class MockRequest:
        def __init__(self, websocket):
            self.client = websocket.client
            self.state = type('State', (), {})()
            # Try to extract user/session info from websocket
            self.state.user_id = getattr(websocket, 'user_id', None)
            self.state.session_id = getattr(websocket, 'session_id', None)
    
    request = MockRequest(websocket)
    client_id = rate_limiter.get_client_identifier(request)
    
    # Use WebSocket-specific rate limit
    bucket = rate_limiter.get_or_create_bucket(client_id, "websocket", "/runtime/events")
    
    if not bucket.consume(message_count):
        # Rate limit exceeded for WebSocket
        retry_after = rate_limiter._calculate_retry_after(bucket)
        
        error_message = {
            "status": "error",
            "error_code": "RATE_LIMIT_EXCEEDED",
            "message": "WebSocket rate limit exceeded",
            "retry_after_seconds": retry_after
        }
        
        import json
        await websocket.send_text(json.dumps(error_message))
        return False
    
    return True 