"""
Unified Controller Exceptions

Defines minimal exception types used by unified controllers and base controller.
"""


class ControllerError(Exception):
    """Base controller error."""


class ValidationError(ControllerError):
    """Validation failure for controller inputs."""


class NotFoundError(ControllerError):
    """Entity not found error."""
