package converter

import (
	"strings"
	"testing"
)

func TestBuilding_Validate(t *testing.T) {
	tests := []struct {
		name        string
		building    Building
		expectIssues int
	}{
		{
			name: "Valid building",
			building: Building{
				Name: "Test Building",
				Floors: []Floor{
					{
						ID:   "1",
						Name: "Ground Floor",
						Rooms: []Room{
							{
								Number: "101",
								Name:   "Office",
								Type:   "office",
								Equipment: []Equipment{
									{
										Tag:  "AHU-01",
										Name: "Air Handler",
										Type: "hvac",
									},
								},
							},
						},
					},
				},
			},
			expectIssues: 0,
		},
		{
			name: "Missing building name",
			building: Building{
				Floors: []Floor{
					{
						ID:    "1",
						Name:  "Ground Floor",
						Rooms: []Room{{Number: "101", Name: "Office", Type: "office"}},
					},
				},
			},
			expectIssues: 1,
		},
		{
			name: "No floors",
			building: Building{
				Name: "Test Building",
			},
			expectIssues: 1,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			issues := tt.building.Validate()
			if len(issues) != tt.expectIssues {
				t.Errorf("Validate() found %d issues, want %d. Issues: %v", len(issues), tt.expectIssues, issues)
			}
		})
	}
}

func TestBuilding_ToBIM(t *testing.T) {
	building := Building{
		ID:      "B001",
		Name:    "Test Building",
		Address: "123 Test Street",
		Metadata: Metadata{
			Source: "Test Import",
			Format: "TEST",
		},
		Floors: []Floor{
			{
				ID:        "1",
				Name:      "Ground Floor",
				Elevation: 0.0,
				Rooms: []Room{
					{
						Number: "101",
						Name:   "Conference Room",
						Type:   "conference",
						Area:   250.0,
						Equipment: []Equipment{
							{
								Tag:    "AHU-01",
								Name:   "Air Handler",
								Type:   "hvac",
								Status: "operational",
							},
						},
					},
				},
			},
		},
	}

	bim := building.ToBIM()

	// Check that all major sections are present
	expectedSections := []string{
		"# ArxOS Building Information Model",
		"# Building: B001",
		"# Name: Test Building",
		"# Address: 123 Test Street",
		"# Source: Test Import (TEST)",
		"## FLOORS",
		"FLOOR 1 \"Ground Floor\" 0.0",
		"## ROOMS",
		"ROOM 1/101 \"Conference Room\" conference 250.0",
		"## EQUIPMENT",
		"EQUIPMENT 1/101/AHU-01 \"Air Handler\" hvac operational",
	}

	for _, section := range expectedSections {
		if !strings.Contains(bim, section) {
			t.Errorf("ToBIM() missing expected section: %v", section)
		}
	}
}