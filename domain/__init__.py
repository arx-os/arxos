"""
Domain Layer - Core Business Logic

This package contains the domain layer of the Clean Architecture implementation.
It includes entities, value objects, domain events, and repository interfaces.

The domain layer is the innermost layer and contains:
- Entities: Core business objects with identity and lifecycle
- Value Objects: Immutable objects that describe domain characteristics
- Domain Events: Events that occur within the domain
- Repository Interfaces: Abstract interfaces for data access
- Domain Services: Business logic that doesn't belong to entities
"""

from .entities import *
from .value_objects import *
from .events import *
from .repositories import *
from .services import *
from .exceptions import *

# PDF Analysis specific imports
from .entities.pdf_analysis import PDFAnalysis
from .value_objects.pdf_analysis_value_objects import (
    TaskId, TaskStatus, ConfidenceScore, FileName, FilePath, 
    AnalysisResult, AnalysisRequirements
)
from .events.pdf_analysis_events import (
    PDFAnalysisCreated, PDFAnalysisStarted, PDFAnalysisCompleted,
    PDFAnalysisFailed, PDFAnalysisCancelled, PDFAnalysisResultGenerated,
    PDFAnalysisExported, PDFAnalysisValidated, PDFAnalysisRequirementsUpdated,
    PDFAnalysisStatusChanged, PDFAnalysisProcessingStarted, PDFAnalysisProcessingProgress,
    PDFAnalysisSymbolRecognized, PDFAnalysisSystemIdentified, PDFAnalysisQualityAssessed,
    PDFAnalysisCostEstimated, PDFAnalysisTimelineGenerated, PDFAnalysisBackupCreated,
    PDFAnalysisRestored, PDFAnalysisArchived, PDFAnalysisShared, PDFAnalysisCommented,
    PDFAnalysisVersionCreated, PDFAnalysisCollaboratorAdded, PDFAnalysisCollaboratorRemoved,
    PDFAnalysisNotificationSent, PDFAnalysisAuditLogCreated
)
from .repositories.pdf_analysis_repository import PDFAnalysisRepository

__all__ = [
    # Entities
    'Building',
    'Floor',
    'Room',
    'Device',
    'User',
    'Project',
    'PDFAnalysis',
    
    # Value Objects
    'BuildingId',
    'FloorId',
    'RoomId',
    'DeviceId',
    'UserId',
    'ProjectId',
    'TaskId',
    'TaskStatus',
    'ConfidenceScore',
    'FileName',
    'FilePath',
    'AnalysisResult',
    'AnalysisRequirements',
    'Address',
    'Coordinates',
    'Dimensions',
    'Email',
    'PhoneNumber',
    'BuildingStatus',
    'FloorStatus',
    'RoomStatus',
    'DeviceStatus',
    'UserRole',
    'ProjectStatus',
    
    # Events
    'DomainEvent',
    'EventType',
    'EventHandler',
    'EventBus',
    'BuildingCreated',
    'BuildingUpdated',
    'BuildingStatusChanged',
    'FloorAdded',
    'FloorUpdated',
    'FloorStatusChanged',
    'RoomAdded',
    'RoomUpdated',
    'RoomStatusChanged',
    'DeviceAdded',
    'DeviceUpdated',
    'DeviceStatusChanged',
    'UserCreated',
    'UserUpdated',
    'UserRoleChanged',
    'ProjectCreated',
    'ProjectUpdated',
    'ProjectStatusChanged',
    'publish_event',
    'subscribe_to_event',
    'unsubscribe_from_event',
    
    # PDF Analysis Events
    'PDFAnalysisCreated',
    'PDFAnalysisStarted',
    'PDFAnalysisCompleted',
    'PDFAnalysisFailed',
    'PDFAnalysisCancelled',
    'PDFAnalysisResultGenerated',
    'PDFAnalysisExported',
    'PDFAnalysisValidated',
    'PDFAnalysisRequirementsUpdated',
    'PDFAnalysisStatusChanged',
    'PDFAnalysisProcessingStarted',
    'PDFAnalysisProcessingProgress',
    'PDFAnalysisSymbolRecognized',
    'PDFAnalysisSystemIdentified',
    'PDFAnalysisQualityAssessed',
    'PDFAnalysisCostEstimated',
    'PDFAnalysisTimelineGenerated',
    'PDFAnalysisBackupCreated',
    'PDFAnalysisRestored',
    'PDFAnalysisArchived',
    'PDFAnalysisShared',
    'PDFAnalysisCommented',
    'PDFAnalysisVersionCreated',
    'PDFAnalysisCollaboratorAdded',
    'PDFAnalysisCollaboratorRemoved',
    'PDFAnalysisNotificationSent',
    'PDFAnalysisAuditLogCreated',
    
    # Repository Interfaces
    'BuildingRepository',
    'FloorRepository',
    'RoomRepository',
    'DeviceRepository',
    'UserRepository',
    'ProjectRepository',
    'PDFAnalysisRepository',
    'UnitOfWork',
    'RepositoryFactory',
    
    # Domain Services
    'BuildingDomainService',
    'FloorDomainService',
    'RoomDomainService',
    'DeviceDomainService',
    'UserDomainService',
    'ProjectDomainService',
    'PDFAnalysisDomainService',
    
    # Exceptions
    'DomainException',
    'InvalidBuildingError',
    'InvalidFloorError',
    'InvalidRoomError',
    'InvalidDeviceError',
    'InvalidUserError',
    'InvalidProjectError',
    'InvalidPDFAnalysisError',
    'InvalidTaskStatusError',
    'InvalidAddressError',
    'InvalidCoordinatesError',
    'InvalidDimensionsError',
    'InvalidEmailError',
    'InvalidPhoneNumberError',
    'DuplicateFloorError',
    'DuplicateRoomError',
    'DuplicateDeviceError',
    'BuildingNotFoundError',
    'FloorNotFoundError',
    'RoomNotFoundError',
    'DeviceNotFoundError',
    'UserNotFoundError',
    'ProjectNotFoundError',
    'InvalidStatusTransitionError',
    'InsufficientPermissionsError',
    'BusinessRuleViolationError',
    'ValidationError',
    'ConcurrencyError',
    'DomainEventError',
    'RepositoryError',
    'RepositoryConnectionError',
    'RepositoryQueryError',
    'RepositoryTransactionError',
    'DomainServiceError',
    'DomainServiceConfigurationError',
    'DomainServiceExecutionError',
    'format_error_message',
    'raise_domain_exception',
] 