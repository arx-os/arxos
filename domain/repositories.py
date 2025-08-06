"""
Domain Repository Interfaces

This module defines the abstract repository interfaces for the domain layer.
These interfaces define the contract for data access operations.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime
from decimal import Decimal

from .entities import Building, Floor, Room, Device, User, Project


class BuildingRepository(ABC):
    """Abstract building repository interface."""

    @abstractmethod
    def create(self, building: Building) -> Building:
        """Create a new building."""
        pass

    @abstractmethod
    def get_by_id(self, building_id: str) -> Optional[Building]:
        """Get building by ID."""
        pass

    @abstractmethod
    def get_all(self) -> List[Building]:
        """Get all buildings."""
        pass

    @abstractmethod
    def update(self, building: Building) -> Building:
        """Update a building."""
        pass

    @abstractmethod
    def delete(self, building_id: str) -> bool:
        """Delete a building."""
        pass

    @abstractmethod
    def find_by_criteria(self, criteria: Dict[str, Any]) -> List[Building]:
        """Find buildings by criteria."""
        pass


class FloorRepository(ABC):
    """Abstract floor repository interface."""

    @abstractmethod
    def create(self, floor: Floor) -> Floor:
        """Create a new floor."""
        pass

    @abstractmethod
    def get_by_id(self, floor_id: str) -> Optional[Floor]:
        """Get floor by ID."""
        pass

    @abstractmethod
    def get_by_building_id(self, building_id: str) -> List[Floor]:
        """Get floors by building ID."""
        pass

    @abstractmethod
    def get_all(self) -> List[Floor]:
        """Get all floors."""
        pass

    @abstractmethod
    def update(self, floor: Floor) -> Floor:
        """Update a floor."""
        pass

    @abstractmethod
    def delete(self, floor_id: str) -> bool:
        """Delete a floor."""
        pass


class RoomRepository(ABC):
    """Abstract room repository interface."""

    @abstractmethod
    def create(self, room: Room) -> Room:
        """Create a new room."""
        pass

    @abstractmethod
    def get_by_id(self, room_id: str) -> Optional[Room]:
        """Get room by ID."""
        pass

    @abstractmethod
    def get_by_floor_id(self, floor_id: str) -> List[Room]:
        """Get rooms by floor ID."""
        pass

    @abstractmethod
    def get_all(self) -> List[Room]:
        """Get all rooms."""
        pass

    @abstractmethod
    def update(self, room: Room) -> Room:
        """Update a room."""
        pass

    @abstractmethod
    def delete(self, room_id: str) -> bool:
        """Delete a room."""
        pass


class DeviceRepository(ABC):
    """Abstract device repository interface."""

    @abstractmethod
    def create(self, device: Device) -> Device:
        """Create a new device."""
        pass

    @abstractmethod
    def get_by_id(self, device_id: str) -> Optional[Device]:
        """Get device by ID."""
        pass

    @abstractmethod
    def get_by_room_id(self, room_id: str) -> List[Device]:
        """Get devices by room ID."""
        pass

    @abstractmethod
    def get_all(self) -> List[Device]:
        """Get all devices."""
        pass

    @abstractmethod
    def update(self, device: Device) -> Device:
        """Update a device."""
        pass

    @abstractmethod
    def delete(self, device_id: str) -> bool:
        """Delete a device."""
        pass


class UserRepository(ABC):
    """Abstract user repository interface."""

    @abstractmethod
    def create(self, user: User) -> User:
        """Create a new user."""
        pass

    @abstractmethod
    def get_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID."""
        pass

    @abstractmethod
    def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        pass

    @abstractmethod
    def get_all(self) -> List[User]:
        """Get all users."""
        pass

    @abstractmethod
    def update(self, user: User) -> User:
        """Update a user."""
        pass

    @abstractmethod
    def delete(self, user_id: str) -> bool:
        """Delete a user."""
        pass


class ProjectRepository(ABC):
    """Abstract project repository interface."""

    @abstractmethod
    def create(self, project: Project) -> Project:
        """Create a new project."""
        pass

    @abstractmethod
    def get_by_id(self, project_id: str) -> Optional[Project]:
        """Get project by ID."""
        pass

    @abstractmethod
    def get_by_user_id(self, user_id: str) -> List[Project]:
        """Get projects by user ID."""
        pass

    @abstractmethod
    def get_all(self) -> List[Project]:
        """Get all projects."""
        pass

    @abstractmethod
    def update(self, project: Project) -> Project:
        """Update a project."""
        pass

    @abstractmethod
    def delete(self, project_id: str) -> bool:
        """Delete a project."""
        pass


# BILT Token System Repositories


class ContributionRepository(ABC):
    """Abstract contribution repository interface for BILT token system."""

    @abstractmethod
    def create(self, contribution_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new contribution record."""
        pass

    @abstractmethod
    def get_by_id(self, contribution_id: str) -> Optional[Dict[str, Any]]:
        """Get contribution by ID."""
        pass

    @abstractmethod
    def get_by_contributor(self, contributor_wallet: str) -> List[Dict[str, Any]]:
        """Get contributions by contributor wallet."""
        pass

    @abstractmethod
    def get_by_biltobject_hash(self, biltobject_hash: str) -> Optional[Dict[str, Any]]:
        """Get contribution by building object hash."""
        pass

    @abstractmethod
    def get_all(self) -> List[Dict[str, Any]]:
        """Get all contributions."""
        pass

    @abstractmethod
    def update(self, contribution_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update a contribution."""
        pass

    @abstractmethod
    def delete(self, contribution_id: str) -> bool:
        """Delete a contribution."""
        pass

    @abstractmethod
    def get_total_contributions(self) -> int:
        """Get total number of contributions."""
        pass

    @abstractmethod
    def get_contributions_by_date_range(
        self, start_date: datetime, end_date: datetime
    ) -> List[Dict[str, Any]]:
        """Get contributions within date range."""
        pass


class RevenueRepository(ABC):
    """Abstract revenue repository interface for BILT token system."""

    @abstractmethod
    def create(self, revenue_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new revenue record."""
        pass

    @abstractmethod
    def get_by_id(self, revenue_id: str) -> Optional[Dict[str, Any]]:
        """Get revenue by ID."""
        pass

    @abstractmethod
    def get_by_source(self, source: str) -> List[Dict[str, Any]]:
        """Get revenue by source."""
        pass

    @abstractmethod
    def get_all(self) -> List[Dict[str, Any]]:
        """Get all revenue records."""
        pass

    @abstractmethod
    def update(self, revenue_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update a revenue record."""
        pass

    @abstractmethod
    def delete(self, revenue_id: str) -> bool:
        """Delete a revenue record."""
        pass

    @abstractmethod
    def get_total_revenue(self) -> Decimal:
        """Get total revenue."""
        pass

    @abstractmethod
    def get_revenue_by_date_range(
        self, start_date: datetime, end_date: datetime
    ) -> List[Dict[str, Any]]:
        """Get revenue within date range."""
        pass

    @abstractmethod
    def get_revenue_for_distribution(
        self, distribution_id: str
    ) -> List[Dict[str, Any]]:
        """Get revenue records for a specific distribution."""
        pass


class DividendRepository(ABC):
    """Abstract dividend repository interface for BILT token system."""

    @abstractmethod
    def create(self, dividend_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new dividend distribution record."""
        pass

    @abstractmethod
    def get_by_id(self, distribution_id: str) -> Optional[Dict[str, Any]]:
        """Get dividend distribution by ID."""
        pass

    @abstractmethod
    def get_all(self) -> List[Dict[str, Any]]:
        """Get all dividend distributions."""
        pass

    @abstractmethod
    def update(self, distribution_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update a dividend distribution."""
        pass

    @abstractmethod
    def delete(self, distribution_id: str) -> bool:
        """Delete a dividend distribution."""
        pass

    @abstractmethod
    def get_total_distributions(self) -> int:
        """Get total number of distributions."""
        pass

    @abstractmethod
    def get_distributions(
        self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """Get distributions within date range."""
        pass

    @abstractmethod
    def get_claim_data(self, wallet_address: str) -> Dict[str, Any]:
        """Get claim data for a wallet address."""
        pass

    @abstractmethod
    def update_claim_data(
        self, wallet_address: str, claim_amount: Decimal, transaction_hash: str
    ) -> Dict[str, Any]:
        """Update claim data for a wallet address."""
        pass


class VerificationRepository(ABC):
    """Abstract verification repository interface for BILT token system."""

    @abstractmethod
    def create(self, verification_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new verification record."""
        pass

    @abstractmethod
    def get_by_id(self, verification_id: str) -> Optional[Dict[str, Any]]:
        """Get verification by ID."""
        pass

    @abstractmethod
    def get_by_biltobject_hash(self, biltobject_hash: str) -> List[Dict[str, Any]]:
        """Get verifications by building object hash."""
        pass

    @abstractmethod
    def get_by_verifier(self, verifier_wallet: str) -> List[Dict[str, Any]]:
        """Get verifications by verifier wallet."""
        pass

    @abstractmethod
    def get_all(self) -> List[Dict[str, Any]]:
        """Get all verifications."""
        pass

    @abstractmethod
    def update(self, verification_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update a verification."""
        pass

    @abstractmethod
    def delete(self, verification_id: str) -> bool:
        """Delete a verification."""
        pass


class UnitOfWork(ABC):
    """Abstract unit of work interface."""

    @property
    @abstractmethod
    def buildings(self) -> BuildingRepository:
        """Get the building repository."""
        pass

    @property
    @abstractmethod
    def floors(self) -> FloorRepository:
        """Get the floor repository."""
        pass

    @property
    @abstractmethod
    def rooms(self) -> RoomRepository:
        """Get the room repository."""
        pass

    @property
    @abstractmethod
    def devices(self) -> DeviceRepository:
        """Get the device repository."""
        pass

    @property
    @abstractmethod
    def users(self) -> UserRepository:
        """Get the user repository."""
        pass

    @property
    @abstractmethod
    def projects(self) -> ProjectRepository:
        """Get the project repository."""
        pass

    @property
    @abstractmethod
    def contributions(self) -> ContributionRepository:
        """Get the contribution repository."""
        pass

    @property
    @abstractmethod
    def revenue(self) -> RevenueRepository:
        """Get the revenue repository."""
        pass

    @property
    @abstractmethod
    def dividends(self) -> DividendRepository:
        """Get the dividend repository."""
        pass

    @property
    @abstractmethod
    def verifications(self) -> VerificationRepository:
        """Get the verification repository."""
        pass

    @abstractmethod
    def commit(self) -> None:
        """Commit the unit of work."""
        pass

    @abstractmethod
    def rollback(self) -> None:
        """Rollback the unit of work."""
        pass


class RepositoryFactory(ABC):
    """Abstract repository factory interface."""

    @abstractmethod
    def create_building_repository(self) -> BuildingRepository:
        """Create a building repository instance."""
        pass

    @abstractmethod
    def create_floor_repository(self) -> FloorRepository:
        """Create a floor repository instance."""
        pass

    @abstractmethod
    def create_room_repository(self) -> RoomRepository:
        """Create a room repository instance."""
        pass

    @abstractmethod
    def create_device_repository(self) -> DeviceRepository:
        """Create a device repository instance."""
        pass

    @abstractmethod
    def create_user_repository(self) -> UserRepository:
        """Create a user repository instance."""
        pass

    @abstractmethod
    def create_project_repository(self) -> ProjectRepository:
        """Create a project repository instance."""
        pass

    @abstractmethod
    def create_contribution_repository(self) -> ContributionRepository:
        """Create a contribution repository instance."""
        pass

    @abstractmethod
    def create_revenue_repository(self) -> RevenueRepository:
        """Create a revenue repository instance."""
        pass

    @abstractmethod
    def create_dividend_repository(self) -> DividendRepository:
        """Create a dividend repository instance."""
        pass

    @abstractmethod
    def create_verification_repository(self) -> VerificationRepository:
        """Create a verification repository instance."""
        pass

    @abstractmethod
    def create_unit_of_work(self) -> UnitOfWork:
        """Create a unit of work instance."""
        pass
