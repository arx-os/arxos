"""
Test Phase 2 Data Persistence

Tests for the data persistence implementation in Phase 2:
1. Database Integration
2. File Storage System
3. Backup and Recovery
"""

import pytest
import asyncio
import logging
import tempfile
import os
from typing import Dict, Any
from datetime import datetime

# Test imports for database and storage
from infrastructure.database.custom_database import CustomPostgreSQLDatabase, TaskRecord, AnalysisResult
from infrastructure.storage.custom_file_storage import CustomFileStorage, FileInfo
from application.services.pdf_service import PDFAnalysisService


class TestPhase2DataPersistence:
    """Test suite for Phase 2 data persistence"""
    
    def setup_method(self):
        """Setup test environment"""
        # Configure logging for tests
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # Create temporary database and storage
        self.temp_db_path = tempfile.mktemp(suffix='.db')
        self.temp_storage_path = tempfile.mkdtemp()
        
        # Initialize components
        self.db = CustomPostgreSQLDatabase()
        self.file_storage = CustomFileStorage(self.temp_storage_path)
        self.pdf_service = PDFAnalysisService()
    
    def teardown_method(self):
        """Cleanup test environment"""
        # Clean up temporary files
        if os.path.exists(self.temp_db_path):
            os.unlink(self.temp_db_path)
        
        if os.path.exists(self.temp_storage_path):
            import shutil
            shutil.rmtree(self.temp_storage_path)
    
    def test_1_database_initialization(self):
        """Test database initialization and schema"""
        try:
            # Test that database connection is established
            stats = self.db.get_database_stats()
            assert 'total_tasks' in stats
            assert 'total_results' in stats
            assert 'total_sessions' in stats
            assert 'total_api_keys' in stats
            
            self.logger.info("✅ Database initialization successful")
            
        except Exception as e:
            pytest.fail(f"Database initialization test failed: {e}")
    
    def test_2_task_creation_and_retrieval(self):
        """Test task creation and retrieval"""
        try:
            # Create test task
            task_record = TaskRecord(
                task_id="test_task_123",
                user_id="test_user",
                status="processing",
                filename="test.pdf",
                file_path="/tmp/test.pdf",
                requirements={"test": True},
                include_cost_estimation=True,
                include_timeline=True,
                include_quantities=True,
                created_at=datetime.utcnow().isoformat(),
                updated_at=datetime.utcnow().isoformat()
            )
            
            # Save task
            success = self.db.create_task(task_record)
            assert success
            
            # Retrieve task
            retrieved_task = self.db.get_task("test_task_123")
            assert retrieved_task is not None
            assert retrieved_task.task_id == "test_task_123"
            assert retrieved_task.user_id == "test_user"
            assert retrieved_task.status == "processing"
            
            # Test user tasks retrieval
            user_tasks = self.db.get_user_tasks("test_user")
            assert len(user_tasks) == 1
            assert user_tasks[0].task_id == "test_task_123"
            
            self.logger.info("✅ Task creation and retrieval successful")
            
        except Exception as e:
            pytest.fail(f"Task creation and retrieval test failed: {e}")
    
    def test_3_task_update(self):
        """Test task update functionality"""
        try:
            # Create test task
            task_record = TaskRecord(
                task_id="test_update_task",
                user_id="test_user",
                status="processing",
                filename="test.pdf",
                file_path="/tmp/test.pdf",
                requirements={},
                include_cost_estimation=True,
                include_timeline=True,
                include_quantities=True,
                created_at=datetime.utcnow().isoformat(),
                updated_at=datetime.utcnow().isoformat()
            )
            
            # Save task
            self.db.create_task(task_record)
            
            # Update task
            updates = {
                'status': 'completed',
                'confidence': 0.85,
                'total_components': 10,
                'processing_time': 120.5
            }
            
            success = self.db.update_task("test_update_task", updates)
            assert success
            
            # Verify update
            updated_task = self.db.get_task("test_update_task")
            assert updated_task.status == "completed"
            assert updated_task.confidence == 0.85
            assert updated_task.total_components == 10
            assert updated_task.processing_time == 120.5
            
            self.logger.info("✅ Task update successful")
            
        except Exception as e:
            pytest.fail(f"Task update test failed: {e}")
    
    def test_4_analysis_result_storage(self):
        """Test analysis result storage"""
        try:
            # Create test analysis result
            analysis_result = AnalysisResult(
                task_id="test_analysis_task",
                project_info={"name": "Test Project"},
                systems={"architectural": {"components": []}},
                quantities={"total_components": 5},
                cost_estimates={"architectural": 1000.0},
                timeline={"architectural": {"days": 10}},
                confidence=0.9,
                metadata={"version": "1.0"},
                created_at=datetime.utcnow().isoformat()
            )
            
            # Save analysis result
            success = self.db.create_analysis_result(analysis_result)
            assert success
            
            # Retrieve analysis result
            retrieved_result = self.db.get_analysis_result("test_analysis_task")
            assert retrieved_result is not None
            assert retrieved_result.task_id == "test_analysis_task"
            assert retrieved_result.confidence == 0.9
            assert retrieved_result.project_info["name"] == "Test Project"
            
            self.logger.info("✅ Analysis result storage successful")
            
        except Exception as e:
            pytest.fail(f"Analysis result storage test failed: {e}")
    
    def test_5_file_storage_initialization(self):
        """Test file storage initialization"""
        try:
            # Test that storage directories were created
            assert os.path.exists(self.temp_storage_path)
            assert os.path.exists(os.path.join(self.temp_storage_path, "uploads"))
            assert os.path.exists(os.path.join(self.temp_storage_path, "temp"))
            assert os.path.exists(os.path.join(self.temp_storage_path, "exports"))
            assert os.path.exists(os.path.join(self.temp_storage_path, "backups"))
            
            # Test storage stats
            stats = self.file_storage.get_storage_stats()
            assert 'total_files' in stats
            assert 'total_size' in stats
            assert 'uploads_count' in stats
            
            self.logger.info("✅ File storage initialization successful")
            
        except Exception as e:
            pytest.fail(f"File storage initialization test failed: {e}")
    
    def test_6_file_upload_and_validation(self):
        """Test file upload and validation"""
        try:
            # Create test PDF content
            pdf_content = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n>>\nendobj\nxref\n0 4\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n0000000115 00000 n \ntrailer\n<<\n/Size 4\n/Root 1 0 R\n>>\nstartxref\n149\n%%EOF"
            
            # Test file validation
            is_valid, message = self.file_storage.validate_file(pdf_content, "test.pdf")
            assert is_valid
            assert "File validation passed" in message
            
            # Test file upload
            file_info = self.file_storage.save_uploaded_file(pdf_content, "test.pdf", "test_user")
            assert file_info is not None
            assert file_info.original_filename == "test.pdf"
            assert file_info.file_size == len(pdf_content)
            assert file_info.content_type == "application/pdf"
            assert file_info.user_id == "test_user"
            
            # Test file retrieval
            retrieved_file = self.file_storage.get_file(file_info.file_id)
            assert retrieved_file is not None
            assert retrieved_file.original_filename == "test.pdf"
            
            # Test file content retrieval
            content = self.file_storage.get_file_content(file_info.file_id)
            assert content == pdf_content
            
            self.logger.info("✅ File upload and validation successful")
            
        except Exception as e:
            pytest.fail(f"File upload and validation test failed: {e}")
    
    def test_7_file_deletion(self):
        """Test file deletion"""
        try:
            # Create test file
            test_content = b"test content"
            file_info = self.file_storage.save_uploaded_file(test_content, "test_delete.txt", "test_user")
            
            # Verify file exists
            assert self.file_storage.get_file(file_info.file_id) is not None
            
            # Delete file
            success = self.file_storage.delete_file(file_info.file_id)
            assert success
            
            # Verify file is deleted
            assert self.file_storage.get_file(file_info.file_id) is None
            
            self.logger.info("✅ File deletion successful")
            
        except Exception as e:
            pytest.fail(f"File deletion test failed: {e}")
    
    def test_8_temp_file_operations(self):
        """Test temporary file operations"""
        try:
            # Create temp file
            temp_content = b"temporary content"
            temp_path = self.file_storage.create_temp_file(temp_content, "test")
            assert temp_path is not None
            assert os.path.exists(temp_path)
            
            # Test temp file cleanup
            deleted_count = self.file_storage.cleanup_temp_files(max_age_hours=0)
            assert deleted_count >= 0
            
            self.logger.info("✅ Temp file operations successful")
            
        except Exception as e:
            pytest.fail(f"Temp file operations test failed: {e}")
    
    def test_9_export_functionality(self):
        """Test export functionality"""
        try:
            # Create test content
            export_content = b"export test content"
            export_filename = "test_export.json"
            
            # Export file
            export_path = self.file_storage.export_file(export_content, export_filename, "json")
            assert export_path is not None
            assert os.path.exists(export_path)
            
            # Verify export file
            with open(export_path, 'rb') as f:
                content = f.read()
            assert content == export_content
            
            self.logger.info("✅ Export functionality successful")
            
        except Exception as e:
            pytest.fail(f"Export functionality test failed: {e}")
    
    def test_10_backup_functionality(self):
        """Test backup functionality"""
        try:
            # Create test file
            test_content = b"backup test content"
            file_info = self.file_storage.save_uploaded_file(test_content, "test_backup.txt", "test_user")
            
            # Create backup
            success = self.file_storage.backup_file(file_info.file_id)
            assert success
            
            # Verify backup exists
            backup_dir = os.path.join(self.temp_storage_path, "backups")
            backup_files = [f for f in os.listdir(backup_dir) if f.startswith("backup_")]
            assert len(backup_files) > 0
            
            self.logger.info("✅ Backup functionality successful")
            
        except Exception as e:
            pytest.fail(f"Backup functionality test failed: {e}")
    
    def test_11_pdf_service_integration(self):
        """Test PDF service integration with database and storage"""
        try:
            # Test that PDF service can initialize with custom components
            assert self.pdf_service.db is not None
            assert self.pdf_service.file_storage is not None
            
            # Test database stats
            db_stats = self.pdf_service.db.get_database_stats()
            assert isinstance(db_stats, dict)
            
            # Test storage stats
            storage_stats = self.pdf_service.file_storage.get_storage_stats()
            assert isinstance(storage_stats, dict)
            
            self.logger.info("✅ PDF service integration successful")
            
        except Exception as e:
            pytest.fail(f"PDF service integration test failed: {e}")
    
    def test_12_data_persistence_across_restarts(self):
        """Test data persistence across service restarts"""
        try:
            # Create test data
            task_record = TaskRecord(
                task_id="persistence_test",
                user_id="test_user",
                status="completed",
                filename="persistence.pdf",
                file_path="/tmp/persistence.pdf",
                requirements={},
                include_cost_estimation=True,
                include_timeline=True,
                include_quantities=True,
                created_at=datetime.utcnow().isoformat(),
                updated_at=datetime.utcnow().isoformat(),
                confidence=0.95,
                total_components=15
            )
            
            # Save to database
            self.db.create_task(task_record)
            
            # Create new database instance (simulating restart)
            new_db = CustomPostgreSQLDatabase()
            
            # Verify data persists
            retrieved_task = new_db.get_task("persistence_test")
            assert retrieved_task is not None
            assert retrieved_task.task_id == "persistence_test"
            assert retrieved_task.confidence == 0.95
            assert retrieved_task.total_components == 15
            
            self.logger.info("✅ Data persistence across restarts successful")
            
        except Exception as e:
            pytest.fail(f"Data persistence test failed: {e}")
    
    def test_13_custom_implementation_philosophy(self):
        """Test that we're following the custom implementation philosophy"""
        try:
            # Check that we're using PostgreSQL (established Arxos architecture)
            db_source = CustomPostgreSQLDatabase.__module__
            assert 'psycopg2' in db_source  # PostgreSQL adapter
            assert 'sqlalchemy' not in db_source  # No ORM
            assert 'asyncpg' not in db_source  # No async ORM
            
            # Check that we're not using external storage libraries
            storage_source = CustomFileStorage.__module__
            assert 'boto3' not in storage_source
            assert 'azure' not in storage_source
            assert 'google.cloud' not in storage_source
            
            # Check that we're using standard library file operations
            assert 'os' in storage_source
            assert 'pathlib' in storage_source
            
            self.logger.info("✅ Custom implementation philosophy maintained")
            
        except Exception as e:
            pytest.fail(f"Custom implementation philosophy test failed: {e}")


def run_phase2_tests():
    """Run all Phase 2 tests"""
    print("🚀 Running Phase 2 Data Persistence Tests...")
    
    test_instance = TestPhase2DataPersistence()
    test_instance.setup_method()
    
    # Run all tests
    test_methods = [
        test_instance.test_1_database_initialization,
        test_instance.test_2_task_creation_and_retrieval,
        test_instance.test_3_task_update,
        test_instance.test_4_analysis_result_storage,
        test_instance.test_5_file_storage_initialization,
        test_instance.test_6_file_upload_and_validation,
        test_instance.test_7_file_deletion,
        test_instance.test_8_temp_file_operations,
        test_instance.test_9_export_functionality,
        test_instance.test_10_backup_functionality,
        test_instance.test_11_pdf_service_integration,
        test_instance.test_12_data_persistence_across_restarts,
        test_instance.test_13_custom_implementation_philosophy
    ]
    
    passed = 0
    failed = 0
    
    for test_method in test_methods:
        try:
            test_method()
            passed += 1
            print(f"✅ {test_method.__name__}")
        except Exception as e:
            failed += 1
            print(f"❌ {test_method.__name__}: {e}")
    
    print(f"\n📊 Phase 2 Test Results:")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"📈 Success Rate: {passed/(passed+failed)*100:.1f}%")
    
    if failed == 0:
        print("🎉 All Phase 2 data persistence features are working correctly!")
        return True
    else:
        print("⚠️ Some Phase 2 features need attention.")
        return False


if __name__ == "__main__":
    run_phase2_tests() 