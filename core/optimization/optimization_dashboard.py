"""
Optimization Performance Analytics Dashboard.

Advanced analytics, monitoring, and visualization system for optimization
performance, insights generation, and decision support.
"""

import time
import logging
import json
import statistics
from typing import Dict, Any, List, Optional, Tuple, Set, Union
from dataclasses import dataclass, field, asdict
from enum import Enum
from collections import defaultdict, deque
import datetime
import math

# Import optimization components
from .optimization_core import (
    OptimizationResult, OptimizationMetrics, OptimizationConfiguration,
    OptimizationStatus, OptimizationType
)
from .multi_objective import ParetoFrontier, ParetoSolution
from .design_explorer import DesignPoint, SensitivityResult, OptimizationInsights

logger = logging.getLogger(__name__)


class DashboardMode(Enum):
    """Dashboard display modes."""
    
    REAL_TIME = "real_time"
    HISTORICAL = "historical"
    COMPARATIVE = "comparative"
    DETAILED = "detailed"
    SUMMARY = "summary"


class MetricType(Enum):
    """Types of optimization metrics."""
    
    PERFORMANCE = "performance"
    CONVERGENCE = "convergence"
    SOLUTION_QUALITY = "solution_quality"
    RESOURCE_USAGE = "resource_usage"
    ALGORITHM_EFFECTIVENESS = "algorithm_effectiveness"


@dataclass
class OptimizationSession:
    """Single optimization session data."""
    
    session_id: str
    start_time: float
    end_time: Optional[float] = None
    
    # Problem configuration
    problem_description: str = ""
    algorithm_used: str = ""
    variables_count: int = 0
    objectives_count: int = 0
    constraints_count: int = 0
    
    # Results
    optimization_result: Optional[OptimizationResult] = None
    final_metrics: Optional[OptimizationMetrics] = None
    
    # Performance tracking
    convergence_history: List[Dict[str, float]] = field(default_factory=list)
    resource_usage: Dict[str, List[float]] = field(default_factory=dict)
    
    # Analysis results
    sensitivity_analysis: Optional[SensitivityResult] = None
    pareto_frontier: Optional[ParetoFrontier] = None
    optimization_insights: Optional[OptimizationInsights] = None
    
    def get_duration(self) -> float:
        """Get optimization session duration."""
        end = self.end_time or time.time()
        return end - self.start_time
    
    def is_active(self) -> bool:
        """Check if optimization session is still active."""
        return self.end_time is None
    
    def get_success_rate(self) -> float:
        """Get optimization success rate."""
        if not self.optimization_result:
            return 0.0
        
        if self.optimization_result.optimization_status in [
            OptimizationStatus.CONVERGED, OptimizationStatus.MAX_TIME
        ]:
            return 1.0 if self.optimization_result.is_feasible else 0.5
        
        return 0.0


@dataclass
class PerformanceMetrics:
    """Aggregated performance metrics."""
    
    # Timing metrics
    average_optimization_time: float = 0.0
    median_optimization_time: float = 0.0
    fastest_optimization: float = 0.0
    slowest_optimization: float = 0.0
    
    # Success metrics
    success_rate: float = 0.0
    convergence_rate: float = 0.0
    feasibility_rate: float = 0.0
    
    # Solution quality
    average_objective_improvement: float = 0.0
    best_objective_value: float = 0.0
    solution_diversity_score: float = 0.0
    
    # Algorithm performance
    average_iterations: float = 0.0
    average_evaluations: float = 0.0
    evaluations_per_second: float = 0.0
    
    # Resource usage
    peak_memory_usage_mb: float = 0.0
    average_cpu_utilization: float = 0.0
    parallel_efficiency: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary."""
        return asdict(self)


@dataclass
class AlgorithmComparison:
    """Comparison of different optimization algorithms."""
    
    algorithms_compared: List[str] = field(default_factory=list)
    performance_by_algorithm: Dict[str, PerformanceMetrics] = field(default_factory=dict)
    
    # Statistical comparisons
    time_performance_ranking: List[Tuple[str, float]] = field(default_factory=list)
    success_rate_ranking: List[Tuple[str, float]] = field(default_factory=list)
    solution_quality_ranking: List[Tuple[str, float]] = field(default_factory=list)
    
    # Recommendations
    best_overall_algorithm: str = ""
    algorithm_recommendations: Dict[str, List[str]] = field(default_factory=dict)
    
    def generate_comparison_report(self) -> str:
        """Generate algorithm comparison report."""
        
        lines = []
        lines.append("ALGORITHM PERFORMANCE COMPARISON")
        lines.append("=" * 40)
        lines.append("")
        
        # Time performance
        if self.time_performance_ranking:
            lines.append("Time Performance (fastest to slowest):")
            for i, (algorithm, time_score) in enumerate(self.time_performance_ranking, 1):
                lines.append(f"  {i}. {algorithm}: {time_score:.2f}s avg")
            lines.append("")
        
        # Success rate
        if self.success_rate_ranking:
            lines.append("Success Rate (highest to lowest):")
            for i, (algorithm, success_rate) in enumerate(self.success_rate_ranking, 1):
                lines.append(f"  {i}. {algorithm}: {success_rate:.1%}")
            lines.append("")
        
        # Recommendations
        if self.best_overall_algorithm:
            lines.append(f"Best Overall Algorithm: {self.best_overall_algorithm}")
        
        if self.algorithm_recommendations:
            lines.append("\nAlgorithm Recommendations:")
            for scenario, algorithms in self.algorithm_recommendations.items():
                lines.append(f"  {scenario}: {', '.join(algorithms)}")
        
        return "\n".join(lines)


class OptimizationDashboard:
    """
    Optimization performance analytics dashboard.
    
    Provides real-time monitoring, historical analysis, and performance insights
    for optimization algorithms and results.
    """
    
    def __init__(self):
        # Session management
        self.active_sessions: Dict[str, OptimizationSession] = {}
        self.completed_sessions: List[OptimizationSession] = []
        self.session_history_limit = 1000
        
        # Real-time monitoring
        self.real_time_metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
        self.monitoring_interval = 1.0  # seconds
        self.last_update_time = time.time()
        
        # Performance tracking
        self.aggregated_metrics = PerformanceMetrics()
        self.algorithm_comparisons: Dict[str, AlgorithmComparison] = {}
        
        # Dashboard configuration
        self.dashboard_mode = DashboardMode.REAL_TIME
        self.auto_refresh = True
        self.refresh_interval = 5.0  # seconds
        
        logger.info("Initialized OptimizationDashboard")
    
    def start_optimization_session(self, 
                                 session_id: str,
                                 problem_description: str,
                                 algorithm: str,
                                 variables_count: int,
                                 objectives_count: int,
                                 constraints_count: int = 0) -> None:
        """Start tracking a new optimization session."""
        
        session = OptimizationSession(
            session_id=session_id,
            start_time=time.time(),
            problem_description=problem_description,
            algorithm_used=algorithm,
            variables_count=variables_count,
            objectives_count=objectives_count,
            constraints_count=constraints_count
        )
        
        self.active_sessions[session_id] = session
        
        logger.info(f"Started tracking optimization session: {session_id}")
    
    def update_session_metrics(self, 
                             session_id: str,
                             metrics: OptimizationMetrics) -> None:
        """Update real-time metrics for optimization session."""
        
        if session_id not in self.active_sessions:
            logger.warning(f"Unknown session ID: {session_id}")
            return
        
        session = self.active_sessions[session_id]
        
        # Update convergence history
        convergence_entry = {
            'iteration': metrics.current_iteration,
            'objective_value': metrics.best_objective_value,
            'time': time.time() - session.start_time,
            'evaluations': metrics.total_evaluations
        }
        session.convergence_history.append(convergence_entry)
        
        # Update resource usage
        if 'memory_usage' not in session.resource_usage:
            session.resource_usage['memory_usage'] = []
        if 'cpu_utilization' not in session.resource_usage:
            session.resource_usage['cpu_utilization'] = []
        
        session.resource_usage['memory_usage'].append(metrics.memory_usage_mb)
        session.resource_usage['cpu_utilization'].append(metrics.cpu_utilization)
        
        # Update real-time dashboard metrics
        current_time = time.time()
        self.real_time_metrics['objective_value'].append(metrics.best_objective_value)
        self.real_time_metrics['iterations'].append(metrics.current_iteration)
        self.real_time_metrics['evaluations_per_second'].append(metrics.evaluations_per_second)
        self.real_time_metrics['memory_usage'].append(metrics.memory_usage_mb)
        self.real_time_metrics['cpu_utilization'].append(metrics.cpu_utilization)
        self.real_time_metrics['timestamp'].append(current_time)
        
        self.last_update_time = current_time
    
    def complete_optimization_session(self, 
                                    session_id: str,
                                    optimization_result: OptimizationResult,
                                    final_metrics: OptimizationMetrics) -> None:
        """Complete optimization session and store results."""
        
        if session_id not in self.active_sessions:
            logger.warning(f"Unknown session ID: {session_id}")
            return
        
        session = self.active_sessions[session_id]
        session.end_time = time.time()
        session.optimization_result = optimization_result
        session.final_metrics = final_metrics
        
        # Move to completed sessions
        self.completed_sessions.append(session)
        del self.active_sessions[session_id]
        
        # Limit history size
        if len(self.completed_sessions) > self.session_history_limit:
            self.completed_sessions = self.completed_sessions[-self.session_history_limit:]
        
        # Update aggregated metrics
        self._update_aggregated_metrics()
        
        logger.info(f"Completed optimization session: {session_id}")
    
    def add_sensitivity_analysis(self, 
                               session_id: str,
                               sensitivity_result: SensitivityResult) -> None:
        """Add sensitivity analysis results to session."""
        
        # Check active sessions first
        if session_id in self.active_sessions:
            self.active_sessions[session_id].sensitivity_analysis = sensitivity_result
            return
        
        # Check completed sessions
        for session in self.completed_sessions:
            if session.session_id == session_id:
                session.sensitivity_analysis = sensitivity_result
                return
        
        logger.warning(f"Session not found for sensitivity analysis: {session_id}")
    
    def add_pareto_frontier(self, 
                          session_id: str,
                          pareto_frontier: ParetoFrontier) -> None:
        """Add Pareto frontier results to session."""
        
        # Check active sessions first
        if session_id in self.active_sessions:
            self.active_sessions[session_id].pareto_frontier = pareto_frontier
            return
        
        # Check completed sessions
        for session in self.completed_sessions:
            if session.session_id == session_id:
                session.pareto_frontier = pareto_frontier
                return
        
        logger.warning(f"Session not found for Pareto frontier: {session_id}")
    
    def generate_performance_report(self, 
                                  mode: DashboardMode = DashboardMode.SUMMARY,
                                  time_range_hours: Optional[int] = None) -> str:
        """Generate comprehensive performance report."""
        
        # Filter sessions by time range if specified
        sessions = self._filter_sessions_by_time(time_range_hours)
        
        if not sessions:
            return "No optimization sessions found in the specified time range."
        
        lines = []
        lines.append("OPTIMIZATION PERFORMANCE REPORT")
        lines.append("=" * 50)
        lines.append(f"Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        if time_range_hours:
            lines.append(f"Time Range: Last {time_range_hours} hours")
        lines.append(f"Sessions Analyzed: {len(sessions)}")
        lines.append("")
        
        if mode == DashboardMode.SUMMARY:
            lines.extend(self._generate_summary_report(sessions))
        elif mode == DashboardMode.DETAILED:
            lines.extend(self._generate_detailed_report(sessions))
        elif mode == DashboardMode.COMPARATIVE:
            lines.extend(self._generate_comparative_report(sessions))
        elif mode == DashboardMode.HISTORICAL:
            lines.extend(self._generate_historical_report(sessions))
        
        return "\n".join(lines)
    
    def get_real_time_dashboard_data(self) -> Dict[str, Any]:
        """Get real-time dashboard data for visualization."""
        
        dashboard_data = {
            'active_sessions_count': len(self.active_sessions),
            'total_sessions_completed': len(self.completed_sessions),
            'last_update_time': self.last_update_time,
            'real_time_metrics': {},
            'active_session_details': []
        }
        
        # Convert real-time metrics to lists
        for metric_name, values in self.real_time_metrics.items():
            dashboard_data['real_time_metrics'][metric_name] = list(values)
        
        # Active session details
        for session_id, session in self.active_sessions.items():
            session_data = {
                'session_id': session_id,
                'algorithm': session.algorithm_used,
                'duration': session.get_duration(),
                'variables_count': session.variables_count,
                'objectives_count': session.objectives_count,
                'current_iteration': len(session.convergence_history),
                'latest_objective': session.convergence_history[-1]['objective_value'] if session.convergence_history else None
            }
            dashboard_data['active_session_details'].append(session_data)
        
        return dashboard_data
    
    def analyze_algorithm_performance(self) -> AlgorithmComparison:
        """Analyze and compare performance of different algorithms."""
        
        sessions = self.completed_sessions
        
        if not sessions:
            return AlgorithmComparison()
        
        # Group sessions by algorithm
        sessions_by_algorithm = defaultdict(list)
        for session in sessions:
            if session.optimization_result:
                sessions_by_algorithm[session.algorithm_used].append(session)
        
        if len(sessions_by_algorithm) < 2:
            return AlgorithmComparison()
        
        comparison = AlgorithmComparison()
        comparison.algorithms_compared = list(sessions_by_algorithm.keys())
        
        # Calculate performance metrics for each algorithm
        for algorithm, algorithm_sessions in sessions_by_algorithm.items():
            metrics = self._calculate_algorithm_metrics(algorithm_sessions)
            comparison.performance_by_algorithm[algorithm] = metrics
        
        # Create rankings
        comparison.time_performance_ranking = sorted(
            [(algo, metrics.average_optimization_time) 
             for algo, metrics in comparison.performance_by_algorithm.items()],
            key=lambda x: x[1]
        )
        
        comparison.success_rate_ranking = sorted(
            [(algo, metrics.success_rate)
             for algo, metrics in comparison.performance_by_algorithm.items()],
            key=lambda x: x[1], reverse=True
        )
        
        comparison.solution_quality_ranking = sorted(
            [(algo, metrics.average_objective_improvement)
             for algo, metrics in comparison.performance_by_algorithm.items()],
            key=lambda x: x[1], reverse=True
        )
        
        # Determine best overall algorithm (weighted score)
        algorithm_scores = {}
        for algorithm in comparison.algorithms_compared:
            metrics = comparison.performance_by_algorithm[algorithm]
            
            # Normalize and weight different criteria
            time_score = 1.0 / max(metrics.average_optimization_time, 0.1)  # Faster is better
            success_score = metrics.success_rate  # Higher is better
            quality_score = metrics.average_objective_improvement  # Higher is better
            
            # Weighted overall score
            overall_score = (0.3 * time_score + 0.4 * success_score + 0.3 * quality_score)
            algorithm_scores[algorithm] = overall_score
        
        comparison.best_overall_algorithm = max(algorithm_scores, key=algorithm_scores.get)
        
        # Generate recommendations
        comparison.algorithm_recommendations = self._generate_algorithm_recommendations(comparison)
        
        return comparison
    
    def generate_optimization_insights(self, session_id: str) -> Optional[OptimizationInsights]:
        """Generate insights for specific optimization session."""
        
        # Find session
        session = None
        if session_id in self.active_sessions:
            session = self.active_sessions[session_id]
        else:
            for s in self.completed_sessions:
                if s.session_id == session_id:
                    session = s
                    break
        
        if not session or not session.optimization_result:
            return None
        
        insights = OptimizationInsights()
        
        # Analyze convergence behavior
        if session.convergence_history:
            insights.convergence_predictions = self._analyze_convergence_behavior(session)
        
        # Determine optimization difficulty
        insights.optimization_difficulty = self._assess_optimization_difficulty(session)
        
        # Generate recommendations
        insights.algorithm_recommendations = self._generate_session_recommendations(session)
        
        # Performance predictions
        insights.expected_runtime = session.get_duration()
        
        # Critical variable analysis
        if session.sensitivity_analysis:
            insights.critical_variables = self._extract_critical_variables(session.sensitivity_analysis)
        
        return insights
    
    def export_dashboard_data(self, format: str = "json") -> str:
        """Export dashboard data in specified format."""
        
        data = {
            'export_time': time.time(),
            'active_sessions': len(self.active_sessions),
            'completed_sessions': len(self.completed_sessions),
            'aggregated_metrics': self.aggregated_metrics.to_dict(),
            'session_details': []
        }
        
        # Add session details
        for session in self.completed_sessions[-50:]:  # Last 50 sessions
            session_data = {
                'session_id': session.session_id,
                'algorithm': session.algorithm_used,
                'duration': session.get_duration(),
                'success_rate': session.get_success_rate(),
                'variables_count': session.variables_count,
                'objectives_count': session.objectives_count
            }
            
            if session.optimization_result:
                session_data.update({
                    'final_status': session.optimization_result.optimization_status.value,
                    'iterations': session.optimization_result.iteration_count,
                    'evaluations': session.optimization_result.evaluation_count,
                    'is_feasible': session.optimization_result.is_feasible
                })
            
            data['session_details'].append(session_data)
        
        if format.lower() == "json":
            return json.dumps(data, indent=2, default=str)
        else:
            return str(data)
    
    def _filter_sessions_by_time(self, time_range_hours: Optional[int]) -> List[OptimizationSession]:
        """Filter sessions by time range."""
        
        if time_range_hours is None:
            return self.completed_sessions
        
        cutoff_time = time.time() - (time_range_hours * 3600)
        
        return [session for session in self.completed_sessions 
                if session.start_time >= cutoff_time]
    
    def _update_aggregated_metrics(self) -> None:
        """Update aggregated performance metrics."""
        
        sessions = self.completed_sessions
        
        if not sessions:
            return
        
        # Calculate timing metrics
        durations = [session.get_duration() for session in sessions]
        self.aggregated_metrics.average_optimization_time = statistics.mean(durations)
        self.aggregated_metrics.median_optimization_time = statistics.median(durations)
        self.aggregated_metrics.fastest_optimization = min(durations)
        self.aggregated_metrics.slowest_optimization = max(durations)
        
        # Calculate success metrics
        successful_sessions = sum(1 for session in sessions if session.get_success_rate() > 0.5)
        self.aggregated_metrics.success_rate = successful_sessions / len(sessions)
        
        converged_sessions = sum(1 for session in sessions 
                               if (session.optimization_result and 
                                   session.optimization_result.optimization_status == OptimizationStatus.CONVERGED))
        self.aggregated_metrics.convergence_rate = converged_sessions / len(sessions)
        
        feasible_sessions = sum(1 for session in sessions
                              if (session.optimization_result and 
                                  session.optimization_result.is_feasible))
        self.aggregated_metrics.feasibility_rate = feasible_sessions / len(sessions)
        
        # Calculate algorithm performance
        iterations = [session.optimization_result.iteration_count for session in sessions 
                     if session.optimization_result]
        if iterations:
            self.aggregated_metrics.average_iterations = statistics.mean(iterations)
        
        evaluations = [session.optimization_result.evaluation_count for session in sessions
                      if session.optimization_result]
        if evaluations:
            self.aggregated_metrics.average_evaluations = statistics.mean(evaluations)
            
            total_time = sum(durations)
            if total_time > 0:
                self.aggregated_metrics.evaluations_per_second = sum(evaluations) / total_time
        
        # Resource usage
        all_memory_usage = []
        all_cpu_usage = []
        
        for session in sessions:
            if 'memory_usage' in session.resource_usage:
                all_memory_usage.extend(session.resource_usage['memory_usage'])
            if 'cpu_utilization' in session.resource_usage:
                all_cpu_usage.extend(session.resource_usage['cpu_utilization'])
        
        if all_memory_usage:
            self.aggregated_metrics.peak_memory_usage_mb = max(all_memory_usage)
        if all_cpu_usage:
            self.aggregated_metrics.average_cpu_utilization = statistics.mean(all_cpu_usage)
    
    def _calculate_algorithm_metrics(self, sessions: List[OptimizationSession]) -> PerformanceMetrics:
        """Calculate performance metrics for specific algorithm."""
        
        metrics = PerformanceMetrics()
        
        if not sessions:
            return metrics
        
        # Timing
        durations = [session.get_duration() for session in sessions]
        metrics.average_optimization_time = statistics.mean(durations)
        metrics.median_optimization_time = statistics.median(durations)
        metrics.fastest_optimization = min(durations)
        metrics.slowest_optimization = max(durations)
        
        # Success rates
        success_rates = [session.get_success_rate() for session in sessions]
        metrics.success_rate = statistics.mean(success_rates)
        
        converged_count = sum(1 for session in sessions
                            if (session.optimization_result and 
                                session.optimization_result.optimization_status == OptimizationStatus.CONVERGED))
        metrics.convergence_rate = converged_count / len(sessions)
        
        feasible_count = sum(1 for session in sessions
                           if (session.optimization_result and session.optimization_result.is_feasible))
        metrics.feasibility_rate = feasible_count / len(sessions)
        
        # Algorithm performance
        iterations = [session.optimization_result.iteration_count for session in sessions
                     if session.optimization_result]
        if iterations:
            metrics.average_iterations = statistics.mean(iterations)
        
        evaluations = [session.optimization_result.evaluation_count for session in sessions
                      if session.optimization_result]
        if evaluations:
            metrics.average_evaluations = statistics.mean(evaluations)
            
            total_time = sum(durations)
            if total_time > 0:
                metrics.evaluations_per_second = sum(evaluations) / total_time
        
        return metrics
    
    def _generate_summary_report(self, sessions: List[OptimizationSession]) -> List[str]:
        """Generate summary performance report."""
        
        lines = []
        lines.append("SUMMARY")
        lines.append("-" * 20)
        
        if not sessions:
            lines.append("No sessions to analyze.")
            return lines
        
        # Overall statistics
        total_duration = sum(session.get_duration() for session in sessions)
        avg_duration = total_duration / len(sessions)
        success_rate = sum(session.get_success_rate() for session in sessions) / len(sessions)
        
        lines.append(f"Total Sessions: {len(sessions)}")
        lines.append(f"Average Duration: {avg_duration:.1f}s")
        lines.append(f"Success Rate: {success_rate:.1%}")
        lines.append("")
        
        # Algorithm breakdown
        algorithm_counts = defaultdict(int)
        for session in sessions:
            algorithm_counts[session.algorithm_used] += 1
        
        if algorithm_counts:
            lines.append("Algorithms Used:")
            for algorithm, count in sorted(algorithm_counts.items(), key=lambda x: x[1], reverse=True):
                percentage = (count / len(sessions)) * 100
                lines.append(f"  {algorithm}: {count} ({percentage:.1f}%)")
            lines.append("")
        
        # Problem complexity
        avg_variables = statistics.mean(session.variables_count for session in sessions)
        avg_objectives = statistics.mean(session.objectives_count for session in sessions)
        
        lines.append(f"Average Problem Size:")
        lines.append(f"  Variables: {avg_variables:.1f}")
        lines.append(f"  Objectives: {avg_objectives:.1f}")
        
        return lines
    
    def _generate_detailed_report(self, sessions: List[OptimizationSession]) -> List[str]:
        """Generate detailed performance report."""
        
        lines = []
        lines.append("DETAILED ANALYSIS")
        lines.append("-" * 25)
        lines.append("")
        
        # Performance metrics
        lines.append("Performance Metrics:")
        lines.append(f"  Average Time: {self.aggregated_metrics.average_optimization_time:.2f}s")
        lines.append(f"  Median Time: {self.aggregated_metrics.median_optimization_time:.2f}s")
        lines.append(f"  Success Rate: {self.aggregated_metrics.success_rate:.1%}")
        lines.append(f"  Convergence Rate: {self.aggregated_metrics.convergence_rate:.1%}")
        lines.append(f"  Feasibility Rate: {self.aggregated_metrics.feasibility_rate:.1%}")
        lines.append("")
        
        # Resource usage
        lines.append("Resource Usage:")
        lines.append(f"  Peak Memory: {self.aggregated_metrics.peak_memory_usage_mb:.1f} MB")
        lines.append(f"  Average CPU: {self.aggregated_metrics.average_cpu_utilization:.1f}%")
        lines.append(f"  Evaluations/sec: {self.aggregated_metrics.evaluations_per_second:.1f}")
        lines.append("")
        
        return lines
    
    def _generate_comparative_report(self, sessions: List[OptimizationSession]) -> List[str]:
        """Generate comparative algorithm report."""
        
        lines = []
        lines.append("ALGORITHM COMPARISON")
        lines.append("-" * 25)
        lines.append("")
        
        comparison = self.analyze_algorithm_performance()
        lines.append(comparison.generate_comparison_report())
        
        return lines
    
    def _generate_historical_report(self, sessions: List[OptimizationSession]) -> List[str]:
        """Generate historical trend report."""
        
        lines = []
        lines.append("HISTORICAL TRENDS")
        lines.append("-" * 20)
        lines.append("")
        
        if len(sessions) < 10:
            lines.append("Insufficient data for trend analysis (minimum 10 sessions required).")
            return lines
        
        # Time-based analysis
        sessions_by_week = defaultdict(list)
        
        for session in sessions:
            week_key = int(session.start_time) // (7 * 24 * 3600)  # Week number
            sessions_by_week[week_key].append(session)
        
        if len(sessions_by_week) >= 2:
            lines.append("Weekly Performance Trends:")
            
            for week_key in sorted(sessions_by_week.keys()):
                week_sessions = sessions_by_week[week_key]
                avg_time = statistics.mean(s.get_duration() for s in week_sessions)
                success_rate = statistics.mean(s.get_success_rate() for s in week_sessions)
                
                week_date = datetime.datetime.fromtimestamp(week_key * 7 * 24 * 3600).strftime('%Y-%m-%d')
                lines.append(f"  Week {week_date}: {len(week_sessions)} sessions, "
                           f"{avg_time:.1f}s avg, {success_rate:.1%} success")
        
        return lines
    
    def _generate_algorithm_recommendations(self, comparison: AlgorithmComparison) -> Dict[str, List[str]]:
        """Generate algorithm recommendations based on comparison."""
        
        recommendations = {}
        
        # Fast optimization scenarios
        if comparison.time_performance_ranking:
            fastest_algorithms = [algo for algo, _ in comparison.time_performance_ranking[:2]]
            recommendations["Fast optimization needed"] = fastest_algorithms
        
        # High success rate scenarios
        if comparison.success_rate_ranking:
            reliable_algorithms = [algo for algo, rate in comparison.success_rate_ranking[:2] if rate > 0.8]
            if reliable_algorithms:
                recommendations["Reliability critical"] = reliable_algorithms
        
        # Quality optimization scenarios
        if comparison.solution_quality_ranking:
            quality_algorithms = [algo for algo, _ in comparison.solution_quality_ranking[:2]]
            recommendations["Solution quality critical"] = quality_algorithms
        
        return recommendations
    
    def _analyze_convergence_behavior(self, session: OptimizationSession) -> Dict[str, float]:
        """Analyze convergence behavior and make predictions."""
        
        if not session.convergence_history or len(session.convergence_history) < 5:
            return {}
        
        # Extract objective values over time
        objective_values = [entry['objective_value'] for entry in session.convergence_history]
        
        # Calculate convergence rate
        early_values = objective_values[:len(objective_values)//3]
        late_values = objective_values[-len(objective_values)//3:]
        
        if early_values and late_values:
            early_avg = statistics.mean(early_values)
            late_avg = statistics.mean(late_values)
            
            if early_avg != 0:
                improvement_rate = abs(late_avg - early_avg) / abs(early_avg)
            else:
                improvement_rate = 0.0
        else:
            improvement_rate = 0.0
        
        return {
            'convergence_rate': improvement_rate,
            'predicted_final_value': late_values[-1] if late_values else 0.0
        }
    
    def _assess_optimization_difficulty(self, session: OptimizationSession) -> str:
        """Assess optimization problem difficulty."""
        
        # Factors that indicate difficulty
        difficulty_score = 0
        
        # Problem size
        if session.variables_count > 50:
            difficulty_score += 2
        elif session.variables_count > 10:
            difficulty_score += 1
        
        # Multi-objective
        if session.objectives_count > 1:
            difficulty_score += 1
        
        # Constraints
        if session.constraints_count > 10:
            difficulty_score += 2
        elif session.constraints_count > 0:
            difficulty_score += 1
        
        # Convergence behavior
        if session.optimization_result:
            if session.optimization_result.optimization_status == OptimizationStatus.MAX_ITERATIONS:
                difficulty_score += 2
            elif session.optimization_result.iteration_count > 1000:
                difficulty_score += 1
        
        # Classification
        if difficulty_score >= 5:
            return "hard"
        elif difficulty_score >= 3:
            return "medium"
        else:
            return "easy"
    
    def _generate_session_recommendations(self, session: OptimizationSession) -> List[str]:
        """Generate recommendations for optimization session."""
        
        recommendations = []
        
        if not session.optimization_result:
            recommendations.append("Session incomplete - unable to provide recommendations")
            return recommendations
        
        # Time-based recommendations
        if session.get_duration() > 300:  # More than 5 minutes
            recommendations.append("Consider using faster algorithm or reducing problem size for quicker results")
        
        # Success-based recommendations
        if not session.optimization_result.is_feasible:
            recommendations.append("Problem appears infeasible - consider relaxing constraints")
        
        # Convergence-based recommendations
        if session.optimization_result.optimization_status == OptimizationStatus.MAX_ITERATIONS:
            recommendations.append("Algorithm did not converge - consider increasing iteration limit or trying different algorithm")
        
        # Algorithm-specific recommendations
        if session.algorithm_used == "genetic_algorithm" and session.variables_count < 5:
            recommendations.append("Small problem size - simulated annealing might be more efficient")
        
        return recommendations
    
    def _extract_critical_variables(self, sensitivity_result: SensitivityResult) -> Dict[str, List[Tuple[str, float]]]:
        """Extract critical variables from sensitivity analysis."""
        
        critical_vars = {}
        
        # From Sobol indices
        for obj_name, var_sensitivities in sensitivity_result.sobol_indices.items():
            top_vars = sorted(var_sensitivities.items(), key=lambda x: abs(x[1]), reverse=True)[:5]
            critical_vars[obj_name] = top_vars
        
        # From Morris method if available
        if not critical_vars:
            for obj_name, var_sensitivities in sensitivity_result.morris_mu_star.items():
                top_vars = sorted(var_sensitivities.items(), key=lambda x: abs(x[1]), reverse=True)[:5]
                critical_vars[obj_name] = top_vars
        
        return critical_vars


class OptimizationVisualizer:
    """
    Visualization tools for optimization results and dashboard data.
    
    Provides methods to generate visualization data for charts, plots,
    and interactive dashboards.
    """
    
    def __init__(self):
        self.visualization_types = [
            "convergence_plot",
            "pareto_frontier",
            "sensitivity_chart",
            "performance_comparison",
            "resource_usage_timeline"
        ]
    
    def generate_convergence_plot_data(self, session: OptimizationSession) -> Dict[str, Any]:
        """Generate data for convergence plot visualization."""
        
        if not session.convergence_history:
            return {}
        
        plot_data = {
            'x_values': [entry['iteration'] for entry in session.convergence_history],
            'y_values': [entry['objective_value'] for entry in session.convergence_history],
            'title': f"Convergence Plot - {session.session_id}",
            'x_label': "Iteration",
            'y_label': "Objective Value",
            'algorithm': session.algorithm_used
        }
        
        return plot_data
    
    def generate_pareto_frontier_data(self, pareto_frontier: ParetoFrontier) -> Dict[str, Any]:
        """Generate data for Pareto frontier visualization."""
        
        if not pareto_frontier.solutions or len(pareto_frontier.objective_names) < 2:
            return {}
        
        # For 2D visualization
        obj1, obj2 = pareto_frontier.objective_names[:2]
        
        plot_data = {
            'x_values': [sol.objective_values.get(obj1, 0) for sol in pareto_frontier.solutions],
            'y_values': [sol.objective_values.get(obj2, 0) for sol in pareto_frontier.solutions],
            'title': "Pareto Frontier",
            'x_label': obj1,
            'y_label': obj2,
            'solution_count': len(pareto_frontier.solutions)
        }
        
        return plot_data
    
    def generate_performance_comparison_data(self, comparison: AlgorithmComparison) -> Dict[str, Any]:
        """Generate data for algorithm performance comparison."""
        
        if not comparison.algorithms_compared:
            return {}
        
        comparison_data = {
            'algorithms': comparison.algorithms_compared,
            'time_performance': [metrics.average_optimization_time 
                               for metrics in comparison.performance_by_algorithm.values()],
            'success_rates': [metrics.success_rate 
                            for metrics in comparison.performance_by_algorithm.values()],
            'title': "Algorithm Performance Comparison"
        }
        
        return comparison_data


logger.info("Optimization dashboard and analytics system initialized")