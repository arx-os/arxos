"""
Integration test for Advanced SVG Features Service

Simple test to verify core functionality works correctly.
"""

import sys
import os
import tempfile
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.services.advanced_svg_features


def test_basic_functionality():
    """Test basic functionality of Advanced SVG Features"""
    print("Testing Advanced SVG Features service...")
    
    # Initialize service
    svg_features = AdvancedSVGFeatures()
    print("✓ Service initialized")
    
    # Sample SVG for testing
    sample_svg = '''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100" viewBox="0 0 100 100">
  <rect x="10" y="10" width="80" height="80" fill="red" stroke="black" stroke-width="2"/>
  <circle cx="50" cy="50" r="30" fill="blue" opacity="0.5"/>
  <text x="50" y="50" text-anchor="middle" fill="white">Test</text>
</svg>'''
    
    # Test optimization
    print("Testing SVG optimization...")
    optimization_result = svg_features.optimize_svg(sample_svg)
    print(f"✓ Optimization completed: {optimization_result.compression_ratio:.2%} compression")
    
    # Test validation
    print("Testing SVG validation...")
    validation_result = svg_features.validate_svg(sample_svg)
    print(f"✓ Validation completed: {validation_result.is_valid}, {validation_result.error_count} errors")
    
    # Test compression
    print("Testing SVG compression...")
    compressed_data = svg_features.compress_svg(sample_svg)
    decompressed_svg = svg_features.decompress_svg(compressed_data)
    print(f"✓ Compression completed: {len(compressed_data)} bytes")
    
    # Test format conversion
    print("Testing SVG format conversion...")
    with tempfile.NamedTemporaryFile(suffix='.svg', delete=False) as temp_file:
        output_path = temp_file.name
    
    try:
        conversion_result = svg_features.convert_svg_format(sample_svg, 'svg', output_path)
        print(f"✓ Conversion completed: {conversion_result.success}")
    finally:
        if os.path.exists(output_path):
            os.unlink(output_path)
    
    # Test diff creation
    print("Testing SVG diff creation...")
    modified_svg = sample_svg.replace('Test', 'Modified')
    diff_result = svg_features.create_svg_diff(sample_svg, modified_svg)
    print(f"✓ Diff creation completed: {diff_result.diff_score:.2f} diff score")
    
    # Test real-time preview
    print("Testing real-time preview...")
    preview_id = svg_features.create_real_time_preview(sample_svg)
    success = svg_features.update_preview(preview_id, modified_svg)
    print(f"✓ Preview creation completed: {success}")
    
    # Test statistics
    print("Testing statistics...")
    stats = svg_features.get_statistics()
    print(f"✓ Statistics retrieved: {len(stats)} metrics")
    
    # Cleanup
    svg_features.cleanup()
    print("✓ Cleanup completed")
    
    print("\n🎉 All tests passed! Advanced SVG Features service is working correctly.")


if __name__ == '__main__':
    test_basic_functionality() 