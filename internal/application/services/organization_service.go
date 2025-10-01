package services

import (
	"context"
	"fmt"

	"github.com/arx-os/arxos/internal/domain/organization"
	"github.com/arx-os/arxos/internal/interfaces/http/models"
	domainmodels "github.com/arx-os/arxos/pkg/models"
)

// OrganizationApplicationService provides application-level organization operations
type OrganizationApplicationService struct {
	organizationService organization.Service
}

// NewOrganizationApplicationService creates a new organization application service
func NewOrganizationApplicationService(organizationService organization.Service) *OrganizationApplicationService {
	return &OrganizationApplicationService{
		organizationService: organizationService,
	}
}

// ListOrganizations retrieves a list of organizations with filtering and pagination
func (s *OrganizationApplicationService) ListOrganizations(ctx context.Context, filter models.OrganizationFilter, limit, offset int) ([]*domainmodels.Organization, error) {
	// Convert filter to domain format
	domainFilter := organization.Filter{
		Plan:   filter.Plan,
		Active: filter.Active,
	}

	// Call domain service
	organizations, err := s.organizationService.ListOrganizations(ctx, domainFilter)
	if err != nil {
		return nil, fmt.Errorf("failed to list organizations: %w", err)
	}

	// Apply pagination
	start := offset
	end := offset + limit
	if start >= len(organizations) {
		return []*models.Organization{}, nil
	}
	if end > len(organizations) {
		end = len(organizations)
	}

	return organizations[start:end], nil
}

// GetOrganization retrieves an organization by ID
func (s *OrganizationApplicationService) GetOrganization(ctx context.Context, orgID string) (*domainmodels.Organization, error) {
	organization, err := s.organizationService.GetOrganization(ctx, orgID)
	if err != nil {
		return nil, fmt.Errorf("failed to get organization: %w", err)
	}

	return organization, nil
}

// CreateOrganization creates a new organization
func (s *OrganizationApplicationService) CreateOrganization(ctx context.Context, req models.CreateOrganizationRequest) (*domainmodels.Organization, error) {
	// Convert request to domain format
	createReq := organization.CreateOrganizationRequest{
		Name:        req.Name,
		Description: req.Description,
		Plan:        req.Plan,
		IsActive:    req.IsActive,
		Metadata:    req.Metadata,
	}

	// Call domain service
	organization, err := s.organizationService.CreateOrganization(ctx, createReq)
	if err != nil {
		return nil, fmt.Errorf("failed to create organization: %w", err)
	}

	return organization, nil
}

// UpdateOrganization updates an existing organization
func (s *OrganizationApplicationService) UpdateOrganization(ctx context.Context, orgID string, req models.UpdateOrganizationRequest) (*domainmodels.Organization, error) {
	// Convert request to domain format
	updateReq := organization.UpdateOrganizationRequest{
		Name:        req.Name,
		Description: req.Description,
		Plan:        req.Plan,
		IsActive:    req.IsActive,
		Metadata:    req.Metadata,
	}

	// Call domain service
	organization, err := s.organizationService.UpdateOrganization(ctx, orgID, updateReq)
	if err != nil {
		return nil, fmt.Errorf("failed to update organization: %w", err)
	}

	return organization, nil
}

// DeleteOrganization deletes an organization
func (s *OrganizationApplicationService) DeleteOrganization(ctx context.Context, orgID string) error {
	err := s.organizationService.DeleteOrganization(ctx, orgID)
	if err != nil {
		return fmt.Errorf("failed to delete organization: %w", err)
	}

	return nil
}

// GetOrganizationUsers retrieves users for an organization
func (s *OrganizationApplicationService) GetOrganizationUsers(ctx context.Context, orgID string, limit, offset int) ([]*domainmodels.User, error) {
	users, err := s.organizationService.GetOrganizationUsers(ctx, orgID)
	if err != nil {
		return nil, fmt.Errorf("failed to get organization users: %w", err)
	}

	// Apply pagination
	start := offset
	end := offset + limit
	if start >= len(users) {
		return []*models.User{}, nil
	}
	if end > len(users) {
		end = len(users)
	}

	return users[start:end], nil
}

// AddUserToOrganization adds a user to an organization
func (s *OrganizationApplicationService) AddUserToOrganization(ctx context.Context, orgID, userID string) error {
	err := s.organizationService.AddUserToOrganization(ctx, orgID, userID)
	if err != nil {
		return fmt.Errorf("failed to add user to organization: %w", err)
	}

	return nil
}

// RemoveUserFromOrganization removes a user from an organization
func (s *OrganizationApplicationService) RemoveUserFromOrganization(ctx context.Context, orgID, userID string) error {
	err := s.organizationService.RemoveUserFromOrganization(ctx, orgID, userID)
	if err != nil {
		return fmt.Errorf("failed to remove user from organization: %w", err)
	}

	return nil
}
