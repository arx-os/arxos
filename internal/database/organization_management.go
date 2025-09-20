package database

import (
	"context"
	"database/sql"
	"encoding/json"
	"fmt"
	"time"

	"github.com/google/uuid"
	"github.com/arx-os/arxos/pkg/models"
)

// Helper function to convert string to sql.NullString
func nullString(s string) sql.NullString {
	if s == "" {
		return sql.NullString{String: "", Valid: false}
	}
	return sql.NullString{String: s, Valid: true}
}

// generateSecureToken generates a secure random token
func generateSecureToken(length int) string {
	return uuid.New().String()
}

// GetOrganization retrieves an organization by ID
func (p *PostGISDB) GetOrganization(ctx context.Context, id string) (*models.Organization, error) {
	query := `
		SELECT id, name, slug, description, website, logo_url,
			   address, city, state, country, postal_code, phone, email,
			   settings, metadata, is_active, subscription_tier,
			   subscription_expires_at, created_at, updated_at
		FROM organizations
		WHERE id = $1
	`

	var org models.Organization
	var settings, metadata json.RawMessage
	var description, website, logoURL, address, city, state, country, postalCode, phone, email sql.NullString
	var subscriptionExpiresAt sql.NullTime

	err := p.db.QueryRowContext(ctx, query, id).Scan(
		&org.ID, &org.Name, &org.Slug, &description, &website, &logoURL,
		&address, &city, &state, &country, &postalCode, &phone, &email,
		&settings, &metadata, &org.IsActive, &org.SubscriptionTier,
		&subscriptionExpiresAt, &org.CreatedAt, &org.UpdatedAt,
	)

	if err != nil {
		if err == sql.ErrNoRows {
			return nil, fmt.Errorf("organization not found")
		}
		return nil, fmt.Errorf("failed to get organization: %w", err)
	}

	// Handle nullable fields
	org.Description = description.String
	org.Website = website.String
	org.LogoURL = logoURL.String
	org.Address = address.String
	org.City = city.String
	org.State = state.String
	org.Country = country.String
	org.PostalCode = postalCode.String
	org.Phone = phone.String
	org.Email = email.String

	if subscriptionExpiresAt.Valid {
		org.SubscriptionExpiresAt = &subscriptionExpiresAt.Time
	}

	// Parse JSON fields
	if settings != nil {
		if err := json.Unmarshal(settings, &org.Settings); err != nil {
			return nil, fmt.Errorf("failed to parse settings: %w", err)
		}
	}

	if metadata != nil {
		if err := json.Unmarshal(metadata, &org.Metadata); err != nil {
			return nil, fmt.Errorf("failed to parse metadata: %w", err)
		}
	}

	return &org, nil
}

// ListOrganizations lists all organizations with pagination
func (p *PostGISDB) ListOrganizations(ctx context.Context, limit, offset int) ([]*models.Organization, error) {
	query := `
		SELECT o.id, o.name, o.slug, o.description, o.website, o.logo_url,
			   o.address, o.city, o.state, o.country, o.postal_code, o.phone, o.email,
			   o.settings, o.metadata, o.is_active, o.subscription_tier,
			   o.subscription_expires_at, o.created_at, o.updated_at
		FROM organizations o
		WHERE o.is_active = true
		ORDER BY o.created_at DESC
		LIMIT $1 OFFSET $2
	`

	rows, err := p.db.QueryContext(ctx, query, limit, offset)
	if err != nil {
		return nil, fmt.Errorf("failed to query organizations: %w", err)
	}
	defer rows.Close()

	var organizations []*models.Organization

	for rows.Next() {
		var org models.Organization
		var settings, metadata json.RawMessage
		var description, website, logoURL, address, city, state, country, postalCode, phone, email sql.NullString
		var subscriptionExpiresAt sql.NullTime

		err := rows.Scan(
			&org.ID, &org.Name, &org.Slug, &description, &website, &logoURL,
			&address, &city, &state, &country, &postalCode, &phone, &email,
			&settings, &metadata, &org.IsActive, &org.SubscriptionTier,
			&subscriptionExpiresAt, &org.CreatedAt, &org.UpdatedAt,
		)

		if err != nil {
			return nil, fmt.Errorf("failed to scan organization: %w", err)
		}

		// Handle nullable fields
		org.Description = description.String
		org.Website = website.String
		org.LogoURL = logoURL.String
		org.Address = address.String
		org.City = city.String
		org.State = state.String
		org.Country = country.String
		org.PostalCode = postalCode.String
		org.Phone = phone.String
		org.Email = email.String

		if subscriptionExpiresAt.Valid {
			org.SubscriptionExpiresAt = &subscriptionExpiresAt.Time
		}

		// Parse JSON fields
		if settings != nil {
			if err := json.Unmarshal(settings, &org.Settings); err != nil {
				return nil, fmt.Errorf("failed to parse settings: %w", err)
			}
		}

		if metadata != nil {
			if err := json.Unmarshal(metadata, &org.Metadata); err != nil {
				return nil, fmt.Errorf("failed to parse metadata: %w", err)
			}
		}

		organizations = append(organizations, &org)
	}

	if err := rows.Err(); err != nil {
		return nil, fmt.Errorf("error iterating organizations: %w", err)
	}

	return organizations, nil
}

// GetOrganizationsByUser retrieves all organizations for a user
func (p *PostGISDB) GetOrganizationsByUser(ctx context.Context, userID string) ([]*models.Organization, error) {
	query := `
		SELECT o.id, o.name, o.slug, o.description, o.website, o.logo_url,
			   o.address, o.city, o.state, o.country, o.postal_code, o.phone, o.email,
			   o.settings, o.metadata, o.is_active, o.subscription_tier,
			   o.subscription_expires_at, o.created_at, o.updated_at,
			   om.role as member_role, om.joined_at
		FROM organizations o
		JOIN organization_members om ON o.id = om.organization_id
		WHERE om.user_id = $1 AND o.is_active = true
		ORDER BY om.joined_at DESC
	`

	rows, err := p.db.QueryContext(ctx, query, userID)
	if err != nil {
		return nil, fmt.Errorf("failed to query organizations: %w", err)
	}
	defer rows.Close()

	var organizations []*models.Organization

	for rows.Next() {
		var org models.Organization
		var settings, metadata json.RawMessage
		var description, website, logoURL, address, city, state, country, postalCode, phone, email sql.NullString
		var subscriptionExpiresAt sql.NullTime
		var memberRole string
		var joinedAt time.Time

		err := rows.Scan(
			&org.ID, &org.Name, &org.Slug, &description, &website, &logoURL,
			&address, &city, &state, &country, &postalCode, &phone, &email,
			&settings, &metadata, &org.IsActive, &org.SubscriptionTier,
			&subscriptionExpiresAt, &org.CreatedAt, &org.UpdatedAt,
			&memberRole, &joinedAt,
		)

		if err != nil {
			return nil, fmt.Errorf("failed to scan organization: %w", err)
		}

		// Handle nullable fields
		org.Description = description.String
		org.Website = website.String
		org.LogoURL = logoURL.String
		org.Address = address.String
		org.City = city.String
		org.State = state.String
		org.Country = country.String
		org.PostalCode = postalCode.String
		org.Phone = phone.String
		org.Email = email.String

		if subscriptionExpiresAt.Valid {
			org.SubscriptionExpiresAt = &subscriptionExpiresAt.Time
		}

		// Parse JSON fields
		if settings != nil {
			if err := json.Unmarshal(settings, &org.Settings); err != nil {
				return nil, fmt.Errorf("failed to parse settings: %w", err)
			}
		}

		if metadata != nil {
			if err := json.Unmarshal(metadata, &org.Metadata); err != nil {
				return nil, fmt.Errorf("failed to parse metadata: %w", err)
			}
		}

		// Store member info in metadata for convenience
		if org.Metadata == nil {
			org.Metadata = make(map[string]interface{})
		}
		org.Metadata["memberRole"] = memberRole
		org.Metadata["joinedAt"] = joinedAt

		organizations = append(organizations, &org)
	}

	if err := rows.Err(); err != nil {
		return nil, fmt.Errorf("error iterating organizations: %w", err)
	}

	return organizations, nil
}

// CreateOrganization creates a new organization
func (p *PostGISDB) CreateOrganization(ctx context.Context, org *models.Organization) error {
	if org.ID == "" {
		org.ID = uuid.New().String()
	}

	settingsJSON, err := json.Marshal(org.Settings)
	if err != nil {
		return fmt.Errorf("failed to marshal settings: %w", err)
	}

	metadataJSON, err := json.Marshal(org.Metadata)
	if err != nil {
		return fmt.Errorf("failed to marshal metadata: %w", err)
	}

	query := `
		INSERT INTO organizations (
			id, name, slug, description, website, logo_url,
			address, city, state, country, postal_code, phone, email,
			settings, metadata, is_active, subscription_tier,
			subscription_expires_at, created_at, updated_at
		) VALUES (
			$1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13,
			$14, $15, $16, $17, $18, NOW(), NOW()
		)
	`

	_, err = p.db.ExecContext(ctx, query,
		org.ID, org.Name, org.Slug,
		nullString(org.Description), nullString(org.Website), nullString(org.LogoURL),
		nullString(org.Address), nullString(org.City), nullString(org.State),
		nullString(org.Country), nullString(org.PostalCode), nullString(org.Phone),
		nullString(org.Email), settingsJSON, metadataJSON,
		org.IsActive, org.SubscriptionTier, org.SubscriptionExpiresAt,
	)

	if err != nil {
		return fmt.Errorf("failed to create organization: %w", err)
	}

	return nil
}

// UpdateOrganization updates an existing organization
func (p *PostGISDB) UpdateOrganization(ctx context.Context, org *models.Organization) error {
	settingsJSON, err := json.Marshal(org.Settings)
	if err != nil {
		return fmt.Errorf("failed to marshal settings: %w", err)
	}

	metadataJSON, err := json.Marshal(org.Metadata)
	if err != nil {
		return fmt.Errorf("failed to marshal metadata: %w", err)
	}

	query := `
		UPDATE organizations
		SET name = $2, slug = $3, description = $4, website = $5, logo_url = $6,
			address = $7, city = $8, state = $9, country = $10, postal_code = $11,
			phone = $12, email = $13, settings = $14, metadata = $15,
			is_active = $16, subscription_tier = $17, subscription_expires_at = $18,
			updated_at = NOW()
		WHERE id = $1
	`

	result, err := p.db.ExecContext(ctx, query,
		org.ID, org.Name, org.Slug,
		nullString(org.Description), nullString(org.Website), nullString(org.LogoURL),
		nullString(org.Address), nullString(org.City), nullString(org.State),
		nullString(org.Country), nullString(org.PostalCode), nullString(org.Phone),
		nullString(org.Email), settingsJSON, metadataJSON,
		org.IsActive, org.SubscriptionTier, org.SubscriptionExpiresAt,
	)

	if err != nil {
		return fmt.Errorf("failed to update organization: %w", err)
	}

	rowsAffected, _ := result.RowsAffected()
	if rowsAffected == 0 {
		return fmt.Errorf("organization not found")
	}

	return nil
}

// DeleteOrganization deletes an organization
func (p *PostGISDB) DeleteOrganization(ctx context.Context, id string) error {
	query := `DELETE FROM organizations WHERE id = $1`

	result, err := p.db.ExecContext(ctx, query, id)
	if err != nil {
		return fmt.Errorf("failed to delete organization: %w", err)
	}

	rowsAffected, _ := result.RowsAffected()
	if rowsAffected == 0 {
		return fmt.Errorf("organization not found")
	}

	return nil
}

// AddOrganizationMember adds a user to an organization
func (p *PostGISDB) AddOrganizationMember(ctx context.Context, orgID, userID, role string) error {
	// Validate role
	validRoles := map[string]bool{
		"owner":  true,
		"admin":  true,
		"member": true,
		"viewer": true,
	}

	if !validRoles[role] {
		return fmt.Errorf("invalid role: %s", role)
	}

	query := `
		INSERT INTO organization_members (
			id, organization_id, user_id, role, permissions, joined_at
		) VALUES (
			$1, $2, $3, $4, $5, NOW()
		)
	`

	memberID := uuid.New().String()
	permissions := json.RawMessage(`{}`)

	_, err := p.db.ExecContext(ctx, query, memberID, orgID, userID, role, permissions)
	if err != nil {
		return fmt.Errorf("failed to add organization member: %w", err)
	}

	return nil
}

// RemoveOrganizationMember removes a user from an organization
func (p *PostGISDB) RemoveOrganizationMember(ctx context.Context, orgID, userID string) error {
	query := `
		DELETE FROM organization_members
		WHERE organization_id = $1 AND user_id = $2
	`

	result, err := p.db.ExecContext(ctx, query, orgID, userID)
	if err != nil {
		return fmt.Errorf("failed to remove organization member: %w", err)
	}

	rowsAffected, _ := result.RowsAffected()
	if rowsAffected == 0 {
		return fmt.Errorf("member not found in organization")
	}

	return nil
}

// UpdateOrganizationMemberRole updates a member's role
func (p *PostGISDB) UpdateOrganizationMemberRole(ctx context.Context, orgID, userID, role string) error {
	// Validate role
	validRoles := map[string]bool{
		"owner":  true,
		"admin":  true,
		"member": true,
		"viewer": true,
	}

	if !validRoles[role] {
		return fmt.Errorf("invalid role: %s", role)
	}

	query := `
		UPDATE organization_members
		SET role = $3
		WHERE organization_id = $1 AND user_id = $2
	`

	result, err := p.db.ExecContext(ctx, query, orgID, userID, role)
	if err != nil {
		return fmt.Errorf("failed to update member role: %w", err)
	}

	rowsAffected, _ := result.RowsAffected()
	if rowsAffected == 0 {
		return fmt.Errorf("member not found in organization")
	}

	return nil
}

// GetOrganizationMembers gets all members of an organization
func (p *PostGISDB) GetOrganizationMembers(ctx context.Context, orgID string) ([]*models.OrganizationMember, error) {
	query := `
		SELECT om.id, om.organization_id, om.user_id, om.role, om.permissions, om.joined_at,
			   u.email, u.username, u.full_name, u.avatar_url
		FROM organization_members om
		JOIN users u ON om.user_id = u.id
		WHERE om.organization_id = $1
		ORDER BY om.joined_at DESC
	`

	rows, err := p.db.QueryContext(ctx, query, orgID)
	if err != nil {
		return nil, fmt.Errorf("failed to query organization members: %w", err)
	}
	defer rows.Close()

	var members []*models.OrganizationMember

	for rows.Next() {
		var member models.OrganizationMember
		var user models.User
		var permissions json.RawMessage
		var fullName, avatarURL sql.NullString

		err := rows.Scan(
			&member.ID, &member.OrganizationID, &member.UserID,
			&member.Role, &permissions, &member.JoinedAt,
			&user.Email, &user.Username, &fullName, &avatarURL,
		)

		if err != nil {
			return nil, fmt.Errorf("failed to scan member: %w", err)
		}

		// Parse permissions
		if permissions != nil {
			if err := json.Unmarshal(permissions, &member.Permissions); err != nil {
				return nil, fmt.Errorf("failed to parse permissions: %w", err)
			}
		}

		// Attach user info
		user.ID = member.UserID
		user.FullName = fullName.String
		user.AvatarURL = avatarURL.String
		member.User = &user

		members = append(members, &member)
	}

	if err := rows.Err(); err != nil {
		return nil, fmt.Errorf("error iterating members: %w", err)
	}

	return members, nil
}

// GetOrganizationMember gets a specific member
func (p *PostGISDB) GetOrganizationMember(ctx context.Context, orgID, userID string) (*models.OrganizationMember, error) {
	query := `
		SELECT om.id, om.organization_id, om.user_id, om.role, om.permissions, om.joined_at,
			   u.email, u.username, u.full_name, u.avatar_url
		FROM organization_members om
		JOIN users u ON om.user_id = u.id
		WHERE om.organization_id = $1 AND om.user_id = $2
	`

	var member models.OrganizationMember
	var user models.User
	var permissions json.RawMessage
	var fullName, avatarURL sql.NullString

	err := p.db.QueryRowContext(ctx, query, orgID, userID).Scan(
		&member.ID, &member.OrganizationID, &member.UserID,
		&member.Role, &permissions, &member.JoinedAt,
		&user.Email, &user.Username, &fullName, &avatarURL,
	)

	if err != nil {
		if err == sql.ErrNoRows {
			return nil, fmt.Errorf("member not found in organization")
		}
		return nil, fmt.Errorf("failed to get organization member: %w", err)
	}

	// Parse permissions
	if permissions != nil {
		if err := json.Unmarshal(permissions, &member.Permissions); err != nil {
			return nil, fmt.Errorf("failed to parse permissions: %w", err)
		}
	}

	// Attach user info
	user.ID = member.UserID
	user.FullName = fullName.String
	user.AvatarURL = avatarURL.String
	member.User = &user

	return &member, nil
}

// CreateOrganizationInvitation creates an invitation
func (p *PostGISDB) CreateOrganizationInvitation(ctx context.Context, invitation *models.OrganizationInvitation) error {
	if invitation.ID == "" {
		invitation.ID = uuid.New().String()
	}

	if invitation.Token == "" {
		invitation.Token = generateSecureToken(32)
	}

	if invitation.ExpiresAt.IsZero() {
		invitation.ExpiresAt = time.Now().Add(7 * 24 * time.Hour) // 7 days
	}

	query := `
		INSERT INTO organization_invitations (
			id, organization_id, email, role, token, invited_by, expires_at, created_at
		) VALUES (
			$1, $2, $3, $4, $5, $6, $7, NOW()
		)
	`

	_, err := p.db.ExecContext(ctx, query,
		invitation.ID, invitation.OrganizationID, invitation.Email,
		invitation.Role, invitation.Token, invitation.InvitedBy, invitation.ExpiresAt,
	)

	if err != nil {
		return fmt.Errorf("failed to create invitation: %w", err)
	}

	return nil
}

// GetOrganizationInvitationByToken gets invitation by token
func (p *PostGISDB) GetOrganizationInvitationByToken(ctx context.Context, token string) (*models.OrganizationInvitation, error) {
	query := `
		SELECT id, organization_id, email, role, token, invited_by,
			   accepted_at, expires_at, created_at
		FROM organization_invitations
		WHERE token = $1 AND expires_at > NOW() AND accepted_at IS NULL
	`

	var invitation models.OrganizationInvitation
	var acceptedAt sql.NullTime

	err := p.db.QueryRowContext(ctx, query, token).Scan(
		&invitation.ID, &invitation.OrganizationID, &invitation.Email,
		&invitation.Role, &invitation.Token, &invitation.InvitedBy,
		&acceptedAt, &invitation.ExpiresAt, &invitation.CreatedAt,
	)

	if err != nil {
		if err == sql.ErrNoRows {
			return nil, fmt.Errorf("invitation not found or expired")
		}
		return nil, fmt.Errorf("failed to get invitation: %w", err)
	}

	if acceptedAt.Valid {
		invitation.AcceptedAt = &acceptedAt.Time
	}

	return &invitation, nil
}

// GetOrganizationInvitation gets invitation by ID
func (p *PostGISDB) GetOrganizationInvitation(ctx context.Context, id string) (*models.OrganizationInvitation, error) {
	query := `
		SELECT id, organization_id, email, role, token, invited_by,
			   accepted_at, expires_at, created_at
		FROM organization_invitations
		WHERE id = $1
	`

	var invitation models.OrganizationInvitation
	var acceptedAt sql.NullTime

	err := p.db.QueryRowContext(ctx, query, id).Scan(
		&invitation.ID, &invitation.OrganizationID, &invitation.Email,
		&invitation.Role, &invitation.Token, &invitation.InvitedBy,
		&acceptedAt, &invitation.ExpiresAt, &invitation.CreatedAt,
	)

	if err != nil {
		if err == sql.ErrNoRows {
			return nil, fmt.Errorf("invitation not found")
		}
		return nil, fmt.Errorf("failed to get invitation: %w", err)
	}

	if acceptedAt.Valid {
		invitation.AcceptedAt = &acceptedAt.Time
	}

	return &invitation, nil
}

// ListOrganizationInvitations lists all invitations for an org
func (p *PostGISDB) ListOrganizationInvitations(ctx context.Context, orgID string) ([]*models.OrganizationInvitation, error) {
	query := `
		SELECT id, organization_id, email, role, token, invited_by,
			   accepted_at, expires_at, created_at
		FROM organization_invitations
		WHERE organization_id = $1
		ORDER BY created_at DESC
	`

	rows, err := p.db.QueryContext(ctx, query, orgID)
	if err != nil {
		return nil, fmt.Errorf("failed to query invitations: %w", err)
	}
	defer rows.Close()

	var invitations []*models.OrganizationInvitation

	for rows.Next() {
		var invitation models.OrganizationInvitation
		var acceptedAt sql.NullTime

		err := rows.Scan(
			&invitation.ID, &invitation.OrganizationID, &invitation.Email,
			&invitation.Role, &invitation.Token, &invitation.InvitedBy,
			&acceptedAt, &invitation.ExpiresAt, &invitation.CreatedAt,
		)

		if err != nil {
			return nil, fmt.Errorf("failed to scan invitation: %w", err)
		}

		if acceptedAt.Valid {
			invitation.AcceptedAt = &acceptedAt.Time
		}

		invitations = append(invitations, &invitation)
	}

	if err := rows.Err(); err != nil {
		return nil, fmt.Errorf("error iterating invitations: %w", err)
	}

	return invitations, nil
}

// AcceptOrganizationInvitation accepts an invitation
func (p *PostGISDB) AcceptOrganizationInvitation(ctx context.Context, token, userID string) error {
	// Start transaction
	tx, err := p.db.BeginTx(ctx, nil)
	if err != nil {
		return fmt.Errorf("failed to start transaction: %w", err)
	}
	defer tx.Rollback()

	// Get invitation details
	var orgID, role string
	query := `
		UPDATE organization_invitations
		SET accepted_at = NOW()
		WHERE token = $1 AND expires_at > NOW() AND accepted_at IS NULL
		RETURNING organization_id, role
	`

	err = tx.QueryRowContext(ctx, query, token).Scan(&orgID, &role)
	if err != nil {
		if err == sql.ErrNoRows {
			return fmt.Errorf("invitation not found or already used")
		}
		return fmt.Errorf("failed to accept invitation: %w", err)
	}

	// Add user to organization
	memberID := uuid.New().String()
	permissions := json.RawMessage(`{}`)

	insertQuery := `
		INSERT INTO organization_members (
			id, organization_id, user_id, role, permissions, joined_at
		) VALUES (
			$1, $2, $3, $4, $5, NOW()
		)
	`

	_, err = tx.ExecContext(ctx, insertQuery, memberID, orgID, userID, role, permissions)
	if err != nil {
		return fmt.Errorf("failed to add member to organization: %w", err)
	}

	// Commit transaction
	if err := tx.Commit(); err != nil {
		return fmt.Errorf("failed to commit transaction: %w", err)
	}

	return nil
}

// RevokeOrganizationInvitation revokes an invitation
func (p *PostGISDB) RevokeOrganizationInvitation(ctx context.Context, id string) error {
	query := `DELETE FROM organization_invitations WHERE id = $1 AND accepted_at IS NULL`

	result, err := p.db.ExecContext(ctx, query, id)
	if err != nil {
		return fmt.Errorf("failed to revoke invitation: %w", err)
	}

	rowsAffected, _ := result.RowsAffected()
	if rowsAffected == 0 {
		return fmt.Errorf("invitation not found or already accepted")
	}

	return nil
}