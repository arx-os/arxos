package merge

import (
	"encoding/json"
	"fmt"
	"html/template"
	"io"
	"math"
	"sort"
	"strings"
	"time"

	"github.com/arx-os/arxos/internal/spatial"
)

// MergeVisualizer provides visualization for merge operations
type MergeVisualizer struct {
	merger         *SmartMerger
	resolver       *ConflictResolver
	changeDetector *ChangeDetector
	fusion         *DataFusion
}

// NewMergeVisualizer creates a new merge visualizer
func NewMergeVisualizer(
	merger *SmartMerger,
	resolver *ConflictResolver,
	changeDetector *ChangeDetector,
	fusion *DataFusion,
) *MergeVisualizer {
	return &MergeVisualizer{
		merger:         merger,
		resolver:       resolver,
		changeDetector: changeDetector,
		fusion:         fusion,
	}
}

// VisualizationOptions configures visualization output
type VisualizationOptions struct {
	Format          string // "html", "json", "text", "svg"
	ShowConflicts   bool
	ShowChanges     bool
	ShowConfidence  bool
	ShowTimeline    bool
	ShowStatistics  bool
	TimeRange       time.Duration
	EquipmentFilter []string
}

// GenerateVisualization creates a visualization of merge results
func (mv *MergeVisualizer) GenerateVisualization(
	result *FusionResult,
	options VisualizationOptions,
) (string, error) {
	switch options.Format {
	case "html":
		return mv.generateHTMLVisualization(result, options)
	case "json":
		return mv.generateJSONVisualization(result, options)
	case "text":
		return mv.generateTextVisualization(result, options)
	case "svg":
		return mv.generateSVGVisualization(result, options)
	default:
		return "", fmt.Errorf("unsupported format: %s", options.Format)
	}
}

// generateHTMLVisualization creates an HTML visualization
func (mv *MergeVisualizer) generateHTMLVisualization(
	result *FusionResult,
	options VisualizationOptions,
) (string, error) {
	tmpl := `<!DOCTYPE html>
<html>
<head>
    <title>Merge Visualization - {{.BuildingID}}</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .header { background: #f0f0f0; padding: 10px; border-radius: 5px; }
        .section { margin: 20px 0; }
        .conflict { background: #ffeeee; padding: 10px; margin: 5px 0; border-left: 3px solid #ff0000; }
        .change { background: #ffffee; padding: 10px; margin: 5px 0; border-left: 3px solid #ffaa00; }
        .resolved { background: #eeffee; padding: 10px; margin: 5px 0; border-left: 3px solid #00aa00; }
        .equipment { background: #f5f5f5; padding: 10px; margin: 10px 0; border-radius: 5px; }
        .confidence-high { color: #00aa00; }
        .confidence-medium { color: #ffaa00; }
        .confidence-low { color: #ff5500; }
        .confidence-estimated { color: #888888; }
        .stats { display: flex; gap: 20px; }
        .stat-box { background: #f9f9f9; padding: 10px; border-radius: 5px; flex: 1; }
        table { width: 100%; border-collapse: collapse; }
        th, td { padding: 8px; text-align: left; border-bottom: 1px solid #ddd; }
        .timeline { position: relative; padding: 20px 0; }
        .timeline-item { margin: 10px 0; padding-left: 30px; position: relative; }
        .timeline-item:before { content: "•"; position: absolute; left: 10px; }
    </style>
</head>
<body>
    <div class="header">
        <h1>Merge Visualization</h1>
        <p>Building: {{.BuildingID}} | Time: {{.Timestamp}}</p>
        <p>Coverage: {{.Coverage}}% | Confidence: {{.ConfidenceScore}}</p>
    </div>

    {{if .ShowStatistics}}
    <div class="section">
        <h2>Statistics</h2>
        <div class="stats">
            <div class="stat-box">
                <h3>Sources</h3>
                <p>Total: {{.Statistics.TotalSources}}</p>
                {{range $type, $count := .Statistics.SourceBreakdown}}
                <p>{{$type}}: {{$count}}</p>
                {{end}}
            </div>
            <div class="stat-box">
                <h3>Processing</h3>
                <p>Equipment: {{.Statistics.EquipmentProcessed}}</p>
                <p>Conflicts: {{.Statistics.ConflictsDetected}}</p>
                <p>Resolved: {{.Statistics.ConflictsResolved}}</p>
            </div>
            <div class="stat-box">
                <h3>Changes</h3>
                <p>Detected: {{.Statistics.ChangesDetected}}</p>
                <p>Processing Time: {{.Statistics.ProcessingTime}}</p>
            </div>
        </div>
    </div>
    {{end}}

    {{if .ShowConflicts}}
    <div class="section">
        <h2>Conflicts & Resolutions</h2>
        {{range .ConflictDetails}}
        <div class="{{if .Resolved}}resolved{{else}}conflict{{end}}">
            <h3>{{.Type}} Conflict: {{.Equipment}}</h3>
            <p>Sources: {{.Source1}} vs {{.Source2}}</p>
            <p>Difference: {{.Difference}}</p>
            {{if .Resolved}}
            <p>✓ Resolution: {{.Resolution}}</p>
            {{end}}
        </div>
        {{end}}
    </div>
    {{end}}

    {{if .ShowChanges}}
    <div class="section">
        <h2>Detected Changes</h2>
        {{range .ChangeDetails}}
        <div class="change">
            <h3>{{.Type}} Change: {{.Equipment}}</h3>
            <p>Field: {{.Field}}</p>
            <p>Old: {{.OldValue}} → New: {{.NewValue}}</p>
            <p>Magnitude: {{.Magnitude}}</p>
        </div>
        {{end}}
    </div>
    {{end}}

    {{if .ShowEquipment}}
    <div class="section">
        <h2>Merged Equipment</h2>
        {{range .EquipmentDetails}}
        <div class="equipment">
            <h3>{{.ID}}: {{.Type}}</h3>
            <p>Position: {{.Position}}</p>
            <p class="confidence-{{.ConfidenceClass}}">Confidence: {{.Confidence}}</p>
            <p>Sources: {{.SourceCount}}</p>
        </div>
        {{end}}
    </div>
    {{end}}
</body>
</html>`

	// Prepare template data
	data := mv.prepareHTMLData(result, options)

	// Parse and execute template
	t, err := template.New("visualization").Parse(tmpl)
	if err != nil {
		return "", err
	}

	var buf strings.Builder
	if err := t.Execute(&buf, data); err != nil {
		return "", err
	}

	return buf.String(), nil
}

// prepareHTMLData prepares data for HTML template
func (mv *MergeVisualizer) prepareHTMLData(
	result *FusionResult,
	options VisualizationOptions,
) map[string]interface{} {
	data := map[string]interface{}{
		"BuildingID":      result.BuildingID,
		"Timestamp":       result.Timestamp.Format("2006-01-02 15:04:05"),
		"Coverage":        fmt.Sprintf("%.1f", result.Coverage),
		"ConfidenceScore": fmt.Sprintf("%.2f", result.ConfidenceScore),
		"Statistics":      result.Statistics,
		"ShowStatistics":  options.ShowStatistics,
		"ShowConflicts":   options.ShowConflicts,
		"ShowChanges":     options.ShowChanges,
	}

	// Prepare conflict details
	if options.ShowConflicts {
		conflictDetails := make([]map[string]interface{}, 0)
		for i, conflict := range result.Conflicts {
			detail := map[string]interface{}{
				"Type":       conflict.Type,
				"Equipment":  conflict.EquipmentID,
				"Source1":    conflict.Source1.Type,
				"Source2":    conflict.Source2.Type,
				"Difference": fmt.Sprintf("%.3f", conflict.Difference),
				"Resolved":   i < len(result.Resolutions),
			}
			if i < len(result.Resolutions) {
				detail["Resolution"] = result.Resolutions[i].Method
			}
			conflictDetails = append(conflictDetails, detail)
		}
		data["ConflictDetails"] = conflictDetails
	}

	// Prepare change details
	if options.ShowChanges {
		changeDetails := make([]map[string]interface{}, 0)
		for _, change := range result.Changes {
			changeDetails = append(changeDetails, map[string]interface{}{
				"Type":      change.Type,
				"Equipment": change.EquipmentID,
				"Field":     change.Field,
				"OldValue":  fmt.Sprintf("%v", change.OldValue),
				"NewValue":  fmt.Sprintf("%v", change.NewValue),
				"Magnitude": fmt.Sprintf("%.3f", change.Magnitude),
			})
		}
		data["ChangeDetails"] = changeDetails
	}

	// Prepare equipment details
	equipmentDetails := make([]map[string]interface{}, 0)
	for _, eq := range result.MergedEquipment {
		if len(options.EquipmentFilter) > 0 && !contains(options.EquipmentFilter, eq.EquipmentID) {
			continue
		}
		equipmentDetails = append(equipmentDetails, map[string]interface{}{
			"ID":              eq.EquipmentID,
			"Type":            eq.Type,
			"Position":        eq.Position.String(),
			"Confidence":      eq.Confidence.String(),
			"ConfidenceClass": strings.ToLower(eq.Confidence.String()),
			"SourceCount":     len(eq.Sources),
		})
	}
	data["EquipmentDetails"] = equipmentDetails
	data["ShowEquipment"] = len(equipmentDetails) > 0

	return data
}

// generateJSONVisualization creates a JSON visualization
func (mv *MergeVisualizer) generateJSONVisualization(
	result *FusionResult,
	options VisualizationOptions,
) (string, error) {
	data := make(map[string]interface{})

	data["metadata"] = map[string]interface{}{
		"building_id": result.BuildingID,
		"timestamp":   result.Timestamp,
		"coverage":    result.Coverage,
		"confidence":  result.ConfidenceScore,
	}

	if options.ShowStatistics {
		data["statistics"] = result.Statistics
	}

	if options.ShowConflicts {
		data["conflicts"] = result.Conflicts
		data["resolutions"] = result.Resolutions
	}

	if options.ShowChanges {
		data["changes"] = result.Changes
	}

	if options.ShowConfidence {
		data["confidence_distribution"] = mv.generateConfidenceDistribution(result)
	}

	if options.ShowTimeline {
		data["timeline"] = mv.generateTimeline(result, options.TimeRange)
	}

	// Filter equipment if needed
	equipment := result.MergedEquipment
	if len(options.EquipmentFilter) > 0 {
		filtered := make([]*MergedEquipment, 0)
		for _, eq := range equipment {
			if contains(options.EquipmentFilter, eq.EquipmentID) {
				filtered = append(filtered, eq)
			}
		}
		equipment = filtered
	}
	data["equipment"] = equipment

	// Convert to JSON
	jsonData, err := json.MarshalIndent(data, "", "  ")
	if err != nil {
		return "", err
	}

	return string(jsonData), nil
}

// generateTextVisualization creates a text visualization
func (mv *MergeVisualizer) generateTextVisualization(
	result *FusionResult,
	options VisualizationOptions,
) (string, error) {
	var buf strings.Builder

	// Header
	buf.WriteString(strings.Repeat("=", 80) + "\n")
	buf.WriteString(fmt.Sprintf("MERGE VISUALIZATION - Building: %s\n", result.BuildingID))
	buf.WriteString(fmt.Sprintf("Timestamp: %s\n", result.Timestamp.Format("2006-01-02 15:04:05")))
	buf.WriteString(fmt.Sprintf("Coverage: %.1f%% | Confidence: %.2f\n", result.Coverage, result.ConfidenceScore))
	buf.WriteString(strings.Repeat("=", 80) + "\n\n")

	// Statistics
	if options.ShowStatistics {
		buf.WriteString("STATISTICS\n")
		buf.WriteString(strings.Repeat("-", 40) + "\n")
		buf.WriteString(fmt.Sprintf("Total Sources: %d\n", result.Statistics.TotalSources))
		for sourceType, count := range result.Statistics.SourceBreakdown {
			buf.WriteString(fmt.Sprintf("  %s: %d\n", sourceType, count))
		}
		buf.WriteString(fmt.Sprintf("Equipment Processed: %d\n", result.Statistics.EquipmentProcessed))
		buf.WriteString(fmt.Sprintf("Conflicts: %d detected, %d resolved\n",
			result.Statistics.ConflictsDetected,
			result.Statistics.ConflictsResolved))
		buf.WriteString(fmt.Sprintf("Changes Detected: %d\n", result.Statistics.ChangesDetected))
		buf.WriteString(fmt.Sprintf("Processing Time: %v\n", result.Statistics.ProcessingTime))
		buf.WriteString("\n")
	}

	// Conflicts
	if options.ShowConflicts && len(result.Conflicts) > 0 {
		buf.WriteString("CONFLICTS & RESOLUTIONS\n")
		buf.WriteString(strings.Repeat("-", 40) + "\n")
		for i, conflict := range result.Conflicts {
			buf.WriteString(fmt.Sprintf("[%s] %s\n", conflict.Type, conflict.EquipmentID))
			buf.WriteString(fmt.Sprintf("  Sources: %s vs %s\n",
				conflict.Source1.Type, conflict.Source2.Type))
			buf.WriteString(fmt.Sprintf("  Difference: %.3f\n", conflict.Difference))
			if i < len(result.Resolutions) {
				res := result.Resolutions[i]
				buf.WriteString(fmt.Sprintf("  ✓ Resolved: %s\n", res.Method))
				if res.RuleApplied != nil {
					buf.WriteString(fmt.Sprintf("  Rule: %s\n", res.RuleApplied.Name))
				}
			} else {
				buf.WriteString("  ✗ Unresolved\n")
			}
			buf.WriteString("\n")
		}
	}

	// Changes
	if options.ShowChanges && len(result.Changes) > 0 {
		buf.WriteString("DETECTED CHANGES\n")
		buf.WriteString(strings.Repeat("-", 40) + "\n")
		for _, change := range result.Changes {
			buf.WriteString(fmt.Sprintf("[%s] %s - %s\n",
				change.Type, change.EquipmentID, change.Field))
			buf.WriteString(fmt.Sprintf("  %v → %v (magnitude: %.3f)\n",
				change.OldValue, change.NewValue, change.Magnitude))
			if change.Verified {
				buf.WriteString("  ✓ Verified\n")
			}
			buf.WriteString("\n")
		}
	}

	// Equipment Summary
	buf.WriteString("EQUIPMENT SUMMARY\n")
	buf.WriteString(strings.Repeat("-", 40) + "\n")

	// Group by confidence
	confGroups := make(map[spatial.ConfidenceLevel][]*MergedEquipment)
	for _, eq := range result.MergedEquipment {
		if len(options.EquipmentFilter) > 0 && !contains(options.EquipmentFilter, eq.EquipmentID) {
			continue
		}
		confGroups[eq.Confidence] = append(confGroups[eq.Confidence], eq)
	}

	// Display by confidence level
	for _, level := range []spatial.ConfidenceLevel{
		spatial.ConfidenceHigh,
		spatial.ConfidenceMedium,
		spatial.ConfidenceLow,
		spatial.ConfidenceEstimated,
	} {
		if equipment, ok := confGroups[level]; ok && len(equipment) > 0 {
			buf.WriteString(fmt.Sprintf("\n%s Confidence (%d items):\n", level, len(equipment)))
			for _, eq := range equipment {
				buf.WriteString(fmt.Sprintf("  • %s (%s) - %d sources\n",
					eq.EquipmentID, eq.Type, len(eq.Sources)))
			}
		}
	}

	return buf.String(), nil
}

// generateSVGVisualization creates an SVG visualization
func (mv *MergeVisualizer) generateSVGVisualization(
	result *FusionResult,
	options VisualizationOptions,
) (string, error) {
	var buf strings.Builder

	// SVG header
	buf.WriteString(`<svg width="800" height="600" xmlns="http://www.w3.org/2000/svg">`)
	buf.WriteString(`<style>`)
	buf.WriteString(`.title { font-family: Arial; font-size: 20px; font-weight: bold; }`)
	buf.WriteString(`.label { font-family: Arial; font-size: 12px; }`)
	buf.WriteString(`.high { fill: #00aa00; }`)
	buf.WriteString(`.medium { fill: #ffaa00; }`)
	buf.WriteString(`.low { fill: #ff5500; }`)
	buf.WriteString(`.estimated { fill: #888888; }`)
	buf.WriteString(`</style>`)

	// Title
	buf.WriteString(fmt.Sprintf(`<text x="10" y="30" class="title">Merge Visualization - %s</text>`,
		result.BuildingID))

	// Confidence distribution pie chart
	if options.ShowConfidence {
		buf.WriteString(mv.generateConfidencePieChart(result, 100, 100))
	}

	// Timeline
	if options.ShowTimeline {
		buf.WriteString(mv.generateSVGTimeline(result, 400, 100, options.TimeRange))
	}

	// Statistics bars
	if options.ShowStatistics {
		buf.WriteString(mv.generateStatisticsBars(result, 100, 350))
	}

	buf.WriteString(`</svg>`)

	return buf.String(), nil
}

// generateConfidencePieChart creates a pie chart for confidence distribution
func (mv *MergeVisualizer) generateConfidencePieChart(result *FusionResult, cx, cy float64) string {
	var buf strings.Builder

	// Calculate angles for each confidence level
	total := len(result.MergedEquipment)
	if total == 0 {
		return ""
	}

	// Count by confidence
	counts := make(map[spatial.ConfidenceLevel]int)
	for _, eq := range result.MergedEquipment {
		counts[eq.Confidence]++
	}

	radius := 80.0
	startAngle := 0.0

	// Draw pie slices
	for _, level := range []spatial.ConfidenceLevel{
		spatial.ConfidenceHigh,
		spatial.ConfidenceMedium,
		spatial.ConfidenceLow,
		spatial.ConfidenceEstimated,
	} {
		count := counts[level]
		if count == 0 {
			continue
		}

		angle := float64(count) / float64(total) * 360
		endAngle := startAngle + angle

		// Calculate path
		largeArc := 0
		if angle > 180 {
			largeArc = 1
		}

		x1 := cx + radius*math.Cos(startAngle*math.Pi/180)
		y1 := cy + radius*math.Sin(startAngle*math.Pi/180)
		x2 := cx + radius*math.Cos(endAngle*math.Pi/180)
		y2 := cy + radius*math.Sin(endAngle*math.Pi/180)

		class := strings.ToLower(level.String())
		path := fmt.Sprintf(`<path d="M %.1f %.1f L %.1f %.1f A %.1f %.1f 0 %d 1 %.1f %.1f Z" class="%s" opacity="0.8"/>`,
			cx, cy, x1, y1, radius, radius, largeArc, x2, y2, class)
		buf.WriteString(path)

		startAngle = endAngle
	}

	// Add title
	buf.WriteString(fmt.Sprintf(`<text x="%.0f" y="%.0f" text-anchor="middle" class="label">Confidence Distribution</text>`,
		cx, cy+radius+20))

	return buf.String()
}

// generateSVGTimeline creates a timeline visualization
func (mv *MergeVisualizer) generateSVGTimeline(
	result *FusionResult,
	x, y float64,
	timeRange time.Duration,
) string {
	var buf strings.Builder

	// Get recent changes
	changes := mv.changeDetector.GetRecentChanges(timeRange)
	if len(changes) == 0 {
		return ""
	}

	// Sort by timestamp
	sort.Slice(changes, func(i, j int) bool {
		return changes[i].Timestamp.Before(changes[j].Timestamp)
	})

	// Draw timeline
	width := 300.0
	buf.WriteString(fmt.Sprintf(`<line x1="%.0f" y1="%.0f" x2="%.0f" y2="%.0f" stroke="black" stroke-width="2"/>`,
		x, y, x+width, y))

	// Add change markers
	earliest := changes[0].Timestamp
	latest := changes[len(changes)-1].Timestamp
	duration := latest.Sub(earliest).Seconds()
	if duration == 0 {
		duration = 1
	}

	for i, change := range changes {
		// Calculate position
		offset := change.Timestamp.Sub(earliest).Seconds() / duration * width
		markerX := x + offset

		// Draw marker
		color := "#ffaa00"
		if change.Type == ChangeTypeAdded {
			color = "#00aa00"
		} else if change.Type == ChangeTypeRemoved {
			color = "#ff0000"
		}

		buf.WriteString(fmt.Sprintf(`<circle cx="%.0f" cy="%.0f" r="4" fill="%s"/>`,
			markerX, y, color))

		// Add label (every 3rd item to avoid overlap)
		if i%3 == 0 {
			buf.WriteString(fmt.Sprintf(`<text x="%.0f" y="%.0f" class="label" transform="rotate(-45 %.0f %.0f)">%s</text>`,
				markerX, y+15, markerX, y+15, change.Type))
		}
	}

	// Add title
	buf.WriteString(fmt.Sprintf(`<text x="%.0f" y="%.0f" class="label">Change Timeline (%.0f hours)</text>`,
		x, y-10, timeRange.Hours()))

	return buf.String()
}

// generateStatisticsBars creates bar chart for statistics
func (mv *MergeVisualizer) generateStatisticsBars(result *FusionResult, x, y float64) string {
	var buf strings.Builder

	// Data for bars
	bars := []struct {
		label string
		value int
		max   int
		color string
	}{
		{"Sources", result.Statistics.TotalSources, 20, "#4169E1"},
		{"Equipment", result.Statistics.EquipmentProcessed, 100, "#32CD32"},
		{"Conflicts", result.Statistics.ConflictsDetected, 50, "#FF6347"},
		{"Resolved", result.Statistics.ConflictsResolved, 50, "#90EE90"},
		{"Changes", result.Statistics.ChangesDetected, 50, "#FFD700"},
	}

	barWidth := 40.0
	barSpacing := 60.0
	maxHeight := 150.0

	// Draw bars
	for i, bar := range bars {
		barX := x + float64(i)*barSpacing
		if bar.max == 0 {
			bar.max = 1
		}
		height := math.Min(float64(bar.value)/float64(bar.max)*maxHeight, maxHeight)
		barY := y - height

		// Draw bar
		buf.WriteString(fmt.Sprintf(`<rect x="%.0f" y="%.0f" width="%.0f" height="%.0f" fill="%s" opacity="0.7"/>`,
			barX, barY, barWidth, height, bar.color))

		// Add value label
		buf.WriteString(fmt.Sprintf(`<text x="%.0f" y="%.0f" text-anchor="middle" class="label">%d</text>`,
			barX+barWidth/2, barY-5, bar.value))

		// Add label
		buf.WriteString(fmt.Sprintf(`<text x="%.0f" y="%.0f" text-anchor="middle" class="label" font-size="10">%s</text>`,
			barX+barWidth/2, y+15, bar.label))
	}

	// Add title
	buf.WriteString(fmt.Sprintf(`<text x="%.0f" y="%.0f" class="label">Processing Statistics</text>`,
		x, y-maxHeight-20))

	return buf.String()
}

// generateConfidenceDistribution analyzes confidence distribution
func (mv *MergeVisualizer) generateConfidenceDistribution(result *FusionResult) map[string]interface{} {
	dist := make(map[string]int)
	for _, eq := range result.MergedEquipment {
		dist[eq.Confidence.String()]++
	}

	total := len(result.MergedEquipment)
	percentages := make(map[string]float64)
	for level, count := range dist {
		if total > 0 {
			percentages[level] = float64(count) / float64(total) * 100
		}
	}

	return map[string]interface{}{
		"counts":      dist,
		"percentages": percentages,
		"total":       total,
	}
}

// generateTimeline creates a timeline of changes
func (mv *MergeVisualizer) generateTimeline(result *FusionResult, timeRange time.Duration) []map[string]interface{} {
	changes := mv.changeDetector.GetRecentChanges(timeRange)

	// Sort by timestamp
	sort.Slice(changes, func(i, j int) bool {
		return changes[i].Timestamp.Before(changes[j].Timestamp)
	})

	timeline := make([]map[string]interface{}, 0, len(changes))
	for _, change := range changes {
		timeline = append(timeline, map[string]interface{}{
			"timestamp":    change.Timestamp,
			"type":         change.Type,
			"equipment_id": change.EquipmentID,
			"field":        change.Field,
			"magnitude":    change.Magnitude,
			"verified":     change.Verified,
		})
	}

	return timeline
}

// ExportVisualization exports visualization to a writer
func (mv *MergeVisualizer) ExportVisualization(
	result *FusionResult,
	options VisualizationOptions,
	writer io.Writer,
) error {
	output, err := mv.GenerateVisualization(result, options)
	if err != nil {
		return err
	}

	_, err = writer.Write([]byte(output))
	return err
}

// GetConflictSummary generates a summary of conflicts
func (mv *MergeVisualizer) GetConflictSummary(result *FusionResult) ConflictSummary {
	summary := ConflictSummary{
		TotalConflicts:    len(result.Conflicts),
		ResolvedCount:     len(result.Resolutions),
		ConflictsByType:   make(map[string]int),
		ResolutionMethods: make(map[ResolutionMethod]int),
	}

	// Count conflicts by type
	for _, conflict := range result.Conflicts {
		summary.ConflictsByType[conflict.Type]++
	}

	// Count resolution methods
	for _, resolution := range result.Resolutions {
		summary.ResolutionMethods[resolution.Method]++
	}

	// Calculate resolution rate
	if summary.TotalConflicts > 0 {
		summary.ResolutionRate = float64(summary.ResolvedCount) / float64(summary.TotalConflicts)
	}

	return summary
}

// ConflictSummary summarizes conflict information
type ConflictSummary struct {
	TotalConflicts    int                      `json:"total_conflicts"`
	ResolvedCount     int                      `json:"resolved_count"`
	ResolutionRate    float64                  `json:"resolution_rate"`
	ConflictsByType   map[string]int           `json:"conflicts_by_type"`
	ResolutionMethods map[ResolutionMethod]int `json:"resolution_methods"`
}

// GenerateMergeReport creates a comprehensive merge report
func (mv *MergeVisualizer) GenerateMergeReport(result *FusionResult) MergeReport {
	report := MergeReport{
		Timestamp:        result.Timestamp,
		BuildingID:       result.BuildingID,
		Summary:          mv.GetConflictSummary(result),
		ChangeStatistics: mv.changeDetector.GetStatistics(),
		QualityMetrics:   mv.calculateQualityMetrics(result),
		Recommendations:  mv.generateRecommendations(result),
	}

	return report
}

// MergeReport represents a comprehensive merge report
type MergeReport struct {
	Timestamp        time.Time        `json:"timestamp"`
	BuildingID       string           `json:"building_id"`
	Summary          ConflictSummary  `json:"conflict_summary"`
	ChangeStatistics ChangeStatistics `json:"change_statistics"`
	QualityMetrics   QualityMetrics   `json:"quality_metrics"`
	Recommendations  []Recommendation `json:"recommendations"`
}

// QualityMetrics represents data quality metrics
type QualityMetrics struct {
	OverallConfidence  float64 `json:"overall_confidence"`
	CoveragePercentage float64 `json:"coverage_percentage"`
	DataCompleteness   float64 `json:"data_completeness"`
	ConflictDensity    float64 `json:"conflict_density"`
	ChangeVolatility   float64 `json:"change_volatility"`
}

// Recommendation represents a merge improvement recommendation
type Recommendation struct {
	Priority    string `json:"priority"` // "high", "medium", "low"
	Category    string `json:"category"`
	Description string `json:"description"`
	Action      string `json:"action"`
}

// calculateQualityMetrics calculates data quality metrics
func (mv *MergeVisualizer) calculateQualityMetrics(result *FusionResult) QualityMetrics {
	metrics := QualityMetrics{
		OverallConfidence:  result.ConfidenceScore,
		CoveragePercentage: result.Coverage,
	}

	// Calculate data completeness
	if len(result.MergedEquipment) > 0 {
		complete := 0
		for _, eq := range result.MergedEquipment {
			if eq.Confidence >= spatial.ConfidenceMedium && len(eq.Sources) > 1 {
				complete++
			}
		}
		metrics.DataCompleteness = float64(complete) / float64(len(result.MergedEquipment))
	}

	// Calculate conflict density
	if result.Statistics.EquipmentProcessed > 0 {
		metrics.ConflictDensity = float64(result.Statistics.ConflictsDetected) /
			float64(result.Statistics.EquipmentProcessed)
	}

	// Calculate change volatility
	if len(result.Changes) > 0 {
		highMagnitude := 0
		for _, change := range result.Changes {
			if change.Magnitude > 0.5 {
				highMagnitude++
			}
		}
		metrics.ChangeVolatility = float64(highMagnitude) / float64(len(result.Changes))
	}

	return metrics
}

// generateRecommendations generates improvement recommendations
func (mv *MergeVisualizer) generateRecommendations(result *FusionResult) []Recommendation {
	recommendations := make([]Recommendation, 0)

	// Check coverage
	if result.Coverage < 50 {
		recommendations = append(recommendations, Recommendation{
			Priority:    "high",
			Category:    "coverage",
			Description: "Low building coverage detected",
			Action:      "Schedule additional LiDAR scans for unscanned areas",
		})
	}

	// Check confidence
	lowConfidence := 0
	for _, eq := range result.MergedEquipment {
		if eq.Confidence <= spatial.ConfidenceLow {
			lowConfidence++
		}
	}
	if float64(lowConfidence)/float64(len(result.MergedEquipment)) > 0.3 {
		recommendations = append(recommendations, Recommendation{
			Priority:    "medium",
			Category:    "confidence",
			Description: "Many equipment items have low confidence",
			Action:      "Verify equipment with field measurements or AR scanning",
		})
	}

	// Check unresolved conflicts
	if len(result.Conflicts) > len(result.Resolutions) {
		unresolved := len(result.Conflicts) - len(result.Resolutions)
		recommendations = append(recommendations, Recommendation{
			Priority:    "high",
			Category:    "conflicts",
			Description: fmt.Sprintf("%d unresolved conflicts detected", unresolved),
			Action:      "Review and manually resolve remaining conflicts",
		})
	}

	// Check change rate
	stats := mv.changeDetector.GetStatistics()
	if stats.TotalChanges > 100 {
		recommendations = append(recommendations, Recommendation{
			Priority:    "low",
			Category:    "stability",
			Description: "High rate of changes detected",
			Action:      "Review change history for data quality issues",
		})
	}

	return recommendations
}

// Helper function to check if slice contains string
func contains(slice []string, item string) bool {
	for _, s := range slice {
		if s == item {
			return true
		}
	}
	return false
}
