"""
Knowledge Base System

This module provides the core knowledge base functionality for building codes,
engineering standards, and best practices.
"""

import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Set
from pathlib import Path
import asyncio

from pydantic import BaseModel, Field
from sqlalchemy import create_engine, Column, String, Text, DateTime, Integer, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)

Base = declarative_base()


class CodeSection(Base):
    """Database model for code sections"""

    __tablename__ = "code_sections"

    id = Column(Integer, primary_key=True)
    code_standard = Column(
        String(50), nullable=False
    )  # IBC, NEC, IFC, ADA, NFPA, ASHRAE
    section_number = Column(String(20), nullable=False)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    jurisdiction = Column(String(100), nullable=False)
    version = Column(String(20), nullable=False)
    effective_date = Column(DateTime, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class CodeRequirement(BaseModel):
    """Pydantic model for code requirements"""

    code_standard: str = Field(
        ..., description="Building code standard (IBC, NEC, IFC, ADA, NFPA, ASHRAE)"
    )
    section_number: str = Field(..., description="Section number within the code")
    title: str = Field(..., description="Title of the section")
    content: str = Field(..., description="Full content of the section")
    jurisdiction: str = Field(..., description="Jurisdiction this applies to")
    version: str = Field(..., description="Version of the code")
    effective_date: datetime = Field(
        ..., description="When this version became effective"
    )
    requirements: List[str] = Field(
        default_factory=list, description="Extracted requirements"
    )
    keywords: List[str] = Field(default_factory=list, description="Keywords for search")
    related_sections: List[str] = Field(
        default_factory=list, description="Related section numbers"
    )


class KnowledgeBase:
    """Main knowledge base class for building codes and standards"""

    def __init__(self, database_url: str = "sqlite:///knowledge_base.db"):
        """Initialize the knowledge base"""
        self.database_url = database_url
        self.engine = create_engine(database_url)
        Base.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(
            autocommit=False, autoflush=False, bind=self.engine
        )

        # Supported building codes
        self.supported_codes = {
            "IBC": "International Building Code",
            "NEC": "National Electrical Code",
            "IFC": "International Fire Code",
            "ADA": "Americans with Disabilities Act",
            "NFPA": "National Fire Protection Association",
            "ASHRAE": "American Society of Heating, Refrigerating and Air-Conditioning Engineers",
        }

        # Initialize code data
        self._initialize_code_data()

    def _initialize_code_data(self):
        """Initialize with sample building code data"""
        try:
            session = self.SessionLocal()

            # Check if data already exists
            if session.query(CodeSection).count() == 0:
                logger.info(
                    "Initializing knowledge base with sample building code data..."
                )
                self._load_sample_data(session)
                session.commit()
                logger.info("✅ Knowledge base initialized successfully")
            else:
                logger.info("✅ Knowledge base already contains data")

        except Exception as e:
            logger.error(f"❌ Failed to initialize knowledge base: {e}")
            raise
        finally:
            session.close()

    def _load_sample_data(self, session):
        """Load sample building code data"""
        sample_data = [
            {
                "code_standard": "IBC",
                "section_number": "1004.1.1",
                "title": "Occupant Load Determination",
                "content": "The occupant load shall be determined by dividing the floor area assigned to that use by the occupant load factor for that use as set forth in Table 1004.1.2.",
                "jurisdiction": "International",
                "version": "2021",
                "effective_date": datetime(2021, 1, 1),
                "requirements": [
                    "Calculate occupant load",
                    "Use Table 1004.1.2",
                    "Divide floor area by occupant load factor",
                ],
                "keywords": ["occupant load", "floor area", "occupancy", "calculation"],
                "related_sections": ["1004.1.2", "1004.2", "1004.3"],
            },
            {
                "code_standard": "IBC",
                "section_number": "1004.1.2",
                "title": "Occupant Load Factors",
                "content": "The occupant load factors shall be used to determine the occupant load for the following areas: Assembly areas, Business areas, Educational facilities, etc.",
                "jurisdiction": "International",
                "version": "2021",
                "effective_date": datetime(2021, 1, 1),
                "requirements": [
                    "Use specified occupant load factors",
                    "Apply to assembly areas",
                    "Apply to business areas",
                    "Apply to educational facilities",
                ],
                "keywords": [
                    "occupant load factors",
                    "assembly",
                    "business",
                    "educational",
                    "table",
                ],
                "related_sections": ["1004.1.1", "1004.2", "1004.3"],
            },
            {
                "code_standard": "NEC",
                "section_number": "210.8",
                "title": "Ground-Fault Circuit-Interrupter Protection for Personnel",
                "content": "Ground-fault circuit-interrupter protection for personnel shall be provided as required in 210.8(A) through (F).",
                "jurisdiction": "International",
                "version": "2023",
                "effective_date": datetime(2023, 1, 1),
                "requirements": [
                    "Provide GFCI protection",
                    "Install in required locations",
                    "Test regularly",
                ],
                "keywords": [
                    "GFCI",
                    "ground fault",
                    "circuit interrupter",
                    "electrical safety",
                ],
                "related_sections": ["210.8(A)", "210.8(B)", "210.8(C)"],
            },
            {
                "code_standard": "ADA",
                "section_number": "4.1.3",
                "title": "Accessible Buildings: New Construction",
                "content": "All areas of newly designed or newly constructed buildings and facilities shall comply with 4.1.1 through 4.1.7, as applicable.",
                "jurisdiction": "Federal",
                "version": "2010",
                "effective_date": datetime(2010, 3, 15),
                "requirements": [
                    "Comply with accessibility standards",
                    "Design for accessibility",
                    "Construct accessible facilities",
                ],
                "keywords": [
                    "accessibility",
                    "ADA compliance",
                    "new construction",
                    "accessible design",
                ],
                "related_sections": ["4.1.1", "4.1.2", "4.1.4", "4.1.5"],
            },
            {
                "code_standard": "NFPA",
                "section_number": "101-7.2.1.1",
                "title": "Means of Egress Components",
                "content": "Means of egress shall consist of exit access, exits, and exit discharge.",
                "jurisdiction": "International",
                "version": "2021",
                "effective_date": datetime(2021, 1, 1),
                "requirements": [
                    "Provide exit access",
                    "Provide exits",
                    "Provide exit discharge",
                ],
                "keywords": [
                    "means of egress",
                    "exit access",
                    "exits",
                    "exit discharge",
                    "life safety",
                ],
                "related_sections": ["7.2.1.2", "7.2.1.3", "7.2.2"],
            },
        ]

        for data in sample_data:
            code_section = CodeSection(
                code_standard=data["code_standard"],
                section_number=data["section_number"],
                title=data["title"],
                content=data["content"],
                jurisdiction=data["jurisdiction"],
                version=data["version"],
                effective_date=data["effective_date"],
            )
            session.add(code_section)

    async def search_codes(
        self,
        query: str,
        code_standard: Optional[str] = None,
        jurisdiction: Optional[str] = None,
    ) -> List[CodeRequirement]:
        """Search building codes by query"""
        try:
            session = self.SessionLocal()

            # Build query
            db_query = session.query(CodeSection).filter(CodeSection.is_active == True)

            if code_standard:
                db_query = db_query.filter(CodeSection.code_standard == code_standard)

            if jurisdiction:
                db_query = db_query.filter(CodeSection.jurisdiction == jurisdiction)

            # Search in title and content
            search_terms = query.lower().split()
            for term in search_terms:
                db_query = db_query.filter(
                    (CodeSection.title.ilike(f"%{term}%"))
                    | (CodeSection.content.ilike(f"%{term}%"))
                )

            results = db_query.all()

            # Convert to Pydantic models
            code_requirements = []
            for result in results:
                code_requirements.append(
                    CodeRequirement(
                        code_standard=result.code_standard,
                        section_number=result.section_number,
                        title=result.title,
                        content=result.content,
                        jurisdiction=result.jurisdiction,
                        version=result.version,
                        effective_date=result.effective_date,
                    )
                )

            return code_requirements

        except Exception as e:
            logger.error(f"❌ Error searching codes: {e}")
            return []
        finally:
            session.close()

    async def get_code_section(
        self, code_standard: str, section_number: str
    ) -> Optional[CodeRequirement]:
        """Get a specific code section"""
        try:
            session = self.SessionLocal()

            result = (
                session.query(CodeSection)
                .filter(
                    CodeSection.code_standard == code_standard,
                    CodeSection.section_number == section_number,
                    CodeSection.is_active == True,
                )
                .first()
            )

            if result:
                return CodeRequirement(
                    code_standard=result.code_standard,
                    section_number=result.section_number,
                    title=result.title,
                    content=result.content,
                    jurisdiction=result.jurisdiction,
                    version=result.version,
                    effective_date=result.effective_date,
                )

            return None

        except Exception as e:
            logger.error(f"❌ Error getting code section: {e}")
            return None
        finally:
            session.close()

    async def get_supported_codes(self) -> Dict[str, str]:
        """Get list of supported building codes"""
        return self.supported_codes

    async def add_code_section(self, code_requirement: CodeRequirement) -> bool:
        """Add a new code section to the knowledge base"""
        try:
            session = self.SessionLocal()

            # Check if section already exists
            existing = (
                session.query(CodeSection)
                .filter(
                    CodeSection.code_standard == code_requirement.code_standard,
                    CodeSection.section_number == code_requirement.section_number,
                )
                .first()
            )

            if existing:
                logger.warning(
                    f"Code section {code_requirement.code_standard} {code_requirement.section_number} already exists"
                )
                return False

            # Add new section
            code_section = CodeSection(
                code_standard=code_requirement.code_standard,
                section_number=code_requirement.section_number,
                title=code_requirement.title,
                content=code_requirement.content,
                jurisdiction=code_requirement.jurisdiction,
                version=code_requirement.version,
                effective_date=code_requirement.effective_date,
            )

            session.add(code_section)
            session.commit()

            logger.info(
                f"✅ Added code section {code_requirement.code_standard} {code_requirement.section_number}"
            )
            return True

        except Exception as e:
            logger.error(f"❌ Error adding code section: {e}")
            session.rollback()
            return False
        finally:
            session.close()

    async def update_code_section(
        self, code_standard: str, section_number: str, updates: Dict[str, Any]
    ) -> bool:
        """Update an existing code section"""
        try:
            session = self.SessionLocal()

            code_section = (
                session.query(CodeSection)
                .filter(
                    CodeSection.code_standard == code_standard,
                    CodeSection.section_number == section_number,
                )
                .first()
            )

            if not code_section:
                logger.warning(
                    f"Code section {code_standard} {section_number} not found"
                )
                return False

            # Update fields
            for field, value in updates.items():
                if hasattr(code_section, field):
                    setattr(code_section, field, value)

            code_section.updated_at = datetime.utcnow()
            session.commit()

            logger.info(f"✅ Updated code section {code_standard} {section_number}")
            return True

        except Exception as e:
            logger.error(f"❌ Error updating code section: {e}")
            session.rollback()
            return False
        finally:
            session.close()

    async def delete_code_section(
        self, code_standard: str, section_number: str
    ) -> bool:
        """Soft delete a code section (mark as inactive)"""
        try:
            session = self.SessionLocal()

            code_section = (
                session.query(CodeSection)
                .filter(
                    CodeSection.code_standard == code_standard,
                    CodeSection.section_number == section_number,
                )
                .first()
            )

            if not code_section:
                logger.warning(
                    f"Code section {code_standard} {section_number} not found"
                )
                return False

            code_section.is_active = False
            code_section.updated_at = datetime.utcnow()
            session.commit()

            logger.info(f"✅ Deleted code section {code_standard} {section_number}")
            return True

        except Exception as e:
            logger.error(f"❌ Error deleting code section: {e}")
            session.rollback()
            return False
        finally:
            session.close()

    async def get_statistics(self) -> Dict[str, Any]:
        """Get knowledge base statistics"""
        try:
            session = self.SessionLocal()

            total_sections = session.query(CodeSection).count()
            active_sections = (
                session.query(CodeSection).filter(CodeSection.is_active == True).count()
            )

            # Count by code standard
            code_standards = {}
            for code in self.supported_codes.keys():
                count = (
                    session.query(CodeSection)
                    .filter(
                        CodeSection.code_standard == code, CodeSection.is_active == True
                    )
                    .count()
                )
                code_standards[code] = count

            return {
                "total_sections": total_sections,
                "active_sections": active_sections,
                "code_standards": code_standards,
                "supported_codes": len(self.supported_codes),
            }

        except Exception as e:
            logger.error(f"❌ Error getting statistics: {e}")
            return {}
        finally:
            session.close()
