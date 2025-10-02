"""
Spatial Operations Module

This module provides spatial query operations for IFC models including:
- Spatial containment queries
- Geometric intersection tests
- Bounding box operations
- Spatial relationship analysis
"""

import ifcopenshell
import ifcopenshell.util.element
import ifcopenshell.util.placement
import ifcopenshell.util.unit
from typing import Dict, List, Tuple, Any, Optional
import logging
import math
from datetime import datetime

logger = logging.getLogger(__name__)


class SpatialQuery:
    """Spatial query operations for IFC models"""
    
    def __init__(self):
        self.spatial_entities = [
            'IfcSpace',
            'IfcWall',
            'IfcSlab',
            'IfcBeam',
            'IfcColumn',
            'IfcDoor',
            'IfcWindow',
            'IfcBuildingStorey'
        ]

    def query_within_bounds(self, model, bounds: Dict[str, List[float]]) -> Dict[str, Any]:
        """
        Find entities within specified 3D bounds
        
        Args:
            model: IfcOpenShell model
            bounds: Dictionary with 'min' and 'max' coordinates [x, y, z]
            
        Returns:
            Dictionary with query results
        """
        try:
            min_coords = bounds.get('min', [0, 0, 0])
            max_coords = bounds.get('max', [100, 100, 100])
            
            results = []
            
            for entity_type in self.spatial_entities:
                entities = model.by_type(entity_type)
                for entity in entities:
                    if self._is_entity_within_bounds(entity, min_coords, max_coords):
                        entity_info = self._extract_entity_info(entity)
                        entity_info['type'] = entity_type
                        results.append(entity_info)
            
            return {
                "success": True,
                "query_type": "within_bounds",
                "bounds": bounds,
                "results": results,
                "total_found": len(results),
                "metadata": {
                    "timestamp": datetime.utcnow().isoformat(),
                    "entity_types_searched": self.spatial_entities
                }
            }
            
        except Exception as e:
            logger.error(f"Spatial query failed: {e}")
            return {
                "success": False,
                "error": f"Spatial query failed: {str(e)}",
                "query_type": "within_bounds",
                "bounds": bounds
            }

    def query_spatial_relationships(self, model, entity_id: str) -> Dict[str, Any]:
        """
        Find spatial relationships for a specific entity
        
        Args:
            model: IfcOpenShell model
            entity_id: GlobalId of the entity to analyze
            
        Returns:
            Dictionary with relationship information
        """
        try:
            # Find the entity
            entity = model.by_id(entity_id)
            if not entity:
                return {
                    "success": False,
                    "error": f"Entity with ID {entity_id} not found",
                    "entity_id": entity_id
                }
            
            relationships = {
                "contained_in": [],
                "contains": [],
                "adjacent_to": [],
                "overlaps_with": []
            }
            
            # Find containment relationships
            if hasattr(entity, 'ContainedInStructure'):
                for container in entity.ContainedInStructure:
                    relationships["contained_in"].append(self._extract_entity_info(container))
            
            # Find entities this entity contains
            if hasattr(entity, 'ContainsElements'):
                for contained in entity.ContainsElements:
                    relationships["contains"].append(self._extract_entity_info(contained))
            
            # Find adjacent entities (simplified)
            adjacent = self._find_adjacent_entities(model, entity)
            relationships["adjacent_to"] = [self._extract_entity_info(adj) for adj in adjacent]
            
            return {
                "success": True,
                "query_type": "spatial_relationships",
                "entity_id": entity_id,
                "entity_type": entity.is_a(),
                "relationships": relationships,
                "metadata": {
                    "timestamp": datetime.utcnow().isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"Relationship query failed: {e}")
            return {
                "success": False,
                "error": f"Relationship query failed: {str(e)}",
                "entity_id": entity_id
            }

    def query_by_proximity(self, model, center: List[float], radius: float) -> Dict[str, Any]:
        """
        Find entities within a specified radius of a point
        
        Args:
            model: IfcOpenShell model
            center: Center point [x, y, z]
            radius: Search radius
            
        Returns:
            Dictionary with proximity results
        """
        try:
            results = []
            
            for entity_type in self.spatial_entities:
                entities = model.by_type(entity_type)
                for entity in entities:
                    entity_center = self._get_entity_center(entity)
                    if entity_center and self._distance_3d(center, entity_center) <= radius:
                        entity_info = self._extract_entity_info(entity)
                        entity_info['type'] = entity_type
                        entity_info['distance'] = self._distance_3d(center, entity_center)
                        results.append(entity_info)
            
            # Sort by distance
            results.sort(key=lambda x: x.get('distance', float('inf')))
            
            return {
                "success": True,
                "query_type": "proximity",
                "center": center,
                "radius": radius,
                "results": results,
                "total_found": len(results),
                "metadata": {
                    "timestamp": datetime.utcnow().isoformat(),
                    "entity_types_searched": self.spatial_entities
                }
            }
            
        except Exception as e:
            logger.error(f"Proximity query failed: {e}")
            return {
                "success": False,
                "error": f"Proximity query failed: {str(e)}",
                "center": center,
                "radius": radius
            }

    def query_spatial_statistics(self, model) -> Dict[str, Any]:
        """
        Generate spatial statistics for the model
        
        Args:
            model: IfcOpenShell model
            
        Returns:
            Dictionary with spatial statistics
        """
        try:
            stats = {
                "total_entities": 0,
                "entity_counts": {},
                "spatial_coverage": {},
                "bounding_box": None,
                "spatial_density": 0.0
            }
            
            all_coords = []
            
            for entity_type in self.spatial_entities:
                entities = model.by_type(entity_type)
                stats["entity_counts"][entity_type] = len(entities)
                stats["total_entities"] += len(entities)
                
                # Collect coordinates for bounding box calculation
                for entity in entities:
                    coords = self._get_entity_coordinates(entity)
                    if coords:
                        all_coords.extend(coords)
            
            # Calculate bounding box
            if all_coords:
                stats["bounding_box"] = self._calculate_bounding_box(all_coords)
                stats["spatial_coverage"] = self._calculate_spatial_coverage(stats["bounding_box"])
                stats["spatial_density"] = stats["total_entities"] / stats["spatial_coverage"]["volume"]
            
            return {
                "success": True,
                "query_type": "spatial_statistics",
                "statistics": stats,
                "metadata": {
                    "timestamp": datetime.utcnow().isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"Spatial statistics query failed: {e}")
            return {
                "success": False,
                "error": f"Spatial statistics query failed: {str(e)}"
            }

    def _is_entity_within_bounds(self, entity, min_coords: List[float], max_coords: List[float]) -> bool:
        """Check if entity is within specified bounds"""
        try:
            coords = self._get_entity_coordinates(entity)
            if not coords:
                return False
            
            for coord in coords:
                if (min_coords[0] <= coord[0] <= max_coords[0] and
                    min_coords[1] <= coord[1] <= max_coords[1] and
                    min_coords[2] <= coord[2] <= max_coords[2]):
                    return True
            
            return False
            
        except Exception as e:
            logger.warning(f"Bounds check failed for entity: {e}")
            return False

    def _get_entity_coordinates(self, entity) -> List[List[float]]:
        """Extract coordinates from an entity"""
        try:
            coords = []
            
            # Try to get placement
            if hasattr(entity, 'ObjectPlacement') and entity.ObjectPlacement:
                placement = entity.ObjectPlacement
                if hasattr(placement, 'RelativePlacement') and placement.RelativePlacement:
                    location = placement.RelativePlacement.Location
                    if hasattr(location, 'Coordinates') and location.Coordinates:
                        coords.append([float(c) for c in location.Coordinates])
            
            # Try to get geometry bounds
            if hasattr(entity, 'Representation') and entity.Representation:
                # This is a simplified approach - real implementation would use
                # proper geometric analysis
                pass
            
            return coords
            
        except Exception as e:
            logger.warning(f"Coordinate extraction failed: {e}")
            return []

    def _get_entity_center(self, entity) -> Optional[List[float]]:
        """Get the center point of an entity"""
        coords = self._get_entity_coordinates(entity)
        if not coords:
            return None
        
        # Calculate center of all coordinates
        center = [0.0, 0.0, 0.0]
        for coord in coords:
            center[0] += coord[0]
            center[1] += coord[1]
            center[2] += coord[2]
        
        if coords:
            center[0] /= len(coords)
            center[1] /= len(coords)
            center[2] /= len(coords)
        
        return center

    def _extract_entity_info(self, entity) -> Dict[str, Any]:
        """Extract basic information from an entity"""
        info = {
            "global_id": getattr(entity, 'GlobalId', ''),
            "name": getattr(entity, 'Name', ''),
            "type": entity.is_a() if hasattr(entity, 'is_a') else 'Unknown'
        }
        
        # Add coordinates if available
        coords = self._get_entity_coordinates(entity)
        if coords:
            info["coordinates"] = coords
            center = self._get_entity_center(entity)
            if center:
                info["center"] = center
        
        return info

    def _find_adjacent_entities(self, model, entity) -> List:
        """Find entities adjacent to the given entity (simplified)"""
        # This is a placeholder - real implementation would use
        # proper geometric analysis to find truly adjacent entities
        adjacent = []
        
        try:
            # Simple approach: find entities of the same type in the same building storey
            if hasattr(entity, 'ContainedInStructure'):
                for container in entity.ContainedInStructure:
                    if container.is_a('IfcBuildingStorey'):
                        # Find other entities in the same storey
                        for other_entity in model.by_type(entity.is_a()):
                            if (other_entity != entity and 
                                hasattr(other_entity, 'ContainedInStructure')):
                                for other_container in other_entity.ContainedInStructure:
                                    if other_container == container:
                                        adjacent.append(other_entity)
                                        break
        except Exception as e:
            logger.warning(f"Adjacent entity search failed: {e}")
        
        return adjacent

    def _distance_3d(self, point1: List[float], point2: List[float]) -> float:
        """Calculate 3D distance between two points"""
        return math.sqrt(
            (point1[0] - point2[0])**2 +
            (point1[1] - point2[1])**2 +
            (point1[2] - point2[2])**2
        )

    def _calculate_bounding_box(self, coords: List[List[float]]) -> Dict[str, List[float]]:
        """Calculate bounding box from coordinates"""
        if not coords:
            return {"min": [0, 0, 0], "max": [0, 0, 0]}
        
        min_coords = [float('inf'), float('inf'), float('inf')]
        max_coords = [float('-inf'), float('-inf'), float('-inf')]
        
        for coord in coords:
            for i in range(3):
                min_coords[i] = min(min_coords[i], coord[i])
                max_coords[i] = max(max_coords[i], coord[i])
        
        return {"min": min_coords, "max": max_coords}

    def _calculate_spatial_coverage(self, bounding_box: Dict[str, List[float]]) -> Dict[str, float]:
        """Calculate spatial coverage metrics"""
        min_coords = bounding_box["min"]
        max_coords = bounding_box["max"]
        
        width = max_coords[0] - min_coords[0]
        height = max_coords[1] - min_coords[1]
        depth = max_coords[2] - min_coords[2]
        
        return {
            "width": width,
            "height": height,
            "depth": depth,
            "area": width * height,
            "volume": width * height * depth
        }


# Global spatial query instance
spatial_query = SpatialQuery()
