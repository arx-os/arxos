package domain

import (
	"time"

	"github.com/arx-os/arxos/internal/domain/types"
)

// Git-like workflow domain entities for collaborative spatial management
// These implement GitHub-style branching, commits, and collaboration
// Domain-agnostic: works for buildings, ships, warehouses, or any spatial structure

// BranchType represents the type/purpose of a branch
type BranchType string

const (
	BranchTypeMain        BranchType = "main"
	BranchTypeDevelopment BranchType = "development"
	BranchTypeFeature     BranchType = "feature"
	BranchTypeBugfix      BranchType = "bugfix"
	BranchTypeRelease     BranchType = "release"
	BranchTypeHotfix      BranchType = "hotfix"
	BranchTypeContractor  BranchType = "contractor"
	BranchTypeVendor      BranchType = "vendor"
	BranchTypeIssue       BranchType = "issue"
	BranchTypeScan        BranchType = "scan"
)

// BranchStatus represents the status of a branch
type BranchStatus string

const (
	BranchStatusActive BranchStatus = "active"
	BranchStatusStale  BranchStatus = "stale"
	BranchStatusMerged BranchStatus = "merged"
	BranchStatusClosed BranchStatus = "closed"
)

// Branch represents a Git-like branch in a spatial repository
// Works for any domain: building renovations, ship modifications, warehouse reconfigurations
type Branch struct {
	ID           types.ID `json:"id"`
	RepositoryID types.ID `json:"repository_id"`
	Name         string   `json:"name"`
	DisplayName  string   `json:"display_name"`
	Description  string   `json:"description,omitempty"`

	// Branch metadata
	BaseCommit *types.ID `json:"base_commit,omitempty"` // What this branched from
	HeadCommit *types.ID `json:"head_commit,omitempty"` // Current tip

	// Branch type and protection
	BranchType        BranchType `json:"branch_type"`
	Protected         bool       `json:"protected"`
	RequiresReview    bool       `json:"requires_review"`
	AutoDeleteOnMerge bool       `json:"auto_delete_on_merge"`

	// Status
	Status    BranchStatus `json:"status"`
	IsDefault bool         `json:"is_default"`

	// Ownership
	CreatedBy *types.ID `json:"created_by,omitempty"`
	OwnedBy   *types.ID `json:"owned_by,omitempty"`

	// Audit
	CreatedAt time.Time  `json:"created_at"`
	UpdatedAt time.Time  `json:"updated_at"`
	MergedAt  *time.Time `json:"merged_at,omitempty"`
	MergedBy  *types.ID  `json:"merged_by,omitempty"`
}

// Commit represents an enhanced commit with detailed changeset
type Commit struct {
	ID           types.ID `json:"id"`
	RepositoryID types.ID `json:"repository_id"`
	BranchID     types.ID `json:"branch_id"`
	VersionID    types.ID `json:"version_id"`

	// Commit identification
	CommitHash string `json:"commit_hash"`
	ShortHash  string `json:"short_hash"`

	// Commit message
	Message     string `json:"message"`
	Description string `json:"description,omitempty"`

	// Author
	AuthorName  string    `json:"author_name"`
	AuthorEmail string    `json:"author_email"`
	AuthorID    *types.ID `json:"author_id,omitempty"`

	// Relationships
	ParentCommits []types.ID `json:"parent_commits"` // One for regular, multiple for merge
	MergeCommit   bool       `json:"merge_commit"`

	// Changes summary
	ChangesSummary ChangesSummary `json:"changes_summary"`
	FilesChanged   int            `json:"files_changed"`
	LinesAdded     int            `json:"lines_added"`
	LinesDeleted   int            `json:"lines_deleted"`

	// Tags
	Tags []string `json:"tags,omitempty"`

	// Metadata
	Metadata map[string]interface{} `json:"metadata,omitempty"`

	// Audit
	CommittedAt time.Time `json:"committed_at"`
}

// ChangesSummary provides high-level summary of changes in a commit
type ChangesSummary struct {
	BuildingsAdded    int `json:"buildings_added"`
	BuildingsModified int `json:"buildings_modified"`
	BuildingsDeleted  int `json:"buildings_deleted"`

	FloorsAdded    int `json:"floors_added"`
	FloorsModified int `json:"floors_modified"`
	FloorsDeleted  int `json:"floors_deleted"`

	RoomsAdded    int `json:"rooms_added"`
	RoomsModified int `json:"rooms_modified"`
	RoomsDeleted  int `json:"rooms_deleted"`

	EquipmentAdded    int `json:"equipment_added"`
	EquipmentModified int `json:"equipment_modified"`
	EquipmentDeleted  int `json:"equipment_deleted"`

	BASPointsAdded    int `json:"bas_points_added"`
	BASPointsModified int `json:"bas_points_modified"`
	BASPointsDeleted  int `json:"bas_points_deleted"`
}

// ChangeType represents the type of change
type ChangeType string

const (
	ChangeTypeAdded    ChangeType = "added"
	ChangeTypeModified ChangeType = "modified"
	ChangeTypeDeleted  ChangeType = "deleted"
	ChangeTypeRenamed  ChangeType = "renamed"
	ChangeTypeMoved    ChangeType = "moved"
)

// EntityType represents types of entities that can be changed
type EntityType string

const (
	EntityTypeBuilding      EntityType = "building"
	EntityTypeFloor         EntityType = "floor"
	EntityTypeRoom          EntityType = "room"
	EntityTypeEquipment     EntityType = "equipment"
	EntityTypeBASPoint      EntityType = "bas_point"
	EntityTypeBASSystem     EntityType = "bas_system"
	EntityTypeComponent     EntityType = "component"
	EntityTypeSpatialAnchor EntityType = "spatial_anchor"
	EntityTypePointCloud    EntityType = "point_cloud"
)

// CommitChange represents a single entity change in a commit
type CommitChange struct {
	ID       types.ID `json:"id"`
	CommitID types.ID `json:"commit_id"`

	// Entity identification
	EntityType EntityType `json:"entity_type"`
	EntityID   types.ID   `json:"entity_id"`
	EntityPath string     `json:"entity_path,omitempty"` // ArxOS path

	// Change details
	ChangeType ChangeType `json:"change_type"`
	FieldName  string     `json:"field_name,omitempty"`
	OldValue   string     `json:"old_value,omitempty"`
	NewValue   string     `json:"new_value,omitempty"`

	// Diff
	Diff map[string]interface{} `json:"diff,omitempty"`

	CreatedAt time.Time `json:"created_at"`
}

// BranchState represents the current state of a branch
type BranchState struct {
	ID           types.ID `json:"id"`
	RepositoryID types.ID `json:"repository_id"`
	BranchID     types.ID `json:"branch_id"`

	// Entity counts
	BuildingsCount int `json:"buildings_count"`
	FloorsCount    int `json:"floors_count"`
	RoomsCount     int `json:"rooms_count"`
	EquipmentCount int `json:"equipment_count"`
	BASPointsCount int `json:"bas_points_count"`

	// Uncommitted changes
	HasUncommittedChanges   bool `json:"has_uncommitted_changes"`
	UncommittedChangesCount int  `json:"uncommitted_changes_count"`

	// State hash
	StateHash string `json:"state_hash"`

	UpdatedAt time.Time `json:"updated_at"`
}

// WorkingDirectory represents a user's current working state
type WorkingDirectory struct {
	ID           types.ID `json:"id"`
	RepositoryID types.ID `json:"repository_id"`
	UserID       types.ID `json:"user_id"`

	// Current checkout
	CurrentBranchID types.ID  `json:"current_branch_id"`
	CurrentCommitID *types.ID `json:"current_commit_id,omitempty"`

	// Working state
	HasUncommittedChanges bool           `json:"has_uncommitted_changes"`
	StagedChanges         []CommitChange `json:"staged_changes,omitempty"`

	// Metadata
	Metadata map[string]interface{} `json:"metadata,omitempty"`

	// Last activity
	LastCheckoutAt time.Time  `json:"last_checkout_at"`
	LastCommitAt   *time.Time `json:"last_commit_at,omitempty"`
}

// MergeConflict represents a conflict during branch merge
type MergeConflict struct {
	ID           types.ID `json:"id"`
	RepositoryID types.ID `json:"repository_id"`

	// Merge details
	SourceBranchID types.ID `json:"source_branch_id"`
	TargetBranchID types.ID `json:"target_branch_id"`

	// Conflict details
	EntityType EntityType `json:"entity_type"`
	EntityID   types.ID   `json:"entity_id"`
	EntityPath string     `json:"entity_path,omitempty"`

	// Conflicting values
	SourceValue string `json:"source_value"`
	TargetValue string `json:"target_value"`
	BaseValue   string `json:"base_value,omitempty"` // Common ancestor

	// Resolution
	Resolved           bool       `json:"resolved"`
	ResolutionValue    string     `json:"resolution_value,omitempty"`
	ResolvedBy         *types.ID  `json:"resolved_by,omitempty"`
	ResolvedAt         *time.Time `json:"resolved_at,omitempty"`
	ResolutionStrategy string     `json:"resolution_strategy,omitempty"` // ours, theirs, manual, auto

	// Metadata
	ConflictType string                 `json:"conflict_type,omitempty"` // content, delete, rename, move
	Metadata     map[string]interface{} `json:"metadata,omitempty"`

	DetectedAt time.Time `json:"detected_at"`
}

// Request/Response DTOs

// CreateBranchRequest represents a request to create a new branch
type CreateBranchRequest struct {
	RepositoryID types.ID   `json:"repository_id" validate:"required"`
	Name         string     `json:"name" validate:"required"`
	DisplayName  string     `json:"display_name,omitempty"`
	Description  string     `json:"description,omitempty"`
	BaseCommit   *types.ID  `json:"base_commit,omitempty"` // Branch from this commit (defaults to current HEAD)
	BranchType   BranchType `json:"branch_type"`
	CreatedBy    *types.ID  `json:"created_by,omitempty"`
}

// CheckoutBranchRequest represents a request to checkout a branch
type CheckoutBranchRequest struct {
	RepositoryID types.ID `json:"repository_id" validate:"required"`
	BranchName   string   `json:"branch_name" validate:"required"`
	UserID       types.ID `json:"user_id" validate:"required"`
	Force        bool     `json:"force"` // Force checkout even with uncommitted changes
}

// CommitRequest represents a request to create a commit
type CommitRequest struct {
	RepositoryID types.ID  `json:"repository_id" validate:"required"`
	BranchID     types.ID  `json:"branch_id" validate:"required"`
	Message      string    `json:"message" validate:"required"`
	Description  string    `json:"description,omitempty"`
	AuthorName   string    `json:"author_name" validate:"required"`
	AuthorEmail  string    `json:"author_email" validate:"required,email"`
	AuthorID     *types.ID `json:"author_id,omitempty"`
	Tags         []string  `json:"tags,omitempty"`
}

// MergeBranchRequest represents a request to merge branches
type MergeBranchRequest struct {
	RepositoryID   types.ID `json:"repository_id" validate:"required"`
	SourceBranchID types.ID `json:"source_branch_id" validate:"required"`
	TargetBranchID types.ID `json:"target_branch_id" validate:"required"`
	Message        string   `json:"message" validate:"required"`
	AuthorID       types.ID `json:"author_id" validate:"required"`
	Strategy       string   `json:"strategy,omitempty"` // fast-forward, merge-commit, squash
}

// BranchFilter represents filters for querying branches
type BranchFilter struct {
	RepositoryID *types.ID     `json:"repository_id,omitempty"`
	Status       *BranchStatus `json:"status,omitempty"`
	BranchType   *BranchType   `json:"branch_type,omitempty"`
	OwnedBy      *types.ID     `json:"owned_by,omitempty"`
	CreatedBy    *types.ID     `json:"created_by,omitempty"`
	Protected    *bool         `json:"protected,omitempty"`
}

// CommitFilter represents filters for querying commits
type CommitFilter struct {
	RepositoryID *types.ID  `json:"repository_id,omitempty"`
	BranchID     *types.ID  `json:"branch_id,omitempty"`
	AuthorID     *types.ID  `json:"author_id,omitempty"`
	Since        *time.Time `json:"since,omitempty"`
	Until        *time.Time `json:"until,omitempty"`
	MergeCommit  *bool      `json:"merge_commit,omitempty"`
}

// Repository Interfaces

// BranchRepository defines the interface for branch data access
type BranchRepository interface {
	// CRUD operations
	Create(branch *Branch) error
	GetByID(id types.ID) (*Branch, error)
	Update(branch *Branch) error
	Delete(id types.ID) error

	// Query operations
	List(filter BranchFilter) ([]*Branch, error)
	GetByName(repositoryID types.ID, name string) (*Branch, error)
	GetDefaultBranch(repositoryID types.ID) (*Branch, error)
	ListActive(repositoryID types.ID) ([]*Branch, error)

	// Branch operations
	SetHead(branchID, commitID types.ID) error
	MarkMerged(branchID, mergedBy types.ID) error
}

// CommitRepository defines the interface for commit data access
type CommitRepository interface {
	// CRUD operations
	Create(commit *Commit) error
	GetByID(id types.ID) (*Commit, error)
	GetByHash(hash string) (*Commit, error)

	// Query operations
	List(filter CommitFilter, limit, offset int) ([]*Commit, error)
	ListByBranch(branchID types.ID, limit, offset int) ([]*Commit, error)
	GetHistory(branchID types.ID) ([]*Commit, error)

	// Commit relationships
	GetParents(commitID types.ID) ([]*Commit, error)
	GetChildren(commitID types.ID) ([]*Commit, error)
	IsAncestor(ancestor, descendant types.ID) (bool, error)
}

// CommitChangeRepository defines the interface for commit change data access
type CommitChangeRepository interface {
	// Operations
	Create(change *CommitChange) error
	BulkCreate(changes []*CommitChange) error
	ListByCommit(commitID types.ID) ([]*CommitChange, error)
	GetChangesSummary(commitID types.ID) (*ChangesSummary, error)
}

// WorkingDirectoryRepository defines the interface for working directory management
type WorkingDirectoryRepository interface {
	// Operations
	GetOrCreate(repositoryID, userID types.ID) (*WorkingDirectory, error)
	Update(wd *WorkingDirectory) error
	Checkout(wd *WorkingDirectory, branchID types.ID) error
	AddStagedChange(wd *WorkingDirectory, change CommitChange) error
	ClearStagedChanges(wd *WorkingDirectory) error
}

// MergeConflictRepository defines the interface for merge conflict management
type MergeConflictRepository interface {
	// Operations
	Create(conflict *MergeConflict) error
	BulkCreate(conflicts []*MergeConflict) error
	ListByMerge(sourceBranchID, targetBranchID types.ID) ([]*MergeConflict, error)
	ListUnresolved(repositoryID types.ID) ([]*MergeConflict, error)
	Resolve(conflictID types.ID, resolution string, resolvedBy types.ID) error
	DeleteByMerge(sourceBranchID, targetBranchID types.ID) error
}

// CommitComparison represents a comparison between two commits
type CommitComparison struct {
	FromCommit *Commit
	ToCommit   *Commit
	Summary    ChangesSummary
	Changes    []CommitChange
}
