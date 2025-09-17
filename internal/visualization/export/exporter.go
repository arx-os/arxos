package export

import (
	"fmt"
	"io"
	"os"
	"path/filepath"
	"regexp"
	"strings"
	"time"
)

// Format represents export file format
type Format int

const (
	FormatPlainText Format = iota
	FormatANSI
	FormatMarkdown
	FormatHTML
)

// Options for exporting visualizations
type Options struct {
	Format     Format
	FilePath   string
	Append     bool
	Timestamp  bool
	Metadata   map[string]string
	StripANSI  bool
	WrapWidth  int
}

// Exporter handles saving visualizations to files
type Exporter struct {
	options Options
}

// NewExporter creates a new exporter
func NewExporter(options Options) *Exporter {
	return &Exporter{
		options: options,
	}
}

// Export saves visualization output to file
func (e *Exporter) Export(content string) error {
	// Process content based on format
	processed, err := e.processContent(content)
	if err != nil {
		return fmt.Errorf("failed to process content: %w", err)
	}

	// Ensure directory exists
	dir := filepath.Dir(e.options.FilePath)
	if err := os.MkdirAll(dir, 0755); err != nil {
		return fmt.Errorf("failed to create directory: %w", err)
	}

	// Open file
	flags := os.O_CREATE | os.O_WRONLY
	if e.options.Append {
		flags |= os.O_APPEND
	} else {
		flags |= os.O_TRUNC
	}

	file, err := os.OpenFile(e.options.FilePath, flags, 0644)
	if err != nil {
		return fmt.Errorf("failed to open file: %w", err)
	}
	defer file.Close()

	// Write content
	if err := e.writeContent(file, processed); err != nil {
		return fmt.Errorf("failed to write content: %w", err)
	}

	return nil
}

// processContent applies format-specific processing
func (e *Exporter) processContent(content string) (string, error) {
	switch e.options.Format {
	case FormatPlainText:
		return e.toPlainText(content), nil
	case FormatANSI:
		return content, nil // Keep ANSI codes
	case FormatMarkdown:
		return e.toMarkdown(content), nil
	case FormatHTML:
		return e.toHTML(content), nil
	default:
		return content, nil
	}
}

// writeContent writes processed content with optional metadata
func (e *Exporter) writeContent(w io.Writer, content string) error {
	var output strings.Builder

	// Add timestamp if requested
	if e.options.Timestamp {
		timestamp := time.Now().Format("2006-01-02 15:04:05")
		output.WriteString(fmt.Sprintf("# Generated: %s\n", timestamp))
		output.WriteString(strings.Repeat("-", 60) + "\n")
	}

	// Add metadata
	if len(e.options.Metadata) > 0 {
		for key, value := range e.options.Metadata {
			output.WriteString(fmt.Sprintf("# %s: %s\n", key, value))
		}
		output.WriteString(strings.Repeat("-", 60) + "\n")
	}

	// Add content
	output.WriteString(content)

	// Add separator for append mode
	if e.options.Append {
		output.WriteString("\n\n")
	}

	// Write to file
	_, err := w.Write([]byte(output.String()))
	return err
}

// toPlainText strips ANSI codes and formatting
func (e *Exporter) toPlainText(content string) string {
	// Strip ANSI escape sequences
	ansiRegex := regexp.MustCompile(`\x1b\[[0-9;]*m`)
	plain := ansiRegex.ReplaceAllString(content, "")

	// Strip other control sequences
	controlRegex := regexp.MustCompile(`\x1b\[[^m]*[A-Za-z]`)
	plain = controlRegex.ReplaceAllString(plain, "")

	return plain
}

// toMarkdown converts to Markdown format
func (e *Exporter) toMarkdown(content string) string {
	// Strip ANSI codes first
	plain := e.toPlainText(content)

	var output strings.Builder
	output.WriteString("```\n")
	output.WriteString(plain)
	output.WriteString("\n```\n")

	return output.String()
}

// toHTML converts to HTML with preserved formatting
func (e *Exporter) toHTML(content string) string {
	// Strip ANSI codes
	plain := e.toPlainText(content)

	var output strings.Builder
	output.WriteString("<!DOCTYPE html>\n")
	output.WriteString("<html>\n<head>\n")
	output.WriteString("<style>\n")
	output.WriteString("pre { font-family: 'Courier New', monospace; }\n")
	output.WriteString(".visualization { background: #1e1e1e; color: #d4d4d4; padding: 20px; }\n")
	output.WriteString("</style>\n</head>\n<body>\n")
	output.WriteString("<div class=\"visualization\">\n")
	output.WriteString("<pre>\n")

	// Escape HTML entities
	plain = strings.ReplaceAll(plain, "&", "&amp;")
	plain = strings.ReplaceAll(plain, "<", "&lt;")
	plain = strings.ReplaceAll(plain, ">", "&gt;")

	output.WriteString(plain)
	output.WriteString("</pre>\n")
	output.WriteString("</div>\n")
	output.WriteString("</body>\n</html>\n")

	return output.String()
}

// ExportMultiple exports multiple visualizations to a single file
func ExportMultiple(visualizations map[string]string, options Options) error {
	exporter := NewExporter(options)

	var combined strings.Builder
	for title, content := range visualizations {
		combined.WriteString(fmt.Sprintf("\n=== %s ===\n\n", title))
		combined.WriteString(content)
		combined.WriteString("\n")
	}

	return exporter.Export(combined.String())
}

// QuickExport provides simple export with defaults
func QuickExport(content, filename string) error {
	options := Options{
		Format:    FormatPlainText,
		FilePath:  filename,
		Timestamp: true,
	}

	exporter := NewExporter(options)
	return exporter.Export(content)
}