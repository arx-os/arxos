package building

import (
	"time"
)

// Version represents a version snapshot of a building repository
// This implements Git-like version control for buildings
type Version struct {
	ID           string          `json:"id"`
	RepositoryID string          `json:"repository_id"`
	Hash         string          `json:"hash"`      // SHA-256 hash of version contents
	Snapshot     string          `json:"snapshot"`  // Hash of building snapshot
	Parent       string          `json:"parent"`    // Parent version hash (empty for initial)
	Parents      []string        `json:"parents"`   // Multiple parents for merges
	Tag          string          `json:"tag"`       // v1.0.0, v1.1.0, etc.
	Message      string          `json:"message"`   // Commit message
	Author       Author          `json:"author"`    // Who made the change
	Timestamp    time.Time       `json:"timestamp"` // When version was created
	Metadata     VersionMetadata `json:"metadata"`  // Additional metadata
}

// Author represents the author of a version
type Author struct {
	Name  string `json:"name"`  // User name
	Email string `json:"email"` // User email
	ID    string `json:"id"`    // User ID
}

// VersionMetadata provides additional version information
type VersionMetadata struct {
	ChangeCount    int        `json:"change_count"`              // Number of changes
	ChangeSummary  Summary    `json:"change_summary"`            // High-level summary
	Source         string     `json:"source"`                    // How created (manual, import, sync)
	SystemVersion  string     `json:"system_version"`            // ArxOS version
	ValidatedAt    *time.Time `json:"validated_at,omitempty"`    // When validated
	ValidationHash string     `json:"validation_hash,omitempty"` // Hash of validation result
}

// VersionDiff represents the differences between two versions
type VersionDiff struct {
	FromVersion string   `json:"from_version"`
	ToVersion   string   `json:"to_version"`
	Changes     []Change `json:"changes"`
	Summary     Summary  `json:"summary"`
}

// Change represents a single change in a version
type Change struct {
	Type     ChangeType `json:"type"`
	Path     string     `json:"path"`
	OldValue string     `json:"old_value,omitempty"`
	NewValue string     `json:"new_value,omitempty"`
	Size     int64      `json:"size"`
	Hash     string     `json:"hash"`
}

// ChangeType represents the type of change
type ChangeType string

const (
	ChangeTypeAdded    ChangeType = "added"
	ChangeTypeModified ChangeType = "modified"
	ChangeTypeDeleted  ChangeType = "deleted"
	ChangeTypeRenamed  ChangeType = "renamed"
)

// Summary provides a high-level summary of changes
type Summary struct {
	TotalChanges  int   `json:"total_changes"`
	FilesAdded    int   `json:"files_added"`
	FilesModified int   `json:"files_modified"`
	FilesDeleted  int   `json:"files_deleted"`
	SizeAdded     int64 `json:"size_added"`
	SizeModified  int64 `json:"size_modified"`
	SizeDeleted   int64 `json:"size_deleted"`
}

// VersionRequest represents a request to create a new version
type VersionRequest struct {
	RepositoryID string `json:"repository_id" validate:"required"`
	Message      string `json:"message" validate:"required"`
	Author       string `json:"author" validate:"required"`
	Tag          string `json:"tag,omitempty"` // Optional tag (e.g., v1.1.0)
}

// VersionComparisonRequest represents a request to compare versions
type VersionComparisonRequest struct {
	RepositoryID string `json:"repository_id" validate:"required"`
	FromVersion  string `json:"from_version" validate:"required"`
	ToVersion    string `json:"to_version" validate:"required"`
}

// VersionRollbackRequest represents a request to rollback to a version
type VersionRollbackRequest struct {
	RepositoryID string `json:"repository_id" validate:"required"`
	Version      string `json:"version" validate:"required"`
	CreateNew    bool   `json:"create_new"` // Whether to create a new version for rollback
}
