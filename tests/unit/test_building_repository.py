import pytest
from unittest.mock import Mock, patch, MagicMock
from sqlalchemy.exc import SQLAlchemyError, IntegrityError, OperationalError
from domain.exceptions import DatabaseError, RepositoryError
from infrastructure.repositories.building_repository import BuildingRepository
from domain.entities import Building
from domain.value_objects import BuildingId, BuildingStatus, Address, Coordinates, Dimensions


class TestBuildingRepository:
    """Test cases for BuildingRepository."""

    @pytest.fixture
    def mock_session(self):
        """Create a mock SQLAlchemy session."""
        return Mock()

    @pytest.fixture
    def mock_logger(self):
        """Create a mock logger."""
        return Mock()

    @pytest.fixture
    def repository(self, mock_session, mock_logger):
        """Create a repository instance with mocked dependencies."""
        repo = BuildingRepository(mock_session)
        repo.logger = mock_logger
        return repo

    @pytest.fixture
    def sample_building(self):
        """Create a sample building entity."""
        return Building(
            id=BuildingId(),
            name="Test Building",
            address=Address(
                street="123 Test St",
                city="Test City",
                state="Test State",
                country="Test Country",
                postal_code="12345"
            ),
            building_type="Office",
            area=1000.0,
            volume=5000.0,
            floors=5,
            year_built=2020,
            status=BuildingStatus.ACTIVE,
            description="Test building description"
        )

    def test_find_by_name_success(self, repository, mock_session, sample_building):
        """Test successful building search by name."""
        # Arrange
        mock_model = Mock()
        mock_model.name = "Test Building"
        mock_session.query.return_value.filter.return_value.first.return_value = mock_model

        with patch.object(repository, '_model_to_entity', return_value=sample_building):
            # Act
            result = repository.find_by_name("Test Building")

            # Assert
            assert result == sample_building
            mock_session.query.assert_called_once()
            mock_session.query.return_value.filter.assert_called_once()

    def test_find_by_name_not_found(self, repository, mock_session):
        """Test building search by name when not found."""
        # Arrange
        mock_session.query.return_value.filter.return_value.first.return_value = None

        # Act
        result = repository.find_by_name("Non-existent Building")

        # Assert
        assert result is None

    def test_find_by_name_database_error(self, repository, mock_session, mock_logger):
        """Test database error handling when searching by name."""
        # Arrange
        mock_session.query.return_value.filter.return_value.first.side_effect = SQLAlchemyError("Database connection failed")

        # Act & Assert
        with pytest.raises(DatabaseError, match="Failed to find building by name"):
            repository.find_by_name("Test Building")

        mock_logger.error.assert_called_once()

    def test_find_by_status_success(self, repository, mock_session, sample_building):
        """Test successful building search by status."""
        # Arrange
        mock_models = [Mock(), Mock()]
        mock_session.query.return_value.filter.return_value.all.return_value = mock_models

        with patch.object(repository, '_model_to_entity', side_effect=[sample_building, sample_building]):
            # Act
            result = repository.find_by_status("active")

            # Assert
            assert len(result) == 2
            assert all(isinstance(building, Building) for building in result)

    def test_find_by_status_database_error(self, repository, mock_session, mock_logger):
        """Test database error handling when searching by status."""
        # Arrange
        mock_session.query.return_value.filter.return_value.all.side_effect = SQLAlchemyError("Database connection failed")

        # Act & Assert
        with pytest.raises(DatabaseError, match="Failed to find buildings by status"):
            repository.find_by_status("active")

        mock_logger.error.assert_called_once()

    def test_count_success(self, repository, mock_session):
        """Test successful building count."""
        # Arrange
        mock_session.query.return_value.count.return_value = 42

        # Act
        result = repository.count()

        # Assert
        assert result == 42
        mock_session.query.return_value.count.assert_called_once()

    def test_count_database_error(self, repository, mock_session, mock_logger):
        """Test database error handling when counting buildings."""
        # Arrange
        mock_session.query.return_value.count.side_effect = SQLAlchemyError("Database connection failed")

        # Act & Assert
        with pytest.raises(DatabaseError, match="Failed to count buildings"):
            repository.count()

        mock_logger.error.assert_called_once()

    def test_count_by_status_success(self, repository, mock_session):
        """Test successful building count by status."""
        # Arrange
        mock_session.query.return_value.filter.return_value.count.return_value = 15

        # Act
        result = repository.count_by_status("active")

        # Assert
        assert result == 15
        mock_session.query.return_value.filter.assert_called_once()

    def test_count_by_status_database_error(self, repository, mock_session, mock_logger):
        """Test database error handling when counting by status."""
        # Arrange
        mock_session.query.return_value.filter.return_value.count.side_effect = SQLAlchemyError("Database connection failed")

        # Act & Assert
        with pytest.raises(DatabaseError, match="Failed to count buildings by status"):
            repository.count_by_status("active")

        mock_logger.error.assert_called_once()

    def test_find_by_city_success(self, repository, mock_session, sample_building):
        """Test successful building search by city."""
        # Arrange
        mock_models = [Mock(), Mock()]
        mock_session.query.return_value.filter.return_value.all.return_value = mock_models

        with patch.object(repository, '_model_to_entity', side_effect=[sample_building, sample_building]):
            # Act
            result = repository.find_by_city("Test City")

            # Assert
            assert len(result) == 2
            assert all(isinstance(building, Building) for building in result)

    def test_find_by_building_type_success(self, repository, mock_session, sample_building):
        """Test successful building search by building type."""
        # Arrange
        mock_models = [Mock()]
        mock_session.query.return_value.filter.return_value.all.return_value = mock_models

        with patch.object(repository, '_model_to_entity', return_value=sample_building):
            # Act
            result = repository.find_by_building_type("Office")

            # Assert
            assert len(result) == 1
            assert result[0] == sample_building

    def test_search_buildings_success(self, repository, mock_session, sample_building):
        """Test successful building search by query."""
        # Arrange
        mock_models = [Mock()]
        mock_session.query.return_value.filter.return_value.all.return_value = mock_models

        with patch.object(repository, '_model_to_entity', return_value=sample_building):
            # Act
            result = repository.search_buildings("Test")

            # Assert
            assert len(result) == 1
            assert result[0] == sample_building

    def test_search_buildings_database_error(self, repository, mock_session, mock_logger):
        """Test database error handling when searching buildings."""
        # Arrange
        mock_session.query.return_value.filter.return_value.all.side_effect = SQLAlchemyError("Database connection failed")

        # Act & Assert
        with pytest.raises(DatabaseError, match="Failed to search buildings"):
            repository.search_buildings("Test")

        mock_logger.error.assert_called_once()

    def test_get_building_statistics_success(self, repository, mock_session):
        """Test successful building statistics retrieval."""
        # Arrange
        mock_session.query.return_value.count.return_value = 100
        mock_session.query.return_value.filter.return_value.count.return_value = 80

        # Mock the group_by queries
        mock_type_query = Mock()
        mock_type_query.group_by.return_value.all.return_value = [("Office", 50), ("Residential", 30)]
        mock_city_query = Mock()
        mock_city_query.group_by.return_value.all.return_value = [("City A", 40), ("City B", 35)]

        mock_session.query.side_effect = [
            mock_session.query.return_value,  # total_buildings
            mock_session.query.return_value,  # active_buildings
            mock_session.query.return_value,  # inactive_buildings
            mock_type_query,  # building types
            mock_city_query   # cities
        ]

        # Act
        result = repository.get_building_statistics()

        # Assert
        assert result["total_buildings"] == 100
        assert result["active_buildings"] == 80
        assert result["building_types"]["Office"] == 50
        assert result["cities"]["City A"] == 40

    def test_get_building_statistics_database_error(self, repository, mock_session, mock_logger):
        """Test database error handling when getting statistics."""
        # Arrange
        mock_session.query.return_value.count.side_effect = SQLAlchemyError("Database connection failed")

        # Act & Assert
        with pytest.raises(DatabaseError, match="Failed to get building statistics"):
            repository.get_building_statistics()

        mock_logger.error.assert_called_once()

    def test_unexpected_error_handling(self, repository, mock_session, mock_logger):
        """Test handling of unexpected errors."""
        # Arrange
        mock_session.query.return_value.filter.return_value.first.side_effect = Exception("Unexpected error")

        # Act & Assert
        with pytest.raises(RepositoryError, match="Unexpected error finding building by name"):
            repository.find_by_name("Test Building")

        mock_logger.error.assert_called_once()

    def test_error_propagation_chain(self, repository, mock_session, mock_logger):
        """Test that errors are properly propagated through the chain."""
        # Arrange
        mock_session.query.return_value.filter.return_value.first.side_effect = OperationalError("Connection timeout", None, None)

        # Act & Assert
        with pytest.raises(DatabaseError, match="Failed to find building by name"):
            repository.find_by_name("Test Building")

        # Verify the error was logged
        mock_logger.error.assert_called_once()
        error_log = mock_logger.error.call_args[0][0]
        assert "Database error finding building by name" in error_log
