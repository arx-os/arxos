"""
Unified Building Repository Interface

Defines the minimal repository protocol used by unified use cases.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Optional

from domain.unified.entities.building import Building


class BuildingRepository(ABC):
    @abstractmethod
    def save(self, entity: Building) -> Building:
        pass

    @abstractmethod
    def get_by_id(self, entity_id: str) -> Optional[Building]:
        pass

    @abstractmethod
    def get_all(self) -> List[Building]:
        pass

    @abstractmethod
    def delete(self, entity_id: str) -> bool:
        pass
