"""
Comprehensive AR & Mobile Integration Demo

Demonstrates all features of the AR & Mobile Integration service:
- ARKit/ARCore coordinate synchronization
- UWB/BLE calibration for precise positioning
- Offline-first mobile app for field work
- LiDAR + photo input → SVG conversion
- Real-time AR overlay for building systems
- Mobile BIM viewer with AR capabilities
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.ar_mobile_integration import ARMobileIntegration, ARCoordinate, LiDARPoint

def print_section(title):
    print(f"\n{'='*50}")
    print(f" {title}")
    print(f"{'='*50}")

def print_coordinate(coord):
    print(f"  Position: ({coord.x:.2f}, {coord.y:.2f}, {coord.z:.2f})")
    print(f"  Confidence: {coord.confidence:.2f}")
    print(f"  Source: {coord.source}")
    print(f"  Timestamp: {coord.timestamp}")

def print_beacon(beacon):
    print(f"  Beacon ID: {beacon.beacon_id}")
    print(f"  Position: ({beacon.position.x:.2f}, {beacon.position.y:.2f}, {beacon.position.z:.2f})")
    print(f"  Range: {beacon.range:.2f}m")
    print(f"  Accuracy: {beacon.accuracy:.3f}m")
    print(f"  Status: {beacon.status}")

def main():
    print("🎯 Comprehensive AR & Mobile Integration Demo")
    
    # Initialize the service
    ar_mobile = ARMobileIntegration()
    print("✓ Service initialized successfully")
    
    # Sample data for demonstration
    sample_coordinates = [
        ARCoordinate(1.0, 2.0, 3.0, 0.9, None, 'arkit'),
        ARCoordinate(4.0, 5.0, 6.0, 0.8, None, 'arcore'),
        ARCoordinate(7.0, 8.0, 9.0, 0.7, None, 'uwb')
    ]
    
    sample_lidar_points = [
        LiDARPoint(1.0, 2.0, 3.0, 0.5, 0.9, None),
        LiDARPoint(4.0, 5.0, 6.0, 0.6, 0.8, None),
        LiDARPoint(7.0, 8.0, 9.0, 0.7, 0.7, None),
        LiDARPoint(10.0, 11.0, 12.0, 0.8, 0.6, None),
        LiDARPoint(13.0, 14.0, 15.0, 0.9, 0.5, None)
    ]
    
    print(f"\n📊 Created {len(sample_coordinates)} sample coordinates and {len(sample_lidar_points)} LiDAR points")
    
    # 1. AR Coordinate Synchronization Demo
    print_section("AR Coordinate Synchronization")
    
    building_id = "demo_building"
    user_id = "demo_user"
    
    # Create AR session
    print("Creating AR session...")
    session_id = ar_mobile.create_ar_session(building_id, user_id)
    print(f"  ✓ Session created: {session_id}")
    
    # Sync AR coordinates
    print(f"\nSyncing AR coordinates from ARKit...")
    success = ar_mobile.sync_ar_coordinates(session_id, sample_coordinates[:2], 'arkit')
    print(f"  ✓ Sync successful: {success}")
    
    # Sync more coordinates from ARCore
    print(f"\nSyncing AR coordinates from ARCore...")
    success = ar_mobile.sync_ar_coordinates(session_id, sample_coordinates[1:], 'arcore')
    print(f"  ✓ Sync successful: {success}")
    
    # Get session info
    session = ar_mobile.get_ar_session(session_id)
    print(f"\nSession Information:")
    print(f"  Building ID: {session.building_id}")
    print(f"  User ID: {session.user_id}")
    print(f"  Start Time: {session.start_time}")
    print(f"  Last Activity: {session.last_activity}")
    
    # 2. UWB/BLE Calibration Demo
    print_section("UWB/BLE Calibration")
    
    # Calibrate UWB beacons
    uwb_beacons = [
        ("beacon_001", ARCoordinate(0.0, 0.0, 0.0, 0.9, None, 'uwb'), 10.0, 0.1),
        ("beacon_002", ARCoordinate(10.0, 0.0, 0.0, 0.8, None, 'uwb'), 15.0, 0.2),
        ("beacon_003", ARCoordinate(0.0, 10.0, 0.0, 0.7, None, 'uwb'), 12.0, 0.15),
        ("beacon_004", ARCoordinate(5.0, 5.0, 0.0, 0.6, None, 'uwb'), 8.0, 0.25)
    ]
    
    print("Calibrating UWB beacons...")
    for beacon_id, position, range_distance, accuracy in uwb_beacons:
        success = ar_mobile.calibrate_uwb_beacon(beacon_id, position, range_distance, accuracy)
        print(f"  ✓ {beacon_id}: {'Success' if success else 'Failed'}")
    
    # Get precise position using triangulation
    print(f"\nGetting precise position using UWB triangulation...")
    beacon_ids = ["beacon_001", "beacon_002", "beacon_003"]
    precise_position = ar_mobile.get_precise_position(beacon_ids)
    
    if precise_position:
        print("  ✓ Precise position calculated:")
        print_coordinate(precise_position)
    else:
        print("  ❌ Failed to calculate precise position")
    
    # 3. Offline Mobile App Demo
    print_section("Offline Mobile App")
    
    # Sync offline data
    offline_data = {
        "building_info": {
            "name": "Demo Building",
            "address": "123 Demo Street",
            "floors": 3,
            "area": 5000
        },
        "symbols": [
            {"id": "symbol_001", "type": "electrical", "position": [1, 2, 3]},
            {"id": "symbol_002", "type": "plumbing", "position": [4, 5, 6]},
            {"id": "symbol_003", "type": "hvac", "position": [7, 8, 9]}
        ],
        "layers": ["electrical", "plumbing", "hvac", "structural"],
        "last_updated": "2024-12-19T10:00:00Z"
    }
    
    print("Syncing offline data for mobile app...")
    success = ar_mobile.sync_offline_data(user_id, building_id, offline_data)
    print(f"  ✓ Sync successful: {success}")
    
    # Check offline capability
    print(f"\nChecking offline capability...")
    capability = ar_mobile.check_offline_capability(user_id)
    print(f"  Has offline data: {capability['has_offline_data']}")
    print(f"  Data size: {capability['data_size']} bytes")
    print(f"  Sync status: {capability['sync_status']}")
    print(f"  Can work offline: {capability['can_work_offline']}")
    print(f"  Estimated duration: {capability['estimated_duration']} hours")
    
    # Get offline data
    print(f"\nRetrieving offline data...")
    retrieved_data = ar_mobile.get_offline_data(user_id)
    print(f"  ✓ Retrieved {len(retrieved_data)} data items")
    print(f"  Building name: {retrieved_data.get('building_info', {}).get('name', 'Unknown')}")
    print(f"  Symbol count: {len(retrieved_data.get('symbols', []))}")
    
    # 4. LiDAR Conversion Demo
    print_section("LiDAR + Photo Input → SVG Conversion")
    
    # Convert LiDAR to SVG
    print("Converting LiDAR point cloud to SVG...")
    svg_output = ar_mobile.convert_lidar_to_svg(sample_lidar_points)
    print(f"  ✓ Conversion successful")
    print(f"  SVG size: {len(svg_output)} characters")
    print(f"  Point count: {len(sample_lidar_points)}")
    
    # Show SVG preview
    print(f"\nSVG Preview (first 200 chars):")
    print(f"  {svg_output[:200]}...")
    
    # Process photo input
    print(f"\nProcessing photo input...")
    photo_data = b"fake_photo_data_for_demo"
    metadata = {
        "width": 1920,
        "height": 1080,
        "format": "jpeg",
        "size": len(photo_data),
        "timestamp": "2024-12-19T10:00:00Z"
    }
    
    photo_svg = ar_mobile.process_photo_input(photo_data, metadata)
    print(f"  ✓ Photo processing successful")
    print(f"  Photo size: {len(photo_data)} bytes")
    print(f"  Generated SVG size: {len(photo_svg)} characters")
    
    # 5. AR Overlay Demo
    print_section("Real-time AR Overlay")
    
    # Create AR overlay
    overlay_data = {
        "type": "building_systems",
        "layers": {
            "electrical": {
                "visible": True,
                "color": "#FF0000",
                "opacity": 0.8
            },
            "plumbing": {
                "visible": True,
                "color": "#0000FF",
                "opacity": 0.7
            },
            "hvac": {
                "visible": False,
                "color": "#00FF00",
                "opacity": 0.6
            }
        },
        "annotations": [
            {"id": "ann_001", "text": "Main Electrical Panel", "position": [1, 2, 3]},
            {"id": "ann_002", "text": "Water Main", "position": [4, 5, 6]}
        ]
    }
    
    print("Creating AR overlay for building systems...")
    success = ar_mobile.create_ar_overlay(session_id, overlay_data)
    print(f"  ✓ Overlay created: {success}")
    
    # Update overlay
    print(f"\nUpdating AR overlay...")
    overlay_id = list(ar_mobile.overlay_layers.keys())[0]
    update_data = {
        "layers": {
            "hvac": {
                "visible": True,
                "color": "#00FF00",
                "opacity": 0.8
            }
        },
        "annotations": [
            {"id": "ann_003", "text": "HVAC Unit", "position": [7, 8, 9]}
        ]
    }
    
    success = ar_mobile.update_ar_overlay(overlay_id, update_data)
    print(f"  ✓ Overlay updated: {success}")
    
    # Toggle overlay visibility
    print(f"\nToggling overlay visibility...")
    success = ar_mobile.toggle_ar_overlay_visibility(overlay_id)
    print(f"  ✓ Visibility toggled: {success}")
    
    # 6. Mobile BIM Viewer Demo
    print_section("Mobile BIM Viewer with AR Capabilities")
    
    # Create BIM viewer
    print("Creating mobile BIM viewer...")
    viewer_id = ar_mobile.create_bim_viewer(building_id, user_id)
    print(f"  ✓ Viewer created: {viewer_id}")
    
    # Get initial viewer state
    viewer_state = ar_mobile.get_bim_viewer_state(viewer_id)
    print(f"\nInitial Viewer State:")
    print(f"  Building ID: {viewer_state.building_id}")
    print(f"  Current View: {viewer_state.current_view}")
    print(f"  Visible Layers: {viewer_state.visible_layers}")
    print(f"  Overlay Visible: {viewer_state.overlay_visible}")
    
    # Update viewer state
    print(f"\nUpdating BIM viewer...")
    updates = {
        'current_view': '3d',
        'visible_layers': ['walls', 'doors', 'windows', 'electrical'],
        'overlay_visible': True
    }
    
    success = ar_mobile.update_bim_viewer(viewer_id, updates)
    print(f"  ✓ Viewer updated: {success}")
    
    # Get updated state
    updated_state = ar_mobile.get_bim_viewer_state(viewer_id)
    print(f"\nUpdated Viewer State:")
    print(f"  Current View: {updated_state.current_view}")
    print(f"  Visible Layers: {updated_state.visible_layers}")
    print(f"  Overlay Visible: {updated_state.overlay_visible}")
    
    # 7. Integration Demo
    print_section("Integration Example")
    
    print("Complete AR & Mobile workflow:")
    
    # Step 1: AR Session + Coordinate Sync
    print(f"\nStep 1 - AR Session & Coordinate Sync")
    print(f"  Session ID: {session_id}")
    print(f"  Coordinates synced: {len(ar_mobile.coordinate_cache)}")
    
    # Step 2: UWB Calibration + Precise Positioning
    print(f"\nStep 2 - UWB Calibration & Precise Positioning")
    print(f"  UWB beacons calibrated: {len(ar_mobile.uwb_beacons)}")
    if precise_position:
        print(f"  Precise position accuracy: {precise_position.confidence:.3f}")
    
    # Step 3: Offline Data Sync
    print(f"\nStep 3 - Offline Data Sync")
    print(f"  Offline users: {len(ar_mobile.offline_data)}")
    print(f"  Data available: {capability['has_offline_data']}")
    
    # Step 4: LiDAR Conversion
    print(f"\nStep 4 - LiDAR Conversion")
    print(f"  LiDAR conversions: {len(ar_mobile.conversion_cache)}")
    print(f"  SVG generated: {len(svg_output)} characters")
    
    # Step 5: AR Overlay
    print(f"\nStep 5 - AR Overlay")
    print(f"  AR overlays: {len(ar_mobile.overlay_layers)}")
    print(f"  Overlay visibility: {ar_mobile.overlay_visibility.get(overlay_id, False)}")
    
    # Step 6: BIM Viewer
    print(f"\nStep 6 - BIM Viewer")
    print(f"  BIM viewers: {len(ar_mobile.bim_viewers)}")
    print(f"  Viewer state: {updated_state.current_view} view")
    
    # 8. Performance Demo
    print_section("Performance Metrics")
    
    stats = ar_mobile.get_statistics()
    print("Service Statistics:")
    print(f"  Active AR Sessions: {stats['active_ar_sessions']}")
    print(f"  UWB Beacons: {stats['uwb_beacons']}")
    print(f"  Offline Users: {stats['offline_users']}")
    print(f"  LiDAR Conversions: {stats['lidar_conversions']}")
    print(f"  AR Overlays: {stats['ar_overlays']}")
    print(f"  BIM Viewers: {stats['bim_viewers']}")
    print(f"  Coordinate Cache Size: {stats['coordinate_cache_size']}")
    print(f"  Viewer Cache Size: {stats['viewer_cache_size']}")
    
    # Configuration
    print(f"\nConfiguration:")
    print(f"  AR Positioning Accuracy: {ar_mobile.get_ar_positioning_accuracy()}m")
    print(f"  UWB Range Limit: {ar_mobile.get_uwb_range_limit()}m")
    print(f"  Offline Data Retention: {ar_mobile.get_offline_data_retention()} hours")
    print(f"  LiDAR Conversion Accuracy: {ar_mobile.get_lidar_conversion_accuracy()}")
    
    print("\n🎉 AR & Mobile Integration Demo Completed!")
    print("="*50)
    print("\nKey Features Demonstrated:")
    print("  ✓ ARKit/ARCore coordinate synchronization")
    print("  ✓ UWB/BLE calibration for precise positioning")
    print("  ✓ Offline-first mobile app capabilities")
    print("  ✓ LiDAR + photo input → SVG conversion")
    print("  ✓ Real-time AR overlay for building systems")
    print("  ✓ Mobile BIM viewer with AR capabilities")
    print("  ✓ Complete integration workflow")

if __name__ == '__main__':
    main() 