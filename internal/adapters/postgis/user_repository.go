package postgis

import (
	"context"
	"database/sql"
	"fmt"
	"time"

	"github.com/google/uuid"
	"github.com/arx-os/arxos/internal/core/user"
)

// UserRepository implements user.Repository using PostGIS
type UserRepository struct {
	client *Client
}

// NewUserRepository creates a new user repository
func NewUserRepository(client *Client) *UserRepository {
	return &UserRepository{client: client}
}

// User operations

func (r *UserRepository) Create(ctx context.Context, u *user.User) error {
	query := `
		INSERT INTO users (id, email, full_name, password_hash, role, status, created_at, updated_at)
		VALUES ($1, $2, $3, $4, $5, $6, $7, $8)`

	_, err := r.client.db.ExecContext(ctx, query,
		u.ID, u.Email, u.FullName, u.PasswordHash, u.Role, u.Status, u.CreatedAt, u.UpdatedAt)
	if err != nil {
		return fmt.Errorf("failed to create user: %w", err)
	}

	return nil
}

func (r *UserRepository) GetByID(ctx context.Context, id uuid.UUID) (*user.User, error) {
	query := `
		SELECT id, email, full_name, password_hash, role, status, last_login, created_at, updated_at
		FROM users WHERE id = $1`

	u := &user.User{}
	err := r.client.db.GetContext(ctx, u, query, id)
	if err == sql.ErrNoRows {
		return nil, fmt.Errorf("user not found")
	}
	if err != nil {
		return nil, fmt.Errorf("failed to get user: %w", err)
	}

	return u, nil
}

func (r *UserRepository) GetByEmail(ctx context.Context, email string) (*user.User, error) {
	query := `
		SELECT id, email, full_name, password_hash, role, status, last_login, created_at, updated_at
		FROM users WHERE email = $1`

	u := &user.User{}
	err := r.client.db.GetContext(ctx, u, query, email)
	if err == sql.ErrNoRows {
		return nil, fmt.Errorf("user not found")
	}
	if err != nil {
		return nil, fmt.Errorf("failed to get user by email: %w", err)
	}

	return u, nil
}

func (r *UserRepository) Update(ctx context.Context, u *user.User) error {
	query := `
		UPDATE users
		SET email = $2, full_name = $3, password_hash = $4, role = $5, status = $6,
		    last_login = $7, updated_at = $8
		WHERE id = $1`

	_, err := r.client.db.ExecContext(ctx, query,
		u.ID, u.Email, u.FullName, u.PasswordHash, u.Role, u.Status, u.LastLogin, u.UpdatedAt)
	if err != nil {
		return fmt.Errorf("failed to update user: %w", err)
	}

	return nil
}

func (r *UserRepository) Delete(ctx context.Context, id uuid.UUID) error {
	query := `DELETE FROM users WHERE id = $1`
	_, err := r.client.db.ExecContext(ctx, query, id)
	if err != nil {
		return fmt.Errorf("failed to delete user: %w", err)
	}

	return nil
}

func (r *UserRepository) List(ctx context.Context, limit, offset int) ([]*user.User, error) {
	query := `
		SELECT id, email, full_name, password_hash, role, status, last_login, created_at, updated_at
		FROM users
		ORDER BY created_at DESC
		LIMIT $1 OFFSET $2`

	users := []*user.User{}
	err := r.client.db.SelectContext(ctx, &users, query, limit, offset)
	if err != nil {
		return nil, fmt.Errorf("failed to list users: %w", err)
	}

	return users, nil
}

// Session operations

func (r *UserRepository) CreateSession(ctx context.Context, s *user.UserSession) error {
	query := `
		INSERT INTO user_sessions (id, user_id, token, refresh_token, expires_at, created_at, updated_at)
		VALUES ($1, $2, $3, $4, $5, $6, $7)`

	_, err := r.client.db.ExecContext(ctx, query,
		s.ID, s.UserID, s.Token, s.RefreshToken, s.ExpiresAt, s.CreatedAt, s.UpdatedAt)
	if err != nil {
		return fmt.Errorf("failed to create session: %w", err)
	}

	return nil
}

func (r *UserRepository) GetSession(ctx context.Context, token string) (*user.UserSession, error) {
	query := `
		SELECT id, user_id, token, refresh_token, expires_at, created_at, updated_at
		FROM user_sessions WHERE token = $1`

	s := &user.UserSession{}
	err := r.client.db.GetContext(ctx, s, query, token)
	if err == sql.ErrNoRows {
		return nil, fmt.Errorf("session not found")
	}
	if err != nil {
		return nil, fmt.Errorf("failed to get session: %w", err)
	}

	return s, nil
}

func (r *UserRepository) GetSessionByRefreshToken(ctx context.Context, refreshToken string) (*user.UserSession, error) {
	query := `
		SELECT id, user_id, token, refresh_token, expires_at, created_at, updated_at
		FROM user_sessions WHERE refresh_token = $1`

	s := &user.UserSession{}
	err := r.client.db.GetContext(ctx, s, query, refreshToken)
	if err == sql.ErrNoRows {
		return nil, fmt.Errorf("session not found")
	}
	if err != nil {
		return nil, fmt.Errorf("failed to get session by refresh token: %w", err)
	}

	return s, nil
}

func (r *UserRepository) UpdateSession(ctx context.Context, s *user.UserSession) error {
	query := `
		UPDATE user_sessions
		SET token = $2, refresh_token = $3, expires_at = $4, updated_at = $5
		WHERE id = $1`

	_, err := r.client.db.ExecContext(ctx, query,
		s.ID, s.Token, s.RefreshToken, s.ExpiresAt, s.UpdatedAt)
	if err != nil {
		return fmt.Errorf("failed to update session: %w", err)
	}

	return nil
}

func (r *UserRepository) DeleteSession(ctx context.Context, id uuid.UUID) error {
	query := `DELETE FROM user_sessions WHERE id = $1`
	_, err := r.client.db.ExecContext(ctx, query, id)
	if err != nil {
		return fmt.Errorf("failed to delete session: %w", err)
	}

	return nil
}

func (r *UserRepository) DeleteUserSessions(ctx context.Context, userID uuid.UUID) error {
	query := `DELETE FROM user_sessions WHERE user_id = $1`
	_, err := r.client.db.ExecContext(ctx, query, userID)
	if err != nil {
		return fmt.Errorf("failed to delete user sessions: %w", err)
	}

	return nil
}

func (r *UserRepository) DeleteExpiredSessions(ctx context.Context) error {
	query := `DELETE FROM user_sessions WHERE expires_at < $1`
	_, err := r.client.db.ExecContext(ctx, query, time.Now())
	if err != nil {
		return fmt.Errorf("failed to delete expired sessions: %w", err)
	}

	return nil
}

// Password reset operations

func (r *UserRepository) CreatePasswordResetToken(ctx context.Context, t *user.PasswordResetToken) error {
	query := `
		INSERT INTO password_reset_tokens (id, user_id, token, used, expires_at, created_at)
		VALUES ($1, $2, $3, $4, $5, $6)`

	_, err := r.client.db.ExecContext(ctx, query,
		t.ID, t.UserID, t.Token, t.Used, t.ExpiresAt, t.CreatedAt)
	if err != nil {
		return fmt.Errorf("failed to create password reset token: %w", err)
	}

	return nil
}

func (r *UserRepository) GetPasswordResetToken(ctx context.Context, token string) (*user.PasswordResetToken, error) {
	query := `
		SELECT id, user_id, token, used, expires_at, created_at
		FROM password_reset_tokens WHERE token = $1`

	t := &user.PasswordResetToken{}
	err := r.client.db.GetContext(ctx, t, query, token)
	if err == sql.ErrNoRows {
		return nil, fmt.Errorf("token not found")
	}
	if err != nil {
		return nil, fmt.Errorf("failed to get password reset token: %w", err)
	}

	return t, nil
}

func (r *UserRepository) MarkPasswordResetTokenUsed(ctx context.Context, token string) error {
	query := `UPDATE password_reset_tokens SET used = true WHERE token = $1`
	_, err := r.client.db.ExecContext(ctx, query, token)
	if err != nil {
		return fmt.Errorf("failed to mark token as used: %w", err)
	}

	return nil
}

func (r *UserRepository) DeleteExpiredPasswordResetTokens(ctx context.Context) error {
	query := `DELETE FROM password_reset_tokens WHERE expires_at < $1`
	_, err := r.client.db.ExecContext(ctx, query, time.Now())
	if err != nil {
		return fmt.Errorf("failed to delete expired tokens: %w", err)
	}

	return nil
}

// Organization operations

func (r *UserRepository) CreateOrganization(ctx context.Context, org *user.Organization) error {
	query := `
		INSERT INTO organizations (id, name, description, created_by, created_at, updated_at)
		VALUES ($1, $2, $3, $4, $5, $6)`

	_, err := r.client.db.ExecContext(ctx, query,
		org.ID, org.Name, org.Description, org.CreatedBy, org.CreatedAt, org.UpdatedAt)
	if err != nil {
		return fmt.Errorf("failed to create organization: %w", err)
	}

	return nil
}

func (r *UserRepository) GetOrganization(ctx context.Context, id uuid.UUID) (*user.Organization, error) {
	query := `
		SELECT id, name, description, created_by, created_at, updated_at
		FROM organizations WHERE id = $1`

	org := &user.Organization{}
	err := r.client.db.GetContext(ctx, org, query, id)
	if err == sql.ErrNoRows {
		return nil, fmt.Errorf("organization not found")
	}
	if err != nil {
		return nil, fmt.Errorf("failed to get organization: %w", err)
	}

	return org, nil
}

func (r *UserRepository) GetOrganizationsByUser(ctx context.Context, userID uuid.UUID) ([]*user.Organization, error) {
	query := `
		SELECT o.id, o.name, o.description, o.created_by, o.created_at, o.updated_at
		FROM organizations o
		JOIN organization_members om ON o.id = om.organization_id
		WHERE om.user_id = $1
		ORDER BY o.name`

	orgs := []*user.Organization{}
	err := r.client.db.SelectContext(ctx, &orgs, query, userID)
	if err != nil {
		return nil, fmt.Errorf("failed to get user organizations: %w", err)
	}

	return orgs, nil
}

func (r *UserRepository) UpdateOrganization(ctx context.Context, org *user.Organization) error {
	query := `
		UPDATE organizations
		SET name = $2, description = $3, updated_at = $4
		WHERE id = $1`

	_, err := r.client.db.ExecContext(ctx, query,
		org.ID, org.Name, org.Description, org.UpdatedAt)
	if err != nil {
		return fmt.Errorf("failed to update organization: %w", err)
	}

	return nil
}

func (r *UserRepository) DeleteOrganization(ctx context.Context, id uuid.UUID) error {
	query := `DELETE FROM organizations WHERE id = $1`
	_, err := r.client.db.ExecContext(ctx, query, id)
	if err != nil {
		return fmt.Errorf("failed to delete organization: %w", err)
	}

	return nil
}

// Organization member operations

func (r *UserRepository) AddOrganizationMember(ctx context.Context, orgID, userID uuid.UUID, role string) error {
	query := `
		INSERT INTO organization_members (organization_id, user_id, role, joined_at)
		VALUES ($1, $2, $3, $4)`

	_, err := r.client.db.ExecContext(ctx, query, orgID, userID, role, time.Now())
	if err != nil {
		return fmt.Errorf("failed to add organization member: %w", err)
	}

	return nil
}

func (r *UserRepository) RemoveOrganizationMember(ctx context.Context, orgID, userID uuid.UUID) error {
	query := `DELETE FROM organization_members WHERE organization_id = $1 AND user_id = $2`
	_, err := r.client.db.ExecContext(ctx, query, orgID, userID)
	if err != nil {
		return fmt.Errorf("failed to remove organization member: %w", err)
	}

	return nil
}

func (r *UserRepository) UpdateOrganizationMemberRole(ctx context.Context, orgID, userID uuid.UUID, role string) error {
	query := `
		UPDATE organization_members
		SET role = $3
		WHERE organization_id = $1 AND user_id = $2`

	_, err := r.client.db.ExecContext(ctx, query, orgID, userID, role)
	if err != nil {
		return fmt.Errorf("failed to update member role: %w", err)
	}

	return nil
}

func (r *UserRepository) GetOrganizationMembers(ctx context.Context, orgID uuid.UUID) ([]*user.OrganizationMember, error) {
	query := `
		SELECT organization_id, user_id, role, joined_at
		FROM organization_members
		WHERE organization_id = $1
		ORDER BY joined_at`

	members := []*user.OrganizationMember{}
	err := r.client.db.SelectContext(ctx, &members, query, orgID)
	if err != nil {
		return nil, fmt.Errorf("failed to get organization members: %w", err)
	}

	return members, nil
}

func (r *UserRepository) GetOrganizationMember(ctx context.Context, orgID, userID uuid.UUID) (*user.OrganizationMember, error) {
	query := `
		SELECT organization_id, user_id, role, joined_at
		FROM organization_members
		WHERE organization_id = $1 AND user_id = $2`

	member := &user.OrganizationMember{}
	err := r.client.db.GetContext(ctx, member, query, orgID, userID)
	if err == sql.ErrNoRows {
		return nil, fmt.Errorf("member not found")
	}
	if err != nil {
		return nil, fmt.Errorf("failed to get member: %w", err)
	}

	return member, nil
}

// Organization invitation operations

func (r *UserRepository) CreateOrganizationInvitation(ctx context.Context, inv *user.OrganizationInvitation) error {
	query := `
		INSERT INTO organization_invitations
		(id, organization_id, email, role, token, invited_by, expires_at, created_at)
		VALUES ($1, $2, $3, $4, $5, $6, $7, $8)`

	_, err := r.client.db.ExecContext(ctx, query,
		inv.ID, inv.OrganizationID, inv.Email, inv.Role, inv.Token,
		inv.InvitedBy, inv.ExpiresAt, inv.CreatedAt)
	if err != nil {
		return fmt.Errorf("failed to create invitation: %w", err)
	}

	return nil
}

func (r *UserRepository) GetOrganizationInvitation(ctx context.Context, id uuid.UUID) (*user.OrganizationInvitation, error) {
	query := `
		SELECT id, organization_id, email, role, token, invited_by, accepted_at, expires_at, created_at
		FROM organization_invitations WHERE id = $1`

	inv := &user.OrganizationInvitation{}
	err := r.client.db.GetContext(ctx, inv, query, id)
	if err == sql.ErrNoRows {
		return nil, fmt.Errorf("invitation not found")
	}
	if err != nil {
		return nil, fmt.Errorf("failed to get invitation: %w", err)
	}

	return inv, nil
}

func (r *UserRepository) GetOrganizationInvitationByToken(ctx context.Context, token string) (*user.OrganizationInvitation, error) {
	query := `
		SELECT id, organization_id, email, role, token, invited_by, accepted_at, expires_at, created_at
		FROM organization_invitations WHERE token = $1`

	inv := &user.OrganizationInvitation{}
	err := r.client.db.GetContext(ctx, inv, query, token)
	if err == sql.ErrNoRows {
		return nil, fmt.Errorf("invitation not found")
	}
	if err != nil {
		return nil, fmt.Errorf("failed to get invitation by token: %w", err)
	}

	return inv, nil
}

func (r *UserRepository) ListOrganizationInvitations(ctx context.Context, orgID uuid.UUID) ([]*user.OrganizationInvitation, error) {
	query := `
		SELECT id, organization_id, email, role, token, invited_by, accepted_at, expires_at, created_at
		FROM organization_invitations
		WHERE organization_id = $1
		ORDER BY created_at DESC`

	invitations := []*user.OrganizationInvitation{}
	err := r.client.db.SelectContext(ctx, &invitations, query, orgID)
	if err != nil {
		return nil, fmt.Errorf("failed to list invitations: %w", err)
	}

	return invitations, nil
}

func (r *UserRepository) AcceptOrganizationInvitation(ctx context.Context, token string, userID uuid.UUID) error {
	// Start transaction
	tx, err := r.client.db.BeginTxx(ctx, nil)
	if err != nil {
		return fmt.Errorf("failed to begin transaction: %w", err)
	}
	defer tx.Rollback()

	// Get invitation
	var inv user.OrganizationInvitation
	query := `
		SELECT id, organization_id, email, role, token, invited_by, accepted_at, expires_at, created_at
		FROM organization_invitations WHERE token = $1 AND accepted_at IS NULL`

	err = tx.GetContext(ctx, &inv, query, token)
	if err != nil {
		return fmt.Errorf("invitation not found or already accepted: %w", err)
	}

	// Check expiration
	if time.Now().After(inv.ExpiresAt) {
		return fmt.Errorf("invitation has expired")
	}

	// Mark as accepted
	now := time.Now()
	updateQuery := `UPDATE organization_invitations SET accepted_at = $1 WHERE id = $2`
	_, err = tx.ExecContext(ctx, updateQuery, now, inv.ID)
	if err != nil {
		return fmt.Errorf("failed to mark invitation as accepted: %w", err)
	}

	// Add user to organization
	addMemberQuery := `
		INSERT INTO organization_members (organization_id, user_id, role, joined_at)
		VALUES ($1, $2, $3, $4)`
	_, err = tx.ExecContext(ctx, addMemberQuery, inv.OrganizationID, userID, inv.Role, now)
	if err != nil {
		return fmt.Errorf("failed to add member to organization: %w", err)
	}

	return tx.Commit()
}

func (r *UserRepository) RevokeOrganizationInvitation(ctx context.Context, id uuid.UUID) error {
	query := `DELETE FROM organization_invitations WHERE id = $1 AND accepted_at IS NULL`
	result, err := r.client.db.ExecContext(ctx, query, id)
	if err != nil {
		return fmt.Errorf("failed to revoke invitation: %w", err)
	}

	rows, err := result.RowsAffected()
	if err != nil {
		return fmt.Errorf("failed to check rows affected: %w", err)
	}

	if rows == 0 {
		return fmt.Errorf("invitation not found or already accepted")
	}

	return nil
}