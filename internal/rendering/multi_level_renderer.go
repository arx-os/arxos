// Package rendering provides a consolidated multi-level rendering system for ArxOS.
// This replaces multiple overlapping ASCII rendering approaches with a clean system
// that matches the multi-level user experience hierarchy.
package rendering

import (
	"fmt"
	"strings"
	"time"

	"github.com/joelpate/arxos/internal/bim"
	"github.com/joelpate/arxos/internal/database"
	"github.com/joelpate/arxos/pkg/models"
)

// MultiLevelRenderer provides rendering for all three user experience levels
type MultiLevelRenderer struct {
	schematic *SchematicRenderer // Building manager - overview
	tracing   *TracingRenderer   // Systems engineer - detailed connections
	spatial   *SpatialRenderer   // Field technician - coordinate display
	config    *RendererConfig
}

// RendererConfig contains configuration for the multi-level renderer
type RendererConfig struct {
	Width             int           // Terminal width
	Height            int           // Terminal height
	DefaultView       ViewLevel     // Default view level
	ShowGrid          bool          // Show coordinate grid
	ShowLegend        bool          // Show symbol legend
	ShowStatusSummary bool          // Show equipment status summary
	ColorEnabled      bool          // Enable terminal colors
	RefreshInterval   time.Duration // For live monitoring
}

// ViewLevel represents the three levels of detail
type ViewLevel int

const (
	ViewOverview ViewLevel = iota // Building manager - schematic overview
	ViewDetail                    // Systems engineer - detailed system tracing
	ViewSpatial                   // Field technician - precise coordinates
)

// RenderRequest contains all data needed for rendering
type RenderRequest struct {
	// Data sources (from StorageCoordinator)
	BIMBuilding    *bim.Building             // Schematic data
	FloorPlan      *models.FloorPlan         // Cache data
	SpatialAnchors []*database.SpatialAnchor // Spatial data

	// Rendering parameters
	ViewLevel    ViewLevel // Which level to render
	BuildingID   string    // Building identifier
	FloorFilter  string    // Specific floor (optional)
	SystemFilter string    // Specific system (optional)
	StatusFilter string    // Equipment status filter
	ShowAll      bool      // Show all floors/systems
}

// NewMultiLevelRenderer creates a new multi-level renderer
func NewMultiLevelRenderer(config *RendererConfig) *MultiLevelRenderer {
	if config == nil {
		config = DefaultRendererConfig()
	}

	return &MultiLevelRenderer{
		schematic: NewSchematicRenderer(config),
		tracing:   NewTracingRenderer(config),
		spatial:   NewSpatialRenderer(config),
		config:    config,
	}
}

// DefaultRendererConfig returns default renderer configuration
func DefaultRendererConfig() *RendererConfig {
	return &RendererConfig{
		Width:             120,
		Height:            40,
		DefaultView:       ViewOverview,
		ShowGrid:          false,
		ShowLegend:        true,
		ShowStatusSummary: true,
		ColorEnabled:      true,
		RefreshInterval:   1 * time.Second,
	}
}

// Render renders the building data at the specified view level
func (mlr *MultiLevelRenderer) Render(request *RenderRequest) (string, error) {
	switch request.ViewLevel {
	case ViewOverview:
		return mlr.renderOverview(request)
	case ViewDetail:
		return mlr.renderDetail(request)
	case ViewSpatial:
		return mlr.renderSpatial(request)
	default:
		return "", fmt.Errorf("unknown view level: %v", request.ViewLevel)
	}
}

// renderOverview renders schematic overview for building managers
func (mlr *MultiLevelRenderer) renderOverview(request *RenderRequest) (string, error) {
	if request.BIMBuilding == nil {
		return "", fmt.Errorf("no BIM data available for overview")
	}

	return mlr.schematic.RenderBuilding(request.BIMBuilding, SchematicOptions{
		ShowGrid:          mlr.config.ShowGrid,
		ShowLegend:        mlr.config.ShowLegend,
		ShowStatusSummary: mlr.config.ShowStatusSummary,
		FloorFilter:       request.FloorFilter,
		StatusFilter:      request.StatusFilter,
	})
}

// renderDetail renders detailed system tracing for systems engineers
func (mlr *MultiLevelRenderer) renderDetail(request *RenderRequest) (string, error) {
	if request.FloorPlan == nil {
		return "", fmt.Errorf("no floor plan data available for detail view")
	}

	return mlr.tracing.RenderConnections(request.FloorPlan, TracingOptions{
		SystemFilter:     request.SystemFilter,
		ShowPowerPaths:   true,
		ShowNetworkPaths: true,
		ShowHVACPaths:    true,
		HighlightFaults:  true,
	})
}

// renderSpatial renders spatial coordinates for field technicians
func (mlr *MultiLevelRenderer) renderSpatial(request *RenderRequest) (string, error) {
	if request.SpatialAnchors == nil {
		return "", fmt.Errorf("no spatial data available for spatial view")
	}

	return mlr.spatial.RenderAnchors(request.SpatialAnchors, SpatialOptions{
		ShowCoordinates: true,
		ShowPrecision:   true,
		CoordinateUnit:  "meters",
		FloorFilter:     request.FloorFilter,
	})
}

// RenderLive provides live updating display for monitoring
func (mlr *MultiLevelRenderer) RenderLive(request *RenderRequest, outputChan chan<- string) {
	ticker := time.NewTicker(mlr.config.RefreshInterval)
	defer ticker.Stop()

	for range ticker.C {
		output, err := mlr.Render(request)
		if err != nil {
			output = fmt.Sprintf("Error: %v", err)
		}

		// Clear screen and render
		clearScreen := "\033[2J\033[H"
		timestamp := time.Now().Format("15:04:05")
		header := fmt.Sprintf("%s[Live Monitor - %s]%s\n",
			clearScreen, timestamp, strings.Repeat("=", 50))

		select {
		case outputChan <- header + output:
		default:
			// Channel full, skip this update
		}
	}
}

// GetViewLevelName returns human-readable view level name
func GetViewLevelName(level ViewLevel) string {
	switch level {
	case ViewOverview:
		return "Overview (Building Manager)"
	case ViewDetail:
		return "Detail (Systems Engineer)"
	case ViewSpatial:
		return "Spatial (Field Technician)"
	default:
		return "Unknown"
	}
}

// GetAvailableViewLevels returns all available view levels with descriptions
func GetAvailableViewLevels() map[ViewLevel]string {
	return map[ViewLevel]string{
		ViewOverview: "Schematic overview from .bim.txt files - for building operations",
		ViewDetail:   "System tracing and connections - for engineering analysis",
		ViewSpatial:  "Precise coordinates and spatial anchors - for field work",
	}
}

// ValidateRenderRequest checks if a render request has required data
func ValidateRenderRequest(request *RenderRequest) error {
	if request == nil {
		return fmt.Errorf("render request is nil")
	}

	switch request.ViewLevel {
	case ViewOverview:
		if request.BIMBuilding == nil {
			return fmt.Errorf("BIM building data required for overview")
		}
	case ViewDetail:
		if request.FloorPlan == nil {
			return fmt.Errorf("floor plan data required for detail view")
		}
	case ViewSpatial:
		if request.SpatialAnchors == nil {
			return fmt.Errorf("spatial anchors required for spatial view")
		}
	default:
		return fmt.Errorf("invalid view level: %v", request.ViewLevel)
	}

	return nil
}

// RenderUsageHelp renders help text explaining the different view levels
func (mlr *MultiLevelRenderer) RenderUsageHelp() string {
	var sb strings.Builder

	sb.WriteString("ArxOS Multi-Level Rendering System\n")
	sb.WriteString(strings.Repeat("=", 60) + "\n\n")

	sb.WriteString("Available View Levels:\n\n")

	for level, description := range GetAvailableViewLevels() {
		sb.WriteString(fmt.Sprintf("%d. %s\n", int(level)+1, GetViewLevelName(level)))
		sb.WriteString(fmt.Sprintf("   %s\n\n", description))
	}

	sb.WriteString("Usage Examples:\n")
	sb.WriteString("  arx view BUILDING_ID                    # Overview (default)\n")
	sb.WriteString("  arx view BUILDING_ID --detail           # Detailed system tracing\n")
	sb.WriteString("  arx view BUILDING_ID --spatial          # Spatial coordinates\n")
	sb.WriteString("  arx view BUILDING_ID --floor 3          # Specific floor only\n")
	sb.WriteString("  arx view BUILDING_ID --system electrical # Specific system only\n")
	sb.WriteString("  arx monitor BUILDING_ID --live          # Live updating display\n\n")

	return sb.String()
}
