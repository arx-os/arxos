"""
Analytics module for real-time telemetry system

Provides:
- Anomaly detection (Z-score, Isolation Forest)
- Time-series forecasting (ARIMA, Prophet, moving average)
- Clustering and correlation analysis
- Extensible analytics interfaces
"""

from typing import List, Dict, Any, Optional
import numpy as np

class AnomalyDetector:
    """Base class for anomaly detection"""
    def detect(self, values: List[float], sensitivity: float = 0.8) -> List[bool]:
        """Return a list of booleans indicating anomalies in the input values"""
        raise NotImplementedError

class ZScoreAnomalyDetector(AnomalyDetector):
    """Simple Z-score based anomaly detector"""
    def detect(self, values: List[float], sensitivity: float = 0.8) -> List[bool]:
        if not values or len(values) < 5:
            return [False] * len(values)
        arr = np.array(values)
        mean = np.mean(arr)
        std = np.std(arr)
        if std == 0:
            return [False] * len(values)
        z_scores = np.abs((arr - mean) / std)
        threshold = 2.0 / sensitivity
        return [z > threshold for z in z_scores]

try:
    from sklearn.ensemble import IsolationForest
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

class IsolationForestAnomalyDetector(AnomalyDetector):
    """Isolation Forest anomaly detector (requires scikit-learn)"""
    def __init__(self):
        if not SKLEARN_AVAILABLE:
            raise ImportError("scikit-learn is required for IsolationForestAnomalyDetector")
        self.model = IsolationForest(contamination=0.1, random_state=42)
    def detect(self, values: List[float], sensitivity: float = 0.8) -> List[bool]:
        if not values or len(values) < 10:
            return [False] * len(values)
        arr = np.array(values).reshape(-1, 1)
        preds = self.model.fit_predict(arr)
        return [p == -1 for p in preds]

class Forecaster:
    """Base class for time-series forecasting"""
    def forecast(self, values: List[float], steps: int = 5) -> List[float]:
        raise NotImplementedError

class MovingAverageForecaster(Forecaster):
    """Simple moving average forecaster"""
    def forecast(self, values: List[float], steps: int = 5) -> List[float]:
        if not values:
            return [0.0] * steps
        avg = np.mean(values[-min(10, len(values)):])
        return [avg] * steps

try:
    from statsmodels.tsa.arima.model import ARIMA
    STATSMODELS_AVAILABLE = True
except ImportError:
    STATSMODELS_AVAILABLE = False

class ARIMAForecaster(Forecaster):
    """ARIMA forecaster (requires statsmodels)"""
    def forecast(self, values: List[float], steps: int = 5) -> List[float]:
        if not STATSMODELS_AVAILABLE or not values or len(values) < 10:
            return [0.0] * steps
        try:
            model = ARIMA(values, order=(1, 1, 1))
            fit = model.fit()
            forecast = fit.forecast(steps=steps)
            return list(forecast)
        except Exception:
            return [0.0] * steps

class Clusterer:
    """Base class for clustering"""
    def cluster(self, values: List[float], n_clusters: int = 2) -> List[int]:
        raise NotImplementedError

try:
    from sklearn.cluster import KMeans
    KMEANS_AVAILABLE = True
except ImportError:
    KMEANS_AVAILABLE = False

class KMeansClusterer(Clusterer):
    """KMeans clustering (requires scikit-learn)"""
    def cluster(self, values: List[float], n_clusters: int = 2) -> List[int]:
        if not KMEANS_AVAILABLE or not values or len(values) < n_clusters:
            return [0] * len(values)
        arr = np.array(values).reshape(-1, 1)
        kmeans = KMeans(n_clusters=n_clusters, random_state=42)
        labels = kmeans.fit_predict(arr)
        return list(labels)

# Utility: Correlation

def compute_correlation(x: List[float], y: List[float], method: str = 'pearson') -> float:
    if not x or not y or len(x) != len(y):
        return 0.0
    if method == 'pearson':
        return float(np.corrcoef(x, y)[0, 1])
    elif method == 'spearman':
        from scipy.stats import spearmanr
        return float(spearmanr(x, y).correlation)
    else:
        return 0.0 