"""
PostgreSQL PDF Analysis Repository Implementation

This module contains the PostgreSQL implementation of the PDFAnalysisRepository interface.
It provides data access operations for PDF analysis entities using PostgreSQL.
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import json

import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2.pool import SimpleConnectionPool

from domain.entities.pdf_analysis import PDFAnalysis
from domain.value_objects import TaskId, UserId, TaskStatus, ConfidenceScore
from domain.repositories.pdf_analysis_repository import PDFAnalysisRepository
from domain.exceptions import (
    RepositoryError, EntityNotFoundError, InvalidPDFAnalysisError
)
from infrastructure.database.connection_manager import DatabaseConnectionManager


class PostgreSQLPDFAnalysisRepository(PDFAnalysisRepository):
    """
    PostgreSQL implementation of PDFAnalysisRepository.
    
    This repository provides data access operations for PDF analysis entities
    using PostgreSQL as the underlying database.
    """
    
    def __init__(self, connection_manager: DatabaseConnectionManager):
    """
    Perform __init__ operation

Args:
        connection_manager: Description of connection_manager

Returns:
        Description of return value

Raises:
        Exception: Description of exception

Example:
        result = __init__(param)
        print(result)
    """
        self.connection_manager = connection_manager
        self.logger = logging.getLogger(__name__)
        
        # Initialize database tables
        self._init_database()
    
    def _init_database(self) -> None:
        """Initialize database tables for PDF analysis."""
        try:
            with self.connection_manager.get_connection() as conn:
                with conn.cursor() as cursor:
                    # Create PDF analysis tasks table
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS pdf_analysis_tasks (
                            task_id VARCHAR(255) PRIMARY KEY,
                            user_id VARCHAR(255) NOT NULL,
                            filename VARCHAR(255) NOT NULL,
                            file_path TEXT NOT NULL,
                            status VARCHAR(50) NOT NULL,
                            include_cost_estimation BOOLEAN DEFAULT TRUE,
                            include_timeline BOOLEAN DEFAULT TRUE,
                            include_quantities BOOLEAN DEFAULT TRUE,
                            requirements JSONB DEFAULT '{}',
                            confidence DECIMAL(3,2),
                            systems_found JSONB,
                            total_components INTEGER,
                            processing_time DECIMAL(10,3),
                            error_message TEXT,
                            analysis_result JSONB,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    """)
                    
                    # Create indexes for performance
                    cursor.execute("""
                        CREATE INDEX IF NOT EXISTS idx_pdf_analysis_user_id 
                        ON pdf_analysis_tasks(user_id)
                    """)
                    
                    cursor.execute("""
                        CREATE INDEX IF NOT EXISTS idx_pdf_analysis_status 
                        ON pdf_analysis_tasks(status)
                    """)
                    
                    cursor.execute("""
                        CREATE INDEX IF NOT EXISTS idx_pdf_analysis_created_at 
                        ON pdf_analysis_tasks(created_at)
                    """)
                    
                    cursor.execute("""
                        CREATE INDEX IF NOT EXISTS idx_pdf_analysis_updated_at 
                        ON pdf_analysis_tasks(updated_at)
                    """)
                    
                    conn.commit()
                    self.logger.info("PDF analysis database tables initialized successfully")
                    
        except Exception as e:
            self.logger.error(f"Error initializing PDF analysis database: {e}")
            raise RepositoryError(f"Failed to initialize database: {e}")
    
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
        try:
            with self.connection_manager.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute("""
                        INSERT INTO pdf_analysis_tasks (
                            task_id, user_id, filename, file_path, status,
                            include_cost_estimation, include_timeline, include_quantities,
                            requirements, confidence, systems_found, total_components,
                            processing_time, error_message, analysis_result,
                            created_at, updated_at
                        ) VALUES (
                            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                        )
                    """, (
                        str(pdf_analysis.task_id),
                        str(pdf_analysis.user_id),
                        str(pdf_analysis.filename),
                        str(pdf_analysis.file_path),
                        str(pdf_analysis.status),
                        pdf_analysis.include_cost_estimation,
                        pdf_analysis.include_timeline,
                        pdf_analysis.include_quantities,
                        json.dumps(pdf_analysis.requirements),
                        float(pdf_analysis.confidence) if pdf_analysis.confidence else None,
                        json.dumps(pdf_analysis.systems_found) if pdf_analysis.systems_found else None,
                        pdf_analysis.total_components,
                        pdf_analysis.processing_time,
                        pdf_analysis.error_message,
                        json.dumps(pdf_analysis.analysis_result.to_dict()) if pdf_analysis.analysis_result else None,
                        pdf_analysis.created_at,
                        pdf_analysis.updated_at
                    ))
                    
                    conn.commit()
                    self.logger.info(f"Created PDF analysis: {pdf_analysis.task_id}")
                    return pdf_analysis
                    
        except Exception as e:
            self.logger.error(f"Error creating PDF analysis: {e}")
            raise RepositoryError(f"Failed to create PDF analysis: {e}")
    
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
        try:
            with self.connection_manager.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute("""
                        SELECT * FROM pdf_analysis_tasks WHERE task_id = %s
                    """, (str(task_id),))
                    
                    row = cursor.fetchone()
                    if row:
                        return self._row_to_entity(row)
                    return None
                    
        except Exception as e:
            self.logger.error(f"Error getting PDF analysis {task_id}: {e}")
            raise RepositoryError(f"Failed to get PDF analysis: {e}")
    
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
        try:
            with self.connection_manager.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute("""
                        UPDATE pdf_analysis_tasks SET
                            user_id = %s,
                            filename = %s,
                            file_path = %s,
                            status = %s,
                            include_cost_estimation = %s,
                            include_timeline = %s,
                            include_quantities = %s,
                            requirements = %s,
                            confidence = %s,
                            systems_found = %s,
                            total_components = %s,
                            processing_time = %s,
                            error_message = %s,
                            analysis_result = %s,
                            updated_at = %s
                        WHERE task_id = %s
                    """, (
                        str(pdf_analysis.user_id),
                        str(pdf_analysis.filename),
                        str(pdf_analysis.file_path),
                        str(pdf_analysis.status),
                        pdf_analysis.include_cost_estimation,
                        pdf_analysis.include_timeline,
                        pdf_analysis.include_quantities,
                        json.dumps(pdf_analysis.requirements),
                        float(pdf_analysis.confidence) if pdf_analysis.confidence else None,
                        json.dumps(pdf_analysis.systems_found) if pdf_analysis.systems_found else None,
                        pdf_analysis.total_components,
                        pdf_analysis.processing_time,
                        pdf_analysis.error_message,
                        json.dumps(pdf_analysis.analysis_result.to_dict()) if pdf_analysis.analysis_result else None,
                        pdf_analysis.updated_at,
                        str(pdf_analysis.task_id)
                    ))
                    
                    if cursor.rowcount == 0:
                        raise EntityNotFoundError(f"PDF analysis {pdf_analysis.task_id} not found")
                    
                    conn.commit()
                    self.logger.info(f"Updated PDF analysis: {pdf_analysis.task_id}")
                    return pdf_analysis
                    
        except EntityNotFoundError:
            raise
        except Exception as e:
            self.logger.error(f"Error updating PDF analysis {pdf_analysis.task_id}: {e}")
            raise RepositoryError(f"Failed to update PDF analysis: {e}")
    
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
        try:
            with self.connection_manager.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        DELETE FROM pdf_analysis_tasks WHERE task_id = %s
                    """, (str(task_id),))
                    
                    deleted = cursor.rowcount > 0
                    conn.commit()
                    
                    if deleted:
                        self.logger.info(f"Deleted PDF analysis: {task_id}")
                    
                    return deleted
                    
        except Exception as e:
            self.logger.error(f"Error deleting PDF analysis {task_id}: {e}")
            raise RepositoryError(f"Failed to delete PDF analysis: {e}")
    
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
        try:
            with self.connection_manager.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute("""
                        SELECT * FROM pdf_analysis_tasks 
                        WHERE user_id = %s 
                        ORDER BY created_at DESC 
                        LIMIT %s
                    """, (str(user_id), limit))
                    
                    rows = cursor.fetchall()
                    return [self._row_to_entity(row) for row in rows]
                    
        except Exception as e:
            self.logger.error(f"Error getting PDF analyses for user {user_id}: {e}")
            raise RepositoryError(f"Failed to get PDF analyses: {e}")
    
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
        try:
            with self.connection_manager.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute("""
                        SELECT * FROM pdf_analysis_tasks 
                        WHERE status = %s 
                        ORDER BY created_at ASC 
                        LIMIT %s
                    """, (str(status), limit))
                    
                    rows = cursor.fetchall()
                    return [self._row_to_entity(row) for row in rows]
                    
        except Exception as e:
            self.logger.error(f"Error getting PDF analyses with status {status}: {e}")
            raise RepositoryError(f"Failed to get PDF analyses: {e}")
    
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
        return self.get_by_status(TaskStatus.PENDING, limit)
    
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
        return self.get_by_status(TaskStatus.PROCESSING, limit)
    
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
        try:
            with self.connection_manager.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    if user_id:
                        cursor.execute("""
                            SELECT * FROM pdf_analysis_tasks 
                            WHERE status = %s AND user_id = %s
                            ORDER BY created_at DESC 
                            LIMIT %s
                        """, (str(TaskStatus.COMPLETED), str(user_id), limit))
                    else:
                        cursor.execute("""
                            SELECT * FROM pdf_analysis_tasks 
                            WHERE status = %s
                            ORDER BY created_at DESC 
                            LIMIT %s
                        """, (str(TaskStatus.COMPLETED), limit))
                    
                    rows = cursor.fetchall()
                    return [self._row_to_entity(row) for row in rows]
                    
        except Exception as e:
            self.logger.error(f"Error getting completed PDF analyses: {e}")
            raise RepositoryError(f"Failed to get completed PDF analyses: {e}")
    
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
        try:
            with self.connection_manager.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    if user_id:
                        cursor.execute("""
                            SELECT * FROM pdf_analysis_tasks 
                            WHERE status = %s AND user_id = %s
                            ORDER BY created_at DESC 
                            LIMIT %s
                        """, (str(TaskStatus.FAILED), str(user_id), limit))
                    else:
                        cursor.execute("""
                            SELECT * FROM pdf_analysis_tasks 
                            WHERE status = %s
                            ORDER BY created_at DESC 
                            LIMIT %s
                        """, (str(TaskStatus.FAILED), limit))
                    
                    rows = cursor.fetchall()
                    return [self._row_to_entity(row) for row in rows]
                    
        except Exception as e:
            self.logger.error(f"Error getting failed PDF analyses: {e}")
            raise RepositoryError(f"Failed to get failed PDF analyses: {e}")
    
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
        try:
            with self.connection_manager.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        SELECT COUNT(*) FROM pdf_analysis_tasks WHERE user_id = %s
                    """, (str(user_id),))
                    
                    return cursor.fetchone()[0]
                    
        except Exception as e:
            self.logger.error(f"Error counting PDF analyses for user {user_id}: {e}")
            raise RepositoryError(f"Failed to count PDF analyses: {e}")
    
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
        try:
            with self.connection_manager.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        SELECT COUNT(*) FROM pdf_analysis_tasks WHERE status = %s
                    """, (str(status),))
                    
                    return cursor.fetchone()[0]
                    
        except Exception as e:
            self.logger.error(f"Error counting PDF analyses with status {status}: {e}")
            raise RepositoryError(f"Failed to count PDF analyses: {e}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get PDF analysis statistics.
        
        Returns:
            Dictionary containing statistics
            
        Raises:
            RepositoryError: If statistics retrieval fails
        """
        try:
            with self.connection_manager.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    # Get counts by status
                    cursor.execute("""
                        SELECT status, COUNT(*) as count 
                        FROM pdf_analysis_tasks 
                        GROUP BY status
                    """)
                    status_counts = {row['status']: row['count'] for row in cursor.fetchall()}
                    
                    # Get average processing time for completed analyses
                    cursor.execute("""
                        SELECT AVG(processing_time) as avg_time 
                        FROM pdf_analysis_tasks 
                        WHERE status = %s AND processing_time IS NOT NULL
                    """, (str(TaskStatus.COMPLETED),))
                    avg_processing_time = cursor.fetchone()['avg_time'] or 0.0
                    
                    # Get average confidence for completed analyses
                    cursor.execute("""
                        SELECT AVG(confidence) as avg_confidence 
                        FROM pdf_analysis_tasks 
                        WHERE status = %s AND confidence IS NOT NULL
                    """, (str(TaskStatus.COMPLETED),))
                    avg_confidence = cursor.fetchone()['avg_confidence'] or 0.0
                    
                    # Get total components identified
                    cursor.execute("""
                        SELECT SUM(total_components) as total_components 
                        FROM pdf_analysis_tasks 
                        WHERE status = %s AND total_components IS NOT NULL
                    """, (str(TaskStatus.COMPLETED),))
                    total_components = cursor.fetchone()['total_components'] or 0
                    
                    # Get systems found count
                    cursor.execute("""
                        SELECT systems_found 
                        FROM pdf_analysis_tasks 
                        WHERE status = %s AND systems_found IS NOT NULL
                    """, (str(TaskStatus.COMPLETED),))
                    systems_data = cursor.fetchall()
                    
                    systems_count = {}
                    for row in systems_data:
                        if row['systems_found']:
                            systems = json.loads(row['systems_found'])
                            for system in systems:
                                systems_count[system] = systems_count.get(system, 0) + 1
                    
                    # Calculate success and error rates
                    total_analyses = sum(status_counts.values())
                    completed_count = status_counts.get(str(TaskStatus.COMPLETED), 0)
                    failed_count = status_counts.get(str(TaskStatus.FAILED), 0)
                    
                    success_rate = (completed_count / total_analyses * 100) if total_analyses > 0 else 0.0
                    error_rate = (failed_count / total_analyses * 100) if total_analyses > 0 else 0.0
                    
                    return {
                        'total_analyses': total_analyses,
                        'completed_analyses': completed_count,
                        'failed_analyses': failed_count,
                        'pending_analyses': status_counts.get(str(TaskStatus.PENDING), 0),
                        'processing_analyses': status_counts.get(str(TaskStatus.PROCESSING), 0),
                        'cancelled_analyses': status_counts.get(str(TaskStatus.CANCELLED), 0),
                        'average_processing_time': float(avg_processing_time),
                        'average_confidence': float(avg_confidence),
                        'total_components_identified': total_components,
                        'systems_found_count': systems_count,
                        'success_rate': success_rate,
                        'error_rate': error_rate
                    }
                    
        except Exception as e:
            self.logger.error(f"Error getting PDF analysis statistics: {e}")
            raise RepositoryError(f"Failed to get statistics: {e}")
    
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
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
            
            with self.connection_manager.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        DELETE FROM pdf_analysis_tasks 
                        WHERE created_at < %s
                    """, (cutoff_date,))
                    
                    cleaned_count = cursor.rowcount
                    conn.commit()
                    
                    self.logger.info(f"Cleaned up {cleaned_count} old PDF analyses")
                    return cleaned_count
                    
        except Exception as e:
            self.logger.error(f"Error cleaning up old PDF analyses: {e}")
            raise RepositoryError(f"Failed to cleanup old analyses: {e}")
    
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
        try:
            with self.connection_manager.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        SELECT 1 FROM pdf_analysis_tasks WHERE task_id = %s
                    """, (str(task_id),))
                    
                    return cursor.fetchone() is not None
                    
        except Exception as e:
            self.logger.error(f"Error checking if PDF analysis exists {task_id}: {e}")
            raise RepositoryError(f"Failed to check if analysis exists: {e}")
    
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
        # This is the same as get_by_id since we store the result in the same table
        return self.get_by_id(task_id)
    
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
        try:
            with self.connection_manager.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        UPDATE pdf_analysis_tasks 
                        SET analysis_result = %s, updated_at = %s
                        WHERE task_id = %s
                    """, (
                        json.dumps(analysis_result),
                        datetime.utcnow(),
                        str(task_id)
                    ))
                    
                    updated = cursor.rowcount > 0
                    conn.commit()
                    
                    if updated:
                        self.logger.info(f"Saved analysis result for: {task_id}")
                    
                    return updated
                    
        except Exception as e:
            self.logger.error(f"Error saving analysis result for {task_id}: {e}")
            raise RepositoryError(f"Failed to save analysis result: {e}")
    
    def _row_to_entity(self, row: Dict[str, Any]) -> PDFAnalysis:
        """
        Convert database row to PDFAnalysis entity.
        
        Args:
            row: Database row as dictionary
            
        Returns:
            PDFAnalysis entity
        """
        from domain.value_objects import TaskId, UserId, FileName, FilePath, TaskStatus, ConfidenceScore, AnalysisResult
        
        # Parse JSON fields
        requirements = json.loads(row['requirements']) if row['requirements'] else {}
        systems_found = json.loads(row['systems_found']) if row['systems_found'] else None
        analysis_result = AnalysisResult.from_dict(json.loads(row['analysis_result'])) if row['analysis_result'] else None
        
        return PDFAnalysis(
            task_id=TaskId(row['task_id']),
            user_id=UserId(row['user_id']),
            filename=FileName(row['filename']),
            file_path=FilePath(row['file_path']),
            status=TaskStatus(row['status']),
            include_cost_estimation=row['include_cost_estimation'],
            include_timeline=row['include_timeline'],
            include_quantities=row['include_quantities'],
            requirements=requirements,
            confidence=ConfidenceScore(row['confidence']) if row['confidence'] else None,
            systems_found=systems_found,
            total_components=row['total_components'],
            processing_time=float(row['processing_time']) if row['processing_time'] else None,
            error_message=row['error_message'],
            analysis_result=analysis_result,
            created_at=row['created_at'],
            updated_at=row['updated_at']
        ) 