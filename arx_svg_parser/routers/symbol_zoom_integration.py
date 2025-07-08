"""
FastAPI Router for Symbol Library Zoom Integration

This router provides REST API endpoints for testing and managing
symbol library integration with zoom systems.
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from fastapi.responses import HTMLResponse, JSONResponse
from typing import List, Dict, Any, Optional
import logging
from pathlib import Path

# Add the parent directory to the path
import sys
sys.path.append(str(Path(__file__).parent.parent))

from services.symbol_zoom_integration import SymbolZoomIntegration

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/symbol-zoom", tags=["Symbol Zoom Integration"])

# Global integration service instance
_zoom_integration: Optional[SymbolZoomIntegration] = None


def get_zoom_integration() -> SymbolZoomIntegration:
    """Get or create the zoom integration service instance."""
    global _zoom_integration
    if _zoom_integration is None:
        _zoom_integration = SymbolZoomIntegration()
    return _zoom_integration


@router.get("/symbols", response_model=Dict[str, Any])
async def list_symbols(
    integration: SymbolZoomIntegration = Depends(get_zoom_integration)
):
    """
    List all available symbols in the library.
    
    Returns:
        Dictionary containing symbol information
    """
    try:
        symbols = integration.load_symbol_library()
        
        symbol_list = []
        for symbol_id, symbol_data in symbols.items():
            symbol_info = {
                "id": symbol_id,
                "system": symbol_data.get("system", "unknown"),
                "display_name": symbol_data.get("display_name", symbol_id),
                "category": symbol_data.get("category", "unknown"),
                "has_dimensions": "dimensions" in symbol_data,
                "has_svg": "svg" in symbol_data,
                "default_scale": symbol_data.get("default_scale", 1.0)
            }
            symbol_list.append(symbol_info)
        
        return {
            "total_symbols": len(symbols),
            "symbols": symbol_list
        }
    except Exception as e:
        logger.error(f"Error listing symbols: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list symbols: {str(e)}")


@router.get("/symbols/{symbol_id}/scaling", response_model=Dict[str, Any])
async def test_symbol_scaling(
    symbol_id: str,
    zoom_levels: List[float] = Query([0.25, 0.5, 1.0, 2.0, 4.0], description="Zoom levels to test"),
    integration: SymbolZoomIntegration = Depends(get_zoom_integration)
):
    """
    Test symbol scaling at different zoom levels.
    
    Args:
        symbol_id: ID of the symbol to test
        zoom_levels: List of zoom levels to test
        
    Returns:
        Scaling test results
    """
    try:
        scale_data = integration.validate_symbol_consistency(symbol_id, zoom_levels)
        
        if not scale_data:
            raise HTTPException(status_code=404, detail=f"Symbol '{symbol_id}' not found")
        
        # Convert dataclass objects to dictionaries
        scale_results = []
        consistent_count = 0
        
        for data in scale_data:
            scale_result = {
                "zoom_level": data.zoom_level,
                "scale_factor": data.current_scale,
                "actual_width": data.actual_width,
                "actual_height": data.actual_height,
                "is_consistent": data.is_consistent
            }
            scale_results.append(scale_result)
            if data.is_consistent:
                consistent_count += 1
        
        return {
            "symbol_id": symbol_id,
            "total_tests": len(scale_data),
            "consistent_tests": consistent_count,
            "consistency_percentage": (consistent_count / len(scale_data)) * 100,
            "scale_data": scale_results
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error testing symbol scaling for {symbol_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to test symbol scaling: {str(e)}")


@router.get("/symbols/{symbol_id}/placement", response_model=Dict[str, Any])
async def test_symbol_placement(
    symbol_id: str,
    integration: SymbolZoomIntegration = Depends(get_zoom_integration)
):
    """
    Test symbol placement at various positions and zoom levels.
    
    Args:
        symbol_id: ID of the symbol to test
        
    Returns:
        Placement test results
    """
    try:
        # Test positions in a grid pattern
        test_positions = [
            (100, 100), (200, 100), (300, 100),
            (100, 200), (200, 200), (300, 200),
            (100, 300), (200, 300), (300, 300)
        ]
        zoom_levels = [0.5, 1.0, 2.0]
        
        results = integration.test_symbol_placement(symbol_id, test_positions, zoom_levels)
        
        if "error" in results:
            raise HTTPException(status_code=404, detail=results["error"])
        
        return results
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error testing symbol placement for {symbol_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to test symbol placement: {str(e)}")


@router.get("/symbols/{symbol_id}/fix", response_model=Dict[str, Any])
async def fix_symbol_issues(
    symbol_id: str,
    integration: SymbolZoomIntegration = Depends(get_zoom_integration)
):
    """
    Fix scaling issues for a symbol.
    
    Args:
        symbol_id: ID of the symbol to fix
        
    Returns:
        Fix results
    """
    try:
        results = integration.fix_symbol_scaling_issues(symbol_id)
        
        if "error" in results:
            raise HTTPException(status_code=404, detail=results["error"])
        
        return results
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fixing symbol issues for {symbol_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fix symbol issues: {str(e)}")


@router.get("/validate", response_model=Dict[str, Any])
async def validate_library(
    integration: SymbolZoomIntegration = Depends(get_zoom_integration)
):
    """
    Validate the entire symbol library for zoom system compatibility.
    
    Returns:
        Library validation results
    """
    try:
        results = integration.validate_symbol_library()
        return results
    except Exception as e:
        logger.error(f"Error validating symbol library: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to validate library: {str(e)}")


@router.get("/report", response_class=HTMLResponse)
async def generate_report(
    integration: SymbolZoomIntegration = Depends(get_zoom_integration)
):
    """
    Generate a comprehensive test report for zoom system integration.
    
    Returns:
        HTML report
    """
    try:
        report = integration.generate_zoom_test_report()
        return HTMLResponse(content=report)
    except Exception as e:
        logger.error(f"Error generating report: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate report: {str(e)}")


@router.post("/comprehensive-test", response_model=Dict[str, Any])
async def run_comprehensive_test(
    symbol_ids: Optional[List[str]] = None,
    integration: SymbolZoomIntegration = Depends(get_zoom_integration)
):
    """
    Run comprehensive tests on specified symbols or all symbols.
    
    Args:
        symbol_ids: List of symbol IDs to test (if None, tests all symbols)
        
    Returns:
        Comprehensive test results
    """
    try:
        if not symbol_ids:
            symbols = integration.load_symbol_library()
            symbol_ids = list(symbols.keys())
        
        results = {
            "total_symbols": len(symbol_ids),
            "tested_symbols": 0,
            "passed_symbols": 0,
            "failed_symbols": 0,
            "symbol_results": {},
            "library_validation": None,
            "overall_score": 0.0
        }
        
        # Test each symbol
        for symbol_id in symbol_ids:
            try:
                # Test scaling
                zoom_levels = [0.25, 0.5, 1.0, 2.0, 4.0]
                scaling_result = integration.validate_symbol_consistency(symbol_id, zoom_levels)
                
                # Test placement
                test_positions = [(100, 100), (200, 200)]
                placement_zoom_levels = [0.5, 1.0, 2.0]
                placement_result = integration.test_symbol_placement(symbol_id, test_positions, placement_zoom_levels)
                
                # Fix issues
                fix_result = integration.fix_symbol_scaling_issues(symbol_id)
                
                # Determine if symbol passed
                passed = True
                if not scaling_result or "error" in placement_result:
                    passed = False
                elif fix_result.get("issues_found", 0) > 0:
                    passed = False
                
                results["symbol_results"][symbol_id] = {
                    "scaling": {
                        "total_tests": len(scaling_result),
                        "consistent_tests": len([s for s in scaling_result if s.is_consistent]),
                        "consistency_percentage": len([s for s in scaling_result if s.is_consistent]) / len(scaling_result) * 100 if scaling_result else 0
                    },
                    "placement": placement_result,
                    "fixes": fix_result,
                    "passed": passed
                }
                
                results["tested_symbols"] += 1
                if passed:
                    results["passed_symbols"] += 1
                else:
                    results["failed_symbols"] += 1
                    
            except Exception as e:
                logger.error(f"Error testing {symbol_id}: {e}")
                results["symbol_results"][symbol_id] = {"error": str(e), "passed": False}
                results["tested_symbols"] += 1
                results["failed_symbols"] += 1
        
        # Validate entire library
        results["library_validation"] = integration.validate_symbol_library()
        
        # Calculate overall score
        if results["tested_symbols"] > 0:
            results["overall_score"] = (results["passed_symbols"] / results["tested_symbols"]) * 100
        
        return results
    except Exception as e:
        logger.error(f"Error running comprehensive test: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to run comprehensive test: {str(e)}")


@router.get("/zoom-levels", response_model=List[Dict[str, Any]])
async def get_zoom_levels(
    integration: SymbolZoomIntegration = Depends(get_zoom_integration)
):
    """
    Get information about all available zoom levels.
    
    Returns:
        List of zoom level configurations
    """
    try:
        zoom_levels = []
        for zoom in integration.zoom_levels:
            zoom_info = {
                "level": zoom.level,
                "name": zoom.name,
                "min_symbol_size": zoom.min_symbol_size,
                "max_symbol_size": zoom.max_symbol_size,
                "scale_factor": zoom.scale_factor,
                "lod_level": zoom.lod_level
            }
            zoom_levels.append(zoom_info)
        
        return zoom_levels
    except Exception as e:
        logger.error(f"Error getting zoom levels: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get zoom levels: {str(e)}")


@router.post("/scale-symbol", response_model=Dict[str, Any])
async def scale_symbol_svg(
    symbol_id: str,
    scale_factor: float = Query(..., description="Scale factor to apply"),
    zoom_level: float = Query(1.0, description="Current zoom level"),
    integration: SymbolZoomIntegration = Depends(get_zoom_integration)
):
    """
    Scale a symbol's SVG content.
    
    Args:
        symbol_id: ID of the symbol to scale
        scale_factor: Scale factor to apply
        zoom_level: Current zoom level
        
    Returns:
        Scaled SVG content
    """
    try:
        symbols = integration.load_symbol_library()
        
        if symbol_id not in symbols:
            raise HTTPException(status_code=404, detail=f"Symbol '{symbol_id}' not found")
        
        symbol_data = symbols[symbol_id]
        original_svg = symbol_data.get("svg", "")
        
        if not original_svg:
            raise HTTPException(status_code=400, detail="Symbol has no SVG content")
        
        # Calculate optimal scale
        base_scale = symbol_data.get("default_scale", 1.0)
        optimal_scale = integration.calculate_optimal_scale(zoom_level, base_scale)
        
        # Apply scaling
        scaled_svg = integration.scale_symbol_svg(original_svg, scale_factor)
        
        return {
            "symbol_id": symbol_id,
            "original_svg": original_svg,
            "scaled_svg": scaled_svg,
            "applied_scale": scale_factor,
            "optimal_scale": optimal_scale,
            "zoom_level": zoom_level,
            "base_scale": base_scale
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error scaling symbol {symbol_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to scale symbol: {str(e)}")


@router.get("/health", response_model=Dict[str, Any])
async def health_check(
    integration: SymbolZoomIntegration = Depends(get_zoom_integration)
):
    """
    Health check endpoint for the zoom integration service.
    
    Returns:
        Service health status
    """
    try:
        symbols = integration.load_symbol_library()
        
        return {
            "status": "healthy",
            "service": "symbol_zoom_integration",
            "symbols_loaded": len(symbols),
            "zoom_levels_configured": len(integration.zoom_levels),
            "cache_size": len(integration.scale_cache),
            "consistency_threshold": integration.consistency_threshold
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail=f"Service unhealthy: {str(e)}") 