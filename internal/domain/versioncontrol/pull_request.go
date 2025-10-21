package versioncontrol

import (
	"time"

	"github.com/arx-os/arxos/internal/domain/types"
)

// Pull Request domain entities
// These implement GitHub-style pull requests for building repositories
// PRs are used for work orders, contractor projects, issue fixes, etc.

// PRType represents the type/purpose of a pull request
type PRType string

const (
	PRTypeWorkOrder        PRType = "work_order"
	PRTypeContractorWork   PRType = "contractor_work"
	PRTypeVendorService    PRType = "vendor_service"
	PRTypeEquipmentUpgrade PRType = "equipment_upgrade"
	PRTypeBASIntegration   PRType = "bas_integration"
	PRTypeScanUpload       PRType = "scan_upload"
	PRTypeIssueFix         PRType = "issue_fix"
	PRTypeFeature          PRType = "feature"
	PRTypeOther            PRType = "other"
)

// PRStatus represents the status of a pull request
type PRStatus string

const (
	PRStatusOpen             PRStatus = "open"
	PRStatusInReview         PRStatus = "in_review"
	PRStatusChangesRequested PRStatus = "changes_requested"
	PRStatusApproved         PRStatus = "approved"
	PRStatusMerged           PRStatus = "merged"
	PRStatusClosed           PRStatus = "closed"
	PRStatusDraft            PRStatus = "draft"
)

// PRPriority represents priority levels for pull requests
type PRPriority string

const (
	PRPriorityLow       PRPriority = "low"
	PRPriorityNormal    PRPriority = "normal"
	PRPriorityHigh      PRPriority = "high"
	PRPriorityUrgent    PRPriority = "urgent"
	PRPriorityEmergency PRPriority = "emergency"
)

// PullRequest represents a pull request (work order, contractor project, etc.)
type PullRequest struct {
	ID           types.ID `json:"id"`
	RepositoryID types.ID `json:"repository_id"`
	Number       int      `json:"number"` // Auto-incrementing per repository

	// PR content
	Title       string `json:"title"`
	Description string `json:"description,omitempty"`

	// Branches
	SourceBranchID types.ID `json:"source_branch_id"`
	TargetBranchID types.ID `json:"target_branch_id"`

	// Type and status
	PRType   PRType   `json:"pr_type"`
	Status   PRStatus `json:"status"`
	Priority PRPriority `json:"priority"`

	// Review requirements
	RequiresReview     bool `json:"requires_review"`
	RequiredReviewers  int  `json:"required_reviewers"`
	ApprovedCount      int  `json:"approved_count"`

	// Assignment
	AssignedTo   *types.ID `json:"assigned_to,omitempty"`
	AssignedTeam string    `json:"assigned_team,omitempty"`
	AutoAssigned bool      `json:"auto_assigned"`

	// Work tracking
	EstimatedHours *float64 `json:"estimated_hours,omitempty"`
	ActualHours    *float64 `json:"actual_hours,omitempty"`
	BudgetAmount   *float64 `json:"budget_amount,omitempty"`
	ActualCost     *float64 `json:"actual_cost,omitempty"`

	// Scheduling
	DueDate *time.Time `json:"due_date,omitempty"`

	// Labels
	Labels []string `json:"labels,omitempty"`

	// Metadata
	Metadata map[string]any `json:"metadata,omitempty"`

	// Author
	CreatedBy types.ID `json:"created_by"`

	// Audit
	CreatedAt time.Time  `json:"created_at"`
	UpdatedAt time.Time  `json:"updated_at"`
	ClosedAt  *time.Time `json:"closed_at,omitempty"`
	MergedAt  *time.Time `json:"merged_at,omitempty"`
	MergedBy  *types.ID  `json:"merged_by,omitempty"`
}

// PRReviewStatus represents review status
type PRReviewStatus string

const (
	PRReviewStatusPending          PRReviewStatus = "pending"
	PRReviewStatusApproved         PRReviewStatus = "approved"
	PRReviewStatusChangesRequested PRReviewStatus = "changes_requested"
	PRReviewStatusCommented        PRReviewStatus = "commented"
)

// PRReviewer represents a reviewer assigned to a PR
type PRReviewer struct {
	ID     types.ID `json:"id"`
	PRID   types.ID `json:"pr_id"`
	UserID types.ID `json:"user_id"`

	Status     PRReviewStatus `json:"status"`
	Required   bool           `json:"required"`
	ReviewedAt *time.Time     `json:"reviewed_at,omitempty"`

	AddedAt time.Time  `json:"added_at"`
	AddedBy *types.ID `json:"added_by,omitempty"`
}

// PRReviewDecision represents a review decision
type PRReviewDecision string

const (
	PRReviewDecisionApprove         PRReviewDecision = "approve"
	PRReviewDecisionRequestChanges  PRReviewDecision = "request_changes"
	PRReviewDecisionComment         PRReviewDecision = "comment"
)

// PRReview represents a review submission
type PRReview struct {
	ID         types.ID `json:"id"`
	PRID       types.ID `json:"pr_id"`
	ReviewerID types.ID `json:"reviewer_id"`

	Decision PRReviewDecision `json:"decision"`
	Summary  string           `json:"summary,omitempty"`
	Body     string           `json:"body,omitempty"`

	ReviewedAt time.Time `json:"reviewed_at"`
}

// PRCommentType represents types of PR comments
type PRCommentType string

const (
	PRCommentTypeGeneral       PRCommentType = "general"
	PRCommentTypeReview        PRCommentType = "review"
	PRCommentTypeChangeRequest PRCommentType = "change_request"
	PRCommentTypeApproval      PRCommentType = "approval"
	PRCommentTypeStatusUpdate  PRCommentType = "status_update"
)

// PRComment represents a comment on a pull request
type PRComment struct {
	ID   types.ID      `json:"id"`
	PRID types.ID      `json:"pr_id"`
	CommentType PRCommentType `json:"comment_type"`

	Body string `json:"body"`

	// Threading
	ParentCommentID *types.ID `json:"parent_comment_id,omitempty"`
	ThreadResolved  bool      `json:"thread_resolved"`

	// Entity reference (commenting on specific change)
	EntityType *EntityType `json:"entity_type,omitempty"`
	EntityID   *types.ID   `json:"entity_id,omitempty"`

	AuthorID types.ID `json:"author_id"`

	// Reactions
	Reactions map[string]int `json:"reactions,omitempty"` // thumbs_up: 5, heart: 2

	CreatedAt time.Time `json:"created_at"`
	UpdatedAt time.Time `json:"updated_at"`
	Edited    bool      `json:"edited"`
}

// PRFile represents a file attached to a PR
type PRFile struct {
	ID   types.ID `json:"id"`
	PRID types.ID `json:"pr_id"`

	Filename    string `json:"filename"`
	FilePath    string `json:"file_path"`
	FileSize    int64  `json:"file_size"`
	FileType    string `json:"file_type,omitempty"`
	MimeType    string `json:"mime_type,omitempty"`
	Category    string `json:"category,omitempty"`
	Description string `json:"description,omitempty"`

	UploadedBy types.ID  `json:"uploaded_by"`
	UploadedAt time.Time `json:"uploaded_at"`
}

// PRAssignmentRule represents an auto-assignment rule
type PRAssignmentRule struct {
	ID           types.ID `json:"id"`
	RepositoryID types.ID `json:"repository_id"`

	Name        string `json:"name"`
	Description string `json:"description,omitempty"`
	Enabled     bool   `json:"enabled"`
	Priority    int    `json:"priority"` // Higher checked first

	// Matching criteria
	EquipmentType string      `json:"equipment_type,omitempty"`
	RoomType      string      `json:"room_type,omitempty"`
	FloorNumber   *int        `json:"floor_number,omitempty"`
	PRType        *PRType     `json:"pr_type,omitempty"`
	PriorityLevel *PRPriority `json:"priority_level,omitempty"`

	// Assignment action
	AssignToUser *types.ID  `json:"assign_to_user,omitempty"`
	AssignToTeam string     `json:"assign_to_team,omitempty"`
	NotifyUsers  []types.ID `json:"notify_users,omitempty"`

	Metadata map[string]any `json:"metadata,omitempty"`

	CreatedAt time.Time  `json:"created_at"`
	CreatedBy *types.ID `json:"created_by,omitempty"`
}

// PRActivityType represents types of PR activity
type PRActivityType string

const (
	PRActivityCreated          PRActivityType = "created"
	PRActivityAssigned         PRActivityType = "assigned"
	PRActivityReviewRequested  PRActivityType = "review_requested"
	PRActivityReviewed         PRActivityType = "reviewed"
	PRActivityApproved         PRActivityType = "approved"
	PRActivityChangesRequested PRActivityType = "changes_requested"
	PRActivityCommented        PRActivityType = "commented"
	PRActivityStatusChanged    PRActivityType = "status_changed"
	PRActivityMerged           PRActivityType = "merged"
	PRActivityClosed           PRActivityType = "closed"
	PRActivityReopened         PRActivityType = "reopened"
	PRActivityLabeled          PRActivityType = "labeled"
	PRActivityUnlabeled        PRActivityType = "unlabeled"
	PRActivityFileAttached     PRActivityType = "file_attached"
)

// PRActivity represents an activity event on a PR
type PRActivity struct {
	ID   types.ID       `json:"id"`
	PRID types.ID       `json:"pr_id"`
	ActivityType PRActivityType `json:"activity_type"`

	Details  string                 `json:"details,omitempty"`
	Metadata map[string]any `json:"metadata,omitempty"`

	ActorID    *types.ID `json:"actor_id,omitempty"`
	OccurredAt time.Time `json:"occurred_at"`
}

// Request/Response DTOs

// CreatePRRequest represents a request to create a pull request
type CreatePRRequest struct {
	RepositoryID types.ID `json:"repository_id" validate:"required"`
	Title        string   `json:"title" validate:"required"`
	Description  string   `json:"description,omitempty"`

	SourceBranchID types.ID `json:"source_branch_id" validate:"required"`
	TargetBranchID types.ID `json:"target_branch_id" validate:"required"`

	PRType   PRType     `json:"pr_type"`
	Priority PRPriority `json:"priority"`

	AssignedTo *types.ID `json:"assigned_to,omitempty"`
	Reviewers  []types.ID `json:"reviewers,omitempty"`

	DueDate        *time.Time `json:"due_date,omitempty"`
	EstimatedHours *float64   `json:"estimated_hours,omitempty"`
	BudgetAmount   *float64   `json:"budget_amount,omitempty"`

	Labels []string `json:"labels,omitempty"`

	CreatedBy types.ID `json:"created_by" validate:"required"`
}

// UpdatePRRequest represents a request to update a PR
type UpdatePRRequest struct {
	ID          types.ID   `json:"id" validate:"required"`
	Title       *string    `json:"title,omitempty"`
	Description *string    `json:"description,omitempty"`
	Status      *PRStatus  `json:"status,omitempty"`
	Priority    *PRPriority `json:"priority,omitempty"`
	AssignedTo  *types.ID  `json:"assigned_to,omitempty"`
	DueDate     *time.Time `json:"due_date,omitempty"`
	Labels      []string   `json:"labels,omitempty"`
}

// ReviewPRRequest represents a request to review a PR
type ReviewPRRequest struct {
	PRID       types.ID         `json:"pr_id" validate:"required"`
	ReviewerID types.ID         `json:"reviewer_id" validate:"required"`
	Decision   PRReviewDecision `json:"decision" validate:"required"`
	Summary    string           `json:"summary,omitempty"`
	Body       string           `json:"body,omitempty"`
}

// MergePRRequest represents a request to merge a PR
type MergePRRequest struct {
	PRID     types.ID `json:"pr_id" validate:"required"`
	MergedBy types.ID `json:"merged_by" validate:"required"`
	Message  string   `json:"message,omitempty"`
	Strategy string   `json:"strategy,omitempty"` // merge, squash, rebase
}

// AddPRCommentRequest represents a request to add a comment
type AddPRCommentRequest struct {
	PRID   types.ID `json:"pr_id" validate:"required"`
	Body   string   `json:"body" validate:"required"`
	AuthorID types.ID `json:"author_id" validate:"required"`
	
	ParentCommentID *types.ID `json:"parent_comment_id,omitempty"`
	EntityType      *EntityType `json:"entity_type,omitempty"`
	EntityID        *types.ID   `json:"entity_id,omitempty"`
}

// AttachPRFileRequest represents a request to attach a file to PR
type AttachPRFileRequest struct {
	PRID       types.ID `json:"pr_id" validate:"required"`
	Filename   string   `json:"filename" validate:"required"`
	FilePath   string   `json:"file_path" validate:"required"`
	FileSize   int64    `json:"file_size" validate:"required"`
	FileType   string   `json:"file_type,omitempty"`
	Category   string   `json:"category,omitempty"`
	Description string  `json:"description,omitempty"`
	UploadedBy types.ID `json:"uploaded_by" validate:"required"`
}

// PRFilter represents filters for querying pull requests
type PRFilter struct {
	RepositoryID *types.ID   `json:"repository_id,omitempty"`
	Status       *PRStatus   `json:"status,omitempty"`
	PRType       *PRType     `json:"pr_type,omitempty"`
	Priority     *PRPriority `json:"priority,omitempty"`
	AssignedTo   *types.ID   `json:"assigned_to,omitempty"`
	CreatedBy    *types.ID   `json:"created_by,omitempty"`
	Label        string      `json:"label,omitempty"`
	Overdue      bool        `json:"overdue,omitempty"`
}

// Repository Interfaces

// PullRequestRepository defines the interface for PR data access
type PullRequestRepository interface {
	// CRUD operations
	Create(pr *PullRequest) error
	GetByID(id types.ID) (*PullRequest, error)
	GetByNumber(repositoryID types.ID, number int) (*PullRequest, error)
	Update(pr *PullRequest) error
	Delete(id types.ID) error

	// Query operations
	List(filter PRFilter, limit, offset int) ([]*PullRequest, error)
	Count(filter PRFilter) (int, error)
	ListOpen(repositoryID types.ID) ([]*PullRequest, error)
	ListAssigned(userID types.ID) ([]*PullRequest, error)
	ListOverdue(repositoryID types.ID) ([]*PullRequest, error)

	// Status operations
	UpdateStatus(id types.ID, status PRStatus) error
	Merge(id types.ID, mergedBy types.ID) error
	Close(id types.ID) error
}

// PRReviewerRepository defines the interface for reviewer management
type PRReviewerRepository interface {
	Add(reviewer *PRReviewer) error
	Remove(prID, userID types.ID) error
	List(prID types.ID) ([]*PRReviewer, error)
	UpdateStatus(prID, userID types.ID, status PRReviewStatus) error
}

// PRReviewRepository defines the interface for review management
type PRReviewRepository interface {
	Create(review *PRReview) error
	List(prID types.ID) ([]*PRReview, error)
	GetByReviewer(prID, reviewerID types.ID) (*PRReview, error)
}

// PRCommentRepository defines the interface for comment management
type PRCommentRepository interface {
	Create(comment *PRComment) error
	GetByID(id types.ID) (*PRComment, error)
	Update(comment *PRComment) error
	Delete(id types.ID) error
	List(prID types.ID) ([]*PRComment, error)
	ListByThread(parentID types.ID) ([]*PRComment, error)
	ResolveThread(commentID types.ID) error
}

// PRFileRepository defines the interface for file attachment management
type PRFileRepository interface {
	Attach(file *PRFile) error
	List(prID types.ID) ([]*PRFile, error)
	Delete(id types.ID) error
}

// PRAssignmentRuleRepository defines the interface for assignment rules
type PRAssignmentRuleRepository interface {
	Create(rule *PRAssignmentRule) error
	GetByID(id types.ID) (*PRAssignmentRule, error)
	Update(rule *PRAssignmentRule) error
	Delete(id types.ID) error
	ListEnabled(repositoryID types.ID) ([]*PRAssignmentRule, error)
}

// PRActivityRepository defines the interface for activity logging
type PRActivityRepository interface {
	Log(activity *PRActivity) error
	List(prID types.ID, limit int) ([]*PRActivity, error)
}

