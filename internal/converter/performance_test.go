package converter

import (
	"bytes"
	"context"
	"fmt"
	"os"
	"strings"
	"testing"
	"time"
)

func TestStreamingPDFConverter_Performance(t *testing.T) {
	// Create a large test input
	largeInput := createLargeTextInput(1000) // 1000 rooms

	config := &PerformanceConfig{
		MaxMemoryMB:     100, // 100MB limit
		BufferSize:      32 * 1024,
		MaxGoroutines:   4,
		EnableProfiling: true,
	}

	converter := NewStreamingPDFConverter(config)

	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()

	var output bytes.Buffer
	input := strings.NewReader(largeInput)

	start := time.Now()
	err := converter.ConvertToBIMStreaming(ctx, input, &output)
	duration := time.Since(start)

	if err != nil {
		t.Fatalf("Streaming conversion failed: %v", err)
	}

	// Verify performance metrics
	metrics := converter.GetMetrics()

	if metrics.LinesProcessed == 0 {
		t.Error("No lines were processed")
	}

	if metrics.RoomsExtracted < 900 { // Should extract most rooms
		t.Errorf("Expected at least 900 rooms, got %d", metrics.RoomsExtracted)
	}

	t.Logf("Performance: %s", metrics.String())

	// Performance expectations
	if duration > 10*time.Second {
		t.Errorf("Conversion took too long: %v", duration)
	}

	// Memory should be reasonable
	peakMemoryMB := float64(metrics.PeakMemoryBytes) / (1024 * 1024)
	if peakMemoryMB > 150 { // Allow some overhead over the 100MB limit
		t.Errorf("Peak memory usage too high: %.2f MB", peakMemoryMB)
	}
}

func TestMemoryPool(t *testing.T) {
	pool := NewMemoryPool(1024)

	// Get and put buffers
	buf1 := pool.Get()
	buf2 := pool.Get()

	if len(buf1) != 1024 {
		t.Errorf("Expected buffer size 1024, got %d", len(buf1))
	}

	if len(buf2) != 1024 {
		t.Errorf("Expected buffer size 1024, got %d", len(buf2))
	}

	// Return buffers
	pool.Put(buf1)
	pool.Put(buf2)

	// Get again - should reuse
	buf3 := pool.Get()
	if len(buf3) != 1024 {
		t.Errorf("Expected reused buffer size 1024, got %d", len(buf3))
	}
}

func TestPerformanceConfig(t *testing.T) {
	config := DefaultPerformanceConfig()

	if config.MaxMemoryMB <= 0 {
		t.Error("MaxMemoryMB should be positive")
	}

	if config.BufferSize <= 0 {
		t.Error("BufferSize should be positive")
	}

	if config.MaxGoroutines <= 0 {
		t.Error("MaxGoroutines should be positive")
	}
}

func TestConcurrentProcessing(t *testing.T) {
	config := &PerformanceConfig{
		MaxMemoryMB:   50,
		BufferSize:    16 * 1024,
		MaxGoroutines: 2,
	}

	converter := NewStreamingPDFConverter(config)

	// Create input with different room types
	input := `ROOM 101 - Conference Room - 250 sq ft
ROOM 102 - Office Space - 150 sq ft
IDF 103A - Telecom Closet
MDF 104B - Main Distribution Frame
SUITE 201 - Executive Office - 300 sq ft
OFFICE 202 - Manager Office`

	chunks := strings.Split(input, "\n")
	textChunks := make([]string, len(chunks))
	for i, line := range chunks {
		textChunks[i] = line
	}

	ctx := context.Background()
	rooms, _ := converter.processChunksConcurrently(ctx, textChunks)

	// Should find all rooms
	if len(rooms) < 6 {
		t.Errorf("Expected at least 6 rooms, got %d", len(rooms))
	}

	// Verify room types are correctly inferred
	telecomCount := 0
	for _, room := range rooms {
		if room["type"] == "telecom" {
			telecomCount++
		}
	}

	if telecomCount < 2 { // IDF and MDF
		t.Errorf("Expected at least 2 telecom rooms, got %d", telecomCount)
	}
}

func TestMemoryLimitEnforcement(t *testing.T) {
	config := &PerformanceConfig{
		MaxMemoryMB:   1, // Very low limit to trigger enforcement
		BufferSize:    1024,
		MaxGoroutines: 1,
	}

	converter := NewStreamingPDFConverter(config)

	// This should trigger memory limit checking
	err := converter.checkMemoryLimit()

	// The exact behavior depends on current memory usage, but it shouldn't panic
	if err != nil {
		t.Logf("Memory limit enforcement triggered: %v", err)
	}
}

func TestStreamingOutput(t *testing.T) {
	building := &Building{
		Name: "Test Building",
		Metadata: Metadata{
			Source: "Test",
			Format: "TEST",
		},
		Floors: []Floor{
			{
				ID:        "1",
				Name:      "Ground Floor",
				Elevation: 0.0,
				Rooms: []Room{
					{
						Number: "101",
						Name:   "Conference Room",
						Type:   "conference",
						Area:   250.0,
						Equipment: []Equipment{
							{
								Tag:    "AHU-01",
								Name:   "Air Handler",
								Type:   "hvac",
								Status: "operational",
							},
						},
					},
				},
			},
		},
	}

	converter := NewStreamingPDFConverter(nil)

	var output bytes.Buffer
	err := converter.streamBIMOutput(building, &output)
	if err != nil {
		t.Fatalf("Streaming output failed: %v", err)
	}

	result := output.String()

	// Check for required sections
	expectedSections := []string{
		"# ArxOS Building Information Model",
		"# Name: Test Building",
		"## FLOORS",
		"FLOOR 1 \"Ground Floor\" 0.0",
		"## ROOMS",
		"ROOM 1/101 \"Conference Room\" conference 250.0",
		"## EQUIPMENT",
		"EQUIPMENT 1/101/AHU-01 \"Air Handler\" hvac operational",
	}

	for _, section := range expectedSections {
		if !strings.Contains(result, section) {
			t.Errorf("Missing expected section: %s", section)
		}
	}
}

func TestContextCancellation(t *testing.T) {
	config := DefaultPerformanceConfig()
	converter := NewStreamingPDFConverter(config)

	// Create a context that will be cancelled
	ctx, cancel := context.WithCancel(context.Background())

	// Cancel immediately
	cancel()

	input := strings.NewReader("ROOM 101 - Test Room")
	var output bytes.Buffer

	err := converter.ConvertToBIMStreaming(ctx, input, &output)

	// Should return context cancellation error
	if err != context.Canceled {
		t.Errorf("Expected context.Canceled, got %v", err)
	}
}

// Benchmark functions

func BenchmarkStreamingConverter(b *testing.B) {
	config := DefaultPerformanceConfig()
	converter := NewStreamingPDFConverter(config)

	input := createLargeTextInput(100)
	ctx := context.Background()

	b.ResetTimer()

	for i := 0; i < b.N; i++ {
		var output bytes.Buffer
		reader := strings.NewReader(input)

		err := converter.ConvertToBIMStreaming(ctx, reader, &output)
		if err != nil {
			b.Fatalf("Conversion failed: %v", err)
		}
	}
}

func BenchmarkRegularConverter(b *testing.B) {
	// Create a proper PDF for testing
	testPDF := createTestPDF(nil)
	defer func() {
		if testPDF != "" {
			os.Remove(testPDF)
		}
	}()

	converter := NewRealPDFConverter()

	b.ResetTimer()

	for i := 0; i < b.N; i++ {
		input, err := os.Open(testPDF)
		if err != nil {
			b.Fatalf("Failed to open test PDF: %v", err)
		}

		var output bytes.Buffer
		err = converter.ConvertToBIM(input, &output)
		input.Close()

		if err != nil {
			b.Fatalf("Conversion failed: %v", err)
		}
	}
}

func BenchmarkMemoryPool(b *testing.B) {
	pool := NewMemoryPool(1024)

	b.ResetTimer()

	for i := 0; i < b.N; i++ {
		buf := pool.Get()
		pool.Put(buf)
	}
}

func BenchmarkConcurrentProcessing(b *testing.B) {
	config := &PerformanceConfig{
		MaxMemoryMB:   100,
		BufferSize:    32 * 1024,
		MaxGoroutines: 4,
	}

	converter := NewStreamingPDFConverter(config)
	chunks := make([]string, 100)
	for i := range chunks {
		chunks[i] = fmt.Sprintf("ROOM %d - Office %d - 150 sq ft", i+100, i+1)
	}

	ctx := context.Background()

	b.ResetTimer()

	for i := 0; i < b.N; i++ {
		rooms, equipment := converter.processChunksConcurrently(ctx, chunks)
		_ = rooms
		_ = equipment
	}
}

// Helper function to create large test input
func createLargeTextInput(numRooms int) string {
	var builder strings.Builder

	builder.WriteString("LARGE BUILDING FLOOR PLAN\n")

	for i := 0; i < numRooms; i++ {
		roomNum := i + 100
		builder.WriteString(fmt.Sprintf("ROOM %d - Office Room %d - %d sq ft\n", roomNum, i+1, 100+(i%50)))

		// Add some equipment every 10 rooms
		if i%10 == 0 {
			builder.WriteString(fmt.Sprintf("AHU-%d: Air Handler Unit\n", i/10+1))
			builder.WriteString(fmt.Sprintf("LOCATION: ROOM %d\n", roomNum))
		}

		// Add telecom rooms every 25 rooms
		if i%25 == 0 {
			builder.WriteString(fmt.Sprintf("IDF %dA - Telecom Closet Floor %d\n", i/25+1, (i/100)+1))
		}
	}

	return builder.String()
}