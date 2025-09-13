package importer

import (
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	
	"github.com/joelpate/arxos/internal/common/logger"
)

// Extractor handles OCR extraction from PDFs
type Extractor struct {
	tesseractPath string
	languages     []string
}

// NewExtractor creates a new OCR extractor
func NewExtractor() *Extractor {
	return &Extractor{
		tesseractPath: "tesseract", // Assumes tesseract is in PATH
		languages:     []string{"eng"}, // Default to English
	}
}

// ExtractTextFromPDF extracts text from a scanned PDF using OCR
func (e *Extractor) ExtractTextFromPDF(pdfPath string) (string, error) {
	logger.Info("Starting OCR extraction from: %s", pdfPath)
	
	// Check if PDF exists
	if _, err := os.Stat(pdfPath); err != nil {
		return "", fmt.Errorf("PDF file not found: %w", err)
	}
	
	// Check if tesseract is available
	if !e.isTesseractAvailable() {
		logger.Warn("Tesseract not found, trying alternative method")
		return e.extractWithoutOCR(pdfPath)
	}
	
	// Create temporary directory for processing
	tempDir, err := os.MkdirTemp("", "arxos_ocr_*")
	if err != nil {
		return "", fmt.Errorf("failed to create temp directory: %w", err)
	}
	defer os.RemoveAll(tempDir)
	
	// Convert PDF pages to images using pdftoppm (part of poppler-utils)
	if err := e.convertPDFToImages(pdfPath, tempDir); err != nil {
		logger.Warn("Failed to convert PDF to images: %v", err)
		return e.extractWithoutOCR(pdfPath)
	}
	
	// Process each image with OCR
	var extractedText strings.Builder
	imageFiles, err := filepath.Glob(filepath.Join(tempDir, "*.png"))
	if err != nil {
		return "", fmt.Errorf("failed to find image files: %w", err)
	}
	
	for i, imageFile := range imageFiles {
		logger.Debug("Processing page %d: %s", i+1, imageFile)
		
		text, err := e.extractTextFromImage(imageFile)
		if err != nil {
			logger.Warn("Failed to extract text from page %d: %v", i+1, err)
			continue
		}
		
		if i > 0 {
			extractedText.WriteString("\n\n--- Page Break ---\n\n")
		}
		extractedText.WriteString(text)
	}
	
	result := extractedText.String()
	logger.Info("Successfully extracted %d characters from PDF", len(result))
	
	return result, nil
}

// isTesseractAvailable checks if tesseract is installed
func (e *Extractor) isTesseractAvailable() bool {
	cmd := exec.Command(e.tesseractPath, "--version")
	err := cmd.Run()
	return err == nil
}

// convertPDFToImages converts PDF pages to PNG images
func (e *Extractor) convertPDFToImages(pdfPath, outputDir string) error {
	// Try pdftoppm first (more common)
	cmd := exec.Command("pdftoppm", "-png", pdfPath, filepath.Join(outputDir, "page"))
	if err := cmd.Run(); err != nil {
		// Try ImageMagick convert as fallback
		cmd = exec.Command("convert", "-density", "150", pdfPath, filepath.Join(outputDir, "page-%03d.png"))
		if err := cmd.Run(); err != nil {
			return fmt.Errorf("failed to convert PDF to images: %w", err)
		}
	}
	return nil
}

// extractTextFromImage performs OCR on a single image
func (e *Extractor) extractTextFromImage(imagePath string) (string, error) {
	outputBase := strings.TrimSuffix(imagePath, filepath.Ext(imagePath))
	outputFile := outputBase + "_ocr"
	
	// Run tesseract
	cmd := exec.Command(e.tesseractPath, imagePath, outputFile, "-l", strings.Join(e.languages, "+"))
	if err := cmd.Run(); err != nil {
		return "", fmt.Errorf("tesseract failed: %w", err)
	}
	
	// Read the output text file
	textFile := outputFile + ".txt"
	defer os.Remove(textFile)
	
	content, err := os.ReadFile(textFile)
	if err != nil {
		return "", fmt.Errorf("failed to read OCR output: %w", err)
	}
	
	return string(content), nil
}

// extractWithoutOCR attempts to extract embedded text without OCR
func (e *Extractor) extractWithoutOCR(pdfPath string) (string, error) {
	// Try pdftotext (part of poppler-utils)
	cmd := exec.Command("pdftotext", pdfPath, "-")
	output, err := cmd.Output()
	if err != nil {
		return "", fmt.Errorf("no OCR tools available and pdftotext failed: %w", err)
	}
	
	text := string(output)
	if strings.TrimSpace(text) == "" {
		return "", fmt.Errorf("PDF appears to be scanned (no embedded text) and OCR tools are not available")
	}
	
	logger.Info("Extracted embedded text from PDF (no OCR needed)")
	return text, nil
}

// ExtractEquipmentInfo attempts to extract equipment information from OCR text
func (e *Extractor) ExtractEquipmentInfo(text string) []EquipmentInfo {
	var equipment []EquipmentInfo
	
	// Look for common equipment patterns
	lines := strings.Split(text, "\n")
	for _, line := range lines {
		line = strings.TrimSpace(line)
		
		// Look for outlet patterns (e.g., "Outlet 2A-1", "O-101", etc.)
		if strings.Contains(strings.ToLower(line), "outlet") ||
		   strings.Contains(line, "O-") {
			equipment = append(equipment, EquipmentInfo{
				Type: "outlet",
				Name: line,
			})
		}
		
		// Look for panel patterns
		if strings.Contains(strings.ToLower(line), "panel") ||
		   strings.Contains(line, "P-") {
			equipment = append(equipment, EquipmentInfo{
				Type: "panel",
				Name: line,
			})
		}
		
		// Look for switch patterns
		if strings.Contains(strings.ToLower(line), "switch") ||
		   strings.Contains(line, "S-") {
			equipment = append(equipment, EquipmentInfo{
				Type: "switch",
				Name: line,
			})
		}
		
		// Look for circuit patterns
		if strings.Contains(strings.ToLower(line), "circuit") ||
		   strings.Contains(line, "C-") {
			equipment = append(equipment, EquipmentInfo{
				Type: "circuit",
				Name: line,
			})
		}
	}
	
	logger.Info("Extracted %d equipment items from OCR text", len(equipment))
	return equipment
}

// EquipmentInfo represents extracted equipment information
type EquipmentInfo struct {
	Type     string
	Name     string
	Location string
	Notes    string
}

// SetLanguages sets the OCR languages to use
func (e *Extractor) SetLanguages(languages []string) {
	e.languages = languages
}

// IsOCRAvailable checks if OCR tools are available
func (e *Extractor) IsOCRAvailable() bool {
	return e.isTesseractAvailable()
}