"""
Advanced Floor Management Service
Comprehensive floor management with grid calibration, analytics, comparison, and route management
"""

import logging
import asyncio
from typing import Dict, List, Optional, Any, Tuple, Union
from datetime import datetime, timedelta
from uuid import uuid4
import json
import math
import os
from pathlib import Path

from arx_svg_parser.models.floor_management import (
    EnhancedFloor, GridCalibration, FloorAnalytics, FloorComparison,
    GridCalibrationRequest, GridCalibrationResponse, FloorAnalyticsRequest,
    FloorAnalyticsResponse, FloorComparisonRequest, FloorComparisonResponse,
    FloorMergeRequest, FloorMergeResponse, FloorDashboardResponse,
    GridPoint
)
from arx_svg_parser.models.route import (
    Route, RoutePoint, RouteGeometry, RouteSegment,
    RouteCreateRequest, RouteUpdateRequest, RouteResponse,
    RouteListResponse, RouteAnalytics, RouteOptimizationRequest,
    RouteConflict, RouteValidationResult
)
from arx_svg_parser.utils.logger import logger
from arx_svg_parser.utils.auth import get_current_user
from arx_svg_parser.services.cache_service import cache_service

class FloorStatus:
    """Floor status constants"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    MAINTENANCE = "maintenance"
    ARCHIVED = "archived"
    TEMPLATE = "template"

class Floor:
    """Simple Floor model for compatibility"""
    def __init__(self, id: str, name: str, building_id: str, **kwargs):
        self.id = id
        self.name = name
        self.building_id = building_id
        for key, value in kwargs.items():
            setattr(self, key, value)

class FloorManager:
    """
    Advanced Floor Management Service
    
    Provides comprehensive floor management including:
    - Grid calibration and alignment
    - Floor analytics and performance tracking
    - Floor comparison and merging
    - Route management and optimization
    - Quality assessment and validation
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.floors: Dict[str, EnhancedFloor] = {}
        self.grid_calibrations: Dict[str, GridCalibration] = {}
        self.floor_analytics: Dict[str, FloorAnalytics] = {}
        self.routes: Dict[str, List[Route]] = {}
        self.comparisons: Dict[str, FloorComparison] = {}
        
        # Performance tracking
        self.performance_metrics = {
            'total_floors': 0,
            'active_floors': 0,
            'total_routes': 0,
            'total_analytics': 0,
            'last_updated': datetime.utcnow()
        }
        
        # Cache keys
        self.cache_prefix = "floor_manager"
        
    async def start(self):
        """Start the floor manager service"""
        self.logger.info("Starting Floor Manager Service")
        await self._load_floors_from_storage()
        await self._initialize_analytics()
        await self._validate_all_floors()
        self.logger.info(f"Floor Manager Service started with {len(self.floors)} floors")
    
    async def stop(self):
        """Stop the floor manager service"""
        self.logger.info("Stopping Floor Manager Service")
        await self._save_floors_to_storage()
        await self._save_analytics_to_storage()
        self.logger.info("Floor Manager Service stopped")
    
    # ============================================================================
    # FLOOR CRUD OPERATIONS
    # ============================================================================
    
    async def create_floor(self, floor_data: Dict[str, Any], user_id: Optional[str] = None) -> EnhancedFloor:
        """Create a new floor"""
        try:
            floor_id = str(uuid4())
            floor = EnhancedFloor(
                id=floor_id,
                name=floor_data['name'],
                building_id=floor_data['building_id'],
                floor_number=floor_data.get('floor_number'),
                floor_type=floor_data.get('floor_type', 'standard'),
                floor_area=floor_data.get('floor_area'),
                floor_height=floor_data.get('floor_height'),
                svg_path=floor_data['svg_path'],
                thumbnail_path=floor_data.get('thumbnail_path'),
                metadata_path=floor_data.get('metadata_path'),
                description=floor_data.get('description'),
                tags=floor_data.get('tags', []),
                properties=floor_data.get('properties', {}),
                created_by=user_id,
                created_at=datetime.utcnow(),
                updated_by=user_id,
                updated_at=datetime.utcnow()
            )
            
            # Validate floor
            validation_errors = await self._validate_floor(floor)
            if validation_errors:
                floor.validation_errors = validation_errors
                floor.validation_status = "invalid"
            else:
                floor.validation_status = "validated"
            
            # Initialize analytics
            analytics = FloorAnalytics(
                id=str(uuid4()),
                floor_id=floor_id,
                building_id=floor_data['building_id']
            )
            
            # Store floor and analytics
            self.floors[floor_id] = floor
            self.floor_analytics[floor_id] = analytics
            self.routes[floor_id] = []
            
            # Update performance metrics
            self.performance_metrics['total_floors'] += 1
            if floor.is_active:
                self.performance_metrics['active_floors'] += 1
            
            # Cache floor data
            await self._cache_floor(floor_id)
            
            self.logger.info(f"Created floor {floor_id} ({floor.name})")
            return floor
            
        except Exception as e:
            self.logger.error(f"Error creating floor: {e}")
            raise
    
    async def get_floor(self, floor_id: str) -> Optional[EnhancedFloor]:
        """Get a floor by ID"""
        try:
            # Check cache first
            cached_floor = await self._get_cached_floor(floor_id)
            if cached_floor:
                return cached_floor
            
            floor = self.floors.get(floor_id)
            if floor:
                await self._cache_floor(floor_id)
            return floor
            
        except Exception as e:
            self.logger.error(f"Error getting floor {floor_id}: {e}")
            return None
    
    async def update_floor(self, floor_id: str, update_data: Dict[str, Any], user_id: Optional[str] = None) -> Optional[EnhancedFloor]:
        """Update an existing floor"""
        try:
            floor = self.floors.get(floor_id)
            if not floor:
                return None
            
            # Update fields
            for field, value in update_data.items():
                if hasattr(floor, field) and field not in ['id', 'created_by', 'created_at']:
                    setattr(floor, field, value)
            
            # Update metadata
            floor.updated_by = user_id
            floor.updated_at = datetime.utcnow()
            
            # Revalidate floor
            validation_errors = await self._validate_floor(floor)
            if validation_errors:
                floor.validation_errors = validation_errors
                floor.validation_status = "invalid"
            else:
                floor.validation_status = "validated"
                floor.validation_errors = []
            
            # Update quality score
            await self._update_floor_quality_score(floor)
            
            # Update cache
            await self._cache_floor(floor_id)
            
            self.logger.info(f"Updated floor {floor_id}")
            return floor
            
        except Exception as e:
            self.logger.error(f"Error updating floor {floor_id}: {e}")
            return None
    
    async def delete_floor(self, floor_id: str) -> bool:
        """Delete a floor"""
        try:
            if floor_id not in self.floors:
                return False
            
            floor = self.floors[floor_id]
            
            # Update performance metrics
            self.performance_metrics['total_floors'] -= 1
            if floor.is_active:
                self.performance_metrics['active_floors'] -= 1
            
            # Remove from storage
            del self.floors[floor_id]
            if floor_id in self.floor_analytics:
                del self.floor_analytics[floor_id]
            if floor_id in self.routes:
                self.performance_metrics['total_routes'] -= len(self.routes[floor_id])
                del self.routes[floor_id]
            if floor_id in self.grid_calibrations:
                del self.grid_calibrations[floor_id]
            
            # Clear cache
            await self._clear_floor_cache(floor_id)
            
            self.logger.info(f"Deleted floor {floor_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error deleting floor {floor_id}: {e}")
            return False
    
    async def list_floors(self, building_id: Optional[str] = None, filters: Optional[Dict[str, Any]] = None) -> List[EnhancedFloor]:
        """List floors with optional filtering"""
        try:
            floors = list(self.floors.values())
            
            # Apply building filter
            if building_id:
                floors = [f for f in floors if f.building_id == building_id]
            
            # Apply additional filters
            if filters:
                if filters.get('is_active') is not None:
                    floors = [f for f in floors if f.is_active == filters['is_active']]
                if filters.get('floor_type'):
                    floors = [f for f in floors if f.floor_type == filters['floor_type']]
                if filters.get('validation_status'):
                    floors = [f for f in floors if f.validation_status == filters['validation_status']]
                if filters.get('tags'):
                    required_tags = set(filters['tags'])
                    floors = [f for f in floors if required_tags.issubset(set(f.tags))]
            
            return floors
            
        except Exception as e:
            self.logger.error(f"Error listing floors: {e}")
            return []
    
    # ============================================================================
    # GRID CALIBRATION
    # ============================================================================
    
    async def calibrate_grid(self, request: GridCalibrationRequest) -> GridCalibrationResponse:
        """Calibrate grid for a floor"""
        try:
            floor = self.floors.get(request.floor_id)
            if not floor:
                raise ValueError(f"Floor {request.floor_id} not found")
            
            # Create grid calibration
            calibration = GridCalibration(
                floor_id=request.floor_id,
                building_id=floor.building_id,
                grid_size=request.grid_size,
                grid_origin=request.grid_origin,
                grid_rotation=request.grid_rotation,
                grid_type=request.grid_type,
                calibration_points=request.calibration_points,
                reference_points=request.reference_points,
                aligned_with_floors=request.align_with_floors,
                created_by=request.created_by if hasattr(request, 'created_by') else None
            )
            
            # Calculate accuracy and confidence
            calibration.calibration_accuracy = calibration.calculate_accuracy()
            calibration.calibration_confidence = sum(p.confidence for p in calibration.calibration_points) / len(calibration.calibration_points)
            
            # Validate calibration
            validation_errors = await self._validate_grid_calibration(calibration)
            calibration.validation_errors = validation_errors
            calibration.is_valid = len(validation_errors) == 0
            
            # Align with other floors if requested
            alignment_results = {}
            if request.align_with_floors:
                alignment_results = await self._align_with_floors(calibration, request.align_with_floors)
            
            # Store calibration
            self.grid_calibrations[request.floor_id] = calibration
            floor.grid_calibration = calibration
            
            # Update floor quality score
            await self._update_floor_quality_score(floor)
            
            self.logger.info(f"Calibrated grid for floor {request.floor_id} with accuracy {calibration.calibration_accuracy:.2f}")
            
            return GridCalibrationResponse(
                calibration=calibration,
                accuracy=calibration.calibration_accuracy,
                confidence=calibration.calibration_confidence,
                validation_errors=validation_errors,
                alignment_results=alignment_results
            )
            
        except Exception as e:
            self.logger.error(f"Error calibrating grid for floor {request.floor_id}: {e}")
            raise
    
    async def get_grid_calibration(self, floor_id: str) -> Optional[GridCalibration]:
        """Get grid calibration for a floor"""
        return self.grid_calibrations.get(floor_id)
    
    async def update_grid_calibration(self, floor_id: str, calibration_data: Dict[str, Any]) -> Optional[GridCalibration]:
        """Update grid calibration for a floor"""
        try:
            calibration = self.grid_calibrations.get(floor_id)
            if not calibration:
                return None
            
            # Update calibration fields
            for field, value in calibration_data.items():
                if hasattr(calibration, field):
                    setattr(calibration, field, value)
            
            # Recalculate accuracy and confidence
            calibration.calibration_accuracy = calibration.calculate_accuracy()
            if calibration.calibration_points:
                calibration.calibration_confidence = sum(p.confidence for p in calibration.calibration_points) / len(calibration.calibration_points)
            
            # Revalidate
            validation_errors = await self._validate_grid_calibration(calibration)
            calibration.validation_errors = validation_errors
            calibration.is_valid = len(validation_errors) == 0
            
            # Update floor
            floor = self.floors.get(floor_id)
            if floor:
                floor.grid_calibration = calibration
                await self._update_floor_quality_score(floor)
            
            self.logger.info(f"Updated grid calibration for floor {floor_id}")
            return calibration
            
        except Exception as e:
            self.logger.error(f"Error updating grid calibration for floor {floor_id}: {e}")
            return None
    
    # ============================================================================
    # FLOOR ANALYTICS
    # ============================================================================
    
    async def get_floor_analytics(self, request: FloorAnalyticsRequest) -> FloorAnalyticsResponse:
        """Get analytics for a floor"""
        try:
            analytics = self.floor_analytics.get(request.floor_id)
            if not analytics:
                # Create new analytics if none exist
                floor = self.floors.get(request.floor_id)
                if not floor:
                    raise ValueError(f"Floor {request.floor_id} not found")
                
                analytics = FloorAnalytics(
                    id=str(uuid4()),
                    floor_id=request.floor_id,
                    building_id=floor.building_id
                )
                self.floor_analytics[request.floor_id] = analytics
            
            # Calculate trends
            trends = await self._calculate_analytics_trends(analytics, request.date_range)
            
            # Generate recommendations
            recommendations = await self._generate_analytics_recommendations(analytics)
            
            # Calculate performance indicators
            performance_indicators = await self._calculate_performance_indicators(analytics)
            
            return FloorAnalyticsResponse(
                analytics=analytics,
                trends=trends,
                recommendations=recommendations,
                performance_indicators=performance_indicators
            )
            
        except Exception as e:
            self.logger.error(f"Error getting analytics for floor {request.floor_id}: {e}")
            raise
    
    async def update_floor_analytics(self, floor_id: str, analytics_data: Dict[str, Any]) -> Optional[FloorAnalytics]:
        """Update floor analytics"""
        try:
            analytics = self.floor_analytics.get(floor_id)
            if not analytics:
                return None
            
            # Update analytics fields
            for field, value in analytics_data.items():
                if hasattr(analytics, field):
                    setattr(analytics, field, value)
            
            analytics.updated_at = datetime.utcnow()
            
            # Update cache
            await self._cache_analytics(floor_id)
            
            self.logger.info(f"Updated analytics for floor {floor_id}")
            return analytics
            
        except Exception as e:
            self.logger.error(f"Error updating analytics for floor {floor_id}: {e}")
            return None
    
    # ============================================================================
    # FLOOR COMPARISON
    # ============================================================================
    
    async def compare_floors(self, request: FloorComparisonRequest) -> FloorComparisonResponse:
        """Compare two floors"""
        try:
            floor1 = self.floors.get(request.floor_id_1)
            floor2 = self.floors.get(request.floor_id_2)
            
            if not floor1 or not floor2:
                raise ValueError("One or both floors not found")
            
            # Create comparison
            comparison = FloorComparison(
                floor_id_1=request.floor_id_1,
                floor_id_2=request.floor_id_2,
                building_id=floor1.building_id,
                comparison_type=request.comparison_type,
                created_by=request.created_by if hasattr(request, 'created_by') else None
            )
            
            # Perform comparison based on type
            if request.comparison_type == "layout":
                await self._compare_layouts(comparison, floor1, floor2)
            elif request.comparison_type == "objects":
                await self._compare_objects(comparison, floor1, floor2)
            elif request.comparison_type == "routes":
                await self._compare_routes(comparison, floor1, floor2)
            else:  # comprehensive
                await self._compare_comprehensive(comparison, floor1, floor2)
            
            # Calculate grid alignment if requested
            if request.include_grid_alignment:
                await self._calculate_grid_alignment(comparison, floor1, floor2)
            
            # Calculate overall similarity score
            comparison.calculate_similarity_score()
            
            # Store comparison
            comparison_id = str(uuid4())
            self.comparisons[comparison_id] = comparison
            
            # Add to floor comparison lists
            floor1.comparisons.append(comparison)
            floor2.comparisons.append(comparison)
            
            self.logger.info(f"Compared floors {request.floor_id_1} and {request.floor_id_2} with similarity {comparison.similarity_score:.2f}")
            
            return FloorComparisonResponse(
                comparison=comparison,
                differences_summary={
                    'total_differences': len(comparison.differences),
                    'added_objects': len(comparison.added_objects),
                    'removed_objects': len(comparison.removed_objects),
                    'modified_objects': len(comparison.modified_objects)
                },
                similarity_breakdown={
                    'layout_similarity': comparison.layout_similarity,
                    'object_similarity': comparison.object_similarity,
                    'route_similarity': comparison.route_similarity,
                    'grid_alignment': comparison.grid_alignment_score
                },
                recommendations=await self._generate_comparison_recommendations(comparison)
            )
            
        except Exception as e:
            self.logger.error(f"Error comparing floors {request.floor_id_1} and {request.floor_id_2}: {e}")
            raise
    
    # ============================================================================
    # ROUTE MANAGEMENT
    # ============================================================================
    
    async def create_route(self, request: RouteCreateRequest) -> RouteResponse:
        """Create a new route"""
        try:
            floor = self.floors.get(request.floor_id)
            if not floor:
                raise ValueError(f"Floor {request.floor_id} not found")
            
            # Create route
            route = Route(
                id=str(uuid4()),
                name=request.name,
                description=request.description,
                floor_id=request.floor_id,
                building_id=request.building_id,
                type=request.type,
                category=request.category,
                priority=request.priority,
                geometry=request.geometry,
                start_point=request.geometry.points[0],
                end_point=request.geometry.points[-1],
                is_public=request.is_public,
                constraints=request.constraints,
                requirements=request.requirements,
                tags=request.tags,
                created_by=request.created_by if hasattr(request, 'created_by') else None
            )
            
            # Calculate route metrics
            route.update_metrics()
            
            # Validate route
            validation_errors = route.validate_route()
            if validation_errors:
                route.validation_errors = validation_errors
                route.validation_status = "invalid"
            else:
                route.validation_status = "validated"
            
            # Store route
            if request.floor_id not in self.routes:
                self.routes[request.floor_id] = []
            self.routes[request.floor_id].append(route)
            self.performance_metrics['total_routes'] += 1
            
            self.logger.info(f"Created route {route.id} on floor {request.floor_id}")
            
            return RouteResponse(
                route=route,
                validation_errors=validation_errors
            )
            
        except Exception as e:
            self.logger.error(f"Error creating route: {e}")
            raise
    
    async def get_routes(self, floor_id: str, filters: Optional[Dict[str, Any]] = None) -> RouteListResponse:
        """Get routes for a floor"""
        try:
            routes = self.routes.get(floor_id, [])
            
            # Apply filters
            if filters:
                if filters.get('type'):
                    routes = [r for r in routes if r.type == filters['type']]
                if filters.get('is_active') is not None:
                    routes = [r for r in routes if r.is_active == filters['is_active']]
                if filters.get('priority'):
                    routes = [r for r in routes if r.priority == filters['priority']]
            
            return RouteListResponse(
                routes=routes,
                total_count=len(routes),
                filters=filters
            )
            
        except Exception as e:
            self.logger.error(f"Error getting routes for floor {floor_id}: {e}")
            return RouteListResponse(routes=[], total_count=0)
    
    async def update_route(self, route_id: str, request: RouteUpdateRequest) -> Optional[RouteResponse]:
        """Update an existing route"""
        try:
            # Find route
            route = None
            floor_id = None
            for fid, floor_routes in self.routes.items():
                for r in floor_routes:
                    if r.id == route_id:
                        route = r
                        floor_id = fid
                        break
                if route:
                    break
            
            if not route:
                return None
            
            # Update route fields
            for field, value in request.dict(exclude_unset=True).items():
                if hasattr(route, field):
                    setattr(route, field, value)
            
            # Update geometry if provided
            if request.geometry:
                route.geometry = request.geometry
                route.start_point = request.geometry.points[0]
                route.end_point = request.geometry.points[-1]
            
            # Update metrics
            route.update_metrics()
            route.updated_at = datetime.utcnow()
            
            # Revalidate
            validation_errors = route.validate_route()
            if validation_errors:
                route.validation_errors = validation_errors
                route.validation_status = "invalid"
            else:
                route.validation_status = "validated"
                route.validation_errors = []
            
            self.logger.info(f"Updated route {route_id}")
            
            return RouteResponse(
                route=route,
                validation_errors=validation_errors
            )
            
        except Exception as e:
            self.logger.error(f"Error updating route {route_id}: {e}")
            return None
    
    async def delete_route(self, route_id: str) -> bool:
        """Delete a route"""
        try:
            # Find and remove route
            for floor_id, floor_routes in self.routes.items():
                for i, route in enumerate(floor_routes):
                    if route.id == route_id:
                        del floor_routes[i]
                        self.performance_metrics['total_routes'] -= 1
                        self.logger.info(f"Deleted route {route_id}")
                        return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error deleting route {route_id}: {e}")
            return False
    
    # ============================================================================
    # FLOOR DASHBOARD
    # ============================================================================
    
    async def get_floor_dashboard(self, floor_id: str) -> FloorDashboardResponse:
        """Get comprehensive dashboard data for a floor"""
        try:
            floor = self.floors.get(floor_id)
            if not floor:
                raise ValueError(f"Floor {floor_id} not found")
            
            analytics = self.floor_analytics.get(floor_id)
            grid_calibration = self.grid_calibrations.get(floor_id)
            
            # Get recent comparisons
            recent_comparisons = floor.comparisons[-5:] if floor.comparisons else []
            
            # Calculate performance metrics
            performance_metrics = await self._calculate_floor_performance_metrics(floor_id)
            
            # Calculate quality indicators
            quality_indicators = await self._calculate_quality_indicators(floor)
            
            # Generate recommendations
            recommendations = await self._generate_floor_recommendations(floor, analytics)
            
            # Calculate trends
            trends = await self._calculate_floor_trends(floor_id)
            
            return FloorDashboardResponse(
                floor_id=floor_id,
                analytics=analytics,
                grid_calibration=grid_calibration,
                recent_comparisons=recent_comparisons,
                performance_metrics=performance_metrics,
                quality_indicators=quality_indicators,
                recommendations=recommendations,
                trends=trends
            )
            
        except Exception as e:
            self.logger.error(f"Error getting dashboard for floor {floor_id}: {e}")
            raise
    
    # ============================================================================
    # PRIVATE HELPER METHODS
    # ============================================================================
    
    async def _validate_floor(self, floor: EnhancedFloor) -> List[str]:
        """Validate a floor"""
        errors = []
        
        # Check required fields
        if not floor.name.strip():
            errors.append("Floor name is required")
        
        if not floor.svg_path or not os.path.exists(floor.svg_path):
            errors.append("SVG file path is invalid or file does not exist")
        
        # Check floor number uniqueness within building
        if floor.floor_number:
            for other_floor in self.floors.values():
                if (other_floor.id != floor.id and 
                    other_floor.building_id == floor.building_id and 
                    other_floor.floor_number == floor.floor_number):
                    errors.append(f"Floor number {floor.floor_number} already exists in building {floor.building_id}")
                    break
        
        return errors
    
    async def _validate_grid_calibration(self, calibration: GridCalibration) -> List[str]:
        """Validate grid calibration"""
        errors = []
        
        if len(calibration.calibration_points) < 3:
            errors.append("At least 3 calibration points are required")
        
        if len(calibration.reference_points) < 2:
            errors.append("At least 2 reference points are required")
        
        if calibration.grid_size <= 0:
            errors.append("Grid size must be positive")
        
        if calibration.calibration_accuracy < 0.5:
            errors.append("Calibration accuracy is too low")
        
        return errors
    
    async def _update_floor_quality_score(self, floor: EnhancedFloor):
        """Update floor quality score"""
        score = 0.0
        factors = 0
        
        # Validation status (30%)
        if floor.validation_status == "validated":
            score += 30
        elif floor.validation_status == "warning":
            score += 20
        factors += 30
        
        # Grid calibration (25%)
        if floor.grid_calibration and floor.grid_calibration.is_valid:
            score += floor.grid_calibration.calibration_accuracy * 25
        factors += 25
        
        # Analytics completeness (20%)
        analytics = self.floor_analytics.get(floor.id)
        if analytics:
            completeness = (analytics.data_completeness + analytics.data_accuracy) / 2
            score += completeness * 0.2
        factors += 20
        
        # Route coverage (15%)
        routes = self.routes.get(floor.id, [])
        if routes:
            route_score = min(len(routes) / 10.0, 1.0) * 15  # Cap at 10 routes
            score += route_score
        factors += 15
        
        # Metadata completeness (10%)
        metadata_score = 0
        if floor.description:
            metadata_score += 3
        if floor.tags:
            metadata_score += 3
        if floor.properties:
            metadata_score += 4
        score += metadata_score
        factors += 10
        
        floor.quality_score = (score / factors) * 100
    
    async def _calculate_analytics_trends(self, analytics: FloorAnalytics, date_range: Optional[Tuple[datetime, datetime]] = None) -> Dict[str, Any]:
        """Calculate analytics trends"""
        trends = {
            'usage_trend': 'stable',
            'performance_trend': 'stable',
            'growth_rate': 0.0
        }
        
        # Calculate usage trend
        if analytics.daily_usage:
            recent_usage = sum(analytics.daily_usage.values())
            if recent_usage > analytics.total_views * 0.1:  # More than 10% of total views in recent days
                trends['usage_trend'] = 'increasing'
            elif recent_usage < analytics.total_views * 0.05:  # Less than 5% of total views in recent days
                trends['usage_trend'] = 'decreasing'
        
        # Calculate performance trend
        if analytics.render_performance > 80:
            trends['performance_trend'] = 'improving'
        elif analytics.render_performance < 50:
            trends['performance_trend'] = 'declining'
        
        # Calculate growth rate
        if analytics.monthly_growth > 5:
            trends['growth_rate'] = analytics.monthly_growth
        
        return trends
    
    async def _generate_analytics_recommendations(self, analytics: FloorAnalytics) -> List[str]:
        """Generate recommendations based on analytics"""
        recommendations = []
        
        if analytics.render_performance < 70:
            recommendations.append("Consider optimizing floor rendering performance")
        
        if analytics.data_completeness < 80:
            recommendations.append("Add more metadata to improve data completeness")
        
        if analytics.total_views < 10:
            recommendations.append("Consider promoting floor visibility to increase usage")
        
        if analytics.average_rating < 3.0:
            recommendations.append("Review floor quality and user feedback")
        
        return recommendations
    
    async def _calculate_performance_indicators(self, analytics: FloorAnalytics) -> Dict[str, float]:
        """Calculate performance indicators"""
        return {
            'overall_score': analytics.calculate_overall_score(),
            'performance_index': (analytics.render_performance + analytics.interaction_responsiveness) / 2,
            'quality_index': (analytics.data_completeness + analytics.data_accuracy) / 2,
            'engagement_index': analytics.average_rating * analytics.total_views / 100
        }
    
    async def _compare_layouts(self, comparison: FloorComparison, floor1: EnhancedFloor, floor2: EnhancedFloor):
        """Compare floor layouts"""
        # This would implement layout comparison logic
        # For now, use a simple similarity based on floor properties
        similarity = 0.0
        factors = 0
        
        if floor1.floor_type == floor2.floor_type:
            similarity += 0.3
        factors += 0.3
        
        if floor1.floor_area and floor2.floor_area:
            area_diff = abs(floor1.floor_area - floor2.floor_area) / max(floor1.floor_area, floor2.floor_area)
            similarity += (1 - area_diff) * 0.4
        factors += 0.4
        
        if floor1.tags and floor2.tags:
            common_tags = set(floor1.tags) & set(floor2.tags)
            tag_similarity = len(common_tags) / max(len(floor1.tags), len(floor2.tags))
            similarity += tag_similarity * 0.3
        factors += 0.3
        
        comparison.layout_similarity = similarity / factors if factors > 0 else 0.0
    
    async def _compare_objects(self, comparison: FloorComparison, floor1: EnhancedFloor, floor2: EnhancedFloor):
        """Compare floor objects"""
        # This would implement object comparison logic
        # For now, use a placeholder
        comparison.object_similarity = 0.8
        comparison.added_objects = ["obj1", "obj2"]
        comparison.removed_objects = ["obj3"]
        comparison.modified_objects = ["obj4"]
    
    async def _compare_routes(self, comparison: FloorComparison, floor1: EnhancedFloor, floor2: EnhancedFloor):
        """Compare floor routes"""
        routes1 = self.routes.get(floor1.id, [])
        routes2 = self.routes.get(floor2.id, [])
        
        if not routes1 and not routes2:
            comparison.route_similarity = 1.0
            return
        
        if not routes1 or not routes2:
            comparison.route_similarity = 0.0
            return
        
        # Simple route count comparison
        route_count_diff = abs(len(routes1) - len(routes2))
        max_routes = max(len(routes1), len(routes2))
        comparison.route_similarity = 1.0 - (route_count_diff / max_routes)
    
    async def _compare_comprehensive(self, comparison: FloorComparison, floor1: EnhancedFloor, floor2: EnhancedFloor):
        """Perform comprehensive floor comparison"""
        await self._compare_layouts(comparison, floor1, floor2)
        await self._compare_objects(comparison, floor1, floor2)
        await self._compare_routes(comparison, floor1, floor2)
    
    async def _calculate_grid_alignment(self, comparison: FloorComparison, floor1: EnhancedFloor, floor2: EnhancedFloor):
        """Calculate grid alignment between floors"""
        cal1 = self.grid_calibrations.get(floor1.id)
        cal2 = self.grid_calibrations.get(floor2.id)
        
        if not cal1 or not cal2:
            comparison.grid_alignment_score = 0.0
            return
        
        # Calculate alignment based on grid parameters
        grid_size_diff = abs(cal1.grid_size - cal2.grid_size) / max(cal1.grid_size, cal2.grid_size)
        rotation_diff = abs(cal1.grid_rotation - cal2.grid_rotation) / 360.0
        
        alignment_score = 1.0 - (grid_size_diff + rotation_diff) / 2.0
        comparison.grid_alignment_score = max(0.0, alignment_score)
    
    async def _generate_comparison_recommendations(self, comparison: FloorComparison) -> List[str]:
        """Generate recommendations based on comparison results"""
        recommendations = []
        
        if comparison.similarity_score < 0.5:
            recommendations.append("Floors are significantly different - consider if they should be merged")
        
        if comparison.layout_similarity < 0.7:
            recommendations.append("Layout differences detected - review floor layouts for consistency")
        
        if comparison.grid_alignment_score < 0.8:
            recommendations.append("Grid alignment issues detected - consider recalibrating grids")
        
        return recommendations
    
    async def _calculate_floor_performance_metrics(self, floor_id: str) -> Dict[str, float]:
        """Calculate performance metrics for a floor"""
        routes = self.routes.get(floor_id, [])
        analytics = self.floor_analytics.get(floor_id)
        
        metrics = {
            'route_count': len(routes),
            'active_routes': len([r for r in routes if r.is_active]),
            'average_route_performance': 0.0,
            'floor_usage': analytics.total_views if analytics else 0,
            'data_quality': analytics.data_completeness if analytics else 0.0
        }
        
        if routes:
            performance_scores = [r.performance_score for r in routes if r.performance_score is not None]
            if performance_scores:
                metrics['average_route_performance'] = sum(performance_scores) / len(performance_scores)
        
        return metrics
    
    async def _calculate_quality_indicators(self, floor: EnhancedFloor) -> Dict[str, float]:
        """Calculate quality indicators for a floor"""
        return {
            'overall_quality': floor.quality_score,
            'validation_score': 100.0 if floor.validation_status == "validated" else 50.0,
            'grid_quality': floor.grid_calibration.calibration_accuracy if floor.grid_calibration else 0.0,
            'metadata_completeness': len(floor.tags) * 10 + (1 if floor.description else 0) * 20
        }
    
    async def _generate_floor_recommendations(self, floor: EnhancedFloor, analytics: Optional[FloorAnalytics]) -> List[str]:
        """Generate recommendations for a floor"""
        recommendations = []
        
        if floor.validation_status != "validated":
            recommendations.append("Fix validation errors to improve floor quality")
        
        if not floor.grid_calibration:
            recommendations.append("Add grid calibration for better spatial accuracy")
        
        if not floor.tags:
            recommendations.append("Add tags to improve floor categorization")
        
        if analytics and analytics.total_views < 5:
            recommendations.append("Consider promoting floor visibility")
        
        return recommendations
    
    async def _calculate_floor_trends(self, floor_id: str) -> Dict[str, Any]:
        """Calculate trends for a floor"""
        analytics = self.floor_analytics.get(floor_id)
        if not analytics:
            return {}
        
        return {
            'usage_trend': 'stable',
            'performance_trend': 'stable',
            'growth_rate': analytics.monthly_growth
        }
    
    async def _align_with_floors(self, calibration: GridCalibration, floor_ids: List[str]) -> Dict[str, Dict[str, Any]]:
        """Align grid with other floors"""
        results = {}
        
        for floor_id in floor_ids:
            other_calibration = self.grid_calibrations.get(floor_id)
            if other_calibration:
                # Calculate offset between grids
                offset_x = calibration.grid_origin[0] - other_calibration.grid_origin[0]
                offset_y = calibration.grid_origin[1] - other_calibration.grid_origin[1]
                offset_z = 0.0  # Assuming 2D for now
                
                calibration.alignment_offsets[floor_id] = (offset_x, offset_y, offset_z)
                
                results[floor_id] = {
                    'offset': (offset_x, offset_y, offset_z),
                    'alignment_score': 1.0 - abs(calibration.grid_size - other_calibration.grid_size) / max(calibration.grid_size, other_calibration.grid_size)
                }
        
        return results
    
    async def _load_floors_from_storage(self):
        """Load floors from persistent storage"""
        # This would implement loading from database or file storage
        # For now, start with empty state
        pass
    
    async def _save_floors_to_storage(self):
        """Save floors to persistent storage"""
        # This would implement saving to database or file storage
        # For now, just log
        self.logger.info("Saving floors to storage")
    
    async def _initialize_analytics(self):
        """Initialize analytics for existing floors"""
        for floor_id in self.floors:
            if floor_id not in self.floor_analytics:
                floor = self.floors[floor_id]
                analytics = FloorAnalytics(
                    id=str(uuid4()),
                    floor_id=floor_id,
                    building_id=floor.building_id
                )
                self.floor_analytics[floor_id] = analytics
    
    async def _validate_all_floors(self):
        """Validate all floors"""
        for floor in self.floors.values():
            validation_errors = await self._validate_floor(floor)
            if validation_errors:
                floor.validation_errors = validation_errors
                floor.validation_status = "invalid"
            else:
                floor.validation_status = "validated"
                floor.validation_errors = []
    
    async def _cache_floor(self, floor_id: str):
        """Cache floor data"""
        floor = self.floors.get(floor_id)
        if floor:
            cache_key = f"{self.cache_prefix}:floor:{floor_id}"
            await cache_service.set(cache_key, floor.dict(), expire=3600)
    
    async def _get_cached_floor(self, floor_id: str) -> Optional[EnhancedFloor]:
        """Get cached floor data"""
        cache_key = f"{self.cache_prefix}:floor:{floor_id}"
        cached_data = await cache_service.get(cache_key)
        if cached_data:
            return EnhancedFloor(**cached_data)
        return None
    
    async def _clear_floor_cache(self, floor_id: str):
        """Clear floor cache"""
        cache_key = f"{self.cache_prefix}:floor:{floor_id}"
        await cache_service.delete(cache_key)
    
    async def _cache_analytics(self, floor_id: str):
        """Cache analytics data"""
        analytics = self.floor_analytics.get(floor_id)
        if analytics:
            cache_key = f"{self.cache_prefix}:analytics:{floor_id}"
            await cache_service.set(cache_key, analytics.dict(), expire=1800)
    
    async def _save_analytics_to_storage(self):
        """Save analytics to persistent storage"""
        # This would implement saving analytics to database or file storage
        # For now, just log
        self.logger.info("Saving analytics to storage")

# Global floor manager instance
floor_manager = FloorManager() 