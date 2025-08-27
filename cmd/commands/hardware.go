package commands

import (
	"fmt"
	"strings"

	"github.com/arxos/arxos/cmd/models"
	"github.com/spf13/cobra"
)

// HardwareCmd - Hardware and DfM commands
var HardwareCmd = &cobra.Command{
	Use:   "hardware [command]",
	Short: "Hardware design and manufacturing commands",
	Long: `Interact with hardware components, PCBs, and Design for Manufacturing (DfM).
	
Subcommands:
  trace     - Trace electrical path from building to component pin
  bom       - Generate Bill of Materials for device
  pcb       - PCB design and validation
  component - Component management
  test      - Generate test points for hardware validation`,
}

// TraceCmd traces electrical path to hardware level
var TraceCmd = &cobra.Command{
	Use:   "trace [component_id]",
	Short: "Trace electrical path from building to component pin",
	Long: `Shows full electrical traceability from building power distribution
down to individual component pins on PCBs.

Example:
  arxos hardware trace hq/electrical/outlet/f1_r101_north_1/hardware/pcb/main/component/u1/pin/5`,
	RunE: runTrace,
}

// BOMCmd generates bill of materials
var BOMCmd = &cobra.Command{
	Use:   "bom [device_id]",
	Short: "Generate Bill of Materials for device",
	Long: `Generate a complete BOM including PCB components, mechanical parts,
wiring, and assembly materials.

Options:
  --format  Output format: table, csv, json (default: table)
  --cost    Include cost estimation
  --stock   Check component availability`,
	RunE: runBOM,
}

// PCBCmd - PCB design commands
var PCBCmd = &cobra.Command{
	Use:   "pcb [command]",
	Short: "PCB design and validation",
	Long: `PCB design tools including DRC checks, layer stackup,
and manufacturing file generation.

Subcommands:
  validate  - Run Design Rule Checks (DRC)
  stackup   - Show PCB layer stackup
  generate  - Generate manufacturing files (Gerbers, etc.)`,
}

// ComponentCmd - Component management
var ComponentCmd = &cobra.Command{
	Use:   "component [command]",
	Short: "Component management and library",
	Long: `Manage hardware components and component library.

Subcommands:
  add      - Add component to library
  search   - Search component library
  specs    - Show component specifications
  cross    - Find cross-reference alternatives`,
}

func init() {
	// Add subcommands
	HardwareCmd.AddCommand(TraceCmd)
	HardwareCmd.AddCommand(BOMCmd)
	HardwareCmd.AddCommand(PCBCmd)
	HardwareCmd.AddCommand(ComponentCmd)
	
	// Add flags
	BOMCmd.Flags().String("format", "table", "Output format: table, csv, json")
	BOMCmd.Flags().Bool("cost", false, "Include cost estimation")
	BOMCmd.Flags().Bool("stock", false, "Check component availability")
	
	TraceCmd.Flags().Bool("verbose", false, "Show detailed trace information")
	TraceCmd.Flags().Bool("visual", false, "ASCII visualization of path")
}

func runTrace(cmd *cobra.Command, args []string) error {
	if len(args) < 1 {
		return fmt.Errorf("specify component ID to trace")
	}
	
	componentID := args[0]
	verbose, _ := cmd.Flags().GetBool("verbose")
	visual, _ := cmd.Flags().GetBool("visual")
	
	// Get hardware traceability
	trace, err := models.GetHardwareTraceability(componentID)
	if err != nil {
		return err
	}
	
	fmt.Println("\n═══ Hardware Electrical Trace ═══\n")
	
	// Show building-level path
	fmt.Println("📏 Building Distribution:")
	fmt.Printf("  Transformer → Meter → Panel → Breaker → Circuit\n")
	fmt.Printf("  %s\n\n", trace.DeviceID)
	
	// Show device info
	fmt.Println("🔌 Device:")
	fmt.Printf("  Type: %s\n", extractType(trace.DeviceID))
	fmt.Printf("  Location: %s\n", extractLocation(trace.DeviceID))
	fmt.Printf("  ID: %s\n\n", trace.DeviceID)
	
	// Show hardware path
	if len(trace.HardwarePath) > 0 {
		fmt.Println("🔧 Hardware Path:")
		indent := "  "
		for i, part := range trace.HardwarePath {
			if i > 0 && i%2 == 0 {
				indent += "  "
			}
			fmt.Printf("%s└─ %s\n", indent, part)
		}
	}
	
	if visual {
		showVisualTrace(trace)
	}
	
	if verbose {
		showDetailedTrace(trace)
	}
	
	return nil
}

func runBOM(cmd *cobra.Command, args []string) error {
	if len(args) < 1 {
		return fmt.Errorf("specify device ID")
	}
	
	deviceID := args[0]
	format, _ := cmd.Flags().GetString("format")
	showCost, _ := cmd.Flags().GetBool("cost")
	checkStock, _ := cmd.Flags().GetBool("stock")
	
	// Generate sample BOM (would query actual data)
	bom := generateSampleBOM(deviceID)
	
	switch format {
	case "table":
		printBOMTable(bom, showCost, checkStock)
	case "csv":
		printBOMCSV(bom)
	case "json":
		printBOMJSON(bom)
	default:
		printBOMTable(bom, showCost, checkStock)
	}
	
	return nil
}

func showVisualTrace(trace *models.HardwareTraceability) {
	fmt.Println("\n📊 Visual Trace:\n")
	fmt.Println("┌─────────────────┐")
	fmt.Println("│   🏢 Building   │")
	fmt.Println("└────────┬────────┘")
	fmt.Println("         │")
	fmt.Println("    ⚡ Electrical")
	fmt.Println("         │")
	fmt.Println("┌────────▼────────┐")
	fmt.Println("│   Panel: MDF    │")
	fmt.Println("└────────┬────────┘")
	fmt.Println("         │")
	fmt.Println("    Breaker: 12")
	fmt.Println("         │")
	fmt.Println("┌────────▼────────┐")
	fmt.Println("│   🔌 Outlet     │")
	fmt.Println("└────────┬────────┘")
	fmt.Println("         │")
	fmt.Println("    [Hardware]")
	fmt.Println("         │")
	fmt.Println("┌────────▼────────┐")
	fmt.Println("│   PCB: main     │")
	fmt.Println("└────────┬────────┘")
	fmt.Println("         │")
	fmt.Println("┌────────▼────────┐")
	fmt.Println("│  Component: U1  │")
	fmt.Println("└────────┬────────┘")
	fmt.Println("         │")
	fmt.Println("    📍 Pin: 5")
}

func showDetailedTrace(trace *models.HardwareTraceability) {
	fmt.Println("\n📋 Detailed Information:\n")
	
	fmt.Println("Electrical Properties:")
	fmt.Println("  Voltage: 120V AC")
	fmt.Println("  Current: 15A max")
	fmt.Println("  Wire: 14 AWG")
	fmt.Println("  Distance: 45m from panel")
	
	fmt.Println("\nHardware Properties:")
	fmt.Println("  PCB Layers: 4")
	fmt.Println("  Component Type: Microcontroller")
	fmt.Println("  Package: QFP-44")
	fmt.Println("  Pin Function: GPIO/ADC")
	fmt.Println("  Signal Level: 3.3V")
	
	fmt.Println("\nConnections:")
	fmt.Println("  Net: POWER_3V3")
	fmt.Println("  Trace Width: 0.25mm")
	fmt.Println("  Via Count: 2")
	fmt.Println("  Test Point: TP1")
}

func generateSampleBOM(deviceID string) *models.ManufacturingBOM {
	return &models.ManufacturingBOM{
		DeviceID: deviceID,
		Revision: "v1.0",
		Date:     "2024-08-26",
		Components: []models.BOMLine{
			{
				LineNo:      1,
				Designators: []string{"U1"},
				Quantity:    1,
				Description: "Microcontroller",
				Value:       "ESP32-WROOM-32",
				Package:     "SMD Module",
				Manufacturer: "Espressif",
				MfgPartNo:   "ESP32-WROOM-32",
				UnitCost:    3.50,
				ExtCost:     3.50,
			},
			{
				LineNo:      2,
				Designators: []string{"R1", "R2", "R3", "R4"},
				Quantity:    4,
				Description: "Resistor",
				Value:       "10K",
				Package:     "0603",
				UnitCost:    0.01,
				ExtCost:     0.04,
			},
			{
				LineNo:      3,
				Designators: []string{"C1", "C2"},
				Quantity:    2,
				Description: "Capacitor",
				Value:       "100nF",
				Package:     "0603",
				UnitCost:    0.02,
				ExtCost:     0.04,
			},
			{
				LineNo:      4,
				Designators: []string{"K1"},
				Quantity:    1,
				Description: "Relay",
				Value:       "5V SPDT",
				Package:     "THT",
				Manufacturer: "Omron",
				MfgPartNo:   "G5V-1",
				UnitCost:    2.50,
				ExtCost:     2.50,
			},
			{
				LineNo:      5,
				Designators: []string{"J1"},
				Quantity:    1,
				Description: "Terminal Block",
				Value:       "3-pos",
				Package:     "5.08mm",
				UnitCost:    0.75,
				ExtCost:     0.75,
			},
		},
		TotalParts: 9,
		TotalCost:  6.83,
	}
}

func printBOMTable(bom *models.ManufacturingBOM, showCost, checkStock bool) {
	fmt.Printf("\n═══ Bill of Materials: %s ═══\n", bom.DeviceID)
	fmt.Printf("Revision: %s | Date: %s\n\n", bom.Revision, bom.Date)
	
	// Header
	fmt.Printf("%-4s %-20s %-4s %-20s %-10s %-10s", 
		"Line", "Designators", "Qty", "Description", "Value", "Package")
	if showCost {
		fmt.Printf(" %-8s %-8s", "Unit $", "Ext $")
	}
	if checkStock {
		fmt.Printf(" %-10s", "Stock")
	}
	fmt.Println()
	fmt.Println(strings.Repeat("-", 100))
	
	// Components
	for _, line := range bom.Components {
		designators := strings.Join(line.Designators, ",")
		if len(designators) > 18 {
			designators = designators[:15] + "..."
		}
		
		fmt.Printf("%-4d %-20s %-4d %-20s %-10s %-10s",
			line.LineNo, designators, line.Quantity, 
			truncate(line.Description, 20),
			truncate(line.Value, 10),
			truncate(line.Package, 10))
		
		if showCost {
			fmt.Printf(" $%-7.2f $%-7.2f", line.UnitCost, line.ExtCost)
		}
		
		if checkStock {
			stock := checkComponentStock(line.MfgPartNo)
			fmt.Printf(" %-10s", stock)
		}
		
		fmt.Println()
	}
	
	fmt.Println(strings.Repeat("-", 100))
	fmt.Printf("Total Parts: %d", bom.TotalParts)
	if showCost {
		fmt.Printf(" | Total Cost: $%.2f", bom.TotalCost)
	}
	fmt.Println("\n")
}

func printBOMCSV(bom *models.ManufacturingBOM) {
	fmt.Println("Line,Designators,Qty,Description,Value,Package,Manufacturer,MfgPartNo,UnitCost,ExtCost")
	for _, line := range bom.Components {
		fmt.Printf("%d,\"%s\",%d,%s,%s,%s,%s,%s,%.2f,%.2f\n",
			line.LineNo,
			strings.Join(line.Designators, " "),
			line.Quantity,
			line.Description,
			line.Value,
			line.Package,
			line.Manufacturer,
			line.MfgPartNo,
			line.UnitCost,
			line.ExtCost)
	}
}

func printBOMJSON(bom *models.ManufacturingBOM) {
	// Simplified JSON output
	fmt.Printf("{\n  \"device_id\": \"%s\",\n", bom.DeviceID)
	fmt.Printf("  \"revision\": \"%s\",\n", bom.Revision)
	fmt.Printf("  \"total_parts\": %d,\n", bom.TotalParts)
	fmt.Printf("  \"total_cost\": %.2f,\n", bom.TotalCost)
	fmt.Println("  \"components\": [")
	for i, line := range bom.Components {
		fmt.Printf("    {\n")
		fmt.Printf("      \"line\": %d,\n", line.LineNo)
		fmt.Printf("      \"designators\": \"%s\",\n", strings.Join(line.Designators, ","))
		fmt.Printf("      \"quantity\": %d,\n", line.Quantity)
		fmt.Printf("      \"description\": \"%s\",\n", line.Description)
		fmt.Printf("      \"value\": \"%s\",\n", line.Value)
		fmt.Printf("      \"cost\": %.2f\n", line.ExtCost)
		fmt.Printf("    }")
		if i < len(bom.Components)-1 {
			fmt.Println(",")
		} else {
			fmt.Println()
		}
	}
	fmt.Println("  ]")
	fmt.Println("}")
}

func checkComponentStock(partNo string) string {
	// Simulate stock check
	if partNo == "" {
		return "Generic"
	}
	// Random stock status for demo
	statuses := []string{"✅ In Stock", "⚠️ Low", "❌ Out"}
	return statuses[len(partNo)%3]
}

func truncate(s string, max int) string {
	if len(s) <= max {
		return s
	}
	return s[:max-3] + "..."
}

func extractType(id string) string {
	parts := strings.Split(id, "/")
	if len(parts) > 2 {
		return parts[2]
	}
	return "unknown"
}

func extractLocation(id string) string {
	// Extract spatial location from ID
	if strings.Contains(id, "f1_r101") {
		return "Floor 1, Room 101"
	}
	return "Building"
}

// TestPointsCmd generates hardware test points
var TestPointsCmd = &cobra.Command{
	Use:   "test [device_id]",
	Short: "Generate test points for hardware validation",
	RunE: func(cmd *cobra.Command, args []string) error {
		if len(args) < 1 {
			return fmt.Errorf("specify device ID")
		}
		
		fmt.Printf("\n═══ Test Points: %s ═══\n\n", args[0])
		
		// Show test points
		testPoints := models.SmartOutletTestPoints
		
		fmt.Printf("%-15s %-10s %-15s %-15s %-10s %s\n",
			"Test ID", "Type", "Test Point", "Expected", "Tolerance", "Required")
		fmt.Println(strings.Repeat("-", 80))
		
		for _, tp := range testPoints {
			required := "Optional"
			if tp.Required {
				required = "Required"
			}
			fmt.Printf("%-15s %-10s %-15s %-15s %-10s %s\n",
				tp.TestID, tp.TestType, tp.TestPoint,
				tp.ExpectedValue+tp.Units, tp.Tolerance, required)
		}
		
		fmt.Println("\n✅ Test procedure generated")
		return nil
	},
}

func init() {
	HardwareCmd.AddCommand(TestPointsCmd)
}

// OpenHardwareCmd shows open hardware designs
var OpenHardwareCmd = &cobra.Command{
	Use:   "open-hardware",
	Short: "Browse open hardware designs",
	RunE: func(cmd *cobra.Command, args []string) error {
		fmt.Println("\n═══ Open Hardware Library ═══\n")
		fmt.Println("Community designs for the Open Hardware Revolution:\n")
		
		for _, design := range models.OpenHardwareDesigns {
			fmt.Printf("📦 %s\n", design.Name)
			fmt.Printf("   Type: %s\n", design.DeviceType)
			fmt.Printf("   Description: %s\n", design.Description)
			fmt.Printf("   License: %s\n", design.License)
			fmt.Printf("   Repository: %s\n\n", design.Repository)
		}
		
		fmt.Println("Use 'arxos hardware clone [design]' to use a design")
		return nil
	},
}

func init() {
	HardwareCmd.AddCommand(OpenHardwareCmd)
}