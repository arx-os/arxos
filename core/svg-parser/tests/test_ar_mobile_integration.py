"""
Test suite for AR & Mobile Integration Service

Tests all major functionality including:
- ARKit/ARCore coordinate synchronization
- UWB/BLE calibration for precise positioning
- Offline-first mobile app for field work
- LiDAR + photo input → SVG conversion
- Real-time AR overlay for building systems
- Mobile BIM viewer with AR capabilities
"""

import unittest
import tempfile
import os
import time
import json
import threading
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

from services.ar_mobile_integration import (
    ARMobileIntegration,
    ARCoordinate,
    ARAnchor,
    UWBBeacon,
    LiDARPoint,
    ARSession,
    MobileAppState,
    BIMViewerState
)


class TestARMobileIntegration(unittest.TestCase):
    """Test cases for AR & Mobile Integration service"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Use temporary database for testing
        self.temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        self.temp_db.close()
        
        self.ar_mobile = ARMobileIntegration({
            'ar_positioning_accuracy': 0.05,
            'uwb_range_limit': 50.0,
            'offline_data_retention': 24,
            'lidar_conversion_accuracy': 0.95,
            'mobile_app_timeout': 60,
            'bim_viewer_cache_size': 100
        })
        
        # Override database path for testing
        self.ar_mobile.db_path = Path(self.temp_db.name)
        self.ar_mobile._init_databases()
        
        # Sample data for testing
        self.sample_coordinates = [
            ARCoordinate(1.0, 2.0, 3.0, 0.9, datetime.now(), 'arkit'),
            ARCoordinate(4.0, 5.0, 6.0, 0.8, datetime.now(), 'arcore'),
            ARCoordinate(7.0, 8.0, 9.0, 0.7, datetime.now(), 'uwb')
        ]
        
        self.sample_lidar_points = [
            LiDARPoint(1.0, 2.0, 3.0, 0.5, 0.9, datetime.now()),
            LiDARPoint(4.0, 5.0, 6.0, 0.6, 0.8, datetime.now()),
            LiDARPoint(7.0, 8.0, 9.0, 0.7, 0.7, datetime.now())
        ]
    
    def tearDown(self):
        """Clean up test fixtures"""
        self.ar_mobile.cleanup()
        
        # Remove temporary database
        if os.path.exists(self.temp_db.name):
            os.unlink(self.temp_db.name)
    
    def test_initialization(self):
        """Test service initialization"""
        self.assertIsNotNone(self.ar_mobile)
        self.assertTrue(self.ar_mobile.options['enable_ar_sync'])
        self.assertTrue(self.ar_mobile.options['enable_uwb_calibration'])
        self.assertTrue(self.ar_mobile.options['enable_offline_mode'])
        self.assertEqual(self.ar_mobile.options['ar_positioning_accuracy'], 0.05)
        self.assertEqual(self.ar_mobile.options['uwb_range_limit'], 50.0)
    
    # AR Coordinate Synchronization Tests
    
    def test_create_ar_session(self):
        """Test creating an AR session"""
        building_id = "test_building"
        user_id = "test_user"
        
        session_id = self.ar_mobile.create_ar_session(building_id, user_id)
        
        self.assertIsInstance(session_id, str)
        self.assertIn(session_id, self.ar_mobile.ar_sessions)
        
        session = self.ar_mobile.ar_sessions[session_id]
        self.assertEqual(session.building_id, building_id)
        self.assertEqual(session.user_id, user_id)
        self.assertIsInstance(session.start_time, datetime)
    
    def test_sync_ar_coordinates(self):
        """Test syncing AR coordinates"""
        # Create session first
        session_id = self.ar_mobile.create_ar_session("test_building", "test_user")
        
        # Sync coordinates
        success = self.ar_mobile.sync_ar_coordinates(session_id, self.sample_coordinates, 'arkit')
        
        self.assertTrue(success)
        
        # Check that coordinates were stored
        self.assertGreater(len(self.ar_mobile.coordinate_cache), 0)
    
    def test_get_ar_session(self):
        """Test retrieving an AR session"""
        session_id = self.ar_mobile.create_ar_session("test_building", "test_user")
        
        session = self.ar_mobile.get_ar_session(session_id)
        
        self.assertIsNotNone(session)
        self.assertEqual(session.session_id, session_id)
        self.assertEqual(session.building_id, "test_building")
    
    # UWB/BLE Calibration Tests
    
    def test_calibrate_uwb_beacon(self):
        """Test calibrating a UWB beacon"""
        beacon_id = "test_beacon"
        position = ARCoordinate(10.0, 20.0, 30.0, 0.9, datetime.now(), 'uwb')
        range_distance = 25.0
        accuracy = 0.1
        
        success = self.ar_mobile.calibrate_uwb_beacon(beacon_id, position, range_distance, accuracy)
        
        self.assertTrue(success)
        self.assertIn(beacon_id, self.ar_mobile.uwb_beacons)
        
        beacon = self.ar_mobile.uwb_beacons[beacon_id]
        self.assertEqual(beacon.beacon_id, beacon_id)
        self.assertEqual(beacon.range, range_distance)
        self.assertEqual(beacon.accuracy, accuracy)
        self.assertEqual(beacon.status, 'active')
    
    def test_get_precise_position(self):
        """Test getting precise position using UWB beacons"""
        # Calibrate multiple beacons
        beacons = [
            ("beacon1", ARCoordinate(0.0, 0.0, 0.0, 0.9, datetime.now(), 'uwb'), 10.0, 0.1),
            ("beacon2", ARCoordinate(10.0, 0.0, 0.0, 0.8, datetime.now(), 'uwb'), 15.0, 0.2),
            ("beacon3", ARCoordinate(0.0, 10.0, 0.0, 0.7, datetime.now(), 'uwb'), 12.0, 0.15)
        ]
        
        for beacon_id, position, range_distance, accuracy in beacons:
            self.ar_mobile.calibrate_uwb_beacon(beacon_id, position, range_distance, accuracy)
        
        # Get precise position
        position = self.ar_mobile.get_precise_position(["beacon1", "beacon2", "beacon3"])
        
        self.assertIsNotNone(position)
        self.assertIsInstance(position, ARCoordinate)
        self.assertEqual(position.source, 'uwb')
        self.assertGreater(position.confidence, 0.0)
    
    # Offline Mobile App Tests
    
    def test_sync_offline_data(self):
        """Test syncing offline data for mobile app"""
        user_id = "test_user"
        building_id = "test_building"
        offline_data = {
            "building_info": {"name": "Test Building", "floors": 3},
            "symbols": ["symbol1", "symbol2", "symbol3"],
            "last_updated": datetime.now().isoformat()
        }
        
        success = self.ar_mobile.sync_offline_data(user_id, building_id, offline_data)
        
        self.assertTrue(success)
        self.assertIn(user_id, self.ar_mobile.offline_data)
        self.assertEqual(self.ar_mobile.sync_status[user_id], 'synced')
    
    def test_get_offline_data(self):
        """Test getting offline data for mobile app"""
        user_id = "test_user"
        building_id = "test_building"
        offline_data = {"test": "data"}
        
        self.ar_mobile.sync_offline_data(user_id, building_id, offline_data)
        
        retrieved_data = self.ar_mobile.get_offline_data(user_id)
        
        self.assertEqual(retrieved_data, offline_data)
    
    def test_check_offline_capability(self):
        """Test checking offline capability"""
        user_id = "test_user"
        building_id = "test_building"
        offline_data = {"test": "data"}
        
        self.ar_mobile.sync_offline_data(user_id, building_id, offline_data)
        
        capability = self.ar_mobile.check_offline_capability(user_id)
        
        self.assertIn('has_offline_data', capability)
        self.assertIn('data_size', capability)
        self.assertIn('sync_status', capability)
        self.assertIn('can_work_offline', capability)
        self.assertTrue(capability['has_offline_data'])
        self.assertTrue(capability['can_work_offline'])
    
    # LiDAR Conversion Tests
    
    def test_convert_lidar_to_svg(self):
        """Test converting LiDAR point cloud to SVG"""
        svg_output = self.ar_mobile.convert_lidar_to_svg(self.sample_lidar_points)
        
        self.assertIsInstance(svg_output, str)
        self.assertIn('<svg', svg_output)
        self.assertIn('</svg>', svg_output)
        self.assertIn('lidar-points', svg_output)
        
        # Check that conversion was cached
        self.assertGreater(len(self.ar_mobile.conversion_cache), 0)
    
    def test_convert_empty_lidar(self):
        """Test converting empty LiDAR point cloud"""
        svg_output = self.ar_mobile.convert_lidar_to_svg([])
        
        self.assertEqual(svg_output, '<svg></svg>')
    
    def test_process_photo_input(self):
        """Test processing photo input"""
        photo_data = b"fake_photo_data"
        metadata = {"width": 800, "height": 600, "format": "jpeg"}
        
        svg_output = self.ar_mobile.process_photo_input(photo_data, metadata)
        
        self.assertIsInstance(svg_output, str)
        self.assertIn('<svg', svg_output)
        self.assertIn('Photo Input Processed', svg_output)
    
    # AR Overlay Tests
    
    def test_create_ar_overlay(self):
        """Test creating AR overlay"""
        session_id = self.ar_mobile.create_ar_session("test_building", "test_user")
        
        overlay_data = {
            "type": "building_systems",
            "layers": ["electrical", "plumbing", "hvac"],
            "visibility": True
        }
        
        success = self.ar_mobile.create_ar_overlay(session_id, overlay_data)
        
        self.assertTrue(success)
        self.assertGreater(len(self.ar_mobile.overlay_layers), 0)
    
    def test_update_ar_overlay(self):
        """Test updating AR overlay"""
        session_id = self.ar_mobile.create_ar_session("test_building", "test_user")
        
        initial_data = {"type": "building_systems", "layers": ["electrical"]}
        self.ar_mobile.create_ar_overlay(session_id, initial_data)
        
        overlay_id = list(self.ar_mobile.overlay_layers.keys())[0]
        update_data = {"layers": ["electrical", "plumbing"], "new_feature": True}
        
        success = self.ar_mobile.update_ar_overlay(overlay_id, update_data)
        
        self.assertTrue(success)
    
    def test_toggle_ar_overlay_visibility(self):
        """Test toggling AR overlay visibility"""
        session_id = self.ar_mobile.create_ar_session("test_building", "test_user")
        
        overlay_data = {"type": "test"}
        self.ar_mobile.create_ar_overlay(session_id, overlay_data)
        
        overlay_id = list(self.ar_mobile.overlay_layers.keys())[0]
        initial_visibility = self.ar_mobile.overlay_visibility[overlay_id]
        
        success = self.ar_mobile.toggle_ar_overlay_visibility(overlay_id)
        
        self.assertTrue(success)
        self.assertNotEqual(self.ar_mobile.overlay_visibility[overlay_id], initial_visibility)
    
    # Mobile BIM Viewer Tests
    
    def test_create_bim_viewer(self):
        """Test creating mobile BIM viewer"""
        building_id = "test_building"
        user_id = "test_user"
        
        viewer_id = self.ar_mobile.create_bim_viewer(building_id, user_id)
        
        self.assertIsInstance(viewer_id, str)
        self.assertIn(viewer_id, self.ar_mobile.bim_viewers)
        
        viewer = self.ar_mobile.bim_viewers[viewer_id]
        self.assertEqual(viewer.building_id, building_id)
        self.assertEqual(viewer.current_view, '2d')
        self.assertIn('walls', viewer.visible_layers)
    
    def test_update_bim_viewer(self):
        """Test updating BIM viewer"""
        building_id = "test_building"
        user_id = "test_user"
        
        viewer_id = self.ar_mobile.create_bim_viewer(building_id, user_id)
        
        updates = {
            'current_view': '3d',
            'visible_layers': ['walls', 'doors'],
            'overlay_visible': False
        }
        
        success = self.ar_mobile.update_bim_viewer(viewer_id, updates)
        
        self.assertTrue(success)
        
        viewer = self.ar_mobile.bim_viewers[viewer_id]
        self.assertEqual(viewer.current_view, '3d')
        self.assertEqual(viewer.visible_layers, ['walls', 'doors'])
        self.assertFalse(viewer.overlay_visible)
    
    def test_get_bim_viewer_state(self):
        """Test getting BIM viewer state"""
        building_id = "test_building"
        user_id = "test_user"
        
        viewer_id = self.ar_mobile.create_bim_viewer(building_id, user_id)
        
        viewer_state = self.ar_mobile.get_bim_viewer_state(viewer_id)
        
        self.assertIsNotNone(viewer_state)
        self.assertEqual(viewer_state.viewer_id, viewer_id)
        self.assertEqual(viewer_state.building_id, building_id)
    
    # Integration Tests
    
    def test_full_ar_workflow(self):
        """Test complete AR workflow"""
        # 1. Create AR session
        session_id = self.ar_mobile.create_ar_session("test_building", "test_user")
        
        # 2. Sync AR coordinates
        success = self.ar_mobile.sync_ar_coordinates(session_id, self.sample_coordinates, 'arkit')
        self.assertTrue(success)
        
        # 3. Calibrate UWB beacons
        beacon_id = "test_beacon"
        position = ARCoordinate(0.0, 0.0, 0.0, 0.9, datetime.now(), 'uwb')
        success = self.ar_mobile.calibrate_uwb_beacon(beacon_id, position, 10.0, 0.1)
        self.assertTrue(success)
        
        # 4. Get precise position
        precise_position = self.ar_mobile.get_precise_position([beacon_id])
        self.assertIsNotNone(precise_position)
        
        # 5. Create AR overlay
        overlay_data = {"type": "building_systems"}
        success = self.ar_mobile.create_ar_overlay(session_id, overlay_data)
        self.assertTrue(success)
        
        # 6. Create BIM viewer
        viewer_id = self.ar_mobile.create_bim_viewer("test_building", "test_user")
        self.assertIsInstance(viewer_id, str)
        
        # 7. Convert LiDAR to SVG
        svg_output = self.ar_mobile.convert_lidar_to_svg(self.sample_lidar_points)
        self.assertIn('<svg', svg_output)
    
    def test_offline_mobile_workflow(self):
        """Test offline mobile workflow"""
        # 1. Sync offline data
        user_id = "test_user"
        building_id = "test_building"
        offline_data = {"building_info": {"name": "Test Building"}}
        
        success = self.ar_mobile.sync_offline_data(user_id, building_id, offline_data)
        self.assertTrue(success)
        
        # 2. Check offline capability
        capability = self.ar_mobile.check_offline_capability(user_id)
        self.assertTrue(capability['can_work_offline'])
        
        # 3. Get offline data
        retrieved_data = self.ar_mobile.get_offline_data(user_id)
        self.assertEqual(retrieved_data, offline_data)
        
        # 4. Create BIM viewer for offline use
        viewer_id = self.ar_mobile.create_bim_viewer(building_id, user_id)
        self.assertIsInstance(viewer_id, str)
    
    def test_error_handling(self):
        """Test error handling in various scenarios"""
        # Test with non-existent session
        success = self.ar_mobile.sync_ar_coordinates("non_existent", self.sample_coordinates)
        self.assertFalse(success)
        
        # Test with non-existent overlay
        success = self.ar_mobile.update_ar_overlay("non_existent", {})
        self.assertFalse(success)
        
        # Test with non-existent viewer
        success = self.ar_mobile.update_bim_viewer("non_existent", {})
        self.assertFalse(success)
    
    def test_cleanup(self):
        """Test service cleanup"""
        # Create some data
        session_id = self.ar_mobile.create_ar_session("test_building", "test_user")
        viewer_id = self.ar_mobile.create_bim_viewer("test_building", "test_user")
        
        # Verify data exists
        self.assertIn(session_id, self.ar_mobile.ar_sessions)
        self.assertIn(viewer_id, self.ar_mobile.bim_viewers)
        
        # Cleanup
        self.ar_mobile.cleanup()
        
        # Verify cleanup doesn't raise errors
        self.assertTrue(True)
    
    def test_get_statistics(self):
        """Test statistics retrieval"""
        # Create some test data
        session_id = self.ar_mobile.create_ar_session("test_building", "test_user")
        viewer_id = self.ar_mobile.create_bim_viewer("test_building", "test_user")
        self.ar_mobile.sync_offline_data("test_user", "test_building", {"test": "data"})
        
        stats = self.ar_mobile.get_statistics()
        
        self.assertIsInstance(stats, dict)
        self.assertIn('active_ar_sessions', stats)
        self.assertIn('uwb_beacons', stats)
        self.assertIn('offline_users', stats)
        self.assertIn('lidar_conversions', stats)
        self.assertIn('ar_overlays', stats)
        self.assertIn('bim_viewers', stats)
        self.assertIn('coordinate_cache_size', stats)
        self.assertIn('viewer_cache_size', stats)
        
        self.assertIsInstance(stats['active_ar_sessions'], int)
        self.assertIsInstance(stats['bim_viewers'], int)


if __name__ == '__main__':
    unittest.main() 