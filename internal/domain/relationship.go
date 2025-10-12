package domain

import (
	"context"
	"time"

	"github.com/arx-os/arxos/internal/domain/types"
)

// ItemRelationship represents a relationship between two items (equipment)
type ItemRelationship struct {
	ID               types.ID       `json:"id"`
	FromItemID       types.ID       `json:"from_item_id"`
	ToItemID         types.ID       `json:"to_item_id"`
	RelationshipType string         `json:"relationship_type"`
	Properties       map[string]any `json:"properties,omitempty"`
	Strength         float64        `json:"strength"` // 0-1 scale
	Bidirectional    bool           `json:"bidirectional"`
	CreatedAt        time.Time      `json:"created_at"`
	UpdatedAt        time.Time      `json:"updated_at"`
	CreatedBy        string         `json:"created_by,omitempty"`
}

// RelationshipType constants for common relationships
const (
	RelationshipTypeFeeds      = "feeds"       // Power/fluid flow
	RelationshipTypeControls   = "controls"    // Control relationship
	RelationshipTypeContains   = "contains"    // Spatial containment
	RelationshipTypeParentOf   = "parent_of"   // Hierarchical parent
	RelationshipTypeConnectsTo = "connects_to" // Physical connection
	RelationshipTypePowers     = "powers"      // Electrical power
	RelationshipTypeCools      = "cools"       // Cooling relationship
	RelationshipTypeMonitors   = "monitors"    // Monitoring relationship
	RelationshipTypeServes     = "serves"      // Service relationship
	RelationshipTypeUplink     = "uplink"      // Network uplink
)

// CreateRelationshipRequest represents a request to create a relationship
type CreateRelationshipRequest struct {
	FromItemID       types.ID       `json:"from_item_id" validate:"required"`
	ToItemID         types.ID       `json:"to_item_id" validate:"required"`
	RelationshipType string         `json:"relationship_type" validate:"required"`
	Properties       map[string]any `json:"properties,omitempty"`
	Strength         float64        `json:"strength,omitempty"`
	Bidirectional    bool           `json:"bidirectional,omitempty"`
	CreatedBy        string         `json:"created_by,omitempty"`
}

// RelationshipFilter represents filters for relationship queries
type RelationshipFilter struct {
	FromItemID       *types.ID `json:"from_item_id,omitempty"`
	ToItemID         *types.ID `json:"to_item_id,omitempty"`
	RelationshipType *string   `json:"relationship_type,omitempty"`
	Bidirectional    *bool     `json:"bidirectional,omitempty"`
	Limit            int       `json:"limit,omitempty"`
	Offset           int       `json:"offset,omitempty"`
}

// HierarchyNode represents a node in an equipment hierarchy
type HierarchyNode struct {
	Item         *Equipment        `json:"item"`
	Children     []*HierarchyNode  `json:"children,omitempty"`
	Relationship *ItemRelationship `json:"relationship,omitempty"`
	Depth        int               `json:"depth"`
}

// RelationshipRepository defines the interface for relationship persistence
type RelationshipRepository interface {
	// Create and manage relationships
	Create(ctx context.Context, req *CreateRelationshipRequest) (*ItemRelationship, error)
	GetByID(ctx context.Context, id string) (*ItemRelationship, error)
	List(ctx context.Context, filter *RelationshipFilter) ([]*ItemRelationship, error)
	Delete(ctx context.Context, id string) error

	// Graph traversal
	GetUpstream(ctx context.Context, itemID types.ID, relType string, depth int) ([]*ItemRelationship, error)
	GetDownstream(ctx context.Context, itemID types.ID, relType string, depth int) ([]*ItemRelationship, error)
	GetPath(ctx context.Context, fromID, toID types.ID) ([]*ItemRelationship, error)

	// Bulk operations
	CreateBulk(ctx context.Context, relationships []*CreateRelationshipRequest) ([]*ItemRelationship, error)
	DeleteByItem(ctx context.Context, itemID types.ID) error
}
