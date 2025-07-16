"""
SVGX Engine - Symbol Manager Service

This module provides comprehensive symbol management functionality for SVGX Engine,
including CRUD operations, validation, file management, and SVGX-specific features.

Features:
- Symbol creation, reading, updating, and deletion
- SVGX-specific symbol validation and enhancement
- Performance monitoring and caching
- Bulk operations support
- Advanced search and filtering
- SVGX namespace support
"""

import os
import json
import uuid
import re
from typing import Dict, List, Optional, Any, Union, Tuple
from pathlib import Path
from datetime import datetime
import shutil
import importlib
from enum import Enum

from structlog import get_logger

from .error_handler import SVGXErrorHandler
from ..utils.performance import PerformanceMonitor
from ..utils.errors import ValidationError, SymbolError
from ..models.svgx import SVGXElement, SVGXDocument

logger = get_logger()


class SymbolCategory(Enum):
    """Categories of symbols in SVGX Engine."""
    ELECTRICAL = "electrical"
    MECHANICAL = "mechanical"
    PLUMBING = "plumbing"
    HVAC = "hvac"
    FIRE_PROTECTION = "fire_protection"
    SECURITY = "security"
    TELECOMMUNICATIONS = "telecommunications"
    STRUCTURAL = "structural"
    ARCHITECTURAL = "architectural"
    SVGX = "svgx"  # SVGX-specific symbols


class SymbolStatus(Enum):
    """Status of symbols in SVGX Engine."""
    ACTIVE = "active"
    DRAFT = "draft"
    DEPRECATED = "deprecated"
    ARCHIVED = "archived"
    PENDING_REVIEW = "pending_review"


class SymbolValidationLevel(Enum):
    """Validation levels for symbols."""
    BASIC = "basic"
    STANDARD = "standard"
    STRICT = "strict"
    COMPREHENSIVE = "comprehensive"


class SVGXSymbolManager:
    """
    Comprehensive symbol manager for SVGX Engine.
    
    Provides enhanced symbol management functionality with SVGX-specific features,
    performance monitoring, and comprehensive error handling.
    """
    
    def __init__(self, library_path: Optional[str] = None):
        """
        Initialize the SVGX Symbol Manager.
        
        Args:
            library_path: Path to the symbol library. Defaults to standard path.
        """
        self.error_handler = SVGXErrorHandler()
        self.performance_monitor = PerformanceMonitor()
        
        # Set up library paths
        self.library_path = Path(library_path or "svgx_symbols")
        self.symbols_dir = self.library_path / "symbols"
        self.metadata_dir = self.library_path / "metadata"
        self.cache_dir = self.library_path / "cache"
        
        # Ensure directories exist
        for directory in [self.symbols_dir, self.metadata_dir, self.cache_dir]:
            directory.mkdir(parents=True, exist_ok=True)
        
        # Initialize symbol cache
        self._symbol_cache = {}
        self._metadata_cache = {}
        
        logger.info("SVGX Symbol Manager initialized",
                   library_path=str(self.library_path),
                   symbols_dir=str(self.symbols_dir))
    
    def create_symbol(self, symbol_data: Dict[str, Any], 
                     validation_level: SymbolValidationLevel = SymbolValidationLevel.STANDARD) -> Dict[str, Any]:
        """
        Create a new symbol with SVGX enhancements.
        
        Args:
            symbol_data: Symbol data to create
            validation_level: Level of validation to apply
            
        Returns:
            Created symbol data with generated ID and SVGX metadata
            
        Raises:
            ValidationError: If symbol data is invalid
            SymbolError: If symbol creation fails
        """
        with self.performance_monitor.monitor("symbol_creation"):
            try:
                logger.info("SVGX symbol creation attempt",
                           symbol_name=symbol_data.get("name"),
                           category=symbol_data.get("category"))
                
                # Validate symbol data
                validation_result = self._validate_symbol_data(symbol_data, validation_level)
                if not validation_result["is_valid"]:
                    raise ValidationError(f"Symbol validation failed: {validation_result['errors']}")
                
                # Generate symbol ID if not provided
                if "id" not in symbol_data or not symbol_data["id"]:
                    symbol_data["id"] = self._generate_svgx_symbol_id(symbol_data)
                
                symbol_id = symbol_data["id"]
                
                # Check if symbol already exists
                if self._symbol_exists(symbol_id):
                    raise SymbolError(f"Symbol with ID '{symbol_id}' already exists")
                
                # Add SVGX-specific enhancements
                symbol_data = self._add_svgx_enhancements(symbol_data)
                
                # Determine file path
                file_path = self._determine_symbol_file_path(symbol_data)
                
                # Ensure directory exists
                file_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Add creation metadata
                symbol_data = self._add_creation_metadata(symbol_data)
                
                # Write symbol file
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(symbol_data, f, indent=2, ensure_ascii=False)
                
                # Update cache
                self._symbol_cache[symbol_id] = symbol_data
                
                logger.info("SVGX symbol created successfully",
                           symbol_id=symbol_id,
                           symbol_name=symbol_data.get("name"),
                           category=symbol_data.get("category"),
                           file_path=str(file_path))
                
                return symbol_data
                
            except (ValidationError, SymbolError):
                raise
            except Exception as e:
                self.error_handler.handle_general_error(str(e), "symbol_manager")
                raise SymbolError(f"Symbol creation failed: {str(e)}")
    
    def get_symbol(self, symbol_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a symbol by ID with caching.
        
        Args:
            symbol_id: ID of the symbol to retrieve
            
        Returns:
            Symbol data or None if not found
        """
        with self.performance_monitor.monitor("symbol_retrieval"):
            try:
                # Check cache first
                if symbol_id in self._symbol_cache:
                    return self._symbol_cache[symbol_id]
                
                # Load from file
                file_path = self._get_symbol_file_path(symbol_id)
                if not file_path.exists():
                    return None
                
                with open(file_path, 'r', encoding='utf-8') as f:
                    symbol_data = json.load(f)
                
                # Update cache
                self._symbol_cache[symbol_id] = symbol_data
                
                return symbol_data
                
            except Exception as e:
                self.error_handler.handle_general_error(str(e), "symbol_manager")
                logger.error("Failed to retrieve symbol", symbol_id=symbol_id, error=str(e))
                return None
    
    def update_symbol(self, symbol_id: str, updates: Dict[str, Any],
                     validation_level: SymbolValidationLevel = SymbolValidationLevel.STANDARD) -> Optional[Dict[str, Any]]:
        """
        Update a symbol with SVGX enhancements.
        
        Args:
            symbol_id: ID of the symbol to update
            updates: Updates to apply
            validation_level: Level of validation to apply
            
        Returns:
            Updated symbol data or None if not found
        """
        with self.performance_monitor.monitor("symbol_update"):
            try:
                # Get existing symbol
                existing_symbol = self.get_symbol(symbol_id)
                if not existing_symbol:
                    return None
                
                # Merge updates
                updated_symbol = {**existing_symbol, **updates}
                
                # Validate updated symbol
                validation_result = self._validate_symbol_data(updated_symbol, validation_level)
                if not validation_result["is_valid"]:
                    raise ValidationError(f"Symbol validation failed: {validation_result['errors']}")
                
                # Add SVGX enhancements
                updated_symbol = self._add_svgx_enhancements(updated_symbol)
                
                # Add update metadata
                updated_symbol = self._add_update_metadata(updated_symbol)
                
                # Write updated symbol
                file_path = self._get_symbol_file_path(symbol_id)
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(updated_symbol, f, indent=2, ensure_ascii=False)
                
                # Update cache
                self._symbol_cache[symbol_id] = updated_symbol
                
                logger.info("SVGX symbol updated successfully",
                           symbol_id=symbol_id,
                           symbol_name=updated_symbol.get("name"))
                
                return updated_symbol
                
            except ValidationError:
                raise
            except Exception as e:
                self.error_handler.handle_general_error(str(e), "symbol_manager")
                raise SymbolError(f"Symbol update failed: {str(e)}")
    
    def delete_symbol(self, symbol_id: str) -> bool:
        """
        Delete a symbol.
        
        Args:
            symbol_id: ID of the symbol to delete
            
        Returns:
            True if deleted successfully, False otherwise
        """
        with self.performance_monitor.monitor("symbol_deletion"):
            try:
                file_path = self._get_symbol_file_path(symbol_id)
                if not file_path.exists():
                    return False
                
                # Remove from cache
                self._symbol_cache.pop(symbol_id, None)
                
                # Delete file
                file_path.unlink()
                
                logger.info("SVGX symbol deleted successfully", symbol_id=symbol_id)
                return True
                
            except Exception as e:
                self.error_handler.handle_general_error(str(e), "symbol_manager")
                logger.error("Failed to delete symbol", symbol_id=symbol_id, error=str(e))
                return False
    
    def list_symbols(self, category: Optional[SymbolCategory] = None,
                    status: Optional[SymbolStatus] = None) -> List[Dict[str, Any]]:
        """
        List symbols with optional filtering.
        
        Args:
            category: Filter by symbol category
            status: Filter by symbol status
            
        Returns:
            List of symbol data
        """
        with self.performance_monitor.monitor("symbol_listing"):
            try:
                symbols = []
                
                # Scan symbols directory
                for file_path in self.symbols_dir.rglob("*.json"):
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            symbol_data = json.load(f)
                        
                        # Apply filters
                        if category and symbol_data.get("category") != category.value:
                            continue
                        if status and symbol_data.get("status") != status.value:
                            continue
                        
                        symbols.append(symbol_data)
                        
                    except Exception as e:
                        logger.warning("Failed to load symbol file", file_path=str(file_path), error=str(e))
                
                return symbols
                
            except Exception as e:
                self.error_handler.handle_general_error(str(e), "symbol_manager")
                logger.error("Failed to list symbols", error=str(e))
                return []
    
    def search_symbols(self, query: str, category: Optional[SymbolCategory] = None,
                      status: Optional[SymbolStatus] = None) -> List[Dict[str, Any]]:
        """
        Search symbols by query with optional filtering.
        
        Args:
            query: Search query
            category: Filter by symbol category
            status: Filter by symbol status
            
        Returns:
            List of matching symbol data
        """
        with self.performance_monitor.monitor("symbol_search"):
            try:
                all_symbols = self.list_symbols(category, status)
                query_lower = query.lower()
                
                matching_symbols = []
                for symbol in all_symbols:
                    # Search in name, description, and tags
                    searchable_text = f"{symbol.get('name', '')} {symbol.get('description', '')} {' '.join(symbol.get('tags', []))}"
                    
                    if query_lower in searchable_text.lower():
                        matching_symbols.append(symbol)
                
                return matching_symbols
                
            except Exception as e:
                self.error_handler.handle_general_error(str(e), "symbol_manager")
                logger.error("Failed to search symbols", error=str(e))
                return []
    
    def bulk_create_symbols(self, symbols: List[Dict[str, Any]],
                           validation_level: SymbolValidationLevel = SymbolValidationLevel.STANDARD) -> List[Dict[str, Any]]:
        """
        Create multiple symbols in bulk.
        
        Args:
            symbols: List of symbol data to create
            validation_level: Level of validation to apply
            
        Returns:
            List of created symbol data
        """
        with self.performance_monitor.monitor("bulk_symbol_creation"):
            created_symbols = []
            
            for symbol_data in symbols:
                try:
                    created_symbol = self.create_symbol(symbol_data, validation_level)
                    created_symbols.append(created_symbol)
                except Exception as e:
                    logger.error("Failed to create symbol in bulk",
                               symbol_name=symbol_data.get("name"),
                               error=str(e))
            
            return created_symbols
    
    def bulk_update_symbols(self, updates: List[Dict[str, Any]],
                           validation_level: SymbolValidationLevel = SymbolValidationLevel.STANDARD) -> List[Dict[str, Any]]:
        """
        Update multiple symbols in bulk.
        
        Args:
            updates: List of update data (must include 'id' field)
            validation_level: Level of validation to apply
            
        Returns:
            List of updated symbol data
        """
        with self.performance_monitor.monitor("bulk_symbol_update"):
            updated_symbols = []
            
            for update_data in updates:
                try:
                    symbol_id = update_data.get("id")
                    if not symbol_id:
                        logger.warning("Update data missing symbol ID", update_data=update_data)
                        continue
                    
                    # Remove id from updates to avoid overwriting
                    updates_dict = {k: v for k, v in update_data.items() if k != "id"}
                    updated_symbol = self.update_symbol(symbol_id, updates_dict, validation_level)
                    
                    if updated_symbol:
                        updated_symbols.append(updated_symbol)
                        
                except Exception as e:
                    logger.error("Failed to update symbol in bulk",
                               symbol_id=update_data.get("id"),
                               error=str(e))
            
            return updated_symbols
    
    def get_symbol_statistics(self) -> Dict[str, Any]:
        """
        Get comprehensive symbol statistics.
        
        Returns:
            Dictionary with symbol statistics
        """
        with self.performance_monitor.monitor("symbol_statistics"):
            try:
                all_symbols = self.list_symbols()
                
                # Count by category
                category_counts = {}
                status_counts = {}
                total_symbols = len(all_symbols)
                
                for symbol in all_symbols:
                    category = symbol.get("category", "unknown")
                    status = symbol.get("status", "unknown")
                    
                    category_counts[category] = category_counts.get(category, 0) + 1
                    status_counts[status] = status_counts.get(status, 0) + 1
                
                return {
                    "total_symbols": total_symbols,
                    "category_breakdown": category_counts,
                    "status_breakdown": status_counts,
                    "svgx_symbols": len([s for s in all_symbols if s.get("category") == "svgx"]),
                    "performance_metrics": self.performance_monitor.get_metrics()
                }
                
            except Exception as e:
                self.error_handler.handle_general_error(str(e), "symbol_manager")
                logger.error("Failed to get symbol statistics", error=str(e))
                return {}
    
    def _validate_symbol_data(self, symbol_data: Dict[str, Any],
                             validation_level: SymbolValidationLevel) -> Dict[str, Any]:
        """
        Validate symbol data with SVGX-specific rules.
        
        Args:
            symbol_data: Symbol data to validate
            validation_level: Level of validation to apply
            
        Returns:
            Validation result with details
        """
        errors = []
        warnings = []
        
        # Basic validation
        if not symbol_data.get("name"):
            errors.append("Symbol name is required")
        
        if not symbol_data.get("category"):
            errors.append("Symbol category is required")
        
        # Standard validation
        if validation_level in [SymbolValidationLevel.STANDARD, SymbolValidationLevel.STRICT, SymbolValidationLevel.COMPREHENSIVE]:
            if not symbol_data.get("description"):
                warnings.append("Symbol description is recommended")
            
            if not symbol_data.get("tags"):
                warnings.append("Symbol tags are recommended")
        
        # Strict validation
        if validation_level in [SymbolValidationLevel.STRICT, SymbolValidationLevel.COMPREHENSIVE]:
            if not symbol_data.get("svgx_namespace"):
                warnings.append("SVGX namespace is recommended for SVGX symbols")
            
            if not symbol_data.get("version"):
                warnings.append("Symbol version is recommended")
        
        # Comprehensive validation
        if validation_level == SymbolValidationLevel.COMPREHENSIVE:
            if not symbol_data.get("metadata"):
                warnings.append("Symbol metadata is recommended")
            
            if not symbol_data.get("validation_rules"):
                warnings.append("Symbol validation rules are recommended")
        
        return {
            "is_valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "validation_level": validation_level.value
        }
    
    def _generate_svgx_symbol_id(self, symbol_data: Dict[str, Any]) -> str:
        """
        Generate a unique SVGX symbol ID.
        
        Args:
            symbol_data: Symbol data to generate ID for
            
        Returns:
            Generated symbol ID
        """
        name = symbol_data.get("name", "").strip()
        category = symbol_data.get("category", "unknown")
        
        if not name:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            base_id = f"{category}_{timestamp}"
        else:
            base_id = self._normalize_name_to_id(name)
        
        # Ensure uniqueness
        counter = 1
        symbol_id = base_id
        while self._symbol_exists(symbol_id):
            symbol_id = f"{base_id}_{counter}"
            counter += 1
        
        return symbol_id
    
    def _normalize_name_to_id(self, name: str) -> str:
        """
        Normalize a name to a valid symbol ID.
        
        Args:
            name: Name to normalize
            
        Returns:
            Normalized ID
        """
        # Convert to lowercase and replace spaces with underscores
        normalized = re.sub(r'[^a-zA-Z0-9_]', '_', name.lower())
        # Remove multiple consecutive underscores
        normalized = re.sub(r'_+', '_', normalized)
        # Remove leading/trailing underscores
        normalized = normalized.strip('_')
        return normalized
    
    def _add_svgx_enhancements(self, symbol_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Add SVGX-specific enhancements to symbol data.
        
        Args:
            symbol_data: Original symbol data
            
        Returns:
            Enhanced symbol data
        """
        enhanced = symbol_data.copy()
        
        # Add SVGX namespace if not present
        if "svgx_namespace" not in enhanced:
            enhanced["svgx_namespace"] = "arx"
        
        # Add SVGX version if not present
        if "svgx_version" not in enhanced:
            enhanced["svgx_version"] = "1.0"
        
        # Add SVGX metadata
        if "svgx_metadata" not in enhanced:
            enhanced["svgx_metadata"] = {
                "created_by": "svgx_engine",
                "engine_version": "1.0",
                "enhanced_features": True
            }
        
        # Add SVGX validation rules
        if "svgx_validation_rules" not in enhanced:
            enhanced["svgx_validation_rules"] = {
                "geometry_required": True,
                "namespace_required": True,
                "version_required": True
            }
        
        return enhanced
    
    def _add_creation_metadata(self, symbol_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Add creation metadata to symbol data.
        
        Args:
            symbol_data: Symbol data to enhance
            
        Returns:
            Enhanced symbol data
        """
        enhanced = symbol_data.copy()
        
        enhanced["created_at"] = datetime.now().isoformat()
        enhanced["updated_at"] = datetime.now().isoformat()
        enhanced["created_by"] = enhanced.get("created_by", "svgx_engine")
        enhanced["version"] = enhanced.get("version", "1.0")
        enhanced["status"] = enhanced.get("status", SymbolStatus.ACTIVE.value)
        
        return enhanced
    
    def _add_update_metadata(self, symbol_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Add update metadata to symbol data.
        
        Args:
            symbol_data: Symbol data to enhance
            
        Returns:
            Enhanced symbol data
        """
        enhanced = symbol_data.copy()
        enhanced["updated_at"] = datetime.now().isoformat()
        return enhanced
    
    def _determine_symbol_file_path(self, symbol_data: Dict[str, Any]) -> Path:
        """
        Determine the file path for a symbol.
        
        Args:
            symbol_data: Symbol data
            
        Returns:
            File path for the symbol
        """
        category = symbol_data.get("category", "unknown")
        symbol_id = symbol_data.get("id", "unknown")
        
        return self.symbols_dir / category / f"{symbol_id}.json"
    
    def _get_symbol_file_path(self, symbol_id: str) -> Path:
        """
        Get the file path for a symbol by ID.
        
        Args:
            symbol_id: Symbol ID
            
        Returns:
            File path for the symbol
        """
        # Search in all subdirectories
        for file_path in self.symbols_dir.rglob("*.json"):
            if file_path.stem == symbol_id:
                return file_path
        
        # Fallback to unknown category
        return self.symbols_dir / "unknown" / f"{symbol_id}.json"
    
    def _symbol_exists(self, symbol_id: str) -> bool:
        """
        Check if a symbol exists.
        
        Args:
            symbol_id: Symbol ID to check
            
        Returns:
            True if symbol exists, False otherwise
        """
        return self._get_symbol_file_path(symbol_id).exists()
    
    def clear_cache(self):
        """Clear the symbol cache."""
        self._symbol_cache.clear()
        self._metadata_cache.clear()
        logger.info("SVGX symbol cache cleared")


# Convenience function for creating symbol manager
def create_svgx_symbol_manager(library_path: Optional[str] = None) -> SVGXSymbolManager:
    """Create and return a configured SVGX Symbol Manager."""
    return SVGXSymbolManager(library_path) 