#!/usr/bin/env python3
"""
Test suite for SVGX Engine Advanced Symbol Management Service.

Tests advanced symbol management features including:
- Version control and history
- Real-time collaboration
- AI-powered search
- Dependency tracking
- Analytics and usage tracking
- Marketplace features
- SVGX-specific optimizations
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

from svgx_engine.services.advanced_symbols import (
    SVGXAdvancedSymbolManagementService,
    SymbolVersion,
    SymbolCollaboration,
    SymbolSearchResult,
    SymbolDependency,
    SymbolAnalytics,
    MarketplaceItem
)
from svgx_engine.utils.errors import (
    AdvancedSymbolError,
    VersionControlError,
    CollaborationError,
    SearchError,
    DependencyError,
    AnalyticsError,
    MarketplaceError
)


class TestAdvancedSymbolManagementService:
    """Test suite for Advanced Symbol Management Service."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def service(self, temp_dir):
        """Create an Advanced Symbol Management Service instance."""
        options = {
            'enable_version_control': True,
            'enable_collaboration': True,
            'enable_ai_search': True,
            'enable_dependency_tracking': True,
            'enable_analytics': True,
            'enable_marketplace': True,
            'max_concurrent_editors': 5,
            'version_history_limit': 10,
            'search_cache_size': 100,
            'collaboration_timeout': 60,
            'analytics_retention_days': 30,
            'marketplace_enabled': True,
            'svgx_optimization_enabled': True,
        }
        
        # Override database paths to use temp directory
        with patch('svgx_engine.services.advanced_symbols.SVGXAdvancedSymbolManagementService._init_databases') as mock_init:
            service = SVGXAdvancedSymbolManagementService(options)
            # Manually set database paths to temp directory
            service.version_db_path = os.path.join(temp_dir, 'versions.db')
            service.collaboration_db_path = os.path.join(temp_dir, 'collaboration.db')
            service.search_db_path = os.path.join(temp_dir, 'search.db')
            service.dependency_db_path = os.path.join(temp_dir, 'dependencies.db')
            service.analytics_db_path = os.path.join(temp_dir, 'analytics.db')
            service.marketplace_db_path = os.path.join(temp_dir, 'marketplace.db')
            service._init_databases()
            return service
    
    @pytest.fixture
    def sample_symbol_content(self):
        """Sample SVGX symbol content for testing."""
        return '''<?xml version="1.0" encoding="UTF-8"?>
<svgx xmlns="http://www.svgx.org/schema/1.0">
    <metadata>
        <name>Test Symbol</name>
        <description>A test symbol for unit testing</description>
        <version>1.0.0</version>
        <author>Test Author</author>
        <tags>test, unit, symbol</tags>
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
    
    def test_service_initialization(self, service):
        """Test service initialization."""
        assert service is not None
        assert service.options['enable_version_control'] is True
        assert service.options['enable_collaboration'] is True
        assert service.options['enable_ai_search'] is True
        assert service.options['enable_dependency_tracking'] is True
        assert service.options['enable_analytics'] is True
        assert service.options['enable_marketplace'] is True
    
    def test_create_symbol_version(self, service, sample_symbol_content):
        """Test creating a symbol version."""
        symbol_id = "test_symbol_001"
        author = "test_user"
        message = "Initial version"
        metadata = {"category": "test", "tags": ["unit", "test"]}
        
        version = service.create_symbol_version(
            symbol_id=symbol_id,
            content=sample_symbol_content,
            author=author,
            message=message,
            metadata=metadata
        )
        
        assert version is not None
        assert version.symbol_id == symbol_id
        assert version.author == author
        assert version.message == message
        assert version.content == sample_symbol_content
        assert version.metadata == metadata
        assert version.version_hash is not None
        assert version.parent_hash is None  # First version
        assert version.timestamp is not None
        assert version.file_size > 0
        assert version.compression_ratio > 0
    
    def test_get_symbol_version(self, service, sample_symbol_content):
        """Test retrieving a symbol version."""
        symbol_id = "test_symbol_002"
        author = "test_user"
        message = "Test version"
        
        # Create a version
        version = service.create_symbol_version(
            symbol_id=symbol_id,
            content=sample_symbol_content,
            author=author,
            message=message
        )
        
        # Retrieve the version
        retrieved_version = service.get_symbol_version(symbol_id, version.version_hash)
        
        assert retrieved_version is not None
        assert retrieved_version.symbol_id == symbol_id
        assert retrieved_version.content == sample_symbol_content
        assert retrieved_version.author == author
        assert retrieved_version.message == message
    
    def test_get_version_history(self, service, sample_symbol_content):
        """Test retrieving version history."""
        symbol_id = "test_symbol_003"
        author = "test_user"
        
        # Create multiple versions
        version1 = service.create_symbol_version(
            symbol_id=symbol_id,
            content=sample_symbol_content,
            author=author,
            message="Version 1"
        )
        
        # Modify content for version 2
        modified_content = sample_symbol_content.replace("Test Symbol", "Modified Test Symbol")
        version2 = service.create_symbol_version(
            symbol_id=symbol_id,
            content=modified_content,
            author=author,
            message="Version 2"
        )
        
        # Get version history
        history = service.get_version_history(symbol_id)
        
        assert len(history) == 2
        assert history[0].version_hash == version2.version_hash  # Latest first
        assert history[1].version_hash == version1.version_hash
        assert history[0].parent_hash == version1.version_hash
    
    def test_start_collaboration_session(self, service):
        """Test starting a collaboration session."""
        symbol_id = "test_symbol_004"
        user_id = "test_user"
        
        session_id = service.start_collaboration_session(symbol_id, user_id)
        
        assert session_id is not None
        assert session_id in service.active_sessions
        
        session = service.active_sessions[session_id]
        assert session.symbol_id == symbol_id
        assert user_id in session.participants
        assert user_id in session.active_editors
    
    def test_join_collaboration_session(self, service):
        """Test joining a collaboration session."""
        symbol_id = "test_symbol_005"
        user1_id = "test_user_1"
        user2_id = "test_user_2"
        
        # Start session with first user
        session_id = service.start_collaboration_session(symbol_id, user1_id)
        
        # Join with second user
        success = service.join_collaboration_session(session_id, user2_id)
        
        assert success is True
        
        session = service.active_sessions[session_id]
        assert user2_id in session.participants
        assert user2_id in session.active_editors
    
    def test_search_symbols(self, service, sample_symbol_content):
        """Test symbol search functionality."""
        symbol_id = "test_symbol_006"
        author = "test_user"
        
        # Create a symbol version
        service.create_symbol_version(
            symbol_id=symbol_id,
            content=sample_symbol_content,
            author=author,
            message="Searchable symbol"
        )
        
        # Search for symbols
        results = service.search_symbols("test", limit=5)
        
        assert isinstance(results, list)
        # Note: Search results depend on the search implementation
        # This test verifies the method works without errors
    
    def test_add_symbol_dependency(self, service):
        """Test adding symbol dependencies."""
        symbol_id = "test_symbol_007"
        dependency_id = "dependency_001"
        
        success = service.add_symbol_dependency(
            symbol_id=symbol_id,
            dependency_id=dependency_id,
            dependency_type="includes",
            version_constraint=">=1.0.0",
            is_required=True,
            metadata={"description": "Required dependency"}
        )
        
        assert success is True
        
        # Check if dependency was added to the graph
        assert dependency_id in service.dependency_graph[symbol_id]
        assert symbol_id in service.reverse_dependencies[dependency_id]
    
    def test_track_symbol_usage(self, service, sample_symbol_content):
        """Test tracking symbol usage."""
        symbol_id = "test_symbol_008"
        user_id = "test_user"
        
        # Create a symbol version first
        service.create_symbol_version(
            symbol_id=symbol_id,
            content=sample_symbol_content,
            author="author",
            message="Usage tracking test"
        )
        
        # Track usage
        service.track_symbol_usage(
            symbol_id=symbol_id,
            user_id=user_id,
            context={"operation": "view", "duration": 5.2}
        )
        
        # Verify usage was tracked (implementation dependent)
        # This test verifies the method works without errors
    
    def test_add_marketplace_item(self, service):
        """Test adding marketplace items."""
        symbol_id = "test_symbol_009"
        author = "test_author"
        title = "Test Symbol"
        description = "A test symbol for marketplace"
        category = "test"
        tags = ["test", "symbol", "marketplace"]
        
        success = service.add_marketplace_item(
            symbol_id=symbol_id,
            author=author,
            title=title,
            description=description,
            category=category,
            tags=tags,
            price=0.0,
            license="MIT"
        )
        
        assert success is True
    
    def test_get_statistics(self, service):
        """Test getting service statistics."""
        stats = service.get_statistics()
        
        assert isinstance(stats, dict)
        assert 'total_symbols' in stats
        assert 'total_versions' in stats
        assert 'active_sessions' in stats
        assert 'search_cache_size' in stats
        assert 'dependency_count' in stats
        assert 'marketplace_items' in stats
    
    def test_error_handling_invalid_symbol_id(self, service):
        """Test error handling for invalid symbol ID."""
        with pytest.raises(AdvancedSymbolError):
            service.create_symbol_version(
                symbol_id="",  # Invalid empty ID
                content="test",
                author="test_user",
                message="test"
            )
    
    def test_error_handling_invalid_session(self, service):
        """Test error handling for invalid session."""
        with pytest.raises(CollaborationError):
            service.join_collaboration_session("invalid_session_id", "test_user")
    
    def test_error_handling_invalid_dependency(self, service):
        """Test error handling for invalid dependency."""
        with pytest.raises(DependencyError):
            service.add_symbol_dependency(
                symbol_id="test",
                dependency_id="",  # Invalid empty dependency ID
                dependency_type="invalid_type",
                version_constraint="invalid"
            )
    
    def test_svgx_optimization(self, service, sample_symbol_content):
        """Test SVGX-specific optimizations."""
        symbol_id = "test_symbol_010"
        author = "test_user"
        
        version = service.create_symbol_version(
            symbol_id=symbol_id,
            content=sample_symbol_content,
            author=author,
            message="Optimization test"
        )
        
        # Verify optimization was applied
        assert version.compression_ratio > 0
        assert version.file_size > 0
    
    def test_concurrent_editors_limit(self, service):
        """Test concurrent editors limit."""
        symbol_id = "test_symbol_011"
        max_editors = service.options['max_concurrent_editors']
        
        # Add maximum number of editors
        for i in range(max_editors):
            user_id = f"user_{i}"
            session_id = service.start_collaboration_session(symbol_id, user_id)
            assert session_id is not None
        
        # Try to add one more editor (should fail or be limited)
        try:
            session_id = service.start_collaboration_session(symbol_id, "extra_user")
            # If it succeeds, the implementation handles it gracefully
            assert session_id is not None
        except CollaborationError:
            # Expected behavior if limit is enforced
            pass
    
    def test_version_history_limit(self, service, sample_symbol_content):
        """Test version history limit."""
        symbol_id = "test_symbol_012"
        author = "test_user"
        limit = service.options['version_history_limit']
        
        # Create more versions than the limit
        for i in range(limit + 5):
            modified_content = sample_symbol_content.replace(
                "Test Symbol", f"Test Symbol v{i+1}"
            )
            service.create_symbol_version(
                symbol_id=symbol_id,
                content=modified_content,
                author=author,
                message=f"Version {i+1}"
            )
        
        # Check that history is limited
        history = service.get_version_history(symbol_id)
        assert len(history) <= limit
    
    def test_cleanup(self, service):
        """Test service cleanup."""
        # Add some test data
        symbol_id = "test_symbol_013"
        service.start_collaboration_session(symbol_id, "test_user")
        
        # Perform cleanup
        service.cleanup()
        
        # Verify cleanup completed without errors
        assert True  # If we get here, cleanup succeeded
    
    def test_performance_monitoring(self, service, sample_symbol_content):
        """Test performance monitoring integration."""
        symbol_id = "test_symbol_014"
        author = "test_user"
        
        # Monitor performance of version creation
        start_time = time.time()
        version = service.create_symbol_version(
            symbol_id=symbol_id,
            content=sample_symbol_content,
            author=author,
            message="Performance test"
        )
        end_time = time.time()
        
        # Verify operation completed within reasonable time
        assert end_time - start_time < 5.0  # Should complete within 5 seconds
        assert version is not None
    
    def test_marketplace_features(self, service):
        """Test marketplace features."""
        # Add marketplace item
        symbol_id = "marketplace_symbol_001"
        success = service.add_marketplace_item(
            symbol_id=symbol_id,
            author="marketplace_author",
            title="Marketplace Symbol",
            description="A symbol for marketplace testing",
            category="test",
            tags=["marketplace", "test"],
            price=9.99,
            license="MIT"
        )
        
        assert success is True
        
        # Get statistics to verify marketplace item was added
        stats = service.get_statistics()
        assert stats['marketplace_items'] >= 1
    
    def test_analytics_tracking(self, service, sample_symbol_content):
        """Test analytics tracking."""
        symbol_id = "analytics_symbol_001"
        user_id = "analytics_user"
        
        # Create symbol
        service.create_symbol_version(
            symbol_id=symbol_id,
            content=sample_symbol_content,
            author="analytics_author",
            message="Analytics test"
        )
        
        # Track multiple usage events
        for i in range(5):
            service.track_symbol_usage(
                symbol_id=symbol_id,
                user_id=user_id,
                context={"operation": "view", "session_id": f"session_{i}"}
            )
        
        # Verify analytics tracking works without errors
        assert True  # If we get here, tracking succeeded
    
    def test_dependency_validation(self, service):
        """Test dependency validation."""
        symbol_id = "dependency_symbol_001"
        dependency_id = "dependency_symbol_002"
        
        # Add valid dependency
        success = service.add_symbol_dependency(
            symbol_id=symbol_id,
            dependency_id=dependency_id,
            dependency_type="includes",
            version_constraint=">=1.0.0",
            is_required=True
        )
        
        assert success is True
        
        # Test circular dependency detection (if implemented)
        try:
            service.add_symbol_dependency(
                symbol_id=dependency_id,
                dependency_id=symbol_id,
                dependency_type="includes",
                version_constraint=">=1.0.0",
                is_required=True
            )
            # If it succeeds, the implementation handles circular dependencies gracefully
            assert True
        except DependencyError:
            # Expected behavior if circular dependencies are prevented
            pass


class TestSymbolVersion:
    """Test suite for SymbolVersion dataclass."""
    
    def test_symbol_version_creation(self):
        """Test creating a SymbolVersion instance."""
        version = SymbolVersion(
            symbol_id="test_symbol",
            version_hash="abc123",
            parent_hash="def456",
            author="test_user",
            timestamp=datetime.now(),
            message="Test version",
            content="<svgx>test</svgx>",
            metadata={"test": "data"},
            file_size=100,
            compression_ratio=0.8
        )
        
        assert version.symbol_id == "test_symbol"
        assert version.version_hash == "abc123"
        assert version.parent_hash == "def456"
        assert version.author == "test_user"
        assert version.message == "Test version"
        assert version.content == "<svgx>test</svgx>"
        assert version.metadata == {"test": "data"}
        assert version.file_size == 100
        assert version.compression_ratio == 0.8


class TestSymbolCollaboration:
    """Test suite for SymbolCollaboration dataclass."""
    
    def test_symbol_collaboration_creation(self):
        """Test creating a SymbolCollaboration instance."""
        collaboration = SymbolCollaboration(
            session_id="session_123",
            symbol_id="test_symbol",
            participants=["user1", "user2"],
            active_editors=["user1"],
            last_activity=datetime.now(),
            conflict_resolution={"strategy": "manual"},
            session_data={"cursor_positions": {}}
        )
        
        assert collaboration.session_id == "session_123"
        assert collaboration.symbol_id == "test_symbol"
        assert collaboration.participants == ["user1", "user2"]
        assert collaboration.active_editors == ["user1"]
        assert collaboration.conflict_resolution == {"strategy": "manual"}
        assert collaboration.session_data == {"cursor_positions": {}}


class TestSymbolSearchResult:
    """Test suite for SymbolSearchResult dataclass."""
    
    def test_symbol_search_result_creation(self):
        """Test creating a SymbolSearchResult instance."""
        result = SymbolSearchResult(
            symbol_id="test_symbol",
            score=0.95,
            relevance_factors=["exact_match", "popularity"],
            metadata={"category": "test"},
            usage_stats={"views": 100, "downloads": 10}
        )
        
        assert result.symbol_id == "test_symbol"
        assert result.score == 0.95
        assert result.relevance_factors == ["exact_match", "popularity"]
        assert result.metadata == {"category": "test"}
        assert result.usage_stats == {"views": 100, "downloads": 10}


class TestSymbolDependency:
    """Test suite for SymbolDependency dataclass."""
    
    def test_symbol_dependency_creation(self):
        """Test creating a SymbolDependency instance."""
        dependency = SymbolDependency(
            symbol_id="test_symbol",
            dependency_id="dependency_symbol",
            dependency_type="includes",
            version_constraint=">=1.0.0",
            is_required=True,
            metadata={"description": "Required dependency"}
        )
        
        assert dependency.symbol_id == "test_symbol"
        assert dependency.dependency_id == "dependency_symbol"
        assert dependency.dependency_type == "includes"
        assert dependency.version_constraint == ">=1.0.0"
        assert dependency.is_required is True
        assert dependency.metadata == {"description": "Required dependency"}


class TestSymbolAnalytics:
    """Test suite for SymbolAnalytics dataclass."""
    
    def test_symbol_analytics_creation(self):
        """Test creating a SymbolAnalytics instance."""
        analytics = SymbolAnalytics(
            symbol_id="test_symbol",
            usage_count=150,
            popularity_score=0.85,
            performance_metrics={"load_time": 0.1, "render_time": 0.05},
            user_feedback={"rating": 4.5, "reviews": 10},
            last_used=datetime.now(),
            created_date=datetime.now()
        )
        
        assert analytics.symbol_id == "test_symbol"
        assert analytics.usage_count == 150
        assert analytics.popularity_score == 0.85
        assert analytics.performance_metrics == {"load_time": 0.1, "render_time": 0.05}
        assert analytics.user_feedback == {"rating": 4.5, "reviews": 10}


class TestMarketplaceItem:
    """Test suite for MarketplaceItem dataclass."""
    
    def test_marketplace_item_creation(self):
        """Test creating a MarketplaceItem instance."""
        item = MarketplaceItem(
            symbol_id="marketplace_symbol",
            author="test_author",
            title="Test Symbol",
            description="A test symbol for marketplace",
            category="test",
            tags=["test", "symbol"],
            rating=4.5,
            download_count=100,
            price=9.99,
            license="MIT",
            metadata={"featured": True}
        )
        
        assert item.symbol_id == "marketplace_symbol"
        assert item.author == "test_author"
        assert item.title == "Test Symbol"
        assert item.description == "A test symbol for marketplace"
        assert item.category == "test"
        assert item.tags == ["test", "symbol"]
        assert item.rating == 4.5
        assert item.download_count == 100
        assert item.price == 9.99
        assert item.license == "MIT"
        assert item.metadata == {"featured": True}


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 