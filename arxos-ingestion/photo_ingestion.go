package ingestion

import (
	"fmt"
	"math"
	"sort"

	"github.com/arxos/arxos-core"
)

// PhotoIngestion handles photo-of-paper-map ingestion
// This is critical for HCPS reality - paper maps at every school front desk
type PhotoIngestion struct {
	bridge     *IngestionBridge
	recognizer *SymbolRecognizer
	arxRepo    *arxoscore.ArxObjectRepository
}

// NewPhotoIngestion creates a new photo ingestion handler
func NewPhotoIngestion(arxRepo *arxoscore.ArxObjectRepository) (*PhotoIngestion, error) {
	bridge, err := NewIngestionBridge(arxRepo)
	if err != nil {
		return nil, err
	}

	recognizer, err := NewSymbolRecognizer()
	if err != nil {
		return nil, err
	}

	return &PhotoIngestion{
		bridge:     bridge,
		recognizer: recognizer,
		arxRepo:    arxRepo,
	}, nil
}

// IngestPhoto processes a photo of a paper map and creates ArxObjects
func (p *PhotoIngestion) IngestPhoto(imageData []byte, buildingID string, metadata map[string]interface{}) ([]*arxoscore.ArxObject, error) {
	// Step 1: Apply perspective correction
	correctedImage, perspectiveData := p.applyPerspectiveCorrection(imageData)
	
	// Step 2: Enhance image for better recognition
	enhancedImage := p.enhanceImage(correctedImage)
	
	// Step 3: Detect walls and rooms using edge detection
	structuralElements := p.detectStructuralElements(enhancedImage)
	
	// Step 4: OCR for room numbers and labels
	textElements := p.extractTextElements(enhancedImage)
	
	// Step 5: Recognize symbols using the symbol library
	response, err := p.recognizer.RecognizeInImage(enhancedImage)
	if err != nil {
		return nil, fmt.Errorf("failed to recognize symbols in photo: %w", err)
	}

	// Log recognition statistics
	fmt.Printf("Photo Recognition Stats:\n")
	fmt.Printf("  Total symbols found: %d\n", response.Stats.TotalSymbols)
	fmt.Printf("  Recognized symbols: %d\n", response.Stats.RecognizedSymbols)
	fmt.Printf("  Average confidence: %.2f\n", response.Stats.AverageConfidence)
	fmt.Printf("  Structural elements detected: %d\n", len(structuralElements))
	fmt.Printf("  Text elements extracted: %d\n", len(textElements))

	// Step 6: Combine all recognized elements
	var recognizedSymbols []*RecognizedSymbol
	
	// Add symbols from recognition engine
	for _, symbolData := range response.Symbols {
		symbol := p.recognizer.ConvertPythonSymbol(symbolData)
		symbol.Context = "photo"
		
		// Adjust position based on perspective correction
		symbol.Position = p.adjustPosition(symbol.Position, perspectiveData)
		
		// Match symbol to room based on OCR results
		symbol.ParentSpace = p.matchSymbolToRoom(symbol, textElements)
		
		recognizedSymbols = append(recognizedSymbols, symbol)
	}
	
	// Add structural elements
	recognizedSymbols = append(recognizedSymbols, structuralElements...)
	
	// Add text-based elements (room labels become room objects)
	for _, textElem := range textElements {
		if textElem.Type == "room_number" {
			roomSymbol := p.createRoomFromText(textElem)
			recognizedSymbols = append(recognizedSymbols, roomSymbol)
		}
	}

	// Step 7: Build spatial hierarchy from detected rooms
	p.buildSpatialHierarchy(recognizedSymbols)

	// Step 8: Infer connections from proximity and alignment
	p.inferConnections(recognizedSymbols)

	// Step 9: Convert to ArxObjects
	arxObjects, err := p.bridge.ProcessRecognizedSymbols(recognizedSymbols, buildingID)
	if err != nil {
		return nil, fmt.Errorf("failed to process recognized symbols: %w", err)
	}

	// Step 10: Apply confidence-based filtering
	arxObjects = p.filterByConfidence(arxObjects, 0.3) // Lower threshold for photos

	// Step 11: Store in repository
	for _, obj := range arxObjects {
		// Mark as requiring verification due to photo source
		obj.Verified = false
		obj.Source = "photo"
		
		if err := p.arxRepo.Create(obj); err != nil {
			return nil, fmt.Errorf("failed to store ArxObject %s: %w", obj.ID, err)
		}
	}

	return arxObjects, nil
}

// PerspectiveData holds perspective correction parameters
type PerspectiveData struct {
	OriginalCorners []Point
	CorrectedCorners []Point
	TransformMatrix [][]float64
	Scale float64
}

// Point represents a 2D point
type Point struct {
	X float64
	Y float64
}

// TextElement represents extracted text from OCR
type TextElement struct {
	Text     string
	Position Point
	Type     string // room_number, label, annotation
	Confidence float64
}

// applyPerspectiveCorrection corrects perspective distortion from angled photos
func (p *PhotoIngestion) applyPerspectiveCorrection(imageData []byte) ([]byte, *PerspectiveData) {
	// This would use OpenCV or similar for perspective correction
	// Key steps:
	// 1. Detect document corners using edge detection
	// 2. Calculate perspective transform matrix
	// 3. Apply transformation to create top-down view
	
	perspectiveData := &PerspectiveData{
		Scale: 1.0,
		TransformMatrix: [][]float64{
			{1, 0, 0},
			{0, 1, 0},
			{0, 0, 1},
		},
	}
	
	// For now, return original image
	return imageData, perspectiveData
}

// enhanceImage improves image quality for better recognition
func (p *PhotoIngestion) enhanceImage(imageData []byte) []byte {
	// This would apply image enhancement techniques:
	// - Contrast adjustment
	// - Noise reduction
	// - Sharpening
	// - Binarization for line detection
	
	return imageData
}

// detectStructuralElements finds walls, doors, and rooms using computer vision
func (p *PhotoIngestion) detectStructuralElements(imageData []byte) []*RecognizedSymbol {
	var elements []*RecognizedSymbol
	
	// Detect walls using line detection (Hough transform)
	walls := p.detectWalls(imageData)
	for _, wall := range walls {
		elements = append(elements, wall)
	}
	
	// Detect door openings (gaps in walls)
	doors := p.detectDoors(walls)
	for _, door := range doors {
		elements = append(elements, door)
	}
	
	// Detect rooms (enclosed areas)
	rooms := p.detectRooms(walls)
	for _, room := range rooms {
		elements = append(elements, room)
	}
	
	return elements
}

// detectWalls finds walls using line detection
func (p *PhotoIngestion) detectWalls(imageData []byte) []*RecognizedSymbol {
	var walls []*RecognizedSymbol
	
	// This would use Hough line detection to find walls
	// For now, create example walls
	
	// Horizontal walls
	for i := 0; i < 3; i++ {
		wall := &RecognizedSymbol{
			Definition: &SymbolDefinition{
				ID:       fmt.Sprintf("wall_h_%d", i),
				Name:     "Wall",
				System:   "structural",
				Category: "structural",
				Tags:     []string{"wall", "structural"},
			},
			Position: Position{
				X: 0,
				Y: float64(i * 300),
				Z: 0,
			},
			Context:    "photo_structural",
			Confidence: 0.8,
		}
		walls = append(walls, wall)
	}
	
	// Vertical walls
	for i := 0; i < 4; i++ {
		wall := &RecognizedSymbol{
			Definition: &SymbolDefinition{
				ID:       fmt.Sprintf("wall_v_%d", i),
				Name:     "Wall",
				System:   "structural",
				Category: "structural",
				Tags:     []string{"wall", "structural"},
			},
			Position: Position{
				X: float64(i * 250),
				Y: 0,
				Z: 0,
			},
			Context:    "photo_structural",
			Confidence: 0.8,
		}
		walls = append(walls, wall)
	}
	
	return walls
}

// detectDoors finds door openings in walls
func (p *PhotoIngestion) detectDoors(walls []*RecognizedSymbol) []*RecognizedSymbol {
	var doors []*RecognizedSymbol
	
	// This would analyze gaps in walls to find doors
	// For now, create example doors
	
	door := &RecognizedSymbol{
		Definition: &SymbolDefinition{
			ID:       "door_main",
			Name:     "Door",
			System:   "architectural",
			Category: "architectural",
			Tags:     []string{"door", "entrance"},
		},
		Position: Position{
			X: 125,
			Y: 0,
			Z: 0,
		},
		Context:    "photo_door",
		Confidence: 0.7,
	}
	doors = append(doors, door)
	
	return doors
}

// detectRooms finds enclosed areas bounded by walls
func (p *PhotoIngestion) detectRooms(walls []*RecognizedSymbol) []*RecognizedSymbol {
	var rooms []*RecognizedSymbol
	
	// This would use contour detection to find enclosed areas
	// For now, create example rooms based on wall positions
	
	roomPositions := []struct {
		x, y float64
		name string
	}{
		{125, 150, "101"},
		{375, 150, "102"},
		{625, 150, "103"},
		{125, 450, "104"},
		{375, 450, "105"},
		{625, 450, "106"},
	}
	
	for _, pos := range roomPositions {
		room := &RecognizedSymbol{
			Definition: &SymbolDefinition{
				ID:       fmt.Sprintf("room_%s", pos.name),
				Name:     fmt.Sprintf("Room %s", pos.name),
				System:   "architectural",
				Category: "space",
				Tags:     []string{"room", "space"},
			},
			Position: Position{
				X: pos.x,
				Y: pos.y,
				Z: 0,
			},
			Context:    "photo_room",
			Confidence: 0.75,
			ParentSpace: "", // Rooms are top-level spaces
		}
		rooms = append(rooms, room)
	}
	
	return rooms
}

// extractTextElements performs OCR to extract text
func (p *PhotoIngestion) extractTextElements(imageData []byte) []TextElement {
	var elements []TextElement
	
	// This would use Tesseract or similar OCR engine
	// For now, create example text elements
	
	roomNumbers := []struct {
		x, y float64
		text string
	}{
		{125, 140, "101"},
		{375, 140, "102"},
		{625, 140, "103"},
		{125, 440, "104"},
		{375, 440, "105"},
		{625, 440, "106"},
	}
	
	for _, room := range roomNumbers {
		elements = append(elements, TextElement{
			Text:     room.text,
			Position: Point{X: room.x, Y: room.y},
			Type:     "room_number",
			Confidence: 0.9,
		})
	}
	
	// Add some labels
	elements = append(elements, TextElement{
		Text:     "Main Corridor",
		Position: Point{X: 375, Y: 50},
		Type:     "label",
		Confidence: 0.85,
	})
	
	elements = append(elements, TextElement{
		Text:     "Emergency Exit",
		Position: Point{X: 625, Y: 550},
		Type:     "annotation",
		Confidence: 0.8,
	})
	
	return elements
}

// adjustPosition adjusts position based on perspective correction
func (p *PhotoIngestion) adjustPosition(pos Position, perspectiveData *PerspectiveData) Position {
	// Apply perspective transform matrix
	if perspectiveData == nil || perspectiveData.TransformMatrix == nil {
		return pos
	}
	
	m := perspectiveData.TransformMatrix
	newX := m[0][0]*pos.X + m[0][1]*pos.Y + m[0][2]
	newY := m[1][0]*pos.X + m[1][1]*pos.Y + m[1][2]
	w := m[2][0]*pos.X + m[2][1]*pos.Y + m[2][2]
	
	if w != 0 {
		newX /= w
		newY /= w
	}
	
	return Position{
		X: newX * perspectiveData.Scale,
		Y: newY * perspectiveData.Scale,
		Z: pos.Z,
	}
}

// matchSymbolToRoom determines which room contains a symbol
func (p *PhotoIngestion) matchSymbolToRoom(symbol *RecognizedSymbol, textElements []TextElement) string {
	// Find nearest room number
	minDist := math.MaxFloat64
	nearestRoom := ""
	
	for _, text := range textElements {
		if text.Type != "room_number" {
			continue
		}
		
		dx := symbol.Position.X - text.Position.X
		dy := symbol.Position.Y - text.Position.Y
		dist := math.Sqrt(dx*dx + dy*dy)
		
		if dist < minDist {
			minDist = dist
			nearestRoom = fmt.Sprintf("room_%s", text.Text)
		}
	}
	
	// If too far from any room, mark as corridor or common area
	if minDist > 200 {
		return "corridor"
	}
	
	return nearestRoom
}

// createRoomFromText creates a room symbol from OCR text
func (p *PhotoIngestion) createRoomFromText(text TextElement) *RecognizedSymbol {
	return &RecognizedSymbol{
		Definition: &SymbolDefinition{
			ID:       fmt.Sprintf("room_%s", text.Text),
			Name:     fmt.Sprintf("Room %s", text.Text),
			System:   "architectural",
			Category: "space",
			Tags:     []string{"room", "space", "ocr"},
		},
		Position: Position{
			X: text.Position.X,
			Y: text.Position.Y,
			Z: 0,
		},
		Context:    "photo_ocr",
		Confidence: text.Confidence,
	}
}

// buildSpatialHierarchy creates parent-child relationships based on containment
func (p *PhotoIngestion) buildSpatialHierarchy(symbols []*RecognizedSymbol) {
	// Find all rooms
	var rooms []*RecognizedSymbol
	for _, symbol := range symbols {
		if symbol.Definition.Category == "space" {
			rooms = append(rooms, symbol)
		}
	}
	
	// Assign non-room symbols to their containing room
	for _, symbol := range symbols {
		if symbol.Definition.Category == "space" {
			continue // Skip rooms themselves
		}
		
		// Find containing room based on position
		for _, room := range rooms {
			if p.isInsideRoom(symbol.Position, room) {
				symbol.ParentSpace = room.Definition.ID
				break
			}
		}
	}
}

// isInsideRoom checks if a position is inside a room
func (p *PhotoIngestion) isInsideRoom(pos Position, room *RecognizedSymbol) bool {
	// Simplified check - would use proper polygon containment in production
	// Assume rooms are roughly 250x300 units
	roomX := room.Position.X
	roomY := room.Position.Y
	
	return pos.X >= roomX-125 && pos.X <= roomX+125 &&
	       pos.Y >= roomY-150 && pos.Y <= roomY+150
}

// inferConnections infers logical connections from spatial relationships
func (p *PhotoIngestion) inferConnections(symbols []*RecognizedSymbol) {
	// Group symbols by type
	symbolsByType := make(map[string][]*RecognizedSymbol)
	for _, symbol := range symbols {
		symbolsByType[symbol.Definition.System] = append(symbolsByType[symbol.Definition.System], symbol)
	}
	
	// Infer electrical connections based on alignment
	p.inferElectricalConnections(symbolsByType["electrical"])
	
	// Infer door-room relationships
	p.inferDoorConnections(symbols)
	
	// Infer HVAC zones
	p.inferHVACZones(symbolsByType["mechanical"])
}

// inferElectricalConnections infers electrical wiring from outlet/switch alignment
func (p *PhotoIngestion) inferElectricalConnections(electrical []*RecognizedSymbol) {
	if len(electrical) < 2 {
		return
	}
	
	// Sort by position for easier processing
	sort.Slice(electrical, func(i, j int) bool {
		if math.Abs(electrical[i].Position.Y-electrical[j].Position.Y) < 10 {
			return electrical[i].Position.X < electrical[j].Position.X
		}
		return electrical[i].Position.Y < electrical[j].Position.Y
	})
	
	// Connect aligned electrical components
	for i := 0; i < len(electrical)-1; i++ {
		s1 := electrical[i]
		s2 := electrical[i+1]
		
		// Check if horizontally or vertically aligned
		if p.areAligned(s1.Position, s2.Position, 20) { // 20 unit tolerance
			s1.Connections = append(s1.Connections, Connection{
				ToSymbolID: s2.Definition.ID,
				Type:       "electrical_feed",
				Properties: map[string]interface{}{
					"inferred": true,
					"confidence": 0.6,
				},
			})
		}
	}
}

// areAligned checks if two positions are aligned horizontally or vertically
func (p *PhotoIngestion) areAligned(pos1, pos2 Position, tolerance float64) bool {
	// Check horizontal alignment
	if math.Abs(pos1.Y-pos2.Y) < tolerance {
		return true
	}
	
	// Check vertical alignment
	if math.Abs(pos1.X-pos2.X) < tolerance {
		return true
	}
	
	return false
}

// inferDoorConnections connects doors to adjacent rooms
func (p *PhotoIngestion) inferDoorConnections(symbols []*RecognizedSymbol) {
	for _, symbol := range symbols {
		if symbol.Definition.ID == "door" || symbol.Definition.Category == "architectural" {
			// Find adjacent rooms
			for _, other := range symbols {
				if other.Definition.Category == "space" {
					// Check if door is on room boundary
					if p.isDoorOnRoomBoundary(symbol, other) {
						symbol.Connections = append(symbol.Connections, Connection{
							ToSymbolID: other.Definition.ID,
							Type:       "connects_to",
							Properties: map[string]interface{}{
								"access_type": "entrance",
							},
						})
					}
				}
			}
		}
	}
}

// isDoorOnRoomBoundary checks if a door is on a room's boundary
func (p *PhotoIngestion) isDoorOnRoomBoundary(door, room *RecognizedSymbol) bool {
	// Simplified check - would use proper boundary detection in production
	dx := math.Abs(door.Position.X - room.Position.X)
	dy := math.Abs(door.Position.Y - room.Position.Y)
	
	// Check if door is within boundary distance
	boundaryDist := 130.0 // Slightly more than room half-width
	return (dx < boundaryDist && dy < 20) || (dy < boundaryDist && dx < 20)
}

// inferHVACZones groups HVAC components into zones
func (p *PhotoIngestion) inferHVACZones(hvac []*RecognizedSymbol) {
	// Group nearby HVAC components into zones
	for i, h1 := range hvac {
		for j, h2 := range hvac {
			if i >= j {
				continue
			}
			
			// If components are in the same room or nearby
			if h1.ParentSpace == h2.ParentSpace && h1.ParentSpace != "" {
				h1.Connections = append(h1.Connections, Connection{
					ToSymbolID: h2.Definition.ID,
					Type:       "same_zone",
					Properties: map[string]interface{}{
						"zone": h1.ParentSpace,
					},
				})
			}
		}
	}
}

// filterByConfidence filters objects below confidence threshold
func (p *PhotoIngestion) filterByConfidence(objects []*arxoscore.ArxObject, threshold float64) []*arxoscore.ArxObject {
	var filtered []*arxoscore.ArxObject
	
	for _, obj := range objects {
		if obj.Confidence >= threshold {
			filtered = append(filtered, obj)
		} else {
			// Log low confidence objects for review
			fmt.Printf("Filtered low confidence object: %s (confidence: %.2f)\n", 
				obj.Name, obj.Confidence)
		}
	}
	
	return filtered
}