package converter

import (
	"bytes"
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"testing"
)

// TestConverterIntegration tests the complete conversion pipeline
func TestConverterIntegration(t *testing.T) {
	// Create test data directory if it doesn't exist
	testDataDir := "../../test_data"
	if _, err := os.Stat(testDataDir); os.IsNotExist(err) {
		t.Skip("Test data directory not found, skipping integration tests")
	}

	tests := []struct {
		name           string
		inputFile      string
		expectedFormat string
		minRooms       int
		minEquipment   int
	}{
		{
			name:           "IFC Sample File",
			inputFile:      "sample.ifc",
			expectedFormat: "ifc",
			minRooms:       2, // Expect at least 2 rooms from sample.ifc
			minEquipment:   1, // Expect at least 1 equipment item
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			// Set up paths
			inputPath := filepath.Join(testDataDir, tt.inputFile)

			// Check if test file exists
			if _, err := os.Stat(inputPath); os.IsNotExist(err) {
				t.Skipf("Test file not found: %s", inputPath)
			}

			// Create converter registry
			registry := NewRegistry()

			// Get converter for file
			conv, err := registry.GetConverter(inputPath)
			if err != nil {
				t.Fatalf("Failed to get converter: %v", err)
			}

			// Verify expected format
			if conv.GetFormat() != tt.expectedFormat {
				t.Errorf("Expected format %s, got %s", tt.expectedFormat, conv.GetFormat())
			}

			// Open input file
			input, err := os.Open(inputPath)
			if err != nil {
				t.Fatalf("Failed to open input file: %v", err)
			}
			defer input.Close()

			// Convert to BIM
			var output bytes.Buffer
			err = conv.ConvertToBIM(input, &output)
			if err != nil {
				t.Fatalf("Conversion failed: %v", err)
			}

			// Validate output
			bimContent := output.String()

			// Check that output is not empty
			if len(bimContent) == 0 {
				t.Fatal("Output is empty")
			}

			// Check for required sections
			requiredSections := []string{
				"# ArxOS Building Information Model",
				"## FLOORS",
			}

			for _, section := range requiredSections {
				if !strings.Contains(bimContent, section) {
					t.Errorf("Missing required section: %s", section)
				}
			}

			// Count rooms and equipment
			roomCount := strings.Count(bimContent, "ROOM ")
			equipmentCount := strings.Count(bimContent, "EQUIPMENT ")

			if roomCount < tt.minRooms {
				t.Errorf("Expected at least %d rooms, got %d", tt.minRooms, roomCount)
			}

			if equipmentCount < tt.minEquipment {
				t.Errorf("Expected at least %d equipment items, got %d", tt.minEquipment, equipmentCount)
			}

			// Verify BIM format compliance
			validateBIMFormat(t, bimContent)
		})
	}
}

// TestEndToEndConversion tests the complete file conversion process
func TestEndToEndConversion(t *testing.T) {
	// Create a real PDF for testing
	testPDF := createTestPDF(t)
	defer os.Remove(testPDF)

	// Create registry and convert
	registry := NewRegistry()

	// Create temporary output file
	outputFile := filepath.Join(os.TempDir(), "test_output.bim.txt")
	defer os.Remove(outputFile)

	// Convert file
	err := registry.ConvertFile(testPDF, outputFile)
	if err != nil {
		t.Fatalf("End-to-end conversion failed: %v", err)
	}

	// Verify output file exists
	if _, err := os.Stat(outputFile); os.IsNotExist(err) {
		t.Fatal("Output file was not created")
	}

	// Read and validate output
	content, err := os.ReadFile(outputFile)
	if err != nil {
		t.Fatalf("Failed to read output file: %v", err)
	}

	bimContent := string(content)
	validateBIMFormat(t, bimContent)

	// Check for expected content from our test PDF
	expectedContent := []string{
		"Conference Room",
		"Office Space",
		"IDF 103A",
		"MDF 104B",
	}

	for _, expected := range expectedContent {
		if !strings.Contains(bimContent, expected) {
			t.Errorf("Expected content '%s' not found in output", expected)
		}
	}
}

// TestLargeFileHandling tests conversion of larger files
func TestLargeFileHandling(t *testing.T) {
	// Create a large test PDF with many rooms
	largeTestPDF := createLargeTestPDF(t)
	defer os.Remove(largeTestPDF)

	registry := NewRegistry()

	// Convert with performance monitoring
	var output bytes.Buffer
	input, err := os.Open(largeTestPDF)
	if err != nil {
		t.Fatalf("Failed to open large test file: %v", err)
	}
	defer input.Close()

	conv, err := registry.GetConverter(largeTestPDF)
	if err != nil {
		t.Fatalf("Failed to get converter: %v", err)
	}

	err = conv.ConvertToBIM(input, &output)
	if err != nil {
		t.Fatalf("Large file conversion failed: %v", err)
	}

	bimContent := output.String()

	// Should have many rooms
	roomCount := strings.Count(bimContent, "ROOM ")
	if roomCount < 10 {
		t.Errorf("Expected at least 10 rooms in large file, got %d", roomCount)
	}

	// Output should be reasonably sized (not empty, not too small)
	if len(bimContent) < 1000 {
		t.Errorf("Large file output seems too small: %d bytes", len(bimContent))
	}
}

// TestErrorConditions tests various error scenarios
func TestErrorConditions(t *testing.T) {
	registry := NewRegistry()

	tests := []struct {
		name        string
		inputFile   string
		outputFile  string
		expectError bool
		errorMsg    string
	}{
		{
			name:        "Nonexistent input file",
			inputFile:   "/nonexistent/file.pdf",
			outputFile:  "/tmp/output.bim.txt",
			expectError: true,
			errorMsg:    "failed to open input",
		},
		{
			name:        "Invalid output directory",
			inputFile:   createTestPDF(nil), // This will be cleaned up by test
			outputFile:  "/nonexistent_dir/output.bim.txt",
			expectError: true,
			errorMsg:    "failed to create output",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			// Clean up test file if created
			if strings.Contains(tt.inputFile, "arxos_test_") {
				defer os.Remove(tt.inputFile)
			}

			err := registry.ConvertFile(tt.inputFile, tt.outputFile)

			if tt.expectError {
				if err == nil {
					t.Errorf("Expected error containing '%s', but got no error", tt.errorMsg)
				} else if !strings.Contains(err.Error(), tt.errorMsg) {
					t.Errorf("Expected error containing '%s', got: %v", tt.errorMsg, err)
				}
			} else {
				if err != nil {
					t.Errorf("Unexpected error: %v", err)
				}
			}
		})
	}
}

// Helper functions

func validateBIMFormat(t *testing.T, content string) {
	// Check basic structure
	if !strings.HasPrefix(content, "# ArxOS Building Information Model") {
		t.Error("BIM content should start with ArxOS header")
	}

	// Check for proper section formatting
	lines := strings.Split(content, "\n")
	inSection := false
	currentSection := ""

	for _, line := range lines {
		line = strings.TrimSpace(line)
		if line == "" {
			continue
		}

		if strings.HasPrefix(line, "##") {
			inSection = true
			currentSection = line
			continue
		}

		if inSection && currentSection == "## FLOORS" {
			if strings.HasPrefix(line, "FLOOR ") {
				// Validate floor format: FLOOR ID "Name" elevation
				parts := strings.Fields(line)
				if len(parts) < 3 {
					t.Errorf("Invalid floor format: %s", line)
				}
			}
		}

		if inSection && currentSection == "## ROOMS" {
			if strings.HasPrefix(line, "ROOM ") {
				// Validate room format: ROOM FloorID/RoomID "Name" type area
				parts := strings.Fields(line)
				if len(parts) < 4 {
					t.Errorf("Invalid room format: %s", line)
				}
			}
		}

		if inSection && currentSection == "## EQUIPMENT" {
			if strings.HasPrefix(line, "EQUIPMENT ") {
				// Validate equipment format: EQUIPMENT FloorID/RoomID/Tag "Name" type status
				parts := strings.Fields(line)
				if len(parts) < 5 {
					t.Errorf("Invalid equipment format: %s", line)
				}
			}
		}
	}
}

func createTestPDF(t *testing.T) string {
	// Create the same test PDF we used before
	content := `%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj

2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj

3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
/Contents 4 0 R
>>
endobj

4 0 obj
<<
/Length 500
>>
stream
BT
/F1 12 Tf
72 720 Td
(FLOOR PLAN - LEVEL 1) Tj
0 -24 Td
(Building A - Office Complex) Tj
0 -48 Td
(ROOM 101 - Conference Room - 250 sq ft) Tj
0 -24 Td
(ROOM 102 - Office Space - 150 sq ft) Tj
0 -24 Td
(IDF 103A - Telecom Closet) Tj
0 -24 Td
(MDF 104B - Main Distribution Frame) Tj
0 -24 Td
(SUITE 201 - Executive Office - 300 sq ft) Tj
0 -24 Td
(OFFICE 202 - Manager Office) Tj
0 -24 Td
(AHU-01: Rooftop Air Handler) Tj
0 -24 Td
(VAV-101: Variable Air Volume Box) Tj
0 -24 Td
(LOCATION: ROOM 101) Tj
0 -24 Td
(Equipment: FCU-201 Fan Coil Unit) Tj
ET
endstream
endobj

xref
0 5
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
0000000203 00000 n
trailer
<<
/Size 5
/Root 1 0 R
>>
startxref
754
%%EOF`

	tmpFile := filepath.Join(os.TempDir(), "arxos_test_integration.pdf")
	err := os.WriteFile(tmpFile, []byte(content), 0644)
	if t != nil && err != nil {
		t.Fatalf("Failed to create test PDF: %v", err)
	}
	return tmpFile
}

func createLargeTestPDF(t *testing.T) string {
	// Create a PDF with many rooms to test performance
	var contentBuilder strings.Builder
	contentBuilder.WriteString(`%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj

2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj

3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
/Contents 4 0 R
>>
endobj

4 0 obj
<<
/Length 2000
>>
stream
BT
/F1 12 Tf
72 720 Td
(LARGE BUILDING FLOOR PLAN) Tj
0 -24 Td
`)

	// Add many rooms
	for i := 100; i < 150; i++ {
		contentBuilder.WriteString("0 -24 Td\n")
		contentBuilder.WriteString(fmt.Sprintf("(ROOM %d - Office Room %d - %d sq ft) Tj\n", i, i-99, 100+(i%50)))
	}

	// Add telecom rooms
	for i := 1; i <= 5; i++ {
		contentBuilder.WriteString("0 -24 Td\n")
		contentBuilder.WriteString(fmt.Sprintf("(IDF %dA - Telecom Closet Floor %d) Tj\n", i, i))
	}

	contentBuilder.WriteString(`ET
endstream
endobj

xref
0 5
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
0000000203 00000 n
trailer
<<
/Size 5
/Root 1 0 R
>>
startxref
2500
%%EOF`)

	tmpFile := filepath.Join(os.TempDir(), "arxos_test_large.pdf")
	err := os.WriteFile(tmpFile, []byte(contentBuilder.String()), 0644)
	if err != nil {
		t.Fatalf("Failed to create large test PDF: %v", err)
	}
	return tmpFile
}