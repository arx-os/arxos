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
import logging
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

logger = logging.getLogger(__name__)

app = FastAPI(
    title="SVG-BIM API",
    description="API for SVG to BIM conversion and management",
    version="1.0.0"
)

# Initialize services
bim_pipeline = EnhancedBIMAssembly()
export_service = ExportIntegration()

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
        return HealthResponse(
            status="healthy",
            message="SVG-BIM API is running",
            version="1.0.0"
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail="Health check failed")

@app.post("/upload/svg", response_model=SVGUploadResponse)
async def upload_svg(file: UploadFile = File(...)):
    """Upload and parse SVG file."""
    try:
        if not file.filename.endswith('.svg'):
            raise HTTPException(status_code=400, detail="File must be an SVG")
        
        # Read SVG content
        svg_content = await file.read()
        svg_content_str = svg_content.decode('utf-8')
        
        # Parse SVG
        elements = extract_svg_elements(svg_content_str)
        
        # Generate unique ID for this SVG
        svg_id = f"svg_{len(elements)}_{hash(svg_content_str) % 10000}"
        
        logger.info(f"SVG uploaded successfully: {file.filename}, {len(elements)} elements")
        
        return SVGUploadResponse(
            success=True,
            message="SVG uploaded and parsed successfully",
            element_count=len(elements),
            svg_id=svg_id
        )
        
    except SVGParseError as e:
        logger.error(f"SVG parsing error: {e}")
        raise HTTPException(status_code=400, detail=f"SVG parsing failed: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error during SVG upload: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/assemble/bim", response_model=BIMExportResponse)
async def assemble_bim(
    svg_content: str = Form(...),
    format: str = Form("json"),
    validation_level: str = Form("standard")
):
    """Assemble BIM from SVG content."""
    try:
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
                raise HTTPException(status_code=400, detail=f"Unsupported format: {format}")
            
            file_path = f.name
        
        logger.info(f"BIM assembled successfully: {len(result.elements)} elements")
        
        return BIMExportResponse(
            success=True,
            message="BIM assembled successfully",
            file_path=file_path,
            format=format
        )
        
    except BIMAssemblyError as e:
        logger.error(f"BIM assembly error: {e}")
        raise HTTPException(status_code=400, detail=f"BIM assembly failed: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error during BIM assembly: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/export/bim/{file_id}", response_model=BIMExportResponse)
async def export_bim(file_id: str, format: str = "json"):
    """Export BIM data in specified format."""
    try:
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
                raise HTTPException(status_code=400, detail=f"Unsupported format: {format}")
            
            file_path = f.name
        
        return BIMExportResponse(
            success=True,
            message="BIM exported successfully",
            file_path=file_path,
            format=format
        )
        
    except ExportError as e:
        logger.error(f"Export error: {e}")
        raise HTTPException(status_code=400, detail=f"Export failed: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error during export: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/query/bim/{file_id}", response_model=BIMQueryResponse)
async def query_bim(file_id: str, query_type: str = "summary"):
    """Query BIM data."""
    try:
        # Mock query response
        if query_type == "summary":
            data = {
                "element_count": 0,
                "system_count": 0,
                "space_count": 0,
                "relationship_count": 0
            }
        elif query_type == "elements":
            data = {"elements": []}
        elif query_type == "systems":
            data = {"systems": []}
        elif query_type == "spaces":
            data = {"spaces": []}
        elif query_type == "relationships":
            data = {"relationships": []}
        else:
            raise HTTPException(status_code=400, detail=f"Unknown query type: {query_type}")
        
        return BIMQueryResponse(
            success=True,
            data=data,
            count=len(data.get("elements", data.get("systems", data.get("spaces", data.get("relationships", [])))))
        )
        
    except Exception as e:
        logger.error(f"Query error: {e}")
        raise HTTPException(status_code=500, detail="Query failed")

@app.get("/download/{file_path:path}")
async def download_file(file_path: str):
    """Download a file."""
    try:
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="File not found")
        
        return FileResponse(file_path)
        
    except Exception as e:
        logger.error(f"Download error: {e}")
        raise HTTPException(status_code=500, detail="Download failed")

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 