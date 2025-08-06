"""
Contribution Models for BILT Economy

Defines the data models for contributions, verification, and BILT minting.
"""

from datetime import datetime
from enum import Enum
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field


class ContributionLevel(str, Enum):
    """Levels of contribution complexity"""

    BARE_MINIMUM = "bare_minimum"  # 1 BILT - Basic labeling
    BASIC = "basic"  # 5 BILT - Simple layouts
    STANDARD = "standard"  # 15 BILT - Complete systems
    ADVANCED = "advanced"  # 50 BILT - Complex models
    EXPERT = "expert"  # 100 BILT - Innovative solutions


class ContributionStatus(str, Enum):
    """Status of a contribution"""

    PENDING_VERIFICATION = "pending_verification"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"


class ContributionType(str, Enum):
    """Types of contributions"""

    # Basic CAD contributions
    LABEL_ANNOTATION = "label_annotation"
    DIMENSION_ANNOTATION = "dimension_annotation"
    TEXT_ANNOTATION = "text_annotation"

    # Drawing contributions
    ROOM_LAYOUT = "room_layout"
    FLOOR_PLAN = "floor_plan"
    ELECTRICAL_PLAN = "electrical_plan"
    MECHANICAL_PLAN = "mechanical_plan"
    PLUMBING_PLAN = "plumbing_plan"

    # System contributions
    ELECTRICAL_SYSTEM = "electrical_system"
    HVAC_SYSTEM = "hvac_system"
    PLUMBING_SYSTEM = "plumbing_system"
    FIRE_PROTECTION_SYSTEM = "fire_protection_system"

    # Advanced contributions
    COMPLETE_BUILDING_MODEL = "complete_building_model"
    PARAMETRIC_MODEL = "parametric_model"
    CONSTRAINT_SOLUTION = "constraint_solution"
    INNOVATIVE_DESIGN = "innovative_design"

    # Infrastructure as Code
    BIM_COMPONENT = "bim_component"
    SVGX_ELEMENT = "svgx_element"
    XML_STRUCTURE = "xml_structure"
    DIGITAL_TWIN = "digital_twin"


class Contribution(BaseModel):
    """Model for a BILT contribution"""

    id: str = Field(..., description="Unique contribution ID")
    user_id: str = Field(..., description="User who made the contribution")
    type: ContributionType = Field(..., description="Type of contribution")
    data: Dict[str, Any] = Field(
        ..., description="Contribution data (SVGX, metadata, etc.)"
    )
    level: ContributionLevel = Field(..., description="Contribution complexity level")
    status: ContributionStatus = Field(..., description="Current status")
    bilt_amount: int = Field(..., description="BILT tokens to be minted")
    created_at: datetime = Field(..., description="Creation timestamp")
    verified_at: Optional[datetime] = Field(None, description="Verification timestamp")
    minted_at: Optional[datetime] = Field(None, description="Minting timestamp")

    # Metadata
    title: Optional[str] = Field(None, description="Contribution title")
    description: Optional[str] = Field(None, description="Contribution description")
    tags: list[str] = Field(default_factory=list, description="Contribution tags")

    # Quality metrics
    quality_score: Optional[float] = Field(None, description="Quality assessment score")
    complexity_score: Optional[float] = Field(
        None, description="Complexity assessment score"
    )

    # Verification data
    verification_count: int = Field(default=0, description="Number of verifications")
    approval_count: int = Field(default=0, description="Number of approvals")
    rejection_count: int = Field(default=0, description="Number of rejections")

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class ContributionRequest(BaseModel):
    """Request model for creating a contribution"""

    type: ContributionType = Field(..., description="Type of contribution")
    data: Dict[str, Any] = Field(..., description="Contribution data")
    level: ContributionLevel = Field(..., description="Contribution level")
    title: Optional[str] = Field(None, description="Contribution title")
    description: Optional[str] = Field(None, description="Contribution description")
    tags: list[str] = Field(default_factory=list, description="Contribution tags")


class ContributionResponse(BaseModel):
    """Response model for contribution operations"""

    success: bool = Field(..., description="Operation success")
    contribution: Optional[Contribution] = Field(None, description="Contribution data")
    message: str = Field(..., description="Response message")
    bilt_minted: Optional[int] = Field(None, description="BILT tokens minted")


class VerificationRequest(BaseModel):
    """Request model for verifying a contribution"""

    contribution_id: str = Field(..., description="Contribution to verify")
    approved: bool = Field(..., description="Approval decision")
    feedback: Optional[str] = Field(None, description="Verification feedback")
    quality_score: Optional[float] = Field(None, description="Quality assessment")
    complexity_score: Optional[float] = Field(None, description="Complexity assessment")


class VerificationResponse(BaseModel):
    """Response model for verification operations"""

    success: bool = Field(..., description="Operation success")
    contribution_approved: bool = Field(
        ..., description="Whether contribution was approved"
    )
    bilt_minted: Optional[int] = Field(None, description="BILT tokens minted")
    message: str = Field(..., description="Response message")


class ContributionStatistics(BaseModel):
    """Statistics for contributions"""

    total_contributions: int = Field(..., description="Total contributions")
    approved_contributions: int = Field(..., description="Approved contributions")
    pending_contributions: int = Field(..., description="Pending contributions")
    rejected_contributions: int = Field(..., description="Rejected contributions")
    total_bilt_minted: int = Field(..., description="Total BILT minted")
    approval_rate: float = Field(..., description="Approval rate percentage")

    # Level breakdown
    bare_minimum_count: int = Field(..., description="Bare minimum contributions")
    basic_count: int = Field(..., description="Basic contributions")
    standard_count: int = Field(..., description="Standard contributions")
    advanced_count: int = Field(..., description="Advanced contributions")
    expert_count: int = Field(..., description="Expert contributions")

    # Type breakdown
    type_breakdown: Dict[str, int] = Field(..., description="Contributions by type")

    # Time-based metrics
    contributions_this_week: int = Field(..., description="Contributions this week")
    contributions_this_month: int = Field(..., description="Contributions this month")
    average_verification_time: Optional[float] = Field(
        None, description="Average verification time in hours"
    )
