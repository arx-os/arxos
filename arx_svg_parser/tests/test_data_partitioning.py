"""
Tests for Data Partitioning Service
Tests floor-based data partitioning, lazy loading, compression, and performance monitoring
"""

import pytest
import asyncio
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta

from arx_svg_parser.services.data_partitioning import (
    DataPartitioningService, FloorPartitioner, DataCompressor, LazyLoader, PerformanceMonitor,
    PartitionStrategy, CompressionType, LoadStrategy, PartitionInfo, PerformanceMetrics
)

class TestDataCompressor:
    """Test data compression functionality"""
    
    def setup_method(self):
        self.compressor = DataCompressor(CompressionType.GZIP)
    
    def test_compress_dict_data(self):
        """Test compressing dictionary data"""
        test_data = {"test": "data", "number": 123, "list": [1, 2, 3]}
        
        compressed_data, ratio = self.compressor.compress(test_data)
        
        assert isinstance(compressed_data, bytes)
        assert 0 <= ratio <= 1
        assert len(compressed_data) < len(json.dumps(test_data).encode('utf-8'))
    
    def test_compress_string_data(self):
        """Test compressing string data"""
        test_data = "This is a test string with repeated content. " * 100
        
        compressed_data, ratio = self.compressor.compress(test_data)
        
        assert isinstance(compressed_data, bytes)
        assert 0 <= ratio <= 1
        assert len(compressed_data) < len(test_data.encode('utf-8'))
    
    def test_decompress_data(self):
        """Test decompressing data"""
        original_data = {"test": "data", "number": 123}
        compressed_data, _ = self.compressor.compress(original_data)
        
        decompressed_data = self.compressor.decompress(compressed_data)
        decoded_data = json.loads(decompressed_data.decode('utf-8'))
        
        assert decoded_data == original_data
    
    def test_compression_stats(self):
        """Test compression statistics"""
        test_data = {"test": "data"}
        
        # Compress multiple times
        for _ in range(5):
            self.compressor.compress(test_data)
        
        stats = self.compressor.get_compression_stats()
        
        assert "compression_type" in stats
        assert "total_compressed" in stats
        assert "total_uncompressed" in stats
        assert "average_compression_ratio" in stats
        assert "total_savings" in stats
        assert stats["total_compressed"] > 0
        assert stats["total_uncompressed"] > 0

class TestFloorPartitioner:
    """Test floor partitioning functionality"""
    
    def setup_method(self):
        self.partitioner = FloorPartitioner(PartitionStrategy.FLOOR_BASED)
    
    def test_create_partition_id(self):
        """Test partition ID creation"""
        partition_id = self.partitioner.create_partition_id("floor1", "building1")
        assert partition_id == "building1_floor1"
        
        # Test grid-based partition ID
        self.partitioner.partition_strategy = PartitionStrategy.GRID_BASED
        grid_partition_id = self.partitioner.create_partition_id("floor1", "building1", 1, 2)
        assert grid_partition_id == "building1_floor1_grid_1_2"
    
    def test_partition_floor_data_floor_based(self):
        """Test floor-based partitioning"""
        floor_data = {
            "floor_id": "floor1",
            "building_id": "building1",
            "objects": [
                {"id": "obj1", "type": "light", "position": {"x": 100, "y": 100}},
                {"id": "obj2", "type": "outlet", "position": {"x": 200, "y": 200}},
                {"id": "obj3", "type": "sensor", "position": {"x": 300, "y": 300}}
            ]
        }
        
        partitions = self.partitioner.partition_floor_data(floor_data, "floor1", "building1")
        
        assert len(partitions) == 1
        partition = partitions[0]
        assert partition.partition_id == "building1_floor1"
        assert partition.object_count == 3
        assert partition.floor_id == "floor1"
        assert partition.building_id == "building1"
    
    def test_partition_floor_data_grid_based(self):
        """Test grid-based partitioning"""
        self.partitioner.partition_strategy = PartitionStrategy.GRID_BASED
        self.partitioner.grid_size = 100
        
        floor_data = {
            "floor_id": "floor1",
            "building_id": "building1",
            "objects": [
                {"id": "obj1", "type": "light", "position": {"x": 50, "y": 50}},
                {"id": "obj2", "type": "outlet", "position": {"x": 150, "y": 150}},
                {"id": "obj3", "type": "sensor", "position": {"x": 250, "y": 250}}
            ]
        }
        
        partitions = self.partitioner.partition_floor_data(floor_data, "floor1", "building1")
        
        assert len(partitions) == 3  # Should create 3 grid partitions
        partition_ids = [p.partition_id for p in partitions]
        assert "building1_floor1_grid_0_0" in partition_ids
        assert "building1_floor1_grid_1_1" in partition_ids
        assert "building1_floor1_grid_2_2" in partition_ids
    
    def test_partition_floor_data_object_based(self):
        """Test object-based partitioning"""
        self.partitioner.partition_strategy = PartitionStrategy.OBJECT_BASED
        
        floor_data = {
            "floor_id": "floor1",
            "building_id": "building1",
            "objects": [
                {"id": "obj1", "type": "light", "position": {"x": 100, "y": 100}},
                {"id": "obj2", "type": "outlet", "position": {"x": 200, "y": 200}},
                {"id": "obj3", "type": "light", "position": {"x": 300, "y": 300}}
            ]
        }
        
        partitions = self.partitioner.partition_floor_data(floor_data, "floor1", "building1")
        
        assert len(partitions) == 2  # Should create 2 partitions (light, outlet)
        partition_ids = [p.partition_id for p in partitions]
        assert any("light" in pid for pid in partition_ids)
        assert any("outlet" in pid for pid in partition_ids)
    
    def test_get_partition(self):
        """Test getting partition information"""
        partition_info = PartitionInfo(
            partition_id="test_partition",
            partition_type=PartitionStrategy.FLOOR_BASED,
            floor_id="floor1",
            building_id="building1"
        )
        self.partitioner.partitions["test_partition"] = partition_info
        
        retrieved = self.partitioner.get_partition("test_partition")
        assert retrieved == partition_info
        
        # Test non-existent partition
        assert self.partitioner.get_partition("non_existent") is None
    
    def test_get_floor_partitions(self):
        """Test getting floor partitions"""
        # Add test partitions
        partition1 = PartitionInfo(
            partition_id="building1_floor1",
            partition_type=PartitionStrategy.FLOOR_BASED,
            floor_id="floor1",
            building_id="building1"
        )
        partition2 = PartitionInfo(
            partition_id="building1_floor2",
            partition_type=PartitionStrategy.FLOOR_BASED,
            floor_id="floor2",
            building_id="building1"
        )
        partition3 = PartitionInfo(
            partition_id="building2_floor1",
            partition_type=PartitionStrategy.FLOOR_BASED,
            floor_id="floor1",
            building_id="building2"
        )
        
        self.partitioner.partitions.update({
            "building1_floor1": partition1,
            "building1_floor2": partition2,
            "building2_floor1": partition3
        })
        
        floor_partitions = self.partitioner.get_floor_partitions("floor1", "building1")
        assert len(floor_partitions) == 1
        assert floor_partitions[0].partition_id == "building1_floor1"
    
    def test_update_partition_access(self):
        """Test updating partition access statistics"""
        partition_info = PartitionInfo(
            partition_id="test_partition",
            partition_type=PartitionStrategy.FLOOR_BASED,
            floor_id="floor1",
            building_id="building1",
            access_count=5
        )
        self.partitioner.partitions["test_partition"] = partition_info
        
        original_access_count = partition_info.access_count
        original_last_accessed = partition_info.last_accessed
        
        self.partitioner.update_partition_access("test_partition")
        
        assert partition_info.access_count == original_access_count + 1
        assert partition_info.last_accessed > original_last_accessed

class TestLazyLoader:
    """Test lazy loading functionality"""
    
    @pytest.fixture
    def temp_storage(self):
        """Create temporary storage directory"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.mark.asyncio
    async def test_start_stop(self, temp_storage):
        """Test starting and stopping lazy loader"""
        loader = LazyLoader(temp_storage)
        
        await loader.start()
        assert loader.loading_workers > 0
        
        await loader.stop()
    
    @pytest.mark.asyncio
    async def test_load_partition_file_exists(self, temp_storage):
        """Test loading partition from existing file"""
        loader = LazyLoader(temp_storage)
        await loader.start()
        
        # Create test partition file
        test_data = {"test": "data"}
        partition_file = Path(temp_storage) / "test_partition.json.gz"
        
        import gzip
        with gzip.open(partition_file, 'wt', encoding='utf-8') as f:
            json.dump(test_data, f)
        
        # Load partition
        result = await loader.load_partition("test_partition")
        assert result is None  # Should be queued for loading
        
        # Wait for loading to complete
        await asyncio.sleep(0.1)
        
        # Check if loaded
        loaded_data = loader.get_loaded_partition("test_partition")
        assert loaded_data == test_data
        
        await loader.stop()
    
    @pytest.mark.asyncio
    async def test_load_partition_file_not_exists(self, temp_storage):
        """Test loading non-existent partition"""
        loader = LazyLoader(temp_storage)
        await loader.start()
        
        result = await loader.load_partition("non_existent")
        assert result is None
        
        # Check if not loaded
        loaded_data = loader.get_loaded_partition("non_existent")
        assert loaded_data is None
        
        await loader.stop()
    
    def test_is_partition_loaded(self, temp_storage):
        """Test checking if partition is loaded"""
        loader = LazyLoader(temp_storage)
        
        # Test unloaded partition
        assert not loader.is_partition_loaded("test_partition")
        
        # Test loaded partition
        loader.loaded_partitions["test_partition"] = {"test": "data"}
        assert loader.is_partition_loaded("test_partition")
    
    def test_unload_partition(self, temp_storage):
        """Test unloading partition"""
        loader = LazyLoader(temp_storage)
        
        # Load partition
        loader.loaded_partitions["test_partition"] = {"test": "data"}
        assert loader.is_partition_loaded("test_partition")
        
        # Unload partition
        loader.unload_partition("test_partition")
        assert not loader.is_partition_loaded("test_partition")
    
    def test_get_loading_stats(self, temp_storage):
        """Test getting loading statistics"""
        loader = LazyLoader(temp_storage)
        
        # Add some loaded partitions
        loader.loaded_partitions.update({
            "partition1": {"data": 1},
            "partition2": {"data": 2}
        })
        
        stats = loader.get_loading_stats()
        
        assert "loaded_partitions" in stats
        assert "max_loaded_partitions" in stats
        assert "queue_size" in stats
        assert "loading_workers" in stats
        assert stats["loaded_partitions"] == 2

class TestPerformanceMonitor:
    """Test performance monitoring functionality"""
    
    def setup_method(self):
        self.monitor = PerformanceMonitor()
    
    def test_start_end_operation(self):
        """Test operation timing"""
        operation_id = self.monitor.start_operation("test_operation", "partition1")
        
        # Simulate some work
        import time
        time.sleep(0.01)
        
        self.monitor.end_operation(operation_id, "partition1")
        
        # Check if metrics were updated
        partition_metrics = self.monitor.metrics.get("partition1")
        assert partition_metrics is not None
        assert partition_metrics.load_time > 0
    
    def test_record_cache_access(self):
        """Test recording cache access"""
        self.monitor.record_cache_access("partition1", True)  # Hit
        self.monitor.record_cache_access("partition1", False)  # Miss
        
        metrics = self.monitor.metrics["partition1"]
        assert metrics.cache_hits == 1
        assert metrics.cache_misses == 1
    
    def test_record_memory_usage(self):
        """Test recording memory usage"""
        self.monitor.record_memory_usage(1024 * 1024)  # 1MB
        self.monitor.record_memory_usage(2 * 1024 * 1024)  # 2MB
        
        assert len(self.monitor.memory_usage) == 2
        assert self.monitor.memory_usage[-1][1] == 2 * 1024 * 1024
    
    def test_record_access_latency(self):
        """Test recording access latency"""
        self.monitor.record_access_latency("partition1", 0.1)
        
        metrics = self.monitor.metrics["partition1"]
        assert metrics.access_latency == 0.1
    
    def test_get_performance_stats(self):
        """Test getting performance statistics"""
        # Add some test data
        self.monitor.record_cache_access("partition1", True)
        self.monitor.record_cache_access("partition1", False)
        self.monitor.record_memory_usage(1024 * 1024)
        
        stats = self.monitor.get_performance_stats()
        
        assert "total_partitions" in stats
        assert "memory_usage" in stats
        assert "operation_times" in stats
        assert "cache_stats" in stats
        assert "partition_metrics" in stats
        
        # Check cache stats
        cache_stats = stats["cache_stats"]
        assert cache_stats["total_hits"] == 1
        assert cache_stats["total_misses"] == 1
        assert cache_stats["hit_rate"] == 0.5

class TestDataPartitioningService:
    """Test main data partitioning service"""
    
    @pytest.fixture
    def temp_storage(self):
        """Create temporary storage directory"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def service(self, temp_storage):
        """Create data partitioning service"""
        return DataPartitioningService(temp_storage)
    
    @pytest.mark.asyncio
    async def test_start_stop(self, service):
        """Test starting and stopping service"""
        await service.start()
        await service.stop()
    
    @pytest.mark.asyncio
    async def test_partition_and_store_floor(self, service):
        """Test partitioning and storing floor data"""
        await service.start()
        
        floor_data = {
            "floor_id": "floor1",
            "building_id": "building1",
            "objects": [
                {"id": "obj1", "type": "light", "position": {"x": 100, "y": 100}},
                {"id": "obj2", "type": "outlet", "position": {"x": 200, "y": 200}}
            ]
        }
        
        partitions = await service.partition_and_store_floor(
            floor_data, "floor1", "building1", CompressionType.GZIP
        )
        
        assert len(partitions) == 1
        partition = partitions[0]
        assert partition.partition_id == "building1_floor1"
        assert partition.object_count == 2
        assert partition.compressed_size > 0
        assert partition.compression_ratio > 0
        
        await service.stop()
    
    @pytest.mark.asyncio
    async def test_load_floor_partitions_eager(self, service):
        """Test eager loading of floor partitions"""
        await service.start()
        
        # First partition and store
        floor_data = {
            "floor_id": "floor1",
            "building_id": "building1",
            "objects": [
                {"id": "obj1", "type": "light", "position": {"x": 100, "y": 100}}
            ]
        }
        
        await service.partition_and_store_floor(floor_data, "floor1", "building1")
        
        # Load with eager strategy
        result = await service.load_floor_partitions(
            "floor1", "building1", LoadStrategy.EAGER
        )
        
        assert "objects" in result
        assert len(result["objects"]) == 1
        assert "partitions" in result
        assert len(result["partitions"]) == 1
        
        await service.stop()
    
    @pytest.mark.asyncio
    async def test_load_floor_partitions_lazy(self, service):
        """Test lazy loading of floor partitions"""
        await service.start()
        
        # First partition and store
        floor_data = {
            "floor_id": "floor1",
            "building_id": "building1",
            "objects": [
                {"id": "obj1", "type": "light", "position": {"x": 100, "y": 100}}
            ]
        }
        
        await service.partition_and_store_floor(floor_data, "floor1", "building1")
        
        # Load with lazy strategy
        result = await service.load_floor_partitions(
            "floor1", "building1", LoadStrategy.LAZY
        )
        
        assert "lazy_loaded" in result
        assert result["lazy_loaded"] is True
        
        await service.stop()
    
    @pytest.mark.asyncio
    async def test_get_partition(self, service):
        """Test getting individual partition"""
        await service.start()
        
        # First partition and store
        floor_data = {
            "floor_id": "floor1",
            "building_id": "building1",
            "objects": [
                {"id": "obj1", "type": "light", "position": {"x": 100, "y": 100}}
            ]
        }
        
        await service.partition_and_store_floor(floor_data, "floor1", "building1")
        
        # Get partition
        partition_data = await service.get_partition("building1_floor1")
        
        assert partition_data is not None
        assert "objects" in partition_data or "partition_id" in partition_data
        
        await service.stop()
    
    def test_get_partition_info(self, service):
        """Test getting partition information"""
        # Add test partition
        partition_info = PartitionInfo(
            partition_id="test_partition",
            partition_type=PartitionStrategy.FLOOR_BASED,
            floor_id="floor1",
            building_id="building1"
        )
        service.partitioner.partitions["test_partition"] = partition_info
        
        retrieved = service.get_partition_info("test_partition")
        assert retrieved == partition_info
    
    def test_get_floor_partition_info(self, service):
        """Test getting floor partition information"""
        # Add test partitions
        partition1 = PartitionInfo(
            partition_id="building1_floor1",
            partition_type=PartitionStrategy.FLOOR_BASED,
            floor_id="floor1",
            building_id="building1"
        )
        partition2 = PartitionInfo(
            partition_id="building1_floor2",
            partition_type=PartitionStrategy.FLOOR_BASED,
            floor_id="floor2",
            building_id="building1"
        )
        
        service.partitioner.partitions.update({
            "building1_floor1": partition1,
            "building1_floor2": partition2
        })
        
        floor_partitions = service.get_floor_partition_info("floor1", "building1")
        assert len(floor_partitions) == 1
        assert floor_partitions[0].partition_id == "building1_floor1"
    
    def test_get_performance_stats(self, service):
        """Test getting performance statistics"""
        # Add some test data
        service.performance_monitor.record_cache_access("partition1", True)
        service.performance_monitor.record_memory_usage(1024 * 1024)
        
        stats = service.get_performance_stats()
        
        assert "compression" in stats
        assert "lazy_loading" in stats
        assert "partitions" in stats
        assert "performance_stats" in stats
    
    def test_optimize_partitions(self, service):
        """Test partition optimization"""
        # Add test partitions with different characteristics
        large_partition = PartitionInfo(
            partition_id="large_partition",
            partition_type=PartitionStrategy.FLOOR_BASED,
            floor_id="floor1",
            building_id="building1",
            data_size=10 * 1024 * 1024,  # 10MB
            access_count=0
        )
        
        low_compression_partition = PartitionInfo(
            partition_id="low_compression",
            partition_type=PartitionStrategy.FLOOR_BASED,
            floor_id="floor1",
            building_id="building1",
            compression_ratio=0.05,  # 5% compression
            access_count=5
        )
        
        service.partitioner.partitions.update({
            "large_partition": large_partition,
            "low_compression": low_compression_partition
        })
        
        optimization = service.optimize_partitions("floor1", "building1")
        
        assert "recommendations" in optimization
        assert len(optimization["recommendations"]) > 0
        
        # Check for specific recommendations
        recommendation_types = [r["type"] for r in optimization["recommendations"]]
        assert "split_large_partitions" in recommendation_types
        assert "improve_compression" in recommendation_types

class TestIntegration:
    """Integration tests for data partitioning"""
    
    @pytest.fixture
    def temp_storage(self):
        """Create temporary storage directory"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.mark.asyncio
    async def test_full_workflow(self, temp_storage):
        """Test complete data partitioning workflow"""
        service = DataPartitioningService(temp_storage)
        await service.start()
        
        # 1. Create floor data
        floor_data = {
            "floor_id": "floor1",
            "building_id": "building1",
            "objects": [
                {"id": "obj1", "type": "light", "position": {"x": 100, "y": 100}},
                {"id": "obj2", "type": "outlet", "position": {"x": 200, "y": 200}},
                {"id": "obj3", "type": "sensor", "position": {"x": 300, "y": 300}}
            ]
        }
        
        # 2. Partition and store
        partitions = await service.partition_and_store_floor(
            floor_data, "floor1", "building1"
        )
        assert len(partitions) == 1
        
        # 3. Load partitions
        loaded_data = await service.load_floor_partitions(
            "floor1", "building1", LoadStrategy.EAGER
        )
        assert len(loaded_data["objects"]) == 3
        
        # 4. Get performance stats
        stats = service.get_performance_stats()
        assert stats["partitions"]["total"] == 1
        assert stats["partitions"]["loaded"] == 1
        
        # 5. Optimize partitions
        optimization = service.optimize_partitions("floor1", "building1")
        assert "recommendations" in optimization
        
        await service.stop()
    
    @pytest.mark.asyncio
    async def test_multiple_floors(self, temp_storage):
        """Test handling multiple floors"""
        service = DataPartitioningService(temp_storage)
        await service.start()
        
        # Create multiple floors
        floors_data = [
            {
                "floor_id": "floor1",
                "building_id": "building1",
                "objects": [{"id": "obj1", "type": "light", "position": {"x": 100, "y": 100}}]
            },
            {
                "floor_id": "floor2",
                "building_id": "building1",
                "objects": [{"id": "obj2", "type": "outlet", "position": {"x": 200, "y": 200}}]
            }
        ]
        
        # Partition each floor
        for floor_data in floors_data:
            partitions = await service.partition_and_store_floor(
                floor_data, floor_data["floor_id"], floor_data["building_id"]
            )
            assert len(partitions) == 1
        
        # Get all floor partitions
        floor1_partitions = service.get_floor_partition_info("floor1", "building1")
        floor2_partitions = service.get_floor_partition_info("floor2", "building1")
        
        assert len(floor1_partitions) == 1
        assert len(floor2_partitions) == 1
        
        # Load both floors
        floor1_data = await service.load_floor_partitions("floor1", "building1")
        floor2_data = await service.load_floor_partitions("floor2", "building1")
        
        assert len(floor1_data["objects"]) == 1
        assert len(floor2_data["objects"]) == 1
        
        await service.stop()

if __name__ == "__main__":
    pytest.main([__file__]) 