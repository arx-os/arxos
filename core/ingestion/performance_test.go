package ingestion

import (
	"fmt"
	"os"
	"testing"
	"time"

	"github.com/arxos/core/cgo"
)

// ============================================================================
// PERFORMANCE BENCHMARKS
// ============================================================================

// BenchmarkIngestionPipelineCreation measures pipeline creation performance
func BenchmarkIngestionPipelineCreation(b *testing.B) {
	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		pipeline := NewIngestionPipelineCGO()
		pipeline.Close()
	}
}

// BenchmarkFormatDetection measures format detection performance
func BenchmarkFormatDetection(b *testing.B) {
	pipeline := NewIngestionPipelineCGO()
	defer pipeline.Close()
	
	testFiles := []string{
		"test.pdf",
		"test.ifc",
		"test.dwg",
		"test.jpg",
		"test.xlsx",
		"test.las",
	}
	
	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		for _, file := range testFiles {
			pipeline.DetectFormat(file)
		}
	}
}

// BenchmarkFileProcessing measures file processing performance
func BenchmarkFileProcessing(b *testing.B) {
	pipeline := NewIngestionPipelineCGO()
	defer pipeline.Close()
	
	options := GetDefaultOptions()
	
	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		// Test with a sample file path
		pipeline.ProcessFile("test.pdf", options)
	}
}

// BenchmarkMetadataExtraction measures metadata extraction performance
func BenchmarkMetadataExtraction(b *testing.B) {
	pipeline := NewIngestionPipelineCGO()
	defer pipeline.Close()
	
	testFiles := []string{
		"test.pdf",
		"test.ifc",
		"test.dwg",
		"test.jpg",
		"test.xlsx",
		"test.las",
	}
	
	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		for _, file := range testFiles {
			pipeline.GetMetadata(file)
		}
	}
}

// BenchmarkStatisticsRetrieval measures statistics retrieval performance
func BenchmarkStatisticsRetrieval(b *testing.B) {
	pipeline := NewIngestionPipelineCGO()
	defer pipeline.Close()
	
	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		pipeline.GetStatistics()
	}
}

// ============================================================================
// COMPREHENSIVE PERFORMANCE TESTS
// ============================================================================

// TestIngestionPipelinePerformance provides comprehensive performance testing
func TestIngestionPipelinePerformance(t *testing.T) {
	if testing.Short() {
		t.Skip("Skipping performance test in short mode")
	}
	
	t.Run("Pipeline Creation Performance", func(t *testing.T) {
		start := time.Now()
		pipeline := NewIngestionPipelineCGO()
		creationTime := time.Since(start)
		
		t.Logf("Pipeline creation time: %v", creationTime)
		
		// Verify pipeline was created successfully
		if pipeline == nil {
			t.Fatal("Failed to create pipeline")
		}
		
		// Test CGO availability
		t.Logf("CGO bridge available: %v", pipeline.hasCGO)
		
		pipeline.Close()
	})
	
	t.Run("Format Detection Performance", func(t *testing.T) {
		pipeline := NewIngestionPipelineCGO()
		defer pipeline.Close()
		
		testCases := []struct {
			filename string
			expected ArxFileFormat
		}{
			{"test.pdf", ArxFormatPDF},
			{"test.ifc", ArxFormatIFC},
			{"test.dwg", ArxFormatDWG},
			{"test.jpg", ArxFormatImage},
			{"test.xlsx", ArxFormatExcel},
			{"test.las", ArxFormatLiDAR},
			{"test.unknown", ArxFormatUnknown},
		}
		
		for _, tc := range testCases {
			start := time.Now()
			format := pipeline.DetectFormat(tc.filename)
			detectionTime := time.Since(start)
			
			t.Logf("Format detection for %s: %v (expected: %v) in %v", 
				tc.filename, format, tc.expected, detectionTime)
			
			if format != tc.expected {
				t.Errorf("Expected format %v for %s, got %v", tc.expected, tc.filename, format)
			}
		}
	})
	
	t.Run("File Processing Performance", func(t *testing.T) {
		pipeline := NewIngestionPipelineCGO()
		defer pipeline.Close()
		
		options := GetDefaultOptions()
		
		testFiles := []string{
			"test.pdf",
			"test.ifc",
			"test.dwg",
			"test.jpg",
			"test.xlsx",
			"test.las",
		}
		
		for _, filename := range testFiles {
			start := time.Now()
			result, err := pipeline.ProcessFile(filename, options)
			processingTime := time.Since(start)
			
			t.Logf("Processing %s: %v in %v", filename, err, processingTime)
			
			// Since we don't have actual test files, we expect errors
			// In a real test environment, we would have sample files
			if err == nil && result != nil {
				t.Logf("Successfully processed %s: %d objects, confidence: %.2f", 
					filename, result.ObjectCount, result.OverallConfidence)
			}
		}
	})
	
	t.Run("Statistics Performance", func(t *testing.T) {
		pipeline := NewIngestionPipelineCGO()
		defer pipeline.Close()
		
		start := time.Now()
		stats := pipeline.GetStatistics()
		retrievalTime := time.Since(start)
		
		t.Logf("Statistics retrieval time: %v", retrievalTime)
		t.Logf("Statistics: %s", stats)
		
		// Test clearing statistics
		start = time.Now()
		pipeline.ClearStatistics()
		clearTime := time.Since(start)
		
		t.Logf("Statistics clear time: %v", clearTime)
	})
}

// TestCGOBridgeFallback tests fallback functionality when CGO bridge fails
func TestCGOBridgeFallback(t *testing.T) {
	t.Run("Fallback Format Detection", func(t *testing.T) {
		pipeline := NewIngestionPipelineCGO()
		defer pipeline.Close()
		
		// Test fallback format detection
		format := pipeline.fallbackDetectFormat("test.pdf")
		if format != ArxFormatPDF {
			t.Errorf("Expected PDF format, got %v", format)
		}
		
		format = pipeline.fallbackDetectFormat("test.ifc")
		if format != ArxFormatIFC {
			t.Errorf("Expected IFC format, got %v", format)
		}
		
		format = pipeline.fallbackDetectFormat("test.unknown")
		if format != ArxFormatUnknown {
			t.Errorf("Expected unknown format, got %v", format)
		}
	})
	
	t.Run("Fallback Metadata Extraction", func(t *testing.T) {
		pipeline := NewIngestionPipelineCGO()
		defer pipeline.Close()
		
		metadata, err := pipeline.fallbackGetMetadata("test.pdf")
		if err != nil {
			t.Errorf("Unexpected error in fallback metadata: %v", err)
		}
		
		if metadata == nil {
			t.Fatal("Expected metadata, got nil")
		}
		
		if metadata.Format != ArxFormatPDF {
			t.Errorf("Expected PDF format, got %v", metadata.Format)
		}
		
		if metadata.Filename != "test.pdf" {
			t.Errorf("Expected filename 'test.pdf', got '%s'", metadata.Filename)
		}
	})
}

// TestIngestionOptions tests ingestion options functionality
func TestIngestionOptions(t *testing.T) {
	t.Run("Default Options", func(t *testing.T) {
		options := GetDefaultOptions()
		
		if options == nil {
			t.Fatal("Expected default options, got nil")
		}
		
		// Verify default values
		if !options.EnableMerging {
			t.Error("Expected EnableMerging to be true")
		}
		
		if options.MinConfidence != 0.7 {
			t.Errorf("Expected MinConfidence 0.7, got %f", options.MinConfidence)
		}
		
		if !options.RequireValidation {
			t.Error("Expected RequireValidation to be true")
		}
		
		if options.MaxObjectsPerFile != 1000 {
			t.Errorf("Expected MaxObjectsPerFile 1000, got %d", options.MaxObjectsPerFile)
		}
		
		if !options.EnableCaching {
			t.Error("Expected EnableCaching to be true")
		}
	})
	
	t.Run("Options Validation", func(t *testing.T) {
		// Test valid options
		validOptions := GetDefaultOptions()
		if err := ValidateOptions(validOptions); err != nil {
			t.Errorf("Valid options should not produce error: %v", err)
		}
		
		// Test nil options
		if err := ValidateOptions(nil); err != ErrNilOptions {
			t.Errorf("Expected ErrNilOptions, got %v", err)
		}
		
		// Test invalid confidence
		invalidConfidence := GetDefaultOptions()
		invalidConfidence.MinConfidence = 1.5
		if err := ValidateOptions(invalidConfidence); err != ErrInvalidConfidence {
			t.Errorf("Expected ErrInvalidConfidence, got %v", err)
		}
		
		// Test invalid max objects
		invalidMaxObjects := GetDefaultOptions()
		invalidMaxObjects.MaxObjectsPerFile = 0
		if err := ValidateOptions(invalidMaxObjects); err != ErrInvalidMaxObjects {
			t.Errorf("Expected ErrInvalidMaxObjects, got %v", err)
		}
	})
}

// TestFileFormatEnum tests the file format enumeration
func TestFileFormatEnum(t *testing.T) {
	t.Run("Format String Representation", func(t *testing.T) {
		testCases := []struct {
			format ArxFileFormat
			expected string
		}{
			{ArxFormatPDF, "PDF"},
			{ArxFormatIFC, "IFC"},
			{ArxFormatDWG, "DWG"},
			{ArxFormatImage, "Image"},
			{ArxFormatExcel, "Excel"},
			{ArxFormatLiDAR, "LiDAR"},
			{ArxFormatUnknown, "Unknown"},
		}
		
		for _, tc := range testCases {
			result := tc.format.String()
			if result != tc.expected {
				t.Errorf("Expected '%s' for format %d, got '%s'", tc.expected, tc.format, result)
			}
		}
	})
	
	t.Run("Format Validation", func(t *testing.T) {
		validFormats := []ArxFileFormat{
			ArxFormatPDF, ArxFormatIFC, ArxFormatDWG, ArxFormatImage, ArxFormatExcel, ArxFormatLiDAR,
		}
		
		for _, format := range validFormats {
			if !format.IsValid() {
				t.Errorf("Format %v should be valid", format)
			}
		}
		
		invalidFormats := []ArxFileFormat{
			ArxFormatUnknown,
			ArxFileFormat(99),
			ArxFileFormat(-1),
		}
		
		for _, format := range invalidFormats {
			if format.IsValid() {
				t.Errorf("Format %v should be invalid", format)
			}
		}
	})
}

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

// createTestFile creates a temporary test file for testing
func createTestFile(t *testing.T, content string) string {
	tmpfile, err := os.CreateTemp("", "test_*.txt")
	if err != nil {
		t.Fatalf("Failed to create temp file: %v", err)
	}
	
	if _, err := tmpfile.Write([]byte(content)); err != nil {
		t.Fatalf("Failed to write to temp file: %v", err)
	}
	
	if err := tmpfile.Close(); err != nil {
		t.Fatalf("Failed to close temp file: %v", err)
	}
	
	return tmpfile.Name()
}

// cleanupTestFile removes a test file
func cleanupTestFile(filename string) {
	os.Remove(filename)
}

// TestMain sets up and tears down the test environment
func TestMain(m *testing.M) {
	// Check if CGO bridge is available
	if cgo.HasCGOBridge() {
		fmt.Println("CGO bridge available - running full tests")
	} else {
		fmt.Println("CGO bridge not available - running fallback tests only")
	}
	
	// Run tests
	code := m.Run()
	
	// Cleanup
	os.Exit(code)
}
