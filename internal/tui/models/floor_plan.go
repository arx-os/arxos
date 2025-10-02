package models

import (
	"context"
	"fmt"
	"strings"

	tea "github.com/charmbracelet/bubbletea"
	"github.com/charmbracelet/lipgloss"

	"github.com/arx-os/arxos/internal/tui/services"
	"github.com/arx-os/arxos/internal/tui/utils"
	"github.com/arx-os/arxos/internal/config"
)

// FloorPlanModel represents the floor plan TUI model
type FloorPlanModel struct {
	// Core state
	buildingID  string
	floorNumber int
	spatialData *services.SpatialData
	renderer    *services.FloorPlanRenderer

	// Data service
	dataService *services.DataService

	// UI state
	width   int
	height  int
	loading bool
	error   error

	// Configuration
	config *config.TUIConfig
	styles *utils.Styles
	layout *utils.Layout

	// Rendering options
	showGrid      bool
	showLabels    bool
	scale         float64
	selectedFloor int
}

// NewFloorPlanModel creates a new floor plan model
func NewFloorPlanModel(buildingID string, config *config.TUIConfig, dataService *services.DataService) *FloorPlanModel {
	theme := "dark" // Default theme
	if config != nil {
		theme = config.Theme
	}
	styles := utils.GetThemeStyles(theme)

	return &FloorPlanModel{
		buildingID:    buildingID,
		floorNumber:   1, // Start with floor 1
		config:        config,
		styles:        styles,
		dataService:   dataService,
		showGrid:      true,
		showLabels:    true,
		scale:         0.5, // 0.5 meters per character
		selectedFloor: 1,
		loading:       true,
	}
}

// Init initializes the floor plan model
func (m FloorPlanModel) Init() tea.Cmd {
	return tea.Batch(
		m.loadSpatialData(),
	)
}

// Update handles messages and updates the model
func (m FloorPlanModel) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	switch msg := msg.(type) {
	case tea.WindowSizeMsg:
		m.width = msg.Width
		m.height = msg.Height
		m.layout = utils.NewLayout(msg.Width, msg.Height, m.styles)

		// Update renderer dimensions
		if m.renderer != nil {
			m.renderer.SetDimensions(msg.Width, msg.Height)
		}
		return m, nil

	case tea.KeyMsg:
		switch msg.String() {
		case "ctrl+c", "q":
			return m, tea.Quit
		case "up", "k":
			if m.selectedFloor > 1 {
				m.selectedFloor--
			}
			return m, nil
		case "down", "j":
			if m.selectedFloor < 5 { // Assume max 5 floors
				m.selectedFloor++
			}
			return m, nil
		case "enter":
			m.floorNumber = m.selectedFloor
			return m, m.loadSpatialData()
		case "g":
			m.showGrid = !m.showGrid
			return m, nil
		case "l":
			m.showLabels = !m.showLabels
			return m, nil
		case "=", "+":
			m.scale *= 0.8 // Zoom in
			return m, nil
		case "-":
			m.scale *= 1.2 // Zoom out
			return m, nil
		case "r":
			return m, m.loadSpatialData()
		}

	case SpatialDataMsg:
		m.spatialData = &msg.Data
		m.loading = false

		// Update renderer
		if m.renderer == nil {
			m.renderer = services.NewFloorPlanRenderer(m.width, m.height, m.scale)
		} else {
			m.renderer.SetScale(m.scale)
			m.renderer.SetDimensions(m.width, m.height)
		}
		m.renderer.SetOptions(m.showGrid, m.showLabels)
		return m, nil

	case error:
		m.error = msg
		m.loading = false
		return m, nil
	}

	return m, nil
}

// View renders the floor plan
func (m FloorPlanModel) View() string {
	if m.loading {
		return m.renderLoading()
	}

	if m.error != nil {
		return m.renderError()
	}

	if m.layout == nil {
		return "Initializing..."
	}

	var content strings.Builder

	// Header
	header := m.renderHeader()
	content.WriteString(header)
	content.WriteString("\n\n")

	// Floor selection
	floorSelector := m.renderFloorSelector()
	content.WriteString(floorSelector)
	content.WriteString("\n\n")

	// Main floor plan
	if m.spatialData != nil && m.renderer != nil {
		floorPlan := m.renderer.RenderFloorPlan(m.spatialData, m.floorNumber)
		content.WriteString(floorPlan)
	} else {
		content.WriteString("No floor plan data available")
	}

	// Footer
	footer := m.renderFooter()
	content.WriteString("\n\n")
	content.WriteString(footer)

	return content.String()
}

// renderHeader renders the floor plan header
func (m FloorPlanModel) renderHeader() string {
	title := fmt.Sprintf("Floor Plan: %s", m.buildingID)
	status := fmt.Sprintf("Floor %d | Scale: 1:%.0f", m.floorNumber, m.scale*100)

	return m.layout.Header(title, status)
}

// renderFloorSelector renders the floor selection interface
func (m FloorPlanModel) renderFloorSelector() string {
	var content strings.Builder

	content.WriteString("Select Floor: ")

	// Show available floors
	for floor := 1; floor <= 5; floor++ {
		var style lipgloss.Style
		if floor == m.selectedFloor {
			style = m.styles.Primary
		} else if floor == m.floorNumber {
			style = m.styles.Secondary
		} else {
			style = m.styles.Muted
		}

		if floor == m.selectedFloor {
			content.WriteString(style.Render(fmt.Sprintf("[%d]", floor)))
		} else {
			content.WriteString(style.Render(fmt.Sprintf(" %d ", floor)))
		}

		if floor < 5 {
			content.WriteString(" ")
		}
	}

	return content.String()
}

// renderLoading renders the loading state
func (m FloorPlanModel) renderLoading() string {
	return m.styles.Info.Render("Loading floor plan data...")
}

// renderError renders the error state
func (m FloorPlanModel) renderError() string {
	return m.styles.Error.Render("Error: " + m.error.Error())
}

// renderFooter renders the floor plan footer
func (m FloorPlanModel) renderFooter() string {
	helpText := "[↑↓] Select Floor  [Enter] Load  [g] Toggle Grid  [l] Toggle Labels  [±] Zoom  [r] Refresh  [q] Quit"

	return m.layout.Footer(helpText)
}

// Message types
type SpatialDataMsg struct {
	Data services.SpatialData
}

// Commands
func (m FloorPlanModel) loadSpatialData() tea.Cmd {
	return func() tea.Msg {
		if m.dataService == nil {
			return error(fmt.Errorf("data service not initialized"))
		}

		ctx := context.Background()
		spatialData, err := m.dataService.GetSpatialData(ctx, m.buildingID)
		if err != nil {
			return error(err)
		}

		return SpatialDataMsg{Data: *spatialData}
	}
}
