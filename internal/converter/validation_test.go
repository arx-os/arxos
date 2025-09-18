package converter

import (
	"os"
	"path/filepath"
	"strings"
	"testing"
)

func TestFileValidator_ValidateFile(t *testing.T) {
	validator := NewFileValidator(nil)

	// Create a temporary valid PDF for testing
	testPDF := createTestPDF(nil)
	defer os.Remove(testPDF)

	result, err := validator.ValidateFile(testPDF)
	if err != nil {
		t.Fatalf("Validation failed: %v", err)
	}

	if !result.IsValid {
		t.Errorf("Expected valid file, got invalid with issues: %v", result.Issues)
	}

	if result.Extension != ".pdf" {
		t.Errorf("Expected .pdf extension, got %s", result.Extension)
	}

	if result.ContentType != "PDF" {
		t.Errorf("Expected PDF content type, got %s", result.ContentType)
	}
}

func TestFileValidator_NonexistentFile(t *testing.T) {
	validator := NewFileValidator(nil)

	result, err := validator.ValidateFile("/nonexistent/file.pdf")
	if err != nil {
		t.Fatalf("Validation should not error, got: %v", err)
	}

	if result.IsValid {
		t.Error("Expected invalid result for nonexistent file")
	}

	if len(result.Issues) == 0 {
		t.Error("Expected issues for nonexistent file")
	}

	expectedIssue := "File does not exist"
	found := false
	for _, issue := range result.Issues {
		if strings.Contains(issue, expectedIssue) {
			found = true
			break
		}
	}
	if !found {
		t.Errorf("Expected issue containing '%s', got: %v", expectedIssue, result.Issues)
	}
}

func TestFileValidator_EmptyFile(t *testing.T) {
	// Create empty file
	tmpFile := filepath.Join(os.TempDir(), "empty.pdf")
	err := os.WriteFile(tmpFile, []byte{}, 0644)
	if err != nil {
		t.Fatalf("Failed to create empty file: %v", err)
	}
	defer os.Remove(tmpFile)

	validator := NewFileValidator(nil)
	result, err := validator.ValidateFile(tmpFile)
	if err != nil {
		t.Fatalf("Validation failed: %v", err)
	}

	if result.IsValid {
		t.Error("Expected invalid result for empty file")
	}

	expectedIssue := "file is empty"
	found := false
	for _, issue := range result.Issues {
		if strings.Contains(issue, expectedIssue) {
			found = true
			break
		}
	}
	if !found {
		t.Errorf("Expected issue containing '%s', got: %v", expectedIssue, result.Issues)
	}
}

func TestFileValidator_UnsupportedExtension(t *testing.T) {
	// Create file with unsupported extension
	tmpFile := filepath.Join(os.TempDir(), "test.dwg")
	err := os.WriteFile(tmpFile, []byte("test content"), 0644)
	if err != nil {
		t.Fatalf("Failed to create test file: %v", err)
	}
	defer os.Remove(tmpFile)

	validator := NewFileValidator(nil)
	result, err := validator.ValidateFile(tmpFile)
	if err != nil {
		t.Fatalf("Validation failed: %v", err)
	}

	if result.IsValid {
		t.Error("Expected invalid result for unsupported extension")
	}

	expectedIssue := "unsupported file extension"
	found := false
	for _, issue := range result.Issues {
		if strings.Contains(issue, expectedIssue) {
			found = true
			break
		}
	}
	if !found {
		t.Errorf("Expected issue containing '%s', got: %v", expectedIssue, result.Issues)
	}
}

func TestFileValidator_LargeFile(t *testing.T) {
	// Create custom config with small size limit
	config := &ValidationConfig{
		MaxFileSizeMB:           1, // 1MB limit
		SupportedExtensions:     []string{".pdf"},
		RequiredPermissions:     0444,
		EnableContentValidation: false,
	}

	validator := NewFileValidator(config)

	// Create file larger than limit
	tmpFile := filepath.Join(os.TempDir(), "large.pdf")
	largeContent := make([]byte, 2*1024*1024) // 2MB
	copy(largeContent, []byte("%PDF-1.4"))    // Valid PDF header
	err := os.WriteFile(tmpFile, largeContent, 0644)
	if err != nil {
		t.Fatalf("Failed to create large file: %v", err)
	}
	defer os.Remove(tmpFile)

	result, err := validator.ValidateFile(tmpFile)
	if err != nil {
		t.Fatalf("Validation failed: %v", err)
	}

	if result.IsValid {
		t.Error("Expected invalid result for oversized file")
	}

	expectedIssue := "file size"
	found := false
	for _, issue := range result.Issues {
		if strings.Contains(issue, expectedIssue) {
			found = true
			break
		}
	}
	if !found {
		t.Errorf("Expected issue containing '%s', got: %v", expectedIssue, result.Issues)
	}
}

func TestFileValidator_ValidatePDFContent(t *testing.T) {
	validator := NewFileValidator(nil)

	tests := []struct {
		name           string
		content        string
		expectValid    bool
		expectedIssues []string
		expectedType   string
	}{
		{
			name:         "Valid PDF",
			content:      "%PDF-1.4\nsome content",
			expectValid:  true,
			expectedType: "PDF",
		},
		{
			name:           "Invalid PDF header",
			content:        "Not a PDF file",
			expectValid:    false,
			expectedIssues: []string{"invalid PDF header"},
		},
		{
			name:         "Old PDF version",
			content:      "%PDF-1.2\nsome content",
			expectValid:  true,
			expectedType: "PDF",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			// Create temporary file with test content
			tmpFile := filepath.Join(os.TempDir(), "test.pdf")
			err := os.WriteFile(tmpFile, []byte(tt.content), 0644)
			if err != nil {
				t.Fatalf("Failed to create test file: %v", err)
			}
			defer os.Remove(tmpFile)

			result, err := validator.ValidateFile(tmpFile)
			if err != nil {
				t.Fatalf("Validation failed: %v", err)
			}

			if result.IsValid != tt.expectValid {
				t.Errorf("Expected valid=%v, got valid=%v, issues: %v", tt.expectValid, result.IsValid, result.Issues)
			}

			if tt.expectedType != "" && result.ContentType != tt.expectedType {
				t.Errorf("Expected content type %s, got %s", tt.expectedType, result.ContentType)
			}

			for _, expectedIssue := range tt.expectedIssues {
				found := false
				for _, issue := range result.Issues {
					if strings.Contains(issue, expectedIssue) {
						found = true
						break
					}
				}
				if !found {
					t.Errorf("Expected issue containing '%s', got: %v", expectedIssue, result.Issues)
				}
			}
		})
	}
}

func TestFileValidator_ValidateIFCContent(t *testing.T) {
	validator := NewFileValidator(nil)

	tests := []struct {
		name         string
		content      string
		expectValid  bool
		expectedType string
	}{
		{
			name: "Valid IFC",
			content: `ISO-10303-21;
HEADER;
FILE_DESCRIPTION(('ViewDefinition [CoordinationView]'), '2;1');
ENDSEC;
DATA;
#1 = IFCBUILDING('123', $, 'Building', $, $, $, $, $, .ELEMENT., $, $, $);
ENDSEC;
END-ISO-10303-21;`,
			expectValid:  true,
			expectedType: "IFC",
		},
		{
			name:        "Invalid IFC header",
			content:     "Not an IFC file",
			expectValid: false,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			// Create temporary file with test content
			tmpFile := filepath.Join(os.TempDir(), "test.ifc")
			err := os.WriteFile(tmpFile, []byte(tt.content), 0644)
			if err != nil {
				t.Fatalf("Failed to create test file: %v", err)
			}
			defer os.Remove(tmpFile)

			result, err := validator.ValidateFile(tmpFile)
			if err != nil {
				t.Fatalf("Validation failed: %v", err)
			}

			if result.IsValid != tt.expectValid {
				t.Errorf("Expected valid=%v, got valid=%v, issues: %v", tt.expectValid, result.IsValid, result.Issues)
			}

			if tt.expectedType != "" && result.ContentType != tt.expectedType {
				t.Errorf("Expected content type %s, got %s", tt.expectedType, result.ContentType)
			}
		})
	}
}

func TestFileValidator_ValidateIFCXMLContent(t *testing.T) {
	validator := NewFileValidator(nil)

	tests := []struct {
		name         string
		content      string
		expectValid  bool
		expectedType string
	}{
		{
			name: "Valid IFCXML",
			content: `<?xml version="1.0" encoding="UTF-8"?>
<ifcXML xmlns="http://www.iai-tech.org/ifcXML/IFC2x3/FINAL" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <IfcBuilding id="building1" Name="Test Building"/>
</ifcXML>`,
			expectValid:  true,
			expectedType: "IFCXML",
		},
		{
			name:        "Invalid XML header",
			content:     "Not an XML file",
			expectValid: false,
		},
		{
			name: "XML without IFC namespace",
			content: `<?xml version="1.0" encoding="UTF-8"?>
<root>
  <item>Test</item>
</root>`,
			expectValid:  true, // Valid XML, but warning about IFC namespace
			expectedType: "IFCXML",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			// Create temporary file with test content
			tmpFile := filepath.Join(os.TempDir(), "test.ifcxml")
			err := os.WriteFile(tmpFile, []byte(tt.content), 0644)
			if err != nil {
				t.Fatalf("Failed to create test file: %v", err)
			}
			defer os.Remove(tmpFile)

			result, err := validator.ValidateFile(tmpFile)
			if err != nil {
				t.Fatalf("Validation failed: %v", err)
			}

			if result.IsValid != tt.expectValid {
				t.Errorf("Expected valid=%v, got valid=%v, issues: %v", tt.expectValid, result.IsValid, result.Issues)
			}

			if tt.expectedType != "" && result.ContentType != tt.expectedType {
				t.Errorf("Expected content type %s, got %s", tt.expectedType, result.ContentType)
			}
		})
	}
}

func TestFileValidator_CustomConfig(t *testing.T) {
	config := &ValidationConfig{
		MaxFileSizeMB:           50,
		SupportedExtensions:     []string{".pdf", ".custom"},
		RequiredPermissions:     0444,
		EnableContentValidation: false,
	}

	validator := NewFileValidator(config)

	// Test custom extension
	tmpFile := filepath.Join(os.TempDir(), "test.custom")
	err := os.WriteFile(tmpFile, []byte("test content"), 0644)
	if err != nil {
		t.Fatalf("Failed to create test file: %v", err)
	}
	defer os.Remove(tmpFile)

	result, err := validator.ValidateFile(tmpFile)
	if err != nil {
		t.Fatalf("Validation failed: %v", err)
	}

	if !result.IsValid {
		t.Errorf("Expected valid result for custom extension, got issues: %v", result.Issues)
	}

	if result.Extension != ".custom" {
		t.Errorf("Expected .custom extension, got %s", result.Extension)
	}
}

func TestFileValidator_Suggestions(t *testing.T) {
	validator := NewFileValidator(nil)

	// Create a large PDF to trigger suggestions
	tmpFile := filepath.Join(os.TempDir(), "large.pdf")
	largeContent := make([]byte, 60*1024*1024) // 60MB
	copy(largeContent, []byte("%PDF-1.4"))     // Valid PDF header
	err := os.WriteFile(tmpFile, largeContent, 0644)
	if err != nil {
		t.Fatalf("Failed to create large file: %v", err)
	}
	defer os.Remove(tmpFile)

	result, err := validator.ValidateFile(tmpFile)
	if err != nil {
		t.Fatalf("Validation failed: %v", err)
	}

	if len(result.Suggestions) == 0 {
		t.Error("Expected suggestions for large PDF file")
	}

	// Check for streaming suggestion
	foundStreamingSuggestion := false
	for _, suggestion := range result.Suggestions {
		if strings.Contains(suggestion, "streaming conversion") {
			foundStreamingSuggestion = true
			break
		}
	}
	if !foundStreamingSuggestion {
		t.Error("Expected streaming conversion suggestion for large file")
	}
}

func TestValidateBeforeConversion(t *testing.T) {
	// Test with valid file
	testPDF := createTestPDF(nil)
	defer os.Remove(testPDF)

	err := ValidateBeforeConversion(testPDF)
	if err != nil {
		t.Errorf("Expected no error for valid file, got: %v", err)
	}

	// Test with invalid file
	err = ValidateBeforeConversion("/nonexistent/file.pdf")
	if err == nil {
		t.Error("Expected error for nonexistent file")
	}

	expectedError := "file validation failed"
	if !strings.Contains(err.Error(), expectedError) {
		t.Errorf("Expected error containing '%s', got: %v", expectedError, err)
	}
}

func TestFileValidator_EdgeCases(t *testing.T) {
	validator := NewFileValidator(nil)

	tests := []struct {
		name        string
		filename    string
		content     string
		expectValid bool
	}{
		{
			name:        "File with no extension",
			filename:    "test_file",
			content:     "%PDF-1.4\ncontent",
			expectValid: false,
		},
		{
			name:        "File with multiple extensions",
			filename:    "test.backup.pdf",
			content:     "%PDF-1.4\ncontent",
			expectValid: true,
		},
		{
			name:        "File with uppercase extension",
			filename:    "test.PDF",
			content:     "%PDF-1.4\ncontent",
			expectValid: true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			tmpFile := filepath.Join(os.TempDir(), tt.filename)
			err := os.WriteFile(tmpFile, []byte(tt.content), 0644)
			if err != nil {
				t.Fatalf("Failed to create test file: %v", err)
			}
			defer os.Remove(tmpFile)

			result, err := validator.ValidateFile(tmpFile)
			if err != nil {
				t.Fatalf("Validation failed: %v", err)
			}

			if result.IsValid != tt.expectValid {
				t.Errorf("Expected valid=%v, got valid=%v, issues: %v", tt.expectValid, result.IsValid, result.Issues)
			}
		})
	}
}

func TestDefaultValidationConfig(t *testing.T) {
	config := DefaultValidationConfig()

	if config.MaxFileSizeMB != 100 {
		t.Errorf("Expected MaxFileSizeMB=100, got %d", config.MaxFileSizeMB)
	}

	expectedExtensions := []string{".pdf", ".ifc", ".ifcxml"}
	if len(config.SupportedExtensions) != len(expectedExtensions) {
		t.Errorf("Expected %d extensions, got %d", len(expectedExtensions), len(config.SupportedExtensions))
	}

	for i, ext := range expectedExtensions {
		if config.SupportedExtensions[i] != ext {
			t.Errorf("Expected extension %s at index %d, got %s", ext, i, config.SupportedExtensions[i])
		}
	}

	if !config.EnableContentValidation {
		t.Error("Expected EnableContentValidation=true")
	}
}
