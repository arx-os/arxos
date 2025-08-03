"""
Notification API for Arxos SVG-BIM Integration

This FastAPI application provides comprehensive notification capabilities including
email, Slack, SMS, and webhook notifications with enterprise-grade features.

Author: Arxos Engineering Team
Date: 2024-12-19
Version: 1.0.0
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, validator
from enum import Enum

# Import notification services
from svgx_engine.services.notifications.email_notification_service import (
    EmailNotificationService, SMTPConfig, EmailMessage, EmailPriority, EmailStatus
)
from svgx_engine.services.notifications.slack_notification_service import (
    SlackNotificationService, SlackWebhookConfig, SlackMessage, SlackMessageType, SlackMessageStatus
)
from svgx_engine.services.notifications.sms_notification_service import (
    SMSNotificationService, SMSProviderConfig, SMSMessage, SMSProvider, SMSMessageStatus
)
from svgx_engine.services.notifications.webhook_notification_service import (
    WebhookNotificationService, WebhookConfig, WebhookMessage, WebhookMethod, WebhookStatus
)
from svgx_engine.services.notifications.notification_system import (
from core.security.auth_middleware import get_current_user, User
    UnifiedNotificationSystem, NotificationChannel, NotificationPriority, NotificationConfig,
    NotificationResult, UnifiedNotification
)

logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Arxos Notification API",
    description="Comprehensive notification system for email, Slack, SMS, and webhook notifications",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize notification services
email_service = EmailNotificationService()
slack_service = SlackNotificationService()
sms_service = SMSNotificationService()
webhook_service = WebhookNotificationService()
unified_system = UnifiedNotificationSystem()

# Pydantic models for API requests/responses

class NotificationPriorityEnum(str, Enum):
    """Notification priority levels."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"

class NotificationChannelEnum(str, Enum):
    """Notification channels."""
    EMAIL = "email"
    SLACK = "slack"
    SMS = "sms"
    WEBHOOK = "webhook"

class SMTPConfigRequest(BaseModel):
    """SMTP configuration request."""
    host: str = Field(..., description="SMTP server host")
    port: int = Field(587, description="SMTP server port")
    username: str = Field(..., description="SMTP username")
    password: str = Field(..., description="SMTP password")
    use_tls: bool = Field(True, description="Use TLS encryption")
    use_ssl: bool = Field(False, description="Use SSL encryption")
    timeout: int = Field(30, description="Connection timeout in seconds")
    max_retries: int = Field(3, description="Maximum retry attempts")

class SlackWebhookConfigRequest(BaseModel):
    """Slack webhook configuration request."""
    webhook_url: str = Field(..., description="Slack webhook URL")
    username: str = Field("Arxos Bot", description="Bot username")
    icon_emoji: str = Field(":robot_face:", description="Bot icon emoji")
    channel: str = Field("#general", description="Default channel")
    timeout: int = Field(30, description="Request timeout in seconds")
    max_retries: int = Field(3, description="Maximum retry attempts")
    rate_limit_delay: int = Field(1, description="Rate limit delay in seconds")

class SMSProviderConfigRequest(BaseModel):
    """SMS provider configuration request."""
    provider: str = Field(..., description="SMS provider (twilio, aws_sns, custom)")
    api_key: str = Field(..., description="Provider API key")
    api_secret: str = Field(..., description="Provider API secret")
    from_number: str = Field(..., description="Sender phone number")
    webhook_url: Optional[str] = Field(None, description="Custom webhook URL")
    timeout: int = Field(30, description="Request timeout in seconds")
    max_retries: int = Field(3, description="Maximum retry attempts")
    rate_limit_delay: int = Field(1, description="Rate limit delay in seconds")

class WebhookConfigRequest(BaseModel):
    """Webhook configuration request."""
    url: str = Field(..., description="Webhook URL")
    method: str = Field("POST", description="HTTP method")
    headers: Dict[str, str] = Field(default_factory=dict, description="HTTP headers")
    timeout: int = Field(30, description="Request timeout in seconds")
    max_retries: int = Field(3, description="Maximum retry attempts")
    rate_limit_delay: int = Field(1, description="Rate limit delay in seconds")
    auth_token: Optional[str] = Field(None, description="Authentication token")

class EmailNotificationRequest(BaseModel):
    """Email notification request."""
    to: str = Field(..., description="Recipient email address")
    subject: str = Field(..., description="Email subject")
    body: str = Field(..., description="Email body")
    from_address: Optional[str] = Field(None, description="Sender email address")
    html_body: Optional[str] = Field(None, description="HTML email body")
    priority: NotificationPriorityEnum = Field(NotificationPriorityEnum.NORMAL, description="Email priority")
    template_id: Optional[str] = Field(None, description="Template ID")
    template_data: Optional[Dict[str, Any]] = Field(None, description="Template data")

class SlackNotificationRequest(BaseModel):
    """Slack notification request."""
    text: str = Field(..., description="Message text")
    channel: Optional[str] = Field(None, description="Target channel")
    username: Optional[str] = Field(None, description="Bot username")
    icon_emoji: Optional[str] = Field(None, description="Bot icon emoji")
    attachments: Optional[List[Dict[str, Any]]] = Field(None, description="Message attachments")
    blocks: Optional[List[Dict[str, Any]]] = Field(None, description="Message blocks")
    thread_ts: Optional[str] = Field(None, description="Thread timestamp")

class SMSNotificationRequest(BaseModel):
    """SMS notification request."""
    to: str = Field(..., description="Recipient phone number")
    body: str = Field(..., description="Message body")
    from_number: Optional[str] = Field(None, description="Sender phone number")

class WebhookNotificationRequest(BaseModel):
    """Webhook notification request."""
    url: str = Field(..., description="Webhook URL")
    payload: Dict[str, Any] = Field(..., description="Message payload")
    method: str = Field("POST", description="HTTP method")
    headers: Optional[Dict[str, str]] = Field(None, description="HTTP headers")

class UnifiedNotificationRequest(BaseModel):
    """Unified notification request."""
    title: str = Field(..., description="Notification title")
    message: str = Field(..., description="Notification message")
    channels: List[NotificationChannelEnum] = Field(..., description="Target channels")
    priority: NotificationPriorityEnum = Field(NotificationPriorityEnum.NORMAL, description="Notification priority")
    template_data: Optional[Dict[str, Any]] = Field(None, description="Template data")

class NotificationResponse(BaseModel):
    """Notification response."""
    success: bool = Field(..., description="Success status")
    message_id: str = Field(..., description="Message ID")
    status: str = Field(..., description="Delivery status")
    sent_at: Optional[datetime] = Field(None, description="Sent timestamp")
    delivered_at: Optional[datetime] = Field(None, description="Delivered timestamp")
    error_message: Optional[str] = Field(None, description="Error message")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

class NotificationStatistics(BaseModel):
    """Notification statistics."""
    total_notifications: int = Field(..., description="Total notifications")
    successful_notifications: int = Field(..., description="Successful notifications")
    failed_notifications: int = Field(..., description="Failed notifications")
    channel_usage: Dict[str, int] = Field(..., description="Channel usage statistics")
    priority_usage: Dict[str, int] = Field(..., description="Priority usage statistics")
    average_delivery_time: float = Field(..., description="Average delivery time")

class ConfigurationResponse(BaseModel):
    """Configuration response."""
    success: bool = Field(..., description="Success status")
    message: str = Field(..., description="Configuration message")
    service: str = Field(..., description="Service name")

# API Endpoints

@app.get("/")
async def endpoint_name(request: Request, user: User = Depends(get_current_user)):
async def root(user: User = Depends(get_current_user)):
    """Root endpoint."""
    return {
        "message": "Arxos Notification API",
        "version": "1.0.0",
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
async def endpoint_name(request: Request, user: User = Depends(get_current_user)):
async def health_check(user: User = Depends(get_current_user)):
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "email": "available",
            "slack": "available",
            "sms": "available",
            "webhook": "available",
            "unified": "available"
        }
    }

# Configuration endpoints

@app.post("/config/email", response_model=ConfigurationResponse)
async def configure_email(config: SMTPConfigRequest, user: User = Depends(get_current_user)):
    """Configure email service."""
    try:
        smtp_config = SMTPConfig(
            host=config.host,
            port=config.port,
            username=config.username,
            password=config.password,
            use_tls=config.use_tls,
            use_ssl=config.use_ssl,
            timeout=config.timeout,
            max_retries=config.max_retries
        )
        
        email_service.configure_smtp(smtp_config)
        
        return ConfigurationResponse(
            success=True,
            message="Email service configured successfully",
            service="email"
        )
    except Exception as e:
        logger.error(f"Email configuration failed: {e}")
        raise HTTPException(status_code=500, detail=f"Email configuration failed: {str(e)}")

@app.post("/config/slack", response_model=ConfigurationResponse)
async def configure_slack(config: SlackWebhookConfigRequest, user: User = Depends(get_current_user)):
    """Configure Slack service."""
    try:
        webhook_config = SlackWebhookConfig(
            webhook_url=config.webhook_url,
            username=config.username,
            icon_emoji=config.icon_emoji,
            channel=config.channel,
            timeout=config.timeout,
            max_retries=config.max_retries,
            rate_limit_delay=config.rate_limit_delay
        )
        
        slack_service.configure_webhook(webhook_config)
        
        return ConfigurationResponse(
            success=True,
            message="Slack service configured successfully",
            service="slack"
        )
    except Exception as e:
        logger.error(f"Slack configuration failed: {e}")
        raise HTTPException(status_code=500, detail=f"Slack configuration failed: {str(e)}")

@app.post("/config/sms", response_model=ConfigurationResponse)
async def configure_sms(config: SMSProviderConfigRequest, user: User = Depends(get_current_user)):
    """Configure SMS service."""
    try:
        provider_map = {
            "twilio": SMSProvider.TWILIO,
            "aws_sns": SMSProvider.AWS_SNS,
            "custom": SMSProvider.CUSTOM
        }
        
        provider_config = SMSProviderConfig(
            provider=provider_map.get(config.provider, SMSProvider.CUSTOM),
            api_key=config.api_key,
            api_secret=config.api_secret,
            from_number=config.from_number,
            webhook_url=config.webhook_url,
            timeout=config.timeout,
            max_retries=config.max_retries,
            rate_limit_delay=config.rate_limit_delay
        )
        
        sms_service.configure_provider(provider_config)
        
        return ConfigurationResponse(
            success=True,
            message="SMS service configured successfully",
            service="sms"
        )
    except Exception as e:
        logger.error(f"SMS configuration failed: {e}")
        raise HTTPException(status_code=500, detail=f"SMS configuration failed: {str(e)}")

@app.post("/config/webhook", response_model=ConfigurationResponse)
async def configure_webhook(config: WebhookConfigRequest, user: User = Depends(get_current_user)):
    """Configure webhook service."""
    try:
        method_map = {
            "GET": WebhookMethod.GET,
            "POST": WebhookMethod.POST,
            "PUT": WebhookMethod.PUT,
            "PATCH": WebhookMethod.PATCH
        }
        
        webhook_config = WebhookConfig(
            url=config.url,
            method=method_map.get(config.method, WebhookMethod.POST),
            headers=config.headers,
            timeout=config.timeout,
            max_retries=config.max_retries,
            rate_limit_delay=config.rate_limit_delay,
            auth_token=config.auth_token
        )
        
        webhook_service.configure_webhook(webhook_config)
        
        return ConfigurationResponse(
            success=True,
            message="Webhook service configured successfully",
            service="webhook"
        )
    except Exception as e:
        logger.error(f"Webhook configuration failed: {e}")
        raise HTTPException(status_code=500, detail=f"Webhook configuration failed: {str(e)}")

# Email notification endpoints

@app.post("/notifications/email", response_model=NotificationResponse)
async def send_email_notification(request: EmailNotificationRequest, user: User = Depends(get_current_user)):
    """Send email notification."""
    try:
        result = await email_service.send_email(
            to=request.to,
            subject=request.subject,
            body=request.body,
            from_address=request.from_address,
            html_body=request.html_body,
            priority=EmailPriority(request.priority.value),
            template_id=request.template_id,
            template_data=request.template_data
        )
        
        return NotificationResponse(
            success=result.success,
            message_id=result.message_id,
            status=result.status.value,
            sent_at=result.sent_at,
            delivered_at=result.delivered_at,
            error_message=result.error_message,
            metadata=result.metadata
        )
    except Exception as e:
        logger.error(f"Email notification failed: {e}")
        raise HTTPException(status_code=500, detail=f"Email notification failed: {str(e)}")

@app.get("/notifications/email/{message_id}", response_model=NotificationResponse)
async def get_email_notification(message_id: str, user: User = Depends(get_current_user)):
    """Get email notification by ID."""
    try:
        message = email_service.get_message(message_id)
        if not message:
            raise HTTPException(status_code=404, detail="Email notification not found")
        
        result = email_service.get_delivery_result(message_id)
        if not result:
            raise HTTPException(status_code=404, detail="Email delivery result not found")
        
        return NotificationResponse(
            success=result.success,
            message_id=result.message_id,
            status=result.status.value,
            sent_at=result.sent_at,
            delivered_at=result.delivered_at,
            error_message=result.error_message,
            metadata=result.metadata
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get email notification failed: {e}")
        raise HTTPException(status_code=500, detail=f"Get email notification failed: {str(e)}")

@app.get("/notifications/email/statistics", response_model=NotificationStatistics)
async def get_email_statistics(user: User = Depends(get_current_user)):
    """Get email statistics."""
    try:
        stats = email_service.get_email_statistics()
        
        return NotificationStatistics(
            total_notifications=stats["total_emails"],
            successful_notifications=stats["successful_emails"],
            failed_notifications=stats["failed_emails"],
            channel_usage={"email": stats["total_emails"]},
            priority_usage=stats["priority_usage"],
            average_delivery_time=stats["average_delivery_time"]
        )
    except Exception as e:
        logger.error(f"Get email statistics failed: {e}")
        raise HTTPException(status_code=500, detail=f"Get email statistics failed: {str(e)}")

# Slack notification endpoints

@app.post("/notifications/slack", response_model=NotificationResponse)
async def send_slack_notification(request: SlackNotificationRequest, user: User = Depends(get_current_user)):
    """Send Slack notification."""
    try:
        result = await slack_service.send_message(
            text=request.text,
            channel=request.channel,
            username=request.username,
            icon_emoji=request.icon_emoji,
            attachments=request.attachments,
            blocks=request.blocks,
            thread_ts=request.thread_ts
        )
        
        return NotificationResponse(
            success=result.success,
            message_id=result.message_id,
            status=result.status.value,
            sent_at=result.sent_at,
            delivered_at=result.delivered_at,
            error_message=result.error_message,
            metadata=result.metadata
        )
    except Exception as e:
        logger.error(f"Slack notification failed: {e}")
        raise HTTPException(status_code=500, detail=f"Slack notification failed: {str(e)}")

@app.get("/notifications/slack/{message_id}", response_model=NotificationResponse)
async def get_slack_notification(message_id: str, user: User = Depends(get_current_user)):
    """Get Slack notification by ID."""
    try:
        message = slack_service.get_message(message_id)
        if not message:
            raise HTTPException(status_code=404, detail="Slack notification not found")
        
        result = slack_service.get_delivery_result(message_id)
        if not result:
            raise HTTPException(status_code=404, detail="Slack delivery result not found")
        
        return NotificationResponse(
            success=result.success,
            message_id=result.message_id,
            status=result.status.value,
            sent_at=result.sent_at,
            delivered_at=result.delivered_at,
            error_message=result.error_message,
            metadata=result.metadata
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get Slack notification failed: {e}")
        raise HTTPException(status_code=500, detail=f"Get Slack notification failed: {str(e)}")

@app.get("/notifications/slack/statistics", response_model=NotificationStatistics)
async def get_slack_statistics(user: User = Depends(get_current_user)):
    """Get Slack statistics."""
    try:
        stats = slack_service.get_slack_statistics()
        
        return NotificationStatistics(
            total_notifications=stats["total_messages"],
            successful_notifications=stats["successful_messages"],
            failed_notifications=stats["failed_messages"],
            channel_usage=stats["channel_usage"],
            priority_usage={},
            average_delivery_time=stats["average_delivery_time"]
        )
    except Exception as e:
        logger.error(f"Get Slack statistics failed: {e}")
        raise HTTPException(status_code=500, detail=f"Get Slack statistics failed: {str(e)}")

# SMS notification endpoints

@app.post("/notifications/sms", response_model=NotificationResponse)
async def send_sms_notification(request: SMSNotificationRequest, user: User = Depends(get_current_user)):
    """Send SMS notification."""
    try:
        result = await sms_service.send_message(
            to=request.to,
            body=request.body,
            from_number=request.from_number
        )
        
        return NotificationResponse(
            success=result.success,
            message_id=result.message_id,
            status=result.status.value,
            sent_at=result.sent_at,
            delivered_at=result.delivered_at,
            error_message=result.error_message,
            metadata=result.metadata
        )
    except Exception as e:
        logger.error(f"SMS notification failed: {e}")
        raise HTTPException(status_code=500, detail=f"SMS notification failed: {str(e)}")

@app.get("/notifications/sms/{message_id}", response_model=NotificationResponse)
async def get_sms_notification(message_id: str, user: User = Depends(get_current_user)):
    """Get SMS notification by ID."""
    try:
        message = sms_service.get_message(message_id)
        if not message:
            raise HTTPException(status_code=404, detail="SMS notification not found")
        
        result = sms_service.get_delivery_result(message_id)
        if not result:
            raise HTTPException(status_code=404, detail="SMS delivery result not found")
        
        return NotificationResponse(
            success=result.success,
            message_id=result.message_id,
            status=result.status.value,
            sent_at=result.sent_at,
            delivered_at=result.delivered_at,
            error_message=result.error_message,
            metadata=result.metadata
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get SMS notification failed: {e}")
        raise HTTPException(status_code=500, detail=f"Get SMS notification failed: {str(e)}")

@app.get("/notifications/sms/statistics", response_model=NotificationStatistics)
async def get_sms_statistics(user: User = Depends(get_current_user)):
    """Get SMS statistics."""
    try:
        stats = sms_service.get_sms_statistics()
        
        return NotificationStatistics(
            total_notifications=stats["total_messages"],
            successful_notifications=stats["successful_messages"],
            failed_notifications=stats["failed_messages"],
            channel_usage=stats["provider_usage"],
            priority_usage={},
            average_delivery_time=stats["average_delivery_time"]
        )
    except Exception as e:
        logger.error(f"Get SMS statistics failed: {e}")
        raise HTTPException(status_code=500, detail=f"Get SMS statistics failed: {str(e)}")

# Webhook notification endpoints

@app.post("/notifications/webhook", response_model=NotificationResponse)
async def send_webhook_notification(request: WebhookNotificationRequest, user: User = Depends(get_current_user)):
    """Send webhook notification."""
    try:
        method_map = {
            "GET": WebhookMethod.GET,
            "POST": WebhookMethod.POST,
            "PUT": WebhookMethod.PUT,
            "PATCH": WebhookMethod.PATCH
        }
        
        result = await webhook_service.send_webhook(
            url=request.url,
            payload=request.payload,
            method=method_map.get(request.method, WebhookMethod.POST),
            headers=request.headers
        )
        
        return NotificationResponse(
            success=result.success,
            message_id=result.message_id,
            status=result.status.value,
            sent_at=result.sent_at,
            delivered_at=result.delivered_at,
            error_message=result.error_message,
            metadata=result.metadata
        )
    except Exception as e:
        logger.error(f"Webhook notification failed: {e}")
        raise HTTPException(status_code=500, detail=f"Webhook notification failed: {str(e)}")

@app.get("/notifications/webhook/{message_id}", response_model=NotificationResponse)
async def get_webhook_notification(message_id: str, user: User = Depends(get_current_user)):
    """Get webhook notification by ID."""
    try:
        message = webhook_service.get_message(message_id)
        if not message:
            raise HTTPException(status_code=404, detail="Webhook notification not found")
        
        result = webhook_service.get_delivery_result(message_id)
        if not result:
            raise HTTPException(status_code=404, detail="Webhook delivery result not found")
        
        return NotificationResponse(
            success=result.success,
            message_id=result.message_id,
            status=result.status.value,
            sent_at=result.sent_at,
            delivered_at=result.delivered_at,
            error_message=result.error_message,
            metadata=result.metadata
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get webhook notification failed: {e}")
        raise HTTPException(status_code=500, detail=f"Get webhook notification failed: {str(e)}")

@app.get("/notifications/webhook/statistics", response_model=NotificationStatistics)
async def get_webhook_statistics(user: User = Depends(get_current_user)):
    """Get webhook statistics."""
    try:
        stats = webhook_service.get_webhook_statistics()
        
        return NotificationStatistics(
            total_notifications=stats["total_webhooks"],
            successful_notifications=stats["successful_webhooks"],
            failed_notifications=stats["failed_webhooks"],
            channel_usage=stats["method_usage"],
            priority_usage={},
            average_delivery_time=stats["average_delivery_time"]
        )
    except Exception as e:
        logger.error(f"Get webhook statistics failed: {e}")
        raise HTTPException(status_code=500, detail=f"Get webhook statistics failed: {str(e)}")

# Unified notification endpoints

@app.post("/notifications/unified", response_model=List[NotificationResponse])
async def send_unified_notification(request: UnifiedNotificationRequest, user: User = Depends(get_current_user)):
    """Send unified notification to multiple channels."""
    try:
        # Create unified notification
        notification = unified_system.create_notification(
            title=request.title,
            message=request.message,
            channels=[NotificationChannel(channel.value) for channel in request.channels],
            priority=NotificationPriority(request.priority.value),
            template_data=request.template_data or {}
        )
        
        # Send notification
        results = await unified_system.send_notification(notification.notification_id)
        
        # Convert results to response format
        response_results = []
        for result in results:
            response_results.append(NotificationResponse(
                success=result.success,
                message_id=result.message_id,
                status=result.status.value,
                sent_at=result.sent_at,
                delivered_at=result.delivered_at,
                error_message=result.error_message,
                metadata=result.metadata
            ))
        
        return response_results
    except Exception as e:
        logger.error(f"Unified notification failed: {e}")
        raise HTTPException(status_code=500, detail=f"Unified notification failed: {str(e)}")

@app.get("/notifications/unified/statistics", response_model=NotificationStatistics)
async def get_unified_statistics(user: User = Depends(get_current_user)):
    """Get unified notification statistics."""
    try:
        stats = unified_system.get_statistics()
        
        return NotificationStatistics(
            total_notifications=stats["total_notifications"],
            successful_notifications=stats["successful_notifications"],
            failed_notifications=stats["failed_notifications"],
            channel_usage=stats["channel_usage"],
            priority_usage=stats["priority_usage"],
            average_delivery_time=0.0  # Unified system doesn't track this
        )
    except Exception as e:
        logger.error(f"Get unified statistics failed: {e}")
        raise HTTPException(status_code=500, detail=f"Get unified statistics failed: {str(e)}")

# Template management endpoints

@app.post("/templates/email")
async def endpoint_name(request: Request, user: User = Depends(get_current_user)):
async def create_email_template(
    template_id: str,
    name: str,
    subject_template: str,
    body_template: str,
    html_template: Optional[str] = None,
    variables: Optional[List[str]] = None
, user: User = Depends(get_current_user)):
    """Create email template."""
    try:
        email_service.create_template(
            template_id=template_id,
            name=name,
            subject_template=subject_template,
            body_template=body_template,
            html_template=html_template,
            variables=variables
        )
        
        return {"success": True, "message": "Email template created successfully"}
    except Exception as e:
        logger.error(f"Create email template failed: {e}")
        raise HTTPException(status_code=500, detail=f"Create email template failed: {str(e)}")

@app.get("/templates/email/{template_id}")
async def endpoint_name(request: Request, user: User = Depends(get_current_user)):
async def get_email_template(template_id: str, user: User = Depends(get_current_user)):
    """Get email template."""
    try:
        template = email_service.get_template(template_id)
        if not template:
            raise HTTPException(status_code=404, detail="Email template not found")
        
        return {
            "template_id": template.template_id,
            "name": template.name,
            "subject_template": template.subject_template,
            "body_template": template.body_template,
            "html_template": template.html_template,
            "variables": template.variables,
            "created_at": template.created_at.isoformat(),
            "updated_at": template.updated_at.isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get email template failed: {e}")
        raise HTTPException(status_code=500, detail=f"Get email template failed: {str(e)}")

# Service information endpoints

@app.get("/services/email/supported-priorities")
async def endpoint_name(request: Request, user: User = Depends(get_current_user)):
async def get_supported_email_priorities(user: User = Depends(get_current_user)):
    """Get supported email priorities."""
    try:
        priorities = email_service.get_supported_priorities()
        return {"priorities": [p.value for p in priorities]}
    except Exception as e:
        logger.error(f"Get supported email priorities failed: {e}")
        raise HTTPException(status_code=500, detail=f"Get supported email priorities failed: {str(e)}")

@app.get("/services/slack/supported-message-types")
async def endpoint_name(request: Request, user: User = Depends(get_current_user)):
async def get_supported_slack_message_types(user: User = Depends(get_current_user)):
    """Get supported Slack message types."""
    try:
        message_types = slack_service.get_supported_message_types()
        return {"message_types": [mt.value for mt in message_types]}
    except Exception as e:
        logger.error(f"Get supported Slack message types failed: {e}")
        raise HTTPException(status_code=500, detail=f"Get supported Slack message types failed: {str(e)}")

@app.get("/services/sms/supported-providers")
async def endpoint_name(request: Request, user: User = Depends(get_current_user)):
async def get_supported_sms_providers(user: User = Depends(get_current_user)):
    """Get supported SMS providers."""
    try:
        providers = sms_service.get_supported_providers()
        return {"providers": [p.value for p in providers]}
    except Exception as e:
        logger.error(f"Get supported SMS providers failed: {e}")
        raise HTTPException(status_code=500, detail=f"Get supported SMS providers failed: {str(e)}")

@app.get("/services/webhook/supported-methods")
async def endpoint_name(request: Request, user: User = Depends(get_current_user)):
async def get_supported_webhook_methods(user: User = Depends(get_current_user)):
    """Get supported webhook HTTP methods."""
    try:
        methods = webhook_service.get_supported_methods()
        return {"methods": [m.value for m in methods]}
    except Exception as e:
        logger.error(f"Get supported webhook methods failed: {e}")
        raise HTTPException(status_code=500, detail=f"Get supported webhook methods failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8083) 