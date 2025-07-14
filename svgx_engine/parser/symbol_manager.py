"""
SVGX Symbol Manager for managing symbol libraries and references.
"""

import logging
from typing import Dict, Any, List, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class SVGXSymbolManager:
    """Manages SVGX symbols and symbol libraries."""
    
    def __init__(self):
        self.symbols = {}
        self.libraries = {}
    
    def load_symbol(self, symbol_id: str, symbol_content: str):
        """Load a symbol from content."""
        try:
            from .parser import SVGXParser
            parser = SVGXParser()
            elements = parser.parse(symbol_content)
            
            self.symbols[symbol_id] = {
                'content': symbol_content,
                'elements': elements
            }
            
            logger.info(f"Loaded symbol {symbol_id}")
            
        except Exception as e:
            logger.error(f"Failed to load symbol {symbol_id}: {e}")
    
    def get_symbol(self, symbol_id: str) -> Optional[Dict[str, Any]]:
        """Get a symbol by ID."""
        return self.symbols.get(symbol_id)
    
    def list_symbols(self) -> List[str]:
        """List all available symbols."""
        return list(self.symbols.keys()) 