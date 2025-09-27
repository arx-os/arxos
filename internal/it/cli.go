package it

import (
	"bufio"
	"fmt"
	"os"
	"strconv"
	"strings"
	"time"

	"github.com/spf13/cobra"
)

// ITCLI provides command-line interface for IT management
type ITCLI struct {
	itManager *ITManager
}

// NewITCLI creates a new IT CLI
func NewITCLI(itManager *ITManager) *ITCLI {
	return &ITCLI{
		itManager: itManager,
	}
}

// GetCommands returns IT CLI commands
func (cli *ITCLI) GetCommands() []*cobra.Command {
	return []*cobra.Command{
		cli.getAssetCommand(),
		cli.getConfigCommand(),
		cli.getRoomCommand(),
		cli.getWorkOrderCommand(),
		cli.getInventoryCommand(),
		cli.getSummaryCommand(),
		cli.getVersionControlCommand(),
	}
}

// getAssetCommand returns asset management commands
func (cli *ITCLI) getAssetCommand() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "asset",
		Short: "IT asset management commands",
	}

	cmd.AddCommand(&cobra.Command{
		Use:   "list [building-path]",
		Short: "List assets in a building or room",
		Args:  cobra.MaximumNArgs(1),
		Run: func(cmd *cobra.Command, args []string) {
			if len(args) > 0 {
				cli.listAssetsByPath(args[0])
			} else {
				cli.listAllAssets()
			}
		},
	})

	cmd.AddCommand(&cobra.Command{
		Use:   "create",
		Short: "Create a new asset",
		Run: func(cmd *cobra.Command, args []string) {
			cli.createAsset()
		},
	})

	cmd.AddCommand(&cobra.Command{
		Use:   "add-to-room <asset-id> <room-path>",
		Short: "Add asset to a room",
		Args:  cobra.ExactArgs(2),
		Run: func(cmd *cobra.Command, args []string) {
			cli.addAssetToRoom(args[0], args[1])
		},
	})

	cmd.AddCommand(&cobra.Command{
		Use:   "remove-from-room <asset-id> <room-path>",
		Short: "Remove asset from a room",
		Args:  cobra.ExactArgs(2),
		Run: func(cmd *cobra.Command, args []string) {
			cli.removeAssetFromRoom(args[0], args[1])
		},
	})

	return cmd
}

// getConfigCommand returns configuration management commands
func (cli *ITCLI) getConfigCommand() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "config",
		Short: "Configuration management commands",
	}

	cmd.AddCommand(&cobra.Command{
		Use:   "list",
		Short: "List configurations",
		Run: func(cmd *cobra.Command, args []string) {
			cli.listConfigurations()
		},
	})

	cmd.AddCommand(&cobra.Command{
		Use:   "create",
		Short: "Create a new configuration",
		Run: func(cmd *cobra.Command, args []string) {
			cli.createConfiguration()
		},
	})

	cmd.AddCommand(&cobra.Command{
		Use:   "create-from-template <template-id> <asset-type> <room-path>",
		Short: "Create configuration from template",
		Args:  cobra.ExactArgs(3),
		Run: func(cmd *cobra.Command, args []string) {
			cli.createConfigFromTemplate(args[0], args[1], args[2])
		},
	})

	cmd.AddCommand(&cobra.Command{
		Use:   "templates",
		Short: "List configuration templates",
		Run: func(cmd *cobra.Command, args []string) {
			cli.listConfigTemplates()
		},
	})

	return cmd
}

// getRoomCommand returns room setup commands
func (cli *ITCLI) getRoomCommand() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "room",
		Short: "Room setup management commands",
	}

	cmd.AddCommand(&cobra.Command{
		Use:   "setup <room-path> <setup-type>",
		Short: "Create room setup",
		Args:  cobra.ExactArgs(2),
		Run: func(cmd *cobra.Command, args []string) {
			cli.createRoomSetup(args[0], args[1])
		},
	})

	cmd.AddCommand(&cobra.Command{
		Use:   "summary <room-path>",
		Short: "Show room setup summary",
		Args:  cobra.ExactArgs(1),
		Run: func(cmd *cobra.Command, args []string) {
			cli.showRoomSummary(args[0])
		},
	})

	cmd.AddCommand(&cobra.Command{
		Use:   "list [building-path]",
		Short: "List room setups",
		Args:  cobra.MaximumNArgs(1),
		Run: func(cmd *cobra.Command, args []string) {
			if len(args) > 0 {
				cli.listRoomSetupsByBuilding(args[0])
			} else {
				cli.listAllRoomSetups()
			}
		},
	})

	cmd.AddCommand(&cobra.Command{
		Use:   "clone <source-room-path> <dest-room-path>",
		Short: "Clone room setup",
		Args:  cobra.ExactArgs(2),
		Run: func(cmd *cobra.Command, args []string) {
			cli.cloneRoomSetup(args[0], args[1])
		},
	})

	return cmd
}

// getWorkOrderCommand returns work order management commands
func (cli *ITCLI) getWorkOrderCommand() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "workorder",
		Short: "Work order management commands",
	}

	cmd.AddCommand(&cobra.Command{
		Use:   "create <room-path>",
		Short: "Create work order for room",
		Args:  cobra.ExactArgs(1),
		Run: func(cmd *cobra.Command, args []string) {
			cli.createWorkOrder(args[0])
		},
	})

	cmd.AddCommand(&cobra.Command{
		Use:   "list [room-path]",
		Short: "List work orders",
		Args:  cobra.MaximumNArgs(1),
		Run: func(cmd *cobra.Command, args []string) {
			if len(args) > 0 {
				cli.listWorkOrdersByRoom(args[0])
			} else {
				cli.listAllWorkOrders()
			}
		},
	})

	cmd.AddCommand(&cobra.Command{
		Use:   "status <work-order-id> <status>",
		Short: "Update work order status",
		Args:  cobra.ExactArgs(2),
		Run: func(cmd *cobra.Command, args []string) {
			cli.updateWorkOrderStatus(args[0], args[1])
		},
	})

	return cmd
}

// getInventoryCommand returns inventory management commands
func (cli *ITCLI) getInventoryCommand() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "inventory",
		Short: "Inventory management commands",
	}

	cmd.AddCommand(&cobra.Command{
		Use:   "parts",
		Short: "List parts inventory",
		Run: func(cmd *cobra.Command, args []string) {
			cli.listParts()
		},
	})

	cmd.AddCommand(&cobra.Command{
		Use:   "low-stock",
		Short: "List low stock parts",
		Run: func(cmd *cobra.Command, args []string) {
			cli.listLowStockParts()
		},
	})

	cmd.AddCommand(&cobra.Command{
		Use:   "reorder",
		Short: "Generate reorder report",
		Run: func(cmd *cobra.Command, args []string) {
			cli.generateReorderReport()
		},
	})

	cmd.AddCommand(&cobra.Command{
		Use:   "add-part",
		Short: "Add new part to inventory",
		Run: func(cmd *cobra.Command, args []string) {
			cli.addPart()
		},
	})

	return cmd
}

// getSummaryCommand returns summary commands
func (cli *ITCLI) getSummaryCommand() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "summary",
		Short: "IT summary commands",
	}

	cmd.AddCommand(&cobra.Command{
		Use:   "room <room-path>",
		Short: "Show room IT summary",
		Args:  cobra.ExactArgs(1),
		Run: func(cmd *cobra.Command, args []string) {
			cli.showRoomSummary(args[0])
		},
	})

	cmd.AddCommand(&cobra.Command{
		Use:   "building <building-path>",
		Short: "Show building IT summary",
		Args:  cobra.ExactArgs(1),
		Run: func(cmd *cobra.Command, args []string) {
			cli.showBuildingSummary(args[0])
		},
	})

	cmd.AddCommand(&cobra.Command{
		Use:   "overview",
		Short: "Show overall IT overview",
		Run: func(cmd *cobra.Command, args []string) {
			cli.showITOverview()
		},
	})

	return cmd
}

// listAssetsByPath lists assets in a specific building or room
func (cli *ITCLI) listAssetsByPath(path string) {
	// Validate path
	err := cli.itManager.ValidateBuildingPath(path)
	if err != nil {
		fmt.Printf("Invalid path: %v\n", err)
		return
	}

	// Get building, floor, room from path
	building, floor, room, err := cli.itManager.GetPathComponents(path)
	if err != nil {
		fmt.Printf("Error parsing path: %v\n", err)
		return
	}

	fmt.Printf("Assets in %s (Building: %s, Floor: %s, Room: %s)\n", path, building, floor, room)
	fmt.Println("=" + strings.Repeat("=", len(path)+50))

	// Get assets by room path
	assets, err := cli.itManager.GetAssetsByRoomPath(path)
	if err != nil {
		fmt.Printf("Error getting assets: %v\n", err)
		return
	}

	if len(assets) == 0 {
		fmt.Println("No assets found in this room")
		return
	}

	for _, asset := range assets {
		fmt.Printf("ID: %s\n", asset.ID)
		fmt.Printf("Name: %s\n", asset.Name)
		fmt.Printf("Type: %s\n", asset.Type)
		fmt.Printf("Brand: %s\n", asset.Brand)
		fmt.Printf("Model: %s\n", asset.Model)
		fmt.Printf("Status: %s\n", asset.Status)
		fmt.Printf("Condition: %s\n", asset.Condition)
		fmt.Printf("Serial: %s\n", asset.SerialNumber)
		fmt.Printf("Asset Tag: %s\n", asset.AssetTag)
		fmt.Printf("Value: $%.2f\n", asset.CurrentValue)
		fmt.Println("---")
	}
}

// listAllAssets lists all assets
func (cli *ITCLI) listAllAssets() {
	fmt.Println("All IT Assets")
	fmt.Println("=============")

	assets := cli.itManager.assetManager.GetAssets(AssetFilter{})
	if len(assets) == 0 {
		fmt.Println("No assets found")
		return
	}

	for _, asset := range assets {
		fmt.Printf("ID: %s | %s | %s %s | %s | %s\n",
			asset.ID, asset.Name, asset.Brand, asset.Model, asset.Status, asset.Location.Room)
	}
}

// createAsset creates a new asset
func (cli *ITCLI) createAsset() {
	asset := &ITAsset{
		Name:         cli.promptForString("Asset Name: "),
		Type:         AssetType(cli.promptForString("Asset Type: ")),
		Category:     cli.promptForString("Category: "),
		Brand:        cli.promptForString("Brand: "),
		Model:        cli.promptForString("Model: "),
		SerialNumber: cli.promptForString("Serial Number: "),
		AssetTag:     cli.promptForString("Asset Tag: "),
		Status:       AssetStatusActive,
		Condition:    AssetConditionGood,
		Location: Location{
			Building: cli.promptForString("Building: "),
			Floor:    cli.promptForString("Floor: "),
			Room:     cli.promptForString("Room: "),
		},
		PurchasePrice: cli.promptForFloat("Purchase Price: $"),
		CurrentValue:  cli.promptForFloat("Current Value: $"),
		Supplier:      cli.promptForString("Supplier: "),
		Metadata:      make(map[string]interface{}),
	}

	err := cli.itManager.assetManager.CreateAsset(asset)
	if err != nil {
		fmt.Printf("Error creating asset: %v\n", err)
		return
	}

	fmt.Printf("Asset created successfully: %s\n", asset.ID)
}

// addAssetToRoom adds an asset to a room
func (cli *ITCLI) addAssetToRoom(assetID, roomPath string) {
	// Get position from user
	position := Position{
		X:         cli.promptForFloat("X position (feet from left wall): "),
		Y:         cli.promptForFloat("Y position (feet from front wall): "),
		Z:         cli.promptForFloat("Z position (height in feet): "),
		Rotation:  cli.promptForFloat("Rotation (degrees): "),
		MountType: cli.promptForString("Mount type (wall/ceiling/floor/desk): "),
	}

	isPrimary := cli.promptForString("Is this the primary asset? (y/n): ") == "y"

	err := cli.itManager.AddAssetToRoom(assetID, roomPath, position, isPrimary)
	if err != nil {
		fmt.Printf("Error adding asset to room: %v\n", err)
		return
	}

	fmt.Printf("Asset %s added to room %s\n", assetID, roomPath)
}

// removeAssetFromRoom removes an asset from a room
func (cli *ITCLI) removeAssetFromRoom(assetID, roomPath string) {
	err := cli.itManager.RemoveAssetFromRoom(assetID, roomPath)
	if err != nil {
		fmt.Printf("Error removing asset from room: %v\n", err)
		return
	}

	fmt.Printf("Asset %s removed from room %s\n", assetID, roomPath)
}

// listConfigurations lists all configurations
func (cli *ITCLI) listConfigurations() {
	fmt.Println("IT Configurations")
	fmt.Println("=================")

	configs := cli.itManager.configManager.GetConfigurations(ConfigFilter{})
	if len(configs) == 0 {
		fmt.Println("No configurations found")
		return
	}

	for _, config := range configs {
		fmt.Printf("ID: %s | %s | %s | %s\n",
			config.ID, config.Name, config.AssetType, config.CreatedBy)
	}
}

// createConfiguration creates a new configuration
func (cli *ITCLI) createConfiguration() {
	config := &Configuration{
		Name:         cli.promptForString("Configuration Name: "),
		Description:  cli.promptForString("Description: "),
		AssetType:    AssetType(cli.promptForString("Asset Type: ")),
		Components:   []Component{},
		Software:     []Software{},
		UserSettings: make(map[string]interface{}),
		IsTemplate:   cli.promptForString("Is this a template? (y/n): ") == "y",
		CreatedBy:    cli.promptForString("Created By: "),
	}

	// Add components
	for {
		addComponent := cli.promptForString("Add component? (y/n): ")
		if addComponent != "y" {
			break
		}

		component := Component{
			Type:     cli.promptForString("Component Type: "),
			Brand:    cli.promptForString("Brand: "),
			Model:    cli.promptForString("Model: "),
			Quantity: cli.promptForInt("Quantity: "),
			Required: cli.promptForString("Required? (y/n): ") == "y",
			Notes:    cli.promptForString("Notes: "),
		}

		config.Components = append(config.Components, component)
	}

	err := cli.itManager.configManager.CreateConfiguration(config)
	if err != nil {
		fmt.Printf("Error creating configuration: %v\n", err)
		return
	}

	fmt.Printf("Configuration created successfully: %s\n", config.ID)
}

// createConfigFromTemplate creates a configuration from a template
func (cli *ITCLI) createConfigFromTemplate(templateID, assetType, roomPath string) {
	createdBy := cli.promptForString("Created By: ")

	config, err := cli.itManager.CreateConfigurationFromTemplate(templateID, AssetType(assetType), roomPath, createdBy)
	if err != nil {
		fmt.Printf("Error creating configuration from template: %v\n", err)
		return
	}

	fmt.Printf("Configuration created from template: %s\n", config.ID)
}

// listConfigTemplates lists configuration templates
func (cli *ITCLI) listConfigTemplates() {
	fmt.Println("Configuration Templates")
	fmt.Println("=======================")

	templates := cli.itManager.configManager.GetConfigurationTemplates()
	if len(templates) == 0 {
		fmt.Println("No templates found")
		return
	}

	for _, template := range templates {
		fmt.Printf("ID: %s | %s | %s | %s\n",
			template.ID, template.Name, template.AssetType, template.CreatedBy)
	}
}

// createRoomSetup creates a room setup
func (cli *ITCLI) createRoomSetup(roomPath, setupType string) {
	createdBy := cli.promptForString("Created By: ")

	setup, err := cli.itManager.CreateRoomSetupFromPath(roomPath, SetupType(setupType), createdBy)
	if err != nil {
		fmt.Printf("Error creating room setup: %v\n", err)
		return
	}

	fmt.Printf("Room setup created successfully: %s\n", setup.ID)
}

// showRoomSummary shows a room's IT summary
func (cli *ITCLI) showRoomSummary(roomPath string) {
	summary, err := cli.itManager.GetRoomSetupSummary(roomPath)
	if err != nil {
		fmt.Printf("Error getting room summary: %v\n", err)
		return
	}

	fmt.Printf("Room IT Summary: %s\n", roomPath)
	fmt.Println("=" + strings.Repeat("=", len(roomPath)+20))
	fmt.Printf("Setup Type: %s\n", summary.SetupType)
	fmt.Printf("Active: %t\n", summary.IsActive)
	fmt.Printf("Total Assets: %d\n", summary.TotalAssets)
	fmt.Printf("Work Orders: %d (Open: %d)\n", summary.WorkOrders, summary.OpenWorkOrders)
	fmt.Printf("Last Updated: %s\n", summary.LastUpdated.Format("2006-01-02 15:04:05"))

	if len(summary.AssetTypes) > 0 {
		fmt.Println("\nAsset Types:")
		for assetType, count := range summary.AssetTypes {
			fmt.Printf("  %s: %d\n", assetType, count)
		}
	}

	if len(summary.Assets) > 0 {
		fmt.Println("\nAssets:")
		for _, asset := range summary.Assets {
			fmt.Printf("  %s - %s %s (%s)\n", asset.Name, asset.Brand, asset.Model, asset.Status)
		}
	}
}

// listRoomSetupsByBuilding lists room setups for a building
func (cli *ITCLI) listRoomSetupsByBuilding(buildingPath string) {
	fmt.Printf("Room Setups in %s\n", buildingPath)
	fmt.Println("=" + strings.Repeat("=", len(buildingPath)+20))

	// Parse building path to get building name
	pathParts := strings.Split(strings.Trim(buildingPath, "/"), "/")
	if len(pathParts) < 2 {
		fmt.Println("Invalid building path format")
		return
	}

	building := pathParts[1]

	filter := SetupFilter{
		Building: building,
		IsActive: &[]bool{true}[0],
	}

	setups := cli.itManager.configManager.GetRoomSetups(filter)
	if len(setups) == 0 {
		fmt.Println("No room setups found")
		return
	}

	for _, setup := range setups {
		fmt.Printf("Room: %s | Type: %s | Assets: %d | Active: %t\n",
			setup.Room.Room, setup.SetupType, len(setup.Assets), setup.IsActive)
	}
}

// listAllRoomSetups lists all room setups
func (cli *ITCLI) listAllRoomSetups() {
	fmt.Println("All Room Setups")
	fmt.Println("===============")

	setups := cli.itManager.configManager.GetRoomSetups(SetupFilter{})
	if len(setups) == 0 {
		fmt.Println("No room setups found")
		return
	}

	for _, setup := range setups {
		fmt.Printf("ID: %s | %s | %s | %s | Assets: %d\n",
			setup.ID, setup.Name, setup.Room.Building, setup.Room.Room, len(setup.Assets))
	}
}

// cloneRoomSetup clones a room setup
func (cli *ITCLI) cloneRoomSetup(sourceRoomPath, destRoomPath string) {
	createdBy := cli.promptForString("Created By: ")

	// Get source setup
	sourceSetup, err := cli.itManager.GetRoomSetupByPath(sourceRoomPath)
	if err != nil {
		fmt.Printf("Error getting source setup: %v\n", err)
		return
	}

	// Parse destination path
	destBuilding, destFloor, destRoom, err := cli.itManager.GetPathComponents(destRoomPath)
	if err != nil {
		fmt.Printf("Error parsing destination path: %v\n", err)
		return
	}

	destLocation := Location{
		Building:   destBuilding,
		Floor:      destFloor,
		Room:       destRoom,
		RoomNumber: destRoom,
	}

	// Clone the setup
	clone, err := cli.itManager.configManager.CloneRoomSetup(sourceSetup.ID, fmt.Sprintf("%s - %s", destRoom, sourceSetup.SetupType), destLocation, createdBy)
	if err != nil {
		fmt.Printf("Error cloning room setup: %v\n", err)
		return
	}

	fmt.Printf("Room setup cloned successfully: %s\n", clone.ID)
}

// createWorkOrder creates a work order for a room
func (cli *ITCLI) createWorkOrder(roomPath string) {
	title := cli.promptForString("Work Order Title: ")
	description := cli.promptForString("Description: ")
	workOrderType := WorkOrderType(cli.promptForString("Type (installation/repair/maintenance/upgrade/configuration/removal/inspection/other): "))
	priority := Priority(cli.promptForString("Priority (low/medium/high/critical/emergency): "))
	requestedBy := cli.promptForString("Requested By: ")

	workOrder, err := cli.itManager.CreateWorkOrderForRoom(roomPath, title, description, workOrderType, priority, requestedBy)
	if err != nil {
		fmt.Printf("Error creating work order: %v\n", err)
		return
	}

	fmt.Printf("Work order created successfully: %s\n", workOrder.ID)
}

// listWorkOrdersByRoom lists work orders for a room
func (cli *ITCLI) listWorkOrdersByRoom(roomPath string) {
	workOrders, err := cli.itManager.GetWorkOrdersByRoomPath(roomPath)
	if err != nil {
		fmt.Printf("Error getting work orders: %v\n", err)
		return
	}

	fmt.Printf("Work Orders for %s\n", roomPath)
	fmt.Println("=" + strings.Repeat("=", len(roomPath)+20))

	if len(workOrders) == 0 {
		fmt.Println("No work orders found")
		return
	}

	for _, workOrder := range workOrders {
		fmt.Printf("ID: %s | %s | %s | %s | %s\n",
			workOrder.ID, workOrder.Title, workOrder.Type, workOrder.Priority, workOrder.Status)
	}
}

// listAllWorkOrders lists all work orders
func (cli *ITCLI) listAllWorkOrders() {
	fmt.Println("All Work Orders")
	fmt.Println("===============")

	workOrders := cli.itManager.workOrderManager.GetWorkOrders(WorkOrderFilter{})
	if len(workOrders) == 0 {
		fmt.Println("No work orders found")
		return
	}

	for _, workOrder := range workOrders {
		fmt.Printf("ID: %s | %s | %s | %s | %s | %s\n",
			workOrder.ID, workOrder.Title, workOrder.Type, workOrder.Priority, workOrder.Status, workOrder.Location.Room)
	}
}

// updateWorkOrderStatus updates a work order status
func (cli *ITCLI) updateWorkOrderStatus(workOrderID, status string) {
	workOrder, err := cli.itManager.workOrderManager.GetWorkOrder(workOrderID)
	if err != nil {
		fmt.Printf("Error getting work order: %v\n", err)
		return
	}

	workOrder.Status = WorkOrderStatus(status)
	workOrder.UpdatedAt = time.Now()

	if status == string(WorkOrderStatusCompleted) {
		now := time.Now()
		workOrder.CompletedAt = &now
	}

	err = cli.itManager.workOrderManager.UpdateWorkOrder(workOrderID, workOrder)
	if err != nil {
		fmt.Printf("Error updating work order: %v\n", err)
		return
	}

	fmt.Printf("Work order %s status updated to %s\n", workOrderID, status)
}

// listParts lists all parts
func (cli *ITCLI) listParts() {
	fmt.Println("Parts Inventory")
	fmt.Println("===============")

	parts := cli.itManager.inventoryManager.GetParts(PartFilter{})
	if len(parts) == 0 {
		fmt.Println("No parts found")
		return
	}

	for _, part := range parts {
		fmt.Printf("ID: %s | %s | %s | Qty: %d | Status: %s | $%.2f\n",
			part.ID, part.Name, part.PartNumber, part.Quantity, part.Status, part.UnitPrice)
	}
}

// listLowStockParts lists low stock parts
func (cli *ITCLI) listLowStockParts() {
	fmt.Println("Low Stock Parts")
	fmt.Println("===============")

	parts := cli.itManager.inventoryManager.GetLowStockParts()
	if len(parts) == 0 {
		fmt.Println("No low stock parts found")
		return
	}

	for _, part := range parts {
		fmt.Printf("ID: %s | %s | Qty: %d/%d | $%.2f\n",
			part.ID, part.Name, part.Quantity, part.MinQuantity, part.UnitPrice)
	}
}

// generateReorderReport generates a reorder report
func (cli *ITCLI) generateReorderReport() {
	fmt.Println("Reorder Report")
	fmt.Println("==============")

	reorderItems := cli.itManager.inventoryManager.GenerateReorderReport()
	if len(reorderItems) == 0 {
		fmt.Println("No parts need reordering")
		return
	}

	totalCost := 0.0
	for _, item := range reorderItems {
		fmt.Printf("Part: %s | Current: %d | Min: %d | Order: %d | Cost: $%.2f\n",
			item.Name, item.CurrentQuantity, item.MinQuantity, item.SuggestedOrder, item.TotalCost)
		totalCost += item.TotalCost
	}

	fmt.Printf("\nTotal Reorder Cost: $%.2f\n", totalCost)
}

// addPart adds a new part to inventory
func (cli *ITCLI) addPart() {
	part := &Part{
		Name:           cli.promptForString("Part Name: "),
		Description:    cli.promptForString("Description: "),
		PartNumber:     cli.promptForString("Part Number: "),
		Category:       cli.promptForString("Category: "),
		Brand:          cli.promptForString("Brand: "),
		Model:          cli.promptForString("Model: "),
		Supplier:       cli.promptForString("Supplier: "),
		UnitPrice:      cli.promptForFloat("Unit Price: $"),
		Quantity:       cli.promptForInt("Quantity: "),
		MinQuantity:    cli.promptForInt("Minimum Quantity: "),
		MaxQuantity:    cli.promptForInt("Maximum Quantity: "),
		Location:       cli.promptForString("Storage Location: "),
		CompatibleWith: []string{},
		Metadata:       make(map[string]interface{}),
	}

	err := cli.itManager.inventoryManager.CreatePart(part)
	if err != nil {
		fmt.Printf("Error creating part: %v\n", err)
		return
	}

	fmt.Printf("Part created successfully: %s\n", part.ID)
}

// showBuildingSummary shows a building's IT summary
func (cli *ITCLI) showBuildingSummary(buildingPath string) {
	summary, err := cli.itManager.GetBuildingITSummary(buildingPath)
	if err != nil {
		fmt.Printf("Error getting building summary: %v\n", err)
		return
	}

	fmt.Printf("Building IT Summary: %s\n", buildingPath)
	fmt.Println("=" + strings.Repeat("=", len(buildingPath)+25))
	fmt.Printf("Total Rooms: %d\n", summary.TotalRooms)
	fmt.Printf("Total Assets: %d\n", summary.TotalAssets)
	fmt.Printf("Total Work Orders: %d (Open: %d)\n", summary.TotalWorkOrders, summary.OpenWorkOrders)

	if len(summary.AssetTypes) > 0 {
		fmt.Println("\nAsset Types:")
		for assetType, count := range summary.AssetTypes {
			fmt.Printf("  %s: %d\n", assetType, count)
		}
	}

	if len(summary.SetupTypes) > 0 {
		fmt.Println("\nSetup Types:")
		for setupType, count := range summary.SetupTypes {
			fmt.Printf("  %s: %d\n", setupType, count)
		}
	}

	if len(summary.Rooms) > 0 {
		fmt.Println("\nRooms:")
		for _, room := range summary.Rooms {
			fmt.Printf("  %s: %d assets, %d work orders\n",
				room.RoomPath, room.TotalAssets, room.WorkOrders)
		}
	}
}

// showITOverview shows overall IT overview
func (cli *ITCLI) showITOverview() {
	cli.itManager.UpdateMetrics()
	metrics := cli.itManager.GetMetrics()

	fmt.Println("IT Management Overview")
	fmt.Println("=====================")
	fmt.Printf("Total Assets: %d (Active: %d)\n", metrics.TotalAssets, metrics.ActiveAssets)
	fmt.Printf("Total Configurations: %d\n", metrics.TotalConfigurations)
	fmt.Printf("Total Room Setups: %d\n", metrics.TotalRoomSetups)
	fmt.Printf("Total Work Orders: %d (Open: %d)\n", metrics.TotalWorkOrders, metrics.OpenWorkOrders)
	fmt.Printf("Total Parts: %d (Low Stock: %d)\n", metrics.TotalParts, metrics.LowStockParts)
	fmt.Printf("Total Value: $%.2f\n", metrics.TotalValue)
	fmt.Printf("Asset Utilization: %.1f%%\n", metrics.AssetUtilization*100)
	fmt.Printf("Work Order Efficiency: %.1f%%\n", metrics.WorkOrderEfficiency*100)
	fmt.Printf("Inventory Accuracy: %.1f%%\n", metrics.InventoryAccuracy*100)
}

// Helper methods for user input
func (cli *ITCLI) promptForString(prompt string) string {
	fmt.Print(prompt)
	reader := bufio.NewReader(os.Stdin)
	input, _ := reader.ReadString('\n')
	return strings.TrimSpace(input)
}

func (cli *ITCLI) promptForInt(prompt string) int {
	for {
		input := cli.promptForString(prompt)
		if value, err := strconv.Atoi(input); err == nil {
			return value
		}
		fmt.Println("Invalid input. Please enter a number.")
	}
}

func (cli *ITCLI) promptForFloat(prompt string) float64 {
	for {
		input := cli.promptForString(prompt)
		if value, err := strconv.ParseFloat(input, 64); err == nil {
			return value
		}
		fmt.Println("Invalid input. Please enter a number.")
	}
}

// getVersionControlCommand returns version control commands (Git-like operations)
func (cli *ITCLI) getVersionControlCommand() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "vc",
		Short: "Version control commands for room configurations (Git-like operations)",
		Long:  "Version control commands that treat room configurations like Git repositories",
	}

	// Branch commands
	cmd.AddCommand(&cobra.Command{
		Use:   "branch create <room-path> <branch-name> [template]",
		Short: "Create a new branch for room configuration",
		Args:  cobra.RangeArgs(2, 3),
		Run: func(cmd *cobra.Command, args []string) {
			roomPath := args[0]
			branchName := args[1]
			template := "main"
			if len(args) > 2 {
				template = args[2]
			}

			err := cli.itManager.CreateBranch(roomPath, branchName, template)
			if err != nil {
				fmt.Printf("Error creating branch: %v\n", err)
				return
			}

			fmt.Printf("Branch '%s' created for room %s from template '%s'\n", branchName, roomPath, template)
		},
	})

	// Commit commands
	cmd.AddCommand(&cobra.Command{
		Use:   "commit <room-path> <branch> <message> [author]",
		Short: "Commit changes to room configuration",
		Args:  cobra.RangeArgs(3, 4),
		Run: func(cmd *cobra.Command, args []string) {
			roomPath := args[0]
			branch := args[1]
			message := args[2]
			author := "system"
			if len(args) > 3 {
				author = args[3]
			}

			// For now, create empty changes - in real implementation, this would capture actual changes
			changes := []*HardwareChange{}

			commit, err := cli.itManager.CommitChanges(roomPath, branch, message, author, changes)
			if err != nil {
				fmt.Printf("Error committing changes: %v\n", err)
				return
			}

			fmt.Printf("Changes committed: %s\n", commit.ID)
			fmt.Printf("Message: %s\n", commit.Message)
			fmt.Printf("Author: %s\n", commit.Author)
		},
	})

	// Push commands
	cmd.AddCommand(&cobra.Command{
		Use:   "push <room-path> <branch>",
		Short: "Push changes to physical deployment",
		Args:  cobra.ExactArgs(2),
		Run: func(cmd *cobra.Command, args []string) {
			roomPath := args[0]
			branch := args[1]

			err := cli.itManager.PushChanges(roomPath, branch)
			if err != nil {
				fmt.Printf("Error pushing changes: %v\n", err)
				return
			}

			fmt.Printf("Changes pushed to physical deployment for room %s (branch: %s)\n", roomPath, branch)
		},
	})

	// Pull commands
	cmd.AddCommand(&cobra.Command{
		Use:   "pull <room-path> <branch>",
		Short: "Pull latest changes from physical deployment",
		Args:  cobra.ExactArgs(2),
		Run: func(cmd *cobra.Command, args []string) {
			roomPath := args[0]
			branch := args[1]

			err := cli.itManager.PullChanges(roomPath, branch)
			if err != nil {
				fmt.Printf("Error pulling changes: %v\n", err)
				return
			}

			fmt.Printf("Changes pulled from physical deployment for room %s (branch: %s)\n", roomPath, branch)
		},
	})

	// Log commands
	cmd.AddCommand(&cobra.Command{
		Use:   "log <room-path> [branch]",
		Short: "Show commit history for room",
		Args:  cobra.RangeArgs(1, 2),
		Run: func(cmd *cobra.Command, args []string) {
			roomPath := args[0]
			branch := "main"
			if len(args) > 1 {
				branch = args[1]
			}

			history, err := cli.itManager.GetRoomHistory(roomPath, branch)
			if err != nil {
				fmt.Printf("Error getting room history: %v\n", err)
				return
			}

			fmt.Printf("Commit history for room %s (branch: %s)\n", roomPath, branch)
			fmt.Println("=" + strings.Repeat("=", len(roomPath)+len(branch)+30))

			for _, commit := range history {
				fmt.Printf("commit %s\n", commit.ID)
				fmt.Printf("Author: %s\n", commit.Author)
				fmt.Printf("Date: %s\n", commit.Timestamp.Format("Mon Jan 2 15:04:05 2006 -0700"))
				fmt.Printf("Message: %s\n", commit.Message)
				if len(commit.Changes) > 0 {
					fmt.Printf("Changes: %d hardware changes\n", len(commit.Changes))
				}
				fmt.Println()
			}
		},
	})

	// Rollback commands
	cmd.AddCommand(&cobra.Command{
		Use:   "rollback <room-path> <branch> <commit-id>",
		Short: "Rollback room to specific commit",
		Args:  cobra.ExactArgs(3),
		Run: func(cmd *cobra.Command, args []string) {
			roomPath := args[0]
			branch := args[1]
			commitID := args[2]

			err := cli.itManager.RollbackRoom(roomPath, branch, commitID)
			if err != nil {
				fmt.Printf("Error rolling back room: %v\n", err)
				return
			}

			fmt.Printf("Room %s rolled back to commit %s\n", roomPath, commitID)
		},
	})

	// Pull request commands
	cmd.AddCommand(&cobra.Command{
		Use:   "pr create <room-path> <title> <description> <created-by> <base-branch> <head-branch>",
		Short: "Create a pull request for room configuration changes",
		Args:  cobra.ExactArgs(6),
		Run: func(cmd *cobra.Command, args []string) {
			roomPath := args[0]
			title := args[1]
			description := args[2]
			createdBy := args[3]
			baseBranch := args[4]
			headBranch := args[5]

			pr, err := cli.itManager.CreatePullRequest(roomPath, title, description, createdBy, baseBranch, headBranch)
			if err != nil {
				fmt.Printf("Error creating pull request: %v\n", err)
				return
			}

			fmt.Printf("Pull request created: %s\n", pr.ID)
			fmt.Printf("Title: %s\n", pr.Title)
			fmt.Printf("Room: %s\n", pr.RoomPath)
			fmt.Printf("Base: %s -> Head: %s\n", pr.BaseBranch, pr.HeadBranch)
		},
	})

	cmd.AddCommand(&cobra.Command{
		Use:   "pr review <pr-id> <approved> <reviewer>",
		Short: "Review a pull request",
		Args:  cobra.ExactArgs(3),
		Run: func(cmd *cobra.Command, args []string) {
			prID := args[0]
			approved := args[1] == "true"
			reviewer := args[2]

			err := cli.itManager.ReviewPullRequest(prID, approved, reviewer)
			if err != nil {
				fmt.Printf("Error reviewing pull request: %v\n", err)
				return
			}

			status := "rejected"
			if approved {
				status = "approved"
			}
			fmt.Printf("Pull request %s %s by %s\n", prID, status, reviewer)
		},
	})

	cmd.AddCommand(&cobra.Command{
		Use:   "pr merge <pr-id> [deploy]",
		Short: "Merge a pull request",
		Args:  cobra.RangeArgs(1, 2),
		Run: func(cmd *cobra.Command, args []string) {
			prID := args[0]
			deploy := false
			if len(args) > 1 {
				deploy = args[1] == "true"
			}

			err := cli.itManager.MergePullRequest(prID, deploy)
			if err != nil {
				fmt.Printf("Error merging pull request: %v\n", err)
				return
			}

			fmt.Printf("Pull request %s merged", prID)
			if deploy {
				fmt.Printf(" and deployed")
			}
			fmt.Println()
		},
	})

	cmd.AddCommand(&cobra.Command{
		Use:   "pr list <room-path>",
		Short: "List pull requests for a room",
		Args:  cobra.ExactArgs(1),
		Run: func(cmd *cobra.Command, args []string) {
			roomPath := args[0]

			prs, err := cli.itManager.ListPullRequests(roomPath)
			if err != nil {
				fmt.Printf("Error listing pull requests: %v\n", err)
				return
			}

			fmt.Printf("Pull requests for room %s\n", roomPath)
			fmt.Println("=" + strings.Repeat("=", len(roomPath)+25))

			for _, pr := range prs {
				fmt.Printf("PR %s: %s (%s)\n", pr.ID, pr.Title, pr.Status)
				fmt.Printf("  Created by: %s\n", pr.CreatedBy)
				fmt.Printf("  Base: %s -> Head: %s\n", pr.BaseBranch, pr.HeadBranch)
				fmt.Printf("  Created: %s\n", pr.CreatedAt.Format("2006-01-02 15:04:05"))
				fmt.Println()
			}
		},
	})

	// Feature request commands
	cmd.AddCommand(&cobra.Command{
		Use:   "feature-request create <room-path> <title> <description> <priority> <requested-by>",
		Short: "Create a feature request for room configuration changes",
		Args:  cobra.ExactArgs(5),
		Run: func(cmd *cobra.Command, args []string) {
			roomPath := args[0]
			title := args[1]
			description := args[2]
			priority := args[3]
			requestedBy := args[4]

			pr, err := cli.itManager.CreateFeatureRequest(roomPath, title, description, priority, requestedBy)
			if err != nil {
				fmt.Printf("Error creating feature request: %v\n", err)
				return
			}

			fmt.Printf("Feature request created: %s\n", pr.ID)
			fmt.Printf("Title: %s\n", pr.Title)
			fmt.Printf("Priority: %s\n", priority)
			fmt.Printf("Requested by: %s\n", requestedBy)
		},
	})

	// Emergency fix commands
	cmd.AddCommand(&cobra.Command{
		Use:   "emergency-fix create <room-path> <issue> <priority> <reported-by>",
		Short: "Create an emergency fix for room configuration",
		Args:  cobra.ExactArgs(4),
		Run: func(cmd *cobra.Command, args []string) {
			roomPath := args[0]
			issue := args[1]
			priority := args[2]
			reportedBy := args[3]

			pr, err := cli.itManager.CreateEmergencyFix(roomPath, issue, priority, reportedBy)
			if err != nil {
				fmt.Printf("Error creating emergency fix: %v\n", err)
				return
			}

			fmt.Printf("Emergency fix created: %s\n", pr.ID)
			fmt.Printf("Issue: %s\n", issue)
			fmt.Printf("Priority: %s\n", priority)
			fmt.Printf("Reported by: %s\n", reportedBy)
		},
	})

	return cmd
}
