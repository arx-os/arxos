"""
SVGX Engine - Cache Services

Provides caching functionality for SVGX Engine including:
- Redis cache client
- Memory cache
- Cache management utilities
"""

try:
    from svgx_engine.services.cache.redis_client import RedisCacheClient, get_cache_client, initialize_cache, close_cache
except ImportError:
    # Fallback for direct execution
    from .redis_client import RedisCacheClient, get_cache_client, initialize_cache, close_cache

__all__ = [
    'RedisCacheClient',
    'get_cache_client',
    'initialize_cache',
    'close_cache'
] 