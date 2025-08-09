"""
Basic integration tests for Arxos platform.
"""
import unittest
import tempfile
import os


class TestBasicIntegration(unittest.TestCase):
    """Test basic integration functionality."""

    def test_file_operations(self):
        """Test file read/write operations."""
        # Create a temporary file
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("test data")
            temp_file = f.name

        try:
            # Test reading the file
            with open(temp_file, 'r') as f:
                content = f.read()
            self.assertEqual(content, "test data", "File content should match")
        finally:
            # Clean up
            os.unlink(temp_file)

    def test_directory_operations(self):
        """Test directory operations."""
        # Create a temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            # Test creating a file in the directory
            test_file = os.path.join(temp_dir, "test.txt")
            with open(test_file, 'w') as f:
                f.write("test content")

            # Test that file exists
            self.assertTrue(os.path.exists(test_file), "File should exist")

            # Test reading the file
            with open(test_file, 'r') as f:
                content = f.read()
            self.assertEqual(content, "test content", "File content should match")

    def test_import_integration(self):
        """Test that all major modules can be imported together."""
        try:
            # Test importing multiple modules
            import application
            import domain
            import infrastructure
            import api

            self.assertTrue(True, "All modules imported successfully")
        except ImportError as e:
            self.fail(f"Failed to import modules: {e}")

    def test_basic_data_structures(self):
        """Test basic data structure operations."""
        # Test list operations
        test_list = [1, 2, 3, 4, 5]
        self.assertEqual(len(test_list), 5, "List length should be correct")
        self.assertEqual(sum(test_list), 15, "List sum should be correct")

        # Test dictionary operations
        test_dict = {"a": 1, "b": 2, "c": 3}
        self.assertEqual(len(test_dict), 3, "Dictionary length should be correct")
        self.assertEqual(test_dict["a"], 1, "Dictionary value should be correct")

        # Test set operations
        test_set = {1, 2, 3, 4, 5}
        self.assertEqual(len(test_set), 5, "Set length should be correct")
        self.assertIn(3, test_set, "Set should contain element")


if __name__ == '__main__':
    unittest.main()
