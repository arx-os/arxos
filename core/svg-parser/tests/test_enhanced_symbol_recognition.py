"""
Unit tests for Enhanced Symbol Recognition Service.

Tests the updated service with JSON symbol library integration.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import tempfile
import json
import os
from pathlib import Path
from typing import Dict, Any

from services.enhanced_symbol_recognition import (
    EnhancedSymbolRecognition,
    SymbolMatch,
    SymbolType,
    MLModelType
)


class TestEnhancedSymbolRecognition(unittest.TestCase):
    """Test cases for Enhanced Symbol Recognition service."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create temporary symbol library
        self.temp_dir = tempfile.mkdtemp()
        self.symbol_library_path = os.path.join(self.temp_dir, "test_symbols")
        os.makedirs(self.symbol_library_path, exist_ok=True)
        
        # Create test symbols
        self.test_symbols = {
            "test_hvac": {
                "id": "test_hvac",
                "name": "Test HVAC Unit",
                "system": "mechanical",
                "svg": {
                    "content": '<svg viewBox="0 0 100 100"><rect x="10" y="10" width="80" height="80"/></svg>'
                },
                "properties": {
                    "type": "hvac_unit",
                    "capacity": "5000 BTU"
                }
            },
            "test_electrical": {
                "id": "test_electrical", 
                "name": "Test Electrical Outlet",
                "system": "electrical",
                "svg": {
                    "content": '<svg viewBox="0 0 50 50"><circle cx="25" cy="25" r="20"/></svg>'
                },
                "properties": {
                    "type": "outlet",
                    "voltage": "120V"
                }
            }
        }
        
        # Write test symbols to files
        for symbol_id, symbol_data in self.test_symbols.items():
            symbol_file = os.path.join(self.symbol_library_path, f"{symbol_id}.json")
            with open(symbol_file, 'w') as f:
                json.dump(symbol_data, f, indent=2)
        
        # Initialize service
        self.recognition = EnhancedSymbolRecognition(self.symbol_library_path)
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_initialization(self):
        """Test service initialization with JSON library."""
        self.assertIsNotNone(self.recognition.symbol_library)
        self.assertEqual(str(self.recognition.symbol_library.library_path), self.symbol_library_path)
        self.assertIsNotNone(self.recognition.geometry_resolver)
        self.assertIsNotNone(self.recognition.logger)
    
    def test_map_system_to_symbol_type(self):
        """Test system to symbol type mapping."""
        # Test mechanical system
        symbol_type = self.recognition._map_system_to_symbol_type("mechanical")
        self.assertEqual(symbol_type, SymbolType.HVAC)
        
        # Test electrical system
        symbol_type = self.recognition._map_system_to_symbol_type("electrical")
        self.assertEqual(symbol_type, SymbolType.ELECTRICAL)
        
        # Test unknown system
        symbol_type = self.recognition._map_system_to_symbol_type("unknown")
        self.assertEqual(symbol_type, SymbolType.CUSTOM)
    
    def test_parse_svg_elements(self):
        """Test SVG element parsing."""
        svg_content = '''
        <svg viewBox="0 0 100 100">
            <path d="M10 10 L90 10 L90 90 L10 90 Z"/>
            <rect x="20" y="20" width="60" height="60"/>
            <circle cx="50" cy="50" r="30"/>
        </svg>
        '''
        
        elements = self.recognition._parse_svg_elements(svg_content)
        
        self.assertIsInstance(elements, list)
        self.assertGreater(len(elements), 0)
        
        # Check that elements have required structure
        for element in elements:
            self.assertIn('type', element)
            self.assertIn('id', element)
            self.assertIn('data', element)
            self.assertIn('features', element)
    
    def test_extract_path_features(self):
        """Test path feature extraction."""
        path_data = "M10 10 L90 10 L90 90 L10 90 Z"
        features = self.recognition._extract_path_features(path_data)
        
        self.assertIsInstance(features, dict)
        self.assertIn('length', features)
        self.assertIn('commands', features)
        self.assertIn('complexity', features)
        self.assertIn('bounds', features)
    
    def test_calculate_path_complexity(self):
        """Test path complexity calculation."""
        # Simple path
        simple_path = "M10 10 L90 10"
        complexity = self.recognition._calculate_path_complexity(simple_path)
        self.assertIsInstance(complexity, float)
        self.assertGreaterEqual(complexity, 0)
        
        # Complex path
        complex_path = "M10 10 C20 20 30 30 40 40 S50 50 60 60 Q70 70 80 80"
        complexity = self.recognition._calculate_path_complexity(complex_path)
        self.assertIsInstance(complexity, float)
        self.assertGreaterEqual(complexity, 0)
    
    def test_pattern_matching_recognition(self):
        """Test pattern matching recognition."""
        # Create test elements
        elements = [
            {
                'type': 'path',
                'id': 'test_path',
                'data': 'M10 10 L90 10 L90 90 L10 90 Z',
                'features': {
                    'length': 40,
                    'complexity': 0.5,
                    'bounds': (10, 10, 90, 90),
                    'commands': {'M': 1, 'L': 3, 'Z': 1}
                }
            }
        ]
        
        matches = self.recognition._pattern_matching_recognition(elements)
        
        self.assertIsInstance(matches, list)
        # Should find matches if confidence threshold is met
        if matches:
            for match in matches:
                self.assertIsInstance(match, SymbolMatch)
                self.assertIsInstance(match.symbol_id, str)
                self.assertIsInstance(match.symbol_name, str)
                self.assertIsInstance(match.symbol_type, SymbolType)
                self.assertIsInstance(match.confidence, float)
                self.assertGreaterEqual(match.confidence, 0)
                self.assertLessEqual(match.confidence, 1)
    
    def test_recognize_symbols_by_system(self):
        """Test system-based symbol recognition."""
        svg_content = '''
        <svg viewBox="0 0 100 100">
            <rect x="10" y="10" width="80" height="80"/>
        </svg>
        '''
        
        # Test mechanical system recognition
        matches = self.recognition.recognize_symbols_by_system(svg_content, "mechanical")
        self.assertIsInstance(matches, list)
        
        # Test electrical system recognition
        matches = self.recognition.recognize_symbols_by_system(svg_content, "electrical")
        self.assertIsInstance(matches, list)
    
    def test_calculate_pattern_similarity(self):
        """Test pattern similarity calculation."""
        element = {
            'features': {
                'complexity': 0.5,
                'bounds': (10, 10, 90, 90),
                'attributes': {'fill': 'black'}
            }
        }
        
        symbol_data = {
            'features': {
                'complexity': 0.6,
                'bounds': (5, 5, 95, 95),
                'attributes': {'fill': 'black'}
            }
        }
        
        similarity = self.recognition._calculate_pattern_similarity(element, symbol_data)
        self.assertIsInstance(similarity, float)
        self.assertGreaterEqual(similarity, 0)
        self.assertLessEqual(similarity, 1)
    
    def test_calculate_bounds_overlap(self):
        """Test bounds overlap calculation."""
        bounds1 = (0, 0, 100, 100)
        bounds2 = (50, 50, 150, 150)
        
        overlap = self.recognition._calculate_bounds_overlap(bounds1, bounds2)
        self.assertIsInstance(overlap, float)
        self.assertGreaterEqual(overlap, 0)
        self.assertLessEqual(overlap, 1)
        
        # No overlap
        bounds3 = (200, 200, 300, 300)
        overlap = self.recognition._calculate_bounds_overlap(bounds1, bounds3)
        self.assertEqual(overlap, 0.0)
    
    def test_compare_attributes(self):
        """Test attribute comparison."""
        attrs1 = {'fill': 'black', 'stroke': 'red'}
        attrs2 = {'fill': 'black', 'stroke': 'blue'}
        
        similarity = self.recognition._compare_attributes(attrs1, attrs2)
        self.assertIsInstance(similarity, float)
        self.assertGreaterEqual(similarity, 0)
        self.assertLessEqual(similarity, 1)
    
    def test_extract_geometric_features(self):
        """Test geometric feature extraction."""
        element = {
            'features': {
                'bounds': (10, 10, 90, 90)
            }
        }
        
        features = self.recognition._extract_geometric_features(element)
        
        self.assertIsInstance(features, dict)
        self.assertIn('area', features)
        self.assertIn('perimeter', features)
        self.assertIn('aspect_ratio', features)
        self.assertIn('circularity', features)
        self.assertIn('rectangularity', features)
    
    def test_extract_geometric_features_from_svg(self):
        """Test SVG geometric feature extraction."""
        svg_content = '<svg viewBox="0 0 100 100"><rect x="10" y="10" width="80" height="80"/></svg>'
        
        features = self.recognition._extract_geometric_features_from_svg(svg_content)
        
        self.assertIsInstance(features, dict)
        self.assertIn('area', features)
        self.assertIn('perimeter', features)
        self.assertIn('aspect_ratio', features)
        self.assertIn('circularity', features)
        self.assertIn('rectangularity', features)
    
    def test_filter_and_rank_results(self):
        """Test result filtering and ranking."""
        # Create test matches
        matches = [
            SymbolMatch(
                symbol_id="test1",
                symbol_name="Test 1",
                symbol_type=SymbolType.HVAC,
                confidence=0.9,
                bounding_box=(0, 0, 100, 100),
                features={},
                metadata={}
            ),
            SymbolMatch(
                symbol_id="test2",
                symbol_name="Test 2",
                symbol_type=SymbolType.ELECTRICAL,
                confidence=0.7,
                bounding_box=(0, 0, 100, 100),
                features={},
                metadata={}
            ),
            SymbolMatch(
                symbol_id="test3",
                symbol_name="Test 3",
                symbol_type=SymbolType.PLUMBING,
                confidence=0.5,  # Below threshold
                bounding_box=(0, 0, 100, 100),
                features={},
                metadata={}
            )
        ]
        
        options = {'max_results': 2}
        filtered = self.recognition._filter_and_rank_results(matches, options)
        
        self.assertIsInstance(filtered, list)
        self.assertLessEqual(len(filtered), 2)
        
        if filtered:
            # Should be sorted by confidence
            for i in range(len(filtered) - 1):
                self.assertGreaterEqual(filtered[i].confidence, filtered[i + 1].confidence)
    
    def test_get_recognition_statistics(self):
        """Test recognition statistics."""
        stats = self.recognition.get_recognition_statistics()
        
        self.assertIsInstance(stats, dict)
        self.assertIn('total_symbols', stats)
        self.assertIn('system_breakdown', stats)
        self.assertIn('ml_models', stats)
        self.assertIn('min_confidence', stats)
        self.assertIn('enable_ml', stats)
        self.assertIn('feature_extractors', stats)
        self.assertIn('model_types', stats)
        self.assertIn('library_path', stats)
        
        self.assertIsInstance(stats['total_symbols'], int)
        self.assertIsInstance(stats['system_breakdown'], dict)
        self.assertIsInstance(stats['min_confidence'], float)
        self.assertIsInstance(stats['enable_ml'], bool)
    
    def test_add_symbol_to_library(self):
        """Test adding symbol to library."""
        symbol_id = "test_new_symbol"
        symbol_data = {
            "id": symbol_id,
            "name": "New Test Symbol",
            "system": "mechanical",
            "svg": {"content": "<svg></svg>"}
        }
        
        result = self.recognition.add_symbol_to_library(symbol_id, symbol_data)
        self.assertIsInstance(result, bool)
    
    @patch('services.enhanced_symbol_recognition.OPENCV_AVAILABLE', False)
    def test_initialization_without_opencv(self):
        """Test initialization when OpenCV is not available."""
        recognition = EnhancedSymbolRecognition(self.symbol_library_path)
        self.assertFalse(recognition.enable_ml)
    
    def test_recognize_symbols_integration(self):
        """Test full symbol recognition integration."""
        svg_content = '''
        <svg viewBox="0 0 100 100">
            <rect x="10" y="10" width="80" height="80"/>
            <circle cx="50" cy="50" r="30"/>
        </svg>
        '''
        
        options = {'max_results': 5}
        matches = self.recognition.recognize_symbols(svg_content, options)
        
        self.assertIsInstance(matches, list)
        self.assertLessEqual(len(matches), 5)
        
        if matches:
            for match in matches:
                self.assertIsInstance(match, SymbolMatch)
                self.assertIsInstance(match.symbol_id, str)
                self.assertIsInstance(match.symbol_name, str)
                self.assertIsInstance(match.symbol_type, SymbolType)
                self.assertIsInstance(match.confidence, float)
                self.assertGreaterEqual(match.confidence, 0)
                self.assertLessEqual(match.confidence, 1)


if __name__ == '__main__':
    unittest.main() 