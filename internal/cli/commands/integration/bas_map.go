package integration

import (
	"fmt"

	"github.com/arx-os/arxos/internal/domain/types"
	"github.com/spf13/cobra"
)

// newBASMapCommand creates the bas map subcommand
func newBASMapCommand(serviceContext any) *cobra.Command {
	cmd := &cobra.Command{
		Use:   "map <point-id>",
		Short: "Map a BAS point to a room or equipment",
		Long: `Manually map a BAS point to a spatial location (room or equipment).

Examples:
  arx bas map point-123 --room room-301
  arx bas map point-456 --equipment equip-789
  arx bas map AI-1-1 --room room-301 --confidence 3`,
		Args: cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			pointID := args[0]
			roomID, _ := cmd.Flags().GetString("room")
			equipmentID, _ := cmd.Flags().GetString("equipment")
			confidence, _ := cmd.Flags().GetInt("confidence")

			if roomID == "" && equipmentID == "" {
				return fmt.Errorf("either --room or --equipment is required")
			}

			if confidence < 1 || confidence > 3 {
				return fmt.Errorf("confidence must be between 1 and 3")
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

			// Parse IDs
			pid := types.FromString(pointID)

			// Map the point
			var err error
			if roomID != "" {
				rid := types.FromString(roomID)
				err = basPointRepo.MapToRoom(pid, rid, confidence)
				if err != nil {
					return fmt.Errorf("failed to map point to room: %w", err)
				}
				fmt.Printf("✅ Mapped BAS point %s to room %s (confidence: %d/3)\n", pointID, roomID, confidence)
			} else {
				eid := types.FromString(equipmentID)
				err = basPointRepo.MapToEquipment(pid, eid, confidence)
				if err != nil {
					return fmt.Errorf("failed to map point to equipment: %w", err)
				}
				fmt.Printf("✅ Mapped BAS point %s to equipment %s (confidence: %d/3)\n", pointID, equipmentID, confidence)
			}

			fmt.Printf("\nNext steps:\n")
			fmt.Printf("  • View point details: arx bas show %s\n", pointID)
			fmt.Printf("  • List all points:    arx bas list --building <building-id>\n")

			return nil
		},
	}

	cmd.Flags().String("room", "", "Room ID to map to")
	cmd.Flags().String("equipment", "", "Equipment ID to map to")
	cmd.Flags().Int("confidence", 3, "Mapping confidence (1-3, 3=verified)")

	return cmd
}
