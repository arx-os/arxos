package services

import (
	"context"
	"fmt"
	"time"

	"github.com/joelpate/arxos/internal/common/logger"
	"github.com/joelpate/arxos/internal/database"
	"github.com/joelpate/arxos/pkg/models"
)

// OrganizationService handles organization-related operations
type OrganizationService struct {
	db database.DB
}

// NewOrganizationService creates a new organization service
func NewOrganizationService(db database.DB) *OrganizationService {
	return &OrganizationService{
		db: db,
	}
}

// CreateOrganization creates a new organization
func (s *OrganizationService) CreateOrganization(ctx context.Context, req *models.CreateOrganizationRequest) (*models.Organization, error) {
	// Validate input
	if req.Name == "" {
		return nil, fmt.Errorf("organization name is required")
	}

	if len(req.Name) > 255 {
		return nil, fmt.Errorf("organization name too long")
	}

	// Create organization
	now := time.Now()
	org := &models.Organization{
		ID:          generateID(),
		Name:        req.Name,
		Description: req.Description,
		Type:        req.Type,
		Status:      "active",
		Settings:    req.Settings,
		CreatedAt:   &now,
		UpdatedAt:   &now,
	}

	// Set default type if not provided
	if org.Type == "" {
		org.Type = "standard"
	}

	// Validate type
	validTypes := map[string]bool{"standard": true, "enterprise": true, "educational": true}
	if !validTypes[org.Type] {
		return nil, fmt.Errorf("invalid organization type: %s", org.Type)
	}

	// Save to database
	if err := s.db.CreateOrganization(ctx, org); err != nil {
		return nil, fmt.Errorf("failed to create organization: %w", err)
	}

	// Add creator as admin if user ID is provided
	if req.CreatorUserID != "" {
		if err := s.db.AddOrganizationMember(ctx, org.ID, req.CreatorUserID, "admin"); err != nil {
			logger.Warn("Failed to add creator as admin: %v", err)
		}
	}

	logger.Info("Created new organization: %s (%s)", org.Name, org.ID)
	return org, nil
}

// GetOrganization retrieves an organization by ID
func (s *OrganizationService) GetOrganization(ctx context.Context, orgID string) (*models.Organization, error) {
	org, err := s.db.GetOrganization(ctx, orgID)
	if err != nil {
		if err == database.ErrNotFound {
			return nil, fmt.Errorf("organization not found")
		}
		return nil, fmt.Errorf("failed to get organization: %w", err)
	}

	return org, nil
}

// UpdateOrganization updates an organization's information
func (s *OrganizationService) UpdateOrganization(ctx context.Context, orgID string, req *models.UpdateOrganizationRequest) (*models.Organization, error) {
	// Get existing organization
	org, err := s.db.GetOrganization(ctx, orgID)
	if err != nil {
		if err == database.ErrNotFound {
			return nil, fmt.Errorf("organization not found")
		}
		return nil, fmt.Errorf("failed to get organization: %w", err)
	}

	// Update fields if provided
	if req.Name != "" {
		if len(req.Name) > 255 {
			return nil, fmt.Errorf("organization name too long")
		}
		org.Name = req.Name
	}

	if req.Description != "" {
		org.Description = req.Description
	}

	if req.Type != "" {
		validTypes := map[string]bool{"standard": true, "enterprise": true, "educational": true}
		if !validTypes[req.Type] {
			return nil, fmt.Errorf("invalid organization type: %s", req.Type)
		}
		org.Type = req.Type
	}

	if req.Status != "" {
		validStatuses := map[string]bool{"active": true, "inactive": true, "suspended": true}
		if !validStatuses[req.Status] {
			return nil, fmt.Errorf("invalid status: %s", req.Status)
		}
		org.Status = req.Status
	}

	if req.Settings != nil {
		org.Settings = req.Settings
	}

	// Update timestamp
	now := time.Now()
	org.UpdatedAt = &now

	// Save changes
	if err := s.db.UpdateOrganization(ctx, org); err != nil {
		return nil, fmt.Errorf("failed to update organization: %w", err)
	}

	logger.Info("Updated organization: %s (%s)", org.Name, org.ID)
	return org, nil
}

// DeleteOrganization deletes an organization
func (s *OrganizationService) DeleteOrganization(ctx context.Context, orgID string) error {
	// Check if organization exists
	org, err := s.db.GetOrganization(ctx, orgID)
	if err != nil {
		if err == database.ErrNotFound {
			return fmt.Errorf("organization not found")
		}
		return fmt.Errorf("failed to get organization: %w", err)
	}

	// Delete organization
	if err := s.db.DeleteOrganization(ctx, orgID); err != nil {
		return fmt.Errorf("failed to delete organization: %w", err)
	}

	logger.Info("Deleted organization: %s (%s)", org.Name, orgID)
	return nil
}

// AddMember adds a user to an organization
func (s *OrganizationService) AddMember(ctx context.Context, orgID, userID, role string) error {
	// Validate role
	validRoles := map[string]bool{"admin": true, "member": true, "viewer": true}
	if !validRoles[role] {
		return fmt.Errorf("invalid role: %s", role)
	}

	// Check if organization exists
	_, err := s.db.GetOrganization(ctx, orgID)
	if err != nil {
		if err == database.ErrNotFound {
			return fmt.Errorf("organization not found")
		}
		return fmt.Errorf("failed to get organization: %w", err)
	}

	// Check if user exists
	_, err = s.db.GetUser(ctx, userID)
	if err != nil {
		if err == database.ErrNotFound {
			return fmt.Errorf("user not found")
		}
		return fmt.Errorf("failed to get user: %w", err)
	}

	// Check if user is already a member
	member, _ := s.db.GetOrganizationMember(ctx, orgID, userID)
	if member != nil {
		return fmt.Errorf("user is already a member of this organization")
	}

	// Add member
	if err := s.db.AddOrganizationMember(ctx, orgID, userID, role); err != nil {
		return fmt.Errorf("failed to add member: %w", err)
	}

	logger.Info("Added user %s to organization %s with role %s", userID, orgID, role)
	return nil
}

// RemoveMember removes a user from an organization
func (s *OrganizationService) RemoveMember(ctx context.Context, orgID, userID string) error {
	// Check if member exists
	member, err := s.db.GetOrganizationMember(ctx, orgID, userID)
	if err != nil {
		if err == database.ErrNotFound {
			return fmt.Errorf("user is not a member of this organization")
		}
		return fmt.Errorf("failed to get member: %w", err)
	}

	// Prevent removing the last admin
	if member.Role == "admin" {
		members, err := s.db.GetOrganizationMembers(ctx, orgID)
		if err != nil {
			return fmt.Errorf("failed to get members: %w", err)
		}

		adminCount := 0
		for _, m := range members {
			if m.Role == "admin" {
				adminCount++
			}
		}

		if adminCount <= 1 {
			return fmt.Errorf("cannot remove the last admin from the organization")
		}
	}

	// Remove member
	if err := s.db.RemoveOrganizationMember(ctx, orgID, userID); err != nil {
		return fmt.Errorf("failed to remove member: %w", err)
	}

	logger.Info("Removed user %s from organization %s", userID, orgID)
	return nil
}

// UpdateMemberRole updates a member's role in an organization
func (s *OrganizationService) UpdateMemberRole(ctx context.Context, orgID, userID, newRole string) error {
	// Validate role
	validRoles := map[string]bool{"admin": true, "member": true, "viewer": true}
	if !validRoles[newRole] {
		return fmt.Errorf("invalid role: %s", newRole)
	}

	// Check if member exists
	member, err := s.db.GetOrganizationMember(ctx, orgID, userID)
	if err != nil {
		if err == database.ErrNotFound {
			return fmt.Errorf("user is not a member of this organization")
		}
		return fmt.Errorf("failed to get member: %w", err)
	}

	// Prevent demoting the last admin
	if member.Role == "admin" && newRole != "admin" {
		members, err := s.db.GetOrganizationMembers(ctx, orgID)
		if err != nil {
			return fmt.Errorf("failed to get members: %w", err)
		}

		adminCount := 0
		for _, m := range members {
			if m.Role == "admin" {
				adminCount++
			}
		}

		if adminCount <= 1 {
			return fmt.Errorf("cannot demote the last admin of the organization")
		}
	}

	// Update role
	if err := s.db.UpdateOrganizationMemberRole(ctx, orgID, userID, newRole); err != nil {
		return fmt.Errorf("failed to update member role: %w", err)
	}

	logger.Info("Updated user %s role in organization %s to %s", userID, orgID, newRole)
	return nil
}

// GetMembers returns all members of an organization
func (s *OrganizationService) GetMembers(ctx context.Context, orgID string) ([]*models.OrganizationMember, error) {
	// Check if organization exists
	_, err := s.db.GetOrganization(ctx, orgID)
	if err != nil {
		if err == database.ErrNotFound {
			return nil, fmt.Errorf("organization not found")
		}
		return nil, fmt.Errorf("failed to get organization: %w", err)
	}

	members, err := s.db.GetOrganizationMembers(ctx, orgID)
	if err != nil {
		return nil, fmt.Errorf("failed to get members: %w", err)
	}

	return members, nil
}

// CreateInvitation creates an invitation to join an organization
func (s *OrganizationService) CreateInvitation(ctx context.Context, orgID, email, role string, inviterUserID string) (*models.OrganizationInvitation, error) {
	// Validate role
	validRoles := map[string]bool{"admin": true, "member": true, "viewer": true}
	if !validRoles[role] {
		return nil, fmt.Errorf("invalid role: %s", role)
	}

	// Check if organization exists
	_, err := s.db.GetOrganization(ctx, orgID)
	if err != nil {
		if err == database.ErrNotFound {
			return nil, fmt.Errorf("organization not found")
		}
		return nil, fmt.Errorf("failed to get organization: %w", err)
	}

	// Generate invitation token
	token, err := generateSecureToken()
	if err != nil {
		return nil, fmt.Errorf("failed to generate invitation token: %w", err)
	}

	// Create invitation
	now := time.Now()
	invitation := &models.OrganizationInvitation{
		ID:             generateID(),
		OrganizationID: orgID,
		Email:          email,
		Role:           role,
		Token:          token,
		InvitedBy:      inviterUserID,
		Status:         "pending",
		ExpiresAt:      time.Now().Add(7 * 24 * time.Hour), // 7 days
		CreatedAt:      &now,
		UpdatedAt:      &now,
	}

	// Save invitation
	if err := s.db.CreateOrganizationInvitation(ctx, invitation); err != nil {
		return nil, fmt.Errorf("failed to create invitation: %w", err)
	}

	// TODO: Send invitation email

	logger.Info("Created invitation for %s to join organization %s", email, orgID)
	return invitation, nil
}

// AcceptInvitation accepts an organization invitation
func (s *OrganizationService) AcceptInvitation(ctx context.Context, token, userID string) error {
	// Get invitation
	invitation, err := s.db.GetOrganizationInvitationByToken(ctx, token)
	if err != nil {
		if err == database.ErrNotFound {
			return fmt.Errorf("invitation not found or expired")
		}
		return fmt.Errorf("failed to get invitation: %w", err)
	}

	// Check if expired
	if time.Now().After(invitation.ExpiresAt) {
		return fmt.Errorf("invitation has expired")
	}

	// Check if already accepted
	if invitation.Status != "pending" {
		return fmt.Errorf("invitation has already been %s", invitation.Status)
	}

	// Accept invitation
	if err := s.db.AcceptOrganizationInvitation(ctx, token, userID); err != nil {
		return fmt.Errorf("failed to accept invitation: %w", err)
	}

	// Add user to organization
	if err := s.db.AddOrganizationMember(ctx, invitation.OrganizationID, userID, invitation.Role); err != nil {
		return fmt.Errorf("failed to add member to organization: %w", err)
	}

	logger.Info("User %s accepted invitation to organization %s", userID, invitation.OrganizationID)
	return nil
}

// RevokeInvitation revokes an organization invitation
func (s *OrganizationService) RevokeInvitation(ctx context.Context, invitationID string) error {
	// Get invitation
	invitation, err := s.db.GetOrganizationInvitation(ctx, invitationID)
	if err != nil {
		if err == database.ErrNotFound {
			return fmt.Errorf("invitation not found")
		}
		return fmt.Errorf("failed to get invitation: %w", err)
	}

	// Check if already processed
	if invitation.Status != "pending" {
		return fmt.Errorf("invitation has already been %s", invitation.Status)
	}

	// Revoke invitation
	if err := s.db.RevokeOrganizationInvitation(ctx, invitationID); err != nil {
		return fmt.Errorf("failed to revoke invitation: %w", err)
	}

	logger.Info("Revoked invitation %s for organization %s", invitationID, invitation.OrganizationID)
	return nil
}

// ListInvitations returns all pending invitations for an organization
func (s *OrganizationService) ListInvitations(ctx context.Context, orgID string) ([]*models.OrganizationInvitation, error) {
	// Check if organization exists
	_, err := s.db.GetOrganization(ctx, orgID)
	if err != nil {
		if err == database.ErrNotFound {
			return nil, fmt.Errorf("organization not found")
		}
		return nil, fmt.Errorf("failed to get organization: %w", err)
	}

	invitations, err := s.db.ListOrganizationInvitations(ctx, orgID)
	if err != nil {
		return nil, fmt.Errorf("failed to list invitations: %w", err)
	}

	return invitations, nil
}