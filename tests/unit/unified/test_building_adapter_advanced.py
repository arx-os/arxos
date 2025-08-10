from infrastructure.unified.repositories.adapters import BuildingRepositoryAdapter
from domain.unified.entities import Building
from domain.unified.value_objects import Address, BuildingStatus


class _LegacyWithAdvanced:
    def __init__(self, entities):
        self._entities = entities

    def get_by_status(self, status):  # legacy status
        # status may be enum; compare by value
        val = getattr(status, "value", str(status))
        return [e for e in self._entities if getattr(e.status, "value", str(e.status)) == val]

    def find_by_name(self, name: str):
        for e in self._entities:
            if e.name == name:
                return e
        return None


class _LegacyEntity:
    def __init__(self, id_, name, address, status):
        self.id = id_
        self.name = name
        self.address = address
        self.status = status


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


def test_building_adapter_get_by_status_and_find_by_name():
    addr = _Address("1 Ave", "NYC", "NY", "10001")
    planned = _LegacyEntity("id1", "HQ", addr, _Status("planned"))
    completed = _LegacyEntity("id2", "Annex", addr, _Status("completed"))
    legacy_repo = _LegacyWithAdvanced([planned, completed])

    adapter = BuildingRepositoryAdapter(legacy_repo)

    got_planned = adapter.get_by_status("planned")
    assert len(got_planned) == 1
    assert got_planned[0].name == "HQ"

    found = adapter.find_by_name("Annex")
    assert found is not None
    assert found.name == "Annex"
