package domain

import (
	"time"

	"github.com/arx-os/arxos/internal/domain/types"
)

// Contributor management domain entities
// Multi-user access control, teams, and permissions

// ContributorRole represents a user's role in a repository
type ContributorRole string

const (
	ContributorRoleOwner       ContributorRole = "owner"
	ContributorRoleAdmin       ContributorRole = "admin"
	ContributorRoleMaintainer  ContributorRole = "maintainer"
	ContributorRoleContributor ContributorRole = "contributor"
	ContributorRoleReporter    ContributorRole = "reporter"
	ContributorRoleReader      ContributorRole = "reader"
)

// ContributorStatus represents contributor status
type ContributorStatus string

const (
	ContributorStatusActive    ContributorStatus = "active"
	ContributorStatusInactive  ContributorStatus = "inactive"
	ContributorStatusSuspended ContributorStatus = "suspended"
)

// Contributor represents a user with access to a repository
type Contributor struct {
	ID           types.ID `json:"id"`
	RepositoryID types.ID `json:"repository_id"`
	UserID       types.ID `json:"user_id"`

	// Role and permissions
	Role ContributorRole `json:"role"`

	// Granular permissions
	CanRead               bool `json:"can_read"`
	CanWrite              bool `json:"can_write"`
	CanCreateBranch       bool `json:"can_create_branch"`
	CanCreatePR           bool `json:"can_create_pr"`
	CanMergePR            bool `json:"can_merge_pr"`
	CanApprovePR          bool `json:"can_approve_pr"`
	CanDeleteBranch       bool `json:"can_delete_branch"`
	CanManageIssues       bool `json:"can_manage_issues"`
	CanAssignIssues       bool `json:"can_assign_issues"`
	CanManageContributors bool `json:"can_manage_contributors"`
	CanManageSettings     bool `json:"can_manage_settings"`

	// Access scope
	ScopeAllBuildings bool       `json:"scope_all_buildings"`
	ScopeBuildingIDs  []types.ID `json:"scope_building_ids,omitempty"`
	ScopeFloorIDs     []types.ID `json:"scope_floor_ids,omitempty"`
	ScopeRoomTypes    []string   `json:"scope_room_types,omitempty"`
	ScopeEquipmentTypes []string `json:"scope_equipment_types,omitempty"`

	// Invitation
	InvitedBy  *types.ID  `json:"invited_by,omitempty"`
	InvitedAt  *time.Time `json:"invited_at,omitempty"`
	AcceptedAt *time.Time `json:"accepted_at,omitempty"`

	Status ContributorStatus `json:"status"`
	Notes  string            `json:"notes,omitempty"`

	Metadata map[string]interface{} `json:"metadata,omitempty"`

	CreatedAt time.Time  `json:"created_at"`
	CreatedBy *types.ID `json:"created_by,omitempty"`
	UpdatedAt time.Time  `json:"updated_at"`
}

// TeamType represents the type of team
type TeamType string

const (
	TeamTypeInternal    TeamType = "internal"
	TeamTypeContractor  TeamType = "contractor"
	TeamTypeVendor      TeamType = "vendor"
	TeamTypeFacilities  TeamType = "facilities"
	TeamTypeEngineering TeamType = "engineering"
	TeamTypeCustom      TeamType = "custom"
)

// Team represents a group of users
type Team struct {
	ID             types.ID  `json:"id"`
	RepositoryID   *types.ID `json:"repository_id,omitempty"` // Repository-specific team
	OrganizationID *types.ID `json:"organization_id,omitempty"` // Org-wide team

	Slug        string   `json:"slug"`        // URL-friendly
	Name        string   `json:"name"`        // Display name
	Description string   `json:"description,omitempty"`
	TeamType    TeamType `json:"team_type"`

	DefaultRole ContributorRole `json:"default_role"`
	LeadUserID  *types.ID       `json:"lead_user_id,omitempty"`

	Specializations []string `json:"specializations,omitempty"` // electrical, hvac, plumbing

	Color     string `json:"color,omitempty"`
	AvatarURL string `json:"avatar_url,omitempty"`
	Metadata  map[string]interface{} `json:"metadata,omitempty"`

	CreatedAt time.Time  `json:"created_at"`
	CreatedBy *types.ID `json:"created_by,omitempty"`
	UpdatedAt time.Time  `json:"updated_at"`
}

// TeamRole represents a user's role in a team
type TeamRole string

const (
	TeamRoleLead   TeamRole = "lead"
	TeamRoleAdmin  TeamRole = "admin"
	TeamRoleMember TeamRole = "member"
)

// TeamMemberStatus represents team member status
type TeamMemberStatus string

const (
	TeamMemberStatusActive   TeamMemberStatus = "active"
	TeamMemberStatusInactive TeamMemberStatus = "inactive"
)

// TeamMember represents membership in a team
type TeamMember struct {
	ID       types.ID `json:"id"`
	TeamID   types.ID `json:"team_id"`
	UserID   types.ID `json:"user_id"`
	TeamRole TeamRole `json:"team_role"`
	Status   TeamMemberStatus `json:"status"`

	AddedAt time.Time  `json:"added_at"`
	AddedBy *types.ID `json:"added_by,omitempty"`
}

// AccessRule represents an automated access control rule
type AccessRule struct {
	ID           types.ID `json:"id"`
	RepositoryID types.ID `json:"repository_id"`

	Name        string `json:"name"`
	Description string `json:"description,omitempty"`
	Enabled     bool   `json:"enabled"`
	Priority    int    `json:"priority"` // Higher = evaluated first

	// Conditions
	ConditionUserDomain       string   `json:"condition_user_domain,omitempty"`
	ConditionUserRole         string   `json:"condition_user_role,omitempty"`
	ConditionUserTags         []string `json:"condition_user_tags,omitempty"`
	ConditionEquipmentType    string   `json:"condition_equipment_type,omitempty"`
	ConditionSpecialization   string   `json:"condition_specialization,omitempty"`

	// Actions
	ActionAddToTeam       *types.ID       `json:"action_add_to_team,omitempty"`
	ActionGrantRole       ContributorRole `json:"action_grant_role,omitempty"`
	ActionNotifyAdmin     bool            `json:"action_notify_admin"`
	ActionRequireApproval bool            `json:"action_require_approval"`

	Metadata map[string]interface{} `json:"metadata,omitempty"`

	CreatedAt time.Time  `json:"created_at"`
	CreatedBy *types.ID `json:"created_by,omitempty"`
}

// BranchProtectionRule represents protection rules for branches
type BranchProtectionRule struct {
	ID           types.ID `json:"id"`
	RepositoryID types.ID `json:"repository_id"`
	BranchPattern string  `json:"branch_pattern"` // main, contractor/*, etc.

	// Protection settings
	RequirePR               bool `json:"require_pr"`
	RequireReviews          int  `json:"require_reviews"`
	RequireReviewFromOwners bool `json:"require_review_from_owners"`
	DismissStaleReviews     bool `json:"dismiss_stale_reviews"`
	RequireStatusChecks     bool `json:"require_status_checks"`
	RequireUpToDate         bool `json:"require_up_to_date"`

	// Push/merge restrictions
	AllowForcePush         bool   `json:"allow_force_push"`
	AllowDeletions         bool   `json:"allow_deletions"`
	RestrictPushToAdmins   bool   `json:"restrict_push_to_admins"`

	// Auto-merge
	AllowAutoMerge  bool   `json:"allow_auto_merge"`
	AutoMergeMethod string `json:"auto_merge_method,omitempty"` // merge, squash, rebase

	// Allowed users/teams
	AllowedPushUserIDs  []types.ID `json:"allowed_push_user_ids,omitempty"`
	AllowedPushTeamIDs  []types.ID `json:"allowed_push_team_ids,omitempty"`
	AllowedMergeUserIDs []types.ID `json:"allowed_merge_user_ids,omitempty"`
	AllowedMergeTeamIDs []types.ID `json:"allowed_merge_team_ids,omitempty"`

	CreatedAt time.Time  `json:"created_at"`
	CreatedBy *types.ID `json:"created_by,omitempty"`
	UpdatedAt time.Time  `json:"updated_at"`
}

// AccessAuditAction represents types of access audit actions
type AccessAuditAction string

const (
	AccessAuditContributorAdded   AccessAuditAction = "contributor_added"
	AccessAuditContributorRemoved AccessAuditAction = "contributor_removed"
	AccessAuditRoleChanged        AccessAuditAction = "role_changed"
	AccessAuditPermissionsChanged AccessAuditAction = "permissions_changed"
	AccessAuditTeamCreated        AccessAuditAction = "team_created"
	AccessAuditTeamDeleted        AccessAuditAction = "team_deleted"
	AccessAuditTeamMemberAdded    AccessAuditAction = "team_member_added"
	AccessAuditTeamMemberRemoved  AccessAuditAction = "team_member_removed"
	AccessAuditAccessGranted      AccessAuditAction = "access_granted"
	AccessAuditAccessRevoked      AccessAuditAction = "access_revoked"
	AccessAuditBranchProtected    AccessAuditAction = "branch_protected"
	AccessAuditBranchUnprotected  AccessAuditAction = "branch_unprotected"
)

// AccessAuditLog represents an access control audit entry
type AccessAuditLog struct {
	ID           types.ID           `json:"id"`
	RepositoryID *types.ID          `json:"repository_id,omitempty"`
	Action       AccessAuditAction  `json:"action"`

	SubjectUserID *types.ID `json:"subject_user_id,omitempty"`
	SubjectTeamID *types.ID `json:"subject_team_id,omitempty"`

	Details  string                 `json:"details,omitempty"`
	OldValue map[string]interface{} `json:"old_value,omitempty"`
	NewValue map[string]interface{} `json:"new_value,omitempty"`

	ActorID types.ID `json:"actor_id"`
	ActorIP string   `json:"actor_ip,omitempty"`

	OccurredAt time.Time `json:"occurred_at"`
}

// Request/Response DTOs

// AddContributorRequest represents a request to add a contributor
type AddContributorRequest struct {
	RepositoryID types.ID        `json:"repository_id" validate:"required"`
	UserID       types.ID        `json:"user_id" validate:"required"`
	Role         ContributorRole `json:"role" validate:"required"`
	InvitedBy    types.ID        `json:"invited_by" validate:"required"`
}

// UpdateContributorRequest represents a request to update contributor permissions
type UpdateContributorRequest struct {
	ContributorID types.ID         `json:"contributor_id" validate:"required"`
	Role          *ContributorRole `json:"role,omitempty"`
	Status        *ContributorStatus `json:"status,omitempty"`
}

// CreateTeamRequest represents a request to create a team
type CreateTeamRequest struct {
	RepositoryID   *types.ID `json:"repository_id,omitempty"`
	OrganizationID *types.ID `json:"organization_id,omitempty"`
	Slug           string    `json:"slug" validate:"required"`
	Name           string    `json:"name" validate:"required"`
	Description    string    `json:"description,omitempty"`
	TeamType       TeamType  `json:"team_type"`
	Specializations []string `json:"specializations,omitempty"`
	CreatedBy      types.ID  `json:"created_by" validate:"required"`
}

// AddTeamMemberRequest represents a request to add a member to a team
type AddTeamMemberRequest struct {
	TeamID   types.ID `json:"team_id" validate:"required"`
	UserID   types.ID `json:"user_id" validate:"required"`
	TeamRole TeamRole `json:"team_role"`
	AddedBy  types.ID `json:"added_by" validate:"required"`
}

// CreateBranchProtectionRequest represents a request to protect a branch
type CreateBranchProtectionRequest struct {
	RepositoryID    types.ID `json:"repository_id" validate:"required"`
	BranchPattern   string   `json:"branch_pattern" validate:"required"`
	RequirePR       bool     `json:"require_pr"`
	RequireReviews  int      `json:"require_reviews"`
	CreatedBy       types.ID `json:"created_by" validate:"required"`
}

// Repository Interfaces

// ContributorRepository defines the interface for contributor management
type ContributorRepository interface {
	// CRUD operations
	Add(contributor *Contributor) error
	GetByID(id types.ID) (*Contributor, error)
	GetByUser(repositoryID, userID types.ID) (*Contributor, error)
	Update(contributor *Contributor) error
	Remove(id types.ID) error

	// Query operations
	ListByRepository(repositoryID types.ID) ([]*Contributor, error)
	ListByUser(userID types.ID) ([]*Contributor, error)
	CountByRepository(repositoryID types.ID) (int, error)
}

// TeamRepository defines the interface for team management
type TeamRepository interface {
	Create(team *Team) error
	GetByID(id types.ID) (*Team, error)
	GetBySlug(repositoryID types.ID, slug string) (*Team, error)
	Update(team *Team) error
	Delete(id types.ID) error

	ListByRepository(repositoryID types.ID) ([]*Team, error)
	ListByOrganization(organizationID types.ID) ([]*Team, error)
}

// TeamMemberRepository defines the interface for team membership
type TeamMemberRepository interface {
	Add(member *TeamMember) error
	Remove(teamID, userID types.ID) error
	ListByTeam(teamID types.ID) ([]*TeamMember, error)
	ListByUser(userID types.ID) ([]*TeamMember, error)
	IsMember(teamID, userID types.ID) (bool, error)
}

// BranchProtectionRepository defines the interface for branch protection
type BranchProtectionRepository interface {
	Create(rule *BranchProtectionRule) error
	GetByID(id types.ID) (*BranchProtectionRule, error)
	Update(rule *BranchProtectionRule) error
	Delete(id types.ID) error

	ListByRepository(repositoryID types.ID) ([]*BranchProtectionRule, error)
	GetProtectionForBranch(repositoryID types.ID, branchName string) (*BranchProtectionRule, error)
}

// AccessAuditRepository defines the interface for access audit logging
type AccessAuditRepository interface {
	Log(entry *AccessAuditLog) error
	List(repositoryID types.ID, limit int) ([]*AccessAuditLog, error)
	ListByUser(userID types.ID, limit int) ([]*AccessAuditLog, error)
}

