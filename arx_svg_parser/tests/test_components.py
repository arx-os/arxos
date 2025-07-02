#!/usr/bin/env python3
"""
Comprehensive test script for SVG Parser Components
Tests and documents symbol library loading, recognition, rendering, and PDF processing.
"""

import sys
import os
import logging
from typing import Dict, Any

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_symbol_library_loading():
    """Test and document symbol library loading (YAML and hardcoded)."""
    print("\n" + "="*60)
    print("1. TESTING SYMBOL LIBRARY LOADING")
    print("="*60)
    
    try:
        from arx_svg_parser.services.svg_symbol_library import SVG_SYMBOLS, load_symbol_library
        
        # Test hardcoded symbols
        print(f"✓ Hardcoded symbols loaded: {len(SVG_SYMBOLS)} symbols")
        
        # Test YAML symbol loading
        yaml_symbols = load_symbol_library()
        print(f"✓ YAML symbols loaded: {len(yaml_symbols)} symbols")
        
        # Show sample symbols
        print("\nSample hardcoded symbols:")
        for i, (symbol_id, data) in enumerate(list(SVG_SYMBOLS.items())[:5]):
            print(f"  {i+1}. {symbol_id}: {data.get('display_name', 'N/A')} ({data.get('system', 'N/A')})")
        
        print("\nSample YAML symbols:")
        for i, symbol in enumerate(yaml_symbols[:5]):
            print(f"  {i+1}. {symbol.get('symbol_id', 'N/A')}: {symbol.get('display_name', 'N/A')} ({symbol.get('system', 'N/A')})")
        
        # Test filtering
        mechanical_symbols = load_symbol_library(category='mechanical')
        print(f"\n✓ Mechanical symbols filtered: {len(mechanical_symbols)} symbols")
        
        search_results = load_symbol_library(search='ahu')
        print(f"✓ Search for 'ahu': {len(search_results)} results")
        
        return True
        
    except Exception as e:
        print(f"✗ Symbol library loading failed: {e}")
        return False

def test_symbol_recognition_engine():
    """Test and document the symbol recognition engine."""
    print("\n" + "="*60)
    print("2. TESTING SYMBOL RECOGNITION ENGINE")
    print("="*60)
    
    try:
        from arx_svg_parser.services.symbol_recognition import SymbolRecognitionEngine
        
        # Initialize engine
        engine = SymbolRecognitionEngine()
        print("✓ Symbol recognition engine initialized")
        
        # Test text recognition
        test_text = """
        FLOOR PLAN - FIRST FLOOR
        ROOM 101 - CONFERENCE ROOM
        AHU-1 - AIR HANDLING UNIT
        RTU-1 - ROOFTOP UNIT
        VAV-1 - VARIABLE AIR VOLUME BOX
        THERMOSTAT T-1
        RECEPTACLE R-1
        SWITCH S-1
        PANEL PNL-1
        """
        
        recognized_symbols = engine.recognize_symbols_in_content(test_text, content_type='text')
        print(f"✓ Text recognition: {len(recognized_symbols)} symbols recognized")
        
        # Show recognition results
        print("\nRecognized symbols from text:")
        for i, symbol in enumerate(recognized_symbols[:10]):
            print(f"  {i+1}. {symbol['symbol_id']}: {symbol['symbol_data']['display_name']} (confidence: {symbol['confidence']:.2f})")
        
        # Test SVG recognition
        test_svg = '''<?xml version="1.0" encoding="UTF-8"?>
<svg width="800" height="600" xmlns="http://www.w3.org/2000/svg">
  <text x="100" y="100">AHU-1</text>
  <text x="200" y="100">RTU-1</text>
  <text x="300" y="100">VAV-1</text>
  <text x="400" y="100">THERMOSTAT T-1</text>
</svg>'''
        
        svg_symbols = engine.recognize_symbols_in_content(test_svg, content_type='svg')
        print(f"\n✓ SVG recognition: {len(svg_symbols)} symbols recognized")
        
        # Test library info
        library_info = engine.get_symbol_library_info()
        print(f"\n✓ Library info retrieved: {library_info['total_symbols']} total symbols")
        
        return True
        
    except Exception as e:
        print(f"✗ Symbol recognition engine failed: {e}")
        return False

def test_symbol_renderer():
    """Test and document the SVG symbol rendering pipeline."""
    print("\n" + "="*60)
    print("3. TESTING SYMBOL RENDERER")
    print("="*60)
    
    try:
        from arx_svg_parser.services.symbol_renderer import SymbolRenderer
        
        # Initialize renderer
        renderer = SymbolRenderer()
        print("✓ Symbol renderer initialized")
        
        # Test SVG creation
        test_svg = '''<?xml version="1.0" encoding="UTF-8"?>
<svg width="800" height="600" xmlns="http://www.w3.org/2000/svg">
  <rect width="800" height="600" fill="#f8f9fa"/>
  <text x="400" y="30" text-anchor="middle">Test Building</text>
</svg>'''
        
        # Create test symbols to render
        from arx_svg_parser.services.symbol_recognition import SymbolRecognitionEngine
        engine = SymbolRecognitionEngine()
        
        test_symbols = [
            {
                'symbol_id': 'ahu',
                'symbol_data': engine.get_symbol_metadata('ahu'),
                'confidence': 0.9,
                'match_type': 'text',
                'position': {'x': 100, 'y': 100}
            },
            {
                'symbol_id': 'thermostat',
                'symbol_data': engine.get_symbol_metadata('thermostat'),
                'confidence': 0.8,
                'match_type': 'text',
                'position': {'x': 200, 'y': 150}
            }
        ]
        
        # Render symbols
        result = renderer.render_recognized_symbols(
            test_svg, test_symbols, "TEST_BUILDING", "FLOOR_1"
        )
        
        print(f"✓ Symbols rendered: {result['total_rendered']} symbols")
        print(f"✓ Updated SVG generated: {len(result['svg'])} characters")
        
        # Test symbol position update
        if result['rendered_symbols']:
            object_id = result['rendered_symbols'][0]['object_id']
            updated_svg = renderer.update_symbol_position(
                result['svg'], object_id, {'x': 300, 'y': 200}
            )
            print(f"✓ Symbol position updated: {object_id}")
        
        # Test symbol removal
        if result['rendered_symbols']:
            object_id = result['rendered_symbols'][0]['object_id']
            removed_svg = renderer.remove_symbol(result['svg'], object_id)
            print(f"✓ Symbol removed: {object_id}")
        
        return True
        
    except Exception as e:
        print(f"✗ Symbol renderer failed: {e}")
        return False

def test_pdf_processor():
    """Test and document the PDF-to-SVG pipeline (even if stubbed)."""
    print("\n" + "="*60)
    print("4. TESTING PDF PROCESSOR")
    print("="*60)
    
    try:
        from arx_svg_parser.services.pdf_processor import PDFProcessor
        
        # Initialize processor
        processor = PDFProcessor()
        print("✓ PDF processor initialized")
        
        # Create mock PDF data
        mock_pdf_data = b"Mock PDF content for testing"
        
        # Test PDF processing
        result = processor.process_pdf(mock_pdf_data, "TEST_BUILDING", "FLOOR_1")
        
        print(f"✓ PDF processing completed")
        print(f"✓ SVG generated: {len(result['svg'])} characters")
        print(f"✓ Symbols recognized: {len(result['recognized_symbols'])}")
        print(f"✓ Symbols rendered: {len(result['rendered_symbols'])}")
        
        # Show processing summary
        summary = result['summary']
        print(f"\nProcessing Summary:")
        print(f"  - Rooms detected: {summary.get('rooms', 0)}")
        print(f"  - Devices found: {summary.get('devices', 0)}")
        print(f"  - Systems identified: {len(summary.get('systems', {}))}")
        print(f"  - Confidence: {summary.get('confidence', 0):.2f}")
        
        # Test symbol library info
        library_info = processor.get_symbol_library_info()
        print(f"\n✓ Symbol library info: {library_info['total_symbols']} symbols available")
        
        return True
        
    except Exception as e:
        print(f"✗ PDF processor failed: {e}")
        return False

def test_bim_extraction():
    """Test and document BIM extraction from SVG with symbols."""
    print("\n" + "="*60)
    print("5. TESTING BIM EXTRACTION")
    print("="*60)
    
    try:
        from arx_svg_parser.services.bim_extraction import BIMExtractor
        
        # Initialize extractor
        extractor = BIMExtractor()
        print("✓ BIM extractor initialized")
        
        # Create test SVG with symbols
        test_svg = '''<?xml version="1.0" encoding="UTF-8"?>
<svg width="800" height="600" xmlns="http://www.w3.org/2000/svg">
  <g id="arx-objects">
    <g id="ahu_12345678" class="arx-symbol arx-ahu" transform="translate(100,100)" 
       data-symbol-id="ahu" data-symbol-name="Air Handling Unit (AHU)" 
       data-system="mechanical" data-confidence="0.9">
      <rect x="0" y="0" width="40" height="20" fill="#ccc" stroke="#000"/>
      <text x="20" y="15" font-size="10" text-anchor="middle">AHU</text>
    </g>
  </g>
  <text x="100" y="200">ROOM 101 - CONFERENCE ROOM</text>
  <text x="200" y="200">THERMOSTAT T-1</text>
</svg>'''
        
        # Extract BIM data
        bim_data = extractor.extract_bim_from_svg(test_svg, "TEST_BUILDING", "FLOOR_1")
        
        print(f"✓ BIM extraction completed")
        print(f"✓ Devices extracted: {len(bim_data.get('devices', []))}")
        print(f"✓ Rooms extracted: {len(bim_data.get('rooms', []))}")
        print(f"✓ Systems identified: {len(bim_data.get('systems', {}))}")
        print(f"✓ Relationships found: {len(bim_data.get('relationships', []))}")
        
        # Show extracted data
        if bim_data.get('devices'):
            print("\nExtracted devices:")
            for device in bim_data['devices'][:3]:
                print(f"  - {device['name']} ({device['system']}) at {device.get('position', 'N/A')}")
        
        if bim_data.get('rooms'):
            print("\nExtracted rooms:")
            for room in bim_data['rooms'][:3]:
                print(f"  - {room['name']} ({room['type']}) with {len(room['devices'])} devices")
        
        return True
        
    except Exception as e:
        print(f"✗ BIM extraction failed: {e}")
        return False

def test_api_endpoints():
    """Test API endpoint functionality."""
    print("\n" + "="*60)
    print("6. TESTING API ENDPOINTS")
    print("="*60)
    
    try:
        # Test symbol recognition endpoint
        from arx_svg_parser.services.symbol_recognition import SymbolRecognitionEngine
        from arx_svg_parser.models.parse import SymbolRecognitionRequest
        
        engine = SymbolRecognitionEngine()
        
        # Create test request
        test_content = "AHU-1 AIR HANDLING UNIT RTU-1 ROOFTOP UNIT VAV-1"
        request = SymbolRecognitionRequest(
            content=test_content,
            content_type="text",
            confidence_threshold=0.5
        )
        
        # Simulate endpoint processing
        recognized_symbols = engine.recognize_symbols_in_content(
            request.content, request.content_type
        )
        
        print(f"✓ Symbol recognition endpoint: {len(recognized_symbols)} symbols recognized")
        
        # Test symbol library endpoint
        library_info = engine.get_symbol_library_info()
        print(f"✓ Symbol library endpoint: {library_info['total_symbols']} symbols available")
        
        # Test systems endpoint
        systems = engine.get_symbol_library_info()['systems']
        print(f"✓ Systems endpoint: {len(systems)} systems available")
        
        return True
        
    except Exception as e:
        print(f"✗ API endpoint testing failed: {e}")
        return False

def main():
    """Run all component tests."""
    print("SVG PARSER COMPONENT TESTING")
    print("="*60)
    
    tests = [
        ("Symbol Library Loading", test_symbol_library_loading),
        ("Symbol Recognition Engine", test_symbol_recognition_engine),
        ("Symbol Renderer", test_symbol_renderer),
        ("PDF Processor", test_pdf_processor),
        ("BIM Extraction", test_bim_extraction),
        ("API Endpoints", test_api_endpoints),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"✗ {test_name} failed with exception: {e}")
            results[test_name] = False
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status} - {test_name}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All components are working correctly!")
    else:
        print("⚠️  Some components need attention.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 