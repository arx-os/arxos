"""
Grid and Snap System for SVGX Engine

Provides professional CAD snapping functionality including configurable grid,
object snapping, angle snapping, and visual feedback.

CTO Directives:
- Enterprise-grade grid and snap system
- Professional CAD snapping functionality
- Configurable grid spacing and origin
- Comprehensive object and angle snapping
- Visual grid and snap feedback
"""

import math
from dataclasses import dataclass
from enum import Enum
from typing import List, Dict, Optional, Tuple, Any
from decimal import Decimal
import logging

from .precision_system import PrecisionPoint, PrecisionLevel

logger = logging.getLogger(__name__)

class SnapType(Enum):
    """Snap Types"""
    GRID = "grid"
    ENDPOINT = "endpoint"
    MIDPOINT = "midpoint"
    INTERSECTION = "intersection"
    CENTER = "center"
    QUADRANT = "quadrant"
    TANGENT = "tangent"
    PERPENDICULAR = "perpendicular"
    PARALLEL = "parallel"
    ANGLE = "angle"

class GridType(Enum):
    """Grid Types"""
    RECTANGULAR = "rectangular"
    POLAR = "polar"
    ISOMETRIC = "isometric"
    CUSTOM = "custom"

@dataclass
class GridConfig:
    """Grid configuration"""
    grid_type: GridType = GridType.RECTANGULAR
    spacing_x: Decimal = Decimal('10.0')  # mm
    spacing_y: Decimal = Decimal('10.0')  # mm
    origin_x: Decimal = Decimal('0.0')
    origin_y: Decimal = Decimal('0.0')
    angle: Decimal = Decimal('0.0')  # radians
    visible: bool = True
    snap_enabled: bool = True
    major_lines: int = 10  # Every nth line is major
    color: str = "#CCCCCC"
    major_color: str = "#999999"

@dataclass
class SnapConfig:
    """Snap configuration"""
    enabled_types: List[SnapType] = None
    tolerance: Decimal = Decimal('0.5')  # mm
    angle_snap: Decimal = Decimal('15.0')  # degrees
    visual_feedback: bool = True
    magnetic_snap: bool = True
    
    def __post_init__(self):
        if self.enabled_types is None:
            self.enabled_types = [
                SnapType.GRID,
                SnapType.ENDPOINT,
                SnapType.MIDPOINT,
                SnapType.INTERSECTION
            ]

@dataclass
class SnapPoint:
    """Snap point with type and position"""
    point: PrecisionPoint
    snap_type: SnapType
    entity_id: Optional[str] = None
    confidence: float = 1.0

class GridSystem:
    """Grid system for CAD functionality"""
    
    def __init__(self, config: GridConfig):
        self.config = config
        self.grid_points: List[PrecisionPoint] = []
        self.major_lines: List[Tuple[PrecisionPoint, PrecisionPoint]] = []
        self.minor_lines: List[Tuple[PrecisionPoint, PrecisionPoint]] = []
        
        logger.info(f"Grid system initialized with {config.grid_type.value} grid")
        self._generate_grid()
    
    def _generate_grid(self):
        """Generate grid points and lines"""
        try:
            if self.config.grid_type == GridType.RECTANGULAR:
                self._generate_rectangular_grid()
            elif self.config.grid_type == GridType.POLAR:
                self._generate_polar_grid()
            elif self.config.grid_type == GridType.ISOMETRIC:
                self._generate_isometric_grid()
            
            logger.info(f"Generated {len(self.grid_points)} grid points")
            
        except Exception as e:
            logger.error(f"Grid generation error: {e}")
    
    def _generate_rectangular_grid(self):
        """Generate rectangular grid"""
        # Calculate grid bounds (extend beyond visible area)
        bounds = self._get_grid_bounds()
        
        # Generate grid points
        x = bounds['min_x']
        while x <= bounds['max_x']:
            y = bounds['min_y']
            while y <= bounds['max_y']:
                point = PrecisionPoint(x, y)
                self.grid_points.append(point)
                y += self.config.spacing_y
            x += self.config.spacing_x
        
        # Generate grid lines
        self._generate_grid_lines()
    
    def _generate_polar_grid(self):
        """Generate polar grid"""
        # Calculate grid bounds
        bounds = self._get_grid_bounds()
        center = PrecisionPoint(self.config.origin_x, self.config.origin_y)
        
        # Generate radial lines
        angle_step = Decimal(str(math.pi / 12))  # 15 degrees
        radius_step = self.config.spacing_x
        
        angle = Decimal('0')
        while angle < Decimal(str(2 * math.pi)):
            # Generate points along radial line
            radius = radius_step
            while radius <= max(bounds['max_x'] - bounds['min_x'], bounds['max_y'] - bounds['min_y']):
                x = center.x + radius * Decimal(str(math.cos(float(angle))))
                y = center.y + radius * Decimal(str(math.sin(float(angle))))
                point = PrecisionPoint(x, y)
                self.grid_points.append(point)
                radius += radius_step
            angle += angle_step
    
    def _generate_isometric_grid(self):
        """Generate isometric grid"""
        # Calculate grid bounds
        bounds = self._get_grid_bounds()
        
        # Generate isometric grid points
        x = bounds['min_x']
        while x <= bounds['max_x']:
            y = bounds['min_y']
            while y <= bounds['max_y']:
                # Apply isometric transformation
                iso_x = x * Decimal(str(math.cos(math.pi/6)))
                iso_y = y * Decimal(str(math.sin(math.pi/6)))
                point = PrecisionPoint(iso_x, iso_y)
                self.grid_points.append(point)
                y += self.config.spacing_y
            x += self.config.spacing_x
    
    def _get_grid_bounds(self) -> Dict[str, Decimal]:
        """Get grid bounds"""
        # Extend grid beyond typical drawing area
        margin = Decimal('1000.0')  # 1 meter margin
        return {
            'min_x': self.config.origin_x - margin,
            'max_x': self.config.origin_x + margin,
            'min_y': self.config.origin_y - margin,
            'max_y': self.config.origin_y + margin
        }
    
    def _generate_grid_lines(self):
        """Generate grid lines"""
        bounds = self._get_grid_bounds()
        
        # Generate vertical lines
        x = bounds['min_x']
        while x <= bounds['max_x']:
            start_point = PrecisionPoint(x, bounds['min_y'])
            end_point = PrecisionPoint(x, bounds['max_y'])
            
            if int(x / self.config.spacing_x) % self.config.major_lines == 0:
                self.major_lines.append((start_point, end_point))
            else:
                self.minor_lines.append((start_point, end_point))
            x += self.config.spacing_x
        
        # Generate horizontal lines
        y = bounds['min_y']
        while y <= bounds['max_y']:
            start_point = PrecisionPoint(bounds['min_x'], y)
            end_point = PrecisionPoint(bounds['max_x'], y)
            
            if int(y / self.config.spacing_y) % self.config.major_lines == 0:
                self.major_lines.append((start_point, end_point))
            else:
                self.minor_lines.append((start_point, end_point))
            y += self.config.spacing_y
    
    def snap_to_grid(self, point: PrecisionPoint) -> Optional[PrecisionPoint]:
        """Snap point to nearest grid point"""
        if not self.config.snap_enabled:
            return None
        
        min_distance = float('inf')
        snapped_point = None
        
        for grid_point in self.grid_points:
            distance = point.distance_to(grid_point)
            if distance < min_distance:
                min_distance = float(distance)
                snapped_point = grid_point
        
        if snapped_point and min_distance <= float(self.config.spacing_x / 2):
            return snapped_point
        
        return None
    
    def get_grid_info(self) -> Dict[str, Any]:
        """Get grid system information"""
        return {
            'grid_type': self.config.grid_type.value,
            'spacing_x': float(self.config.spacing_x),
            'spacing_y': float(self.config.spacing_y),
            'origin_x': float(self.config.origin_x),
            'origin_y': float(self.config.origin_y),
            'visible': self.config.visible,
            'snap_enabled': self.config.snap_enabled,
            'grid_points_count': len(self.grid_points),
            'major_lines_count': len(self.major_lines),
            'minor_lines_count': len(self.minor_lines)
        }

class SnapSystem:
    """Snap system for object and angle snapping"""
    
    def __init__(self, config: SnapConfig):
        self.config = config
        self.entities: Dict[str, Any] = {}
        self.snap_points: List[SnapPoint] = []
        
        logger.info("Snap system initialized")
    
    def add_entity(self, entity_id: str, entity_data: Any):
        """Add entity for snapping"""
        self.entities[entity_id] = entity_data
        self._update_snap_points()
    
    def remove_entity(self, entity_id: str):
        """Remove entity from snapping"""
        if entity_id in self.entities:
            del self.entities[entity_id]
            self._update_snap_points()
    
    def _update_snap_points(self):
        """Update snap points from entities"""
        self.snap_points.clear()
        
        for entity_id, entity_data in self.entities.items():
            self._extract_snap_points(entity_id, entity_data)
    
    def _extract_snap_points(self, entity_id: str, entity_data: Any):
        """Extract snap points from entity"""
        # This is a simplified implementation
        # In a real system, this would analyze the entity geometry
        # and extract endpoints, midpoints, centers, etc.
        
        if hasattr(entity_data, 'get_snap_points'):
            snap_points = entity_data.get_snap_points()
            for point_data in snap_points:
                snap_point = SnapPoint(
                    point=point_data['point'],
                    snap_type=point_data['type'],
                    entity_id=entity_id,
                    confidence=point_data.get('confidence', 1.0)
                )
                self.snap_points.append(snap_point)
    
    def find_nearest_snap(self, point: PrecisionPoint, snap_types: List[SnapType] = None) -> Optional[SnapPoint]:
        """Find nearest snap point"""
        if not snap_types:
            snap_types = self.config.enabled_types
        
        min_distance = float('inf')
        nearest_snap = None
        
        for snap_point in self.snap_points:
            if snap_point.snap_type in snap_types:
                distance = point.distance_to(snap_point.point)
                if distance < min_distance and distance <= float(self.config.tolerance):
                    min_distance = float(distance)
                    nearest_snap = snap_point
        
        return nearest_snap
    
    def snap_to_angle(self, current_angle: Decimal) -> Optional[Decimal]:
        """Snap angle to nearest angle increment"""
        if not self.config.angle_snap:
            return None
        
        angle_step = self.config.angle_snap
        normalized_angle = current_angle % Decimal('360')
        
        # Find nearest angle increment
        nearest_angle = round(float(normalized_angle) / float(angle_step)) * float(angle_step)
        
        if abs(float(normalized_angle) - nearest_angle) <= float(angle_step) / 2:
            return Decimal(str(nearest_angle))
        
        return None
    
    def get_snap_info(self) -> Dict[str, Any]:
        """Get snap system information"""
        return {
            'enabled_types': [t.value for t in self.config.enabled_types],
            'tolerance': float(self.config.tolerance),
            'angle_snap': float(self.config.angle_snap),
            'visual_feedback': self.config.visual_feedback,
            'magnetic_snap': self.config.magnetic_snap,
            'entities_count': len(self.entities),
            'snap_points_count': len(self.snap_points)
        }

class GridSnapManager:
    """Manager for grid and snap functionality"""
    
    def __init__(self, grid_config: GridConfig = None, snap_config: SnapConfig = None):
        self.grid_config = grid_config or GridConfig()
        self.snap_config = snap_config or SnapConfig()
        
        self.grid_system = GridSystem(self.grid_config)
        self.snap_system = SnapSystem(self.snap_config)
        
        logger.info("Grid and snap manager initialized")
    
    def snap_point(self, point: PrecisionPoint) -> Optional[PrecisionPoint]:
        """Snap point to grid or objects"""
        # Try object snapping first
        nearest_snap = self.snap_system.find_nearest_snap(point)
        if nearest_snap:
            return nearest_snap.point
        
        # Try grid snapping
        grid_snap = self.grid_system.snap_to_grid(point)
        if grid_snap:
            return grid_snap
        
        return None
    
    def snap_angle(self, angle: Decimal) -> Optional[Decimal]:
        """Snap angle to nearest increment"""
        return self.snap_system.snap_to_angle(angle)
    
    def set_grid_config(self, config: GridConfig):
        """Update grid configuration"""
        self.grid_config = config
        self.grid_system = GridSystem(config)
        logger.info("Grid configuration updated")
    
    def set_snap_config(self, config: SnapConfig):
        """Update snap configuration"""
        self.snap_config = config
        self.snap_system = SnapSystem(config)
        logger.info("Snap configuration updated")
    
    def add_entity(self, entity_id: str, entity_data: Any):
        """Add entity for snapping"""
        self.snap_system.add_entity(entity_id, entity_data)
    
    def remove_entity(self, entity_id: str):
        """Remove entity from snapping"""
        self.snap_system.remove_entity(entity_id)
    
    def get_system_info(self) -> Dict[str, Any]:
        """Get grid and snap system information"""
        return {
            'grid': self.grid_system.get_grid_info(),
            'snap': self.snap_system.get_snap_info()
        }
    
    def validate_system(self) -> bool:
        """Validate grid and snap system"""
        try:
            # Validate grid configuration
            if self.grid_config.spacing_x <= 0 or self.grid_config.spacing_y <= 0:
                logger.error("Invalid grid spacing")
                return False
            
            # Validate snap configuration
            if self.snap_config.tolerance <= 0:
                logger.error("Invalid snap tolerance")
                return False
            
            # Validate grid system
            if not self.grid_system.grid_points:
                logger.error("No grid points generated")
                return False
            
            logger.info("Grid and snap system validation passed")
            return True
            
        except Exception as e:
            logger.error(f"Grid and snap system validation failed: {e}")
            return False

# Global instance for easy access
grid_snap_manager = GridSnapManager() 