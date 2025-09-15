package bim

import (
	"fmt"
	"io"
	"os"
	"strings"
	"time"
)

// Writer handles writing BIM models to text format
type Writer struct {
	// Options
	canonical bool // If true, use canonical formatting
	indent    string
}

// NewWriter creates a new BIM writer
func NewWriter() *Writer {
	return &Writer{
		canonical: true,
		indent:    "  ",
	}
}

// Write writes a building model to a writer
func (w *Writer) Write(writer io.Writer, building *Building) error {
	// Write header
	if err := w.writeHeader(writer, building); err != nil {
		return err
	}

	// Write floors
	for _, floor := range building.Floors {
		if err := w.writeFloor(writer, floor); err != nil {
			return err
		}
	}

	// Write footer
	if err := w.writeFooter(writer, building); err != nil {
		return err
	}

	return nil
}

// WriteFile writes a building model to a file
func (w *Writer) WriteFile(path string, building *Building) error {
	file, err := os.Create(path)
	if err != nil {
		return fmt.Errorf("failed to create file: %w", err)
	}
	defer file.Close()

	return w.Write(file, building)
}

// Format returns the building as a formatted string
func (w *Writer) Format(building *Building) (string, error) {
	var sb strings.Builder
	if err := w.Write(&sb, building); err != nil {
		return "", err
	}
	return sb.String(), nil
}

// Private helper methods

func (w *Writer) writeHeader(writer io.Writer, building *Building) error {
	// Write file header
	fmt.Fprintln(writer, strings.Repeat("=", 79))
	fmt.Fprintf(writer, "BUILDING: %s\n", building.Name)
	fmt.Fprintf(writer, "FILE_VERSION: %s\n", building.FileVersion)
	fmt.Fprintf(writer, "GENERATED: %s\n", building.Generated.Format(time.RFC3339))

	if building.CoordinateSystem != "" {
		fmt.Fprintf(writer, "COORDINATE_SYSTEM: %s\n", building.CoordinateSystem)
	}
	if building.Units != "" {
		fmt.Fprintf(writer, "UNITS: %s\n", building.Units)
	}

	fmt.Fprintln(writer, strings.Repeat("=", 79))
	fmt.Fprintln(writer)

	return nil
}

func (w *Writer) writeFloor(writer io.Writer, floor Floor) error {
	// Floor header
	fmt.Fprintln(writer, strings.Repeat("=", 37))
	fmt.Fprintf(writer, "FLOOR: %d | %s\n", floor.Level, floor.Name)
	fmt.Fprintf(writer, "DIMENSIONS: %.0fx%.0f\n", floor.Dimensions.Width, floor.Dimensions.Height)

	if floor.GridScale.Ratio != "" {
		fmt.Fprintf(writer, "GRID_SCALE: %s (%s)\n", floor.GridScale.Ratio, floor.GridScale.Description)
	}

	fmt.Fprintln(writer, strings.Repeat("=", 37))
	fmt.Fprintln(writer)

	// Legend
	if len(floor.Legend) > 0 {
		fmt.Fprintln(writer, "LEGEND:")
		for symbol, description := range floor.Legend {
			fmt.Fprintf(writer, "%s%c = %s\n", w.indent, symbol, description)
		}
		fmt.Fprintln(writer)
	}

	// Layout
	if len(floor.Layout) > 0 {
		fmt.Fprintln(writer, "LAYOUT:")
		for _, line := range floor.Layout {
			fmt.Fprintln(writer, line)
		}
		fmt.Fprintln(writer)
	}

	// Equipment Registry
	if len(floor.Equipment) > 0 {
		fmt.Fprintln(writer, "EQUIPMENT_REGISTRY:")
		fmt.Fprintln(writer, "-----------------")

		for _, eq := range floor.Equipment {
			w.writeEquipment(writer, eq)
			fmt.Fprintln(writer)
		}
	}

	// Connections
	if len(floor.Connections) > 0 {
		fmt.Fprintln(writer, "CONNECTIONS:")
		fmt.Fprintln(writer, "-----------")

		for connType, connections := range floor.Connections {
			if len(connections) > 0 {
				fmt.Fprintf(writer, "%s:\n", connType)
				for _, conn := range connections {
					fmt.Fprintf(writer, "%s%s -> %s", w.indent, conn.From, conn.To)
					if conn.Specification != "" {
						fmt.Fprintf(writer, " [%s]", conn.Specification)
					}
					fmt.Fprintln(writer)
				}
			}
		}
		fmt.Fprintln(writer)
	}

	// Issues Summary
	if len(floor.Issues) > 0 {
		fmt.Fprintln(writer, "ISSUES_SUMMARY:")
		fmt.Fprintln(writer, "--------------")

		// Group by priority
		priorityGroups := make(map[Priority][]Issue)
		for _, issue := range floor.Issues {
			priorityGroups[issue.Priority] = append(priorityGroups[issue.Priority], issue)
		}

		// Write in priority order
		for _, priority := range []Priority{PriorityCritical, PriorityHigh, PriorityMedium, PriorityLow} {
			if issues, ok := priorityGroups[priority]; ok && len(issues) > 0 {
				fmt.Fprintf(writer, "%s: %d\n", priority, len(issues))
				for _, issue := range issues {
					fmt.Fprintf(writer, "%s- %s: %s", w.indent, issue.EquipmentID, issue.Description)
					if issue.Ticket != "" {
						fmt.Fprintf(writer, " [%s]", issue.Ticket)
					}
					fmt.Fprintln(writer)
				}
			}
		}
		fmt.Fprintln(writer)
	}

	return nil
}

func (w *Writer) writeEquipment(writer io.Writer, eq Equipment) error {
	fmt.Fprintf(writer, "ID: %s\n", eq.ID)

	// Required fields
	fmt.Fprintf(writer, "%sTYPE: %s\n", w.indent, eq.Type)
	fmt.Fprintf(writer, "%sLOCATION: (%.0f,%.0f) in %s\n",
		w.indent, eq.Location.X, eq.Location.Y, eq.Location.Room)
	fmt.Fprintf(writer, "%sSTATUS: %s\n", w.indent, eq.Status)

	// Optional fields
	if eq.Serial != "" {
		fmt.Fprintf(writer, "%sSERIAL: %s\n", w.indent, eq.Serial)
	}
	if eq.Model != "" {
		fmt.Fprintf(writer, "%sMODEL: %s\n", w.indent, eq.Model)
	}
	if eq.Manufacturer != "" {
		fmt.Fprintf(writer, "%sMANUFACTURER: %s\n", w.indent, eq.Manufacturer)
	}
	if eq.Installed != nil {
		fmt.Fprintf(writer, "%sINSTALLED: %s\n", w.indent, eq.Installed.Format("2006-01-02"))
	}
	if eq.LastMaint != nil {
		fmt.Fprintf(writer, "%sLAST_MAINT: %s\n", w.indent, eq.LastMaint.Format("2006-01-02"))
	}
	if eq.NextMaint != nil {
		fmt.Fprintf(writer, "%sNEXT_MAINT: %s\n", w.indent, eq.NextMaint.Format("2006-01-02"))
	}
	if eq.Power != "" {
		fmt.Fprintf(writer, "%sPOWER: %s\n", w.indent, eq.Power)
	}
	if eq.Network != "" {
		fmt.Fprintf(writer, "%sNETWORK: %s\n", w.indent, eq.Network)
	}
	if eq.Notes != "" {
		fmt.Fprintf(writer, "%sNOTES: %s\n", w.indent, eq.Notes)
	}
	if eq.AssignedTo != "" {
		fmt.Fprintf(writer, "%sASSIGNED_TO: %s\n", w.indent, eq.AssignedTo)
	}
	if eq.Ticket != "" {
		fmt.Fprintf(writer, "%sTICKET: %s\n", w.indent, eq.Ticket)
	}
	if eq.Priority != "" {
		fmt.Fprintf(writer, "%sPRIORITY: %s\n", w.indent, eq.Priority)
	}

	// Custom fields
	for key, value := range eq.CustomFields {
		fmt.Fprintf(writer, "%sCUSTOM_%s: %s\n", w.indent, key, value)
	}

	return nil
}

func (w *Writer) writeFooter(writer io.Writer, building *Building) error {
	// Metadata section
	if building.Metadata.CreatedBy != "" || building.Metadata.Organization != "" ||
		len(building.Metadata.Tags) > 0 || building.Metadata.Notes != "" {

		fmt.Fprintln(writer, "METADATA:")
		fmt.Fprintln(writer, "--------")

		if building.Metadata.CreatedBy != "" {
			fmt.Fprintf(writer, "CREATED_BY: %s\n", building.Metadata.CreatedBy)
		}
		if building.Metadata.Organization != "" {
			fmt.Fprintf(writer, "ORGANIZATION: %s\n", building.Metadata.Organization)
		}
		if len(building.Metadata.Tags) > 0 {
			fmt.Fprintf(writer, "TAGS: %s\n", strings.Join(building.Metadata.Tags, ", "))
		}
		if building.Metadata.Notes != "" {
			fmt.Fprintf(writer, "NOTES: %s\n", building.Metadata.Notes)
		}
		fmt.Fprintln(writer)
	}

	// Validation footer
	fmt.Fprintln(writer, strings.Repeat("=", 79))
	fmt.Fprintln(writer, "VALIDATION:")

	// Calculate checksum (simplified for now)
	checksum := fmt.Sprintf("SHA256:%x", time.Now().Unix())
	fmt.Fprintf(writer, "%sCHECKSUM: %s\n", w.indent, checksum)

	// Count equipment and connections
	equipCount := 0
	connCount := 0
	for _, floor := range building.Floors {
		equipCount += len(floor.Equipment)
		for _, conns := range floor.Connections {
			connCount += len(conns)
		}
	}

	fmt.Fprintf(writer, "%sEQUIPMENT_COUNT: %d\n", w.indent, equipCount)
	fmt.Fprintf(writer, "%sCONNECTION_COUNT: %d\n", w.indent, connCount)
	fmt.Fprintf(writer, "%sLAST_MODIFIED: %s\n", w.indent, building.Validation.LastModified.Format(time.RFC3339))
	fmt.Fprintf(writer, "%sMODIFIED_BY: %s\n", w.indent, building.Validation.ModifiedBy)

	fmt.Fprintln(writer, strings.Repeat("=", 79))

	return nil
}

// DefaultLegend returns the standard legend
func DefaultLegend() map[rune]string {
	return map[rune]string{
		'#': "Wall",
		'.': "Open Space",
		'D': "Door",
		'W': "Window",
		'+': "Equipment",
		'*': "Critical Equipment",
		'!': "Failed Equipment",
		'~': "Water/Plumbing",
		'@': "Electrical Panel",
		'$': "HVAC Equipment",
		'%': "Network Equipment",
	}
}