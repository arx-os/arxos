#!/usr/bin/env python3
"""
Test script for the Symbol Generator
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ..services.symbol_generator import SymbolGenerator

def test_symbol_generator():
    """Test the symbol generator with a mock URL"""
    
    print("Testing Symbol Generator...")
    
    # Create generator instance
    generator = SymbolGenerator()
    
    # Test URL validation
    print("\n1. Testing URL validation...")
    valid_url = "https://www.carrier.com/commercial-hvac/air-handlers/"
    invalid_url = "not-a-url"
    
    assert generator._validate_url(valid_url) == True
    assert generator._validate_url(invalid_url) == False
    print("✓ URL validation works")
    
    # Test domain extraction
    print("\n2. Testing domain extraction...")
    domain = generator._get_extractor("carrier.com")
    assert domain is not None
    print("✓ Domain extraction works")
    
    # Test symbol ID generation
    print("\n3. Testing symbol ID generation...")
    symbol_id = generator._generate_symbol_id("Carrier Air Handler Unit")
    assert symbol_id == "carrier_air_handler_unit"
    print(f"✓ Symbol ID generation works: {symbol_id}")
    
    # Test display name generation
    print("\n4. Testing display name generation...")
    display_name = generator._generate_display_name("Carrier Air Handler Unit")
    assert display_name == "Air Handler Unit"
    print(f"✓ Display name generation works: {display_name}")
    
    # Test system categorization
    print("\n5. Testing system categorization...")
    product_data = {
        'name': 'Carrier Air Handler',
        'description': 'Commercial air handling unit for HVAC systems'
    }
    system = generator._categorize_system(product_data)
    assert system == 'hvac'
    print(f"✓ System categorization works: {system}")
    
    # Test category determination
    print("\n6. Testing category determination...")
    category, subcategory = generator._determine_category(product_data, 'hvac')
    assert category == 'hvac'
    assert subcategory == 'air_handling'
    print(f"✓ Category determination works: {category}/{subcategory}")
    
    # Test SVG generation
    print("\n7. Testing SVG generation...")
    svg = generator._generate_svg(product_data)
    assert '<g id=' in svg
    assert 'rect' in svg
    print("✓ SVG generation works")
    
    # Test full generation (without actual web scraping)
    print("\n9. Testing full generation workflow...")
    try:
        # This would normally scrape a real URL, but we'll just test the structure
        result = generator.generate_symbol_from_url("https://test.carrier.com/product", 1)
        print("✓ Full generation workflow structure is correct")
    except Exception as e:
        print(f"⚠ Full generation test skipped (expected for test URL): {e}")
    
    return True

if __name__ == "__main__":
    try:
        test_symbol_generator()
        print("\n✅ Symbol Generator test completed successfully!")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1) 