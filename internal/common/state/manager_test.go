package state

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"testing"
	"time"

	"github.com/arx-os/arxos/pkg/models"
)

func TestNewManager(t *testing.T) {
	// Create temporary directory
	tmpDir := t.TempDir()

	manager, err := NewManager(tmpDir)
	if err != nil {
		t.Fatalf("NewManager failed: %v", err)
	}

	if manager == nil {
		t.Fatal("Manager is nil")
	}
	if manager.stateDir != tmpDir {
		t.Errorf("Expected stateDir=%s, got %s", tmpDir, manager.stateDir)
	}
	if manager.currentPlan != nil {
		t.Error("Expected currentPlan to be nil initially")
	}
	if manager.currentFile != "" {
		t.Error("Expected currentFile to be empty initially")
	}
	if manager.dirty {
		t.Error("Expected dirty to be false initially")
	}
}

func TestNewManager_CreateDirectory(t *testing.T) {
	// Test with non-existent directory
	tmpDir := filepath.Join(t.TempDir(), "non-existent", "subdir")

	manager, err := NewManager(tmpDir)
	if err != nil {
		t.Fatalf("NewManager failed: %v", err)
	}

	if manager.stateDir != tmpDir {
		t.Errorf("Expected stateDir=%s, got %s", tmpDir, manager.stateDir)
	}

	// Check that directory was created
	if _, err := os.Stat(tmpDir); os.IsNotExist(err) {
		t.Error("Directory was not created")
	}
}

func TestLoadFloorPlan_NonExistent(t *testing.T) {
	tmpDir := t.TempDir()
	manager, err := NewManager(tmpDir)
	if err != nil {
		t.Fatalf("NewManager failed: %v", err)
	}

	// Load non-existent file
	err = manager.LoadFloorPlan("non-existent.json")
	if err != nil {
		t.Fatalf("LoadFloorPlan failed: %v", err)
	}

	// Should create new floor plan
	if manager.currentPlan == nil {
		t.Fatal("Expected currentPlan to be created")
	}
	if manager.currentPlan.Name != "non-existent.json" {
		t.Errorf("Expected Name='non-existent.json', got '%s'", manager.currentPlan.Name)
	}
	if manager.currentPlan.Building != "Default Building" {
		t.Errorf("Expected Building='Default Building', got '%s'", manager.currentPlan.Building)
	}
	if manager.currentPlan.Level != 1 {
		t.Errorf("Expected Level=1, got %d", manager.currentPlan.Level)
	}
	if manager.currentFile != "non-existent.json" {
		t.Errorf("Expected currentFile='non-existent.json', got '%s'", manager.currentFile)
	}
	if manager.dirty {
		t.Error("Expected dirty to be false")
	}
}

func TestLoadFloorPlan_Existing(t *testing.T) {
	tmpDir := t.TempDir()
	manager, err := NewManager(tmpDir)
	if err != nil {
		t.Fatalf("NewManager failed: %v", err)
	}

	// Create test floor plan
	testPlan := &models.FloorPlan{
		Name:      "test-floor",
		Building:  "test-building",
		Level:     2,
		Rooms:     []*models.Room{},
		Equipment: []*models.Equipment{},
		CreatedAt: func() *time.Time { t := time.Now(); return &t }(),
		UpdatedAt: func() *time.Time { t := time.Now(); return &t }(),
	}

	// Save floor plan to file
	data, err := json.MarshalIndent(testPlan, "", "  ")
	if err != nil {
		t.Fatalf("Failed to marshal test plan: %v", err)
	}

	filePath := filepath.Join(tmpDir, "test-floor.json")
	err = os.WriteFile(filePath, data, 0644)
	if err != nil {
		t.Fatalf("Failed to write test file: %v", err)
	}

	// Load floor plan
	err = manager.LoadFloorPlan("test-floor.json")
	if err != nil {
		t.Fatalf("LoadFloorPlan failed: %v", err)
	}

	// Check loaded data
	if manager.currentPlan == nil {
		t.Fatal("Expected currentPlan to be loaded")
	}
	if manager.currentPlan.Name != "test-floor" {
		t.Errorf("Expected Name='test-floor', got '%s'", manager.currentPlan.Name)
	}
	if manager.currentPlan.Building != "test-building" {
		t.Errorf("Expected Building='test-building', got '%s'", manager.currentPlan.Building)
	}
	if manager.currentPlan.Level != 2 {
		t.Errorf("Expected Level=2, got %d", manager.currentPlan.Level)
	}
	if manager.currentFile != "test-floor.json" {
		t.Errorf("Expected currentFile='test-floor.json', got '%s'", manager.currentFile)
	}
	if manager.dirty {
		t.Error("Expected dirty to be false")
	}
}

func TestLoadFloorPlan_InvalidJSON(t *testing.T) {
	tmpDir := t.TempDir()
	manager, err := NewManager(tmpDir)
	if err != nil {
		t.Fatalf("NewManager failed: %v", err)
	}

	// Create invalid JSON file
	filePath := filepath.Join(tmpDir, "invalid.json")
	err = os.WriteFile(filePath, []byte("invalid json"), 0644)
	if err != nil {
		t.Fatalf("Failed to write invalid file: %v", err)
	}

	// Load invalid file
	err = manager.LoadFloorPlan("invalid.json")
	if err == nil {
		t.Error("Expected error for invalid JSON")
	}
	if !strings.Contains(err.Error(), "failed to parse floor plan") {
		t.Errorf("Expected parse error, got: %v", err)
	}
}

func TestSaveFloorPlan_NoPlan(t *testing.T) {
	tmpDir := t.TempDir()
	manager, err := NewManager(tmpDir)
	if err != nil {
		t.Fatalf("NewManager failed: %v", err)
	}

	// Try to save without loading a plan
	err = manager.SaveFloorPlan()
	if err == nil {
		t.Error("Expected error when saving without plan")
	}
	if !strings.Contains(err.Error(), "no floor plan loaded") {
		t.Errorf("Expected 'no floor plan loaded' error, got: %v", err)
	}
}

func TestSaveFloorPlan_NoFile(t *testing.T) {
	tmpDir := t.TempDir()
	manager, err := NewManager(tmpDir)
	if err != nil {
		t.Fatalf("NewManager failed: %v", err)
	}

	// Set plan but no file
	manager.SetFloorPlan(&models.FloorPlan{
		Name:      "test",
		Building:  "test",
		Level:     1,
		Rooms:     []*models.Room{},
		Equipment: []*models.Equipment{},
	})

	// Try to save without file
	err = manager.SaveFloorPlan()
	if err == nil {
		t.Error("Expected error when saving without file")
	}
	if !strings.Contains(err.Error(), "no file specified") {
		t.Errorf("Expected 'no file specified' error, got: %v", err)
	}
}

func TestSaveFloorPlan_Success(t *testing.T) {
	tmpDir := t.TempDir()
	manager, err := NewManager(tmpDir)
	if err != nil {
		t.Fatalf("NewManager failed: %v", err)
	}

	// Load a plan (creates new one)
	err = manager.LoadFloorPlan("test-save.json")
	if err != nil {
		t.Fatalf("LoadFloorPlan failed: %v", err)
	}

	// Modify the plan
	manager.currentPlan.Building = "modified-building"
	manager.dirty = true

	// Save the plan
	err = manager.SaveFloorPlan()
	if err != nil {
		t.Fatalf("SaveFloorPlan failed: %v", err)
	}

	// Check that file was created
	filePath := filepath.Join(tmpDir, "test-save.json")
	if _, err := os.Stat(filePath); os.IsNotExist(err) {
		t.Error("File was not created")
	}

	// Check that dirty flag is cleared
	if manager.dirty {
		t.Error("Expected dirty to be false after save")
	}

	// Verify file contents
	data, err := os.ReadFile(filePath)
	if err != nil {
		t.Fatalf("Failed to read saved file: %v", err)
	}

	var savedPlan models.FloorPlan
	err = json.Unmarshal(data, &savedPlan)
	if err != nil {
		t.Fatalf("Failed to unmarshal saved file: %v", err)
	}

	if savedPlan.Building != "modified-building" {
		t.Errorf("Expected Building='modified-building', got '%s'", savedPlan.Building)
	}
}

func TestGetFloorPlan(t *testing.T) {
	tmpDir := t.TempDir()
	manager, err := NewManager(tmpDir)
	if err != nil {
		t.Fatalf("NewManager failed: %v", err)
	}

	// Initially should return nil
	plan := manager.GetFloorPlan()
	if plan != nil {
		t.Error("Expected nil plan initially")
	}

	// Load a plan
	err = manager.LoadFloorPlan("test.json")
	if err != nil {
		t.Fatalf("LoadFloorPlan failed: %v", err)
	}

	// Should return the loaded plan
	plan = manager.GetFloorPlan()
	if plan == nil {
		t.Fatal("Expected non-nil plan after load")
	}
	if plan.Name != "test.json" {
		t.Errorf("Expected Name='test.json', got '%s'", plan.Name)
	}
}

func TestSetFloorPlan(t *testing.T) {
	tmpDir := t.TempDir()
	manager, err := NewManager(tmpDir)
	if err != nil {
		t.Fatalf("NewManager failed: %v", err)
	}

	testPlan := &models.FloorPlan{
		Name:      "test-plan",
		Building:  "test-building",
		Level:     3,
		Rooms:     []*models.Room{},
		Equipment: []*models.Equipment{},
	}

	manager.SetFloorPlan(testPlan)

	// Check that plan was set
	if manager.currentPlan != testPlan {
		t.Error("Plan was not set correctly")
	}
	if !manager.dirty {
		t.Error("Expected dirty to be true after setting plan")
	}
}

func TestMarkEquipment_NoPlan(t *testing.T) {
	tmpDir := t.TempDir()
	manager, err := NewManager(tmpDir)
	if err != nil {
		t.Fatalf("NewManager failed: %v", err)
	}

	// Try to mark equipment without plan
	err = manager.MarkEquipment("eq1", "failed", "test notes", "user1")
	if err == nil {
		t.Error("Expected error when marking equipment without plan")
	}
	if !strings.Contains(err.Error(), "no floor plan loaded") {
		t.Errorf("Expected 'no floor plan loaded' error, got: %v", err)
	}
}

func TestMarkEquipment_NotFound(t *testing.T) {
	tmpDir := t.TempDir()
	manager, err := NewManager(tmpDir)
	if err != nil {
		t.Fatalf("NewManager failed: %v", err)
	}

	// Load a plan
	err = manager.LoadFloorPlan("test.json")
	if err != nil {
		t.Fatalf("LoadFloorPlan failed: %v", err)
	}

	// Try to mark non-existent equipment
	err = manager.MarkEquipment("non-existent", "failed", "test notes", "user1")
	if err == nil {
		t.Error("Expected error when marking non-existent equipment")
	}
	if !strings.Contains(err.Error(), "equipment not found") {
		t.Errorf("Expected 'equipment not found' error, got: %v", err)
	}
}

func TestMarkEquipment_Success(t *testing.T) {
	tmpDir := t.TempDir()
	manager, err := NewManager(tmpDir)
	if err != nil {
		t.Fatalf("NewManager failed: %v", err)
	}

	// Load a plan
	err = manager.LoadFloorPlan("test.json")
	if err != nil {
		t.Fatalf("LoadFloorPlan failed: %v", err)
	}

	// Add equipment
	err = manager.AddEquipment("Test Equipment", "HVAC", "", 10.5, 20.3, "test notes")
	if err != nil {
		t.Fatalf("AddEquipment failed: %v", err)
	}

	// Mark equipment
	err = manager.MarkEquipment("test_equipment", "failed", "marked as failed", "user1")
	if err != nil {
		t.Fatalf("MarkEquipment failed: %v", err)
	}

	// Check that equipment was marked
	equipment := manager.currentPlan.Equipment[0]
	if equipment.Status != "failed" {
		t.Errorf("Expected Status='failed', got '%s'", equipment.Status)
	}
	if equipment.Notes != "marked as failed" {
		t.Errorf("Expected Notes='marked as failed', got '%s'", equipment.Notes)
	}
	if equipment.MarkedBy != "user1" {
		t.Errorf("Expected MarkedBy='user1', got '%s'", equipment.MarkedBy)
	}
	if equipment.MarkedAt == nil {
		t.Error("Expected MarkedAt to be set")
	}
	if !manager.dirty {
		t.Error("Expected dirty to be true after marking equipment")
	}
}

func TestMarkEquipment_CaseInsensitive(t *testing.T) {
	tmpDir := t.TempDir()
	manager, err := NewManager(tmpDir)
	if err != nil {
		t.Fatalf("NewManager failed: %v", err)
	}

	// Load a plan
	err = manager.LoadFloorPlan("test.json")
	if err != nil {
		t.Fatalf("LoadFloorPlan failed: %v", err)
	}

	// Add equipment
	err = manager.AddEquipment("Test Equipment", "HVAC", "", 10.5, 20.3, "")
	if err != nil {
		t.Fatalf("AddEquipment failed: %v", err)
	}

	// Mark equipment with different case
	err = manager.MarkEquipment("TEST_EQUIPMENT", "failed", "", "user1")
	if err != nil {
		t.Fatalf("MarkEquipment failed: %v", err)
	}

	// Check that equipment was found and marked
	equipment := manager.currentPlan.Equipment[0]
	if equipment.Status != "failed" {
		t.Errorf("Expected Status='failed', got '%s'", equipment.Status)
	}
}

func TestAddEquipment_NoPlan(t *testing.T) {
	tmpDir := t.TempDir()
	manager, err := NewManager(tmpDir)
	if err != nil {
		t.Fatalf("NewManager failed: %v", err)
	}

	// Try to add equipment without plan
	err = manager.AddEquipment("Test Equipment", "HVAC", "", 10.5, 20.3, "")
	if err == nil {
		t.Error("Expected error when adding equipment without plan")
	}
	if !strings.Contains(err.Error(), "no floor plan loaded") {
		t.Errorf("Expected 'no floor plan loaded' error, got: %v", err)
	}
}

func TestAddEquipment_Success(t *testing.T) {
	tmpDir := t.TempDir()
	manager, err := NewManager(tmpDir)
	if err != nil {
		t.Fatalf("NewManager failed: %v", err)
	}

	// Load a plan
	err = manager.LoadFloorPlan("test.json")
	if err != nil {
		t.Fatalf("LoadFloorPlan failed: %v", err)
	}

	// Add equipment
	err = manager.AddEquipment("Test Equipment", "HVAC", "", 10.5, 20.3, "test notes")
	if err != nil {
		t.Fatalf("AddEquipment failed: %v", err)
	}

	// Check that equipment was added
	if len(manager.currentPlan.Equipment) != 1 {
		t.Errorf("Expected 1 equipment, got %d", len(manager.currentPlan.Equipment))
	}

	equipment := manager.currentPlan.Equipment[0]
	if equipment.ID != "test_equipment" {
		t.Errorf("Expected ID='test_equipment', got '%s'", equipment.ID)
	}
	if equipment.Name != "Test Equipment" {
		t.Errorf("Expected Name='Test Equipment', got '%s'", equipment.Name)
	}
	if equipment.Type != "HVAC" {
		t.Errorf("Expected Type='HVAC', got '%s'", equipment.Type)
	}
	if equipment.Location.X != 10.5 {
		t.Errorf("Expected Location.X=10.5, got %f", equipment.Location.X)
	}
	if equipment.Location.Y != 20.3 {
		t.Errorf("Expected Location.Y=20.3, got %f", equipment.Location.Y)
	}
	if equipment.Notes != "test notes" {
		t.Errorf("Expected Notes='test notes', got '%s'", equipment.Notes)
	}
	if equipment.Status != models.StatusOperational {
		t.Errorf("Expected Status='%s', got '%s'", models.StatusOperational, equipment.Status)
	}
	if !manager.dirty {
		t.Error("Expected dirty to be true after adding equipment")
	}
}

func TestAddEquipment_DuplicateID(t *testing.T) {
	tmpDir := t.TempDir()
	manager, err := NewManager(tmpDir)
	if err != nil {
		t.Fatalf("NewManager failed: %v", err)
	}

	// Load a plan
	err = manager.LoadFloorPlan("test.json")
	if err != nil {
		t.Fatalf("LoadFloorPlan failed: %v", err)
	}

	// Add first equipment
	err = manager.AddEquipment("Test Equipment", "HVAC", "", 10.5, 20.3, "")
	if err != nil {
		t.Fatalf("AddEquipment failed: %v", err)
	}

	// Try to add equipment with same name (generates same ID)
	err = manager.AddEquipment("Test Equipment", "Lighting", "", 15.0, 25.0, "")
	if err == nil {
		t.Error("Expected error when adding duplicate equipment")
	}
	if !strings.Contains(err.Error(), "already exists") {
		t.Errorf("Expected 'already exists' error, got: %v", err)
	}
}

func TestAddEquipment_WithRoom(t *testing.T) {
	tmpDir := t.TempDir()
	manager, err := NewManager(tmpDir)
	if err != nil {
		t.Fatalf("NewManager failed: %v", err)
	}

	// Load a plan
	err = manager.LoadFloorPlan("test.json")
	if err != nil {
		t.Fatalf("LoadFloorPlan failed: %v", err)
	}

	// Create a room first
	err = manager.CreateRoom("Test Room", 0, 0, 100, 100)
	if err != nil {
		t.Fatalf("CreateRoom failed: %v", err)
	}

	// Add equipment to room
	err = manager.AddEquipment("Test Equipment", "HVAC", "test_room", 10.5, 20.3, "")
	if err != nil {
		t.Fatalf("AddEquipment failed: %v", err)
	}

	// Check that equipment was added to room
	room := manager.currentPlan.Rooms[0]
	if len(room.Equipment) != 1 {
		t.Errorf("Expected 1 equipment in room, got %d", len(room.Equipment))
	}
	if room.Equipment[0] != "test_equipment" {
		t.Errorf("Expected room equipment ID='test_equipment', got '%s'", room.Equipment[0])
	}

	// Check that equipment has room ID
	equipment := manager.currentPlan.Equipment[0]
	if equipment.RoomID != "test_room" {
		t.Errorf("Expected RoomID='test_room', got '%s'", equipment.RoomID)
	}
}

func TestAddEquipment_RoomNotFound(t *testing.T) {
	tmpDir := t.TempDir()
	manager, err := NewManager(tmpDir)
	if err != nil {
		t.Fatalf("NewManager failed: %v", err)
	}

	// Load a plan
	err = manager.LoadFloorPlan("test.json")
	if err != nil {
		t.Fatalf("LoadFloorPlan failed: %v", err)
	}

	// Try to add equipment to non-existent room
	err = manager.AddEquipment("Test Equipment", "HVAC", "non-existent-room", 10.5, 20.3, "")
	if err == nil {
		t.Error("Expected error when adding equipment to non-existent room")
	}
	if !strings.Contains(err.Error(), "room not found") {
		t.Errorf("Expected 'room not found' error, got: %v", err)
	}
}

func TestRemoveEquipment_NoPlan(t *testing.T) {
	tmpDir := t.TempDir()
	manager, err := NewManager(tmpDir)
	if err != nil {
		t.Fatalf("NewManager failed: %v", err)
	}

	// Try to remove equipment without plan
	err = manager.RemoveEquipment("eq1")
	if err == nil {
		t.Error("Expected error when removing equipment without plan")
	}
	if !strings.Contains(err.Error(), "no floor plan loaded") {
		t.Errorf("Expected 'no floor plan loaded' error, got: %v", err)
	}
}

func TestRemoveEquipment_NotFound(t *testing.T) {
	tmpDir := t.TempDir()
	manager, err := NewManager(tmpDir)
	if err != nil {
		t.Fatalf("NewManager failed: %v", err)
	}

	// Load a plan
	err = manager.LoadFloorPlan("test.json")
	if err != nil {
		t.Fatalf("LoadFloorPlan failed: %v", err)
	}

	// Try to remove non-existent equipment
	err = manager.RemoveEquipment("non-existent")
	if err == nil {
		t.Error("Expected error when removing non-existent equipment")
	}
	if !strings.Contains(err.Error(), "not found") {
		t.Errorf("Expected 'not found' error, got: %v", err)
	}
}

func TestRemoveEquipment_Success(t *testing.T) {
	tmpDir := t.TempDir()
	manager, err := NewManager(tmpDir)
	if err != nil {
		t.Fatalf("NewManager failed: %v", err)
	}

	// Load a plan
	err = manager.LoadFloorPlan("test.json")
	if err != nil {
		t.Fatalf("LoadFloorPlan failed: %v", err)
	}

	// Add equipment
	err = manager.AddEquipment("Test Equipment", "HVAC", "", 10.5, 20.3, "")
	if err != nil {
		t.Fatalf("AddEquipment failed: %v", err)
	}

	// Remove equipment
	err = manager.RemoveEquipment("test_equipment")
	if err != nil {
		t.Fatalf("RemoveEquipment failed: %v", err)
	}

	// Check that equipment was removed
	if len(manager.currentPlan.Equipment) != 0 {
		t.Errorf("Expected 0 equipment, got %d", len(manager.currentPlan.Equipment))
	}
	if !manager.dirty {
		t.Error("Expected dirty to be true after removing equipment")
	}
}

func TestRemoveEquipment_FromRoom(t *testing.T) {
	tmpDir := t.TempDir()
	manager, err := NewManager(tmpDir)
	if err != nil {
		t.Fatalf("NewManager failed: %v", err)
	}

	// Load a plan
	err = manager.LoadFloorPlan("test.json")
	if err != nil {
		t.Fatalf("LoadFloorPlan failed: %v", err)
	}

	// Create a room
	err = manager.CreateRoom("Test Room", 0, 0, 100, 100)
	if err != nil {
		t.Fatalf("CreateRoom failed: %v", err)
	}

	// Add equipment to room
	err = manager.AddEquipment("Test Equipment", "HVAC", "test_room", 10.5, 20.3, "")
	if err != nil {
		t.Fatalf("AddEquipment failed: %v", err)
	}

	// Remove equipment
	err = manager.RemoveEquipment("test_equipment")
	if err != nil {
		t.Fatalf("RemoveEquipment failed: %v", err)
	}

	// Check that equipment was removed from room
	room := manager.currentPlan.Rooms[0]
	if len(room.Equipment) != 0 {
		t.Errorf("Expected 0 equipment in room, got %d", len(room.Equipment))
	}
}

func TestCreateRoom_NoPlan(t *testing.T) {
	tmpDir := t.TempDir()
	manager, err := NewManager(tmpDir)
	if err != nil {
		t.Fatalf("NewManager failed: %v", err)
	}

	// Try to create room without plan
	err = manager.CreateRoom("Test Room", 0, 0, 100, 100)
	if err == nil {
		t.Error("Expected error when creating room without plan")
	}
	if !strings.Contains(err.Error(), "no floor plan loaded") {
		t.Errorf("Expected 'no floor plan loaded' error, got: %v", err)
	}
}

func TestCreateRoom_Success(t *testing.T) {
	tmpDir := t.TempDir()
	manager, err := NewManager(tmpDir)
	if err != nil {
		t.Fatalf("NewManager failed: %v", err)
	}

	// Load a plan
	err = manager.LoadFloorPlan("test.json")
	if err != nil {
		t.Fatalf("LoadFloorPlan failed: %v", err)
	}

	// Create room
	err = manager.CreateRoom("Test Room", 0, 0, 100, 100)
	if err != nil {
		t.Fatalf("CreateRoom failed: %v", err)
	}

	// Check that room was created
	if len(manager.currentPlan.Rooms) != 1 {
		t.Errorf("Expected 1 room, got %d", len(manager.currentPlan.Rooms))
	}

	room := manager.currentPlan.Rooms[0]
	if room.ID != "test_room" {
		t.Errorf("Expected ID='test_room', got '%s'", room.ID)
	}
	if room.Name != "Test Room" {
		t.Errorf("Expected Name='Test Room', got '%s'", room.Name)
	}
	if room.Bounds.MinX != 0 {
		t.Errorf("Expected Bounds.MinX=0, got %f", room.Bounds.MinX)
	}
	if room.Bounds.MinY != 0 {
		t.Errorf("Expected Bounds.MinY=0, got %f", room.Bounds.MinY)
	}
	if room.Bounds.MaxX != 100 {
		t.Errorf("Expected Bounds.MaxX=100, got %f", room.Bounds.MaxX)
	}
	if room.Bounds.MaxY != 100 {
		t.Errorf("Expected Bounds.MaxY=100, got %f", room.Bounds.MaxY)
	}
	if len(room.Equipment) != 0 {
		t.Errorf("Expected 0 equipment in room, got %d", len(room.Equipment))
	}
	if !manager.dirty {
		t.Error("Expected dirty to be true after creating room")
	}
}

func TestCreateRoom_DuplicateID(t *testing.T) {
	tmpDir := t.TempDir()
	manager, err := NewManager(tmpDir)
	if err != nil {
		t.Fatalf("NewManager failed: %v", err)
	}

	// Load a plan
	err = manager.LoadFloorPlan("test.json")
	if err != nil {
		t.Fatalf("LoadFloorPlan failed: %v", err)
	}

	// Create first room
	err = manager.CreateRoom("Test Room", 0, 0, 100, 100)
	if err != nil {
		t.Fatalf("CreateRoom failed: %v", err)
	}

	// Try to create room with same name (generates same ID)
	err = manager.CreateRoom("Test Room", 200, 200, 300, 300)
	if err == nil {
		t.Error("Expected error when creating duplicate room")
	}
	if !strings.Contains(err.Error(), "already exists") {
		t.Errorf("Expected 'already exists' error, got: %v", err)
	}
}

func TestFindEquipment(t *testing.T) {
	tmpDir := t.TempDir()
	manager, err := NewManager(tmpDir)
	if err != nil {
		t.Fatalf("NewManager failed: %v", err)
	}

	// Load a plan
	err = manager.LoadFloorPlan("test.json")
	if err != nil {
		t.Fatalf("LoadFloorPlan failed: %v", err)
	}

	// Add equipment
	err = manager.AddEquipment("HVAC Unit", "HVAC", "", 10.5, 20.3, "")
	if err != nil {
		t.Fatalf("AddEquipment failed: %v", err)
	}

	// Find by ID
	results := manager.FindEquipment("hvac_unit")
	if len(results) != 1 {
		t.Errorf("Expected 1 result for ID search, got %d", len(results))
	}

	// Find by name
	results = manager.FindEquipment("HVAC Unit")
	if len(results) != 1 {
		t.Errorf("Expected 1 result for name search, got %d", len(results))
	}

	// Find by type
	results = manager.FindEquipment("HVAC")
	if len(results) != 1 {
		t.Errorf("Expected 1 result for type search, got %d", len(results))
	}

	// Find non-existent
	results = manager.FindEquipment("non-existent")
	if len(results) != 0 {
		t.Errorf("Expected 0 results for non-existent search, got %d", len(results))
	}
}

func TestFindEquipment_NoPlan(t *testing.T) {
	tmpDir := t.TempDir()
	manager, err := NewManager(tmpDir)
	if err != nil {
		t.Fatalf("NewManager failed: %v", err)
	}

	// Find equipment without plan
	results := manager.FindEquipment("test")
	if results != nil {
		t.Error("Expected nil results when no plan loaded")
	}
}

func TestGetEquipmentByStatus(t *testing.T) {
	tmpDir := t.TempDir()
	manager, err := NewManager(tmpDir)
	if err != nil {
		t.Fatalf("NewManager failed: %v", err)
	}

	// Load a plan
	err = manager.LoadFloorPlan("test.json")
	if err != nil {
		t.Fatalf("LoadFloorPlan failed: %v", err)
	}

	// Add equipment
	err = manager.AddEquipment("HVAC Unit", "HVAC", "", 10.5, 20.3, "")
	if err != nil {
		t.Fatalf("AddEquipment failed: %v", err)
	}

	// Mark equipment as failed
	err = manager.MarkEquipment("hvac_unit", "failed", "", "user1")
	if err != nil {
		t.Fatalf("MarkEquipment failed: %v", err)
	}

	// Get equipment by status
	results := manager.GetEquipmentByStatus("failed")
	if len(results) != 1 {
		t.Errorf("Expected 1 failed equipment, got %d", len(results))
	}

	results = manager.GetEquipmentByStatus("operational")
	if len(results) != 0 {
		t.Errorf("Expected 0 operational equipment, got %d", len(results))
	}
}

func TestGetEquipmentByStatus_NoPlan(t *testing.T) {
	tmpDir := t.TempDir()
	manager, err := NewManager(tmpDir)
	if err != nil {
		t.Fatalf("NewManager failed: %v", err)
	}

	// Get equipment by status without plan
	results := manager.GetEquipmentByStatus("operational")
	if results != nil {
		t.Error("Expected nil results when no plan loaded")
	}
}

func TestGetRoom(t *testing.T) {
	tmpDir := t.TempDir()
	manager, err := NewManager(tmpDir)
	if err != nil {
		t.Fatalf("NewManager failed: %v", err)
	}

	// Load a plan
	err = manager.LoadFloorPlan("test.json")
	if err != nil {
		t.Fatalf("LoadFloorPlan failed: %v", err)
	}

	// Create room
	err = manager.CreateRoom("Test Room", 0, 0, 100, 100)
	if err != nil {
		t.Fatalf("CreateRoom failed: %v", err)
	}

	// Get room by ID
	room := manager.GetRoom("test_room")
	if room == nil {
		t.Fatal("Expected room to be found by ID")
	}
	if room.Name != "Test Room" {
		t.Errorf("Expected Name='Test Room', got '%s'", room.Name)
	}

	// Get room by name
	room = manager.GetRoom("Test Room")
	if room == nil {
		t.Fatal("Expected room to be found by name")
	}
	if room.ID != "test_room" {
		t.Errorf("Expected ID='test_room', got '%s'", room.ID)
	}

	// Get non-existent room
	room = manager.GetRoom("non-existent")
	if room != nil {
		t.Error("Expected nil for non-existent room")
	}
}

func TestGetRoom_NoPlan(t *testing.T) {
	tmpDir := t.TempDir()
	manager, err := NewManager(tmpDir)
	if err != nil {
		t.Fatalf("NewManager failed: %v", err)
	}

	// Get room without plan
	room := manager.GetRoom("test")
	if room != nil {
		t.Error("Expected nil room when no plan loaded")
	}
}

func TestIsDirty(t *testing.T) {
	tmpDir := t.TempDir()
	manager, err := NewManager(tmpDir)
	if err != nil {
		t.Fatalf("NewManager failed: %v", err)
	}

	// Initially should not be dirty
	if manager.IsDirty() {
		t.Error("Expected not dirty initially")
	}

	// Load a plan
	err = manager.LoadFloorPlan("test.json")
	if err != nil {
		t.Fatalf("LoadFloorPlan failed: %v", err)
	}

	// Should not be dirty after load
	if manager.IsDirty() {
		t.Error("Expected not dirty after load")
	}

	// Set plan should make it dirty
	manager.SetFloorPlan(&models.FloorPlan{
		Name:      "test",
		Building:  "test",
		Level:     1,
		Rooms:     []*models.Room{},
		Equipment: []*models.Equipment{},
	})

	if !manager.IsDirty() {
		t.Error("Expected dirty after setting plan")
	}
}

func TestListFloorPlans(t *testing.T) {
	tmpDir := t.TempDir()
	manager, err := NewManager(tmpDir)
	if err != nil {
		t.Fatalf("NewManager failed: %v", err)
	}

	// Initially should be empty
	plans, err := manager.ListFloorPlans()
	if err != nil {
		t.Fatalf("ListFloorPlans failed: %v", err)
	}
	if len(plans) != 0 {
		t.Errorf("Expected 0 plans initially, got %d", len(plans))
	}

	// Create some test files
	testFiles := []string{"plan1.json", "plan2.json", "not-a-plan.txt"}
	for _, filename := range testFiles {
		filePath := filepath.Join(tmpDir, filename)
		err = os.WriteFile(filePath, []byte("{}"), 0644)
		if err != nil {
			t.Fatalf("Failed to create test file %s: %v", filename, err)
		}
	}

	// List floor plans
	plans, err = manager.ListFloorPlans()
	if err != nil {
		t.Fatalf("ListFloorPlans failed: %v", err)
	}
	if len(plans) != 2 {
		t.Errorf("Expected 2 plans, got %d", len(plans))
	}

	// Check that only JSON files are included
	for _, plan := range plans {
		if !strings.HasSuffix(plan, ".json") {
			t.Errorf("Expected only JSON files, got: %s", plan)
		}
	}
}

func TestExportForGit_NoPlan(t *testing.T) {
	tmpDir := t.TempDir()
	manager, err := NewManager(tmpDir)
	if err != nil {
		t.Fatalf("NewManager failed: %v", err)
	}

	// Try to export without plan
	_, err = manager.ExportForGit()
	if err == nil {
		t.Error("Expected error when exporting without plan")
	}
	if !strings.Contains(err.Error(), "no floor plan loaded") {
		t.Errorf("Expected 'no floor plan loaded' error, got: %v", err)
	}
}

func TestExportForGit_Success(t *testing.T) {
	tmpDir := t.TempDir()
	manager, err := NewManager(tmpDir)
	if err != nil {
		t.Fatalf("NewManager failed: %v", err)
	}

	// Load a plan
	err = manager.LoadFloorPlan("test.json")
	if err != nil {
		t.Fatalf("LoadFloorPlan failed: %v", err)
	}

	// Add some equipment with different statuses
	err = manager.AddEquipment("HVAC Unit", "HVAC", "", 10.5, 20.3, "")
	if err != nil {
		t.Fatalf("AddEquipment failed: %v", err)
	}

	err = manager.AddEquipment("Lighting", "Lighting", "", 15.0, 25.0, "")
	if err != nil {
		t.Fatalf("AddEquipment failed: %v", err)
	}

	// Mark equipment with different statuses
	err = manager.MarkEquipment("hvac_unit", "FAILED", "", "user1")
	if err != nil {
		t.Fatalf("MarkEquipment failed: %v", err)
	}

	err = manager.MarkEquipment("lighting", "DEGRADED", "", "user1")
	if err != nil {
		t.Fatalf("MarkEquipment failed: %v", err)
	}

	// Export for Git
	export, err := manager.ExportForGit()
	if err != nil {
		t.Fatalf("ExportForGit failed: %v", err)
	}

	// Check export structure
	if export["building"] != "Default Building" {
		t.Errorf("Expected building='Default Building', got '%v'", export["building"])
	}
	if export["floor"] != "test.json" {
		t.Errorf("Expected floor='test.json', got '%v'", export["floor"])
	}
	if export["level"] != 1 {
		t.Errorf("Expected level=1, got '%v'", export["level"])
	}

	// Check summary
	summary, ok := export["summary"].(map[string]int)
	if !ok {
		t.Fatal("Expected summary to be map[string]int")
	}
	if summary["total_rooms"] != 0 {
		t.Errorf("Expected total_rooms=0, got %d", summary["total_rooms"])
	}
	if summary["total_equipment"] != 2 {
		t.Errorf("Expected total_equipment=2, got %d", summary["total_equipment"])
	}
	if summary["needs_repair"] != 1 {
		t.Errorf("Expected needs_repair=1, got %d", summary["needs_repair"])
	}
	if summary["failed"] != 1 {
		t.Errorf("Expected failed=1, got %d", summary["failed"])
	}

	// Check changes
	changes, ok := export["changes"].([]string)
	if !ok {
		t.Fatal("Expected changes to be []string")
	}
	if len(changes) != 0 {
		t.Errorf("Expected 0 changes, got %d", len(changes))
	}

	// Verify export was created successfully
	if export == nil {
		t.Error("Export should not be nil")
	}

	// Verify export structure is complete
	if len(export) == 0 {
		t.Error("Export should contain data")
	}
}

// Benchmark tests
func BenchmarkLoadFloorPlan(b *testing.B) {
	tmpDir := b.TempDir()
	manager, err := NewManager(tmpDir)
	if err != nil {
		b.Fatalf("NewManager failed: %v", err)
	}

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		manager.LoadFloorPlan("benchmark.json")
	}
}

func BenchmarkSaveFloorPlan(b *testing.B) {
	tmpDir := b.TempDir()
	manager, err := NewManager(tmpDir)
	if err != nil {
		b.Fatalf("NewManager failed: %v", err)
	}

	// Load a plan
	err = manager.LoadFloorPlan("benchmark.json")
	if err != nil {
		b.Fatalf("LoadFloorPlan failed: %v", err)
	}

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		manager.SaveFloorPlan()
	}
}

func BenchmarkAddEquipment(b *testing.B) {
	tmpDir := b.TempDir()
	manager, err := NewManager(tmpDir)
	if err != nil {
		b.Fatalf("NewManager failed: %v", err)
	}

	// Load a plan
	err = manager.LoadFloorPlan("benchmark.json")
	if err != nil {
		b.Fatalf("LoadFloorPlan failed: %v", err)
	}

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		manager.AddEquipment(fmt.Sprintf("Equipment %d", i), "HVAC", "", float64(i), float64(i), "")
	}
}

func BenchmarkFindEquipment(b *testing.B) {
	tmpDir := b.TempDir()
	manager, err := NewManager(tmpDir)
	if err != nil {
		b.Fatalf("NewManager failed: %v", err)
	}

	// Load a plan
	err = manager.LoadFloorPlan("benchmark.json")
	if err != nil {
		b.Fatalf("LoadFloorPlan failed: %v", err)
	}

	// Add equipment
	err = manager.AddEquipment("Test Equipment", "HVAC", "", 10.5, 20.3, "")
	if err != nil {
		b.Fatalf("AddEquipment failed: %v", err)
	}

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		manager.FindEquipment("test_equipment")
	}
}
