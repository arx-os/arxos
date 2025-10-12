package naming

import (
	"testing"
)

func TestGenerateEquipmentPath(t *testing.T) {
	tests := []struct {
		name      string
		building  string
		floor     string
		room      string
		system    string
		equipment string
		want      string
	}{
		{
			name:      "Full path with room",
			building:  "B1",
			floor:     "3",
			room:      "301",
			system:    "HVAC",
			equipment: "VAV-301",
			want:      "/B1/3/301/HVAC/VAV-301",
		},
		{
			name:      "Building level equipment (no room)",
			building:  "B1",
			floor:     "R",
			room:      "",
			system:    "HVAC",
			equipment: "AHU-1",
			want:      "/B1/R/HVAC/AHU-1",
		},
		{
			name:      "Electrical panel in electrical room",
			building:  "B1",
			floor:     "1",
			room:      "ELEC-RM",
			system:    "ELEC",
			equipment: "PANEL-1A",
			want:      "/B1/1/ELEC-RM/ELEC/PANEL-1A",
		},
		{
			name:      "Network equipment in MDF",
			building:  "MAIN",
			floor:     "1",
			room:      "MDF",
			system:    "NETWORK",
			equipment: "CORE-SW-1",
			want:      "/MAIN/1/MDF/NETWORK/CORE-SW-1",
		},
		{
			name:      "Sanitizes lowercase input",
			building:  "b1",
			floor:     "2",
			room:      "room 205",
			system:    "network",
			equipment: "wap-205",
			want:      "/B1/2/ROOM-205/NETWORK/WAP-205",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got := GenerateEquipmentPath(tt.building, tt.floor, tt.room, tt.system, tt.equipment)
			if got != tt.want {
				t.Errorf("GenerateEquipmentPath() = %v, want %v", got, tt.want)
			}
		})
	}
}

func TestParseEquipmentPath(t *testing.T) {
	tests := []struct {
		name    string
		path    string
		want    *PathComponents
		wantErr bool
	}{
		{
			name: "Full path with room",
			path: "/B1/3/301/HVAC/VAV-301",
			want: &PathComponents{
				Building:  "B1",
				Floor:     "3",
				Room:      "301",
				System:    "HVAC",
				Equipment: "VAV-301",
			},
			wantErr: false,
		},
		{
			name: "Building level (no room)",
			path: "/B1/R/HVAC/AHU-1",
			want: &PathComponents{
				Building:  "B1",
				Floor:     "R",
				Room:      "",
				System:    "HVAC",
				Equipment: "AHU-1",
			},
			wantErr: false,
		},
		{
			name:    "Missing leading slash",
			path:    "B1/3/301/HVAC/VAV-301",
			want:    nil,
			wantErr: true,
		},
		{
			name:    "Too few segments",
			path:    "/B1/3/HVAC",
			want:    nil,
			wantErr: true,
		},
		{
			name:    "Too many segments",
			path:    "/B1/3/301/HVAC/VAV-301/EXTRA",
			want:    nil,
			wantErr: true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got, err := ParseEquipmentPath(tt.path)
			if (err != nil) != tt.wantErr {
				t.Errorf("ParseEquipmentPath() error = %v, wantErr %v", err, tt.wantErr)
				return
			}
			if !tt.wantErr {
				if got.Building != tt.want.Building ||
					got.Floor != tt.want.Floor ||
					got.Room != tt.want.Room ||
					got.System != tt.want.System ||
					got.Equipment != tt.want.Equipment {
					t.Errorf("ParseEquipmentPath() = %+v, want %+v", got, tt.want)
				}
			}
		})
	}
}

func TestIsValidPath(t *testing.T) {
	tests := []struct {
		name string
		path string
		want bool
	}{
		{
			name: "Valid full path",
			path: "/B1/3/301/HVAC/VAV-301",
			want: true,
		},
		{
			name: "Valid building level path",
			path: "/B1/R/HVAC/AHU-1",
			want: true,
		},
		{
			name: "Valid complex building code",
			path: "/HS-LINCOLN/2/IDF-2A/NETWORK/SW-01",
			want: true,
		},
		{
			name: "Invalid - lowercase",
			path: "/b1/3/301/hvac/vav-301",
			want: false,
		},
		{
			name: "Invalid - spaces",
			path: "/B1/3/Room 301/HVAC/VAV 301",
			want: false,
		},
		{
			name: "Invalid - missing leading slash",
			path: "B1/3/301/HVAC/VAV-301",
			want: false,
		},
		{
			name: "Invalid - empty segment",
			path: "/B1//301/HVAC/VAV-301",
			want: false,
		},
		{
			name: "Invalid - too few segments",
			path: "/B1/3/HVAC",
			want: false,
		},
		{
			name: "Invalid - special characters",
			path: "/B1/3/301/HVAC/VAV_301",
			want: false,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got := IsValidPath(tt.path)
			if got != tt.want {
				t.Errorf("IsValidPath() = %v, want %v", got, tt.want)
			}
		})
	}
}

func TestMatchPathPattern(t *testing.T) {
	tests := []struct {
		name    string
		path    string
		pattern string
		want    bool
	}{
		{
			name:    "Exact match",
			path:    "/B1/3/301/HVAC/VAV-301",
			pattern: "/B1/3/301/HVAC/VAV-301",
			want:    true,
		},
		{
			name:    "Wildcard room",
			path:    "/B1/3/301/HVAC/VAV-301",
			pattern: "/B1/3/*/HVAC/VAV-301",
			want:    true,
		},
		{
			name:    "Wildcard equipment",
			path:    "/B1/3/301/HVAC/VAV-301",
			pattern: "/B1/3/301/HVAC/*",
			want:    true,
		},
		{
			name:    "Multiple wildcards",
			path:    "/B1/3/301/HVAC/VAV-301",
			pattern: "/B1/*/*/HVAC/*",
			want:    true,
		},
		{
			name:    "All HVAC equipment",
			path:    "/B1/2/205/HVAC/STAT-01",
			pattern: "/*/*/*/HVAC/*",
			want:    true,
		},
		{
			name:    "Wrong floor",
			path:    "/B1/3/301/HVAC/VAV-301",
			pattern: "/B1/2/*/HVAC/*",
			want:    false,
		},
		{
			name:    "Wrong system",
			path:    "/B1/3/301/ELEC/OUTLET-1",
			pattern: "/B1/3/301/HVAC/*",
			want:    false,
		},
		{
			name:    "Different segment count",
			path:    "/B1/R/HVAC/AHU-1",
			pattern: "/B1/R/*/HVAC/AHU-1",
			want:    false,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got := MatchPathPattern(tt.path, tt.pattern)
			if got != tt.want {
				t.Errorf("MatchPathPattern() = %v, want %v", got, tt.want)
			}
		})
	}
}

func TestSanitizePathSegment(t *testing.T) {
	tests := []struct {
		name    string
		segment string
		want    string
	}{
		{
			name:    "Simple uppercase",
			segment: "B1",
			want:    "B1",
		},
		{
			name:    "Lowercase to uppercase",
			segment: "building1",
			want:    "BUILDING1",
		},
		{
			name:    "Spaces to hyphens",
			segment: "Room 301",
			want:    "ROOM-301",
		},
		{
			name:    "Remove special characters",
			segment: "Panel_1A!",
			want:    "PANEL1A",
		},
		{
			name:    "Multiple spaces collapse",
			segment: "Main   Building",
			want:    "MAIN-BUILDING",
		},
		{
			name:    "Leading/trailing spaces",
			segment: " B1 ",
			want:    "B1",
		},
		{
			name:    "Mixed case with hyphens",
			segment: "north-wing",
			want:    "NORTH-WING",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got := sanitizePathSegment(tt.segment)
			if got != tt.want {
				t.Errorf("sanitizePathSegment() = %v, want %v", got, tt.want)
			}
		})
	}
}

func TestGetSystemCode(t *testing.T) {
	tests := []struct {
		name     string
		category string
		want     string
	}{
		{
			name:     "Electrical",
			category: "electrical",
			want:     "ELEC",
		},
		{
			name:     "HVAC",
			category: "hvac",
			want:     "HVAC",
		},
		{
			name:     "Network",
			category: "network",
			want:     "NETWORK",
		},
		{
			name:     "Safety",
			category: "safety",
			want:     "SAFETY",
		},
		{
			name:     "Fire (alias for safety)",
			category: "fire",
			want:     "SAFETY",
		},
		{
			name:     "IT (alias for network)",
			category: "it",
			want:     "NETWORK",
		},
		{
			name:     "Unknown category",
			category: "custom_system",
			want:     "CUSTOMSYSTEM", // Underscores are removed, not converted to hyphens
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got := GetSystemCode(tt.category)
			if got != tt.want {
				t.Errorf("GetSystemCode() = %v, want %v", got, tt.want)
			}
		})
	}
}

func TestGenerateEquipmentCode(t *testing.T) {
	tests := []struct {
		name       string
		equipName  string
		identifier string
		want       string
	}{
		{
			name:       "Electrical Panel",
			equipName:  "Electrical Panel",
			identifier: "1A",
			want:       "PANEL-1A",
		},
		{
			name:       "VAV Box",
			equipName:  "VAV Box",
			identifier: "301",
			want:       "VAV-301",
		},
		{
			name:       "Air Handler",
			equipName:  "Air Handler Unit",
			identifier: "1",
			want:       "AHU-1",
		},
		{
			name:       "Transformer",
			equipName:  "Transformer",
			identifier: "T1",
			want:       "XFMR-T1",
		},
		{
			name:       "Network Switch",
			equipName:  "Network Switch",
			identifier: "2F-01",
			want:       "SW-2F-01",
		},
		{
			name:       "Wireless Access Point",
			equipName:  "Wireless Access Point",
			identifier: "205",
			want:       "WAP-205",
		},
		{
			name:       "No identifier",
			equipName:  "Electrical Panel",
			identifier: "",
			want:       "PANEL",
		},
		{
			name:       "Unknown equipment type",
			equipName:  "Custom Device XYZ",
			identifier: "A1",
			want:       "CUSTOM-A1",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got := GenerateEquipmentCode(tt.equipName, tt.identifier)
			if got != tt.want {
				t.Errorf("GenerateEquipmentCode() = %v, want %v", got, tt.want)
			}
		})
	}
}

func TestBuildingCodeFromName(t *testing.T) {
	tests := []struct {
		name  string
		input string
		want  string
	}{
		{
			name:  "Main Building",
			input: "Main Building",
			want:  "MAIN",
		},
		{
			name:  "North Wing",
			input: "North Wing Building",
			want:  "NORTH",
		},
		{
			name:  "Office Tower",
			input: "Office Tower",
			want:  "OFFICE-TWR",
		},
		{
			name:  "High School",
			input: "Lincoln High School",
			want:  "LINCOLN-HS",
		},
		{
			name:  "Simple B1",
			input: "Building 1",
			want:  "1",
		},
		{
			name:  "Empty name",
			input: "",
			want:  "B1",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got := BuildingCodeFromName(tt.input)
			if got != tt.want {
				t.Errorf("BuildingCodeFromName() = %v, want %v", got, tt.want)
			}
		})
	}
}

func TestFloorCodeFromLevel(t *testing.T) {
	tests := []struct {
		name  string
		level string
		want  string
	}{
		{
			name:  "Floor 1",
			level: "1",
			want:  "1",
		},
		{
			name:  "Ground Floor",
			level: "Ground Floor",
			want:  "1",
		},
		{
			name:  "Basement",
			level: "Basement",
			want:  "B",
		},
		{
			name:  "Roof",
			level: "Roof",
			want:  "R",
		},
		{
			name:  "Mezzanine",
			level: "Mezzanine",
			want:  "M",
		},
		{
			name:  "Level 3",
			level: "Level 3",
			want:  "3",
		},
		{
			name:  "Second Floor",
			level: "Second",
			want:  "SECOND",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got := FloorCodeFromLevel(tt.level)
			if got != tt.want {
				t.Errorf("FloorCodeFromLevel() = %v, want %v", got, tt.want)
			}
		})
	}
}

func TestRoomCodeFromName(t *testing.T) {
	tests := []struct {
		name string
		room string
		want string
	}{
		{
			name: "Simple room number",
			room: "101",
			want: "101",
		},
		{
			name: "Room 301",
			room: "Room 301",
			want: "301",
		},
		{
			name: "Conference Room",
			room: "Conference Room 301",
			want: "CONF-301",
		},
		{
			name: "Mechanical Room",
			room: "Mechanical Room A",
			want: "MECH-A",
		},
		{
			name: "Electrical Room",
			room: "Electrical Room",
			want: "ELEC",
		},
		{
			name: "MDF",
			room: "MDF",
			want: "MDF",
		},
		{
			name: "IDF 2A",
			room: "IDF 2A",
			want: "IDF-2A",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got := RoomCodeFromName(tt.room)
			if got != tt.want {
				t.Errorf("RoomCodeFromName() = %v, want %v", got, tt.want)
			}
		})
	}
}

func TestToSQLPattern(t *testing.T) {
	tests := []struct {
		name    string
		pattern string
		want    string
	}{
		{
			name:    "All HVAC on floor 3",
			pattern: "/B1/3/*/HVAC/*",
			want:    "/B1/3/%/HVAC/%",
		},
		{
			name:    "All electrical panels",
			pattern: "/*/*/*/ELEC/PANEL-*",
			want:    "/%/%/%/ELEC/PANEL-%",
		},
		{
			name:    "Specific equipment",
			pattern: "/B1/3/301/HVAC/VAV-301",
			want:    "/B1/3/301/HVAC/VAV-301",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got := ToSQLPattern(tt.pattern)
			if got != tt.want {
				t.Errorf("ToSQLPattern() = %v, want %v", got, tt.want)
			}
		})
	}
}
