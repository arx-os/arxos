"""
Symbol Manager Service

This module provides CRUD (Create, Read, Update, Delete) operations for symbols
in the JSON symbol library. It handles symbol creation, validation, file management,
and integration with the JSONSymbolLibrary.

Author: Arxos Development Team
Date: 2024
"""

import os
import json
import logging
import uuid
import re
from typing import Dict, List, Optional, Any, Union
from pathlib import Path
from datetime import datetime
import shutil
import importlib

from services.json_symbol_library import JSONSymbolLibrary
from services.symbol_schema_validator import SymbolSchemaValidator

# Try to import jsonschema for advanced validation
if importlib.util.find_spec('jsonschema'):
    from jsonschema import validate as jsonschema_validate, ValidationError as JsonSchemaValidationError
    _use_jsonschema = True
else:
    _use_jsonschema = False

# Setup logging
logger = logging.getLogger(__name__)


class SymbolManager:
    """
    Symbol Manager for CRUD operations on JSON symbols.
    
    This class provides comprehensive symbol management functionality including
    creation, validation, file management, and integration with the symbol library.
    """
    
    def __init__(self, library_path: Optional[str] = None):
        """
        Initialize the Symbol Manager.
        
        Args:
            library_path (Optional[str]): Path to the symbol library. 
                                        Defaults to the standard library path.
        """
        self.library = JSONSymbolLibrary(library_path)
        self.library_path = Path(self.library.library_path)
        self.symbols_dir = self.library_path / "symbols"
        
        # Initialize schema validator
        self.schema_validator = SymbolSchemaValidator()
        
        # Ensure symbols directory exists
        self.symbols_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Initialized Symbol Manager at: {self.library_path}")
    
    def create_symbol(self, symbol_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new symbol with validation and file management.
        
        Args:
            symbol_data (Dict[str, Any]): Symbol data to create
            
        Returns:
            Dict[str, Any]: Created symbol data with generated ID and file path
            
        Raises:
            ValueError: If symbol data is invalid
            FileExistsError: If symbol with same ID already exists
        """
        # Validate symbol data
        if not self._validate_symbol_data(symbol_data):
            raise ValueError("Invalid symbol data provided")
        
        # Generate symbol ID if not provided
        if "id" not in symbol_data or not symbol_data["id"]:
            symbol_data["id"] = self._generate_symbol_id(symbol_data)
        
        symbol_id = symbol_data["id"]
        
        # Check if symbol already exists
        if self._symbol_exists(symbol_id):
            raise FileExistsError(f"Symbol with ID '{symbol_id}' already exists")
        
        # Determine file path
        file_path = self._determine_symbol_file_path(symbol_data)
        
        # Ensure system directory exists
        system_dir = file_path.parent
        system_dir.mkdir(parents=True, exist_ok=True)
        
        # Add metadata
        symbol_data = self._add_creation_metadata(symbol_data)
        
        # Write symbol file
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(symbol_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Created symbol '{symbol_id}' at {file_path}")
            
            # Clear library cache to reflect changes
            self.library.clear_cache()
            
            return symbol_data
            
        except Exception as e:
            logger.error(f"Failed to create symbol '{symbol_id}': {e}")
            raise
    
    def _validate_symbol_data(self, symbol_data: Dict[str, Any]) -> bool:
        """
        Validate symbol data against JSON schema.
        
        Args:
            symbol_data (Dict[str, Any]): Symbol data to validate
            
        Returns:
            bool: True if valid, False otherwise
        """
        try:
            is_valid, errors = self.schema_validator.validate_symbol(symbol_data)
            
            if not is_valid:
                for error in errors:
                    logger.error(f"Validation error: {error['field_path']} - {error['message']}")
            
            return is_valid
            
        except Exception as e:
            logger.error(f"Validation failed with exception: {e}")
            return False
    
    def _generate_symbol_id(self, symbol_data: Dict[str, Any]) -> str:
        """
        Generate a unique symbol ID based on symbol data.
        
        Args:
            symbol_data (Dict[str, Any]): Symbol data to generate ID for
            
        Returns:
            str: Generated symbol ID
        """
        # Use name as base for ID
        name = symbol_data.get("name", "").strip()
        if not name:
            # Fallback to system + timestamp
            system = symbol_data.get("system", "unknown")
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            base_id = f"{system}_{timestamp}"
        else:
            # Convert name to ID format
            base_id = self._normalize_name_to_id(name)
        
        # Ensure uniqueness
        counter = 1
        symbol_id = base_id
        while self._symbol_exists(symbol_id):
            symbol_id = f"{base_id}_{counter}"
            counter += 1
        
        logger.debug(f"Generated symbol ID: {symbol_id}")
        return symbol_id
    
    def _normalize_name_to_id(self, name: str) -> str:
        """
        Normalize a symbol name to a valid ID format.
        
        Args:
            name (str): Symbol name to normalize
            
        Returns:
            str: Normalized ID
        """
        # Convert to lowercase
        normalized = name.lower()
        
        # Replace spaces and special characters with underscores
        normalized = re.sub(r'[^a-z0-9]+', '_', normalized)
        
        # Remove leading/trailing underscores
        normalized = normalized.strip('_')
        
        # Ensure it starts with a letter
        if normalized and not normalized[0].isalpha():
            normalized = f"symbol_{normalized}"
        
        # Limit length
        if len(normalized) > 50:
            normalized = normalized[:50]
        
        return normalized
    
    def _determine_symbol_file_path(self, symbol_data: Dict[str, Any]) -> Path:
        """
        Determine the file path for a symbol based on its system.
        
        Args:
            symbol_data (Dict[str, Any]): Symbol data
            
        Returns:
            Path: File path for the symbol
        """
        system = symbol_data["system"].lower()
        symbol_id = symbol_data["id"]
        
        # Create system directory path
        system_dir = self.symbols_dir / system
        
        # Create file path
        file_path = system_dir / f"{symbol_id}.json"
        
        return file_path
    
    def _is_valid_system(self, system: str) -> bool:
        """
        Check if a system is valid.
        
        Args:
            system (str): System name to validate
            
        Returns:
            bool: True if valid, False otherwise
        """
        if not system or not isinstance(system, str):
            return False
        
        # Get known systems from library
        known_systems = self.library._get_known_systems()
        
        return system.lower() in [s.lower() for s in known_systems]
    
    def _symbol_exists(self, symbol_id: str) -> bool:
        """
        Check if a symbol with the given ID already exists.
        
        Args:
            symbol_id (str): Symbol ID to check
            
        Returns:
            bool: True if exists, False otherwise
        """
        # Check if symbol exists in library
        existing_symbol = self.library.get_symbol(symbol_id)
        return existing_symbol is not None
    
    def _add_creation_metadata(self, symbol_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Add creation metadata to symbol data.
        
        Args:
            symbol_data (Dict[str, Any]): Original symbol data
            
        Returns:
            Dict[str, Any]: Symbol data with added metadata
        """
        # Create a copy to avoid modifying original
        symbol_data = symbol_data.copy()
        
        # Add creation timestamp
        symbol_data["created_at"] = datetime.now().isoformat()
        
        # Add version
        symbol_data["version"] = "1.0"
        
        # Add metadata section if not present
        if "metadata" not in symbol_data:
            symbol_data["metadata"] = {}
        
        symbol_data["metadata"]["created_by"] = "symbol_manager"
        symbol_data["metadata"]["created_date"] = datetime.now().isoformat()
        
        return symbol_data
    
    def get_symbol(self, symbol_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a symbol by ID.
        
        Args:
            symbol_id (str): Symbol ID to retrieve
            
        Returns:
            Optional[Dict[str, Any]]: Symbol data or None if not found
        """
        return self.library.get_symbol(symbol_id)
    
    def update_symbol(self, symbol_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Update an existing symbol.
        
        Args:
            symbol_id (str): Symbol ID to update
            updates (Dict[str, Any]): Updates to apply
            
        Returns:
            Optional[Dict[str, Any]]: Updated symbol data or None if not found
        """
        # Get existing symbol
        existing_symbol = self.get_symbol(symbol_id)
        if not existing_symbol:
            logger.warning(f"Symbol '{symbol_id}' not found for update")
            return None
        
        # Merge updates with existing data
        updated_symbol = existing_symbol.copy()
        updated_symbol.update(updates)
        
        # Validate updated symbol
        if not self._validate_symbol_data(updated_symbol):
            raise ValueError("Updated symbol data is invalid")
        
        # Determine file path
        file_path = self._determine_symbol_file_path(updated_symbol)
        
        # Add update metadata
        updated_symbol = self._add_update_metadata(updated_symbol)
        
        # Write updated symbol
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(updated_symbol, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Updated symbol '{symbol_id}'")
            
            # Clear library cache
            self.library.clear_cache()
            
            return updated_symbol
            
        except Exception as e:
            logger.error(f"Failed to update symbol '{symbol_id}': {e}")
            raise
    
    def _add_update_metadata(self, symbol_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Add update metadata to symbol data.
        
        Args:
            symbol_data (Dict[str, Any]): Symbol data to update
            
        Returns:
            Dict[str, Any]: Symbol data with update metadata
        """
        symbol_data = symbol_data.copy()
        
        # Add update timestamp
        symbol_data["updated_at"] = datetime.now().isoformat()
        
        # Update version
        if "version" in symbol_data:
            try:
                major, minor = symbol_data["version"].split(".")
                symbol_data["version"] = f"{major}.{int(minor) + 1}"
            except:
                symbol_data["version"] = "1.1"
        else:
            symbol_data["version"] = "1.1"
        
        # Update metadata
        if "metadata" not in symbol_data:
            symbol_data["metadata"] = {}
        
        symbol_data["metadata"]["updated_by"] = "symbol_manager"
        symbol_data["metadata"]["updated_date"] = datetime.now().isoformat()
        
        return symbol_data
    
    def delete_symbol(self, symbol_id: str) -> bool:
        """
        Delete a symbol by ID.
        
        Args:
            symbol_id (str): Symbol ID to delete
            
        Returns:
            bool: True if deleted, False if not found
        """
        # Get symbol to determine file path
        symbol_data = self.get_symbol(symbol_id)
        if not symbol_data:
            logger.warning(f"Symbol '{symbol_id}' not found for deletion")
            return False
        
        # Determine file path
        file_path = self._determine_symbol_file_path(symbol_data)
        
        try:
            # Delete the file
            if file_path.exists():
                file_path.unlink()
                logger.info(f"Deleted symbol '{symbol_id}' at {file_path}")
                
                # Clear library cache
                self.library.clear_cache()
                
                return True
            else:
                logger.warning(f"Symbol file not found: {file_path}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to delete symbol '{symbol_id}': {e}")
            return False
    
    def list_symbols(self, system: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List all symbols or symbols for a specific system.
        
        Args:
            system (Optional[str]): System to filter by
            
        Returns:
            List[Dict[str, Any]]: List of symbol data
        """
        if system:
            symbols = self.library.load_symbols_by_system(system)
        else:
            symbols = self.library.load_all_symbols()
        
        return list(symbols.values())
    
    def search_symbols(self, query: str, system: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Search for symbols.
        
        Args:
            query (str): Search query
            system (Optional[str]): System to filter by
            
        Returns:
            List[Dict[str, Any]]: List of matching symbols
        """
        return self.library.search_symbols(query, system=system)
    
    def get_symbol_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about symbols in the library.
        
        Returns:
            Dict[str, Any]: Symbol statistics
        """
        all_symbols = self.library.load_all_symbols()
        
        stats = {
            "total_symbols": len(all_symbols),
            "systems": {},
            "recent_symbols": [],
            "symbol_sizes": {}
        }
        
        # Count by system
        for symbol_id, symbol_data in all_symbols.items():
            system = symbol_data.get("system", "unknown")
            if system not in stats["systems"]:
                stats["systems"][system] = 0
            stats["systems"][system] += 1
        
        # Get recent symbols (last 10 created)
        symbols_with_dates = []
        for symbol_id, symbol_data in all_symbols.items():
            created_at = symbol_data.get("created_at")
            if created_at:
                symbols_with_dates.append((created_at, symbol_data))
        
        symbols_with_dates.sort(key=lambda x: x[0], reverse=True)
        stats["recent_symbols"] = [s[1] for s in symbols_with_dates[:10]]
        
        # Calculate symbol sizes
        for symbol_id, symbol_data in all_symbols.items():
            svg_content = symbol_data.get("svg", {}).get("content", "")
            stats["symbol_sizes"][symbol_id] = len(svg_content)
        
        return stats 

    def advanced_validate_symbol(self, symbol_data: Dict[str, Any]) -> bool:
        """
        Advanced validation for symbol data using JSON Schema if available.
        Args:
            symbol_data (Dict[str, Any]): Symbol data to validate
        Returns:
            bool: True if valid, False otherwise
        """
        schema = {
            "type": "object",
            "required": ["name", "system", "svg"],
            "properties": {
                "id": {"type": "string"},
                "name": {"type": "string", "minLength": 1},
                "system": {"type": "string", "minLength": 1},
                "category": {"type": "string"},
                "svg": {
                    "type": "object",
                    "required": ["content"],
                    "properties": {
                        "content": {"type": "string", "minLength": 1},
                        "width": {"type": "number"},
                        "height": {"type": "number"},
                        "scale": {"type": "number"}
                    }
                },
                "properties": {"type": "object"},
                "connections": {"type": "array"},
                "tags": {"type": "array", "items": {"type": "string"}},
                "metadata": {"type": "object"}
            }
        }
        if _use_jsonschema:
            try:
                jsonschema_validate(instance=symbol_data, schema=schema)
                return True
            except JsonSchemaValidationError as e:
                logger.error(f"JSON Schema validation error: {e}")
                return False
        else:
            # Fallback to manual validation
            return self._validate_symbol_data(symbol_data)

    def bulk_create_symbols(self, symbols: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Bulk create symbols with comprehensive validation.
        
        Args:
            symbols (List[Dict[str, Any]]): List of symbol data dicts
            
        Returns:
            List[Dict[str, Any]]: List of created symbol data
        """
        created = []
        validation_errors = []
        
        for i, symbol in enumerate(symbols):
            try:
                # Validate symbol using comprehensive schema validation
                is_valid, errors = self.schema_validator.validate_symbol(symbol)
                
                if not is_valid:
                    error_msg = f"Symbol {i+1} validation failed: {errors}"
                    logger.error(error_msg)
                    validation_errors.append({
                        "index": i,
                        "symbol_name": symbol.get("name", "unknown"),
                        "errors": errors
                    })
                    continue
                
                created_symbol = self.create_symbol(symbol)
                created.append(created_symbol)
                
            except Exception as e:
                error_msg = f"Bulk create failed for symbol {i+1} ({symbol.get('name', 'unknown')}): {e}"
                logger.error(error_msg)
                validation_errors.append({
                    "index": i,
                    "symbol_name": symbol.get("name", "unknown"),
                    "error": str(e)
                })
        
        if validation_errors:
            logger.warning(f"Bulk create completed with {len(validation_errors)} validation errors")
        
        return created

    def bulk_update_symbols(self, updates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Bulk update symbols with comprehensive validation.
        
        Args:
            updates (List[Dict[str, Any]]): List of update dicts
            
        Returns:
            List[Dict[str, Any]]: List of updated symbol data
        """
        updated = []
        validation_errors = []
        
        for i, update in enumerate(updates):
            symbol_id = update.get('id')
            if not symbol_id:
                error_msg = f"Bulk update: Missing symbol ID in update {i+1}"
                logger.error(error_msg)
                validation_errors.append({
                    "index": i,
                    "error": "Missing symbol ID"
                })
                continue
            
            try:
                # Get existing symbol to merge with updates
                existing_symbol = self.get_symbol(symbol_id)
                if not existing_symbol:
                    error_msg = f"Bulk update: Symbol '{symbol_id}' not found"
                    logger.error(error_msg)
                    validation_errors.append({
                        "index": i,
                        "symbol_id": symbol_id,
                        "error": "Symbol not found"
                    })
                    continue
                
                # Merge updates with existing data
                merged_symbol = existing_symbol.copy()
                merged_symbol.update(update)
                
                # Validate merged symbol using comprehensive schema validation
                is_valid, errors = self.schema_validator.validate_symbol(merged_symbol)
                
                if not is_valid:
                    error_msg = f"Bulk update: Symbol '{symbol_id}' validation failed: {errors}"
                    logger.error(error_msg)
                    validation_errors.append({
                        "index": i,
                        "symbol_id": symbol_id,
                        "errors": errors
                    })
                    continue
                
                result = self.update_symbol(symbol_id, update)
                if result:
                    updated.append(result)
                    
            except Exception as e:
                error_msg = f"Bulk update failed for symbol ID {symbol_id}: {e}"
                logger.error(error_msg)
                validation_errors.append({
                    "index": i,
                    "symbol_id": symbol_id,
                    "error": str(e)
                })
        
        if validation_errors:
            logger.warning(f"Bulk update completed with {len(validation_errors)} validation errors")
        
        return updated

    def bulk_delete_symbols(self, symbol_ids: List[str]) -> Dict[str, bool]:
        """
        Bulk delete symbols by ID.
        Args:
            symbol_ids (List[str]): List of symbol IDs to delete
        Returns:
            Dict[str, bool]: Dict of symbol_id -> deletion success
        """
        results = {}
        for symbol_id in symbol_ids:
            try:
                results[symbol_id] = self.delete_symbol(symbol_id)
            except Exception as e:
                logger.error(f"Bulk delete failed for symbol ID {symbol_id}: {e}")
                results[symbol_id] = False
        return results
    
    def validate_symbol_with_details(self, symbol_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate symbol data and return detailed validation results.
        
        Args:
            symbol_data (Dict[str, Any]): Symbol data to validate
            
        Returns:
            Dict[str, Any]: Validation results with details
        """
        try:
            is_valid, errors = self.schema_validator.validate_symbol(symbol_data)
            
            return {
                "is_valid": is_valid,
                "errors": errors,
                "symbol_name": symbol_data.get("name", "unknown"),
                "symbol_id": symbol_data.get("id", "unknown")
            }
            
        except Exception as e:
            return {
                "is_valid": False,
                "errors": [{"field_path": "validation", "message": f"Validation exception: {str(e)}"}],
                "symbol_name": symbol_data.get("name", "unknown"),
                "symbol_id": symbol_data.get("id", "unknown")
            }
    
    def validate_batch_with_details(self, symbols: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Validate a batch of symbols and return detailed validation results.
        
        Args:
            symbols (List[Dict[str, Any]]): List of symbol data to validate
            
        Returns:
            Dict[str, Any]: Batch validation results with details
        """
        results = {
            "total_symbols": len(symbols),
            "valid_symbols": 0,
            "invalid_symbols": 0,
            "validation_details": []
        }
        
        for i, symbol in enumerate(symbols):
            validation_result = self.validate_symbol_with_details(symbol)
            validation_result["index"] = i
            
            if validation_result["is_valid"]:
                results["valid_symbols"] += 1
            else:
                results["invalid_symbols"] += 1
            
            results["validation_details"].append(validation_result)
        
        return results 