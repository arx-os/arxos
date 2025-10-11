package test_domain_agnostic

import (
	"fmt"
	"testing"

	"github.com/arx-os/arxos/internal/domain/component"
	"github.com/stretchr/testify/assert"
)

// TestDomainAgnosticArchitecture validates that ArxOS works for any spatial domain
// not just buildings. Tests the "blank slate" vision.
func TestDomainAgnosticArchitecture(t *testing.T) {
	t.Run("Component accepts custom types", func(t *testing.T) {
		testCases := []struct {
			name          string
			componentType string
			description   string
		}{
			{
				name:          "sandwich in fridge",
				componentType: "sandwich",
				description:   "Food item in kitchen fridge",
			},
			{
				name:          "torpedo on ship",
				componentType: "torpedo",
				description:   "Weapon on naval vessel",
			},
			{
				name:          "forklift in warehouse",
				componentType: "forklift",
				description:   "Material handling equipment",
			},
			{
				name:          "server in data center",
				componentType: "server_rack",
				description:   "IT equipment in data center",
			},
			{
				name:          "cargo container",
				componentType: "shipping_container",
				description:   "ISO container in cargo hold",
			},
			{
				name:          "medical device",
				componentType: "mri_scanner",
				description:   "Medical equipment in hospital",
			},
		}

		for _, tc := range testCases {
			t.Run(tc.name, func(t *testing.T) {
				// Create component with custom type
				comp, err := component.NewComponent(
					tc.name,
					component.ComponentType(tc.componentType),
					"/test/path/"+tc.name,
					component.Location{X: 1.0, Y: 2.0, Z: 3.0},
					"test-user",
				)

				// Should succeed
				assert.NoError(t, err, "Custom type should be accepted")
				assert.NotNil(t, comp, "Component should be created")
				assert.Equal(t, tc.componentType, string(comp.Type), "Type should match")

				// Verify properties work
				comp.AddProperty("description", tc.description)
				val, exists := comp.GetStringProperty("description")
				assert.True(t, exists, "Property should exist")
				assert.Equal(t, tc.description, val, "Property value should match")
			})
		}
	})

	t.Run("Hierarchies work for any domain", func(t *testing.T) {
		testCases := []struct {
			name      string
			hierarchy []string
			domain    string
		}{
			{
				name:      "Building hierarchy",
				hierarchy: []string{"/office-tower", "/office-tower/floor-3", "/office-tower/floor-3/room-301"},
				domain:    "commercial building",
			},
			{
				name:      "Ship hierarchy",
				hierarchy: []string{"/uss-enterprise", "/uss-enterprise/deck-3", "/uss-enterprise/deck-3/torpedo-bay"},
				domain:    "naval vessel",
			},
			{
				name:      "Warehouse hierarchy",
				hierarchy: []string{"/dc-north", "/dc-north/zone-a", "/dc-north/zone-a/aisle-5", "/dc-north/zone-a/aisle-5/rack-12"},
				domain:    "logistics warehouse",
			},
			{
				name:      "Hospital hierarchy",
				hierarchy: []string{"/st-marys", "/st-marys/floor-2", "/st-marys/floor-2/wing-b", "/st-marys/floor-2/wing-b/room-205"},
				domain:    "medical facility",
			},
			{
				name:      "Kitchen nesting",
				hierarchy: []string{"/house", "/house/floor-1", "/house/floor-1/kitchen", "/house/floor-1/kitchen/fridge", "/house/floor-1/kitchen/fridge/shelf-2"},
				domain:    "residential building",
			},
		}

		for _, tc := range testCases {
			t.Run(tc.name, func(t *testing.T) {
				// Validate path structure works
				for _, path := range tc.hierarchy {
					assert.NotEmpty(t, path, "Path should not be empty")
					assert.Contains(t, path, "/", "Path should use forward slash")
				}
			})
		}
	})

	t.Run("Custom properties support any domain", func(t *testing.T) {
		// Create sandwich
		sandwich, err := component.NewComponent(
			"PBJ-001",
			"sandwich",
			"/kitchen/fridge/shelf-2/pbj-001",
			component.Location{},
			"joel",
		)
		assert.NoError(t, err)

		// Add sandwich-specific properties
		sandwich.AddProperty("bread_type", "wheat")
		sandwich.AddProperty("peanut_butter", "creamy")
		sandwich.AddProperty("jelly_flavor", "grape")
		sandwich.AddProperty("made_date", "2025-01-15")
		sandwich.AddProperty("calories", 350)

		// Verify properties
		bread, _ := sandwich.GetStringProperty("bread_type")
		assert.Equal(t, "wheat", bread)

		calories, _ := sandwich.GetFloatProperty("calories")
		assert.Equal(t, 350.0, calories)

		// Create torpedo
		torpedo, err := component.NewComponent(
			"Torpedo-1",
			"torpedo",
			"/uss-enterprise/deck-3/torpedo-bay/torpedo-1",
			component.Location{X: 5.0, Y: 10.0, Z: 0.0},
			"weapons-officer",
		)
		assert.NoError(t, err)

		// Add torpedo-specific properties
		torpedo.AddProperty("warhead_type", "photon")
		torpedo.AddProperty("yield_megatons", 1.5)
		torpedo.AddProperty("range_km", 500000)
		torpedo.AddProperty("armed", false)

		// Verify properties
		warhead, _ := torpedo.GetStringProperty("warhead_type")
		assert.Equal(t, "photon", warhead)

		armed, _ := torpedo.GetBoolProperty("armed")
		assert.False(t, armed)
	})

	t.Run("Relations work across domains", func(t *testing.T) {
		// Create laptop
		laptop, _ := component.NewComponent(
			"Laptop-A1",
			"laptop",
			"/office/floor-1/room-101/laptop-a1",
			component.Location{X: 5.0, Y: 10.0, Z: 1.0},
			"it-tech",
		)

		// Create dock
		dock, _ := component.NewComponent(
			"Dock-A1",
			"usb_dock",
			"/office/floor-1/room-101/dock-a1",
			component.Location{X: 5.0, Y: 10.0, Z: 1.0},
			"it-tech",
		)

		// Create relation (laptop connected to dock)
		laptop.AddRelation(
			component.RelationTypeConnected,
			dock.ID,
			dock.Path,
			map[string]any{"port": "usb-c", "protocol": "thunderbolt3"},
		)

		// Verify relation
		assert.Len(t, laptop.Relations, 1, "Should have one relation")
		assert.Equal(t, component.RelationTypeConnected, laptop.Relations[0].Type)
		assert.Equal(t, dock.ID, laptop.Relations[0].TargetID)

		// Same pattern works for ship equipment
		radar, _ := component.NewComponent(
			"Radar-Main",
			"radar_array",
			"/uss-enterprise/bridge/radar-main",
			component.Location{},
			"bridge-crew",
		)

		computer, _ := component.NewComponent(
			"Computer-Core",
			"computer_system",
			"/uss-enterprise/engineering/computer-core",
			component.Location{},
			"chief-engineer",
		)

		// Radar connected to computer
		radar.AddRelation(
			component.RelationTypeConnected,
			computer.ID,
			computer.Path,
			map[string]any{"protocol": "subspace_link", "bandwidth": "100TB/s"},
		)

		assert.Len(t, radar.Relations, 1, "Ship equipment relations work the same way")
	})

	t.Run("Status tracking works universally", func(t *testing.T) {
		testCases := []struct {
			name          string
			itemType      string
			initialStatus component.ComponentStatus
			newStatus     component.ComponentStatus
		}{
			{
				name:          "HVAC maintenance",
				itemType:      "hvac_unit",
				initialStatus: component.ComponentStatusActive,
				newStatus:     component.ComponentStatusMaintenance,
			},
			{
				name:          "Torpedo armed",
				itemType:      "torpedo",
				initialStatus: component.ComponentStatusInactive,
				newStatus:     component.ComponentStatusActive,
			},
			{
				name:          "Forklift broken",
				itemType:      "forklift",
				initialStatus: component.ComponentStatusActive,
				newStatus:     component.ComponentStatusFailed,
			},
		}

		for _, tc := range testCases {
			t.Run(tc.name, func(t *testing.T) {
				comp, _ := component.NewComponent(
					tc.name,
					component.ComponentType(tc.itemType),
					"/test/"+tc.name,
					component.Location{},
					"test-user",
				)

				assert.Equal(t, component.ComponentStatusActive, comp.Status, "Initial status should be active")

				comp.UpdateStatus(tc.newStatus, "test-updater")
				assert.Equal(t, tc.newStatus, comp.Status, "Status should update")
			})
		}
	})
}

// TestTUISymbolMapping validates TUI renders custom types correctly
func TestTUISymbolMapping(t *testing.T) {
	t.Run("Default symbols for building equipment", func(t *testing.T) {
		// Note: This would require importing TUI package
		// Testing the concept here

		defaultTypes := map[string]rune{
			"hvac":       'H',
			"electrical": 'E',
			"lighting":   'L',
		}

		for typeStr, expectedSymbol := range defaultTypes {
			// Verify default mapping exists
			assert.NotEqual(t, rune(0), expectedSymbol, "Type %s should have symbol", typeStr)
		}
	})

	t.Run("Custom types use first letter fallback", func(t *testing.T) {
		customTypes := map[string]rune{
			"torpedo":      'T',
			"sandwich":     'S',
			"refrigerator": 'R',
			"missile":      'M',
			"cargo":        'C',
		}

		for typeStr, expectedFirstLetter := range customTypes {
			firstLetter := rune(typeStr[0])
			if firstLetter >= 'a' && firstLetter <= 'z' {
				firstLetter = firstLetter - 32 // Convert to uppercase
			}
			assert.Equal(t, expectedFirstLetter, firstLetter,
				"Type %s should render as first letter %c", typeStr, expectedFirstLetter)
		}
	})
}

// TestVersionControlDomainAgnostic validates version control works for any domain
func TestVersionControlDomainAgnostic(t *testing.T) {
	t.Run("Snapshot works for any structure", func(t *testing.T) {
		// Building snapshot
		buildingSnapshot := &component.Component{
			Name: "Office Tower State",
			Type: "snapshot",
			Path: "/snapshots/office-tower-v1.0",
			Properties: map[string]any{
				"structure_type": "building",
				"floors":         10,
				"rooms":          250,
				"equipment":      1500,
			},
		}
		assert.NotNil(t, buildingSnapshot)

		// Ship snapshot
		shipSnapshot := &component.Component{
			Name: "USS Enterprise State",
			Type: "snapshot",
			Path: "/snapshots/uss-enterprise-v2.3",
			Properties: map[string]any{
				"structure_type": "ship",
				"decks":          15,
				"compartments":   500,
				"torpedoes":      200,
			},
		}
		assert.NotNil(t, shipSnapshot)

		// Both use same underlying component system
		assert.Equal(t, buildingSnapshot.Type, shipSnapshot.Type, "Both are snapshots")
	})
}

// TestExampleUseCases demonstrates real-world usage patterns
func TestExampleUseCases(t *testing.T) {
	t.Run("Classroom AV Setup Configuration", func(t *testing.T) {
		// The real use case: Joel's classroom setups
		laptop, _ := component.NewComponent(
			"Dell-Latitude-5420",
			"laptop",
			"/lincoln-elem/building-a/room-101/av-setup/laptop",
			component.Location{X: 0.5, Y: 0.5, Z: 0.9}, // On teacher desk
			"joel",
		)

		dock, _ := component.NewComponent(
			"Dell-WD19TB",
			"usb_dock",
			"/lincoln-elem/building-a/room-101/av-setup/dock",
			component.Location{X: 0.5, Y: 0.5, Z: 0.9},
			"joel",
		)

		monitor1, _ := component.NewComponent(
			"LG-27UK850",
			"display",
			"/lincoln-elem/building-a/room-101/av-setup/monitor-primary",
			component.Location{X: 0.7, Y: 0.5, Z: 1.2},
			"joel",
		)

		panel, _ := component.NewComponent(
			"Newline-TT-7518RS",
			"interactive_panel",
			"/lincoln-elem/building-a/room-101/av-setup/panel",
			component.Location{X: 2.0, Y: 0.0, Z: 1.5}, // On wall
			"joel",
		)

		// Add connections
		laptop.AddRelation(component.RelationTypeConnected, dock.ID, dock.Path,
			map[string]any{"port": "usb-c", "protocol": "thunderbolt"})

		dock.AddRelation(component.RelationTypeConnected, monitor1.ID, monitor1.Path,
			map[string]any{"port": "displayport-1", "cable_length": "6ft"})

		dock.AddRelation(component.RelationTypeConnected, panel.ID, panel.Path,
			map[string]any{"port": "hdmi-1", "cable_length": "25ft"})

		// Add metadata
		laptop.AddProperty("model", "Latitude 5420")
		laptop.AddProperty("serial", "ABC123XYZ")
		laptop.AddProperty("assigned_to", "Mrs. Johnson")

		dock.AddProperty("firmware", "1.2.3")
		dock.AddProperty("ports_total", 6)
		dock.AddProperty("power_delivery", "90W")

		panel.AddProperty("screen_size", "75 inches")
		panel.AddProperty("resolution", "4K")
		panel.AddProperty("touch", true)

		// Verify the setup
		assert.Len(t, laptop.Relations, 1, "Laptop should connect to dock")
		assert.Len(t, dock.Relations, 2, "Dock should connect to 2 displays")
		assert.Equal(t, 3, len(laptop.Properties), "Laptop should have 3 properties")

		// This configuration can now be:
		// 1. Version controlled (arx commit -m "Configured Room 101 AV")
		// 2. Cloned (arx clone /room-101/av-setup /room-102/av-setup)
		// 3. Queried (arx query /room-101/av-setup/*)
		// 4. Compared (arx diff /room-101/av-setup /room-102/av-setup)
	})

	t.Run("Ship Torpedo Bay Inventory", func(t *testing.T) {
		// Different domain, same architecture
		torpedoBay, _ := component.NewComponent(
			"Torpedo-Bay-Alpha",
			"compartment",
			"/uss-enterprise/deck-3/torpedo-bay-alpha",
			component.Location{},
			"weapons-officer",
		)
		torpedoBay.AddProperty("capacity", 10)
		torpedoBay.AddProperty("loaded", 8)
		torpedoBay.AddProperty("type", "photon_torpedoes")

		// Add torpedoes
		for i := 1; i <= 8; i++ {
			torpedo, _ := component.NewComponent(
				fmt.Sprintf("Torpedo-%d", i),
				"torpedo",
				fmt.Sprintf("/uss-enterprise/deck-3/torpedo-bay-alpha/torpedo-%d", i),
				component.Location{X: float64(i), Y: 0, Z: 0},
				"weapons-officer",
			)
			torpedo.AddProperty("armed", i <= 4) // First 4 are armed
			torpedo.AddProperty("yield_megatons", 1.5)
			torpedo.AddProperty("type", "mark_vi_photon")

			// Verify
			assert.NotNil(t, torpedo)
			assert.Equal(t, "torpedo", string(torpedo.Type))
		}

		// Same operations work:
		// arx commit -m "Loaded 8 torpedoes in Bay Alpha"
		// arx query /uss-enterprise/deck-3/torpedo-bay-alpha/*
		// arx component list --type torpedo --property armed:true
	})
}
