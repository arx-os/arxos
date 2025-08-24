package display

import (
	"fmt"
	"strings"
	"text/tabwriter"
	"os"
	
	"github.com/fatih/color"
)

// TableDisplay handles table formatting
type TableDisplay struct {
	writer    *tabwriter.Writer
	useColor  bool
	headers   []string
	rows      [][]string
}

// NewTableDisplay creates a new table display
func NewTableDisplay() *TableDisplay {
	return &TableDisplay{
		writer:   tabwriter.NewWriter(os.Stdout, 0, 0, 2, ' ', 0),
		useColor: true,
		rows:     [][]string{},
	}
}

// SetHeaders sets the table headers
func (t *TableDisplay) SetHeaders(headers ...string) {
	t.headers = headers
}

// AddRow adds a row to the table
func (t *TableDisplay) AddRow(values ...string) {
	t.rows = append(t.rows, values)
}

// Render displays the table
func (t *TableDisplay) Render() {
	if len(t.headers) == 0 && len(t.rows) == 0 {
		return
	}
	
	// Print border
	t.printBorder()
	
	// Print headers
	if len(t.headers) > 0 {
		t.printRow(t.headers, true)
		t.printSeparator()
	}
	
	// Print rows
	for _, row := range t.rows {
		t.printRow(row, false)
	}
	
	// Print bottom border
	t.printBorder()
	
	t.writer.Flush()
}

func (t *TableDisplay) printBorder() {
	width := t.calculateWidth()
	fmt.Println("┌" + strings.Repeat("─", width) + "┐")
}

func (t *TableDisplay) printSeparator() {
	width := t.calculateWidth()
	fmt.Println("├" + strings.Repeat("─", width) + "┤")
}

func (t *TableDisplay) printRow(values []string, isHeader bool) {
	fmt.Print("│ ")
	for i, val := range values {
		if isHeader && t.useColor {
			fmt.Print(color.New(color.FgCyan, color.Bold).Sprint(val))
		} else {
			fmt.Print(val)
		}
		if i < len(values)-1 {
			fmt.Print(" │ ")
		}
	}
	fmt.Println(" │")
}

func (t *TableDisplay) calculateWidth() int {
	maxWidth := 0
	
	// Check headers
	if len(t.headers) > 0 {
		width := len(strings.Join(t.headers, " │ ")) + 4
		if width > maxWidth {
			maxWidth = width
		}
	}
	
	// Check rows
	for _, row := range t.rows {
		width := len(strings.Join(row, " │ ")) + 4
		if width > maxWidth {
			maxWidth = width
		}
	}
	
	return maxWidth
}

// ArxObjectTable displays ArxObject results in a table
func ArxObjectTable(objects []interface{}) {
	table := NewTableDisplay()
	table.SetHeaders("ID", "Type", "Confidence", "Validated", "Location")
	
	for range objects {
		// Type assertion and formatting would go here
		// This is a placeholder
		table.AddRow(
			"obj_123",
			"wall",
			"85%",
			"Yes",
			"Floor 3",
		)
	}
	
	table.Render()
}

// Color functions for terminal output
func Red(text string) string {
	return color.New(color.FgRed).Sprint(text)
}

func Green(text string) string {
	return color.New(color.FgGreen).Sprint(text)
}

func Yellow(text string) string {
	return color.New(color.FgYellow).Sprint(text)
}

func Blue(text string) string {
	return color.New(color.FgBlue).Sprint(text)
}

// Global display settings
var (
	outputFormat string
	isVerbose    bool
)

// SetFormat sets the output format
func SetFormat(format string) {
	outputFormat = format
}

// SetVerbose sets verbose mode
func SetVerbose(verbose bool) {
	isVerbose = verbose
}