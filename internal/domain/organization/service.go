package organization

import (
	"context"
	"fmt"
	"time"

	"github.com/arx-os/arxos/internal/database"
	"github.com/arx-os/arxos/pkg/models"
	"github.com/google/uuid"
)

// Service defines the interface for organization business logic following Clean Architecture principles
type Service interface {
	// Organization management
	CreateOrganization(ctx context.Context, req CreateOrganizationRequest) (*Organization, error)
	GetOrganization(ctx context.Context, id uuid.UUID) (*Organization, error)
	GetOrganizationByName(ctx context.Context, name string) (*Organization, error)
	UpdateOrganization(ctx context.Context, id uuid.UUID, req UpdateOrganizationRequest) (*Organization, error)
	DeleteOrganization(ctx context.Context, id uuid.UUID) error
	ListOrganizations(ctx context.Context, req ListOrganizationsRequest) ([]*Organization, error)

	// Organization members
	AddMember(ctx context.Context, orgID, userID uuid.UUID, role string) error
	RemoveMember(ctx context.Context, orgID, userID uuid.UUID) error
	GetMembers(ctx context.Context, orgID uuid.UUID) ([]*Member, error)
	UpdateMemberRole(ctx context.Context, orgID, userID uuid.UUID, role string) error

	// Legacy methods for backward compatibility
	GetOrganizationLegacy(ctx context.Context, orgID string) (*models.Organization, error)
}

// Organization represents an organization entity
type Organization struct {
	ID          uuid.UUID              `json:"id"`
	Name        string                 `json:"name"`
	Description string                 `json:"description,omitempty"`
	Domain      string                 `json:"domain,omitempty"`
	IsActive    bool                   `json:"is_active"`
	CreatedAt   time.Time              `json:"created_at"`
	UpdatedAt   time.Time              `json:"updated_at"`
	Metadata    map[string]interface{} `json:"metadata,omitempty"`
}

// Member represents an organization member
type Member struct {
	ID             uuid.UUID `json:"id"`
	OrganizationID uuid.UUID `json:"organization_id"`
	UserID         uuid.UUID `json:"user_id"`
	Role           string    `json:"role"`
	JoinedAt       time.Time `json:"joined_at"`
}

// Request types
type CreateOrganizationRequest struct {
	Name        string                 `json:"name" validate:"required"`
	Description string                 `json:"description,omitempty"`
	Domain      string                 `json:"domain,omitempty"`
	Metadata    map[string]interface{} `json:"metadata,omitempty"`
}

type UpdateOrganizationRequest struct {
	Name        *string                `json:"name,omitempty"`
	Description *string                `json:"description,omitempty"`
	Domain      *string                `json:"domain,omitempty"`
	IsActive    *bool                  `json:"is_active,omitempty"`
	Metadata    map[string]interface{} `json:"metadata,omitempty"`
}

type ListOrganizationsRequest struct {
	Active *bool `json:"active,omitempty"`
	Limit  int   `json:"limit" validate:"min=1,max=100"`
	Offset int   `json:"offset" validate:"min=0"`
}

// service implements the organization service following Clean Architecture principles
type service struct {
	db database.DB
}

// NewService creates a new organization service with dependency injection
func NewService(db database.DB) Service {
	return &service{
		db: db,
	}
}

// CreateOrganization creates a new organization
func (s *service) CreateOrganization(ctx context.Context, req CreateOrganizationRequest) (*Organization, error) {
	// Validate request
	if err := s.validateCreateRequest(req); err != nil {
		return nil, fmt.Errorf("validation failed: %w", err)
	}

	// Check if organization with name already exists
	existing, err := s.GetOrganizationByName(ctx, req.Name)
	if err == nil && existing != nil {
		return nil, fmt.Errorf("organization with name %s already exists", req.Name)
	}

	// Create organization entity
	org := &Organization{
		ID:          uuid.New(),
		Name:        req.Name,
		Description: req.Description,
		Domain:      req.Domain,
		IsActive:    true,
		Metadata:    req.Metadata,
		CreatedAt:   time.Now(),
		UpdatedAt:   time.Now(),
	}

	// Validate entity
	if err := s.validateOrganization(org); err != nil {
		return nil, fmt.Errorf("entity validation failed: %w", err)
	}

	// TODO: Save to database
	return org, nil
}

// GetOrganization retrieves an organization by ID
func (s *service) GetOrganization(ctx context.Context, id uuid.UUID) (*Organization, error) {
	// TODO: Implement database lookup
	// For now, return a mock organization
	return &Organization{
		ID:        id,
		Name:      "Test Organization",
		IsActive:  true,
		CreatedAt: time.Now(),
		UpdatedAt: time.Now(),
	}, nil
}

// GetOrganizationByName retrieves an organization by name
func (s *service) GetOrganizationByName(ctx context.Context, name string) (*Organization, error) {
	// TODO: Implement database lookup
	// For now, return nil (organization not found)
	return nil, nil
}

// UpdateOrganization updates an existing organization
func (s *service) UpdateOrganization(ctx context.Context, id uuid.UUID, req UpdateOrganizationRequest) (*Organization, error) {
	// Get existing organization
	org, err := s.GetOrganization(ctx, id)
	if err != nil {
		return nil, fmt.Errorf("failed to get organization: %w", err)
	}
	if org == nil {
		return nil, fmt.Errorf("organization not found")
	}

	// Update fields if provided
	if req.Name != nil {
		org.Name = *req.Name
	}
	if req.Description != nil {
		org.Description = *req.Description
	}
	if req.Domain != nil {
		org.Domain = *req.Domain
	}
	if req.IsActive != nil {
		org.IsActive = *req.IsActive
	}
	if req.Metadata != nil {
		org.Metadata = req.Metadata
	}

	// Set updated timestamp
	org.UpdatedAt = time.Now()

	// Validate entity
	if err := s.validateOrganization(org); err != nil {
		return nil, fmt.Errorf("entity validation failed: %w", err)
	}

	// TODO: Save to database
	return org, nil
}

// DeleteOrganization deletes an organization
func (s *service) DeleteOrganization(ctx context.Context, id uuid.UUID) error {
	// Check if organization exists
	org, err := s.GetOrganization(ctx, id)
	if err != nil {
		return fmt.Errorf("failed to get organization: %w", err)
	}
	if org == nil {
		return fmt.Errorf("organization not found")
	}

	// TODO: Delete from database
	return nil
}

// ListOrganizations lists organizations with pagination
func (s *service) ListOrganizations(ctx context.Context, req ListOrganizationsRequest) ([]*Organization, error) {
	// Validate request
	if err := s.validateListRequest(req); err != nil {
		return nil, fmt.Errorf("validation failed: %w", err)
	}

	// TODO: Implement database query with filters
	// For now, return empty list
	return []*Organization{}, nil
}

// AddMember adds a user to an organization
func (s *service) AddMember(ctx context.Context, orgID, userID uuid.UUID, role string) error {
	// Validate inputs
	if orgID == uuid.Nil {
		return fmt.Errorf("organization ID is required")
	}
	if userID == uuid.Nil {
		return fmt.Errorf("user ID is required")
	}
	if role == "" {
		return fmt.Errorf("role is required")
	}

	// TODO: Implement database operation
	return nil
}

// RemoveMember removes a user from an organization
func (s *service) RemoveMember(ctx context.Context, orgID, userID uuid.UUID) error {
	// Validate inputs
	if orgID == uuid.Nil {
		return fmt.Errorf("organization ID is required")
	}
	if userID == uuid.Nil {
		return fmt.Errorf("user ID is required")
	}

	// TODO: Implement database operation
	return nil
}

// GetMembers retrieves all members of an organization
func (s *service) GetMembers(ctx context.Context, orgID uuid.UUID) ([]*Member, error) {
	// Validate inputs
	if orgID == uuid.Nil {
		return nil, fmt.Errorf("organization ID is required")
	}

	// TODO: Implement database query
	// For now, return empty list
	return []*Member{}, nil
}

// UpdateMemberRole updates a member's role in an organization
func (s *service) UpdateMemberRole(ctx context.Context, orgID, userID uuid.UUID, role string) error {
	// Validate inputs
	if orgID == uuid.Nil {
		return fmt.Errorf("organization ID is required")
	}
	if userID == uuid.Nil {
		return fmt.Errorf("user ID is required")
	}
	if role == "" {
		return fmt.Errorf("role is required")
	}

	// TODO: Implement database operation
	return nil
}

// Legacy methods for backward compatibility

// GetOrganizationLegacy retrieves an organization by string ID (legacy method)
func (s *service) GetOrganizationLegacy(ctx context.Context, orgID string) (*models.Organization, error) {
	// TODO: Implement database lookup
	// For now, return a mock organization
	return &models.Organization{
		ID:   orgID,
		Name: "Test Organization",
	}, nil
}

// Helper methods for validation
func (s *service) validateCreateRequest(req CreateOrganizationRequest) error {
	if req.Name == "" {
		return fmt.Errorf("name is required")
	}
	return nil
}

func (s *service) validateListRequest(req ListOrganizationsRequest) error {
	if req.Limit <= 0 {
		req.Limit = 10 // Default limit
	}
	if req.Limit > 100 {
		return fmt.Errorf("limit cannot exceed 100")
	}
	if req.Offset < 0 {
		req.Offset = 0
	}
	return nil
}

func (s *service) validateOrganization(org *Organization) error {
	if org.Name == "" {
		return fmt.Errorf("name is required")
	}
	return nil
}
