"""
Domain Services - Business Logic Services

This module contains domain services that implement business logic
that doesn't belong to entities. Domain services coordinate between
entities and implement complex business rules.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import math

from .entities import Building, Floor, Room, Device, User, Project
from .value_objects import (
    BuildingId, FloorId, RoomId, DeviceId, UserId, ProjectId,
    BuildingStatus, FloorStatus, RoomStatus, DeviceStatus, UserRole, ProjectStatus,
    Address, Coordinates, Dimensions
)
from .repositories import (
    BuildingRepository, FloorRepository, RoomRepository, DeviceRepository,
    UserRepository, ProjectRepository, UnitOfWork
)
from .exceptions import (
    DomainServiceError, BuildingNotFoundError, FloorNotFoundError,
    RoomNotFoundError, DeviceNotFoundError, UserNotFoundError, ProjectNotFoundError,
    InvalidStatusTransitionError, BusinessRuleViolationError
)


class BuildingDomainService:
    """Domain service for building-related business logic."""
    
    def __init__(self, building_repository: BuildingRepository):
        self.building_repository = building_repository
    
    def create_building(
        self,
        name: str,
        address: Address,
        created_by: str,
        coordinates: Optional[Coordinates] = None,
        dimensions: Optional[Dimensions] = None,
        description: Optional[str] = None
    ) -> Building:
        """Create a new building with validation."""
        # Business rule: Check if building already exists at this address
        existing_buildings = self.building_repository.get_by_address(str(address))
        if existing_buildings:
            raise BusinessRuleViolationError(
                f"Building already exists at address: {address.full_address}"
            )
        
        building = Building(
            id=BuildingId(),
            name=name,
            address=address,
            coordinates=coordinates,
            dimensions=dimensions,
            description=description,
            created_by=created_by
        )
        
        self.building_repository.save(building)
        return building
    
    def update_building_status(
        self,
        building_id: BuildingId,
        new_status: BuildingStatus,
        updated_by: str
    ) -> Building:
        """Update building status with business rules."""
        building = self.building_repository.get_by_id(building_id)
        if not building:
            raise BuildingNotFoundError(f"Building with ID {building_id} not found")
        
        building.update_status(new_status, updated_by)
        self.building_repository.save(building)
        return building
    
    def get_building_statistics(self, building_id: BuildingId) -> Dict[str, Any]:
        """Get comprehensive building statistics."""
        building = self.building_repository.get_with_floors(building_id)
        if not building:
            raise BuildingNotFoundError(f"Building with ID {building_id} not found")
        
        total_rooms = sum(len(floor.rooms) for floor in building.floors)
        total_devices = sum(
            len(room.devices) 
            for floor in building.floors 
            for room in floor.rooms
        )
        
        # Calculate occupancy rates
        operational_rooms = sum(
            len([r for r in floor.rooms if r.status == RoomStatus.OPERATIONAL])
            for floor in building.floors
        )
        occupied_rooms = sum(
            len([r for r in floor.rooms if r.status == RoomStatus.OCCUPIED])
            for floor in building.floors
        )
        
        occupancy_rate = (occupied_rooms / total_rooms * 100) if total_rooms > 0 else 0
        
        # Calculate device health
        operational_devices = sum(
            len([d for d in room.devices if d.status == DeviceStatus.OPERATIONAL])
            for floor in building.floors
            for room in floor.rooms
        )
        
        device_health_rate = (operational_devices / total_devices * 100) if total_devices > 0 else 0
        
        return {
            "building_id": str(building_id),
            "building_name": building.name,
            "total_floors": building.floor_count,
            "total_rooms": total_rooms,
            "total_devices": total_devices,
            "operational_rooms": operational_rooms,
            "occupied_rooms": occupied_rooms,
            "occupancy_rate": round(occupancy_rate, 2),
            "operational_devices": operational_devices,
            "device_health_rate": round(device_health_rate, 2),
            "building_area": building.area,
            "building_volume": building.volume,
            "status": building.status.value
        }
    
    def calculate_building_efficiency(self, building_id: BuildingId) -> Dict[str, float]:
        """Calculate building efficiency metrics."""
        building = self.building_repository.get_with_floors(building_id)
        if not building:
            raise BuildingNotFoundError(f"Building with ID {building_id} not found")
        
        total_area = building.area or 0
        total_rooms = sum(len(floor.rooms) for floor in building.floors)
        
        if total_area == 0 or total_rooms == 0:
            return {
                "space_utilization": 0.0,
                "room_density": 0.0,
                "device_density": 0.0
            }
        
        # Space utilization (rooms per square meter)
        space_utilization = total_rooms / total_area if total_area > 0 else 0
        
        # Room density (rooms per floor)
        room_density = total_rooms / building.floor_count if building.floor_count > 0 else 0
        
        # Device density (devices per room)
        total_devices = sum(
            len(room.devices) 
            for floor in building.floors 
            for room in floor.rooms
        )
        device_density = total_devices / total_rooms if total_rooms > 0 else 0
        
        return {
            "space_utilization": round(space_utilization, 4),
            "room_density": round(room_density, 2),
            "device_density": round(device_density, 2)
        }


class FloorDomainService:
    """Domain service for floor-related business logic."""
    
    def __init__(self, floor_repository: FloorRepository):
        self.floor_repository = floor_repository
    
    def create_floor(
        self,
        building_id: BuildingId,
        floor_number: int,
        name: str,
        created_by: str,
        description: Optional[str] = None
    ) -> Floor:
        """Create a new floor with validation."""
        # Business rule: Check if floor number already exists
        existing_floor = self.floor_repository.get_by_building_and_number(building_id, floor_number)
        if existing_floor:
            raise BusinessRuleViolationError(
                f"Floor {floor_number} already exists in building {building_id}"
            )
        
        floor = Floor(
            id=FloorId(),
            building_id=building_id,
            floor_number=floor_number,
            name=name,
            description=description,
            created_by=created_by
        )
        
        self.floor_repository.save(floor)
        return floor
    
    def get_floor_statistics(self, floor_id: FloorId) -> Dict[str, Any]:
        """Get comprehensive floor statistics."""
        floor = self.floor_repository.get_by_id(floor_id)
        if not floor:
            raise FloorNotFoundError(f"Floor with ID {floor_id} not found")
        
        total_rooms = len(floor.rooms)
        total_devices = sum(len(room.devices) for room in floor.rooms)
        
        # Room type distribution
        room_types = {}
        for room in floor.rooms:
            room_type = room.room_type
            room_types[room_type] = room_types.get(room_type, 0) + 1
        
        # Device type distribution
        device_types = {}
        for room in floor.rooms:
            for device in room.devices:
                device_type = device.device_type
                device_types[device_type] = device_types.get(device_type, 0) + 1
        
        return {
            "floor_id": str(floor_id),
            "floor_name": floor.name,
            "floor_number": floor.floor_number,
            "total_rooms": total_rooms,
            "total_devices": total_devices,
            "room_types": room_types,
            "device_types": device_types,
            "status": floor.status.value
        }


class RoomDomainService:
    """Domain service for room-related business logic."""
    
    def __init__(self, room_repository: RoomRepository):
        self.room_repository = room_repository
    
    def create_room(
        self,
        floor_id: FloorId,
        room_number: str,
        name: str,
        room_type: str,
        created_by: str,
        dimensions: Optional[Dimensions] = None,
        description: Optional[str] = None
    ) -> Room:
        """Create a new room with validation."""
        # Business rule: Check if room number already exists on this floor
        existing_room = self.room_repository.get_by_floor_and_number(floor_id, room_number)
        if existing_room:
            raise BusinessRuleViolationError(
                f"Room {room_number} already exists on floor {floor_id}"
            )
        
        room = Room(
            id=RoomId(),
            floor_id=floor_id,
            room_number=room_number,
            name=name,
            room_type=room_type,
            dimensions=dimensions,
            description=description,
            created_by=created_by
        )
        
        self.room_repository.save(room)
        return room
    
    def get_room_statistics(self, room_id: RoomId) -> Dict[str, Any]:
        """Get comprehensive room statistics."""
        room = self.room_repository.get_by_id(room_id)
        if not room:
            raise RoomNotFoundError(f"Room with ID {room_id} not found")
        
        total_devices = len(room.devices)
        
        # Device status distribution
        device_statuses = {}
        for device in room.devices:
            status = device.status.value
            device_statuses[status] = device_statuses.get(status, 0) + 1
        
        # Device type distribution
        device_types = {}
        for device in room.devices:
            device_type = device.device_type
            device_types[device_type] = device_types.get(device_type, 0) + 1
        
        return {
            "room_id": str(room_id),
            "room_name": room.name,
            "room_number": room.room_number,
            "room_type": room.room_type,
            "total_devices": total_devices,
            "device_statuses": device_statuses,
            "device_types": device_types,
            "area": room.area,
            "volume": room.volume,
            "status": room.status.value
        }
    
    def calculate_room_efficiency(self, room_id: RoomId) -> Dict[str, float]:
        """Calculate room efficiency metrics."""
        room = self.room_repository.get_by_id(room_id)
        if not room:
            raise RoomNotFoundError(f"Room with ID {room_id} not found")
        
        area = room.area or 0
        device_count = len(room.devices)
        
        if area == 0:
            return {
                "device_density": 0.0,
                "space_utilization": 0.0
            }
        
        # Device density (devices per square meter)
        device_density = device_count / area if area > 0 else 0
        
        # Space utilization (based on room type and device count)
        # This is a simplified calculation - in practice, this would be more complex
        space_utilization = min(device_density * 10, 100)  # Arbitrary scaling
        
        return {
            "device_density": round(device_density, 4),
            "space_utilization": round(space_utilization, 2)
        }


class DeviceDomainService:
    """Domain service for device-related business logic."""
    
    def __init__(self, device_repository: DeviceRepository):
        self.device_repository = device_repository
    
    def create_device(
        self,
        room_id: RoomId,
        device_id: str,
        device_type: str,
        name: str,
        created_by: str,
        manufacturer: Optional[str] = None,
        model: Optional[str] = None,
        serial_number: Optional[str] = None,
        description: Optional[str] = None
    ) -> Device:
        """Create a new device with validation."""
        # Business rule: Check if device ID already exists
        existing_devices = self.device_repository.get_by_type(device_type)
        for device in existing_devices:
            if device.device_id == device_id:
                raise BusinessRuleViolationError(
                    f"Device with ID {device_id} already exists"
                )
        
        device = Device(
            id=DeviceId(),
            room_id=room_id,
            device_id=device_id,
            device_type=device_type,
            name=name,
            manufacturer=manufacturer,
            model=model,
            serial_number=serial_number,
            description=description,
            created_by=created_by
        )
        
        self.device_repository.save(device)
        return device
    
    def get_device_statistics(self, device_id: DeviceId) -> Dict[str, Any]:
        """Get comprehensive device statistics."""
        device = self.device_repository.get_by_id(device_id)
        if not device:
            raise DeviceNotFoundError(f"Device with ID {device_id} not found")
        
        # Calculate device age
        device_age = (datetime.utcnow() - device.created_at).days
        
        return {
            "device_id": str(device_id),
            "device_name": device.name,
            "device_type": device.device_type,
            "manufacturer": device.manufacturer,
            "model": device.model,
            "serial_number": device.serial_number,
            "status": device.status.value,
            "device_age_days": device_age,
            "created_by": device.created_by
        }
    
    def get_devices_by_status(self, status: DeviceStatus) -> List[Device]:
        """Get all devices with a specific status."""
        return self.device_repository.get_by_status(status)
    
    def get_device_health_summary(self) -> Dict[str, Any]:
        """Get overall device health summary."""
        all_devices = self.device_repository.get_all()
        
        total_devices = len(all_devices)
        if total_devices == 0:
            return {
                "total_devices": 0,
                "operational_devices": 0,
                "maintenance_devices": 0,
                "offline_devices": 0,
                "error_devices": 0,
                "health_rate": 0.0
            }
        
        status_counts = {}
        for device in all_devices:
            status = device.status.value
            status_counts[status] = status_counts.get(status, 0) + 1
        
        operational_count = status_counts.get(DeviceStatus.OPERATIONAL.value, 0)
        health_rate = (operational_count / total_devices) * 100
        
        return {
            "total_devices": total_devices,
            "operational_devices": operational_count,
            "maintenance_devices": status_counts.get(DeviceStatus.MAINTENANCE.value, 0),
            "offline_devices": status_counts.get(DeviceStatus.OFFLINE.value, 0),
            "error_devices": status_counts.get(DeviceStatus.ERROR.value, 0),
            "health_rate": round(health_rate, 2)
        }


class UserDomainService:
    """Domain service for user-related business logic."""
    
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository
    
    def create_user(
        self,
        email: str,
        username: str,
        created_by: str,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        phone_number: Optional[str] = None,
        role: UserRole = UserRole.VIEWER
    ) -> User:
        """Create a new user with validation."""
        from .value_objects import Email, PhoneNumber
        
        # Business rule: Check if email already exists
        if self.user_repository.exists_by_email(email):
            raise BusinessRuleViolationError(f"User with email {email} already exists")
        
        # Business rule: Check if username already exists
        existing_users = self.user_repository.get_all()
        for user in existing_users:
            if user.username == username:
                raise BusinessRuleViolationError(f"Username {username} already exists")
        
        user = User(
            id=UserId(),
            email=Email(email),
            username=username,
            role=role,
            first_name=first_name,
            last_name=last_name,
            phone_number=PhoneNumber(phone_number) if phone_number else None,
            created_by=created_by
        )
        
        self.user_repository.save(user)
        return user
    
    def get_user_statistics(self) -> Dict[str, Any]:
        """Get comprehensive user statistics."""
        all_users = self.user_repository.get_all()
        active_users = self.user_repository.get_active_users()
        
        # Role distribution
        role_counts = {}
        for user in all_users:
            role = user.role.value
            role_counts[role] = role_counts.get(role, 0) + 1
        
        # Active vs inactive users
        active_count = len(active_users)
        inactive_count = len(all_users) - active_count
        
        return {
            "total_users": len(all_users),
            "active_users": active_count,
            "inactive_users": inactive_count,
            "role_distribution": role_counts,
            "activation_rate": round((active_count / len(all_users)) * 100, 2) if all_users else 0
        }
    
    def get_users_by_role(self, role: UserRole) -> List[User]:
        """Get all users with a specific role."""
        return self.user_repository.get_by_role(role)


class ProjectDomainService:
    """Domain service for project-related business logic."""
    
    def __init__(self, project_repository: ProjectRepository):
        self.project_repository = project_repository
    
    def create_project(
        self,
        name: str,
        building_id: BuildingId,
        created_by: str,
        description: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Project:
        """Create a new project with validation."""
        # Business rule: Check if project name already exists for this building
        existing_projects = self.project_repository.get_by_building_id(building_id)
        for project in existing_projects:
            if project.name == name:
                raise BusinessRuleViolationError(
                    f"Project with name '{name}' already exists for building {building_id}"
                )
        
        project = Project(
            id=ProjectId(),
            name=name,
            building_id=building_id,
            description=description,
            start_date=start_date,
            end_date=end_date,
            created_by=created_by
        )
        
        self.project_repository.save(project)
        return project
    
    def get_project_statistics(self, project_id: ProjectId) -> Dict[str, Any]:
        """Get comprehensive project statistics."""
        project = self.project_repository.get_by_id(project_id)
        if not project:
            raise ProjectNotFoundError(f"Project with ID {project_id} not found")
        
        # Calculate project progress
        total_days = project.duration_days or 0
        if project.start_date and project.end_date:
            elapsed_days = (datetime.utcnow() - project.start_date).days
            progress_percentage = min((elapsed_days / total_days) * 100, 100) if total_days > 0 else 0
        else:
            progress_percentage = 0
        
        return {
            "project_id": str(project_id),
            "project_name": project.name,
            "status": project.status.value,
            "start_date": project.start_date.isoformat() if project.start_date else None,
            "end_date": project.end_date.isoformat() if project.end_date else None,
            "duration_days": total_days,
            "progress_percentage": round(progress_percentage, 2),
            "created_by": project.created_by
        }
    
    def get_projects_by_status(self, status: ProjectStatus) -> List[Project]:
        """Get all projects with a specific status."""
        return self.project_repository.get_by_status(status)
    
    def get_project_summary(self) -> Dict[str, Any]:
        """Get overall project summary."""
        all_projects = self.project_repository.get_all()
        
        # Status distribution
        status_counts = {}
        for project in all_projects:
            status = project.status.value
            status_counts[status] = status_counts.get(status, 0) + 1
        
        # Calculate average project duration
        total_duration = 0
        projects_with_duration = 0
        for project in all_projects:
            if project.duration_days:
                total_duration += project.duration_days
                projects_with_duration += 1
        
        avg_duration = total_duration / projects_with_duration if projects_with_duration > 0 else 0
        
        return {
            "total_projects": len(all_projects),
            "status_distribution": status_counts,
            "average_duration_days": round(avg_duration, 1)
        } 