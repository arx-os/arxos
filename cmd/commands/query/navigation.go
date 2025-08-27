package query

import (
	"fmt"
	"strings"
	"time"

	"github.com/spf13/cobra"
)

var navigateCmd = &cobra.Command{
	Use:   "navigate [path]",
	Short: "Navigate through building hierarchy with spatial awareness",
	Long: `Navigate through the building hierarchy with enhanced spatial awareness.
Provides intelligent path resolution, spatial queries, and relationship navigation.

Features:
  - Hierarchical path navigation (building:floor:room:equipment)
  - Spatial queries (near, within, connected)
  - Relationship traversal (parent, children, siblings)
  - Breadcrumb navigation
  - Spatial context awareness

Examples:
  arx query navigate building:hq:floor:3
  arx query navigate --near=room:305 --radius=10m
  arx query navigate --connected=electrical_panel:e1
  arx query navigate --spatial=3d --view=ascii-bim`,
	Args: cobra.MaximumNArgs(1),
	RunE: runNavigate,
}

func init() {
	QueryCmd.AddCommand(navigateCmd)

	// Navigation flags
	navigateCmd.Flags().String("near", "", "Navigate to objects near specified location")
	navigateCmd.Flags().String("radius", "5m", "Radius for near queries (e.g., 5m, 10ft)")
	navigateCmd.Flags().String("connected", "", "Navigate through connected objects")
	navigateCmd.Flags().String("spatial", "2d", "Spatial mode (2d, 3d, ascii-bim)")
	navigateCmd.Flags().String("view", "tree", "View mode (tree, list, ascii-bim, spatial)")
	navigateCmd.Flags().Bool("breadcrumbs", true, "Show navigation breadcrumbs")
	navigateCmd.Flags().Bool("relationships", false, "Show object relationships")
}

func runNavigate(cmd *cobra.Command, args []string) error {
	path := ""
	if len(args) > 0 {
		path = args[0]
	}

	near, _ := cmd.Flags().GetString("near")
	radius, _ := cmd.Flags().GetString("radius")
	connected, _ := cmd.Flags().GetString("connected")
	spatial, _ := cmd.Flags().GetString("spatial")
	view, _ := cmd.Flags().GetString("view")
	breadcrumbs, _ := cmd.Flags().GetBool("breadcrumbs")
	relationships, _ := cmd.Flags().GetBool("relationships")
	_ = breadcrumbs   // TODO: Implement breadcrumb display
	_ = relationships // TODO: Implement relationship display

	// Create navigation context
	nav := NewNavigationContext(path, near, radius, connected, spatial, view)

	// Execute navigation
	result := nav.Navigate()

	// Display results
	display := NewResultDisplay(view, "default")
	return display.DisplayResult(result)
}

// NavigationContext represents the navigation context and parameters
type NavigationContext struct {
	Path            string
	NearLocation    string
	Radius          string
	ConnectedObject string
	SpatialMode     string
	ViewMode        string
	Breadcrumbs     []string
	CurrentLevel    string
}

// NewNavigationContext creates a new navigation context
func NewNavigationContext(path, near, radius, connected, spatial, view string) *NavigationContext {
	return &NavigationContext{
		Path:            path,
		NearLocation:    near,
		Radius:          radius,
		ConnectedObject: connected,
		SpatialMode:     spatial,
		ViewMode:        view,
		Breadcrumbs:     make([]string, 0),
		CurrentLevel:    "root",
	}
}

// Navigate executes the navigation based on context
func (nc *NavigationContext) Navigate() *AQLResult {
	var objects []interface{}
	var message string
	var metadata map[string]interface{}

	// Handle different navigation types
	if nc.NearLocation != "" {
		objects, message, metadata = nc.navigateNear()
	} else if nc.ConnectedObject != "" {
		objects, message, metadata = nc.navigateConnected()
	} else if nc.Path != "" {
		objects, message, metadata = nc.navigatePath()
	} else {
		objects, message, metadata = nc.navigateRoot()
	}

	// Add breadcrumbs to metadata
	if len(nc.Breadcrumbs) > 0 {
		metadata["breadcrumbs"] = nc.Breadcrumbs
		metadata["current_level"] = nc.CurrentLevel
	}

	return &AQLResult{
		Type:       "NAVIGATE",
		Objects:    objects,
		Count:      len(objects),
		Message:    message,
		Metadata:   metadata,
		ExecutedAt: time.Now(),
	}
}

// navigateNear handles spatial navigation to nearby objects
func (nc *NavigationContext) navigateNear() ([]interface{}, string, map[string]interface{}) {
	// Parse location and radius
	location := nc.parseLocation(nc.NearLocation)
	radius := nc.parseRadius(nc.Radius)

	// Generate mock nearby objects
	objects := generateMockNearbyObjects(location, radius)

	message := fmt.Sprintf("Found %d objects within %s of %s", len(objects), nc.Radius, nc.NearLocation)

	metadata := map[string]interface{}{
		"navigation_type": "spatial",
		"near_location":   nc.NearLocation,
		"radius":          nc.Radius,
		"spatial_mode":    nc.SpatialMode,
		"coordinates":     location,
	}

	nc.CurrentLevel = "spatial"
	nc.addBreadcrumb(fmt.Sprintf("near:%s:%s", nc.NearLocation, nc.Radius))

	return objects, message, metadata
}

// navigateConnected handles relationship-based navigation
func (nc *NavigationContext) navigateConnected() ([]interface{}, string, map[string]interface{}) {
	// Parse connected object
	parts := strings.Split(nc.ConnectedObject, ":")
	if len(parts) < 2 {
		return []interface{}{}, "Invalid connected object format", map[string]interface{}{}
	}

	objectType := parts[0]
	objectID := parts[1]

	// Generate mock connected objects
	objects := generateMockConnectedObjects(objectType, objectID)

	message := fmt.Sprintf("Found %d objects connected to %s:%s", len(objects), objectType, objectID)

	metadata := map[string]interface{}{
		"navigation_type": "relationship",
		"source_type":     objectType,
		"source_id":       objectID,
		"view_mode":       nc.ViewMode,
	}

	nc.CurrentLevel = "connected"
	nc.addBreadcrumb(fmt.Sprintf("connected:%s", nc.ConnectedObject))

	return objects, message, metadata
}

// navigatePath handles hierarchical path navigation
func (nc *NavigationContext) navigatePath() ([]interface{}, string, map[string]interface{}) {
	// Parse path components
	parts := strings.Split(nc.Path, ":")

	// Build breadcrumbs
	for i, part := range parts {
		if i == 0 {
			nc.addBreadcrumb(part)
		} else {
			nc.addBreadcrumb(fmt.Sprintf("%s:%s", parts[i-1], part))
		}
	}

	// Generate mock objects for the path
	objects := generateMockPathObjects(nc.Path, parts)

	message := fmt.Sprintf("Navigated to %s, found %d objects", nc.Path, len(objects))

	metadata := map[string]interface{}{
		"navigation_type": "hierarchical",
		"path":            nc.Path,
		"path_depth":      len(parts),
		"view_mode":       nc.ViewMode,
	}

	nc.CurrentLevel = parts[len(parts)-1]

	return objects, message, metadata
}

// navigateRoot handles root-level navigation
func (nc *NavigationContext) navigateRoot() ([]interface{}, string, map[string]interface{}) {
	// Generate mock root objects
	objects := generateMockRootObjects()

	message := "At root level - showing available buildings and top-level objects"

	metadata := map[string]interface{}{
		"navigation_type": "root",
		"view_mode":       nc.ViewMode,
	}

	nc.CurrentLevel = "root"
	nc.addBreadcrumb("root")

	return objects, message, metadata
}

// Helper functions for navigation
func (nc *NavigationContext) parseLocation(location string) map[string]interface{} {
	// Simple location parsing (in production, this would be more sophisticated)
	parts := strings.Split(location, ":")

	if len(parts) >= 2 {
		return map[string]interface{}{
			"type": parts[0],
			"id":   parts[1],
			"x":    0.0,
			"y":    0.0,
			"z":    0.0,
		}
	}

	return map[string]interface{}{
		"type": "unknown",
		"id":   location,
		"x":    0.0,
		"y":    0.0,
		"z":    0.0,
	}
}

func (nc *NavigationContext) parseRadius(radius string) float64 {
	// Simple radius parsing (in production, this would handle units)
	if strings.HasSuffix(radius, "m") {
		radius = strings.TrimSuffix(radius, "m")
		return 5.0 // Default to 5 meters
	}
	return 5.0
}

func (nc *NavigationContext) addBreadcrumb(crumb string) {
	nc.Breadcrumbs = append(nc.Breadcrumbs, crumb)
	if len(nc.Breadcrumbs) > 10 { // Keep last 10 breadcrumbs
		nc.Breadcrumbs = nc.Breadcrumbs[1:]
	}
}

// Mock data generation functions for navigation
func generateMockNearbyObjects(location map[string]interface{}, radius float64) []interface{} {
	return []interface{}{
		map[string]interface{}{
			"id": "obj-001", "name": "Nearby Wall", "type": "wall",
			"distance": 2.5, "direction": "north", "confidence": 0.9,
		},
		map[string]interface{}{
			"id": "obj-002", "name": "Adjacent Door", "type": "door",
			"distance": 4.1, "direction": "east", "confidence": 0.85,
		},
		map[string]interface{}{
			"id": "obj-003", "name": "Corner Column", "type": "column",
			"distance": 3.8, "direction": "southwest", "confidence": 0.92,
		},
	}
}

func generateMockConnectedObjects(objectType, objectID string) []interface{} {
	return []interface{}{
		map[string]interface{}{
			"id": "conn-001", "name": "Connected Panel", "type": "electrical_panel",
			"connection_type": "electrical", "distance": 0.0, "confidence": 0.95,
		},
		map[string]interface{}{
			"id": "conn-002", "name": "Linked Equipment", "type": "hvac",
			"connection_type": "mechanical", "distance": 2.1, "confidence": 0.88,
		},
		map[string]interface{}{
			"id": "conn-003", "name": "Adjacent Room", "type": "room",
			"connection_type": "spatial", "distance": 0.0, "confidence": 1.0,
		},
	}
}

func generateMockPathObjects(path string, parts []string) []interface{} {
	if len(parts) == 0 {
		return []interface{}{}
	}

	// Generate objects based on path depth
	switch len(parts) {
	case 1: // Building level
		return []interface{}{
			map[string]interface{}{
				"id": "building-001", "name": parts[0], "type": "building",
				"floors": 5, "area_sqm": 2500, "status": "active",
			},
		}
	case 2: // Floor level
		return []interface{}{
			map[string]interface{}{
				"id": fmt.Sprintf("floor-%s", parts[1]), "name": fmt.Sprintf("Floor %s", parts[1]),
				"type": "floor", "building": parts[0], "rooms": 12, "area_sqm": 500,
			},
		}
	case 3: // Room level
		return []interface{}{
			map[string]interface{}{
				"id": fmt.Sprintf("room-%s", parts[2]), "name": fmt.Sprintf("Room %s", parts[2]),
				"type": "room", "floor": parts[1], "building": parts[0], "area_sqm": 25,
			},
		}
	default: // Equipment/object level
		return []interface{}{
			map[string]interface{}{
				"id": fmt.Sprintf("obj-%s", parts[len(parts)-1]), "name": fmt.Sprintf("Object %s", parts[len(parts)-1]),
				"type": "equipment", "path": path, "status": "active",
			},
		}
	}
}

func generateMockRootObjects() []interface{} {
	return []interface{}{
		map[string]interface{}{
			"id": "building-hq", "name": "HQ Building", "type": "building",
			"floors": 5, "area_sqm": 2500, "status": "active",
		},
		map[string]interface{}{
			"id": "building-warehouse", "name": "Warehouse", "type": "building",
			"floors": 2, "area_sqm": 5000, "status": "active",
		},
		map[string]interface{}{
			"id": "site-main", "name": "Main Campus", "type": "site",
			"buildings": 3, "area_hectares": 2.5, "status": "active",
		},
	}
}
