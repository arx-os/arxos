"""
Comprehensive Stress and Performance Testing for Arxos Platform

Tests cover:
- Load testing with high concurrency
- Memory usage monitoring
- Database performance under stress
- Scalability testing
- Performance benchmarking
- Resource utilization testing
"""

import pytest
import json
import tempfile
import shutil
import asyncio
import concurrent.futures
import threading
import time
import random
import string
import psutil
import gc
import os
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock, AsyncMock
from typing import Dict, List, Any

# Import all services
from arx_svg_parser.services.version_control import VersionControlService
from arx_svg_parser.services.route_manager import RouteManager
from arx_svg_parser.services.floor_manager import FloorManager
from arx_svg_parser.services.auto_snapshot import AutoSnapshotService
from arx_svg_parser.services.realtime_service import RealTimeService as RealtimeService
from arx_svg_parser.services.cache_service import CacheService
from arx_svg_parser.services.data_partitioning import DataPartitioningService
from arx_svg_parser.services.access_control import AccessControlService


class TestLoadTesting:
    """Load testing with high concurrency"""
    
    @pytest.fixture
    def vc_service(self):
        """Create version control service for load testing"""
        temp_dir = tempfile.mkdtemp()
        db_path = Path(temp_dir) / "test_load.db"
        storage_path = Path(temp_dir) / "versions"
        service = VersionControlService(str(db_path), str(storage_path))
        yield service
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def floor_manager(self):
        """Create floor manager for load testing"""
        return FloorManager()
    
    def test_high_concurrency_version_creation(self, vc_service):
        """Test high concurrency version creation"""
        
        # Create initial version
        initial_floor = {"floor_id": "load-floor", "building_id": "load-building", "objects": []}
        current_version = vc_service.create_version(
            initial_floor,
            "load-floor",
            "load-building",
            "main",
            "Initial version",
            "architect"
        )
        
        # Test with different concurrency levels
        concurrency_levels = [10, 50, 100, 200]
        results = {}
        
        for concurrency in concurrency_levels:
            print(f"\nTesting with {concurrency} concurrent operations...")
            
            start_time = time.time()
            start_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
            
            def create_version(version_id):
                try:
                    modified_floor = initial_floor.copy()
                    modified_floor["objects"].append({
                        "id": f"obj-{version_id}",
                        "type": "device",
                        "x": version_id,
                        "y": version_id
                    })
                    
                    return vc_service.create_version(
                        modified_floor,
                        "load-floor",
                        "load-building",
                        "main",
                        f"Version {version_id}",
                        f"user-{version_id % 10}"
                    )
                except Exception as e:
                    return {"success": False, "error": str(e)}
            
            # Execute concurrent operations
            with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as executor:
                futures = [executor.submit(create_version, i) for i in range(concurrency)]
                operation_results = [future.result() for future in futures]
            
            end_time = time.time()
            end_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
            
            total_time = end_time - start_time
            memory_used = end_memory - start_memory
            successful_operations = sum(1 for r in operation_results if r["success"])
            
            results[concurrency] = {
                "total_time": total_time,
                "memory_used_mb": memory_used,
                "successful_operations": successful_operations,
                "success_rate": successful_operations / concurrency,
                "operations_per_second": concurrency / total_time
            }
            
            print(f"  Time: {total_time:.2f}s")
            print(f"  Memory: {memory_used:.2f}MB")
            print(f"  Success Rate: {successful_operations/concurrency*100:.1f}%")
            print(f"  Ops/sec: {concurrency/total_time:.2f}")
        
        # Verify performance requirements
        for concurrency, result in results.items():
            assert result["success_rate"] >= 0.95  # 95% success rate
            assert result["operations_per_second"] >= 10  # At least 10 ops/sec
            assert result["memory_used_mb"] < 1000  # Less than 1GB memory increase
    
    def test_concurrent_branch_operations_load(self, vc_service):
        """Test load with concurrent branch operations"""
        
        # Create initial version
        initial_floor = {"floor_id": "branch-load-floor", "building_id": "branch-load-building", "objects": []}
        initial_version = vc_service.create_version(
            initial_floor,
            "branch-load-floor",
            "branch-load-building",
            "main",
            "Initial version",
            "architect"
        )
        
        # Test concurrent branch creation and operations
        def branch_operation(operation_id):
            try:
                # Create branch
                branch_name = f"load-branch-{operation_id}"
                branch_result = vc_service.create_branch(
                    branch_name,
                    "branch-load-floor",
                    "branch-load-building",
                    initial_version["version_id"],
                    f"user-{operation_id}",
                    f"Load test branch {operation_id}"
                )
                
                if not branch_result["success"]:
                    return {"operation_id": operation_id, "success": False, "stage": "branch_creation"}
                
                # Create version in branch
                modified_floor = initial_floor.copy()
                modified_floor["objects"].append({
                    "id": f"obj-{operation_id}",
                    "type": "device",
                    "x": operation_id,
                    "y": operation_id
                })
                
                version_result = vc_service.create_version(
                    modified_floor,
                    "branch-load-floor",
                    "branch-load-building",
                    branch_name,
                    f"Version {operation_id}",
                    f"user-{operation_id}"
                )
                
                if not version_result["success"]:
                    return {"operation_id": operation_id, "success": False, "stage": "version_creation"}
                
                # Create merge request
                merge_result = vc_service.create_merge_request(
                    version_result["version_id"],
                    initial_version["version_id"],
                    f"user-{operation_id}",
                    f"Merge request {operation_id}"
                )
                
                return {
                    "operation_id": operation_id,
                    "success": merge_result["success"],
                    "branch_id": branch_result["branch_name"],
                    "version_id": version_result["version_id"],
                    "merge_request_id": merge_result.get("merge_request_id")
                }
                
            except Exception as e:
                return {"operation_id": operation_id, "success": False, "error": str(e)}
        
        # Test with different load levels
        load_levels = [20, 50, 100]
        load_results = {}
        
        for load in load_levels:
            print(f"\nTesting branch operations with {load} concurrent operations...")
            
            start_time = time.time()
            start_memory = psutil.Process().memory_info().rss / 1024 / 1024
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=load) as executor:
                futures = [executor.submit(branch_operation, i) for i in range(load)]
                results = [future.result() for future in futures]
            
            end_time = time.time()
            end_memory = psutil.Process().memory_info().rss / 1024 / 1024
            
            total_time = end_time - start_time
            memory_used = end_memory - start_memory
            successful_operations = sum(1 for r in results if r["success"])
            
            load_results[load] = {
                "total_time": total_time,
                "memory_used_mb": memory_used,
                "successful_operations": successful_operations,
                "success_rate": successful_operations / load,
                "operations_per_second": load / total_time
            }
            
            print(f"  Time: {total_time:.2f}s")
            print(f"  Memory: {memory_used:.2f}MB")
            print(f"  Success Rate: {successful_operations/load*100:.1f}%")
            print(f"  Ops/sec: {load/total_time:.2f}")
        
        # Verify performance
        for load, result in load_results.items():
            assert result["success_rate"] >= 0.90  # 90% success rate for complex operations
            assert result["operations_per_second"] >= 5  # At least 5 ops/sec
            assert result["memory_used_mb"] < 500  # Less than 500MB memory increase
    
    def test_database_connection_pool_stress(self, vc_service):
        """Test database connection pool under stress"""
        
        # Simulate database connection stress
        def database_stress_operation(operation_id):
            try:
                # Multiple database operations
                operations = []
                
                # Create version
                floor_data = {
                    "floor_id": f"db-stress-{operation_id}",
                    "building_id": "db-stress-building",
                    "objects": [{"id": f"obj-{operation_id}", "type": "device", "x": operation_id, "y": operation_id}],
                    "metadata": {"name": f"DB Stress {operation_id}"}
                }
                
                create_result = vc_service.create_version(
                    floor_data,
                    f"db-stress-{operation_id}",
                    "db-stress-building",
                    "main",
                    f"DB stress version {operation_id}",
                    f"user-{operation_id}"
                )
                
                if create_result["success"]:
                    operations.append("create")
                    
                    # Retrieve version
                    retrieve_result = vc_service.get_version_data(create_result["version_id"])
                    if retrieve_result["success"]:
                        operations.append("retrieve")
                    
                    # Get history
                    history_result = vc_service.get_version_history(f"db-stress-{operation_id}", "db-stress-building")
                    if history_result["success"]:
                        operations.append("history")
                    
                    # Create branch
                    branch_result = vc_service.create_branch(
                        f"stress-branch-{operation_id}",
                        f"db-stress-{operation_id}",
                        "db-stress-building",
                        create_result["version_id"],
                        f"user-{operation_id}",
                        f"Stress branch {operation_id}"
                    )
                    
                    if branch_result["success"]:
                        operations.append("branch")
                
                return {
                    "operation_id": operation_id,
                    "success": len(operations) >= 2,  # At least 2 operations successful
                    "operations": operations
                }
                
            except Exception as e:
                return {"operation_id": operation_id, "success": False, "error": str(e)}
        
        # Test with high concurrency
        concurrency = 200
        print(f"\nTesting database connection pool with {concurrency} concurrent operations...")
        
        start_time = time.time()
        start_memory = psutil.Process().memory_info().rss / 1024 / 1024
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as executor:
            futures = [executor.submit(database_stress_operation, i) for i in range(concurrency)]
            results = [future.result() for future in futures]
        
        end_time = time.time()
        end_memory = psutil.Process().memory_info().rss / 1024 / 1024
        
        total_time = end_time - start_time
        memory_used = end_memory - start_memory
        successful_operations = sum(1 for r in results if r["success"])
        
        print(f"  Total Time: {total_time:.2f}s")
        print(f"  Memory Used: {memory_used:.2f}MB")
        print(f"  Success Rate: {successful_operations/concurrency*100:.1f}%")
        print(f"  Operations/sec: {concurrency/total_time:.2f}")
        
        # Verify performance
        assert successful_operations / concurrency >= 0.85  # 85% success rate
        assert concurrency / total_time >= 5  # At least 5 ops/sec
        assert memory_used < 800  # Less than 800MB memory increase


class TestMemoryUsageMonitoring:
    """Memory usage monitoring and testing"""
    
    @pytest.fixture
    def vc_service(self):
        """Create version control service for memory testing"""
        temp_dir = tempfile.mkdtemp()
        db_path = Path(temp_dir) / "test_memory.db"
        storage_path = Path(temp_dir) / "versions"
        service = VersionControlService(str(db_path), str(storage_path))
        yield service
        shutil.rmtree(temp_dir)
    
    def test_memory_usage_with_large_objects(self, vc_service):
        """Test memory usage with large objects"""
        
        # Monitor memory usage
        def get_memory_usage():
            process = psutil.Process()
            return process.memory_info().rss / 1024 / 1024  # MB
        
        initial_memory = get_memory_usage()
        print(f"Initial memory usage: {initial_memory:.2f}MB")
        
        # Create large objects
        large_objects = []
        for i in range(100):
            large_object = {
                "id": f"large-obj-{i}",
                "type": "device",
                "x": i,
                "y": i,
                "properties": {
                    "name": f"Large Device {i}",
                    "description": "A" * 10000,  # 10KB description
                    "specifications": {
                        "technical_details": "B" * 5000,  # 5KB technical details
                        "requirements": "C" * 5000,  # 5KB requirements
                        "metadata": {
                            "tags": [f"tag-{j}" for j in range(50)],
                            "history": [
                                {
                                    "timestamp": datetime.utcnow().isoformat(),
                                    "action": "created",
                                    "details": "D" * 1000
                                }
                                for _ in range(20)
                            ]
                        }
                    }
                }
            }
            large_objects.append(large_object)
        
        large_floor = {
            "floor_id": "memory-floor",
            "building_id": "memory-building",
            "objects": large_objects,
            "metadata": {"name": "Memory Test Floor"}
        }
        
        # Create version
        before_create_memory = get_memory_usage()
        result = vc_service.create_version(
            large_floor,
            "memory-floor",
            "memory-building",
            "main",
            "Large objects version",
            "architect"
        )
        after_create_memory = get_memory_usage()
        
        print(f"Memory before creation: {before_create_memory:.2f}MB")
        print(f"Memory after creation: {after_create_memory:.2f}MB")
        print(f"Memory increase: {after_create_memory - before_create_memory:.2f}MB")
        
        assert result["success"] is True
        
        # Retrieve version
        before_retrieve_memory = get_memory_usage()
        version_data = vc_service.get_version_data(result["version_id"])
        after_retrieve_memory = get_memory_usage()
        
        print(f"Memory before retrieval: {before_retrieve_memory:.2f}MB")
        print(f"Memory after retrieval: {after_retrieve_memory:.2f}MB")
        print(f"Memory increase: {after_retrieve_memory - before_retrieve_memory:.2f}MB")
        
        assert version_data["success"] is True
        
        # Force garbage collection
        gc.collect()
        after_gc_memory = get_memory_usage()
        print(f"Memory after GC: {after_gc_memory:.2f}MB")
        
        # Verify memory usage is reasonable
        total_memory_increase = after_gc_memory - initial_memory
        print(f"Total memory increase: {total_memory_increase:.2f}MB")
        
        assert total_memory_increase < 100  # Less than 100MB total increase
    
    def test_memory_leak_detection(self, vc_service):
        """Test for memory leaks during repeated operations"""
        
        def get_memory_usage():
            process = psutil.Process()
            return process.memory_info().rss / 1024 / 1024  # MB
        
        initial_memory = get_memory_usage()
        print(f"Initial memory: {initial_memory:.2f}MB")
        
        # Perform repeated operations
        memory_samples = []
        
        for i in range(100):
            # Create version
            floor_data = {
                "floor_id": f"leak-test-{i}",
                "building_id": "leak-test-building",
                "objects": [
                    {"id": f"obj-{i}-{j}", "type": "device", "x": j, "y": j}
                    for j in range(100)
                ],
                "metadata": {"name": f"Leak Test {i}"}
            }
            
            result = vc_service.create_version(
                floor_data,
                f"leak-test-{i}",
                "leak-test-building",
                "main",
                f"Version {i}",
                "architect"
            )
            
            if result["success"]:
                # Retrieve version
                version_data = vc_service.get_version_data(result["version_id"])
                
                # Sample memory every 10 operations
                if i % 10 == 0:
                    current_memory = get_memory_usage()
                    memory_samples.append((i, current_memory))
                    print(f"Operation {i}: {current_memory:.2f}MB")
        
        # Force garbage collection
        gc.collect()
        final_memory = get_memory_usage()
        print(f"Final memory after GC: {final_memory:.2f}MB")
        
        # Check for memory leaks
        memory_increase = final_memory - initial_memory
        print(f"Total memory increase: {memory_increase:.2f}MB")
        
        # Memory increase should be reasonable (less than 50MB for 100 operations)
        assert memory_increase < 50
        
        # Check memory trend
        if len(memory_samples) > 5:
            # Calculate memory growth rate
            first_memory = memory_samples[0][1]
            last_memory = memory_samples[-1][1]
            growth_rate = (last_memory - first_memory) / len(memory_samples)
            
            print(f"Memory growth rate per 10 operations: {growth_rate:.2f}MB")
            
            # Growth rate should be small
            assert growth_rate < 5  # Less than 5MB per 10 operations
    
    def test_memory_usage_with_concurrent_operations(self, vc_service):
        """Test memory usage during concurrent operations"""
        
        def get_memory_usage():
            process = psutil.Process()
            return process.memory_info().rss / 1024 / 1024  # MB
        
        initial_memory = get_memory_usage()
        print(f"Initial memory: {initial_memory:.2f}MB")
        
        def concurrent_operation(operation_id):
            try:
                # Create version
                floor_data = {
                    "floor_id": f"concurrent-memory-{operation_id}",
                    "building_id": "concurrent-memory-building",
                    "objects": [
                        {"id": f"obj-{operation_id}-{j}", "type": "device", "x": j, "y": j}
                        for j in range(50)
                    ],
                    "metadata": {"name": f"Concurrent Memory {operation_id}"}
                }
                
                result = vc_service.create_version(
                    floor_data,
                    f"concurrent-memory-{operation_id}",
                    "concurrent-memory-building",
                    "main",
                    f"Version {operation_id}",
                    f"user-{operation_id}"
                )
                
                if result["success"]:
                    # Retrieve version
                    version_data = vc_service.get_version_data(result["version_id"])
                    return {"operation_id": operation_id, "success": version_data["success"]}
                else:
                    return {"operation_id": operation_id, "success": False}
                    
            except Exception as e:
                return {"operation_id": operation_id, "success": False, "error": str(e)}
        
        # Run concurrent operations
        concurrency = 50
        print(f"Running {concurrency} concurrent operations...")
        
        start_memory = get_memory_usage()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as executor:
            futures = [executor.submit(concurrent_operation, i) for i in range(concurrency)]
            results = [future.result() for future in futures]
        
        peak_memory = get_memory_usage()
        
        # Force garbage collection
        gc.collect()
        final_memory = get_memory_usage()
        
        print(f"Start memory: {start_memory:.2f}MB")
        print(f"Peak memory: {peak_memory:.2f}MB")
        print(f"Final memory: {final_memory:.2f}MB")
        print(f"Peak increase: {peak_memory - start_memory:.2f}MB")
        print(f"Final increase: {final_memory - start_memory:.2f}MB")
        
        # Verify memory usage
        successful_operations = sum(1 for r in results if r["success"])
        print(f"Successful operations: {successful_operations}/{concurrency}")
        
        assert successful_operations >= concurrency * 0.9  # 90% success rate
        assert peak_memory - start_memory < 200  # Less than 200MB peak increase
        assert final_memory - start_memory < 100  # Less than 100MB final increase


class TestDatabasePerformance:
    """Database performance testing"""
    
    @pytest.fixture
    def vc_service(self):
        """Create version control service for database testing"""
        temp_dir = tempfile.mkdtemp()
        db_path = Path(temp_dir) / "test_db_performance.db"
        storage_path = Path(temp_dir) / "versions"
        service = VersionControlService(str(db_path), str(storage_path))
        yield service
        shutil.rmtree(temp_dir)
    
    def test_database_write_performance(self, vc_service):
        """Test database write performance"""
        
        # Test bulk insert performance
        print("Testing database write performance...")
        
        start_time = time.time()
        
        # Create 1000 versions
        for i in range(1000):
            floor_data = {
                "floor_id": f"write-perf-{i}",
                "building_id": "write-perf-building",
                "objects": [
                    {"id": f"obj-{i}-{j}", "type": "device", "x": j, "y": j}
                    for j in range(10)
                ],
                "metadata": {"name": f"Write Performance {i}"}
            }
            
            result = vc_service.create_version(
                floor_data,
                f"write-perf-{i}",
                "write-perf-building",
                "main",
                f"Version {i}",
                "architect"
            )
            
            if not result["success"]:
                print(f"Failed at version {i}: {result['message']}")
                break
        
        end_time = time.time()
        total_time = end_time - start_time
        
        print(f"Created 1000 versions in {total_time:.2f} seconds")
        print(f"Average time per version: {total_time/1000*1000:.2f}ms")
        print(f"Versions per second: {1000/total_time:.2f}")
        
        # Performance requirements
        assert total_time < 60  # Less than 60 seconds for 1000 versions
        assert 1000 / total_time >= 15  # At least 15 versions per second
    
    def test_database_read_performance(self, vc_service):
        """Test database read performance"""
        
        # Create test data
        print("Creating test data for read performance...")
        
        version_ids = []
        for i in range(100):
            floor_data = {
                "floor_id": f"read-perf-{i}",
                "building_id": "read-perf-building",
                "objects": [
                    {"id": f"obj-{i}-{j}", "type": "device", "x": j, "y": j}
                    for j in range(50)
                ],
                "metadata": {"name": f"Read Performance {i}"}
            }
            
            result = vc_service.create_version(
                floor_data,
                f"read-perf-{i}",
                "read-perf-building",
                "main",
                f"Version {i}",
                "architect"
            )
            
            if result["success"]:
                version_ids.append(result["version_id"])
        
        print(f"Created {len(version_ids)} versions for testing")
        
        # Test read performance
        print("Testing read performance...")
        
        start_time = time.time()
        
        for version_id in version_ids:
            version_data = vc_service.get_version_data(version_id)
            if not version_data["success"]:
                print(f"Failed to read version {version_id}")
        
        end_time = time.time()
        total_time = end_time - start_time
        
        print(f"Read {len(version_ids)} versions in {total_time:.2f} seconds")
        print(f"Average time per read: {total_time/len(version_ids)*1000:.2f}ms")
        print(f"Reads per second: {len(version_ids)/total_time:.2f}")
        
        # Performance requirements
        assert total_time < 10  # Less than 10 seconds for 100 reads
        assert len(version_ids) / total_time >= 10  # At least 10 reads per second
    
    def test_database_query_performance(self, vc_service):
        """Test database query performance"""
        
        # Create test data with different patterns
        print("Creating test data for query performance...")
        
        buildings = ["building-a", "building-b", "building-c"]
        floors_per_building = 50
        
        for building in buildings:
            for floor in range(floors_per_building):
                floor_data = {
                    "floor_id": f"query-perf-{building}-{floor}",
                    "building_id": building,
                    "objects": [
                        {"id": f"obj-{building}-{floor}-{j}", "type": "device", "x": j, "y": j}
                        for j in range(20)
                    ],
                    "metadata": {"name": f"Query Performance {building} {floor}"}
                }
                
                vc_service.create_version(
                    floor_data,
                    f"query-perf-{building}-{floor}",
                    building,
                    "main",
                    f"Version {floor}",
                    "architect"
                )
        
        print(f"Created {len(buildings) * floors_per_building} versions")
        
        # Test query performance
        print("Testing query performance...")
        
        query_times = []
        
        # Test get_version_history queries
        for building in buildings:
            start_time = time.time()
            history = vc_service.get_version_history(f"query-perf-{building}-0", building)
            end_time = time.time()
            
            query_time = end_time - start_time
            query_times.append(query_time)
            
            print(f"History query for {building}: {query_time*1000:.2f}ms")
        
        # Test get_branches queries
        for building in buildings:
            start_time = time.time()
            branches = vc_service.get_branches(f"query-perf-{building}-0", building)
            end_time = time.time()
            
            query_time = end_time - start_time
            query_times.append(query_time)
            
            print(f"Branches query for {building}: {query_time*1000:.2f}ms")
        
        avg_query_time = sum(query_times) / len(query_times)
        max_query_time = max(query_times)
        
        print(f"Average query time: {avg_query_time*1000:.2f}ms")
        print(f"Maximum query time: {max_query_time*1000:.2f}ms")
        
        # Performance requirements
        assert avg_query_time < 0.1  # Less than 100ms average
        assert max_query_time < 0.5  # Less than 500ms maximum
    
    def test_database_concurrent_access_performance(self, vc_service):
        """Test database performance under concurrent access"""
        
        # Create initial data
        initial_floor = {"floor_id": "concurrent-db-floor", "building_id": "concurrent-db-building", "objects": []}
        initial_version = vc_service.create_version(
            initial_floor,
            "concurrent-db-floor",
            "concurrent-db-building",
            "main",
            "Initial version",
            "architect"
        )
        
        def concurrent_db_operation(operation_id):
            try:
                # Mix of read and write operations
                operations = []
                
                # Read operation
                version_data = vc_service.get_version_data(initial_version["version_id"])
                if version_data["success"]:
                    operations.append("read")
                
                # Write operation
                modified_floor = initial_floor.copy()
                modified_floor["objects"].append({
                    "id": f"concurrent-obj-{operation_id}",
                    "type": "device",
                    "x": operation_id,
                    "y": operation_id
                })
                
                write_result = vc_service.create_version(
                    modified_floor,
                    "concurrent-db-floor",
                    "concurrent-db-building",
                    "main",
                    f"Concurrent version {operation_id}",
                    f"user-{operation_id}"
                )
                
                if write_result["success"]:
                    operations.append("write")
                
                # Query operation
                history = vc_service.get_version_history("concurrent-db-floor", "concurrent-db-building")
                if history["success"]:
                    operations.append("query")
                
                return {
                    "operation_id": operation_id,
                    "success": len(operations) >= 2,
                    "operations": operations
                }
                
            except Exception as e:
                return {"operation_id": operation_id, "success": False, "error": str(e)}
        
        # Test with different concurrency levels
        concurrency_levels = [10, 25, 50, 100]
        performance_results = {}
        
        for concurrency in concurrency_levels:
            print(f"\nTesting concurrent DB access with {concurrency} operations...")
            
            start_time = time.time()
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as executor:
                futures = [executor.submit(concurrent_db_operation, i) for i in range(concurrency)]
                results = [future.result() for future in futures]
            
            end_time = time.time()
            total_time = end_time - start_time
            
            successful_operations = sum(1 for r in results if r["success"])
            
            performance_results[concurrency] = {
                "total_time": total_time,
                "successful_operations": successful_operations,
                "success_rate": successful_operations / concurrency,
                "operations_per_second": concurrency / total_time
            }
            
            print(f"  Time: {total_time:.2f}s")
            print(f"  Success Rate: {successful_operations/concurrency*100:.1f}%")
            print(f"  Ops/sec: {concurrency/total_time:.2f}")
        
        # Verify performance requirements
        for concurrency, result in performance_results.items():
            assert result["success_rate"] >= 0.85  # 85% success rate
            assert result["operations_per_second"] >= 5  # At least 5 ops/sec


class TestScalabilityTesting:
    """Scalability testing"""
    
    @pytest.fixture
    def vc_service(self):
        """Create version control service for scalability testing"""
        temp_dir = tempfile.mkdtemp()
        db_path = Path(temp_dir) / "test_scalability.db"
        storage_path = Path(temp_dir) / "versions"
        service = VersionControlService(str(db_path), str(storage_path))
        yield service
        shutil.rmtree(temp_dir)
    
    def test_scalability_with_increasing_data_size(self, vc_service):
        """Test scalability with increasing data size"""
        
        data_sizes = [100, 500, 1000, 2000, 5000]
        scalability_results = {}
        
        for size in data_sizes:
            print(f"\nTesting with {size} objects per version...")
            
            # Create large floor data
            large_objects = [
                {"id": f"obj-{i}", "type": "device", "x": i, "y": i}
                for i in range(size)
            ]
            
            large_floor = {
                "floor_id": f"scalability-{size}",
                "building_id": "scalability-building",
                "objects": large_objects,
                "metadata": {"name": f"Scalability Test {size}"}
            }
            
            # Measure creation time
            start_time = time.time()
            result = vc_service.create_version(
                large_floor,
                f"scalability-{size}",
                "scalability-building",
                "main",
                f"Scalability version {size}",
                "architect"
            )
            creation_time = time.time() - start_time
            
            if result["success"]:
                # Measure retrieval time
                start_time = time.time()
                version_data = vc_service.get_version_data(result["version_id"])
                retrieval_time = time.time() - start_time
                
                scalability_results[size] = {
                    "creation_time": creation_time,
                    "retrieval_time": retrieval_time,
                    "creation_rate": size / creation_time,
                    "retrieval_rate": size / retrieval_time
                }
                
                print(f"  Creation time: {creation_time:.2f}s")
                print(f"  Retrieval time: {retrieval_time:.2f}s")
                print(f"  Creation rate: {size/creation_time:.2f} objects/sec")
                print(f"  Retrieval rate: {size/retrieval_time:.2f} objects/sec")
        
        # Analyze scalability
        print("\nScalability Analysis:")
        for size, result in scalability_results.items():
            print(f"  {size} objects: {result['creation_rate']:.2f} create/sec, {result['retrieval_rate']:.2f} retrieve/sec")
        
        # Verify scalability characteristics
        sizes = list(scalability_results.keys())
        if len(sizes) >= 3:
            # Performance should not degrade more than linearly
            first_rate = scalability_results[sizes[0]]["creation_rate"]
            last_rate = scalability_results[sizes[-1]]["creation_rate"]
            size_ratio = sizes[-1] / sizes[0]
            rate_ratio = first_rate / last_rate
            
            print(f"Size increase: {size_ratio:.1f}x")
            print(f"Rate decrease: {rate_ratio:.1f}x")
            
            # Rate should not decrease more than the size increase
            assert rate_ratio <= size_ratio * 2  # Allow some degradation
    
    def test_scalability_with_increasing_concurrency(self, vc_service):
        """Test scalability with increasing concurrency"""
        
        concurrency_levels = [1, 5, 10, 20, 50, 100]
        concurrency_results = {}
        
        for concurrency in concurrency_levels:
            print(f"\nTesting with {concurrency} concurrent operations...")
            
            def simple_operation(operation_id):
                try:
                    floor_data = {
                        "floor_id": f"concurrency-{operation_id}",
                        "building_id": "concurrency-building",
                        "objects": [{"id": f"obj-{operation_id}", "type": "device", "x": operation_id, "y": operation_id}],
                        "metadata": {"name": f"Concurrency Test {operation_id}"}
                    }
                    
                    result = vc_service.create_version(
                        floor_data,
                        f"concurrency-{operation_id}",
                        "concurrency-building",
                        "main",
                        f"Version {operation_id}",
                        f"user-{operation_id}"
                    )
                    
                    return {"operation_id": operation_id, "success": result["success"]}
                    
                except Exception as e:
                    return {"operation_id": operation_id, "success": False, "error": str(e)}
            
            start_time = time.time()
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as executor:
                futures = [executor.submit(simple_operation, i) for i in range(concurrency)]
                results = [future.result() for future in futures]
            
            end_time = time.time()
            total_time = end_time - start_time
            
            successful_operations = sum(1 for r in results if r["success"])
            
            concurrency_results[concurrency] = {
                "total_time": total_time,
                "successful_operations": successful_operations,
                "success_rate": successful_operations / concurrency,
                "operations_per_second": concurrency / total_time
            }
            
            print(f"  Time: {total_time:.2f}s")
            print(f"  Success Rate: {successful_operations/concurrency*100:.1f}%")
            print(f"  Ops/sec: {concurrency/total_time:.2f}")
        
        # Analyze concurrency scalability
        print("\nConcurrency Scalability Analysis:")
        for concurrency, result in concurrency_results.items():
            print(f"  {concurrency} concurrent: {result['operations_per_second']:.2f} ops/sec")
        
        # Verify concurrency characteristics
        concurrency_levels = list(concurrency_results.keys())
        if len(concurrency_levels) >= 3:
            # Throughput should increase with concurrency up to a point
            throughputs = [concurrency_results[c]["operations_per_second"] for c in concurrency_levels]
            
            # Find peak throughput
            peak_throughput = max(throughputs)
            peak_concurrency = concurrency_levels[throughputs.index(peak_throughput)]
            
            print(f"Peak throughput: {peak_throughput:.2f} ops/sec at {peak_concurrency} concurrent")
            
            # Success rate should remain high
            for concurrency, result in concurrency_results.items():
                assert result["success_rate"] >= 0.8  # 80% success rate minimum


if __name__ == "__main__":
    pytest.main([__file__]) 