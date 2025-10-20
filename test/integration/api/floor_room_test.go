package integration

import (
	"net/http"
	"net/http/httptest"
	"testing"

	"github.com/arx-os/arxos/internal/app"
	"github.com/arx-os/arxos/internal/domain"
	"github.com/arx-os/arxos/internal/domain/types"
	"github.com/stretchr/testify/assert"
)

func TestFloorRoomRESTAPI(t *testing.T) {
	WithTestServer(t, func(t *testing.T, server *httptest.Server, auth *TestAuthHelper, container *app.Container) {
		// Shared variables across subtests
		var buildingID, floorID, roomID string

		// Create a building first
		t.Run("Create_Building_First", func(t *testing.T) {
			buildingID = auth.CreateTestBuilding(t, "Test Building for Floors", "123 Test St")
			assert.NotEmpty(t, buildingID)
		})

		// Test Floor CRUD
		t.Run("Create_Floor", func(t *testing.T) {
			createReq := domain.CreateFloorRequest{
				BuildingID: types.FromString(buildingID),
				Name:       "Ground Floor",
				Level:      0,
			}

			resp := auth.POST(t, "/api/v1/floors", createReq)
			defer resp.Body.Close()

			assert.Equal(t, http.StatusCreated, resp.StatusCode)

			var floor domain.Floor
			auth.DecodeJSON(t, resp, &floor)
			floorID = floor.ID.String()

			assert.Equal(t, "Ground Floor", floor.Name)
			assert.Equal(t, 0, floor.Level)
			assert.NotEmpty(t, floorID)
		})

		t.Run("Get_Floor_by_ID", func(t *testing.T) {
			resp := auth.GET(t, "/api/v1/floors/"+floorID)
			defer resp.Body.Close()

			assert.Equal(t, http.StatusOK, resp.StatusCode)

			var floor domain.Floor
			auth.DecodeJSON(t, resp, &floor)

			assert.Equal(t, floorID, floor.ID.String())
			assert.Equal(t, "Ground Floor", floor.Name)
		})

		t.Run("List_Floors_by_Building", func(t *testing.T) {
			resp := auth.GET(t, "/api/v1/floors?building_id="+buildingID)
			defer resp.Body.Close()

			assert.Equal(t, http.StatusOK, resp.StatusCode)

			var result map[string]any
			auth.DecodeJSON(t, resp, &result)

			assert.Contains(t, result, "floors")
			floors := result["floors"].([]any)
			assert.GreaterOrEqual(t, len(floors), 1)
		})

		t.Run("Update_Floor", func(t *testing.T) {
			updatedName := "Updated Floor Name"
			updateReq := domain.UpdateFloorRequest{
				ID:   types.FromString(floorID),
				Name: &updatedName,
			}

			resp := auth.PUT(t, "/api/v1/floors/"+floorID, updateReq)
			defer resp.Body.Close()

			assert.Equal(t, http.StatusOK, resp.StatusCode)

			var floor domain.Floor
			auth.DecodeJSON(t, resp, &floor)

			assert.Equal(t, updatedName, floor.Name)
		})

		// Test Room CRUD
		t.Run("Create_Room", func(t *testing.T) {
			createReq := domain.CreateRoomRequest{
				FloorID: types.FromString(floorID),
				Name:    "Conference Room A",
				Number:  "101",
			}

			resp := auth.POST(t, "/api/v1/rooms", createReq)
			defer resp.Body.Close()

			assert.Equal(t, http.StatusCreated, resp.StatusCode)

			var room domain.Room
			auth.DecodeJSON(t, resp, &room)
			roomID = room.ID.String()

			assert.Equal(t, "Conference Room A", room.Name)
			assert.Equal(t, "101", room.Number)
			assert.NotEmpty(t, roomID)
		})

		t.Run("Get_Room_by_ID", func(t *testing.T) {
			resp := auth.GET(t, "/api/v1/rooms/"+roomID)
			defer resp.Body.Close()

			assert.Equal(t, http.StatusOK, resp.StatusCode)

			var room domain.Room
			auth.DecodeJSON(t, resp, &room)

			assert.Equal(t, roomID, room.ID.String())
			assert.Equal(t, "Conference Room A", room.Name)
		})

		t.Run("List_Rooms_by_Floor", func(t *testing.T) {
			resp := auth.GET(t, "/api/v1/rooms?floor_id="+floorID)
			defer resp.Body.Close()

			assert.Equal(t, http.StatusOK, resp.StatusCode)

			var result map[string]any
			auth.DecodeJSON(t, resp, &result)

			assert.Contains(t, result, "rooms")
			rooms := result["rooms"].([]any)
			assert.GreaterOrEqual(t, len(rooms), 1)
		})

		t.Run("Update_Room", func(t *testing.T) {
			updatedName := "Updated Conference Room"
			updateReq := domain.UpdateRoomRequest{
				ID:   types.FromString(roomID),
				Name: &updatedName,
			}

			resp := auth.PUT(t, "/api/v1/rooms/"+roomID, updateReq)
			defer resp.Body.Close()

			assert.Equal(t, http.StatusOK, resp.StatusCode)

			var room domain.Room
			auth.DecodeJSON(t, resp, &room)

			assert.Equal(t, updatedName, room.Name)
		})

		t.Run("Get_Floor_Rooms", func(t *testing.T) {
			resp := auth.GET(t, "/api/v1/floors/"+floorID+"/rooms")
			defer resp.Body.Close()

			assert.Equal(t, http.StatusOK, resp.StatusCode)

			var result map[string]any
			auth.DecodeJSON(t, resp, &result)

			// The response should contain rooms array
			if result["rooms"] != nil {
				rooms := result["rooms"].([]any)
				assert.GreaterOrEqual(t, len(rooms), 1)
			}
		})

		// Test Delete (in reverse order: room -> floor)
		t.Run("Delete_Room", func(t *testing.T) {
			resp := auth.DELETE(t, "/api/v1/rooms/"+roomID)
			defer resp.Body.Close()

			assert.Equal(t, http.StatusNoContent, resp.StatusCode)

			// Verify deletion
			getResp := auth.GET(t, "/api/v1/rooms/"+roomID)
			defer getResp.Body.Close()

			assert.Equal(t, http.StatusNotFound, getResp.StatusCode)
		})

		t.Run("Delete_Floor", func(t *testing.T) {
			resp := auth.DELETE(t, "/api/v1/floors/"+floorID)
			defer resp.Body.Close()

			assert.Equal(t, http.StatusNoContent, resp.StatusCode)

			// Verify deletion
			getResp := auth.GET(t, "/api/v1/floors/"+floorID)
			defer getResp.Body.Close()

			assert.Equal(t, http.StatusNotFound, getResp.StatusCode)
		})
	})
}
