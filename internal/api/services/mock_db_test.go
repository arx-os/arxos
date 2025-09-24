package services

import (
	"context"
	"time"

	"github.com/arx-os/arxos/internal/database"
	pkgmodels "github.com/arx-os/arxos/pkg/models"
	"github.com/stretchr/testify/mock"
)

// MockDB is a mock implementation of database.DB
type MockDB struct {
	mock.Mock
	database.DB // Embed interface to automatically satisfy all methods
}

func (m *MockDB) GetUser(ctx context.Context, id string) (*pkgmodels.User, error) {
	args := m.Called(ctx, id)
	if args.Get(0) == nil {
		return nil, args.Error(1)
	}
	return args.Get(0).(*pkgmodels.User), args.Error(1)
}

func (m *MockDB) GetUserByEmail(ctx context.Context, email string) (*pkgmodels.User, error) {
	args := m.Called(ctx, email)
	if args.Get(0) == nil {
		return nil, args.Error(1)
	}
	return args.Get(0).(*pkgmodels.User), args.Error(1)
}

func (m *MockDB) CreateUser(ctx context.Context, user *pkgmodels.User) error {
	args := m.Called(ctx, user)
	return args.Error(0)
}

func (m *MockDB) UpdateUser(ctx context.Context, user *pkgmodels.User) error {
	args := m.Called(ctx, user)
	return args.Error(0)
}

func (m *MockDB) DeleteUser(ctx context.Context, id string) error {
	args := m.Called(ctx, id)
	return args.Error(0)
}

func (m *MockDB) CreateSession(ctx context.Context, session *pkgmodels.UserSession) error {
	args := m.Called(ctx, session)
	return args.Error(0)
}

func (m *MockDB) GetSession(ctx context.Context, token string) (*pkgmodels.UserSession, error) {
	args := m.Called(ctx, token)
	if args.Get(0) == nil {
		return nil, args.Error(1)
	}
	return args.Get(0).(*pkgmodels.UserSession), args.Error(1)
}

func (m *MockDB) GetSessionByRefreshToken(ctx context.Context, refreshToken string) (*pkgmodels.UserSession, error) {
	args := m.Called(ctx, refreshToken)
	if args.Get(0) == nil {
		return nil, args.Error(1)
	}
	return args.Get(0).(*pkgmodels.UserSession), args.Error(1)
}

func (m *MockDB) UpdateSession(ctx context.Context, session *pkgmodels.UserSession) error {
	args := m.Called(ctx, session)
	return args.Error(0)
}

func (m *MockDB) DeleteSession(ctx context.Context, id string) error {
	args := m.Called(ctx, id)
	return args.Error(0)
}

func (m *MockDB) DeleteExpiredSessions(ctx context.Context) error {
	args := m.Called(ctx)
	return args.Error(0)
}

func (m *MockDB) DeleteUserSessions(ctx context.Context, userID string) error {
	args := m.Called(ctx, userID)
	return args.Error(0)
}

func (m *MockDB) GetOrganization(ctx context.Context, id string) (*pkgmodels.Organization, error) {
	args := m.Called(ctx, id)
	if args.Get(0) == nil {
		return nil, args.Error(1)
	}
	return args.Get(0).(*pkgmodels.Organization), args.Error(1)
}

func (m *MockDB) GetOrganizationsByUser(ctx context.Context, userID string) ([]*pkgmodels.Organization, error) {
	args := m.Called(ctx, userID)
	if args.Get(0) == nil {
		return nil, args.Error(1)
	}
	return args.Get(0).([]*pkgmodels.Organization), args.Error(1)
}

func (m *MockDB) CreateOrganization(ctx context.Context, org *pkgmodels.Organization) error {
	args := m.Called(ctx, org)
	return args.Error(0)
}

func (m *MockDB) UpdateOrganization(ctx context.Context, org *pkgmodels.Organization) error {
	args := m.Called(ctx, org)
	return args.Error(0)
}

func (m *MockDB) DeleteOrganization(ctx context.Context, id string) error {
	args := m.Called(ctx, id)
	return args.Error(0)
}

func (m *MockDB) AddOrganizationMember(ctx context.Context, orgID, userID, role string) error {
	args := m.Called(ctx, orgID, userID, role)
	return args.Error(0)
}

func (m *MockDB) RemoveOrganizationMember(ctx context.Context, orgID, userID string) error {
	args := m.Called(ctx, orgID, userID)
	return args.Error(0)
}

func (m *MockDB) UpdateOrganizationMemberRole(ctx context.Context, orgID, userID, role string) error {
	args := m.Called(ctx, orgID, userID, role)
	return args.Error(0)
}

func (m *MockDB) GetOrganizationMembers(ctx context.Context, orgID string) ([]*pkgmodels.OrganizationMember, error) {
	args := m.Called(ctx, orgID)
	if args.Get(0) == nil {
		return nil, args.Error(1)
	}
	return args.Get(0).([]*pkgmodels.OrganizationMember), args.Error(1)
}

func (m *MockDB) GetOrganizationMember(ctx context.Context, orgID, userID string) (*pkgmodels.OrganizationMember, error) {
	args := m.Called(ctx, orgID, userID)
	if args.Get(0) == nil {
		return nil, args.Error(1)
	}
	return args.Get(0).(*pkgmodels.OrganizationMember), args.Error(1)
}

// Test helper functions

func createTestUser(email string, password string, active bool) *pkgmodels.User {
	now := time.Now()
	return &pkgmodels.User{
		ID:           "test-user-id",
		Email:        email,
		FullName:     "Test User",
		PasswordHash: password, // In tests, we'll use plain password for simplicity
		IsActive:     active,
		CreatedAt:    now,
		UpdatedAt:    now,
	}
}

func createTestSession(userID, token, refreshToken string) *pkgmodels.UserSession {
	return &pkgmodels.UserSession{
		ID:           "session-id",
		UserID:       userID,
		Token:        token,
		RefreshToken: refreshToken,
		ExpiresAt:    time.Now().Add(15 * time.Minute),
		CreatedAt:    time.Now(),
		LastAccessAt: time.Now(),
	}
}
