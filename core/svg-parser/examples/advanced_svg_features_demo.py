"""
Advanced SVG Features Demo

Demonstrates all major capabilities of the Advanced SVG Features service:
- SVG optimization with different levels
- Real-time preview capabilities
- Format conversion utilities
- Compression and caching strategies
- Advanced validation with error reporting
- SVG diff visualization
"""

import sys
import os
import tempfile
import time
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.advanced_svg_features import AdvancedSVGFeatures


def main():
    """Main demonstration function"""
    print("🎨 Advanced SVG Features Demo")
    print("=" * 50)
    
    # Initialize the service
    svg_features = AdvancedSVGFeatures()
    print("✓ Service initialized successfully")
    
    # Sample SVG content for demonstration
    sample_svg = '''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="200" height="200" viewBox="0 0 200 200">
  <defs>
    <linearGradient id="grad1" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" style="stop-color:rgb(255,255,0);stop-opacity:1" />
      <stop offset="100%" style="stop-color:rgb(255,0,0);stop-opacity:1" />
    </linearGradient>
    <filter id="blur">
      <feGaussianBlur stdDeviation="2"/>
    </filter>
  </defs>
  
  <!-- Background -->
  <rect width="200" height="200" fill="lightblue"/>
  
  <!-- Main content -->
  <g transform="translate(50,50)">
    <rect x="0" y="0" width="100" height="100" fill="url(#grad1)" stroke="black" stroke-width="2"/>
    <circle cx="50" cy="50" r="40" fill="blue" opacity="0.7"/>
    <path d="M 10 10 Q 50 0 90 10 T 90 90 Q 50 100 10 90 Z" fill="green" opacity="0.8"/>
  </g>
  
  <!-- Text elements -->
  <text x="100" y="180" text-anchor="middle" font-size="16" fill="darkblue">Advanced SVG Demo</text>
  <text x="100" y="20" text-anchor="middle" font-size="12" fill="darkred">Optimization Test</text>
</svg>'''
    
    print(f"\n📊 Original SVG size: {len(sample_svg.encode('utf-8'))} bytes")
    
    # 1. SVG Optimization Demo
    print("\n🔧 SVG Optimization Demo")
    print("-" * 30)
    
    optimization_levels = ['conservative', 'balanced', 'aggressive']
    
    for level in optimization_levels:
        print(f"\nOptimizing with {level} level...")
        start_time = time.time()
        result = svg_features.optimize_svg(sample_svg, level)
        optimization_time = time.time() - start_time
        
        print(f"  ✓ Original size: {result.original_size} bytes")
        print(f"  ✓ Optimized size: {result.optimized_size} bytes")
        print(f"  ✓ Compression ratio: {result.compression_ratio:.2%}")
        print(f"  ✓ Optimization time: {result.optimization_time:.3f}s")
        print(f"  ✓ Techniques applied: {len(result.techniques_applied)}")
        print(f"  ✓ Quality score: {result.quality_score:.2f}")
        print(f"  ✓ Techniques: {', '.join(result.techniques_applied)}")
    
    # 2. SVG Validation Demo
    print("\n🔍 SVG Validation Demo")
    print("-" * 30)
    
    # Valid SVG
    print("Validating sample SVG...")
    validation_result = svg_features.validate_svg(sample_svg)
    print(f"  ✓ Is valid: {validation_result.is_valid}")
    print(f"  ✓ Errors: {validation_result.error_count}")
    print(f"  ✓ Warnings: {validation_result.warning_count}")
    print(f"  ✓ Validation time: {validation_result.validation_time:.3f}s")
    
    if validation_result.errors:
        print("  ⚠️  Errors:")
        for error in validation_result.errors:
            print(f"    - {error}")
    
    if validation_result.warnings:
        print("  ⚠️  Warnings:")
        for warning in validation_result.warnings:
            print(f"    - {warning}")
    
    # Invalid SVG
    invalid_svg = '''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100">
  <rect x="10" y="10" width="80" height="80" fill="red"/>
  <script>alert("dangerous")</script>
  <invalid_element>This is invalid</invalid_element>
</svg>'''
    
    print("\nValidating invalid SVG...")
    invalid_result = svg_features.validate_svg(invalid_svg)
    print(f"  ✓ Is valid: {invalid_result.is_valid}")
    print(f"  ✓ Errors: {invalid_result.error_count}")
    print(f"  ✓ Warnings: {invalid_result.warning_count}")
    
    if invalid_result.errors:
        print("  ❌ Errors:")
        for error in invalid_result.errors:
            print(f"    - {error}")
    
    # 3. SVG Compression Demo
    print("\n🗜️  SVG Compression Demo")
    print("-" * 30)
    
    compression_levels = [1, 6, 9]
    
    for level in compression_levels:
        print(f"\nCompressing with level {level}...")
        start_time = time.time()
        compressed_data = svg_features.compress_svg(sample_svg, level)
        compression_time = time.time() - start_time
        
        print(f"  ✓ Original size: {len(sample_svg.encode('utf-8'))} bytes")
        print(f"  ✓ Compressed size: {len(compressed_data)} bytes")
        print(f"  ✓ Compression ratio: {(1 - len(compressed_data) / len(sample_svg.encode('utf-8'))):.2%}")
        print(f"  ✓ Compression time: {compression_time:.3f}s")
        
        # Test decompression
        decompressed_svg = svg_features.decompress_svg(compressed_data)
        print(f"  ✓ Decompression successful: {len(decompressed_svg) > 0}")
    
    # 4. SVG Format Conversion Demo
    print("\n🔄 SVG Format Conversion Demo")
    print("-" * 30)
    
    # Test SVG to optimized SVG conversion
    with tempfile.NamedTemporaryFile(suffix='.svg', delete=False) as temp_file:
        output_path = temp_file.name
    
    try:
        print("Converting SVG to optimized SVG...")
        conversion_result = svg_features.convert_svg_format(sample_svg, 'svg', output_path)
        
        print(f"  ✓ Success: {conversion_result.success}")
        print(f"  ✓ Output format: {conversion_result.output_format}")
        print(f"  ✓ File size: {conversion_result.file_size} bytes")
        print(f"  ✓ Quality score: {conversion_result.quality_score:.2f}")
        print(f"  ✓ Conversion time: {conversion_result.conversion_time:.3f}s")
        
        if conversion_result.error_message:
            print(f"  ❌ Error: {conversion_result.error_message}")
    
    finally:
        if os.path.exists(output_path):
            os.unlink(output_path)
    
    # 5. SVG Diff Demo
    print("\n📊 SVG Diff Demo")
    print("-" * 30)
    
    # Create a modified version
    modified_svg = sample_svg.replace('Advanced SVG Demo', 'Modified SVG Demo')
    modified_svg = modified_svg.replace('Optimization Test', 'Diff Test')
    
    print("Creating diff between original and modified SVG...")
    start_time = time.time()
    diff_result = svg_features.create_svg_diff(sample_svg, modified_svg)
    diff_time = time.time() - start_time
    
    print(f"  ✓ Changes detected: {len(diff_result.changes)}")
    print(f"  ✓ Added elements: {len(diff_result.added_elements)}")
    print(f"  ✓ Removed elements: {len(diff_result.removed_elements)}")
    print(f"  ✓ Modified elements: {len(diff_result.modified_elements)}")
    print(f"  ✓ Diff score: {diff_result.diff_score:.2f}")
    print(f"  ✓ Diff time: {diff_result.diff_time:.3f}s")
    
    # 6. Real-time Preview Demo
    print("\n👁️  Real-time Preview Demo")
    print("-" * 30)
    
    print("Creating real-time preview...")
    preview_id = svg_features.create_real_time_preview(sample_svg)
    print(f"  ✓ Preview ID: {preview_id}")
    
    # Update preview
    print("Updating preview content...")
    success = svg_features.update_preview(preview_id, modified_svg)
    print(f"  ✓ Update successful: {success}")
    
    # Get preview content
    preview_content = svg_features.get_preview_content(preview_id)
    print(f"  ✓ Preview content retrieved: {len(preview_content) if preview_content else 0} bytes")
    
    # 7. Statistics Demo
    print("\n📈 Service Statistics")
    print("-" * 30)
    
    stats = svg_features.get_statistics()
    print(f"  ✓ Optimization cache size: {stats['optimization_cache_size']}")
    print(f"  ✓ Preview cache size: {stats['preview_cache_size']}")
    print(f"  ✓ Conversion cache size: {stats['conversion_cache_size']}")
    print(f"  ✓ Supported formats: {', '.join(stats['supported_formats'])}")
    print(f"  ✓ Optimization techniques: {len(stats['optimization_techniques'])}")
    print(f"  ✓ Validation rules: {len(stats['validation_rules'])}")
    
    # 8. Performance Demo
    print("\n⚡ Performance Demo")
    print("-" * 30)
    
    # Test with larger SVG
    large_svg = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="1000" viewBox="0 0 1000 1000">
  <defs>
    <linearGradient id="grad1" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" style="stop-color:rgb(255,255,0);stop-opacity:1" />
      <stop offset="100%" style="stop-color:rgb(255,0,0);stop-opacity:1" />
    </linearGradient>
  </defs>
  <rect width="1000" height="1000" fill="lightblue"/>
  {"".join([f'<rect x="{i}" y="{i}" width="10" height="10" fill="red" stroke="black"/>' for i in range(0, 1000, 20)])}
  <text x="500" y="500" text-anchor="middle" font-size="24" fill="darkblue">Large SVG Test</text>
</svg>'''
    
    print(f"Testing with large SVG ({len(large_svg.encode('utf-8'))} bytes)...")
    
    start_time = time.time()
    large_optimization = svg_features.optimize_svg(large_svg)
    optimization_time = time.time() - start_time
    
    print(f"  ✓ Large SVG optimization time: {optimization_time:.3f}s")
    print(f"  ✓ Large SVG compression ratio: {large_optimization.compression_ratio:.2%}")
    
    start_time = time.time()
    large_validation = svg_features.validate_svg(large_svg)
    validation_time = time.time() - start_time
    
    print(f"  ✓ Large SVG validation time: {validation_time:.3f}s")
    print(f"  ✓ Large SVG validation result: {large_validation.is_valid}")
    
    # Cleanup
    print("\n🧹 Cleanup")
    print("-" * 30)
    
    svg_features.cleanup()
    print("  ✓ Service cleanup completed")
    
    print("\n🎉 Advanced SVG Features Demo Completed!")
    print("=" * 50)
    print("\nKey Features Demonstrated:")
    print("  ✓ SVG optimization with multiple levels")
    print("  ✓ Comprehensive validation with error reporting")
    print("  ✓ Advanced compression with multiple levels")
    print("  ✓ Format conversion capabilities")
    print("  ✓ Diff visualization for change tracking")
    print("  ✓ Real-time preview with updates")
    print("  ✓ Performance optimization for large files")
    print("  ✓ Comprehensive statistics and monitoring")


if __name__ == '__main__':
    main() 