package core

// Color represents a terminal color
type Color int

// Standard terminal colors
const (
	NoColor Color = iota
	Black
	Red
	Green
	Yellow
	Blue
	Magenta
	Cyan
	White
	BrightBlack
	BrightRed
	BrightGreen
	BrightYellow
	BrightBlue
	BrightMagenta
	BrightCyan
	BrightWhite
)

// ColorScheme defines colors for different chart elements
type ColorScheme struct {
	Primary     Color
	Secondary   Color
	Success     Color
	Warning     Color
	Error       Color
	Info        Color

	// Gradient colors for heatmaps
	GradientLow  Color
	GradientMid  Color
	GradientHigh Color

	// Chart-specific
	BarColors  []Color
	LineColors []Color

	// UI elements
	Border     Color
	Text       Color
	Background Color
}

// DefaultColorScheme provides standard colors
var DefaultColorScheme = ColorScheme{
	Primary:      Blue,
	Secondary:    Cyan,
	Success:      Green,
	Warning:      Yellow,
	Error:        Red,
	Info:         Cyan,
	GradientLow:  Blue,
	GradientMid:  Yellow,
	GradientHigh: Red,
	BarColors:    []Color{Blue, Green, Yellow, Magenta, Cyan},
	LineColors:   []Color{Blue, Green, Red, Yellow, Magenta},
	Border:       White,
	Text:         White,
	Background:   NoColor,
}

// MonochromeScheme provides a monochrome color scheme
var MonochromeScheme = ColorScheme{
	Primary:      White,
	Secondary:    White,
	Success:      White,
	Warning:      White,
	Error:        White,
	Info:         White,
	GradientLow:  White,
	GradientMid:  White,
	GradientHigh: White,
	BarColors:    []Color{White},
	LineColors:   []Color{White},
	Border:       White,
	Text:         White,
	Background:   NoColor,
}

// HighContrastScheme provides high contrast colors
var HighContrastScheme = ColorScheme{
	Primary:      BrightWhite,
	Secondary:    BrightCyan,
	Success:      BrightGreen,
	Warning:      BrightYellow,
	Error:        BrightRed,
	Info:         BrightCyan,
	GradientLow:  BrightBlue,
	GradientMid:  BrightYellow,
	GradientHigh: BrightRed,
	BarColors:    []Color{BrightBlue, BrightGreen, BrightYellow, BrightMagenta, BrightCyan},
	LineColors:   []Color{BrightBlue, BrightGreen, BrightRed, BrightYellow, BrightMagenta},
	Border:       BrightWhite,
	Text:         BrightWhite,
	Background:   Black,
}

// IsEmpty checks if the color scheme is empty
func (cs ColorScheme) IsEmpty() bool {
	return cs.Primary == NoColor && cs.Secondary == NoColor
}

// GetBarColor returns a color for bar charts (cycles through available colors)
func (cs ColorScheme) GetBarColor(index int) Color {
	if len(cs.BarColors) == 0 {
		return cs.Primary
	}
	return cs.BarColors[index%len(cs.BarColors)]
}

// GetLineColor returns a color for line charts (cycles through available colors)
func (cs ColorScheme) GetLineColor(index int) Color {
	if len(cs.LineColors) == 0 {
		return cs.Primary
	}
	return cs.LineColors[index%len(cs.LineColors)]
}

// GetGradientColor returns a color based on a value between 0 and 1
func (cs ColorScheme) GetGradientColor(value float64) Color {
	if value < 0 {
		value = 0
	}
	if value > 1 {
		value = 1
	}

	if value < 0.33 {
		return cs.GradientLow
	} else if value < 0.67 {
		return cs.GradientMid
	} else {
		return cs.GradientHigh
	}
}

// GetStatusColor returns a color based on status
func (cs ColorScheme) GetStatusColor(status string) Color {
	switch status {
	case "success", "operational", "ok", "healthy":
		return cs.Success
	case "warning", "maintenance", "degraded":
		return cs.Warning
	case "error", "failed", "critical", "down":
		return cs.Error
	case "info", "unknown", "pending":
		return cs.Info
	default:
		return cs.Primary
	}
}