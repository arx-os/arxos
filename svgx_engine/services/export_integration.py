"""
SVGX Engine - Export Integration Service

This service handles SVGX export with proper scale preservation, metadata embedding,
and compatibility validation across different zoom levels and export formats.

Features:
- Scale-aware SVGX export with SVGX namespace support
- Metadata embedding in SVGX and sidecar files
- Export consistency validation across zoom levels
- Compatibility testing with BIM/CAD tools
- Multi-format export support with SVGX optimizations
- SVGX-specific scale preservation and coordinate handling
"""

import json
import time
import hashlib
import uuid
import threading
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path
import sqlite3
from contextlib import contextmanager
import math
import re
import xml.etree.ElementTree as ET

from structlog import get_logger

try:
    from svgx_engine.utils.errors import ExportError, ValidationError, PersistenceError
except ImportError:
    # Fallback for direct execution
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from svgx_engine.utils.errors import ExportError, ValidationError, PersistenceError

from svgx_engine.models.svgx import SVGXDocument, SVGXElement
from svgx_engine.models.bim import BIMElement, BIMSystem, BIMSpace

logger = get_logger()


@dataclass
class ScaleMetadata:
    """Metadata for scale information in exported files."""
    original_scale: float
    current_scale: float
    zoom_level: float
    units: str
    scale_factor: float
    viewport_width: float
    viewport_height: float
    created_at: str
    coordinate_system: str
    svgx_namespace: str = "http://svgx.engine/scale"


@dataclass
class ExportMetadata:
    """Complete metadata for exported files."""
    title: str
    description: str
    building_id: str
    floor_label: str
    version: str
    created_at: str
    created_by: str
    scale_metadata: ScaleMetadata
    symbol_count: int
    element_count: int
    export_format: str
    export_version: str
    svgx_version: str = "1.0"


@dataclass
class ExportOptions:
    """Options for export operations."""
    include_metadata: bool = True
    include_scale_info: bool = True
    include_symbol_data: bool = True
    optimize_svg: bool = True
    compress_output: bool = False
    embed_symbols: bool = True
    preserve_coordinates: bool = True
    export_format: str = "svgx"  # Default to SVGX format
    scale_factor: float = 1.0
    units: str = "mm"
    svgx_optimization: bool = True
    include_svgx_namespace: bool = True


class SVGXExportIntegrationService:
    """
    SVGX Engine Export Integration Service.
    
    Handles export integration with scale preservation and metadata embedding
    specifically optimized for SVGX Engine operations.
    
    Features:
    - Scale-aware SVGX export with SVGX namespace support
    - Metadata embedding in SVGX and sidecar files
    - Export consistency validation across zoom levels
    - Compatibility testing with BIM/CAD tools
    - Multi-format export support with SVGX optimizations
    - SVGX-specific scale preservation and coordinate handling
    """
    
    def __init__(self, symbol_library_path: str = "svgx-symbol-library"):
        self.symbol_library_path = Path(symbol_library_path)
        self.export_formats = ["svgx", "svg", "json", "xml", "pdf"]
        self.metadata_namespace = "http://svgx.engine/metadata"
        self.scale_namespace = "http://svgx.engine/scale"
        self.svgx_namespace = "http://svgx.engine/svgx"
        
        # Export settings
        self.default_units = "mm"
        self.default_scale_factor = 1.0
        self.metadata_embedding = True
        self.sidecar_metadata = True
        self.svgx_optimization = True
        
        # Initialize persistence service
        try:
            from svgx_engine.services.persistence import SVGXPersistenceService
            self.persistence = SVGXPersistenceService()
        except ImportError:
            # Fallback if persistence service not available
            self.persistence = None
        
        logger.info("SVGX Export Integration Service initialized")
    
    def save_svgx_document(self, svgx_document: SVGXDocument, file_path: str, 
                           format: str = "svgx") -> None:
        """
        Save SVGX document to file in specified format.
        
        Args:
            svgx_document: SVGX document to save
            file_path: Output file path
            format: Output format (svgx, json, xml)
        """
        try:
            if format.lower() == "svgx":
                self._save_svgx_format(svgx_document, file_path)
            elif format.lower() == "json":
                self._save_json_format(svgx_document, file_path)
            elif format.lower() == "xml":
                self._save_xml_format(svgx_document, file_path)
            else:
                raise ExportError(f"Unsupported format: {format}")
            logger.info(f"SVGX document saved to {format}: {file_path}")
        except Exception as e:
            logger.error(f"Failed to save SVGX document: {e}")
            raise ExportError(f"Failed to save SVGX document: {e}") from e
    
    def load_svgx_document(self, file_path: str, format: str = "svgx") -> SVGXDocument:
        """
        Load SVGX document from file.
        
        Args:
            file_path: Input file path
            format: Input format (svgx, json, xml)
            
        Returns:
            SVGX document
        """
        try:
            if format.lower() == "svgx":
                return self._load_svgx_format(file_path)
            elif format.lower() == "json":
                return self._load_json_format(file_path)
            elif format.lower() == "xml":
                return self._load_xml_format(file_path)
            else:
                raise ValidationError(f"Unsupported format: {format}")
        except Exception as e:
            logger.error(f"Failed to load SVGX document: {e}")
            raise ValidationError(f"Failed to load SVGX document: {e}") from e
    
    def save_svgx_with_metadata(self, svgx_content: str, file_path: str, 
                                metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Save SVGX with embedded metadata.
        
        Args:
            svgx_content: SVGX content to save
            file_path: Output file path
            metadata: Optional metadata to embed
        """
        try:
            if metadata:
                # Embed metadata in SVGX
                root = ET.fromstring(svgx_content.encode('utf-8'))
                self._embed_export_metadata(root, metadata)
                svgx_content = ET.tostring(root, encoding='unicode', method='xml')
            
            if self.persistence:
                self.persistence.save_svgx(svgx_content, file_path)
            else:
                # Fallback direct file writing
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(svgx_content)
            
            logger.info(f"SVGX with metadata saved: {file_path}")
        except Exception as e:
            logger.error(f"Failed to save SVGX with metadata: {e}")
            raise ExportError(f"Failed to save SVGX with metadata: {e}") from e
    
    def load_svgx_with_metadata(self, file_path: str) -> Tuple[str, Optional[Dict[str, Any]]]:
        """
        Load SVGX and extract embedded metadata.
        
        Args:
            file_path: Input file path
            
        Returns:
            Tuple of (svgx_content, metadata)
        """
        try:
            if self.persistence:
                svgx_content = self.persistence.load_svgx(file_path)
            else:
                # Fallback direct file reading
                with open(file_path, 'r', encoding='utf-8') as f:
                    svgx_content = f.read()
            
            # Extract metadata if present
            metadata = None
            try:
                root = ET.fromstring(svgx_content.encode('utf-8'))
                metadata = self._extract_metadata(root)
            except Exception as e:
                logger.warning(f"Failed to extract metadata from SVGX: {e}")
            
            return svgx_content, metadata
        except Exception as e:
            logger.error(f"Failed to load SVGX with metadata: {e}")
            raise ValidationError(f"Failed to load SVGX with metadata: {e}") from e
    
    def _extract_metadata(self, root: ET.Element) -> Optional[Dict[str, Any]]:
        """Extract metadata from SVGX element."""
        try:
            metadata_elem = root.find('.//{http://www.w3.org/2000/svg}metadata')
            if metadata_elem is not None:
                # Convert metadata element to dict
                metadata = {}
                for child in metadata_elem:
                    metadata[child.tag] = child.attrib
                return metadata
            return None
        except Exception as e:
            logger.warning(f"Failed to extract metadata: {e}")
            return None

    def export_svgx_with_scale(self, svgx_content: str, scale_metadata: ScaleMetadata,
                               options: ExportOptions) -> str:
        """
        Export SVGX with proper scale preservation and metadata.
        
        Args:
            svgx_content: Original SVGX content
            scale_metadata: Scale metadata to embed
            options: Export options
            
        Returns:
            Modified SVGX with embedded scale information
        """
        try:
            # Parse SVGX
            root = ET.fromstring(svgx_content.encode('utf-8'))
            
            # Add SVGX namespace if requested
            if options.include_svgx_namespace:
                self._add_svgx_namespace(root)
            
            # Add scale metadata
            if options.include_scale_info:
                self._embed_scale_metadata(root, scale_metadata)
            
            # Add general metadata
            if options.include_metadata:
                self._embed_export_metadata(root, scale_metadata, options)
            
            # Apply scale transformations
            if scale_metadata.scale_factor != 1.0:
                self._apply_scale_transformations(root, scale_metadata)
            
            # Optimize SVGX if requested
            if options.optimize_svg and options.svgx_optimization:
                self._optimize_svgx(root)
            
            # Convert back to string
            result = ET.tostring(root, encoding='unicode', method='xml')
            
            logger.info(f"Exported SVGX with scale factor: {scale_metadata.scale_factor}")
            return result
            
        except Exception as e:
            logger.error(f"Error exporting SVGX with scale: {e}")
            raise ExportError(f"Error exporting SVGX with scale: {e}") from e
    
    def _add_svgx_namespace(self, root: ET.Element):
        """Add SVGX namespace to the root element."""
        root.set('xmlns:svgx', self.svgx_namespace)
    
    def _embed_scale_metadata(self, root: ET.Element, scale_metadata: ScaleMetadata):
        """Embed scale metadata in SVGX."""
        # Create metadata element if it doesn't exist
        metadata_elem = root.find('.//{http://www.w3.org/2000/svg}metadata')
        if metadata_elem is None:
            metadata_elem = ET.SubElement(root, '{http://www.w3.org/2000/svg}metadata')
        
        # Add scale information
        scale_elem = ET.SubElement(metadata_elem, f'{{{self.scale_namespace}}}scale')
        
        # Add scale attributes
        scale_elem.set('original_scale', str(scale_metadata.original_scale))
        scale_elem.set('current_scale', str(scale_metadata.current_scale))
        scale_elem.set('zoom_level', str(scale_metadata.zoom_level))
        scale_elem.set('units', scale_metadata.units)
        scale_elem.set('scale_factor', str(scale_metadata.scale_factor))
        scale_elem.set('viewport_width', str(scale_metadata.viewport_width))
        scale_elem.set('viewport_height', str(scale_metadata.viewport_height))
        scale_elem.set('coordinate_system', scale_metadata.coordinate_system)
        scale_elem.set('created_at', scale_metadata.created_at)
        scale_elem.set('svgx_namespace', scale_metadata.svgx_namespace)
    
    def _embed_export_metadata(self, root: ET.Element, scale_metadata: ScaleMetadata,
                              options: ExportOptions):
        """Embed general export metadata in SVGX."""
        metadata_elem = root.find('.//{http://www.w3.org/2000/svg}metadata')
        if metadata_elem is None:
            metadata_elem = ET.SubElement(root, '{http://www.w3.org/2000/svg}metadata')
        
        # Add export information
        export_elem = ET.SubElement(metadata_elem, f'{{{self.metadata_namespace}}}export')
        export_elem.set('format', options.export_format)
        export_elem.set('version', '1.0')
        export_elem.set('created_at', datetime.now().isoformat())
        export_elem.set('units', options.units)
        export_elem.set('scale_factor', str(options.scale_factor))
        export_elem.set('svgx_optimization', str(options.svgx_optimization))
    
    def _apply_scale_transformations(self, root: ET.Element, scale_metadata: ScaleMetadata):
        """Apply scale transformations to SVGX elements."""
        # Update viewBox if present
        viewbox = root.get('viewBox')
        if viewbox:
            try:
                x, y, width, height = map(float, viewbox.split())
                new_viewbox = f"{x} {y} {width * scale_metadata.scale_factor} {height * scale_metadata.scale_factor}"
                root.set('viewBox', new_viewbox)
            except ValueError:
                logger.warning("Invalid viewBox format, skipping transformation")
        
        # Update width and height attributes
        width = root.get('width')
        height = root.get('height')
        if width and height:
            try:
                new_width = float(width) * scale_metadata.scale_factor
                new_height = float(height) * scale_metadata.scale_factor
                root.set('width', str(new_width))
                root.set('height', str(new_height))
            except ValueError:
                logger.warning("Invalid width/height format, skipping transformation")
    
    def _optimize_svgx(self, root: ET.Element):
        """Optimize SVGX for export."""
        # Remove unnecessary whitespace
        for elem in root.iter():
            if elem.text and elem.text.strip() == '':
                elem.text = None
            if elem.tail and elem.tail.strip() == '':
                elem.tail = None
        
        # Remove empty groups
        for group in root.findall('.//{http://www.w3.org/2000/svg}g'):
            if len(group) == 0:
                parent = group.getparent()
                if parent is not None:
                    parent.remove(group)
    
    def create_scale_metadata(self, original_scale: float, current_scale: float,
                            zoom_level: float, viewport_size: Tuple[float, float],
                            units: str = "mm") -> ScaleMetadata:
        """Create scale metadata object."""
        return ScaleMetadata(
            original_scale=original_scale,
            current_scale=current_scale,
            zoom_level=zoom_level,
            units=units,
            scale_factor=current_scale / original_scale if original_scale > 0 else 1.0,
            viewport_width=viewport_size[0],
            viewport_height=viewport_size[1],
            created_at=datetime.now().isoformat(),
            coordinate_system="cartesian",
            svgx_namespace=self.svgx_namespace
        )
    
    def export_with_metadata_sidecar(self, svgx_content: str, export_metadata: ExportMetadata,
                                   options: ExportOptions) -> Dict[str, str]:
        """
        Export SVGX with metadata sidecar file.
        
        Args:
            svgx_content: SVGX content
            export_metadata: Complete export metadata
            options: Export options
            
        Returns:
            Dictionary with SVGX content and metadata sidecar
        """
        try:
            # Export SVGX with embedded metadata
            exported_svgx = self.export_svgx_with_scale(
                svgx_content, 
                export_metadata.scale_metadata, 
                options
            )
            
            # Create metadata sidecar
            metadata_sidecar = self._create_metadata_sidecar(export_metadata)
            
            return {
                'svgx': exported_svgx,
                'metadata': metadata_sidecar,
                'format': 'svgx_with_sidecar'
            }
            
        except Exception as e:
            logger.error(f"Error creating export with sidecar: {e}")
            raise
    
    def _create_metadata_sidecar(self, export_metadata: ExportMetadata) -> str:
        """Create metadata sidecar file content."""
        metadata_dict = asdict(export_metadata)
        
        # Convert to JSON with proper formatting
        return json.dumps(metadata_dict, indent=2, default=str)
    
    def _save_svgx_format(self, svgx_document: SVGXDocument, file_path: str):
        """Save SVGX document in SVGX format."""
        # Convert SVGX document to SVGX format
        svgx_content = self._convert_svgx_document_to_svgx(svgx_document)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(svgx_content)
    
    def _save_json_format(self, svgx_document: SVGXDocument, file_path: str):
        """Save SVGX document in JSON format."""
        # Convert SVGX document to JSON
        json_data = self._convert_svgx_document_to_json(svgx_document)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, indent=2, default=str)
    
    def _save_xml_format(self, svgx_document: SVGXDocument, file_path: str):
        """Save SVGX document in XML format."""
        # Convert SVGX document to XML
        xml_content = self._convert_svgx_document_to_xml(svgx_document)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(xml_content)
    
    def _load_svgx_format(self, file_path: str) -> SVGXDocument:
        """Load SVGX document from SVGX format."""
        with open(file_path, 'r', encoding='utf-8') as f:
            svgx_content = f.read()
        return self._convert_svgx_to_document(svgx_content)
    
    def _load_json_format(self, file_path: str) -> SVGXDocument:
        """Load SVGX document from JSON format."""
        with open(file_path, 'r', encoding='utf-8') as f:
            json_data = json.load(f)
        return self._convert_json_to_document(json_data)
    
    def _load_xml_format(self, file_path: str) -> SVGXDocument:
        """Load SVGX document from XML format."""
        with open(file_path, 'r', encoding='utf-8') as f:
            xml_content = f.read()
        return self._convert_xml_to_document(xml_content)
    
    def _convert_svgx_document_to_svgx(self, svgx_document: SVGXDocument) -> str:
        """Convert SVGX document to SVGX format string."""
        # Implementation would convert SVGX document to SVGX format
        # This is a placeholder implementation
        return f"<svgx xmlns:svgx='{self.svgx_namespace}'>{svgx_document.id}</svgx>"
    
    def _convert_svgx_document_to_json(self, svgx_document: SVGXDocument) -> Dict[str, Any]:
        """Convert SVGX document to JSON format."""
        # Implementation would convert SVGX document to JSON
        # This is a placeholder implementation
        return {
            "id": svgx_document.id,
            "type": "svgx_document",
            "elements": []
        }
    
    def _convert_svgx_document_to_xml(self, svgx_document: SVGXDocument) -> str:
        """Convert SVGX document to XML format."""
        # Implementation would convert SVGX document to XML
        # This is a placeholder implementation
        return f"<svgx_document id='{svgx_document.id}'></svgx_document>"
    
    def _convert_svgx_to_document(self, svgx_content: str) -> SVGXDocument:
        """Convert SVGX format string to SVGX document."""
        # Implementation would parse SVGX content and create SVGX document
        # This is a placeholder implementation
        return SVGXDocument(id="converted_document")
    
    def _convert_json_to_document(self, json_data: Dict[str, Any]) -> SVGXDocument:
        """Convert JSON data to SVGX document."""
        # Implementation would convert JSON data to SVGX document
        # This is a placeholder implementation
        return SVGXDocument(id=json_data.get("id", "json_document"))
    
    def _convert_xml_to_document(self, xml_content: str) -> SVGXDocument:
        """Convert XML content to SVGX document."""
        # Implementation would parse XML content and create SVGX document
        # This is a placeholder implementation
        return SVGXDocument(id="xml_document") 