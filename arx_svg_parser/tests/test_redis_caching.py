"""
Tests for Redis Caching Implementation

Tests the Redis cache utility and its integration with:
- Export service caching
- Metadata service caching
- Cache hit/miss scenarios
- Error handling and fallbacks
- Performance metrics
"""

import pytest
import asyncio
import json
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime

from utils.cache import RedisCache, redis_cache, generate_export_cache_key, generate_metadata_cache_key
from services.metadata_service import MetadataService, ObjectMetadata, SymbolMetadata
from services.export_integration import ExportIntegration


class TestRedisCache:
    """Test Redis cache utility functionality."""
    
    @pytest.fixture
    async def cache(self):
        """Create a test cache instance."""
        cache = RedisCache(url="redis://localhost:6379", default_ttl=60)
        yield cache
        await cache.close()
    
    @pytest.mark.asyncio
    async def test_cache_initialization(self, cache):
        """Test cache initialization."""
        assert cache.url == "redis://localhost:6379"
        assert cache.default_ttl == 60
        assert cache.connected == False
        assert cache.stats['hits'] == 0
        assert cache.stats['misses'] == 0
    
    @pytest.mark.asyncio
    async def test_cache_set_and_get(self, cache):
        """Test basic set and get operations."""
        with patch('aioredis.from_url') as mock_redis:
            mock_redis_instance = AsyncMock()
            mock_redis.return_value = mock_redis_instance
            mock_redis_instance.ping.return_value = None
            mock_redis_instance.set.return_value = True
            mock_redis_instance.get.return_value = json.dumps({"test": "value"})
            
            # Test set
            result = await cache.set("test_key", {"test": "value"})
            assert result == True
            
            # Test get
            result = await cache.get("test_key")
            assert result == {"test": "value"}
    
    @pytest.mark.asyncio
    async def test_cache_miss(self, cache):
        """Test cache miss scenario."""
        with patch('aioredis.from_url') as mock_redis:
            mock_redis_instance = AsyncMock()
            mock_redis.return_value = mock_redis_instance
            mock_redis_instance.ping.return_value = None
            mock_redis_instance.get.return_value = None
            
            result = await cache.get("nonexistent_key")
            assert result is None
            assert cache.stats['misses'] == 1
    
    @pytest.mark.asyncio
    async def test_cache_hit(self, cache):
        """Test cache hit scenario."""
        with patch('aioredis.from_url') as mock_redis:
            mock_redis_instance = AsyncMock()
            mock_redis.return_value = mock_redis_instance
            mock_redis_instance.ping.return_value = None
            mock_redis_instance.get.return_value = json.dumps({"test": "value"})
            
            result = await cache.get("test_key")
            assert result == {"test": "value"}
            assert cache.stats['hits'] == 1
    
    @pytest.mark.asyncio
    async def test_cache_delete(self, cache):
        """Test cache delete operation."""
        with patch('aioredis.from_url') as mock_redis:
            mock_redis_instance = AsyncMock()
            mock_redis.return_value = mock_redis_instance
            mock_redis_instance.ping.return_value = None
            mock_redis_instance.delete.return_value = 1
            
            result = await cache.delete("test_key")
            assert result == True
            assert cache.stats['deletes'] == 1
    
    @pytest.mark.asyncio
    async def test_cache_error_handling(self, cache):
        """Test error handling in cache operations."""
        with patch('aioredis.from_url') as mock_redis:
            mock_redis.side_effect = Exception("Connection failed")
            
            result = await cache.get("test_key")
            assert result is None
            assert cache.stats['errors'] > 0
    
    @pytest.mark.asyncio
    async def test_cache_stats(self, cache):
        """Test cache statistics."""
        with patch('aioredis.from_url') as mock_redis:
            mock_redis_instance = AsyncMock()
            mock_redis.return_value = mock_redis_instance
            mock_redis_instance.ping.return_value = None
            mock_redis_instance.get.return_value = json.dumps({"test": "value"})
            mock_redis_instance.set.return_value = True
            
            # Perform some operations
            await cache.set("key1", {"value": 1})
            await cache.get("key1")
            await cache.get("key2")  # Miss
            
            stats = cache.get_stats()
            assert stats['sets'] == 1
            assert stats['hits'] == 1
            assert stats['misses'] == 1
            assert 'hit_rate' in stats
    
    @pytest.mark.asyncio
    async def test_cache_health_check(self, cache):
        """Test cache health check."""
        with patch('aioredis.from_url') as mock_redis:
            mock_redis_instance = AsyncMock()
            mock_redis.return_value = mock_redis_instance
            mock_redis_instance.ping.return_value = None
            mock_redis_instance.set.return_value = True
            mock_redis_instance.get.return_value = json.dumps({"test": "value"})
            mock_redis_instance.delete.return_value = 1
            
            health = await cache.health_check()
            assert health['connected'] == True
            assert health['set_operation'] == True
            assert health['get_operation'] == True
            assert health['overall_healthy'] == True


class TestMetadataService:
    """Test metadata service with caching."""
    
    @pytest.fixture
    async def metadata_service(self):
        """Create a test metadata service."""
        return MetadataService(cache_ttl=60)
    
    @pytest.mark.asyncio
    async def test_get_object_metadata_cache_hit(self, metadata_service):
        """Test object metadata retrieval with cache hit."""
        with patch.object(metadata_service.cache, 'get') as mock_get:
            mock_get.return_value = {
                "object_id": "test_obj",
                "object_type": "symbol",
                "name": "Test Object",
                "description": "Test description",
                "created_at": "2024-01-01T00:00:00",
                "updated_at": "2024-01-01T00:00:00",
                "created_by": "test_user",
                "version": "1.0",
                "tags": ["tag1", "tag2"],
                "properties": {"prop1": "value1"},
                "relationships": ["rel1"],
                "location": None,
                "status": "active",
                "metadata_hash": None
            }
            
            result = await metadata_service.get_object_metadata("test_obj")
            
            assert result is not None
            assert result.object_id == "test_obj"
            assert result.name == "Test Object"
            mock_get.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_object_metadata_cache_miss(self, metadata_service):
        """Test object metadata retrieval with cache miss."""
        with patch.object(metadata_service.cache, 'get') as mock_get, \
             patch.object(metadata_service.cache, 'set') as mock_set:
            
            mock_get.return_value = None  # Cache miss
            
            result = await metadata_service.get_object_metadata("test_obj")
            
            assert result is not None
            assert result.object_id == "test_obj"
            mock_get.assert_called_once()
            mock_set.assert_called_once()  # Should cache the result
    
    @pytest.mark.asyncio
    async def test_get_symbol_metadata(self, metadata_service):
        """Test symbol metadata retrieval."""
        with patch.object(metadata_service.cache, 'get') as mock_get:
            mock_get.return_value = {
                "symbol_id": "test_symbol",
                "symbol_name": "Test Symbol",
                "category": "electrical",
                "system": "E",
                "version": "1.0",
                "created_at": "2024-01-01T00:00:00",
                "updated_at": "2024-01-01T00:00:00",
                "author": "test_user",
                "description": "Test symbol",
                "tags": ["electrical"],
                "properties": {"voltage": "120V"},
                "usage_count": 5,
                "rating": 4.5,
                "status": "active"
            }
            
            result = await metadata_service.get_symbol_metadata("test_symbol")
            
            assert result is not None
            assert result.symbol_id == "test_symbol"
            assert result.category == "electrical"
    
    @pytest.mark.asyncio
    async def test_update_object_metadata(self, metadata_service):
        """Test object metadata update with cache invalidation."""
        with patch.object(metadata_service, '_update_object_metadata_in_db') as mock_update, \
             patch.object(metadata_service.cache, 'delete') as mock_delete:
            
            mock_update.return_value = True
            
            metadata = ObjectMetadata(
                object_id="test_obj",
                object_type="symbol",
                name="Updated Object",
                description="Updated description"
            )
            
            result = await metadata_service.update_object_metadata("test_obj", metadata)
            
            assert result == True
            mock_update.assert_called_once()
            mock_delete.assert_called_once()  # Should invalidate cache
    
    @pytest.mark.asyncio
    async def test_invalidate_metadata_cache(self, metadata_service):
        """Test metadata cache invalidation."""
        with patch.object(metadata_service.cache, 'delete') as mock_delete:
            mock_delete.return_value = True
            
            result = await metadata_service.invalidate_metadata_cache("test_obj")
            
            assert result == True
            mock_delete.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_cache_stats(self, metadata_service):
        """Test cache statistics retrieval."""
        with patch.object(metadata_service.cache, 'get_stats') as mock_stats:
            mock_stats.return_value = {
                'hits': 10,
                'misses': 5,
                'sets': 8,
                'deletes': 2,
                'errors': 0,
                'fallbacks': 0,
                'hit_rate': 0.67,
                'connected': True
            }
            
            stats = await metadata_service.get_cache_stats()
            
            assert stats['hits'] == 10
            assert stats['misses'] == 5
            assert stats['hit_rate'] == 0.67
            mock_stats.assert_called_once()


class TestExportIntegration:
    """Test export integration with caching."""
    
    @pytest.fixture
    async def export_integration(self):
        """Create a test export integration instance."""
        return ExportIntegration()
    
    @pytest.mark.asyncio
    async def test_get_export_result_cache_hit(self, export_integration):
        """Test export result retrieval with cache hit."""
        with patch('utils.cache.redis_cache.get') as mock_get:
            mock_get.return_value = {
                "export_id": "test_export",
                "status": "completed",
                "created_at": "2024-01-01T00:00:00",
                "completed_at": "2024-01-01T00:00:00",
                "file_path": "/exports/test_export.svg",
                "file_size": 1024,
                "format": "svg",
                "metadata": {
                    "title": "Test Export",
                    "description": "Test export result",
                    "symbol_count": 25,
                    "element_count": 150
                }
            }
            
            result = await export_integration.get_export_result("test_export")
            
            assert result is not None
            assert result["export_id"] == "test_export"
            assert result["status"] == "completed"
            mock_get.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_export_result_cache_miss(self, export_integration):
        """Test export result retrieval with cache miss."""
        with patch('utils.cache.redis_cache.get') as mock_get, \
             patch('utils.cache.redis_cache.set') as mock_set, \
             patch.object(export_integration, '_query_export_from_db') as mock_query:
            
            mock_get.return_value = None  # Cache miss
            mock_query.return_value = {
                "export_id": "test_export",
                "status": "completed",
                "created_at": "2024-01-01T00:00:00"
            }
            
            result = await export_integration.get_export_result("test_export")
            
            assert result is not None
            assert result["export_id"] == "test_export"
            mock_get.assert_called_once()
            mock_query.assert_called_once()
            mock_set.assert_called_once()  # Should cache the result
    
    @pytest.mark.asyncio
    async def test_invalidate_export_cache(self, export_integration):
        """Test export cache invalidation."""
        with patch('utils.cache.redis_cache.delete') as mock_delete:
            mock_delete.return_value = True
            
            result = await export_integration.invalidate_export_cache("test_export")
            
            assert result == True
            mock_delete.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_export_result_error_handling(self, export_integration):
        """Test error handling in export result retrieval."""
        with patch('utils.cache.redis_cache.get') as mock_get, \
             patch.object(export_integration, '_query_export_from_db') as mock_query:
            
            mock_get.side_effect = Exception("Cache error")
            mock_query.return_value = {
                "export_id": "test_export",
                "status": "completed"
            }
            
            result = await export_integration.get_export_result("test_export")
            
            assert result is not None
            assert result["export_id"] == "test_export"
            mock_query.assert_called_once()  # Should fallback to database


class TestCacheKeyGeneration:
    """Test cache key generation functions."""
    
    def test_generate_export_cache_key(self):
        """Test export cache key generation."""
        key = generate_export_cache_key("test_export_123")
        assert key == "export:test_export_123:result"
    
    def test_generate_metadata_cache_key(self):
        """Test metadata cache key generation."""
        key = generate_metadata_cache_key("test_object_456")
        assert key == "object:test_object_456:metadata"


class TestCachePerformance:
    """Test cache performance characteristics."""
    
    @pytest.mark.asyncio
    async def test_cache_performance_under_load(self):
        """Test cache performance under concurrent load."""
        cache = RedisCache()
        
        with patch('aioredis.from_url') as mock_redis:
            mock_redis_instance = AsyncMock()
            mock_redis.return_value = mock_redis_instance
            mock_redis_instance.ping.return_value = None
            mock_redis_instance.set.return_value = True
            mock_redis_instance.get.return_value = json.dumps({"test": "value"})
            
            # Simulate concurrent operations
            tasks = []
            for i in range(10):
                tasks.append(cache.set(f"key_{i}", {"value": i}))
                tasks.append(cache.get(f"key_{i}"))
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Check that all operations completed
            assert len(results) == 20
            assert all(not isinstance(r, Exception) for r in results)
    
    @pytest.mark.asyncio
    async def test_cache_memory_efficiency(self):
        """Test cache memory efficiency."""
        cache = RedisCache()
        
        with patch('aioredis.from_url') as mock_redis:
            mock_redis_instance = AsyncMock()
            mock_redis.return_value = mock_redis_instance
            mock_redis_instance.ping.return_value = None
            mock_redis_instance.set.return_value = True
            
            # Test with large data
            large_data = {"data": "x" * 10000}  # 10KB of data
            
            result = await cache.set("large_key", large_data)
            assert result == True


if __name__ == "__main__":
    pytest.main([__file__]) 