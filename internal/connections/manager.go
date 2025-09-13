package connections

import (
	"context"
	"fmt"
	
	"github.com/joelpate/arxos/internal/database"
	"github.com/joelpate/arxos/internal/common/logger"
)

// Manager manages equipment connections and relationships
type Manager struct {
	db    database.DB
	graph *Graph
}

// NewManager creates a new connection manager
func NewManager(db database.DB) *Manager {
	return &Manager{
		db:    db,
		graph: NewGraph(db),
	}
}

// GetDownstream returns all equipment IDs downstream from the given ID
func (m *Manager) GetDownstream(equipmentID string) []string {
	ctx := context.Background()
	connections, err := m.graph.GetConnections(ctx, equipmentID, Downstream)
	if err != nil {
		logger.Error("Failed to get downstream connections: %v", err)
		return []string{}
	}
	
	ids := make([]string, 0, len(connections))
	for _, conn := range connections {
		ids = append(ids, conn.ToID)
	}
	return ids
}

// GetUpstream returns all equipment IDs upstream from the given ID
func (m *Manager) GetUpstream(equipmentID string) []string {
	ctx := context.Background()
	connections, err := m.graph.GetConnections(ctx, equipmentID, Upstream)
	if err != nil {
		logger.Error("Failed to get upstream connections: %v", err)
		return []string{}
	}
	
	ids := make([]string, 0, len(connections))
	for _, conn := range connections {
		ids = append(ids, conn.FromID)
	}
	return ids
}

// GetConnectionType returns the type of connection between two equipment
func (m *Manager) GetConnectionType(fromID, toID string) string {
	ctx := context.Background()
	conn, err := m.graph.GetConnection(ctx, fromID, toID)
	if err != nil {
		return "unknown"
	}
	return string(conn.ConnectionType)
}

// AddConnection creates a new connection between equipment
func (m *Manager) AddConnection(fromID, toID string, connType ConnectionType) error {
	ctx := context.Background()
	conn := &Connection{
		FromID:         fromID,
		ToID:           toID,
		ConnectionType: connType,
	}
	return m.graph.AddConnection(ctx, *conn)
}

// RemoveConnection removes a connection between equipment
func (m *Manager) RemoveConnection(fromID, toID string, connType ConnectionType) error {
	ctx := context.Background()
	return m.graph.RemoveConnection(ctx, fromID, toID, connType)
}

// GetAllConnections returns all connections in the system
func (m *Manager) GetAllConnections() ([]*Connection, error) {
	ctx := context.Background()
	return m.graph.GetAllConnections(ctx)
}

// TraceCircuit traces an electrical circuit from source to all endpoints
func (m *Manager) TraceCircuit(sourceID string) ([]string, error) {
	path := []string{sourceID}
	visited := make(map[string]bool)
	visited[sourceID] = true
	
	var trace func(id string)
	trace = func(id string) {
		downstream := m.GetDownstream(id)
		for _, nextID := range downstream {
			if !visited[nextID] {
				visited[nextID] = true
				path = append(path, nextID)
				trace(nextID)
			}
		}
	}
	
	trace(sourceID)
	return path, nil
}

// FindPath finds the shortest path between two equipment
func (m *Manager) FindPath(fromID, toID string) ([]string, error) {
	// Simple BFS implementation
	queue := [][]string{{fromID}}
	visited := make(map[string]bool)
	visited[fromID] = true
	
	for len(queue) > 0 {
		path := queue[0]
		queue = queue[1:]
		
		current := path[len(path)-1]
		if current == toID {
			return path, nil
		}
		
		// Check all connections
		downstream := m.GetDownstream(current)
		upstream := m.GetUpstream(current)
		
		neighbors := append(downstream, upstream...)
		for _, next := range neighbors {
			if !visited[next] {
				visited[next] = true
				newPath := append([]string{}, path...)
				newPath = append(newPath, next)
				queue = append(queue, newPath)
			}
		}
	}
	
	return nil, fmt.Errorf("no path found from %s to %s", fromID, toID)
}

// ConnectionPoint represents a point in a connection path
type ConnectionPoint struct {
	X, Y float64
}

// GetConnectionPath returns the geometric path points for a connection
func (m *Manager) GetConnectionPath(connectionID string) ([]ConnectionPoint, error) {
	// For now, generate a simple path based on equipment positions
	// In a real implementation, this would query stored path data
	
	// Parse connection ID to get from/to equipment
	// Assuming format "fromID->toID" or similar
	parts := []string{connectionID} // Simplified for now
	if len(parts) < 2 {
		return nil, fmt.Errorf("invalid connection ID format")
	}
	
	// Get equipment positions (this is a simplified implementation)
	// In reality, we'd need to access equipment data or have stored path points
	points := []ConnectionPoint{
		{X: 0, Y: 0},   // Start point
		{X: 10, Y: 10}, // End point
	}
	
	return points, nil
}

// ConnectionStatistics holds connection system statistics
type ConnectionStatistics struct {
	TotalConnections  int     `json:"total_connections"`
	ActiveConnections int     `json:"active_connections"`
	FailedConnections int     `json:"failed_connections"`
	AverageLatency    float64 `json:"average_latency_ms"`
	ThroughputMbps    float64 `json:"throughput_mbps"`
	ErrorRate         float64 `json:"error_rate"`
}

// GetStatistics returns current connection system statistics
func (m *Manager) GetStatistics() ConnectionStatistics {
	connections, err := m.GetAllConnections()
	if err != nil {
		logger.Warn("Failed to get connections for statistics: %v", err)
		return ConnectionStatistics{}
	}
	
	total := len(connections)
	active := 0
	failed := 0
	
	// Count active and failed connections
	for _, conn := range connections {
		if conn.IsActive {
			active++
		} else {
			failed++
		}
	}
	
	// Calculate error rate
	errorRate := 0.0
	if total > 0 {
		errorRate = (float64(failed) / float64(total)) * 100
	}
	
	return ConnectionStatistics{
		TotalConnections:  total,
		ActiveConnections: active,
		FailedConnections: failed,
		AverageLatency:    2.5,  // Mock latency in ms
		ThroughputMbps:    125.0, // Mock throughput
		ErrorRate:         errorRate,
	}
}