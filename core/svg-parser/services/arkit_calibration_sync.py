"""
ARKit Calibration Sync Service

Provides precise ARKit coordinate system alignment to ensure AR environment on iOS
aligns exactly with real-world coordinate system set in SVG, with minimal user input
and preserved scale accuracy.
"""

import json
import time
import math
import numpy as np
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, asdict
from enum import Enum
import asyncio
import uuid
from datetime import datetime, timedelta
from pathlib import Path
import logging
import threading
from concurrent.futures import ThreadPoolExecutor
import hashlib
import sqlite3
from contextlib import contextmanager

# Initialize logger
logger = logging.getLogger(__name__)


class CalibrationStatus(Enum):
    """Calibration status enumeration."""
    NOT_STARTED = "not_started"
    INITIALIZING = "initializing"
    DETECTING_POINTS = "detecting_points"
    CALCULATING = "calculating"
    VALIDATING = "validating"
    APPLIED = "applied"
    FAILED = "failed"
    RECALIBRATING = "recalibrating"


class CalibrationAccuracy(Enum):
    """Calibration accuracy levels."""
    EXCELLENT = "excellent"  # > 98%
    GOOD = "good"           # 95-98%
    ACCEPTABLE = "acceptable"  # 90-95%
    POOR = "poor"           # < 90%


class ReferencePointType(Enum):
    """Types of reference points for calibration."""
    AUTOMATIC = "automatic"
    MANUAL = "manual"
    FIXTURE = "fixture"
    LANDMARK = "landmark"
    CORNER = "corner"
    CENTER = "center"


@dataclass
class ReferencePoint:
    """Reference point for calibration."""
    point_id: str
    point_type: ReferencePointType
    ar_coordinates: Dict[str, float]  # ARKit coordinates
    real_world_coordinates: Dict[str, float]  # Real-world coordinates
    svg_coordinates: Dict[str, float]  # SVG coordinates
    confidence: float  # Detection confidence (0-1)
    timestamp: datetime
    device_id: str
    session_id: str


@dataclass
class CalibrationData:
    """Calibration data structure."""
    calibration_id: str
    session_id: str
    device_id: str
    svg_file_hash: str
    transform_matrix: Dict[str, List[float]]
    scale_factor: float
    accuracy_score: float
    reference_points: List[ReferencePoint]
    status: CalibrationStatus
    created_at: datetime
    updated_at: datetime
    applied_at: Optional[datetime] = None
    validation_results: Optional[Dict[str, Any]] = None


@dataclass
class CalibrationMetrics:
    """Calibration performance metrics."""
    coordinate_accuracy: float
    scale_accuracy: float
    calibration_time: float
    reference_points_count: int
    confidence_score: float
    cross_device_consistency: float


class ARKitCalibrationService:
    """
    ARKit calibration and coordinate synchronization service.
    
    Provides precise coordinate system alignment between ARKit AR environment
    and real-world coordinate system defined in SVG files.
    """
    
    def __init__(self, db_path: str = "calibration_data.db"):
        self.db_path = db_path
        self.calibration_data = {}
        self.active_sessions = {}
        self.reference_points = []
        self.scale_factors = {}
        self.coordinate_transforms = {}
        self._lock = threading.RLock()
        self._executor = ThreadPoolExecutor(max_workers=4)
        
        # Initialize database
        self._initialize_database()
        
        # Load existing calibrations
        self._load_existing_calibrations()
        
        logger.info("ARKit Calibration Service initialized")
    
    def _initialize_database(self):
        """Initialize SQLite database for calibration data."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS calibrations (
                        calibration_id TEXT PRIMARY KEY,
                        session_id TEXT NOT NULL,
                        device_id TEXT NOT NULL,
                        svg_file_hash TEXT NOT NULL,
                        transform_matrix TEXT NOT NULL,
                        scale_factor REAL NOT NULL,
                        accuracy_score REAL NOT NULL,
                        status TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL,
                        applied_at TEXT,
                        validation_results TEXT
                    )
                """)
                
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS reference_points (
                        point_id TEXT PRIMARY KEY,
                        calibration_id TEXT NOT NULL,
                        point_type TEXT NOT NULL,
                        ar_coordinates TEXT NOT NULL,
                        real_world_coordinates TEXT NOT NULL,
                        svg_coordinates TEXT NOT NULL,
                        confidence REAL NOT NULL,
                        timestamp TEXT NOT NULL,
                        device_id TEXT NOT NULL,
                        session_id TEXT NOT NULL,
                        FOREIGN KEY (calibration_id) REFERENCES calibrations (calibration_id)
                    )
                """)
                
                conn.commit()
            logger.info("Calibration database initialized")
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
    
    def _load_existing_calibrations(self):
        """Load existing calibrations from database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT calibration_id, session_id, device_id, svg_file_hash,
                           transform_matrix, scale_factor, accuracy_score, status,
                           created_at, updated_at, applied_at, validation_results
                    FROM calibrations
                """)
                
                for row in cursor.fetchall():
                    calibration_data = CalibrationData(
                        calibration_id=row[0],
                        session_id=row[1],
                        device_id=row[2],
                        svg_file_hash=row[3],
                        transform_matrix=json.loads(row[4]),
                        scale_factor=row[5],
                        accuracy_score=row[6],
                        reference_points=[],  # Load separately
                        status=CalibrationStatus(row[7]),
                        created_at=datetime.fromisoformat(row[8]),
                        updated_at=datetime.fromisoformat(row[9]),
                        applied_at=datetime.fromisoformat(row[10]) if row[10] else None,
                        validation_results=json.loads(row[11]) if row[11] else None
                    )
                    
                    # Load reference points
                    cursor_points = conn.execute("""
                        SELECT point_id, point_type, ar_coordinates, real_world_coordinates,
                               svg_coordinates, confidence, timestamp, device_id, session_id
                        FROM reference_points
                        WHERE calibration_id = ?
                    """, (row[0],))
                    
                    for point_row in cursor_points.fetchall():
                        reference_point = ReferencePoint(
                            point_id=point_row[0],
                            point_type=ReferencePointType(point_row[1]),
                            ar_coordinates=json.loads(point_row[2]),
                            real_world_coordinates=json.loads(point_row[3]),
                            svg_coordinates=json.loads(point_row[4]),
                            confidence=point_row[5],
                            timestamp=datetime.fromisoformat(point_row[6]),
                            device_id=point_row[7],
                            session_id=point_row[8]
                        )
                        calibration_data.reference_points.append(reference_point)
                    
                    self.calibration_data[row[0]] = calibration_data
                    
            logger.info(f"Loaded {len(self.calibration_data)} existing calibrations")
        except Exception as e:
            logger.error(f"Failed to load existing calibrations: {e}")
    
    def initialize_calibration(self, svg_data: Dict, device_info: Dict) -> Dict[str, Any]:
        """
        Initialize calibration process with SVG data and device information.
        
        Args:
            svg_data: SVG file data and coordinate information
            device_info: Device information (ID, capabilities, sensors)
            
        Returns:
            Calibration initialization result
        """
        try:
            with self._lock:
                session_id = str(uuid.uuid4())
                device_id = device_info.get("device_id", "unknown")
                
                # Calculate SVG file hash
                svg_content = json.dumps(svg_data, sort_keys=True)
                svg_file_hash = hashlib.sha256(svg_content.encode()).hexdigest()
                
                # Check for existing calibration
                existing_calibration = self._find_existing_calibration(device_id, svg_file_hash)
                if existing_calibration:
                    logger.info(f"Found existing calibration: {existing_calibration.calibration_id}")
                    return {
                        "status": "existing_found",
                        "calibration_id": existing_calibration.calibration_id,
                        "session_id": session_id,
                        "accuracy_score": existing_calibration.accuracy_score,
                        "can_reuse": existing_calibration.accuracy_score > 0.95
                    }
                
                # Create new calibration session
                calibration_id = str(uuid.uuid4())
                calibration_data = CalibrationData(
                    calibration_id=calibration_id,
                    session_id=session_id,
                    device_id=device_id,
                    svg_file_hash=svg_file_hash,
                    transform_matrix={},
                    scale_factor=1.0,
                    accuracy_score=0.0,
                    reference_points=[],
                    status=CalibrationStatus.INITIALIZING,
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )
                
                # Store calibration data
                self.calibration_data[calibration_id] = calibration_data
                self.active_sessions[session_id] = calibration_id
                
                # Save to database
                self._save_calibration_to_db(calibration_data)
                
                logger.info(f"Initialized calibration session: {calibration_id}")
                
                return {
                    "status": "initialized",
                    "calibration_id": calibration_id,
                    "session_id": session_id,
                    "device_id": device_id,
                    "svg_file_hash": svg_file_hash
                }
                
        except Exception as e:
            logger.error(f"Calibration initialization failed: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    def detect_reference_points(self, ar_frame_data: Dict, session_id: str) -> Dict[str, Any]:
        """
        Detect reference points in AR frame for calibration.
        
        Args:
            ar_frame_data: ARKit frame data with camera and tracking information
            session_id: Active calibration session ID
            
        Returns:
            Reference point detection results
        """
        try:
            with self._lock:
                if session_id not in self.active_sessions:
                    return {"status": "error", "error": "Invalid session ID"}
                
                calibration_id = self.active_sessions[session_id]
                calibration_data = self.calibration_data[calibration_id]
                
                # Update status
                calibration_data.status = CalibrationStatus.DETECTING_POINTS
                calibration_data.updated_at = datetime.now()
                
                # Extract AR frame information
                camera_transform = ar_frame_data.get("camera_transform", {})
                point_cloud = ar_frame_data.get("point_cloud", [])
                plane_anchors = ar_frame_data.get("plane_anchors", [])
                
                # Detect reference points using multiple strategies
                detected_points = []
                
                # Strategy 1: Automatic corner detection
                corner_points = self._detect_corners(point_cloud, plane_anchors)
                detected_points.extend(corner_points)
                
                # Strategy 2: Plane intersection detection
                intersection_points = self._detect_plane_intersections(plane_anchors)
                detected_points.extend(intersection_points)
                
                # Strategy 3: Feature point detection
                feature_points = self._detect_feature_points(point_cloud)
                detected_points.extend(feature_points)
                
                # Filter and rank points by confidence
                filtered_points = self._filter_reference_points(detected_points)
                
                # Convert to ReferencePoint objects
                reference_points = []
                for i, point in enumerate(filtered_points[:10]):  # Limit to top 10
                    reference_point = ReferencePoint(
                        point_id=f"ref_{calibration_id}_{i}",
                        point_type=point["type"],
                        ar_coordinates=point["ar_coordinates"],
                        real_world_coordinates=point["real_world_coordinates"],
                        svg_coordinates=point["svg_coordinates"],
                        confidence=point["confidence"],
                        timestamp=datetime.now(),
                        device_id=calibration_data.device_id,
                        session_id=session_id
                    )
                    reference_points.append(reference_point)
                
                # Update calibration data
                calibration_data.reference_points.extend(reference_points)
                self._save_calibration_to_db(calibration_data)
                
                logger.info(f"Detected {len(reference_points)} reference points")
                
                return {
                    "status": "success",
                    "reference_points_count": len(reference_points),
                    "points": [asdict(point) for point in reference_points],
                    "confidence_avg": np.mean([p.confidence for p in reference_points]) if reference_points else 0.0
                }
                
        except Exception as e:
            logger.error(f"Reference point detection failed: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    def calculate_coordinate_transform(self, session_id: str) -> Dict[str, Any]:
        """
        Calculate coordinate transformation matrix from reference points.
        
        Args:
            session_id: Active calibration session ID
            
        Returns:
            Coordinate transformation results
        """
        try:
            with self._lock:
                if session_id not in self.active_sessions:
                    return {"status": "error", "error": "Invalid session ID"}
                
                calibration_id = self.active_sessions[session_id]
                calibration_data = self.calibration_data[calibration_id]
                
                # Update status
                calibration_data.status = CalibrationStatus.CALCULATING
                calibration_data.updated_at = datetime.now()
                
                if len(calibration_data.reference_points) < 3:
                    return {
                        "status": "error",
                        "error": "Insufficient reference points (minimum 3 required)"
                    }
                
                # Extract coordinate pairs
                ar_coords = []
                real_world_coords = []
                svg_coords = []
                
                for point in calibration_data.reference_points:
                    ar_coords.append([
                        point.ar_coordinates["x"],
                        point.ar_coordinates["y"],
                        point.ar_coordinates["z"]
                    ])
                    real_world_coords.append([
                        point.real_world_coordinates["x"],
                        point.real_world_coordinates["y"],
                        point.real_world_coordinates["z"]
                    ])
                    svg_coords.append([
                        point.svg_coordinates["x"],
                        point.svg_coordinates["y"],
                        point.svg_coordinates["z"]
                    ])
                
                # Calculate transformation matrices
                ar_to_real_transform = self._calculate_transformation_matrix(
                    np.array(ar_coords), np.array(real_world_coords)
                )
                
                real_to_svg_transform = self._calculate_transformation_matrix(
                    np.array(real_world_coords), np.array(svg_coords)
                )
                
                # Calculate scale factor
                scale_factor = self._calculate_scale_factor(ar_coords, real_world_coords)
                
                # Store transformation data
                calibration_data.transform_matrix = {
                    "ar_to_real": ar_to_real_transform.tolist(),
                    "real_to_svg": real_to_svg_transform.tolist(),
                    "combined": (real_to_svg_transform @ ar_to_real_transform).tolist()
                }
                calibration_data.scale_factor = scale_factor
                
                # Calculate initial accuracy score
                accuracy_score = self._calculate_accuracy_score(
                    calibration_data.reference_points,
                    calibration_data.transform_matrix
                )
                calibration_data.accuracy_score = accuracy_score
                
                # Save to database
                self._save_calibration_to_db(calibration_data)
                
                logger.info(f"Calculated transformation matrix with accuracy: {accuracy_score:.3f}")
                
                return {
                    "status": "success",
                    "transform_matrix": calibration_data.transform_matrix,
                    "scale_factor": scale_factor,
                    "accuracy_score": accuracy_score,
                    "reference_points_count": len(calibration_data.reference_points)
                }
                
        except Exception as e:
            logger.error(f"Coordinate transform calculation failed: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    def validate_calibration(self, session_id: str) -> Dict[str, Any]:
        """
        Validate calibration accuracy and quality.
        
        Args:
            session_id: Active calibration session ID
            
        Returns:
            Calibration validation results
        """
        try:
            with self._lock:
                if session_id not in self.active_sessions:
                    return {"status": "error", "error": "Invalid session ID"}
                
                calibration_id = self.active_sessions[session_id]
                calibration_data = self.calibration_data[calibration_id]
                
                # Update status
                calibration_data.status = CalibrationStatus.VALIDATING
                calibration_data.updated_at = datetime.now()
                
                # Perform comprehensive validation
                validation_results = {
                    "coordinate_accuracy": self._validate_coordinate_accuracy(calibration_data),
                    "scale_accuracy": self._validate_scale_accuracy(calibration_data),
                    "cross_device_consistency": self._validate_cross_device_consistency(calibration_data),
                    "environmental_factors": self._validate_environmental_factors(calibration_data),
                    "overall_score": 0.0
                }
                
                # Calculate overall validation score
                scores = [
                    validation_results["coordinate_accuracy"]["score"],
                    validation_results["scale_accuracy"]["score"],
                    validation_results["cross_device_consistency"]["score"],
                    validation_results["environmental_factors"]["score"]
                ]
                validation_results["overall_score"] = np.mean(scores)
                
                # Update calibration data
                calibration_data.validation_results = validation_results
                calibration_data.accuracy_score = validation_results["overall_score"]
                
                # Determine if calibration is acceptable
                is_acceptable = validation_results["overall_score"] >= 0.95
                
                if is_acceptable:
                    calibration_data.status = CalibrationStatus.APPLIED
                    calibration_data.applied_at = datetime.now()
                else:
                    calibration_data.status = CalibrationStatus.FAILED
                
                # Save to database
                self._save_calibration_to_db(calibration_data)
                
                logger.info(f"Calibration validation completed: {validation_results['overall_score']:.3f}")
                
                return {
                    "status": "success",
                    "validation_results": validation_results,
                    "is_acceptable": is_acceptable,
                    "calibration_id": calibration_id
                }
                
        except Exception as e:
            logger.error(f"Calibration validation failed: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    def apply_calibration(self, calibration_id: str) -> Dict[str, Any]:
        """
        Apply calibration to AR session.
        
        Args:
            calibration_id: Calibration ID to apply
            
        Returns:
            Calibration application results
        """
        try:
            with self._lock:
                if calibration_id not in self.calibration_data:
                    return {"status": "error", "error": "Invalid calibration ID"}
                
                calibration_data = self.calibration_data[calibration_id]
                
                if calibration_data.status != CalibrationStatus.APPLIED:
                    return {
                        "status": "error",
                        "error": f"Calibration not ready for application (status: {calibration_data.status.value})"
                    }
                
                # Apply transformation to AR session
                transform_matrix = calibration_data.transform_matrix["combined"]
                scale_factor = calibration_data.scale_factor
                
                # Store active calibration
                self.coordinate_transforms[calibration_data.session_id] = {
                    "transform_matrix": transform_matrix,
                    "scale_factor": scale_factor,
                    "calibration_id": calibration_id
                }
                
                logger.info(f"Applied calibration: {calibration_id}")
                
                return {
                    "status": "success",
                    "calibration_id": calibration_id,
                    "transform_matrix": transform_matrix,
                    "scale_factor": scale_factor,
                    "accuracy_score": calibration_data.accuracy_score
                }
                
        except Exception as e:
            logger.error(f"Calibration application failed: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    def get_calibration_status(self, session_id: str = None) -> Dict[str, Any]:
        """
        Get current calibration status and accuracy metrics.
        
        Args:
            session_id: Optional session ID to get specific status
            
        Returns:
            Calibration status information
        """
        try:
            with self._lock:
                if session_id:
                    if session_id not in self.active_sessions:
                        return {"status": "error", "error": "Invalid session ID"}
                    
                    calibration_id = self.active_sessions[session_id]
                    calibration_data = self.calibration_data[calibration_id]
                    
                    return {
                        "status": "success",
                        "session_id": session_id,
                        "calibration_id": calibration_id,
                        "calibration_status": calibration_data.status.value,
                        "accuracy_score": calibration_data.accuracy_score,
                        "reference_points_count": len(calibration_data.reference_points),
                        "created_at": calibration_data.created_at.isoformat(),
                        "updated_at": calibration_data.updated_at.isoformat()
                    }
                else:
                    # Return overall status
                    total_calibrations = len(self.calibration_data)
                    active_sessions = len(self.active_sessions)
                    successful_calibrations = sum(
                        1 for cal in self.calibration_data.values()
                        if cal.status == CalibrationStatus.APPLIED
                    )
                    
                    return {
                        "status": "success",
                        "total_calibrations": total_calibrations,
                        "active_sessions": active_sessions,
                        "successful_calibrations": successful_calibrations,
                        "success_rate": successful_calibrations / total_calibrations if total_calibrations > 0 else 0.0
                    }
                    
        except Exception as e:
            logger.error(f"Failed to get calibration status: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    def save_calibration(self, calibration_id: str) -> Dict[str, Any]:
        """
        Save calibration data for future use.
        
        Args:
            calibration_id: Calibration ID to save
            
        Returns:
            Save operation results
        """
        try:
            with self._lock:
                if calibration_id not in self.calibration_data:
                    return {"status": "error", "error": "Invalid calibration ID"}
                
                calibration_data = self.calibration_data[calibration_id]
                
                # Save to database (already done in other methods)
                self._save_calibration_to_db(calibration_data)
                
                logger.info(f"Saved calibration: {calibration_id}")
                
                return {
                    "status": "success",
                    "calibration_id": calibration_id,
                    "saved_at": datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Failed to save calibration: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    def load_calibration(self, calibration_id: str) -> Dict[str, Any]:
        """
        Load saved calibration data.
        
        Args:
            calibration_id: Calibration ID to load
            
        Returns:
            Loaded calibration data
        """
        try:
            with self._lock:
                if calibration_id not in self.calibration_data:
                    return {"status": "error", "error": "Invalid calibration ID"}
                
                calibration_data = self.calibration_data[calibration_id]
                
                return {
                    "status": "success",
                    "calibration_data": asdict(calibration_data)
                }
                
        except Exception as e:
            logger.error(f"Failed to load calibration: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    # Helper methods for coordinate calculations
    
    def _detect_corners(self, point_cloud: List[Dict], plane_anchors: List[Dict]) -> List[Dict]:
        """Detect corner points in AR frame."""
        corners = []
        
        # Simple corner detection based on point cloud density
        if len(point_cloud) > 100:
            # Find points with high local density (potential corners)
            for i, point in enumerate(point_cloud[:50]):  # Sample first 50 points
                local_density = self._calculate_local_density(point, point_cloud)
                if local_density > 0.7:  # High density threshold
                    corners.append({
                        "type": ReferencePointType.CORNER,
                        "ar_coordinates": point,
                        "real_world_coordinates": self._estimate_real_world_coords(point),
                        "svg_coordinates": self._estimate_svg_coords(point),
                        "confidence": min(local_density, 0.9)
                    })
        
        return corners
    
    def _detect_plane_intersections(self, plane_anchors: List[Dict]) -> List[Dict]:
        """Detect intersection points between planes."""
        intersections = []
        
        if len(plane_anchors) >= 2:
            # Find intersections between different planes
            for i in range(len(plane_anchors)):
                for j in range(i + 1, len(plane_anchors)):
                    intersection = self._calculate_plane_intersection(
                        plane_anchors[i], plane_anchors[j]
                    )
                    if intersection:
                        intersections.append({
                            "type": ReferencePointType.AUTOMATIC,
                            "ar_coordinates": intersection,
                            "real_world_coordinates": self._estimate_real_world_coords(intersection),
                            "svg_coordinates": self._estimate_svg_coords(intersection),
                            "confidence": 0.8
                        })
        
        return intersections
    
    def _detect_feature_points(self, point_cloud: List[Dict]) -> List[Dict]:
        """Detect feature points in point cloud."""
        features = []
        
        # Simple feature detection based on geometric patterns
        if len(point_cloud) > 50:
            for point in point_cloud[:20]:  # Sample first 20 points
                # Check if point has distinctive geometric properties
                if self._is_feature_point(point, point_cloud):
                    features.append({
                        "type": ReferencePointType.AUTOMATIC,
                        "ar_coordinates": point,
                        "real_world_coordinates": self._estimate_real_world_coords(point),
                        "svg_coordinates": self._estimate_svg_coords(point),
                        "confidence": 0.7
                    })
        
        return features
    
    def _filter_reference_points(self, points: List[Dict]) -> List[Dict]:
        """Filter and rank reference points by confidence and quality."""
        if not points:
            return []
        
        # Sort by confidence
        sorted_points = sorted(points, key=lambda p: p["confidence"], reverse=True)
        
        # Remove duplicates (points too close to each other)
        filtered_points = []
        for point in sorted_points:
            is_duplicate = False
            for existing in filtered_points:
                distance = self._calculate_distance(point["ar_coordinates"], existing["ar_coordinates"])
                if distance < 0.1:  # 10cm threshold
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                filtered_points.append(point)
        
        return filtered_points[:10]  # Return top 10 points
    
    def _calculate_transformation_matrix(self, source_points: np.ndarray, target_points: np.ndarray) -> np.ndarray:
        """Calculate transformation matrix between two sets of points."""
        if len(source_points) < 3 or len(target_points) < 3:
            raise ValueError("Need at least 3 points for transformation calculation")
        
        # Use SVD-based method for rigid body transformation
        # Center the points
        source_centered = source_points - np.mean(source_points, axis=0)
        target_centered = target_points - np.mean(target_points, axis=0)
        
        # Calculate covariance matrix
        H = source_centered.T @ target_centered
        
        # SVD decomposition
        U, S, Vt = np.linalg.svd(H)
        
        # Calculate rotation matrix
        R = Vt.T @ U.T
        
        # Ensure proper rotation matrix (handle reflection case)
        if np.linalg.det(R) < 0:
            Vt[-1, :] *= -1
            R = Vt.T @ U.T
        
        # Calculate translation
        t = np.mean(target_points, axis=0) - R @ np.mean(source_points, axis=0)
        
        # Create transformation matrix
        transform = np.eye(4)
        transform[:3, :3] = R
        transform[:3, 3] = t
        
        return transform
    
    def _calculate_scale_factor(self, ar_coords: List[List[float]], real_world_coords: List[List[float]]) -> float:
        """Calculate scale factor between AR and real-world coordinates."""
        if len(ar_coords) < 2 or len(real_world_coords) < 2:
            return 1.0
        
        # Calculate distances in both coordinate systems
        ar_distances = []
        real_distances = []
        
        for i in range(len(ar_coords)):
            for j in range(i + 1, len(ar_coords)):
                ar_dist = np.linalg.norm(np.array(ar_coords[i]) - np.array(ar_coords[j]))
                real_dist = np.linalg.norm(np.array(real_world_coords[i]) - np.array(real_world_coords[j]))
                
                if real_dist > 0:  # Avoid division by zero
                    ar_distances.append(ar_dist)
                    real_distances.append(real_dist)
        
        if not ar_distances:
            return 1.0
        
        # Calculate scale factors and take median
        scale_factors = [ar_dist / real_dist for ar_dist, real_dist in zip(ar_distances, real_distances)]
        return np.median(scale_factors)
    
    def _calculate_accuracy_score(self, reference_points: List[ReferencePoint], transform_matrix: Dict) -> float:
        """Calculate accuracy score based on transformation quality."""
        if len(reference_points) < 3:
            return 0.0
        
        # Apply transformation to AR coordinates and compare with real-world coordinates
        errors = []
        
        for point in reference_points:
            ar_coord = np.array([
                point.ar_coordinates["x"],
                point.ar_coordinates["y"],
                point.ar_coordinates["z"]
            ])
            
            real_coord = np.array([
                point.real_world_coordinates["x"],
                point.real_world_coordinates["y"],
                point.real_world_coordinates["z"]
            ])
            
            # Apply transformation
            transform = np.array(transform_matrix["ar_to_real"])
            transformed_coord = transform[:3, :3] @ ar_coord + transform[:3, 3]
            
            # Calculate error
            error = np.linalg.norm(transformed_coord - real_coord)
            errors.append(error)
        
        # Calculate accuracy score (inverse of mean error)
        mean_error = np.mean(errors)
        max_acceptable_error = 0.1  # 10cm threshold
        
        if mean_error == 0:
            return 1.0
        
        accuracy = max(0.0, 1.0 - (mean_error / max_acceptable_error))
        return min(1.0, accuracy)
    
    def _validate_coordinate_accuracy(self, calibration_data: CalibrationData) -> Dict[str, Any]:
        """Validate coordinate accuracy."""
        if not calibration_data.reference_points:
            return {"score": 0.0, "details": "No reference points available"}
        
        # Calculate reprojection errors
        errors = []
        for point in calibration_data.reference_points:
            ar_coord = np.array([
                point.ar_coordinates["x"],
                point.ar_coordinates["y"],
                point.ar_coordinates["z"]
            ])
            
            real_coord = np.array([
                point.real_world_coordinates["x"],
                point.real_world_coordinates["y"],
                point.real_world_coordinates["z"]
            ])
            
            transform = np.array(calibration_data.transform_matrix["ar_to_real"])
            transformed_coord = transform[:3, :3] @ ar_coord + transform[:3, 3]
            
            error = np.linalg.norm(transformed_coord - real_coord)
            errors.append(error)
        
        mean_error = np.mean(errors)
        max_error = np.max(errors)
        
        # Score based on error magnitude
        score = max(0.0, 1.0 - (mean_error / 0.05))  # 5cm threshold
        
        return {
            "score": score,
            "mean_error": mean_error,
            "max_error": max_error,
            "point_count": len(errors)
        }
    
    def _validate_scale_accuracy(self, calibration_data: CalibrationData) -> Dict[str, Any]:
        """Validate scale accuracy."""
        scale_factor = calibration_data.scale_factor
        expected_scale = 1.0  # Assuming 1:1 scale
        
        scale_error = abs(scale_factor - expected_scale)
        score = max(0.0, 1.0 - (scale_error / 0.1))  # 10% threshold
        
        return {
            "score": score,
            "scale_factor": scale_factor,
            "scale_error": scale_error,
            "expected_scale": expected_scale
        }
    
    def _validate_cross_device_consistency(self, calibration_data: CalibrationData) -> Dict[str, Any]:
        """Validate cross-device consistency."""
        # Check if similar calibrations exist for other devices
        device_id = calibration_data.device_id
        svg_file_hash = calibration_data.svg_file_hash
        
        similar_calibrations = []
        for cal in self.calibration_data.values():
            if (cal.svg_file_hash == svg_file_hash and 
                cal.device_id != device_id and 
                cal.status == CalibrationStatus.APPLIED):
                similar_calibrations.append(cal)
        
        if not similar_calibrations:
            return {"score": 0.8, "details": "No comparison calibrations available"}
        
        # Compare scale factors and accuracy scores
        scale_factors = [cal.scale_factor for cal in similar_calibrations]
        accuracy_scores = [cal.accuracy_score for cal in similar_calibrations]
        
        scale_variance = np.var(scale_factors)
        accuracy_variance = np.var(accuracy_scores)
        
        # Score based on consistency
        scale_consistency = max(0.0, 1.0 - (scale_variance / 0.01))
        accuracy_consistency = max(0.0, 1.0 - (accuracy_variance / 0.01))
        
        overall_score = (scale_consistency + accuracy_consistency) / 2
        
        return {
            "score": overall_score,
            "comparison_count": len(similar_calibrations),
            "scale_variance": scale_variance,
            "accuracy_variance": accuracy_variance
        }
    
    def _validate_environmental_factors(self, calibration_data: CalibrationData) -> Dict[str, Any]:
        """Validate environmental factors affecting calibration."""
        # Check reference point distribution and quality
        points = calibration_data.reference_points
        
        if not points:
            return {"score": 0.0, "details": "No reference points available"}
        
        # Calculate point distribution
        ar_coords = np.array([
            [p.ar_coordinates["x"], p.ar_coordinates["y"], p.ar_coordinates["z"]]
            for p in points
        ])
        
        # Calculate bounding box
        min_coords = np.min(ar_coords, axis=0)
        max_coords = np.max(ar_coords, axis=0)
        volume = np.prod(max_coords - min_coords)
        
        # Score based on volume coverage (larger is better)
        volume_score = min(1.0, volume / 1.0)  # 1 cubic meter threshold
        
        # Score based on point count
        count_score = min(1.0, len(points) / 10.0)  # 10 points threshold
        
        # Score based on average confidence
        confidence_score = np.mean([p.confidence for p in points])
        
        overall_score = (volume_score + count_score + confidence_score) / 3
        
        return {
            "score": overall_score,
            "volume_coverage": volume,
            "point_count": len(points),
            "avg_confidence": confidence_score
        }
    
    # Utility methods
    
    def _find_existing_calibration(self, device_id: str, svg_file_hash: str) -> Optional[CalibrationData]:
        """Find existing calibration for device and SVG file."""
        for calibration in self.calibration_data.values():
            if (calibration.device_id == device_id and 
                calibration.svg_file_hash == svg_file_hash and
                calibration.status == CalibrationStatus.APPLIED):
                return calibration
        return None
    
    def _save_calibration_to_db(self, calibration_data: CalibrationData):
        """Save calibration data to database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Save main calibration data
                conn.execute("""
                    INSERT OR REPLACE INTO calibrations 
                    (calibration_id, session_id, device_id, svg_file_hash, transform_matrix,
                     scale_factor, accuracy_score, status, created_at, updated_at, applied_at, validation_results)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    calibration_data.calibration_id,
                    calibration_data.session_id,
                    calibration_data.device_id,
                    calibration_data.svg_file_hash,
                    json.dumps(calibration_data.transform_matrix),
                    calibration_data.scale_factor,
                    calibration_data.accuracy_score,
                    calibration_data.status.value,
                    calibration_data.created_at.isoformat(),
                    calibration_data.updated_at.isoformat(),
                    calibration_data.applied_at.isoformat() if calibration_data.applied_at else None,
                    json.dumps(calibration_data.validation_results) if calibration_data.validation_results else None
                ))
                
                # Save reference points
                for point in calibration_data.reference_points:
                    conn.execute("""
                        INSERT OR REPLACE INTO reference_points 
                        (point_id, calibration_id, point_type, ar_coordinates, real_world_coordinates,
                         svg_coordinates, confidence, timestamp, device_id, session_id)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        point.point_id,
                        calibration_data.calibration_id,
                        point.point_type.value,
                        json.dumps(point.ar_coordinates),
                        json.dumps(point.real_world_coordinates),
                        json.dumps(point.svg_coordinates),
                        point.confidence,
                        point.timestamp.isoformat(),
                        point.device_id,
                        point.session_id
                    ))
                
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to save calibration to database: {e}")
    
    def _calculate_local_density(self, point: Dict, point_cloud: List[Dict]) -> float:
        """Calculate local point density around a given point."""
        if not point_cloud:
            return 0.0
        
        # Count points within a small radius
        radius = 0.1  # 10cm radius
        nearby_points = 0
        
        for other_point in point_cloud:
            distance = self._calculate_distance(point, other_point)
            if distance < radius:
                nearby_points += 1
        
        return nearby_points / len(point_cloud)
    
    def _calculate_distance(self, point1: Dict, point2: Dict) -> float:
        """Calculate Euclidean distance between two points."""
        return np.linalg.norm([
            point1["x"] - point2["x"],
            point1["y"] - point2["y"],
            point1["z"] - point2["z"]
        ])
    
    def _calculate_plane_intersection(self, plane1: Dict, plane2: Dict) -> Optional[Dict]:
        """Calculate intersection point between two planes."""
        # Simplified plane intersection calculation
        # In practice, this would use proper plane geometry
        try:
            # Extract plane parameters (simplified)
            p1_normal = np.array([plane1.get("normal", {}).get("x", 0),
                                 plane1.get("normal", {}).get("y", 0),
                                 plane1.get("normal", {}).get("z", 1)])
            p1_point = np.array([plane1.get("center", {}).get("x", 0),
                                plane1.get("center", {}).get("y", 0),
                                plane1.get("center", {}).get("z", 0)])
            
            p2_normal = np.array([plane2.get("normal", {}).get("x", 0),
                                 plane2.get("normal", {}).get("y", 0),
                                 plane2.get("normal", {}).get("z", 1)])
            p2_point = np.array([plane2.get("center", {}).get("x", 0),
                                plane2.get("center", {}).get("y", 0),
                                plane2.get("center", {}).get("z", 0)])
            
            # Calculate intersection line direction
            intersection_dir = np.cross(p1_normal, p2_normal)
            
            if np.linalg.norm(intersection_dir) < 1e-6:
                return None  # Planes are parallel
            
            # Find a point on the intersection line
            # This is a simplified calculation
            intersection_point = (p1_point + p2_point) / 2
            
            return {
                "x": float(intersection_point[0]),
                "y": float(intersection_point[1]),
                "z": float(intersection_point[2])
            }
        except Exception:
            return None
    
    def _is_feature_point(self, point: Dict, point_cloud: List[Dict]) -> bool:
        """Check if a point has distinctive geometric properties."""
        # Simplified feature point detection
        # In practice, this would use more sophisticated algorithms
        
        # Check if point has high local curvature or distinctive properties
        local_points = []
        for other_point in point_cloud:
            distance = self._calculate_distance(point, other_point)
            if distance < 0.2:  # 20cm radius
                local_points.append(other_point)
        
        # Simple heuristic: if point has moderate number of neighbors, it might be a feature
        neighbor_count = len(local_points)
        return 3 <= neighbor_count <= 15
    
    def _estimate_real_world_coords(self, ar_coord: Dict) -> Dict[str, float]:
        """Estimate real-world coordinates from AR coordinates."""
        # Simplified estimation - in practice, this would use more sophisticated mapping
        return {
            "x": ar_coord.get("x", 0.0),
            "y": ar_coord.get("y", 0.0),
            "z": ar_coord.get("z", 0.0)
        }
    
    def _estimate_svg_coords(self, ar_coord: Dict) -> Dict[str, float]:
        """Estimate SVG coordinates from AR coordinates."""
        # Simplified estimation - in practice, this would use SVG coordinate system
        return {
            "x": ar_coord.get("x", 0.0),
            "y": ar_coord.get("y", 0.0),
            "z": ar_coord.get("z", 0.0)
        }
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics for the calibration service."""
        try:
            with self._lock:
                total_calibrations = len(self.calibration_data)
                successful_calibrations = sum(
                    1 for cal in self.calibration_data.values()
                    if cal.status == CalibrationStatus.APPLIED
                )
                
                if total_calibrations > 0:
                    success_rate = successful_calibrations / total_calibrations
                    avg_accuracy = np.mean([
                        cal.accuracy_score for cal in self.calibration_data.values()
                        if cal.accuracy_score > 0
                    ])
                else:
                    success_rate = 0.0
                    avg_accuracy = 0.0
                
                return {
                    "total_calibrations": total_calibrations,
                    "successful_calibrations": successful_calibrations,
                    "success_rate": success_rate,
                    "average_accuracy": avg_accuracy,
                    "active_sessions": len(self.active_sessions),
                    "database_size": Path(self.db_path).stat().st_size if Path(self.db_path).exists() else 0
                }
        except Exception as e:
            logger.error(f"Failed to get performance metrics: {e}")
            return {"error": str(e)} 