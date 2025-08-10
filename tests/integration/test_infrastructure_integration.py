"""
Integration tests for Infrastructure Layer Integration.

Tests integration between domain/application layers and infrastructure
services including database, caching, logging, and external services.
"""

import pytest
from typing import Dict, Any, List
from datetime import datetime, timedelta
import json
import time
from unittest.mock import patch, Mock

from tests.framework.test_base import IntegrationTestCase
from application.services.building_service import BuildingApplicationService
from domain.entities import Building
from domain.value_objects import BuildingStatus
from infrastructure.database.query_optimization import DatabaseOptimizer
from infrastructure.database.optimized_repository_factory import OptimizedRepositoryFactory
from infrastructure.services.cache_service import RedisCacheService
from infrastructure.error_handling import InfrastructureError
from infrastructure.logging.structured_logging import get_logger, log_context, performance_logger


logger = get_logger(__name__)


class TestInfrastructureIntegration(IntegrationTestCase):
    """Integration tests for infrastructure layer components."""
    
    def setUp(self) -> None:
        """Set up infrastructure integration tests."""
        super().setUp()
        
        # Initialize infrastructure services
        self.cache_service = RedisCacheService() if self.config.cache_enabled else None
        self.building_service = BuildingApplicationService(
            unit_of_work=self.unit_of_work,
            cache_service=self.cache_service
        )
        
        # Initialize database optimizer for testing
        self.db_optimizer = DatabaseOptimizer(self.engine)
    
    def test_database_optimization_integration(self) -> None:
        """Test database optimization features with real queries."""
        # Clear any existing metrics
        self.db_optimizer.query_metrics.clear()
        
        # Perform various database operations
        hierarchy = self.create_test_building_hierarchy()
        building_id = str(hierarchy["building"].id)
        
        # Simple query
        building_response = self.building_service.get_building(building_id)
        self.assertTrue(building_response.success)
        
        # More complex query - list with filtering
        list_response = self.building_service.list_buildings()
        self.assertTrue(list_response.success)
        
        # Search query
        search_response = self.building_service.search_buildings_by_address("Test")
        self.assertTrue(search_response.success)
        
        # Check that query metrics were collected
        metrics = self.db_optimizer.query_metrics
        self.assertGreater(len(metrics), 0, "No query metrics were collected")
        
        # Verify performance report generation
        performance_report = self.db_optimizer.get_performance_report()
        self.assertIn("total_queries", performance_report)
        self.assertIn("complexity_breakdown", performance_report)
        self.assertGreater(performance_report["total_queries"], 0)
        
        logger.info("Database optimization integration test completed", extra={
            "queries_analyzed": len(metrics),
            "performance_report": performance_report
        })
    
    def test_caching_integration_with_database(self) -> None:
        """Test caching integration with database operations."""
        if not self.cache_service:
            self.skipTest("Cache service not available")
        
        # Create test building
        create_response = self.building_service.create_building(
            name="Cache Integration Building",
            address=self.test_data.create_test_address().__dict__,
            created_by="cache_integration_user"
        )
        self.assertTrue(create_response.success)
        building_id = create_response.building_id
        
        # First retrieval - should hit database and populate cache
        start_time = time.time()
        first_retrieval = self.building_service.get_building(building_id)
        first_duration = time.time() - start_time
        self.assertTrue(first_retrieval.success)
        
        # Second retrieval - should hit cache (faster)
        start_time = time.time()
        second_retrieval = self.building_service.get_building(building_id)
        second_duration = time.time() - start_time
        self.assertTrue(second_retrieval.success)
        
        # Verify data consistency
        self.assertEqual(first_retrieval.building, second_retrieval.building)
        
        # Cache hit should generally be faster (though this may vary in test environment)
        logger.info("Cache timing comparison", extra={
            "first_retrieval_ms": round(first_duration * 1000, 2),
            "second_retrieval_ms": round(second_duration * 1000, 2),
            "cache_improvement": round(((first_duration - second_duration) / first_duration) * 100, 1) if first_duration > 0 else 0
        })
        
        # Update building - should invalidate cache
        update_response = self.building_service.update_building_name(
            building_id=building_id,
            new_name="Updated Cache Building",
            updated_by="cache_integration_user"
        )
        self.assertTrue(update_response.success)
        
        # Next retrieval should reflect the update
        updated_retrieval = self.building_service.get_building(building_id)
        self.assertTrue(updated_retrieval.success)
        self.assertEqual(updated_retrieval.building["name"], "Updated Cache Building")
        self.assertNotEqual(updated_retrieval.building["name"], first_retrieval.building["name"])
    
    def test_error_handling_integration(self) -> None:
        """Test error handling integration across layers."""
        # Test domain validation errors
        domain_error_response = self.building_service.create_building(
            name="",  # Invalid empty name
            address=self.test_data.create_test_address().__dict__,
            created_by="error_test_user"
        )
        self.assertFalse(domain_error_response.success)
        self.assertIn("name cannot be empty", domain_error_response.message.lower())
        
        # Test infrastructure errors (simulated database failure)
        with patch.object(self.building_repository, 'save', side_effect=Exception("Database connection failed")):
            infra_error_response = self.building_service.create_building(
                name="Infrastructure Error Building",
                address=self.test_data.create_test_address().__dict__,
                created_by="error_test_user"
            )
            self.assertFalse(infra_error_response.success)
            self.assertIn("database connection failed", infra_error_response.message.lower())
        
        # Test not found scenarios
        not_found_response = self.building_service.get_building("non-existent-id")
        self.assertFalse(not_found_response.success)
        self.assertIn("not found", not_found_response.message.lower())
    
    def test_logging_integration(self) -> None:
        """Test structured logging integration across operations."""
        with log_context(
            operation="logging_integration_test",
            user_id="test_user",
            component="integration_test"
        ):
            # Create building with logging context
            create_response = self.building_service.create_building(
                name="Logging Integration Building",
                address=self.test_data.create_test_address().__dict__,
                created_by="logging_test_user"
            )
            self.assertTrue(create_response.success)
            building_id = create_response.building_id
            
            # Perform operations that should generate various log events
            get_response = self.building_service.get_building(building_id)
            update_response = self.building_service.update_building_name(
                building_id=building_id,
                new_name="Updated Logging Building",
                updated_by="logging_test_user"
            )
            
            # Test performance logging
            performance_logger.log_database_query(
                query_type="integration_test",
                table="buildings",
                duration=0.123,
                success=True
            )
            
            performance_logger.log_cache_operation(
                operation="get",
                key="test_key",
                hit=True,
                duration=0.001
            )
            
            # Verify operations completed successfully (logging is tested via observation)
            self.assertTrue(get_response.success)
            self.assertTrue(update_response.success)
    
    def test_repository_factory_integration(self) -> None:
        """Test optimized repository factory integration."""
        # Test repository creation through factory
        if hasattr(self, 'repository_factory'):
            building_repo = self.repository_factory.get_building_repository()
            self.assertIsNotNone(building_repo)
            
            # Test repository caching
            building_repo2 = self.repository_factory.get_building_repository()
            # Should return same cached instance (if using factory pattern)
            
            # Test performance report generation
            performance_report = self.repository_factory.get_performance_report()
            self.assertIsInstance(performance_report, dict)
            self.assertIn("timestamp", performance_report)
    
    def test_transaction_integration(self) -> None:
        """Test transaction handling across service boundaries."""
        # Test successful transaction
        with self.unit_of_work:
            building = self.test_data.create_test_building()
            saved_building = self.building_repository.save(building)
            self.unit_of_work.commit()
        
        # Verify building was saved
        retrieved_building = self.building_repository.get_by_id(saved_building.id)
        self.assertIsNotNone(retrieved_building)
        self.assertEqual(retrieved_building.name, building.name)
        
        # Test transaction rollback
        initial_count = len(self.building_repository.get_all())
        
        try:
            with self.unit_of_work:
                # Create building
                rollback_building = self.test_data.create_test_building(name="Rollback Building")
                self.building_repository.save(rollback_building)
                
                # Simulate error to trigger rollback
                raise Exception("Simulated transaction error")
                
        except Exception as e:
            # Expected exception
            self.assertEqual(str(e), "Simulated transaction error")
        
        # Verify rollback occurred - building should not be saved
        final_count = len(self.building_repository.get_all())
        self.assertEqual(initial_count, final_count)
    
    def test_bulk_operations_integration(self) -> None:
        """Test bulk operations with infrastructure optimization."""
        # Create multiple buildings for bulk testing
        bulk_data = []
        for i in range(20):
            building_data = {
                "name": f"Bulk Integration Building {i:02d}",
                "address": {
                    "street": f"{i*10} Bulk Street",
                    "city": "Bulk City",
                    "state": "BK",
                    "postal_code": f"{i:05d}"
                },
                "created_by": "bulk_integration_user"
            }
            bulk_data.append(building_data)
        
        # Measure bulk creation performance
        start_time = time.time()
        created_ids = []
        
        for building_data in bulk_data:
            response = self.building_service.create_building(**building_data)
            if response.success:
                created_ids.append(response.building_id)
        
        creation_time = time.time() - start_time
        
        # Verify all buildings were created
        self.assertEqual(len(created_ids), 20)
        
        # Measure bulk retrieval performance
        retrieval_start = time.time()
        retrieved_buildings = []
        
        for building_id in created_ids:
            response = self.building_service.get_building(building_id)
            if response.success:
                retrieved_buildings.append(response.building)
        
        retrieval_time = time.time() - retrieval_start
        
        # Verify all buildings were retrieved
        self.assertEqual(len(retrieved_buildings), 20)
        
        # Performance logging
        logger.info("Bulk operations performance", extra={
            "buildings_created": len(created_ids),
            "creation_time_seconds": round(creation_time, 2),
            "retrieval_time_seconds": round(retrieval_time, 2),
            "avg_creation_time_ms": round((creation_time / len(created_ids)) * 1000, 2) if created_ids else 0,
            "avg_retrieval_time_ms": round((retrieval_time / len(retrieved_buildings)) * 1000, 2) if retrieved_buildings else 0
        })
        
        # Performance assertions
        avg_creation_time = creation_time / len(created_ids) if created_ids else float('inf')
        avg_retrieval_time = retrieval_time / len(retrieved_buildings) if retrieved_buildings else float('inf')
        
        self.assertLess(avg_creation_time, 0.5, "Average creation time too slow")
        self.assertLess(avg_retrieval_time, 0.1, "Average retrieval time too slow")
        
        # Cleanup
        for building_id in created_ids:
            self.building_service.delete_building(building_id)
    
    def test_connection_pool_integration(self) -> None:
        """Test database connection pool behavior under load."""
        import threading
        import concurrent.futures
        
        def create_and_retrieve_building(thread_id: int) -> Dict[str, Any]:
            """Create and retrieve a building in a separate thread."""
            try:
                # Create building
                create_response = self.building_service.create_building(
                    name=f"Pool Test Building {thread_id}",
                    address={
                        "street": f"{thread_id} Pool Street",
                        "city": "Pool City",
                        "state": "PL",
                        "postal_code": f"{thread_id:05d}"
                    },
                    created_by=f"pool_test_user_{thread_id}"
                )
                
                if not create_response.success:
                    return {"success": False, "error": create_response.message}
                
                building_id = create_response.building_id
                
                # Retrieve building
                get_response = self.building_service.get_building(building_id)
                
                if not get_response.success:
                    return {"success": False, "error": get_response.message}
                
                # Clean up
                delete_response = self.building_service.delete_building(building_id)
                
                return {
                    "success": True,
                    "thread_id": thread_id,
                    "building_id": building_id,
                    "cleanup_success": delete_response.success
                }
                
            except Exception as e:
                return {"success": False, "thread_id": thread_id, "error": str(e)}
        
        # Test concurrent database access
        num_threads = 10
        
        start_time = time.time()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(create_and_retrieve_building, i) for i in range(num_threads)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        execution_time = time.time() - start_time
        
        # Analyze results
        successful_operations = [r for r in results if r.get("success", False)]
        failed_operations = [r for r in results if not r.get("success", False)]
        
        self.assertEqual(len(successful_operations), num_threads, 
                        f"Expected all {num_threads} operations to succeed, but {len(failed_operations)} failed")
        
        # Log performance metrics
        logger.info("Connection pool stress test completed", extra={
            "concurrent_threads": num_threads,
            "successful_operations": len(successful_operations),
            "failed_operations": len(failed_operations),
            "total_execution_time_seconds": round(execution_time, 2),
            "average_operation_time_ms": round((execution_time / num_threads) * 1000, 2)
        })
        
        if failed_operations:
            logger.warning("Some operations failed during connection pool test", extra={
                "failed_operations": failed_operations
            })
    
    def test_health_monitoring_integration(self) -> None:
        """Test health monitoring integration."""
        # Test database health check
        from infrastructure.database.query_optimization import DatabaseHealthChecker
        
        health_checker = DatabaseHealthChecker(self.engine)
        health_report = health_checker.check_database_health()
        
        self.assertIn("database", health_report)
        self.assertIn("connection_pool", health_report)
        
        # Database should be healthy in test environment
        self.assertEqual(health_report["database"], "healthy")
        
        # Test service health checks
        building_health = self.building_service.health_check()
        self.assertIsInstance(building_health, dict)
        self.assertIn("status", building_health)
        
        logger.info("Health monitoring test completed", extra={
            "database_health": health_report,
            "service_health": building_health
        })


if __name__ == '__main__':
    import unittest
    unittest.main()