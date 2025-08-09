"""
Domain Exceptions - Custom Domain-Specific Exceptions

This module contains custom exceptions that represent domain-specific
error conditions. These exceptions help maintain domain integrity and
provide clear error messages for business rule violations.
"""

from typing import Optional, Any


class DomainException(Exception):
    """Base exception for all domain-related errors."""

    def __init__(self, message: str, details: Optional[Any] = None):
        """Initialize the domain exception."

        Args:
            message: Error message
            details: Additional error details

        Returns:
            None

        Raises:
            None
        """
        self.message = message
        self.details = details
        super().__init__(self.message)


class InvalidBuildingError(DomainException):
    """Raised when building data is invalid."""
    pass


class InvalidFloorError(DomainException):
    """Raised when floor data is invalid."""
    pass


class InvalidRoomError(DomainException):
    """Raised when room data is invalid."""
    pass


class InvalidDeviceError(DomainException):
    """Raised when device data is invalid."""
    pass


class InvalidUserError(DomainException):
    """Raised when user data is invalid."""
    pass


class InvalidProjectError(DomainException):
    """Raised when project data is invalid."""
    pass


class DuplicateBuildingError(DomainException):
    """Raised when attempting to add a duplicate building."""
    pass


class DuplicateFloorError(DomainException):
    """Raised when attempting to add a duplicate floor."""
    pass


class DuplicateRoomError(DomainException):
    """Raised when attempting to add a duplicate room."""
    pass


class DuplicateDeviceError(DomainException):
    """Raised when attempting to add a duplicate device."""
    pass


class DuplicateUserError(DomainException):
    """Raised when attempting to add a duplicate user."""
    pass


class DuplicateProjectError(DomainException):
    """Raised when attempting to add a duplicate project."""
    pass


class BuildingNotFoundError(DomainException):
    """Raised when a building is not found."""
    pass


class FloorNotFoundError(DomainException):
    """Raised when a floor is not found."""
    pass


class RoomNotFoundError(DomainException):
    """Raised when a room is not found."""
    pass


class DeviceNotFoundError(DomainException):
    """Raised when a device is not found."""
    pass


class UserNotFoundError(DomainException):
    """Raised when a user is not found."""
    pass


class ProjectNotFoundError(DomainException):
    """Raised when a project is not found."""
    pass


class InvalidAddressError(DomainException):
    """Raised when address data is invalid."""
    pass


class InvalidCoordinatesError(DomainException):
    """Raised when coordinate data is invalid."""
    pass


class InvalidDimensionsError(DomainException):
    """Raised when dimension data is invalid."""
    pass


class InvalidEmailError(DomainException):
    """Raised when email format is invalid."""
    pass


class InvalidPhoneNumberError(DomainException):
    """Raised when phone number format is invalid."""
    pass


class InvalidStatusTransitionError(DomainException):
    """Raised when attempting an invalid status transition."""
    pass


class InsufficientPermissionsError(DomainException):
    """Raised when user lacks required permissions."""
    pass


class BusinessRuleViolationError(DomainException):
    """Raised when a business rule is violated."""
    pass


class ValidationError(DomainException):
    """Raised when data validation fails."""
    pass


class ConcurrencyError(DomainException):
    """Raised when concurrent modification conflicts occur."""
    pass


class DomainEventError(DomainException):
    """Raised when domain event processing fails."""
    pass


class RepositoryError(DomainException):
    """Base exception for repository-related errors."""
    pass


class RepositoryConnectionError(RepositoryError):
    """Raised when repository connection fails."""
    pass


class RepositoryQueryError(RepositoryError):
    """Raised when repository query fails."""
    pass


class RepositoryTransactionError(RepositoryError):
    """Raised when repository transaction fails."""
    pass


class DomainServiceError(DomainException):
    """Base exception for domain service errors."""
    pass


class DomainServiceConfigurationError(DomainServiceError):
    """Raised when domain service configuration is invalid."""
    pass


class DomainServiceExecutionError(DomainServiceError):
    """Raised when domain service execution fails."""
    pass


# Error message constants for consistent messaging
ERROR_MESSAGES = {
    'building_not_found': "Building with ID '{building_id}' not found",
    'floor_not_found': "Floor with ID '{floor_id}' not found in building '{building_id}'",
    'room_not_found': "Room with ID '{room_id}' not found in floor '{floor_id}'",
    'device_not_found': "Device with ID '{device_id}' not found in room '{room_id}'",
    'user_not_found': "User with ID '{user_id}' not found",
    'project_not_found': "Project with ID '{project_id}' not found",
    'duplicate_floor': "Floor '{floor_number}' already exists in building '{building_id}'",
    'duplicate_room': "Room '{room_number}' already exists in floor '{floor_id}'",
    'duplicate_device': "Device '{device_id}' already exists in room '{room_id}'",
    'invalid_building_status': "Invalid building status transition from '{current_status}' to '{new_status}'",
    'invalid_floor_status': "Invalid floor status transition from '{current_status}' to '{new_status}'",
    'invalid_room_status': "Invalid room status transition from '{current_status}' to '{new_status}'",
    'invalid_device_status': "Invalid device status transition from '{current_status}' to '{new_status}'",
    'insufficient_permissions': "User '{user_id}' lacks required permissions for operation '{operation}'",
    'invalid_address': "Invalid address: {reason}",
    'invalid_coordinates': "Invalid coordinates: {reason}",
    'invalid_dimensions': "Invalid dimensions: {reason}",
    'invalid_email': "Invalid email format: '{email}'",
    'invalid_phone': "Invalid phone number format: '{phone}'",
    'business_rule_violation': "Business rule violation: {rule}",
    'validation_error': "Validation error: {field} - {reason}",
    'concurrency_error': "Concurrent modification detected for entity '{entity_type}' with ID '{entity_id}'",
    'domain_event_error': "Domain event processing failed: {event_type}",
    'repository_connection_error': "Repository connection failed: {reason}",
    'repository_query_error': "Repository query failed: {reason}",
    'repository_transaction_error': "Repository transaction failed: {reason}",
    'domain_service_error': "Domain service error: {service} - {reason}",
}


def format_error_message(message_key: str, **kwargs) -> str:
    """Format error message with provided parameters."""
    if message_key not in ERROR_MESSAGES:
        return f"Unknown error: {message_key}"

    try:
        return ERROR_MESSAGES[message_key].format(**kwargs)
    except KeyError as e:
        return f"Error message formatting failed for key '{message_key}': missing parameter {e}"


def raise_domain_exception(exception_class: type, message_key: str, **kwargs) -> None:
    """Raise a domain exception with formatted message."""
    message = format_error_message(message_key, **kwargs)
    raise exception_class(message, details=kwargs)
