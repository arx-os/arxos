"""
AR & Mobile Integration Service

Implements augmented reality and mobile capabilities for on-site building management:
- ARKit/ARCore coordinate synchronization
- UWB/BLE calibration for precise positioning
- Offline-first mobile app for field work
- LiDAR + photo input → SVG conversion
- Real-time AR overlay for building systems
- Mobile BIM viewer with AR capabilities
"""

import logging
import json
import time
import uuid
import threading
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
import sqlite3
import asyncio
from concurrent.futures import ThreadPoolExecutor
import numpy as np
from collections import defaultdict, deque
import pickle
import zlib
import base64

logger = logging.getLogger(__name__)


@dataclass
class ARCoordinate:
    """Represents a coordinate in AR space"""
    x: float
    y: float
    z: float
    confidence: float
    timestamp: datetime
    source: str  # 'arkit', 'arcore', 'uwb', 'ble'


@dataclass
class ARAnchor:
    """Represents an AR anchor point"""
    anchor_id: str
    position: ARCoordinate
    orientation: Tuple[float, float, float, float]  # quaternion
    scale: Tuple[float, float, float]
    tracking_state: str  # 'tracking', 'limited', 'not_tracking'
    metadata: Dict[str, Any]


@dataclass
class UWBBeacon:
    """Represents a UWB beacon for precise positioning"""
    beacon_id: str
    position: ARCoordinate
    range: float
    accuracy: float
    last_seen: datetime
    status: str  # 'active', 'inactive', 'error'


@dataclass
class LiDARPoint:
    """Represents a LiDAR point cloud data point"""
    x: float
    y: float
    z: float
    intensity: float
    confidence: float
    timestamp: datetime


@dataclass
class ARSession:
    """Represents an AR session for building management"""
    session_id: str
    building_id: str
    user_id: str
    anchors: List[ARAnchor]
    beacons: List[UWBBeacon]
    point_cloud: List[LiDARPoint]
    overlay_data: Dict[str, Any]
    session_data: Dict[str, Any]
    start_time: datetime
    last_activity: datetime


@dataclass
class MobileAppState:
    """Represents the state of the mobile app"""
    app_version: str
    user_id: str
    building_id: str
    offline_data: Dict[str, Any]
    sync_status: str  # 'synced', 'pending', 'conflict'
    last_sync: datetime
    battery_level: float
    network_status: str  # 'online', 'offline', 'limited'


@dataclass
class BIMViewerState:
    """Represents the state of the mobile BIM viewer"""
    viewer_id: str
    building_id: str
    current_view: str  # '2d', '3d', 'ar'
    visible_layers: List[str]
    camera_position: ARCoordinate
    camera_orientation: Tuple[float, float, float, float]
    selected_objects: List[str]
    overlay_visible: bool


class ARMobileIntegration:
    """AR & Mobile Integration implementation"""
    
    def __init__(self, options: Optional[Dict[str, Any]] = None):
        self.options = {
            'enable_ar_sync': True,
            'enable_uwb_calibration': True,
            'enable_offline_mode': True,
            'enable_lidar_conversion': True,
            'enable_ar_overlay': True,
            'enable_mobile_bim': True,
            'ar_positioning_accuracy': 0.05,  # 5cm
            'uwb_range_limit': 50.0,  # meters
            'offline_data_retention': 24,  # hours
            'lidar_conversion_accuracy': 0.95,
            'mobile_app_timeout': 300,  # 5 minutes
            'bim_viewer_cache_size': 1000,
            **(options or {})
        }
        
        # Initialize databases
        self._init_databases()
        
        # AR coordinate synchronization
        self.ar_sessions = {}  # session_id -> ARSession
        self.coordinate_cache = {}  # coordinate_id -> ARCoordinate
        self.anchor_registry = {}  # anchor_id -> ARAnchor
        
        # UWB/BLE calibration
        self.uwb_beacons = {}  # beacon_id -> UWBBeacon
        self.ble_devices = {}  # device_id -> device_info
        self.calibration_data = {}  # calibration_id -> calibration_info
        
        # Offline mobile app
        self.offline_data = {}  # user_id -> offline_data
        self.sync_queue = deque()
        self.sync_status = {}  # user_id -> sync_status
        
        # LiDAR conversion
        self.lidar_processors = {}  # processor_id -> processor_info
        self.conversion_cache = {}  # conversion_id -> conversion_result
        
        # AR overlay
        self.overlay_layers = {}  # layer_id -> overlay_data
        self.overlay_visibility = {}  # layer_id -> visibility_state
        
        # Mobile BIM viewer
        self.bim_viewers = {}  # viewer_id -> BIMViewerState
        self.viewer_cache = {}  # cache_id -> cached_data
        
        # Thread pool for async operations
        self.executor = ThreadPoolExecutor(max_workers=4)
        
        # Background tasks
        self.sync_task = None
        self.calibration_task = None
        
        logger.info('AR & Mobile Integration initialized')
    
    def _init_databases(self):
        """Initialize SQLite databases for persistent storage"""
        self.db_path = Path("data/ar_mobile.db")
        self.db_path.parent.mkdir(exist_ok=True)
        
        # Create tables
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS ar_sessions (
                    session_id TEXT PRIMARY KEY,
                    building_id TEXT,
                    user_id TEXT,
                    session_data TEXT,
                    start_time TEXT,
                    last_activity TEXT
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS ar_anchors (
                    anchor_id TEXT PRIMARY KEY,
                    session_id TEXT,
                    position_x REAL,
                    position_y REAL,
                    position_z REAL,
                    orientation_w REAL,
                    orientation_x REAL,
                    orientation_y REAL,
                    orientation_z REAL,
                    scale_x REAL,
                    scale_y REAL,
                    scale_z REAL,
                    tracking_state TEXT,
                    metadata TEXT,
                    timestamp TEXT
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS uwb_beacons (
                    beacon_id TEXT PRIMARY KEY,
                    position_x REAL,
                    position_y REAL,
                    position_z REAL,
                    range REAL,
                    accuracy REAL,
                    last_seen TEXT,
                    status TEXT
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS mobile_app_states (
                    user_id TEXT PRIMARY KEY,
                    app_version TEXT,
                    building_id TEXT,
                    offline_data TEXT,
                    sync_status TEXT,
                    last_sync TEXT,
                    battery_level REAL,
                    network_status TEXT
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS lidar_conversions (
                    conversion_id TEXT PRIMARY KEY,
                    point_cloud_data TEXT,
                    svg_output TEXT,
                    accuracy REAL,
                    processing_time REAL,
                    timestamp TEXT
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS bim_viewer_states (
                    viewer_id TEXT PRIMARY KEY,
                    building_id TEXT,
                    current_view TEXT,
                    visible_layers TEXT,
                    camera_position TEXT,
                    camera_orientation TEXT,
                    selected_objects TEXT,
                    overlay_visible BOOLEAN,
                    timestamp TEXT
                )
            """)
            
            conn.commit()
    
    # AR Coordinate Synchronization Methods
    
    def sync_ar_coordinates(self, session_id: str, coordinates: List[ARCoordinate], 
                           platform: str = 'arkit') -> bool:
        """Synchronize AR coordinates from ARKit/ARCore"""
        try:
            if session_id not in self.ar_sessions:
                return False
            
            session = self.ar_sessions[session_id]
            
            # Process and validate coordinates
            for coord in coordinates:
                coord.source = platform
                coord.timestamp = datetime.now()
                
                # Store in coordinate cache
                coord_id = f"{session_id}_{coord.x}_{coord.y}_{coord.z}"
                self.coordinate_cache[coord_id] = coord
                
                # Update session
                session.last_activity = datetime.now()
            
            # Store in database
            with sqlite3.connect(self.db_path) as conn:
                for coord in coordinates:
                    conn.execute("""
                        INSERT OR REPLACE INTO ar_anchors
                        (anchor_id, session_id, position_x, position_y, position_z,
                         orientation_w, orientation_x, orientation_y, orientation_z,
                         scale_x, scale_y, scale_z, tracking_state, metadata, timestamp)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        f"coord_{coord.x}_{coord.y}_{coord.z}",
                        session_id, coord.x, coord.y, coord.z,
                        1.0, 0.0, 0.0, 0.0,  # Default orientation
                        1.0, 1.0, 1.0,  # Default scale
                        'tracking', json.dumps({'source': platform}), coord.timestamp.isoformat()
                    ))
                conn.commit()
            
            logger.info(f'Synced {len(coordinates)} coordinates for session {session_id}')
            return True
            
        except Exception as e:
            logger.error(f'Failed to sync AR coordinates: {e}')
            return False
    
    def get_ar_session(self, session_id: str) -> Optional[ARSession]:
        """Get AR session by ID"""
        return self.ar_sessions.get(session_id)
    
    def create_ar_session(self, building_id: str, user_id: str) -> str:
        """Create a new AR session"""
        try:
            session_id = str(uuid.uuid4())
            
            session = ARSession(
                session_id=session_id,
                building_id=building_id,
                user_id=user_id,
                anchors=[],
                beacons=[],
                point_cloud=[],
                overlay_data={},
                session_data={},
                start_time=datetime.now(),
                last_activity=datetime.now()
            )
            
            self.ar_sessions[session_id] = session
            
            # Store in database
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO ar_sessions
                    (session_id, building_id, user_id, session_data, start_time, last_activity)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    session_id, building_id, user_id,
                    json.dumps({}), session.start_time.isoformat(),
                    session.last_activity.isoformat()
                ))
                conn.commit()
            
            logger.info(f'Created AR session {session_id} for building {building_id}')
            return session_id
            
        except Exception as e:
            logger.error(f'Failed to create AR session: {e}')
            raise
    
    # UWB/BLE Calibration Methods
    
    def calibrate_uwb_beacon(self, beacon_id: str, position: ARCoordinate, 
                            range: float, accuracy: float) -> bool:
        """Calibrate a UWB beacon for precise positioning"""
        try:
            beacon = UWBBeacon(
                beacon_id=beacon_id,
                position=position,
                range=range,
                accuracy=accuracy,
                last_seen=datetime.now(),
                status='active'
            )
            
            self.uwb_beacons[beacon_id] = beacon
            
            # Store in database
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO uwb_beacons
                    (beacon_id, position_x, position_y, position_z, range, accuracy, last_seen, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    beacon_id, position.x, position.y, position.z,
                    range, accuracy, beacon.last_seen.isoformat(), beacon.status
                ))
                conn.commit()
            
            logger.info(f'Calibrated UWB beacon {beacon_id}')
            return True
            
        except Exception as e:
            logger.error(f'Failed to calibrate UWB beacon: {e}')
            return False
    
    def get_precise_position(self, beacon_ids: List[str]) -> Optional[ARCoordinate]:
        """Get precise position using UWB beacons"""
        try:
            if not beacon_ids:
                return None
            
            # Calculate position using triangulation
            positions = []
            weights = []
            
            for beacon_id in beacon_ids:
                beacon = self.uwb_beacons.get(beacon_id)
                if beacon and beacon.status == 'active':
                    positions.append(beacon.position)
                    weights.append(1.0 / beacon.accuracy)
            
            if not positions:
                return None
            
            # Weighted average of positions
            total_weight = sum(weights)
            if total_weight == 0:
                return None
            
            avg_x = sum(p.x * w for p, w in zip(positions, weights)) / total_weight
            avg_y = sum(p.y * w for p, w in zip(positions, weights)) / total_weight
            avg_z = sum(p.z * w for p, w in zip(positions, weights)) / total_weight
            
            # Calculate confidence based on beacon accuracy
            avg_accuracy = sum(weights) / len(weights)
            
            return ARCoordinate(
                x=avg_x, y=avg_y, z=avg_z,
                confidence=avg_accuracy,
                timestamp=datetime.now(),
                source='uwb'
            )
            
        except Exception as e:
            logger.error(f'Failed to get precise position: {e}')
            return None
    
    # Offline Mobile App Methods
    
    def sync_offline_data(self, user_id: str, building_id: str, 
                          offline_data: Dict[str, Any]) -> bool:
        """Sync offline data for mobile app"""
        try:
            # Store offline data
            self.offline_data[user_id] = {
                'building_id': building_id,
                'data': offline_data,
                'timestamp': datetime.now(),
                'version': '1.0'
            }
            
            # Update sync status
            self.sync_status[user_id] = 'synced'
            
            # Store in database
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO mobile_app_states
                    (user_id, app_version, building_id, offline_data, sync_status, 
                     last_sync, battery_level, network_status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    user_id, '1.0', building_id, json.dumps(offline_data),
                    'synced', datetime.now().isoformat(), 100.0, 'offline'
                ))
                conn.commit()
            
            logger.info(f'Synced offline data for user {user_id}')
            return True
            
        except Exception as e:
            logger.error(f'Failed to sync offline data: {e}')
            return False
    
    def get_offline_data(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get offline data for mobile app"""
        return self.offline_data.get(user_id, {}).get('data')
    
    def check_offline_capability(self, user_id: str) -> Dict[str, Any]:
        """Check offline capability and data availability"""
        try:
            offline_data = self.offline_data.get(user_id, {})
            
            return {
                'has_offline_data': bool(offline_data.get('data')),
                'data_size': len(str(offline_data.get('data', {}))),
                'last_sync': offline_data.get('timestamp'),
                'sync_status': self.sync_status.get(user_id, 'unknown'),
                'can_work_offline': bool(offline_data.get('data')),
                'estimated_duration': self.options['offline_data_retention']
            }
            
        except Exception as e:
            logger.error(f'Failed to check offline capability: {e}')
            return {'error': str(e)}
    
    # LiDAR Conversion Methods
    
    def convert_lidar_to_svg(self, point_cloud: List[LiDARPoint], 
                            conversion_options: Dict[str, Any] = None) -> str:
        """Convert LiDAR point cloud to SVG"""
        try:
            conversion_id = str(uuid.uuid4())
            start_time = time.time()
            
            # Process point cloud
            if not point_cloud:
                return '<svg></svg>'
            
            # Extract bounding box
            x_coords = [p.x for p in point_cloud]
            y_coords = [p.y for p in point_cloud]
            z_coords = [p.z for p in point_cloud]
            
            min_x, max_x = min(x_coords), max(x_coords)
            min_y, max_y = min(y_coords), max(y_coords)
            min_z, max_z = min(z_coords), max(z_coords)
            
            width = max_x - min_x
            height = max_y - min_y
            
            # Generate SVG
            svg_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" 
     viewBox="{min_x} {min_y} {width} {height}">
  <defs>
    <filter id="point" x="-50%" y="-50%" width="200%" height="200%">
      <feGaussianBlur in="SourceGraphic" stdDeviation="1"/>
    </filter>
  </defs>
  <g id="lidar-points">'''
            
            # Add points to SVG
            for point in point_cloud:
                # Normalize intensity to color
                intensity = min(255, max(0, int(point.intensity * 255)))
                color = f"rgb({intensity},{intensity},{intensity})"
                
                svg_content += f'''
    <circle cx="{point.x}" cy="{point.y}" r="0.5" 
            fill="{color}" opacity="{point.confidence}" filter="url(#point)"/>'''
            
            svg_content += '''
  </g>
</svg>'''
            
            processing_time = time.time() - start_time
            
            # Store conversion result
            conversion_result = {
                'conversion_id': conversion_id,
                'point_count': len(point_cloud),
                'svg_size': len(svg_content),
                'processing_time': processing_time,
                'accuracy': self.options['lidar_conversion_accuracy'],
                'timestamp': datetime.now()
            }
            
            self.conversion_cache[conversion_id] = conversion_result
            
            # Store in database
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO lidar_conversions
                    (conversion_id, point_cloud_data, svg_output, accuracy, processing_time, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    conversion_id, json.dumps([(p.x, p.y, p.z, p.intensity) for p in point_cloud]),
                    svg_content, conversion_result['accuracy'], processing_time,
                    conversion_result['timestamp'].isoformat()
                ))
                conn.commit()
            
            logger.info(f'Converted LiDAR point cloud to SVG: {len(point_cloud)} points')
            return svg_content
            
        except Exception as e:
            logger.error(f'Failed to convert LiDAR to SVG: {e}')
            return '<svg></svg>'
    
    def process_photo_input(self, photo_data: bytes, metadata: Dict[str, Any] = None) -> str:
        """Process photo input and convert to SVG-like representation"""
        try:
            # Simulate photo processing
            # In a real implementation, this would use computer vision
            # to extract building features from the photo
            
            # For demo purposes, create a simple SVG based on metadata
            width = metadata.get('width', 800) if metadata else 800
            height = metadata.get('height', 600) if metadata else 600
            
            svg_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" 
     viewBox="0 0 {width} {height}">
  <rect width="{width}" height="{height}" fill="lightgray"/>
  <text x="{width//2}" y="{height//2}" text-anchor="middle" font-size="24">
    Photo Input Processed
  </text>
  <text x="{width//2}" y="{height//2 + 30}" text-anchor="middle" font-size="16">
    Size: {len(photo_data)} bytes
  </text>
</svg>'''
            
            logger.info(f'Processed photo input: {len(photo_data)} bytes')
            return svg_content
            
        except Exception as e:
            logger.error(f'Failed to process photo input: {e}')
            return '<svg></svg>'
    
    # AR Overlay Methods
    
    def create_ar_overlay(self, session_id: str, overlay_data: Dict[str, Any]) -> bool:
        """Create real-time AR overlay for building systems"""
        try:
            if session_id not in self.ar_sessions:
                return False
            
            session = self.ar_sessions[session_id]
            
            # Process overlay data
            overlay_id = str(uuid.uuid4())
            
            overlay_info = {
                'overlay_id': overlay_id,
                'session_id': session_id,
                'data': overlay_data,
                'timestamp': datetime.now(),
                'visible': True
            }
            
            session.overlay_data[overlay_id] = overlay_info
            self.overlay_layers[overlay_id] = overlay_info
            self.overlay_visibility[overlay_id] = True
            
            session.last_activity = datetime.now()
            
            logger.info(f'Created AR overlay {overlay_id} for session {session_id}')
            return True
            
        except Exception as e:
            logger.error(f'Failed to create AR overlay: {e}')
            return False
    
    def update_ar_overlay(self, overlay_id: str, overlay_data: Dict[str, Any]) -> bool:
        """Update AR overlay with new data"""
        try:
            if overlay_id not in self.overlay_layers:
                return False
            
            overlay_info = self.overlay_layers[overlay_id]
            overlay_info['data'].update(overlay_data)
            overlay_info['timestamp'] = datetime.now()
            
            logger.info(f'Updated AR overlay {overlay_id}')
            return True
            
        except Exception as e:
            logger.error(f'Failed to update AR overlay: {e}')
            return False
    
    def toggle_ar_overlay_visibility(self, overlay_id: str) -> bool:
        """Toggle AR overlay visibility"""
        try:
            if overlay_id in self.overlay_visibility:
                self.overlay_visibility[overlay_id] = not self.overlay_visibility[overlay_id]
                logger.info(f'Toggled AR overlay {overlay_id} visibility')
                return True
            return False
            
        except Exception as e:
            logger.error(f'Failed to toggle AR overlay visibility: {e}')
            return False
    
    # Mobile BIM Viewer Methods
    
    def create_bim_viewer(self, building_id: str, user_id: str) -> str:
        """Create mobile BIM viewer with AR capabilities"""
        try:
            viewer_id = str(uuid.uuid4())
            
            viewer_state = BIMViewerState(
                viewer_id=viewer_id,
                building_id=building_id,
                current_view='2d',
                visible_layers=['walls', 'doors', 'windows'],
                camera_position=ARCoordinate(0, 0, 0, 1.0, datetime.now(), 'viewer'),
                camera_orientation=(1.0, 0.0, 0.0, 0.0),
                selected_objects=[],
                overlay_visible=True
            )
            
            self.bim_viewers[viewer_id] = viewer_state
            
            # Store in database
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO bim_viewer_states
                    (viewer_id, building_id, current_view, visible_layers, camera_position,
                     camera_orientation, selected_objects, overlay_visible, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    viewer_id, building_id, viewer_state.current_view,
                    json.dumps(viewer_state.visible_layers),
                    json.dumps([viewer_state.camera_position.x, viewer_state.camera_position.y, viewer_state.camera_position.z]),
                    json.dumps(viewer_state.camera_orientation),
                    json.dumps(viewer_state.selected_objects),
                    viewer_state.overlay_visible,
                    datetime.now().isoformat()
                ))
                conn.commit()
            
            logger.info(f'Created BIM viewer {viewer_id} for building {building_id}')
            return viewer_id
            
        except Exception as e:
            logger.error(f'Failed to create BIM viewer: {e}')
            raise
    
    def update_bim_viewer(self, viewer_id: str, updates: Dict[str, Any]) -> bool:
        """Update BIM viewer state"""
        try:
            if viewer_id not in self.bim_viewers:
                return False
            
            viewer = self.bim_viewers[viewer_id]
            
            # Apply updates
            for key, value in updates.items():
                if hasattr(viewer, key):
                    setattr(viewer, key, value)
            
            # Store in database
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    UPDATE bim_viewer_states
                    SET current_view = ?, visible_layers = ?, camera_position = ?,
                        camera_orientation = ?, selected_objects = ?, overlay_visible = ?, timestamp = ?
                    WHERE viewer_id = ?
                """, (
                    viewer.current_view, json.dumps(viewer.visible_layers),
                    json.dumps([viewer.camera_position.x, viewer.camera_position.y, viewer.camera_position.z]),
                    json.dumps(viewer.camera_orientation), json.dumps(viewer.selected_objects),
                    viewer.overlay_visible, datetime.now().isoformat(), viewer_id
                ))
                conn.commit()
            
            logger.info(f'Updated BIM viewer {viewer_id}')
            return True
            
        except Exception as e:
            logger.error(f'Failed to update BIM viewer: {e}')
            return False
    
    def get_bim_viewer_state(self, viewer_id: str) -> Optional[BIMViewerState]:
        """Get BIM viewer state"""
        return self.bim_viewers.get(viewer_id)
    
    # Utility Methods
    
    def get_ar_positioning_accuracy(self) -> float:
        """Get current AR positioning accuracy"""
        return self.options['ar_positioning_accuracy']
    
    def get_uwb_range_limit(self) -> float:
        """Get UWB range limit"""
        return self.options['uwb_range_limit']
    
    def get_offline_data_retention(self) -> int:
        """Get offline data retention period"""
        return self.options['offline_data_retention']
    
    def get_lidar_conversion_accuracy(self) -> float:
        """Get LiDAR conversion accuracy"""
        return self.options['lidar_conversion_accuracy']
    
    def cleanup(self):
        """Cleanup resources"""
        try:
            # Shutdown thread pool
            self.executor.shutdown(wait=True)
            
            logger.info('AR & Mobile Integration cleanup completed')
        except Exception as e:
            logger.error(f'Cleanup error: {e}')
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get service statistics"""
        return {
            'active_ar_sessions': len(self.ar_sessions),
            'uwb_beacons': len(self.uwb_beacons),
            'offline_users': len(self.offline_data),
            'lidar_conversions': len(self.conversion_cache),
            'ar_overlays': len(self.overlay_layers),
            'bim_viewers': len(self.bim_viewers),
            'coordinate_cache_size': len(self.coordinate_cache),
            'viewer_cache_size': len(self.viewer_cache)
        } 