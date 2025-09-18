package converter

import (
	"strings"
	"testing"
)

func TestPDFProcessor_ParseEquipmentFromText(t *testing.T) {
	processor := &PDFProcessor{}

	testCases := []struct {
		name     string
		text     string
		expected int
	}{
		{
			name:     "HVAC equipment pattern",
			text:     "Equipment ID: HVAC-001: Air Handler Unit - Model AC500",
			expected: 1,
		},
		{
			name:     "Panel with location pattern",
			text:     "Equipment ID: PANEL-001, Type: Electrical Panel, Location: Room 101",
			expected: 1,
		},
		{
			name:     "Equipment schedule pattern",
			text:     "AHU-01  Air Handling Unit  Carrier-39M  2  HVAC",
			expected: 1,
		},
		{
			name: "Multiple equipment entries",
			text: `Equipment ID: HVAC-001: Air Handler Unit - Model AC500
Equipment ID: PANEL-001, Type: Electrical Panel, Location: Room 101
AHU-01  Air Handling Unit  Carrier-39M  2  HVAC`,
			expected: 3,
		},
	}

	for _, tc := range testCases {
		t.Run(tc.name, func(t *testing.T) {
			equipment := processor.parseEquipmentFromText(tc.text)
			if len(equipment) != tc.expected {
				t.Errorf("Expected %d equipment items, got %d", tc.expected, len(equipment))
				for i, eq := range equipment {
					t.Logf("Equipment %d: ID=%s, Name=%s, Type=%s", i, eq.ID, eq.Name, eq.Type)
				}
			}
		})
	}
}

func TestPDFProcessor_InferEquipmentType(t *testing.T) {
	processor := &PDFProcessor{}

	testCases := []struct {
		text     string
		expected string
	}{
		{"Air Handler Unit", "HVAC"},
		{"Electrical Panel", "ELECTRICAL"},
		{"Water Pump", "PLUMBING"},
		{"Security Camera", "SECURITY"},
		{"Light Switch", "LIGHTING"},
		{"Network Switch", "NETWORK"},
		{"Fire Alarm", "FIRE"},
		{"Unknown Device", "GENERAL"},
	}

	for _, tc := range testCases {
		t.Run(tc.text, func(t *testing.T) {
			result := processor.inferEquipmentType(tc.text)
			if result != tc.expected {
				t.Errorf("For '%s', expected type '%s', got '%s'", tc.text, tc.expected, result)
			}
		})
	}
}

func TestPDFProcessor_ExtractFloorNumber(t *testing.T) {
	processor := &PDFProcessor{}

	testCases := []struct {
		equipment Equipment
		expected  int
	}{
		{
			equipment: Equipment{ID: "3/A/301"},
			expected:  3,
		},
		{
			equipment: Equipment{ID: "EQUIP-001", Name: "Floor 5 Equipment"},
			expected:  5,
		},
		{
			equipment: Equipment{ID: "PUMP-L2-001"},
			expected:  1, // Default when no floor pattern found
		},
		{
			equipment: Equipment{Name: "Level 2 Device"},
			expected:  2,
		},
	}

	for _, tc := range testCases {
		t.Run(tc.equipment.ID, func(t *testing.T) {
			result := processor.extractFloorNumber(&tc.equipment)
			if result != tc.expected {
				t.Errorf("For equipment %s, expected floor %d, got %d",
					tc.equipment.ID, tc.expected, result)
			}
		})
	}
}

func TestPDFProcessor_DetectTables(t *testing.T) {
	processor := &PDFProcessor{}

	tableText := `ID          Name                    Type        Model       Serial
OUTLET-01   Power Outlet           ELECTRICAL   LEV-5362    A12345
OUTLET-02   Power Outlet           ELECTRICAL   LEV-5362    A12346
SWITCH-01   Light Switch           ELECTRICAL   LEV-1201    B98765`

	tables := processor.detectTables(tableText)

	if len(tables) == 0 {
		t.Error("Expected to detect at least one table")
	}

	if len(tables) > 0 {
		table := tables[0]
		if len(table.Headers) < 3 {
			t.Errorf("Expected at least 3 headers, got %d", len(table.Headers))
		}
		if len(table.Rows) != 3 {
			t.Errorf("Expected 3 rows, got %d", len(table.Rows))
		}
	}
}

func TestPDFProcessor_IsEquipmentTable(t *testing.T) {
	processor := &PDFProcessor{}

	testCases := []struct {
		name     string
		table    Table
		expected bool
	}{
		{
			name: "Equipment table",
			table: Table{
				Headers: []string{"ID", "Name", "Type", "Model"},
			},
			expected: true,
		},
		{
			name: "Non-equipment table",
			table: Table{
				Headers: []string{"Date", "Time", "Description"},
			},
			expected: false,
		},
		{
			name: "Tag-based equipment table",
			table: Table{
				Headers: []string{"Tag", "Description", "Location"},
			},
			expected: true,
		},
	}

	for _, tc := range testCases {
		t.Run(tc.name, func(t *testing.T) {
			result := processor.isEquipmentTable(tc.table)
			if result != tc.expected {
				t.Errorf("Expected %v, got %v for headers: %v",
					tc.expected, result, strings.Join(tc.table.Headers, ", "))
			}
		})
	}
}
