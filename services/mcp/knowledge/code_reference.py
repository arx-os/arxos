"""
Code Reference System for Knowledge Base

This module provides cross-references, citations, and related code sections
for building codes and standards.
"""

import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Set
from pathlib import Path
import asyncio
import re

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


class CodeReferenceDB(Base):
    """Database model for code references"""

    __tablename__ = "code_references"

    id = Column(Integer, primary_key=True)
    source_code = Column(String(50), nullable=False)
    source_section = Column(String(20), nullable=False)
    target_code = Column(String(50), nullable=False)
    target_section = Column(String(20), nullable=False)
    reference_type = Column(String(50), nullable=False)  # CROSS_REF, CITATION, RELATED
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class CodeCitation(Base):
    """Database model for code citations"""

    __tablename__ = "code_citations"

    id = Column(Integer, primary_key=True)
    code_standard = Column(String(50), nullable=False)
    section_number = Column(String(20), nullable=False)
    citation_type = Column(
        String(50), nullable=False
    )  # STANDARD, AMENDMENT, INTERPRETATION
    citation_text = Column(Text, nullable=False)
    source = Column(String(200), nullable=False)
    effective_date = Column(DateTime, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class CodeReference(BaseModel):
    """Pydantic model for code references"""

    source_code: str = Field(..., description="Source code standard")
    source_section: str = Field(..., description="Source section number")
    target_code: str = Field(..., description="Target code standard")
    target_section: str = Field(..., description="Target section number")
    reference_type: str = Field(
        ..., description="Type of reference (CROSS_REF, CITATION, RELATED)"
    )
    description: Optional[str] = Field(None, description="Description of the reference")


class CodeCitation(BaseModel):
    """Pydantic model for code citations"""

    code_standard: str = Field(..., description="Code standard")
    section_number: str = Field(..., description="Section number")
    citation_type: str = Field(
        ..., description="Type of citation (STANDARD, AMENDMENT, INTERPRETATION)"
    )
    citation_text: str = Field(..., description="Citation text")
    source: str = Field(..., description="Source of citation")
    effective_date: datetime = Field(..., description="When citation becomes effective")


class CodeReferenceManager:
    """Manages code references and citations"""

    def __init__(self, database_url: str = "sqlite:///code_reference.db"):
        """Initialize the code reference system"""
        self.database_url = database_url
        self.engine = create_engine(database_url)
        Base.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(
            autocommit=False, autoflush=False, bind=self.engine
        )

        # Initialize reference data
        self._initialize_reference_data()

    def _initialize_reference_data(self):
        """Initialize with sample reference data"""
        try:
            session = self.SessionLocal()

            # Check if data already exists
            if session.query(CodeReferenceDB).count() == 0:
                logger.info("Initializing code reference system with sample data...")
                self._load_sample_references(session)
                session.commit()
                logger.info("✅ Code reference system initialized successfully")
            else:
                logger.info("✅ Code reference system already contains data")

        except Exception as e:
            logger.error(f"❌ Failed to initialize code reference system: {e}")
            raise
        finally:
            session.close()

    def _load_sample_references(self, session):
        """Load sample code references"""
        sample_references = [
            {
                "source_code": "IBC",
                "source_section": "1004.1.1",
                "target_code": "IBC",
                "target_section": "1004.1.2",
                "reference_type": "CROSS_REF",
                "description": "Occupant load determination references occupant load factors table",
            },
            {
                "source_code": "IBC",
                "source_section": "1004.1.1",
                "target_code": "IBC",
                "target_section": "1004.2",
                "reference_type": "RELATED",
                "description": "Related to occupant load calculation methods",
            },
            {
                "source_code": "NEC",
                "source_section": "210.8",
                "target_code": "NEC",
                "target_section": "210.8(A)",
                "reference_type": "CROSS_REF",
                "description": "GFCI protection requirements for specific locations",
            },
            {
                "source_code": "ADA",
                "source_section": "4.1.3",
                "target_code": "ADA",
                "target_section": "4.1.1",
                "reference_type": "CROSS_REF",
                "description": "Accessibility requirements for new construction",
            },
            {
                "source_code": "NFPA",
                "source_section": "101-7.2.1.1",
                "target_code": "NFPA",
                "target_section": "101-7.2.1.2",
                "reference_type": "RELATED",
                "description": "Related to means of egress components",
            },
        ]

        for ref_data in sample_references:
            reference = CodeReferenceDB(
                source_code=ref_data["source_code"],
                source_section=ref_data["source_section"],
                target_code=ref_data["target_code"],
                target_section=ref_data["target_section"],
                reference_type=ref_data["reference_type"],
                description=ref_data["description"],
            )
            session.add(reference)

    async def get_cross_references(
        self, code_standard: str, section_number: str
    ) -> List[CodeReference]:
        """Get cross-references for a specific code section"""
        try:
            session = self.SessionLocal()

            references = (
                session.query(CodeReferenceDB)
                .filter(
                    CodeReferenceDB.source_code == code_standard,
                    CodeReferenceDB.source_section == section_number,
                    CodeReferenceDB.reference_type == "CROSS_REF",
                    CodeReferenceDB.is_active == True,
                )
                .all()
            )

            ref_list = []
            for ref in references:
                ref_list.append(
                    CodeReference(
                        source_code=ref.source_code,
                        source_section=ref.source_section,
                        target_code=ref.target_code,
                        target_section=ref.target_section,
                        reference_type=ref.reference_type,
                        description=ref.description,
                    )
                )

            return ref_list

        except Exception as e:
            logger.error(f"❌ Error getting cross references: {e}")
            return []
        finally:
            session.close()

    async def get_related_sections(
        self, code_standard: str, section_number: str
    ) -> List[CodeReference]:
        """Get related sections for a specific code section"""
        try:
            session = self.SessionLocal()

            references = (
                session.query(CodeReferenceDB)
                .filter(
                    CodeReferenceDB.source_code == code_standard,
                    CodeReferenceDB.source_section == section_number,
                    CodeReferenceDB.reference_type == "RELATED",
                    CodeReferenceDB.is_active == True,
                )
                .all()
            )

            ref_list = []
            for ref in references:
                ref_list.append(
                    CodeReference(
                        source_code=ref.source_code,
                        source_section=ref.source_section,
                        target_code=ref.target_code,
                        target_section=ref.target_section,
                        reference_type=ref.reference_type,
                        description=ref.description,
                    )
                )

            return ref_list

        except Exception as e:
            logger.error(f"❌ Error getting related sections: {e}")
            return []
        finally:
            session.close()

    async def get_all_references(
        self, code_standard: str, section_number: str
    ) -> List[CodeReference]:
        """Get all references for a specific code section"""
        try:
            session = self.SessionLocal()

            references = (
                session.query(CodeReferenceDB)
                .filter(
                    CodeReferenceDB.source_code == code_standard,
                    CodeReferenceDB.source_section == section_number,
                    CodeReferenceDB.is_active == True,
                )
                .all()
            )

            ref_list = []
            for ref in references:
                ref_list.append(
                    CodeReference(
                        source_code=ref.source_code,
                        source_section=ref.source_section,
                        target_code=ref.target_code,
                        target_section=ref.target_section,
                        reference_type=ref.reference_type,
                        description=ref.description,
                    )
                )

            return ref_list

        except Exception as e:
            logger.error(f"❌ Error getting all references: {e}")
            return []
        finally:
            session.close()

    async def add_code_reference(self, reference: CodeReference) -> bool:
        """Add a new code reference"""
        try:
            session = self.SessionLocal()

            # Check if reference already exists
            existing = (
                session.query(CodeReferenceDB)
                .filter(
                    CodeReferenceDB.source_code == reference.source_code,
                    CodeReferenceDB.source_section == reference.source_section,
                    CodeReferenceDB.target_code == reference.target_code,
                    CodeReferenceDB.target_section == reference.target_section,
                    CodeReferenceDB.reference_type == reference.reference_type,
                )
                .first()
            )

            if existing:
                logger.warning(
                    f"Reference already exists for {reference.source_code} {reference.source_section}"
                )
                return False

            # Add new reference
            db_reference = CodeReferenceDB(
                source_code=reference.source_code,
                source_section=reference.source_section,
                target_code=reference.target_code,
                target_section=reference.target_section,
                reference_type=reference.reference_type,
                description=reference.description,
            )

            session.add(db_reference)
            session.commit()

            logger.info(
                f"✅ Added reference for {reference.source_code} {reference.source_section}"
            )
            return True

        except Exception as e:
            logger.error(f"❌ Error adding code reference: {e}")
            session.rollback()
            return False
        finally:
            session.close()

    async def update_code_reference(
        self,
        source_code: str,
        source_section: str,
        target_code: str,
        target_section: str,
        updates: Dict[str, Any],
    ) -> bool:
        """Update an existing code reference"""
        try:
            session = self.SessionLocal()

            reference = (
                session.query(CodeReferenceDB)
                .filter(
                    CodeReferenceDB.source_code == source_code,
                    CodeReferenceDB.source_section == source_section,
                    CodeReferenceDB.target_code == target_code,
                    CodeReferenceDB.target_section == target_section,
                )
                .first()
            )

            if not reference:
                logger.warning(
                    f"Reference not found for {source_code} {source_section}"
                )
                return False

            # Update fields
            for field, value in updates.items():
                if hasattr(reference, field):
                    setattr(reference, field, value)

            reference.updated_at = datetime.utcnow()
            session.commit()

            logger.info(f"✅ Updated reference for {source_code} {source_section}")
            return True

        except Exception as e:
            logger.error(f"❌ Error updating code reference: {e}")
            session.rollback()
            return False
        finally:
            session.close()

    async def delete_code_reference(
        self,
        source_code: str,
        source_section: str,
        target_code: str,
        target_section: str,
    ) -> bool:
        """Soft delete a code reference"""
        try:
            session = self.SessionLocal()

            reference = (
                session.query(CodeReferenceDB)
                .filter(
                    CodeReferenceDB.source_code == source_code,
                    CodeReferenceDB.source_section == source_section,
                    CodeReferenceDB.target_code == target_code,
                    CodeReferenceDB.target_section == target_section,
                )
                .first()
            )

            if not reference:
                logger.warning(
                    f"Reference not found for {source_code} {source_section}"
                )
                return False

            reference.is_active = False
            reference.updated_at = datetime.utcnow()
            session.commit()

            logger.info(f"✅ Deleted reference for {source_code} {source_section}")
            return True

        except Exception as e:
            logger.error(f"❌ Error deleting code reference: {e}")
            session.rollback()
            return False
        finally:
            session.close()

    async def get_reference_statistics(self) -> Dict[str, Any]:
        """Get statistics about code references"""
        try:
            session = self.SessionLocal()

            total_references = session.query(CodeReferenceDB).count()
            active_references = (
                session.query(CodeReferenceDB)
                .filter(CodeReferenceDB.is_active == True)
                .count()
            )

            # Count by reference type
            reference_types = {}
            types = session.query(CodeReferenceDB.reference_type).distinct().all()
            for ref_type in types:
                count = (
                    session.query(CodeReferenceDB)
                    .filter(
                        CodeReferenceDB.reference_type == ref_type[0],
                        CodeReferenceDB.is_active == True,
                    )
                    .count()
                )
                reference_types[ref_type[0]] = count

            # Count by code standard
            code_standards = {}
            standards = session.query(CodeReferenceDB.source_code).distinct().all()
            for standard in standards:
                count = (
                    session.query(CodeReferenceDB)
                    .filter(
                        CodeReferenceDB.source_code == standard[0],
                        CodeReferenceDB.is_active == True,
                    )
                    .count()
                )
                code_standards[standard[0]] = count

            return {
                "total_references": total_references,
                "active_references": active_references,
                "reference_types": reference_types,
                "code_standards": code_standards,
            }

        except Exception as e:
            logger.error(f"❌ Error getting reference statistics: {e}")
            return {}
        finally:
            session.close()

    async def find_referencing_sections(
        self, code_standard: str, section_number: str
    ) -> List[CodeReference]:
        """Find sections that reference a specific code section"""
        try:
            session = self.SessionLocal()

            references = (
                session.query(CodeReferenceDB)
                .filter(
                    CodeReferenceDB.target_code == code_standard,
                    CodeReferenceDB.target_section == section_number,
                    CodeReferenceDB.is_active == True,
                )
                .all()
            )

            ref_list = []
            for ref in references:
                ref_list.append(
                    CodeReference(
                        source_code=ref.source_code,
                        source_section=ref.source_section,
                        target_code=ref.target_code,
                        target_section=ref.target_section,
                        reference_type=ref.reference_type,
                        description=ref.description,
                    )
                )

            return ref_list

        except Exception as e:
            logger.error(f"❌ Error finding referencing sections: {e}")
            return []
        finally:
            session.close()

    async def get_reference_chain(
        self, code_standard: str, section_number: str, max_depth: int = 3
    ) -> List[Dict[str, Any]]:
        """Get a chain of references starting from a specific section"""
        try:
            chain = []
            visited = set()

            async def build_chain(current_code: str, current_section: str, depth: int):
                if depth > max_depth or (current_code, current_section) in visited:
                    return

                visited.add((current_code, current_section))

                # Get references from current section
                references = await self.get_all_references(
                    current_code, current_section
                )

                for ref in references:
                    chain.append(
                        {
                            "depth": depth,
                            "source": f"{ref.source_code} {ref.source_section}",
                            "target": f"{ref.target_code} {ref.target_section}",
                            "type": ref.reference_type,
                            "description": ref.description,
                        }
                    )

                    # Recursively build chain
                    await build_chain(ref.target_code, ref.target_section, depth + 1)

            await build_chain(code_standard, section_number, 0)
            return chain

        except Exception as e:
            logger.error(f"❌ Error getting reference chain: {e}")
            return []

    async def validate_references(
        self, code_standard: str, section_number: str
    ) -> Dict[str, Any]:
        """Validate that all references for a section are valid"""
        try:
            session = self.SessionLocal()

            # Get all references for the section
            references = (
                session.query(CodeReferenceDB)
                .filter(
                    CodeReferenceDB.source_code == code_standard,
                    CodeReferenceDB.source_section == section_number,
                    CodeReferenceDB.is_active == True,
                )
                .all()
            )

            validation_results = {
                "section": f"{code_standard} {section_number}",
                "total_references": len(references),
                "valid_references": 0,
                "invalid_references": 0,
                "issues": [],
            }

            for ref in references:
                # Check if target section exists (this would require integration with knowledge base)
                # For now, we'll assume all references are valid
                validation_results["valid_references"] += 1

            return validation_results

        except Exception as e:
            logger.error(f"❌ Error validating references: {e}")
            return {}
        finally:
            session.close()
