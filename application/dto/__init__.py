"""
Data Transfer Objects (DTOs) - Application Layer Contracts

This module contains DTOs that define the contracts for data transfer
between the application layer and external components (API, UI, etc.).
DTOs are simple data structures without business logic.
"""

from .building_dto import *
from .floor_dto import *
from .room_dto import *
from .device_dto import *
from .user_dto import *
from .project_dto import *

__all__ = [
    # Building DTOs
    "CreateBuildingRequest",
    "CreateBuildingResponse",
    "UpdateBuildingRequest",
    "UpdateBuildingResponse",
    "GetBuildingResponse",
    "ListBuildingsResponse",
    "DeleteBuildingResponse",
    # Floor DTOs
    "CreateFloorRequest",
    "CreateFloorResponse",
    "UpdateFloorRequest",
    "UpdateFloorResponse",
    "GetFloorResponse",
    "ListFloorsResponse",
    "DeleteFloorResponse",
    # Room DTOs
    "CreateRoomRequest",
    "CreateRoomResponse",
    "UpdateRoomRequest",
    "UpdateRoomResponse",
    "GetRoomResponse",
    "ListRoomsResponse",
    "DeleteRoomResponse",
    # Device DTOs
    "CreateDeviceRequest",
    "CreateDeviceResponse",
    "UpdateDeviceRequest",
    "UpdateDeviceResponse",
    "GetDeviceResponse",
    "ListDevicesResponse",
    "DeleteDeviceResponse",
    # User DTOs
    "CreateUserRequest",
    "CreateUserResponse",
    "UpdateUserRequest",
    "UpdateUserResponse",
    "GetUserResponse",
    "ListUsersResponse",
    "DeleteUserResponse",
    # Project DTOs
    "CreateProjectRequest",
    "CreateProjectResponse",
    "UpdateProjectRequest",
    "UpdateProjectResponse",
    "GetProjectResponse",
    "ListProjectsResponse",
    "DeleteProjectResponse",
]
