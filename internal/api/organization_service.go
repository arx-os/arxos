package api

import (
	"context"
	"crypto/rand"
	"encoding/base64"
	"fmt"
	"time"

	"github.com/arx-os/arxos/internal/common/logger"
	"github.com/arx-os/arxos/internal/database"
	"github.com/arx-os/arxos/pkg/models"
	"github.com/google/uuid"
)

// OrganizationServiceImpl implements the OrganizationService interface
type OrganizationServiceImpl struct {
	db database.DB
}

// NewOrganizationService creates a new organization service
func NewOrganizationService(db database.DB) OrganizationService {
	return &OrganizationServiceImpl{
		db: db,
	}
}

// Organization CRUD operations

// GetOrganization retrieves an organization by ID
func (s *OrganizationServiceImpl) GetOrganization(ctx context.Context, id string) (*models.Organization, error) {
	return s.db.GetOrganization(ctx, id)
}

// GetOrganizationBySlug retrieves an organization by slug
func (s *OrganizationServiceImpl) GetOrganizationBySlug(ctx context.Context, slug string) (*models.Organization, error) {
	// For now, we'll use a query since we don't have a dedicated method
	// In a real implementation, we'd add GetOrganizationBySlug to the database interface
	query := `SELECT id, name, slug, plan, max_users, max_buildings, status, created_at, updated_at FROM organizations WHERE slug = ?`

	row := s.db.QueryRow(ctx, query, slug)
	var org models.Organization
	err := row.Scan(&org.ID, &org.Name, &org.Slug, &org.Plan, &org.MaxUsers, &org.MaxBuildings, &org.Status, &org.CreatedAt, &org.UpdatedAt)
	if err != nil {
		return nil, err
	}

	return &org, nil
}

// ListOrganizations retrieves organizations for a user
func (s *OrganizationServiceImpl) ListOrganizations(ctx context.Context, userID string) ([]*models.Organization, error) {
	return s.db.GetOrganizationsByUser(ctx, userID)
}

// CreateOrganization creates a new organization and adds the owner as a member
func (s *OrganizationServiceImpl) CreateOrganization(ctx context.Context, org *models.Organization, ownerID string) error {
	// Generate ID if not provided
	if org.ID == "" {
		org.ID = uuid.New().String()
	}

	// Set timestamps
	now := time.Now()
	org.CreatedAt = &now
	org.UpdatedAt = &now

	// Set defaults
	if org.Status == "" {
		org.Status = "active"
	}
	if org.Plan == "" {
		org.Plan = models.PlanFree
	}
	if org.MaxUsers == 0 {
		org.MaxUsers = 5 // Default for free plan
	}
	if org.MaxBuildings == 0 {
		org.MaxBuildings = 1 // Default for free plan
	}

	// Create organization
	if err := s.db.CreateOrganization(ctx, org); err != nil {
		return fmt.Errorf("failed to create organization: %w", err)
	}

	// Add owner as member
	if err := s.db.AddOrganizationMember(ctx, org.ID, ownerID, string(models.RoleOwner)); err != nil {
		logger.Error("Failed to add owner to organization %s: %v", org.ID, err)
		// Note: In production, we'd want to rollback the organization creation
		return fmt.Errorf("failed to add owner to organization: %w", err)
	}

	logger.Info("Created organization %s (%s) with owner %s", org.Name, org.ID, ownerID)
	return nil
}

// UpdateOrganization updates an existing organization
func (s *OrganizationServiceImpl) UpdateOrganization(ctx context.Context, org *models.Organization) error {
	now := time.Now()
	org.UpdatedAt = &now
	return s.db.UpdateOrganization(ctx, org)
}

// DeleteOrganization deletes an organization
func (s *OrganizationServiceImpl) DeleteOrganization(ctx context.Context, id string) error {
	return s.db.DeleteOrganization(ctx, id)
}

// Member management

// AddMember adds a user to an organization
func (s *OrganizationServiceImpl) AddMember(ctx context.Context, orgID, userID string, role models.Role) error {
	return s.db.AddOrganizationMember(ctx, orgID, userID, string(role))
}

// RemoveMember removes a user from an organization
func (s *OrganizationServiceImpl) RemoveMember(ctx context.Context, orgID, userID string) error {
	return s.db.RemoveOrganizationMember(ctx, orgID, userID)
}

// UpdateMemberRole updates a member's role in an organization
func (s *OrganizationServiceImpl) UpdateMemberRole(ctx context.Context, orgID, userID string, role models.Role) error {
	return s.db.UpdateOrganizationMemberRole(ctx, orgID, userID, string(role))
}

// GetMembers retrieves all members of an organization
func (s *OrganizationServiceImpl) GetMembers(ctx context.Context, orgID string) ([]*models.OrganizationMember, error) {
	return s.db.GetOrganizationMembers(ctx, orgID)
}

// GetMemberRole retrieves a user's role in an organization
func (s *OrganizationServiceImpl) GetMemberRole(ctx context.Context, orgID, userID string) (*models.Role, error) {
	member, err := s.db.GetOrganizationMember(ctx, orgID, userID)
	if err != nil {
		if err == database.ErrNotFound {
			return nil, nil // User is not a member
		}
		return nil, err
	}

	return &member.Role, nil
}

// Invitation management

// CreateInvitation creates a new organization invitation
func (s *OrganizationServiceImpl) CreateInvitation(ctx context.Context, orgID, email string, role models.Role, invitedBy string) (*models.OrganizationInvitation, error) {
	// Generate invitation
	now := time.Now()
	invitation := &models.OrganizationInvitation{
		ID:             uuid.New().String(),
		OrganizationID: orgID,
		Email:          email,
		Role:           string(role),
		Token:          s.generateInvitationToken(),
		InvitedBy:      invitedBy,
		Status:         "pending",
		ExpiresAt:      time.Now().Add(7 * 24 * time.Hour), // 7 days
		CreatedAt:      &now,
		UpdatedAt:      &now,
	}

	if err := s.db.CreateOrganizationInvitation(ctx, invitation); err != nil {
		return nil, fmt.Errorf("failed to create invitation: %w", err)
	}

	logger.Info("Created invitation for %s to join organization %s", email, orgID)
	return invitation, nil
}

// AcceptInvitation accepts an organization invitation
func (s *OrganizationServiceImpl) AcceptInvitation(ctx context.Context, token string, userID string) error {
	if err := s.db.AcceptOrganizationInvitation(ctx, token, userID); err != nil {
		return fmt.Errorf("failed to accept invitation: %w", err)
	}

	logger.Info("User %s accepted organization invitation", userID)
	return nil
}

// RevokeInvitation revokes an organization invitation
func (s *OrganizationServiceImpl) RevokeInvitation(ctx context.Context, invitationID string) error {
	return s.db.RevokeOrganizationInvitation(ctx, invitationID)
}

// ListPendingInvitations retrieves pending invitations for an organization
func (s *OrganizationServiceImpl) ListPendingInvitations(ctx context.Context, orgID string) ([]*models.OrganizationInvitation, error) {
	return s.db.ListOrganizationInvitations(ctx, orgID)
}

// Permission and access control

// HasPermission checks if a user has a specific permission in an organization
func (s *OrganizationServiceImpl) HasPermission(ctx context.Context, orgID, userID string, permission models.Permission) (bool, error) {
	role, err := s.GetMemberRole(ctx, orgID, userID)
	if err != nil {
		return false, err
	}

	if role == nil {
		return false, nil // User is not a member
	}

	// Check if the role has the required permission
	permissions := role.GetPermissions()
	for _, p := range permissions {
		if p == permission {
			return true, nil
		}
	}

	return false, nil
}

// GetUserPermissions retrieves all permissions for a user in an organization
func (s *OrganizationServiceImpl) GetUserPermissions(ctx context.Context, orgID, userID string) ([]models.Permission, error) {
	role, err := s.GetMemberRole(ctx, orgID, userID)
	if err != nil {
		return nil, err
	}

	if role == nil {
		return []models.Permission{}, nil // User is not a member
	}

	return role.GetPermissions(), nil
}

// CanUserAccessOrganization checks if a user can access an organization
func (s *OrganizationServiceImpl) CanUserAccessOrganization(ctx context.Context, orgID, userID string) (bool, error) {
	role, err := s.GetMemberRole(ctx, orgID, userID)
	if err != nil {
		return false, err
	}

	return role != nil, nil // User can access if they have any role
}

// Helper methods

// generateInvitationToken generates a secure token for invitations
func (s *OrganizationServiceImpl) generateInvitationToken() string {
	b := make([]byte, 32)
	rand.Read(b)
	return base64.URLEncoding.EncodeToString(b)
}
