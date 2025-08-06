"""
Jurisdiction Manager for Knowledge Base

This module manages jurisdiction-specific building codes, local amendments,
and regional variations of national building codes.
"""

import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Set
from pathlib import Path
import asyncio

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


class JurisdictionAmendmentDB(Base):
    """Database model for jurisdiction amendments"""

    __tablename__ = "jurisdiction_amendments"

    id = Column(Integer, primary_key=True)
    jurisdiction = Column(String(100), nullable=False)
    code_standard = Column(String(50), nullable=False)
    section_number = Column(String(20), nullable=False)
    amendment_type = Column(String(50), nullable=False)  # ADD, MODIFY, DELETE
    original_content = Column(Text, nullable=True)
    amended_content = Column(Text, nullable=False)
    effective_date = Column(DateTime, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class JurisdictionInfo(BaseModel):
    """Pydantic model for jurisdiction information"""

    jurisdiction: str = Field(..., description="Jurisdiction name")
    state: Optional[str] = Field(None, description="State or province")
    country: str = Field(..., description="Country")
    code_standards: List[str] = Field(
        default_factory=list, description="Supported code standards"
    )
    amendments_count: int = Field(0, description="Number of local amendments")
    last_updated: datetime = Field(..., description="Last update date")
    contact_info: Dict[str, str] = Field(
        default_factory=dict, description="Contact information"
    )


class JurisdictionAmendment(BaseModel):
    """Pydantic model for jurisdiction amendments"""

    jurisdiction: str = Field(..., description="Jurisdiction name")
    code_standard: str = Field(..., description="Code standard being amended")
    section_number: str = Field(..., description="Section number being amended")
    amendment_type: str = Field(
        ..., description="Type of amendment (ADD, MODIFY, DELETE)"
    )
    original_content: Optional[str] = Field(
        None, description="Original content (for MODIFY/DELETE)"
    )
    amended_content: str = Field(..., description="Amended content")
    effective_date: datetime = Field(
        ..., description="When amendment becomes effective"
    )
    reason: Optional[str] = Field(None, description="Reason for amendment")


class JurisdictionManager:
    """Manages jurisdiction-specific building codes and amendments"""

    def __init__(self, database_url: str = "sqlite:///jurisdiction.db"):
        """Initialize the jurisdiction manager"""
        self.database_url = database_url
        self.engine = create_engine(database_url)
        Base.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(
            autocommit=False, autoflush=False, bind=self.engine
        )

        # Common jurisdictions with their characteristics
        self.jurisdictions = {
            "International": {
                "country": "International",
                "code_standards": ["IBC", "NEC", "IFC", "NFPA", "ASHRAE"],
                "amendments_count": 0,
                "last_updated": datetime.utcnow(),
                "contact_info": {},
            },
            "Federal": {
                "country": "United States",
                "code_standards": ["ADA"],
                "amendments_count": 0,
                "last_updated": datetime.utcnow(),
                "contact_info": {},
            },
            "California": {
                "country": "United States",
                "state": "California",
                "code_standards": ["IBC", "NEC", "IFC", "NFPA", "ASHRAE", "ADA"],
                "amendments_count": 0,
                "last_updated": datetime.utcnow(),
                "contact_info": {
                    "building_department": "California Building Standards Commission",
                    "website": "https://www.dgs.ca.gov/bsc",
                    "phone": "(916) 263-0911",
                },
            },
            "New York": {
                "country": "United States",
                "state": "New York",
                "code_standards": ["IBC", "NEC", "IFC", "NFPA", "ASHRAE", "ADA"],
                "amendments_count": 0,
                "last_updated": datetime.utcnow(),
                "contact_info": {
                    "building_department": "New York State Department of State",
                    "website": "https://www.dos.ny.gov/dcea",
                    "phone": "(518) 474-4073",
                },
            },
            "Texas": {
                "country": "United States",
                "state": "Texas",
                "code_standards": ["IBC", "NEC", "IFC", "NFPA", "ASHRAE", "ADA"],
                "amendments_count": 0,
                "last_updated": datetime.utcnow(),
                "contact_info": {
                    "building_department": "Texas Department of Licensing and Regulation",
                    "website": "https://www.tdlr.texas.gov",
                    "phone": "(512) 463-6599",
                },
            },
            "Florida": {
                "country": "United States",
                "state": "Florida",
                "code_standards": ["IBC", "NEC", "IFC", "NFPA", "ASHRAE", "ADA"],
                "amendments_count": 0,
                "last_updated": datetime.utcnow(),
                "contact_info": {
                    "building_department": "Florida Building Commission",
                    "website": "https://floridabuilding.org",
                    "phone": "(850) 487-1824",
                },
            },
        }

        # Initialize jurisdiction data
        self._initialize_jurisdiction_data()

    def _initialize_jurisdiction_data(self):
        """Initialize with sample jurisdiction amendments"""
        try:
            session = self.SessionLocal()

            # Check if data already exists
            if session.query(JurisdictionAmendmentDB).count() == 0:
                logger.info(
                    "Initializing jurisdiction manager with sample amendments..."
                )
                self._load_sample_amendments(session)
                session.commit()
                logger.info("✅ Jurisdiction manager initialized successfully")
            else:
                logger.info("✅ Jurisdiction manager already contains data")

        except Exception as e:
            logger.error(f"❌ Failed to initialize jurisdiction manager: {e}")
            raise
        finally:
            session.close()

    def _load_sample_amendments(self, session):
        """Load sample jurisdiction amendments"""
        sample_amendments = [
            {
                "jurisdiction": "California",
                "code_standard": "IBC",
                "section_number": "1004.1.1",
                "amendment_type": "MODIFY",
                "original_content": "The occupant load shall be determined by dividing the floor area assigned to that use by the occupant load factor for that use as set forth in Table 1004.1.2.",
                "amended_content": "The occupant load shall be determined by dividing the floor area assigned to that use by the occupant load factor for that use as set forth in Table 1004.1.2. For California, additional factors may apply based on local conditions.",
                "effective_date": datetime(2021, 1, 1),
                "reason": "California-specific occupancy considerations",
            },
            {
                "jurisdiction": "California",
                "code_standard": "NEC",
                "section_number": "210.8",
                "amendment_type": "ADD",
                "original_content": None,
                "amended_content": "In California, additional GFCI protection requirements apply to outdoor receptacles within 6 feet of water sources.",
                "effective_date": datetime(2023, 1, 1),
                "reason": "Enhanced electrical safety for California climate",
            },
            {
                "jurisdiction": "New York",
                "code_standard": "IBC",
                "section_number": "1004.1.2",
                "amendment_type": "MODIFY",
                "original_content": "The occupant load factors shall be used to determine the occupant load for the following areas: Assembly areas, Business areas, Educational facilities, etc.",
                "amended_content": "The occupant load factors shall be used to determine the occupant load for the following areas: Assembly areas, Business areas, Educational facilities, etc. New York City requires additional considerations for high-density areas.",
                "effective_date": datetime(2021, 1, 1),
                "reason": "New York City density considerations",
            },
            {
                "jurisdiction": "Texas",
                "code_standard": "IFC",
                "section_number": "101-7.2.1.1",
                "amendment_type": "ADD",
                "original_content": None,
                "amended_content": "Texas requires additional fire safety measures for buildings in hurricane-prone areas.",
                "effective_date": datetime(2021, 1, 1),
                "reason": "Hurricane safety requirements",
            },
            {
                "jurisdiction": "Florida",
                "code_standard": "IBC",
                "section_number": "1603.1.1",
                "amendment_type": "MODIFY",
                "original_content": "Buildings and other structures shall be designed and constructed to resist the effects of earthquake motions in accordance with this code.",
                "amended_content": "Buildings and other structures shall be designed and constructed to resist the effects of earthquake motions and hurricane forces in accordance with this code and Florida-specific requirements.",
                "effective_date": datetime(2021, 1, 1),
                "reason": "Florida hurricane and seismic requirements",
            },
        ]

        for amendment_data in sample_amendments:
            amendment = JurisdictionAmendmentDB(
                jurisdiction=amendment_data["jurisdiction"],
                code_standard=amendment_data["code_standard"],
                section_number=amendment_data["section_number"],
                amendment_type=amendment_data["amendment_type"],
                original_content=amendment_data["original_content"],
                amended_content=amendment_data["amended_content"],
                effective_date=amendment_data["effective_date"],
            )
            session.add(amendment)

    async def get_jurisdiction_info(
        self, jurisdiction: str
    ) -> Optional[JurisdictionInfo]:
        """Get information about a specific jurisdiction"""
        try:
            if jurisdiction not in self.jurisdictions:
                return None

            jurisdiction_data = self.jurisdictions[jurisdiction]

            # Get amendment count
            session = self.SessionLocal()
            amendments_count = (
                session.query(JurisdictionAmendmentDB)
                .filter(
                    JurisdictionAmendmentDB.jurisdiction == jurisdiction,
                    JurisdictionAmendmentDB.is_active == True,
                )
                .count()
            )
            session.close()

            return JurisdictionInfo(
                jurisdiction=jurisdiction,
                state=jurisdiction_data.get("state"),
                country=jurisdiction_data["country"],
                code_standards=jurisdiction_data["code_standards"],
                amendments_count=amendments_count,
                last_updated=jurisdiction_data["last_updated"],
                contact_info=jurisdiction_data["contact_info"],
            )

        except Exception as e:
            logger.error(f"❌ Error getting jurisdiction info: {e}")
            return None

    async def get_all_jurisdictions(self) -> List[JurisdictionInfo]:
        """Get information about all jurisdictions"""
        try:
            jurisdictions = []

            for jurisdiction_name in self.jurisdictions.keys():
                jurisdiction_info = await self.get_jurisdiction_info(jurisdiction_name)
                if jurisdiction_info:
                    jurisdictions.append(jurisdiction_info)

            return jurisdictions

        except Exception as e:
            logger.error(f"❌ Error getting all jurisdictions: {e}")
            return []

    async def get_jurisdiction_amendments(
        self, jurisdiction: str, code_standard: Optional[str] = None
    ) -> List[JurisdictionAmendment]:
        """Get amendments for a specific jurisdiction"""
        try:
            session = self.SessionLocal()

            query = session.query(JurisdictionAmendmentDB).filter(
                JurisdictionAmendmentDB.jurisdiction == jurisdiction,
                JurisdictionAmendmentDB.is_active == True,
            )

            if code_standard:
                query = query.filter(
                    JurisdictionAmendment.code_standard == code_standard
                )

            results = query.all()

            amendments = []
            for result in results:
                amendments.append(
                    JurisdictionAmendment(
                        jurisdiction=result.jurisdiction,
                        code_standard=result.code_standard,
                        section_number=result.section_number,
                        amendment_type=result.amendment_type,
                        original_content=result.original_content,
                        amended_content=result.amended_content,
                        effective_date=result.effective_date,
                    )
                )

            return amendments

        except Exception as e:
            logger.error(f"❌ Error getting jurisdiction amendments: {e}")
            return []
        finally:
            session.close()

    async def add_jurisdiction_amendment(
        self, amendment: JurisdictionAmendment
    ) -> bool:
        """Add a new jurisdiction amendment"""
        try:
            session = self.SessionLocal()

            # Check if amendment already exists
            existing = (
                session.query(JurisdictionAmendmentDB)
                .filter(
                    JurisdictionAmendmentDB.jurisdiction == amendment.jurisdiction,
                    JurisdictionAmendmentDB.code_standard == amendment.code_standard,
                    JurisdictionAmendmentDB.section_number == amendment.section_number,
                    JurisdictionAmendmentDB.amendment_type == amendment.amendment_type,
                )
                .first()
            )

            if existing:
                logger.warning(
                    f"Amendment already exists for {amendment.jurisdiction} {amendment.code_standard} {amendment.section_number}"
                )
                return False

            # Add new amendment
            db_amendment = JurisdictionAmendmentDB(
                jurisdiction=amendment.jurisdiction,
                code_standard=amendment.code_standard,
                section_number=amendment.section_number,
                amendment_type=amendment.amendment_type,
                original_content=amendment.original_content,
                amended_content=amendment.amended_content,
                effective_date=amendment.effective_date,
            )

            session.add(db_amendment)
            session.commit()

            logger.info(
                f"✅ Added amendment for {amendment.jurisdiction} {amendment.code_standard} {amendment.section_number}"
            )
            return True

        except Exception as e:
            logger.error(f"❌ Error adding jurisdiction amendment: {e}")
            session.rollback()
            return False
        finally:
            session.close()

    async def update_jurisdiction_amendment(
        self,
        jurisdiction: str,
        code_standard: str,
        section_number: str,
        updates: Dict[str, Any],
    ) -> bool:
        """Update an existing jurisdiction amendment"""
        try:
            session = self.SessionLocal()

            amendment = (
                session.query(JurisdictionAmendmentDB)
                .filter(
                    JurisdictionAmendmentDB.jurisdiction == jurisdiction,
                    JurisdictionAmendmentDB.code_standard == code_standard,
                    JurisdictionAmendmentDB.section_number == section_number,
                )
                .first()
            )

            if not amendment:
                logger.warning(
                    f"Amendment not found for {jurisdiction} {code_standard} {section_number}"
                )
                return False

            # Update fields
            for field, value in updates.items():
                if hasattr(amendment, field):
                    setattr(amendment, field, value)

            amendment.updated_at = datetime.utcnow()
            session.commit()

            logger.info(
                f"✅ Updated amendment for {jurisdiction} {code_standard} {section_number}"
            )
            return True

        except Exception as e:
            logger.error(f"❌ Error updating jurisdiction amendment: {e}")
            session.rollback()
            return False
        finally:
            session.close()

    async def delete_jurisdiction_amendment(
        self, jurisdiction: str, code_standard: str, section_number: str
    ) -> bool:
        """Soft delete a jurisdiction amendment"""
        try:
            session = self.SessionLocal()

            amendment = (
                session.query(JurisdictionAmendmentDB)
                .filter(
                    JurisdictionAmendmentDB.jurisdiction == jurisdiction,
                    JurisdictionAmendmentDB.code_standard == code_standard,
                    JurisdictionAmendmentDB.section_number == section_number,
                )
                .first()
            )

            if not amendment:
                logger.warning(
                    f"Amendment not found for {jurisdiction} {code_standard} {section_number}"
                )
                return False

            amendment.is_active = False
            amendment.updated_at = datetime.utcnow()
            session.commit()

            logger.info(
                f"✅ Deleted amendment for {jurisdiction} {code_standard} {section_number}"
            )
            return True

        except Exception as e:
            logger.error(f"❌ Error deleting jurisdiction amendment: {e}")
            session.rollback()
            return False
        finally:
            session.close()

    async def get_amendment_statistics(self) -> Dict[str, Any]:
        """Get statistics about jurisdiction amendments"""
        try:
            session = self.SessionLocal()

            total_amendments = session.query(JurisdictionAmendmentDB).count()
            active_amendments = (
                session.query(JurisdictionAmendmentDB)
                .filter(JurisdictionAmendmentDB.is_active == True)
                .count()
            )

            # Count by jurisdiction
            jurisdictions = {}
            for jurisdiction in self.jurisdictions.keys():
                count = (
                    session.query(JurisdictionAmendmentDB)
                    .filter(
                        JurisdictionAmendmentDB.jurisdiction == jurisdiction,
                        JurisdictionAmendmentDB.is_active == True,
                    )
                    .count()
                )
                jurisdictions[jurisdiction] = count

            # Count by amendment type
            amendment_types = {}
            types = (
                session.query(JurisdictionAmendmentDB.amendment_type).distinct().all()
            )
            for amendment_type in types:
                count = (
                    session.query(JurisdictionAmendmentDB)
                    .filter(
                        JurisdictionAmendmentDB.amendment_type == amendment_type[0],
                        JurisdictionAmendmentDB.is_active == True,
                    )
                    .count()
                )
                amendment_types[amendment_type[0]] = count

            return {
                "total_amendments": total_amendments,
                "active_amendments": active_amendments,
                "jurisdictions": jurisdictions,
                "amendment_types": amendment_types,
            }

        except Exception as e:
            logger.error(f"❌ Error getting amendment statistics: {e}")
            return {}
        finally:
            session.close()

    async def check_jurisdiction_compliance(
        self, jurisdiction: str, code_standard: str, section_number: str
    ) -> Dict[str, Any]:
        """Check if a jurisdiction has specific amendments for a code section"""
        try:
            session = self.SessionLocal()

            amendments = (
                session.query(JurisdictionAmendmentDB)
                .filter(
                    JurisdictionAmendmentDB.jurisdiction == jurisdiction,
                    JurisdictionAmendmentDB.code_standard == code_standard,
                    JurisdictionAmendmentDB.section_number == section_number,
                    JurisdictionAmendmentDB.is_active == True,
                )
                .all()
            )

            compliance_info = {
                "jurisdiction": jurisdiction,
                "code_standard": code_standard,
                "section_number": section_number,
                "has_amendments": len(amendments) > 0,
                "amendments": [],
            }

            for amendment in amendments:
                compliance_info["amendments"].append(
                    {
                        "amendment_type": amendment.amendment_type,
                        "amended_content": amendment.amended_content,
                        "effective_date": amendment.effective_date.isoformat(),
                        "reason": getattr(amendment, "reason", None),
                    }
                )

            return compliance_info

        except Exception as e:
            logger.error(f"❌ Error checking jurisdiction compliance: {e}")
            return {}
        finally:
            session.close()
