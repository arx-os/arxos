// Package rendering provides the consolidated multi-level rendering system for ArxOS.
// This file serves as the main interface that replaces the complex overlapping rendering systems
// with a clean, purpose-built solution matching the user experience hierarchy.
package rendering

import (
	"strings"

	"github.com/joelpate/arxos/internal/bim"
	"github.com/joelpate/arxos/internal/database"
	"github.com/joelpate/arxos/pkg/models"
)

// ConsolidatedRenderer is the main interface for all ArxOS rendering operations
// It replaces the complex system of multiple overlapping renderers with a clean,
// multi-level approach that matches the user experience hierarchy
type ConsolidatedRenderer struct {
	multiLevel *MultiLevelRenderer
}

// NewConsolidatedRenderer creates a new consolidated renderer
func NewConsolidatedRenderer() *ConsolidatedRenderer {
	config := DefaultRendererConfig()

	return &ConsolidatedRenderer{
		multiLevel: NewMultiLevelRenderer(config),
	}
}

// NewConsolidatedRendererWithConfig creates a renderer with custom configuration
func NewConsolidatedRendererWithConfig(config *RendererConfig) *ConsolidatedRenderer {
	return &ConsolidatedRenderer{
		multiLevel: NewMultiLevelRenderer(config),
	}
}

// Building Manager Interface - Schematic Overview
// These methods serve building managers who need general layout and status information

// RenderBuildingOverview renders schematic overview from .bim.txt data
func (cr *ConsolidatedRenderer) RenderBuildingOverview(building *bim.Building) (string, error) {
	request := &RenderRequest{
		BIMBuilding: building,
		ViewLevel:   ViewOverview,
	}

	return cr.multiLevel.Render(request)
}

// RenderFloorOverview renders overview of a specific floor
func (cr *ConsolidatedRenderer) RenderFloorOverview(building *bim.Building, floorID string) (string, error) {
	request := &RenderRequest{
		BIMBuilding: building,
		ViewLevel:   ViewOverview,
		FloorFilter: floorID,
	}

	return cr.multiLevel.Render(request)
}

// Systems Engineer Interface - Detailed System Tracing
// These methods serve systems engineers who need connection paths and technical details

// RenderSystemTrace renders detailed system connections and paths
func (cr *ConsolidatedRenderer) RenderSystemTrace(floorPlan *models.FloorPlan, systemType string) (string, error) {
	request := &RenderRequest{
		FloorPlan:    floorPlan,
		ViewLevel:    ViewDetail,
		SystemFilter: systemType,
	}

	return cr.multiLevel.Render(request)
}

// RenderConnectionTrace traces connections from specific equipment
func (cr *ConsolidatedRenderer) RenderConnectionTrace(floorPlan *models.FloorPlan, equipmentID string) (string, error) {
	// Create tracing renderer for detailed connection analysis
	tracing := NewTracingRenderer(cr.multiLevel.config)

	return tracing.RenderConnections(floorPlan, TracingOptions{
		TraceFromID:      equipmentID,
		ShowPowerPaths:   true,
		ShowNetworkPaths: true,
		ShowHVACPaths:    true,
		HighlightFaults:  true,
	})
}

// RenderSystemAnalysis renders analysis of all systems with fault detection
func (cr *ConsolidatedRenderer) RenderSystemAnalysis(floorPlan *models.FloorPlan) (string, error) {
	request := &RenderRequest{
		FloorPlan: floorPlan,
		ViewLevel: ViewDetail,
	}

	return cr.multiLevel.Render(request)
}

// Field Technician Interface - Spatial Coordinates
// These methods serve field technicians who need precise positioning for AR applications

// RenderSpatialAnchors renders precise coordinate information
func (cr *ConsolidatedRenderer) RenderSpatialAnchors(anchors []*database.SpatialAnchor) (string, error) {
	request := &RenderRequest{
		SpatialAnchors: anchors,
		ViewLevel:      ViewSpatial,
	}

	return cr.multiLevel.Render(request)
}

// RenderEquipmentCoordinates renders coordinates for specific equipment
func (cr *ConsolidatedRenderer) RenderEquipmentCoordinates(anchors []*database.SpatialAnchor, equipmentID string) (string, error) {
	// Filter anchors to specific equipment
	var filtered []*database.SpatialAnchor
	for _, anchor := range anchors {
		if strings.Contains(anchor.EquipmentPath, equipmentID) {
			filtered = append(filtered, anchor)
		}
	}

	request := &RenderRequest{
		SpatialAnchors: filtered,
		ViewLevel:      ViewSpatial,
	}

	return cr.multiLevel.Render(request)
}

// RenderNearbyEquipment renders equipment within radius of a point
func (cr *ConsolidatedRenderer) RenderNearbyEquipment(anchors []*database.SpatialAnchor, centerX, centerY, radius float64) (string, error) {
	spatial := NewSpatialRenderer(cr.multiLevel.config)

	return spatial.RenderAnchors(anchors, SpatialOptions{
		ShowCoordinates: true,
		ShowPrecision:   true,
		CoordinateUnit:  "meters",
		RadiusFilter:    radius,
		CenterPoint:     &Point3D{X: centerX, Y: centerY, Z: 0},
	})
}

// Live Monitoring Interface
// These methods provide real-time updating displays

// RenderLiveMonitor provides live updating display for any view level
func (cr *ConsolidatedRenderer) RenderLiveMonitor(request *RenderRequest, outputChan chan<- string) {
	cr.multiLevel.RenderLive(request, outputChan)
}

// Utility Methods

// GetSupportedViewLevels returns information about all supported view levels
func (cr *ConsolidatedRenderer) GetSupportedViewLevels() map[ViewLevel]string {
	return GetAvailableViewLevels()
}

// ValidateRenderData validates that render request has required data
func (cr *ConsolidatedRenderer) ValidateRenderData(request *RenderRequest) error {
	return ValidateRenderRequest(request)
}

// RenderUsageHelp renders help information about the rendering system
func (cr *ConsolidatedRenderer) RenderUsageHelp() string {
	return cr.multiLevel.RenderUsageHelp()
}

// Configuration Methods

// SetWidth updates the renderer width
func (cr *ConsolidatedRenderer) SetWidth(width int) {
	cr.multiLevel.config.Width = width
	// Update all sub-renderers
	cr.multiLevel.schematic.width = width
	cr.multiLevel.tracing.width = width
	cr.multiLevel.spatial.width = width
}

// SetHeight updates the renderer height
func (cr *ConsolidatedRenderer) SetHeight(height int) {
	cr.multiLevel.config.Height = height
	// Update all sub-renderers
	cr.multiLevel.schematic.height = height
	cr.multiLevel.tracing.height = height
	cr.multiLevel.spatial.height = height
}

// EnableColors enables or disables terminal colors
func (cr *ConsolidatedRenderer) EnableColors(enabled bool) {
	cr.multiLevel.config.ColorEnabled = enabled
}

// SetDefaultView sets the default view level
func (cr *ConsolidatedRenderer) SetDefaultView(level ViewLevel) {
	cr.multiLevel.config.DefaultView = level
}
