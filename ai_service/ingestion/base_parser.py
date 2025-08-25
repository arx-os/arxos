"""
Base Parser - Abstract interface for all building plan parsers
Defines the common interface that all file type parsers must implement
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Tuple, Optional
from dataclasses import dataclass

@dataclass
class BuildingElement:
    """Extracted building element from any file format"""
    element_type: str
    coordinates: Tuple[float, float, float, float]  # x1, y1, x2, y2
    properties: Dict[str, Any]
    confidence: float
    source_page: int
    source_file: str

@dataclass
class BuildingPlan:
    """Parsed building plan data from any format"""
    building_name: str
    floors: List[str]
    rooms: List[Dict[str, Any]]
    elements: List[BuildingElement]
    dimensions: Tuple[float, float]  # width, height
    scale_factor: float
    metadata: Dict[str, Any]
    source_format: str

class BaseParser(ABC):
    """
    Abstract base class for all building plan parsers
    Ensures consistent interface across different file formats
    """
    
    def __init__(self):
        self.supported_formats = []
        self.parser_name = "BaseParser"
    
    @abstractmethod
    async def can_parse(self, file_path: str) -> bool:
        """
        Check if this parser can handle the given file
        
        Args:
            file_path: Path to the file to check
            
        Returns:
            True if this parser can handle the file
        """
        pass
    
    @abstractmethod
    async def parse_building_plan(self, file_path: str) -> BuildingPlan:
        """
        Parse a building plan file and extract building structure
        
        Args:
            file_path: Path to the building plan file
            
        Returns:
            BuildingPlan with extracted building data
        """
        pass
    
    @abstractmethod
    async def validate_file(self, file_path: str) -> Dict[str, Any]:
        """
        Validate that the file is a valid building plan
        
        Args:
            file_path: Path to the file to validate
            
        Returns:
            Validation result with status and details
        """
        pass
    
    @abstractmethod
    async def get_file_info(self, file_path: str) -> Dict[str, Any]:
        """
        Get basic information about the file without parsing
        
        Args:
            file_path: Path to the file
            
        Returns:
            File metadata and basic info
        """
        pass
    
    def get_supported_formats(self) -> List[str]:
        """Get list of file formats this parser supports"""
        return self.supported_formats
    
    def get_parser_name(self) -> str:
        """Get the name of this parser"""
        return self.parser_name
    
    async def estimate_processing_time(self, file_path: str) -> float:
        """
        Estimate how long it will take to process the file
        
        Args:
            file_path: Path to the file
            
        Returns:
            Estimated processing time in seconds
        """
        # Default implementation - can be overridden
        return 5.0  # Default 5 seconds
    
    async def get_memory_requirements(self, file_path: str) -> Dict[str, float]:
        """
        Estimate memory requirements for processing
        
        Args:
            file_path: Path to the file
            
        Returns:
            Memory requirements in MB
        """
        # Default implementation - can be overridden
        return {
            'min_memory': 50.0,   # Minimum memory in MB
            'peak_memory': 200.0, # Peak memory in MB
            'recommended': 100.0  # Recommended memory in MB
        }
