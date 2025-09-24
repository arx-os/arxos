package services_test

import (
	"context"
	"errors"
	"time"

	"github.com/arx-os/arxos/internal/api"
	"github.com/arx-os/arxos/internal/bim"
	"github.com/arx-os/arxos/internal/interfaces"
	"github.com/arx-os/arxos/pkg/models"
)

// MockAuthService is a mock implementation of AuthService
type MockAuthService struct {
	Users      map[string]*models.User
	Sessions   map[string]*models.UserSession
	EnableAuth bool
}

func NewMockAuthService() *MockAuthService {
	return &MockAuthService{
		Users:      make(map[string]*models.User),
		Sessions:   make(map[string]*models.UserSession),
		EnableAuth: false,
	}
}

func (m *MockAuthService) Login(ctx context.Context, email, password string) (interface{}, error) {
	// Simple mock implementation
	if email == "test@example.com" && password == "TestPass123!" {
		return map[string]interface{}{
			"access_token":  "test-token",
			"refresh_token": "test-refresh-token",
			"token_type":    "Bearer",
			"expires_in":    3600,
		}, nil
	}
	return nil, errors.New("invalid credentials")
}

func (m *MockAuthService) Register(ctx context.Context, email, password, name string) (interface{}, error) {
	// Simple mock implementation
	return map[string]interface{}{
		"id":    "new-user-id",
		"email": email,
		"name":  name,
	}, nil
}

func (m *MockAuthService) RefreshToken(ctx context.Context, refreshToken string) (string, string, error) {
	if refreshToken == "test-refresh-token" {
		return "new-test-token", "new-refresh-token", nil
	}
	return "", "", errors.New("invalid refresh token")
}

func (m *MockAuthService) Logout(ctx context.Context, token string) error {
	delete(m.Sessions, token)
	return nil
}

func (m *MockAuthService) ValidateToken(ctx context.Context, token string) (*interfaces.TokenClaims, error) {
	if !m.EnableAuth {
		// Auth disabled, return default user ID
		return &interfaces.TokenClaims{
			UserID: "test-user",
			Email:  "test@example.com",
			Role:   "user",
		}, nil
	}

	if token == "test-token" || token == "new-test-token" {
		return &interfaces.TokenClaims{
			UserID: "test-user",
			Email:  "test@example.com",
			Role:   "user",
		}, nil
	}
	return nil, errors.New("invalid token")
}

func (m *MockAuthService) ChangePassword(ctx context.Context, userID, oldPassword, newPassword string) error {
	// Mock implementation for testing
	return nil
}

func (m *MockAuthService) ConfirmPasswordReset(ctx context.Context, token, newPassword string) error {
	// Mock implementation for testing
	return nil
}

func (m *MockAuthService) ResetPassword(ctx context.Context, email string) error {
	// Mock implementation for testing
	return nil
}

func (m *MockAuthService) RevokeToken(ctx context.Context, token string) error {
	delete(m.Sessions, token)
	return nil
}

func (m *MockAuthService) GenerateToken(ctx context.Context, userID, email, role, orgID string) (string, error) {
	// Mock implementation for testing
	return "mock-token", nil
}

func (m *MockAuthService) DeleteSession(ctx context.Context, userID, sessionID string) error {
	delete(m.Sessions, sessionID)
	return nil
}

func (m *MockAuthService) ValidateTokenClaims(ctx context.Context, token string) (*api.TokenClaims, error) {
	// Mock implementation for testing
	return &api.TokenClaims{
		UserID: "test-user",
		Email:  "test@example.com",
		Role:   "user",
	}, nil
}

// MockBuildingService is a mock implementation of BuildingService
type MockBuildingService struct {
	Buildings map[string]*models.FloorPlan
}

func NewMockBuildingService() *MockBuildingService {
	return &MockBuildingService{
		Buildings: make(map[string]*models.FloorPlan),
	}
}

func (m *MockBuildingService) CreateBuilding(ctx context.Context, name string) (interface{}, error) {
	// Create a mock building response
	building := map[string]interface{}{
		"id":   "mock-building-id",
		"name": name,
	}
	return building, nil
}

func (m *MockBuildingService) GetBuilding(ctx context.Context, id string) (interface{}, error) {
	if b, ok := m.Buildings[id]; ok {
		return b, nil
	}
	return nil, errors.New("building not found")
}

func (m *MockBuildingService) GetBuildings(ctx context.Context) ([]interface{}, error) {
	var buildings []interface{}
	for _, b := range m.Buildings {
		buildings = append(buildings, b)
	}
	return buildings, nil
}

func (m *MockBuildingService) UpdateBuilding(ctx context.Context, id, name string) (interface{}, error) {
	// Mock implementation for testing
	return map[string]interface{}{
		"id":   id,
		"name": name,
	}, nil
}

func (m *MockBuildingService) DeleteBuilding(ctx context.Context, id string) error {
	delete(m.Buildings, id)
	return nil
}

func (m *MockBuildingService) CreateEquipment(ctx context.Context, equipment *models.Equipment) error {
	// Mock implementation for testing
	return nil
}

func (m *MockBuildingService) CreateRoom(ctx context.Context, room *models.Room) error {
	// Mock implementation for testing
	return nil
}

func (m *MockBuildingService) DeleteEquipment(ctx context.Context, id string) error {
	// Mock implementation for testing
	return nil
}

func (m *MockBuildingService) ListBuildings(ctx context.Context, orgID string, page, limit int) ([]interface{}, error) {
	var buildings []interface{}
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

func (m *MockBuildingService) DeleteRoom(ctx context.Context, id string) error {
	// Mock implementation for testing
	return nil
}

func (m *MockBuildingService) GetEquipment(ctx context.Context, id string) (*models.Equipment, error) {
	// Mock implementation for testing
	return nil, nil
}

func (m *MockBuildingService) GetRoom(ctx context.Context, id string) (*models.Room, error) {
	// Mock implementation for testing
	return nil, nil
}

func (m *MockBuildingService) ListEquipment(ctx context.Context, buildingID string, filters map[string]interface{}) ([]interface{}, error) {
	// Mock implementation for testing
	return []interface{}{}, nil
}

func (m *MockBuildingService) ListRooms(ctx context.Context, buildingID string) ([]interface{}, error) {
	// Mock implementation for testing
	return []interface{}{}, nil
}

func (m *MockBuildingService) UpdateEquipment(ctx context.Context, equipment *models.Equipment) error {
	// Mock implementation for testing
	return nil
}

func (m *MockBuildingService) UpdateRoom(ctx context.Context, room *models.Room) error {
	// Mock implementation for testing
	return nil
}

func (m *MockBuildingService) GetConnectionGraph(ctx context.Context, buildingID string) (interface{}, error) {
	// Mock implementation for testing
	return map[string]interface{}{
		"building_id": buildingID,
		"connections": []interface{}{},
	}, nil
}

func (m *MockBuildingService) CreateConnection(ctx context.Context, fromID, toID, connType string) (interface{}, error) {
	// Mock implementation for testing
	return map[string]interface{}{
		"id":         "mock-connection-id",
		"from_id":    fromID,
		"to_id":      toID,
		"type":       connType,
		"created_at": "2023-01-01T00:00:00Z",
	}, nil
}

func (m *MockBuildingService) DeleteConnection(ctx context.Context, connectionID string) error {
	// Mock implementation for testing
	return nil
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

func (m *MockUserService) CreateUser(ctx context.Context, email, password, name string) (interface{}, error) {
	user := &api.User{
		ID:    "user-" + email,
		Email: email,
		Name:  name,
		Role:  "user",
	}
	m.Users[user.ID] = user
	return user, nil
}

func (m *MockUserService) GetUser(ctx context.Context, id string) (interface{}, error) {
	if u, ok := m.Users[id]; ok {
		return u, nil
	}
	return nil, errors.New("user not found")
}

func (m *MockUserService) UpdateUser(ctx context.Context, id string, updates map[string]interface{}) (interface{}, error) {
	if u, ok := m.Users[id]; ok {
		// Apply updates
		if name, ok := updates["name"].(string); ok {
			u.Name = name
		}
		if email, ok := updates["email"].(string); ok {
			u.Email = email
		}
		if role, ok := updates["role"].(string); ok {
			u.Role = role
		}
		return u, nil
	}
	return nil, errors.New("user not found")
}

func (m *MockUserService) DeleteUser(ctx context.Context, id string) error {
	delete(m.Users, id)
	return nil
}

func (m *MockUserService) ListUsers(ctx context.Context, filter interface{}) ([]interface{}, error) {
	var users []interface{}
	for _, u := range m.Users {
		users = append(users, u)
	}
	return users, nil
}

func (m *MockUserService) GetUserByEmail(ctx context.Context, email string) (interface{}, error) {
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

func (m *MockUserService) ChangePassword(ctx context.Context, userID, oldPassword, newPassword string) error {
	// Mock implementation for testing
	return nil
}

func (m *MockUserService) ConfirmPasswordReset(ctx context.Context, token, newPassword string) error {
	// Mock implementation for testing
	return nil
}

func (m *MockUserService) RequestPasswordReset(ctx context.Context, email string) error {
	// Mock implementation for testing
	return nil
}

func (m *MockUserService) DeleteSession(ctx context.Context, userID, sessionID string) error {
	// Mock implementation for testing
	return nil
}

func (m *MockUserService) GetUserOrganizations(ctx context.Context, userID string) ([]interface{}, error) {
	// Mock implementation for testing
	return []interface{}{}, nil
}

func (m *MockUserService) GetUserSessions(ctx context.Context, userID string) ([]interface{}, error) {
	// Mock implementation for testing
	return []interface{}{}, nil
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

func (m *MockOrganizationService) CreateOrganization(ctx context.Context, name, description, userID string) (interface{}, error) {
	// Mock implementation for testing
	org := map[string]interface{}{
		"id":          "mock-org-id",
		"name":        name,
		"description": description,
		"owner_id":    userID,
	}
	return org, nil
}

func (m *MockOrganizationService) GetOrganization(ctx context.Context, id string) (interface{}, error) {
	if o, ok := m.Organizations[id]; ok {
		return o, nil
	}
	return nil, errors.New("organization not found")
}

func (m *MockOrganizationService) GetOrganizationBySlug(ctx context.Context, slug string) (*models.Organization, error) {
	// Mock implementation for testing
	return nil, errors.New("organization not found")
}

func (m *MockOrganizationService) UpdateOrganization(ctx context.Context, id string, updates map[string]interface{}) (interface{}, error) {
	// Mock implementation for testing
	return map[string]interface{}{
		"id":   id,
		"name": updates["name"],
	}, nil
}

func (m *MockOrganizationService) DeleteOrganization(ctx context.Context, id string) error {
	delete(m.Organizations, id)
	return nil
}

func (m *MockOrganizationService) ListOrganizations(ctx context.Context, userID string) ([]interface{}, error) {
	var orgs []interface{}
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

func (m *MockOrganizationService) GetMembers(ctx context.Context, orgID string) ([]interface{}, error) {
	return []interface{}{}, nil
}

func (m *MockOrganizationService) GetMemberRole(ctx context.Context, orgID, userID string) (string, error) {
	// Mock implementation for testing
	return "member", nil
}

func (m *MockOrganizationService) AcceptInvitation(ctx context.Context, token string) error {
	// Mock implementation for testing
	return nil
}

func (m *MockOrganizationService) ListPendingInvitations(ctx context.Context, orgID string) ([]interface{}, error) {
	// Mock implementation for testing
	return []interface{}{}, nil
}

func (m *MockOrganizationService) RevokeInvitation(ctx context.Context, orgID, invitationID string) error {
	// Mock implementation for testing
	return nil
}

func (m *MockOrganizationService) CanUserAccessOrganization(ctx context.Context, userID, orgID string) (bool, error) {
	// Mock implementation for testing
	return true, nil
}

func (m *MockOrganizationService) GetUserPermissions(ctx context.Context, orgID, userID string) ([]models.Permission, error) {
	// Mock implementation for testing
	return []models.Permission{}, nil
}

func (m *MockOrganizationService) HasPermission(ctx context.Context, orgID, userID string, permission models.Permission) (bool, error) {
	// Mock implementation for testing
	return true, nil
}

func (m *MockOrganizationService) CreateInvitation(ctx context.Context, orgID, email, role string) (interface{}, error) {
	// Mock implementation for testing
	return map[string]interface{}{
		"id":              "test-invitation",
		"organization_id": orgID,
		"email":           email,
		"role":            role,
		"token":           "test-token",
		"expires_at":      time.Now().Add(24 * time.Hour),
		"created_at":      time.Now(),
	}, nil
}

// MockEquipmentService is a mock implementation of EquipmentService
type MockEquipmentService struct {
	Equipment map[string]*models.Equipment
}

func NewMockEquipmentService() *MockEquipmentService {
	return &MockEquipmentService{
		Equipment: make(map[string]*models.Equipment),
	}
}

func (m *MockEquipmentService) CreateEquipment(ctx context.Context, equipment *models.Equipment) error {
	m.Equipment[equipment.ID] = equipment
	return nil
}

func (m *MockEquipmentService) GetEquipment(ctx context.Context, id string) (*models.Equipment, error) {
	if e, ok := m.Equipment[id]; ok {
		return e, nil
	}
	return nil, errors.New("equipment not found")
}

func (m *MockEquipmentService) UpdateEquipment(ctx context.Context, equipment *models.Equipment) error {
	m.Equipment[equipment.ID] = equipment
	return nil
}

func (m *MockEquipmentService) DeleteEquipment(ctx context.Context, id string) error {
	delete(m.Equipment, id)
	return nil
}

func (m *MockEquipmentService) ListEquipment(ctx context.Context, buildingID string) ([]*models.Equipment, error) {
	var equipment []*models.Equipment
	for _, e := range m.Equipment {
		// Since Equipment doesn't have BuildingID, we'll return all equipment for now
		// In a real implementation, you'd need to track the relationship
		equipment = append(equipment, e)
	}
	return equipment, nil
}
