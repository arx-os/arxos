package main

import (
	"context"
	"fmt"
	"strings"
	"time"

	"github.com/arx-os/arxos/internal/app/types"
	"github.com/arx-os/arxos/internal/common/logger"
	"github.com/arx-os/arxos/pkg/errors"
	"github.com/arx-os/arxos/pkg/models"
	"github.com/spf13/cobra"
)

var listCmd = &cobra.Command{
	Use:   "list <type>",
	Short: "List building components",
	Long: `List building components with filtering, sorting, and pagination support.
Optimized for large datasets with streaming and caching capabilities.

Examples:
  arx list equipment --building ARXOS-001 --floor 2
  arx list equipment --type "Air Handler" --status operational
  arx list room --floor 2 --limit 10 --offset 20
  arx list equipment --near "1000,2000,2700" --radius 5000
  arx list equipment --export results.csv --format csv`,
	Args: cobra.ExactArgs(1),
	RunE: runList,
}

var (
	listBuilding  string
	listFloor     int
	listRoom      string
	listType      string
	listStatus    string
	listSystem    string
	listTags      []string
	listLimit     int
	listOffset    int
	listSortBy    string
	listSortOrder string
	listFormat    string
	listExport    string
	listCache     bool
	listStream    bool
	listVerbose   bool
	listCount     bool
	listNear      string
	listRadius    float64
	listWithin    string
	listContains  string
)

func init() {
	// Filtering flags
	listCmd.Flags().StringVar(&listBuilding, "building", "", "Filter by building ID")
	listCmd.Flags().IntVar(&listFloor, "floor", 0, "Filter by floor number")
	listCmd.Flags().StringVar(&listRoom, "room", "", "Filter by room ID")
	listCmd.Flags().StringVar(&listType, "type", "", "Filter by component type")
	listCmd.Flags().StringVar(&listStatus, "status", "", "Filter by status")
	listCmd.Flags().StringVar(&listSystem, "system", "", "Filter by system type")
	listCmd.Flags().StringSliceVar(&listTags, "tags", []string{}, "Filter by tags")

	// Spatial filtering flags
	listCmd.Flags().StringVar(&listNear, "near", "", "Find components near coordinates (x,y,z)")
	listCmd.Flags().Float64Var(&listRadius, "radius", 0, "Search radius in millimeters (use with --near)")
	listCmd.Flags().StringVar(&listWithin, "within", "", "Find components within bounding box (minX,minY,maxX,maxY)")
	listCmd.Flags().StringVar(&listContains, "contains", "", "Find components containing point (x,y,z)")

	// Pagination and sorting
	listCmd.Flags().IntVar(&listLimit, "limit", 50, "Maximum number of results to return")
	listCmd.Flags().IntVar(&listOffset, "offset", 0, "Offset for pagination")
	listCmd.Flags().StringVar(&listSortBy, "sort-by", "name", "Sort by field (name, type, status, created_at)")
	listCmd.Flags().StringVar(&listSortOrder, "sort-order", "asc", "Sort order (asc, desc)")

	// Output format
	listCmd.Flags().StringVar(&listFormat, "format", "table", "Output format (table, json, csv)")
	listCmd.Flags().StringVar(&listExport, "export", "", "Export results to file")

	// Performance flags
	listCmd.Flags().BoolVar(&listCache, "cache", true, "Use caching for repeated queries")
	listCmd.Flags().BoolVar(&listStream, "stream", false, "Stream results for large datasets")
	listCmd.Flags().BoolVar(&listVerbose, "verbose", false, "Show detailed information")
	listCmd.Flags().BoolVar(&listCount, "count", false, "Show count only")
}

func runList(cmd *cobra.Command, args []string) error {
	ctx := context.Background()
	componentType := strings.ToLower(args[0])

	// Get services from DI container
	services := diContainer.GetServices()

	// Validate component type
	if !isValidComponentType(componentType) {
		return errors.New(errors.CodeInvalidInput, fmt.Sprintf("invalid component type: %s (supported: equipment, room, floor)", componentType))
	}

	// Validate pagination parameters
	if listLimit <= 0 {
		return errors.New(errors.CodeInvalidInput, "limit must be greater than 0")
	}
	if listOffset < 0 {
		return errors.New(errors.CodeInvalidInput, "offset must be non-negative")
	}

	// Validate sort parameters
	if !isValidSortField(listSortBy) {
		return errors.New(errors.CodeInvalidInput, fmt.Sprintf("invalid sort field: %s", listSortBy))
	}
	if !isValidSortOrder(listSortOrder) {
		return errors.New(errors.CodeInvalidInput, fmt.Sprintf("invalid sort order: %s (supported: asc, desc)", listSortOrder))
	}

	// Validate output format
	if !isValidOutputFormat(listFormat) {
		return errors.New(errors.CodeInvalidInput, fmt.Sprintf("invalid output format: %s (supported: table, json, csv)", listFormat))
	}

	// Create list options
	options := &ListOptions{
		Building:  listBuilding,
		Floor:     listFloor,
		Room:      listRoom,
		Type:      listType,
		Status:    listStatus,
		System:    listSystem,
		Tags:      listTags,
		Limit:     listLimit,
		Offset:    listOffset,
		SortBy:    listSortBy,
		SortOrder: listSortOrder,
		Format:    listFormat,
		Export:    listExport,
		UseCache:  listCache,
		Stream:    listStream,
		Verbose:   listVerbose,
		CountOnly: listCount,
		Near:      listNear,
		Radius:    listRadius,
		Within:    listWithin,
		Contains:  listContains,
	}

	// List components based on type
	switch componentType {
	case "equipment":
		return listEquipment(ctx, services, options)
	case "room":
		return listRooms(ctx, services, options)
	case "floor":
		return listFloors(ctx, services, options)
	default:
		return errors.New(errors.CodeInvalidInput, fmt.Sprintf("unsupported component type: %s", componentType))
	}
}

// ListOptions holds all list command options
type ListOptions struct {
	Building  string
	Floor     int
	Room      string
	Type      string
	Status    string
	System    string
	Tags      []string
	Limit     int
	Offset    int
	SortBy    string
	SortOrder string
	Format    string
	Export    string
	UseCache  bool
	Stream    bool
	Verbose   bool
	CountOnly bool
	Near      string
	Radius    float64
	Within    string
	Contains  string
}

func listEquipment(ctx context.Context, services *types.Services, options *ListOptions) error {
	startTime := time.Now()

	// TODO: Implement equipment listing when service is available
	logger.Info("Listing equipment", "building", options.Building, "limit", options.Limit)

	// For now, create placeholder results
	results := &EquipmentListResult{
		Equipment: []models.Equipment{
			{
				ID:     "eq-001",
				Name:   "Placeholder Equipment 1",
				Type:   "outlet",
				Status: "active",
				Notes:  "This is a placeholder - service not implemented yet",
			},
			{
				ID:     "eq-002",
				Name:   "Placeholder Equipment 2",
				Type:   "switch",
				Status: "active",
				Notes:  "This is a placeholder - service not implemented yet",
			},
		},
		Total: 2,
	}

	// Show count only if requested
	if options.CountOnly {
		fmt.Printf("Total equipment: %d\n", results.Total)
		return nil
	}

	// Display results
	if err := displayEquipmentList(results, options); err != nil {
		return errors.Wrap(err, errors.CodeInternal, "failed to display results")
	}

	// Show performance info if verbose
	if options.Verbose {
		duration := time.Since(startTime)
		fmt.Printf("\nQuery completed in %v\n", duration)
		fmt.Printf("Total: %d, Returned: %d\n", results.Total, len(results.Equipment))
	}

	return nil
}

func listRooms(ctx context.Context, services *types.Services, options *ListOptions) error {
	startTime := time.Now()

	// TODO: Implement room listing when service is available
	logger.Info("Listing rooms", "building", options.Building, "limit", options.Limit)

	// For now, create placeholder results
	results := &RoomListResult{
		Rooms: []models.Room{
			{
				ID:   "room-001",
				Name: "Placeholder Room 1",
				Bounds: models.Bounds{
					MinX: 0,
					MinY: 0,
					MaxX: 1000,
					MaxY: 1000,
				},
			},
			{
				ID:   "room-002",
				Name: "Placeholder Room 2",
				Bounds: models.Bounds{
					MinX: 1000,
					MinY: 0,
					MaxX: 2000,
					MaxY: 1000,
				},
			},
		},
		Total: 2,
	}

	// Show count only if requested
	if options.CountOnly {
		fmt.Printf("Total rooms: %d\n", results.Total)
		return nil
	}

	// Display results
	if err := displayRoomList(results, options); err != nil {
		return errors.Wrap(err, errors.CodeInternal, "failed to display results")
	}

	// Show performance info if verbose
	if options.Verbose {
		duration := time.Since(startTime)
		fmt.Printf("\nQuery completed in %v\n", duration)
		fmt.Printf("Total: %d, Returned: %d\n", results.Total, len(results.Rooms))
	}

	return nil
}

func listFloors(ctx context.Context, services *types.Services, options *ListOptions) error {
	startTime := time.Now()

	// TODO: Implement floor listing when service is available
	logger.Info("Listing floors", "building", options.Building, "limit", options.Limit)

	// For now, create placeholder results
	results := &FloorListResult{
		Floors: []models.FloorPlan{
			{
				ID:    "floor-001",
				Name:  "Placeholder Floor 1",
				Level: 1,
			},
			{
				ID:    "floor-002",
				Name:  "Placeholder Floor 2",
				Level: 2,
			},
		},
		Total: 2,
	}

	// Show count only if requested
	if options.CountOnly {
		fmt.Printf("Total floors: %d\n", results.Total)
		return nil
	}

	// Display results
	if err := displayFloorList(results, options); err != nil {
		return errors.Wrap(err, errors.CodeInternal, "failed to display results")
	}

	// Show performance info if verbose
	if options.Verbose {
		duration := time.Since(startTime)
		fmt.Printf("\nQuery completed in %v\n", duration)
		fmt.Printf("Total: %d, Returned: %d\n", results.Total, len(results.Floors))
	}

	return nil
}

// Display functions

func displayEquipmentList(results *EquipmentListResult, options *ListOptions) error {
	if len(results.Equipment) == 0 {
		fmt.Println("No equipment found")
		return nil
	}

	switch options.Format {
	case "json":
		return displayEquipmentListJSON(results, options)
	case "csv":
		return displayEquipmentListCSV(results, options)
	default:
		return displayEquipmentListTable(results, options)
	}
}

func displayEquipmentListTable(results *EquipmentListResult, options *ListOptions) error {
	fmt.Printf("Equipment List (%d of %d)\n", len(results.Equipment), results.Total)
	fmt.Printf("========================\n\n")

	// Calculate column widths
	widths := map[string]int{
		"ID":     8,
		"Name":   20,
		"Type":   15,
		"Status": 12,
		"Room":   10,
		"System": 12,
	}

	for _, eq := range results.Equipment {
		if len(eq.ID) > widths["ID"] {
			widths["ID"] = len(eq.ID)
		}
		if len(eq.Name) > widths["Name"] {
			widths["Name"] = len(eq.Name)
		}
		if len(eq.Type) > widths["Type"] {
			widths["Type"] = len(eq.Type)
		}
		if len(eq.Status) > widths["Status"] {
			widths["Status"] = len(eq.Status)
		}
		if len(eq.RoomID) > widths["Room"] {
			widths["Room"] = len(eq.RoomID)
		}
	}

	// Print header
	fmt.Printf("%-*s %-*s %-*s %-*s %-*s\n",
		widths["ID"], "ID",
		widths["Name"], "Name",
		widths["Type"], "Type",
		widths["Status"], "Status",
		widths["Room"], "Room")

	// Print separator
	fmt.Printf("%s %s %s %s %s\n",
		strings.Repeat("-", widths["ID"]),
		strings.Repeat("-", widths["Name"]),
		strings.Repeat("-", widths["Type"]),
		strings.Repeat("-", widths["Status"]),
		strings.Repeat("-", widths["Room"]))

	// Print rows
	for _, eq := range results.Equipment {
		fmt.Printf("%-*s %-*s %-*s %-*s %-*s\n",
			widths["ID"], eq.ID,
			widths["Name"], eq.Name,
			widths["Type"], eq.Type,
			widths["Status"], eq.Status,
			widths["Room"], eq.RoomID)
	}

	return nil
}

func displayEquipmentListJSON(results *EquipmentListResult, options *ListOptions) error {
	fmt.Printf("JSON output not implemented yet\n")
	return nil
}

func displayEquipmentListCSV(results *EquipmentListResult, options *ListOptions) error {
	fmt.Printf("CSV output not implemented yet\n")
	return nil
}

func displayRoomList(results *RoomListResult, options *ListOptions) error {
	if len(results.Rooms) == 0 {
		fmt.Println("No rooms found")
		return nil
	}

	switch options.Format {
	case "json":
		return displayRoomListJSON(results, options)
	case "csv":
		return displayRoomListCSV(results, options)
	default:
		return displayRoomListTable(results, options)
	}
}

func displayRoomListTable(results *RoomListResult, options *ListOptions) error {
	fmt.Printf("Room List (%d of %d)\n", len(results.Rooms), results.Total)
	fmt.Printf("==================\n\n")

	// Calculate column widths
	widths := map[string]int{
		"ID":     8,
		"Name":   25,
		"Floor":  6,
		"Bounds": 20,
	}

	for _, room := range results.Rooms {
		if len(room.ID) > widths["ID"] {
			widths["ID"] = len(room.ID)
		}
		if len(room.Name) > widths["Name"] {
			widths["Name"] = len(room.Name)
		}
		boundsStr := fmt.Sprintf("(%.0f,%.0f)-(%.0f,%.0f)", room.Bounds.MinX, room.Bounds.MinY, room.Bounds.MaxX, room.Bounds.MaxY)
		if len(boundsStr) > widths["Bounds"] {
			widths["Bounds"] = len(boundsStr)
		}
	}

	// Print header
	fmt.Printf("%-*s %-*s %-*s\n",
		widths["ID"], "ID",
		widths["Name"], "Name",
		widths["Bounds"], "Bounds")

	// Print separator
	fmt.Printf("%s %s %s\n",
		strings.Repeat("-", widths["ID"]),
		strings.Repeat("-", widths["Name"]),
		strings.Repeat("-", widths["Bounds"]))

	// Print rows
	for _, room := range results.Rooms {
		boundsStr := fmt.Sprintf("(%.0f,%.0f)-(%.0f,%.0f)", room.Bounds.MinX, room.Bounds.MinY, room.Bounds.MaxX, room.Bounds.MaxY)
		fmt.Printf("%-*s %-*s %-*s\n",
			widths["ID"], room.ID,
			widths["Name"], room.Name,
			widths["Bounds"], boundsStr)
	}

	return nil
}

func displayRoomListJSON(results *RoomListResult, options *ListOptions) error {
	fmt.Printf("JSON output not implemented yet\n")
	return nil
}

func displayRoomListCSV(results *RoomListResult, options *ListOptions) error {
	fmt.Printf("CSV output not implemented yet\n")
	return nil
}

func displayFloorList(results *FloorListResult, options *ListOptions) error {
	if len(results.Floors) == 0 {
		fmt.Println("No floors found")
		return nil
	}

	switch options.Format {
	case "json":
		return displayFloorListJSON(results, options)
	case "csv":
		return displayFloorListCSV(results, options)
	default:
		return displayFloorListTable(results, options)
	}
}

func displayFloorListTable(results *FloorListResult, options *ListOptions) error {
	fmt.Printf("Floor List (%d of %d)\n", len(results.Floors), results.Total)
	fmt.Printf("===================\n\n")

	// Calculate column widths
	widths := map[string]int{
		"ID":     8,
		"Name":   20,
		"Level":  6,
		"Height": 8,
	}

	for _, floor := range results.Floors {
		if len(floor.ID) > widths["ID"] {
			widths["ID"] = len(floor.ID)
		}
		if len(floor.Name) > widths["Name"] {
			widths["Name"] = len(floor.Name)
		}
	}

	// Print header
	fmt.Printf("%-*s %-*s %-*s\n",
		widths["ID"], "ID",
		widths["Name"], "Name",
		widths["Level"], "Level")

	// Print separator
	fmt.Printf("%s %s %s\n",
		strings.Repeat("-", widths["ID"]),
		strings.Repeat("-", widths["Name"]),
		strings.Repeat("-", widths["Level"]))

	// Print rows
	for _, floor := range results.Floors {
		fmt.Printf("%-*s %-*s %-*d\n",
			widths["ID"], floor.ID,
			widths["Name"], floor.Name,
			widths["Level"], floor.Level)
	}

	return nil
}

func displayFloorListJSON(results *FloorListResult, options *ListOptions) error {
	fmt.Printf("JSON output not implemented yet\n")
	return nil
}

func displayFloorListCSV(results *FloorListResult, options *ListOptions) error {
	fmt.Printf("CSV output not implemented yet\n")
	return nil
}

// Helper functions

func isValidSortField(field string) bool {
	validFields := []string{"name", "type", "status", "created_at", "updated_at"}
	for _, valid := range validFields {
		if field == valid {
			return true
		}
	}
	return false
}

func isValidSortOrder(order string) bool {
	return order == "asc" || order == "desc"
}

func generateCacheKey(componentType string, options *ListOptions) string {
	// Generate a cache key based on all filter parameters
	key := fmt.Sprintf("list:%s:%s:%d:%s:%s:%s:%s:%d:%d:%s:%s",
		componentType,
		options.Building,
		options.Floor,
		options.Room,
		options.Type,
		options.Status,
		options.System,
		options.Limit,
		options.Offset,
		options.SortBy,
		options.SortOrder)
	return key
}

// Placeholder types - these would be defined in the actual service interfaces
type EquipmentListResult struct {
	Equipment []models.Equipment
	Total     int
}

type RoomListResult struct {
	Rooms []models.Room
	Total int
}

type FloorListResult struct {
	Floors []models.FloorPlan
	Total  int
}

type EquipmentListParams struct {
	Building  string
	Floor     int
	Room      string
	Type      string
	Status    string
	System    string
	Tags      []string
	Limit     int
	Offset    int
	SortBy    string
	SortOrder string
	Near      string
	Radius    float64
	Within    string
	Contains  string
}

type RoomListParams struct {
	Building  string
	Floor     int
	Tags      []string
	Limit     int
	Offset    int
	SortBy    string
	SortOrder string
}

type FloorListParams struct {
	Building  string
	Tags      []string
	Limit     int
	Offset    int
	SortBy    string
	SortOrder string
}
