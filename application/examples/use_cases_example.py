"""
Application Use Cases Example

This example demonstrates how to use the application use cases
with the UnitOfWork pattern for transaction management.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from domain.entities import Building, Floor, Room, Device
from domain.value_objects import (
    BuildingId, FloorId, RoomId, DeviceId,
    Address, BuildingStatus, FloorStatus, RoomStatus, DeviceStatus
)
from infrastructure import (
    SQLAlchemyUnitOfWork, SQLAlchemyRepositoryFactory,
    initialize_repository_factory, get_repository_factory
)
from application.use_cases import (
    CreateBuildingUseCase, GetBuildingUseCase, ListBuildingsUseCase,
    CreateBuildingWithFloorsUseCase, GetBuildingHierarchyUseCase,
    AddRoomToFloorUseCase, UpdateBuildingStatusUseCase, GetBuildingStatisticsUseCase
)
from application.dto.building_dto import CreateBuildingRequest


def setup_database():
    """Setup database connection and session factory."""
    # Create engine (using SQLite for this example)
    engine = create_engine('sqlite:///arxos_use_cases.db', echo=True)
    
    # Create session factory
    session_factory = sessionmaker(bind=engine)
    
    # Initialize repository factory
    initialize_repository_factory(session_factory)
    
    return engine, session_factory


def example_basic_use_cases():
    """Example of basic use cases with UnitOfWork."""
    print("=== Basic Use Cases Example ===")
    
    # Get repository factory
    factory = get_repository_factory()
    
    # Create UnitOfWork
    uow = factory.create_unit_of_work()
    
    try:
        with uow:
            # Create use cases with UnitOfWork
            create_building_uc = CreateBuildingUseCase(uow)
            get_building_uc = GetBuildingUseCase(uow)
            list_buildings_uc = ListBuildingsUseCase(uow)
            
            # Create a building
            create_request = CreateBuildingRequest(
                name="Office Building A",
                address="123 Business St, Tech City, CA 12345",
                description="Modern office building with smart systems",
                created_by="system"
            )
            
            create_response = create_building_uc.execute(create_request)
            
            if create_response.success:
                print(f"✅ Building created: {create_response.building_id}")
                
                # Get the building
                get_response = get_building_uc.execute(create_response.building_id)
                
                if get_response.success:
                    print(f"✅ Building retrieved: {get_response.building['name']}")
                else:
                    print(f"❌ Failed to get building: {get_response.error_message}")
                
                # List all buildings
                list_response = list_buildings_uc.execute(page=1, page_size=10)
                
                if list_response.success:
                    print(f"✅ Found {list_response.total_count} buildings")
                    for building in list_response.buildings:
                        print(f"  - {building['name']} ({building['status']})")
                else:
                    print(f"❌ Failed to list buildings: {list_response.error_message}")
            else:
                print(f"❌ Failed to create building: {create_response.error_message}")
                
    except Exception as e:
        print(f"❌ Error in basic use cases: {e}")


def example_complex_use_cases():
    """Example of complex use cases with multiple entities."""
    print("\n=== Complex Use Cases Example ===")
    
    factory = get_repository_factory()
    uow = factory.create_unit_of_work()
    
    try:
        with uow:
            # Create building with floors use case
            create_with_floors_uc = CreateBuildingWithFloorsUseCase(uow)
            
            # Create building request
            building_request = CreateBuildingRequest(
                name="Tech Campus Building",
                address="456 Innovation Ave, Tech City, CA 12345",
                description="Multi-story tech campus building",
                created_by="system"
            )
            
            # Floor data
            floors_data = [
                {
                    'floor_number': 1,
                    'name': 'Ground Floor',
                    'description': 'Lobby and common areas'
                },
                {
                    'floor_number': 2,
                    'name': 'Second Floor',
                    'description': 'Office spaces'
                },
                {
                    'floor_number': 3,
                    'name': 'Third Floor',
                    'description': 'Conference rooms and labs'
                }
            ]
            
            # Create building with floors
            create_response = create_with_floors_uc.execute(building_request, floors_data)
            
            if create_response.success:
                print(f"✅ Building with floors created: {create_response.building_id}")
                
                # Get building hierarchy
                hierarchy_uc = GetBuildingHierarchyUseCase(uow)
                hierarchy_response = hierarchy_uc.execute(create_response.building_id)
                
                if hierarchy_response.success:
                    building = hierarchy_response.building
                    print(f"✅ Building hierarchy retrieved:")
                    print(f"  Building: {building['name']}")
                    print(f"  Floors: {building['floor_count']}")
                    print(f"  Rooms: {building['room_count']}")
                    print(f"  Devices: {building['device_count']}")
                    
                    for floor in building['floors']:
                        print(f"    Floor {floor['floor_number']}: {floor['name']} ({floor['room_count']} rooms)")
                        
                        for room in floor['rooms']:
                            print(f"      Room {room['room_number']}: {room['name']} ({room['device_count']} devices)")
                            
                            for device in room['devices']:
                                print(f"        Device: {device['name']} ({device['device_type']})")
                else:
                    print(f"❌ Failed to get hierarchy: {hierarchy_response.error_message}")
            else:
                print(f"❌ Failed to create building with floors: {create_response.error_message}")
                
    except Exception as e:
        print(f"❌ Error in complex use cases: {e}")


def example_business_logic_use_cases():
    """Example of business logic use cases."""
    print("\n=== Business Logic Use Cases Example ===")
    
    factory = get_repository_factory()
    uow = factory.create_unit_of_work()
    
    try:
        with uow:
            # First create a building with floors
            create_with_floors_uc = CreateBuildingWithFloorsUseCase(uow)
            
            building_request = CreateBuildingRequest(
                name="Smart Building",
                address="789 Smart St, Tech City, CA 12345",
                description="Intelligent building with IoT devices",
                created_by="system"
            )
            
            floors_data = [
                {
                    'floor_number': 1,
                    'name': 'Ground Floor',
                    'description': 'Main entrance and lobby'
                }
            ]
            
            create_response = create_with_floors_uc.execute(building_request, floors_data)
            
            if create_response.success:
                print(f"✅ Smart building created: {create_response.building_id}")
                
                # Get the first floor ID (in a real scenario, you'd get this from the response)
                # For this example, we'll assume we know the floor ID
                floor_id = "example-floor-id"  # In practice, this would come from the created floor
                
                # Add room to floor use case
                add_room_uc = AddRoomToFloorUseCase(uow)
                
                room_data = {
                    'room_number': '101',
                    'name': 'Smart Conference Room',
                    'room_type': 'conference',
                    'description': 'Conference room with smart systems',
                    'created_by': 'system'
                }
                
                devices_data = [
                    {
                        'device_id': 'HVAC-101',
                        'name': 'HVAC Controller',
                        'device_type': 'hvac',
                        'manufacturer': 'SmartTech',
                        'model': 'ST-HVAC-2000',
                        'description': 'Smart HVAC controller'
                    },
                    {
                        'device_id': 'LIGHT-101',
                        'name': 'Smart Lighting',
                        'device_type': 'lighting',
                        'manufacturer': 'LightCorp',
                        'model': 'LC-Smart-1000',
                        'description': 'Intelligent lighting system'
                    }
                ]
                
                add_room_response = add_room_uc.execute(floor_id, room_data, devices_data)
                
                if add_room_response['success']:
                    print(f"✅ Room added: {add_room_response['room_name']}")
                    print(f"  Devices: {add_room_response['device_count']}")
                else:
                    print(f"❌ Failed to add room: {add_room_response['error_message']}")
                
                # Update building status use case
                update_status_uc = UpdateBuildingStatusUseCase(uow)
                update_response = update_status_uc.execute(
                    create_response.building_id,
                    'under_construction',
                    'system'
                )
                
                if update_response['success']:
                    print(f"✅ Building status updated: {update_response['new_status']}")
                    print(f"  Updated floors: {update_response['updated_floors']}")
                    print(f"  Updated rooms: {update_response['updated_rooms']}")
                else:
                    print(f"❌ Failed to update status: {update_response['error_message']}")
                
                # Get building statistics
                stats_uc = GetBuildingStatisticsUseCase(uow)
                stats_response = stats_uc.execute(create_response.building_id)
                
                if stats_response['success']:
                    stats = stats_response['statistics']
                    print(f"✅ Building statistics:")
                    print(f"  Total floors: {stats['total_floors']}")
                    print(f"  Total rooms: {stats['total_rooms']}")
                    print(f"  Total devices: {stats['total_devices']}")
                    print(f"  Device types: {stats['device_types']}")
                    print(f"  Room types: {stats['room_types']}")
                else:
                    print(f"❌ Failed to get statistics: {stats_response['error_message']}")
            else:
                print(f"❌ Failed to create smart building: {create_response.error_message}")
                
    except Exception as e:
        print(f"❌ Error in business logic use cases: {e}")


if __name__ == "__main__":
    # Setup database
    engine, session_factory = setup_database()
    
    # Run examples
    example_basic_use_cases()
    example_complex_use_cases()
    example_business_logic_use_cases()
    
    print("\n=== Use Cases Examples Completed ===") 