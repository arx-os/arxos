"""
Tests for Advanced Version Control Service
"""

import pytest
import json
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
from unittest.mock import patch, MagicMock

from services.version_control import (
    VersionControlService, Version, Branch, MergeRequest, 
    Conflict, Annotation, Comment, VersionType, BranchStatus, 
    MergeStatus, ConflictType, ConflictResolution
)

class TestVersionControlService:
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for tests"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def vc_service(self, temp_dir):
        """Create version control service instance"""
        db_path = Path(temp_dir) / "test_version_control.db"
        storage_path = Path(temp_dir) / "versions"
        return VersionControlService(str(db_path), str(storage_path))
    
    @pytest.fixture
    def sample_floor_data(self):
        """Sample floor data for testing"""
        return {
            "floor_id": "test-floor-1",
            "building_id": "test-building-1",
            "objects": [
                {"id": "obj1", "type": "wall", "x": 100, "y": 100},
                {"id": "obj2", "type": "door", "x": 200, "y": 200}
            ],
            "metadata": {"name": "Test Floor", "level": 1}
        }
    
    @pytest.fixture
    def sample_floor_data_modified(self):
        """Modified sample floor data for testing"""
        return {
            "floor_id": "test-floor-1",
            "building_id": "test-building-1",
            "objects": [
                {"id": "obj1", "type": "wall", "x": 150, "y": 150},  # Modified
                {"id": "obj2", "type": "door", "x": 200, "y": 200},
                {"id": "obj3", "type": "window", "x": 300, "y": 300}  # Added
            ],
            "metadata": {"name": "Test Floor Modified", "level": 1}
        }

    def test_init_database(self, vc_service):
        """Test database initialization"""
        # Check if database file exists
        assert Path(vc_service.db_path).exists()
        
        # Check if storage directory exists
        assert Path(vc_service.storage_path).exists()
        
        # Check if tables were created
        import sqlite3
        conn = sqlite3.connect(vc_service.db_path)
        cursor = conn.cursor()
        
        # Check tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        expected_tables = ['versions', 'branches', 'merge_requests', 'conflicts', 'annotations', 'comments']
        for table in expected_tables:
            assert table in tables
        
        conn.close()

    def test_create_version(self, vc_service, sample_floor_data):
        """Test version creation"""
        result = vc_service.create_version(
            sample_floor_data,
            "test-floor-1",
            "test-building-1",
            "main",
            "Initial commit",
            "test-user",
            version_type=VersionType.MINOR
        )
        
        assert result["success"] is True
        assert "version_id" in result
        assert "version_number" in result
        assert "data_hash" in result
        
        # Check if version file was created
        version_file = Path(vc_service.storage_path) / f"{result['version_id']}.json"
        assert version_file.exists()
        
        # Check file content
        with open(version_file, 'r') as f:
            saved_data = json.load(f)
        assert saved_data == sample_floor_data

    def test_create_branch(self, vc_service):
        """Test branch creation"""
        # First create a version to use as base
        sample_data = {"test": "data"}
        version_result = vc_service.create_version(
            sample_data, "test-floor-1", "test-building-1",
            "main", "Initial commit", "test-user"
        )
        
        result = vc_service.create_branch(
            "feature-branch",
            "test-floor-1",
            "test-building-1",
            version_result["version_id"],
            "test-user",
            "Test feature branch"
        )
        
        assert result["success"] is True
        assert result["branch_name"] == "feature-branch"

    def test_create_duplicate_branch(self, vc_service):
        """Test creating duplicate branch fails"""
        # Create first branch
        sample_data = {"test": "data"}
        version_result = vc_service.create_version(
            sample_data, "test-floor-1", "test-building-1",
            "main", "Initial commit", "test-user"
        )
        
        vc_service.create_branch(
            "feature-branch",
            "test-floor-1",
            "test-building-1",
            version_result["version_id"],
            "test-user"
        )
        
        # Try to create duplicate branch
        result = vc_service.create_branch(
            "feature-branch",
            "test-floor-1",
            "test-building-1",
            version_result["version_id"],
            "test-user"
        )
        
        assert result["success"] is False
        assert "already exists" in result["message"]

    def test_get_branches(self, vc_service):
        """Test getting branches"""
        # Create some branches
        sample_data = {"test": "data"}
        version_result = vc_service.create_version(
            sample_data, "test-floor-1", "test-building-1",
            "main", "Initial commit", "test-user"
        )
        
        vc_service.create_branch(
            "branch1",
            "test-floor-1",
            "test-building-1",
            version_result["version_id"],
            "test-user"
        )
        
        vc_service.create_branch(
            "branch2",
            "test-floor-1",
            "test-building-1",
            version_result["version_id"],
            "test-user"
        )
        
        result = vc_service.get_branches("test-floor-1", "test-building-1")
        
        assert result["success"] is True
        assert len(result["branches"]) == 2
        branch_names = [b["branch_name"] for b in result["branches"]]
        assert "branch1" in branch_names
        assert "branch2" in branch_names

    def test_get_version_history(self, vc_service, sample_floor_data):
        """Test getting version history"""
        # Create multiple versions
        vc_service.create_version(
            sample_floor_data, "test-floor-1", "test-building-1",
            "main", "Version 1", "test-user"
        )
        
        vc_service.create_version(
            sample_floor_data, "test-floor-1", "test-building-1",
            "main", "Version 2", "test-user"
        )
        
        result = vc_service.get_version_history("test-floor-1", "test-building-1")
        
        assert result["success"] is True
        assert len(result["versions"]) == 2
        assert result["versions"][0]["commit_message"] == "Version 2"  # Most recent first

    def test_get_version_data(self, vc_service, sample_floor_data):
        """Test getting version data"""
        version_result = vc_service.create_version(
            sample_floor_data, "test-floor-1", "test-building-1",
            "main", "Test version", "test-user"
        )
        
        result = vc_service.get_version_data(version_result["version_id"])
        
        assert result["success"] is True
        assert result["data"] == sample_floor_data

    def test_get_nonexistent_version_data(self, vc_service):
        """Test getting non-existent version data"""
        result = vc_service.get_version_data("nonexistent-id")
        
        assert result["success"] is False
        assert "not found" in result["message"]

    def test_create_merge_request(self, vc_service, sample_floor_data, sample_floor_data_modified):
        """Test creating merge request"""
        # Create source branch with modified data
        source_version = vc_service.create_version(
            sample_floor_data_modified, "test-floor-1", "test-building-1",
            "feature-branch", "Feature changes", "test-user"
        )
        
        # Create target branch with original data
        target_version = vc_service.create_version(
            sample_floor_data, "test-floor-1", "test-building-1",
            "main", "Main version", "test-user"
        )
        
        result = vc_service.create_merge_request(
            "feature-branch",
            "main",
            "test-floor-1",
            "test-building-1",
            "test-user",
            "Merge feature changes"
        )
        
        assert result["success"] is True
        assert "merge_id" in result
        assert "conflicts" in result
        assert result["has_conflicts"] is True

    def test_resolve_conflict(self, vc_service):
        """Test conflict resolution"""
        # Create a merge request first
        sample_data = {"test": "data"}
        version_result = vc_service.create_version(
            sample_data, "test-floor-1", "test-building-1",
            "main", "Initial commit", "test-user"
        )
        
        merge_result = vc_service.create_merge_request(
            "feature-branch",
            "main",
            "test-floor-1",
            "test-building-1",
            "test-user"
        )
        
        # Get conflicts from database
        import sqlite3
        conn = sqlite3.connect(vc_service.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT conflict_id FROM conflicts WHERE merge_id = ?", (merge_result["merge_id"],))
        conflicts = cursor.fetchall()
        conn.close()
        
        if conflicts:
            conflict_id = conflicts[0][0]
            result = vc_service.resolve_conflict(conflict_id, "source", "test-user")
            
            assert result["success"] is True
            assert result["conflict_id"] == conflict_id

    def test_execute_merge(self, vc_service):
        """Test merge execution"""
        # Create a merge request
        sample_data = {"test": "data"}
        version_result = vc_service.create_version(
            sample_data, "test-floor-1", "test-building-1",
            "main", "Initial commit", "test-user"
        )
        
        merge_result = vc_service.create_merge_request(
            "feature-branch",
            "main",
            "test-floor-1",
            "test-building-1",
            "test-user"
        )
        
        # Resolve all conflicts first
        import sqlite3
        conn = sqlite3.connect(vc_service.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT conflict_id FROM conflicts WHERE merge_id = ?", (merge_result["merge_id"],))
        conflicts = cursor.fetchall()
        
        for conflict in conflicts:
            cursor.execute(
                "UPDATE conflicts SET resolution = ?, resolved_by = ?, resolved_at = ? WHERE conflict_id = ?",
                ("source", "test-user", datetime.utcnow().isoformat(), conflict[0])
            )
        conn.commit()
        conn.close()
        
        # Execute merge
        result = vc_service.execute_merge(merge_result["merge_id"], "test-user")
        
        assert result["success"] is True
        assert result["merge_id"] == merge_result["merge_id"]

    def test_add_annotation(self, vc_service):
        """Test adding annotation"""
        # Create a version first
        sample_data = {"test": "data"}
        version_result = vc_service.create_version(
            sample_data, "test-floor-1", "test-building-1",
            "main", "Initial commit", "test-user"
        )
        
        result = vc_service.add_annotation(
            version_result["version_id"],
            "test-floor-1",
            "test-building-1",
            "Test Annotation",
            "This is a test annotation",
            "test-user",
            object_id="obj1",
            position_x=100.0,
            position_y=200.0,
            annotation_type="note"
        )
        
        assert result["success"] is True
        assert "annotation_id" in result

    def test_get_annotations(self, vc_service):
        """Test getting annotations"""
        # Create a version and annotation
        sample_data = {"test": "data"}
        version_result = vc_service.create_version(
            sample_data, "test-floor-1", "test-building-1",
            "main", "Initial commit", "test-user"
        )
        
        annotation_result = vc_service.add_annotation(
            version_result["version_id"],
            "test-floor-1",
            "test-building-1",
            "Test Annotation",
            "This is a test annotation",
            "test-user"
        )
        
        result = vc_service.get_annotations(version_result["version_id"])
        
        assert result["success"] is True
        assert len(result["annotations"]) == 1
        assert result["annotations"][0]["title"] == "Test Annotation"

    def test_add_comment(self, vc_service):
        """Test adding comment"""
        # Create a version first
        sample_data = {"test": "data"}
        version_result = vc_service.create_version(
            sample_data, "test-floor-1", "test-building-1",
            "main", "Initial commit", "test-user"
        )
        
        result = vc_service.add_comment(
            version_result["version_id"],
            "version",
            "This is a test comment",
            "test-user"
        )
        
        assert result["success"] is True
        assert "comment_id" in result

    def test_get_comments(self, vc_service):
        """Test getting comments"""
        # Create a version and comment
        sample_data = {"test": "data"}
        version_result = vc_service.create_version(
            sample_data, "test-floor-1", "test-building-1",
            "main", "Initial commit", "test-user"
        )
        
        comment_result = vc_service.add_comment(
            version_result["version_id"],
            "version",
            "This is a test comment",
            "test-user"
        )
        
        result = vc_service.get_comments(version_result["version_id"], "version")
        
        assert result["success"] is True
        assert len(result["comments"]) == 1
        assert result["comments"][0]["content"] == "This is a test comment"

    def test_search_annotations(self, vc_service):
        """Test searching annotations"""
        # Create a version and annotation
        sample_data = {"test": "data"}
        version_result = vc_service.create_version(
            sample_data, "test-floor-1", "test-building-1",
            "main", "Initial commit", "test-user"
        )
        
        vc_service.add_annotation(
            version_result["version_id"],
            "test-floor-1",
            "test-building-1",
            "Test Annotation",
            "This is a test annotation with searchable content",
            "test-user"
        )
        
        result = vc_service.search_annotations("test-floor-1", "test-building-1", "searchable")
        
        assert result["success"] is True
        assert len(result["annotations"]) == 1
        assert "searchable" in result["annotations"][0]["content"]

    def test_generate_version_number(self, vc_service):
        """Test version number generation"""
        version_number = vc_service._generate_version_number("main", VersionType.MINOR)
        
        assert "main" in version_number
        assert "minor" in version_number
        assert "." in version_number  # Should contain timestamp

    def test_detect_conflicts(self, vc_service, sample_floor_data, sample_floor_data_modified):
        """Test conflict detection"""
        # Create branches with different data
        source_version = vc_service.create_version(
            sample_floor_data_modified, "test-floor-1", "test-building-1",
            "feature-branch", "Feature changes", "test-user"
        )
        
        target_version = vc_service.create_version(
            sample_floor_data, "test-floor-1", "test-building-1",
            "main", "Main version", "test-user"
        )
        
        conflicts = vc_service._detect_conflicts(
            "feature-branch",
            "main",
            "test-floor-1",
            "test-building-1"
        )
        
        assert len(conflicts) > 0
        
        # Check for specific conflict types
        conflict_types = [c["type"] for c in conflicts]
        assert ConflictType.OBJECT_MODIFIED.value in conflict_types
        assert ConflictType.OBJECT_ADDED.value in conflict_types

    def test_error_handling(self, vc_service):
        """Test error handling"""
        # Test with invalid data
        result = vc_service.create_version(
            None,  # Invalid data
            "test-floor-1",
            "test-building-1",
            "main",
            "Test commit",
            "test-user"
        )
        
        assert result["success"] is False
        assert "message" in result

    def test_concurrent_access(self, vc_service, sample_floor_data):
        """Test concurrent access to version control"""
        import threading
        import time
        
        results = []
        errors = []
        
        def create_version_thread():
            try:
                result = vc_service.create_version(
                    sample_floor_data,
                    "test-floor-1",
                    "test-building-1",
                    "main",
                    f"Thread commit {threading.current_thread().name}",
                    "test-user"
                )
                results.append(result)
            except Exception as e:
                errors.append(e)
        
        # Create multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=create_version_thread)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Check results
        assert len(errors) == 0
        assert len(results) == 5
        assert all(r["success"] for r in results)

    def test_data_integrity(self, vc_service, sample_floor_data):
        """Test data integrity across operations"""
        # Create version
        version_result = vc_service.create_version(
            sample_floor_data,
            "test-floor-1",
            "test-building-1",
            "main",
            "Initial commit",
            "test-user"
        )
        
        # Retrieve and verify data
        retrieved_data = vc_service.get_version_data(version_result["version_id"])
        
        assert retrieved_data["success"] is True
        assert retrieved_data["data"] == sample_floor_data
        
        # Verify hash matches
        import hashlib
        expected_hash = hashlib.sha256(json.dumps(sample_floor_data, sort_keys=True).encode()).hexdigest()
        assert version_result["data_hash"] == expected_hash

    def test_cleanup_and_maintenance(self, vc_service):
        """Test cleanup and maintenance operations"""
        # Create some test data
        sample_data = {"test": "data"}
        for i in range(10):
            vc_service.create_version(
                sample_data,
                "test-floor-1",
                "test-building-1",
                "main",
                f"Test commit {i}",
                "test-user"
            )
        
        # Verify data exists
        versions = vc_service.get_version_history("test-floor-1", "test-building-1")
        assert len(versions["versions"]) == 10
        
        # Test database integrity
        import sqlite3
        conn = sqlite3.connect(vc_service.db_path)
        cursor = conn.cursor()
        
        # Check for orphaned files
        cursor.execute("SELECT version_id FROM versions")
        version_ids = [row[0] for row in cursor.fetchall()]
        
        for version_id in version_ids:
            version_file = Path(vc_service.storage_path) / f"{version_id}.json"
            assert version_file.exists(), f"Version file missing for {version_id}"
        
        conn.close()

if __name__ == "__main__":
    pytest.main([__file__]) 