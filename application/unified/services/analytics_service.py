"""
Analytics Service - Unified Analytics and Reporting for Building Management

This module provides comprehensive analytics services including performance
analytics, predictive modeling, and advanced reporting capabilities.
"""

from typing import Dict, Any, List, Optional, Union
import asyncio
import logging
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

from application.unified.dto.building_dto import BuildingDTO
from application.unified.dto.analytics_dto import (
    AnalyticsReport, PerformanceMetrics, TrendAnalysis,
    ComparativeAnalysis, PredictiveInsights, AnalyticsRequest
)
from infrastructure.analytics.data_processor import DataProcessor
from infrastructure.analytics.trend_analyzer import TrendAnalyzer
from infrastructure.analytics.predictive_engine import PredictiveEngine
from infrastructure.analytics.report_generator import ReportGenerator

logger = logging.getLogger(__name__)


class AnalyticsType(str, Enum):
    """Analytics types."""
    PERFORMANCE = "performance"
    TREND = "trend"
    COMPARATIVE = "comparative"
    PREDICTIVE = "predictive"
    ENERGY = "energy"
    MAINTENANCE = "maintenance"
    OCCUPANCY = "occupancy"
    COST = "cost"


@dataclass
class AnalyticsConfig:
    """Configuration for analytics features."""
    data_retention_days: int = 365
    batch_processing_size: int = 1000
    real_time_processing: bool = True
    enable_machine_learning: bool = True
    enable_predictive_analytics: bool = True
    enable_anomaly_detection: bool = True


class AnalyticsService:
    """
    Unified analytics service providing advanced analytics and reporting.

    This service implements:
    - Performance analytics and metrics
    - Trend analysis and forecasting
    - Comparative analysis across buildings
    - Predictive modeling and insights
    - Advanced reporting and visualization
    """

    def __init__(self,
                 data_processor: DataProcessor,
                 trend_analyzer: TrendAnalyzer,
                 predictive_engine: PredictiveEngine,
                 report_generator: ReportGenerator,
                 config: AnalyticsConfig = None):
        """Initialize analytics service with components."""
        self.data_processor = data_processor
        self.trend_analyzer = trend_analyzer
        self.predictive_engine = predictive_engine
        self.report_generator = report_generator
        self.config = config or AnalyticsConfig()
        self.logger = logging.getLogger(self.__class__.__name__)

    async def generate_performance_analytics(self, building_dto: BuildingDTO,
                                           time_range: str = "30d") -> PerformanceMetrics:
        """
        Generate comprehensive performance analytics for a building.

        Args:
            building_dto: Building data for analysis
            time_range: Time range for analysis (7d, 30d, 90d, 1y)

        Returns:
            Performance metrics and analytics
        """
        try:
            self.logger.info(f"Generating performance analytics for building {building_dto.id}")

            # Process building data
            processed_data = await self.data_processor.process_building_data(
                building_dto, time_range
            )

            # Calculate performance metrics
            metrics = await self._calculate_performance_metrics(processed_data)

            # Generate insights
            insights = await self._generate_performance_insights(metrics, building_dto)

            result = PerformanceMetrics(
                building_id=building_dto.id,
                time_range=time_range,
                energy_efficiency=metrics.get('energy_efficiency', 0.0),
                maintenance_efficiency=metrics.get('maintenance_efficiency', 0.0),
                occupancy_rate=metrics.get('occupancy_rate', 0.0),
                cost_per_sqm=metrics.get('cost_per_sqm', 0.0),
                satisfaction_score=metrics.get('satisfaction_score', 0.0),
                sustainability_score=metrics.get('sustainability_score', 0.0),
                insights=insights,
                generated_at=datetime.utcnow()
            )

            self.logger.info(f"Performance analytics completed for building {building_dto.id}")
            return result

        except Exception as e:
            self.logger.error(f"Error generating performance analytics: {e}")
            raise

    async def analyze_trends(self, building_dto: BuildingDTO,
                            metric_type: str = "energy_consumption",
                            time_period: str = "12m") -> TrendAnalysis:
        """
        Analyze trends for specific metrics over time.

        Args:
            building_dto: Building data for analysis
            metric_type: Type of metric to analyze
            time_period: Time period for analysis

        Returns:
            Trend analysis results
        """
        try:
            self.logger.info(f"Analyzing trends for building {building_dto.id}")

            # Get historical data
            historical_data = await self.data_processor.get_historical_data(
                building_dto.id, metric_type, time_period
            )

            # Analyze trends
            trend_results = await self.trend_analyzer.analyze_trends(
                data=historical_data,
                metric_type=metric_type,
                time_period=time_period
            )

            # Generate trend insights
            insights = await self._generate_trend_insights(trend_results, building_dto)

            result = TrendAnalysis(
                building_id=building_dto.id,
                metric_type=metric_type,
                time_period=time_period,
                trend_direction=trend_results.get('direction', 'stable'),
                trend_strength=trend_results.get('strength', 0.0),
                seasonal_patterns=trend_results.get('seasonal_patterns', []),
                anomalies=trend_results.get('anomalies', []),
                forecast=trend_results.get('forecast', {}),
                insights=insights,
                analyzed_at=datetime.utcnow()
            )

            self.logger.info(f"Trend analysis completed for building {building_dto.id}")
            return result

        except Exception as e:
            self.logger.error(f"Error analyzing trends: {e}")
            raise

    async def perform_comparative_analysis(self, building_dto: BuildingDTO,
                                         comparison_buildings: List[str],
                                         metrics: List[str]) -> ComparativeAnalysis:
        """
        Perform comparative analysis against other buildings.

        Args:
            building_dto: Primary building for comparison
            comparison_buildings: List of building IDs to compare against
            metrics: List of metrics to compare

        Returns:
            Comparative analysis results
        """
        try:
            self.logger.info(f"Performing comparative analysis for building {building_dto.id}")

            # Gather data for all buildings
            all_buildings_data = await self._gather_comparison_data(
                building_dto, comparison_buildings, metrics
            )

            # Perform comparative analysis
            comparison_results = await self.data_processor.compare_buildings(
                primary_building=building_dto.id,
                comparison_buildings=comparison_buildings,
                metrics=metrics,
                data=all_buildings_data
            )

            # Generate comparative insights
            insights = await self._generate_comparative_insights(comparison_results, building_dto)

            result = ComparativeAnalysis(
                primary_building_id=building_dto.id,
                comparison_buildings=comparison_buildings,
                metrics=metrics,
                rankings=comparison_results.get('rankings', {}),
                percentiles=comparison_results.get('percentiles', {}),
                benchmarks=comparison_results.get('benchmarks', {}),
                insights=insights,
                analyzed_at=datetime.utcnow()
            )

            self.logger.info(f"Comparative analysis completed for building {building_dto.id}")
            return result

        except Exception as e:
            self.logger.error(f"Error performing comparative analysis: {e}")
            raise

    async def generate_predictive_insights(self, building_dto: BuildingDTO,
                                         prediction_horizon: int = 12) -> PredictiveInsights:
        """
        Generate predictive insights using machine learning models.

        Args:
            building_dto: Building data for prediction
            prediction_horizon: Number of months to predict

        Returns:
            Predictive insights and forecasts
        """
        try:
            self.logger.info(f"Generating predictive insights for building {building_dto.id}")

            # Prepare data for prediction
            prediction_data = await self.data_processor.prepare_prediction_data(
                building_dto, prediction_horizon
            )

            # Generate predictions
            predictions = await self.predictive_engine.generate_predictions(
                data=prediction_data,
                horizon=prediction_horizon
            )

            # Generate predictive insights
            insights = await self._generate_predictive_insights(predictions, building_dto)

            result = PredictiveInsights(
                building_id=building_dto.id,
                prediction_horizon=prediction_horizon,
                energy_forecast=predictions.get('energy_forecast', {}),
                maintenance_forecast=predictions.get('maintenance_forecast', {}),
                cost_forecast=predictions.get('cost_forecast', {}),
                risk_assessment=predictions.get('risk_assessment', {}),
                optimization_opportunities=predictions.get('optimization_opportunities', []),
                insights=insights,
                confidence_scores=predictions.get('confidence_scores', {}),
                generated_at=datetime.utcnow()
            )

            self.logger.info(f"Predictive insights completed for building {building_dto.id}")
            return result

        except Exception as e:
            self.logger.error(f"Error generating predictive insights: {e}")
            raise

    async def generate_comprehensive_report(self, building_dto: BuildingDTO,
                                         report_type: str = "comprehensive",
                                         include_visualizations: bool = True) -> AnalyticsReport:
        """
        Generate comprehensive analytics report.

        Args:
            building_dto: Building data for report
            report_type: Type of report to generate
            include_visualizations: Whether to include charts and graphs

        Returns:
            Comprehensive analytics report
        """
        try:
            self.logger.info(f"Generating {report_type} report for building {building_dto.id}")

            # Generate all analytics components
            performance_metrics = await self.generate_performance_analytics(building_dto)
            trend_analysis = await self.analyze_trends(building_dto)
            predictive_insights = await self.generate_predictive_insights(building_dto)

            # Generate report
            report_data = await self.report_generator.generate_report(
                building_data=building_dto,
                performance_metrics=performance_metrics,
                trend_analysis=trend_analysis,
                predictive_insights=predictive_insights,
                report_type=report_type,
                include_visualizations=include_visualizations
            )

            result = AnalyticsReport(
                building_id=building_dto.id,
                report_type=report_type,
                executive_summary=report_data.get('executive_summary', ''),
                key_findings=report_data.get('key_findings', []),
                recommendations=report_data.get('recommendations', []),
                visualizations=report_data.get('visualizations', []) if include_visualizations else [],
                detailed_analysis=report_data.get('detailed_analysis', {}),
                generated_at=datetime.utcnow()
            )

            self.logger.info(f"Comprehensive report completed for building {building_dto.id}")
            return result

        except Exception as e:
            self.logger.error(f"Error generating comprehensive report: {e}")
            raise

    async def analyze_energy_performance(self, building_dto: BuildingDTO) -> Dict[str, Any]:
        """
        Analyze energy performance specifically.

        Args:
            building_dto: Building data for analysis

        Returns:
            Energy performance analysis
        """
        try:
            self.logger.info(f"Analyzing energy performance for building {building_dto.id}")

            # Get energy data
            energy_data = await self.data_processor.get_energy_data(building_dto.id)

            # Analyze energy patterns
            energy_analysis = await self.trend_analyzer.analyze_energy_patterns(energy_data)

            # Generate energy insights
            insights = await self._generate_energy_insights(energy_analysis, building_dto)

            result = {
                'building_id': building_dto.id,
                'energy_consumption': energy_analysis.get('consumption', {}),
                'efficiency_score': energy_analysis.get('efficiency_score', 0.0),
                'optimization_opportunities': energy_analysis.get('optimization_opportunities', []),
                'cost_savings_potential': energy_analysis.get('cost_savings_potential', 0.0),
                'insights': insights,
                'analyzed_at': datetime.utcnow().isoformat()
            }

            self.logger.info(f"Energy performance analysis completed for building {building_dto.id}")
            return result

        except Exception as e:
            self.logger.error(f"Error analyzing energy performance: {e}")
            raise

    async def analyze_maintenance_patterns(self, building_dto: BuildingDTO) -> Dict[str, Any]:
        """
        Analyze maintenance patterns and predict future needs.

        Args:
            building_dto: Building data for analysis

        Returns:
            Maintenance pattern analysis
        """
        try:
            self.logger.info(f"Analyzing maintenance patterns for building {building_dto.id}")

            # Get maintenance data
            maintenance_data = await self.data_processor.get_maintenance_data(building_dto.id)

            # Analyze maintenance patterns
            maintenance_analysis = await self.trend_analyzer.analyze_maintenance_patterns(maintenance_data)

            # Generate maintenance insights
            insights = await self._generate_maintenance_insights(maintenance_analysis, building_dto)

            result = {
                'building_id': building_dto.id,
                'maintenance_frequency': maintenance_analysis.get('frequency', {}),
                'cost_trends': maintenance_analysis.get('cost_trends', {}),
                'priority_items': maintenance_analysis.get('priority_items', []),
                'predictive_maintenance': maintenance_analysis.get('predictive_maintenance', {}),
                'insights': insights,
                'analyzed_at': datetime.utcnow().isoformat()
            }

            self.logger.info(f"Maintenance pattern analysis completed for building {building_dto.id}")
            return result

        except Exception as e:
            self.logger.error(f"Error analyzing maintenance patterns: {e}")
            raise

    async def _calculate_performance_metrics(self, processed_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate performance metrics from processed data."""
        metrics = {}

        # Energy efficiency
        if 'energy_consumption' in processed_data:
            metrics['energy_efficiency'] = self._calculate_energy_efficiency(
                processed_data['energy_consumption']
            )

        # Maintenance efficiency
        if 'maintenance_data' in processed_data:
            metrics['maintenance_efficiency'] = self._calculate_maintenance_efficiency(
                processed_data['maintenance_data']
            )

        # Occupancy rate
        if 'occupancy_data' in processed_data:
            metrics['occupancy_rate'] = self._calculate_occupancy_rate(
                processed_data['occupancy_data']
            )

        # Cost per square meter
        if 'cost_data' in processed_data and 'area' in processed_data:
            metrics['cost_per_sqm'] = self._calculate_cost_per_sqm(
                processed_data['cost_data'], processed_data['area']
            )

        # Satisfaction score
        if 'satisfaction_data' in processed_data:
            metrics['satisfaction_score'] = self._calculate_satisfaction_score(
                processed_data['satisfaction_data']
            )

        # Sustainability score
        if 'sustainability_data' in processed_data:
            metrics['sustainability_score'] = self._calculate_sustainability_score(
                processed_data['sustainability_data']
            )

        return metrics

    def _calculate_energy_efficiency(self, energy_data: Dict[str, Any]) -> float:
        """Calculate energy efficiency score."""
        # Implementation would include complex energy efficiency calculations
        return energy_data.get('efficiency_score', 0.0)

    def _calculate_maintenance_efficiency(self, maintenance_data: Dict[str, Any]) -> float:
        """Calculate maintenance efficiency score."""
        # Implementation would include maintenance efficiency calculations
        return maintenance_data.get('efficiency_score', 0.0)

    def _calculate_occupancy_rate(self, occupancy_data: Dict[str, Any]) -> float:
        """Calculate occupancy rate."""
        return occupancy_data.get('average_occupancy', 0.0)

    def _calculate_cost_per_sqm(self, cost_data: Dict[str, Any], area: float) -> float:
        """Calculate cost per square meter."""
        total_cost = cost_data.get('total_cost', 0.0)
        return total_cost / area if area > 0 else 0.0

    def _calculate_satisfaction_score(self, satisfaction_data: Dict[str, Any]) -> float:
        """Calculate satisfaction score."""
        return satisfaction_data.get('average_satisfaction', 0.0)

    def _calculate_sustainability_score(self, sustainability_data: Dict[str, Any]) -> float:
        """Calculate sustainability score."""
        return sustainability_data.get('sustainability_score', 0.0)

    async def _generate_performance_insights(self, metrics: Dict[str, Any],
                                           building_dto: BuildingDTO) -> List[str]:
        """Generate insights from performance metrics."""
        insights = []

        # Energy efficiency insights
        if metrics.get('energy_efficiency', 0) < 0.7:
            insights.append("Energy efficiency is below optimal levels. Consider energy optimization measures.")

        # Maintenance efficiency insights
        if metrics.get('maintenance_efficiency', 0) < 0.8:
            insights.append("Maintenance efficiency could be improved. Review maintenance schedules.")

        # Occupancy insights
        occupancy_rate = metrics.get('occupancy_rate', 0)
        if occupancy_rate < 0.6:
            insights.append("Low occupancy rate detected. Consider space utilization optimization.")
        elif occupancy_rate > 0.95:
            insights.append("High occupancy rate. Consider expansion opportunities.")

        # Cost insights
        if metrics.get('cost_per_sqm', 0) > 100:  # Example threshold
            insights.append("Cost per square meter is high. Review operational costs.")

        return insights

    async def _generate_trend_insights(self, trend_results: Dict[str, Any],
                                     building_dto: BuildingDTO) -> List[str]:
        """Generate insights from trend analysis."""
        insights = []

        direction = trend_results.get('direction', 'stable')
        strength = trend_results.get('strength', 0.0)

        if direction == 'increasing' and strength > 0.7:
            insights.append("Strong upward trend detected. Monitor for potential issues.")
        elif direction == 'decreasing' and strength > 0.7:
            insights.append("Strong downward trend detected. Verify data accuracy.")

        anomalies = trend_results.get('anomalies', [])
        if anomalies:
            insights.append(f"Detected {len(anomalies)} anomalies. Review for data quality issues.")

        return insights

    async def _generate_comparative_insights(self, comparison_results: Dict[str, Any],
                                           building_dto: BuildingDTO) -> List[str]:
        """Generate insights from comparative analysis."""
        insights = []

        rankings = comparison_results.get('rankings', {})
        percentiles = comparison_results.get('percentiles', {})

        for metric, ranking in rankings.items():
            if ranking <= 0.25:
                insights.append(f"Building performs in top 25% for {metric}.")
            elif ranking >= 0.75:
                insights.append(f"Building performs in bottom 25% for {metric}. Consider improvements.")

        return insights

    async def _generate_predictive_insights(self, predictions: Dict[str, Any],
                                          building_dto: BuildingDTO) -> List[str]:
        """Generate insights from predictive analysis."""
        insights = []

        # Energy forecast insights
        energy_forecast = predictions.get('energy_forecast', {})
        if energy_forecast.get('trend') == 'increasing':
            insights.append("Energy consumption expected to increase. Plan for optimization measures.")

        # Maintenance forecast insights
        maintenance_forecast = predictions.get('maintenance_forecast', {})
        if maintenance_forecast.get('upcoming_maintenance'):
            insights.append("Upcoming maintenance needs predicted. Schedule preventive maintenance.")

        # Risk assessment insights
        risk_assessment = predictions.get('risk_assessment', {})
        high_risks = risk_assessment.get('high_risks', [])
        if high_risks:
            insights.append(f"Identified {len(high_risks)} high-risk areas. Prioritize mitigation.")

        return insights

    async def _gather_comparison_data(self, building_dto: BuildingDTO,
                                    comparison_buildings: List[str],
                                    metrics: List[str]) -> Dict[str, Any]:
        """Gather data for comparative analysis."""
        all_data = {
            building_dto.id: await self.data_processor.get_building_metrics(
                building_dto.id, metrics
            )
        }

        for building_id in comparison_buildings:
            all_data[building_id] = await self.data_processor.get_building_metrics(
                building_id, metrics
            )

        return all_data

    async def _generate_energy_insights(self, energy_analysis: Dict[str, Any],
                                      building_dto: BuildingDTO) -> List[str]:
        """Generate energy-specific insights."""
        insights = []

        efficiency_score = energy_analysis.get('efficiency_score', 0.0)
        if efficiency_score < 0.7:
            insights.append("Energy efficiency below optimal levels. Consider energy optimization.")

        cost_savings = energy_analysis.get('cost_savings_potential', 0.0)
        if cost_savings > 10000:  # Example threshold
            insights.append(f"Potential cost savings of ${cost_savings:,.2f} through energy optimization.")

        return insights

    async def _generate_maintenance_insights(self, maintenance_analysis: Dict[str, Any],
                                           building_dto: BuildingDTO) -> List[str]:
        """Generate maintenance-specific insights."""
        insights = []

        priority_items = maintenance_analysis.get('priority_items', [])
        if priority_items:
            insights.append(f"{len(priority_items)} priority maintenance items identified.")

        cost_trends = maintenance_analysis.get('cost_trends', {})
        if cost_trends.get('trend') == 'increasing':
            insights.append("Maintenance costs trending upward. Review maintenance strategies.")

        return insights
