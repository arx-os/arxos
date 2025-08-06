"""
Tests for SVGX Engine Symbol Manager Service

Comprehensive test suite covering:
- Symbol CRUD operations
- Validation and error handling
- Bulk operations
- SVGX-specific features
- Performance monitoring
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch

from svgx_engine.services.symbol_manager import (
    SVGXSymbolManager,
    SymbolCategory,
    SymbolStatus,
    SymbolValidationLevel,
    create_svgx_symbol_manager,
)
from svgx_engine.utils.errors import ValidationError, SymbolError


class TestSVGXSymbolManager:
    """Test suite for SVGX Symbol Manager."""

    @pytest.fixture
    def temp_library_path(self):
        """Create a temporary library path for testing."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def symbol_manager(self, temp_library_path):
        """Create a symbol manager instance for testing."""
        return SVGXSymbolManager(temp_library_path)

    @pytest.fixture
    def sample_symbol_data(self):
        """Sample symbol data for testing."""
        return {
            "name": "Test Electrical Outlet",
            "category": "electrical",
            "description": "A standard electrical outlet symbol",
            "tags": ["electrical", "outlet", "power"],
            "svgx_namespace": "arx",
            "svgx_version": "1.0",
            "validation_rules": ["must_have_dimensions", "must_have_material"],
        }

    def test_initialization(self, temp_library_path):
        """Test symbol manager initialization."""
        manager = SVGXSymbolManager(temp_library_path)
        assert manager.library_path == Path(temp_library_path)
        assert manager.symbols_dir.exists()
        assert manager.metadata_dir.exists()
        assert manager.cache_dir.exists()

    def test_create_symbol_success(self, symbol_manager, sample_symbol_data):
        """Test successful symbol creation."""
        result = symbol_manager.create_symbol(sample_symbol_data)

        assert "id" in result
        assert result["name"] == sample_symbol_data["name"]
        assert result["category"] == sample_symbol_data["category"]
        assert result["svgx_namespace"] == "arx"
        assert result["status"] == SymbolStatus.ACTIVE.value
        assert "created_at" in result
        assert "updated_at" in result

    def test_create_symbol_with_existing_id(self, symbol_manager, sample_symbol_data):
        """Test symbol creation with existing ID."""
        sample_symbol_data["id"] = "test_outlet_001"
        result = symbol_manager.create_symbol(sample_symbol_data)

        assert result["id"] == "test_outlet_001"

    def test_create_symbol_duplicate_id(self, symbol_manager, sample_symbol_data):
        """Test symbol creation with duplicate ID."""
        sample_symbol_data["id"] = "duplicate_id"
        symbol_manager.create_symbol(sample_symbol_data)

        # Try to create another symbol with same ID
        with pytest.raises(SymbolError, match="already exists"):
            symbol_manager.create_symbol(sample_symbol_data)

    def test_get_symbol_success(self, symbol_manager, sample_symbol_data):
        """Test successful symbol retrieval."""
        created_symbol = symbol_manager.create_symbol(sample_symbol_data)
        retrieved_symbol = symbol_manager.get_symbol(created_symbol["id"])

        assert retrieved_symbol is not None
        assert retrieved_symbol["name"] == sample_symbol_data["name"]
        assert retrieved_symbol["id"] == created_symbol["id"]

    def test_get_symbol_not_found(self, symbol_manager):
        """Test symbol retrieval for non-existent symbol."""
        result = symbol_manager.get_symbol("non_existent_id")
        assert result is None

    def test_update_symbol_success(self, symbol_manager, sample_symbol_data):
        """Test successful symbol update."""
        created_symbol = symbol_manager.create_symbol(sample_symbol_data)
        updates = {
            "description": "Updated description",
            "tags": ["electrical", "outlet", "power", "updated"],
        }

        updated_symbol = symbol_manager.update_symbol(created_symbol["id"], updates)

        assert updated_symbol["description"] == "Updated description"
        assert "updated" in updated_symbol["tags"]
        assert "updated_at" in updated_symbol

    def test_update_symbol_not_found(self, symbol_manager):
        """Test symbol update for non-existent symbol."""
        updates = {"description": "Updated description"}
        result = symbol_manager.update_symbol("non_existent_id", updates)
        assert result is None

    def test_delete_symbol_success(self, symbol_manager, sample_symbol_data):
        """Test successful symbol deletion."""
        created_symbol = symbol_manager.create_symbol(sample_symbol_data)
        result = symbol_manager.delete_symbol(created_symbol["id"])

        assert result is True
        assert symbol_manager.get_symbol(created_symbol["id"]) is None

    def test_delete_symbol_not_found(self, symbol_manager):
        """Test symbol deletion for non-existent symbol."""
        result = symbol_manager.delete_symbol("non_existent_id")
        assert result is False

    def test_list_symbols_empty(self, symbol_manager):
        """Test listing symbols when library is empty."""
        symbols = symbol_manager.list_symbols()
        assert symbols == []

    def test_list_symbols_with_filtering(self, symbol_manager, sample_symbol_data):
        """Test listing symbols with category filtering."""
        # Create electrical symbol
        symbol_manager.create_symbol(sample_symbol_data)

        # Create mechanical symbol
        mechanical_data = sample_symbol_data.copy()
        mechanical_data["name"] = "Test HVAC Duct"
        mechanical_data["category"] = "mechanical"
        symbol_manager.create_symbol(mechanical_data)

        # Test filtering by category
        electrical_symbols = symbol_manager.list_symbols(
            category=SymbolCategory.ELECTRICAL
        )
        mechanical_symbols = symbol_manager.list_symbols(
            category=SymbolCategory.MECHANICAL
        )

        assert len(electrical_symbols) == 1
        assert len(mechanical_symbols) == 1
        assert electrical_symbols[0]["category"] == "electrical"
        assert mechanical_symbols[0]["category"] == "mechanical"

    def test_search_symbols(self, symbol_manager, sample_symbol_data):
        """Test symbol search functionality."""
        symbol_manager.create_symbol(sample_symbol_data)

        # Search by name
        results = symbol_manager.search_symbols("electrical")
        assert len(results) == 1
        assert results[0]["name"] == sample_symbol_data["name"]

        # Search by tag
        results = symbol_manager.search_symbols("outlet")
        assert len(results) == 1

        # Search non-existent
        results = symbol_manager.search_symbols("non_existent")
        assert len(results) == 0

    def test_bulk_create_symbols(self, symbol_manager):
        """Test bulk symbol creation."""
        symbols_data = [
            {
                "name": "Symbol 1",
                "category": "electrical",
                "description": "First symbol",
            },
            {
                "name": "Symbol 2",
                "category": "mechanical",
                "description": "Second symbol",
            },
        ]

        created_symbols = symbol_manager.bulk_create_symbols(symbols_data)

        assert len(created_symbols) == 2
        assert all("id" in symbol for symbol in created_symbols)

    def test_bulk_update_symbols(self, symbol_manager, sample_symbol_data):
        """Test bulk symbol updates."""
        # Create symbols first
        symbol1 = symbol_manager.create_symbol(sample_symbol_data)

        sample_symbol_data["name"] = "Test Mechanical Valve"
        sample_symbol_data["category"] = "mechanical"
        symbol2 = symbol_manager.create_symbol(sample_symbol_data)

        # Prepare updates
        updates = [
            {"id": symbol1["id"], "description": "Updated symbol 1"},
            {"id": symbol2["id"], "description": "Updated symbol 2"},
        ]

        updated_symbols = symbol_manager.bulk_update_symbols(updates)

        assert len(updated_symbols) == 2
        assert updated_symbols[0]["description"] == "Updated symbol 1"
        assert updated_symbols[1]["description"] == "Updated symbol 2"

    def test_get_symbol_statistics(self, symbol_manager, sample_symbol_data):
        """Test symbol statistics."""
        # Create symbols in different categories
        symbol_manager.create_symbol(sample_symbol_data)

        sample_symbol_data["name"] = "Test Mechanical Valve"
        sample_symbol_data["category"] = "mechanical"
        symbol_manager.create_symbol(sample_symbol_data)

        stats = symbol_manager.get_symbol_statistics()

        assert stats["total_symbols"] == 2
        assert "electrical" in stats["category_breakdown"]
        assert "mechanical" in stats["category_breakdown"]
        assert "performance_metrics" in stats

    def test_validation_levels(self, symbol_manager):
        """Test different validation levels."""
        # Test with basic validation
        basic_data = {"name": "Basic Symbol", "category": "electrical"}
        result = symbol_manager.create_symbol(basic_data, SymbolValidationLevel.BASIC)
        assert result is not None

        # Test with strict validation (should fail without description)
        strict_data = {"name": "Strict Symbol", "category": "electrical"}
        with pytest.raises(ValidationError):
            symbol_manager.create_symbol(strict_data, SymbolValidationLevel.STRICT)

    def test_clear_cache(self, symbol_manager, sample_symbol_data):
        """Test cache clearing functionality."""
        symbol_manager.create_symbol(sample_symbol_data)

        # Verify symbol is in cache
        symbol_id = symbol_manager.list_symbols()[0]["id"]
        assert symbol_id in symbol_manager._symbol_cache

        # Clear cache
        symbol_manager.clear_cache()
        assert len(symbol_manager._symbol_cache) == 0
        assert len(symbol_manager._metadata_cache) == 0


class TestSVGXSymbolManagerConvenienceFunction:
    """Test the convenience function for creating symbol managers."""

    def test_create_svgx_symbol_manager_default(self):
        """Test creating symbol manager with default path."""
        manager = create_svgx_symbol_manager()
        assert isinstance(manager, SVGXSymbolManager)

    def test_create_svgx_symbol_manager_custom_path(self, temp_library_path):
        """Test creating symbol manager with custom path."""
        manager = create_svgx_symbol_manager(temp_library_path)
        assert isinstance(manager, SVGXSymbolManager)
        assert manager.library_path == Path(temp_library_path)


if __name__ == "__main__":
    pytest.main([__file__])
