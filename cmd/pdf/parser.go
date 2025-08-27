package pdf

import (
	"encoding/json"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"regexp"
	"strconv"
	"strings"

	"github.com/arxos/arxos/cmd/models"
)

// PDFParser handles PDF extraction and parsing
type PDFParser struct {
	BuildingID string
	OutputDir  string
	Verbose    bool
}

// NewPDFParser creates a new PDF parser
func NewPDFParser(buildingID string) *PDFParser {
	return &PDFParser{
		BuildingID: buildingID,
		OutputDir:  ".arxos/extracted",
	}
}

// ParsePDF extracts and parses building data from PDF
func (p *PDFParser) ParsePDF(pdfPath string) ([]*models.ArxObjectV2, error) {
	// Ensure output directory exists
	if err := os.MkdirAll(p.OutputDir, 0755); err != nil {
		return nil, fmt.Errorf("failed to create output directory: %w", err)
	}

	// Extract text from PDF
	textFile := filepath.Join(p.OutputDir, "extracted.txt")
	if err := p.extractText(pdfPath, textFile); err != nil {
		return nil, fmt.Errorf("failed to extract text: %w", err)
	}

	// Read extracted text
	content, err := os.ReadFile(textFile)
	if err != nil {
		return nil, fmt.Errorf("failed to read extracted text: %w", err)
	}

	text := string(content)
	objects := []*models.ArxObjectV2{}

	// Try different parsers based on content
	if strings.Contains(text, "PANEL") || strings.Contains(text, "Panel Schedule") {
		panelObjects := p.parseElectricalPanels(text)
		objects = append(objects, panelObjects...)
	}

	if strings.Contains(text, "EQUIPMENT") || strings.Contains(text, "Equipment Schedule") {
		equipObjects := p.parseEquipmentSchedule(text)
		objects = append(objects, equipObjects...)
	}

	if strings.Contains(text, "VAV") || strings.Contains(text, "Air Handler") {
		hvacObjects := p.parseHVACSchedule(text)
		objects = append(objects, hvacObjects...)
	}

	// Parse room/space information
	if strings.Contains(text, "ROOM") || strings.Contains(text, "Room Schedule") {
		roomObjects := p.parseRoomSchedule(text)
		objects = append(objects, roomObjects...)
	}

	return objects, nil
}

// extractText uses pdftotext to extract text from PDF
func (p *PDFParser) extractText(pdfPath, outputPath string) error {
	// Try pdftotext first (best for text extraction)
	cmd := exec.Command("pdftotext", "-layout", pdfPath, outputPath)
	if err := cmd.Run(); err != nil {
		// Fallback to trying other methods
		if p.Verbose {
			fmt.Printf("pdftotext failed, trying alternative extraction: %v\n", err)
		}
		return p.extractTextFallback(pdfPath, outputPath)
	}
	return nil
}

// extractTextFallback uses alternative methods
func (p *PDFParser) extractTextFallback(pdfPath, outputPath string) error {
	// Try using strings command on PDF directly (crude but sometimes works)
	cmd := exec.Command("strings", pdfPath)
	output, err := cmd.Output()
	if err != nil {
		return fmt.Errorf("all extraction methods failed: %w", err)
	}

	return os.WriteFile(outputPath, output, 0644)
}

// parseElectricalPanels extracts electrical panel schedules
func (p *PDFParser) parseElectricalPanels(text string) []*models.ArxObjectV2 {
	objects := []*models.ArxObjectV2{}
	lines := strings.Split(text, "\n")
	
	var currentPanel *models.ArxObjectV2
	inPanelSchedule := false
	
	// Patterns for panel parsing
	panelPattern := regexp.MustCompile(`(?i)PANEL\s+([A-Z0-9-]+)`)
	breakerPattern := regexp.MustCompile(`^\s*(\d+)\s+(.+?)\s+(\d+)\s*A\s+(\d+)?\s*W?`)
	voltagePattern := regexp.MustCompile(`(\d+)\s*V`)
	phasePattern := regexp.MustCompile(`(\d+)\s*(?:PH|PHASE)`)
	
	for _, line := range lines {
		// Detect panel start
		if matches := panelPattern.FindStringSubmatch(line); matches != nil {
			// Save previous panel if exists
			if currentPanel != nil {
				objects = append(objects, currentPanel)
			}
			
			panelID := strings.ToLower(strings.ReplaceAll(matches[1], "-", "_"))
			currentPanel = &models.ArxObjectV2{
				ID:     fmt.Sprintf("%s/electrical/panel/%s", p.BuildingID, panelID),
				Type:   "panel",
				System: "electrical",
				Name:   fmt.Sprintf("Panel %s", matches[1]),
				Properties: map[string]interface{}{
					"panel_name": matches[1],
					"breakers":   []map[string]interface{}{},
				},
				Relationships: map[string][]string{
					"contains": []string{},
				},
			}
			
			// Extract voltage if present
			if vMatches := voltagePattern.FindStringSubmatch(line); vMatches != nil {
				voltage, _ := strconv.Atoi(vMatches[1])
				currentPanel.Properties["voltage"] = voltage
			}
			
			// Extract phase
			if phMatches := phasePattern.FindStringSubmatch(line); phMatches != nil {
				phase, _ := strconv.Atoi(phMatches[1])
				currentPanel.Properties["phase"] = phase
			}
			
			inPanelSchedule = true
			continue
		}
		
		// Parse breakers within panel
		if inPanelSchedule && currentPanel != nil {
			if matches := breakerPattern.FindStringSubmatch(line); matches != nil {
				breakerNum, _ := strconv.Atoi(matches[1])
				description := strings.TrimSpace(matches[2])
				amperage, _ := strconv.Atoi(matches[3])
				wattage := 0
				if matches[4] != "" {
					wattage, _ = strconv.Atoi(matches[4])
				}
				
				// Create breaker object
				breakerID := fmt.Sprintf("%s/breaker/%d", currentPanel.ID, breakerNum)
				breaker := &models.ArxObjectV2{
					ID:     breakerID,
					Type:   "breaker",
					System: "electrical",
					Name:   fmt.Sprintf("Breaker %d - %s", breakerNum, description),
					Properties: map[string]interface{}{
						"number":      breakerNum,
						"description": description,
						"amperage":    amperage,
						"wattage":     wattage,
					},
					Relationships: map[string][]string{
						"fed_from": []string{currentPanel.ID},
					},
				}
				
				objects = append(objects, breaker)
				
				// Add to panel's breakers list
				breakers := currentPanel.Properties["breakers"].([]map[string]interface{})
				breakers = append(breakers, map[string]interface{}{
					"number":      breakerNum,
					"description": description,
					"amperage":    amperage,
					"circuit_id":  breakerID,
				})
				currentPanel.Properties["breakers"] = breakers
				currentPanel.Relationships["contains"] = append(
					currentPanel.Relationships["contains"], 
					breakerID,
				)
			}
		}
		
		// Detect end of panel schedule
		if inPanelSchedule && (line == "" || strings.Contains(line, "---")) {
			inPanelSchedule = false
		}
	}
	
	// Add last panel
	if currentPanel != nil {
		objects = append(objects, currentPanel)
	}
	
	return objects
}

// parseEquipmentSchedule extracts mechanical equipment
func (p *PDFParser) parseEquipmentSchedule(text string) []*models.ArxObjectV2 {
	objects := []*models.ArxObjectV2{}
	lines := strings.Split(text, "\n")
	
	// Patterns for equipment
	equipPattern := regexp.MustCompile(`(?i)(AHU|RTU|VAV|FCU|EF|SF|RF)-?(\d+[A-Z]?)`)
	hpPattern := regexp.MustCompile(`(\d+(?:\.\d+)?)\s*HP`)
	cfmPattern := regexp.MustCompile(`(\d+)\s*CFM`)
	kWPattern := regexp.MustCompile(`(\d+(?:\.\d+)?)\s*kW`)
	
	for _, line := range lines {
		if matches := equipPattern.FindAllStringSubmatch(line, -1); len(matches) > 0 {
			for _, match := range matches {
				equipType := strings.ToUpper(match[1])
				equipNum := match[2]
				equipID := fmt.Sprintf("%s_%s", strings.ToLower(match[1]), strings.ToLower(equipNum))
				
				// Determine system based on type
				system := "hvac"
				objType := ""
				switch equipType {
				case "AHU":
					objType = "air_handler"
				case "RTU":
					objType = "rooftop_unit"
				case "VAV":
					objType = "vav_box"
				case "FCU":
					objType = "fan_coil"
				case "EF", "SF", "RF":
					objType = "exhaust_fan"
				}
				
				obj := &models.ArxObjectV2{
					ID:     fmt.Sprintf("%s/%s/%s/%s", p.BuildingID, system, objType, equipID),
					Type:   objType,
					System: system,
					Name:   fmt.Sprintf("%s-%s", equipType, equipNum),
					Properties: map[string]interface{}{
						"tag": fmt.Sprintf("%s-%s", equipType, equipNum),
					},
				}
				
				// Extract specifications
				if hpMatches := hpPattern.FindStringSubmatch(line); hpMatches != nil {
					hp, _ := strconv.ParseFloat(hpMatches[1], 64)
					obj.Properties["horsepower"] = hp
					// Estimate electrical load
					obj.PowerLoad = &models.LoadInformation{
						Power: hp * 746, // Convert HP to watts
					}
				}
				
				if cfmMatches := cfmPattern.FindStringSubmatch(line); cfmMatches != nil {
					cfm, _ := strconv.Atoi(cfmMatches[1])
					obj.Properties["airflow_cfm"] = cfm
				}
				
				if kWMatches := kWPattern.FindStringSubmatch(line); kWMatches != nil {
					kw, _ := strconv.ParseFloat(kWMatches[1], 64)
					obj.Properties["power_kw"] = kw
					if obj.PowerLoad == nil {
						obj.PowerLoad = &models.LoadInformation{}
					}
					obj.PowerLoad.Power = kw * 1000
				}
				
				objects = append(objects, obj)
			}
		}
	}
	
	return objects
}

// parseHVACSchedule extracts HVAC equipment details
func (p *PDFParser) parseHVACSchedule(text string) []*models.ArxObjectV2 {
	objects := []*models.ArxObjectV2{}
	
	// Look for VAV schedules
	vavPattern := regexp.MustCompile(`(?i)VAV[- ]?(\d+[A-Z]?)\s+.*?(\d+)\s*CFM`)
	lines := strings.Split(text, "\n")
	
	for _, line := range lines {
		if matches := vavPattern.FindStringSubmatch(line); matches != nil {
			vavNum := matches[1]
			cfm, _ := strconv.Atoi(matches[2])
			
			vav := &models.ArxObjectV2{
				ID:     fmt.Sprintf("%s/hvac/vav/vav_%s", p.BuildingID, strings.ToLower(vavNum)),
				Type:   "vav_box",
				System: "hvac",
				Name:   fmt.Sprintf("VAV-%s", vavNum),
				Properties: map[string]interface{}{
					"tag":         fmt.Sprintf("VAV-%s", vavNum),
					"airflow_cfm": cfm,
					"type":        "vav",
				},
			}
			
			// Check if it has reheat
			if strings.Contains(strings.ToUpper(line), "REHEAT") || strings.Contains(line, "RH") {
				vav.Properties["reheat"] = true
				if strings.Contains(strings.ToUpper(line), "ELEC") {
					vav.Properties["reheat_type"] = "electric"
					// Estimate reheat power
					vav.PowerLoad = &models.LoadInformation{
						Power: float64(cfm) * 3, // Rough estimate: 3W per CFM
					}
				} else {
					vav.Properties["reheat_type"] = "hot_water"
				}
			}
			
			objects = append(objects, vav)
		}
	}
	
	return objects
}

// parseRoomSchedule extracts room/space information
func (p *PDFParser) parseRoomSchedule(text string) []*models.ArxObjectV2 {
	objects := []*models.ArxObjectV2{}
	
	// Room patterns
	roomPattern := regexp.MustCompile(`(?i)(?:ROOM|RM|SPACE)\s*(\d+[A-Z]?)\s+(.+?)\s+(\d+)\s*(?:SF|SQ\s*FT)`)
	floorPattern := regexp.MustCompile(`(?i)(?:FLOOR|LEVEL|FL)\s*(\d+|[BG]\d*)`)
	
	currentFloor := "1"
	lines := strings.Split(text, "\n")
	
	for _, line := range lines {
		// Check for floor indicator
		if matches := floorPattern.FindStringSubmatch(line); matches != nil {
			floor := strings.ToLower(matches[1])
			if floor == "g" || floor == "0" {
				currentFloor = "1"
			} else if strings.HasPrefix(floor, "b") {
				currentFloor = floor
			} else {
				currentFloor = floor
			}
		}
		
		// Parse room info
		if matches := roomPattern.FindStringSubmatch(line); matches != nil {
			roomNum := matches[1]
			roomName := strings.TrimSpace(matches[2])
			area, _ := strconv.Atoi(matches[3])
			
			room := &models.ArxObjectV2{
				ID:     fmt.Sprintf("%s/f%s/room/%s", p.BuildingID, currentFloor, strings.ToLower(roomNum)),
				Type:   "room",
				System: "spatial",
				Name:   fmt.Sprintf("Room %s - %s", roomNum, roomName),
				Properties: map[string]interface{}{
					"number":    roomNum,
					"name":      roomName,
					"area_sqft": area,
					"floor":     currentFloor,
				},
				SpatialLocation: fmt.Sprintf("%s/f%s", p.BuildingID, currentFloor),
			}
			
			// Determine room type based on name
			roomNameLower := strings.ToLower(roomName)
			if strings.Contains(roomNameLower, "office") {
				room.Properties["type"] = "office"
			} else if strings.Contains(roomNameLower, "conference") {
				room.Properties["type"] = "conference"
			} else if strings.Contains(roomNameLower, "mechanical") || strings.Contains(roomNameLower, "elec") {
				room.Properties["type"] = "mechanical"
			} else if strings.Contains(roomNameLower, "it") || strings.Contains(roomNameLower, "server") {
				room.Properties["type"] = "it_room"
				room.Critical = true
			}
			
			objects = append(objects, room)
		}
	}
	
	return objects
}

// SaveObjects saves parsed objects to JSON files
func (p *PDFParser) SaveObjects(objects []*models.ArxObjectV2) error {
	objectDir := ".arxos/objects"
	if err := os.MkdirAll(objectDir, 0755); err != nil {
		return fmt.Errorf("failed to create object directory: %w", err)
	}
	
	// Group objects by system
	bySystem := make(map[string][]*models.ArxObjectV2)
	for _, obj := range objects {
		bySystem[obj.System] = append(bySystem[obj.System], obj)
	}
	
	// Save each system's objects
	for system, sysObjects := range bySystem {
		filename := filepath.Join(objectDir, fmt.Sprintf("%s_%s.json", p.BuildingID, system))
		
		data, err := json.MarshalIndent(sysObjects, "", "  ")
		if err != nil {
			return fmt.Errorf("failed to marshal %s objects: %w", system, err)
		}
		
		if err := os.WriteFile(filename, data, 0644); err != nil {
			return fmt.Errorf("failed to save %s objects: %w", system, err)
		}
		
		if p.Verbose {
			fmt.Printf("Saved %d %s objects to %s\n", len(sysObjects), system, filename)
		}
	}
	
	return nil
}

// ExtractTables attempts to extract tabular data from PDF
func (p *PDFParser) ExtractTables(pdfPath string) ([]Table, error) {
	// This would use more sophisticated table extraction
	// For now, use basic pattern matching
	
	textFile := filepath.Join(p.OutputDir, "tables.txt")
	cmd := exec.Command("pdftotext", "-layout", "-nopgbrk", pdfPath, textFile)
	if err := cmd.Run(); err != nil {
		return nil, fmt.Errorf("failed to extract tables: %w", err)
	}
	
	content, err := os.ReadFile(textFile)
	if err != nil {
		return nil, err
	}
	
	return p.parseTablesFromText(string(content)), nil
}

// Table represents extracted tabular data
type Table struct {
	Headers []string
	Rows    [][]string
	Type    string // panel_schedule, equipment_list, etc.
}

// parseTablesFromText extracts tables from text
func (p *PDFParser) parseTablesFromText(text string) []Table {
	tables := []Table{}
	lines := strings.Split(text, "\n")
	
	var currentTable *Table
	var inTable bool
	
	for i, line := range lines {
		// Detect table headers (multiple words separated by 2+ spaces)
		if strings.Count(line, "  ") >= 3 && !inTable {
			fields := regexp.MustCompile(`\s{2,}`).Split(line, -1)
			cleanFields := []string{}
			for _, f := range fields {
				if trimmed := strings.TrimSpace(f); trimmed != "" {
					cleanFields = append(cleanFields, trimmed)
				}
			}
			
			if len(cleanFields) >= 3 {
				// Looks like a header
				currentTable = &Table{
					Headers: cleanFields,
					Rows:    [][]string{},
				}
				
				// Determine table type
				headerText := strings.ToUpper(strings.Join(cleanFields, " "))
				if strings.Contains(headerText, "PANEL") || strings.Contains(headerText, "BREAKER") {
					currentTable.Type = "panel_schedule"
				} else if strings.Contains(headerText, "EQUIPMENT") {
					currentTable.Type = "equipment_schedule"
				}
				
				inTable = true
				continue
			}
		}
		
		// Parse table rows
		if inTable && currentTable != nil {
			// Check if we're still in the table
			if line == "" || strings.HasPrefix(line, "---") {
				// End of table
				if len(currentTable.Rows) > 0 {
					tables = append(tables, *currentTable)
				}
				inTable = false
				currentTable = nil
				continue
			}
			
			// Parse row
			fields := regexp.MustCompile(`\s{2,}`).Split(line, -1)
			cleanFields := []string{}
			for _, f := range fields {
				cleanFields = append(cleanFields, strings.TrimSpace(f))
			}
			
			if len(cleanFields) >= len(currentTable.Headers)-1 {
				currentTable.Rows = append(currentTable.Rows, cleanFields)
			}
		}
		
		// Safety check - don't let tables run too long
		if inTable && i > 0 && (i%100 == 0) {
			if len(currentTable.Rows) > 0 {
				tables = append(tables, *currentTable)
			}
			inTable = false
			currentTable = nil
		}
	}
	
	// Add final table if exists
	if currentTable != nil && len(currentTable.Rows) > 0 {
		tables = append(tables, *currentTable)
	}
	
	return tables
}