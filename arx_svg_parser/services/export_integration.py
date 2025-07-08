"""
Export Integration Service

This service handles SVG export with proper scale preservation, metadata embedding,
and compatibility validation across different zoom levels and export formats.

Phase 7.3: Export Integration
- Update SVG export to maintain proper scale
- Add scale metadata to exported files
- Test export consistency across zoom levels
- Validate exported file compatibility
"""

import json
import logging
import math
import base64
from typing import Dict, List, Tuple, Optional, Any, Union
from dataclasses import dataclass, asdict
from pathlib import Path
from datetime import datetime
import xml.etree.ElementTree as ET
from lxml import etree
import yaml

from utils.errors import ExportError, ValidationError
from services.persistence import PersistenceService

logger = logging.getLogger(__name__)


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
    export_format: str = "svg"
    scale_factor: float = 1.0
    units: str = "mm"


class ExportIntegration:
    """
    Handles export integration with scale preservation and metadata embedding.
    
    Features:
    - Scale-aware SVG export
    - Metadata embedding in SVG and sidecar files
    - Export consistency validation across zoom levels
    - Compatibility testing with BIM/CAD tools
    - Multi-format export support
    """
    
    def __init__(self, symbol_library_path: str = "arx-symbol-library"):
        self.symbol_library_path = Path(symbol_library_path)
        self.export_formats = ["svg", "json", "xml", "pdf"]
        self.metadata_namespace = "http://arxos.io/metadata"
        self.scale_namespace = "http://arxos.io/scale"
        
        # Export settings
        self.default_units = "mm"
        self.default_scale_factor = 1.0
        self.metadata_embedding = True
        self.sidecar_metadata = True
        
        # Initialize persistence service
        self.persistence = PersistenceService()
        
        logger.info("ExportIntegration initialized")
    
    def save_bim_assembly(self, bim_data: Dict[str, Any], file_path: str, format: str = "json") -> None:
        """
        Save BIM assembly data to file in specified format.
        
        Args:
            bim_data: BIM assembly data to save
            file_path: Output file path
            format: Output format (json, xml)
        """
        try:
            if format.lower() == "json":
                self.persistence.save_bim_json(bim_data, file_path)
            elif format.lower() == "xml":
                self.persistence.save_bim_xml(bim_data, file_path)
            else:
                raise ExportError(f"Unsupported format: {format}")
            logger.info(f"BIM assembly saved to {format}: {file_path}")
        except Exception as e:
            logger.error(f"Failed to save BIM assembly: {e}")
            raise ExportError(f"Failed to save BIM assembly: {e}") from e
    
    def load_bim_assembly(self, file_path: str, format: str = "json") -> Dict[str, Any]:
        """
        Load BIM assembly data from file.
        
        Args:
            file_path: Input file path
            format: Input format (json, xml)
            
        Returns:
            BIM assembly data
        """
        try:
            if format.lower() == "json":
                return self.persistence.load_bim_json(file_path)
            elif format.lower() == "xml":
                return self.persistence.load_bim_xml(file_path)
            else:
                raise ValidationError(f"Unsupported format: {format}")
        except Exception as e:
            logger.error(f"Failed to load BIM assembly: {e}")
            raise ValidationError(f"Failed to load BIM assembly: {e}") from e
    
    def save_svg_with_metadata(self, svg_content: str, file_path: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Save SVG with embedded metadata.
        
        Args:
            svg_content: SVG content to save
            file_path: Output file path
            metadata: Optional metadata to embed
        """
        try:
            if metadata:
                # Embed metadata in SVG
                root = etree.fromstring(svg_content.encode('utf-8'))
                self._embed_export_metadata(root, metadata)
                svg_content = etree.tostring(root, encoding='unicode', pretty_print=True)
            
            self.persistence.save_svg(svg_content, file_path)
            logger.info(f"SVG with metadata saved: {file_path}")
        except Exception as e:
            logger.error(f"Failed to save SVG with metadata: {e}")
            raise ExportError(f"Failed to save SVG with metadata: {e}") from e
    
    def load_svg_with_metadata(self, file_path: str) -> Tuple[str, Optional[Dict[str, Any]]]:
        """
        Load SVG and extract embedded metadata.
        
        Args:
            file_path: Input file path
            
        Returns:
            Tuple of (svg_content, metadata)
        """
        try:
            svg_content = self.persistence.load_svg(file_path)
            
            # Extract metadata if present
            metadata = None
            try:
                root = etree.fromstring(svg_content.encode('utf-8'))
                metadata = self._extract_metadata(root)
            except Exception as e:
                logger.warning(f"Failed to extract metadata from SVG: {e}")
            
            return svg_content, metadata
        except Exception as e:
            logger.error(f"Failed to load SVG with metadata: {e}")
            raise ValidationError(f"Failed to load SVG with metadata: {e}") from e
    
    def _extract_metadata(self, root: etree.Element) -> Optional[Dict[str, Any]]:
        """Extract metadata from SVG element."""
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

    def export_svg_with_scale(self, svg_content: str, scale_metadata: ScaleMetadata,
                             options: ExportOptions) -> str:
        """
        Export SVG with proper scale preservation and metadata.
        
        Args:
            svg_content: Original SVG content
            scale_metadata: Scale metadata to embed
            options: Export options
            
        Returns:
            Modified SVG with embedded scale information
        """
        try:
            # Parse SVG
            root = etree.fromstring(svg_content.encode('utf-8'))
            
            # Add scale metadata
            if options.include_scale_info:
                self._embed_scale_metadata(root, scale_metadata)
            
            # Add general metadata
            if options.include_metadata:
                self._embed_export_metadata(root, scale_metadata, options)
            
            # Apply scale transformations
            if scale_metadata.scale_factor != 1.0:
                self._apply_scale_transformations(root, scale_metadata)
            
            # Optimize SVG if requested
            if options.optimize_svg:
                self._optimize_svg(root)
            
            # Convert back to string
            result = etree.tostring(root, encoding='unicode', pretty_print=True)
            
            logger.info(f"Exported SVG with scale factor: {scale_metadata.scale_factor}")
            return result
            
        except Exception as e:
            logger.error(f"Error exporting SVG with scale: {e}")
            raise ExportError(f"Error exporting SVG with scale: {e}") from e
    
    def _embed_scale_metadata(self, root: etree.Element, scale_metadata: ScaleMetadata):
        """Embed scale metadata in SVG."""
        # Create metadata element if it doesn't exist
        metadata_elem = root.find('.//{http://www.w3.org/2000/svg}metadata')
        if metadata_elem is None:
            metadata_elem = etree.SubElement(root, '{http://www.w3.org/2000/svg}metadata')
        
        # Add scale information
        scale_elem = etree.SubElement(metadata_elem, f'{{{self.scale_namespace}}}scale')
        
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
    
    def _embed_export_metadata(self, root: etree.Element, scale_metadata: ScaleMetadata,
                              options: ExportOptions):
        """Embed general export metadata in SVG."""
        metadata_elem = root.find('.//{http://www.w3.org/2000/svg}metadata')
        if metadata_elem is None:
            metadata_elem = etree.SubElement(root, '{http://www.w3.org/2000/svg}metadata')
        
        # Add export information
        export_elem = etree.SubElement(metadata_elem, f'{{{self.metadata_namespace}}}export')
        export_elem.set('format', options.export_format)
        export_elem.set('version', '1.0')
        export_elem.set('created_at', datetime.now().isoformat())
        export_elem.set('units', options.units)
        export_elem.set('scale_factor', str(options.scale_factor))
    
    def _apply_scale_transformations(self, root: etree.Element, scale_metadata: ScaleMetadata):
        """Apply scale transformations to SVG elements."""
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
    
    def _optimize_svg(self, root: etree.Element):
        """Optimize SVG for export."""
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
            coordinate_system="cartesian"
        )
    
    def export_with_metadata_sidecar(self, svg_content: str, export_metadata: ExportMetadata,
                                   options: ExportOptions) -> Dict[str, str]:
        """
        Export SVG with metadata sidecar file.
        
        Args:
            svg_content: SVG content
            export_metadata: Complete export metadata
            options: Export options
            
        Returns:
            Dictionary with SVG content and metadata sidecar
        """
        try:
            # Export SVG with embedded metadata
            exported_svg = self.export_svg_with_scale(
                svg_content, 
                export_metadata.scale_metadata, 
                options
            )
            
            # Create metadata sidecar
            metadata_sidecar = self._create_metadata_sidecar(export_metadata)
            
            return {
                'svg': exported_svg,
                'metadata': metadata_sidecar,
                'format': 'svg_with_sidecar'
            }
            
        except Exception as e:
            logger.error(f"Error creating export with sidecar: {e}")
            raise
    
    def _create_metadata_sidecar(self, export_metadata: ExportMetadata) -> str:
        """Create metadata sidecar file content."""
        metadata_dict = asdict(export_metadata)
        
        # Convert to JSON with proper formatting
        return json.dumps(metadata_dict, indent=2, default=str)
    
    def test_export_consistency(self, svg_content: str, zoom_levels: List[float],
                              options: ExportOptions) -> Dict[str, Any]:
        """
        Test export consistency across different zoom levels.
        
        Args:
            svg_content: Original SVG content
            zoom_levels: List of zoom levels to test
            options: Export options
            
        Returns:
            Consistency test results
        """
        results = {
            'tested_levels': [],
            'consistency_score': 0.0,
            'scale_variations': [],
            'issues': [],
            'recommendations': []
        }
        
        try:
            # Test each zoom level
            for zoom_level in zoom_levels:
                level_result = self._test_single_zoom_level(svg_content, zoom_level, options)
                results['tested_levels'].append(level_result)
            
            # Calculate consistency score
            results['consistency_score'] = self._calculate_consistency_score(results['tested_levels'])
            
            # Analyze scale variations
            results['scale_variations'] = self._analyze_scale_variations(results['tested_levels'])
            
            # Generate recommendations
            results['recommendations'] = self._generate_export_recommendations(results)
            
            logger.info(f"Export consistency test completed with score: {results['consistency_score']:.2f}")
            return results
            
        except Exception as e:
            logger.error(f"Error testing export consistency: {e}")
            results['issues'].append(f"Test failed: {str(e)}")
            return results
    
    def _test_single_zoom_level(self, svg_content: str, zoom_level: float,
                               options: ExportOptions) -> Dict[str, Any]:
        """Test export for a single zoom level."""
        try:
            # Create scale metadata for this zoom level
            scale_metadata = self.create_scale_metadata(
                original_scale=1.0,
                current_scale=zoom_level,
                zoom_level=zoom_level,
                viewport_size=(800, 600)  # Default viewport
            )
            
            # Export SVG
            exported_svg = self.export_svg_with_scale(svg_content, scale_metadata, options)
            
            # Analyze exported SVG
            analysis = self._analyze_exported_svg(exported_svg, zoom_level)
            
            return {
                'zoom_level': zoom_level,
                'exported_svg': exported_svg,
                'analysis': analysis,
                'scale_metadata': scale_metadata
            }
            
        except Exception as e:
            return {
                'zoom_level': zoom_level,
                'error': str(e),
                'analysis': {}
            }
    
    def _analyze_exported_svg(self, svg_content: str, zoom_level: float) -> Dict[str, Any]:
        """Analyze exported SVG for consistency and quality."""
        try:
            root = etree.fromstring(svg_content.encode('utf-8'))
            
            # Count elements
            element_counts = {}
            for elem in root.iter():
                tag = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag
                element_counts[tag] = element_counts.get(tag, 0) + 1
            
            # Check for scale metadata
            scale_metadata_present = root.find('.//{http://arxos.io/scale}scale') is not None
            
            # Check for export metadata
            export_metadata_present = root.find('.//{http://arxos.io/metadata}export') is not None
            
            # Analyze transformations
            transform_count = 0
            for elem in root.iter():
                if elem.get('transform'):
                    transform_count += 1
            
            return {
                'element_counts': element_counts,
                'scale_metadata_present': scale_metadata_present,
                'export_metadata_present': export_metadata_present,
                'transform_count': transform_count,
                'total_elements': sum(element_counts.values()),
                'zoom_level': zoom_level
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    def _calculate_consistency_score(self, tested_levels: List[Dict[str, Any]]) -> float:
        """Calculate consistency score across zoom levels."""
        if not tested_levels:
            return 0.0
        
        # Calculate element count consistency
        element_counts = []
        for level in tested_levels:
            if 'analysis' in level and 'total_elements' in level['analysis']:
                element_counts.append(level['analysis']['total_elements'])
        
        if not element_counts:
            return 0.0
        
        # Calculate coefficient of variation
        mean_count = sum(element_counts) / len(element_counts)
        if mean_count == 0:
            return 0.0
        
        variance = sum((count - mean_count) ** 2 for count in element_counts) / len(element_counts)
        std_dev = math.sqrt(variance)
        cv = std_dev / mean_count
        
        # Convert to consistency score (0-1, higher is better)
        consistency_score = max(0.0, 1.0 - cv)
        
        return consistency_score
    
    def _analyze_scale_variations(self, tested_levels: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Analyze scale variations across zoom levels."""
        variations = []
        
        for level in tested_levels:
            if 'scale_metadata' in level:
                metadata = level['scale_metadata']
                variations.append({
                    'zoom_level': metadata.zoom_level,
                    'scale_factor': metadata.scale_factor,
                    'original_scale': metadata.original_scale,
                    'current_scale': metadata.current_scale
                })
        
        return variations
    
    def _generate_export_recommendations(self, results: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on test results."""
        recommendations = []
        
        consistency_score = results.get('consistency_score', 0.0)
        
        if consistency_score < 0.8:
            recommendations.append("Consider standardizing element counts across zoom levels")
        
        if consistency_score < 0.6:
            recommendations.append("Review scale transformation logic for better consistency")
        
        # Check for missing metadata
        tested_levels = results.get('tested_levels', [])
        for level in tested_levels:
            if 'analysis' in level and not level['analysis'].get('scale_metadata_present', False):
                recommendations.append("Ensure scale metadata is embedded in all exports")
                break
        
        if not recommendations:
            recommendations.append("Export consistency is good, no major issues detected")
        
        return recommendations
    
    def validate_export_compatibility(self, exported_svg: str, target_formats: List[str]) -> Dict[str, Any]:
        """
        Validate exported file compatibility with different tools.
        
        Args:
            exported_svg: Exported SVG content
            target_formats: List of target formats to validate
            
        Returns:
            Compatibility validation results
        """
        results = {
            'svg_validation': {},
            'format_compatibility': {},
            'overall_compatibility': 0.0,
            'issues': [],
            'warnings': []
        }
        
        try:
            # Validate SVG structure
            results['svg_validation'] = self._validate_svg_structure(exported_svg)
            
            # Check format compatibility
            for format_name in target_formats:
                results['format_compatibility'][format_name] = self._check_format_compatibility(
                    exported_svg, format_name
                )
            
            # Calculate overall compatibility score
            results['overall_compatibility'] = self._calculate_compatibility_score(results)
            
            logger.info(f"Export compatibility validation completed with score: {results['overall_compatibility']:.2f}")
            return results
            
        except Exception as e:
            logger.error(f"Error validating export compatibility: {e}")
            raise ValidationError(f"Error validating export compatibility: {e}") from e
    
    def _validate_svg_structure(self, svg_content: str) -> Dict[str, Any]:
        """Validate SVG structure and syntax."""
        try:
            root = etree.fromstring(svg_content.encode('utf-8'))
            
            # Check for required SVG elements
            has_svg_root = root.tag.endswith('svg')
            has_viewbox = root.get('viewBox') is not None
            has_dimensions = (root.get('width') is not None and root.get('height') is not None)
            
            # Check for metadata
            has_metadata = root.find('.//{http://www.w3.org/2000/svg}metadata') is not None
            
            # Check for valid elements
            valid_elements = ['rect', 'circle', 'line', 'path', 'text', 'g', 'use']
            element_validation = {}
            
            for elem_name in valid_elements:
                elements = root.findall(f'.//{{{self._get_svg_namespace()}}}{elem_name}')
                element_validation[elem_name] = len(elements)
            
            return {
                'is_valid': True,
                'has_svg_root': has_svg_root,
                'has_viewbox': has_viewbox,
                'has_dimensions': has_dimensions,
                'has_metadata': has_metadata,
                'element_counts': element_validation,
                'total_elements': sum(element_validation.values())
            }
            
        except Exception as e:
            return {
                'is_valid': False,
                'error': str(e)
            }
    
    def _check_format_compatibility(self, svg_content: str, format_name: str) -> Dict[str, Any]:
        """Check compatibility with specific format."""
        compatibility_checks = {
            'bim': self._check_bim_compatibility,
            'cad': self._check_cad_compatibility,
            'web': self._check_web_compatibility,
            'print': self._check_print_compatibility
        }
        
        if format_name in compatibility_checks:
            return compatibility_checks[format_name](svg_content)
        else:
            return {
                'compatible': False,
                'reason': f'Unknown format: {format_name}'
            }
    
    def _check_bim_compatibility(self, svg_content: str) -> Dict[str, Any]:
        """Check BIM tool compatibility."""
        try:
            root = etree.fromstring(svg_content.encode('utf-8'))
            
            # Check for BIM-specific metadata
            has_bim_metadata = root.find('.//{http://arxos.io/metadata}export') is not None
            has_scale_info = root.find('.//{http://arxos.io/scale}scale') is not None
            
            # Check for coordinate system information
            has_coordinates = any(
                elem.get('data-x') is not None and elem.get('data-y') is not None
                for elem in root.iter()
            )
            
            return {
                'compatible': has_bim_metadata and has_scale_info,
                'has_metadata': has_bim_metadata,
                'has_scale_info': has_scale_info,
                'has_coordinates': has_coordinates,
                'score': 0.8 if has_bim_metadata and has_scale_info else 0.3
            }
            
        except Exception as e:
            return {
                'compatible': False,
                'error': str(e)
            }
    
    def _check_cad_compatibility(self, svg_content: str) -> Dict[str, Any]:
        """Check CAD tool compatibility."""
        try:
            root = etree.fromstring(svg_content.encode('utf-8'))
            
            # Check for CAD-friendly elements
            has_paths = len(root.findall('.//{http://www.w3.org/2000/svg}path')) > 0
            has_lines = len(root.findall('.//{http://www.w3.org/2000/svg}line')) > 0
            has_rectangles = len(root.findall('.//{http://www.w3.org/2000/svg}rect')) > 0
            
            # Check for proper scaling
            has_viewbox = root.get('viewBox') is not None
            has_dimensions = (root.get('width') is not None and root.get('height') is not None)
            
            return {
                'compatible': has_paths or has_lines or has_rectangles,
                'has_paths': has_paths,
                'has_lines': has_lines,
                'has_rectangles': has_rectangles,
                'has_viewbox': has_viewbox,
                'has_dimensions': has_dimensions,
                'score': 0.7 if (has_paths or has_lines or has_rectangles) else 0.2
            }
            
        except Exception as e:
            return {
                'compatible': False,
                'error': str(e)
            }
    
    def _check_web_compatibility(self, svg_content: str) -> Dict[str, Any]:
        """Check web browser compatibility."""
        try:
            root = etree.fromstring(svg_content.encode('utf-8'))
            
            # Check for web-safe elements
            has_web_elements = len(root.findall('.//{http://www.w3.org/2000/svg}g')) > 0
            has_styling = any(elem.get('style') is not None for elem in root.iter())
            
            # Check for proper namespace
            has_svg_namespace = 'http://www.w3.org/2000/svg' in root.nsmap.values()
            
            return {
                'compatible': has_web_elements and has_svg_namespace,
                'has_web_elements': has_web_elements,
                'has_styling': has_styling,
                'has_svg_namespace': has_svg_namespace,
                'score': 0.9 if has_web_elements and has_svg_namespace else 0.4
            }
            
        except Exception as e:
            return {
                'compatible': False,
                'error': str(e)
            }
    
    def _check_print_compatibility(self, svg_content: str) -> Dict[str, Any]:
        """Check print compatibility."""
        try:
            root = etree.fromstring(svg_content.encode('utf-8'))
            
            # Check for print-friendly attributes
            has_dimensions = (root.get('width') is not None and root.get('height') is not None)
            has_viewbox = root.get('viewBox') is not None
            
            # Check for proper scaling
            has_scale_info = root.find('.//{http://arxos.io/scale}scale') is not None
            
            return {
                'compatible': has_dimensions and has_viewbox,
                'has_dimensions': has_dimensions,
                'has_viewbox': has_viewbox,
                'has_scale_info': has_scale_info,
                'score': 0.8 if has_dimensions and has_viewbox else 0.3
            }
            
        except Exception as e:
            return {
                'compatible': False,
                'error': str(e)
            }
    
    def _calculate_compatibility_score(self, results: Dict[str, Any]) -> float:
        """Calculate overall compatibility score."""
        format_scores = []
        
        for format_name, compatibility in results.get('format_compatibility', {}).items():
            if 'score' in compatibility:
                format_scores.append(compatibility['score'])
        
        if not format_scores:
            return 0.0
        
        return sum(format_scores) / len(format_scores)
    
    def _get_svg_namespace(self) -> str:
        """Get SVG namespace."""
        return "http://www.w3.org/2000/svg"
    
    def generate_export_report(self, test_results: Dict[str, Any]) -> str:
        """Generate comprehensive export report."""
        report = []
        report.append("# Export Integration Report")
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        # Consistency Results
        report.append("## Export Consistency")
        consistency_score = test_results.get('consistency_score', 0.0)
        report.append(f"Overall Consistency Score: {consistency_score:.2f}")
        report.append("")
        
        # Tested Levels
        report.append("### Tested Zoom Levels")
        for level in test_results.get('tested_levels', []):
            zoom_level = level.get('zoom_level', 'Unknown')
            if 'analysis' in level:
                analysis = level['analysis']
                total_elements = analysis.get('total_elements', 0)
                report.append(f"- Zoom {zoom_level}: {total_elements} elements")
        report.append("")
        
        # Issues and Recommendations
        issues = test_results.get('issues', [])
        if issues:
            report.append("## Issues Found")
            for issue in issues:
                report.append(f"- {issue}")
            report.append("")
        
        recommendations = test_results.get('recommendations', [])
        if recommendations:
            report.append("## Recommendations")
            for rec in recommendations:
                report.append(f"- {rec}")
            report.append("")
        
        return "\n".join(report) 