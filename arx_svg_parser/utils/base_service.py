class BaseService:
    """
    BaseService provides common functionality for all services, including a reference to the manager
    and hooks for validation, metrics, and tracing.
    """
    def __init__(self, manager=None):
        self.manager = manager

    def validate(self):
        """Override in child for input validation."""
        pass

    def record_service_metric(self, name, value, labels=None):
        """Hook for recording service-level metrics (override in child if needed)."""
        pass

    def start_service_trace(self, operation):
        """Hook for starting a service-level trace (override in child if needed)."""
        return None 