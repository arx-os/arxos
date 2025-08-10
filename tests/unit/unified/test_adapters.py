from infrastructure.unified.repositories.adapters import BuildingRepositoryAdapter, FloorRepositoryAdapter, RoomRepositoryAdapter, DeviceRepositoryAdapter
from domain.unified.entities import Building
from domain.unified.value_objects import Address, BuildingStatus


class _LegacyBuilding:
    def __init__(self, id_, name, address, status, coordinates=None, dimensions=None, description=None, created_by=None, metadata=None):
        self.id = id_
        self.name = name
        self.address = address
        self.status = status
        self.coordinates = coordinates
        self.dimensions = dimensions
        self.description = description
        self.created_by = created_by
        self.metadata = metadata or {}


class _Address:
    def __init__(self, street, city, state, postal_code, country="USA"):
        self.street = street
        self.city = city
        self.state = state
        self.postal_code = postal_code
        self.country = country


class _Status:
    def __init__(self, value):
        self.value = value


class _LegacyRepo:
    def __init__(self, entity):
        self._entity = entity

    def get_by_id(self, building_id):
        # building_id is a VO in legacy; accept any and compare by string
        return self._entity if str(self._entity.id) == str(getattr(building_id, "value", building_id)) else None

    def get_all(self):
        return [self._entity]

    def delete(self, building_id):
        if str(self._entity.id) == str(getattr(building_id, "value", building_id)):
            self._entity = None


def test_building_repository_adapter_maps_legacy_to_unified():
    legacy_addr = _Address("1 Ave", "NYC", "NY", "10001")
    legacy_status = _Status("planned")
    legacy = _LegacyBuilding(id_="abc-123", name="HQ", address=legacy_addr, status=legacy_status)
    adapted = BuildingRepositoryAdapter(_LegacyRepo(legacy))

    got = adapted.get_by_id("abc-123")
    assert got is not None
    assert got.name == "HQ"
    assert got.address.city == "NYC"
    assert got.status == BuildingStatus.PLANNED

    all_buildings = adapted.get_all()
    assert len(all_buildings) == 1
    assert all_buildings[0].name == "HQ"


def test_passthrough_adapters_floor_room_device():
    class _R:
        def __init__(self):
            self.saved = []
        def save(self, e):
            self.saved.append(e)
            return e
        def get_by_id(self, _):
            return None
        def get_all(self):
            return []
        def delete(self, _):
            return True

    floor_adapt = FloorRepositoryAdapter(_R())
    room_adapt = RoomRepositoryAdapter(_R())
    device_adapt = DeviceRepositoryAdapter(_R())

    # Smoke call save/get/delete
    dummy = object()
    assert floor_adapt.save(dummy) is dummy
    assert room_adapt.get_all() == []
    assert device_adapt.delete("x") is True
