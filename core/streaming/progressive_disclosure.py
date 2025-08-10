"""
Progressive Disclosure System for 14KB Architecture.

Implements Level-of-Detail (LOD) system for progressive loading of
building components based on user needs and viewport constraints.
"""

import logging
from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass
from enum import Enum
import json

logger = logging.getLogger(__name__)


class LODLevel(Enum):
    """Level of Detail enumeration for progressive disclosure."""
    
    BUILDING_OUTLINE = 0    # 2KB: Building outline + major systems
    ROOM_LAYOUT = 1         # 6KB: Room layouts + primary MEP
    DETAILED_COMPONENTS = 2 # 12KB: Detailed components
    CONFLICT_ZONES = 3      # 14KB: Conflict zones + full details
    FULL_DETAIL = 4         # Unlimited: Stream from server on-demand


@dataclass
class LODConfiguration:
    """Configuration for each LOD level."""
    
    level: LODLevel
    max_size_bytes: int
    description: str
    object_filters: Dict[str, Any]
    priority_threshold: int  # Maximum system priority to include
    
    def __post_init__(self):
        """Validate configuration."""
        if self.max_size_bytes <= 0:
            raise ValueError("max_size_bytes must be positive")
        
        if self.priority_threshold < 1 or self.priority_threshold > 5:
            raise ValueError("priority_threshold must be between 1-5")


class ProgressiveDisclosure:
    """
    Progressive Disclosure system for 14KB streaming architecture.
    
    Manages Level-of-Detail loading strategy to ensure critical building
    information loads first while staying within bundle size constraints.
    """
    
    def __init__(self, max_levels: int = 4, base_size: int = 2048):
        """
        Initialize progressive disclosure system.
        
        Args:
            max_levels: Maximum LOD levels to support
            base_size: Base size in bytes for Level 0
        """
        self.max_levels = max_levels
        self.base_size = base_size
        
        # Initialize LOD configurations
        self.lod_configs = self._initialize_lod_configurations()
        
        # Disclosure state tracking
        self.current_objects_by_level: Dict[LODLevel, Set[str]] = {}
        self.size_usage_by_level: Dict[LODLevel, int] = {}
        
        # Performance metrics
        self.metrics = {
            'disclosure_requests': 0,
            'level_transitions': 0,
            'average_disclosure_time_ms': 0.0,
            'size_efficiency_ratio': 0.0
        }
        
        logger.info(f"Initialized ProgressiveDisclosure with {max_levels} levels, "
                   f"base size: {base_size} bytes")
    
    def _initialize_lod_configurations(self) -> Dict[LODLevel, LODConfiguration]:
        """Initialize LOD level configurations based on 14KB principle."""
        
        configs = {}
        
        # Level 0: Building outline + major systems (2KB)
        configs[LODLevel.BUILDING_OUTLINE] = LODConfiguration(
            level=LODLevel.BUILDING_OUTLINE,
            max_size_bytes=self.base_size,
            description="Building outline + structural grid + major systems",
            object_filters={
                'systems': ['structural'],
                'object_types': [
                    'structural_beam', 'structural_column', 'structural_wall',
                    'structural_slab', 'structural_foundation'
                ],
                'include_major_only': True
            },
            priority_threshold=1  # Only structural (highest priority)
        )
        
        # Level 1: Room layouts + primary MEP (6KB total)
        configs[LODLevel.ROOM_LAYOUT] = LODConfiguration(
            level=LODLevel.ROOM_LAYOUT,
            max_size_bytes=6 * 1024,
            description="Room layouts + primary MEP systems",
            object_filters={
                'systems': ['structural', 'life_safety', 'electrical', 'hvac', 'plumbing'],
                'object_types': [
                    'fire_sprinkler', 'fire_alarm', 'emergency_exit',
                    'electrical_panel', 'hvac_unit', 'plumbing_fixture'
                ],
                'include_primary_only': True
            },
            priority_threshold=3  # Structural + Life Safety + MEP
        )
        
        # Level 2: Detailed components (12KB total)
        configs[LODLevel.DETAILED_COMPONENTS] = LODConfiguration(
            level=LODLevel.DETAILED_COMPONENTS,
            max_size_bytes=12 * 1024,
            description="Detailed building components",
            object_filters={
                'systems': ['structural', 'life_safety', 'electrical', 'hvac', 'plumbing', 'telecommunications'],
                'exclude_finishes': True,
                'include_detailed': True
            },
            priority_threshold=4  # All except finishes
        )
        
        # Level 3: Conflict zones + full details (14KB total)
        configs[LODLevel.CONFLICT_ZONES] = LODConfiguration(
            level=LODLevel.CONFLICT_ZONES,
            max_size_bytes=14 * 1024,
            description="Conflict zones + full building details",
            object_filters={
                'systems': 'all',
                'include_conflicts': True,
                'include_finishes': True
            },
            priority_threshold=5  # All systems including finishes
        )
        
        # Level 4: Full detail (unlimited streaming)
        configs[LODLevel.FULL_DETAIL] = LODConfiguration(
            level=LODLevel.FULL_DETAIL,
            max_size_bytes=float('inf'),
            description="Full detail streaming from server",
            object_filters={
                'systems': 'all',
                'include_everything': True
            },
            priority_threshold=5
        )
        
        return configs
    
    def get_disclosure_level(self, 
                           current_bundle_size: int, 
                           user_role: str,
                           viewport_area: float = None) -> LODLevel:
        """
        Determine appropriate LOD level based on constraints.
        
        Args:
            current_bundle_size: Current bundle size in bytes
            user_role: User role for bundle limits
            viewport_area: Viewport area for detail calculation
            
        Returns:
            Appropriate LOD level
        """
        self.metrics['disclosure_requests'] += 1
        
        # Role-based bundle limits
        role_limits = {
            'construction_worker': 8 * 1024,
            'superintendent': 12 * 1024,
            'architect': 14 * 1024,
            'full_featured': float('inf')
        }
        
        bundle_limit = role_limits.get(user_role, 14 * 1024)
        
        # Find highest LOD level that fits within constraints
        for level in reversed(list(LODLevel)):
            config = self.lod_configs.get(level)
            if not config:
                continue
            
            # Check size constraint
            if config.max_size_bytes <= bundle_limit:
                # If viewport area provided, consider detail requirements
                if viewport_area is not None:
                    required_level = self._calculate_viewport_lod(viewport_area)
                    if level.value >= required_level.value:
                        return level
                else:
                    return level
        
        # Fallback to lowest level
        return LODLevel.BUILDING_OUTLINE
    
    def _calculate_viewport_lod(self, viewport_area: float) -> LODLevel:
        """Calculate required LOD based on viewport area."""
        
        if viewport_area < 100:  # Very detailed view < 10x10
            return LODLevel.CONFLICT_ZONES
        elif viewport_area < 1000:  # Room detail < 30x30
            return LODLevel.DETAILED_COMPONENTS
        elif viewport_area < 10000:  # Building section < 100x100
            return LODLevel.ROOM_LAYOUT
        else:  # Building overview
            return LODLevel.BUILDING_OUTLINE
    
    def should_include_object(self, 
                            arxobject_data: Dict[str, Any], 
                            lod_level: LODLevel) -> bool:
        """
        Determine if object should be included at given LOD level.
        
        Args:
            arxobject_data: Object data dictionary
            lod_level: Target LOD level
            
        Returns:
            True if object should be included
        """
        config = self.lod_configs.get(lod_level)
        if not config:
            return False
        
        # Check system priority
        system_priority = arxobject_data.get('system_priority', 5)
        if system_priority > config.priority_threshold:
            return False
        
        # Apply object filters
        filters = config.object_filters
        
        # System filter
        if 'systems' in filters and filters['systems'] != 'all':
            object_system = arxobject_data.get('system_type', '')
            if isinstance(filters['systems'], list):
                if object_system not in filters['systems']:
                    return False
        
        # Object type filter
        if 'object_types' in filters:
            object_type = arxobject_data.get('type', '')
            if object_type not in filters['object_types']:
                return False
        
        # Exclude finishes filter
        if filters.get('exclude_finishes', False):
            if system_priority >= 5:  # Finishes have priority 5
                return False
        
        # Major objects only filter
        if filters.get('include_major_only', False):
            # Check if object is "major" (larger size or structural importance)
            volume = arxobject_data.get('volume', 0)
            if volume < 10.0:  # Less than 10 cubic feet considered minor
                return False
        
        # Primary objects only filter
        if filters.get('include_primary_only', False):
            # Include only primary MEP components
            object_type = arxobject_data.get('type', '')
            primary_types = {
                'electrical_panel', 'hvac_unit', 'hvac_duct', 'plumbing_fixture',
                'fire_sprinkler', 'fire_alarm', 'emergency_exit'
            }
            if object_type not in primary_types and system_priority > 2:
                return False
        
        return True
    
    def filter_objects_for_level(self, 
                                objects: List[Dict[str, Any]], 
                                lod_level: LODLevel) -> List[Dict[str, Any]]:
        """
        Filter objects list for specific LOD level.
        
        Args:
            objects: List of object data dictionaries
            lod_level: Target LOD level
            
        Returns:
            Filtered objects list
        """
        filtered_objects = []
        
        for obj in objects:
            if self.should_include_object(obj, lod_level):
                filtered_objects.append(obj)
        
        # Sort by priority for consistent loading order
        filtered_objects.sort(key=lambda x: (
            x.get('system_priority', 5),
            -x.get('volume', 0),  # Larger objects first
            x.get('id', '')
        ))
        
        logger.debug(f"Filtered {len(objects)} objects to {len(filtered_objects)} "
                    f"for LOD level {lod_level.value}")
        
        return filtered_objects
    
    def estimate_level_size(self, 
                          objects: List[Dict[str, Any]], 
                          lod_level: LODLevel) -> Dict[str, Any]:
        """
        Estimate bundle size for objects at LOD level.
        
        Args:
            objects: Objects to estimate size for
            lod_level: Target LOD level
            
        Returns:
            Size estimation details
        """
        filtered_objects = self.filter_objects_for_level(objects, lod_level)
        
        # Estimate serialized size
        total_size = 0
        object_sizes = []
        
        for obj in filtered_objects:
            # Estimate size based on JSON serialization
            obj_json = json.dumps(obj, separators=(',', ':'))
            obj_size = len(obj_json.encode('utf-8'))
            
            total_size += obj_size
            object_sizes.append({
                'id': obj.get('id', 'unknown'),
                'type': obj.get('type', 'unknown'),
                'size_bytes': obj_size
            })
        
        config = self.lod_configs.get(lod_level)
        max_size = config.max_size_bytes if config else 0
        
        return {
            'lod_level': lod_level.value,
            'total_size_bytes': total_size,
            'max_allowed_bytes': max_size,
            'utilization_percent': (total_size / max_size) * 100 if max_size > 0 else 0,
            'object_count': len(filtered_objects),
            'fits_in_budget': total_size <= max_size,
            'largest_objects': sorted(object_sizes, key=lambda x: x['size_bytes'], reverse=True)[:5],
            'size_by_system': self._calculate_size_by_system(filtered_objects)
        }
    
    def _calculate_size_by_system(self, objects: List[Dict[str, Any]]) -> Dict[str, int]:
        """Calculate size breakdown by building system."""
        size_by_system = {}
        
        for obj in objects:
            system = obj.get('system_type', 'unknown')
            obj_json = json.dumps(obj, separators=(',', ':'))
            obj_size = len(obj_json.encode('utf-8'))
            
            size_by_system[system] = size_by_system.get(system, 0) + obj_size
        
        return size_by_system
    
    def get_disclosure_strategy(self, 
                              total_objects: int,
                              target_bundle_size: int,
                              user_role: str) -> Dict[str, Any]:
        """
        Generate progressive disclosure strategy.
        
        Args:
            total_objects: Total objects available
            target_bundle_size: Target bundle size in bytes
            user_role: User role for optimization
            
        Returns:
            Disclosure strategy details
        """
        strategy = {
            'user_role': user_role,
            'target_bundle_size': target_bundle_size,
            'total_objects_available': total_objects,
            'recommended_levels': [],
            'loading_sequence': []
        }
        
        # Determine recommended levels based on bundle size
        for level in LODLevel:
            config = self.lod_configs.get(level)
            if not config:
                continue
            
            if config.max_size_bytes <= target_bundle_size:
                strategy['recommended_levels'].append({
                    'level': level.value,
                    'description': config.description,
                    'max_size_bytes': config.max_size_bytes,
                    'priority_threshold': config.priority_threshold
                })
        
        # Generate loading sequence
        if strategy['recommended_levels']:
            max_level = max(strategy['recommended_levels'], key=lambda x: x['level'])
            
            for level_value in range(max_level['level'] + 1):
                level = LODLevel(level_value)
                config = self.lod_configs.get(level)
                
                if config:
                    strategy['loading_sequence'].append({
                        'step': level_value + 1,
                        'level': level.value,
                        'description': config.description,
                        'load_trigger': self._get_load_trigger(level),
                        'estimated_objects': self._estimate_objects_at_level(total_objects, level)
                    })
        
        return strategy
    
    def _get_load_trigger(self, lod_level: LODLevel) -> str:
        """Get loading trigger description for LOD level."""
        triggers = {
            LODLevel.BUILDING_OUTLINE: "Application startup",
            LODLevel.ROOM_LAYOUT: "Navigate to building section",
            LODLevel.DETAILED_COMPONENTS: "Zoom into room or system",
            LODLevel.CONFLICT_ZONES: "Detect conflicts or detailed editing",
            LODLevel.FULL_DETAIL: "Stream on user interaction"
        }
        
        return triggers.get(lod_level, "User triggered")
    
    def _estimate_objects_at_level(self, total_objects: int, lod_level: LODLevel) -> int:
        """Estimate number of objects at LOD level."""
        # Simple estimation based on level
        level_ratios = {
            LODLevel.BUILDING_OUTLINE: 0.05,    # 5% of objects
            LODLevel.ROOM_LAYOUT: 0.20,         # 20% of objects
            LODLevel.DETAILED_COMPONENTS: 0.60,  # 60% of objects
            LODLevel.CONFLICT_ZONES: 0.85,      # 85% of objects
            LODLevel.FULL_DETAIL: 1.0           # 100% of objects
        }
        
        ratio = level_ratios.get(lod_level, 1.0)
        return int(total_objects * ratio)
    
    def update_level_metrics(self, lod_level: LODLevel, objects_loaded: int, size_bytes: int) -> None:
        """Update metrics for LOD level usage."""
        
        # Track objects by level
        if lod_level not in self.current_objects_by_level:
            self.current_objects_by_level[lod_level] = set()
        
        # Track size usage
        self.size_usage_by_level[lod_level] = size_bytes
        
        # Update efficiency metrics
        config = self.lod_configs.get(lod_level)
        if config and config.max_size_bytes > 0:
            efficiency = size_bytes / config.max_size_bytes
            self.metrics['size_efficiency_ratio'] = (
                (self.metrics['size_efficiency_ratio'] + efficiency) / 2
            )
        
        logger.debug(f"Updated metrics for LOD {lod_level.value}: "
                    f"{objects_loaded} objects, {size_bytes} bytes")
    
    def get_current_state(self) -> Dict[str, Any]:
        """Get current progressive disclosure state."""
        
        current_levels = []
        for level, object_ids in self.current_objects_by_level.items():
            config = self.lod_configs.get(level)
            size_used = self.size_usage_by_level.get(level, 0)
            
            current_levels.append({
                'level': level.value,
                'description': config.description if config else 'Unknown',
                'objects_loaded': len(object_ids),
                'size_used_bytes': size_used,
                'max_size_bytes': config.max_size_bytes if config else 0,
                'utilization_percent': (size_used / config.max_size_bytes * 100) 
                                     if config and config.max_size_bytes > 0 else 0
            })
        
        return {
            'active_levels': current_levels,
            'total_objects_loaded': sum(len(objects) for objects in self.current_objects_by_level.values()),
            'total_size_used': sum(self.size_usage_by_level.values()),
            'performance_metrics': self.metrics.copy(),
            'available_levels': [level.value for level in LODLevel]
        }
    
    def clear_level(self, lod_level: LODLevel) -> int:
        """Clear objects from specific LOD level."""
        
        objects_cleared = 0
        
        if lod_level in self.current_objects_by_level:
            objects_cleared = len(self.current_objects_by_level[lod_level])
            self.current_objects_by_level[lod_level].clear()
        
        if lod_level in self.size_usage_by_level:
            del self.size_usage_by_level[lod_level]
        
        logger.info(f"Cleared {objects_cleared} objects from LOD level {lod_level.value}")
        return objects_cleared