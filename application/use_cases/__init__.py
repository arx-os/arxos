"""
Use Cases - Application Layer Business Logic

This module contains use cases that implement the application's business
logic by orchestrating domain objects and infrastructure services.
Use cases represent the application's use cases and business workflows.
"""

from .building_use_cases import *
from .building_hierarchy_use_cases import *
from .floor_use_cases import *
from .room_use_cases import *
from .device_use_cases import *
from .user_use_cases import *
from .project_use_cases import *

__all__ = [
    # Building Use Cases
    "CreateBuildingUseCase",
    "UpdateBuildingUseCase",
    "GetBuildingUseCase",
    "ListBuildingsUseCase",
    "DeleteBuildingUseCase",
    # Building Hierarchy Use Cases (Complex Business Logic)
    "CreateBuildingWithFloorsUseCase",
    "GetBuildingHierarchyUseCase",
    "AddRoomToFloorUseCase",
    "UpdateBuildingStatusUseCase",
    "GetBuildingStatisticsUseCase",
    # Floor Use Cases
    "CreateFloorUseCase",
    "UpdateFloorUseCase",
    "GetFloorUseCase",
    "ListFloorsUseCase",
    "DeleteFloorUseCase",
    # Room Use Cases
    "CreateRoomUseCase",
    "UpdateRoomUseCase",
    "GetRoomUseCase",
    "ListRoomsUseCase",
    "DeleteRoomUseCase",
    # Device Use Cases
    "CreateDeviceUseCase",
    "UpdateDeviceUseCase",
    "GetDeviceUseCase",
    "ListDevicesUseCase",
    "DeleteDeviceUseCase",
    # User Use Cases
    "CreateUserUseCase",
    "UpdateUserUseCase",
    "GetUserUseCase",
    "ListUsersUseCase",
    "DeleteUserUseCase",
    # Project Use Cases
    "CreateProjectUseCase",
    "UpdateProjectUseCase",
    "GetProjectUseCase",
    "ListProjectsUseCase",
    "DeleteProjectUseCase",
]
