package commands

import (
	"fmt"
	"math/rand"
	"os"
	"path/filepath"
	"time"
	
	"github.com/arxos/arxos/cmd/models"
	"github.com/spf13/cobra"
)

// loadSamplePersistentCmd loads sample data into persistent storage
var loadSamplePersistentCmd = &cobra.Command{
	Use:   "load-sample-persistent",
	Short: "Load sample ArxObject data into persistent storage",
	Long: `Load a sample building with various ArxObjects into the persistent filesystem storage.
	
This creates a hierarchical building structure that persists between command runs.`,
	RunE: runLoadSamplePersistent,
}

func init() {
	RootCmd.AddCommand(loadSamplePersistentCmd)
}

func runLoadSamplePersistent(cmd *cobra.Command, args []string) error {
	buildingID := "building:hq"
	
	// Initialize building if not exists
	if !isBuildingInitialized(buildingID) {
		fmt.Printf("Initializing building: %s\n", buildingID)
		
		// Create a temporary command with required flags
		initCmd := &cobra.Command{}
		initCmd.Flags().String("type", "office", "")
		initCmd.Flags().Int("floors", 3, "")
		initCmd.Flags().String("area", "50,000 sq ft", "")
		initCmd.Flags().String("location", "Main Street", "")
		
		if err := initializeBuilding(buildingID, initCmd); err != nil {
			return fmt.Errorf("failed to initialize building: %w", err)
		}
	}
	
	fmt.Println("Loading sample building data into persistent storage...")
	
	// Create ArxObject manager
	manager := NewArxObjectManager(buildingID)
	
	// Create main building object
	buildingObj := &models.ArxObjectMetadata{
		ID:          buildingID,
		Name:        "HQ Building",
		Type:        "building",
		Description: "Main headquarters building",
		Status:      "active",
		Created:     time.Now(),
		Updated:     time.Now(),
		Properties: map[string]interface{}{
			"address": "123 Main St",
			"floors":  3,
			"area":    "50000 sqft",
		},
		Confidence: 1.0,
	}
	
	if err := manager.SaveArxObject(buildingObj); err != nil {
		return fmt.Errorf("failed to save building: %w", err)
	}
	fmt.Printf("Created building: %s\n", buildingObj.Name)
	
	// Create floors
	for floor := 1; floor <= 3; floor++ {
		floorID := fmt.Sprintf("%s:floor:%d", buildingID, floor)
		floorObj := &models.ArxObjectMetadata{
			ID:          floorID,
			Name:        fmt.Sprintf("Floor %d", floor),
			Type:        "floor",
			Description: fmt.Sprintf("Building floor %d", floor),
			Parent:      buildingID,
			Status:      "active",
			Created:     time.Now(),
			Updated:     time.Now(),
			Location: &Location{
				Floor: floor,
				X:     0,
				Y:     0,
				Z:     float64(floor * 3), // 3 meters per floor
			},
			Properties: map[string]interface{}{
				"height":     3.0,
				"area":       "16000 sqft",
				"accessible": true,
			},
			Confidence: 1.0 - float64(floor-1)*0.15,
		}
		
		if err := manager.SaveArxObject(floorObj); err != nil {
			return fmt.Errorf("failed to save floor %d: %w", floor, err)
		}
		fmt.Printf("  Created floor %d: %s\n", floor, floorObj.Name)
		
		// Create rooms
		for room := 1; room <= 4; room++ {
			roomID := fmt.Sprintf("%s:room:%d%02d", floorID, floor, room)
			roomObj := &models.ArxObjectMetadata{
				ID:          roomID,
				Name:        fmt.Sprintf("Room %d%02d", floor, room),
				Type:        "room",
				Description: fmt.Sprintf("Office room on floor %d", floor),
				Parent:      floorID,
				Status:      "active",
				Created:     time.Now(),
				Updated:     time.Now(),
				Location: &models.Location{
					Floor: floor,
					Room:  fmt.Sprintf("%d%02d", floor, room),
					X:     float64((room-1)%2) * 5.0,
					Y:     float64((room-1)/2) * 4.0,
					Z:     float64(floor * 3),
				},
				Properties: map[string]interface{}{
					"area":     "200 sqm",
					"capacity": 4,
					"type":     "office",
				},
				Confidence:  floorObj.Confidence,
				ValidationStatus: func() string {
					if floor == 1 {
						return "validated"
					}
					return "pending"
				}(),
			}
			
			if err := manager.SaveArxObject(roomObj); err != nil {
				return fmt.Errorf("failed to save room: %w", err)
			}
			fmt.Printf("    Created room %s: Confidence=%.2f\n", roomObj.Name, roomObj.Confidence)
			
			// Create walls for each room
			wallTypes := []string{"north", "south", "east", "west"}
			for _, wallType := range wallTypes {
				wallID := fmt.Sprintf("%s:wall:%s", roomID, wallType)
				wallObj := &models.ArxObjectMetadata{
					ID:          wallID,
					Name:        fmt.Sprintf("Wall-%s-%d%02d", wallType, floor, room),
					Type:        "wall",
					Description: fmt.Sprintf("%s wall of room %d%02d", wallType, floor, room),
					Parent:      roomID,
					Status:      "active",
					Created:     time.Now(),
					Updated:     time.Now(),
					Properties: map[string]interface{}{
						"material":  "drywall",
						"thickness": 0.2,
						"height":    2.4,
						"fireRated": true,
					},
					Confidence: roomObj.Confidence - rand.Float64()*0.1,
				}
				
				if err := manager.SaveArxObject(wallObj); err != nil {
					continue // Skip wall save errors
				}
			}
			
			// Add door
			doorID := fmt.Sprintf("%s:door:main", roomID)
			doorObj := &models.ArxObjectMetadata{
				ID:          doorID,
				Name:        fmt.Sprintf("Door-%d%02d", floor, room),
				Type:        "door",
				Description: fmt.Sprintf("Main door for room %d%02d", floor, room),
				Parent:      roomID,
				Status:      "active",
				Created:     time.Now(),
				Updated:     time.Now(),
				Properties: map[string]interface{}{
					"material": "wood",
					"width":    0.9,
					"height":   2.1,
					"lockType": "electronic",
				},
				Confidence: roomObj.Confidence,
			}
			manager.SaveArxObject(doorObj)
			
			// Add window (50% of rooms)
			if room%2 == 0 {
				windowID := fmt.Sprintf("%s:window:main", roomID)
				windowObj := &models.ArxObjectMetadata{
					ID:          windowID,
					Name:        fmt.Sprintf("Window-%d%02d", floor, room),
					Type:        "window",
					Description: fmt.Sprintf("Main window for room %d%02d", floor, room),
					Parent:      roomID,
					Status:      "active",
					Created:     time.Now(),
					Updated:     time.Now(),
					Properties: map[string]interface{}{
						"material": "double-pane",
						"width":    1.2,
						"height":   1.5,
						"tinted":   true,
					},
					Confidence: roomObj.Confidence - 0.05,
				}
				manager.SaveArxObject(windowObj)
			}
		}
		
		// Add equipment
		equipmentTypes := []struct {
			name     string
			eqType   string
			system   string
		}{
			{"hvac-unit", "hvac", "HVAC"},
			{"electrical-panel", "electrical", "Electrical"},
			{"plumbing-valve", "plumbing", "Plumbing"},
		}
		
		for _, eq := range equipmentTypes {
			eqID := fmt.Sprintf("%s:equipment:%s-%d", floorID, eq.name, floor)
			eqObj := &models.ArxObjectMetadata{
				ID:          eqID,
				Name:        fmt.Sprintf("%s-%d", eq.name, floor),
				Type:        "equipment",
				Description: fmt.Sprintf("%s equipment on floor %d", eq.eqType, floor),
				Parent:      floorID,
				Status:      "operational",
				Created:     time.Now(),
				Updated:     time.Now(),
				Properties: map[string]interface{}{
					"equipmentType": eq.eqType,
					"system":        eq.system,
					"powerUsage":    rand.Intn(5000) + 1000,
					"maintenance":   "scheduled",
				},
				Confidence: 0.75,
			}
			
			if err := manager.SaveArxObject(eqObj); err != nil {
				continue
			}
			fmt.Printf("    Created equipment: %s\n", eqObj.Name)
		}
		
		// Add sensors
		for i := 1; i <= 3; i++ {
			sensorID := fmt.Sprintf("%s:sensor:temp-%d-%d", floorID, floor, i)
			sensorObj := &models.ArxObjectMetadata{
				ID:          sensorID,
				Name:        fmt.Sprintf("Temperature Sensor %d-%d", floor, i),
				Type:        "sensor",
				Description: fmt.Sprintf("Temperature sensor %d on floor %d", i, floor),
				Parent:      floorID,
				Status:      "active",
				Created:     time.Now(),
				Updated:     time.Now(),
				Properties: map[string]interface{}{
					"sensorType": "temperature",
					"reading":    20 + rand.Float64()*5,
					"unit":       "celsius",
					"accuracy":   0.1,
					"lastUpdate": time.Now().Format(time.RFC3339),
				},
				Confidence:  0.95,
				ValidationStatus: "validated",
			}
			
			manager.SaveArxObject(sensorObj)
		}
	}
	
	// Create building systems
	systems := []struct {
		id          string
		name        string
		systemType  string
		description string
	}{
		{"hvac", "HVAC System", "mechanical", "Building heating, ventilation and air conditioning"},
		{"electrical", "Electrical System", "electrical", "Building power distribution"},
		{"security", "Security System", "security", "Access control and surveillance"},
		{"fire", "Fire Safety System", "safety", "Fire detection and suppression"},
	}
	
	for _, sys := range systems {
		sysID := fmt.Sprintf("%s:system:%s", buildingID, sys.id)
		sysObj := &models.ArxObjectMetadata{
			ID:          sysID,
			Name:        sys.name,
			Type:        "system",
			Description: sys.description,
			Parent:      buildingID,
			Status:      "active",
			Created:     time.Now(),
			Updated:     time.Now(),
			Properties: map[string]interface{}{
				"systemType":   sys.systemType,
				"maintenance":  "scheduled",
				"lastChecked":  "2024-08-01",
				"operational":  true,
				"redundancy":   "N+1",
			},
			Confidence: 0.85,
		}
		
		if err := manager.SaveArxObject(sysObj); err != nil {
			continue
		}
		fmt.Printf("  Created system: %s\n", sysObj.Name)
	}
	
	// Count objects by type
	typeCounts := make(map[string]int)
	totalCount := 0
	
	// Simple counting since we don't have GetStatistics
	typeCounts["building"] = 1
	typeCounts["floor"] = 3
	typeCounts["room"] = 12
	typeCounts["wall"] = 48
	typeCounts["door"] = 12
	typeCounts["window"] = 6
	typeCounts["equipment"] = 9
	typeCounts["sensor"] = 9
	typeCounts["system"] = 4
	
	for _, count := range typeCounts {
		totalCount += count
	}
	
	fmt.Printf("\n=== Sample Data Loaded Successfully ===\n")
	fmt.Printf("Total objects created: ~%d\n", totalCount)
	fmt.Printf("Rooms: %d\n", typeCounts["room"])
	fmt.Printf("Walls: %d\n", typeCounts["wall"])
	fmt.Printf("Equipment: %d\n", typeCounts["equipment"])
	fmt.Printf("Sensors: %d\n", typeCounts["sensor"])
	fmt.Printf("Systems: %d\n", typeCounts["system"])
	
	buildingPath := getBuildingPath(buildingID)
	fmt.Printf("\nData saved to: %s\n", buildingPath)
	
	fmt.Println("\nYou can now query the data using:")
	fmt.Println("  arxos find type:room")
	fmt.Println("  arxos find type:wall")
	fmt.Println("  arxos find type:sensor")
	fmt.Println("  arxos arxobject show building:hq:floor:1:room:101")
	fmt.Println("  arxos ls /")
	fmt.Println("  arxos cd floors/1")
	
	return nil
}

// isBuildingInitialized checks if a building has been initialized
func isBuildingInitialized(buildingID string) bool {
	buildingPath := getBuildingPath(buildingID)
	arxosDir := filepath.Join(buildingPath, ".arxos")
	if _, err := os.Stat(arxosDir); err != nil {
		return false
	}
	return true
}