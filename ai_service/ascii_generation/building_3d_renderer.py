"""
Building 3D Renderer - Generate 3D ASCII art building representations
Creates isometric-style 3D views of buildings from parsed data
"""

import logging
from typing import Dict, List, Any, Tuple, Optional

logger = logging.getLogger(__name__)

class Building3DRenderer:
    """
    Render 3D ASCII art building representations
    Creates isometric-style 3D views showing building height and structure
    """
    
    def __init__(self):
        # ASCII characters for 3D building elements
        self.element_chars = {
            'wall': '|',
            'door': 'D',
            'window': 'W',
            'floor': '_',
            'ceiling': '=',
            'stairs': '/',
            'elevator': 'E',
            'roof': '^'
        }
        
        # Default 3D canvas dimensions
        self.default_width = 60
        self.default_height = 30
        self.default_depth = 20
    
    async def render_3d_building(self, building_plan: Dict[str, Any]) -> str:
        """
        Render a 3D ASCII art building representation
        
        Args:
            building_plan: Parsed building plan data
            
        Returns:
            3D ASCII art building representation as string
        """
        try:
            # Extract building dimensions
            width, height = building_plan.get('dimensions', (self.default_width, self.default_height))
            floors = building_plan.get('floors', ['Ground Floor'])
            
            # Create 3D canvas
            canvas = self._create_3d_canvas(width, height, len(floors))
            
            # Render each floor
            for floor_idx, floor_name in enumerate(floors):
                canvas = self._render_floor(canvas, building_plan, floor_idx, floor_name)
            
            # Render building elements in 3D
            elements = building_plan.get('elements', [])
            for element in elements:
                canvas = self._render_3d_element(canvas, element, floors)
            
            # Add building name and 3D legend
            canvas = self._add_3d_building_info(canvas, building_plan)
            
            return self._canvas_3d_to_string(canvas)
            
        except Exception as e:
            logger.error(f"Error rendering 3D building: {e}")
            raise
    
    def _create_3d_canvas(self, width: int, height: int, depth: int) -> List[List[List[str]]]:
        """Create empty 3D ASCII canvas"""
        canvas = []
        for z in range(depth):
            floor = []
            for y in range(height):
                row = []
                for x in range(width):
                    row.append(' ')
                floor.append(row)
            canvas.append(floor)
        return canvas
    
    def _render_floor(self, canvas: List[List[List[str]]], building_plan: Dict[str, Any], 
                      floor_idx: int, floor_name: str) -> List[List[List[str]]]:
        """Render a floor level on the 3D canvas"""
        try:
            if floor_idx >= len(canvas):
                return canvas
            
            # Get rooms for this floor
            rooms = building_plan.get('rooms', [])
            
            # Render floor plane
            floor_canvas = canvas[floor_idx]
            for y in range(len(floor_canvas)):
                for x in range(len(floor_canvas[0])):
                    floor_canvas[y][x] = '_'  # Floor surface
            
            # Add floor label
            if floor_canvas and len(floor_canvas) > 0:
                label = f" {floor_name} "
                for i, char in enumerate(label):
                    if i < len(floor_canvas[0]):
                        floor_canvas[0][i] = char
            
        except Exception as e:
            logger.warning(f"Error rendering floor {floor_idx}: {e}")
        
        return canvas
    
    def _render_3d_element(self, canvas: List[List[List[str]]], element: Dict[str, Any], 
                          floors: List[str]) -> List[List[List[str]]]:
        """Render a building element in 3D space"""
        try:
            # Get element properties
            element_type = element.get('type', 'unknown')
            coords = element.get('coordinates', [0, 0, 0, 0])
            source_page = element.get('source_page', 0)
            
            # Get character for element type
            char = self.element_chars.get(element_type, '?')
            
            # Determine 3D position
            if source_page < len(canvas):
                z = source_page  # Use page number as Z coordinate
                
                # Scale coordinates to canvas
                x1, y1, x2, y2 = self._scale_3d_coordinates(coords, len(canvas[z][0]), len(canvas[z]))
                
                # Place element in 3D space
                center_x = (x1 + x2) // 2
                center_y = (y1 + y2) // 2
                
                if (0 <= z < len(canvas) and 
                    0 <= center_y < len(canvas[z]) and 
                    0 <= center_x < len(canvas[z][0])):
                    canvas[z][center_y][center_x] = char
                    
                    # Add height if it's a wall or structural element
                    if element_type in ['wall', 'stairs', 'elevator']:
                        for h in range(z + 1, min(z + 3, len(canvas))):
                            if (0 <= center_y < len(canvas[h]) and 
                                0 <= center_x < len(canvas[h][0])):
                                canvas[h][center_y][center_x] = '|'
            
        except Exception as e:
            logger.warning(f"Error rendering 3D element: {e}")
        
        return canvas
    
    def _scale_3d_coordinates(self, coords: List[float], canvas_width: int, canvas_height: int) -> Tuple[int, int, int, int]:
        """Scale building coordinates to 3D canvas coordinates"""
        try:
            x1, y1, x2, y2 = coords
            
            # Simple scaling for 3D
            scale_x = canvas_width / 100.0
            scale_y = canvas_height / 100.0
            
            scaled_x1 = int(x1 * scale_x)
            scaled_y1 = int(y1 * scale_y)
            scaled_x2 = int(x2 * scale_x)
            scaled_y2 = int(y2 * scale_y)
            
            return scaled_x1, scaled_y1, scaled_x2, scaled_y2
            
        except Exception as e:
            logger.warning(f"Error scaling 3D coordinates: {e}")
            return 0, 0, 10, 10
    
    def _add_3d_building_info(self, canvas: List[List[List[str]]], building_plan: Dict[str, Any]) -> List[List[List[str]]]:
        """Add building name and 3D legend to canvas"""
        try:
            building_name = building_plan.get('building_name', 'Unnamed Building')
            
            # Add building name at top of first floor
            if canvas and len(canvas) > 0 and len(canvas[0]) > 0:
                name_line = f" 3D Building: {building_name} "
                for i, char in enumerate(name_line):
                    if i < len(canvas[0][0]):
                        canvas[0][0][i] = char
            
            # Add 3D legend at bottom of last floor
            if canvas and len(canvas) > 0 and len(canvas[-1]) > 1:
                legend_line = " 3D Legend: |=Wall D=Door W=Window _=Floor "
                for i, char in enumerate(legend_line):
                    if i < len(canvas[-1][-2]) and i < len(legend_line):
                        canvas[-1][-2][i] = char
            
        except Exception as e:
            logger.warning(f"Error adding 3D building info: {e}")
        
        return canvas
    
    def _canvas_3d_to_string(self, canvas: List[List[List[str]]]) -> str:
        """Convert 3D canvas to string representation"""
        try:
            lines = []
            
            # Render each floor level
            for z, floor in enumerate(canvas):
                lines.append(f"\n--- Floor {z} ---")
                for y, row in enumerate(floor):
                    lines.append(''.join(row))
            
            return '\n'.join(lines)
            
        except Exception as e:
            logger.error(f"Error converting 3D canvas to string: {e}")
            return "Error generating 3D building representation"
