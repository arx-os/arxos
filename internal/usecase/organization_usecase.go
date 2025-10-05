package usecase

import (
	"context"
	"fmt"
	"time"

	"github.com/arx-os/arxos/internal/domain"
	"github.com/arx-os/arxos/internal/infrastructure/utils"
)

// OrganizationUseCase implements the organization business logic following Clean Architecture
type OrganizationUseCase struct {
	organizationRepo domain.OrganizationRepository
	userRepo         domain.UserRepository
	logger           domain.Logger
	idGenerator      *utils.IDGenerator
}

// NewOrganizationUseCase creates a new OrganizationUseCase
func NewOrganizationUseCase(organizationRepo domain.OrganizationRepository, userRepo domain.UserRepository, logger domain.Logger) *OrganizationUseCase {
	return &OrganizationUseCase{
		organizationRepo: organizationRepo,
		userRepo:         userRepo,
		logger:           logger,
		idGenerator:      utils.NewIDGenerator(),
	}
}

// CreateOrganization creates a new organization
func (uc *OrganizationUseCase) CreateOrganization(ctx context.Context, req *domain.CreateOrganizationRequest) (*domain.Organization, error) {
	uc.logger.Info("Creating organization", "name", req.Name)

	// Validate business rules
	if err := uc.validateCreateOrganization(req); err != nil {
		uc.logger.Error("Organization validation failed", "error", err)
		return nil, fmt.Errorf("validation failed: %w", err)
	}

	// Check if organization with same name already exists
	existingOrg, err := uc.organizationRepo.GetByName(ctx, req.Name)
	if err == nil && existingOrg != nil {
		return nil, fmt.Errorf("organization with name %s already exists", req.Name)
	}

	// Create organization entity
	organization := &domain.Organization{
		ID:          uc.idGenerator.GenerateOrganizationID(req.Name),
		Name:        req.Name,
		Description: req.Description,
		Plan:        req.Plan,
		Active:      true,
		CreatedAt:   time.Now(),
		UpdatedAt:   time.Now(),
	}

	// Save to repository
	if err := uc.organizationRepo.Create(ctx, organization); err != nil {
		uc.logger.Error("Failed to create organization", "error", err)
		return nil, fmt.Errorf("failed to create organization: %w", err)
	}

	uc.logger.Info("Organization created successfully", "organization_id", organization.ID)
	return organization, nil
}

// GetOrganization retrieves an organization by ID
func (uc *OrganizationUseCase) GetOrganization(ctx context.Context, id string) (*domain.Organization, error) {
	uc.logger.Info("Getting organization", "organization_id", id)

	if id == "" {
		return nil, fmt.Errorf("organization ID is required")
	}

	organization, err := uc.organizationRepo.GetByID(ctx, id)
	if err != nil {
		uc.logger.Error("Failed to get organization", "organization_id", id, "error", err)
		return nil, fmt.Errorf("failed to get organization: %w", err)
	}

	return organization, nil
}

// UpdateOrganization updates an existing organization
func (uc *OrganizationUseCase) UpdateOrganization(ctx context.Context, req *domain.UpdateOrganizationRequest) (*domain.Organization, error) {
	uc.logger.Info("Updating organization", "organization_id", req.ID)

	// Get existing organization
	organization, err := uc.organizationRepo.GetByID(ctx, req.ID.String())
	if err != nil {
		uc.logger.Error("Failed to get organization for update", "organization_id", req.ID.String(), "error", err)
		return nil, fmt.Errorf("failed to get organization: %w", err)
	}

	// Update fields if provided
	if req.Name != nil {
		organization.Name = *req.Name
	}
	if req.Description != nil {
		organization.Description = *req.Description
	}
	if req.Plan != nil {
		organization.Plan = *req.Plan
	}
	if req.Active != nil {
		organization.Active = *req.Active
	}
	organization.UpdatedAt = time.Now()

	// Validate business rules
	if err := uc.validateUpdateOrganization(organization); err != nil {
		uc.logger.Error("Organization validation failed", "error", err)
		return nil, fmt.Errorf("validation failed: %w", err)
	}

	// Save to repository
	if err := uc.organizationRepo.Update(ctx, organization); err != nil {
		uc.logger.Error("Failed to update organization", "organization_id", req.ID, "error", err)
		return nil, fmt.Errorf("failed to update organization: %w", err)
	}

	uc.logger.Info("Organization updated successfully", "organization_id", organization.ID)
	return organization, nil
}

// DeleteOrganization deletes an organization
func (uc *OrganizationUseCase) DeleteOrganization(ctx context.Context, id string) error {
	uc.logger.Info("Deleting organization", "organization_id", id)

	if id == "" {
		return fmt.Errorf("organization ID is required")
	}

	// Check if organization exists
	_, err := uc.organizationRepo.GetByID(ctx, id)
	if err != nil {
		uc.logger.Error("Failed to get organization for deletion", "organization_id", id, "error", err)
		return fmt.Errorf("failed to get organization: %w", err)
	}

	// Business rule: Check if organization has users
	users, err := uc.organizationRepo.GetUsers(ctx, id)
	if err == nil && len(users) > 0 {
		return fmt.Errorf("cannot delete organization with existing users")
	}

	// Delete from repository
	if err := uc.organizationRepo.Delete(ctx, id); err != nil {
		uc.logger.Error("Failed to delete organization", "organization_id", id, "error", err)
		return fmt.Errorf("failed to delete organization: %w", err)
	}

	uc.logger.Info("Organization deleted successfully", "organization_id", id)
	return nil
}

// ListOrganizations retrieves a list of organizations with optional filtering
func (uc *OrganizationUseCase) ListOrganizations(ctx context.Context, filter *domain.OrganizationFilter) ([]*domain.Organization, error) {
	uc.logger.Info("Listing organizations", "filter", filter)

	// Set default pagination if not provided
	if filter.Limit <= 0 {
		filter.Limit = 100
	}

	organizations, err := uc.organizationRepo.List(ctx, filter)
	if err != nil {
		uc.logger.Error("Failed to list organizations", "error", err)
		return nil, fmt.Errorf("failed to list organizations: %w", err)
	}

	uc.logger.Info("Organizations listed successfully", "count", len(organizations))
	return organizations, nil
}

// AddUserToOrganization adds a user to an organization
func (uc *OrganizationUseCase) AddUserToOrganization(ctx context.Context, orgID, userID string) error {
	uc.logger.Info("Adding user to organization", "organization_id", orgID, "user_id", userID)

	// Validate inputs
	if orgID == "" {
		return fmt.Errorf("organization ID is required")
	}
	if userID == "" {
		return fmt.Errorf("user ID is required")
	}

	// Verify organization exists
	_, err := uc.organizationRepo.GetByID(ctx, orgID)
	if err != nil {
		uc.logger.Error("Failed to verify organization exists", "organization_id", orgID, "error", err)
		return fmt.Errorf("organization not found: %w", err)
	}

	// Verify user exists
	_, err = uc.userRepo.GetByID(ctx, userID)
	if err != nil {
		uc.logger.Error("Failed to verify user exists", "user_id", userID, "error", err)
		return fmt.Errorf("user not found: %w", err)
	}

	// Add user to organization
	if err := uc.organizationRepo.AddUser(ctx, orgID, userID); err != nil {
		uc.logger.Error("Failed to add user to organization", "organization_id", orgID, "user_id", userID, "error", err)
		return fmt.Errorf("failed to add user to organization: %w", err)
	}

	uc.logger.Info("User added to organization successfully", "organization_id", orgID, "user_id", userID)
	return nil
}

// RemoveUserFromOrganization removes a user from an organization
func (uc *OrganizationUseCase) RemoveUserFromOrganization(ctx context.Context, orgID, userID string) error {
	uc.logger.Info("Removing user from organization", "organization_id", orgID, "user_id", userID)

	// Validate inputs
	if orgID == "" {
		return fmt.Errorf("organization ID is required")
	}
	if userID == "" {
		return fmt.Errorf("user ID is required")
	}

	// Verify organization exists
	_, err := uc.organizationRepo.GetByID(ctx, orgID)
	if err != nil {
		uc.logger.Error("Failed to verify organization exists", "organization_id", orgID, "error", err)
		return fmt.Errorf("organization not found: %w", err)
	}

	// Verify user exists
	_, err = uc.userRepo.GetByID(ctx, userID)
	if err != nil {
		uc.logger.Error("Failed to verify user exists", "user_id", userID, "error", err)
		return fmt.Errorf("user not found: %w", err)
	}

	// Remove user from organization
	if err := uc.organizationRepo.RemoveUser(ctx, orgID, userID); err != nil {
		uc.logger.Error("Failed to remove user from organization", "organization_id", orgID, "user_id", userID, "error", err)
		return fmt.Errorf("failed to remove user from organization: %w", err)
	}

	uc.logger.Info("User removed from organization successfully", "organization_id", orgID, "user_id", userID)
	return nil
}

// GetOrganizationUsers retrieves users for an organization
func (uc *OrganizationUseCase) GetOrganizationUsers(ctx context.Context, orgID string) ([]*domain.User, error) {
	uc.logger.Info("Getting organization users", "organization_id", orgID)

	if orgID == "" {
		return nil, fmt.Errorf("organization ID is required")
	}

	// Verify organization exists
	_, err := uc.organizationRepo.GetByID(ctx, orgID)
	if err != nil {
		uc.logger.Error("Failed to verify organization exists", "organization_id", orgID, "error", err)
		return nil, fmt.Errorf("organization not found: %w", err)
	}

	users, err := uc.organizationRepo.GetUsers(ctx, orgID)
	if err != nil {
		uc.logger.Error("Failed to get organization users", "organization_id", orgID, "error", err)
		return nil, fmt.Errorf("failed to get organization users: %w", err)
	}

	return users, nil
}

// Private helper methods

func (uc *OrganizationUseCase) validateCreateOrganization(req *domain.CreateOrganizationRequest) error {
	if req.Name == "" {
		return fmt.Errorf("organization name is required")
	}
	if req.Plan == "" {
		return fmt.Errorf("organization plan is required")
	}

	// Validate plan
	validPlans := []string{"basic", "professional", "enterprise"}
	valid := false
	for _, plan := range validPlans {
		if req.Plan == plan {
			valid = true
			break
		}
	}
	if !valid {
		return fmt.Errorf("invalid plan: %s", req.Plan)
	}

	return nil
}

func (uc *OrganizationUseCase) validateUpdateOrganization(organization *domain.Organization) error {
	if organization.Name == "" {
		return fmt.Errorf("organization name cannot be empty")
	}
	if organization.Plan == "" {
		return fmt.Errorf("organization plan cannot be empty")
	}

	// Validate plan
	validPlans := []string{"basic", "professional", "enterprise"}
	valid := false
	for _, plan := range validPlans {
		if organization.Plan == plan {
			valid = true
			break
		}
	}
	if !valid {
		return fmt.Errorf("invalid plan: %s", organization.Plan)
	}

	return nil
}
