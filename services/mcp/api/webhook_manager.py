#!/usr/bin/env python3
"""
Webhook Manager for MCP API

This module provides comprehensive webhook capabilities including:
- Multiple webhook types (validation events, system events, user events)
- Retry logic with exponential backoff
- Webhook signature verification
- Real-time event delivery
- Webhook management and monitoring
"""

import asyncio
import json
import logging
import time
import hashlib
import hmac
from typing import Dict, List, Optional, Any, Callable, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import aiohttp
from urllib.parse import urlparse
import threading

from pydantic import BaseModel, HttpUrl

logger = logging.getLogger(__name__)


class WebhookEventType(str, Enum):
    """Webhook event types"""

    VALIDATION_STARTED = "validation.started"
    VALIDATION_COMPLETED = "validation.completed"
    VALIDATION_FAILED = "validation.failed"
    BUILDING_MODEL_UPDATED = "building_model.updated"
    JURISDICTION_CHANGED = "jurisdiction.changed"
    USER_LOGIN = "user.login"
    USER_LOGOUT = "user.logout"
    SYSTEM_ALERT = "system.alert"
    CACHE_INVALIDATED = "cache.invalidated"
    RATE_LIMIT_EXCEEDED = "rate_limit.exceeded"


class WebhookStatus(str, Enum):
    """Webhook delivery status"""

    PENDING = "pending"
    DELIVERED = "delivered"
    FAILED = "failed"
    RETRYING = "retrying"


@dataclass
class WebhookEvent:
    """Webhook event structure"""

    id: str
    event_type: WebhookEventType
    data: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)
    source: str = "mcp_service"
    version: str = "1.0"


@dataclass
class WebhookEndpoint:
    """Webhook endpoint configuration"""

    id: str
    url: str
    secret: str
    events: List[WebhookEventType]
    is_active: bool = True
    retry_count: int = 3
    retry_delay: int = 60  # seconds
    timeout: int = 30  # seconds
    created_at: datetime = field(default_factory=datetime.now)
    last_delivery: Optional[datetime] = None
    delivery_count: int = 0
    failure_count: int = 0


@dataclass
class WebhookDelivery:
    """Webhook delivery attempt"""

    id: str
    endpoint_id: str
    event_id: str
    status: WebhookStatus
    attempt: int = 1
    response_code: Optional[int] = None
    response_body: Optional[str] = None
    error_message: Optional[str] = None
    delivered_at: Optional[datetime] = None
    next_retry: Optional[datetime] = None


class WebhookSignature:
    """Webhook signature utilities"""

    @staticmethod
    def generate_signature(payload: str, secret: str) -> str:
        """Generate HMAC signature for webhook payload"""
        return hmac.new(
            secret.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256
        ).hexdigest()

    @staticmethod
    def verify_signature(payload: str, signature: str, secret: str) -> bool:
        """Verify webhook signature"""
        expected_signature = WebhookSignature.generate_signature(payload, secret)
        return hmac.compare_digest(signature, expected_signature)


class WebhookRetryManager:
    """Manages webhook retry logic with exponential backoff"""

    def __init__(self, max_retries: int = 3, base_delay: int = 60):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.retry_queue: asyncio.Queue = asyncio.Queue()
        self.retry_task: Optional[asyncio.Task] = None

        # Start retry worker
        self._start_retry_worker()

    def _start_retry_worker(self):
        """Start background retry worker"""
        loop = asyncio.get_event_loop()
        self.retry_task = loop.create_task(self._retry_worker())

    async def _retry_worker(self):
        """Background worker for handling retries"""
        while True:
            try:
                delivery = await self.retry_queue.get()

                if delivery.status == WebhookStatus.RETRYING:
                    # Calculate delay with exponential backoff
                    delay = self.base_delay * (2 ** (delivery.attempt - 1))

                    # Wait for retry
                    await asyncio.sleep(delay)

                    # Attempt delivery
                    success = await self._attempt_delivery(delivery)

                    if not success and delivery.attempt < self.max_retries:
                        # Schedule next retry
                        delivery.attempt += 1
                        delivery.next_retry = datetime.now() + timedelta(
                            seconds=delay * 2
                        )
                        await self.retry_queue.put(delivery)
                    elif not success:
                        # Max retries reached
                        delivery.status = WebhookStatus.FAILED
                        logger.error(
                            f"Webhook delivery failed after {self.max_retries} attempts: {delivery.endpoint_id}"
                        )

                self.retry_queue.task_done()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in webhook retry worker: {e}")

    async def _attempt_delivery(self, delivery: WebhookDelivery) -> bool:
        """Attempt webhook delivery"""
        try:
            # Get endpoint configuration
            endpoint = webhook_manager.get_endpoint(delivery.endpoint_id)
            if not endpoint:
                logger.error(f"Webhook endpoint not found: {delivery.endpoint_id}")
                return False

            # Get event data
            event = webhook_manager.get_event(delivery.event_id)
            if not event:
                logger.error(f"Webhook event not found: {delivery.event_id}")
                return False

            # Prepare payload
            payload = {
                "id": event.id,
                "event_type": event.event_type.value,
                "data": event.data,
                "timestamp": event.timestamp.isoformat(),
                "source": event.source,
                "version": event.version,
            }

            # Generate signature
            payload_str = json.dumps(payload, sort_keys=True)
            signature = WebhookSignature.generate_signature(
                payload_str, endpoint.secret
            )

            # Prepare headers
            headers = {
                "Content-Type": "application/json",
                "X-Webhook-Signature": signature,
                "X-Webhook-Event": event.event_type.value,
                "X-Webhook-ID": event.id,
                "User-Agent": "MCP-Webhook/1.0",
            }

            # Send webhook
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    endpoint.url,
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=endpoint.timeout),
                ) as response:
                    delivery.response_code = response.status
                    delivery.response_body = await response.text()

                    if response.status in [200, 201, 202]:
                        delivery.status = WebhookStatus.DELIVERED
                        delivery.delivered_at = datetime.now()
                        endpoint.last_delivery = datetime.now()
                        endpoint.delivery_count += 1
                        logger.info(f"Webhook delivered successfully: {endpoint.url}")
                        return True
                    else:
                        delivery.status = WebhookStatus.FAILED
                        delivery.error_message = (
                            f"HTTP {response.status}: {delivery.response_body}"
                        )
                        endpoint.failure_count += 1
                        logger.warning(
                            f"Webhook delivery failed: {endpoint.url} - {delivery.error_message}"
                        )
                        return False

        except asyncio.TimeoutError:
            delivery.status = WebhookStatus.FAILED
            delivery.error_message = "Request timeout"
            logger.warning(f"Webhook delivery timeout: {delivery.endpoint_id}")
            return False
        except Exception as e:
            delivery.status = WebhookStatus.FAILED
            delivery.error_message = str(e)
            logger.error(f"Webhook delivery error: {delivery.endpoint_id} - {e}")
            return False

    async def schedule_retry(self, delivery: WebhookDelivery):
        """Schedule webhook for retry"""
        delivery.status = WebhookStatus.RETRYING
        await self.retry_queue.put(delivery)

    async def shutdown(self):
        """Shutdown retry manager"""
        if self.retry_task:
            self.retry_task.cancel()
            try:
                await self.retry_task
            except asyncio.CancelledError:
                pass


class WebhookManager:
    """Central webhook manager"""

    def __init__(self):
        self.endpoints: Dict[str, WebhookEndpoint] = {}
        self.events: Dict[str, WebhookEvent] = {}
        self.deliveries: Dict[str, WebhookDelivery] = {}
        self.retry_manager = WebhookRetryManager()
        self.event_queue: asyncio.Queue = asyncio.Queue()
        self.delivery_task: Optional[asyncio.Task] = None

        # Start delivery worker
        self._start_delivery_worker()

    def _start_delivery_worker(self):
        """Start background delivery worker"""
        loop = asyncio.get_event_loop()
        self.delivery_task = loop.create_task(self._delivery_worker())

    async def _delivery_worker(self):
        """Background worker for webhook delivery"""
        while True:
            try:
                event = await self.event_queue.get()

                # Store event
                self.events[event.id] = event

                # Find matching endpoints
                matching_endpoints = [
                    endpoint
                    for endpoint in self.endpoints.values()
                    if endpoint.is_active and event.event_type in endpoint.events
                ]

                # Create deliveries for each endpoint
                for endpoint in matching_endpoints:
                    delivery = WebhookDelivery(
                        id=f"delivery_{len(self.deliveries) + 1}",
                        endpoint_id=endpoint.id,
                        event_id=event.id,
                        status=WebhookStatus.PENDING,
                    )

                    self.deliveries[delivery.id] = delivery

                    # Attempt immediate delivery
                    success = await self.retry_manager._attempt_delivery(delivery)

                    if not success and endpoint.retry_count > 0:
                        # Schedule for retry
                        await self.retry_manager.schedule_retry(delivery)

                self.event_queue.task_done()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in webhook delivery worker: {e}")

    async def register_endpoint(self, endpoint: WebhookEndpoint) -> bool:
        """Register a new webhook endpoint"""
        try:
            # Validate URL
            parsed_url = urlparse(endpoint.url)
            if not parsed_url.scheme or not parsed_url.netloc:
                raise ValueError("Invalid webhook URL")

            # Validate secret
            if not endpoint.secret or len(endpoint.secret) < 16:
                raise ValueError("Webhook secret must be at least 16 characters")

            # Store endpoint
            self.endpoints[endpoint.id] = endpoint
            logger.info(f"Registered webhook endpoint: {endpoint.url}")
            return True

        except Exception as e:
            logger.error(f"Failed to register webhook endpoint: {e}")
            return False

    async def unregister_endpoint(self, endpoint_id: str) -> bool:
        """Unregister a webhook endpoint"""
        if endpoint_id in self.endpoints:
            del self.endpoints[endpoint_id]
            logger.info(f"Unregistered webhook endpoint: {endpoint_id}")
            return True
        return False

    async def update_endpoint(self, endpoint_id: str, updates: Dict[str, Any]) -> bool:
        """Update webhook endpoint configuration"""
        if endpoint_id not in self.endpoints:
            return False

        endpoint = self.endpoints[endpoint_id]

        # Update fields
        for field, value in updates.items():
            if hasattr(endpoint, field):
                setattr(endpoint, field, value)

        logger.info(f"Updated webhook endpoint: {endpoint_id}")
        return True

    async def trigger_event(
        self,
        event_type: WebhookEventType,
        data: Dict[str, Any],
        source: str = "mcp_service",
    ) -> str:
        """Trigger a webhook event"""
        event = WebhookEvent(
            id=f"event_{len(self.events) + 1}_{int(time.time())}",
            event_type=event_type,
            data=data,
            source=source,
        )

        # Queue event for delivery
        await self.event_queue.put(event)
        logger.info(f"Triggered webhook event: {event_type.value}")

        return event.id

    def get_endpoint(self, endpoint_id: str) -> Optional[WebhookEndpoint]:
        """Get webhook endpoint by ID"""
        return self.endpoints.get(endpoint_id)

    def get_event(self, event_id: str) -> Optional[WebhookEvent]:
        """Get webhook event by ID"""
        return self.events.get(event_id)

    def get_delivery(self, delivery_id: str) -> Optional[WebhookDelivery]:
        """Get webhook delivery by ID"""
        return self.deliveries.get(delivery_id)

    def get_endpoints_by_event(
        self, event_type: WebhookEventType
    ) -> List[WebhookEndpoint]:
        """Get endpoints that subscribe to a specific event type"""
        return [
            endpoint
            for endpoint in self.endpoints.values()
            if endpoint.is_active and event_type in endpoint.events
        ]

    def get_delivery_stats(self) -> Dict[str, Any]:
        """Get webhook delivery statistics"""
        total_deliveries = len(self.deliveries)
        successful_deliveries = len(
            [d for d in self.deliveries.values() if d.status == WebhookStatus.DELIVERED]
        )
        failed_deliveries = len(
            [d for d in self.deliveries.values() if d.status == WebhookStatus.FAILED]
        )
        pending_deliveries = len(
            [d for d in self.deliveries.values() if d.status == WebhookStatus.PENDING]
        )

        return {
            "total_deliveries": total_deliveries,
            "successful_deliveries": successful_deliveries,
            "failed_deliveries": failed_deliveries,
            "pending_deliveries": pending_deliveries,
            "success_rate": (
                (successful_deliveries / total_deliveries * 100)
                if total_deliveries > 0
                else 0
            ),
            "total_endpoints": len(self.endpoints),
            "active_endpoints": len(
                [e for e in self.endpoints.values() if e.is_active]
            ),
            "total_events": len(self.events),
        }

    def get_endpoint_stats(self, endpoint_id: str) -> Optional[Dict[str, Any]]:
        """Get statistics for a specific endpoint"""
        endpoint = self.get_endpoint(endpoint_id)
        if not endpoint:
            return None

        endpoint_deliveries = [
            d for d in self.deliveries.values() if d.endpoint_id == endpoint_id
        ]

        successful = len(
            [d for d in endpoint_deliveries if d.status == WebhookStatus.DELIVERED]
        )
        failed = len(
            [d for d in endpoint_deliveries if d.status == WebhookStatus.FAILED]
        )
        total = len(endpoint_deliveries)

        return {
            "endpoint_id": endpoint_id,
            "url": endpoint.url,
            "is_active": endpoint.is_active,
            "total_deliveries": total,
            "successful_deliveries": successful,
            "failed_deliveries": failed,
            "success_rate": (successful / total * 100) if total > 0 else 0,
            "delivery_count": endpoint.delivery_count,
            "failure_count": endpoint.failure_count,
            "last_delivery": (
                endpoint.last_delivery.isoformat() if endpoint.last_delivery else None
            ),
            "created_at": endpoint.created_at.isoformat(),
        }

    async def test_endpoint(self, endpoint_id: str) -> Dict[str, Any]:
        """Test webhook endpoint with a test event"""
        endpoint = self.get_endpoint(endpoint_id)
        if not endpoint:
            return {"success": False, "error": "Endpoint not found"}

        # Create test event
        test_data = {
            "test": True,
            "message": "This is a test webhook event",
            "timestamp": datetime.now().isoformat(),
        }

        event_id = await self.trigger_event(
            WebhookEventType.SYSTEM_ALERT, test_data, "webhook_test"
        )

        # Wait for delivery
        await asyncio.sleep(2)

        # Check delivery status
        deliveries = [
            d
            for d in self.deliveries.values()
            if d.event_id == event_id and d.endpoint_id == endpoint_id
        ]

        if deliveries:
            delivery = deliveries[0]
            return {
                "success": delivery.status == WebhookStatus.DELIVERED,
                "status": delivery.status.value,
                "response_code": delivery.response_code,
                "error_message": delivery.error_message,
            }
        else:
            return {"success": False, "error": "No delivery found"}

    async def shutdown(self):
        """Shutdown webhook manager"""
        if self.delivery_task:
            self.delivery_task.cancel()
            try:
                await self.delivery_task
            except asyncio.CancelledError:
                pass

        await self.retry_manager.shutdown()
        logger.info("Webhook manager shutdown complete")


# Global webhook manager instance
webhook_manager = WebhookManager()


# Convenience functions for triggering events
async def trigger_validation_event(
    event_type: WebhookEventType, building_id: str, validation_data: Dict[str, Any]
):
    """Trigger validation-related webhook event"""
    data = {
        "building_id": building_id,
        "validation_data": validation_data,
        "timestamp": datetime.now().isoformat(),
    }

    await webhook_manager.trigger_event(event_type, data)


async def trigger_user_event(
    event_type: WebhookEventType, user_id: str, user_data: Dict[str, Any]
):
    """Trigger user-related webhook event"""
    data = {
        "user_id": user_id,
        "user_data": user_data,
        "timestamp": datetime.now().isoformat(),
    }

    await webhook_manager.trigger_event(event_type, data)


async def trigger_system_event(
    event_type: WebhookEventType, system_data: Dict[str, Any]
):
    """Trigger system-related webhook event"""
    data = {"system_data": system_data, "timestamp": datetime.now().isoformat()}

    await webhook_manager.trigger_event(event_type, data)
