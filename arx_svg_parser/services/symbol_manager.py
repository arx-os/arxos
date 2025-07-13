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
import uuid
import re
from typing import Dict, List, Optional, Any, Union
from pathlib import Path
from datetime import datetime
import shutil
import importlib

from structlog import get_logger

from services.json_symbol_library import JSONSymbolLibrary
from services.symbol_schema_validator import SymbolSchemaValidator

# Try to import jsonschema for advanced validation
if importlib.util.find_spec('jsonschema'):
    from jsonschema import validate as jsonschema_validate, ValidationError as JsonSchemaValidationError
    _use_jsonschema = True
else:
    _use_jsonschema = False

# Setup logging
logger = get_logger()


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
        
        logger.info("symbol_manager_initialized",
                   library_path=str(self.library_path),
                   symbols_dir=str(self.symbols_dir))
    
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
        try:
            logger.info("symbol_creation_attempt",
                       symbol_name=symbol_data.get("name"),
                       system=symbol_data.get("system"))
            
            # Validate symbol data
            if not self._validate_symbol_data(symbol_data):
                logger.warning("symbol_creation_failed_validation",
                             symbol_name=symbol_data.get("name"),
                             system=symbol_data.get("system"))
                raise ValueError("Invalid symbol data provided")
            
            # Generate symbol ID if not provided
            if "id" not in symbol_data or not symbol_data["id"]:
                symbol_data["id"] = self._generate_symbol_id(symbol_data)
            
            symbol_id = symbol_data["id"]
            
            # Check if symbol already exists
            if self._symbol_exists(symbol_id):
                logger.warning("symbol_creation_failed_exists",
                             symbol_id=symbol_id,
                             symbol_name=symbol_data.get("name"))
                raise FileExistsError(f"Symbol with ID '{symbol_id}' already exists")
            
            # Determine file path
            file_path = self._determine_symbol_file_path(symbol_data)
            
            # Ensure system directory exists
            system_dir = file_path.parent
            system_dir.mkdir(parents=True, exist_ok=True)
            
            # Add metadata
            symbol_data = self._add_creation_metadata(symbol_data)
            
            # Write symbol file
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(symbol_data, f, indent=2, ensure_ascii=False)
            
            logger.info("symbol_created_successfully",
                       symbol_id=symbol_id,
                       symbol_name=symbol_data.get("name"),
                       system=symbol_data.get("system"),
                       file_path=str(file_path))
            
            # Clear library cache to reflect changes
            self.library.clear_cache()
            
            return symbol_data
            
        except (ValueError, FileExistsError):
            raise
        except Exception as e:
            logger.error("symbol_creation_failed",
                        symbol_name=symbol_data.get("name"),
                        system=symbol_data.get("system"),
                        error=str(e),
                        error_type=type(e).__name__)
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
                logger.warning("symbol_validation_failed",
                             symbol_name=symbol_data.get("name"),
                             validation_errors=errors)
            
            return is_valid
            
        except Exception as e:
            logger.error("symbol_validation_exception",
                        symbol_name=symbol_data.get("name"),
                        error=str(e),
                        error_type=type(e).__name__)
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
        
        logger.debug("symbol_id_generated",
                    original_name=name,
                    generated_id=symbol_id,
                    counter=counter - 1)
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
        system = symbol_data.get("system", "unknown")
        
        # Validate system
        if not self._is_valid_system(system):
            system = "unknown"
        
        # Create system directory path
        system_dir = self.symbols_dir / system
        
        # Generate filename
        symbol_id = symbol_data.get("id", "unknown")
        filename = f"{symbol_id}.json"
        
        return system_dir / filename
    
    def _is_valid_system(self, system: str) -> bool:
        """
        Check if a system name is valid.
        
        Args:
            system (str): System name to validate
            
        Returns:
            bool: True if valid, False otherwise
        """
        if not system or not isinstance(system, str):
            return False
        
        # Check for valid characters
        if not re.match(r'^[a-zA-Z0-9_-]+$', system):
            return False
        
        # Check length
        if len(system) > 50:
            return False
        
        return True
    
    def _symbol_exists(self, symbol_id: str) -> bool:
        """
        Check if a symbol with the given ID exists.
        
        Args:
            symbol_id (str): Symbol ID to check
            
        Returns:
            bool: True if exists, False otherwise
        """
        try:
            # Try to get the symbol
            symbol = self.library.get_symbol(symbol_id)
            return symbol is not None
        except Exception:
            return False
    
    def _add_creation_metadata(self, symbol_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Add creation metadata to symbol data.
        
        Args:
            symbol_data (Dict[str, Any]): Symbol data to add metadata to
            
        Returns:
            Dict[str, Any]: Symbol data with metadata added
        """
        now = datetime.utcnow().isoformat()
        
        # Add metadata
        symbol_data["metadata"] = symbol_data.get("metadata", {})
        symbol_data["metadata"]["created_at"] = now
        symbol_data["metadata"]["created_by"] = "symbol_manager"
        symbol_data["metadata"]["version"] = "1.0"
        
        # Add file path info
        file_path = self._determine_symbol_file_path(symbol_data)
        symbol_data["metadata"]["file_path"] = str(file_path)
        
        return symbol_data
    
    def get_symbol(self, symbol_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a symbol by ID.
        
        Args:
            symbol_id (str): Symbol ID to retrieve
            
        Returns:
            Optional[Dict[str, Any]]: Symbol data or None if not found
        """
        try:
            logger.debug("symbol_retrieval_attempt", symbol_id=symbol_id)
            
            symbol = self.library.get_symbol(symbol_id)
            
            if symbol:
                logger.debug("symbol_retrieved_successfully",
                           symbol_id=symbol_id,
                           symbol_name=symbol.get("name"))
            else:
                logger.debug("symbol_not_found", symbol_id=symbol_id)
            
            return symbol
            
        except Exception as e:
            logger.error("symbol_retrieval_failed",
                        symbol_id=symbol_id,
                        error=str(e),
                        error_type=type(e).__name__)
            return None
    
    def update_symbol(self, symbol_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Update a symbol with new data.
        
        Args:
            symbol_id (str): Symbol ID to update
            updates (Dict[str, Any]): Updates to apply
            
        Returns:
            Optional[Dict[str, Any]]: Updated symbol data or None if not found
        """
        try:
            logger.info("symbol_update_attempt",
                       symbol_id=symbol_id,
                       update_fields=list(updates.keys()))
            
            # Get current symbol
            current_symbol = self.get_symbol(symbol_id)
            if not current_symbol:
                logger.warning("symbol_update_failed_not_found", symbol_id=symbol_id)
                return None
            
            # Merge updates
            updated_symbol = {**current_symbol, **updates}
            
            # Validate updated symbol
            if not self._validate_symbol_data(updated_symbol):
                logger.warning("symbol_update_failed_validation",
                             symbol_id=symbol_id,
                             symbol_name=updated_symbol.get("name"))
                raise ValueError("Updated symbol data is invalid")
            
            # Add update metadata
            updated_symbol = self._add_update_metadata(updated_symbol)
            
            # Determine new file path (in case system changed)
            new_file_path = self._determine_symbol_file_path(updated_symbol)
            old_file_path = Path(current_symbol.get("metadata", {}).get("file_path", ""))
            
            # Write updated symbol
            with open(new_file_path, 'w', encoding='utf-8') as f:
                json.dump(updated_symbol, f, indent=2, ensure_ascii=False)
            
            # Remove old file if path changed
            if old_file_path.exists() and old_file_path != new_file_path:
                old_file_path.unlink()
                logger.debug("old_symbol_file_removed",
                           old_path=str(old_file_path),
                           new_path=str(new_file_path))
            
            logger.info("symbol_updated_successfully",
                       symbol_id=symbol_id,
                       symbol_name=updated_symbol.get("name"),
                       file_path=str(new_file_path))
            
            # Clear library cache
            self.library.clear_cache()
            
            return updated_symbol
            
        except Exception as e:
            logger.error("symbol_update_failed",
                        symbol_id=symbol_id,
                        error=str(e),
                        error_type=type(e).__name__)
            raise
    
    def _add_update_metadata(self, symbol_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Add update metadata to symbol data.
        
        Args:
            symbol_data (Dict[str, Any]): Symbol data to add metadata to
            
        Returns:
            Dict[str, Any]: Symbol data with metadata added
        """
        now = datetime.utcnow().isoformat()
        
        # Ensure metadata exists
        if "metadata" not in symbol_data:
            symbol_data["metadata"] = {}
        
        # Add update metadata
        symbol_data["metadata"]["updated_at"] = now
        symbol_data["metadata"]["updated_by"] = "symbol_manager"
        
        # Update file path
        file_path = self._determine_symbol_file_path(symbol_data)
        symbol_data["metadata"]["file_path"] = str(file_path)
        
        return symbol_data
    
    def delete_symbol(self, symbol_id: str) -> bool:
        """
        Delete a symbol by ID.
        
        Args:
            symbol_id (str): Symbol ID to delete
            
        Returns:
            bool: True if deleted, False if not found
        """
        try:
            logger.info("symbol_deletion_attempt", symbol_id=symbol_id)
            
            # Get symbol to find file path
            symbol = self.get_symbol(symbol_id)
            if not symbol:
                logger.warning("symbol_deletion_failed_not_found", symbol_id=symbol_id)
                return False
            
            # Get file path
            file_path = Path(symbol.get("metadata", {}).get("file_path", ""))
            
            # Delete file
            if file_path.exists():
                file_path.unlink()
                logger.info("symbol_deleted_successfully",
                           symbol_id=symbol_id,
                           symbol_name=symbol.get("name"),
                           file_path=str(file_path))
            else:
                logger.warning("symbol_file_not_found",
                             symbol_id=symbol_id,
                             file_path=str(file_path))
            
            # Clear library cache
            self.library.clear_cache()
            
            return True
            
        except Exception as e:
            logger.error("symbol_deletion_failed",
                        symbol_id=symbol_id,
                        error=str(e),
                        error_type=type(e).__name__)
            return False
    
    def list_symbols(self, system: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List all symbols, optionally filtered by system.
        
        Args:
            system (Optional[str]): System to filter by
            
        Returns:
            List[Dict[str, Any]]: List of symbol data
        """
        try:
            logger.debug("symbol_list_request", system=system)
            
            symbols = self.library.list_symbols(system=system)
            
            logger.debug("symbol_list_retrieved",
                        system=system,
                        symbol_count=len(symbols))
            
            return symbols
            
        except Exception as e:
            logger.error("symbol_list_failed",
                        system=system,
                        error=str(e),
                        error_type=type(e).__name__)
            return []
    
    def search_symbols(self, query: str, system: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Search symbols by query string.
        
        Args:
            query (str): Search query
            system (Optional[str]): System to filter by
            
        Returns:
            List[Dict[str, Any]]: List of matching symbols
        """
        try:
            logger.debug("symbol_search_request",
                        query=query,
                        system=system)
            
            symbols = self.library.search_symbols(query, system=system)
            
            logger.debug("symbol_search_completed",
                        query=query,
                        system=system,
                        result_count=len(symbols))
            
            return symbols
            
        except Exception as e:
            logger.error("symbol_search_failed",
                        query=query,
                        system=system,
                        error=str(e),
                        error_type=type(e).__name__)
            return []
    
    def get_symbol_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about the symbol library.
        
        Returns:
            Dict[str, Any]: Statistics data
        """
        try:
            logger.debug("symbol_statistics_request")
            
            all_symbols = self.list_symbols()
            
            # Calculate statistics
            total_symbols = len(all_symbols)
            systems = {}
            recent_symbols = []
            
            for symbol in all_symbols:
                # Count by system
                system = symbol.get("system", "unknown")
                systems[system] = systems.get(system, 0) + 1
                
                # Get recent symbols (last 10)
                created_at = symbol.get("metadata", {}).get("created_at")
                if created_at:
                    recent_symbols.append((created_at, symbol))
            
            # Sort recent symbols by creation date
            recent_symbols.sort(key=lambda x: x[0], reverse=True)
            recent_symbols = [symbol for _, symbol in recent_symbols[:10]]
            
            statistics = {
                "total_symbols": total_symbols,
                "systems": systems,
                "recent_symbols": recent_symbols,
                "symbol_sizes": {
                    "small": len([s for s in all_symbols if len(str(s.get("svg", {}))) < 1000]),
                    "medium": len([s for s in all_symbols if 1000 <= len(str(s.get("svg", {}))) < 5000]),
                    "large": len([s for s in all_symbols if len(str(s.get("svg", {}))) >= 5000])
                }
            }
            
            logger.info("symbol_statistics_retrieved",
                       total_symbols=total_symbols,
                       system_count=len(systems),
                       recent_count=len(recent_symbols))
            
            return statistics
            
        except Exception as e:
            logger.error("symbol_statistics_failed",
                        error=str(e),
                        error_type=type(e).__name__)
            return {
                "total_symbols": 0,
                "systems": {},
                "recent_symbols": [],
                "symbol_sizes": {"small": 0, "medium": 0, "large": 0}
            }
    
    def advanced_validate_symbol(self, symbol_data: Dict[str, Any]) -> bool:
        """
        Perform advanced validation on symbol data.
        
        Args:
            symbol_data (Dict[str, Any]): Symbol data to validate
            
        Returns:
            bool: True if valid, False otherwise
        """
        try:
            logger.debug("advanced_symbol_validation_attempt",
                        symbol_name=symbol_data.get("name"),
                        system=symbol_data.get("system"))
            
            # Basic validation
            if not self._validate_symbol_data(symbol_data):
                return False
            
            # Advanced validation with jsonschema if available
            if _use_jsonschema:
                try:
                    # Get schema from validator
                    schema = self.schema_validator.get_schema()
                    jsonschema_validate(symbol_data, schema)
                    logger.debug("advanced_validation_passed",
                               symbol_name=symbol_data.get("name"))
                    return True
                except JsonSchemaValidationError as e:
                    logger.warning("advanced_validation_failed",
                                 symbol_name=symbol_data.get("name"),
                                 jsonschema_error=str(e))
                    return False
            
            # Fallback to basic validation
            logger.debug("advanced_validation_skipped_no_jsonschema",
                        symbol_name=symbol_data.get("name"))
            return True
            
        except Exception as e:
            logger.error("advanced_validation_exception",
                        symbol_name=symbol_data.get("name"),
                        error=str(e),
                        error_type=type(e).__name__)
            return False
    
    def bulk_create_symbols(self, symbols: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Create multiple symbols in bulk.
        
        Args:
            symbols (List[Dict[str, Any]]): List of symbol data to create
            
        Returns:
            List[Dict[str, Any]]: List of created symbols
        """
        try:
            logger.info("bulk_symbol_creation_attempt",
                       symbol_count=len(symbols))
            
            created_symbols = []
            failed_symbols = []
            
            for i, symbol_data in enumerate(symbols):
                try:
                    created_symbol = self.create_symbol(symbol_data)
                    created_symbols.append(created_symbol)
                    
                    logger.debug("bulk_symbol_created",
                               index=i,
                               symbol_id=created_symbol["id"],
                               symbol_name=created_symbol.get("name"))
                    
                except Exception as e:
                    failed_symbols.append({
                        "index": i,
                        "symbol_name": symbol_data.get("name"),
                        "error": str(e)
                    })
                    
                    logger.warning("bulk_symbol_creation_failed",
                                 index=i,
                                 symbol_name=symbol_data.get("name"),
                                 error=str(e))
            
            logger.info("bulk_symbol_creation_completed",
                       total_symbols=len(symbols),
                       successful=len(created_symbols),
                       failed=len(failed_symbols))
            
            return created_symbols
            
        except Exception as e:
            logger.error("bulk_symbol_creation_exception",
                        symbol_count=len(symbols),
                        error=str(e),
                        error_type=type(e).__name__)
            return []
    
    def bulk_update_symbols(self, updates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Update multiple symbols in bulk.
        
        Args:
            updates (List[Dict[str, Any]]): List of symbol updates with IDs
            
        Returns:
            List[Dict[str, Any]]: List of updated symbols
        """
        try:
            logger.info("bulk_symbol_update_attempt",
                       update_count=len(updates))
            
            updated_symbols = []
            failed_updates = []
            
            for i, update_data in enumerate(updates):
                try:
                    symbol_id = update_data.get("id")
                    if not symbol_id:
                        raise ValueError("Symbol ID is required for updates")
                    
                    # Remove ID from update data
                    update_fields = {k: v for k, v in update_data.items() if k != "id"}
                    
                    updated_symbol = self.update_symbol(symbol_id, update_fields)
                    if updated_symbol:
                        updated_symbols.append(updated_symbol)
                        
                        logger.debug("bulk_symbol_updated",
                                   index=i,
                                   symbol_id=symbol_id,
                                   symbol_name=updated_symbol.get("name"))
                    else:
                        failed_updates.append({
                            "index": i,
                            "symbol_id": symbol_id,
                            "error": "Symbol not found"
                        })
                        
                        logger.warning("bulk_symbol_update_failed_not_found",
                                     index=i,
                                     symbol_id=symbol_id)
                    
                except Exception as e:
                    failed_updates.append({
                        "index": i,
                        "symbol_id": update_data.get("id"),
                        "error": str(e)
                    })
                    
                    logger.warning("bulk_symbol_update_failed",
                                 index=i,
                                 symbol_id=update_data.get("id"),
                                 error=str(e))
            
            logger.info("bulk_symbol_update_completed",
                       total_updates=len(updates),
                       successful=len(updated_symbols),
                       failed=len(failed_updates))
            
            return updated_symbols
            
        except Exception as e:
            logger.error("bulk_symbol_update_exception",
                        update_count=len(updates),
                        error=str(e),
                        error_type=type(e).__name__)
            return []
    
    def bulk_delete_symbols(self, symbol_ids: List[str]) -> Dict[str, bool]:
        """
        Delete multiple symbols in bulk.
        
        Args:
            symbol_ids (List[str]): List of symbol IDs to delete
            
        Returns:
            Dict[str, bool]: Mapping of symbol ID to deletion success
        """
        try:
            logger.info("bulk_symbol_deletion_attempt",
                       symbol_count=len(symbol_ids))
            
            results = {}
            
            for symbol_id in symbol_ids:
                try:
                    success = self.delete_symbol(symbol_id)
                    results[symbol_id] = success
                    
                    if success:
                        logger.debug("bulk_symbol_deleted", symbol_id=symbol_id)
                    else:
                        logger.warning("bulk_symbol_deletion_failed", symbol_id=symbol_id)
                    
                except Exception as e:
                    results[symbol_id] = False
                    logger.error("bulk_symbol_deletion_exception",
                               symbol_id=symbol_id,
                               error=str(e))
            
            successful = sum(1 for success in results.values() if success)
            failed = len(results) - successful
            
            logger.info("bulk_symbol_deletion_completed",
                       total_symbols=len(symbol_ids),
                       successful=successful,
                       failed=failed)
            
            return results
            
        except Exception as e:
            logger.error("bulk_symbol_deletion_exception",
                        symbol_count=len(symbol_ids),
                        error=str(e),
                        error_type=type(e).__name__)
            return {symbol_id: False for symbol_id in symbol_ids}
    
    def validate_symbol_with_details(self, symbol_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate symbol with detailed results.
        
        Args:
            symbol_data (Dict[str, Any]): Symbol data to validate
            
        Returns:
            Dict[str, Any]: Detailed validation results
        """
        try:
            logger.debug("detailed_symbol_validation_attempt",
                        symbol_name=symbol_data.get("name"))
            
            # Basic validation
            basic_valid, basic_errors = self.schema_validator.validate_symbol(symbol_data)
            
            # Advanced validation
            advanced_valid = self.advanced_validate_symbol(symbol_data)
            
            result = {
                "symbol_name": symbol_data.get("name"),
                "symbol_id": symbol_data.get("id"),
                "basic_validation": {
                    "valid": basic_valid,
                    "errors": basic_errors
                },
                "advanced_validation": {
                    "valid": advanced_valid,
                    "available": _use_jsonschema
                },
                "overall_valid": basic_valid and advanced_valid
            }
            
            logger.debug("detailed_symbol_validation_completed",
                        symbol_name=symbol_data.get("name"),
                        overall_valid=result["overall_valid"])
            
            return result
            
        except Exception as e:
            logger.error("detailed_symbol_validation_failed",
                        symbol_name=symbol_data.get("name"),
                        error=str(e),
                        error_type=type(e).__name__)
            return {
                "symbol_name": symbol_data.get("name"),
                "symbol_id": symbol_data.get("id"),
                "basic_validation": {"valid": False, "errors": [str(e)]},
                "advanced_validation": {"valid": False, "available": _use_jsonschema},
                "overall_valid": False
            }
    
    def validate_batch_with_details(self, symbols: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Validate a batch of symbols with detailed results.
        
        Args:
            symbols (List[Dict[str, Any]]): List of symbol data to validate
            
        Returns:
            Dict[str, Any]: Batch validation results
        """
        try:
            logger.info("batch_symbol_validation_attempt",
                       symbol_count=len(symbols))
            
            results = []
            valid_count = 0
            invalid_count = 0
            
            for i, symbol_data in enumerate(symbols):
                result = self.validate_symbol_with_details(symbol_data)
                results.append(result)
                
                if result["overall_valid"]:
                    valid_count += 1
                else:
                    invalid_count += 1
            
            batch_result = {
                "total_symbols": len(symbols),
                "valid_symbols": valid_count,
                "invalid_symbols": invalid_count,
                "validation_rate": valid_count / len(symbols) if symbols else 0,
                "results": results
            }
            
            logger.info("batch_symbol_validation_completed",
                       total_symbols=len(symbols),
                       valid_count=valid_count,
                       invalid_count=invalid_count,
                       validation_rate=batch_result["validation_rate"])
            
            return batch_result
            
        except Exception as e:
            logger.error("batch_symbol_validation_failed",
                        symbol_count=len(symbols),
                        error=str(e),
                        error_type=type(e).__name__)
            return {
                "total_symbols": len(symbols),
                "valid_symbols": 0,
                "invalid_symbols": len(symbols),
                "validation_rate": 0,
                "results": []
            } 