package web

import (
	"context"
	"database/sql"
	"encoding/json"
	"errors"
	"fmt"
	"net/http"
	"net/http/httptest"
	"net/url"
	"strings"
	"testing"
	"time"

	apimodels "github.com/arx-os/arxos/internal/api/models"
	"github.com/arx-os/arxos/internal/api/types"
	"github.com/arx-os/arxos/internal/database"
	"github.com/arx-os/arxos/pkg/models"
	syncpkg "github.com/arx-os/arxos/pkg/sync"
	"github.com/go-chi/chi/v5"
)

// MockDB implements database.DB for testing
type MockDB struct {
	users      map[string]*models.User
	buildings  map[string]*models.Building
	equipment  map[string]*models.Equipment
	sessions   map[string]*models.UserSession
	shouldFail bool
}

func NewMockDB() *MockDB {
	return &MockDB{
		users:     make(map[string]*models.User),
		buildings: make(map[string]*models.Building),
		equipment: make(map[string]*models.Equipment),
		sessions:  make(map[string]*models.UserSession),
	}
}

func (m *MockDB) GetUser(ctx context.Context, id string) (*models.User, error) {
	if m.shouldFail {
		return nil, database.ErrNotFound
	}
	user, ok := m.users[id]
	if !ok {
		return nil, database.ErrNotFound
	}
	return user, nil
}

func (m *MockDB) GetUserByEmail(ctx context.Context, email string) (*models.User, error) {
	if m.shouldFail {
		return nil, database.ErrNotFound
	}
	for _, user := range m.users {
		if user.Email == email {
			return user, nil
		}
	}
	return nil, database.ErrNotFound
}

func (m *MockDB) CreateUser(ctx context.Context, user *models.User) error {
	if m.shouldFail {
		return fmt.Errorf("internal error")
	}
	m.users[user.ID] = user
	return nil
}

func (m *MockDB) UpdateUser(ctx context.Context, user *models.User) error {
	if m.shouldFail {
		return fmt.Errorf("internal error")
	}
	m.users[user.ID] = user
	return nil
}

func (m *MockDB) DeleteUser(ctx context.Context, id string) error {
	if m.shouldFail {
		return fmt.Errorf("internal error")
	}
	delete(m.users, id)
	return nil
}

func (m *MockDB) CreateSession(ctx context.Context, session *models.UserSession) error {
	if m.shouldFail {
		return fmt.Errorf("internal error")
	}
	m.sessions[session.Token] = session
	return nil
}

func (m *MockDB) GetSession(ctx context.Context, token string) (*models.UserSession, error) {
	if m.shouldFail {
		return nil, database.ErrNotFound
	}
	session, ok := m.sessions[token]
	if !ok {
		return nil, database.ErrNotFound
	}
	return session, nil
}

func (m *MockDB) DeleteSession(ctx context.Context, id string) error {
	for token, session := range m.sessions {
		if session.ID == id {
			delete(m.sessions, token)
			break
		}
	}
	return nil
}

func (m *MockDB) GetBuilding(ctx context.Context, id string) (*models.Building, error) {
	if m.shouldFail {
		return nil, database.ErrNotFound
	}
	building, ok := m.buildings[id]
	if !ok {
		return nil, database.ErrNotFound
	}
	return building, nil
}

func (m *MockDB) ListBuildings(ctx context.Context, opts interface{}) ([]*models.Building, error) {
	if m.shouldFail {
		return nil, fmt.Errorf("internal error")
	}
	var buildings []*models.Building
	for _, b := range m.buildings {
		buildings = append(buildings, b)
	}
	return buildings, nil
}

// ListFloorPlans implements the database interface
func (m *MockDB) ListFloorPlans(ctx context.Context) ([]*models.FloorPlan, error) {
	if m.shouldFail {
		return nil, fmt.Errorf("internal error")
	}
	return []*models.FloorPlan{}, nil
}

func (m *MockDB) CreateBuilding(ctx context.Context, building *models.Building) error {
	if m.shouldFail {
		return fmt.Errorf("internal error")
	}
	m.buildings[building.ID] = building
	return nil
}

func (m *MockDB) UpdateBuilding(ctx context.Context, building *models.Building) error {
	if m.shouldFail {
		return fmt.Errorf("internal error")
	}
	m.buildings[building.ID] = building
	return nil
}

func (m *MockDB) DeleteBuilding(ctx context.Context, id string) error {
	if m.shouldFail {
		return fmt.Errorf("internal error")
	}
	delete(m.buildings, id)
	return nil
}

func (m *MockDB) GetEquipment(ctx context.Context, id string) (*models.Equipment, error) {
	if m.shouldFail {
		return nil, database.ErrNotFound
	}
	equipment, ok := m.equipment[id]
	if !ok {
		return nil, database.ErrNotFound
	}
	return equipment, nil
}

func (m *MockDB) Query(ctx context.Context, query string, args ...interface{}) (*sql.Rows, error) {
	return nil, nil
}

func (m *MockDB) Exec(ctx context.Context, query string, args ...interface{}) (sql.Result, error) {
	return nil, nil
}

func (m *MockDB) Close() error {
	return nil
}

func (m *MockDB) AcceptOrganizationInvitation(ctx context.Context, token, userID string) error {
	// Mock implementation for testing
	return nil
}

func (m *MockDB) AddOrganizationMember(ctx context.Context, orgID, userID, role string) error {
	// Mock implementation for testing
	return nil
}

func (m *MockDB) ApplyChange(ctx context.Context, change *syncpkg.Change) error {
	// Mock implementation for testing
	return nil
}

func (m *MockDB) BeginTx(ctx context.Context) (*sql.Tx, error) {
	// Mock implementation for testing
	return nil, nil
}

func (m *MockDB) Connect(ctx context.Context, dsn string) error {
	// Mock implementation for testing
	return nil
}

func (m *MockDB) CreateOrganization(ctx context.Context, org *models.Organization) error {
	// Mock implementation for testing
	return nil
}

func (m *MockDB) CreateOrganizationInvitation(ctx context.Context, invitation *models.OrganizationInvitation) error {
	// Mock implementation for testing
	return nil
}

func (m *MockDB) CreatePasswordResetToken(ctx context.Context, token *models.PasswordResetToken) error {
	// Mock implementation for testing
	return nil
}

func (m *MockDB) DeleteEquipment(ctx context.Context, id string) error {
	// Mock implementation for testing
	return nil
}

func (m *MockDB) DeleteExpiredPasswordResetTokens(ctx context.Context) error {
	// Mock implementation for testing
	return nil
}

func (m *MockDB) DeleteFloorPlan(ctx context.Context, id string) error {
	// Mock implementation for testing
	return nil
}

func (m *MockDB) DeleteOrganization(ctx context.Context, id string) error {
	// Mock implementation for testing
	return nil
}

func (m *MockDB) DeleteRoom(ctx context.Context, id string) error {
	// Mock implementation for testing
	return nil
}

func (m *MockDB) GetAllFloorPlans(ctx context.Context) ([]*models.FloorPlan, error) {
	// Mock implementation for testing
	return []*models.FloorPlan{}, nil
}

func (m *MockDB) GetChangesSince(ctx context.Context, since time.Time, entityType string) ([]*syncpkg.Change, error) {
	// Mock implementation for testing
	return []*syncpkg.Change{}, nil
}

func (m *MockDB) GetConflictCount(ctx context.Context, buildingID string) (int, error) {
	// Mock implementation for testing
	return 0, nil
}

func (m *MockDB) GetEntityVersion(ctx context.Context, entityType, entityID string) (int, error) {
	// Mock implementation for testing
	return 1, nil
}

func (m *MockDB) GetEquipmentByFloorPlan(ctx context.Context, floorPlanID string) ([]*models.Equipment, error) {
	// Mock implementation for testing
	return []*models.Equipment{}, nil
}

func (m *MockDB) GetFloorPlan(ctx context.Context, id string) (*models.FloorPlan, error) {
	// Mock implementation for testing
	return nil, nil
}

func (m *MockDB) GetLastSyncTime(ctx context.Context, buildingID string) (time.Time, error) {
	// Mock implementation for testing
	return time.Now(), nil
}

func (m *MockDB) GetOrganization(ctx context.Context, id string) (*models.Organization, error) {
	// Mock implementation for testing
	return nil, nil
}

func (m *MockDB) GetOrganizationInvitation(ctx context.Context, token string) (*models.OrganizationInvitation, error) {
	// Mock implementation for testing
	return nil, nil
}

func (m *MockDB) GetOrganizationInvitationByToken(ctx context.Context, token string) (*models.OrganizationInvitation, error) {
	// Mock implementation for testing
	return nil, nil
}

func (m *MockDB) GetOrganizationMember(ctx context.Context, orgID, userID string) (*models.OrganizationMember, error) {
	// Mock implementation for testing
	return nil, nil
}

func (m *MockDB) GetOrganizationMembers(ctx context.Context, orgID string) ([]*models.OrganizationMember, error) {
	// Mock implementation for testing
	return []*models.OrganizationMember{}, nil
}

func (m *MockDB) GetOrganizationsByUser(ctx context.Context, userID string) ([]*models.Organization, error) {
	// Mock implementation for testing
	return []*models.Organization{}, nil
}

func (m *MockDB) GetPasswordResetToken(ctx context.Context, token string) (*models.PasswordResetToken, error) {
	// Mock implementation for testing
	return nil, nil
}

func (m *MockDB) GetPendingChangesCount(ctx context.Context, buildingID string) (int, error) {
	// Mock implementation for testing
	return 0, nil
}

func (m *MockDB) GetPendingConflicts(ctx context.Context, buildingID string) ([]*syncpkg.Conflict, error) {
	// Mock implementation for testing
	return []*syncpkg.Conflict{}, nil
}

func (m *MockDB) GetRoom(ctx context.Context, id string) (*models.Room, error) {
	// Mock implementation for testing
	return nil, nil
}

func (m *MockDB) GetRoomsByFloorPlan(ctx context.Context, floorPlanID string) ([]*models.Room, error) {
	// Mock implementation for testing
	return []*models.Room{}, nil
}

func (m *MockDB) GetSessionByRefreshToken(ctx context.Context, refreshToken string) (*models.UserSession, error) {
	// Mock implementation for testing
	return nil, nil
}

func (m *MockDB) GetSpatialDB() (database.SpatialDB, error) {
	// Mock implementation for testing
	return nil, nil
}

func (m *MockDB) GetVersion(ctx context.Context) (int, error) {
	// Mock implementation for testing
	return 1, nil
}

func (m *MockDB) HasSpatialSupport() bool {
	// Mock implementation for testing
	return true
}

func (m *MockDB) ListOrganizationInvitations(ctx context.Context, orgID string) ([]*models.OrganizationInvitation, error) {
	// Mock implementation for testing
	return []*models.OrganizationInvitation{}, nil
}

func (m *MockDB) ListUsers(ctx context.Context, limit, offset int) ([]*models.User, error) {
	// Mock implementation for testing
	return []*models.User{}, nil
}

func (m *MockDB) MarkPasswordResetTokenUsed(ctx context.Context, token string) error {
	// Mock implementation for testing
	return nil
}

func (m *MockDB) Migrate(ctx context.Context) error {
	// Mock implementation for testing
	return nil
}

func (m *MockDB) QueryRow(ctx context.Context, query string, args ...interface{}) *sql.Row {
	// Mock implementation for testing
	return nil
}

func (m *MockDB) RemoveOrganizationMember(ctx context.Context, orgID, userID string) error {
	// Mock implementation for testing
	return nil
}

func (m *MockDB) ResolveConflict(ctx context.Context, conflictID string, resolution string) error {
	// Mock implementation for testing
	return nil
}

func (m *MockDB) RevokeOrganizationInvitation(ctx context.Context, invitationID string) error {
	// Mock implementation for testing
	return nil
}

func (m *MockDB) SaveConflict(ctx context.Context, conflict *syncpkg.Conflict) error {
	// Mock implementation for testing
	return nil
}

func (m *MockDB) SaveEquipment(ctx context.Context, equipment *models.Equipment) error {
	// Mock implementation for testing
	return nil
}

func (m *MockDB) SaveFloorPlan(ctx context.Context, floorPlan *models.FloorPlan) error {
	// Mock implementation for testing
	return nil
}

func (m *MockDB) SaveRoom(ctx context.Context, room *models.Room) error {
	// Mock implementation for testing
	return nil
}

func (m *MockDB) UpdateEquipment(ctx context.Context, equipment *models.Equipment) error {
	// Mock implementation for testing
	return nil
}

func (m *MockDB) UpdateFloorPlan(ctx context.Context, floorPlan *models.FloorPlan) error {
	// Mock implementation for testing
	return nil
}

func (m *MockDB) UpdateLastSyncTime(ctx context.Context, buildingID string, syncTime time.Time) error {
	// Mock implementation for testing
	return nil
}

func (m *MockDB) UpdateOrganization(ctx context.Context, org *models.Organization) error {
	// Mock implementation for testing
	return nil
}

func (m *MockDB) UpdateOrganizationMemberRole(ctx context.Context, orgID, userID, newRole string) error {
	// Mock implementation for testing
	return nil
}

func (m *MockDB) UpdateRoom(ctx context.Context, room *models.Room) error {
	// Mock implementation for testing
	return nil
}

func (m *MockDB) UpdateSession(ctx context.Context, session *models.UserSession) error {
	// Mock implementation for testing
	return nil
}

// Mock implementations of other required methods...
func (m *MockDB) CreateUserWithPassword(ctx context.Context, user *models.User, password string) error {
	return m.CreateUser(ctx, user)
}

// MockAuthService is a mock implementation of api.AuthService
type MockAuthService struct {
	EnableAuth bool
}

func (m *MockAuthService) Login(ctx context.Context, email, password string) (*apimodels.AuthResponse, error) {
	// Mock implementation for testing
	return &apimodels.AuthResponse{
		AccessToken: "test-token",
		TokenType:   "Bearer",
		ExpiresIn:   3600,
	}, nil
}

func (m *MockAuthService) Logout(ctx context.Context, token string) error {
	// Mock implementation for testing
	return nil
}

func (m *MockAuthService) RefreshToken(ctx context.Context, refreshToken string) (*apimodels.AuthResponse, error) {
	// Mock implementation for testing
	return &apimodels.AuthResponse{
		AccessToken: "new-test-token",
		TokenType:   "Bearer",
		ExpiresIn:   3600,
	}, nil
}

func (m *MockAuthService) ValidateToken(ctx context.Context, token string) (string, error) {
	if !m.EnableAuth {
		// Auth disabled, return default user ID
		return "test-user", nil
	}

	if token == "test-token" || token == "new-test-token" {
		return "test-user", nil
	}
	return "", errors.New("invalid token")
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

func (m *MockAuthService) Register(ctx context.Context, email, password, fullName string) (*apimodels.User, error) {
	// Mock implementation for testing
	return &apimodels.User{
		ID:     "test-user",
		Email:  email,
		Name:   fullName,
		Active: true,
	}, nil
}

func (m *MockAuthService) RevokeToken(ctx context.Context, token string) error {
	// Mock implementation for testing
	return nil
}

func (m *MockAuthService) ValidateTokenClaims(ctx context.Context, token string) (*apimodels.TokenClaims, error) {
	// Mock implementation for testing
	return &apimodels.TokenClaims{
		UserID: "test-user",
		Email:  "test@example.com",
		Role:   "user",
	}, nil
}

// Additional methods to implement types.UserService interface
func (m *MockAuthService) GetUser(ctx context.Context, id string) (interface{}, error) {
	return map[string]interface{}{
		"id":    id,
		"email": "test@example.com",
		"name":  "Test User",
	}, nil
}

func (m *MockAuthService) CreateUser(ctx context.Context, email, password, name string) (interface{}, error) {
	return map[string]interface{}{
		"id":    "test-user",
		"email": email,
		"name":  name,
	}, nil
}

func (m *MockAuthService) UpdateUser(ctx context.Context, id string, updates map[string]interface{}) (interface{}, error) {
	return map[string]interface{}{
		"id":    id,
		"email": "test@example.com",
		"name":  "Updated User",
	}, nil
}

func (m *MockAuthService) ListUsers(ctx context.Context, filter interface{}) ([]interface{}, error) {
	return []interface{}{}, nil
}

func (m *MockAuthService) GetUserByEmail(ctx context.Context, email string) (interface{}, error) {
	return map[string]interface{}{
		"id":    "test-user",
		"email": email,
		"name":  "Test User",
	}, nil
}

func (m *MockAuthService) GetUserOrganizations(ctx context.Context, userID string) ([]interface{}, error) {
	return []interface{}{}, nil
}

func (m *MockAuthService) GetUserSessions(ctx context.Context, userID string) ([]interface{}, error) {
	return []interface{}{}, nil
}

func (m *MockAuthService) DeleteSession(ctx context.Context, userID, sessionID string) error {
	return nil
}

func (m *MockAuthService) GenerateToken(ctx context.Context, userID, email, role, orgID string) (string, error) {
	return "test-token", nil
}

func (m *MockAuthService) DeleteUser(ctx context.Context, userID string) error {
	return nil
}

func (m *MockAuthService) RequestPasswordReset(ctx context.Context, email string) error {
	return nil
}

func (m *MockDB) UpdateUserLoginInfo(ctx context.Context, userID string, success bool) error {
	return nil
}

func (m *MockDB) GetUserSessions(ctx context.Context, userID string) ([]*models.UserSession, error) {
	var sessions []*models.UserSession
	for _, s := range m.sessions {
		if s.UserID == userID {
			sessions = append(sessions, s)
		}
	}
	return sessions, nil
}

func (m *MockDB) DeleteUserSessions(ctx context.Context, userID string) error {
	for token, session := range m.sessions {
		if session.UserID == userID {
			delete(m.sessions, token)
		}
	}
	return nil
}

func (m *MockDB) DeleteExpiredSessions(ctx context.Context) error {
	return nil
}

// setupTestHandler creates a handler with mock services for testing
func setupTestHandler() (*Handler, *MockDB) {
	mockDB := NewMockDB()

	// Create mock services
	// Create mock auth service
	mockAuthService2 := &MockAuthService{EnableAuth: false}

	services := &types.Services{
		DB:   mockDB,
		User: mockAuthService2, // Use the mock directly since it implements the interface
	}

	// Create handler
	handler, _ := NewHandler(services)

	return handler, mockDB
}

// TestDashboardHandler tests the dashboard handler
func TestDashboardHandler(t *testing.T) {
	handler, mockDB := setupTestHandler()

	// Add test data
	mockDB.buildings["b1"] = &models.Building{
		ID:   "b1",
		Name: "Test Building 1",
	}
	mockDB.buildings["b2"] = &models.Building{
		ID:   "b2",
		Name: "Test Building 2",
	}

	req := httptest.NewRequest("GET", "/dashboard", nil)
	w := httptest.NewRecorder()

	handler.HandleDashboard(w, req)

	resp := w.Result()
	if resp.StatusCode != http.StatusOK {
		t.Errorf("Expected status 200, got %d", resp.StatusCode)
	}

	// Check content type
	contentType := resp.Header.Get("Content-Type")
	if !strings.Contains(contentType, "text/html") {
		t.Errorf("Expected HTML content type, got %s", contentType)
	}
}

// TestBuildingsHandler tests the buildings list handler
func TestBuildingsHandler(t *testing.T) {
	handler, mockDB := setupTestHandler()

	// Add test buildings
	for i := 0; i < 5; i++ {
		mockDB.buildings[string(rune('a'+i))] = &models.Building{
			ID:          string(rune('a' + i)),
			Name:        "Building " + string(rune('A'+i)),
			Address:     "123 Test St, Test City, TS 12345, Test Country",
			Description: "Test office building",
			CreatedAt:   time.Now(),
			UpdatedAt:   time.Now(),
		}
	}

	req := httptest.NewRequest("GET", "/buildings", nil)
	w := httptest.NewRecorder()

	handler.HandleBuildingsList(w, req)

	resp := w.Result()
	if resp.StatusCode != http.StatusOK {
		t.Errorf("Expected status 200, got %d", resp.StatusCode)
	}

	body := w.Body.String()
	// Check that buildings are in the response
	if !strings.Contains(body, "Building A") {
		t.Error("Expected building names in response")
	}
}

// TestBuildingDetailHandler tests the building detail handler
func TestBuildingDetailHandler(t *testing.T) {
	handler, mockDB := setupTestHandler()

	// Add test building
	mockDB.buildings["test-id"] = &models.Building{
		ID:          "test-id",
		Name:        "Test Building",
		Address:     "456 Main St, Test City, TS 12345, USA",
		Description: "Commercial building with 5 floors",
	}

	// Create router for path params
	r := chi.NewRouter()
	r.Get("/buildings/{id}", handler.handleBuildingDetail)

	req := httptest.NewRequest("GET", "/buildings/test-id", nil)
	w := httptest.NewRecorder()

	r.ServeHTTP(w, req)

	resp := w.Result()
	if resp.StatusCode != http.StatusOK {
		t.Errorf("Expected status 200, got %d", resp.StatusCode)
	}

	body := w.Body.String()
	if !strings.Contains(body, "Test Building") {
		t.Error("Expected building name in response")
	}
}

// TestLoginHandler tests the login page handler
func TestLoginHandler(t *testing.T) {
	handler, _ := setupTestHandler()

	req := httptest.NewRequest("GET", "/login", nil)
	w := httptest.NewRecorder()

	handler.handleLogin(w, req)

	resp := w.Result()
	if resp.StatusCode != http.StatusOK {
		t.Errorf("Expected status 200, got %d", resp.StatusCode)
	}

	body := w.Body.String()
	// Check for login form elements
	if !strings.Contains(body, "login") || !strings.Contains(body, "password") {
		t.Error("Expected login form elements in response")
	}
}

// TestLoginPostHandler tests the login form submission
func TestLoginPostHandler(t *testing.T) {
	handler, mockDB := setupTestHandler()

	// Add test user
	mockDB.users["user1"] = &models.User{
		ID:           "user1",
		Email:        "test@example.com",
		PasswordHash: "$2a$10$...", // Mock bcrypt hash
		IsActive:     true,
	}

	// Test successful login
	form := url.Values{}
	form.Add("email", "test@example.com")
	form.Add("password", "password123")

	req := httptest.NewRequest("POST", "/login", strings.NewReader(form.Encode()))
	req.Header.Add("Content-Type", "application/x-www-form-urlencoded")
	w := httptest.NewRecorder()

	handler.handleLogin(w, req)

	resp := w.Result()
	// Should redirect on successful login
	if resp.StatusCode != http.StatusSeeOther && resp.StatusCode != http.StatusOK {
		t.Errorf("Expected redirect or OK status, got %d", resp.StatusCode)
	}
}

// TestLogoutHandler tests the logout handler
func TestLogoutHandler(t *testing.T) {
	handler, mockDB := setupTestHandler()

	// Create a session
	session := &models.UserSession{
		ID:        "session1",
		UserID:    "user1",
		Token:     "test-token",
		ExpiresAt: time.Now().Add(1 * time.Hour),
	}
	mockDB.sessions[session.Token] = session

	// Create request with session cookie
	req := httptest.NewRequest("POST", "/logout", nil)
	req.AddCookie(&http.Cookie{
		Name:  "session",
		Value: session.Token,
	})
	w := httptest.NewRecorder()

	handler.handleLogout(w, req)

	resp := w.Result()
	// Should redirect after logout
	if resp.StatusCode != http.StatusSeeOther && resp.StatusCode != http.StatusFound {
		t.Errorf("Expected redirect status, got %d", resp.StatusCode)
	}

	// Check that session was deleted
	if _, ok := mockDB.sessions[session.Token]; ok {
		t.Error("Session should have been deleted")
	}
}

// TestSearchHandler tests the search functionality
func TestSearchHandler(t *testing.T) {
	handler, mockDB := setupTestHandler()

	// Add test data
	mockDB.buildings["b1"] = &models.Building{
		ID:   "b1",
		Name: "Corporate Headquarters",
	}
	mockDB.equipment["e1"] = &models.Equipment{
		ID:   "e1",
		Name: "HVAC Unit 1",
		Type: "hvac",
	}

	req := httptest.NewRequest("GET", "/search?q=headquarters", nil)
	w := httptest.NewRecorder()

	handler.handleGlobalSearch(w, req)

	resp := w.Result()
	if resp.StatusCode != http.StatusOK {
		t.Errorf("Expected status 200, got %d", resp.StatusCode)
	}

	// For HTMX requests, check if fragment is returned
	req.Header.Set("HX-Request", "true")
	w = httptest.NewRecorder()

	handler.handleGlobalSearch(w, req)

	resp = w.Result()
	if resp.StatusCode != http.StatusOK {
		t.Errorf("Expected status 200 for HTMX request, got %d", resp.StatusCode)
	}
}

// TestAPIHealthHandler tests the API health endpoint
func TestAPIHealthHandler(t *testing.T) {
	handler, _ := setupTestHandler()

	req := httptest.NewRequest("GET", "/api/health", nil)
	w := httptest.NewRecorder()

	handler.handleHealth(w, req)

	resp := w.Result()
	if resp.StatusCode != http.StatusOK {
		t.Errorf("Expected status 200, got %d", resp.StatusCode)
	}

	var health map[string]interface{}
	if err := json.NewDecoder(resp.Body).Decode(&health); err != nil {
		t.Fatalf("Failed to decode health response: %v", err)
	}

	if status, ok := health["status"].(string); !ok || status != "healthy" {
		t.Error("Expected healthy status in response")
	}
}

// TestErrorHandling tests error handling in handlers
func TestErrorHandling(t *testing.T) {
	handler, mockDB := setupTestHandler()

	// Force database errors
	mockDB.shouldFail = true

	// Test dashboard with DB error
	req := httptest.NewRequest("GET", "/dashboard", nil)
	w := httptest.NewRecorder()

	handler.HandleDashboard(w, req)

	resp := w.Result()
	// Should handle error gracefully
	if resp.StatusCode == http.StatusInternalServerError {
		t.Log("Error handled correctly with 500 status")
	}
}

// TestConcurrentRequests tests concurrent request handling
func TestConcurrentRequests(t *testing.T) {
	handler, mockDB := setupTestHandler()

	// Add test data
	for i := 0; i < 10; i++ {
		mockDB.buildings[string(rune('a'+i))] = &models.Building{
			ID:   string(rune('a' + i)),
			Name: "Building " + string(rune('A'+i)),
		}
	}

	// Run concurrent requests
	done := make(chan bool, 10)
	for i := 0; i < 10; i++ {
		go func() {
			defer func() { done <- true }()

			req := httptest.NewRequest("GET", "/buildings", nil)
			w := httptest.NewRecorder()

			handler.HandleBuildingsList(w, req)

			if w.Result().StatusCode != http.StatusOK {
				t.Errorf("Concurrent request failed")
			}
		}()
	}

	// Wait for all requests
	for i := 0; i < 10; i++ {
		<-done
	}
}

// BenchmarkDashboardHandler benchmarks the dashboard handler
func BenchmarkDashboardHandler(b *testing.B) {
	handler, mockDB := setupTestHandler()

	// Add test data
	for i := 0; i < 100; i++ {
		id := fmt.Sprintf("%d", i)
		mockDB.buildings[id] = &models.Building{
			ID:   id,
			Name: "Building " + id,
		}
	}

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		req := httptest.NewRequest("GET", "/dashboard", nil)
		w := httptest.NewRecorder()
		handler.HandleDashboard(w, req)
	}
}

// BenchmarkBuildingsHandler benchmarks the buildings list handler
func BenchmarkBuildingsHandler(b *testing.B) {
	handler, mockDB := setupTestHandler()

	// Add test buildings
	for i := 0; i < 100; i++ {
		id := fmt.Sprintf("%d", i)
		mockDB.buildings[id] = &models.Building{
			ID:   id,
			Name: "Building " + id,
		}
	}

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		req := httptest.NewRequest("GET", "/buildings", nil)
		w := httptest.NewRecorder()
		handler.HandleBuildingsList(w, req)
	}
}
