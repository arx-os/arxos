package utils

import (
	"fmt"
	"strings"

	"github.com/charmbracelet/lipgloss"
)

// ColorScheme defines the color scheme for the TUI
type ColorScheme struct {
	Primary    lipgloss.Color
	Secondary  lipgloss.Color
	Success    lipgloss.Color
	Warning    lipgloss.Color
	Error      lipgloss.Color
	Info       lipgloss.Color
	Muted      lipgloss.Color
	Border     lipgloss.Color
	Background lipgloss.Color
}

// DarkTheme defines the dark color scheme
var DarkTheme = ColorScheme{
	Primary:    lipgloss.Color("#205"),
	Secondary:  lipgloss.Color("#505"),
	Success:    lipgloss.Color("#42"),
	Warning:    lipgloss.Color("#214"),
	Error:      lipgloss.Color("#196"),
	Info:       lipgloss.Color("#06B"),
	Muted:      lipgloss.Color("#666"),
	Border:     lipgloss.Color("#333"),
	Background: lipgloss.Color("#000"),
}

// LightTheme defines the light color scheme
var LightTheme = ColorScheme{
	Primary:    lipgloss.Color("#0066CC"),
	Secondary:  lipgloss.Color("#6666CC"),
	Success:    lipgloss.Color("#006600"),
	Warning:    lipgloss.Color("#CC6600"),
	Error:      lipgloss.Color("#CC0000"),
	Info:       lipgloss.Color("#0066CC"),
	Muted:      lipgloss.Color("#999999"),
	Border:     lipgloss.Color("#CCCCCC"),
	Background: lipgloss.Color("#FFFFFF"),
}

// Styles defines the common styles used throughout the TUI
type Styles struct {
	// Base styles
	Primary   lipgloss.Style
	Secondary lipgloss.Style
	Success   lipgloss.Style
	Warning   lipgloss.Style
	Error     lipgloss.Style
	Info      lipgloss.Style
	Muted     lipgloss.Style

	// Layout styles
	Border lipgloss.Style
	Header lipgloss.Style
	Footer lipgloss.Style
	Panel  lipgloss.Style

	// Component styles
	Button   lipgloss.Style
	Input    lipgloss.Style
	Progress lipgloss.Style
	List     lipgloss.Style

	// Status styles
	StatusOK          lipgloss.Style
	StatusWarning     lipgloss.Style
	StatusError       lipgloss.Style
	StatusOffline     lipgloss.Style
	StatusMaintenance lipgloss.Style
}

// NewStyles creates a new Styles instance with the given color scheme
func NewStyles(colors ColorScheme) *Styles {
	return &Styles{
		// Base styles
		Primary:   lipgloss.NewStyle().Foreground(colors.Primary).Bold(true),
		Secondary: lipgloss.NewStyle().Foreground(colors.Secondary),
		Success:   lipgloss.NewStyle().Foreground(colors.Success).Bold(true),
		Warning:   lipgloss.NewStyle().Foreground(colors.Warning).Bold(true),
		Error:     lipgloss.NewStyle().Foreground(colors.Error).Bold(true),
		Info:      lipgloss.NewStyle().Foreground(colors.Info),
		Muted:     lipgloss.NewStyle().Foreground(colors.Muted),

		// Layout styles
		Border: lipgloss.NewStyle().
			Border(lipgloss.RoundedBorder()).
			BorderForeground(colors.Border),
		Header: lipgloss.NewStyle().
			Foreground(colors.Primary).
			Bold(true).
			Align(lipgloss.Center).
			Padding(0, 1),
		Footer: lipgloss.NewStyle().
			Foreground(colors.Muted).
			Align(lipgloss.Center).
			Padding(0, 1),
		Panel: lipgloss.NewStyle().
			Border(lipgloss.RoundedBorder()).
			BorderForeground(colors.Border).
			Padding(1),

		// Component styles
		Button: lipgloss.NewStyle().
			Foreground(colors.Background).
			Background(colors.Primary).
			Padding(0, 1).
			Bold(true),
		Input: lipgloss.NewStyle().
			Border(lipgloss.RoundedBorder()).
			BorderForeground(colors.Border).
			Padding(0, 1),
		Progress: lipgloss.NewStyle().
			Foreground(colors.Success).
			Background(colors.Muted),
		List: lipgloss.NewStyle().
			Border(lipgloss.RoundedBorder()).
			BorderForeground(colors.Border).
			Padding(1),

		// Status styles
		StatusOK: lipgloss.NewStyle().
			Foreground(colors.Success).
			Bold(true),
		StatusWarning: lipgloss.NewStyle().
			Foreground(colors.Warning).
			Bold(true),
		StatusError: lipgloss.NewStyle().
			Foreground(colors.Error).
			Bold(true),
		StatusOffline: lipgloss.NewStyle().
			Foreground(colors.Muted),
		StatusMaintenance: lipgloss.NewStyle().
			Foreground(colors.Warning).
			Bold(true),
	}
}

// GetThemeStyles returns styles for the given theme
func GetThemeStyles(theme string) *Styles {
	switch theme {
	case "light":
		return NewStyles(LightTheme)
	case "dark", "auto":
		return NewStyles(DarkTheme)
	default:
		return NewStyles(DarkTheme)
	}
}

// FormatStatus formats a status string with appropriate styling
func (s *Styles) FormatStatus(status string) string {
	switch status {
	case "ok", "operational", "active", "online":
		return s.StatusOK.Render("✓ " + status)
	case "warning", "degraded", "maintenance":
		return s.StatusWarning.Render("⚠ " + status)
	case "error", "failed", "fault", "critical":
		return s.StatusError.Render("✗ " + status)
	case "offline", "disabled", "inactive":
		return s.StatusOffline.Render("○ " + status)
	default:
		return s.Muted.Render("? " + status)
	}
}

// FormatEquipment formats equipment information with appropriate styling
func (s *Styles) FormatEquipment(id, equipmentType, status string) string {
	statusFormatted := s.FormatStatus(status)
	return s.Primary.Render(id) + " " + s.Secondary.Render("["+equipmentType+"]") + " " + statusFormatted
}

// GetStatusStyle returns the lipgloss style for a status
func (s *Styles) GetStatusStyle(status string) lipgloss.Style {
	switch strings.ToLower(status) {
	case "ok", "operational", "active", "online":
		return s.StatusOK
	case "warning", "degraded", "maintenance":
		return s.StatusWarning
	case "error", "failed", "fault", "critical":
		return s.StatusError
	case "offline", "disabled", "inactive":
		return s.StatusOffline
	default:
		return s.StatusOffline
	}
}

// FormatCoordinates formats spatial coordinates with appropriate styling
func (s *Styles) FormatCoordinates(x, y, z float64) string {
	return s.Muted.Render("@" + fmt.Sprintf("(%.1f,%.1f,%.1f)", x, y, z))
}
