package main

import (
	"fmt"
	"github.com/arxos/arxos/cmd/ascii"
)

// DemoAlafiaES creates a demonstration of Alafia ES IDF room
func DemoAlafiaES() {
	fmt.Println("\n╔════════════════════════════════════════════════════════════════════════╗")
	fmt.Println("║                    ALAFIA ELEMENTARY SCHOOL - IDF ROOM                 ║")
	fmt.Println("╚════════════════════════════════════════════════════════════════════════╝\n")
	
	// Create the IDF room layout
	fb := ascii.NewFloorBuilder()
	
	// IDF room with network racks
	idfRoom := ascii.Room{
		Number: "IDF-1",
		Name:   "IDF Room",
		Bounds: ascii.Rectangle{X: 10, Y: 10, Width: 20, Height: 15},
		Walls: []ascii.Wall{
			{Start: ascii.Point{10, 10}, End: ascii.Point{30, 10}, Type: "exterior"},
			{Start: ascii.Point{10, 25}, End: ascii.Point{30, 25}, Type: "exterior"},
			{Start: ascii.Point{10, 10}, End: ascii.Point{10, 25}, Type: "exterior"},
			{Start: ascii.Point{30, 10}, End: ascii.Point{30, 25}, Type: "exterior"},
		},
		Doors: []ascii.Door{
			{Position: ascii.Point{15, 25}, Width: 3, Type: "single", SwingDir: "out", Wall: "south"},
		},
		Equipment: []ascii.Equipment{
			// Network Racks
			{Type: "rack", Position: ascii.Point{12, 15}, ID: "RACK-1"},
			{Type: "rack", Position: ascii.Point{18, 15}, ID: "RACK-2"},
			{Type: "rack", Position: ascii.Point{24, 15}, ID: "RACK-3"},
			
			// Electrical
			{Type: "panel", Position: ascii.Point{28, 12}, ID: "IDF-PANEL"},
			{Type: "outlet_duplex", Position: ascii.Point{12, 24}},
			{Type: "outlet_duplex", Position: ascii.Point{18, 24}},
			{Type: "outlet_duplex", Position: ascii.Point{24, 24}},
			
			// HVAC
			{Type: "diffuser", Position: ascii.Point{20, 17}},
			{Type: "thermostat", Position: ascii.Point{29, 20}},
			
			// Emergency
			{Type: "exit_sign", Position: ascii.Point{15, 24}},
		},
	}
	
	fb.Rooms = []ascii.Room{idfRoom}
	fb.Renderer.DetailLevel = 3
	
	// Render the floor plan
	fmt.Println(fb.Render())
	
	// Show electrical distribution
	fmt.Println("\n═══ ELECTRICAL DISTRIBUTION ═══\n")
	fmt.Println("🏢 Building Main Service")
	fmt.Println("│")
	fmt.Println("├─⚡ Main Distribution Panel (MDP)")
	fmt.Println("│   480V 3-Phase → 208V/120V")
	fmt.Println("│")
	fmt.Println("└─🔌 Panel IDF-1 (Fed from MDP)")
	fmt.Println("    ├─ [1-3] Network Rack 1 (20A)")
	fmt.Println("    │   └─ Switches, Routers, Patch Panels")
	fmt.Println("    ├─ [4-6] Network Rack 2 (20A)")
	fmt.Println("    │   └─ PoE Switches for Cameras/Phones")
	fmt.Println("    ├─ [7-9] Network Rack 3 (20A)")
	fmt.Println("    │   └─ Servers, NAS Storage")
	fmt.Println("    ├─ [10] HVAC Controls (15A)")
	fmt.Println("    ├─ [11] Emergency Lighting (10A)")
	fmt.Println("    └─ [12] Convenience Outlets (20A)")
	
	// Show network topology
	fmt.Println("\n═══ NETWORK TOPOLOGY ═══\n")
	fmt.Println("RACK-1 (Core Network)")
	fmt.Println("├─ Core Switch (48-port)")
	fmt.Println("│  ├─ Uplink to District WAN")
	fmt.Println("│  ├─ Trunk to RACK-2")
	fmt.Println("│  └─ Trunk to RACK-3")
	fmt.Println("├─ Firewall")
	fmt.Println("└─ UPS (2000VA)")
	fmt.Println("")
	fmt.Println("RACK-2 (PoE Distribution)")
	fmt.Println("├─ PoE Switch 1 (24-port)")
	fmt.Println("│  └─ Classroom APs & Cameras")
	fmt.Println("├─ PoE Switch 2 (24-port)")
	fmt.Println("│  └─ VoIP Phones")
	fmt.Println("└─ Patch Panel (48-port)")
	fmt.Println("")
	fmt.Println("RACK-3 (Servers)")
	fmt.Println("├─ Domain Controller")
	fmt.Println("├─ File Server")
	fmt.Println("├─ Security NVR")
	fmt.Println("└─ Backup NAS")
	
	// Show cross-system connections
	fmt.Println("\n═══ CROSS-SYSTEM CONNECTIONS ═══\n")
	fmt.Println("⚡ POWER → 🌐 NETWORK:")
	fmt.Println("  Panel IDF-1 → Breakers 1-9 → Network Racks")
	fmt.Println("  Critical circuits on UPS backup")
	fmt.Println("")
	fmt.Println("🌐 NETWORK → 📹 SECURITY:")
	fmt.Println("  PoE Switches → IP Cameras (30W per camera)")
	fmt.Println("  Network → NVR for recording")
	fmt.Println("")
	fmt.Println("🌡️ HVAC → 🌐 NETWORK:")
	fmt.Println("  Cooling required: 3 tons")
	fmt.Println("  Temperature monitoring via BMS")
	fmt.Println("  Critical temp alarm at 85°F")
}

// Run the demo
func init() {
	// This would be called from a command
	// DemoAlafiaES()
}