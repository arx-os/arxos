package exporter

import (
	"encoding/json"
	"fmt"
	"io"
	"time"

	"github.com/arx-os/arxos/pkg/models"
)

// JSONExporter exports data to JSON format
type JSONExporter struct {
	PrettyPrint bool
	IncludeMeta bool
}

// NewJSONExporter creates a new JSON exporter
func NewJSONExporter() *JSONExporter {
	return &JSONExporter{
		PrettyPrint: true,
		IncludeMeta: true,
	}
}

// ExportBuilding exports complete building data to JSON
func (e *JSONExporter) ExportBuilding(plans []*models.FloorPlan, w io.Writer) error {
	if len(plans) == 0 {
		return fmt.Errorf("no floor plans provided")
	}

	// Create building structure
	building := BuildingJSON{
		UUID:        plans[0].UUID,
		Name:        plans[0].Building,
		Description: plans[0].Description,
		Metadata:    make(map[string]interface{}),
		Floors:      make([]FloorJSON, 0, len(plans)),
		Statistics:  e.calculateStatistics(plans),
	}

	// Add metadata if enabled
	if e.IncludeMeta {
		building.Metadata["exported_at"] = time.Now().Format(time.RFC3339)
		building.Metadata["version"] = "1.0.0"
		building.Metadata["format"] = "ArxOS JSON"
	}

	// Convert floor plans
	for _, plan := range plans {
		floor := e.convertFloor(plan)
		building.Floors = append(building.Floors, floor)
	}

	// Encode to JSON
	encoder := json.NewEncoder(w)
	if e.PrettyPrint {
		encoder.SetIndent("", "  ")
	}

	return encoder.Encode(building)
}

// ExportEquipmentList exports equipment list to JSON
func (e *JSONExporter) ExportEquipmentList(equipment []*models.Equipment, w io.Writer) error {
	// Create equipment list structure
	list := EquipmentListJSON{
		Equipment:  make([]EquipmentJSON, 0, len(equipment)),
		TotalCount: len(equipment),
		ExportedAt: time.Now().Format(time.RFC3339),
	}

	// Count by status and type
	statusCounts := make(map[string]int)
	typeCounts := make(map[string]int)

	for _, eq := range equipment {
		// Convert equipment
		eqJSON := e.convertEquipment(eq)
		list.Equipment = append(list.Equipment, eqJSON)

		// Update counts
		statusCounts[eq.Status]++
		typeCounts[eq.Type]++
	}

	list.StatusBreakdown = statusCounts
	list.TypeBreakdown = typeCounts

	// Encode to JSON
	encoder := json.NewEncoder(w)
	if e.PrettyPrint {
		encoder.SetIndent("", "  ")
	}

	return encoder.Encode(list)
}

// ExportSpatialData exports spatial query results to JSON
func (e *JSONExporter) ExportSpatialData(results interface{}, w io.Writer) error {
	// Generic spatial data export
	data := SpatialDataJSON{
		Type:       "FeatureCollection",
		Features:   []interface{}{},
		Properties: make(map[string]interface{}),
	}

	// Add metadata
	if e.IncludeMeta {
		data.Properties["generated_at"] = time.Now().Format(time.RFC3339)
		data.Properties["coordinate_system"] = "WGS84"
	}

	// TODO: Convert spatial results to GeoJSON features
	// This would handle PostGIS query results

	// Encode to JSON
	encoder := json.NewEncoder(w)
	if e.PrettyPrint {
		encoder.SetIndent("", "  ")
	}

	return encoder.Encode(data)
}

// ExportAPIResponse exports data in API response format
func (e *JSONExporter) ExportAPIResponse(data interface{}, success bool, message string, w io.Writer) error {
	response := APIResponse{
		Success:   success,
		Message:   message,
		Data:      data,
		Timestamp: time.Now().Format(time.RFC3339),
	}

	encoder := json.NewEncoder(w)
	if e.PrettyPrint {
		encoder.SetIndent("", "  ")
	}

	return encoder.Encode(response)
}

// Helper functions

func (e *JSONExporter) convertFloor(plan *models.FloorPlan) FloorJSON {
	floor := FloorJSON{
		Level:       plan.Level,
		Name:        plan.Name,
		Description: plan.Description,
		Rooms:       make([]RoomJSON, 0, len(plan.Rooms)),
		Equipment:   make([]EquipmentJSON, 0, len(plan.Equipment)),
	}

	// Convert rooms
	for _, room := range plan.Rooms {
		roomJSON := RoomJSON{
			ID:   room.ID,
			Name: room.Name,
			Bounds: BoundsJSON{
				MinX: room.Bounds.MinX,
				MinY: room.Bounds.MinY,
				MaxX: room.Bounds.MaxX,
				MaxY: room.Bounds.MaxY,
			},
			EquipmentIDs: room.Equipment,
		}
		floor.Rooms = append(floor.Rooms, roomJSON)
	}

	// Convert equipment
	for _, eq := range plan.Equipment {
		eqJSON := e.convertEquipment(eq)
		floor.Equipment = append(floor.Equipment, eqJSON)
	}

	return floor
}

func (e *JSONExporter) convertEquipment(eq *models.Equipment) EquipmentJSON {
	eqJSON := EquipmentJSON{
		ID:     eq.ID,
		Name:   eq.Name,
		Type:   eq.Type,
		Status: eq.Status,
		RoomID: eq.RoomID,
		Path:   eq.Path,
		Model:  eq.Model,
		Serial: eq.Serial,
		Notes:  eq.Notes,
	}

	// Add location if available
	if eq.Location != nil {
		eqJSON.Location = &LocationJSON{
			X: eq.Location.X,
			Y: eq.Location.Y,
		}
	}

	// Add timestamps if available
	if eq.Installed != nil {
		eqJSON.InstalledDate = eq.Installed.Format("2006-01-02")
	}
	if eq.Maintained != nil {
		eqJSON.MaintenanceDate = eq.Maintained.Format("2006-01-02")
	}

	// Add metadata if enabled
	if e.IncludeMeta && eq.Metadata != nil {
		eqJSON.Metadata = eq.Metadata
	}

	return eqJSON
}

func (e *JSONExporter) calculateStatistics(plans []*models.FloorPlan) StatisticsJSON {
	stats := StatisticsJSON{
		FloorCount:     len(plans),
		StatusCounts:   make(map[string]int),
		TypeCounts:     make(map[string]int),
		FloorBreakdown: make([]FloorStatsJSON, 0, len(plans)),
	}

	for _, plan := range plans {
		stats.TotalRooms += len(plan.Rooms)
		stats.TotalEquipment += len(plan.Equipment)

		// Floor statistics
		floorStats := FloorStatsJSON{
			Level:          plan.Level,
			Name:           plan.Name,
			RoomCount:      len(plan.Rooms),
			EquipmentCount: len(plan.Equipment),
		}
		stats.FloorBreakdown = append(stats.FloorBreakdown, floorStats)

		// Count equipment by status and type
		for _, eq := range plan.Equipment {
			stats.StatusCounts[eq.Status]++
			stats.TypeCounts[eq.Type]++
		}
	}

	return stats
}

// JSON structure definitions

type BuildingJSON struct {
	UUID        string                 `json:"uuid,omitempty"`
	Name        string                 `json:"name"`
	Description string                 `json:"description,omitempty"`
	Metadata    map[string]interface{} `json:"metadata,omitempty"`
	Floors      []FloorJSON            `json:"floors"`
	Statistics  StatisticsJSON         `json:"statistics"`
}

type FloorJSON struct {
	Level       int             `json:"level"`
	Name        string          `json:"name"`
	Description string          `json:"description,omitempty"`
	Rooms       []RoomJSON      `json:"rooms"`
	Equipment   []EquipmentJSON `json:"equipment"`
}

type RoomJSON struct {
	ID           string     `json:"id"`
	Name         string     `json:"name"`
	Bounds       BoundsJSON `json:"bounds,omitempty"`
	EquipmentIDs []string   `json:"equipment_ids,omitempty"`
}

type EquipmentJSON struct {
	ID              string                 `json:"id"`
	Name            string                 `json:"name"`
	Type            string                 `json:"type"`
	Status          string                 `json:"status"`
	RoomID          string                 `json:"room_id,omitempty"`
	Path            string                 `json:"path,omitempty"`
	Location        *LocationJSON          `json:"location,omitempty"`
	Model           string                 `json:"model,omitempty"`
	Serial          string                 `json:"serial,omitempty"`
	InstalledDate   string                 `json:"installed_date,omitempty"`
	MaintenanceDate string                 `json:"maintenance_date,omitempty"`
	Notes           string                 `json:"notes,omitempty"`
	Metadata        map[string]interface{} `json:"metadata,omitempty"`
}

type LocationJSON struct {
	X float64 `json:"x"`
	Y float64 `json:"y"`
}

type BoundsJSON struct {
	MinX float64 `json:"min_x"`
	MinY float64 `json:"min_y"`
	MaxX float64 `json:"max_x"`
	MaxY float64 `json:"max_y"`
}

type EquipmentListJSON struct {
	Equipment       []EquipmentJSON   `json:"equipment"`
	TotalCount      int               `json:"total_count"`
	StatusBreakdown map[string]int    `json:"status_breakdown"`
	TypeBreakdown   map[string]int    `json:"type_breakdown"`
	ExportedAt      string            `json:"exported_at"`
}

type StatisticsJSON struct {
	FloorCount     int                `json:"floor_count"`
	TotalRooms     int                `json:"total_rooms"`
	TotalEquipment int                `json:"total_equipment"`
	StatusCounts   map[string]int     `json:"status_counts"`
	TypeCounts     map[string]int     `json:"type_counts"`
	FloorBreakdown []FloorStatsJSON   `json:"floor_breakdown"`
}

type FloorStatsJSON struct {
	Level          int    `json:"level"`
	Name           string `json:"name"`
	RoomCount      int    `json:"room_count"`
	EquipmentCount int    `json:"equipment_count"`
}

type SpatialDataJSON struct {
	Type       string                 `json:"type"`
	Features   []interface{}          `json:"features"`
	Properties map[string]interface{} `json:"properties,omitempty"`
}

type APIResponse struct {
	Success   bool        `json:"success"`
	Message   string      `json:"message,omitempty"`
	Data      interface{} `json:"data,omitempty"`
	Timestamp string      `json:"timestamp"`
}