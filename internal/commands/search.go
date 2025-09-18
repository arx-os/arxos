package commands

import (
	"context"
	"encoding/json"
	"fmt"
	"os"
	"strings"
	"text/tabwriter"

	"github.com/arx-os/arxos/internal/common/logger"
	"github.com/arx-os/arxos/internal/database"
	"github.com/arx-os/arxos/pkg/models"
)

// SearchOptions defines options for search command
type SearchOptions struct {
	Query      string
	Type       string // "building", "equipment", "room", "all"
	Format     string // "json", "table", "csv"
	OutputFile string
}

// ExecuteSearch performs database search
func ExecuteSearch(opts SearchOptions) error {
	ctx := context.Background()

	// Connect to database
	db, err := database.NewSQLiteDBFromPath("arxos.db")
	if err != nil {
		return fmt.Errorf("failed to connect to database: %w", err)
	}
	defer db.Close()

	// Perform search based on type
	var results interface{}
	switch opts.Type {
	case "building":
		results, err = searchBuildings(ctx, db, opts.Query)
	case "equipment":
		results, err = searchEquipment(ctx, db, opts.Query)
	case "room":
		results, err = searchRooms(ctx, db, opts.Query)
	case "all":
		results, err = searchAll(ctx, db, opts.Query)
	default:
		return fmt.Errorf("invalid search type: %s", opts.Type)
	}

	if err != nil {
		return fmt.Errorf("search failed: %w", err)
	}

	// Format and output results
	return outputSearchResults(results, opts)
}

func searchBuildings(ctx context.Context, db *database.SQLiteDB, query string) ([]*models.FloorPlan, error) {
	all, err := db.GetAllFloorPlans(ctx)
	if err != nil {
		return nil, err
	}

	var results []*models.FloorPlan
	queryLower := strings.ToLower(query)

	for _, plan := range all {
		if strings.Contains(strings.ToLower(plan.Name), queryLower) ||
			strings.Contains(strings.ToLower(plan.ID), queryLower) ||
			strings.Contains(strings.ToLower(plan.Building), queryLower) ||
			strings.Contains(strings.ToLower(plan.Description), queryLower) {
			results = append(results, plan)
		}
	}

	logger.Info("Found %d buildings matching '%s'", len(results), query)
	return results, nil
}

func searchEquipment(ctx context.Context, db *database.SQLiteDB, query string) ([]*models.Equipment, error) {
	// Get all buildings first
	buildings, err := db.GetAllFloorPlans(ctx)
	if err != nil {
		return nil, err
	}

	var results []*models.Equipment
	queryLower := strings.ToLower(query)

	for _, building := range buildings {
		for _, eq := range building.Equipment {
			if strings.Contains(strings.ToLower(eq.ID), queryLower) ||
				strings.Contains(strings.ToLower(eq.Name), queryLower) ||
				strings.Contains(strings.ToLower(eq.Type), queryLower) ||
				strings.Contains(strings.ToLower(string(eq.Status)), queryLower) {
				results = append(results, eq)
			}
		}
	}

	logger.Info("Found %d equipment items matching '%s'", len(results), query)
	return results, nil
}

func searchRooms(ctx context.Context, db *database.SQLiteDB, query string) ([]*models.Room, error) {
	// Get all buildings first
	buildings, err := db.GetAllFloorPlans(ctx)
	if err != nil {
		return nil, err
	}

	var results []*models.Room
	queryLower := strings.ToLower(query)

	for _, building := range buildings {
		for _, room := range building.Rooms {
			if strings.Contains(strings.ToLower(room.ID), queryLower) ||
				strings.Contains(strings.ToLower(room.Name), queryLower) {
				results = append(results, room)
			}
		}
	}

	logger.Info("Found %d rooms matching '%s'", len(results), query)
	return results, nil
}

type SearchResults struct {
	Buildings []*models.FloorPlan `json:"buildings,omitempty"`
	Equipment []*models.Equipment `json:"equipment,omitempty"`
	Rooms     []*models.Room      `json:"rooms,omitempty"`
}

func searchAll(ctx context.Context, db *database.SQLiteDB, query string) (*SearchResults, error) {
	results := &SearchResults{}

	// Search buildings
	buildings, err := searchBuildings(ctx, db, query)
	if err != nil {
		return nil, err
	}
	results.Buildings = buildings

	// Search equipment
	equipment, err := searchEquipment(ctx, db, query)
	if err != nil {
		return nil, err
	}
	results.Equipment = equipment

	// Search rooms
	rooms, err := searchRooms(ctx, db, query)
	if err != nil {
		return nil, err
	}
	results.Rooms = rooms

	return results, nil
}

func outputSearchResults(results interface{}, opts SearchOptions) error {
	var output *os.File
	if opts.OutputFile != "" {
		file, err := os.Create(opts.OutputFile)
		if err != nil {
			return fmt.Errorf("failed to create output file: %w", err)
		}
		defer file.Close()
		output = file
	} else {
		output = os.Stdout
	}

	switch opts.Format {
	case "json":
		encoder := json.NewEncoder(output)
		encoder.SetIndent("", "  ")
		return encoder.Encode(results)

	case "table":
		w := tabwriter.NewWriter(output, 0, 0, 2, ' ', 0)
		defer w.Flush()

		switch r := results.(type) {
		case []*models.FloorPlan:
			fmt.Fprintln(w, "ID\tName\tBuilding\tLevel\tEquipment\tRooms")
			for _, b := range r {
				fmt.Fprintf(w, "%s\t%s\t%s\t%d\t%d\t%d\n",
					b.ID, b.Name, b.Building, b.Level,
					len(b.Equipment), len(b.Rooms))
			}

		case []*models.Equipment:
			fmt.Fprintln(w, "ID\tName\tType\tStatus")
			for _, e := range r {
				fmt.Fprintf(w, "%s\t%s\t%s\t%s\n",
					e.ID, e.Name, e.Type, e.Status)
			}

		case []*models.Room:
			fmt.Fprintln(w, "ID\tName")
			for _, room := range r {
				fmt.Fprintf(w, "%s\t%s\n",
					room.ID, room.Name)
			}

		case *SearchResults:
			fmt.Fprintf(w, "=== Search Results for '%s' ===\n", opts.Query)
			fmt.Fprintf(w, "Buildings: %d\n", len(r.Buildings))
			fmt.Fprintf(w, "Equipment: %d\n", len(r.Equipment))
			fmt.Fprintf(w, "Rooms: %d\n", len(r.Rooms))

			if len(r.Buildings) > 0 {
				fmt.Fprintln(w, "\n--- Buildings ---")
				fmt.Fprintln(w, "ID\tName")
				for _, b := range r.Buildings {
					fmt.Fprintf(w, "%s\t%s\n", b.ID, b.Name)
				}
			}

			if len(r.Equipment) > 0 {
				fmt.Fprintln(w, "\n--- Equipment ---")
				fmt.Fprintln(w, "ID\tType\tStatus")
				for _, e := range r.Equipment {
					fmt.Fprintf(w, "%s\t%s\t%s\n", e.ID, e.Type, e.Status)
				}
			}

			if len(r.Rooms) > 0 {
				fmt.Fprintln(w, "\n--- Rooms ---")
				fmt.Fprintln(w, "ID\tName")
				for _, room := range r.Rooms {
					fmt.Fprintf(w, "%s\t%s\n", room.ID, room.Name)
				}
			}
		}

	case "csv":
		// Simple CSV output
		switch r := results.(type) {
		case []*models.Equipment:
			fmt.Fprintln(output, "ID,Name,Type,Status")
			for _, e := range r {
				fmt.Fprintf(output, "%s,%s,%s,%s\n",
					e.ID, e.Name, e.Type, e.Status)
			}
		}

	default:
		return fmt.Errorf("unsupported format: %s", opts.Format)
	}

	return nil
}
