"""
Telemetry Data Model and Ingestion Service

- Defines telemetry data schema
- Supports real-time and simulated data
- Ingests from file, API, or socket
- Provides hooks for live updates
"""

import threading
import time
import json
from typing import List, Dict, Any, Callable, Optional
from dataclasses import dataclass, field
from queue import Queue, Empty

from structlog import get_logger

logger = get_logger()

@dataclass
class TelemetryRecord:
    timestamp: float
    source: str
    type: str
    value: Any
    status: str = "OK"
    meta: Dict[str, Any] = field(default_factory=dict)

class TelemetryBuffer:
    """Thread-safe buffer for telemetry records"""
    def __init__(self, max_size: int = 10000):
        self.queue = Queue(maxsize=max_size)
        self.listeners: List[Callable[[TelemetryRecord], None]] = []
        self.running = False
        self.thread = None

    def start(self):
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._process, daemon=True)
            self.thread.start()

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join()

    def add_listener(self, listener: Callable[[TelemetryRecord], None]):
        self.listeners.append(listener)

    def ingest(self, record: TelemetryRecord):
        self.queue.put(record)

    def _process(self):
        while self.running:
            try:
                record = self.queue.get(timeout=0.5)
                for listener in self.listeners:
                    try:
                        listener(record)
                    except Exception as e:
                        logger.error(f"Listener error: {e}")
            except Empty:
                continue

class TelemetryIngestor:
    """Ingests telemetry data from various sources"""
    def __init__(self, buffer: TelemetryBuffer):
        self.buffer = buffer

    def ingest_from_file(self, file_path: str, delay: float = 0.0):
        """Ingest telemetry from a JSONL file (one record per line)"""
        with open(file_path, 'r') as f:
            for line in f:
                try:
                    data = json.loads(line)
                    record = TelemetryRecord(**data)
                    self.buffer.ingest(record)
                    if delay > 0:
                        time.sleep(delay)
                except Exception as e:
                    logger.error(f"Failed to ingest line: {e}")

    def ingest_from_list(self, records: List[Dict[str, Any]], delay: float = 0.0):
        for data in records:
            try:
                record = TelemetryRecord(**data)
                self.buffer.ingest(record)
                if delay > 0:
                    time.sleep(delay)
            except Exception as e:
                logger.error(f"Failed to ingest record: {e}")

    def ingest_from_socket(self, socket, stop_event: threading.Event):
        """Ingest telemetry from a socket (expects JSON per line)"""
        while not stop_event.is_set():
            try:
                line = socket.recv(4096).decode('utf-8')
                if not line:
                    break
                data = json.loads(line)
                record = TelemetryRecord(**data)
                self.buffer.ingest(record)
            except Exception as e:
                logger.error(f"Socket ingest error: {e}")

# Example hook for simulation or geometry resolver
class TelemetryHook:
    """Attach to buffer to react to telemetry in real time"""
    def __init__(self):
        self.events: List[TelemetryRecord] = []
        self.alerts: List[str] = []

    def on_telemetry(self, record: TelemetryRecord):
        self.events.append(record)
        # Example: trigger alert if value exceeds threshold
        if record.type == "temperature" and record.value > 80:
            alert = f"ALERT: High temperature from {record.source}: {record.value} at {record.timestamp}"
            self.alerts.append(alert)
            logger.warning(alert)

# Utility to simulate telemetry data
def generate_simulated_telemetry(sources: List[str], types: List[str], count: int = 100) -> List[Dict[str, Any]]:
    import random
    now = time.time()
    records = []
    for i in range(count):
        record = {
            "timestamp": now + i,
            "source": random.choice(sources),
            "type": random.choice(types),
            "value": random.uniform(0, 100),
            "status": "OK"
        }
        records.append(record)
    return records 