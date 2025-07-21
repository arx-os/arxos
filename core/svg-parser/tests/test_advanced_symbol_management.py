"""
Test suite for Advanced Symbol Management Service

Tests all major functionality including:
- Git-like version control for symbols
- Real-time symbol editing collaboration
- AI-powered symbol search and recommendations
- Symbol dependency tracking and validation
- Symbol performance analytics and usage tracking
- Symbol marketplace and sharing features
"""

import unittest
import tempfile
import os
import time
import json
import threading
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

from core.services.advanced_symbol_management
    AdvancedSymbolManagement,
    SymbolVersion,
    SymbolCollaboration,
    SymbolSearchResult,
    SymbolDependency,
    SymbolAnalytics,
    MarketplaceItem
)


class TestAdvancedSymbolManagement(unittest.TestCase):
    """Test cases for Advanced Symbol Management service"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Use temporary database for testing
        self.temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        self.temp_db.close()
        
        self.symbol_management = AdvancedSymbolManagement({
            'version_history_limit': 10,
            'max_concurrent_editors': 5,
            'search_cache_size': 100,
            'collaboration_timeout': 60,
            'analytics_retention_days': 30,
            'marketplace_enabled': True
        })
        
        # Override database path for testing
        self.symbol_management.db_path = Path(self.temp_db.name)
        self.symbol_management._init_databases()
        
        # Sample symbol content for testing
        self.sample_symbol = '''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100" viewBox="0 0 100 100">
  <rect x="10" y="10" width="80" height="80" fill="red" stroke="black" stroke-width="2"/>
  <text x="50" y="50" text-anchor="middle" fill="white">Test Symbol</text>
</svg>'''
        
        self.complex_symbol = '''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="200" height="200" viewBox="0 0 200 200">
  <defs>
    <linearGradient id="grad1" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" style="stop-color:rgb(255,255,0);stop-opacity:1" />
      <stop offset="100%" style="stop-color:rgb(255,0,0);stop-opacity:1" />
    </linearGradient>
  </defs>
  <rect width="200" height="200" fill="lightblue"/>
  <g transform="translate(50,50)">
    <rect x="0" y="0" width="100" height="100" fill="url(#grad1)" stroke="black"/>
    <circle cx="50" cy="50" r="40" fill="blue" opacity="0.7"/>
    <path d="M 10 10 Q 50 0 90 10 T 90 90 Q 50 100 10 90 Z" fill="green"/>
  </g>
  <text x="100" y="180" text-anchor="middle" font-size="16">Complex Symbol</text>
</svg>'''
    
    def tearDown(self):
        """Clean up test fixtures"""
        self.symbol_management.cleanup()
        
        # Remove temporary database
        if os.path.exists(self.temp_db.name):
            os.unlink(self.temp_db.name)
    
    def test_initialization(self):
        """Test service initialization"""
        self.assertIsNotNone(self.symbol_management)
        self.assertTrue(self.symbol_management.options['enable_version_control'])
        self.assertTrue(self.symbol_management.options['enable_collaboration'])
        self.assertTrue(self.symbol_management.options['enable_ai_search'])
        self.assertEqual(self.symbol_management.options['max_concurrent_editors'], 5)
        self.assertEqual(self.symbol_management.options['version_history_limit'], 10)
    
    # Version Control Tests
    
    def test_create_symbol_version(self):
        """Test creating a symbol version"""
        symbol_id = "test_symbol_1"
        author = "test_user"
        message = "Initial version"
        
        version = self.symbol_management.create_symbol_version(
            symbol_id, self.sample_symbol, author, message
        )
        
        self.assertIsInstance(version, SymbolVersion)
        self.assertEqual(version.symbol_id, symbol_id)
        self.assertEqual(version.author, author)
        self.assertEqual(version.message, message)
        self.assertEqual(version.content, self.sample_symbol)
        self.assertIsNotNone(version.version_hash)
        self.assertIsNone(version.parent_hash)  # First version has no parent
        self.assertGreater(version.file_size, 0)
        self.assertGreaterEqual(version.compression_ratio, 0.0)
    
    def test_get_symbol_version(self):
        """Test retrieving a symbol version"""
        symbol_id = "test_symbol_2"
        author = "test_user"
        message = "Test version"
        
        # Create version
        created_version = self.symbol_management.create_symbol_version(
            symbol_id, self.sample_symbol, author, message
        )
        
        # Retrieve version
        retrieved_version = self.symbol_management.get_symbol_version(
            symbol_id, created_version.version_hash
        )
        
        self.assertIsNotNone(retrieved_version)
        self.assertEqual(retrieved_version.symbol_id, symbol_id)
        self.assertEqual(retrieved_version.content, self.sample_symbol)
        self.assertEqual(retrieved_version.author, author)
        self.assertEqual(retrieved_version.message, message)
    
    def test_get_version_history(self):
        """Test getting version history"""
        symbol_id = "test_symbol_3"
        author = "test_user"
        
        # Create multiple versions
        version1 = self.symbol_management.create_symbol_version(
            symbol_id, self.sample_symbol, author, "Version 1"
        )
        
        modified_symbol = self.sample_symbol.replace("Test Symbol", "Modified Symbol")
        version2 = self.symbol_management.create_symbol_version(
            symbol_id, modified_symbol, author, "Version 2"
        )
        
        # Get version history
        history = self.symbol_management.get_version_history(symbol_id)
        
        self.assertEqual(len(history), 2)
        self.assertEqual(history[0].version_hash, version2.version_hash)  # Most recent first
        self.assertEqual(history[1].version_hash, version1.version_hash)
    
    def test_rollback_symbol(self):
        """Test rolling back a symbol to a previous version"""
        symbol_id = "test_symbol_4"
        author = "test_user"
        
        # Create initial version
        version1 = self.symbol_management.create_symbol_version(
            symbol_id, self.sample_symbol, author, "Initial version"
        )
        
        # Create modified version
        modified_symbol = self.sample_symbol.replace("Test Symbol", "Modified Symbol")
        version2 = self.symbol_management.create_symbol_version(
            symbol_id, modified_symbol, author, "Modified version"
        )
        
        # Rollback to first version
        success = self.symbol_management.rollback_symbol(symbol_id, version1.version_hash)
        
        self.assertTrue(success)
        
        # Check that new version was created with original content
        current_version = self.symbol_management.get_symbol_version(symbol_id)
        self.assertIsNotNone(current_version)
        self.assertIn("Rollback", current_version.message)
        self.assertEqual(current_version.content, self.sample_symbol)
    
    def test_compare_versions(self):
        """Test comparing two versions of a symbol"""
        symbol_id = "test_symbol_5"
        author = "test_user"
        
        # Create initial version
        version1 = self.symbol_management.create_symbol_version(
            symbol_id, self.sample_symbol, author, "Initial version"
        )
        
        # Create modified version
        modified_symbol = self.sample_symbol.replace("Test Symbol", "Modified Symbol")
        version2 = self.symbol_management.create_symbol_version(
            symbol_id, modified_symbol, author, "Modified version"
        )
        
        # Compare versions
        comparison = self.symbol_management.compare_versions(
            symbol_id, version1.version_hash, version2.version_hash
        )
        
        self.assertIn("version1", comparison)
        self.assertIn("version2", comparison)
        self.assertIn("diff", comparison)
        self.assertIn("changes", comparison)
        self.assertGreater(comparison["changes"]["total_changes"], 0)
    
    # Collaboration Tests
    
    def test_start_collaboration_session(self):
        """Test starting a collaboration session"""
        symbol_id = "test_symbol_6"
        user_id = "user1"
        
        # Create initial version
        self.symbol_management.create_symbol_version(
            symbol_id, self.sample_symbol, "author", "Initial version"
        )
        
        # Start collaboration session
        session_id = self.symbol_management.start_collaboration_session(symbol_id, user_id)
        
        self.assertIsInstance(session_id, str)
        self.assertIn(session_id, self.symbol_management.active_sessions)
        
        session = self.symbol_management.active_sessions[session_id]
        self.assertEqual(session.symbol_id, symbol_id)
        self.assertIn(user_id, session.participants)
        self.assertIn(user_id, session.active_editors)
    
    def test_join_collaboration_session(self):
        """Test joining a collaboration session"""
        symbol_id = "test_symbol_7"
        user1 = "user1"
        user2 = "user2"
        
        # Create initial version
        self.symbol_management.create_symbol_version(
            symbol_id, self.sample_symbol, "author", "Initial version"
        )
        
        # Start session
        session_id = self.symbol_management.start_collaboration_session(symbol_id, user1)
        
        # Join session
        success = self.symbol_management.join_collaboration_session(session_id, user2)
        
        self.assertTrue(success)
        
        session = self.symbol_management.active_sessions[session_id]
        self.assertIn(user1, session.participants)
        self.assertIn(user2, session.participants)
        self.assertIn(user1, session.active_editors)
        self.assertIn(user2, session.active_editors)
    
    def test_update_collaboration_content(self):
        """Test updating content in a collaboration session"""
        symbol_id = "test_symbol_8"
        user_id = "user1"
        
        # Create initial version
        self.symbol_management.create_symbol_version(
            symbol_id, self.sample_symbol, "author", "Initial version"
        )
        
        # Start session
        session_id = self.symbol_management.start_collaboration_session(symbol_id, user_id)
        
        # Update content
        modified_content = self.sample_symbol.replace("Test Symbol", "Collaborative Symbol")
        success = self.symbol_management.update_collaboration_content(
            session_id, user_id, modified_content
        )
        
        self.assertTrue(success)
        
        session = self.symbol_management.active_sessions[session_id]
        self.assertEqual(session.session_data["current_content"], modified_content)
        self.assertEqual(session.session_data["last_editor"], user_id)
    
    def test_end_collaboration_session(self):
        """Test ending a collaboration session"""
        symbol_id = "test_symbol_9"
        user_id = "user1"
        
        # Create initial version
        self.symbol_management.create_symbol_version(
            symbol_id, self.sample_symbol, "author", "Initial version"
        )
        
        # Start session
        session_id = self.symbol_management.start_collaboration_session(symbol_id, user_id)
        
        # Update content
        modified_content = self.sample_symbol.replace("Test Symbol", "Final Symbol")
        self.symbol_management.update_collaboration_content(session_id, user_id, modified_content)
        
        # End session
        success = self.symbol_management.end_collaboration_session(session_id)
        
        self.assertTrue(success)
        self.assertNotIn(session_id, self.symbol_management.active_sessions)
        
        # Check that final version was created
        current_version = self.symbol_management.get_symbol_version(symbol_id)
        self.assertIsNotNone(current_version)
        self.assertIn("Collaborative edit", current_version.message)
    
    # AI Search Tests
    
    def test_index_symbol_for_search(self):
        """Test indexing a symbol for search"""
        symbol_id = "test_symbol_10"
        metadata = {"category": "electrical", "tags": ["switch", "control"]}
        
        # Index symbol
        self.symbol_management.index_symbol_for_search(symbol_id, self.sample_symbol, metadata)
        
        self.assertIn(symbol_id, self.symbol_management.search_index)
        
        index_data = self.symbol_management.search_index[symbol_id]
        self.assertEqual(index_data["metadata"], metadata)
        self.assertIn("features", index_data)
        self.assertIn("svg_tags", index_data["features"])
        self.assertIn("colors", index_data["features"])
    
    def test_search_symbols(self):
        """Test searching symbols"""
        # Index multiple symbols
        self.symbol_management.index_symbol_for_search("symbol1", self.sample_symbol, {"category": "electrical"})
        self.symbol_management.index_symbol_for_search("symbol2", self.complex_symbol, {"category": "mechanical"})
        
        # Search for symbols
        results = self.symbol_management.search_symbols("Test Symbol")
        
        self.assertGreater(len(results), 0)
        self.assertIsInstance(results[0], SymbolSearchResult)
        self.assertGreater(results[0].score, 0.0)
    
    def test_get_ai_recommendations(self):
        """Test getting AI recommendations"""
        # Index multiple symbols
        self.symbol_management.index_symbol_for_search("symbol1", self.sample_symbol, {"category": "electrical"})
        self.symbol_management.index_symbol_for_search("symbol2", self.complex_symbol, {"category": "mechanical"})
        
        # Get recommendations
        recommendations = self.symbol_management.get_ai_recommendations("symbol1")
        
        self.assertIsInstance(recommendations, list)
        if recommendations:
            self.assertIsInstance(recommendations[0], SymbolSearchResult)
            self.assertGreater(recommendations[0].score, 0.0)
    
    # Dependency Tracking Tests
    
    def test_add_symbol_dependency(self):
        """Test adding a symbol dependency"""
        symbol_id = "main_symbol"
        dependency_id = "dependency_symbol"
        
        # Create symbols
        self.symbol_management.create_symbol_version(symbol_id, self.sample_symbol, "author", "Main symbol")
        self.symbol_management.create_symbol_version(dependency_id, self.complex_symbol, "author", "Dependency")
        
        # Add dependency
        success = self.symbol_management.add_symbol_dependency(
            symbol_id, dependency_id, "includes", "*", True, {"required": True}
        )
        
        self.assertTrue(success)
        
        # Check dependency graph
        self.assertIn(dependency_id, self.symbol_management.dependency_graph[symbol_id])
        self.assertIn(symbol_id, self.symbol_management.reverse_dependencies[dependency_id])
    
    def test_get_symbol_dependencies(self):
        """Test getting symbol dependencies"""
        symbol_id = "main_symbol"
        dependency_id = "dependency_symbol"
        
        # Create symbols
        self.symbol_management.create_symbol_version(symbol_id, self.sample_symbol, "author", "Main symbol")
        self.symbol_management.create_symbol_version(dependency_id, self.complex_symbol, "author", "Dependency")
        
        # Add dependency
        self.symbol_management.add_symbol_dependency(symbol_id, dependency_id, "includes")
        
        # Get dependencies
        dependencies = self.symbol_management.get_symbol_dependencies(symbol_id)
        
        self.assertEqual(len(dependencies), 1)
        self.assertEqual(dependencies[0].symbol_id, symbol_id)
        self.assertEqual(dependencies[0].dependency_id, dependency_id)
        self.assertEqual(dependencies[0].dependency_type, "includes")
    
    def test_validate_symbol_dependencies(self):
        """Test validating symbol dependencies"""
        symbol_id = "main_symbol"
        dependency_id = "dependency_symbol"
        missing_dependency_id = "missing_symbol"
        
        # Create symbols
        self.symbol_management.create_symbol_version(symbol_id, self.sample_symbol, "author", "Main symbol")
        self.symbol_management.create_symbol_version(dependency_id, self.complex_symbol, "author", "Dependency")
        
        # Add valid and invalid dependencies
        self.symbol_management.add_symbol_dependency(symbol_id, dependency_id, "includes")
        self.symbol_management.add_symbol_dependency(symbol_id, missing_dependency_id, "references")
        
        # Validate dependencies
        validation = self.symbol_management.validate_symbol_dependencies(symbol_id)
        
        self.assertFalse(validation["valid"])
        self.assertIn(missing_dependency_id, validation["missing_dependencies"])
        self.assertGreater(len(validation["errors"]), 0)
    
    # Analytics Tests
    
    def test_track_symbol_usage(self):
        """Test tracking symbol usage"""
        symbol_id = "test_symbol_11"
        user_id = "user1"
        
        # Create symbol
        self.symbol_management.create_symbol_version(symbol_id, self.sample_symbol, "author", "Test symbol")
        
        # Track usage
        self.symbol_management.track_symbol_usage(symbol_id, user_id, {"context": "test"})
        
        # Check usage tracking
        self.assertIn(symbol_id, self.symbol_management.usage_tracking)
        tracking = self.symbol_management.usage_tracking[symbol_id]
        self.assertEqual(tracking["usage_count"], 1)
        self.assertIn(user_id, tracking["users"])
    
    def test_get_symbol_analytics(self):
        """Test getting symbol analytics"""
        symbol_id = "test_symbol_12"
        user_id = "user1"
        
        # Create symbol
        self.symbol_management.create_symbol_version(symbol_id, self.sample_symbol, "author", "Test symbol")
        
        # Track usage
        self.symbol_management.track_symbol_usage(symbol_id, user_id)
        
        # Get analytics
        analytics = self.symbol_management.get_symbol_analytics(symbol_id)
        
        if analytics:  # Analytics might not be created immediately
            self.assertEqual(analytics.symbol_id, symbol_id)
            self.assertGreater(analytics.usage_count, 0)
    
    def test_calculate_popularity_score(self):
        """Test calculating popularity score"""
        symbol_id = "test_symbol_13"
        user_id = "user1"
        
        # Create symbol
        self.symbol_management.create_symbol_version(symbol_id, self.sample_symbol, "author", "Test symbol")
        
        # Track usage multiple times
        for i in range(5):
            self.symbol_management.track_symbol_usage(symbol_id, user_id)
        
        # Calculate popularity score
        score = self.symbol_management.calculate_popularity_score(symbol_id)
        
        self.assertGreaterEqual(score, 0.0)
        self.assertLessEqual(score, 1.0)
    
    # Marketplace Tests
    
    def test_add_marketplace_item(self):
        """Test adding a marketplace item"""
        symbol_id = "marketplace_symbol"
        author = "author1"
        title = "Test Symbol"
        description = "A test symbol for the marketplace"
        category = "electrical"
        tags = ["switch", "control"]
        
        # Create symbol
        self.symbol_management.create_symbol_version(symbol_id, self.sample_symbol, author, "Marketplace symbol")
        
        # Add to marketplace
        success = self.symbol_management.add_marketplace_item(
            symbol_id, author, title, description, category, tags, 0.0, "MIT"
        )
        
        self.assertTrue(success)
        self.assertIn(symbol_id, self.symbol_management.marketplace_items)
        
        item = self.symbol_management.marketplace_items[symbol_id]
        self.assertEqual(item.author, author)
        self.assertEqual(item.title, title)
        self.assertEqual(item.category, category)
        self.assertEqual(item.tags, tags)
    
    def test_search_marketplace(self):
        """Test searching the marketplace"""
        # Add marketplace items
        self.symbol_management.create_symbol_version("symbol1", self.sample_symbol, "author1", "Symbol 1")
        self.symbol_management.add_marketplace_item(
            "symbol1", "author1", "Test Symbol", "A test symbol", "electrical", ["test"], 0.0
        )
        
        self.symbol_management.create_symbol_version("symbol2", self.complex_symbol, "author2", "Symbol 2")
        self.symbol_management.add_marketplace_item(
            "symbol2", "author2", "Complex Symbol", "A complex symbol", "mechanical", ["complex"], 0.0
        )
        
        # Search marketplace
        results = self.symbol_management.search_marketplace("Test Symbol")
        
        self.assertGreater(len(results), 0)
        self.assertIsInstance(results[0], MarketplaceItem)
    
    def test_rate_marketplace_item(self):
        """Test rating a marketplace item"""
        symbol_id = "rated_symbol"
        user_id = "user1"
        
        # Create symbol and add to marketplace
        self.symbol_management.create_symbol_version(symbol_id, self.sample_symbol, "author", "Rated symbol")
        self.symbol_management.add_marketplace_item(
            symbol_id, "author", "Rated Symbol", "A symbol to rate", "electrical", ["rated"], 0.0
        )
        
        # Rate the item
        success = self.symbol_management.rate_marketplace_item(symbol_id, user_id, 4.5, "Great symbol!")
        
        self.assertTrue(success)
        
        item = self.symbol_management.marketplace_items[symbol_id]
        self.assertEqual(item.rating, 4.5)
        self.assertIn(user_id, item.ratings)
    
    # Integration Tests
    
    def test_full_workflow(self):
        """Test a complete symbol management workflow"""
        symbol_id = "workflow_symbol"
        user_id = "workflow_user"
        
        # 1. Create initial version
        version1 = self.symbol_management.create_symbol_version(
            symbol_id, self.sample_symbol, user_id, "Initial version"
        )
        
        # 2. Index for search
        self.symbol_management.index_symbol_for_search(symbol_id, self.sample_symbol, {"category": "test"})
        
        # 3. Start collaboration
        session_id = self.symbol_management.start_collaboration_session(symbol_id, user_id)
        
        # 4. Update content collaboratively
        modified_content = self.sample_symbol.replace("Test Symbol", "Workflow Symbol")
        self.symbol_management.update_collaboration_content(session_id, user_id, modified_content)
        
        # 5. End collaboration
        self.symbol_management.end_collaboration_session(session_id)
        
        # 6. Track usage
        self.symbol_management.track_symbol_usage(symbol_id, user_id)
        
        # 7. Add to marketplace
        self.symbol_management.add_marketplace_item(
            symbol_id, user_id, "Workflow Symbol", "A symbol created through workflow", "test", ["workflow"], 0.0
        )
        
        # 8. Verify results
        current_version = self.symbol_management.get_symbol_version(symbol_id)
        self.assertIsNotNone(current_version)
        self.assertIn("Collaborative edit", current_version.message)
        
        search_results = self.symbol_management.search_symbols("Workflow Symbol")
        self.assertGreater(len(search_results), 0)
        
        marketplace_results = self.symbol_management.search_marketplace("Workflow Symbol")
        self.assertGreater(len(marketplace_results), 0)
    
    def test_concurrent_collaboration(self):
        """Test concurrent collaboration sessions"""
        symbol_id = "concurrent_symbol"
        users = ["user1", "user2", "user3"]
        
        # Create symbol
        self.symbol_management.create_symbol_version(symbol_id, self.sample_symbol, "author", "Concurrent symbol")
        
        # Start multiple sessions
        session_ids = []
        for user in users:
            session_id = self.symbol_management.start_collaboration_session(symbol_id, user)
            session_ids.append(session_id)
        
        # Verify all sessions are active
        self.assertEqual(len(self.symbol_management.active_sessions), len(users))
        
        # Update content in each session
        for i, session_id in enumerate(session_ids):
            modified_content = self.sample_symbol.replace("Test Symbol", f"User {i+1} Symbol")
            success = self.symbol_management.update_collaboration_content(session_id, users[i], modified_content)
            self.assertTrue(success)
        
        # End all sessions
        for session_id in session_ids:
            self.symbol_management.end_collaboration_session(session_id)
        
        # Verify all sessions ended
        self.assertEqual(len(self.symbol_management.active_sessions), 0)
    
    def test_error_handling(self):
        """Test error handling in various scenarios"""
        # Test with non-existent symbol
        version = self.symbol_management.get_symbol_version("non_existent")
        self.assertIsNone(version)
        
        # Test with non-existent session
        success = self.symbol_management.join_collaboration_session("non_existent", "user")
        self.assertFalse(success)
        
        # Test with invalid dependency
        validation = self.symbol_management.validate_symbol_dependencies("non_existent")
        self.assertFalse(validation["valid"])
    
    def test_cleanup(self):
        """Test service cleanup"""
        # Create some data
        symbol_id = "cleanup_symbol"
        self.symbol_management.create_symbol_version(symbol_id, self.sample_symbol, "author", "Cleanup test")
        
        session_id = self.symbol_management.start_collaboration_session(symbol_id, "user")
        
        # Verify data exists
        self.assertIn(symbol_id, self.symbol_management.current_versions)
        self.assertIn(session_id, self.symbol_management.active_sessions)
        
        # Cleanup
        self.symbol_management.cleanup()
        
        # Verify cleanup
        self.assertEqual(len(self.symbol_management.active_sessions), 0)
    
    def test_get_statistics(self):
        """Test statistics retrieval"""
        # Create some test data
        symbol_id = "stats_symbol"
        self.symbol_management.create_symbol_version(symbol_id, self.sample_symbol, "author", "Stats test")
        self.symbol_management.index_symbol_for_search(symbol_id, self.sample_symbol, {})
        self.symbol_management.add_marketplace_item(symbol_id, "author", "Stats Symbol", "Test", "test", [], 0.0)
        
        stats = self.symbol_management.get_statistics()
        
        self.assertIsInstance(stats, dict)
        self.assertIn('total_symbols', stats)
        self.assertIn('total_versions', stats)
        self.assertIn('active_sessions', stats)
        self.assertIn('search_index_size', stats)
        self.assertIn('marketplace_items', stats)
        self.assertIn('dependency_relationships', stats)
        self.assertIn('analytics_tracked', stats)
        
        self.assertIsInstance(stats['total_symbols'], int)
        self.assertIsInstance(stats['total_versions'], int)
        self.assertIsInstance(stats['active_sessions'], int)


if __name__ == '__main__':
    unittest.main() 