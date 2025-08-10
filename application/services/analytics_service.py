"""
Advanced Analytics Application Service.

Provides comprehensive analytics capabilities including real-time metrics,
historical analysis, predictive analytics, and custom report generation.
"""

from typing import Dict, Any, List, Optional, Union, Tuple
from datetime import datetime, timezone, timedelta
from dataclasses import asdict
from decimal import Decimal
import asyncio

from application.services.base_service import BaseApplicationService
from application.dto.analytics_dto import (
    AnalyticsRequest, AnalyticsResponse,
    DashboardMetricsResponse, ReportGenerationRequest, ReportGenerationResponse,
    CustomQueryRequest, CustomQueryResponse, TrendAnalysisRequest, TrendAnalysisResponse,
    PredictiveAnalyticsRequest, PredictiveAnalyticsResponse
)
from domain.entities.analytics_entity import (
    AnalyticsQuery, ReportTemplate, DashboardMetric,
    MetricType, AggregationType, TimeGranularity
)
from domain.value_objects import BuildingId, FloorId, RoomId, DeviceId, UserId
from domain.repositories import (
    BuildingRepository, FloorRepository, RoomRepository, DeviceRepository,
    AnalyticsRepository, ReportRepository, UnitOfWork
)
from domain.exceptions import AnalyticsError, ReportGenerationError, DataNotFoundError
from application.exceptions import ValidationError, PermissionDeniedError
from infrastructure.services.data_warehouse import DataWarehouseService
from infrastructure.services.reporting_engine import ReportingEngineService
from infrastructure.services.machine_learning import MLPredictionService
from infrastructure.logging.structured_logging import get_logger, log_context
from infrastructure.performance.monitoring import performance_monitor, monitor_performance
from infrastructure.security import require_permission, Permission


logger = get_logger(__name__)


class AnalyticsApplicationService(BaseApplicationService):
    """Advanced analytics service for comprehensive data analysis."""
    
    def __init__(self, unit_of_work: UnitOfWork,
                 data_warehouse: DataWarehouseService,
                 reporting_engine: ReportingEngineService,
                 ml_service: MLPredictionService,
                 cache_service=None, event_store=None, message_queue=None, metrics=None):
        super().__init__(unit_of_work, cache_service, event_store, message_queue, metrics)
        
        self.building_repository = unit_of_work.building_repository
        self.floor_repository = unit_of_work.floor_repository
        self.room_repository = unit_of_work.room_repository
        self.device_repository = unit_of_work.device_repository
        self.analytics_repository = unit_of_work.analytics_repository
        self.report_repository = unit_of_work.report_repository
        
        self.data_warehouse = data_warehouse
        self.reporting_engine = reporting_engine
        self.ml_service = ml_service
    
    @monitor_performance("dashboard_metrics")
    @require_permission(Permission.VIEW_ANALYTICS)
    def get_dashboard_metrics(self, user_id: str, time_range: str = "24h",
                            include_predictions: bool = False) -> DashboardMetricsResponse:
        """Get comprehensive dashboard metrics."""
        with log_context(operation="get_dashboard_metrics", user_id=user_id):
            try:
                # Parse time range
                end_time = datetime.now(timezone.utc)
                start_time = self._parse_time_range(time_range, end_time)
                
                # Check cache first
                cache_key = f"dashboard_metrics:{user_id}:{time_range}:{include_predictions}"
                if self.cache_service:
                    cached_metrics = self.cache_service.get(cache_key)
                    if cached_metrics:
                        return DashboardMetricsResponse.from_dict(cached_metrics)
                
                # Get building summary
                building_metrics = self._get_building_summary_metrics(start_time, end_time)
                
                # Get occupancy metrics
                occupancy_metrics = self._get_occupancy_metrics(start_time, end_time)
                
                # Get device health metrics
                device_metrics = self._get_device_health_metrics(start_time, end_time)
                
                # Get energy usage metrics
                energy_metrics = self._get_energy_usage_metrics(start_time, end_time)
                
                # Get space utilization metrics
                utilization_metrics = self._get_space_utilization_metrics(start_time, end_time)
                
                # Get environmental metrics
                environmental_metrics = self._get_environmental_metrics(start_time, end_time)
                
                # Get maintenance metrics
                maintenance_metrics = self._get_maintenance_metrics(start_time, end_time)
                
                # Get predictive insights if requested
                predictions = {}
                if include_predictions:
                    predictions = self._get_predictive_insights(start_time, end_time)
                
                # Get alerts and notifications
                alerts = self._get_active_alerts()
                
                # Calculate trends
                trends = self._calculate_metric_trends(start_time, end_time)
                
                dashboard_data = {
                    "time_range": {
                        "start": start_time.isoformat(),
                        "end": end_time.isoformat(),
                        "period": time_range
                    },
                    "summary": building_metrics,
                    "occupancy": occupancy_metrics,
                    "device_health": device_metrics,
                    "energy_usage": energy_metrics,
                    "space_utilization": utilization_metrics,
                    "environmental": environmental_metrics,
                    "maintenance": maintenance_metrics,
                    "alerts": alerts,
                    "trends": trends,
                    "predictions": predictions if include_predictions else {},
                    "generated_at": datetime.now(timezone.utc).isoformat()
                }
                
                # Cache results
                if self.cache_service:
                    self.cache_service.set(cache_key, asdict(dashboard_data), ttl=300)  # 5 minutes
                
                # Record metrics
                if self.metrics:
                    self.metrics.increment_counter(
                        "dashboard_metrics_generated",
                        {"user_id": user_id, "include_predictions": str(include_predictions)}
                    )
                
                return DashboardMetricsResponse(
                    success=True,
                    data=dashboard_data
                )
                
            except Exception as e:
                logger.error(f"Dashboard metrics generation failed: {e}")
                return DashboardMetricsResponse(
                    success=False,
                    message="Failed to generate dashboard metrics",
                    data={}
                )
    
    @monitor_performance("custom_analytics")
    @require_permission(Permission.VIEW_ANALYTICS)
    def execute_custom_query(self, request: CustomQueryRequest, user_id: str) -> CustomQueryResponse:
        """Execute custom analytics query."""
        with log_context(operation="custom_analytics", user_id=user_id):
            try:
                # Validate query request
                self._validate_custom_query(request)
                
                # Build analytics query
                query = AnalyticsQuery(
                    metrics=request.metrics,
                    dimensions=request.dimensions,
                    filters=request.filters,
                    time_range=request.time_range,
                    aggregations=request.aggregations,
                    granularity=TimeGranularity(request.granularity)
                )
                
                # Execute query through data warehouse
                query_result = self.data_warehouse.execute_analytics_query(query)
                
                # Process results
                processed_results = self._process_query_results(query_result, request)
                
                # Generate visualizations if requested
                visualizations = {}
                if request.include_visualizations:
                    visualizations = self._generate_visualizations(processed_results, request)
                
                # Calculate statistical insights
                insights = self._calculate_statistical_insights(processed_results)
                
                # Record metrics
                if self.metrics:
                    self.metrics.increment_counter(
                        "custom_queries_executed",
                        {"user_id": user_id, "metric_count": str(len(request.metrics))}
                    )
                
                return CustomQueryResponse(
                    success=True,
                    data={
                        "query": asdict(query),
                        "results": processed_results,
                        "visualizations": visualizations,
                        "insights": insights,
                        "execution_time_ms": query_result.get("execution_time_ms", 0),
                        "row_count": len(processed_results.get("data", []))
                    }
                )
                
            except ValidationError as e:
                logger.warning(f"Custom query validation failed: {e}")
                return CustomQueryResponse(
                    success=False,
                    message=f"Query validation failed: {str(e)}",
                    data={}
                )
            except Exception as e:
                logger.error(f"Custom query execution failed: {e}")
                return CustomQueryResponse(
                    success=False,
                    message="Custom query execution failed",
                    data={}
                )
    
    @monitor_performance("trend_analysis")
    @require_permission(Permission.VIEW_ANALYTICS)
    def analyze_trends(self, request: TrendAnalysisRequest, user_id: str) -> TrendAnalysisResponse:
        """Perform comprehensive trend analysis."""
        with log_context(operation="trend_analysis", user_id=user_id):
            try:
                # Validate request
                if not request.metrics or not request.time_range:
                    raise ValidationError("Metrics and time range are required for trend analysis")
                
                # Parse time range
                end_time = datetime.now(timezone.utc)
                start_time = self._parse_time_range(request.time_range.get("period", "30d"), end_time)
                
                trends_data = {}
                
                # Analyze each metric
                for metric in request.metrics:
                    metric_trends = self._analyze_metric_trend(
                        metric=metric,
                        start_time=start_time,
                        end_time=end_time,
                        entities=request.entities,
                        granularity=request.granularity
                    )
                    trends_data[metric] = metric_trends
                
                # Detect anomalies
                anomalies = self._detect_trend_anomalies(trends_data, request)
                
                # Generate forecasts if ML service is available
                forecasts = {}
                if request.include_forecasts and self.ml_service:
                    forecasts = self._generate_trend_forecasts(trends_data, request)
                
                # Calculate correlation analysis
                correlations = self._calculate_trend_correlations(trends_data, request)
                
                # Generate insights
                insights = self._generate_trend_insights(trends_data, anomalies, correlations)
                
                return TrendAnalysisResponse(
                    success=True,
                    data={
                        "time_range": {
                            "start": start_time.isoformat(),
                            "end": end_time.isoformat(),
                            "period": request.time_range.get("period", "30d")
                        },
                        "metrics": list(request.metrics),
                        "trends": trends_data,
                        "anomalies": anomalies,
                        "forecasts": forecasts,
                        "correlations": correlations,
                        "insights": insights,
                        "analysis_date": datetime.now(timezone.utc).isoformat()
                    }
                )
                
            except Exception as e:
                logger.error(f"Trend analysis failed: {e}")
                return TrendAnalysisResponse(
                    success=False,
                    message="Trend analysis failed",
                    data={}
                )
    
    @monitor_performance("predictive_analytics")
    @require_permission(Permission.VIEW_ANALYTICS)
    def generate_predictions(self, request: PredictiveAnalyticsRequest, 
                           user_id: str) -> PredictiveAnalyticsResponse:
        """Generate predictive analytics insights."""
        with log_context(operation="predictive_analytics", user_id=user_id):
            try:
                if not self.ml_service:
                    raise AnalyticsError("Machine learning service not available")
                
                # Validate request
                if not request.prediction_types:
                    raise ValidationError("Prediction types are required")
                
                predictions = {}
                
                # Generate different types of predictions
                for prediction_type in request.prediction_types:
                    if prediction_type == "energy_usage":
                        predictions["energy_usage"] = self._predict_energy_usage(request)
                    elif prediction_type == "occupancy":
                        predictions["occupancy"] = self._predict_occupancy(request)
                    elif prediction_type == "maintenance":
                        predictions["maintenance"] = self._predict_maintenance_needs(request)
                    elif prediction_type == "equipment_failure":
                        predictions["equipment_failure"] = self._predict_equipment_failures(request)
                    elif prediction_type == "space_demand":
                        predictions["space_demand"] = self._predict_space_demand(request)
                
                # Calculate confidence intervals
                confidence_analysis = self._calculate_prediction_confidence(predictions)
                
                # Generate recommendations based on predictions
                recommendations = self._generate_prediction_recommendations(predictions, request)
                
                # Calculate potential impacts
                impact_analysis = self._calculate_prediction_impacts(predictions, request)
                
                return PredictiveAnalyticsResponse(
                    success=True,
                    data={
                        "predictions": predictions,
                        "confidence_analysis": confidence_analysis,
                        "recommendations": recommendations,
                        "impact_analysis": impact_analysis,
                        "model_info": {
                            "models_used": list(predictions.keys()),
                            "prediction_horizon": request.time_horizon,
                            "generated_at": datetime.now(timezone.utc).isoformat()
                        }
                    }
                )
                
            except Exception as e:
                logger.error(f"Predictive analytics failed: {e}")
                return PredictiveAnalyticsResponse(
                    success=False,
                    message="Predictive analytics generation failed",
                    data={}
                )
    
    @monitor_performance("report_generation")
    @require_permission(Permission.GENERATE_REPORTS)
    def generate_report(self, request: ReportGenerationRequest, 
                       user_id: str) -> ReportGenerationResponse:
        """Generate comprehensive reports."""
        with log_context(operation="report_generation", user_id=user_id, report_type=request.report_type):
            try:
                # Validate request
                if not request.report_type:
                    raise ValidationError("Report type is required")
                
                # Get or create report template
                template = self._get_report_template(request.report_type, request.template_options)
                
                # Gather data for report
                report_data = self._gather_report_data(request, template)
                
                # Generate report using reporting engine
                report_result = self.reporting_engine.generate_report(
                    template=template,
                    data=report_data,
                    format=request.format,
                    options=request.options
                )
                
                # Save report metadata
                report_metadata = {
                    "id": report_result["report_id"],
                    "type": request.report_type,
                    "format": request.format,
                    "generated_by": user_id,
                    "generated_at": datetime.now(timezone.utc).isoformat(),
                    "parameters": request.parameters,
                    "file_size": report_result.get("file_size", 0),
                    "page_count": report_result.get("page_count", 1)
                }
                
                # Store report metadata
                with self.unit_of_work:
                    self.report_repository.save_report_metadata(report_metadata)
                    self.unit_of_work.commit()
                
                # Schedule delivery if requested
                if request.delivery_options:
                    self._schedule_report_delivery(report_result, request.delivery_options)
                
                # Record metrics
                if self.metrics:
                    self.metrics.increment_counter(
                        "reports_generated",
                        {"type": request.report_type, "format": request.format, "user_id": user_id}
                    )
                
                return ReportGenerationResponse(
                    success=True,
                    report_id=report_result["report_id"],
                    download_url=report_result.get("download_url"),
                    metadata=report_metadata,
                    message="Report generated successfully"
                )
                
            except Exception as e:
                logger.error(f"Report generation failed: {e}")
                return ReportGenerationResponse(
                    success=False,
                    message="Report generation failed"
                )
    
    def _parse_time_range(self, time_range: str, end_time: datetime) -> datetime:
        """Parse time range string to start datetime."""
        if time_range == "1h":
            return end_time - timedelta(hours=1)
        elif time_range == "24h":
            return end_time - timedelta(hours=24)
        elif time_range == "7d":
            return end_time - timedelta(days=7)
        elif time_range == "30d":
            return end_time - timedelta(days=30)
        elif time_range == "90d":
            return end_time - timedelta(days=90)
        else:
            return end_time - timedelta(hours=24)  # Default
    
    def _get_building_summary_metrics(self, start_time: datetime, end_time: datetime) -> Dict[str, Any]:
        """Get building summary metrics."""
        total_buildings = self.building_repository.count()
        operational_buildings = self.building_repository.count_by_status("operational")
        maintenance_buildings = self.building_repository.count_by_status("maintenance")
        
        # Get total counts
        total_floors = self.floor_repository.count()
        total_rooms = self.room_repository.count()
        total_devices = self.device_repository.count()
        
        return {
            "total_buildings": total_buildings,
            "operational_buildings": operational_buildings,
            "maintenance_buildings": maintenance_buildings,
            "total_floors": total_floors,
            "total_rooms": total_rooms,
            "total_devices": total_devices,
            "building_utilization_rate": (operational_buildings / total_buildings * 100) if total_buildings > 0 else 0
        }
    
    def _get_occupancy_metrics(self, start_time: datetime, end_time: datetime) -> Dict[str, Any]:
        """Get occupancy metrics."""
        # Get current occupancy data
        current_occupancy = self.data_warehouse.get_current_occupancy()
        
        # Calculate occupancy trends
        occupancy_trend = self.data_warehouse.get_occupancy_trend(start_time, end_time)
        
        # Identify peak and low occupancy periods
        peak_hours = self.data_warehouse.get_peak_occupancy_hours()
        
        return {
            "current_occupancy_rate": current_occupancy.get("rate", 0),
            "current_occupied_rooms": current_occupancy.get("occupied_rooms", 0),
            "peak_occupancy_today": occupancy_trend.get("peak_today", 0),
            "average_occupancy": occupancy_trend.get("average", 0),
            "peak_hours": peak_hours,
            "low_occupancy_rooms": current_occupancy.get("low_occupancy_rooms", []),
            "occupancy_trend": occupancy_trend.get("direction", "stable")
        }
    
    def _get_device_health_metrics(self, start_time: datetime, end_time: datetime) -> Dict[str, Any]:
        """Get device health metrics."""
        device_health = self.data_warehouse.get_device_health_summary()
        
        return {
            "total_devices": device_health.get("total", 0),
            "operational_devices": device_health.get("operational", 0),
            "maintenance_required": device_health.get("maintenance_required", 0),
            "offline_devices": device_health.get("offline", 0),
            "error_devices": device_health.get("error", 0),
            "overall_health_score": device_health.get("health_score", 0),
            "devices_by_type": device_health.get("by_type", {}),
            "critical_issues": device_health.get("critical_issues", [])
        }
    
    def _get_energy_usage_metrics(self, start_time: datetime, end_time: datetime) -> Dict[str, Any]:
        """Get energy usage metrics."""
        energy_data = self.data_warehouse.get_energy_usage_summary(start_time, end_time)
        
        return {
            "total_consumption_kwh": energy_data.get("total_kwh", 0),
            "average_daily_usage": energy_data.get("avg_daily", 0),
            "peak_demand_kw": energy_data.get("peak_demand", 0),
            "energy_cost": energy_data.get("cost", 0),
            "efficiency_score": energy_data.get("efficiency_score", 0),
            "consumption_by_category": energy_data.get("by_category", {}),
            "top_consumers": energy_data.get("top_consumers", []),
            "savings_opportunities": energy_data.get("savings_opportunities", [])
        }
    
    def _get_space_utilization_metrics(self, start_time: datetime, end_time: datetime) -> Dict[str, Any]:
        """Get space utilization metrics."""
        utilization_data = self.data_warehouse.get_space_utilization_summary(start_time, end_time)
        
        return {
            "overall_utilization_rate": utilization_data.get("overall_rate", 0),
            "underutilized_spaces": utilization_data.get("underutilized", []),
            "overutilized_spaces": utilization_data.get("overutilized", []),
            "utilization_by_building": utilization_data.get("by_building", {}),
            "utilization_by_room_type": utilization_data.get("by_room_type", {}),
            "optimization_recommendations": utilization_data.get("recommendations", [])
        }
    
    def _get_environmental_metrics(self, start_time: datetime, end_time: datetime) -> Dict[str, Any]:
        """Get environmental metrics."""
        env_data = self.data_warehouse.get_environmental_summary(start_time, end_time)
        
        return {
            "average_temperature": env_data.get("avg_temperature", 0),
            "average_humidity": env_data.get("avg_humidity", 0),
            "air_quality_index": env_data.get("air_quality", 0),
            "co2_levels": env_data.get("co2_levels", 0),
            "comfort_score": env_data.get("comfort_score", 0),
            "environmental_alerts": env_data.get("alerts", []),
            "trend_analysis": env_data.get("trends", {})
        }
    
    def _get_maintenance_metrics(self, start_time: datetime, end_time: datetime) -> Dict[str, Any]:
        """Get maintenance metrics."""
        maintenance_data = self.data_warehouse.get_maintenance_summary(start_time, end_time)
        
        return {
            "scheduled_maintenance": maintenance_data.get("scheduled", 0),
            "completed_maintenance": maintenance_data.get("completed", 0),
            "overdue_maintenance": maintenance_data.get("overdue", 0),
            "maintenance_cost": maintenance_data.get("cost", 0),
            "mtbf_average": maintenance_data.get("mtbf", 0),  # Mean Time Between Failures
            "maintenance_efficiency": maintenance_data.get("efficiency", 0),
            "upcoming_maintenance": maintenance_data.get("upcoming", [])
        }
    
    def _get_active_alerts(self) -> List[Dict[str, Any]]:
        """Get active system alerts."""
        return self.data_warehouse.get_active_alerts()
    
    def _calculate_metric_trends(self, start_time: datetime, end_time: datetime) -> Dict[str, Any]:
        """Calculate trends for key metrics."""
        return self.data_warehouse.calculate_trends(start_time, end_time)
    
    def _get_predictive_insights(self, start_time: datetime, end_time: datetime) -> Dict[str, Any]:
        """Get predictive insights using ML models."""
        if not self.ml_service:
            return {}
        
        return {
            "energy_forecast": self.ml_service.predict_energy_usage(7),  # 7 days
            "maintenance_predictions": self.ml_service.predict_maintenance_needs(),
            "occupancy_forecast": self.ml_service.predict_occupancy(24)  # 24 hours
        }
    
    def _validate_custom_query(self, request: CustomQueryRequest) -> None:
        """Validate custom query request."""
        if not request.metrics:
            raise ValidationError("At least one metric is required")
        
        if request.time_range and request.time_range.get("start") and request.time_range.get("end"):
            start = datetime.fromisoformat(request.time_range["start"])
            end = datetime.fromisoformat(request.time_range["end"])
            if start >= end:
                raise ValidationError("Start time must be before end time")
    
    def _process_query_results(self, query_result: Dict[str, Any], 
                             request: CustomQueryRequest) -> Dict[str, Any]:
        """Process and format query results."""
        # Transform raw results into structured format
        processed_data = {
            "columns": query_result.get("columns", []),
            "data": query_result.get("rows", []),
            "summary": self._calculate_result_summary(query_result),
            "metadata": {
                "row_count": len(query_result.get("rows", [])),
                "execution_time_ms": query_result.get("execution_time_ms", 0),
                "query_hash": query_result.get("query_hash", "")
            }
        }
        
        return processed_data
    
    def _calculate_result_summary(self, query_result: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate summary statistics for query results."""
        rows = query_result.get("rows", [])
        if not rows:
            return {}
        
        # Calculate basic statistics
        summary = {
            "total_rows": len(rows),
            "numeric_summaries": {}
        }
        
        # For each numeric column, calculate summary stats
        columns = query_result.get("columns", [])
        for i, column in enumerate(columns):
            try:
                values = [float(row[i]) for row in rows if row[i] is not None and str(row[i]).replace('.', '').replace('-', '').isdigit()]
                if values:
                    summary["numeric_summaries"][column] = {
                        "count": len(values),
                        "sum": sum(values),
                        "average": sum(values) / len(values),
                        "min": min(values),
                        "max": max(values)
                    }
            except (ValueError, IndexError):
                continue
        
        return summary
    
    def _generate_visualizations(self, results: Dict[str, Any], 
                               request: CustomQueryRequest) -> Dict[str, Any]:
        """Generate visualization configurations for results."""
        visualizations = {}
        
        # Generate chart configurations based on data structure
        data = results.get("data", [])
        columns = results.get("columns", [])
        
        if len(columns) >= 2 and data:
            # Time series visualization
            if any("time" in col.lower() or "date" in col.lower() for col in columns):
                visualizations["time_series"] = {
                    "type": "line_chart",
                    "x_axis": next(col for col in columns if "time" in col.lower() or "date" in col.lower()),
                    "y_axes": [col for col in columns if col not in [visualizations.get("time_series", {}).get("x_axis")]],
                    "config": {"responsive": True, "show_legend": True}
                }
            
            # Bar chart for categorical data
            if len(columns) == 2:
                visualizations["bar_chart"] = {
                    "type": "bar_chart",
                    "x_axis": columns[0],
                    "y_axis": columns[1],
                    "config": {"horizontal": False, "show_values": True}
                }
        
        return visualizations
    
    def _calculate_statistical_insights(self, results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Calculate statistical insights from results."""
        insights = []
        summary = results.get("summary", {})
        numeric_summaries = summary.get("numeric_summaries", {})
        
        for column, stats in numeric_summaries.items():
            if stats["count"] > 0:
                # Calculate insights
                range_value = stats["max"] - stats["min"]
                if stats["average"] != 0:
                    coefficient_of_variation = (range_value / 2) / stats["average"]
                    
                    if coefficient_of_variation > 0.5:
                        insights.append({
                            "type": "high_variability",
                            "metric": column,
                            "message": f"{column} shows high variability (CV: {coefficient_of_variation:.2f})",
                            "severity": "info"
                        })
                
                # Detect outliers (simple approach)
                if range_value > stats["average"] * 3:
                    insights.append({
                        "type": "potential_outliers",
                        "metric": column,
                        "message": f"{column} may contain outliers (range is {range_value:.2f}, average is {stats['average']:.2f})",
                        "severity": "warning"
                    })
        
        return insights
    
    def _analyze_metric_trend(self, metric: str, start_time: datetime, end_time: datetime,
                            entities: Optional[List[str]], granularity: str) -> Dict[str, Any]:
        """Analyze trend for a specific metric."""
        trend_data = self.data_warehouse.get_metric_trend(
            metric=metric,
            start_time=start_time,
            end_time=end_time,
            entities=entities,
            granularity=granularity
        )
        
        # Calculate trend direction and strength
        values = trend_data.get("values", [])
        if len(values) >= 2:
            first_half_avg = sum(values[:len(values)//2]) / (len(values)//2)
            second_half_avg = sum(values[len(values)//2:]) / (len(values) - len(values)//2)
            
            trend_direction = "increasing" if second_half_avg > first_half_avg else "decreasing"
            trend_strength = abs(second_half_avg - first_half_avg) / first_half_avg if first_half_avg != 0 else 0
        else:
            trend_direction = "stable"
            trend_strength = 0
        
        return {
            "data": trend_data,
            "direction": trend_direction,
            "strength": trend_strength,
            "summary": {
                "min": min(values) if values else 0,
                "max": max(values) if values else 0,
                "average": sum(values) / len(values) if values else 0
            }
        }
    
    def _detect_trend_anomalies(self, trends_data: Dict[str, Any], 
                              request: TrendAnalysisRequest) -> List[Dict[str, Any]]:
        """Detect anomalies in trend data."""
        anomalies = []
        
        for metric, trend_info in trends_data.items():
            values = trend_info.get("data", {}).get("values", [])
            if len(values) < 10:  # Need sufficient data for anomaly detection
                continue
            
            # Simple statistical anomaly detection
            mean_val = sum(values) / len(values)
            variance = sum((x - mean_val) ** 2 for x in values) / len(values)
            std_dev = variance ** 0.5
            
            threshold = 2 * std_dev  # 2 standard deviations
            
            for i, value in enumerate(values):
                if abs(value - mean_val) > threshold:
                    anomalies.append({
                        "metric": metric,
                        "timestamp_index": i,
                        "value": value,
                        "expected_range": [mean_val - threshold, mean_val + threshold],
                        "severity": "high" if abs(value - mean_val) > 3 * std_dev else "medium",
                        "type": "statistical_outlier"
                    })
        
        return anomalies
    
    def _generate_trend_forecasts(self, trends_data: Dict[str, Any], 
                                request: TrendAnalysisRequest) -> Dict[str, Any]:
        """Generate forecasts for trends using ML models."""
        forecasts = {}
        
        for metric, trend_info in trends_data.items():
            values = trend_info.get("data", {}).get("values", [])
            if len(values) >= 10:  # Need sufficient historical data
                try:
                    forecast = self.ml_service.forecast_metric(
                        metric=metric,
                        historical_values=values,
                        forecast_periods=request.forecast_periods or 7
                    )
                    forecasts[metric] = forecast
                except Exception as e:
                    logger.warning(f"Failed to generate forecast for {metric}: {e}")
                    continue
        
        return forecasts
    
    def _calculate_trend_correlations(self, trends_data: Dict[str, Any], 
                                    request: TrendAnalysisRequest) -> Dict[str, Any]:
        """Calculate correlations between different metrics."""
        correlations = {}
        metric_names = list(trends_data.keys())
        
        for i, metric1 in enumerate(metric_names):
            for metric2 in metric_names[i+1:]:
                values1 = trends_data[metric1].get("data", {}).get("values", [])
                values2 = trends_data[metric2].get("data", {}).get("values", [])
                
                if len(values1) == len(values2) and len(values1) > 1:
                    # Calculate Pearson correlation coefficient
                    correlation = self._calculate_correlation(values1, values2)
                    correlations[f"{metric1}_vs_{metric2}"] = {
                        "correlation": correlation,
                        "strength": self._classify_correlation_strength(correlation),
                        "direction": "positive" if correlation > 0 else "negative"
                    }
        
        return correlations
    
    def _calculate_correlation(self, values1: List[float], values2: List[float]) -> float:
        """Calculate Pearson correlation coefficient."""
        n = len(values1)
        if n == 0:
            return 0
        
        mean1 = sum(values1) / n
        mean2 = sum(values2) / n
        
        numerator = sum((values1[i] - mean1) * (values2[i] - mean2) for i in range(n))
        
        sum_sq1 = sum((val - mean1) ** 2 for val in values1)
        sum_sq2 = sum((val - mean2) ** 2 for val in values2)
        denominator = (sum_sq1 * sum_sq2) ** 0.5
        
        if denominator == 0:
            return 0
        
        return numerator / denominator
    
    def _classify_correlation_strength(self, correlation: float) -> str:
        """Classify correlation strength."""
        abs_corr = abs(correlation)
        if abs_corr >= 0.7:
            return "strong"
        elif abs_corr >= 0.3:
            return "moderate"
        else:
            return "weak"
    
    def _generate_trend_insights(self, trends_data: Dict[str, Any], anomalies: List[Dict[str, Any]],
                               correlations: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate actionable insights from trend analysis."""
        insights = []
        
        # Insights from trends
        for metric, trend_info in trends_data.items():
            direction = trend_info.get("direction", "stable")
            strength = trend_info.get("strength", 0)
            
            if direction != "stable" and strength > 0.1:
                insights.append({
                    "type": "trend",
                    "metric": metric,
                    "message": f"{metric} is {direction} with {strength:.1%} change",
                    "recommendation": self._get_trend_recommendation(metric, direction),
                    "priority": "high" if strength > 0.3 else "medium"
                })
        
        # Insights from anomalies
        high_severity_anomalies = [a for a in anomalies if a["severity"] == "high"]
        if high_severity_anomalies:
            insights.append({
                "type": "anomaly",
                "message": f"Detected {len(high_severity_anomalies)} high-severity anomalies",
                "affected_metrics": list(set(a["metric"] for a in high_severity_anomalies)),
                "recommendation": "Investigate anomalous values and their root causes",
                "priority": "high"
            })
        
        # Insights from correlations
        strong_correlations = [
            (pair, data) for pair, data in correlations.items() 
            if data["strength"] == "strong"
        ]
        if strong_correlations:
            insights.append({
                "type": "correlation",
                "message": f"Found {len(strong_correlations)} strong correlations between metrics",
                "correlations": strong_correlations,
                "recommendation": "Leverage correlated metrics for predictive modeling",
                "priority": "medium"
            })
        
        return insights
    
    def _get_trend_recommendation(self, metric: str, direction: str) -> str:
        """Get recommendation based on metric trend."""
        recommendations = {
            ("energy_usage", "increasing"): "Review energy efficiency measures and identify conservation opportunities",
            ("energy_usage", "decreasing"): "Continue current efficiency initiatives",
            ("occupancy", "increasing"): "Monitor space capacity and consider expansion",
            ("occupancy", "decreasing"): "Analyze utilization patterns and optimize space allocation",
            ("maintenance_cost", "increasing"): "Review maintenance schedules and consider preventive measures",
            ("device_failures", "increasing"): "Implement proactive monitoring and replacement schedules"
        }
        
        return recommendations.get((metric, direction), f"Monitor {metric} trends and adjust strategies accordingly")
    
    def _predict_energy_usage(self, request: PredictiveAnalyticsRequest) -> Dict[str, Any]:
        """Predict energy usage patterns."""
        return self.ml_service.predict_energy_usage(
            horizon_hours=request.time_horizon,
            entities=request.entities,
            include_weather=True
        )
    
    def _predict_occupancy(self, request: PredictiveAnalyticsRequest) -> Dict[str, Any]:
        """Predict occupancy patterns."""
        return self.ml_service.predict_occupancy(
            horizon_hours=request.time_horizon,
            entities=request.entities,
            include_events=True
        )
    
    def _predict_maintenance_needs(self, request: PredictiveAnalyticsRequest) -> Dict[str, Any]:
        """Predict maintenance requirements."""
        return self.ml_service.predict_maintenance_needs(
            horizon_days=request.time_horizon // 24,
            entities=request.entities
        )
    
    def _predict_equipment_failures(self, request: PredictiveAnalyticsRequest) -> Dict[str, Any]:
        """Predict equipment failure probabilities."""
        return self.ml_service.predict_equipment_failures(
            horizon_days=request.time_horizon // 24,
            entities=request.entities
        )
    
    def _predict_space_demand(self, request: PredictiveAnalyticsRequest) -> Dict[str, Any]:
        """Predict space demand patterns."""
        return self.ml_service.predict_space_demand(
            horizon_days=request.time_horizon // 24,
            entities=request.entities
        )
    
    def _calculate_prediction_confidence(self, predictions: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate confidence intervals for predictions."""
        confidence_analysis = {}
        
        for prediction_type, prediction_data in predictions.items():
            if "confidence_interval" in prediction_data:
                confidence_analysis[prediction_type] = {
                    "confidence_level": prediction_data.get("confidence_level", 0.95),
                    "average_confidence": prediction_data.get("average_confidence", 0.0),
                    "confidence_range": prediction_data.get("confidence_interval", []),
                    "reliability_score": self._calculate_reliability_score(prediction_data)
                }
        
        return confidence_analysis
    
    def _calculate_reliability_score(self, prediction_data: Dict[str, Any]) -> float:
        """Calculate reliability score for predictions."""
        # Simple heuristic based on available metrics
        base_score = 0.8
        
        # Adjust based on historical accuracy
        if "historical_accuracy" in prediction_data:
            base_score *= prediction_data["historical_accuracy"]
        
        # Adjust based on data quality
        if "data_quality_score" in prediction_data:
            base_score *= prediction_data["data_quality_score"]
        
        return min(1.0, max(0.0, base_score))
    
    def _generate_prediction_recommendations(self, predictions: Dict[str, Any], 
                                           request: PredictiveAnalyticsRequest) -> List[Dict[str, Any]]:
        """Generate recommendations based on predictions."""
        recommendations = []
        
        for prediction_type, prediction_data in predictions.items():
            if prediction_type == "energy_usage":
                if prediction_data.get("trend") == "increasing":
                    recommendations.append({
                        "type": "energy_optimization",
                        "priority": "high",
                        "message": "Predicted energy usage increase - implement conservation measures",
                        "actions": [
                            "Review HVAC schedules",
                            "Optimize lighting controls",
                            "Implement demand response strategies"
                        ]
                    })
            
            elif prediction_type == "maintenance":
                high_risk_items = prediction_data.get("high_risk_items", [])
                if high_risk_items:
                    recommendations.append({
                        "type": "maintenance_scheduling",
                        "priority": "high",
                        "message": f"Schedule maintenance for {len(high_risk_items)} high-risk items",
                        "actions": ["Schedule preventive maintenance", "Order replacement parts", "Allocate technician resources"],
                        "affected_items": high_risk_items
                    })
        
        return recommendations
    
    def _calculate_prediction_impacts(self, predictions: Dict[str, Any], 
                                    request: PredictiveAnalyticsRequest) -> Dict[str, Any]:
        """Calculate potential impacts of predictions."""
        impacts = {}
        
        for prediction_type, prediction_data in predictions.items():
            if prediction_type == "energy_usage":
                predicted_usage = prediction_data.get("total_predicted", 0)
                baseline_usage = prediction_data.get("baseline", 0)
                
                if baseline_usage > 0:
                    impact_percent = ((predicted_usage - baseline_usage) / baseline_usage) * 100
                    cost_impact = impact_percent * 0.15  # Assume $0.15 per kWh
                    
                    impacts["energy_usage"] = {
                        "usage_change_percent": impact_percent,
                        "estimated_cost_impact": cost_impact,
                        "environmental_impact": impact_percent * 0.0005  # CO2 estimate
                    }
        
        return impacts
    
    def _get_report_template(self, report_type: str, template_options: Optional[Dict[str, Any]]) -> ReportTemplate:
        """Get or create report template."""
        # Try to get existing template
        template = self.report_repository.get_template_by_type(report_type)
        
        if not template:
            # Create default template
            template = ReportTemplate(
                type=report_type,
                sections=self._get_default_report_sections(report_type),
                options=template_options or {}
            )
        
        return template
    
    def _get_default_report_sections(self, report_type: str) -> List[Dict[str, Any]]:
        """Get default sections for report type."""
        if report_type == "dashboard":
            return [
                {"section": "executive_summary", "required": True},
                {"section": "building_metrics", "required": True},
                {"section": "occupancy_analysis", "required": False},
                {"section": "energy_analysis", "required": False},
                {"section": "device_health", "required": False}
            ]
        elif report_type == "energy":
            return [
                {"section": "energy_summary", "required": True},
                {"section": "consumption_trends", "required": True},
                {"section": "cost_analysis", "required": True},
                {"section": "efficiency_recommendations", "required": False}
            ]
        else:
            return [{"section": "general_summary", "required": True}]
    
    def _gather_report_data(self, request: ReportGenerationRequest, 
                          template: ReportTemplate) -> Dict[str, Any]:
        """Gather data required for report generation."""
        report_data = {}
        
        # Parse time range for data gathering
        end_time = datetime.now(timezone.utc)
        if request.parameters and "time_range" in request.parameters:
            start_time = self._parse_time_range(request.parameters["time_range"], end_time)
        else:
            start_time = end_time - timedelta(days=30)  # Default to 30 days
        
        # Gather data for each required section
        for section in template.sections:
            section_name = section["section"]
            
            if section_name == "executive_summary":
                report_data[section_name] = self._get_executive_summary_data(start_time, end_time)
            elif section_name == "building_metrics":
                report_data[section_name] = self._get_building_summary_metrics(start_time, end_time)
            elif section_name == "occupancy_analysis":
                report_data[section_name] = self._get_occupancy_metrics(start_time, end_time)
            elif section_name == "energy_analysis":
                report_data[section_name] = self._get_energy_usage_metrics(start_time, end_time)
            elif section_name == "device_health":
                report_data[section_name] = self._get_device_health_metrics(start_time, end_time)
        
        return report_data
    
    def _get_executive_summary_data(self, start_time: datetime, end_time: datetime) -> Dict[str, Any]:
        """Get executive summary data for reports."""
        return {
            "report_period": {
                "start": start_time.isoformat(),
                "end": end_time.isoformat()
            },
            "key_metrics": self._get_building_summary_metrics(start_time, end_time),
            "highlights": self._get_period_highlights(start_time, end_time),
            "concerns": self._get_period_concerns(start_time, end_time)
        }
    
    def _get_period_highlights(self, start_time: datetime, end_time: datetime) -> List[str]:
        """Get key highlights for the reporting period."""
        highlights = []
        
        # Get some sample highlights based on metrics
        energy_data = self._get_energy_usage_metrics(start_time, end_time)
        if energy_data.get("efficiency_score", 0) > 85:
            highlights.append("Energy efficiency exceeded target at {:.1f}%".format(energy_data["efficiency_score"]))
        
        device_health = self._get_device_health_metrics(start_time, end_time)
        if device_health.get("overall_health_score", 0) > 90:
            highlights.append("Device health score maintained above 90%")
        
        return highlights
    
    def _get_period_concerns(self, start_time: datetime, end_time: datetime) -> List[str]:
        """Get key concerns for the reporting period."""
        concerns = []
        
        device_health = self._get_device_health_metrics(start_time, end_time)
        if device_health.get("offline_devices", 0) > 10:
            concerns.append("{} devices are currently offline".format(device_health["offline_devices"]))
        
        if device_health.get("maintenance_required", 0) > 20:
            concerns.append("{} devices require maintenance".format(device_health["maintenance_required"]))
        
        return concerns
    
    def _schedule_report_delivery(self, report_result: Dict[str, Any], 
                                delivery_options: Dict[str, Any]) -> None:
        """Schedule report delivery via email or other methods."""
        # This would integrate with email service or notification system
        if self.message_queue:
            delivery_message = {
                "type": "report_delivery",
                "report_id": report_result["report_id"],
                "delivery_options": delivery_options,
                "scheduled_at": datetime.now(timezone.utc).isoformat()
            }
            self.message_queue.publish("report_delivery", delivery_message)