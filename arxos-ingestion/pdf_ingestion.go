package ingestion

import (
	"fmt"
	"strings"

	"github.com/arxos/arxos-core"
)

// PDFIngestion handles PDF document ingestion
type PDFIngestion struct {
	bridge     *IngestionBridge
	recognizer *SymbolRecognizer
	arxRepo    *arxoscore.ArxObjectRepository
}

// NewPDFIngestion creates a new PDF ingestion handler
func NewPDFIngestion(arxRepo *arxoscore.ArxObjectRepository) (*PDFIngestion, error) {
	bridge, err := NewIngestionBridge(arxRepo)
	if err != nil {
		return nil, err
	}

	recognizer, err := NewSymbolRecognizer()
	if err != nil {
		return nil, err
	}

	return &PDFIngestion{
		bridge:     bridge,
		recognizer: recognizer,
		arxRepo:    arxRepo,
	}, nil
}

// IngestPDF processes a PDF document and creates ArxObjects
func (p *PDFIngestion) IngestPDF(pdfData []byte, buildingID string, metadata map[string]interface{}) ([]*arxoscore.ArxObject, error) {
	// Step 1: Recognize symbols in PDF
	response, err := p.recognizer.RecognizeInPDF(pdfData)
	if err != nil {
		return nil, fmt.Errorf("failed to recognize symbols in PDF: %w", err)
	}

	// Log recognition statistics
	fmt.Printf("PDF Recognition Stats:\n")
	fmt.Printf("  Total symbols found: %d\n", response.Stats.TotalSymbols)
	fmt.Printf("  Recognized symbols: %d\n", response.Stats.RecognizedSymbols)
	fmt.Printf("  Average confidence: %.2f\n", response.Stats.AverageConfidence)

	// Step 2: Convert recognized symbols to internal format
	var recognizedSymbols []*RecognizedSymbol
	for _, symbolData := range response.Symbols {
		symbol := p.recognizer.ConvertPythonSymbol(symbolData)
		
		// Add PDF-specific context
		symbol.Context = "pdf"
		if pageNum, ok := metadata["page_number"].(int); ok {
			symbol.SourcePage = pageNum
		}
		
		// Determine parent space from position or metadata
		symbol.ParentSpace = p.determineParentSpace(symbol, metadata)
		
		recognizedSymbols = append(recognizedSymbols, symbol)
	}

	// Step 3: Extract structural elements (walls, rooms, floors)
	structuralElements := p.extractStructuralElements(pdfData, metadata)
	recognizedSymbols = append(recognizedSymbols, structuralElements...)

	// Step 4: Analyze relationships and connections
	p.analyzeRelationships(recognizedSymbols)

	// Step 5: Convert to ArxObjects
	arxObjects, err := p.bridge.ProcessRecognizedSymbols(recognizedSymbols, buildingID)
	if err != nil {
		return nil, fmt.Errorf("failed to process recognized symbols: %w", err)
	}

	// Step 6: Store in repository
	for _, obj := range arxObjects {
		if err := p.arxRepo.Create(obj); err != nil {
			return nil, fmt.Errorf("failed to store ArxObject %s: %w", obj.ID, err)
		}
	}

	return arxObjects, nil
}

// extractStructuralElements extracts walls, rooms, and other structural elements
func (p *PDFIngestion) extractStructuralElements(pdfData []byte, metadata map[string]interface{}) []*RecognizedSymbol {
	var elements []*RecognizedSymbol

	// This would use PDF parsing libraries to extract vector graphics
	// For now, we'll create some example structural elements

	// Example: Extract walls from vector paths
	wallSymbol := &RecognizedSymbol{
		Definition: &SymbolDefinition{
			ID:          "wall",
			Name:        "Wall",
			System:      "structural",
			Category:    "structural",
			DisplayName: "Wall",
			Tags:        []string{"wall", "structural"},
		},
		Position: Position{X: 0, Y: 0, Z: 0},
		Context:  "pdf_structural",
		Confidence: 0.95,
	}
	elements = append(elements, wallSymbol)

	// Example: Extract rooms from bounded areas
	roomSymbol := &RecognizedSymbol{
		Definition: &SymbolDefinition{
			ID:          "room",
			Name:        "Room",
			System:      "architectural",
			Category:    "space",
			DisplayName: "Room",
			Tags:        []string{"room", "space"},
		},
		Position: Position{X: 100, Y: 100, Z: 0},
		Context:  "pdf_space",
		Confidence: 0.90,
	}
	elements = append(elements, roomSymbol)

	return elements
}

// determineParentSpace determines which room or area a symbol belongs to
func (p *PDFIngestion) determineParentSpace(symbol *RecognizedSymbol, metadata map[string]interface{}) string {
	// This would use spatial analysis to determine which room contains the symbol
	// For now, return a default based on position
	
	if symbol.Position.X < 500 && symbol.Position.Y < 500 {
		return "room_101"
	} else if symbol.Position.X >= 500 && symbol.Position.Y < 500 {
		return "room_102"
	} else if symbol.Position.X < 500 && symbol.Position.Y >= 500 {
		return "room_103"
	}
	return "room_104"
}

// analyzeRelationships analyzes spatial and logical relationships between symbols
func (p *PDFIngestion) analyzeRelationships(symbols []*RecognizedSymbol) {
	// Analyze electrical connections
	p.analyzeElectricalConnections(symbols)
	
	// Analyze HVAC connections
	p.analyzeHVACConnections(symbols)
	
	// Analyze plumbing connections
	p.analyzePlumbingConnections(symbols)
	
	// Analyze control relationships
	p.analyzeControlRelationships(symbols)
}

// analyzeElectricalConnections finds electrical relationships
func (p *PDFIngestion) analyzeElectricalConnections(symbols []*RecognizedSymbol) {
	for i, symbol1 := range symbols {
		if symbol1.Definition.System != "electrical" {
			continue
		}

		for j, symbol2 := range symbols {
			if i == j || symbol2.Definition.System != "electrical" {
				continue
			}

			// Check if symbols are connected by wiring
			if p.areElectricallyConnected(symbol1, symbol2) {
				symbol1.Connections = append(symbol1.Connections, Connection{
					ToSymbolID: symbol2.Definition.ID,
					Type:       "electrical_feed",
					Properties: map[string]interface{}{
						"voltage": "120V",
						"phase":   "single",
					},
				})
			}
		}
	}
}

// areElectricallyConnected checks if two electrical symbols are connected
func (p *PDFIngestion) areElectricallyConnected(s1, s2 *RecognizedSymbol) bool {
	// This would analyze the PDF vector graphics to find wire connections
	// For now, use distance-based heuristic
	
	dx := s1.Position.X - s2.Position.X
	dy := s1.Position.Y - s2.Position.Y
	distance := dx*dx + dy*dy
	
	// If within 200 units and both electrical, assume connected
	return distance < 200*200
}

// analyzeHVACConnections finds HVAC relationships
func (p *PDFIngestion) analyzeHVACConnections(symbols []*RecognizedSymbol) {
	for i, symbol1 := range symbols {
		if symbol1.Definition.System != "mechanical" && symbol1.Definition.System != "hvac" {
			continue
		}

		for j, symbol2 := range symbols {
			if i == j {
				continue
			}

			// Thermostat controls HVAC unit
			if strings.Contains(symbol1.Definition.ID, "thermostat") && 
			   (symbol2.Definition.System == "mechanical" || symbol2.Definition.System == "hvac") {
				symbol1.Connections = append(symbol1.Connections, Connection{
					ToSymbolID: symbol2.Definition.ID,
					Type:       "control",
					Properties: map[string]interface{}{
						"control_type": "temperature",
					},
				})
			}

			// Duct connections
			if strings.Contains(symbol1.Definition.ID, "duct") && 
			   strings.Contains(symbol2.Definition.ID, "diffuser") {
				if p.areDuctConnected(symbol1, symbol2) {
					symbol1.Connections = append(symbol1.Connections, Connection{
						ToSymbolID: symbol2.Definition.ID,
						Type:       "air_flow",
						Properties: map[string]interface{}{
							"flow_type": "supply",
						},
					})
				}
			}
		}
	}
}

// areDuctConnected checks if HVAC components are connected
func (p *PDFIngestion) areDuctConnected(s1, s2 *RecognizedSymbol) bool {
	// This would trace duct paths in the PDF
	// For now, use proximity
	
	dx := s1.Position.X - s2.Position.X
	dy := s1.Position.Y - s2.Position.Y
	distance := dx*dx + dy*dy
	
	return distance < 300*300
}

// analyzePlumbingConnections finds plumbing relationships
func (p *PDFIngestion) analyzePlumbingConnections(symbols []*RecognizedSymbol) {
	for i, symbol1 := range symbols {
		if symbol1.Definition.System != "plumbing" {
			continue
		}

		for j, symbol2 := range symbols {
			if i == j || symbol2.Definition.System != "plumbing" {
				continue
			}

			// Check pipe connections
			if strings.Contains(symbol1.Definition.ID, "pipe") {
				if p.arePipesConnected(symbol1, symbol2) {
					symbol1.Connections = append(symbol1.Connections, Connection{
						ToSymbolID: symbol2.Definition.ID,
						Type:       "water_flow",
						Properties: map[string]interface{}{
							"flow_direction": p.determineFlowDirection(symbol1, symbol2),
							"pipe_type":      "supply", // or "drain"
						},
					})
				}
			}
		}
	}
}

// arePipesConnected checks if plumbing components are connected
func (p *PDFIngestion) arePipesConnected(s1, s2 *RecognizedSymbol) bool {
	// Would analyze pipe paths in PDF
	dx := s1.Position.X - s2.Position.X
	dy := s1.Position.Y - s2.Position.Y
	distance := dx*dx + dy*dy
	
	return distance < 250*250
}

// determineFlowDirection determines water flow direction
func (p *PDFIngestion) determineFlowDirection(s1, s2 *RecognizedSymbol) string {
	// Would analyze PDF annotations or symbols
	// For now, use position-based heuristic
	
	if s1.Position.Z > s2.Position.Z {
		return "down"
	} else if s1.Position.Z < s2.Position.Z {
		return "up"
	} else if s1.Position.X < s2.Position.X {
		return "right"
	}
	return "left"
}

// analyzeControlRelationships finds control relationships (switches to lights, etc.)
func (p *PDFIngestion) analyzeControlRelationships(symbols []*RecognizedSymbol) {
	for i, symbol1 := range symbols {
		// Switch controls light
		if strings.Contains(symbol1.Definition.ID, "switch") {
			for j, symbol2 := range symbols {
				if strings.Contains(symbol2.Definition.ID, "light") {
					if p.isSwitchControllingLight(symbol1, symbol2) {
						symbol1.Connections = append(symbol1.Connections, Connection{
							ToSymbolID: symbol2.Definition.ID,
							Type:       "control",
							Properties: map[string]interface{}{
								"control_type": "on_off",
							},
						})
					}
				}
			}
		}

		// Sensor triggers alarm
		if strings.Contains(symbol1.Definition.ID, "sensor") {
			for j, symbol2 := range symbols {
				if strings.Contains(symbol2.Definition.ID, "alarm") {
					if p.isSensorTriggeringAlarm(symbol1, symbol2) {
						symbol1.Connections = append(symbol1.Connections, Connection{
							ToSymbolID: symbol2.Definition.ID,
							Type:       "trigger",
							Properties: map[string]interface{}{
								"trigger_type": "motion", // or "smoke", "heat", etc.
							},
						})
					}
				}
			}
		}
	}
}

// isSwitchControllingLight determines if a switch controls a light
func (p *PDFIngestion) isSwitchControllingLight(switch, light *RecognizedSymbol) bool {
	// Would analyze electrical diagrams
	// For now, use room-based heuristic
	
	return switch.ParentSpace == light.ParentSpace
}

// isSensorTriggeringAlarm determines if a sensor triggers an alarm
func (p *PDFIngestion) isSensorTriggeringAlarm(sensor, alarm *RecognizedSymbol) bool {
	// Would analyze control diagrams
	// For now, use proximity
	
	dx := sensor.Position.X - alarm.Position.X
	dy := sensor.Position.Y - alarm.Position.Y
	distance := dx*dx + dy*dy
	
	return distance < 400*400
}