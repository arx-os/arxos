import logging

class BaseManager:
    """
    BaseManager provides common functionality for all managers, including logging, context,
    and hooks for metrics, tracing, and transaction management.
    """
    def __init__(self, logger=None, context=None):
        self.logger = logger or logging.getLogger(self.__class__.__name__)
        self.context = context

    def log_info(self, msg, *args):
        self.logger.info(msg, *args)

    def log_error(self, msg, *args):
        self.logger.error(msg, *args)

    def with_context(self, context):
        self.context = context
        return self

    def record_metric(self, name, value, labels=None):
        """Hook for recording metrics (override in child if needed)."""
        pass

    def start_trace(self, operation):
        """Hook for starting a trace (override in child if needed)."""
        return None

    def start_transaction(self, name):
        """Hook for starting a transaction (override in child if needed)."""
        return None 