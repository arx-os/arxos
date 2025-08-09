"""
Building Hierarchy Use Cases - Complex Business Logic

This module contains use cases that demonstrate complex business logic
involving multiple entities and the UnitOfWork pattern for transaction management.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime

from domain.entities import Building, Floor, Room, Device
from domain.repositories import UnitOfWork
from domain.value_objects import (
    BuildingId, FloorId, RoomId, DeviceId,
    Address, BuildingStatus, FloorStatus, RoomStatus, DeviceStatus
)
from domain.exceptions import (
    BuildingNotFoundError, FloorNotFoundError, RoomNotFoundError,
    DeviceNotFoundError, DuplicateFloorError, DuplicateRoomError,
    DuplicateDeviceError, InvalidStatusTransitionError
)
from application.dto.building_dto import (
    CreateBuildingRequest, CreateBuildingResponse,
    GetBuildingResponse, ListBuildingsResponse
)


class CreateBuildingWithFloorsUseCase:
    """Use case for creating a building with multiple floors in a single transaction."""

    def __init__(self, unit_of_work: UnitOfWork):
    """
    Perform __init__ operation

Args:
        unit_of_work: Description of unit_of_work

Returns:
        Description of return value

Raises:
        Exception: Description of exception

Example:
        result = __init__(param)
        print(result)
    """
        self.unit_of_work = unit_of_work

    def execute(self, building_request: CreateBuildingRequest,
                floors_data: List[Dict[str, Any]]) -> CreateBuildingResponse:
        """Execute the create building with floors use case."""
        try:
            # Create building
            building_id = BuildingId()
            address = Address.from_string(building_request.address)

            building = Building(
                id=building_id,
                name=building_request.name.strip(),
                address=address,
                description=building_request.description,
                created_by=building_request.created_by,
                metadata=building_request.metadata or {}
            )

            # Save building
            self.unit_of_work.buildings.save(building)

            # Create floors for the building
            created_floors = []
            for floor_data in floors_data:
                floor = Floor(
                    id=FloorId(),
                    building_id=building.id,
                    floor_number=floor_data['floor_number'],
                    name=floor_data['name'],
                    status=FloorStatus.PLANNED,
                    description=floor_data.get('description'),
                    created_by=building_request.created_by
                )

                self.unit_of_work.floors.save(floor)
                created_floors.append(floor)

            return CreateBuildingResponse(
                success=True,
                building_id=str(building_id),
                message=f"Building created successfully with {len(created_floors)} floors",
                created_at=datetime.utcnow()
        except DuplicateFloorError as e:
            return CreateBuildingResponse(
                success=False,
                error_message=f"Duplicate floor: {str(e)}"
            )
        except Exception as e:
            return CreateBuildingResponse(
                success=False,
                error_message=f"Failed to create building with floors: {str(e)}"
            )


class GetBuildingHierarchyUseCase:
    """
    Perform __init__ operation

Args:
        unit_of_work: Description of unit_of_work

Returns:
        Description of return value

Raises:
        Exception: Description of exception

Example:
        result = __init__(param)
        print(result)
    """
    """Use case for getting a complete building hierarchy (building, floors, rooms, devices)."""

    def __init__(self, unit_of_work: UnitOfWork):
        self.unit_of_work = unit_of_work

    def execute(self, building_id: str) -> GetBuildingResponse:
        """Execute the get building hierarchy use case."""
        try:
            building = self.unit_of_work.buildings.get_by_id(BuildingId(building_id)
            if not building:
                return GetBuildingResponse(
                    success=False,
                    error_message="Building not found"
                )

            # Get floors for the building
            floors = self.unit_of_work.floors.get_by_building_id(building.id)

            # Get rooms and devices for each floor
            floors_data = []
            total_rooms = 0
            total_devices = 0

            for floor in floors:
                rooms = self.unit_of_work.rooms.get_by_floor_id(floor.id)

                rooms_data = []
                floor_device_count = 0

                for room in rooms:
                    devices = self.unit_of_work.devices.get_by_room_id(room.id)

                    devices_data = []
                    for device in devices:
                        devices_data.append({
                            'id': str(device.id),
                            'name': device.name,
                            'device_type': device.device_type,
                            'status': device.status.value,
                            'manufacturer': device.manufacturer,
                            'model': device.model,
                            'serial_number': device.serial_number,
                            'description': device.description
                        })

                    rooms_data.append({
                        'id': str(room.id),
                        'name': room.name,
                        'room_number': room.room_number,
                        'room_type': room.room_type,
                        'status': room.status.value,
                        'description': room.description,
                        'devices': devices_data,
                        'device_count': len(devices)
                    })

                    floor_device_count += len(devices)
                    total_devices += len(devices)

                floors_data.append({
                    'id': str(floor.id),
                    'name': floor.name,
                    'floor_number': floor.floor_number,
                    'status': floor.status.value,
                    'description': floor.description,
                    'rooms': rooms_data,
                    'room_count': len(rooms),
                    'device_count': floor_device_count
                })

                total_rooms += len(rooms)

            # Build complete building hierarchy
            building_data = {
                'id': str(building.id),
                'name': building.name,
                'address': str(building.address),
                'status': building.status.value,
                'description': building.description,
                'created_at': building.created_at.isoformat() if building.created_at else None,
                'updated_at': building.updated_at.isoformat() if building.updated_at else None,
                'created_by': building.created_by,
                'updated_by': building.updated_by,
                'metadata': building.metadata,
                'floors': floors_data,
                'floor_count': len(floors),
                'room_count': total_rooms,
                'device_count': total_devices
            }

            if building.coordinates:
                building_data['coordinates'] = {
                    'latitude': building.coordinates.latitude,
                    'longitude': building.coordinates.longitude
                }

            if building.dimensions:
                building_data['dimensions'] = {
                    'width': building.dimensions.width,
                    'length': building.dimensions.length,
                    'height': building.dimensions.height,
                    'unit': building.dimensions.unit
                }

            return GetBuildingResponse(
                success=True,
                building=building_data
            )

        except Exception as e:
            return GetBuildingResponse(
                success=False,
                error_message=f"Failed to get building hierarchy: {str(e)}"
            )


class AddRoomToFloorUseCase:
    """Use case for adding a room to a floor with devices."""

    def __init__(self, unit_of_work: UnitOfWork):
        self.unit_of_work = unit_of_work

    def execute(self, floor_id: str, room_data: Dict[str, Any],
                devices_data: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute the add room to floor use case."""
        try:
            # Get floor
            floor = self.unit_of_work.floors.get_by_id(FloorId(floor_id)
            if not floor:
                return {
                    'success': False,
                    'error_message': "Floor not found"
                }

            # Create room
            room = Room(
                id=RoomId(),
                floor_id=floor.id,
                room_number=room_data['room_number'],
                name=room_data['name'],
                room_type=room_data.get('room_type', 'general'),
                status=RoomStatus.PLANNED,
                description=room_data.get('description'),
                created_by=room_data.get('created_by', 'system')
            # Save room
            self.unit_of_work.rooms.save(room)

            # Add devices if provided
            created_devices = []
            if devices_data:
                for device_data in devices_data:
                    device = Device(
                        id=DeviceId(),
                        room_id=room.id,
                        device_id=device_data['device_id'],
                        name=device_data['name'],
                        device_type=device_data['device_type'],
                        status=DeviceStatus.INSTALLED,
                        manufacturer=device_data.get('manufacturer'),
                        model=device_data.get('model'),
                        serial_number=device_data.get('serial_number'),
                        description=device_data.get('description'),
                        created_by=room_data.get('created_by', 'system')
                    self.unit_of_work.devices.save(device)
                    created_devices.append(device)

            return {
                'success': True,
                'room_id': str(room.id),
                'room_name': room.name,
                'device_count': len(created_devices),
                'message': f"Room '{room.name}' created successfully with {len(created_devices)} devices"
            }

        except DuplicateRoomError as e:
            return {
                'success': False,
                'error_message': f"Room already exists: {str(e)}"
            }
        except DuplicateDeviceError as e:
            return {
                'success': False,
                'error_message': f"Device already exists: {str(e)}"
            }
        except Exception as e:
            return {
                'success': False,
                'error_message': f"Failed to add room to floor: {str(e)}"
            }


class UpdateBuildingStatusUseCase:
    """Use case for updating building status with cascading updates to floors and rooms."""

    def __init__(self, unit_of_work: UnitOfWork):
        self.unit_of_work = unit_of_work

    def execute(self, building_id: str, new_status: str, updated_by: str) -> Dict[str, Any]:
        """Execute the update building status use case."""
        try:
            # Get building
            building = self.unit_of_work.buildings.get_by_id(BuildingId(building_id)
            if not building:
                return {
                    'success': False,
                    'error_message': "Building not found"
                }

            # Update building status
            try:
                new_building_status = BuildingStatus(new_status)
                building.update_status(new_building_status, updated_by)
                self.unit_of_work.buildings.save(building)
            except ValueError:
                return {
                    'success': False,
                    'error_message': f"Invalid building status: {new_status}"
                }
            except InvalidStatusTransitionError as e:
                return {
                    'success': False,
                    'error_message': f"Invalid status transition: {str(e)}"
                }

            # Get all floors for the building
            floors = self.unit_of_work.floors.get_by_building_id(building.id)

            # Update floor statuses based on building status
            updated_floors = 0
            for floor in floors:
                try:
                    # Map building status to floor status
                    floor_status_mapping = {
                        BuildingStatus.PLANNED: FloorStatus.PLANNED,
                        BuildingStatus.UNDER_CONSTRUCTION: FloorStatus.UNDER_CONSTRUCTION,
                        BuildingStatus.COMPLETED: FloorStatus.COMPLETED,
                        BuildingStatus.OPERATIONAL: FloorStatus.OPERATIONAL,
                        BuildingStatus.MAINTENANCE: FloorStatus.MAINTENANCE,
                        BuildingStatus.DECOMMISSIONED: FloorStatus.MAINTENANCE
                    }

                    new_floor_status = floor_status_mapping.get(new_building_status, FloorStatus.PLANNED)
                    floor.update_status(new_floor_status, updated_by)
                    self.unit_of_work.floors.save(floor)
                    updated_floors += 1

                except InvalidStatusTransitionError:
                    # Skip floors that can't transition to the new status'
                    continue

            # Get all rooms for the building
            rooms = self.unit_of_work.rooms.get_by_building_id(building.id)

            # Update room statuses based on building status
            updated_rooms = 0
            for room in rooms:
                try:
                    # Map building status to room status
                    room_status_mapping = {
                        BuildingStatus.PLANNED: RoomStatus.PLANNED,
                        BuildingStatus.UNDER_CONSTRUCTION: RoomStatus.UNDER_CONSTRUCTION,
                        BuildingStatus.COMPLETED: RoomStatus.COMPLETED,
                        BuildingStatus.OPERATIONAL: RoomStatus.OPERATIONAL,
                        BuildingStatus.MAINTENANCE: RoomStatus.MAINTENANCE,
                        BuildingStatus.DECOMMISSIONED: RoomStatus.MAINTENANCE
                    }

                    new_room_status = room_status_mapping.get(new_building_status, RoomStatus.PLANNED)
                    room.update_status(new_room_status, updated_by)
                    self.unit_of_work.rooms.save(room)
                    updated_rooms += 1

                except InvalidStatusTransitionError:
                    # Skip rooms that can't transition to the new status'
                    continue

            return {
                'success': True,
                'building_id': building_id,
                'new_status': new_status,
                'updated_floors': updated_floors,
                'updated_rooms': updated_rooms,
                'message': f"Building status updated to '{new_status}' with {updated_floors} floors and {updated_rooms} rooms updated"
            }

        except Exception as e:
            return {
                'success': False,
                'error_message': f"Failed to update building status: {str(e)}"
            }


class GetBuildingStatisticsUseCase:
    """Use case for getting comprehensive building statistics."""

    def __init__(self, unit_of_work: UnitOfWork):
        self.unit_of_work = unit_of_work

    def execute(self, building_id: str) -> Dict[str, Any]:
        """Execute the get building statistics use case."""
        try:
            building = self.unit_of_work.buildings.get_by_id(BuildingId(building_id)
            if not building:
                return {
                    'success': False,
                    'error_message': "Building not found"
                }

            # Get floors
            floors = self.unit_of_work.floors.get_by_building_id(building.id)

            # Get rooms
            rooms = self.unit_of_work.rooms.get_by_building_id(building.id)

            # Get devices
            devices = self.unit_of_work.devices.get_by_building_id(building.id)

            # Calculate statistics
            floor_count = len(floors)
            room_count = len(rooms)
            device_count = len(devices)

            # Status breakdowns
            floor_statuses = {}
            room_statuses = {}
            device_statuses = {}

            for floor in floors:
                status = floor.status.value
                floor_statuses[status] = floor_statuses.get(status, 0) + 1

            for room in rooms:
                status = room.status.value
                room_statuses[status] = room_statuses.get(status, 0) + 1

            for device in devices:
                status = device.status.value
                device_statuses[status] = device_statuses.get(status, 0) + 1

            # Device type breakdown
            device_types = {}
            for device in devices:
                device_type = device.device_type
                device_types[device_type] = device_types.get(device_type, 0) + 1

            # Room type breakdown
            room_types = {}
            for room in rooms:
                room_type = room.room_type
                room_types[room_type] = room_types.get(room_type, 0) + 1

            return {
                'success': True,
                'building_id': building_id,
                'building_name': building.name,
                'building_status': building.status.value,
                'statistics': {
                    'total_floors': floor_count,
                    'total_rooms': room_count,
                    'total_devices': device_count,
                    'floor_statuses': floor_statuses,
                    'room_statuses': room_statuses,
                    'device_statuses': device_statuses,
                    'device_types': device_types,
                    'room_types': room_types
                },
                'calculated_at': datetime.utcnow().isoformat()
            }

        except Exception as e:
            return {
                'success': False,
                'error_message': f"Failed to get building statistics: {str(e)}"
            }
