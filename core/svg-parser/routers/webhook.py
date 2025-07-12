"""
Webhook router for handling external notifications.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Dict, Any, Optional
import httpx
import asyncio
from datetime import datetime

from models.webhook import WebhookRequest, WebhookResponse
from services.robust_error_handling import create_error_handler

router = APIRouter(prefix="/webhook", tags=["webhook"])
error_handler = create_error_handler()


@router.post("/notify", response_model=WebhookResponse)
async def notify_webhook(webhook: WebhookRequest, background_tasks: BackgroundTasks):
    """
    Send webhook notification to external service.
    
    Args:
        webhook: Webhook request data
        background_tasks: FastAPI background tasks
        
    Returns:
        WebhookResponse: Notification result
    """
    try:
        # Implement webhook notification logic
        notification_result = await _send_webhook_notification(webhook)
        
        # Add to background tasks for async processing
        background_tasks.add_task(_process_webhook_async, webhook)
        
        return WebhookResponse(
            success=True,
            message="Webhook notification sent successfully",
            timestamp=datetime.now(),
            webhook_id=webhook.webhook_id,
            status="sent"
        )
        
    except Exception as e:
        error_handler.handle_webhook_error(str(e), webhook.webhook_id)
        raise HTTPException(status_code=500, detail=f"Webhook notification failed: {str(e)}")


async def _send_webhook_notification(webhook: WebhookRequest) -> Dict[str, Any]:
    """Send webhook notification to external service."""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                webhook.url,
                json=webhook.payload,
                headers=webhook.headers or {}
            )
            
            return {
                "status_code": response.status_code,
                "response": response.text,
                "success": response.status_code < 400
            }
            
    except httpx.TimeoutException:
        raise Exception("Webhook request timed out")
    except httpx.RequestError as e:
        raise Exception(f"Webhook request failed: {str(e)}")


async def _process_webhook_async(webhook: WebhookRequest):
    """Process webhook asynchronously."""
    try:
        # Additional async processing logic
        await asyncio.sleep(0.1)  # Simulate processing time
        
        # Log webhook processing
        print(f"Processed webhook: {webhook.webhook_id}")
        
    except Exception as e:
        error_handler.handle_webhook_error(str(e), webhook.webhook_id) 