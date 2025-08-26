package commands

import (
	"encoding/json"
	"os"
	"path/filepath"
	"testing"
	"time"
)

func TestProcessPDFFloorPlan(t *testing.T) {
	// Create a temporary directory for testing
	tempDir, err := os.MkdirTemp("", "arxos-test-*")
	if err != nil {
		t.Fatalf("Failed to create temp dir: %v", err)
	}
	defer os.RemoveAll(tempDir)

	// Change to temp directory
	originalDir, err := os.Getwd()
	if err != nil {
		t.Fatalf("Failed to get current directory: %v", err)
	}
	defer os.Chdir(originalDir)

	if err := os.Chdir(tempDir); err != nil {
		t.Fatalf("Failed to change to temp directory: %v", err)
	}

	// Create a test PDF file
	testPDF := "test_floor_plan.pdf"
	if err := os.WriteFile(testPDF, []byte("fake PDF content"), 0644); err != nil {
		t.Fatalf("Failed to create test PDF: %v", err)
	}

	// Test PDF processing
	buildingID := "building:test"
	if err := processPDFFloorPlan(buildingID, testPDF); err != nil {
		t.Fatalf("processPDFFloorPlan() failed: %v", err)
	}

	// Verify PDF processing directory was created
	pdfDir := filepath.Join(buildingID, ".arxos", "processing", "pdf")
	if _, err := os.Stat(pdfDir); os.IsNotExist(err) {
		t.Errorf("PDF processing directory not created: %s", pdfDir)
	}

	// Verify PDF was copied
	copiedPDF := filepath.Join(pdfDir, "floor_plan.pdf")
	if _, err := os.Stat(copiedPDF); os.IsNotExist(err) {
		t.Errorf("PDF file not copied: %s", copiedPDF)
	}

	// Verify metadata was created
	metadataPath := filepath.Join(pdfDir, "metadata.json")
	if _, err := os.Stat(metadataPath); os.IsNotExist(err) {
		t.Errorf("PDF metadata not created: %s", metadataPath)
	}
}

func TestProcessIFCFile(t *testing.T) {
	// Create a temporary directory for testing
	tempDir, err := os.MkdirTemp("", "arxos-test-*")
	if err != nil {
		t.Fatalf("Failed to create temp dir: %v", err)
	}
	defer os.RemoveAll(tempDir)

	// Change to temp directory
	originalDir, err := os.Getwd()
	if err != nil {
		t.Fatalf("Failed to get current directory: %v", err)
	}
	defer os.Chdir(originalDir)

	if err := os.Chdir(tempDir); err != nil {
		t.Fatalf("Failed to change to temp directory: %v", err)
	}

	// Create a test IFC file
	testIFC := "test_building.ifc"
	if err := os.WriteFile(testIFC, []byte("fake IFC content"), 0644); err != nil {
		t.Fatalf("Failed to create test IFC: %v", err)
	}

	// Test IFC processing
	buildingID := "building:test"
	if err := processIFCFile(buildingID, testIFC); err != nil {
		t.Fatalf("processIFCFile() failed: %v", err)
	}

	// Verify IFC processing directory was created
	ifcDir := filepath.Join(buildingID, ".arxos", "processing", "ifc")
	if _, err := os.Stat(ifcDir); os.IsNotExist(err) {
		t.Errorf("IFC processing directory not created: %s", ifcDir)
	}

	// Verify IFC was copied
	copiedIFC := filepath.Join(ifcDir, "building_model.ifc")
	if _, err := os.Stat(copiedIFC); os.IsNotExist(err) {
		t.Errorf("IFC file not copied: %s", copiedIFC)
	}

	// Verify metadata was created
	metadataPath := filepath.Join(ifcDir, "metadata.json")
	if _, err := os.Stat(metadataPath); os.IsNotExist(err) {
		t.Errorf("IFC metadata not created: %s", metadataPath)
	}
}

func TestApplyBuildingTemplate(t *testing.T) {
	// Create a temporary directory for testing
	tempDir, err := os.MkdirTemp("", "arxos-test-*")
	if err != nil {
		t.Fatalf("Failed to create temp dir: %v", err)
	}
	defer os.RemoveAll(tempDir)

	// Change to temp directory
	originalDir, err := os.Getwd()
	if err != nil {
		t.Fatalf("Failed to get current directory: %v", err)
	}
	defer os.Chdir(originalDir)

	if err := os.Chdir(tempDir); err != nil {
		t.Fatalf("Failed to change to temp directory: %v", err)
	}

	// Test template application
	buildingID := "building:test"
	templateName := "standard_office"
	if err := applyBuildingTemplate(buildingID, templateName); err != nil {
		t.Fatalf("applyBuildingTemplate() failed: %v", err)
	}

	// Verify template directory was created
	templateDir := filepath.Join(buildingID, ".arxos", "templates")
	if _, err := os.Stat(templateDir); os.IsNotExist(err) {
		t.Errorf("Template directory not created: %s", templateDir)
	}

	// Verify template metadata was created
	metadataPath := filepath.Join(templateDir, "applied_template.json")
	if _, err := os.Stat(metadataPath); os.IsNotExist(err) {
		t.Errorf("Template metadata not created: %s", metadataPath)
	}
}

func TestCopyFile(t *testing.T) {
	// Create a temporary directory for testing
	tempDir, err := os.MkdirTemp("", "arxos-test-*")
	if err != nil {
		t.Fatalf("Failed to create temp dir: %v", err)
	}
	defer os.RemoveAll(tempDir)

	// Create source file with content
	sourceFile := filepath.Join(tempDir, "source.txt")
	sourceContent := "This is test content for file copying"
	if err := os.WriteFile(sourceFile, []byte(sourceContent), 0644); err != nil {
		t.Fatalf("Failed to create source file: %v", err)
	}

	// Copy file
	destFile := filepath.Join(tempDir, "dest.txt")
	if err := copyFile(sourceFile, destFile); err != nil {
		t.Fatalf("copyFile() failed: %v", err)
	}

	// Verify destination file exists
	if _, err := os.Stat(destFile); os.IsNotExist(err) {
		t.Errorf("Destination file not created: %s", destFile)
	}

	// Verify content was copied correctly
	destContent, err := os.ReadFile(destFile)
	if err != nil {
		t.Fatalf("Failed to read destination file: %v", err)
	}

	if string(destContent) != sourceContent {
		t.Errorf("File content not copied correctly. Expected: %s, Got: %s", sourceContent, string(destContent))
	}
}

func TestLoadBuildingTemplate(t *testing.T) {
	templateName := "test_template"
	template, err := loadBuildingTemplate(templateName)
	if err != nil {
		t.Fatalf("loadBuildingTemplate() failed: %v", err)
	}

	// Verify template structure
	if template["name"] != templateName {
		t.Errorf("Template name not set correctly. Expected: %s, Got: %v", templateName, template["name"])
	}

	if template["version"] != "1.0.0" {
		t.Errorf("Template version not set correctly. Expected: 1.0.0, Got: %v", template["version"])
	}

	// Verify systems exist
	systems, ok := template["systems"].(map[string]interface{})
	if !ok {
		t.Fatalf("Template systems not found or wrong type")
	}

	if systems["electrical"] == nil {
		t.Errorf("Electrical system not found in template")
	}

	if systems["hvac"] == nil {
		t.Errorf("HVAC system not found in template")
	}
}

func TestWriteJSON(t *testing.T) {
	// Create a temporary directory for testing
	tempDir, err := os.MkdirTemp("", "arxos-test-*")
	if err != nil {
		t.Fatalf("Failed to create temp dir: %v", err)
	}
	defer os.RemoveAll(tempDir)

	// Test data structure
	testData := map[string]interface{}{
		"string":  "test value",
		"number":  42,
		"boolean": true,
		"array":   []string{"item1", "item2"},
		"nested": map[string]interface{}{
			"key": "value",
		},
	}

	// Write JSON file
	jsonPath := filepath.Join(tempDir, "test.json")
	if err := writeJSON(jsonPath, testData); err != nil {
		t.Fatalf("writeJSON() failed: %v", err)
	}

	// Verify file was created
	if _, err := os.Stat(jsonPath); os.IsNotExist(err) {
		t.Errorf("JSON file not created: %s", jsonPath)
	}

	// Verify file content is valid JSON
	content, err := os.ReadFile(jsonPath)
	if err != nil {
		t.Fatalf("Failed to read JSON file: %v", err)
	}

	// Try to unmarshal to verify it's valid JSON
	var parsed map[string]interface{}
	if err := json.Unmarshal(content, &parsed); err != nil {
		t.Errorf("Generated file is not valid JSON: %v", err)
	}

	// Verify content matches
	if parsed["string"] != "test value" {
		t.Errorf("String value not preserved. Expected: test value, Got: %v", parsed["string"])
	}

	if parsed["number"] != float64(42) { // JSON numbers are float64
		t.Errorf("Number value not preserved. Expected: 42, Got: %v", parsed["number"])
	}

	if parsed["boolean"] != true {
		t.Errorf("Boolean value not preserved. Expected: true, Got: %v", parsed["boolean"])
	}
}

func TestInputFileProcessingIntegration(t *testing.T) {
	// Create a temporary directory for testing
	tempDir, err := os.MkdirTemp("", "arxos-test-*")
	if err != nil {
		t.Fatalf("Failed to create temp dir: %v", err)
	}
	defer os.RemoveAll(tempDir)

	// Change to temp directory
	originalDir, err := os.Getwd()
	if err != nil {
		t.Fatalf("Failed to get current directory: %v", err)
	}
	defer os.Chdir(originalDir)

	if err := os.Chdir(tempDir); err != nil {
		t.Fatalf("Failed to change to temp directory: %v", err)
	}

	// Create test files
	testPDF := "floor_plan.pdf"
	testIFC := "building.ifc"
	
	if err := os.WriteFile(testPDF, []byte("fake PDF"), 0644); err != nil {
		t.Fatalf("Failed to create test PDF: %v", err)
	}
	
	if err := os.WriteFile(testIFC, []byte("fake IFC"), 0644); err != nil {
		t.Fatalf("Failed to create test IFC: %v", err)
	}

	// Test complete input processing workflow
	buildingID := "building:test"
	options := &InitOptions{
		BuildingType: "office",
		Floors:       2,
		FromPDF:      testPDF,
		FromIFC:      testIFC,
		Template:     "standard_office",
	}

	if err := processInputFiles(buildingID, options); err != nil {
		t.Fatalf("processInputFiles() failed: %v", err)
	}

	// Verify all processing directories were created
	processingDirs := []string{
		filepath.Join(buildingID, ".arxos", "processing", "pdf"),
		filepath.Join(buildingID, ".arxos", "processing", "ifc"),
		filepath.Join(buildingID, ".arxos", "templates"),
	}

	for _, dir := range processingDirs {
		if _, err := os.Stat(dir); os.IsNotExist(err) {
			t.Errorf("Processing directory not created: %s", dir)
		}
	}

	// Verify all metadata files were created
	metadataFiles := []string{
		filepath.Join(buildingID, ".arxos", "processing", "pdf", "metadata.json"),
		filepath.Join(buildingID, ".arxos", "processing", "ifc", "metadata.json"),
		filepath.Join(buildingID, ".arxos", "templates", "applied_template.json"),
	}

	for _, file := range metadataFiles {
		if _, err := os.Stat(file); os.IsNotExist(err) {
			t.Errorf("Metadata file not created: %s", file)
		}
	}
}

func TestMetadataStructures(t *testing.T) {
	// Test PDF metadata creation
	pdfMeta := &PDFMetadata{
		SourceFile:    "/path/to/plan.pdf",
		ProcessedAt:   time.Now(),
		Status:        "uploaded",
		PageCount:     5,
		BuildingID:    "building:test",
		ProcessingLog: []string{"PDF processed successfully"},
	}

	// Verify all fields are set
	if pdfMeta.SourceFile == "" {
		t.Error("PDFMetadata SourceFile not set")
	}
	if pdfMeta.Status == "" {
		t.Error("PDFMetadata Status not set")
	}
	if pdfMeta.BuildingID == "" {
		t.Error("PDFMetadata BuildingID not set")
	}
	if len(pdfMeta.ProcessingLog) == 0 {
		t.Error("PDFMetadata ProcessingLog not set")
	}

	// Test IFC metadata creation
	ifcMeta := &IFCMetadata{
		SourceFile:    "/path/to/model.ifc",
		ProcessedAt:   time.Now(),
		Status:        "uploaded",
		BuildingID:    "building:test",
		ProcessingLog: []string{"IFC processed successfully"},
	}

	// Verify all fields are set
	if ifcMeta.SourceFile == "" {
		t.Error("IFCMetadata SourceFile not set")
	}
	if ifcMeta.Status == "" {
		t.Error("IFCMetadata Status not set")
	}
	if ifcMeta.BuildingID == "" {
		t.Error("IFCMetadata BuildingID not set")
	}

	// Test template metadata creation
	templateMeta := &TemplateMetadata{
		TemplateName:  "standard_office",
		AppliedAt:     time.Now(),
		BuildingID:    "building:test",
		TemplateData:  map[string]interface{}{"name": "test"},
		ProcessingLog: []string{"Template applied successfully"},
	}

	// Verify all fields are set
	if templateMeta.TemplateName == "" {
		t.Error("TemplateMetadata TemplateName not set")
	}
	if templateMeta.BuildingID == "" {
		t.Error("TemplateMetadata BuildingID not set")
	}
	if templateMeta.TemplateData == nil {
		t.Error("TemplateMetadata TemplateData not set")
	}
}
