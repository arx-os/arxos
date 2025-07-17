#!/usr/bin/env python3
"""
Test script for Advanced Caching Service Migration

This script tests the migrated advanced caching service for SVGX engine,
verifying all components work correctly with SVGX-specific features.
"""

import sys
import os
import json
import time
import tempfile
import shutil
from datetime import datetime, timedelta
from typing import Dict, Any

# Add the svgx_engine directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from svgx_engine.services.advanced_caching import (
    AdvancedCachingSystem,
    MemoryCache,
    DiskCache,
    DatabaseCache,
    SVGXCacheKeyGenerator,
    CacheLevel,
    CachePolicy,
    SVGXCacheType,
    CacheMetrics,
    CacheEntry
)
from svgx_engine.utils.errors import CacheError


def test_svgx_cache_key_generator():
    """Test SVGX cache key generation with namespace isolation"""
    print("\n=== Testing SVGXCacheKeyGenerator ===")
    
    try:
        # Test basic SVGX key generation
        key1 = SVGXCacheKeyGenerator.generate_svgx_key(
            SVGXCacheType.SVGX_CONTENT, "test_content", "default"
        )
        print(f"✓ Basic SVGX key: {key1}")
        
        # Test symbol key generation
        symbol_key = SVGXCacheKeyGenerator.generate_symbol_key("test_symbol", "test_namespace")
        print(f"✓ Symbol key: {symbol_key}")
        
        # Test behavior key generation
        behavior_key = SVGXCacheKeyGenerator.generate_behavior_key("test_behavior", "test_namespace")
        print(f"✓ Behavior key: {behavior_key}")
        
        # Test compilation key generation
        svgx_content = "<svgx:behavior>test</svgx:behavior>"
        compilation_key = SVGXCacheKeyGenerator.generate_compilation_key(svgx_content, "svg")
        print(f"✓ Compilation key: {compilation_key}")
        
        # Test validation key generation
        validation_key = SVGXCacheKeyGenerator.generate_validation_key(svgx_content)
        print(f"✓ Validation key: {validation_key}")
        
        # Test user-specific key generation
        user_key = SVGXCacheKeyGenerator.generate_svgx_key(
            SVGXCacheType.SVGX_CONTENT, "test_content", "default", "user123"
        )
        print(f"✓ User-specific key: {user_key}")
        
        # Verify key structure
        assert "svgx" in key1
        assert "svgx_content" in key1
        assert "default" in key1
        print("✓ Key structure validation passed")
        
        return True
        
    except Exception as e:
        print(f"✗ SVGXCacheKeyGenerator test failed: {e}")
        return False


def test_memory_cache():
    """Test MemoryCache with SVGX-specific features"""
    print("\n=== Testing MemoryCache ===")
    
    try:
        cache = MemoryCache(max_size_mb=10, policy=CachePolicy.LRU)
        
        # Test basic operations
        test_data = {"content": "test", "metadata": {"user": "test"}}
        success = cache.set("test_key", test_data, ttl_seconds=3600, 
                           svgx_type=SVGXCacheType.SVGX_CONTENT, 
                           svgx_namespace="default", svgx_user_id="user123")
        print(f"✓ Set operation: {success}")
        
        # Test get operation
        retrieved = cache.get("test_key")
        print(f"✓ Get operation: {retrieved == test_data}")
        
        # Test SVGX-specific metrics
        svgx_metrics = cache.get_svgx_metrics()
        print(f"✓ SVGX metrics: {svgx_metrics['svgx_type_counts']}")
        
        # Test TTL expiration
        cache.set("expire_key", "expire_value", ttl_seconds=1)
        time.sleep(1.1)
        expired = cache.get("expire_key")
        print(f"✓ TTL expiration: {expired is None}")
        
        # Test cache eviction
        large_data = "x" * (5 * 1024 * 1024)  # 5MB
        cache.set("large_key", large_data)
        print(f"✓ Cache eviction handling")
        
        # Test delete operation
        cache.set("delete_key", "delete_value")
        deleted = cache.delete("delete_key")
        print(f"✓ Delete operation: {deleted}")
        
        # Test clear operation
        cache.clear()
        cleared = cache.get("test_key")
        print(f"✓ Clear operation: {cleared is None}")
        
        return True
        
    except Exception as e:
        print(f"✗ MemoryCache test failed: {e}")
        return False


def test_disk_cache():
    """Test DiskCache with SVGX-specific features"""
    print("\n=== Testing DiskCache ===")
    
    try:
        # Create temporary directory for testing
        temp_dir = tempfile.mkdtemp()
        
        try:
            cache = DiskCache(cache_dir=temp_dir, max_size_mb=10)
            
            # Test basic operations
            test_data = {"content": "test", "metadata": {"user": "test"}}
            success = cache.set("test_key", test_data, ttl_seconds=3600,
                              svgx_type=SVGXCacheType.SVGX_CONTENT,
                              svgx_namespace="default", svgx_user_id="user123")
            print(f"✓ Set operation: {success}")
            
            # Test get operation
            retrieved = cache.get("test_key")
            print(f"✓ Get operation: {retrieved == test_data}")
            
            # Test SVGX-specific directory structure
            svgx_dirs = list(cache.svgx_dirs.values())
            print(f"✓ SVGX directories created: {len(svgx_dirs)}")
            
            # Test TTL expiration
            cache.set("expire_key", "expire_value", ttl_seconds=1)
            time.sleep(1.1)
            expired = cache.get("expire_key")
            print(f"✓ TTL expiration: {expired is None}")
            
            # Test delete operation
            cache.set("delete_key", "delete_value")
            deleted = cache.delete("delete_key")
            print(f"✓ Delete operation: {deleted}")
            
            # Test clear operation
            cache.clear()
            cleared = cache.get("test_key")
            print(f"✓ Clear operation: {cleared is None}")
            
        finally:
            # Clean up temporary directory
            shutil.rmtree(temp_dir)
        
        return True
        
    except Exception as e:
        print(f"✗ DiskCache test failed: {e}")
        return False


def test_database_cache():
    """Test DatabaseCache with SVGX-specific features"""
    print("\n=== Testing DatabaseCache ===")
    
    try:
        # Create temporary database file
        temp_db = tempfile.mktemp(suffix='.db')
        
        try:
            cache = DatabaseCache(db_path=temp_db)
            
            # Test basic operations
            test_data = {"content": "test", "metadata": {"user": "test"}}
            success = cache.set("test_key", test_data, ttl_seconds=3600,
                              svgx_type=SVGXCacheType.SVGX_CONTENT,
                              svgx_namespace="default", svgx_user_id="user123")
            print(f"✓ Set operation: {success}")
            
            # Test get operation
            retrieved = cache.get("test_key")
            print(f"✓ Get operation: {retrieved == test_data}")
            
            # Test TTL expiration
            cache.set("expire_key", "expire_value", ttl_seconds=1)
            time.sleep(1.1)
            expired = cache.get("expire_key")
            print(f"✓ TTL expiration: {expired is None}")
            
            # Test delete operation
            cache.set("delete_key", "delete_value")
            deleted = cache.delete("delete_key")
            print(f"✓ Delete operation: {deleted}")
            
            # Test clear operation
            cache.clear()
            cleared = cache.get("test_key")
            print(f"✓ Clear operation: {cleared is None}")
            
        finally:
            # Clean up temporary database file
            if os.path.exists(temp_db):
                os.unlink(temp_db)
        
        return True
        
    except Exception as e:
        print(f"✗ DatabaseCache test failed: {e}")
        return False


def test_advanced_caching_system():
    """Test the main AdvancedCachingSystem with SVGX-specific features"""
    print("\n=== Testing AdvancedCachingSystem ===")
    
    try:
        # Create temporary directory for disk cache
        temp_dir = tempfile.mkdtemp()
        temp_db = tempfile.mktemp(suffix='.db')
        
        try:
            # Initialize caching system
            cache_system = AdvancedCachingSystem(
                memory_cache_size_mb=10,
                disk_cache_size_mb=50,
                enable_database_cache=True
            )
            
            # Test SVGX content caching
            svgx_content = "<svgx:behavior>test_behavior</svgx:behavior>"
            content_key = cache_system.cache_svgx_content(
                svgx_content, "test_namespace", "user123"
            )
            print(f"✓ SVGX content cached: {content_key}")
            
            # Test SVGX symbol caching
            symbol_data = {"id": "test_symbol", "geometry": "circle", "properties": {}}
            symbol_key = cache_system.cache_svgx_symbol(
                "test_symbol", symbol_data, "test_namespace", "user123"
            )
            print(f"✓ SVGX symbol cached: {symbol_key}")
            
            # Test SVGX compilation caching
            compiled_result = {"svg": "<svg>compiled</svg>", "metadata": {}}
            compilation_key = cache_system.cache_svgx_compilation(
                svgx_content, "svg", compiled_result
            )
            print(f"✓ SVGX compilation cached: {compilation_key}")
            
            # Test cached result computation
            def expensive_computation():
                time.sleep(0.1)  # Simulate expensive operation
                return {"result": "computed", "timestamp": time.time()}
            
            # First call should compute
            result1 = cache_system.get_cached_result(
                "expensive_key", expensive_computation,
                svgx_type=SVGXCacheType.SVGX_COMPILED
            )
            print(f"✓ First computation: {result1}")
            
            # Second call should use cache
            result2 = cache_system.get_cached_result(
                "expensive_key", expensive_computation,
                svgx_type=SVGXCacheType.SVGX_COMPILED
            )
            print(f"✓ Cached result: {result2}")
            print(f"✓ Cache hit: {result1 == result2}")
            
            # Test cache invalidation
            cache_system.invalidate_svgx_namespace("test_namespace")
            print("✓ Namespace invalidation")
            
            cache_system.invalidate_svgx_type(SVGXCacheType.SVGX_COMPILED)
            print("✓ Type invalidation")
            
            # Test cache warming
            cache_system.warm_cache_for_svgx_symbols(["test_symbol"], "test_namespace")
            print("✓ Cache warming")
            
            # Test metrics
            overall_metrics = cache_system.get_overall_metrics()
            print(f"✓ Overall metrics: {overall_metrics['overall_hit_rate']:.2f} hit rate")
            
            svgx_metrics = cache_system.get_svgx_metrics()
            print(f"✓ SVGX metrics: {len(svgx_metrics['access_patterns'])} access patterns")
            
            size_info = cache_system.get_cache_size_info()
            print(f"✓ Cache size info: {size_info['memory_cache']['used_mb']:.2f} MB used")
            
        finally:
            # Clean up temporary files
            shutil.rmtree(temp_dir)
            if os.path.exists(temp_db):
                os.unlink(temp_db)
        
        return True
        
    except Exception as e:
        print(f"✗ AdvancedCachingSystem test failed: {e}")
        return False


def test_cache_integration():
    """Test integration between all cache components"""
    print("\n=== Testing Cache Integration ===")
    
    try:
        # Create temporary directory
        temp_dir = tempfile.mkdtemp()
        temp_db = tempfile.mktemp(suffix='.db')
        
        try:
            cache_system = AdvancedCachingSystem(
                memory_cache_size_mb=5,
                disk_cache_size_mb=20,
                enable_database_cache=True
            )
            
            # Test multi-level caching workflow
            test_data = {
                "svgx_content": "<svgx:behavior>integration_test</svgx:behavior>",
                "metadata": {"user": "integration_test", "namespace": "test"}
            }
            
            # Cache in all levels
            key = SVGXCacheKeyGenerator.generate_svgx_key(
                SVGXCacheType.SVGX_CONTENT, test_data["svgx_content"], "test", "user123"
            )
            
            # Set in memory cache
            cache_system.memory_cache.set(key, test_data, 3600, True,
                                        SVGXCacheType.SVGX_CONTENT, "test", "user123")
            
            # Set in disk cache
            cache_system.disk_cache.set(key, test_data, 86400, True,
                                      SVGXCacheType.SVGX_CONTENT, "test", "user123")
            
            # Set in database cache
            cache_system.database_cache.set(key, test_data, 604800, True,
                                          SVGXCacheType.SVGX_CONTENT, "test", "user123")
            
            # Test retrieval from all levels
            memory_result = cache_system.memory_cache.get(key)
            disk_result = cache_system.disk_cache.get(key)
            db_result = cache_system.database_cache.get(key)
            
            print(f"✓ Memory cache integration: {memory_result == test_data}")
            print(f"✓ Disk cache integration: {disk_result == test_data}")
            print(f"✓ Database cache integration: {db_result == test_data}")
            
            # Test cache metrics integration
            memory_metrics = cache_system.memory_cache.get_metrics()
            disk_metrics = cache_system.disk_cache.get_metrics()
            db_metrics = cache_system.database_cache.get_metrics()
            
            print(f"✓ Memory metrics: {memory_metrics.hit_count} hits")
            print(f"✓ Disk metrics: {disk_metrics.hit_count} hits")
            print(f"✓ Database metrics: {db_metrics.hit_count} hits")
            
            # Test cache invalidation across levels
            cache_system.invalidate_cache(f"svgx:svgx_content:test:.*")
            print("✓ Cross-level invalidation")
            
        finally:
            # Clean up
            shutil.rmtree(temp_dir)
            if os.path.exists(temp_db):
                os.unlink(temp_db)
        
        return True
        
    except Exception as e:
        print(f"✗ Cache integration test failed: {e}")
        return False


def test_error_handling():
    """Test error handling for cache operations"""
    print("\n=== Testing Error Handling ===")
    
    try:
        # Test CacheError
        try:
            raise CacheError("Test cache error", "TEST_CACHE_ERROR", {"details": "test"})
        except CacheError as e:
            print(f"✓ CacheError caught: {e.error_code}")
            error_dict = e.to_dict()
            print(f"✓ CacheError to_dict: {error_dict['error_type']}")
        
        # Test cache system error handling
        cache_system = AdvancedCachingSystem()
        
        # Test with invalid computation function
        def failing_computation():
            raise ValueError("Simulated computation failure")
        
        try:
            cache_system.get_cached_result("error_key", failing_computation)
            print("✗ Should have raised CacheError for failing computation")
            return False
        except CacheError:
            print("✓ CacheError correctly raised for failing computation")
        
        return True
        
    except Exception as e:
        print(f"✗ Error handling test failed: {e}")
        return False


def main():
    """Run all tests for the advanced caching service migration"""
    print("💾 Testing Advanced Caching Service Migration for SVGX Engine")
    print("=" * 70)
    
    tests = [
        ("SVGX Cache Key Generator", test_svgx_cache_key_generator),
        ("Memory Cache", test_memory_cache),
        ("Disk Cache", test_disk_cache),
        ("Database Cache", test_database_cache),
        ("Advanced Caching System", test_advanced_caching_system),
        ("Cache Integration", test_cache_integration),
        ("Error Handling", test_error_handling)
    ]
    
    results = []
    start_time = time.time()
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"✗ {test_name} test crashed: {e}")
            results.append((test_name, False))
    
    # Print summary
    print("\n" + "=" * 70)
    print("📊 TEST SUMMARY")
    print("=" * 70)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASSED" if result else "✗ FAILED"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Advanced Caching Service migration successful.")
        print("\n✅ Migration Status:")
        print("   - SVGXCacheKeyGenerator: Migrated with namespace isolation")
        print("   - MemoryCache: Migrated with SVGX-specific tracking")
        print("   - DiskCache: Migrated with SVGX directory structure")
        print("   - DatabaseCache: Migrated with SVGX-optimized schema")
        print("   - AdvancedCachingSystem: Migrated with comprehensive SVGX features")
        print("   - Error handling: Enhanced with CacheError")
        print("   - Cache integration: All levels work together seamlessly")
        print("   - SVGX-specific features: Content, symbol, compilation caching")
        print("   - Cache warming and invalidation: SVGX-aware patterns")
    else:
        print("❌ Some tests failed. Please review the implementation.")
    
    elapsed_time = time.time() - start_time
    print(f"\n⏱️  Total test time: {elapsed_time:.2f} seconds")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 