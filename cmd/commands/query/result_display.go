package query

import (
	"encoding/csv"
	"encoding/json"
	"fmt"
	"os"
	"strings"
	"text/tabwriter"
	"time"
)

// AQLResult represents the result of an AQL query execution
type AQLResult struct {
	Type       string
	Objects    []interface{}
	Count      int
	Message    string
	Metadata   map[string]interface{}
	ExecutedAt time.Time
}

// ResultDisplay handles formatting and displaying AQL query results
type ResultDisplay struct {
	Format     string
	Style      string
	Pagination bool
	Highlight  bool
	MaxWidth   int
}

// NewResultDisplay creates a new result display instance
func NewResultDisplay(format, style string) *ResultDisplay {
	return &ResultDisplay{
		Format:     format,
		Style:      style,
		Pagination: true,
		Highlight:  true,
		MaxWidth:   120,
	}
}

// DisplayResult formats and displays query results
func (rd *ResultDisplay) DisplayResult(result *AQLResult) error {
	switch rd.Format {
	case "table":
		return rd.displayTable(result)
	case "json":
		return rd.displayJSON(result)
	case "csv":
		return rd.displayCSV(result)
	case "ascii-bim":
		return rd.displayASCIIBIM(result)
	case "summary":
		return rd.displaySummary(result)
	default:
		return rd.displayTable(result) // Default to table format
	}
}

// displayTable displays results in a formatted table
func (rd *ResultDisplay) displayTable(result *AQLResult) error {
	if result == nil || len(result.Objects) == 0 {
		fmt.Println("No results found.")
		return nil
	}

	// Create tabwriter for aligned columns
	w := tabwriter.NewWriter(os.Stdout, 0, 0, 2, ' ', 0)
	defer w.Flush()

	// Print header
	rd.printTableHeader(w, result)

	// Print results
	for i, obj := range result.Objects {
		rd.printTableRow(w, obj, i+1)
	}

	// Print footer with summary
	rd.printTableFooter(w, result)

	return nil
}

// printTableHeader prints the table header
func (rd *ResultDisplay) printTableHeader(w *tabwriter.Writer, result *AQLResult) {
	// Determine columns based on first object
	if len(result.Objects) == 0 {
		return
	}

	obj := result.Objects[0]
	columns := rd.getObjectColumns(obj)

	// Print column headers
	header := "#\t"
	for _, col := range columns {
		header += col + "\t"
	}
	fmt.Fprintln(w, header)

	// Print separator line
	separator := "---\t"
	for range columns {
		separator += "---\t"
	}
	fmt.Fprintln(w, separator)
}

// printTableRow prints a single table row
func (rd *ResultDisplay) printTableRow(w *tabwriter.Writer, obj interface{}, index int) {
	// Convert object to map for display
	objMap := rd.objectToMap(obj)

	// Print row number
	row := fmt.Sprintf("%d\t", index)

	// Print object data
	for _, value := range objMap {
		row += fmt.Sprintf("%v\t", value)
	}

	fmt.Fprintln(w, row)
}

// printTableFooter prints table summary
func (rd *ResultDisplay) printTableFooter(w *tabwriter.Writer, result *AQLResult) {
	fmt.Fprintln(w, "")
	fmt.Fprintf(w, "Total Results: %d\t", result.Count)
	fmt.Fprintf(w, "Executed: %s\t", result.ExecutedAt.Format("2006-01-02 15:04:05"))

	if result.Metadata != nil {
		if rowsAffected, ok := result.Metadata["rows_affected"]; ok {
			fmt.Fprintf(w, "Rows Affected: %v", rowsAffected)
		}
	}
	fmt.Fprintln(w, "")
}

// displayJSON displays results in JSON format
func (rd *ResultDisplay) displayJSON(result *AQLResult) error {
	if result == nil {
		fmt.Println("null")
		return nil
	}

	// Create output structure
	output := map[string]interface{}{
		"type":        result.Type,
		"count":       result.Count,
		"executed_at": result.ExecutedAt,
		"metadata":    result.Metadata,
		"results":     result.Objects,
	}

	// Marshal to JSON with pretty printing
	jsonData, err := json.MarshalIndent(output, "", "  ")
	if err != nil {
		return fmt.Errorf("failed to marshal JSON: %w", err)
	}

	fmt.Println(string(jsonData))
	return nil
}

// displayCSV displays results in CSV format
func (rd *ResultDisplay) displayCSV(result *AQLResult) error {
	if result == nil || len(result.Objects) == 0 {
		return nil
	}

	// Create CSV writer
	w := csv.NewWriter(os.Stdout)
	defer w.Flush()

	// Get columns from first object
	obj := result.Objects[0]
	columns := rd.getObjectColumns(obj)

	// Write header
	if err := w.Write(columns); err != nil {
		return fmt.Errorf("failed to write CSV header: %w", err)
	}

	// Write data rows
	for _, obj := range result.Objects {
		objMap := rd.objectToMap(obj)
		row := make([]string, len(columns))

		for i, col := range columns {
			if value, ok := objMap[col]; ok {
				row[i] = fmt.Sprintf("%v", value)
			}
		}

		if err := w.Write(row); err != nil {
			return fmt.Errorf("failed to write CSV row: %w", err)
		}
	}

	return nil
}

// displayASCIIBIM displays results in ASCII-BIM format for spatial queries
func (rd *ResultDisplay) displayASCIIBIM(result *AQLResult) error {
	if result == nil || len(result.Objects) == 0 {
		fmt.Println("No spatial results to display.")
		return nil
	}

	fmt.Println("=== ASCII-BIM Spatial View ===")
	fmt.Printf("Results: %d objects\n", result.Count)
	fmt.Println()

	// Group objects by type for spatial display
	typeGroups := make(map[string][]interface{})
	for _, obj := range result.Objects {
		objMap := rd.objectToMap(obj)
		if objType, ok := objMap["type"]; ok {
			typeStr := fmt.Sprintf("%v", objType)
			typeGroups[typeStr] = append(typeGroups[typeStr], obj)
		}
	}

	// Display each type group
	for objType, objects := range typeGroups {
		fmt.Printf("--- %s (%d objects) ---\n", objType, len(objects))

		for i, obj := range objects {
			objMap := rd.objectToMap(obj)
			fmt.Printf("%d. %s", i+1, rd.formatObjectSummary(objMap))

			// Show spatial information if available
			if location, ok := objMap["location"]; ok {
				fmt.Printf(" @ %v", location)
			}
			if coordinates, ok := objMap["coordinates"]; ok {
				fmt.Printf(" [%v]", coordinates)
			}
			fmt.Println()
		}
		fmt.Println()
	}

	return nil
}

// displaySummary displays a concise summary of results
func (rd *ResultDisplay) displaySummary(result *AQLResult) error {
	if result == nil {
		fmt.Println("No results.")
		return nil
	}

	fmt.Printf("Query Results Summary\n")
	fmt.Printf("====================\n")
	fmt.Printf("Type: %s\n", result.Type)
	fmt.Printf("Count: %d objects\n", result.Count)
	fmt.Printf("Executed: %s\n", result.ExecutedAt.Format("2006-01-02 15:04:05"))

	if result.Metadata != nil {
		fmt.Printf("Metadata: %v\n", result.Metadata)
	}

	// Show sample results if available
	if len(result.Objects) > 0 {
		fmt.Printf("\nSample Results:\n")
		sampleCount := 3
		if len(result.Objects) < sampleCount {
			sampleCount = len(result.Objects)
		}

		for i := 0; i < sampleCount; i++ {
			obj := result.Objects[i]
			objMap := rd.objectToMap(obj)
			fmt.Printf("  %d. %s\n", i+1, rd.formatObjectSummary(objMap))
		}

		if len(result.Objects) > sampleCount {
			fmt.Printf("  ... and %d more\n", len(result.Objects)-sampleCount)
		}
	}

	return nil
}

// getObjectColumns extracts column names from an object
func (rd *ResultDisplay) getObjectColumns(obj interface{}) []string {
	objMap := rd.objectToMap(obj)

	// Common ArxObject fields
	commonFields := []string{"id", "type", "path", "confidence", "status", "created_at", "updated_at"}

	// Add custom fields from object data
	customFields := make([]string, 0)
	for key := range objMap {
		if !rd.isCommonField(key) {
			customFields = append(customFields, key)
		}
	}

	// Combine and return
	allFields := append(commonFields, customFields...)
	return allFields
}

// isCommonField checks if a field is a common ArxObject field
func (rd *ResultDisplay) isCommonField(field string) bool {
	commonFields := map[string]bool{
		"id": true, "type": true, "path": true, "confidence": true,
		"status": true, "created_at": true, "updated_at": true,
	}
	return commonFields[field]
}

// objectToMap converts an object to a map for display
func (rd *ResultDisplay) objectToMap(obj interface{}) map[string]interface{} {
	// For now, handle basic types - this will be enhanced with proper ArxObject handling
	objMap := make(map[string]interface{})

	// Try to convert to JSON and back to get a map
	if jsonData, err := json.Marshal(obj); err == nil {
		if err := json.Unmarshal(jsonData, &objMap); err == nil {
			return objMap
		}
	}

	// Fallback: create basic map
	objMap["id"] = "unknown"
	objMap["type"] = "unknown"
	objMap["path"] = "unknown"

	return objMap
}

// formatObjectSummary creates a brief summary of an object
func (rd *ResultDisplay) formatObjectSummary(objMap map[string]interface{}) string {
	parts := make([]string, 0)

	if id, ok := objMap["id"]; ok {
		parts = append(parts, fmt.Sprintf("ID:%v", id))
	}

	if objType, ok := objMap["type"]; ok {
		parts = append(parts, fmt.Sprintf("Type:%v", objType))
	}

	if path, ok := objMap["path"]; ok {
		parts = append(parts, fmt.Sprintf("Path:%v", path))
	}

	if confidence, ok := objMap["confidence"]; ok {
		parts = append(parts, fmt.Sprintf("Confidence:%.2f", confidence))
	}

	return strings.Join(parts, " | ")
}

// SetFormat sets the output format
func (rd *ResultDisplay) SetFormat(format string) {
	rd.Format = format
}

// SetStyle sets the display style
func (rd *ResultDisplay) SetStyle(style string) {
	rd.Style = style
}

// SetPagination enables/disables pagination
func (rd *ResultDisplay) SetPagination(enabled bool) {
	rd.Pagination = enabled
}

// SetHighlight enables/disables highlighting
func (rd *ResultDisplay) SetHighlight(enabled bool) {
	rd.Highlight = enabled
}

// SetMaxWidth sets the maximum display width
func (rd *ResultDisplay) SetMaxWidth(width int) {
	rd.MaxWidth = width
}
