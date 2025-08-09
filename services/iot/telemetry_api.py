"""
BAS & IoT Telemetry API

Real-time telemetry data collection, processing, and storage for BAS and IoT devices.
Provides RESTful API endpoints for telemetry ingestion, querying, and analytics.
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
import sqlite3
import threading
from concurrent.futures import ThreadPoolExecutor
import aiohttp
from aiohttp import web
import numpy as np
from collections import defaultdict, deque
import hashlib
import hmac
import base64
import uuid

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class TelemetryPoint:
    """Single telemetry data point."""
    device_id: str
    capability_name: str
    value: Any
    timestamp: datetime
    quality: Optional[float] = None  # Data quality score (0-1)
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class TelemetryBatch:
    """Batch of telemetry data points."""
    device_id: str
    points: List[TelemetryPoint]
    batch_id: Optional[str] = None
    source: Optional[str] = None
    compression: Optional[str] = None


@dataclass
class TelemetryQuery:
    """Telemetry data query parameters."""
    device_ids: Optional[List[str]] = None
    capability_names: Optional[List[str]] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    limit: Optional[int] = 1000
    aggregation: Optional[str] = None  # avg, min, max, sum, count
    interval: Optional[str] = None  # 1m, 5m, 1h, 1d
    quality_threshold: Optional[float] = None


class TelemetryProcessor:
    """Process and validate telemetry data."""

    def __init__(self):
        pass
    """
    Perform __init__ operation

Args:
        None

Returns:
        Description of return value

Raises:
        Exception: Description of exception

Example:
        result = __init__(param)
        print(result)
    """
        self.validators = {}
        self.transformers = {}
        self.aggregators = {}
        self._init_default_processors()

    def _init_default_processors(self):
        """Initialize default processors."""
        # Default validators
        self.validators["range"] = self._validate_range
        self.validators["type"] = self._validate_type
        self.validators["rate_of_change"] = self._validate_rate_of_change

        # Default transformers
        self.transformers["unit_conversion"] = self._convert_units
        self.transformers["normalization"] = self._normalize_value
        self.transformers["filtering"] = self._filter_noise

        # Default aggregators
        self.aggregators["avg"] = self._aggregate_average
        self.aggregators["min"] = self._aggregate_min
        self.aggregators["max"] = self._aggregate_max
        self.aggregators["sum"] = self._aggregate_sum
        self.aggregators["count"] = self._aggregate_count

    def validate_point(self, point: TelemetryPoint, rules: Dict[str, Any]) -> bool:
        """Validate a telemetry point against rules."""
        try:
            for validator_name, validator_config in rules.get("validators", {}).items():
                validator = self.validators.get(validator_name)
                if validator and not validator(point, validator_config):
                    return False
            return True
        except Exception as e:
            logger.error(f"Validation error: {e}")
            return False

    def transform_point(self, point: TelemetryPoint, rules: Dict[str, Any]) -> TelemetryPoint:
        """Transform a telemetry point according to rules."""
        try:
            for transformer_name, transformer_config in rules.get("transformers", {}).items():
                transformer = self.transformers.get(transformer_name)
                if transformer:
                    point = transformer(point, transformer_config)
            return point
        except Exception as e:
            logger.error(f"Transformation error: {e}")
            return point

    def aggregate_points(self, points: List[TelemetryPoint],
                        aggregation_type: str, interval: str) -> List[TelemetryPoint]:
        """Aggregate telemetry points."""
        try:
            aggregator = self.aggregators.get(aggregation_type)
            if not aggregator:
                return points

            # Group points by time interval
            grouped_points = self._group_by_interval(points, interval)

            aggregated_points = []
            for interval_start, interval_points in grouped_points.items():
                aggregated_value = aggregator(interval_points)
                aggregated_point = TelemetryPoint(
                    device_id=interval_points[0].device_id,
                    capability_name=interval_points[0].capability_name,
                    value=aggregated_value,
                    timestamp=interval_start,
                    quality=np.mean([p.quality or 1.0 for p in interval_points])
                aggregated_points.append(aggregated_point)

            return aggregated_points

        except Exception as e:
            logger.error(f"Aggregation error: {e}")
            return points

    def _validate_range(self, point: TelemetryPoint, config: Dict[str, Any]) -> bool:
        """Validate value is within specified range."""
        min_val = config.get("min")
        max_val = config.get("max")

        if min_val is not None and point.value < min_val:
            return False
        if max_val is not None and point.value > max_val:
            return False

        return True

    def _validate_type(self, point: TelemetryPoint, config: Dict[str, Any]) -> bool:
        """Validate value type."""
        expected_type = config.get("type")
        if expected_type == "number" and not isinstance(point.value, (int, float)):
            return False
        elif expected_type == "boolean" and not isinstance(point.value, bool):
            return False
        elif expected_type == "string" and not isinstance(point.value, str):
            return False

        return True

    def _validate_rate_of_change(self, point: TelemetryPoint, config: Dict[str, Any]) -> bool:
        """Validate rate of change."""
        # This would need historical data to implement properly
        return True

    def _convert_units(self, point: TelemetryPoint, config: Dict[str, Any]) -> TelemetryPoint:
        """Convert units."""
        from_unit = config.get("from")
        to_unit = config.get("to")

        if from_unit and to_unit and isinstance(point.value, (int, float)):
            # Simple unit conversion examples
            if from_unit == "celsius" and to_unit == "fahrenheit":
                point.value = (point.value * 9/5) + 32
            elif from_unit == "fahrenheit" and to_unit == "celsius":
                point.value = (point.value - 32) * 5/9
            elif from_unit == "psi" and to_unit == "kpa":
                point.value = point.value * 6.89476
            elif from_unit == "kpa" and to_unit == "psi":
                point.value = point.value / 6.89476

        return point

    def _normalize_value(self, point: TelemetryPoint, config: Dict[str, Any]) -> TelemetryPoint:
        """Normalize value to 0-1 range."""
        min_val = config.get("min", 0)
        max_val = config.get("max", 1)

        if isinstance(point.value, (int, float)) and max_val > min_val:
            point.value = (point.value - min_val) / (max_val - min_val)

        return point

    def _filter_noise(self, point: TelemetryPoint, config: Dict[str, Any]) -> TelemetryPoint:
        """Filter noise from signal."""
        # Simple moving average filter
        window_size = config.get("window_size", 5)
        # This would need historical data to implement properly
        return point

    def _aggregate_average(self, points: List[TelemetryPoint]) -> float:
        """Calculate average of numeric values."""
        numeric_values = [p.value for p in points if isinstance(p.value, (int, float))]
        return np.mean(numeric_values) if numeric_values else 0

    def _aggregate_min(self, points: List[TelemetryPoint]) -> float:
        """Calculate minimum of numeric values."""
        numeric_values = [p.value for p in points if isinstance(p.value, (int, float))]
        return np.min(numeric_values) if numeric_values else 0

    def _aggregate_max(self, points: List[TelemetryPoint]) -> float:
        """Calculate maximum of numeric values."""
        numeric_values = [p.value for p in points if isinstance(p.value, (int, float))]
        return np.max(numeric_values) if numeric_values else 0

    def _aggregate_sum(self, points: List[TelemetryPoint]) -> float:
        """Calculate sum of numeric values."""
        numeric_values = [p.value for p in points if isinstance(p.value, (int, float))]
        return np.sum(numeric_values) if numeric_values else 0

    def _aggregate_count(self, points: List[TelemetryPoint]) -> int:
        """Count number of points."""
        return len(points)

    def _group_by_interval(self, points: List[TelemetryPoint],
                          interval: str) -> Dict[datetime, List[TelemetryPoint]]:
        """Group points by time interval."""
        grouped = defaultdict(list)

        for point in points:
            interval_start = self._get_interval_start(point.timestamp, interval)
            grouped[interval_start].append(point)

        return dict(grouped)

    def _get_interval_start(self, timestamp: datetime, interval: str) -> datetime:
        """Get the start of the interval containing the timestamp."""
        if interval == "1m":
            return timestamp.replace(second=0, microsecond=0)
        elif interval == "5m":
            minutes = (timestamp.minute // 5) * 5
            return timestamp.replace(minute=minutes, second=0, microsecond=0)
        elif interval == "1h":
            return timestamp.replace(minute=0, second=0, microsecond=0)
        elif interval == "1d":
            return timestamp.replace(hour=0, minute=0, second=0, microsecond=0)
        else:
            return timestamp


class TelemetryStorage:
    """
    Perform __init__ operation

Args:
        db_path: Description of db_path

Returns:
        Description of return value

Raises:
        Exception: Description of exception

Example:
        result = __init__(param)
        print(result)
    """
    """Store and retrieve telemetry data."""

    def __init__(self, db_path: str = "telemetry.db"):
        self.db_path = db_path
        self.cache = {}
        self.cache_size = 10000
        self.lock = threading.RLock()
        self._init_database()

    def _init_database(self):
        """Initialize telemetry database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Main telemetry table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS telemetry (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        device_id TEXT NOT NULL,
                        capability_name TEXT NOT NULL,
                        value TEXT NOT NULL,
                        timestamp TEXT NOT NULL,
                        quality REAL,
                        metadata TEXT,
                        created_at TEXT NOT NULL
                    )
                """)
                # Indexes for performance
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_telemetry_device_time
                    ON telemetry(device_id, timestamp)
                """)
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_telemetry_capability
                    ON telemetry(capability_name)
                """)
                # Aggregated data table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS telemetry_aggregated (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        device_id TEXT NOT NULL,
                        capability_name TEXT NOT NULL,
                        aggregation_type TEXT NOT NULL,
                        interval TEXT NOT NULL,
                        value TEXT NOT NULL,
                        timestamp TEXT NOT NULL,
                        quality REAL,
                        created_at TEXT NOT NULL
                    )
                """)
                # Batch processing table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS telemetry_batches (
                        batch_id TEXT PRIMARY KEY,
                        device_id TEXT NOT NULL,
                        source TEXT,
                        compression TEXT,
                        point_count INTEGER,
                        created_at TEXT NOT NULL
                    )
                """)
                conn.commit()
                logger.info("Telemetry database initialized")

        except Exception as e:
            logger.error(f"Failed to initialize telemetry database: {e}")
            raise

    def store_point(self, point: TelemetryPoint) -> bool:
        """Store a single telemetry point."""
        try:
            with self.lock:
                # Add to cache
                cache_key = f"{point.device_id}:{point.capability_name}"
                if cache_key not in self.cache:
                    self.cache[cache_key] = deque(maxlen=100)

                self.cache[cache_key].append(point)

                # Store in database
                with sqlite3.connect(self.db_path) as conn:
                    conn.execute("""
                        INSERT INTO telemetry
                        (device_id, capability_name, value, timestamp, quality, metadata, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, ("
                        point.device_id,
                        point.capability_name,
                        json.dumps(point.value),
                        point.timestamp.isoformat(),
                        point.quality,
                        json.dumps(point.metadata) if point.metadata else None,
                        datetime.utcnow().isoformat()
                    ))
                    conn.commit()

                return True

        except Exception as e:
            logger.error(f"Failed to store telemetry point: {e}")
            return False

    def store_batch(self, batch: TelemetryBatch) -> bool:
        """Store a batch of telemetry points."""
        try:
            with self.lock:
                # Store batch metadata
                with sqlite3.connect(self.db_path) as conn:
                    conn.execute("""
                        INSERT INTO telemetry_batches
                        (batch_id, device_id, source, compression, point_count, created_at)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, ("
                        batch.batch_id or str(uuid.uuid4()),
                        batch.device_id,
                        batch.source,
                        batch.compression,
                        len(batch.points),
                        datetime.utcnow().isoformat()
                    ))

                    # Store all points
                    for point in batch.points:
                        conn.execute("""
                            INSERT INTO telemetry
                            (device_id, capability_name, value, timestamp, quality, metadata, created_at)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                        """, ("
                            point.device_id,
                            point.capability_name,
                            json.dumps(point.value),
                            point.timestamp.isoformat(),
                            point.quality,
                            json.dumps(point.metadata) if point.metadata else None,
                            datetime.utcnow().isoformat()
                        ))

                    conn.commit()

                return True

        except Exception as e:
            logger.error(f"Failed to store telemetry batch: {e}")
            return False

    def query_points(self, query: TelemetryQuery) -> List[TelemetryPoint]:
        """Query telemetry points."""
        try:
            sql = "SELECT * FROM telemetry WHERE 1=1"
            params = []

            if query.device_ids:
                placeholders = ",".join(["?" for _ in query.device_ids])
                sql += f" AND device_id IN ({placeholders})
                params.extend(query.device_ids)

            if query.capability_names:
                placeholders = ",".join(["?" for _ in query.capability_names])
                sql += f" AND capability_name IN ({placeholders})
                params.extend(query.capability_names)

            if query.start_time:
                sql += " AND timestamp >= ?"
                params.append(query.start_time.isoformat()
            if query.end_time:
                sql += " AND timestamp <= ?"
                params.append(query.end_time.isoformat()
            if query.quality_threshold:
                sql += " AND quality >= ?"
                params.append(query.quality_threshold)

            sql += " ORDER BY timestamp DESC"

            if query.limit:
                sql += f" LIMIT {query.limit}"

            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(sql, params)
                points = []
                for row in cursor.fetchall():
                    point = TelemetryPoint(
                        device_id=row[1],
                        capability_name=row[2],
                        value=json.loads(row[3]),
                        timestamp=datetime.fromisoformat(row[4]),
                        quality=row[5],
                        metadata=json.loads(row[6]) if row[6] else None
                    )
                    points.append(point)

                return points

        except Exception as e:
            logger.error(f"Failed to query telemetry points: {e}")
            return []

    def get_latest_points(self, device_ids: Optional[List[str]] = None,
                         capability_names: Optional[List[str]] = None) -> List[TelemetryPoint]:
        """Get latest telemetry points for devices/capabilities."""
        try:
            sql = """
                SELECT t1.* FROM telemetry t1
                INNER JOIN (
                    SELECT device_id, capability_name, MAX(timestamp) as max_timestamp
                    FROM telemetry
                    GROUP BY device_id, capability_name
                ) t2 ON t1.device_id = t2.device_id
                    AND t1.capability_name = t2.capability_name
                    AND t1.timestamp = t2.max_timestamp
            """
            params = []

            if device_ids:
                placeholders = ",".join(["?" for _ in device_ids])
                sql += f" WHERE t1.device_id IN ({placeholders})
                params.extend(device_ids)

            if capability_names:
                clause = "AND" if device_ids else "WHERE"
                placeholders = ",".join(["?" for _ in capability_names])
                sql += f" {clause} t1.capability_name IN ({placeholders})
                params.extend(capability_names)

            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(sql, params)
                points = []
                for row in cursor.fetchall():
                    point = TelemetryPoint(
                        device_id=row[1],
                        capability_name=row[2],
                        value=json.loads(row[3]),
                        timestamp=datetime.fromisoformat(row[4]),
                        quality=row[5],
                        metadata=json.loads(row[6]) if row[6] else None
                    )
                    points.append(point)

                return points

        except Exception as e:
            logger.error(f"Failed to get latest points: {e}")
            return []

    def store_aggregated_data(self, points: List[TelemetryPoint],
                            aggregation_type: str, interval: str) -> bool:
        """Store aggregated telemetry data."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                for point in points:
                    conn.execute("""
                        INSERT INTO telemetry_aggregated
                        (device_id, capability_name, aggregation_type, interval, value, timestamp, quality, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, ("
                        point.device_id,
                        point.capability_name,
                        aggregation_type,
                        interval,
                        json.dumps(point.value),
                        point.timestamp.isoformat(),
                        point.quality,
                        datetime.utcnow().isoformat()
                    ))
                conn.commit()
            return True
        except Exception as e:
            logger.error(f"Failed to store aggregated data: {e}")
            return False


class TelemetryAPI:
    """RESTful API for telemetry data."""

    def __init__(self, storage: TelemetryStorage, processor: TelemetryProcessor):
        self.storage = storage
        self.processor = processor
        self.app = web.Application()
        self._setup_routes()

    def _setup_routes(self):
        """Setup API routes."""
        self.app.router.add_post('/telemetry/point', self.store_point)
        self.app.router.add_post('/telemetry/batch', self.store_batch)
        self.app.router.add_get('/telemetry/query', self.query_points)
        self.app.router.add_get('/telemetry/latest', self.get_latest)
        self.app.router.add_get('/telemetry/aggregated', self.get_aggregated)
        self.app.router.add_get('/telemetry/stats', self.get_stats)
        self.app.router.add_post('/telemetry/process', self.process_points)

    async def store_point(self, request: web.Request) -> web.Response:
        """Store a single telemetry point."""
        try:
            data = await request.json()

            point = TelemetryPoint(
                device_id=data['device_id'],
                capability_name=data['capability_name'],
                value=data['value'],
                timestamp=datetime.fromisoformat(data['timestamp']),
                quality=data.get('quality'),
                metadata=data.get('metadata')
            # Apply processing rules if provided
            rules = data.get('processing_rules', {})
            if rules:
                if not self.processor.validate_point(point, rules):
                    return web.json_response(
                        {'error': 'Validation failed'},
                        status=400
                    )
                point = self.processor.transform_point(point, rules)

            success = self.storage.store_point(point)

            if success:
                return web.json_response({'status': 'success'})
            else:
                return web.json_response(
                    {'error': 'Failed to store point'},
                    status=500
                )

        except Exception as e:
            logger.error(f"Store point error: {e}")
            return web.json_response(
                {'error': str(e)},
                status=400
            )

    async def store_batch(self, request: web.Request) -> web.Response:
        """Store a batch of telemetry points."""
        try:
            data = await request.json()

            points = []
            for point_data in data['points']:
                point = TelemetryPoint(
                    device_id=point_data['device_id'],
                    capability_name=point_data['capability_name'],
                    value=point_data['value'],
                    timestamp=datetime.fromisoformat(point_data['timestamp']),
                    quality=point_data.get('quality'),
                    metadata=point_data.get('metadata')
                points.append(point)

            batch = TelemetryBatch(
                device_id=data['device_id'],
                points=points,
                batch_id=data.get('batch_id'),
                source=data.get('source'),
                compression=data.get('compression')
            success = self.storage.store_batch(batch)

            if success:
                return web.json_response({'status': 'success'})
            else:
                return web.json_response(
                    {'error': 'Failed to store batch'},
                    status=500
                )

        except Exception as e:
            logger.error(f"Store batch error: {e}")
            return web.json_response(
                {'error': str(e)},
                status=400
            )

    async def query_points(self, request: web.Request) -> web.Response:
        """Query telemetry points."""
        try:
            # Parse query parameters
            device_ids = request.query.get('device_ids', '').split(',') if request.query.get('device_ids') else None
            capability_names = request.query.get('capability_names', '').split(',') if request.query.get('capability_names') else None
            start_time = datetime.fromisoformat(request.query['start_time']) if request.query.get('start_time') else None
            end_time = datetime.fromisoformat(request.query['end_time']) if request.query.get('end_time') else None
            limit = int(request.query['limit']) if request.query.get('limit') else 1000
            quality_threshold = float(request.query['quality_threshold']) if request.query.get('quality_threshold') else None

            query = TelemetryQuery(
                device_ids=device_ids,
                capability_names=capability_names,
                start_time=start_time,
                end_time=end_time,
                limit=limit,
                quality_threshold=quality_threshold
            )

            points = self.storage.query_points(query)

            # Convert to JSON-serializable format
            result = []
            for point in points:
                result.append({
                    'device_id': point.device_id,
                    'capability_name': point.capability_name,
                    'value': point.value,
                    'timestamp': point.timestamp.isoformat(),
                    'quality': point.quality,
                    'metadata': point.metadata
                })

            return web.json_response({'points': result})

        except Exception as e:
            logger.error(f"Query points error: {e}")
            return web.json_response(
                {'error': str(e)},
                status=400
            )

    async def get_latest(self, request: web.Request) -> web.Response:
        """Get latest telemetry points."""
        try:
            device_ids = request.query.get('device_ids', '').split(',') if request.query.get('device_ids') else None
            capability_names = request.query.get('capability_names', '').split(',') if request.query.get('capability_names') else None

            points = self.storage.get_latest_points(device_ids, capability_names)

            result = []
            for point in points:
                result.append({
                    'device_id': point.device_id,
                    'capability_name': point.capability_name,
                    'value': point.value,
                    'timestamp': point.timestamp.isoformat(),
                    'quality': point.quality,
                    'metadata': point.metadata
                })

            return web.json_response({'points': result})

        except Exception as e:
            logger.error(f"Get latest error: {e}")
            return web.json_response(
                {'error': str(e)},
                status=400
            )

    async def get_aggregated(self, request: web.Request) -> web.Response:
        """Get aggregated telemetry data."""
        try:
            # Parse query parameters
            device_ids = request.query.get('device_ids', '').split(',') if request.query.get('device_ids') else None
            capability_names = request.query.get('capability_names', '').split(',') if request.query.get('capability_names') else None
            start_time = datetime.fromisoformat(request.query['start_time']) if request.query.get('start_time') else None
            end_time = datetime.fromisoformat(request.query['end_time']) if request.query.get('end_time') else None
            aggregation = request.query.get('aggregation', 'avg')
            interval = request.query.get('interval', '1h')

            # Query raw points
            query = TelemetryQuery(
                device_ids=device_ids,
                capability_names=capability_names,
                start_time=start_time,
                end_time=end_time
            )

            points = self.storage.query_points(query)

            # Aggregate points
            aggregated_points = self.processor.aggregate_points(points, aggregation, interval)

            # Store aggregated data
            self.storage.store_aggregated_data(aggregated_points, aggregation, interval)

            result = []
            for point in aggregated_points:
                result.append({
                    'device_id': point.device_id,
                    'capability_name': point.capability_name,
                    'value': point.value,
                    'timestamp': point.timestamp.isoformat(),
                    'quality': point.quality
                })

            return web.json_response({'points': result})

        except Exception as e:
            logger.error(f"Get aggregated error: {e}")
            return web.json_response(
                {'error': str(e)},
                status=400
            )

    async def get_stats(self, request: web.Request) -> web.Response:
        """Get telemetry statistics."""
        try:
            with sqlite3.connect(self.storage.db_path) as conn:
                # Get basic stats
                cursor = conn.execute("SELECT COUNT(*) FROM telemetry")
                total_points = cursor.fetchone()[0]

                cursor = conn.execute("SELECT COUNT(DISTINCT device_id) FROM telemetry")
                unique_devices = cursor.fetchone()[0]

                cursor = conn.execute("SELECT COUNT(DISTINCT capability_name) FROM telemetry")
                unique_capabilities = cursor.fetchone()[0]

                # Get recent activity
                cursor = conn.execute("""
                    SELECT COUNT(*) FROM telemetry
                    WHERE timestamp >= datetime('now', '-1 hour')
                """)
                points_last_hour = cursor.fetchone()[0]

                cursor = conn.execute("""
                    SELECT COUNT(*) FROM telemetry
                    WHERE timestamp >= datetime('now', '-24 hours')
                """)
                points_last_day = cursor.fetchone()[0]

                stats = {
                    'total_points': total_points,
                    'unique_devices': unique_devices,
                    'unique_capabilities': unique_capabilities,
                    'points_last_hour': points_last_hour,
                    'points_last_day': points_last_day
                }

                return web.json_response(stats)

        except Exception as e:
            logger.error(f"Get stats error: {e}")
            return web.json_response(
                {'error': str(e)},
                status=400
            )

    async def process_points(self, request: web.Request) -> web.Response:
        """Process telemetry points with custom rules."""
        try:
            data = await request.json()
            points_data = data['points']
            rules = data['rules']

            processed_points = []
            for point_data in points_data:
                point = TelemetryPoint(
                    device_id=point_data['device_id'],
                    capability_name=point_data['capability_name'],
                    value=point_data['value'],
                    timestamp=datetime.fromisoformat(point_data['timestamp']),
                    quality=point_data.get('quality'),
                    metadata=point_data.get('metadata')
                # Apply processing
                if self.processor.validate_point(point, rules):
                    processed_point = self.processor.transform_point(point, rules)
                    processed_points.append(processed_point)

            result = []
            for point in processed_points:
                result.append({
                    'device_id': point.device_id,
                    'capability_name': point.capability_name,
                    'value': point.value,
                    'timestamp': point.timestamp.isoformat(),
                    'quality': point.quality,
                    'metadata': point.metadata
                })

            return web.json_response({'points': result})

        except Exception as e:
            logger.error(f"Process points error: {e}")
            return web.json_response(
                {'error': str(e)},
                status=400
            )


def run_telemetry_api(host: str = 'localhost', port: int = 8080):
    """Run the telemetry API server."""
    storage = TelemetryStorage()
    processor = TelemetryProcessor()
    api = TelemetryAPI(storage, processor)

    web.run_app(api.app, host=host, port=port)


if __name__ == "__main__":
    run_telemetry_api()
