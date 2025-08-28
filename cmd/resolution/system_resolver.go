// Package resolution provides path-to-ArxObject conversion for all building systems
package resolution

import (
	"fmt"
	"strings"
	
	"github.com/arxos/arxos/cmd/navigation"
)

// DatabaseService provides query interface for ArxObjects
type DatabaseService interface {
	Query(query Query) ([]interface{}, error)
}

// Query represents a database query with filters
type Query struct {
	Type    string
	Filters []Filter
}

// Filter represents a database filter condition
type Filter struct {
	Field    string
	Operator string
	Value    interface{}
}

// ArxObjectUnified represents a unified ArxObject for resolution
type ArxObjectUnified struct {
	ID          string                 `json:"id"`
	Type        string                 `json:"type"`
	Name        string                 `json:"name"`
	Description string                 `json:"description"`
	System      string                 `json:"system"`
	Path        string                 `json:"path"`
	Properties  map[string]interface{} `json:"properties"`
	Position    Position               `json:"position"`
}

// Position represents the physical position of an object
type Position struct {
	X float64 `json:"x"`
	Y float64 `json:"y"`
	Z float64 `json:"z"`
}

// GetID returns the object ID
func (obj *ArxObjectUnified) GetID() string {
	return obj.ID
}

// GetSystem returns the system name
func (obj *ArxObjectUnified) GetSystem() string {
	return obj.System
}

// GetPath returns the object path
func (obj *ArxObjectUnified) GetPath() string {
	return obj.Path
}

// SystemResolver converts building system paths to ArxObjects
type SystemResolver struct {
	db DatabaseService
}

// MockDatabaseService provides a simple in-memory implementation for testing
type MockDatabaseService struct{}

// Query implements DatabaseService interface with sample data
func (m *MockDatabaseService) Query(query Query) ([]interface{}, error) {
	// Return empty result set for now - will be populated with sample data later
	return []interface{}{}, nil
}

// NewSystemResolver creates a new system resolver
func NewSystemResolver(db DatabaseService) *SystemResolver {
	return &SystemResolver{
		db: db,
	}
}

// NewMockSystemResolver creates a system resolver with mock database for testing
func NewMockSystemResolver() *SystemResolver {
	return &SystemResolver{
		db: &MockDatabaseService{},
	}
}

// ResolveSystemPath converts a building path to ArxObjects
func (sr *SystemResolver) ResolveSystemPath(path string) ([]*ArxObjectUnified, error) {
	if sr.db == nil {
		return nil, fmt.Errorf("database service not initialized")
	}
	
	// Normalize the path
	normalizedPath := navigation.NormalizePath(path)
	
	// Extract system from path
	system := navigation.GetSystemFromPath(normalizedPath)
	
	// Route to appropriate system handler
	switch system {
	case "structural":
		return sr.getStructuralObjects(normalizedPath)
	case "electrical":
		return sr.getElectricalObjects(normalizedPath)
	case "hvac":
		return sr.getHVACObjects(normalizedPath)
	case "plumbing":
		return sr.getPlumbingObjects(normalizedPath)
	case "fire":
		return sr.getFireObjects(normalizedPath)
	case "security":
		return sr.getSecurityObjects(normalizedPath)
	case "network":
		return sr.getNetworkObjects(normalizedPath)
	case "floors":
		return sr.getFloorObjects(normalizedPath)
	case "zones":
		return sr.getZoneObjects(normalizedPath)
	case "equipment":
		return sr.getEquipmentObjects(normalizedPath)
	case "":
		// Root path - return system summaries
		return sr.getRootObjects()
	default:
		return nil, fmt.Errorf("unknown system: %s", system)
	}
}

// getStructuralObjects returns structural system components
func (sr *SystemResolver) getStructuralObjects(path string) ([]*ArxObjectUnified, error) {
	// Query for structural components matching the path
	query := Query{
		Type: "arxobject",
		Filters: []Filter{
			{Field: "path", Operator: "LIKE", Value: path + "%"},
			{Field: "type", Operator: "IN", Value: []string{
				"wall", "beam", "column", "foundation", "slab", "door", "window",
			}},
		},
	}
	
	results, err := sr.db.Query(query)
	if err != nil {
		return nil, fmt.Errorf("failed to query structural objects: %w", err)
	}
	
	return sr.convertResults(results)
}

// getElectricalObjects returns electrical system components
func (sr *SystemResolver) getElectricalObjects(path string) ([]*ArxObjectUnified, error) {
	query := Query{
		Type: "arxobject",
		Filters: []Filter{
			{Field: "path", Operator: "LIKE", Value: path + "%"},
			{Field: "type", Operator: "IN", Value: []string{
				"electrical_panel", "electrical_outlet", "electrical_switch", 
				"electrical_conduit", "light_fixture",
			}},
		},
	}
	
	results, err := sr.db.Query(query)
	if err != nil {
		return nil, fmt.Errorf("failed to query electrical objects: %w", err)
	}
	
	return sr.convertResults(results)
}

// getHVACObjects returns HVAC system components
func (sr *SystemResolver) getHVACObjects(path string) ([]*ArxObjectUnified, error) {
	query := Query{
		Type: "arxobject",
		Filters: []Filter{
			{Field: "path", Operator: "LIKE", Value: path + "%"},
			{Field: "type", Operator: "IN", Value: []string{
				"hvac_unit", "hvac_duct", "hvac_vent", "thermostat",
			}},
		},
	}
	
	results, err := sr.db.Query(query)
	if err != nil {
		return nil, fmt.Errorf("failed to query HVAC objects: %w", err)
	}
	
	return sr.convertResults(results)
}

// getPlumbingObjects returns plumbing system components
func (sr *SystemResolver) getPlumbingObjects(path string) ([]*ArxObjectUnified, error) {
	query := Query{
		Type: "arxobject",
		Filters: []Filter{
			{Field: "path", Operator: "LIKE", Value: path + "%"},
			{Field: "type", Operator: "IN", Value: []string{
				"plumbing_pipe", "plumbing_fixture", "plumbing_valve", "drain",
			}},
		},
	}
	
	results, err := sr.db.Query(query)
	if err != nil {
		return nil, fmt.Errorf("failed to query plumbing objects: %w", err)
	}
	
	return sr.convertResults(results)
}

// getFireObjects returns fire protection system components
func (sr *SystemResolver) getFireObjects(path string) ([]*ArxObjectUnified, error) {
	query := Query{
		Type: "arxobject",
		Filters: []Filter{
			{Field: "path", Operator: "LIKE", Value: path + "%"},
			{Field: "type", Operator: "IN", Value: []string{
				"fire_sprinkler", "fire_alarm", "smoke_detector", 
				"emergency_exit", "fire_extinguisher",
			}},
		},
	}
	
	results, err := sr.db.Query(query)
	if err != nil {
		return nil, fmt.Errorf("failed to query fire protection objects: %w", err)
	}
	
	return sr.convertResults(results)
}

// getSecurityObjects returns security system components
func (sr *SystemResolver) getSecurityObjects(path string) ([]*ArxObjectUnified, error) {
	query := Query{
		Type: "arxobject",
		Filters: []Filter{
			{Field: "path", Operator: "LIKE", Value: path + "%"},
			{Field: "type", Operator: "IN", Value: []string{
				"sensor", "actuator", "controller", "network_device",
			}},
			{Field: "system", Operator: "=", Value: "security"},
		},
	}
	
	results, err := sr.db.Query(query)
	if err != nil {
		return nil, fmt.Errorf("failed to query security objects: %w", err)
	}
	
	return sr.convertResults(results)
}

// getNetworkObjects returns network infrastructure components  
func (sr *SystemResolver) getNetworkObjects(path string) ([]*ArxObjectUnified, error) {
	query := Query{
		Type: "arxobject",
		Filters: []Filter{
			{Field: "path", Operator: "LIKE", Value: path + "%"},
			{Field: "type", Operator: "IN", Value: []string{
				"network_device", "sensor", "controller",
			}},
			{Field: "system", Operator: "=", Value: "network"},
		},
	}
	
	results, err := sr.db.Query(query)
	if err != nil {
		return nil, fmt.Errorf("failed to query network objects: %w", err)
	}
	
	return sr.convertResults(results)
}

// getFloorObjects returns floor-based organization
func (sr *SystemResolver) getFloorObjects(path string) ([]*ArxObjectUnified, error) {
	// Extract floor number from path if present
	floorFilter := Filter{Field: "path", Operator: "LIKE", Value: path + "%"}
	
	// If path contains specific floor, filter by floor_id
	pathParts := navigation.ParsePath(path)
	if len(pathParts) > 1 && strings.HasPrefix(pathParts[1], "floor") {
		floorID := pathParts[1]
		floorFilter = Filter{Field: "floor_id", Operator: "=", Value: floorID}
	}
	
	query := Query{
		Type: "arxobject",
		Filters: []Filter{floorFilter},
	}
	
	results, err := sr.db.Query(query)
	if err != nil {
		return nil, fmt.Errorf("failed to query floor objects: %w", err)
	}
	
	return sr.convertResults(results)
}

// getZoneObjects returns zone-based organization
func (sr *SystemResolver) getZoneObjects(path string) ([]*ArxObjectUnified, error) {
	query := Query{
		Type: "arxobject", 
		Filters: []Filter{
			{Field: "path", Operator: "LIKE", Value: path + "%"},
		},
	}
	
	// If path contains specific zone, filter by zone_id
	pathParts := navigation.ParsePath(path)
	if len(pathParts) > 1 {
		zoneID := pathParts[1]
		query.Filters = append(query.Filters, 
			Filter{Field: "zone_id", Operator: "=", Value: zoneID})
	}
	
	results, err := sr.db.Query(query)
	if err != nil {
		return nil, fmt.Errorf("failed to query zone objects: %w", err)
	}
	
	return sr.convertResults(results)
}

// getEquipmentObjects returns general equipment
func (sr *SystemResolver) getEquipmentObjects(path string) ([]*ArxObjectUnified, error) {
	query := Query{
		Type: "arxobject",
		Filters: []Filter{
			{Field: "path", Operator: "LIKE", Value: path + "%"},
			{Field: "type", Operator: "IN", Value: []string{
				"equipment", "furniture", "appliance",
			}},
		},
	}
	
	results, err := sr.db.Query(query)
	if err != nil {
		return nil, fmt.Errorf("failed to query equipment objects: %w", err)
	}
	
	return sr.convertResults(results)
}

// getRootObjects returns system summaries for root path
func (sr *SystemResolver) getRootObjects() ([]*ArxObjectUnified, error) {
	// Create virtual objects representing each system
	systems := []struct {
		name        string
		description string
		path        string
	}{
		{"structural", "Structural System (walls, beams, columns)", "/structural"},
		{"electrical", "Electrical System (panels, circuits, outlets)", "/electrical"},
		{"hvac", "HVAC System (air handling, ducts, controls)", "/hvac"},
		{"plumbing", "Plumbing System (pipes, fixtures, valves)", "/plumbing"},
		{"fire", "Fire Protection (sprinklers, alarms, detectors)", "/fire"},
		{"security", "Security System (cameras, access control)", "/security"},
		{"network", "Network Infrastructure (switches, APs, cabling)", "/network"},
		{"floors", "Floor-based Organization", "/floors"},
		{"zones", "Zone-based Organization", "/zones"},
		{"equipment", "General Equipment", "/equipment"},
	}
	
	objects := make([]*ArxObjectUnified, 0, len(systems))
	
	for _, sys := range systems {
		// Create virtual ArxObject for each system
		obj := &ArxObjectUnified{
			ID:          sys.name,
			Type:        "system",
			Name:        sys.name,
			Description: sys.description,
			System:      sys.name,
			Path:        sys.path,
			Properties: map[string]interface{}{
				"system_type": sys.name,
				"virtual":     true,
			},
		}
		
		objects = append(objects, obj)
	}
	
	return objects, nil
}

// convertResults converts database query results to ArxObjects
func (sr *SystemResolver) convertResults(results []interface{}) ([]*ArxObjectUnified, error) {
	objects := make([]*ArxObjectUnified, 0, len(results))
	
	for _, result := range results {
		if obj, ok := result.(*ArxObjectUnified); ok {
			objects = append(objects, obj)
		}
	}
	
	return objects, nil
}

// GetSystemStats returns statistics for a system path
func (sr *SystemResolver) GetSystemStats(path string) (*SystemStats, error) {
	objects, err := sr.ResolveSystemPath(path)
	if err != nil {
		return nil, err
	}
	
	stats := &SystemStats{
		Path:         path,
		TotalObjects: len(objects),
		ObjectTypes:  make(map[string]int),
		Systems:      make(map[string]int),
	}
	
	for _, obj := range objects {
		// Count by type
		objType := string(obj.Type)
		stats.ObjectTypes[objType]++
		
		// Count by system
		system := obj.GetSystem()
		if system != "" {
			stats.Systems[system]++
		}
	}
	
	return stats, nil
}

// SystemStats provides statistics about objects in a system path
type SystemStats struct {
	Path         string         `json:"path"`
	TotalObjects int            `json:"total_objects"`
	ObjectTypes  map[string]int `json:"object_types"`
	Systems      map[string]int `json:"systems"`
}

// GetAvailablePaths returns child paths for a given system path
func (sr *SystemResolver) GetAvailablePaths(path string) ([]string, error) {
	objects, err := sr.ResolveSystemPath(path)
	if err != nil {
		return nil, err
	}
	
	// Extract unique child paths
	childPaths := make(map[string]bool)
	basePath := strings.TrimSuffix(path, "/")
	
	for _, obj := range objects {
		objPath := obj.GetPath()
		
		// Find child paths one level deeper
		if strings.HasPrefix(objPath, basePath) {
			relativePath := strings.TrimPrefix(objPath, basePath)
			relativePath = strings.TrimPrefix(relativePath, "/")
			
			// Get first component of relative path
			parts := strings.Split(relativePath, "/")
			if len(parts) > 0 && parts[0] != "" {
				childPath := basePath + "/" + parts[0]
				childPaths[childPath] = true
			}
		}
	}
	
	// Convert map to sorted slice
	paths := make([]string, 0, len(childPaths))
	for path := range childPaths {
		paths = append(paths, path)
	}
	
	return paths, nil
}