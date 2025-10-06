package models

import (
	"testing"
	"time"
)

func TestBuildingManager(t *testing.T) {
	bm := NewBuildingManager()

	// Create a test building
	building := &EnhancedBuilding{
		ID:           "building-001",
		UUID:         "550e8400-e29b-41d4-a716-446655440000",
		Name:         "Test Building",
		Description:  "A test building for unit tests",
		Address:      "123 Test Street",
		BuildingType: BuildingTypeOffice,
		Status:       BuildingStatusActive,
		Floors:       []FloorPlan{},
		Systems:      []string{},
		Source:       "manual",
		Confidence:   ConfidenceMedium,
		ImportedAt:   time.Now(),
		UpdatedAt:    time.Now(),
		Properties:   map[string]any{"test": true},
		Coverage:     75.5,
	}

	// Test building validation
	issues := bm.ValidateBuilding(building)
	if len(issues) != 1 {
		t.Errorf("Expected 1 validation issue (no floors warning), got %d", len(issues))
		for _, issue := range issues {
			t.Logf("Issue: %s - %s", issue.Level, issue.Message)
		}
	}

	// Test building stats calculation
	stats := bm.CalculateBuildingStats(building)
	if stats.TotalBuildings != 1 {
		t.Errorf("Expected TotalBuildings 1, got %d", stats.TotalBuildings)
	}
	if stats.ActiveBuildings != 1 {
		t.Errorf("Expected ActiveBuildings 1, got %d", stats.ActiveBuildings)
	}

	// Test adding floors
	floor1 := FloorPlan{
		ID:          "floor-001",
		Level:       1,
		Name:        "Ground Floor",
		Description: "Ground level floor",
		Rooms:       []*Room{},
		Equipment:   []*Equipment{},
		Metadata:    map[string]any{},
	}

	err := bm.AddFloor(building, floor1)
	if err != nil {
		t.Fatalf("Failed to add floor: %v", err)
	}

	if len(building.Floors) != 1 {
		t.Errorf("Expected 1 floor, got %d", len(building.Floors))
	}

	// Test adding equipment
	equipment1 := Equipment{
		ID:       "equipment-001",
		Name:     "Main HVAC Unit",
		Type:     "hvac",
		Path:     "N/3/A/301/E",
		Location: &Point3D{X: 1000, Y: 2000, Z: 0},
		Status:   StatusOperational,
		Model:    "TC-HVAC-1000",
		Metadata: map[string]any{},
	}

	err = bm.AddEquipment(building, 1, equipment1)
	if err != nil {
		t.Fatalf("Failed to add equipment: %v", err)
	}

	floor := bm.GetFloorByNumber(building, 1)
	if floor == nil {
		t.Fatal("Floor not found")
	}

	if len(floor.Equipment) != 1 {
		t.Errorf("Expected 1 equipment, got %d", len(floor.Equipment))
	}

	// Test getting equipment by ID
	equipment := bm.GetEquipmentByID(building, "equipment-001")
	if equipment == nil {
		t.Fatal("Equipment not found")
	}

	if equipment.Name != "Main HVAC Unit" {
		t.Errorf("Expected equipment name 'Main HVAC Unit', got '%s'", equipment.Name)
	}

	// Test updating equipment
	updates := map[string]any{
		"name":   "Updated HVAC Unit",
		"status": StatusMaintenance,
	}

	err = bm.UpdateEquipment(building, "equipment-001", updates)
	if err != nil {
		t.Fatalf("Failed to update equipment: %v", err)
	}

	updatedEquipment := bm.GetEquipmentByID(building, "equipment-001")
	if updatedEquipment.Name != "Updated HVAC Unit" {
		t.Errorf("Expected updated name 'Updated HVAC Unit', got '%s'", updatedEquipment.Name)
	}
	if updatedEquipment.Status != StatusMaintenance {
		t.Errorf("Expected updated status '%s', got '%s'", StatusMaintenance, updatedEquipment.Status)
	}

	// Test removing equipment
	err = bm.RemoveEquipment(building, "equipment-001")
	if err != nil {
		t.Fatalf("Failed to remove equipment: %v", err)
	}

	equipment = bm.GetEquipmentByID(building, "equipment-001")
	if equipment != nil {
		t.Error("Equipment should be removed")
	}

	// Test removing floor (should work now that equipment is removed)
	err = bm.RemoveFloor(building, 1)
	if err != nil {
		t.Fatalf("Failed to remove floor: %v", err)
	}

	if len(building.Floors) != 0 {
		t.Errorf("Expected 0 floors, got %d", len(building.Floors))
	}
}

func TestBuildingValidation(t *testing.T) {
	bm := NewBuildingManager()

	tests := []struct {
		name           string
		building       *EnhancedBuilding
		expectedIssues int
	}{
		{
			name: "Valid building",
			building: &EnhancedBuilding{
				ID:           "building-001",
				Name:         "Valid Building",
				BuildingType: BuildingTypeOffice,
				Status:       BuildingStatusActive,
				Floors:       []FloorPlan{},
			},
			expectedIssues: 1, // Warning about no floors
		},
		{
			name: "Missing ID",
			building: &EnhancedBuilding{
				Name:         "No ID Building",
				BuildingType: BuildingTypeOffice,
				Status:       BuildingStatusActive,
			},
			expectedIssues: 2, // Error for missing ID, warning for no floors
		},
		{
			name: "Missing name",
			building: &EnhancedBuilding{
				ID:           "building-002",
				BuildingType: BuildingTypeOffice,
				Status:       BuildingStatusActive,
			},
			expectedIssues: 2, // Warning for missing name, warning for no floors
		},
		{
			name: "Invalid building type",
			building: &EnhancedBuilding{
				ID:           "building-003",
				Name:         "Invalid Type Building",
				BuildingType: "invalid_type",
				Status:       BuildingStatusActive,
			},
			expectedIssues: 2, // Error for invalid type, warning for no floors
		},
		{
			name: "Invalid status",
			building: &EnhancedBuilding{
				ID:           "building-004",
				Name:         "Invalid Status Building",
				BuildingType: BuildingTypeOffice,
				Status:       "invalid_status",
			},
			expectedIssues: 2, // Error for invalid status, warning for no floors
		},
		{
			name: "Duplicate floor numbers",
			building: &EnhancedBuilding{
				ID:           "building-005",
				Name:         "Duplicate Floors Building",
				BuildingType: BuildingTypeOffice,
				Status:       BuildingStatusActive,
				Floors: []FloorPlan{
					{ID: "floor-001", Level: 1, Name: "Floor 1"},
					{ID: "floor-002", Level: 1, Name: "Floor 1 Duplicate"},
				},
			},
			expectedIssues: 1, // Error for duplicate floor numbers
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			issues := bm.ValidateBuilding(tt.building)
			if len(issues) != tt.expectedIssues {
				t.Errorf("Expected %d issues, got %d", tt.expectedIssues, len(issues))
				for _, issue := range issues {
					t.Logf("Issue: %s - %s: %s", issue.Level, issue.Field, issue.Message)
				}
			}
		})
	}
}

func TestBuildingStats(t *testing.T) {
	bm := NewBuildingManager()

	// Create building with floors and equipment
	building := &EnhancedBuilding{
		ID:           "building-stats-test",
		Name:         "Stats Test Building",
		BuildingType: BuildingTypeOffice,
		Status:       BuildingStatusActive,
		Coverage:     85.5,
		Floors: []FloorPlan{
			{
				ID:    "floor-001",
				Level: 1,
				Name:  "Ground Floor",
				Rooms: []*Room{
					{ID: "room-001", Name: "Office 101"},
					{ID: "room-002", Name: "Office 102"},
				},
				Equipment: []*Equipment{
					{ID: "equipment-001", Name: "HVAC Unit 1"},
					{ID: "equipment-002", Name: "Lighting Panel 1"},
				},
			},
			{
				ID:    "floor-002",
				Level: 2,
				Name:  "Second Floor",
				Rooms: []*Room{
					{ID: "room-003", Name: "Conference Room"},
				},
				Equipment: []*Equipment{
					{ID: "equipment-003", Name: "HVAC Unit 2"},
				},
			},
		},
	}

	stats := bm.CalculateBuildingStats(building)

	// Verify stats
	if stats.TotalBuildings != 1 {
		t.Errorf("Expected TotalBuildings 1, got %d", stats.TotalBuildings)
	}
	if stats.ActiveBuildings != 1 {
		t.Errorf("Expected ActiveBuildings 1, got %d", stats.ActiveBuildings)
	}
	if stats.TotalFloors != 2 {
		t.Errorf("Expected TotalFloors 2, got %d", stats.TotalFloors)
	}
	if stats.TotalRooms != 3 {
		t.Errorf("Expected TotalRooms 3, got %d", stats.TotalRooms)
	}
	if stats.TotalEquipment != 3 {
		t.Errorf("Expected TotalEquipment 3, got %d", stats.TotalEquipment)
	}
	if stats.AverageCoverage != 85.5 {
		t.Errorf("Expected AverageCoverage 85.5, got %f", stats.AverageCoverage)
	}

	// Note: Area and volume calculations are not implemented in FloorPlan
	// These would need to be calculated from room data or added to FloorPlan
	// For now, we expect 0 values
	if stats.TotalFloorArea != 0.0 {
		t.Errorf("Expected TotalFloorArea 0.0, got %f", stats.TotalFloorArea)
	}

	if stats.TotalBuildingVolume != 0.0 {
		t.Errorf("Expected TotalBuildingVolume 0.0, got %f", stats.TotalBuildingVolume)
	}
}

func TestBuildingTypeValidation(t *testing.T) {
	tests := []struct {
		buildingType BuildingType
		expected     bool
	}{
		{BuildingTypeOffice, true},
		{BuildingTypeResidential, true},
		{BuildingTypeCommercial, true},
		{BuildingTypeIndustrial, true},
		{BuildingTypeEducational, true},
		{BuildingTypeHealthcare, true},
		{BuildingTypeRetail, true},
		{BuildingTypeWarehouse, true},
		{BuildingTypeMixed, true},
		{"invalid_type", false},
		{"", false},
	}

	for _, tt := range tests {
		t.Run(string(tt.buildingType), func(t *testing.T) {
			result := isValidBuildingType(tt.buildingType)
			if result != tt.expected {
				t.Errorf("Expected %v, got %v", tt.expected, result)
			}
		})
	}
}

func TestBuildingStatusValidation(t *testing.T) {
	tests := []struct {
		status   BuildingStatus
		expected bool
	}{
		{BuildingStatusActive, true},
		{BuildingStatusInactive, true},
		{BuildingStatusMaintenance, true},
		{BuildingStatusConstruction, true},
		{BuildingStatusDemolished, true},
		{"invalid_status", false},
		{"", false},
	}

	for _, tt := range tests {
		t.Run(string(tt.status), func(t *testing.T) {
			result := isValidBuildingStatus(tt.status)
			if result != tt.expected {
				t.Errorf("Expected %v, got %v", tt.expected, result)
			}
		})
	}
}

func TestBuildingManagerErrors(t *testing.T) {
	bm := NewBuildingManager()

	building := &EnhancedBuilding{
		ID:   "test-building",
		Name: "Test Building",
		Floors: []FloorPlan{
			{ID: "floor-001", Level: 1, Name: "Floor 1"},
		},
	}

	// Test adding equipment to non-existent floor
	equipment := Equipment{
		ID:   "equipment-001",
		Name: "Test Equipment",
		Type: "test",
	}

	err := bm.AddEquipment(building, 999, equipment)
	if err == nil {
		t.Error("Expected error when adding equipment to non-existent floor")
	}
	if err.Error() != "NOT_FOUND: Floor number 999 not found" {
		t.Errorf("Expected NotFound error, got: %v", err)
	}

	// Test removing non-existent equipment
	err = bm.RemoveEquipment(building, "non-existent")
	if err == nil {
		t.Error("Expected error when removing non-existent equipment")
	}
	if err.Error() != "NOT_FOUND: Equipment non-existent not found" {
		t.Errorf("Expected NotFound error, got: %v", err)
	}

	// Test updating non-existent equipment
	updates := map[string]any{"name": "Updated"}
	err = bm.UpdateEquipment(building, "non-existent", updates)
	if err == nil {
		t.Error("Expected error when updating non-existent equipment")
	}
	if err.Error() != "NOT_FOUND: Equipment non-existent not found" {
		t.Errorf("Expected NotFound error, got: %v", err)
	}

	// Test removing non-existent floor
	err = bm.RemoveFloor(building, 999)
	if err == nil {
		t.Error("Expected error when removing non-existent floor")
	}
	if err.Error() != "NOT_FOUND: Floor number 999 not found" {
		t.Errorf("Expected NotFound error, got: %v", err)
	}

	// Test adding duplicate floor number
	floor1 := FloorPlan{ID: "floor-002", Level: 1, Name: "Duplicate Floor"}
	err = bm.AddFloor(building, floor1)
	if err == nil {
		t.Error("Expected error when adding duplicate floor number")
	}
	if err.Error() != "CONFLICT: Floor number 1 already exists" {
		t.Errorf("Expected Conflict error, got: %v", err)
	}
}

func TestBuildingQuery(t *testing.T) {
	// Test building query structure
	officeType := BuildingTypeOffice
	activeStatus := BuildingStatusActive
	query := &BuildingQuery{
		Name:         stringPtr("Test Building"),
		BuildingType: &officeType,
		Status:       &activeStatus,
		Limit:        10,
		Offset:       0,
		SortBy:       "name",
		SortOrder:    "asc",
	}

	if query.Name == nil || *query.Name != "Test Building" {
		t.Error("Query name not set correctly")
	}
	if query.BuildingType == nil || *query.BuildingType != BuildingTypeOffice {
		t.Error("Query building type not set correctly")
	}
	if query.Status == nil || *query.Status != BuildingStatusActive {
		t.Error("Query status not set correctly")
	}
	if query.Limit != 10 {
		t.Error("Query limit not set correctly")
	}
	if query.Offset != 0 {
		t.Error("Query offset not set correctly")
	}
	if query.SortBy != "name" {
		t.Error("Query sort by not set correctly")
	}
	if query.SortOrder != "asc" {
		t.Error("Query sort order not set correctly")
	}
}

// Helper function for creating string pointers
func stringPtr(s string) *string {
	return &s
}
