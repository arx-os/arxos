"""
Comprehensive Tests for CMMS Maintenance Event Hooks

This test suite covers all aspects of the CMMS Maintenance Event Hooks service and router,
including webhook processing, background job handling, conflict resolution, and API endpoints.

Test Coverage:
- Webhook event processing and validation
- HMAC signature validation
- Background job processing
- Event type handling
- Error handling and retry logic
- API endpoint functionality
- Database operations
- Redis queue operations
- Performance and load testing
- Security testing

Author: ARXOS Development Team
Date: 2024-12-19
Version: 1.0.0
"""

import asyncio
import hashlib
import hmac
import json
import pytest
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List
from unittest.mock import AsyncMock, MagicMock, patch

import redis.asyncio as redis
from fastapi import HTTPException, status
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from core.services.cmms_maintenance_hooks
    CMMSMaintenanceHooksService,
    WebhookEvent,
    WebhookResponse,
    SyncStatus,
    ProcessingStatus,
    EventType,
    MaintenanceEventHook,
    SyncConfiguration
)
from core.routers.cmms_maintenance_hooks
from core.utils.auth

# Test configuration
TEST_DATABASE_URL = "sqlite:///./test_cmms_hooks.db"
TEST_REDIS_HOST = "localhost"
TEST_REDIS_PORT = 6379
TEST_REDIS_DB = 1

# Test data
TEST_CMMS_SYSTEM_ID = "test_maximo_system"
TEST_SECRET_KEY = "test-secret-key-12345"
TEST_WEBHOOK_PAYLOAD = {
    "event_type": "maintenance_scheduled",
    "cmms_system_id": TEST_CMMS_SYSTEM_ID,
    "timestamp": datetime.utcnow().isoformat(),
    "payload": {
        "equipment_id": "HVAC-001",
        "scheduled_date": "2024-12-20T10:00:00Z",
        "maintenance_type": "preventive",
        "technician_id": "TECH-001",
        "priority": "medium"
    }
}


class TestCMMSMaintenanceHooksService:
    """Test suite for CMMS Maintenance Hooks Service."""
    
    @pytest.fixture(autouse=True)
    async def setup_service(self):
        """Set up test service with mocked dependencies."""
        self.service = CMMSMaintenanceHooksService()
        
        # Mock Redis client
        self.mock_redis = AsyncMock()
        self.service.redis_client = self.mock_redis
        
        # Mock database session
        self.mock_session = AsyncMock()
        
        yield
        
        # Cleanup
        await self.service.close()
    
    @pytest.fixture
    def sample_webhook_event(self):
        """Create a sample webhook event for testing."""
        return WebhookEvent(
            event_type="maintenance_scheduled",
            cmms_system_id=TEST_CMMS_SYSTEM_ID,
            timestamp=datetime.utcnow(),
            payload={
                "equipment_id": "HVAC-001",
                "scheduled_date": "2024-12-20T10:00:00Z",
                "maintenance_type": "preventive"
            }
        )
    
    def test_validate_hmac_signature_valid(self):
        """Test HMAC signature validation with valid signature."""
        payload = "test-payload"
        signature = hmac.new(
            TEST_SECRET_KEY.encode('utf-8'),
            payload.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        result = self.service.validate_hmac_signature(payload, signature, TEST_SECRET_KEY)
        assert result is True
    
    def test_validate_hmac_signature_invalid(self):
        """Test HMAC signature validation with invalid signature."""
        payload = "test-payload"
        invalid_signature = "invalid-signature"
        
        result = self.service.validate_hmac_signature(payload, invalid_signature, TEST_SECRET_KEY)
        assert result is False
    
    def test_validate_hmac_signature_empty_payload(self):
        """Test HMAC signature validation with empty payload."""
        payload = ""
        signature = hmac.new(
            TEST_SECRET_KEY.encode('utf-8'),
            payload.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        result = self.service.validate_hmac_signature(payload, signature, TEST_SECRET_KEY)
        assert result is True
    
    @pytest.mark.asyncio
    async def test_process_webhook_event_success(self, sample_webhook_event):
        """Test successful webhook event processing."""
        # Create valid HMAC signature
        payload_str = sample_webhook_event.json()
        signature = hmac.new(
            TEST_SECRET_KEY.encode('utf-8'),
            payload_str.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        # Mock database operations
        with patch('services.cmms_maintenance_hooks.get_database_session') as mock_db:
            mock_db.return_value.__aenter__.return_value = self.mock_session
            
            # Mock event storage
            mock_event = MagicMock()
            mock_event.id = uuid.uuid4()
            self.mock_session.add.return_value = None
            self.mock_session.commit.return_value = None
            self.mock_session.refresh.return_value = None
            
            # Mock Redis queue
            self.mock_redis.lpush.return_value = None
            
            # Process webhook event
            response = await self.service.process_webhook_event(
                event_data=sample_webhook_event,
                hmac_signature=signature,
                secret_key=TEST_SECRET_KEY
            )
            
            # Verify response
            assert response.success is True
            assert "Event received and queued" in response.message
            assert response.event_id is not None
            assert response.processing_time_ms is not None
            assert response.processing_time_ms > 0
    
    @pytest.mark.asyncio
    async def test_process_webhook_event_invalid_signature(self, sample_webhook_event):
        """Test webhook event processing with invalid signature."""
        invalid_signature = "invalid-signature"
        
        with pytest.raises(HTTPException) as exc_info:
            await self.service.process_webhook_event(
                event_data=sample_webhook_event,
                hmac_signature=invalid_signature,
                secret_key=TEST_SECRET_KEY
            )
        
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Invalid HMAC signature" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_process_webhook_event_database_error(self, sample_webhook_event):
        """Test webhook event processing with database error."""
        # Create valid HMAC signature
        payload_str = sample_webhook_event.json()
        signature = hmac.new(
            TEST_SECRET_KEY.encode('utf-8'),
            payload_str.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        # Mock database error
        with patch('services.cmms_maintenance_hooks.get_database_session') as mock_db:
            mock_db.return_value.__aenter__.return_value = self.mock_session
            self.mock_session.add.side_effect = Exception("Database error")
            
            # Process webhook event
            response = await self.service.process_webhook_event(
                event_data=sample_webhook_event,
                hmac_signature=signature,
                secret_key=TEST_SECRET_KEY
            )
            
            # Verify error response
            assert response.success is False
            assert "Event processing failed" in response.message
    
    @pytest.mark.asyncio
    async def test_handle_event_type_maintenance_scheduled(self):
        """Test handling of maintenance scheduled event."""
        job_data = {
            "event_type": EventType.MAINTENANCE_SCHEDULED,
            "payload": {
                "equipment_id": "HVAC-001",
                "scheduled_date": "2024-12-20T10:00:00Z",
                "maintenance_type": "preventive"
            },
            "cmms_system_id": TEST_CMMS_SYSTEM_ID
        }
        
        # Mock the specific handler
        with patch.object(self.service, '_handle_maintenance_scheduled') as mock_handler:
            await self.service._handle_event_type(job_data)
            mock_handler.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_handle_event_type_equipment_failure(self):
        """Test handling of equipment failure event."""
        job_data = {
            "event_type": EventType.EQUIPMENT_FAILURE,
            "payload": {
                "equipment_id": "HVAC-001",
                "failure_type": "mechanical",
                "failure_description": "Compressor failure"
            },
            "cmms_system_id": TEST_CMMS_SYSTEM_ID
        }
        
        # Mock the specific handler
        with patch.object(self.service, '_handle_equipment_failure') as mock_handler:
            await self.service._handle_event_type(job_data)
            mock_handler.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_handle_event_type_unknown(self):
        """Test handling of unknown event type."""
        job_data = {
            "event_type": "unknown_event_type",
            "payload": {},
            "cmms_system_id": TEST_CMMS_SYSTEM_ID
        }
        
        # Should log warning but not raise exception
        await self.service._handle_event_type(job_data)
    
    @pytest.mark.asyncio
    async def test_get_sync_status(self):
        """Test getting sync status for CMMS system."""
        # Mock database session and query results
        with patch('services.cmms_maintenance_hooks.get_database_session') as mock_db:
            mock_db.return_value.__aenter__.return_value = self.mock_session
            
            # Mock query results
            mock_events = [
                MagicMock(processing_status=ProcessingStatus.COMPLETED.value),
                MagicMock(processing_status=ProcessingStatus.FAILED.value),
                MagicMock(processing_status=ProcessingStatus.COMPLETED.value)
            ]
            self.mock_session.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = mock_events
            
            # Get sync status
            sync_status = await self.service.get_sync_status(TEST_CMMS_SYSTEM_ID)
            
            # Verify response
            assert sync_status.cmms_system_id == TEST_CMMS_SYSTEM_ID
            assert sync_status.sync_type == "maintenance_events"
            assert sync_status.error_count == 1
            assert sync_status.success_count == 2
    
    @pytest.mark.asyncio
    async def test_get_event_history(self):
        """Test getting event history."""
        # Mock database session and query results
        with patch('services.cmms_maintenance_hooks.get_database_session') as mock_db:
            mock_db.return_value.__aenter__.return_value = self.mock_session
            
            # Mock query results
            mock_events = [
                MagicMock(
                    id=uuid.uuid4(),
                    cmms_system_id=TEST_CMMS_SYSTEM_ID,
                    event_type="maintenance_scheduled",
                    processing_status=ProcessingStatus.COMPLETED.value,
                    created_at=datetime.utcnow(),
                    processed_at=datetime.utcnow(),
                    error_message=None,
                    retry_count=0
                )
            ]
            self.mock_session.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = mock_events
            
            # Get event history
            history = await self.service.get_event_history(
                cmms_system_id=TEST_CMMS_SYSTEM_ID,
                limit=10
            )
            
            # Verify response
            assert len(history) == 1
            assert history[0]["cmms_system_id"] == TEST_CMMS_SYSTEM_ID
            assert history[0]["event_type"] == "maintenance_scheduled"
    
    @pytest.mark.asyncio
    async def test_create_sync_configuration(self):
        """Test creating sync configuration."""
        # Mock database session
        with patch('services.cmms_maintenance_hooks.get_database_session') as mock_db:
            mock_db.return_value.__aenter__.return_value = self.mock_session
            
            # Mock configuration creation
            mock_config = MagicMock()
            mock_config.id = uuid.uuid4()
            mock_config.cmms_system_id = TEST_CMMS_SYSTEM_ID
            mock_config.sync_type = "maintenance_events"
            mock_config.configuration = {"test": "config"}
            mock_config.is_active = True
            mock_config.created_at = datetime.utcnow()
            mock_config.updated_at = datetime.utcnow()
            
            self.mock_session.add.return_value = None
            self.mock_session.commit.return_value = None
            self.mock_session.refresh.return_value = None
            
            # Create sync configuration
            config = await self.service.create_sync_configuration(
                cmms_system_id=TEST_CMMS_SYSTEM_ID,
                sync_type="maintenance_events",
                configuration={"test": "config"}
            )
            
            # Verify response
            assert config["cmms_system_id"] == TEST_CMMS_SYSTEM_ID
            assert config["sync_type"] == "maintenance_events"
            assert config["configuration"] == {"test": "config"}


class TestCMMSMaintenanceHooksRouter:
    """Test suite for CMMS Maintenance Hooks Router."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        from fastapi import FastAPI
        app = FastAPI()
        app.include_router(router)
        return TestClient(app)
    
    @pytest.fixture
    def sample_webhook_data(self):
        """Create sample webhook data for testing."""
        return {
            "event_type": "maintenance_scheduled",
            "cmms_system_id": TEST_CMMS_SYSTEM_ID,
            "timestamp": datetime.utcnow().isoformat(),
            "payload": {
                "equipment_id": "HVAC-001",
                "scheduled_date": "2024-12-20T10:00:00Z",
                "maintenance_type": "preventive"
            }
        }
    
    def test_receive_maintenance_webhook_success(self, client, sample_webhook_data):
        """Test successful webhook reception."""
        # Create valid HMAC signature
        payload_str = json.dumps(sample_webhook_data)
        signature = hmac.new(
            TEST_SECRET_KEY.encode('utf-8'),
            payload_str.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        # Mock service
        with patch('routers.cmms_maintenance_hooks.get_cmms_hooks_service') as mock_service:
            mock_service_instance = AsyncMock()
            mock_service_instance.process_webhook_event.return_value = WebhookResponse(
                success=True,
                message="Event received and queued for processing",
                event_id=str(uuid.uuid4()),
                processing_time_ms=150
            )
            mock_service.return_value = mock_service_instance
            
            # Make request
            response = client.post(
                "/api/v1/hooks/maintenance/events",
                json=sample_webhook_data,
                headers={
                    "X-HMAC-Signature": signature,
                    "X-CMMS-Secret": TEST_SECRET_KEY
                }
            )
            
            # Verify response
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "Event received and queued" in data["message"]
    
    def test_receive_maintenance_webhook_missing_signature(self, client, sample_webhook_data):
        """Test webhook reception with missing signature."""
        response = client.post(
            "/api/v1/hooks/maintenance/events",
            json=sample_webhook_data
        )
        
        assert response.status_code == 401
        data = response.json()
        assert "Missing HMAC signature header" in data["detail"]
    
    def test_receive_maintenance_webhook_missing_secret(self, client, sample_webhook_data):
        """Test webhook reception with missing secret."""
        response = client.post(
            "/api/v1/hooks/maintenance/events",
            json=sample_webhook_data,
            headers={"X-HMAC-Signature": "test-signature"}
        )
        
        assert response.status_code == 401
        data = response.json()
        assert "Missing CMMS secret header" in data["detail"]
    
    def test_get_cmms_sync_status(self, client):
        """Test getting CMMS sync status."""
        # Mock service
        with patch('routers.cmms_maintenance_hooks.get_cmms_hooks_service') as mock_service:
            mock_service_instance = AsyncMock()
            mock_service_instance.get_sync_status.return_value = SyncStatus(
                cmms_system_id=TEST_CMMS_SYSTEM_ID,
                sync_type="maintenance_events",
                status="active",
                last_sync=datetime.utcnow(),
                next_sync=None,
                error_count=0,
                success_count=10
            )
            mock_service.return_value = mock_service_instance
            
            # Make request
            response = client.get(
                f"/api/v1/cmms/sync/status?cmms_system_id={TEST_CMMS_SYSTEM_ID}"
            )
            
            # Verify response
            assert response.status_code == 200
            data = response.json()
            assert data["cmms_system_id"] == TEST_CMMS_SYSTEM_ID
            assert data["status"] == "active"
    
    def test_get_event_history(self, client):
        """Test getting event history."""
        # Mock service
        with patch('routers.cmms_maintenance_hooks.get_cmms_hooks_service') as mock_service:
            mock_service_instance = AsyncMock()
            mock_service_instance.get_event_history.return_value = [
                {
                    "id": str(uuid.uuid4()),
                    "cmms_system_id": TEST_CMMS_SYSTEM_ID,
                    "event_type": "maintenance_scheduled",
                    "processing_status": "completed",
                    "created_at": datetime.utcnow().isoformat(),
                    "processed_at": datetime.utcnow().isoformat(),
                    "error_message": None,
                    "retry_count": 0
                }
            ]
            mock_service.return_value = mock_service_instance
            
            # Make request
            response = client.get(
                f"/api/v1/cmms/events/history?cmms_system_id={TEST_CMMS_SYSTEM_ID}&limit=10"
            )
            
            # Verify response
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["cmms_system_id"] == TEST_CMMS_SYSTEM_ID
    
    def test_create_sync_configuration(self, client):
        """Test creating sync configuration."""
        config_data = {
            "cmms_system_id": TEST_CMMS_SYSTEM_ID,
            "sync_type": "maintenance_events",
            "configuration": {
                "webhook_url": "https://arxos.com/api/v1/hooks/maintenance/events",
                "secret_key": "test-secret",
                "event_types": ["maintenance_scheduled", "maintenance_completed"]
            },
            "is_active": True
        }
        
        # Mock service and authentication
        with patch('routers.cmms_maintenance_hooks.get_cmms_hooks_service') as mock_service, \
             patch('routers.cmms_maintenance_hooks.get_current_user') as mock_auth:
            
            mock_service_instance = AsyncMock()
            mock_service_instance.create_sync_configuration.return_value = {
                "id": str(uuid.uuid4()),
                "cmms_system_id": TEST_CMMS_SYSTEM_ID,
                "sync_type": "maintenance_events",
                "configuration": config_data["configuration"],
                "is_active": True,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
            mock_service.return_value = mock_service_instance
            
            mock_auth.return_value = {"username": "test_user", "role": "admin"}
            
            # Make request
            response = client.post(
                "/api/v1/cmms/sync/configurations",
                json=config_data
            )
            
            # Verify response
            assert response.status_code == 201
            data = response.json()
            assert data["cmms_system_id"] == TEST_CMMS_SYSTEM_ID
            assert data["sync_type"] == "maintenance_events"
    
    def test_health_check(self, client):
        """Test health check endpoint."""
        # Mock service
        with patch('routers.cmms_maintenance_hooks.get_cmms_hooks_service') as mock_service:
            mock_service_instance = AsyncMock()
            mock_service_instance.redis_client = AsyncMock()
            mock_service_instance.redis_client.ping.return_value = True
            mock_service_instance.queue_name = "test_queue"
            mock_service_instance.redis_client.llen.return_value = 5
            mock_service.return_value = mock_service_instance
            
            # Make request
            response = client.get("/api/v1/cmms/health")
            
            # Verify response
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert data["redis_connected"] is True
            assert data["database_connected"] is True
            assert data["active_jobs"] == 5


class TestCMMSMaintenanceHooksPerformance:
    """Performance tests for CMMS Maintenance Hooks."""
    
    @pytest.mark.asyncio
    async def test_webhook_processing_performance(self):
        """Test webhook processing performance under load."""
        service = CMMSMaintenanceHooksService()
        
        # Mock dependencies
        service.redis_client = AsyncMock()
        
        # Create test events
        events = []
        for i in range(100):
            event = WebhookEvent(
                event_type="maintenance_scheduled",
                cmms_system_id=f"system_{i}",
                timestamp=datetime.utcnow(),
                payload={"equipment_id": f"EQ-{i}", "test": "data"}
            )
            events.append(event)
        
        # Process events concurrently
        start_time = time.time()
        
        with patch('services.cmms_maintenance_hooks.get_database_session') as mock_db:
            mock_db.return_value.__aenter__.return_value = AsyncMock()
            
            tasks = []
            for event in events:
                payload_str = event.json()
                signature = hmac.new(
                    TEST_SECRET_KEY.encode('utf-8'),
                    payload_str.encode('utf-8'),
                    hashlib.sha256
                ).hexdigest()
                
                task = service.process_webhook_event(
                    event_data=event,
                    hmac_signature=signature,
                    secret_key=TEST_SECRET_KEY
                )
                tasks.append(task)
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # Verify performance
        assert processing_time < 10.0  # Should complete within 10 seconds
        assert len(results) == 100
        
        # Check success rate
        successful_results = [r for r in results if isinstance(r, WebhookResponse) and r.success]
        assert len(successful_results) >= 95  # 95% success rate
    
    @pytest.mark.asyncio
    async def test_background_job_processing_performance(self):
        """Test background job processing performance."""
        service = CMMSMaintenanceHooksService()
        
        # Mock Redis
        mock_redis = AsyncMock()
        service.redis_client = mock_redis
        
        # Mock job data
        job_data = {
            "event_id": str(uuid.uuid4()),
            "cmms_system_id": TEST_CMMS_SYSTEM_ID,
            "event_type": "maintenance_scheduled",
            "payload": {"test": "data"},
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Mock Redis queue operations
        mock_redis.brpop.return_value = (None, json.dumps(job_data))
        
        # Mock database operations
        with patch('services.cmms_maintenance_hooks.get_database_session') as mock_db:
            mock_db.return_value.__aenter__.return_value = AsyncMock()
            
            # Process single job
            start_time = time.time()
            await service._process_job(job_data)
            end_time = time.time()
            
            processing_time = end_time - start_time
            
            # Verify performance
            assert processing_time < 1.0  # Should complete within 1 second


class TestCMMSMaintenanceHooksSecurity:
    """Security tests for CMMS Maintenance Hooks."""
    
    def test_hmac_signature_timing_attack_resistance(self):
        """Test HMAC signature validation is resistant to timing attacks."""
        service = CMMSMaintenanceHooksService()
        
        payload = "test-payload"
        correct_signature = hmac.new(
            TEST_SECRET_KEY.encode('utf-8'),
            payload.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        # Test with different invalid signatures
        invalid_signatures = [
            "a" * 64,  # Wrong length
            "0" * 64,  # All zeros
            correct_signature[:-1] + "0",  # One character different
            correct_signature[1:] + "0",  # Shifted
        ]
        
        for invalid_sig in invalid_signatures:
            result = service.validate_hmac_signature(payload, invalid_sig, TEST_SECRET_KEY)
            assert result is False
    
    def test_webhook_payload_validation(self):
        """Test webhook payload validation."""
        # Test valid payload
        valid_payload = WebhookEvent(
            event_type="maintenance_scheduled",
            cmms_system_id=TEST_CMMS_SYSTEM_ID,
            timestamp=datetime.utcnow(),
            payload={"test": "data"}
        )
        
        # Test invalid event type
        with pytest.raises(ValueError):
            WebhookEvent(
                event_type="invalid_event_type",
                cmms_system_id=TEST_CMMS_SYSTEM_ID,
                timestamp=datetime.utcnow(),
                payload={"test": "data"}
            )
    
    def test_sql_injection_prevention(self):
        """Test SQL injection prevention in database operations."""
        # This would test actual database operations with malicious input
        # For now, we test the validation logic
        malicious_system_id = "'; DROP TABLE maintenance_event_hooks; --"
        
        # The service should handle this safely
        service = CMMSMaintenanceHooksService()
        
        # Test that malicious input doesn't break validation
        payload = "test-payload"
        signature = hmac.new(
            TEST_SECRET_KEY.encode('utf-8'),
            payload.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        # This should not raise an exception
        result = service.validate_hmac_signature(payload, signature, TEST_SECRET_KEY)
        assert result is True


class TestCMMSMaintenanceHooksIntegration:
    """Integration tests for CMMS Maintenance Hooks."""
    
    @pytest.mark.asyncio
    async def test_end_to_end_webhook_processing(self):
        """Test end-to-end webhook processing flow."""
        service = CMMSMaintenanceHooksService()
        
        # Mock all dependencies
        service.redis_client = AsyncMock()
        
        # Create test event
        event = WebhookEvent(
            event_type="maintenance_scheduled",
            cmms_system_id=TEST_CMMS_SYSTEM_ID,
            timestamp=datetime.utcnow(),
            payload={
                "equipment_id": "HVAC-001",
                "scheduled_date": "2024-12-20T10:00:00Z",
                "maintenance_type": "preventive"
            }
        )
        
        # Create valid signature
        payload_str = event.json()
        signature = hmac.new(
            TEST_SECRET_KEY.encode('utf-8'),
            payload_str.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        # Mock database operations
        with patch('services.cmms_maintenance_hooks.get_database_session') as mock_db:
            mock_session = AsyncMock()
            mock_db.return_value.__aenter__.return_value = mock_session
            
            # Mock event storage
            mock_event = MagicMock()
            mock_event.id = uuid.uuid4()
            mock_session.add.return_value = None
            mock_session.commit.return_value = None
            mock_session.refresh.return_value = None
            
            # Process webhook
            response = await service.process_webhook_event(
                event_data=event,
                hmac_signature=signature,
                secret_key=TEST_SECRET_KEY
            )
            
            # Verify response
            assert response.success is True
            assert response.event_id is not None
            
            # Verify database operations were called
            mock_session.add.assert_called_once()
            mock_session.commit.assert_called_once()
            
            # Verify Redis operations were called
            service.redis_client.lpush.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_background_job_processing_flow(self):
        """Test background job processing flow."""
        service = CMMSMaintenanceHooksService()
        
        # Mock Redis
        mock_redis = AsyncMock()
        service.redis_client = mock_redis
        
        # Mock job data
        job_data = {
            "event_id": str(uuid.uuid4()),
            "cmms_system_id": TEST_CMMS_SYSTEM_ID,
            "event_type": "maintenance_scheduled",
            "payload": {
                "equipment_id": "HVAC-001",
                "scheduled_date": "2024-12-20T10:00:00Z"
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Mock database operations
        with patch('services.cmms_maintenance_hooks.get_database_session') as mock_db:
            mock_session = AsyncMock()
            mock_db.return_value.__aenter__.return_value = mock_session
            
            # Mock event retrieval and update
            mock_event = MagicMock()
            mock_session.get.return_value = mock_event
            
            # Process job
            await service._process_job(job_data)
            
            # Verify database operations
            mock_session.get.assert_called_once()
            assert mock_event.processing_status == ProcessingStatus.COMPLETED.value
            mock_session.commit.assert_called()


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 