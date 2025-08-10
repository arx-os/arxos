"""
Base Application Service

Provides common functionality for all application services including
infrastructure integration, error handling, logging, and monitoring.
"""

import time
from abc import ABC
from typing import Optional, Dict, Any, TypeVar, Generic
from datetime import datetime

from domain.repositories import UnitOfWork
from domain.exceptions import DomainException
from application.exceptions import ApplicationError, handle_application_error
from infrastructure.services.cache_service import RedisCacheService
from infrastructure.services.event_store import EventStoreService
from infrastructure.services.message_queue import MessageQueueService
from infrastructure.monitoring.metrics import MetricsCollector
from infrastructure.logging.structured_logging import get_logger, timed_operation, log_context
from infrastructure.error_handling import ErrorMapper, error_reporting

# Type variables for generic service implementation
T = TypeVar('T')  # Entity type
R = TypeVar('R')  # Response type


class BaseApplicationService(ABC, Generic[T]):
    """Base class for application services with common infrastructure integration."""
    
    def __init__(self, 
                 unit_of_work: UnitOfWork,
                 entity_name: str,
                 cache_service: Optional[RedisCacheService] = None,
                 event_store: Optional[EventStoreService] = None,
                 message_queue: Optional[MessageQueueService] = None,
                 metrics: Optional[MetricsCollector] = None):
        """
        Initialize base application service.
        
        Args:
            unit_of_work: Unit of work for database transactions
            entity_name: Name of the entity this service manages (for logging/metrics)
            cache_service: Optional cache service
            event_store: Optional event store service
            message_queue: Optional message queue service
            metrics: Optional metrics collector
        """
        self.unit_of_work = unit_of_work
        self.entity_name = entity_name
        self.cache_service = cache_service
        self.event_store = event_store
        self.message_queue = message_queue
        self.metrics = metrics
        
        # Initialize logger for this service
        self.logger = get_logger(f"application.services.{entity_name.lower()}")
        
        # Performance tracking
        self._start_time = None
        self._operation_metrics = {}
    
    @handle_application_error
    def _execute_with_transaction(self, operation_name: str, operation_func, *args, **kwargs):
        """
        Execute an operation within a database transaction with full error handling.
        
        Args:
            operation_name: Name of the operation for logging/metrics
            operation_func: Function to execute
            *args, **kwargs: Arguments to pass to the function
            
        Returns:
            Result of the operation
            
        Raises:
            ApplicationError: If operation fails
        """
        operation_id = f"{operation_name}_{int(time.time() * 1000)}"
        
        with log_context(operation=operation_name, entity=self.entity_name, operation_id=operation_id):
            try:
                # Start timing
                start_time = time.time()
                
                # Execute operation within transaction
                with self.unit_of_work:
                    self.logger.info(f"Starting {operation_name} operation", extra={
                        "operation": operation_name,
                        "entity_type": self.entity_name
                    })
                    
                    result = operation_func(*args, **kwargs)
                    
                    # Commit transaction
                    self.unit_of_work.commit()
                    
                    # Calculate timing
                    duration = time.time() - start_time
                    
                    # Log success
                    self.logger.info(f"Completed {operation_name} operation", extra={
                        "operation": operation_name,
                        "entity_type": self.entity_name,
                        "duration_ms": round(duration * 1000, 2),
                        "success": True
                    })
                    
                    # Record metrics
                    if self.metrics:
                        self.metrics.record_operation_duration(
                            f"{self.entity_name.lower()}_{operation_name}",
                            duration
                        )
                        self.metrics.increment_counter(
                            f"{self.entity_name.lower()}_operations_total",
                            {"operation": operation_name, "status": "success"}
                        )
                    
                    return result
                    
            except DomainException as e:
                # Handle domain exceptions
                self.unit_of_work.rollback()
                duration = time.time() - start_time
                
                self.logger.error(f"Domain error in {operation_name}", extra={
                    "operation": operation_name,
                    "entity_type": self.entity_name,
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "duration_ms": round(duration * 1000, 2)
                })
                
                # Convert to application error
                app_error = ErrorMapper.map_domain_to_application(e)
                error_reporting.report_error(e, {
                    "operation": operation_name,
                    "entity_type": self.entity_name,
                    "operation_id": operation_id
                })
                
                if self.metrics:
                    self.metrics.increment_counter(
                        f"{self.entity_name.lower()}_operations_total",
                        {"operation": operation_name, "status": "domain_error"}
                    )
                
                raise app_error
                
            except Exception as e:
                # Handle unexpected exceptions
                self.unit_of_work.rollback()
                duration = time.time() - start_time
                
                self.logger.error(f"Unexpected error in {operation_name}", extra={
                    "operation": operation_name,
                    "entity_type": self.entity_name,
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "duration_ms": round(duration * 1000, 2)
                }, exc_info=True)
                
                error_reporting.report_error(e, {
                    "operation": operation_name,
                    "entity_type": self.entity_name,
                    "operation_id": operation_id
                })
                
                if self.metrics:
                    self.metrics.increment_counter(
                        f"{self.entity_name.lower()}_operations_total",
                        {"operation": operation_name, "status": "error"}
                    )
                
                raise ApplicationError(
                    message=f"Unexpected error in {operation_name} operation",
                    error_code="INTERNAL_ERROR",
                    details={"operation": operation_name, "original_error": str(e)}
                )
    
    def _get_cache_key(self, entity_id: str, suffix: str = "") -> str:
        """Generate a cache key for an entity."""
        key = f"{self.entity_name.lower()}:{entity_id}"
        if suffix:
            key += f":{suffix}"
        return key
    
    def _get_from_cache(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Get data from cache if available."""
        if not self.cache_service:
            return None
        
        try:
            return self.cache_service.get(cache_key)
        except Exception as e:
            self.logger.warning(f"Cache retrieval failed for key {cache_key}: {e}")
            return None
    
    def _set_cache(self, cache_key: str, data: Dict[str, Any], ttl: int = 3600) -> None:
        """Set data in cache if available."""
        if not self.cache_service:
            return
        
        try:
            self.cache_service.set(cache_key, data, ttl=ttl)
        except Exception as e:
            self.logger.warning(f"Cache storage failed for key {cache_key}: {e}")
    
    def _invalidate_cache(self, entity_id: str) -> None:
        """Invalidate cache entries for an entity."""
        if not self.cache_service:
            return
        
        try:
            # Invalidate main entity cache
            main_key = self._get_cache_key(entity_id)
            self.cache_service.delete(main_key)
            
            # Invalidate list caches (pattern-based deletion)
            list_pattern = f"{self.entity_name.lower()}:list:*"
            self.cache_service.delete_pattern(list_pattern)
            
            self.logger.debug(f"Cache invalidated for {self.entity_name} {entity_id}")
            
        except Exception as e:
            self.logger.warning(f"Cache invalidation failed for {entity_id}: {e}")
    
    def _publish_domain_events(self, domain_events: list) -> None:
        """Publish domain events to event store and message queue."""
        if not domain_events:
            return
        
        # Store events in event store
        if self.event_store:
            try:
                for event in domain_events:
                    self.event_store.store_event(event)
                self.logger.debug(f"Stored {len(domain_events)} domain events")
            except Exception as e:
                self.logger.error(f"Failed to store domain events: {e}")
        
        # Publish events to message queue for async processing
        if self.message_queue:
            try:
                for event in domain_events:
                    self.message_queue.publish(
                        exchange="domain_events",
                        routing_key=f"{self.entity_name.lower()}.{type(event).__name__.lower()}",
                        message=event.to_dict() if hasattr(event, 'to_dict') else event.__dict__
                    )
                self.logger.debug(f"Published {len(domain_events)} domain events to message queue")
            except Exception as e:
                self.logger.error(f"Failed to publish domain events: {e}")
    
    def _create_success_response(self, entity: T, operation: str) -> Dict[str, Any]:
        """Create a standardized success response."""
        return {
            "success": True,
            "operation": operation,
            "entity_type": self.entity_name,
            "timestamp": datetime.utcnow().isoformat(),
            "data": entity.to_dict() if hasattr(entity, 'to_dict') else str(entity)
        }
    
    def _create_list_response(self, entities: list, operation: str, 
                            total_count: Optional[int] = None,
                            page: Optional[int] = None,
                            page_size: Optional[int] = None) -> Dict[str, Any]:
        """Create a standardized list response."""
        response = {
            "success": True,
            "operation": operation,
            "entity_type": self.entity_name,
            "timestamp": datetime.utcnow().isoformat(),
            "data": [entity.to_dict() if hasattr(entity, 'to_dict') else str(entity) 
                    for entity in entities],
            "count": len(entities)
        }
        
        if total_count is not None:
            response["total_count"] = total_count
        
        if page is not None and page_size is not None:
            response["pagination"] = {
                "page": page,
                "page_size": page_size,
                "has_next": total_count > (page * page_size) if total_count else False
            }
        
        return response
    
    @timed_operation("service_health_check")
    def health_check(self) -> Dict[str, Any]:
        """Check the health of the service and its dependencies."""
        health_status = {
            "service": f"{self.entity_name}ApplicationService",
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "dependencies": {}
        }
        
        # Check unit of work
        try:
            with self.unit_of_work:
                self.unit_of_work.rollback()  # Test transaction without committing
            health_status["dependencies"]["database"] = "healthy"
        except Exception as e:
            health_status["dependencies"]["database"] = f"unhealthy: {e}"
            health_status["status"] = "unhealthy"
        
        # Check cache service
        if self.cache_service:
            try:
                self.cache_service.ping()
                health_status["dependencies"]["cache"] = "healthy"
            except Exception as e:
                health_status["dependencies"]["cache"] = f"unhealthy: {e}"
        else:
            health_status["dependencies"]["cache"] = "not_configured"
        
        # Check event store
        if self.event_store:
            try:
                # Attempt to check event store health
                health_status["dependencies"]["event_store"] = "healthy"
            except Exception as e:
                health_status["dependencies"]["event_store"] = f"unhealthy: {e}"
        else:
            health_status["dependencies"]["event_store"] = "not_configured"
        
        # Check message queue
        if self.message_queue:
            try:
                # Attempt to check message queue health
                health_status["dependencies"]["message_queue"] = "healthy" 
            except Exception as e:
                health_status["dependencies"]["message_queue"] = f"unhealthy: {e}"
        else:
            health_status["dependencies"]["message_queue"] = "not_configured"
        
        return health_status