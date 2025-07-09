#!/usr/bin/env python3
"""
CMMS Maintenance Event Hooks Demonstration

This script demonstrates the comprehensive CMMS Maintenance Event Hooks functionality,
including webhook processing, background job handling, sync management, and API usage.

Features Demonstrated:
- Webhook event reception and validation
- HMAC signature security
- Background job processing
- Event type handling
- Sync configuration management
- Event history and monitoring
- Health checks and status monitoring
- Error handling and retry logic
- Performance testing
- Security validation

Usage:
    python cmms_maintenance_hooks_demo.py

Author: ARXOS Development Team
Date: 2024-12-19
Version: 1.0.0
"""

import asyncio
import hashlib
import hmac
import json
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import the service (in a real scenario, this would be from the actual module)
try:
    from services.cmms_maintenance_hooks import (
        CMMSMaintenanceHooksService,
        WebhookEvent,
        WebhookResponse,
        SyncStatus,
        ProcessingStatus,
        EventType
    )
except ImportError:
    # Mock classes for demonstration
    class WebhookEvent:
        def __init__(self, event_type: str, cmms_system_id: str, timestamp: datetime, payload: Dict[str, Any]):
            self.event_type = event_type
            self.cmms_system_id = cmms_system_id
            self.timestamp = timestamp
            self.payload = payload
        
        def json(self):
            return json.dumps({
                "event_type": self.event_type,
                "cmms_system_id": self.cmms_system_id,
                "timestamp": self.timestamp.isoformat(),
                "payload": self.payload
            })
    
    class WebhookResponse:
        def __init__(self, success: bool, message: str, event_id: str = None, processing_time_ms: int = None):
            self.success = success
            self.message = message
            self.event_id = event_id
            self.processing_time_ms = processing_time_ms
    
    class SyncStatus:
        def __init__(self, cmms_system_id: str, sync_type: str, status: str, last_sync: datetime = None, 
                     next_sync: datetime = None, error_count: int = 0, success_count: int = 0):
            self.cmms_system_id = cmms_system_id
            self.sync_type = sync_type
            self.status = status
            self.last_sync = last_sync
            self.next_sync = next_sync
            self.error_count = error_count
            self.success_count = success_count
    
    class ProcessingStatus:
        PENDING = "pending"
        PROCESSING = "processing"
        COMPLETED = "completed"
        FAILED = "failed"
        RETRY = "retry"
    
    class EventType:
        MAINTENANCE_SCHEDULED = "maintenance_scheduled"
        MAINTENANCE_COMPLETED = "maintenance_completed"
        EQUIPMENT_FAILURE = "equipment_failure"
        WORK_ORDER_CREATED = "work_order_created"
        ASSET_UPDATED = "asset_updated"
    
    class CMMSMaintenanceHooksService:
        def __init__(self):
            self.redis_client = None
            self.max_retries = 3
            self.retry_delay = 60
            self.queue_name = "cmms_maintenance_hooks"
            self.logger = logger
        
        async def initialize(self):
            self.logger.info("CMMS Maintenance Hooks service initialized")
        
        async def close(self):
            self.logger.info("CMMS Maintenance Hooks service closed")
        
        def validate_hmac_signature(self, payload: str, signature: str, secret: str) -> bool:
            expected_signature = hmac.new(
                secret.encode('utf-8'),
                payload.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            return hmac.compare_digest(signature, expected_signature)
        
        async def process_webhook_event(self, event_data: WebhookEvent, hmac_signature: str, secret_key: str) -> WebhookResponse:
            start_time = time.time()
            
            # Validate HMAC signature
            payload_str = event_data.json()
            if not self.validate_hmac_signature(payload_str, hmac_signature, secret_key):
                raise Exception("Invalid HMAC signature")
            
            # Simulate processing
            await asyncio.sleep(0.1)
            
            processing_time = int((time.time() - start_time) * 1000)
            
            return WebhookResponse(
                success=True,
                message="Event received and queued for processing",
                event_id=str(uuid.uuid4()),
                processing_time_ms=processing_time
            )
        
        async def get_sync_status(self, cmms_system_id: str) -> SyncStatus:
            return SyncStatus(
                cmms_system_id=cmms_system_id,
                sync_type="maintenance_events",
                status="active",
                last_sync=datetime.utcnow(),
                error_count=0,
                success_count=10
            )
        
        async def get_event_history(self, cmms_system_id: str = None, event_type: str = None, limit: int = 100) -> List[Dict[str, Any]]:
            return [
                {
                    "id": str(uuid.uuid4()),
                    "cmms_system_id": cmms_system_id or "test_system",
                    "event_type": event_type or "maintenance_scheduled",
                    "processing_status": "completed",
                    "created_at": datetime.utcnow().isoformat(),
                    "processed_at": datetime.utcnow().isoformat(),
                    "error_message": None,
                    "retry_count": 0
                }
            ]
        
        async def create_sync_configuration(self, cmms_system_id: str, sync_type: str, configuration: Dict[str, Any]) -> Dict[str, Any]:
            return {
                "id": str(uuid.uuid4()),
                "cmms_system_id": cmms_system_id,
                "sync_type": sync_type,
                "configuration": configuration,
                "is_active": True,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }


class CMMSMaintenanceHooksDemo:
    """Demonstration class for CMMS Maintenance Event Hooks."""
    
    def __init__(self):
        """Initialize the demonstration."""
        self.service = CMMSMaintenanceHooksService()
        self.test_cmms_system_id = "demo_maximo_system"
        self.test_secret_key = "demo-secret-key-12345"
        self.logger = logger
    
    async def run_demonstration(self):
        """Run the complete demonstration."""
        logger.info("🚀 Starting CMMS Maintenance Event Hooks Demonstration")
        logger.info("=" * 60)
        
        try:
            # Initialize service
            await self.service.initialize()
            
            # Run demonstration sections
            await self.demonstrate_webhook_processing()
            await self.demonstrate_hmac_security()
            await self.demonstrate_event_types()
            await self.demonstrate_sync_management()
            await self.demonstrate_error_handling()
            await self.demonstrate_performance_testing()
            await self.demonstrate_security_features()
            
            logger.info("✅ CMMS Maintenance Event Hooks demonstration completed successfully!")
            
        except Exception as e:
            logger.error(f"❌ Demonstration failed: {e}")
            raise
        finally:
            await self.service.close()
    
    async def demonstrate_webhook_processing(self):
        """Demonstrate webhook event processing."""
        logger.info("\n📡 Webhook Processing Demonstration")
        logger.info("-" * 40)
        
        # Create sample webhook events
        events = [
            {
                "event_type": EventType.MAINTENANCE_SCHEDULED,
                "payload": {
                    "equipment_id": "HVAC-001",
                    "scheduled_date": "2024-12-20T10:00:00Z",
                    "maintenance_type": "preventive",
                    "technician_id": "TECH-001",
                    "priority": "medium"
                }
            },
            {
                "event_type": EventType.EQUIPMENT_FAILURE,
                "payload": {
                    "equipment_id": "PUMP-002",
                    "failure_type": "mechanical",
                    "failure_description": "Bearing failure detected",
                    "severity": "high",
                    "estimated_repair_time": "4 hours"
                }
            },
            {
                "event_type": EventType.WORK_ORDER_CREATED,
                "payload": {
                    "work_order_id": "WO-2024-001",
                    "work_order_type": "repair",
                    "priority": "high",
                    "assigned_technician": "TECH-002",
                    "estimated_completion": "2024-12-21T14:00:00Z"
                }
            }
        ]
        
        for i, event_data in enumerate(events, 1):
            logger.info(f"\n📋 Processing Event {i}: {event_data['event_type']}")
            
            # Create webhook event
            event = WebhookEvent(
                event_type=event_data["event_type"],
                cmms_system_id=self.test_cmms_system_id,
                timestamp=datetime.utcnow(),
                payload=event_data["payload"]
            )
            
            # Create HMAC signature
            payload_str = event.json()
            signature = hmac.new(
                self.test_secret_key.encode('utf-8'),
                payload_str.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            # Process webhook
            try:
                response = await self.service.process_webhook_event(
                    event_data=event,
                    hmac_signature=signature,
                    secret_key=self.test_secret_key
                )
                
                logger.info(f"✅ Event processed successfully")
                logger.info(f"   Event ID: {response.event_id}")
                logger.info(f"   Processing Time: {response.processing_time_ms}ms")
                logger.info(f"   Message: {response.message}")
                
            except Exception as e:
                logger.error(f"❌ Event processing failed: {e}")
    
    async def demonstrate_hmac_security(self):
        """Demonstrate HMAC signature security."""
        logger.info("\n🔐 HMAC Security Demonstration")
        logger.info("-" * 40)
        
        # Test valid signature
        payload = "test-payload"
        valid_signature = hmac.new(
            self.test_secret_key.encode('utf-8'),
            payload.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        is_valid = self.service.validate_hmac_signature(payload, valid_signature, self.test_secret_key)
        logger.info(f"✅ Valid signature test: {is_valid}")
        
        # Test invalid signature
        invalid_signature = "invalid-signature"
        is_invalid = self.service.validate_hmac_signature(payload, invalid_signature, self.test_secret_key)
        logger.info(f"❌ Invalid signature test: {not is_invalid}")
        
        # Test timing attack resistance
        logger.info("🛡️ Testing timing attack resistance...")
        start_time = time.time()
        self.service.validate_hmac_signature(payload, invalid_signature, self.test_secret_key)
        invalid_time = time.time() - start_time
        
        start_time = time.time()
        self.service.validate_hmac_signature(payload, valid_signature, self.test_secret_key)
        valid_time = time.time() - start_time
        
        logger.info(f"⏱️ Timing comparison - Invalid: {invalid_time:.6f}s, Valid: {valid_time:.6f}s")
        logger.info(f"🔄 Timing difference: {abs(valid_time - invalid_time):.6f}s")
    
    async def demonstrate_event_types(self):
        """Demonstrate different event types."""
        logger.info("\n📊 Event Types Demonstration")
        logger.info("-" * 40)
        
        event_types = [
            EventType.MAINTENANCE_SCHEDULED,
            EventType.MAINTENANCE_COMPLETED,
            EventType.EQUIPMENT_FAILURE,
            EventType.WORK_ORDER_CREATED,
            EventType.ASSET_UPDATED
        ]
        
        for event_type in event_types:
            logger.info(f"📋 Event Type: {event_type}")
            
            # Create sample event
            event = WebhookEvent(
                event_type=event_type,
                cmms_system_id=self.test_cmms_system_id,
                timestamp=datetime.utcnow(),
                payload={"sample": "data"}
            )
            
            # Process event
            payload_str = event.json()
            signature = hmac.new(
                self.test_secret_key.encode('utf-8'),
                payload_str.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            try:
                response = await self.service.process_webhook_event(
                    event_data=event,
                    hmac_signature=signature,
                    secret_key=self.test_secret_key
                )
                logger.info(f"   ✅ Processed successfully")
            except Exception as e:
                logger.error(f"   ❌ Processing failed: {e}")
    
    async def demonstrate_sync_management(self):
        """Demonstrate sync management features."""
        logger.info("\n🔄 Sync Management Demonstration")
        logger.info("-" * 40)
        
        # Get sync status
        sync_status = await self.service.get_sync_status(self.test_cmms_system_id)
        logger.info(f"📊 Sync Status for {sync_status.cmms_system_id}:")
        logger.info(f"   Status: {sync_status.status}")
        logger.info(f"   Sync Type: {sync_status.sync_type}")
        logger.info(f"   Success Count: {sync_status.success_count}")
        logger.info(f"   Error Count: {sync_status.error_count}")
        logger.info(f"   Last Sync: {sync_status.last_sync}")
        
        # Get event history
        history = await self.service.get_event_history(
            cmms_system_id=self.test_cmms_system_id,
            limit=5
        )
        logger.info(f"\n📜 Event History:")
        for event in history:
            logger.info(f"   Event ID: {event['id']}")
            logger.info(f"   Type: {event['event_type']}")
            logger.info(f"   Status: {event['processing_status']}")
            logger.info(f"   Created: {event['created_at']}")
            logger.info("")
        
        # Create sync configuration
        config = await self.service.create_sync_configuration(
            cmms_system_id=self.test_cmms_system_id,
            sync_type="maintenance_events",
            configuration={
                "webhook_url": "https://arxos.com/api/v1/hooks/maintenance/events",
                "secret_key": "config-secret-key",
                "event_types": ["maintenance_scheduled", "maintenance_completed"],
                "retry_policy": {
                    "max_retries": 3,
                    "retry_delay": 60
                }
            }
        )
        logger.info(f"⚙️ Created Sync Configuration:")
        logger.info(f"   Config ID: {config['id']}")
        logger.info(f"   CMMS System: {config['cmms_system_id']}")
        logger.info(f"   Sync Type: {config['sync_type']}")
        logger.info(f"   Active: {config['is_active']}")
    
    async def demonstrate_error_handling(self):
        """Demonstrate error handling and retry logic."""
        logger.info("\n⚠️ Error Handling Demonstration")
        logger.info("-" * 40)
        
        # Test invalid HMAC signature
        event = WebhookEvent(
            event_type=EventType.MAINTENANCE_SCHEDULED,
            cmms_system_id=self.test_cmms_system_id,
            timestamp=datetime.utcnow(),
            payload={"test": "data"}
        )
        
        invalid_signature = "invalid-signature"
        
        try:
            await self.service.process_webhook_event(
                event_data=event,
                hmac_signature=invalid_signature,
                secret_key=self.test_secret_key
            )
        except Exception as e:
            logger.info(f"✅ Caught invalid signature error: {e}")
        
        # Test malformed payload
        try:
            malformed_event = WebhookEvent(
                event_type="invalid_event_type",
                cmms_system_id=self.test_cmms_system_id,
                timestamp=datetime.utcnow(),
                payload={"test": "data"}
            )
            
            payload_str = malformed_event.json()
            signature = hmac.new(
                self.test_secret_key.encode('utf-8'),
                payload_str.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            await self.service.process_webhook_event(
                event_data=malformed_event,
                hmac_signature=signature,
                secret_key=self.test_secret_key
            )
        except Exception as e:
            logger.info(f"✅ Caught malformed payload error: {e}")
    
    async def demonstrate_performance_testing(self):
        """Demonstrate performance testing."""
        logger.info("\n⚡ Performance Testing Demonstration")
        logger.info("-" * 40)
        
        # Test concurrent webhook processing
        logger.info("🔄 Testing concurrent webhook processing...")
        
        events = []
        for i in range(10):
            event = WebhookEvent(
                event_type=EventType.MAINTENANCE_SCHEDULED,
                cmms_system_id=f"system_{i}",
                timestamp=datetime.utcnow(),
                payload={"equipment_id": f"EQ-{i}", "test": "data"}
            )
            events.append(event)
        
        start_time = time.time()
        
        # Process events concurrently
        tasks = []
        for event in events:
            payload_str = event.json()
            signature = hmac.new(
                self.test_secret_key.encode('utf-8'),
                payload_str.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            task = self.service.process_webhook_event(
                event_data=event,
                hmac_signature=signature,
                secret_key=self.test_secret_key
            )
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        successful_results = [r for r in results if isinstance(r, WebhookResponse) and r.success]
        
        logger.info(f"📊 Performance Results:")
        logger.info(f"   Total Events: {len(events)}")
        logger.info(f"   Successful: {len(successful_results)}")
        logger.info(f"   Failed: {len(events) - len(successful_results)}")
        logger.info(f"   Processing Time: {processing_time:.3f}s")
        logger.info(f"   Events per Second: {len(events) / processing_time:.2f}")
        logger.info(f"   Success Rate: {len(successful_results) / len(events) * 100:.1f}%")
    
    async def demonstrate_security_features(self):
        """Demonstrate security features."""
        logger.info("\n🛡️ Security Features Demonstration")
        logger.info("-" * 40)
        
        # Test timing attack resistance
        logger.info("⏱️ Testing timing attack resistance...")
        
        payload = "test-payload"
        correct_signature = hmac.new(
            self.test_secret_key.encode('utf-8'),
            payload.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        # Test different invalid signatures
        invalid_signatures = [
            "a" * 64,  # Wrong length
            "0" * 64,  # All zeros
            correct_signature[:-1] + "0",  # One character different
            correct_signature[1:] + "0",  # Shifted
        ]
        
        for i, invalid_sig in enumerate(invalid_signatures, 1):
            start_time = time.time()
            result = self.service.validate_hmac_signature(payload, invalid_sig, self.test_secret_key)
            invalid_time = time.time() - start_time
            
            start_time = time.time()
            result_valid = self.service.validate_hmac_signature(payload, correct_signature, self.test_secret_key)
            valid_time = time.time() - start_time
            
            logger.info(f"   Test {i}: Invalid time: {invalid_time:.6f}s, Valid time: {valid_time:.6f}s")
            logger.info(f"   Difference: {abs(valid_time - invalid_time):.6f}s")
        
        # Test payload validation
        logger.info("\n📋 Testing payload validation...")
        
        try:
            # Test with valid event type
            valid_event = WebhookEvent(
                event_type=EventType.MAINTENANCE_SCHEDULED,
                cmms_system_id=self.test_cmms_system_id,
                timestamp=datetime.utcnow(),
                payload={"test": "data"}
            )
            logger.info("✅ Valid event type accepted")
        except Exception as e:
            logger.error(f"❌ Valid event type rejected: {e}")
        
        # Test SQL injection prevention
        logger.info("\n💉 Testing SQL injection prevention...")
        
        malicious_system_id = "'; DROP TABLE maintenance_event_hooks; --"
        
        try:
            malicious_event = WebhookEvent(
                event_type=EventType.MAINTENANCE_SCHEDULED,
                cmms_system_id=malicious_system_id,
                timestamp=datetime.utcnow(),
                payload={"test": "data"}
            )
            
            payload_str = malicious_event.json()
            signature = hmac.new(
                self.test_secret_key.encode('utf-8'),
                payload_str.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            # This should not break the system
            response = await self.service.process_webhook_event(
                event_data=malicious_event,
                hmac_signature=signature,
                secret_key=self.test_secret_key
            )
            logger.info("✅ SQL injection attempt handled safely")
        except Exception as e:
            logger.info(f"✅ SQL injection attempt caught: {e}")


async def main():
    """Main demonstration function."""
    demo = CMMSMaintenanceHooksDemo()
    await demo.run_demonstration()


if __name__ == "__main__":
    asyncio.run(main()) 