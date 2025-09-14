// Package rendering provides 256-color terminal support for enhanced visualization
package rendering

import (
	"fmt"
	"math"
)

// Color256 represents a 256-color palette entry
type Color256 uint8

// Standard 256-color palette constants
const (
	// System colors (0-15)
	Black         Color256 = 0
	Red           Color256 = 1
	Green         Color256 = 2
	Yellow        Color256 = 3
	Blue          Color256 = 4
	Magenta       Color256 = 5
	Cyan          Color256 = 6
	White         Color256 = 7
	BrightBlack   Color256 = 8
	BrightRed     Color256 = 9
	BrightGreen   Color256 = 10
	BrightYellow  Color256 = 11
	BrightBlue    Color256 = 12
	BrightMagenta Color256 = 13
	BrightCyan    Color256 = 14
	BrightWhite   Color256 = 15

	// Extended colors for building visualization
	WallGray      Color256 = 238
	FloorGray     Color256 = 236
	GridDark      Color256 = 234
	GridLight     Color256 = 240
	
	// Equipment colors
	OutletOrange  Color256 = 208
	SwitchBlue    Color256 = 33
	PanelRed      Color256 = 196
	LightYellow   Color256 = 226
	SensorGreen   Color256 = 46
	
	// Status colors
	StatusOperational  Color256 = 82  // Light green
	StatusWarning Color256 = 220 // Gold
	StatusFailed  Color256 = 160 // Dark red
	StatusOffline Color256 = 245 // Medium gray
	
	// Energy flow colors (gradient)
	EnergyLow     Color256 = 22  // Dark green
	EnergyMedium  Color256 = 28  // Medium green
	EnergyHigh    Color256 = 46  // Bright green
	EnergyOverload Color256 = 196 // Bright red
	
	// Temperature gradient (cold to hot)
	TempCold      Color256 = 21  // Deep blue
	TempCool      Color256 = 39  // Light blue
	TempNormal    Color256 = 82  // Green
	TempWarm      Color256 = 220 // Yellow
	TempHot       Color256 = 208 // Orange
	TempCritical  Color256 = 196 // Red
)

// Palette manages color schemes for different visualization modes
type Palette struct {
	Mode           PaletteMode
	Background     Color256
	Foreground     Color256
	HighContrast   bool
	ColorBlindMode bool
}

// PaletteMode defines different color schemes
type PaletteMode string

const (
	ModeDefault     PaletteMode = "default"
	ModeDark        PaletteMode = "dark"
	ModeLight       PaletteMode = "light"
	ModeHighContrast PaletteMode = "high_contrast"
	ModeColorBlind  PaletteMode = "color_blind"
	ModeMonochrome  PaletteMode = "monochrome"
)

// NewPalette creates a new color palette
func NewPalette(mode PaletteMode) *Palette {
	p := &Palette{
		Mode: mode,
	}
	
	switch mode {
	case ModeDark:
		p.Background = Black
		p.Foreground = White
	case ModeLight:
		p.Background = BrightWhite
		p.Foreground = Black
	case ModeHighContrast:
		p.Background = Black
		p.Foreground = BrightWhite
		p.HighContrast = true
	case ModeColorBlind:
		p.ColorBlindMode = true
		p.Background = Black
		p.Foreground = White
	case ModeMonochrome:
		p.Background = Black
		p.Foreground = White
	default:
		p.Background = Black
		p.Foreground = White
	}
	
	return p
}

// GetEquipmentColor returns appropriate color for equipment type
func (p *Palette) GetEquipmentColor(equipType string, status string) Color256 {
	if p.Mode == ModeMonochrome {
		return p.getMonochromeIntensity(equipType, status)
	}
	
	// Handle status-based coloring
	switch status {
	case "failed":
		return p.adaptColor(StatusFailed)
	case "warning", "needs_repair":
		return p.adaptColor(StatusWarning)
	case "offline":
		return p.adaptColor(StatusOffline)
	}
	
	// Equipment type coloring
	switch equipType {
	case "outlet":
		return p.adaptColor(OutletOrange)
	case "switch":
		return p.adaptColor(SwitchBlue)
	case "panel":
		return p.adaptColor(PanelRed)
	case "light":
		return p.adaptColor(LightYellow)
	case "sensor":
		return p.adaptColor(SensorGreen)
	default:
		return p.Foreground
	}
}

// GetEnergyColor returns color based on energy level (0.0 to 1.0)
func (p *Palette) GetEnergyColor(level float64) Color256 {
	if p.Mode == ModeMonochrome {
		// Use grayscale intensity
		gray := Color256(232 + uint8(level*23)) // Grayscale range 232-255
		return gray
	}
	
	// Color gradient based on energy level
	if level > 1.0 {
		return p.adaptColor(EnergyOverload)
	} else if level > 0.75 {
		return p.adaptColor(EnergyHigh)
	} else if level > 0.5 {
		return p.adaptColor(EnergyMedium)
	} else {
		return p.adaptColor(EnergyLow)
	}
}

// GetTemperatureColor returns color based on temperature
func (p *Palette) GetTemperatureColor(temp float64) Color256 {
	if p.Mode == ModeMonochrome {
		// Map temperature to grayscale
		normalized := (temp - 10.0) / 30.0 // Normalize 10-40°C to 0-1
		gray := Color256(232 + uint8(math.Min(23, normalized*23)))
		return gray
	}
	
	// Temperature gradient
	if temp < 15 {
		return p.adaptColor(TempCold)
	} else if temp < 18 {
		return p.adaptColor(TempCool)
	} else if temp < 24 {
		return p.adaptColor(TempNormal)
	} else if temp < 28 {
		return p.adaptColor(TempWarm)
	} else if temp < 35 {
		return p.adaptColor(TempHot)
	} else {
		return p.adaptColor(TempCritical)
	}
}

// GetStructuralColor returns colors for building structure elements
func (p *Palette) GetStructuralColor(element string) Color256 {
	if p.Mode == ModeMonochrome {
		switch element {
		case "wall":
			return Color256(245) // Medium gray
		case "floor":
			return Color256(236) // Dark gray
		case "grid":
			return Color256(234) // Very dark gray
		default:
			return p.Foreground
		}
	}
	
	switch element {
	case "wall":
		return p.adaptColor(WallGray)
	case "floor":
		return p.adaptColor(FloorGray)
	case "grid":
		return p.adaptColor(GridDark)
	case "door":
		return p.adaptColor(Color256(94)) // Brown
	case "window":
		return p.adaptColor(Color256(123)) // Light cyan
	default:
		return p.Foreground
	}
}

// adaptColor adjusts color for color-blind mode
func (p *Palette) adaptColor(color Color256) Color256 {
	if !p.ColorBlindMode {
		return color
	}
	
	// Map colors to color-blind friendly alternatives
	// Using deuteranopia-friendly palette
	switch color {
	case Red, PanelRed, StatusFailed:
		return Color256(130) // Orange-brown
	case Green, SensorGreen, StatusOperational:
		return Color256(33)  // Blue
	case Yellow, LightYellow, StatusWarning:
		return Color256(226) // Bright yellow (usually visible)
	default:
		return color
	}
}

// getMonochromeIntensity returns grayscale intensity for monochrome mode
func (p *Palette) getMonochromeIntensity(equipType, status string) Color256 {
	// Base intensity on importance/status
	baseIntensity := uint8(240) // Medium gray default
	
	switch status {
	case "failed":
		baseIntensity = 255 // Bright white
	case "warning", "needs_repair":
		baseIntensity = 250 // Near white
	case "offline":
		baseIntensity = 235 // Dark gray
	}
	
	// Adjust slightly by type for distinction
	switch equipType {
	case "panel":
		baseIntensity += 5
	case "sensor":
		baseIntensity -= 5
	}
	
	return Color256(baseIntensity)
}

// Gradient creates a color gradient between two colors
func Gradient(start, end Color256, steps int) []Color256 {
	if steps <= 1 {
		return []Color256{start}
	}
	
	gradient := make([]Color256, steps)
	gradient[0] = start
	gradient[steps-1] = end
	
	// For 256-color mode, we need to interpolate in RGB space
	// then map back to nearest 256-color palette entry
	// Simplified version using direct palette indices
	
	startIdx := float64(start)
	endIdx := float64(end)
	
	for i := 1; i < steps-1; i++ {
		ratio := float64(i) / float64(steps-1)
		idx := startIdx + (endIdx-startIdx)*ratio
		gradient[i] = Color256(uint8(idx))
	}
	
	return gradient
}

// Format returns ANSI escape sequence for the color
func (c Color256) Format(text string) string {
	return fmt.Sprintf("\033[38;5;%dm%s\033[0m", c, text)
}

// FormatBg returns ANSI escape sequence for background color
func (c Color256) FormatBg(text string) string {
	return fmt.Sprintf("\033[48;5;%dm%s\033[0m", c, text)
}

// RGB converts 256-color to approximate RGB values
func (c Color256) RGB() (r, g, b uint8) {
	// System colors (0-15)
	if c < 16 {
		// Simplified mapping for system colors
		systemColors := [][3]uint8{
			{0, 0, 0},       // Black
			{128, 0, 0},     // Red
			{0, 128, 0},     // Green
			{128, 128, 0},   // Yellow
			{0, 0, 128},     // Blue
			{128, 0, 128},   // Magenta
			{0, 128, 128},   // Cyan
			{192, 192, 192}, // White
			{128, 128, 128}, // Bright Black
			{255, 0, 0},     // Bright Red
			{0, 255, 0},     // Bright Green
			{255, 255, 0},   // Bright Yellow
			{0, 0, 255},     // Bright Blue
			{255, 0, 255},   // Bright Magenta
			{0, 255, 255},   // Bright Cyan
			{255, 255, 255}, // Bright White
		}
		rgb := systemColors[c]
		return rgb[0], rgb[1], rgb[2]
	}
	
	// 216 color cube (16-231)
	if c >= 16 && c <= 231 {
		idx := int(c) - 16
		r = uint8((idx/36)*51)
		g = uint8(((idx%36)/6)*51)
		b = uint8((idx%6)*51)
		return
	}
	
	// Grayscale (232-255)
	if c >= 232 {
		gray := uint8(8 + (int(c)-232)*10)
		return gray, gray, gray
	}
	
	return 0, 0, 0
}

// FromRGB finds the nearest 256-color palette entry for RGB values
func FromRGB(r, g, b uint8) Color256 {
	// Check if it's grayscale
	if r == g && g == b {
		// Map to grayscale range (232-255)
		gray := (int(r) - 8) / 10
		if gray < 0 {
			gray = 0
		}
		if gray > 23 {
			gray = 23
		}
		return Color256(232 + gray)
	}
	
	// Map to 216-color cube
	rIdx := r / 51
	gIdx := g / 51
	bIdx := b / 51
	
	return Color256(16 + rIdx*36 + gIdx*6 + bIdx)
}

// SupportsColor256 checks if terminal supports 256 colors
func SupportsColor256() bool {
	// Check TERM environment variable
	// Most modern terminals support 256 colors
	return true // Simplified - actual implementation would check TERM env var
}