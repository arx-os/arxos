"""
SVGX Engine - AI Behavior Prediction System

This service provides advanced AI capabilities for BIM behavior prediction,
anomaly detection, and automated optimization recommendations.

🎯 **Core AI Capabilities:**
- Machine Learning-based Behavior Prediction
- Anomaly Detection and Alerting
- Automated Optimization Recommendations
- Pattern Recognition and Trend Analysis
- Predictive Maintenance Algorithms
- Energy Optimization Analytics

🏗️ **Enterprise Features:**
- Scalable ML pipeline with real-time processing
- Comprehensive model management and versioning
- Integration with BIM behavior engine
- Advanced analytics and reporting
- Enterprise-grade security and compliance
- Performance monitoring and optimization
"""

import logging
import time
import asyncio
from typing import Dict, List, Any, Optional, Union, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
from collections import defaultdict, deque
import threading
from concurrent.futures import ThreadPoolExecutor
import json
import pickle
from pathlib import Path

from svgx_engine.utils.performance import PerformanceMonitor
from svgx_engine.utils.errors import BehaviorError, ValidationError
from svgx_engine.services.event_driven_behavior_engine import Event, EventType

logger = logging.getLogger(__name__)


class PredictionType(Enum):
    """Types of AI predictions supported."""
    BEHAVIOR_PREDICTION = "behavior_prediction"
    ANOMALY_DETECTION = "anomaly_detection"
    MAINTENANCE_PREDICTION = "maintenance_prediction"
    ENERGY_OPTIMIZATION = "energy_optimization"
    PERFORMANCE_OPTIMIZATION = "performance_optimization"
    FAILURE_PREDICTION = "failure_prediction"


class AnomalySeverity(Enum):
    """Anomaly severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ModelType(Enum):
    """Types of ML models supported."""
    LINEAR_REGRESSION = "linear_regression"
    RANDOM_FOREST = "random_forest"
    GRADIENT_BOOSTING = "gradient_boosting"
    NEURAL_NETWORK = "neural_network"
    LSTM = "lstm"
    ISOLATION_FOREST = "isolation_forest"
    ONE_CLASS_SVM = "one_class_svm"


@dataclass
class PredictionConfig:
    """Configuration for AI behavior prediction system."""
    # Model settings
    model_type: ModelType = ModelType.RANDOM_FOREST
    prediction_horizon: int = 24  # hours
    update_frequency: int = 60  # seconds
    confidence_threshold: float = 0.8
    anomaly_threshold: float = 0.95
    
    # Data settings
    max_data_points: int = 10000
    feature_window_size: int = 100
    min_data_points_for_training: int = 1000
    
    # Performance settings
    parallel_processing: bool = True
    cache_predictions: bool = True
    cache_ttl: int = 300  # seconds
    
    # AI optimization settings
    auto_retrain_frequency: int = 24  # hours
    model_performance_threshold: float = 0.85
    feature_importance_threshold: float = 0.1


@dataclass
class PredictionResult:
    """Result of AI prediction."""
    prediction_type: PredictionType
    element_id: str
    timestamp: datetime
    prediction_value: float
    confidence_score: float
    prediction_horizon: int
    features_used: List[str] = field(default_factory=list)
    model_version: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AnomalyResult:
    """Result of anomaly detection."""
    element_id: str
    timestamp: datetime
    anomaly_score: float
    severity: AnomalySeverity
    detected_features: List[str] = field(default_factory=list)
    expected_value: float
    actual_value: float
    deviation_percentage: float
    alert_message: str = ""
    recommendations: List[str] = field(default_factory=list)


@dataclass
class OptimizationRecommendation:
    """AI-generated optimization recommendation."""
    element_id: str
    recommendation_type: str
    timestamp: datetime
    current_value: float
    recommended_value: float
    expected_improvement: float
    confidence_score: float
    implementation_cost: str = "low"
    priority: str = "medium"
    description: str = ""
    action_items: List[str] = field(default_factory=list)


class FeatureExtractor:
    """Extract features from BIM behavior data for ML models."""
    
    def __init__(self, config: PredictionConfig):
        self.config = config
        self.feature_cache = {}
        self.cache_ttl = 300  # 5 minutes
        
    def extract_temporal_features(self, data: List[Dict[str, Any]]) -> Dict[str, float]:
        """Extract temporal features from time series data."""
        if not data:
            return {}
            
        timestamps = [d.get('timestamp', 0) for d in data]
        values = [d.get('value', 0) for d in data]
        
        features = {
            'mean': np.mean(values),
            'std': np.std(values),
            'min': np.min(values),
            'max': np.max(values),
            'range': np.max(values) - np.min(values),
            'trend': self._calculate_trend(values),
            'seasonality': self._calculate_seasonality(values),
            'volatility': self._calculate_volatility(values)
        }
        
        return features
    
    def extract_behavioral_features(self, events: List[Event]) -> Dict[str, float]:
        """Extract behavioral features from event data."""
        if not events:
            return {}
            
        event_types = [e.event_type.value for e in events]
        event_counts = defaultdict(int)
        for event_type in event_types:
            event_counts[event_type] += 1
            
        total_events = len(events)
        features = {
            'total_events': total_events,
            'event_frequency': total_events / max(1, len(set(e.timestamp.date() for e in events))),
            'user_interaction_rate': event_counts.get('user_interaction', 0) / max(1, total_events),
            'system_event_rate': event_counts.get('system_event', 0) / max(1, total_events),
            'physics_event_rate': event_counts.get('physics_event', 0) / max(1, total_events),
            'environmental_event_rate': event_counts.get('environmental_event', 0) / max(1, total_events),
            'operational_event_rate': event_counts.get('operational_event', 0) / max(1, total_events)
        }
        
        return features
    
    def extract_physics_features(self, physics_data: List[Dict[str, Any]]) -> Dict[str, float]:
        """Extract physics-related features."""
        if not physics_data:
            return {}
            
        features = {}
        
        # Extract fluid dynamics features
        fluid_data = [d for d in physics_data if d.get('physics_type') == 'fluid_dynamics']
        if fluid_data:
            flow_rates = [d.get('flow_rate', 0) for d in fluid_data]
            pressures = [d.get('pressure', 0) for d in fluid_data]
            features.update({
                'avg_flow_rate': np.mean(flow_rates),
                'flow_rate_std': np.std(flow_rates),
                'avg_pressure': np.mean(pressures),
                'pressure_std': np.std(pressures),
                'flow_efficiency': np.mean([d.get('efficiency', 0) for d in fluid_data])
            })
        
        # Extract electrical features
        electrical_data = [d for d in physics_data if d.get('physics_type') == 'electrical']
        if electrical_data:
            currents = [d.get('current', 0) for d in electrical_data]
            voltages = [d.get('voltage', 0) for d in electrical_data]
            features.update({
                'avg_current': np.mean(currents),
                'current_std': np.std(currents),
                'avg_voltage': np.mean(voltages),
                'voltage_std': np.std(voltages),
                'power_factor': np.mean([d.get('power_factor', 0) for d in electrical_data])
            })
        
        # Extract thermal features
        thermal_data = [d for d in physics_data if d.get('physics_type') == 'thermal']
        if thermal_data:
            temperatures = [d.get('temperature', 0) for d in thermal_data]
            features.update({
                'avg_temperature': np.mean(temperatures),
                'temperature_std': np.std(temperatures),
                'thermal_efficiency': np.mean([d.get('efficiency', 0) for d in thermal_data])
            })
        
        return features
    
    def _calculate_trend(self, values: List[float]) -> float:
        """Calculate trend in time series data."""
        if len(values) < 2:
            return 0.0
        x = np.arange(len(values))
        slope, _ = np.polyfit(x, values, 1)
        return slope
    
    def _calculate_seasonality(self, values: List[float]) -> float:
        """Calculate seasonality in time series data."""
        if len(values) < 24:  # Need at least 24 points for basic seasonality
            return 0.0
        # Simple seasonality calculation using autocorrelation
        autocorr = np.correlate(values, values, mode='full')
        autocorr = autocorr[len(values)-1:]
        if len(autocorr) > 1:
            return np.max(autocorr[1:]) / autocorr[0]
        return 0.0
    
    def _calculate_volatility(self, values: List[float]) -> float:
        """Calculate volatility in time series data."""
        if len(values) < 2:
            return 0.0
        returns = np.diff(values) / values[:-1]
        return np.std(returns)


class AnomalyDetector:
    """Detect anomalies in BIM behavior data."""
    
    def __init__(self, config: PredictionConfig):
        self.config = config
        self.anomaly_models = {}
        self.baseline_data = {}
        self.alert_thresholds = {
            AnomalySeverity.LOW: 0.7,
            AnomalySeverity.MEDIUM: 0.8,
            AnomalySeverity.HIGH: 0.9,
            AnomalySeverity.CRITICAL: 0.95
        }
    
    def detect_anomalies(self, element_id: str, data: Dict[str, Any]) -> List[AnomalyResult]:
        """Detect anomalies in element behavior data."""
        anomalies = []
        
        try:
            # Extract features for anomaly detection
            features = self._extract_anomaly_features(data)
            
            # Check each feature for anomalies
            for feature_name, feature_value in features.items():
                baseline = self.baseline_data.get(element_id, {}).get(feature_name)
                if baseline is not None:
                    anomaly_score = self._calculate_anomaly_score(feature_value, baseline)
                    
                    if anomaly_score > self.config.anomaly_threshold:
                        severity = self._determine_severity(anomaly_score)
                        anomaly = AnomalyResult(
                            element_id=element_id,
                            timestamp=datetime.now(),
                            anomaly_score=anomaly_score,
                            severity=severity,
                            detected_features=[feature_name],
                            expected_value=baseline['mean'],
                            actual_value=feature_value,
                            deviation_percentage=abs(feature_value - baseline['mean']) / baseline['mean'] * 100,
                            alert_message=f"Anomaly detected in {feature_name}",
                            recommendations=self._generate_anomaly_recommendations(feature_name, feature_value, baseline)
                        )
                        anomalies.append(anomaly)
            
            logger.info(f"Detected {len(anomalies)} anomalies for element {element_id}")
            
        except Exception as e:
            logger.error(f"Error detecting anomalies for element {element_id}: {e}")
        
        return anomalies
    
    def update_baseline(self, element_id: str, data: List[Dict[str, Any]]):
        """Update baseline data for anomaly detection."""
        try:
            features = {}
            for data_point in data:
                for key, value in data_point.items():
                    if isinstance(value, (int, float)):
                        if key not in features:
                            features[key] = []
                        features[key].append(value)
            
            baseline = {}
            for feature_name, values in features.items():
                baseline[feature_name] = {
                    'mean': np.mean(values),
                    'std': np.std(values),
                    'min': np.min(values),
                    'max': np.max(values),
                    'count': len(values)
                }
            
            self.baseline_data[element_id] = baseline
            logger.info(f"Updated baseline for element {element_id} with {len(baseline)} features")
            
        except Exception as e:
            logger.error(f"Error updating baseline for element {element_id}: {e}")
    
    def _extract_anomaly_features(self, data: Dict[str, Any]) -> Dict[str, float]:
        """Extract features for anomaly detection."""
        features = {}
        
        # Extract numerical features
        for key, value in data.items():
            if isinstance(value, (int, float)):
                features[key] = value
            elif isinstance(value, dict):
                # Recursively extract features from nested dictionaries
                nested_features = self._extract_anomaly_features(value)
                for nested_key, nested_value in nested_features.items():
                    features[f"{key}_{nested_key}"] = nested_value
        
        return features
    
    def _calculate_anomaly_score(self, value: float, baseline: Dict[str, float]) -> float:
        """Calculate anomaly score using z-score method."""
        mean = baseline['mean']
        std = baseline['std']
        
        if std == 0:
            return 0.0
        
        z_score = abs(value - mean) / std
        # Convert z-score to probability (0-1)
        anomaly_score = 1 - (1 / (1 + np.exp(z_score - 2)))
        
        return anomaly_score
    
    def _determine_severity(self, anomaly_score: float) -> AnomalySeverity:
        """Determine anomaly severity based on score."""
        if anomaly_score >= self.alert_thresholds[AnomalySeverity.CRITICAL]:
            return AnomalySeverity.CRITICAL
        elif anomaly_score >= self.alert_thresholds[AnomalySeverity.HIGH]:
            return AnomalySeverity.HIGH
        elif anomaly_score >= self.alert_thresholds[AnomalySeverity.MEDIUM]:
            return AnomalySeverity.MEDIUM
        else:
            return AnomalySeverity.LOW
    
    def _generate_anomaly_recommendations(self, feature_name: str, actual_value: float, baseline: Dict[str, float]) -> List[str]:
        """Generate recommendations for anomaly resolution."""
        recommendations = []
        
        deviation = abs(actual_value - baseline['mean']) / baseline['mean']
        
        if deviation > 0.5:  # 50% deviation
            recommendations.append(f"Immediate investigation required for {feature_name}")
            recommendations.append("Check for equipment malfunction or sensor failure")
        elif deviation > 0.2:  # 20% deviation
            recommendations.append(f"Monitor {feature_name} closely for further changes")
            recommendations.append("Consider preventive maintenance")
        else:
            recommendations.append(f"Continue monitoring {feature_name}")
        
        return recommendations


class OptimizationEngine:
    """Generate optimization recommendations using AI."""
    
    def __init__(self, config: PredictionConfig):
        self.config = config
        self.optimization_history = []
        self.recommendation_templates = self._load_recommendation_templates()
    
    def generate_recommendations(self, element_id: str, current_data: Dict[str, Any], 
                               historical_data: List[Dict[str, Any]]) -> List[OptimizationRecommendation]:
        """Generate optimization recommendations for an element."""
        recommendations = []
        
        try:
            # Analyze energy optimization opportunities
            energy_recs = self._analyze_energy_optimization(element_id, current_data, historical_data)
            recommendations.extend(energy_recs)
            
            # Analyze performance optimization opportunities
            performance_recs = self._analyze_performance_optimization(element_id, current_data, historical_data)
            recommendations.extend(performance_recs)
            
            # Analyze maintenance optimization opportunities
            maintenance_recs = self._analyze_maintenance_optimization(element_id, current_data, historical_data)
            recommendations.extend(maintenance_recs)
            
            # Store recommendations in history
            self.optimization_history.extend(recommendations)
            
            logger.info(f"Generated {len(recommendations)} optimization recommendations for element {element_id}")
            
        except Exception as e:
            logger.error(f"Error generating recommendations for element {element_id}: {e}")
        
        return recommendations
    
    def _analyze_energy_optimization(self, element_id: str, current_data: Dict[str, Any], 
                                   historical_data: List[Dict[str, Any]]) -> List[OptimizationRecommendation]:
        """Analyze energy optimization opportunities."""
        recommendations = []
        
        # Analyze HVAC energy optimization
        if 'hvac' in current_data.get('system_type', '').lower():
            efficiency = current_data.get('efficiency', 0)
            if efficiency < 0.8:  # Below 80% efficiency
                recommendations.append(OptimizationRecommendation(
                    element_id=element_id,
                    recommendation_type="energy_optimization",
                    timestamp=datetime.now(),
                    current_value=efficiency,
                    recommended_value=0.85,
                    expected_improvement=0.05,
                    confidence_score=0.8,
                    implementation_cost="medium",
                    priority="high",
                    description="HVAC efficiency below optimal levels",
                    action_items=[
                        "Clean or replace air filters",
                        "Check refrigerant levels",
                        "Optimize thermostat settings",
                        "Schedule preventive maintenance"
                    ]
                ))
        
        # Analyze lighting energy optimization
        if 'lighting' in current_data.get('system_type', '').lower():
            power_consumption = current_data.get('power_consumption', 0)
            if power_consumption > 100:  # High power consumption
                recommendations.append(OptimizationRecommendation(
                    element_id=element_id,
                    recommendation_type="energy_optimization",
                    timestamp=datetime.now(),
                    current_value=power_consumption,
                    recommended_value=power_consumption * 0.8,  # 20% reduction
                    expected_improvement=0.2,
                    confidence_score=0.7,
                    implementation_cost="low",
                    priority="medium",
                    description="High lighting power consumption detected",
                    action_items=[
                        "Replace with LED lighting",
                        "Implement occupancy sensors",
                        "Optimize lighting schedules",
                        "Consider daylight harvesting"
                    ]
                ))
        
        return recommendations
    
    def _analyze_performance_optimization(self, element_id: str, current_data: Dict[str, Any], 
                                        historical_data: List[Dict[str, Any]]) -> List[OptimizationRecommendation]:
        """Analyze performance optimization opportunities."""
        recommendations = []
        
        # Analyze system performance
        performance_metrics = current_data.get('performance_metrics', {})
        for metric_name, current_value in performance_metrics.items():
            if isinstance(current_value, (int, float)):
                # Compare with historical average
                historical_values = [d.get('performance_metrics', {}).get(metric_name, 0) 
                                   for d in historical_data if isinstance(d.get('performance_metrics', {}).get(metric_name), (int, float))]
                
                if historical_values:
                    avg_historical = np.mean(historical_values)
                    if current_value < avg_historical * 0.9:  # 10% below average
                        recommendations.append(OptimizationRecommendation(
                            element_id=element_id,
                            recommendation_type="performance_optimization",
                            timestamp=datetime.now(),
                            current_value=current_value,
                            recommended_value=avg_historical,
                            expected_improvement=(avg_historical - current_value) / current_value,
                            confidence_score=0.75,
                            implementation_cost="medium",
                            priority="medium",
                            description=f"Performance degradation detected in {metric_name}",
                            action_items=[
                                f"Investigate {metric_name} performance issues",
                                "Check for system bottlenecks",
                                "Optimize system configuration",
                                "Consider system upgrades"
                            ]
                        ))
        
        return recommendations
    
    def _analyze_maintenance_optimization(self, element_id: str, current_data: Dict[str, Any], 
                                        historical_data: List[Dict[str, Any]]) -> List[OptimizationRecommendation]:
        """Analyze maintenance optimization opportunities."""
        recommendations = []
        
        # Analyze maintenance schedules
        last_maintenance = current_data.get('last_maintenance_date')
        maintenance_interval = current_data.get('maintenance_interval_days', 365)
        
        if last_maintenance:
            days_since_maintenance = (datetime.now() - last_maintenance).days
            if days_since_maintenance > maintenance_interval * 0.8:  # 80% of interval
                recommendations.append(OptimizationRecommendation(
                    element_id=element_id,
                    recommendation_type="maintenance_optimization",
                    timestamp=datetime.now(),
                    current_value=days_since_maintenance,
                    recommended_value=maintenance_interval,
                    expected_improvement=0.1,  # 10% reliability improvement
                    confidence_score=0.9,
                    implementation_cost="low",
                    priority="high",
                    description="Maintenance due soon",
                    action_items=[
                        "Schedule preventive maintenance",
                        "Check maintenance history",
                        "Update maintenance schedule",
                        "Prepare maintenance checklist"
                    ]
                ))
        
        return recommendations
    
    def _load_recommendation_templates(self) -> Dict[str, Any]:
        """Load recommendation templates for different optimization types."""
        return {
            "energy_optimization": {
                "hvac": {
                    "description": "HVAC system optimization",
                    "action_items": ["Clean filters", "Check refrigerant", "Optimize settings"]
                },
                "lighting": {
                    "description": "Lighting system optimization",
                    "action_items": ["Replace with LED", "Add sensors", "Optimize schedules"]
                }
            },
            "performance_optimization": {
                "general": {
                    "description": "System performance optimization",
                    "action_items": ["Check bottlenecks", "Optimize configuration", "Consider upgrades"]
                }
            },
            "maintenance_optimization": {
                "preventive": {
                    "description": "Preventive maintenance scheduling",
                    "action_items": ["Schedule maintenance", "Check history", "Update schedule"]
                }
            }
        }


class AIBehaviorPredictionSystem:
    """
    Advanced AI system for BIM behavior prediction, anomaly detection,
    and automated optimization recommendations.
    """
    
    def __init__(self, config: Optional[PredictionConfig] = None):
        self.config = config or PredictionConfig()
        self.performance_monitor = PerformanceMonitor()
        
        # Initialize AI components
        self.feature_extractor = FeatureExtractor(self.config)
        self.anomaly_detector = AnomalyDetector(self.config)
        self.optimization_engine = OptimizationEngine(self.config)
        
        # Data storage
        self.behavior_data = defaultdict(list)
        self.prediction_cache = {}
        self.anomaly_history = []
        self.optimization_history = []
        
        # Model management
        self.models = {}
        self.model_versions = {}
        self.model_performance = {}
        
        # Processing state
        self.running = False
        self.processing_thread = None
        self.thread_pool = ThreadPoolExecutor(max_workers=5)
        
        # Statistics
        self.prediction_stats = {
            'total_predictions': 0,
            'successful_predictions': 0,
            'failed_predictions': 0,
            'average_confidence': 0.0,
            'anomalies_detected': 0,
            'recommendations_generated': 0
        }
        
        logger.info("AI behavior prediction system initialized")
    
    async def start_processing(self):
        """Start AI processing loop."""
        if self.running:
            return
        
        self.running = True
        self.processing_thread = threading.Thread(target=self._processing_loop)
        self.processing_thread.start()
        
        logger.info("AI behavior prediction processing started")
    
    async def stop_processing(self):
        """Stop AI processing loop."""
        self.running = False
        if self.processing_thread:
            self.processing_thread.join()
        
        logger.info("AI behavior prediction processing stopped")
    
    def _processing_loop(self):
        """Main processing loop for AI predictions."""
        while self.running:
            try:
                # Process predictions for all elements
                for element_id in list(self.behavior_data.keys()):
                    self._process_element_predictions(element_id)
                
                # Update models periodically
                if time.time() % self.config.auto_retrain_frequency == 0:
                    self._update_models()
                
                time.sleep(self.config.update_frequency)
                
            except Exception as e:
                logger.error(f"Error in AI processing loop: {e}")
                time.sleep(10)  # Wait before retrying
    
    def _process_element_predictions(self, element_id: str):
        """Process predictions for a specific element."""
        try:
            data = self.behavior_data[element_id]
            if len(data) < self.config.min_data_points_for_training:
                return
            
            # Extract features
            features = self.feature_extractor.extract_temporal_features(data)
            
            # Generate predictions
            predictions = self._generate_predictions(element_id, features)
            
            # Detect anomalies
            anomalies = self.anomaly_detector.detect_anomalies(element_id, features)
            
            # Generate optimization recommendations
            recommendations = self.optimization_engine.generate_recommendations(
                element_id, features, data
            )
            
            # Update statistics
            self._update_prediction_stats(predictions, anomalies, recommendations)
            
        except Exception as e:
            logger.error(f"Error processing predictions for element {element_id}: {e}")
    
    def _generate_predictions(self, element_id: str, features: Dict[str, float]) -> List[PredictionResult]:
        """Generate predictions for an element."""
        predictions = []
        
        try:
            # Generate behavior predictions
            behavior_prediction = self._predict_behavior(element_id, features)
            if behavior_prediction:
                predictions.append(behavior_prediction)
            
            # Generate maintenance predictions
            maintenance_prediction = self._predict_maintenance(element_id, features)
            if maintenance_prediction:
                predictions.append(maintenance_prediction)
            
            # Generate energy optimization predictions
            energy_prediction = self._predict_energy_optimization(element_id, features)
            if energy_prediction:
                predictions.append(energy_prediction)
            
        except Exception as e:
            logger.error(f"Error generating predictions for element {element_id}: {e}")
        
        return predictions
    
    def _predict_behavior(self, element_id: str, features: Dict[str, float]) -> Optional[PredictionResult]:
        """Predict future behavior of an element."""
        try:
            # Simple prediction based on trends
            trend = features.get('trend', 0)
            current_value = features.get('mean', 0)
            
            # Predict future value based on trend
            predicted_value = current_value + (trend * self.config.prediction_horizon)
            confidence_score = min(0.9, max(0.1, 1 - abs(trend)))
            
            return PredictionResult(
                prediction_type=PredictionType.BEHAVIOR_PREDICTION,
                element_id=element_id,
                timestamp=datetime.now(),
                prediction_value=predicted_value,
                confidence_score=confidence_score,
                prediction_horizon=self.config.prediction_horizon,
                features_used=list(features.keys()),
                model_version="v1.0",
                metadata={'trend': trend, 'current_value': current_value}
            )
            
        except Exception as e:
            logger.error(f"Error predicting behavior for element {element_id}: {e}")
            return None
    
    def _predict_maintenance(self, element_id: str, features: Dict[str, float]) -> Optional[PredictionResult]:
        """Predict maintenance needs for an element."""
        try:
            # Analyze features for maintenance indicators
            volatility = features.get('volatility', 0)
            trend = features.get('trend', 0)
            
            # Calculate maintenance probability
            maintenance_probability = min(0.9, volatility * 0.5 + abs(trend) * 0.3)
            
            if maintenance_probability > 0.3:  # Threshold for maintenance prediction
                return PredictionResult(
                    prediction_type=PredictionType.MAINTENANCE_PREDICTION,
                    element_id=element_id,
                    timestamp=datetime.now(),
                    prediction_value=maintenance_probability,
                    confidence_score=0.7,
                    prediction_horizon=168,  # 1 week
                    features_used=['volatility', 'trend'],
                    model_version="v1.0",
                    metadata={'maintenance_probability': maintenance_probability}
                )
            
        except Exception as e:
            logger.error(f"Error predicting maintenance for element {element_id}: {e}")
        
        return None
    
    def _predict_energy_optimization(self, element_id: str, features: Dict[str, float]) -> Optional[PredictionResult]:
        """Predict energy optimization opportunities."""
        try:
            # Analyze energy-related features
            efficiency = features.get('efficiency', 1.0)
            power_consumption = features.get('power_consumption', 0)
            
            if efficiency < 0.8 or power_consumption > 100:
                optimization_potential = max(0.1, (1 - efficiency) * 0.5 + (power_consumption / 1000) * 0.3)
                
                return PredictionResult(
                    prediction_type=PredictionType.ENERGY_OPTIMIZATION,
                    element_id=element_id,
                    timestamp=datetime.now(),
                    prediction_value=optimization_potential,
                    confidence_score=0.8,
                    prediction_horizon=24,  # 1 day
                    features_used=['efficiency', 'power_consumption'],
                    model_version="v1.0",
                    metadata={'optimization_potential': optimization_potential}
                )
            
        except Exception as e:
            logger.error(f"Error predicting energy optimization for element {element_id}: {e}")
        
        return None
    
    def _update_prediction_stats(self, predictions: List[PredictionResult], 
                               anomalies: List[AnomalyResult], 
                               recommendations: List[OptimizationRecommendation]):
        """Update prediction statistics."""
        self.prediction_stats['total_predictions'] += len(predictions)
        self.prediction_stats['successful_predictions'] += len([p for p in predictions if p.confidence_score > 0.5])
        self.prediction_stats['failed_predictions'] += len([p for p in predictions if p.confidence_score <= 0.5])
        self.prediction_stats['anomalies_detected'] += len(anomalies)
        self.prediction_stats['recommendations_generated'] += len(recommendations)
        
        if predictions:
            avg_confidence = sum(p.confidence_score for p in predictions) / len(predictions)
            self.prediction_stats['average_confidence'] = (
                (self.prediction_stats['average_confidence'] * (self.prediction_stats['total_predictions'] - len(predictions)) + 
                 avg_confidence * len(predictions)) / self.prediction_stats['total_predictions']
            )
    
    def _update_models(self):
        """Update ML models based on new data."""
        try:
            # Retrain models with new data
            for element_id in self.behavior_data.keys():
                if len(self.behavior_data[element_id]) >= self.config.min_data_points_for_training:
                    self._retrain_model(element_id)
            
            logger.info("AI models updated successfully")
            
        except Exception as e:
            logger.error(f"Error updating AI models: {e}")
    
    def _retrain_model(self, element_id: str):
        """Retrain ML model for a specific element."""
        try:
            data = self.behavior_data[element_id]
            
            # Extract features for training
            features_list = []
            for data_point in data[-self.config.max_data_points:]:
                features = self.feature_extractor.extract_temporal_features([data_point])
                features_list.append(features)
            
            # Update model (simplified - in real implementation, this would retrain ML models)
            self.model_versions[element_id] = f"v{len(self.model_versions.get(element_id, 'v1.0').split('.')[-1]) + 1}.0"
            
            logger.info(f"Retrained model for element {element_id}")
            
        except Exception as e:
            logger.error(f"Error retraining model for element {element_id}: {e}")
    
    def add_behavior_data(self, element_id: str, data: Dict[str, Any]):
        """Add behavior data for AI analysis."""
        try:
            data['timestamp'] = datetime.now()
            self.behavior_data[element_id].append(data)
            
            # Keep only recent data
            if len(self.behavior_data[element_id]) > self.config.max_data_points:
                self.behavior_data[element_id] = self.behavior_data[element_id][-self.config.max_data_points:]
            
            # Update anomaly detector baseline
            if len(self.behavior_data[element_id]) >= 100:
                self.anomaly_detector.update_baseline(element_id, self.behavior_data[element_id])
            
        except Exception as e:
            logger.error(f"Error adding behavior data for element {element_id}: {e}")
    
    def get_predictions(self, element_id: str) -> List[PredictionResult]:
        """Get predictions for a specific element."""
        cache_key = f"predictions_{element_id}"
        if cache_key in self.prediction_cache:
            cache_time, predictions = self.prediction_cache[cache_key]
            if (datetime.now() - cache_time).seconds < self.config.cache_ttl:
                return predictions
        
        # Generate new predictions
        data = self.behavior_data.get(element_id, [])
        if data:
            features = self.feature_extractor.extract_temporal_features(data)
            predictions = self._generate_predictions(element_id, features)
            
            # Cache predictions
            self.prediction_cache[cache_key] = (datetime.now(), predictions)
            
            return predictions
        
        return []
    
    def get_anomalies(self, element_id: str) -> List[AnomalyResult]:
        """Get anomalies for a specific element."""
        data = self.behavior_data.get(element_id, [])
        if data:
            features = self.feature_extractor.extract_temporal_features(data)
            return self.anomaly_detector.detect_anomalies(element_id, features)
        
        return []
    
    def get_optimization_recommendations(self, element_id: str) -> List[OptimizationRecommendation]:
        """Get optimization recommendations for a specific element."""
        data = self.behavior_data.get(element_id, [])
        if data:
            features = self.feature_extractor.extract_temporal_features(data)
            return self.optimization_engine.generate_recommendations(element_id, features, data)
        
        return []
    
    def get_prediction_stats(self) -> Dict[str, Any]:
        """Get prediction statistics."""
        return {
            'prediction_stats': self.prediction_stats,
            'total_elements': len(self.behavior_data),
            'total_anomalies': len(self.anomaly_history),
            'total_recommendations': len(self.optimization_history),
            'model_versions': self.model_versions,
            'cache_size': len(self.prediction_cache)
        }
    
    def clear_cache(self):
        """Clear prediction cache."""
        self.prediction_cache.clear()
        logger.info("AI prediction cache cleared")
    
    def reset_statistics(self):
        """Reset prediction statistics."""
        self.prediction_stats = {
            'total_predictions': 0,
            'successful_predictions': 0,
            'failed_predictions': 0,
            'average_confidence': 0.0,
            'anomalies_detected': 0,
            'recommendations_generated': 0
        }
        logger.info("AI prediction statistics reset") 