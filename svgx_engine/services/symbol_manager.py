"""
Symbol Manager Service for Arxos SVGX Engine

Handles symbol validation, creation, and management for the pipeline integration.
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
import logging

from svgx_engine.utils.errors import SymbolError, ValidationError

logger = logging.getLogger(__name__)


class SymbolManager:
    """Manages SVGX symbols for the pipeline integration."""
    
    def __init__(self, symbol_library_path: str = "arx-symbol-library"):
        self.symbol_library_path = Path(symbol_library_path)
        self.symbol_index_file = self.symbol_library_path / "symbol_index.json"
        
    def validate_symbol(self, symbol_name: str) -> Dict[str, Any]:
        """Validate a symbol by name."""
        try:
            # Find the symbol file
            symbol_file = self._find_symbol_file(symbol_name)
            if not symbol_file:
                raise SymbolError(f"Symbol not found: {symbol_name}", symbol_name)
            
            # Load and validate the symbol
            with open(symbol_file, 'r') as f:
                symbol_data = json.load(f)
            
            # Basic validation
            validation_result = self._validate_symbol_structure(symbol_data)
            
            return {
                "symbol_name": symbol_name,
                "symbol_file": str(symbol_file),
                "validation_passed": validation_result["valid"],
                "validation_details": validation_result
            }
            
        except Exception as e:
            if isinstance(e, SymbolError):
                raise e
            raise SymbolError(f"Symbol validation failed: {str(e)}", symbol_name)
    
    def create_symbol(self, system: str, symbol_name: str) -> Path:
        """Create a new symbol for a system."""
        try:
            # Create system directory if it doesn't exist
            system_dir = self.symbol_library_path / system
            system_dir.mkdir(parents=True, exist_ok=True)
            
            # Create metadata directory
            metadata_dir = system_dir / "metadata"
            metadata_dir.mkdir(exist_ok=True)
            
            # Create symbol file
            symbol_file = system_dir / f"{symbol_name}.svgx"
            
            # Create basic SVGX content
            svgx_content = self._create_basic_svgx(system, symbol_name)
            
            with open(symbol_file, 'w') as f:
                f.write(svgx_content)
            
            # Create metadata file
            metadata_file = metadata_dir / f"{symbol_name}.json"
            metadata_content = self._create_basic_metadata(system, symbol_name)
            
            with open(metadata_file, 'w') as f:
                json.dump(metadata_content, f, indent=2)
            
            # Update symbol index
            self._update_symbol_index(system, symbol_name, str(symbol_file))
            
            logger.info(f"Created symbol: {symbol_name} for system: {system}")
            return symbol_file
            
        except Exception as e:
            raise SymbolError(f"Failed to create symbol: {str(e)}", symbol_name)
    
    def _find_symbol_file(self, symbol_name: str) -> Optional[Path]:
        """Find a symbol file by name."""
        # Search in all system directories
        for system_dir in self.symbol_library_path.iterdir():
            if system_dir.is_dir():
                symbol_file = system_dir / f"{symbol_name}.svgx"
                if symbol_file.exists():
                    return symbol_file
        
        return None
    
    def _validate_symbol_structure(self, symbol_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate the structure of a symbol."""
        errors = []
        warnings = []
        
        # Check required fields
        required_fields = ["id", "name", "system", "svg"]
        for field in required_fields:
            if field not in symbol_data:
                errors.append(f"Missing required field: {field}")
        
        # Check system field
        if "system" in symbol_data:
            system = symbol_data["system"]
            valid_systems = ["E", "LV", "FA", "N", "M", "P", "S", "AV"]
            if system not in valid_systems:
                warnings.append(f"Unknown system: {system}")
        
        # Check SVG content
        if "svg" in symbol_data:
            svg = symbol_data["svg"]
            if not svg.strip():
                errors.append("SVG content is empty")
            elif not svg.startswith("<svg"):
                warnings.append("SVG content may not be valid")
        
        # Check properties
        if "properties" in symbol_data:
            properties = symbol_data["properties"]
            if not isinstance(properties, dict):
                errors.append("Properties must be a dictionary")
        
        # Check connections
        if "connections" in symbol_data:
            connections = symbol_data["connections"]
            if not isinstance(connections, list):
                errors.append("Connections must be a list")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }
    
    def _create_basic_svgx(self, system: str, symbol_name: str) -> str:
        """Create basic SVGX content for a symbol."""
        return f'''<?xml version="1.0" encoding="UTF-8"?>
<svgx xmlns="http://arxos.com/svgx" version="1.0">
  <metadata>
    <system>{system}</system>
    <object_type>{symbol_name}</object_type>
    <behavior_profile>default</behavior_profile>
  </metadata>
  <svg viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
    <rect x="10" y="10" width="80" height="80" fill="none" stroke="black" stroke-width="2"/>
    <text x="50" y="55" text-anchor="middle" font-family="Arial" font-size="12">{symbol_name}</text>
  </svg>
</svgx>'''
    
    def _create_basic_metadata(self, system: str, symbol_name: str) -> Dict[str, Any]:
        """Create basic metadata for a symbol."""
        return {
            "id": f"{system}_{symbol_name}",
            "name": symbol_name,
            "system": system,
            "category": "default",
            "description": f"Default {symbol_name} for {system} system",
            "properties": {
                "physical": {},
                "electrical": {},
                "mechanical": {},
                "operational": {}
            },
            "connections": [],
            "metadata": {
                "version": "1.0",
                "created_at": __import__("time").time(),
                "created_by": "pipeline"
            }
        }
    
    def _update_symbol_index(self, system: str, symbol_name: str, symbol_path: str):
        """Update the symbol index with a new symbol."""
        try:
            # Load existing index
            if self.symbol_index_file.exists():
                with open(self.symbol_index_file, 'r') as f:
                    index = json.load(f)
            else:
                index = {}
            
            # Add symbol to index
            if system not in index:
                index[system] = {}
            
            index[system][symbol_name] = {
                "path": symbol_path,
                "created_at": __import__("time").time(),
                "status": "active"
            }
            
            # Write updated index
            with open(self.symbol_index_file, 'w') as f:
                json.dump(index, f, indent=2)
                
        except Exception as e:
            logger.warning(f"Failed to update symbol index: {str(e)}")
    
    def list_symbols(self, system: str = None) -> List[Dict[str, Any]]:
        """List all symbols, optionally filtered by system."""
        symbols = []
        
        try:
            if self.symbol_index_file.exists():
                with open(self.symbol_index_file, 'r') as f:
                    index = json.load(f)
                
                for sys_name, sys_symbols in index.items():
                    if system and sys_name != system:
                        continue
                    
                    for symbol_name, symbol_info in sys_symbols.items():
                        symbols.append({
                            "system": sys_name,
                            "name": symbol_name,
                            "path": symbol_info.get("path"),
                            "status": symbol_info.get("status", "unknown"),
                            "created_at": symbol_info.get("created_at")
                        })
        
        except Exception as e:
            logger.error(f"Failed to list symbols: {str(e)}")
        
        return symbols


# Alias for backward compatibility
SVGXSymbolManager = SymbolManager 