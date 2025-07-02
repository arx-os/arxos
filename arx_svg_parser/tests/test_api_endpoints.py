#!/usr/bin/env python3
"""
API Endpoint Testing Script for SVG Parser Microservice
Tests all the requested API endpoints for symbol recognition, rendering, and BIM extraction.
"""

import requests
import json
import time
from typing import Dict, Any

# API base URL
BASE_URL = "http://localhost:8000"

def test_health_endpoint():
    """Test the health check endpoint."""
    print("\n" + "="*60)
    print("1. TESTING HEALTH ENDPOINT")
    print("="*60)
    
    try:
        response = requests.get(f"{BASE_URL}/v1/health")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health check passed: {data}")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False

def test_symbol_recognition_endpoint():
    """Test symbol recognition in text/SVG."""
    print("\n" + "="*60)
    print("2. TESTING SYMBOL RECOGNITION ENDPOINT")
    print("="*60)
    
    # Test text recognition
    text_payload = {
        "content": "AHU-1 AIR HANDLING UNIT RTU-1 ROOFTOP UNIT VAV-1 VARIABLE AIR VOLUME THERMOSTAT T-1",
        "content_type": "text",
        "confidence_threshold": 0.5
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/v1/parse/recognize-symbols",
            json=text_payload,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Text recognition successful: {data['total_recognized']} symbols recognized")
            print(f"   Sample symbols: {[s['symbol_id'] for s in data['recognized_symbols'][:5]]}")
            return True
        else:
            print(f"❌ Text recognition failed: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Text recognition error: {e}")
        return False

def test_symbol_rendering_endpoint():
    """Test rendering recognized symbols into SVG-BIM."""
    print("\n" + "="*60)
    print("3. TESTING SYMBOL RENDERING ENDPOINT")
    print("="*60)
    
    # Create test SVG content
    test_svg = '''<?xml version="1.0" encoding="UTF-8"?>
<svg width="800" height="600" xmlns="http://www.w3.org/2000/svg">
  <rect width="800" height="600" fill="#f8f9fa"/>
  <text x="400" y="30" text-anchor="middle">Test Building</text>
  <text x="100" y="100">AHU-1</text>
  <text x="200" y="100">RTU-1</text>
</svg>'''
    
    try:
        response = requests.post(
            f"{BASE_URL}/v1/parse/render-symbols",
            data={
                "svg_content": test_svg,
                "building_id": "TEST_BUILDING",
                "floor_label": "FLOOR_1"
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Symbol rendering successful: {data['total_rendered']} symbols rendered")
            print(f"   SVG length: {len(data['svg'])} characters")
            print(f"   Rendered symbols: {len(data['rendered_symbols'])}")
            return True
        else:
            print(f"❌ Symbol rendering failed: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Symbol rendering error: {e}")
        return False

def test_auto_recognition_endpoint():
    """Test auto-recognize-and-render endpoint for PDF/SVG uploads."""
    print("\n" + "="*60)
    print("4. TESTING AUTO RECOGNITION ENDPOINT")
    print("="*60)
    
    # Create test SVG file content
    test_svg_content = '''<?xml version="1.0" encoding="UTF-8"?>
<svg width="800" height="600" xmlns="http://www.w3.org/2000/svg">
  <rect width="800" height="600" fill="#f8f9fa"/>
  <text x="400" y="30" text-anchor="middle">Test Building</text>
  <text x="100" y="100">AHU-1 AIR HANDLING UNIT</text>
  <text x="200" y="100">RTU-1 ROOFTOP UNIT</text>
  <text x="300" y="100">VAV-1 VARIABLE AIR VOLUME</text>
  <text x="400" y="100">THERMOSTAT T-1</text>
</svg>'''
    
    try:
        # Create a mock file upload
        files = {
            'file': ('test.svg', test_svg_content, 'image/svg+xml')
        }
        data = {
            'building_id': 'TEST_BUILDING',
            'floor_label': 'FLOOR_1',
            'confidence_threshold': '0.5'
        }
        
        response = requests.post(
            f"{BASE_URL}/v1/parse/auto-recognize-and-render",
            files=files,
            data=data
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Auto recognition successful: {data['file_type']} file processed")
            print(f"   Recognized symbols: {len(data['recognized_symbols'])}")
            print(f"   Rendered symbols: {len(data['rendered_symbols'])}")
            print(f"   SVG length: {len(data['svg'])} characters")
            return True
        else:
            print(f"❌ Auto recognition failed: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Auto recognition error: {e}")
        return False

def test_bim_extraction_endpoint():
    """Test BIM extraction from SVG with dynamic symbols."""
    print("\n" + "="*60)
    print("5. TESTING BIM EXTRACTION ENDPOINT")
    print("="*60)
    
    # Create test SVG with rendered symbols
    test_svg_with_symbols = '''<?xml version="1.0" encoding="UTF-8"?>
<svg width="800" height="600" xmlns="http://www.w3.org/2000/svg">
  <g id="arx-objects">
    <g id="ahu_12345678" class="arx-symbol arx-ahu" transform="translate(100,100)" 
       data-symbol-id="ahu" data-symbol-name="Air Handling Unit (AHU)" 
       data-system="mechanical" data-confidence="0.9">
      <rect x="0" y="0" width="40" height="20" fill="#ccc" stroke="#000"/>
      <text x="20" y="15" font-size="10" text-anchor="middle">AHU</text>
    </g>
    <g id="thermostat_87654321" class="arx-symbol arx-thermostat" transform="translate(200,150)" 
       data-symbol-id="thermostat" data-symbol-name="Thermostat" 
       data-system="mechanical" data-confidence="0.8">
      <circle cx="0" cy="0" r="15" fill="#fff" stroke="#000"/>
      <text x="0" y="5" font-size="8" text-anchor="middle">T</text>
    </g>
  </g>
  <text x="100" y="200">ROOM 101 - CONFERENCE ROOM</text>
  <text x="200" y="200">THERMOSTAT T-1</text>
</svg>'''
    
    try:
        response = requests.post(
            f"{BASE_URL}/v1/parse/extract-bim",
            data={
                "svg_content": test_svg_with_symbols,
                "building_id": "TEST_BUILDING",
                "floor_label": "FLOOR_1"
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ BIM extraction successful")
            print(f"   Devices extracted: {len(data.get('devices', []))}")
            print(f"   Rooms extracted: {len(data.get('rooms', []))}")
            print(f"   Systems identified: {len(data.get('systems', {}))}")
            return True
        else:
            print(f"❌ BIM extraction failed: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ BIM extraction error: {e}")
        return False

def test_symbol_library_endpoint():
    """Test symbol library information endpoint."""
    print("\n" + "="*60)
    print("6. TESTING SYMBOL LIBRARY ENDPOINT")
    print("="*60)
    
    try:
        response = requests.get(f"{BASE_URL}/v1/parse/symbol-library")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Symbol library endpoint successful")
            print(f"   Total symbols: {data.get('total_symbols', 0)}")
            print(f"   Available systems: {list(data.get('systems', {}).keys())}")
            return True
        else:
            print(f"❌ Symbol library failed: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Symbol library error: {e}")
        return False

def test_systems_endpoint():
    """Test systems information endpoint."""
    print("\n" + "="*60)
    print("7. TESTING SYSTEMS ENDPOINT")
    print("="*60)
    
    try:
        response = requests.get(f"{BASE_URL}/v1/parse/systems")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Systems endpoint successful")
            print(f"   Available systems: {data.get('systems', [])}")
            return True
        else:
            print(f"❌ Systems endpoint failed: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Systems endpoint error: {e}")
        return False

def test_categories_endpoint():
    """Test categories information endpoint."""
    print("\n" + "="*60)
    print("8. TESTING CATEGORIES ENDPOINT")
    print("="*60)
    
    try:
        response = requests.get(f"{BASE_URL}/v1/parse/categories")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Categories endpoint successful")
            print(f"   Available categories: {data.get('categories', [])}")
            return True
        else:
            print(f"❌ Categories endpoint failed: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Categories endpoint error: {e}")
        return False

def test_symbol_position_update():
    """Test symbol position update endpoint."""
    print("\n" + "="*60)
    print("9. TESTING SYMBOL POSITION UPDATE ENDPOINT")
    print("="*60)
    
    # Create test SVG with a symbol
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
</svg>'''
    
    try:
        response = requests.put(
            f"{BASE_URL}/v1/parse/update-symbol-position",
            data={
                "svg_content": test_svg,
                "object_id": "ahu_12345678",
                "x": "300",
                "y": "200"
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Symbol position update successful")
            print(f"   Updated object: {data.get('object_id')}")
            print(f"   New position: {data.get('new_position')}")
            return True
        else:
            print(f"❌ Symbol position update failed: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Symbol position update error: {e}")
        return False

def test_symbol_removal():
    """Test symbol removal endpoint."""
    print("\n" + "="*60)
    print("10. TESTING SYMBOL REMOVAL ENDPOINT")
    print("="*60)
    
    # Create test SVG with a symbol
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
</svg>'''
    
    try:
        response = requests.delete(
            f"{BASE_URL}/v1/parse/remove-symbol",
            data={
                "svg_content": test_svg,
                "object_id": "ahu_12345678"
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Symbol removal successful")
            print(f"   Removed object: {data.get('object_id')}")
            return True
        else:
            print(f"❌ Symbol removal failed: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Symbol removal error: {e}")
        return False

def main():
    """Run all API endpoint tests."""
    print("API ENDPOINT TESTING")
    print("="*60)
    print(f"Testing endpoints at: {BASE_URL}")
    
    # Check if server is running
    print("\nChecking if server is running...")
    try:
        response = requests.get(f"{BASE_URL}/", timeout=5)
        if response.status_code == 200:
            print("✅ Server is running")
        else:
            print("❌ Server is not responding correctly")
            return
    except Exception as e:
        print(f"❌ Cannot connect to server: {e}")
        print("Please start the server with: uvicorn app:app --reload --host 0.0.0.0 --port 8000")
        return
    
    # Run all tests
    tests = [
        ("Health Check", test_health_endpoint),
        ("Symbol Recognition", test_symbol_recognition_endpoint),
        ("Symbol Rendering", test_symbol_rendering_endpoint),
        ("Auto Recognition", test_auto_recognition_endpoint),
        ("BIM Extraction", test_bim_extraction_endpoint),
        ("Symbol Library", test_symbol_library_endpoint),
        ("Systems Info", test_systems_endpoint),
        ("Categories Info", test_categories_endpoint),
        ("Symbol Position Update", test_symbol_position_update),
        ("Symbol Removal", test_symbol_removal),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results[test_name] = False
    
    # Summary
    print("\n" + "="*60)
    print("API ENDPOINT TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print(f"\nOverall: {passed}/{total} endpoints working")
    
    if passed == total:
        print("🎉 All API endpoints are working correctly!")
    else:
        print("⚠️  Some endpoints need attention.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1) 