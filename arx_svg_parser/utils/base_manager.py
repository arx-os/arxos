import structlog

class BaseManager:
    """
    BaseManager provides common functionality for all managers, including logging, context,
    and hooks for metrics, tracing, and transaction management.
    """
    def __init__(self, logger=None, context=None):
        self.logger = logger or structlog.get_logger(self.__class__.__name__)
        self.context = context

    def log_info(self, event, **kwargs):
        """Log info message with structured context."""
        if self.context:
            kwargs.update(self.context)
        self.logger.info(event, **kwargs)

    def log_error(self, event, **kwargs):
        """Log error message with structured context."""
        if self.context:
            kwargs.update(self.context)
        self.logger.error(event, **kwargs)

    def log_debug(self, event, **kwargs):
        """Log debug message with structured context."""
        if self.context:
            kwargs.update(self.context)
        self.logger.debug(event, **kwargs)

    def log_warning(self, event, **kwargs):
        """Log warning message with structured context."""
        if self.context:
            kwargs.update(self.context)
        self.logger.warning(event, **kwargs)

    def with_context(self, context):
        """Add context to the manager."""
        self.context = context
        return self

    def record_metric(self, name, value, labels=None):
        """Hook for recording metrics (override in child if needed)."""
        self.log_debug("metric_recorded", metric_name=name, metric_value=value, labels=labels)

    def start_trace(self, operation):
        """Hook for starting a trace (override in child if needed)."""
        self.log_debug("trace_started", operation=operation)
        return None

    def start_transaction(self, name):
        """Hook for starting a transaction (override in child if needed)."""
        self.log_debug("transaction_started", transaction_name=name)
        return None 