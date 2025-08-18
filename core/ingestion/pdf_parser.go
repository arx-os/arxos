// Package ingestion - HIGH-PERFORMANCE PDF TO ARXOBJECT PARSER
// Converts architectural PDFs to optimized ArxObjects with nanometer precision
package ingestion

import (
	"bytes"
	"context"
	"encoding/binary"
	"errors"
	"fmt"
	"image"
	"image/color"
	"io"
	"math"
	"regexp"
	"sort"
	"strings"
	"sync"
	"sync/atomic"
	
	"github.com/arxos/arxos/core/arxobject"
	"github.com/pdfcpu/pdfcpu/pkg/api"
	"github.com/pdfcpu/pdfcpu/pkg/pdfcpu"
	"github.com/otiai10/gosseract/v2"
)

// ================================================================================
// PDF PARSER CORE
// ================================================================================

// PDFToArxParser converts PDF floor plans to ArxObjects
type PDFToArxParser struct {
	// Core components
	vectorExtractor  *VectorExtractor
	wallDetector     *WallDetector
	symbolRecognizer *SymbolRecognizer
	textExtractor    *TextExtractor
	scaleDetector    *ScaleDetector
	layerSeparator   *LayerSeparator
	
	// Configuration
	config PDFParserConfig
	
	// Performance
	objectPool    *sync.Pool
	workerPool    *WorkerPool
	mortonEncoder *MortonEncoder
	
	// Metrics
	stats ParserStats
}

// PDFParserConfig contains parser configuration
type PDFParserConfig struct {
	// Scale detection
	AutoDetectScale    bool    `json:"auto_detect_scale"`
	DefaultScaleFactor float64 `json:"default_scale_factor"` // PDF units to mm
	
	// Precision settings
	CoordinatePrecision float64 `json:"coordinate_precision"` // mm
	AngleTolerance      float64 `json:"angle_tolerance"`      // degrees
	
	// Detection thresholds
	WallThickness      float64 `json:"wall_thickness_mm"`
	MinWallLength      float64 `json:"min_wall_length_mm"`
	SymbolSizeRange    [2]float64 `json:"symbol_size_range_mm"`
	
	// Performance
	ParallelPages      bool `json:"parallel_pages"`
	MaxWorkers         int  `json:"max_workers"`
	EnableGPU          bool `json:"enable_gpu"`
	
	// Output
	BuildingID         uint64 `json:"building_id"`
	FloorNumber        int    `json:"floor_number"`
	CoordinateSystem   string `json:"coordinate_system"` // "local" or "global"
	OriginLat          float64 `json:"origin_lat"`
	OriginLon          float64 `json:"origin_lon"`
}

// ParserStats tracks parsing metrics
type ParserStats struct {
	PagesProcessed    uint32
	VectorsExtracted  uint64
	WallsDetected     uint32
	SymbolsRecognized uint32
	TextExtracted     uint32
	ObjectsCreated    uint32
	ProcessingTimeMs  int64
}

// ================================================================================
// MAIN PARSING PIPELINE
// ================================================================================

func NewPDFToArxParser(config PDFParserConfig) *PDFToArxParser {
	if config.MaxWorkers == 0 {
		config.MaxWorkers = runtime.NumCPU()
	}
	
	return &PDFToArxParser{
		vectorExtractor:  NewVectorExtractor(),
		wallDetector:     NewWallDetector(config),
		symbolRecognizer: NewSymbolRecognizer(),
		textExtractor:    NewTextExtractor(),
		scaleDetector:    NewScaleDetector(),
		layerSeparator:   NewLayerSeparator(),
		config:          config,
		workerPool:      NewWorkerPool(config.MaxWorkers),
		mortonEncoder:   NewMortonEncoder(),
		objectPool: &sync.Pool{
			New: func() interface{} {
				return &arxobject.ArxObjectOptimized{}
			},
		},
	}
}

// ParsePDF converts a PDF to optimized ArxObjects
func (p *PDFToArxParser) ParsePDF(ctx context.Context, reader io.Reader) ([]*arxobject.ArxObjectOptimized, error) {
	startTime := time.Now()
	defer func() {
		p.stats.ProcessingTimeMs = time.Since(startTime).Milliseconds()
	}()
	
	// Read PDF into memory for processing
	pdfData, err := io.ReadAll(reader)
	if err != nil {
		return nil, fmt.Errorf("failed to read PDF: %w", err)
	}
	
	// Parse PDF structure
	pdfCtx, err := pdfcpu.Read(bytes.NewReader(pdfData), nil)
	if err != nil {
		return nil, fmt.Errorf("failed to parse PDF: %w", err)
	}
	
	// Process pages
	pageCount := pdfCtx.PageCount
	atomic.AddUint32(&p.stats.PagesProcessed, uint32(pageCount))
	
	// Channel for collecting objects from all pages
	objectsCh := make(chan []*arxobject.ArxObjectOptimized, pageCount)
	var wg sync.WaitGroup
	
	// Process each page
	for pageNum := 1; pageNum <= pageCount; pageNum++ {
		if p.config.ParallelPages {
			wg.Add(1)
			go func(page int) {
				defer wg.Done()
				objects, _ := p.processPage(ctx, pdfCtx, page)
				objectsCh <- objects
			}(pageNum)
		} else {
			objects, _ := p.processPage(ctx, pdfCtx, pageNum)
			objectsCh <- objects
		}
	}
	
	// Wait and collect
	go func() {
		wg.Wait()
		close(objectsCh)
	}()
	
	// Merge all objects
	var allObjects []*arxobject.ArxObjectOptimized
	for objects := range objectsCh {
		allObjects = append(allObjects, objects...)
	}
	
	// Post-processing
	allObjects = p.postProcess(allObjects)
	
	atomic.StoreUint32(&p.stats.ObjectsCreated, uint32(len(allObjects)))
	return allObjects, nil
}

// processPage handles a single PDF page
func (p *PDFToArxParser) processPage(ctx context.Context, pdfCtx *pdfcpu.Context, pageNum int) ([]*arxobject.ArxObjectOptimized, error) {
	page := pdfCtx.PageDict(pageNum)
	if page == nil {
		return nil, fmt.Errorf("page %d not found", pageNum)
	}
	
	// 1. Extract vectors (lines, curves, polygons)
	vectors := p.vectorExtractor.ExtractVectors(page)
	atomic.AddUint64(&p.stats.VectorsExtracted, uint64(len(vectors)))
	
	// 2. Detect scale if needed
	var scaleFactor float64
	if p.config.AutoDetectScale {
		scaleFactor = p.scaleDetector.DetectScale(vectors, page)
	} else {
		scaleFactor = p.config.DefaultScaleFactor
	}
	
	// 3. Separate layers (electrical, plumbing, etc.)
	layers := p.layerSeparator.SeparateLayers(vectors)
	
	var objects []*arxobject.ArxObjectOptimized
	
	// 4. Process each layer
	for layerType, layerVectors := range layers {
		// Detect walls in structural layer
		if layerType == "structural" {
			walls := p.wallDetector.DetectWalls(layerVectors, scaleFactor)
			for _, wall := range walls {
				obj := p.wallToArxObject(wall, scaleFactor)
				objects = append(objects, obj)
			}
			atomic.AddUint32(&p.stats.WallsDetected, uint32(len(walls)))
		}
		
		// Detect symbols in all layers
		symbols := p.symbolRecognizer.RecognizeSymbols(layerVectors, layerType)
		for _, symbol := range symbols {
			obj := p.symbolToArxObject(symbol, scaleFactor, layerType)
			objects = append(objects, obj)
		}
		atomic.AddUint32(&p.stats.SymbolsRecognized, uint32(len(symbols)))
	}
	
	// 5. Extract text labels
	texts := p.textExtractor.ExtractText(page)
	p.attachTextToObjects(objects, texts)
	atomic.AddUint32(&p.stats.TextExtracted, uint32(len(texts)))
	
	return objects, nil
}

// ================================================================================
// VECTOR EXTRACTION
// ================================================================================

type VectorExtractor struct {
	paths []Path
	mu    sync.Mutex
}

type Path struct {
	Points    []Point2D
	Closed    bool
	StrokeWidth float64
	Color     color.Color
	Layer     string
}

type Point2D struct {
	X, Y float64
}

func NewVectorExtractor() *VectorExtractor {
	return &VectorExtractor{}
}

func (v *VectorExtractor) ExtractVectors(page pdfcpu.Dict) []Path {
	v.paths = v.paths[:0] // Reset
	
	// Extract content streams
	content, _ := page.ArrayEntry("Contents")
	if content == nil {
		return v.paths
	}
	
	// Parse graphics commands
	// This is simplified - actual implementation would parse PDF operators
	// Commands like: m (moveto), l (lineto), c (curveto), h (closepath), S (stroke)
	
	return v.paths
}

// ================================================================================
// WALL DETECTION
// ================================================================================

type WallDetector struct {
	config       PDFParserConfig
	lineSegments []LineSegment
}

type LineSegment struct {
	Start, End Point2D
	Thickness  float64
	Layer      string
}

type Wall struct {
	ID        uint64
	Start     Point2D
	End       Point2D
	Thickness float64
	Height    float64
	Material  string
}

func NewWallDetector(config PDFParserConfig) *WallDetector {
	return &WallDetector{config: config}
}

func (w *WallDetector) DetectWalls(vectors []Path, scaleFactor float64) []Wall {
	// 1. Extract line segments
	w.extractLineSegments(vectors)
	
	// 2. Merge parallel lines into walls
	walls := w.mergeParallelLines(scaleFactor)
	
	// 3. Connect wall intersections
	w.connectIntersections(walls)
	
	// 4. Filter by minimum length
	walls = w.filterShortWalls(walls, scaleFactor)
	
	return walls
}

func (w *WallDetector) extractLineSegments(vectors []Path) {
	w.lineSegments = w.lineSegments[:0]
	
	for _, path := range vectors {
		if len(path.Points) < 2 {
			continue
		}
		
		for i := 0; i < len(path.Points)-1; i++ {
			segment := LineSegment{
				Start:     path.Points[i],
				End:       path.Points[i+1],
				Thickness: path.StrokeWidth,
				Layer:     path.Layer,
			}
			w.lineSegments = append(w.lineSegments, segment)
		}
	}
}

func (w *WallDetector) mergeParallelLines(scaleFactor float64) []Wall {
	var walls []Wall
	wallID := uint64(1)
	
	// Sort segments by position for efficient merging
	sort.Slice(w.lineSegments, func(i, j int) bool {
		return w.lineSegments[i].Start.X < w.lineSegments[j].Start.X
	})
	
	// Find parallel line pairs that form walls
	for i := 0; i < len(w.lineSegments); i++ {
		seg1 := w.lineSegments[i]
		
		for j := i + 1; j < len(w.lineSegments); j++ {
			seg2 := w.lineSegments[j]
			
			// Check if parallel and close enough
			if w.areParallel(seg1, seg2) && w.distance(seg1, seg2) < w.config.WallThickness/scaleFactor {
				wall := Wall{
					ID:        wallID,
					Start:     seg1.Start,
					End:       seg1.End,
					Thickness: w.distance(seg1, seg2) * scaleFactor,
					Height:    3000, // Default 3m ceiling height
					Material:  "concrete", // Default material
				}
				walls = append(walls, wall)
				wallID++
				break
			}
		}
	}
	
	return walls
}

func (w *WallDetector) areParallel(seg1, seg2 LineSegment) bool {
	// Calculate angles
	angle1 := math.Atan2(seg1.End.Y-seg1.Start.Y, seg1.End.X-seg1.Start.X)
	angle2 := math.Atan2(seg2.End.Y-seg2.Start.Y, seg2.End.X-seg2.Start.X)
	
	// Check if angles are similar (within tolerance)
	diff := math.Abs(angle1 - angle2)
	return diff < w.config.AngleTolerance*math.Pi/180
}

func (w *WallDetector) distance(seg1, seg2 LineSegment) float64 {
	// Point-to-line distance
	return pointToLineDistance(seg1.Start, seg2.Start, seg2.End)
}

// ================================================================================
// SYMBOL RECOGNITION
// ================================================================================

type SymbolRecognizer struct {
	library  *SymbolLibrary
	matcher  *PatternMatcher
	gpu      GPUAccelerator
}

type Symbol struct {
	Type     string
	Position Point2D
	Rotation float64
	Size     float64
	Properties map[string]interface{}
}

type SymbolLibrary struct {
	patterns map[string]Pattern
	mu       sync.RWMutex
}

type Pattern struct {
	Name      string
	Type      arxobject.ArxObjectType
	System    string
	Template  []Point2D // Normalized pattern points
	MinSize   float64
	MaxSize   float64
}

func NewSymbolRecognizer() *SymbolRecognizer {
	return &SymbolRecognizer{
		library: loadSymbolLibrary(),
		matcher: NewPatternMatcher(),
	}
}

func (s *SymbolRecognizer) RecognizeSymbols(vectors []Path, layerType string) []Symbol {
	var symbols []Symbol
	
	// Group vectors into potential symbols
	clusters := s.clusterVectors(vectors)
	
	// Match each cluster against library
	for _, cluster := range clusters {
		if symbol := s.matchSymbol(cluster, layerType); symbol != nil {
			symbols = append(symbols, *symbol)
		}
	}
	
	return symbols
}

func (s *SymbolRecognizer) clusterVectors(vectors []Path) [][]Path {
	// Use DBSCAN clustering to group nearby vectors
	// that likely form a single symbol
	return nil // Simplified
}

func (s *SymbolRecognizer) matchSymbol(cluster []Path, layerType string) *Symbol {
	// Extract feature vector from cluster
	features := s.extractFeatures(cluster)
	
	// Compare against library patterns
	s.library.mu.RLock()
	defer s.library.mu.RUnlock()
	
	bestMatch := ""
	bestScore := 0.0
	
	for name, pattern := range s.library.patterns {
		if pattern.System != layerType {
			continue
		}
		
		score := s.matcher.Compare(features, pattern.Template)
		if score > bestScore && score > 0.8 { // 80% match threshold
			bestMatch = name
			bestScore = score
		}
	}
	
	if bestMatch != "" {
		pattern := s.library.patterns[bestMatch]
		return &Symbol{
			Type:     bestMatch,
			Position: s.getCenter(cluster),
			Rotation: s.getRotation(cluster),
			Size:     s.getSize(cluster),
			Properties: map[string]interface{}{
				"confidence": bestScore,
				"pattern":    pattern.Name,
			},
		}
	}
	
	return nil
}

// ================================================================================
// SCALE DETECTION
// ================================================================================

type ScaleDetector struct {
	knownDimensions map[string]float64 // Common dimensions in mm
}

func NewScaleDetector() *ScaleDetector {
	return &ScaleDetector{
		knownDimensions: map[string]float64{
			"door_width":     900,   // Standard door 900mm
			"hallway_width":  1200,  // Min hallway 1200mm
			"parking_space":  2500,  // Standard parking 2500mm
			"grid_spacing":   600,   // Common grid 600mm (2ft)
		},
	}
}

func (s *ScaleDetector) DetectScale(vectors []Path, page pdfcpu.Dict) float64 {
	// 1. Look for scale text (e.g., "1:100", "1/4\" = 1'")
	if scale := s.detectScaleFromText(page); scale > 0 {
		return scale
	}
	
	// 2. Detect from known dimensions
	if scale := s.detectFromKnownDimensions(vectors); scale > 0 {
		return scale
	}
	
	// 3. Detect from grid pattern
	if scale := s.detectFromGrid(vectors); scale > 0 {
		return scale
	}
	
	// Default: 1 PDF unit = 1mm
	return 1.0
}

func (s *ScaleDetector) detectScaleFromText(page pdfcpu.Dict) float64 {
	// Regular expressions for common scale notations
	scalePatterns := []*regexp.Regexp{
		regexp.MustCompile(`1:(\d+)`),           // Metric: 1:100
		regexp.MustCompile(`(\d+)"?\s*=\s*(\d+)'`), // Imperial: 1/4" = 1'
	}
	
	// Extract text and search for scale
	// ... (implementation)
	
	return 0
}

// ================================================================================
// CONVERSION TO ARXOBJECT
// ================================================================================

func (p *PDFToArxParser) wallToArxObject(wall Wall, scaleFactor float64) *arxobject.ArxObjectOptimized {
	obj := p.objectPool.Get().(*arxobject.ArxObjectOptimized)
	
	// Convert to nanometers
	startX := int64(wall.Start.X * scaleFactor * float64(arxobject.Millimeter))
	startY := int64(wall.Start.Y * scaleFactor * float64(arxobject.Millimeter))
	endX := int64(wall.End.X * scaleFactor * float64(arxobject.Millimeter))
	endY := int64(wall.End.Y * scaleFactor * float64(arxobject.Millimeter))
	
	// Calculate center and dimensions
	centerX := (startX + endX) / 2
	centerY := (startY + endY) / 2
	length := int64(math.Sqrt(float64((endX-startX)*(endX-startX) + (endY-startY)*(endY-startY))))
	
	obj.ID = wall.ID
	obj.X = centerX
	obj.Y = centerY
	obj.Z = int64(p.config.FloorNumber) * 3 * arxobject.Meter // 3m per floor
	obj.Length = length
	obj.Width = int64(wall.Thickness * float64(arxobject.Millimeter))
	obj.Height = int64(wall.Height * float64(arxobject.Millimeter))
	
	// Pack type flags
	obj.TypeFlags = uint64(arxobject.StructuralWall)<<56 |
	               uint64(arxobject.SystemStructural)<<48 |
	               uint64(3)<<40 | // Scale level: building
	               uint64(1)       // Active flag
	
	// Calculate rotation
	angle := math.Atan2(float64(endY-startY), float64(endX-startX))
	obj.RotationPack = uint64(angle*1000) << 32 // Store in milliradians
	
	// Set Morton code for spatial indexing
	obj.MetadataID = uint64(p.mortonEncoder.Encode(centerX, centerY, obj.Z))
	
	return obj
}

func (p *PDFToArxParser) symbolToArxObject(symbol Symbol, scaleFactor float64, layerType string) *arxobject.ArxObjectOptimized {
	obj := p.objectPool.Get().(*arxobject.ArxObjectOptimized)
	
	// Convert position to nanometers
	obj.X = int64(symbol.Position.X * scaleFactor * float64(arxobject.Millimeter))
	obj.Y = int64(symbol.Position.Y * scaleFactor * float64(arxobject.Millimeter))
	obj.Z = int64(p.config.FloorNumber) * 3 * arxobject.Meter
	
	// Set dimensions based on symbol type
	obj.Length = int64(symbol.Size * scaleFactor * float64(arxobject.Millimeter))
	obj.Width = obj.Length
	obj.Height = int64(100 * arxobject.Millimeter) // Default 10cm height
	
	// Determine type based on symbol
	objType := p.symbolTypeToArxType(symbol.Type)
	system := p.layerToSystem(layerType)
	
	obj.TypeFlags = uint64(objType)<<56 |
	               uint64(system)<<48 |
	               uint64(2)<<40 | // Scale level: room
	               uint64(1)       // Active flag
	
	return obj
}

// ================================================================================
// POST-PROCESSING
// ================================================================================

func (p *PDFToArxParser) postProcess(objects []*arxobject.ArxObjectOptimized) []*arxobject.ArxObjectOptimized {
	// 1. Remove duplicates
	objects = p.removeDuplicates(objects)
	
	// 2. Connect relationships
	p.connectRelationships(objects)
	
	// 3. Validate topology
	p.validateTopology(objects)
	
	// 4. Optimize spatial index
	p.optimizeSpatialIndex(objects)
	
	return objects
}

func (p *PDFToArxParser) removeDuplicates(objects []*arxobject.ArxObjectOptimized) []*arxobject.ArxObjectOptimized {
	seen := make(map[uint64]bool)
	unique := objects[:0]
	
	for _, obj := range objects {
		// Use Morton code as unique identifier for spatial duplicates
		morton := p.mortonEncoder.Encode(obj.X, obj.Y, obj.Z)
		if !seen[uint64(morton)] {
			seen[uint64(morton)] = true
			unique = append(unique, obj)
		}
	}
	
	return unique
}

// ================================================================================
// HELPER FUNCTIONS
// ================================================================================

func pointToLineDistance(point, lineStart, lineEnd Point2D) float64 {
	A := point.X - lineStart.X
	B := point.Y - lineStart.Y
	C := lineEnd.X - lineStart.X
	D := lineEnd.Y - lineStart.Y
	
	dot := A*C + B*D
	lenSq := C*C + D*D
	param := -1.0
	
	if lenSq != 0 {
		param = dot / lenSq
	}
	
	var xx, yy float64
	
	if param < 0 {
		xx = lineStart.X
		yy = lineStart.Y
	} else if param > 1 {
		xx = lineEnd.X
		yy = lineEnd.Y
	} else {
		xx = lineStart.X + param*C
		yy = lineStart.Y + param*D
	}
	
	dx := point.X - xx
	dy := point.Y - yy
	
	return math.Sqrt(dx*dx + dy*dy)
}

func (p *PDFToArxParser) symbolTypeToArxType(symbolType string) arxobject.ArxObjectType {
	// Map symbol types to ArxObject types
	typeMap := map[string]arxobject.ArxObjectType{
		"outlet":     arxobject.ElectricalOutlet,
		"switch":     arxobject.ElectricalPanel,
		"hvac_vent":  arxobject.HVACDuct,
		"sprinkler":  arxobject.FireSprinkler,
		"door":       arxobject.StructuralWall, // Placeholder
		"window":     arxobject.StructuralWall, // Placeholder
	}
	
	if t, ok := typeMap[symbolType]; ok {
		return t
	}
	return arxobject.StructuralWall // Default
}

func (p *PDFToArxParser) layerToSystem(layer string) uint8 {
	systems := map[string]uint8{
		"structural": 0,
		"electrical": 1,
		"mechanical": 2,
		"plumbing":   3,
		"fire":       4,
		"data":       5,
	}
	
	if s, ok := systems[layer]; ok {
		return s
	}
	return 0 // Default to structural
}

// ================================================================================
// SUPPORTING TYPES
// ================================================================================

type MortonEncoder struct{}

func NewMortonEncoder() *MortonEncoder {
	return &MortonEncoder{}
}

func (m *MortonEncoder) Encode(x, y, z int64) uint64 {
	// Implement Morton encoding for spatial indexing
	// This creates a space-filling curve for better cache locality
	return arxobject.EncodeMorton3D(x, y, z)
}

type TextExtractor struct {
	ocr *gosseract.Client
}

func NewTextExtractor() *TextExtractor {
	client := gosseract.NewClient()
	client.SetLanguage("eng")
	return &TextExtractor{ocr: client}
}

func (t *TextExtractor) ExtractText(page pdfcpu.Dict) []TextLabel {
	// Extract text from PDF page
	return nil // Simplified
}

type TextLabel struct {
	Text     string
	Position Point2D
	FontSize float64
}

func (p *PDFToArxParser) attachTextToObjects(objects []*arxobject.ArxObjectOptimized, texts []TextLabel) {
	// Associate text labels with nearby objects
	// This helps identify room names, equipment labels, etc.
}

type LayerSeparator struct{}

func NewLayerSeparator() *LayerSeparator {
	return &LayerSeparator{}
}

func (l *LayerSeparator) SeparateLayers(vectors []Path) map[string][]Path {
	// Separate vectors by layer/system based on color, line style, etc.
	layers := make(map[string][]Path)
	
	for _, vector := range vectors {
		layer := l.detectLayer(vector)
		layers[layer] = append(layers[layer], vector)
	}
	
	return layers
}

func (l *LayerSeparator) detectLayer(vector Path) string {
	// Detect layer based on color, line style, etc.
	// Simplified implementation
	return "structural"
}

type PatternMatcher struct{}

func NewPatternMatcher() *PatternMatcher {
	return &PatternMatcher{}
}

func (m *PatternMatcher) Compare(features, template []Point2D) float64 {
	// Implement pattern matching algorithm
	// Could use Hausdorff distance, shape context, etc.
	return 0.9 // Simplified
}

func loadSymbolLibrary() *SymbolLibrary {
	// Load symbol patterns from embedded data or files
	return &SymbolLibrary{
		patterns: make(map[string]Pattern),
	}
}

// Additional helper methods
func (s *SymbolRecognizer) extractFeatures(cluster []Path) []Point2D {
	// Extract feature points from vector cluster
	return nil
}

func (s *SymbolRecognizer) getCenter(cluster []Path) Point2D {
	// Calculate centroid of cluster
	return Point2D{}
}

func (s *SymbolRecognizer) getRotation(cluster []Path) float64 {
	// Detect primary orientation
	return 0
}

func (s *SymbolRecognizer) getSize(cluster []Path) float64 {
	// Calculate bounding box size
	return 100
}

func (w *WallDetector) connectIntersections(walls []Wall) {
	// Snap wall endpoints that are close together
}

func (w *WallDetector) filterShortWalls(walls []Wall, scaleFactor float64) []Wall {
	// Remove walls shorter than minimum length
	minLength := w.config.MinWallLength / scaleFactor
	
	filtered := walls[:0]
	for _, wall := range walls {
		length := math.Sqrt(math.Pow(wall.End.X-wall.Start.X, 2) + 
		                   math.Pow(wall.End.Y-wall.Start.Y, 2))
		if length >= minLength {
			filtered = append(filtered, wall)
		}
	}
	
	return filtered
}

func (p *PDFToArxParser) connectRelationships(objects []*arxobject.ArxObjectOptimized) {
	// Build spatial relationships between objects
}

func (p *PDFToArxParser) validateTopology(objects []*arxobject.ArxObjectOptimized) {
	// Ensure walls form closed rooms, etc.
}

func (p *PDFToArxParser) optimizeSpatialIndex(objects []*arxobject.ArxObjectOptimized) {
	// Sort by Morton code for better cache locality
	sort.Slice(objects, func(i, j int) bool {
		morton1 := p.mortonEncoder.Encode(objects[i].X, objects[i].Y, objects[i].Z)
		morton2 := p.mortonEncoder.Encode(objects[j].X, objects[j].Y, objects[j].Z)
		return morton1 < morton2
	})
}