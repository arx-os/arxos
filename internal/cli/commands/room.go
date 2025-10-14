package commands

import (
	"context"
	"fmt"
	"os"
	"text/tabwriter"

	"github.com/arx-os/arxos/internal/domain"
	"github.com/arx-os/arxos/internal/domain/types"
	"github.com/arx-os/arxos/internal/usecase"
	"github.com/spf13/cobra"
)

// RoomServiceProvider provides access to room services
type RoomServiceProvider interface {
	GetRoomUseCase() *usecase.RoomUseCase
}

// CreateRoomCommands creates room management commands
func CreateRoomCommands(serviceContext any) *cobra.Command {
	roomCmd := &cobra.Command{
		Use:   "room",
		Short: "Manage rooms",
		Long:  `Create, list, get, update, and delete rooms in buildings`,
	}

	roomCmd.AddCommand(createRoomCreateCommand(serviceContext))
	roomCmd.AddCommand(createRoomListCommand(serviceContext))
	roomCmd.AddCommand(createRoomGetCommand(serviceContext))
	roomCmd.AddCommand(createRoomDeleteCommand(serviceContext))
	roomCmd.AddCommand(createRoomMoveCommand(serviceContext))
	roomCmd.AddCommand(createRoomResizeCommand(serviceContext))

	return roomCmd
}

// createRoomCreateCommand creates the room create command
func createRoomCreateCommand(serviceContext any) *cobra.Command {
	var (
		name    string
		number  string
		floorID string
		x       float64
		y       float64
		width   float64
		height  float64
	)

	cmd := &cobra.Command{
		Use:   "create",
		Short: "Create a new room",
		Long:  "Create a new room on a floor with specified room number and optional dimensions",
		Example: `  # Create a room
  arx room create --floor abc123 --name "Room 101" --number "101"

  # Create room with position and dimensions
  arx room create --floor abc123 --name "Room 101" --number "101" \
    --x 10 --y 20 --width 30 --height 20`,
		RunE: func(cmd *cobra.Command, args []string) error {
			ctx := context.Background()

			// Get service from context
			sc, ok := serviceContext.(RoomServiceProvider)
			if !ok {
				return fmt.Errorf("service context is not available")
			}
			roomUC := sc.GetRoomUseCase()

			// Validate required fields
			if name == "" {
				return fmt.Errorf("room name is required (--name)")
			}
			if floorID == "" {
				return fmt.Errorf("floor ID is required (--floor)")
			}
			if number == "" {
				return fmt.Errorf("room number is required (--number)")
			}

			// Create request
			req := &domain.CreateRoomRequest{
				FloorID: types.FromString(floorID),
				Name:    name,
				Number:  number,
			}

			// Add location if provided
			if x != 0 || y != 0 {
				req.Location = &domain.Location{
					X: x,
					Y: y,
					Z: 0,
				}
			}

			// Add dimensions if provided
			if width > 0 {
				req.Width = width
			}
			if height > 0 {
				req.Height = height
			}

			// Create room
			room, err := roomUC.CreateRoom(ctx, req)
			if err != nil {
				return fmt.Errorf("failed to create room: %w", err)
			}

			// Print success
			fmt.Printf("✅ Room created successfully!\n\n")
			fmt.Printf("   ID:     %s\n", room.ID.String())
			fmt.Printf("   Name:   %s\n", room.Name)
			fmt.Printf("   Number: %s\n", room.Number)
			fmt.Printf("   Floor:  %s\n", room.FloorID.String())
			fmt.Printf("\n")

			return nil
		},
	}

	// Add flags
	cmd.Flags().StringVarP(&name, "name", "n", "", "Room name (required)")
	cmd.Flags().StringVar(&number, "number", "", "Room number (required)")
	cmd.Flags().StringVarP(&floorID, "floor", "f", "", "Floor ID (required)")
	cmd.Flags().Float64Var(&x, "x", 0, "X coordinate (optional)")
	cmd.Flags().Float64Var(&y, "y", 0, "Y coordinate (optional)")
	cmd.Flags().Float64Var(&width, "width", 0, "Width in meters (optional)")
	cmd.Flags().Float64Var(&height, "height", 0, "Height in meters (optional)")

	cmd.MarkFlagRequired("name")
	cmd.MarkFlagRequired("number")
	cmd.MarkFlagRequired("floor")

	return cmd
}

// createRoomListCommand creates the room list command
func createRoomListCommand(serviceContext any) *cobra.Command {
	var (
		floorID string
		limit   int
		offset  int
	)

	cmd := &cobra.Command{
		Use:   "list",
		Short: "List rooms",
		Long:  "List rooms on a floor",
		Example: `  # List all rooms on a floor
  arx room list --floor abc123`,
		RunE: func(cmd *cobra.Command, args []string) error {
			ctx := context.Background()

			// Validate required fields
			if floorID == "" {
				return fmt.Errorf("floor ID is required (--floor)")
			}

			// Get service from context
			sc, ok := serviceContext.(RoomServiceProvider)
			if !ok {
				return fmt.Errorf("service context is not available")
			}
			roomUC := sc.GetRoomUseCase()

			// List rooms
			rooms, err := roomUC.ListRooms(ctx, types.FromString(floorID), limit, offset)
			if err != nil {
				return fmt.Errorf("failed to list rooms: %w", err)
			}

			if len(rooms) == 0 {
				fmt.Println("No rooms found.")
				return nil
			}

			// Print results in table format
			w := tabwriter.NewWriter(os.Stdout, 0, 0, 3, ' ', 0)
			fmt.Fprintf(w, "ID\tNAME\tNUMBER\tCREATED\n")
			fmt.Fprintf(w, "--\t----\t------\t-------\n")

			for _, room := range rooms {
				fmt.Fprintf(w, "%s\t%s\t%s\t%s\n",
					room.ID.String()[:8]+"...",
					room.Name,
					room.Number,
					room.CreatedAt.Format("2006-01-02"),
				)
			}
			w.Flush()

			fmt.Printf("\n%d room(s) found\n", len(rooms))

			return nil
		},
	}

	// Add flags
	cmd.Flags().StringVarP(&floorID, "floor", "f", "", "Floor ID (required)")
	cmd.Flags().IntVarP(&limit, "limit", "l", 100, "Maximum number of results")
	cmd.Flags().IntVarP(&offset, "offset", "o", 0, "Offset for pagination")

	cmd.MarkFlagRequired("floor")

	return cmd
}

// createRoomGetCommand creates the room get command
func createRoomGetCommand(serviceContext any) *cobra.Command {
	cmd := &cobra.Command{
		Use:   "get <room-id>",
		Short: "Get room details",
		Long:  "Get detailed information about a specific room by ID",
		Example: `  # Get room details
  arx room get abc123def456`,
		Args: cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			ctx := context.Background()
			roomID := args[0]

			// Get service from context
			sc, ok := serviceContext.(RoomServiceProvider)
			if !ok {
				return fmt.Errorf("service context is not available")
			}
			roomUC := sc.GetRoomUseCase()

			// Get room
			room, err := roomUC.GetRoom(ctx, types.FromString(roomID))
			if err != nil {
				return fmt.Errorf("failed to get room: %w", err)
			}

			// Print room details
			fmt.Printf("Room Details:\n\n")
			fmt.Printf("   ID:      %s\n", room.ID.String())
			fmt.Printf("   Name:    %s\n", room.Name)
			fmt.Printf("   Number:  %s\n", room.Number)
			fmt.Printf("   Floor:   %s\n", room.FloorID.String())
			fmt.Printf("   Created: %s\n", room.CreatedAt.Format("2006-01-02 15:04:05"))
			fmt.Printf("   Updated: %s\n", room.UpdatedAt.Format("2006-01-02 15:04:05"))
			fmt.Printf("\n")

			return nil
		},
	}

	return cmd
}

// createRoomDeleteCommand creates the room delete command
func createRoomDeleteCommand(serviceContext any) *cobra.Command {
	var force bool

	cmd := &cobra.Command{
		Use:   "delete <room-id>",
		Short: "Delete a room",
		Long:  "Delete a room from the system (requires confirmation unless --force is used)",
		Example: `  # Delete with confirmation
  arx room delete abc123

  # Delete without confirmation
  arx room delete abc123 --force`,
		Args: cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			ctx := context.Background()
			roomID := args[0]

			// Get service from context
			sc, ok := serviceContext.(RoomServiceProvider)
			if !ok {
				return fmt.Errorf("service context is not available")
			}
			roomUC := sc.GetRoomUseCase()

			// Confirmation prompt unless --force
			if !force {
				fmt.Printf("⚠️  Are you sure you want to delete room %s? (yes/no): ", roomID)
				var response string
				fmt.Scanln(&response)
				if response != "yes" && response != "y" {
					fmt.Println("Deletion cancelled.")
					return nil
				}
			}

			// Delete room
			err := roomUC.DeleteRoom(ctx, roomID)
			if err != nil {
				return fmt.Errorf("failed to delete room: %w", err)
			}

			// Print success
			fmt.Printf("✅ Room deleted successfully!\n")

			return nil
		},
	}

	// Add flags
	cmd.Flags().BoolVarP(&force, "force", "f", false, "Skip confirmation prompt")

	return cmd
}

// createRoomMoveCommand creates the room move command
func createRoomMoveCommand(serviceContext any) *cobra.Command {
	var (
		x float64
		y float64
	)

	cmd := &cobra.Command{
		Use:   "move <room-id>",
		Short: "Move a room to a new position",
		Long:  "Move a room to a new position on the floor plan (sets the center point)",
		Example: `  # Move room to position (10, 20)
  arx room move abc123 --x 10 --y 20`,
		Args: cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			ctx := context.Background()
			roomID := args[0]

			// Get service from context
			sc, ok := serviceContext.(RoomServiceProvider)
			if !ok {
				return fmt.Errorf("service context is not available")
			}
			roomUC := sc.GetRoomUseCase()

			// Get existing room
			room, err := roomUC.GetRoom(ctx, types.FromString(roomID))
			if err != nil {
				return fmt.Errorf("failed to get room: %w", err)
			}

			// Update location
			location := &domain.Location{
				X: x,
				Y: y,
				Z: 0, // Floor level
			}

			// Create update request
			req := &domain.UpdateRoomRequest{
				ID:       room.ID,
				Location: location,
			}

			// Update room
			updatedRoom, err := roomUC.UpdateRoom(ctx, req)
			if err != nil {
				return fmt.Errorf("failed to move room: %w", err)
			}

			// Print success
			fmt.Printf("✅ Room moved successfully!\n\n")
			fmt.Printf("   Room:     %s (%s)\n", updatedRoom.Name, updatedRoom.Number)
			fmt.Printf("   Position: (%.2f, %.2f)\n", updatedRoom.Location.X, updatedRoom.Location.Y)
			fmt.Printf("\n")

			return nil
		},
	}

	// Add flags
	cmd.Flags().Float64Var(&x, "x", 0, "X coordinate (required)")
	cmd.Flags().Float64Var(&y, "y", 0, "Y coordinate (required)")

	cmd.MarkFlagRequired("x")
	cmd.MarkFlagRequired("y")

	return cmd
}

// createRoomResizeCommand creates the room resize command
func createRoomResizeCommand(serviceContext any) *cobra.Command {
	var (
		width  float64
		height float64
	)

	cmd := &cobra.Command{
		Use:   "resize <room-id>",
		Short: "Resize a room",
		Long:  "Resize a room by setting its width and height dimensions",
		Example: `  # Resize room to 30x20 meters
  arx room resize abc123 --width 30 --height 20`,
		Args: cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			ctx := context.Background()
			roomID := args[0]

			// Get service from context
			sc, ok := serviceContext.(RoomServiceProvider)
			if !ok {
				return fmt.Errorf("service context is not available")
			}
			roomUC := sc.GetRoomUseCase()

			// Get existing room
			room, err := roomUC.GetRoom(ctx, types.FromString(roomID))
			if err != nil {
				return fmt.Errorf("failed to get room: %w", err)
			}

			// Create update request
			req := &domain.UpdateRoomRequest{
				ID:     room.ID,
				Width:  &width,
				Height: &height,
			}

			// Update room
			updatedRoom, err := roomUC.UpdateRoom(ctx, req)
			if err != nil {
				return fmt.Errorf("failed to resize room: %w", err)
			}

			// Print success
			fmt.Printf("✅ Room resized successfully!\n\n")
			fmt.Printf("   Room:       %s (%s)\n", updatedRoom.Name, updatedRoom.Number)
			fmt.Printf("   Dimensions: %.2f x %.2f meters\n", updatedRoom.Width, updatedRoom.Height)
			fmt.Printf("   Area:       %.2f m²\n", updatedRoom.Width*updatedRoom.Height)
			fmt.Printf("\n")

			return nil
		},
	}

	// Add flags
	cmd.Flags().Float64Var(&width, "width", 0, "Width in meters (required)")
	cmd.Flags().Float64Var(&height, "height", 0, "Height in meters (required)")

	cmd.MarkFlagRequired("width")
	cmd.MarkFlagRequired("height")

	return cmd
}
