package component

import (
	"context"
)

// ComponentRepository defines the interface for component persistence
type ComponentRepository interface {
	// Create creates a new component
	Create(ctx context.Context, component *Component) error

	// GetByID retrieves a component by ID
	GetByID(ctx context.Context, id string) (*Component, error)

	// GetByPath retrieves a component by path
	GetByPath(ctx context.Context, path string) (*Component, error)

	// GetByType retrieves components by type
	GetByType(ctx context.Context, compType ComponentType) ([]*Component, error)

	// GetByLocation retrieves components within a location range
	GetByLocation(ctx context.Context, location Location, radius float64) ([]*Component, error)

	// Update updates an existing component
	Update(ctx context.Context, component *Component) error

	// Delete deletes a component by ID
	Delete(ctx context.Context, id string) error

	// List retrieves components with pagination and filtering
	List(ctx context.Context, filter ComponentFilter) ([]*Component, error)

	// Count returns the total count of components matching the filter
	Count(ctx context.Context, filter ComponentFilter) (int64, error)
}

// ComponentFilter defines filtering criteria for component queries
type ComponentFilter struct {
	Type       *ComponentType   `json:"type,omitempty"`
	Status     *ComponentStatus `json:"status,omitempty"`
	Building   string           `json:"building,omitempty"`
	Floor      string           `json:"floor,omitempty"`
	Room       string           `json:"room,omitempty"`
	PathPrefix string           `json:"path_prefix,omitempty"`
	CreatedBy  string           `json:"created_by,omitempty"`
	Limit      int              `json:"limit,omitempty"`
	Offset     int              `json:"offset,omitempty"`
}

// ComponentService defines the business logic interface for components
type ComponentService interface {
	// CreateComponent creates a new component with validation
	CreateComponent(ctx context.Context, req CreateComponentRequest) (*Component, error)

	// GetComponent retrieves a component by ID or path
	GetComponent(ctx context.Context, identifier string) (*Component, error)

	// UpdateComponent updates an existing component
	UpdateComponent(ctx context.Context, req UpdateComponentRequest) (*Component, error)

	// DeleteComponent deletes a component
	DeleteComponent(ctx context.Context, id string) error

	// ListComponents retrieves components with filtering
	ListComponents(ctx context.Context, filter ComponentFilter) ([]*Component, error)

	// AddProperty adds a property to a component
	AddProperty(ctx context.Context, componentID, key string, value any) error

	// RemoveProperty removes a property from a component
	RemoveProperty(ctx context.Context, componentID, key string) error

	// AddRelation adds a relation between components
	AddRelation(ctx context.Context, req AddRelationRequest) error

	// RemoveRelation removes a relation between components
	RemoveRelation(ctx context.Context, componentID, relationID string) error

	// UpdateStatus updates the status of a component
	UpdateStatus(ctx context.Context, componentID string, status ComponentStatus, updatedBy string) error

	// GetComponentsByRelation retrieves components related to a given component
	GetComponentsByRelation(ctx context.Context, componentID string, relationType RelationType) ([]*Component, error)
}

// CreateComponentRequest represents a request to create a new component
type CreateComponentRequest struct {
	Name       string         `json:"name" validate:"required"`
	Type       ComponentType  `json:"type" validate:"required"`
	Path       string         `json:"path" validate:"required"`
	Location   Location       `json:"location"`
	Properties map[string]any `json:"properties,omitempty"`
	CreatedBy  string         `json:"created_by" validate:"required"`
}

// UpdateComponentRequest represents a request to update a component
type UpdateComponentRequest struct {
	ID         string           `json:"id" validate:"required"`
	Name       *string          `json:"name,omitempty"`
	Path       *string          `json:"path,omitempty"`
	Location   *Location        `json:"location,omitempty"`
	Properties map[string]any   `json:"properties,omitempty"`
	Status     *ComponentStatus `json:"status,omitempty"`
	UpdatedBy  string           `json:"updated_by" validate:"required"`
}

// AddRelationRequest represents a request to add a relation between components
type AddRelationRequest struct {
	SourceComponentID string         `json:"source_component_id" validate:"required"`
	RelationType      RelationType   `json:"relation_type" validate:"required"`
	TargetComponentID string         `json:"target_component_id" validate:"required"`
	Properties        map[string]any `json:"properties,omitempty"`
	CreatedBy         string         `json:"created_by" validate:"required"`
}
