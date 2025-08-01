"""
Simple Test for Application Use Cases

This script tests the use cases directly without the complex application layer
dependencies to verify our UnitOfWork implementation works correctly.
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
from application.use_cases.building_use_cases import (
    CreateBuildingUseCase, GetBuildingUseCase, ListBuildingsUseCase
)
from application.dto.building_dto import CreateBuildingRequest


def test_basic_use_cases():
    """Test basic use cases with UnitOfWork."""
    print("=== Testing Basic Use Cases ===")
    
    # Setup database
    engine = create_engine('sqlite:///test_arxos.db', echo=False)
    session_factory = sessionmaker(bind=engine)
    initialize_repository_factory(session_factory)
    
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
                name="Test Building",
                address="123 Test St, Test City, CA 12345",
                description="Test building for unit testing",
                created_by="test_user"
            )
            
            create_response = create_building_uc.execute(create_request)
            
            if create_response.success:
                print(f"✅ Building created: {create_response.building_id}")
                
                # Get the building
                get_response = get_building_uc.execute(create_response.building_id)
                
                if get_response.success:
                    print(f"✅ Building retrieved: {get_response.building['name']}")
                    print(f"  Address: {get_response.building['address']}")
                    print(f"  Status: {get_response.building['status']}")
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
        print(f"❌ Error in test: {e}")
        import traceback
        traceback.print_exc()


def test_unit_of_work_directly():
    """Test UnitOfWork directly without use cases."""
    print("\n=== Testing UnitOfWork Directly ===")
    
    # Setup database
    engine = create_engine('sqlite:///test_arxos_direct.db', echo=False)
    session_factory = sessionmaker(bind=engine)
    initialize_repository_factory(session_factory)
    
    # Get repository factory
    factory = get_repository_factory()
    
    # Create UnitOfWork
    uow = factory.create_unit_of_work()
    
    try:
        with uow:
            # Create a building directly
            building_id = BuildingId()
            address = Address.from_string("456 Direct St, Direct City, CA 12345")
            
            building = Building(
                id=building_id,
                name="Direct Test Building",
                address=address,
                description="Building created directly with UnitOfWork",
                created_by="test_user"
            )
            
            # Save building using UnitOfWork
            uow.buildings.save(building)
            print(f"✅ Building saved directly: {building.name}")
            
            # Retrieve building
            retrieved_building = uow.buildings.get_by_id(building_id)
            
            if retrieved_building:
                print(f"✅ Building retrieved directly: {retrieved_building.name}")
                print(f"  Address: {retrieved_building.address}")
                print(f"  Status: {retrieved_building.status.value}")
            else:
                print("❌ Failed to retrieve building")
            
            # List all buildings
            all_buildings = uow.buildings.get_all()
            print(f"✅ Total buildings: {len(all_buildings)}")
            
            for b in all_buildings:
                print(f"  - {b.name} ({b.status.value})")
                
    except Exception as e:
        print(f"❌ Error in direct test: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("🚀 Starting Use Cases Tests")
    print("=" * 50)
    
    test_basic_use_cases()
    test_unit_of_work_directly()
    
    print("\n" + "=" * 50)
    print("✅ Use Cases Tests Completed") 