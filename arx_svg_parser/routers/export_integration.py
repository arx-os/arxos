"""
Export Integration Router

FastAPI router for export integration endpoints that handle SVG export with
proper scale preservation, metadata embedding, and compatibility validation.

Phase 7.3: Export Integration
- Update SVG export to maintain proper scale
- Add scale metadata to exported files
- Test export consistency across zoom levels
- Validate exported file compatibility
"""

from fastapi import APIRouter, HTTPException, Form, Query, UploadFile, File
from typing import Optional, List, Dict, Any
import logging
from services.export_integration import (
    ExportIntegration, ScaleMetadata, ExportMetadata, ExportOptions
)
from models.parse import ParseRequest

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/v1/export", tags=["export"])

# Initialize export integration service
export_integration = ExportIntegration()


@router.post("/svg-with-scale")
async def export_svg_with_scale(
    svg_content: str = Form(..., description="SVG content to export"),
    original_scale: float = Form(1.0, description="Original scale factor"),
    current_scale: float = Form(1.0, description="Current scale factor"),
    zoom_level: float = Form(1.0, description="Current zoom level"),
    viewport_width: float = Form(800, description="Viewport width"),
    viewport_height: float = Form(600, description="Viewport height"),
    units: str = Form("mm", description="Units for scale"),
    include_metadata: bool = Form(True, description="Include metadata in export"),
    include_scale_info: bool = Form(True, description="Include scale information"),
    optimize_svg: bool = Form(True, description="Optimize SVG output")
):
    """
    Export SVG with proper scale preservation and metadata embedding.
    
    This endpoint takes SVG content and exports it with embedded scale information,
    metadata, and proper transformations to maintain scale across different zoom levels.
    """
    try:
        # Create scale metadata
        scale_metadata = export_integration.create_scale_metadata(
            original_scale=original_scale,
            current_scale=current_scale,
            zoom_level=zoom_level,
            viewport_size=(viewport_width, viewport_height),
            units=units
        )
        
        # Create export options
        options = ExportOptions(
            include_metadata=include_metadata,
            include_scale_info=include_scale_info,
            optimize_svg=optimize_svg,
            export_format="svg",
            scale_factor=scale_metadata.scale_factor,
            units=units
        )
        
        # Export SVG with scale
        exported_svg = export_integration.export_svg_with_scale(
            svg_content, scale_metadata, options
        )
        
        return {
            'exported_svg': exported_svg,
            'scale_metadata': {
                'original_scale': scale_metadata.original_scale,
                'current_scale': scale_metadata.current_scale,
                'zoom_level': scale_metadata.zoom_level,
                'units': scale_metadata.units,
                'scale_factor': scale_metadata.scale_factor,
                'viewport_width': scale_metadata.viewport_width,
                'viewport_height': scale_metadata.viewport_height,
                'coordinate_system': scale_metadata.coordinate_system,
                'created_at': scale_metadata.created_at
            },
            'export_options': {
                'include_metadata': options.include_metadata,
                'include_scale_info': options.include_scale_info,
                'optimize_svg': options.optimize_svg,
                'export_format': options.export_format,
                'scale_factor': options.scale_factor,
                'units': options.units
            }
        }
        
    except Exception as e:
        logger.error(f"SVG export with scale failed: {e}")
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


@router.post("/svg-with-sidecar")
async def export_svg_with_metadata_sidecar(
    svg_content: str = Form(..., description="SVG content to export"),
    title: str = Form("Floor Plan", description="Export title"),
    description: str = Form("", description="Export description"),
    building_id: str = Form(..., description="Building identifier"),
    floor_label: str = Form(..., description="Floor label"),
    original_scale: float = Form(1.0, description="Original scale factor"),
    current_scale: float = Form(1.0, description="Current scale factor"),
    zoom_level: float = Form(1.0, description="Current zoom level"),
    viewport_width: float = Form(800, description="Viewport width"),
    viewport_height: float = Form(600, description="Viewport height"),
    units: str = Form("mm", description="Units for scale"),
    symbol_count: int = Form(0, description="Number of symbols in the SVG"),
    element_count: int = Form(0, description="Number of elements in the SVG"),
    created_by: str = Form("system", description="User who created the export")
):
    """
    Export SVG with metadata sidecar file.
    
    This endpoint exports SVG content with both embedded metadata and a separate
    metadata sidecar file for external tool compatibility.
    """
    try:
        # Create scale metadata
        scale_metadata = export_integration.create_scale_metadata(
            original_scale=original_scale,
            current_scale=current_scale,
            zoom_level=zoom_level,
            viewport_size=(viewport_width, viewport_height),
            units=units
        )
        
        # Create export metadata
        export_metadata = ExportMetadata(
            title=title,
            description=description,
            building_id=building_id,
            floor_label=floor_label,
            version="1.0",
            created_at=scale_metadata.created_at,
            created_by=created_by,
            scale_metadata=scale_metadata,
            symbol_count=symbol_count,
            element_count=element_count,
            export_format="svg",
            export_version="1.0"
        )
        
        # Create export options
        options = ExportOptions(
            include_metadata=True,
            include_scale_info=True,
            optimize_svg=True,
            export_format="svg",
            scale_factor=scale_metadata.scale_factor,
            units=units
        )
        
        # Export with sidecar
        result = export_integration.export_with_metadata_sidecar(
            svg_content, export_metadata, options
        )
        
        return {
            'svg': result['svg'],
            'metadata': result['metadata'],
            'format': result['format'],
            'export_metadata': {
                'title': export_metadata.title,
                'description': export_metadata.description,
                'building_id': export_metadata.building_id,
                'floor_label': export_metadata.floor_label,
                'version': export_metadata.version,
                'created_at': export_metadata.created_at,
                'created_by': export_metadata.created_by,
                'symbol_count': export_metadata.symbol_count,
                'element_count': export_metadata.element_count,
                'export_format': export_metadata.export_format,
                'export_version': export_metadata.export_version
            }
        }
        
    except Exception as e:
        logger.error(f"SVG export with sidecar failed: {e}")
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


@router.post("/test-consistency")
async def test_export_consistency(
    svg_content: str = Form(..., description="SVG content to test"),
    zoom_levels: str = Form("0.25,0.5,1.0,2.0,4.0", description="Comma-separated zoom levels to test"),
    include_metadata: bool = Form(True, description="Include metadata in test exports"),
    include_scale_info: bool = Form(True, description="Include scale information"),
    optimize_svg: bool = Form(True, description="Optimize SVG output"),
    units: str = Form("mm", description="Units for scale")
):
    """
    Test export consistency across different zoom levels.
    
    This endpoint tests how well the export maintains consistency across
    different zoom levels and provides recommendations for improvement.
    """
    try:
        # Parse zoom levels
        zoom_level_list = [float(z.strip()) for z in zoom_levels.split(',')]
        
        # Create export options
        options = ExportOptions(
            include_metadata=include_metadata,
            include_scale_info=include_scale_info,
            optimize_svg=optimize_svg,
            export_format="svg",
            scale_factor=1.0,
            units=units
        )
        
        # Test consistency
        results = export_integration.test_export_consistency(
            svg_content, zoom_level_list, options
        )
        
        # Generate report
        report = export_integration.generate_export_report(results)
        
        return {
            'consistency_score': results['consistency_score'],
            'tested_levels': len(results['tested_levels']),
            'scale_variations': results['scale_variations'],
            'issues': results['issues'],
            'recommendations': results['recommendations'],
            'report': report,
            'detailed_results': {
                'tested_levels': [
                    {
                        'zoom_level': level.get('zoom_level'),
                        'total_elements': level.get('analysis', {}).get('total_elements', 0),
                        'scale_metadata_present': level.get('analysis', {}).get('scale_metadata_present', False),
                        'export_metadata_present': level.get('analysis', {}).get('export_metadata_present', False)
                    }
                    for level in results.get('tested_levels', [])
                ]
            }
        }
        
    except Exception as e:
        logger.error(f"Export consistency test failed: {e}")
        raise HTTPException(status_code=500, detail=f"Consistency test failed: {str(e)}")


@router.post("/validate-compatibility")
async def validate_export_compatibility(
    exported_svg: str = Form(..., description="Exported SVG content to validate"),
    target_formats: str = Form("bim,cad,web,print", description="Comma-separated target formats to validate")
):
    """
    Validate exported file compatibility with different tools.
    
    This endpoint validates how well the exported SVG works with different
    target formats and tools like BIM software, CAD applications, web browsers, and print.
    """
    try:
        # Parse target formats
        format_list = [f.strip() for f in target_formats.split(',')]
        
        # Validate compatibility
        results = export_integration.validate_export_compatibility(
            exported_svg, format_list
        )
        
        return {
            'overall_compatibility': results['overall_compatibility'],
            'svg_validation': results['svg_validation'],
            'format_compatibility': results['format_compatibility'],
            'issues': results['issues'],
            'warnings': results['warnings'],
            'summary': {
                'is_svg_valid': results['svg_validation'].get('is_valid', False),
                'compatible_formats': [
                    format_name for format_name, compatibility in results['format_compatibility'].items()
                    if compatibility.get('compatible', False)
                ],
                'total_formats_tested': len(results['format_compatibility']),
                'compatible_formats_count': len([
                    format_name for format_name, compatibility in results['format_compatibility'].items()
                    if compatibility.get('compatible', False)
                ])
            }
        }
        
    except Exception as e:
        logger.error(f"Export compatibility validation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Compatibility validation failed: {str(e)}")


@router.post("/batch-export")
async def batch_export_with_scale(
    file: UploadFile = File(..., description="SVG file to export"),
    zoom_levels: str = Form("0.25,0.5,1.0,2.0,4.0", description="Comma-separated zoom levels"),
    include_metadata: bool = Form(True, description="Include metadata in exports"),
    include_scale_info: bool = Form(True, description="Include scale information"),
    optimize_svg: bool = Form(True, description="Optimize SVG output"),
    units: str = Form("mm", description="Units for scale"),
    export_format: str = Form("svg", description="Export format")
):
    """
    Batch export SVG at multiple zoom levels.
    
    This endpoint exports the same SVG content at multiple zoom levels,
    creating a set of scaled versions for different use cases.
    """
    try:
        # Read file content
        file_content = await file.read()
        svg_content = file_content.decode('utf-8')
        
        # Parse zoom levels
        zoom_level_list = [float(z.strip()) for z in zoom_levels.split(',')]
        
        # Create export options
        options = ExportOptions(
            include_metadata=include_metadata,
            include_scale_info=include_scale_info,
            optimize_svg=optimize_svg,
            export_format=export_format,
            scale_factor=1.0,
            units=units
        )
        
        # Export at each zoom level
        batch_results = []
        for zoom_level in zoom_level_list:
            try:
                # Create scale metadata
                scale_metadata = export_integration.create_scale_metadata(
                    original_scale=1.0,
                    current_scale=zoom_level,
                    zoom_level=zoom_level,
                    viewport_size=(800, 600),
                    units=units
                )
                
                # Export SVG
                exported_svg = export_integration.export_svg_with_scale(
                    svg_content, scale_metadata, options
                )
                
                batch_results.append({
                    'zoom_level': zoom_level,
                    'exported_svg': exported_svg,
                    'scale_metadata': {
                        'original_scale': scale_metadata.original_scale,
                        'current_scale': scale_metadata.current_scale,
                        'zoom_level': scale_metadata.zoom_level,
                        'units': scale_metadata.units,
                        'scale_factor': scale_metadata.scale_factor,
                        'viewport_width': scale_metadata.viewport_width,
                        'viewport_height': scale_metadata.viewport_height,
                        'coordinate_system': scale_metadata.coordinate_system,
                        'created_at': scale_metadata.created_at
                    },
                    'status': 'success'
                })
                
            except Exception as e:
                batch_results.append({
                    'zoom_level': zoom_level,
                    'error': str(e),
                    'status': 'failed'
                })
        
        # Calculate success rate
        successful_exports = len([r for r in batch_results if r['status'] == 'success'])
        total_exports = len(batch_results)
        success_rate = successful_exports / total_exports if total_exports > 0 else 0
        
        return {
            'batch_results': batch_results,
            'summary': {
                'total_exports': total_exports,
                'successful_exports': successful_exports,
                'failed_exports': total_exports - successful_exports,
                'success_rate': success_rate,
                'zoom_levels_tested': zoom_level_list
            },
            'export_options': {
                'include_metadata': options.include_metadata,
                'include_scale_info': options.include_scale_info,
                'optimize_svg': options.optimize_svg,
                'export_format': options.export_format,
                'units': options.units
            }
        }
        
    except Exception as e:
        logger.error(f"Batch export failed: {e}")
        raise HTTPException(status_code=500, detail=f"Batch export failed: {str(e)}")


@router.get("/export-formats")
async def get_supported_export_formats():
    """
    Get list of supported export formats.
    
    Returns information about all supported export formats and their capabilities.
    """
    try:
        formats = {
            'svg': {
                'name': 'Scalable Vector Graphics',
                'description': 'Vector graphics format with embedded metadata support',
                'supports_scale': True,
                'supports_metadata': True,
                'supports_optimization': True,
                'file_extension': '.svg',
                'mime_type': 'image/svg+xml'
            },
            'json': {
                'name': 'JavaScript Object Notation',
                'description': 'Structured data format with complete metadata',
                'supports_scale': True,
                'supports_metadata': True,
                'supports_optimization': False,
                'file_extension': '.json',
                'mime_type': 'application/json'
            },
            'xml': {
                'name': 'Extensible Markup Language',
                'description': 'Structured markup format with schema validation',
                'supports_scale': True,
                'supports_metadata': True,
                'supports_optimization': True,
                'file_extension': '.xml',
                'mime_type': 'application/xml'
            },
            'pdf': {
                'name': 'Portable Document Format',
                'description': 'Document format with print optimization',
                'supports_scale': True,
                'supports_metadata': True,
                'supports_optimization': True,
                'file_extension': '.pdf',
                'mime_type': 'application/pdf'
            }
        }
        
        return {
            'supported_formats': formats,
            'total_formats': len(formats),
            'default_format': 'svg',
            'recommended_formats': {
                'web': 'svg',
                'print': 'pdf',
                'bim': 'svg',
                'cad': 'svg'
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get export formats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get export formats: {str(e)}")


@router.get("/export-statistics")
async def get_export_statistics():
    """
    Get export integration statistics and performance metrics.
    
    Returns statistics about export operations, performance, and usage patterns.
    """
    try:
        # This would typically come from a database or monitoring system
        # For now, return mock statistics
        statistics = {
            'total_exports': 0,
            'successful_exports': 0,
            'failed_exports': 0,
            'average_export_time': 0.0,
            'most_used_format': 'svg',
            'most_used_zoom_level': 1.0,
            'average_consistency_score': 0.0,
            'average_compatibility_score': 0.0,
            'export_formats_used': {
                'svg': 0,
                'json': 0,
                'xml': 0,
                'pdf': 0
            },
            'zoom_levels_used': {
                '0.25': 0,
                '0.5': 0,
                '1.0': 0,
                '2.0': 0,
                '4.0': 0
            }
        }
        
        return {
            'statistics': statistics,
            'last_updated': '2024-01-01T00:00:00Z',
            'data_source': 'export_integration_service'
        }
        
    except Exception as e:
        logger.error(f"Failed to get export statistics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get export statistics: {str(e)}") 