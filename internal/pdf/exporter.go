package pdf

import (
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"time"

	"github.com/pdfcpu/pdfcpu/pkg/pdfcpu/model"

	"github.com/joelpate/arxos/internal/logger"
	"github.com/joelpate/arxos/pkg/models"
)

// Exporter handles PDF export with equipment markups
type Exporter struct {
	config *model.Configuration
}

// NewExporter creates a new PDF exporter
func NewExporter() *Exporter {
	return &Exporter{
		config: model.NewDefaultConfiguration(),
	}
}

// ExportWithMarkups exports a floor plan with equipment status markups
func (e *Exporter) ExportWithMarkups(plan *models.FloorPlan, originalPDF, outputPath string) error {
	logger.Info("Exporting floor plan with markups to: %s", outputPath)
	
	// If we have an original PDF, overlay markups on it
	if originalPDF != "" && fileExists(originalPDF) {
		return e.overlayMarkupsOnPDF(plan, originalPDF, outputPath)
	}
	
	// Otherwise, create a new PDF from scratch
	return e.createPDFFromScratch(plan, outputPath)
}

// overlayMarkupsOnPDF adds markups to an existing PDF
func (e *Exporter) overlayMarkupsOnPDF(plan *models.FloorPlan, inputPath, outputPath string) error {
	// For now, just copy the original PDF and append a report
	// Full PDF markup overlay would require more complex PDF manipulation
	
	// Copy the original PDF to output location
	if err := copyFile(inputPath, outputPath); err != nil {
		return fmt.Errorf("failed to copy PDF: %w", err)
	}
	
	// Generate report as separate file for now
	reportPath := strings.TrimSuffix(outputPath, ".pdf") + "_report.txt"
	report := e.generateTextReport(plan)
	if err := os.WriteFile(reportPath, []byte(report), 0644); err != nil {
		logger.Warn("Failed to create report file: %v", err)
	} else {
		logger.Info("Created inspection report at: %s", reportPath)
	}
	
	logger.Info("Successfully exported PDF (original with separate report)")
	return nil
}

// createPDFFromScratch creates a new PDF with floor plan visualization
func (e *Exporter) createPDFFromScratch(plan *models.FloorPlan, outputPath string) error {
	logger.Info("Creating new PDF from floor plan data")
	
	// For now, create a simple text file that can be converted to PDF
	// This is a temporary implementation until we have proper PDF generation
	
	content := e.generateTextReport(plan)
	
	// Create a temporary text file
	tempFile := outputPath + ".txt"
	if err := os.WriteFile(tempFile, []byte(content), 0644); err != nil {
		return fmt.Errorf("failed to write temp file: %w", err)
	}
	
	// For now, just copy the text file as a placeholder
	// In production, this would use a proper PDF library to generate the PDF
	if err := os.WriteFile(outputPath, []byte(content), 0644); err != nil {
		return fmt.Errorf("failed to write PDF: %w", err)
	}
	
	// Clean up temp file
	os.Remove(tempFile)
	
	logger.Info("Successfully created PDF export (text format)")
	return nil
}

// generateTextReport generates a text report of the floor plan
func (e *Exporter) generateTextReport(plan *models.FloorPlan) string {
	var report string
	
	// Header
	report += fmt.Sprintf("FLOOR PLAN INSPECTION REPORT\n")
	report += fmt.Sprintf("=" + strings.Repeat("=", 50) + "\n\n")
	
	// Building info
	report += fmt.Sprintf("Building: %s\n", plan.Building)
	report += fmt.Sprintf("Floor: %s\n", plan.Name)
	report += fmt.Sprintf("Generated: %s\n", time.Now().Format("2006-01-02 15:04:05"))
	report += fmt.Sprintf("\n" + strings.Repeat("-", 50) + "\n\n")
	
	// Equipment Status Summary
	report += "EQUIPMENT STATUS SUMMARY\n"
	report += strings.Repeat("-", 30) + "\n"
	
	statusCounts := e.countByStatus(plan)
	total := len(plan.Equipment)
	
	report += fmt.Sprintf("Total Equipment: %d\n", total)
	report += fmt.Sprintf("  ✓ Normal: %d\n", statusCounts[models.StatusNormal])
	report += fmt.Sprintf("  ⚠ Needs Repair: %d\n", statusCounts[models.StatusNeedsRepair])
	report += fmt.Sprintf("  ✗ Failed: %d\n", statusCounts[models.StatusFailed])
	report += fmt.Sprintf("  ? Unknown: %d\n", statusCounts[models.StatusUnknown])
	
	report += fmt.Sprintf("\n" + strings.Repeat("-", 50) + "\n\n")
	
	// Items needing attention
	var failedItems []models.Equipment
	var repairItems []models.Equipment
	
	for _, equip := range plan.Equipment {
		if equip.Status == models.StatusFailed {
			failedItems = append(failedItems, equip)
		} else if equip.Status == models.StatusNeedsRepair {
			repairItems = append(repairItems, equip)
		}
	}
	
	if len(failedItems) > 0 {
		report += "FAILED EQUIPMENT (URGENT)\n"
		report += strings.Repeat("-", 30) + "\n"
		for _, equip := range failedItems {
			report += fmt.Sprintf("\n✗ %s (%s)\n", equip.Name, equip.Type)
			report += fmt.Sprintf("  Location: Room %s\n", equip.RoomID)
			if equip.Notes != "" {
				report += fmt.Sprintf("  Notes: %s\n", equip.Notes)
			}
			if equip.MarkedBy != "" {
				report += fmt.Sprintf("  Marked by: %s at %s\n", 
					equip.MarkedBy, equip.MarkedAt.Format("2006-01-02 15:04"))
			}
		}
		report += "\n"
	}
	
	if len(repairItems) > 0 {
		report += "EQUIPMENT NEEDING REPAIR\n"
		report += strings.Repeat("-", 30) + "\n"
		for _, equip := range repairItems {
			report += fmt.Sprintf("\n⚠ %s (%s)\n", equip.Name, equip.Type)
			report += fmt.Sprintf("  Location: Room %s\n", equip.RoomID)
			if equip.Notes != "" {
				report += fmt.Sprintf("  Notes: %s\n", equip.Notes)
			}
			if equip.MarkedBy != "" {
				report += fmt.Sprintf("  Marked by: %s at %s\n", 
					equip.MarkedBy, equip.MarkedAt.Format("2006-01-02 15:04"))
			}
		}
		report += "\n"
	}
	
	// Room-by-room breakdown
	report += strings.Repeat("=", 50) + "\n"
	report += "ROOM-BY-ROOM EQUIPMENT LIST\n"
	report += strings.Repeat("-", 30) + "\n\n"
	
	for _, room := range plan.Rooms {
		if len(room.Equipment) > 0 {
			report += fmt.Sprintf("Room: %s\n", room.Name)
			for _, equipID := range room.Equipment {
				equip := e.findEquipment(plan, equipID)
				if equip != nil {
					statusSymbol := e.getStatusSymbol(equip.Status)
					report += fmt.Sprintf("  %s %s (%s)\n", statusSymbol, equip.Name, equip.Type)
				}
			}
			report += "\n"
		}
	}
	
	report += strings.Repeat("=", 50) + "\n"
	report += "END OF REPORT\n"
	
	return report
}


// findEquipment finds equipment by ID
func (e *Exporter) findEquipment(plan *models.FloorPlan, id string) *models.Equipment {
	for i := range plan.Equipment {
		if plan.Equipment[i].ID == id {
			return &plan.Equipment[i]
		}
	}
	return nil
}

// getStatusSymbol returns a visual symbol for equipment status
func (e *Exporter) getStatusSymbol(status models.EquipmentStatus) string {
	switch status {
	case models.StatusNormal:
		return "✓"
	case models.StatusNeedsRepair:
		return "⚠"
	case models.StatusFailed:
		return "✗"
	default:
		return "?"
	}
}

// countByStatus counts equipment by status
func (e *Exporter) countByStatus(plan *models.FloorPlan) map[models.EquipmentStatus]int {
	counts := make(map[models.EquipmentStatus]int)
	for _, equip := range plan.Equipment {
		counts[equip.Status]++
	}
	return counts
}

// fileExists checks if a file exists
func fileExists(path string) bool {
	_, err := os.Stat(path)
	return !os.IsNotExist(err)
}

// copyFile copies a file from src to dst
func copyFile(src, dst string) error {
	// Ensure destination directory exists
	if err := os.MkdirAll(filepath.Dir(dst), 0755); err != nil {
		return err
	}
	
	input, err := os.ReadFile(src)
	if err != nil {
		return err
	}
	
	return os.WriteFile(dst, input, 0644)
}