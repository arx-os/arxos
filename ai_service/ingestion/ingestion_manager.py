"""
Ingestion Manager - Coordinates all building plan parsers
Automatically selects the right parser for each file type
"""

import logging
import os
from typing import Dict, List, Any, Optional, Type
from .base_parser import BaseParser, BuildingPlan

logger = logging.getLogger(__name__)

class IngestionManager:
    """
    Manages all building plan parsers and routes files to appropriate parsers
    Automatically detects file types and selects the best parser
    """
    
    def __init__(self):
        self.parsers: Dict[str, BaseParser] = {}
        self.file_extensions: Dict[str, str] = {}
        self.parser_priorities: Dict[str, int] = {}
        
        # Register default parsers
        self._register_default_parsers()
    
    def register_parser(self, 
                       parser: BaseParser, 
                       priority: int = 100) -> None:
        """
        Register a new parser with the ingestion manager
        
        Args:
            parser: Parser instance to register
            priority: Priority level (lower = higher priority)
        """
        parser_name = parser.get_parser_name()
        self.parsers[parser_name] = parser
        self.parser_priorities[parser_name] = priority
        
        # Register file extensions
        for format_type in parser.get_supported_formats():
            self.file_extensions[format_type.lower()] = parser_name
        
        logger.info(f"Registered parser: {parser_name} with priority {priority}")
    
    def get_available_parsers(self) -> List[str]:
        """Get list of all registered parser names"""
        return list(self.parsers.keys())
    
    def get_supported_formats(self) -> List[str]:
        """Get list of all supported file formats"""
        return list(self.file_extensions.keys())
    
    async def can_parse_file(self, file_path: str) -> bool:
        """
        Check if any parser can handle the given file
        
        Args:
            file_path: Path to the file to check
            
        Returns:
            True if any parser can handle the file
        """
        try:
            # Check file extension first
            file_ext = self._get_file_extension(file_path)
            if file_ext in self.file_extensions:
                parser_name = self.file_extensions[file_ext]
                parser = self.parsers[parser_name]
                return await parser.can_parse(file_path)
            
            # Fallback: ask all parsers
            for parser in self.parsers.values():
                if await parser.can_parse(file_path):
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking if file can be parsed: {e}")
            return False
    
    async def get_best_parser(self, file_path: str) -> Optional[BaseParser]:
        """
        Get the best parser for the given file
        
        Args:
            file_path: Path to the file
            
        Returns:
            Best parser for the file, or None if no parser can handle it
        """
        try:
            # Check file extension first
            file_ext = self._get_file_extension(file_path)
            if file_ext in self.file_extensions:
                parser_name = self.file_extensions[file_ext]
                parser = self.parsers[parser_name]
                if await parser.can_parse(file_path):
                    return parser
            
            # Fallback: find parser with highest priority that can handle it
            best_parser = None
            best_priority = float('inf')
            
            for parser_name, parser in self.parsers.items():
                if await parser.can_parse(file_path):
                    priority = self.parser_priorities.get(parser_name, 1000)
                    if priority < best_priority:
                        best_priority = priority
                        best_parser = parser
            
            return best_parser
            
        except Exception as e:
            logger.error(f"Error finding best parser: {e}")
            return None
    
    async def parse_building_plan(self, file_path: str) -> BuildingPlan:
        """
        Parse a building plan file using the best available parser
        
        Args:
            file_path: Path to the building plan file
            
        Returns:
            BuildingPlan with extracted building data
            
        Raises:
            ValueError: If no parser can handle the file
        """
        try:
            # Find the best parser
            parser = await self.get_best_parser(file_path)
            if not parser:
                supported_formats = ', '.join(self.get_supported_formats())
                raise ValueError(
                    f"No parser found for file: {file_path}. "
                    f"Supported formats: {supported_formats}"
                )
            
            logger.info(f"Using parser {parser.get_parser_name()} for {file_path}")
            
            # Parse the file
            building_plan = await parser.parse_building_plan(file_path)
            
            # Add source format information
            building_plan.source_format = parser.get_parser_name()
            
            return building_plan
            
        except Exception as e:
            logger.error(f"Error parsing building plan: {e}")
            raise
    
    async def validate_file(self, file_path: str) -> Dict[str, Any]:
        """
        Validate a building plan file
        
        Args:
            file_path: Path to the file to validate
            
        Returns:
            Validation result with status and details
        """
        try:
            parser = await self.get_best_parser(file_path)
            if not parser:
                return {
                    'is_valid': False,
                    'errors': [f"No parser found for file: {file_path}"],
                    'warnings': [],
                    'parser': None
                }
            
            # Validate with the parser
            validation_result = await parser.validate_file(file_path)
            validation_result['parser'] = parser.get_parser_name()
            
            return validation_result
            
        except Exception as e:
            logger.error(f"Error validating file: {e}")
            return {
                'is_valid': False,
                'errors': [f"Validation failed: {str(e)}"],
                'warnings': [],
                'parser': None
            }
    
    async def get_file_info(self, file_path: str) -> Dict[str, Any]:
        """
        Get information about a building plan file
        
        Args:
            file_path: Path to the file
            
        Returns:
            File information and metadata
        """
        try:
            parser = await self.get_best_parser(file_path)
            if not parser:
                return {
                    'error': f"No parser found for file: {file_path}",
                    'parser': None
                }
            
            # Get file info from parser
            file_info = await parser.get_file_info(file_path)
            file_info['parser'] = parser.get_parser_name()
            file_info['estimated_processing_time'] = await parser.estimate_processing_time(file_path)
            file_info['memory_requirements'] = await parser.get_memory_requirements(file_path)
            
            return file_info
            
        except Exception as e:
            logger.error(f"Error getting file info: {e}")
            return {
                'error': f"Failed to get file info: {str(e)}",
                'parser': None
            }
    
    def _get_file_extension(self, file_path: str) -> str:
        """Extract file extension from file path"""
        _, ext = os.path.splitext(file_path)
        return ext.lower().lstrip('.')
    
    def _register_default_parsers(self) -> None:
        """Register the default parsers that come with the system"""
        try:
            # Import and register PDF parser
            from .pdf_parser import PDFParser
            pdf_parser = PDFParser()
            self.register_parser(pdf_parser, priority=100)
            
            logger.info("Registered default parsers")
            
        except ImportError as e:
            logger.warning(f"Could not import default parsers: {e}")
    
    async def get_parser_status(self) -> Dict[str, Any]:
        """Get status of all registered parsers"""
        status = {
            'total_parsers': len(self.parsers),
            'supported_formats': self.get_supported_formats(),
            'parsers': {}
        }
        
        for parser_name, parser in self.parsers.items():
            status['parsers'][parser_name] = {
                'priority': self.parser_priorities.get(parser_name, 1000),
                'supported_formats': parser.get_supported_formats(),
                'name': parser.get_parser_name()
            }
        
        return status
