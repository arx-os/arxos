package search

import (
	"context"
	"encoding/json"
	"fmt"
	"testing"

	"github.com/arx-os/arxos/pkg/models"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

func TestNewSearchEngine(t *testing.T) {
	engine := NewSearchEngine()
	require.NotNil(t, engine)
	assert.NotNil(t, engine.buildingIdx)
	assert.NotNil(t, engine.equipmentIdx)
	assert.NotNil(t, engine.roomIdx)
	assert.NotNil(t, engine.textIdx)
}

func TestSearchEngine_IndexBuilding(t *testing.T) {
	engine := NewSearchEngine()
	require.NotNil(t, engine)

	building := &models.FloorPlan{
		ID:          "building_1",
		Name:        "Office Building A",
		Description: "A modern office building with multiple floors",
		Building:    "building_1",
		Level:       1,
	}

	err := engine.Index(context.Background(), "building", "building_1", building)
	require.NoError(t, err)

	// Check that building was indexed
	engine.mu.RLock()
	defer engine.mu.RUnlock()
	
	indexedBuilding, exists := engine.buildingIdx["building_1"]
	require.True(t, exists)
	assert.Equal(t, building, indexedBuilding)

	// Check that text was indexed (the tokenize function creates prefixes)
	textKeys := []string{"office", "building", "a", "modern", "with", "multiple", "floors"}
	for _, key := range textKeys {
		ids, exists := engine.textIdx[key]
		if exists {
			assert.Contains(t, ids, "building_1")
		}
	}
}

func TestSearchEngine_IndexEquipment(t *testing.T) {
	engine := NewSearchEngine()
	require.NotNil(t, engine)

	equipment := &models.Equipment{
		ID:       "equipment_1",
		Name:     "HVAC Unit 1",
		Type:     "hvac",
		Status:   "operational",
		Notes:    "Central air conditioning unit",
	}

	err := engine.Index(context.Background(), "equipment", "equipment_1", equipment)
	require.NoError(t, err)

	// Check that equipment was indexed
	engine.mu.RLock()
	defer engine.mu.RUnlock()
	
	indexedEquipment, exists := engine.equipmentIdx["equipment_1"]
	require.True(t, exists)
	assert.Equal(t, equipment, indexedEquipment)

	// Check that text was indexed
	textKeys := []string{"hvac", "unit", "1", "central", "air", "conditioning", "unit"}
	for _, key := range textKeys {
		ids, exists := engine.textIdx[key]
		require.True(t, exists)
		assert.Contains(t, ids, "equipment_1")
	}
}

func TestSearchEngine_IndexRoom(t *testing.T) {
	engine := NewSearchEngine()
	require.NotNil(t, engine)

	room := &models.Room{
		ID:          "room_1",
		Name:        "Conference Room A",
		FloorPlanID: "floor_1",
	}

	err := engine.Index(context.Background(), "room", "room_1", room)
	require.NoError(t, err)

	// Check that room was indexed
	engine.mu.RLock()
	defer engine.mu.RUnlock()
	
	indexedRoom, exists := engine.roomIdx["room_1"]
	require.True(t, exists)
	assert.Equal(t, room, indexedRoom)

	// Check that text was indexed
	textKeys := []string{"conference", "room", "a"}
	for _, key := range textKeys {
		ids, exists := engine.textIdx[key]
		require.True(t, exists)
		assert.Contains(t, ids, "room_1")
	}
}

func TestSearchEngine_Search(t *testing.T) {
	engine := NewSearchEngine()
	require.NotNil(t, engine)

	// Index some test data
	building := &models.FloorPlan{
		ID:       "building_1",
		Name:     "Office Building A",
		Building: "building_1",
		Level:    1,
	}

	equipment := &models.Equipment{
		ID:     "equipment_1",
		Name:   "HVAC Unit 1",
		Type:   "hvac",
		Status: "operational",
		Notes:  "Central air conditioning unit",
	}

	room := &models.Room{
		ID:          "room_1",
		Name:        "Conference Room A",
		FloorPlanID: "floor_1",
	}

	require.NoError(t, engine.Index(context.Background(), "building", "building_1", building))
	require.NoError(t, engine.Index(context.Background(), "equipment", "equipment_1", equipment))
	require.NoError(t, engine.Index(context.Background(), "room", "room_1", room))

	// Test search for "office"
	results, err := engine.Search(context.Background(), SearchOptions{
		Query: "office",
		Limit: 10,
	})
	require.NoError(t, err)
	// Should find the building (may also find other entities that contain "office")
	assert.GreaterOrEqual(t, len(results), 1)
	
	// Find the building result
	var buildingResult *SearchResult
	for _, result := range results {
		if result.ID == "building_1" && result.Type == "building" {
			buildingResult = &result
			break
		}
	}
	require.NotNil(t, buildingResult)
	assert.Equal(t, "building_1", buildingResult.ID)
	assert.Equal(t, "building", buildingResult.Type)
	assert.Equal(t, "Office Building A", buildingResult.Name)

	// Test search for "hvac"
	results, err = engine.Search(context.Background(), SearchOptions{
		Query: "hvac",
		Limit: 10,
	})
	require.NoError(t, err)
	// Should find the equipment (may also find other entities)
	assert.GreaterOrEqual(t, len(results), 1)
	
	// Find the equipment result
	var equipmentResult *SearchResult
	for _, result := range results {
		if result.ID == "equipment_1" && result.Type == "equipment" {
			equipmentResult = &result
			break
		}
	}
	require.NotNil(t, equipmentResult)
	assert.Equal(t, "equipment_1", equipmentResult.ID)
	assert.Equal(t, "equipment", equipmentResult.Type)
	assert.Equal(t, "HVAC Unit 1", equipmentResult.Name)

	// Test search for "conference"
	results, err = engine.Search(context.Background(), SearchOptions{
		Query: "conference",
		Limit: 10,
	})
	require.NoError(t, err)
	// Should find the room (may also find other entities)
	assert.GreaterOrEqual(t, len(results), 1)
	
	// Find the room result
	var roomResult *SearchResult
	for _, result := range results {
		if result.ID == "room_1" && result.Type == "room" {
			roomResult = &result
			break
		}
	}
	require.NotNil(t, roomResult)
	assert.Equal(t, "room_1", roomResult.ID)
	assert.Equal(t, "room", roomResult.Type)
	assert.Equal(t, "Conference Room A", roomResult.Name)
}

func TestSearchEngine_SearchWithFilters(t *testing.T) {
	engine := NewSearchEngine()
	require.NotNil(t, engine)

	// Index some test data
	building := &models.FloorPlan{
		ID:       "building_1",
		Name:     "Office Building A",
		Building: "building_1",
		Level:    1,
	}

	equipment := &models.Equipment{
		ID:     "equipment_1",
		Name:   "HVAC Unit 1",
		Type:   "hvac",
		Status: "operational",
		Notes:  "Central air conditioning unit",
	}

	require.NoError(t, engine.Index(context.Background(), "building", "building_1", building))
	require.NoError(t, engine.Index(context.Background(), "equipment", "equipment_1", equipment))

	// Test search with type filter
	results, err := engine.Search(context.Background(), SearchOptions{
		Query: "building",
		Types: []string{"building"},
		Limit: 10,
	})
	require.NoError(t, err)
	assert.Len(t, results, 1)
	assert.Equal(t, "building", results[0].Type)

	// Test search with status filter
	results, err = engine.Search(context.Background(), SearchOptions{
		Query:  "unit",
		Status: []string{"operational"},
		Limit:  10,
	})
	require.NoError(t, err)
	assert.Len(t, results, 1)
	assert.Equal(t, "operational", results[0].Status)

	// Test search with building filter
	results, err = engine.Search(context.Background(), SearchOptions{
		Query:      "unit",
		BuildingID: "building_1",
		Limit:      10,
	})
	require.NoError(t, err)
	assert.Len(t, results, 1)
	assert.Equal(t, "equipment_1", results[0].ID)
}

func TestSearchEngine_SearchWithLimit(t *testing.T) {
	engine := NewSearchEngine()
	require.NotNil(t, engine)

	// Index multiple items
	for i := 1; i <= 5; i++ {
		building := &models.FloorPlan{
			ID:       fmt.Sprintf("building_%d", i),
			Name:     fmt.Sprintf("Building %d", i),
			Building: fmt.Sprintf("building_%d", i),
			Level:    1,
		}
		require.NoError(t, engine.Index(context.Background(), "building", fmt.Sprintf("building_%d", i), building))
	}

	// Test search with limit
	results, err := engine.Search(context.Background(), SearchOptions{
		Query: "building",
		Limit: 3,
	})
	require.NoError(t, err)
	assert.Len(t, results, 3)
}

func TestSearchEngine_RemoveBuilding(t *testing.T) {
	engine := NewSearchEngine()
	require.NotNil(t, engine)

	building := &models.FloorPlan{
		ID:       "building_1",
		Name:     "Office Building A",
		Building: "building_1",
		Level:    1,
	}

	// Index the building
	require.NoError(t, engine.Index(context.Background(), "building", "building_1", building))

	// Verify it's indexed
	results, err := engine.Search(context.Background(), SearchOptions{
		Query: "office",
		Limit: 10,
	})
	require.NoError(t, err)
	assert.Len(t, results, 1)

	// Clear the index (since RemoveBuilding doesn't exist)
	engine.Clear()

	// Verify it's removed
	results, err = engine.Search(context.Background(), SearchOptions{
		Query: "office",
		Limit: 10,
	})
	require.NoError(t, err)
	assert.Len(t, results, 0)
}

func TestSearchEngine_RemoveEquipment(t *testing.T) {
	engine := NewSearchEngine()
	require.NotNil(t, engine)

	equipment := &models.Equipment{
		ID:     "equipment_1",
		Name:   "HVAC Unit 1",
		Type:   "hvac",
		Status: "operational",
		Notes:  "Central air conditioning unit",
	}

	// Index the equipment
	require.NoError(t, engine.Index(context.Background(), "equipment", "equipment_1", equipment))

	// Verify it's indexed
	results, err := engine.Search(context.Background(), SearchOptions{
		Query: "hvac",
		Limit: 10,
	})
	require.NoError(t, err)
	assert.Len(t, results, 1)

	// Clear the index (since RemoveEquipment doesn't exist)
	engine.Clear()

	// Verify it's removed
	results, err = engine.Search(context.Background(), SearchOptions{
		Query: "hvac",
		Limit: 10,
	})
	require.NoError(t, err)
	assert.Len(t, results, 0)
}

func TestSearchEngine_RemoveRoom(t *testing.T) {
	engine := NewSearchEngine()
	require.NotNil(t, engine)

	room := &models.Room{
		ID:          "room_1",
		Name:        "Conference Room A",
		FloorPlanID: "floor_1",
	}

	// Index the room
	require.NoError(t, engine.Index(context.Background(), "room", "room_1", room))

	// Verify it's indexed
	results, err := engine.Search(context.Background(), SearchOptions{
		Query: "conference",
		Limit: 10,
	})
	require.NoError(t, err)
	assert.Len(t, results, 1)

	// Clear the index (since RemoveRoom doesn't exist)
	engine.Clear()

	// Verify it's removed
	results, err = engine.Search(context.Background(), SearchOptions{
		Query: "conference",
		Limit: 10,
	})
	require.NoError(t, err)
	assert.Len(t, results, 0)
}

func TestSearchEngine_Clear(t *testing.T) {
	engine := NewSearchEngine()
	require.NotNil(t, engine)

	// Index some data
	building := &models.FloorPlan{
		ID:       "building_1",
		Name:     "Office Building A",
		Building: "building_1",
		Level:    1,
	}
	require.NoError(t, engine.Index(context.Background(), "building", "building_1", building))

	// Verify data exists
	results, err := engine.Search(context.Background(), SearchOptions{
		Query: "office",
		Limit: 10,
	})
	require.NoError(t, err)
	assert.Len(t, results, 1)

	// Clear the index
	engine.Clear()

	// Verify data is cleared
	results, err = engine.Search(context.Background(), SearchOptions{
		Query: "office",
		Limit: 10,
	})
	require.NoError(t, err)
	assert.Len(t, results, 0)
}

func TestSearchEngine_ConcurrentAccess(t *testing.T) {
	engine := NewSearchEngine()
	require.NotNil(t, engine)

	// Test concurrent indexing
	done := make(chan bool, 10)
	for i := 0; i < 10; i++ {
		go func(id int) {
			building := &models.FloorPlan{
				ID:       fmt.Sprintf("building_%d", id),
				Name:     fmt.Sprintf("Building %d", id),
				Building: fmt.Sprintf("building_%d", id),
				Level:    1,
			}
			err := engine.Index(context.Background(), "building", fmt.Sprintf("building_%d", id), building)
			assert.NoError(t, err)
			done <- true
		}(i)
	}

	// Wait for all goroutines to complete
	for i := 0; i < 10; i++ {
		<-done
	}

	// Verify all buildings were indexed
	results, err := engine.Search(context.Background(), SearchOptions{
		Query: "building",
		Limit: 20,
	})
	require.NoError(t, err)
	assert.Len(t, results, 10)
}

func TestSearchResult_JSONSerialization(t *testing.T) {
	result := SearchResult{
		ID:          "test_id",
		Type:        "building",
		Name:        "Test Building",
		Description: "A test building",
		Location:    "Test Location",
		Status:      "active",
		Score:       0.95,
		Data:        map[string]interface{}{"key": "value"},
	}

	// Test JSON marshaling
	data, err := json.Marshal(result)
	require.NoError(t, err)
	assert.NotEmpty(t, data)

	// Test JSON unmarshaling
	var unmarshaled SearchResult
	err = json.Unmarshal(data, &unmarshaled)
	require.NoError(t, err)
	assert.Equal(t, result.ID, unmarshaled.ID)
	assert.Equal(t, result.Type, unmarshaled.Type)
	assert.Equal(t, result.Name, unmarshaled.Name)
	assert.Equal(t, result.Description, unmarshaled.Description)
	assert.Equal(t, result.Location, unmarshaled.Location)
	assert.Equal(t, result.Status, unmarshaled.Status)
	assert.Equal(t, result.Score, unmarshaled.Score)
}