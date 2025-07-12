"""
Symbol Generator API Router
Handles automated symbol generation from URLs
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, HttpUrl
from typing import Dict, Optional
import json
from datetime import datetime

from services.symbol_generator import SymbolGenerator
from utils.auth import get_current_user

router = APIRouter(prefix="/api/v1/symbol-generator", tags=["Symbol Generator"])

class SymbolGenerationRequest(BaseModel):
    url: HttpUrl
    custom_name: Optional[str] = None
    category: Optional[str] = None
    subcategory: Optional[str] = None

class SymbolGenerationResponse(BaseModel):
    success: bool
    symbol_data: Optional[Dict] = None
    svg_preview: Optional[str] = None
    product_data: Optional[Dict] = None
    error: Optional[str] = None

class SymbolSaveRequest(BaseModel):
    symbol_id: str
    json_content: str
    custom_name: Optional[str] = None

@router.post("/generate", response_model=SymbolGenerationResponse)
async def generate_symbol_from_url(
    request: SymbolGenerationRequest,
    current_user: Dict = Depends(get_current_user)
):
    """
    Generate a symbol from a product URL
    
    Args:
        request: Symbol generation request with URL
        current_user: Current authenticated user
        
    Returns:
        Generated symbol data and YAML content
    """
    try:
        generator = SymbolGenerator()
        
        # Generate symbol from URL
        result = generator.generate_symbol_from_url(
            url=str(request.url),
            user_id=current_user["user_id"]
        )
        
        if not result['success']:
            raise HTTPException(status_code=400, detail=result['error'])
        
        # Apply custom overrides if provided
        if request.custom_name:
            result['symbol_data']['display_name'] = request.custom_name
        
        if request.category:
            result['symbol_data']['category'] = request.category
            
        if request.subcategory:
            result['symbol_data']['subcategory'] = request.subcategory
        
        return SymbolGenerationResponse(**result)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating symbol: {str(e)}")

@router.post("/save")
async def save_generated_symbol(
    request: SymbolSaveRequest,
    current_user: Dict = Depends(get_current_user)
):
    """
    Save a generated symbol to the symbol library
    
    Args:
        request: Symbol save request
        current_user: Current authenticated user
        
    Returns:
        Success status and symbol file path
    """
    try:
        generator = SymbolGenerator()
        
        # Save symbol to library
        success = generator.save_symbol(
            json_content=request.json_content,
            symbol_id=request.symbol_id
        )
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to save symbol")
        
        return {
            "success": True,
            "message": f"Symbol {request.symbol_id} saved successfully",
            "symbol_file": f"{request.symbol_id}.json"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving symbol: {str(e)}")

@router.get("/supported-domains")
async def get_supported_domains():
    """
    Get list of supported manufacturer domains
    
    Returns:
        List of supported domains for symbol generation
    """
    generator = SymbolGenerator()
    return {
        "supported_domains": list(generator.supported_domains.keys()),
        "total_count": len(generator.supported_domains)
    }

@router.get("/system-categories")
async def get_system_categories():
    """
    Get available system categories and keywords
    
    Returns:
        System categories and their associated keywords
    """
    generator = SymbolGenerator()
    return {
        "system_categories": generator.system_keywords,
        "total_categories": len(generator.system_keywords)
    }

@router.post("/preview")
async def preview_symbol_generation(
    request: SymbolGenerationRequest,
    current_user: Dict = Depends(get_current_user)
):
    """
    Preview symbol generation without saving
    
    Args:
        request: Symbol generation request
        current_user: Current authenticated user
        
    Returns:
        Preview of generated symbol data
    """
    try:
        generator = SymbolGenerator()
        
        # Generate symbol preview
        result = generator.generate_symbol_from_url(
            url=str(request.url),
            user_id=current_user["user_id"]
        )
        
        if not result['success']:
            raise HTTPException(status_code=400, detail=result['error'])
        
        # Return preview data
        return {
            "success": True,
            "preview": {
                "symbol_id": result['symbol_data']['symbol_id'],
                "display_name": result['symbol_data']['display_name'],
                "system": result['symbol_data']['system'],
                "category": result['symbol_data']['category'],
                "subcategory": result['symbol_data']['subcategory'],
                "manufacturer": result['symbol_data']['manufacturer'],
                "model_number": result['symbol_data']['model_number'],
                "svg_preview": result['svg_preview'],
                "description": result['symbol_data']['description'][:200] + "..." if len(result['symbol_data']['description']) > 200 else result['symbol_data']['description']
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating preview: {str(e)}") 