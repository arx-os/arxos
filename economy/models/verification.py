"""
Verification Models for BILT Economy

Defines the data models for contribution verification and quality assessment.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class Verification(BaseModel):
    """Model for a contribution verification"""

    contribution_id: str = Field(..., description="Contribution being verified")
    verifier_id: str = Field(..., description="User performing verification")
    approved: bool = Field(..., description="Approval decision")
    feedback: Optional[str] = Field(None, description="Verification feedback")
    quality_score: Optional[float] = Field(
        None, description="Quality assessment (0-10)"
    )
    complexity_score: Optional[float] = Field(
        None, description="Complexity assessment (0-10)"
    )
    verified_at: datetime = Field(..., description="Verification timestamp")

    # Verification criteria
    accuracy_score: Optional[float] = Field(
        None, description="Accuracy assessment (0-10)"
    )
    completeness_score: Optional[float] = Field(
        None, description="Completeness assessment (0-10)"
    )
    innovation_score: Optional[float] = Field(
        None, description="Innovation assessment (0-10)"
    )
    usability_score: Optional[float] = Field(
        None, description="Usability assessment (0-10)"
    )

    # Metadata
    verification_time_seconds: Optional[float] = Field(
        None, description="Time spent verifying"
    )
    verification_method: Optional[str] = Field(
        None, description="Method used for verification"
    )

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class VerificationCriteria(BaseModel):
    """Criteria for verifying contributions"""

    # Quality criteria
    accuracy_threshold: float = Field(default=7.0, description="Minimum accuracy score")
    completeness_threshold: float = Field(
        default=7.0, description="Minimum completeness score"
    )
    innovation_threshold: float = Field(
        default=5.0, description="Minimum innovation score"
    )
    usability_threshold: float = Field(
        default=6.0, description="Minimum usability score"
    )

    # Complexity criteria
    complexity_weight: float = Field(
        default=0.3, description="Weight for complexity in scoring"
    )
    quality_weight: float = Field(
        default=0.7, description="Weight for quality in scoring"
    )

    # Verification requirements
    min_verifications: int = Field(
        default=1, description="Minimum verifications required"
    )
    max_verifications: int = Field(
        default=3, description="Maximum verifications allowed"
    )
    verification_timeout_hours: int = Field(
        default=168, description="Verification timeout in hours"
    )


class VerificationSummary(BaseModel):
    """Summary of verification results"""

    contribution_id: str = Field(..., description="Contribution ID")
    total_verifications: int = Field(..., description="Total number of verifications")
    approval_count: int = Field(..., description="Number of approvals")
    rejection_count: int = Field(..., description="Number of rejections")

    # Average scores
    average_quality_score: Optional[float] = Field(
        None, description="Average quality score"
    )
    average_complexity_score: Optional[float] = Field(
        None, description="Average complexity score"
    )
    average_accuracy_score: Optional[float] = Field(
        None, description="Average accuracy score"
    )
    average_completeness_score: Optional[float] = Field(
        None, description="Average completeness score"
    )
    average_innovation_score: Optional[float] = Field(
        None, description="Average innovation score"
    )
    average_usability_score: Optional[float] = Field(
        None, description="Average usability score"
    )

    # Final decision
    final_decision: str = Field(..., description="Final decision (approved/rejected)")
    decision_reason: Optional[str] = Field(
        None, description="Reason for final decision"
    )

    # Timing
    first_verification_time: Optional[datetime] = Field(
        None, description="First verification timestamp"
    )
    last_verification_time: Optional[datetime] = Field(
        None, description="Last verification timestamp"
    )
    average_verification_time: Optional[float] = Field(
        None, description="Average verification time in seconds"
    )


class VerifierProfile(BaseModel):
    """Profile of a verifier"""

    verifier_id: str = Field(..., description="Verifier user ID")
    total_verifications: int = Field(..., description="Total verifications performed")
    approved_verifications: int = Field(
        ..., description="Verifications that led to approval"
    )
    rejected_verifications: int = Field(
        ..., description="Verifications that led to rejection"
    )

    # Quality metrics
    average_verification_time: float = Field(
        ..., description="Average time per verification"
    )
    verification_accuracy: float = Field(
        ..., description="Accuracy of verification decisions"
    )

    # Reputation
    reputation_score: float = Field(..., description="Verifier reputation score")
    trust_level: str = Field(..., description="Trust level (novice/expert/master)")

    # Specializations
    preferred_contribution_types: list[str] = Field(
        default_factory=list, description="Preferred contribution types"
    )
    expertise_areas: list[str] = Field(
        default_factory=list, description="Areas of expertise"
    )

    # Activity
    last_verification_time: Optional[datetime] = Field(
        None, description="Last verification timestamp"
    )
    verification_streak_days: int = Field(
        default=0, description="Current verification streak"
    )
    total_verification_time_hours: float = Field(
        default=0.0, description="Total time spent verifying"
    )


class VerificationRequest(BaseModel):
    """Request for verification"""

    contribution_id: str = Field(..., description="Contribution to verify")
    verifier_id: str = Field(..., description="User performing verification")
    approved: bool = Field(..., description="Approval decision")
    feedback: Optional[str] = Field(None, description="Verification feedback")

    # Scoring
    quality_score: Optional[float] = Field(
        None, description="Quality assessment (0-10)"
    )
    complexity_score: Optional[float] = Field(
        None, description="Complexity assessment (0-10)"
    )
    accuracy_score: Optional[float] = Field(
        None, description="Accuracy assessment (0-10)"
    )
    completeness_score: Optional[float] = Field(
        None, description="Completeness assessment (0-10)"
    )
    innovation_score: Optional[float] = Field(
        None, description="Innovation assessment (0-10)"
    )
    usability_score: Optional[float] = Field(
        None, description="Usability assessment (0-10)"
    )

    # Metadata
    verification_time_seconds: Optional[float] = Field(
        None, description="Time spent verifying"
    )
    verification_method: Optional[str] = Field(
        None, description="Method used for verification"
    )


class VerificationResponse(BaseModel):
    """Response for verification operation"""

    success: bool = Field(..., description="Operation success")
    verification: Optional[Verification] = Field(None, description="Verification data")
    contribution_approved: bool = Field(
        ..., description="Whether contribution was approved"
    )
    bilt_minted: Optional[int] = Field(None, description="BILT tokens minted")
    message: str = Field(..., description="Response message")

    # Updated statistics
    total_verifications: int = Field(
        ..., description="Total verifications for contribution"
    )
    approval_count: int = Field(..., description="Approval count for contribution")
    rejection_count: int = Field(..., description="Rejection count for contribution")
