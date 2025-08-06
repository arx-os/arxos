package handlers

import (
	"encoding/json"
	"fmt"
	"net/http"
	"strconv"
	"strings"
	"time"

	"arx/db"
	"arx/models"

	"github.com/go-chi/chi/v5"
)

// ExportFormat represents supported export formats
type ExportFormat string

const (
	ExportFormatIFC ExportFormat = "ifc"
	ExportFormatDXF ExportFormat = "dxf"
	ExportFormatSVG ExportFormat = "svg"
	ExportFormatJSON ExportFormat = "json"
)

// ExportOptions contains configuration for export operations
type ExportOptions struct {
	Format      ExportFormat `json:"format"`
	Precision   int          `json:"precision"`
	IncludeMetadata bool      `json:"include_metadata"`
	IncludeGeometry bool      `json:"include_geometry"`
	CoordinateSystem string   `json:"coordinate_system"`
}

// ExportResult contains the result of an export operation
type ExportResult struct {
	Success     bool   `json:"success"`
	Format      string `json:"format"`
	Content     string `json:"content"`
	Filename    string `json:"filename"`
	Size        int    `json:"size"`
	ExportTime  string `json:"export_time"`
	Error       string `json:"error,omitempty"`
}

// ExportBIM handles export requests for BIM models
func ExportBIM(w http.ResponseWriter, r *http.Request) {
	// Authentication
	user, err := GetUserFromRequest(r)
	if err != nil {
		http.Error(w, "Unauthorized", http.StatusUnauthorized)
		return
	}

	// Extract project ID
	projectID, err := extractProjectID(r)
	if err != nil {
		http.Error(w, "Invalid project ID", http.StatusBadRequest)
		return
	}

	// Parse export options
	var options ExportOptions
	if err := json.NewDecoder(r.Body).Decode(&options); err != nil {
		// Use default options if not provided
		options = ExportOptions{
			Format: ExportFormatJSON,
			Precision: 2,
			IncludeMetadata: true,
			IncludeGeometry: true,
			CoordinateSystem: "WGS84",
		}
	}

	// Get BIM model
	var bimModel models.BIMModel
	if err := db.DB.Where("project_id = ?", projectID).First(&bimModel).Error; err != nil {
		http.Error(w, "BIM model not found", http.StatusNotFound)
		return
	}

	// Load related data
	db.DB.Model(&bimModel).Association("Rooms").Find(&bimModel.Rooms)
	db.DB.Model(&bimModel).Association("Walls").Find(&bimModel.Walls)
	db.DB.Model(&bimModel).Association("Devices").Find(&bimModel.Devices)
	db.DB.Model(&bimModel).Association("Labels").Find(&bimModel.Labels)
	db.DB.Model(&bimModel).Association("Zones").Find(&bimModel.Zones)

	// Export based on format
	var result ExportResult
	switch options.Format {
	case ExportFormatIFC:
		result = exportAsIFC(bimModel, options)
	case ExportFormatDXF:
		result = exportAsDXF(bimModel, options)
	case ExportFormatSVG:
		result = exportAsSVG(bimModel, options)
	case ExportFormatJSON:
		result = exportAsJSON(bimModel, options)
	default:
		result = ExportResult{
			Success: false,
			Error:   fmt.Sprintf("Unsupported export format: %s", options.Format),
		}
	}

	// Set response headers
	w.Header().Set("Content-Type", "application/json")
	if result.Success {
		w.Header().Set("Content-Disposition", fmt.Sprintf("attachment; filename=%s", result.Filename))
	}

	// Return result
	json.NewEncoder(w).Encode(result)
}

// exportAsIFC exports BIM model as IFC format
func exportAsIFC(bimModel models.BIMModel, options ExportOptions) ExportResult {
	startTime := time.Now()
	
	// Generate IFC content
	ifcContent := generateIFCContent(bimModel, options)
	
	// Create filename
	filename := fmt.Sprintf("bim_model_%d_%s.ifc", bimModel.ID, time.Now().Format("20060102_150405"))
	
	return ExportResult{
		Success:    true,
		Format:     "IFC",
		Content:    ifcContent,
		Filename:   filename,
		Size:       len(ifcContent),
		ExportTime: time.Since(startTime).String(),
	}
}

// exportAsDXF exports BIM model as DXF format
func exportAsDXF(bimModel models.BIMModel, options ExportOptions) ExportResult {
	startTime := time.Now()
	
	// Generate DXF content
	dxfContent := generateDXFContent(bimModel, options)
	
	// Create filename
	filename := fmt.Sprintf("bim_model_%d_%s.dxf", bimModel.ID, time.Now().Format("20060102_150405"))
	
	return ExportResult{
		Success:    true,
		Format:     "DXF",
		Content:    dxfContent,
		Filename:   filename,
		Size:       len(dxfContent),
		ExportTime: time.Since(startTime).String(),
	}
}

// exportAsSVG exports BIM model as SVG format
func exportAsSVG(bimModel models.BIMModel, options ExportOptions) ExportResult {
	startTime := time.Now()
	
	// Generate SVG content
	svgContent := generateSVGContent(bimModel, options)
	
	// Create filename
	filename := fmt.Sprintf("bim_model_%d_%s.svg", bimModel.ID, time.Now().Format("20060102_150405"))
	
	return ExportResult{
		Success:    true,
		Format:     "SVG",
		Content:    svgContent,
		Filename:   filename,
		Size:       len(svgContent),
		ExportTime: time.Since(startTime).String(),
	}
}

// exportAsJSON exports BIM model as JSON format
func exportAsJSON(bimModel models.BIMModel, options ExportOptions) ExportResult {
	startTime := time.Now()
	
	// Generate JSON content
	jsonContent := generateJSONContent(bimModel, options)
	
	// Create filename
	filename := fmt.Sprintf("bim_model_%d_%s.json", bimModel.ID, time.Now().Format("20060102_150405"))
	
	return ExportResult{
		Success:    true,
		Format:     "JSON",
		Content:    jsonContent,
		Filename:   filename,
		Size:       len(jsonContent),
		ExportTime: time.Since(startTime).String(),
	}
}

// generateIFCContent generates IFC format content
func generateIFCContent(bimModel models.BIMModel, options ExportOptions) string {
	var sb strings.Builder
	
	// IFC header
	sb.WriteString("ISO-10303-21;\n")
	sb.WriteString("HEADER;\n")
	sb.WriteString("FILE_DESCRIPTION(('Arxos BIM Export'),'2;1');\n")
	sb.WriteString("FILE_NAME('bim_model.ifc','")
	sb.WriteString(time.Now().Format("2006-01-02T15:04:05"))
	sb.WriteString("',('Arxos User'),('Arxos Platform'),'','','');\n")
	sb.WriteString("FILE_SCHEMA(('IFC4'));\n")
	sb.WriteString("ENDSEC;\n\n")
	
	// IFC data section
	sb.WriteString("DATA;\n")
	
	// Generate IFC entities for each component
	entityID := 1
	
	// Site
	sb.WriteString(fmt.Sprintf("#%d=IFCSITE('SiteID',$,Site,$,$,$,$,$,.ELEMENT.,(0,0,0),$,$);\n", entityID))
	entityID++
	
	// Building
	sb.WriteString(fmt.Sprintf("#%d=IFCBUILDING('BuildingID',$,Building,$,$,$,$,$,.ELEMENT.,$,$,$);\n", entityID))
	entityID++
	
	// Building Storey
	sb.WriteString(fmt.Sprintf("#%d=IFCBUILDINGSTOREY('StoreyID',$,Storey,$,$,$,$,$,.ELEMENT.,$,$,$);\n", entityID))
	entityID++
	
	// Rooms
	for _, room := range bimModel.Rooms {
		sb.WriteString(fmt.Sprintf("#%d=IFCSPACE('RoomID%d',$,Room %s,$,$,$,$,$,.ELEMENT.,$,$,$);\n", 
			entityID, entityID, room.Name))
		entityID++
	}
	
	// Walls
	for _, wall := range bimModel.Walls {
		sb.WriteString(fmt.Sprintf("#%d=IFCWALL('WallID%d',$,Wall %s,$,$,$,$,$,.ELEMENT.,$,$,$);\n", 
			entityID, entityID, wall.Name))
		entityID++
	}
	
	// Devices
	for _, device := range bimModel.Devices {
		sb.WriteString(fmt.Sprintf("#%d=IFCDISTRIBUTIONELEMENT('DeviceID%d',$,Device %s,$,$,$,$,$,.ELEMENT.,$,$,$);\n", 
			entityID, entityID, device.Type))
		entityID++
	}
	
	sb.WriteString("ENDSEC;\n\n")
	
	// IFC footer
	sb.WriteString("END-ISO-10303-21;\n")
	
	return sb.String()
}

// generateDXFContent generates DXF format content
func generateDXFContent(bimModel models.BIMModel, options ExportOptions) string {
	var sb strings.Builder
	
	// DXF header
	sb.WriteString("0\nSECTION\n")
	sb.WriteString("2\nHEADER\n")
	sb.WriteString("9\n$ACADVER\n")
	sb.WriteString("1\nAC1021\n")
	sb.WriteString("9\n$DWGCODEPAGE\n")
	sb.WriteString("3\nANSI_1252\n")
	sb.WriteString("9\n$INSBASE\n")
	sb.WriteString("10\n0.0\n")
	sb.WriteString("20\n0.0\n")
	sb.WriteString("30\n0.0\n")
	sb.WriteString("9\n$EXTMIN\n")
	sb.WriteString("10\n0.0\n")
	sb.WriteString("20\n0.0\n")
	sb.WriteString("30\n0.0\n")
	sb.WriteString("9\n$EXTMAX\n")
	sb.WriteString("10\n1000.0\n")
	sb.WriteString("20\n1000.0\n")
	sb.WriteString("30\n0.0\n")
	sb.WriteString("0\nENDSEC\n")
	
	// DXF entities
	sb.WriteString("0\nSECTION\n")
	sb.WriteString("2\nENTITIES\n")
	
	// Generate DXF entities for each component
	entityID := 1
	
	// Rooms (as polylines)
	for _, room := range bimModel.Rooms {
		if len(room.Geometry.Points) > 2 {
			sb.WriteString("0\nPOLYLINE\n")
			sb.WriteString("8\nROOMS\n")
			sb.WriteString("66\n1\n")
			sb.WriteString("70\n1\n")
			
			for _, point := range room.Geometry.Points {
				sb.WriteString("0\nVERTEX\n")
				sb.WriteString("8\nROOMS\n")
				sb.WriteString(fmt.Sprintf("10\n%.2f\n", point.X))
				sb.WriteString(fmt.Sprintf("20\n%.2f\n", point.Y))
			}
			
			sb.WriteString("0\nSEQEND\n")
			sb.WriteString("8\nROOMS\n")
		}
	}
	
	// Walls (as lines)
	for _, wall := range bimModel.Walls {
		if len(wall.Geometry.Points) >= 2 {
			sb.WriteString("0\nLINE\n")
			sb.WriteString("8\nWALLS\n")
			sb.WriteString(fmt.Sprintf("10\n%.2f\n", wall.Geometry.Points[0].X))
			sb.WriteString(fmt.Sprintf("20\n%.2f\n", wall.Geometry.Points[0].Y))
			sb.WriteString(fmt.Sprintf("11\n%.2f\n", wall.Geometry.Points[1].X))
			sb.WriteString(fmt.Sprintf("21\n%.2f\n", wall.Geometry.Points[1].Y))
		}
	}
	
	// Devices (as points)
	for _, device := range bimModel.Devices {
		if len(device.Geometry.Points) > 0 {
			sb.WriteString("0\nPOINT\n")
			sb.WriteString("8\nDEVICES\n")
			sb.WriteString(fmt.Sprintf("10\n%.2f\n", device.Geometry.Points[0].X))
			sb.WriteString(fmt.Sprintf("20\n%.2f\n", device.Geometry.Points[0].Y))
		}
	}
	
	sb.WriteString("0\nENDSEC\n")
	
	// DXF footer
	sb.WriteString("0\nSECTION\n")
	sb.WriteString("2\nOBJECTS\n")
	sb.WriteString("0\nENDSEC\n")
	sb.WriteString("0\nEOF\n")
	
	return sb.String()
}

// generateSVGContent generates SVG format content
func generateSVGContent(bimModel models.BIMModel, options ExportOptions) string {
	var sb strings.Builder
	
	// Calculate bounding box
	minX, minY, maxX, maxY := calculateBoundingBox(bimModel)
	width := maxX - minX
	height := maxY - minY
	
	// SVG header
	sb.WriteString("<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n")
	sb.WriteString(fmt.Sprintf("<svg width=\"%.2f\" height=\"%.2f\" viewBox=\"%.2f %.2f %.2f %.2f\" xmlns=\"http://www.w3.org/2000/svg\">\n",
		width, height, minX, minY, width, height))
	
	// SVG definitions
	sb.WriteString("  <defs>\n")
	sb.WriteString("    <style>\n")
	sb.WriteString("      .room { fill: #e6f3ff; stroke: #0066cc; stroke-width: 2; }\n")
	sb.WriteString("      .wall { stroke: #333333; stroke-width: 3; fill: none; }\n")
	sb.WriteString("      .device { fill: #ff6666; stroke: #cc0000; stroke-width: 1; }\n")
	sb.WriteString("      .label { font-family: Arial; font-size: 12px; fill: #333333; }\n")
	sb.WriteString("    </style>\n")
	sb.WriteString("  </defs>\n")
	
	// Rooms
	for _, room := range bimModel.Rooms {
		if len(room.Geometry.Points) > 2 {
			sb.WriteString("  <polygon class=\"room\" points=\"")
			for i, point := range room.Geometry.Points {
				if i > 0 {
					sb.WriteString(" ")
				}
				sb.WriteString(fmt.Sprintf("%.2f,%.2f", point.X, point.Y))
			}
			sb.WriteString("\" />\n")
			
			// Room label
			if room.Name != "" {
				centerX, centerY := calculatePolygonCenter(room.Geometry.Points)
				sb.WriteString(fmt.Sprintf("  <text class=\"label\" x=\"%.2f\" y=\"%.2f\" text-anchor=\"middle\">%s</text>\n",
					centerX, centerY, room.Name))
			}
		}
	}
	
	// Walls
	for _, wall := range bimModel.Walls {
		if len(wall.Geometry.Points) >= 2 {
			sb.WriteString("  <line class=\"wall\" ")
			sb.WriteString(fmt.Sprintf("x1=\"%.2f\" y1=\"%.2f\" ", wall.Geometry.Points[0].X, wall.Geometry.Points[0].Y))
			sb.WriteString(fmt.Sprintf("x2=\"%.2f\" y2=\"%.2f\" />\n", wall.Geometry.Points[1].X, wall.Geometry.Points[1].Y))
		}
	}
	
	// Devices
	for _, device := range bimModel.Devices {
		if len(device.Geometry.Points) > 0 {
			sb.WriteString("  <circle class=\"device\" ")
			sb.WriteString(fmt.Sprintf("cx=\"%.2f\" cy=\"%.2f\" r=\"5\" />\n",
				device.Geometry.Points[0].X, device.Geometry.Points[0].Y))
			
			// Device label
			if device.Type != "" {
				sb.WriteString(fmt.Sprintf("  <text class=\"label\" x=\"%.2f\" y=\"%.2f\" text-anchor=\"middle\">%s</text>\n",
					device.Geometry.Points[0].X, device.Geometry.Points[0].Y-10, device.Type))
			}
		}
	}
	
	// Labels
	for _, label := range bimModel.Labels {
		if len(label.Geometry.Points) > 0 {
			sb.WriteString(fmt.Sprintf("  <text class=\"label\" x=\"%.2f\" y=\"%.2f\">%s</text>\n",
				label.Geometry.Points[0].X, label.Geometry.Points[0].Y, label.Text))
		}
	}
	
	sb.WriteString("</svg>")
	
	return sb.String()
}

// generateJSONContent generates JSON format content
func generateJSONContent(bimModel models.BIMModel, options ExportOptions) string {
	// Create export structure
	exportData := map[string]interface{}{
		"metadata": map[string]interface{}{
			"export_format": "JSON",
			"export_time":   time.Now().Format(time.RFC3339),
			"precision":     options.Precision,
			"coordinate_system": options.CoordinateSystem,
		},
		"bim_model": map[string]interface{}{
			"id":          bimModel.ID,
			"name":        bimModel.Name,
			"description": bimModel.Description,
			"created_at":  bimModel.CreatedAt,
			"updated_at":  bimModel.UpdatedAt,
		},
		"components": map[string]interface{}{
			"rooms":   bimModel.Rooms,
			"walls":   bimModel.Walls,
			"devices": bimModel.Devices,
			"labels":  bimModel.Labels,
			"zones":   bimModel.Zones,
		},
	}
	
	// Convert to JSON
	jsonBytes, err := json.MarshalIndent(exportData, "", "  ")
	if err != nil {
		return fmt.Sprintf(`{"error": "Failed to generate JSON: %s"}`, err.Error())
	}
	
	return string(jsonBytes)
}

// calculateBoundingBox calculates the bounding box of all components
func calculateBoundingBox(bimModel models.BIMModel) (minX, minY, maxX, maxY float64) {
	minX, minY = 1e9, 1e9
	maxX, maxY = -1e9, -1e9
	
	// Helper function to update bounding box
	updateBoundingBox := func(points []models.Point) {
		for _, point := range points {
			if point.X < minX {
				minX = point.X
			}
			if point.X > maxX {
				maxX = point.X
			}
			if point.Y < minY {
				minY = point.Y
			}
			if point.Y > maxY {
				maxY = point.Y
			}
		}
	}
	
	// Update bounding box for all components
	for _, room := range bimModel.Rooms {
		updateBoundingBox(room.Geometry.Points)
	}
	for _, wall := range bimModel.Walls {
		updateBoundingBox(wall.Geometry.Points)
	}
	for _, device := range bimModel.Devices {
		updateBoundingBox(device.Geometry.Points)
	}
	for _, label := range bimModel.Labels {
		updateBoundingBox(label.Geometry.Points)
	}
	for _, zone := range bimModel.Zones {
		updateBoundingBox(zone.Geometry.Points)
	}
	
	// Add padding
	padding := 50.0
	minX -= padding
	minY -= padding
	maxX += padding
	maxY += padding
	
	return minX, minY, maxX, maxY
}

// calculatePolygonCenter calculates the center point of a polygon
func calculatePolygonCenter(points []models.Point) (centerX, centerY float64) {
	if len(points) == 0 {
		return 0, 0
	}
	
	var sumX, sumY float64
	for _, point := range points {
		sumX += point.X
		sumY += point.Y
	}
	
	return sumX / float64(len(points)), sumY / float64(len(points))
}

// GetExportFormats returns available export formats
func GetExportFormats(w http.ResponseWriter, r *http.Request) {
	formats := []map[string]interface{}{
		{
			"format":        "IFC",
			"description":   "Industry Foundation Classes format for BIM interoperability",
			"extension":     ".ifc",
			"mime_type":     "application/ifc",
			"supports_metadata": true,
		},
		{
			"format":        "DXF",
			"description":   "AutoCAD Drawing Exchange Format",
			"extension":     ".dxf",
			"mime_type":     "application/dxf",
			"supports_metadata": false,
		},
		{
			"format":        "SVG",
			"description":   "Scalable Vector Graphics format",
			"extension":     ".svg",
			"mime_type":     "image/svg+xml",
			"supports_metadata": true,
		},
		{
			"format":        "JSON",
			"description":   "JavaScript Object Notation format",
			"extension":     ".json",
			"mime_type":     "application/json",
			"supports_metadata": true,
		},
	}
	
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(formats)
} 