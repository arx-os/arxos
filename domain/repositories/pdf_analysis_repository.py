"""
PDF Analysis Repository Interface

This module contains the repository interface for PDF analysis domain entities.
The repository interface defines the contract for data access operations.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime

from ..entities.pdf_analysis import PDFAnalysis
from ..value_objects import TaskId, UserId, TaskStatus


class PDFAnalysisRepository(ABC):
    """
    Repository interface for PDF analysis entities.

    This interface defines the contract for data access operations
    on PDF analysis domain entities.
    """

    @abstractmethod
def create(self, pdf_analysis: PDFAnalysis) -> PDFAnalysis:
        """
        Create a new PDF analysis.

        Args:
            pdf_analysis: The PDF analysis entity to create

        Returns:
            The created PDF analysis entity

        Raises:
            RepositoryError: If creation fails
        """
        pass

    @abstractmethod
def get_by_id(self, task_id: TaskId) -> Optional[PDFAnalysis]:
        """
        Get PDF analysis by task ID.

        Args:
            task_id: The task ID to search for

        Returns:
            The PDF analysis entity if found, None otherwise

        Raises:
            RepositoryError: If retrieval fails
        """
        pass

    @abstractmethod
def update(self, pdf_analysis: PDFAnalysis) -> PDFAnalysis:
        """
        Update an existing PDF analysis.

        Args:
            pdf_analysis: The PDF analysis entity to update

        Returns:
            The updated PDF analysis entity

        Raises:
            RepositoryError: If update fails
            EntityNotFoundError: If entity not found
        """
        pass

    @abstractmethod
def delete(self, task_id: TaskId) -> bool:
        """
        Delete a PDF analysis by task ID.

        Args:
            task_id: The task ID to delete

        Returns:
            True if deleted successfully, False otherwise

        Raises:
            RepositoryError: If deletion fails
        """
        pass

    @abstractmethod
def get_by_user_id(self, user_id: UserId, limit: int = 50) -> List[PDFAnalysis]:
        """
        Get PDF analyses by user ID.

        Args:
            user_id: The user ID to search for
            limit: Maximum number of results to return

        Returns:
            List of PDF analysis entities

        Raises:
            RepositoryError: If retrieval fails
        """
        pass

    @abstractmethod
def get_by_status(self, status: TaskStatus, limit: int = 50) -> List[PDFAnalysis]:
        """
        Get PDF analyses by status.

        Args:
            status: The status to search for
            limit: Maximum number of results to return

        Returns:
            List of PDF analysis entities

        Raises:
            RepositoryError: If retrieval fails
        """
        pass

    @abstractmethod
def get_pending_analyses(self, limit: int = 10) -> List[PDFAnalysis]:
        """
        Get pending PDF analyses for processing.

        Args:
            limit: Maximum number of results to return

        Returns:
            List of pending PDF analysis entities

        Raises:
            RepositoryError: If retrieval fails
        """
        pass

    @abstractmethod
def get_processing_analyses(self, limit: int = 10) -> List[PDFAnalysis]:
        """
        Get currently processing PDF analyses.

        Args:
            limit: Maximum number of results to return

        Returns:
            List of processing PDF analysis entities

        Raises:
            RepositoryError: If retrieval fails
        """
        pass

    @abstractmethod
def get_completed_analyses(self, user_id: Optional[UserId] = None, limit: int = 50) -> List[PDFAnalysis]:
        """
        Get completed PDF analyses.

        Args:
            user_id: Optional user ID to filter by
            limit: Maximum number of results to return

        Returns:
            List of completed PDF analysis entities

        Raises:
            RepositoryError: If retrieval fails
        """
        pass

    @abstractmethod
def get_failed_analyses(self, user_id: Optional[UserId] = None, limit: int = 50) -> List[PDFAnalysis]:
        """
        Get failed PDF analyses.

        Args:
            user_id: Optional user ID to filter by
            limit: Maximum number of results to return

        Returns:
            List of failed PDF analysis entities

        Raises:
            RepositoryError: If retrieval fails
        """
        pass

    @abstractmethod
def count_by_user_id(self, user_id: UserId) -> int:
        """
        Count PDF analyses by user ID.

        Args:
            user_id: The user ID to count for

        Returns:
            Number of PDF analyses for the user

        Raises:
            RepositoryError: If count fails
        """
        pass

    @abstractmethod
def count_by_status(self, status: TaskStatus) -> int:
        """
        Count PDF analyses by status.

        Args:
            status: The status to count for

        Returns:
            Number of PDF analyses with the status

        Raises:
            RepositoryError: If count fails
        """
        pass

    @abstractmethod
def get_statistics(self) -> Dict[str, Any]:
        """
        Get PDF analysis statistics.

        Returns:
            Dictionary containing statistics

        Raises:
            RepositoryError: If statistics retrieval fails
        """
        pass

    @abstractmethod
def cleanup_old_analyses(self, days_to_keep: int = 30) -> int:
        """
        Clean up old PDF analyses.

        Args:
            days_to_keep: Number of days to keep analyses

        Returns:
            Number of analyses cleaned up

        Raises:
            RepositoryError: If cleanup fails
        """
        pass

    @abstractmethod
def exists(self, task_id: TaskId) -> bool:
        """
        Check if PDF analysis exists.

        Args:
            task_id: The task ID to check

        Returns:
            True if analysis exists, False otherwise

        Raises:
            RepositoryError: If check fails
        """
        pass

    @abstractmethod
def get_analysis_with_result(self, task_id: TaskId) -> Optional[PDFAnalysis]:
        """
        Get PDF analysis with its analysis result.

        Args:
            task_id: The task ID to search for

        Returns:
            The PDF analysis entity with result if found, None otherwise

        Raises:
            RepositoryError: If retrieval fails
        """
        pass

    @abstractmethod
def save_analysis_result(self, task_id: TaskId, analysis_result: Dict[str, Any]) -> bool:
        """
        Save analysis result for a PDF analysis.

        Args:
            task_id: The task ID to save result for
            analysis_result: The analysis result data

        Returns:
            True if saved successfully, False otherwise

        Raises:
            RepositoryError: If save fails
        """
        pass
