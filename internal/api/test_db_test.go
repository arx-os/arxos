package api_test

import (
	"context"
	"database/sql"
	"time"

	"github.com/arx-os/arxos/internal/database"
	"github.com/arx-os/arxos/pkg/models"
)

// TestDB wraps a sql.DB to implement the database.DB interface for testing
type TestDB struct {
	db *sql.DB
}

// NewTestDB creates a new test database wrapper
func NewTestDB(db *sql.DB) *TestDB {
	return &TestDB{db: db}
}

// Connect is a no-op for test database (already connected)
func (t *TestDB) Connect(ctx context.Context, dbPath string) error {
	return nil
}

// Close closes the underlying database
func (t *TestDB) Close() error {
	if t.db != nil {
		return t.db.Close()
	}
	return nil
}

// GetDB returns the underlying sql.DB
func (t *TestDB) GetDB() *sql.DB {
	return t.db
}

// User operations
func (t *TestDB) GetUser(ctx context.Context, id string) (*models.User, error) {
	var user models.User
	err := t.db.QueryRowContext(ctx,
		"SELECT id, email, username, password_hash, role, created_at FROM users WHERE id = ?",
		id).Scan(&user.ID, &user.Email, &user.Username, &user.PasswordHash, &user.Role, &user.CreatedAt)
	if err != nil {
		return nil, err
	}
	return &user, nil
}

func (t *TestDB) GetUserByEmail(ctx context.Context, email string) (*models.User, error) {
	var user models.User
	err := t.db.QueryRowContext(ctx,
		"SELECT id, email, username, password_hash, role, created_at FROM users WHERE email = ?",
		email).Scan(&user.ID, &user.Email, &user.Username, &user.PasswordHash, &user.Role, &user.CreatedAt)
	if err != nil {
		return nil, err
	}
	return &user, nil
}

func (t *TestDB) CreateUser(ctx context.Context, user *models.User) error {
	_, err := t.db.ExecContext(ctx,
		"INSERT INTO users (id, email, username, password_hash, role, created_at) VALUES (?, ?, ?, ?, ?, ?)",
		user.ID, user.Email, user.Username, user.PasswordHash, user.Role, time.Now())
	return err
}

func (t *TestDB) UpdateUser(ctx context.Context, user *models.User) error {
	_, err := t.db.ExecContext(ctx,
		"UPDATE users SET email = ?, username = ?, role = ? WHERE id = ?",
		user.Email, user.Username, user.Role, user.ID)
	return err
}

func (t *TestDB) DeleteUser(ctx context.Context, id string) error {
	_, err := t.db.ExecContext(ctx, "DELETE FROM users WHERE id = ?", id)
	return err
}

// Session operations
func (t *TestDB) CreateSession(ctx context.Context, session *models.UserSession) error {
	_, err := t.db.ExecContext(ctx,
		"INSERT INTO sessions (id, user_id, token, expires_at, created_at) VALUES (?, ?, ?, ?, ?)",
		session.ID, session.UserID, session.Token, session.ExpiresAt, session.CreatedAt)
	return err
}

func (t *TestDB) GetSession(ctx context.Context, token string) (*models.UserSession, error) {
	var session models.UserSession
	err := t.db.QueryRowContext(ctx,
		"SELECT id, user_id, token, expires_at, created_at FROM sessions WHERE token = ?",
		token).Scan(&session.ID, &session.UserID, &session.Token, &session.ExpiresAt, &session.CreatedAt)
	if err != nil {
		return nil, err
	}
	return &session, nil
}

func (t *TestDB) GetSessionByRefreshToken(ctx context.Context, refreshToken string) (*models.UserSession, error) {
	// For testing, we'll just return a mock session
	return nil, sql.ErrNoRows
}

func (t *TestDB) UpdateSession(ctx context.Context, session *models.UserSession) error {
	_, err := t.db.ExecContext(ctx,
		"UPDATE sessions SET expires_at = ? WHERE id = ?",
		session.ExpiresAt, session.ID)
	return err
}

func (t *TestDB) DeleteSession(ctx context.Context, id string) error {
	_, err := t.db.ExecContext(ctx, "DELETE FROM sessions WHERE id = ?", id)
	return err
}

func (t *TestDB) DeleteExpiredSessions(ctx context.Context) error {
	_, err := t.db.ExecContext(ctx, "DELETE FROM sessions WHERE expires_at < ?", time.Now())
	return err
}

func (t *TestDB) DeleteUserSessions(ctx context.Context, userID string) error {
	_, err := t.db.ExecContext(ctx, "DELETE FROM sessions WHERE user_id = ?", userID)
	return err
}

// Organization operations
func (t *TestDB) GetOrganization(ctx context.Context, id string) (*models.Organization, error) {
	return nil, sql.ErrNoRows
}

func (t *TestDB) GetOrganizationsByUser(ctx context.Context, userID string) ([]*models.Organization, error) {
	return []*models.Organization{}, nil
}

func (t *TestDB) CreateOrganization(ctx context.Context, org *models.Organization) error {
	return nil
}

func (t *TestDB) UpdateOrganization(ctx context.Context, org *models.Organization) error {
	return nil
}

func (t *TestDB) DeleteOrganization(ctx context.Context, id string) error {
	return nil
}

func (t *TestDB) AddOrganizationMember(ctx context.Context, orgID, userID, role string) error {
	return nil
}

func (t *TestDB) RemoveOrganizationMember(ctx context.Context, orgID, userID string) error {
	return nil
}

func (t *TestDB) UpdateOrganizationMemberRole(ctx context.Context, orgID, userID, role string) error {
	return nil
}

func (t *TestDB) GetOrganizationMembers(ctx context.Context, orgID string) ([]*models.OrganizationMember, error) {
	return []*models.OrganizationMember{}, nil
}

func (t *TestDB) GetOrganizationMember(ctx context.Context, orgID, userID string) (*models.OrganizationMember, error) {
	return nil, sql.ErrNoRows
}

// Ensure TestDB implements database.DB
var _ database.DB = (*TestDB)(nil)