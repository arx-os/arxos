#!/usr/bin/env python3
"""
Integration Test for MCP Service

This script tests the complete MCP service integration including:
- WebSocket connections
- Redis caching
- Authentication
- Performance monitoring
- Rule engine validation
"""

import asyncio
import json
import time
import logging
from typing import Dict, Any
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MCPIntegrationTest:
    """Integration test for MCP service components"""
    
    def __init__(self):
        self.test_results = {}
        self.start_time = time.time()
    
    async def test_redis_connection(self):
        """Test Redis connection and basic operations"""
        logger.info("🔍 Testing Redis Connection...")
        
        try:
            from cache.redis_manager import redis_manager
            
            # Test health check
            health = await redis_manager.health_check()
            assert health["status"] == "healthy", f"Redis health check failed: {health}"
            
            # Test basic operations
            test_key = "integration_test"
            test_data = {"test": "data", "timestamp": datetime.now().isoformat()}
            
            # Test cache set
            success = await redis_manager.cache_validation(test_key, test_data)
            assert success, "Failed to cache validation data"
            
            # Test cache get
            cached_data = await redis_manager.get_cached_validation(test_key)
            assert cached_data == test_data, "Cached data mismatch"
            
            # Test cache invalidation
            success = await redis_manager.invalidate_cache(test_key)
            assert success, "Failed to invalidate cache"
            
            # Test cache miss
            cached_data = await redis_manager.get_cached_validation(test_key)
            assert cached_data is None, "Cache should be empty after invalidation"
            
            # Test performance metrics
            metrics = await redis_manager.get_performance_metrics()
            assert "connected_clients" in metrics, "Missing Redis metrics"
            
            self.test_results["redis"] = "✅ PASSED"
            logger.info("✅ Redis Connection Test PASSED")
            
        except Exception as e:
            self.test_results["redis"] = f"❌ FAILED: {str(e)}"
            logger.error(f"❌ Redis Connection Test FAILED: {e}")
    
    async def test_authentication(self):
        """Test authentication system"""
        logger.info("🔍 Testing Authentication System...")
        
        try:
            from auth.authentication import auth_manager, UserRole, Permission
            
            # Test user authentication
            user = auth_manager.authenticate_user("admin", "admin123")
            assert user is not None, "Admin authentication failed"
            assert user.username == "admin", "Wrong user returned"
            
            # Test invalid credentials
            user = auth_manager.authenticate_user("admin", "wrong_password")
            assert user is None, "Invalid credentials should return None"
            
            # Test token creation
            token_data = {
                "sub": user.user_id,
                "username": user.username,
                "roles": [role.value for role in user.roles],
                "permissions": [perm.value for perm in user.permissions]
            }
            
            access_token = auth_manager.create_access_token(token_data)
            assert access_token is not None, "Failed to create access token"
            
            # Test token verification
            from auth.authentication import TokenData
            token_info = auth_manager.verify_token(access_token)
            assert token_info.user_id == user.user_id, "Token verification failed"
            
            # Test permissions
            has_permission = auth_manager.has_permission(user, Permission.READ_VALIDATION)
            assert has_permission, "Admin should have READ_VALIDATION permission"
            
            # Test role checking
            has_role = auth_manager.has_role(user, UserRole.ADMIN)
            assert has_role, "User should have ADMIN role"
            
            self.test_results["authentication"] = "✅ PASSED"
            logger.info("✅ Authentication System Test PASSED")
            
        except Exception as e:
            self.test_results["authentication"] = f"❌ FAILED: {str(e)}"
            logger.error(f"❌ Authentication System Test FAILED: {e}")
    
    async def test_websocket_manager(self):
        """Test WebSocket manager"""
        logger.info("🔍 Testing WebSocket Manager...")
        
        try:
            from websocket.websocket_manager import websocket_manager
            
            # Test connection stats
            stats = websocket_manager.get_connection_stats()
            assert "total_connections" in stats, "Missing connection stats"
            assert stats["total_connections"] == 0, "Should start with 0 connections"
            
            # Test building connections
            connections = websocket_manager.get_building_connections("test_building")
            assert connections == 0, "Should start with 0 building connections"
            
            self.test_results["websocket_manager"] = "✅ PASSED"
            logger.info("✅ WebSocket Manager Test PASSED")
            
        except Exception as e:
            self.test_results["websocket_manager"] = f"❌ FAILED: {str(e)}"
            logger.error(f"❌ WebSocket Manager Test FAILED: {e}")
    
    async def test_metrics_collector(self):
        """Test metrics collector"""
        logger.info("🔍 Testing Metrics Collector...")
        
        try:
            from monitoring.prometheus_metrics import metrics_collector, ValidationMetrics
            
            # Test metrics recording
            metrics = ValidationMetrics(
                building_id="test_building",
                jurisdiction="US",
                total_rules=100,
                passed_rules=95,
                failed_rules=5,
                violations_count=5,
                warnings_count=2,
                duration_seconds=1.5,
                cache_hit=False
            )
            
            metrics_collector.record_validation(metrics)
            
            # Test API request metrics
            metrics_collector.record_api_request("POST", "/api/v1/validate", 200, 0.5)
            
            # Test error metrics
            metrics_collector.record_error("test_error", "test_component")
            
            # Test metrics summary
            summary = metrics_collector.get_metrics_summary()
            assert "total_validation_requests" in summary, "Missing metrics summary"
            
            self.test_results["metrics_collector"] = "✅ PASSED"
            logger.info("✅ Metrics Collector Test PASSED")
            
        except Exception as e:
            self.test_results["metrics_collector"] = f"❌ FAILED: {str(e)}"
            logger.error(f"❌ Metrics Collector Test FAILED: {e}")
    
    async def test_rule_engine_integration(self):
        """Test rule engine with new components"""
        logger.info("🔍 Testing Rule Engine Integration...")
        
        try:
            from validate.rule_engine import MCPRuleEngine
            from models.mcp_models import BuildingModel, BuildingObject
            
            # Create test building model
            building_model = BuildingModel(
                building_id="test_building_001",
                building_name="Test Building",
                objects=[
                    BuildingObject(
                        object_id="panel_main",
                        object_type="electrical_panel",
                        properties={
                            "voltage": 120,
                            "amperage": 200,
                            "circuit_count": 20
                        }
                    ),
                    BuildingObject(
                        object_id="outlet_bathroom_1",
                        object_type="electrical_outlet",
                        properties={
                            "voltage": 120,
                            "amperage": 15,
                            "location": "bathroom"
                        }
                    )
                ],
                metadata={
                    "location": {
                        "country": "US",
                        "state": "CA",
                        "city": "San Francisco"
                    }
                }
            )
            
            # Initialize rule engine
            rule_engine = MCPRuleEngine()
            
            # Test jurisdiction matching
            jurisdiction_info = rule_engine.get_jurisdiction_info(building_model)
            assert "location_found" in jurisdiction_info, "Missing jurisdiction info"
            assert jurisdiction_info["location_found"] == True, "Location should be found"
            
            # Test validation (with auto-detection)
            validation_report = rule_engine.validate_building_model(building_model)
            assert validation_report is not None, "Validation report should not be None"
            assert hasattr(validation_report, 'total_rules'), "Missing total_rules"
            assert hasattr(validation_report, 'total_violations'), "Missing total_violations"
            
            self.test_results["rule_engine_integration"] = "✅ PASSED"
            logger.info("✅ Rule Engine Integration Test PASSED")
            
        except Exception as e:
            self.test_results["rule_engine_integration"] = f"❌ FAILED: {str(e)}"
            logger.error(f"❌ Rule Engine Integration Test FAILED: {e}")
    
    async def test_cache_integration(self):
        """Test cache integration with rule engine"""
        logger.info("🔍 Testing Cache Integration...")
        
        try:
            from cache.redis_manager import redis_manager
            from models.mcp_models import BuildingModel, BuildingObject
            
            # Create test building model
            building_model = BuildingModel(
                building_id="cache_test_building",
                building_name="Cache Test Building",
                objects=[],
                metadata={}
            )
            
            # Test caching building model
            success = await redis_manager.cache_building_model(
                building_model.building_id,
                building_model.dict()
            )
            assert success, "Failed to cache building model"
            
            # Test retrieving cached building model
            cached_model = await redis_manager.get_cached_building_model(building_model.building_id)
            assert cached_model is not None, "Failed to retrieve cached building model"
            assert cached_model["building_id"] == building_model.building_id, "Cached model mismatch"
            
            # Test cache invalidation
            success = await redis_manager.invalidate_cache(building_model.building_id, "building_model")
            assert success, "Failed to invalidate building model cache"
            
            # Test cache miss after invalidation
            cached_model = await redis_manager.get_cached_building_model(building_model.building_id)
            assert cached_model is None, "Cache should be empty after invalidation"
            
            self.test_results["cache_integration"] = "✅ PASSED"
            logger.info("✅ Cache Integration Test PASSED")
            
        except Exception as e:
            self.test_results["cache_integration"] = f"❌ FAILED: {str(e)}"
            logger.error(f"❌ Cache Integration Test FAILED: {e}")
    
    async def test_performance_monitoring(self):
        """Test performance monitoring integration"""
        logger.info("🔍 Testing Performance Monitoring...")
        
        try:
            from monitoring.prometheus_metrics import metrics_collector
            from cache.redis_manager import redis_manager
            
            # Test Redis performance metrics
            redis_metrics = await redis_manager.get_performance_metrics()
            assert "connected_clients" in redis_metrics, "Missing Redis metrics"
            assert "hit_ratio_percent" in redis_metrics, "Missing cache hit ratio"
            
            # Test cache statistics
            cache_stats = await redis_manager.get_cache_stats()
            assert "total_keys" in cache_stats, "Missing cache stats"
            
            # Test metrics collector
            summary = metrics_collector.get_metrics_summary()
            assert "system_uptime_seconds" in summary, "Missing system metrics"
            
            # Test memory usage tracking
            metrics_collector.update_memory_usage("test_component", 1024 * 1024)  # 1MB
            
            # Test active users tracking
            metrics_collector.update_active_users("admin", 5)
            
            self.test_results["performance_monitoring"] = "✅ PASSED"
            logger.info("✅ Performance Monitoring Test PASSED")
            
        except Exception as e:
            self.test_results["performance_monitoring"] = f"❌ FAILED: {str(e)}"
            logger.error(f"❌ Performance Monitoring Test FAILED: {e}")
    
    async def run_all_tests(self):
        """Run all integration tests"""
        logger.info("🚀 Starting MCP Service Integration Tests...")
        logger.info("=" * 60)
        
        # Run all tests
        await self.test_redis_connection()
        await self.test_authentication()
        await self.test_websocket_manager()
        await self.test_metrics_collector()
        await self.test_rule_engine_integration()
        await self.test_cache_integration()
        await self.test_performance_monitoring()
        
        # Calculate test duration
        duration = time.time() - self.start_time
        
        # Print results
        logger.info("=" * 60)
        logger.info("📊 INTEGRATION TEST RESULTS")
        logger.info("=" * 60)
        
        passed = 0
        failed = 0
        
        for test_name, result in self.test_results.items():
            logger.info(f"{test_name}: {result}")
            if "PASSED" in result:
                passed += 1
            else:
                failed += 1
        
        logger.info("=" * 60)
        logger.info(f"✅ PASSED: {passed}")
        logger.info(f"❌ FAILED: {failed}")
        logger.info(f"⏱️  Duration: {duration:.2f} seconds")
        logger.info("=" * 60)
        
        if failed == 0:
            logger.info("🎉 ALL TESTS PASSED! MCP Service is ready for production.")
        else:
            logger.error(f"⚠️  {failed} test(s) failed. Please check the logs above.")
        
        return failed == 0


async def main():
    """Main test runner"""
    test_runner = MCPIntegrationTest()
    success = await test_runner.run_all_tests()
    
    if success:
        print("\n🎉 Integration tests completed successfully!")
        print("🚀 MCP Service is ready for deployment!")
    else:
        print("\n❌ Some integration tests failed.")
        print("🔧 Please fix the issues before deployment.")
    
    return success


if __name__ == "__main__":
    asyncio.run(main()) 