"""
Million-Scale Performance Test for Arxos Spatial System.

Comprehensive test to validate that the spatial indexing system can handle
1 million+ ArxObjects with acceptable performance for conflict detection
and spatial queries.
"""

import sys
import time
import random
import math
import logging
import gc
import psutil
import os
from pathlib import Path
from typing import List, Dict, Any
import multiprocessing as mp

# Add core modules to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.spatial import (
    SpatialConflictEngine, ArxObject, ArxObjectType, ArxObjectPrecision,
    ArxObjectGeometry, ArxObjectMetadata, BoundingBox3D
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PerformanceMonitor:
    """Monitor system performance during testing."""
    
    def __init__(self):
        self.start_time = time.time()
        self.process = psutil.Process()
        self.measurements = []
    
    def take_measurement(self, label: str) -> Dict[str, Any]:
        """Take a performance measurement."""
        try:
            memory_mb = self.process.memory_info().rss / (1024 * 1024)
            cpu_percent = self.process.cpu_percent()
            elapsed = time.time() - self.start_time
            
            measurement = {
                'label': label,
                'elapsed_time': elapsed,
                'memory_mb': memory_mb,
                'cpu_percent': cpu_percent,
                'timestamp': time.time()
            }
            
            self.measurements.append(measurement)
            return measurement
            
        except Exception as e:
            logger.error(f"Failed to take measurement: {e}")
            return {'label': label, 'error': str(e)}
    
    def get_peak_memory(self) -> float:
        """Get peak memory usage in MB."""
        return max(m.get('memory_mb', 0) for m in self.measurements)
    
    def get_summary(self) -> Dict[str, Any]:
        """Get performance summary."""
        if not self.measurements:
            return {}
        
        return {
            'total_elapsed': time.time() - self.start_time,
            'peak_memory_mb': self.get_peak_memory(),
            'final_memory_mb': self.measurements[-1].get('memory_mb', 0),
            'measurement_count': len(self.measurements),
            'measurements': self.measurements
        }


class ArxObjectGenerator:
    """Generate realistic ArxObjects for performance testing."""
    
    def __init__(self, world_bounds: BoundingBox3D, seed: int = 42):
        self.world_bounds = world_bounds
        self.rng = random.Random(seed)
        
        # Define realistic size ranges for different object types (in feet)
        self.size_ranges = {
            ArxObjectType.STRUCTURAL_BEAM: (10.0, 50.0, 0.5, 2.0, 0.5, 2.0),
            ArxObjectType.STRUCTURAL_COLUMN: (0.5, 2.0, 0.5, 2.0, 8.0, 16.0),
            ArxObjectType.STRUCTURAL_WALL: (8.0, 50.0, 0.25, 1.0, 8.0, 12.0),
            ArxObjectType.ELECTRICAL_OUTLET: (0.2, 0.5, 0.1, 0.3, 0.1, 0.3),
            ArxObjectType.ELECTRICAL_CONDUIT: (5.0, 100.0, 0.1, 0.5, 0.1, 0.5),
            ArxObjectType.HVAC_DUCT: (5.0, 50.0, 1.0, 3.0, 0.5, 2.0),
            ArxObjectType.PLUMBING_PIPE: (5.0, 100.0, 0.1, 1.0, 0.1, 1.0),
            ArxObjectType.FIRE_SPRINKLER: (0.2, 0.5, 0.2, 0.5, 0.2, 0.5),
            ArxObjectType.CEILING_TILE: (2.0, 4.0, 2.0, 4.0, 0.1, 0.2),
            ArxObjectType.FURNITURE: (2.0, 8.0, 1.0, 4.0, 2.5, 4.0)
        }
        
        # Distribution of object types (percentage)
        self.type_distribution = [
            (ArxObjectType.CEILING_TILE, 25),          # Most common
            (ArxObjectType.ELECTRICAL_OUTLET, 20),
            (ArxObjectType.FURNITURE, 15),
            (ArxObjectType.PLUMBING_PIPE, 10),
            (ArxObjectType.ELECTRICAL_CONDUIT, 8),
            (ArxObjectType.HVAC_DUCT, 7),
            (ArxObjectType.FIRE_SPRINKLER, 5),
            (ArxObjectType.STRUCTURAL_WALL, 4),
            (ArxObjectType.STRUCTURAL_BEAM, 3),
            (ArxObjectType.STRUCTURAL_COLUMN, 3)
        ]
        
        # Create weighted list for sampling
        self.weighted_types = []
        for obj_type, weight in self.type_distribution:
            self.weighted_types.extend([obj_type] * weight)
    
    def generate_object(self, object_id: Optional[str] = None) -> ArxObject:
        """Generate a single realistic ArxObject."""
        # Select object type
        obj_type = self.rng.choice(self.weighted_types)
        
        # Get size range for this type
        if obj_type in self.size_ranges:
            size_range = self.size_ranges[obj_type]
            length = self.rng.uniform(size_range[0], size_range[1])
            width = self.rng.uniform(size_range[2], size_range[3])
            height = self.rng.uniform(size_range[4], size_range[5])
        else:
            # Default size range
            length = self.rng.uniform(1.0, 10.0)
            width = self.rng.uniform(1.0, 10.0)
            height = self.rng.uniform(1.0, 10.0)
        
        # Generate position within world bounds
        x = self.rng.uniform(
            self.world_bounds.min_x + length/2,
            self.world_bounds.max_x - length/2
        )
        y = self.rng.uniform(
            self.world_bounds.min_y + width/2,
            self.world_bounds.max_y - width/2
        )
        z = self.rng.uniform(
            self.world_bounds.min_z + height/2,
            self.world_bounds.max_z - height/2
        )
        
        # Create geometry
        geometry = ArxObjectGeometry(
            x=x, y=y, z=z,
            length=length, width=width, height=height
        )
        
        # Create metadata
        metadata = ArxObjectMetadata(
            name=f"{obj_type.value}_{self.rng.randint(1000, 9999)}",
            description=f"Generated {obj_type.value} for testing"
        )
        
        # Select precision (mostly standard, some fine)
        precision = self.rng.choices(
            [ArxObjectPrecision.STANDARD, ArxObjectPrecision.FINE],
            weights=[90, 10]
        )[0]
        
        return ArxObject(
            arxobject_type=obj_type,
            geometry=geometry,
            metadata=metadata,
            precision=precision,
            building_id="test_building",
            floor_id=f"floor_{self.rng.randint(1, 10)}",
            room_id=f"room_{self.rng.randint(100, 999)}",
            arxobject_id=object_id
        )
    
    def generate_batch(self, count: int, start_id: int = 0) -> List[ArxObject]:
        """Generate a batch of ArxObjects."""
        objects = []
        for i in range(count):
            obj_id = f"test_obj_{start_id + i:06d}"
            obj = self.generate_object(obj_id)
            objects.append(obj)
        return objects


def test_spatial_index_performance(target_objects: int = 1000000, 
                                 batch_size: int = 10000) -> Dict[str, Any]:
    """Test spatial index performance with target number of objects."""
    
    logger.info(f"Starting spatial index performance test with {target_objects:,} objects")
    
    # Initialize performance monitor
    monitor = PerformanceMonitor()
    
    # Define large world bounds (1000ft x 1000ft x 100ft building)
    world_bounds = BoundingBox3D(
        min_x=-500.0, min_y=-500.0, min_z=0.0,
        max_x=500.0, max_y=500.0, max_z=100.0
    )
    
    # Initialize spatial conflict engine
    logger.info("Initializing spatial conflict engine...")
    conflict_engine = SpatialConflictEngine(
        world_bounds=world_bounds,
        max_workers=min(8, mp.cpu_count())
    )
    
    monitor.take_measurement("engine_initialized")
    
    # Initialize object generator
    generator = ArxObjectGenerator(world_bounds)
    
    # Performance tracking
    insertion_times = []
    batch_times = []
    memory_usage = []
    
    # Insert objects in batches
    logger.info(f"Inserting {target_objects:,} objects in batches of {batch_size:,}...")
    
    objects_inserted = 0
    batch_num = 0
    
    while objects_inserted < target_objects:
        batch_start = time.time()
        
        # Calculate batch size (handle remainder)
        current_batch_size = min(batch_size, target_objects - objects_inserted)
        
        # Generate batch
        batch_objects = generator.generate_batch(current_batch_size, objects_inserted)
        
        # Insert batch with timing
        insert_start = time.time()
        
        successful_inserts = 0
        for obj in batch_objects:
            if conflict_engine.add_arxobject(obj):
                successful_inserts += 1
        
        insert_time = time.time() - insert_start
        insertion_times.append(insert_time)
        
        objects_inserted += successful_inserts
        batch_num += 1
        
        batch_time = time.time() - batch_start
        batch_times.append(batch_time)
        
        # Take measurements
        measurement = monitor.take_measurement(f"batch_{batch_num}")
        memory_usage.append(measurement.get('memory_mb', 0))
        
        # Progress reporting
        if batch_num % 10 == 0 or objects_inserted >= target_objects:
            progress = objects_inserted / target_objects * 100
            rate = objects_inserted / (time.time() - monitor.start_time)
            logger.info(f"Progress: {objects_inserted:,}/{target_objects:,} ({progress:.1f}%) "
                       f"Rate: {rate:.0f} objects/sec, Memory: {measurement.get('memory_mb', 0):.1f} MB")
        
        # Force garbage collection every 50 batches
        if batch_num % 50 == 0:
            gc.collect()
    
    logger.info(f"✅ Successfully inserted {objects_inserted:,} objects")
    
    # Test query performance
    logger.info("Testing spatial query performance...")
    
    # Test range queries
    query_times = []
    query_results = []
    
    for i in range(100):  # 100 sample queries
        # Generate random query box
        query_size = random.uniform(10.0, 100.0)  # 10-100 ft box
        center_x = random.uniform(world_bounds.min_x + query_size, 
                                world_bounds.max_x - query_size)
        center_y = random.uniform(world_bounds.min_y + query_size,
                                world_bounds.max_y - query_size)
        center_z = random.uniform(world_bounds.min_z + query_size,
                                world_bounds.max_z - query_size)
        
        query_bounds = BoundingBox3D(
            min_x=center_x - query_size/2,
            min_y=center_y - query_size/2,
            min_z=center_z - query_size/2,
            max_x=center_x + query_size/2,
            max_y=center_y + query_size/2,
            max_z=center_z + query_size/2
        )
        
        # Execute query
        query_start = time.time()
        results = conflict_engine.octree.query_range(query_bounds)
        query_time = time.time() - query_start
        
        query_times.append(query_time)
        query_results.append(len(results))
    
    monitor.take_measurement("queries_completed")
    
    # Test conflict detection performance
    logger.info("Testing conflict detection performance...")
    
    # Sample 1000 objects for conflict detection
    sample_objects = random.sample(list(conflict_engine.objects.values()), 
                                 min(1000, len(conflict_engine.objects)))
    
    conflict_times = []
    conflict_counts = []
    
    detection_start = time.time()
    
    for i, obj in enumerate(sample_objects):
        detect_start = time.time()
        conflicts = conflict_engine.detect_conflicts(obj)
        detect_time = time.time() - detect_start
        
        conflict_times.append(detect_time)
        conflict_counts.append(len(conflicts))
        
        if (i + 1) % 100 == 0:
            logger.info(f"Conflict detection progress: {i+1}/{len(sample_objects)}")
    
    total_detection_time = time.time() - detection_start
    
    monitor.take_measurement("conflict_detection_completed")
    
    # Get final statistics
    stats = conflict_engine.get_statistics()
    final_measurement = monitor.take_measurement("test_completed")
    
    # Compile results
    results = {
        'test_parameters': {
            'target_objects': target_objects,
            'actual_objects': objects_inserted,
            'batch_size': batch_size,
            'world_bounds': {
                'volume': world_bounds.volume(),
                'dimensions': f"{world_bounds.max_x - world_bounds.min_x} x "
                            f"{world_bounds.max_y - world_bounds.min_y} x "
                            f"{world_bounds.max_z - world_bounds.min_z} ft"
            }
        },
        'insertion_performance': {
            'total_time': sum(insertion_times),
            'average_batch_time': sum(batch_times) / len(batch_times),
            'insertion_rate_per_second': objects_inserted / sum(insertion_times),
            'peak_memory_mb': monitor.get_peak_memory(),
            'final_memory_mb': final_measurement.get('memory_mb', 0)
        },
        'query_performance': {
            'average_query_time': sum(query_times) / len(query_times),
            'max_query_time': max(query_times),
            'min_query_time': min(query_times),
            'average_results_per_query': sum(query_results) / len(query_results),
            'queries_per_second': len(query_times) / sum(query_times)
        },
        'conflict_detection_performance': {
            'average_detection_time': sum(conflict_times) / len(conflict_times),
            'max_detection_time': max(conflict_times),
            'total_detection_time': total_detection_time,
            'detection_rate_per_second': len(sample_objects) / total_detection_time,
            'average_conflicts_per_object': sum(conflict_counts) / len(conflict_counts),
            'max_conflicts_for_object': max(conflict_counts)
        },
        'spatial_index_statistics': stats,
        'performance_monitoring': monitor.get_summary(),
        'success': True,
        'test_timestamp': time.time()
    }
    
    return results


def run_scalability_tests() -> Dict[str, Any]:
    """Run comprehensive scalability tests."""
    
    logger.info("🚀 Starting Arxos Million-Scale Performance Tests")
    
    all_results = {}
    test_scales = [10000, 50000, 100000, 500000, 1000000]
    
    for scale in test_scales:
        logger.info(f"\n📊 Testing scale: {scale:,} objects")
        
        try:
            results = test_spatial_index_performance(
                target_objects=scale,
                batch_size=min(10000, scale // 10)
            )
            
            all_results[f"scale_{scale}"] = results
            
            # Print summary for this scale
            insertion_rate = results['insertion_performance']['insertion_rate_per_second']
            query_time = results['query_performance']['average_query_time']
            detection_time = results['conflict_detection_performance']['average_detection_time']
            memory_mb = results['insertion_performance']['final_memory_mb']
            
            logger.info(f"✅ Scale {scale:,} completed:")
            logger.info(f"   Insertion rate: {insertion_rate:.0f} objects/sec")
            logger.info(f"   Average query time: {query_time:.4f}s")
            logger.info(f"   Average conflict detection time: {detection_time:.4f}s")
            logger.info(f"   Memory usage: {memory_mb:.1f} MB")
            
            # Memory cleanup
            gc.collect()
            
            # Break early if memory usage is too high
            if memory_mb > 8000:  # 8GB limit
                logger.warning(f"Memory limit reached at scale {scale:,}, stopping tests")
                break
                
        except Exception as e:
            logger.error(f"❌ Test failed at scale {scale:,}: {e}")
            all_results[f"scale_{scale}"] = {
                'success': False,
                'error': str(e),
                'test_timestamp': time.time()
            }
            break
    
    # Generate summary report
    summary = {
        'test_suite': 'arxos_million_scale_performance',
        'test_timestamp': time.time(),
        'scales_tested': len([r for r in all_results.values() if r.get('success', False)]),
        'max_scale_achieved': max([int(k.split('_')[1]) for k, v in all_results.items() 
                                  if v.get('success', False)], default=0),
        'results': all_results
    }
    
    return summary


def print_performance_report(results: Dict[str, Any]) -> None:
    """Print formatted performance report."""
    
    print("\n" + "="*70)
    print("🏗️  ARXOS MILLION-SCALE PERFORMANCE TEST RESULTS")
    print("="*70)
    
    print(f"Test Suite: {results['test_suite']}")
    print(f"Scales Tested: {results['scales_tested']}")
    print(f"Maximum Scale Achieved: {results['max_scale_achieved']:,} objects")
    print()
    
    print("📊 Performance Summary by Scale:")
    print("-" * 70)
    print(f"{'Scale':<12} {'Insert/sec':<12} {'Query ms':<12} {'Detect ms':<12} {'Memory MB':<12}")
    print("-" * 70)
    
    for scale_key, scale_results in results['results'].items():
        if not scale_results.get('success', False):
            continue
        
        scale = int(scale_key.split('_')[1])
        insert_rate = scale_results['insertion_performance']['insertion_rate_per_second']
        query_time = scale_results['query_performance']['average_query_time'] * 1000
        detect_time = scale_results['conflict_detection_performance']['average_detection_time'] * 1000
        memory_mb = scale_results['insertion_performance']['final_memory_mb']
        
        print(f"{scale:,:<12} {insert_rate:,.0f:<12} {query_time:.2f:<12} "
              f"{detect_time:.2f:<12} {memory_mb:.1f:<12}")
    
    print("-" * 70)
    
    # Print detailed results for maximum scale
    max_scale_key = f"scale_{results['max_scale_achieved']}"
    if max_scale_key in results['results']:
        max_results = results['results'][max_scale_key]
        
        print(f"\n🎯 Detailed Results for Maximum Scale ({results['max_scale_achieved']:,} objects):")
        print("-" * 50)
        
        # Spatial index statistics
        spatial_stats = max_results['spatial_index_statistics']
        octree_stats = spatial_stats['spatial_indices']['octree']
        rtree_stats = spatial_stats['spatial_indices']['rtree']
        
        print("3D Octree Performance:")
        print(f"   Total nodes: {octree_stats['total_nodes']:,}")
        print(f"   Leaf nodes: {octree_stats['leaf_nodes']:,}")
        print(f"   Max depth used: {octree_stats['max_depth_used']}")
        print(f"   Objects per leaf: {octree_stats['average_objects_per_leaf']:.1f}")
        
        print("\n2D R-tree Performance:")
        print(f"   Total nodes: {rtree_stats['total_nodes']:,}")
        print(f"   Tree height: {rtree_stats['tree_height']}")
        print(f"   Fill factor: {rtree_stats['fill_factor']:.1%}")
        
        # Performance metrics
        insertion_perf = max_results['insertion_performance']
        query_perf = max_results['query_performance']
        conflict_perf = max_results['conflict_detection_performance']
        
        print(f"\nInsertion Performance:")
        print(f"   Rate: {insertion_perf['insertion_rate_per_second']:.0f} objects/sec")
        print(f"   Peak memory: {insertion_perf['peak_memory_mb']:.1f} MB")
        
        print(f"\nQuery Performance:")
        print(f"   Average time: {query_perf['average_query_time']*1000:.2f} ms")
        print(f"   Queries/sec: {query_perf['queries_per_second']:.0f}")
        
        print(f"\nConflict Detection Performance:")
        print(f"   Average time: {conflict_perf['average_detection_time']*1000:.2f} ms")
        print(f"   Detection rate: {conflict_perf['detection_rate_per_second']:.0f} objects/sec")
        print(f"   Avg conflicts/object: {conflict_perf['average_conflicts_per_object']:.1f}")
    
    print("\n" + "="*70)
    
    # Performance assessment
    max_achieved = results['max_scale_achieved']
    if max_achieved >= 1000000:
        print("🎉 EXCELLENT: Successfully handled 1M+ objects!")
    elif max_achieved >= 500000:
        print("✅ GOOD: Successfully handled 500K+ objects")
    elif max_achieved >= 100000:
        print("⚠️  ACCEPTABLE: Handled 100K+ objects, optimization needed for 1M scale")
    else:
        print("❌ NEEDS IMPROVEMENT: Failed to achieve target scale")
    
    print("="*70)


if __name__ == '__main__':
    try:
        # Run the comprehensive scalability tests
        results = run_scalability_tests()
        
        # Print formatted report
        print_performance_report(results)
        
        # Save results to file
        results_file = Path(__file__).parent / "million_scale_test_results.json"
        with open(results_file, 'w') as f:
            import json
            json.dump(results, f, indent=2)
        
        logger.info(f"📄 Detailed results saved to: {results_file}")
        
        # Exit with appropriate code
        if results['max_scale_achieved'] >= 1000000:
            logger.info("🎉 Million-scale performance test PASSED!")
            sys.exit(0)
        else:
            logger.warning("⚠️  Million-scale performance test did not achieve target")
            sys.exit(1)
        
    except KeyboardInterrupt:
        logger.info("❌ Test cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)