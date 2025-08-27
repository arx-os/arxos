package ascii

import (
	"fmt"
)

// RenderExampleOffice creates a detailed office floor plan
func RenderExampleOffice() string {
	fb := NewFloorBuilder()
	
	// Create office rooms with realistic dimensions
	fb.Rooms = []Room{
		{
			Number: "101",
			Name:   "Reception",
			Bounds: Rectangle{X: 10, Y: 10, Width: 20, Height: 15},
			Walls: []Wall{
				{Start: Point{10, 10}, End: Point{30, 10}, Type: "exterior"},
				{Start: Point{10, 25}, End: Point{30, 25}, Type: "interior"},
				{Start: Point{10, 10}, End: Point{10, 25}, Type: "exterior"},
				{Start: Point{30, 10}, End: Point{30, 25}, Type: "interior"},
			},
			Doors: []Door{
				{Position: Point{20, 25}, Width: 6, Type: "double", SwingDir: "out", Wall: "south"},
			},
			Windows: []Window{
				{Position: Point{15, 10}, Width: 10, Type: "fixed", Wall: "north"},
			},
			Equipment: []Equipment{
				{Type: "outlet_duplex", Position: Point{12, 24}},
				{Type: "outlet_duplex", Position: Point{28, 24}},
				{Type: "switch_3way", Position: Point{22, 25}},
				{Type: "diffuser", Position: Point{20, 17}},
				{Type: "thermostat", Position: Point{29, 17}},
			},
		},
		{
			Number: "102",
			Name:   "Conference",
			Bounds: Rectangle{X: 30, Y: 10, Width: 25, Height: 15},
			Walls: []Wall{
				{Start: Point{30, 10}, End: Point{55, 10}, Type: "exterior"},
				{Start: Point{30, 25}, End: Point{55, 25}, Type: "interior"},
				{Start: Point{30, 10}, End: Point{30, 25}, Type: "interior"},
				{Start: Point{55, 10}, End: Point{55, 25}, Type: "interior"},
			},
			Doors: []Door{
				{Position: Point{32, 25}, Width: 3, Type: "single", SwingDir: "in", Wall: "south"},
			},
			Windows: []Window{
				{Position: Point{35, 10}, Width: 8, Type: "fixed", Wall: "north"},
				{Position: Point{45, 10}, Width: 8, Type: "fixed", Wall: "north"},
			},
			Equipment: []Equipment{
				{Type: "outlet_duplex", Position: Point{32, 24}},
				{Type: "outlet_duplex", Position: Point{42, 24}},
				{Type: "outlet_duplex", Position: Point{52, 24}},
				{Type: "data_outlet", Position: Point{42, 17}},
				{Type: "diffuser", Position: Point{42, 17}},
				{Type: "light_recessed", Position: Point{37, 17}},
				{Type: "light_recessed", Position: Point{47, 17}},
			},
		},
		{
			Number: "103",
			Name:   "Office",
			Bounds: Rectangle{X: 55, Y: 10, Width: 12, Height: 15},
			Walls: []Wall{
				{Start: Point{55, 10}, End: Point{67, 10}, Type: "exterior"},
				{Start: Point{55, 25}, End: Point{67, 25}, Type: "interior"},
				{Start: Point{55, 10}, End: Point{55, 25}, Type: "interior"},
				{Start: Point{67, 10}, End: Point{67, 25}, Type: "exterior"},
			},
			Doors: []Door{
				{Position: Point{57, 25}, Width: 3, Type: "single", SwingDir: "in", Wall: "south"},
			},
			Windows: []Window{
				{Position: Point{60, 10}, Width: 5, Type: "casement", Wall: "north"},
			},
			Equipment: []Equipment{
				{Type: "outlet_duplex", Position: Point{57, 24}},
				{Type: "outlet_duplex", Position: Point{65, 24}},
				{Type: "switch", Position: Point{58, 25}},
				{Type: "diffuser", Position: Point{61, 17}},
			},
		},
		{
			Number: "104",
			Name:   "Office",
			Bounds: Rectangle{X: 67, Y: 10, Width: 12, Height: 15},
			Walls: []Wall{
				{Start: Point{67, 10}, End: Point{79, 10}, Type: "exterior"},
				{Start: Point{67, 25}, End: Point{79, 25}, Type: "interior"},
				{Start: Point{67, 10}, End: Point{67, 25}, Type: "interior"},
				{Start: Point{79, 10}, End: Point{79, 25}, Type: "exterior"},
			},
			Doors: []Door{
				{Position: Point{69, 25}, Width: 3, Type: "single", SwingDir: "in", Wall: "south"},
			},
			Windows: []Window{
				{Position: Point{72, 10}, Width: 5, Type: "casement", Wall: "north"},
			},
			Equipment: []Equipment{
				{Type: "outlet_duplex", Position: Point{69, 24}},
				{Type: "outlet_duplex", Position: Point{77, 24}},
				{Type: "switch", Position: Point{70, 25}},
				{Type: "diffuser", Position: Point{73, 17}},
			},
		},
	}
	
	// Add main corridor
	fb.Corridors = []Corridor{
		{
			ID:     "main_corridor",
			Bounds: Rectangle{X: 10, Y: 25, Width: 69, Height: 6},
			Type:   "main",
		},
	}
	
	// Update wall types
	fb.updateWallTypes()
	
	// Render
	return fb.Render()
}

// RenderExampleElectricalRoom creates a detailed electrical room
func RenderExampleElectricalRoom() string {
	return `
╔════════════════════════════════════════════════════════════════════╗
║                    ELECTRICAL ROOM - DETAILED VIEW                 ║
╚════════════════════════════════════════════════════════════════════╝

╔═══════════════════════════════════════════════════════════════════╗
║                                                                   ║
║  ▣═══╦═══╦═══╦═══╗    ╔════════════════╗    ┌──────────┐       ║
║  ║ A ║ B ║ C ║ D ║    ║                ║    │          │       ║
║  ╠═══╬═══╬═══╬═══╣    ║   MAIN PANEL   ║    │   UPS    │       ║
║  ║ 1 ║ 1 ║ 1 ║ 1 ║    ║     MDF        ║    │  10kVA   │       ║
║  ║ 2 ║ 2 ║ 2 ║ 2 ║    ║   400A/208V    ║    │          │       ║
║  ║ 3 ║ 3 ║ 3 ║ 3 ║    ║                ║    └──────────┘       ║
║  ║ 4 ║ 4 ║ 4 ║ 4 ║    ╠════════════════╣                       ║
║  ╚═══╩═══╩═══╩═══╝    ║ [01] 20A  ⚡   ║    ┌──────────┐       ║
║   SUB-PANEL LP-1      ║ [02] 20A  ⚡   ║    │  XFMR-1  │       ║
║    120V/240V          ║ [03] 30A  ⚡   ║    │ 480/208V │       ║
║                       ║ [04] 30A  ⚡   ║    │  75kVA   │       ║
║  ┌─────────────┐      ║ [05] 50A  ⚡   ║    └──────────┘       ║
║  │   METER     │      ║ [06] 50A  ⚡   ║                       ║
║  │  ▥▥▥▥▥▥    │      ║ [07] 60A  ⚡   ║    ╔══════════╗       ║
║  │  ▥▥▥▥▥▥    │      ║ [08] 60A  ⚡   ║    ║ TRANSFER ║       ║
║  │   MAIN      │      ║ [09] 100A ⚡   ║    ║  SWITCH  ║       ║
║  └─────────────┘      ║ [10] 100A ⚡   ║    ╚══════════╝       ║
║                       ║ [11] 125A ⚡   ║                       ║
║  ⊙ ⊙ ⊙ ⊙             ║ [12] SPACE     ║    Ground Bar        ║
║  Maintenance          ╚════════════════╝    ═══════════        ║
║  Outlets                                                        ║
║                                                      ◦          ║
╚══════════════════════════════════════════════════════════╗ DOOR ║
                                                           ╚══════╝

LEGEND:
  ▣ Panel        ⚡ Active Breaker    ▥ Meter         ⊙ Outlet
  ═ Bus Bar      □ Junction Box      ◦ Door          ║ Wall
`
}

// RenderExampleMechanicalRoom creates a mechanical room layout
func RenderExampleMechanicalRoom() string {
	return `
╔════════════════════════════════════════════════════════════════════╗
║                   MECHANICAL ROOM - EQUIPMENT LAYOUT               ║
╚════════════════════════════════════════════════════════════════════╝

╔═════════════════════════════════════════════════════════════════════╗
║                                                                     ║
║   ╔═══════════════╗        ╔═══════════════════╗                  ║
║   ║               ║        ║                   ║                  ║
║   ║    AHU-1      ║═══════>║     AHU-2         ║                  ║
║   ║   10 TON      ║        ║     8 TON         ║                  ║
║   ║               ║        ║                   ║                  ║
║   ╚═══════╤═══════╝        ╚═══════╤═══════════╝                  ║
║           │                         │                              ║
║     Supply│Duct               Supply│Duct                         ║
║           ▼                         ▼                              ║
║    ┌─────────────────────────────────────────┐      ╔═══════╗    ║
║    │         MAIN SUPPLY DUCT HEADER         │      ║ CRAC  ║    ║
║    └──┬──────┬──────┬──────┬──────┬─────────┘      ║  5T   ║    ║
║       │      │      │      │      │                 ╚═══════╝    ║
║       ▼      ▼      ▼      ▼      ▼                              ║
║      VAV    VAV    VAV    VAV    VAV         ┌──────────────┐    ║
║      101    102    103    104    105         │   CHILLER    │    ║
║                                              │    CH-1      │    ║
║   ◎═══◎═══◎═══◎═══◎═══◎═══◎═══◎            │   50 TON    │    ║
║   Chilled Water Supply Loop                  └──────┬───────┘    ║
║                                                      │            ║
║   ◎───◎───◎───◎───◎───◎───◎───◎            ┌──────▼───────┐    ║
║   Chilled Water Return Loop                  │   CHW PUMP   │    ║
║                                              │    P-1       │    ║
║   ♨═══♨═══♨═══♨═══♨═══♨═══♨═══♨            │   10 HP      │    ║
║   Hot Water Supply Loop                      └──────────────┘    ║
║                                                                   ║
║   ┌────────────┐    ┌────────────┐    ┌────────────┐           ║
║   │  BOILER-1  │    │  BOILER-2  │    │ EXP TANK   │           ║
║   │   500MBH   │    │   500MBH   │    │            │     ◦     ║
║   └────────────┘    └────────────┘    └────────────┘    DOOR   ║
╚═════════════════════════════════════════════════════════════════╝

EQUIPMENT SCHEDULE:
  AHU-1: 208V/3PH/30A    VAV Boxes: 24VAC      Chiller: 480V/3PH/100A
  AHU-2: 208V/3PH/25A    Controls: BACnet/IP   Pumps: 208V/3PH/15A
`
}

// RenderDetailComparison shows the difference between detail levels
func RenderDetailComparison() string {
	comparison := fmt.Sprintf(`
╔════════════════════════════════════════════════════════════════════╗
║                    ASCII-BIM DETAIL LEVEL COMPARISON               ║
╚════════════════════════════════════════════════════════════════════╝

BASIC (Level 1) - Simple Lines:
┌─────────────┬─────────────┐
│    101      │    102      │
│             │             │
│      D      │      D      │
└─────────────┴─────────────┘

NORMAL (Level 2) - Wall Types & Basic Symbols:
╔═════════════╦═════════════╗
║    101      ║    102      ║
║      ⊙      ║      ⊙      ║
║      ◦      ║      ◦      ║
╚═════════════╩═════════════╝

DETAILED (Level 3) - Full Symbols & Dimensions:
╔═════════════════════╦═════════════════════╗
║  ROOM 101           ║  ROOM 102           ║
║  Reception          ║  Office             ║
║                     ║                     ║
║  ⊙──────────────⊙  ║  ⊙──────────────⊙  ║
║  Outlet      Outlet ║  Outlet      Outlet ║
║                     ║                     ║
║  ╬ Supply Diffuser  ║  ╬ Supply Diffuser  ║
║  ╪ Return Grille    ║                     ║
║                     ║  ◫ Thermostat       ║
║       ⌐◈            ║       ⌐◈            ║
║      Door  Switch   ║      Door  Switch   ║
╚═════════════════════╩═════════════════════╝
        15'-0"                15'-0"

ELECTRICAL SYMBOLS:        HVAC SYMBOLS:         PLUMBING:
⊙  Duplex Outlet          ╬  Supply Diffuser    ◎  Valve
⊕  GFCI Outlet           ╪  Return Grille      ◉  Drain
◈  Single Switch         ▢  VAV Box            ♨  Hot Water
◇  3-Way Switch          ◫  Thermostat         ≈  Cold Water
▣  Electrical Panel      ※  Exhaust Fan
☀  Light Fixture         ▦  Air Handler
○  Recessed Light
`)
	return comparison
}