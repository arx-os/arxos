"""
File Storage Service for PDF Analysis

This module contains the file storage service for PDF analysis operations.
It provides secure file upload, validation, and management capabilities.
"""

import logging
import os
import shutil
import tempfile
from pathlib import Path
from typing import Optional, Tuple
from datetime import datetime
import hashlib
import mimetypes

from domain.exceptions import FileStorageError, ValidationError


class FileStorageService:
    """
    File storage service for PDF analysis operations.
    
    This service provides secure file upload, validation, and management
    capabilities for PDF files and analysis results.
    """
    
    def __init__(self, storage_base_path: str, max_file_size: int = 100 * 1024 * 1024):
    """
    Perform __init__ operation

Args:
        storage_base_path: Description of storage_base_path
        max_file_size: Description of max_file_size

Returns:
        Description of return value

Raises:
        Exception: Description of exception

Example:
        result = __init__(param)
        print(result)
    """
        self.storage_base_path = Path(storage_base_path)
        self.max_file_size = max_file_size  # 100MB default
        self.logger = logging.getLogger(__name__)
        
        # Ensure storage directory exists
        self.storage_base_path.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories
        self.uploads_path = self.storage_base_path / "uploads"
        self.results_path = self.storage_base_path / "results"
        self.temp_path = self.storage_base_path / "temp"
        self.backup_path = self.storage_base_path / "backup"
        
        for path in [self.uploads_path, self.results_path, self.temp_path, self.backup_path]:
            path.mkdir(exist_ok=True)
    
    async def save_uploaded_file(
        self,
        task_id: str,
        filename: str,
        file_content: bytes
    ) -> str:
        """
        Save uploaded file to storage.
        
        Args:
            task_id: Task ID for organization
            filename: Original filename
            file_content: File content as bytes
            
        Returns:
            File path where saved
            
        Raises:
            ValidationError: If file validation fails
            FileStorageError: If storage operation fails
        """
        try:
            # Validate file
            self._validate_file(filename, file_content)
            
            # Create task directory
            task_dir = self.uploads_path / task_id
            task_dir.mkdir(exist_ok=True)
            
            # Generate safe filename
            safe_filename = self._generate_safe_filename(filename)
            file_path = task_dir / safe_filename
            
            # Save file
            with open(file_path, 'wb') as f:
                f.write(file_content)
            
            # Verify file was saved correctly
            if not file_path.exists():
                raise FileStorageError("File was not saved successfully")
            
            self.logger.info(f"Saved uploaded file: {file_path}")
            return str(file_path)
            
        except (ValidationError, FileStorageError):
            raise
        except Exception as e:
            self.logger.error(f"Error saving uploaded file: {e}")
            raise FileStorageError(f"Failed to save uploaded file: {e}")
    
    async def get_file_content(self, task_id: str, filename: str) -> bytes:
        """
        Get file content from storage.
        
        Args:
            task_id: Task ID
            filename: Filename to retrieve
            
        Returns:
            File content as bytes
            
        Raises:
            FileStorageError: If file not found or read fails
        """
        try:
            file_path = self.uploads_path / task_id / filename
            
            if not file_path.exists():
                raise FileStorageError(f"File not found: {file_path}")
            
            with open(file_path, 'rb') as f:
                content = f.read()
            
            self.logger.info(f"Retrieved file content: {file_path}")
            return content
            
        except FileStorageError:
            raise
        except Exception as e:
            self.logger.error(f"Error getting file content: {e}")
            raise FileStorageError(f"Failed to get file content: {e}")
    
    async def save_analysis_result(
        self,
        task_id: str,
        result_data: dict,
        format_type: str = 'json'
    ) -> str:
        """
        Save analysis result to storage.
        
        Args:
            task_id: Task ID
            result_data: Analysis result data
            format_type: Output format ('json', 'csv', 'pdf', 'excel')
            
        Returns:
            File path where saved
            
        Raises:
            FileStorageError: If storage operation fails
        """
        try:
            # Create results directory
            result_dir = self.results_path / task_id
            result_dir.mkdir(exist_ok=True)
            
            # Generate filename
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            filename = f"analysis_result_{timestamp}.{format_type}"
            file_path = result_dir / filename
            
            # Save based on format
            if format_type == 'json':
                import json
                with open(file_path, 'w') as f:
                    json.dump(result_data, f, indent=2, default=str)
            elif format_type == 'csv':
                import csv
                with open(file_path, 'w', newline='') as f:
                    writer = csv.writer(f)
                    # Flatten result data for CSV
                    flattened_data = self._flatten_dict(result_data)
                    for key, value in flattened_data.items():
                        writer.writerow([key, value])
            else:
                # For other formats, save as text
                with open(file_path, 'w') as f:
                    f.write(str(result_data))
            
            self.logger.info(f"Saved analysis result: {file_path}")
            return str(file_path)
            
        except Exception as e:
            self.logger.error(f"Error saving analysis result: {e}")
            raise FileStorageError(f"Failed to save analysis result: {e}")
    
    async def export_analysis_result(
        self,
        task_id: str,
        export_format: str,
        include_metadata: bool = True
    ) -> Tuple[bytes, str]:
        """
        Export analysis result in specified format.
        
        Args:
            task_id: Task ID
            export_format: Export format ('json', 'csv', 'pdf', 'excel')
            include_metadata: Whether to include metadata
            
        Returns:
            Tuple of (file_content, filename)
            
        Raises:
            FileStorageError: If export fails
        """
        try:
            # Get analysis result
            result_dir = self.results_path / task_id
            if not result_dir.exists():
                raise FileStorageError(f"No results found for task: {task_id}")
            
            # Find latest result file
            result_files = list(result_dir.glob("analysis_result_*.json"))
            if not result_files:
                raise FileStorageError(f"No result files found for task: {task_id}")
            
            latest_result = max(result_files, key=lambda f: f.stat().st_mtime)
            
            # Read result data
            import json
            with open(latest_result, 'r') as f:
                result_data = json.load(f)
            
            # Generate export filename
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            filename = f"export_{task_id}_{timestamp}.{export_format}"
            
            # Convert to requested format
            if export_format == 'json':
                content = json.dumps(result_data, indent=2, default=str).encode('utf-8')
            elif export_format == 'csv':
                import csv
                import io
                output = io.StringIO()
                writer = csv.writer(output)
                flattened_data = self._flatten_dict(result_data)
                for key, value in flattened_data.items():
                    writer.writerow([key, value])
                content = output.getvalue().encode('utf-8')
            else:
                # Default to text format
                content = str(result_data).encode('utf-8')
            
            self.logger.info(f"Exported analysis result: {filename}")
            return content, filename
            
        except FileStorageError:
            raise
        except Exception as e:
            self.logger.error(f"Error exporting analysis result: {e}")
            raise FileStorageError(f"Failed to export analysis result: {e}")
    
    async def delete_file(self, task_id: str, filename: str) -> bool:
        """
        Delete file from storage.
        
        Args:
            task_id: Task ID
            filename: Filename to delete
            
        Returns:
            True if deleted successfully
            
        Raises:
            FileStorageError: If deletion fails
        """
        try:
            file_path = self.uploads_path / task_id / filename
            
            if file_path.exists():
                file_path.unlink()
                self.logger.info(f"Deleted file: {file_path}")
                return True
            else:
                self.logger.warning(f"File not found for deletion: {file_path}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error deleting file: {e}")
            raise FileStorageError(f"Failed to delete file: {e}")
    
    async def cleanup_task_files(self, task_id: str) -> bool:
        """
        Clean up all files for a task.
        
        Args:
            task_id: Task ID to cleanup
            
        Returns:
            True if cleanup successful
            
        Raises:
            FileStorageError: If cleanup fails
        """
        try:
            # Clean up uploads
            upload_dir = self.uploads_path / task_id
            if upload_dir.exists():
                shutil.rmtree(upload_dir)
            
            # Clean up results
            result_dir = self.results_path / task_id
            if result_dir.exists():
                shutil.rmtree(result_dir)
            
            # Clean up temp files
            temp_dir = self.temp_path / task_id
            if temp_dir.exists():
                shutil.rmtree(temp_dir)
            
            self.logger.info(f"Cleaned up files for task: {task_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error cleaning up task files: {e}")
            raise FileStorageError(f"Failed to cleanup task files: {e}")
    
    async def create_backup(self, task_id: str) -> str:
        """
        Create backup of task files.
        
        Args:
            task_id: Task ID to backup
            
        Returns:
            Backup file path
            
        Raises:
            FileStorageError: If backup fails
        """
        try:
            backup_dir = self.backup_path / task_id
            backup_dir.mkdir(exist_ok=True)
            
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"backup_{task_id}_{timestamp}.tar.gz"
            backup_path = backup_dir / backup_filename
            
            # Create tar.gz backup
            import tarfile
            with tarfile.open(backup_path, 'w:gz') as tar:
                # Add uploads
                upload_dir = self.uploads_path / task_id
                if upload_dir.exists():
                    tar.add(upload_dir, arcname=f"{task_id}/uploads")
                
                # Add results
                result_dir = self.results_path / task_id
                if result_dir.exists():
                    tar.add(result_dir, arcname=f"{task_id}/results")
            
            self.logger.info(f"Created backup: {backup_path}")
            return str(backup_path)
            
        except Exception as e:
            self.logger.error(f"Error creating backup: {e}")
            raise FileStorageError(f"Failed to create backup: {e}")
    
    def _validate_file(self, filename: str, file_content: bytes) -> None:
        """
        Validate uploaded file.
        
        Args:
            filename: Original filename
            file_content: File content
            
        Raises:
            ValidationError: If validation fails
        """
        # Check file size
        if len(file_content) > self.max_file_size:
            raise ValidationError(f"File size exceeds maximum allowed size of {self.max_file_size} bytes")
        
        # Check file extension
        if not filename.lower().endswith('.pdf'):
            raise ValidationError("Only PDF files are allowed")
        
        # Check file content (basic PDF header check)
        if not file_content.startswith(b'%PDF'):
            raise ValidationError("File does not appear to be a valid PDF")
        
        # Check for malicious content (basic check)
        if b'<script>' in file_content.lower():
            raise ValidationError("File contains potentially malicious content")
    
    def _generate_safe_filename(self, original_filename: str) -> str:
        """
        Generate safe filename from original.
        
        Args:
            original_filename: Original filename
            
        Returns:
            Safe filename
        """
        # Remove path separators and special characters
        safe_name = Path(original_filename).name
        safe_name = "".join(c for c in safe_name if c.isalnum() or c in "._-")
        
        # Add timestamp to ensure uniqueness
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        return f"{timestamp}_{safe_name}"
    
    def _flatten_dict(self, data: dict, prefix: str = "") -> dict:
        """
        Flatten nested dictionary for CSV export.
        
        Args:
            data: Dictionary to flatten
            prefix: Current key prefix
            
        Returns:
            Flattened dictionary
        """
        flattened = {}
        
        for key, value in data.items():
            new_key = f"{prefix}.{key}" if prefix else key
            
            if isinstance(value, dict):
                flattened.update(self._flatten_dict(value, new_key))
            elif isinstance(value, list):
                flattened[new_key] = str(value)
            else:
                flattened[new_key] = str(value)
        
        return flattened
    
    def get_storage_info(self) -> dict:
        """
        Get storage information.
        
        Returns:
            Storage information dictionary
        """
        try:
            total_size = sum(f.stat().st_size for f in self.storage_base_path.rglob('*') if f.is_file())
            
            return {
                'storage_path': str(self.storage_base_path),
                'total_size_bytes': total_size,
                'total_size_mb': total_size / (1024 * 1024),
                'uploads_count': len(list(self.uploads_path.rglob('*'))),
                'results_count': len(list(self.results_path.rglob('*'))),
                'backups_count': len(list(self.backup_path.rglob('*'))),
                'max_file_size_bytes': self.max_file_size,
                'max_file_size_mb': self.max_file_size / (1024 * 1024)
            }
            
        except Exception as e:
            self.logger.error(f"Error getting storage info: {e}")
            return {} 