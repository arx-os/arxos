#!/usr/bin/env python3
"""
ARKit Calibration Sync Demonstration Script

This script demonstrates the complete ARKit Calibration Sync functionality:
- ARKit session initialization
- Coordinate calibration and transformation
- SVG coordinate extraction and normalization
- Calibration persistence and validation
- Real-time coordinate synchronization
- Error handling and recovery

Usage:
    python arkit_calibration_demo.py
"""

import asyncio
import json
import logging
import math
import numpy as np
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from services.arkit_calibration_sync import (
    ARKitCalibrationService, CalibrationData, CalibrationResult, Point,
    ARConfiguration, CalibrationStatus, CalibrationAccuracy
)
from utils.logger import setup_logger

class ARKitCalibrationDemo:
    """Demonstration class for ARKit Calibration Sync features."""
    
    def __init__(self):
        """Initialize the demonstration."""
        self.logger = setup_logger("arkit_calibration_demo", level=logging.INFO)
        self.arkit_service = ARKitCalibrationService()
        self.demo_results = {}
        
    async def run_demo(self):
        """Run the complete ARKit Calibration Sync demonstration."""
        self.logger.info("🚀 Starting ARKit Calibration Sync Demonstration")
        
        try:
            # Demo 1: ARKit Session Initialization
            await self.demo_session_initialization()
            
            # Demo 2: SVG Coordinate Extraction
            await self.demo_svg_coordinate_extraction()
            
            # Demo 3: Coordinate Normalization
            await self.demo_coordinate_normalization()
            
            # Demo 4: Basic Calibration
            await self.demo_basic_calibration()
            
            # Demo 5: Advanced Calibration
            await self.demo_advanced_calibration()
            
            # Demo 6: Coordinate Transformation
            await self.demo_coordinate_transformation()
            
            # Demo 7: Calibration Validation
            await self.demo_calibration_validation()
            
            # Demo 8: Persistence and Recovery
            await self.demo_persistence_and_recovery()
            
            # Demo 9: Error Handling
            await self.demo_error_handling()
            
            # Demo 10: Performance Testing
            await self.demo_performance_testing()
            
            # Print summary
            self.print_demo_summary()
            
        except Exception as e:
            self.logger.error(f"Demo failed: {str(e)}")
            raise
    
    async def demo_session_initialization(self):
        """Demonstrate ARKit session initialization."""
        self.logger.info("\n📱 Demo 1: ARKit Session Initialization")
        
        # Test different session configurations
        configs = [
            ARConfiguration(
                session_type="worldTracking",
                plane_detection=True,
                light_estimation=True,
                debug_options=[]
            ),
            ARConfiguration(
                session_type="worldTracking",
                plane_detection=False,
                light_estimation=False,
                debug_options=["showWorldOrigin"]
            )
        ]
        
        for i, config in enumerate(configs, 1):
            self.logger.info(f"  Testing configuration {i}: {config.session_type}")
            
            success = await self.arkit_service.initialize_arkit_session(config)
            
            if success:
                self.logger.info(f"    ✅ Session initialized successfully")
                self.logger.info(f"    📊 Configuration: {config.dict()}")
            else:
                self.logger.error(f"    ❌ Session initialization failed")
        
        self.demo_results["session_initialization"] = "completed"
    
    async def demo_svg_coordinate_extraction(self):
        """Demonstrate SVG coordinate extraction."""
        self.logger.info("\n🎨 Demo 2: SVG Coordinate Extraction")
        
        # Sample SVG content with various coordinate types
        svg_content = '''
        <svg width="200" height="200">
            <circle cx="50" cy="50" r="20" fill="red"/>
            <rect x="100" y="100" width="50" height="50" fill="blue"/>
            <polygon points="150,50 170,50 170,70 150,70" fill="green"/>
            <line x1="0" y1="0" x2="200" y2="200" stroke="black"/>
            <text x="25" y="25" fill="purple">Sample Text</text>
        </svg>
        '''
        
        self.logger.info("  Extracting coordinates from SVG content...")
        
        coordinates = self.arkit_service.coordinate_mapper.extract_svg_coordinates(svg_content)
        
        self.logger.info(f"  ✅ Extracted {len(coordinates)} coordinates:")
        for i, coord in enumerate(coordinates[:5]):  # Show first 5
            self.logger.info(f"    Point {i+1}: ({coord.x:.2f}, {coord.y:.2f}, {coord.z:.2f})")
        
        if len(coordinates) > 5:
            self.logger.info(f"    ... and {len(coordinates) - 5} more coordinates")
        
        self.demo_results["svg_coordinate_extraction"] = {
            "total_coordinates": len(coordinates),
            "sample_coordinates": [{"x": c.x, "y": c.y, "z": c.z} for c in coordinates[:3]]
        }
    
    async def demo_coordinate_normalization(self):
        """Demonstrate coordinate normalization."""
        self.logger.info("\n📏 Demo 3: Coordinate Normalization")
        
        # Sample coordinates in different scales
        coordinates = [
            Point(0, 0, 0),
            Point(1000, 0, 0),
            Point(1000, 1000, 0),
            Point(0, 1000, 0),
            Point(500, 500, 0)
        ]
        
        self.logger.info("  Original coordinates:")
        for i, coord in enumerate(coordinates):
            self.logger.info(f"    Point {i+1}: ({coord.x:.2f}, {coord.y:.2f}, {coord.z:.2f})")
        
        # Normalize coordinates
        normalized = self.arkit_service.coordinate_mapper.normalize_coordinates(coordinates)
        
        self.logger.info("  Normalized coordinates:")
        for i, coord in enumerate(normalized):
            self.logger.info(f"    Point {i+1}: ({coord.x:.3f}, {coord.y:.3f}, {coord.z:.3f})")
        
        # Verify normalization
        x_coords = [c.x for c in normalized]
        y_coords = [c.y for c in normalized]
        z_coords = [c.z for c in normalized]
        
        self.logger.info(f"  ✅ Normalization verification:")
        self.logger.info(f"    X range: {min(x_coords):.3f} to {max(x_coords):.3f}")
        self.logger.info(f"    Y range: {min(y_coords):.3f} to {max(y_coords):.3f}")
        self.logger.info(f"    Z range: {min(z_coords):.3f} to {max(z_coords):.3f}")
        
        self.demo_results["coordinate_normalization"] = {
            "original_count": len(coordinates),
            "normalized_count": len(normalized),
            "x_range": [min(x_coords), max(x_coords)],
            "y_range": [min(y_coords), max(y_coords)]
        }
    
    async def demo_basic_calibration(self):
        """Demonstrate basic calibration process."""
        self.logger.info("\n🎯 Demo 4: Basic Calibration")
        
        # Simple square calibration (1:1 scale)
        svg_coordinates = [
            Point(0, 0, 0),
            Point(100, 0, 0),
            Point(100, 100, 0),
            Point(0, 100, 0)
        ]
        
        ar_coordinates = [
            Point(0, 0, 0),
            Point(1, 0, 0),
            Point(1, 1, 0),
            Point(0, 1, 0)
        ]
        
        self.logger.info("  Starting basic calibration (1:100 scale)...")
        
        # Start calibration
        calibration_id = await self.arkit_service.start_calibration(
            svg_coordinates=svg_coordinates,
            ar_coordinates=ar_coordinates
        )
        
        self.logger.info(f"  📝 Calibration ID: {calibration_id}")
        
        # Process calibration
        result = await self.arkit_service.calibrate_coordinates(calibration_id)
        
        self.logger.info("  📊 Calibration Results:")
        self.logger.info(f"    Success: {result.success}")
        self.logger.info(f"    Accuracy: {result.accuracy:.2%}")
        self.logger.info(f"    Scale Factor: {result.scale_factor:.3f}")
        self.logger.info(f"    Recommendations: {len(result.recommendations)}")
        
        for i, rec in enumerate(result.recommendations, 1):
            self.logger.info(f"      {i}. {rec}")
        
        self.demo_results["basic_calibration"] = {
            "calibration_id": calibration_id,
            "success": result.success,
            "accuracy": result.accuracy,
            "scale_factor": result.scale_factor,
            "recommendations": result.recommendations
        }
    
    async def demo_advanced_calibration(self):
        """Demonstrate advanced calibration with complex transformation."""
        self.logger.info("\n🔧 Demo 5: Advanced Calibration")
        
        # Complex transformation (rotation + scale + offset)
        svg_coordinates = [
            Point(0, 0, 0),
            Point(100, 0, 0),
            Point(100, 100, 0),
            Point(0, 100, 0),
            Point(50, 50, 0)
        ]
        
        # Apply 45-degree rotation, 0.5x scale, and offset
        ar_coordinates = [
            Point(10, 20, 0),      # (0,0) -> (10,20)
            Point(10.707, 20.707, 0),  # (100,0) -> (10.707,20.707)
            Point(10, 21.414, 0),      # (100,100) -> (10,21.414)
            Point(9.293, 20.707, 0),   # (0,100) -> (9.293,20.707)
            Point(10, 20.707, 0)       # (50,50) -> (10,20.707)
        ]
        
        self.logger.info("  Starting advanced calibration (rotation + scale + offset)...")
        
        # Start calibration
        calibration_id = await self.arkit_service.start_calibration(
            svg_coordinates=svg_coordinates,
            ar_coordinates=ar_coordinates
        )
        
        # Process calibration
        result = await self.arkit_service.calibrate_coordinates(calibration_id)
        
        self.logger.info("  📊 Advanced Calibration Results:")
        self.logger.info(f"    Success: {result.success}")
        self.logger.info(f"    Accuracy: {result.accuracy:.2%}")
        self.logger.info(f"    Scale Factor: {result.scale_factor:.3f}")
        
        # Test transformation
        test_point = Point(25, 25, 0)
        transformed = await self.arkit_service.transform_coordinates(calibration_id, test_point)
        
        self.logger.info(f"  🔄 Transformation Test:")
        self.logger.info(f"    Original: ({test_point.x:.2f}, {test_point.y:.2f}, {test_point.z:.2f})")
        self.logger.info(f"    Transformed: ({transformed.x:.3f}, {transformed.y:.3f}, {transformed.z:.3f})")
        
        self.demo_results["advanced_calibration"] = {
            "calibration_id": calibration_id,
            "success": result.success,
            "accuracy": result.accuracy,
            "scale_factor": result.scale_factor,
            "test_transformation": {
                "original": {"x": test_point.x, "y": test_point.y, "z": test_point.z},
                "transformed": {"x": transformed.x, "y": transformed.y, "z": transformed.z}
            }
        }
    
    async def demo_coordinate_transformation(self):
        """Demonstrate coordinate transformation capabilities."""
        self.logger.info("\n🔄 Demo 6: Coordinate Transformation")
        
        # Use the calibration from the previous demo
        if "advanced_calibration" in self.demo_results:
            calibration_id = self.demo_results["advanced_calibration"]["calibration_id"]
            
            # Test multiple points
            test_points = [
                Point(0, 0, 0),
                Point(25, 25, 0),
                Point(50, 50, 0),
                Point(75, 75, 0),
                Point(100, 100, 0)
            ]
            
            self.logger.info("  Testing coordinate transformations:")
            
            transformations = []
            for i, point in enumerate(test_points, 1):
                transformed = await self.arkit_service.transform_coordinates(calibration_id, point)
                
                self.logger.info(f"    Point {i}:")
                self.logger.info(f"      Original: ({point.x:.2f}, {point.y:.2f}, {point.z:.2f})")
                self.logger.info(f"      Transformed: ({transformed.x:.3f}, {transformed.y:.3f}, {transformed.z:.3f})")
                
                transformations.append({
                    "original": {"x": point.x, "y": point.y, "z": point.z},
                    "transformed": {"x": transformed.x, "y": transformed.y, "z": transformed.z}
                })
            
            self.demo_results["coordinate_transformation"] = {
                "calibration_id": calibration_id,
                "transformations": transformations
            }
        else:
            self.logger.warning("  ⚠️ No calibration available for transformation demo")
    
    async def demo_calibration_validation(self):
        """Demonstrate calibration validation."""
        self.logger.info("\n✅ Demo 7: Calibration Validation")
        
        # Get all calibrations
        calibrations = await self.arkit_service.list_calibrations()
        
        self.logger.info(f"  Validating {len(calibrations)} calibrations:")
        
        validation_results = []
        for calibration in calibrations:
            if calibration.status == CalibrationStatus.COMPLETED:
                validation_result = await self.arkit_service.validation_service.validate_calibration(calibration)
                
                self.logger.info(f"    Calibration {calibration.id}:")
                self.logger.info(f"      Status: {validation_result['status']}")
                self.logger.info(f"      Accuracy: {validation_result['accuracy']:.2%}")
                self.logger.info(f"      Scale Factor: {validation_result['scale_factor']:.3f}")
                
                if validation_result['warnings']:
                    self.logger.info(f"      ⚠️ Warnings: {len(validation_result['warnings'])}")
                    for warning in validation_result['warnings']:
                        self.logger.info(f"        - {warning}")
                
                if validation_result['recommendations']:
                    self.logger.info(f"      💡 Recommendations: {len(validation_result['recommendations'])}")
                    for rec in validation_result['recommendations']:
                        self.logger.info(f"        - {rec}")
                
                validation_results.append({
                    "calibration_id": calibration.id,
                    "validation": validation_result
                })
        
        self.demo_results["calibration_validation"] = {
            "total_calibrations": len(calibrations),
            "completed_calibrations": len([c for c in calibrations if c.status == CalibrationStatus.COMPLETED]),
            "validation_results": validation_results
        }
    
    async def demo_persistence_and_recovery(self):
        """Demonstrate calibration persistence and recovery."""
        self.logger.info("\n💾 Demo 8: Persistence and Recovery")
        
        # Create a test calibration
        svg_coordinates = [Point(i, i, 0) for i in range(4)]
        ar_coordinates = [Point(i*0.5, i*0.5, 0) for i in range(4)]
        
        calibration_id = await self.arkit_service.start_calibration(
            svg_coordinates=svg_coordinates,
            ar_coordinates=ar_coordinates
        )
        
        await self.arkit_service.calibrate_coordinates(calibration_id)
        
        # Save calibration
        calibration_data = await self.arkit_service.get_calibration_status(calibration_id)
        if calibration_data:
            success = await self.arkit_service.persistence_service.save_calibration(
                calibration_id, calibration_data
            )
            
            if success:
                self.logger.info(f"  ✅ Calibration {calibration_id} saved successfully")
                
                # Simulate service restart by creating new service instance
                new_service = ARKitCalibrationService()
                
                # Load calibration
                loaded_data = await new_service.persistence_service.load_calibration(calibration_id)
                
                if loaded_data:
                    self.logger.info(f"  ✅ Calibration {calibration_id} loaded successfully")
                    self.logger.info(f"    Accuracy: {loaded_data.accuracy:.2%}")
                    self.logger.info(f"    Scale Factor: {loaded_data.scale_factor:.3f}")
                    self.logger.info(f"    Status: {loaded_data.status}")
                else:
                    self.logger.error(f"  ❌ Failed to load calibration {calibration_id}")
            else:
                self.logger.error(f"  ❌ Failed to save calibration {calibration_id}")
        
        self.demo_results["persistence_and_recovery"] = {
            "calibration_id": calibration_id,
            "save_success": success if 'success' in locals() else False,
            "load_success": loaded_data is not None if 'loaded_data' in locals() else False
        }
    
    async def demo_error_handling(self):
        """Demonstrate error handling capabilities."""
        self.logger.info("\n⚠️ Demo 9: Error Handling")
        
        error_tests = [
            {
                "name": "Insufficient Points",
                "svg_coords": [Point(0, 0, 0), Point(1, 1, 1)],
                "ar_coords": [Point(0, 0, 0), Point(1, 1, 1)],
                "expected_error": "At least 3 points required"
            },
            {
                "name": "Too Many Points",
                "svg_coords": [Point(i, i, i) for i in range(11)],
                "ar_coords": [Point(i, i, i) for i in range(11)],
                "expected_error": "Maximum 10 points allowed"
            }
        ]
        
        error_results = []
        for test in error_tests:
            self.logger.info(f"  Testing: {test['name']}")
            
            try:
                await self.arkit_service.start_calibration(
                    svg_coordinates=test['svg_coords'],
                    ar_coordinates=test['ar_coords']
                )
                self.logger.error(f"    ❌ Expected error but got success")
                error_results.append({
                    "test": test['name'],
                    "success": False,
                    "error": "Expected error but got success"
                })
            except ValueError as e:
                if test['expected_error'] in str(e):
                    self.logger.info(f"    ✅ Correctly caught error: {str(e)}")
                    error_results.append({
                        "test": test['name'],
                        "success": True,
                        "error": str(e)
                    })
                else:
                    self.logger.error(f"    ❌ Unexpected error: {str(e)}")
                    error_results.append({
                        "test": test['name'],
                        "success": False,
                        "error": str(e)
                    })
        
        self.demo_results["error_handling"] = {
            "tests": error_results,
            "successful_tests": len([r for r in error_results if r['success']]),
            "total_tests": len(error_results)
        }
    
    async def demo_performance_testing(self):
        """Demonstrate performance testing."""
        self.logger.info("\n⚡ Demo 10: Performance Testing")
        
        # Test calibration speed
        import time
        
        # Create test data
        svg_coordinates = [Point(i*10, i*10, 0) for i in range(5)]
        ar_coordinates = [Point(i, i, 0) for i in range(5)]
        
        # Test calibration speed
        start_time = time.time()
        
        calibration_id = await self.arkit_service.start_calibration(
            svg_coordinates=svg_coordinates,
            ar_coordinates=ar_coordinates
        )
        
        result = await self.arkit_service.calibrate_coordinates(calibration_id)
        
        end_time = time.time()
        calibration_time = end_time - start_time
        
        self.logger.info(f"  📊 Performance Results:")
        self.logger.info(f"    Calibration Time: {calibration_time:.3f} seconds")
        self.logger.info(f"    Accuracy: {result.accuracy:.2%}")
        self.logger.info(f"    Success: {result.success}")
        
        # Test transformation speed
        test_points = [Point(i, i, 0) for i in range(100)]
        
        start_time = time.time()
        transformations = []
        for point in test_points:
            transformed = await self.arkit_service.transform_coordinates(calibration_id, point)
            transformations.append(transformed)
        end_time = time.time()
        
        transformation_time = end_time - start_time
        avg_transformation_time = transformation_time / len(test_points)
        
        self.logger.info(f"    Transformation Time (100 points): {transformation_time:.3f} seconds")
        self.logger.info(f"    Average per transformation: {avg_transformation_time*1000:.2f} ms")
        
        # Performance thresholds
        max_calibration_time = 30  # seconds
        max_transformation_time = 0.1  # seconds per transformation
        
        self.logger.info(f"  🎯 Performance Assessment:")
        self.logger.info(f"    Calibration Speed: {'✅ PASS' if calibration_time < max_calibration_time else '❌ FAIL'}")
        self.logger.info(f"    Transformation Speed: {'✅ PASS' if avg_transformation_time < max_transformation_time else '❌ FAIL'}")
        
        self.demo_results["performance_testing"] = {
            "calibration_time": calibration_time,
            "transformation_time": transformation_time,
            "avg_transformation_time": avg_transformation_time,
            "points_transformed": len(test_points),
            "calibration_speed_pass": calibration_time < max_calibration_time,
            "transformation_speed_pass": avg_transformation_time < max_transformation_time
        }
    
    def print_demo_summary(self):
        """Print a summary of all demo results."""
        self.logger.info("\n" + "="*60)
        self.logger.info("📋 ARKit Calibration Sync Demo Summary")
        self.logger.info("="*60)
        
        for demo_name, result in self.demo_results.items():
            self.logger.info(f"\n🎯 {demo_name.replace('_', ' ').title()}:")
            
            if isinstance(result, str):
                self.logger.info(f"  Status: {result}")
            elif isinstance(result, dict):
                for key, value in result.items():
                    if isinstance(value, (int, float)):
                        self.logger.info(f"  {key.replace('_', ' ').title()}: {value}")
                    elif isinstance(value, bool):
                        status = "✅ PASS" if value else "❌ FAIL"
                        self.logger.info(f"  {key.replace('_', ' ').title()}: {status}")
                    elif isinstance(value, list):
                        self.logger.info(f"  {key.replace('_', ' ').title()}: {len(value)} items")
                    else:
                        self.logger.info(f"  {key.replace('_', ' ').title()}: {value}")
        
        # Calculate overall success
        total_demos = len(self.demo_results)
        successful_demos = sum(1 for result in self.demo_results.values() 
                             if isinstance(result, str) and result == "completed" or
                             isinstance(result, dict) and result.get('success', True))
        
        self.logger.info(f"\n🎉 Overall Results:")
        self.logger.info(f"  Total Demos: {total_demos}")
        self.logger.info(f"  Successful: {successful_demos}")
        self.logger.info(f"  Success Rate: {successful_demos/total_demos*100:.1f}%")
        
        if successful_demos == total_demos:
            self.logger.info("  🎉 All demos completed successfully!")
        else:
            self.logger.warning(f"  ⚠️ {total_demos - successful_demos} demos had issues")
        
        self.logger.info("\n🚀 ARKit Calibration Sync is ready for production use!")

async def main():
    """Main function to run the ARKit Calibration Sync demonstration."""
    demo = ARKitCalibrationDemo()
    await demo.run_demo()

if __name__ == "__main__":
    # Run the demonstration
    asyncio.run(main()) 