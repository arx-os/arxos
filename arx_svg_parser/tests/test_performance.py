"""
Performance Testing Framework for Arxos Platform

Comprehensive performance tests including:
- Load testing
- Stress testing
- Performance benchmarking
- Memory usage monitoring
- Response time analysis
"""

import pytest
import time
import psutil
import threading
import concurrent.futures
import asyncio
import tempfile
import os
import json
import statistics
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import gc

from ..services.export_interoperability import ExportInteroperabilityService, ExportFormat
from ..services.enhanced_bim_assembly import EnhancedBIMAssembly
from ..services.access_control import AccessControlService
from services.validation_framework import UnifiedValidator

@dataclass
class PerformanceMetrics:
    """Performance metrics for testing."""
    operation: str
    duration_ms: float
    memory_usage_mb: float
    cpu_usage_percent: float
    success: bool
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class PerformanceTestFramework:
    """Framework for comprehensive performance testing."""
    
    def __init__(self):
        self.metrics: List[PerformanceMetrics] = []
        self.process = psutil.Process()
    
    def measure_operation(self, operation_name: str, func, *args, **kwargs) -> PerformanceMetrics:
        """Measure performance of an operation."""
        # Get initial memory usage
        initial_memory = self.process.memory_info().rss / 1024 / 1024  # MB
        initial_cpu = self.process.cpu_percent()
        
        # Measure operation
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            success = True
            error_message = None
        except Exception as e:
            result = None
            success = False
            error_message = str(e)
        
        end_time = time.time()
        
        # Get final memory usage
        final_memory = self.process.memory_info().rss / 1024 / 1024  # MB
        final_cpu = self.process.cpu_percent()
        
        # Calculate metrics
        duration_ms = (end_time - start_time) * 1000
        memory_usage_mb = final_memory - initial_memory
        cpu_usage_percent = (initial_cpu + final_cpu) / 2
        
        metrics = PerformanceMetrics(
            operation=operation_name,
            duration_ms=duration_ms,
            memory_usage_mb=memory_usage_mb,
            cpu_usage_percent=cpu_usage_percent,
            success=success,
            error_message=error_message,
            metadata={"result_size": len(str(result)) if result else 0}
        )
        
        self.metrics.append(metrics)
        return metrics
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get performance statistics."""
        if not self.metrics:
            return {}
        
        successful_metrics = [m for m in self.metrics if m.success]
        failed_metrics = [m for m in self.metrics if not m.success]
        
        stats = {
            "total_operations": len(self.metrics),
            "successful_operations": len(successful_metrics),
            "failed_operations": len(failed_metrics),
            "success_rate": len(successful_metrics) / len(self.metrics) * 100,
            "average_duration_ms": statistics.mean([m.duration_ms for m in successful_metrics]) if successful_metrics else 0,
            "median_duration_ms": statistics.median([m.duration_ms for m in successful_metrics]) if successful_metrics else 0,
            "min_duration_ms": min([m.duration_ms for m in successful_metrics]) if successful_metrics else 0,
            "max_duration_ms": max([m.duration_ms for m in successful_metrics]) if successful_metrics else 0,
            "average_memory_usage_mb": statistics.mean([m.memory_usage_mb for m in successful_metrics]) if successful_metrics else 0,
            "average_cpu_usage_percent": statistics.mean([m.cpu_usage_percent for m in successful_metrics]) if successful_metrics else 0,
            "total_memory_usage_mb": sum([m.memory_usage_mb for m in successful_metrics]),
            "operations_per_second": len(successful_metrics) / (sum([m.duration_ms for m in successful_metrics]) / 1000) if successful_metrics else 0
        }
        
        return stats

class TestExportPerformance:
    """Performance tests for export operations."""
    
    @pytest.fixture
    def temp_db(self):
        """Create temporary database for testing."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        yield db_path
        if os.path.exists(db_path):
            os.unlink(db_path)
    
    @pytest.fixture
    def export_service(self, temp_db):
        """Create export service instance."""
        return ExportInteroperabilityService(db_path=temp_db)
    
    @pytest.fixture
    def performance_framework(self):
        """Create performance testing framework."""
        return PerformanceTestFramework()
    
    @pytest.fixture
    def small_building_data(self):
        """Small building data for performance testing."""
        return {
            "building_id": "PERF_TEST_SMALL",
            "building_name": "Small Test Building",
            "floor_count": 1,
            "total_area_sqft": 1000.0,
            "elements": [
                {
                    "id": f"ELEMENT_{i:03d}",
                    "name": f"Element {i}",
                    "type": "WALL" if i % 3 == 0 else "COLUMN" if i % 3 == 1 else "WINDOW",
                    "x": float(i % 10),
                    "y": float(i // 10),
                    "z": 0.0,
                    "system": "STRUCTURAL" if i % 3 == 0 else "ARCHITECTURAL",
                    "floor": 1,
                    "properties": {
                        "material": "Concrete" if i % 3 == 0 else "Steel",
                        "size": i % 5 + 1
                    }
                }
                for i in range(100)  # 100 elements
            ]
        }
    
    @pytest.fixture
    def medium_building_data(self):
        """Medium building data for performance testing."""
        return {
            "building_id": "PERF_TEST_MEDIUM",
            "building_name": "Medium Test Building",
            "floor_count": 5,
            "total_area_sqft": 50000.0,
            "elements": [
                {
                    "id": f"ELEMENT_{i:04d}",
                    "name": f"Element {i}",
                    "type": "WALL" if i % 3 == 0 else "COLUMN" if i % 3 == 1 else "WINDOW",
                    "x": float(i % 100),
                    "y": float(i // 100),
                    "z": float(i % 10),
                    "system": "STRUCTURAL" if i % 3 == 0 else "ARCHITECTURAL",
                    "floor": (i % 5) + 1,
                    "properties": {
                        "material": "Concrete" if i % 3 == 0 else "Steel",
                        "size": i % 10 + 1
                    }
                }
                for i in range(1000)  # 1000 elements
            ]
        }
    
    @pytest.fixture
    def large_building_data(self):
        """Large building data for performance testing."""
        return {
            "building_id": "PERF_TEST_LARGE",
            "building_name": "Large Test Building",
            "floor_count": 20,
            "total_area_sqft": 500000.0,
            "elements": [
                {
                    "id": f"ELEMENT_{i:05d}",
                    "name": f"Element {i}",
                    "type": "WALL" if i % 3 == 0 else "COLUMN" if i % 3 == 1 else "WINDOW",
                    "x": float(i % 200),
                    "y": float(i // 200),
                    "z": float(i % 20),
                    "system": "STRUCTURAL" if i % 3 == 0 else "ARCHITECTURAL",
                    "floor": (i % 20) + 1,
                    "properties": {
                        "material": "Concrete" if i % 3 == 0 else "Steel",
                        "size": i % 15 + 1
                    }
                }
                for i in range(5000)  # 5000 elements
            ]
        }
    
    def test_export_performance_small_building(self, export_service, performance_framework, small_building_data):
        """Test export performance with small building data."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Test IFC-lite export
            metrics = performance_framework.measure_operation(
                "export_ifc_lite_small",
                export_service.export_to_ifc_lite,
                building_data=small_building_data,
                options={"output_path": os.path.join(temp_dir, "small.ifc")}
            )
            
            assert metrics.success
            assert metrics.duration_ms < 1000  # Should complete in under 1 second
            assert metrics.memory_usage_mb < 50  # Should use less than 50MB
            
            print(f"Small building IFC export: {metrics.duration_ms:.2f}ms, {metrics.memory_usage_mb:.2f}MB")
    
    def test_export_performance_medium_building(self, export_service, performance_framework, medium_building_data):
        """Test export performance with medium building data."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Test IFC-lite export
            metrics = performance_framework.measure_operation(
                "export_ifc_lite_medium",
                export_service.export_to_ifc_lite,
                building_data=medium_building_data,
                options={"output_path": os.path.join(temp_dir, "medium.ifc")}
            )
            
            assert metrics.success
            assert metrics.duration_ms < 5000  # Should complete in under 5 seconds
            assert metrics.memory_usage_mb < 200  # Should use less than 200MB
            
            print(f"Medium building IFC export: {metrics.duration_ms:.2f}ms, {metrics.memory_usage_mb:.2f}MB")
    
    def test_export_performance_large_building(self, export_service, performance_framework, large_building_data):
        """Test export performance with large building data."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Test IFC-lite export
            metrics = performance_framework.measure_operation(
                "export_ifc_lite_large",
                export_service.export_to_ifc_lite,
                building_data=large_building_data,
                options={"output_path": os.path.join(temp_dir, "large.ifc")}
            )
            
            assert metrics.success
            assert metrics.duration_ms < 30000  # Should complete in under 30 seconds
            assert metrics.memory_usage_mb < 500  # Should use less than 500MB
            
            print(f"Large building IFC export: {metrics.duration_ms:.2f}ms, {metrics.memory_usage_mb:.2f}MB")
    
    def test_multi_format_export_performance(self, export_service, performance_framework, medium_building_data):
        """Test performance of exporting to multiple formats."""
        with tempfile.TemporaryDirectory() as temp_dir:
            formats = [
                ("ifc_lite", "ifc"),
                ("gltf", "gltf"),
                ("ascii_bim", "txt"),
                ("geojson", "geojson")
            ]
            
            for format_name, extension in formats:
                metrics = performance_framework.measure_operation(
                    f"export_{format_name}",
                    getattr(export_service, f"export_to_{format_name}"),
                    building_data=medium_building_data,
                    options={"output_path": os.path.join(temp_dir, f"test.{extension}")}
                )
                
                assert metrics.success
                assert metrics.duration_ms < 10000  # Should complete in under 10 seconds
                
                print(f"{format_name.upper()} export: {metrics.duration_ms:.2f}ms, {metrics.memory_usage_mb:.2f}MB")
    
    def test_concurrent_export_performance(self, export_service, performance_framework, small_building_data):
        """Test performance with concurrent export operations."""
        with tempfile.TemporaryDirectory() as temp_dir:
            def export_operation(operation_id):
                return performance_framework.measure_operation(
                    f"concurrent_export_{operation_id}",
                    export_service.export_to_ifc_lite,
                    building_data=small_building_data,
                    options={"output_path": os.path.join(temp_dir, f"concurrent_{operation_id}.ifc")}
                )
            
            # Run 5 concurrent exports
            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                futures = [executor.submit(export_operation, i) for i in range(5)]
                results = [future.result() for future in concurrent.futures.as_completed(futures)]
            
            # Verify all operations succeeded
            assert all(result.success for result in results)
            
            # Calculate concurrent performance
            total_time = max(result.duration_ms for result in results)
            total_memory = sum(result.memory_usage_mb for result in results)
            
            print(f"Concurrent exports (5): {total_time:.2f}ms total, {total_memory:.2f}MB total memory")
            
            # Should complete in reasonable time
            assert total_time < 5000  # Under 5 seconds for all concurrent operations
    
    def test_memory_usage_under_load(self, export_service, performance_framework, medium_building_data):
        """Test memory usage under sustained load."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Perform multiple exports to test memory usage
            for i in range(10):
                metrics = performance_framework.measure_operation(
                    f"memory_test_{i}",
                    export_service.export_to_ifc_lite,
                    building_data=medium_building_data,
                    options={"output_path": os.path.join(temp_dir, f"memory_test_{i}.ifc")}
                )
                
                assert metrics.success
                
                # Force garbage collection to measure actual memory usage
                gc.collect()
            
            # Get memory statistics
            stats = performance_framework.get_statistics()
            
            print(f"Memory usage under load: {stats['average_memory_usage_mb']:.2f}MB average")
            print(f"Peak memory usage: {stats['total_memory_usage_mb']:.2f}MB total")
            
            # Memory usage should be reasonable
            assert stats['average_memory_usage_mb'] < 100  # Less than 100MB average
            assert stats['total_memory_usage_mb'] < 1000  # Less than 1GB total

class TestBIMAssemblyPerformance:
    """Performance tests for BIM assembly operations."""
    
    @pytest.fixture
    def bim_service(self):
        """Create BIM assembly service."""
        return EnhancedBIMAssembly()
    
    @pytest.fixture
    def performance_framework(self):
        """Create performance testing framework."""
        return PerformanceTestFramework()
    
    def test_bim_assembly_performance(self, bim_service, performance_framework):
        """Test BIM assembly performance."""
        # Create test data
        test_data = {
            "building_id": "PERF_TEST_BIM",
            "elements": [
                {
                    "id": f"ELEMENT_{i}",
                    "name": f"Element {i}",
                    "type": "WALL",
                    "x": float(i % 10),
                    "y": float(i // 10),
                    "z": 0.0,
                    "system": "STRUCTURAL",
                    "floor": 1,
                    "properties": {"material": "Concrete"}
                }
                for i in range(500)  # 500 elements
            ]
        }
        
        # Test BIM assembly
        metrics = performance_framework.measure_operation(
            "bim_assembly",
            bim_service.assemble_bim,
            test_data
        )
        
        assert metrics.success
        assert metrics.duration_ms < 2000  # Should complete in under 2 seconds
        assert metrics.memory_usage_mb < 100  # Should use less than 100MB
        
        print(f"BIM assembly: {metrics.duration_ms:.2f}ms, {metrics.memory_usage_mb:.2f}MB")

class TestValidationPerformance:
    """Performance tests for validation operations."""
    
    @pytest.fixture
    def validator(self):
        """Create validation framework."""
        return UnifiedValidator()
    
    @pytest.fixture
    def performance_framework(self):
        """Create performance testing framework."""
        return PerformanceTestFramework()
    
    def test_validation_performance(self, validator, performance_framework):
        """Test validation performance."""
        # Create test BIM data
        test_bim_data = {
            "building_id": "PERF_TEST_VALIDATION",
            "elements": [
                {
                    "id": f"ELEMENT_{i}",
                    "name": f"Element {i}",
                    "type": "WALL",
                    "x": float(i % 10),
                    "y": float(i // 10),
                    "z": 0.0,
                    "system": "STRUCTURAL",
                    "floor": 1,
                    "properties": {"material": "Concrete"}
                }
                for i in range(1000)  # 1000 elements
            ]
        }
        
        # Test validation
        metrics = performance_framework.measure_operation(
            "validation",
            validator.validate_bim_model,
            test_bim_data
        )
        
        assert metrics.success
        assert metrics.duration_ms < 3000  # Should complete in under 3 seconds
        assert metrics.memory_usage_mb < 150  # Should use less than 150MB
        
        print(f"Validation: {metrics.duration_ms:.2f}ms, {metrics.memory_usage_mb:.2f}MB")

class TestLoadTesting:
    """Load testing for the platform."""
    
    @pytest.fixture
    def export_service(self):
        """Create export service."""
        return ExportInteroperabilityService()
    
    def test_concurrent_users_load(self, export_service):
        """Test system performance under concurrent user load."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Simulate 10 concurrent users
            def user_workload(user_id):
                building_data = {
                    "building_id": f"LOAD_TEST_USER_{user_id}",
                    "building_name": f"User {user_id} Building",
                    "elements": [
                        {
                            "id": f"ELEMENT_{user_id}_{i}",
                            "name": f"Element {i}",
                            "type": "WALL",
                            "x": float(i % 10),
                            "y": float(i // 10),
                            "z": 0.0,
                            "system": "STRUCTURAL",
                            "floor": 1,
                            "properties": {"material": "Concrete"}
                        }
                        for i in range(100)  # 100 elements per user
                    ]
                }
                
                start_time = time.time()
                
                # Perform export
                result_path = export_service.export_to_ifc_lite(
                    building_data=building_data,
                    options={"output_path": os.path.join(temp_dir, f"user_{user_id}.ifc")}
                )
                
                end_time = time.time()
                duration = (end_time - start_time) * 1000
                
                return {
                    "user_id": user_id,
                    "duration_ms": duration,
                    "success": os.path.exists(result_path)
                }
            
            # Run concurrent workloads
            with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                futures = [executor.submit(user_workload, i) for i in range(10)]
                results = [future.result() for future in concurrent.futures.as_completed(futures)]
            
            # Analyze results
            successful_results = [r for r in results if r["success"]]
            failed_results = [r for r in results if not r["success"]]
            
            avg_duration = statistics.mean([r["duration_ms"] for r in successful_results]) if successful_results else 0
            max_duration = max([r["duration_ms"] for r in successful_results]) if successful_results else 0
            
            print(f"Load test results:")
            print(f"  Successful operations: {len(successful_results)}/10")
            print(f"  Average duration: {avg_duration:.2f}ms")
            print(f"  Maximum duration: {max_duration:.2f}ms")
            
            # Verify performance requirements
            assert len(successful_results) >= 8  # At least 80% success rate
            assert avg_duration < 5000  # Average under 5 seconds
            assert max_duration < 10000  # Maximum under 10 seconds

class TestStressTesting:
    """Stress testing for the platform."""
    
    @pytest.fixture
    def export_service(self):
        """Create export service."""
        return ExportInteroperabilityService()
    
    def test_large_file_processing(self, export_service):
        """Test processing of very large building data."""
        # Create very large building data
        large_building_data = {
            "building_id": "STRESS_TEST_LARGE",
            "building_name": "Stress Test Large Building",
            "floor_count": 50,
            "total_area_sqft": 2000000.0,
            "elements": [
                {
                    "id": f"ELEMENT_{i:06d}",
                    "name": f"Element {i}",
                    "type": "WALL" if i % 3 == 0 else "COLUMN" if i % 3 == 1 else "WINDOW",
                    "x": float(i % 500),
                    "y": float(i // 500),
                    "z": float(i % 50),
                    "system": "STRUCTURAL" if i % 3 == 0 else "ARCHITECTURAL",
                    "floor": (i % 50) + 1,
                    "properties": {
                        "material": "Concrete" if i % 3 == 0 else "Steel",
                        "size": i % 20 + 1,
                        "complex_property": "x" * 1000  # Large property
                    }
                }
                for i in range(10000)  # 10,000 elements
            ]
        }
        
        with tempfile.TemporaryDirectory() as temp_dir:
            start_time = time.time()
            
            # Test export
            result_path = export_service.export_to_ifc_lite(
                building_data=large_building_data,
                options={"output_path": os.path.join(temp_dir, "stress_test.ifc")}
            )
            
            end_time = time.time()
            duration = (end_time - start_time) * 1000
            
            # Verify export completed
            assert os.path.exists(result_path)
            file_size = os.path.getsize(result_path)
            
            print(f"Stress test results:")
            print(f"  Duration: {duration:.2f}ms")
            print(f"  File size: {file_size} bytes")
            print(f"  Elements processed: 10,000")
            
            # Verify performance requirements
            assert duration < 60000  # Under 60 seconds
            assert file_size > 100000  # Substantial file size
    
    def test_memory_stress_test(self, export_service):
        """Test memory usage under stress conditions."""
        # Create multiple large buildings to stress memory
        buildings = []
        
        for building_id in range(5):
            building_data = {
                "building_id": f"STRESS_MEMORY_{building_id}",
                "building_name": f"Memory Stress Building {building_id}",
                "elements": [
                    {
                        "id": f"ELEMENT_{building_id}_{i:04d}",
                        "name": f"Element {i}",
                        "type": "WALL",
                        "x": float(i % 100),
                        "y": float(i // 100),
                        "z": 0.0,
                        "system": "STRUCTURAL",
                        "floor": 1,
                        "properties": {
                            "material": "Concrete",
                            "large_property": "x" * 5000  # Very large property
                        }
                    }
                    for i in range(2000)  # 2000 elements per building
                ]
            }
            buildings.append(building_data)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            process = psutil.Process()
            initial_memory = process.memory_info().rss / 1024 / 1024  # MB
            
            # Process all buildings
            for i, building_data in enumerate(buildings):
                result_path = export_service.export_to_ifc_lite(
                    building_data=building_data,
                    options={"output_path": os.path.join(temp_dir, f"stress_memory_{i}.ifc")}
                )
                
                # Force garbage collection
                gc.collect()
            
            final_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_increase = final_memory - initial_memory
            
            print(f"Memory stress test results:")
            print(f"  Initial memory: {initial_memory:.2f}MB")
            print(f"  Final memory: {final_memory:.2f}MB")
            print(f"  Memory increase: {memory_increase:.2f}MB")
            
            # Verify memory usage is reasonable
            assert memory_increase < 1000  # Less than 1GB increase
            assert final_memory < 2000  # Less than 2GB total

def test_performance_benchmarks():
    """Run comprehensive performance benchmarks."""
    print("\n" + "="*60)
    print("PERFORMANCE BENCHMARKS")
    print("="*60)
    
    # Create performance framework
    framework = PerformanceTestFramework()
    
    # Test export service
    export_service = ExportInteroperabilityService()
    
    # Test data
    test_data = {
        "building_id": "BENCHMARK_TEST",
        "building_name": "Benchmark Test Building",
        "elements": [
            {
                "id": f"ELEMENT_{i:04d}",
                "name": f"Element {i}",
                "type": "WALL" if i % 3 == 0 else "COLUMN" if i % 3 == 1 else "WINDOW",
                "x": float(i % 100),
                "y": float(i // 100),
                "z": 0.0,
                "system": "STRUCTURAL" if i % 3 == 0 else "ARCHITECTURAL",
                "floor": 1,
                "properties": {"material": "Concrete"}
            }
            for i in range(1000)  # 1000 elements
        ]
    }
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Benchmark different export formats
        formats = [
            ("IFC-lite", "ifc"),
            ("glTF", "gltf"),
            ("ASCII-BIM", "txt"),
            ("GeoJSON", "geojson")
        ]
        
        for format_name, extension in formats:
            metrics = framework.measure_operation(
                f"benchmark_{format_name.lower()}",
                getattr(export_service, f"export_to_{format_name.lower().replace('-', '_')}"),
                building_data=test_data,
                options={"output_path": os.path.join(temp_dir, f"benchmark.{extension}")}
            )
            
            print(f"{format_name:12} | {metrics.duration_ms:8.2f}ms | {metrics.memory_usage_mb:8.2f}MB")
    
    # Get overall statistics
    stats = framework.get_statistics()
    
    print("\n" + "-"*60)
    print("OVERALL STATISTICS")
    print("-"*60)
    print(f"Total operations: {stats['total_operations']}")
    print(f"Success rate: {stats['success_rate']:.1f}%")
    print(f"Average duration: {stats['average_duration_ms']:.2f}ms")
    print(f"Operations per second: {stats['operations_per_second']:.2f}")
    print(f"Total memory usage: {stats['total_memory_usage_mb']:.2f}MB")
    
    # Performance requirements
    assert stats['success_rate'] >= 95.0  # 95% success rate
    assert stats['average_duration_ms'] < 5000  # Under 5 seconds average
    assert stats['operations_per_second'] >= 0.2  # At least 0.2 ops/sec
    assert stats['total_memory_usage_mb'] < 1000  # Less than 1GB total memory

if __name__ == "__main__":
    # Run performance benchmarks
    test_performance_benchmarks() 