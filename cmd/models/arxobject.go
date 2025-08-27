package models

import "time"

// ArxObjectMetadata represents an ArxObject in the system
type ArxObjectMetadata struct {
	ID               string                 `json:"id"`
	Name             string                 `json:"name"`
	Type             string                 `json:"type"`
	Description      string                 `json:"description,omitempty"`
	Parent           string                 `json:"parent,omitempty"`
	Children         []string               `json:"children,omitempty"`
	Status           string                 `json:"status"`
	Created          time.Time              `json:"created"`
	Updated          time.Time              `json:"updated"`
	Location         *Location              `json:"location,omitempty"`
	Properties       map[string]interface{} `json:"properties,omitempty"`
	Confidence       float64                `json:"confidence"`
	ValidationStatus string                 `json:"validation_status,omitempty"`
	ValidatedAt      *time.Time             `json:"validated_at,omitempty"`
	Tags             []string               `json:"tags,omitempty"`
	Relationships    []RelationshipMetadata `json:"relationships,omitempty"`
	Validations      []ValidationMetadata   `json:"validations,omitempty"`
	Flags            uint32                 `json:"flags,omitempty"`
	Hash             string                 `json:"hash,omitempty"`
	Version          int                    `json:"version,omitempty"`
	SourceType       string                 `json:"source_type,omitempty"`
	SourceFile       string                 `json:"source_file,omitempty"`
	SourcePage       int                    `json:"source_page,omitempty"`
}

// Location represents spatial location information
type Location struct {
	Floor    int     `json:"floor,omitempty"`
	Room     string  `json:"room,omitempty"`
	Building string  `json:"building,omitempty"`
	X        float64 `json:"x,omitempty"`
	Y        float64 `json:"y,omitempty"`
	Z        float64 `json:"z,omitempty"`
}

// RelationshipMetadata represents relationships between ArxObjects
type RelationshipMetadata struct {
	ID         string                 `json:"id"`
	Type       string                 `json:"type"`
	TargetID   string                 `json:"target_id"`
	SourceID   string                 `json:"source_id"`
	Properties map[string]interface{} `json:"properties,omitempty"`
	Confidence float64                `json:"confidence"`
	CreatedAt  time.Time              `json:"created_at"`
	Direction  string                 `json:"direction,omitempty"` // "incoming", "outgoing", "bidirectional"
}

// ValidationMetadata represents validation records for ArxObjects
type ValidationMetadata struct {
	ID          string                 `json:"id"`
	Timestamp   time.Time              `json:"timestamp"`
	ValidatedBy string                 `json:"validated_by"`
	Method      string                 `json:"method"`
	Evidence    map[string]interface{} `json:"evidence,omitempty"`
	Confidence  float64                `json:"confidence"`
	Notes       string                 `json:"notes,omitempty"`
	Status      string                 `json:"status"` // "pending", "approved", "rejected"
}