"""
Unit of Work Example

This example demonstrates how to use the UnitOfWork and RepositoryFactory
implementations for transaction management and data access.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from domain.entities import Building, Floor, Room, Device, User, Project
from domain.value_objects import (
    BuildingId, FloorId, RoomId, DeviceId, UserId, ProjectId,
    Address, Coordinates, Dimensions, Email, PhoneNumber,
    BuildingStatus, FloorStatus, RoomStatus, DeviceStatus, UserRole, ProjectStatus
)
from infrastructure import (
    SQLAlchemyUnitOfWork, SQLAlchemyRepositoryFactory,
    initialize_repository_factory, get_repository_factory
)


def setup_database():
    """Setup database connection and session factory."""
    # Create engine (using SQLite for this example)
    engine = create_engine('sqlite:///arxos_example.db', echo=True)

    # Create session factory
    session_factory = sessionmaker(bind=engine)

    # Initialize repository factory
    initialize_repository_factory(session_factory)

    return engine, session_factory


def example_basic_usage():
    """Example of basic UnitOfWork usage."""
    print("=== Basic UnitOfWork Usage ===")

    # Get repository factory
    factory = get_repository_factory()

    # Create UnitOfWork
    uow = factory.create_unit_of_work()

    try:
        with uow:
            # Create a building
            building = Building(
                id=BuildingId(),
                name="Example Building",
                address=Address(
                    street="123 Main St",
                    city="Anytown",
                    state="CA",
                    postal_code="12345"
                ),
                status=BuildingStatus.PLANNED,
                created_by="system"
            )

            # Save building using UnitOfWork
            uow.buildings.save(building)
            print(f"Created building: {building.name}")

            # Create a floor
            floor = Floor(
                id=FloorId(),
                building_id=building.id,
                floor_number=1,
                name="Ground Floor",
                status=FloorStatus.PLANNED,
                created_by="system"
            )

            # Save floor using UnitOfWork
            uow.floors.save(floor)
            print(f"Created floor: {floor.name}")

            # Create a room
            room = Room(
                id=RoomId(),
                floor_id=floor.id,
                room_number="101",
                name="Conference Room",
                room_type="conference",
                status=RoomStatus.PLANNED,
                created_by="system"
            )

            # Save room using UnitOfWork
            uow.rooms.save(room)
            print(f"Created room: {room.name}")

            # Create a device
            device = Device(
                id=DeviceId(),
                room_id=room.id,
                device_id="HVAC-001",
                name="HVAC Controller",
                device_type="hvac",
                status=DeviceStatus.INSTALLED,
                manufacturer="ACME Corp",
                model="HVAC-2000",
                created_by="system"
            )

            # Save device using UnitOfWork
            uow.devices.save(device)
            print(f"Created device: {device.name}")

            # All operations will be committed automatically when exiting the context
            print("All entities created successfully!")

    except Exception as e:
        print(f"Error occurred: {e}")
        # Transaction will be rolled back automatically


def example_complex_transaction():
    """Example of complex transaction with multiple operations."""
    print("\n=== Complex Transaction Example ===")

    factory = get_repository_factory()
    uow = factory.create_unit_of_work()

    try:
        with uow:
            # Create a user
            user = User(
                id=UserId(),
                email=Email("john.doe@example.com"),
                username="john.doe",
                role=UserRole.ENGINEER,
                first_name="John",
                last_name="Doe",
                created_by="system"
            )
            uow.users.save(user)
            print(f"Created user: {user.full_name}")

            # Create a building
            building = Building(
                id=BuildingId(),
                name="Office Complex",
                address=Address(
                    street="456 Business Ave",
                    city="Tech City",
                    state="CA",
                    postal_code="54321"
                ),
                status=BuildingStatus.UNDER_CONSTRUCTION,
                created_by=user.id.value
            )
            uow.buildings.save(building)
            print(f"Created building: {building.name}")

            # Create a project
            project = Project(
                id=ProjectId(),
                building_id=building.id,
                name="Office Renovation",
                status=ProjectStatus.IN_PROGRESS,
                description="Complete renovation of office complex",
                created_by=user.id.value
            )
            uow.projects.save(project)
            print(f"Created project: {project.name}")

            # Query operations
            buildings = uow.buildings.get_all()
            print(f"Total buildings: {len(buildings)}")

            users = uow.users.get_active_users()
            print(f"Active users: {len(users)}")

            # All operations committed successfully
            print("Complex transaction completed successfully!")

    except Exception as e:
        print(f"Complex transaction failed: {e}")
        # Transaction will be rolled back automatically


def example_query_operations():
    """Example of query operations using UnitOfWork."""
    print("\n=== Query Operations Example ===")

    factory = get_repository_factory()
    uow = factory.create_unit_of_work()

    try:
        with uow:
            # Get all buildings
            buildings = uow.buildings.get_all()
            print(f"Found {len(buildings)} buildings")

            for building in buildings:
                print(f"  - {building.name} ({building.status.value})")

                # Get floors for this building
                floors = uow.floors.get_by_building_id(building.id)
                print(f"    Floors: {len(floors)}")

                for floor in floors:
                    print(f"      - {floor.name} (Floor {floor.floor_number})")

                    # Get rooms for this floor
                    rooms = uow.rooms.get_by_floor_id(floor.id)
                    print(f"        Rooms: {len(rooms)}")

                    for room in rooms:
                        print(f"          - {room.name} ({room.room_number})")

                        # Get devices for this room
                        devices = uow.devices.get_by_room_id(room.id)
                        print(f"            Devices: {len(devices)}")

                        for device in devices:
                            print(f"              - {device.name} ({device.device_type})")

            # Get users by role
            engineers = uow.users.get_by_role(UserRole.ENGINEER)
            print(f"\nEngineers: {len(engineers)}")

            for engineer in engineers:
                print(f"  - {engineer.full_name} ({engineer.email})")

            # Get projects by status
            active_projects = uow.projects.get_by_status(ProjectStatus.IN_PROGRESS)
            print(f"\nActive projects: {len(active_projects)}")

            for project in active_projects:
                print(f"  - {project.name} ({project.description})")

    except Exception as e:
        print(f"Query operations failed: {e}")


if __name__ == "__main__":
    # Setup database
    engine, session_factory = setup_database()

    # Run examples
    example_basic_usage()
    example_complex_transaction()
    example_query_operations()

    print("\n=== UnitOfWork Examples Completed ===")
