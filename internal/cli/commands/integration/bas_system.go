package integration

import (
	"fmt"
	"strings"

	"github.com/arx-os/arxos/internal/domain"
	"github.com/arx-os/arxos/internal/domain/bas"
	"github.com/arx-os/arxos/internal/domain/types"
	"github.com/arx-os/arxos/internal/usecase/integration"
	"github.com/spf13/cobra"
)

// ContainerProvider interface for accessing the DI container
type ContainerProvider interface {
	GetBASImportUseCase() *integration.BASImportUseCase
	GetBASSystemRepository() bas.BASSystemRepository
	GetBASPointRepository() bas.BASPointRepository
	GetLogger() domain.Logger
}

// NewBASCommand creates the BAS integration command
func NewBASCommand(serviceContext any) *cobra.Command {
	cmd := &cobra.Command{
		Use:   "bas",
		Short: "BAS/BMS integration commands",
		Long: `Manage Building Automation System (BAS) integrations.

ArxOS integrates with BAS systems like Johnson Controls Metasys, Siemens Desigo,
Honeywell, and Tridium Niagara to provide spatial reference and version control
for control points.

Examples:
  # Import BAS points from Metasys export
  arx bas import points.csv --building bldg-001 --system metasys

  # List BAS systems
  arx bas list --building bldg-001

  # Show unmapped points
  arx bas unmapped --building bldg-001

  # Map a point to a room
  arx bas map AI-1-1 --room room-301`,
	}

	// Add subcommands
	cmd.AddCommand(newBASImportCommand(serviceContext))
	cmd.AddCommand(newBASListCommand(serviceContext))
	cmd.AddCommand(newBASUnmappedCommand(serviceContext))
	cmd.AddCommand(newBASMapCommand(serviceContext))
	cmd.AddCommand(newBASShowCommand(serviceContext))

	return cmd
}

// newBASListCommand creates the bas list subcommand
func newBASListCommand(serviceContext any) *cobra.Command {
	cmd := &cobra.Command{
		Use:   "list",
		Short: "List BAS systems and points",
		Long: `List BAS systems configured for a building or points within a system.

Examples:
  arx bas list --building bldg-001
  arx bas list --building bldg-001 --system sys-001
  arx bas list --room room-301`,
		RunE: func(cmd *cobra.Command, args []string) error {
			buildingID, _ := cmd.Flags().GetString("building")
			systemID, _ := cmd.Flags().GetString("system")
			roomID, _ := cmd.Flags().GetString("room")
			floorID, _ := cmd.Flags().GetString("floor")

			if buildingID == "" && systemID == "" && roomID == "" {
				return fmt.Errorf("one of --building, --system, or --room is required")
			}

			// Get container
			cp, ok := serviceContext.(ContainerProvider)
			if !ok {
				return fmt.Errorf("BAS service not available - database not initialized")
			}

			basPointRepo := cp.GetBASPointRepository()
			if basPointRepo == nil {
				return fmt.Errorf("BAS point repository not available")
			}

			// Build filter based on CLI flags
			filter := bas.BASPointFilter{}

			if buildingID != "" {
				bid := types.FromString(buildingID)
				filter.BuildingID = &bid
			}

			if systemID != "" {
				sid := types.FromString(systemID)
				filter.BASSystemID = &sid
			}

			if roomID != "" {
				rid := types.FromString(roomID)
				filter.RoomID = &rid
			}

			if floorID != "" {
				fid := types.FromString(floorID)
				filter.FloorID = &fid
			}

			// Query BAS points
			points, err := basPointRepo.List(filter, 1000, 0)
			if err != nil {
				return fmt.Errorf("failed to list BAS points: %w", err)
			}

			// Display results
			fmt.Printf("📋 BAS Points:\n\n")

			if len(points) == 0 {
				fmt.Printf("No BAS points found matching filters.\n")
				fmt.Printf("\nFilters applied:\n")
				if buildingID != "" {
					fmt.Printf("  Building: %s\n", buildingID)
				}
				if systemID != "" {
					fmt.Printf("  System:   %s\n", systemID)
				}
				if roomID != "" {
					fmt.Printf("  Room:     %s\n", roomID)
				}
				if floorID != "" {
					fmt.Printf("  Floor:    %s\n", floorID)
				}
				return nil
			}

			// Print table header
			fmt.Printf("%-20s %-15s %-12s %-30s %-20s %s\n",
				"Point Name", "Device ID", "Type", "Description", "Location", "Mapped")
			fmt.Printf("%s\n", strings.Repeat("-", 120))

			// Print each point
			for _, point := range points {
				mappedStatus := "❌ No"
				if point.Mapped {
					mappedStatus = fmt.Sprintf("✅ Yes (%d/3)", point.MappingConfidence)
				}

				// Truncate long descriptions
				desc := point.Description
				if len(desc) > 28 {
					desc = desc[:25] + "..."
				}

				location := point.LocationText
				if len(location) > 18 {
					location = location[:15] + "..."
				}

				fmt.Printf("%-20s %-15s %-12s %-30s %-20s %s\n",
					point.PointName,
					point.DeviceID,
					point.PointType,
					desc,
					location,
					mappedStatus,
				)
			}

			// Print summary
			mapped := 0
			for _, p := range points {
				if p.Mapped {
					mapped++
				}
			}

			fmt.Printf("\n")
			fmt.Printf("Total: %d points (%d mapped, %d unmapped)\n", len(points), mapped, len(points)-mapped)

			// Show next steps if there are unmapped points
			if len(points)-mapped > 0 && buildingID != "" {
				fmt.Printf("\nNext steps:\n")
				fmt.Printf("  • View unmapped: arx bas unmapped --building %s\n", buildingID)
				fmt.Printf("  • Map a point:   arx bas map <point-id> --room <room-id>\n")
			}

			return nil
		},
	}

	cmd.Flags().String("building", "", "Building ID")
	cmd.Flags().String("system", "", "BAS system ID")
	cmd.Flags().String("room", "", "Room ID")
	cmd.Flags().String("floor", "", "Floor ID")

	return cmd
}

// newBASUnmappedCommand creates the bas unmapped subcommand
func newBASUnmappedCommand(serviceContext any) *cobra.Command {
	cmd := &cobra.Command{
		Use:   "unmapped",
		Short: "List unmapped BAS points",
		Long: `List BAS points that haven't been mapped to rooms or equipment.

Examples:
  arx bas unmapped --building bldg-001
  arx bas unmapped --building bldg-001 --auto-map`,
		RunE: func(cmd *cobra.Command, args []string) error {
			buildingID, _ := cmd.Flags().GetString("building")
			autoMap, _ := cmd.Flags().GetBool("auto-map")

			if buildingID == "" {
				return fmt.Errorf("--building flag is required")
			}

			// Get container
			cp, ok := serviceContext.(ContainerProvider)
			if !ok {
				return fmt.Errorf("BAS service not available - database not initialized")
			}

			basPointRepo := cp.GetBASPointRepository()
			if basPointRepo == nil {
				return fmt.Errorf("BAS point repository not available")
			}

			// Query unmapped points
			bid := types.FromString(buildingID)
			points, err := basPointRepo.ListUnmapped(bid)
			if err != nil {
				return fmt.Errorf("failed to list unmapped points: %w", err)
			}

			fmt.Printf("⚠️  Unmapped BAS Points:\n\n")

			if len(points) == 0 {
				fmt.Printf("✅ All BAS points are mapped! No unmapped points found.\n")
				return nil
			}

			// Print table header
			fmt.Printf("%-20s %-15s %-12s %-30s %-25s\n",
				"Point Name", "Device ID", "Type", "Description", "Location Text")
			fmt.Printf("%s\n", strings.Repeat("-", 110))

			// Print each unmapped point
			for _, point := range points {
				// Truncate long descriptions
				desc := point.Description
				if len(desc) > 28 {
					desc = desc[:25] + "..."
				}

				location := point.LocationText
				if len(location) > 23 {
					location = location[:20] + "..."
				}

				fmt.Printf("%-20s %-15s %-12s %-30s %-25s\n",
					point.PointName,
					point.DeviceID,
					point.PointType,
					desc,
					location,
				)
			}

			fmt.Printf("\n")
			fmt.Printf("Total: %d unmapped points\n\n", len(points))

			if autoMap {
				// Get BAS import use case for auto-mapping
				basImportUC := cp.GetBASImportUseCase()
				if basImportUC == nil {
					fmt.Printf("⚠️  Auto-mapping not available - BAS import use case not initialized\n")
				} else {
					fmt.Printf("🗺️  Auto-mapping functionality coming soon\n")
					fmt.Printf("   Manual mapping: arx bas map <point-id> --room <room-id>\n")
				}
			} else {
				fmt.Printf("Next steps:\n")
				fmt.Printf("  • Map manually: arx bas map <point-id> --room <room-id>\n")
				fmt.Printf("  • Auto-map all: arx bas unmapped --building %s --auto-map (coming soon)\n", buildingID)
			}

			return nil
		},
	}

	cmd.Flags().String("building", "", "Building ID (required)")
	cmd.Flags().Bool("auto-map", false, "Attempt automatic mapping")

	return cmd
}

// newBASShowCommand creates the bas show subcommand
func newBASShowCommand(serviceContext any) *cobra.Command {
	cmd := &cobra.Command{
		Use:   "show <point-id>",
		Short: "Show details of a BAS point",
		Long: `Display detailed information about a BAS control point.

Examples:
  arx bas show point-123
  arx bas show AI-1-1`,
		Args: cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			pointID := args[0]

			// Get container
			cp, ok := serviceContext.(ContainerProvider)
			if !ok {
				return fmt.Errorf("BAS service not available - database not initialized")
			}

			basPointRepo := cp.GetBASPointRepository()
			if basPointRepo == nil {
				return fmt.Errorf("BAS point repository not available")
			}

			// Get the point
			pid := types.FromString(pointID)
			point, err := basPointRepo.GetByID(pid)
			if err != nil {
				return fmt.Errorf("failed to get BAS point: %w", err)
			}

			// Display point details
			fmt.Printf("BAS Point: %s\n", point.PointName)
			fmt.Printf("%s\n", strings.Repeat("=", 70))
			fmt.Printf("\n")

			fmt.Printf("Point Information:\n")
			fmt.Printf("  ID:          %s\n", point.ID)
			fmt.Printf("  Name:        %s\n", point.PointName)
			fmt.Printf("  Device:      %s\n", point.DeviceID)
			fmt.Printf("  Type:        %s\n", point.PointType)
			if point.ObjectType != "" {
				fmt.Printf("  Object Type: %s\n", point.ObjectType)
			}
			if point.Description != "" {
				fmt.Printf("  Description: %s\n", point.Description)
			}
			if point.Units != "" {
				fmt.Printf("  Units:       %s\n", point.Units)
			}
			fmt.Printf("  Writeable:   %v\n", point.Writeable)
			if point.MinValue != nil {
				fmt.Printf("  Min Value:   %.2f\n", *point.MinValue)
			}
			if point.MaxValue != nil {
				fmt.Printf("  Max Value:   %.2f\n", *point.MaxValue)
			}
			fmt.Printf("\n")

			fmt.Printf("BAS System:\n")
			fmt.Printf("  System ID:   %s\n", point.BASSystemID)
			fmt.Printf("  Building ID: %s\n", point.BuildingID)
			fmt.Printf("\n")

			fmt.Printf("Spatial Mapping:\n")
			if point.Mapped {
				fmt.Printf("  Mapped:      ✅ Yes\n")
				fmt.Printf("  Confidence:  %d/3", point.MappingConfidence)
				switch point.MappingConfidence {
				case 1:
					fmt.Printf(" (low - auto-mapped)")
				case 2:
					fmt.Printf(" (medium - verified by user)")
				case 3:
					fmt.Printf(" (high - manually verified)")
				}
				fmt.Printf("\n")

				if point.RoomID != nil {
					fmt.Printf("  Room ID:     %s\n", *point.RoomID)
				}
				if point.FloorID != nil {
					fmt.Printf("  Floor ID:    %s\n", *point.FloorID)
				}
				if point.EquipmentID != nil {
					fmt.Printf("  Equipment:   %s\n", *point.EquipmentID)
				}
				if point.LocationText != "" {
					fmt.Printf("  Location:    %s\n", point.LocationText)
				}
			} else {
				fmt.Printf("  Mapped:      ❌ No\n")
				if point.LocationText != "" {
					fmt.Printf("  Location:    %s (text only)\n", point.LocationText)
				}
			}
			fmt.Printf("\n")

			if point.CurrentValue != nil || point.CurrentValueNumeric != nil {
				fmt.Printf("Current Value:\n")
				if point.CurrentValueNumeric != nil {
					fmt.Printf("  Value:       %.2f", *point.CurrentValueNumeric)
					if point.Units != "" {
						fmt.Printf(" %s", point.Units)
					}
					fmt.Printf("\n")
				} else if point.CurrentValue != nil {
					fmt.Printf("  Value:       %s\n", *point.CurrentValue)
				}
				if point.LastUpdated != nil {
					fmt.Printf("  Updated:     %s\n", point.LastUpdated.Format("2006-01-02 15:04:05"))
				}
				fmt.Printf("\n")
			}

			fmt.Printf("Import Information:\n")
			fmt.Printf("  Imported:    %s\n", point.ImportedAt.Format("2006-01-02 15:04:05"))
			if point.ImportSource != "" {
				fmt.Printf("  Source:      %s\n", point.ImportSource)
			}
			fmt.Printf("  Created:     %s\n", point.CreatedAt.Format("2006-01-02 15:04:05"))
			fmt.Printf("  Updated:     %s\n", point.UpdatedAt.Format("2006-01-02 15:04:05"))
			fmt.Printf("\n")

			// Show next steps
			if !point.Mapped {
				fmt.Printf("Next steps:\n")
				fmt.Printf("  • Map to room:   arx bas map %s --room <room-id>\n", pointID)
				fmt.Printf("  • Map to equipment: arx bas map %s --equipment <equipment-id>\n", pointID)
			}

			return nil
		},
	}

	return cmd
}
