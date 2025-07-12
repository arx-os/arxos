"""
Unit tests for Failure Detection System

Tests cover:
- Anomaly detection (if scikit-learn available)
- Trend analysis
- Pattern recognition
- Failure prediction (if scikit-learn available)
- Risk assessment
- Integration tests
"""

import unittest
import tempfile
import json
import os
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

# Add parent directory to path for imports
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

# Check if scikit-learn is available
try:
    import sklearn
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    print("Warning: scikit-learn not available. ML tests will be skipped.")

from services.failure_detection import (
    TrendAnalyzer, PatternRecognizer, RiskAssessor, FailureDetectionSystem,
    generate_failure_data, generate_component_data, FailureType, AlertLevel
)

# Only import ML components if available
if SKLEARN_AVAILABLE:
    from services.failure_detection import AnomalyDetector, FailurePredictor


class TestTrendAnalyzer(unittest.TestCase):
    """Test TrendAnalyzer class"""
    
    def setUp(self):
        """Set up test data"""
        # Create data with clear trends
        self.trend_data = pd.Series([i + np.random.normal(0, 0.1) for i in range(50)])
        self.flat_data = pd.Series([10 + np.random.normal(0, 0.1) for _ in range(50)])
    
    def test_trend_analyzer_creation(self):
        """Test trend analyzer creation"""
        analyzer = TrendAnalyzer(window_size=10, threshold=0.1)
        self.assertIsNotNone(analyzer)
        self.assertEqual(analyzer.window_size, 10)
        self.assertEqual(analyzer.threshold, 0.1)
    
    def test_trend_detection(self):
        """Test trend detection"""
        analyzer = TrendAnalyzer(window_size=10, threshold=0.1)
        trends = analyzer.detect_trends(self.trend_data)
        
        # Should detect trends in trending data
        self.assertGreater(len(trends), 0)
        
        # Check trend structure
        for trend in trends:
            self.assertIn('index', trend)
            self.assertIn('trend_type', trend)
            self.assertIn('slope', trend)
            self.assertIn('strength', trend)
            self.assertIn('window_data', trend)
    
    def test_flat_data(self):
        """Test trend detection on flat data"""
        analyzer = TrendAnalyzer(window_size=10, threshold=0.1)
        trends = analyzer.detect_trends(self.flat_data)
        
        # Should detect fewer or no trends in flat data
        # (depends on noise level and threshold)
        self.assertIsInstance(trends, list)
    
    def test_breakpoint_detection(self):
        """Test breakpoint detection"""
        analyzer = TrendAnalyzer(window_size=5, threshold=0.1)
        
        # Create data with a clear breakpoint
        data = pd.Series([1] * 25 + [10] * 25)
        breakpoints = analyzer.detect_breakpoints(data)
        
        # Should detect breakpoint around index 25
        self.assertGreater(len(breakpoints), 0)
    
    def test_insufficient_data(self):
        """Test handling of insufficient data"""
        analyzer = TrendAnalyzer(window_size=10)
        
        # Data shorter than window size
        short_data = pd.Series([1, 2, 3, 4, 5])
        trends = analyzer.detect_trends(short_data)
        breakpoints = analyzer.detect_breakpoints(short_data)
        
        self.assertEqual(len(trends), 0)
        self.assertEqual(len(breakpoints), 0)


class TestPatternRecognizer(unittest.TestCase):
    """Test PatternRecognizer class"""
    
    def setUp(self):
        """Set up test data"""
        # Create data with repeating patterns
        pattern = [1, 2, 3, 4, 5]
        self.pattern_data = pd.Series(pattern * 10)  # Repeat pattern 10 times
        
        # Add some noise
        self.pattern_data += np.random.normal(0, 0.1, len(self.pattern_data))
    
    def test_pattern_recognizer_creation(self):
        """Test pattern recognizer creation"""
        recognizer = PatternRecognizer(min_pattern_length=3, similarity_threshold=0.8)
        self.assertIsNotNone(recognizer)
        self.assertEqual(recognizer.min_pattern_length, 3)
        self.assertEqual(recognizer.similarity_threshold, 0.8)
    
    def test_pattern_recognition(self):
        """Test pattern recognition"""
        recognizer = PatternRecognizer(min_pattern_length=3, similarity_threshold=0.7)
        patterns = recognizer.find_repeating_patterns(self.pattern_data)
        
        # Should find some patterns
        self.assertGreater(len(patterns), 0)
        
        # Check pattern structure
        for pattern in patterns:
            self.assertIn('pattern', pattern)
            self.assertIn('start_indices', pattern)
            self.assertIn('length', pattern)
            self.assertIn('occurrences', pattern)
    
    def test_similarity_calculation(self):
        """Test similarity calculation"""
        recognizer = PatternRecognizer()
        
        # Test identical patterns
        pattern1 = pd.Series([1, 2, 3, 4, 5])
        pattern2 = pd.Series([1, 2, 3, 4, 5])
        similarity = recognizer._calculate_similarity(pattern1, pattern2)
        self.assertAlmostEqual(similarity, 1.0, places=5)
        
        # Test different patterns
        pattern3 = pd.Series([5, 4, 3, 2, 1])
        similarity = recognizer._calculate_similarity(pattern1, pattern3)
        self.assertLess(similarity, 1.0)
    
    def test_insufficient_data(self):
        """Test handling of insufficient data"""
        recognizer = PatternRecognizer(min_pattern_length=5)
        
        # Data shorter than minimum pattern length * 2
        short_data = pd.Series([1, 2, 3, 4, 5, 6, 7, 8])
        patterns = recognizer.find_repeating_patterns(short_data)
        
        self.assertEqual(len(patterns), 0)


class TestRiskAssessor(unittest.TestCase):
    """Test RiskAssessor class"""
    
    def setUp(self):
        """Set up test data"""
        self.component_data = {
            'component_id': 'test_comp_001',
            'age': 5.0,
            'usage_hours': 8000,
            'environment_score': 0.3,
            'days_since_maintenance': 180,
            'anomaly_count': 2
        }
    
    def test_risk_assessor_creation(self):
        """Test risk assessor creation"""
        assessor = RiskAssessor()
        self.assertIsNotNone(assessor)
        self.assertIn('age', assessor.risk_factors)
        self.assertIn('usage', assessor.risk_factors)
    
    def test_risk_assessment(self):
        """Test risk assessment"""
        assessor = RiskAssessor()
        assessment = assessor.assess_risk(self.component_data)
        
        self.assertIsNotNone(assessment)
        self.assertEqual(assessment.component_id, 'test_comp_001')
        self.assertGreaterEqual(assessment.risk_score, 0)
        self.assertLessEqual(assessment.risk_score, 1)
        self.assertIsInstance(assessment.risk_factors, dict)
        self.assertIsInstance(assessment.recommendations, list)
    
    def test_high_risk_component(self):
        """Test assessment of high-risk component"""
        high_risk_data = {
            'component_id': 'high_risk_comp',
            'age': 15.0,  # Very old
            'usage_hours': 15000,  # High usage
            'environment_score': 0.9,  # Poor environment
            'days_since_maintenance': 700,  # Long time since maintenance
            'anomaly_count': 10  # Many anomalies
        }
        
        assessor = RiskAssessor()
        assessment = assessor.assess_risk(high_risk_data)
        
        self.assertGreater(assessment.risk_score, 0.7)  # Should be high risk
        self.assertGreater(len(assessment.recommendations), 0)
    
    def test_low_risk_component(self):
        """Test assessment of low-risk component"""
        low_risk_data = {
            'component_id': 'low_risk_comp',
            'age': 1.0,  # New
            'usage_hours': 1000,  # Low usage
            'environment_score': 0.1,  # Good environment
            'days_since_maintenance': 30,  # Recent maintenance
            'anomaly_count': 0  # No anomalies
        }
        
        assessor = RiskAssessor()
        assessment = assessor.assess_risk(low_risk_data)
        
        self.assertLess(assessment.risk_score, 0.4)  # Should be low risk


@unittest.skipUnless(SKLEARN_AVAILABLE, "scikit-learn not available")
class TestAnomalyDetector(unittest.TestCase):
    """Test AnomalyDetector class (requires scikit-learn)"""
    
    def setUp(self):
        """Set up test data"""
        # Create sample data with some anomalies
        np.random.seed(42)
        self.normal_data = pd.DataFrame({
            'value1': np.random.normal(0, 1, 100),
            'value2': np.random.normal(10, 2, 100)
        })
        
        # Add some anomalies
        self.normal_data.loc[50, 'value1'] = 10  # Clear anomaly
        self.normal_data.loc[75, 'value2'] = 25  # Clear anomaly
    
    def test_anomaly_detector_creation(self):
        """Test anomaly detector creation"""
        detector = AnomalyDetector(contamination=0.1)
        self.assertIsNotNone(detector)
        self.assertFalse(detector.is_fitted)
    
    def test_anomaly_detection(self):
        """Test anomaly detection"""
        detector = AnomalyDetector()
        detector.fit(self.normal_data)
        
        predictions = detector.predict(self.normal_data)
        scores = detector.predict_scores(self.normal_data)
        
        self.assertEqual(len(predictions), len(self.normal_data))
        self.assertEqual(len(scores), len(self.normal_data))
        
        # Should detect some anomalies
        self.assertGreater(np.sum(predictions), 0)


@unittest.skipUnless(SKLEARN_AVAILABLE, "scikit-learn not available")
class TestFailurePredictor(unittest.TestCase):
    """Test FailurePredictor class (requires scikit-learn)"""
    
    def setUp(self):
        """Set up test data"""
        # Generate sample failure data
        self.failure_data = generate_failure_data(100, 0.2)
    
    def test_failure_predictor_creation(self):
        """Test failure predictor creation"""
        predictor = FailurePredictor(model_type="random_forest")
        self.assertIsNotNone(predictor)
        self.assertFalse(predictor.is_fitted)
    
    def test_model_fitting(self):
        """Test model fitting"""
        predictor = FailurePredictor()
        predictor.fit(self.failure_data, "failure")
        
        self.assertTrue(predictor.is_fitted)
        self.assertGreater(len(predictor.feature_names), 0)
        self.assertGreater(len(predictor.class_names), 0)
    
    def test_failure_prediction(self):
        """Test failure prediction"""
        predictor = FailurePredictor()
        predictor.fit(self.failure_data, "failure")
        
        predictions = predictor.predict(self.failure_data)
        probabilities = predictor.predict_proba(self.failure_data)
        
        self.assertEqual(len(predictions), len(self.failure_data))
        self.assertGreater(len(probabilities), 0)


class TestFailureDetectionSystem(unittest.TestCase):
    """Test FailureDetectionSystem class"""
    
    def setUp(self):
        """Set up test system"""
        self.system = FailureDetectionSystem()
        self.test_data = generate_failure_data(100, 0.15)
    
    def test_system_creation(self):
        """Test system creation"""
        self.assertIsNotNone(self.system.trend_analyzer)
        self.assertIsNotNone(self.system.pattern_recognizer)
        self.assertIsNotNone(self.system.risk_assessor)
        
        # ML components may or may not be available
        if SKLEARN_AVAILABLE:
            self.assertIsNotNone(self.system.anomaly_detector)
            self.assertIsNotNone(self.system.failure_predictor)
    
    def test_telemetry_processing(self):
        """Test telemetry data processing"""
        patterns = self.system.process_telemetry_data(self.test_data, "test_source")
        
        self.assertIsInstance(patterns, list)
        # May or may not detect patterns depending on data characteristics
    
    def test_risk_assessment(self):
        """Test risk assessment"""
        components = generate_component_data(5)
        assessments = self.system.assess_risks(components)
        
        self.assertEqual(len(assessments), 5)
        for assessment in assessments:
            self.assertIsInstance(assessment.risk_score, float)
            self.assertIsInstance(assessment.recommendations, list)
    
    def test_system_summary(self):
        """Test system summary generation"""
        # Process some data first
        self.system.process_telemetry_data(self.test_data, "test_source")
        self.system.assess_risks(generate_component_data(3))
        
        summary = self.system.get_summary()
        
        self.assertIn('timestamp', summary)
        self.assertIn('patterns_detected', summary)
        self.assertIn('alerts_generated', summary)
        self.assertIn('risk_assessments', summary)
    
    @unittest.skipUnless(SKLEARN_AVAILABLE, "scikit-learn not available")
    def test_model_save_load(self):
        """Test model save and load functionality"""
        # Fit some models first
        self.system.anomaly_detector.fit(self.test_data.select_dtypes(include=[np.number]))
        self.system.failure_predictor.fit(self.test_data, "failure")
        
        # Save models
        with tempfile.NamedTemporaryFile(suffix='.pkl', delete=False) as f:
            model_file = f.name
        
        try:
            self.system.save_model(model_file)
            
            # Create new system and load models
            new_system = FailureDetectionSystem()
            new_system.load_model(model_file)
            
            # Check that models are loaded
            self.assertTrue(new_system.anomaly_detector.is_fitted)
            self.assertTrue(new_system.failure_predictor.is_fitted)
        
        finally:
            if os.path.exists(model_file):
                os.unlink(model_file)


class TestDataGeneration(unittest.TestCase):
    """Test data generation utilities"""
    
    def test_failure_data_generation(self):
        """Test failure data generation"""
        data = generate_failure_data(100, 0.2)
        
        self.assertIsInstance(data, pd.DataFrame)
        self.assertEqual(len(data), 100)
        self.assertIn('failure', data.columns)
        self.assertIn('timestamp', data.columns)
        
        # Check failure rate
        failure_rate = data['failure'].mean()
        self.assertAlmostEqual(failure_rate, 0.2, delta=0.1)
    
    def test_component_data_generation(self):
        """Test component data generation"""
        components = generate_component_data(10)
        
        self.assertEqual(len(components), 10)
        
        for component in components:
            self.assertIn('component_id', component)
            self.assertIn('age', component)
            self.assertIn('usage_hours', component)
            self.assertIn('environment_score', component)
            self.assertIn('days_since_maintenance', component)
            self.assertIn('anomaly_count', component)


class TestIntegration(unittest.TestCase):
    """Test integration scenarios"""
    
    def test_end_to_end_analysis(self):
        """Test end-to-end failure analysis"""
        # Generate test data
        data = generate_failure_data(200, 0.15)
        components = generate_component_data(5)
        
        # Create system and run analysis
        system = FailureDetectionSystem()
        
        # Process telemetry
        patterns = system.process_telemetry_data(data, "integration_test")
        
        # Assess risks
        assessments = system.assess_risks(components)
        
        # Get summary
        summary = system.get_summary()
        
        # Verify results
        self.assertIsInstance(patterns, list)
        self.assertIsInstance(assessments, list)
        self.assertIsInstance(summary, dict)
        
        # All components should have risk assessments
        self.assertEqual(len(assessments), 5)
    
    def test_alert_generation(self):
        """Test alert generation with high-risk scenarios"""
        # Create data with clear failure indicators
        data = pd.DataFrame({
            'temperature': [50] * 90 + [120] * 10,  # High temperature at end
            'pressure': [100] * 90 + [200] * 10,    # High pressure at end
            'vibration': [0.5] * 90 + [2.0] * 10,  # High vibration at end
            'failure': [0] * 90 + [1] * 10         # Failures at end
        })
        
        system = FailureDetectionSystem()
        
        # Should detect patterns and generate alerts
        patterns = system.process_telemetry_data(data, "alert_test")
        
        # Should detect some patterns due to anomalies
        self.assertIsInstance(patterns, list)


if __name__ == '__main__':
    unittest.main() 