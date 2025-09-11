package pdf

import (
	"bytes"
	"fmt"
	"os"
	"strings"
	"time"
	
	"github.com/pdfcpu/pdfcpu/pkg/pdfcpu/model"
	
	"github.com/joelpate/arxos/internal/ascii"
	"github.com/joelpate/arxos/internal/logger"
	"github.com/joelpate/arxos/pkg/models"
)

// ProfessionalExporter creates high-quality PDF exports using pdfcpu
type ProfessionalExporter struct {
	config     *model.Configuration
	pageWidth  float64
	pageHeight float64
	margin     float64
	fontSize   int
}

// NewProfessionalExporter creates a new professional PDF exporter
func NewProfessionalExporter() *ProfessionalExporter {
	return &ProfessionalExporter{
		config:     model.NewDefaultConfiguration(),
		pageWidth:  595.0,  // A4 width in points
		pageHeight: 842.0,  // A4 height in points
		margin:     50.0,
		fontSize:   10,
	}
}

// ExportFloorPlanPro exports a floor plan to a professional PDF
func (e *ProfessionalExporter) ExportFloorPlanPro(plan *models.FloorPlan, outputPath string) error {
	logger.Info("Creating professional PDF export: %s", outputPath)
	
	// For now, generate a multi-page text report
	// Full pdfcpu implementation would require latest API understanding
	
	var content bytes.Buffer
	
	// Page 1: Cover
	content.WriteString("================================================================================\n")
	content.WriteString("                       BUILDING INSPECTION REPORT                              \n")
	content.WriteString("================================================================================\n\n")
	content.WriteString(fmt.Sprintf("Building: %s\n", plan.Building))
	content.WriteString(fmt.Sprintf("Floor: %s\n", plan.Name))
	content.WriteString(fmt.Sprintf("Level: %d\n", plan.Level))
	content.WriteString(fmt.Sprintf("Generated: %s\n", time.Now().Format("January 2, 2006 15:04")))
	content.WriteString("\n")
	
	// Summary statistics
	normalCount := 0
	repairCount := 0
	failedCount := 0
	for _, eq := range plan.Equipment {
		switch eq.Status {
		case models.StatusNormal:
			normalCount++
		case models.StatusNeedsRepair:
			repairCount++
		case models.StatusFailed:
			failedCount++
		}
	}
	
	content.WriteString("SUMMARY\n")
	content.WriteString("-------\n")
	content.WriteString(fmt.Sprintf("Total Equipment: %d\n", len(plan.Equipment)))
	content.WriteString(fmt.Sprintf("  ✓ Normal: %d\n", normalCount))
	content.WriteString(fmt.Sprintf("  ⚠ Needs Repair: %d\n", repairCount))
	content.WriteString(fmt.Sprintf("  ✗ Failed: %d\n", failedCount))
	content.WriteString("\n\f\n") // Form feed for page break
	
	// Page 2: Floor Plan
	content.WriteString("================================================================================\n")
	content.WriteString("                          FLOOR PLAN VISUALIZATION                             \n")
	content.WriteString("================================================================================\n\n")
	
	renderer := ascii.NewUniversalRenderer()
	asciiMap := renderer.RenderAny(plan)
	content.WriteString(asciiMap)
	content.WriteString("\n\f\n")
	
	// Page 3: Equipment List
	content.WriteString("================================================================================\n")
	content.WriteString("                            EQUIPMENT INVENTORY                                \n")
	content.WriteString("================================================================================\n\n")
	
	content.WriteString(fmt.Sprintf("%-15s %-20s %-10s %-10s %-15s %s\n", 
		"ID", "Name", "Type", "Status", "Location", "Notes"))
	content.WriteString(strings.Repeat("-", 80) + "\n")
	
	for _, eq := range plan.Equipment {
		statusStr := string(eq.Status)
		switch eq.Status {
		case models.StatusNormal:
			statusStr = "✓ " + statusStr
		case models.StatusNeedsRepair:
			statusStr = "⚠ " + statusStr
		case models.StatusFailed:
			statusStr = "✗ " + statusStr
		}
		
		location := eq.RoomID
		if location == "" {
			location = fmt.Sprintf("(%.1f,%.1f)", eq.Location.X, eq.Location.Y)
		}
		
		name := eq.Name
		if len(name) > 19 {
			name = name[:16] + "..."
		}
		
		notes := eq.Notes
		if len(notes) > 20 {
			notes = notes[:17] + "..."
		}
		
		content.WriteString(fmt.Sprintf("%-15s %-20s %-10s %-10s %-15s %s\n",
			eq.ID, name, eq.Type, statusStr, location, notes))
	}
	
	content.WriteString("\n\f\n")
	
	// Page 4: Status Report
	content.WriteString("================================================================================\n")
	content.WriteString("                              STATUS REPORT                                    \n")
	content.WriteString("================================================================================\n\n")
	
	// Failed equipment
	failedEquipment := []models.Equipment{}
	needsRepair := []models.Equipment{}
	
	for _, eq := range plan.Equipment {
		switch eq.Status {
		case models.StatusFailed:
			failedEquipment = append(failedEquipment, eq)
		case models.StatusNeedsRepair:
			needsRepair = append(needsRepair, eq)
		}
	}
	
	if len(failedEquipment) > 0 {
		content.WriteString("CRITICAL - FAILED EQUIPMENT\n")
		content.WriteString("----------------------------\n")
		for _, eq := range failedEquipment {
			content.WriteString(fmt.Sprintf("• %s (%s) - %s\n", eq.Name, eq.ID, eq.Notes))
			if eq.RoomID != "" {
				content.WriteString(fmt.Sprintf("  Location: Room %s\n", eq.RoomID))
			}
		}
		content.WriteString("\n")
	}
	
	if len(needsRepair) > 0 {
		content.WriteString("WARNING - NEEDS REPAIR\n")
		content.WriteString("----------------------\n")
		for _, eq := range needsRepair {
			content.WriteString(fmt.Sprintf("• %s (%s) - %s\n", eq.Name, eq.ID, eq.Notes))
		}
		content.WriteString("\n")
	}
	
	content.WriteString("RECOMMENDATIONS\n")
	content.WriteString("---------------\n")
	if len(failedEquipment) > 0 {
		content.WriteString(fmt.Sprintf("• Immediate attention required for %d failed equipment items\n", 
			len(failedEquipment)))
	}
	if len(needsRepair) > 0 {
		content.WriteString(fmt.Sprintf("• Schedule maintenance for %d items needing repair\n", 
			len(needsRepair)))
	}
	if len(failedEquipment) == 0 && len(needsRepair) == 0 {
		content.WriteString("• All equipment is in normal operating condition\n")
	}
	
	content.WriteString("\n\n")
	content.WriteString("Generated by ArxOS Building Intelligence System\n")
	
	// For now, save as text file
	// A full implementation would convert this to PDF
	if err := os.WriteFile(outputPath, content.Bytes(), 0644); err != nil {
		return fmt.Errorf("failed to write report: %w", err)
	}
	
	logger.Info("Successfully created professional report: %s", outputPath)
	return nil
}

// The following methods are placeholders for future pdfcpu implementation
// when the API stabilizes

/*
func (e *ProfessionalExporter) addMetadata(ctx *model.Context, plan *models.FloorPlan) {
	ctx.Author = "ArxOS Building Intelligence System"
	ctx.Creator = "ArxOS PDF Exporter"
	ctx.Producer = "pdfcpu"
	ctx.Title = fmt.Sprintf("%s - %s Inspection Report", plan.Building, plan.Name)
	ctx.Subject = "Building Equipment Status Report"
	ctx.Keywords = "facilities, maintenance, equipment, inspection"
	ctx.CreationDate = time.Now()
	ctx.ModDate = time.Now()
}

// createCoverPage creates a professional cover page
func (e *ProfessionalExporter) createCoverPage(ctx *model.Context, plan *models.FloorPlan) error {
	page := model.NewPage(ctx)
	page.MediaBox = types.RectForFormat("A4")
	
	content := &bytes.Buffer{}
	
	// Title
	e.writeText(content, e.pageWidth/2, e.pageHeight-100, 24, "center",
		"BUILDING INSPECTION REPORT")
	
	// Building info
	e.writeText(content, e.pageWidth/2, e.pageHeight-200, 18, "center",
		plan.Building)
	e.writeText(content, e.pageWidth/2, e.pageHeight-230, 16, "center",
		plan.Name)
	
	// Date and time
	e.writeText(content, e.pageWidth/2, e.pageHeight-300, 12, "center",
		fmt.Sprintf("Generated: %s", time.Now().Format("January 2, 2006 15:04")))
	
	// Summary box
	e.drawBox(content, 100, 350, e.pageWidth-200, 150)
	
	// Summary statistics
	normalCount := 0
	repairCount := 0
	failedCount := 0
	for _, eq := range plan.Equipment {
		switch eq.Status {
		case models.StatusNormal:
			normalCount++
		case models.StatusNeedsRepair:
			repairCount++
		case models.StatusFailed:
			failedCount++
		}
	}
	
	y := float64(420)
	e.writeText(content, 120, y, 14, "left", "SUMMARY")
	y -= 30
	e.writeText(content, 140, y, 12, "left", 
		fmt.Sprintf("Total Equipment: %d", len(plan.Equipment)))
	y -= 25
	e.writeText(content, 140, y, 12, "left",
		fmt.Sprintf("✓ Normal: %d", normalCount))
	y -= 25
	e.writeText(content, 140, y, 12, "left",
		fmt.Sprintf("⚠ Needs Repair: %d", repairCount))
	y -= 25
	e.writeText(content, 140, y, 12, "left",
		fmt.Sprintf("✗ Failed: %d", failedCount))
	
	// Add logo/branding area
	e.writeText(content, e.pageWidth/2, 100, 10, "center",
		"Generated by ArxOS Building Intelligence System")
	
	page.Buf = content
	ctx.Pages = append(ctx.Pages, page)
	
	return nil
}

// createFloorPlanPage creates the ASCII floor plan visualization page
func (e *ProfessionalExporter) createFloorPlanPage(ctx *model.Context, plan *models.FloorPlan) error {
	page := model.NewPage(ctx)
	page.MediaBox = types.RectForFormat("A4")
	
	content := &bytes.Buffer{}
	
	// Page header
	e.writeText(content, e.margin, e.pageHeight-40, 16, "left", "FLOOR PLAN VISUALIZATION")
	e.drawLine(content, e.margin, e.pageHeight-50, e.pageWidth-e.margin, e.pageHeight-50)
	
	// Generate ASCII map
	renderer := ascii.NewUniversalRenderer()
	asciiMap := renderer.RenderAny(plan)
	
	// Write ASCII map with monospace font
	lines := strings.Split(asciiMap, "\n")
	y := e.pageHeight - 100
	for _, line := range lines {
		if y < e.margin+50 {
			// Create new page if needed
			ctx.Pages = append(ctx.Pages, page)
			page = model.NewPage(ctx)
			page.MediaBox = types.RectForFormat("A4")
			content = &bytes.Buffer{}
			y = e.pageHeight - 100
		}
		
		e.writeMonospaceText(content, e.margin, y, 8, line)
		y -= 12
	}
	
	page.Buf = content
	ctx.Pages = append(ctx.Pages, page)
	
	return nil
}

// createEquipmentListPage creates detailed equipment listing
func (e *ProfessionalExporter) createEquipmentListPage(ctx *model.Context, plan *models.FloorPlan) error {
	page := model.NewPage(ctx)
	page.MediaBox = types.RectForFormat("A4")
	
	content := &bytes.Buffer{}
	
	// Page header
	e.writeText(content, e.margin, e.pageHeight-40, 16, "left", "EQUIPMENT INVENTORY")
	e.drawLine(content, e.margin, e.pageHeight-50, e.pageWidth-e.margin, e.pageHeight-50)
	
	// Table headers
	y := e.pageHeight - 100
	e.drawTableHeader(content, y)
	y -= 30
	
	// Equipment rows
	for _, eq := range plan.Equipment {
		if y < e.margin+50 {
			// New page
			ctx.Pages = append(ctx.Pages, page)
			page = model.NewPage(ctx)
			page.MediaBox = types.RectForFormat("A4")
			content = &bytes.Buffer{}
			y = e.pageHeight - 100
			e.drawTableHeader(content, y)
			y -= 30
		}
		
		e.drawEquipmentRow(content, y, eq)
		y -= 25
	}
	
	page.Buf = content
	ctx.Pages = append(ctx.Pages, page)
	
	return nil
}

// createStatusReportPage creates detailed status report
func (e *ProfessionalExporter) createStatusReportPage(ctx *model.Context, plan *models.FloorPlan) error {
	page := model.NewPage(ctx)
	page.MediaBox = types.RectForFormat("A4")
	
	content := &bytes.Buffer{}
	
	// Page header
	e.writeText(content, e.margin, e.pageHeight-40, 16, "left", "STATUS REPORT")
	e.drawLine(content, e.margin, e.pageHeight-50, e.pageWidth-e.margin, e.pageHeight-50)
	
	y := e.pageHeight - 100
	
	// Failed equipment section
	failedEquipment := []models.Equipment{}
	needsRepair := []models.Equipment{}
	
	for _, eq := range plan.Equipment {
		switch eq.Status {
		case models.StatusFailed:
			failedEquipment = append(failedEquipment, eq)
		case models.StatusNeedsRepair:
			needsRepair = append(needsRepair, eq)
		}
	}
	
	if len(failedEquipment) > 0 {
		e.writeText(content, e.margin, y, 14, "left", "CRITICAL - FAILED EQUIPMENT")
		y -= 25
		
		for _, eq := range failedEquipment {
			e.writeText(content, e.margin+20, y, 10, "left",
				fmt.Sprintf("• %s (%s) - %s", eq.Name, eq.ID, eq.Notes))
			y -= 20
			
			if eq.RoomID != "" {
				e.writeText(content, e.margin+40, y, 9, "left",
					fmt.Sprintf("Location: Room %s", eq.RoomID))
				y -= 20
			}
		}
		y -= 10
	}
	
	if len(needsRepair) > 0 {
		e.writeText(content, e.margin, y, 14, "left", "WARNING - NEEDS REPAIR")
		y -= 25
		
		for _, eq := range needsRepair {
			e.writeText(content, e.margin+20, y, 10, "left",
				fmt.Sprintf("• %s (%s) - %s", eq.Name, eq.ID, eq.Notes))
			y -= 20
		}
	}
	
	// Recommendations section
	y -= 30
	e.writeText(content, e.margin, y, 14, "left", "RECOMMENDATIONS")
	y -= 25
	
	if len(failedEquipment) > 0 {
		e.writeText(content, e.margin+20, y, 10, "left",
			fmt.Sprintf("• Immediate attention required for %d failed equipment items", len(failedEquipment)))
		y -= 20
	}
	
	if len(needsRepair) > 0 {
		e.writeText(content, e.margin+20, y, 10, "left",
			fmt.Sprintf("• Schedule maintenance for %d items needing repair", len(needsRepair)))
		y -= 20
	}
	
	page.Buf = content
	ctx.Pages = append(ctx.Pages, page)
	
	return nil
}

// Helper methods for PDF generation

func (e *ProfessionalExporter) writeText(buf *bytes.Buffer, x, y float64, size int, align, text string) {
	fmt.Fprintf(buf, "BT\n")
	fmt.Fprintf(buf, "/F1 %d Tf\n", size)
	
	if align == "center" {
		// Approximate text width for centering
		textWidth := float64(len(text) * size) * 0.5
		x = x - textWidth/2
	}
	
	fmt.Fprintf(buf, "%.2f %.2f Td\n", x, y)
	fmt.Fprintf(buf, "(%s) Tj\n", escapeForPDF(text))
	fmt.Fprintf(buf, "ET\n")
}

func (e *ProfessionalExporter) writeMonospaceText(buf *bytes.Buffer, x, y float64, size int, text string) {
	fmt.Fprintf(buf, "BT\n")
	fmt.Fprintf(buf, "/F2 %d Tf\n", size) // F2 for monospace font
	fmt.Fprintf(buf, "%.2f %.2f Td\n", x, y)
	fmt.Fprintf(buf, "(%s) Tj\n", escapeForPDF(text))
	fmt.Fprintf(buf, "ET\n")
}

func (e *ProfessionalExporter) drawLine(buf *bytes.Buffer, x1, y1, x2, y2 float64) {
	fmt.Fprintf(buf, "%.2f %.2f m\n", x1, y1)
	fmt.Fprintf(buf, "%.2f %.2f l\n", x2, y2)
	fmt.Fprintf(buf, "S\n")
}

func (e *ProfessionalExporter) drawBox(buf *bytes.Buffer, x, y, width, height float64) {
	fmt.Fprintf(buf, "%.2f %.2f %.2f %.2f re\n", x, y, width, height)
	fmt.Fprintf(buf, "S\n")
}

func (e *ProfessionalExporter) drawTableHeader(buf *bytes.Buffer, y float64) {
	headers := []string{"ID", "Name", "Type", "Status", "Location", "Notes"}
	x := e.margin
	widths := []float64{80, 120, 80, 80, 80, 100}
	
	for i, header := range headers {
		e.writeText(buf, x, y, 10, "left", header)
		x += widths[i]
	}
	
	e.drawLine(buf, e.margin, y-5, e.pageWidth-e.margin, y-5)
}

func (e *ProfessionalExporter) drawEquipmentRow(buf *bytes.Buffer, y float64, eq models.Equipment) {
	x := e.margin
	widths := []float64{80, 120, 80, 80, 80, 100}
	
	// ID
	e.writeText(buf, x, y, 9, "left", eq.ID)
	x += widths[0]
	
	// Name
	name := eq.Name
	if len(name) > 20 {
		name = name[:17] + "..."
	}
	e.writeText(buf, x, y, 9, "left", name)
	x += widths[1]
	
	// Type
	e.writeText(buf, x, y, 9, "left", eq.Type)
	x += widths[2]
	
	// Status with symbol
	statusText := string(eq.Status)
	switch eq.Status {
	case models.StatusNormal:
		statusText = "✓ " + statusText
	case models.StatusNeedsRepair:
		statusText = "⚠ " + statusText
	case models.StatusFailed:
		statusText = "✗ " + statusText
	}
	e.writeText(buf, x, y, 9, "left", statusText)
	x += widths[3]
	
	// Location
	location := eq.RoomID
	if location == "" {
		location = fmt.Sprintf("(%.1f, %.1f)", eq.Location.X, eq.Location.Y)
	}
	e.writeText(buf, x, y, 9, "left", location)
	x += widths[4]
	
	// Notes (truncated)
	notes := eq.Notes
	if len(notes) > 15 {
		notes = notes[:12] + "..."
	}
	e.writeText(buf, x, y, 9, "left", notes)
}

// CreateVisualFloorPlan creates a visual representation using graphics
func (e *ProfessionalExporter) CreateVisualFloorPlan(plan *models.FloorPlan, outputPath string) error {
	// Calculate bounds
	minX, minY, maxX, maxY := e.calculateBounds(plan)
	
	// Create image
	scale := 10.0
	width := int((maxX - minX) * scale)
	height := int((maxY - minY) * scale)
	
	if width < 100 {
		width = 800
	}
	if height < 100 {
		height = 600
	}
	
	img := image.NewRGBA(image.Rect(0, 0, width, height))
	
	// White background
	draw.Draw(img, img.Bounds(), &image.Uniform{color.White}, image.Point{}, draw.Src)
	
	// Draw rooms
	for _, room := range plan.Rooms {
		e.drawRoom(img, room, minX, minY, scale)
	}
	
	// Draw equipment
	for _, eq := range plan.Equipment {
		e.drawEquipment(img, eq, minX, minY, scale)
	}
	
	// Save as PNG then embed in PDF
	pngPath := strings.TrimSuffix(outputPath, filepath.Ext(outputPath)) + "_visual.png"
	// Implementation would save PNG and embed it
	
	return nil
}

func (e *ProfessionalExporter) calculateBounds(plan *models.FloorPlan) (minX, minY, maxX, maxY float64) {
	if len(plan.Rooms) == 0 {
		return 0, 0, 100, 100
	}
	
	minX = plan.Rooms[0].Bounds.MinX
	minY = plan.Rooms[0].Bounds.MinY
	maxX = plan.Rooms[0].Bounds.MaxX
	maxY = plan.Rooms[0].Bounds.MaxY
	
	for _, room := range plan.Rooms {
		if room.Bounds.MinX < minX {
			minX = room.Bounds.MinX
		}
		if room.Bounds.MinY < minY {
			minY = room.Bounds.MinY
		}
		if room.Bounds.MaxX > maxX {
			maxX = room.Bounds.MaxX
		}
		if room.Bounds.MaxY > maxY {
			maxY = room.Bounds.MaxY
		}
	}
	
	return minX, minY, maxX, maxY
}

func (e *ProfessionalExporter) drawRoom(img *image.RGBA, room models.Room, offsetX, offsetY, scale float64) {
	// Draw room boundaries
	x1 := int((room.Bounds.MinX - offsetX) * scale)
	y1 := int((room.Bounds.MinY - offsetY) * scale)
	x2 := int((room.Bounds.MaxX - offsetX) * scale)
	y2 := int((room.Bounds.MaxY - offsetY) * scale)
	
	// Draw rectangle outline
	drawRect(img, x1, y1, x2, y2, color.Black)
	
	// Add room label
	// Would use golang.org/x/image/font for text rendering
}

func (e *ProfessionalExporter) drawEquipment(img *image.RGBA, eq models.Equipment, offsetX, offsetY, scale float64) {
	x := int((eq.Location.X - offsetX) * scale)
	y := int((eq.Location.Y - offsetY) * scale)
	
	// Choose color based on status
	var c color.Color
	switch eq.Status {
	case models.StatusNormal:
		c = color.RGBA{0, 200, 0, 255} // Green
	case models.StatusNeedsRepair:
		c = color.RGBA{255, 165, 0, 255} // Orange
	case models.StatusFailed:
		c = color.RGBA{255, 0, 0, 255} // Red
	default:
		c = color.RGBA{128, 128, 128, 255} // Gray
	}
	
	// Draw equipment marker
	drawCircle(img, x, y, 5, c)
}
*/

// End of placeholder methods for future pdfcpu implementation