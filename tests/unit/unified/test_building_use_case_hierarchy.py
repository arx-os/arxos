from datetime import datetime

from application.unified.use_cases.building_use_case import UnifiedBuildingUseCase
from domain.unified.entities import Building, Floor, Room, Device
from domain.unified.value_objects import BuildingId, Address, BuildingStatus, FloorId, RoomId


class _StubBuildingRepo:
    def __init__(self, building):
        self._building = building

    def get_by_id(self, building_id: str):
        return self._building if str(self._building.id) == building_id else None

    def save(self, entity):
        self._building = entity
        return entity


class _StubFloorRepo:
    def __init__(self, floors):
        self._floors = floors

    def get_by_building_id(self, building_id: str):
        return [f for f in self._floors if str(f.building_id) == building_id]


class _StubRoomRepo:
    def __init__(self, rooms):
        self._rooms = rooms

    def get_by_floor_id(self, floor_id: str):
        return [r for r in self._rooms if str(r.floor_id) == floor_id]


class _StubDeviceRepo:
    def __init__(self, devices):
        self._devices = devices

    def get_by_room_id(self, room_id: str):
        return [d for d in self._devices if str(d.room_id) == room_id]


class _StubProjectRepo:
    pass


def test_get_building_hierarchy_basic():
    building = Building.create(
        name="HQ",
        address=Address(street="1 Ave", city="NYC", state="NY", postal_code="10001"),
        status=BuildingStatus.PLANNED,
        description="test",
    )
    floor = Floor.create(building_id=building.id, floor_number=1, name="Level 1")
    room = Room.create(floor_id=FloorId(str(floor.id)), room_number="101", name="Conf A")
    device = Device.create(room_id=RoomId(str(room.id)), device_id="dev-1", device_type="sensor", name="Temp")

    uc = UnifiedBuildingUseCase(
        building_repository=_StubBuildingRepo(building),
        floor_repository=_StubFloorRepo([floor]),
        room_repository=_StubRoomRepo([room]),
        device_repository=_StubDeviceRepo([device]),
        project_repository=_StubProjectRepo(),
    )

    hierarchy = uc.get_building_hierarchy(str(building.id))

    assert hierarchy["building"]["name"] == "HQ"
    assert len(hierarchy["floors"]) == 1
    assert len(hierarchy["floors"][0]["rooms"]) == 1
    assert len(hierarchy["floors"][0]["rooms"][0]["devices"]) == 1
