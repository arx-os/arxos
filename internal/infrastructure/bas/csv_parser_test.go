package bas

import (
	"fmt"
	"os"
	"path/filepath"
	"testing"

	"github.com/arx-os/arxos/internal/domain/types"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

func TestCSVParser_ParseCSV(t *testing.T) {
	tests := []struct {
		name          string
		csvContent    string
		expectedCount int
		expectedError bool
		validate      func(t *testing.T, result *ParsedBASData)
	}{
		{
			name: "Valid Metasys export",
			csvContent: `Point Name,Device,Object Type,Description,Units,Location
AI-1-1,100301,Analog Input,Zone Temperature,degF,Floor 3 Room 301
AV-1-1,100301,Analog Value,Cooling Setpoint,degF,Floor 3 Room 301
BO-1-1,100301,Binary Output,Damper Command,%,Floor 3 Room 301`,
			expectedCount: 3,
			expectedError: false,
			validate: func(t *testing.T, result *ParsedBASData) {
				assert.Equal(t, 3, len(result.Points))
				assert.Equal(t, 3, result.RowCount)
				assert.Equal(t, 0, len(result.ParseErrors))

				// Check first point
				point := result.Points[0]
				assert.Equal(t, "AI-1-1", point.PointName)
				assert.Equal(t, "100301", point.DeviceID)
				assert.Equal(t, "Analog Input", point.ObjectType)
				assert.Equal(t, "Zone Temperature", point.Description)
				assert.Equal(t, "degF", point.Units)
				assert.Equal(t, "Floor 3 Room 301", point.LocationText)
				assert.Equal(t, "temperature", point.PointType)
			},
		},
		{
			name: "CSV with different column order",
			csvContent: `Description,Units,Point Name,Device,Object Type,Location
Zone Temperature,degF,AI-1-1,100301,Analog Input,Floor 3 Room 301`,
			expectedCount: 1,
			expectedError: false,
			validate: func(t *testing.T, result *ParsedBASData) {
				assert.Equal(t, 1, len(result.Points))
				point := result.Points[0]
				assert.Equal(t, "AI-1-1", point.PointName)
				assert.Equal(t, "Zone Temperature", point.Description)
			},
		},
		{
			name: "CSV with min/max values",
			csvContent: `Point Name,Device,Object Type,Description,Units,Min,Max
AI-1-1,100301,Analog Input,Zone Temperature,degF,32.0,120.0`,
			expectedCount: 1,
			expectedError: false,
			validate: func(t *testing.T, result *ParsedBASData) {
				point := result.Points[0]
				require.NotNil(t, point.MinValue)
				require.NotNil(t, point.MaxValue)
				assert.Equal(t, 32.0, *point.MinValue)
				assert.Equal(t, 120.0, *point.MaxValue)
			},
		},
		{
			name: "CSV with writeable column",
			csvContent: `Point Name,Device,Object Type,Writeable
AV-1-1,100301,Analog Value,true
BI-1-1,100301,Binary Input,false`,
			expectedCount: 2,
			expectedError: false,
			validate: func(t *testing.T, result *ParsedBASData) {
				assert.True(t, result.Points[0].Writeable)
				assert.False(t, result.Points[1].Writeable)
			},
		},
		{
			name:          "Empty CSV",
			csvContent:    `Point Name,Device,Object Type`,
			expectedCount: 0,
			expectedError: true, // Changed: Empty CSV should error
		},
		{
			name:          "Missing required columns",
			csvContent:    `Point Name,Description`,
			expectedCount: 0,
			expectedError: true,
		},
		{
			name: "CSV with empty rows",
			csvContent: `Point Name,Device,Object Type
AI-1-1,100301,Analog Input

AV-1-1,100301,Analog Value`,
			expectedCount: 2,
			expectedError: false,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			// Create temporary file
			tmpDir := t.TempDir()
			tmpFile := filepath.Join(tmpDir, "test.csv")

			err := os.WriteFile(tmpFile, []byte(tt.csvContent), 0644)
			require.NoError(t, err)

			// Parse CSV
			parser := NewCSVParser()
			result, err := parser.ParseCSV(tmpFile)

			if tt.expectedError {
				assert.Error(t, err)
				return
			}

			require.NoError(t, err)
			require.NotNil(t, result)
			assert.Equal(t, tt.expectedCount, len(result.Points))

			if tt.validate != nil {
				tt.validate(t, result)
			}
		})
	}
}

func TestCSVParser_inferPointType(t *testing.T) {
	parser := NewCSVParser()

	tests := []struct {
		objectType  string
		description string
		units       string
		expected    string
	}{
		{"Analog Input", "Zone Temperature", "degF", "temperature"},
		{"Analog Input", "Supply Air Pressure", "PSI", "pressure"},
		{"Analog Input", "Airflow", "CFM", "flow"},
		{"Binary Output", "Damper Command", "%", "control"},
		{"Binary Input", "Fan Status", "On/Off", "fan_status"},
		{"Analog Value", "Cooling Setpoint", "degF", "setpoint"},
		{"Analog Input", "Unknown Sensor", "", "analog_sensor"},
		{"Binary Input", "Unknown", "", "binary_sensor"},
		{"", "", "", "unknown"},
	}

	for _, tt := range tests {
		t.Run(tt.description, func(t *testing.T) {
			result := parser.inferPointType(tt.objectType, tt.description, tt.units)
			assert.Equal(t, tt.expected, result)
		})
	}
}

func TestCSVParser_ParseLocationText(t *testing.T) {
	parser := NewCSVParser()

	tests := []struct {
		input            string
		expectedFloor    string
		expectedRoom     string
		expectedBuilding string
	}{
		{"Floor 3 Room 301", "3", "301", ""},
		{"3rd Floor Room 301", "3", "301", ""},
		{"Fl 3 Rm 301", "3", "301", ""},
		{"Level 2 Conference A", "2", "a", ""},
		{"Building 1 Floor 3 Room 301", "3", "301", "1"},
		{"Bldg 2 Fl 1 Conf Room B", "1", "b", "2"},
		{"", "", "", ""},
	}

	for _, tt := range tests {
		t.Run(tt.input, func(t *testing.T) {
			result := parser.ParseLocationText(tt.input)

			if tt.input == "" {
				assert.Nil(t, result)
				return
			}

			require.NotNil(t, result)
			assert.Equal(t, tt.expectedFloor, result.Floor, "Floor mismatch")
			assert.Equal(t, tt.expectedRoom, result.Room, "Room mismatch")
			assert.Equal(t, tt.expectedBuilding, result.Building, "Building mismatch")
		})
	}
}

func TestCSVParser_DetectBASSystemType(t *testing.T) {
	parser := NewCSVParser()
	tmpDir := t.TempDir()

	tests := []struct {
		filename     string
		csvContent   string
		expectedType string
	}{
		{
			filename:     "metasys_export.csv",
			csvContent:   "Point Name,Device,Type\nAI-1-1,100301,Analog Input",
			expectedType: "johnson_controls_metasys",
		},
		{
			filename:     "desigo_points.csv",
			csvContent:   "Point Name,Device,Type\nAI-1-1,100301,Analog Input",
			expectedType: "siemens_desigo",
		},
		{
			filename:     "honeywell_export.csv",
			csvContent:   "Point Name,Device,Type\nAI-1-1,100301,Analog Input",
			expectedType: "honeywell_ebi",
		},
		{
			filename:     "points.csv",
			csvContent:   "Point Name,Device,Type\nAI-1-1,100301,Analog Input",
			expectedType: "other",
		},
	}

	for _, tt := range tests {
		t.Run(tt.filename, func(t *testing.T) {
			tmpFile := filepath.Join(tmpDir, tt.filename)
			err := os.WriteFile(tmpFile, []byte(tt.csvContent), 0644)
			require.NoError(t, err)

			result, err := parser.DetectBASSystemType(tmpFile)
			require.NoError(t, err)
			assert.Equal(t, tt.expectedType, string(result))
		})
	}
}

func TestCSVParser_ValidateCSV(t *testing.T) {
	parser := NewCSVParser()
	tmpDir := t.TempDir()

	t.Run("Valid CSV", func(t *testing.T) {
		tmpFile := filepath.Join(tmpDir, "valid.csv")
		content := "Point Name,Device,Type\nAI-1-1,100301,Analog Input"
		err := os.WriteFile(tmpFile, []byte(content), 0644)
		require.NoError(t, err)

		err = parser.ValidateCSV(tmpFile)
		assert.NoError(t, err)
	})

	t.Run("Empty file", func(t *testing.T) {
		tmpFile := filepath.Join(tmpDir, "empty.csv")
		err := os.WriteFile(tmpFile, []byte(""), 0644)
		require.NoError(t, err)

		err = parser.ValidateCSV(tmpFile)
		assert.Error(t, err)
		assert.Contains(t, err.Error(), "empty")
	})

	t.Run("Too few columns", func(t *testing.T) {
		tmpFile := filepath.Join(tmpDir, "few_cols.csv")
		content := "Point Name,Device"
		err := os.WriteFile(tmpFile, []byte(content), 0644)
		require.NoError(t, err)

		err = parser.ValidateCSV(tmpFile)
		assert.Error(t, err)
		assert.Contains(t, err.Error(), "at least 3 columns")
	})

	t.Run("Non-existent file", func(t *testing.T) {
		err := parser.ValidateCSV("/nonexistent/file.csv")
		assert.Error(t, err)
	})
}

func TestCSVParser_ToBASPoints(t *testing.T) {
	parser := NewCSVParser()

	parsedData := &ParsedBASData{
		Points: []ParsedBASPoint{
			{
				PointName:    "AI-1-1",
				DeviceID:     "100301",
				ObjectType:   "Analog Input",
				Description:  "Zone Temperature",
				Units:        "degF",
				LocationText: "Floor 3 Room 301",
				PointType:    "temperature",
			},
			{
				PointName:    "AV-1-1",
				DeviceID:     "100301",
				ObjectType:   "Analog Value",
				Description:  "Cooling Setpoint",
				Units:        "degF",
				LocationText: "Floor 3 Room 301",
				PointType:    "setpoint",
				Writeable:    true,
			},
		},
	}

	buildingID := types.NewID()
	systemID := types.NewID()

	points := parser.ToBASPoints(parsedData, buildingID, systemID)

	require.Equal(t, 2, len(points))

	// Check first point
	point1 := points[0]
	assert.Equal(t, buildingID, point1.BuildingID)
	assert.Equal(t, systemID, point1.BASSystemID)
	assert.Equal(t, "AI-1-1", point1.PointName)
	assert.Equal(t, "100301", point1.DeviceID)
	assert.Equal(t, "temperature", point1.PointType)
	assert.False(t, point1.Mapped)
	assert.Equal(t, 0, point1.MappingConfidence)

	// Check second point
	point2 := points[1]
	assert.Equal(t, "AV-1-1", point2.PointName)
	assert.True(t, point2.Writeable)
	assert.Equal(t, "setpoint", point2.PointType)
}

func TestCSVParser_mapColumns(t *testing.T) {
	parser := NewCSVParser()

	tests := []struct {
		name     string
		header   []string
		expected map[string]int
	}{
		{
			name:   "Standard Metasys header",
			header: []string{"Point Name", "Device", "Object Type", "Description", "Units", "Location"},
			expected: map[string]int{
				"point_name":  0,
				"device":      1,
				"object_type": 2,
				"description": 3,
				"units":       4,
				"location":    5,
			},
		},
		{
			name:   "Alternate column names",
			header: []string{"PointName", "DeviceID", "Type", "Desc", "Unit", "Room"},
			expected: map[string]int{
				"point_name":  0,
				"device":      1,
				"object_type": 2,
				"description": 3,
				"units":       4,
				"location":    5,
			},
		},
		{
			name:   "Case insensitive",
			header: []string{"POINT NAME", "DEVICE", "OBJECT TYPE"},
			expected: map[string]int{
				"point_name":  0,
				"device":      1,
				"object_type": 2,
			},
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := parser.mapColumns(tt.header)

			for key, expectedIdx := range tt.expected {
				actualIdx, exists := result[key]
				assert.True(t, exists, "Column %s not found", key)
				assert.Equal(t, expectedIdx, actualIdx, "Column %s has wrong index", key)
			}
		})
	}
}

func TestCSVParser_parseBool(t *testing.T) {
	parser := NewCSVParser()

	tests := []struct {
		input    string
		expected bool
	}{
		{"true", true},
		{"True", true},
		{"TRUE", true},
		{"yes", true},
		{"Yes", true},
		{"y", true},
		{"1", true},
		{"on", true},
		{"enabled", true},
		{"writable", true},
		{"false", false},
		{"no", false},
		{"0", false},
		{"off", false},
		{"", false},
		{"random", false},
	}

	for _, tt := range tests {
		t.Run(tt.input, func(t *testing.T) {
			result := parser.parseBool(tt.input)
			assert.Equal(t, tt.expected, result)
		})
	}
}

func TestCSVParser_validateColumns(t *testing.T) {
	parser := NewCSVParser()

	tests := []struct {
		name          string
		columns       map[string]int
		expectedError bool
	}{
		{
			name: "All required columns present",
			columns: map[string]int{
				"point_name":  0,
				"device":      1,
				"object_type": 2,
			},
			expectedError: false,
		},
		{
			name: "Missing point_name",
			columns: map[string]int{
				"device":      1,
				"object_type": 2,
			},
			expectedError: true,
		},
		{
			name: "Missing device",
			columns: map[string]int{
				"point_name":  0,
				"object_type": 2,
			},
			expectedError: true,
		},
		{
			name:          "No columns",
			columns:       map[string]int{},
			expectedError: true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			err := parser.validateColumns(tt.columns)

			if tt.expectedError {
				assert.Error(t, err)
			} else {
				assert.NoError(t, err)
			}
		})
	}
}

// Helper function to create test CSV file
func createTestCSVFile(t *testing.T, content string) string {
	tmpDir := t.TempDir()
	tmpFile := filepath.Join(tmpDir, "test.csv")

	err := os.WriteFile(tmpFile, []byte(content), 0644)
	require.NoError(t, err)

	return tmpFile
}

func BenchmarkCSVParser_ParseCSV(b *testing.B) {
	// Create a large CSV for benchmarking
	var content string
	content = "Point Name,Device,Object Type,Description,Units,Location\n"
	for i := 0; i < 1000; i++ {
		content += fmt.Sprintf("AI-%d-1,%d,Analog Input,Zone Temperature,degF,Floor 3 Room %d\n", i, 100000+i, i)
	}

	tmpDir := b.TempDir()
	tmpFile := filepath.Join(tmpDir, "benchmark.csv")
	os.WriteFile(tmpFile, []byte(content), 0644)

	parser := NewCSVParser()

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		_, err := parser.ParseCSV(tmpFile)
		if err != nil {
			b.Fatal(err)
		}
	}
}
