package usecase

import (
	"context"
	"fmt"
	"strings"
	"time"

	"github.com/arx-os/arxos/internal/domain/component"
	"github.com/google/uuid"
)

// ComponentUseCase implements component.ComponentService
type ComponentUseCase struct {
	componentRepo component.ComponentRepository
}

// NewComponentUseCase creates a new component use case
func NewComponentUseCase(componentRepo component.ComponentRepository) component.ComponentService {
	return &ComponentUseCase{
		componentRepo: componentRepo,
	}
}

// CreateComponent creates a new component with validation
func (uc *ComponentUseCase) CreateComponent(ctx context.Context, req component.CreateComponentRequest) (*component.Component, error) {
	// Validate request
	if err := uc.validateCreateRequest(req); err != nil {
		return nil, fmt.Errorf("validation failed: %w", err)
	}

	// Check if component with same path already exists
	existing, err := uc.componentRepo.GetByPath(ctx, req.Path)
	if err == nil && existing != nil {
		return nil, fmt.Errorf("component with path '%s' already exists", req.Path)
	}

	// Generate unique ID
	id := uuid.New().String()

	// Create component
	comp := &component.Component{
		ID:         id,
		Name:       req.Name,
		Type:       req.Type,
		Path:       req.Path,
		Location:   req.Location,
		Properties: req.Properties,
		Relations:  []component.Relation{},
		Status:     component.ComponentStatusActive,
		Version:    "1.0.0",
		CreatedAt:  time.Now(),
		UpdatedAt:  time.Now(),
		CreatedBy:  req.CreatedBy,
		UpdatedBy:  req.CreatedBy,
	}

	// Save to repository
	if err := uc.componentRepo.Create(ctx, comp); err != nil {
		return nil, fmt.Errorf("failed to create component: %w", err)
	}

	return comp, nil
}

// GetComponent retrieves a component by ID or path
func (uc *ComponentUseCase) GetComponent(ctx context.Context, identifier string) (*component.Component, error) {
	if identifier == "" {
		return nil, fmt.Errorf("identifier cannot be empty")
	}

	// Try to get by ID first (UUID format)
	if uc.isUUID(identifier) {
		comp, err := uc.componentRepo.GetByID(ctx, identifier)
		if err == nil {
			return comp, nil
		}
	}

	// Try to get by path
	comp, err := uc.componentRepo.GetByPath(ctx, identifier)
	if err != nil {
		return nil, fmt.Errorf("component not found: %w", err)
	}

	return comp, nil
}

// UpdateComponent updates an existing component
func (uc *ComponentUseCase) UpdateComponent(ctx context.Context, req component.UpdateComponentRequest) (*component.Component, error) {
	// Validate request
	if err := uc.validateUpdateRequest(req); err != nil {
		return nil, fmt.Errorf("validation failed: %w", err)
	}

	// Get existing component
	comp, err := uc.componentRepo.GetByID(ctx, req.ID)
	if err != nil {
		return nil, fmt.Errorf("component not found: %w", err)
	}

	// Update fields if provided
	if req.Name != nil {
		comp.Name = *req.Name
	}
	if req.Path != nil {
		// Check if new path conflicts with existing component
		if *req.Path != comp.Path {
			existing, err := uc.componentRepo.GetByPath(ctx, *req.Path)
			if err == nil && existing != nil && existing.ID != comp.ID {
				return nil, fmt.Errorf("component with path '%s' already exists", *req.Path)
			}
		}
		comp.Path = *req.Path
	}
	if req.Location != nil {
		comp.Location = *req.Location
	}
	if req.Status != nil {
		comp.Status = *req.Status
	}
	if req.Properties != nil {
		comp.Properties = req.Properties
	}

	comp.UpdatedBy = req.UpdatedBy
	comp.UpdatedAt = time.Now()

	// Save to repository
	if err := uc.componentRepo.Update(ctx, comp); err != nil {
		return nil, fmt.Errorf("failed to update component: %w", err)
	}

	return comp, nil
}

// DeleteComponent deletes a component
func (uc *ComponentUseCase) DeleteComponent(ctx context.Context, id string) error {
	if id == "" {
		return fmt.Errorf("component ID cannot be empty")
	}

	// Check if component exists
	_, err := uc.componentRepo.GetByID(ctx, id)
	if err != nil {
		return fmt.Errorf("component not found: %w", err)
	}

	// Delete from repository
	if err := uc.componentRepo.Delete(ctx, id); err != nil {
		return fmt.Errorf("failed to delete component: %w", err)
	}

	return nil
}

// ListComponents retrieves components with filtering
func (uc *ComponentUseCase) ListComponents(ctx context.Context, filter component.ComponentFilter) ([]*component.Component, error) {
	components, err := uc.componentRepo.List(ctx, filter)
	if err != nil {
		return nil, fmt.Errorf("failed to list components: %w", err)
	}

	return components, nil
}

// AddProperty adds a property to a component
func (uc *ComponentUseCase) AddProperty(ctx context.Context, componentID, key string, value interface{}) error {
	if componentID == "" || key == "" {
		return fmt.Errorf("component ID and property key cannot be empty")
	}

	// Get component
	comp, err := uc.componentRepo.GetByID(ctx, componentID)
	if err != nil {
		return fmt.Errorf("component not found: %w", err)
	}

	// Add property
	comp.AddProperty(key, value)

	// Save to repository
	if err := uc.componentRepo.Update(ctx, comp); err != nil {
		return fmt.Errorf("failed to update component: %w", err)
	}

	return nil
}

// RemoveProperty removes a property from a component
func (uc *ComponentUseCase) RemoveProperty(ctx context.Context, componentID, key string) error {
	if componentID == "" || key == "" {
		return fmt.Errorf("component ID and property key cannot be empty")
	}

	// Get component
	comp, err := uc.componentRepo.GetByID(ctx, componentID)
	if err != nil {
		return fmt.Errorf("component not found: %w", err)
	}

	// Remove property
	if comp.Properties != nil {
		delete(comp.Properties, key)
		comp.UpdatedAt = time.Now()
	}

	// Save to repository
	if err := uc.componentRepo.Update(ctx, comp); err != nil {
		return fmt.Errorf("failed to update component: %w", err)
	}

	return nil
}

// AddRelation adds a relation between components
func (uc *ComponentUseCase) AddRelation(ctx context.Context, req component.AddRelationRequest) error {
	// Validate request
	if err := uc.validateAddRelationRequest(req); err != nil {
		return fmt.Errorf("validation failed: %w", err)
	}

	// Get source component
	sourceComp, err := uc.componentRepo.GetByID(ctx, req.SourceComponentID)
	if err != nil {
		return fmt.Errorf("source component not found: %w", err)
	}

	// Get target component
	targetComp, err := uc.componentRepo.GetByID(ctx, req.TargetComponentID)
	if err != nil {
		return fmt.Errorf("target component not found: %w", err)
	}

	// Add relation to source component
	sourceComp.AddRelation(req.RelationType, req.TargetComponentID, targetComp.Path, req.Properties)

	// Save source component
	if err := uc.componentRepo.Update(ctx, sourceComp); err != nil {
		return fmt.Errorf("failed to update source component: %w", err)
	}

	return nil
}

// RemoveRelation removes a relation between components
func (uc *ComponentUseCase) RemoveRelation(ctx context.Context, componentID, relationID string) error {
	if componentID == "" || relationID == "" {
		return fmt.Errorf("component ID and relation ID cannot be empty")
	}

	// Get component
	comp, err := uc.componentRepo.GetByID(ctx, componentID)
	if err != nil {
		return fmt.Errorf("component not found: %w", err)
	}

	// Find and remove relation
	for i, rel := range comp.Relations {
		if rel.ID == relationID {
			comp.Relations = append(comp.Relations[:i], comp.Relations[i+1:]...)
			comp.UpdatedAt = time.Now()
			break
		}
	}

	// Save to repository
	if err := uc.componentRepo.Update(ctx, comp); err != nil {
		return fmt.Errorf("failed to update component: %w", err)
	}

	return nil
}

// UpdateStatus updates the status of a component
func (uc *ComponentUseCase) UpdateStatus(ctx context.Context, componentID string, status component.ComponentStatus, updatedBy string) error {
	if componentID == "" || updatedBy == "" {
		return fmt.Errorf("component ID and updated by cannot be empty")
	}

	// Get component
	comp, err := uc.componentRepo.GetByID(ctx, componentID)
	if err != nil {
		return fmt.Errorf("component not found: %w", err)
	}

	// Update status
	comp.UpdateStatus(status, updatedBy)

	// Save to repository
	if err := uc.componentRepo.Update(ctx, comp); err != nil {
		return fmt.Errorf("failed to update component: %w", err)
	}

	return nil
}

// GetComponentsByRelation retrieves components related to a given component
func (uc *ComponentUseCase) GetComponentsByRelation(ctx context.Context, componentID string, relationType component.RelationType) ([]*component.Component, error) {
	if componentID == "" {
		return nil, fmt.Errorf("component ID cannot be empty")
	}

	// Get source component
	sourceComp, err := uc.componentRepo.GetByID(ctx, componentID)
	if err != nil {
		return nil, fmt.Errorf("source component not found: %w", err)
	}

	// Find relations of specified type
	var relatedComponents []*component.Component
	for _, rel := range sourceComp.Relations {
		if rel.Type == relationType {
			comp, err := uc.componentRepo.GetByID(ctx, rel.TargetID)
			if err == nil {
				relatedComponents = append(relatedComponents, comp)
			}
		}
	}

	return relatedComponents, nil
}

// Helper methods

func (uc *ComponentUseCase) validateCreateRequest(req component.CreateComponentRequest) error {
	if req.Name == "" {
		return fmt.Errorf("component name is required")
	}
	if req.Type == "" {
		return fmt.Errorf("component type is required")
	}
	if req.Path == "" {
		return fmt.Errorf("component path is required")
	}
	if req.CreatedBy == "" {
		return fmt.Errorf("creator is required")
	}
	if !strings.HasPrefix(req.Path, "/") {
		return fmt.Errorf("component path must start with '/'")
	}
	return nil
}

func (uc *ComponentUseCase) validateUpdateRequest(req component.UpdateComponentRequest) error {
	if req.ID == "" {
		return fmt.Errorf("component ID is required")
	}
	if req.UpdatedBy == "" {
		return fmt.Errorf("updated by is required")
	}
	if req.Path != nil && !strings.HasPrefix(*req.Path, "/") {
		return fmt.Errorf("component path must start with '/'")
	}
	return nil
}

func (uc *ComponentUseCase) validateAddRelationRequest(req component.AddRelationRequest) error {
	if req.SourceComponentID == "" {
		return fmt.Errorf("source component ID is required")
	}
	if req.TargetComponentID == "" {
		return fmt.Errorf("target component ID is required")
	}
	if req.RelationType == "" {
		return fmt.Errorf("relation type is required")
	}
	if req.CreatedBy == "" {
		return fmt.Errorf("creator is required")
	}
	if req.SourceComponentID == req.TargetComponentID {
		return fmt.Errorf("source and target components cannot be the same")
	}
	return nil
}

func (uc *ComponentUseCase) isUUID(str string) bool {
	_, err := uuid.Parse(str)
	return err == nil
}
