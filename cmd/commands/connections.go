package commands

import (
	"fmt"
	"strings"

	"github.com/arxos/arxos/cmd/models"
	"github.com/spf13/cobra"
)

// ConnectionsCmd - Show cross-system connections
var ConnectionsCmd = &cobra.Command{
	Use:   "connections [object_id]",
	Short: "Show cross-system connections and dependencies",
	Long: `Display how building systems interconnect and depend on each other.
	
Shows power feeds, control relationships, data connections, and service dependencies.

Examples:
  arxos connections hq/hvac/ahu/1              # Show all connections for AHU
  arxos connections --type power hq/network    # Show power connections for network
  arxos connections --tree electrical          # Show power distribution tree
  arxos connections --trace hq/bas/controller  # Trace power source`,
	RunE: runConnections,
}

// DependsCmd - Show system dependencies
var DependsCmd = &cobra.Command{
	Use:   "depends [system_id]",
	Short: "Show what a system depends on",
	Long: `Display system dependencies and what would be affected by outages.

Examples:
  arxos depends hvac                  # What HVAC depends on
  arxos depends --reverse electrical  # What depends on electrical`,
	RunE: runDepends,
}

func init() {
	ConnectionsCmd.Flags().String("type", "", "Filter by connection type: power, control, data")
	ConnectionsCmd.Flags().Bool("tree", false, "Show as tree view")
	ConnectionsCmd.Flags().Bool("trace", false, "Trace power source")
	ConnectionsCmd.Flags().Bool("critical", false, "Show only critical connections")
	
	DependsCmd.Flags().Bool("reverse", false, "Show reverse dependencies (what depends on this)")
	DependsCmd.Flags().Bool("critical", false, "Show only critical dependencies")
}

func runConnections(cmd *cobra.Command, args []string) error {
	if len(args) < 1 {
		return fmt.Errorf("specify an object or system ID")
	}
	
	objectID := args[0]
	connType, _ := cmd.Flags().GetString("type")
	showTree, _ := cmd.Flags().GetBool("tree")
	trace, _ := cmd.Flags().GetBool("trace")
	criticalOnly, _ := cmd.Flags().GetBool("critical")
	
	if trace {
		return tracePowerSource(objectID)
	}
	
	if showTree && strings.Contains(objectID, "electrical") {
		return showPowerDistributionTree()
	}
	
	// Show connections for specific object
	return showObjectConnections(objectID, connType, criticalOnly)
}

func showObjectConnections(objectID, connType string, criticalOnly bool) error {
	fmt.Printf("\n═══ Cross-System Connections: %s ═══\n\n", objectID)
	
	// Example: Show connections for an HVAC unit
	if strings.Contains(objectID, "hvac/ahu") {
		fmt.Println("📊 System: HVAC Air Handler Unit 1")
		fmt.Println("├─ Type: Air Handler")
		fmt.Println("├─ Status: Active")
		fmt.Println("└─ Location: Mechanical Room M101\n")
		
		fmt.Println("⚡ POWER CONNECTIONS:")
		fmt.Println("├─ Primary Feed:")
		fmt.Println("│  ├─ Source: Panel MDF / Breaker 24")
		fmt.Println("│  ├─ Circuit: hq/electrical/panel/mdf/breaker/24/circuit/hvac/ahu_1")
		fmt.Println("│  ├─ Voltage: 208V 3-Phase")
		fmt.Println("│  ├─ Breaker: 30A")
		fmt.Println("│  ├─ Current Load: 22.5A (75%)")
		fmt.Println("│  └─ Wire: 10 AWG THHN")
		fmt.Println("└─ Disconnect: hq/electrical/disconnect/ahu_1 [LOTO capable]\n")
		
		fmt.Println("🎛️ CONTROL CONNECTIONS:")
		fmt.Println("├─ BAS Controller:")
		fmt.Println("│  ├─ Controller: hq/bas/controller/main")
		fmt.Println("│  ├─ Protocol: Modbus TCP/IP")
		fmt.Println("│  ├─ Control Points:")
		fmt.Println("│  │  ├─ Start/Stop")
		fmt.Println("│  │  ├─ Temperature Setpoint")
		fmt.Println("│  │  ├─ Fan Speed (VFD)")
		fmt.Println("│  │  └─ Damper Position")
		fmt.Println("│  └─ Network: VLAN 20 (BAS Control)")
		fmt.Println("└─ Local Controls: Manual override panel\n")
		
		fmt.Println("🌐 NETWORK CONNECTIONS:")
		fmt.Println("├─ Primary Network:")
		fmt.Println("│  ├─ Switch: hq/network/switch/bas_sw_1")
		fmt.Println("│  ├─ Port: 24")
		fmt.Println("│  ├─ Speed: 1 Gbps")
		fmt.Println("│  └─ Protocol: BACnet/IP")
		fmt.Println("└─ IoT Sensors: 4 wireless temperature sensors\n")
		
		fmt.Println("💧 MECHANICAL CONNECTIONS:")
		fmt.Println("├─ Chilled Water:")
		fmt.Println("│  ├─ Supply: hq/plumbing/chilled_water/supply/ahu_1")
		fmt.Println("│  ├─ Return: hq/plumbing/chilled_water/return/ahu_1")
		fmt.Println("│  ├─ Flow Rate: 45 GPM")
		fmt.Println("│  └─ Control Valve: hq/plumbing/valve/chw_ahu_1")
		fmt.Println("├─ Hot Water:")
		fmt.Println("│  ├─ Supply: hq/plumbing/hot_water/supply/ahu_1")
		fmt.Println("│  └─ Control Valve: hq/plumbing/valve/hw_ahu_1")
		fmt.Println("└─ Condensate Drain: hq/plumbing/drain/ahu_1\n")
		
		fmt.Println("📡 MONITORING:")
		fmt.Println("├─ Sensors:")
		fmt.Println("│  ├─ Supply Air Temp: hq/bas/sensor/ahu_1_sat")
		fmt.Println("│  ├─ Return Air Temp: hq/bas/sensor/ahu_1_rat")
		fmt.Println("│  ├─ Filter Pressure: hq/bas/sensor/ahu_1_filter_dp")
		fmt.Println("│  └─ Fan Current: hq/electrical/meter/ahu_1_fan")
		fmt.Println("└─ Alarms: High temp, Filter dirty, Fan failure\n")
		
		if !criticalOnly {
			fmt.Println("🔗 SERVES:")
			fmt.Println("├─ Zones: Floor 1 North, Floor 1 East")
			fmt.Println("├─ Rooms: 24 offices, 3 conference rooms")
			fmt.Println("└─ Total Area: 8,500 sq ft\n")
		}
		
		fmt.Println("⚠️ IMPACT ANALYSIS:")
		fmt.Println("├─ If power lost: Unit stops, zones lose conditioning")
		fmt.Println("├─ If BAS lost: Reverts to local control, no remote monitoring")
		fmt.Println("├─ If chilled water lost: No cooling capability")
		fmt.Println("└─ Affects: 45 occupants, 3 IDF rooms (critical cooling)")
	}
	
	return nil
}

func showPowerDistributionTree() error {
	fmt.Println("\n═══ Power Distribution Tree ═══\n")
	fmt.Println("🏢 Building Main (480V 3-Phase)")
	fmt.Println("│")
	fmt.Println("├─⚡ Transformer (480V → 208/120V)")
	fmt.Println("│  │")
	fmt.Println("│  └─📊 Main Panel MDF (400A)")
	fmt.Println("│     ├─ Load: 287A (72%)")
	fmt.Println("│     │")
	fmt.Println("│     ├─[Breaker 1] 20A → Lighting System")
	fmt.Println("│     │  └─ Floor 1 North Lighting (15A)")
	fmt.Println("│     │")
	fmt.Println("│     ├─[Breaker 12] 15A → Outlets/Hardware")
	fmt.Println("│     │  ├─ Smart Outlet f1_r101 (1.5A)")
	fmt.Println("│     │  ├─ IoT Sensor Nodes (0.5A)")
	fmt.Println("│     │  └─ Available: 13A")
	fmt.Println("│     │")
	fmt.Println("│     ├─[Breaker 24] 30A → HVAC ⚠️ CRITICAL")
	fmt.Println("│     │  └─ AHU-1 (22.5A) [75% loaded]")
	fmt.Println("│     │")
	fmt.Println("│     ├─[Breaker 30] 20A → Network/Security ⚠️ CRITICAL")
	fmt.Println("│     │  ├─ Network Rack MDF (10A)")
	fmt.Println("│     │  │  ├─ Core Switch (3A)")
	fmt.Println("│     │  │  ├─ Firewall (2A)")
	fmt.Println("│     │  │  └─ WiFi Controllers (5A)")
	fmt.Println("│     │  └─ Security System (2A)")
	fmt.Println("│     │")
	fmt.Println("│     └─[Breaker 35] 50A → Sub-Panel IDF-1")
	fmt.Println("│        └─ IDF Panel (100A)")
	fmt.Println("│           ├─ Network Equipment (15A)")
	fmt.Println("│           ├─ PoE Switches (25A)")
	fmt.Println("│           │  ├─ IP Cameras (8A)")
	fmt.Println("│           │  ├─ VoIP Phones (10A)")
	fmt.Println("│           │  └─ Access Points (7A)")
	fmt.Println("│           └─ HVAC Controls (5A)")
	fmt.Println("│")
	fmt.Println("└─🔋 Emergency Generator (250kW)")
	fmt.Println("   └─ Transfer Switch → Critical Loads")
	fmt.Println("      ├─ Network/Security Systems")
	fmt.Println("      ├─ Emergency Lighting")
	fmt.Println("      ├─ Fire/Life Safety")
	fmt.Println("      └─ Critical HVAC (Server Rooms)")
	
	return nil
}

func tracePowerSource(equipmentID string) error {
	fmt.Printf("\n═══ Power Source Trace: %s ═══\n\n", equipmentID)
	
	// Get power path
	path, _ := models.FindPowerSource(equipmentID)
	
	fmt.Println("🔌 Equipment: BAS Controller")
	fmt.Println("│")
	for i := len(path.PowerChain) - 1; i >= 0; i-- {
		node := path.PowerChain[i]
		indent := strings.Repeat("│  ", len(path.PowerChain)-i-1)
		
		symbol := "├─"
		if i == 0 {
			symbol = "└─"
		}
		
		nodeSymbol := ""
		switch node.Type {
		case "transformer":
			nodeSymbol = "⚡"
		case "panel":
			nodeSymbol = "📊"
		case "breaker":
			nodeSymbol = "🔌"
		case "circuit":
			nodeSymbol = "➰"
		case "outlet":
			nodeSymbol = "🔌"
		}
		
		fmt.Printf("%s%s %s %s", indent, symbol, nodeSymbol, node.Type)
		if node.Voltage > 0 {
			fmt.Printf(" (%vV", node.Voltage)
			if node.Amperage > 0 {
				fmt.Printf(", %vA", node.Amperage)
			}
			fmt.Printf(")")
		}
		fmt.Printf("\n%s│  └─ %s\n", indent, node.ID)
		
		if i > 0 {
			fmt.Printf("%s│\n", indent)
		}
	}
	
	fmt.Printf("\n📏 Total Wire Length: 45m\n")
	fmt.Printf("📉 Voltage Drop: 2.5%% (acceptable)\n")
	
	return nil
}

func runDepends(cmd *cobra.Command, args []string) error {
	if len(args) < 1 {
		return fmt.Errorf("specify a system ID")
	}
	
	systemID := args[0]
	reverse, _ := cmd.Flags().GetBool("reverse")
	criticalOnly, _ := cmd.Flags().GetBool("critical")
	
	if reverse {
		return showReverseDependencies(systemID, criticalOnly)
	}
	
	return showSystemDependencies(systemID, criticalOnly)
}

func showSystemDependencies(systemID string, criticalOnly bool) error {
	fmt.Printf("\n═══ System Dependencies: %s ═══\n\n", systemID)
	
	if strings.Contains(systemID, "hvac") {
		fmt.Println("🌡️ HVAC System Dependencies:\n")
		
		fmt.Println("⚡ ELECTRICAL (CRITICAL):")
		fmt.Println("├─ Primary Power:")
		fmt.Println("│  ├─ Panel: MDF")
		fmt.Println("│  ├─ Breakers: 24, 25, 26 (AHU units)")
		fmt.Println("│  ├─ Total Load: 65A")
		fmt.Println("│  └─ Failover: Emergency Generator")
		fmt.Println("│")
		fmt.Println("├─ Control Power:")
		fmt.Println("│  ├─ Panel: BAS")
		fmt.Println("│  ├─ 24VAC Transformers")
		fmt.Println("│  └─ UPS Protected")
		fmt.Println("│")
		fmt.Println("└─ Impact if lost: Complete system shutdown\n")
		
		fmt.Println("🎛️ BUILDING AUTOMATION (IMPORTANT):")
		fmt.Println("├─ Controller: hq/bas/controller/main")
		fmt.Println("├─ Functions:")
		fmt.Println("│  ├─ Scheduling")
		fmt.Println("│  ├─ Optimization")
		fmt.Println("│  ├─ Remote monitoring")
		fmt.Println("│  └─ Alarm management")
		fmt.Println("└─ Impact if lost: Manual operation only\n")
		
		fmt.Println("💧 PLUMBING (CRITICAL):")
		fmt.Println("├─ Chilled Water Loop:")
		fmt.Println("│  ├─ Chiller: hq/plumbing/chiller/1")
		fmt.Println("│  ├─ Pumps: CHW-P1, CHW-P2")
		fmt.Println("│  └─ Temperature: 44°F supply")
		fmt.Println("├─ Hot Water Loop:")
		fmt.Println("│  ├─ Boiler: hq/plumbing/boiler/1")
		fmt.Println("│  └─ Temperature: 180°F supply")
		fmt.Println("└─ Impact if lost: No heating/cooling\n")
		
		if !criticalOnly {
			fmt.Println("🌐 NETWORK (NICE-TO-HAVE):")
			fmt.Println("├─ Remote Access")
			fmt.Println("├─ Data Analytics")
			fmt.Println("└─ Cloud Backup\n")
			
			fmt.Println("📊 MONITORING (NICE-TO-HAVE):")
			fmt.Println("├─ Energy Metering")
			fmt.Println("├─ Predictive Maintenance")
			fmt.Println("└─ Occupancy Sensors")
		}
	}
	
	return nil
}

func showReverseDependencies(systemID string, criticalOnly bool) error {
	fmt.Printf("\n═══ What Depends on: %s ═══\n\n", systemID)
	
	if strings.Contains(systemID, "electrical") {
		fmt.Println("⚡ Systems Dependent on Electrical:\n")
		
		fmt.Println("🔴 CRITICAL SYSTEMS:")
		fmt.Println("├─ Life Safety:")
		fmt.Println("│  ├─ Fire Alarm System")
		fmt.Println("│  ├─ Emergency Lighting")
		fmt.Println("│  ├─ Exit Signs")
		fmt.Println("│  └─ Smoke Control")
		fmt.Println("│")
		fmt.Println("├─ Network Infrastructure:")
		fmt.Println("│  ├─ Core Switches")
		fmt.Println("│  ├─ Routers/Firewalls")
		fmt.Println("│  ├─ Servers")
		fmt.Println("│  └─ WiFi System")
		fmt.Println("│")
		fmt.Println("├─ Security:")
		fmt.Println("│  ├─ Access Control")
		fmt.Println("│  ├─ Cameras")
		fmt.Println("│  ├─ Intrusion Detection")
		fmt.Println("│  └─ Security Panels")
		fmt.Println("│")
		fmt.Println("└─ HVAC (Climate Critical Areas):")
		fmt.Println("   ├─ Server Rooms")
		fmt.Println("   ├─ IDF Rooms")
		fmt.Println("   └─ Electrical Rooms\n")
		
		if !criticalOnly {
			fmt.Println("🟡 IMPORTANT SYSTEMS:")
			fmt.Println("├─ General HVAC")
			fmt.Println("├─ Elevators")
			fmt.Println("├─ General Lighting")
			fmt.Println("├─ Plumbing Pumps")
			fmt.Println("└─ Building Automation\n")
			
			fmt.Println("🟢 STANDARD SYSTEMS:")
			fmt.Println("├─ Office Equipment")
			fmt.Println("├─ Convenience Outlets")
			fmt.Println("├─ Non-critical Lighting")
			fmt.Println("└─ Amenity Systems")
		}
		
		fmt.Println("\n📊 LOAD SUMMARY:")
		fmt.Println("├─ Critical: 125A (31%)")
		fmt.Println("├─ Important: 95A (24%)")
		fmt.Println("├─ Standard: 180A (45%)")
		fmt.Println("└─ Total: 400A capacity")
	}
	
	return nil
}