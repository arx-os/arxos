"""
User Repository Implementation

This module contains the SQLAlchemy implementation of the UserRepository
interface defined in the domain layer.
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from domain.entities import User
from domain.value_objects import UserId, UserRole
from domain.repositories import UserRepository
from domain.exceptions import RepositoryError

from .base import BaseRepository
from infrastructure.database.models.user import UserModel


class SQLAlchemyUserRepository(BaseRepository[User, UserModel], UserRepository):
    """SQLAlchemy implementation of UserRepository."""

    def __init__(self, session: Session):
        """Initialize user repository."""
        super().__init__(session, User, UserModel)

    def save(self, user: User) -> None:
        """Save a user to the repository."""
        try:
            model = self._entity_to_model(user)
            self.session.add(model)
            self.session.flush()
        except Exception as e:
            raise RepositoryError(f"Failed to save user: {str(e)}")

    def get_by_id(self, user_id: UserId) -> Optional[User]:
        """Get a user by their ID."""
        try:
            model = self.session.query(UserModel).filter(
                and_(
                    UserModel.id == user_id.value,
                    UserModel.deleted_at.is_(None)
                )
            ).first()

            if model is None:
                return None

            return self._model_to_entity(model)
        except Exception as e:
            raise RepositoryError(f"Failed to get user by ID: {str(e)}")

    def get_by_email(self, email: str) -> Optional[User]:
        """Get a user by email address."""
        try:
            model = self.session.query(UserModel).filter(
                and_(
                    UserModel.email == email,
                    UserModel.deleted_at.is_(None)
                )
            ).first()

            if model is None:
                return None

            return self._model_to_entity(model)
        except Exception as e:
            raise RepositoryError(f"Failed to get user by email: {str(e)}")

    def get_all(self) -> List[User]:
        """Get all users."""
        try:
            models = self.session.query(UserModel).filter(
                UserModel.deleted_at.is_(None)
            ).order_by(UserModel.username).all()

            return [self._model_to_entity(model) for model in models]
        except Exception as e:
            raise RepositoryError(f"Failed to get all users: {str(e)}")

    def get_by_role(self, role: UserRole) -> List[User]:
        """Get users by role."""
        try:
            models = self.session.query(UserModel).filter(
                and_(
                    UserModel.role == role,
                    UserModel.deleted_at.is_(None)
                )
            ).order_by(UserModel.username).all()

            return [self._model_to_entity(model) for model in models]
        except Exception as e:
            raise RepositoryError(f"Failed to find users by role: {str(e)}")

    def get_active_users(self) -> List[User]:
        """Get all active users."""
        try:
            models = self.session.query(UserModel).filter(
                and_(
                    UserModel.is_active == True,
                    UserModel.deleted_at.is_(None)
                )
            ).order_by(UserModel.username).all()

            return [self._model_to_entity(model) for model in models]
        except Exception as e:
            raise RepositoryError(f"Failed to find active users: {str(e)}")

    def delete(self, user_id: UserId) -> None:
        """Delete a user by ID."""
        try:
            model = self.session.query(UserModel).filter(
                and_(
                    UserModel.id == user_id.value,
                    UserModel.deleted_at.is_(None)
                )
            ).first()

            if model is None:
                raise RepositoryError(f"User with ID {user_id} not found")

            model.soft_delete()
            self.session.flush()
        except Exception as e:
            raise RepositoryError(f"Failed to delete user: {str(e)}")

    def exists(self, user_id: UserId) -> bool:
        """Check if a user exists."""
        try:
            return self.session.query(UserModel).filter(
                and_(
                    UserModel.id == user_id.value,
                    UserModel.deleted_at.is_(None)
                )
            ).first() is not None
        except Exception as e:
            raise RepositoryError(f"Failed to check user existence: {str(e)}")

    def exists_by_email(self, email: str) -> bool:
        """Check if a user exists by email."""
        try:
            return self.session.query(UserModel).filter(
                and_(
                    UserModel.email == email,
                    UserModel.deleted_at.is_(None)
                )
            ).first() is not None
        except Exception as e:
            raise RepositoryError(f"Failed to check user existence by email: {str(e)}")

    def count(self) -> int:
        """Get the total number of users."""
        try:
            return self.session.query(UserModel).filter(
                UserModel.deleted_at.is_(None)
            ).count()
        except Exception as e:
            raise RepositoryError(f"Failed to count users: {str(e)}")

    def find_by_email(self, email: str) -> Optional[User]:
        """Find a user by email."""
        try:
            model = self.session.query(UserModel).filter(
                and_(
                    UserModel.email == email,
                    UserModel.deleted_at.is_(None)
                )
            ).first()

            if model is None:
                return None

            return self._model_to_entity(model)
        except Exception as e:
            raise RepositoryError(f"Failed to find user by email: {str(e)}")

    def find_by_username(self, username: str) -> Optional[User]:
        """Find a user by username."""
        try:
            model = self.session.query(UserModel).filter(
                and_(
                    UserModel.username == username,
                    UserModel.deleted_at.is_(None)
                )
            ).first()

            if model is None:
                return None

            return self._model_to_entity(model)
        except Exception as e:
            raise RepositoryError(f"Failed to find user by username: {str(e)}")

    def find_by_role(self, role: UserRole) -> List[User]:
        """Find users by role."""
        try:
            models = self.session.query(UserModel).filter(
                and_(
                    UserModel.role == role,
                    UserModel.deleted_at.is_(None)
                )
            ).order_by(UserModel.username).all()

            return [self._model_to_entity(model) for model in models]
        except Exception as e:
            raise RepositoryError(f"Failed to find users by role: {str(e)}")

    def find_active_users(self) -> List[User]:
        """Find all active users."""
        try:
            models = self.session.query(UserModel).filter(
                and_(
                    UserModel.is_active == True,
                    UserModel.deleted_at.is_(None)
                )
            ).order_by(UserModel.username).all()

            return [self._model_to_entity(model) for model in models]
        except Exception as e:
            raise RepositoryError(f"Failed to find active users: {str(e)}")

    def search_users(self, search_term: str) -> List[User]:
        """Search users by name, email, or username."""
        try:
            search_pattern = f"%{search_term}%"
            models = self.session.query(UserModel).filter(
                and_(
                    or_(
                        UserModel.first_name.ilike(search_pattern),
                        UserModel.last_name.ilike(search_pattern),
                        UserModel.email.ilike(search_pattern),
                        UserModel.username.ilike(search_pattern)
                    ),
                    UserModel.deleted_at.is_(None)
                )
            ).order_by(UserModel.username).all()

            return [self._model_to_entity(model) for model in models]
        except Exception as e:
            raise RepositoryError(f"Failed to search users: {str(e)}")

    def _entity_to_model(self, entity: User) -> UserModel:
        """Convert User entity to UserModel."""
        model = UserModel(
            id=entity.id.value,
            email=entity.email.value,
            username=entity.username,
            role=entity.role,
            first_name=entity.first_name,
            last_name=entity.last_name,
            phone_number=entity.phone_number.value if entity.phone_number else None,
            is_active=entity.is_active,
            created_by=entity.created_by,
            updated_by=entity.updated_by
        )

        # Copy metadata if available
        if hasattr(entity, 'metadata') and entity.metadata:
            model.metadata_json = entity.metadata

        return model

    def _model_to_entity(self, model: UserModel) -> User:
        """Convert UserModel to User entity."""
        from domain.value_objects import Email, PhoneNumber

        # Create email
        email = Email(model.email)

        # Create phone number if available
        phone_number = None
        if model.phone_number:
            phone_number = PhoneNumber(model.phone_number)

        user = User(
            id=UserId(model.id),
            email=email,
            username=model.username,
            role=model.role,
            first_name=model.first_name,
            last_name=model.last_name,
            phone_number=phone_number,
            is_active=model.is_active,
            created_by=model.created_by,
            updated_by=model.updated_by
        )

        # Copy metadata if available
        if model.metadata_json:
            user.metadata = model.metadata_json

        return user
