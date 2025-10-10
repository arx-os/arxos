package domain

import (
	"time"

	"github.com/arx-os/arxos/internal/domain/types"
)

// Issue domain entities
// GitHub-style issue tracking for building repositories
// Issues represent problems, tasks, or questions reported by building staff

// IssueType represents the type/category of an issue
type IssueType string

const (
	IssueTypeProblem       IssueType = "problem"
	IssueTypeMaintenance   IssueType = "maintenance"
	IssueTypeImprovement   IssueType = "improvement"
	IssueTypeQuestion      IssueType = "question"
	IssueTypeDocumentation IssueType = "documentation"
	IssueTypeSafety        IssueType = "safety"
	IssueTypeEmergency     IssueType = "emergency"
)

// IssueStatus represents the status of an issue
type IssueStatus string

const (
	IssueStatusOpen       IssueStatus = "open"
	IssueStatusInProgress IssueStatus = "in_progress"
	IssueStatusResolved   IssueStatus = "resolved"
	IssueStatusClosed     IssueStatus = "closed"
	IssueStatusDuplicate  IssueStatus = "duplicate"
	IssueStatusWontFix    IssueStatus = "wont_fix"
)

// IssuePriority represents priority levels
type IssuePriority string

const (
	IssuePriorityLow       IssuePriority = "low"
	IssuePriorityNormal    IssuePriority = "normal"
	IssuePriorityHigh      IssuePriority = "high"
	IssuePriorityUrgent    IssuePriority = "urgent"
	IssuePriorityEmergency IssuePriority = "emergency"
)

// ReportedVia indicates how the issue was reported
type ReportedVia string

const (
	ReportedViaMobileAR  ReportedVia = "mobile_ar"
	ReportedViaMobileApp ReportedVia = "mobile_app"
	ReportedViaCLI       ReportedVia = "cli"
	ReportedViaAPI       ReportedVia = "api"
	ReportedViaWeb       ReportedVia = "web"
)

// Issue represents a problem, task, or question
type Issue struct {
	ID           types.ID `json:"id"`
	RepositoryID types.ID `json:"repository_id"`
	Number       int      `json:"number"` // Auto-incrementing per repository

	// Content
	Title string `json:"title"`
	Body  string `json:"body,omitempty"`

	// Spatial context (WHERE is the problem?)
	BuildingID  *types.ID `json:"building_id,omitempty"`
	FloorID     *types.ID `json:"floor_id,omitempty"`
	RoomID      *types.ID `json:"room_id,omitempty"`
	EquipmentID *types.ID `json:"equipment_id,omitempty"`
	BASPointID  *types.ID `json:"bas_point_id,omitempty"`

	// Location
	Location            *Location `json:"location,omitempty"`
	LocationDescription string    `json:"location_description,omitempty"`

	// Classification
	IssueType IssueType     `json:"issue_type"`
	Status    IssueStatus   `json:"status"`
	Priority  IssuePriority `json:"priority"`

	// Assignment
	AssignedTo   *types.ID `json:"assigned_to,omitempty"`
	AssignedTeam string    `json:"assigned_team,omitempty"`
	AutoAssigned bool      `json:"auto_assigned"`

	// Git integration
	BranchID *types.ID `json:"branch_id,omitempty"` // Auto-created branch
	PRID     *types.ID `json:"pr_id,omitempty"`     // Auto-created PR

	// Reporter
	ReportedBy  types.ID     `json:"reported_by"`
	ReportedVia *ReportedVia `json:"reported_via,omitempty"`

	// Resolution
	ResolvedBy      *types.ID  `json:"resolved_by,omitempty"`
	ResolvedAt      *time.Time `json:"resolved_at,omitempty"`
	ResolutionNotes string     `json:"resolution_notes,omitempty"`

	// Verification
	VerifiedByReporter bool       `json:"verified_by_reporter"`
	VerifiedAt         *time.Time `json:"verified_at,omitempty"`

	// Metadata
	Metadata map[string]interface{} `json:"metadata,omitempty"`

	// Audit
	CreatedAt time.Time  `json:"created_at"`
	UpdatedAt time.Time  `json:"updated_at"`
	ClosedAt  *time.Time `json:"closed_at,omitempty"`
}

// IssueLabel represents a label for categorizing issues
type IssueLabel struct {
	ID           types.ID `json:"id"`
	RepositoryID types.ID `json:"repository_id"`

	Name        string `json:"name"`
	DisplayName string `json:"display_name,omitempty"`
	Description string `json:"description,omitempty"`
	Color       string `json:"color,omitempty"` // Hex color

	Category string `json:"category,omitempty"` // type, priority, system, location, custom

	// Auto-apply rules
	AutoApplyEquipmentType string `json:"auto_apply_equipment_type,omitempty"`
	AutoApplyIssueType     string `json:"auto_apply_issue_type,omitempty"`

	UsageCount int `json:"usage_count"`

	CreatedAt time.Time `json:"created_at"`
	CreatedBy *types.ID `json:"created_by,omitempty"`
}

// IssueCommentType represents types of issue comments
type IssueCommentType string

const (
	IssueCommentTypeComment      IssueCommentType = "comment"
	IssueCommentTypeStatusUpdate IssueCommentType = "status_update"
	IssueCommentTypeAssignment   IssueCommentType = "assignment"
	IssueCommentTypeResolution   IssueCommentType = "resolution"
	IssueCommentTypeVerification IssueCommentType = "verification"
)

// IssueComment represents a comment on an issue
type IssueComment struct {
	ID          types.ID         `json:"id"`
	IssueID     types.ID         `json:"issue_id"`
	Body        string           `json:"body"`
	CommentType IssueCommentType `json:"comment_type"`

	ParentCommentID *types.ID `json:"parent_comment_id,omitempty"`

	AuthorID  types.ID       `json:"author_id"`
	Reactions map[string]int `json:"reactions,omitempty"`

	CreatedAt time.Time `json:"created_at"`
	UpdatedAt time.Time `json:"updated_at"`
	Edited    bool      `json:"edited"`
}

// PhotoType represents the type/purpose of a photo
type PhotoType string

const (
	PhotoTypeProblem        PhotoType = "problem"
	PhotoTypeBefore         PhotoType = "before"
	PhotoTypeDuring         PhotoType = "during"
	PhotoTypeAfter          PhotoType = "after"
	PhotoTypeContext        PhotoType = "context"
	PhotoTypeEquipmentLabel PhotoType = "equipment_label"
)

// IssuePhoto represents a photo attached to an issue
type IssuePhoto struct {
	ID      types.ID `json:"id"`
	IssueID types.ID `json:"issue_id"`

	Filename string `json:"filename"`
	FilePath string `json:"file_path"`
	FileSize int64  `json:"file_size"`
	MimeType string `json:"mime_type,omitempty"`

	// Capture metadata (from mobile)
	CapturedLocation *Location  `json:"captured_location,omitempty"`
	CapturedAt       *time.Time `json:"captured_at,omitempty"`
	DeviceInfo       string     `json:"device_info,omitempty"`

	PhotoType PhotoType `json:"photo_type"`
	Caption   string    `json:"caption,omitempty"`

	UploadedBy types.ID  `json:"uploaded_by"`
	UploadedAt time.Time `json:"uploaded_at"`
}

// IssueActivityType represents types of issue activity
type IssueActivityType string

const (
	IssueActivityCreated         IssueActivityType = "created"
	IssueActivityAssigned        IssueActivityType = "assigned"
	IssueActivityStatusChanged   IssueActivityType = "status_changed"
	IssueActivityPriorityChanged IssueActivityType = "priority_changed"
	IssueActivityLabeled         IssueActivityType = "labeled"
	IssueActivityUnlabeled       IssueActivityType = "unlabeled"
	IssueActivityCommented       IssueActivityType = "commented"
	IssueActivityBranchCreated   IssueActivityType = "branch_created"
	IssueActivityPRCreated       IssueActivityType = "pr_created"
	IssueActivityPRMerged        IssueActivityType = "pr_merged"
	IssueActivityResolved        IssueActivityType = "resolved"
	IssueActivityVerified        IssueActivityType = "verified"
	IssueActivityClosed          IssueActivityType = "closed"
	IssueActivityReopened        IssueActivityType = "reopened"
)

// IssueActivity represents an activity event on an issue
type IssueActivity struct {
	ID           types.ID          `json:"id"`
	IssueID      types.ID          `json:"issue_id"`
	ActivityType IssueActivityType `json:"activity_type"`

	Details  string                 `json:"details,omitempty"`
	Metadata map[string]interface{} `json:"metadata,omitempty"`

	ActorID    *types.ID `json:"actor_id,omitempty"`
	OccurredAt time.Time `json:"occurred_at"`
}

// Request/Response DTOs

// CreateIssueRequest represents a request to create an issue
type CreateIssueRequest struct {
	RepositoryID types.ID `json:"repository_id" validate:"required"`
	Title        string   `json:"title" validate:"required"`
	Body         string   `json:"body,omitempty"`

	// Spatial context
	BuildingID  *types.ID `json:"building_id,omitempty"`
	FloorID     *types.ID `json:"floor_id,omitempty"`
	RoomID      *types.ID `json:"room_id,omitempty"`
	EquipmentID *types.ID `json:"equipment_id,omitempty"`
	BASPointID  *types.ID `json:"bas_point_id,omitempty"`

	Location            *Location `json:"location,omitempty"`
	LocationDescription string    `json:"location_description,omitempty"`

	IssueType IssueType     `json:"issue_type"`
	Priority  IssuePriority `json:"priority"`

	Labels []string `json:"labels,omitempty"`

	ReportedBy  types.ID     `json:"reported_by" validate:"required"`
	ReportedVia *ReportedVia `json:"reported_via,omitempty"`
}

// UpdateIssueRequest represents a request to update an issue
type UpdateIssueRequest struct {
	ID         types.ID       `json:"id" validate:"required"`
	Title      *string        `json:"title,omitempty"`
	Body       *string        `json:"body,omitempty"`
	Status     *IssueStatus   `json:"status,omitempty"`
	Priority   *IssuePriority `json:"priority,omitempty"`
	AssignedTo *types.ID      `json:"assigned_to,omitempty"`
	Labels     []string       `json:"labels,omitempty"`
}

// ResolveIssueRequest represents a request to resolve an issue
type ResolveIssueRequest struct {
	IssueID         types.ID `json:"issue_id" validate:"required"`
	ResolvedBy      types.ID `json:"resolved_by" validate:"required"`
	ResolutionNotes string   `json:"resolution_notes"`
}

// VerifyIssueRequest represents reporter verification of fix
type VerifyIssueRequest struct {
	IssueID     types.ID `json:"issue_id" validate:"required"`
	VerifiedBy  types.ID `json:"verified_by" validate:"required"`
	Confirmed   bool     `json:"confirmed"` // true = fixed, false = still broken
	VerifyNotes string   `json:"verify_notes,omitempty"`
}

// AddIssueCommentRequest represents a request to add a comment
type AddIssueCommentRequest struct {
	IssueID         types.ID  `json:"issue_id" validate:"required"`
	Body            string    `json:"body" validate:"required"`
	AuthorID        types.ID  `json:"author_id" validate:"required"`
	ParentCommentID *types.ID `json:"parent_comment_id,omitempty"`
}

// AttachIssuePhotoRequest represents a request to attach a photo
type AttachIssuePhotoRequest struct {
	IssueID   types.ID  `json:"issue_id" validate:"required"`
	Filename  string    `json:"filename" validate:"required"`
	FilePath  string    `json:"file_path" validate:"required"`
	FileSize  int64     `json:"file_size" validate:"required"`
	PhotoType PhotoType `json:"photo_type"`
	Caption   string    `json:"caption,omitempty"`

	CapturedLocation *Location  `json:"captured_location,omitempty"`
	CapturedAt       *time.Time `json:"captured_at,omitempty"`
	DeviceInfo       string     `json:"device_info,omitempty"`

	UploadedBy types.ID `json:"uploaded_by" validate:"required"`
}

// IssueFilter represents filters for querying issues
type IssueFilter struct {
	RepositoryID *types.ID      `json:"repository_id,omitempty"`
	Status       *IssueStatus   `json:"status,omitempty"`
	IssueType    *IssueType     `json:"issue_type,omitempty"`
	Priority     *IssuePriority `json:"priority,omitempty"`
	AssignedTo   *types.ID      `json:"assigned_to,omitempty"`
	ReportedBy   *types.ID      `json:"reported_by,omitempty"`
	BuildingID   *types.ID      `json:"building_id,omitempty"`
	RoomID       *types.ID      `json:"room_id,omitempty"`
	EquipmentID  *types.ID      `json:"equipment_id,omitempty"`
	Label        string         `json:"label,omitempty"`
	ReportedVia  *ReportedVia   `json:"reported_via,omitempty"`
	Unverified   bool           `json:"unverified,omitempty"` // Resolved but not verified
}

// Repository Interfaces

// IssueRepository defines the interface for issue data access
type IssueRepository interface {
	// CRUD operations
	Create(issue *Issue) error
	GetByID(id types.ID) (*Issue, error)
	GetByNumber(repositoryID types.ID, number int) (*Issue, error)
	Update(issue *Issue) error
	Delete(id types.ID) error

	// Query operations
	List(filter IssueFilter, limit, offset int) ([]*Issue, error)
	Count(filter IssueFilter) (int, error)
	ListOpen(repositoryID types.ID) ([]*Issue, error)
	ListAssigned(userID types.ID) ([]*Issue, error)
	ListByRoom(roomID types.ID) ([]*Issue, error)
	ListByEquipment(equipmentID types.ID) ([]*Issue, error)
	ListUnverified(repositoryID types.ID) ([]*Issue, error)

	// Status operations
	UpdateStatus(id types.ID, status IssueStatus) error
	Resolve(id types.ID, resolvedBy types.ID, notes string) error
	Verify(id types.ID, verifiedBy types.ID) error
	Close(id types.ID) error
	Reopen(id types.ID) error
}

// IssueLabelRepository defines the interface for label management
type IssueLabelRepository interface {
	Create(label *IssueLabel) error
	GetByID(id types.ID) (*IssueLabel, error)
	GetByName(repositoryID types.ID, name string) (*IssueLabel, error)
	Update(label *IssueLabel) error
	Delete(id types.ID) error
	List(repositoryID types.ID) ([]*IssueLabel, error)

	// Label assignment
	AddLabelToIssue(issueID, labelID types.ID) error
	RemoveLabelFromIssue(issueID, labelID types.ID) error
	GetIssueLabels(issueID types.ID) ([]*IssueLabel, error)
}

// IssueCommentRepository defines the interface for comment management
type IssueCommentRepository interface {
	Create(comment *IssueComment) error
	GetByID(id types.ID) (*IssueComment, error)
	Update(comment *IssueComment) error
	Delete(id types.ID) error
	List(issueID types.ID) ([]*IssueComment, error)
}

// IssuePhotoRepository defines the interface for photo management
type IssuePhotoRepository interface {
	Attach(photo *IssuePhoto) error
	List(issueID types.ID) ([]*IssuePhoto, error)
	Delete(id types.ID) error
}

// IssueActivityRepository defines the interface for activity logging
type IssueActivityRepository interface {
	Log(activity *IssueActivity) error
	List(issueID types.ID, limit int) ([]*IssueActivity, error)
}
