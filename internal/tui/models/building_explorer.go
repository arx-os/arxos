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
	"github.com/arx-os/arxos/pkg/models/building"
)

// BuildingExplorerModel represents the building explorer TUI model
type BuildingExplorerModel struct {
	// Core state
	buildingID string
	building   *building.BuildingModel
	floors     []*building.Floor
	equipment  []*building.Equipment

	// Data service
	dataService *services.DataService

	// UI state
	selectedIndex int
	cursor        int
	width         int
	height        int
	loading       bool
	error         error

	// Navigation state
	currentLevel string // "building", "floor", "room", "equipment"
	currentID    string
	path         []string // Navigation breadcrumb

	// Configuration
	config *config.TUIConfig
	styles *utils.Styles
	layout *utils.Layout
}

// NewBuildingExplorerModel creates a new building explorer model
func NewBuildingExplorerModel(buildingID string, config *config.TUIConfig, dataService *services.DataService) *BuildingExplorerModel {
	theme := "dark" // Default theme
	if config != nil {
		theme = config.Theme
	}
	styles := utils.GetThemeStyles(theme)

	return &BuildingExplorerModel{
		buildingID:   buildingID,
		config:       config,
		styles:       styles,
		dataService:  dataService,
		currentLevel: "building",
		currentID:    buildingID,
		loading:      true,
	}
}

// Init initializes the building explorer model
func (m BuildingExplorerModel) Init() tea.Cmd {
	return tea.Batch(
		m.loadBuildingData(),
	)
}

// Update handles messages and updates the model
func (m BuildingExplorerModel) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
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
			maxItems := m.getMaxItems()
			if m.cursor < maxItems-1 {
				m.cursor++
			}
			return m, nil
		case "enter":
			return m, m.navigateToSelected()
		case "left", "h":
			return m, m.navigateUp()
		case "right", "l":
			return m, m.navigateDown()
		case "home":
			m.currentLevel = "building"
			m.currentID = m.buildingID
			m.path = []string{}
			m.cursor = 0
			return m, m.loadBuildingData()
		case "r":
			return m, m.refreshCurrentLevel()
		}

	case BuildingDataMsg:
		m.building = msg.Building
		m.floors = msg.Floors
		m.equipment = msg.Equipment
		m.loading = false
		return m, nil

	case error:
		m.error = msg
		m.loading = false
		return m, nil
	}

	return m, nil
}

// View renders the building explorer
func (m BuildingExplorerModel) View() string {
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

	// Header with breadcrumb
	header := m.renderHeader()
	content.WriteString(header)
	content.WriteString("\n\n")

	// Main content based on current level
	switch m.currentLevel {
	case "building":
		content.WriteString(m.renderBuildingView())
	case "floor":
		content.WriteString(m.renderFloorView())
	case "room":
		content.WriteString(m.renderRoomView())
	case "equipment":
		content.WriteString(m.renderEquipmentView())
	default:
		content.WriteString("Unknown view")
	}

	// Footer
	footer := m.renderFooter()
	content.WriteString("\n\n")
	content.WriteString(footer)

	return content.String()
}

// renderHeader renders the header with breadcrumb navigation
func (m BuildingExplorerModel) renderHeader() string {
	title := "Building Explorer"

	// Build breadcrumb
	var breadcrumb strings.Builder
	breadcrumb.WriteString("🏢 ")

	for i, pathItem := range m.path {
		if i > 0 {
			breadcrumb.WriteString(" > ")
		}
		breadcrumb.WriteString(pathItem)
	}

	if m.building != nil {
		breadcrumb.WriteString(" > ")
		breadcrumb.WriteString(m.building.Name)
	}

	return m.layout.Header(title, breadcrumb.String())
}

// renderBuildingView renders the building overview
func (m BuildingExplorerModel) renderBuildingView() string {
	var content strings.Builder

	if m.building == nil {
		return "No building data available"
	}

	// Building summary
	summary := fmt.Sprintf(`
Building: %s
├─ Address: %s
├─ Floors: %d
├─ Equipment: %d
└─ Description: %s
`,
		m.building.Name,
		m.building.Address,
		len(m.floors),
		len(m.equipment),
		m.building.Description,
	)

	content.WriteString(m.layout.Panel("Building Overview", summary))
	content.WriteString("\n\n")

	// Floors list
	content.WriteString("Floors:\n")
	for i, floor := range m.floors {
		var style lipgloss.Style
		if i == m.cursor {
			style = m.styles.Primary
		} else {
			style = m.styles.Secondary
		}

		cursor := "  "
		if i == m.cursor {
			cursor = "> "
		}

		floorText := fmt.Sprintf("%sFloor %d: %s", cursor, floor.Number, floor.Name)
		content.WriteString(style.Render(floorText))
		content.WriteString("\n")
	}

	return content.String()
}

// renderFloorView renders the floor view
func (m BuildingExplorerModel) renderFloorView() string {
	var content strings.Builder

	// Find current floor
	var currentFloor *building.Floor
	for _, floor := range m.floors {
		if floor.ID == m.currentID {
			currentFloor = floor
			break
		}
	}

	if currentFloor == nil {
		return "Floor not found"
	}

	// Floor summary
	summary := fmt.Sprintf(`
Floor %d: %s
├─ Height: %.1fm
├─ Elevation: %.1fm
├─ Rooms: %d
└─ Equipment: %d
`,
		currentFloor.Number,
		currentFloor.Name,
		currentFloor.Height,
		currentFloor.Elevation,
		len(currentFloor.Rooms),
		len(currentFloor.Equipment),
	)

	content.WriteString(m.layout.Panel("Floor Overview", summary))
	content.WriteString("\n\n")

	// Rooms list
	content.WriteString("Rooms:\n")
	for i, room := range currentFloor.Rooms {
		var style lipgloss.Style
		if i == m.cursor {
			style = m.styles.Primary
		} else {
			style = m.styles.Secondary
		}

		cursor := "  "
		if i == m.cursor {
			cursor = "> "
		}

		roomText := fmt.Sprintf("%s%s: %s", cursor, room.Number, room.Name)
		content.WriteString(style.Render(roomText))
		content.WriteString("\n")
	}

	return content.String()
}

// renderRoomView renders the room view
func (m BuildingExplorerModel) renderRoomView() string {
	var content strings.Builder

	// Find current room
	var currentRoom *building.Room
	for _, floor := range m.floors {
		for _, room := range floor.Rooms {
			if room.ID == m.currentID {
				currentRoom = &room
				break
			}
		}
		if currentRoom != nil {
			break
		}
	}

	if currentRoom == nil {
		return "Room not found"
	}

	// Room summary
	summary := fmt.Sprintf(`
Room %s: %s
├─ Type: %s
├─ Area: %.1f m²
├─ Height: %.1fm
└─ Equipment: %d items
`,
		currentRoom.Number,
		currentRoom.Name,
		currentRoom.Type,
		currentRoom.Area,
		currentRoom.Height,
		len(currentRoom.Equipment),
	)

	content.WriteString(m.layout.Panel("Room Overview", summary))
	content.WriteString("\n\n")

	// Equipment in room
	content.WriteString("Equipment:\n")
	roomEquipment := m.getEquipmentInRoom(currentRoom.ID)

	for i, eq := range roomEquipment {
		var style lipgloss.Style
		if i == m.cursor {
			style = m.styles.Primary
		} else {
			style = m.styles.Secondary
		}

		cursor := "  "
		if i == m.cursor {
			cursor = "> "
		}

		statusStyle := m.styles.FormatStatus(eq.Status)
		equipmentText := fmt.Sprintf("%s%s [%s] %s", cursor, eq.Name, eq.Type, statusStyle)
		content.WriteString(style.Render(equipmentText))
		content.WriteString("\n")
	}

	return content.String()
}

// renderEquipmentView renders the equipment detail view
func (m BuildingExplorerModel) renderEquipmentView() string {
	var content strings.Builder

	// Find current equipment
	var currentEquipment *building.Equipment
	for _, eq := range m.equipment {
		if eq.ID == m.currentID {
			currentEquipment = eq
			break
		}
	}

	if currentEquipment == nil {
		return "Equipment not found"
	}

	// Equipment details
	details := fmt.Sprintf(`
Equipment: %s
├─ Type: %s
├─ Status: %s
├─ Location: %s
├─ Model: %s
└─ Serial: %s
`,
		currentEquipment.Name,
		currentEquipment.Type,
		currentEquipment.Status,
		m.formatLocation(currentEquipment),
		currentEquipment.Model,
		currentEquipment.SerialNumber,
	)

	content.WriteString(m.layout.Panel("Equipment Details", details))
	content.WriteString("\n\n")

	// Spatial information
	if currentEquipment.Position != nil {
		spatial := fmt.Sprintf(`
Spatial Information:
├─ Position: (%.1f, %.1f, %.1f)
├─ Floor: %s
└─ Room: %s
`,
			currentEquipment.Position.X,
			currentEquipment.Position.Y,
			currentEquipment.Position.Z,
			currentEquipment.FloorID,
			currentEquipment.RoomID,
		)

		content.WriteString(m.layout.Panel("Spatial Data", spatial))
	}

	return content.String()
}

// renderLoading renders the loading state
func (m BuildingExplorerModel) renderLoading() string {
	return m.styles.Info.Render("Loading building data...")
}

// renderError renders the error state
func (m BuildingExplorerModel) renderError() string {
	return m.styles.Error.Render("Error: " + m.error.Error())
}

// renderFooter renders the footer with navigation help
func (m BuildingExplorerModel) renderFooter() string {
	helpText := "[↑↓] Navigate  [Enter] Select  [←] Back  [→] Forward  [Home] Root  [r] Refresh  [q] Quit"
	return m.layout.Footer(helpText)
}

// Helper methods
func (m BuildingExplorerModel) getMaxItems() int {
	switch m.currentLevel {
	case "building":
		return len(m.floors)
	case "floor":
		for _, floor := range m.floors {
			if floor.ID == m.currentID {
				return len(floor.Rooms)
			}
		}
		return 0
	case "room":
		roomEquipment := m.getEquipmentInRoom(m.currentID)
		return len(roomEquipment)
	default:
		return 0
	}
}

func (m BuildingExplorerModel) getEquipmentInRoom(roomID string) []*building.Equipment {
	var equipment []*building.Equipment
	for _, eq := range m.equipment {
		if eq.RoomID == roomID {
			equipment = append(equipment, eq)
		}
	}
	return equipment
}

func (m BuildingExplorerModel) formatLocation(eq *building.Equipment) string {
	if eq.Position != nil {
		return fmt.Sprintf("(%.1f, %.1f, %.1f)", eq.Position.X, eq.Position.Y, eq.Position.Z)
	}
	return "Unknown"
}

// Navigation methods
func (m BuildingExplorerModel) navigateToSelected() tea.Cmd {
	switch m.currentLevel {
	case "building":
		if m.cursor < len(m.floors) {
			floor := m.floors[m.cursor]
			m.currentLevel = "floor"
			m.currentID = floor.ID
			m.path = append(m.path, m.building.Name)
			m.cursor = 0
			return m.loadFloorData(floor.ID)
		}
	case "floor":
		for _, floor := range m.floors {
			if floor.ID == m.currentID && m.cursor < len(floor.Rooms) {
				room := floor.Rooms[m.cursor]
				m.currentLevel = "room"
				m.currentID = room.ID
				m.path = append(m.path, fmt.Sprintf("Floor %d", floor.Number))
				m.cursor = 0
				return m.loadRoomData(room.ID)
			}
		}
	case "room":
		roomEquipment := m.getEquipmentInRoom(m.currentID)
		if m.cursor < len(roomEquipment) {
			eq := roomEquipment[m.cursor]
			m.currentLevel = "equipment"
			m.currentID = eq.ID
			// Find room name for path
			for _, floor := range m.floors {
				for _, room := range floor.Rooms {
					if room.ID == m.currentID {
						m.path = append(m.path, fmt.Sprintf("Room %s", room.Number))
						break
					}
				}
			}
			m.cursor = 0
			return m.loadEquipmentData(eq.ID)
		}
	}
	return nil
}

func (m BuildingExplorerModel) navigateUp() tea.Cmd {
	if len(m.path) > 0 {
		// Remove last path item
		m.path = m.path[:len(m.path)-1]
		m.cursor = 0

		// Determine new level and ID
		if len(m.path) == 0 {
			m.currentLevel = "building"
			m.currentID = m.buildingID
			return m.loadBuildingData()
		} else if len(m.path) == 1 {
			m.currentLevel = "floor"
			// Find floor ID from path
			for _, floor := range m.floors {
				if fmt.Sprintf("Floor %d", floor.Number) == m.path[0] {
					m.currentID = floor.ID
					break
				}
			}
			return m.loadFloorData(m.currentID)
		}
	}
	return nil
}

func (m BuildingExplorerModel) navigateDown() tea.Cmd {
	return m.navigateToSelected()
}

func (m BuildingExplorerModel) refreshCurrentLevel() tea.Cmd {
	switch m.currentLevel {
	case "building":
		return m.loadBuildingData()
	case "floor":
		return m.loadFloorData(m.currentID)
	case "room":
		return m.loadRoomData(m.currentID)
	case "equipment":
		return m.loadEquipmentData(m.currentID)
	}
	return nil
}

// Data loading methods
func (m BuildingExplorerModel) loadBuildingData() tea.Cmd {
	return func() tea.Msg {
		if m.dataService == nil {
			return error(fmt.Errorf("data service not initialized"))
		}

		ctx := context.Background()
		buildingData, err := m.dataService.GetBuildingData(ctx, m.buildingID)
		if err != nil {
			return error(err)
		}

		return BuildingDataMsg{
			Building:  buildingData.Building,
			Floors:    buildingData.Floors,
			Equipment: buildingData.Equipment,
			Alerts:    buildingData.Alerts,
			Metrics:   buildingData.Metrics,
		}
	}
}

func (m BuildingExplorerModel) loadFloorData(floorID string) tea.Cmd {
	// For now, return nil - data is already loaded
	// In a real implementation, this would load specific floor data
	return nil
}

func (m BuildingExplorerModel) loadRoomData(roomID string) tea.Cmd {
	// For now, return nil - data is already loaded
	// In a real implementation, this would load specific room data
	return nil
}

func (m BuildingExplorerModel) loadEquipmentData(equipmentID string) tea.Cmd {
	// For now, return nil - data is already loaded
	// In a real implementation, this would load specific equipment data
	return nil
}
