package ingestion

import (
	"context"
	"fmt"
	"testing"
	"time"
)

// TestPDFParser demonstrates the PDF parsing pipeline
func TestPDFParser(t *testing.T) {
	// Configuration for parsing
	config := PDFParserConfig{
		// Scale detection
		AutoDetectScale:    true,
		DefaultScaleFactor: 1.0, // 1 PDF unit = 1mm fallback
		
		// Precision settings
		CoordinatePrecision: 0.1,  // 0.1mm precision
		AngleTolerance:      1.0,   // 1 degree tolerance
		
		// Detection thresholds
		WallThickness:   300,        // 300mm max wall thickness
		MinWallLength:   500,        // 500mm minimum wall length
		SymbolSizeRange: [2]float64{50, 500}, // 5cm to 50cm symbols
		
		// Performance
		ParallelPages: true,
		MaxWorkers:    8,
		EnableGPU:     false,
		
		// Output
		BuildingID:       12345,
		FloorNumber:      1,
		CoordinateSystem: "local",
	}
	
	// Create parser
	parser := NewPDFToArxParser(config)
	
	// Simulate PDF data (in real use, this would be an actual PDF file)
	mockPDF := createMockPDF()
	
	// Parse PDF
	ctx := context.Background()
	startTime := time.Now()
	
	objects, err := parser.ParsePDF(ctx, mockPDF)
	if err != nil {
		t.Fatalf("Failed to parse PDF: %v", err)
	}
	
	elapsed := time.Since(startTime)
	
	// Print results
	fmt.Printf("=== PDF Parsing Results ===\n")
	fmt.Printf("Processing time: %v\n", elapsed)
	fmt.Printf("Objects created: %d\n", len(objects))
	fmt.Printf("Pages processed: %d\n", parser.stats.PagesProcessed)
	fmt.Printf("Vectors extracted: %d\n", parser.stats.VectorsExtracted)
	fmt.Printf("Walls detected: %d\n", parser.stats.WallsDetected)
	fmt.Printf("Symbols recognized: %d\n", parser.stats.SymbolsRecognized)
	fmt.Printf("Text labels extracted: %d\n", parser.stats.TextExtracted)
	
	// Analyze object types
	typeCount := make(map[uint8]int)
	systemCount := make(map[uint8]int)
	scaleCount := make(map[uint8]int)
	
	for _, obj := range objects {
		typeCount[obj.GetType()]++
		systemCount[obj.GetSystem()]++
		scaleCount[obj.GetScale()]++
	}
	
	fmt.Printf("\n=== Object Analysis ===\n")
	fmt.Printf("Types: %v\n", typeCount)
	fmt.Printf("Systems: %v\n", systemCount)
	fmt.Printf("Scale levels: %v\n", scaleCount)
	
	// Sample object details
	if len(objects) > 0 {
		fmt.Printf("\n=== Sample Object (First Wall) ===\n")
		obj := objects[0]
		fmt.Printf("ID: %d\n", obj.ID)
		fmt.Printf("Position: (%d, %d, %d) nanometers\n", obj.X, obj.Y, obj.Z)
		fmt.Printf("Position: (%.2f, %.2f, %.2f) meters\n", 
			float64(obj.X)/1e9, float64(obj.Y)/1e9, float64(obj.Z)/1e9)
		fmt.Printf("Dimensions: %.2f x %.2f x %.2f mm\n",
			float64(obj.Length)/1e6, float64(obj.Width)/1e6, float64(obj.Height)/1e6)
		fmt.Printf("Type: %d, System: %d, Scale: %d\n", 
			obj.GetType(), obj.GetSystem(), obj.GetScale())
	}
	
	// Performance metrics
	fmt.Printf("\n=== Performance Metrics ===\n")
	if elapsed.Seconds() > 0 {
		fmt.Printf("Objects/second: %.0f\n", float64(len(objects))/elapsed.Seconds())
		fmt.Printf("Vectors/second: %.0f\n", float64(parser.stats.VectorsExtracted)/elapsed.Seconds())
	}
	
	// Memory usage
	fmt.Printf("Memory per object: %d bytes\n", 128) // ArxObjectOptimized size
	fmt.Printf("Total memory: %.2f MB\n", float64(len(objects)*128)/(1024*1024))
}

// createMockPDF creates simulated PDF data for testing
func createMockPDF() *MockPDFReader {
	return &MockPDFReader{
		data: []byte("mock PDF data"),
	}
}

type MockPDFReader struct {
	data []byte
	pos  int
}

func (m *MockPDFReader) Read(p []byte) (n int, err error) {
	if m.pos >= len(m.data) {
		return 0, io.EOF
	}
	n = copy(p, m.data[m.pos:])
	m.pos += n
	return n, nil
}

// BenchmarkPDFParsing benchmarks the parsing performance
func BenchmarkPDFParsing(b *testing.B) {
	config := PDFParserConfig{
		AutoDetectScale:    false,
		DefaultScaleFactor: 1.0,
		WallThickness:      300,
		MinWallLength:      500,
		ParallelPages:      true,
		MaxWorkers:         8,
	}
	
	parser := NewPDFToArxParser(config)
	ctx := context.Background()
	mockPDF := createMockPDF()
	
	b.ResetTimer()
	b.ReportAllocs()
	
	for i := 0; i < b.N; i++ {
		mockPDF.pos = 0 // Reset reader
		_, _ = parser.ParsePDF(ctx, mockPDF)
	}
	
	b.ReportMetric(float64(parser.stats.ObjectsCreated)/b.Elapsed().Seconds(), "objects/sec")
}

// TestScaleDetection tests automatic scale detection
func TestScaleDetection(t *testing.T) {
	detector := NewScaleDetector()
	
	testCases := []struct {
		name     string
		vectors  []Path
		expected float64
	}{
		{
			name: "Standard door width",
			vectors: []Path{
				{Points: []Point2D{{0, 0}, {900, 0}}}, // 900 PDF units = 900mm door
			},
			expected: 1.0,
		},
		{
			name: "1:100 scale",
			vectors: []Path{
				{Points: []Point2D{{0, 0}, {9, 0}}}, // 9 PDF units = 900mm door at 1:100
			},
			expected: 100.0,
		},
	}
	
	for _, tc := range testCases {
		t.Run(tc.name, func(t *testing.T) {
			scale := detector.DetectScale(tc.vectors, nil)
			if scale != tc.expected {
				t.Errorf("Expected scale %f, got %f", tc.expected, scale)
			}
		})
	}
}

// TestWallDetection tests wall detection algorithm
func TestWallDetection(t *testing.T) {
	config := PDFParserConfig{
		WallThickness:  300,
		MinWallLength:  500,
		AngleTolerance: 1.0,
	}
	
	detector := NewWallDetector(config)
	
	// Create test vectors representing walls
	vectors := []Path{
		// Horizontal wall (two parallel lines)
		{Points: []Point2D{{0, 0}, {1000, 0}}, StrokeWidth: 1},
		{Points: []Point2D{{0, 200}, {1000, 200}}, StrokeWidth: 1},
		
		// Vertical wall
		{Points: []Point2D{{0, 0}, {0, 1000}}, StrokeWidth: 1},
		{Points: []Point2D{{200, 0}, {200, 1000}}, StrokeWidth: 1},
	}
	
	walls := detector.DetectWalls(vectors, 1.0)
	
	if len(walls) != 2 {
		t.Errorf("Expected 2 walls, got %d", len(walls))
	}
	
	// Check wall properties
	for i, wall := range walls {
		fmt.Printf("Wall %d: Start(%.1f,%.1f) End(%.1f,%.1f) Thickness:%.1fmm\n",
			i, wall.Start.X, wall.Start.Y, wall.End.X, wall.End.Y, wall.Thickness)
	}
}

// TestSymbolRecognition tests symbol pattern matching
func TestSymbolRecognition(t *testing.T) {
	recognizer := NewSymbolRecognizer()
	
	// Create test vectors representing an electrical outlet symbol
	vectors := []Path{
		// Circle
		{Points: makeCircle(100, 100, 25), Closed: true},
		// Two vertical lines (outlet slots)
		{Points: []Point2D{{90, 95}, {90, 105}}},
		{Points: []Point2D{{110, 95}, {110, 105}}},
	}
	
	symbols := recognizer.RecognizeSymbols(vectors, "electrical")
	
	if len(symbols) > 0 {
		fmt.Printf("Recognized %d symbols\n", len(symbols))
		for _, sym := range symbols {
			fmt.Printf("Symbol: %s at (%.1f,%.1f)\n", sym.Type, sym.Position.X, sym.Position.Y)
		}
	}
}

// Helper function to create circle points
func makeCircle(cx, cy, radius float64) []Point2D {
	points := make([]Point2D, 0, 36)
	for i := 0; i < 36; i++ {
		angle := float64(i) * 10 * math.Pi / 180
		x := cx + radius*math.Cos(angle)
		y := cy + radius*math.Sin(angle)
		points = append(points, Point2D{x, y})
	}
	return points
}

// TestMortonEncoding tests spatial indexing
func TestMortonEncoding(t *testing.T) {
	encoder := NewMortonEncoder()
	
	// Test that nearby points have similar Morton codes
	morton1 := encoder.Encode(1000000000, 1000000000, 0) // 1m, 1m, 0
	morton2 := encoder.Encode(1001000000, 1001000000, 0) // 1.001m, 1.001m, 0
	morton3 := encoder.Encode(5000000000, 5000000000, 0) // 5m, 5m, 0
	
	// Nearby points should have closer Morton codes
	diff12 := abs(int64(morton1) - int64(morton2))
	diff13 := abs(int64(morton1) - int64(morton3))
	
	if diff12 >= diff13 {
		t.Errorf("Morton encoding not preserving spatial locality: near(%d) far(%d)", diff12, diff13)
	}
	
	fmt.Printf("Morton codes: 1m=%d, 1.001m=%d, 5m=%d\n", morton1, morton2, morton3)
}

func abs(x int64) int64 {
	if x < 0 {
		return -x
	}
	return x
}