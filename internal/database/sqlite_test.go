package database

import (
	"context"
	"os"
	"path/filepath"
	"testing"
	"time"
	
	"github.com/arx-os/arxos/pkg/models"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

func setupTestDB(t *testing.T) (*SQLiteDB, string, func()) {
	tempDir, err := os.MkdirTemp("", "arxos_db_test_*")
	require.NoError(t, err)
	
	dbPath := filepath.Join(tempDir, "test.db")
	config := NewConfig(dbPath)
	db := NewSQLiteDB(config)
	
	ctx := context.Background()
	err = db.Connect(ctx, dbPath)
	require.NoError(t, err)
	
	cleanup := func() {
		db.Close()
		os.RemoveAll(tempDir)
	}
	
	return db, dbPath, cleanup
}

func TestSQLiteDB_SaveAndLoadFloorPlan(t *testing.T) {
	db, _, cleanup := setupTestDB(t)
	defer cleanup()
	
	ctx := context.Background()
	
	// Create test floor plan
	now := time.Now()
	plan := &models.FloorPlan{
		Name:      "TestFloor",
		Building:  "TestBuilding",
		Level:     3,
		CreatedAt: &now,
		UpdatedAt: &now,
		Rooms: []*models.Room{
			{
				ID:   "room1",
				Name: "Room 1",
				Bounds: models.Bounds{
					MinX: 0, MinY: 0,
					MaxX: 10, MaxY: 10,
				},
			},
			{
				ID:   "room2", 
				Name: "Room 2",
				Bounds: models.Bounds{
					MinX: 10, MinY: 0,
					MaxX: 20, MaxY: 10,
				},
			},
		},
		Equipment: []*models.Equipment{
			{
				ID:       "eq1",
				Name:     "Equipment 1",
				Type:     "outlet",
				RoomID:   "room1",
				Location: &models.Point{X: 5, Y: 5},
				Status:   models.StatusNormal,
			},
			{
				ID:       "eq2",
				Name:     "Equipment 2",
				Type:     "panel",
				RoomID:   "room2",
				Location: &models.Point{X: 15, Y: 5},
				Status:   models.StatusFailed,
				Notes:    "Needs inspection",
			},
		},
	}
	
	// Save floor plan
	err := db.SaveFloorPlan(ctx, plan)
	assert.NoError(t, err)
	assert.NotEmpty(t, plan.ID, "Floor plan should have an ID after saving")
	
	// Load floor plan using the generated ID
	loaded, err := db.GetFloorPlan(ctx, plan.ID)
	assert.NoError(t, err)
	assert.NotNil(t, loaded)
	
	// Verify basic properties
	assert.Equal(t, plan.Name, loaded.Name)
	assert.Equal(t, plan.Building, loaded.Building)
	assert.Equal(t, plan.Level, loaded.Level)
	
	// Verify rooms
	assert.Len(t, loaded.Rooms, 2)
	room1Found := false
	for _, room := range loaded.Rooms {
		if room.ID == "room1" {
			room1Found = true
			assert.Equal(t, "Room 1", room.Name)
			assert.Equal(t, 0.0, room.Bounds.MinX)
			assert.Equal(t, 10.0, room.Bounds.MaxX)
		}
	}
	assert.True(t, room1Found, "Room 1 not found")
	
	// Verify equipment
	assert.Len(t, loaded.Equipment, 2)
	eq2Found := false
	for _, eq := range loaded.Equipment {
		if eq.ID == "eq2" {
			eq2Found = true
			assert.Equal(t, "Equipment 2", eq.Name)
			assert.Equal(t, "panel", eq.Type)
			assert.Equal(t, "room2", eq.RoomID)
			assert.Equal(t, models.StatusFailed, eq.Status)
			assert.Equal(t, "Needs inspection", eq.Notes)
		}
	}
	assert.True(t, eq2Found, "Equipment 2 not found")
}

func TestSQLiteDB_UpdateFloorPlan(t *testing.T) {
	db, _, cleanup := setupTestDB(t)
	defer cleanup()
	
	ctx := context.Background()
	
	// Create and save initial floor plan
	plan := &models.FloorPlan{
		ID:       "UpdateTest",
		Name:     "UpdateTest",
		Building: "Building A",
		Level:    1,
		Rooms: []*models.Room{
			{
				ID:   "room1",
				Name: "Initial Room",
				Bounds: models.Bounds{
					MinX: 0, MinY: 0,
					MaxX: 5, MaxY: 5,
				},
			},
		},
	}
	
	err := db.SaveFloorPlan(ctx, plan)
	require.NoError(t, err)
	
	// Update the floor plan
	plan.Building = "Building B"
	plan.Level = 2
	plan.Rooms = []models.Room{
		{
			ID:   "room2",
			Name: "Updated Room",
			Bounds: models.Bounds{
				MinX: 0, MinY: 0,
				MaxX: 10, MaxY: 10,
			},
		},
	}
	plan.Equipment = []models.Equipment{
		{
			ID:       "new_eq",
			Name:     "New Equipment",
			Type:     "switch",
			RoomID:   "room2",
			Location: models.Point{X: 5, Y: 5},
			Status:   models.StatusNormal,
		},
	}
	
	err = db.UpdateFloorPlan(ctx, plan)
	assert.NoError(t, err)
	
	// Load and verify updates
	loaded, err := db.GetFloorPlan(ctx, plan.ID)
	require.NoError(t, err)
	
	assert.Equal(t, "Building B", loaded.Building)
	assert.Equal(t, 2, loaded.Level)
	assert.Len(t, loaded.Rooms, 1)
	assert.Equal(t, "room2", loaded.Rooms[0].ID)
	assert.Len(t, loaded.Equipment, 1)
	assert.Equal(t, "new_eq", loaded.Equipment[0].ID)
}

func TestSQLiteDB_ForeignKeyConstraints(t *testing.T) {
	db, _, cleanup := setupTestDB(t)
	defer cleanup()
	
	ctx := context.Background()
	
	// Test that equipment with invalid room_id is handled
	plan := &models.FloorPlan{
		ID:       "FKTest",
		Name:     "FKTest",
		Building: "Test",
		Level:    1,
		Rooms: []*models.Room{
			{
				ID:   "valid_room",
				Name: "Valid Room",
				Bounds: models.Bounds{
					MinX: 0, MinY: 0,
					MaxX: 10, MaxY: 10,
				},
			},
		},
		Equipment: []*models.Equipment{
			{
				ID:       "eq1",
				Name:     "Equipment with invalid room",
				Type:     "outlet",
				RoomID:   "non_existent_room", // This room doesn't exist
				Location: &models.Point{X: 5, Y: 5},
				Status:   models.StatusNormal,
			},
		},
	}
	
	// SaveFloorPlanFixed should handle this gracefully
	err := db.SaveFloorPlan(ctx, plan)
	assert.NoError(t, err)
	
	// Load and check that equipment room_id was set to empty
	loaded, err := db.GetFloorPlan(ctx, plan.ID)
	require.NoError(t, err)
	assert.Len(t, loaded.Equipment, 1)
	assert.Equal(t, "", loaded.Equipment[0].RoomID)
}

func TestValidateFloorPlan(t *testing.T) {
	tests := []struct {
		name        string
		plan        *models.FloorPlan
		expectError bool
		errorMsg    string
	}{
		{
			name:        "NilPlan",
			plan:        nil,
			expectError: true,
			errorMsg:    "floor plan is nil",
		},
		{
			name: "EmptyName",
			plan: &models.FloorPlan{
				ID:       "test-id",
				Building: "Test",
			},
			expectError: true,
			errorMsg:    "floor plan name is required",
		},
		{
			name: "EmptyBuilding",
			plan: &models.FloorPlan{
				ID:   "test-id",
				Name: "Test",
			},
			expectError: true,
			errorMsg:    "building name is required",
		},
		{
			name: "DuplicateRoomID",
			plan: &models.FloorPlan{
				ID:       "test-id",
				Name:     "Test",
				Building: "Test",
				Rooms: []*models.Room{
					{ID: "room1", Name: "Room 1"},
					{ID: "room1", Name: "Room 2"},
				},
			},
			expectError: true,
			errorMsg:    "duplicate room ID: room1",
		},
		{
			name: "DuplicateEquipmentID",
			plan: &models.FloorPlan{
				ID:       "test-id",
				Name:     "Test",
				Building: "Test",
				Equipment: []*models.Equipment{
					{ID: "eq1", Name: "Equipment 1"},
					{ID: "eq1", Name: "Equipment 2"},
				},
			},
			expectError: true,
			errorMsg:    "duplicate equipment ID: eq1",
		},
		{
			name: "InvalidRoomReference",
			plan: &models.FloorPlan{
				ID:       "test-id",
				Name:     "Test",
				Building: "Test",
				Rooms: []*models.Room{
					{ID: "room1", Name: "Room 1"},
				},
				Equipment: []*models.Equipment{
					{ID: "eq1", Name: "Equipment 1", RoomID: "invalid_room"},
				},
			},
			expectError: true,
			errorMsg:    "equipment eq1 references non-existent room invalid_room",
		},
		{
			name: "ValidPlan",
			plan: &models.FloorPlan{
				ID:       "test-id",
				Name:     "Test",
				Building: "Test",
				Rooms: []*models.Room{
					{ID: "room1", Name: "Room 1"},
				},
				Equipment: []*models.Equipment{
					{ID: "eq1", Name: "Equipment 1", RoomID: "room1"},
					{ID: "eq2", Name: "Equipment 2", RoomID: ""},
				},
			},
			expectError: false,
		},
	}
	
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			err := ValidateFloorPlan(tt.plan)
			if tt.expectError {
				assert.Error(t, err)
				assert.Contains(t, err.Error(), tt.errorMsg)
			} else {
				assert.NoError(t, err)
			}
		})
	}
}