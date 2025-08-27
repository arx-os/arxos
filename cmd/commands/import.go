package commands

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"strings"

	"github.com/arxos/arxos/cmd/ascii"
	"github.com/arxos/arxos/cmd/models"
	"github.com/arxos/arxos/cmd/pdf"
	"github.com/spf13/cobra"
)

// ImportCmd imports building data from various sources
var ImportCmd = &cobra.Command{
	Use:   "import [source]",
	Short: "Import building data from PDF, CSV, or other sources",
	Long: `Import building information from various sources including:
- PDF drawings and schedules
- CSV equipment lists
- JSON ArxObject files

Examples:
  arxos import panel_schedule.pdf           # Import electrical panel schedule
  arxos import equipment_list.pdf           # Import mechanical equipment
  arxos import --building hq drawings.pdf   # Import with specific building ID
  arxos import --visualize schedule.pdf     # Import and show ASCII-BIM
  arxos import test_site/*.pdf              # Import multiple PDFs`,
	RunE: runImport,
}

func init() {
	ImportCmd.Flags().String("building", "", "Building ID (defaults to current building)")
	ImportCmd.Flags().String("type", "auto", "Source type: pdf, csv, json, auto")
	ImportCmd.Flags().Bool("visualize", false, "Show ASCII-BIM visualization after import")
	ImportCmd.Flags().Bool("dry-run", false, "Parse without saving")
	ImportCmd.Flags().Bool("verbose", false, "Verbose output")
	ImportCmd.Flags().String("output", ".arxos/objects", "Output directory for objects")
}

func runImport(cmd *cobra.Command, args []string) error {
	if len(args) < 1 {
		return fmt.Errorf("specify a file or directory to import")
	}

	// Get flags
	buildingID, _ := cmd.Flags().GetString("building")
	sourceType, _ := cmd.Flags().GetString("type")
	visualize, _ := cmd.Flags().GetBool("visualize")
	dryRun, _ := cmd.Flags().GetBool("dry-run")
	verbose, _ := cmd.Flags().GetBool("verbose")
	outputDir, _ := cmd.Flags().GetString("output")

	// Determine building ID
	if buildingID == "" {
		buildingID = getCurrentBuildingID()
		if buildingID == "" {
			buildingID = "imported_building"
		}
	}

	// Process each input file
	allObjects := []*models.ArxObjectV2{}
	
	for _, source := range args {
		// Check if source is a directory
		info, err := os.Stat(source)
		if err != nil {
			return fmt.Errorf("cannot access %s: %w", source, err)
		}

		var files []string
		if info.IsDir() {
			// Get all PDF files in directory
			pattern := filepath.Join(source, "*.pdf")
			matches, err := filepath.Glob(pattern)
			if err != nil {
				return fmt.Errorf("failed to list files: %w", err)
			}
			files = matches
		} else {
			files = []string{source}
		}

		// Process each file
		for _, file := range files {
			fmt.Printf("Importing: %s\n", file)
			
			objects, err := importFile(file, buildingID, sourceType, verbose)
			if err != nil {
				fmt.Printf("  ⚠️ Error: %v\n", err)
				continue
			}
			
			fmt.Printf("  ✅ Extracted %d objects\n", len(objects))
			allObjects = append(allObjects, objects...)
		}
	}

	if len(allObjects) == 0 {
		return fmt.Errorf("no objects extracted from input files")
	}

	// Show summary
	fmt.Printf("\n═══ IMPORT SUMMARY ═══\n\n")
	showImportSummary(allObjects)

	// Save objects if not dry-run
	if !dryRun {
		if err := saveImportedObjects(allObjects, buildingID, outputDir); err != nil {
			return fmt.Errorf("failed to save objects: %w", err)
		}
		fmt.Printf("\n✅ Saved %d objects to %s\n", len(allObjects), outputDir)
	} else {
		fmt.Println("\n🔍 Dry run - no objects saved")
	}

	// Show visualization if requested
	if visualize {
		showASCIIVisualization(allObjects, buildingID)
	}

	return nil
}

func importFile(file, buildingID, sourceType string, verbose bool) ([]*models.ArxObjectV2, error) {
	// Auto-detect type if needed
	if sourceType == "auto" {
		ext := strings.ToLower(filepath.Ext(file))
		switch ext {
		case ".pdf":
			sourceType = "pdf"
		case ".csv":
			sourceType = "csv"
		case ".json":
			sourceType = "json"
		default:
			return nil, fmt.Errorf("unknown file type: %s", ext)
		}
	}

	switch sourceType {
	case "pdf":
		return importPDF(file, buildingID, verbose)
	case "csv":
		return importCSV(file, buildingID)
	case "json":
		return importJSON(file)
	default:
		return nil, fmt.Errorf("unsupported source type: %s", sourceType)
	}
}

func importPDF(file, buildingID string, verbose bool) ([]*models.ArxObjectV2, error) {
	// Use our raw PDF parser
	rawParser := pdf.NewRawPDFParser()
	if err := rawParser.ParseFile(file); err != nil {
		return nil, fmt.Errorf("failed to parse PDF: %w", err)
	}
	
	// Extract text
	text := rawParser.GetText()
	if verbose {
		fmt.Printf("  📄 Extracted %d pages\n", len(rawParser.GetText()))
		if len(text) > 200 {
			fmt.Printf("  Preview: %s...\n", text[:200])
		}
	}
	
	// Parse electrical data
	electricalItems := rawParser.ParseElectricalData()
	fmt.Printf("  ⚡ Found %d electrical items\n", len(electricalItems))
	
	// Convert to ArxObjects
	objects := []*models.ArxObjectV2{}
	
	for _, item := range electricalItems {
		obj := &models.ArxObjectV2{
			System: "electrical",
			Status: "active",
		}
		
		switch item.Type {
		case "panel":
			obj.ID = fmt.Sprintf("%s/electrical/panel/%s", buildingID, strings.ToLower(item.ID))
			obj.Type = "panel"
			obj.Name = item.Name
			if item.Voltage > 0 {
				obj.Properties = map[string]interface{}{
					"voltage": item.Voltage,
				}
			}
			
		case "circuit":
			if item.Panel != "" {
				obj.ID = fmt.Sprintf("%s/electrical/panel/%s/breaker/%s", 
					buildingID, strings.ToLower(item.Panel), item.Circuit)
			} else {
				obj.ID = fmt.Sprintf("%s/electrical/circuit/%s", buildingID, item.Circuit)
			}
			obj.Type = "circuit"
			obj.Name = item.Name
			obj.Properties = map[string]interface{}{
				"circuit_number": item.Circuit,
				"amperage":      item.Amperage,
				"description":   item.Description,
			}
			if item.Panel != "" {
				obj.Relationships = map[string][]string{
					"fed_from": {fmt.Sprintf("%s/electrical/panel/%s", buildingID, strings.ToLower(item.Panel))},
				}
			}
		}
		
		objects = append(objects, obj)
	}
	
	// Also check for structured tables
	tables := rawParser.GetStructuredText()
	if len(tables) > 0 {
		fmt.Printf("  📊 Found %d potential tables\n", len(tables))
	}
	
	return objects, nil
}

func importCSV(file, buildingID string) ([]*models.ArxObjectV2, error) {
	// CSV import would be implemented here
	// For now, return empty
	return []*models.ArxObjectV2{}, fmt.Errorf("CSV import not yet implemented")
}

func importJSON(file string) ([]*models.ArxObjectV2, error) {
	data, err := os.ReadFile(file)
	if err != nil {
		return nil, fmt.Errorf("failed to read file: %w", err)
	}

	var objects []*models.ArxObjectV2
	if err := json.Unmarshal(data, &objects); err != nil {
		// Try single object
		var obj models.ArxObjectV2
		if err := json.Unmarshal(data, &obj); err != nil {
			return nil, fmt.Errorf("failed to parse JSON: %w", err)
		}
		objects = []*models.ArxObjectV2{&obj}
	}

	return objects, nil
}

func showImportSummary(objects []*models.ArxObjectV2) {
	// Count by system and type
	systemCounts := make(map[string]int)
	typeCounts := make(map[string]int)
	
	for _, obj := range objects {
		systemCounts[obj.System]++
		typeCounts[obj.Type]++
	}

	fmt.Println("BY SYSTEM:")
	for sys, count := range systemCounts {
		emoji := getSystemEmoji(sys)
		fmt.Printf("  %s %-12s: %d\n", emoji, strings.Title(sys), count)
	}

	fmt.Println("\nBY TYPE:")
	// Show top types
	maxShow := 10
	shown := 0
	for typ, count := range typeCounts {
		if shown >= maxShow {
			remaining := len(typeCounts) - shown
			if remaining > 0 {
				fmt.Printf("  ... and %d more types\n", remaining)
			}
			break
		}
		fmt.Printf("  • %-15s: %d\n", typ, count)
		shown++
	}

	// Show sample objects
	fmt.Println("\nSAMPLE OBJECTS:")
	maxSamples := 5
	for i, obj := range objects {
		if i >= maxSamples {
			break
		}
		fmt.Printf("  - %s (%s/%s)\n", obj.Name, obj.System, obj.Type)
	}
}

func saveImportedObjects(objects []*models.ArxObjectV2, buildingID, outputDir string) error {
	// Ensure output directory exists
	if err := os.MkdirAll(outputDir, 0755); err != nil {
		return fmt.Errorf("failed to create output directory: %w", err)
	}

	// Group objects by system
	bySystem := make(map[string][]*models.ArxObjectV2)
	for _, obj := range objects {
		bySystem[obj.System] = append(bySystem[obj.System], obj)
	}

	// Save each system's objects
	for system, sysObjects := range bySystem {
		filename := filepath.Join(outputDir, fmt.Sprintf("%s_%s.json", buildingID, system))
		
		data, err := json.MarshalIndent(sysObjects, "", "  ")
		if err != nil {
			return fmt.Errorf("failed to marshal %s objects: %w", system, err)
		}

		if err := os.WriteFile(filename, data, 0644); err != nil {
			return fmt.Errorf("failed to save %s objects: %w", system, err)
		}
	}

	// Also save a complete index
	indexFile := filepath.Join(outputDir, fmt.Sprintf("%s_index.json", buildingID))
	indexData, err := json.MarshalIndent(objects, "", "  ")
	if err != nil {
		return fmt.Errorf("failed to marshal index: %w", err)
	}

	return os.WriteFile(indexFile, indexData, 0644)
}

func showASCIIVisualization(objects []*models.ArxObjectV2, buildingID string) {
	builder := pdf.NewASCIIBuilder(buildingID)
	visualization := builder.BuildFullVisualization(objects)
	fmt.Println(visualization)
}

func getCurrentBuildingID() string {
	// Try to get from current directory context
	cwd, _ := os.Getwd()
	if strings.Contains(cwd, "building:") {
		parts := strings.Split(cwd, "building:")
		if len(parts) > 1 {
			return strings.Split(parts[1], string(os.PathSeparator))[0]
		}
	}
	
	// Try to get from navigation context
	if navContext.BuildingID != "" {
		return navContext.BuildingID
	}

	return ""
}

func getSystemEmoji(system string) string {
	emojis := map[string]string{
		"electrical": "⚡",
		"hvac":       "🌡️",
		"plumbing":   "💧",
		"fire":       "🔥",
		"security":   "🔒",
		"network":    "🌐",
		"spatial":    "🏢",
		"hardware":   "🔧",
	}
	
	if emoji, ok := emojis[system]; ok {
		return emoji
	}
	return "•"
}

// TestSiteCmd - Quick command to import test sites
var TestSiteCmd = &cobra.Command{
	Use:   "test-site [path]",
	Short: "Import a test site from PDF drawings",
	Long: `Quickly import and visualize a test site from PDF drawings.

This command streamlines the import process for testing:
- Auto-detects panel schedules, equipment lists, and floor plans
- Generates ASCII-BIM visualization
- Creates ArxObjects with proper naming convention

Examples:
  arxos test-site drawings/site1.pdf
  arxos test-site ~/Documents/test_sites/
  arxos test-site --building acme panel_schedule.pdf`,
	RunE: func(cmd *cobra.Command, args []string) error {
		if len(args) < 1 {
			return fmt.Errorf("specify test site PDF or directory")
		}

		buildingID, _ := cmd.Flags().GetString("building")
		if buildingID == "" {
			// Generate building ID from filename
			base := filepath.Base(args[0])
			buildingID = strings.TrimSuffix(base, filepath.Ext(base))
			buildingID = strings.ReplaceAll(buildingID, " ", "_")
			buildingID = strings.ToLower(buildingID)
		}

		fmt.Printf("\n🏢 Importing Test Site: %s\n\n", buildingID)

		// Run import with visualization
		importCmd := &cobra.Command{}
		importCmd.Flags().String("building", buildingID, "")
		importCmd.Flags().Bool("visualize", true, "")
		importCmd.Flags().Bool("verbose", true, "")

		return runImport(importCmd, args)
	},
}

func init() {
	TestSiteCmd.Flags().String("building", "", "Building ID for test site")
}

// DemoCmd shows demo buildings
var DemoCmd = &cobra.Command{
	Use:   "demo [site]",
	Short: "Show demo building visualizations",
	Long: `Display demonstration building layouts in ASCII-BIM.

Available demos:
  alafia    - Alafia Elementary School IDF Room
  office    - Corporate office floor plan
  electric  - Electrical room with panels
  
Examples:
  arxos demo alafia
  arxos demo office`,
	RunE: func(cmd *cobra.Command, args []string) error {
		if len(args) < 1 {
			return fmt.Errorf("specify demo site: alafia, office, electric")
		}
		
		switch args[0] {
		case "alafia":
			showAlafiaDemo()
		case "office":
			fmt.Println(ascii.RenderExampleOffice())
		case "electric":
			fmt.Println(ascii.RenderExampleElectricalRoom())
		default:
			return fmt.Errorf("unknown demo: %s", args[0])
		}
		
		return nil
	},
}

func showAlafiaDemo() {
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
			{Type: "panel", Position: ascii.Point{28, 12}, ID: "IDF-PNL"},
			{Type: "outlet_duplex", Position: ascii.Point{12, 24}},
			{Type: "outlet_duplex", Position: ascii.Point{18, 24}},
			{Type: "outlet_duplex", Position: ascii.Point{24, 24}},
			
			// HVAC
			{Type: "diffuser", Position: ascii.Point{20, 17}},
			{Type: "thermostat", Position: ascii.Point{29, 20}},
		},
	}
	
	// Update equipment types for racks
	for i := range idfRoom.Equipment {
		if idfRoom.Equipment[i].Type == "rack" {
			idfRoom.Equipment[i].Symbol = '▦'
		}
	}
	
	fb.Rooms = []ascii.Room{idfRoom}
	fb.Renderer.DetailLevel = 3
	
	// Custom render for network racks
	fmt.Println("╔════════════════════════════════════════════════════════╗")
	fmt.Println("║                      IDF-1 ROOM                        ║")
	fmt.Println("║                                                        ║")
	fmt.Println("║  ┌──────┐     ┌──────┐     ┌──────┐      ╔═══════╗  ║")
	fmt.Println("║  │      │     │      │     │      │      ║ PANEL ║  ║")
	fmt.Println("║  │ RACK │     │ RACK │     │ RACK │      ║  IDF  ║  ║")
	fmt.Println("║  │  01  │     │  02  │     │  03  │      ║       ║  ║")
	fmt.Println("║  │      │     │      │     │      │      ╠═══════╣  ║")
	fmt.Println("║  │ ████ │     │ ████ │     │ ████ │      ║ [01]  ║  ║")
	fmt.Println("║  │ ████ │     │ ████ │     │ ████ │      ║ [02]  ║  ║")
	fmt.Println("║  │ ████ │     │ ████ │     │ ████ │      ║ [03]  ║  ║")
	fmt.Println("║  │      │     │      │     │      │      ║ [04]  ║  ║")
	fmt.Println("║  └──────┘     └──────┘     └──────┘      ║ [05]  ║  ║")
	fmt.Println("║     42U          42U          42U         ║ [06]  ║  ║")
	fmt.Println("║                                           ╚═══════╝  ║")
	fmt.Println("║     ⊙             ⊙             ⊙                    ║")
	fmt.Println("║   Outlet        Outlet        Outlet        ◫ Stat  ║")
	fmt.Println("║                                                      ║")
	fmt.Println("║                    ╬ HVAC Supply                     ║")
	fmt.Println("║                                              ◦ Door  ║")
	fmt.Println("╚════════════════════════════════════════════════════════╝")
	
	// Show electrical distribution
	fmt.Println("\n═══ ELECTRICAL DISTRIBUTION ═══\n")
	fmt.Println("🏢 Building Main Service (Alafia ES)")
	fmt.Println("│")
	fmt.Println("├─⚡ Main Distribution Panel (MDP)")
	fmt.Println("│   480V 3-Phase → 208V/120V Transformer")
	fmt.Println("│")
	fmt.Println("└─🔌 Panel IDF-1 (Fed from MDP Breaker 42)")
	fmt.Println("    │")
	fmt.Println("    ├─ [01-02] Network Rack 1 (20A) - Core Network")
	fmt.Println("    │   └─ Core Switch, Firewall, Router")
	fmt.Println("    │")
	fmt.Println("    ├─ [03-04] Network Rack 2 (20A) - PoE Distribution")
	fmt.Println("    │   └─ PoE Switches (Cameras, Phones, APs)")
	fmt.Println("    │")
	fmt.Println("    ├─ [05-06] Network Rack 3 (20A) - Servers")
	fmt.Println("    │   └─ File Server, Security NVR, Backup")
	fmt.Println("    │")
	fmt.Println("    ├─ [07] HVAC Control (15A)")
	fmt.Println("    ├─ [08] Emergency Lighting (10A)")
	fmt.Println("    └─ [09-10] Convenience Outlets (20A each)")
	
	// Show network connections
	fmt.Println("\n═══ NETWORK ARCHITECTURE ═══\n")
	fmt.Println("         ┌─────────────┐")
	fmt.Println("         │  DISTRICT   │")
	fmt.Println("         │     WAN     │")
	fmt.Println("         └──────┬──────┘")
	fmt.Println("                │ Fiber")
	fmt.Println("         ┌──────▼──────┐")
	fmt.Println("         │   FIREWALL  │")
	fmt.Println("         │  (Rack 01)  │")
	fmt.Println("         └──────┬──────┘")
	fmt.Println("                │")
	fmt.Println("         ┌──────▼──────┐")
	fmt.Println("         │ CORE SWITCH │")
	fmt.Println("         │   48-Port   │")
	fmt.Println("         │  (Rack 01)  │")
	fmt.Println("         └──┬───┬───┬──┘")
	fmt.Println("            │   │   │")
	fmt.Println("     ┌──────┘   │   └──────┐")
	fmt.Println("     │          │          │")
	fmt.Println("┌────▼────┐ ┌──▼──┐ ┌─────▼────┐")
	fmt.Println("│PoE SW 1 │ │PoE  │ │  SERVER  │")
	fmt.Println("│Cameras  │ │SW 2 │ │  SWITCH  │")
	fmt.Println("│(Rack 02)│ │APs  │ │(Rack 03) │")
	fmt.Println("└─────────┘ └─────┘ └──────────┘")
	
	// Show critical systems
	fmt.Println("\n═══ CRITICAL SYSTEMS & REDUNDANCY ═══\n")
	fmt.Println("🔋 UPS Protection:")
	fmt.Println("  • Rack 01: 3000VA UPS (30 min runtime)")
	fmt.Println("  • Rack 03: 2000VA UPS (20 min runtime)")
	fmt.Println("")
	fmt.Println("🌡️ Environmental:")
	fmt.Println("  • Required Cooling: 3 Tons")
	fmt.Println("  • Current Temp: 72°F")
	fmt.Println("  • Humidity: 45%")
	fmt.Println("  • Alarm Threshold: 85°F")
	fmt.Println("")
	fmt.Println("⚠️ Monitoring:")
	fmt.Println("  • SNMP to BMS")
	fmt.Println("  • Temperature Sensors")
	fmt.Println("  • Door Contact")
	fmt.Println("  • Smoke Detection")
}