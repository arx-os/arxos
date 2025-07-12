"""
Data Partitioning Service for Large Building Support
Handles floor-based data partitioning, lazy loading, compression, and performance monitoring
"""

import json
import gzip
import zlib
import pickle
import hashlib
from typing import Dict, List, Optional, Any, Tuple, Union, Set
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import logging
import asyncio
from pathlib import Path
import sqlite3
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

logger = logging.getLogger(__name__)

class PartitionStrategy(Enum):
    """Data partitioning strategies"""
    FLOOR_BASED = "floor_based"
    GRID_BASED = "grid_based"
    OBJECT_BASED = "object_based"
    HYBRID = "hybrid"

class CompressionType(Enum):
    """Compression types for floor data"""
    NONE = "none"
    GZIP = "gzip"
    ZLIB = "zlib"
    LZ4 = "lz4"
    SNAPPY = "snappy"

class LoadStrategy(Enum):
    """Data loading strategies"""
    EAGER = "eager"
    LAZY = "lazy"
    PROGRESSIVE = "progressive"
    ON_DEMAND = "on_demand"

@dataclass
class PartitionInfo:
    """Information about a data partition"""
    partition_id: str
    partition_type: PartitionStrategy
    floor_id: str
    building_id: str
    grid_x: Optional[int] = None
    grid_y: Optional[int] = None
    object_count: int = 0
    data_size: int = 0
    compressed_size: int = 0
    compression_ratio: float = 0.0
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_accessed: datetime = field(default_factory=datetime.utcnow)
    access_count: int = 0
    is_loaded: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class PerformanceMetrics:
    """Performance metrics for data partitioning"""
    partition_id: str
    load_time: float = 0.0
    compression_time: float = 0.0
    decompression_time: float = 0.0
    memory_usage: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    access_latency: float = 0.0
    last_updated: datetime = field(default_factory=datetime.utcnow)

class DataCompressor:
    """Handles data compression and decompression"""
    
    def __init__(self, compression_type: CompressionType = CompressionType.GZIP):
        self.compression_type = compression_type
        self.compression_stats = {
            "total_compressed": 0,
            "total_uncompressed": 0,
            "compression_ratios": []
        }
    
    def compress(self, data: Union[str, bytes, dict]) -> Tuple[bytes, float]:
        """Compress data and return compressed bytes with compression ratio"""
        start_time = datetime.utcnow()
        
        # Convert to bytes if needed
        if isinstance(data, dict):
            data_bytes = json.dumps(data, default=str).encode('utf-8')
        elif isinstance(data, str):
            data_bytes = data.encode('utf-8')
        else:
            data_bytes = data
        
        original_size = len(data_bytes)
        
        try:
            if self.compression_type == CompressionType.GZIP:
                compressed_data = gzip.compress(data_bytes, compresslevel=6)
            elif self.compression_type == CompressionType.ZLIB:
                compressed_data = zlib.compress(data_bytes, level=6)
            elif self.compression_type == CompressionType.LZ4:
                try:
                    import lz4.frame
                    compressed_data = lz4.frame.compress(data_bytes)
                except ImportError:
                    logger.warning("LZ4 not available, falling back to gzip")
                    compressed_data = gzip.compress(data_bytes, compresslevel=6)
            elif self.compression_type == CompressionType.SNAPPY:
                try:
                    import snappy
                    compressed_data = snappy.compress(data_bytes)
                except ImportError:
                    logger.warning("Snappy not available, falling back to gzip")
                    compressed_data = gzip.compress(data_bytes, compresslevel=6)
            else:
                compressed_data = data_bytes
            
            compressed_size = len(compressed_data)
            compression_ratio = 1 - (compressed_size / original_size) if original_size > 0 else 0
            
            # Update stats
            self.compression_stats["total_compressed"] += compressed_size
            self.compression_stats["total_uncompressed"] += original_size
            self.compression_stats["compression_ratios"].append(compression_ratio)
            
            compression_time = (datetime.utcnow() - start_time).total_seconds()
            logger.debug(f"Compressed {original_size} bytes to {compressed_size} bytes "
                        f"(ratio: {compression_ratio:.2%}) in {compression_time:.3f}s")
            
            return compressed_data, compression_ratio
            
        except Exception as e:
            logger.error(f"Compression failed: {e}")
            return data_bytes, 0.0
    
    def decompress(self, compressed_data: bytes) -> bytes:
        """Decompress data"""
        start_time = datetime.utcnow()
        
        try:
            if self.compression_type == CompressionType.GZIP:
                decompressed_data = gzip.decompress(compressed_data)
            elif self.compression_type == CompressionType.ZLIB:
                decompressed_data = zlib.decompress(compressed_data)
            elif self.compression_type == CompressionType.LZ4:
                try:
                    import lz4.frame
                    decompressed_data = lz4.frame.decompress(compressed_data)
                except ImportError:
                    logger.warning("LZ4 not available, falling back to gzip")
                    decompressed_data = gzip.decompress(compressed_data)
            elif self.compression_type == CompressionType.SNAPPY:
                try:
                    import snappy
                    decompressed_data = snappy.uncompress(compressed_data)
                except ImportError:
                    logger.warning("Snappy not available, falling back to gzip")
                    decompressed_data = gzip.decompress(compressed_data)
            else:
                decompressed_data = compressed_data
            
            decompression_time = (datetime.utcnow() - start_time).total_seconds()
            logger.debug(f"Decompressed {len(compressed_data)} bytes to {len(decompressed_data)} bytes "
                        f"in {decompression_time:.3f}s")
            
            return decompressed_data
            
        except Exception as e:
            logger.error(f"Decompression failed: {e}")
            return compressed_data
    
    def get_compression_stats(self) -> Dict[str, Any]:
        """Get compression statistics"""
        avg_ratio = (sum(self.compression_stats["compression_ratios"]) / 
                    len(self.compression_stats["compression_ratios"]) 
                    if self.compression_stats["compression_ratios"] else 0)
        
        return {
            "compression_type": self.compression_type.value,
            "total_compressed": self.compression_stats["total_compressed"],
            "total_uncompressed": self.compression_stats["total_uncompressed"],
            "average_compression_ratio": avg_ratio,
            "total_savings": self.compression_stats["total_uncompressed"] - self.compression_stats["total_compressed"]
        }

class FloorPartitioner:
    """Handles floor-based data partitioning"""
    
    def __init__(self, partition_strategy: PartitionStrategy = PartitionStrategy.FLOOR_BASED):
        self.partition_strategy = partition_strategy
        self.partitions: Dict[str, PartitionInfo] = {}
        self.grid_size = 1000  # Grid cell size in pixels
        self.max_partition_size = 10 * 1024 * 1024  # 10MB max partition size
        
    def create_partition_id(self, floor_id: str, building_id: str, 
                           grid_x: Optional[int] = None, grid_y: Optional[int] = None) -> str:
        """Create a unique partition ID"""
        if self.partition_strategy == PartitionStrategy.GRID_BASED and grid_x is not None and grid_y is not None:
            return f"{building_id}_{floor_id}_grid_{grid_x}_{grid_y}"
        else:
            return f"{building_id}_{floor_id}"
    
    def partition_floor_data(self, floor_data: Dict[str, Any], floor_id: str, 
                           building_id: str) -> List[PartitionInfo]:
        """Partition floor data based on strategy"""
        partitions = []
        
        if self.partition_strategy == PartitionStrategy.FLOOR_BASED:
            # Simple floor-based partitioning
            partition_id = self.create_partition_id(floor_id, building_id)
            partition_info = PartitionInfo(
                partition_id=partition_id,
                partition_type=self.partition_strategy,
                floor_id=floor_id,
                building_id=building_id,
                object_count=len(floor_data.get("objects", [])),
                data_size=len(json.dumps(floor_data)),
                metadata={"partition_strategy": "floor_based"}
            )
            partitions.append(partition_info)
            
        elif self.partition_strategy == PartitionStrategy.GRID_BASED:
            # Grid-based partitioning
            objects = floor_data.get("objects", [])
            grid_objects = self._group_objects_by_grid(objects)
            
            for (grid_x, grid_y), grid_obj_list in grid_objects.items():
                partition_id = self.create_partition_id(floor_id, building_id, grid_x, grid_y)
                grid_data = {
                    "objects": grid_obj_list,
                    "grid_info": {"x": grid_x, "y": grid_y, "size": self.grid_size}
                }
                
                partition_info = PartitionInfo(
                    partition_id=partition_id,
                    partition_type=self.partition_strategy,
                    floor_id=floor_id,
                    building_id=building_id,
                    grid_x=grid_x,
                    grid_y=grid_y,
                    object_count=len(grid_obj_list),
                    data_size=len(json.dumps(grid_data)),
                    metadata={"partition_strategy": "grid_based", "grid_data": grid_data}
                )
                partitions.append(partition_info)
                
        elif self.partition_strategy == PartitionStrategy.OBJECT_BASED:
            # Object-based partitioning
            objects = floor_data.get("objects", [])
            object_groups = self._group_objects_by_type(objects)
            
            for object_type, type_objects in object_groups.items():
                partition_id = f"{building_id}_{floor_id}_objects_{object_type}"
                type_data = {"objects": type_objects, "object_type": object_type}
                
                partition_info = PartitionInfo(
                    partition_id=partition_id,
                    partition_type=self.partition_strategy,
                    floor_id=floor_id,
                    building_id=building_id,
                    object_count=len(type_objects),
                    data_size=len(json.dumps(type_data)),
                    metadata={"partition_strategy": "object_based", "object_type": object_type}
                )
                partitions.append(partition_info)
        
        # Store partitions
        for partition in partitions:
            self.partitions[partition.partition_id] = partition
        
        return partitions
    
    def _group_objects_by_grid(self, objects: List[Dict[str, Any]]) -> Dict[Tuple[int, int], List[Dict[str, Any]]]:
        """Group objects by grid coordinates"""
        grid_objects = {}
        
        for obj in objects:
            # Extract position from object
            position = obj.get("position", {})
            x = position.get("x", 0)
            y = position.get("y", 0)
            
            # Calculate grid coordinates
            grid_x = int(x // self.grid_size)
            grid_y = int(y // self.grid_size)
            grid_key = (grid_x, grid_y)
            
            if grid_key not in grid_objects:
                grid_objects[grid_key] = []
            grid_objects[grid_key].append(obj)
        
        return grid_objects
    
    def _group_objects_by_type(self, objects: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Group objects by type"""
        type_objects = {}
        
        for obj in objects:
            obj_type = obj.get("type", "unknown")
            if obj_type not in type_objects:
                type_objects[obj_type] = []
            type_objects[obj_type].append(obj)
        
        return type_objects
    
    def get_partition(self, partition_id: str) -> Optional[PartitionInfo]:
        """Get partition information"""
        return self.partitions.get(partition_id)
    
    def get_floor_partitions(self, floor_id: str, building_id: str) -> List[PartitionInfo]:
        """Get all partitions for a floor"""
        floor_partitions = []
        for partition in self.partitions.values():
            if partition.floor_id == floor_id and partition.building_id == building_id:
                floor_partitions.append(partition)
        return floor_partitions
    
    def update_partition_access(self, partition_id: str):
        """Update partition access statistics"""
        if partition_id in self.partitions:
            partition = self.partitions[partition_id]
            partition.last_accessed = datetime.utcnow()
            partition.access_count += 1

class LazyLoader:
    """Handles lazy loading of partitioned data"""
    
    def __init__(self, storage_path: str = "./data/partitions"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.loaded_partitions: Dict[str, Any] = {}
        self.loading_queue = asyncio.Queue()
        self.loading_workers = 4
        self.max_loaded_partitions = 100
        self.loading_lock = threading.Lock()
        
    async def start(self):
        """Start lazy loading workers"""
        for _ in range(self.loading_workers):
            asyncio.create_task(self._loading_worker())
        logger.info(f"Started {self.loading_workers} lazy loading workers")
    
    async def stop(self):
        """Stop lazy loading workers"""
        # Signal workers to stop
        for _ in range(self.loading_workers):
            await self.loading_queue.put(None)
        logger.info("Stopped lazy loading workers")
    
    async def _loading_worker(self):
        """Background worker for loading partitions"""
        while True:
            try:
                task = await self.loading_queue.get()
                if task is None:  # Stop signal
                    break
                
                partition_id, load_callback = task
                await self._load_partition(partition_id, load_callback)
                
            except Exception as e:
                logger.error(f"Error in loading worker: {e}")
    
    async def _load_partition(self, partition_id: str, load_callback):
        """Load a partition from storage"""
        try:
            partition_file = self.storage_path / f"{partition_id}.json.gz"
            
            if partition_file.exists():
                # Load compressed data
                with gzip.open(partition_file, 'rt', encoding='utf-8') as f:
                    data = json.load(f)
                
                with self.loading_lock:
                    self.loaded_partitions[partition_id] = data
                    
                    # Enforce memory limit
                    if len(self.loaded_partitions) > self.max_loaded_partitions:
                        self._evict_least_used()
                
                if load_callback:
                    await load_callback(partition_id, data)
                
                logger.debug(f"Loaded partition: {partition_id}")
            else:
                logger.warning(f"Partition file not found: {partition_id}")
                
        except Exception as e:
            logger.error(f"Failed to load partition {partition_id}: {e}")
    
    def _evict_least_used(self):
        """Evict least recently used partitions"""
        # Simple LRU eviction - in production, use a proper LRU cache
        if len(self.loaded_partitions) > self.max_loaded_partitions:
            # Remove oldest partition (simple implementation)
            oldest_key = next(iter(self.loaded_partitions))
            del self.loaded_partitions[oldest_key]
    
    async def load_partition(self, partition_id: str, load_callback=None) -> Optional[Any]:
        """Load a partition (returns immediately if already loaded)"""
        # Check if already loaded
        if partition_id in self.loaded_partitions:
            return self.loaded_partitions[partition_id]
        
        # Queue for loading
        await self.loading_queue.put((partition_id, load_callback))
        return None
    
    def get_loaded_partition(self, partition_id: str) -> Optional[Any]:
        """Get a loaded partition"""
        return self.loaded_partitions.get(partition_id)
    
    def is_partition_loaded(self, partition_id: str) -> bool:
        """Check if partition is loaded"""
        return partition_id in self.loaded_partitions
    
    def unload_partition(self, partition_id: str):
        """Unload a partition from memory"""
        if partition_id in self.loaded_partitions:
            del self.loaded_partitions[partition_id]
            logger.debug(f"Unloaded partition: {partition_id}")
    
    def get_loading_stats(self) -> Dict[str, Any]:
        """Get lazy loading statistics"""
        return {
            "loaded_partitions": len(self.loaded_partitions),
            "max_loaded_partitions": self.max_loaded_partitions,
            "queue_size": self.loading_queue.qsize(),
            "loading_workers": self.loading_workers
        }

class PerformanceMonitor:
    """Monitors performance of data partitioning operations"""
    
    def __init__(self):
        self.metrics: Dict[str, PerformanceMetrics] = {}
        self.operation_times: Dict[str, List[float]] = {}
        self.memory_usage: List[Tuple[datetime, int]] = []
        self.monitoring_interval = 60  # seconds
        
    def start_operation(self, operation_name: str, partition_id: str = None) -> str:
        """Start timing an operation"""
        operation_id = f"{operation_name}_{partition_id}_{datetime.utcnow().timestamp()}"
        self.operation_times[operation_id] = [datetime.utcnow().timestamp()]
        return operation_id
    
    def end_operation(self, operation_id: str, partition_id: str = None):
        """End timing an operation"""
        if operation_id in self.operation_times:
            start_time = self.operation_times[operation_id][0]
            end_time = datetime.utcnow().timestamp()
            duration = end_time - start_time
            
            # Store operation time
            operation_name = operation_id.split('_')[0]
            if operation_name not in self.operation_times:
                self.operation_times[operation_name] = []
            self.operation_times[operation_name].append(duration)
            
            # Update partition metrics if applicable
            if partition_id:
                if partition_id not in self.metrics:
                    self.metrics[partition_id] = PerformanceMetrics(partition_id=partition_id)
                
                metrics = self.metrics[partition_id]
                if operation_name == "load":
                    metrics.load_time = duration
                elif operation_name == "compress":
                    metrics.compression_time = duration
                elif operation_name == "decompress":
                    metrics.decompression_time = duration
                
                metrics.last_updated = datetime.utcnow()
            
            del self.operation_times[operation_id]
    
    def record_cache_access(self, partition_id: str, hit: bool):
        """Record cache access"""
        if partition_id not in self.metrics:
            self.metrics[partition_id] = PerformanceMetrics(partition_id=partition_id)
        
        metrics = self.metrics[partition_id]
        if hit:
            metrics.cache_hits += 1
        else:
            metrics.cache_misses += 1
    
    def record_memory_usage(self, usage_bytes: int):
        """Record memory usage"""
        self.memory_usage.append((datetime.utcnow(), usage_bytes))
        
        # Keep only last 1000 records
        if len(self.memory_usage) > 1000:
            self.memory_usage = self.memory_usage[-1000:]
    
    def record_access_latency(self, partition_id: str, latency: float):
        """Record access latency"""
        if partition_id not in self.metrics:
            self.metrics[partition_id] = PerformanceMetrics(partition_id=partition_id)
        
        metrics = self.metrics[partition_id]
        metrics.access_latency = latency
        metrics.last_updated = datetime.utcnow()
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get comprehensive performance statistics"""
        stats = {
            "total_partitions": len(self.metrics),
            "memory_usage": self._get_memory_stats(),
            "operation_times": self._get_operation_stats(),
            "cache_stats": self._get_cache_stats(),
            "partition_metrics": {}
        }
        
        for partition_id, metrics in self.metrics.items():
            stats["partition_metrics"][partition_id] = {
                "load_time": metrics.load_time,
                "compression_time": metrics.compression_time,
                "decompression_time": metrics.decompression_time,
                "cache_hits": metrics.cache_hits,
                "cache_misses": metrics.cache_misses,
                "access_latency": metrics.access_latency,
                "hit_rate": (metrics.cache_hits / (metrics.cache_hits + metrics.cache_misses) 
                           if (metrics.cache_hits + metrics.cache_misses) > 0 else 0)
            }
        
        return stats
    
    def _get_memory_stats(self) -> Dict[str, Any]:
        """Get memory usage statistics"""
        if not self.memory_usage:
            return {"current": 0, "average": 0, "peak": 0}
        
        current = self.memory_usage[-1][1] if self.memory_usage else 0
        usages = [usage for _, usage in self.memory_usage]
        
        return {
            "current": current,
            "average": sum(usages) / len(usages),
            "peak": max(usages),
            "trend": "increasing" if len(usages) > 1 and usages[-1] > usages[-2] else "stable"
        }
    
    def _get_operation_stats(self) -> Dict[str, Any]:
        """Get operation timing statistics"""
        stats = {}
        
        for operation_name, times in self.operation_times.items():
            if isinstance(times, list) and times:
                stats[operation_name] = {
                    "count": len(times),
                    "average": sum(times) / len(times),
                    "min": min(times),
                    "max": max(times)
                }
        
        return stats
    
    def _get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_hits = sum(m.cache_hits for m in self.metrics.values())
        total_misses = sum(m.cache_misses for m in self.metrics.values())
        total_accesses = total_hits + total_misses
        
        return {
            "total_hits": total_hits,
            "total_misses": total_misses,
            "total_accesses": total_accesses,
            "hit_rate": total_hits / total_accesses if total_accesses > 0 else 0
        }

class DataPartitioningService:
    """Main service for data partitioning and management"""
    
    def __init__(self, storage_path: str = "./data/partitions"):
        self.partitioner = FloorPartitioner()
        self.compressor = DataCompressor()
        self.lazy_loader = LazyLoader(storage_path)
        self.performance_monitor = PerformanceMonitor()
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
    async def start(self):
        """Start the data partitioning service"""
        await self.lazy_loader.start()
        logger.info("Data partitioning service started")
    
    async def stop(self):
        """Stop the data partitioning service"""
        await self.lazy_loader.stop()
        logger.info("Data partitioning service stopped")
    
    async def partition_and_store_floor(self, floor_data: Dict[str, Any], 
                                      floor_id: str, building_id: str,
                                      compression_type: CompressionType = CompressionType.GZIP) -> List[PartitionInfo]:
        """Partition floor data and store partitions"""
        operation_id = self.performance_monitor.start_operation("partition", floor_id)
        
        try:
            # Create partitions
            partitions = self.partitioner.partition_floor_data(floor_data, floor_id, building_id)
            
            # Store each partition
            for partition in partitions:
                await self._store_partition(partition, compression_type)
            
            self.performance_monitor.end_operation(operation_id, floor_id)
            logger.info(f"Partitioned floor {floor_id} into {len(partitions)} partitions")
            
            return partitions
            
        except Exception as e:
            logger.error(f"Failed to partition floor {floor_id}: {e}")
            return []
    
    async def _store_partition(self, partition: PartitionInfo, compression_type: CompressionType):
        """Store a partition with compression"""
        operation_id = self.performance_monitor.start_operation("compress", partition.partition_id)
        
        try:
            # Get partition data
            partition_data = partition.symbol_metadata.get("grid_data") or partition.symbol_metadata.get("object_data")
            if not partition_data:
                # Create basic partition data
                partition_data = {
                    "partition_id": partition.partition_id,
                    "floor_id": partition.floor_id,
                    "building_id": partition.building_id,
                    "partition_type": partition.partition_type.value,
                    "object_count": partition.object_count,
                    "created_at": partition.created_at.isoformat()
                }
            
            # Compress data
            compressed_data, compression_ratio = self.compressor.compress(partition_data)
            
            # Update partition info
            partition.compressed_size = len(compressed_data)
            partition.compression_ratio = compression_ratio
            
            # Store to file
            partition_file = self.storage_path / f"{partition.partition_id}.json.gz"
            with gzip.open(partition_file, 'wb') as f:
                f.write(compressed_data)
            
            self.performance_monitor.end_operation(operation_id, partition.partition_id)
            logger.debug(f"Stored partition {partition.partition_id} "
                        f"({partition.data_size} -> {partition.compressed_size} bytes)")
            
        except Exception as e:
            logger.error(f"Failed to store partition {partition.partition_id}: {e}")
    
    async def load_floor_partitions(self, floor_id: str, building_id: str, 
                                  load_strategy: LoadStrategy = LoadStrategy.LAZY) -> Dict[str, Any]:
        """Load floor partitions based on strategy"""
        operation_id = self.performance_monitor.start_operation("load_floor", floor_id)
        
        try:
            partitions = self.partitioner.get_floor_partitions(floor_id, building_id)
            
            if load_strategy == LoadStrategy.EAGER:
                # Load all partitions immediately
                floor_data = await self._load_all_partitions(partitions)
            elif load_strategy == LoadStrategy.LAZY:
                # Load partitions on demand
                floor_data = await self._load_partitions_lazy(partitions)
            elif load_strategy == LoadStrategy.PROGRESSIVE:
                # Load partitions progressively
                floor_data = await self._load_partitions_progressive(partitions)
            else:  # ON_DEMAND
                # Return partition info only
                floor_data = {"partitions": [p.partition_id for p in partitions]}
            
            self.performance_monitor.end_operation(operation_id, floor_id)
            return floor_data
            
        except Exception as e:
            logger.error(f"Failed to load floor partitions for {floor_id}: {e}")
            return {}
    
    async def _load_all_partitions(self, partitions: List[PartitionInfo]) -> Dict[str, Any]:
        """Load all partitions immediately"""
        floor_data = {"objects": [], "partitions": {}}
        
        for partition in partitions:
            partition_data = await self._load_single_partition(partition.partition_id)
            if partition_data:
                # Merge objects
                if "objects" in partition_data:
                    floor_data["objects"].extend(partition_data["objects"])
                
                # Store partition data
                floor_data["partitions"][partition.partition_id] = partition_data
        
        return floor_data
    
    async def _load_partitions_lazy(self, partitions: List[PartitionInfo]) -> Dict[str, Any]:
        """Load partitions lazily"""
        floor_data = {"objects": [], "partitions": {}, "lazy_loaded": True}
        
        # Queue all partitions for loading
        for partition in partitions:
            await self.lazy_loader.load_partition(
                partition.partition_id,
                lambda pid, data: self._on_partition_loaded(pid, data, floor_data)
            )
        
        return floor_data
    
    async def _load_partitions_progressive(self, partitions: List[PartitionInfo]) -> Dict[str, Any]:
        """Load partitions progressively"""
        floor_data = {"objects": [], "partitions": {}, "progressive_loaded": True}
        
        # Load partitions in batches
        batch_size = 3
        for i in range(0, len(partitions), batch_size):
            batch = partitions[i:i + batch_size]
            
            # Load batch
            for partition in batch:
                partition_data = await self._load_single_partition(partition.partition_id)
                if partition_data:
                    if "objects" in partition_data:
                        floor_data["objects"].extend(partition_data["objects"])
                    floor_data["partitions"][partition.partition_id] = partition_data
            
            # Small delay between batches
            await asyncio.sleep(0.1)
        
        return floor_data
    
    async def _load_single_partition(self, partition_id: str) -> Optional[Dict[str, Any]]:
        """Load a single partition"""
        start_time = datetime.utcnow()
        
        # Check if already loaded
        loaded_data = self.lazy_loader.get_loaded_partition(partition_id)
        if loaded_data:
            self.performance_monitor.record_cache_access(partition_id, True)
            return loaded_data
        
        self.performance_monitor.record_cache_access(partition_id, False)
        
        # Load from storage
        partition_file = self.storage_path / f"{partition_id}.json.gz"
        
        if partition_file.exists():
            try:
                with gzip.open(partition_file, 'rt', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Store in lazy loader
                self.lazy_loader.loaded_partitions[partition_id] = data
                
                # Update access stats
                self.partitioner.update_partition_access(partition_id)
                
                # Record latency
                latency = (datetime.utcnow() - start_time).total_seconds()
                self.performance_monitor.record_access_latency(partition_id, latency)
                
                return data
                
            except Exception as e:
                logger.error(f"Failed to load partition {partition_id}: {e}")
        
        return None
    
    def _on_partition_loaded(self, partition_id: str, data: Dict[str, Any], floor_data: Dict[str, Any]):
        """Callback when partition is loaded"""
        if "objects" in data:
            floor_data["objects"].extend(data["objects"])
        floor_data["partitions"][partition_id] = data
    
    async def get_partition(self, partition_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific partition"""
        return await self._load_single_partition(partition_id)
    
    def get_partition_info(self, partition_id: str) -> Optional[PartitionInfo]:
        """Get partition information"""
        return self.partitioner.get_partition(partition_id)
    
    def get_floor_partition_info(self, floor_id: str, building_id: str) -> List[PartitionInfo]:
        """Get partition information for a floor"""
        return self.partitioner.get_floor_partitions(floor_id, building_id)
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get comprehensive performance statistics"""
        stats = self.performance_monitor.get_performance_stats()
        stats.update({
            "compression": self.compressor.get_compression_stats(),
            "lazy_loading": self.lazy_loader.get_loading_stats(),
            "partitions": {
                "total": len(self.partitioner.partitions),
                "loaded": len(self.lazy_loader.loaded_partitions)
            }
        })
        return stats
    
    def optimize_partitions(self, floor_id: str, building_id: str) -> Dict[str, Any]:
        """Optimize partitions for a floor"""
        partitions = self.partitioner.get_floor_partitions(floor_id, building_id)
        
        optimization_results = {
            "floor_id": floor_id,
            "total_partitions": len(partitions),
            "total_objects": sum(p.object_count for p in partitions),
            "total_size": sum(p.data_size for p in partitions),
            "total_compressed_size": sum(p.compressed_size for p in partitions),
            "average_compression_ratio": sum(p.compression_ratio for p in partitions) / len(partitions) if partitions else 0,
            "recommendations": []
        }
        
        # Analyze partition sizes
        large_partitions = [p for p in partitions if p.data_size > 5 * 1024 * 1024]  # 5MB
        if large_partitions:
            optimization_results["recommendations"].append({
                "type": "split_large_partitions",
                "description": f"Consider splitting {len(large_partitions)} large partitions",
                "partitions": [p.partition_id for p in large_partitions]
            })
        
        # Analyze compression ratios
        low_compression = [p for p in partitions if p.compression_ratio < 0.1]
        if low_compression:
            optimization_results["recommendations"].append({
                "type": "improve_compression",
                "description": f"Consider different compression for {len(low_compression)} partitions",
                "partitions": [p.partition_id for p in low_compression]
            })
        
        # Analyze access patterns
        unused_partitions = [p for p in partitions if p.access_count == 0]
        if unused_partitions:
            optimization_results["recommendations"].append({
                "type": "archive_unused",
                "description": f"Consider archiving {len(unused_partitions)} unused partitions",
                "partitions": [p.partition_id for p in unused_partitions]
            })
        
        return optimization_results

# Global service instance - lazy singleton
_data_partitioning_service = None

def get_data_partitioning_service() -> DataPartitioningService:
    """Get the global data partitioning service instance (lazy singleton)"""
    global _data_partitioning_service
    if _data_partitioning_service is None:
        _data_partitioning_service = DataPartitioningService()
    return _data_partitioning_service

# For backward compatibility
data_partitioning_service = get_data_partitioning_service() 