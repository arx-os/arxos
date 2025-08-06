"""
Test cases for the Arxos BAS & IoT Telemetry API.

This module contains comprehensive tests for telemetry data collection,
processing, querying, and export functionality.
"""

import pytest
import tempfile
import os
import json
import pandas as pd
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock, patch

# Import the telemetry API module
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from telemetry_api import TelemetryAPI, TelemetryData, ExportFormat


class TestTelemetryAPI:
    """Test cases for TelemetryAPI class."""

    @pytest.fixture
    def temp_db(self):
        """Create a temporary database for testing."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        yield db_path

        # Cleanup
        if os.path.exists(db_path):
            os.unlink(db_path)

    @pytest.fixture
    def telemetry_api(self, temp_db):
        """Create a TelemetryAPI instance with temporary database."""
        api = TelemetryAPI(database_url=f"sqlite:///{temp_db}")
        api.initialize_database()
        return api

    def test_initialize_database(self, temp_db):
        """Test database initialization."""
        api = TelemetryAPI(database_url=f"sqlite:///{temp_db}")
        api.initialize_database()

        # Verify database was created
        assert os.path.exists(temp_db)

    def test_submit_data(self, telemetry_api):
        """Test submitting telemetry data."""
        data = {
            "device_id": "test_sensor_001",
            "timestamp": "2024-01-15T10:30:00Z",
            "data": {"temperature": 22.5, "humidity": 45.2, "battery_level": 85},
        }

        result = telemetry_api.submit_data(**data)

        assert result["device_id"] == "test_sensor_001"
        assert result["timestamp"] == "2024-01-15T10:30:00Z"
        assert result["data"]["temperature"] == 22.5

    def test_submit_data_with_metadata(self, telemetry_api):
        """Test submitting telemetry data with metadata."""
        data = {
            "device_id": "test_sensor_002",
            "timestamp": "2024-01-15T10:30:00Z",
            "data": {"temperature": 23.1, "humidity": 47.8},
            "metadata": {
                "location": "Building A, Room 101",
                "operator": "system_auto",
                "quality_score": 0.95,
            },
        }

        result = telemetry_api.submit_data(**data)

        assert result["device_id"] == "test_sensor_002"
        assert result["metadata"]["location"] == "Building A, Room 101"
        assert result["metadata"]["quality_score"] == 0.95

    def test_submit_batch_data(self, telemetry_api):
        """Test submitting batch telemetry data."""
        batch_data = [
            {
                "device_id": "batch_sensor_001",
                "timestamp": "2024-01-15T10:00:00Z",
                "data": {"temperature": 22.0, "humidity": 45.0},
            },
            {
                "device_id": "batch_sensor_001",
                "timestamp": "2024-01-15T10:05:00Z",
                "data": {"temperature": 22.1, "humidity": 45.1},
            },
            {
                "device_id": "batch_sensor_001",
                "timestamp": "2024-01-15T10:10:00Z",
                "data": {"temperature": 22.2, "humidity": 45.2},
            },
        ]

        results = telemetry_api.submit_batch_data(batch_data)

        assert len(results) == 3
        assert all(result["status"] == "success" for result in results)

    def test_query_data(self, telemetry_api):
        """Test querying telemetry data."""
        # Submit some test data
        test_data = [
            {
                "device_id": "query_sensor_001",
                "timestamp": "2024-01-15T10:00:00Z",
                "data": {"temperature": 22.0, "humidity": 45.0},
            },
            {
                "device_id": "query_sensor_001",
                "timestamp": "2024-01-15T10:05:00Z",
                "data": {"temperature": 22.1, "humidity": 45.1},
            },
            {
                "device_id": "query_sensor_001",
                "timestamp": "2024-01-15T10:10:00Z",
                "data": {"temperature": 22.2, "humidity": 45.2},
            },
        ]

        for data in test_data:
            telemetry_api.submit_data(**data)

        # Query the data
        query_result = telemetry_api.query_data(
            device_id="query_sensor_001",
            start_time="2024-01-15T10:00:00Z",
            end_time="2024-01-15T10:15:00Z",
            metrics=["temperature", "humidity"],
        )

        assert len(query_result) == 3
        assert all("temperature" in record["data"] for record in query_result)
        assert all("humidity" in record["data"] for record in query_result)

    def test_query_data_with_aggregation(self, telemetry_api):
        """Test querying data with aggregation."""
        # Submit test data
        test_data = [
            {
                "device_id": "agg_sensor",
                "timestamp": "2024-01-15T10:00:00Z",
                "data": {"temperature": 20.0},
            },
            {
                "device_id": "agg_sensor",
                "timestamp": "2024-01-15T10:05:00Z",
                "data": {"temperature": 22.0},
            },
            {
                "device_id": "agg_sensor",
                "timestamp": "2024-01-15T10:10:00Z",
                "data": {"temperature": 24.0},
            },
            {
                "device_id": "agg_sensor",
                "timestamp": "2024-01-15T10:15:00Z",
                "data": {"temperature": 26.0},
            },
        ]

        for data in test_data:
            telemetry_api.submit_data(**data)

        # Query with aggregation
        agg_result = telemetry_api.query_data(
            device_id="agg_sensor",
            start_time="2024-01-15T10:00:00Z",
            end_time="2024-01-15T10:20:00Z",
            metrics=["temperature"],
            aggregation="hourly",
        )

        assert len(agg_result) > 0
        assert "aggregated_data" in agg_result[0]

    def test_export_data_csv(self, telemetry_api, tmp_path):
        """Test exporting data to CSV format."""
        # Submit test data
        test_data = [
            {
                "device_id": "export_sensor",
                "timestamp": "2024-01-15T10:00:00Z",
                "data": {"temperature": 22.0},
            },
            {
                "device_id": "export_sensor",
                "timestamp": "2024-01-15T10:05:00Z",
                "data": {"temperature": 22.1},
            },
            {
                "device_id": "export_sensor",
                "timestamp": "2024-01-15T10:10:00Z",
                "data": {"temperature": 22.2},
            },
        ]

        for data in test_data:
            telemetry_api.submit_data(**data)

        # Export to CSV
        output_file = tmp_path / "telemetry_export.csv"
        result = telemetry_api.export_data(
            device_ids=["export_sensor"],
            start_time="2024-01-15T10:00:00Z",
            end_time="2024-01-15T10:15:00Z",
            format=ExportFormat.CSV,
            output_file=str(output_file),
        )

        assert result["status"] == "success"
        assert output_file.exists()

        # Verify CSV content
        df = pd.read_csv(output_file)
        assert len(df) == 3
        assert "temperature" in df.columns

    def test_export_data_json(self, telemetry_api, tmp_path):
        """Test exporting data to JSON format."""
        # Submit test data
        test_data = [
            {
                "device_id": "json_export_sensor",
                "timestamp": "2024-01-15T10:00:00Z",
                "data": {"temperature": 22.0},
            },
            {
                "device_id": "json_export_sensor",
                "timestamp": "2024-01-15T10:05:00Z",
                "data": {"temperature": 22.1},
            },
        ]

        for data in test_data:
            telemetry_api.submit_data(**data)

        # Export to JSON
        output_file = tmp_path / "telemetry_export.json"
        result = telemetry_api.export_data(
            device_ids=["json_export_sensor"],
            start_time="2024-01-15T10:00:00Z",
            end_time="2024-01-15T10:10:00Z",
            format=ExportFormat.JSON,
            output_file=str(output_file),
        )

        assert result["status"] == "success"
        assert output_file.exists()

        # Verify JSON content
        with open(output_file, "r") as f:
            data = json.load(f)
        assert len(data) == 2
        assert data[0]["device_id"] == "json_export_sensor"

    def test_export_data_parquet(self, telemetry_api, tmp_path):
        """Test exporting data to Parquet format."""
        # Submit test data
        test_data = [
            {
                "device_id": "parquet_export_sensor",
                "timestamp": "2024-01-15T10:00:00Z",
                "data": {"temperature": 22.0},
            },
            {
                "device_id": "parquet_export_sensor",
                "timestamp": "2024-01-15T10:05:00Z",
                "data": {"temperature": 22.1},
            },
        ]

        for data in test_data:
            telemetry_api.submit_data(**data)

        # Export to Parquet
        output_file = tmp_path / "telemetry_export.parquet"
        result = telemetry_api.export_data(
            device_ids=["parquet_export_sensor"],
            start_time="2024-01-15T10:00:00Z",
            end_time="2024-01-15T10:10:00Z",
            format=ExportFormat.PARQUET,
            output_file=str(output_file),
        )

        assert result["status"] == "success"
        assert output_file.exists()

        # Verify Parquet content
        df = pd.read_parquet(output_file)
        assert len(df) == 2
        assert "temperature" in df.columns

    def test_data_compression(self, telemetry_api):
        """Test data compression functionality."""
        # Submit data that should be compressed
        large_data = {
            "device_id": "compression_test_sensor",
            "timestamp": "2024-01-15T10:00:00Z",
            "data": {
                "temperature": 22.5,
                "humidity": 45.2,
                "pressure": 1013.25,
                "wind_speed": 5.2,
                "wind_direction": 180,
                "solar_radiation": 850.5,
                "uv_index": 3.2,
                "air_quality": 45,
                "co2_level": 450,
                "voc_level": 0.8,
            },
        }

        result = telemetry_api.submit_data(**large_data)

        # Verify data was stored (compression is internal)
        assert result["device_id"] == "compression_test_sensor"
        assert result["data"]["temperature"] == 22.5

    def test_data_validation(self, telemetry_api):
        """Test data validation."""
        # Test invalid device ID
        invalid_data = {
            "device_id": "",  # Empty device ID
            "timestamp": "2024-01-15T10:00:00Z",
            "data": {"temperature": 22.5},
        }

        with pytest.raises(ValueError, match="Device ID cannot be empty"):
            telemetry_api.submit_data(**invalid_data)

        # Test invalid timestamp
        invalid_data = {
            "device_id": "test_sensor",
            "timestamp": "invalid_timestamp",
            "data": {"temperature": 22.5},
        }

        with pytest.raises(ValueError, match="Invalid timestamp format"):
            telemetry_api.submit_data(**invalid_data)

        # Test empty data
        invalid_data = {
            "device_id": "test_sensor",
            "timestamp": "2024-01-15T10:00:00Z",
            "data": {},
        }

        with pytest.raises(ValueError, match="Data cannot be empty"):
            telemetry_api.submit_data(**invalid_data)

    def test_data_retention(self, telemetry_api):
        """Test data retention policies."""
        # Submit old data
        old_data = {
            "device_id": "retention_test_sensor",
            "timestamp": "2020-01-15T10:00:00Z",  # Old data
            "data": {"temperature": 22.5},
        }

        telemetry_api.submit_data(**old_data)

        # Apply retention policy (keep only last 30 days)
        deleted_count = telemetry_api.apply_retention_policy(days=30)

        # Verify old data was deleted
        query_result = telemetry_api.query_data(
            device_id="retention_test_sensor",
            start_time="2020-01-15T00:00:00Z",
            end_time="2020-01-15T23:59:59Z",
        )

        assert len(query_result) == 0

    def test_alert_configuration(self, telemetry_api):
        """Test alert configuration and triggering."""
        # Configure alert
        alert_config = {
            "device_id": "alert_test_sensor",
            "metric": "temperature",
            "condition": ">",
            "threshold": 25.0,
            "duration": 300,  # 5 minutes
            "notification": {
                "email": "admin@arxos.com",
                "webhook": "https://hooks.slack.com/alert",
            },
        }

        telemetry_api.configure_alert(**alert_config)

        # Submit data that should trigger alert
        alert_data = {
            "device_id": "alert_test_sensor",
            "timestamp": "2024-01-15T10:00:00Z",
            "data": {"temperature": 26.0},  # Above threshold
        }

        with patch.object(telemetry_api, "_send_alert") as mock_send_alert:
            telemetry_api.submit_data(**alert_data)
            mock_send_alert.assert_called_once()

    def test_performance_metrics(self, telemetry_api):
        """Test performance metrics collection."""
        # Submit multiple data points
        for i in range(100):
            data = {
                "device_id": "perf_test_sensor",
                "timestamp": f"2024-01-15T10:{i:02d}:00Z",
                "data": {"temperature": 22.0 + i * 0.1},
            }
            telemetry_api.submit_data(**data)

        # Get performance metrics
        metrics = telemetry_api.get_performance_metrics()

        assert "total_records" in metrics
        assert "average_processing_time" in metrics
        assert "storage_size" in metrics
        assert metrics["total_records"] >= 100


if __name__ == "__main__":
    pytest.main([__file__])
