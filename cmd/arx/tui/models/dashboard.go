package models

import (
	"context"
	"fmt"
	"strings"
	"time"

	tea "github.com/charmbracelet/bubbletea"
	"github.com/charmbracelet/lipgloss"

	"github.com/arx-os/arxos/cmd/arx/tui/services"
	"github.com/arx-os/arxos/cmd/arx/tui/utils"
	"github.com/arx-os/arxos/internal/config"
	"github.com/arx-os/arxos/pkg/models/building"
)

// DashboardModel represents the main dashboard TUI model
type DashboardModel struct {
	// Core state
	building  *building.BuildingModel
	equipment []*building.Equipment
	alerts    []services.Alert
	metrics   *services.BuildingMetrics

	// Data service
	dataService *services.DataService

	// UI state
	selectedTab int
	cursor      int
	width       int
	height      int
	loading     bool
	error       error

	// Configuration
	config *config.TUIConfig
	styles *utils.Styles
	layout *utils.Layout

	// Real-time updates
	lastUpdate  time.Time
	updateTimer time.Duration
}

// TUIConfig represents TUI configuration (imported from parent package)
type TUIConfig struct {
	Enabled           bool
	Theme             string
	UpdateInterval    string
	MaxEquipment      int
	RealTimeEnabled   bool
	AnimationsEnabled bool
}

// NewDashboardModel creates a new dashboard model
func NewDashboardModel(config *config.TUIConfig, dataService *services.DataService) *DashboardModel {
	theme := "dark" // Default theme
	if config != nil {
		theme = config.Theme
	}
	styles := utils.GetThemeStyles(theme)

	updateTimer := 1 * time.Second // Default update interval
	if config != nil {
		if parsed, err := config.ParseUpdateInterval(); err == nil {
			updateTimer = parsed
		}
	}

	return &DashboardModel{
		config:      config,
		styles:      styles,
		dataService: dataService,
		updateTimer: updateTimer,
		loading:     true,
	}
}

// Init initializes the dashboard model
func (m DashboardModel) Init() tea.Cmd {
	return tea.Batch(
		m.loadBuildingData(),
		m.startUpdateTimer(),
	)
}

// Update handles messages and updates the model
func (m DashboardModel) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
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
		case "tab":
			m.selectedTab = (m.selectedTab + 1) % 4
			return m, nil
		case "shift+tab":
			m.selectedTab = (m.selectedTab - 1 + 4) % 4
			return m, nil
		case "up", "k":
			if m.cursor > 0 {
				m.cursor--
			}
			return m, nil
		case "down", "j":
			if m.cursor < len(m.equipment)-1 {
				m.cursor++
			}
			return m, nil
		case "enter":
			return m, m.selectEquipment()
		case "r":
			return m, m.refreshData()
		}

	case BuildingDataMsg:
		m.building = msg.Building
		m.equipment = msg.Equipment
		m.alerts = msg.Alerts
		m.metrics = msg.Metrics
		m.loading = false
		m.lastUpdate = time.Now()
		return m, nil

	case UpdateTimerMsg:
		if m.config.RealTimeEnabled {
			return m, m.loadBuildingData()
		}
		return m, m.startUpdateTimer()

	case error:
		m.error = msg
		m.loading = false
		return m, nil
	}

	return m, nil
}

// View renders the dashboard
func (m DashboardModel) View() string {
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

	// Main content based on selected tab
	switch m.selectedTab {
	case 0:
		content.WriteString(m.renderOverview())
	case 1:
		content.WriteString(m.renderEquipment())
	case 2:
		content.WriteString(m.renderAlerts())
	case 3:
		content.WriteString(m.renderMetrics())
	}

	// Footer
	footer := m.renderFooter()
	content.WriteString("\n\n")
	content.WriteString(footer)

	return content.String()
}

// renderHeader renders the dashboard header
func (m DashboardModel) renderHeader() string {
	if m.building == nil {
		return m.styles.Header.Render("ArxOS Building Manager")
	}

	title := fmt.Sprintf("Building: %s", m.building.Name)
	status := "Operational"
	if m.metrics != nil {
		status = fmt.Sprintf("Status: %s", status)
	}

	return m.layout.Header(title, status)
}

// renderOverview renders the building overview tab
func (m DashboardModel) renderOverview() string {
	if m.building == nil || m.metrics == nil {
		return m.styles.Muted.Render("No building data available")
	}

	var content strings.Builder

	// Building summary
	summary := fmt.Sprintf(`
Building Summary:
├─ Status: Operational
├─ Floors: %d
├─ Equipment: %d total
├─ Operational: %d (%.1f%%)
├─ Maintenance: %d (%.1f%%)
└─ Offline: %d (%.1f%%)
`,
		4, // TODO: Get actual floor count from building data
		m.metrics.TotalEquipment,
		m.metrics.Operational,
		float64(m.metrics.Operational)/float64(m.metrics.TotalEquipment)*100,
		m.metrics.Maintenance,
		float64(m.metrics.Maintenance)/float64(m.metrics.TotalEquipment)*100,
		m.metrics.Offline,
		float64(m.metrics.Offline)/float64(m.metrics.TotalEquipment)*100,
	)

	content.WriteString(m.layout.Panel("Building Overview", summary))
	content.WriteString("\n\n")

	// Performance metrics
	metrics := fmt.Sprintf(`
Performance Metrics:
├─ Uptime: %.1f%%
├─ Energy/m²: %.1f kWh
├─ Response Time: %v
└─ Coverage: %.1f%%
`,
		m.metrics.Uptime,
		m.metrics.EnergyPerSqM,
		m.metrics.ResponseTime,
		m.metrics.Coverage,
	)

	content.WriteString(m.layout.Panel("Performance", metrics))

	return content.String()
}

// renderEquipment renders the equipment tab
func (m DashboardModel) renderEquipment() string {
	if len(m.equipment) == 0 {
		return m.styles.Muted.Render("No equipment data available")
	}

	var content strings.Builder

	// Equipment list
	content.WriteString(m.styles.Header.Render("Equipment Status"))
	content.WriteString("\n\n")

	// Show equipment with cursor highlighting
	for i, eq := range m.equipment {
		if i >= 20 { // Limit display to first 20 items
			break
		}

		var line strings.Builder

		// Cursor indicator
		if i == m.cursor {
			line.WriteString("> ")
		} else {
			line.WriteString("  ")
		}

		// Equipment info
		line.WriteString(m.styles.FormatEquipment(eq.ID, eq.Type, string(eq.Status)))

		if eq.Position != nil {
			line.WriteString(" ")
			line.WriteString(m.styles.FormatCoordinates(eq.Position.X, eq.Position.Y, eq.Position.Z))
		}

		content.WriteString(line.String())
		content.WriteString("\n")
	}

	if len(m.equipment) > 20 {
		content.WriteString(fmt.Sprintf("\n... and %d more items", len(m.equipment)-20))
	}

	return content.String()
}

// renderAlerts renders the alerts tab
func (m DashboardModel) renderAlerts() string {
	if len(m.alerts) == 0 {
		return m.styles.Success.Render("No active alerts")
	}

	var content strings.Builder

	content.WriteString(m.styles.Header.Render("Active Alerts"))
	content.WriteString("\n\n")

	for _, alert := range m.alerts {
		var alertStyle lipgloss.Style
		switch alert.Severity {
		case "critical", "error":
			alertStyle = m.styles.Error
		case "warning":
			alertStyle = m.styles.Warning
		default:
			alertStyle = m.styles.Info
		}

		alertText := fmt.Sprintf("⚠️  %s: %s", alert.Severity, alert.Message)
		content.WriteString(alertStyle.Render(alertText))
		content.WriteString("\n")
	}

	return content.String()
}

// renderMetrics renders the metrics tab
func (m DashboardModel) renderMetrics() string {
	if m.metrics == nil {
		return m.styles.Muted.Render("No metrics data available")
	}

	var content strings.Builder

	// Uptime progress bar
	uptimeBar := m.layout.ProgressBar(int(m.metrics.Uptime), 100, "Uptime")
	content.WriteString(uptimeBar)
	content.WriteString("\n\n")

	// Coverage progress bar
	coverageBar := m.layout.ProgressBar(int(m.metrics.Coverage), 100, "Coverage")
	content.WriteString(coverageBar)
	content.WriteString("\n\n")

	// Status grid
	statusItems := []utils.StatusItem{
		{Label: "Operational", Status: "ok"},
		{Label: "Maintenance", Status: "warning"},
		{Label: "Offline", Status: "error"},
	}

	statusGrid := m.layout.StatusGrid(statusItems)
	content.WriteString(m.layout.Panel("Status Distribution", statusGrid))

	return content.String()
}

// renderLoading renders the loading state
func (m DashboardModel) renderLoading() string {
	return m.styles.Info.Render("Loading building data...")
}

// renderError renders the error state
func (m DashboardModel) renderError() string {
	return m.styles.Error.Render("Error: " + m.error.Error())
}

// renderFooter renders the dashboard footer
func (m DashboardModel) renderFooter() string {
	helpText := "[Tab] Switch Tabs  [↑↓] Navigate  [Enter] Select  [r] Refresh  [q] Quit"
	if m.lastUpdate.IsZero() {
		helpText += "  Last Update: Never"
	} else {
		helpText += fmt.Sprintf("  Last Update: %s", m.lastUpdate.Format("15:04:05"))
	}

	return m.layout.Footer(helpText)
}

// Message types for the dashboard
type BuildingDataMsg struct {
	Building  *building.BuildingModel
	Floors    []*building.Floor
	Equipment []*building.Equipment
	Alerts    []services.Alert
	Metrics   *services.BuildingMetrics
}

type UpdateTimerMsg time.Time

// Commands
func (m DashboardModel) loadBuildingData() tea.Cmd {
	return func() tea.Msg {
		if m.dataService == nil {
			return error(fmt.Errorf("data service not initialized"))
		}

		ctx := context.Background()
		buildingData, err := m.dataService.GetBuildingData(ctx, "default")
		if err != nil {
			return error(err)
		}

		return BuildingDataMsg{
			Building:  buildingData.Building,
			Equipment: buildingData.Equipment,
			Alerts:    buildingData.Alerts,
			Metrics:   buildingData.Metrics,
		}
	}
}

func (m DashboardModel) startUpdateTimer() tea.Cmd {
	return tea.Tick(m.updateTimer, func(t time.Time) tea.Msg {
		return UpdateTimerMsg(t)
	})
}

func (m DashboardModel) selectEquipment() tea.Cmd {
	return func() tea.Msg {
		if m.cursor < len(m.equipment) {
			// This would navigate to equipment details
			return tea.Msg("equipment_selected")
		}
		return nil
	}
}

func (m DashboardModel) refreshData() tea.Cmd {
	m.loading = true
	return m.loadBuildingData()
}
