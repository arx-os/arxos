from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Query
from typing import Optional, List, Dict, Any
import logging
from arx_svg_parser.services.symbol_recognition import SymbolRecognitionEngine
from arx_svg_parser.services.symbol_renderer import SymbolRenderer
from arx_svg_parser.services.bim_extraction import BIMExtractor
from arx_svg_parser.models.parse import ParseRequest, ParseResponse, SymbolRecognitionRequest, SymbolRecognitionResponse
from arx_svg_parser.services.pdf_processor import PDFProcessor

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/v1/parse", tags=["parse"])

# Initialize services
symbol_recognition = SymbolRecognitionEngine()
symbol_renderer = SymbolRenderer()
bim_extractor = BIMExtractor()

@router.post("/recognize-symbols", response_model=SymbolRecognitionResponse)
async def recognize_symbols_in_content(
    request: SymbolRecognitionRequest
):
    """
    Recognize building system symbols in text or SVG content.
    
    This endpoint analyzes content and identifies building system symbols
    that match the symbol library, returning confidence scores and metadata.
    """
    try:
        # Recognize symbols in the content
        recognized_symbols = symbol_recognition.recognize_symbols_in_content(
            request.content, 
            content_type=request.content_type
        )
        
        # Get symbol library information
        library_info = symbol_recognition.get_symbol_library_info()
        
        return SymbolRecognitionResponse(
            recognized_symbols=recognized_symbols,
            total_recognized=len(recognized_symbols),
            symbol_library_info=library_info,
            confidence_threshold=request.confidence_threshold,
            content_type=request.content_type
        )
        
    except Exception as e:
        logger.error(f"Symbol recognition failed: {e}")
        raise HTTPException(status_code=500, detail=f"Symbol recognition failed: {str(e)}")

@router.post("/render-symbols")
async def render_recognized_symbols(
    svg_content: str = Form(..., description="SVG content to render symbols into"),
    building_id: str = Form(..., description="Building identifier"),
    floor_label: str = Form(..., description="Floor label"),
    symbol_ids: Optional[str] = Form(None, description="Comma-separated list of symbol IDs to render")
):
    """
    Render recognized symbols into SVG content.
    
    This endpoint takes SVG content and renders recognized symbols as
    dynamic SVG elements with metadata and positioning.
    """
    try:
        # Parse symbol IDs if provided
        symbols_to_render = []
        if symbol_ids:
            symbol_id_list = [s.strip() for s in symbol_ids.split(',')]
            for symbol_id in symbol_id_list:
                symbol_data = symbol_recognition.get_symbol_metadata(symbol_id)
                if symbol_data:
                    symbols_to_render.append({
                        'symbol_id': symbol_id,
                        'symbol_data': symbol_data,
                        'confidence': 1.0,
                        'match_type': 'manual'
                    })
        
        # If no specific symbols provided, recognize from SVG content
        if not symbols_to_render:
            recognized_symbols = symbol_recognition.recognize_symbols_in_content(
                svg_content, content_type='svg'
            )
            symbols_to_render = recognized_symbols
        
        # Render symbols into SVG
        render_result = symbol_renderer.render_recognized_symbols(
            svg_content, symbols_to_render, building_id, floor_label
        )
        
        return {
            'svg': render_result['svg'],
            'rendered_symbols': render_result['rendered_symbols'],
            'total_recognized': render_result['total_recognized'],
            'total_rendered': render_result['total_rendered'],
            'building_id': building_id,
            'floor_label': floor_label
        }
        
    except Exception as e:
        logger.error(f"Symbol rendering failed: {e}")
        raise HTTPException(status_code=500, detail=f"Symbol rendering failed: {str(e)}")

@router.post("/auto-recognize-and-render")
async def auto_recognize_and_render(
    file: UploadFile = File(..., description="PDF or SVG file to process"),
    building_id: str = Form(..., description="Building identifier"),
    floor_label: str = Form(..., description="Floor label"),
    confidence_threshold: float = Form(0.5, description="Minimum confidence for symbol recognition")
):
    """
    Automatically recognize and render symbols from uploaded file.
    
    This endpoint combines symbol recognition and rendering in a single operation,
    processing the uploaded file and returning SVG with rendered symbols.
    """
    try:
        # Read file content
        file_content = await file.read()
        
        # Determine file type
        file_type = file.filename.lower().split('.')[-1]
        
        if file_type == 'pdf':
            # Use PDF processor for PDF files
            pdf_processor = PDFProcessor()
            result = pdf_processor.process_pdf(file_content, building_id, floor_label)
            
            return {
                'svg': result['svg'],
                'recognized_symbols': result['recognized_symbols'],
                'rendered_symbols': result['rendered_symbols'],
                'recognition_stats': result['recognition_stats'],
                'summary': result['summary'],
                'building_id': building_id,
                'floor_label': floor_label,
                'file_type': 'pdf'
            }
            
        elif file_type == 'svg':
            # Process SVG file
            svg_content = file_content.decode('utf-8')
            
            # Recognize symbols
            recognized_symbols = symbol_recognition.recognize_symbols_in_content(
                svg_content, content_type='svg'
            )
            
            # Filter by confidence threshold
            filtered_symbols = [
                s for s in recognized_symbols 
                if s['confidence'] >= confidence_threshold
            ]
            
            # Render symbols
            render_result = symbol_renderer.render_recognized_symbols(
                svg_content, filtered_symbols, building_id, floor_label
            )
            
            return {
                'svg': render_result['svg'],
                'recognized_symbols': recognized_symbols,
                'rendered_symbols': render_result['rendered_symbols'],
                'recognition_stats': {
                    'total_recognized': len(recognized_symbols),
                    'total_rendered': render_result['total_rendered'],
                    'confidence_threshold': confidence_threshold
                },
                'building_id': building_id,
                'floor_label': floor_label,
                'file_type': 'svg'
            }
            
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported file type: {file_type}")
        
    except Exception as e:
        logger.error(f"Auto recognition and rendering failed: {e}")
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")

@router.get("/symbol-library")
async def get_symbol_library(
    system: Optional[str] = Query(None, description="Filter by building system"),
    category: Optional[str] = Query(None, description="Filter by category"),
    search: Optional[str] = Query(None, description="Search in symbol names and descriptions")
):
    """
    Get information about the symbol library.
    
    Returns available symbols with filtering options by system, category, or search terms.
    """
    try:
        # Get symbol library info
        library_info = symbol_recognition.get_symbol_library_info()
        
        # Get filtered symbols
        symbols = symbol_recognition.symbol_library
        
        # Apply filters
        if system:
            symbols = {
                k: v for k, v in symbols.items() 
                if v.get('system') == system
            }
        
        if category:
            symbols = {
                k: v for k, v in symbols.items() 
                if v.get('category') == category
            }
        
        if search:
            search_lower = search.lower()
            symbols = {
                k: v for k, v in symbols.items() 
                if (search_lower in k.lower() or 
                    search_lower in v.get('display_name', '').lower() or
                    search_lower in ' '.join(v.get('tags', [])).lower())
            }
        
        return {
            'library_info': library_info,
            'symbols': symbols,
            'total_symbols': len(symbols),
            'filters_applied': {
                'system': system,
                'category': category,
                'search': search
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get symbol library: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get symbol library: {str(e)}")

@router.get("/systems")
async def get_available_systems():
    """
    Get list of available building systems in the symbol library.
    """
    try:
        systems = symbol_recognition.get_symbol_library_info()['systems']
        return {
            'systems': systems,
            'total_systems': len(systems)
        }
    except Exception as e:
        logger.error(f"Failed to get systems: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get systems: {str(e)}")

@router.get("/categories")
async def get_available_categories():
    """
    Get list of available categories in the symbol library.
    """
    try:
        categories = symbol_recognition.get_symbol_library_info()['categories']
        return {
            'categories': categories,
            'total_categories': len(categories)
        }
    except Exception as e:
        logger.error(f"Failed to get categories: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get categories: {str(e)}")

@router.post("/extract-bim")
async def extract_bim_from_svg_with_symbols(
    svg_content: str = Form(..., description="SVG content with rendered symbols"),
    building_id: Optional[str] = Form(None, description="Building identifier"),
    floor_label: Optional[str] = Form(None, description="Floor label")
):
    """
    Extract comprehensive BIM data from SVG with recognized symbols.
    
    This endpoint analyzes SVG content containing rendered symbols and
    extracts structured BIM data including rooms, devices, systems, and relationships.
    """
    try:
        # Extract BIM data
        bim_data = bim_extractor.extract_bim_from_svg(svg_content, building_id, floor_label)
        
        return {
            'bim_data': bim_data,
            'extraction_summary': {
                'devices_found': len(bim_data.get('devices', [])),
                'rooms_found': len(bim_data.get('rooms', [])),
                'systems_found': len(bim_data.get('systems', {})),
                'relationships_found': len(bim_data.get('relationships', [])),
                'extraction_method': 'symbol_recognition'
            }
        }
        
    except Exception as e:
        logger.error(f"BIM extraction failed: {e}")
        raise HTTPException(status_code=500, detail=f"BIM extraction failed: {str(e)}")

@router.put("/update-symbol-position")
async def update_symbol_position(
    svg_content: str = Form(..., description="SVG content"),
    object_id: str = Form(..., description="Object ID of the symbol to update"),
    x: float = Form(..., description="New X coordinate"),
    y: float = Form(..., description="New Y coordinate")
):
    """
    Update the position of a rendered symbol in the SVG.
    """
    try:
        new_position = {'x': x, 'y': y}
        updated_svg = symbol_renderer.update_symbol_position(svg_content, object_id, new_position)
        
        return {
            'svg': updated_svg,
            'object_id': object_id,
            'new_position': new_position,
            'updated_at': 'now'
        }
        
    except Exception as e:
        logger.error(f"Failed to update symbol position: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update symbol position: {str(e)}")

@router.delete("/remove-symbol")
async def remove_symbol(
    svg_content: str = Form(..., description="SVG content"),
    object_id: str = Form(..., description="Object ID of the symbol to remove")
):
    """
    Remove a rendered symbol from the SVG.
    """
    try:
        updated_svg = symbol_renderer.remove_symbol(svg_content, object_id)
        
        return {
            'svg': updated_svg,
            'object_id': object_id,
            'removed_at': 'now'
        }
        
    except Exception as e:
        logger.error(f"Failed to remove symbol: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to remove symbol: {str(e)}")

@router.post("/parse", response_model=ParseResponse)
def parse_svg(request: ParseRequest):
    summary = read_svg(request.svg_base64)
    if isinstance(summary, dict) and "error" in summary:
        raise HTTPException(status_code=400, detail=summary["error"])
    return {"summary": summary} 