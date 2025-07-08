"""
Failure Pattern Detection System

This module provides:
- Machine learning for failure prediction
- Pattern recognition algorithms
- Predictive maintenance alerts
- Risk assessment models
- Anomaly detection
- Trend analysis
"""

import numpy as np
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import logging
import json
import pickle
from collections import defaultdict, deque
from enum import Enum
import warnings

# Check for optional dependencies
try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    logging.warning("pandas not available. Some features will be disabled.")

# Suppress sklearn warnings
warnings.filterwarnings('ignore', category=UserWarning)

try:
    from sklearn.ensemble import IsolationForest, RandomForestClassifier
    from sklearn.preprocessing import StandardScaler, MinMaxScaler
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import classification_report, confusion_matrix
    from sklearn.cluster import DBSCAN
    from sklearn.decomposition import PCA
    import joblib
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logging.warning("scikit-learn not available. ML features will be disabled.")

logger = logging.getLogger(__name__)


class FailureType(Enum):
    """Types of failures that can be detected"""
    ANOMALY = "anomaly"
    TREND = "trend"
    THRESHOLD = "threshold"
    PATTERN = "pattern"
    SEASONAL = "seasonal"
    CUMULATIVE = "cumulative"


class AlertLevel(Enum):
    """Alert levels for failure predictions"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


@dataclass
class FailurePattern:
    """Represents a detected failure pattern"""
    pattern_id: str
    failure_type: FailureType
    source: str
    confidence: float
    severity: float
    description: str
    timestamp: datetime
    data_points: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MaintenanceAlert:
    """Represents a predictive maintenance alert"""
    alert_id: str
    alert_level: AlertLevel
    source: str
    predicted_failure_time: datetime
    confidence: float
    description: str
    recommended_actions: List[str] = field(default_factory=list)
    risk_score: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class RiskAssessment:
    """Represents a risk assessment for a system or component"""
    assessment_id: str
    component_id: str
    risk_score: float
    risk_factors: Dict[str, float] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)
    valid_until: datetime = field(default_factory=lambda: datetime.now() + timedelta(days=7))


class TrendAnalyzer:
    """Analyzes trends in time series data"""
    
    def __init__(self, window_size: int = 10, threshold: float = 0.1):
        self.window_size = window_size
        self.threshold = threshold
    
    def detect_trends(self, data) -> List[Dict[str, Any]]:
        """Detect trends in time series data"""
        if len(data) < self.window_size:
            return []
        
        # Convert to list if needed
        if hasattr(data, 'values'):
            data = data.values
        elif not isinstance(data, (list, np.ndarray)):
            data = list(data)
        
        trends = []
        
        for i in range(self.window_size, len(data)):
            window = data[i-self.window_size:i]
            
            # Calculate trend using linear regression
            x = np.arange(len(window))
            y = np.array(window)
            
            # Simple linear regression
            slope = np.polyfit(x, y, 1)[0]
            
            # Calculate trend strength
            trend_strength = abs(slope) / (np.std(window) + 1e-8)
            
            if trend_strength > self.threshold:
                trend_type = "increasing" if slope > 0 else "decreasing"
                trends.append({
                    'index': i,
                    'trend_type': trend_type,
                    'slope': slope,
                    'strength': trend_strength,
                    'window_data': window.tolist() if hasattr(window, 'tolist') else list(window)
                })
        
        return trends
    
    def detect_breakpoints(self, data) -> List[int]:
        """Detect breakpoints in time series data"""
        if len(data) < 3:
            return []
        
        # Convert to list if needed
        if hasattr(data, 'values'):
            data = data.values
        elif not isinstance(data, (list, np.ndarray)):
            data = list(data)
        
        breakpoints = []
        
        for i in range(2, len(data)):
            # Calculate change in mean
            before_mean = np.mean(data[:i])
            after_mean = np.mean(data[i:])
            
            change = abs(after_mean - before_mean) / (np.std(data) + 1e-8)
            
            if change > self.threshold:
                breakpoints.append(i)
        
        return breakpoints


class PatternRecognizer:
    """Recognizes patterns in time series data"""
    
    def __init__(self, min_pattern_length: int = 5, similarity_threshold: float = 0.8):
        self.min_pattern_length = min_pattern_length
        self.similarity_threshold = similarity_threshold
    
    def find_repeating_patterns(self, data) -> List[Dict[str, Any]]:
        """Find repeating patterns in time series data"""
        if len(data) < self.min_pattern_length * 2:
            return []
        
        # Convert to list if needed
        if hasattr(data, 'values'):
            data = data.values
        elif not isinstance(data, (list, np.ndarray)):
            data = list(data)
        
        patterns = []
        
        for pattern_length in range(self.min_pattern_length, len(data) // 2):
            for start in range(len(data) - pattern_length):
                pattern = data[start:start + pattern_length]
                
                # Look for similar patterns
                matches = self._find_similar_patterns(data, pattern, start + pattern_length)
                
                if len(matches) > 1:  # At least 2 occurrences
                    patterns.append({
                        'pattern': pattern.tolist() if hasattr(pattern, 'tolist') else list(pattern),
                        'start_indices': [start] + matches,
                        'length': pattern_length,
                        'occurrences': len(matches) + 1
                    })
        
        return patterns
    
    def _find_similar_patterns(self, data, pattern, start_after: int) -> List[int]:
        """Find patterns similar to the given pattern"""
        matches = []
        
        for i in range(start_after, len(data) - len(pattern)):
            candidate = data[i:i + len(pattern)]
            similarity = self._calculate_similarity(pattern, candidate)
            
            if similarity >= self.similarity_threshold:
                matches.append(i)
        
        return matches
    
    def _calculate_similarity(self, pattern1, pattern2) -> float:
        """Calculate similarity between two patterns using correlation"""
        if len(pattern1) != len(pattern2):
            return 0.0
        
        # Convert to numpy arrays
        p1 = np.array(pattern1)
        p2 = np.array(pattern2)
        
        # Calculate correlation
        correlation = np.corrcoef(p1, p2)[0, 1]
        return abs(correlation) if not np.isnan(correlation) else 0.0


class RiskAssessor:
    """Assesses risk based on multiple factors"""
    
    def __init__(self):
        self.risk_factors = {
            'age': 0.3,
            'usage': 0.25,
            'environment': 0.2,
            'maintenance': 0.15,
            'anomalies': 0.1
        }
    
    def assess_risk(self, component_data: Dict[str, Any]) -> RiskAssessment:
        """Assess risk for a component"""
        risk_scores = {}
        total_risk = 0.0
        
        # Age factor
        if 'age' in component_data:
            age_risk = min(component_data['age'] / 10.0, 1.0)  # Normalize to 0-1
            risk_scores['age'] = age_risk
            total_risk += age_risk * self.risk_factors['age']
        
        # Usage factor
        if 'usage_hours' in component_data:
            usage_risk = min(component_data['usage_hours'] / 10000.0, 1.0)
            risk_scores['usage'] = usage_risk
            total_risk += usage_risk * self.risk_factors['usage']
        
        # Environment factor
        if 'environment_score' in component_data:
            env_risk = component_data['environment_score']
            risk_scores['environment'] = env_risk
            total_risk += env_risk * self.risk_factors['environment']
        
        # Maintenance factor
        if 'days_since_maintenance' in component_data:
            maint_risk = min(component_data['days_since_maintenance'] / 365.0, 1.0)
            risk_scores['maintenance'] = maint_risk
            total_risk += maint_risk * self.risk_factors['maintenance']
        
        # Anomalies factor
        if 'anomaly_count' in component_data:
            anomaly_risk = min(component_data['anomaly_count'] / 10.0, 1.0)
            risk_scores['anomalies'] = anomaly_risk
            total_risk += anomaly_risk * self.risk_factors['anomalies']
        
        # Generate recommendations
        recommendations = self._generate_recommendations(risk_scores, total_risk)
        
        return RiskAssessment(
            assessment_id=f"risk_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            component_id=component_data.get('component_id', 'unknown'),
            risk_score=total_risk,
            risk_factors=risk_scores,
            recommendations=recommendations
        )
    
    def _generate_recommendations(self, risk_scores: Dict[str, float], total_risk: float) -> List[str]:
        """Generate recommendations based on risk factors"""
        recommendations = []
        
        if risk_scores.get('age', 0) > 0.7:
            recommendations.append("Consider component replacement due to age")
        
        if risk_scores.get('usage', 0) > 0.8:
            recommendations.append("High usage detected - schedule maintenance")
        
        if risk_scores.get('environment', 0) > 0.6:
            recommendations.append("Environmental conditions may be affecting performance")
        
        if risk_scores.get('maintenance', 0) > 0.5:
            recommendations.append("Schedule preventive maintenance")
        
        if risk_scores.get('anomalies', 0) > 0.3:
            recommendations.append("Multiple anomalies detected - investigate root cause")
        
        if total_risk > 0.8:
            recommendations.append("CRITICAL: High overall risk - immediate attention required")
        elif total_risk > 0.6:
            recommendations.append("WARNING: Elevated risk - schedule inspection")
        elif total_risk > 0.4:
            recommendations.append("MODERATE: Monitor closely and plan maintenance")
        
        return recommendations


class FailureDetectionSystem:
    """Main failure detection system that coordinates all components"""
    
    def __init__(self):
        self.trend_analyzer = TrendAnalyzer()
        self.pattern_recognizer = PatternRecognizer()
        self.risk_assessor = RiskAssessor()
        
        # Initialize ML components only if available
        if SKLEARN_AVAILABLE:
            from services.failure_detection import AnomalyDetector, FailurePredictor
            self.anomaly_detector = AnomalyDetector()
            self.failure_predictor = FailurePredictor()
        else:
            self.anomaly_detector = None
            self.failure_predictor = None
        
        self.detected_patterns: List[FailurePattern] = []
        self.maintenance_alerts: List[MaintenanceAlert] = []
        self.risk_assessments: List[RiskAssessment] = []
        
        self.data_buffer = deque(maxlen=10000)
        self.alert_thresholds = {
            'anomaly_confidence': 0.8,
            'trend_strength': 0.5,
            'pattern_occurrences': 3,
            'risk_score': 0.7
        }
    
    def process_telemetry_data(self, data, source: str = "unknown") -> List[FailurePattern]:
        """Process telemetry data and detect failure patterns"""
        if len(data) == 0:
            return []
        
        patterns = []
        
        # Detect trends
        for column in self._get_numeric_columns(data):
            try:
                column_data = self._extract_column_data(data, column)
                trends = self.trend_analyzer.detect_trends(column_data)
                
                for trend in trends:
                    if trend['strength'] > self.alert_thresholds['trend_strength']:
                        pattern = FailurePattern(
                            pattern_id=f"trend_{source}_{column}_{trend['index']}",
                            failure_type=FailureType.TREND,
                            source=source,
                            confidence=trend['strength'],
                            severity=min(trend['strength'], 1.0),
                            description=f"{trend['trend_type'].title()} trend detected in {column}",
                            timestamp=datetime.now(),
                            data_points=trend['window_data']
                        )
                        patterns.append(pattern)
            except Exception as e:
                logger.error(f"Trend detection failed for {column}: {e}")
        
        # Detect patterns
        for column in self._get_numeric_columns(data):
            try:
                column_data = self._extract_column_data(data, column)
                patterns_found = self.pattern_recognizer.find_repeating_patterns(column_data)
                
                for pattern_data in patterns_found:
                    if pattern_data['occurrences'] >= self.alert_thresholds['pattern_occurrences']:
                        pattern = FailurePattern(
                            pattern_id=f"pattern_{source}_{column}_{len(patterns)}",
                            failure_type=FailureType.PATTERN,
                            source=source,
                            confidence=pattern_data['occurrences'] / 10.0,  # Normalize
                            severity=min(pattern_data['occurrences'] / 5.0, 1.0),
                            description=f"Repeating pattern detected in {column} ({pattern_data['occurrences']} occurrences)",
                            timestamp=datetime.now(),
                            data_points=pattern_data['pattern']
                        )
                        patterns.append(pattern)
            except Exception as e:
                logger.error(f"Pattern detection failed for {column}: {e}")
        
        self.detected_patterns.extend(patterns)
        return patterns
    
    def _get_numeric_columns(self, data):
        """Get numeric columns from data"""
        if PANDAS_AVAILABLE and hasattr(data, 'select_dtypes'):
            return data.select_dtypes(include=[np.number]).columns
        else:
            # Fallback for non-pandas data
            if isinstance(data, dict):
                return [k for k, v in data.items() if isinstance(v, (int, float, list))]
            elif hasattr(data, 'columns'):
                return data.columns
            else:
                return ['data']  # Default column name
    
    def _extract_column_data(self, data, column):
        """Extract column data from various data formats"""
        if PANDAS_AVAILABLE and hasattr(data, 'iloc'):
            return data[column]
        elif isinstance(data, dict) and column in data:
            return data[column]
        elif hasattr(data, '__getitem__'):
            return data[column]
        else:
            # Fallback: assume data is a list of values
            return data
    
    def assess_risks(self, component_data: List[Dict[str, Any]]) -> List[RiskAssessment]:
        """Assess risks for multiple components"""
        assessments = []
        
        for component in component_data:
            try:
                assessment = self.risk_assessor.assess_risk(component)
                assessments.append(assessment)
            except Exception as e:
                logger.error(f"Risk assessment failed for component {component.get('component_id', 'unknown')}: {e}")
        
        self.risk_assessments.extend(assessments)
        return assessments
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary of all detections and predictions"""
        return {
            'timestamp': datetime.now().isoformat(),
            'patterns_detected': len(self.detected_patterns),
            'alerts_generated': len(self.maintenance_alerts),
            'risk_assessments': len(self.risk_assessments),
            'recent_patterns': [
                {
                    'id': p.pattern_id,
                    'type': p.failure_type.value,
                    'source': p.source,
                    'confidence': p.confidence,
                    'severity': p.severity,
                    'description': p.description
                }
                for p in self.detected_patterns[-10:]  # Last 10 patterns
            ],
            'recent_alerts': [
                {
                    'id': a.alert_id,
                    'level': a.alert_level.value,
                    'confidence': a.confidence,
                    'description': a.description,
                    'predicted_time': a.predicted_failure_time.isoformat()
                }
                for a in self.maintenance_alerts[-10:]  # Last 10 alerts
            ],
            'high_risk_components': [
                {
                    'id': r.component_id,
                    'risk_score': r.risk_score,
                    'recommendations': r.recommendations[:3]  # Top 3 recommendations
                }
                for r in self.risk_assessments
                if r.risk_score > 0.7
            ]
        }


# ML components (only if scikit-learn is available)
if SKLEARN_AVAILABLE:
    class AnomalyDetector:
        """Detects anomalies in telemetry data using isolation forest"""
        
        def __init__(self, contamination: float = 0.1, random_state: int = 42):
            self.model = IsolationForest(
                contamination=contamination,
                random_state=random_state,
                n_estimators=100
            )
            self.scaler = StandardScaler()
            self.is_fitted = False
            self.feature_names = []
        
        def fit(self, data) -> 'AnomalyDetector':
            """Fit the anomaly detection model"""
            if len(data) == 0:
                raise ValueError("Data cannot be empty")
            
            # Convert to numpy array if needed
            if hasattr(data, 'values'):
                data_array = data.values
            else:
                data_array = np.array(data)
            
            if len(data_array.shape) == 1:
                data_array = data_array.reshape(-1, 1)
            
            self.feature_names = list(range(data_array.shape[1]))
            scaled_data = self.scaler.fit_transform(data_array)
            self.model.fit(scaled_data)
            self.is_fitted = True
            
            logger.info(f"Anomaly detector fitted with {len(data_array)} samples")
            return self
        
        def predict(self, data) -> np.ndarray:
            """Predict anomalies in data"""
            if not self.is_fitted:
                raise ValueError("Model must be fitted before prediction")
            
            if len(data) == 0:
                return np.array([])
            
            # Convert to numpy array if needed
            if hasattr(data, 'values'):
                data_array = data.values
            else:
                data_array = np.array(data)
            
            if len(data_array.shape) == 1:
                data_array = data_array.reshape(-1, 1)
            
            scaled_data = self.scaler.transform(data_array)
            predictions = self.model.predict(scaled_data)
            # Convert to binary: -1 (anomaly) -> 1, 1 (normal) -> 0
            return (predictions == -1).astype(int)
        
        def predict_scores(self, data) -> np.ndarray:
            """Get anomaly scores (lower = more anomalous)"""
            if not self.is_fitted:
                raise ValueError("Model must be fitted before prediction")
            
            if len(data) == 0:
                return np.array([])
            
            # Convert to numpy array if needed
            if hasattr(data, 'values'):
                data_array = data.values
            else:
                data_array = np.array(data)
            
            if len(data_array.shape) == 1:
                data_array = data_array.reshape(-1, 1)
            
            scaled_data = self.scaler.transform(data_array)
            return self.model.decision_function(scaled_data)
    
    class FailurePredictor:
        """Predicts failures using machine learning models"""
        
        def __init__(self, model_type: str = "random_forest"):
            self.model_type = model_type
            self.model = None
            self.scaler = StandardScaler()
            self.is_fitted = False
            self.feature_names = []
            self.class_names = []
        
        def prepare_features(self, data, target_column: str = None) -> Tuple[Any, Any]:
            """Prepare features for failure prediction"""
            if target_column and hasattr(data, '__getitem__') and target_column in data:
                features = data.drop(columns=[target_column]) if hasattr(data, 'drop') else data
                targets = data[target_column]
            else:
                features = data
                targets = [0] * len(data) if hasattr(data, '__len__') else [0]
            
            return features, targets
        
        def fit(self, data, target_column: str = "failure") -> 'FailurePredictor':
            """Fit the failure prediction model"""
            if len(data) == 0:
                raise ValueError("Data cannot be empty")
            
            features, targets = self.prepare_features(data, target_column)
            
            if len(features) == 0:
                raise ValueError("No valid features after preprocessing")
            
            # Convert to numpy arrays
            if hasattr(features, 'values'):
                features_array = features.values
            else:
                features_array = np.array(features)
            
            if len(features_array.shape) == 1:
                features_array = features_array.reshape(-1, 1)
            
            self.feature_names = list(range(features_array.shape[1]))
            self.class_names = list(set(targets))
            
            # Scale features
            scaled_features = self.scaler.fit_transform(features_array)
            
            # Create and fit model
            if self.model_type == "random_forest":
                self.model = RandomForestClassifier(
                    n_estimators=100,
                    random_state=42,
                    class_weight='balanced'
                )
            else:
                raise ValueError(f"Unsupported model type: {self.model_type}")
            
            self.model.fit(scaled_features, targets)
            self.is_fitted = True
            
            logger.info(f"Failure predictor fitted with {len(features_array)} samples")
            return self
        
        def predict(self, data) -> np.ndarray:
            """Predict failures in data"""
            if not self.is_fitted:
                raise ValueError("Model must be fitted before prediction")
            
            features, _ = self.prepare_features(data)
            
            if len(features) == 0:
                return np.array([])
            
            # Convert to numpy array
            if hasattr(features, 'values'):
                features_array = features.values
            else:
                features_array = np.array(features)
            
            if len(features_array.shape) == 1:
                features_array = features_array.reshape(-1, 1)
            
            scaled_features = self.scaler.transform(features_array)
            return self.model.predict(scaled_features)
        
        def predict_proba(self, data) -> np.ndarray:
            """Get failure probabilities"""
            if not self.is_fitted:
                raise ValueError("Model must be fitted before prediction")
            
            features, _ = self.prepare_features(data)
            
            if len(features) == 0:
                return np.array([])
            
            # Convert to numpy array
            if hasattr(features, 'values'):
                features_array = features.values
            else:
                features_array = np.array(features)
            
            if len(features_array.shape) == 1:
                features_array = features_array.reshape(-1, 1)
            
            scaled_features = self.scaler.transform(features_array)
            return self.model.predict_proba(scaled_features)
        
        def get_feature_importance(self) -> Dict[str, float]:
            """Get feature importance scores"""
            if not self.is_fitted or not hasattr(self.model, 'feature_importances_'):
                return {}
            
            return dict(zip(self.feature_names, self.model.feature_importances_))


# Utility functions for data generation and testing
def generate_failure_data(n_samples: int = 1000, failure_rate: float = 0.1):
    """Generate synthetic data for testing failure detection"""
    np.random.seed(42)
    
    # Generate normal operating data
    normal_data = {
        'temperature': np.random.normal(50, 10, n_samples),
        'pressure': np.random.normal(100, 15, n_samples),
        'vibration': np.random.normal(0.5, 0.1, n_samples),
        'current': np.random.normal(10, 2, n_samples),
        'voltage': np.random.normal(220, 5, n_samples)
    }
    
    # Add some anomalies
    n_failures = int(n_samples * failure_rate)
    failure_indices = np.random.choice(n_samples, n_failures, replace=False)
    
    for idx in failure_indices:
        # Simulate different types of failures
        failure_type = np.random.choice(['temperature', 'pressure', 'vibration'])
        
        if failure_type == 'temperature':
            normal_data['temperature'][idx] = np.random.uniform(80, 120)
        elif failure_type == 'pressure':
            normal_data['pressure'][idx] = np.random.uniform(150, 200)
        elif failure_type == 'vibration':
            normal_data['vibration'][idx] = np.random.uniform(1.0, 2.0)
    
    # Add failure labels
    failure_labels = np.zeros(n_samples)
    failure_labels[failure_indices] = 1
    
    # Create DataFrame if pandas is available, otherwise return dict
    if PANDAS_AVAILABLE:
        df = pd.DataFrame(normal_data)
        df['failure'] = failure_labels
        df['timestamp'] = pd.date_range(start='2024-01-01', periods=n_samples, freq='H')
        return df
    else:
        # Return as dict with lists
        result = normal_data.copy()
        result['failure'] = failure_labels.tolist()
        result['timestamp'] = [datetime.now() + timedelta(hours=i) for i in range(n_samples)]
        return result


def generate_component_data(n_components: int = 10) -> List[Dict[str, Any]]:
    """Generate synthetic component data for risk assessment"""
    components = []
    
    for i in range(n_components):
        component = {
            'component_id': f'comp_{i:03d}',
            'age': np.random.uniform(0, 15),  # Years
            'usage_hours': np.random.uniform(1000, 15000),
            'environment_score': np.random.uniform(0, 1),
            'days_since_maintenance': np.random.uniform(0, 730),  # Days
            'anomaly_count': np.random.poisson(2)  # Poisson distribution
        }
        components.append(component)
    
    return components 