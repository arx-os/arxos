package formats

import (
	"bytes"
	"fmt"
	"image"
	"image/jpeg"
	"image/png"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"sync"

	"github.com/arx-os/arxos/internal/common/logger"
)

// OCREngine provides OCR capabilities for scanned documents
type OCREngine struct {
	engine      string // "tesseract", "gosseract", or "cloud"
	language    string
	tempDir     string
	concurrency int
	mu          sync.RWMutex
}

// OCRResult contains OCR processing results
type OCRResult struct {
	Text       string
	Confidence float64
	Language   string
	Metadata   map[string]interface{}
}

// NewOCREngine creates a new OCR engine
func NewOCREngine() (*OCREngine, error) {
	engine := &OCREngine{
		language:    "eng",
		concurrency: 4,
	}

	// Check which OCR engine is available
	if engine.isTesseractAvailable() {
		engine.engine = "tesseract"
		logger.Info("Using Tesseract OCR engine")
	} else {
		return nil, fmt.Errorf("no OCR engine available")
	}

	// Create temp directory for OCR processing
	tempDir, err := os.MkdirTemp("", "ocr_temp_*")
	if err != nil {
		return nil, fmt.Errorf("failed to create temp directory: %w", err)
	}
	engine.tempDir = tempDir

	return engine, nil
}

// ProcessImages performs OCR on multiple images
func (e *OCREngine) ProcessImages(images []ExtractedImage) (string, error) {
	if len(images) == 0 {
		return "", nil
	}

	var results []string
	var wg sync.WaitGroup
	resultsChan := make(chan string, len(images))
	errorsChan := make(chan error, len(images))

	// Process images concurrently with limited concurrency
	semaphore := make(chan struct{}, e.concurrency)

	for i, img := range images {
		wg.Add(1)
		go func(idx int, image ExtractedImage) {
			defer wg.Done()

			semaphore <- struct{}{} // Acquire
			defer func() { <-semaphore }() // Release

			text, err := e.processImage(image, idx)
			if err != nil {
				errorsChan <- fmt.Errorf("failed to process image %d: %w", idx, err)
				return
			}

			resultsChan <- text
		}(i, img)
	}

	// Wait for all goroutines to complete
	go func() {
		wg.Wait()
		close(resultsChan)
		close(errorsChan)
	}()

	// Collect results
	var errors []error
	for {
		select {
		case text, ok := <-resultsChan:
			if !ok {
				resultsChan = nil
			} else if text != "" {
				results = append(results, text)
			}
		case err, ok := <-errorsChan:
			if !ok {
				errorsChan = nil
			} else if err != nil {
				errors = append(errors, err)
			}
		}

		if resultsChan == nil && errorsChan == nil {
			break
		}
	}

	// Log errors but continue
	for _, err := range errors {
		logger.Warn("OCR error: %v", err)
	}

	return strings.Join(results, "\n\n"), nil
}

// processImage performs OCR on a single image
func (e *OCREngine) processImage(img ExtractedImage, index int) (string, error) {
	// Save image to temp file
	tempFile := filepath.Join(e.tempDir, fmt.Sprintf("ocr_image_%d", index))

	// Determine image format and save
	switch img.Format {
	case "jpeg", "jpg":
		tempFile += ".jpg"
		if err := e.saveAsJPEG(img.Data, tempFile); err != nil {
			return "", err
		}
	case "png":
		tempFile += ".png"
		if err := e.saveAsPNG(img.Data, tempFile); err != nil {
			return "", err
		}
	default:
		// Try to decode and save as PNG
		tempFile += ".png"
		if err := e.saveImageData(img.Data, tempFile); err != nil {
			return "", err
		}
	}
	defer os.Remove(tempFile)

	// Perform OCR based on engine
	switch e.engine {
	case "tesseract":
		return e.tesseractOCR(tempFile)
	default:
		return "", fmt.Errorf("unsupported OCR engine: %s", e.engine)
	}
}

// tesseractOCR performs OCR using Tesseract
func (e *OCREngine) tesseractOCR(imagePath string) (string, error) {
	// Run tesseract command
	cmd := exec.Command("tesseract", imagePath, "-", "-l", e.language, "--psm", "3")
	output, err := cmd.Output()
	if err != nil {
		return "", fmt.Errorf("tesseract failed: %w", err)
	}

	text := string(output)

	// Clean up the text
	text = e.cleanOCRText(text)

	return text, nil
}

// cleanOCRText cleans up OCR output
func (e *OCREngine) cleanOCRText(text string) string {
	// Remove excessive whitespace
	lines := strings.Split(text, "\n")
	var cleaned []string

	for _, line := range lines {
		line = strings.TrimSpace(line)
		if line != "" {
			cleaned = append(cleaned, line)
		}
	}

	text = strings.Join(cleaned, "\n")

	// Fix common OCR errors
	replacements := map[string]string{
		"ﬂ":  "fl",
		"ﬁ":  "fi",
		"œ":  "oe",
		"æ":  "ae",
		"™":  "TM",
		"©":  "(c)",
		"®":  "(R)",
		"…":  "...",
		"—":  "-",
		"–":  "-",
		"\u201C": "\"", // Left double quotation mark
		"\u201D": "\"", // Right double quotation mark
		"\u2018": "'",  // Left single quotation mark
		"\u2019": "'",  // Right single quotation mark
	}

	for old, new := range replacements {
		text = strings.ReplaceAll(text, old, new)
	}

	return text
}

// isTesseractAvailable checks if Tesseract is installed
func (e *OCREngine) isTesseractAvailable() bool {
	cmd := exec.Command("tesseract", "--version")
	err := cmd.Run()
	return err == nil
}

// saveAsJPEG saves image data as JPEG
func (e *OCREngine) saveAsJPEG(data []byte, path string) error {
	img, _, err := image.Decode(bytes.NewReader(data))
	if err != nil {
		// Data might already be JPEG
		return os.WriteFile(path, data, 0644)
	}

	file, err := os.Create(path)
	if err != nil {
		return err
	}
	defer file.Close()

	return jpeg.Encode(file, img, &jpeg.Options{Quality: 95})
}

// saveAsPNG saves image data as PNG
func (e *OCREngine) saveAsPNG(data []byte, path string) error {
	img, _, err := image.Decode(bytes.NewReader(data))
	if err != nil {
		// Data might already be PNG
		return os.WriteFile(path, data, 0644)
	}

	file, err := os.Create(path)
	if err != nil {
		return err
	}
	defer file.Close()

	return png.Encode(file, img)
}

// saveImageData saves raw image data
func (e *OCREngine) saveImageData(data []byte, path string) error {
	// Try to decode and re-encode as PNG
	img, _, err := image.Decode(bytes.NewReader(data))
	if err != nil {
		// If decode fails, save raw data
		return os.WriteFile(path, data, 0644)
	}

	file, err := os.Create(path)
	if err != nil {
		return err
	}
	defer file.Close()

	return png.Encode(file, img)
}

// ProcessPDF performs OCR on an entire PDF
func (e *OCREngine) ProcessPDF(pdfPath string) (*OCRResult, error) {
	// Convert PDF pages to images first
	images, err := e.pdfToImages(pdfPath)
	if err != nil {
		return nil, fmt.Errorf("failed to convert PDF to images: %w", err)
	}

	// Process all images
	text, err := e.ProcessImages(images)
	if err != nil {
		return nil, fmt.Errorf("OCR processing failed: %w", err)
	}

	result := &OCRResult{
		Text:     text,
		Language: e.language,
		Metadata: map[string]interface{}{
			"engine":     e.engine,
			"num_pages":  len(images),
			"processed":  true,
		},
	}

	// Estimate confidence based on text quality
	result.Confidence = e.estimateConfidence(text)

	return result, nil
}

// pdfToImages converts PDF pages to images
func (e *OCREngine) pdfToImages(pdfPath string) ([]ExtractedImage, error) {
	var images []ExtractedImage

	// Use pdftoppm or similar tool to convert PDF to images
	// This is a simplified implementation
	cmd := exec.Command("pdftoppm", "-png", pdfPath, filepath.Join(e.tempDir, "page"))
	if err := cmd.Run(); err != nil {
		// Try alternative method using ImageMagick
		cmd = exec.Command("convert", "-density", "300", pdfPath, filepath.Join(e.tempDir, "page-%03d.png"))
		if err := cmd.Run(); err != nil {
			return nil, fmt.Errorf("failed to convert PDF to images: %w", err)
		}
	}

	// Read generated images
	files, err := filepath.Glob(filepath.Join(e.tempDir, "page*.png"))
	if err != nil {
		return nil, err
	}

	for i, file := range files {
		data, err := os.ReadFile(file)
		if err != nil {
			continue
		}

		images = append(images, ExtractedImage{
			Data:   data,
			Format: "png",
			Page:   i + 1,
		})

		// Clean up temp file
		os.Remove(file)
	}

	return images, nil
}

// estimateConfidence estimates OCR confidence based on text quality
func (e *OCREngine) estimateConfidence(text string) float64 {
	if text == "" {
		return 0.0
	}

	confidence := 0.5 // Base confidence

	// Check for common words (indicates good OCR)
	commonWords := []string{"the", "and", "of", "to", "in", "a", "is", "that", "it", "for"}
	wordCount := 0
	commonWordCount := 0

	words := strings.Fields(strings.ToLower(text))
	for _, word := range words {
		wordCount++
		for _, common := range commonWords {
			if word == common {
				commonWordCount++
				break
			}
		}
	}

	if wordCount > 0 {
		commonRatio := float64(commonWordCount) / float64(wordCount)
		if commonRatio > 0.05 && commonRatio < 0.3 {
			confidence += 0.2
		}
	}

	// Check for excessive special characters (indicates poor OCR)
	specialCount := 0
	for _, r := range text {
		if !((r >= 'a' && r <= 'z') || (r >= 'A' && r <= 'Z') ||
			(r >= '0' && r <= '9') || r == ' ' || r == '.' || r == ',' ||
			r == '\n' || r == '\t') {
			specialCount++
		}
	}

	specialRatio := float64(specialCount) / float64(len(text))
	if specialRatio < 0.1 {
		confidence += 0.2
	} else if specialRatio > 0.3 {
		confidence -= 0.2
	}

	// Check for reasonable line lengths
	lines := strings.Split(text, "\n")
	reasonableLines := 0
	for _, line := range lines {
		length := len(strings.TrimSpace(line))
		if length > 10 && length < 100 {
			reasonableLines++
		}
	}

	if len(lines) > 0 {
		lineRatio := float64(reasonableLines) / float64(len(lines))
		if lineRatio > 0.5 {
			confidence += 0.1
		}
	}

	// Clamp confidence between 0 and 1
	if confidence < 0 {
		confidence = 0
	} else if confidence > 1 {
		confidence = 1
	}

	return confidence
}

// SetLanguage sets the OCR language
func (e *OCREngine) SetLanguage(lang string) {
	e.mu.Lock()
	defer e.mu.Unlock()
	e.language = lang
}

// Cleanup cleans up temporary files
func (e *OCREngine) Cleanup() error {
	if e.tempDir != "" {
		return os.RemoveAll(e.tempDir)
	}
	return nil
}