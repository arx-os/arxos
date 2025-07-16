"""
Tests for SVGX Engine Symbol Recognition Service

Comprehensive test suite covering:
- Fuzzy matching functionality
- Context-aware interpretation
- Symbol validation
- Text and SVGX content recognition
- Error handling and edge cases
"""

import pytest
from unittest.mock import Mock, patch
from svgx_engine.services.symbol_recognition import (
    SVGXSymbolRecognitionService,
    create_svgx_symbol_recognition_service
)
from svgx_engine.services.symbol_manager import SVGXSymbolManager
from svgx_engine.utils.errors import RecognitionError


class TestSVGXSymbolRecognitionService:
    """Test suite for SVGX Symbol Recognition Service."""
    
    @pytest.fixture
    def mock_symbol_manager(self):
        """Create a mock symbol manager for testing."""
        mock_manager = Mock(spec=SVGXSymbolManager)
        
        # Mock symbol library
        mock_symbols = [
            {
                "id": "electrical_outlet",
                "name": "Electrical Outlet",
                "category": "electrical",
                "tags": ["electrical", "outlet", "power"],
                "validation_rules": ["must_have_dimensions", "must_have_material"]
            },
            {
                "id": "hvac_duct",
                "name": "HVAC Duct",
                "category": "mechanical", 
                "tags": ["hvac", "duct", "air"],
                "validation_rules": ["must_have_size", "must_have_flow_rate"]
            },
            {
                "id": "water_pipe",
                "name": "Water Pipe",
                "category": "plumbing",
                "tags": ["plumbing", "pipe", "water"],
                "validation_rules": ["must_have_size", "must_have_pressure"]
            }
        ]
        
        mock_manager.list_symbols.return_value = mock_symbols
        return mock_manager
    
    @pytest.fixture
    def recognition_service(self, mock_symbol_manager):
        """Create a recognition service instance for testing."""
        return SVGXSymbolRecognitionService(mock_symbol_manager)
    
    def test_initialization(self, mock_symbol_manager):
        """Test recognition service initialization."""
        service = SVGXSymbolRecognitionService(mock_symbol_manager)
        
        assert service.symbol_manager == mock_symbol_manager
        assert len(service.symbol_library) == 3
        assert "electrical_outlet" in service.symbol_library
        assert "hvac_duct" in service.symbol_library
        assert "water_pipe" in service.symbol_library
    
    def test_load_symbol_library(self, recognition_service):
        """Test symbol library loading."""
        library = recognition_service.symbol_library
        
        assert len(library) == 3
        assert library["electrical_outlet"]["name"] == "Electrical Outlet"
        assert library["hvac_duct"]["category"] == "mechanical"
        assert library["water_pipe"]["tags"] == ["plumbing", "pipe", "water"]
    
    def test_build_recognition_patterns(self, recognition_service):
        """Test recognition pattern building."""
        patterns = recognition_service.recognition_patterns
        
        assert "electrical_outlet" in patterns
        assert "Electrical Outlet" in patterns["electrical_outlet"]
        assert "electrical" in patterns["electrical_outlet"]
        assert "outlet" in patterns["electrical_outlet"]
        assert "power" in patterns["electrical_outlet"]
    
    def test_build_context_rules(self, recognition_service):
        """Test context rules building."""
        rules = recognition_service.context_rules
        
        assert "spatial_context" in rules
        assert "system_context" in rules
        assert "scale_context" in rules
        
        # Check specific rules
        spatial_rules = rules["spatial_context"]
        assert len(spatial_rules) == 2
        assert any(rule["rule"] == "room_contains_devices" for rule in spatial_rules)
    
    def test_build_validation_rules(self, recognition_service):
        """Test validation rules building."""
        rules = recognition_service.validation_rules
        
        assert "must_have_dimensions" in rules
        assert "must_have_material" in rules
        assert "must_have_size" in rules
        assert rules["must_have_dimensions"]["required"] is True
        assert rules["must_have_flow_rate"]["required"] is False
    
    def test_fuzzy_match_symbols_exact_match(self, recognition_service):
        """Test fuzzy matching with exact match."""
        matches = recognition_service.fuzzy_match_symbols("Electrical Outlet")
        
        assert len(matches) > 0
        assert matches[0]["symbol_id"] == "electrical_outlet"
        assert matches[0]["score"] == 1.0
    
    def test_fuzzy_match_symbols_partial_match(self, recognition_service):
        """Test fuzzy matching with partial match."""
        matches = recognition_service.fuzzy_match_symbols("outlet")
        
        assert len(matches) > 0
        assert matches[0]["symbol_id"] == "electrical_outlet"
        assert matches[0]["score"] >= 0.6
    
    def test_fuzzy_match_symbols_no_match(self, recognition_service):
        """Test fuzzy matching with no match."""
        matches = recognition_service.fuzzy_match_symbols("nonexistent")
        
        assert len(matches) == 0
    
    def test_fuzzy_match_symbols_with_threshold(self, recognition_service):
        """Test fuzzy matching with custom threshold."""
        # High threshold - should find fewer matches
        high_threshold_matches = recognition_service.fuzzy_match_symbols("electrical", threshold=0.9)
        
        # Low threshold - should find more matches
        low_threshold_matches = recognition_service.fuzzy_match_symbols("electrical", threshold=0.3)
        
        assert len(high_threshold_matches) <= len(low_threshold_matches)
    
    def test_context_aware_interpretation_success(self, recognition_service):
        """Test context-aware interpretation with valid symbol."""
        context = {
            "spatial_context": ["room_contains_devices"],
            "system_context": ["electrical_panel_near_outlets"]
        }
        
        result = recognition_service.context_aware_interpretation("electrical_outlet", context)
        
        assert result["symbol_id"] == "electrical_outlet"
        assert result["symbol"]["name"] == "Electrical Outlet"
        assert result["confidence"] > 1.0  # Should be boosted by context
    
    def test_context_aware_interpretation_symbol_not_found(self, recognition_service):
        """Test context-aware interpretation with invalid symbol."""
        context = {"spatial_context": ["room_contains_devices"]}
        
        with pytest.raises(RecognitionError, match="Symbol 'nonexistent' not found"):
            recognition_service.context_aware_interpretation("nonexistent", context)
    
    def test_context_aware_interpretation_no_context(self, recognition_service):
        """Test context-aware interpretation without context."""
        result = recognition_service.context_aware_interpretation("electrical_outlet", {})
        
        assert result["symbol_id"] == "electrical_outlet"
        assert result["confidence"] == 1.0  # No boost without context
    
    def test_validate_symbol_success(self, recognition_service):
        """Test symbol validation with valid properties."""
        properties = {
            "must_have_dimensions": "10x20",
            "must_have_material": "steel"
        }
        
        result = recognition_service.validate_symbol("electrical_outlet", properties)
        
        assert result["symbol_id"] == "electrical_outlet"
        assert result["valid"] is True
        assert len(result["errors"]) == 0
    
    def test_validate_symbol_missing_required(self, recognition_service):
        """Test symbol validation with missing required properties."""
        properties = {
            "must_have_dimensions": "10x20"
            # Missing must_have_material
        }
        
        result = recognition_service.validate_symbol("electrical_outlet", properties)
        
        assert result["symbol_id"] == "electrical_outlet"
        assert result["valid"] is False
        assert len(result["errors"]) == 1
        assert "Missing required property: must_have_material" in result["errors"]
    
    def test_validate_symbol_symbol_not_found(self, recognition_service):
        """Test symbol validation with invalid symbol."""
        properties = {"must_have_dimensions": "10x20"}
        
        with pytest.raises(RecognitionError, match="Symbol 'nonexistent' not found"):
            recognition_service.validate_symbol("nonexistent", properties)
    
    def test_recognize_symbols_in_text(self, recognition_service):
        """Test symbol recognition in text content."""
        text = "The building has electrical outlets and HVAC ducts."
        
        results = recognition_service.recognize_symbols_in_text(text)
        
        assert len(results) > 0
        # Should recognize "electrical" and "outlets" as matching electrical_outlet
        # Should recognize "hvac" and "ducts" as matching hvac_duct
    
    def test_recognize_symbols_in_text_no_matches(self, recognition_service):
        """Test symbol recognition in text with no matches."""
        text = "This text contains no symbol references."
        
        results = recognition_service.recognize_symbols_in_text(text)
        
        assert len(results) == 0
    
    def test_recognize_symbols_in_svgx(self, recognition_service):
        """Test symbol recognition in SVGX content."""
        svgx_content = {
            "svgx_elements": [
                {
                    "id": "element_001",
                    "name": "Electrical Outlet",
                    "type": "electrical"
                },
                {
                    "id": "element_002",
                    "name": "HVAC Duct",
                    "type": "mechanical"
                }
            ]
        }
        
        results = recognition_service.recognize_symbols_in_svgx(svgx_content)
        
        assert len(results) == 2
        assert results[0]["element"]["name"] == "Electrical Outlet"
        assert results[0]["symbol_match"]["symbol_id"] == "electrical_outlet"
        assert results[1]["element"]["name"] == "HVAC Duct"
        assert results[1]["symbol_match"]["symbol_id"] == "hvac_duct"
    
    def test_recognize_symbols_in_svgx_no_matches(self, recognition_service):
        """Test symbol recognition in SVGX content with no matches."""
        svgx_content = {
            "svgx_elements": [
                {
                    "id": "element_001",
                    "name": "Unknown Element",
                    "type": "unknown"
                }
            ]
        }
        
        results = recognition_service.recognize_symbols_in_svgx(svgx_content)
        
        assert len(results) == 0
    
    def test_get_symbol_metadata_success(self, recognition_service):
        """Test getting symbol metadata."""
        metadata = recognition_service.get_symbol_metadata("electrical_outlet")
        
        assert metadata is not None
        assert metadata["name"] == "Electrical Outlet"
        assert metadata["category"] == "electrical"
        assert "electrical" in metadata["tags"]
    
    def test_get_symbol_metadata_not_found(self, recognition_service):
        """Test getting metadata for non-existent symbol."""
        metadata = recognition_service.get_symbol_metadata("nonexistent")
        
        assert metadata is None


class TestSVGXSymbolRecognitionServiceConvenienceFunction:
    """Test the convenience function for creating recognition services."""
    
    def test_create_svgx_symbol_recognition_service_default(self):
        """Test creating recognition service with default symbol manager."""
        service = create_svgx_symbol_recognition_service()
        assert isinstance(service, SVGXSymbolRecognitionService)
    
    def test_create_svgx_symbol_recognition_service_custom_manager(self, mock_symbol_manager):
        """Test creating recognition service with custom symbol manager."""
        service = create_svgx_symbol_recognition_service(mock_symbol_manager)
        assert isinstance(service, SVGXSymbolRecognitionService)
        assert service.symbol_manager == mock_symbol_manager


if __name__ == "__main__":
    pytest.main([__file__]) 