package formats

import (
	"bytes"
	"context"
	"crypto/md5"
	"encoding/hex"
	"fmt"
	"image"
	"io"
	"os"
	"path/filepath"
	"regexp"
	"strings"
	"sync"
	"time"

	"github.com/arx-os/arxos/internal/common/logger"
	"github.com/arx-os/arxos/internal/core/building"
	"github.com/arx-os/arxos/internal/core/equipment"
	"github.com/arx-os/arxos/internal/importer"
	"github.com/google/uuid"
	"github.com/pdfcpu/pdfcpu/v3/pkg/api"
	"github.com/pdfcpu/pdfcpu/v3/pkg/pdfcpu"
	"github.com/pdfcpu/pdfcpu/v3/pkg/pdfcpu/model"
)

// EnhancedPDFImporter provides advanced PDF import capabilities
type EnhancedPDFImporter struct {
	textExtractor   *PDFTextExtractor
	imageExtractor  *PDFImageExtractor
	ocrEngine      *OCREngine
	diagramParser  *DiagramParser
	nlpProcessor   *NLPProcessor
	confidenceCalc *AdvancedConfidenceScorer
	cache          *ExtractionCache
	mu             sync.RWMutex
}

// NewEnhancedPDFImporter creates a new enhanced PDF importer
func NewEnhancedPDFImporter() (*EnhancedPDFImporter, error) {
	ocrEngine, err := NewOCREngine()
	if err != nil {
		logger.Warn("OCR engine not available: %v", err)
		// Continue without OCR - graceful degradation
		ocrEngine = nil
	}

	return &EnhancedPDFImporter{
		textExtractor:   NewPDFTextExtractor(),
		imageExtractor:  NewPDFImageExtractor(),
		ocrEngine:      ocrEngine,
		diagramParser:  NewDiagramParser(),
		nlpProcessor:   NewNLPProcessor(),
		confidenceCalc: NewAdvancedConfidenceScorer(),
		cache:          NewExtractionCache(100), // Cache last 100 extractions
	}, nil
}

// GetFormat returns the format name
func (p *EnhancedPDFImporter) GetFormat() string {
	return "pdf-enhanced"
}

// GetCapabilities returns enhanced importer capabilities
func (p *EnhancedPDFImporter) GetCapabilities() importer.ImportCapabilities {
	return importer.ImportCapabilities{
		SupportsSpatial:    true,  // Can extract from diagrams
		SupportsHierarchy:  true,
		SupportsMetadata:   true,
		SupportsConfidence: true,
		SupportsStreaming:  false,
		MaxFileSize:        500 * 1024 * 1024, // 500MB limit
	}
}

// ImportToModel converts PDF to building model with enhanced extraction
func (p *EnhancedPDFImporter) ImportToModel(ctx context.Context, input io.Reader, opts importer.ImportOptions) (*building.BuildingModel, error) {
	logger.Info("Starting enhanced PDF import for building: %s", opts.BuildingName)

	// Check cache first
	cacheKey := p.generateCacheKey(input)
	if cached, ok := p.cache.Get(cacheKey); ok {
		logger.Info("Using cached extraction for PDF")
		return cached.(*building.BuildingModel), nil
	}

	// Save input to temporary file for processing
	tmpFile, err := p.saveToTempFile(input)
	if err != nil {
		return nil, fmt.Errorf("failed to save PDF: %w", err)
	}
	defer os.Remove(tmpFile)

	// Extract all content types in parallel
	extractionResult, err := p.extractAll(ctx, tmpFile)
	if err != nil {
		return nil, fmt.Errorf("extraction failed: %w", err)
	}

	// Process extracted content
	processedData, err := p.processExtraction(ctx, extractionResult)
	if err != nil {
		return nil, fmt.Errorf("processing failed: %w", err)
	}

	// Build the model
	model, err := p.buildModel(processedData, opts)
	if err != nil {
		return nil, fmt.Errorf("model building failed: %w", err)
	}

	// Calculate and set confidence score
	confidence := p.confidenceCalc.Calculate(processedData)
	p.setModelConfidence(model, confidence)

	// Cache the result
	p.cache.Set(cacheKey, model)

	logger.Info("Enhanced PDF import complete: %d floors, %d rooms, %d equipment items, confidence: %.2f",
		len(model.Floors), len(model.Rooms), len(model.Equipment), confidence.Overall)

	return model, nil
}

// ExtractionResult contains all extracted content
type ExtractionResult struct {
	Text     string
	Images   []ExtractedImage
	Tables   []ExtractedTable
	Metadata map[string]string
}

// ExtractedImage represents an extracted image
type ExtractedImage struct {
	Data   []byte
	Format string
	Page   int
	Bounds image.Rectangle
}

// ExtractedTable represents an extracted table
type ExtractedTable struct {
	Headers []string
	Rows    [][]string
	Page    int
}

// ProcessedData contains processed extraction results
type ProcessedData struct {
	Floors      []ProcessedFloor
	Equipment   []ProcessedEquipment
	Spatial     []SpatialData
	Metadata    map[string]interface{}
	Diagrams    []ProcessedDiagram
	TextQuality float64
}

// ProcessedFloor represents a processed floor
type ProcessedFloor struct {
	ID          uuid.UUID
	Level       int
	Name        string
	Rooms       []ProcessedRoom
	Area        float64
	Height      float64
	Boundaries  [][]float64 // Polygon coordinates if extracted from diagram
	Metadata    map[string]interface{}
}

// ProcessedRoom represents a processed room
type ProcessedRoom struct {
	ID         uuid.UUID
	Number     string
	Name       string
	Type       string
	Area       float64
	Boundaries [][]float64 // Polygon coordinates if extracted from diagram
	Equipment  []string    // Equipment IDs in this room
	Metadata   map[string]interface{}
}

// ProcessedEquipment represents processed equipment
type ProcessedEquipment struct {
	ID           uuid.UUID
	Name         string
	Type         string
	Location     SpatialLocation
	Manufacturer string
	Model        string
	SerialNumber string
	InstallDate  *time.Time
	Metadata     map[string]interface{}
}

// SpatialLocation represents spatial location data
type SpatialLocation struct {
	Floor    string
	Room     string
	Position *Position3D
}

// Position3D represents 3D position
type Position3D struct {
	X, Y, Z float64
}

// SpatialData represents extracted spatial information
type SpatialData struct {
	Type       string // "floor_plan", "equipment_location", etc.
	Geometry   interface{}
	Properties map[string]interface{}
}

// ProcessedDiagram represents a processed diagram
type ProcessedDiagram struct {
	Type     string // "floor_plan", "equipment_layout", "electrical", etc.
	Page     int
	Elements []DiagramElement
}

// DiagramElement represents an element in a diagram
type DiagramElement struct {
	Type       string
	Geometry   interface{}
	Properties map[string]interface{}
}

// extractAll performs parallel extraction of all content types
func (p *EnhancedPDFImporter) extractAll(ctx context.Context, pdfPath string) (*ExtractionResult, error) {
	result := &ExtractionResult{
		Metadata: make(map[string]string),
	}

	var wg sync.WaitGroup
	var extractErr error
	var mu sync.Mutex

	// Extract text
	wg.Add(1)
	go func() {
		defer wg.Done()
		text, metadata, err := p.textExtractor.ExtractEnhanced(pdfPath)
		mu.Lock()
		defer mu.Unlock()
		if err != nil {
			extractErr = fmt.Errorf("text extraction failed: %w", err)
			return
		}
		result.Text = text
		for k, v := range metadata {
			result.Metadata[k] = v
		}
	}()

	// Extract images
	wg.Add(1)
	go func() {
		defer wg.Done()
		images, err := p.imageExtractor.ExtractImages(pdfPath)
		mu.Lock()
		defer mu.Unlock()
		if err != nil {
			logger.Warn("Image extraction failed: %v", err)
			return
		}
		result.Images = images
	}()

	// Extract tables
	wg.Add(1)
	go func() {
		defer wg.Done()
		tables, err := p.extractTables(pdfPath)
		mu.Lock()
		defer mu.Unlock()
		if err != nil {
			logger.Warn("Table extraction failed: %v", err)
			return
		}
		result.Tables = tables
	}()

	// Wait for all extractions to complete
	wg.Wait()

	if extractErr != nil {
		return nil, extractErr
	}

	// If text is minimal and we have images, try OCR
	if p.needsOCR(result.Text, result.Images) && p.ocrEngine != nil {
		ocrText, err := p.ocrEngine.ProcessImages(result.Images)
		if err == nil {
			result.Text += "\n\n--- OCR Extracted Text ---\n" + ocrText
			result.Metadata["ocr_applied"] = "true"
		}
	}

	return result, nil
}

// processExtraction processes the extracted content
func (p *EnhancedPDFImporter) processExtraction(ctx context.Context, extraction *ExtractionResult) (*ProcessedData, error) {
	processed := &ProcessedData{
		Metadata: make(map[string]interface{}),
	}

	// Process text with NLP
	if extraction.Text != "" {
		nlpResult, err := p.nlpProcessor.Process(extraction.Text)
		if err == nil {
			processed.Floors = nlpResult.Floors
			processed.Equipment = nlpResult.Equipment
			processed.TextQuality = p.assessTextQuality(extraction.Text)
		}
	}

	// Process images for diagrams
	for _, img := range extraction.Images {
		if p.diagramParser.IsDiagram(img) {
			diagram, err := p.diagramParser.Parse(img)
			if err == nil {
				processed.Diagrams = append(processed.Diagrams, diagram)
				// Extract spatial data from diagrams
				if spatial := p.extractSpatialFromDiagram(diagram); spatial != nil {
					processed.Spatial = append(processed.Spatial, *spatial)
				}
			}
		}
	}

	// Process tables for equipment lists
	for _, table := range extraction.Tables {
		if equipment := p.extractEquipmentFromTable(table); len(equipment) > 0 {
			processed.Equipment = append(processed.Equipment, equipment...)
		}
	}

	// Merge and deduplicate data
	processed = p.mergeAndDeduplicate(processed)

	// Copy metadata
	for k, v := range extraction.Metadata {
		processed.Metadata[k] = v
	}

	return processed, nil
}

// buildModel builds the building model from processed data
func (p *EnhancedPDFImporter) buildModel(data *ProcessedData, opts importer.ImportOptions) (*building.BuildingModel, error) {
	buildingID := opts.BuildingID
	if buildingID == uuid.Nil {
		buildingID = uuid.New()
	}

	buildingName := opts.BuildingName
	if buildingName == "" {
		buildingName = "Imported Building"
		if name, ok := data.Metadata["building_name"].(string); ok {
			buildingName = name
		}
	}

	bldg := building.NewBuilding(buildingID, buildingName)
	bldg.Metadata = data.Metadata

	model := building.NewBuildingModel(bldg)
	model.ImportMetadata.Format = building.DataSourcePDF
	model.ImportMetadata.ImportedAt = time.Now()
	model.ImportMetadata.SourceFile = opts.FileName

	// Add floors
	for _, floor := range data.Floors {
		f := building.Floor{
			ID:         floor.ID,
			BuildingID: buildingID,
			Level:      floor.Level,
			Name:       floor.Name,
			Metadata:   floor.Metadata,
		}

		if floor.Area > 0 {
			f.Metadata["area"] = floor.Area
		}
		if floor.Height > 0 {
			f.Metadata["height"] = floor.Height
		}
		if len(floor.Boundaries) > 0 {
			f.Metadata["boundaries"] = floor.Boundaries
		}

		model.AddFloor(f)

		// Add rooms for this floor
		for _, room := range floor.Rooms {
			r := building.Room{
				ID:         room.ID,
				BuildingID: buildingID,
				FloorID:    floor.ID,
				Name:       room.Name,
				Type:       room.Type,
				Area:       room.Area,
				Metadata:   room.Metadata,
			}

			if room.Number != "" {
				r.Metadata["room_number"] = room.Number
			}
			if len(room.Boundaries) > 0 {
				r.Metadata["boundaries"] = room.Boundaries
			}

			model.AddRoom(r)
		}
	}

	// Add equipment
	for _, eq := range data.Equipment {
		equip := &equipment.Equipment{
			ID:         eq.ID,
			BuildingID: buildingID,
			Name:       eq.Name,
			Type:       eq.Type,
			Status:     equipment.StatusOperational,
			Metadata:   eq.Metadata,
		}

		// Set location if available
		if eq.Location.Floor != "" {
			equip.Metadata["floor"] = eq.Location.Floor
		}
		if eq.Location.Room != "" {
			equip.Metadata["room"] = eq.Location.Room
		}
		if eq.Location.Position != nil {
			equip.Metadata["position"] = map[string]float64{
				"x": eq.Location.Position.X,
				"y": eq.Location.Position.Y,
				"z": eq.Location.Position.Z,
			}
		}

		// Set manufacturer info
		if eq.Manufacturer != "" {
			equip.Metadata["manufacturer"] = eq.Manufacturer
		}
		if eq.Model != "" {
			equip.Metadata["model"] = eq.Model
		}
		if eq.SerialNumber != "" {
			equip.Metadata["serial_number"] = eq.SerialNumber
		}
		if eq.InstallDate != nil {
			equip.Metadata["install_date"] = eq.InstallDate.Format(time.RFC3339)
		}

		model.AddEquipment(equip)
	}

	// Add spatial data if available
	if len(data.Spatial) > 0 {
		model.Building.Metadata["spatial_data"] = data.Spatial
	}

	return model, nil
}

// Helper functions

func (p *EnhancedPDFImporter) saveToTempFile(input io.Reader) (string, error) {
	tmpFile, err := os.CreateTemp("", "pdf_import_*.pdf")
	if err != nil {
		return "", err
	}
	defer tmpFile.Close()

	if _, err := io.Copy(tmpFile, input); err != nil {
		os.Remove(tmpFile.Name())
		return "", err
	}

	return tmpFile.Name(), nil
}

func (p *EnhancedPDFImporter) generateCacheKey(input io.Reader) string {
	h := md5.New()
	io.Copy(h, input)
	return hex.EncodeToString(h.Sum(nil))
}

func (p *EnhancedPDFImporter) needsOCR(text string, images []ExtractedImage) bool {
	// Need OCR if text is minimal but we have images
	textWords := len(strings.Fields(text))
	return textWords < 100 && len(images) > 0
}

func (p *EnhancedPDFImporter) assessTextQuality(text string) float64 {
	// Simple text quality assessment
	score := 0.0
	factors := 0

	// Check text length
	if len(text) > 1000 {
		score += 1.0
		factors++
	}

	// Check for structure indicators
	if strings.Contains(strings.ToLower(text), "floor") ||
		strings.Contains(strings.ToLower(text), "level") {
		score += 1.0
		factors++
	}

	// Check for equipment mentions
	if regexp.MustCompile(`(?i)(hvac|electrical|plumbing|equipment)`).MatchString(text) {
		score += 1.0
		factors++
	}

	// Check for room information
	if regexp.MustCompile(`(?i)(room|suite|office|space)`).MatchString(text) {
		score += 1.0
		factors++
	}

	if factors == 0 {
		return 0.0
	}

	return score / float64(factors)
}

func (p *EnhancedPDFImporter) extractTables(pdfPath string) ([]ExtractedTable, error) {
	// Basic table extraction - would be enhanced with proper library
	var tables []ExtractedTable

	// This is a placeholder - in production, use a proper PDF table extraction library
	// like tabula-go or similar

	return tables, nil
}

func (p *EnhancedPDFImporter) extractEquipmentFromTable(table ExtractedTable) []ProcessedEquipment {
	var equipment []ProcessedEquipment

	// Look for equipment-related headers
	hasEquipmentData := false
	nameCol, typeCol, locationCol := -1, -1, -1

	for i, header := range table.Headers {
		headerLower := strings.ToLower(header)
		if strings.Contains(headerLower, "name") || strings.Contains(headerLower, "description") {
			nameCol = i
			hasEquipmentData = true
		}
		if strings.Contains(headerLower, "type") || strings.Contains(headerLower, "category") {
			typeCol = i
		}
		if strings.Contains(headerLower, "location") || strings.Contains(headerLower, "room") {
			locationCol = i
		}
	}

	if !hasEquipmentData {
		return equipment
	}

	// Extract equipment from rows
	for _, row := range table.Rows {
		eq := ProcessedEquipment{
			ID:       uuid.New(),
			Metadata: make(map[string]interface{}),
		}

		if nameCol >= 0 && nameCol < len(row) {
			eq.Name = row[nameCol]
		}
		if typeCol >= 0 && typeCol < len(row) {
			eq.Type = p.normalizeEquipmentType(row[typeCol])
		}
		if locationCol >= 0 && locationCol < len(row) {
			eq.Location.Room = row[locationCol]
		}

		if eq.Name != "" {
			equipment = append(equipment, eq)
		}
	}

	return equipment
}

func (p *EnhancedPDFImporter) normalizeEquipmentType(typeStr string) string {
	typeStr = strings.ToLower(strings.TrimSpace(typeStr))

	// Map common variations to standard types
	typeMap := map[string]string{
		"hvac":         "hvac",
		"air handler":  "hvac",
		"ahu":          "hvac",
		"vav":          "hvac",
		"electrical":   "electrical",
		"panel":        "electrical",
		"lighting":     "lighting",
		"plumbing":     "plumbing",
		"fire":         "fire_safety",
		"security":     "security",
		"sensor":       "sensor",
		"thermostat":   "sensor",
	}

	for key, value := range typeMap {
		if strings.Contains(typeStr, key) {
			return value
		}
	}

	return "other"
}

func (p *EnhancedPDFImporter) extractSpatialFromDiagram(diagram ProcessedDiagram) *SpatialData {
	if diagram.Type != "floor_plan" || len(diagram.Elements) == 0 {
		return nil
	}

	spatial := &SpatialData{
		Type:       "floor_plan",
		Properties: make(map[string]interface{}),
	}

	// Extract geometry from diagram elements
	var geometries []interface{}
	for _, elem := range diagram.Elements {
		if elem.Geometry != nil {
			geometries = append(geometries, elem.Geometry)
		}
	}

	if len(geometries) > 0 {
		spatial.Geometry = geometries
		spatial.Properties["page"] = diagram.Page
		return spatial
	}

	return nil
}

func (p *EnhancedPDFImporter) mergeAndDeduplicate(data *ProcessedData) *ProcessedData {
	// Deduplicate equipment by name and type
	equipmentMap := make(map[string]ProcessedEquipment)
	for _, eq := range data.Equipment {
		key := fmt.Sprintf("%s:%s", eq.Name, eq.Type)
		if existing, ok := equipmentMap[key]; ok {
			// Merge metadata
			for k, v := range eq.Metadata {
				existing.Metadata[k] = v
			}
			equipmentMap[key] = existing
		} else {
			equipmentMap[key] = eq
		}
	}

	// Convert back to slice
	data.Equipment = make([]ProcessedEquipment, 0, len(equipmentMap))
	for _, eq := range equipmentMap {
		data.Equipment = append(data.Equipment, eq)
	}

	return data
}

func (p *EnhancedPDFImporter) setModelConfidence(model *building.BuildingModel, confidence ConfidenceScore) {
	// Set overall confidence
	var confLevel building.ConfidenceLevel
	switch {
	case confidence.Overall >= 80:
		confLevel = building.ConfidenceHigh
	case confidence.Overall >= 60:
		confLevel = building.ConfidenceMedium
	case confidence.Overall >= 40:
		confLevel = building.ConfidenceLow
	default:
		confLevel = building.ConfidenceEstimated
	}

	// Store detailed confidence scores
	model.Building.Metadata["confidence"] = map[string]interface{}{
		"level":     confLevel,
		"overall":   confidence.Overall,
		"text":      confidence.Text,
		"structure": confidence.Structure,
		"equipment": confidence.Equipment,
		"metadata":  confidence.Metadata,
	}

	// Set confidence for equipment
	for _, eq := range model.Equipment {
		switch confLevel {
		case building.ConfidenceHigh:
			eq.Confidence = equipment.ConfidenceHigh
		case building.ConfidenceMedium:
			eq.Confidence = equipment.ConfidenceMedium
		case building.ConfidenceLow:
			eq.Confidence = equipment.ConfidenceLow
		default:
			eq.Confidence = equipment.ConfidenceEstimated
		}
	}
}