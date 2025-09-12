package organization

import (
	"context"
	"crypto/rand"
	"encoding/hex"
	"fmt"
	"strings"
	"time"

	"github.com/google/uuid"
	"github.com/joelpate/arxos/internal/database"
	"github.com/joelpate/arxos/pkg/models"
)

// Service handles organization management
type Service struct {
	db database.DB
}

// NewService creates a new organization service
func NewService(db database.DB) *Service {
	return &Service{db: db}
}

// CreateOrganization creates a new organization
func (s *Service) CreateOrganization(ctx context.Context, org *models.Organization, ownerID string) error {
	// Generate ID if not provided
	if org.ID == "" {
		org.ID = "org_" + uuid.New().String()[:8]
	}

	// Generate slug from name if not provided
	if org.Slug == "" {
		org.Slug = s.generateSlug(org.Name)
	}

	// Set defaults
	if org.Plan == "" {
		org.Plan = models.PlanFree
	}
	org.Status = models.OrgStatusTrial
	
	// Set plan limits
	maxUsers, maxBuildings, maxStorage := models.GetPlanLimits(org.Plan)
	org.MaxUsers = maxUsers
	org.MaxBuildings = maxBuildings
	org.MaxStorage = maxStorage

	// Set trial period (14 days)
	trialEnd := time.Now().AddDate(0, 0, 14)
	org.TrialEndsAt = &trialEnd

	org.CreatedAt = time.Now()
	org.UpdatedAt = time.Now()

	// Start transaction
	tx, err := s.db.BeginTx(ctx)
	if err != nil {
		return fmt.Errorf("failed to start transaction: %w", err)
	}
	defer tx.Rollback()

	// Create organization
	query := `
		INSERT INTO organizations (
			id, name, slug, domain, plan, status, 
			trial_ends_at, max_users, max_buildings, max_storage,
			created_at, updated_at
		) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
	`
	_, err = tx.ExecContext(ctx, query,
		org.ID, org.Name, org.Slug, org.Domain, org.Plan, org.Status,
		org.TrialEndsAt, org.MaxUsers, org.MaxBuildings, org.MaxStorage,
		org.CreatedAt, org.UpdatedAt,
	)
	if err != nil {
		return fmt.Errorf("failed to create organization: %w", err)
	}

	// Add owner as member
	member := &models.OrganizationMember{
		ID:             "member_" + uuid.New().String()[:8],
		OrganizationID: org.ID,
		UserID:         ownerID,
		Role:           models.RoleOwner,
		InvitedBy:      ownerID,
		InvitedAt:      time.Now(),
		JoinedAt:       &org.CreatedAt,
	}

	memberQuery := `
		INSERT INTO organization_members (
			id, organization_id, user_id, role, 
			invited_by, invited_at, joined_at
		) VALUES ($1, $2, $3, $4, $5, $6, $7)
	`
	_, err = tx.ExecContext(ctx, memberQuery,
		member.ID, member.OrganizationID, member.UserID, member.Role,
		member.InvitedBy, member.InvitedAt, member.JoinedAt,
	)
	if err != nil {
		return fmt.Errorf("failed to add owner: %w", err)
	}

	// Commit transaction
	if err := tx.Commit(); err != nil {
		return fmt.Errorf("failed to commit transaction: %w", err)
	}

	return nil
}

// GetOrganization retrieves an organization by ID
func (s *Service) GetOrganization(ctx context.Context, orgID string) (*models.Organization, error) {
	query := `
		SELECT id, name, slug, domain, plan, status,
		       trial_ends_at, max_users, max_buildings, max_storage,
		       used_storage, created_at, updated_at
		FROM organizations
		WHERE id = $1
	`
	
	var org models.Organization
	err := s.db.QueryRow(ctx, query, orgID).Scan(
		&org.ID, &org.Name, &org.Slug, &org.Domain, &org.Plan, &org.Status,
		&org.TrialEndsAt, &org.MaxUsers, &org.MaxBuildings, &org.MaxStorage,
		&org.UsedStorage, &org.CreatedAt, &org.UpdatedAt,
	)
	if err != nil {
		return nil, err
	}

	return &org, nil
}

// GetOrganizationBySlug retrieves an organization by slug
func (s *Service) GetOrganizationBySlug(ctx context.Context, slug string) (*models.Organization, error) {
	query := `
		SELECT id, name, slug, domain, plan, status,
		       trial_ends_at, max_users, max_buildings, max_storage,
		       used_storage, created_at, updated_at
		FROM organizations
		WHERE slug = $1
	`
	
	var org models.Organization
	err := s.db.QueryRow(ctx, query, slug).Scan(
		&org.ID, &org.Name, &org.Slug, &org.Domain, &org.Plan, &org.Status,
		&org.TrialEndsAt, &org.MaxUsers, &org.MaxBuildings, &org.MaxStorage,
		&org.UsedStorage, &org.CreatedAt, &org.UpdatedAt,
	)
	if err != nil {
		return nil, err
	}

	return &org, nil
}

// UpdateOrganization updates an organization
func (s *Service) UpdateOrganization(ctx context.Context, org *models.Organization) error {
	org.UpdatedAt = time.Now()

	query := `
		UPDATE organizations
		SET name = $2, slug = $3, domain = $4, plan = $5,
		    status = $6, max_users = $7, max_buildings = $8,
		    max_storage = $9, updated_at = $10
		WHERE id = $1
	`
	
	_, err := s.db.Exec(ctx, query,
		org.ID, org.Name, org.Slug, org.Domain, org.Plan,
		org.Status, org.MaxUsers, org.MaxBuildings,
		org.MaxStorage, org.UpdatedAt,
	)
	
	return err
}

// ListUserOrganizations lists all organizations a user belongs to
func (s *Service) ListUserOrganizations(ctx context.Context, userID string) ([]models.OrganizationMember, error) {
	query := `
		SELECT om.id, om.organization_id, om.user_id, om.role,
		       om.invited_by, om.invited_at, om.joined_at, om.last_access_at,
		       o.name, o.slug, o.plan, o.status
		FROM organization_members om
		JOIN organizations o ON om.organization_id = o.id
		WHERE om.user_id = $1 AND o.status != $2
		ORDER BY om.joined_at DESC
	`
	
	rows, err := s.db.Query(ctx, query, userID, models.OrgStatusCanceled)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var members []models.OrganizationMember
	for rows.Next() {
		var member models.OrganizationMember
		var org models.Organization
		
		err := rows.Scan(
			&member.ID, &member.OrganizationID, &member.UserID, &member.Role,
			&member.InvitedBy, &member.InvitedAt, &member.JoinedAt, &member.LastAccessAt,
			&org.Name, &org.Slug, &org.Plan, &org.Status,
		)
		if err != nil {
			return nil, err
		}
		
		org.ID = member.OrganizationID
		member.Organization = &org
		members = append(members, member)
	}

	return members, nil
}

// AddMember adds a user to an organization
func (s *Service) AddMember(ctx context.Context, member *models.OrganizationMember) error {
	if member.ID == "" {
		member.ID = "member_" + uuid.New().String()[:8]
	}
	
	now := time.Now()
	member.InvitedAt = now
	member.JoinedAt = &now

	query := `
		INSERT INTO organization_members (
			id, organization_id, user_id, role,
			invited_by, invited_at, joined_at
		) VALUES ($1, $2, $3, $4, $5, $6, $7)
	`
	
	_, err := s.db.Exec(ctx, query,
		member.ID, member.OrganizationID, member.UserID, member.Role,
		member.InvitedBy, member.InvitedAt, member.JoinedAt,
	)
	
	return err
}

// UpdateMemberRole updates a member's role in an organization
func (s *Service) UpdateMemberRole(ctx context.Context, orgID, userID string, role models.Role) error {
	query := `
		UPDATE organization_members
		SET role = $3
		WHERE organization_id = $1 AND user_id = $2
	`
	
	_, err := s.db.Exec(ctx, query, orgID, userID, role)
	return err
}

// RemoveMember removes a user from an organization
func (s *Service) RemoveMember(ctx context.Context, orgID, userID string) error {
	query := `
		DELETE FROM organization_members
		WHERE organization_id = $1 AND user_id = $2
	`
	
	_, err := s.db.Exec(ctx, query, orgID, userID)
	return err
}

// CreateInvitation creates an invitation to join an organization
func (s *Service) CreateInvitation(ctx context.Context, inv *models.Invitation) error {
	if inv.ID == "" {
		inv.ID = "inv_" + uuid.New().String()[:8]
	}

	// Generate secure token
	token := make([]byte, 32)
	if _, err := rand.Read(token); err != nil {
		return err
	}
	inv.Token = hex.EncodeToString(token)

	inv.InvitedAt = time.Now()
	inv.ExpiresAt = time.Now().AddDate(0, 0, 7) // 7 days expiry

	query := `
		INSERT INTO invitations (
			id, organization_id, email, role, token,
			invited_by, invited_at, expires_at
		) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
	`
	
	_, err := s.db.Exec(ctx, query,
		inv.ID, inv.OrganizationID, inv.Email, inv.Role, inv.Token,
		inv.InvitedBy, inv.InvitedAt, inv.ExpiresAt,
	)
	
	return err
}

// AcceptInvitation accepts an invitation and adds the user to the organization
func (s *Service) AcceptInvitation(ctx context.Context, token string, userID string) (*models.OrganizationMember, error) {
	// Start transaction
	tx, err := s.db.BeginTx(ctx)
	if err != nil {
		return nil, err
	}
	defer tx.Rollback()

	// Get invitation
	var inv models.Invitation
	query := `
		SELECT id, organization_id, email, role, invited_by, expires_at
		FROM invitations
		WHERE token = $1 AND accepted_at IS NULL
	`
	err = tx.QueryRowContext(ctx, query, token).Scan(
		&inv.ID, &inv.OrganizationID, &inv.Email, &inv.Role,
		&inv.InvitedBy, &inv.ExpiresAt,
	)
	if err != nil {
		return nil, fmt.Errorf("invitation not found or already used")
	}

	// Check expiry
	if inv.IsExpired() {
		return nil, fmt.Errorf("invitation has expired")
	}

	// Mark invitation as accepted
	now := time.Now()
	updateQuery := `
		UPDATE invitations
		SET accepted_at = $2
		WHERE id = $1
	`
	_, err = tx.ExecContext(ctx, updateQuery, inv.ID, now)
	if err != nil {
		return nil, err
	}

	// Add user to organization
	member := &models.OrganizationMember{
		ID:             "member_" + uuid.New().String()[:8],
		OrganizationID: inv.OrganizationID,
		UserID:         userID,
		Role:           inv.Role,
		InvitedBy:      inv.InvitedBy,
		InvitedAt:      inv.InvitedAt,
		JoinedAt:       &now,
	}

	memberQuery := `
		INSERT INTO organization_members (
			id, organization_id, user_id, role,
			invited_by, invited_at, joined_at
		) VALUES ($1, $2, $3, $4, $5, $6, $7)
	`
	_, err = tx.ExecContext(ctx, memberQuery,
		member.ID, member.OrganizationID, member.UserID, member.Role,
		member.InvitedBy, member.InvitedAt, member.JoinedAt,
	)
	if err != nil {
		return nil, err
	}

	// Commit transaction
	if err := tx.Commit(); err != nil {
		return nil, err
	}

	return member, nil
}

// Helper methods

func (s *Service) generateSlug(name string) string {
	// Convert to lowercase and replace spaces with hyphens
	slug := strings.ToLower(name)
	slug = strings.ReplaceAll(slug, " ", "-")
	
	// Remove special characters
	slug = strings.Map(func(r rune) rune {
		if (r >= 'a' && r <= 'z') || (r >= '0' && r <= '9') || r == '-' {
			return r
		}
		return -1
	}, slug)
	
	// Add random suffix to ensure uniqueness
	suffix := uuid.New().String()[:4]
	return fmt.Sprintf("%s-%s", slug, suffix)
}

// CheckPermission checks if a user has a specific permission in an organization
func (s *Service) CheckPermission(ctx context.Context, userID, orgID string, permission models.Permission) (bool, error) {
	// Get member info
	query := `
		SELECT role, permissions
		FROM organization_members
		WHERE user_id = $1 AND organization_id = $2
	`
	
	var role models.Role
	var customPerms []byte
	err := s.db.QueryRow(ctx, query, userID, orgID).Scan(&role, &customPerms)
	if err != nil {
		return false, err
	}

	// Check role permissions
	for _, p := range role.GetPermissions() {
		if p == permission {
			return true, nil
		}
	}

	// Check custom permissions (if implemented)
	// ...

	return false, nil
}