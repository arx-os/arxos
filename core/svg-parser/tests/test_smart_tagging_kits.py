"""
Smart Tagging Kits Test Suite

Comprehensive tests for QR + BLE tag assignment, scanning, resolution,
and management with offline capabilities.
"""

import unittest
import json
import tempfile
import os
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
import sqlite3
import shutil

# Add parent directory to path for imports
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.smart_tagging_kits import (
    SmartTaggingService, TagType, TagStatus, ScanResult,
    TagData, ObjectMapping, ScanHistory, AssignmentHistory
)
from routers.smart_tagging_kits import router
from cli_commands.smart_tagging_cli import SmartTaggingCLI
from fastapi.testclient import TestClient
from fastapi import FastAPI


class TestSmartTaggingService(unittest.TestCase):
    """Test cases for Smart Tagging Service."""
    
    def setUp(self):
        """Set up test environment."""
        # Create temporary database
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        
        # Initialize service with temporary database
        self.service = SmartTaggingService(self.temp_db.name)
        
        # Test data
        self.test_object_id = "test_object_123"
        self.test_user_id = "test_user_1"
        self.test_device_id = "test_device_1"
        self.test_tag_data = "TEST_QR_123456"
        self.test_tag_type = TagType.QR
    
    def tearDown(self):
        """Clean up test environment."""
        # Remove temporary database
        if os.path.exists(self.temp_db.name):
            os.unlink(self.temp_db.name)
    
    def test_service_initialization(self):
        """Test service initialization."""
        self.assertIsNotNone(self.service)
        self.assertEqual(len(self.service.tag_database), 0)
        self.assertEqual(len(self.service.object_mappings), 0)
        self.assertEqual(len(self.service.scan_history), 0)
        self.assertEqual(len(self.service.assignment_history), 0)
    
    def test_tag_validation_valid_qr(self):
        """Test valid QR tag validation."""
        result = self.service.validate_tag("QR123456", TagType.QR)
        self.assertTrue(result["valid"])
        self.assertIn("message", result)
    
    def test_tag_validation_invalid_qr(self):
        """Test invalid QR tag validation."""
        result = self.service.validate_tag("", TagType.QR)
        self.assertFalse(result["valid"])
        self.assertIn("error", result)
    
    def test_tag_validation_valid_ble(self):
        """Test valid BLE tag validation."""
        result = self.service.validate_tag("1234567890abcdef", TagType.BLE)
        self.assertTrue(result["valid"])
    
    def test_tag_validation_invalid_ble(self):
        """Test invalid BLE tag validation."""
        result = self.service.validate_tag("invalid", TagType.BLE)
        self.assertFalse(result["valid"])
        self.assertIn("error", result)
    
    def test_tag_validation_valid_hybrid(self):
        """Test valid hybrid tag validation."""
        result = self.service.validate_tag("QR123:1234567890abcdef", TagType.HYBRID)
        self.assertTrue(result["valid"])
    
    def test_tag_validation_invalid_hybrid(self):
        """Test invalid hybrid tag validation."""
        result = self.service.validate_tag("invalid", TagType.HYBRID)
        self.assertFalse(result["valid"])
        self.assertIn("error", result)
    
    def test_tag_assignment_success(self):
        """Test successful tag assignment."""
        result = self.service.assign_tag(
            object_id=self.test_object_id,
            tag_type=self.test_tag_type,
            tag_data=self.test_tag_data,
            user_id=self.test_user_id,
            device_id=self.test_device_id
        )
        
        self.assertTrue(result["success"])
        self.assertIn("tag_id", result)
        self.assertEqual(result["object_id"], self.test_object_id)
        self.assertEqual(result["tag_type"], self.test_tag_type.value)
    
    def test_tag_assignment_duplicate(self):
        """Test tag assignment with duplicate tag data."""
        # First assignment
        result1 = self.service.assign_tag(
            object_id=self.test_object_id,
            tag_type=self.test_tag_type,
            tag_data=self.test_tag_data,
            user_id=self.test_user_id,
            device_id=self.test_device_id
        )
        self.assertTrue(result1["success"])
        
        # Second assignment with same tag data
        result2 = self.service.assign_tag(
            object_id="another_object",
            tag_type=self.test_tag_type,
            tag_data=self.test_tag_data,
            user_id=self.test_user_id,
            device_id=self.test_device_id
        )
        self.assertFalse(result2["success"])
        self.assertIn("already assigned", result2["error"])
    
    def test_tag_scanning_success(self):
        """Test successful tag scanning."""
        # First assign a tag
        assign_result = self.service.assign_tag(
            object_id=self.test_object_id,
            tag_type=self.test_tag_type,
            tag_data=self.test_tag_data,
            user_id=self.test_user_id,
            device_id=self.test_device_id
        )
        
        # Then scan it
        scan_result = self.service.scan_tag(
            tag_data=self.test_tag_data,
            tag_type=self.test_tag_type,
            user_id=self.test_user_id,
            device_id=self.test_device_id
        )
        
        self.assertTrue(scan_result["success"])
        self.assertEqual(scan_result["result"], ScanResult.SUCCESS.value)
        self.assertEqual(scan_result["object_id"], self.test_object_id)
    
    def test_tag_scanning_not_found(self):
        """Test tag scanning with non-existent tag."""
        scan_result = self.service.scan_tag(
            tag_data="NON_EXISTENT_TAG",
            tag_type=self.test_tag_type,
            user_id=self.test_user_id,
            device_id=self.test_device_id
        )
        
        self.assertFalse(scan_result["success"])
        self.assertEqual(scan_result["result"], ScanResult.NOT_FOUND.value)
    
    def test_offline_resolution_success(self):
        """Test successful offline tag resolution."""
        # First assign a tag
        assign_result = self.service.assign_tag(
            object_id=self.test_object_id,
            tag_type=self.test_tag_type,
            tag_data=self.test_tag_data,
            user_id=self.test_user_id,
            device_id=self.test_device_id
        )
        
        # Then resolve it offline
        resolve_result = self.service.resolve_object(self.test_tag_data, self.test_tag_type)
        
        self.assertTrue(resolve_result["success"])
        self.assertTrue(resolve_result["found"])
        self.assertEqual(resolve_result["object_id"], self.test_object_id)
    
    def test_offline_resolution_not_found(self):
        """Test offline resolution with non-existent tag."""
        resolve_result = self.service.resolve_object("NON_EXISTENT_TAG", self.test_tag_type)
        
        self.assertFalse(resolve_result["success"])
        self.assertFalse(resolve_result["found"])
    
    def test_tag_history(self):
        """Test tag history retrieval."""
        # Assign a tag
        assign_result = self.service.assign_tag(
            object_id=self.test_object_id,
            tag_type=self.test_tag_type,
            tag_data=self.test_tag_data,
            user_id=self.test_user_id,
            device_id=self.test_device_id
        )
        
        # Scan the tag
        self.service.scan_tag(
            tag_data=self.test_tag_data,
            tag_type=self.test_tag_type,
            user_id=self.test_user_id,
            device_id=self.test_device_id
        )
        
        # Get history
        history = self.service.get_tag_history(self.test_tag_data)
        
        self.assertIsInstance(history, list)
        self.assertGreater(len(history), 0)
        
        # Check for creation event
        creation_events = [h for h in history if h["event_type"] == "created"]
        self.assertGreater(len(creation_events), 0)
        
        # Check for assignment event
        assignment_events = [h for h in history if h["event_type"] == "assign"]
        self.assertGreater(len(assignment_events), 0)
        
        # Check for scan event
        scan_events = [h for h in history if h["event_type"] == "scanned"]
        self.assertGreater(len(scan_events), 0)
    
    def test_tag_mapping_update(self):
        """Test tag mapping update."""
        # First assign a tag
        assign_result = self.service.assign_tag(
            object_id=self.test_object_id,
            tag_type=self.test_tag_type,
            tag_data=self.test_tag_data,
            user_id=self.test_user_id,
            device_id=self.test_device_id
        )
        
        # Update to new object
        new_object_id = "new_object_456"
        success = self.service.update_tag_mapping(
            tag_data=self.test_tag_data,
            object_id=new_object_id,
            user_id=self.test_user_id,
            device_id=self.test_device_id
        )
        
        self.assertTrue(success)
        
        # Verify the update
        resolve_result = self.service.resolve_object(self.test_tag_data, self.test_tag_type)
        self.assertEqual(resolve_result["object_id"], new_object_id)
    
    def test_tag_assignment_removal(self):
        """Test tag assignment removal."""
        # First assign a tag
        assign_result = self.service.assign_tag(
            object_id=self.test_object_id,
            tag_type=self.test_tag_type,
            tag_data=self.test_tag_data,
            user_id=self.test_user_id,
            device_id=self.test_device_id
        )
        
        # Remove assignment
        success = self.service.remove_tag_assignment(
            tag_data=self.test_tag_data,
            user_id=self.test_user_id,
            device_id=self.test_device_id
        )
        
        self.assertTrue(success)
        
        # Verify the removal
        resolve_result = self.service.resolve_object(self.test_tag_data, self.test_tag_type)
        self.assertFalse(resolve_result["found"])
    
    def test_get_object_tags(self):
        """Test getting all tags for an object."""
        # Assign multiple tags to the same object
        tag_data_1 = "TAG_1"
        tag_data_2 = "TAG_2"
        
        self.service.assign_tag(
            object_id=self.test_object_id,
            tag_type=self.test_tag_type,
            tag_data=tag_data_1,
            user_id=self.test_user_id,
            device_id=self.test_device_id
        )
        
        self.service.assign_tag(
            object_id=self.test_object_id,
            tag_type=self.test_tag_type,
            tag_data=tag_data_2,
            user_id=self.test_user_id,
            device_id=self.test_device_id
        )
        
        # Get object tags
        tags = self.service.get_object_tags(self.test_object_id)
        
        self.assertEqual(len(tags), 2)
        tag_data_list = [tag["tag_data"] for tag in tags]
        self.assertIn(tag_data_1, tag_data_list)
        self.assertIn(tag_data_2, tag_data_list)
    
    def test_bulk_tag_assignment(self):
        """Test bulk tag assignment."""
        assignments = [
            {
                "object_id": "obj_1",
                "tag_type": "qr",
                "tag_data": "QR_1",
                "user_id": self.test_user_id,
                "device_id": self.test_device_id
            },
            {
                "object_id": "obj_2",
                "tag_type": "ble",
                "tag_data": "1234567890abcdef",
                "user_id": self.test_user_id,
                "device_id": self.test_device_id
            }
        ]
        
        result = self.service.bulk_assign_tags(assignments)
        
        self.assertEqual(result["total"], 2)
        self.assertEqual(result["successful"], 2)
        self.assertEqual(result["failed"], 0)
    
    def test_data_export_import(self):
        """Test data export and import."""
        # Create some test data
        self.service.assign_tag(
            object_id=self.test_object_id,
            tag_type=self.test_tag_type,
            tag_data=self.test_tag_data,
            user_id=self.test_user_id,
            device_id=self.test_device_id
        )
        
        # Export data
        exported_json = self.service.export_tag_data("json")
        self.assertIsInstance(exported_json, str)
        self.assertGreater(len(exported_json), 0)
        
        # Create new service for import test
        temp_db_2 = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        temp_db_2.close()
        
        try:
            new_service = SmartTaggingService(temp_db_2.name)
            
            # Import data
            import_result = new_service.import_tag_data(exported_json, "json")
            
            self.assertEqual(import_result["total"], 1)
            self.assertEqual(import_result["successful"], 1)
            self.assertEqual(import_result["failed"], 0)
            
            # Verify imported data
            resolve_result = new_service.resolve_object(self.test_tag_data, self.test_tag_type)
            self.assertTrue(resolve_result["found"])
            self.assertEqual(resolve_result["object_id"], self.test_object_id)
            
        finally:
            if os.path.exists(temp_db_2.name):
                os.unlink(temp_db_2.name)
    
    def test_analytics_generation(self):
        """Test analytics generation."""
        # Create some test data
        self.service.assign_tag(
            object_id=self.test_object_id,
            tag_type=self.test_tag_type,
            tag_data=self.test_tag_data,
            user_id=self.test_user_id,
            device_id=self.test_device_id
        )
        
        self.service.scan_tag(
            tag_data=self.test_tag_data,
            tag_type=self.test_tag_type,
            user_id=self.test_user_id,
            device_id=self.test_device_id
        )
        
        # Generate analytics
        analytics = self.service.get_analytics(period_days=30)
        
        self.assertIsInstance(analytics, dict)
        self.assertIn("total_tags", analytics)
        self.assertIn("assigned_tags", analytics)
        self.assertIn("total_scans", analytics)
        self.assertIn("successful_scans", analytics)
    
    def test_performance_metrics(self):
        """Test performance metrics retrieval."""
        metrics = self.service.get_performance_metrics()
        
        self.assertIsInstance(metrics, dict)
        self.assertIn("total_tags", metrics)
        self.assertIn("assigned_tags", metrics)
        self.assertIn("assignment_rate", metrics)
        self.assertIn("total_scans", metrics)
        self.assertIn("avg_response_time", metrics)
    
    def test_cache_functionality(self):
        """Test cache functionality."""
        # Assign a tag
        self.service.assign_tag(
            object_id=self.test_object_id,
            tag_type=self.test_tag_type,
            tag_data=self.test_tag_data,
            user_id=self.test_user_id,
            device_id=self.test_device_id
        )
        
        # First resolution (should populate cache)
        result1 = self.service.resolve_object(self.test_tag_data, self.test_tag_type)
        
        # Second resolution (should use cache)
        result2 = self.service.resolve_object(self.test_tag_data, self.test_tag_type)
        
        # Results should be identical
        self.assertEqual(result1, result2)
        
        # Clear cache
        self.service._clear_cache()
        self.assertEqual(len(self.service._cache), 0)


class TestSmartTaggingAPI(unittest.TestCase):
    """Test cases for Smart Tagging API endpoints."""
    
    def setUp(self):
        """Set up test environment."""
        self.app = FastAPI()
        self.app.include_router(router)
        self.client = TestClient(self.app)
    
    def test_assign_tag_endpoint(self):
        """Test tag assignment endpoint."""
        response = self.client.post("/smart-tagging/tags/assign", json={
            "object_id": "test_object",
            "tag_type": "qr",
            "tag_data": "TEST_QR_123",
            "user_id": "test_user",
            "device_id": "test_device"
        })
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "success")
        self.assertTrue(data["data"]["success"])
    
    def test_scan_tag_endpoint(self):
        """Test tag scanning endpoint."""
        # First assign a tag
        self.client.post("/smart-tagging/tags/assign", json={
            "object_id": "test_object",
            "tag_type": "qr",
            "tag_data": "TEST_QR_123",
            "user_id": "test_user",
            "device_id": "test_device"
        })
        
        # Then scan it
        response = self.client.get("/smart-tagging/tags/scan/TEST_QR_123", params={
            "tag_type": "qr",
            "user_id": "test_user",
            "device_id": "test_device"
        })
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "success")
        self.assertTrue(data["data"]["success"])
    
    def test_resolve_tag_endpoint(self):
        """Test tag resolution endpoint."""
        # First assign a tag
        self.client.post("/smart-tagging/tags/assign", json={
            "object_id": "test_object",
            "tag_type": "qr",
            "tag_data": "TEST_QR_123",
            "user_id": "test_user",
            "device_id": "test_device"
        })
        
        # Then resolve it
        response = self.client.get("/smart-tagging/tags/resolve/TEST_QR_123", params={
            "tag_type": "qr"
        })
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "success")
        self.assertTrue(data["data"]["success"])
    
    def test_validate_tag_endpoint(self):
        """Test tag validation endpoint."""
        response = self.client.post("/smart-tagging/tags/validate", json={
            "tag_data": "TEST_QR_123",
            "tag_type": "qr"
        })
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "success")
        self.assertTrue(data["data"]["valid"])
    
    def test_get_tag_history_endpoint(self):
        """Test tag history endpoint."""
        # First assign a tag
        self.client.post("/smart-tagging/tags/assign", json={
            "object_id": "test_object",
            "tag_type": "qr",
            "tag_data": "TEST_QR_123",
            "user_id": "test_user",
            "device_id": "test_device"
        })
        
        # Then get history
        response = self.client.get("/smart-tagging/tags/history/TEST_QR_123")
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "success")
        self.assertIn("history", data["data"])
    
    def test_update_tag_mapping_endpoint(self):
        """Test tag mapping update endpoint."""
        # First assign a tag
        self.client.post("/smart-tagging/tags/assign", json={
            "object_id": "test_object",
            "tag_type": "qr",
            "tag_data": "TEST_QR_123",
            "user_id": "test_user",
            "device_id": "test_device"
        })
        
        # Then update it
        response = self.client.put("/smart-tagging/tags/update", json={
            "tag_data": "TEST_QR_123",
            "object_id": "new_object",
            "user_id": "test_user",
            "device_id": "test_device"
        })
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "success")
    
    def test_remove_tag_assignment_endpoint(self):
        """Test tag assignment removal endpoint."""
        # First assign a tag
        self.client.post("/smart-tagging/tags/assign", json={
            "object_id": "test_object",
            "tag_type": "qr",
            "tag_data": "TEST_QR_123",
            "user_id": "test_user",
            "device_id": "test_device"
        })
        
        # Then remove it
        response = self.client.delete("/smart-tagging/tags/remove", json={
            "tag_data": "TEST_QR_123",
            "user_id": "test_user",
            "device_id": "test_device"
        })
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "success")
    
    def test_get_object_tags_endpoint(self):
        """Test get object tags endpoint."""
        # First assign a tag
        self.client.post("/smart-tagging/tags/assign", json={
            "object_id": "test_object",
            "tag_type": "qr",
            "tag_data": "TEST_QR_123",
            "user_id": "test_user",
            "device_id": "test_device"
        })
        
        # Then get object tags
        response = self.client.get("/smart-tagging/tags/object/test_object")
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "success")
        self.assertIn("tags", data["data"])
    
    def test_bulk_assign_endpoint(self):
        """Test bulk tag assignment endpoint."""
        assignments = [
            {
                "object_id": "obj_1",
                "tag_type": "qr",
                "tag_data": "QR_1",
                "user_id": "test_user",
                "device_id": "test_device"
            },
            {
                "object_id": "obj_2",
                "tag_type": "ble",
                "tag_data": "1234567890abcdef",
                "user_id": "test_user",
                "device_id": "test_device"
            }
        ]
        
        response = self.client.post("/smart-tagging/tags/bulk-assign", json=assignments)
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["data"]["total"], 2)
    
    def test_export_data_endpoint(self):
        """Test data export endpoint."""
        # First assign a tag
        self.client.post("/smart-tagging/tags/assign", json={
            "object_id": "test_object",
            "tag_type": "qr",
            "tag_data": "TEST_QR_123",
            "user_id": "test_user",
            "device_id": "test_device"
        })
        
        # Then export data
        response = self.client.get("/smart-tagging/tags/export", params={"format": "json"})
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "success")
        self.assertIn("data", data["data"])
    
    def test_import_data_endpoint(self):
        """Test data import endpoint."""
        # Create test data
        test_data = {
            "tags": [
                {
                    "tag_id": "test_tag_1",
                    "tag_type": "qr",
                    "tag_data": "TEST_QR_123",
                    "object_id": "test_object",
                    "status": "assigned",
                    "created_at": datetime.now().isoformat(),
                    "assigned_at": datetime.now().isoformat(),
                    "last_scan_at": None,
                    "scan_count": 0,
                    "metadata": {},
                    "device_id": "test_device",
                    "user_id": "test_user"
                }
            ],
            "mappings": [],
            "export_timestamp": datetime.now().isoformat(),
            "total_tags": 1,
            "total_mappings": 0
        }
        
        response = self.client.post("/smart-tagging/tags/import", json={
            "data": json.dumps(test_data),
            "format": "json"
        })
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["data"]["successful"], 1)
    
    def test_analytics_endpoint(self):
        """Test analytics endpoint."""
        response = self.client.get("/smart-tagging/tags/analytics", params={"period_days": 30})
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "success")
        self.assertIn("total_tags", data["data"])
    
    def test_status_endpoint(self):
        """Test status endpoint."""
        response = self.client.get("/smart-tagging/tags/status")
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "success")
        self.assertIn("service_status", data["data"])
    
    def test_health_endpoint(self):
        """Test health endpoint."""
        response = self.client.get("/smart-tagging/health")
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("healthy", data["data"])
    
    def test_diagnostics_endpoint(self):
        """Test diagnostics endpoint."""
        response = self.client.get("/smart-tagging/diagnostics")
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "success")
        self.assertIn("service_status", data["data"])
    
    def test_generate_tag_endpoint(self):
        """Test tag generation endpoint."""
        response = self.client.post("/smart-tagging/tags/generate", json={
            "tag_type": "qr",
            "prefix": "TEST"
        })
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "success")
        self.assertIn("tag_data", data["data"])
    
    def test_cleanup_tags_endpoint(self):
        """Test tag cleanup endpoint."""
        response = self.client.post("/smart-tagging/tags/cleanup", json={
            "days_old": 90,
            "dry_run": True
        })
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "success")
        self.assertTrue(data["data"]["dry_run"])


class TestSmartTaggingCLI(unittest.TestCase):
    """Test cases for Smart Tagging CLI."""
    
    def setUp(self):
        """Set up test environment."""
        self.cli = SmartTaggingCLI()
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir)
    
    def test_cli_initialization(self):
        """Test CLI initialization."""
        self.assertIsNotNone(self.cli)
        self.assertIsNotNone(self.cli.service)
    
    def test_tag_validation_cli(self):
        """Test tag validation via CLI."""
        # Create test arguments
        args = Mock()
        args.tag_data = "TEST_QR_123"
        args.tag_type = "qr"
        args.output = None
        
        # Mock sys.exit to prevent actual exit
        with patch('sys.exit'):
            self.cli.validate_tag(args)
    
    def test_tag_assignment_cli(self):
        """Test tag assignment via CLI."""
        # Create test arguments
        args = Mock()
        args.object_id = "test_object"
        args.tag_type = "qr"
        args.tag_data = "TEST_QR_123"
        args.user_id = "test_user"
        args.device_id = "test_device"
        args.metadata = None
        args.output = None
        
        # Mock sys.exit to prevent actual exit
        with patch('sys.exit'):
            self.cli.assign_tag(args)
    
    def test_tag_scanning_cli(self):
        """Test tag scanning via CLI."""
        # First assign a tag
        assign_args = Mock()
        assign_args.object_id = "test_object"
        assign_args.tag_type = "qr"
        assign_args.tag_data = "TEST_QR_123"
        assign_args.user_id = "test_user"
        assign_args.device_id = "test_device"
        assign_args.metadata = None
        assign_args.output = None
        
        with patch('sys.exit'):
            self.cli.assign_tag(assign_args)
        
        # Then scan it
        scan_args = Mock()
        scan_args.tag_data = "TEST_QR_123"
        scan_args.tag_type = "qr"
        scan_args.user_id = "test_user"
        scan_args.device_id = "test_device"
        scan_args.location = None
        scan_args.output = None
        
        with patch('sys.exit'):
            self.cli.scan_tag(scan_args)
    
    def test_bulk_assignment_cli(self):
        """Test bulk assignment via CLI."""
        # Create test assignments file
        assignments_file = os.path.join(self.temp_dir, "assignments.json")
        assignments = [
            {
                "object_id": "obj_1",
                "tag_type": "qr",
                "tag_data": "QR_1",
                "user_id": "test_user",
                "device_id": "test_device"
            },
            {
                "object_id": "obj_2",
                "tag_type": "ble",
                "tag_data": "1234567890abcdef",
                "user_id": "test_user",
                "device_id": "test_device"
            }
        ]
        
        with open(assignments_file, 'w') as f:
            json.dump(assignments, f)
        
        # Test bulk assignment
        args = Mock()
        args.file = assignments_file
        args.output = None
        
        with patch('sys.exit'):
            self.cli.bulk_assign(args)
    
    def test_data_export_cli(self):
        """Test data export via CLI."""
        # First assign a tag
        assign_args = Mock()
        assign_args.object_id = "test_object"
        assign_args.tag_type = "qr"
        assign_args.tag_data = "TEST_QR_123"
        assign_args.user_id = "test_user"
        assign_args.device_id = "test_device"
        assign_args.metadata = None
        assign_args.output = None
        
        with patch('sys.exit'):
            self.cli.assign_tag(assign_args)
        
        # Then export data
        export_args = Mock()
        export_args.format = "json"
        export_args.output = None
        
        with patch('sys.exit'):
            self.cli.export_data(export_args)
    
    def test_analytics_cli(self):
        """Test analytics via CLI."""
        args = Mock()
        args.period = 30
        args.output = None
        
        with patch('sys.exit'):
            self.cli.get_analytics(args)
    
    def test_status_cli(self):
        """Test status via CLI."""
        args = Mock()
        args.detailed = False
        args.output = None
        
        with patch('sys.exit'):
            self.cli.get_status(args)
    
    def test_health_cli(self):
        """Test health check via CLI."""
        args = Mock()
        args.detailed = False
        args.output = None
        
        with patch('sys.exit'):
            self.cli.health_check(args)


class TestSmartTaggingPerformance(unittest.TestCase):
    """Performance tests for Smart Tagging Kits."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.service = SmartTaggingService(self.temp_db.name)
    
    def tearDown(self):
        """Clean up test environment."""
        if os.path.exists(self.temp_db.name):
            os.unlink(self.temp_db.name)
    
    def test_bulk_assignment_performance(self):
        """Test bulk assignment performance."""
        # Create 100 assignments
        assignments = []
        for i in range(100):
            assignments.append({
                "object_id": f"obj_{i}",
                "tag_type": "qr",
                "tag_data": f"QR_{i}_{i*1000}",
                "user_id": "test_user",
                "device_id": "test_device"
            })
        
        start_time = time.time()
        result = self.service.bulk_assign_tags(assignments)
        end_time = time.time()
        
        self.assertEqual(result["total"], 100)
        self.assertEqual(result["successful"], 100)
        self.assertEqual(result["failed"], 0)
        
        # Performance should be under 5 seconds
        self.assertLess(end_time - start_time, 5.0)
    
    def test_scan_performance(self):
        """Test scan performance."""
        # Create 50 tags
        for i in range(50):
            self.service.assign_tag(
                object_id=f"obj_{i}",
                tag_type=TagType.QR,
                tag_data=f"QR_{i}_{i*1000}",
                user_id="test_user",
                device_id="test_device"
            )
        
        # Test scan performance
        start_time = time.time()
        for i in range(50):
            result = self.service.scan_tag(
                tag_data=f"QR_{i}_{i*1000}",
                tag_type=TagType.QR,
                user_id="test_user",
                device_id="test_device"
            )
            self.assertTrue(result["success"])
        end_time = time.time()
        
        # Average scan time should be under 0.1 seconds
        avg_scan_time = (end_time - start_time) / 50
        self.assertLess(avg_scan_time, 0.1)
    
    def test_resolution_performance(self):
        """Test resolution performance."""
        # Create 100 tags
        for i in range(100):
            self.service.assign_tag(
                object_id=f"obj_{i}",
                tag_type=TagType.QR,
                tag_data=f"QR_{i}_{i*1000}",
                user_id="test_user",
                device_id="test_device"
            )
        
        # Test resolution performance
        start_time = time.time()
        for i in range(100):
            result = self.service.resolve_object(f"QR_{i}_{i*1000}", TagType.QR)
            self.assertTrue(result["success"])
        end_time = time.time()
        
        # Average resolution time should be under 0.01 seconds
        avg_resolution_time = (end_time - start_time) / 100
        self.assertLess(avg_resolution_time, 0.01)
    
    def test_cache_performance(self):
        """Test cache performance."""
        # Assign a tag
        self.service.assign_tag(
            object_id="test_object",
            tag_type=TagType.QR,
            tag_data="TEST_QR_123",
            user_id="test_user",
            device_id="test_device"
        )
        
        # First resolution (populate cache)
        start_time = time.time()
        result1 = self.service.resolve_object("TEST_QR_123", TagType.QR)
        first_time = time.time() - start_time
        
        # Second resolution (use cache)
        start_time = time.time()
        result2 = self.service.resolve_object("TEST_QR_123", TagType.QR)
        second_time = time.time() - start_time
        
        # Cached resolution should be faster
        self.assertLess(second_time, first_time)
        self.assertEqual(result1, result2)


def run_performance_tests():
    """Run performance tests and generate report."""
    print("🚀 Running Smart Tagging Kits Performance Tests")
    print("=" * 50)
    
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TestSmartTaggingPerformance)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Generate performance report
    print("\n📊 Performance Test Summary")
    print("=" * 30)
    print(f"Tests Run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.failures:
        print("\n❌ Failures:")
        for test, traceback in result.failures:
            print(f"  - {test}: {traceback}")
    
    if result.errors:
        print("\n❌ Errors:")
        for test, traceback in result.errors:
            print(f"  - {test}: {traceback}")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    # Run all tests
    unittest.main(verbosity=2) 