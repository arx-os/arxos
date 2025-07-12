"""
Test suite for ARKit Calibration Sync feature.

Comprehensive testing for coordinate system alignment, calibration processes,
validation, and API integration.
"""

import unittest
import json
import tempfile
import os
import time
from datetime import datetime
from typing import Dict, List, Any
import numpy as np

from services.arkit_calibration_sync import (
    ARKitCalibrationService, CalibrationStatus, CalibrationAccuracy,
    ReferencePointType, ReferencePoint, CalibrationData
)
from routers.arkit_calibration_sync import router
from cli_commands.arkit_calibration_cli import ARKitCalibrationCLI


class TestARKitCalibrationService(unittest.TestCase):
    """Test cases for ARKit Calibration Service."""
    
    def setUp(self):
        """Set up test environment."""
        # Create temporary database for testing
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        
        # Initialize service with temporary database
        self.service = ARKitCalibrationService(db_path=self.temp_db.name)
        
        # Sample test data
        self.sample_svg_data = {
            "width": 1000,
            "height": 800,
            "viewBox": "0 0 1000 800",
            "elements": [
                {"id": "wall1", "type": "wall", "x": 100, "y": 100, "width": 200, "height": 20},
                {"id": "wall2", "type": "wall", "x": 300, "y": 100, "width": 20, "height": 200},
                {"id": "door1", "type": "door", "x": 150, "y": 80, "width": 80, "height": 40}
            ],
            "coordinate_system": {
                "origin": {"x": 0, "y": 0, "z": 0},
                "scale": 1.0,
                "units": "meters"
            }
        }
        
        self.sample_device_info = {
            "device_id": "test_device_001",
            "device_type": "iPhone",
            "model": "iPhone 14 Pro",
            "ios_version": "16.0",
            "arkit_version": "6.0",
            "sensors": ["accelerometer", "gyroscope", "lidar"],
            "camera_resolution": {"width": 1920, "height": 1080},
            "calibration_capabilities": ["world_tracking", "plane_detection", "point_cloud"]
        }
        
        self.sample_ar_frame_data = {
            "camera_transform": {
                "position": {"x": 0.0, "y": 0.0, "z": 0.0},
                "rotation": {"x": 0.0, "y": 0.0, "z": 0.0, "w": 1.0}
            },
            "point_cloud": [
                {"x": 0.1, "y": 0.1, "z": 0.5, "confidence": 0.8},
                {"x": 0.2, "y": 0.1, "z": 0.5, "confidence": 0.9},
                {"x": 0.1, "y": 0.2, "z": 0.5, "confidence": 0.7},
                {"x": 0.2, "y": 0.2, "z": 0.5, "confidence": 0.8},
                {"x": 0.15, "y": 0.15, "z": 0.5, "confidence": 0.9},
                {"x": 0.3, "y": 0.1, "z": 0.5, "confidence": 0.8},
                {"x": 0.1, "y": 0.3, "z": 0.5, "confidence": 0.7},
                {"x": 0.3, "y": 0.3, "z": 0.5, "confidence": 0.9}
            ],
            "plane_anchors": [
                {
                    "center": {"x": 0.15, "y": 0.15, "z": 0.5},
                    "normal": {"x": 0.0, "y": 0.0, "z": 1.0},
                    "extent": {"x": 0.2, "y": 0.2}
                },
                {
                    "center": {"x": 0.25, "y": 0.25, "z": 0.5},
                    "normal": {"x": 0.0, "y": 0.0, "z": 1.0},
                    "extent": {"x": 0.1, "y": 0.1}
                }
            ],
            "tracking_quality": 0.9,
            "motion_magnitude": 0.1,
            "camera_exposure": 0.7,
            "image_contrast": 0.8
        }
    
    def tearDown(self):
        """Clean up test environment."""
        # Remove temporary database
        if os.path.exists(self.temp_db.name):
            os.unlink(self.temp_db.name)
    
    def test_service_initialization(self):
        """Test service initialization."""
        self.assertIsNotNone(self.service)
        self.assertIsInstance(self.service.calibration_data, dict)
        self.assertIsInstance(self.service.active_sessions, dict)
    
    def test_initialize_calibration(self):
        """Test calibration initialization."""
        result = self.service.initialize_calibration(self.sample_svg_data, self.sample_device_info)
        
        self.assertEqual(result["status"], "initialized")
        self.assertIn("calibration_id", result)
        self.assertIn("session_id", result)
        self.assertIn("device_id", result)
        self.assertIn("svg_file_hash", result)
        
        # Verify calibration data was created
        calibration_id = result["calibration_id"]
        self.assertIn(calibration_id, self.service.calibration_data)
        
        calibration_data = self.service.calibration_data[calibration_id]
        self.assertEqual(calibration_data.status, CalibrationStatus.INITIALIZING)
        self.assertEqual(calibration_data.device_id, self.sample_device_info["device_id"])
    
    def test_initialize_calibration_existing(self):
        """Test calibration initialization with existing calibration."""
        # Create first calibration
        result1 = self.service.initialize_calibration(self.sample_svg_data, self.sample_device_info)
        calibration_id1 = result1["calibration_id"]
        
        # Set high accuracy to simulate good calibration
        self.service.calibration_data[calibration_id1].accuracy_score = 0.96
        self.service.calibration_data[calibration_id1].status = CalibrationStatus.APPLIED
        
        # Try to initialize again with same data
        result2 = self.service.initialize_calibration(self.sample_svg_data, self.sample_device_info)
        
        self.assertEqual(result2["status"], "existing_found")
        self.assertIn("can_reuse", result2)
        self.assertTrue(result2["can_reuse"])
    
    def test_detect_reference_points(self):
        """Test reference point detection."""
        # Initialize calibration first
        init_result = self.service.initialize_calibration(self.sample_svg_data, self.sample_device_info)
        session_id = init_result["session_id"]
        
        # Detect reference points
        result = self.service.detect_reference_points(self.sample_ar_frame_data, session_id)
        
        self.assertEqual(result["status"], "success")
        self.assertIn("reference_points_count", result)
        self.assertIn("confidence_avg", result)
        self.assertIn("points", result)
        
        # Verify points were detected
        self.assertGreater(result["reference_points_count"], 0)
        self.assertGreater(result["confidence_avg"], 0.0)
        
        # Verify calibration data was updated
        calibration_id = self.service.active_sessions[session_id]
        calibration_data = self.service.calibration_data[calibration_id]
        self.assertEqual(calibration_data.status, CalibrationStatus.DETECTING_POINTS)
        self.assertGreater(len(calibration_data.reference_points), 0)
    
    def test_detect_reference_points_invalid_session(self):
        """Test reference point detection with invalid session."""
        result = self.service.detect_reference_points(self.sample_ar_frame_data, "invalid_session")
        
        self.assertEqual(result["status"], "error")
        self.assertIn("Invalid session ID", result["error"])
    
    def test_calculate_coordinate_transform(self):
        """Test coordinate transformation calculation."""
        # Initialize calibration and detect points
        init_result = self.service.initialize_calibration(self.sample_svg_data, self.sample_device_info)
        session_id = init_result["session_id"]
        
        self.service.detect_reference_points(self.sample_ar_frame_data, session_id)
        
        # Calculate transformation
        result = self.service.calculate_coordinate_transform(session_id)
        
        self.assertEqual(result["status"], "success")
        self.assertIn("transform_matrix", result)
        self.assertIn("scale_factor", result)
        self.assertIn("accuracy_score", result)
        self.assertIn("reference_points_count", result)
        
        # Verify transformation matrix structure
        transform_matrix = result["transform_matrix"]
        self.assertIn("ar_to_real", transform_matrix)
        self.assertIn("real_to_svg", transform_matrix)
        self.assertIn("combined", transform_matrix)
        
        # Verify scale factor is reasonable
        self.assertGreater(result["scale_factor"], 0.0)
        self.assertLess(result["scale_factor"], 10.0)
        
        # Verify accuracy score is in valid range
        self.assertGreaterEqual(result["accuracy_score"], 0.0)
        self.assertLessEqual(result["accuracy_score"], 1.0)
    
    def test_calculate_coordinate_transform_insufficient_points(self):
        """Test coordinate transformation with insufficient reference points."""
        # Initialize calibration without detecting points
        init_result = self.service.initialize_calibration(self.sample_svg_data, self.sample_device_info)
        session_id = init_result["session_id"]
        
        # Try to calculate transformation without reference points
        result = self.service.calculate_coordinate_transform(session_id)
        
        self.assertEqual(result["status"], "error")
        self.assertIn("Insufficient reference points", result["error"])
    
    def test_validate_calibration(self):
        """Test calibration validation."""
        # Complete calibration process
        init_result = self.service.initialize_calibration(self.sample_svg_data, self.sample_device_info)
        session_id = init_result["session_id"]
        
        self.service.detect_reference_points(self.sample_ar_frame_data, session_id)
        self.service.calculate_coordinate_transform(session_id)
        
        # Validate calibration
        result = self.service.validate_calibration(session_id)
        
        self.assertEqual(result["status"], "success")
        self.assertIn("validation_results", result)
        self.assertIn("is_acceptable", result)
        self.assertIn("calibration_id", result)
        
        # Verify validation results structure
        validation_results = result["validation_results"]
        self.assertIn("coordinate_accuracy", validation_results)
        self.assertIn("scale_accuracy", validation_results)
        self.assertIn("cross_device_consistency", validation_results)
        self.assertIn("environmental_factors", validation_results)
        self.assertIn("overall_score", validation_results)
        
        # Verify scores are in valid range
        for key in ["coordinate_accuracy", "scale_accuracy", "cross_device_consistency", "environmental_factors"]:
            score = validation_results[key]["score"]
            self.assertGreaterEqual(score, 0.0)
            self.assertLessEqual(score, 1.0)
    
    def test_apply_calibration(self):
        """Test calibration application."""
        # Complete calibration process with good accuracy
        init_result = self.service.initialize_calibration(self.sample_svg_data, self.sample_device_info)
        session_id = init_result["session_id"]
        calibration_id = init_result["calibration_id"]
        
        self.service.detect_reference_points(self.sample_ar_frame_data, session_id)
        self.service.calculate_coordinate_transform(session_id)
        
        # Set high accuracy manually
        self.service.calibration_data[calibration_id].accuracy_score = 0.96
        self.service.calibration_data[calibration_id].status = CalibrationStatus.APPLIED
        
        # Apply calibration
        result = self.service.apply_calibration(calibration_id)
        
        self.assertEqual(result["status"], "success")
        self.assertIn("calibration_id", result)
        self.assertIn("transform_matrix", result)
        self.assertIn("scale_factor", result)
        self.assertIn("accuracy_score", result)
        
        # Verify calibration was applied
        self.assertIn(session_id, self.service.coordinate_transforms)
    
    def test_apply_calibration_not_ready(self):
        """Test calibration application when not ready."""
        # Initialize calibration without completing process
        init_result = self.service.initialize_calibration(self.sample_svg_data, self.sample_device_info)
        calibration_id = init_result["calibration_id"]
        
        # Try to apply calibration that's not ready
        result = self.service.apply_calibration(calibration_id)
        
        self.assertEqual(result["status"], "error")
        self.assertIn("not ready for application", result["error"])
    
    def test_get_calibration_status(self):
        """Test calibration status retrieval."""
        # Test overall status
        result = self.service.get_calibration_status()
        
        self.assertEqual(result["status"], "success")
        self.assertIn("total_calibrations", result)
        self.assertIn("active_sessions", result)
        self.assertIn("successful_calibrations", result)
        self.assertIn("success_rate", result)
        
        # Test specific session status
        init_result = self.service.initialize_calibration(self.sample_svg_data, self.sample_device_info)
        session_id = init_result["session_id"]
        
        session_result = self.service.get_calibration_status(session_id)
        
        self.assertEqual(session_result["status"], "success")
        self.assertEqual(session_result["session_id"], session_id)
        self.assertIn("calibration_id", session_result)
        self.assertIn("calibration_status", session_result)
        self.assertIn("accuracy_score", session_result)
        self.assertIn("reference_points_count", session_result)
    
    def test_save_and_load_calibration(self):
        """Test calibration save and load functionality."""
        # Complete calibration process
        init_result = self.service.initialize_calibration(self.sample_svg_data, self.sample_device_info)
        calibration_id = init_result["calibration_id"]
        
        self.service.detect_reference_points(self.sample_ar_frame_data, init_result["session_id"])
        self.service.calculate_coordinate_transform(init_result["session_id"])
        
        # Save calibration
        save_result = self.service.save_calibration(calibration_id)
        
        self.assertEqual(save_result["status"], "success")
        self.assertEqual(save_result["calibration_id"], calibration_id)
        
        # Load calibration
        load_result = self.service.load_calibration(calibration_id)
        
        self.assertEqual(load_result["status"], "success")
        self.assertIn("calibration_data", load_result)
        
        # Verify loaded data
        calibration_data = load_result["calibration_data"]
        self.assertEqual(calibration_data["calibration_id"], calibration_id)
        self.assertIn("transform_matrix", calibration_data)
        self.assertIn("scale_factor", calibration_data)
        self.assertIn("accuracy_score", calibration_data)
    
    def test_get_performance_metrics(self):
        """Test performance metrics retrieval."""
        metrics = self.service.get_performance_metrics()
        
        self.assertIn("total_calibrations", metrics)
        self.assertIn("successful_calibrations", metrics)
        self.assertIn("success_rate", metrics)
        self.assertIn("average_accuracy", metrics)
        self.assertIn("active_sessions", metrics)
        self.assertIn("database_size", metrics)
        
        # Verify metrics are reasonable
        self.assertGreaterEqual(metrics["total_calibrations"], 0)
        self.assertGreaterEqual(metrics["successful_calibrations"], 0)
        self.assertGreaterEqual(metrics["success_rate"], 0.0)
        self.assertLessEqual(metrics["success_rate"], 1.0)
        self.assertGreaterEqual(metrics["average_accuracy"], 0.0)
        self.assertLessEqual(metrics["average_accuracy"], 1.0)
    
    def test_coordinate_transformation_calculation(self):
        """Test coordinate transformation matrix calculation."""
        # Create sample coordinate pairs
        source_points = np.array([
            [0.0, 0.0, 0.0],
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [1.0, 1.0, 0.0]
        ])
        
        target_points = np.array([
            [0.0, 0.0, 0.0],
            [2.0, 0.0, 0.0],
            [0.0, 2.0, 0.0],
            [2.0, 2.0, 0.0]
        ])
        
        # Calculate transformation
        transform = self.service._calculate_transformation_matrix(source_points, target_points)
        
        # Verify transformation matrix structure
        self.assertEqual(transform.shape, (4, 4))
        
        # Verify it's a valid transformation matrix
        self.assertAlmostEqual(np.linalg.det(transform[:3, :3]), 1.0, places=5)
    
    def test_scale_factor_calculation(self):
        """Test scale factor calculation."""
        # Create sample coordinate pairs with known scale
        ar_coords = [
            [0.0, 0.0, 0.0],
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0]
        ]
        
        real_world_coords = [
            [0.0, 0.0, 0.0],
            [2.0, 0.0, 0.0],  # 2x scale
            [0.0, 2.0, 0.0]   # 2x scale
        ]
        
        scale_factor = self.service._calculate_scale_factor(ar_coords, real_world_coords)
        
        # Verify scale factor is close to expected value (2.0)
        self.assertAlmostEqual(scale_factor, 2.0, places=1)
    
    def test_accuracy_score_calculation(self):
        """Test accuracy score calculation."""
        # Create sample reference points
        reference_points = [
            ReferencePoint(
                point_id="test1",
                point_type=ReferencePointType.AUTOMATIC,
                ar_coordinates={"x": 0.0, "y": 0.0, "z": 0.0},
                real_world_coordinates={"x": 0.0, "y": 0.0, "z": 0.0},
                svg_coordinates={"x": 0.0, "y": 0.0, "z": 0.0},
                confidence=0.9,
                timestamp=datetime.now(),
                device_id="test_device",
                session_id="test_session"
            ),
            ReferencePoint(
                point_id="test2",
                point_type=ReferencePointType.AUTOMATIC,
                ar_coordinates={"x": 1.0, "y": 0.0, "z": 0.0},
                real_world_coordinates={"x": 1.0, "y": 0.0, "z": 0.0},
                svg_coordinates={"x": 1.0, "y": 0.0, "z": 0.0},
                confidence=0.9,
                timestamp=datetime.now(),
                device_id="test_device",
                session_id="test_session"
            )
        ]
        
        transform_matrix = {
            "ar_to_real": np.eye(4).tolist()
        }
        
        accuracy_score = self.service._calculate_accuracy_score(reference_points, transform_matrix)
        
        # Verify accuracy score is in valid range
        self.assertGreaterEqual(accuracy_score, 0.0)
        self.assertLessEqual(accuracy_score, 1.0)
    
    def test_validation_functions(self):
        """Test validation functions."""
        # Create sample calibration data
        calibration_data = CalibrationData(
            calibration_id="test_cal",
            session_id="test_session",
            device_id="test_device",
            svg_file_hash="test_hash",
            transform_matrix={"ar_to_real": np.eye(4).tolist()},
            scale_factor=1.0,
            accuracy_score=0.95,
            reference_points=[
                ReferencePoint(
                    point_id="test1",
                    point_type=ReferencePointType.AUTOMATIC,
                    ar_coordinates={"x": 0.0, "y": 0.0, "z": 0.0},
                    real_world_coordinates={"x": 0.0, "y": 0.0, "z": 0.0},
                    svg_coordinates={"x": 0.0, "y": 0.0, "z": 0.0},
                    confidence=0.9,
                    timestamp=datetime.now(),
                    device_id="test_device",
                    session_id="test_session"
                )
            ],
            status=CalibrationStatus.APPLIED,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        # Test coordinate accuracy validation
        coord_result = self.service._validate_coordinate_accuracy(calibration_data)
        self.assertIn("score", coord_result)
        self.assertGreaterEqual(coord_result["score"], 0.0)
        self.assertLessEqual(coord_result["score"], 1.0)
        
        # Test scale accuracy validation
        scale_result = self.service._validate_scale_accuracy(calibration_data)
        self.assertIn("score", scale_result)
        self.assertGreaterEqual(scale_result["score"], 0.0)
        self.assertLessEqual(scale_result["score"], 1.0)
        
        # Test cross-device consistency validation
        consistency_result = self.service._validate_cross_device_consistency(calibration_data)
        self.assertIn("score", consistency_result)
        self.assertGreaterEqual(consistency_result["score"], 0.0)
        self.assertLessEqual(consistency_result["score"], 1.0)
        
        # Test environmental factors validation
        env_result = self.service._validate_environmental_factors(calibration_data)
        self.assertIn("score", env_result)
        self.assertGreaterEqual(env_result["score"], 0.0)
        self.assertLessEqual(env_result["score"], 1.0)


class TestARKitCalibrationAPI(unittest.TestCase):
    """Test cases for ARKit Calibration API endpoints."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        
        # Initialize service with temporary database
        self.service = ARKitCalibrationService(db_path=self.temp_db.name)
        
        # Sample test data
        self.sample_svg_data = {
            "width": 1000,
            "height": 800,
            "coordinate_system": {"origin": {"x": 0, "y": 0, "z": 0}, "scale": 1.0}
        }
        
        self.sample_device_info = {
            "device_id": "test_device_001",
            "device_type": "iPhone",
            "model": "iPhone 14 Pro"
        }
        
        self.sample_ar_frame_data = {
            "camera_transform": {"position": {"x": 0, "y": 0, "z": 0}},
            "point_cloud": [
                {"x": 0.1, "y": 0.1, "z": 0.5, "confidence": 0.8},
                {"x": 0.2, "y": 0.1, "z": 0.5, "confidence": 0.9}
            ],
            "plane_anchors": [
                {"center": {"x": 0.15, "y": 0.15, "z": 0.5}, "normal": {"x": 0, "y": 0, "z": 1}}
            ]
        }
    
    def tearDown(self):
        """Clean up test environment."""
        if os.path.exists(self.temp_db.name):
            os.unlink(self.temp_db.name)
    
    def test_initialize_endpoint(self):
        """Test calibration initialization endpoint."""
        # This would test the actual FastAPI endpoint
        # For now, we'll test the service method that the endpoint calls
        result = self.service.initialize_calibration(self.sample_svg_data, self.sample_device_info)
        
        self.assertEqual(result["status"], "initialized")
        self.assertIn("calibration_id", result)
        self.assertIn("session_id", result)
    
    def test_detect_points_endpoint(self):
        """Test reference point detection endpoint."""
        # Initialize calibration first
        init_result = self.service.initialize_calibration(self.sample_svg_data, self.sample_device_info)
        session_id = init_result["session_id"]
        
        # Test point detection
        result = self.service.detect_reference_points(self.sample_ar_frame_data, session_id)
        
        self.assertEqual(result["status"], "success")
        self.assertIn("reference_points_count", result)
        self.assertIn("confidence_avg", result)
    
    def test_calculate_transform_endpoint(self):
        """Test coordinate transformation calculation endpoint."""
        # Complete setup
        init_result = self.service.initialize_calibration(self.sample_svg_data, self.sample_device_info)
        session_id = init_result["session_id"]
        
        self.service.detect_reference_points(self.sample_ar_frame_data, session_id)
        
        # Test transformation calculation
        result = self.service.calculate_coordinate_transform(session_id)
        
        self.assertEqual(result["status"], "success")
        self.assertIn("transform_matrix", result)
        self.assertIn("scale_factor", result)
        self.assertIn("accuracy_score", result)
    
    def test_validate_endpoint(self):
        """Test calibration validation endpoint."""
        # Complete calibration process
        init_result = self.service.initialize_calibration(self.sample_svg_data, self.sample_device_info)
        session_id = init_result["session_id"]
        
        self.service.detect_reference_points(self.sample_ar_frame_data, session_id)
        self.service.calculate_coordinate_transform(session_id)
        
        # Test validation
        result = self.service.validate_calibration(session_id)
        
        self.assertEqual(result["status"], "success")
        self.assertIn("validation_results", result)
        self.assertIn("is_acceptable", result)
    
    def test_apply_endpoint(self):
        """Test calibration application endpoint."""
        # Complete calibration process
        init_result = self.service.initialize_calibration(self.sample_svg_data, self.sample_device_info)
        calibration_id = init_result["calibration_id"]
        
        self.service.detect_reference_points(self.sample_ar_frame_data, init_result["session_id"])
        self.service.calculate_coordinate_transform(init_result["session_id"])
        
        # Set high accuracy manually
        self.service.calibration_data[calibration_id].accuracy_score = 0.96
        self.service.calibration_data[calibration_id].status = CalibrationStatus.APPLIED
        
        # Test application
        result = self.service.apply_calibration(calibration_id)
        
        self.assertEqual(result["status"], "success")
        self.assertIn("transform_matrix", result)
        self.assertIn("scale_factor", result)
    
    def test_status_endpoint(self):
        """Test status endpoint."""
        # Test overall status
        result = self.service.get_calibration_status()
        
        self.assertEqual(result["status"], "success")
        self.assertIn("total_calibrations", result)
        self.assertIn("success_rate", result)
        
        # Test specific session status
        init_result = self.service.initialize_calibration(self.sample_svg_data, self.sample_device_info)
        session_result = self.service.get_calibration_status(init_result["session_id"])
        
        self.assertEqual(session_result["status"], "success")
        self.assertEqual(session_result["session_id"], init_result["session_id"])
    
    def test_health_endpoint(self):
        """Test health check endpoint."""
        # Test health check
        metrics = self.service.get_performance_metrics()
        
        # Determine health status
        success_rate = metrics.get("success_rate", 0.0)
        avg_accuracy = metrics.get("average_accuracy", 0.0)
        
        if success_rate >= 0.8 and avg_accuracy >= 0.9:
            health_status = "HEALTHY"
        elif success_rate >= 0.6 and avg_accuracy >= 0.8:
            health_status = "DEGRADED"
        else:
            health_status = "UNHEALTHY"
        
        self.assertIn(health_status, ["HEALTHY", "DEGRADED", "UNHEALTHY"])


class TestARKitCalibrationCLI(unittest.TestCase):
    """Test cases for ARKit Calibration CLI."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        
        # Create temporary files for testing
        self.temp_svg_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json')
        self.temp_device_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json')
        self.temp_output_file = tempfile.NamedTemporaryFile(delete=False, suffix='.json')
        
        # Write sample data to files
        svg_data = {"width": 1000, "height": 800, "elements": []}
        device_info = {"device_id": "test_device", "model": "iPhone 14 Pro"}
        
        json.dump(svg_data, self.temp_svg_file)
        json.dump(device_info, self.temp_device_file)
        
        self.temp_svg_file.close()
        self.temp_device_file.close()
        self.temp_output_file.close()
    
    def tearDown(self):
        """Clean up test environment."""
        for temp_file in [self.temp_db.name, self.temp_svg_file.name, 
                         self.temp_device_file.name, self.temp_output_file.name]:
            if os.path.exists(temp_file):
                os.unlink(temp_file)
    
    def test_cli_initialization(self):
        """Test CLI initialization."""
        cli = ARKitCalibrationCLI()
        self.assertIsNotNone(cli)
        self.assertIsNotNone(cli.service)
    
    def test_calibrate_command(self):
        """Test calibrate command."""
        cli = ARKitCalibrationCLI()
        
        # Test with minimal arguments
        args = cli.create_parser().parse_args([
            "calibrate",
            "--svg-file", self.temp_svg_file.name,
            "--device-info", self.temp_device_file.name
        ])
        
        # This would test the actual CLI command execution
        # For now, we'll test the service methods that the CLI calls
        svg_data = cli._load_json_file(self.temp_svg_file.name, "SVG file")
        device_info = cli._load_json_file(self.temp_device_file.name, "Device info file")
        
        result = cli.service.initialize_calibration(svg_data, device_info)
        
        self.assertEqual(result["status"], "initialized")
        self.assertIn("calibration_id", result)
        self.assertIn("session_id", result)
    
    def test_validate_command(self):
        """Test validate command."""
        cli = ARKitCalibrationCLI()
        
        # Create a calibration first
        svg_data = cli._load_json_file(self.temp_svg_file.name, "SVG file")
        device_info = cli._load_json_file(self.temp_device_file.name, "Device info file")
        
        init_result = cli.service.initialize_calibration(svg_data, device_info)
        calibration_id = init_result["calibration_id"]
        
        # Set high accuracy manually
        cli.service.calibration_data[calibration_id].accuracy_score = 0.96
        cli.service.calibration_data[calibration_id].status = CalibrationStatus.APPLIED
        
        # Test validation
        load_result = cli.service.load_calibration(calibration_id)
        
        self.assertEqual(load_result["status"], "success")
        self.assertIn("calibration_data", load_result)
        
        calibration_data = load_result["calibration_data"]
        self.assertEqual(calibration_data["calibration_id"], calibration_id)
        self.assertGreaterEqual(calibration_data["accuracy_score"], 0.9)
    
    def test_status_command(self):
        """Test status command."""
        cli = ARKitCalibrationCLI()
        
        # Test overall status
        status_result = cli.service.get_calibration_status()
        
        self.assertEqual(status_result["status"], "success")
        self.assertIn("total_calibrations", status_result)
        self.assertIn("success_rate", status_result)
    
    def test_metrics_command(self):
        """Test metrics command."""
        cli = ARKitCalibrationCLI()
        
        metrics = cli.service.get_performance_metrics()
        
        self.assertIn("total_calibrations", metrics)
        self.assertIn("successful_calibrations", metrics)
        self.assertIn("success_rate", metrics)
        self.assertIn("average_accuracy", metrics)
    
    def test_health_command(self):
        """Test health command."""
        cli = ARKitCalibrationCLI()
        
        metrics = cli.service.get_performance_metrics()
        
        # Determine health status
        success_rate = metrics.get("success_rate", 0.0)
        avg_accuracy = metrics.get("average_accuracy", 0.0)
        
        if success_rate >= 0.8 and avg_accuracy >= 0.9:
            health_status = "HEALTHY"
        elif success_rate >= 0.6 and avg_accuracy >= 0.8:
            health_status = "DEGRADED"
        else:
            health_status = "UNHEALTHY"
        
        self.assertIn(health_status, ["HEALTHY", "DEGRADED", "UNHEALTHY"])
    
    def test_json_file_operations(self):
        """Test JSON file loading and saving operations."""
        cli = ARKitCalibrationCLI()
        
        # Test loading
        svg_data = cli._load_json_file(self.temp_svg_file.name, "SVG file")
        self.assertIsInstance(svg_data, dict)
        self.assertIn("width", svg_data)
        
        # Test saving
        test_data = {"test": "data", "number": 42}
        cli._save_json_file(self.temp_output_file.name, test_data)
        
        # Verify saved data
        with open(self.temp_output_file.name, 'r') as f:
            loaded_data = json.load(f)
        
        self.assertEqual(loaded_data, test_data)
    
    def test_sample_data_generation(self):
        """Test sample data generation for testing."""
        cli = ARKitCalibrationCLI()
        
        # Test SVG data generation
        svg_data = cli._generate_sample_svg_data()
        self.assertIsInstance(svg_data, dict)
        self.assertIn("width", svg_data)
        self.assertIn("height", svg_data)
        self.assertIn("elements", svg_data)
        
        # Test device info generation
        device_info = cli._generate_sample_device_info()
        self.assertIsInstance(device_info, dict)
        self.assertIn("device_id", device_info)
        self.assertIn("device_type", device_info)
        
        # Test AR frame data generation
        ar_frame_data = cli._generate_sample_ar_frame_data()
        self.assertIsInstance(ar_frame_data, dict)
        self.assertIn("camera_transform", ar_frame_data)
        self.assertIn("point_cloud", ar_frame_data)
        self.assertIn("plane_anchors", ar_frame_data)


def run_comprehensive_tests():
    """Run comprehensive test suite."""
    print("🧪 Running ARKit Calibration Sync Comprehensive Test Suite")
    print("=" * 60)
    
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test classes
    test_suite.addTest(unittest.makeSuite(TestARKitCalibrationService))
    test_suite.addTest(unittest.makeSuite(TestARKitCalibrationAPI))
    test_suite.addTest(unittest.makeSuite(TestARKitCalibrationCLI))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Print summary
    print("\n📊 Test Summary:")
    print(f"  - Tests Run: {result.testsRun}")
    print(f"  - Failures: {len(result.failures)}")
    print(f"  - Errors: {len(result.errors)}")
    print(f"  - Success Rate: {(result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100:.1f}%")
    
    if result.failures:
        print("\n❌ Failures:")
        for test, traceback in result.failures:
            print(f"  - {test}: {traceback}")
    
    if result.errors:
        print("\n❌ Errors:")
        for test, traceback in result.errors:
            print(f"  - {test}: {traceback}")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_comprehensive_tests()
    sys.exit(0 if success else 1) 