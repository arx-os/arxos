package commands

import (
	"context"
	"encoding/json"
	"fmt"
	"os"
	"strings"
	"text/tabwriter"

	"github.com/joelpate/arxos/internal/database"
	"github.com/joelpate/arxos/pkg/models"
)

// ExecuteQuery handles database queries
func ExecuteQuery(opts QueryOptions) error {
	ctx := context.Background()

	// Connect to database
	db, err := database.NewSQLiteDBFromPath("arxos.db")
	if err != nil {
		return fmt.Errorf("failed to connect to database: %w", err)
	}
	defer db.Close()

	// Build query
	var equipment []*models.Equipment

	if opts.BuildingID != "" {
		// Query specific building
		building, err := db.GetFloorPlan(ctx, opts.BuildingID)
		if err != nil {
			return fmt.Errorf("failed to load building: %w", err)
		}
		equipment = building.Equipment
	} else {
		// Query all buildings
		buildings, err := db.GetAllFloorPlans(ctx)
		if err != nil {
			return fmt.Errorf("failed to load buildings: %w", err)
		}

		for _, b := range buildings {
			equipment = append(equipment, b.Equipment...)
		}
	}

	// Apply filters
	filtered := filterEquipment(equipment, opts)

	// Output results
	switch opts.Format {
	case "json":
		return outputJSON(filtered, opts.OutputFile)
	case "csv":
		return outputCSV(filtered, opts.OutputFile)
	default:
		return outputTable(filtered, opts.OutputFile)
	}
}

func filterEquipment(equipment []*models.Equipment, opts QueryOptions) []*models.Equipment {
	var filtered []*models.Equipment

	for _, eq := range equipment {
		// Apply status filter
		if opts.Status != "" && !strings.EqualFold(eq.Status, opts.Status) {
			continue
		}

		// Apply type filter
		if opts.Type != "" && !strings.Contains(strings.ToLower(eq.Type), strings.ToLower(opts.Type)) {
			continue
		}

		// Apply floor filter (if location data available)
		if opts.Floor != -999 {
			// TODO: Add floor filtering when location data is available
		}

		filtered = append(filtered, eq)
	}

	return filtered
}

func outputTable(equipment []*models.Equipment, outputFile string) error {
	var w *tabwriter.Writer

	if outputFile != "" {
		file, err := os.Create(outputFile)
		if err != nil {
			return err
		}
		defer file.Close()
		w = tabwriter.NewWriter(file, 0, 0, 2, ' ', 0)
	} else {
		w = tabwriter.NewWriter(os.Stdout, 0, 0, 2, ' ', 0)
	}

	// Header
	fmt.Fprintln(w, "ID\tType\tStatus\tLocation")
	fmt.Fprintln(w, "---\t----\t------\t--------")

	// Data
	for _, eq := range equipment {
		location := "N/A"
		if eq.Location != nil {
			location = fmt.Sprintf("%.1f,%.1f", eq.Location.X, eq.Location.Y)
		}
		fmt.Fprintf(w, "%s\t%s\t%s\t%s\n", eq.ID, eq.Type, eq.Status, location)
	}

	return w.Flush()
}

func outputJSON(equipment []*models.Equipment, outputFile string) error {
	output := os.Stdout
	if outputFile != "" {
		var err error
		output, err = os.Create(outputFile)
		if err != nil {
			return err
		}
		defer output.Close()
	}

	encoder := json.NewEncoder(output)
	encoder.SetIndent("", "  ")
	return encoder.Encode(equipment)
}

func outputCSV(equipment []*models.Equipment, outputFile string) error {
	output := os.Stdout
	if outputFile != "" {
		var err error
		output, err = os.Create(outputFile)
		if err != nil {
			return err
		}
		defer output.Close()
	}

	// CSV header
	fmt.Fprintln(output, "ID,Type,Status,Location")

	// CSV data
	for _, eq := range equipment {
		location := "N/A"
		if eq.Location != nil {
			location = fmt.Sprintf("%.1f,%.1f", eq.Location.X, eq.Location.Y)
		}
		fmt.Fprintf(output, "%s,%s,%s,%s\n", eq.ID, eq.Type, eq.Status, location)
	}

	return nil
}