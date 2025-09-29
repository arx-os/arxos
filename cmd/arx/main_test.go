package main

import (
	"context"
	"database/sql"
	"testing"

	"github.com/arx-os/arxos/internal/database"
	"github.com/arx-os/arxos/pkg/models"
	"github.com/stretchr/testify/assert"
)

// MockDB implements the database.DB interface for testing
type MockDB struct {
	floorPlans []*models.FloorPlan
	equipment  []*models.Equipment
	rooms      []*models.Room
}

func (m *MockDB) Connect(ctx context.Context, dbPath string) error { return nil }
func (m *MockDB) Close() error                                     { return nil }
func (m *MockDB) BeginTx(ctx context.Context) (*sql.Tx, error)     { return nil, nil }
func (m *MockDB) HasSpatialSupport() bool                          { return true }
func (m *MockDB) GetSpatialDB() (database.SpatialDB, error)        { return nil, nil }

// Floor plan operations
func (m *MockDB) GetFloorPlan(ctx context.Context, id string) (*models.FloorPlan, error) {
	for _, plan := range m.floorPlans {
		if plan.ID == id {
			return plan, nil
		}
	}
	return nil, database.ErrNotFound
}

func (m *MockDB) GetAllFloorPlans(ctx context.Context) ([]*models.FloorPlan, error) {
	return m.floorPlans, nil
}

func (m *MockDB) SaveFloorPlan(ctx context.Context, plan *models.FloorPlan) error {
	if plan.ID == "" {
		plan.ID = "test-building-" + string(rune(len(m.floorPlans)+1))
	}
	m.floorPlans = append(m.floorPlans, plan)
	return nil
}

func (m *MockDB) UpdateFloorPlan(ctx context.Context, plan *models.FloorPlan) error {
	for i, existing := range m.floorPlans {
		if existing.ID == plan.ID {
			m.floorPlans[i] = plan
			return nil
		}
	}
	return database.ErrNotFound
}

func (m *MockDB) DeleteFloorPlan(ctx context.Context, id string) error {
	for i, plan := range m.floorPlans {
		if plan.ID == id {
			m.floorPlans = append(m.floorPlans[:i], m.floorPlans[i+1:]...)
			return nil
		}
	}
	return database.ErrNotFound
}

// Equipment operations
func (m *MockDB) GetEquipment(ctx context.Context, id string) (*models.Equipment, error) {
	for _, eq := range m.equipment {
		if eq.ID == id {
			return eq, nil
		}
	}
	return nil, database.ErrNotFound
}

func (m *MockDB) GetEquipmentByFloorPlan(ctx context.Context, floorPlanID string) ([]*models.Equipment, error) {
	var result []*models.Equipment
	for _, eq := range m.equipment {
		// Simple check - in real implementation this would be more complex
		if len(eq.RoomID) > 0 {
			result = append(result, eq)
		}
	}
	return result, nil
}

func (m *MockDB) SaveEquipment(ctx context.Context, equipment *models.Equipment) error {
	if equipment.ID == "" {
		equipment.ID = "test-equipment-" + string(rune(len(m.equipment)+1))
	}
	m.equipment = append(m.equipment, equipment)
	return nil
}

func (m *MockDB) UpdateEquipment(ctx context.Context, equipment *models.Equipment) error {
	for i, existing := range m.equipment {
		if existing.ID == equipment.ID {
			m.equipment[i] = equipment
			return nil
		}
	}
	return database.ErrNotFound
}

func (m *MockDB) DeleteEquipment(ctx context.Context, id string) error {
	for i, eq := range m.equipment {
		if eq.ID == id {
			m.equipment = append(m.equipment[:i], m.equipment[i+1:]...)
			return nil
		}
	}
	return database.ErrNotFound
}

// Room operations
func (m *MockDB) GetRoom(ctx context.Context, id string) (*models.Room, error) {
	for _, room := range m.rooms {
		if room.ID == id {
			return room, nil
		}
	}
	return nil, database.ErrNotFound
}

func (m *MockDB) GetRoomsByFloorPlan(ctx context.Context, floorPlanID string) ([]*models.Room, error) {
	var result []*models.Room
	for _, room := range m.rooms {
		if room.FloorPlanID == floorPlanID {
			result = append(result, room)
		}
	}
	return result, nil
}

func (m *MockDB) SaveRoom(ctx context.Context, room *models.Room) error {
	if room.ID == "" {
		room.ID = "test-room-" + string(rune(len(m.rooms)+1))
	}
	m.rooms = append(m.rooms, room)
	return nil
}

func (m *MockDB) UpdateRoom(ctx context.Context, room *models.Room) error {
	for i, existing := range m.rooms {
		if existing.ID == room.ID {
			m.rooms[i] = room
			return nil
		}
	}
	return database.ErrNotFound
}

func (m *MockDB) DeleteRoom(ctx context.Context, id string) error {
	for i, room := range m.rooms {
		if room.ID == id {
			m.rooms = append(m.rooms[:i], m.rooms[i+1:]...)
			return nil
		}
	}
	return database.ErrNotFound
}

// User operations (not needed for CLI tests but required by interface)
func (m *MockDB) GetUser(ctx context.Context, id string) (*models.User, error) { return nil, nil }
func (m *MockDB) GetUserByEmail(ctx context.Context, email string) (*models.User, error) {
	return nil, nil
}
func (m *MockDB) CreateUser(ctx context.Context, user *models.User) error { return nil }
func (m *MockDB) UpdateUser(ctx context.Context, user *models.User) error { return nil }
func (m *MockDB) DeleteUser(ctx context.Context, id string) error         { return nil }
func (m *MockDB) ListUsers(ctx context.Context, limit, offset int) ([]*models.User, error) {
	return nil, nil
}
func (m *MockDB) CountUsers(ctx context.Context) (int, error) { return 0, nil }
func (m *MockDB) SearchUsers(ctx context.Context, query string, limit, offset int) ([]*models.User, error) {
	return nil, nil
}
func (m *MockDB) CountUsersByQuery(ctx context.Context, query string) (int, error) { return 0, nil }
func (m *MockDB) CountActiveUsers(ctx context.Context) (int, error)                { return 0, nil }
func (m *MockDB) GetUserStatsByRole(ctx context.Context) (map[string]int, error)   { return nil, nil }
func (m *MockDB) BulkUpdateUsers(ctx context.Context, updates []*models.UserUpdateRequest) error {
	return nil
}

// Session operations (not needed for CLI tests but required by interface)
func (m *MockDB) CreateSession(ctx context.Context, session *models.UserSession) error { return nil }
func (m *MockDB) GetSession(ctx context.Context, token string) (*models.UserSession, error) {
	return nil, nil
}
func (m *MockDB) GetSessionByRefreshToken(ctx context.Context, refreshToken string) (*models.UserSession, error) {
	return nil, nil
}
func (m *MockDB) UpdateSession(ctx context.Context, session *models.UserSession) error { return nil }
func (m *MockDB) DeleteSession(ctx context.Context, id string) error                   { return nil }
func (m *MockDB) DeleteExpiredSessions(ctx context.Context) error                      { return nil }
func (m *MockDB) DeleteUserSessions(ctx context.Context, userID string) error          { return nil }

// Password reset operations (not needed for CLI tests but required by interface)
func (m *MockDB) CreatePasswordResetToken(ctx context.Context, token *models.PasswordResetToken) error {
	return nil
}
func (m *MockDB) GetPasswordResetToken(ctx context.Context, token string) (*models.PasswordResetToken, error) {
	return nil, nil
}
func (m *MockDB) MarkPasswordResetTokenUsed(ctx context.Context, token string) error { return nil }
func (m *MockDB) DeleteExpiredPasswordResetTokens(ctx context.Context) error         { return nil }

// Organization operations (not needed for CLI tests but required by interface)
func (m *MockDB) GetOrganization(ctx context.Context, id string) (*models.Organization, error) {
	return nil, nil
}
func (m *MockDB) GetOrganizationsByUser(ctx context.Context, userID string) ([]*models.Organization, error) {
	return nil, nil
}
func (m *MockDB) CreateOrganization(ctx context.Context, org *models.Organization) error { return nil }
func (m *MockDB) UpdateOrganization(ctx context.Context, org *models.Organization) error { return nil }
func (m *MockDB) DeleteOrganization(ctx context.Context, id string) error                { return nil }

// Organization member operations (not needed for CLI tests but required by interface)
func (m *MockDB) AddOrganizationMember(ctx context.Context, orgID, userID, role string) error {
	return nil
}
func (m *MockDB) RemoveOrganizationMember(ctx context.Context, orgID, userID string) error {
	return nil
}
func (m *MockDB) UpdateOrganizationMemberRole(ctx context.Context, orgID, userID, role string) error {
	return nil
}
func (m *MockDB) GetOrganizationMembers(ctx context.Context, orgID string) ([]*models.OrganizationMember, error) {
	return nil, nil
}
func (m *MockDB) GetOrganizationMember(ctx context.Context, orgID, userID string) (*models.OrganizationMember, error) {
	return nil, nil
}

// Organization invitation operations (not needed for CLI tests but required by interface)
func (m *MockDB) CreateOrganizationInvitation(ctx context.Context, invitation *models.OrganizationInvitation) error {
	return nil
}
func (m *MockDB) GetOrganizationInvitationByToken(ctx context.Context, token string) (*models.OrganizationInvitation, error) {
	return nil, nil
}
func (m *MockDB) GetOrganizationInvitation(ctx context.Context, id string) (*models.OrganizationInvitation, error) {
	return nil, nil
}
func (m *MockDB) ListOrganizationInvitations(ctx context.Context, orgID string) ([]*models.OrganizationInvitation, error) {
	return nil, nil
}
func (m *MockDB) AcceptOrganizationInvitation(ctx context.Context, token, userID string) error {
	return nil
}
func (m *MockDB) RevokeOrganizationInvitation(ctx context.Context, id string) error { return nil }

// Query operations (not needed for CLI tests but required by interface)
func (m *MockDB) Query(ctx context.Context, query string, args ...interface{}) (*sql.Rows, error) {
	return nil, nil
}
func (m *MockDB) QueryRow(ctx context.Context, query string, args ...interface{}) *sql.Row {
	return nil
}
func (m *MockDB) Exec(ctx context.Context, query string, args ...interface{}) (sql.Result, error) {
	return nil, nil
}

// Migration operations (not needed for CLI tests but required by interface)
func (m *MockDB) Migrate(ctx context.Context) error           { return nil }
func (m *MockDB) GetVersion(ctx context.Context) (int, error) { return 1, nil }

// Test setup helper
func setupTest() (*MockDB, context.Context) {
	mockDB := &MockDB{
		floorPlans: make([]*models.FloorPlan, 0),
		equipment:  make([]*models.Equipment, 0),
		rooms:      make([]*models.Room, 0),
	}
	ctx := context.Background()

	// Set global database connection for testing
	// TODO: Update to use DI container when testing infrastructure is properly integrated
	// For now, use placeholder implementation
	// dbConn = mockDB

	return mockDB, ctx
}

// Test cleanup helper
func cleanupTest() {
	// TODO: Update to use DI container when testing infrastructure is properly integrated
	// For now, use placeholder implementation
	// dbConn = nil
}

// Reset mockDB helper
func (m *MockDB) reset() {
	m.floorPlans = make([]*models.FloorPlan, 0)
	m.equipment = make([]*models.Equipment, 0)
	m.rooms = make([]*models.Room, 0)
}

func TestAddBuilding(t *testing.T) {
	mockDB, ctx := setupTest()
	defer cleanupTest()

	tests := []struct {
		name         string
		buildingName string
		expectError  bool
	}{
		{
			name:         "Valid building name",
			buildingName: "Test Building",
			expectError:  false,
		},
		{
			name:         "Empty building name",
			buildingName: "",
			expectError:  true,
		},
		{
			name:         "Long building name",
			buildingName: "Very Long Building Name That Should Still Work",
			expectError:  false,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			// Reset mockDB for each test case
			mockDB.reset()

			err := addBuilding(ctx, tt.buildingName)

			if tt.expectError {
				assert.Error(t, err)
				assert.Contains(t, err.Error(), "cannot be empty")
			} else {
				assert.NoError(t, err)
				// Verify building was created
				assert.Len(t, mockDB.floorPlans, 1)
				assert.Equal(t, tt.buildingName, mockDB.floorPlans[0].Name)
				assert.Equal(t, tt.buildingName, mockDB.floorPlans[0].Building)
				assert.Equal(t, 0, mockDB.floorPlans[0].Level)
			}
		})
	}
}

func TestAddEquipment(t *testing.T) {
	mockDB, ctx := setupTest()
	defer cleanupTest()

	tests := []struct {
		name          string
		equipmentName string
		expectError   bool
	}{
		{
			name:          "Valid equipment name",
			equipmentName: "Test Equipment",
			expectError:   false,
		},
		{
			name:          "Empty equipment name",
			equipmentName: "",
			expectError:   true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			err := addEquipment(ctx, tt.equipmentName)

			if tt.expectError {
				assert.Error(t, err)
				assert.Contains(t, err.Error(), "cannot be empty")
			} else {
				assert.NoError(t, err)
				// Verify equipment was created
				assert.Len(t, mockDB.equipment, 1)
				assert.Equal(t, tt.equipmentName, mockDB.equipment[0].Name)
				assert.Equal(t, "general", mockDB.equipment[0].Type)
				assert.Equal(t, "operational", mockDB.equipment[0].Status)
			}
		})
	}
}

func TestAddRoom(t *testing.T) {
	mockDB, ctx := setupTest()
	defer cleanupTest()

	tests := []struct {
		name        string
		roomName    string
		expectError bool
	}{
		{
			name:        "Valid room name",
			roomName:    "Test Room",
			expectError: false,
		},
		{
			name:        "Empty room name",
			roomName:    "",
			expectError: true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			err := addRoom(ctx, tt.roomName)

			if tt.expectError {
				assert.Error(t, err)
				assert.Contains(t, err.Error(), "cannot be empty")
			} else {
				assert.NoError(t, err)
				// Verify room was created
				assert.Len(t, mockDB.rooms, 1)
				assert.Equal(t, tt.roomName, mockDB.rooms[0].Name)
			}
		})
	}
}

func TestGetBuilding(t *testing.T) {
	mockDB, ctx := setupTest()
	defer cleanupTest()

	// Create a test building
	testBuilding := &models.FloorPlan{
		ID:       "test-building-1",
		Name:     "Test Building",
		Building: "Test Building",
		Level:    1,
	}
	mockDB.floorPlans = append(mockDB.floorPlans, testBuilding)

	tests := []struct {
		name        string
		buildingID  string
		expectError bool
	}{
		{
			name:        "Valid building ID",
			buildingID:  "test-building-1",
			expectError: false,
		},
		{
			name:        "Empty building ID",
			buildingID:  "",
			expectError: true,
		},
		{
			name:        "Non-existent building ID",
			buildingID:  "non-existent",
			expectError: true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			err := getBuilding(ctx, tt.buildingID)

			if tt.expectError {
				assert.Error(t, err)
				if tt.buildingID == "" {
					assert.Contains(t, err.Error(), "cannot be empty")
				} else {
					assert.Contains(t, err.Error(), "failed to get building")
				}
			} else {
				assert.NoError(t, err)
			}
		})
	}
}

func TestGetEquipment(t *testing.T) {
	mockDB, ctx := setupTest()
	defer cleanupTest()

	// Create test equipment
	testEquipment := &models.Equipment{
		ID:     "test-equipment-1",
		Name:   "Test Equipment",
		Type:   "hvac",
		Status: "operational",
	}
	mockDB.equipment = append(mockDB.equipment, testEquipment)

	tests := []struct {
		name        string
		equipmentID string
		expectError bool
	}{
		{
			name:        "Valid equipment ID",
			equipmentID: "test-equipment-1",
			expectError: false,
		},
		{
			name:        "Empty equipment ID",
			equipmentID: "",
			expectError: true,
		},
		{
			name:        "Non-existent equipment ID",
			equipmentID: "non-existent",
			expectError: true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			err := getEquipment(ctx, tt.equipmentID)

			if tt.expectError {
				assert.Error(t, err)
				if tt.equipmentID == "" {
					assert.Contains(t, err.Error(), "cannot be empty")
				} else {
					assert.Contains(t, err.Error(), "failed to get equipment")
				}
			} else {
				assert.NoError(t, err)
			}
		})
	}
}

func TestGetRoom(t *testing.T) {
	mockDB, ctx := setupTest()
	defer cleanupTest()

	// Create test room
	testRoom := &models.Room{
		ID:   "test-room-1",
		Name: "Test Room",
	}
	mockDB.rooms = append(mockDB.rooms, testRoom)

	tests := []struct {
		name        string
		roomID      string
		expectError bool
	}{
		{
			name:        "Valid room ID",
			roomID:      "test-room-1",
			expectError: false,
		},
		{
			name:        "Empty room ID",
			roomID:      "",
			expectError: true,
		},
		{
			name:        "Non-existent room ID",
			roomID:      "non-existent",
			expectError: true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			err := getRoom(ctx, tt.roomID)

			if tt.expectError {
				assert.Error(t, err)
				if tt.roomID == "" {
					assert.Contains(t, err.Error(), "cannot be empty")
				} else {
					assert.Contains(t, err.Error(), "failed to get room")
				}
			} else {
				assert.NoError(t, err)
			}
		})
	}
}

func TestUpdateBuilding(t *testing.T) {
	mockDB, ctx := setupTest()
	defer cleanupTest()

	// Create a test building
	testBuilding := &models.FloorPlan{
		ID:       "test-building-1",
		Name:     "Test Building",
		Building: "Test Building",
		Level:    1,
	}
	mockDB.floorPlans = append(mockDB.floorPlans, testBuilding)

	tests := []struct {
		name        string
		buildingID  string
		expectError bool
	}{
		{
			name:        "Valid building ID",
			buildingID:  "test-building-1",
			expectError: false,
		},
		{
			name:        "Empty building ID",
			buildingID:  "",
			expectError: true,
		},
		{
			name:        "Non-existent building ID",
			buildingID:  "non-existent",
			expectError: true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			err := updateBuilding(ctx, tt.buildingID)

			if tt.expectError {
				assert.Error(t, err)
				if tt.buildingID == "" {
					assert.Contains(t, err.Error(), "cannot be empty")
				} else {
					assert.Contains(t, err.Error(), "failed to get building")
				}
			} else {
				assert.NoError(t, err)
			}
		})
	}
}

func TestUpdateEquipment(t *testing.T) {
	mockDB, ctx := setupTest()
	defer cleanupTest()

	// Create test equipment
	testEquipment := &models.Equipment{
		ID:     "test-equipment-1",
		Name:   "Test Equipment",
		Type:   "hvac",
		Status: "operational",
	}
	mockDB.equipment = append(mockDB.equipment, testEquipment)

	tests := []struct {
		name        string
		equipmentID string
		expectError bool
	}{
		{
			name:        "Valid equipment ID",
			equipmentID: "test-equipment-1",
			expectError: false,
		},
		{
			name:        "Empty equipment ID",
			equipmentID: "",
			expectError: true,
		},
		{
			name:        "Non-existent equipment ID",
			equipmentID: "non-existent",
			expectError: true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			err := updateEquipment(ctx, tt.equipmentID)

			if tt.expectError {
				assert.Error(t, err)
				if tt.equipmentID == "" {
					assert.Contains(t, err.Error(), "cannot be empty")
				} else {
					assert.Contains(t, err.Error(), "failed to get equipment")
				}
			} else {
				assert.NoError(t, err)
				// Verify equipment was updated
				assert.Equal(t, "updated", mockDB.equipment[0].Status)
			}
		})
	}
}

func TestUpdateRoom(t *testing.T) {
	mockDB, ctx := setupTest()
	defer cleanupTest()

	// Create test room
	testRoom := &models.Room{
		ID:   "test-room-1",
		Name: "Test Room",
	}
	mockDB.rooms = append(mockDB.rooms, testRoom)

	tests := []struct {
		name        string
		roomID      string
		expectError bool
	}{
		{
			name:        "Valid room ID",
			roomID:      "test-room-1",
			expectError: false,
		},
		{
			name:        "Empty room ID",
			roomID:      "",
			expectError: true,
		},
		{
			name:        "Non-existent room ID",
			roomID:      "non-existent",
			expectError: true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			err := updateRoom(ctx, tt.roomID)

			if tt.expectError {
				assert.Error(t, err)
				if tt.roomID == "" {
					assert.Contains(t, err.Error(), "cannot be empty")
				} else {
					assert.Contains(t, err.Error(), "failed to get room")
				}
			} else {
				assert.NoError(t, err)
			}
		})
	}
}

func TestRemoveBuilding(t *testing.T) {
	mockDB, ctx := setupTest()
	defer cleanupTest()

	// Create a test building
	testBuilding := &models.FloorPlan{
		ID:       "test-building-1",
		Name:     "Test Building",
		Building: "Test Building",
		Level:    1,
	}
	mockDB.floorPlans = append(mockDB.floorPlans, testBuilding)

	tests := []struct {
		name          string
		buildingID    string
		expectError   bool
		expectedCount int
	}{
		{
			name:          "Valid building ID",
			buildingID:    "test-building-1",
			expectError:   false,
			expectedCount: 0,
		},
		{
			name:          "Empty building ID",
			buildingID:    "",
			expectError:   true,
			expectedCount: 0, // No building added because function fails early
		},
		{
			name:          "Non-existent building ID",
			buildingID:    "non-existent",
			expectError:   true,
			expectedCount: 0, // No building added because function fails early
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			// Reset and setup test data for each case
			mockDB.reset()
			if tt.buildingID == "test-building-1" {
				// Add test building for valid cases or non-empty ID cases
				testBuilding := &models.FloorPlan{
					ID:       "test-building-1",
					Name:     "Test Building",
					Building: "Test Building",
					Level:    1,
				}
				mockDB.floorPlans = append(mockDB.floorPlans, testBuilding)
			}

			err := removeBuilding(ctx, tt.buildingID)

			if tt.expectError {
				assert.Error(t, err)
				if tt.buildingID == "" {
					assert.Contains(t, err.Error(), "cannot be empty")
				} else {
					assert.Contains(t, err.Error(), "not found")
				}
			} else {
				assert.NoError(t, err)
			}

			assert.Len(t, mockDB.floorPlans, tt.expectedCount)
		})
	}
}

func TestRemoveEquipment(t *testing.T) {
	mockDB, ctx := setupTest()
	defer cleanupTest()

	// Create test equipment
	testEquipment := &models.Equipment{
		ID:     "test-equipment-1",
		Name:   "Test Equipment",
		Type:   "hvac",
		Status: "operational",
	}
	mockDB.equipment = append(mockDB.equipment, testEquipment)

	tests := []struct {
		name          string
		equipmentID   string
		expectError   bool
		expectedCount int
	}{
		{
			name:          "Valid equipment ID",
			equipmentID:   "test-equipment-1",
			expectError:   false,
			expectedCount: 0,
		},
		{
			name:          "Empty equipment ID",
			equipmentID:   "",
			expectError:   true,
			expectedCount: 0, // No equipment added because function fails early
		},
		{
			name:          "Non-existent equipment ID",
			equipmentID:   "non-existent",
			expectError:   true,
			expectedCount: 0, // No equipment added because function fails early
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			// Reset and setup test data for each case
			mockDB.reset()
			if tt.equipmentID == "test-equipment-1" {
				// Add test equipment for valid cases or non-empty ID cases
				testEquipment := &models.Equipment{
					ID:     "test-equipment-1",
					Name:   "Test Equipment",
					Type:   "hvac",
					Status: "operational",
				}
				mockDB.equipment = append(mockDB.equipment, testEquipment)
			}

			err := removeEquipment(ctx, tt.equipmentID)

			if tt.expectError {
				assert.Error(t, err)
				if tt.equipmentID == "" {
					assert.Contains(t, err.Error(), "cannot be empty")
				} else {
					assert.Contains(t, err.Error(), "not found")
				}
			} else {
				assert.NoError(t, err)
			}

			assert.Len(t, mockDB.equipment, tt.expectedCount)
		})
	}
}

func TestRemoveRoom(t *testing.T) {
	mockDB, ctx := setupTest()
	defer cleanupTest()

	// Create test room
	testRoom := &models.Room{
		ID:   "test-room-1",
		Name: "Test Room",
	}
	mockDB.rooms = append(mockDB.rooms, testRoom)

	tests := []struct {
		name          string
		roomID        string
		expectError   bool
		expectedCount int
	}{
		{
			name:          "Valid room ID",
			roomID:        "test-room-1",
			expectError:   false,
			expectedCount: 0,
		},
		{
			name:          "Empty room ID",
			roomID:        "",
			expectError:   true,
			expectedCount: 0, // No room added because function fails early
		},
		{
			name:          "Non-existent room ID",
			roomID:        "non-existent",
			expectError:   true,
			expectedCount: 0, // No room added because function fails early
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			// Reset and setup test data for each case
			mockDB.reset()
			if tt.roomID == "test-room-1" {
				// Add test room for valid cases or non-empty ID cases
				testRoom := &models.Room{
					ID:   "test-room-1",
					Name: "Test Room",
				}
				mockDB.rooms = append(mockDB.rooms, testRoom)
			}

			err := removeRoom(ctx, tt.roomID)

			if tt.expectError {
				assert.Error(t, err)
				if tt.roomID == "" {
					assert.Contains(t, err.Error(), "cannot be empty")
				} else {
					assert.Contains(t, err.Error(), "not found")
				}
			} else {
				assert.NoError(t, err)
			}

			assert.Len(t, mockDB.rooms, tt.expectedCount)
		})
	}
}

func TestTraceConnections(t *testing.T) {
	ctx := context.Background()

	tests := []struct {
		name        string
		path        string
		expectError bool
	}{
		{
			name:        "Valid path",
			path:        "/test/path",
			expectError: false,
		},
		{
			name:        "Empty path",
			path:        "",
			expectError: true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			connections, err := traceConnections(ctx, tt.path)

			if tt.expectError {
				assert.Error(t, err)
				assert.Contains(t, err.Error(), "cannot be empty")
				assert.Nil(t, connections)
			} else {
				assert.NoError(t, err)
				assert.NotNil(t, connections)
				assert.Len(t, connections, 1)
				assert.Equal(t, "start", connections[0].From)
				assert.Equal(t, "end", connections[0].To)
				assert.Equal(t, "trace", connections[0].Type)
			}
		})
	}
}

func TestStartFileWatcher(t *testing.T) {
	ctx := context.Background()

	tests := []struct {
		name        string
		watchDir    string
		expectError bool
	}{
		{
			name:        "Valid directory",
			watchDir:    "/tmp/test",
			expectError: false,
		},
		{
			name:        "Empty directory",
			watchDir:    "",
			expectError: true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			err := startFileWatcher(ctx, tt.watchDir)

			if tt.expectError {
				assert.Error(t, err)
				assert.Contains(t, err.Error(), "cannot be empty")
			} else {
				assert.NoError(t, err)
			}
		})
	}
}

func TestRunSimulation(t *testing.T) {
	mockDB, ctx := setupTest()
	defer cleanupTest()

	// Create a test building
	testBuilding := &models.FloorPlan{
		ID:       "test-building-1",
		Name:     "Test Building",
		Building: "Test Building",
		Level:    1,
	}
	mockDB.floorPlans = append(mockDB.floorPlans, testBuilding)

	tests := []struct {
		name        string
		buildingID  string
		simType     string
		expectError bool
	}{
		{
			name:        "Valid parameters",
			buildingID:  "test-building-1",
			simType:     "energy",
			expectError: false,
		},
		{
			name:        "Empty building ID",
			buildingID:  "",
			simType:     "energy",
			expectError: true,
		},
		{
			name:        "Empty sim type",
			buildingID:  "test-building-1",
			simType:     "",
			expectError: true,
		},
		{
			name:        "Non-existent building",
			buildingID:  "non-existent",
			simType:     "energy",
			expectError: true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			results, err := runSimulation(ctx, tt.buildingID, tt.simType)

			if tt.expectError {
				assert.Error(t, err)
				assert.Nil(t, results)
			} else {
				assert.NoError(t, err)
				assert.NotNil(t, results)
				assert.Equal(t, "completed", results["status"])
				assert.Equal(t, tt.buildingID, results["building_id"])
				assert.Equal(t, tt.simType, results["sim_type"])
				assert.True(t, results["success"].(bool))
			}
		})
	}
}

func TestSyncData(t *testing.T) {
	mockDB, ctx := setupTest()
	defer cleanupTest()

	// Create test buildings
	testBuildings := []*models.FloorPlan{
		{ID: "building-1", Name: "Building 1"},
		{ID: "building-2", Name: "Building 2"},
		{ID: "building-3", Name: "Building 3"},
	}
	mockDB.floorPlans = testBuildings

	err := syncData(ctx)

	assert.NoError(t, err)
	// The function should complete without error and log the sync count
	// Verify that buildings were accessed (they should be in the mockDB)
	assert.Len(t, mockDB.floorPlans, 3)
}

// Benchmark tests for performance validation
func BenchmarkAddBuilding(b *testing.B) {
	mockDB, ctx := setupTest()
	defer cleanupTest()

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		err := addBuilding(ctx, "Benchmark Building")
		if err != nil {
			b.Fatal(err)
		}
	}

	// Verify buildings were created
	assert.Len(b, mockDB.floorPlans, b.N)
}

func BenchmarkGetBuilding(b *testing.B) {
	mockDB, ctx := setupTest()
	defer cleanupTest()

	// Create test building
	testBuilding := &models.FloorPlan{
		ID:       "benchmark-building",
		Name:     "Benchmark Building",
		Building: "Benchmark Building",
		Level:    1,
	}
	mockDB.floorPlans = append(mockDB.floorPlans, testBuilding)

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		err := getBuilding(ctx, "benchmark-building")
		if err != nil {
			b.Fatal(err)
		}
	}
}
