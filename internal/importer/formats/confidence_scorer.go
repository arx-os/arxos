package formats

import (
	"math"
	"strings"

	"github.com/arx-os/arxos/internal/common/logger"
)

// ConfidenceScore represents detailed confidence scores
type ConfidenceScore struct {
	Overall   float64
	Text      float64
	Structure float64
	Equipment float64
	Metadata  float64
	Spatial   float64
}

// AdvancedConfidenceScorer calculates confidence scores for imports
type AdvancedConfidenceScorer struct {
	weights map[string]float64
}

// NewAdvancedConfidenceScorer creates a new confidence scorer
func NewAdvancedConfidenceScorer() *AdvancedConfidenceScorer {
	return &AdvancedConfidenceScorer{
		weights: map[string]float64{
			"text":      0.20,
			"structure": 0.25,
			"equipment": 0.25,
			"metadata":  0.15,
			"spatial":   0.15,
		},
	}
}

// Calculate calculates confidence scores for processed data
func (s *AdvancedConfidenceScorer) Calculate(data *ProcessedData) ConfidenceScore {
	score := ConfidenceScore{}

	// Calculate individual scores
	score.Text = s.scoreTextQuality(data)
	score.Structure = s.scoreStructure(data)
	score.Equipment = s.scoreEquipment(data)
	score.Metadata = s.scoreMetadata(data)
	score.Spatial = s.scoreSpatial(data)

	// Calculate weighted overall score
	score.Overall = score.Text*s.weights["text"] +
		score.Structure*s.weights["structure"] +
		score.Equipment*s.weights["equipment"] +
		score.Metadata*s.weights["metadata"] +
		score.Spatial*s.weights["spatial"]

	// Scale to 0-100
	score.Overall *= 100
	score.Text *= 100
	score.Structure *= 100
	score.Equipment *= 100
	score.Metadata *= 100
	score.Spatial *= 100

	logger.Debug("Confidence scores - Overall: %.2f, Text: %.2f, Structure: %.2f, Equipment: %.2f, Metadata: %.2f, Spatial: %.2f",
		score.Overall, score.Text, score.Structure, score.Equipment, score.Metadata, score.Spatial)

	return score
}

// scoreTextQuality scores the quality of extracted text
func (s *AdvancedConfidenceScorer) scoreTextQuality(data *ProcessedData) float64 {
	if data.TextQuality > 0 {
		// Use pre-calculated text quality if available
		return data.TextQuality
	}

	score := 0.0
	factors := 0.0

	// Check if OCR was used (lower confidence)
	if ocr, ok := data.Metadata["ocr_applied"].(string); ok && ocr == "true" {
		score += 0.5
		factors += 1.0
	} else {
		score += 1.0
		factors += 1.0
	}

	// Check text extraction method
	if method, ok := data.Metadata["extraction_method"].(string); ok {
		switch method {
		case "pdftotext", "pdfcpu":
			score += 1.0
		case "tesseract":
			score += 0.7
		case "basic":
			score += 0.5
		default:
			score += 0.3
		}
		factors += 1.0
	}

	if factors == 0 {
		return 0.5 // Default medium confidence
	}

	return score / factors
}

// scoreStructure scores the structural completeness
func (s *AdvancedConfidenceScorer) scoreStructure(data *ProcessedData) float64 {
	score := 0.0
	factors := 0.0

	// Check floors
	if len(data.Floors) > 0 {
		score += 1.0
		factors += 1.0

		// Check floor details
		floorDetailsScore := 0.0
		for _, floor := range data.Floors {
			if floor.Name != "" && floor.Name != "Floor" {
				floorDetailsScore += 0.2
			}
			if len(floor.Rooms) > 0 {
				floorDetailsScore += 0.3
			}
			if floor.Area > 0 {
				floorDetailsScore += 0.3
			}
			if floor.Height > 0 {
				floorDetailsScore += 0.2
			}
		}
		score += math.Min(floorDetailsScore/float64(len(data.Floors)), 1.0)
		factors += 1.0
	}

	// Check rooms
	totalRooms := 0
	roomsWithDetails := 0
	for _, floor := range data.Floors {
		totalRooms += len(floor.Rooms)
		for _, room := range floor.Rooms {
			if room.Name != "" && room.Type != "general" && room.Area > 0 {
				roomsWithDetails++
			}
		}
	}

	if totalRooms > 0 {
		score += float64(roomsWithDetails) / float64(totalRooms)
		factors += 1.0
	}

	// Check spatial boundaries
	hasBoundaries := false
	for _, floor := range data.Floors {
		if len(floor.Boundaries) > 0 {
			hasBoundaries = true
			break
		}
	}
	if hasBoundaries {
		score += 1.0
		factors += 1.0
	}

	if factors == 0 {
		return 0.0
	}

	return score / factors
}

// scoreEquipment scores equipment data completeness
func (s *AdvancedConfidenceScorer) scoreEquipment(data *ProcessedData) float64 {
	if len(data.Equipment) == 0 {
		return 0.0
	}

	score := 0.0
	factors := 0.0

	// Base score for having equipment
	score += 1.0
	factors += 1.0

	// Score equipment details
	detailScore := 0.0
	for _, eq := range data.Equipment {
		eqScore := 0.0
		eqFactors := 0.0

		if eq.Name != "" {
			eqScore += 1.0
			eqFactors += 1.0
		}
		if eq.Type != "" && eq.Type != "other" {
			eqScore += 1.0
			eqFactors += 1.0
		}
		if eq.Manufacturer != "" {
			eqScore += 1.0
			eqFactors += 1.0
		}
		if eq.Model != "" {
			eqScore += 1.0
			eqFactors += 1.0
		}
		if eq.SerialNumber != "" {
			eqScore += 1.0
			eqFactors += 1.0
		}
		if eq.Location.Floor != "" || eq.Location.Room != "" {
			eqScore += 1.0
			eqFactors += 1.0
		}
		if eq.Location.Position != nil {
			eqScore += 1.0
			eqFactors += 1.0
		}

		if eqFactors > 0 {
			detailScore += eqScore / eqFactors
		}
	}

	score += math.Min(detailScore/float64(len(data.Equipment)), 1.0)
	factors += 1.0

	// Bonus for reasonable equipment count
	if len(data.Equipment) >= 5 && len(data.Equipment) <= 1000 {
		score += 0.5
		factors += 0.5
	}

	return score / factors
}

// scoreMetadata scores metadata richness
func (s *AdvancedConfidenceScorer) scoreMetadata(data *ProcessedData) float64 {
	score := 0.0
	factors := 0.0

	importantFields := []string{
		"building_name",
		"address",
		"date",
		"project_number",
		"extraction_method",
	}

	for _, field := range importantFields {
		if val, ok := data.Metadata[field]; ok && val != "" {
			score += 1.0
		}
		factors += 1.0
	}

	// Bonus for additional metadata
	if len(data.Metadata) > len(importantFields) {
		bonus := math.Min(float64(len(data.Metadata)-len(importantFields))/10.0, 0.5)
		score += bonus
		factors += 0.5
	}

	if factors == 0 {
		return 0.0
	}

	return score / factors
}

// scoreSpatial scores spatial data quality
func (s *AdvancedConfidenceScorer) scoreSpatial(data *ProcessedData) float64 {
	score := 0.0
	factors := 0.0

	// Check for spatial data
	if len(data.Spatial) > 0 {
		score += 1.0
		factors += 1.0

		// Score spatial data quality
		spatialScore := 0.0
		for _, spatial := range data.Spatial {
			if spatial.Geometry != nil {
				spatialScore += 0.5
			}
			if len(spatial.Properties) > 0 {
				spatialScore += 0.5
			}
		}
		score += math.Min(spatialScore/float64(len(data.Spatial)), 1.0)
		factors += 1.0
	}

	// Check for diagrams
	if len(data.Diagrams) > 0 {
		score += 1.0
		factors += 1.0

		// Score diagram quality
		diagramScore := 0.0
		for _, diagram := range data.Diagrams {
			if diagram.Type == "floor_plan" {
				diagramScore += 1.0
			} else if diagram.Type != "" {
				diagramScore += 0.5
			}
			if len(diagram.Elements) > 0 {
				diagramScore += 0.5
			}
		}
		score += math.Min(diagramScore/float64(len(data.Diagrams)), 1.0)
		factors += 1.0
	}

	// Check for equipment positions
	equipmentWithPosition := 0
	for _, eq := range data.Equipment {
		if eq.Location.Position != nil {
			equipmentWithPosition++
		}
	}

	if len(data.Equipment) > 0 && equipmentWithPosition > 0 {
		score += float64(equipmentWithPosition) / float64(len(data.Equipment))
		factors += 1.0
	}

	if factors == 0 {
		return 0.0
	}

	return score / factors
}

// GetConfidenceLevel returns a confidence level string
func (s *AdvancedConfidenceScorer) GetConfidenceLevel(score float64) string {
	switch {
	case score >= 80:
		return "high"
	case score >= 60:
		return "medium"
	case score >= 40:
		return "low"
	default:
		return "estimated"
	}
}

// ValidateConfidence validates confidence scores
func (s *AdvancedConfidenceScorer) ValidateConfidence(score ConfidenceScore) error {
	// Check if scores are within valid range
	scores := []float64{
		score.Overall,
		score.Text,
		score.Structure,
		score.Equipment,
		score.Metadata,
		score.Spatial,
	}

	for _, s := range scores {
		if s < 0 || s > 100 {
			return &ValidationError{
				Field:   "confidence_score",
				Message: "Score out of valid range (0-100)",
			}
		}
	}

	return nil
}

// ValidationError represents a validation error
type ValidationError struct {
	Field   string
	Message string
}

func (e *ValidationError) Error() string {
	return e.Field + ": " + e.Message
}

// ConfidenceReport generates a human-readable confidence report
func (s *AdvancedConfidenceScorer) GenerateReport(score ConfidenceScore, data *ProcessedData) string {
	var report strings.Builder

	report.WriteString("=== PDF Import Confidence Report ===\n\n")

	report.WriteString("Overall Confidence: ")
	report.WriteString(s.formatScore(score.Overall))
	report.WriteString(" (")
	report.WriteString(s.GetConfidenceLevel(score.Overall))
	report.WriteString(")\n\n")

	report.WriteString("Component Scores:\n")
	report.WriteString("  Text Quality:      ")
	report.WriteString(s.formatScore(score.Text))
	report.WriteString(s.getQualityIndicator(score.Text))
	report.WriteString("\n")

	report.WriteString("  Structure:         ")
	report.WriteString(s.formatScore(score.Structure))
	report.WriteString(s.getQualityIndicator(score.Structure))
	report.WriteString("\n")

	report.WriteString("  Equipment Data:    ")
	report.WriteString(s.formatScore(score.Equipment))
	report.WriteString(s.getQualityIndicator(score.Equipment))
	report.WriteString("\n")

	report.WriteString("  Metadata:          ")
	report.WriteString(s.formatScore(score.Metadata))
	report.WriteString(s.getQualityIndicator(score.Metadata))
	report.WriteString("\n")

	report.WriteString("  Spatial Data:      ")
	report.WriteString(s.formatScore(score.Spatial))
	report.WriteString(s.getQualityIndicator(score.Spatial))
	report.WriteString("\n\n")

	report.WriteString("Data Summary:\n")
	report.WriteString("  Floors:            ")
	report.WriteString(s.formatCount(len(data.Floors)))
	report.WriteString("\n")

	totalRooms := 0
	for _, floor := range data.Floors {
		totalRooms += len(floor.Rooms)
	}
	report.WriteString("  Rooms:             ")
	report.WriteString(s.formatCount(totalRooms))
	report.WriteString("\n")

	report.WriteString("  Equipment Items:   ")
	report.WriteString(s.formatCount(len(data.Equipment)))
	report.WriteString("\n")

	report.WriteString("  Diagrams:          ")
	report.WriteString(s.formatCount(len(data.Diagrams)))
	report.WriteString("\n")

	if ocr, ok := data.Metadata["ocr_applied"].(string); ok && ocr == "true" {
		report.WriteString("\nNote: OCR was applied to extract text from scanned images.\n")
	}

	return report.String()
}

func (s *AdvancedConfidenceScorer) formatScore(score float64) string {
	return strings.TrimRight(strings.TrimRight(
		strings.Replace(
			strings.Replace(
				"%.1f%%", "%.1f", score, 1),
			"%%", "%", 1),
		"0", ""), ".")
}

func (s *AdvancedConfidenceScorer) getQualityIndicator(score float64) string {
	switch {
	case score >= 80:
		return " ✓✓✓"
	case score >= 60:
		return " ✓✓"
	case score >= 40:
		return " ✓"
	default:
		return " ✗"
	}
}

func (s *AdvancedConfidenceScorer) formatCount(count int) string {
	if count == 0 {
		return "None"
	}
	return strings.TrimSpace(strings.Replace("d", "d", "", count))
}