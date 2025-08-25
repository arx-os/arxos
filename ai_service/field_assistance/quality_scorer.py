"""
Quality Scorer - Assess field worker contributions for BILT token rewards
Lightweight scoring system to encourage quality contributions
"""

import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class QualityScore:
    """Quality score for field worker contribution"""
    overall_score: float  # 0.0 to 1.0
    token_reward: int     # BILT tokens earned
    breakdown: Dict[str, float]  # Individual category scores
    feedback: List[str]   # Suggestions for improvement
    timestamp: datetime

class QualityScorer:
    """
    Lightweight quality scoring system for field worker contributions
    Determines BILT token rewards based on contribution quality
    """
    
    def __init__(self):
        # Scoring weights for different quality factors
        self.scoring_weights = {
            'completeness': 0.25,      # How complete is the information
            'accuracy': 0.30,          # How accurate is the data
            'detail': 0.20,            # Level of detail provided
            'location': 0.15,          # Quality of location data
            'photos': 0.10             # Photo documentation quality
        }
        
        # Token reward tiers
        self.token_tiers = {
            0.9: 10,   # Excellent: 10 BILT tokens
            0.8: 8,    # Very Good: 8 BILT tokens
            0.7: 6,    # Good: 6 BILT tokens
            0.6: 4,    # Fair: 4 BILT tokens
            0.5: 2,    # Poor: 2 BILT tokens
            0.0: 0     # Unacceptable: 0 tokens
        }
    
    async def score_contribution(self, 
                                contribution_data: Dict[str, Any],
                                validation_result: Optional[Dict[str, Any]] = None) -> QualityScore:
        """
        Score a field worker contribution for quality
        
        Args:
            contribution_data: The contribution data from field worker
            validation_result: Optional validation result from component validator
            
        Returns:
            QualityScore with overall score and token reward
        """
        try:
            # Calculate individual category scores
            completeness_score = self._score_completeness(contribution_data)
            accuracy_score = self._score_accuracy(contribution_data, validation_result)
            detail_score = self._score_detail(contribution_data)
            location_score = self._score_location(contribution_data)
            photo_score = self._score_photos(contribution_data)
            
            # Calculate weighted overall score
            breakdown = {
                'completeness': completeness_score,
                'accuracy': accuracy_score,
                'detail': detail_score,
                'location': location_score,
                'photos': photo_score
            }
            
            overall_score = sum(
                breakdown[category] * weight 
                for category, weight in self.scoring_weights.items()
            )
            
            # Determine token reward
            token_reward = self._calculate_token_reward(overall_score)
            
            # Generate feedback
            feedback = self._generate_feedback(breakdown, overall_score)
            
            return QualityScore(
                overall_score=overall_score,
                token_reward=token_reward,
                breakdown=breakdown,
                feedback=feedback,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Quality scoring error: {e}")
            return QualityScore(
                overall_score=0.0,
                token_reward=0,
                breakdown={},
                feedback=[f"Scoring failed: {str(e)}"],
                timestamp=datetime.now()
            )
    
    def _score_completeness(self, contribution_data: Dict[str, Any]) -> float:
        """Score the completeness of the contribution"""
        score = 0.0
        required_fields = ['type', 'name', 'location']
        optional_fields = ['properties', 'description', 'notes', 'photos']
        
        # Check required fields
        for field in required_fields:
            if field in contribution_data and contribution_data[field]:
                score += 0.3
            else:
                score += 0.0
        
        # Check optional fields
        for field in optional_fields:
            if field in contribution_data and contribution_data[field]:
                score += 0.1
        
        return min(score, 1.0)
    
    def _score_accuracy(self, 
                        contribution_data: Dict[str, Any], 
                        validation_result: Optional[Dict[str, Any]]) -> float:
        """Score the accuracy of the contribution"""
        if not validation_result:
            return 0.5  # Default score if no validation
        
        # Use validation confidence as accuracy score
        confidence = validation_result.get('confidence', 0.5)
        
        # Bonus for passing validation
        if validation_result.get('is_valid', False):
            confidence += 0.2
        
        # Penalty for validation errors
        errors = validation_result.get('errors', [])
        if errors:
            confidence -= len(errors) * 0.1
        
        return max(0.0, min(confidence, 1.0))
    
    def _score_detail(self, contribution_data: Dict[str, Any]) -> float:
        """Score the level of detail provided"""
        score = 0.0
        
        # Basic component type
        if 'type' in contribution_data:
            score += 0.2
        
        # Properties detail
        properties = contribution_data.get('properties', {})
        if properties:
            score += min(len(properties) * 0.1, 0.3)
        
        # Description quality
        description = contribution_data.get('description', '')
        if description:
            score += min(len(description) / 100.0, 0.2)
        
        # Notes and additional info
        notes = contribution_data.get('notes', '')
        if notes:
            score += min(len(notes) / 50.0, 0.1)
        
        # Manufacturer/model info
        if 'manufacturer' in contribution_data or 'model' in contribution_data:
            score += 0.1
        
        # Serial number or identification
        if 'serial_number' in contribution_data or 'id' in contribution_data:
            score += 0.1
        
        return min(score, 1.0)
    
    def _score_location(self, contribution_data: Dict[str, Any]) -> float:
        """Score the quality of location data"""
        score = 0.0
        location = contribution_data.get('location', {})
        
        if not location:
            return 0.0
        
        # Room information
        if 'room' in location and location['room']:
            score += 0.3
        
        # Floor information
        if 'floor' in location and location['floor']:
            score += 0.2
        
        # Building section/area
        if 'section' in location or 'area' in location:
            score += 0.2
        
        # Specific coordinates or position
        if 'coordinates' in location or 'position' in location:
            score += 0.2
        
        # Relative position (near, behind, etc.)
        if 'relative_position' in location:
            score += 0.1
        
        return min(score, 1.0)
    
    def _score_photos(self, contribution_data: Dict[str, Any]) -> float:
        """Score the quality of photo documentation"""
        score = 0.0
        photos = contribution_data.get('photos', [])
        
        if not photos:
            return 0.0
        
        # Number of photos
        if len(photos) >= 3:
            score += 0.4
        elif len(photos) >= 2:
            score += 0.3
        elif len(photos) >= 1:
            score += 0.2
        
        # Photo quality indicators (if available)
        for photo in photos:
            if isinstance(photo, dict):
                # Check for photo metadata
                if 'size' in photo and photo['size'] > 1000000:  # >1MB
                    score += 0.1
                if 'resolution' in photo:
                    width, height = photo['resolution']
                    if width > 1920 and height > 1080:  # HD+
                        score += 0.1
        
        return min(score, 1.0)
    
    def _calculate_token_reward(self, overall_score: float) -> int:
        """Calculate BILT token reward based on overall score"""
        for threshold, tokens in sorted(self.token_tiers.items(), reverse=True):
            if overall_score >= threshold:
                return tokens
        
        return 0
    
    def _generate_feedback(self, breakdown: Dict[str, float], overall_score: float) -> List[str]:
        """Generate feedback for improvement"""
        feedback = []
        
        # Overall feedback
        if overall_score >= 0.9:
            feedback.append("Excellent contribution! Keep up the great work.")
        elif overall_score >= 0.8:
            feedback.append("Very good contribution. Consider adding more details.")
        elif overall_score >= 0.7:
            feedback.append("Good contribution. A few improvements could earn more tokens.")
        elif overall_score >= 0.6:
            feedback.append("Fair contribution. Several areas need improvement.")
        else:
            feedback.append("Poor contribution. Significant improvements needed.")
        
        # Specific feedback for low-scoring categories
        for category, score in breakdown.items():
            if score < 0.5:
                if category == 'completeness':
                    feedback.append("Add missing required information (type, name, location).")
                elif category == 'accuracy':
                    feedback.append("Verify the information provided is correct.")
                elif category == 'detail':
                    feedback.append("Include more properties and descriptions.")
                elif category == 'location':
                    feedback.append("Provide more specific location information.")
                elif category == 'photos':
                    feedback.append("Add clear photos of the component.")
        
        # Positive feedback for high-scoring categories
        for category, score in breakdown.items():
            if score >= 0.8:
                if category == 'completeness':
                    feedback.append("Great job providing complete information!")
                elif category == 'accuracy':
                    feedback.append("Excellent accuracy in your contribution!")
                elif category == 'detail':
                    feedback.append("Wonderful level of detail provided!")
                elif category == 'location':
                    feedback.append("Excellent location documentation!")
                elif category == 'photos':
                    feedback.append("Great photo documentation!")
        
        return feedback
