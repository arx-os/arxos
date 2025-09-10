package models

import (
	"testing"
	"time"
)

func TestBoundsContains(t *testing.T) {
	tests := []struct {
		name     string
		bounds   Bounds
		point    Point
		expected bool
	}{
		{
			name: "point inside bounds",
			bounds: Bounds{MinX: 0, MinY: 0, MaxX: 10, MaxY: 10},
			point: Point{X: 5, Y: 5},
			expected: true,
		},
		{
			name: "point on edge",
			bounds: Bounds{MinX: 0, MinY: 0, MaxX: 10, MaxY: 10},
			point: Point{X: 0, Y: 0},
			expected: true,
		},
		{
			name: "point outside bounds",
			bounds: Bounds{MinX: 0, MinY: 0, MaxX: 10, MaxY: 10},
			point: Point{X: 15, Y: 15},
			expected: false,
		},
		{
			name: "point partially outside",
			bounds: Bounds{MinX: 0, MinY: 0, MaxX: 10, MaxY: 10},
			point: Point{X: 5, Y: 15},
			expected: false,
		},
	}
	
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := tt.bounds.Contains(tt.point)
			if result != tt.expected {
				t.Errorf("Contains() = %v, want %v", result, tt.expected)
			}
		})
	}
}

func TestBoundsDimensions(t *testing.T) {
	bounds := Bounds{MinX: 10, MinY: 20, MaxX: 50, MaxY: 80}
	
	expectedWidth := 40.0
	if width := bounds.Width(); width != expectedWidth {
		t.Errorf("Width() = %v, want %v", width, expectedWidth)
	}
	
	expectedHeight := 60.0
	if height := bounds.Height(); height != expectedHeight {
		t.Errorf("Height() = %v, want %v", height, expectedHeight)
	}
}

func TestEquipmentStatus(t *testing.T) {
	equipment := Equipment{
		ID:     "test_outlet",
		Name:   "Test Outlet",
		Type:   "outlet",
		Status: StatusNormal,
	}
	
	// Test status values
	statuses := []EquipmentStatus{
		StatusNormal,
		StatusNeedsRepair,
		StatusFailed,
		StatusUnknown,
	}
	
	for _, status := range statuses {
		equipment.Status = status
		if equipment.Status != status {
			t.Errorf("Status assignment failed: got %v, want %v", equipment.Status, status)
		}
	}
}

func TestFloorPlanCreation(t *testing.T) {
	now := time.Now()
	
	plan := FloorPlan{
		Name:      "Test Floor",
		Building:  "Test Building",
		Level:     2,
		CreatedAt: now,
		UpdatedAt: now,
		Rooms: []Room{
			{
				ID:   "room_1",
				Name: "Room 1",
				Bounds: Bounds{MinX: 0, MinY: 0, MaxX: 100, MaxY: 100},
				Equipment: []string{"equip_1", "equip_2"},
			},
		},
		Equipment: []Equipment{
			{
				ID:       "equip_1",
				Name:     "Outlet 1",
				Type:     "outlet",
				Location: Point{X: 50, Y: 50},
				RoomID:   "room_1",
				Status:   StatusNormal,
			},
			{
				ID:       "equip_2",
				Name:     "Switch 1",
				Type:     "switch",
				Location: Point{X: 30, Y: 30},
				RoomID:   "room_1",
				Status:   StatusNeedsRepair,
			},
		},
	}
	
	if len(plan.Rooms) != 1 {
		t.Errorf("Expected 1 room, got %d", len(plan.Rooms))
	}
	
	if len(plan.Equipment) != 2 {
		t.Errorf("Expected 2 equipment items, got %d", len(plan.Equipment))
	}
	
	// Verify equipment is in correct room
	room := plan.Rooms[0]
	if len(room.Equipment) != 2 {
		t.Errorf("Expected 2 equipment IDs in room, got %d", len(room.Equipment))
	}
	
	// Verify equipment references
	for _, equipID := range room.Equipment {
		found := false
		for _, equip := range plan.Equipment {
			if equip.ID == equipID {
				found = true
				if equip.RoomID != room.ID {
					t.Errorf("Equipment %s has wrong room ID: got %s, want %s", 
						equipID, equip.RoomID, room.ID)
				}
				break
			}
		}
		if !found {
			t.Errorf("Equipment ID %s not found in equipment list", equipID)
		}
	}
}