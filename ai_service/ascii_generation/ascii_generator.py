"""
ASCII Generator - Main class for converting building plans to ASCII art
Coordinates 2D and 3D ASCII generation from parsed building data
"""

import logging
from typing import Dict, List, Any, Optional
from .floor_plan_renderer import FloorPlanRenderer
from .building_3d_renderer import Building3DRenderer

logger = logging.getLogger(__name__)

class ASCIIGenerator:
    """
    Main ASCII art generator for building plans
    Coordinates 2D floor plan and 3D building rendering
    """
    
    def __init__(self):
        self.floor_renderer = FloorPlanRenderer()
        self.building_3d_renderer = Building3DRenderer()
    
    async def generate_2d_floor_plan(self, building_plan: Dict[str, Any]) -> str:
        """
        Generate 2D ASCII art floor plan
        
        Args:
            building_plan: Parsed building plan data
            
        Returns:
            2D ASCII art representation of the floor plan
        """
        try:
            return await self.floor_renderer.render_floor_plan(building_plan)
        except Exception as e:
            logger.error(f"Error generating 2D floor plan: {e}")
            raise
    
    async def generate_3d_building(self, building_plan: Dict[str, Any]) -> str:
        """
        Generate 3D ASCII art building representation
        
        Args:
            building_plan: Parsed building plan data
            
        Returns:
            3D ASCII art representation of the building
        """
        try:
            return await self.building_3d_renderer.render_3d_building(building_plan)
        except Exception as e:
            logger.error(f"Error generating 3D building: {e}")
            raise
    
    async def generate_both_representations(self, building_plan: Dict[str, Any]) -> Dict[str, str]:
        """
        Generate both 2D and 3D ASCII representations
        
        Args:
            building_plan: Parsed building plan data
            
        Returns:
            Dictionary with both 2D and 3D ASCII art
        """
        try:
            floor_plan_2d = await self.generate_2d_floor_plan(building_plan)
            building_3d = await self.generate_3d_building(building_plan)
            
            return {
                'floor_plan_2d': floor_plan_2d,
                'building_3d': building_3d
            }
        except Exception as e:
            logger.error(f"Error generating both representations: {e}")
            raise
