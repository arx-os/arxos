"""
Floor Plan Renderer - Generate 2D ASCII art floor plans
Converts building room and element data into 2D ASCII representations
"""

import logging
from typing import Dict, List, Any, Tuple, Optional

logger = logging.getLogger(__name__)

class FloorPlanRenderer:
    """
    Render 2D ASCII art floor plans from building data
    Creates top-down view of building layout
    """
    
    def __init__(self):
        # ASCII characters for different building elements
        self.element_chars = {
            'wall': '#',
            'door': 'D',
            'window': 'W',
            'room': ' ',
            'stairs': 'S',
            'elevator': 'E',
            'bathroom': 'B',
            'kitchen': 'K',
            'bedroom': 'R',
            'living': 'L',
            'office': 'O',
            'corridor': 'C'
        }
        
        # Default canvas size
        self.default_width = 80
        self.default_height = 40
    
    async def render_floor_plan(self, building_plan: Dict[str, Any]) -> str:
        """
        Render a 2D ASCII art floor plan
        
        Args:
            building_plan: Parsed building plan data
            
        Returns:
            2D ASCII art floor plan as string
        """
        try:
            # Extract building dimensions
            width, height = building_plan.get('dimensions', (self.default_width, self.default_height))
            
            # Create canvas
            canvas = self._create_canvas(width, height)
            
            # Render rooms
            rooms = building_plan.get('rooms', [])
            for room in rooms:
                canvas = self._render_room(canvas, room)
            
            # Render building elements
            elements = building_plan.get('elements', [])
            for element in elements:
                canvas = self._render_element(canvas, element)
            
            # Add building name and legend
            canvas = self._add_building_info(canvas, building_plan)
            
            return self._canvas_to_string(canvas)
            
        except Exception as e:
            logger.error(f"Error rendering floor plan: {e}")
            raise
    
    def _create_canvas(self, width: int, height: int) -> List[List[str]]:
        """Create empty ASCII canvas"""
        return [[' ' for _ in range(width)] for _ in range(height)]
    
    def _render_room(self, canvas: List[List[str]], room: Dict[str, Any]) -> List[List[str]]:
        """Render a room on the canvas"""
        try:
            # Get room coordinates and type
            coords = room.get('coordinates', [0, 0, 10, 10])
            room_type = room.get('type', 'general')
            
            # Get character for room type
            char = self.element_chars.get(room_type, ' ')
            
            # Fill room area
            x1, y1, x2, y2 = self._scale_coordinates(coords, len(canvas[0]), len(canvas))
            
            for y in range(max(0, y1), min(len(canvas), y2)):
                for x in range(max(0, x1), min(len(canvas[0]), x2)):
                    canvas[y][x] = char
            
            # Add room label
            room_id = room.get('id', '')
            if room_id and y1 < len(canvas) and x1 < len(canvas[0]):
                canvas[y1][x1] = room_id[0].upper()
            
        except Exception as e:
            logger.warning(f"Error rendering room: {e}")
        
        return canvas
    
    def _render_element(self, canvas: List[List[str]], element: Dict[str, Any]) -> List[List[str]]:
        """Render a building element on the canvas"""
        try:
            # Get element coordinates and type
            coords = element.get('coordinates', [0, 0, 0, 0])
            element_type = element.get('type', 'unknown')
            
            # Get character for element type
            char = self.element_chars.get(element_type, '?')
            
            # Scale coordinates to canvas
            x1, y1, x2, y2 = self._scale_coordinates(coords, len(canvas[0]), len(canvas))
            
            # Place element (center point)
            center_x = (x1 + x2) // 2
            center_y = (y1 + y2) // 2
            
            if (0 <= center_y < len(canvas) and 
                0 <= center_x < len(canvas[0])):
                canvas[center_y][center_x] = char
            
        except Exception as e:
            logger.warning(f"Error rendering element: {e}")
        
        return canvas
    
    def _scale_coordinates(self, coords: List[float], canvas_width: int, canvas_height: int) -> Tuple[int, int, int, int]:
        """Scale building coordinates to canvas coordinates"""
        try:
            x1, y1, x2, y2 = coords
            
            # Simple scaling - can be improved with proper coordinate transformation
            scale_x = canvas_width / 100.0  # Assume 100 units = canvas width
            scale_y = canvas_height / 100.0  # Assume 100 units = canvas height
            
            scaled_x1 = int(x1 * scale_x)
            scaled_y1 = int(y1 * scale_y)
            scaled_x2 = int(x2 * scale_x)
            scaled_y2 = int(y2 * scale_y)
            
            return scaled_x1, scaled_y1, scaled_x2, scaled_y2
            
        except Exception as e:
            logger.warning(f"Error scaling coordinates: {e}")
            return 0, 0, 10, 10
    
    def _add_building_info(self, canvas: List[List[str]], building_plan: Dict[str, Any]) -> List[List[str]]:
        """Add building name and legend to canvas"""
        try:
            building_name = building_plan.get('building_name', 'Unnamed Building')
            
            # Add building name at top
            if canvas and len(canvas) > 0:
                name_line = f" Building: {building_name} "
                for i, char in enumerate(name_line):
                    if i < len(canvas[0]):
                        canvas[0][i] = char
            
            # Add legend at bottom
            if len(canvas) > 2:
                legend_line = " Legend: #=Wall D=Door W=Window R=Room "
                for i, char in enumerate(legend_line):
                    if i < len(canvas[-2]) and i < len(legend_line):
                        canvas[-2][i] = char
            
        except Exception as e:
            logger.warning(f"Error adding building info: {e}")
        
        return canvas
    
    def _canvas_to_string(self, canvas: List[List[str]]) -> str:
        """Convert canvas to string representation"""
        try:
            lines = []
            for row in canvas:
                lines.append(''.join(row))
            return '\n'.join(lines)
        except Exception as e:
            logger.error(f"Error converting canvas to string: {e}")
            return "Error generating floor plan"
