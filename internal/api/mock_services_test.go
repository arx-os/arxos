package api_test

import (
	"context"
	"errors"
	"time"

	"github.com/arx-os/arxos/internal/api"
	"github.com/arx-os/arxos/internal/bim"
	"github.com/arx-os/arxos/pkg/models"
)

// MockAuthService is a mock implementation of AuthService
type MockAuthService struct {
	Users     map[string]*models.User
	Sessions  map[string]*models.UserSession
	EnableAuth bool
}

func NewMockAuthService() *MockAuthService {
	return &MockAuthService{
		Users:     make(map[string]*models.User),
		Sessions:  make(map[string]*models.UserSession),
		EnableAuth: false,
	}
}

func (m *MockAuthService) Login(ctx context.Context, username, password string) (*api.AuthResponse, error) {
	// Simple mock implementation
	if username == "testuser" && password == "TestPass123!" {
		return &api.AuthResponse{
			Token:        "test-token",
			RefreshToken: "test-refresh-token",
			ExpiresAt:    time.Now().Add(1 * time.Hour),
		}, nil
	}
	return nil, errors.New("invalid credentials")
}

func (m *MockAuthService) Register(ctx context.Context, email, password, name string) (*api.User, error) {
	// Simple mock implementation
	return &api.User{
		ID:    "new-user-id",
		Email: email,
		Name:  name,
	}, nil
}

func (m *MockAuthService) RefreshToken(ctx context.Context, refreshToken string) (*api.AuthResponse, error) {
	if refreshToken == "test-refresh-token" {
		return &api.AuthResponse{
			Token:        "new-test-token",
			RefreshToken: "new-refresh-token",
			ExpiresAt:    time.Now().Add(1 * time.Hour),
		}, nil
	}
	return nil, errors.New("invalid refresh token")
}

func (m *MockAuthService) Logout(ctx context.Context, token string) error {
	delete(m.Sessions, token)
	return nil
}

func (m *MockAuthService) ValidateToken(ctx context.Context, token string) (*api.TokenClaims, error) {
	if !m.EnableAuth {
		// Auth disabled, return default claims
		return &api.TokenClaims{
			UserID: "test-user",
			Email:  "test@example.com",
		}, nil
	}

	if token == "test-token" || token == "new-test-token" {
		return &api.TokenClaims{
			UserID: "test-user",
			Email:  "test@example.com",
		}, nil
	}
	return nil, errors.New("invalid token")
}

func (m *MockAuthService) RevokeToken(ctx context.Context, token string) error {
	delete(m.Sessions, token)
	return nil
}

// MockBuildingService is a mock implementation of BuildingService
type MockBuildingService struct {
	Buildings map[string]*bim.Building
}

func NewMockBuildingService() *MockBuildingService {
	return &MockBuildingService{
		Buildings: make(map[string]*bim.Building),
	}
}

func (m *MockBuildingService) CreateBuilding(ctx context.Context, building *bim.Building) error {
	m.Buildings[building.ID] = building
	return nil
}

func (m *MockBuildingService) GetBuilding(ctx context.Context, id string) (*bim.Building, error) {
	if b, ok := m.Buildings[id]; ok {
		return b, nil
	}
	return nil, errors.New("building not found")
}

func (m *MockBuildingService) UpdateBuilding(ctx context.Context, building *bim.Building) error {
	m.Buildings[building.ID] = building
	return nil
}

func (m *MockBuildingService) DeleteBuilding(ctx context.Context, id string) error {
	delete(m.Buildings, id)
	return nil
}

func (m *MockBuildingService) ListBuildings(ctx context.Context, limit, offset int) ([]*bim.Building, error) {
	var buildings []*bim.Building
	for _, b := range m.Buildings {
		buildings = append(buildings, b)
	}
	return buildings, nil
}

func (m *MockBuildingService) AddRoom(ctx context.Context, buildingID string, room *bim.Room) error {
	return errors.New("not implemented")
}

func (m *MockBuildingService) AddEquipment(ctx context.Context, buildingID string, equipment *bim.Equipment) error {
	return errors.New("not implemented")
}

// MockUserService is a mock implementation of UserService
type MockUserService struct {
	Users map[string]*api.User
}

func NewMockUserService() *MockUserService {
	return &MockUserService{
		Users: make(map[string]*api.User),
	}
}

func (m *MockUserService) CreateUser(ctx context.Context, req api.CreateUserRequest) (*api.User, error) {
	user := &api.User{
		ID:    "user-" + req.Email,
		Email: req.Email,
		Name:  req.Name,
		Role:  req.Role,
		OrgID: req.OrgID,
	}
	m.Users[user.ID] = user
	return user, nil
}

func (m *MockUserService) GetUser(ctx context.Context, id string) (*api.User, error) {
	if u, ok := m.Users[id]; ok {
		return u, nil
	}
	return nil, errors.New("user not found")
}

func (m *MockUserService) UpdateUser(ctx context.Context, userID string, updates api.UserUpdate) (*api.User, error) {
	if u, ok := m.Users[userID]; ok {
		// Apply updates
		if updates.Name != nil {
			u.Name = *updates.Name
		}
		if updates.Email != nil {
			u.Email = *updates.Email
		}
		if updates.Role != nil {
			u.Role = *updates.Role
		}
		return u, nil
	}
	return nil, errors.New("user not found")
}

func (m *MockUserService) DeleteUser(ctx context.Context, id string) error {
	delete(m.Users, id)
	return nil
}

func (m *MockUserService) ListUsers(ctx context.Context, filter api.UserFilter) ([]*api.User, error) {
	var users []*api.User
	for _, u := range m.Users {
		users = append(users, u)
	}
	return users, nil
}

func (m *MockUserService) GetUserByEmail(ctx context.Context, email string) (*api.User, error) {
	for _, u := range m.Users {
		if u.Email == email {
			return u, nil
		}
	}
	return nil, errors.New("user not found")
}

func (m *MockUserService) GetUserPermissions(ctx context.Context, userID string) ([]string, error) {
	if u, ok := m.Users[userID]; ok {
		return u.Permissions, nil
	}
	return nil, errors.New("user not found")
}

func (m *MockUserService) UpdateUserActivity(ctx context.Context, userID string) error {
	if _, ok := m.Users[userID]; ok {
		return nil
	}
	return errors.New("user not found")
}

// MockOrganizationService is a mock implementation of OrganizationService
type MockOrganizationService struct {
	Organizations map[string]*models.Organization
}

func NewMockOrganizationService() *MockOrganizationService {
	return &MockOrganizationService{
		Organizations: make(map[string]*models.Organization),
	}
}

func (m *MockOrganizationService) CreateOrganization(ctx context.Context, org *models.Organization) error {
	m.Organizations[org.ID] = org
	return nil
}

func (m *MockOrganizationService) GetOrganization(ctx context.Context, id string) (*models.Organization, error) {
	if o, ok := m.Organizations[id]; ok {
		return o, nil
	}
	return nil, errors.New("organization not found")
}

func (m *MockOrganizationService) UpdateOrganization(ctx context.Context, org *models.Organization) error {
	m.Organizations[org.ID] = org
	return nil
}

func (m *MockOrganizationService) DeleteOrganization(ctx context.Context, id string) error {
	delete(m.Organizations, id)
	return nil
}

func (m *MockOrganizationService) ListOrganizations(ctx context.Context, limit, offset int) ([]*models.Organization, error) {
	var orgs []*models.Organization
	for _, o := range m.Organizations {
		orgs = append(orgs, o)
	}
	return orgs, nil
}

func (m *MockOrganizationService) AddMember(ctx context.Context, orgID, userID, role string) error {
	return nil
}

func (m *MockOrganizationService) RemoveMember(ctx context.Context, orgID, userID string) error {
	return nil
}

func (m *MockOrganizationService) UpdateMemberRole(ctx context.Context, orgID, userID, role string) error {
	return nil
}

func (m *MockOrganizationService) GetMembers(ctx context.Context, orgID string) ([]*models.OrganizationMember, error) {
	return []*models.OrganizationMember{}, nil
}