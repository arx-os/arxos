"""
SVGX Telemetry Data Model and Ingestion Service

This module provides:
- SVGX-specific telemetry data schema and tracking
- Real-time and simulated SVGX data ingestion
- SVGX namespace and component tracking
- Performance monitoring for SVGX operations
- Integration with SVGX caching and security systems
- Cross-platform compatibility with Windows optimizations
"""

import threading
import time
import json
import platform
import os
from typing import List, Dict, Any, Callable, Optional, Union
from dataclasses import dataclass, field
from queue import Queue, Empty
from enum import Enum
from datetime import datetime, timedelta

from structlog import get_logger

try:
    from ..utils.errors import TelemetryError, ValidationError
except ImportError:
    # Fallback for direct execution
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from utils.errors import TelemetryError, ValidationError

logger = get_logger(__name__)


class SVGXTelemetryType(Enum):
    """SVGX-specific telemetry types"""
    SVGX_PARSER = "svgx_parser"          # SVGX parsing operations
    SVGX_RUNTIME = "svgx_runtime"         # SVGX runtime execution
    SVGX_COMPILER = "svgx_compiler"       # SVGX compilation operations
    SVGX_SYMBOL = "svgx_symbol"           # SVGX symbol operations
    SVGX_BEHAVIOR = "svgx_behavior"       # SVGX behavior execution
    SVGX_PHYSICS = "svgx_physics"         # SVGX physics simulation
    SVGX_CACHE = "svgx_cache"             # SVGX caching operations
    SVGX_SECURITY = "svgx_security"       # SVGX security events
    SVGX_EXPORT = "svgx_export"           # SVGX export operations
    SVGX_BIM = "svgx_bim"                 # SVGX BIM operations
    SVGX_PERFORMANCE = "svgx_performance" # SVGX performance metrics
    SVGX_ERROR = "svgx_error"             # SVGX error events


class SVGXTelemetrySeverity(Enum):
    """SVGX telemetry severity levels"""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class SVGXTelemetryRecord:
    """SVGX-specific telemetry record with enhanced metadata"""
    timestamp: float
    source: str
    type: SVGXTelemetryType
    value: Any
    namespace: str = "default"
    component: str = "unknown"
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    status: str = "OK"
    severity: SVGXTelemetrySeverity = SVGXTelemetrySeverity.INFO
    duration_ms: Optional[float] = None
    memory_usage_mb: Optional[float] = None
    cpu_usage_percent: Optional[float] = None
    meta: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate and set default values"""
        if not isinstance(self.type, SVGXTelemetryType):
            self.type = SVGXTelemetryType(self.type)
        if not isinstance(self.severity, SVGXTelemetrySeverity):
            self.severity = SVGXTelemetrySeverity(self.severity)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'timestamp': self.timestamp,
            'source': self.source,
            'type': self.type.value,
            'value': self.value,
            'namespace': self.namespace,
            'component': self.component,
            'user_id': self.user_id,
            'session_id': self.session_id,
            'status': self.status,
            'severity': self.severity.value,
            'duration_ms': self.duration_ms,
            'memory_usage_mb': self.memory_usage_mb,
            'cpu_usage_percent': self.cpu_usage_percent,
            'meta': self.meta
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SVGXTelemetryRecord':
        """Create from dictionary"""
        return cls(**data)


class SVGXTelemetryBuffer:
    """Thread-safe buffer for SVGX telemetry records with enhanced features"""
    
    def __init__(self, max_size: int = 10000, enable_persistence: bool = True):
        self.queue = Queue(maxsize=max_size)
        self.listeners: List[Callable[[SVGXTelemetryRecord], None]] = []
        self.running = False
        self.thread = None
        self.logger = get_logger(__name__)
        
        # SVGX-specific tracking
        self.namespace_stats: Dict[str, Dict[str, int]] = {}
        self.component_stats: Dict[str, Dict[str, int]] = {}
        self.severity_stats: Dict[str, int] = {}
        self.performance_metrics: Dict[str, List[float]] = {}
        
        # Persistence for Windows compatibility
        self.enable_persistence = enable_persistence
        if enable_persistence:
            self._setup_persistence()
    
    def _setup_persistence(self):
        """Setup persistence with Windows compatibility"""
        try:
            import tempfile
            temp_dir = tempfile.gettempdir()
            if platform.system() == "Windows":
                # Use unique filename to avoid conflicts
                self.persistence_file = os.path.join(
                    temp_dir, 
                    f"svgx_telemetry_{os.getpid()}_{int(time.time())}.jsonl"
                )
            else:
                self.persistence_file = os.path.join(temp_dir, "svgx_telemetry.jsonl")
        except Exception as e:
            self.logger.warning(f"Failed to setup persistence: {e}")
            self.enable_persistence = False
    
    def start(self):
        """Start the telemetry buffer processing"""
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._process, daemon=True)
            self.thread.start()
            self.logger.info("SVGX telemetry buffer started")
    
    def stop(self):
        """Stop the telemetry buffer processing"""
        self.running = False
        if self.thread:
            self.thread.join()
        self.logger.info("SVGX telemetry buffer stopped")
    
    def add_listener(self, listener: Callable[[SVGXTelemetryRecord], None]):
        """Add a listener for telemetry events"""
        self.listeners.append(listener)
    
    def ingest(self, record: SVGXTelemetryRecord):
        """Ingest a telemetry record"""
        try:
            # Update statistics
            self._update_stats(record)
            
            # Add to queue
            self.queue.put(record)
            
            # Persist if enabled
            if self.enable_persistence:
                self._persist_record(record)
                
        except Exception as e:
            self.logger.error(f"Failed to ingest telemetry record: {e}")
    
    def _update_stats(self, record: SVGXTelemetryRecord):
        """Update SVGX-specific statistics"""
        # Namespace statistics
        if record.namespace not in self.namespace_stats:
            self.namespace_stats[record.namespace] = {}
        self.namespace_stats[record.namespace][record.type.value] = \
            self.namespace_stats[record.namespace].get(record.type.value, 0) + 1
        
        # Component statistics
        if record.component not in self.component_stats:
            self.component_stats[record.component] = {}
        self.component_stats[record.component][record.type.value] = \
            self.component_stats[record.component].get(record.type.value, 0) + 1
        
        # Severity statistics
        self.severity_stats[record.severity.value] = \
            self.severity_stats.get(record.severity.value, 0) + 1
        
        # Performance metrics
        if record.duration_ms is not None:
            if record.type.value not in self.performance_metrics:
                self.performance_metrics[record.type.value] = []
            self.performance_metrics[record.type.value].append(record.duration_ms)
            
            # Keep only recent performance data
            if len(self.performance_metrics[record.type.value]) > 1000:
                self.performance_metrics[record.type.value] = \
                    self.performance_metrics[record.type.value][-500:]
    
    def _persist_record(self, record: SVGXTelemetryRecord):
        """Persist record to file with Windows compatibility"""
        try:
            with open(self.persistence_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(record.to_dict()) + '\n')
        except Exception as e:
            self.logger.error(f"Failed to persist telemetry record: {e}")
    
    def _process(self):
        """Process telemetry records in background thread"""
        while self.running:
            try:
                record = self.queue.get(timeout=0.5)
                for listener in self.listeners:
                    try:
                        listener(record)
                    except Exception as e:
                        self.logger.error(f"Listener error: {e}")
            except Empty:
                continue
    
    def get_stats(self) -> Dict[str, Any]:
        """Get SVGX-specific statistics"""
        return {
            'namespace_stats': self.namespace_stats,
            'component_stats': self.component_stats,
            'severity_stats': self.severity_stats,
            'performance_metrics': {
                k: {
                    'count': len(v),
                    'avg_duration_ms': sum(v) / len(v) if v else 0,
                    'min_duration_ms': min(v) if v else 0,
                    'max_duration_ms': max(v) if v else 0
                } for k, v in self.performance_metrics.items()
            },
            'queue_size': self.queue.qsize(),
            'listener_count': len(self.listeners)
        }


class SVGXTelemetryIngestor:
    """Ingests SVGX telemetry data from various sources with enhanced features"""
    
    def __init__(self, buffer: SVGXTelemetryBuffer):
        self.buffer = buffer
        self.logger = get_logger(__name__)
    
    def ingest_from_file(self, file_path: str, delay: float = 0.0, namespace: str = "default"):
        """Ingest SVGX telemetry from a JSONL file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    try:
                        data = json.loads(line.strip())
                        # Add namespace if not present
                        if 'namespace' not in data:
                            data['namespace'] = namespace
                        record = SVGXTelemetryRecord.from_dict(data)
                        self.buffer.ingest(record)
                        if delay > 0:
                            time.sleep(delay)
                    except Exception as e:
                        self.logger.error(f"Failed to ingest line {line_num}: {e}")
        except Exception as e:
            self.logger.error(f"Failed to ingest from file {file_path}: {e}")
            raise TelemetryError(f"File ingestion failed: {e}")
    
    def ingest_from_list(self, records: List[Dict[str, Any]], delay: float = 0.0):
        """Ingest SVGX telemetry from a list of dictionaries"""
        for i, data in enumerate(records):
            try:
                record = SVGXTelemetryRecord.from_dict(data)
                self.buffer.ingest(record)
                if delay > 0:
                    time.sleep(delay)
            except Exception as e:
                self.logger.error(f"Failed to ingest record {i}: {e}")
    
    def ingest_from_socket(self, socket, stop_event: threading.Event, namespace: str = "default"):
        """Ingest SVGX telemetry from a socket with namespace support"""
        while not stop_event.is_set():
            try:
                line = socket.recv(4096).decode('utf-8')
                if not line:
                    break
                data = json.loads(line)
                # Add namespace if not present
                if 'namespace' not in data:
                    data['namespace'] = namespace
                record = SVGXTelemetryRecord.from_dict(data)
                self.buffer.ingest(record)
            except Exception as e:
                self.logger.error(f"Socket ingest error: {e}")
    
    def ingest_svgx_operation(self, operation_type: SVGXTelemetryType, 
                             component: str, value: Any, namespace: str = "default",
                             user_id: str = None, session_id: str = None,
                             duration_ms: float = None, severity: SVGXTelemetrySeverity = SVGXTelemetrySeverity.INFO):
        """Ingest SVGX operation telemetry with performance tracking"""
        record = SVGXTelemetryRecord(
            timestamp=time.time(),
            source=f"svgx_engine.{component}",
            type=operation_type,
            value=value,
            namespace=namespace,
            component=component,
            user_id=user_id,
            session_id=session_id,
            duration_ms=duration_ms,
            severity=severity
        )
        self.buffer.ingest(record)
        return record


class SVGXTelemetryHook:
    """SVGX-specific telemetry hook for real-time monitoring and alerting"""
    
    def __init__(self):
        self.events: List[SVGXTelemetryRecord] = []
        self.alerts: List[str] = []
        self.logger = get_logger(__name__)
        
        # SVGX-specific thresholds
        self.thresholds = {
            SVGXTelemetryType.SVGX_PARSER: {'max_duration_ms': 5000},
            SVGXTelemetryType.SVGX_RUNTIME: {'max_duration_ms': 10000},
            SVGXTelemetryType.SVGX_COMPILER: {'max_duration_ms': 15000},
            SVGXTelemetryType.SVGX_CACHE: {'max_duration_ms': 1000},
            SVGXTelemetryType.SVGX_SECURITY: {'max_duration_ms': 2000}
        }
    
    def on_telemetry(self, record: SVGXTelemetryRecord):
        """Process incoming SVGX telemetry"""
        self.events.append(record)
        
        # Check for performance issues
        if record.duration_ms and record.type in self.thresholds:
            threshold = self.thresholds[record.type]['max_duration_ms']
            if record.duration_ms > threshold:
                alert = f"PERFORMANCE_ALERT: {record.type.value} from {record.component} took {record.duration_ms}ms (threshold: {threshold}ms)"
                self.alerts.append(alert)
                self.logger.warning(alert)
        
        # Check for errors
        if record.severity in [SVGXTelemetrySeverity.ERROR, SVGXTelemetrySeverity.CRITICAL]:
            alert = f"ERROR_ALERT: {record.severity.value} in {record.type.value} from {record.component}: {record.value}"
            self.alerts.append(alert)
            self.logger.error(alert)
        
        # Check for security events
        if record.type == SVGXTelemetryType.SVGX_SECURITY:
            if record.severity in [SVGXTelemetrySeverity.WARNING, SVGXTelemetrySeverity.ERROR, SVGXTelemetrySeverity.CRITICAL]:
                alert = f"SECURITY_ALERT: {record.severity.value} in {record.component}: {record.value}"
                self.alerts.append(alert)
                self.logger.warning(alert)
    
    def get_recent_events(self, limit: int = 100) -> List[SVGXTelemetryRecord]:
        """Get recent telemetry events"""
        return self.events[-limit:] if self.events else []
    
    def get_alerts(self, limit: int = 50) -> List[str]:
        """Get recent alerts"""
        return self.alerts[-limit:] if self.alerts else []
    
    def clear_events(self):
        """Clear stored events"""
        self.events.clear()
        self.alerts.clear()


# Utility functions for SVGX telemetry

def generate_svgx_simulated_telemetry(sources: List[str], types: List[SVGXTelemetryType], 
                                     count: int = 100, namespace: str = "default") -> List[Dict[str, Any]]:
    """Generate simulated SVGX telemetry data"""
    import random
    
    now = time.time()
    records = []
    
    for i in range(count):
        record = {
            "timestamp": now + i,
            "source": random.choice(sources),
            "type": random.choice(types).value,
            "value": random.uniform(0, 100),
            "namespace": namespace,
            "component": f"svgx_{random.choice(['parser', 'runtime', 'compiler', 'cache'])}",
            "status": "OK",
            "severity": random.choice([s.value for s in SVGXTelemetrySeverity]),
            "duration_ms": random.uniform(10, 5000),
            "memory_usage_mb": random.uniform(1, 100),
            "cpu_usage_percent": random.uniform(0, 50)
        }
        records.append(record)
    
    return records


def create_svgx_telemetry_buffer(max_size: int = 10000, enable_persistence: bool = True) -> SVGXTelemetryBuffer:
    """Create a configured SVGX telemetry buffer"""
    return SVGXTelemetryBuffer(max_size=max_size, enable_persistence=enable_persistence)


def create_svgx_telemetry_ingestor(buffer: SVGXTelemetryBuffer) -> SVGXTelemetryIngestor:
    """Create a configured SVGX telemetry ingestor"""
    return SVGXTelemetryIngestor(buffer)


def create_svgx_telemetry_hook() -> SVGXTelemetryHook:
    """Create a configured SVGX telemetry hook"""
    return SVGXTelemetryHook() 