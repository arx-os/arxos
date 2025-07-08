"""
Database service for Arxos SVG-BIM Integration System.

This module provides a comprehensive database service using SQLAlchemy,
supporting both SQLite (development) and PostgreSQL (production) with
proper connection pooling, error handling, and transaction management.
"""

import uuid
import logging
from typing import Optional, Dict, Any, List, Union
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, IntegrityError, OperationalError
from sqlalchemy import and_, or_, desc, asc

from models.database import (
    DatabaseManager, DatabaseConfig, get_db_manager,
    BIMModel, BIMModelElement, BIMModelSystem, BIMModelSpace, BIMModelRelationship,
    SymbolLibrary, ValidationJob, ExportJob, User
)
from models.bim import BIMModel as BIMDataModel
from services.persistence_export_interoperability import BIMSerializer
from utils.errors import PersistenceError, ValidationError, DatabaseError

logger = logging.getLogger(__name__)


class DatabaseService:
    """Comprehensive database service with SQLAlchemy."""
    
    def __init__(self, db_manager: Optional[DatabaseManager] = None):
        self.db_manager = db_manager or get_db_manager()
        self.serializer = BIMSerializer()
    
    def get_session(self) -> Session:
        """Get a database session with proper error handling."""
        try:
            return self.db_manager.get_session()
        except Exception as e:
            logger.error(f"Failed to get database session: {e}")
            raise DatabaseError(f"Database connection failed: {e}") from e
    
    def save_bim_model(self, bim_model: BIMDataModel, model_id: Optional[str] = None, 
                       metadata: Optional[Dict[str, Any]] = None) -> str:
        """Save BIM model to database with proper error handling."""
        if not model_id:
            model_id = str(uuid.uuid4())
        
        session = self.get_session()
        try:
            # Check if model already exists
            existing_model = session.query(BIMModel).filter(BIMModel.id == model_id).first()
            
            # Serialize BIM model
            model_data = self.serializer.to_dict(bim_model)
            
            if existing_model:
                # Update existing model
                existing_model.model_data = model_data
                existing_model.updated_at = datetime.utcnow()
                if metadata:
                    existing_model.model_metadata = metadata
                logger.info(f"Updated BIM model {model_id}")
            else:
                # Create new model
                db_model = BIMModel(
                    id=model_id,
                    name=metadata.get('name', f'BIM Model {model_id}') if metadata else f'BIM Model {model_id}',
                    description=metadata.get('description', '') if metadata else '',
                    model_data=model_data,
                    model_metadata=metadata,
                    created_by=metadata.get('created_by') if metadata else None,
                    project_id=metadata.get('project_id') if metadata else None,
                    version=metadata.get('version', '1.0') if metadata else '1.0'
                )
                session.add(db_model)
                logger.info(f"Created BIM model {model_id}")
            
            session.commit()
            return model_id
            
        except IntegrityError as e:
            session.rollback()
            logger.error(f"Database integrity error saving BIM model: {e}")
            raise PersistenceError(f"Model with ID {model_id} already exists") from e
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Database error saving BIM model: {e}")
            raise DatabaseError(f"Failed to save BIM model: {e}") from e
        except Exception as e:
            session.rollback()
            logger.error(f"Unexpected error saving BIM model: {e}")
            raise PersistenceError(f"Failed to save BIM model: {e}") from e
        finally:
            session.close()
    
    def load_bim_model(self, model_id: str) -> BIMDataModel:
        """Load BIM model from database with proper error handling."""
        session = self.get_session()
        try:
            db_model = session.query(BIMModel).filter(BIMModel.id == model_id).first()
            
            if not db_model:
                raise PersistenceError(f"BIM model {model_id} not found")
            
            # Deserialize BIM model
            bim_model = self.serializer.from_dict(db_model.model_data, BIMDataModel)
            logger.info(f"Loaded BIM model {model_id}")
            return bim_model
            
        except SQLAlchemyError as e:
            logger.error(f"Database error loading BIM model: {e}")
            raise DatabaseError(f"Failed to load BIM model: {e}") from e
        except Exception as e:
            logger.error(f"Unexpected error loading BIM model: {e}")
            raise PersistenceError(f"Failed to load BIM model: {e}") from e
        finally:
            session.close()
    
    def list_bim_models(self, project_id: Optional[str] = None, 
                       created_by: Optional[str] = None, 
                       active_only: bool = True) -> List[Dict[str, Any]]:
        """List BIM models with filtering options."""
        session = self.get_session()
        try:
            query = session.query(BIMModel)
            
            if active_only:
                query = query.filter(BIMModel.is_active == True)
            
            if project_id:
                query = query.filter(BIMModel.project_id == project_id)
            
            if created_by:
                query = query.filter(BIMModel.created_by == created_by)
            
            # Order by updated_at descending
            query = query.order_by(desc(BIMModel.updated_at))
            
            models = query.all()
            
            result = []
            for model in models:
                result.append({
                    'id': model.id,
                    'name': model.name,
                    'description': model.description,
                    'created_at': model.created_at.isoformat() if model.created_at else None,
                    'updated_at': model.updated_at.isoformat() if model.updated_at else None,
                    'created_by': model.created_by,
                    'project_id': model.project_id,
                    'version': model.version,
                    'is_active': model.is_active
                })
            
            logger.info(f"Listed {len(result)} BIM models")
            return result
            
        except SQLAlchemyError as e:
            logger.error(f"Database error listing BIM models: {e}")
            raise DatabaseError(f"Failed to list BIM models: {e}") from e
        except Exception as e:
            logger.error(f"Unexpected error listing BIM models: {e}")
            raise PersistenceError(f"Failed to list BIM models: {e}") from e
        finally:
            session.close()
    
    def delete_bim_model(self, model_id: str) -> bool:
        """Delete BIM model from database."""
        session = self.get_session()
        try:
            db_model = session.query(BIMModel).filter(BIMModel.id == model_id).first()
            
            if not db_model:
                raise PersistenceError(f"BIM model {model_id} not found")
            
            session.delete(db_model)
            session.commit()
            
            logger.info(f"Deleted BIM model {model_id}")
            return True
            
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Database error deleting BIM model: {e}")
            raise DatabaseError(f"Failed to delete BIM model: {e}") from e
        except Exception as e:
            session.rollback()
            logger.error(f"Unexpected error deleting BIM model: {e}")
            raise PersistenceError(f"Failed to delete BIM model: {e}") from e
        finally:
            session.close()
    
    def save_symbol(self, symbol_data: Dict[str, Any], symbol_id: Optional[str] = None) -> str:
        """Save symbol to database."""
        if not symbol_id:
            symbol_id = symbol_data.get('id') or str(uuid.uuid4())
        
        session = self.get_session()
        try:
            # Check if symbol already exists
            existing_symbol = session.query(SymbolLibrary).filter(SymbolLibrary.symbol_id == symbol_id).first()
            
            if existing_symbol:
                # Update existing symbol
                existing_symbol.name = symbol_data.get('name', existing_symbol.name)
                existing_symbol.system = symbol_data.get('system', existing_symbol.system)
                existing_symbol.category = symbol_data.get('category', existing_symbol.category)
                existing_symbol.symbol_data = symbol_data
                existing_symbol.svg_content = symbol_data.get('svg_content', existing_symbol.svg_content)
                existing_symbol.properties = symbol_data.get('properties', existing_symbol.properties)
                existing_symbol.connections = symbol_data.get('connections', existing_symbol.connections)
                existing_symbol.symbol_metadata = symbol_data.get('metadata', existing_symbol.symbol_metadata)
                existing_symbol.version = symbol_data.get('version', existing_symbol.version)
                existing_symbol.updated_at = datetime.utcnow()
                logger.info(f"Updated symbol {symbol_id}")
            else:
                # Create new symbol
                db_symbol = SymbolLibrary(
                    symbol_id=symbol_id,
                    name=symbol_data.get('name', ''),
                    system=symbol_data.get('system', ''),
                    category=symbol_data.get('category'),
                    symbol_data=symbol_data,
                    svg_content=symbol_data.get('svg_content'),
                    properties=symbol_data.get('properties'),
                    connections=symbol_data.get('connections'),
                    symbol_metadata=symbol_data.get('metadata'),
                    version=symbol_data.get('version', '1.0')
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
            db_symbol = session.query(SymbolLibrary).filter(SymbolLibrary.symbol_id == symbol_id).first()
            
            if not db_symbol:
                raise PersistenceError(f"Symbol {symbol_id} not found")
            
            symbol_data = db_symbol.symbol_data
            logger.info(f"Loaded symbol {symbol_id}")
            return symbol_data
            
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
                    'id': symbol.symbol_id,
                    'name': symbol.name,
                    'system': symbol.system,
                    'category': symbol.category,
                    'version': symbol.version,
                    'is_active': symbol.is_active,
                    'created_at': symbol.created_at.isoformat() if symbol.created_at else None,
                    'updated_at': symbol.updated_at.isoformat() if symbol.updated_at else None
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
            db_symbol = session.query(SymbolLibrary).filter(SymbolLibrary.symbol_id == symbol_id).first()
            
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
            job = ValidationJob(
                id=job_id,
                job_type=job_type,
                status="pending",
                total_items=total_items,
                processed_items=0,
                progress=0
            )
            session.add(job)
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
        """Update validation job status."""
        session = self.get_session()
        try:
            job = session.query(ValidationJob).filter(ValidationJob.id == job_id).first()
            
            if not job:
                raise PersistenceError(f"Validation job {job_id} not found")
            
            job.status = status
            job.updated_at = datetime.utcnow()
            
            if progress is not None:
                job.progress = progress
            
            if processed_items is not None:
                job.processed_items = processed_items
            
            if errors is not None:
                job.errors = errors
            
            if warnings is not None:
                job.warnings = warnings
            
            if result_data is not None:
                job.result_data = result_data
            
            if status in ["completed", "failed"]:
                job.completed_at = datetime.utcnow()
            
            session.commit()
            logger.info(f"Updated validation job {job_id}: {status}")
            
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
        """Get validation job details."""
        session = self.get_session()
        try:
            job = session.query(ValidationJob).filter(ValidationJob.id == job_id).first()
            
            if not job:
                return None
            
            return {
                'id': job.id,
                'job_type': job.job_type,
                'status': job.status,
                'progress': job.progress,
                'total_items': job.total_items,
                'processed_items': job.processed_items,
                'errors': job.errors,
                'warnings': job.warnings,
                'result_data': job.result_data,
                'created_at': job.created_at.isoformat() if job.created_at else None,
                'updated_at': job.updated_at.isoformat() if job.updated_at else None,
                'completed_at': job.completed_at.isoformat() if job.completed_at else None
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
            job = ExportJob(
                id=job_id,
                job_type=job_type,
                status="pending",
                export_format=export_format,
                total_items=total_items,
                processed_items=0,
                progress=0
            )
            session.add(job)
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
        """Update export job status."""
        session = self.get_session()
        try:
            job = session.query(ExportJob).filter(ExportJob.id == job_id).first()
            
            if not job:
                raise PersistenceError(f"Export job {job_id} not found")
            
            job.status = status
            job.updated_at = datetime.utcnow()
            
            if progress is not None:
                job.progress = progress
            
            if processed_items is not None:
                job.processed_items = processed_items
            
            if file_path is not None:
                job.file_path = file_path
            
            if file_size is not None:
                job.file_size = file_size
            
            if errors is not None:
                job.errors = errors
            
            if status in ["completed", "failed"]:
                job.completed_at = datetime.utcnow()
            
            session.commit()
            logger.info(f"Updated export job {job_id}: {status}")
            
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
        """Get export job details."""
        session = self.get_session()
        try:
            job = session.query(ExportJob).filter(ExportJob.id == job_id).first()
            
            if not job:
                return None
            
            return {
                'id': job.id,
                'job_type': job.job_type,
                'status': job.status,
                'progress': job.progress,
                'total_items': job.total_items,
                'processed_items': job.processed_items,
                'export_format': job.export_format,
                'file_path': job.file_path,
                'file_size': job.file_size,
                'errors': job.errors,
                'created_at': job.created_at.isoformat() if job.created_at else None,
                'updated_at': job.updated_at.isoformat() if job.updated_at else None,
                'completed_at': job.completed_at.isoformat() if job.completed_at else None
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
            user = User(**user_data)
            session.add(user)
            session.commit()
            session.refresh(user)
            return user
        finally:
            session.close()
    
    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID."""
        session = self.get_session()
        try:
            return session.query(User).filter(User.id == user_id).first()
        finally:
            session.close()
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username."""
        session = self.get_session()
        try:
            return session.query(User).filter(User.username == username).first()
        finally:
            session.close()
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        session = self.get_session()
        try:
            return session.query(User).filter(User.email == email).first()
        finally:
            session.close()
    
    def update_user(self, user_id: str, user_data: dict) -> Optional[User]:
        """Update user."""
        session = self.get_session()
        try:
            user = session.query(User).filter(User.id == user_id).first()
            if user:
                for key, value in user_data.items():
                    setattr(user, key, value)
                session.commit()
                session.refresh(user)
            return user
        finally:
            session.close()
    
    def delete_user(self, user_id: str) -> bool:
        """Delete user."""
        session = self.get_session()
        try:
            user = session.query(User).filter(User.id == user_id).first()
            if user:
                session.delete(user)
                session.commit()
                return True
            return False
        finally:
            session.close()
    
    def list_users(self) -> List[User]:
        """List all users."""
        session = self.get_session()
        try:
            return session.query(User).all()
        finally:
            session.close()
    
    def close(self):
        """Close database connections."""
        if self.db_manager:
            self.db_manager.close() 