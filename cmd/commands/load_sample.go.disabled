package commands

import (
	"fmt"
	"math/rand"
	
	"github.com/arxos/arxos/cmd/cgo"
	"github.com/spf13/cobra"
)

// loadSampleCmd represents the load-sample command
var loadSampleCmd = &cobra.Command{
	Use:   "load-sample",
	Short: "Load sample ArxObject data for testing",
	Long: `Load a sample building with various ArxObjects for testing AQL queries.
	
This creates a hierarchical building structure with floors, rooms, walls, doors, and other components.`,
	RunE: runLoadSample,
}

func init() {
	RootCmd.AddCommand(loadSampleCmd)
}

func runLoadSample(cmd *cobra.Command, args []string) error {
	// Initialize CGO ArxObject system
	if err := cgo.Initialize(map[string]interface{}{"log_level": 2}); err != nil {
		return fmt.Errorf("failed to initialize ArxObject system: %w", err)
	}
	defer cgo.Cleanup()
	
	fmt.Println("Loading sample building data...")
	
	// Create main building
	building, err := cgo.CreateObject(
		"HQ Building",
		"/building/hq",
		cgo.TypeBuilding,
		0, 0, 0,
	)
	if err != nil {
		return fmt.Errorf("failed to create building: %w", err)
	}
	fmt.Printf("Created building: ID=%d, Name=%s\n", building.ID, building.Name)
	
	// Create 3 floors
	for floor := 1; floor <= 3; floor++ {
		floorObj, err := cgo.CreateObject(
			fmt.Sprintf("Floor %d", floor),
			fmt.Sprintf("/building/hq/floor/%d", floor),
			cgo.TypeFloor,
			0, 0, int32(floor*3000), // Each floor is 3 meters high
		)
		if err != nil {
			return fmt.Errorf("failed to create floor %d: %w", floor, err)
		}
		fmt.Printf("  Created floor %d: ID=%d\n", floor, floorObj.ID)
		
		// Create 4 rooms per floor
		for room := 1; room <= 4; room++ {
			roomX := int32((room-1)%2) * 5000 // Arrange rooms in 2x2 grid
			roomY := int32((room-1)/2) * 4000
			
			roomObj, err := cgo.CreateObject(
				fmt.Sprintf("Room %d%02d", floor, room),
				fmt.Sprintf("/building/hq/floor/%d/room/%d", floor, room),
				cgo.TypeRoom,
				roomX, roomY, int32(floor*3000),
			)
			if err != nil {
				return fmt.Errorf("failed to create room: %w", err)
			}
			
			// Set confidence based on floor (lower floors have higher confidence)
			roomObj.Confidence = float32(1.0 - float32(floor-1)*0.15)
			roomObj.IsValidated = (floor == 1) // Only first floor is validated
			cgo.UpdateObject(roomObj)
			
			fmt.Printf("    Created room %d%02d: ID=%d, Confidence=%.2f\n", 
				floor, room, roomObj.ID, roomObj.Confidence)
			
			// Create walls for each room
			wallPositions := []struct {
				name   string
				x, y   int32
				width  int32
				height int32
			}{
				{"north", roomX, roomY, 5000, 200},
				{"south", roomX, roomY + 3800, 5000, 200},
				{"east", roomX + 4800, roomY, 200, 4000},
				{"west", roomX, roomY, 200, 4000},
			}
			
			for _, wall := range wallPositions {
				wallObj, err := cgo.CreateObject(
					fmt.Sprintf("Wall-%s-%d%02d", wall.name, floor, room),
					fmt.Sprintf("/building/hq/floor/%d/room/%d/wall/%s", floor, room, wall.name),
					cgo.TypeWall,
					wall.x, wall.y, int32(floor*3000),
				)
				if err != nil {
					continue
				}
				wallObj.Width = wall.width
				wallObj.Height = 2400 // 2.4m high walls
				wallObj.Depth = wall.height
				wallObj.Confidence = roomObj.Confidence - rand.Float32()*0.1
				cgo.UpdateObject(wallObj)
			}
			
			// Add a door to each room
			doorObj, err := cgo.CreateObject(
				fmt.Sprintf("Door-%d%02d", floor, room),
				fmt.Sprintf("/building/hq/floor/%d/room/%d/door/main", floor, room),
				cgo.TypeDoor,
				roomX+2000, roomY, int32(floor*3000),
			)
			if err == nil {
				doorObj.Width = 900
				doorObj.Height = 2100
				doorObj.Depth = 50
				doorObj.Confidence = roomObj.Confidence
				cgo.UpdateObject(doorObj)
			}
			
			// Add windows to some rooms
			if room%2 == 0 {
				windowObj, err := cgo.CreateObject(
					fmt.Sprintf("Window-%d%02d", floor, room),
					fmt.Sprintf("/building/hq/floor/%d/room/%d/window/main", floor, room),
					cgo.TypeWindow,
					roomX+4800, roomY+1500, int32(floor*3000+900),
				)
				if err == nil {
					windowObj.Width = 200
					windowObj.Height = 1500
					windowObj.Depth = 1200
					windowObj.Confidence = roomObj.Confidence - 0.05
					cgo.UpdateObject(windowObj)
				}
			}
		}
		
		// Add equipment on each floor
		equipmentTypes := []string{"hvac", "electrical", "plumbing"}
		for i, eqType := range equipmentTypes {
			equipment, err := cgo.CreateObject(
				fmt.Sprintf("%s-unit-%d", eqType, floor),
				fmt.Sprintf("/building/hq/floor/%d/equipment/%s", floor, eqType),
				cgo.TypeEquipment,
				int32(i*2000), 8000, int32(floor*3000),
			)
			if err == nil {
				equipment.Confidence = 0.75
				equipment.Properties = map[string]interface{}{
					"type":   eqType,
					"status": "operational",
					"power":  rand.Intn(5000) + 1000,
				}
				cgo.UpdateObject(equipment)
				fmt.Printf("    Created equipment: %s\n", equipment.Name)
			}
		}
		
		// Add sensors
		for i := 1; i <= 3; i++ {
			sensor, err := cgo.CreateObject(
				fmt.Sprintf("sensor-%d-%d", floor, i),
				fmt.Sprintf("/building/hq/floor/%d/sensor/%d", floor, i),
				cgo.TypeSensor,
				int32(rand.Intn(10000)), int32(rand.Intn(8000)), int32(floor*3000+2500),
			)
			if err == nil {
				sensor.Confidence = 0.95
				sensor.IsValidated = true
				sensor.Properties = map[string]interface{}{
					"type":        "temperature",
					"reading":     20 + rand.Float32()*5,
					"unit":        "celsius",
					"last_update": "2024-08-26T12:00:00Z",
				}
				cgo.UpdateObject(sensor)
			}
		}
	}
	
	// Create building systems
	systems := []struct {
		name string
		path string
	}{
		{"HVAC System", "/building/hq/system/hvac"},
		{"Electrical System", "/building/hq/system/electrical"},
		{"Security System", "/building/hq/system/security"},
		{"Fire Safety System", "/building/hq/system/fire"},
	}
	
	for _, sys := range systems {
		sysObj, err := cgo.CreateObject(
			sys.name,
			sys.path,
			cgo.TypeSystem,
			0, 0, 0,
		)
		if err == nil {
			sysObj.Confidence = 0.85
			sysObj.Properties = map[string]interface{}{
				"status":       "active",
				"maintenance":  "scheduled",
				"last_checked": "2024-08-01",
			}
			cgo.UpdateObject(sysObj)
			fmt.Printf("  Created system: %s\n", sysObj.Name)
		}
	}
	
	// Get statistics
	stats := cgo.GetPerformanceStats()
	fmt.Printf("\n=== Sample Data Loaded Successfully ===\n")
	fmt.Printf("Total objects created: %d\n", stats.TotalObjects)
	fmt.Printf("Average create time: %.2f ms\n", stats.AvgCreateTimeMS)
	fmt.Printf("Memory usage: %d bytes\n", stats.MemoryUsageBytes)
	
	fmt.Println("\nYou can now query the data using AQL, for example:")
	fmt.Println("  arxos query select \"* FROM wall WHERE confidence > 0.7\"")
	fmt.Println("  arxos query select \"* FROM room WHERE validated = true\"")
	fmt.Println("  arxos query select \"* FROM sensor\"")
	fmt.Println("  arxos query select \"id, name, path FROM equipment\"")
	
	return nil
}