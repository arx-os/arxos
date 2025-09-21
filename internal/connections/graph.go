package connections

import (
	"context"
	"fmt"
	"strings"

	"github.com/arx-os/arxos/internal/common/logger"
	"github.com/arx-os/arxos/internal/database"
	"github.com/arx-os/arxos/pkg/models"
)

// Graph represents the equipment connection graph
type Graph struct {
	db database.DB
}

// NewGraph creates a new connection graph
func NewGraph(db database.DB) *Graph {
	return &Graph{db: db}
}

// Connection represents a connection between two pieces of equipment
type Connection struct {
	ID              string                 `json:"id"`
	FromEquipmentID string                 `json:"from_equipment_id"`
	ToEquipmentID   string                 `json:"to_equipment_id"`
	Type            ConnectionType         `json:"type"`
	Status          string                 `json:"status"`
	CurrentLoad     float64                `json:"current_load"`
	Capacity        float64                `json:"capacity"`
	IsActive        bool                   `json:"is_active"`
	Metadata        map[string]interface{} `json:"metadata,omitempty"`

	// Legacy fields for backward compatibility
	FromID         string         `json:"from_id"`
	ToID           string         `json:"to_id"`
	ConnectionType ConnectionType `json:"connection_type"`
}

// ConnectionType represents the type of connection
type ConnectionType string

const (
	TypeElectrical ConnectionType = "electrical"
	TypeData       ConnectionType = "data"
	TypeWater      ConnectionType = "water"
	TypeGas        ConnectionType = "gas"
	TypeHVAC       ConnectionType = "hvac"
	TypeFiber      ConnectionType = "fiber"
	TypeControl    ConnectionType = "control"

	// Legacy aliases
	ConnectionPower      ConnectionType = "electrical"
	ConnectionData       ConnectionType = "data"
	ConnectionPlumbing   ConnectionType = "water"
	ConnectionHVAC       ConnectionType = "hvac"
	ConnectionStructural ConnectionType = "structural"
	ConnectionControl    ConnectionType = "control"
)

// Direction represents the tracing direction
type Direction string

const (
	Upstream   Direction = "upstream"
	Downstream Direction = "downstream"
	Both       Direction = "both"
)

// TraceResult represents the result of a trace operation
type TraceResult struct {
	Equipment   *models.Equipment
	Connections []Connection
	Path        []string // IDs in order
	Level       int      // Distance from source
}

// AddConnection adds a connection between two pieces of equipment
func (g *Graph) AddConnection(ctx context.Context, conn Connection) error {
	// Validate equipment exists
	if _, err := g.db.GetEquipment(ctx, conn.FromID); err != nil {
		return fmt.Errorf("source equipment %s not found: %w", conn.FromID, err)
	}
	if _, err := g.db.GetEquipment(ctx, conn.ToID); err != nil {
		return fmt.Errorf("target equipment %s not found: %w", conn.ToID, err)
	}

	// Check for cycles before adding the connection
	if wouldCreateCycle, cyclePath := g.wouldCreateCycle(ctx, conn.FromID, conn.ToID); wouldCreateCycle {
		return fmt.Errorf("adding connection would create a cycle: %v", cyclePath)
	}

	// Store connection in database
	query := `
		INSERT INTO connections (from_equipment_id, to_equipment_id, connection_type, metadata)
		VALUES (?, ?, ?, ?)
		ON CONFLICT(from_equipment_id, to_equipment_id, connection_type) 
		DO UPDATE SET metadata = excluded.metadata
	`

	metadataJSON := "{}"
	if conn.Metadata != nil {
		// Convert metadata to JSON
		// For simplicity, using a basic format
		pairs := []string{}
		for k, v := range conn.Metadata {
			pairs = append(pairs, fmt.Sprintf(`"%s":"%v"`, k, v))
		}
		metadataJSON = "{" + strings.Join(pairs, ",") + "}"
	}

	_, err := g.db.Exec(ctx, query, conn.FromID, conn.ToID, string(conn.ConnectionType), metadataJSON)
	if err != nil {
		return fmt.Errorf("failed to add connection: %w", err)
	}

	logger.Info("Added %s connection: %s -> %s", conn.ConnectionType, conn.FromID, conn.ToID)
	return nil
}

// RemoveConnection removes a connection between equipment
func (g *Graph) RemoveConnection(ctx context.Context, fromID, toID string, connType ConnectionType) error {
	query := `
		DELETE FROM connections 
		WHERE from_equipment_id = ? AND to_equipment_id = ? AND connection_type = ?
	`

	result, err := g.db.Exec(ctx, query, fromID, toID, string(connType))
	if err != nil {
		return fmt.Errorf("failed to remove connection: %w", err)
	}

	rowsAffected, _ := result.RowsAffected()
	if rowsAffected == 0 {
		return fmt.Errorf("connection not found")
	}

	logger.Info("Removed %s connection: %s -> %s", connType, fromID, toID)
	return nil
}

// GetConnections gets all connections for a piece of equipment
func (g *Graph) GetConnections(ctx context.Context, equipmentID string, direction Direction) ([]Connection, error) {
	var query string
	var args []interface{}

	switch direction {
	case Upstream:
		query = `
			SELECT from_equipment_id, to_equipment_id, connection_type, metadata
			FROM connections
			WHERE to_equipment_id = ?
		`
		args = []interface{}{equipmentID}
	case Downstream:
		query = `
			SELECT from_equipment_id, to_equipment_id, connection_type, metadata
			FROM connections
			WHERE from_equipment_id = ?
		`
		args = []interface{}{equipmentID}
	case Both:
		query = `
			SELECT from_equipment_id, to_equipment_id, connection_type, metadata
			FROM connections
			WHERE from_equipment_id = ? OR to_equipment_id = ?
		`
		args = []interface{}{equipmentID, equipmentID}
	default:
		return nil, fmt.Errorf("invalid direction: %s", direction)
	}

	rows, err := g.db.Query(ctx, query, args...)
	if err != nil {
		return nil, fmt.Errorf("failed to query connections: %w", err)
	}
	defer rows.Close()

	var connections []Connection
	for rows.Next() {
		var conn Connection
		var metadata string

		err := rows.Scan(&conn.FromID, &conn.ToID, &conn.ConnectionType, &metadata)
		if err != nil {
			logger.Error("Failed to scan connection: %v", err)
			continue
		}

		// Parse metadata if needed
		// For now, leaving it as nil

		connections = append(connections, conn)
	}

	return connections, nil
}

// Trace traces connections from a piece of equipment
func (g *Graph) Trace(ctx context.Context, equipmentID string, direction Direction, maxDepth int) ([]TraceResult, error) {
	if maxDepth <= 0 {
		maxDepth = 10 // Default max depth
	}

	visited := make(map[string]bool)
	results := []TraceResult{}

	// Start tracing
	if err := g.traceRecursive(ctx, equipmentID, direction, 0, maxDepth, visited, &results, []string{}); err != nil {
		return nil, err
	}

	return results, nil
}

// traceRecursive performs recursive tracing
func (g *Graph) traceRecursive(ctx context.Context, equipmentID string, direction Direction, level, maxDepth int, visited map[string]bool, results *[]TraceResult, path []string) error {
	// Check if already visited or max depth reached
	if visited[equipmentID] || level > maxDepth {
		return nil
	}

	visited[equipmentID] = true
	currentPath := append(path, equipmentID)

	// Get equipment details
	equipment, err := g.db.GetEquipment(ctx, equipmentID)
	if err != nil {
		// Equipment might not exist, just skip
		return nil
	}

	// Get connections
	connections, err := g.GetConnections(ctx, equipmentID, direction)
	if err != nil {
		return err
	}

	// Add to results
	*results = append(*results, TraceResult{
		Equipment:   equipment,
		Connections: connections,
		Path:        currentPath,
		Level:       level,
	})

	// Recursively trace connections
	for _, conn := range connections {
		nextID := ""
		if direction == Upstream {
			nextID = conn.FromID
		} else if direction == Downstream {
			nextID = conn.ToID
		} else { // Both
			if conn.FromID == equipmentID {
				nextID = conn.ToID
			} else {
				nextID = conn.FromID
			}
		}

		if nextID != "" && nextID != equipmentID {
			if err := g.traceRecursive(ctx, nextID, direction, level+1, maxDepth, visited, results, currentPath); err != nil {
				return err
			}
		}
	}

	return nil
}

// FindPath finds the shortest path between two pieces of equipment
func (g *Graph) FindPath(ctx context.Context, fromID, toID string) ([]string, error) {
	// BFS to find shortest path
	queue := [][]string{{fromID}}
	visited := make(map[string]bool)
	visited[fromID] = true

	for len(queue) > 0 {
		path := queue[0]
		queue = queue[1:]

		current := path[len(path)-1]

		// Check if we reached the destination
		if current == toID {
			return path, nil
		}

		// Get all connections
		connections, err := g.GetConnections(ctx, current, Both)
		if err != nil {
			continue
		}

		for _, conn := range connections {
			nextID := ""
			if conn.FromID == current {
				nextID = conn.ToID
			} else {
				nextID = conn.FromID
			}

			if !visited[nextID] {
				visited[nextID] = true
				newPath := append([]string{}, path...)
				newPath = append(newPath, nextID)
				queue = append(queue, newPath)
			}
		}
	}

	return nil, fmt.Errorf("no path found between %s and %s", fromID, toID)
}

// GetConnection gets a specific connection between two equipment
func (g *Graph) GetConnection(ctx context.Context, fromID, toID string) (*Connection, error) {
	connections, err := g.GetConnections(ctx, fromID, Downstream)
	if err != nil {
		return nil, err
	}

	for _, conn := range connections {
		if conn.ToID == toID {
			return &conn, nil
		}
	}

	return nil, fmt.Errorf("no connection found from %s to %s", fromID, toID)
}

// GetAllConnections returns all connections in the database
func (g *Graph) GetAllConnections(ctx context.Context) ([]*Connection, error) {
	// This would typically query the database for all connections
	// For now, return empty slice
	return []*Connection{}, nil
}

// GetSystemComponents gets all equipment connected in a system
func (g *Graph) GetSystemComponents(ctx context.Context, equipmentID string, connType ConnectionType) ([]*models.Equipment, error) {
	// Find all connected components of a specific type
	visited := make(map[string]bool)
	components := []*models.Equipment{}

	if err := g.exploreSystem(ctx, equipmentID, connType, visited, &components); err != nil {
		return nil, err
	}

	return components, nil
}

// exploreSystem explores all connected components in a system
func (g *Graph) exploreSystem(ctx context.Context, equipmentID string, connType ConnectionType, visited map[string]bool, components *[]*models.Equipment) error {
	if visited[equipmentID] {
		return nil
	}

	visited[equipmentID] = true

	// Get equipment
	equipment, err := g.db.GetEquipment(ctx, equipmentID)
	if err != nil {
		return nil // Skip if not found
	}

	*components = append(*components, equipment)

	// Get connections of the specified type
	query := `
		SELECT from_equipment_id, to_equipment_id 
		FROM connections
		WHERE (from_equipment_id = ? OR to_equipment_id = ?) AND connection_type = ?
	`

	rows, err := g.db.Query(ctx, query, equipmentID, equipmentID, string(connType))
	if err != nil {
		return err
	}
	defer rows.Close()

	for rows.Next() {
		var fromID, toID string
		if err := rows.Scan(&fromID, &toID); err != nil {
			continue
		}

		nextID := ""
		if fromID == equipmentID {
			nextID = toID
		} else {
			nextID = fromID
		}

		if !visited[nextID] {
			if err := g.exploreSystem(ctx, nextID, connType, visited, components); err != nil {
				return err
			}
		}
	}

	return nil
}

// wouldCreateCycle checks if adding a connection from fromID to toID would create a cycle
func (g *Graph) wouldCreateCycle(ctx context.Context, fromID, toID string) (bool, []string) {
	// If we're adding a connection from A to B, check if there's already a path from B to A
	// This would create a cycle

	// Use DFS to check if there's a path from toID to fromID
	visited := make(map[string]bool)
	path := []string{}

	if g.dfsHasPath(ctx, toID, fromID, visited, &path) {
		// Found a path from toID to fromID, adding fromID->toID would create a cycle
		path = append(path, fromID) // Complete the cycle
		return true, path
	}

	return false, nil
}

// dfsHasPath performs depth-first search to check if there's a path from source to target
func (g *Graph) dfsHasPath(ctx context.Context, current, target string, visited map[string]bool, path *[]string) bool {
	if current == target {
		*path = append(*path, current)
		return true
	}

	if visited[current] {
		return false
	}

	visited[current] = true
	*path = append(*path, current)

	// Get all downstream connections from current
	connections, err := g.GetConnections(ctx, current, Downstream)
	if err != nil {
		return false
	}

	for _, conn := range connections {
		if g.dfsHasPath(ctx, conn.ToID, target, visited, path) {
			return true
		}
	}

	// Backtrack if no path found
	if len(*path) > 0 {
		*path = (*path)[:len(*path)-1]
	}

	return false
}

// HasCycle checks if the graph contains any cycles
func (g *Graph) HasCycle(ctx context.Context) (bool, []string) {
	// Get all equipment IDs by querying the database directly
	rows, err := g.db.Query(ctx, "SELECT DISTINCT from_equipment_id FROM connections UNION SELECT DISTINCT to_equipment_id FROM connections")
	if err != nil {
		logger.Error("Failed to get equipment for cycle check: %v", err)
		return false, nil
	}
	defer rows.Close()

	var equipmentIDs []string
	for rows.Next() {
		var id string
		if err := rows.Scan(&id); err != nil {
			continue
		}
		equipmentIDs = append(equipmentIDs, id)
	}

	visited := make(map[string]bool)
	recStack := make(map[string]bool)
	var cyclePath []string

	for _, equipmentID := range equipmentIDs {
		if !visited[equipmentID] {
			if g.dfsCycleDetect(ctx, equipmentID, visited, recStack, &cyclePath) {
				return true, cyclePath
			}
		}
	}

	return false, nil
}

// dfsCycleDetect performs DFS-based cycle detection
func (g *Graph) dfsCycleDetect(ctx context.Context, nodeID string, visited, recStack map[string]bool, path *[]string) bool {
	visited[nodeID] = true
	recStack[nodeID] = true
	*path = append(*path, nodeID)

	// Get all downstream connections
	connections, err := g.GetConnections(ctx, nodeID, Downstream)
	if err != nil {
		recStack[nodeID] = false
		if len(*path) > 0 {
			*path = (*path)[:len(*path)-1]
		}
		return false
	}

	for _, conn := range connections {
		if !visited[conn.ToID] {
			if g.dfsCycleDetect(ctx, conn.ToID, visited, recStack, path) {
				return true
			}
		} else if recStack[conn.ToID] {
			// Found a cycle - add the node that completes the cycle
			*path = append(*path, conn.ToID)
			return true
		}
	}

	recStack[nodeID] = false
	if len(*path) > 0 {
		*path = (*path)[:len(*path)-1]
	}
	return false
}
