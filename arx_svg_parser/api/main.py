"""
FastAPI-based API layer for SVG-BIM system.

Provides RESTful endpoints for:
- Uploading SVGs
- Downloading/exporting BIM models
- Querying BIM objects, relationships, and metadata
- Health/status checks
"""

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel
from typing import Dict, List, Any, Optional
import structlog
import tempfile
import os
from pathlib import Path

from services.svg_parser import extract_svg_elements
from services.enhanced_bim_assembly import EnhancedBIMAssembly, AssemblyConfig
from services.export_integration import ExportIntegration
from utils.errors import (
    SVGParseError, BIMAssemblyError, GeometryError, RelationshipError, 
    EnrichmentError, ValidationError, ExportError, APIError
)
from routers import symbol_management
from routers import auth
from routers import export_interoperability
from routers import advanced_infrastructure
from routers import advanced_security
from routers import ahj_api
from routers import arkit_calibration_sync
from routers import smart_tagging_kits
from routers import data_api_structuring
from routers import contributor_reputation
from routers import cmms_maintenance_hooks
from routers import data_vendor_api_expansion
from routers import multi_system_integration
from routers import ahj_api_integration
from routers import advanced_export_interoperability
from arx_common.handlers import error_handlers as common_error_handlers
from fastapi.exceptions import RequestValidationError
from arx_svg_parser.main import register_exception_handlers

logger = structlog.get_logger(__name__)

app = FastAPI(
    title="SVG-BIM API",
    description="API for SVG to BIM conversion and management",
    version="1.0.0"
)

# Initialize services
bim_pipeline = EnhancedBIMAssembly()
export_service = ExportIntegration()

logger.info("api_services_initialized",
           bim_pipeline="EnhancedBIMAssembly",
           export_service="ExportIntegration")

# Register unified error handlers
app.add_exception_handler(HTTPException, common_error_handlers.http_exception_handler)
app.add_exception_handler(RequestValidationError, common_error_handlers.validation_exception_handler)
app.add_exception_handler(Exception, common_error_handlers.generic_exception_handler)
register_exception_handlers(app)

logger.info("error_handlers_registered",
           handlers=["HTTPException", "RequestValidationError", "Exception"])

# Include routers
app.include_router(symbol_management.router, prefix="/api/v1")
app.include_router(auth.router, prefix="/api/v1")
app.include_router(export_interoperability.router, prefix="/api/v1")
app.include_router(advanced_infrastructure.router, prefix="/api/v1")
app.include_router(advanced_security.router, prefix="/api/v1")
app.include_router(ahj_api.router, prefix="/api/v1")
app.include_router(arkit_calibration_sync.router, prefix="/api/v1")
app.include_router(smart_tagging_kits.router, prefix="/api/v1")
app.include_router(data_api_structuring.router, prefix="/api/v1")
app.include_router(contributor_reputation.router, prefix="/api/v1")
app.include_router(cmms_maintenance_hooks.router, prefix="/api/v1")
app.include_router(data_vendor_api_expansion.router, prefix="/api/v1")
app.include_router(multi_system_integration.router, prefix="/api/v1")
app.include_router(ahj_api_integration.router, prefix="/api/v1")
app.include_router(advanced_export_interoperability.router, prefix="/api/v1")

logger.info("routers_included",
           router_count=16,
           routers=[
               "symbol_management", "auth", "export_interoperability",
               "advanced_infrastructure", "advanced_security", "ahj_api",
               "arkit_calibration_sync", "smart_tagging_kits", "data_api_structuring",
               "contributor_reputation", "cmms_maintenance_hooks", "data_vendor_api_expansion",
               "multi_system_integration", "ahj_api_integration", "advanced_export_interoperability"
           ])

class HealthResponse(BaseModel):
    status: str
    message: str
    version: str

class SVGUploadResponse(BaseModel):
    success: bool
    message: str
    element_count: int
    svg_id: str

class BIMExportResponse(BaseModel):
    success: bool
    message: str
    file_path: str
    format: str

class BIMQueryResponse(BaseModel):
    success: bool
    data: Dict[str, Any]
    count: int

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    try:
        logger.debug("health_check_requested")
        
        response = HealthResponse(
            status="healthy",
            message="SVG-BIM API is running",
            version="1.0.0"
        )
        
        logger.debug("health_check_completed", status="healthy")
        return response
        
    except Exception as e:
        logger.error("health_check_failed",
                    error=str(e),
                    error_type=type(e).__name__)
        raise HTTPException(status_code=500, detail="Health check failed")

@app.post("/upload/svg", response_model=SVGUploadResponse)
async def upload_svg(file: UploadFile = File(...)):
    """Upload and parse SVG file."""
    try:
        logger.info("svg_upload_attempt",
                   filename=file.filename,
                   content_type=file.content_type,
                   file_size=file.size if hasattr(file, 'size') else "unknown")
        
        if not file.filename.endswith('.svg'):
            logger.warning("svg_upload_failed_invalid_format",
                          filename=file.filename,
                          expected_format=".svg")
            raise HTTPException(status_code=400, detail="File must be an SVG")
        
        # Read SVG content
        svg_content = await file.read()
        svg_content_str = svg_content.decode('utf-8')
        
        # Parse SVG
        elements = extract_svg_elements(svg_content_str)
        
        # Generate unique ID for this SVG
        svg_id = f"svg_{len(elements)}_{hash(svg_content_str) % 10000}"
        
        logger.info("svg_upload_successful",
                   filename=file.filename,
                   svg_id=svg_id,
                   element_count=len(elements),
                   content_length=len(svg_content_str))
        
        return SVGUploadResponse(
            success=True,
            message="SVG uploaded and parsed successfully",
            element_count=len(elements),
            svg_id=svg_id
        )
        
    except SVGParseError as e:
        logger.error("svg_parsing_error",
                    filename=file.filename,
                    error=str(e),
                    error_type="SVGParseError")
        raise HTTPException(status_code=400, detail=f"SVG parsing failed: {str(e)}")
    except Exception as e:
        logger.error("svg_upload_unexpected_error",
                    filename=file.filename,
                    error=str(e),
                    error_type=type(e).__name__)
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/assemble/bim", response_model=BIMExportResponse)
async def assemble_bim(
    svg_content: str = Form(...),
    format: str = Form("json"),
    validation_level: str = Form("standard")
):
    """Assemble BIM from SVG content."""
    try:
        logger.info("bim_assembly_attempt",
                   format=format,
                   validation_level=validation_level,
                   content_length=len(svg_content))
        
        # Parse SVG
        svg_elements = extract_svg_elements(svg_content)
        
        # Configure assembly
        config = AssemblyConfig(
            validation_level=validation_level,
            conflict_resolution_enabled=True,
            performance_optimization_enabled=True
        )
        
        # Assemble BIM
        svg_data = {"elements": svg_elements}
        result = bim_pipeline.assemble_bim(svg_data, config=config)
        
        if not result.success:
            logger.warning("bim_assembly_failed",
                          format=format,
                          validation_level=validation_level,
                          element_count=len(svg_elements))
            raise HTTPException(status_code=400, detail="BIM assembly failed")
        
        # Export BIM data
        bim_data = {
            "elements": [elem.dict() for elem in result.elements],
            "systems": [sys.dict() for sys in result.systems],
            "spaces": [space.dict() for space in result.spaces],
            "relationships": [rel.dict() for rel in result.relationships],
            "metadata": {
                "assembly_time": result.assembly_time,
                "element_count": len(result.elements),
                "system_count": len(result.systems),
                "space_count": len(result.spaces),
                "relationship_count": len(result.relationships)
            }
        }
        
        # Save to temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix=f'.{format}', delete=False) as f:
            if format == "json":
                import json
                json.dump(bim_data, f, indent=2)
            elif format == "xml":
                import xml.etree.ElementTree as ET
                root = ET.Element("BIMAssembly")
                # Convert dict to XML (simplified)
                for key, value in bim_data.items():
                    elem = ET.SubElement(root, key)
                    elem.text = str(value)
                tree = ET.ElementTree(root)
                tree.write(f.name, encoding='utf-8', xml_declaration=True)
            else:
                logger.warning("bim_export_unsupported_format",
                              format=format,
                              supported_formats=["json", "xml"])
                raise HTTPException(status_code=400, detail=f"Unsupported format: {format}")
            
            file_path = f.name
        
        logger.info("bim_assembly_successful",
                   format=format,
                   file_path=file_path,
                   element_count=len(result.elements),
                   system_count=len(result.systems),
                   space_count=len(result.spaces),
                   relationship_count=len(result.relationships),
                   assembly_time=result.assembly_time)
        
        return BIMExportResponse(
            success=True,
            message="BIM assembled successfully",
            file_path=file_path,
            format=format
        )
        
    except BIMAssemblyError as e:
        logger.error("bim_assembly_error",
                    format=format,
                    validation_level=validation_level,
                    error=str(e),
                    error_type="BIMAssemblyError")
        raise HTTPException(status_code=400, detail=f"BIM assembly failed: {str(e)}")
    except Exception as e:
        logger.error("bim_assembly_unexpected_error",
                    format=format,
                    validation_level=validation_level,
                    error=str(e),
                    error_type=type(e).__name__)
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/export/bim/{file_id}", response_model=BIMExportResponse)
async def export_bim(file_id: str, format: str = "json"):
    """Export BIM data in specified format."""
    try:
        logger.info("bim_export_attempt",
                   file_id=file_id,
                   format=format)
        
        # This would typically load from a database or file system
        # For now, return a mock response
        bim_data = {
            "elements": [],
            "systems": [],
            "spaces": [],
            "relationships": [],
            "metadata": {"file_id": file_id}
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix=f'.{format}', delete=False) as f:
            if format == "json":
                import json
                json.dump(bim_data, f, indent=2)
            elif format == "xml":
                import xml.etree.ElementTree as ET
                root = ET.Element("BIMAssembly")
                for key, value in bim_data.items():
                    elem = ET.SubElement(root, key)
                    elem.text = str(value)
                tree = ET.ElementTree(root)
                tree.write(f.name, encoding='utf-8', xml_declaration=True)
            else:
                logger.warning("bim_export_unsupported_format",
                              file_id=file_id,
                              format=format,
                              supported_formats=["json", "xml"])
                raise HTTPException(status_code=400, detail=f"Unsupported format: {format}")
            
            file_path = f.name
        
        logger.info("bim_export_successful",
                   file_id=file_id,
                   format=format,
                   file_path=file_path)
        
        return BIMExportResponse(
            success=True,
            message="BIM exported successfully",
            file_path=file_path,
            format=format
        )
        
    except Exception as e:
        logger.error("bim_export_failed",
                    file_id=file_id,
                    format=format,
                    error=str(e),
                    error_type=type(e).__name__)
        raise HTTPException(status_code=500, detail="Export failed")

@app.get("/query/bim/{file_id}", response_model=BIMQueryResponse)
async def query_bim(file_id: str, query_type: str = "summary"):
    """Query BIM data by file ID."""
    try:
        logger.info("bim_query_attempt",
                   file_id=file_id,
                   query_type=query_type)
        
        # This would typically query a database
        # For now, return mock data
        mock_data = {
            "file_id": file_id,
            "query_type": query_type,
            "elements": [],
            "systems": [],
            "spaces": [],
            "relationships": []
        }
        
        logger.info("bim_query_successful",
                   file_id=file_id,
                   query_type=query_type,
                   result_count=len(mock_data))
        
        return BIMQueryResponse(
            success=True,
            data=mock_data,
            count=len(mock_data)
        )
        
    except Exception as e:
        logger.error("bim_query_failed",
                    file_id=file_id,
                    query_type=query_type,
                    error=str(e),
                    error_type=type(e).__name__)
        raise HTTPException(status_code=500, detail="Query failed")

@app.get("/download/{file_path:path}")
async def download_file(file_path: str):
    """Download a file by path."""
    try:
        logger.info("file_download_attempt",
                   file_path=file_path)
        
        # Validate file path for security
        if ".." in file_path or file_path.startswith("/"):
            logger.warning("file_download_security_violation",
                          file_path=file_path,
                          reason="path_traversal_attempt")
            raise HTTPException(status_code=400, detail="Invalid file path")
        
        # Check if file exists
        if not os.path.exists(file_path):
            logger.warning("file_download_not_found",
                          file_path=file_path)
            raise HTTPException(status_code=404, detail="File not found")
        
        logger.info("file_download_successful",
                   file_path=file_path,
                   file_size=os.path.getsize(file_path))
        
        return FileResponse(file_path)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("file_download_failed",
                    file_path=file_path,
                    error=str(e),
                    error_type=type(e).__name__)
        raise HTTPException(status_code=500, detail="Download failed")

# Startup event
@app.on_event("startup")
async def startup_event():
    """Application startup event."""
    logger.info("api_startup_completed",
               title="SVG-BIM API",
               version="1.0.0",
               description="API for SVG to BIM conversion and management")

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown event."""
    logger.info("api_shutdown_completed") 