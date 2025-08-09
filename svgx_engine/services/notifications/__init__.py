"""
SVGX Engine - Notifications Module

This module provides comprehensive notification functionality including email, Slack, SMS,
and webhook notifications for enterprise-grade alerting and communication.

Now integrates with Go notification API for enhanced performance and reliability.

Author: Arxos Engineering Team
Date: 2024-12-19
Version: 2.0.0
"""

# Import Go notification client (primary interface)
from .go_client import (
    GoNotificationClient,
    GoNotificationWrapper,
    NotificationRequest,
    NotificationResponse,
    NotificationHistoryRequest,
    NotificationStatistics,
    NotificationChannelType,
    NotificationPriority,
    NotificationType,
    NotificationStatus,
    create_go_notification_client,
    create_go_notification_wrapper
)

# Import optimized client and monitoring
try:
    from .go_client_optimized import (
        OptimizedGoNotificationClient,
        ConnectionPool,
        RateLimiter,
        CacheEntry,
        BackgroundJobProcessor,
        create_optimized_go_notification_client
    )
except ImportError:
    OptimizedGoNotificationClient = None
    ConnectionPool = None
    RateLimiter = None
    CacheEntry = None
    BackgroundJobProcessor = None
    create_optimized_go_notification_client = None

try:
    from .monitoring import (
        NotificationMonitoring,
        StructuredLogger,
        PrometheusMetrics,
        HealthChecker,
        AlertManager,
        NotificationDashboard,
        AlertEvent,
        AlertSeverity,
        ChannelHealth,
        NotificationMetrics,
        create_notification_monitoring,
        create_structured_logger
    )
except ImportError:
    NotificationMonitoring = None
    StructuredLogger = None
    PrometheusMetrics = None
    HealthChecker = None
    AlertManager = None
    NotificationDashboard = None
    AlertEvent = None
    AlertSeverity = None
    ChannelHealth = None
    NotificationMetrics = None
    create_notification_monitoring = None
    create_structured_logger = None

__all__ = [
    # Go notification client (primary interface)
    'GoNotificationClient',
    'GoNotificationWrapper',
    'NotificationRequest',
    'NotificationResponse',
    'NotificationHistoryRequest',
    'NotificationStatistics',
    'NotificationChannelType',
    'NotificationPriority',
    'NotificationType',
    'NotificationStatus',
    'create_go_notification_client',
    'create_go_notification_wrapper',

    # Optimized client and components
    'OptimizedGoNotificationClient',
    'ConnectionPool',
    'RateLimiter',
    'CacheEntry',
    'BackgroundJobProcessor',
    'create_optimized_go_notification_client',

    # Monitoring and observability
    'NotificationMonitoring',
    'StructuredLogger',
    'PrometheusMetrics',
    'HealthChecker',
    'AlertManager',
    'NotificationDashboard',
    'AlertEvent',
    'AlertSeverity',
    'ChannelHealth',
    'NotificationMetrics',
    'create_notification_monitoring',
    'create_structured_logger'
]
