package exporter_test

import (
	"bytes"
	"encoding/csv"
	"encoding/json"
	"strings"
	"testing"
	"time"

	"github.com/arx-os/arxos/internal/exporter"
	"github.com/arx-os/arxos/pkg/models"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

// TestIntegrationExportPipeline tests the complete export pipeline
func TestIntegrationExportPipeline(t *testing.T) {
	// Create test data
	floorPlans := createTestFloorPlans()

	t.Run("BIM Text Generation", func(t *testing.T) {
		generator := exporter.NewBIMGenerator()
		var buf bytes.Buffer
		err := generator.GenerateFromFloorPlans(floorPlans, &buf)
		require.NoError(t, err)

		output := buf.String()
		assert.Contains(t, output, "BUILDING: TEST-001 Test Building")
		assert.Contains(t, output, "FLOOR: 1 Ground Floor")
		assert.Contains(t, output, "ROOM: 101 Main Room")
		assert.Contains(t, output, "EQUIPMENT: EQ-001")
		assert.Contains(t, output, "[hvac]")
		assert.Contains(t, output, "AC Unit")
	})

	t.Run("CSV Equipment Export", func(t *testing.T) {
		exporter := exporter.NewCSVExporter()
		var buf bytes.Buffer

		// Collect all equipment
		var equipment []*models.Equipment
		for _, plan := range floorPlans {
			equipment = append(equipment, plan.Equipment...)
		}

		err := exporter.ExportEquipment(equipment, &buf)
		require.NoError(t, err)

		// Parse CSV output
		reader := csv.NewReader(&buf)
		records, err := reader.ReadAll()
		require.NoError(t, err)

		// Verify headers
		assert.Equal(t, "ID", records[0][0])
		assert.Equal(t, "Name", records[0][1])
		assert.Equal(t, "Type", records[0][2])
		assert.Equal(t, "Status", records[0][3])

		// Verify data
		assert.Equal(t, "EQ-001", records[1][0])
		assert.Equal(t, "AC Unit", records[1][1])
		assert.Equal(t, "HVAC", records[1][2])
		assert.Equal(t, "OPERATIONAL", records[1][3])
	})

	t.Run("JSON Building Export", func(t *testing.T) {
		exporter := exporter.NewJSONExporter()
		var buf bytes.Buffer
		err := exporter.ExportBuilding(floorPlans, &buf)
		require.NoError(t, err)

		var building map[string]interface{}
		err = json.Unmarshal(buf.Bytes(), &building)
		require.NoError(t, err)

		assert.Equal(t, "TEST-001", building["uuid"])
		assert.Equal(t, "Test Building", building["name"])

		floors := building["floors"].([]interface{})
		assert.Len(t, floors, 2)

		floor1 := floors[0].(map[string]interface{})
		assert.Equal(t, float64(1), floor1["level"])
		assert.Equal(t, "Ground Floor", floor1["name"])

		rooms := floor1["rooms"].([]interface{})
		assert.Len(t, rooms, 1)
	})

	t.Run("Maintenance Schedule Export", func(t *testing.T) {
		exporter := exporter.NewCSVExporter()
		var buf bytes.Buffer

		// Create equipment with maintenance dates
		old := time.Now().AddDate(0, -7, 0) // 7 months ago
		equipment := []*models.Equipment{
			{
				ID:         "EQ-M001",
				Name:       "Old AC Unit",
				Type:       "HVAC",
				Status:     "DEGRADED",
				Maintained: &old,
			},
		}

		err := exporter.ExportMaintenanceSchedule(equipment, &buf)
		require.NoError(t, err)

		reader := csv.NewReader(&buf)
		records, err := reader.ReadAll()
		require.NoError(t, err)

		// Should have header and one equipment needing maintenance
		assert.Len(t, records, 2)
		assert.Equal(t, "Equipment ID", records[0][0])
		assert.Equal(t, "EQ-M001", records[1][0])
		assert.Equal(t, "Old AC Unit", records[1][1])
		assert.Equal(t, "High", records[1][6]) // Priority
	})

	t.Run("Building Summary Export", func(t *testing.T) {
		exporter := exporter.NewCSVExporter()
		var buf bytes.Buffer
		err := exporter.ExportSummary(floorPlans, &buf)
		require.NoError(t, err)

		output := buf.String()
		assert.Contains(t, output, "Test Building")
		assert.Contains(t, output, "Total Floors,2")
		assert.Contains(t, output, "Total Rooms,2")
		assert.Contains(t, output, "Total Equipment,4")
	})
}

// TestBIMGeneratorOptions tests different generator options
func TestBIMGeneratorOptions(t *testing.T) {
	floorPlans := createTestFloorPlans()

	t.Run("Without Metadata", func(t *testing.T) {
		generator := exporter.NewBIMGenerator()
		generator.IncludeMetadata = false

		var buf bytes.Buffer
		err := generator.GenerateFromFloorPlans(floorPlans, &buf)
		require.NoError(t, err)

		output := buf.String()
		assert.NotContains(t, output, "# Serial:")
		assert.NotContains(t, output, "# Installed:")
	})

	t.Run("Without Status", func(t *testing.T) {
		generator := exporter.NewBIMGenerator()
		generator.IncludeStatus = false

		var buf bytes.Buffer
		err := generator.GenerateFromFloorPlans(floorPlans, &buf)
		require.NoError(t, err)

		output := buf.String()
		assert.NotContains(t, output, "<maintenance>")
	})
}

// TestJSONExporterOptions tests JSON exporter options
func TestJSONExporterOptions(t *testing.T) {
	floorPlans := createTestFloorPlans()

	t.Run("Without Pretty Print", func(t *testing.T) {
		exporter := exporter.NewJSONExporter()
		exporter.PrettyPrint = false

		var buf bytes.Buffer
		err := exporter.ExportBuilding(floorPlans, &buf)
		require.NoError(t, err)

		output := buf.String()
		// Non-pretty printed JSON should be on one line
		assert.Equal(t, 1, strings.Count(output, "\n"))
	})

	t.Run("Without Metadata", func(t *testing.T) {
		exporter := exporter.NewJSONExporter()
		exporter.IncludeMeta = false

		var buf bytes.Buffer
		err := exporter.ExportBuilding(floorPlans, &buf)
		require.NoError(t, err)

		var building map[string]interface{}
		err = json.Unmarshal(buf.Bytes(), &building)
		require.NoError(t, err)

		metadata, ok := building["metadata"].(map[string]interface{})
		if ok {
			assert.Len(t, metadata, 0)
		} else {
			// metadata field should not exist or be empty
			assert.Nil(t, building["metadata"])
		}
	})
}

// TestCSVExporterDelimiter tests custom delimiter
func TestCSVExporterDelimiter(t *testing.T) {
	exporter := exporter.NewCSVExporter()
	exporter.Delimiter = ';'

	var buf bytes.Buffer
	equipment := []*models.Equipment{
		{
			ID:   "EQ-001",
			Name: "Test Equipment",
			Type: "TEST",
		},
	}

	err := exporter.ExportEquipment(equipment, &buf)
	require.NoError(t, err)

	output := buf.String()
	assert.Contains(t, output, "ID;Name;Type")
	assert.Contains(t, output, "EQ-001;Test Equipment;TEST")
}

// TestExportErrorHandling tests error scenarios
func TestExportErrorHandling(t *testing.T) {
	t.Run("Empty Floor Plans", func(t *testing.T) {
		generator := exporter.NewBIMGenerator()
		var buf bytes.Buffer
		err := generator.GenerateFromFloorPlans([]*models.FloorPlan{}, &buf)
		assert.Error(t, err)
		assert.Contains(t, err.Error(), "no floor plans provided")
	})

	t.Run("API Response Export", func(t *testing.T) {
		exporter := exporter.NewJSONExporter()
		var buf bytes.Buffer

		testData := map[string]string{"test": "data"}
		err := exporter.ExportAPIResponse(testData, true, "Success", &buf)
		require.NoError(t, err)

		var response map[string]interface{}
		err = json.Unmarshal(buf.Bytes(), &response)
		require.NoError(t, err)

		assert.Equal(t, true, response["success"])
		assert.Equal(t, "Success", response["message"])
		assert.NotNil(t, response["data"])
		assert.NotEmpty(t, response["timestamp"])
	})
}

// Helper function to create test floor plans
func createTestFloorPlans() []*models.FloorPlan {
	installDate := time.Now().AddDate(-1, 0, 0)
	maintDate := time.Now().AddDate(0, -3, 0)

	return []*models.FloorPlan{
		{
			UUID:        "TEST-001",
			Building:    "Test Building",
			Description: "Test building for integration tests",
			Level:       1,
			Name:        "Ground Floor",
			Rooms: []*models.Room{
				{
					ID:   "101",
					Name: "Main Room",
					Bounds: models.Bounds{
						MinX: 0,
						MinY: 0,
						MaxX: 10,
						MaxY: 10,
					},
					Equipment: []string{"EQ-001", "EQ-002"},
				},
			},
			Equipment: []*models.Equipment{
				{
					ID:         "EQ-001",
					Name:       "AC Unit",
					Type:       "HVAC",
					Status:     "OPERATIONAL",
					RoomID:     "101",
					Path:       "1/A/101/E/AC_001",
					Model:      "AC-5000",
					Serial:     "SN12345",
					Installed:  &installDate,
					Maintained: &maintDate,
					Notes:      "Regular maintenance required",
					Location:   &models.Point{X: 5.0, Y: 5.0},
				},
				{
					ID:     "EQ-002",
					Name:   "Light Fixture",
					Type:   "LIGHTING",
					Status: "OPERATIONAL",
					RoomID: "101",
				},
			},
		},
		{
			UUID:     "TEST-001",
			Building: "Test Building",
			Level:    2,
			Name:     "Second Floor",
			Rooms: []*models.Room{
				{
					ID:   "201",
					Name: "Office",
					Bounds: models.Bounds{
						MinX: 0,
						MinY: 0,
						MaxX: 8,
						MaxY: 8,
					},
					Equipment: []string{"EQ-003"},
				},
			},
			Equipment: []*models.Equipment{
				{
					ID:     "EQ-003",
					Name:   "Outlet",
					Type:   "ELECTRICAL",
					Status: "OPERATIONAL",
					RoomID: "201",
				},
				{
					ID:     "EQ-004",
					Name:   "Emergency Light",
					Type:   "SAFETY",
					Status: "MAINTENANCE",
					RoomID: "UNASSIGNED",
				},
			},
		},
	}
}