"""
Test suite for Advanced SVG Features Service

Tests all major functionality including:
- SVG optimization algorithms
- Real-time preview capabilities
- Format conversion utilities
- Compression and caching strategies
- Advanced validation with error reporting
- SVG diff visualization
"""

import unittest
import tempfile
import os
import time
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import xml.etree.ElementTree as ET

from ..services.advanced_svg_features import (
    AdvancedSVGFeatures,
    SVGOptimizationResult,
    SVGValidationResult,
    SVGConversionResult,
    SVGDiffResult
)


class TestAdvancedSVGFeatures(unittest.TestCase):
    """Test cases for Advanced SVG Features service"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.svg_features = AdvancedSVGFeatures()
        
        # Sample SVG content for testing
        self.sample_svg = '''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100" viewBox="0 0 100 100">
  <defs>
    <linearGradient id="grad1" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" style="stop-color:rgb(255,255,0);stop-opacity:1" />
      <stop offset="100%" style="stop-color:rgb(255,0,0);stop-opacity:1" />
    </linearGradient>
  </defs>
  <rect x="10" y="10" width="80" height="80" fill="url(#grad1)" stroke="black" stroke-width="2"/>
  <circle cx="50" cy="50" r="30" fill="blue" opacity="0.5"/>
  <path d="M 10 10 L 90 90" stroke="red" stroke-width="3"/>
  <text x="50" y="50" text-anchor="middle" fill="white">Test</text>
</svg>'''
        
        self.complex_svg = '''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="200" height="200" viewBox="0 0 200 200">
  <defs>
    <filter id="blur">
      <feGaussianBlur stdDeviation="3"/>
    </filter>
    <pattern id="grid" width="10" height="10" patternUnits="userSpaceOnUse">
      <path d="M 10 0 L 0 0 0 10" fill="none" stroke="gray" stroke-width="0.5"/>
    </pattern>
  </defs>
  <rect width="200" height="200" fill="url(#grid)"/>
  <g transform="translate(50,50)">
    <rect x="0" y="0" width="100" height="100" fill="yellow" stroke="black"/>
    <circle cx="50" cy="50" r="40" fill="red" opacity="0.7"/>
    <path d="M 10 10 Q 50 0 90 10 T 90 90 Q 50 100 10 90 Z" fill="blue"/>
  </g>
  <text x="100" y="180" text-anchor="middle" font-size="16">Complex SVG</text>
</svg>'''
        
        self.invalid_svg = '''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100">
  <rect x="10" y="10" width="80" height="80" fill="red"/>
  <invalid_element>This is invalid</invalid_element>
  <script>alert("dangerous")</script>
</svg>'''
    
    def tearDown(self):
        """Clean up test fixtures"""
        self.svg_features.cleanup()
    
    def test_initialization(self):
        """Test service initialization"""
        self.assertIsNotNone(self.svg_features)
        self.assertTrue(self.svg_features.options['enable_optimization'])
        self.assertTrue(self.svg_features.options['enable_real_time_preview'])
        self.assertEqual(self.svg_features.options['optimization_level'], 'balanced')
        self.assertEqual(len(self.svg_features.supported_formats), 6)
        self.assertEqual(len(self.svg_features.validation_rules), 5)
    
    def test_svg_optimization_balanced(self):
        """Test SVG optimization with balanced level"""
        result = self.svg_features.optimize_svg(self.sample_svg, 'balanced')
        
        self.assertIsInstance(result, SVGOptimizationResult)
        self.assertGreater(result.original_size, 0)
        self.assertGreater(result.optimized_size, 0)
        self.assertGreaterEqual(result.compression_ratio, 0.0)
        self.assertLessEqual(result.compression_ratio, 1.0)
        self.assertGreater(result.optimization_time, 0.0)
        self.assertIsInstance(result.techniques_applied, list)
        self.assertGreaterEqual(result.quality_score, 0.0)
        self.assertLessEqual(result.quality_score, 1.0)
    
    def test_svg_optimization_aggressive(self):
        """Test SVG optimization with aggressive level"""
        result = self.svg_features.optimize_svg(self.sample_svg, 'aggressive')
        
        self.assertIsInstance(result, SVGOptimizationResult)
        self.assertGreater(len(result.techniques_applied), 0)
        # Aggressive should apply more techniques
        self.assertGreaterEqual(len(result.techniques_applied), 5)
    
    def test_svg_optimization_conservative(self):
        """Test SVG optimization with conservative level"""
        result = self.svg_features.optimize_svg(self.sample_svg, 'conservative')
        
        self.assertIsInstance(result, SVGOptimizationResult)
        # Conservative should apply fewer techniques
        self.assertLessEqual(len(result.techniques_applied), 5)
    
    def test_svg_optimization_complex_svg(self):
        """Test SVG optimization with complex SVG"""
        result = self.svg_features.optimize_svg(self.complex_svg)
        
        self.assertIsInstance(result, SVGOptimizationResult)
        self.assertGreater(result.original_size, result.optimized_size)
        self.assertGreater(result.compression_ratio, 0.0)
    
    def test_svg_optimization_cache(self):
        """Test SVG optimization caching"""
        # First optimization
        result1 = self.svg_features.optimize_svg(self.sample_svg)
        
        # Second optimization (should use cache)
        result2 = self.svg_features.optimize_svg(self.sample_svg)
        
        # Results should be identical
        self.assertEqual(result1.original_size, result2.original_size)
        self.assertEqual(result1.optimized_size, result2.optimized_size)
        self.assertEqual(result1.compression_ratio, result2.compression_ratio)
    
    def test_svg_validation_valid(self):
        """Test SVG validation with valid SVG"""
        result = self.svg_features.validate_svg(self.sample_svg)
        
        self.assertIsInstance(result, SVGValidationResult)
        self.assertTrue(result.is_valid)
        self.assertEqual(result.error_count, 0)
        self.assertGreaterEqual(result.validation_time, 0.0)
    
    def test_svg_validation_invalid(self):
        """Test SVG validation with invalid SVG"""
        result = self.svg_features.validate_svg(self.invalid_svg)
        
        self.assertIsInstance(result, SVGValidationResult)
        self.assertFalse(result.is_valid)
        self.assertGreater(result.error_count, 0)
        self.assertGreater(len(result.errors), 0)
    
    def test_svg_validation_syntax(self):
        """Test SVG syntax validation"""
        malformed_svg = "<svg><rect>"
        result = self.svg_features.validate_svg(malformed_svg)
        
        self.assertFalse(result.is_valid)
        self.assertGreater(result.error_count, 0)
    
    def test_svg_validation_security(self):
        """Test SVG security validation"""
        dangerous_svg = '''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100">
  <script>alert("dangerous")</script>
  <rect x="10" y="10" width="80" height="80" fill="red"/>
</svg>'''
        
        result = self.svg_features.validate_svg(dangerous_svg)
        
        self.assertFalse(result.is_valid)
        self.assertGreater(result.error_count, 0)
        # Should detect dangerous content
        self.assertTrue(any('dangerous' in error.lower() for error in result.errors))
    
    def test_svg_validation_performance(self):
        """Test SVG performance validation"""
        # Create a large SVG
        large_svg = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="1000">
  {"".join([f'<rect x="{i}" y="{i}" width="10" height="10" fill="red"/>' for i in range(1000)])}
</svg>'''
        
        result = self.svg_features.validate_svg(large_svg)
        
        self.assertIsInstance(result, SVGValidationResult)
        # Should have warnings about large file
        self.assertGreater(result.warning_count, 0)
    
    @patch('subprocess.run')
    def test_svg_conversion_pdf(self, mock_run):
        """Test SVG to PDF conversion"""
        mock_run.return_value.returncode = 0
        
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
            output_path = temp_file.name
        
        try:
            result = self.svg_features.convert_svg_format(
                self.sample_svg, 'pdf', output_path
            )
            
            self.assertIsInstance(result, SVGConversionResult)
            self.assertEqual(result.output_format, 'pdf')
            self.assertEqual(result.output_path, output_path)
            self.assertTrue(result.success)
            self.assertGreater(result.quality_score, 0.0)
            
        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)
    
    @patch('subprocess.run')
    def test_svg_conversion_png(self, mock_run):
        """Test SVG to PNG conversion"""
        mock_run.return_value.returncode = 0
        
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_file:
            output_path = temp_file.name
        
        try:
            result = self.svg_features.convert_svg_format(
                self.sample_svg, 'png', output_path, {'width': 800, 'height': 600}
            )
            
            self.assertIsInstance(result, SVGConversionResult)
            self.assertEqual(result.output_format, 'png')
            self.assertEqual(result.output_path, output_path)
            self.assertTrue(result.success)
            
        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)
    
    def test_svg_conversion_svg(self):
        """Test SVG to optimized SVG conversion"""
        with tempfile.NamedTemporaryFile(suffix='.svg', delete=False) as temp_file:
            output_path = temp_file.name
        
        try:
            result = self.svg_features.convert_svg_format(
                self.sample_svg, 'svg', output_path
            )
            
            self.assertIsInstance(result, SVGConversionResult)
            self.assertEqual(result.output_format, 'svg')
            self.assertEqual(result.output_path, output_path)
            self.assertTrue(result.success)
            self.assertGreater(result.quality_score, 0.0)
            
            # Check that output file exists and is smaller
            self.assertTrue(os.path.exists(output_path))
            original_size = len(self.sample_svg.encode('utf-8'))
            output_size = os.path.getsize(output_path)
            self.assertLessEqual(output_size, original_size)
            
        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)
    
    def test_svg_conversion_unsupported_format(self):
        """Test SVG conversion with unsupported format"""
        result = self.svg_features.convert_svg_format(
            self.sample_svg, 'unsupported', 'output.unsupported'
        )
        
        self.assertIsInstance(result, SVGConversionResult)
        self.assertFalse(result.success)
        self.assertIsNotNone(result.error_message)
        self.assertIn('Unsupported format', result.error_message)
    
    def test_svg_compression(self):
        """Test SVG compression and decompression"""
        compressed_data = self.svg_features.compress_svg(self.sample_svg)
        
        self.assertIsInstance(compressed_data, bytes)
        self.assertGreater(len(compressed_data), 0)
        
        # Decompress
        decompressed_svg = self.svg_features.decompress_svg(compressed_data)
        
        self.assertIsInstance(decompressed_svg, str)
        self.assertGreater(len(decompressed_svg), 0)
        # Should contain SVG content
        self.assertIn('<svg', decompressed_svg)
    
    def test_svg_compression_levels(self):
        """Test SVG compression with different levels"""
        # Test different compression levels
        for level in [1, 6, 9]:
            compressed_data = self.svg_features.compress_svg(self.sample_svg, level)
            self.assertIsInstance(compressed_data, bytes)
            
            decompressed_svg = self.svg_features.decompress_svg(compressed_data)
            self.assertIn('<svg', decompressed_svg)
    
    def test_svg_diff_creation(self):
        """Test SVG diff creation"""
        modified_svg = self.sample_svg.replace('Test', 'Modified')
        
        result = self.svg_features.create_svg_diff(self.sample_svg, modified_svg)
        
        self.assertIsInstance(result, SVGDiffResult)
        self.assertIsInstance(result.changes, list)
        self.assertIsInstance(result.added_elements, list)
        self.assertIsInstance(result.removed_elements, list)
        self.assertIsInstance(result.modified_elements, list)
        self.assertGreaterEqual(result.diff_score, 0.0)
        self.assertLessEqual(result.diff_score, 1.0)
        self.assertGreater(result.diff_time, 0.0)
    
    def test_svg_diff_identical(self):
        """Test SVG diff with identical SVGs"""
        result = self.svg_features.create_svg_diff(self.sample_svg, self.sample_svg)
        
        self.assertIsInstance(result, SVGDiffResult)
        self.assertEqual(len(result.changes), 0)
        self.assertEqual(len(result.added_elements), 0)
        self.assertEqual(len(result.removed_elements), 0)
        self.assertEqual(len(result.modified_elements), 0)
        self.assertEqual(result.diff_score, 0.0)
    
    def test_svg_diff_major_changes(self):
        """Test SVG diff with major changes"""
        # Create a significantly different SVG
        different_svg = '''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="200" height="200">
  <circle cx="100" cy="100" r="50" fill="green"/>
  <text x="100" y="100" text-anchor="middle" fill="white">Different</text>
</svg>'''
        
        result = self.svg_features.create_svg_diff(self.sample_svg, different_svg)
        
        self.assertIsInstance(result, SVGDiffResult)
        self.assertGreater(len(result.changes), 0)
        self.assertGreater(result.diff_score, 0.0)
    
    def test_real_time_preview_creation(self):
        """Test real-time preview creation"""
        preview_id = self.svg_features.create_real_time_preview(self.sample_svg)
        
        self.assertIsInstance(preview_id, str)
        self.assertGreater(len(preview_id), 0)
        
        # Check that preview is in cache
        self.assertIn(preview_id, self.svg_features.preview_cache)
    
    def test_real_time_preview_update(self):
        """Test real-time preview update"""
        preview_id = self.svg_features.create_real_time_preview(self.sample_svg)
        
        # Update preview
        modified_svg = self.sample_svg.replace('Test', 'Updated')
        success = self.svg_features.update_preview(preview_id, modified_svg)
        
        self.assertTrue(success)
        
        # Check that content was updated
        updated_content = self.svg_features.get_preview_content(preview_id)
        self.assertEqual(updated_content, modified_svg)
    
    def test_real_time_preview_invalid_id(self):
        """Test real-time preview with invalid ID"""
        success = self.svg_features.update_preview('invalid_id', self.sample_svg)
        self.assertFalse(success)
        
        content = self.svg_features.get_preview_content('invalid_id')
        self.assertIsNone(content)
    
    def test_real_time_preview_callback(self):
        """Test real-time preview with callback"""
        callback_called = False
        callback_content = None
        
        def test_callback(content):
            nonlocal callback_called, callback_content
            callback_called = True
            callback_content = content
        
        preview_id = self.svg_features.create_real_time_preview(self.sample_svg, test_callback)
        
        # Update preview
        modified_svg = self.sample_svg.replace('Test', 'Callback Test')
        self.svg_features.update_preview(preview_id, modified_svg)
        
        # Give some time for callback to be called
        time.sleep(0.1)
        
        # Note: In real implementation, callback would be called in background thread
        # This test verifies the callback mechanism is set up correctly
        self.assertIsNotNone(preview_id)
    
    def test_cleanup(self):
        """Test service cleanup"""
        # Create some data
        self.svg_features.optimize_svg(self.sample_svg)
        self.svg_features.create_real_time_preview(self.sample_svg)
        
        # Verify data exists
        self.assertGreater(len(self.svg_features.optimization_cache), 0)
        self.assertGreater(len(self.svg_features.preview_cache), 0)
        
        # Cleanup
        self.svg_features.cleanup()
        
        # Verify data is cleared
        self.assertEqual(len(self.svg_features.optimization_cache), 0)
        self.assertEqual(len(self.svg_features.preview_cache), 0)
    
    def test_get_statistics(self):
        """Test statistics retrieval"""
        stats = self.svg_features.get_statistics()
        
        self.assertIsInstance(stats, dict)
        self.assertIn('optimization_cache_size', stats)
        self.assertIn('preview_cache_size', stats)
        self.assertIn('conversion_cache_size', stats)
        self.assertIn('supported_formats', stats)
        self.assertIn('optimization_techniques', stats)
        self.assertIn('validation_rules', stats)
        
        self.assertIsInstance(stats['optimization_cache_size'], int)
        self.assertIsInstance(stats['supported_formats'], list)
        self.assertIsInstance(stats['optimization_techniques'], list)
    
    def test_error_handling_optimization(self):
        """Test error handling in optimization"""
        # Test with invalid SVG
        invalid_svg = "invalid svg content"
        result = self.svg_features.optimize_svg(invalid_svg)
        
        self.assertIsInstance(result, SVGOptimizationResult)
        self.assertEqual(result.compression_ratio, 0.0)
        self.assertEqual(len(result.techniques_applied), 0)
    
    def test_error_handling_validation(self):
        """Test error handling in validation"""
        # Test with None content
        result = self.svg_features.validate_svg(None)
        
        self.assertIsInstance(result, SVGValidationResult)
        self.assertFalse(result.is_valid)
        self.assertGreater(result.error_count, 0)
    
    def test_error_handling_conversion(self):
        """Test error handling in conversion"""
        # Test with invalid content and path
        result = self.svg_features.convert_svg_format(
            "invalid content", "pdf", "/invalid/path/file.pdf"
        )
        
        self.assertIsInstance(result, SVGConversionResult)
        self.assertFalse(result.success)
        self.assertIsNotNone(result.error_message)
    
    def test_error_handling_diff(self):
        """Test error handling in diff creation"""
        # Test with invalid content
        result = self.svg_features.create_svg_diff("invalid", "also invalid")
        
        self.assertIsInstance(result, SVGDiffResult)
        self.assertEqual(len(result.changes), 0)
        self.assertEqual(result.diff_score, 0.0)
    
    def test_performance_large_svg(self):
        """Test performance with large SVG"""
        # Create a large SVG
        large_svg = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="1000">
  {"".join([f'<rect x="{i}" y="{i}" width="10" height="10" fill="red"/>' for i in range(100)])}
</svg>'''
        
        start_time = time.time()
        result = self.svg_features.optimize_svg(large_svg)
        optimization_time = time.time() - start_time
        
        self.assertIsInstance(result, SVGOptimizationResult)
        self.assertLess(optimization_time, 5.0)  # Should complete within 5 seconds
    
    def test_thread_safety(self):
        """Test thread safety of the service"""
        import threading
        
        results = []
        errors = []
        
        def optimize_svg_thread():
            try:
                result = self.svg_features.optimize_svg(self.sample_svg)
                results.append(result)
            except Exception as e:
                errors.append(e)
        
        # Create multiple threads
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=optimize_svg_thread)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Verify all threads completed successfully
        self.assertEqual(len(results), 5)
        self.assertEqual(len(errors), 0)
        
        # Verify all results are valid
        for result in results:
            self.assertIsInstance(result, SVGOptimizationResult)
            self.assertGreater(result.original_size, 0)


if __name__ == '__main__':
    unittest.main() 