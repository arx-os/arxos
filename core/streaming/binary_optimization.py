"""
Binary Optimization for 14KB Architecture.

Implements binary encoding and compression techniques for coordinate data,
typed arrays, and geometric information to minimize bundle size.
"""

import struct
import zlib
import time
import logging
from typing import Dict, Any, List, Optional, Tuple, Union
from dataclasses import dataclass
from enum import Enum
import json
import base64
import numpy as np

logger = logging.getLogger(__name__)


class DataType(Enum):
    """Binary data types for optimization."""
    
    FLOAT32 = "float32"      # 32-bit float
    FLOAT64 = "float64"      # 64-bit float  
    INT32 = "int32"          # 32-bit integer
    INT16 = "int16"          # 16-bit integer
    INT8 = "int8"            # 8-bit integer
    UINT32 = "uint32"        # Unsigned 32-bit integer
    UINT16 = "uint16"        # Unsigned 16-bit integer
    UINT8 = "uint8"          # Unsigned 8-bit integer


@dataclass
class BinaryData:
    """Binary encoded data with metadata."""
    
    data: bytes
    data_type: DataType
    shape: Tuple[int, ...]
    compression: Optional[str] = None
    original_size: int = 0
    compressed_size: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'data': base64.b64encode(self.data).decode('ascii'),
            'data_type': self.data_type.value,
            'shape': list(self.shape),
            'compression': self.compression,
            'original_size': self.original_size,
            'compressed_size': self.compressed_size,
            'encoding': 'binary_optimized'
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BinaryData':
        """Create BinaryData from dictionary."""
        return cls(
            data=base64.b64decode(data['data'].encode('ascii')),
            data_type=DataType(data['data_type']),
            shape=tuple(data['shape']),
            compression=data.get('compression'),
            original_size=data.get('original_size', 0),
            compressed_size=data.get('compressed_size', 0)
        )


class TypedArrayEncoder:
    """
    Typed array encoder for coordinate data and geometric properties.
    
    Converts JSON arrays to binary typed arrays for space efficiency,
    following the 14KB principle's data structure optimization.
    """
    
    def __init__(self, default_precision: int = 2, compression_threshold: int = 100):
        """
        Initialize typed array encoder.
        
        Args:
            default_precision: Default decimal precision for floats
            compression_threshold: Minimum array size to apply compression
        """
        self.default_precision = default_precision
        self.compression_threshold = compression_threshold
        
        # Type mappings
        self.numpy_type_map = {
            DataType.FLOAT32: np.float32,
            DataType.FLOAT64: np.float64,
            DataType.INT32: np.int32,
            DataType.INT16: np.int16,
            DataType.INT8: np.int8,
            DataType.UINT32: np.uint32,
            DataType.UINT16: np.uint16,
            DataType.UINT8: np.uint8
        }
        
        self.struct_format_map = {
            DataType.FLOAT32: 'f',
            DataType.FLOAT64: 'd',
            DataType.INT32: 'i',
            DataType.INT16: 'h',
            DataType.INT8: 'b',
            DataType.UINT32: 'I',
            DataType.UINT16: 'H',
            DataType.UINT8: 'B'
        }
        
        logger.info(f"Initialized TypedArrayEncoder with precision: {default_precision}")
    
    def encode_coordinates(self, coordinates: List[List[float]], 
                          precision: Optional[int] = None) -> BinaryData:
        """
        Encode coordinate arrays using binary format.
        
        Args:
            coordinates: List of [x, y, z] coordinate arrays
            precision: Decimal precision for coordinates
            
        Returns:
            Binary encoded coordinate data
        """
        if not coordinates:
            return BinaryData(b'', DataType.FLOAT32, (0, 0))
        
        precision = precision or self.default_precision
        
        # Flatten and quantize coordinates
        flat_coords = []
        for coord_set in coordinates:
            for coord in coord_set:
                # Quantize to reduce precision
                quantized = round(coord, precision)
                flat_coords.append(quantized)
        
        # Determine optimal data type based on value range
        min_val, max_val = min(flat_coords), max(flat_coords)
        data_type = self._determine_optimal_type(min_val, max_val, precision)
        
        # Convert to typed array
        if data_type in [DataType.INT16, DataType.INT32]:
            # Scale floats to integers for better compression
            scale_factor = 10 ** precision
            scaled_values = [int(val * scale_factor) for val in flat_coords]
            array_data = np.array(scaled_values, dtype=self.numpy_type_map[data_type])
        else:
            array_data = np.array(flat_coords, dtype=self.numpy_type_map[data_type])
        
        # Convert to bytes
        binary_data = array_data.tobytes()
        original_size = len(binary_data)
        
        # Apply compression if beneficial
        compressed_data = binary_data
        compression = None
        
        if len(binary_data) > self.compression_threshold:
            zlib_compressed = zlib.compress(binary_data, level=6)
            if len(zlib_compressed) < len(binary_data):
                compressed_data = zlib_compressed
                compression = "zlib"
        
        shape = (len(coordinates), len(coordinates[0]) if coordinates else 0)
        
        return BinaryData(
            data=compressed_data,
            data_type=data_type,
            shape=shape,
            compression=compression,
            original_size=original_size,
            compressed_size=len(compressed_data)
        )
    
    def decode_coordinates(self, binary_data: BinaryData) -> List[List[float]]:
        """
        Decode binary coordinate data back to coordinate arrays.
        
        Args:
            binary_data: Binary encoded coordinate data
            
        Returns:
            List of [x, y, z] coordinate arrays
        """
        # Decompress if needed
        data_bytes = binary_data.data
        if binary_data.compression == "zlib":
            data_bytes = zlib.decompress(data_bytes)
        
        # Convert bytes back to numpy array
        numpy_type = self.numpy_type_map[binary_data.data_type]
        array_data = np.frombuffer(data_bytes, dtype=numpy_type)
        
        # Handle scaling for integer types
        if binary_data.data_type in [DataType.INT16, DataType.INT32]:
            scale_factor = 10 ** self.default_precision
            array_data = array_data.astype(np.float32) / scale_factor
        
        # Reshape to coordinate format
        rows, cols = binary_data.shape
        if rows == 0 or cols == 0:
            return []
        
        reshaped = array_data.reshape((rows, cols))
        return [list(row) for row in reshaped]
    
    def _determine_optimal_type(self, min_val: float, max_val: float, 
                               precision: int) -> DataType:
        """Determine optimal data type based on value range."""
        
        # Check if values can be represented as integers
        scale_factor = 10 ** precision
        scaled_min = int(min_val * scale_factor)
        scaled_max = int(max_val * scale_factor)
        
        # Try integer types for better compression
        if -32768 <= scaled_min <= scaled_max <= 32767:
            return DataType.INT16
        elif -2147483648 <= scaled_min <= scaled_max <= 2147483647:
            return DataType.INT32
        else:
            # Use float32 for large or high-precision values
            return DataType.FLOAT32
    
    def encode_property_array(self, values: List[Union[int, float, str]], 
                             property_name: str) -> BinaryData:
        """
        Encode property arrays (dimensions, materials, etc.).
        
        Args:
            values: Array of property values
            property_name: Name of property for type optimization
            
        Returns:
            Binary encoded property data
        """
        if not values:
            return BinaryData(b'', DataType.UINT8, (0,))
        
        # Determine optimal encoding based on property type
        if all(isinstance(v, bool) for v in values):
            # Boolean array - use bit packing
            return self._encode_boolean_array(values)
        
        elif all(isinstance(v, int) for v in values):
            # Integer array
            return self._encode_integer_array(values)
        
        elif all(isinstance(v, (int, float)) for v in values):
            # Numeric array
            return self._encode_numeric_array(values)
        
        elif all(isinstance(v, str) for v in values):
            # String array - use string table
            return self._encode_string_array(values)
        
        else:
            # Mixed types - fall back to JSON
            json_data = json.dumps(values).encode('utf-8')
            return BinaryData(
                data=json_data,
                data_type=DataType.UINT8,
                shape=(len(json_data),),
                compression=None,
                original_size=len(json_data),
                compressed_size=len(json_data)
            )
    
    def _encode_boolean_array(self, values: List[bool]) -> BinaryData:
        """Encode boolean array using bit packing."""
        # Pack 8 booleans per byte
        packed_bytes = []
        
        for i in range(0, len(values), 8):
            byte_chunk = values[i:i+8]
            byte_value = 0
            
            for j, bit in enumerate(byte_chunk):
                if bit:
                    byte_value |= (1 << j)
            
            packed_bytes.append(byte_value)
        
        binary_data = bytes(packed_bytes)
        
        return BinaryData(
            data=binary_data,
            data_type=DataType.UINT8,
            shape=(len(values),),
            compression=None,
            original_size=len(values),
            compressed_size=len(binary_data)
        )
    
    def _encode_integer_array(self, values: List[int]) -> BinaryData:
        """Encode integer array with optimal type."""
        min_val, max_val = min(values), max(values)
        
        # Choose smallest integer type that can hold the range
        if 0 <= min_val <= max_val <= 255:
            data_type = DataType.UINT8
        elif -128 <= min_val <= max_val <= 127:
            data_type = DataType.INT8
        elif 0 <= min_val <= max_val <= 65535:
            data_type = DataType.UINT16
        elif -32768 <= min_val <= max_val <= 32767:
            data_type = DataType.INT16
        else:
            data_type = DataType.INT32
        
        # Convert to numpy array and bytes
        numpy_type = self.numpy_type_map[data_type]
        array_data = np.array(values, dtype=numpy_type)
        binary_data = array_data.tobytes()
        
        # Try compression
        compressed_data = binary_data
        compression = None
        
        if len(binary_data) > self.compression_threshold:
            zlib_compressed = zlib.compress(binary_data, level=6)
            if len(zlib_compressed) < len(binary_data):
                compressed_data = zlib_compressed
                compression = "zlib"
        
        return BinaryData(
            data=compressed_data,
            data_type=data_type,
            shape=(len(values),),
            compression=compression,
            original_size=len(binary_data),
            compressed_size=len(compressed_data)
        )
    
    def _encode_numeric_array(self, values: List[Union[int, float]]) -> BinaryData:
        """Encode mixed numeric array."""
        # Convert all to float32 for consistency
        float_values = [float(v) for v in values]
        
        array_data = np.array(float_values, dtype=np.float32)
        binary_data = array_data.tobytes()
        
        # Try compression
        compressed_data = binary_data
        compression = None
        
        if len(binary_data) > self.compression_threshold:
            zlib_compressed = zlib.compress(binary_data, level=6)
            if len(zlib_compressed) < len(binary_data):
                compressed_data = zlib_compressed
                compression = "zlib"
        
        return BinaryData(
            data=compressed_data,
            data_type=DataType.FLOAT32,
            shape=(len(values),),
            compression=compression,
            original_size=len(binary_data),
            compressed_size=len(compressed_data)
        )
    
    def _encode_string_array(self, values: List[str]) -> BinaryData:
        """Encode string array using string table compression."""
        # Create string table
        unique_strings = list(set(values))
        string_to_index = {s: i for i, s in enumerate(unique_strings)}
        
        # Encode indices
        indices = [string_to_index[s] for s in values]
        
        # Choose index type based on unique string count
        if len(unique_strings) <= 255:
            index_type = DataType.UINT8
        else:
            index_type = DataType.UINT16
        
        # Encode indices
        numpy_type = self.numpy_type_map[index_type]
        index_array = np.array(indices, dtype=numpy_type)
        index_data = index_array.tobytes()
        
        # Encode string table
        string_table = json.dumps(unique_strings).encode('utf-8')
        
        # Combine index data and string table
        combined_data = struct.pack('I', len(index_data)) + index_data + string_table
        
        # Try compression
        compressed_data = combined_data
        compression = None
        
        if len(combined_data) > self.compression_threshold:
            zlib_compressed = zlib.compress(combined_data, level=6)
            if len(zlib_compressed) < len(combined_data):
                compressed_data = zlib_compressed
                compression = "zlib"
        
        return BinaryData(
            data=compressed_data,
            data_type=index_type,
            shape=(len(values),),
            compression=compression,
            original_size=len(combined_data),
            compressed_size=len(compressed_data)
        )


class BinaryOptimizer:
    """
    Binary optimization for ArxObjects and building components.
    
    Implements the 14KB principle's binary encoding strategies for
    coordinate data, typed arrays, and geometric properties.
    """
    
    def __init__(self, compression_level: int = 6, enable_quantization: bool = True):
        """
        Initialize binary optimizer.
        
        Args:
            compression_level: Zlib compression level (1-9)
            enable_quantization: Enable coordinate quantization
        """
        self.compression_level = compression_level
        self.enable_quantization = enable_quantization
        
        self.typed_encoder = TypedArrayEncoder()
        
        # Performance metrics
        self.metrics = {
            'objects_optimized': 0,
            'total_size_reduction_bytes': 0,
            'average_compression_ratio': 0.0,
            'optimization_time_ms': 0.0
        }
        
        logger.info(f"Initialized BinaryOptimizer with compression level: {compression_level}")
    
    def optimize_arxobject(self, arxobject_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Optimize ArxObject using binary encoding strategies.
        
        Args:
            arxobject_data: ArxObject data dictionary
            
        Returns:
            Optimized object with binary encodings
        """
        start_time = time.time()
        
        optimized_data = arxobject_data.copy()
        original_size = len(json.dumps(arxobject_data).encode('utf-8'))
        
        # Optimize geometry coordinates
        if 'geometry' in arxobject_data and isinstance(arxobject_data['geometry'], dict):
            optimized_data['geometry'] = self._optimize_geometry(arxobject_data['geometry'])
        
        # Optimize metadata arrays
        if 'metadata' in arxobject_data and isinstance(arxobject_data['metadata'], dict):
            optimized_data['metadata'] = self._optimize_metadata(arxobject_data['metadata'])
        
        # Optimize system-specific data
        system_type = arxobject_data.get('system_type', '')
        if system_type in ['electrical', 'mechanical', 'plumbing']:
            optimized_data = self._optimize_system_data(optimized_data, system_type)
        
        # Calculate compression metrics
        optimized_size = len(json.dumps(optimized_data).encode('utf-8'))
        size_reduction = original_size - optimized_size
        compression_ratio = optimized_size / original_size if original_size > 0 else 1.0
        
        # Update metrics
        self.metrics['objects_optimized'] += 1
        self.metrics['total_size_reduction_bytes'] += max(0, size_reduction)
        
        current_avg = self.metrics['average_compression_ratio']
        self.metrics['average_compression_ratio'] = (current_avg + compression_ratio) / 2
        
        elapsed_ms = (time.time() - start_time) * 1000
        current_time = self.metrics['optimization_time_ms']
        self.metrics['optimization_time_ms'] = (current_time + elapsed_ms) / 2
        
        # Add optimization metadata
        optimized_data['_binary_optimization'] = {
            'optimized': True,
            'original_size': original_size,
            'optimized_size': optimized_size,
            'compression_ratio': compression_ratio,
            'strategies_applied': self._get_applied_strategies(arxobject_data)
        }
        
        logger.debug(f"Optimized ArxObject {arxobject_data.get('id', 'unknown')}: "
                    f"{original_size} -> {optimized_size} bytes "
                    f"({compression_ratio:.2f} ratio)")
        
        return optimized_data
    
    def _optimize_geometry(self, geometry: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize geometry data using binary encoding."""
        optimized_geometry = geometry.copy()
        
        # Optimize coordinate arrays
        coordinate_fields = ['vertices', 'edges', 'faces', 'points', 'path']
        
        for field in coordinate_fields:
            if field in geometry and isinstance(geometry[field], list):
                if self._is_coordinate_array(geometry[field]):
                    binary_data = self.typed_encoder.encode_coordinates(geometry[field])
                    optimized_geometry[f"{field}_binary"] = binary_data.to_dict()
                    
                    # Keep original for compatibility (can be removed in production)
                    # del optimized_geometry[field]
        
        # Optimize dimension arrays
        dimension_fields = ['length', 'width', 'height', 'radius', 'diameter']
        
        for field in dimension_fields:
            if field in geometry and isinstance(geometry[field], (list, tuple)):
                binary_data = self.typed_encoder.encode_property_array(
                    list(geometry[field]), field
                )
                optimized_geometry[f"{field}_binary"] = binary_data.to_dict()
        
        return optimized_geometry
    
    def _optimize_metadata(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize metadata using appropriate encoding strategies."""
        optimized_metadata = metadata.copy()
        
        # Optimize string arrays (materials, manufacturers, etc.)
        string_array_fields = ['materials', 'finishes', 'manufacturers', 'model_numbers']
        
        for field in string_array_fields:
            if field in metadata and isinstance(metadata[field], list):
                if all(isinstance(item, str) for item in metadata[field]):
                    binary_data = self.typed_encoder.encode_property_array(
                        metadata[field], field
                    )
                    optimized_metadata[f"{field}_binary"] = binary_data.to_dict()
        
        # Optimize boolean flags
        boolean_fields = ['is_energized', 'is_accessible', 'requires_maintenance']
        boolean_values = []
        boolean_keys = []
        
        for field in boolean_fields:
            if field in metadata and isinstance(metadata[field], bool):
                boolean_values.append(metadata[field])
                boolean_keys.append(field)
        
        if boolean_values:
            binary_data = self.typed_encoder.encode_property_array(boolean_values, 'boolean_flags')
            optimized_metadata['boolean_flags_binary'] = {
                'data': binary_data.to_dict(),
                'keys': boolean_keys
            }
            
            # Remove individual boolean fields
            for key in boolean_keys:
                optimized_metadata.pop(key, None)
        
        return optimized_metadata
    
    def _optimize_system_data(self, data: Dict[str, Any], system_type: str) -> Dict[str, Any]:
        """Optimize system-specific data based on type."""
        optimized_data = data.copy()
        
        if system_type == 'electrical':
            # Optimize electrical properties
            electrical_fields = ['voltage', 'amperage', 'wattage', 'phases']
            
            for field in electrical_fields:
                if field in data and isinstance(data[field], (list, tuple)):
                    binary_data = self.typed_encoder.encode_property_array(
                        list(data[field]), field
                    )
                    optimized_data[f"{field}_binary"] = binary_data.to_dict()
        
        elif system_type == 'mechanical':
            # Optimize mechanical properties  
            mechanical_fields = ['pressure', 'temperature', 'flow_rate', 'cfm']
            
            for field in mechanical_fields:
                if field in data and isinstance(data[field], (list, tuple)):
                    binary_data = self.typed_encoder.encode_property_array(
                        list(data[field]), field
                    )
                    optimized_data[f"{field}_binary"] = binary_data.to_dict()
        
        elif system_type == 'plumbing':
            # Optimize plumbing properties
            plumbing_fields = ['pipe_diameter', 'flow_rate', 'pressure_rating']
            
            for field in plumbing_fields:
                if field in data and isinstance(data[field], (list, tuple)):
                    binary_data = self.typed_encoder.encode_property_array(
                        list(data[field]), field
                    )
                    optimized_data[f"{field}_binary"] = binary_data.to_dict()
        
        return optimized_data
    
    def _is_coordinate_array(self, data: List[Any]) -> bool:
        """Check if array contains coordinate data."""
        if not data or not isinstance(data, list):
            return False
        
        # Check if it's array of arrays with numeric values
        if isinstance(data[0], list):
            return all(
                isinstance(coord, list) and 
                len(coord) >= 2 and 
                all(isinstance(val, (int, float)) for val in coord)
                for coord in data[:5]  # Check first 5 items
            )
        
        return False
    
    def _get_applied_strategies(self, original_data: Dict[str, Any]) -> List[str]:
        """Get list of optimization strategies applied to object."""
        strategies = []
        
        if 'geometry' in original_data:
            strategies.append('geometry_binary_encoding')
        
        if 'metadata' in original_data:
            strategies.append('metadata_optimization')
        
        system_type = original_data.get('system_type', '')
        if system_type in ['electrical', 'mechanical', 'plumbing']:
            strategies.append(f'{system_type}_system_optimization')
        
        return strategies
    
    def decompress_object(self, optimized_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Decompress binary-optimized object back to standard format.
        
        Args:
            optimized_data: Binary-optimized object data
            
        Returns:
            Standard object data
        """
        if not optimized_data.get('_binary_optimization', {}).get('optimized', False):
            return optimized_data  # Not optimized
        
        decompressed_data = optimized_data.copy()
        
        # Remove optimization metadata
        decompressed_data.pop('_binary_optimization', None)
        
        # Decompress geometry
        if 'geometry' in decompressed_data:
            decompressed_data['geometry'] = self._decompress_geometry(decompressed_data['geometry'])
        
        # Decompress metadata
        if 'metadata' in decompressed_data:
            decompressed_data['metadata'] = self._decompress_metadata(decompressed_data['metadata'])
        
        return decompressed_data
    
    def _decompress_geometry(self, geometry: Dict[str, Any]) -> Dict[str, Any]:
        """Decompress binary-encoded geometry data."""
        decompressed_geometry = geometry.copy()
        
        # Decompress coordinate arrays
        binary_fields = [key for key in geometry.keys() if key.endswith('_binary')]
        
        for binary_field in binary_fields:
            if binary_field in geometry:
                original_field = binary_field.replace('_binary', '')
                
                binary_data = BinaryData.from_dict(geometry[binary_field])
                
                if 'coordinates' in binary_field or original_field in ['vertices', 'edges', 'points']:
                    decompressed_coords = self.typed_encoder.decode_coordinates(binary_data)
                    decompressed_geometry[original_field] = decompressed_coords
                
                # Remove binary field
                del decompressed_geometry[binary_field]
        
        return decompressed_geometry
    
    def _decompress_metadata(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Decompress binary-encoded metadata."""
        decompressed_metadata = metadata.copy()
        
        # Handle boolean flags
        if 'boolean_flags_binary' in metadata:
            boolean_data = metadata['boolean_flags_binary']
            binary_obj = BinaryData.from_dict(boolean_data['data'])
            keys = boolean_data['keys']
            
            # Decode boolean array (simplified - would need full implementation)
            boolean_values = [True] * len(keys)  # Placeholder
            
            for key, value in zip(keys, boolean_values):
                decompressed_metadata[key] = value
            
            del decompressed_metadata['boolean_flags_binary']
        
        # Remove other binary fields (simplified)
        binary_fields = [key for key in metadata.keys() if key.endswith('_binary')]
        for field in binary_fields:
            del decompressed_metadata[field]
        
        return decompressed_metadata
    
    def get_optimization_stats(self) -> Dict[str, Any]:
        """Get binary optimization statistics."""
        return {
            'optimization_metrics': self.metrics.copy(),
            'compression_level': self.compression_level,
            'quantization_enabled': self.enable_quantization,
            'encoder_settings': {
                'default_precision': self.typed_encoder.default_precision,
                'compression_threshold': self.typed_encoder.compression_threshold
            }
        }