"""
JSON Symbol Library Service

This module provides a JSON-based symbol library implementation that replaces
the current YAML-based system. It supports loading symbols from JSON files,
caching, search functionality, and system-based organization.

Author: Arxos Development Team
Date: 2024
"""

import os
import json
import logging
from typing import Dict, List, Optional, Any, Union
from pathlib import Path
import time
from functools import lru_cache
import importlib

# Try to import rapidfuzz for fuzzy search, else fallback to difflib
try:
    import importlib.util
    if importlib.util.find_spec('rapidfuzz'):
        from rapidfuzz import fuzz, process as fuzz_process
        _use_rapidfuzz = True
    else:
        import difflib
        _use_rapidfuzz = False
except ImportError:
    import difflib
    _use_rapidfuzz = False

# Import schema validator
from services.symbol_schema_validator import SymbolSchemaValidator

# Setup logging
logger = logging.getLogger(__name__)


class JSONSymbolLibrary:
    """
    JSON-based symbol library implementation.
    
    This class provides functionality to load, cache, and manage symbols
    from JSON files organized by system categories. It replaces the
    current YAML-based system with improved performance and structure.
    
    Attributes:
        library_path (Path): Path to the symbol library directory
        symbols_cache (Dict): Cache for loaded symbols
        metadata_cache (Dict): Cache for library metadata
        cache_timestamp (float): Timestamp of last cache update
        cache_ttl (int): Time-to-live for cache in seconds
    """
    
    def __init__(self, library_path: Optional[str] = None):
        """
        Initialize the JSON symbol library.
        
        Args:
            library_path (Optional[str]): Path to the symbol library directory.
                                       If None, uses default path.
        """
        if library_path is None:
            # Default path relative to this file
            current_dir = Path(__file__).parent
            self.library_path = current_dir.parent.parent / "arx-symbol-library"
        else:
            self.library_path = Path(library_path)
        
        # Initialize caches
        self.symbols_cache: Dict[str, Dict[str, Any]] = {}
        self.metadata_cache: Dict[str, Any] = {}
        self.cache_timestamp = 0.0
        self.cache_ttl = 300  # 5 minutes
        
        # Initialize schema validator
        self.schema_validator = SymbolSchemaValidator()
        
        # Validate library path
        if not self.library_path.exists():
            raise FileNotFoundError(f"Symbol library path not found: {self.library_path}")
        
        logger.info(f"Initialized JSON Symbol Library at: {self.library_path}")
    
    def _get_known_systems(self) -> List[str]:
        """
        Load known systems from index.json for validation.
        Returns:
            List[str]: List of valid system names
        """
        if 'systems' in self.metadata_cache and self._is_cache_valid():
            return self.metadata_cache['systems']
        index_path = self.library_path / 'index.json'
        try:
            with open(index_path, 'r', encoding='utf-8') as f:
                index_data = json.load(f)
                systems = list(index_data.get('by_system', {}).keys())
                self.metadata_cache['systems'] = systems
                self.cache_timestamp = time.time()
                return systems
        except Exception as e:
            logger.warning(f"Failed to load systems from index.json: {e}")
            return []

    def _get_symbols_dir_mtime(self) -> float:
        """
        Get the latest modification time of the symbols directory and its files.
        Returns:
            float: Latest modification timestamp
        """
        symbols_dir = self.library_path / "symbols"
        latest_mtime = 0.0
        if not symbols_dir.exists():
            return latest_mtime
        for root, dirs, files in os.walk(symbols_dir):
            for fname in files:
                fpath = os.path.join(root, fname)
                try:
                    mtime = os.path.getmtime(fpath)
                    if mtime > latest_mtime:
                        latest_mtime = mtime
                except Exception:
                    continue
        return latest_mtime

    def _is_cache_valid(self) -> bool:
        """
        Check if the current cache is still valid (by TTL and file mtime).
        Returns:
            bool: True if cache is valid, False otherwise
        """
        if (time.time() - self.cache_timestamp) >= self.cache_ttl:
            return False
        # Invalidate cache if files have changed
        current_mtime = self._get_symbols_dir_mtime()
        if hasattr(self, '_symbols_dir_mtime'):
            if current_mtime > getattr(self, '_symbols_dir_mtime', 0):
                logger.info("Symbol files changed, invalidating cache.")
                return False
        return True
    
    def _load_json_file(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """
        Load and parse a JSON file safely with validation.
        
        Args:
            file_path (Path): Path to the JSON file
            
        Returns:
            Optional[Dict[str, Any]]: Parsed JSON data or None if error
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
                # Validate symbol data if it has required fields
                if isinstance(data, dict) and "id" in data and "name" in data:
                    if not self.validate_symbol(data):
                        logger.warning(f"Symbol validation failed for {file_path}")
                        return None
                
                return data
        except (json.JSONDecodeError, FileNotFoundError, PermissionError) as e:
            logger.warning(f"Failed to load JSON file {file_path}: {e}")
            return None
    
    def load_all_symbols(self) -> Dict[str, Dict[str, Any]]:
        """
        Load all symbols from the library, with cache and size limit.
        Returns:
            Dict[str, Dict[str, Any]]: Dictionary of all symbols indexed by symbol ID
        """
        # Check cache first
        if self._is_cache_valid() and self.symbols_cache:
            logger.debug("Returning cached symbols")
            return self.symbols_cache
        logger.info("Loading all symbols from JSON files...")
        symbols = {}
        symbols_dir = self.library_path / "symbols"
        if not symbols_dir.exists():
            logger.warning(f"Symbols directory not found: {symbols_dir}")
            return symbols
        for system_dir in symbols_dir.iterdir():
            if not system_dir.is_dir():
                continue
            system_name = system_dir.name
            logger.debug(f"Loading symbols for system: {system_name}")
            for json_file in system_dir.glob("*.json"):
                symbol_data = self._load_json_file(json_file)
                if symbol_data and "id" in symbol_data:
                    symbol_id = symbol_data["id"]
                    symbols[symbol_id] = symbol_data
                    logger.debug(f"Loaded symbol: {symbol_id}")
        # Cache size limit
        if len(symbols) > 2000:
            logger.warning(f"Symbol cache size exceeded 2000 ({len(symbols)}). Clearing cache.")
            symbols = {}
        self.symbols_cache = symbols
        self.cache_timestamp = time.time()
        self._symbols_dir_mtime = self._get_symbols_dir_mtime()
        logger.info(f"Loaded {len(symbols)} symbols")
        return symbols
    
    def load_symbols_by_system(self, system: str) -> Dict[str, Dict[str, Any]]:
        """
        Load symbols for a specific system, with validation.
        Args:
            system (str): System name (e.g., 'mechanical', 'electrical')
        Returns:
            Dict[str, Dict[str, Any]]: Dictionary of symbols for the specified system
        """
        known_systems = self._get_known_systems()
        if system.lower() not in [s.lower() for s in known_systems]:
            logger.warning(f"Requested system '{system}' is not a known system: {known_systems}")
            return {}
        all_symbols = self.load_all_symbols()
        system_symbols = {}
        for symbol_id, symbol_data in all_symbols.items():
            if symbol_data.get("system", "").lower() == system.lower():
                system_symbols[symbol_id] = symbol_data
        logger.info(f"Loaded {len(system_symbols)} symbols for system: {system}")
        return system_symbols
    
    def get_symbol(self, symbol_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific symbol by ID.
        
        Args:
            symbol_id (str): The symbol ID to retrieve
            
        Returns:
            Optional[Dict[str, Any]]: Symbol data or None if not found
        """
        # Load all symbols (uses cache)
        all_symbols = self.load_all_symbols()
        return all_symbols.get(symbol_id)
    
    def search_symbols(
        self,
        query: str,
        system: Optional[str] = None,
        tags: Optional[List[str]] = None,
        properties: Optional[Dict[str, Any]] = None,
        max_results: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Enhanced search for symbols with fuzzy matching, tag/property filtering, and ranking.
        Args:
            query (str): Search query string
            system (Optional[str]): Filter by system name
            tags (Optional[List[str]]): Filter by required tags
            properties (Optional[Dict[str, Any]]): Filter by required property key/values
            max_results (int): Maximum number of results to return
        Returns:
            List[Dict[str, Any]]: Ranked list of matching symbols
        """
        query = (query or '').strip().lower()
        tags = [t.lower() for t in tags] if tags else []
        properties = properties or {}
        results = []
        # Load symbols based on system filter
        if system:
            symbols = self.load_symbols_by_system(system)
        else:
            symbols = self.load_all_symbols()
        # Precompute for ranking
        scored = []
        for symbol_id, symbol_data in symbols.items():
            name = symbol_data.get("name", "").lower()
            description = symbol_data.get("description", "").lower()
            symbol_tags = [tag.lower() for tag in symbol_data.get("tags", [])]
            symbol_properties = symbol_data.get("properties", {})
            # Tag-based filtering
            if tags and not all(t in symbol_tags for t in tags):
                continue
            # Property-based filtering
            if properties:
                match = True
                for k, v in properties.items():
                    if symbol_properties.get(k, '').lower() != str(v).lower():
                        match = False
                        break
                if not match:
                    continue
            # Fuzzy and substring search
            if not query:
                score = 0
            else:
                if _use_rapidfuzz:
                    score = max(
                        fuzz.partial_ratio(query, name),
                        fuzz.partial_ratio(query, description),
                        fuzz.partial_ratio(query, symbol_id.lower()),
                        max([fuzz.partial_ratio(query, t) for t in symbol_tags], default=0)
                    )
                else:
                    # Use difflib for fallback
                    score = max(
                        difflib.SequenceMatcher(None, query, name).ratio(),
                        difflib.SequenceMatcher(None, query, description).ratio(),
                        difflib.SequenceMatcher(None, query, symbol_id.lower()).ratio(),
                        max([difflib.SequenceMatcher(None, query, t).ratio() for t in symbol_tags], default=0)
                    ) * 100
            # Only include if relevant
            if score > 40 or (not query):
                scored.append((score, symbol_data))
        # Sort by score descending
        scored.sort(key=lambda x: x[0], reverse=True)
        # Performance: limit results
        results = [s for _, s in scored[:max_results]]
        logger.info(f"Search for '{query}' (system={system}, tags={tags}, properties={properties}) returned {len(results)} results.")
        return results
    
    def get_available_systems(self) -> List[str]:
        """
        Get list of available systems.
        
        Returns:
            List[str]: List of system names
        """
        symbols_dir = self.library_path / "symbols"
        if not symbols_dir.exists():
            return []
        
        systems = []
        for system_dir in symbols_dir.iterdir():
            if system_dir.is_dir():
                systems.append(system_dir.name)
        
        return sorted(systems)
    
    def get_symbol_count(self) -> int:
        """
        Get total number of symbols in the library.
        
        Returns:
            int: Total symbol count
        """
        symbols = self.load_all_symbols()
        return len(symbols)
    
    def clear_cache(self) -> None:
        """
        Clear the symbol cache.
        """
        self.symbols_cache.clear()
        self.metadata_cache.clear()
        self.cache_timestamp = 0.0
        logger.info("Symbol cache cleared")
    
    def validate_symbol(self, symbol_data: Dict[str, Any]) -> bool:
        """
        Validate symbol data using comprehensive schema validation.
        
        Args:
            symbol_data (Dict[str, Any]): Symbol data to validate
            
        Returns:
            bool: True if valid, False otherwise
        """
        try:
            is_valid, errors = self.schema_validator.validate_symbol(symbol_data)
            
            if not is_valid:
                for error in errors:
                    logger.warning(f"Symbol validation error: {error['field_path']} - {error['message']}")
            
            return is_valid
            
        except Exception as e:
            logger.error(f"Symbol validation failed with exception: {e}")
            return False
    
    def load_systems_metadata(self) -> Dict[str, Any]:
        """
        Load systems metadata from systems.json.
        
        Returns:
            Dict[str, Any]: Systems metadata including system list, categories, and counts
        """
        cache_key = 'systems_metadata'
        if cache_key in self.metadata_cache and self._is_cache_valid():
            logger.debug("Returning cached systems metadata")
            return self.metadata_cache[cache_key]
        
        systems_file = self.library_path / "systems.json"
        if not systems_file.exists():
            logger.warning(f"Systems metadata file not found: {systems_file}")
            return {}
        
        try:
            with open(systems_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
                self.metadata_cache[cache_key] = metadata
                logger.info("Loaded systems metadata successfully")
                return metadata
        except Exception as e:
            logger.error(f"Failed to load systems metadata: {e}")
            return {}
    
    def load_categories_metadata(self) -> Dict[str, Any]:
        """
        Load categories metadata from categories.json.
        
        Returns:
            Dict[str, Any]: Categories metadata including category definitions
        """
        cache_key = 'categories_metadata'
        if cache_key in self.metadata_cache and self._is_cache_valid():
            logger.debug("Returning cached categories metadata")
            return self.metadata_cache[cache_key]
        
        categories_file = self.library_path / "categories.json"
        if not categories_file.exists():
            logger.warning(f"Categories metadata file not found: {categories_file}")
            return {}
        
        try:
            with open(categories_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
                self.metadata_cache[cache_key] = metadata
                logger.info("Loaded categories metadata successfully")
                return metadata
        except Exception as e:
            logger.error(f"Failed to load categories metadata: {e}")
            return {}
    
    def load_symbol_index(self) -> Dict[str, Any]:
        """
        Load symbol index from index.json.
        
        Returns:
            Dict[str, Any]: Symbol index including symbol list and system mappings
        """
        cache_key = 'symbol_index'
        if cache_key in self.metadata_cache and self._is_cache_valid():
            logger.debug("Returning cached symbol index")
            return self.metadata_cache[cache_key]
        
        index_file = self.library_path / "index.json"
        if not index_file.exists():
            logger.warning(f"Symbol index file not found: {index_file}")
            return {}
        
        try:
            with open(index_file, 'r', encoding='utf-8') as f:
                index_data = json.load(f)
                self.metadata_cache[cache_key] = index_data
                logger.info("Loaded symbol index successfully")
                return index_data
        except Exception as e:
            logger.error(f"Failed to load symbol index: {e}")
            return {}
    
    def validate_metadata(self, metadata: Dict[str, Any], metadata_type: str) -> bool:
        """
        Validate metadata structure.
        
        Args:
            metadata (Dict[str, Any]): Metadata to validate
            metadata_type (str): Type of metadata ('systems', 'categories', 'index')
            
        Returns:
            bool: True if valid, False otherwise
        """
        if not isinstance(metadata, dict):
            logger.warning(f"Invalid {metadata_type} metadata: not a dictionary")
            return False
        
        if metadata_type == 'systems':
            required_keys = ['systems', 'categories', 'total_symbols', 'system_counts']
            for key in required_keys:
                if key not in metadata:
                    logger.warning(f"Missing required key in systems metadata: {key}")
                    return False
            
            # Validate systems list
            if not isinstance(metadata['systems'], list):
                logger.warning("Systems metadata 'systems' field must be a list")
                return False
            
            # Validate categories structure
            if not isinstance(metadata['categories'], dict):
                logger.warning("Systems metadata 'categories' field must be a dictionary")
                return False
        
        elif metadata_type == 'categories':
            required_keys = ['categories']
            for key in required_keys:
                if key not in metadata:
                    logger.warning(f"Missing required key in categories metadata: {key}")
                    return False
            
            # Validate categories structure
            if not isinstance(metadata['categories'], dict):
                logger.warning("Categories metadata 'categories' field must be a dictionary")
                return False
        
        elif metadata_type == 'index':
            required_keys = ['symbols', 'by_system', 'total_count']
            for key in required_keys:
                if key not in metadata:
                    logger.warning(f"Missing required key in symbol index: {key}")
                    return False
            
            # Validate symbols list
            if not isinstance(metadata['symbols'], list):
                logger.warning("Symbol index 'symbols' field must be a list")
                return False
            
            # Validate by_system structure
            if not isinstance(metadata['by_system'], dict):
                logger.warning("Symbol index 'by_system' field must be a dictionary")
                return False
        
        logger.debug(f"{metadata_type} metadata validation passed")
        return True
    
    def get_system_categories(self, system: str) -> List[str]:
        """
        Get categories for a specific system.
        
        Args:
            system (str): System name
            
        Returns:
            List[str]: List of categories for the system
        """
        systems_metadata = self.load_systems_metadata()
        if not self.validate_metadata(systems_metadata, 'systems'):
            return []
        
        categories = systems_metadata.get('categories', {})
        return categories.get(system, [])
    
    def get_system_symbol_count(self, system: str) -> int:
        """
        Get symbol count for a specific system.
        
        Args:
            system (str): System name
            
        Returns:
            int: Number of symbols in the system
        """
        systems_metadata = self.load_systems_metadata()
        if not self.validate_metadata(systems_metadata, 'systems'):
            return 0
        
        system_counts = systems_metadata.get('system_counts', {})
        return system_counts.get(system, 0)
    
    def get_all_categories(self) -> Dict[str, List[str]]:
        """
        Get all categories organized by system.
        
        Returns:
            Dict[str, List[str]]: Dictionary mapping systems to their categories
        """
        categories_metadata = self.load_categories_metadata()
        if not self.validate_metadata(categories_metadata, 'categories'):
            return {}
        
        return categories_metadata.get('categories', {})
    
    def get_symbols_by_system_from_index(self, system: str) -> List[str]:
        """
        Get symbol IDs for a system from the index.
        
        Args:
            system (str): System name
            
        Returns:
            List[str]: List of symbol IDs for the system
        """
        index_data = self.load_symbol_index()
        if not self.validate_metadata(index_data, 'index'):
            return []
        
        by_system = index_data.get('by_system', {})
        return by_system.get(system, [])
    
    def refresh_metadata_cache(self) -> None:
        """
        Clear metadata cache to force reload of all metadata files.
        """
        self.metadata_cache.clear()
        logger.info("Metadata cache cleared")
    
    def get_metadata_summary(self) -> Dict[str, Any]:
        """
        Get a summary of all metadata.
        
        Returns:
            Dict[str, Any]: Summary of systems, categories, and symbol counts
        """
        systems_metadata = self.load_systems_metadata()
        categories_metadata = self.load_categories_metadata()
        index_data = self.load_symbol_index()
        
        summary = {
            'systems': systems_metadata.get('systems', []),
            'total_symbols': systems_metadata.get('total_symbols', 0),
            'system_counts': systems_metadata.get('system_counts', {}),
            'categories': categories_metadata.get('categories', {}),
            'index_symbols': len(index_data.get('symbols', [])),
            'cache_status': {
                'symbols_cache_size': len(self.symbols_cache),
                'metadata_cache_size': len(self.metadata_cache),
                'cache_timestamp': self.cache_timestamp,
                'cache_valid': self._is_cache_valid()
            }
        }
        
        return summary 