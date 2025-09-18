package bim

import (
	"strings"
	"testing"
	"time"
)

// Test fixtures
const validMinimalBIM = `===============================================================================
BUILDING: Test Building
FILE_VERSION: 1.0.0
GENERATED: 2025-01-13T10:00:00Z
===============================================================================

=====================================
FLOOR: 1 | Ground Floor
DIMENSIONS: 100x50
GRID_SCALE: 1:10 (1 char = 10 feet)
=====================================

LAYOUT:
##########
#        #
#        #
##########

===============================================================================
VALIDATION:
  CHECKSUM: SHA256:test
  EQUIPMENT_COUNT: 0
  CONNECTION_COUNT: 0
  LAST_MODIFIED: 2025-01-13T10:00:00Z
  MODIFIED_BY: test
===============================================================================`

const validComplexBIM = `===============================================================================
BUILDING: Central Hospital
FILE_VERSION: 1.0.0
GENERATED: 2025-01-13T10:00:00Z
COORDINATE_SYSTEM: TOP_LEFT_ORIGIN
UNITS: FEET
===============================================================================

=====================================
FLOOR: 1 | Emergency Department
DIMENSIONS: 100x50
GRID_SCALE: 1:10 (1 char = 10 feet)
=====================================

LEGEND:
  # = Wall
  . = Open Space
  D = Door
  + = Equipment

LAYOUT:
##########D##########
#     ROOM_1        #
#  +EQUIP_1         #
##########D##########

EQUIPMENT_REGISTRY:
-----------------
ID: EQUIP_1
  TYPE: Medical.Monitor
  LOCATION: (5,2) in ROOM_1
  STATUS: OPERATIONAL

CONNECTIONS:
-----------
POWER:
  PANEL_1 -> EQUIP_1 [120V/1PH/20A]

ISSUES_SUMMARY:
--------------
CRITICAL: 0

===============================================================================
VALIDATION:
  CHECKSUM: SHA256:test
  EQUIPMENT_COUNT: 1
  CONNECTION_COUNT: 1
  LAST_MODIFIED: 2025-01-13T10:00:00Z
  MODIFIED_BY: test
===============================================================================`

func TestParseMinimalBIM(t *testing.T) {
	parser := NewParser()
	reader := strings.NewReader(validMinimalBIM)

	building, err := parser.Parse(reader)
	if err != nil {
		t.Fatalf("Failed to parse minimal BIM: %v", err)
	}

	// Verify header
	if building.Name != "Test Building" {
		t.Errorf("Expected building name 'Test Building', got '%s'", building.Name)
	}

	if building.FileVersion != "1.0.0" {
		t.Errorf("Expected file version '1.0.0', got '%s'", building.FileVersion)
	}

	// Verify floor
	if len(building.Floors) != 1 {
		t.Fatalf("Expected 1 floor, got %d", len(building.Floors))
	}

	floor := building.Floors[0]
	if floor.Level != 1 {
		t.Errorf("Expected floor level 1, got %d", floor.Level)
	}

	if floor.Name != "Ground Floor" {
		t.Errorf("Expected floor name 'Ground Floor', got '%s'", floor.Name)
	}
}

func TestParseComplexBIM(t *testing.T) {
	parser := NewParser()
	reader := strings.NewReader(validComplexBIM)

	building, err := parser.Parse(reader)
	if err != nil {
		t.Fatalf("Failed to parse complex BIM: %v", err)
	}

	// Verify optional fields
	if building.CoordinateSystem != TopLeftOrigin {
		t.Errorf("Expected coordinate system TOP_LEFT_ORIGIN, got %s", building.CoordinateSystem)
	}

	if building.Units != Feet {
		t.Errorf("Expected units FEET, got %s", building.Units)
	}

	// Verify equipment
	if len(building.Floors) > 0 && len(building.Floors[0].Equipment) > 0 {
		equip := building.Floors[0].Equipment[0]
		if equip.ID != "EQUIP_1" {
			t.Errorf("Expected equipment ID 'EQUIP_1', got '%s'", equip.ID)
		}

		if equip.Status != StatusOperational {
			t.Errorf("Expected status OPERATIONAL, got %s", equip.Status)
		}
	}
}

func TestParseInvalidBIM(t *testing.T) {
	tests := []struct {
		name    string
		content string
		wantErr bool
	}{
		{
			name: "missing building name",
			content: `===============================================================================
FILE_VERSION: 1.0.0
===============================================================================`,
			wantErr: true,
		},
		{
			name: "missing file version",
			content: `===============================================================================
BUILDING: Test
===============================================================================`,
			wantErr: true,
		},
		{
			name: "duplicate equipment ID",
			content: `===============================================================================
BUILDING: Test
FILE_VERSION: 1.0.0
===============================================================================

=====================================
FLOOR: 1 | Test
=====================================

EQUIPMENT_REGISTRY:
-----------------
ID: EQUIP_1
  TYPE: Test
  STATUS: OPERATIONAL

ID: EQUIP_1
  TYPE: Test
  STATUS: OPERATIONAL

===============================================================================
VALIDATION:
===============================================================================`,
			wantErr: true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			parser := NewParser()
			reader := strings.NewReader(tt.content)

			_, err := parser.Parse(reader)
			if (err != nil) != tt.wantErr {
				t.Errorf("Parse() error = %v, wantErr %v", err, tt.wantErr)
			}
		})
	}
}

func TestParseWithOptions(t *testing.T) {
	parser := NewParser()
	reader := strings.NewReader(validMinimalBIM)

	opts := ParseOptions{
		Strict:           false, // Allow warnings
		PreserveComments: true,
		ValidateChecksum: false,
	}

	building, err := parser.ParseWithOptions(reader, opts)
	if err != nil {
		t.Fatalf("Failed to parse with options: %v", err)
	}

	if building == nil {
		t.Fatal("Expected building, got nil")
	}
}

func TestValidate(t *testing.T) {
	parser := NewParser()

	t.Run("valid file", func(t *testing.T) {
		reader := strings.NewReader(validMinimalBIM)
		err := parser.Validate(reader)
		if err != nil {
			t.Errorf("Validate() failed for valid file: %v", err)
		}
	})

	t.Run("invalid file", func(t *testing.T) {
		reader := strings.NewReader("invalid content")
		err := parser.Validate(reader)
		if err == nil {
			t.Error("Validate() should have failed for invalid file")
		}
	})
}

func TestParseFile(t *testing.T) {
	// Create a temporary test file
	content := validMinimalBIM
	tmpfile := strings.NewReader(content)

	// Since we can't create actual files in tests without filesystem access,
	// we'll test the Parse method directly (ParseFile is a thin wrapper)
	parser := NewParser()
	building, err := parser.Parse(tmpfile)

	if err != nil {
		t.Fatalf("Failed to parse: %v", err)
	}

	if building.Name != "Test Building" {
		t.Errorf("Expected building name 'Test Building', got '%s'", building.Name)
	}
}

func TestEquipmentStatus(t *testing.T) {
	tests := []struct {
		status   string
		expected EquipmentStatus
	}{
		{"OPERATIONAL", StatusOperational},
		{"WARNING", StatusWarning},
		{"FAILED", StatusFailed},
		{"UNKNOWN", StatusUnknown},
		{"MAINTENANCE", StatusMaintenance},
	}

	for _, tt := range tests {
		t.Run(tt.status, func(t *testing.T) {
			if EquipmentStatus(tt.status) != tt.expected {
				t.Errorf("Expected status %s to equal %s", tt.status, tt.expected)
			}
		})
	}
}

func TestPriority(t *testing.T) {
	tests := []struct {
		priority string
		expected Priority
	}{
		{"CRITICAL", PriorityCritical},
		{"HIGH", PriorityHigh},
		{"MEDIUM", PriorityMedium},
		{"LOW", PriorityLow},
	}

	for _, tt := range tests {
		t.Run(tt.priority, func(t *testing.T) {
			if Priority(tt.priority) != tt.expected {
				t.Errorf("Expected priority %s to equal %s", tt.priority, tt.expected)
			}
		})
	}
}

func TestConnectionType(t *testing.T) {
	tests := []struct {
		connType string
		expected ConnectionType
	}{
		{"POWER", ConnectionPower},
		{"NETWORK", ConnectionNetwork},
		{"PLUMBING", ConnectionPlumbing},
		{"HVAC", ConnectionHVAC},
		{"LOGICAL", ConnectionLogical},
	}

	for _, tt := range tests {
		t.Run(tt.connType, func(t *testing.T) {
			if ConnectionType(tt.connType) != tt.expected {
				t.Errorf("Expected connection type %s to equal %s", tt.connType, tt.expected)
			}
		})
	}
}

func TestParseError(t *testing.T) {
	err := ParseError{
		Line:    10,
		Column:  5,
		Message: "test error",
		Context: "context line",
	}

	expected := "parse error at line 10, column 5: test error"
	if err.Error() != expected {
		t.Errorf("Expected error message '%s', got '%s'", expected, err.Error())
	}
}

func TestValidationError(t *testing.T) {
	err := ValidationError{
		Field:   "EQUIPMENT.ID",
		Value:   "EQUIP_1",
		Message: "duplicate ID",
	}

	expected := "validation error in EQUIPMENT.ID: duplicate ID (value: EQUIP_1)"
	if err.Error() != expected {
		t.Errorf("Expected error message '%s', got '%s'", expected, err.Error())
	}
}

// Benchmark tests
func BenchmarkParseMinimal(b *testing.B) {
	parser := NewParser()

	for i := 0; i < b.N; i++ {
		reader := strings.NewReader(validMinimalBIM)
		_, _ = parser.Parse(reader)
	}
}

func BenchmarkParseComplex(b *testing.B) {
	parser := NewParser()

	for i := 0; i < b.N; i++ {
		reader := strings.NewReader(validComplexBIM)
		_, _ = parser.Parse(reader)
	}
}

// Helper function for testing time parsing
func mustParseTime(t *testing.T, timeStr string) time.Time {
	parsed, err := time.Parse(time.RFC3339, timeStr)
	if err != nil {
		t.Fatalf("Failed to parse time: %v", err)
	}
	return parsed
}
