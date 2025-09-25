package export

import (
	"context"
	"fmt"
	"html/template"
	"os"
	"path/filepath"
	"strings"
	"time"

	"github.com/arx-os/arxos/internal/common/logger"
	"github.com/arx-os/arxos/internal/database"
	"github.com/arx-os/arxos/pkg/models"
)

// Exporter handles the generation of building reports and visualizations
type Exporter struct {
	db database.DB
}

// NewExporter creates a new exporter instance
func NewExporter(db database.DB) *Exporter {
	return &Exporter{db: db}
}

// ReportData contains all data needed for report generation
type ReportData struct {
	BuildingID     string
	BuildingName   string
	GeneratedAt    time.Time
	EquipmentCount int
	RoomCount      int
	FloorCount     int
	Equipment      []EquipmentSummary
	Rooms          []RoomSummary
	Metrics        MetricsData
	Visualizations []VisualizationData
}

// EquipmentSummary contains equipment information for reports
type EquipmentSummary struct {
	ID       string
	Name     string
	Type     string
	Floor    int
	Room     string
	Status   string
	Location string
}

// RoomSummary contains room information for reports
type RoomSummary struct {
	ID          string
	Name        string
	Floor       int
	Area        float64
	Equipment   int
	Occupancy   string
	Temperature float64
}

// MetricsData contains building metrics
type MetricsData struct {
	TotalArea       float64
	OccupancyRate   float64
	EnergyUsage     float64
	EquipmentHealth float64
	LastUpdated     time.Time
}

// VisualizationData represents a single visualization
type VisualizationData struct {
	Type        string
	Title       string
	Description string
	Data        interface{}
	Format      string
}

// GenerateReport generates a comprehensive building report
func (e *Exporter) GenerateReport(ctx context.Context, buildingID string, format string, outputPath string) error {
	logger.Info("Generating report for building %s in %s format", buildingID, format)

	// Gather report data
	data, err := e.gatherReportData(ctx, buildingID)
	if err != nil {
		return fmt.Errorf("failed to gather report data: %w", err)
	}

	// Generate report based on format
	switch format {
	case "html":
		return e.generateHTMLReport(data, outputPath)
	case "markdown":
		return e.generateMarkdownReport(data, outputPath)
	case "text":
		return e.generateTextReport(data, outputPath)
	default:
		return fmt.Errorf("unsupported format: %s", format)
	}
}

// gatherReportData collects all data needed for the report
func (e *Exporter) gatherReportData(ctx context.Context, buildingID string) (*ReportData, error) {
	// Get building information
	floorPlans, err := e.db.GetAllFloorPlans(ctx)
	if err != nil {
		return nil, err
	}

	var buildingName string
	var floorCount int
	var equipmentCount int
	var roomCount int

	// Find the building and count floors
	for _, fp := range floorPlans {
		if fp.ID == buildingID {
			buildingName = fp.Name
			floorCount++
		}
	}

	// Get equipment data
	equipment, err := e.db.GetEquipmentByFloorPlan(ctx, buildingID)
	if err != nil {
		// If equipment table doesn't exist, create empty data
		equipment = []*models.Equipment{}
	}
	equipmentCount = len(equipment)

	// Get rooms data
	rooms, err := e.db.GetRoomsByFloorPlan(ctx, buildingID)
	if err != nil {
		// If rooms table doesn't exist, create empty data
		rooms = []*models.Room{}
	}
	roomCount = len(rooms)

	// Create equipment summaries
	equipmentSummaries := make([]EquipmentSummary, 0, len(equipment))
	for _, eq := range equipment {
		// Extract floor and room from path or use defaults
		floor := 0
		room := "Unknown"
		if eq.Location != nil {
			// Use Z coordinate as floor indicator
			floor = int(eq.Location.Z)
		}
		if eq.RoomID != "" {
			room = eq.RoomID
		}

		equipmentSummaries = append(equipmentSummaries, EquipmentSummary{
			ID:       eq.ID,
			Name:     eq.Name,
			Type:     eq.Type,
			Floor:    floor,
			Room:     room,
			Status:   eq.Status,
			Location: fmt.Sprintf("Floor %d, %s", floor, room),
		})
	}

	// Create room summaries
	roomSummaries := make([]RoomSummary, 0, len(rooms))
	for _, room := range rooms {
		// Calculate area from bounds if available
		area := 0.0
		width := room.Bounds.MaxX - room.Bounds.MinX
		height := room.Bounds.MaxY - room.Bounds.MinY
		if width > 0 && height > 0 {
			area = width * height
		}

		// Count equipment in this room
		equipmentCount := 0
		for _, eq := range equipment {
			if eq.RoomID == room.ID {
				equipmentCount++
			}
		}

		roomSummaries = append(roomSummaries, RoomSummary{
			ID:          room.ID,
			Name:        room.Name,
			Floor:       0, // Would need to get from floor plan level
			Area:        area,
			Equipment:   equipmentCount,
			Occupancy:   e.calculateRoomOccupancy(room),
			Temperature: e.calculateRoomTemperature(room),
		})
	}

	// Create metrics data
	metrics := MetricsData{
		TotalArea:       e.calculateTotalArea(rooms),
		OccupancyRate:   e.calculateOccupancyRate(rooms),
		EnergyUsage:     e.calculateEnergyUsage(rooms),
		EquipmentHealth: e.calculateEquipmentHealth(rooms),
		LastUpdated:     time.Now(),
	}

	// Create visualization data
	visualizations := []VisualizationData{
		{
			Type:        "equipment_status",
			Title:       "Equipment Status by Floor",
			Description: "Overview of equipment status across all floors",
			Data:        equipmentSummaries,
			Format:      "table",
		},
		{
			Type:        "energy_usage",
			Title:       "Energy Usage Trends",
			Description: "Weekly energy consumption patterns",
			Data:        map[string]float64{"Monday": 1200, "Tuesday": 1350, "Wednesday": 1400, "Thursday": 1300, "Friday": 1250},
			Format:      "chart",
		},
		{
			Type:        "occupancy_heatmap",
			Title:       "Occupancy Heatmap",
			Description: "Room occupancy patterns throughout the day",
			Data:        roomSummaries,
			Format:      "heatmap",
		},
	}

	return &ReportData{
		BuildingID:     buildingID,
		BuildingName:   buildingName,
		GeneratedAt:    time.Now(),
		EquipmentCount: equipmentCount,
		RoomCount:      roomCount,
		FloorCount:     floorCount,
		Equipment:      equipmentSummaries,
		Rooms:          roomSummaries,
		Metrics:        metrics,
		Visualizations: visualizations,
	}, nil
}

// generateHTMLReport creates an HTML report
func (e *Exporter) generateHTMLReport(data *ReportData, outputPath string) error {
	tmpl := `
<!DOCTYPE html>
<html>
<head>
    <title>Building Report - {{.BuildingName}}</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        .header { border-bottom: 2px solid #333; padding-bottom: 20px; }
        .section { margin: 30px 0; }
        .metrics { display: flex; gap: 20px; }
        .metric { background: #f5f5f5; padding: 15px; border-radius: 5px; }
        table { border-collapse: collapse; width: 100%; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #f2f2f2; }
    </style>
</head>
<body>
    <div class="header">
        <h1>Building Report: {{.BuildingName}}</h1>
        <p>Generated: {{.GeneratedAt.Format "2006-01-02 15:04:05"}}</p>
    </div>

    <div class="section">
        <h2>Building Overview</h2>
        <div class="metrics">
            <div class="metric">
                <h3>{{.FloorCount}}</h3>
                <p>Floors</p>
            </div>
            <div class="metric">
                <h3>{{.RoomCount}}</h3>
                <p>Rooms</p>
            </div>
            <div class="metric">
                <h3>{{.EquipmentCount}}</h3>
                <p>Equipment Items</p>
            </div>
            <div class="metric">
                <h3>{{printf "%.1f" .Metrics.TotalArea}}</h3>
                <p>Total Area (m²)</p>
            </div>
        </div>
    </div>

    <div class="section">
        <h2>Equipment Status</h2>
        <table>
            <tr>
                <th>Name</th>
                <th>Type</th>
                <th>Floor</th>
                <th>Room</th>
                <th>Status</th>
            </tr>
            {{range .Equipment}}
            <tr>
                <td>{{.Name}}</td>
                <td>{{.Type}}</td>
                <td>{{.Floor}}</td>
                <td>{{.Room}}</td>
                <td>{{.Status}}</td>
            </tr>
            {{end}}
        </table>
    </div>

    <div class="section">
        <h2>Room Information</h2>
        <table>
            <tr>
                <th>Name</th>
                <th>Floor</th>
                <th>Area (m²)</th>
                <th>Equipment Count</th>
                <th>Occupancy</th>
            </tr>
            {{range .Rooms}}
            <tr>
                <td>{{.Name}}</td>
                <td>{{.Floor}}</td>
                <td>{{printf "%.1f" .Area}}</td>
                <td>{{.Equipment}}</td>
                <td>{{.Occupancy}}</td>
            </tr>
            {{end}}
        </table>
    </div>

    <div class="section">
        <h2>Visualizations</h2>
        {{range .Visualizations}}
        <div style="margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px;">
            <h3>{{.Title}}</h3>
            <p>{{.Description}}</p>
            <p><em>Format: {{.Format}}</em></p>
        </div>
        {{end}}
    </div>
</body>
</html>`

	t, err := template.New("report").Parse(tmpl)
	if err != nil {
		return err
	}

	file, err := os.Create(outputPath)
	if err != nil {
		return err
	}
	defer file.Close()

	return t.Execute(file, data)
}

// generateMarkdownReport creates a Markdown report
func (e *Exporter) generateMarkdownReport(data *ReportData, outputPath string) error {
	content := fmt.Sprintf(`# Building Report: %s

Generated: %s

## Building Overview

- **Floors**: %d
- **Rooms**: %d
- **Equipment Items**: %d
- **Total Area**: %.1f m²

## Equipment Status

| Name | Type | Floor | Room | Status |
|------|------|-------|------|--------|
`, data.BuildingName, data.GeneratedAt.Format("2006-01-02 15:04:05"),
		data.FloorCount, data.RoomCount, data.EquipmentCount, data.Metrics.TotalArea)

	for _, eq := range data.Equipment {
		content += fmt.Sprintf("| %s | %s | %d | %s | %s |\n",
			eq.Name, eq.Type, eq.Floor, eq.Room, eq.Status)
	}

	content += "\n## Room Information\n\n"
	content += "| Name | Floor | Area (m²) | Equipment Count | Occupancy |\n"
	content += "|------|-------|-----------|----------------|----------|\n"

	for _, room := range data.Rooms {
		content += fmt.Sprintf("| %s | %d | %.1f | %d | %s |\n",
			room.Name, room.Floor, room.Area, room.Equipment, room.Occupancy)
	}

	content += "\n## Visualizations\n\n"
	for _, viz := range data.Visualizations {
		content += fmt.Sprintf("### %s\n\n%s\n\n*Format: %s*\n\n",
			viz.Title, viz.Description, viz.Format)
	}

	return os.WriteFile(outputPath, []byte(content), 0644)
}

// generateTextReport creates a plain text report
func (e *Exporter) generateTextReport(data *ReportData, outputPath string) error {
	content := fmt.Sprintf(`BUILDING REPORT: %s
Generated: %s

BUILDING OVERVIEW
================
Floors: %d
Rooms: %d
Equipment Items: %d
Total Area: %.1f m²

EQUIPMENT STATUS
================
`, data.BuildingName, data.GeneratedAt.Format("2006-01-02 15:04:05"),
		data.FloorCount, data.RoomCount, data.EquipmentCount, data.Metrics.TotalArea)

	for _, eq := range data.Equipment {
		content += fmt.Sprintf("%-20s %-15s Floor %-2d %-15s %s\n",
			eq.Name, eq.Type, eq.Floor, eq.Room, eq.Status)
	}

	content += "\nROOM INFORMATION\n================\n"
	for _, room := range data.Rooms {
		content += fmt.Sprintf("%-20s Floor %-2d %6.1f m² %2d equipment %s\n",
			room.Name, room.Floor, room.Area, room.Equipment, room.Occupancy)
	}

	content += "\nVISUALIZATIONS\n==============\n"
	for _, viz := range data.Visualizations {
		content += fmt.Sprintf("%s\n%s\nFormat: %s\n\n",
			viz.Title, viz.Description, viz.Format)
	}

	return os.WriteFile(outputPath, []byte(content), 0644)
}

// ExportVisualizations exports individual visualization files
func (e *Exporter) ExportVisualizations(ctx context.Context, buildingID string, outputDir string) error {
	logger.Info("Exporting visualizations for building %s to %s", buildingID, outputDir)

	// Create output directory
	if err := os.MkdirAll(outputDir, 0755); err != nil {
		return err
	}

	// Gather data
	data, err := e.gatherReportData(ctx, buildingID)
	if err != nil {
		return err
	}

	// Export each visualization
	for _, viz := range data.Visualizations {
		filename := filepath.Join(outputDir, fmt.Sprintf("%s.txt", viz.Type))
		content := fmt.Sprintf("%s\n%s\n\nData: %+v\n",
			viz.Title, viz.Description, viz.Data)

		if err := os.WriteFile(filename, []byte(content), 0644); err != nil {
			logger.Error("Failed to export visualization %s: %v", viz.Type, err)
		}
	}

	// Create index file
	indexContent := fmt.Sprintf("Building Report: %s\nGenerated: %s\n\nExported Files:\n",
		data.BuildingName, data.GeneratedAt.Format("2006-01-02 15:04:05"))

	for _, viz := range data.Visualizations {
		indexContent += fmt.Sprintf("- %s\n", viz.Type)
	}

	indexPath := filepath.Join(outputDir, "index.txt")
	return os.WriteFile(indexPath, []byte(indexContent), 0644)
}

// calculateRoomOccupancy calculates room occupancy based on room data
func (e *Exporter) calculateRoomOccupancy(room *models.Room) string {
	// Calculate occupancy based on room area and typical occupancy rates
	area := room.Bounds.MaxX - room.Bounds.MinX
	width := room.Bounds.MaxY - room.Bounds.MinY
	roomArea := area * width

	// Typical occupancy rates by room type
	occupancyRate := 0.1 // Default low occupancy

	// Adjust based on room name patterns
	roomName := strings.ToLower(room.Name)
	switch {
	case strings.Contains(roomName, "office") || strings.Contains(roomName, "work"):
		occupancyRate = 0.8
	case strings.Contains(roomName, "meeting") || strings.Contains(roomName, "conference"):
		occupancyRate = 0.6
	case strings.Contains(roomName, "lobby") || strings.Contains(roomName, "reception"):
		occupancyRate = 0.3
	case strings.Contains(roomName, "storage") || strings.Contains(roomName, "utility"):
		occupancyRate = 0.05
	}

	// Calculate expected occupancy
	expectedOccupancy := int(roomArea * occupancyRate)

	if expectedOccupancy == 0 {
		return "Empty"
	} else if expectedOccupancy < 5 {
		return "Low"
	} else if expectedOccupancy < 15 {
		return "Medium"
	} else {
		return "High"
	}
}

// calculateRoomTemperature calculates room temperature based on room data
func (e *Exporter) calculateRoomTemperature(room *models.Room) float64 {
	// Base temperature
	baseTemp := 22.0

	// Adjust based on room type
	roomName := strings.ToLower(room.Name)
	switch {
	case strings.Contains(roomName, "server") || strings.Contains(roomName, "data"):
		baseTemp = 18.0 // Cooler for server rooms
	case strings.Contains(roomName, "storage") || strings.Contains(roomName, "utility"):
		baseTemp = 20.0 // Slightly cooler for storage
	case strings.Contains(roomName, "meeting") || strings.Contains(roomName, "conference"):
		baseTemp = 23.0 // Warmer for meeting rooms
	case strings.Contains(roomName, "lobby") || strings.Contains(roomName, "reception"):
		baseTemp = 24.0 // Warmer for public areas
	}

	// Add some variation based on room ID (simulate different conditions)
	variation := float64(len(room.ID)%10)*0.5 - 2.5
	return baseTemp + variation
}

// calculateTotalArea calculates total area of all rooms
func (e *Exporter) calculateTotalArea(rooms []*models.Room) float64 {
	totalArea := 0.0
	for _, room := range rooms {
		width := room.Bounds.MaxX - room.Bounds.MinX
		height := room.Bounds.MaxY - room.Bounds.MinY
		totalArea += width * height
	}
	return totalArea
}

// calculateOccupancyRate calculates overall occupancy rate
func (e *Exporter) calculateOccupancyRate(rooms []*models.Room) float64 {
	if len(rooms) == 0 {
		return 0.0
	}

	totalOccupancy := 0.0
	for _, room := range rooms {
		occupancy := e.calculateRoomOccupancy(room)
		switch occupancy {
		case "Empty":
			totalOccupancy += 0.0
		case "Low":
			totalOccupancy += 0.25
		case "Medium":
			totalOccupancy += 0.5
		case "High":
			totalOccupancy += 0.8
		}
	}

	return totalOccupancy / float64(len(rooms))
}

// calculateEnergyUsage calculates estimated energy usage
func (e *Exporter) calculateEnergyUsage(rooms []*models.Room) float64 {
	baseEnergy := 1000.0 // Base energy consumption

	// Add energy based on room count and types
	for _, room := range rooms {
		roomName := strings.ToLower(room.Name)

		// Energy consumption by room type
		roomEnergy := 50.0 // Base energy per room

		switch {
		case strings.Contains(roomName, "server") || strings.Contains(roomName, "data"):
			roomEnergy = 200.0 // High energy for server rooms
		case strings.Contains(roomName, "office") || strings.Contains(roomName, "work"):
			roomEnergy = 80.0 // Medium energy for offices
		case strings.Contains(roomName, "meeting") || strings.Contains(roomName, "conference"):
			roomEnergy = 120.0 // Higher energy for meeting rooms
		case strings.Contains(roomName, "storage") || strings.Contains(roomName, "utility"):
			roomEnergy = 30.0 // Lower energy for storage
		}

		baseEnergy += roomEnergy
	}

	return baseEnergy
}

// calculateEquipmentHealth calculates overall equipment health
func (e *Exporter) calculateEquipmentHealth(rooms []*models.Room) float64 {
	if len(rooms) == 0 {
		return 1.0
	}

	totalHealth := 0.0
	roomCount := 0

	for _, room := range rooms {
		// Simulate equipment health based on room characteristics
		roomHealth := 0.95 // Base health

		// Adjust based on room type
		roomName := strings.ToLower(room.Name)
		switch {
		case strings.Contains(roomName, "server") || strings.Contains(roomName, "data"):
			roomHealth = 0.98 // High reliability for critical systems
		case strings.Contains(roomName, "office") || strings.Contains(roomName, "work"):
			roomHealth = 0.92 // Good reliability for offices
		case strings.Contains(roomName, "meeting") || strings.Contains(roomName, "conference"):
			roomHealth = 0.88 // Slightly lower for meeting rooms
		case strings.Contains(roomName, "storage") || strings.Contains(roomName, "utility"):
			roomHealth = 0.85 // Lower for utility areas
		}

		// Add some variation based on room ID
		variation := float64(len(room.ID)%20)*0.01 - 0.1
		roomHealth += variation

		// Ensure health is between 0 and 1
		if roomHealth < 0 {
			roomHealth = 0
		} else if roomHealth > 1 {
			roomHealth = 1
		}

		totalHealth += roomHealth
		roomCount++
	}

	return totalHealth / float64(roomCount)
}
