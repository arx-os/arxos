package formats

import (
	"context"
	"fmt"
	"io"
	"os"
	"regexp"
	"strings"

	"github.com/arx-os/arxos/internal/common/logger"
)

// TableExtractor provides PDF table extraction functionality
type TableExtractor struct {
	config TableExtractionConfig
}

// TableExtractionConfig holds configuration for table extraction
type TableExtractionConfig struct {
	MinCellWidth   int     `json:"min_cell_width"`
	MinCellHeight  int     `json:"min_cell_height"`
	MinTableRows   int     `json:"min_table_rows"`
	MinTableCols   int     `json:"min_table_cols"`
	CellPadding    int     `json:"cell_padding"`
	MergeThreshold float64 `json:"merge_threshold"`
	TextSimilarity float64 `json:"text_similarity"`
	UseOCR         bool    `json:"use_ocr"`
	OCRConfidence  float64 `json:"ocr_confidence"`
}

// DefaultTableExtractionConfig returns default configuration
func DefaultTableExtractionConfig() TableExtractionConfig {
	return TableExtractionConfig{
		MinCellWidth:   20,
		MinCellHeight:  10,
		MinTableRows:   2,
		MinTableCols:   2,
		CellPadding:    2,
		MergeThreshold: 0.8,
		TextSimilarity: 0.7,
		UseOCR:         false,
		OCRConfidence:  0.8,
	}
}

// NewTableExtractor creates a new table extractor
func NewTableExtractor(config TableExtractionConfig) *TableExtractor {
	return &TableExtractor{
		config: config,
	}
}

// ExtractTables extracts tables from PDF content
func (t *TableExtractor) ExtractTables(ctx context.Context, pdfPath string) ([]ExtractedTable, error) {
	// Read PDF file
	file, err := os.Open(pdfPath)
	if err != nil {
		return nil, fmt.Errorf("failed to open PDF file: %w", err)
	}
	defer file.Close()

	// Extract text content
	text, err := t.extractTextFromPDF(file)
	if err != nil {
		return nil, fmt.Errorf("failed to extract text from PDF: %w", err)
	}

	// Parse tables from text
	tables, err := t.parseTablesFromText(text)
	if err != nil {
		return nil, fmt.Errorf("failed to parse tables from text: %w", err)
	}

	logger.Debug("Extracted %d tables from PDF: %s", len(tables), pdfPath)
	return tables, nil
}

// extractTextFromPDF extracts text content from PDF
func (t *TableExtractor) extractTextFromPDF(file *os.File) (string, error) {
	// For now, use a simple text extraction approach
	// In production, this would use a proper PDF library like pdfcpu or unidoc
	content, err := io.ReadAll(file)
	if err != nil {
		return "", err
	}

	// Basic text extraction using regex patterns
	// This is a simplified approach - real implementation would use PDF parsing library
	text := t.extractTextFromBytes(content)
	return text, nil
}

// extractTextFromBytes extracts text from PDF bytes using basic patterns
func (t *TableExtractor) extractTextFromBytes(data []byte) string {
	// Look for text streams in PDF content
	textPattern := regexp.MustCompile(`BT\s+.*?ET`)
	matches := textPattern.FindAll(data, -1)

	var textBuilder strings.Builder

	for _, match := range matches {
		// Extract text content from text objects
		textContent := t.extractTextFromStream(match)
		if textContent != "" {
			textBuilder.WriteString(textContent)
			textBuilder.WriteString("\n")
		}
	}

	return textBuilder.String()
}

// extractTextFromStream extracts text from a PDF text stream
func (t *TableExtractor) extractTextFromStream(stream []byte) string {
	// Look for text strings in the stream
	textPattern := regexp.MustCompile(`\(([^)]+)\)`)
	matches := textPattern.FindAllSubmatch(stream, -1)

	var textBuilder strings.Builder

	for _, match := range matches {
		if len(match) > 1 {
			text := string(match[1])
			// Clean up text
			text = strings.TrimSpace(text)
			if text != "" {
				textBuilder.WriteString(text)
				textBuilder.WriteString(" ")
			}
		}
	}

	return textBuilder.String()
}

// parseTablesFromText parses tables from extracted text
func (t *TableExtractor) parseTablesFromText(text string) ([]ExtractedTable, error) {
	var tables []ExtractedTable

	// Split text into lines
	lines := strings.Split(text, "\n")

	// Look for table patterns
	tableLines := t.identifyTableLines(lines)

	// Group consecutive table lines into tables
	tableGroups := t.groupTableLines(tableLines)

	// Parse each table group
	for i, group := range tableGroups {
		table, err := t.parseTableGroup(group, i)
		if err != nil {
			logger.Warn("Failed to parse table group %d: %v", i, err)
			continue
		}

		if t.isValidTable(table) {
			tables = append(tables, *table)
		}
	}

	return tables, nil
}

// identifyTableLines identifies lines that might be part of tables
func (t *TableExtractor) identifyTableLines(lines []string) []TableLine {
	var tableLines []TableLine

	for i, line := range lines {
		line = strings.TrimSpace(line)
		if line == "" {
			continue
		}

		// Check if line looks like a table row
		if t.looksLikeTableRow(line) {
			tableLines = append(tableLines, TableLine{
				LineNumber: i,
				Content:    line,
				Columns:    t.splitIntoColumns(line),
			})
		}
	}

	return tableLines
}

// looksLikeTableRow checks if a line looks like a table row
func (t *TableExtractor) looksLikeTableRow(line string) bool {
	// Check for common table patterns
	patterns := []string{
		`\s+\|\s+`,       // Pipe separators
		`\s{2,}`,         // Multiple spaces
		`\t+`,            // Tabs
		`\s+\d+\.\d+\s+`, // Numbers with decimals
		`\s+[A-Z]+\s+`,   // Uppercase words
		`\s+\d+\s+`,      // Numbers
	}

	for _, pattern := range patterns {
		matched, _ := regexp.MatchString(pattern, line)
		if matched {
			return true
		}
	}

	// Check if line has multiple columns when split by spaces
	columns := strings.Fields(line)
	return len(columns) >= t.config.MinTableCols
}

// splitIntoColumns splits a line into columns
func (t *TableExtractor) splitIntoColumns(line string) []string {
	// Try different splitting strategies
	strategies := []func(string) []string{
		t.splitByPipes,
		t.splitByMultipleSpaces,
		t.splitByTabs,
		t.splitByFixedWidth,
	}

	for _, strategy := range strategies {
		columns := strategy(line)
		if len(columns) >= t.config.MinTableCols {
			return columns
		}
	}

	// Fallback to simple space splitting
	return strings.Fields(line)
}

// splitByPipes splits by pipe characters
func (t *TableExtractor) splitByPipes(line string) []string {
	parts := strings.Split(line, "|")
	var columns []string
	for _, part := range parts {
		part = strings.TrimSpace(part)
		if part != "" {
			columns = append(columns, part)
		}
	}
	return columns
}

// splitByMultipleSpaces splits by multiple spaces
func (t *TableExtractor) splitByMultipleSpaces(line string) []string {
	re := regexp.MustCompile(`\s{2,}`)
	return re.Split(line, -1)
}

// splitByTabs splits by tab characters
func (t *TableExtractor) splitByTabs(line string) []string {
	return strings.Split(line, "\t")
}

// splitByFixedWidth splits by fixed width (simplified)
func (t *TableExtractor) splitByFixedWidth(line string) []string {
	// This is a simplified fixed-width parser
	// Real implementation would analyze column positions
	width := len(line) / t.config.MinTableCols
	var columns []string

	for i := 0; i < len(line); i += width {
		end := i + width
		if end > len(line) {
			end = len(line)
		}
		column := strings.TrimSpace(line[i:end])
		if column != "" {
			columns = append(columns, column)
		}
	}

	return columns
}

// groupTableLines groups consecutive table lines into tables
func (t *TableExtractor) groupTableLines(tableLines []TableLine) [][]TableLine {
	var groups [][]TableLine
	var currentGroup []TableLine

	for i, line := range tableLines {
		if len(currentGroup) == 0 {
			currentGroup = append(currentGroup, line)
		} else {
			// Check if this line is consecutive with the previous one
			if line.LineNumber == tableLines[i-1].LineNumber+1 {
				currentGroup = append(currentGroup, line)
			} else {
				// Start a new group
				if len(currentGroup) >= t.config.MinTableRows {
					groups = append(groups, currentGroup)
				}
				currentGroup = []TableLine{line}
			}
		}
	}

	// Add the last group if it's valid
	if len(currentGroup) >= t.config.MinTableRows {
		groups = append(groups, currentGroup)
	}

	return groups
}

// parseTableGroup parses a group of table lines into a table
func (t *TableExtractor) parseTableGroup(group []TableLine, tableIndex int) (*ExtractedTable, error) {
	if len(group) == 0 {
		return nil, fmt.Errorf("empty table group")
	}

	// Determine the number of columns
	maxCols := 0
	for _, line := range group {
		if len(line.Columns) > maxCols {
			maxCols = len(line.Columns)
		}
	}

	// Normalize all rows to have the same number of columns
	rows := make([][]string, len(group))
	for i, line := range group {
		rows[i] = make([]string, maxCols)
		for j, col := range line.Columns {
			if j < maxCols {
				rows[i][j] = col
			}
		}
	}

	// Extract headers (usually the first row)
	headers := make([]string, maxCols)
	if len(rows) > 0 {
		for i, header := range rows[0] {
			if i < len(headers) {
				headers[i] = strings.TrimSpace(header)
			}
		}
	}

	// Extract data rows
	var dataRows [][]string
	if len(rows) > 1 {
		dataRows = rows[1:]
	}

	table := &ExtractedTable{
		Headers: headers,
		Rows:    dataRows,
		Page:    1, // Placeholder page number
	}

	return table, nil
}

// isValidTable checks if a table is valid according to configuration
func (t *TableExtractor) isValidTable(table *ExtractedTable) bool {
	if len(table.Headers) < t.config.MinTableCols {
		return false
	}

	if len(table.Rows) < t.config.MinTableRows {
		return false
	}

	// Check if table has meaningful content
	hasContent := false
	for _, row := range table.Rows {
		for _, cell := range row {
			if strings.TrimSpace(cell) != "" {
				hasContent = true
				break
			}
		}
		if hasContent {
			break
		}
	}

	return hasContent
}

// TableLine represents a line that might be part of a table
type TableLine struct {
	LineNumber int
	Content    string
	Columns    []string
}

// TableBounds represents the bounds of a table
type TableBounds struct {
	X      float64
	Y      float64
	Width  float64
	Height float64
}
