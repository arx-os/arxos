"""
Enhanced Symbol Recognition Demo

This script demonstrates the updated Enhanced Symbol Recognition service
with JSON symbol library integration.
"""

import sys
import os
import json
import tempfile
from pathlib import Path

# Add the parent directory to the path to import services
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.enhanced_symbol_recognition import (
    EnhancedSymbolRecognition,
    SymbolType,
    MLModelType
)


def create_test_symbol_library():
    """Create a test symbol library for demonstration."""
    temp_dir = tempfile.mkdtemp()
    symbol_library_path = os.path.join(temp_dir, "demo_symbols")
    os.makedirs(symbol_library_path, exist_ok=True)
    
    # Create symbols directory structure
    symbols_dir = os.path.join(symbol_library_path, "symbols")
    os.makedirs(symbols_dir, exist_ok=True)
    
    # Create system directories
    mechanical_dir = os.path.join(symbols_dir, "mechanical")
    electrical_dir = os.path.join(symbols_dir, "electrical")
    plumbing_dir = os.path.join(symbols_dir, "plumbing")
    
    os.makedirs(mechanical_dir, exist_ok=True)
    os.makedirs(electrical_dir, exist_ok=True)
    os.makedirs(plumbing_dir, exist_ok=True)
    
    # Create test symbols
    test_symbols = {
        "hvac_unit": {
            "id": "hvac_unit",
            "name": "HVAC Unit",
            "system": "mechanical",
            "svg": {
                "content": '''
                <svg viewBox="0 0 100 100">
                    <rect x="10" y="10" width="80" height="80" fill="lightblue" stroke="blue"/>
                    <circle cx="30" cy="30" r="5" fill="white"/>
                    <circle cx="70" cy="30" r="5" fill="white"/>
                    <rect x="20" y="60" width="60" height="20" fill="white"/>
                </svg>
                '''
            },
            "properties": {
                "type": "hvac_unit",
                "capacity": "5000 BTU",
                "efficiency": "high"
            }
        },
        "electrical_outlet": {
            "id": "electrical_outlet",
            "name": "Electrical Outlet",
            "system": "electrical",
            "svg": {
                "content": '''
                <svg viewBox="0 0 50 50">
                    <circle cx="25" cy="25" r="20" fill="yellow" stroke="black"/>
                    <circle cx="25" cy="25" r="15" fill="none" stroke="black"/>
                    <line x1="15" y1="25" x2="35" y2="25" stroke="black" stroke-width="2"/>
                </svg>
                '''
            },
            "properties": {
                "type": "outlet",
                "voltage": "120V",
                "amperage": "15A"
            }
        },
        "plumbing_fixture": {
            "id": "plumbing_fixture",
            "name": "Plumbing Fixture",
            "system": "plumbing",
            "svg": {
                "content": '''
                <svg viewBox="0 0 80 80">
                    <rect x="20" y="10" width="40" height="60" fill="white" stroke="black"/>
                    <circle cx="40" cy="25" r="8" fill="none" stroke="black"/>
                    <rect x="30" y="50" width="20" height="20" fill="lightgray"/>
                </svg>
                '''
            },
            "properties": {
                "type": "fixture",
                "material": "stainless_steel",
                "connection": "threaded"
            }
        }
    }
    
    # Write symbols to appropriate system directories
    for symbol_id, symbol_data in test_symbols.items():
        system = symbol_data.get('system', 'custom')
        system_dir = os.path.join(symbols_dir, system)
        
        # Create system directory if it doesn't exist
        os.makedirs(system_dir, exist_ok=True)
        
        symbol_file = os.path.join(system_dir, f"{symbol_id}.json")
        with open(symbol_file, 'w') as f:
            json.dump(symbol_data, f, indent=2)
    
    # Create index.json file
    index_data = {
        "version": "1.0",
        "total_symbols": len(test_symbols),
        "by_system": {
            "mechanical": ["hvac_unit"],
            "electrical": ["electrical_outlet"],
            "plumbing": ["plumbing_fixture"]
        },
        "systems": ["mechanical", "electrical", "plumbing"]
    }
    
    index_file = os.path.join(symbol_library_path, "index.json")
    with open(index_file, 'w') as f:
        json.dump(index_data, f, indent=2)
    
    return symbol_library_path


def demo_basic_recognition():
    """Demonstrate basic symbol recognition."""
    print("=== Enhanced Symbol Recognition Demo ===\n")
    
    # Create test symbol library
    library_path = create_test_symbol_library()
    print(f"Created test symbol library at: {library_path}")
    
    # Initialize recognition service
    recognition = EnhancedSymbolRecognition(library_path)
    print("✓ Enhanced Symbol Recognition service initialized")
    
    # Test SVG content
    test_svg = '''
    <svg viewBox="0 0 100 100">
        <rect x="10" y="10" width="80" height="80" fill="lightblue" stroke="blue"/>
        <circle cx="30" cy="30" r="5" fill="white"/>
        <circle cx="70" cy="30" r="5" fill="white"/>
        <rect x="20" y="60" width="60" height="20" fill="white"/>
    </svg>
    '''
    
    print(f"\n--- Testing Basic Recognition ---")
    print("Input SVG (HVAC unit):")
    print(test_svg.strip())
    
    # Perform recognition
    matches = recognition.recognize_symbols(test_svg)
    
    print(f"\nRecognition Results:")
    if matches:
        for i, match in enumerate(matches, 1):
            print(f"  {i}. {match.symbol_name} ({match.symbol_id})")
            print(f"     Type: {match.symbol_type.value}")
            print(f"     Confidence: {match.confidence:.2f}")
            print(f"     Bounds: {match.bounding_box}")
    else:
        print("  No matches found")
    
    return recognition


def demo_system_based_recognition(recognition):
    """Demonstrate system-based symbol recognition."""
    print(f"\n--- Testing System-Based Recognition ---")
    
    # Test electrical system
    electrical_svg = '''
    <svg viewBox="0 0 50 50">
        <circle cx="25" cy="25" r="20" fill="yellow" stroke="black"/>
        <circle cx="25" cy="25" r="15" fill="none" stroke="black"/>
        <line x1="15" y1="25" x2="35" y2="25" stroke="black" stroke-width="2"/>
    </svg>
    '''
    
    print("Input SVG (Electrical outlet):")
    print(electrical_svg.strip())
    
    # Test mechanical system recognition
    print(f"\nMechanical System Recognition:")
    matches = recognition.recognize_symbols_by_system(electrical_svg, "mechanical")
    if matches:
        for match in matches:
            print(f"  - {match.symbol_name} (confidence: {match.confidence:.2f})")
    else:
        print("  No mechanical matches found")
    
    # Test electrical system recognition
    print(f"\nElectrical System Recognition:")
    matches = recognition.recognize_symbols_by_system(electrical_svg, "electrical")
    if matches:
        for match in matches:
            print(f"  - {match.symbol_name} (confidence: {match.confidence:.2f})")
    else:
        print("  No electrical matches found")


def demo_feature_extraction(recognition):
    """Demonstrate feature extraction capabilities."""
    print(f"\n--- Testing Feature Extraction ---")
    
    # Test path feature extraction
    path_data = "M10 10 L90 10 L90 90 L10 90 Z"
    features = recognition._extract_path_features(path_data)
    
    print(f"Path Features:")
    print(f"  Length: {features.get('length', 0)}")
    print(f"  Complexity: {features.get('complexity', 0):.2f}")
    print(f"  Commands: {features.get('commands', {})}")
    print(f"  Bounds: {features.get('bounds', (0, 0, 0, 0))}")
    
    # Test geometric feature extraction
    element = {
        'features': {
            'bounds': (10, 10, 90, 90)
        }
    }
    geometric_features = recognition._extract_geometric_features(element)
    
    print(f"\nGeometric Features:")
    print(f"  Area: {geometric_features.get('area', 0):.2f}")
    print(f"  Perimeter: {geometric_features.get('perimeter', 0):.2f}")
    print(f"  Aspect Ratio: {geometric_features.get('aspect_ratio', 0):.2f}")
    print(f"  Circularity: {geometric_features.get('circularity', 0):.2f}")


def demo_statistics(recognition):
    """Demonstrate recognition statistics."""
    print(f"\n--- Recognition Statistics ---")
    
    stats = recognition.get_recognition_statistics()
    
    print(f"Total Symbols: {stats.get('total_symbols', 0)}")
    print(f"System Breakdown: {stats.get('system_breakdown', {})}")
    print(f"ML Models: {stats.get('ml_models', 0)}")
    print(f"Min Confidence: {stats.get('min_confidence', 0):.2f}")
    print(f"ML Enabled: {stats.get('enable_ml', False)}")
    print(f"Feature Extractors: {stats.get('feature_extractors', [])}")
    print(f"Library Path: {stats.get('library_path', 'N/A')}")


def demo_custom_training(recognition):
    """Demonstrate custom symbol training."""
    print(f"\n--- Custom Symbol Training Demo ---")
    
    # Create training data
    training_data = [
        {
            'features': {
                'length': 40,
                'complexity': 0.5,
                'bounds': (10, 10, 90, 90),
                'commands': {'M': 1, 'L': 3, 'Z': 1}
            }
        },
        {
            'features': {
                'length': 35,
                'complexity': 0.4,
                'bounds': (15, 15, 85, 85),
                'commands': {'M': 1, 'L': 3, 'Z': 1}
            }
        }
    ]
    
    print("Training custom symbol 'demo_symbol'...")
    success = recognition.train_custom_symbol(
        "demo_symbol",
        training_data,
        MLModelType.SVM
    )
    
    if success:
        print("✓ Custom symbol training successful")
    else:
        print("✗ Custom symbol training failed (expected without scikit-learn)")


def main():
    """Run the enhanced symbol recognition demo."""
    try:
        # Demo 1: Basic recognition
        recognition = demo_basic_recognition()
        
        # Demo 2: System-based recognition
        demo_system_based_recognition(recognition)
        
        # Demo 3: Feature extraction
        demo_feature_extraction(recognition)
        
        # Demo 4: Statistics
        demo_statistics(recognition)
        
        # Demo 5: Custom training
        demo_custom_training(recognition)
        
        print(f"\n=== Demo Complete ===")
        print("The Enhanced Symbol Recognition service has been successfully updated")
        print("to work with the new JSON-based symbol library structure.")
        
    except Exception as e:
        print(f"Demo failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main() 