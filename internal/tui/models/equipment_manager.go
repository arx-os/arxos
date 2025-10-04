package models

import (
	"context"
	"fmt"
	"sort"
	"strings"

	tea "github.com/charmbracelet/bubbletea"
	"github.com/charmbracelet/lipgloss"

	"github.com/arx-os/arxos/internal/config"
	"github.com/arx-os/arxos/internal/tui/services"
	"github.com/arx-os/arxos/internal/tui/utils"
	"github.com/arx-os/arxos/pkg/models/building"
)

// EquipmentManagerModel represents the equipment manager TUI model
type EquipmentManagerModel struct {
	// Core state
	equipment         []*building.Equipment
	filteredEquipment []*building.Equipment

	// Data service
	dataService *services.DataService

	// UI state
	cursor  int
	width   int
	height  int
	loading bool
	error   error

	// Filtering and sorting
	filterType   string // "all", "hvac", "electrical", "plumbing", etc.
	filterStatus string // "all", "operational", "maintenance", "offline"
	sortBy       string // "name", "type", "status", "location"
	sortOrder    string // "asc", "desc"

	// Search
	searchQuery string
	searchMode  bool

	// Configuration
	config *config.TUIConfig
	styles *utils.Styles
	layout *utils.Layout
}

// NewEquipmentManagerModel creates a new equipment manager model
func NewEquipmentManagerModel(config *config.TUIConfig, dataService *services.DataService) *EquipmentManagerModel {
	theme := "dark" // Default theme
	if config != nil {
		theme = config.Theme
	}
	styles := utils.GetThemeStyles(theme)

	return &EquipmentManagerModel{
		config:       config,
		styles:       styles,
		dataService:  dataService,
		filterType:   "all",
		filterStatus: "all",
		sortBy:       "name",
		sortOrder:    "asc",
		loading:      true,
	}
}

// Init initializes the equipment manager model
func (m EquipmentManagerModel) Init() tea.Cmd {
	return tea.Batch(
		m.loadEquipmentData(),
	)
}

// Update handles messages and updates the model
func (m EquipmentManagerModel) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
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
			if m.cursor < len(m.filteredEquipment)-1 {
				m.cursor++
			}
			return m, nil
		case "enter":
			return m, m.showEquipmentDetails()
		case "t":
			return m, m.cycleFilterType()
		case "s":
			return m, m.cycleFilterStatus()
		case "o":
			return m, m.cycleSortBy()
		case "r":
			return m, m.reverseSortOrder()
		case "/":
			m.searchMode = true
			return m, nil
		case "escape":
			m.searchMode = false
			m.searchQuery = ""
			m.applyFilters()
			return m, nil
		case "R":
			return m, m.loadEquipmentData()
		}

		// Handle search input
		if m.searchMode {
			switch msg.String() {
			case "backspace":
				if len(m.searchQuery) > 0 {
					m.searchQuery = m.searchQuery[:len(m.searchQuery)-1]
					m.applyFilters()
				}
				return m, nil
			case "enter":
				m.searchMode = false
				return m, nil
			default:
				if len(msg.String()) == 1 {
					m.searchQuery += msg.String()
					m.applyFilters()
				}
				return m, nil
			}
		}

	case EquipmentDataMsg:
		m.equipment = msg.Equipment
		m.applyFilters()
		m.loading = false
		return m, nil

	case error:
		m.error = msg
		m.loading = false
		return m, nil
	}

	return m, nil
}

// View renders the equipment manager
func (m EquipmentManagerModel) View() string {
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

	// Filters and search
	filters := m.renderFilters()
	content.WriteString(filters)
	content.WriteString("\n\n")

	// Equipment list
	equipmentList := m.renderEquipmentList()
	content.WriteString(equipmentList)
	content.WriteString("\n\n")

	// Footer
	footer := m.renderFooter()
	content.WriteString(footer)

	return content.String()
}

// renderHeader renders the header
func (m EquipmentManagerModel) renderHeader() string {
	title := "Equipment Manager"
	subtitle := fmt.Sprintf("%d equipment items", len(m.filteredEquipment))

	return m.layout.Header(title, subtitle)
}

// renderFilters renders the filter and search interface
func (m EquipmentManagerModel) renderFilters() string {
	var content strings.Builder

	content.WriteString("Filters: ")

	// Type filter
	typeStyle := m.styles.Primary
	if m.filterType != "all" {
		typeStyle = m.styles.Primary
	}
	content.WriteString(typeStyle.Render(fmt.Sprintf("[T]ype:%s", m.filterType)))
	content.WriteString("  ")

	// Status filter
	statusStyle := m.styles.Primary
	if m.filterStatus != "all" {
		statusStyle = m.styles.Primary
	}
	content.WriteString(statusStyle.Render(fmt.Sprintf("[S]tatus:%s", m.filterStatus)))
	content.WriteString("  ")

	// Sort options
	sortStyle := m.styles.Primary
	content.WriteString(sortStyle.Render(fmt.Sprintf("[O]rder:%s", m.sortBy)))
	content.WriteString("  ")

	// Search
	if m.searchMode {
		content.WriteString(m.styles.Primary.Render(fmt.Sprintf("Search: %s_", m.searchQuery)))
	} else {
		content.WriteString(m.styles.Secondary.Render("[/] Search"))
	}

	return content.String()
}

// renderEquipmentList renders the equipment list
func (m EquipmentManagerModel) renderEquipmentList() string {
	if len(m.filteredEquipment) == 0 {
		return m.styles.Warning.Render("No equipment found matching filters")
	}

	var content strings.Builder

	// Table header
	header := fmt.Sprintf("%-15s %-12s %-12s %-20s %-15s",
		"ID", "Type", "Status", "Name", "Location")
	content.WriteString(m.styles.Header.Render(header))
	content.WriteString("\n")
	content.WriteString(strings.Repeat("─", len(header)))
	content.WriteString("\n")

	// Equipment rows
	for i, eq := range m.filteredEquipment {
		var style lipgloss.Style
		if i == m.cursor {
			style = m.styles.Primary
		} else {
			style = m.styles.Secondary
		}

		// Status styling
		statusStyle := m.styles.GetStatusStyle(eq.Status)

		// Location formatting
		location := m.formatLocation(eq)
		if len(location) > 15 {
			location = location[:12] + "..."
		}

		row := fmt.Sprintf("%-15s %-12s %-12s %-20s %-15s",
			eq.ID,
			eq.Type,
			statusStyle.Render(eq.Status),
			eq.Name,
			location,
		)

		content.WriteString(style.Render(row))
		content.WriteString("\n")
	}

	return content.String()
}

// renderLoading renders the loading state
func (m EquipmentManagerModel) renderLoading() string {
	return m.styles.Info.Render("Loading equipment data...")
}

// renderError renders the error state
func (m EquipmentManagerModel) renderError() string {
	return m.styles.Error.Render("Error: " + m.error.Error())
}

// renderFooter renders the footer with help
func (m EquipmentManagerModel) renderFooter() string {
	var helpText string

	if m.searchMode {
		helpText = "[Type] Search  [Enter] Confirm  [Escape] Cancel"
	} else {
		helpText = "[↑↓] Navigate  [Enter] Details  [T] Type Filter  [S] Status Filter  [O] Sort  [R] Reverse  [/] Search  [r] Refresh  [q] Quit"
	}

	return m.layout.Footer(helpText)
}

// Helper methods

func (m EquipmentManagerModel) formatLocation(eq *building.Equipment) string {
	if eq.Position != nil {
		return fmt.Sprintf("(%.1f,%.1f,%.1f)", eq.Position.X, eq.Position.Y, eq.Position.Z)
	}
	return "Unknown"
}

// Filter and sort methods
func (m EquipmentManagerModel) applyFilters() {
	m.filteredEquipment = make([]*building.Equipment, 0)

	for _, eq := range m.equipment {
		// Type filter
		if m.filterType != "all" && !strings.EqualFold(eq.Type, m.filterType) {
			continue
		}

		// Status filter
		if m.filterStatus != "all" && !strings.EqualFold(eq.Status, m.filterStatus) {
			continue
		}

		// Search filter
		if m.searchQuery != "" {
			searchLower := strings.ToLower(m.searchQuery)
			eqLower := strings.ToLower(eq.Name + " " + eq.Type + " " + eq.ID)
			if !strings.Contains(eqLower, searchLower) {
				continue
			}
		}

		m.filteredEquipment = append(m.filteredEquipment, eq)
	}

	// Apply sorting
	m.sortEquipment()

	// Reset cursor if needed
	if m.cursor >= len(m.filteredEquipment) {
		m.cursor = 0
	}
}

func (m EquipmentManagerModel) sortEquipment() {
	sort.Slice(m.filteredEquipment, func(i, j int) bool {
		var result bool

		switch m.sortBy {
		case "name":
			result = m.filteredEquipment[i].Name < m.filteredEquipment[j].Name
		case "type":
			result = m.filteredEquipment[i].Type < m.filteredEquipment[j].Type
		case "status":
			result = m.filteredEquipment[i].Status < m.filteredEquipment[j].Status
		case "location":
			// Sort by Z (floor) first, then X, then Y
			if m.filteredEquipment[i].Position != nil && m.filteredEquipment[j].Position != nil {
				if m.filteredEquipment[i].Position.Z != m.filteredEquipment[j].Position.Z {
					result = m.filteredEquipment[i].Position.Z < m.filteredEquipment[j].Position.Z
				} else if m.filteredEquipment[i].Position.X != m.filteredEquipment[j].Position.X {
					result = m.filteredEquipment[i].Position.X < m.filteredEquipment[j].Position.X
				} else {
					result = m.filteredEquipment[i].Position.Y < m.filteredEquipment[j].Position.Y
				}
			} else {
				result = false
			}
		default:
			result = m.filteredEquipment[i].Name < m.filteredEquipment[j].Name
		}

		if m.sortOrder == "desc" {
			return !result
		}
		return result
	})
}

func (m EquipmentManagerModel) cycleFilterType() tea.Cmd {
	types := []string{"all", "hvac", "electrical", "plumbing", "lighting", "fire", "security"}
	currentIndex := 0

	for i, t := range types {
		if t == m.filterType {
			currentIndex = i
			break
		}
	}

	nextIndex := (currentIndex + 1) % len(types)
	m.filterType = types[nextIndex]
	m.applyFilters()

	return nil
}

func (m EquipmentManagerModel) cycleFilterStatus() tea.Cmd {
	statuses := []string{"all", "operational", "maintenance", "offline"}
	currentIndex := 0

	for i, s := range statuses {
		if s == m.filterStatus {
			currentIndex = i
			break
		}
	}

	nextIndex := (currentIndex + 1) % len(statuses)
	m.filterStatus = statuses[nextIndex]
	m.applyFilters()

	return nil
}

func (m EquipmentManagerModel) cycleSortBy() tea.Cmd {
	sortOptions := []string{"name", "type", "status", "location"}
	currentIndex := 0

	for i, s := range sortOptions {
		if s == m.sortBy {
			currentIndex = i
			break
		}
	}

	nextIndex := (currentIndex + 1) % len(sortOptions)
	m.sortBy = sortOptions[nextIndex]
	m.sortEquipment()

	return nil
}

func (m EquipmentManagerModel) reverseSortOrder() tea.Cmd {
	if m.sortOrder == "asc" {
		m.sortOrder = "desc"
	} else {
		m.sortOrder = "asc"
	}
	m.sortEquipment()

	return nil
}

func (m EquipmentManagerModel) showEquipmentDetails() tea.Cmd {
	// This would show detailed equipment information
	// For now, just return nil
	return nil
}

// Data loading
func (m EquipmentManagerModel) loadEquipmentData() tea.Cmd {
	return func() tea.Msg {
		if m.dataService == nil {
			return error(fmt.Errorf("data service not initialized"))
		}

		ctx := context.Background()
		buildingData, err := m.dataService.GetBuildingData(ctx, "default")
		if err != nil {
			return error(err)
		}

		return EquipmentDataMsg{
			Equipment: buildingData.Equipment,
		}
	}
}

// Message types
type EquipmentDataMsg struct {
	Equipment []*building.Equipment
}
