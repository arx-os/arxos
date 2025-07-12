from pydantic import BaseModel, constr, Field
import re
from typing import List, Dict, Any, Optional

base64_pattern = r'^[A-Za-z0-9+/=\s]+$'

class SymbolData(BaseModel):
    """Model for symbol data including funding source."""
    symbol_id: str = Field(..., description="Unique symbol identifier")
    display_name: str = Field(..., description="Human-readable symbol name")
    system: str = Field(..., description="Building system category")
    category: Optional[str] = Field(None, description="Symbol category")
    subcategory: Optional[str] = Field(None, description="Symbol subcategory")
    description: Optional[str] = Field(None, description="Symbol description")
    svg_content: Optional[str] = Field(None, description="SVG content for the symbol")
    properties: List[Dict[str, Any]] = Field(default_factory=list, description="Symbol properties")
    connections: List[Dict[str, Any]] = Field(default_factory=list, description="Symbol connections")
    tags: List[str] = Field(default_factory=list, description="Symbol tags")
    funding_source: Optional[str] = Field(None, description="Source of funding for this asset")
    dimensions: Optional[Dict[str, Any]] = Field(None, description="Symbol dimensions")
    default_scale: Optional[float] = Field(None, description="Default scale factor")

class ParseRequest(BaseModel):
    """Request model for SVG parsing."""
    svg_content: str = Field(..., description="SVG content to parse")
    building_id: Optional[str] = Field(None, description="Building identifier")
    floor_label: Optional[str] = Field(None, description="Floor label")

class ParseResponse(BaseModel):
    """Response model for SVG parsing."""
    message: str = Field(..., description="Parsing result message")
    rooms: List[Dict[str, Any]] = Field(default_factory=list, description="Extracted rooms")
    walls: List[Dict[str, Any]] = Field(default_factory=list, description="Extracted walls")
    doors: List[Dict[str, Any]] = Field(default_factory=list, description="Extracted doors")
    devices: List[Dict[str, Any]] = Field(default_factory=list, description="Extracted devices")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Extracted metadata")

class SymbolRecognitionRequest(BaseModel):
    """Request model for symbol recognition."""
    content: str = Field(..., description="Text or SVG content to analyze")
    content_type: str = Field(default="text", description="Type of content: 'text' or 'svg'")
    confidence_threshold: float = Field(default=0.5, description="Minimum confidence for recognition")

class SymbolRecognitionResponse(BaseModel):
    """Response model for symbol recognition."""
    recognized_symbols: List[Dict[str, Any]] = Field(..., description="List of recognized symbols with funding_source")
    total_recognized: int = Field(..., description="Total number of recognized symbols")
    symbol_library_info: Dict[str, Any] = Field(..., description="Symbol library information")
    confidence_threshold: float = Field(..., description="Confidence threshold used")
    content_type: str = Field(..., description="Type of content analyzed")

class SymbolRenderRequest(BaseModel):
    """Request model for symbol rendering."""
    svg_content: str = Field(..., description="SVG content to render symbols into")
    building_id: str = Field(..., description="Building identifier")
    floor_label: str = Field(..., description="Floor label")
    symbol_ids: Optional[List[str]] = Field(None, description="Specific symbol IDs to render")

class SymbolRenderResponse(BaseModel):
    """Response model for symbol rendering."""
    svg: str = Field(..., description="Updated SVG with rendered symbols")
    rendered_symbols: List[Dict[str, Any]] = Field(..., description="List of rendered symbols with funding_source")
    total_recognized: int = Field(..., description="Total symbols recognized")
    total_rendered: int = Field(..., description="Total symbols rendered")
    building_id: str = Field(..., description="Building identifier")
    floor_label: str = Field(..., description="Floor label")

class BIMExtractionRequest(BaseModel):
    """Request model for BIM extraction."""
    svg_content: str = Field(..., description="SVG content with rendered symbols")
    building_id: Optional[str] = Field(None, description="Building identifier")
    floor_label: Optional[str] = Field(None, description="Floor label")

class BIMExtractionResponse(BaseModel):
    """Response model for BIM extraction."""
    bim_data: Dict[str, Any] = Field(..., description="Extracted BIM data")
    extraction_summary: Dict[str, Any] = Field(..., description="Summary of extraction results")

class SymbolPositionUpdateRequest(BaseModel):
    """Request model for updating symbol position."""
    svg_content: str = Field(..., description="SVG content")
    object_id: str = Field(..., description="Object ID of the symbol to update")
    x: float = Field(..., description="New X coordinate")
    y: float = Field(..., description="New Y coordinate")

class SymbolPositionUpdateResponse(BaseModel):
    """Response model for symbol position update."""
    svg: str = Field(..., description="Updated SVG content")
    object_id: str = Field(..., description="Object ID of updated symbol")
    new_position: Dict[str, float] = Field(..., description="New position coordinates")
    updated_at: str = Field(..., description="Timestamp of update")

class SymbolRemovalRequest(BaseModel):
    """Request model for removing a symbol."""
    svg_content: str = Field(..., description="SVG content")
    object_id: str = Field(..., description="Object ID of the symbol to remove")

class SymbolRemovalResponse(BaseModel):
    """Response model for symbol removal."""
    svg: str = Field(..., description="Updated SVG content")
    object_id: str = Field(..., description="Object ID of removed symbol")
    removed_at: str = Field(..., description="Timestamp of removal")

class SymbolLibraryRequest(BaseModel):
    """Request model for symbol library queries."""
    system: Optional[str] = Field(None, description="Filter by building system")
    category: Optional[str] = Field(None, description="Filter by category")
    search: Optional[str] = Field(None, description="Search in symbol names and descriptions")

class SymbolLibraryResponse(BaseModel):
    """Response model for symbol library queries."""
    library_info: Dict[str, Any] = Field(..., description="Symbol library information")
    symbols: List[SymbolData] = Field(..., description="Filtered symbols with funding_source")
    total_symbols: int = Field(..., description="Total number of symbols")
    filters_applied: Dict[str, Any] = Field(..., description="Filters that were applied")

class AutoRecognitionRequest(BaseModel):
    """Request model for automatic recognition and rendering."""
    building_id: str = Field(..., description="Building identifier")
    floor_label: str = Field(..., description="Floor label")
    confidence_threshold: float = Field(default=0.5, description="Minimum confidence for recognition")

class AutoRecognitionResponse(BaseModel):
    """Response model for automatic recognition and rendering."""
    svg: str = Field(..., description="Generated SVG with rendered symbols")
    recognized_symbols: List[Dict[str, Any]] = Field(..., description="List of recognized symbols with funding_source")
    rendered_symbols: List[Dict[str, Any]] = Field(..., description="List of rendered symbols with funding_source")
    recognition_stats: Dict[str, Any] = Field(..., description="Recognition statistics")
    summary: Optional[Dict[str, Any]] = Field(None, description="Processing summary")
    building_id: str = Field(..., description="Building identifier")
    floor_label: str = Field(..., description="Floor label")
    file_type: str = Field(..., description="Type of file processed") 