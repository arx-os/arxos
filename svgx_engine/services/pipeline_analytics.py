#!/usr/bin/env python3
"""
Pipeline Analytics and Insights System

Provides comprehensive analytics, performance analysis, and optimization
recommendations for the Arxos pipeline system.
"""

import json
import logging
import sqlite3
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import statistics
from collections import defaultdict, Counter
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class PipelineInsight:
    """Pipeline insight data structure."""
    insight_type: str
    title: str
    description: str
    severity: str  # "info", "warning", "critical"
    metric_value: float
    threshold: float
    recommendation: str
    timestamp: float


@dataclass
class PerformanceAnalysis:
    """Performance analysis data structure."""
    system: str
    total_executions: int
    successful_executions: int
    failed_executions: int
    avg_execution_time: float
    success_rate: float
    bottleneck_operations: List[str]
    optimization_opportunities: List[str]


@dataclass
class TrendAnalysis:
    """Trend analysis data structure."""
    metric_name: str
    time_period: str
    trend_direction: str  # "improving", "declining", "stable"
    change_percentage: float
    data_points: List[Tuple[float, float]]  # (timestamp, value)


class PipelineAnalytics:
    """Advanced analytics and insights system for pipeline operations."""
    
    def __init__(self, metrics_db_path: str = "pipeline_metrics.db"):
        self.metrics_db_path = metrics_db_path
        self.insights = []
        self.performance_cache = {}
        self.trend_cache = {}
        
        # Analytics configuration
        self.performance_thresholds = {
            "success_rate": 95.0,
            "avg_execution_time": 300.0,  # seconds
            "error_rate": 5.0,
            "resource_usage": 80.0
        }
    
    def analyze_pipeline_performance(self, system: str = None, 
                                   days: int = 30) -> PerformanceAnalysis:
        """Analyze pipeline performance for a system."""
        try:
            cutoff_time = time.time() - (days * 24 * 3600)
            
            conn = sqlite3.connect(self.metrics_db_path)
            
            # Get execution metrics
            if system:
                cursor = conn.execute("""
                    SELECT COUNT(*) as total,
                           SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as successful,
                           SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed,
                           AVG(CASE WHEN completed_at IS NOT NULL 
                               THEN (completed_at - started_at) ELSE NULL END) as avg_time
                    FROM pipeline_executions 
                    WHERE system = ? AND created_at > ?
                """, (system, cutoff_time))
            else:
                cursor = conn.execute("""
                    SELECT COUNT(*) as total,
                           SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as successful,
                           SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed,
                           AVG(CASE WHEN completed_at IS NOT NULL 
                               THEN (completed_at - started_at) ELSE NULL END) as avg_time
                    FROM pipeline_executions 
                    WHERE created_at > ?
                """, (cutoff_time,))
            
            row = cursor.fetchone()
            total_executions, successful_executions, failed_executions, avg_time = row
            
            # Calculate success rate
            success_rate = (successful_executions / total_executions * 100) if total_executions > 0 else 0
            
            # Get bottleneck operations
            bottleneck_operations = self._identify_bottlenecks(system, cutoff_time)
            
            # Get optimization opportunities
            optimization_opportunities = self._identify_optimization_opportunities(system, cutoff_time)
            
            conn.close()
            
            analysis = PerformanceAnalysis(
                system=system or "all",
                total_executions=total_executions,
                successful_executions=successful_executions,
                failed_executions=failed_executions,
                avg_execution_time=avg_time or 0,
                success_rate=success_rate,
                bottleneck_operations=bottleneck_operations,
                optimization_opportunities=optimization_opportunities
            )
            
            # Cache the analysis
            cache_key = f"{system}_{days}"
            self.performance_cache[cache_key] = analysis
            
            return analysis
            
        except Exception as e:
            logger.error(f"Failed to analyze pipeline performance: {e}")
            return None
    
    def _identify_bottlenecks(self, system: str, cutoff_time: float) -> List[str]:
        """Identify bottleneck operations."""
        try:
            conn = sqlite3.connect(self.metrics_db_path)
            
            if system:
                cursor = conn.execute("""
                    SELECT step_name, AVG(duration_ms) as avg_duration,
                           COUNT(*) as total_operations
                    FROM pipeline_steps ps
                    JOIN pipeline_executions pe ON ps.execution_id = pe.id
                    WHERE pe.system = ? AND pe.created_at > ?
                    GROUP BY step_name
                    ORDER BY avg_duration DESC
                    LIMIT 5
                """, (system, cutoff_time))
            else:
                cursor = conn.execute("""
                    SELECT step_name, AVG(duration_ms) as avg_duration,
                           COUNT(*) as total_operations
                    FROM pipeline_steps
                    WHERE created_at > ?
                    GROUP BY step_name
                    ORDER BY avg_duration DESC
                    LIMIT 5
                """, (cutoff_time,))
            
            bottlenecks = []
            for row in cursor.fetchall():
                step_name, avg_duration, total_ops = row
                if avg_duration > 5000:  # 5 seconds threshold
                    bottlenecks.append(f"{step_name} ({avg_duration:.0f}ms avg)")
            
            conn.close()
            return bottlenecks
            
        except Exception as e:
            logger.error(f"Failed to identify bottlenecks: {e}")
            return []
    
    def _identify_optimization_opportunities(self, system: str, cutoff_time: float) -> List[str]:
        """Identify optimization opportunities."""
        opportunities = []
        
        try:
            conn = sqlite3.connect(self.metrics_db_path)
            
            # Check for high error rates
            if system:
                cursor = conn.execute("""
                    SELECT step_name, 
                           COUNT(*) as total_ops,
                           SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed_ops
                    FROM pipeline_steps ps
                    JOIN pipeline_executions pe ON ps.execution_id = pe.id
                    WHERE pe.system = ? AND pe.created_at > ?
                    GROUP BY step_name
                    HAVING failed_ops > 0
                """, (system, cutoff_time))
            else:
                cursor = conn.execute("""
                    SELECT step_name, 
                           COUNT(*) as total_ops,
                           SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed_ops
                    FROM pipeline_steps
                    WHERE created_at > ?
                    GROUP BY step_name
                    HAVING failed_ops > 0
                """, (cutoff_time,))
            
            for row in cursor.fetchall():
                step_name, total_ops, failed_ops = row
                error_rate = (failed_ops / total_ops) * 100
                if error_rate > 10:  # 10% error rate threshold
                    opportunities.append(f"Reduce error rate in {step_name} (currently {error_rate:.1f}%)")
            
            # Check for resource usage patterns
            cursor = conn.execute("""
                SELECT metric_name, AVG(metric_value) as avg_value
                FROM pipeline_metrics
                WHERE metric_name IN ('cpu_usage', 'memory_usage', 'disk_usage')
                AND timestamp > ?
                GROUP BY metric_name
            """, (cutoff_time,))
            
            for row in cursor.fetchall():
                metric_name, avg_value = row
                if avg_value > 80:  # 80% usage threshold
                    opportunities.append(f"Optimize {metric_name} usage (currently {avg_value:.1f}%)")
            
            conn.close()
            
        except Exception as e:
            logger.error(f"Failed to identify optimization opportunities: {e}")
        
        return opportunities
    
    def analyze_trends(self, metric_name: str, days: int = 30) -> TrendAnalysis:
        """Analyze trends for a specific metric."""
        try:
            cutoff_time = time.time() - (days * 24 * 3600)
            
            conn = sqlite3.connect(self.metrics_db_path)
            cursor = conn.execute("""
                SELECT timestamp, metric_value
                FROM pipeline_metrics
                WHERE metric_name = ? AND timestamp > ?
                ORDER BY timestamp
            """, (metric_name, cutoff_time))
            
            data_points = cursor.fetchall()
            conn.close()
            
            if len(data_points) < 2:
                return None
            
            # Calculate trend
            timestamps, values = zip(*data_points)
            
            # Simple linear regression
            x = np.array(timestamps)
            y = np.array(values)
            
            # Normalize timestamps to days for better slope interpretation
            x_normalized = (x - x[0]) / (24 * 3600)  # Convert to days
            
            slope, intercept = np.polyfit(x_normalized, y, 1)
            
            # Calculate change percentage
            first_value = values[0]
            last_value = values[-1]
            change_percentage = ((last_value - first_value) / first_value * 100) if first_value != 0 else 0
            
            # Determine trend direction
            if abs(change_percentage) < 5:
                trend_direction = "stable"
            elif change_percentage > 0:
                trend_direction = "improving" if metric_name in ["success_rate"] else "declining"
            else:
                trend_direction = "declining" if metric_name in ["success_rate"] else "improving"
            
            trend = TrendAnalysis(
                metric_name=metric_name,
                time_period=f"{days} days",
                trend_direction=trend_direction,
                change_percentage=change_percentage,
                data_points=data_points
            )
            
            # Cache the trend
            cache_key = f"{metric_name}_{days}"
            self.trend_cache[cache_key] = trend
            
            return trend
            
        except Exception as e:
            logger.error(f"Failed to analyze trends for {metric_name}: {e}")
            return None
    
    def generate_insights(self, system: str = None) -> List[PipelineInsight]:
        """Generate insights based on current metrics."""
        insights = []
        
        try:
            # Analyze performance
            performance = self.analyze_pipeline_performance(system)
            if performance:
                # Success rate insight
                if performance.success_rate < self.performance_thresholds["success_rate"]:
                    insights.append(PipelineInsight(
                        insight_type="performance",
                        title="Low Success Rate",
                        description=f"Pipeline success rate is {performance.success_rate:.1f}%, below threshold of {self.performance_thresholds['success_rate']}%",
                        severity="warning" if performance.success_rate > 80 else "critical",
                        metric_value=performance.success_rate,
                        threshold=self.performance_thresholds["success_rate"],
                        recommendation="Review failed executions and improve error handling",
                        timestamp=time.time()
                    ))
                
                # Execution time insight
                if performance.avg_execution_time > self.performance_thresholds["avg_execution_time"]:
                    insights.append(PipelineInsight(
                        insight_type="performance",
                        title="Slow Execution",
                        description=f"Average execution time is {performance.avg_execution_time:.1f}s, above threshold of {self.performance_thresholds['avg_execution_time']}s",
                        severity="warning",
                        metric_value=performance.avg_execution_time,
                        threshold=self.performance_thresholds["avg_execution_time"],
                        recommendation="Optimize bottleneck operations and consider parallel processing",
                        timestamp=time.time()
                    ))
                
                # Bottleneck insights
                for bottleneck in performance.bottleneck_operations[:3]:  # Top 3 bottlenecks
                    insights.append(PipelineInsight(
                        insight_type="bottleneck",
                        title="Performance Bottleneck",
                        description=f"Operation {bottleneck} is causing performance issues",
                        severity="warning",
                        metric_value=0,  # Will be filled with actual duration
                        threshold=5000,  # 5 second threshold
                        recommendation="Optimize this operation or consider caching",
                        timestamp=time.time()
                    ))
            
            # Analyze trends
            trend_metrics = ["success_rate", "avg_execution_time", "cpu_usage", "memory_usage"]
            for metric in trend_metrics:
                trend = self.analyze_trends(metric)
                if trend and abs(trend.change_percentage) > 10:  # 10% change threshold
                    insights.append(PipelineInsight(
                        insight_type="trend",
                        title=f"{metric.replace('_', ' ').title()} Trend",
                        description=f"{metric} is {trend.trend_direction} by {abs(trend.change_percentage):.1f}%",
                        severity="info" if trend.trend_direction == "improving" else "warning",
                        metric_value=trend.change_percentage,
                        threshold=10,
                        recommendation=f"Monitor this trend and take action if needed",
                        timestamp=time.time()
                    ))
            
            self.insights = insights
            return insights
            
        except Exception as e:
            logger.error(f"Failed to generate insights: {e}")
            return []
    
    def generate_optimization_recommendations(self, system: str = None) -> List[str]:
        """Generate specific optimization recommendations."""
        recommendations = []
        
        try:
            performance = self.analyze_pipeline_performance(system)
            if not performance:
                return recommendations
            
            # Success rate recommendations
            if performance.success_rate < 95:
                recommendations.append("Implement better error handling and retry mechanisms")
                recommendations.append("Add more comprehensive validation before pipeline execution")
                recommendations.append("Review and fix common failure patterns")
            
            # Performance recommendations
            if performance.avg_execution_time > 300:
                recommendations.append("Implement parallel processing for independent steps")
                recommendations.append("Add caching for frequently accessed data")
                recommendations.append("Optimize database queries and add indexes")
            
            # Bottleneck-specific recommendations
            for bottleneck in performance.bottleneck_operations:
                if "validate" in bottleneck.lower():
                    recommendations.append("Implement incremental validation to reduce processing time")
                elif "symbol" in bottleneck.lower():
                    recommendations.append("Optimize symbol loading with lazy loading and caching")
                elif "behavior" in bottleneck.lower():
                    recommendations.append("Implement behavior profile caching and optimization")
            
            # Resource optimization recommendations
            conn = sqlite3.connect(self.metrics_db_path)
            cursor = conn.execute("""
                SELECT metric_name, AVG(metric_value) as avg_value
                FROM pipeline_metrics
                WHERE metric_name IN ('cpu_usage', 'memory_usage', 'disk_usage')
                AND timestamp > ?
                GROUP BY metric_name
            """, (time.time() - (7 * 24 * 3600),))  # Last 7 days
            
            for row in cursor.fetchall():
                metric_name, avg_value = row
                if avg_value > 80:
                    if metric_name == "cpu_usage":
                        recommendations.append("Implement CPU-intensive operations in background jobs")
                    elif metric_name == "memory_usage":
                        recommendations.append("Implement memory pooling and garbage collection optimization")
                    elif metric_name == "disk_usage":
                        recommendations.append("Implement data archiving and cleanup procedures")
            
            conn.close()
            
        except Exception as e:
            logger.error(f"Failed to generate optimization recommendations: {e}")
        
        return recommendations
    
    def create_performance_report(self, system: str = None, days: int = 30) -> Dict[str, Any]:
        """Create a comprehensive performance report."""
        try:
            performance = self.analyze_pipeline_performance(system, days)
            insights = self.generate_insights(system)
            recommendations = self.generate_optimization_recommendations(system)
            
            # Get trend data
            trends = {}
            trend_metrics = ["success_rate", "avg_execution_time", "cpu_usage", "memory_usage"]
            for metric in trend_metrics:
                trend = self.analyze_trends(metric, days)
                if trend:
                    trends[metric] = {
                        "direction": trend.trend_direction,
                        "change_percentage": trend.change_percentage,
                        "data_points": len(trend.data_points)
                    }
            
            report = {
                "report_timestamp": time.time(),
                "report_date": datetime.now().isoformat(),
                "system": system or "all",
                "time_period_days": days,
                "performance_summary": {
                    "total_executions": performance.total_executions if performance else 0,
                    "successful_executions": performance.successful_executions if performance else 0,
                    "failed_executions": performance.failed_executions if performance else 0,
                    "success_rate": performance.success_rate if performance else 0,
                    "avg_execution_time": performance.avg_execution_time if performance else 0
                },
                "insights": [asdict(insight) for insight in insights],
                "trends": trends,
                "bottlenecks": performance.bottleneck_operations if performance else [],
                "optimization_opportunities": performance.optimization_opportunities if performance else [],
                "recommendations": recommendations,
                "summary": {
                    "critical_insights": len([i for i in insights if i.severity == "critical"]),
                    "warning_insights": len([i for i in insights if i.severity == "warning"]),
                    "info_insights": len([i for i in insights if i.severity == "info"]),
                    "total_recommendations": len(recommendations)
                }
            }
            
            return report
            
        except Exception as e:
            logger.error(f"Failed to create performance report: {e}")
            return {"error": str(e)}
    
    def export_analytics_data(self, format: str = "json", system: str = None) -> str:
        """Export analytics data in specified format."""
        try:
            if format == "json":
                report = self.create_performance_report(system)
                return json.dumps(report, indent=2)
            elif format == "csv":
                # Export performance data as CSV
                conn = sqlite3.connect(self.metrics_db_path)
                
                if system:
                    df = pd.read_sql_query("""
                        SELECT pe.system, pe.status, pe.created_at, pe.completed_at,
                               ps.step_name, ps.duration_ms, ps.status as step_status
                        FROM pipeline_executions pe
                        LEFT JOIN pipeline_steps ps ON pe.id = ps.execution_id
                        WHERE pe.system = ?
                        ORDER BY pe.created_at DESC
                    """, conn, params=(system,))
                else:
                    df = pd.read_sql_query("""
                        SELECT pe.system, pe.status, pe.created_at, pe.completed_at,
                               ps.step_name, ps.duration_ms, ps.status as step_status
                        FROM pipeline_executions pe
                        LEFT JOIN pipeline_steps ps ON pe.id = ps.execution_id
                        ORDER BY pe.created_at DESC
                    """, conn)
                
                conn.close()
                return df.to_csv(index=False)
            else:
                return "Unsupported format"
                
        except Exception as e:
            logger.error(f"Failed to export analytics data: {e}")
            return f"Error: {str(e)}"
    
    def generate_visualizations(self, system: str = None, output_dir: str = "analytics_charts"):
        """Generate visualization charts for analytics data."""
        try:
            output_path = Path(output_dir)
            output_path.mkdir(exist_ok=True)
            
            conn = sqlite3.connect(self.metrics_db_path)
            
            # Success rate over time
            if system:
                df = pd.read_sql_query("""
                    SELECT DATE(created_at, 'unixepoch') as date,
                           COUNT(*) as total,
                           SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as successful
                    FROM pipeline_executions
                    WHERE system = ?
                    GROUP BY DATE(created_at, 'unixepoch')
                    ORDER BY date
                """, conn, params=(system,))
            else:
                df = pd.read_sql_query("""
                    SELECT DATE(created_at, 'unixepoch') as date,
                           COUNT(*) as total,
                           SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as successful
                    FROM pipeline_executions
                    GROUP BY DATE(created_at, 'unixepoch')
                    ORDER BY date
                """, conn)
            
            if not df.empty:
                df['success_rate'] = (df['successful'] / df['total'] * 100)
                
                plt.figure(figsize=(12, 6))
                plt.plot(df['date'], df['success_rate'], marker='o')
                plt.title(f'Pipeline Success Rate Over Time - {system or "All Systems"}')
                plt.xlabel('Date')
                plt.ylabel('Success Rate (%)')
                plt.xticks(rotation=45)
                plt.grid(True, alpha=0.3)
                plt.tight_layout()
                plt.savefig(output_path / 'success_rate_trend.png', dpi=300, bbox_inches='tight')
                plt.close()
            
            # Execution time distribution
            if system:
                df_time = pd.read_sql_query("""
                    SELECT (completed_at - started_at) as duration
                    FROM pipeline_executions
                    WHERE system = ? AND completed_at IS NOT NULL AND started_at IS NOT NULL
                """, conn, params=(system,))
            else:
                df_time = pd.read_sql_query("""
                    SELECT (completed_at - started_at) as duration
                    FROM pipeline_executions
                    WHERE completed_at IS NOT NULL AND started_at IS NOT NULL
                """, conn)
            
            if not df_time.empty:
                plt.figure(figsize=(10, 6))
                plt.hist(df_time['duration'], bins=30, alpha=0.7, edgecolor='black')
                plt.title(f'Pipeline Execution Time Distribution - {system or "All Systems"}')
                plt.xlabel('Execution Time (seconds)')
                plt.ylabel('Frequency')
                plt.grid(True, alpha=0.3)
                plt.tight_layout()
                plt.savefig(output_path / 'execution_time_distribution.png', dpi=300, bbox_inches='tight')
                plt.close()
            
            # Step performance comparison
            if system:
                df_steps = pd.read_sql_query("""
                    SELECT ps.step_name, AVG(ps.duration_ms) as avg_duration,
                           COUNT(*) as total_operations
                    FROM pipeline_steps ps
                    JOIN pipeline_executions pe ON ps.execution_id = pe.id
                    WHERE pe.system = ?
                    GROUP BY ps.step_name
                    ORDER BY avg_duration DESC
                """, conn, params=(system,))
            else:
                df_steps = pd.read_sql_query("""
                    SELECT step_name, AVG(duration_ms) as avg_duration,
                           COUNT(*) as total_operations
                    FROM pipeline_steps
                    GROUP BY step_name
                    ORDER BY avg_duration DESC
                """, conn)
            
            if not df_steps.empty:
                plt.figure(figsize=(12, 8))
                bars = plt.bar(df_steps['step_name'], df_steps['avg_duration'])
                plt.title(f'Average Step Duration - {system or "All Systems"}')
                plt.xlabel('Pipeline Step')
                plt.ylabel('Average Duration (ms)')
                plt.xticks(rotation=45, ha='right')
                plt.grid(True, alpha=0.3)
                
                # Add value labels on bars
                for bar in bars:
                    height = bar.get_height()
                    plt.text(bar.get_x() + bar.get_width()/2., height,
                            f'{height:.0f}ms', ha='center', va='bottom')
                
                plt.tight_layout()
                plt.savefig(output_path / 'step_performance.png', dpi=300, bbox_inches='tight')
                plt.close()
            
            conn.close()
            logger.info(f"Generated visualizations in {output_path}")
            
        except Exception as e:
            logger.error(f"Failed to generate visualizations: {e}")


# Global analytics instance
analytics = PipelineAnalytics()


def get_analytics() -> PipelineAnalytics:
    """Get the global analytics instance."""
    return analytics


if __name__ == "__main__":
    # Example usage
    analytics = PipelineAnalytics()
    
    # Analyze performance
    performance = analytics.analyze_pipeline_performance("electrical")
    if performance:
        print(f"Success rate: {performance.success_rate:.1f}%")
        print(f"Average execution time: {performance.avg_execution_time:.1f}s")
        print(f"Bottlenecks: {performance.bottleneck_operations}")
    
    # Generate insights
    insights = analytics.generate_insights("electrical")
    for insight in insights:
        print(f"Insight: {insight.title} - {insight.description}")
    
    # Create performance report
    report = analytics.create_performance_report("electrical")
    print(json.dumps(report, indent=2))
    
    # Generate visualizations
    analytics.generate_visualizations("electrical") 