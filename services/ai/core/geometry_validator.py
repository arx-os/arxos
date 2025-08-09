"""
Geometry Validator

AI-powered geometry validation and analysis for CAD/BIM data.
"""

import asyncio
from typing import Dict, Any, List, Optional
import numpy as np
from shapely.geometry import Point, LineString, Polygon
from shapely.validation import make_valid
import structlog

logger = structlog.get_logger()


class GeometryValidator:
    """AI-powered geometry validation and analysis"""

    def __init__(self, config: Dict[str, Any]):
        """Initialize the geometry validator"""
        self.config = config
        self.logger = structlog.get_logger(__name__)

        # Validation rules
        self.validation_rules = {
            "comprehensive": self._comprehensive_validation,
            "basic": self._basic_validation,
            "topology": self._topology_validation,
            "precision": self._precision_validation
        }

        self.logger.info("Geometry Validator initialized")

    async def validate(
        self,
        geometry_data: Dict[str, Any],
        validation_type: str = "comprehensive"
    ) -> Dict[str, Any]:
        """Validate geometry using AI-powered analysis"""
        try:
            self.logger.info(f"Validating geometry with type: {validation_type}")

            # Parse geometry data
            geometries = self._parse_geometry_data(geometry_data)

            # Run validation based on type
            if validation_type in self.validation_rules:
                validation_result = await self.validation_rules[validation_type](geometries)
            else:
                validation_result = await self._comprehensive_validation(geometries)

            # Add metadata
            validation_result.update({
                "validation_type": validation_type,
                "geometry_count": len(geometries),
                "timestamp": asyncio.get_event_loop().time()
            })

            return validation_result

        except Exception as e:
            self.logger.error(f"Error validating geometry: {e}")
            return {
                "valid": False,
                "errors": [str(e)],
                "validation_type": validation_type
            }

    def _parse_geometry_data(self, geometry_data: Dict[str, Any]) -> List[Any]:
        """Parse geometry data into Shapely objects"""
        geometries = []

        try:
            if "geometries" in geometry_data:
                for geom_data in geometry_data["geometries"]:
                    geom = self._create_shapely_geometry(geom_data)
                    if geom:
                        geometries.append(geom)
            elif "geometry" in geometry_data:
                geom = self._create_shapely_geometry(geometry_data["geometry"])
                if geom:
                    geometries.append(geom)
            else:
                # Assume the data itself is geometry
                geom = self._create_shapely_geometry(geometry_data)
                if geom:
                    geometries.append(geom)

        except Exception as e:
            self.logger.error(f"Error parsing geometry data: {e}")

        return geometries

    def _create_shapely_geometry(self, geom_data: Dict[str, Any]) -> Optional[Any]:
        """Create Shapely geometry from data"""
        try:
            geom_type = geom_data.get("type", "").lower()
            coordinates = geom_data.get("coordinates", [])

            if geom_type == "point":
                return Point(coordinates)
            elif geom_type == "linestring":
                return LineString(coordinates)
            elif geom_type == "polygon":
                return Polygon(coordinates[0], coordinates[1:] if len(coordinates) > 1 else [])
            else:
                self.logger.warning(f"Unsupported geometry type: {geom_type}")
                return None

        except Exception as e:
            self.logger.error(f"Error creating geometry: {e}")
            return None

    async def _comprehensive_validation(self, geometries: List[Any]) -> Dict[str, Any]:
        """Comprehensive geometry validation"""
        results = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "statistics": {}
        }

        for i, geom in enumerate(geometries):
            # Basic validity check
            if not geom.is_valid:
                results["valid"] = False
                results["errors"].append(f"Geometry {i}: Invalid geometry")

                # Try to fix
                try:
                    fixed_geom = make_valid(geom)
                    if fixed_geom.is_valid:
                        results["warnings"].append(f"Geometry {i}: Fixed invalid geometry")
                except Exception as e:
                    results["errors"].append(f"Geometry {i}: Could not fix invalid geometry: {e}")

            # Area/volume checks
            if hasattr(geom, 'area'):
                area = geom.area
                if area < 1e-10:
                    results["warnings"].append(f"Geometry {i}: Very small area ({area})")
                elif area > 1e10:
                    results["warnings"].append(f"Geometry {i}: Very large area ({area})")

            # Coordinate checks
            coords = list(geom.coords)
            for j, coord in enumerate(coords):
                if any(abs(c) > 1e6 for c in coord):
                    results["warnings"].append(f"Geometry {i}: Large coordinate values at position {j}")

        # Calculate statistics
        if geometries:
            areas = [g.area for g in geometries if hasattr(g, 'area')]
            results["statistics"] = {
                "total_geometries": len(geometries),
                "valid_geometries": sum(1 for g in geometries if g.is_valid),
                "total_area": sum(areas) if areas else 0,
                "average_area": np.mean(areas) if areas else 0
            }

        return results

    async def _basic_validation(self, geometries: List[Any]) -> Dict[str, Any]:
        """Basic geometry validation"""
        results = {
            "valid": True,
            "errors": [],
            "statistics": {}
        }

        for i, geom in enumerate(geometries):
            if not geom.is_valid:
                results["valid"] = False
                results["errors"].append(f"Geometry {i}: Invalid geometry")

        results["statistics"] = {
            "total_geometries": len(geometries),
            "valid_geometries": sum(1 for g in geometries if g.is_valid)
        }

        return results

    async def _topology_validation(self, geometries: List[Any]) -> Dict[str, Any]:
        """Topology-focused validation"""
        results = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "topology_issues": []
        }

        for i, geom in enumerate(geometries):
            # Check for self-intersections
            if hasattr(geom, 'intersects') and geom.intersects(geom):
                results["topology_issues"].append(f"Geometry {i}: Self-intersection detected")

            # Check for degenerate geometries
            if hasattr(geom, 'length') and geom.length < 1e-10:
                results["warnings"].append(f"Geometry {i}: Degenerate line (very short)")

            if hasattr(geom, 'area') and geom.area < 1e-10:
                results["warnings"].append(f"Geometry {i}: Degenerate polygon (very small area)")

        return results

    async def _precision_validation(self, geometries: List[Any]) -> Dict[str, Any]:
        """Precision-focused validation"""
        results = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "precision_issues": []
        }

        for i, geom in enumerate(geometries):
            coords = list(geom.coords)

            # Check coordinate precision
            for j, coord in enumerate(coords):
                # Check for very small coordinates (potential precision issues)
                if any(0 < abs(c) < 1e-10 for c in coord):
                    results["precision_issues"].append(
                        f"Geometry {i}: Very small coordinate values at position {j}"
                    )

                # Check for very large coordinates
                if any(abs(c) > 1e6 for c in coord):
                    results["warnings"].append(
                        f"Geometry {i}: Very large coordinate values at position {j}"
                    )

        return results

    async def execute_task(self, task: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute geometry-related tasks"""
        try:
            if task == "validate":
                return await self.validate(
                    parameters.get("geometry_data", {}),
                    parameters.get("validation_type", "comprehensive")
                )
            elif task == "fix":
                return await self._fix_geometry(parameters.get("geometry_data", {}))
            elif task == "analyze":
                return await self._analyze_geometry(parameters.get("geometry_data", {}))
            else:
                return {
                    "error": f"Unknown geometry task: {task}",
                    "available_tasks": ["validate", "fix", "analyze"]
                }

        except Exception as e:
            self.logger.error(f"Error executing geometry task: {e}")
            return {"error": str(e)}

    async def _fix_geometry(self, geometry_data: Dict[str, Any]) -> Dict[str, Any]:
        """Fix geometry issues"""
        geometries = self._parse_geometry_data(geometry_data)
        fixed_geometries = []

        for i, geom in enumerate(geometries):
            if not geom.is_valid:
                try:
                    fixed_geom = make_valid(geom)
                    fixed_geometries.append(fixed_geom)
                except Exception as e:
                    self.logger.error(f"Could not fix geometry {i}: {e}")
                    fixed_geometries.append(geom)
            else:
                fixed_geometries.append(geom)

        return {
            "fixed_geometries": len([g for g in fixed_geometries if g.is_valid]),
            "total_geometries": len(fixed_geometries),
            "success": True
        }

    async def _analyze_geometry(self, geometry_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze geometry characteristics"""
        geometries = self._parse_geometry_data(geometry_data)

        analysis = {
            "total_geometries": len(geometries),
            "geometry_types": {},
            "area_statistics": {},
            "coordinate_statistics": {}
        }

        for geom in geometries:
            geom_type = geom.geom_type
            analysis["geometry_types"][geom_type] = analysis["geometry_types"].get(geom_type, 0) + 1

            if hasattr(geom, 'area'):
                if "areas" not in analysis["area_statistics"]:
                    analysis["area_statistics"]["areas"] = []
                analysis["area_statistics"]["areas"].append(geom.area)

        # Calculate statistics
        if analysis["area_statistics"].get("areas"):
            areas = analysis["area_statistics"]["areas"]
            analysis["area_statistics"].update({
                "total_area": sum(areas),
                "average_area": np.mean(areas),
                "min_area": min(areas),
                "max_area": max(areas)
            })

        return analysis
