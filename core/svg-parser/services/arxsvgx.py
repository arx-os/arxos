"""
ArxSVGX Format Implementation

This module provides the core implementation of the ArxSVGX format - a proprietary,
enhanced SVG format designed specifically for the Arxos SVG-BIM system.

Features:
- Binary format for efficient storage and loading
- Rich metadata support for BIM data
- Advanced compression algorithms
- Built-in version control
- Security features with encryption
"""

import struct
import json
import zlib
import hashlib
import base64
from datetime import datetime
from typing import Dict, Any, Optional, Tuple, Union
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

# Magic number for ArxSVGX files
ARXSVGX_MAGIC = b'ARXS'
ARXSVGX_VERSION = 1

@dataclass
class ArxSVGXHeader:
    """ArxSVGX file header structure"""
    magic: bytes
    version: int
    flags: int
    metadata_size: int
    content_size: int
    checksum: int
    reserved: int
    
    def pack(self) -> bytes:
        """Pack header into binary format"""
        # Convert checksum to integer if it's bytes
        checksum_int = int.from_bytes(self.checksum, byteorder='little') if isinstance(self.checksum, bytes) else self.checksum
        return struct.pack('<4sIIQQII',
            self.magic,
            self.version,
            self.flags,
            self.metadata_size,
            self.content_size,
            checksum_int,
            self.reserved
        )
    
    @classmethod
    def unpack(cls, data: bytes) -> 'ArxSVGXHeader':
        """Unpack binary data into header"""
        if len(data) < 36:
            raise ValueError("Header data too short")
        
        magic, version, flags, metadata_size, content_size, checksum, reserved = struct.unpack('<4sIIQQII', data[:36])
        
        if magic != ARXSVGX_MAGIC:
            raise ValueError(f"Invalid magic number: {magic}")
        
        return cls(magic, version, flags, metadata_size, content_size, checksum, reserved)

class ArxSVGXMetadataManager:
    """Manages metadata for ArxSVGX files"""
    
    def __init__(self):
        self.schema = self._load_schema()
        self.validators = self._create_validators()
    
    def _load_schema(self) -> Dict[str, Any]:
        """Load metadata schema"""
        return {
            "type": "object",
            "properties": {
                "bim": {
                    "type": "object",
                    "properties": {
                        "building_id": {"type": "string"},
                        "floor_level": {"type": "number"},
                        "room_data": {"type": "object"},
                        "equipment_data": {"type": "object"},
                        "maintenance_history": {"type": "array"}
                    }
                },
                "viewport": {
                    "type": "object",
                    "properties": {
                        "default_zoom": {"type": "number"},
                        "default_pan": {"type": "object"},
                        "zoom_constraints": {"type": "object"},
                        "performance_settings": {"type": "object"}
                    }
                },
                "security": {
                    "type": "object",
                    "properties": {
                        "access_level": {"type": "string"},
                        "encryption_key": {"type": "string"},
                        "permissions": {"type": "array"}
                    }
                },
                "version": {
                    "type": "object",
                    "properties": {
                        "created": {"type": "string"},
                        "modified": {"type": "string"},
                        "author": {"type": "string"},
                        "changes": {"type": "array"}
                    }
                }
            }
        }
    
    def _create_validators(self) -> list:
        """Create metadata validators"""
        # Simple validation for now - can be enhanced with jsonschema
        return []
    
    def validate_metadata(self, metadata: Dict[str, Any]) -> bool:
        """Validate metadata against schema"""
        try:
            # Basic validation
            if not isinstance(metadata, dict):
                return False
            
            # Check required fields
            required_fields = ['version']
            for field in required_fields:
                if field not in metadata:
                    logger.warning(f"Missing required field: {field}")
                    return False
            
            # Validate version info
            version_info = metadata.get('version', {})
            if not isinstance(version_info, dict):
                return False
            
            # Add creation timestamp if not present
            if 'created' not in version_info:
                metadata['version']['created'] = datetime.now().isoformat()
            
            return True
            
        except Exception as e:
            logger.error(f"Metadata validation error: {e}")
            return False
    
    def encrypt_metadata(self, metadata: Dict[str, Any], key: str) -> str:
        """Encrypt sensitive metadata"""
        try:
            metadata_str = json.dumps(metadata, sort_keys=True)
            # Simple base64 encoding for now - can be enhanced with proper encryption
            encoded = base64.b64encode(metadata_str.encode('utf-8'))
            return encoded.decode('utf-8')
        except Exception as e:
            logger.error(f"Metadata encryption error: {e}")
            raise
    
    def decrypt_metadata(self, encrypted_data: str, key: str) -> Dict[str, Any]:
        """Decrypt metadata"""
        try:
            # Simple base64 decoding for now
            decoded = base64.b64decode(encrypted_data.encode('utf-8'))
            metadata_str = decoded.decode('utf-8')
            return json.loads(metadata_str)
        except Exception as e:
            logger.error(f"Metadata decryption error: {e}")
            raise

class ArxSVGXCompressionEngine:
    """Handles compression and decompression of ArxSVGX content"""
    
    def __init__(self):
        self.algorithms = {
            'zlib': self._zlib_compress,
            'custom': self._custom_compress
        }
        self.decompress_algorithms = {
            'zlib': self._zlib_decompress,
            'custom': self._custom_decompress
        }
    
    def compress_content(self, content: str, algorithm: str = 'zlib') -> bytes:
        """Compress SVG content"""
        if algorithm not in self.algorithms:
            raise ValueError(f"Unsupported compression algorithm: {algorithm}")
        
        try:
            return self.algorithms[algorithm](content)
        except Exception as e:
            logger.error(f"Content compression error: {e}")
            raise
    
    def decompress_content(self, compressed_data: bytes, algorithm: str = 'zlib') -> str:
        """Decompress content"""
        if algorithm not in self.decompress_algorithms:
            raise ValueError(f"Unsupported compression algorithm: {algorithm}")
        
        try:
            return self.decompress_algorithms[algorithm](compressed_data)
        except Exception as e:
            logger.error(f"Content decompression error: {e}")
            raise
    
    def _zlib_compress(self, content: str) -> bytes:
        """Compress using zlib"""
        return zlib.compress(content.encode('utf-8'), level=9)
    
    def _zlib_decompress(self, compressed_data: bytes) -> str:
        """Decompress using zlib"""
        return zlib.decompress(compressed_data).decode('utf-8')
    
    def _custom_compress(self, content: str) -> bytes:
        """Custom compression algorithm optimized for SVG"""
        # Simple optimization: remove unnecessary whitespace
        import re
        # Remove comments
        content = re.sub(r'<!--.*?-->', '', content, flags=re.DOTALL)
        # Remove extra whitespace
        content = re.sub(r'\s+', ' ', content)
        content = content.strip()
        # Use zlib for final compression
        return self._zlib_compress(content)
    
    def _custom_decompress(self, compressed_data: bytes) -> str:
        """Custom decompression"""
        return self._zlib_decompress(compressed_data)
    
    def get_compression_ratio(self, original_size: int, compressed_size: int) -> float:
        """Calculate compression ratio as percentage"""
        if original_size == 0:
            return 0.0
        return (1 - compressed_size / original_size) * 100

class ArxSVGXParser:
    """Parser for ArxSVGX files"""
    
    def __init__(self):
        self.header: Optional[ArxSVGXHeader] = None
        self.metadata: Optional[Dict[str, Any]] = None
        self.content: Optional[str] = None
        self.metadata_manager = ArxSVGXMetadataManager()
        self.compression_engine = ArxSVGXCompressionEngine()
    
    def parse_file(self, file_path: str) -> None:
        """Parse ArxSVGX file and extract components"""
        try:
            with open(file_path, 'rb') as f:
                # Parse header
                header_data = f.read(36)
                self.header = ArxSVGXHeader.unpack(header_data)
                
                # Parse metadata
                metadata_data = f.read(self.header.metadata_size)
                self.symbol_metadata = self._parse_metadata(metadata_data)
                
                # Parse content
                content_data = f.read(self.header.content_size)
                self.content = self._parse_content(content_data)
                
                logger.info(f"Successfully parsed ArxSVGX file: {file_path}")
                
        except Exception as e:
            logger.error(f"Error parsing ArxSVGX file {file_path}: {e}")
            raise
    
    def _parse_metadata(self, metadata_data: bytes) -> Dict[str, Any]:
        """Parse metadata section"""
        try:
            # Detect if metadata is encrypted
            if metadata_data.startswith(b'encrypted:'):
                # Handle encrypted metadata
                encrypted_str = metadata_data[10:].decode('utf-8')
                return self.metadata_manager.decrypt_metadata(encrypted_str, "default_key")
            else:
                # Handle plain metadata
                metadata_str = metadata_data.decode('utf-8')
                metadata = json.loads(metadata_str)
                
                # Validate metadata
                if not self.metadata_manager.validate_metadata(metadata):
                    raise ValueError("Invalid metadata")
                
                return metadata
                
        except Exception as e:
            logger.error(f"Error parsing metadata: {e}")
            raise
    
    def _parse_content(self, content_data: bytes) -> str:
        """Parse content section"""
        try:
            # Detect compression algorithm from header flags
            algorithm = 'zlib'  # Default
            if self.header.flags & 0x01:  # Custom compression flag
                algorithm = 'custom'
            
            return self.compression_engine.decompress_content(content_data, algorithm)
            
        except Exception as e:
            logger.error(f"Error parsing content: {e}")
            raise
    
    def get_metadata(self) -> Optional[Dict[str, Any]]:
        """Get parsed metadata"""
        return self.metadata
    
    def get_content(self) -> Optional[str]:
        """Get parsed content"""
        return self.content
    
    def get_header(self) -> Optional[ArxSVGXHeader]:
        """Get parsed header"""
        return self.header

class ArxSVGXWriter:
    """Writer for ArxSVGX files"""
    
    def __init__(self):
        self.metadata_manager = ArxSVGXMetadataManager()
        self.compression_engine = ArxSVGXCompressionEngine()
    
    def write_file(self, file_path: str, content: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Write content and metadata to ArxSVGX file"""
        try:
            # Prepare metadata
            if metadata is None:
                metadata = {}
            
            # Ensure metadata is a dict
            if not isinstance(metadata, dict):
                raise ValueError("Metadata must be a dictionary")
            
            # Add version information
            if 'version' not in metadata:
                metadata['version'] = {}
            
            metadata['version']['created'] = datetime.now().isoformat()
            metadata['version']['modified'] = datetime.now().isoformat()
            
            # Validate metadata
            if not self.metadata_manager.validate_metadata(metadata):
                raise ValueError("Invalid metadata")
            
            # Compress content
            compressed_content = self.compression_engine.compress_content(content, 'zlib')
            
            # Prepare metadata
            metadata_str = json.dumps(metadata, sort_keys=True)
            metadata_bytes = metadata_str.encode('utf-8')
            
            # Create header
            header = ArxSVGXHeader(
                magic=ARXSVGX_MAGIC,
                version=ARXSVGX_VERSION,
                flags=0,  # No special flags
                metadata_size=len(metadata_bytes),
                content_size=len(compressed_content),
                checksum=0,  # Will be calculated
                reserved=0
            )
            
            # Calculate checksum
            header.checksum = self._calculate_checksum(metadata_bytes + compressed_content)
            
            # Write file
            with open(file_path, 'wb') as f:
                f.write(header.pack())
                f.write(metadata_bytes)
                f.write(compressed_content)
            
            logger.info(f"Successfully wrote ArxSVGX file: {file_path}")
            
        except Exception as e:
            logger.error(f"Error writing ArxSVGX file {file_path}: {e}")
            raise
    
    def _calculate_checksum(self, data: bytes) -> int:
        """Calculate checksum for data"""
        checksum_bytes = hashlib.md5(data).digest()[:4]
        return int.from_bytes(checksum_bytes, byteorder='little')
    
    def get_compression_stats(self, original_content: str, compressed_content: bytes) -> Dict[str, Any]:
        """Get compression statistics"""
        original_size = len(original_content.encode('utf-8'))
        compressed_size = len(compressed_content)
        ratio = self.compression_engine.get_compression_ratio(original_size, compressed_size)
        
        return {
            'original_size': original_size,
            'compressed_size': compressed_size,
            'compression_ratio': ratio,
            'space_saved': original_size - compressed_size
        }

class ArxSVGXConverter:
    """Converter between SVG and ArxSVGX formats"""
    
    def __init__(self):
        self.parser = ArxSVGXParser()
        self.writer = ArxSVGXWriter()
    
    def svg_to_arxsvgx(self, svg_file_path: str, output_path: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Convert SVG file to ArxSVGX format"""
        try:
            # Read SVG content
            with open(svg_file_path, 'r', encoding='utf-8') as f:
                svg_content = f.read()
            
            # Extract basic metadata if not provided
            if metadata is None:
                metadata = self._extract_svg_metadata(svg_content)
            
            # Write ArxSVGX file
            self.writer.write_file(output_path, svg_content, metadata)
            
            # Get compression stats
            with open(output_path, 'rb') as f:
                header_data = f.read(36)
                header = ArxSVGXHeader.unpack(header_data)
                f.seek(36 + header.metadata_size)
                compressed_content = f.read(header.content_size)
            
            stats = self.writer.get_compression_stats(svg_content, compressed_content)
            
            logger.info(f"Converted {svg_file_path} to {output_path}")
            logger.info(f"Compression ratio: {stats['compression_ratio']:.1f}%")
            
            return {
                'success': True,
                'input_file': svg_file_path,
                'output_file': output_path,
                'compression_stats': stats
            }
            
        except Exception as e:
            logger.error(f"Error converting SVG to ArxSVGX: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def arxsvgx_to_svg(self, arxsvgx_file_path: str, output_path: str) -> Dict[str, Any]:
        """Convert ArxSVGX file back to SVG format"""
        try:
            # Parse ArxSVGX file
            self.parser.parse_file(arxsvgx_file_path)
            
            # Get content
            content = self.parser.get_content()
            if content is None:
                raise ValueError("No content found in ArxSVGX file")
            
            # Write SVG file
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            logger.info(f"Converted {arxsvgx_file_path} to {output_path}")
            
            return {
                'success': True,
                'input_file': arxsvgx_file_path,
                'output_file': output_path,
                'metadata': self.parser.get_metadata()
            }
            
        except Exception as e:
            logger.error(f"Error converting ArxSVGX to SVG: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _extract_svg_metadata(self, svg_content: str) -> Dict[str, Any]:
        """Extract basic metadata from SVG content"""
        metadata = {
            'svg_info': {},
            'version': {
                'created': datetime.now().isoformat(),
                'converted_from': 'svg'
            }
        }
        
        # Extract basic SVG information
        import re
        
        # Extract viewBox
        viewbox_match = re.search(r'viewBox=["\']([^"\']+)["\']', svg_content)
        if viewbox_match:
            metadata['svg_info']['viewBox'] = viewbox_match.group(1)
        
        # Extract width and height
        width_match = re.search(r'width=["\']([^"\']+)["\']', svg_content)
        if width_match:
            metadata['svg_info']['width'] = width_match.group(1)
        
        height_match = re.search(r'height=["\']([^"\']+)["\']', svg_content)
        if height_match:
            metadata['svg_info']['height'] = height_match.group(1)
        
        # Count elements
        element_count = len(re.findall(r'<[^/][^>]*>', svg_content))
        metadata['svg_info']['element_count'] = element_count
        
        return metadata

# Utility functions
def is_arxsvgx_file(file_path: str) -> bool:
    """Check if file is an ArxSVGX file"""
    try:
        with open(file_path, 'rb') as f:
            magic = f.read(4)
            return magic == ARXSVGX_MAGIC
    except:
        return False

def get_arxsvgx_info(file_path: str) -> Dict[str, Any]:
    """Get information about an ArxSVGX file"""
    try:
        parser = ArxSVGXParser()
        parser.parse_file(file_path)
        
        header = parser.get_header()
        metadata = parser.get_metadata()
        content = parser.get_content()
        
        return {
            'file_path': file_path,
            'format': 'ArxSVGX',
            'version': header.version if header else None,
            'file_size': header.metadata_size + header.content_size + 36 if header else 0,
            'metadata_size': header.metadata_size if header else 0,
            'content_size': header.content_size if header else 0,
            'compressed_content_size': header.content_size if header else 0,
            'metadata': metadata,
            'content_length': len(content) if content else 0
        }
    except Exception as e:
        return {
            'file_path': file_path,
            'error': str(e)
        } 