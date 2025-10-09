package models

import (
	"context"
	"fmt"
	"strings"

	tea "github.com/charmbracelet/bubbletea"
	"github.com/charmbracelet/lipgloss"

	"github.com/arx-os/arxos/internal/config"
	"github.com/arx-os/arxos/internal/tui/services"
	"github.com/arx-os/arxos/internal/tui/utils"
)

// SpatialQueryModel represents the spatial query TUI model
type SpatialQueryModel struct {
	// Core state
	queryResults []services.EquipmentPosition
	spatialData  *services.SpatialData

	// Data service
	dataService *services.DataService

	// UI state
	cursor  int
	width   int
	height  int
	loading bool
	error   error

	// Query state
	currentQuery *services.SpatialQuery
	queryMode    string // "radius", "bbox", "floor", "type"

	// Input state
	inputMode   bool
	inputBuffer string
	inputLabel  string

	// Configuration
	config *config.TUIConfig
	styles *utils.Styles
	layout *utils.Layout
}

// NewSpatialQueryModel creates a new spatial query model
func NewSpatialQueryModel(config *config.TUIConfig, dataService *services.DataService) *SpatialQueryModel {
	theme := "dark" // Default theme
	if config != nil {
		theme = config.Theme
	}
	styles := utils.GetThemeStyles(theme)

	return &SpatialQueryModel{
		config:      config,
		styles:      styles,
		dataService: dataService,
		queryMode:   "radius",
		loading:     false,
	}
}

// Init initializes the spatial query model
func (m SpatialQueryModel) Init() tea.Cmd {
	return tea.Batch(
		m.loadSpatialData(),
	)
}

// Update handles messages and updates the model
func (m SpatialQueryModel) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	switch msg := msg.(type) {
	case tea.WindowSizeMsg:
		m.width = msg.Width
		m.height = msg.Height
		m.layout = utils.NewLayout(msg.Width, msg.Height, m.styles)
		return m, nil

	case tea.KeyMsg:
		switch msg.String() {
		case "ctrl+c", "q":
			return m, tea.Quit
		case "up", "k":
			if m.cursor > 0 {
				m.cursor--
			}
			return m, nil
		case "down", "j":
			if m.cursor < len(m.queryResults)-1 {
				m.cursor++
			}
			return m, nil
		case "enter":
			if m.inputMode {
				return m, m.processInput()
			} else {
				return m, m.showEquipmentDetails()
			}
		case "escape":
			m.inputMode = false
			m.inputBuffer = ""
			m.inputLabel = ""
			return m, nil
		case "1":
			return m, m.setQueryMode("radius")
		case "2":
			return m, m.setQueryMode("bbox")
		case "3":
			return m, m.setQueryMode("floor")
		case "4":
			return m, m.setQueryMode("type")
		case "r":
			return m, m.executeQuery()
		case "c":
			return m, m.clearResults()
		}

		// Handle input mode
		if m.inputMode {
			switch msg.String() {
			case "backspace":
				if len(m.inputBuffer) > 0 {
					m.inputBuffer = m.inputBuffer[:len(m.inputBuffer)-1]
				}
				return m, nil
			default:
				if len(msg.String()) == 1 {
					m.inputBuffer += msg.String()
				}
				return m, nil
			}
		}

	case SpatialDataMsg:
		m.spatialData = &msg.Data
		m.loading = false
		return m, nil

	case QueryResultsMsg:
		m.queryResults = msg.Results
		m.loading = false
		return m, nil

	case error:
		m.error = msg
		m.loading = false
		return m, nil
	}

	return m, nil
}

// View renders the spatial query interface
func (m SpatialQueryModel) View() string {
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

	// Query interface
	queryInterface := m.renderQueryInterface()
	content.WriteString(queryInterface)
	content.WriteString("\n\n")

	// Results
	results := m.renderResults()
	content.WriteString(results)
	content.WriteString("\n\n")

	// Footer
	footer := m.renderFooter()
	content.WriteString(footer)

	return content.String()
}

// renderHeader renders the header
func (m SpatialQueryModel) renderHeader() string {
	title := "Spatial Query Interface"
	subtitle := fmt.Sprintf("%d results found", len(m.queryResults))

	return m.layout.Header(title, subtitle)
}

// renderQueryInterface renders the query input interface
func (m SpatialQueryModel) renderQueryInterface() string {
	var content strings.Builder

	content.WriteString("Query Mode: ")

	// Mode selection
	modes := []string{"[1] Radius", "[2] Bounding Box", "[3] Floor", "[4] Type"}
	for i, mode := range modes {
		var style lipgloss.Style
		if strings.Contains(mode, m.queryMode) {
			style = m.styles.Primary
		} else {
			style = m.styles.Secondary
		}
		content.WriteString(style.Render(mode))
		if i < len(modes)-1 {
			content.WriteString("  ")
		}
	}
	content.WriteString("\n\n")

	// Current query display
	content.WriteString("Current Query:\n")
	content.WriteString(m.renderCurrentQuery())
	content.WriteString("\n")

	// Input interface
	if m.inputMode {
		content.WriteString(m.renderInputInterface())
	} else {
		content.WriteString(m.renderQueryOptions())
	}

	return content.String()
}

// renderCurrentQuery renders the current query parameters
func (m SpatialQueryModel) renderCurrentQuery() string {
	if m.currentQuery == nil {
		return m.styles.Muted.Render("No query defined")
	}

	var content strings.Builder
	content.WriteString(fmt.Sprintf("Type: %s\n", m.currentQuery.Type))

	switch m.currentQuery.Type {
	case "radius":
		if m.currentQuery.Center != nil {
			content.WriteString(fmt.Sprintf("Center: (%.1f, %.1f, %.1f)\n",
				m.currentQuery.Center.X, m.currentQuery.Center.Y, m.currentQuery.Center.Z))
		}
		if m.currentQuery.Radius != nil {
			content.WriteString(fmt.Sprintf("Radius: %.1fm\n", *m.currentQuery.Radius))
		}
	case "bbox":
		if m.currentQuery.BoundingBox != nil {
			content.WriteString(fmt.Sprintf("Min: (%.1f, %.1f, %.1f)\n",
				m.currentQuery.BoundingBox.Min.X, m.currentQuery.BoundingBox.Min.Y, m.currentQuery.BoundingBox.Min.Z))
			content.WriteString(fmt.Sprintf("Max: (%.1f, %.1f, %.1f)\n",
				m.currentQuery.BoundingBox.Max.X, m.currentQuery.BoundingBox.Max.Y, m.currentQuery.BoundingBox.Max.Z))
		}
	case "floor":
		if m.currentQuery.Floor != nil {
			content.WriteString(fmt.Sprintf("Floor: %d\n", *m.currentQuery.Floor))
		}
	}

	return content.String()
}

// renderInputInterface renders the input interface
func (m SpatialQueryModel) renderInputInterface() string {
	var content strings.Builder

	content.WriteString(m.styles.Primary.Render(fmt.Sprintf("%s: %s_", m.inputLabel, m.inputBuffer)))
	content.WriteString("\n")
	content.WriteString(m.styles.Muted.Render("[Enter] Confirm  [Escape] Cancel"))

	return content.String()
}

// renderQueryOptions renders the query configuration options
func (m SpatialQueryModel) renderQueryOptions() string {
	var content strings.Builder

	switch m.queryMode {
	case "radius":
		content.WriteString("Configure Radius Query:\n")
		content.WriteString("[x] Set center point (X,Y,Z)\n")
		content.WriteString("[r] Set radius in meters\n")
		content.WriteString("[Enter] Execute query\n")
	case "bbox":
		content.WriteString("Configure Bounding Box Query:\n")
		content.WriteString("[min] Set minimum coordinates (X,Y,Z)\n")
		content.WriteString("[max] Set maximum coordinates (X,Y,Z)\n")
		content.WriteString("[Enter] Execute query\n")
	case "floor":
		content.WriteString("Configure Floor Query:\n")
		content.WriteString("[f] Set floor number\n")
		content.WriteString("[Enter] Execute query\n")
	case "type":
		content.WriteString("Configure Type Query:\n")
		content.WriteString("[t] Set equipment type\n")
		content.WriteString("[Enter] Execute query\n")
	}

	return content.String()
}

// renderResults renders the query results
func (m SpatialQueryModel) renderResults() string {
	if len(m.queryResults) == 0 {
		return m.styles.Warning.Render("No results found")
	}

	var content strings.Builder

	content.WriteString("Query Results:\n")
	content.WriteString(strings.Repeat("─", 80))
	content.WriteString("\n")

	// Table header
	header := fmt.Sprintf("%-15s %-12s %-20s %-15s %-10s",
		"Equipment ID", "Type", "Position", "Confidence", "Source")
	content.WriteString(m.styles.Header.Render(header))
	content.WriteString("\n")
	content.WriteString(strings.Repeat("─", 80))
	content.WriteString("\n")

	// Results rows
	for i, result := range m.queryResults {
		var style lipgloss.Style
		if i == m.cursor {
			style = m.styles.Primary
		} else {
			style = m.styles.Secondary
		}

		// Position formatting
		position := "Unknown"
		if result.Position3D != nil {
			position = fmt.Sprintf("(%.1f,%.1f,%.1f)",
				result.Position3D.X, result.Position3D.Y, result.Position3D.Z)
		}

		// Confidence formatting
		confidence := "Unknown"
		switch result.PositionConfidence {
		case 0:
			confidence = "Estimated"
		case 1:
			confidence = "Low"
		case 2:
			confidence = "Medium"
		case 3:
			confidence = "High"
		}

		row := fmt.Sprintf("%-15s %-12s %-20s %-15s %-10s",
			result.EquipmentID,
			m.getEquipmentType(result.EquipmentID),
			position,
			confidence,
			result.PositionSource,
		)

		content.WriteString(style.Render(row))
		content.WriteString("\n")
	}

	return content.String()
}

// renderLoading renders the loading state
func (m SpatialQueryModel) renderLoading() string {
	return m.styles.Info.Render("Loading spatial data...")
}

// renderError renders the error state
func (m SpatialQueryModel) renderError() string {
	return m.styles.Error.Render("Error: " + m.error.Error())
}

// renderFooter renders the footer with help
func (m SpatialQueryModel) renderFooter() string {
	var helpText string

	if m.inputMode {
		helpText = "[Type] Input  [Enter] Confirm  [Escape] Cancel"
	} else {
		helpText = "[1-4] Query Mode  [↑↓] Navigate  [Enter] Details  [r] Execute  [c] Clear  [q] Quit"
	}

	return m.layout.Footer(helpText)
}

// Helper methods
func (m SpatialQueryModel) getEquipmentType(equipmentID string) string {
	// This would look up the equipment type from the equipment data
	// For now, return a mock type
	return "Unknown"
}

// Query methods
func (m SpatialQueryModel) setQueryMode(mode string) tea.Cmd {
	m.queryMode = mode
	m.currentQuery = &services.SpatialQuery{Type: mode}
	m.inputMode = false
	m.inputBuffer = ""

	return nil
}

func (m SpatialQueryModel) processInput() tea.Cmd {
	// Process the input based on the current query mode and input label
	switch m.inputLabel {
	case "center_x", "center_y", "center_z":
		// Handle center point coordinates
		return m.updateCenterPoint()
	case "radius":
		// Handle radius input
		return m.updateRadius()
	case "floor":
		// Handle floor input
		return m.updateFloor()
	case "type":
		// Handle type input
		return m.updateType()
	}

	m.inputMode = false
	m.inputBuffer = ""
	return nil
}

func (m SpatialQueryModel) updateCenterPoint() tea.Cmd {
	// This would update the center point coordinates
	// For now, just exit input mode
	m.inputMode = false
	m.inputBuffer = ""
	return nil
}

func (m SpatialQueryModel) updateRadius() tea.Cmd {
	// This would update the radius
	// For now, just exit input mode
	m.inputMode = false
	m.inputBuffer = ""
	return nil
}

func (m SpatialQueryModel) updateFloor() tea.Cmd {
	// This would update the floor
	// For now, just exit input mode
	m.inputMode = false
	m.inputBuffer = ""
	return nil
}

func (m SpatialQueryModel) updateType() tea.Cmd {
	// This would update the equipment type
	// For now, just exit input mode
	m.inputMode = false
	m.inputBuffer = ""
	return nil
}

func (m SpatialQueryModel) executeQuery() tea.Cmd {
	return func() tea.Msg {
		if m.dataService == nil {
			return error(fmt.Errorf("data service not initialized"))
		}

		ctx := context.Background()
		// Use DataService to get spatial data
		_, err := m.dataService.GetSpatialData(ctx, "default")
		if err != nil {
			return error(err)
		}

		// Convert spatial data to equipment positions for display
		var resultsSlice []services.EquipmentPosition
		// TODO: Full implementation would convert spatialData.Floors.Equipment
		// to EquipmentPosition format based on query criteria

		return QueryResultsMsg{Results: resultsSlice}
	}
}

func (m SpatialQueryModel) clearResults() tea.Cmd {
	m.queryResults = []services.EquipmentPosition{}
	m.cursor = 0
	return nil
}

func (m SpatialQueryModel) showEquipmentDetails() tea.Cmd {
	// This would show detailed equipment information
	// For now, just return nil
	return nil
}

// Data loading
func (m SpatialQueryModel) loadSpatialData() tea.Cmd {
	return func() tea.Msg {
		if m.dataService == nil {
			return error(fmt.Errorf("data service not initialized"))
		}

		ctx := context.Background()
		spatialData, err := m.dataService.GetSpatialData(ctx, "default")
		if err != nil {
			return error(err)
		}

		return SpatialDataMsg{Data: *spatialData}
	}
}

// Message types
type QueryResultsMsg struct {
	Results []services.EquipmentPosition
}
