"""
Data Partitioning Router
Handles floor-based data partitioning, lazy loading, compression, and performance monitoring APIs
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import Dict, List, Optional, Any
import json
import logging
from datetime import datetime

from arx_svg_parser.services.data_partitioning import (
    data_partitioning_service, PartitionStrategy, CompressionType, LoadStrategy
)
from arx_svg_parser.utils.auth import get_current_user_optional

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/partitioning", tags=["partitioning"])

@router.post("/partition-floor")
async def partition_floor(
    floor_data: Dict[str, Any],
    floor_id: str,
    building_id: str,
    partition_strategy: PartitionStrategy = PartitionStrategy.FLOOR_BASED,
    compression_type: CompressionType = CompressionType.GZIP,
    background_tasks: BackgroundTasks = None,
    current_user: Optional[Dict] = Depends(get_current_user_optional)
):
    """Partition floor data and store partitions"""
    try:
        # Update partitioner strategy
        data_partitioning_service.partitioner.partition_strategy = partition_strategy
        
        # Partition and store floor data
        partitions = await data_partitioning_service.partition_and_store_floor(
            floor_data, floor_id, building_id, compression_type
        )
        
        # Return partition information
        partition_info = []
        for partition in partitions:
            partition_info.append({
                "partition_id": partition.partition_id,
                "partition_type": partition.partition_type.value,
                "floor_id": partition.floor_id,
                "building_id": partition.building_id,
                "grid_x": partition.grid_x,
                "grid_y": partition.grid_y,
                "object_count": partition.object_count,
                "data_size": partition.data_size,
                "compressed_size": partition.compressed_size,
                "compression_ratio": partition.compression_ratio,
                "created_at": partition.created_at.isoformat(),
                "metadata": partition.metadata
            })
        
        return JSONResponse({
            "success": True,
            "floor_id": floor_id,
            "building_id": building_id,
            "partition_strategy": partition_strategy.value,
            "compression_type": compression_type.value,
            "partitions": partition_info,
            "total_partitions": len(partitions),
            "total_objects": sum(p.object_count for p in partitions),
            "total_size": sum(p.data_size for p in partitions),
            "total_compressed_size": sum(p.compressed_size for p in partitions),
            "timestamp": datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Failed to partition floor {floor_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to partition floor: {str(e)}")

@router.get("/floor-partitions/{building_id}/{floor_id}")
async def get_floor_partitions(
    building_id: str,
    floor_id: str,
    current_user: Optional[Dict] = Depends(get_current_user_optional)
):
    """Get partition information for a floor"""
    try:
        partitions = data_partitioning_service.get_floor_partition_info(floor_id, building_id)
        
        partition_info = []
        for partition in partitions:
            partition_info.append({
                "partition_id": partition.partition_id,
                "partition_type": partition.partition_type.value,
                "floor_id": partition.floor_id,
                "building_id": partition.building_id,
                "grid_x": partition.grid_x,
                "grid_y": partition.grid_y,
                "object_count": partition.object_count,
                "data_size": partition.data_size,
                "compressed_size": partition.compressed_size,
                "compression_ratio": partition.compression_ratio,
                "created_at": partition.created_at.isoformat(),
                "last_accessed": partition.last_accessed.isoformat(),
                "access_count": partition.access_count,
                "is_loaded": data_partitioning_service.lazy_loader.is_partition_loaded(partition.partition_id),
                "metadata": partition.metadata
            })
        
        return JSONResponse({
            "building_id": building_id,
            "floor_id": floor_id,
            "partitions": partition_info,
            "total_partitions": len(partitions),
            "loaded_partitions": len([p for p in partitions if data_partitioning_service.lazy_loader.is_partition_loaded(p.partition_id)]),
            "timestamp": datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Failed to get floor partitions for {floor_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get floor partitions: {str(e)}")

@router.post("/load-floor")
async def load_floor_partitions(
    building_id: str,
    floor_id: str,
    load_strategy: LoadStrategy = LoadStrategy.LAZY,
    current_user: Optional[Dict] = Depends(get_current_user_optional)
):
    """Load floor partitions using specified strategy"""
    try:
        floor_data = await data_partitioning_service.load_floor_partitions(
            floor_id, building_id, load_strategy
        )
        
        return JSONResponse({
            "success": True,
            "building_id": building_id,
            "floor_id": floor_id,
            "load_strategy": load_strategy.value,
            "objects_loaded": len(floor_data.get("objects", [])),
            "partitions_loaded": len(floor_data.get("partitions", {})),
            "lazy_loaded": floor_data.get("lazy_loaded", False),
            "progressive_loaded": floor_data.get("progressive_loaded", False),
            "timestamp": datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Failed to load floor partitions for {floor_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to load floor partitions: {str(e)}")

@router.get("/partition/{partition_id}")
async def get_partition(
    partition_id: str,
    current_user: Optional[Dict] = Depends(get_current_user_optional)
):
    """Get a specific partition"""
    try:
        partition_data = await data_partitioning_service.get_partition(partition_id)
        
        if partition_data is None:
            raise HTTPException(status_code=404, detail="Partition not found")
        
        partition_info = data_partitioning_service.get_partition_info(partition_id)
        
        return JSONResponse({
            "partition_id": partition_id,
            "partition_info": {
                "partition_type": partition_info.partition_type.value if partition_info else None,
                "floor_id": partition_info.floor_id if partition_info else None,
                "building_id": partition_info.building_id if partition_info else None,
                "object_count": partition_info.object_count if partition_info else 0,
                "data_size": partition_info.data_size if partition_info else 0,
                "compressed_size": partition_info.compressed_size if partition_info else 0,
                "compression_ratio": partition_info.compression_ratio if partition_info else 0,
                "access_count": partition_info.access_count if partition_info else 0,
                "last_accessed": partition_info.last_accessed.isoformat() if partition_info else None
            },
            "data": partition_data,
            "timestamp": datetime.utcnow().isoformat()
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get partition {partition_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get partition: {str(e)}")

@router.post("/load-partition")
async def load_partition(
    partition_id: str,
    current_user: Optional[Dict] = Depends(get_current_user_optional)
):
    """Load a specific partition"""
    try:
        partition_data = await data_partitioning_service.get_partition(partition_id)
        
        if partition_data is None:
            raise HTTPException(status_code=404, detail="Partition not found")
        
        return JSONResponse({
            "success": True,
            "partition_id": partition_id,
            "loaded": True,
            "timestamp": datetime.utcnow().isoformat()
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to load partition {partition_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to load partition: {str(e)}")

@router.delete("/unload-partition/{partition_id}")
async def unload_partition(
    partition_id: str,
    current_user: Optional[Dict] = Depends(get_current_user_optional)
):
    """Unload a partition from memory"""
    try:
        data_partitioning_service.lazy_loader.unload_partition(partition_id)
        
        return JSONResponse({
            "success": True,
            "partition_id": partition_id,
            "unloaded": True,
            "timestamp": datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Failed to unload partition {partition_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to unload partition: {str(e)}")

@router.get("/performance-stats")
async def get_performance_stats(
    current_user: Optional[Dict] = Depends(get_current_user_optional)
):
    """Get comprehensive performance statistics"""
    try:
        stats = data_partitioning_service.get_performance_stats()
        
        return JSONResponse({
            "performance_stats": stats,
            "timestamp": datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Failed to get performance stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get performance stats: {str(e)}")

@router.get("/optimize-floor/{building_id}/{floor_id}")
async def optimize_floor_partitions(
    building_id: str,
    floor_id: str,
    current_user: Optional[Dict] = Depends(get_current_user_optional)
):
    """Get optimization recommendations for a floor"""
    try:
        optimization_results = data_partitioning_service.optimize_partitions(floor_id, building_id)
        
        return JSONResponse({
            "optimization_results": optimization_results,
            "timestamp": datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Failed to optimize floor {floor_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to optimize floor: {str(e)}")

@router.post("/compress-partition")
async def compress_partition(
    partition_id: str,
    compression_type: CompressionType = CompressionType.GZIP,
    current_user: Optional[Dict] = Depends(get_current_user_optional)
):
    """Recompress a partition with different compression"""
    try:
        # Get partition data
        partition_data = await data_partitioning_service.get_partition(partition_id)
        
        if partition_data is None:
            raise HTTPException(status_code=404, detail="Partition not found")
        
        # Compress with new type
        compressed_data, compression_ratio = data_partitioning_service.compressor.compress(partition_data)
        
        # Update partition info
        partition_info = data_partitioning_service.get_partition_info(partition_id)
        if partition_info:
            partition_info.compressed_size = len(compressed_data)
            partition_info.compression_ratio = compression_ratio
        
        return JSONResponse({
            "success": True,
            "partition_id": partition_id,
            "compression_type": compression_type.value,
            "original_size": len(json.dumps(partition_data)),
            "compressed_size": len(compressed_data),
            "compression_ratio": compression_ratio,
            "timestamp": datetime.utcnow().isoformat()
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to compress partition {partition_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to compress partition: {str(e)}")

@router.get("/compression-stats")
async def get_compression_stats(
    current_user: Optional[Dict] = Depends(get_current_user_optional)
):
    """Get compression statistics"""
    try:
        stats = data_partitioning_service.compressor.get_compression_stats()
        
        return JSONResponse({
            "compression_stats": stats,
            "timestamp": datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Failed to get compression stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get compression stats: {str(e)}")

@router.get("/lazy-loading-stats")
async def get_lazy_loading_stats(
    current_user: Optional[Dict] = Depends(get_current_user_optional)
):
    """Get lazy loading statistics"""
    try:
        stats = data_partitioning_service.lazy_loader.get_loading_stats()
        
        return JSONResponse({
            "lazy_loading_stats": stats,
            "timestamp": datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Failed to get lazy loading stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get lazy loading stats: {str(e)}")

@router.post("/batch-partition")
async def batch_partition_floors(
    floors_data: List[Dict[str, Any]],
    partition_strategy: PartitionStrategy = PartitionStrategy.FLOOR_BASED,
    compression_type: CompressionType = CompressionType.GZIP,
    background_tasks: BackgroundTasks = None,
    current_user: Optional[Dict] = Depends(get_current_user_optional)
):
    """Partition multiple floors in batch"""
    try:
        results = []
        
        for floor_data in floors_data:
            floor_id = floor_data.get("floor_id")
            building_id = floor_data.get("building_id")
            
            if not floor_id or not building_id:
                continue
            
            try:
                partitions = await data_partitioning_service.partition_and_store_floor(
                    floor_data, floor_id, building_id, compression_type
                )
                
                results.append({
                    "floor_id": floor_id,
                    "building_id": building_id,
                    "success": True,
                    "partitions_created": len(partitions),
                    "total_objects": sum(p.object_count for p in partitions),
                    "total_size": sum(p.data_size for p in partitions)
                })
                
            except Exception as e:
                results.append({
                    "floor_id": floor_id,
                    "building_id": building_id,
                    "success": False,
                    "error": str(e)
                })
        
        return JSONResponse({
            "batch_results": results,
            "total_floors": len(floors_data),
            "successful_floors": len([r for r in results if r["success"]]),
            "failed_floors": len([r for r in results if not r["success"]]),
            "partition_strategy": partition_strategy.value,
            "compression_type": compression_type.value,
            "timestamp": datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Failed to batch partition floors: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to batch partition floors: {str(e)}")

@router.get("/partition-status/{partition_id}")
async def get_partition_status(
    partition_id: str,
    current_user: Optional[Dict] = Depends(get_current_user_optional)
):
    """Get detailed status of a partition"""
    try:
        partition_info = data_partitioning_service.get_partition_info(partition_id)
        
        if partition_info is None:
            raise HTTPException(status_code=404, detail="Partition not found")
        
        is_loaded = data_partitioning_service.lazy_loader.is_partition_loaded(partition_id)
        
        # Get performance metrics
        performance_stats = data_partitioning_service.performance_monitor.get_performance_stats()
        partition_metrics = performance_stats.get("partition_metrics", {}).get(partition_id, {})
        
        return JSONResponse({
            "partition_id": partition_id,
            "status": {
                "is_loaded": is_loaded,
                "partition_type": partition_info.partition_type.value,
                "floor_id": partition_info.floor_id,
                "building_id": partition_info.building_id,
                "object_count": partition_info.object_count,
                "data_size": partition_info.data_size,
                "compressed_size": partition_info.compressed_size,
                "compression_ratio": partition_info.compression_ratio,
                "access_count": partition_info.access_count,
                "last_accessed": partition_info.last_accessed.isoformat(),
                "created_at": partition_info.created_at.isoformat()
            },
            "performance": partition_metrics,
            "timestamp": datetime.utcnow().isoformat()
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get partition status for {partition_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get partition status: {str(e)}")

@router.post("/preload-partitions")
async def preload_partitions(
    partition_ids: List[str],
    current_user: Optional[Dict] = Depends(get_current_user_optional)
):
    """Preload multiple partitions"""
    try:
        results = []
        
        for partition_id in partition_ids:
            try:
                # Queue partition for loading
                await data_partitioning_service.lazy_loader.load_partition(partition_id)
                
                results.append({
                    "partition_id": partition_id,
                    "success": True,
                    "queued": True
                })
                
            except Exception as e:
                results.append({
                    "partition_id": partition_id,
                    "success": False,
                    "error": str(e)
                })
        
        return JSONResponse({
            "preload_results": results,
            "total_partitions": len(partition_ids),
            "queued_partitions": len([r for r in results if r["success"]]),
            "failed_partitions": len([r for r in results if not r["success"]]),
            "timestamp": datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Failed to preload partitions: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to preload partitions: {str(e)}")

@router.get("/storage-info")
async def get_storage_info(
    current_user: Optional[Dict] = Depends(get_current_user_optional)
):
    """Get storage information and statistics"""
    try:
        storage_path = data_partitioning_service.storage_path
        
        # Get storage statistics
        total_files = 0
        total_size = 0
        partition_files = []
        
        if storage_path.exists():
            for file_path in storage_path.glob("*.json.gz"):
                total_files += 1
                file_size = file_path.stat().st_size
                total_size += file_size
                
                partition_files.append({
                    "filename": file_path.name,
                    "size": file_size,
                    "modified": datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
                })
        
        return JSONResponse({
            "storage_info": {
                "storage_path": str(storage_path),
                "total_files": total_files,
                "total_size": total_size,
                "total_size_mb": total_size / (1024 * 1024),
                "partition_files": partition_files
            },
            "timestamp": datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Failed to get storage info: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get storage info: {str(e)}") 