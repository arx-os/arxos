"""
Unit tests for ArxSVGX format implementation

This module provides comprehensive testing for the ArxSVGX format,
including header parsing, metadata management, compression, and conversion.
"""

import unittest
import tempfile
import os
import json
import time
from unittest.mock import patch, MagicMock

from services.arxsvgx import (
    ArxSVGXHeader,
    ArxSVGXMetadataManager,
    ArxSVGXCompressionEngine,
    ArxSVGXParser,
    ArxSVGXWriter,
    ArxSVGXConverter,
    is_arxsvgx_file,
    get_arxsvgx_info,
    ARXSVGX_MAGIC,
    ARXSVGX_VERSION
)

class TestArxSVGXHeader(unittest.TestCase):
    """Test ArxSVGX header functionality"""
    
    def setUp(self):
        self.header = ArxSVGXHeader(
            magic=ARXSVGX_MAGIC,
            version=ARXSVGX_VERSION,
            flags=0,
            metadata_size=100,
            content_size=1000,
            checksum=12345,
            reserved=0
        )
    
    def test_header_pack(self):
        """Test header packing"""
        packed = self.header.pack()
        self.assertEqual(len(packed), 36)  # 4s + I + I + Q + Q + I + I = 36 bytes
        self.assertEqual(packed[:4], ARXSVGX_MAGIC)
    
    def test_header_unpack(self):
        """Test header unpacking"""
        packed = self.header.pack()
        unpacked = ArxSVGXHeader.unpack(packed)
        
        self.assertEqual(unpacked.magic, self.header.magic)
        self.assertEqual(unpacked.version, self.header.version)
        self.assertEqual(unpacked.flags, self.header.flags)
        self.assertEqual(unpacked.metadata_size, self.header.metadata_size)
        self.assertEqual(unpacked.content_size, self.header.content_size)
        self.assertEqual(unpacked.checksum, self.header.checksum)
        self.assertEqual(unpacked.reserved, self.header.reserved)
    
    def test_header_unpack_invalid_magic(self):
        """Test header unpacking with invalid magic number"""
        invalid_header = ArxSVGXHeader(
            magic=b'INVL',
            version=ARXSVGX_VERSION,
            flags=0,
            metadata_size=100,
            content_size=1000,
            checksum=12345,
            reserved=0
        )
        packed = invalid_header.pack()
        
        with self.assertRaises(ValueError):
            ArxSVGXHeader.unpack(packed)
    
    def test_header_unpack_short_data(self):
        """Test header unpacking with insufficient data"""
        with self.assertRaises(ValueError):
            ArxSVGXHeader.unpack(b'short')

class TestArxSVGXMetadataManager(unittest.TestCase):
    """Test metadata management functionality"""
    
    def setUp(self):
        self.manager = ArxSVGXMetadataManager()
        self.valid_metadata = {
            'version': {
                'created': '2024-01-01T00:00:00',
                'modified': '2024-01-01T00:00:00',
                'author': 'test_user'
            },
            'bim': {
                'building_id': 'test_building',
                'floor_level': 1
            }
        }
    
    def test_validate_metadata_valid(self):
        """Test metadata validation with valid data"""
        result = self.manager.validate_metadata(self.valid_metadata)
        self.assertTrue(result)
    
    def test_validate_metadata_invalid_type(self):
        """Test metadata validation with invalid type"""
        result = self.manager.validate_metadata("not a dict")
        self.assertFalse(result)
    
    def test_validate_metadata_missing_version(self):
        """Test metadata validation with missing version"""
        invalid_metadata = {'bim': {'building_id': 'test'}}
        result = self.manager.validate_metadata(invalid_metadata)
        self.assertFalse(result)
    
    def test_validate_metadata_adds_created_timestamp(self):
        """Test that validation adds creation timestamp if missing"""
        metadata = {'version': {}}
        result = self.manager.validate_metadata(metadata)
        self.assertTrue(result)
        self.assertIn('created', metadata['version'])
    
    def test_encrypt_decrypt_metadata(self):
        """Test metadata encryption and decryption"""
        encrypted = self.manager.encrypt_metadata(self.valid_metadata, "test_key")
        decrypted = self.manager.decrypt_metadata(encrypted, "test_key")
        
        self.assertEqual(self.valid_metadata, decrypted)

class TestArxSVGXCompressionEngine(unittest.TestCase):
    """Test compression engine functionality"""
    
    def setUp(self):
        self.engine = ArxSVGXCompressionEngine()
        self.test_content = """
        <svg width="100" height="100">
            <rect x="10" y="10" width="80" height="80" fill="red"/>
            <circle cx="50" cy="50" r="30" fill="blue"/>
        </svg>
        """
    
    def test_zlib_compression(self):
        """Test zlib compression and decompression"""
        compressed = self.engine.compress_content(self.test_content, 'zlib')
        decompressed = self.engine.decompress_content(compressed, 'zlib')
        
        self.assertEqual(self.test_content, decompressed)
    
    def test_custom_compression(self):
        """Test custom compression and decompression"""
        compressed = self.engine.compress_content(self.test_content, 'custom')
        decompressed = self.engine.decompress_content(compressed, 'custom')
        
        # Custom compression removes whitespace, so we need to normalize
        normalized_original = ' '.join(self.test_content.split())
        normalized_decompressed = ' '.join(decompressed.split())
        self.assertEqual(normalized_original, normalized_decompressed)
    
    def test_unsupported_algorithm(self):
        """Test error handling for unsupported algorithms"""
        with self.assertRaises(ValueError):
            self.engine.compress_content(self.test_content, 'unsupported')
        
        with self.assertRaises(ValueError):
            self.engine.decompress_content(b'test', 'unsupported')
    
    def test_compression_ratio(self):
        """Test compression ratio calculation"""
        compressed = self.engine.compress_content(self.test_content, 'zlib')
        ratio = self.engine.get_compression_ratio(len(self.test_content), len(compressed))
        
        self.assertGreater(ratio, 0)
        self.assertLess(ratio, 100)
    
    def test_compression_ratio_zero_size(self):
        """Test compression ratio with zero size"""
        ratio = self.engine.get_compression_ratio(0, 100)
        self.assertEqual(ratio, 0.0)

class TestArxSVGXParser(unittest.TestCase):
    """Test ArxSVGX parser functionality"""
    
    def setUp(self):
        self.parser = ArxSVGXParser()
        self.test_svg = '<svg width="100" height="100"><rect x="10" y="10" width="80" height="80"/></svg>'
        self.test_metadata = {
            'version': {
                'created': '2024-01-01T00:00:00',
                'author': 'test_user'
            }
        }
    
    def test_parse_file(self):
        """Test parsing a complete ArxSVGX file"""
        with tempfile.NamedTemporaryFile(suffix='.arxsvgx', delete=False) as f:
            f.close()  # Close the file handle immediately
            
            try:
                # Create a simple ArxSVGX file
                writer = ArxSVGXWriter()
                writer.write_file(f.name, self.test_svg, self.test_metadata)
                
                # Parse the file
                self.parser.parse_file(f.name)
                
                # Verify parsing results
                self.assertIsNotNone(self.parser.header)
                self.assertIsNotNone(self.parser.metadata)
                self.assertIsNotNone(self.parser.content)
                
                self.assertEqual(self.parser.header.magic, ARXSVGX_MAGIC)
                self.assertEqual(self.parser.content, self.test_svg)
                
            finally:
                # Cleanup
                try:
                    os.unlink(f.name)
                except PermissionError:
                    pass  # File might be locked, ignore
    
    def test_parse_nonexistent_file(self):
        """Test parsing a non-existent file"""
        with self.assertRaises(FileNotFoundError):
            self.parser.parse_file('nonexistent.arxsvgx')
    
    def test_get_parsed_data(self):
        """Test getting parsed data"""
        self.parser.symbol_metadata = self.test_metadata
        self.parser.content = self.test_svg
        
        self.assertEqual(self.parser.get_metadata(), self.test_metadata)
        self.assertEqual(self.parser.get_content(), self.test_svg)

class TestArxSVGXWriter(unittest.TestCase):
    """Test ArxSVGX writer functionality"""
    
    def setUp(self):
        self.writer = ArxSVGXWriter()
        self.test_svg = '<svg width="100" height="100"><rect x="10" y="10" width="80" height="80"/></svg>'
        self.test_metadata = {
            'version': {
                'created': '2024-01-01T00:00:00',
                'author': 'test_user'
            }
        }
    
    def test_write_file(self):
        """Test writing ArxSVGX file"""
        with tempfile.NamedTemporaryFile(suffix='.arxsvgx', delete=False) as f:
            f.close()
            
            try:
                self.writer.write_file(f.name, self.test_svg, self.test_metadata)
                
                # Verify file was created and has correct magic number
                self.assertTrue(os.path.exists(f.name))
                
                with open(f.name, 'rb') as f_read:
                    magic = f_read.read(4)
                    self.assertEqual(magic, ARXSVGX_MAGIC)
                
                # Verify file can be parsed
                parser = ArxSVGXParser()
                parser.parse_file(f.name)
                self.assertEqual(parser.content, self.test_svg)
                
            finally:
                os.unlink(f.name)
    
    def test_write_file_no_metadata(self):
        """Test writing file without metadata"""
        with tempfile.NamedTemporaryFile(suffix='.arxsvgx', delete=False) as f:
            f.close()
            
            try:
                self.writer.write_file(f.name, self.test_svg)
                
                # Verify file was created
                self.assertTrue(os.path.exists(f.name))
                
                # Verify file can be parsed
                parser = ArxSVGXParser()
                parser.parse_file(f.name)
                self.assertEqual(parser.content, self.test_svg)
                
            finally:
                os.unlink(f.name)
    
    def test_write_file_invalid_metadata(self):
        """Test writing file with invalid metadata"""
        with tempfile.NamedTemporaryFile(suffix='.arxsvgx', delete=False) as f:
            f.close()
            
            try:
                with self.assertRaises(ValueError):
                    self.writer.write_file(f.name, self.test_svg, "invalid metadata")
            finally:
                if os.path.exists(f.name):
                    os.unlink(f.name)
    
    def test_compression_stats(self):
        """Test compression statistics"""
        compressed = self.writer.compression_engine.compress_content(self.test_svg)
        stats = self.writer.get_compression_stats(self.test_svg, compressed)
        
        self.assertIn('original_size', stats)
        self.assertIn('compressed_size', stats)
        self.assertIn('compression_ratio', stats)
        self.assertIn('space_saved', stats)
        
        self.assertGreater(stats['compression_ratio'], 0)

class TestArxSVGXConverter(unittest.TestCase):
    """Test ArxSVGX converter functionality"""
    
    def setUp(self):
        self.converter = ArxSVGXConverter()
        self.test_svg = '''
        <svg width="100" height="100" viewBox="0 0 100 100">
            <rect x="10" y="10" width="80" height="80" fill="red"/>
            <circle cx="50" cy="50" r="30" fill="blue"/>
        </svg>
        '''
    
    def test_svg_to_arxsvgx(self):
        """Test SVG to ArxSVGX conversion"""
        with tempfile.NamedTemporaryFile(suffix='.svg', delete=False) as svg_file:
            svg_file.write(self.test_svg.encode('utf-8'))
            svg_file.close()
            
            with tempfile.NamedTemporaryFile(suffix='.arxsvgx', delete=False) as arxsvgx_file:
                arxsvgx_file.close()
                
                try:
                    result = self.converter.svg_to_arxsvgx(svg_file.name, arxsvgx_file.name)
                    
                    self.assertTrue(result['success'])
                    self.assertEqual(result['input_file'], svg_file.name)
                    self.assertEqual(result['output_file'], arxsvgx_file.name)
                    self.assertIn('compression_stats', result)
                    
                    # Verify output file is valid ArxSVGX
                    self.assertTrue(is_arxsvgx_file(arxsvgx_file.name))
                    
                finally:
                    os.unlink(svg_file.name)
                    os.unlink(arxsvgx_file.name)
    
    def test_arxsvgx_to_svg(self):
        """Test ArxSVGX to SVG conversion"""
        with tempfile.NamedTemporaryFile(suffix='.svg', delete=False) as svg_file:
            svg_file.write(self.test_svg.encode('utf-8'))
            svg_file.close()
            
            with tempfile.NamedTemporaryFile(suffix='.arxsvgx', delete=False) as arxsvgx_file:
                arxsvgx_file.close()
                
                with tempfile.NamedTemporaryFile(suffix='.svg', delete=False) as output_svg:
                    output_svg.close()
                    
                    try:
                        # First convert SVG to ArxSVGX
                        self.converter.svg_to_arxsvgx(svg_file.name, arxsvgx_file.name)
                        
                        # Then convert back to SVG
                        result = self.converter.arxsvgx_to_svg(arxsvgx_file.name, output_svg.name)
                        
                        self.assertTrue(result['success'])
                        self.assertEqual(result['input_file'], arxsvgx_file.name)
                        self.assertEqual(result['output_file'], output_svg.name)
                        self.assertIn('metadata', result)
                        
                        # Verify content is preserved
                        with open(output_svg.name, 'r') as f:
                            converted_content = f.read()
                        
                        # Normalize whitespace for comparison
                        original_normalized = ' '.join(self.test_svg.split())
                        converted_normalized = ' '.join(converted_content.split())
                        self.assertEqual(original_normalized, converted_normalized)
                        
                    finally:
                        os.unlink(svg_file.name)
                        os.unlink(arxsvgx_file.name)
                        os.unlink(output_svg.name)
    
    def test_extract_svg_metadata(self):
        """Test SVG metadata extraction"""
        metadata = self.converter._extract_svg_metadata(self.test_svg)
        
        self.assertIn('svg_info', metadata)
        self.assertIn('version', metadata)
        self.assertIn('viewBox', metadata['svg_info'])
        self.assertIn('element_count', metadata['svg_info'])
        
        self.assertEqual(metadata['svg_info']['viewBox'], '0 0 100 100')
        self.assertGreater(metadata['svg_info']['element_count'], 0)

class TestArxSVGXUtilities(unittest.TestCase):
    """Test utility functions"""
    
    def setUp(self):
        self.test_svg = '<svg width="100" height="100"><rect x="10" y="10" width="80" height="80"/></svg>'
    
    def test_is_arxsvgx_file_valid(self):
        """Test ArxSVGX file detection with valid file"""
        with tempfile.NamedTemporaryFile(suffix='.arxsvgx', delete=False) as f:
            f.close()
            
            try:
                # Create a valid ArxSVGX file
                writer = ArxSVGXWriter()
                writer.write_file(f.name, self.test_svg)
                
                self.assertTrue(is_arxsvgx_file(f.name))
                
            finally:
                os.unlink(f.name)
    
    def test_is_arxsvgx_file_invalid(self):
        """Test ArxSVGX file detection with invalid file"""
        with tempfile.NamedTemporaryFile(suffix='.svg', delete=False) as f:
            f.write(self.test_svg.encode('utf-8'))
            f.close()
            
            try:
                self.assertFalse(is_arxsvgx_file(f.name))
            finally:
                os.unlink(f.name)
    
    def test_is_arxsvgx_file_nonexistent(self):
        """Test ArxSVGX file detection with non-existent file"""
        self.assertFalse(is_arxsvgx_file('nonexistent.arxsvgx'))
    
    def test_get_arxsvgx_info(self):
        """Test getting ArxSVGX file information"""
        with tempfile.NamedTemporaryFile(suffix='.arxsvgx', delete=False) as f:
            f.close()
            
            try:
                # Create a valid ArxSVGX file
                writer = ArxSVGXWriter()
                writer.write_file(f.name, self.test_svg)
                
                info = get_arxsvgx_info(f.name)
                
                self.assertEqual(info['format'], 'ArxSVGX')
                self.assertEqual(info['version'], ARXSVGX_VERSION)
                self.assertGreater(info['file_size'], 0)
                self.assertIn('metadata', info)
                self.assertGreater(info['content_length'], 0)
                
            finally:
                os.unlink(f.name)
    
    def test_get_arxsvgx_info_invalid_file(self):
        """Test getting info for invalid file"""
        with tempfile.NamedTemporaryFile(suffix='.svg', delete=False) as f:
            f.write(self.test_svg.encode('utf-8'))
            f.close()
            
            try:
                info = get_arxsvgx_info(f.name)
                self.assertIn('error', info)
            finally:
                os.unlink(f.name)

class TestArxSVGXPerformance(unittest.TestCase):
    """Test ArxSVGX performance characteristics"""
    
    def setUp(self):
        self.converter = ArxSVGXConverter()
        self.large_svg = self._generate_large_svg()
    
    def _generate_large_svg(self, elements=1000):
        """Generate a large SVG for testing"""
        svg = '<svg width="1000" height="1000" viewBox="0 0 1000 1000">'
        for i in range(elements):
            x = (i * 10) % 1000
            y = (i * 10) % 1000
            svg += f'<rect x="{x}" y="{y}" width="5" height="5" fill="rgb({i%255},{i%255},{i%255})"/>'
        svg += '</svg>'
        return svg
    
    def test_compression_performance(self):
        """Test compression performance"""
        with tempfile.NamedTemporaryFile(suffix='.svg', delete=False) as svg_file:
            svg_file.write(self.large_svg.encode('utf-8'))
            svg_file.close()
            
            with tempfile.NamedTemporaryFile(suffix='.arxsvgx', delete=False) as arxsvgx_file:
                arxsvgx_file.close()
                
                try:
                    start_time = time.time()
                    result = self.converter.svg_to_arxsvgx(svg_file.name, arxsvgx_file.name)
                    conversion_time = time.time() - start_time
                    
                    self.assertTrue(result['success'])
                    
                    # Verify reasonable performance (should be under 5 seconds for 1000 elements)
                    self.assertLess(conversion_time, 5.0)
                    
                    # Verify good compression ratio (should be at least 30%)
                    compression_ratio = result['compression_stats']['compression_ratio']
                    self.assertGreater(compression_ratio, 30.0)
                    
                finally:
                    os.unlink(svg_file.name)
                    os.unlink(arxsvgx_file.name)
    
    def test_loading_performance(self):
        """Test loading performance"""
        with tempfile.NamedTemporaryFile(suffix='.svg', delete=False) as svg_file:
            svg_file.write(self.large_svg.encode('utf-8'))
            svg_file.close()
            
            with tempfile.NamedTemporaryFile(suffix='.arxsvgx', delete=False) as arxsvgx_file:
                arxsvgx_file.close()
                
                try:
                    # Convert to ArxSVGX
                    self.converter.svg_to_arxsvgx(svg_file.name, arxsvgx_file.name)
                    
                    # Test loading performance
                    parser = ArxSVGXParser()
                    
                    start_time = time.time()
                    parser.parse_file(arxsvgx_file.name)
                    load_time = time.time() - start_time
                    
                    # Verify reasonable loading time (should be under 2 seconds)
                    self.assertLess(load_time, 2.0)
                    
                    # Verify content is loaded correctly
                    self.assertIsNotNone(parser.content)
                    self.assertGreater(len(parser.content), 0)
                    
                finally:
                    os.unlink(svg_file.name)
                    os.unlink(arxsvgx_file.name)

if __name__ == '__main__':
    unittest.main() 
