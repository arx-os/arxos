// Package sync contains shared synchronization types
package sync

import (
	"time"
)

// Change represents a data change
type Change struct {
	ID        string                 `json:"id"`
	ChangeID  string                 `json:"change_id"` // Alias for ID for compatibility
	Type      string                 `json:"type"`      // create, update, delete
	Entity    string                 `json:"entity"`    // building, equipment, room
	EntityID  string                 `json:"entity_id"`
	Data      map[string]interface{} `json:"data"`
	Timestamp time.Time              `json:"timestamp"`
	UserID    string                 `json:"user_id"`
	Version   int                    `json:"version,omitempty"`
}

// GetChangeID returns the change ID
func (c *Change) GetChangeID() string {
	if c.ChangeID != "" {
		return c.ChangeID
	}
	return c.ID
}

// Conflict represents a sync conflict
type Conflict struct {
	ID            string                 `json:"id"`
	Entity        string                 `json:"entity"`
	EntityID      string                 `json:"entity_id"`
	ConflictType  string                 `json:"conflict_type"`
	LocalVersion  int                    `json:"local_version"`
	RemoteVersion int                    `json:"remote_version"`
	LocalData     map[string]interface{} `json:"local_data"`
	RemoteData    map[string]interface{} `json:"remote_data"`
	LocalChange   *Change                `json:"local_change,omitempty"`
	RemoteChange  *Change                `json:"remote_change,omitempty"`
	Resolution    string                 `json:"resolution"`
	ResolvedBy    string                 `json:"resolved_by,omitempty"`
	CreatedAt     time.Time              `json:"created_at"`
	ResolvedAt    *time.Time             `json:"resolved_at,omitempty"`
}

// SyncRequest represents a synchronization request
type SyncRequest struct {
	BuildingID string                 `json:"building_id"`
	Changes    []Change               `json:"changes"`
	LastSync   time.Time              `json:"last_sync"`
	Metadata   map[string]interface{} `json:"metadata"`
}

// SyncResponse represents a synchronization response
type SyncResponse struct {
	Success         bool             `json:"success"`
	Message         string           `json:"message,omitempty"`
	AppliedChanges  []Change         `json:"applied_changes,omitempty"`
	RejectedChanges []RejectedChange `json:"rejected_changes,omitempty"`
	Conflicts       []Conflict       `json:"conflicts,omitempty"`
}

// RejectedChange represents a change that was rejected during sync
type RejectedChange struct {
	Change Change `json:"change"`
	Reason string `json:"reason"`
}
