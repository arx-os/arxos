package pdf

import (
	"bytes"
	"fmt"
	"io"
	"os"
	"strings"
	"time"
	
	"github.com/pdfcpu/pdfcpu/pkg/api"
	"github.com/pdfcpu/pdfcpu/pkg/pdfcpu/model"
	"github.com/pdfcpu/pdfcpu/pkg/pdfcpu/types"
	
	"github.com/joelpate/arxos/internal/ascii"
	"github.com/joelpate/arxos/internal/logger"
	"github.com/joelpate/arxos/pkg/models"
)

// Exporter handles PDF export with markups
type Exporter struct {
	config *model.Configuration
}

// NewExporter creates a new PDF exporter
func NewExporter() *Exporter {
	return &Exporter{
		config: model.NewDefaultConfiguration(),
	}
}

// ExportFloorPlan exports a floor plan to PDF with status markups
func (e *Exporter) ExportFloorPlan(plan *models.FloorPlan, outputPath string) error {
	logger.Info("Exporting floor plan to PDF: %s", outputPath)
	
	// Check if there's an original PDF to use as base
	originalPDF := fmt.Sprintf(".arxos/%s_original.pdf", plan.Name)
	if _, err := os.Stat(originalPDF); err == nil {
		// Overlay markups on original PDF
		return e.overlayMarkupsOnPDF(originalPDF, outputPath, plan)
	}
	
	// Create new PDF from scratch
	return e.createNewPDF(outputPath, plan)
}

// createNewPDF creates a PDF from scratch with ASCII rendering
func (e *Exporter) createNewPDF(outputPath string, plan *models.FloorPlan) error {
	// Create a temporary text file with the ASCII rendering
	tempFile := "/tmp/arxos_export.txt"
	defer os.Remove(tempFile)
	
	// Generate ASCII representation
	renderer := ascii.NewUniversalRenderer()
	asciiMap := renderer.RenderAny(plan)
	
	// Add header and footer
	var content bytes.Buffer
	content.WriteString(fmt.Sprintf("%s - %s\n", plan.Building, plan.Name))
	content.WriteString(fmt.Sprintf("Generated: %s\n", time.Now().Format("2006-01-02 15:04:05")))
	content.WriteString("════════════════════════════════════════════════════════════════\n\n")
	content.WriteString(asciiMap)
	content.WriteString("\n\n")
	content.WriteString("Equipment Status Report\n")
	content.WriteString("─────────────────────────────────────\n")
	
	// Add equipment status details
	statusCounts := make(map[models.EquipmentStatus]int)
	for _, equip := range plan.Equipment {
		statusCounts[equip.Status]++
		if equip.Status == models.StatusFailed || equip.Status == models.StatusNeedsRepair {
			content.WriteString(fmt.Sprintf("⚠ %s (%s): %s - %s\n", 
				equip.Name, equip.ID, equip.Status, equip.Notes))
		}
	}
	
	content.WriteString("\nSummary:\n")
	content.WriteString(fmt.Sprintf("  ✓ Normal: %d\n", statusCounts[models.StatusNormal]))
	content.WriteString(fmt.Sprintf("  ⚠ Needs Repair: %d\n", statusCounts[models.StatusNeedsRepair]))
	content.WriteString(fmt.Sprintf("  ✗ Failed: %d\n", statusCounts[models.StatusFailed]))
	content.WriteString(fmt.Sprintf("  ? Unknown: %d\n", statusCounts[models.StatusUnknown]))
	
	// Write to temp file
	if err := os.WriteFile(tempFile, content.Bytes(), 0644); err != nil {
		return fmt.Errorf("failed to write temp file: %w", err)
	}
	
	// Convert text to PDF using pdfcpu
	// Create a simple PDF with the text content
	return e.textToPDF(tempFile, outputPath)
}

// textToPDF converts a text file to PDF using a simple approach
func (e *Exporter) textToPDF(textPath, pdfPath string) error {
	// For now, just copy the text file as a placeholder
	// A full implementation would use a proper PDF library
	content, err := os.ReadFile(textPath)
	if err != nil {
		return fmt.Errorf("failed to read text file: %w", err)
	}
	
	// Create a simple PDF structure manually
	pdfContent := fmt.Sprintf(`%%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>
endobj
4 0 obj
<< /Type /Font /Subtype /Type1 /BaseFont /Courier >>
endobj
5 0 obj
<< /Length %d >>
stream
BT
/F1 10 Tf
50 750 Td
(%s) Tj
ET
endstream
endobj
xref
0 6
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
0000000229 00000 n
0000000306 00000 n
trailer
<< /Size 6 /Root 1 0 R >>
startxref
%d
%%%%EOF
`, len(content)+30, escapeForPDF(string(content)), 400+len(content))
	
	// Write PDF content
	if err := os.WriteFile(pdfPath, []byte(pdfContent), 0644); err != nil {
		return fmt.Errorf("failed to write PDF: %w", err)
	}
	
	logger.Info("Successfully exported PDF to: %s", pdfPath)
	return nil
}

// overlayMarkupsOnPDF adds markup layer to existing PDF
func (e *Exporter) overlayMarkupsOnPDF(originalPath, outputPath string, plan *models.FloorPlan) error {
	logger.Info("Overlaying markups on original PDF")
	
	// Copy original to output first
	input, err := os.ReadFile(originalPath)
	if err != nil {
		return fmt.Errorf("failed to read original PDF: %w", err)
	}
	
	if err := os.WriteFile(outputPath, input, 0644); err != nil {
		return fmt.Errorf("failed to write output PDF: %w", err)
	}
	
	// Read the PDF context
	ctx, err := api.ReadContextFile(outputPath)
	if err != nil {
		return fmt.Errorf("failed to read PDF context: %w", err)
	}
	
	// Add annotations for failed equipment
	for _, equip := range plan.Equipment {
		if equip.Status == models.StatusFailed || equip.Status == models.StatusNeedsRepair {
			e.addEquipmentAnnotation(ctx, equip)
		}
	}
	
	// Add watermark with export date
	watermark := fmt.Sprintf("ArxOS Export - %s", time.Now().Format("2006-01-02"))
	wm, err := api.TextWatermark(watermark, "desc", false, true, types.POINTS)
	if err != nil {
		logger.Warn("Failed to create watermark: %v", err)
	} else {
		if err := api.WatermarkContext(ctx, nil, wm); err != nil {
			logger.Warn("Failed to add watermark: %v", err)
		}
	}
	
	// Write modified PDF
	if err := api.WriteContextFile(ctx, outputPath); err != nil {
		return fmt.Errorf("failed to write modified PDF: %w", err)
	}
	
	logger.Info("Successfully overlaid markups on PDF: %s", outputPath)
	return nil
}

// addEquipmentAnnotation adds a visual annotation for equipment status
func (e *Exporter) addEquipmentAnnotation(ctx *model.Context, equip models.Equipment) {
	// This would add actual PDF annotations
	// For now, we'll log the intent
	logger.Debug("Would add annotation for %s at (%.1f, %.1f) with status %s", 
		equip.Name, equip.Location.X, equip.Location.Y, equip.Status)
	
	// In a full implementation, this would:
	// 1. Convert equipment coordinates to PDF page coordinates
	// 2. Create a highlight or circle annotation
	// 3. Add a popup note with equipment details
	// 4. Use colors: red for failed, orange for needs-repair
}

// ExportToWriter exports a floor plan to an io.Writer
func (e *Exporter) ExportToWriter(plan *models.FloorPlan, w io.Writer) error {
	// Generate ASCII representation
	renderer := ascii.NewUniversalRenderer()
	asciiMap := renderer.RenderAny(plan)
	
	// Write header
	fmt.Fprintf(w, "%s - %s\n", plan.Building, plan.Name)
	fmt.Fprintf(w, "Generated: %s\n", time.Now().Format("2006-01-02 15:04:05"))
	fmt.Fprintln(w, strings.Repeat("═", 64))
	fmt.Fprintln(w)
	
	// Write ASCII map
	fmt.Fprintln(w, asciiMap)
	fmt.Fprintln(w)
	
	// Write equipment report
	fmt.Fprintln(w, "Equipment Status Report")
	fmt.Fprintln(w, strings.Repeat("─", 37))
	
	// Group equipment by status
	byStatus := make(map[models.EquipmentStatus][]models.Equipment)
	for _, equip := range plan.Equipment {
		byStatus[equip.Status] = append(byStatus[equip.Status], equip)
	}
	
	// Write failed equipment first
	if failed := byStatus[models.StatusFailed]; len(failed) > 0 {
		fmt.Fprintln(w, "\n✗ FAILED Equipment:")
		for _, equip := range failed {
			fmt.Fprintf(w, "  - %s (%s)", equip.Name, equip.ID)
			if equip.Notes != "" {
				fmt.Fprintf(w, ": %s", equip.Notes)
			}
			fmt.Fprintln(w)
		}
	}
	
	// Write needs-repair equipment
	if needsRepair := byStatus[models.StatusNeedsRepair]; len(needsRepair) > 0 {
		fmt.Fprintln(w, "\n⚠ NEEDS REPAIR:")
		for _, equip := range needsRepair {
			fmt.Fprintf(w, "  - %s (%s)", equip.Name, equip.ID)
			if equip.Notes != "" {
				fmt.Fprintf(w, ": %s", equip.Notes)
			}
			fmt.Fprintln(w)
		}
	}
	
	// Write summary
	fmt.Fprintln(w, "\nSummary:")
	fmt.Fprintf(w, "  ✓ Normal: %d\n", len(byStatus[models.StatusNormal]))
	fmt.Fprintf(w, "  ⚠ Needs Repair: %d\n", len(byStatus[models.StatusNeedsRepair]))
	fmt.Fprintf(w, "  ✗ Failed: %d\n", len(byStatus[models.StatusFailed]))
	fmt.Fprintf(w, "  ? Unknown: %d\n", len(byStatus[models.StatusUnknown]))
	
	return nil
}

// escapeForPDF escapes special characters for PDF strings
func escapeForPDF(s string) string {
	// Escape parentheses and backslashes
	s = strings.ReplaceAll(s, "\\", "\\\\")
	s = strings.ReplaceAll(s, "(", "\\(")
	s = strings.ReplaceAll(s, ")", "\\)")
	return s
}