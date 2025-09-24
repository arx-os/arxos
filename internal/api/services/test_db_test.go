package services_test

import (
	"context"
	"database/sql"
	"time"

	"github.com/arx-os/arxos/internal/database"
	"github.com/arx-os/arxos/pkg/models"
	syncpkg "github.com/arx-os/arxos/pkg/sync"
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

func (t *TestDB) AcceptOrganizationInvitation(ctx context.Context, token, userID string) error {
	// Mock implementation for testing
	return nil
}

func (t *TestDB) BeginTx(ctx context.Context) (*sql.Tx, error) {
	// Mock implementation for testing
	return t.db.BeginTx(ctx, nil)
}

func (t *TestDB) CreateOrganizationInvitation(ctx context.Context, invitation *models.OrganizationInvitation) error {
	// Mock implementation for testing
	return nil
}

func (t *TestDB) ApplyChange(ctx context.Context, change *syncpkg.Change) error {
	// Mock implementation for testing
	return nil
}

func (t *TestDB) CreatePasswordResetToken(ctx context.Context, token *models.PasswordResetToken) error {
	// Mock implementation for testing
	return nil
}

func (t *TestDB) DeleteEquipment(ctx context.Context, id string) error {
	// Mock implementation for testing
	return nil
}

func (t *TestDB) DeleteExpiredPasswordResetTokens(ctx context.Context) error {
	// Mock implementation for testing
	return nil
}

func (t *TestDB) DeleteFloorPlan(ctx context.Context, id string) error {
	// Mock implementation for testing
	return nil
}

func (t *TestDB) DeleteRoom(ctx context.Context, id string) error {
	// Mock implementation for testing
	return nil
}

func (t *TestDB) Exec(ctx context.Context, query string, args ...interface{}) (sql.Result, error) {
	// Mock implementation for testing
	return nil, nil
}

func (t *TestDB) GetAllFloorPlans(ctx context.Context) ([]*models.FloorPlan, error) {
	// Mock implementation for testing
	return []*models.FloorPlan{}, nil
}

func (t *TestDB) GetEquipment(ctx context.Context, id string) (*models.Equipment, error) {
	// Mock implementation for testing
	return nil, nil
}

func (t *TestDB) GetEquipmentByFloorPlan(ctx context.Context, floorPlanID string) ([]*models.Equipment, error) {
	// Mock implementation for testing
	return []*models.Equipment{}, nil
}

func (t *TestDB) GetFloorPlan(ctx context.Context, id string) (*models.FloorPlan, error) {
	// Mock implementation for testing
	return nil, nil
}

func (t *TestDB) GetOrganizationInvitation(ctx context.Context, token string) (*models.OrganizationInvitation, error) {
	// Mock implementation for testing
	return nil, nil
}

func (t *TestDB) GetOrganizationInvitationByToken(ctx context.Context, token string) (*models.OrganizationInvitation, error) {
	// Mock implementation for testing
	return nil, nil
}

func (t *TestDB) GetPasswordResetToken(ctx context.Context, token string) (*models.PasswordResetToken, error) {
	// Mock implementation for testing
	return nil, nil
}

func (t *TestDB) GetRoom(ctx context.Context, id string) (*models.Room, error) {
	// Mock implementation for testing
	return nil, nil
}

func (t *TestDB) GetRoomsByFloorPlan(ctx context.Context, floorPlanID string) ([]*models.Room, error) {
	// Mock implementation for testing
	return []*models.Room{}, nil
}

func (t *TestDB) GetSpatialDB() (database.SpatialDB, error) {
	// Mock implementation for testing
	return nil, nil
}

func (t *TestDB) GetVersion(ctx context.Context) (int, error) {
	// Mock implementation for testing
	return 1, nil
}

func (t *TestDB) HasSpatialSupport() bool {
	// Mock implementation for testing
	return true
}

func (t *TestDB) ListOrganizationInvitations(ctx context.Context, orgID string) ([]*models.OrganizationInvitation, error) {
	// Mock implementation for testing
	return []*models.OrganizationInvitation{}, nil
}

func (t *TestDB) MarkPasswordResetTokenUsed(ctx context.Context, token string) error {
	// Mock implementation for testing
	return nil
}

func (t *TestDB) Migrate(ctx context.Context) error {
	// Mock implementation for testing
	return nil
}

func (t *TestDB) Query(ctx context.Context, query string, args ...interface{}) (*sql.Rows, error) {
	// Mock implementation for testing
	return nil, nil
}

func (t *TestDB) QueryRow(ctx context.Context, query string, args ...interface{}) *sql.Row {
	// Mock implementation for testing
	return nil
}

func (t *TestDB) RevokeOrganizationInvitation(ctx context.Context, invitationID string) error {
	// Mock implementation for testing
	return nil
}

func (t *TestDB) SaveEquipment(ctx context.Context, equipment *models.Equipment) error {
	// Mock implementation for testing
	return nil
}

func (t *TestDB) SaveFloorPlan(ctx context.Context, floorPlan *models.FloorPlan) error {
	// Mock implementation for testing
	return nil
}

func (t *TestDB) SaveRoom(ctx context.Context, room *models.Room) error {
	// Mock implementation for testing
	return nil
}

func (t *TestDB) UpdateEquipment(ctx context.Context, equipment *models.Equipment) error {
	// Mock implementation for testing
	return nil
}

func (t *TestDB) UpdateFloorPlan(ctx context.Context, floorPlan *models.FloorPlan) error {
	// Mock implementation for testing
	return nil
}

func (t *TestDB) UpdateRoom(ctx context.Context, room *models.Room) error {
	// Mock implementation for testing
	return nil
}

func (t *TestDB) GetChangesSince(ctx context.Context, since time.Time, entityType string) ([]*syncpkg.Change, error) {
	// Mock implementation for testing
	return []*syncpkg.Change{}, nil
}

func (t *TestDB) GetConflictCount(ctx context.Context, buildingID string) (int, error) {
	// Mock implementation for testing
	return 0, nil
}

func (t *TestDB) GetEntityVersion(ctx context.Context, entityType, entityID string) (int, error) {
	// Mock implementation for testing
	return 1, nil
}

func (t *TestDB) GetLastSyncTime(ctx context.Context, buildingID string) (time.Time, error) {
	// Mock implementation for testing
	return time.Now(), nil
}

func (t *TestDB) GetPendingChangesCount(ctx context.Context, buildingID string) (int, error) {
	// Mock implementation for testing
	return 0, nil
}

func (t *TestDB) GetPendingConflicts(ctx context.Context, buildingID string) ([]*syncpkg.Conflict, error) {
	// Mock implementation for testing
	return []*syncpkg.Conflict{}, nil
}

func (t *TestDB) ListUsers(ctx context.Context, limit, offset int) ([]*models.User, error) {
	// Mock implementation for testing
	return []*models.User{}, nil
}

func (t *TestDB) ResolveConflict(ctx context.Context, conflictID string, resolution string) error {
	// Mock implementation for testing
	return nil
}

func (t *TestDB) SaveConflict(ctx context.Context, conflict *syncpkg.Conflict) error {
	// Mock implementation for testing
	return nil
}

func (t *TestDB) UpdateLastSyncTime(ctx context.Context, buildingID string, syncTime time.Time) error {
	// Mock implementation for testing
	return nil
}

// Ensure TestDB implements database.DB
var _ database.DB = (*TestDB)(nil)
