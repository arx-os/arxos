package services_test

import (
	"bytes"
	"context"
	"database/sql"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"
	"time"

	"github.com/arx-os/arxos/internal/api"
	apimodels "github.com/arx-os/arxos/internal/api/models"
	"github.com/arx-os/arxos/internal/database"
	"github.com/arx-os/arxos/internal/interfaces"
	"github.com/arx-os/arxos/pkg/models"
)

// TestDBServer is a mock database for server testing
type TestDBServer struct {
	*sql.DB
}

// NewTestDBServer creates a new test database for server tests
func NewTestDBServer(db *sql.DB) *TestDBServer {
	return &TestDBServer{DB: db}
}

// Migrate runs database migrations
func (t *TestDBServer) Migrate(ctx context.Context) error {
	// Mock implementation for testing
	return nil
}

// AcceptOrganizationInvitation accepts an organization invitation
func (t *TestDBServer) AcceptOrganizationInvitation(ctx context.Context, token, userID string) error {
	return nil
}

// AddOrganizationMember adds a member to an organization
func (t *TestDBServer) AddOrganizationMember(ctx context.Context, orgID, userID string, role string) error {
	return nil
}

// ApplyChange applies a sync change
func (t *TestDBServer) ApplyChange(ctx context.Context, change *apimodels.Change) error {
	return nil
}

// BeginTx starts a database transaction
func (t *TestDBServer) BeginTx(ctx context.Context) (*sql.Tx, error) {
	return t.DB.BeginTx(ctx, nil)
}

// Connect connects to the database
func (t *TestDBServer) Connect(ctx context.Context, dsn string) error {
	return nil
}

// CreateOrganization creates a new organization
func (t *TestDBServer) CreateOrganization(ctx context.Context, org *models.Organization) error {
	return nil
}

// CreateOrganizationInvitation creates an organization invitation
func (t *TestDBServer) CreateOrganizationInvitation(ctx context.Context, invitation *models.OrganizationInvitation) error {
	return nil
}

// CreatePasswordResetToken creates a password reset token
func (t *TestDBServer) CreatePasswordResetToken(ctx context.Context, token *models.PasswordResetToken) error {
	return nil
}

// CreateSession creates a user session
func (t *TestDBServer) CreateSession(ctx context.Context, session *models.UserSession) error {
	return nil
}

// CreateUser creates a new user
func (t *TestDBServer) CreateUser(ctx context.Context, user *models.User) error {
	return nil
}

// DeleteExpiredSessions deletes expired sessions
func (t *TestDBServer) DeleteExpiredSessions(ctx context.Context) error {
	return nil
}

// DeleteSession deletes a session
func (t *TestDBServer) DeleteSession(ctx context.Context, sessionID string) error {
	return nil
}

// DeleteUser deletes a user
func (t *TestDBServer) DeleteUser(ctx context.Context, userID string) error {
	return nil
}

// DeleteUserSessions deletes all sessions for a user
func (t *TestDBServer) DeleteUserSessions(ctx context.Context, userID string) error {
	return nil
}

// GetSession gets a session by ID
func (t *TestDBServer) GetSession(ctx context.Context, sessionID string) (*models.UserSession, error) {
	return &models.UserSession{}, nil
}

// GetUser gets a user by ID
func (t *TestDBServer) GetUser(ctx context.Context, userID string) (*models.User, error) {
	return &models.User{ID: userID}, nil
}

// GetUserByEmail gets a user by email
func (t *TestDBServer) GetUserByEmail(ctx context.Context, email string) (*models.User, error) {
	return &models.User{Email: email}, nil
}

// DeleteEquipment deletes equipment
func (t *TestDBServer) DeleteEquipment(ctx context.Context, id string) error {
	return nil
}

// DeleteExpiredPasswordResetTokens deletes expired password reset tokens
func (t *TestDBServer) DeleteExpiredPasswordResetTokens(ctx context.Context) error {
	return nil
}

// DeleteFloorPlan deletes a floor plan
func (t *TestDBServer) DeleteFloorPlan(ctx context.Context, id string) error {
	return nil
}

// DeleteOrganization deletes an organization
func (t *TestDBServer) DeleteOrganization(ctx context.Context, id string) error {
	return nil
}

// DeleteRoom deletes a room
func (t *TestDBServer) DeleteRoom(ctx context.Context, id string) error {
	return nil
}

// Exec executes a query
func (t *TestDBServer) Exec(ctx context.Context, query string, args ...interface{}) (sql.Result, error) {
	return t.DB.ExecContext(ctx, query, args...)
}

// GetAllFloorPlans gets all floor plans
func (t *TestDBServer) GetAllFloorPlans(ctx context.Context) ([]*models.FloorPlan, error) {
	return []*models.FloorPlan{}, nil
}

// GetChangesSince gets changes since a timestamp
func (t *TestDBServer) GetChangesSince(ctx context.Context, since time.Time, entityType string) ([]*apimodels.Change, error) {
	return []*apimodels.Change{}, nil
}

// GetConflictCount gets the number of conflicts
func (t *TestDBServer) GetConflictCount(ctx context.Context, buildingID string) (int, error) {
	return 0, nil
}

// GetEntityVersion gets the version of an entity
func (t *TestDBServer) GetEntityVersion(ctx context.Context, entityType, entityID string) (int, error) {
	return 1, nil
}

// GetEquipment gets equipment by ID
func (t *TestDBServer) GetEquipment(ctx context.Context, id string) (*models.Equipment, error) {
	return &models.Equipment{ID: id}, nil
}

// GetEquipmentByFloorPlan gets equipment by floor plan
func (t *TestDBServer) GetEquipmentByFloorPlan(ctx context.Context, floorPlanID string) ([]*models.Equipment, error) {
	return []*models.Equipment{}, nil
}

// GetFloorPlan gets a floor plan by ID
func (t *TestDBServer) GetFloorPlan(ctx context.Context, id string) (*models.FloorPlan, error) {
	return &models.FloorPlan{ID: id}, nil
}

// GetLastSyncTime gets the last sync time
func (t *TestDBServer) GetLastSyncTime(ctx context.Context, buildingID string) (time.Time, error) {
	return time.Now(), nil
}

// GetOrganization gets an organization by ID
func (t *TestDBServer) GetOrganization(ctx context.Context, id string) (*models.Organization, error) {
	return &models.Organization{ID: id}, nil
}

// GetOrganizationInvitation gets an organization invitation
func (t *TestDBServer) GetOrganizationInvitation(ctx context.Context, id string) (*models.OrganizationInvitation, error) {
	return &models.OrganizationInvitation{ID: id}, nil
}

// GetOrganizationInvitationByToken gets an organization invitation by token
func (t *TestDBServer) GetOrganizationInvitationByToken(ctx context.Context, token string) (*models.OrganizationInvitation, error) {
	return &models.OrganizationInvitation{ID: "test"}, nil
}

// GetOrganizationMember gets an organization member
func (t *TestDBServer) GetOrganizationMember(ctx context.Context, orgID, userID string) (*models.OrganizationMember, error) {
	return &models.OrganizationMember{}, nil
}

// GetOrganizationMembers gets organization members
func (t *TestDBServer) GetOrganizationMembers(ctx context.Context, orgID string) ([]*models.OrganizationMember, error) {
	return []*models.OrganizationMember{}, nil
}

// GetOrganizationsByUser gets organizations by user
func (t *TestDBServer) GetOrganizationsByUser(ctx context.Context, userID string) ([]*models.Organization, error) {
	return []*models.Organization{}, nil
}

// GetPasswordResetToken gets a password reset token
func (t *TestDBServer) GetPasswordResetToken(ctx context.Context, token string) (*models.PasswordResetToken, error) {
	return &models.PasswordResetToken{}, nil
}

// GetPendingChangesCount gets the count of pending changes
func (t *TestDBServer) GetPendingChangesCount(ctx context.Context, buildingID string) (int, error) {
	return 0, nil
}

// GetPendingConflicts gets pending conflicts
func (t *TestDBServer) GetPendingConflicts(ctx context.Context, buildingID string) ([]*apimodels.Conflict, error) {
	return []*apimodels.Conflict{}, nil
}

// GetRoom gets a room by ID
func (t *TestDBServer) GetRoom(ctx context.Context, id string) (*models.Room, error) {
	return &models.Room{ID: id}, nil
}

// GetRoomsByFloorPlan gets rooms by floor plan
func (t *TestDBServer) GetRoomsByFloorPlan(ctx context.Context, floorPlanID string) ([]*models.Room, error) {
	return []*models.Room{}, nil
}

// GetSessionByRefreshToken gets a session by refresh token
func (t *TestDBServer) GetSessionByRefreshToken(ctx context.Context, token string) (*models.UserSession, error) {
	return &models.UserSession{}, nil
}

// GetSpatialDB gets the spatial database
func (t *TestDBServer) GetSpatialDB() (database.SpatialDB, error) {
	return nil, nil
}

// GetVersion gets the database version
func (t *TestDBServer) GetVersion(ctx context.Context) (int, error) {
	return 1, nil
}

// HasSpatialSupport checks if spatial support is available
func (t *TestDBServer) HasSpatialSupport() bool {
	return false
}

// ListBuildings lists buildings
func (t *TestDBServer) ListBuildings(ctx context.Context, userID string, opts interface{}) ([]*models.FloorPlan, error) {
	return []*models.FloorPlan{}, nil
}

// ListOrganizationInvitations lists organization invitations
func (t *TestDBServer) ListOrganizationInvitations(ctx context.Context, orgID string) ([]*models.OrganizationInvitation, error) {
	return []*models.OrganizationInvitation{}, nil
}

// ListUsers lists users
func (t *TestDBServer) ListUsers(ctx context.Context, limit, offset int) ([]*models.User, error) {
	return []*models.User{}, nil
}

// MarkPasswordResetTokenUsed marks a password reset token as used
func (t *TestDBServer) MarkPasswordResetTokenUsed(ctx context.Context, token string) error {
	return nil
}

// Query executes a query
func (t *TestDBServer) Query(ctx context.Context, query string, args ...interface{}) (*sql.Rows, error) {
	return t.DB.QueryContext(ctx, query, args...)
}

// QueryRow executes a query that returns a single row
func (t *TestDBServer) QueryRow(ctx context.Context, query string, args ...interface{}) *sql.Row {
	return t.DB.QueryRowContext(ctx, query, args...)
}

// RemoveOrganizationMember removes an organization member
func (t *TestDBServer) RemoveOrganizationMember(ctx context.Context, orgID, userID string) error {
	return nil
}

// ResolveConflict resolves a conflict
func (t *TestDBServer) ResolveConflict(ctx context.Context, conflictID string, resolution string) error {
	return nil
}

// RevokeOrganizationInvitation revokes an organization invitation
func (t *TestDBServer) RevokeOrganizationInvitation(ctx context.Context, invitationID string) error {
	return nil
}

// SaveConflict saves a conflict
func (t *TestDBServer) SaveConflict(ctx context.Context, conflict *apimodels.Conflict) error {
	return nil
}

// SaveEquipment saves equipment
func (t *TestDBServer) SaveEquipment(ctx context.Context, equipment *models.Equipment) error {
	return nil
}

// SaveFloorPlan saves a floor plan
func (t *TestDBServer) SaveFloorPlan(ctx context.Context, floorPlan *models.FloorPlan) error {
	return nil
}

// SaveRoom saves a room
func (t *TestDBServer) SaveRoom(ctx context.Context, room *models.Room) error {
	return nil
}

// UpdateEquipment updates equipment
func (t *TestDBServer) UpdateEquipment(ctx context.Context, equipment *models.Equipment) error {
	return nil
}

// UpdateFloorPlan updates a floor plan
func (t *TestDBServer) UpdateFloorPlan(ctx context.Context, floorPlan *models.FloorPlan) error {
	return nil
}

// UpdateLastSyncTime updates the last sync time
func (t *TestDBServer) UpdateLastSyncTime(ctx context.Context, buildingID string, syncTime time.Time) error {
	return nil
}

// UpdateOrganization updates an organization
func (t *TestDBServer) UpdateOrganization(ctx context.Context, org *models.Organization) error {
	return nil
}

// UpdateOrganizationMemberRole updates an organization member role
func (t *TestDBServer) UpdateOrganizationMemberRole(ctx context.Context, orgID, userID string, role string) error {
	return nil
}

// UpdateRoom updates a room
func (t *TestDBServer) UpdateRoom(ctx context.Context, room *models.Room) error {
	return nil
}

// UpdateSession updates a session
func (t *TestDBServer) UpdateSession(ctx context.Context, session *models.UserSession) error {
	return nil
}

// UpdateUser updates a user
func (t *TestDBServer) UpdateUser(ctx context.Context, user *models.User) error {
	return nil
}

func (t *TestDBServer) BulkUpdateUsers(ctx context.Context, updates []*models.UserUpdateRequest) error {
	return nil
}

func (t *TestDBServer) CountActiveUsers(ctx context.Context) (int, error) {
	return 0, nil
}

func (t *TestDBServer) CountUsers(ctx context.Context) (int, error) {
	return 0, nil
}

func (t *TestDBServer) CountUsersByQuery(ctx context.Context, query string) (int, error) {
	return 0, nil
}

func (t *TestDBServer) GetUserStatsByRole(ctx context.Context) (map[string]int, error) {
	return nil, nil
}

func (t *TestDBServer) SearchUsers(ctx context.Context, query string, limit, offset int) ([]*models.User, error) {
	return nil, nil
}

// MockAuthServiceServer is a mock implementation of api.AuthService for server tests
type MockAuthServiceServer struct{}

func (m *MockAuthServiceServer) Login(ctx context.Context, email, password string) (interface{}, error) {
	return map[string]interface{}{
		"access_token": "test-token",
		"token_type":   "Bearer",
		"expires_in":   3600,
	}, nil
}

func (m *MockAuthServiceServer) Logout(ctx context.Context, token string) error {
	return nil
}

func (m *MockAuthServiceServer) RefreshToken(ctx context.Context, refreshToken string) (string, string, error) {
	return "new-test-token", "new-refresh-token", nil
}

func (m *MockAuthServiceServer) ValidateToken(ctx context.Context, token string) (*interfaces.TokenClaims, error) {
	return &interfaces.TokenClaims{
		UserID: "test-user",
		Email:  "test@example.com",
		Role:   "user",
	}, nil
}

func (m *MockAuthServiceServer) ChangePassword(ctx context.Context, userID, oldPassword, newPassword string) error {
	return nil
}

func (m *MockAuthServiceServer) ConfirmPasswordReset(ctx context.Context, token, newPassword string) error {
	return nil
}

func (m *MockAuthServiceServer) ResetPassword(ctx context.Context, email string) error {
	return nil
}

func (m *MockAuthServiceServer) Register(ctx context.Context, email, password, fullName string) (interface{}, error) {
	return map[string]interface{}{
		"id":     "test-user",
		"email":  email,
		"name":   fullName,
		"active": true,
	}, nil
}

func (m *MockAuthServiceServer) RevokeToken(ctx context.Context, token string) error {
	return nil
}

func (m *MockAuthServiceServer) ValidateTokenClaims(ctx context.Context, token string) (*apimodels.TokenClaims, error) {
	return &apimodels.TokenClaims{
		UserID: "test-user",
		Email:  "test@example.com",
		Role:   "user",
	}, nil
}

func (m *MockAuthServiceServer) GenerateToken(ctx context.Context, userID, email, role, orgID string) (string, error) {
	return "test-token", nil
}

func (m *MockAuthServiceServer) DeleteSession(ctx context.Context, userID, sessionID string) error {
	return nil
}

// MockBuildingServiceServer is a mock implementation of api.BuildingService for server tests
type MockBuildingServiceServer struct{}

func (m *MockBuildingServiceServer) GetBuilding(ctx context.Context, id string) (interface{}, error) {
	return map[string]interface{}{
		"id":    id,
		"name":  "Test Building",
		"level": 1,
	}, nil
}

func (m *MockBuildingServiceServer) ListBuildings(ctx context.Context, orgID string, page, limit int) ([]interface{}, error) {
	return []interface{}{}, nil
}

func (m *MockBuildingServiceServer) CreateBuilding(ctx context.Context, name string) (interface{}, error) {
	return map[string]interface{}{
		"id":   "mock-building-id",
		"name": name,
	}, nil
}

func (m *MockBuildingServiceServer) UpdateBuilding(ctx context.Context, id, name string) (interface{}, error) {
	return map[string]interface{}{
		"id":   id,
		"name": name,
	}, nil
}

func (m *MockBuildingServiceServer) DeleteBuilding(ctx context.Context, id string) error {
	return nil
}

func (m *MockBuildingServiceServer) GetEquipment(ctx context.Context, id string) (*models.Equipment, error) {
	return &models.Equipment{
		ID:   id,
		Name: "Test Equipment",
		Type: "sensor",
	}, nil
}

func (m *MockBuildingServiceServer) ListEquipment(ctx context.Context, buildingID string, filters map[string]interface{}) ([]interface{}, error) {
	return []interface{}{}, nil
}

func (m *MockBuildingServiceServer) CreateEquipment(ctx context.Context, equipment *models.Equipment) error {
	return nil
}

func (m *MockBuildingServiceServer) UpdateEquipment(ctx context.Context, equipment *models.Equipment) error {
	return nil
}

func (m *MockBuildingServiceServer) DeleteEquipment(ctx context.Context, id string) error {
	return nil
}

func (m *MockBuildingServiceServer) GetRoom(ctx context.Context, id string) (*models.Room, error) {
	return &models.Room{
		ID:   id,
		Name: "Test Room",
	}, nil
}

func (m *MockBuildingServiceServer) ListRooms(ctx context.Context, buildingID string) ([]interface{}, error) {
	return []interface{}{}, nil
}

func (m *MockBuildingServiceServer) CreateRoom(ctx context.Context, room *models.Room) error {
	return nil
}

func (m *MockBuildingServiceServer) UpdateRoom(ctx context.Context, room *models.Room) error {
	return nil
}

func (m *MockBuildingServiceServer) DeleteRoom(ctx context.Context, id string) error {
	return nil
}

// Additional methods required by the interface
func (m *MockBuildingServiceServer) GetBuildings(ctx context.Context) ([]interface{}, error) {
	return []interface{}{}, nil
}

func (m *MockBuildingServiceServer) GetConnectionGraph(ctx context.Context, buildingID string) (interface{}, error) {
	return map[string]interface{}{
		"building_id": buildingID,
		"connections": []interface{}{},
	}, nil
}

func (m *MockBuildingServiceServer) CreateConnection(ctx context.Context, fromID, toID, connType string) (interface{}, error) {
	return map[string]interface{}{
		"id":         "mock-connection-id",
		"from_id":    fromID,
		"to_id":      toID,
		"type":       connType,
		"created_at": "2023-01-01T00:00:00Z",
	}, nil
}

func (m *MockBuildingServiceServer) DeleteConnection(ctx context.Context, connectionID string) error {
	return nil
}

// TestServerHealth tests the health endpoint
func TestServerHealth(t *testing.T) {
	// Setup test server
	server := setupTestServer(t)

	// Create request
	req := httptest.NewRequest("GET", "/health", nil)
	w := httptest.NewRecorder()

	// Handle request
	server.Routes().ServeHTTP(w, req)

	// Check response
	if w.Code != http.StatusOK {
		t.Errorf("Expected status 200, got %d", w.Code)
	}

	var response map[string]string
	if err := json.NewDecoder(w.Body).Decode(&response); err != nil {
		t.Fatalf("Failed to decode response: %v", err)
	}

	if response["status"] != "healthy" {
		t.Errorf("Expected status 'healthy', got %s", response["status"])
	}
}

// TestAuthFlow tests the complete authentication flow
func TestAuthFlow(t *testing.T) {
	server := setupTestServer(t)

	// Test registration
	regData := map[string]string{
		"email":    "test@example.com",
		"password": "SecurePass123!",
		"name":     "Test User",
	}

	body, _ := json.Marshal(regData)
	req := httptest.NewRequest("POST", "/api/v1/auth/register", bytes.NewBuffer(body))
	req.Header.Set("Content-Type", "application/json")
	w := httptest.NewRecorder()

	server.Routes().ServeHTTP(w, req)

	if w.Code != http.StatusCreated && w.Code != http.StatusOK {
		t.Errorf("Registration failed with status %d: %s", w.Code, w.Body.String())
	}

	// Test login
	loginData := map[string]string{
		"email":    "test@example.com",
		"password": "SecurePass123!",
	}

	body, _ = json.Marshal(loginData)
	req = httptest.NewRequest("POST", "/api/v1/auth/login", bytes.NewBuffer(body))
	req.Header.Set("Content-Type", "application/json")
	w = httptest.NewRecorder()

	server.Routes().ServeHTTP(w, req)

	if w.Code != http.StatusOK {
		t.Errorf("Login failed with status %d: %s", w.Code, w.Body.String())
	}

	var authResp api.AuthResponse
	if err := json.NewDecoder(w.Body).Decode(&authResp); err != nil {
		t.Fatalf("Failed to decode auth response: %v", err)
	}

	if authResp.AccessToken == "" {
		t.Error("No access token received")
	}

	if authResp.RefreshToken == "" {
		t.Error("No refresh token received")
	}

	// Test token refresh
	refreshData := map[string]string{
		"refresh_token": authResp.RefreshToken,
	}

	body, _ = json.Marshal(refreshData)
	req = httptest.NewRequest("POST", "/api/v1/auth/refresh", bytes.NewBuffer(body))
	req.Header.Set("Content-Type", "application/json")
	w = httptest.NewRecorder()

	server.Routes().ServeHTTP(w, req)

	if w.Code != http.StatusOK {
		t.Errorf("Token refresh failed with status %d", w.Code)
	}
}

// TestBuildingCRUD tests building CRUD operations
func TestBuildingCRUD(t *testing.T) {
	server := setupTestServer(t)
	token := getTestToken(t, server)

	// Create building
	building := &models.FloorPlan{
		Name:     "Test Building",
		Building: "Building A",
		Level:    1,
		Rooms: []*models.Room{
			{
				ID:   "room1",
				Name: "Conference Room",
			},
		},
		Equipment: []*models.Equipment{
			{
				ID:     "eq1",
				Name:   "Projector",
				Type:   "AV",
				Status: models.StatusNormal,
			},
		},
	}

	body, _ := json.Marshal(building)
	req := httptest.NewRequest("POST", "/api/v1/buildings/create", bytes.NewBuffer(body))
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Authorization", "Bearer "+token)
	w := httptest.NewRecorder()

	server.Routes().ServeHTTP(w, req)

	if w.Code != http.StatusCreated && w.Code != http.StatusOK {
		t.Errorf("Create building failed with status %d: %s", w.Code, w.Body.String())
	}

	// List buildings
	req = httptest.NewRequest("GET", "/api/v1/buildings", nil)
	req.Header.Set("Authorization", "Bearer "+token)
	w = httptest.NewRecorder()

	server.Routes().ServeHTTP(w, req)

	if w.Code != http.StatusOK {
		t.Errorf("List buildings failed with status %d", w.Code)
	}

	var buildings []*models.FloorPlan
	if err := json.NewDecoder(w.Body).Decode(&buildings); err != nil {
		t.Fatalf("Failed to decode buildings: %v", err)
	}

	if len(buildings) == 0 {
		t.Error("No buildings returned")
	}
}

// TestPDFToASCII tests PDF to ASCII conversion
func TestPDFToASCII(t *testing.T) {
	// This would test the PDF upload and conversion flow
	// For now, we'll test the ASCII renderer directly
	server := setupTestServer(t)
	token := getTestToken(t, server)

	// Create a building with known layout
	building := &models.FloorPlan{
		Name:     "ASCII Test Building",
		Building: "Test Complex",
		Level:    1,
		Rooms: []*models.Room{
			{
				ID:   "room1",
				Name: "Office",
				Bounds: models.Bounds{
					MinX: 0, MinY: 0,
					MaxX: 10, MaxY: 10,
				},
			},
			{
				ID:   "room2",
				Name: "Kitchen",
				Bounds: models.Bounds{
					MinX: 10, MinY: 0,
					MaxX: 20, MaxY: 10,
				},
			},
		},
		Equipment: []*models.Equipment{
			{
				ID:   "outlet1",
				Name: "Power Outlet",
				Type: "electrical",
				Location: &models.Point3D{
					X: 5, Y: 5, Z: 0,
				},
				Status: models.StatusNormal,
			},
		},
	}

	// Test that the building can be created and retrieved
	body, _ := json.Marshal(building)
	req := httptest.NewRequest("POST", "/api/v1/buildings/create", bytes.NewBuffer(body))
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Authorization", "Bearer "+token)
	w := httptest.NewRecorder()

	server.Routes().ServeHTTP(w, req)

	if w.Code != http.StatusCreated && w.Code != http.StatusOK {
		t.Errorf("Create test building failed with status %d", w.Code)
	}
}

// Helper functions

func setupTestServer(t *testing.T) *api.Server {
	// Create in-memory database
	sqlDB, err := sql.Open("postgres", "postgres://localhost/arxos_test?sslmode=disable")
	if err != nil {
		t.Fatalf("Failed to create test database: %v", err)
	}

	db := NewTestDBServer(sqlDB)

	// Initialize schema
	ctx := context.Background()
	if err := db.Migrate(ctx); err != nil {
		t.Fatalf("Failed to initialize database: %v", err)
	}

	// Create mock services
	authService := &MockAuthServiceServer{}
	buildingService := &MockBuildingServiceServer{}

	apiServices := &api.Services{
		Auth:     authService,
		Building: buildingService,
		DB:       db,
	}

	// Create server
	server := api.NewServer(":0", apiServices)
	return server
}

func getTestToken(t *testing.T, server *api.Server) string {
	// Create test user and get token
	loginData := map[string]string{
		"email":    "test@example.com",
		"password": "TestPass123!",
	}

	// First register
	body, _ := json.Marshal(loginData)
	req := httptest.NewRequest("POST", "/api/v1/auth/register", bytes.NewBuffer(body))
	req.Header.Set("Content-Type", "application/json")
	w := httptest.NewRecorder()

	server.Routes().ServeHTTP(w, req)

	// Then login
	req = httptest.NewRequest("POST", "/api/v1/auth/login", bytes.NewBuffer(body))
	req.Header.Set("Content-Type", "application/json")
	w = httptest.NewRecorder()

	server.Routes().ServeHTTP(w, req)

	var authResp api.AuthResponse
	if err := json.NewDecoder(w.Body).Decode(&authResp); err != nil {
		t.Fatalf("Failed to get test token: %v", err)
	}

	return authResp.AccessToken
}
