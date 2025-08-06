"""
Version Control for Knowledge Base

This module provides version control functionality for building codes,
including version tracking, change history, and rollback capabilities.
"""

import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Set
from pathlib import Path
import asyncio
import hashlib

from pydantic import BaseModel, Field
from sqlalchemy import (
    create_engine,
    Column,
    String,
    Text,
    DateTime,
    Integer,
    Boolean,
    JSON,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)

Base = declarative_base()


class CodeVersion(Base):
    """Database model for code versions"""

    __tablename__ = "code_versions"

    id = Column(Integer, primary_key=True)
    code_standard = Column(String(50), nullable=False)
    version_number = Column(String(20), nullable=False)
    release_date = Column(DateTime, nullable=False)
    effective_date = Column(DateTime, nullable=False)
    is_active = Column(Boolean, default=True)
    change_summary = Column(Text, nullable=True)
    file_hash = Column(String(64), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class CodeChange(Base):
    """Database model for code changes"""

    __tablename__ = "code_changes"

    id = Column(Integer, primary_key=True)
    code_standard = Column(String(50), nullable=False)
    version_from = Column(String(20), nullable=False)
    version_to = Column(String(20), nullable=False)
    section_number = Column(String(20), nullable=False)
    change_type = Column(String(50), nullable=False)  # ADD, MODIFY, DELETE
    old_content = Column(Text, nullable=True)
    new_content = Column(Text, nullable=False)
    change_reason = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class CodeVersionInfo(BaseModel):
    """Pydantic model for code version information"""

    code_standard: str = Field(..., description="Building code standard")
    version_number: str = Field(..., description="Version number")
    release_date: datetime = Field(..., description="When version was released")
    effective_date: datetime = Field(..., description="When version becomes effective")
    is_active: bool = Field(True, description="Whether version is currently active")
    change_summary: Optional[str] = Field(None, description="Summary of changes")
    file_hash: Optional[str] = Field(None, description="Hash of version file")
    sections_count: int = Field(0, description="Number of sections in this version")


class CodeChange(BaseModel):
    """Pydantic model for code changes"""

    code_standard: str = Field(..., description="Building code standard")
    version_from: str = Field(..., description="Previous version")
    version_to: str = Field(..., description="New version")
    section_number: str = Field(..., description="Section number changed")
    change_type: str = Field(..., description="Type of change (ADD, MODIFY, DELETE)")
    old_content: Optional[str] = Field(None, description="Previous content")
    new_content: str = Field(..., description="New content")
    change_reason: Optional[str] = Field(None, description="Reason for change")


class VersionControl:
    """Manages version control for building codes"""

    def __init__(self, database_url: str = "sqlite:///version_control.db"):
        """Initialize the version control system"""
        self.database_url = database_url
        self.engine = create_engine(database_url)
        Base.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(
            autocommit=False, autoflush=False, bind=self.engine
        )

        # Initialize version data
        self._initialize_version_data()

    def _initialize_version_data(self):
        """Initialize with sample version data"""
        try:
            session = self.SessionLocal()

            # Check if data already exists
            if session.query(CodeVersion).count() == 0:
                logger.info("Initializing version control with sample version data...")
                self._load_sample_versions(session)
                session.commit()
                logger.info("✅ Version control initialized successfully")
            else:
                logger.info("✅ Version control already contains data")

        except Exception as e:
            logger.error(f"❌ Failed to initialize version control: {e}")
            raise
        finally:
            session.close()

    def _load_sample_versions(self, session):
        """Load sample code versions"""
        sample_versions = [
            {
                "code_standard": "IBC",
                "version_number": "2021",
                "release_date": datetime(2020, 12, 1),
                "effective_date": datetime(2021, 1, 1),
                "is_active": True,
                "change_summary": "Major updates to fire safety, accessibility, and structural requirements",
                "file_hash": "abc123def456",
            },
            {
                "code_standard": "IBC",
                "version_number": "2018",
                "release_date": datetime(2017, 12, 1),
                "effective_date": datetime(2018, 1, 1),
                "is_active": False,
                "change_summary": "Updates to energy efficiency and sustainability requirements",
                "file_hash": "def456ghi789",
            },
            {
                "code_standard": "NEC",
                "version_number": "2023",
                "release_date": datetime(2022, 12, 1),
                "effective_date": datetime(2023, 1, 1),
                "is_active": True,
                "change_summary": "Enhanced electrical safety requirements and new technology integration",
                "file_hash": "ghi789jkl012",
            },
            {
                "code_standard": "NEC",
                "version_number": "2020",
                "release_date": datetime(2019, 12, 1),
                "effective_date": datetime(2020, 1, 1),
                "is_active": False,
                "change_summary": "Updates to renewable energy and energy storage systems",
                "file_hash": "jkl012mno345",
            },
            {
                "code_standard": "ADA",
                "version_number": "2010",
                "release_date": datetime(2010, 3, 15),
                "effective_date": datetime(2010, 3, 15),
                "is_active": True,
                "change_summary": "Comprehensive accessibility standards for public accommodations",
                "file_hash": "mno345pqr678",
            },
        ]

        for version_data in sample_versions:
            version = CodeVersion(
                code_standard=version_data["code_standard"],
                version_number=version_data["version_number"],
                release_date=version_data["release_date"],
                effective_date=version_data["effective_date"],
                is_active=version_data["is_active"],
                change_summary=version_data["change_summary"],
                file_hash=version_data["file_hash"],
            )
            session.add(version)

    async def get_code_versions(
        self, code_standard: Optional[str] = None
    ) -> List[CodeVersionInfo]:
        """Get all versions for a code standard"""
        try:
            session = self.SessionLocal()

            query = session.query(CodeVersion)
            if code_standard:
                query = query.filter(CodeVersion.code_standard == code_standard)

            results = query.order_by(CodeVersion.release_date.desc()).all()

            versions = []
            for result in results:
                versions.append(
                    CodeVersionInfo(
                        code_standard=result.code_standard,
                        version_number=result.version_number,
                        release_date=result.release_date,
                        effective_date=result.effective_date,
                        is_active=result.is_active,
                        change_summary=result.change_summary,
                        file_hash=result.file_hash,
                        sections_count=0,  # Would be calculated from actual data
                    )
                )

            return versions

        except Exception as e:
            logger.error(f"❌ Error getting code versions: {e}")
            return []
        finally:
            session.close()

    async def get_active_version(self, code_standard: str) -> Optional[CodeVersionInfo]:
        """Get the currently active version for a code standard"""
        try:
            session = self.SessionLocal()

            result = (
                session.query(CodeVersion)
                .filter(
                    CodeVersion.code_standard == code_standard,
                    CodeVersion.is_active == True,
                )
                .first()
            )

            if result:
                return CodeVersionInfo(
                    code_standard=result.code_standard,
                    version_number=result.version_number,
                    release_date=result.release_date,
                    effective_date=result.effective_date,
                    is_active=result.is_active,
                    change_summary=result.change_summary,
                    file_hash=result.file_hash,
                    sections_count=0,
                )

            return None

        except Exception as e:
            logger.error(f"❌ Error getting active version: {e}")
            return None
        finally:
            session.close()

    async def add_code_version(self, version_info: CodeVersionInfo) -> bool:
        """Add a new code version"""
        try:
            session = self.SessionLocal()

            # Check if version already exists
            existing = (
                session.query(CodeVersion)
                .filter(
                    CodeVersion.code_standard == version_info.code_standard,
                    CodeVersion.version_number == version_info.version_number,
                )
                .first()
            )

            if existing:
                logger.warning(
                    f"Version {version_info.code_standard} {version_info.version_number} already exists"
                )
                return False

            # Add new version
            version = CodeVersion(
                code_standard=version_info.code_standard,
                version_number=version_info.version_number,
                release_date=version_info.release_date,
                effective_date=version_info.effective_date,
                is_active=version_info.is_active,
                change_summary=version_info.change_summary,
                file_hash=version_info.file_hash,
            )

            session.add(version)
            session.commit()

            logger.info(
                f"✅ Added version {version_info.code_standard} {version_info.version_number}"
            )
            return True

        except Exception as e:
            logger.error(f"❌ Error adding code version: {e}")
            session.rollback()
            return False
        finally:
            session.close()

    async def update_code_version(
        self, code_standard: str, version_number: str, updates: Dict[str, Any]
    ) -> bool:
        """Update an existing code version"""
        try:
            session = self.SessionLocal()

            version = (
                session.query(CodeVersion)
                .filter(
                    CodeVersion.code_standard == code_standard,
                    CodeVersion.version_number == version_number,
                )
                .first()
            )

            if not version:
                logger.warning(f"Version {code_standard} {version_number} not found")
                return False

            # Update fields
            for field, value in updates.items():
                if hasattr(version, field):
                    setattr(version, field, value)

            version.updated_at = datetime.utcnow()
            session.commit()

            logger.info(f"✅ Updated version {code_standard} {version_number}")
            return True

        except Exception as e:
            logger.error(f"❌ Error updating code version: {e}")
            session.rollback()
            return False
        finally:
            session.close()

    async def activate_version(self, code_standard: str, version_number: str) -> bool:
        """Activate a specific version and deactivate others"""
        try:
            session = self.SessionLocal()

            # Deactivate all versions for this code standard
            session.query(CodeVersion).filter(
                CodeVersion.code_standard == code_standard
            ).update({"is_active": False})

            # Activate the specified version
            version = (
                session.query(CodeVersion)
                .filter(
                    CodeVersion.code_standard == code_standard,
                    CodeVersion.version_number == version_number,
                )
                .first()
            )

            if not version:
                logger.warning(f"Version {code_standard} {version_number} not found")
                return False

            version.is_active = True
            version.updated_at = datetime.utcnow()
            session.commit()

            logger.info(f"✅ Activated version {code_standard} {version_number}")
            return True

        except Exception as e:
            logger.error(f"❌ Error activating version: {e}")
            session.rollback()
            return False
        finally:
            session.close()

    async def get_version_changes(
        self, code_standard: str, version_from: str, version_to: str
    ) -> List[CodeChange]:
        """Get changes between two versions"""
        try:
            session = self.SessionLocal()

            changes = (
                session.query(CodeChange)
                .filter(
                    CodeChange.code_standard == code_standard,
                    CodeChange.version_from == version_from,
                    CodeChange.version_to == version_to,
                )
                .all()
            )

            change_list = []
            for change in changes:
                change_list.append(
                    CodeChange(
                        code_standard=change.code_standard,
                        version_from=change.version_from,
                        version_to=change.version_to,
                        section_number=change.section_number,
                        change_type=change.change_type,
                        old_content=change.old_content,
                        new_content=change.new_content,
                        change_reason=change.change_reason,
                    )
                )

            return change_list

        except Exception as e:
            logger.error(f"❌ Error getting version changes: {e}")
            return []
        finally:
            session.close()

    async def add_version_change(self, change: CodeChange) -> bool:
        """Add a change record between versions"""
        try:
            session = self.SessionLocal()

            # Check if change already exists
            existing = (
                session.query(CodeChange)
                .filter(
                    CodeChange.code_standard == change.code_standard,
                    CodeChange.version_from == change.version_from,
                    CodeChange.version_to == change.version_to,
                    CodeChange.section_number == change.section_number,
                )
                .first()
            )

            if existing:
                logger.warning(
                    f"Change already exists for {change.code_standard} {change.section_number}"
                )
                return False

            # Add new change
            db_change = CodeChange(
                code_standard=change.code_standard,
                version_from=change.version_from,
                version_to=change.version_to,
                section_number=change.section_number,
                change_type=change.change_type,
                old_content=change.old_content,
                new_content=change.new_content,
                change_reason=change.change_reason,
            )

            session.add(db_change)
            session.commit()

            logger.info(
                f"✅ Added change for {change.code_standard} {change.section_number}"
            )
            return True

        except Exception as e:
            logger.error(f"❌ Error adding version change: {e}")
            session.rollback()
            return False
        finally:
            session.close()

    async def calculate_file_hash(self, content: str) -> str:
        """Calculate hash for file content"""
        try:
            return hashlib.sha256(content.encode("utf-8")).hexdigest()
        except Exception as e:
            logger.error(f"❌ Error calculating file hash: {e}")
            return ""

    async def get_version_statistics(self) -> Dict[str, Any]:
        """Get statistics about code versions"""
        try:
            session = self.SessionLocal()

            total_versions = session.query(CodeVersion).count()
            active_versions = (
                session.query(CodeVersion).filter(CodeVersion.is_active == True).count()
            )

            # Count by code standard
            code_standards = {}
            standards = session.query(CodeVersion.code_standard).distinct().all()
            for standard in standards:
                count = (
                    session.query(CodeVersion)
                    .filter(CodeVersion.code_standard == standard[0])
                    .count()
                )
                code_standards[standard[0]] = count

            # Get latest versions
            latest_versions = {}
            for standard in code_standards.keys():
                latest = (
                    session.query(CodeVersion)
                    .filter(CodeVersion.code_standard == standard)
                    .order_by(CodeVersion.release_date.desc())
                    .first()
                )

                if latest:
                    latest_versions[standard] = {
                        "version": latest.version_number,
                        "release_date": latest.release_date.isoformat(),
                        "is_active": latest.is_active,
                    }

            return {
                "total_versions": total_versions,
                "active_versions": active_versions,
                "code_standards": code_standards,
                "latest_versions": latest_versions,
            }

        except Exception as e:
            logger.error(f"❌ Error getting version statistics: {e}")
            return {}
        finally:
            session.close()

    async def rollback_to_version(
        self, code_standard: str, version_number: str
    ) -> bool:
        """Rollback to a specific version (mark as active)"""
        try:
            return await self.activate_version(code_standard, version_number)
        except Exception as e:
            logger.error(f"❌ Error rolling back to version: {e}")
            return False

    async def get_version_timeline(self, code_standard: str) -> List[Dict[str, Any]]:
        """Get timeline of versions for a code standard"""
        try:
            session = self.SessionLocal()

            versions = (
                session.query(CodeVersion)
                .filter(CodeVersion.code_standard == code_standard)
                .order_by(CodeVersion.release_date.asc())
                .all()
            )

            timeline = []
            for version in versions:
                timeline.append(
                    {
                        "version": version.version_number,
                        "release_date": version.release_date.isoformat(),
                        "effective_date": version.effective_date.isoformat(),
                        "is_active": version.is_active,
                        "change_summary": version.change_summary,
                    }
                )

            return timeline

        except Exception as e:
            logger.error(f"❌ Error getting version timeline: {e}")
            return []
        finally:
            session.close()
