package exporter

import (
	"encoding/csv"
	"fmt"
	"io"
	"sort"
	"strconv"
	"time"

	"github.com/arx-os/arxos/pkg/models"
)

// CSVExporter exports data to CSV format
type CSVExporter struct {
	IncludeHeaders bool
	Delimiter      rune
}

// NewCSVExporter creates a new CSV exporter
func NewCSVExporter() *CSVExporter {
	return &CSVExporter{
		IncludeHeaders: true,
		Delimiter:      ',',
	}
}

// ExportEquipment exports equipment list to CSV
func (e *CSVExporter) ExportEquipment(equipment []*models.Equipment, w io.Writer) error {
	writer := csv.NewWriter(w)
	writer.Comma = e.Delimiter
	defer writer.Flush()

	// Write headers if enabled
	if e.IncludeHeaders {
		headers := []string{
			"ID",
			"Name",
			"Type",
			"Status",
			"Room ID",
			"Path",
			"Model",
			"Serial",
			"Installed",
			"Maintained",
			"Notes",
			"X (mm)",
			"Y (mm)",
			"Z (mm)",
		}
		if err := writer.Write(headers); err != nil {
			return fmt.Errorf("failed to write headers: %w", err)
		}
	}

	// Sort equipment by ID
	sort.Slice(equipment, func(i, j int) bool {
		return equipment[i].ID < equipment[j].ID
	})

	// Write equipment data
	for _, eq := range equipment {
		// Get spatial coordinates
		xStr, yStr, zStr := "", "", ""
		if eq.Location != nil {
			xStr = fmt.Sprintf("%.3f", eq.Location.X)
			yStr = fmt.Sprintf("%.3f", eq.Location.Y)
		}
		// Check for Z in metadata
		if eq.Metadata != nil {
			if z, ok := eq.Metadata["location_z"]; ok {
				zStr = fmt.Sprintf("%.3f", z)
			}
		}

		record := []string{
			eq.ID,
			eq.Name,
			eq.Type,
			eq.Status,
			eq.RoomID,
			eq.Path,
			eq.Model,
			eq.Serial,
			formatTime(eq.Installed),
			formatTime(eq.Maintained),
			eq.Notes,
			xStr,
			yStr,
			zStr,
		}
		if err := writer.Write(record); err != nil {
			return fmt.Errorf("failed to write equipment %s: %w", eq.ID, err)
		}
	}

	return nil
}

// ExportFloorPlans exports floor plans to CSV
func (e *CSVExporter) ExportFloorPlans(plans []*models.FloorPlan, w io.Writer) error {
	writer := csv.NewWriter(w)
	writer.Comma = e.Delimiter
	defer writer.Flush()

	// Write headers if enabled
	if e.IncludeHeaders {
		headers := []string{
			"Building",
			"Floor Level",
			"Floor Name",
			"Room ID",
			"Room Name",
			"Equipment Count",
			"Room Area",
		}
		if err := writer.Write(headers); err != nil {
			return fmt.Errorf("failed to write headers: %w", err)
		}
	}

	// Write floor plan data
	for _, plan := range plans {
		for _, room := range plan.Rooms {
			// Count equipment in room
			equipmentCount := len(room.Equipment)

			record := []string{
				plan.Building,
				strconv.Itoa(plan.Level),
				plan.Name,
				room.ID,
				room.Name,
				strconv.Itoa(equipmentCount),
				fmt.Sprintf("%.2f", calculateRoomArea(room)),
			}
			if err := writer.Write(record); err != nil {
				return fmt.Errorf("failed to write room %s: %w", room.ID, err)
			}
		}
	}

	return nil
}

// ExportMaintenanceSchedule exports maintenance schedule to CSV
func (e *CSVExporter) ExportMaintenanceSchedule(equipment []*models.Equipment, w io.Writer) error {
	writer := csv.NewWriter(w)
	writer.Comma = e.Delimiter
	defer writer.Flush()

	// Write headers if enabled
	if e.IncludeHeaders {
		headers := []string{
			"Equipment ID",
			"Name",
			"Type",
			"Last Maintained",
			"Days Since Maintenance",
			"Status",
			"Priority",
			"Notes",
		}
		if err := writer.Write(headers); err != nil {
			return fmt.Errorf("failed to write headers: %w", err)
		}
	}

	// Filter and sort equipment needing maintenance
	var maintenanceItems []*maintenanceItem
	for _, eq := range equipment {
		item := createMaintenanceItem(eq)
		if item.Priority != "None" {
			maintenanceItems = append(maintenanceItems, item)
		}
	}

	// Sort by priority and days since maintenance
	sort.Slice(maintenanceItems, func(i, j int) bool {
		if maintenanceItems[i].Priority != maintenanceItems[j].Priority {
			return getPriorityValue(maintenanceItems[i].Priority) > getPriorityValue(maintenanceItems[j].Priority)
		}
		return maintenanceItems[i].DaysSince > maintenanceItems[j].DaysSince
	})

	// Write maintenance items
	for _, item := range maintenanceItems {
		record := []string{
			item.Equipment.ID,
			item.Equipment.Name,
			item.Equipment.Type,
			formatTime(item.Equipment.Maintained),
			strconv.Itoa(item.DaysSince),
			item.Equipment.Status,
			item.Priority,
			item.Equipment.Notes,
		}
		if err := writer.Write(record); err != nil {
			return fmt.Errorf("failed to write maintenance item: %w", err)
		}
	}

	return nil
}

// ExportSummary exports a building summary to CSV
func (e *CSVExporter) ExportSummary(plans []*models.FloorPlan, w io.Writer) error {
	writer := csv.NewWriter(w)
	writer.Comma = e.Delimiter
	defer writer.Flush()

	// Calculate summary statistics
	totalRooms := 0
	totalEquipment := 0
	statusCounts := make(map[string]int)
	typeCounts := make(map[string]int)

	for _, plan := range plans {
		totalRooms += len(plan.Rooms)
		totalEquipment += len(plan.Equipment)

		for _, eq := range plan.Equipment {
			statusCounts[eq.Status]++
			typeCounts[eq.Type]++
		}
	}

	// Write summary data
	if e.IncludeHeaders {
		if err := writer.Write([]string{"Metric", "Value"}); err != nil {
			return err
		}
	}

	summaryData := [][]string{
		{"Building", plans[0].Building},
		{"Total Floors", strconv.Itoa(len(plans))},
		{"Total Rooms", strconv.Itoa(totalRooms)},
		{"Total Equipment", strconv.Itoa(totalEquipment)},
	}

	// Add status breakdown
	for status, count := range statusCounts {
		if status == "" {
			status = "Unknown"
		}
		summaryData = append(summaryData, []string{
			fmt.Sprintf("Equipment %s", status),
			strconv.Itoa(count),
		})
	}

	// Add type breakdown
	for equipType, count := range typeCounts {
		if equipType == "" {
			equipType = "Unspecified"
		}
		summaryData = append(summaryData, []string{
			fmt.Sprintf("Type: %s", equipType),
			strconv.Itoa(count),
		})
	}

	for _, row := range summaryData {
		if err := writer.Write(row); err != nil {
			return err
		}
	}

	return nil
}

// Helper types and functions

type maintenanceItem struct {
	Equipment *models.Equipment
	DaysSince int
	Priority  string
}

func createMaintenanceItem(eq *models.Equipment) *maintenanceItem {
	item := &maintenanceItem{
		Equipment: eq,
		DaysSince: -1,
		Priority:  "None",
	}

	// Calculate days since maintenance
	if eq.Maintained != nil {
		item.DaysSince = int(time.Since(*eq.Maintained).Hours() / 24)
	}

	// Determine priority based on status and days
	if eq.Status == models.StatusFailed {
		item.Priority = "Critical"
	} else if eq.Status == models.StatusDegraded {
		item.Priority = "High"
	} else if eq.Status == models.StatusMaintenance {
		item.Priority = "Scheduled"
	} else if item.DaysSince > 365 {
		item.Priority = "High"
	} else if item.DaysSince > 180 {
		item.Priority = "Medium"
	} else if item.DaysSince > 90 {
		item.Priority = "Low"
	}

	return item
}

func getPriorityValue(priority string) int {
	switch priority {
	case "Critical":
		return 4
	case "High":
		return 3
	case "Medium":
		return 2
	case "Low":
		return 1
	default:
		return 0
	}
}

func calculateRoomArea(room *models.Room) float64 {
	if room.Bounds.MaxX == 0 && room.Bounds.MaxY == 0 {
		return 0
	}
	return room.Bounds.Width() * room.Bounds.Height()
}

func formatTime(t *time.Time) string {
	if t == nil {
		return ""
	}
	return t.Format("2006-01-02")
}