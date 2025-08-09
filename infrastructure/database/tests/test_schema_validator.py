"""
Tests for the Schema Validator

Tests the schema validation functionality including:
- Foreign key ordering validation
- Index presence validation
- SQL parsing and error detection
- CI integration scenarios
"""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

from tools.schema_validator import SchemaValidator, ValidationError, TableInfo


class TestSchemaValidator:
    """Test schema validator functionality."""

    @pytest.fixture
def temp_migrations_dir(self):
        """Create a temporary migrations directory for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            migrations_dir = Path(temp_dir) / "migrations"
            migrations_dir.mkdir()
            yield migrations_dir

    @pytest.fixture
def validator(self, temp_migrations_dir):
        """Create a schema validator instance."""
        return SchemaValidator(str(temp_migrations_dir)
    def test_validator_initialization(self, validator):
        """Test validator initialization."""
        assert validator.migrations_dir.exists()
        assert len(validator.tables) == 0
        assert len(validator.errors) == 0
        assert len(validator.warnings) == 0

    def test_parse_create_table(self, validator, temp_migrations_dir):
        """Test parsing CREATE TABLE statements."""
        migration_file = temp_migrations_dir / "001_create_users.sql"
        migration_file.write_text("""
        CREATE TABLE users (
            id INTEGER PRIMARY KEY,
            name VARCHAR(255)
        );
        """)
        validator._parse_migration_file(migration_file)

        assert "users" in validator.tables
        table_info = validator.tables["users"]
        assert table_info.name == "users"
        assert table_info.file_path == str(migration_file)
        assert table_info.line_number == 2

    def test_parse_foreign_key(self, validator, temp_migrations_dir):
        """Test parsing foreign key declarations."""
        migration_file = temp_migrations_dir / "002_create_posts.sql"
        migration_file.write_text("""
        CREATE TABLE posts (
            id INTEGER PRIMARY KEY,
            user_id INTEGER,
            title VARCHAR(255),
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
        """)
        validator._parse_migration_file(migration_file)

        assert "posts" in validator.tables
        table_info = validator.tables["posts"]
        assert ("user_id", "users") in table_info.foreign_keys

    def test_parse_index(self, validator, temp_migrations_dir):
        """Test parsing index declarations."""
        migration_file = temp_migrations_dir / "003_add_indexes.sql"
        migration_file.write_text("""
        CREATE INDEX idx_posts_user_id ON posts(user_id);
        """)
        validator._parse_migration_file(migration_file)

        assert "posts" in validator.tables
        table_info = validator.tables["posts"]
        assert "user_id" in table_info.indexes

    def test_parse_alter_table_foreign_key(self, validator, temp_migrations_dir):
        """Test parsing ALTER TABLE ADD FOREIGN KEY."""
        migration_file = temp_migrations_dir / "004_add_foreign_key.sql"
        migration_file.write_text("""
        ALTER TABLE posts ADD FOREIGN KEY (user_id) REFERENCES users(id);
        """)
        validator._parse_migration_file(migration_file)

        assert "posts" in validator.tables
        table_info = validator.tables["posts"]
        assert ("user_id", "users") in table_info.foreign_keys

    def test_parse_alter_table_index(self, validator, temp_migrations_dir):
        """Test parsing ALTER TABLE ADD INDEX."""
        migration_file = temp_migrations_dir / "005_add_index.sql"
        migration_file.write_text("""
        ALTER TABLE posts ADD INDEX idx_posts_user_id (user_id);
        """)
        validator._parse_migration_file(migration_file)

        assert "posts" in validator.tables
        table_info = validator.tables["posts"]
        assert "user_id" in table_info.indexes

    def test_validate_foreign_key_ordering_valid(self, validator, temp_migrations_dir):
        """Test foreign key ordering validation with valid order."""
        # Create users table first
        users_file = temp_migrations_dir / "001_create_users.sql"
        users_file.write_text("""
        CREATE TABLE users (
            id INTEGER PRIMARY KEY,
            name VARCHAR(255)
        );
        """)
        # Create posts table second
        posts_file = temp_migrations_dir / "002_create_posts.sql"
        posts_file.write_text("""
        CREATE TABLE posts (
            id INTEGER PRIMARY KEY,
            user_id INTEGER,
            title VARCHAR(255),
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
        """)
        validator._parse_migration_file(users_file)
        validator._parse_migration_file(posts_file)
        validator._validate_foreign_key_ordering()

        assert len(validator.errors) == 0

    def test_validate_foreign_key_ordering_invalid(self, validator, temp_migrations_dir):
        """Test foreign key ordering validation with invalid order."""
        # Create posts table first (references users)
        posts_file = temp_migrations_dir / "001_create_posts.sql"
        posts_file.write_text("""
        CREATE TABLE posts (
            id INTEGER PRIMARY KEY,
            user_id INTEGER,
            title VARCHAR(255),
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
        """)
        # Create users table second
        users_file = temp_migrations_dir / "002_create_users.sql"
        users_file.write_text("""
        CREATE TABLE users (
            id INTEGER PRIMARY KEY,
            name VARCHAR(255)
        );
        """)
        validator._parse_migration_file(posts_file)
        validator._parse_migration_file(users_file)
        validator._validate_foreign_key_ordering()

        assert len(validator.errors) == 1
        error = validator.errors[0]
        assert error.error_type == "missing_referenced_table"
        assert "users" in error.message

    def test_validate_foreign_key_indexes_valid(self, validator, temp_migrations_dir):
        """Test foreign key index validation with valid indexes."""
        migration_file = temp_migrations_dir / "001_create_posts.sql"
        migration_file.write_text("""
        CREATE TABLE posts (
            id INTEGER PRIMARY KEY,
            user_id INTEGER,
            title VARCHAR(255),
            FOREIGN KEY (user_id) REFERENCES users(id),
            INDEX idx_posts_user_id (user_id)
        );
        """)
        validator._parse_migration_file(migration_file)
        validator._validate_foreign_key_indexes()

        assert len(validator.errors) == 0

    def test_validate_foreign_key_indexes_invalid(self, validator, temp_migrations_dir):
        """Test foreign key index validation with missing indexes."""
        migration_file = temp_migrations_dir / "001_create_posts.sql"
        migration_file.write_text("""
        CREATE TABLE posts (
            id INTEGER PRIMARY KEY,
            user_id INTEGER,
            title VARCHAR(255),
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
        """)
        validator._parse_migration_file(migration_file)
        validator._validate_foreign_key_indexes()

        assert len(validator.errors) == 1
        error = validator.errors[0]
        assert error.error_type == "missing_foreign_key_index"
        assert "user_id" in error.message

    def test_validate_migrations_success(self, validator, temp_migrations_dir):
        """Test successful migration validation."""
        # Create valid migration files
        users_file = temp_migrations_dir / "001_create_users.sql"
        users_file.write_text("""
        CREATE TABLE users (
            id INTEGER PRIMARY KEY,
            name VARCHAR(255)
        );
        """)
        posts_file = temp_migrations_dir / "002_create_posts.sql"
        posts_file.write_text("""
        CREATE TABLE posts (
            id INTEGER PRIMARY KEY,
            user_id INTEGER,
            title VARCHAR(255),
            FOREIGN KEY (user_id) REFERENCES users(id),
            INDEX idx_posts_user_id (user_id)
        );
        """)
        success = validator.validate_migrations()

        assert success is True
        assert len(validator.errors) == 0
        assert len(validator.tables) == 2

    def test_validate_migrations_failure(self, validator, temp_migrations_dir):
        """Test failed migration validation."""
        # Create invalid migration file (missing referenced table)
        posts_file = temp_migrations_dir / "001_create_posts.sql"
        posts_file.write_text("""
        CREATE TABLE posts (
            id INTEGER PRIMARY KEY,
            user_id INTEGER,
            title VARCHAR(255),
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
        """)
        success = validator.validate_migrations()

        assert success is False
        assert len(validator.errors) > 0

    def test_validate_migrations_no_files(self, validator):
        """Test validation with no migration files."""
        success = validator.validate_migrations()

        assert success is True
        assert len(validator.errors) == 0

    def test_validate_migrations_directory_not_found(self):
        """Test validation with non-existent directory."""
        validator = SchemaValidator("non_existent_directory")
        success = validator.validate_migrations()

        assert success is False
        assert len(validator.errors) == 1
        error = validator.errors[0]
        assert error.error_type == "directory_not_found"

    def test_parse_migration_file_error(self, validator, temp_migrations_dir):
        """Test parsing error handling."""
        migration_file = temp_migrations_dir / "invalid.sql"
        migration_file.write_text("""
        CREATE TABLE users (
            id INTEGER PRIMARY KEY,
            name VARCHAR(255)
        """)  # Missing closing parenthesis"

        # Mock file reading to raise an exception
        with patch('builtins.open', side_effect=Exception("File read error")):
            validator._parse_migration_file(migration_file)

        assert len(validator.errors) == 1
        error = validator.errors[0]
        assert error.error_type == "parse_error"

    def test_get_validation_summary(self, validator, temp_migrations_dir):
        """Test validation summary generation."""
        # Create some test data
        validator.tables["users"] = TableInfo("users", "test.sql", 1)
        validator.tables["posts"] = TableInfo("posts", "test.sql", 2)
        validator.errors.append(ValidationError(
            "test_error", "Test error message", "test.sql", 1
        )
        summary = validator.get_validation_summary()

        assert summary["total_tables"] == 2
        assert summary["errors"] == 1
        assert summary["warnings"] == 0
        assert summary["passed"] is False
        assert "users" in summary["tables"]
        assert "posts" in summary["tables"]
        assert len(summary["error_details"]) == 1

    def test_complex_migration_scenario(self, validator, temp_migrations_dir):
        """Test complex migration scenario with multiple tables and relationships."""
        # Create users table
        users_file = temp_migrations_dir / "001_create_users.sql"
        users_file.write_text("""
        CREATE TABLE users (
            id INTEGER PRIMARY KEY,
            name VARCHAR(255),
            email VARCHAR(255) UNIQUE
        );
        """)
        # Create categories table
        categories_file = temp_migrations_dir / "002_create_categories.sql"
        categories_file.write_text("""
        CREATE TABLE categories (
            id INTEGER PRIMARY KEY,
            name VARCHAR(255)
        );
        """)
        # Create posts table with foreign keys
        posts_file = temp_migrations_dir / "003_create_posts.sql"
        posts_file.write_text("""
        CREATE TABLE posts (
            id INTEGER PRIMARY KEY,
            user_id INTEGER,
            category_id INTEGER,
            title VARCHAR(255),
            content TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (category_id) REFERENCES categories(id),
            INDEX idx_posts_user_id (user_id),
            INDEX idx_posts_category_id (category_id)
        );
        """)
        # Create comments table
        comments_file = temp_migrations_dir / "004_create_comments.sql"
        comments_file.write_text("""
        CREATE TABLE comments (
            id INTEGER PRIMARY KEY,
            post_id INTEGER,
            user_id INTEGER,
            content TEXT,
            FOREIGN KEY (post_id) REFERENCES posts(id),
            FOREIGN KEY (user_id) REFERENCES users(id),
            INDEX idx_comments_post_id (post_id),
            INDEX idx_comments_user_id (user_id)
        );
        """)
        success = validator.validate_migrations()

        assert success is True
        assert len(validator.tables) == 4
        assert len(validator.errors) == 0

        # Verify all tables have proper indexes
        posts_table = validator.tables["posts"]
        assert ("user_id", "users") in posts_table.foreign_keys
        assert ("category_id", "categories") in posts_table.foreign_keys
        assert "user_id" in posts_table.indexes
        assert "category_id" in posts_table.indexes

        comments_table = validator.tables["comments"]
        assert ("post_id", "posts") in comments_table.foreign_keys
        assert ("user_id", "users") in comments_table.foreign_keys
        assert "post_id" in comments_table.indexes
        assert "user_id" in comments_table.indexes


class TestValidationError:
    """Test ValidationError class."""

    def test_validation_error_creation(self):
        """Test ValidationError creation."""
        error = ValidationError(
            error_type="test_error",
            message="Test error message",
            file_path="test.sql",
            line_number=10,
            severity="error"
        )

        assert error.error_type == "test_error"
        assert error.message == "Test error message"
        assert error.file_path == "test.sql"
        assert error.line_number == 10
        assert error.severity == "error"

    def test_validation_error_default_severity(self):
        """Test ValidationError with default severity."""
        error = ValidationError(
            error_type="test_error",
            message="Test error message",
            file_path="test.sql",
            line_number=10
        )

        assert error.severity == "error"


class TestTableInfo:
    """Test TableInfo class."""

    def test_table_info_creation(self):
        """Test TableInfo creation."""
        table_info = TableInfo(
            name="users",
            file_path="test.sql",
            line_number=5
        )

        assert table_info.name == "users"
        assert table_info.file_path == "test.sql"
        assert table_info.line_number == 5
        assert table_info.created is False
        assert table_info.foreign_keys == []
        assert table_info.indexes == set()

    def test_table_info_with_foreign_keys(self):
        """Test TableInfo with foreign keys."""
        table_info = TableInfo(
            name="posts",
            file_path="test.sql",
            line_number=10
        )

        table_info.foreign_keys.append(("user_id", "users")
        table_info.indexes.add("user_id")

        assert ("user_id", "users") in table_info.foreign_keys
        assert "user_id" in table_info.indexes


if __name__ == "__main__":
    pytest.main([__file__])
