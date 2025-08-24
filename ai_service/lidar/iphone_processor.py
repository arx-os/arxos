"""
iPhone LiDAR Processing
Converts iPhone 3D scans to architectural BIM elements
"""

import logging
from typing import Dict, List, Any, Optional
import io

import numpy as np
import open3d as o3d
from scipy.spatial import ConvexHull
from sklearn.cluster import DBSCAN

logger = logging.getLogger(__name__)

class iPhoneLiDARProcessor:
    """
    Process iPhone LiDAR scans (RoomPlan API data)
    Extracts walls, floors, and room geometry from 3D point clouds
    """
    
    def __init__(self):
        self.current_scan = None
        self.accumulated_points = []
        
    async def process_scan(
        self, 
        scan_data: bytes,
        format: str = '.ply'
    ) -> Dict[str, Any]:
        """
        Process complete LiDAR scan from iPhone
        
        Supported formats:
        - PLY (Point Cloud)
        - USDZ (Apple's 3D format)
        - OBJ (Mesh)
        
        Returns:
        - Detected walls
        - Floor plane
        - Room boundaries
        """
        try:
            # Load point cloud
            if format == '.ply':
                pcd = self._load_ply(scan_data)
            elif format == '.usdz':
                pcd = self._load_usdz(scan_data)
            else:
                raise ValueError(f"Unsupported format: {format}")
            
            # Preprocess point cloud
            pcd = self._preprocess_pointcloud(pcd)
            
            # Detect floor plane using RANSAC
            floor = self._detect_floor_plane(pcd)
            
            # Extract walls using projection and line detection
            walls = self._detect_walls(pcd, floor)
            
            # Identify rooms from wall intersections
            rooms = self._identify_rooms(walls, floor)
            
            # Calculate quality metrics
            quality = self._assess_scan_quality(pcd)
            
            return {
                'walls': walls,
                'floor': floor,
                'rooms': rooms,
                'point_count': len(pcd.points),
                'quality_score': quality,
                'processing_time': 0.0  # TODO: Add timing
            }
            
        except Exception as e:
            logger.error(f"LiDAR processing failed: {e}")
            raise
    
    async def process_stream_chunk(self, chunk_data: bytes) -> Dict[str, Any]:
        """
        Process streaming LiDAR data from iPhone in real-time
        Used for live scanning with WebSocket
        """
        # Accumulate points
        new_points = self._parse_stream_chunk(chunk_data)
        self.accumulated_points.extend(new_points)
        
        # Process if we have enough points
        if len(self.accumulated_points) > 1000:
            # Create point cloud from accumulated data
            pcd = o3d.geometry.PointCloud()
            pcd.points = o3d.utility.Vector3dVector(
                np.array(self.accumulated_points)
            )
            
            # Quick wall detection on partial scan
            walls = self._detect_walls_incremental(pcd)
            
            return {
                'new_elements': walls,
                'progress': self._estimate_scan_progress()
            }
        
        return {'new_elements': [], 'progress': 0.0}
    
    def _load_ply(self, data: bytes) -> o3d.geometry.PointCloud:
        """Load PLY format point cloud"""
        # Create temporary file-like object
        file = io.BytesIO(data)
        
        # Open3D needs a file path, so we save temporarily
        import tempfile
        with tempfile.NamedTemporaryFile(suffix='.ply', delete=False) as tmp:
            tmp.write(data)
            tmp_path = tmp.name
        
        pcd = o3d.io.read_point_cloud(tmp_path)
        
        # Clean up temp file
        import os
        os.unlink(tmp_path)
        
        return pcd
    
    def _load_usdz(self, data: bytes) -> o3d.geometry.PointCloud:
        """Load Apple USDZ format (from RoomPlan API)"""
        # TODO: Implement USDZ parsing
        # This would extract point cloud from Apple's format
        logger.warning("USDZ support not yet implemented")
        return o3d.geometry.PointCloud()
    
    def _preprocess_pointcloud(self, pcd: o3d.geometry.PointCloud) -> o3d.geometry.PointCloud:
        """Clean and downsample point cloud"""
        # Remove outliers
        pcd, _ = pcd.remove_statistical_outlier(
            nb_neighbors=20,
            std_ratio=2.0
        )
        
        # Downsample for faster processing
        pcd = pcd.voxel_down_sample(voxel_size=0.02)  # 2cm voxels
        
        # Estimate normals
        pcd.estimate_normals()
        
        return pcd
    
    def _detect_floor_plane(self, pcd: o3d.geometry.PointCloud) -> Dict[str, Any]:
        """
        Detect floor plane using RANSAC
        Assumes floor is the largest horizontal plane
        """
        points = np.asarray(pcd.points)
        
        # RANSAC for plane fitting
        plane_model, inliers = pcd.segment_plane(
            distance_threshold=0.01,
            ransac_n=3,
            num_iterations=1000
        )
        
        # Extract floor points
        floor_cloud = pcd.select_by_index(inliers)
        floor_points = np.asarray(floor_cloud.points)
        
        # Get floor boundary
        if len(floor_points) > 3:
            hull = ConvexHull(floor_points[:, :2])  # 2D projection
            boundary = floor_points[hull.vertices]
        else:
            boundary = floor_points
        
        return {
            'plane': plane_model.tolist(),  # [a, b, c, d] where ax+by+cz+d=0
            'elevation': -plane_model[3] / plane_model[2],  # z when x=y=0
            'area': hull.volume if len(floor_points) > 3 else 0,  # 2D area
            'boundary': boundary.tolist()
        }
    
    def _detect_walls(
        self, 
        pcd: o3d.geometry.PointCloud,
        floor: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Detect walls from point cloud
        Projects points to 2D and finds vertical surfaces
        """
        points = np.asarray(pcd.points)
        
        # Remove floor points (within threshold of floor plane)
        plane = floor['plane']
        distances = np.abs(
            points[:, 0] * plane[0] + 
            points[:, 1] * plane[1] + 
            points[:, 2] * plane[2] + 
            plane[3]
        )
        wall_mask = distances > 0.1  # Points >10cm from floor
        wall_points = points[wall_mask]
        
        # Cluster wall points
        if len(wall_points) > 0:
            clustering = DBSCAN(eps=0.1, min_samples=50).fit(wall_points)
            labels = clustering.labels_
        else:
            return []
        
        walls = []
        for label in set(labels):
            if label == -1:  # Noise
                continue
            
            cluster_points = wall_points[labels == label]
            
            # Fit line to cluster (simplified - should use RANSAC)
            if len(cluster_points) > 10:
                # Project to 2D (top view)
                points_2d = cluster_points[:, :2]
                
                # Fit line using PCA
                mean = np.mean(points_2d, axis=0)
                centered = points_2d - mean
                cov = np.cov(centered.T)
                eigenvalues, eigenvectors = np.linalg.eig(cov)
                
                # Principal direction is the wall direction
                direction = eigenvectors[:, np.argmax(eigenvalues)]
                
                # Get wall endpoints
                projections = centered @ direction
                start_idx = np.argmin(projections)
                end_idx = np.argmax(projections)
                
                start_point = cluster_points[start_idx]
                end_point = cluster_points[end_idx]
                
                # Calculate wall height
                height = np.max(cluster_points[:, 2]) - np.min(cluster_points[:, 2])
                
                walls.append({
                    'id': len(walls),
                    'line_3d': [start_point.tolist(), end_point.tolist()],
                    'height': float(height),
                    'confidence': min(len(cluster_points) / 100, 1.0),
                    'point_count': len(cluster_points)
                })
        
        return walls
    
    def _detect_walls_incremental(self, pcd: o3d.geometry.PointCloud) -> List[Dict[str, Any]]:
        """Quick wall detection for streaming data"""
        # Simplified version for real-time processing
        points = np.asarray(pcd.points)
        
        # Quick clustering
        if len(points) > 100:
            clustering = DBSCAN(eps=0.15, min_samples=30).fit(points)
            
            walls = []
            for label in set(clustering.labels_):
                if label == -1:
                    continue
                    
                cluster = points[clustering.labels_ == label]
                if len(cluster) > 50:
                    # Simple bounding box as wall
                    min_pt = np.min(cluster, axis=0)
                    max_pt = np.max(cluster, axis=0)
                    
                    walls.append({
                        'id': label,
                        'bounds': [min_pt.tolist(), max_pt.tolist()],
                        'confidence': 0.5  # Lower confidence for quick detection
                    })
            
            return walls
        
        return []
    
    def _identify_rooms(
        self, 
        walls: List[Dict[str, Any]],
        floor: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Identify rooms from wall intersections
        Creates closed polygons from wall segments
        """
        if len(walls) < 3:
            return []
        
        # TODO: Implement room detection from walls
        # This would:
        # 1. Find wall intersections
        # 2. Build graph of connected walls
        # 3. Find closed loops (rooms)
        # 4. Calculate room properties
        
        # Placeholder for now
        rooms = [{
            'id': 0,
            'boundary_3d': floor.get('boundary', []),
            'height': 2.5,  # Assume standard height
            'volume': floor.get('area', 0) * 2.5,
            'floor_area': floor.get('area', 0)
        }]
        
        return rooms
    
    def _assess_scan_quality(self, pcd: o3d.geometry.PointCloud) -> float:
        """Assess scan quality based on point density and coverage"""
        points = np.asarray(pcd.points)
        
        if len(points) == 0:
            return 0.0
        
        # Calculate metrics
        density = len(points) / 1000  # Points per square meter (estimated)
        
        # Check coverage (bounding box volume)
        min_bound = points.min(axis=0)
        max_bound = points.max(axis=0)
        volume = np.prod(max_bound - min_bound)
        
        # Quality score (0-1)
        quality = min(1.0, density / 100) * min(1.0, volume / 100)
        
        return float(quality)
    
    def _parse_stream_chunk(self, data: bytes) -> List[List[float]]:
        """Parse streaming point cloud data from iPhone"""
        # This would parse the binary format from iPhone
        # Typically: [x, y, z, confidence] per point
        
        # Placeholder - actual implementation would parse binary
        return []
    
    def _estimate_scan_progress(self) -> float:
        """Estimate scanning progress based on accumulated data"""
        # Simple heuristic based on point count
        target_points = 50000  # Expected points for complete scan
        progress = min(1.0, len(self.accumulated_points) / target_points)
        return progress