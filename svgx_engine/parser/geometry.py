"""
SVGX Geometry module for geometric calculations and transformations.
"""

import math
import logging
from typing import Dict, Any, List, Optional, Tuple

logger = logging.getLogger(__name__)


class SVGXGeometry:
    """Handles geometric calculations for SVGX elements."""
    
    def __init__(self):
        self.precision = 0.001  # Default precision in mm
    
    def calculate_area(self, element) -> float:
        """Calculate area of an element."""
        try:
            if element.tag == 'rect':
                width = float(element.attributes.get('width', 0))
                height = float(element.attributes.get('height', 0))
                return width * height
            elif element.tag == 'circle':
                radius = float(element.attributes.get('r', 0))
                return math.pi * radius * radius
            elif element.tag == 'ellipse':
                rx = float(element.attributes.get('rx', 0))
                ry = float(element.attributes.get('ry', 0))
                return math.pi * rx * ry
            else:
                return 0.0
        except Exception as e:
            logger.error(f"Failed to calculate area: {e}")
            return 0.0
    
    def calculate_perimeter(self, element) -> float:
        """Calculate perimeter of an element."""
        try:
            if element.tag == 'rect':
                width = float(element.attributes.get('width', 0))
                height = float(element.attributes.get('height', 0))
                return 2 * (width + height)
            elif element.tag == 'circle':
                radius = float(element.attributes.get('r', 0))
                return 2 * math.pi * radius
            elif element.tag == 'ellipse':
                rx = float(element.attributes.get('rx', 0))
                ry = float(element.attributes.get('ry', 0))
                # Approximation for ellipse perimeter
                return math.pi * (3 * (rx + ry) - math.sqrt((3 * rx + ry) * (rx + 3 * ry)))
            else:
                return 0.0
        except Exception as e:
            logger.error(f"Failed to calculate perimeter: {e}")
            return 0.0
    
    def get_bounding_box(self, element) -> Tuple[float, float, float, float]:
        """Get bounding box of an element."""
        try:
            if element.tag == 'rect':
                x = float(element.attributes.get('x', 0))
                y = float(element.attributes.get('y', 0))
                width = float(element.attributes.get('width', 0))
                height = float(element.attributes.get('height', 0))
                return (x, y, x + width, y + height)
            elif element.tag == 'circle':
                cx = float(element.attributes.get('cx', 0))
                cy = float(element.attributes.get('cy', 0))
                r = float(element.attributes.get('r', 0))
                return (cx - r, cy - r, cx + r, cy + r)
            else:
                return (0, 0, 0, 0)
        except Exception as e:
            logger.error(f"Failed to get bounding box: {e}")
            return (0, 0, 0, 0)
    
    def convert_units(self, value: str, from_unit: str, to_unit: str) -> float:
        """Convert between different units."""
        try:
            # Parse value
            if isinstance(value, str):
                numeric_value = float(value.replace(from_unit, ''))
            else:
                numeric_value = float(value)
            
            # Conversion factors (to mm)
            unit_factors = {
                'mm': 1.0,
                'cm': 10.0,
                'm': 1000.0,
                'in': 25.4,
                'ft': 304.8
            }
            
            # Convert to mm first
            mm_value = numeric_value * unit_factors.get(from_unit, 1.0)
            
            # Convert from mm to target unit
            target_factor = unit_factors.get(to_unit, 1.0)
            return mm_value / target_factor
            
        except Exception as e:
            logger.error(f"Failed to convert units: {e}")
            return 0.0 