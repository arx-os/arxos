"""
Advanced Export Interoperability Service

This service provides comprehensive export capabilities for multiple CAD and BIM formats,
including IFC, GLTF, DXF, and other industry-standard formats.

Author: Arxos Engineering Team
Date: 2024-12-19
Version: 1.0.0
"""

import json
import logging
import math
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import pandas as pd

logger = logging.getLogger(__name__)


class ExportFormat:
    IFC_LITE = "ifc-lite"
    GLTF = "gltf"
    ASCII_BIM = "ascii-bim"
    EXCEL = "excel"
    PARQUET = "parquet"
    GEOJSON = "geojson"


class IFCEntityType:
    """IFC entity types for BIM export."""
    WALL = "IfcWall"
    DOOR = "IfcDoor"
    WINDOW = "IfcWindow"
    BEAM = "IfcBeam"
    COLUMN = "IfcColumn"
    SLAB = "IfcSlab"
    SPACE = "IfcSpace"
    BUILDING = "IfcBuilding"
    SITE = "IfcSite"
    FLOOR = "IfcBuildingStorey"


class AdvancedExportInteroperabilityService:
    """
    Core export service for BIM data supporting multiple formats.
    """
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.export_statistics = {
            "total_exports": 0,
            "successful_exports": 0,
            "failed_exports": 0,
            "export_times": []
        }

    def export(self, data: Dict[str, Any], format: str, output_path: Union[str, Path], options: Optional[Dict[str, Any]] = None) -> Path:
        """
        Export BIM data to the specified format.
        Args:
            data: BIM data as a dictionary (internal model)
            format: Export format (see ExportFormat)
            output_path: Output file path
            options: Optional export options
        Returns:
            Path to the exported file
        """
        start_time = datetime.now()
        self.export_statistics["total_exports"] += 1
        
        try:
            if format == ExportFormat.IFC_LITE:
                result_path = self.export_ifc_lite(data, output_path, options)
            elif format == ExportFormat.GLTF:
                result_path = self.export_gltf(data, output_path, options)
            elif format == ExportFormat.ASCII_BIM:
                result_path = self.export_ascii_bim(data, output_path, options)
            elif format == ExportFormat.EXCEL:
                result_path = self.export_excel(data, output_path, options)
            elif format == ExportFormat.PARQUET:
                result_path = self.export_parquet(data, output_path, options)
            elif format == ExportFormat.GEOJSON:
                result_path = self.export_geojson(data, output_path, options)
            else:
                raise ValueError(f"Unsupported export format: {format}")
            
            self.export_statistics["successful_exports"] += 1
            export_time = (datetime.now() - start_time).total_seconds()
            self.export_statistics["export_times"].append(export_time)
            
            self.logger.info(f"Export completed successfully: {format} -> {result_path}")
            return result_path
            
        except Exception as e:
            self.export_statistics["failed_exports"] += 1
            self.logger.error(f"Export failed: {format} -> {e}")
            raise

    def export_ifc_lite(self, data: Dict[str, Any], output_path: Union[str, Path], options: Optional[Dict[str, Any]] = None) -> Path:
        """Export BIM data to IFC-lite format with comprehensive entity mapping."""
        try:
            # Create IFC-lite structure
            ifc_lite_data = {
                "metadata": {
                    "format": "IFC-Lite",
                    "version": "1.0",
                    "exported_at": datetime.now().isoformat(),
                    "source": "Arxos BIM Export",
                    "options": options or {}
                },
                "project": {
                    "name": data.get("project_name", "Arxos Project"),
                    "description": data.get("project_description", ""),
                    "site": self._extract_site_info(data),
                    "buildings": self._extract_buildings(data),
                    "spaces": self._extract_spaces(data),
                    "elements": self._extract_elements(data),
                    "relationships": self._extract_relationships(data)
                }
            }
            
            # Write to file
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(ifc_lite_data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"IFC-lite export completed: {len(ifc_lite_data['project']['elements'])} elements")
            return Path(output_path)
            
        except Exception as e:
            self.logger.error(f"IFC-lite export failed: {e}")
            raise

    def _extract_site_info(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract site information from BIM data."""
        site_data = data.get("site", {})
        return {
            "id": site_data.get("id", "SITE_001"),
            "name": site_data.get("name", "Site"),
            "description": site_data.get("description", ""),
            "location": site_data.get("location", {"x": 0, "y": 0, "z": 0}),
            "properties": site_data.get("properties", {})
        }

    def _extract_buildings(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract building information from BIM data."""
        buildings = []
        for building in data.get("buildings", []):
            buildings.append({
                "id": building.get("id", f"BUILDING_{len(buildings)+1:03d}"),
                "name": building.get("name", f"Building {len(buildings)+1}"),
                "description": building.get("description", ""),
                "location": building.get("location", {"x": 0, "y": 0, "z": 0}),
                "dimensions": building.get("dimensions", {"width": 0, "length": 0, "height": 0}),
                "properties": building.get("properties", {}),
                "floors": self._extract_floors(building)
            })
        return buildings

    def _extract_floors(self, building: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract floor information from building data."""
        floors = []
        for floor in building.get("floors", []):
            floors.append({
                "id": floor.get("id", f"FLOOR_{len(floors)+1:03d}"),
                "name": floor.get("name", f"Floor {len(floors)+1}"),
                "level": floor.get("level", len(floors)),
                "height": floor.get("height", 0),
                "properties": floor.get("properties", {})
            })
        return floors

    def _extract_spaces(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract space information from BIM data."""
        spaces = []
        for space in data.get("spaces", []):
            spaces.append({
                "id": space.get("id", f"SPACE_{len(spaces)+1:03d}"),
                "name": space.get("name", f"Space {len(spaces)+1}"),
                "type": space.get("type", "Room"),
                "location": space.get("location", {"x": 0, "y": 0, "z": 0}),
                "dimensions": space.get("dimensions", {"width": 0, "length": 0, "height": 0}),
                "properties": space.get("properties", {}),
                "building_id": space.get("building_id"),
                "floor_id": space.get("floor_id")
            })
        return spaces

    def _extract_elements(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract BIM elements with IFC entity mapping."""
        elements = []
        for element in data.get("elements", []):
            ifc_entity = self._map_to_ifc_entity(element)
            if ifc_entity:
                elements.append(ifc_entity)
        return elements

    def _map_to_ifc_entity(self, element: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Map BIM element to IFC entity."""
        element_type = element.get("type", "").lower()
        
        # Map element types to IFC entities
        ifc_mapping = {
            "wall": IFCEntityType.WALL,
            "door": IFCEntityType.DOOR,
            "window": IFCEntityType.WINDOW,
            "beam": IFCEntityType.BEAM,
            "column": IFCEntityType.COLUMN,
            "slab": IFCEntityType.SLAB,
            "space": IFCEntityType.SPACE
        }
        
        ifc_type = ifc_mapping.get(element_type, "IfcElement")
        
        return {
            "id": element.get("id", f"ELEMENT_{len(element):03d}"),
            "name": element.get("name", f"Element {len(element)}"),
            "type": ifc_type,
            "location": element.get("location", {"x": 0, "y": 0, "z": 0}),
            "dimensions": element.get("dimensions", {"width": 0, "length": 0, "height": 0}),
            "properties": element.get("properties", {}),
            "geometry": element.get("geometry", {}),
            "relationships": element.get("relationships", []),
            "material": element.get("material", "Unknown"),
            "status": element.get("status", "Active")
        }

    def _extract_relationships(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract element relationships."""
        relationships = []
        for rel in data.get("relationships", []):
            relationships.append({
                "id": rel.get("id", f"REL_{len(relationships)+1:03d}"),
                "type": rel.get("type", "Contains"),
                "source_id": rel.get("source_id"),
                "target_id": rel.get("target_id"),
                "properties": rel.get("properties", {})
            })
        return relationships

    def export_gltf(self, data: Dict[str, Any], output_path: Union[str, Path], options: Optional[Dict[str, Any]] = None) -> Path:
        """Export BIM data to glTF format for 3D visualization."""
        try:
            # Create glTF structure
            gltf_data = {
                "asset": {
                    "version": "2.0",
                    "generator": "Arxos BIM Export",
                    "copyright": "Arxos Engineering"
                },
                "scene": 0,
                "scenes": [{
                    "name": "Arxos BIM Scene",
                    "nodes": []
                }],
                "nodes": self._create_gltf_nodes(data),
                "meshes": self._create_gltf_meshes(data),
                "materials": self._create_gltf_materials(data),
                "accessors": [],
                "bufferViews": [],
                "buffers": []
            }
            
            # Write to file
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(gltf_data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"glTF export completed: {len(gltf_data['nodes'])} nodes")
            return Path(output_path)
            
        except Exception as e:
            self.logger.error(f"glTF export failed: {e}")
            raise

    def _create_gltf_nodes(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create glTF nodes from BIM elements."""
        nodes = []
        for i, element in enumerate(data.get("elements", [])):
            nodes.append({
                "name": element.get("name", f"Element_{i}"),
                "mesh": i,
                "translation": element.get("location", [0, 0, 0]),
                "rotation": [0, 0, 0, 1],  # Identity quaternion
                "scale": [1, 1, 1]
            })
        return nodes

    def _create_gltf_meshes(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create glTF meshes from BIM elements."""
        meshes = []
        for i, element in enumerate(data.get("elements", [])):
            # Simplified mesh creation - in practice would use actual geometry
            meshes.append({
                "name": f"Mesh_{i}",
                "primitives": [{
                    "attributes": {
                        "POSITION": i * 2,  # Accessor index
                        "NORMAL": i * 2 + 1
                    },
                    "indices": i * 3,
                    "material": i
                }]
            })
        return meshes

    def _create_gltf_materials(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create glTF materials from BIM elements."""
        materials = []
        for element in data.get("elements", []):
            materials.append({
                "name": f"Material_{len(materials)}",
                "pbrMetallicRoughness": {
                    "baseColorFactor": [0.8, 0.8, 0.8, 1.0],
                    "metallicFactor": 0.0,
                    "roughnessFactor": 0.5
                }
            })
        return materials

    def export_ascii_bim(self, data: Dict[str, Any], output_path: Union[str, Path], options: Optional[Dict[str, Any]] = None) -> Path:
        """Export BIM data to ASCII-BIM format."""
        try:
            # Create ASCII-BIM structure
            ascii_bim_data = {
                "format": "ASCII-BIM",
                "version": "1.0",
                "exported_at": datetime.now().isoformat(),
                "project": {
                    "name": data.get("project_name", "Arxos Project"),
                    "elements": []
                }
            }
            
            # Convert elements to ASCII-BIM format
            for element in data.get("elements", []):
                ascii_element = {
                    "id": element.get("id"),
                    "type": element.get("type"),
                    "name": element.get("name"),
                    "x": element.get("location", {}).get("x", 0),
                    "y": element.get("location", {}).get("y", 0),
                    "z": element.get("location", {}).get("z", 0),
                    "width": element.get("dimensions", {}).get("width", 0),
                    "length": element.get("dimensions", {}).get("length", 0),
                    "height": element.get("dimensions", {}).get("height", 0),
                    "properties": element.get("properties", {})
                }
                ascii_bim_data["project"]["elements"].append(ascii_element)
            
            # Write to file
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(ascii_bim_data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"ASCII-BIM export completed: {len(ascii_bim_data['project']['elements'])} elements")
            return Path(output_path)
            
        except Exception as e:
            self.logger.error(f"ASCII-BIM export failed: {e}")
            raise

    def export_excel(self, data: Dict[str, Any], output_path: Union[str, Path], options: Optional[Dict[str, Any]] = None) -> Path:
        """Export BIM data to Excel format."""
        try:
            # Convert BIM data to DataFrame
            elements_data = []
            for element in data.get("elements", []):
                element_row = {
                    "ID": element.get("id"),
                    "Name": element.get("name"),
                    "Type": element.get("type"),
                    "X": element.get("location", {}).get("x", 0),
                    "Y": element.get("location", {}).get("y", 0),
                    "Z": element.get("location", {}).get("z", 0),
                    "Width": element.get("dimensions", {}).get("width", 0),
                    "Length": element.get("dimensions", {}).get("length", 0),
                    "Height": element.get("dimensions", {}).get("height", 0),
                    "Material": element.get("material", "Unknown"),
                    "Status": element.get("status", "Active")
                }
                # Add properties as additional columns
                for key, value in element.get("properties", {}).items():
                    element_row[f"Prop_{key}"] = value
                elements_data.append(element_row)
            
            df = pd.DataFrame(elements_data)
            df.to_excel(output_path, index=False, engine='openpyxl')
            
            self.logger.info(f"Excel export completed: {len(elements_data)} elements")
            return Path(output_path)
            
        except Exception as e:
            self.logger.error(f"Excel export failed: {e}")
            raise

    def export_parquet(self, data: Dict[str, Any], output_path: Union[str, Path], options: Optional[Dict[str, Any]] = None) -> Path:
        """Export BIM data to Parquet format."""
        try:
            # Convert BIM data to DataFrame
            elements_data = []
            for element in data.get("elements", []):
                element_row = {
                    "id": element.get("id"),
                    "name": element.get("name"),
                    "type": element.get("type"),
                    "x": element.get("location", {}).get("x", 0),
                    "y": element.get("location", {}).get("y", 0),
                    "z": element.get("location", {}).get("z", 0),
                    "width": element.get("dimensions", {}).get("width", 0),
                    "length": element.get("dimensions", {}).get("length", 0),
                    "height": element.get("dimensions", {}).get("height", 0),
                    "material": element.get("material", "Unknown"),
                    "status": element.get("status", "Active")
                }
                # Add properties as additional columns
                for key, value in element.get("properties", {}).items():
                    element_row[f"prop_{key}"] = value
                elements_data.append(element_row)
            
            df = pd.DataFrame(elements_data)
            df.to_parquet(output_path, index=False)
            
            self.logger.info(f"Parquet export completed: {len(elements_data)} elements")
            return Path(output_path)
            
        except Exception as e:
            self.logger.error(f"Parquet export failed: {e}")
            raise

    def export_geojson(self, data: Dict[str, Any], output_path: Union[str, Path], options: Optional[Dict[str, Any]] = None) -> Path:
        """Export BIM data to GeoJSON format."""
        try:
            geojson = {
                "type": "FeatureCollection",
                "features": []
            }
            
            for element in data.get("elements", []):
                # Create geometry based on element type
                geometry = self._create_geojson_geometry(element)
                
                feature = {
                    "type": "Feature",
                    "geometry": geometry,
                    "properties": {
                        "id": element.get("id"),
                        "name": element.get("name"),
                        "type": element.get("type"),
                        "material": element.get("material", "Unknown"),
                        "status": element.get("status", "Active"),
                        "height": element.get("dimensions", {}).get("height", 0),
                        **element.get("properties", {})
                    }
                }
                geojson["features"].append(feature)
            
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(geojson, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"GeoJSON export completed: {len(geojson['features'])} features")
            return Path(output_path)
            
        except Exception as e:
            self.logger.error(f"GeoJSON export failed: {e}")
            raise

    def _create_geojson_geometry(self, element: Dict[str, Any]) -> Dict[str, Any]:
        """Create GeoJSON geometry from BIM element."""
        element_type = element.get("type", "").lower()
        location = element.get("location", {"x": 0, "y": 0, "z": 0})
        dimensions = element.get("dimensions", {"width": 0, "length": 0, "height": 0})
        
        if element_type in ["wall", "beam", "column"]:
            # Line geometry for linear elements
            return {
                "type": "LineString",
                "coordinates": [
                    [location["x"], location["y"]],
                    [location["x"] + dimensions["length"], location["y"]]
                ]
            }
        else:
            # Polygon geometry for area elements
            x, y = location["x"], location["y"]
            width, length = dimensions["width"], dimensions["length"]
            
            return {
                "type": "Polygon",
                "coordinates": [[
                    [x, y],
                    [x + width, y],
                    [x + width, y + length],
                    [x, y + length],
                    [x, y]
                ]]
            }

    def get_export_statistics(self) -> Dict[str, Any]:
        """Get export statistics."""
        if self.export_statistics["export_times"]:
            avg_time = sum(self.export_statistics["export_times"]) / len(self.export_statistics["export_times"])
        else:
            avg_time = 0
        
        return {
            **self.export_statistics,
            "average_export_time": avg_time,
            "success_rate": self.export_statistics["successful_exports"] / max(self.export_statistics["total_exports"], 1)
        } 