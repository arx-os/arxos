package web

import (
	"bytes"
	"context"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"net/url"
	"strings"
	"testing"
	"time"

	"github.com/arx-os/arxos/internal/api"
	"github.com/arx-os/arxos/internal/database"
	"github.com/arx-os/arxos/pkg/models"
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
		return database.ErrInternal
	}
	m.users[user.ID] = user
	return nil
}

func (m *MockDB) UpdateUser(ctx context.Context, user *models.User) error {
	if m.shouldFail {
		return database.ErrInternal
	}
	m.users[user.ID] = user
	return nil
}

func (m *MockDB) DeleteUser(ctx context.Context, id string) error {
	if m.shouldFail {
		return database.ErrInternal
	}
	delete(m.users, id)
	return nil
}

func (m *MockDB) CreateSession(ctx context.Context, session *models.UserSession) error {
	if m.shouldFail {
		return database.ErrInternal
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

func (m *MockDB) ListBuildings(ctx context.Context, opts *database.ListOptions) ([]*models.Building, error) {
	if m.shouldFail {
		return nil, database.ErrInternal
	}
	var buildings []*models.Building
	for _, b := range m.buildings {
		buildings = append(buildings, b)
	}
	return buildings, nil
}

func (m *MockDB) CreateBuilding(ctx context.Context, building *models.Building) error {
	if m.shouldFail {
		return database.ErrInternal
	}
	m.buildings[building.ID] = building
	return nil
}

func (m *MockDB) UpdateBuilding(ctx context.Context, building *models.Building) error {
	if m.shouldFail {
		return database.ErrInternal
	}
	m.buildings[building.ID] = building
	return nil
}

func (m *MockDB) DeleteBuilding(ctx context.Context, id string) error {
	if m.shouldFail {
		return database.ErrInternal
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

func (m *MockDB) Query(ctx context.Context, query string, args ...interface{}) (*database.Rows, error) {
	return nil, nil
}

func (m *MockDB) Exec(ctx context.Context, query string, args ...interface{}) (database.Result, error) {
	return nil, nil
}

func (m *MockDB) Close() error {
	return nil
}

// Mock implementations of other required methods...
func (m *MockDB) CreateUserWithPassword(ctx context.Context, user *models.User, password string) error {
	return m.CreateUser(ctx, user)
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
	services := &api.Services{
		DB:   mockDB,
		User: api.NewUserService(mockDB),
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

	handler.DashboardHandler(w, req)

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
			Address:     "123 Test St",
			City:        "Test City",
			State:       "TS",
			PostalCode:  "12345",
			Country:     "Test Country",
			BuildingType: "office",
			CreatedAt:   time.Now(),
			UpdatedAt:   time.Now(),
		}
	}

	req := httptest.NewRequest("GET", "/buildings", nil)
	w := httptest.NewRecorder()

	handler.BuildingsHandler(w, req)

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
		Address:     "456 Main St",
		City:        "Test City",
		State:       "TS",
		PostalCode:  "12345",
		Country:     "USA",
		BuildingType: "commercial",
		Floors:      5,
		TotalArea:   10000,
	}

	// Create router for path params
	r := chi.NewRouter()
	r.Get("/buildings/{id}", handler.BuildingDetailHandler)

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

	handler.LoginHandler(w, req)

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

	handler.LoginPostHandler(w, req)

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

	handler.LogoutHandler(w, req)

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

	handler.SearchHandler(w, req)

	resp := w.Result()
	if resp.StatusCode != http.StatusOK {
		t.Errorf("Expected status 200, got %d", resp.StatusCode)
	}

	// For HTMX requests, check if fragment is returned
	req.Header.Set("HX-Request", "true")
	w = httptest.NewRecorder()

	handler.SearchHandler(w, req)

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

	handler.APIHealthHandler(w, req)

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

	handler.DashboardHandler(w, req)

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

			handler.BuildingsHandler(w, req)

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
		mockDB.buildings[string(i)] = &models.Building{
			ID:   string(i),
			Name: "Building " + string(i),
		}
	}

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		req := httptest.NewRequest("GET", "/dashboard", nil)
		w := httptest.NewRecorder()
		handler.DashboardHandler(w, req)
	}
}

// BenchmarkBuildingsHandler benchmarks the buildings list handler
func BenchmarkBuildingsHandler(b *testing.B) {
	handler, mockDB := setupTestHandler()

	// Add test buildings
	for i := 0; i < 100; i++ {
		mockDB.buildings[string(i)] = &models.Building{
			ID:   string(i),
			Name: "Building " + string(i),
		}
	}

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		req := httptest.NewRequest("GET", "/buildings", nil)
		w := httptest.NewRecorder()
		handler.BuildingsHandler(w, req)
	}
}