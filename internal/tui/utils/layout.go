package utils

import (
	"fmt"
	"strings"

	"github.com/charmbracelet/lipgloss"
)

// Layout provides utilities for arranging TUI components
type Layout struct {
	width  int
	height int
	styles *Styles
}

// NewLayout creates a new layout instance
func NewLayout(width, height int, styles *Styles) *Layout {
	return &Layout{
		width:  width,
		height: height,
		styles: styles,
	}
}

// Header creates a styled header with title and status
func (l *Layout) Header(title, status string) string {
	titleStyled := l.styles.Header.Render(title)
	statusStyled := l.styles.Info.Render(status)

	// Calculate padding to center the content
	padding := l.width - len(title) - len(status) - 4
	if padding < 0 {
		padding = 0
	}

	spacer := strings.Repeat(" ", padding)
	return fmt.Sprintf("%s%s%s", titleStyled, spacer, statusStyled)
}

// Footer creates a styled footer with help text
func (l *Layout) Footer(helpText string) string {
	return l.styles.Footer.Render(helpText)
}

// Panel creates a bordered panel with content
func (l *Layout) Panel(title, content string) string {
	if title != "" {
		titleStyled := l.styles.Header.Render(title)
		return l.styles.Panel.Render(titleStyled + "\n" + content)
	}
	return l.styles.Panel.Render(content)
}

// TwoColumn creates a two-column layout
func (l *Layout) TwoColumn(left, right string) string {
	// Calculate column widths
	leftWidth := (l.width - 4) / 2 // Account for padding and border
	rightWidth := l.width - leftWidth - 4

	// Truncate content to fit
	leftTruncated := l.truncateString(left, leftWidth)
	rightTruncated := l.truncateString(right, rightWidth)

	// Create columns with borders
	leftPanel := l.styles.Panel.Render(leftTruncated)
	rightPanel := l.styles.Panel.Render(rightTruncated)

	return lipgloss.JoinHorizontal(lipgloss.Top, leftPanel, rightPanel)
}

// ThreeColumn creates a three-column layout
func (l *Layout) ThreeColumn(left, center, right string) string {
	// Calculate column widths
	columnWidth := (l.width - 8) / 3 // Account for padding and borders

	// Truncate content to fit
	leftTruncated := l.truncateString(left, columnWidth)
	centerTruncated := l.truncateString(center, columnWidth)
	rightTruncated := l.truncateString(right, columnWidth)

	// Create columns with borders
	leftPanel := l.styles.Panel.Render(leftTruncated)
	centerPanel := l.styles.Panel.Render(centerTruncated)
	rightPanel := l.styles.Panel.Render(rightTruncated)

	return lipgloss.JoinHorizontal(lipgloss.Top, leftPanel, centerPanel, rightPanel)
}

// ProgressBar creates a progress bar with percentage
func (l *Layout) ProgressBar(current, total int, label string) string {
	if total == 0 {
		return l.styles.Muted.Render(label + ": N/A")
	}

	percentage := float64(current) / float64(total)
	barWidth := l.width - len(label) - 10 // Account for label and percentage text

	if barWidth < 10 {
		barWidth = 10
	}

	filled := int(percentage * float64(barWidth))
	empty := barWidth - filled

	bar := strings.Repeat("█", filled) + strings.Repeat("░", empty)
	percentageText := fmt.Sprintf("%.1f%%", percentage*100)

	barStyled := l.styles.Progress.Render(bar)
	return fmt.Sprintf("%s: %s %s", label, barStyled, percentageText)
}

// StatusGrid creates a grid of status indicators
func (l *Layout) StatusGrid(items []StatusItem) string {
	if len(items) == 0 {
		return l.styles.Muted.Render("No items to display")
	}

	var rows []string
	itemsPerRow := l.width / 20 // Approximate items per row

	for i := 0; i < len(items); i += itemsPerRow {
		var rowItems []string
		for j := i; j < i+itemsPerRow && j < len(items); j++ {
			item := items[j]
			statusStyled := l.styles.FormatStatus(item.Status)
			itemText := fmt.Sprintf("%s %s", item.Label, statusStyled)
			rowItems = append(rowItems, itemText)
		}
		rows = append(rows, strings.Join(rowItems, "  "))
	}

	return strings.Join(rows, "\n")
}

// StatusItem represents an item in a status grid
type StatusItem struct {
	Label  string
	Status string
}

// truncateString truncates a string to fit within the specified width
func (l *Layout) truncateString(s string, width int) string {
	if len(s) <= width {
		return s
	}

	if width <= 3 {
		return "..."
	}

	return s[:width-3] + "..."
}

// WrapText wraps text to fit within the specified width
func (l *Layout) WrapText(text string, width int) string {
	words := strings.Fields(text)
	if len(words) == 0 {
		return ""
	}

	var lines []string
	var currentLine string

	for _, word := range words {
		if len(currentLine)+len(word)+1 <= width {
			if currentLine != "" {
				currentLine += " " + word
			} else {
				currentLine = word
			}
		} else {
			if currentLine != "" {
				lines = append(lines, currentLine)
			}
			currentLine = word
		}
	}

	if currentLine != "" {
		lines = append(lines, currentLine)
	}

	return strings.Join(lines, "\n")
}

// Center centers text within the specified width
func (l *Layout) Center(text string, width int) string {
	if len(text) >= width {
		return text
	}

	padding := (width - len(text)) / 2
	return strings.Repeat(" ", padding) + text + strings.Repeat(" ", width-len(text)-padding)
}
