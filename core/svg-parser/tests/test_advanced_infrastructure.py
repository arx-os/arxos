"""
Comprehensive Test Suite for Advanced Infrastructure Service

This test suite covers all aspects of the advanced infrastructure functionality including:
- Hierarchical SVG grouping for large buildings
- Advanced caching system for calculations
- Distributed processing for complex operations
- Real-time collaboration with conflict resolution
- Advanced compression algorithms
- Microservices architecture for scalability

Performance Targets:
- System handles buildings with 10,000+ objects
- Calculation cache reduces processing time by 80%
- Distributed processing scales linearly
- Real-time collaboration supports 50+ concurrent users
"""

import pytest
import json
import tempfile
import shutil
from datetime import datetime, timedelta
from typing import Dict, List, Any
from unittest.mock import Mock, patch, MagicMock
import time
import threading
import os
import random

from services.advanced_infrastructure import (
    AdvancedInfrastructure,
    CacheStrategy,
    ProcessingMode,
    CompressionLevel,
    CacheEntry,
    ProcessingTask,
    CollaborationSession
)


class TestAdvancedInfrastructure:
    """Test suite for the AdvancedInfrastructure."""
    
    @pytest.fixture
    def temp_db(self):
        """Create a temporary database for testing."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            temp_path = f.name
        
        yield temp_path
        
        # Cleanup
        try:
            os.unlink(temp_path)
        except OSError:
            pass
    
    @pytest.fixture
    def infrastructure(self, temp_db):
        """Create an advanced infrastructure instance for testing."""
        return AdvancedInfrastructure(db_path=temp_db)
    
    @pytest.fixture
    def sample_svg_elements(self):
        """Sample SVG elements for testing."""
        return [
            {
                "type": "rect",
                "id": "rect1",
                "x": 10,
                "y": 10,
                "width": 100,
                "height": 50,
                "fill": "blue"
            },
            {
                "type": "circle",
                "id": "circle1",
                "cx": 50,
                "cy": 50,
                "r": 25,
                "fill": "red"
            },
            {
                "type": "line",
                "id": "line1",
                "x1": 0,
                "y1": 0,
                "x2": 100,
                "y2": 100,
                "stroke": "black"
            }
        ]
    
    def test_infrastructure_initialization(self, infrastructure):
        """Test infrastructure initialization and setup."""
        assert infrastructure is not None
        assert infrastructure.cache == {}
        assert infrastructure.cache_strategy == CacheStrategy.LRU
        assert infrastructure.max_cache_size == 1000
        assert infrastructure.max_cache_memory == 100 * 1024 * 1024
        assert infrastructure.total_operations == 0
        assert infrastructure.cache_hits == 0
        assert infrastructure.cache_misses == 0
        assert len(infrastructure.sessions) == 0
    
    def test_svg_group_creation(self, infrastructure, sample_svg_elements):
        """Test SVG group creation functionality."""
        # Create a simple SVG group
        group_id = infrastructure.create_hierarchical_svg_group(
            name="Test Group",
            elements=sample_svg_elements,
            metadata={"description": "Test group for unit testing"}
        )
        
        assert group_id is not None
        
        # Verify group was created
        group = infrastructure.get_svg_group(group_id)
        assert group is not None
        assert group['name'] == "Test Group"
        assert group['elements'] == sample_svg_elements
        assert group['metadata']['description'] == "Test group for unit testing"
        assert group['parent_id'] is None
    
    def test_svg_hierarchy_creation(self, infrastructure, sample_svg_elements):
        """Test SVG hierarchy creation and retrieval."""
        # Create parent group
        parent_id = infrastructure.create_hierarchical_svg_group(
            name="Parent Group",
            elements=sample_svg_elements[:1],
            metadata={"level": "parent"}
        )
        
        # Create child groups
        child1_id = infrastructure.create_hierarchical_svg_group(
            name="Child Group 1",
            elements=sample_svg_elements[1:2],
            parent_id=parent_id,
            metadata={"level": "child1"}
        )
        
        child2_id = infrastructure.create_hierarchical_svg_group(
            name="Child Group 2",
            elements=sample_svg_elements[2:],
            parent_id=parent_id,
            metadata={"level": "child2"}
        )
        
        # Get hierarchy
        hierarchy = infrastructure.get_svg_hierarchy(parent_id)
        
        assert hierarchy is not None
        assert hierarchy['name'] == "Parent Group"
        assert hierarchy['group_id'] == parent_id
        assert len(hierarchy['children']) == 2
        
        child_names = [child['name'] for child in hierarchy['children']]
        assert "Child Group 1" in child_names
        assert "Child Group 2" in child_names
    
    def test_cache_operations(self, infrastructure):
        """Test cache operations with different strategies."""
        # Test LRU strategy
        infrastructure.cache_strategy = CacheStrategy.LRU
        
        # Add cache entries
        assert infrastructure.cache_set("key1", "value1", ttl=60)
        assert infrastructure.cache_set("key2", "value2", ttl=60)
        assert infrastructure.cache_set("key3", "value3", ttl=60)
        
        # Test cache retrieval
        value1 = infrastructure.cache_get("key1")
        assert value1 == "value1"
        
        value2 = infrastructure.cache_get("key2")
        assert value2 == "value2"
        
        # Test cache miss
        value_none = infrastructure.cache_get("nonexistent")
        assert value_none is None
        
        # Test LFU strategy
        infrastructure.cache_strategy = CacheStrategy.LFU
        infrastructure.cache.clear()
        
        # Add entries with different access patterns
        assert infrastructure.cache_set("key1", "value1")
        assert infrastructure.cache_set("key2", "value2")
        
        # Access key1 multiple times
        for _ in range(5):
            infrastructure.cache_get("key1")
        
        # Access key2 once
        infrastructure.cache_get("key2")
        
        # Add more entries to trigger eviction
        for i in range(1000):
            infrastructure.cache_set(f"key{i}", f"value{i}")
        
        # key2 should be evicted before key1 (LFU)
        assert infrastructure.cache_get("key1") is not None
        assert infrastructure.cache_get("key2") is None
    
    def test_cache_ttl(self, infrastructure):
        """Test cache TTL functionality."""
        # Set cache entry with TTL
        assert infrastructure.cache_set("key1", "value1", ttl=1)  # 1 second TTL
        
        # Should be available immediately
        assert infrastructure.cache_get("key1") == "value1"
        
        # Wait for TTL to expire
        time.sleep(1.1)
        
        # Should be expired
        assert infrastructure.cache_get("key1") is None
    
    def test_distributed_processing(self, infrastructure):
        """Test distributed processing functionality."""
        # Test sequential processing
        task_id = infrastructure.process_distributed_task(
            task_type="calculation",
            data={"operation": "add", "values": [1, 2, 3, 4, 5]},
            priority=1,
            mode=ProcessingMode.SEQUENTIAL
        )
        
        assert task_id is not None
        
        # Test parallel processing
        task_id2 = infrastructure.process_distributed_task(
            task_type="svg_optimization",
            data={"svg": "<svg><rect x='0' y='0' width='100' height='100'/></svg>"},
            priority=2,
            mode=ProcessingMode.PARALLEL
        )
        
        assert task_id2 is not None
        
        # Test distributed processing
        task_id3 = infrastructure.process_distributed_task(
            task_type="compression",
            data={"content": "test content", "algorithm": "gzip"},
            priority=3,
            mode=ProcessingMode.DISTRIBUTED
        )
        
        assert task_id3 is not None
    
    def test_calculation_processing(self, infrastructure):
        """Test calculation processing tasks."""
        # Test addition
        result = infrastructure._perform_calculation({
            "operation": "add",
            "values": [1, 2, 3, 4, 5]
        })
        
        assert result['operation'] == "add"
        assert result['values'] == [1, 2, 3, 4, 5]
        assert result['result'] == 15
        
        # Test multiplication
        result = infrastructure._perform_calculation({
            "operation": "multiply",
            "values": [2, 3, 4]
        })
        
        assert result['operation'] == "multiply"
        assert result['result'] == 24
        
        # Test average
        result = infrastructure._perform_calculation({
            "operation": "average",
            "values": [10, 20, 30]
        })
        
        assert result['operation'] == "average"
        assert result['result'] == 20.0
    
    def test_svg_optimization(self, infrastructure):
        """Test SVG optimization processing."""
        svg_content = """
        <svg width="100" height="100">
            <!-- This is a comment -->
            <rect x="0" y="0" width="100" height="100" fill="blue"/>
            <circle cx="50" cy="50" r="25" fill="red"/>
        </svg>
        """
        
        result = infrastructure._optimize_svg({
            "svg": svg_content
        })
        
        assert result['original_size'] > 0
        assert result['optimized_size'] > 0
        assert result['compression_ratio'] >= 0
        assert result['optimized_svg'] is not None
        
        # Check that comments were removed
        assert "<!--" not in result['optimized_svg']
        assert "-->" not in result['optimized_svg']
    
    def test_compression_processing(self, infrastructure):
        """Test compression processing tasks."""
        content = "This is a test content for compression testing. " * 100
        
        # Test gzip compression
        result = infrastructure._compress_data({
            "content": content,
            "algorithm": "gzip",
            "level": CompressionLevel.BALANCED
        })
        
        assert result['original_size'] > 0
        assert result['compressed_size'] > 0
        assert result['compression_ratio'] > 0
        assert result['algorithm'] == "gzip"
        assert result['compressed_data'] is not None
        
        # Test zlib compression
        result = infrastructure._compress_data({
            "content": content,
            "algorithm": "zlib",
            "level": CompressionLevel.MAXIMUM
        })
        
        assert result['algorithm'] == "zlib"
        assert result['compressed_data'] is not None
    
    def test_collaboration_session_creation(self, infrastructure):
        """Test collaboration session creation and management."""
        # Create session
        session_id = infrastructure.create_collaboration_session(
            document_id="doc123",
            users=["user1", "user2", "user3"]
        )
        
        assert session_id is not None
        
        # Verify session exists
        assert session_id in infrastructure.sessions
        session = infrastructure.sessions[session_id]
        assert session.document_id == "doc123"
        assert session.users == ["user1", "user2", "user3"]
        assert len(session.changes) == 0
        assert len(session.conflicts) == 0
    
    def test_collaboration_join_session(self, infrastructure):
        """Test joining collaboration sessions."""
        # Create session
        session_id = infrastructure.create_collaboration_session(
            document_id="doc123",
            users=["user1", "user2"]
        )
        
        # Join session
        success = infrastructure.join_collaboration_session(session_id, "user3")
        assert success is True
        
        # Verify user was added
        session = infrastructure.sessions[session_id]
        assert "user3" in session.users
        
        # Try to join non-existent session
        success = infrastructure.join_collaboration_session("nonexistent", "user4")
        assert success is False
    
    def test_collaboration_changes(self, infrastructure):
        """Test adding changes to collaboration sessions."""
        # Create session
        session_id = infrastructure.create_collaboration_session(
            document_id="doc123",
            users=["user1", "user2"]
        )
        
        # Add changes
        change1 = {
            "element_id": "rect1",
            "type": "move",
            "x": 10,
            "y": 20
        }
        
        success = infrastructure.add_collaboration_change(
            session_id=session_id,
            user_id="user1",
            change=change1
        )
        
        assert success is True
        
        # Verify change was added
        session = infrastructure.sessions[session_id]
        assert len(session.changes) == 1
        assert session.changes[0]['user_id'] == "user1"
        assert session.changes[0]['change'] == change1
        
        # Add another change
        change2 = {
            "element_id": "circle1",
            "type": "resize",
            "radius": 30
        }
        
        success = infrastructure.add_collaboration_change(
            session_id=session_id,
            user_id="user2",
            change=change2
        )
        
        assert success is True
        assert len(session.changes) == 2
    
    def test_conflict_detection(self, infrastructure):
        """Test conflict detection in collaboration."""
        # Create session
        session_id = infrastructure.create_collaboration_session(
            document_id="doc123",
            users=["user1", "user2"]
        )
        
        # Add conflicting changes to same element
        change1 = {
            "element_id": "rect1",
            "type": "move",
            "x": 10,
            "y": 20
        }
        
        change2 = {
            "element_id": "rect1",
            "type": "resize",
            "width": 200,
            "height": 150
        }
        
        # Add first change
        infrastructure.add_collaboration_change(session_id, "user1", change1)
        
        # Add conflicting change
        infrastructure.add_collaboration_change(session_id, "user2", change2)
        
        # Check for conflicts
        session = infrastructure.sessions[session_id]
        assert len(session.conflicts) > 0
        
        # Verify conflict details
        conflict = session.conflicts[0]
        assert conflict['new_change']['change']['element_id'] == "rect1"
        assert conflict['conflicting_change']['change']['element_id'] == "rect1"
    
    def test_performance_metrics(self, infrastructure):
        """Test performance metrics collection."""
        # Perform some operations
        infrastructure.cache_set("key1", "value1")
        infrastructure.cache_get("key1")
        infrastructure.cache_get("nonexistent")
        
        infrastructure.create_collaboration_session("doc1", ["user1"])
        infrastructure.create_collaboration_session("doc2", ["user2"])
        
        # Get metrics
        metrics = infrastructure.get_performance_metrics()
        
        assert metrics['total_operations'] >= 0
        assert metrics['cache_hits'] >= 1
        assert metrics['cache_misses'] >= 1
        assert metrics['cache_hit_rate'] >= 0
        assert metrics['cache_size'] >= 0
        assert metrics['processing_tasks'] >= 0
        assert metrics['collaboration_sessions'] >= 2
        assert metrics['active_sessions'] >= 2
        assert metrics['memory_usage'] >= 0
    
    def test_large_scale_svg_groups(self, infrastructure):
        """Test handling large numbers of SVG groups."""
        # Create many groups
        group_ids = []
        for i in range(100):
            group_id = infrastructure.create_hierarchical_svg_group(
                name=f"Group {i}",
                elements=[{"type": "rect", "id": f"rect{i}", "x": i, "y": i}],
                metadata={"index": i}
            )
            group_ids.append(group_id)
        
        assert len(group_ids) == 100
        
        # Verify all groups can be retrieved
        for group_id in group_ids:
            group = infrastructure.get_svg_group(group_id)
            assert group is not None
            assert group['name'].startswith("Group ")
    
    def test_cache_performance(self, infrastructure):
        """Test cache performance under load."""
        # Fill cache with many entries
        for i in range(1000):
            infrastructure.cache_set(f"key{i}", f"value{i}")
        
        # Test cache hit performance
        start_time = time.time()
        for i in range(100):
            value = infrastructure.cache_get(f"key{i}")
            assert value == f"value{i}"
        end_time = time.time()
        
        # Should be very fast (cache hits)
        assert end_time - start_time < 1.0  # Less than 1 second for 100 operations
        
        # Test cache miss performance
        start_time = time.time()
        for i in range(100):
            value = infrastructure.cache_get(f"nonexistent{i}")
            assert value is None
        end_time = time.time()
        
        # Should still be fast
        assert end_time - start_time < 1.0
    
    def test_concurrent_processing(self, infrastructure):
        """Test concurrent processing capabilities."""
        import threading
        import time
        
        results = []
        errors = []
        
        def process_worker(task_id):
            try:
                result = infrastructure.process_distributed_task(
                    task_type="calculation",
                    data={"operation": "add", "values": [1, 2, 3]},
                    priority=1,
                    mode=ProcessingMode.PARALLEL
                )
                results.append(result)
            except Exception as e:
                errors.append(e)
        
        # Start multiple threads
        threads = []
        for i in range(10):
            thread = threading.Thread(target=process_worker, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join()
        
        # Check results
        assert len(errors) == 0, f"Concurrent processing failed: {errors}"
        assert len(results) == 10
    
    def test_collaboration_concurrency(self, infrastructure):
        """Test collaboration session concurrency."""
        import threading
        import time
        
        # Create session
        session_id = infrastructure.create_collaboration_session(
            document_id="doc123",
            users=["user1", "user2", "user3"]
        )
        
        changes_added = []
        errors = []
        
        def change_worker(user_id):
            try:
                for i in range(10):
                    change = {
                        "element_id": f"element{i}",
                        "type": "modify",
                        "user": user_id,
                        "timestamp": time.time()
                    }
                    success = infrastructure.add_collaboration_change(
                        session_id, user_id, change
                    )
                    if success:
                        changes_added.append(change)
                    time.sleep(0.01)  # Small delay
            except Exception as e:
                errors.append(e)
        
        # Start multiple threads adding changes
        threads = []
        for user_id in ["user1", "user2", "user3"]:
            thread = threading.Thread(target=change_worker, args=(user_id,))
            threads.append(thread)
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join()
        
        # Check results
        assert len(errors) == 0, f"Collaboration concurrency failed: {errors}"
        assert len(changes_added) > 0
        
        # Verify session state
        session = infrastructure.sessions[session_id]
        assert len(session.changes) > 0
    
    def test_memory_management(self, infrastructure):
        """Test memory management and limits."""
        # Test large value handling
        large_value = "x" * (infrastructure.max_cache_memory + 1024)  # Exceeds limit
        
        success = infrastructure.cache_set("large_key", large_value)
        assert success is False  # Should fail due to size limit
        
        # Test cache size limits
        for i in range(infrastructure.max_cache_size + 100):
            infrastructure.cache_set(f"key{i}", f"value{i}")
        
        # Cache should not exceed max size
        assert len(infrastructure.cache) <= infrastructure.max_cache_size
    
    def test_error_handling(self, infrastructure):
        """Test error handling and recovery."""
        # Test invalid cache strategy
        with pytest.raises(ValueError):
            infrastructure.cache_strategy = "invalid_strategy"
        
        # Test invalid processing mode
        with pytest.raises(ValueError):
            infrastructure.process_distributed_task(
                task_type="test",
                data={},
                mode="invalid_mode"
            )
        
        # Test non-existent session operations
        success = infrastructure.join_collaboration_session("nonexistent", "user1")
        assert success is False
        
        success = infrastructure.add_collaboration_change("nonexistent", "user1", {})
        assert success is False
    
    def test_cleanup_and_shutdown(self, infrastructure):
        """Test cleanup and shutdown procedures."""
        # Add some data
        infrastructure.cache_set("key1", "value1")
        infrastructure.create_collaboration_session("doc1", ["user1"])
        
        # Shutdown
        infrastructure.shutdown()
        
        # Verify cleanup
        assert len(infrastructure.cache) == 0
        assert len(infrastructure.sessions) == 0


class TestAdvancedInfrastructureIntegration:
    """Integration tests for advanced infrastructure functionality."""
    
    @pytest.fixture
    def infrastructure(self):
        """Create an advanced infrastructure for integration testing."""
        return AdvancedInfrastructure()
    
    def test_full_workflow(self, infrastructure):
        """Test complete workflow with all features."""
        # 1. Create SVG groups
        group1_id = infrastructure.create_hierarchical_svg_group(
            name="Building Floor 1",
            elements=[{"type": "rect", "id": "floor1", "x": 0, "y": 0, "width": 100, "height": 50}],
            metadata={"floor": 1}
        )
        
        group2_id = infrastructure.create_hierarchical_svg_group(
            name="Building Floor 2",
            elements=[{"type": "rect", "id": "floor2", "x": 0, "y": 50, "width": 100, "height": 50}],
            parent_id=group1_id,
            metadata={"floor": 2}
        )
        
        # 2. Cache calculations
        infrastructure.cache_set("floor_area", 5000, ttl=3600)
        infrastructure.cache_set("building_height", 100, ttl=3600)
        
        # 3. Process distributed tasks
        task1_id = infrastructure.process_distributed_task(
            task_type="calculation",
            data={"operation": "add", "values": [5000, 5000]},
            mode=ProcessingMode.SEQUENTIAL
        )
        
        task2_id = infrastructure.process_distributed_task(
            task_type="svg_optimization",
            data={"svg": "<svg><rect x='0' y='0' width='100' height='100'/></svg>"},
            mode=ProcessingMode.PARALLEL
        )
        
        # 4. Create collaboration session
        session_id = infrastructure.create_collaboration_session(
            document_id="building_design",
            users=["architect", "engineer", "contractor"]
        )
        
        # 5. Add collaboration changes
        infrastructure.add_collaboration_change(
            session_id, "architect",
            {"element_id": "floor1", "type": "modify", "width": 120}
        )
        
        infrastructure.add_collaboration_change(
            session_id, "engineer",
            {"element_id": "floor1", "type": "modify", "height": 60}
        )
        
        # 6. Get performance metrics
        metrics = infrastructure.get_performance_metrics()
        
        # Verify all components worked
        assert group1_id is not None
        assert group2_id is not None
        assert infrastructure.cache_get("floor_area") == 5000
        assert task1_id is not None
        assert task2_id is not None
        assert session_id is not None
        assert metrics['total_operations'] >= 0
        assert metrics['cache_hits'] >= 1
        assert metrics['collaboration_sessions'] >= 1
    
    def test_performance_targets(self, infrastructure):
        """Test that system meets performance targets."""
        # Test large building handling (10,000+ objects)
        start_time = time.time()
        for i in range(10000):
            infrastructure.create_hierarchical_svg_group(
                name=f"Object {i}",
                elements=[{"type": "rect", "id": f"obj{i}", "x": i, "y": i}],
                metadata={"index": i}
            )
        creation_time = time.time() - start_time
        
        # Should complete within reasonable time
        assert creation_time < 60  # Less than 60 seconds for 10,000 objects
        
        # Test cache performance (80% reduction target)
        large_data = "x" * 10000
        
        # Without cache
        start_time = time.time()
        for _ in range(100):
            result = infrastructure._perform_calculation({
                "operation": "add",
                "values": list(range(1000))
            })
        without_cache_time = time.time() - start_time
        
        # With cache
        infrastructure.cache_set("calc_result", result, ttl=3600)
        
        start_time = time.time()
        for _ in range(100):
            cached_result = infrastructure.cache_get("calc_result")
        with_cache_time = time.time() - start_time
        
        # Cache should be significantly faster
        assert with_cache_time < without_cache_time * 0.2  # 80% reduction
        
        # Test collaboration concurrency (50+ users)
        session_id = infrastructure.create_collaboration_session(
            document_id="large_project",
            users=[f"user{i}" for i in range(60)]
        )
        
        session = infrastructure.sessions[session_id]
        assert len(session.users) == 60  # Supports 50+ users


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 