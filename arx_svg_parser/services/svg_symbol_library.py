import os
import json
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path

# Setup basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import the new JSON symbol library
from services.json_symbol_library import JSONSymbolLibrary

# Initialize the JSON symbol library
_json_library = None

def _get_json_library() -> JSONSymbolLibrary:
    """Get or create the JSON symbol library instance."""
    global _json_library
    if _json_library is None:
        _json_library = JSONSymbolLibrary()
    return _json_library

def load_symbol_library(search=None, category=None):
    """
    Load symbol library using the new JSON implementation.
    
    This function maintains backward compatibility with the old YAML-based
    system while using the new JSON symbol library under the hood.
    
    Args:
        search (Optional[str]): Search query to filter symbols
        category (Optional[str]): Category to filter symbols (maps to system)
        
    Returns:
        List[Dict]: List of symbol data dictionaries
    """
    try:
        library = _get_json_library()
        
        # Load symbols based on category (system) filter
        if category:
            symbols_dict = library.load_symbols_by_system(category)
        else:
            symbols_dict = library.load_all_symbols()
        
        # Convert to list format for backward compatibility
        symbols = []
        for symbol_id, symbol_data in symbols_dict.items():
            # Transform to match old format
            transformed_symbol = {
                'symbol_id': symbol_id,
                'name': symbol_data.get('name', ''),
                'system': symbol_data.get('system', ''),
                'category': symbol_data.get('category', ''),
                'description': symbol_data.get('description', ''),
                'svg': symbol_data.get('svg', {}).get('content', ''),
                'properties': symbol_data.get('properties', {}),
                'connections': symbol_data.get('connections', []),
                'tags': symbol_data.get('tags', []),
                'metadata': symbol_data.get('metadata', {})
            }
            symbols.append(transformed_symbol)
        
        # Apply search filter if provided
        if search:
            search = search.lower()
            symbols = [s for s in symbols if 
                      search in s.get('name', '').lower() or 
                      search in s.get('symbol_id', '').lower() or
                      search in s.get('description', '').lower()]
        
        logger.info(f"Loaded {len(symbols)} symbols from JSON library")
        return symbols
        
    except Exception as e:
        logger.error(f"Error loading symbol library: {e}")
        # Fallback to empty list
        return []

# Symbol data is now loaded from JSON files via JSONSymbolLibrary for backward compatibility.

def read_svg(svg_base64):
    """
    Read and parse SVG from base64 encoded string.
    
    Args:
        svg_base64 (str): Base64 encoded SVG string
        
    Returns:
        Dict: Summary of SVG elements or error information
    """
    try:
        import base64
        from lxml import etree as ET
        
        svg_bytes = base64.b64decode(svg_base64)
        svg_str = svg_bytes.decode('utf-8')
        root = ET.fromstring(svg_str.encode('utf-8'))
        
        # Count common SVG elements (using localname for namespace-agnostic search)
        tags = ['rect', 'circle', 'ellipse', 'line', 'polyline', 'polygon', 'path', 'text', 'g']
        summary = {tag: 0 for tag in tags}
        for elem in root.iter():
            tag = ET.QName(elem).localname
            if tag in summary:
                summary[tag] += 1

        summary['total_elements'] = sum(summary.values())
        logger.info("SVG successfully decoded and parsed.")
        return summary
        
    except Exception as e:
        logger.error(f"Failed to decode or parse SVG: {str(e)}")
        return {"error": f"Failed to decode or parse SVG: {str(e)}"}