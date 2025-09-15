package converter

import (
	"strings"
	"testing"
)

func TestImprovedIFCConverter_GetFormat(t *testing.T) {
	converter := NewImprovedIFCConverter()
	if got := converter.GetFormat(); got != "ifc" {
		t.Errorf("GetFormat() = %v, want ifc", got)
	}
}

func TestImprovedIFCConverter_GetDescription(t *testing.T) {
	converter := NewImprovedIFCConverter()
	desc := converter.GetDescription()
	if !strings.Contains(desc, "IFC") {
		t.Errorf("GetDescription() = %v, should contain 'IFC'", desc)
	}
}

func TestImprovedIFCConverter_CanConvert(t *testing.T) {
	converter := NewImprovedIFCConverter()

	tests := []struct {
		filename string
		want     bool
	}{
		{"model.ifc", true},
		{"MODEL.IFC", true},
		{"building.ifcxml", true},
		{"project.ifczip", true},
		{"file.txt", false},
		{"file.dwg", false},
		{"file", false},
		{"", false},
	}

	for _, tt := range tests {
		t.Run(tt.filename, func(t *testing.T) {
			if got := converter.CanConvert(tt.filename); got != tt.want {
				t.Errorf("CanConvert(%v) = %v, want %v", tt.filename, got, tt.want)
			}
		})
	}
}

func TestImprovedIFCConverter_parseIFCProperties(t *testing.T) {
	converter := NewImprovedIFCConverter()

	tests := []struct {
		name     string
		input    string
		expected []string
	}{
		{
			name:     "Simple properties",
			input:    "'guid',$,'name','description'",
			expected: []string{"'guid'", "$", "'name'", "'description'"},
		},
		{
			name:     "Properties with nested parentheses",
			input:    "'guid',IFCAXIS2PLACEMENT3D(#13,$,$),'name'",
			expected: []string{"'guid'", "IFCAXIS2PLACEMENT3D(#13,$,$)", "'name'"},
		},
		{
			name:     "Properties with quoted commas",
			input:    "'guid,with,commas',$,'name'",
			expected: []string{"'guid,with,commas'", "$", "'name'"},
		},
		{
			name:     "Empty input",
			input:    "",
			expected: []string{},
		},
		{
			name:     "Single property",
			input:    "'single'",
			expected: []string{"'single'"},
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := converter.parseIFCProperties(tt.input)

			if len(result) != len(tt.expected) {
				t.Errorf("parseIFCProperties() returned %d items, want %d", len(result), len(tt.expected))
				return
			}

			for i, prop := range result {
				if prop != tt.expected[i] {
					t.Errorf("parseIFCProperties()[%d] = %v, want %v", i, prop, tt.expected[i])
				}
			}
		})
	}
}

func TestImprovedIFCConverter_extractRoomNumber(t *testing.T) {
	converter := NewImprovedIFCConverter()

	tests := []struct {
		name     string
		roomName string
		expected string
	}{
		{"Room with number", "Room 101", "101"},
		{"Space number", "Space 201A", "201"},
		{"Office number", "Office 305B", "305"},
		{"Number only", "123", "123"},
		{"No number", "Conference Room", "Conference Room"},
		{"Multiple numbers", "Room 101 Level 2", "101"},
		{"Empty name", "", ""},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			if got := converter.extractRoomNumber(tt.roomName); got != tt.expected {
				t.Errorf("extractRoomNumber(%v) = %v, want %v", tt.roomName, got, tt.expected)
			}
		})
	}
}

func TestImprovedIFCConverter_mapIFCToEquipmentType(t *testing.T) {
	converter := NewImprovedIFCConverter()

	tests := []struct {
		name     string
		ifcType  string
		expected string
	}{
		{"Flow controller", "IFCFLOWCONTROLLER", "hvac"},
		{"Flow terminal", "IFCFLOWTERMINAL", "hvac"},
		{"Energy conversion", "IFCENERGYCONVERSIONDEVICE", "hvac"},
		{"Flow moving device", "IFCFLOWMOVINGDEVICE", "hvac"},
		{"Furnishing", "IFCFURNISHINGELEMENT", "furniture"},
		{"Distribution", "IFCDISTRIBUTIONELEMENT", "mechanical"},
		{"Building proxy", "IFCBUILDINGELEMENTPROXY", "equipment"},
		{"Flow fitting", "IFCFLOWFITTING", "plumbing"},
		{"Flow storage", "IFCFLOWSTORAGEDEVICE", "storage"},
		{"Unknown type", "IFCUNKNOWN", "equipment"},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			if got := converter.mapIFCToEquipmentType(tt.ifcType); got != tt.expected {
				t.Errorf("mapIFCToEquipmentType(%v) = %v, want %v", tt.ifcType, got, tt.expected)
			}
		})
	}
}

func TestImprovedIFCConverter_getEntitiesByType(t *testing.T) {
	converter := NewImprovedIFCConverter()

	entities := []IFCEntity{
		{ID: "#1", Type: "IFCBUILDING", Name: "Building 1"},
		{ID: "#2", Type: "IFCBUILDINGSTOREY", Name: "Floor 1"},
		{ID: "#3", Type: "IFCSPACE", Name: "Room 101"},
		{ID: "#4", Type: "IFCBUILDING", Name: "Building 2"},
		{ID: "#5", Type: "IFCSPACE", Name: "Room 102"},
	}

	tests := []struct {
		name       string
		entityType string
		expected   int
	}{
		{"Buildings", "IFCBUILDING", 2},
		{"Building storeys", "IFCBUILDINGSTOREY", 1},
		{"Spaces", "IFCSPACE", 2},
		{"Non-existent", "IFCWALL", 0},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := converter.getEntitiesByType(entities, tt.entityType)
			if len(result) != tt.expected {
				t.Errorf("getEntitiesByType(%v) returned %d entities, want %d", tt.entityType, len(result), tt.expected)
			}
		})
	}
}