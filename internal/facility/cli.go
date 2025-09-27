package facility

import (
	"fmt"
	"os"
	"strconv"
	"strings"
	"time"

	"github.com/spf13/cobra"
)

// FacilityCLI provides command-line interface for facility management
type FacilityCLI struct {
	facilityManager    *FacilityManager
	workOrderManager   *WorkOrderManager
	maintenanceManager *MaintenanceManager
	inspectionManager  *InspectionManager
	vendorManager      *VendorManager
}

// NewFacilityCLI creates a new facility CLI
func NewFacilityCLI() *FacilityCLI {
	facilityManager := NewFacilityManager()
	workOrderManager := NewWorkOrderManager(facilityManager)
	maintenanceManager := NewMaintenanceManager(facilityManager, workOrderManager)
	inspectionManager := NewInspectionManager(facilityManager, workOrderManager)
	vendorManager := NewVendorManager(facilityManager)

	return &FacilityCLI{
		facilityManager:    facilityManager,
		workOrderManager:   workOrderManager,
		maintenanceManager: maintenanceManager,
		inspectionManager:  inspectionManager,
		vendorManager:      vendorManager,
	}
}

// CreateCommands creates the CLI commands
func (cli *FacilityCLI) CreateCommands() *cobra.Command {
	rootCmd := &cobra.Command{
		Use:   "facility",
		Short: "ArxOS Facility Management CLI",
		Long:  "Command-line interface for managing buildings, assets, work orders, maintenance, and inspections",
	}

	// Building commands
	rootCmd.AddCommand(cli.createBuildingCommands())

	// Space commands
	rootCmd.AddCommand(cli.createSpaceCommands())

	// Asset commands
	rootCmd.AddCommand(cli.createAssetCommands())

	// Work order commands
	rootCmd.AddCommand(cli.createWorkOrderCommands())

	// Maintenance commands
	rootCmd.AddCommand(cli.createMaintenanceCommands())

	// Inspection commands
	rootCmd.AddCommand(cli.createInspectionCommands())

	// Vendor commands
	rootCmd.AddCommand(cli.createVendorCommands())

	// Metrics commands
	rootCmd.AddCommand(cli.createMetricsCommands())

	return rootCmd
}

// Building Commands

func (cli *FacilityCLI) createBuildingCommands() *cobra.Command {
	buildingCmd := &cobra.Command{
		Use:   "building",
		Short: "Manage buildings",
		Long:  "Create, read, update, and delete building information",
	}

	// List buildings
	listCmd := &cobra.Command{
		Use:   "list",
		Short: "List all buildings",
		Run: func(cmd *cobra.Command, args []string) {
			buildings := cli.facilityManager.ListBuildings()
			cli.printBuildings(buildings)
		},
	}
	buildingCmd.AddCommand(listCmd)

	// Create building
	createCmd := &cobra.Command{
		Use:   "create",
		Short: "Create a new building",
		Run: func(cmd *cobra.Command, args []string) {
			building := cli.promptForBuilding()
			if err := cli.facilityManager.CreateBuilding(building); err != nil {
				fmt.Printf("Error creating building: %v\n", err)
				os.Exit(1)
			}
			fmt.Printf("Building '%s' created successfully\n", building.Name)
		},
	}
	buildingCmd.AddCommand(createCmd)

	// Get building
	getCmd := &cobra.Command{
		Use:   "get <building-id>",
		Short: "Get building details",
		Args:  cobra.ExactArgs(1),
		Run: func(cmd *cobra.Command, args []string) {
			building, err := cli.facilityManager.GetBuilding(args[0])
			if err != nil {
				fmt.Printf("Error getting building: %v\n", err)
				os.Exit(1)
			}
			cli.printBuilding(building)
		},
	}
	buildingCmd.AddCommand(getCmd)

	// Update building
	updateCmd := &cobra.Command{
		Use:   "update <building-id>",
		Short: "Update building information",
		Args:  cobra.ExactArgs(1),
		Run: func(cmd *cobra.Command, args []string) {
			updates := cli.promptForBuildingUpdates()
			if err := cli.facilityManager.UpdateBuilding(args[0], updates); err != nil {
				fmt.Printf("Error updating building: %v\n", err)
				os.Exit(1)
			}
			fmt.Printf("Building '%s' updated successfully\n", args[0])
		},
	}
	buildingCmd.AddCommand(updateCmd)

	// Delete building
	deleteCmd := &cobra.Command{
		Use:   "delete <building-id>",
		Short: "Delete a building",
		Args:  cobra.ExactArgs(1),
		Run: func(cmd *cobra.Command, args []string) {
			if err := cli.facilityManager.DeleteBuilding(args[0]); err != nil {
				fmt.Printf("Error deleting building: %v\n", err)
				os.Exit(1)
			}
			fmt.Printf("Building '%s' deleted successfully\n", args[0])
		},
	}
	buildingCmd.AddCommand(deleteCmd)

	return buildingCmd
}

// Space Commands

func (cli *FacilityCLI) createSpaceCommands() *cobra.Command {
	spaceCmd := &cobra.Command{
		Use:   "space",
		Short: "Manage spaces",
		Long:  "Create, read, update, and delete space information",
	}

	// List spaces
	listCmd := &cobra.Command{
		Use:   "list",
		Short: "List all spaces",
		Run: func(cmd *cobra.Command, args []string) {
			spaces := cli.facilityManager.ListSpaces()
			cli.printSpaces(spaces)
		},
	}
	spaceCmd.AddCommand(listCmd)

	// List spaces by building
	listByBuildingCmd := &cobra.Command{
		Use:   "list-by-building <building-id>",
		Short: "List spaces in a building",
		Args:  cobra.ExactArgs(1),
		Run: func(cmd *cobra.Command, args []string) {
			spaces := cli.facilityManager.GetSpacesByBuilding(args[0])
			cli.printSpaces(spaces)
		},
	}
	spaceCmd.AddCommand(listByBuildingCmd)

	// Create space
	createCmd := &cobra.Command{
		Use:   "create",
		Short: "Create a new space",
		Run: func(cmd *cobra.Command, args []string) {
			space := cli.promptForSpace()
			if err := cli.facilityManager.CreateSpace(space); err != nil {
				fmt.Printf("Error creating space: %v\n", err)
				os.Exit(1)
			}
			fmt.Printf("Space '%s' created successfully\n", space.Name)
		},
	}
	spaceCmd.AddCommand(createCmd)

	// Get space
	getCmd := &cobra.Command{
		Use:   "get <space-id>",
		Short: "Get space details",
		Args:  cobra.ExactArgs(1),
		Run: func(cmd *cobra.Command, args []string) {
			space, err := cli.facilityManager.GetSpace(args[0])
			if err != nil {
				fmt.Printf("Error getting space: %v\n", err)
				os.Exit(1)
			}
			cli.printSpace(space)
		},
	}
	spaceCmd.AddCommand(getCmd)

	return spaceCmd
}

// Asset Commands

func (cli *FacilityCLI) createAssetCommands() *cobra.Command {
	assetCmd := &cobra.Command{
		Use:   "asset",
		Short: "Manage assets",
		Long:  "Create, read, update, and delete asset information",
	}

	// List assets
	listCmd := &cobra.Command{
		Use:   "list",
		Short: "List all assets",
		Run: func(cmd *cobra.Command, args []string) {
			assets := cli.facilityManager.ListAssets()
			cli.printAssets(assets)
		},
	}
	assetCmd.AddCommand(listCmd)

	// List assets by building
	listByBuildingCmd := &cobra.Command{
		Use:   "list-by-building <building-id>",
		Short: "List assets in a building",
		Args:  cobra.ExactArgs(1),
		Run: func(cmd *cobra.Command, args []string) {
			assets := cli.facilityManager.GetAssetsByBuilding(args[0])
			cli.printAssets(assets)
		},
	}
	assetCmd.AddCommand(listByBuildingCmd)

	// List assets by space
	listBySpaceCmd := &cobra.Command{
		Use:   "list-by-space <space-id>",
		Short: "List assets in a space",
		Args:  cobra.ExactArgs(1),
		Run: func(cmd *cobra.Command, args []string) {
			assets := cli.facilityManager.GetAssetsBySpace(args[0])
			cli.printAssets(assets)
		},
	}
	assetCmd.AddCommand(listBySpaceCmd)

	// Create asset
	createCmd := &cobra.Command{
		Use:   "create",
		Short: "Create a new asset",
		Run: func(cmd *cobra.Command, args []string) {
			asset := cli.promptForAsset()
			if err := cli.facilityManager.CreateAsset(asset); err != nil {
				fmt.Printf("Error creating asset: %v\n", err)
				os.Exit(1)
			}
			fmt.Printf("Asset '%s' created successfully\n", asset.Name)
		},
	}
	assetCmd.AddCommand(createCmd)

	// Get asset
	getCmd := &cobra.Command{
		Use:   "get <asset-id>",
		Short: "Get asset details",
		Args:  cobra.ExactArgs(1),
		Run: func(cmd *cobra.Command, args []string) {
			asset, err := cli.facilityManager.GetAsset(args[0])
			if err != nil {
				fmt.Printf("Error getting asset: %v\n", err)
				os.Exit(1)
			}
			cli.printAsset(asset)
		},
	}
	assetCmd.AddCommand(getCmd)

	return assetCmd
}

// Work Order Commands

func (cli *FacilityCLI) createWorkOrderCommands() *cobra.Command {
	workOrderCmd := &cobra.Command{
		Use:   "workorder",
		Short: "Manage work orders",
		Long:  "Create, assign, track, and complete work orders",
	}

	// List work orders
	listCmd := &cobra.Command{
		Use:   "list",
		Short: "List all work orders",
		Run: func(cmd *cobra.Command, args []string) {
			workOrders := cli.workOrderManager.ListWorkOrders()
			cli.printWorkOrders(workOrders)
		},
	}
	workOrderCmd.AddCommand(listCmd)

	// Create work order
	createCmd := &cobra.Command{
		Use:   "create",
		Short: "Create a new work order",
		Run: func(cmd *cobra.Command, args []string) {
			workOrder := cli.promptForWorkOrder()
			if err := cli.workOrderManager.CreateWorkOrder(workOrder); err != nil {
				fmt.Printf("Error creating work order: %v\n", err)
				os.Exit(1)
			}
			fmt.Printf("Work order '%s' created successfully\n", workOrder.Title)
		},
	}
	workOrderCmd.AddCommand(createCmd)

	// Assign work order
	assignCmd := &cobra.Command{
		Use:   "assign <work-order-id> <technician-id>",
		Short: "Assign work order to technician",
		Args:  cobra.ExactArgs(2),
		Run: func(cmd *cobra.Command, args []string) {
			if err := cli.workOrderManager.AssignWorkOrder(args[0], args[1]); err != nil {
				fmt.Printf("Error assigning work order: %v\n", err)
				os.Exit(1)
			}
			fmt.Printf("Work order '%s' assigned to technician '%s'\n", args[0], args[1])
		},
	}
	workOrderCmd.AddCommand(assignCmd)

	// Start work order
	startCmd := &cobra.Command{
		Use:   "start <work-order-id>",
		Short: "Start work order execution",
		Args:  cobra.ExactArgs(1),
		Run: func(cmd *cobra.Command, args []string) {
			if err := cli.workOrderManager.StartWorkOrder(args[0]); err != nil {
				fmt.Printf("Error starting work order: %v\n", err)
				os.Exit(1)
			}
			fmt.Printf("Work order '%s' started\n", args[0])
		},
	}
	workOrderCmd.AddCommand(startCmd)

	// Complete work order
	completeCmd := &cobra.Command{
		Use:   "complete <work-order-id>",
		Short: "Complete work order",
		Args:  cobra.ExactArgs(1),
		Run: func(cmd *cobra.Command, args []string) {
			notes := cli.promptForString("Enter completion notes: ")
			if err := cli.workOrderManager.CompleteWorkOrder(args[0], []string{notes}); err != nil {
				fmt.Printf("Error completing work order: %v\n", err)
				os.Exit(1)
			}
			fmt.Printf("Work order '%s' completed\n", args[0])
		},
	}
	workOrderCmd.AddCommand(completeCmd)

	// Cancel work order
	cancelCmd := &cobra.Command{
		Use:   "cancel <work-order-id>",
		Short: "Cancel work order",
		Args:  cobra.ExactArgs(1),
		Run: func(cmd *cobra.Command, args []string) {
			reason := cli.promptForString("Enter cancellation reason: ")
			if err := cli.workOrderManager.CancelWorkOrder(args[0], reason); err != nil {
				fmt.Printf("Error cancelling work order: %v\n", err)
				os.Exit(1)
			}
			fmt.Printf("Work order '%s' cancelled\n", args[0])
		},
	}
	workOrderCmd.AddCommand(cancelCmd)

	return workOrderCmd
}

// Maintenance Commands

func (cli *FacilityCLI) createMaintenanceCommands() *cobra.Command {
	maintenanceCmd := &cobra.Command{
		Use:   "maintenance",
		Short: "Manage maintenance schedules",
		Long:  "Create, schedule, and execute maintenance tasks",
	}

	// List maintenance schedules
	listCmd := &cobra.Command{
		Use:   "list",
		Short: "List all maintenance schedules",
		Run: func(cmd *cobra.Command, args []string) {
			schedules := cli.maintenanceManager.ListMaintenanceSchedules()
			cli.printMaintenanceSchedules(schedules)
		},
	}
	maintenanceCmd.AddCommand(listCmd)

	// Create maintenance schedule
	createCmd := &cobra.Command{
		Use:   "create",
		Short: "Create a new maintenance schedule",
		Run: func(cmd *cobra.Command, args []string) {
			schedule := cli.promptForMaintenanceSchedule()
			if err := cli.maintenanceManager.CreateMaintenanceSchedule(schedule); err != nil {
				fmt.Printf("Error creating maintenance schedule: %v\n", err)
				os.Exit(1)
			}
			fmt.Printf("Maintenance schedule '%s' created successfully\n", schedule.Name)
		},
	}
	maintenanceCmd.AddCommand(createCmd)

	// Execute maintenance
	executeCmd := &cobra.Command{
		Use:   "execute <schedule-id>",
		Short: "Execute maintenance schedule",
		Args:  cobra.ExactArgs(1),
		Run: func(cmd *cobra.Command, args []string) {
			workOrder, err := cli.maintenanceManager.ExecuteMaintenanceSchedule(args[0])
			if err != nil {
				fmt.Printf("Error executing maintenance schedule: %v\n", err)
				os.Exit(1)
			}
			fmt.Printf("Maintenance schedule executed, work order '%s' created\n", workOrder.ID)
		},
	}
	maintenanceCmd.AddCommand(executeCmd)

	// Execute all due maintenance
	executeAllCmd := &cobra.Command{
		Use:   "execute-all",
		Short: "Execute all due maintenance schedules",
		Run: func(cmd *cobra.Command, args []string) {
			workOrders, err := cli.maintenanceManager.ExecuteAllDueMaintenance()
			if err != nil {
				fmt.Printf("Error executing maintenance schedules: %v\n", err)
				os.Exit(1)
			}
			fmt.Printf("Executed %d maintenance schedules\n", len(workOrders))
		},
	}
	maintenanceCmd.AddCommand(executeAllCmd)

	return maintenanceCmd
}

// Inspection Commands

func (cli *FacilityCLI) createInspectionCommands() *cobra.Command {
	inspectionCmd := &cobra.Command{
		Use:   "inspection",
		Short: "Manage inspections",
		Long:  "Create, schedule, and conduct inspections",
	}

	// List inspections
	listCmd := &cobra.Command{
		Use:   "list",
		Short: "List all inspections",
		Run: func(cmd *cobra.Command, args []string) {
			inspections := cli.inspectionManager.ListInspections()
			cli.printInspections(inspections)
		},
	}
	inspectionCmd.AddCommand(listCmd)

	// Create inspection
	createCmd := &cobra.Command{
		Use:   "create",
		Short: "Create a new inspection",
		Run: func(cmd *cobra.Command, args []string) {
			inspection := cli.promptForInspection()
			if err := cli.inspectionManager.CreateInspection(inspection); err != nil {
				fmt.Printf("Error creating inspection: %v\n", err)
				os.Exit(1)
			}
			fmt.Printf("Inspection '%s' created successfully\n", inspection.Name)
		},
	}
	inspectionCmd.AddCommand(createCmd)

	// Start inspection
	startCmd := &cobra.Command{
		Use:   "start <inspection-id>",
		Short: "Start inspection",
		Args:  cobra.ExactArgs(1),
		Run: func(cmd *cobra.Command, args []string) {
			if err := cli.inspectionManager.StartInspection(args[0]); err != nil {
				fmt.Printf("Error starting inspection: %v\n", err)
				os.Exit(1)
			}
			fmt.Printf("Inspection '%s' started\n", args[0])
		},
	}
	inspectionCmd.AddCommand(startCmd)

	// Complete inspection
	completeCmd := &cobra.Command{
		Use:   "complete <inspection-id>",
		Short: "Complete inspection",
		Args:  cobra.ExactArgs(1),
		Run: func(cmd *cobra.Command, args []string) {
			score := cli.promptForFloat("Enter inspection score (0-100): ")
			notes := cli.promptForString("Enter inspection notes: ")
			if err := cli.inspectionManager.CompleteInspection(args[0], score, notes); err != nil {
				fmt.Printf("Error completing inspection: %v\n", err)
				os.Exit(1)
			}
			fmt.Printf("Inspection '%s' completed with score %.1f\n", args[0], score)
		},
	}
	inspectionCmd.AddCommand(completeCmd)

	return inspectionCmd
}

// Vendor Commands

func (cli *FacilityCLI) createVendorCommands() *cobra.Command {
	vendorCmd := &cobra.Command{
		Use:   "vendor",
		Short: "Manage vendors and contracts",
		Long:  "Create, update, and manage vendor information and contracts",
	}

	// List vendors
	listVendorsCmd := &cobra.Command{
		Use:   "list",
		Short: "List all vendors",
		Run: func(cmd *cobra.Command, args []string) {
			vendors := cli.vendorManager.ListVendors()
			cli.printVendors(vendors)
		},
	}
	vendorCmd.AddCommand(listVendorsCmd)

	// Create vendor
	createVendorCmd := &cobra.Command{
		Use:   "create",
		Short: "Create a new vendor",
		Run: func(cmd *cobra.Command, args []string) {
			vendor := cli.promptForVendor()
			if err := cli.vendorManager.CreateVendor(vendor); err != nil {
				fmt.Printf("Error creating vendor: %v\n", err)
				os.Exit(1)
			}
			fmt.Printf("Vendor '%s' created successfully\n", vendor.Name)
		},
	}
	vendorCmd.AddCommand(createVendorCmd)

	// List contracts
	listContractsCmd := &cobra.Command{
		Use:   "contracts",
		Short: "List all contracts",
		Run: func(cmd *cobra.Command, args []string) {
			contracts := cli.vendorManager.ListContracts()
			cli.printContracts(contracts)
		},
	}
	vendorCmd.AddCommand(listContractsCmd)

	// Create contract
	createContractCmd := &cobra.Command{
		Use:   "create-contract",
		Short: "Create a new contract",
		Run: func(cmd *cobra.Command, args []string) {
			contract := cli.promptForContract()
			if err := cli.vendorManager.CreateContract(contract); err != nil {
				fmt.Printf("Error creating contract: %v\n", err)
				os.Exit(1)
			}
			fmt.Printf("Contract '%s' created successfully\n", contract.Name)
		},
	}
	vendorCmd.AddCommand(createContractCmd)

	return vendorCmd
}

// Metrics Commands

func (cli *FacilityCLI) createMetricsCommands() *cobra.Command {
	metricsCmd := &cobra.Command{
		Use:   "metrics",
		Short: "View facility metrics",
		Long:  "Display various metrics and statistics for facility management",
	}

	// Facility metrics
	facilityCmd := &cobra.Command{
		Use:   "facility",
		Short: "Show facility metrics",
		Run: func(cmd *cobra.Command, args []string) {
			metrics := cli.facilityManager.GetMetrics()
			cli.printFacilityMetrics(metrics)
		},
	}
	metricsCmd.AddCommand(facilityCmd)

	// Work order metrics
	workOrderCmd := &cobra.Command{
		Use:   "workorders",
		Short: "Show work order metrics",
		Run: func(cmd *cobra.Command, args []string) {
			metrics := cli.workOrderManager.GetWorkOrderMetrics()
			cli.printWorkOrderMetrics(metrics)
		},
	}
	metricsCmd.AddCommand(workOrderCmd)

	// Maintenance metrics
	maintenanceCmd := &cobra.Command{
		Use:   "maintenance",
		Short: "Show maintenance metrics",
		Run: func(cmd *cobra.Command, args []string) {
			metrics := cli.maintenanceManager.GetMaintenanceMetrics()
			cli.printMaintenanceMetrics(metrics)
		},
	}
	metricsCmd.AddCommand(maintenanceCmd)

	// Inspection metrics
	inspectionCmd := &cobra.Command{
		Use:   "inspections",
		Short: "Show inspection metrics",
		Run: func(cmd *cobra.Command, args []string) {
			metrics := cli.inspectionManager.GetInspectionMetrics()
			cli.printInspectionMetrics(metrics)
		},
	}
	metricsCmd.AddCommand(inspectionCmd)

	// Vendor metrics
	vendorCmd := &cobra.Command{
		Use:   "vendors",
		Short: "Show vendor metrics",
		Run: func(cmd *cobra.Command, args []string) {
			metrics := cli.vendorManager.GetVendorMetrics()
			cli.printVendorMetrics(metrics)
		},
	}
	metricsCmd.AddCommand(vendorCmd)

	return metricsCmd
}

// Prompt Functions

func (cli *FacilityCLI) promptForBuilding() *Building {
	return &Building{
		ID:           cli.promptForString("Building ID: "),
		Name:         cli.promptForString("Building Name: "),
		Address:      cli.promptForString("Address: "),
		City:         cli.promptForString("City: "),
		State:        cli.promptForString("State: "),
		ZipCode:      cli.promptForString("Zip Code: "),
		Country:      cli.promptForString("Country: "),
		BuildingType: cli.promptForString("Building Type: "),
		Floors:       cli.promptForInt("Number of Floors: "),
		TotalArea:    cli.promptForFloat("Total Area (sq ft): "),
		YearBuilt:    cli.promptForInt("Year Built: "),
		Status:       BuildingStatusActive,
		CreatedAt:    time.Now(),
		UpdatedAt:    time.Now(),
	}
}

func (cli *FacilityCLI) promptForBuildingUpdates() map[string]interface{} {
	updates := make(map[string]interface{})

	if name := cli.promptForString("New name (press Enter to skip): "); name != "" {
		updates["name"] = name
	}
	if address := cli.promptForString("New address (press Enter to skip): "); address != "" {
		updates["address"] = address
	}
	if status := cli.promptForString("New status (press Enter to skip): "); status != "" {
		updates["status"] = status
	}

	return updates
}

func (cli *FacilityCLI) promptForSpace() *Space {
	return &Space{
		ID:         cli.promptForString("Space ID: "),
		BuildingID: cli.promptForString("Building ID: "),
		Name:       cli.promptForString("Space Name: "),
		SpaceType:  cli.promptForString("Space Type: "),
		Floor:      cli.promptForInt("Floor: "),
		Area:       cli.promptForFloat("Area (sq ft): "),
		Capacity:   cli.promptForInt("Capacity: "),
		Status:     SpaceStatusActive,
		CreatedAt:  time.Now(),
		UpdatedAt:  time.Now(),
	}
}

func (cli *FacilityCLI) promptForAsset() *Asset {
	return &Asset{
		ID:             cli.promptForString("Asset ID: "),
		BuildingID:     cli.promptForString("Building ID: "),
		SpaceID:        cli.promptForString("Space ID: "),
		Name:           cli.promptForString("Asset Name: "),
		AssetType:      cli.promptForString("Asset Type: "),
		Manufacturer:   cli.promptForString("Manufacturer: "),
		Model:          cli.promptForString("Model: "),
		SerialNumber:   cli.promptForString("Serial Number: "),
		InstallDate:    cli.promptForDate("Install Date (YYYY-MM-DD): "),
		WarrantyExpiry: func() *time.Time { t := cli.promptForDate("Warranty Expiry (YYYY-MM-DD): "); return &t }(),
		Status:         AssetStatusActive,
		CreatedAt:      time.Now(),
		UpdatedAt:      time.Now(),
	}
}

func (cli *FacilityCLI) promptForWorkOrder() *WorkOrder {
	return &WorkOrder{
		ID:          cli.promptForString("Work Order ID: "),
		Title:       cli.promptForString("Title: "),
		Description: cli.promptForString("Description: "),
		Priority:    WorkOrderPriority(cli.promptForString("Priority (low/medium/high/urgent): ")),
		Status:      WorkOrderStatusOpen,
		AssetID:     cli.promptForString("Asset ID: "),
		SpaceID:     cli.promptForString("Space ID: "),
		BuildingID:  cli.promptForString("Building ID: "),
		CreatedBy:   cli.promptForString("Created By: "),
		CreatedAt:   time.Now(),
		UpdatedAt:   time.Now(),
	}
}

func (cli *FacilityCLI) promptForMaintenanceSchedule() *MaintenanceSchedule {
	return &MaintenanceSchedule{
		ID:          cli.promptForString("Schedule ID: "),
		Name:        cli.promptForString("Schedule Name: "),
		Description: cli.promptForString("Description: "),
		AssetID:     cli.promptForString("Asset ID: "),
		Frequency:   cli.promptForString("Frequency (daily/weekly/monthly/yearly): "),
		Interval:    cli.promptForInt("Interval: "),
		NextDue:     cli.promptForDate("Next Due Date (YYYY-MM-DD): "),
		Status:      MaintenanceStatusActive,
		CreatedAt:   time.Now(),
		UpdatedAt:   time.Now(),
	}
}

func (cli *FacilityCLI) promptForInspection() *Inspection {
	return &Inspection{
		ID:            cli.promptForString("Inspection ID: "),
		Name:          cli.promptForString("Inspection Name: "),
		Type:          cli.promptForString("Inspection Type: "),
		AssetID:       cli.promptForString("Asset ID: "),
		SpaceID:       cli.promptForString("Space ID: "),
		BuildingID:    cli.promptForString("Building ID: "),
		ScheduledDate: cli.promptForDate("Scheduled Date (YYYY-MM-DD): "),
		Status:        InspectionStatusScheduled,
		CreatedAt:     time.Now(),
		UpdatedAt:     time.Now(),
	}
}

func (cli *FacilityCLI) promptForVendor() *Vendor {
	return &Vendor{
		ID:          cli.promptForString("Vendor ID: "),
		Name:        cli.promptForString("Vendor Name: "),
		ContactName: cli.promptForString("Contact Name: "),
		Email:       cli.promptForString("Email: "),
		Phone:       cli.promptForString("Phone: "),
		Address:     cli.promptForString("Address: "),
		City:        cli.promptForString("City: "),
		State:       cli.promptForString("State: "),
		ZipCode:     cli.promptForString("Zip Code: "),
		Country:     cli.promptForString("Country: "),
		Status:      VendorStatusActive,
		CreatedAt:   time.Now(),
		UpdatedAt:   time.Now(),
	}
}

func (cli *FacilityCLI) promptForContract() *Contract {
	return &Contract{
		ID:          cli.promptForString("Contract ID: "),
		VendorID:    cli.promptForString("Vendor ID: "),
		Name:        cli.promptForString("Contract Name: "),
		Description: cli.promptForString("Description: "),
		StartDate:   cli.promptForDate("Start Date (YYYY-MM-DD): "),
		EndDate:     cli.promptForDate("End Date (YYYY-MM-DD): "),
		Value:       cli.promptForFloat("Contract Value: "),
		Status:      ContractStatusActive,
		CreatedAt:   time.Now(),
		UpdatedAt:   time.Now(),
	}
}

// Helper Functions

func (cli *FacilityCLI) promptForString(prompt string) string {
	fmt.Print(prompt)
	var input string
	fmt.Scanln(&input)
	return input
}

func (cli *FacilityCLI) promptForInt(prompt string) int {
	fmt.Print(prompt)
	var input string
	fmt.Scanln(&input)
	value, _ := strconv.Atoi(input)
	return value
}

func (cli *FacilityCLI) promptForFloat(prompt string) float64 {
	fmt.Print(prompt)
	var input string
	fmt.Scanln(&input)
	value, _ := strconv.ParseFloat(input, 64)
	return value
}

func (cli *FacilityCLI) promptForDate(prompt string) time.Time {
	fmt.Print(prompt)
	var input string
	fmt.Scanln(&input)
	date, _ := time.Parse("2006-01-02", input)
	return date
}

// Print Functions

func (cli *FacilityCLI) printBuildings(buildings []*Building) {
	fmt.Printf("\nBuildings (%d):\n", len(buildings))
	fmt.Println(strings.Repeat("-", 80))
	for _, building := range buildings {
		fmt.Printf("ID: %s | Name: %s | Type: %s | Status: %s\n",
			building.ID, building.Name, building.BuildingType, building.Status)
	}
}

func (cli *FacilityCLI) printBuilding(building *Building) {
	fmt.Printf("\nBuilding Details:\n")
	fmt.Println(strings.Repeat("-", 40))
	fmt.Printf("ID: %s\n", building.ID)
	fmt.Printf("Name: %s\n", building.Name)
	fmt.Printf("Address: %s\n", building.Address)
	fmt.Printf("Type: %s\n", building.BuildingType)
	fmt.Printf("Floors: %d\n", building.Floors)
	fmt.Printf("Total Area: %.2f sq ft\n", building.TotalArea)
	fmt.Printf("Status: %s\n", building.Status)
}

func (cli *FacilityCLI) printSpaces(spaces []*Space) {
	fmt.Printf("\nSpaces (%d):\n", len(spaces))
	fmt.Println(strings.Repeat("-", 80))
	for _, space := range spaces {
		fmt.Printf("ID: %s | Name: %s | Type: %s | Floor: %d | Status: %s\n",
			space.ID, space.Name, space.SpaceType, space.Floor, space.Status)
	}
}

func (cli *FacilityCLI) printSpace(space *Space) {
	fmt.Printf("\nSpace Details:\n")
	fmt.Println(strings.Repeat("-", 40))
	fmt.Printf("ID: %s\n", space.ID)
	fmt.Printf("Name: %s\n", space.Name)
	fmt.Printf("Type: %s\n", space.SpaceType)
	fmt.Printf("Floor: %d\n", space.Floor)
	fmt.Printf("Area: %.2f sq ft\n", space.Area)
	fmt.Printf("Capacity: %d\n", space.Capacity)
	fmt.Printf("Status: %s\n", space.Status)
}

func (cli *FacilityCLI) printAssets(assets []*Asset) {
	fmt.Printf("\nAssets (%d):\n", len(assets))
	fmt.Println(strings.Repeat("-", 80))
	for _, asset := range assets {
		fmt.Printf("ID: %s | Name: %s | Type: %s | Status: %s\n",
			asset.ID, asset.Name, asset.AssetType, asset.Status)
	}
}

func (cli *FacilityCLI) printAsset(asset *Asset) {
	fmt.Printf("\nAsset Details:\n")
	fmt.Println(strings.Repeat("-", 40))
	fmt.Printf("ID: %s\n", asset.ID)
	fmt.Printf("Name: %s\n", asset.Name)
	fmt.Printf("Type: %s\n", asset.AssetType)
	fmt.Printf("Manufacturer: %s\n", asset.Manufacturer)
	fmt.Printf("Model: %s\n", asset.Model)
	fmt.Printf("Serial Number: %s\n", asset.SerialNumber)
	fmt.Printf("Status: %s\n", asset.Status)
}

func (cli *FacilityCLI) printWorkOrders(workOrders []*WorkOrder) {
	fmt.Printf("\nWork Orders (%d):\n", len(workOrders))
	fmt.Println(strings.Repeat("-", 80))
	for _, wo := range workOrders {
		fmt.Printf("ID: %s | Title: %s | Priority: %s | Status: %s\n",
			wo.ID, wo.Title, wo.Priority, wo.Status)
	}
}

func (cli *FacilityCLI) printMaintenanceSchedules(schedules []*MaintenanceSchedule) {
	fmt.Printf("\nMaintenance Schedules (%d):\n", len(schedules))
	fmt.Println(strings.Repeat("-", 80))
	for _, schedule := range schedules {
		fmt.Printf("ID: %s | Name: %s | Frequency: %s | Next Due: %s\n",
			schedule.ID, schedule.Name, schedule.Frequency, schedule.NextDue.Format("2006-01-02"))
	}
}

func (cli *FacilityCLI) printInspections(inspections []*Inspection) {
	fmt.Printf("\nInspections (%d):\n", len(inspections))
	fmt.Println(strings.Repeat("-", 80))
	for _, inspection := range inspections {
		fmt.Printf("ID: %s | Name: %s | Type: %s | Status: %s\n",
			inspection.ID, inspection.Name, inspection.Type, inspection.Status)
	}
}

func (cli *FacilityCLI) printVendors(vendors []*Vendor) {
	fmt.Printf("\nVendors (%d):\n", len(vendors))
	fmt.Println(strings.Repeat("-", 80))
	for _, vendor := range vendors {
		fmt.Printf("ID: %s | Name: %s | Contact: %s | Status: %s\n",
			vendor.ID, vendor.Name, vendor.ContactName, vendor.Status)
	}
}

func (cli *FacilityCLI) printContracts(contracts []*Contract) {
	fmt.Printf("\nContracts (%d):\n", len(contracts))
	fmt.Println(strings.Repeat("-", 80))
	for _, contract := range contracts {
		fmt.Printf("ID: %s | Name: %s | Vendor: %s | Value: $%.2f | Status: %s\n",
			contract.ID, contract.Name, contract.VendorID, contract.Value, contract.Status)
	}
}

func (cli *FacilityCLI) printFacilityMetrics(metrics *FacilityMetrics) {
	fmt.Printf("\nFacility Metrics:\n")
	fmt.Println(strings.Repeat("-", 40))
	fmt.Printf("Total Buildings: %d\n", metrics.TotalBuildings)
	fmt.Printf("Total Spaces: %d\n", metrics.TotalSpaces)
	fmt.Printf("Total Assets: %d\n", metrics.TotalAssets)
	fmt.Printf("Active Buildings: %d\n", metrics.ActiveBuildings)
	fmt.Printf("Active Spaces: %d\n", metrics.ActiveSpaces)
	fmt.Printf("Active Assets: %d\n", metrics.ActiveAssets)
}

func (cli *FacilityCLI) printWorkOrderMetrics(metrics *WorkOrderMetrics) {
	fmt.Printf("\nWork Order Metrics:\n")
	fmt.Println(strings.Repeat("-", 40))
	fmt.Printf("Total Work Orders: %d\n", metrics.TotalWorkOrders)
	fmt.Printf("Open Work Orders: %d\n", metrics.OpenWorkOrders)
	fmt.Printf("In Progress: %d\n", metrics.InProgressWorkOrders)
	fmt.Printf("Completed: %d\n", metrics.CompletedWorkOrders)
	fmt.Printf("Cancelled: %d\n", metrics.CancelledWorkOrders)
	fmt.Printf("Average Resolution Time: %.2f hours\n", metrics.AvgResolutionTimeHours)
}

func (cli *FacilityCLI) printMaintenanceMetrics(metrics *MaintenanceMetrics) {
	fmt.Printf("\nMaintenance Metrics:\n")
	fmt.Println(strings.Repeat("-", 40))
	fmt.Printf("Total Schedules: %d\n", metrics.TotalSchedules)
	fmt.Printf("Active Schedules: %d\n", metrics.ActiveSchedules)
	fmt.Printf("Due Schedules: %d\n", metrics.DueSchedules)
	fmt.Printf("Overdue Schedules: %d\n", metrics.OverdueSchedules)
	fmt.Printf("Completed Tasks: %d\n", metrics.CompletedTasks)
	fmt.Printf("Average Completion Time: %.2f hours\n", metrics.AvgCompletionTimeHours)
}

func (cli *FacilityCLI) printInspectionMetrics(metrics *InspectionMetrics) {
	fmt.Printf("\nInspection Metrics:\n")
	fmt.Println(strings.Repeat("-", 40))
	fmt.Printf("Total Inspections: %d\n", metrics.TotalInspections)
	fmt.Printf("Scheduled: %d\n", metrics.ScheduledInspections)
	fmt.Printf("In Progress: %d\n", metrics.InProgressInspections)
	fmt.Printf("Completed: %d\n", metrics.CompletedInspections)
	fmt.Printf("Overdue: %d\n", metrics.OverdueInspections)
	fmt.Printf("Average Score: %.2f\n", metrics.AverageScore)
	fmt.Printf("Critical Findings: %d\n", metrics.CriticalFindings)
}

func (cli *FacilityCLI) printVendorMetrics(metrics *VendorMetrics) {
	fmt.Printf("\nVendor Metrics:\n")
	fmt.Println(strings.Repeat("-", 40))
	fmt.Printf("Total Vendors: %d\n", metrics.TotalVendors)
	fmt.Printf("Active Vendors: %d\n", metrics.ActiveVendors)
	fmt.Printf("Total Contracts: %d\n", metrics.TotalContracts)
	fmt.Printf("Active Contracts: %d\n", metrics.ActiveContracts)
	fmt.Printf("Expiring Contracts: %d\n", metrics.ExpiringContracts)
	fmt.Printf("Total Contract Value: $%.2f\n", metrics.TotalContractValue)
}
