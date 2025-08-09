#!/usr/bin/env python3
"""
Test suite for SVGX Engine Symbol Schema Validation Service.

Tests comprehensive schema validation features including:
- XML and JSON schema validation
- Custom validation rules
- Schema versioning
- Validation caching
- Performance monitoring
- SVGX-specific validations
- Error handling and reporting
"""

import pytest
import tempfile
import shutil
import os
import json
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any, List

# Add the parent directory to the path for imports
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from svgx_engine.services.symbol_schema_validation import (
    SVGXSymbolSchemaValidationService,
    ValidationRule,
    ValidationResult,
    SchemaVersion,
    ValidationCache,
    create_symbol_schema_validation_service
)
from svgx_engine.utils.errors import (
    ValidationError,
    SchemaError,
    SVGXError,
    PerformanceError
)


class TestSymbolSchemaValidationService:
    """Test suite for Symbol Schema Validation Service."""

    @pytest.fixture
def temp_dir(self):
        """Create a temporary directory for testing."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)

    @pytest.fixture
def service(self, temp_dir):
        """Create a Symbol Schema Validation Service instance."""
        options = {
            'enable_caching': True,
            'cache_ttl_seconds': 60,
            'max_cache_size': 100,
            'enable_performance_monitoring': True,
            'validation_timeout_seconds': 10,
            'max_concurrent_validations': 5,
            'enable_schema_versioning': True,
            'default_schema_version': '1.0.0',
            'svgx_validation_enabled': True,
            'custom_rules_enabled': True,
            'performance_optimization': True,
        }

        # Override database paths to use temp directory
        with patch('services.symbol_schema_validation.SymbolSchemaValidationService._init_databases') as mock_init:
            service = SVGXSymbolSchemaValidationService(options)
            # Manually set database paths to temp directory
            service.validation_db_path = os.path.join(temp_dir, 'validation.db')
            service.schema_db_path = os.path.join(temp_dir, 'schema.db')
            service.cache_db_path = os.path.join(temp_dir, 'cache.db')
            service._init_databases()
            return service

    @pytest.fixture
def sample_svgx_xml(self):
        """Sample SVGX XML content for testing."""
        return '''<?xml version="1.0" encoding="UTF-8"?>'
<svgx xmlns="http://www.svgx.org/schema/1.0">
    <metadata>
        <name>Test Symbol</name>
        <description>A test symbol for validation</description>
        <version>1.0.0</version>
        <author>Test Author</author>
        <tags>test, validation, symbol</tags>
    </metadata>
    <geometry>
        <rect x="0" y="0" width="100" height="50" fill="blue"/>
    </geometry>
    <behaviors>
        <behavior name="click" type="interaction">
            <action>highlight</action>
        </behavior>
    </behaviors>
    <physics>
        <mass>1.0</mass>
        <friction>0.1</friction>
    </physics>
</svgx>'''

    @pytest.fixture
def sample_svgx_json(self):
        """Sample SVGX JSON content for testing."""
        return json.dumps({
            "metadata": {
                "name": "Test Symbol",
                "description": "A test symbol for validation",
                "version": "1.0.0",
                "author": "Test Author",
                "tags": "test, validation, symbol"
            },
            "geometry": {
                "elements": [
                    {
                        "type": "rect",
                        "attributes": {
                            "x": 0,
                            "y": 0,
                            "width": 100,
                            "height": 50,
                            "fill": "blue"
                        }
                    }
                ]
            },
            "behaviors": {
                "actions": [
                    {
                        "name": "click",
                        "type": "interaction",
                        "action": "highlight"
                    }
                ]
            },
            "physics": {
                "mass": 1.0,
                "friction": 0.1
            }
        })

    def test_service_initialization(self, service):
        """Test service initialization."""
        assert service is not None
        assert service.options['enable_caching'] is True
        assert service.options['enable_performance_monitoring'] is True
        assert service.options['svgx_validation_enabled'] is True
        assert service.options['custom_rules_enabled'] is True
        assert len(service.schemas) > 0  # Should have default schema
        assert len(service.active_rules) > 0  # Should have default rules

    def test_validate_symbol_xml(self, service, sample_svgx_xml):
        """Test validating SVGX XML symbol."""
        symbol_id = "test_symbol_001"

        result = service.validate_symbol(
            symbol_id=symbol_id,
            content=sample_svgx_xml
        )

        assert result is not None
        assert result.symbol_id == symbol_id
        assert result.is_valid is True
        assert result.validation_time > 0
        assert result.schema_version == service.options['default_schema_version']
        assert len(result.applied_rules) > 0
        assert result.metadata['content_type'] == 'xml'

    def test_validate_symbol_json(self, service, sample_svgx_json):
        """Test validating SVGX JSON symbol."""
        symbol_id = "test_symbol_002"

        result = service.validate_symbol(
            symbol_id=symbol_id,
            content=sample_svgx_json
        )

        assert result is not None
        assert result.symbol_id == symbol_id
        assert result.is_valid is True
        assert result.validation_time > 0
        assert result.schema_version == service.options['default_schema_version']
        assert len(result.applied_rules) > 0
        assert result.metadata['content_type'] == 'json'

    def test_validate_invalid_xml(self, service):
        """Test validating invalid XML content."""
        symbol_id = "test_symbol_003"
        invalid_xml = "<svgx><invalid>content</invalid>"

        result = service.validate_symbol(
            symbol_id=symbol_id,
            content=invalid_xml
        )

        assert result is not None
        assert result.is_valid is False
        assert len(result.errors) > 0

    def test_validate_invalid_json(self, service):
        """Test validating invalid JSON content."""
        symbol_id = "test_symbol_004"
        invalid_json = '{"invalid": "json", "missing": "closing"}'

        result = service.validate_symbol(
            symbol_id=symbol_id,
            content=invalid_json
        )

        assert result is not None
        assert result.is_valid is False
        assert len(result.errors) > 0

    def test_validation_caching(self, service, sample_svgx_xml):
        """Test validation result caching."""
        symbol_id = "test_symbol_005"

        # First validation
        result1 = service.validate_symbol(
            symbol_id=symbol_id,
            content=sample_svgx_xml
        )

        # Second validation (should use cache)
        result2 = service.validate_symbol(
            symbol_id=symbol_id,
            content=sample_svgx_xml
        )

        assert result1.symbol_id == result2.symbol_id
        assert result1.is_valid == result2.is_valid

        # Check cache statistics
        stats = service.get_validation_statistics()
        assert stats['cache_hits'] > 0
        assert stats['cache_misses'] > 0

    def test_add_validation_rule(self, service):
        """Test adding a custom validation rule."""
        rule = ValidationRule(
            rule_id="test_rule_001",
            name="Test Rule",
            description="A test validation rule",
            rule_type="regex",
            schema_content=r"<svgx.*>",
            severity="warning"
        )

        success = service.add_validation_rule(rule)
        assert success is True
        assert rule.rule_id in service.active_rules

    def test_remove_validation_rule(self, service):
        """Test removing a validation rule."""
        rule = ValidationRule(
            rule_id="test_rule_002",
            name="Test Rule",
            description="A test validation rule",
            rule_type="regex",
            schema_content=r"<svgx.*>",
            severity="warning"
        )

        # Add rule
        service.add_validation_rule(rule)
        assert rule.rule_id in service.active_rules

        # Remove rule
        success = service.remove_validation_rule(rule.rule_id)
        assert success is True
        assert rule.rule_id not in service.active_rules

    def test_add_schema_version(self, service):
        """Test adding a new schema version."""
        schema = SchemaVersion(
            version="2.0.0",
            description="Test schema version",
            schema_content="<xs:schema>...</xs:schema>",
            rules=[],
            is_default=False,
            metadata={"test": "data"}
        )

        success = service.add_schema_version(schema)
        assert success is True
        assert schema.version in service.schemas

    def test_get_schema_version(self, service):
        """Test getting a schema version."""
        default_version = service.options['default_schema_version']
        schema = service.get_schema_version(default_version)

        assert schema is not None
        assert schema.version == default_version
        assert schema.is_default is True

    def test_validation_statistics(self, service, sample_svgx_xml):
        """Test getting validation statistics."""
        # Perform some validations
        for i in range(3):
            service.validate_symbol(
                symbol_id=f"test_symbol_{i}",
                content=sample_svgx_xml
            )

        stats = service.get_validation_statistics()

        assert stats['total_validations'] >= 3
        assert stats['average_validation_time'] > 0
        assert 'cache_size' in stats
        assert 'active_rules_count' in stats
        assert 'schema_versions_count' in stats

    def test_clear_cache(self, service, sample_svgx_xml):
        """Test clearing validation cache."""
        # Perform validation to populate cache
        service.validate_symbol(
            symbol_id="test_symbol_cache",
            content=sample_svgx_xml
        )

        # Clear cache
        success = service.clear_cache()
        assert success is True

        # Check cache is empty
        stats = service.get_validation_statistics()
        assert stats['cache_size'] == 0

    def test_svgx_specific_validation(self, service):
        """Test SVGX-specific validation rules."""
        # Test with valid SVGX content
        valid_svgx = '''<?xml version="1.0" encoding="UTF-8"?>'
<svgx xmlns="http://www.svgx.org/schema/1.0">
    <metadata>
        <name>Test</name>
        <version>1.0</version>
        <author>Test</author>
    </metadata>
    <geometry>
        <rect x="0" y="0" width="100" height="50"/>
    </geometry>
</svgx>'''

        result = service.validate_symbol(
            symbol_id="test_svgx_specific",
            content=valid_svgx
        )

        assert result.is_valid is True

        # Test with missing SVGX root element
        invalid_svgx = '''<?xml version="1.0" encoding="UTF-8"?>'
<svg xmlns="http://www.w3.org/2000/svg">
    <rect x="0" y="0" width="100" height="50"/>
</svg>'''

        result = service.validate_symbol(
            symbol_id="test_svgx_invalid",
            content=invalid_svgx
        )

        assert result.is_valid is False
        assert len(result.errors) > 0

    def test_custom_validation_rules(self, service):
        """Test custom validation rules."""
        # Add a custom regex rule
        rule = ValidationRule(
            rule_id="test_regex_rule",
            name="Test Regex Rule",
            description="Tests for SVGX root element",
            rule_type="regex",
            schema_content=r"<svgx[^>]*>",
            severity="error"
        )

        service.add_validation_rule(rule)

        # Test with valid content
        valid_content = "<svgx xmlns='http://www.svgx.org/schema/1.0'></svgx>"
        result = service.validate_symbol(
            symbol_id="test_custom_valid",
            content=valid_content
        )

        # Test with invalid content
        invalid_content = "<svg xmlns='http://www.w3.org/2000/svg'></svg>"
        result = service.validate_symbol(
            symbol_id="test_custom_invalid",
            content=invalid_content
        )

        assert result.is_valid is False

    def test_performance_monitoring(self, service, sample_svgx_xml):
        """Test performance monitoring integration."""
        start_time = time.time()

        result = service.validate_symbol(
            symbol_id="test_performance",
            content=sample_svgx_xml
        )

        end_time = time.time()

        # Verify performance monitoring works
        assert result.validation_time > 0
        assert result.validation_time < (end_time - start_time + 0.1)  # Allow some tolerance

        # Check performance metrics
        stats = service.get_validation_statistics()
        assert stats['average_validation_time'] > 0

    def test_error_handling(self, service):
        """Test error handling for various scenarios."""
        # Test with empty content
        with pytest.raises(ValidationError):
            service.validate_symbol(
                symbol_id="test_empty",
                content=""
            )

        # Test with None content
        with pytest.raises(ValidationError):
            service.validate_symbol(
                symbol_id="test_none",
                content=None
            )

    def test_schema_versioning(self, service):
        """Test schema versioning functionality."""
        # Create a new schema version
        new_schema = SchemaVersion(
            version="1.1.0",
            description="Updated schema version",
            schema_content="<xs:schema>updated schema</xs:schema>",
            rules=[],
            is_default=False
        )

        success = service.add_schema_version(new_schema)
        assert success is True

        # Validate with specific schema version
        result = service.validate_symbol(
            symbol_id="test_schema_version",
            content="<svgx></svgx>",
            schema_version="1.1.0"
        )

        assert result.schema_version == "1.1.0"

    def test_cleanup(self, service):
        """Test service cleanup."""
        # Add some test data
        service.validate_symbol(
            symbol_id="test_cleanup",
            content="<svgx></svgx>"
        )

        # Perform cleanup
        service.cleanup()

        # Verify cleanup completed without errors
        assert True  # If we get here, cleanup succeeded

    def test_concurrent_validations(self, service, sample_svgx_xml):
        """Test concurrent validation operations."""
        import threading

        results = []
        errors = []

        def validate_symbol(symbol_id):
            try:
                result = service.validate_symbol(
                    symbol_id=symbol_id,
                    content=sample_svgx_xml
                )
                results.append(result)
            except Exception as e:
                errors.append(e)

        # Start multiple validation threads
        threads = []
        for i in range(5):
            thread = threading.Thread(
                target=validate_symbol,
                args=(f"concurrent_symbol_{i}",)
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Verify all validations completed
        assert len(results) == 5
        assert len(errors) == 0

        for result in results:
            assert result.is_valid is True


class TestValidationRule:
    """Test suite for ValidationRule dataclass."""

    def test_validation_rule_creation(self):
        """Test creating a ValidationRule instance."""
        rule = ValidationRule(
            rule_id="test_rule",
            name="Test Rule",
            description="A test validation rule",
            rule_type="regex",
            schema_content=r"<svgx.*>",
            severity="warning",
            is_active=True
        )

        assert rule.rule_id == "test_rule"
        assert rule.name == "Test Rule"
        assert rule.description == "A test validation rule"
        assert rule.rule_type == "regex"
        assert rule.schema_content == r"<svgx.*>"
        assert rule.severity == "warning"
        assert rule.is_active is True


class TestValidationResult:
    """Test suite for ValidationResult dataclass."""

    def test_validation_result_creation(self):
        """Test creating a ValidationResult instance."""
        result = ValidationResult(
            symbol_id="test_symbol",
            is_valid=True,
            errors=[],
            warnings=[{"message": "Test warning"}],
            info=[{"message": "Test info"}],
            validation_time=0.1,
            schema_version="1.0.0",
            applied_rules=["xml_schema_validation"],
            metadata={"test": "data"}
        )

        assert result.symbol_id == "test_symbol"
        assert result.is_valid is True
        assert len(result.errors) == 0
        assert len(result.warnings) == 1
        assert len(result.info) == 1
        assert result.validation_time == 0.1
        assert result.schema_version == "1.0.0"
        assert result.applied_rules == ["xml_schema_validation"]
        assert result.metadata == {"test": "data"}


class TestSchemaVersion:
    """Test suite for SchemaVersion dataclass."""

    def test_schema_version_creation(self):
        """Test creating a SchemaVersion instance."""
        schema = SchemaVersion(
            version="1.0.0",
            description="Test schema",
            schema_content="<xs:schema>...</xs:schema>",
            rules=[],
            is_default=True,
            metadata={"test": "data"}
        )

        assert schema.version == "1.0.0"
        assert schema.description == "Test schema"
        assert schema.schema_content == "<xs:schema>...</xs:schema>"
        assert len(schema.rules) == 0
        assert schema.is_default is True
        assert schema.metadata == {"test": "data"}


class TestValidationCache:
    """Test suite for ValidationCache dataclass."""

    def test_validation_cache_creation(self):
        """Test creating a ValidationCache instance."""
        result = ValidationResult(
            symbol_id="test",
            is_valid=True,
            errors=[],
            warnings=[],
            info=[],
            validation_time=0.1,
            schema_version="1.0.0",
            applied_rules=[],
            metadata={}
        )

        cache = ValidationCache(
            symbol_hash="abc123",
            schema_version="1.0.0",
            validation_result=result,
            cached_at=datetime.now(),
            expires_at=datetime.now() + timedelta(hours=1)
        assert cache.symbol_hash == "abc123"
        assert cache.schema_version == "1.0.0"
        assert cache.validation_result == result
        assert cache.cached_at is not None
        assert cache.expires_at is not None


def test_create_symbol_schema_validation_service():
    """Test creating a service instance using the factory function."""
    service = create_symbol_schema_validation_service()

    assert service is not None
    assert isinstance(service, SVGXSymbolSchemaValidationService)
    assert service.options['enable_caching'] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
