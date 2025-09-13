// Package navigation provides multi-floor building navigation
package navigation

import (
	"fmt"
	"math"
	"strings"

	"github.com/joelpate/arxos/internal/common/logger"
	"github.com/joelpate/arxos/pkg/models"
)

// MultiFloorNavigator handles navigation across multiple building floors
type MultiFloorNavigator struct {
	floors        map[int]*models.FloorPlan
	currentFloor  int
	currentRoom   string
	connections   map[string]FloorConnection
	elevators     []Elevator
	stairs        []Stairway
}

// FloorConnection represents a connection between floors
type FloorConnection struct {
	ID         string
	Type       ConnectionType
	FromFloor  int
	ToFloor    int
	FromRoom   string
	ToRoom     string
	Location   models.Point
	Accessible bool
}

// ConnectionType defines types of vertical connections
type ConnectionType string

const (
	ConnectionElevator   ConnectionType = "elevator"
	ConnectionStairs     ConnectionType = "stairs"
	ConnectionEscalator  ConnectionType = "escalator"
	ConnectionRamp       ConnectionType = "ramp"
	ConnectionLadder     ConnectionType = "ladder"
)

// Elevator represents an elevator system
type Elevator struct {
	ID           string
	Name         string
	Floors       []int // Floors served
	CurrentFloor int
	Capacity     int
	Status       string
	Location     models.Point
}

// Stairway represents a stairway between floors
type Stairway struct {
	ID         string
	Name       string
	StartFloor int
	EndFloor   int
	Type       string // "emergency", "main", "service"
	Width      float64
	Location   models.Point
}

// NewMultiFloorNavigator creates a new multi-floor navigation system
func NewMultiFloorNavigator() *MultiFloorNavigator {
	return &MultiFloorNavigator{
		floors:       make(map[int]*models.FloorPlan),
		connections:  make(map[string]FloorConnection),
		elevators:    []Elevator{},
		stairs:      []Stairway{},
		currentFloor: 1,
	}
}

// AddFloor adds a floor plan to the navigation system
func (n *MultiFloorNavigator) AddFloor(level int, plan *models.FloorPlan) {
	n.floors[level] = plan
	logger.Debug("Added floor %d: %s", level, plan.Name)
}

// AddElevator adds an elevator to the system
func (n *MultiFloorNavigator) AddElevator(elevator Elevator) {
	n.elevators = append(n.elevators, elevator)
	
	// Create connections for each floor pair the elevator serves
	for i := 0; i < len(elevator.Floors)-1; i++ {
		for j := i + 1; j < len(elevator.Floors); j++ {
			connID := fmt.Sprintf("elev_%s_%d_%d", elevator.ID, elevator.Floors[i], elevator.Floors[j])
			conn := FloorConnection{
				ID:         connID,
				Type:       ConnectionElevator,
				FromFloor:  elevator.Floors[i],
				ToFloor:    elevator.Floors[j],
				Location:   elevator.Location,
				Accessible: elevator.Status == "operational",
			}
			n.connections[connID] = conn
		}
	}
	
	logger.Debug("Added elevator %s serving floors %v", elevator.Name, elevator.Floors)
}

// AddStairway adds a stairway to the system
func (n *MultiFloorNavigator) AddStairway(stair Stairway) {
	n.stairs = append(n.stairs, stair)
	
	// Create connections for each floor the stairs connect
	if stair.StartFloor < stair.EndFloor {
		for floor := stair.StartFloor; floor < stair.EndFloor; floor++ {
			connID := fmt.Sprintf("stair_%s_%d_%d", stair.ID, floor, floor+1)
			conn := FloorConnection{
				ID:         connID,
				Type:       ConnectionStairs,
				FromFloor:  floor,
				ToFloor:    floor + 1,
				Location:   stair.Location,
				Accessible: true,
			}
			n.connections[connID] = conn
		}
	}
	
	logger.Debug("Added stairway %s from floor %d to %d", stair.Name, stair.StartFloor, stair.EndFloor)
}

// NavigateToFloor moves to a specific floor
func (n *MultiFloorNavigator) NavigateToFloor(targetFloor int) ([]NavigationStep, error) {
	if targetFloor == n.currentFloor {
		return []NavigationStep{}, nil
	}
	
	if _, exists := n.floors[targetFloor]; !exists {
		return nil, fmt.Errorf("floor %d does not exist", targetFloor)
	}
	
	// Find available paths to target floor
	paths := n.findPaths(n.currentFloor, targetFloor)
	if len(paths) == 0 {
		return nil, fmt.Errorf("no path found from floor %d to floor %d", n.currentFloor, targetFloor)
	}
	
	// Choose the best path (shortest with preference for elevators)
	bestPath := n.selectBestPath(paths)
	
	// Convert to navigation steps
	steps := n.pathToSteps(bestPath)
	
	// Update current floor
	n.currentFloor = targetFloor
	
	return steps, nil
}

// NavigationStep represents a single navigation instruction
type NavigationStep struct {
	Action      string
	Direction   string
	Target      string
	Distance    float64
	FloorChange int
	Details     string
}

// findPaths finds all possible paths between floors
func (n *MultiFloorNavigator) findPaths(fromFloor, toFloor int) [][]FloorConnection {
	var paths [][]FloorConnection
	visited := make(map[int]bool)
	currentPath := []FloorConnection{}
	
	n.dfs(fromFloor, toFloor, visited, currentPath, &paths)
	
	return paths
}

// dfs performs depth-first search to find paths
func (n *MultiFloorNavigator) dfs(current, target int, visited map[int]bool, path []FloorConnection, paths *[][]FloorConnection) {
	if current == target {
		// Found a path
		pathCopy := make([]FloorConnection, len(path))
		copy(pathCopy, path)
		*paths = append(*paths, pathCopy)
		return
	}
	
	visited[current] = true
	defer func() { visited[current] = false }()
	
	// Check all connections from current floor
	for _, conn := range n.connections {
		var nextFloor int
		if conn.FromFloor == current && !visited[conn.ToFloor] {
			nextFloor = conn.ToFloor
		} else if conn.ToFloor == current && !visited[conn.FromFloor] {
			nextFloor = conn.FromFloor
		} else {
			continue
		}
		
		if conn.Accessible {
			path = append(path, conn)
			n.dfs(nextFloor, target, visited, path, paths)
			path = path[:len(path)-1]
		}
	}
}

// selectBestPath chooses the optimal path
func (n *MultiFloorNavigator) selectBestPath(paths [][]FloorConnection) []FloorConnection {
	if len(paths) == 0 {
		return nil
	}
	
	bestPath := paths[0]
	bestScore := n.scorePath(bestPath)
	
	for _, path := range paths[1:] {
		score := n.scorePath(path)
		if score < bestScore {
			bestScore = score
			bestPath = path
		}
	}
	
	return bestPath
}

// scorePath calculates a score for a path (lower is better)
func (n *MultiFloorNavigator) scorePath(path []FloorConnection) float64 {
	score := 0.0
	
	for _, conn := range path {
		switch conn.Type {
		case ConnectionElevator:
			score += 1.0 // Preferred
		case ConnectionEscalator:
			score += 1.5
		case ConnectionStairs:
			score += 2.0 + math.Abs(float64(conn.ToFloor-conn.FromFloor))
		case ConnectionRamp:
			score += 2.5
		case ConnectionLadder:
			score += 5.0 // Least preferred
		}
	}
	
	return score
}

// pathToSteps converts a path to navigation steps
func (n *MultiFloorNavigator) pathToSteps(path []FloorConnection) []NavigationStep {
	var steps []NavigationStep
	
	for _, conn := range path {
		step := NavigationStep{
			FloorChange: conn.ToFloor - conn.FromFloor,
		}
		
		switch conn.Type {
		case ConnectionElevator:
			elevator := n.findElevator(conn.ID)
			if elevator != nil {
				step.Action = "Take elevator"
				step.Target = elevator.Name
				step.Details = fmt.Sprintf("From floor %d to floor %d", conn.FromFloor, conn.ToFloor)
			}
		case ConnectionStairs:
			stair := n.findStairway(conn.ID)
			if stair != nil {
				step.Action = "Take stairs"
				step.Target = stair.Name
				if conn.ToFloor > conn.FromFloor {
					step.Direction = "up"
				} else {
					step.Direction = "down"
				}
				step.Details = fmt.Sprintf("%s %d floor(s)", step.Direction, int(math.Abs(float64(conn.ToFloor-conn.FromFloor))))
			}
		}
		
		steps = append(steps, step)
	}
	
	return steps
}

// findElevator finds an elevator by connection ID
func (n *MultiFloorNavigator) findElevator(connID string) *Elevator {
	for i := range n.elevators {
		if strings.Contains(connID, n.elevators[i].ID) {
			return &n.elevators[i]
		}
	}
	return nil
}

// findStairway finds a stairway by connection ID
func (n *MultiFloorNavigator) findStairway(connID string) *Stairway {
	for i := range n.stairs {
		if strings.Contains(connID, n.stairs[i].ID) {
			return &n.stairs[i]
		}
	}
	return nil
}

// GetCurrentFloor returns the current floor number
func (n *MultiFloorNavigator) GetCurrentFloor() int {
	return n.currentFloor
}

// GetCurrentRoom returns the current room ID
func (n *MultiFloorNavigator) GetCurrentRoom() string {
	return n.currentRoom
}

// SetCurrentLocation sets the current floor and room
func (n *MultiFloorNavigator) SetCurrentLocation(floor int, room string) error {
	if _, exists := n.floors[floor]; !exists {
		return fmt.Errorf("floor %d does not exist", floor)
	}
	
	n.currentFloor = floor
	n.currentRoom = room
	return nil
}

// ListFloors returns all available floors
func (n *MultiFloorNavigator) ListFloors() []int {
	floors := make([]int, 0, len(n.floors))
	for floor := range n.floors {
		floors = append(floors, floor)
	}
	return floors
}

// GetFloorPlan returns the floor plan for a specific level
func (n *MultiFloorNavigator) GetFloorPlan(floor int) (*models.FloorPlan, error) {
	if plan, exists := n.floors[floor]; exists {
		return plan, nil
	}
	return nil, fmt.Errorf("floor %d not found", floor)
}

// FindEquipmentAcrossFloors searches for equipment across all floors
func (n *MultiFloorNavigator) FindEquipmentAcrossFloors(equipmentType string) []FloorEquipment {
	var results []FloorEquipment
	
	for floor, plan := range n.floors {
		for _, equip := range plan.Equipment {
			if equip.Type == equipmentType {
				results = append(results, FloorEquipment{
					Floor:     floor,
					Equipment: equip,
				})
			}
		}
	}
	
	return results
}

// FloorEquipment represents equipment with its floor location
type FloorEquipment struct {
	Floor     int
	Equipment models.Equipment
}

// GetVerticalPath finds vertical connections between equipment on different floors
func (n *MultiFloorNavigator) GetVerticalPath(fromEquipID string, fromFloor int, toEquipID string, toFloor int) ([]NavigationStep, error) {
	// First navigate between floors
	floorSteps, err := n.NavigateToFloor(toFloor)
	if err != nil {
		return nil, err
	}
	
	// Add equipment-specific navigation at each end
	var steps []NavigationStep
	
	// Navigate to vertical connection on current floor
	if fromFloor != toFloor {
		steps = append(steps, NavigationStep{
			Action:    "Navigate to",
			Target:    "vertical connection",
			Direction: "towards stairs/elevator",
			Details:   fmt.Sprintf("From %s", fromEquipID),
		})
	}
	
	// Add floor navigation steps
	steps = append(steps, floorSteps...)
	
	// Navigate from vertical connection to target equipment
	if fromFloor != toFloor {
		steps = append(steps, NavigationStep{
			Action:    "Navigate to",
			Target:    toEquipID,
			Direction: "from stairs/elevator",
			Details:   fmt.Sprintf("On floor %d", toFloor),
		})
	}
	
	return steps, nil
}

// RenderMultiFloorMap creates an ASCII representation of multiple floors
func (n *MultiFloorNavigator) RenderMultiFloorMap() string {
	var output strings.Builder
	
	// Sort floors for consistent display
	floors := n.ListFloors()
	if len(floors) == 0 {
		return "No floors available"
	}
	
	// Simple stacked representation
	for i := len(floors) - 1; i >= 0; i-- {
		floor := floors[i]
		plan := n.floors[floor]
		
		output.WriteString(fmt.Sprintf("\n━━━ Floor %d: %s ━━━\n", floor, plan.Name))
		
		// Show rooms and equipment count
		output.WriteString(fmt.Sprintf("  Rooms: %d | Equipment: %d\n", len(plan.Rooms), len(plan.Equipment)))
		
		// Show vertical connections
		var elevatorCount, stairCount int
		for _, conn := range n.connections {
			if conn.FromFloor == floor || conn.ToFloor == floor {
				switch conn.Type {
				case ConnectionElevator:
					elevatorCount++
				case ConnectionStairs:
					stairCount++
				}
			}
		}
		
		if elevatorCount > 0 || stairCount > 0 {
			output.WriteString(fmt.Sprintf("  Connections: %d elevators, %d stairs\n", elevatorCount/2, stairCount))
		}
		
		// Mark current floor
		if floor == n.currentFloor {
			output.WriteString("  >>> YOU ARE HERE <<<\n")
		}
	}
	
	return output.String()
}