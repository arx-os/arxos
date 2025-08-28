package main

import (
	"context"
	"os"
	"path/filepath"
	"testing"
	"time"

	// Using local mock pipeline implementation
)

func TestProgressiveConstructionPipeline(t *testing.T) {
	// Setup test environment
	tempDir := t.TempDir()
	outputDir := filepath.Join(tempDir, "output")
	
	config := &PipelineConfig{
		EnableLiDARFusion:   true,
		RequiredAccuracy:    1.0,
		ConfidenceThreshold: 0.7,
		Generate3DMesh:      true,
		GenerateASCII:       false, // Skip ASCII for faster test
		ValidateAgainstCode: true,
		TempDirectory:       tempDir,
		OutputDirectory:     outputDir,
	}
	
	// Create directories
	if err := os.MkdirAll(outputDir, 0755); err != nil {
		t.Fatal("Failed to create output directory:", err)
	}
	
	// Initialize pipeline
	pcp := NewProgressiveConstructionPipeline(config)
	
	// Track progress for testing
	progressUpdates := make([]string, 0)
	pcp.SetProgressCallback(func(stage string, progress float64, message string) {
		progressUpdates = append(progressUpdates, stage)
		t.Logf("Progress [%s]: %.1f%% - %s", stage, progress*100, message)
	})
	
	// Create a mock PDF file for testing
	mockPDFPath := filepath.Join(tempDir, "test-floorplan.pdf")
	if err := createMockPDF(mockPDFPath); err != nil {
		t.Fatal("Failed to create mock PDF:", err)
	}
	
	// Process the mock PDF
	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()
	
	result, err := pcp.ProcessPDF(ctx, mockPDFPath, "test-building-001")
	
	// Validate results
	if err != nil {
		t.Fatalf("Pipeline processing failed: %v", err)
	}
	
	// Check that all stages were called
	expectedStages := []string{"validation", "pdf", "measurements", "lidar", "reconstruction", "complete"}
	for _, expectedStage := range expectedStages {
		found := false
		for _, actualStage := range progressUpdates {
			if actualStage == expectedStage {
				found = true
				break
			}
		}
		if !found {
			t.Errorf("Expected stage '%s' was not called", expectedStage)
		}
	}
	
	// Validate result structure
	if result == nil {
		t.Fatal("Result should not be nil")
	}
	
	if result.ProcessingTime == 0 {
		t.Error("Processing time should be greater than 0")
	}
	
	if len(result.StageResults) == 0 {
		t.Error("Should have stage results")
	}
	
	// Check that PDF stage succeeded (others might fail due to mock data)
	if pdfResult, exists := result.StageResults["pdf"]; exists && !pdfResult.Success {
		t.Errorf("PDF stage should succeed, got error: %v", pdfResult.Errors)
	}
	
	t.Logf("Pipeline completed successfully in %v", result.ProcessingTime)
	t.Logf("Created %d ArxObjects with overall confidence: %.2f", 
		len(result.ArxObjects), result.OverallConfidence)
}

func createMockPDF(path string) error {
	// Create a minimal PDF file for testing
	// In a real scenario, this would be a proper architectural drawing
	pdfContent := []byte(`%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>
endobj
xref
0 4
0000000000 65535 f 
0000000015 00000 n 
0000000060 00000 n 
0000000111 00000 n 
trailer
<< /Size 4 /Root 1 0 R >>
startxref
190
%%EOF`)
	
	return os.WriteFile(path, pdfContent, 0644)
}

func BenchmarkProgressiveConstructionPipeline(b *testing.B) {
	// Setup
	tempDir := b.TempDir()
	config := &PipelineConfig{
		EnableLiDARFusion:   false, // Disable for faster benchmark
		RequiredAccuracy:    5.0,   // Lower accuracy for speed
		ConfidenceThreshold: 0.5,
		Generate3DMesh:      false,
		GenerateASCII:       false,
		ValidateAgainstCode: false,
		TempDirectory:       tempDir,
		OutputDirectory:     filepath.Join(tempDir, "output"),
	}
	
	mockPDFPath := filepath.Join(tempDir, "benchmark.pdf")
	createMockPDF(mockPDFPath)
	
	b.ResetTimer()
	
	for i := 0; i < b.N; i++ {
		pcp := NewProgressiveConstructionPipeline(config)
		ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
		
		_, err := pcp.ProcessPDF(ctx, mockPDFPath, "benchmark-building")
		cancel()
		
		if err != nil {
			b.Fatal("Benchmark iteration failed:", err)
		}
	}
}