"""
Extended User Management for Governance Board Assignment
Extends moderation tools with governance board management capabilities
"""

import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, asdict
import json
import logging

from services.governance.models.board_roles
    governance_board, 
    BoardMember, 
    RoleType, 
    PermissionType
)

logger = logging.getLogger(__name__)


class UserRole(Enum):
    """Extended user roles including governance roles"""
    # Basic roles
    USER = "user"
    MODERATOR = "moderator"
    ADMIN = "admin"
    
    # Governance roles
    BOARD_CHAIR = "board_chair"
    BOARD_VICE_CHAIR = "board_vice_chair"
    BOARD_TREASURER = "board_treasurer"
    BOARD_SECRETARY = "board_secretary"
    BOARD_TECHNICAL_REVIEWER = "board_technical_reviewer"
    BOARD_FINANCIAL_REVIEWER = "board_financial_reviewer"
    BOARD_COMMUNITY_REPRESENTATIVE = "board_community_representative"
    BOARD_LEGAL_ADVISOR = "board_legal_advisor"
    BOARD_SUSTAINABILITY_EXPERT = "board_sustainability_expert"
    BOARD_MEMBER = "board_member"


@dataclass
class UserProfile:
    """Extended user profile with governance capabilities"""
    id: str
    username: str
    email: str
    display_name: str
    roles: Set[str]
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime]
    
    # Governance fields
    governance_roles: Set[str]
    board_member_id: Optional[str]
    governance_permissions: Set[str]
    participation_score: float
    reputation_score: float
    skills: List[str]
    experience_years: int
    bio: str
    contact_info: Dict
    
    def __post_init__(self):
        if self.governance_roles is None:
            self.governance_roles = set()
        if self.governance_permissions is None:
            self.governance_permissions = set()
        if self.skills is None:
            self.skills = []
        if self.contact_info is None:
            self.contact_info = {}


class GovernanceUserManager:
    """Manages user roles and governance board assignments"""
    
    def __init__(self):
        self.users: Dict[str, UserProfile] = {}
        self.role_assignments: Dict[str, List[str]] = {}
        self.participation_logs: Dict[str, List[Dict]] = {}
        self.logger = logging.getLogger(__name__)
    
    def create_user_profile(
        self,
        username: str,
        email: str,
        display_name: str,
        skills: List[str] = None,
        experience_years: int = 0,
        bio: str = "",
        contact_info: Dict = None
    ) -> UserProfile:
        """Create a new user profile with governance capabilities"""
        
        user_id = str(uuid.uuid4())
        created_at = datetime.utcnow()
        
        user = UserProfile(
            id=user_id,
            username=username,
            email=email,
            display_name=display_name,
            roles={UserRole.USER.value},
            is_active=True,
            created_at=created_at,
            last_login=None,
            governance_roles=set(),
            board_member_id=None,
            governance_permissions=set(),
            participation_score=0.0,
            reputation_score=0.0,
            skills=skills or [],
            experience_years=experience_years,
            bio=bio,
            contact_info=contact_info or {}
        )
        
        self.users[user_id] = user
        self.role_assignments[user_id] = []
        self.participation_logs[user_id] = []
        
        self.logger.info(f"Created user profile for {username}")
        return user
    
    def assign_governance_role(
        self,
        user_id: str,
        role_type: RoleType,
        assigned_by: str,
        reason: str = ""
    ) -> Optional[BoardMember]:
        """Assign a governance board role to a user"""
        
        if user_id not in self.users:
            raise ValueError(f"User {user_id} not found")
        
        user = self.users[user_id]
        
        # Check if assigner has permission
        if not governance_board.has_permission(assigned_by, PermissionType.ASSIGN_BOARD_ROLES):
            raise ValueError(f"User {assigned_by} does not have permission to assign board roles")
        
        # Check if user already has a board role
        if user.board_member_id:
            raise ValueError(f"User {user_id} already has a board role")
        
        # Validate role requirements
        role_perm = governance_board.role_permissions[role_type]
        
        # Check experience requirements
        if user.experience_years < role_perm.required_experience_years:
            raise ValueError(f"User does not meet experience requirement for {role_type.value}")
        
        # Check skills requirements
        user_skills = set(user.skills)
        required_skills = set(role_perm.required_skills)
        if not required_skills.issubset(user_skills):
            missing_skills = required_skills - user_skills
            raise ValueError(f"User missing required skills: {missing_skills}")
        
        # Create board member
        board_member = governance_board.add_board_member(
            user_id=user_id,
            role_type=role_type,
            display_name=user.display_name,
            email=user.email,
            skills=user.skills,
            bio=user.bio,
            contact_info=user.contact_info
        )
        
        # Update user profile
        user.governance_roles.add(role_type.value)
        user.board_member_id = board_member.id
        user.governance_permissions.update(role_perm.permissions)
        user.roles.add(UserRole.BOARD_MEMBER.value)
        
        # Log assignment
        self._log_participation(user_id, "role_assignment", {
            "role": role_type.value,
            "assigned_by": assigned_by,
            "reason": reason,
            "board_member_id": board_member.id
        })
        
        self.logger.info(f"Assigned governance role {role_type.value} to user {user_id}")
        return board_member
    
    def remove_governance_role(
        self,
        user_id: str,
        removed_by: str,
        reason: str = ""
    ) -> bool:
        """Remove a governance board role from a user"""
        
        if user_id not in self.users:
            raise ValueError(f"User {user_id} not found")
        
        user = self.users[user_id]
        
        if not user.board_member_id:
            raise ValueError(f"User {user_id} does not have a board role")
        
        # Check if remover has permission
        if not governance_board.has_permission(removed_by, PermissionType.REMOVE_BOARD_ROLES):
            raise ValueError(f"User {removed_by} does not have permission to remove board roles")
        
        # Remove from governance board
        governance_board.remove_board_member(user.board_member_id, reason)
        
        # Update user profile
        user.governance_roles.clear()
        user.board_member_id = None
        user.governance_permissions.clear()
        user.roles.discard(UserRole.BOARD_MEMBER.value)
        
        # Log removal
        self._log_participation(user_id, "role_removal", {
            "removed_by": removed_by,
            "reason": reason,
            "previous_board_member_id": user.board_member_id
        })
        
        self.logger.info(f"Removed governance role from user {user_id}")
        return True
    
    def suspend_user(
        self,
        user_id: str,
        suspended_by: str,
        duration_days: int,
        reason: str
    ) -> bool:
        """Suspend a user temporarily"""
        
        if user_id not in self.users:
            raise ValueError(f"User {user_id} not found")
        
        user = self.users[user_id]
        
        if not user.board_member_id:
            raise ValueError(f"User {user_id} does not have a board role to suspend")
        
        # Check if suspender has permission
        if not governance_board.has_permission(suspended_by, PermissionType.SUSPEND_BOARD_MEMBER):
            raise ValueError(f"User {suspended_by} does not have permission to suspend board members")
        
        # Suspend in governance board
        governance_board.suspend_board_member(user.board_member_id, duration_days, reason)
        
        # Update user profile
        user.is_active = False
        
        # Log suspension
        self._log_participation(user_id, "suspension", {
            "suspended_by": suspended_by,
            "duration_days": duration_days,
            "reason": reason
        })
        
        self.logger.info(f"Suspended user {user_id} for {duration_days} days")
        return True
    
    def update_participation_score(self, user_id: str, score: float):
        """Update user participation score"""
        
        if user_id not in self.users:
            raise ValueError(f"User {user_id} not found")
        
        user = self.users[user_id]
        user.participation_score = max(0.0, min(1.0, score))
        
        # Update governance board if user is a board member
        if user.board_member_id:
            governance_board.update_participation_score(user.board_member_id, score)
    
    def update_reputation_score(self, user_id: str, score: float):
        """Update user reputation score"""
        
        if user_id not in self.users:
            raise ValueError(f"User {user_id} not found")
        
        user = self.users[user_id]
        user.reputation_score = max(0.0, min(10.0, score))
        
        # Update governance board if user is a board member
        if user.board_member_id:
            governance_board.update_reputation_score(user.board_member_id, score)
    
    def get_governance_candidates(self, role_type: RoleType) -> List[UserProfile]:
        """Get users eligible for a specific governance role"""
        
        role_perm = governance_board.role_permissions[role_type]
        candidates = []
        
        for user in self.users.values():
            if not user.is_active or user.board_member_id:
                continue
            
            # Check experience requirement
            if user.experience_years < role_perm.required_experience_years:
                continue
            
            # Check skills requirement
            user_skills = set(user.skills)
            required_skills = set(role_perm.required_skills)
            if not required_skills.issubset(user_skills):
                continue
            
            # Calculate eligibility score
            skill_match = len(user_skills.intersection(required_skills)) / len(required_skills)
            experience_bonus = min(1.0, user.experience_years / role_perm.required_experience_years)
            participation_bonus = user.participation_score
            reputation_bonus = user.reputation_score / 10.0
            
            eligibility_score = (skill_match * 0.4 + experience_bonus * 0.3 + 
                               participation_bonus * 0.2 + reputation_bonus * 0.1)
            
            candidates.append({
                "user": user,
                "eligibility_score": eligibility_score,
                "skill_match": skill_match,
                "experience_bonus": experience_bonus,
                "participation_bonus": participation_bonus,
                "reputation_bonus": reputation_bonus
            })
        
        # Sort by eligibility score
        candidates.sort(key=lambda x: x["eligibility_score"], reverse=True)
        return candidates
    
    def get_governance_summary(self) -> Dict:
        """Get comprehensive governance user summary"""
        
        total_users = len(self.users)
        governance_users = [u for u in self.users.values() if u.board_member_id]
        
        role_distribution = {}
        for role_type in RoleType:
            role_distribution[role_type.value] = len([
                u for u in governance_users 
                if role_type.value in u.governance_roles
            ])
        
        avg_participation = sum(u.participation_score for u in governance_users) / len(governance_users) if governance_users else 0
        avg_reputation = sum(u.reputation_score for u in governance_users) / len(governance_users) if governance_users else 0
        
        return {
            "total_users": total_users,
            "governance_users": len(governance_users),
            "role_distribution": role_distribution,
            "average_participation": avg_participation,
            "average_reputation": avg_reputation,
            "active_board_members": len([u for u in governance_users if u.is_active]),
            "suspended_board_members": len([u for u in governance_users if not u.is_active])
        }
    
    def get_user_governance_profile(self, user_id: str) -> Dict:
        """Get detailed governance profile for a user"""
        
        if user_id not in self.users:
            raise ValueError(f"User {user_id} not found")
        
        user = self.users[user_id]
        
        profile = {
            "id": user.id,
            "username": user.username,
            "display_name": user.display_name,
            "email": user.email,
            "roles": list(user.roles),
            "governance_roles": list(user.governance_roles),
            "governance_permissions": list(user.governance_permissions),
            "is_active": user.is_active,
            "participation_score": user.participation_score,
            "reputation_score": user.reputation_score,
            "skills": user.skills,
            "experience_years": user.experience_years,
            "bio": user.bio,
            "contact_info": user.contact_info,
            "created_at": user.created_at.isoformat(),
            "last_login": user.last_login.isoformat() if user.last_login else None
        }
        
        # Add board member info if applicable
        if user.board_member_id:
            board_member = governance_board.members.get(user.board_member_id)
            if board_member:
                profile["board_member"] = {
                    "id": board_member.id,
                    "role_type": board_member.role_type.value,
                    "appointed_date": board_member.appointed_date.isoformat(),
                    "term_end_date": board_member.term_end_date.isoformat(),
                    "voting_weight": board_member.voting_weight,
                    "decisions_made": board_member.decisions_made,
                    "decisions_correct": board_member.decisions_correct
                }
        
        # Add participation history
        profile["participation_history"] = self.participation_logs.get(user_id, [])
        
        return profile
    
    def _log_participation(self, user_id: str, action: str, details: Dict):
        """Log user participation activity"""
        
        if user_id not in self.participation_logs:
            self.participation_logs[user_id] = []
        
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "action": action,
            "details": details
        }
        
        self.participation_logs[user_id].append(log_entry)
    
    def search_users(self, query: str, role_filter: Optional[str] = None) -> List[UserProfile]:
        """Search users with optional role filtering"""
        
        results = []
        query_lower = query.lower()
        
        for user in self.users.values():
            # Check if user matches query
            if (query_lower in user.username.lower() or 
                query_lower in user.display_name.lower() or
                query_lower in user.email.lower()):
                
                # Apply role filter if specified
                if role_filter:
                    if role_filter not in user.roles and role_filter not in user.governance_roles:
                        continue
                
                results.append(user)
        
        return results


# Global governance user manager instance
governance_user_manager = GovernanceUserManager() 