// Simple HTTP server for ArxOS ASCII-BIM PWA development and testing
package main

import (
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"path/filepath"
	"strconv"
	"time"

	"github.com/gorilla/websocket"
)

// Mock ArxObject for demo purposes
type MockArxObject struct {
	ID          string                 `json:"id"`
	Type        string                 `json:"type"`
	Name        string                 `json:"name"`
	Description string                 `json:"description"`
	BuildingID  string                 `json:"building_id"`
	FloorID     string                 `json:"floor_id"`
	Geometry    MockGeometry           `json:"geometry"`
	Properties  map[string]interface{} `json:"properties"`
	Confidence  float64                `json:"confidence"`
	SourceType  string                 `json:"source_type"`
	SourceFile  string                 `json:"source_file"`
	Version     int                    `json:"version"`
}

type MockGeometry struct {
	Position    Position    `json:"position"`
	BoundingBox BoundingBox `json:"bounding_box"`
}

type Position struct {
	X float64 `json:"x"`
	Y float64 `json:"y"`
	Z float64 `json:"z"`
}

type BoundingBox struct {
	Min Position `json:"min"`
	Max Position `json:"max"`
}

type WebSocketMessage struct {
	Type      string      `json:"type"`
	Payload   interface{} `json:"payload,omitempty"`
	Context   interface{} `json:"context,omitempty"`
	Timestamp string      `json:"timestamp"`
}

type BuildingData struct {
	Objects []MockArxObject `json:"objects"`
	Floor   string          `json:"floor"`
}

var upgrader = websocket.Upgrader{
	CheckOrigin: func(r *http.Request) bool {
		return true // Allow all origins for development
	},
}

func main() {
	// Serve static files
	fs := http.FileServer(http.Dir("./"))
	http.Handle("/", fs)

	// WebSocket endpoint
	http.HandleFunc("/ws", handleWebSocket)

	// API endpoints for testing
	http.HandleFunc("/api/buildings", handleBuildings)
	http.HandleFunc("/api/building/", handleBuildingData)

	port := 8080
	fmt.Printf("Starting ArxOS ASCII-BIM PWA server on port %d\n", port)
	fmt.Printf("PWA URL: http://localhost:%d\n", port)
	fmt.Printf("WebSocket URL: ws://localhost:%d/ws\n", port)

	log.Fatal(http.ListenAndServe(fmt.Sprintf(":%d", port), nil))
}

func handleWebSocket(w http.ResponseWriter, r *http.Request) {
	conn, err := upgrader.Upgrade(w, r, nil)
	if err != nil {
		log.Printf("WebSocket upgrade error: %v", err)
		return
	}
	defer conn.Close()

	log.Printf("WebSocket client connected: %s", r.RemoteAddr)

	for {
		var msg WebSocketMessage
		err := conn.ReadJSON(&msg)
		if err != nil {
			log.Printf("WebSocket read error: %v", err)
			break
		}

		log.Printf("Received WebSocket message: %s", msg.Type)

		switch msg.Type {
		case "layer_context":
			// Acknowledge layer context
			response := WebSocketMessage{
				Type:      "layer_context_ack",
				Timestamp: time.Now().Format(time.RFC3339),
			}
			conn.WriteJSON(response)

		case "get_building_list":
			// Send building list
			buildings := []map[string]interface{}{
				{"id": "demo-office", "name": "Demo Office Building"},
				{"id": "sample-retail", "name": "Sample Retail Space"},
				{"id": "test-warehouse", "name": "Test Warehouse"},
			}
			
			response := WebSocketMessage{
				Type:      "building_list",
				Payload:   buildings,
				Timestamp: time.Now().Format(time.RFC3339),
			}
			conn.WriteJSON(response)

		case "select_building":
			// Handle building selection
			payloadBytes, _ := json.Marshal(msg.Payload)
			var buildingRequest map[string]interface{}
			json.Unmarshal(payloadBytes, &buildingRequest)
			
			buildingID, _ := buildingRequest["building_id"].(string)
			floor, _ := buildingRequest["floor"].(string)
			if floor == "" {
				floor = "f1"
			}

			objects := generateMockObjects(buildingID, floor)
			
			response := WebSocketMessage{
				Type: "building_data",
				Payload: BuildingData{
					Objects: objects,
					Floor:   floor,
				},
				Timestamp: time.Now().Format(time.RFC3339),
			}
			conn.WriteJSON(response)

		case "viewport_change":
			// Acknowledge viewport change
			log.Printf("Viewport changed: %+v", msg.Payload)
			
		default:
			log.Printf("Unknown message type: %s", msg.Type)
		}
	}

	log.Printf("WebSocket client disconnected: %s", r.RemoteAddr)
}

func handleBuildings(w http.ResponseWriter, r *http.Request) {
	buildings := []map[string]interface{}{
		{"id": "demo-office", "name": "Demo Office Building"},
		{"id": "sample-retail", "name": "Sample Retail Space"},
		{"id": "test-warehouse", "name": "Test Warehouse"},
	}

	w.Header().Set("Content-Type", "application/json")
	w.Header().Set("Access-Control-Allow-Origin", "*")
	json.NewEncoder(w).Encode(buildings)
}

func handleBuildingData(w http.ResponseWriter, r *http.Request) {
	buildingID := filepath.Base(r.URL.Path)
	floor := r.URL.Query().Get("floor")
	if floor == "" {
		floor = "f1"
	}

	objects := generateMockObjects(buildingID, floor)

	w.Header().Set("Content-Type", "application/json")
	w.Header().Set("Access-Control-Allow-Origin", "*")
	json.NewEncoder(w).Encode(map[string]interface{}{
		"objects": objects,
		"floor":   floor,
	})
}

func generateMockObjects(buildingID, floor string) []MockArxObject {
	objects := []MockArxObject{}

	switch buildingID {
	case "demo-office":
		objects = []MockArxObject{
			{
				ID: buildingID + "/" + floor + "/room/1", Type: "room", Name: "Reception Area",
				Description: "Main reception and waiting area", BuildingID: buildingID, FloorID: floor,
				Geometry: MockGeometry{
					Position:    Position{X: 15, Y: 10, Z: 0},
					BoundingBox: BoundingBox{Min: Position{X: 10, Y: 5}, Max: Position{X: 20, Y: 15}},
				},
				Properties: map[string]interface{}{"area_sqm": 50, "room_type": "reception"},
				Confidence: 0.95, SourceType: "cad", Version: 1,
			},
			{
				ID: buildingID + "/" + floor + "/room/2", Type: "room", Name: "Conference Room",
				Description: "Large conference room", BuildingID: buildingID, FloorID: floor,
				Geometry: MockGeometry{
					Position:    Position{X: 35, Y: 10, Z: 0},
					BoundingBox: BoundingBox{Min: Position{X: 25, Y: 5}, Max: Position{X: 45, Y: 15}},
				},
				Properties: map[string]interface{}{"area_sqm": 80, "room_type": "meeting", "capacity": 12},
				Confidence: 0.92, SourceType: "cad", Version: 1,
			},
			{
				ID: buildingID + "/" + floor + "/room/3", Type: "room", Name: "Open Office",
				Description: "Open office workspace", BuildingID: buildingID, FloorID: floor,
				Geometry: MockGeometry{
					Position:    Position{X: 30, Y: 30, Z: 0},
					BoundingBox: BoundingBox{Min: Position{X: 10, Y: 20}, Max: Position{X: 50, Y: 40}},
				},
				Properties: map[string]interface{}{"area_sqm": 300, "room_type": "workspace", "desks": 24},
				Confidence: 0.88, SourceType: "scan", Version: 1,
			},
		}

	case "sample-retail":
		objects = []MockArxObject{
			{
				ID: buildingID + "/" + floor + "/room/1", Type: "room", Name: "Sales Floor",
				Description: "Main retail sales area", BuildingID: buildingID, FloorID: floor,
				Geometry: MockGeometry{
					Position:    Position{X: 25, Y: 20, Z: 0},
					BoundingBox: BoundingBox{Min: Position{X: 5, Y: 5}, Max: Position{X: 45, Y: 35}},
				},
				Properties: map[string]interface{}{"area_sqm": 600, "room_type": "retail"},
				Confidence: 0.97, SourceType: "survey", Version: 1,
			},
			{
				ID: buildingID + "/" + floor + "/room/2", Type: "room", Name: "Storage",
				Description: "Back room storage", BuildingID: buildingID, FloorID: floor,
				Geometry: MockGeometry{
					Position:    Position{X: 55, Y: 20, Z: 0},
					BoundingBox: BoundingBox{Min: Position{X: 48, Y: 10}, Max: Position{X: 62, Y: 30}},
				},
				Properties: map[string]interface{}{"area_sqm": 140, "room_type": "storage"},
				Confidence: 0.90, SourceType: "survey", Version: 1,
			},
		}

	case "test-warehouse":
		objects = []MockArxObject{
			{
				ID: buildingID + "/" + floor + "/room/1", Type: "room", Name: "Warehouse Floor",
				Description: "Main warehouse storage area", BuildingID: buildingID, FloorID: floor,
				Geometry: MockGeometry{
					Position:    Position{X: 50, Y: 40, Z: 0},
					BoundingBox: BoundingBox{Min: Position{X: 10, Y: 10}, Max: Position{X: 90, Y: 70}},
				},
				Properties: map[string]interface{}{"area_sqm": 2400, "room_type": "warehouse", "height_m": 12},
				Confidence: 0.99, SourceType: "lidar", Version: 1,
			},
		}
	}

	// Add common elements to all buildings
	commonObjects := []MockArxObject{
		{
			ID: buildingID + "/" + floor + "/wall/1", Type: "wall", Name: "Exterior Wall North",
			Description: "North exterior wall", BuildingID: buildingID, FloorID: floor,
			Geometry: MockGeometry{
				Position:    Position{X: 30, Y: 45, Z: 0},
				BoundingBox: BoundingBox{Min: Position{X: 0, Y: 44}, Max: Position{X: 60, Y: 46}},
			},
			Properties: map[string]interface{}{"thickness_mm": 200, "load_bearing": true, "exterior": true},
			Confidence: 0.98, SourceType: "scan", Version: 1,
		},
		{
			ID: buildingID + "/" + floor + "/door/1", Type: "door", Name: "Main Entrance",
			Description: "Primary building entrance", BuildingID: buildingID, FloorID: floor,
			Geometry: MockGeometry{
				Position:    Position{X: 30, Y: 0, Z: 0},
				BoundingBox: BoundingBox{Min: Position{X: 29, Y: -1}, Max: Position{X: 31, Y: 1}},
			},
			Properties: map[string]interface{}{"width_mm": 900, "door_type": "double", "automatic": true},
			Confidence: 0.95, SourceType: "survey", Version: 1,
		},
		{
			ID: buildingID + "/" + floor + "/window/1", Type: "window", Name: "Front Windows",
			Description: "Front-facing windows", BuildingID: buildingID, FloorID: floor,
			Geometry: MockGeometry{
				Position:    Position{X: 20, Y: 0, Z: 1.5},
				BoundingBox: BoundingBox{Min: Position{X: 15, Y: -1}, Max: Position{X: 25, Y: 1}},
			},
			Properties: map[string]interface{}{"width_mm": 2000, "height_mm": 1500, "window_type": "fixed"},
			Confidence: 0.90, SourceType: "survey", Version: 1,
		},
	}

	objects = append(objects, commonObjects...)

	// Add some electrical equipment
	for i := 0; i < 3; i++ {
		objects = append(objects, MockArxObject{
			ID: buildingID + "/" + floor + "/outlet/" + strconv.Itoa(i+1), Type: "electrical_outlet",
			Name: "Power Outlet " + strconv.Itoa(i+1), Description: "Standard power outlet",
			BuildingID: buildingID, FloorID: floor,
			Geometry: MockGeometry{
				Position:    Position{X: float64(10 + i*15), Y: 5, Z: 0.3},
				BoundingBox: BoundingBox{Min: Position{X: float64(9 + i*15), Y: 4}, Max: Position{X: float64(11 + i*15), Y: 6}},
			},
			Properties: map[string]interface{}{"voltage": 120, "amperage": 20, "type": "duplex"},
			Confidence: 0.87, SourceType: "survey", Version: 1,
		})
	}

	return objects
}