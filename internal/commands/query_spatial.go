package commands

import (
	"context"
	"encoding/json"
	"fmt"
	"os"
	"strconv"
	"strings"

	"github.com/arx-os/arxos/internal/common/logger"
	"github.com/arx-os/arxos/internal/database"
	"github.com/arx-os/arxos/internal/spatial"
)

// ExecuteSpatialQuery executes spatial queries using PostGIS
func ExecuteSpatialQuery(opts QueryOptions) error {
	ctx := context.Background()

	// Check if any spatial parameters are provided
	if !hasSpatialParams(opts) {
		return fmt.Errorf("no spatial parameters provided")
	}

	// Create database configuration
	dbConfig := database.NewConfig("arxos.db")

	// Try to create a PostGIS hybrid database
	pgConfig := database.PostGISConfig{
		Host:     getEnvOrDefault("POSTGIS_HOST", "localhost"),
		Port:     5432,
		Database: getEnvOrDefault("POSTGIS_DB", "arxos"),
		User:     getEnvOrDefault("POSTGIS_USER", "postgres"),
		Password: getEnvOrDefault("POSTGIS_PASSWORD", ""),
		SSLMode:  "prefer",
	}

	hybridDB := database.NewPostGISHybridDB(pgConfig, dbConfig)
	if err := hybridDB.Connect(ctx, "arxos.db"); err != nil {
		logger.Warn("Failed to connect to PostGIS, spatial queries unavailable: %v", err)
		return fmt.Errorf("spatial queries require PostGIS connection")
	}
	defer hybridDB.Close()

	// Check if spatial support is available
	if !hybridDB.HasSpatialSupport() {
		return fmt.Errorf("spatial queries require PostGIS to be available")
	}

	// Get spatial database
	spatialDB, err := hybridDB.GetSpatialDB()
	if err != nil {
		return fmt.Errorf("failed to get spatial database: %w", err)
	}

	// Execute the appropriate spatial query
	var results []*database.SpatialEquipment

	if opts.Near != "" && opts.Radius > 0 {
		// Proximity query
		center, err := parseCoordinates(opts.Near)
		if err != nil {
			return fmt.Errorf("invalid coordinates for --near: %w", err)
		}

		logger.Info("Executing proximity query: center=%v, radius=%.2f", center, opts.Radius)
		results, err = spatialDB.QueryBySpatialProximity(center, opts.Radius)
		if err != nil {
			return fmt.Errorf("proximity query failed: %w", err)
		}

	} else if opts.Within != "" {
		// Bounding box query
		bbox, err := parseBoundingBox(opts.Within)
		if err != nil {
			return fmt.Errorf("invalid bounding box for --within: %w", err)
		}

		logger.Info("Executing bounding box query: %v", bbox)
		results, err = spatialDB.QueryByBoundingBox(*bbox)
		if err != nil {
			return fmt.Errorf("bounding box query failed: %w", err)
		}

	} else if opts.Contains != "" {
		// Containment query - find equipment whose bounds contain the point
		point, err := parseCoordinates(opts.Contains)
		if err != nil {
			return fmt.Errorf("invalid coordinates for --contains: %w", err)
		}

		// For containment, we can use a small radius proximity query
		// and filter results that actually contain the point
		logger.Info("Executing containment query for point: %v", point)
		results, err = spatialDB.QueryBySpatialProximity(point, 0.1) // 10cm radius
		if err != nil {
			return fmt.Errorf("containment query failed: %w", err)
		}
	}

	// Apply additional filters if provided
	results = filterSpatialResults(results, opts)

	// Output results
	return outputSpatialResults(results, opts)
}

// hasSpatialParams checks if spatial parameters are provided
func hasSpatialParams(opts QueryOptions) bool {
	return opts.Near != "" || opts.Within != "" || opts.Contains != ""
}

// parseCoordinates parses a coordinate string "x,y,z" into a Point3D
func parseCoordinates(coordStr string) (spatial.Point3D, error) {
	parts := strings.Split(coordStr, ",")
	if len(parts) != 3 {
		return spatial.Point3D{}, fmt.Errorf("coordinates must be in format 'x,y,z'")
	}

	x, err := strconv.ParseFloat(strings.TrimSpace(parts[0]), 64)
	if err != nil {
		return spatial.Point3D{}, fmt.Errorf("invalid x coordinate: %w", err)
	}

	y, err := strconv.ParseFloat(strings.TrimSpace(parts[1]), 64)
	if err != nil {
		return spatial.Point3D{}, fmt.Errorf("invalid y coordinate: %w", err)
	}

	z, err := strconv.ParseFloat(strings.TrimSpace(parts[2]), 64)
	if err != nil {
		return spatial.Point3D{}, fmt.Errorf("invalid z coordinate: %w", err)
	}

	return spatial.Point3D{X: x, Y: y, Z: z}, nil
}

// parseBoundingBox parses a bounding box string "minX,minY,minZ,maxX,maxY,maxZ"
func parseBoundingBox(bboxStr string) (*spatial.BoundingBox, error) {
	parts := strings.Split(bboxStr, ",")
	if len(parts) != 6 {
		return nil, fmt.Errorf("bounding box must be in format 'minX,minY,minZ,maxX,maxY,maxZ'")
	}

	coords := make([]float64, 6)
	for i, part := range parts {
		val, err := strconv.ParseFloat(strings.TrimSpace(part), 64)
		if err != nil {
			return nil, fmt.Errorf("invalid coordinate at position %d: %w", i+1, err)
		}
		coords[i] = val
	}

	return &spatial.BoundingBox{
		Min: spatial.Point3D{X: coords[0], Y: coords[1], Z: coords[2]},
		Max: spatial.Point3D{X: coords[3], Y: coords[4], Z: coords[5]},
	}, nil
}

// filterSpatialResults applies additional filters to spatial query results
func filterSpatialResults(results []*database.SpatialEquipment, opts QueryOptions) []*database.SpatialEquipment {
	filtered := make([]*database.SpatialEquipment, 0)

	for _, eq := range results {
		// Apply type filter
		if opts.Type != "" && !strings.Contains(strings.ToLower(eq.Equipment.ID), strings.ToLower(opts.Type)) {
			continue
		}

		// Apply status filter
		if opts.Status != "" && eq.Equipment.Status != opts.Status {
			continue
		}

		// Apply building filter
		if opts.Building != "" && !strings.HasPrefix(eq.Equipment.ID, opts.Building) {
			continue
		}

		filtered = append(filtered, eq)
	}

	// Apply limit if specified
	if opts.Limit > 0 && len(filtered) > opts.Limit {
		filtered = filtered[:opts.Limit]
	}

	return filtered
}

// outputSpatialResults outputs spatial query results in the requested format
func outputSpatialResults(results []*database.SpatialEquipment, opts QueryOptions) error {
	if opts.Count {
		fmt.Printf("Count: %d\n", len(results))
		return nil
	}

	switch opts.Output {
	case "json":
		return outputSpatialJSON(results)
	case "csv":
		return outputSpatialCSV(results)
	default:
		return outputSpatialTable(results)
	}
}

// outputSpatialTable outputs results as a formatted table
func outputSpatialTable(results []*database.SpatialEquipment) error {
	if len(results) == 0 {
		fmt.Println("No equipment found matching spatial criteria")
		return nil
	}

	// Print header
	fmt.Println("┌─────────────────────────────────────────────────────────────────────────────┐")
	fmt.Println("│ Equipment ID                    │ Position (X,Y,Z)      │ Distance │ Confidence │")
	fmt.Println("├─────────────────────────────────────────────────────────────────────────────┤")

	// Print results
	for _, eq := range results {
		id := eq.Equipment.ID
		if len(id) > 30 {
			id = id[:27] + "..."
		}

		var posStr string
		var distance string
		var confidence string

		if eq.SpatialData != nil {
			posStr = fmt.Sprintf("(%.2f, %.2f, %.2f)",
				eq.SpatialData.Position.X,
				eq.SpatialData.Position.Y,
				eq.SpatialData.Position.Z)

			if eq.SpatialData.DistanceFromQuery > 0 {
				distance = fmt.Sprintf("%.2fm", eq.SpatialData.DistanceFromQuery)
			} else {
				distance = "-"
			}

			confidence = eq.SpatialData.PositionConfidence.String()
		} else {
			posStr = "(no spatial data)"
			distance = "-"
			confidence = "-"
		}

		fmt.Printf("│ %-31s │ %-21s │ %-8s │ %-10s │\n", id, posStr, distance, confidence)
	}

	fmt.Println("└─────────────────────────────────────────────────────────────────────────────┘")
	fmt.Printf("\nTotal: %d equipment found\n", len(results))

	return nil
}

// outputSpatialJSON outputs results as JSON
func outputSpatialJSON(results []*database.SpatialEquipment) error {
	// Create a simplified JSON structure
	type JSONResult struct {
		ID         string                   `json:"id"`
		Position   *spatial.Point3D         `json:"position,omitempty"`
		Distance   float64                  `json:"distance,omitempty"`
		Confidence string                   `json:"confidence,omitempty"`
		Metadata   map[string]interface{}   `json:"metadata,omitempty"`
	}

	jsonResults := make([]JSONResult, 0, len(results))
	for _, eq := range results {
		jr := JSONResult{
			ID: eq.Equipment.ID,
		}

		if eq.SpatialData != nil {
			jr.Position = &eq.SpatialData.Position
			jr.Distance = eq.SpatialData.DistanceFromQuery
			jr.Confidence = eq.SpatialData.PositionConfidence.String()
		}

		jsonResults = append(jsonResults, jr)
	}

	output, err := json.MarshalIndent(jsonResults, "", "  ")
	if err != nil {
		return fmt.Errorf("failed to marshal JSON: %w", err)
	}

	fmt.Println(string(output))
	return nil
}

// outputSpatialCSV outputs results as CSV
func outputSpatialCSV(results []*database.SpatialEquipment) error {
	// Print CSV header
	fmt.Println("ID,X,Y,Z,Distance,Confidence")

	// Print CSV rows
	for _, eq := range results {
		id := eq.Equipment.ID
		var x, y, z, distance string
		confidence := "UNKNOWN"

		if eq.SpatialData != nil {
			x = fmt.Sprintf("%.3f", eq.SpatialData.Position.X)
			y = fmt.Sprintf("%.3f", eq.SpatialData.Position.Y)
			z = fmt.Sprintf("%.3f", eq.SpatialData.Position.Z)

			if eq.SpatialData.DistanceFromQuery > 0 {
				distance = fmt.Sprintf("%.3f", eq.SpatialData.DistanceFromQuery)
			} else {
				distance = "0"
			}

			confidence = eq.SpatialData.PositionConfidence.String()
		} else {
			x, y, z = "", "", ""
			distance = ""
		}

		// Escape ID if it contains commas
		if strings.Contains(id, ",") {
			id = fmt.Sprintf("\"%s\"", strings.ReplaceAll(id, "\"", "\"\""))
		}

		fmt.Printf("%s,%s,%s,%s,%s,%s\n", id, x, y, z, distance, confidence)
	}

	return nil
}

// getEnvOrDefault gets an environment variable or returns a default value
func getEnvOrDefault(key, defaultValue string) string {
	if value := os.Getenv(key); value != "" {
		return value
	}
	return defaultValue
}