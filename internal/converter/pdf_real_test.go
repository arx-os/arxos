package converter

import (
	"strings"
	"testing"
)

func TestRealPDFConverter_GetFormat(t *testing.T) {
	converter := NewRealPDFConverter()
	if got := converter.GetFormat(); got != "pdf" {
		t.Errorf("GetFormat() = %v, want pdf", got)
	}
}

func TestRealPDFConverter_GetDescription(t *testing.T) {
	converter := NewRealPDFConverter()
	desc := converter.GetDescription()
	if !strings.Contains(desc, "PDF") {
		t.Errorf("GetDescription() = %v, should contain 'PDF'", desc)
	}
}

func TestRealPDFConverter_CanConvert(t *testing.T) {
	converter := NewRealPDFConverter()

	tests := []struct {
		filename string
		want     bool
	}{
		{"test.pdf", true},
		{"TEST.PDF", true},
		{"document.Pdf", true},
		{"file.txt", false},
		{"file.doc", false},
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

func TestRealPDFConverter_extractRooms(t *testing.T) {
	converter := NewRealPDFConverter()

	tests := []struct {
		name     string
		text     string
		expected []map[string]string
	}{
		{
			name: "Standard room format",
			text: "ROOM 101 - Conference Room - 250 sq ft",
			expected: []map[string]string{
				{
					"number": "101",
					"name":   "Conference Room",
					"area":   "250",
				},
			},
		},
		{
			name: "IDF telecom room",
			text: "IDF 103A - Telecom Closet",
			expected: []map[string]string{
				{
					"number": "103A",
					"name":   "IDF 103A - Telecom Closet",
					"type":   "telecom",
				},
			},
		},
		{
			name: "MDF telecom room",
			text: "MDF 104B - Main Distribution Frame",
			expected: []map[string]string{
				{
					"number": "104B",
					"name":   "MDF 104B - Main Distribution Frame",
					"type":   "telecom",
				},
			},
		},
		{
			name: "Suite format",
			text: "SUITE 201 - Executive Office - 300 sq ft",
			expected: []map[string]string{
				{
					"number": "201",
					"name":   "SUITE 201 - Executive Office",
					"type":   "suite",
					"area":   "300",
				},
			},
		},
		{
			name: "Office format",
			text: "OFFICE 202 - Manager Office",
			expected: []map[string]string{
				{
					"number": "202",
					"name":   "OFFICE 202 - Manager Office",
					"type":   "office",
				},
			},
		},
		{
			name: "Multiple rooms",
			text: `ROOM 101 - Conference Room - 250 sq ft
ROOM 102 - Office Space - 150 sq ft
IDF 103A - Telecom Closet`,
			expected: []map[string]string{
				{
					"number": "101",
					"name":   "Conference Room",
					"area":   "250",
				},
				{
					"number": "102",
					"name":   "Office Space",
					"area":   "150",
				},
				{
					"number": "103A",
					"name":   "IDF 103A - Telecom Closet",
					"type":   "telecom",
				},
			},
		},
		{
			name: "No rooms",
			text: "Building Information\nNo room data here",
			expected: []map[string]string{},
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			rooms := converter.extractRooms(tt.text)

			if len(rooms) != len(tt.expected) {
				t.Errorf("extractRooms() returned %d rooms, want %d", len(rooms), len(tt.expected))
				return
			}

			for i, room := range rooms {
				expected := tt.expected[i]

				if room["number"] != expected["number"] {
					t.Errorf("Room %d: number = %v, want %v", i, room["number"], expected["number"])
				}
				if room["name"] != expected["name"] {
					t.Errorf("Room %d: name = %v, want %v", i, room["name"], expected["name"])
				}
				if expected["type"] != "" && room["type"] != expected["type"] {
					t.Errorf("Room %d: type = %v, want %v", i, room["type"], expected["type"])
				}
				if expected["area"] != "" && room["area"] != expected["area"] {
					t.Errorf("Room %d: area = %v, want %v", i, room["area"], expected["area"])
				}
			}
		})
	}
}

func TestRealPDFConverter_inferRoomType(t *testing.T) {
	converter := NewRealPDFConverter()

	tests := []struct {
		name     string
		roomName string
		expected string
	}{
		{"IDF room", "IDF 101", "telecom"},
		{"MDF room", "MDF 201", "telecom"},
		{"TDF room", "TDF 301", "telecom"},
		{"Lobby", "Main Lobby", "lobby"},
		{"Conference room", "Conference Room A", "conference"},
		{"Office", "Office Space", "office"},
		{"Server room", "Server Room", "datacenter"},
		{"Storage", "Storage Closet", "storage"},
		{"Mechanical", "Mechanical Room", "mechanical"},
		{"Electrical", "Electrical Room", "electrical"},
		{"Restroom", "Men's Restroom", "restroom"},
		{"Bathroom", "Employee Bathroom", "restroom"},
		{"Unknown", "Unknown Space", "room"},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			if got := converter.inferRoomType(tt.roomName); got != tt.expected {
				t.Errorf("inferRoomType(%v) = %v, want %v", tt.roomName, got, tt.expected)
			}
		})
	}
}

func TestRealPDFConverter_inferEquipmentType(t *testing.T) {
	converter := NewRealPDFConverter()

	tests := []struct {
		name     string
		tag      string
		expected string
	}{
		{"AHU equipment", "AHU-01", "hvac"},
		{"VAV equipment", "VAV-101", "hvac"},
		{"FCU equipment", "FCU-201", "hvac"},
		{"RTU equipment", "RTU-01", "hvac"},
		{"Panel equipment", "PANEL-A", "electrical"},
		{"EP equipment", "EP-101", "electrical"},
		{"PDU equipment", "PDU-02", "electrical"},
		{"UPS equipment", "UPS-01", "electrical"},
		{"Pump equipment", "PUMP-01", "plumbing"},
		{"Valve equipment", "VALVE-23", "plumbing"},
		{"Fire equipment", "FIRE-01", "fire_safety"},
		{"Smoke equipment", "SMOKE-02", "fire_safety"},
		{"Unknown equipment", "UNKNOWN-01", "equipment"},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			if got := converter.inferEquipmentType(tt.tag); got != tt.expected {
				t.Errorf("inferEquipmentType(%v) = %v, want %v", tt.tag, got, tt.expected)
			}
		})
	}
}