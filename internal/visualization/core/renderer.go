package core

import (
	"fmt"
	"os"
	"strings"

	"github.com/muesli/termenv"
	"golang.org/x/term"
)

// Renderer is the base interface for all visualization renderers
type Renderer interface {
	// Core rendering method
	Render(data DataSet, options RenderOptions) (*Canvas, error)

	// Get dimensions
	GetDimensions() (width, height int)

	// Capability detection
	SupportsUnicode() bool
	SupportsColors() bool
	Supports256Colors() bool
	SupportsTrueColor() bool
}

// DataSet represents input data for visualization
type DataSet interface {
	// GetType returns the data type (bar, line, heatmap, etc.)
	GetType() string
	// Validate checks if data is valid for visualization
	Validate() error
}

// RenderOptions configures how data is rendered
type RenderOptions struct {
	Width       int
	Height      int
	ColorScheme ColorScheme
	SymbolSet   SymbolSet
	Title       string
	ShowLegend  bool
	ShowAxes    bool
	ShowValues  bool
	Interactive bool
}

// TerminalRenderer implements the Renderer interface
type TerminalRenderer struct {
	output *termenv.Output
	caps   TerminalCapabilities
}

// TerminalCapabilities describes terminal features
type TerminalCapabilities struct {
	Colors      bool
	Colors256   bool
	TrueColor   bool
	Unicode     bool
	Width       int
	Height      int
	Interactive bool
}

// NewTerminalRenderer creates a new terminal renderer
func NewTerminalRenderer() *TerminalRenderer {
	output := termenv.NewOutput(os.Stdout)

	return &TerminalRenderer{
		output: output,
		caps:   detectCapabilities(output),
	}
}

// Render implements the Renderer interface
func (r *TerminalRenderer) Render(data DataSet, options RenderOptions) (*Canvas, error) {
	if err := data.Validate(); err != nil {
		return nil, fmt.Errorf("invalid data: %w", err)
	}

	// Use terminal dimensions if not specified
	if options.Width == 0 || options.Height == 0 {
		options.Width, options.Height = r.GetDimensions()
	}

	// Create canvas
	canvas := NewCanvas(options.Width, options.Height)

	// Apply appropriate symbol set based on capabilities
	if options.SymbolSet.IsEmpty() {
		if r.SupportsUnicode() {
			options.SymbolSet = UnicodeSymbols
		} else {
			options.SymbolSet = ASCIISymbols
		}
	}

	// Apply color scheme based on capabilities
	if options.ColorScheme.IsEmpty() {
		if r.SupportsColors() {
			options.ColorScheme = DefaultColorScheme
		} else {
			options.ColorScheme = MonochromeScheme
		}
	}

	return canvas, nil
}

// GetDimensions returns terminal width and height
func (r *TerminalRenderer) GetDimensions() (width, height int) {
	return r.caps.Width, r.caps.Height
}

// SupportsUnicode checks if terminal supports Unicode
func (r *TerminalRenderer) SupportsUnicode() bool {
	return r.caps.Unicode
}

// SupportsColors checks if terminal supports basic colors
func (r *TerminalRenderer) SupportsColors() bool {
	return r.caps.Colors
}

// Supports256Colors checks if terminal supports 256 colors
func (r *TerminalRenderer) Supports256Colors() bool {
	return r.caps.Colors256
}

// SupportsTrueColor checks if terminal supports true color
func (r *TerminalRenderer) SupportsTrueColor() bool {
	return r.caps.TrueColor
}

// detectCapabilities detects terminal capabilities
func detectCapabilities(output *termenv.Output) TerminalCapabilities {
	width, height, _ := term.GetSize(int(os.Stdout.Fd()))

	// Default to reasonable values if detection fails
	if width <= 0 {
		width = 80
	}
	if height <= 0 {
		height = 24
	}

	caps := TerminalCapabilities{
		Width:       width,
		Height:      height,
		Interactive: term.IsTerminal(int(os.Stdout.Fd())),
	}

	// Detect color support
	switch output.Profile {
	case termenv.TrueColor:
		caps.TrueColor = true
		caps.Colors256 = true
		caps.Colors = true
	case termenv.ANSI256:
		caps.Colors256 = true
		caps.Colors = true
	case termenv.ANSI:
		caps.Colors = true
	}

	// Detect Unicode support (simple heuristic)
	caps.Unicode = detectUnicodeSupport()

	return caps
}

// detectUnicodeSupport attempts to detect Unicode support
func detectUnicodeSupport() bool {
	// Check common environment variables
	lang := os.Getenv("LANG")
	lcAll := os.Getenv("LC_ALL")
	lcCtype := os.Getenv("LC_CTYPE")

	// Look for UTF-8 in locale settings
	for _, env := range []string{lang, lcAll, lcCtype} {
		if strings.Contains(strings.ToUpper(env), "UTF-8") ||
			strings.Contains(strings.ToUpper(env), "UTF8") {
			return true
		}
	}

	// Check TERM variable for known Unicode-capable terminals
	term := os.Getenv("TERM")
	unicodeTerms := []string{"xterm", "rxvt", "konsole", "gnome", "iTerm"}
	for _, ut := range unicodeTerms {
		if strings.Contains(term, ut) {
			return true
		}
	}

	// Default to false for safety
	return false
}

// RenderToString converts a canvas to a string for terminal output
func RenderToString(canvas *Canvas) string {
	var output strings.Builder

	for y := 0; y < canvas.Height; y++ {
		for x := 0; x < canvas.Width; x++ {
			cell := canvas.GetCell(x, y)
			// Apply colors if supported
			if cell.Foreground != NoColor || cell.Background != NoColor {
				// Color rendering would go here
				output.WriteRune(cell.Char)
			} else {
				output.WriteRune(cell.Char)
			}
		}
		if y < canvas.Height-1 {
			output.WriteRune('\n')
		}
	}

	return output.String()
}
