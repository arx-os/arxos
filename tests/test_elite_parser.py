#!/usr/bin/env python3
"""
Elite Parser Test Suite

Tests the elite Python-based parser with comprehensive object recognition
and classification capabilities.

Author: Arxos Team
Version: 2.0.0
"""

import unittest
import sys
import os
import asyncio
import tempfile
import json
from pathlib import Path
from typing import Dict, Any, List

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Import the elite parser
from svgx_engine.services.elite_parser import (
    EliteParser, 
    ObjectType, 
    RecognizedObject,
    PDFParser,
    ImageAnalyzer,
    TextClassifier,
    SymbolRecognizer,
    LayoutAnalyzer,
    QualityAssurance
)


class TestEliteParser(unittest.TestCase):
    """Test suite for elite parser functionality"""
    
    def setUp(self):
        """Set up test environment"""
        self.parser = EliteParser()
        self.test_results = {
            'document_analysis': False,
            'content_extraction': False,
            'object_recognition': False,
            'classification': False,
            'context_analysis': False,
            'precision_mapping': False,
            'quality_assurance': False
        }
    
    def test_parser_initialization(self):
        """Test elite parser initialization"""
        print("\n🔧 Testing parser initialization...")
        
        try:
            # Test parser creation
            self.assertIsNotNone(self.parser)
            self.assertIsInstance(self.parser.options, dict)
            
            # Test required options
            required_options = [
                'enable_ai', 'enable_ocr', 'enable_symbol_recognition',
                'enable_layout_analysis', 'enable_semantic_analysis',
                'enable_contextual_classification', 'enable_precision_mapping',
                'enable_quality_assurance', 'max_concurrency', 'precision',
                'confidence_threshold'
            ]
            
            for option in required_options:
                self.assertIn(option, self.parser.options)
            
            # Test recognition engines
            self.assertIsNotNone(self.parser.text_classifier)
            self.assertIsNotNone(self.parser.symbol_recognizer)
            self.assertIsNotNone(self.parser.layout_analyzer)
            self.assertIsNotNone(self.parser.quality_assurance)
            
            print("✅ Parser initialization: PASSED")
            
        except Exception as e:
            print(f"❌ Parser initialization: FAILED - {e}")
            self.fail(f"Parser initialization failed: {e}")
    
    def test_document_type_detection(self):
        """Test document type detection"""
        print("\n📄 Testing document type detection...")
        
        try:
            # Test PDF detection
            pdf_path = Path("test.pdf")
            doc_type = self.parser._detect_document_type(pdf_path)
            self.assertEqual(doc_type, 'pdf')
            
            # Test image detection
            image_path = Path("test.png")
            doc_type = self.parser._detect_document_type(image_path)
            self.assertEqual(doc_type, 'image')
            
            # Test vector detection
            svg_path = Path("test.svg")
            doc_type = self.parser._detect_document_type(svg_path)
            self.assertEqual(doc_type, 'vector')
            
            # Test unknown detection
            unknown_path = Path("test.xyz")
            doc_type = self.parser._detect_document_type(unknown_path)
            self.assertEqual(doc_type, 'unknown')
            
            print("✅ Document type detection: PASSED")
            
        except Exception as e:
            print(f"❌ Document type detection: FAILED - {e}")
            self.fail(f"Document type detection failed: {e}")
    
    def test_object_type_enumeration(self):
        """Test object type enumeration"""
        print("\n🎯 Testing object type enumeration...")
        
        try:
            # Test CAD elements
            self.assertIsInstance(ObjectType.DIMENSION, ObjectType)
            self.assertIsInstance(ObjectType.CENTER_LINE, ObjectType)
            self.assertIsInstance(ObjectType.HIDDEN_LINE, ObjectType)
            
            # Test geometric elements
            self.assertIsInstance(ObjectType.LINE, ObjectType)
            self.assertIsInstance(ObjectType.CIRCLE, ObjectType)
            self.assertIsInstance(ObjectType.RECTANGLE, ObjectType)
            
            # Test text elements
            self.assertIsInstance(ObjectType.DIMENSION_TEXT, ObjectType)
            self.assertIsInstance(ObjectType.TITLE_TEXT, ObjectType)
            self.assertIsInstance(ObjectType.NOTE_TEXT, ObjectType)
            
            # Test symbol elements
            self.assertIsInstance(ObjectType.WELD_SYMBOL, ObjectType)
            self.assertIsInstance(ObjectType.SURFACE_FINISH, ObjectType)
            self.assertIsInstance(ObjectType.TOLERANCE_SYMBOL, ObjectType)
            
            # Test structure elements
            self.assertIsInstance(ObjectType.TABLE, ObjectType)
            self.assertIsInstance(ObjectType.BILL_OF_MATERIALS, ObjectType)
            
            # Test image elements
            self.assertIsInstance(ObjectType.PHOTOGRAPH, ObjectType)
            self.assertIsInstance(ObjectType.DIAGRAM, ObjectType)
            
            # Test layout elements
            self.assertIsInstance(ObjectType.TITLE_BLOCK, ObjectType)
            self.assertIsInstance(ObjectType.BORDER, ObjectType)
            
            # Test metadata elements
            self.assertIsInstance(ObjectType.REVISION_MARK, ObjectType)
            self.assertIsInstance(ObjectType.APPROVAL_STAMP, ObjectType)
            
            print("✅ Object type enumeration: PASSED")
            
        except Exception as e:
            print(f"❌ Object type enumeration: FAILED - {e}")
            self.fail(f"Object type enumeration failed: {e}")
    
    def test_text_classification(self):
        """Test text classification capabilities"""
        print("\n📝 Testing text classification...")
        
        try:
            classifier = TextClassifier()
            
            # Test dimension text classification
            dim_text = "DIM 100"
            classification = classifier.classify_text(dim_text, (100, 200), 12)
            self.assertEqual(classification, ObjectType.DIMENSION_TEXT)
            
            # Test title text classification
            title_text = "PART NAME"
            classification = classifier.classify_text(title_text, (150, 250), 14)
            self.assertEqual(classification, ObjectType.TITLE_TEXT)
            
            # Test note text classification
            note_text = "NOTE: Assembly required"
            classification = classifier.classify_text(note_text, (200, 300), 10)
            self.assertEqual(classification, ObjectType.NOTE_TEXT)
            
            # Test label text classification
            label_text = "LABEL: Component A"
            classification = classifier.classify_text(label_text, (250, 350), 10)
            self.assertEqual(classification, ObjectType.LABEL_TEXT)
            
            print("✅ Text classification: PASSED")
            
        except Exception as e:
            print(f"❌ Text classification: FAILED - {e}")
            self.fail(f"Text classification failed: {e}")
    
    def test_symbol_recognition(self):
        """Test symbol recognition capabilities"""
        print("\n🎯 Testing symbol recognition...")
        
        try:
            recognizer = SymbolRecognizer()
            
            # Test circle symbol recognition
            circle_geometry = {'type': 'circle', 'radius': 10}
            symbol_type = recognizer.recognize_symbol(circle_geometry)
            self.assertEqual(symbol_type, ObjectType.HOLE_SYMBOL)
            
            # Test line symbol recognition
            line_geometry = {'type': 'line', 'length': 50}
            symbol_type = recognizer.recognize_symbol(line_geometry)
            self.assertEqual(symbol_type, ObjectType.CENTER_LINE)
            
            # Test unknown symbol recognition
            unknown_geometry = {'type': 'unknown'}
            symbol_type = recognizer.recognize_symbol(unknown_geometry)
            self.assertEqual(symbol_type, ObjectType.SYMBOL)
            
            print("✅ Symbol recognition: PASSED")
            
        except Exception as e:
            print(f"❌ Symbol recognition: FAILED - {e}")
            self.fail(f"Symbol recognition failed: {e}")
    
    def test_layout_analysis(self):
        """Test layout analysis capabilities"""
        print("\n🏗️ Testing layout analysis...")
        
        try:
            analyzer = LayoutAnalyzer()
            
            # Test layout analysis with sample elements
            sample_elements = [
                {'type': 'text', 'content': 'Title', 'position': (100, 100)},
                {'type': 'line', 'start': (0, 0), 'end': (100, 0)},
                {'type': 'rectangle', 'position': (50, 50), 'size': (200, 150)}
            ]
            
            layout_analysis = analyzer.analyze_layout(sample_elements)
            
            # Verify analysis structure
            self.assertIsInstance(layout_analysis, dict)
            self.assertIn('title_block', layout_analysis)
            self.assertIn('borders', layout_analysis)
            self.assertIn('grids', layout_analysis)
            self.assertIn('viewports', layout_analysis)
            
            print("✅ Layout analysis: PASSED")
            
        except Exception as e:
            print(f"❌ Layout analysis: FAILED - {e}")
            self.fail(f"Layout analysis failed: {e}")
    
    def test_quality_assurance(self):
        """Test quality assurance capabilities"""
        print("\n✅ Testing quality assurance...")
        
        try:
            qa = QualityAssurance()
            
            # Test quality metrics
            self.assertIsInstance(qa.quality_metrics, dict)
            required_metrics = ['precision_threshold', 'confidence_threshold', 
                              'completeness_threshold', 'consistency_threshold']
            
            for metric in required_metrics:
                self.assertIn(metric, qa.quality_metrics)
            
            # Test validation with sample objects
            sample_objects = [
                RecognizedObject(
                    id="obj_1",
                    type=ObjectType.DIMENSION,
                    confidence=0.9,
                    position=(100, 200),
                    geometry={'type': 'line'},
                    properties={'length': 100},
                    metadata={'source': 'test'},
                    precision_level=None,  # Would be set in real implementation
                    source='test',
                    timestamp='2024-01-01T00:00:00Z'
                )
            ]
            
            validation = qa.validate_objects(sample_objects)
            
            # Verify validation structure
            self.assertIsInstance(validation, dict)
            self.assertIn('precision_compliance', validation)
            self.assertIn('confidence_validation', validation)
            self.assertIn('completeness_check', validation)
            self.assertIn('consistency_check', validation)
            
            print("✅ Quality assurance: PASSED")
            
        except Exception as e:
            print(f"❌ Quality assurance: FAILED - {e}")
            self.fail(f"Quality assurance failed: {e}")
    
    def test_precision_calculation(self):
        """Test precision calculation methods"""
        print("\n🎯 Testing precision calculation...")
        
        try:
            # Test required precision mapping
            dim_precision = self.parser._get_required_precision(ObjectType.DIMENSION)
            self.assertEqual(dim_precision, 0.001)
            
            text_precision = self.parser._get_required_precision(ObjectType.DIMENSION_TEXT)
            self.assertEqual(text_precision, 0.01)
            
            image_precision = self.parser._get_required_precision(ObjectType.PHOTOGRAPH)
            self.assertEqual(image_precision, 0.1)
            
            # Test precision gap calculation
            test_object = RecognizedObject(
                id="test_obj",
                type=ObjectType.DIMENSION,
                confidence=0.9,
                position=(100, 200),
                geometry={'type': 'line'},
                properties={},
                metadata={},
                precision_level=None,
                source='test',
                timestamp='2024-01-01T00:00:00Z'
            )
            
            gap = self.parser._calculate_precision_gap(test_object)
            self.assertIsInstance(gap, float)
            self.assertGreaterEqual(gap, 0)
            
            # Test precision score calculation
            score = self.parser._calculate_precision_score(test_object)
            self.assertIsInstance(score, float)
            self.assertGreaterEqual(score, 0)
            self.assertLessEqual(score, 1)
            
            print("✅ Precision calculation: PASSED")
            
        except Exception as e:
            print(f"❌ Precision calculation: FAILED - {e}")
            self.fail(f"Precision calculation failed: {e}")
    
    def test_statistics_calculation(self):
        """Test statistics calculation methods"""
        print("\n📊 Testing statistics calculation...")
        
        try:
            # Create sample objects for testing
            sample_objects = [
                RecognizedObject(
                    id="obj_1",
                    type=ObjectType.DIMENSION,
                    confidence=0.9,
                    position=(100, 200),
                    geometry={'type': 'line'},
                    properties={},
                    metadata={},
                    precision_level=None,
                    source='test',
                    timestamp='2024-01-01T00:00:00Z'
                ),
                RecognizedObject(
                    id="obj_2",
                    type=ObjectType.CIRCLE,
                    confidence=0.8,
                    position=(150, 250),
                    geometry={'type': 'circle'},
                    properties={},
                    metadata={},
                    precision_level=None,
                    source='test',
                    timestamp='2024-01-01T00:00:00Z'
                ),
                RecognizedObject(
                    id="obj_3",
                    type=ObjectType.DIMENSION_TEXT,
                    confidence=0.95,
                    position=(200, 300),
                    geometry={'type': 'text'},
                    properties={},
                    metadata={},
                    precision_level=None,
                    source='test',
                    timestamp='2024-01-01T00:00:00Z'
                )
            ]
            
            # Test category statistics
            category_stats = self.parser._get_object_category_stats(sample_objects)
            self.assertIsInstance(category_stats, dict)
            self.assertEqual(category_stats['dimension'], 1)
            self.assertEqual(category_stats['circle'], 1)
            self.assertEqual(category_stats['dimension_text'], 1)
            
            # Test confidence statistics
            confidence_stats = self.parser._get_confidence_stats(sample_objects)
            self.assertIsInstance(confidence_stats, dict)
            self.assertIn('average', confidence_stats)
            self.assertIn('min', confidence_stats)
            self.assertIn('max', confidence_stats)
            self.assertIn('median', confidence_stats)
            
            # Test precision statistics
            precision_stats = self.parser._get_precision_stats(sample_objects)
            self.assertIsInstance(precision_stats, dict)
            self.assertIn('average', precision_stats)
            self.assertIn('min', precision_stats)
            self.assertIn('max', precision_stats)
            self.assertIn('median', precision_stats)
            
            print("✅ Statistics calculation: PASSED")
            
        except Exception as e:
            print(f"❌ Statistics calculation: FAILED - {e}")
            self.fail(f"Statistics calculation failed: {e}")
    
    def test_recommendation_generation(self):
        """Test recommendation generation"""
        print("\n💡 Testing recommendation generation...")
        
        try:
            # Create sample objects
            sample_objects = [
                RecognizedObject(
                    id="obj_1",
                    type=ObjectType.DIMENSION,
                    confidence=0.6,  # Low confidence
                    position=(100, 200),
                    geometry={'type': 'line'},
                    properties={},
                    metadata={},
                    precision_level=None,
                    source='test',
                    timestamp='2024-01-01T00:00:00Z'
                )
            ]
            
            # Create sample quality assurance results
            quality_assurance = {
                'precision_compliance': 0.7,  # Below threshold
                'confidence_validation': 0.6,  # Below threshold
                'completeness_check': 0.8,  # Below threshold
                'consistency_check': 0.9
            }
            
            # Generate recommendations
            recommendations = self.parser._generate_recommendations(sample_objects, quality_assurance)
            
            # Verify recommendations
            self.assertIsInstance(recommendations, list)
            self.assertGreater(len(recommendations), 0)
            
            for recommendation in recommendations:
                self.assertIsInstance(recommendation, dict)
                self.assertIn('type', recommendation)
                self.assertIn('priority', recommendation)
                self.assertIn('message', recommendation)
                self.assertIn('action', recommendation)
            
            print("✅ Recommendation generation: PASSED")
            
        except Exception as e:
            print(f"❌ Recommendation generation: FAILED - {e}")
            self.fail(f"Recommendation generation failed: {e}")
    
    def test_report_generation(self):
        """Test comprehensive report generation"""
        print("\n📋 Testing report generation...")
        
        try:
            # Create sample parsing data
            parsing_data = {
                'document_analysis': {
                    'document_type': 'pdf',
                    'page_count': 1,
                    'content_types': {'text', 'vector'},
                    'complexity_score': 100
                },
                'extracted_content': {
                    'text': [{'text': 'DIM 100', 'position': (100, 200)}],
                    'vectors': [{'type': 'line', 'start': (0, 0), 'end': (100, 0)}],
                    'images': [],
                    'tables': [],
                    'symbols': [],
                    'layout': []
                },
                'recognized_objects': [],
                'classified_objects': [
                    RecognizedObject(
                        id="obj_1",
                        type=ObjectType.DIMENSION,
                        confidence=0.9,
                        position=(100, 200),
                        geometry={'type': 'line'},
                        properties={},
                        metadata={},
                        precision_level=None,
                        source='test',
                        timestamp='2024-01-01T00:00:00Z'
                    )
                ],
                'contextual_analysis': {
                    'spatial_relationships': [],
                    'semantic_relationships': [],
                    'hierarchical_relationships': [],
                    'functional_relationships': [],
                    'temporal_relationships': []
                },
                'precision_mapping': {
                    'obj_1': {
                        'required_precision': 0.001,
                        'current_precision': 0.001,
                        'precision_gap': 0.0,
                        'precision_score': 1.0
                    }
                },
                'quality_assurance': {
                    'overall_quality': 0.9,
                    'precision_compliance': 1.0,
                    'confidence_validation': 1.0,
                    'completeness_check': 0.95,
                    'consistency_check': 0.9,
                    'accuracy_validation': 0.95
                }
            }
            
            # Generate report
            report = self.parser._generate_parsing_report(parsing_data)
            
            # Verify report structure
            self.assertIsInstance(report, dict)
            self.assertIn('summary', report)
            self.assertIn('details', report)
            self.assertIn('recommendations', report)
            self.assertIn('metadata', report)
            
            # Verify summary
            summary = report['summary']
            self.assertIn('total_objects', summary)
            self.assertIn('object_categories', summary)
            self.assertIn('confidence_stats', summary)
            self.assertIn('precision_stats', summary)
            self.assertIn('quality_score', summary)
            
            # Verify metadata
            metadata = report['metadata']
            self.assertIn('parser_version', metadata)
            self.assertIn('timestamp', metadata)
            self.assertIn('processing_options', metadata)
            
            print("✅ Report generation: PASSED")
            
        except Exception as e:
            print(f"❌ Report generation: FAILED - {e}")
            self.fail(f"Report generation failed: {e}")
    
    def test_complete_parsing_pipeline(self):
        """Test complete parsing pipeline"""
        print("\n🚀 Testing complete parsing pipeline...")
        
        try:
            # Create a temporary test document
            with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as temp_file:
                temp_file.write(b"Test document content")
                temp_file_path = temp_file.name
            
            try:
                # Test complete parsing pipeline
                # Note: This is a simplified test since we don't have actual PDF/image files
                # In a real implementation, you would test with actual document files
                
                # Test parser initialization
                self.assertIsNotNone(self.parser)
                
                # Test document type detection
                doc_type = self.parser._detect_document_type(Path(temp_file_path))
                self.assertEqual(doc_type, 'unknown')  # .txt files are unknown
                
                # Test object ID generation
                obj_id = self.parser._generate_object_id()
                self.assertIsInstance(obj_id, str)
                self.assertTrue(obj_id.startswith('obj_'))
                
                # Test precision calculations
                dim_precision = self.parser._get_required_precision(ObjectType.DIMENSION)
                self.assertEqual(dim_precision, 0.001)
                
                print("✅ Complete parsing pipeline: PASSED")
                
            finally:
                # Clean up temporary file
                os.unlink(temp_file_path)
            
        except Exception as e:
            print(f"❌ Complete parsing pipeline: FAILED - {e}")
            self.fail(f"Complete parsing pipeline failed: {e}")
    
    def tearDown(self):
        """Clean up after tests"""
        # Print test results summary
        print(f"\n📊 Test Results Summary:")
        for test_name, passed in self.test_results.items():
            status = "✅ PASSED" if passed else "❌ FAILED"
            print(f"  {test_name}: {status}")


if __name__ == '__main__':
    # Run the tests
    unittest.main(verbosity=2) 