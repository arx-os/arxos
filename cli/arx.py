#!/usr/bin/env python3
"""
Arxos CLI - Building-Infrastructure-as-Code command line interface.

The 'arx' command provides comprehensive tools for managing ArxObjects,
spatial conflict detection, and building information modeling.
"""

import sys
import os
import argparse
import json
import time
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path

# Add core modules to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.spatial import (
    SpatialConflictEngine, ArxObject, ArxObjectType, ArxObjectPrecision,
    ArxObjectGeometry, ArxObjectMetadata, BoundingBox3D
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)


class ArxosContext:
    """Global context for Arxos CLI operations."""
    
    def __init__(self):
        self.workspace_path = Path.cwd()
        self.config_file = self.workspace_path / '.arxos' / 'config.json'
        self.data_dir = self.workspace_path / '.arxos' / 'data'
        self.conflicts_dir = self.workspace_path / '.arxos' / 'conflicts'
        
        # Default world bounds (1000ft x 1000ft x 100ft building)
        self.world_bounds = BoundingBox3D(
            min_x=-500.0, min_y=-500.0, min_z=0.0,
            max_x=500.0, max_y=500.0, max_z=100.0
        )
        
        self.conflict_engine: Optional[SpatialConflictEngine] = None
        self.config: Dict[str, Any] = {}
        
        self._ensure_workspace()
        self._load_config()
    
    def _ensure_workspace(self) -> None:
        """Ensure .arxos workspace directory exists."""
        for directory in [self.data_dir, self.conflicts_dir]:
            directory.mkdir(parents=True, exist_ok=True)
    
    def _load_config(self) -> None:
        """Load Arxos configuration."""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    self.config = json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load config: {e}")
                self.config = {}
        
        # Set defaults
        self.config.setdefault('world_bounds', {
            'min_x': -500.0, 'min_y': -500.0, 'min_z': 0.0,
            'max_x': 500.0, 'max_y': 500.0, 'max_z': 100.0
        })
        self.config.setdefault('max_workers', 8)
        self.config.setdefault('default_precision', 'standard')
    
    def _save_config(self) -> None:
        """Save Arxos configuration."""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save config: {e}")
    
    def initialize_conflict_engine(self) -> None:
        """Initialize spatial conflict engine."""
        if self.conflict_engine is None:
            bounds_config = self.config['world_bounds']
            self.world_bounds = BoundingBox3D(**bounds_config)
            
            self.conflict_engine = SpatialConflictEngine(
                world_bounds=self.world_bounds,
                max_workers=self.config['max_workers']
            )
            
            logger.info("Initialized spatial conflict engine")
    
    def get_data_file(self, filename: str) -> Path:
        """Get path to data file."""
        return self.data_dir / filename
    
    def get_conflicts_file(self, filename: str) -> Path:
        """Get path to conflicts file."""
        return self.conflicts_dir / filename


# Global context
ctx = ArxosContext()


def cmd_init(args) -> None:
    """Initialize new Arxos workspace."""
    print("Initializing Arxos workspace...")
    
    # Create workspace structure
    ctx._ensure_workspace()
    
    # Set world bounds if provided
    if hasattr(args, 'bounds') and args.bounds:
        try:
            bounds = [float(x) for x in args.bounds.split(',')]
            if len(bounds) == 6:
                ctx.config['world_bounds'] = {
                    'min_x': bounds[0], 'min_y': bounds[1], 'min_z': bounds[2],
                    'max_x': bounds[3], 'max_y': bounds[4], 'max_z': bounds[5]
                }
                print(f"Set world bounds: {args.bounds}")
        except ValueError:
            print("Error: Invalid bounds format. Use 'min_x,min_y,min_z,max_x,max_y,max_z'")
            return
    
    # Save configuration
    ctx._save_config()
    
    print(f"✅ Arxos workspace initialized in {ctx.workspace_path}")
    print(f"📁 Data directory: {ctx.data_dir}")
    print(f"⚡ Conflicts directory: {ctx.conflicts_dir}")
    print(f"📦 World bounds: {ctx.config['world_bounds']}")


def cmd_add(args) -> None:
    """Add ArxObject to spatial index."""
    ctx.initialize_conflict_engine()
    
    try:
        # Parse object type
        try:
            obj_type = ArxObjectType(args.type)
        except ValueError:
            print(f"Error: Invalid object type '{args.type}'")
            print(f"Valid types: {[t.value for t in ArxObjectType]}")
            return
        
        # Parse geometry
        geometry_parts = args.geometry.split(',')
        if len(geometry_parts) != 6:
            print("Error: Geometry must be 'x,y,z,length,width,height'")
            return
        
        try:
            x, y, z, length, width, height = [float(p) for p in geometry_parts]
        except ValueError:
            print("Error: All geometry values must be numbers")
            return
        
        geometry = ArxObjectGeometry(
            x=x, y=y, z=z,
            length=length, width=width, height=height
        )
        
        # Create metadata
        metadata = ArxObjectMetadata(
            name=getattr(args, 'name', ''),
            description=getattr(args, 'description', '')
        )
        
        # Parse precision
        precision = ArxObjectPrecision(getattr(args, 'precision', ctx.config['default_precision']))
        
        # Create ArxObject
        arxobject = ArxObject(
            arxobject_type=obj_type,
            geometry=geometry,
            metadata=metadata,
            precision=precision,
            building_id=getattr(args, 'building_id', None),
            floor_id=getattr(args, 'floor_id', None),
            room_id=getattr(args, 'room_id', None)
        )
        
        # Add to conflict engine
        success = ctx.conflict_engine.add_arxobject(arxobject)
        
        if success:
            print(f"✅ Added ArxObject {arxobject.id}")
            print(f"   Type: {obj_type.value}")
            print(f"   Location: ({x}, {y}, {z})")
            print(f"   Dimensions: {length} x {width} x {height} ft")
            print(f"   Precision: {precision.value}")
            
            # Check for conflicts
            conflicts = ctx.conflict_engine.detect_conflicts(arxobject)
            if conflicts:
                print(f"⚠️  Detected {len(conflicts)} conflicts:")
                for i, conflict in enumerate(conflicts[:5]):  # Show first 5
                    print(f"   {i+1}. {conflict.description} ({conflict.severity})")
                if len(conflicts) > 5:
                    print(f"   ... and {len(conflicts) - 5} more")
            else:
                print("✅ No conflicts detected")
        else:
            print("❌ Failed to add ArxObject")
    
    except Exception as e:
        print(f"❌ Error adding ArxObject: {e}")


def cmd_remove(args) -> None:
    """Remove ArxObject from spatial index."""
    ctx.initialize_conflict_engine()
    
    success = ctx.conflict_engine.remove_arxobject(args.object_id)
    
    if success:
        print(f"✅ Removed ArxObject {args.object_id}")
    else:
        print(f"❌ ArxObject {args.object_id} not found")


def cmd_list(args) -> None:
    """List ArxObjects in spatial index."""
    ctx.initialize_conflict_engine()
    
    objects = ctx.conflict_engine.objects
    
    if not objects:
        print("No ArxObjects found in workspace")
        return
    
    print(f"Found {len(objects)} ArxObjects:")
    print()
    
    # Group by system type
    by_system = {}
    for obj in objects.values():
        system = obj.get_system_type()
        if system not in by_system:
            by_system[system] = []
        by_system[system].append(obj)
    
    for system, system_objects in sorted(by_system.items()):
        print(f"📦 {system.upper()} ({len(system_objects)} objects)")
        
        for obj in sorted(system_objects, key=lambda x: x.id)[:10]:  # Show first 10
            center = obj.get_center()
            print(f"   • {obj.id[:12]}... ({obj.type.value})")
            print(f"     Location: ({center[0]:.2f}, {center[1]:.2f}, {center[2]:.2f})")
            print(f"     Volume: {obj.get_volume():.2f} ft³")
        
        if len(system_objects) > 10:
            print(f"     ... and {len(system_objects) - 10} more")
        print()


def cmd_conflicts(args) -> None:
    """Show spatial conflicts."""
    ctx.initialize_conflict_engine()
    
    active_conflicts = list(ctx.conflict_engine.active_conflicts.values())
    
    if not active_conflicts:
        print("✅ No active conflicts found")
        return
    
    print(f"Found {len(active_conflicts)} active conflicts:")
    print()
    
    # Group by severity
    by_severity = {'critical': [], 'high': [], 'medium': [], 'low': []}
    for conflict in active_conflicts:
        by_severity[conflict.severity].append(conflict)
    
    for severity in ['critical', 'high', 'medium', 'low']:
        conflicts = by_severity[severity]
        if not conflicts:
            continue
        
        severity_emoji = {'critical': '🚨', 'high': '⚠️', 'medium': '💡', 'low': '📝'}
        print(f"{severity_emoji[severity]} {severity.upper()} ({len(conflicts)} conflicts)")
        
        for conflict in conflicts[:5]:  # Show first 5
            obj1 = ctx.conflict_engine.objects.get(conflict.object1_id)
            obj2 = ctx.conflict_engine.objects.get(conflict.object2_id)
            
            obj1_type = obj1.type.value if obj1 else conflict.object1_id
            obj2_type = obj2.type.value if obj2 else conflict.object2_id
            
            print(f"   • {obj1_type} ↔ {obj2_type}")
            print(f"     {conflict.description}")
            print(f"     Distance: {conflict.distance:.3f} ft")
            if conflict.resolution_strategy:
                print(f"     Resolution: {conflict.resolution_strategy}")
        
        if len(conflicts) > 5:
            print(f"     ... and {len(conflicts) - 5} more")
        print()


def cmd_detect(args) -> None:
    """Run conflict detection."""
    ctx.initialize_conflict_engine()
    
    print("🔍 Running spatial conflict detection...")
    start_time = time.time()
    
    if hasattr(args, 'object_id') and args.object_id:
        # Detect conflicts for specific object
        if args.object_id not in ctx.conflict_engine.objects:
            print(f"❌ ArxObject {args.object_id} not found")
            return
        
        obj = ctx.conflict_engine.objects[args.object_id]
        conflicts = ctx.conflict_engine.detect_conflicts(obj)
        elapsed = time.time() - start_time
        
        print(f"✅ Detected {len(conflicts)} conflicts for {args.object_id} in {elapsed:.2f}s")
    else:
        # Batch conflict detection
        results = ctx.conflict_engine.batch_detect_conflicts()
        elapsed = time.time() - start_time
        
        total_conflicts = sum(len(conflicts) for conflicts in results.values())
        objects_with_conflicts = sum(1 for conflicts in results.values() if conflicts)
        
        print(f"✅ Detected {total_conflicts} total conflicts across {len(results)} objects in {elapsed:.2f}s")
        print(f"📊 {objects_with_conflicts}/{len(results)} objects have conflicts")
    
    # Show summary
    stats = ctx.conflict_engine.get_statistics()
    print(f"📈 Performance: {len(ctx.conflict_engine.objects)/elapsed:.0f} objects/sec")


def cmd_resolve(args) -> None:
    """Attempt automatic conflict resolution."""
    ctx.initialize_conflict_engine()
    
    print("🔧 Starting automated conflict resolution...")
    start_time = time.time()
    
    # Run resolution
    summary = ctx.conflict_engine.resolve_conflicts()
    elapsed = time.time() - start_time
    
    print(f"✅ Resolution completed in {elapsed:.2f}s")
    print(f"📊 Results:")
    print(f"   • Processed: {summary['conflicts_processed']}")
    print(f"   • Resolved: {summary['resolved_count']}")
    print(f"   • Failed: {summary['failed_count']}")
    print(f"   • Success rate: {summary['success_rate']:.1%}")
    print(f"   • Estimated cost: ${summary['total_cost']:.2f}")
    print(f"   • Estimated time: {summary['total_time_hours']:.1f} hours")


def cmd_stats(args) -> None:
    """Show system statistics."""
    ctx.initialize_conflict_engine()
    
    stats = ctx.conflict_engine.get_statistics()
    
    print("📊 Arxos System Statistics")
    print("=" * 50)
    
    # Engine stats
    engine = stats['engine_stats']
    print(f"Objects: {engine['total_objects']}")
    print(f"Conflicts detected: {engine['total_conflicts_detected']}")
    print(f"Conflicts resolved: {engine['total_conflicts_resolved']}")
    print(f"Average detection time: {engine['average_detection_time']:.4f}s")
    print(f"Cache hit rate: {engine.get('cache_hit_rate', 0.0):.1%}")
    print(f"Parallel efficiency: {engine.get('parallel_efficiency', 0.0):.1%}")
    print()
    
    # Spatial indices
    octree = stats['spatial_indices']['octree']
    rtree = stats['spatial_indices']['rtree']
    
    print("3D Octree Index:")
    print(f"   Nodes: {octree['total_nodes']} ({octree['leaf_nodes']} leaf)")
    print(f"   Max depth: {octree['max_depth_used']}/{octree['max_depth_configured']}")
    print(f"   Objects per leaf: {octree['average_objects_per_leaf']:.1f}")
    print()
    
    print("2D R-tree Index:")
    print(f"   Nodes: {rtree['total_nodes']}")
    print(f"   Tree height: {rtree['tree_height']}")
    print(f"   Fill factor: {rtree['fill_factor']:.1%}")
    print()
    
    # Conflicts
    conflicts = stats['conflicts']
    print("Active Conflicts:")
    for conflict_type, count in conflicts['conflicts_by_type'].items():
        print(f"   {conflict_type}: {count}")
    print()
    
    print("Conflicts by Severity:")
    for severity, count in conflicts['conflicts_by_severity'].items():
        print(f"   {severity}: {count}")
    print()
    
    # Objects by system
    print("Objects by System:")
    for system, count in stats['objects']['objects_by_system'].items():
        print(f"   {system}: {count}")


def cmd_export(args) -> None:
    """Export data in various formats."""
    ctx.initialize_conflict_engine()
    
    output_file = Path(args.output) if args.output else Path(f"arxos_export_{int(time.time())}.json")
    
    try:
        if args.format == 'conflicts':
            # Export conflicts
            data = ctx.conflict_engine.export_conflicts('json')
            
        elif args.format == 'objects':
            # Export objects
            objects_data = []
            for obj in ctx.conflict_engine.objects.values():
                objects_data.append(obj.to_dict())
            
            data = json.dumps({
                'objects': objects_data,
                'statistics': ctx.conflict_engine.get_statistics(),
                'export_timestamp': time.time()
            }, indent=2)
            
        elif args.format == 'ifc':
            # Export IFC-compatible data
            ifc_data = []
            for obj in ctx.conflict_engine.objects.values():
                ifc_data.append(obj.to_ifc())
            
            data = json.dumps({
                'ifc_entities': ifc_data,
                'project_info': {
                    'name': 'Arxos BIM Export',
                    'world_bounds': ctx.config['world_bounds'],
                    'export_timestamp': time.time()
                }
            }, indent=2)
        
        else:
            print(f"❌ Unknown export format: {args.format}")
            return
        
        # Write to file
        with open(output_file, 'w') as f:
            f.write(data)
        
        print(f"✅ Exported {args.format} to {output_file}")
        print(f"📄 File size: {output_file.stat().st_size:,} bytes")
        
    except Exception as e:
        print(f"❌ Export failed: {e}")


def cmd_optimize(args) -> None:
    """Optimize spatial indices."""
    ctx.initialize_conflict_engine()
    
    print("⚡ Optimizing spatial indices...")
    start_time = time.time()
    
    ctx.conflict_engine.optimize()
    
    elapsed = time.time() - start_time
    print(f"✅ Optimization completed in {elapsed:.2f}s")


def cmd_clear(args) -> None:
    """Clear all data."""
    ctx.initialize_conflict_engine()
    
    if not args.force:
        response = input("⚠️  This will delete all ArxObjects and conflicts. Continue? (y/N): ")
        if response.lower() != 'y':
            print("Cancelled")
            return
    
    ctx.conflict_engine.clear()
    print("✅ Cleared all data")


def create_parser() -> argparse.ArgumentParser:
    """Create argument parser for Arxos CLI."""
    
    parser = argparse.ArgumentParser(
        prog='arx',
        description='Arxos BIM - Building-Infrastructure-as-Code CLI',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  arx init --bounds "-100,-100,0,100,100,50"
  arx add --type structural_beam --geometry "0,0,10,20,1,1" --name "Main Beam"
  arx conflicts
  arx detect
  arx resolve
  arx export --format conflicts --output conflicts.json
        """
    )
    
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Init command
    init_parser = subparsers.add_parser('init', help='Initialize Arxos workspace')
    init_parser.add_argument('--bounds', help='World bounds: min_x,min_y,min_z,max_x,max_y,max_z')
    
    # Add command
    add_parser = subparsers.add_parser('add', help='Add ArxObject')
    add_parser.add_argument('--type', required=True, help='Object type')
    add_parser.add_argument('--geometry', required=True, help='Geometry: x,y,z,length,width,height')
    add_parser.add_argument('--name', help='Object name')
    add_parser.add_argument('--description', help='Object description')
    add_parser.add_argument('--precision', choices=[p.value for p in ArxObjectPrecision], 
                           help='Precision level')
    add_parser.add_argument('--building-id', help='Building ID')
    add_parser.add_argument('--floor-id', help='Floor ID') 
    add_parser.add_argument('--room-id', help='Room ID')
    
    # Remove command
    remove_parser = subparsers.add_parser('remove', help='Remove ArxObject')
    remove_parser.add_argument('object_id', help='Object ID to remove')
    
    # List command
    subparsers.add_parser('list', help='List ArxObjects')
    
    # Conflicts command
    subparsers.add_parser('conflicts', help='Show spatial conflicts')
    
    # Detect command
    detect_parser = subparsers.add_parser('detect', help='Run conflict detection')
    detect_parser.add_argument('--object-id', help='Detect conflicts for specific object')
    
    # Resolve command
    subparsers.add_parser('resolve', help='Resolve conflicts automatically')
    
    # Stats command
    subparsers.add_parser('stats', help='Show system statistics')
    
    # Export command
    export_parser = subparsers.add_parser('export', help='Export data')
    export_parser.add_argument('--format', choices=['conflicts', 'objects', 'ifc'], 
                              default='objects', help='Export format')
    export_parser.add_argument('--output', help='Output file path')
    
    # Optimize command
    subparsers.add_parser('optimize', help='Optimize spatial indices')
    
    # Clear command
    clear_parser = subparsers.add_parser('clear', help='Clear all data')
    clear_parser.add_argument('--force', action='store_true', help='Skip confirmation')
    
    return parser


def main():
    """Main CLI entry point."""
    parser = create_parser()
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Command dispatch
    commands = {
        'init': cmd_init,
        'add': cmd_add,
        'remove': cmd_remove,
        'list': cmd_list,
        'conflicts': cmd_conflicts,
        'detect': cmd_detect,
        'resolve': cmd_resolve,
        'stats': cmd_stats,
        'export': cmd_export,
        'optimize': cmd_optimize,
        'clear': cmd_clear
    }
    
    if args.command in commands:
        try:
            commands[args.command](args)
        except KeyboardInterrupt:
            print("\n❌ Cancelled by user")
            sys.exit(1)
        except Exception as e:
            if args.verbose:
                import traceback
                traceback.print_exc()
            else:
                print(f"❌ Error: {e}")
            sys.exit(1)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()