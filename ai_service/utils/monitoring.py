"""
Monitoring utilities for the AI service
"""

from prometheus_client import Counter, Histogram, Gauge
import time


# Define metrics
conversion_counter = Counter(
    'arxos_pdf_conversions_total',
    'Total number of PDF conversions',
    ['building_type', 'status']
)

conversion_duration = Histogram(
    'arxos_pdf_conversion_duration_seconds',
    'Duration of PDF conversions',
    ['building_type']
)

objects_created = Counter(
    'arxos_objects_created_total',
    'Total number of ArxObjects created',
    ['object_type']
)

confidence_gauge = Gauge(
    'arxos_conversion_confidence',
    'Average confidence of conversions',
    ['building_type']
)

active_conversions = Gauge(
    'arxos_active_conversions',
    'Number of active PDF conversions'
)


def setup_monitoring():
    """Initialize monitoring components"""
    # Reset gauges on startup
    active_conversions.set(0)
    print("Monitoring initialized")


def track_conversion(
    building_type: str,
    object_count: int,
    confidence: float,
    processing_time: float
):
    """
    Track metrics for a PDF conversion
    
    Args:
        building_type: Type of building processed
        object_count: Number of objects created
        confidence: Overall confidence score
        processing_time: Time taken to process
    """
    # Increment conversion counter
    conversion_counter.labels(
        building_type=building_type or 'unknown',
        status='success'
    ).inc()
    
    # Record duration
    conversion_duration.labels(
        building_type=building_type or 'unknown'
    ).observe(processing_time)
    
    # Update confidence gauge
    confidence_gauge.labels(
        building_type=building_type or 'unknown'
    ).set(confidence)
    
    # Track objects created (simplified - in production would track by type)
    objects_created.labels(object_type='all').inc(object_count)


def track_validation(
    object_type: str,
    confidence_improvement: float,
    cascaded_count: int
):
    """
    Track metrics for a validation
    
    Args:
        object_type: Type of object validated
        confidence_improvement: Improvement in confidence
        cascaded_count: Number of objects affected
    """
    # Track validation metrics
    # In production, would have specific validation metrics
    pass


class ConversionTimer:
    """Context manager for timing conversions"""
    
    def __init__(self, building_type: str):
        self.building_type = building_type
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        active_conversions.inc()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start_time
        active_conversions.dec()
        
        if exc_type is None:
            # Success
            conversion_duration.labels(
                building_type=self.building_type
            ).observe(duration)
        else:
            # Failure
            conversion_counter.labels(
                building_type=self.building_type,
                status='failure'
            ).inc()