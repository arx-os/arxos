package connections

import (
	"context"
	"fmt"
	"sort"

	"github.com/arx-os/arxos/internal/database"
	"github.com/arx-os/arxos/pkg/models"
)

// Analyzer provides intelligent analysis of equipment connections
type Analyzer struct {
	graph *Graph
	db    database.DB
}

// NewAnalyzer creates a new connection analyzer
func NewAnalyzer(db database.DB) *Analyzer {
	return &Analyzer{
		graph: NewGraph(db),
		db:    db,
	}
}

// ImpactAnalysis analyzes the impact of equipment failure
type ImpactAnalysis struct {
	EquipmentID        string
	DirectlyAffected   []*models.Equipment
	IndirectlyAffected []*models.Equipment
	TotalImpact        int
	CriticalPath       bool
	SystemsAffected    []ConnectionType
}

// CircuitLoad represents load analysis for electrical circuits
type CircuitLoad struct {
	CircuitID   string
	TotalLoad   float64
	MaxCapacity float64
	LoadPercent float64
	Equipment   []*models.Equipment
	Overloaded  bool
}

// AnalyzeImpact analyzes the impact of equipment failure
func (a *Analyzer) AnalyzeImpact(ctx context.Context, equipmentID string) (*ImpactAnalysis, error) {
	analysis := &ImpactAnalysis{
		EquipmentID: equipmentID,
	}

	// Get directly connected downstream equipment
	downstream, err := a.graph.Trace(ctx, equipmentID, Downstream, 1)
	if err != nil {
		return nil, err
	}

	for _, result := range downstream {
		if result.Level == 1 {
			analysis.DirectlyAffected = append(analysis.DirectlyAffected, result.Equipment)
		}
	}

	// Get all downstream equipment (indirect impact)
	allDownstream, err := a.graph.Trace(ctx, equipmentID, Downstream, 10)
	if err != nil {
		return nil, err
	}

	for _, result := range allDownstream {
		if result.Level > 1 {
			analysis.IndirectlyAffected = append(analysis.IndirectlyAffected, result.Equipment)
		}
	}

	analysis.TotalImpact = len(analysis.DirectlyAffected) + len(analysis.IndirectlyAffected)

	// Identify affected systems
	systemMap := make(map[ConnectionType]bool)
	connections, _ := a.graph.GetConnections(ctx, equipmentID, Both)
	for _, conn := range connections {
		systemMap[conn.ConnectionType] = true
	}

	for system := range systemMap {
		analysis.SystemsAffected = append(analysis.SystemsAffected, system)
	}

	// Check if this is on a critical path (no redundancy)
	analysis.CriticalPath = a.isOnCriticalPath(ctx, equipmentID)

	return analysis, nil
}

// isOnCriticalPath checks if equipment is on a critical path with no redundancy
func (a *Analyzer) isOnCriticalPath(ctx context.Context, equipmentID string) bool {
	// Check if removing this equipment breaks connectivity
	// For now, simplified: equipment with both upstream and downstream connections
	upstream, _ := a.graph.GetConnections(ctx, equipmentID, Upstream)
	downstream, _ := a.graph.GetConnections(ctx, equipmentID, Downstream)

	return len(upstream) > 0 && len(downstream) > 0
}

// AnalyzeCircuitLoad analyzes electrical circuit loads
func (a *Analyzer) AnalyzeCircuitLoad(ctx context.Context, circuitID string) (*CircuitLoad, error) {
	load := &CircuitLoad{
		CircuitID:   circuitID,
		MaxCapacity: 20.0, // Default 20A circuit
	}

	// Get all equipment on this circuit
	components, err := a.graph.GetSystemComponents(ctx, circuitID, ConnectionPower)
	if err != nil {
		return nil, err
	}

	load.Equipment = components

	// Calculate total load (simplified)
	for _, equip := range components {
		// Estimate load based on equipment type
		switch equip.Type {
		case "outlet":
			load.TotalLoad += 1.5 // 1.5A per outlet average
		case "light":
			load.TotalLoad += 0.5 // 0.5A per light
		case "switch":
			load.TotalLoad += 0.1 // Minimal load
		case "panel":
			load.TotalLoad += 0 // Panels don't consume
		default:
			load.TotalLoad += 1.0 // Default 1A
		}
	}

	load.LoadPercent = (load.TotalLoad / load.MaxCapacity) * 100
	load.Overloaded = load.LoadPercent > 80 // 80% threshold

	return load, nil
}

// FindRedundantPaths finds redundant paths between equipment
func (a *Analyzer) FindRedundantPaths(ctx context.Context, fromID, toID string) ([][]string, error) {
	paths := [][]string{}
	visited := make(map[string]bool)

	// DFS to find all paths
	currentPath := []string{}
	a.findAllPaths(ctx, fromID, toID, visited, currentPath, &paths)

	// Sort paths by length
	sort.Slice(paths, func(i, j int) bool {
		return len(paths[i]) < len(paths[j])
	})

	return paths, nil
}

// findAllPaths finds all paths between two nodes using DFS
func (a *Analyzer) findAllPaths(ctx context.Context, current, target string, visited map[string]bool, currentPath []string, paths *[][]string) {
	if current == target {
		// Found a path
		pathCopy := append([]string{}, currentPath...)
		pathCopy = append(pathCopy, target)
		*paths = append(*paths, pathCopy)
		return
	}

	visited[current] = true
	currentPath = append(currentPath, current)

	// Get all connections
	connections, _ := a.graph.GetConnections(ctx, current, Both)

	for _, conn := range connections {
		nextID := ""
		if conn.FromID == current {
			nextID = conn.ToID
		} else {
			nextID = conn.FromID
		}

		if !visited[nextID] {
			a.findAllPaths(ctx, nextID, target, visited, currentPath, paths)
		}
	}

	// Backtrack
	visited[current] = false
}

// FindFailurePoints finds single points of failure in the system
func (a *Analyzer) FindFailurePoints(ctx context.Context, floorPlanID string) ([]*models.Equipment, error) {
	failurePoints := []*models.Equipment{}

	// Get candidate equipment IDs on this floor plan
	queryIDs := `
        SELECT DISTINCT e.id 
        FROM equipment e
        WHERE e.floor_plan_id = ?
    `

	rows, err := a.db.Query(ctx, queryIDs, floorPlanID)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	// Collect IDs
	ids := make([]string, 0, 256)
	for rows.Next() {
		var id string
		if err := rows.Scan(&id); err == nil {
			ids = append(ids, id)
		}
	}

	if len(ids) == 0 {
		return failurePoints, nil
	}

	// Bulk-evaluate SOPF in SQL (heuristic similar to isSinglePointOfFailure)
	// Simplified: one upstream and >2 downstream connections
	// Note: uses LEFT JOINs and GROUP BY to prefilter candidates
	sopfQuery := `
        WITH conn AS (
            SELECT c.from_equipment_id, c.to_equipment_id
            FROM connections c
        ), stats AS (
            SELECT e.id,
                   SUM(CASE WHEN c1.to_equipment_id = e.id THEN 1 ELSE 0 END) AS upstream_cnt,
                   SUM(CASE WHEN c2.from_equipment_id = e.id THEN 1 ELSE 0 END) AS downstream_cnt
            FROM equipment e
            LEFT JOIN conn c1 ON c1.to_equipment_id = e.id
            LEFT JOIN conn c2 ON c2.from_equipment_id = e.id
            WHERE e.id = ANY($1)
            GROUP BY e.id
        )
        SELECT id FROM stats WHERE upstream_cnt = 1 AND downstream_cnt > 2
    `

	// Execute bulk SOPF query
	sopfRows, err := a.db.Query(ctx, sopfQuery, ids)
	if err != nil {
		return nil, err
	}
	defer sopfRows.Close()

	candidateIDs := make([]string, 0, len(ids))
	for sopfRows.Next() {
		var id string
		if err := sopfRows.Scan(&id); err == nil {
			candidateIDs = append(candidateIDs, id)
		}
	}

	if len(candidateIDs) == 0 {
		return failurePoints, nil
	}

	// Bulk fetch equipment details
	// Note: use a helper to fetch by IDs in one call if available; otherwise fall back to individual fetches
	placeholders := make([]interface{}, len(candidateIDs))
	for i, id := range candidateIDs {
		placeholders[i] = id
	}

	eqQuery := `
        SELECT id, name, type, status, room_id, location_x, location_y, location_z
        FROM equipment
        WHERE id = ANY($1)
    `

	eqRows, err := a.db.Query(ctx, eqQuery, candidateIDs)
	if err != nil {
		return nil, err
	}
	defer eqRows.Close()

	for eqRows.Next() {
		e := &models.Equipment{}
		if err := eqRows.Scan(&e.ID, &e.Name, &e.Type, &e.Status, &e.RoomID, &e.Location.X, &e.Location.Y, &e.Location.Z); err == nil {
			failurePoints = append(failurePoints, e)
		}
	}

	return failurePoints, nil
}

// isSinglePointOfFailure checks if equipment is a single point of failure
func (a *Analyzer) isSinglePointOfFailure(ctx context.Context, equipmentID string) bool {
	// Check if this equipment connects two separate groups
	// If removing it would disconnect the graph, it's a failure point

	upstream, _ := a.graph.GetConnections(ctx, equipmentID, Upstream)
	downstream, _ := a.graph.GetConnections(ctx, equipmentID, Downstream)

	// Simple heuristic: if it has multiple downstream with only one upstream
	// or is the only connection between groups
	if len(upstream) == 1 && len(downstream) > 2 {
		return true
	}

	// Check if it's a panel or main distribution point
	equipment, err := a.db.GetEquipment(ctx, equipmentID)
	if err == nil {
		if equipment.Type == "panel" || equipment.Type == "mdf" || equipment.Type == "main" {
			return true
		}
	}

	return false
}

// SuggestConnections suggests potential connections based on proximity and type
func (a *Analyzer) SuggestConnections(ctx context.Context, equipmentID string, maxDistance float64) ([]Connection, error) {
	suggestions := []Connection{}

	equipment, err := a.db.GetEquipment(ctx, equipmentID)
	if err != nil {
		return nil, err
	}

	// Find nearby equipment of compatible types
	query := `
		SELECT id, type, location_x, location_y,
		       SQRT(POWER(location_x - ?, 2) + POWER(location_y - ?, 2)) as distance
		FROM equipment
		WHERE id != ? 
		  AND room_id = ?
		  AND SQRT(POWER(location_x - ?, 2) + POWER(location_y - ?, 2)) <= ?
		ORDER BY distance
	`

	rows, err := a.db.Query(ctx, query,
		equipment.Location.X, equipment.Location.Y,
		equipmentID,
		equipment.RoomID,
		equipment.Location.X, equipment.Location.Y,
		maxDistance,
	)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	for rows.Next() {
		var nearbyID, nearbyType string
		var locX, locY, distance float64

		if err := rows.Scan(&nearbyID, &nearbyType, &locX, &locY, &distance); err != nil {
			continue
		}

		// Suggest connections based on equipment types
		connType := a.suggestConnectionType(equipment.Type, nearbyType)
		if connType != "" {
			suggestions = append(suggestions, Connection{
				FromID:         equipmentID,
				ToID:           nearbyID,
				ConnectionType: connType,
				Metadata: map[string]interface{}{
					"distance":  distance,
					"suggested": true,
				},
			})
		}
	}

	return suggestions, nil
}

// suggestConnectionType suggests connection type based on equipment types
func (a *Analyzer) suggestConnectionType(type1, type2 string) ConnectionType {
	// Electrical connections
	if (type1 == "outlet" && type2 == "panel") || (type1 == "panel" && type2 == "outlet") {
		return ConnectionPower
	}
	if (type1 == "switch" && type2 == "panel") || (type1 == "panel" && type2 == "switch") {
		return ConnectionPower
	}

	// Data connections
	if (type1 == "outlet" && type2 == "idf") || (type1 == "idf" && type2 == "outlet") {
		return ConnectionData
	}
	if (type1 == "switch" && type2 == "idf") || (type1 == "idf" && type2 == "switch") {
		return ConnectionData
	}

	// HVAC connections
	if type1 == "thermostat" || type2 == "thermostat" {
		return ConnectionHVAC
	}

	return ""
}

// ValidateConnections validates all connections for consistency
func (a *Analyzer) ValidateConnections(ctx context.Context) ([]string, error) {
	errors := []string{}

	// Check for orphaned connections (equipment doesn't exist)
	query := `
		SELECT c.from_equipment_id, c.to_equipment_id, c.connection_type
		FROM connections c
		LEFT JOIN equipment e1 ON c.from_equipment_id = e1.id
		LEFT JOIN equipment e2 ON c.to_equipment_id = e2.id
		WHERE e1.id IS NULL OR e2.id IS NULL
	`

	rows, err := a.db.Query(ctx, query)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	for rows.Next() {
		var fromID, toID, connType string
		if err := rows.Scan(&fromID, &toID, &connType); err != nil {
			continue
		}
		errors = append(errors, fmt.Sprintf("Orphaned connection: %s -> %s (%s)", fromID, toID, connType))
	}

	// Check for circular connections
	// This would require more complex graph cycle detection

	return errors, nil
}
