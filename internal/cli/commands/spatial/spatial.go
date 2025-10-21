package spatial

import (
	"context"
	"fmt"
	"os"
	"text/tabwriter"

	"github.com/arx-os/arxos/internal/infrastructure/postgis"
	"github.com/jmoiron/sqlx"
	"github.com/spf13/cobra"
)

// SpatialServiceProvider provides access to spatial services
type SpatialServiceProvider interface {
	GetPostGIS() *postgis.PostGIS
}

// CreateSpatialCommands creates spatial query commands
func CreateSpatialCommands(serviceContext any) *cobra.Command {
	spatialCmd := &cobra.Command{
		Use:   "spatial",
		Short: "Spatial queries and operations",
		Long:  `Find equipment and buildings using spatial queries (nearby, within bounds, etc.)`,
	}

	spatialCmd.AddCommand(createSpatialNearbyCommand(serviceContext))
	spatialCmd.AddCommand(createSpatialWithinCommand(serviceContext))
	spatialCmd.AddCommand(createSpatialDistanceCommand(serviceContext))

	return spatialCmd
}

// Helper function to get spatial repo from context
func getSpatialRepo(serviceContext any) (*postgis.SpatialRepository, error) {
	sc, ok := serviceContext.(SpatialServiceProvider)
	if !ok {
		return nil, fmt.Errorf("service context is not available")
	}
	postgisClient := sc.GetPostGIS()
	sqlxDB := sqlx.NewDb(postgisClient.GetDB(), "postgres")
	return postgis.NewSpatialRepository(sqlxDB, nil), nil
}

// createSpatialNearbyCommand creates the spatial nearby command
func createSpatialNearbyCommand(serviceContext any) *cobra.Command {
	var (
		lat        float64
		lon        float64
		radius     float64
		buildingID string
		entityType string
	)

	cmd := &cobra.Command{
		Use:   "nearby",
		Short: "Find entities near a location",
		Long:  "Find buildings or equipment within a radius of GPS coordinates",
		Example: `  # Find equipment within 100 meters
  arx spatial nearby --lat 37.7749 --lon -122.4194 --radius 100 --type equipment

  # Find buildings within 1km
  arx spatial nearby --lat 37.7749 --lon -122.4194 --radius 1000 --type building

  # Find equipment in a specific building
  arx spatial nearby --lat 37.7749 --lon -122.4194 --radius 50 --type equipment --building abc123`,
		RunE: func(cmd *cobra.Command, args []string) error {
			ctx := context.Background()

			// Validate required fields
			if lat == 0 && lon == 0 {
				return fmt.Errorf("latitude and longitude are required (--lat, --lon)")
			}
			if radius <= 0 {
				return fmt.Errorf("radius must be greater than 0 (--radius)")
			}
			if entityType == "" {
				entityType = "equipment" // Default to equipment
			}

			// Get spatial repo using helper
			spatialRepo, err := getSpatialRepo(serviceContext)
			if err != nil {
				return err
			}

			if entityType == "equipment" {
				// Find nearby equipment
				equipment, err := spatialRepo.FindEquipmentNearby(ctx, lat, lon, radius, buildingID)
				if err != nil {
					return fmt.Errorf("failed to find nearby equipment: %w", err)
				}

				if len(equipment) == 0 {
					fmt.Printf("No equipment found within %.0fm of (%.6f, %.6f)\n", radius, lat, lon)
					return nil
				}

				// Print results
				w := tabwriter.NewWriter(os.Stdout, 0, 0, 3, ' ', 0)
				fmt.Fprintf(w, "NAME\tTYPE\tSTATUS\tLOCATION\n")
				fmt.Fprintf(w, "----\t----\t------\t--------\n")

				for _, eq := range equipment {
					locationStr := "N/A"
					if eq.Location != nil {
						locationStr = fmt.Sprintf("(%.2f, %.2f, %.2f)", eq.Location.X, eq.Location.Y, eq.Location.Z)
					}
					fmt.Fprintf(w, "%s\t%s\t%s\t%s\n",
						eq.Name,
						eq.Type,
						eq.Status,
						locationStr,
					)
				}
				w.Flush()

				fmt.Printf("\n%d equipment item(s) found within %.0fm\n", len(equipment), radius)

			} else if entityType == "building" {
				// Find nearby buildings
				buildings, err := spatialRepo.FindBuildingsNearby(ctx, lat, lon, radius)
				if err != nil {
					return fmt.Errorf("failed to find nearby buildings: %w", err)
				}

				if len(buildings) == 0 {
					fmt.Printf("No buildings found within %.0fm of (%.6f, %.6f)\n", radius, lat, lon)
					return nil
				}

				// Print results
				w := tabwriter.NewWriter(os.Stdout, 0, 0, 3, ' ', 0)
				fmt.Fprintf(w, "NAME\tADDRESS\tCOORDINATES\n")
				fmt.Fprintf(w, "----\t-------\t-----------\n")

				for _, b := range buildings {
					coordStr := "N/A"
					if b.Coordinates != nil {
						coordStr = fmt.Sprintf("%.6f°N, %.6f°E", b.Coordinates.Y, b.Coordinates.X)
					}
					fmt.Fprintf(w, "%s\t%s\t%s\n",
						b.Name,
						b.Address,
						coordStr,
					)
				}
				w.Flush()

				fmt.Printf("\n%d building(s) found within %.0fm\n", len(buildings), radius)
			}

			return nil
		},
	}

	// Add flags
	cmd.Flags().Float64Var(&lat, "lat", 0, "Latitude (required)")
	cmd.Flags().Float64Var(&lon, "lon", 0, "Longitude (required)")
	cmd.Flags().Float64Var(&radius, "radius", 100, "Radius in meters")
	cmd.Flags().StringVar(&buildingID, "building", "", "Filter by building ID (equipment only)")
	cmd.Flags().StringVar(&entityType, "type", "equipment", "Entity type (equipment, building)")

	cmd.MarkFlagRequired("lat")
	cmd.MarkFlagRequired("lon")

	return cmd
}

// createSpatialWithinCommand creates the spatial within bounds command
func createSpatialWithinCommand(serviceContext any) *cobra.Command {
	var (
		minLat float64
		minLon float64
		maxLat float64
		maxLon float64
	)

	cmd := &cobra.Command{
		Use:   "within",
		Short: "Find equipment within bounding box",
		Long:  "Find equipment within a rectangular bounding box defined by min/max coordinates",
		Example: `  # Find equipment in San Francisco area
  arx spatial within \
    --min-lat 37.70 --min-lon -122.50 \
    --max-lat 37.80 --max-lon -122.35`,
		RunE: func(cmd *cobra.Command, args []string) error {
			ctx := context.Background()

			// Validate required fields
			if minLat == 0 || minLon == 0 || maxLat == 0 || maxLon == 0 {
				return fmt.Errorf("all bounding box coordinates are required (--min-lat, --min-lon, --max-lat, --max-lon)")
			}

			// Validate bounds
			if minLat >= maxLat {
				return fmt.Errorf("min-lat must be less than max-lat")
			}
			if minLon >= maxLon {
				return fmt.Errorf("min-lon must be less than max-lon")
			}

			// Get spatial repo using helper
			spatialRepo, err := getSpatialRepo(serviceContext)
			if err != nil {
				return err
			}

			// Find equipment within bounds
			equipment, err := spatialRepo.FindEquipmentWithinBounds(ctx, minLat, minLon, maxLat, maxLon)
			if err != nil {
				return fmt.Errorf("failed to find equipment within bounds: %w", err)
			}

			if len(equipment) == 0 {
				fmt.Printf("No equipment found within bounds\n")
				return nil
			}

			// Print results
			w := tabwriter.NewWriter(os.Stdout, 0, 0, 3, ' ', 0)
			fmt.Fprintf(w, "NAME\tTYPE\tSTATUS\tLOCATION\tBUILDING\n")
			fmt.Fprintf(w, "----\t----\t------\t--------\t--------\n")

			for _, eq := range equipment {
				locationStr := "N/A"
				if eq.Location != nil {
					locationStr = fmt.Sprintf("(%.2f, %.2f, %.2f)", eq.Location.X, eq.Location.Y, eq.Location.Z)
				}
				fmt.Fprintf(w, "%s\t%s\t%s\t%s\t%s\n",
					eq.Name,
					eq.Type,
					eq.Status,
					locationStr,
					eq.BuildingID.String()[:8]+"...",
				)
			}
			w.Flush()

			fmt.Printf("\n%d equipment item(s) found within bounding box\n", len(equipment))

			return nil
		},
	}

	// Add flags
	cmd.Flags().Float64Var(&minLat, "min-lat", 0, "Minimum latitude (required)")
	cmd.Flags().Float64Var(&minLon, "min-lon", 0, "Minimum longitude (required)")
	cmd.Flags().Float64Var(&maxLat, "max-lat", 0, "Maximum latitude (required)")
	cmd.Flags().Float64Var(&maxLon, "max-lon", 0, "Maximum longitude (required)")

	cmd.MarkFlagRequired("min-lat")
	cmd.MarkFlagRequired("min-lon")
	cmd.MarkFlagRequired("max-lat")
	cmd.MarkFlagRequired("max-lon")

	return cmd
}

// createSpatialDistanceCommand creates the distance calculation command
func createSpatialDistanceCommand(serviceContext any) *cobra.Command {
	var (
		lat1 float64
		lon1 float64
		lat2 float64
		lon2 float64
	)

	cmd := &cobra.Command{
		Use:   "distance",
		Short: "Calculate distance between two points",
		Long:  "Calculate the distance in meters between two GPS coordinates",
		Example: `  # Calculate distance between two locations
  arx spatial distance --lat1 37.7749 --lon1 -122.4194 --lat2 37.7849 --lon2 -122.4094`,
		RunE: func(cmd *cobra.Command, args []string) error {
			ctx := context.Background()

			// Validate required fields
			if lat1 == 0 || lon1 == 0 || lat2 == 0 || lon2 == 0 {
				return fmt.Errorf("all coordinates are required (--lat1, --lon1, --lat2, --lon2)")
			}

			// Get spatial repo using helper
			spatialRepo, err := getSpatialRepo(serviceContext)
			if err != nil {
				return err
			}

			// Calculate distance
			distance, err := spatialRepo.CalculateDistance(ctx, lat1, lon1, lat2, lon2)
			if err != nil {
				return fmt.Errorf("failed to calculate distance: %w", err)
			}

			// Print result
			fmt.Printf("Distance Calculation:\n\n")
			fmt.Printf("   Point 1:  %.6f°N, %.6f°E\n", lat1, lon1)
			fmt.Printf("   Point 2:  %.6f°N, %.6f°E\n", lat2, lon2)
			fmt.Printf("   Distance: %.2f meters\n", distance)
			fmt.Printf("            %.2f kilometers\n", distance/1000)
			fmt.Printf("            %.2f miles\n", distance*0.000621371)
			fmt.Printf("\n")

			return nil
		},
	}

	// Add flags
	cmd.Flags().Float64Var(&lat1, "lat1", 0, "First point latitude (required)")
	cmd.Flags().Float64Var(&lon1, "lon1", 0, "First point longitude (required)")
	cmd.Flags().Float64Var(&lat2, "lat2", 0, "Second point latitude (required)")
	cmd.Flags().Float64Var(&lon2, "lon2", 0, "Second point longitude (required)")

	cmd.MarkFlagRequired("lat1")
	cmd.MarkFlagRequired("lon1")
	cmd.MarkFlagRequired("lat2")
	cmd.MarkFlagRequired("lon2")

	return cmd
}
