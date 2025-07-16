"""
Database service for SVGX Engine.

This module provides a comprehensive database service using SQLAlchemy,
supporting both SQLite (development) and PostgreSQL (production) with
proper connection pooling, error handling, and transaction management.
Enhanced for SVGX-specific data models and workflows.
"""

import uuid
import logging
from typing import Optional, Dict, Any, List, Union
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, IntegrityError, OperationalError
from sqlalchemy import and_, or_, desc, asc

# Import SVGX-specific models
from ..models.database import (
    DatabaseManager, DatabaseConfig, get_db_manager,
    SVGXModel, SVGXElement, SVGXObject, SVGXBehavior, SVGXPhysics,
    SymbolLibrary, ValidationJob, ExportJob, User
)
from ..models.svgx import SVGXDocument, SVGXObject as SVGXDataObject
try:
    try:
    from ..utils.errors import PersistenceError, ValidationError, DatabaseError
except ImportError:
    # Fallback for direct execution
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from utils.errors import PersistenceError, ValidationError, DatabaseError
except ImportError:
    # Fallback for direct execution
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from utils.errors import PersistenceError, ValidationError, DatabaseError

logger = logging.getLogger(__name__)


class SVGXDatabaseService:
    """Comprehensive database service with SQLAlchemy for SVGX Engine."""
    
    def __init__(self, db_manager: Optional[DatabaseManager] = None):
        self.db_manager = db_manager or get_db_manager()
    
    def get_session(self) -> Session:
        """Get a database session with proper error handling."""
        try:
            return self.db_manager.get_session()
        except Exception as e:
            logger.error(f"Failed to get database session: {e}")
            raise DatabaseError(f"Database connection failed: {e}") from e
    
    def save_svgx_document(self, svgx_document: SVGXDocument, document_id: Optional[str] = None, 
                           metadata: Optional[Dict[str, Any]] = None) -> str:
        """Save SVGX document to database with proper error handling."""
        if not document_id:
            document_id = str(uuid.uuid4())
        
        session = self.get_session()
        try:
            # Check if document already exists
            existing_document = session.query(SVGXModel).filter(SVGXModel.id == document_id).first()
            
            # Serialize SVGX document
            document_data = self._serialize_svgx_document(svgx_document)
            
            if existing_document:
                # Update existing document
                existing_document.document_data = document_data
                existing_document.updated_at = datetime.utcnow()
                if metadata:
                    existing_document.document_metadata = metadata
                logger.info(f"Updated SVGX document {document_id}")
            else:
                # Create new document
                db_document = SVGXModel(
                    id=document_id,
                    name=metadata.get('name', f'SVGX Document {document_id}') if metadata else f'SVGX Document {document_id}',
                    description=metadata.get('description', '') if metadata else '',
                    document_data=document_data,
                    document_metadata=metadata,
                    created_by=metadata.get('created_by') if metadata else None,
                    project_id=metadata.get('project_id') if metadata else None,
                    version=metadata.get('version', '1.0') if metadata else '1.0',
                    document_type='svgx'
                )
                session.add(db_document)
                logger.info(f"Created SVGX document {document_id}")
            
            session.commit()
            return document_id
            
        except IntegrityError as e:
            session.rollback()
            logger.error(f"Database integrity error saving SVGX document: {e}")
            raise PersistenceError(f"Document with ID {document_id} already exists") from e
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Database error saving SVGX document: {e}")
            raise DatabaseError(f"Failed to save SVGX document: {e}") from e
        except Exception as e:
            session.rollback()
            logger.error(f"Unexpected error saving SVGX document: {e}")
            raise PersistenceError(f"Failed to save SVGX document: {e}") from e
        finally:
            session.close()
    
    def load_svgx_document(self, document_id: str) -> SVGXDocument:
        """Load SVGX document from database with proper error handling."""
        session = self.get_session()
        try:
            db_document = session.query(SVGXModel).filter(SVGXModel.id == document_id).first()
            
            if not db_document:
                raise PersistenceError(f"SVGX document {document_id} not found")
            
            # Deserialize SVGX document
            svgx_document = self._deserialize_svgx_document(db_document.document_data)
            logger.info(f"Loaded SVGX document {document_id}")
            return svgx_document
            
        except SQLAlchemyError as e:
            logger.error(f"Database error loading SVGX document: {e}")
            raise DatabaseError(f"Failed to load SVGX document: {e}") from e
        except Exception as e:
            logger.error(f"Unexpected error loading SVGX document: {e}")
            raise PersistenceError(f"Failed to load SVGX document: {e}") from e
        finally:
            session.close()
    
    def list_svgx_documents(self, project_id: Optional[str] = None, 
                           created_by: Optional[str] = None, 
                           active_only: bool = True) -> List[Dict[str, Any]]:
        """List SVGX documents with filtering options."""
        session = self.get_session()
        try:
            query = session.query(SVGXModel).filter(SVGXModel.document_type == 'svgx')
            
            if active_only:
                query = query.filter(SVGXModel.is_active == True)
            
            if project_id:
                query = query.filter(SVGXModel.project_id == project_id)
            
            if created_by:
                query = query.filter(SVGXModel.created_by == created_by)
            
            # Order by updated_at descending
            query = query.order_by(desc(SVGXModel.updated_at))
            
            documents = query.all()
            
            result = []
            for document in documents:
                result.append({
                    'id': document.id,
                    'name': document.name,
                    'description': document.description,
                    'created_at': document.created_at.isoformat() if document.created_at else None,
                    'updated_at': document.updated_at.isoformat() if document.updated_at else None,
                    'created_by': document.created_by,
                    'project_id': document.project_id,
                    'version': document.version,
                    'is_active': document.is_active,
                    'document_type': document.document_type
                })
            
            logger.info(f"Listed {len(result)} SVGX documents")
            return result
            
        except SQLAlchemyError as e:
            logger.error(f"Database error listing SVGX documents: {e}")
            raise DatabaseError(f"Failed to list SVGX documents: {e}") from e
        except Exception as e:
            logger.error(f"Unexpected error listing SVGX documents: {e}")
            raise PersistenceError(f"Failed to list SVGX documents: {e}") from e
        finally:
            session.close()
    
    def delete_svgx_document(self, document_id: str) -> bool:
        """Delete SVGX document from database."""
        session = self.get_session()
        try:
            db_document = session.query(SVGXModel).filter(SVGXModel.id == document_id).first()
            
            if not db_document:
                raise PersistenceError(f"SVGX document {document_id} not found")
            
            session.delete(db_document)
            session.commit()
            
            logger.info(f"Deleted SVGX document {document_id}")
            return True
            
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Database error deleting SVGX document: {e}")
            raise DatabaseError(f"Failed to delete SVGX document: {e}") from e
        except Exception as e:
            session.rollback()
            logger.error(f"Unexpected error deleting SVGX document: {e}")
            raise PersistenceError(f"Failed to delete SVGX document: {e}") from e
        finally:
            session.close()
    
    def save_svgx_object(self, svgx_object: SVGXDataObject, object_id: Optional[str] = None) -> str:
        """Save SVGX object to database."""
        if not object_id:
            object_id = svgx_object.object_id or str(uuid.uuid4())
        
        session = self.get_session()
        try:
            # Check if object already exists
            existing_object = session.query(SVGXObject).filter(SVGXObject.id == object_id).first()
            
            # Serialize SVGX object
            object_data = self._serialize_svgx_object(svgx_object)
            
            if existing_object:
                # Update existing object
                existing_object.object_data = object_data
                existing_object.updated_at = datetime.utcnow()
                logger.info(f"Updated SVGX object {object_id}")
            else:
                # Create new object
                db_object = SVGXObject(
                    id=object_id,
                    object_type=svgx_object.object_type,
                    system=svgx_object.system,
                    object_data=object_data,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                session.add(db_object)
                logger.info(f"Created SVGX object {object_id}")
            
            session.commit()
            return object_id
            
        except IntegrityError as e:
            session.rollback()
            logger.error(f"Database integrity error saving SVGX object: {e}")
            raise PersistenceError(f"Object with ID {object_id} already exists") from e
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Database error saving SVGX object: {e}")
            raise DatabaseError(f"Failed to save SVGX object: {e}") from e
        except Exception as e:
            session.rollback()
            logger.error(f"Unexpected error saving SVGX object: {e}")
            raise PersistenceError(f"Failed to save SVGX object: {e}") from e
        finally:
            session.close()
    
    def load_svgx_object(self, object_id: str) -> SVGXDataObject:
        """Load SVGX object from database."""
        session = self.get_session()
        try:
            db_object = session.query(SVGXObject).filter(SVGXObject.id == object_id).first()
            
            if not db_object:
                raise PersistenceError(f"SVGX object {object_id} not found")
            
            # Deserialize SVGX object
            svgx_object = self._deserialize_svgx_object(db_object.object_data)
            logger.info(f"Loaded SVGX object {object_id}")
            return svgx_object
            
        except SQLAlchemyError as e:
            logger.error(f"Database error loading SVGX object: {e}")
            raise DatabaseError(f"Failed to load SVGX object: {e}") from e
        except Exception as e:
            logger.error(f"Unexpected error loading SVGX object: {e}")
            raise PersistenceError(f"Failed to load SVGX object: {e}") from e
        finally:
            session.close()
    
    def list_svgx_objects(self, system: Optional[str] = None, 
                         object_type: Optional[str] = None,
                         active_only: bool = True) -> List[Dict[str, Any]]:
        """List SVGX objects with filtering options."""
        session = self.get_session()
        try:
            query = session.query(SVGXObject)
            
            if active_only:
                query = query.filter(SVGXObject.is_active == True)
            
            if system:
                query = query.filter(SVGXObject.system == system)
            
            if object_type:
                query = query.filter(SVGXObject.object_type == object_type)
            
            # Order by updated_at descending
            query = query.order_by(desc(SVGXObject.updated_at))
            
            objects = query.all()
            
            result = []
            for obj in objects:
                result.append({
                    'id': obj.id,
                    'object_type': obj.object_type,
                    'system': obj.system,
                    'created_at': obj.created_at.isoformat() if obj.created_at else None,
                    'updated_at': obj.updated_at.isoformat() if obj.updated_at else None,
                    'is_active': obj.is_active
                })
            
            logger.info(f"Listed {len(result)} SVGX objects")
            return result
            
        except SQLAlchemyError as e:
            logger.error(f"Database error listing SVGX objects: {e}")
            raise DatabaseError(f"Failed to list SVGX objects: {e}") from e
        except Exception as e:
            logger.error(f"Unexpected error listing SVGX objects: {e}")
            raise PersistenceError(f"Failed to list SVGX objects: {e}") from e
        finally:
            session.close()
    
    def delete_svgx_object(self, object_id: str) -> bool:
        """Delete SVGX object from database."""
        session = self.get_session()
        try:
            db_object = session.query(SVGXObject).filter(SVGXObject.id == object_id).first()
            
            if not db_object:
                raise PersistenceError(f"SVGX object {object_id} not found")
            
            session.delete(db_object)
            session.commit()
            
            logger.info(f"Deleted SVGX object {object_id}")
            return True
            
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Database error deleting SVGX object: {e}")
            raise DatabaseError(f"Failed to delete SVGX object: {e}") from e
        except Exception as e:
            session.rollback()
            logger.error(f"Unexpected error deleting SVGX object: {e}")
            raise PersistenceError(f"Failed to delete SVGX object: {e}") from e
        finally:
            session.close()
    
    def save_symbol(self, symbol_data: Dict[str, Any], symbol_id: Optional[str] = None) -> str:
        """Save symbol to database."""
        if not symbol_id:
            symbol_id = symbol_data.get('id') or str(uuid.uuid4())
        
        session = self.get_session()
        try:
            # Check if symbol already exists
            existing_symbol = session.query(SymbolLibrary).filter(SymbolLibrary.id == symbol_id).first()
            
            if existing_symbol:
                # Update existing symbol
                existing_symbol.symbol_data = symbol_data
                existing_symbol.updated_at = datetime.utcnow()
                logger.info(f"Updated symbol {symbol_id}")
            else:
                # Create new symbol
                db_symbol = SymbolLibrary(
                    id=symbol_id,
                    name=symbol_data.get('name', ''),
                    system=symbol_data.get('system', ''),
                    category=symbol_data.get('category', ''),
                    symbol_data=symbol_data,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                session.add(db_symbol)
                logger.info(f"Created symbol {symbol_id}")
            
            session.commit()
            return symbol_id
            
        except IntegrityError as e:
            session.rollback()
            logger.error(f"Database integrity error saving symbol: {e}")
            raise PersistenceError(f"Symbol with ID {symbol_id} already exists") from e
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Database error saving symbol: {e}")
            raise DatabaseError(f"Failed to save symbol: {e}") from e
        except Exception as e:
            session.rollback()
            logger.error(f"Unexpected error saving symbol: {e}")
            raise PersistenceError(f"Failed to save symbol: {e}") from e
        finally:
            session.close()
    
    def load_symbol(self, symbol_id: str) -> Dict[str, Any]:
        """Load symbol from database."""
        session = self.get_session()
        try:
            db_symbol = session.query(SymbolLibrary).filter(SymbolLibrary.id == symbol_id).first()
            
            if not db_symbol:
                raise PersistenceError(f"Symbol {symbol_id} not found")
            
            logger.info(f"Loaded symbol {symbol_id}")
            return db_symbol.symbol_data
            
        except SQLAlchemyError as e:
            logger.error(f"Database error loading symbol: {e}")
            raise DatabaseError(f"Failed to load symbol: {e}") from e
        except Exception as e:
            logger.error(f"Unexpected error loading symbol: {e}")
            raise PersistenceError(f"Failed to load symbol: {e}") from e
        finally:
            session.close()
    
    def list_symbols(self, system: Optional[str] = None, category: Optional[str] = None,
                    active_only: bool = True) -> List[Dict[str, Any]]:
        """List symbols with filtering options."""
        session = self.get_session()
        try:
            query = session.query(SymbolLibrary)
            
            if active_only:
                query = query.filter(SymbolLibrary.is_active == True)
            
            if system:
                query = query.filter(SymbolLibrary.system == system)
            
            if category:
                query = query.filter(SymbolLibrary.category == category)
            
            # Order by name
            query = query.order_by(asc(SymbolLibrary.name))
            
            symbols = query.all()
            
            result = []
            for symbol in symbols:
                result.append({
                    'id': symbol.id,
                    'name': symbol.name,
                    'system': symbol.system,
                    'category': symbol.category,
                    'created_at': symbol.created_at.isoformat() if symbol.created_at else None,
                    'updated_at': symbol.updated_at.isoformat() if symbol.updated_at else None,
                    'is_active': symbol.is_active
                })
            
            logger.info(f"Listed {len(result)} symbols")
            return result
            
        except SQLAlchemyError as e:
            logger.error(f"Database error listing symbols: {e}")
            raise DatabaseError(f"Failed to list symbols: {e}") from e
        except Exception as e:
            logger.error(f"Unexpected error listing symbols: {e}")
            raise PersistenceError(f"Failed to list symbols: {e}") from e
        finally:
            session.close()
    
    def delete_symbol(self, symbol_id: str) -> bool:
        """Delete symbol from database."""
        session = self.get_session()
        try:
            db_symbol = session.query(SymbolLibrary).filter(SymbolLibrary.id == symbol_id).first()
            
            if not db_symbol:
                raise PersistenceError(f"Symbol {symbol_id} not found")
            
            session.delete(db_symbol)
            session.commit()
            
            logger.info(f"Deleted symbol {symbol_id}")
            return True
            
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Database error deleting symbol: {e}")
            raise DatabaseError(f"Failed to delete symbol: {e}") from e
        except Exception as e:
            session.rollback()
            logger.error(f"Unexpected error deleting symbol: {e}")
            raise PersistenceError(f"Failed to delete symbol: {e}") from e
        finally:
            session.close()
    
    def create_validation_job(self, job_type: str, total_items: int = 0) -> str:
        """Create a validation job."""
        job_id = str(uuid.uuid4())
        
        session = self.get_session()
        try:
            db_job = ValidationJob(
                id=job_id,
                job_type=job_type,
                status='pending',
                total_items=total_items,
                processed_items=0,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            session.add(db_job)
            session.commit()
            
            logger.info(f"Created validation job {job_id}")
            return job_id
            
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Database error creating validation job: {e}")
            raise DatabaseError(f"Failed to create validation job: {e}") from e
        except Exception as e:
            session.rollback()
            logger.error(f"Unexpected error creating validation job: {e}")
            raise PersistenceError(f"Failed to create validation job: {e}") from e
        finally:
            session.close()
    
    def update_validation_job(self, job_id: str, status: str, progress: int = None,
                            processed_items: int = None, errors: List[str] = None,
                            warnings: List[str] = None, result_data: Dict[str, Any] = None):
        """Update a validation job."""
        session = self.get_session()
        try:
            db_job = session.query(ValidationJob).filter(ValidationJob.id == job_id).first()
            
            if not db_job:
                raise PersistenceError(f"Validation job {job_id} not found")
            
            db_job.status = status
            db_job.updated_at = datetime.utcnow()
            
            if progress is not None:
                db_job.progress = progress
            
            if processed_items is not None:
                db_job.processed_items = processed_items
            
            if errors is not None:
                db_job.errors = errors
            
            if warnings is not None:
                db_job.warnings = warnings
            
            if result_data is not None:
                db_job.result_data = result_data
            
            session.commit()
            
            logger.info(f"Updated validation job {job_id} - status: {status}")
            
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Database error updating validation job: {e}")
            raise DatabaseError(f"Failed to update validation job: {e}") from e
        except Exception as e:
            session.rollback()
            logger.error(f"Unexpected error updating validation job: {e}")
            raise PersistenceError(f"Failed to update validation job: {e}") from e
        finally:
            session.close()
    
    def get_validation_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get a validation job."""
        session = self.get_session()
        try:
            db_job = session.query(ValidationJob).filter(ValidationJob.id == job_id).first()
            
            if not db_job:
                return None
            
            return {
                'id': db_job.id,
                'job_type': db_job.job_type,
                'status': db_job.status,
                'progress': db_job.progress,
                'total_items': db_job.total_items,
                'processed_items': db_job.processed_items,
                'errors': db_job.errors,
                'warnings': db_job.warnings,
                'result_data': db_job.result_data,
                'created_at': db_job.created_at.isoformat() if db_job.created_at else None,
                'updated_at': db_job.updated_at.isoformat() if db_job.updated_at else None
            }
            
        except SQLAlchemyError as e:
            logger.error(f"Database error getting validation job: {e}")
            raise DatabaseError(f"Failed to get validation job: {e}") from e
        except Exception as e:
            logger.error(f"Unexpected error getting validation job: {e}")
            raise PersistenceError(f"Failed to get validation job: {e}") from e
        finally:
            session.close()
    
    def create_export_job(self, job_type: str, export_format: str, total_items: int = 0) -> str:
        """Create an export job."""
        job_id = str(uuid.uuid4())
        
        session = self.get_session()
        try:
            db_job = ExportJob(
                id=job_id,
                job_type=job_type,
                export_format=export_format,
                status='pending',
                total_items=total_items,
                processed_items=0,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            session.add(db_job)
            session.commit()
            
            logger.info(f"Created export job {job_id}")
            return job_id
            
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Database error creating export job: {e}")
            raise DatabaseError(f"Failed to create export job: {e}") from e
        except Exception as e:
            session.rollback()
            logger.error(f"Unexpected error creating export job: {e}")
            raise PersistenceError(f"Failed to create export job: {e}") from e
        finally:
            session.close()
    
    def update_export_job(self, job_id: str, status: str, progress: int = None,
                         processed_items: int = None, file_path: str = None,
                         file_size: int = None, errors: List[str] = None):
        """Update an export job."""
        session = self.get_session()
        try:
            db_job = session.query(ExportJob).filter(ExportJob.id == job_id).first()
            
            if not db_job:
                raise PersistenceError(f"Export job {job_id} not found")
            
            db_job.status = status
            db_job.updated_at = datetime.utcnow()
            
            if progress is not None:
                db_job.progress = progress
            
            if processed_items is not None:
                db_job.processed_items = processed_items
            
            if file_path is not None:
                db_job.file_path = file_path
            
            if file_size is not None:
                db_job.file_size = file_size
            
            if errors is not None:
                db_job.errors = errors
            
            session.commit()
            
            logger.info(f"Updated export job {job_id} - status: {status}")
            
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Database error updating export job: {e}")
            raise DatabaseError(f"Failed to update export job: {e}") from e
        except Exception as e:
            session.rollback()
            logger.error(f"Unexpected error updating export job: {e}")
            raise PersistenceError(f"Failed to update export job: {e}") from e
        finally:
            session.close()
    
    def get_export_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get an export job."""
        session = self.get_session()
        try:
            db_job = session.query(ExportJob).filter(ExportJob.id == job_id).first()
            
            if not db_job:
                return None
            
            return {
                'id': db_job.id,
                'job_type': db_job.job_type,
                'export_format': db_job.export_format,
                'status': db_job.status,
                'progress': db_job.progress,
                'total_items': db_job.total_items,
                'processed_items': db_job.processed_items,
                'file_path': db_job.file_path,
                'file_size': db_job.file_size,
                'errors': db_job.errors,
                'created_at': db_job.created_at.isoformat() if db_job.created_at else None,
                'updated_at': db_job.updated_at.isoformat() if db_job.updated_at else None
            }
            
        except SQLAlchemyError as e:
            logger.error(f"Database error getting export job: {e}")
            raise DatabaseError(f"Failed to get export job: {e}") from e
        except Exception as e:
            logger.error(f"Unexpected error getting export job: {e}")
            raise PersistenceError(f"Failed to get export job: {e}") from e
        finally:
            session.close()
    
    def create_user(self, user_data: dict) -> User:
        """Create a new user."""
        session = self.get_session()
        try:
            db_user = User(**user_data)
            session.add(db_user)
            session.commit()
            
            logger.info(f"Created user {db_user.id}")
            return db_user
            
        except IntegrityError as e:
            session.rollback()
            logger.error(f"Database integrity error creating user: {e}")
            raise PersistenceError(f"User already exists") from e
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Database error creating user: {e}")
            raise DatabaseError(f"Failed to create user: {e}") from e
        except Exception as e:
            session.rollback()
            logger.error(f"Unexpected error creating user: {e}")
            raise PersistenceError(f"Failed to create user: {e}") from e
        finally:
            session.close()
    
    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID."""
        session = self.get_session()
        try:
            return session.query(User).filter(User.id == user_id).first()
        except SQLAlchemyError as e:
            logger.error(f"Database error getting user by ID: {e}")
            raise DatabaseError(f"Failed to get user: {e}") from e
        finally:
            session.close()
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username."""
        session = self.get_session()
        try:
            return session.query(User).filter(User.username == username).first()
        except SQLAlchemyError as e:
            logger.error(f"Database error getting user by username: {e}")
            raise DatabaseError(f"Failed to get user: {e}") from e
        finally:
            session.close()
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        session = self.get_session()
        try:
            return session.query(User).filter(User.email == email).first()
        except SQLAlchemyError as e:
            logger.error(f"Database error getting user by email: {e}")
            raise DatabaseError(f"Failed to get user: {e}") from e
        finally:
            session.close()
    
    def update_user(self, user_id: str, user_data: dict) -> Optional[User]:
        """Update user."""
        session = self.get_session()
        try:
            db_user = session.query(User).filter(User.id == user_id).first()
            
            if not db_user:
                return None
            
            for key, value in user_data.items():
                if hasattr(db_user, key):
                    setattr(db_user, key, value)
            
            db_user.updated_at = datetime.utcnow()
            session.commit()
            
            logger.info(f"Updated user {user_id}")
            return db_user
            
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Database error updating user: {e}")
            raise DatabaseError(f"Failed to update user: {e}") from e
        except Exception as e:
            session.rollback()
            logger.error(f"Unexpected error updating user: {e}")
            raise PersistenceError(f"Failed to update user: {e}") from e
        finally:
            session.close()
    
    def delete_user(self, user_id: str) -> bool:
        """Delete user."""
        session = self.get_session()
        try:
            db_user = session.query(User).filter(User.id == user_id).first()
            
            if not db_user:
                return False
            
            session.delete(db_user)
            session.commit()
            
            logger.info(f"Deleted user {user_id}")
            return True
            
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Database error deleting user: {e}")
            raise DatabaseError(f"Failed to delete user: {e}") from e
        except Exception as e:
            session.rollback()
            logger.error(f"Unexpected error deleting user: {e}")
            raise PersistenceError(f"Failed to delete user: {e}") from e
        finally:
            session.close()
    
    def list_users(self) -> List[User]:
        """List all users."""
        session = self.get_session()
        try:
            return session.query(User).all()
        except SQLAlchemyError as e:
            logger.error(f"Database error listing users: {e}")
            raise DatabaseError(f"Failed to list users: {e}") from e
        finally:
            session.close()
    
    def close(self):
        """Close database connections."""
        if self.db_manager:
            self.db_manager.close()
    
    def _serialize_svgx_document(self, svgx_document: SVGXDocument) -> Dict[str, Any]:
        """Serialize SVGX document to dictionary."""
        return {
            'version': svgx_document.version,
            'elements': [self._serialize_svgx_element(elem) for elem in svgx_document.elements],
            'metadata': svgx_document.metadata,
            'created_at': svgx_document.created_at.isoformat() if svgx_document.created_at else None,
            'updated_at': svgx_document.updated_at.isoformat() if svgx_document.updated_at else None
        }
    
    def _deserialize_svgx_document(self, document_data: Dict[str, Any]) -> SVGXDocument:
        """Deserialize SVGX document from dictionary."""
        elements = [self._deserialize_svgx_element(elem_data) for elem_data in document_data.get('elements', [])]
        
        return SVGXDocument(
            version=document_data.get('version', '1.0'),
            elements=elements,
            metadata=document_data.get('metadata', {}),
            created_at=datetime.fromisoformat(document_data['created_at']) if document_data.get('created_at') else None,
            updated_at=datetime.fromisoformat(document_data['updated_at']) if document_data.get('updated_at') else None
        )
    
    def _serialize_svgx_element(self, element) -> Dict[str, Any]:
        """Serialize SVGX element to dictionary."""
        return {
            'tag': element.tag,
            'attributes': element.attributes,
            'content': element.content,
            'position': element.position,
            'children': [self._serialize_svgx_element(child) for child in element.children],
            'arx_object': self._serialize_arx_object(element.arx_object) if element.arx_object else None,
            'arx_behavior': self._serialize_arx_behavior(element.arx_behavior) if element.arx_behavior else None,
            'arx_physics': self._serialize_arx_physics(element.arx_physics) if element.arx_physics else None
        }
    
    def _deserialize_svgx_element(self, element_data: Dict[str, Any]):
        """Deserialize SVGX element from dictionary."""
        from ..parser.parser import SVGXElement, ArxObject, ArxBehavior, ArxPhysics
        
        element = SVGXElement(
            tag=element_data['tag'],
            attributes=element_data['attributes'],
            content=element_data['content'],
            position=element_data['position']
        )
        
        # Add children
        for child_data in element_data.get('children', []):
            child = self._deserialize_svgx_element(child_data)
            element.add_child(child)
        
        # Add arx objects
        if element_data.get('arx_object'):
            element.arx_object = self._deserialize_arx_object(element_data['arx_object'])
        
        if element_data.get('arx_behavior'):
            element.arx_behavior = self._deserialize_arx_behavior(element_data['arx_behavior'])
        
        if element_data.get('arx_physics'):
            element.arx_physics = self._deserialize_arx_physics(element_data['arx_physics'])
        
        return element
    
    def _serialize_arx_object(self, arx_object) -> Dict[str, Any]:
        """Serialize ArxObject to dictionary."""
        if not arx_object:
            return None
        
        return {
            'object_id': arx_object.object_id,
            'object_type': arx_object.object_type,
            'system': arx_object.system,
            'properties': arx_object.properties
        }
    
    def _deserialize_arx_object(self, object_data: Dict[str, Any]):
        """Deserialize ArxObject from dictionary."""
        from ..parser.parser import ArxObject
        
        if not object_data:
            return None
        
        arx_object = ArxObject(
            object_id=object_data['object_id'],
            object_type=object_data['object_type'],
            system=object_data.get('system')
        )
        
        for key, value in object_data.get('properties', {}).items():
            arx_object.add_property(key, value)
        
        return arx_object
    
    def _serialize_arx_behavior(self, arx_behavior) -> Dict[str, Any]:
        """Serialize ArxBehavior to dictionary."""
        if not arx_behavior:
            return None
        
        return {
            'variables': arx_behavior.variables,
            'calculations': arx_behavior.calculations,
            'triggers': arx_behavior.triggers
        }
    
    def _deserialize_arx_behavior(self, behavior_data: Dict[str, Any]):
        """Deserialize ArxBehavior from dictionary."""
        from ..parser.parser import ArxBehavior
        
        if not behavior_data:
            return None
        
        arx_behavior = ArxBehavior()
        
        for name, var_data in behavior_data.get('variables', {}).items():
            arx_behavior.add_variable(name, var_data['value'], var_data.get('unit'))
        
        for name, formula in behavior_data.get('calculations', {}).items():
            arx_behavior.add_calculation(name, formula)
        
        for trigger in behavior_data.get('triggers', []):
            arx_behavior.add_trigger(trigger['event'], trigger['action'])
        
        return arx_behavior
    
    def _serialize_arx_physics(self, arx_physics) -> Dict[str, Any]:
        """Serialize ArxPhysics to dictionary."""
        if not arx_physics:
            return None
        
        return {
            'mass': arx_physics.mass,
            'anchor': arx_physics.anchor,
            'forces': arx_physics.forces
        }
    
    def _deserialize_arx_physics(self, physics_data: Dict[str, Any]):
        """Deserialize ArxPhysics from dictionary."""
        from ..parser.parser import ArxPhysics
        
        if not physics_data:
            return None
        
        arx_physics = ArxPhysics()
        
        if physics_data.get('mass'):
            mass_data = physics_data['mass']
            arx_physics.set_mass(mass_data['value'], mass_data.get('unit', 'kg'))
        
        if physics_data.get('anchor'):
            arx_physics.set_anchor(physics_data['anchor'])
        
        for force in physics_data.get('forces', []):
            arx_physics.add_force(force['type'], force.get('direction'), force.get('value'))
        
        return arx_physics
    
    def _serialize_svgx_object(self, svgx_object: SVGXDataObject) -> Dict[str, Any]:
        """Serialize SVGX object to dictionary."""
        return {
            'object_id': svgx_object.object_id,
            'object_type': svgx_object.object_type,
            'system': svgx_object.system,
            'properties': svgx_object.properties,
            'geometry': svgx_object.geometry,
            'behavior': svgx_object.behavior,
            'physics': svgx_object.physics
        }
    
    def _deserialize_svgx_object(self, object_data: Dict[str, Any]) -> SVGXDataObject:
        """Deserialize SVGX object from dictionary."""
        return SVGXDataObject(
            object_id=object_data['object_id'],
            object_type=object_data['object_type'],
            system=object_data.get('system'),
            properties=object_data.get('properties', {}),
            geometry=object_data.get('geometry'),
            behavior=object_data.get('behavior'),
            physics=object_data.get('physics')
        ) 