package facility

import (
	"fmt"
	"sort"
	"time"

	"github.com/arx-os/arxos/internal/common/logger"
)

// VendorManager manages vendors and contracts
type VendorManager struct {
	facilityManager *FacilityManager
	vendors         map[string]*Vendor
	contracts       map[string]*Contract
	metrics         *VendorMetrics
}

// VendorMetrics tracks vendor performance
type VendorMetrics struct {
	TotalVendors         int64   `json:"total_vendors"`
	ActiveVendors        int64   `json:"active_vendors"`
	InactiveVendors      int64   `json:"inactive_vendors"`
	SuspendedVendors     int64   `json:"suspended_vendors"`
	BlacklistedVendors   int64   `json:"blacklisted_vendors"`
	TotalContracts       int64   `json:"total_contracts"`
	ActiveContracts      int64   `json:"active_contracts"`
	ExpiredContracts     int64   `json:"expired_contracts"`
	ExpiringContracts    int64   `json:"expiring_contracts"`
	AverageRating        float64 `json:"average_rating"`
	TotalContractValue   float64 `json:"total_contract_value"`
	AverageContractValue float64 `json:"average_contract_value"`
}

// NewVendorManager creates a new vendor manager
func NewVendorManager(facilityManager *FacilityManager) *VendorManager {
	return &VendorManager{
		facilityManager: facilityManager,
		vendors:         make(map[string]*Vendor),
		contracts:       make(map[string]*Contract),
		metrics:         &VendorMetrics{},
	}
}

// CreateVendor creates a new vendor
func (vm *VendorManager) CreateVendor(vendor *Vendor) error {
	if vendor == nil {
		return fmt.Errorf("vendor cannot be nil")
	}

	if vendor.ID == "" {
		vendor.ID = fmt.Sprintf("vendor_%d", time.Now().UnixNano())
	}

	if vendor.Name == "" {
		return fmt.Errorf("vendor name cannot be empty")
	}

	if vendor.Type == "" {
		return fmt.Errorf("vendor type cannot be empty")
	}

	// Set timestamps
	now := time.Now()
	vendor.CreatedAt = now
	vendor.UpdatedAt = now

	// Set default status
	if vendor.Status == "" {
		vendor.Status = VendorStatusActive
	}

	// Set default rating
	if vendor.Rating == 0 {
		vendor.Rating = 5.0
	}

	// Store vendor
	vm.vendors[vendor.ID] = vendor
	vm.metrics.TotalVendors++

	// Update facility manager
	vm.facilityManager.vendors[vendor.ID] = vendor

	logger.Info("Vendor created: %s (%s)", vendor.ID, vendor.Name)
	return nil
}

// GetVendor retrieves a vendor by ID
func (vm *VendorManager) GetVendor(vendorID string) (*Vendor, error) {
	vendor, exists := vm.vendors[vendorID]
	if !exists {
		return nil, fmt.Errorf("vendor %s not found", vendorID)
	}
	return vendor, nil
}

// UpdateVendor updates an existing vendor
func (vm *VendorManager) UpdateVendor(vendorID string, updates map[string]interface{}) error {
	vendor, exists := vm.vendors[vendorID]
	if !exists {
		return fmt.Errorf("vendor %s not found", vendorID)
	}

	// Apply updates
	for key, value := range updates {
		switch key {
		case "name":
			if name, ok := value.(string); ok {
				vendor.Name = name
			}
		case "type":
			if vendorType, ok := value.(string); ok {
				vendor.Type = VendorType(vendorType)
			}
		case "status":
			if status, ok := value.(string); ok {
				vendor.Status = VendorStatus(status)
			}
		case "rating":
			if rating, ok := value.(float64); ok {
				vendor.Rating = rating
			}
		case "contact":
			if contact, ok := value.(Contact); ok {
				vendor.Contact = contact
			}
		case "services":
			if services, ok := value.([]string); ok {
				vendor.Services = services
			}
		}
	}

	vendor.UpdatedAt = time.Now()
	logger.Info("Vendor updated: %s", vendorID)
	return nil
}

// DeleteVendor deletes a vendor
func (vm *VendorManager) DeleteVendor(vendorID string) error {
	vendor, exists := vm.vendors[vendorID]
	if !exists {
		return fmt.Errorf("vendor %s not found", vendorID)
	}

	// Delete associated contracts
	for contractID, contract := range vm.contracts {
		if contract.VendorID == vendorID {
			delete(vm.contracts, contractID)
			delete(vm.facilityManager.contracts, contractID)
		}
	}

	// Delete vendor
	delete(vm.vendors, vendorID)
	delete(vm.facilityManager.vendors, vendorID)
	vm.metrics.TotalVendors--

	logger.Info("Vendor deleted: %s (%s)", vendorID, vendor.Name)
	return nil
}

// ListVendors returns all vendors
func (vm *VendorManager) ListVendors() []*Vendor {
	vendors := make([]*Vendor, 0, len(vm.vendors))
	for _, vendor := range vm.vendors {
		vendors = append(vendors, vendor)
	}
	return vendors
}

// GetVendorsByType returns vendors by type
func (vm *VendorManager) GetVendorsByType(vendorType VendorType) []*Vendor {
	var vendors []*Vendor
	for _, vendor := range vm.vendors {
		if vendor.Type == vendorType {
			vendors = append(vendors, vendor)
		}
	}
	return vendors
}

// GetVendorsByStatus returns vendors by status
func (vm *VendorManager) GetVendorsByStatus(status VendorStatus) []*Vendor {
	var vendors []*Vendor
	for _, vendor := range vm.vendors {
		if vendor.Status == status {
			vendors = append(vendors, vendor)
		}
	}
	return vendors
}

// GetVendorsByService returns vendors that provide a specific service
func (vm *VendorManager) GetVendorsByService(service string) []*Vendor {
	var vendors []*Vendor
	for _, vendor := range vm.vendors {
		for _, s := range vendor.Services {
			if s == service {
				vendors = append(vendors, vendor)
				break
			}
		}
	}
	return vendors
}

// GetVendorsByRating returns vendors with a minimum rating
func (vm *VendorManager) GetVendorsByRating(minRating float64) []*Vendor {
	var vendors []*Vendor
	for _, vendor := range vm.vendors {
		if vendor.Rating >= minRating {
			vendors = append(vendors, vendor)
		}
	}
	return vendors
}

// SuspendVendor suspends a vendor
func (vm *VendorManager) SuspendVendor(vendorID string, reason string) error {
	vendor, exists := vm.vendors[vendorID]
	if !exists {
		return fmt.Errorf("vendor %s not found", vendorID)
	}

	vendor.Status = VendorStatusSuspended
	vendor.UpdatedAt = time.Now()

	logger.Info("Vendor %s suspended: %s", vendorID, reason)
	return nil
}

// BlacklistVendor blacklists a vendor
func (vm *VendorManager) BlacklistVendor(vendorID string, reason string) error {
	vendor, exists := vm.vendors[vendorID]
	if !exists {
		return fmt.Errorf("vendor %s not found", vendorID)
	}

	vendor.Status = VendorStatusBlacklisted
	vendor.UpdatedAt = time.Now()

	logger.Info("Vendor %s blacklisted: %s", vendorID, reason)
	return nil
}

// ReactivateVendor reactivates a vendor
func (vm *VendorManager) ReactivateVendor(vendorID string) error {
	vendor, exists := vm.vendors[vendorID]
	if !exists {
		return fmt.Errorf("vendor %s not found", vendorID)
	}

	vendor.Status = VendorStatusActive
	vendor.UpdatedAt = time.Now()

	logger.Info("Vendor %s reactivated", vendorID)
	return nil
}

// UpdateVendorRating updates a vendor's rating
func (vm *VendorManager) UpdateVendorRating(vendorID string, rating float64) error {
	vendor, exists := vm.vendors[vendorID]
	if !exists {
		return fmt.Errorf("vendor %s not found", vendorID)
	}

	if rating < 0 || rating > 5 {
		return fmt.Errorf("rating must be between 0 and 5")
	}

	vendor.Rating = rating
	vendor.UpdatedAt = time.Now()

	logger.Info("Vendor %s rating updated to %.2f", vendorID, rating)
	return nil
}

// Contract Management Methods

// CreateContract creates a new contract
func (vm *VendorManager) CreateContract(contract *Contract) error {
	if contract == nil {
		return fmt.Errorf("contract cannot be nil")
	}

	if contract.ID == "" {
		contract.ID = fmt.Sprintf("contract_%d", time.Now().UnixNano())
	}

	if contract.Name == "" {
		return fmt.Errorf("contract name cannot be empty")
	}

	if contract.VendorID == "" {
		return fmt.Errorf("vendor ID cannot be empty")
	}

	if contract.BuildingID == "" {
		return fmt.Errorf("building ID cannot be empty")
	}

	// Validate vendor exists
	if _, exists := vm.vendors[contract.VendorID]; !exists {
		return fmt.Errorf("vendor %s not found", contract.VendorID)
	}

	// Validate building exists
	if _, exists := vm.facilityManager.buildings[contract.BuildingID]; !exists {
		return fmt.Errorf("building %s not found", contract.BuildingID)
	}

	// Set timestamps
	now := time.Now()
	contract.CreatedAt = now
	contract.UpdatedAt = now

	// Set default status
	if contract.Status == "" {
		contract.Status = ContractStatusDraft
	}

	// Store contract
	vm.contracts[contract.ID] = contract
	vm.metrics.TotalContracts++

	// Update facility manager
	vm.facilityManager.contracts[contract.ID] = contract

	logger.Info("Contract created: %s (%s)", contract.ID, contract.Name)
	return nil
}

// GetContract retrieves a contract by ID
func (vm *VendorManager) GetContract(contractID string) (*Contract, error) {
	contract, exists := vm.contracts[contractID]
	if !exists {
		return nil, fmt.Errorf("contract %s not found", contractID)
	}
	return contract, nil
}

// UpdateContract updates an existing contract
func (vm *VendorManager) UpdateContract(contractID string, updates map[string]interface{}) error {
	contract, exists := vm.contracts[contractID]
	if !exists {
		return fmt.Errorf("contract %s not found", contractID)
	}

	// Apply updates
	for key, value := range updates {
		switch key {
		case "name":
			if name, ok := value.(string); ok {
				contract.Name = name
			}
		case "type":
			if contractType, ok := value.(string); ok {
				contract.Type = ContractType(contractType)
			}
		case "status":
			if status, ok := value.(string); ok {
				contract.Status = ContractStatus(status)
			}
		case "start_date":
			if startDate, ok := value.(time.Time); ok {
				contract.StartDate = startDate
			}
		case "end_date":
			if endDate, ok := value.(time.Time); ok {
				contract.EndDate = endDate
			}
		case "value":
			if value, ok := value.(float64); ok {
				contract.Value = value
			}
		case "terms":
			if terms, ok := value.(string); ok {
				contract.Terms = terms
			}
		}
	}

	contract.UpdatedAt = time.Now()
	logger.Info("Contract updated: %s", contractID)
	return nil
}

// DeleteContract deletes a contract
func (vm *VendorManager) DeleteContract(contractID string) error {
	contract, exists := vm.contracts[contractID]
	if !exists {
		return fmt.Errorf("contract %s not found", contractID)
	}

	// Delete contract
	delete(vm.contracts, contractID)
	delete(vm.facilityManager.contracts, contractID)
	vm.metrics.TotalContracts--

	logger.Info("Contract deleted: %s (%s)", contractID, contract.Name)
	return nil
}

// ListContracts returns all contracts
func (vm *VendorManager) ListContracts() []*Contract {
	contracts := make([]*Contract, 0, len(vm.contracts))
	for _, contract := range vm.contracts {
		contracts = append(contracts, contract)
	}
	return contracts
}

// GetContractsByVendor returns contracts for a specific vendor
func (vm *VendorManager) GetContractsByVendor(vendorID string) []*Contract {
	var contracts []*Contract
	for _, contract := range vm.contracts {
		if contract.VendorID == vendorID {
			contracts = append(contracts, contract)
		}
	}
	return contracts
}

// GetContractsByBuilding returns contracts for a specific building
func (vm *VendorManager) GetContractsByBuilding(buildingID string) []*Contract {
	var contracts []*Contract
	for _, contract := range vm.contracts {
		if contract.BuildingID == buildingID {
			contracts = append(contracts, contract)
		}
	}
	return contracts
}

// GetContractsByType returns contracts by type
func (vm *VendorManager) GetContractsByType(contractType ContractType) []*Contract {
	var contracts []*Contract
	for _, contract := range vm.contracts {
		if contract.Type == contractType {
			contracts = append(contracts, contract)
		}
	}
	return contracts
}

// GetContractsByStatus returns contracts by status
func (vm *VendorManager) GetContractsByStatus(status ContractStatus) []*Contract {
	var contracts []*Contract
	for _, contract := range vm.contracts {
		if contract.Status == status {
			contracts = append(contracts, contract)
		}
	}
	return contracts
}

// GetExpiringContracts returns contracts expiring in the next specified days
func (vm *VendorManager) GetExpiringContracts(days int) []*Contract {
	var expiringContracts []*Contract
	now := time.Now()
	cutoff := now.AddDate(0, 0, days)

	for _, contract := range vm.contracts {
		if contract.Status == ContractStatusActive && contract.EndDate.After(now) && contract.EndDate.Before(cutoff) {
			expiringContracts = append(expiringContracts, contract)
		}
	}

	return expiringContracts
}

// GetExpiredContracts returns expired contracts
func (vm *VendorManager) GetExpiredContracts() []*Contract {
	var expiredContracts []*Contract
	now := time.Now()

	for _, contract := range vm.contracts {
		if contract.Status == ContractStatusActive && contract.EndDate.Before(now) {
			expiredContracts = append(expiredContracts, contract)
		}
	}

	return expiredContracts
}

// ActivateContract activates a contract
func (vm *VendorManager) ActivateContract(contractID string) error {
	contract, exists := vm.contracts[contractID]
	if !exists {
		return fmt.Errorf("contract %s not found", contractID)
	}

	if contract.Status != ContractStatusDraft {
		return fmt.Errorf("contract must be in draft status to activate")
	}

	contract.Status = ContractStatusActive
	contract.UpdatedAt = time.Now()

	logger.Info("Contract %s activated", contractID)
	return nil
}

// TerminateContract terminates a contract
func (vm *VendorManager) TerminateContract(contractID string, reason string) error {
	contract, exists := vm.contracts[contractID]
	if !exists {
		return fmt.Errorf("contract %s not found", contractID)
	}

	contract.Status = ContractStatusTerminated
	contract.UpdatedAt = time.Now()

	logger.Info("Contract %s terminated: %s", contractID, reason)
	return nil
}

// RenewContract renews a contract
func (vm *VendorManager) RenewContract(contractID string, newEndDate time.Time, newValue float64) error {
	contract, exists := vm.contracts[contractID]
	if !exists {
		return fmt.Errorf("contract %s not found", contractID)
	}

	contract.EndDate = newEndDate
	contract.Value = newValue
	contract.Status = ContractStatusRenewed
	contract.UpdatedAt = time.Now()

	logger.Info("Contract %s renewed until %s", contractID, newEndDate.Format("2006-01-02"))
	return nil
}

// GetVendorStatistics returns vendor statistics
func (vm *VendorManager) GetVendorStatistics() map[string]interface{} {
	stats := make(map[string]interface{})

	// Count by type
	typeCounts := make(map[VendorType]int)
	for _, vendor := range vm.vendors {
		typeCounts[vendor.Type]++
	}
	stats["vendor_type_counts"] = typeCounts

	// Count by status
	statusCounts := make(map[VendorStatus]int)
	for _, vendor := range vm.vendors {
		statusCounts[vendor.Status]++
	}
	stats["vendor_status_counts"] = statusCounts

	// Count contracts by type
	contractTypeCounts := make(map[ContractType]int)
	for _, contract := range vm.contracts {
		contractTypeCounts[contract.Type]++
	}
	stats["contract_type_counts"] = contractTypeCounts

	// Count contracts by status
	contractStatusCounts := make(map[ContractStatus]int)
	for _, contract := range vm.contracts {
		contractStatusCounts[contract.Status]++
	}
	stats["contract_status_counts"] = contractStatusCounts

	// Calculate averages
	var totalRating float64
	var ratingCount int
	var totalValue float64

	for _, vendor := range vm.vendors {
		totalRating += vendor.Rating
		ratingCount++
	}

	for _, contract := range vm.contracts {
		totalValue += contract.Value
	}

	if ratingCount > 0 {
		stats["average_rating"] = totalRating / float64(ratingCount)
	}

	stats["total_contract_value"] = totalValue
	stats["average_contract_value"] = totalValue / float64(len(vm.contracts))

	// Count expiring and expired
	stats["expiring_contracts"] = len(vm.GetExpiringContracts(30))
	stats["expired_contracts"] = len(vm.GetExpiredContracts())

	stats["total_vendors"] = len(vm.vendors)
	stats["total_contracts"] = len(vm.contracts)

	return stats
}

// GetVendorMetrics returns vendor metrics
func (vm *VendorManager) GetVendorMetrics() *VendorMetrics {
	// Update metrics
	vm.metrics.TotalVendors = int64(len(vm.vendors))
	vm.metrics.TotalContracts = int64(len(vm.contracts))

	// Count vendors by status
	vm.metrics.ActiveVendors = 0
	vm.metrics.InactiveVendors = 0
	vm.metrics.SuspendedVendors = 0
	vm.metrics.BlacklistedVendors = 0

	for _, vendor := range vm.vendors {
		switch vendor.Status {
		case VendorStatusActive:
			vm.metrics.ActiveVendors++
		case VendorStatusInactive:
			vm.metrics.InactiveVendors++
		case VendorStatusSuspended:
			vm.metrics.SuspendedVendors++
		case VendorStatusBlacklisted:
			vm.metrics.BlacklistedVendors++
		}
	}

	// Count contracts by status
	vm.metrics.ActiveContracts = 0
	vm.metrics.ExpiredContracts = 0
	vm.metrics.ExpiringContracts = 0

	now := time.Now()
	expiringCutoff := now.AddDate(0, 0, 30)

	for _, contract := range vm.contracts {
		switch contract.Status {
		case ContractStatusActive:
			vm.metrics.ActiveContracts++
			if contract.EndDate.Before(now) {
				vm.metrics.ExpiredContracts++
			} else if contract.EndDate.Before(expiringCutoff) {
				vm.metrics.ExpiringContracts++
			}
		case ContractStatusExpired:
			vm.metrics.ExpiredContracts++
		}
	}

	// Calculate average rating
	var totalRating float64
	var ratingCount int
	for _, vendor := range vm.vendors {
		totalRating += vendor.Rating
		ratingCount++
	}

	if ratingCount > 0 {
		vm.metrics.AverageRating = totalRating / float64(ratingCount)
	}

	// Calculate total and average contract value
	var totalValue float64
	for _, contract := range vm.contracts {
		totalValue += contract.Value
	}

	vm.metrics.TotalContractValue = totalValue
	if len(vm.contracts) > 0 {
		vm.metrics.AverageContractValue = totalValue / float64(len(vm.contracts))
	}

	return vm.metrics
}

// Helper methods

// SortVendorsByRating sorts vendors by rating
func (vm *VendorManager) SortVendorsByRating(vendors []*Vendor) []*Vendor {
	sort.Slice(vendors, func(i, j int) bool {
		return vendors[i].Rating > vendors[j].Rating
	})
	return vendors
}

// SortVendorsByName sorts vendors by name
func (vm *VendorManager) SortVendorsByName(vendors []*Vendor) []*Vendor {
	sort.Slice(vendors, func(i, j int) bool {
		return vendors[i].Name < vendors[j].Name
	})
	return vendors
}

// SortContractsByEndDate sorts contracts by end date
func (vm *VendorManager) SortContractsByEndDate(contracts []*Contract) []*Contract {
	sort.Slice(contracts, func(i, j int) bool {
		return contracts[i].EndDate.Before(contracts[j].EndDate)
	})
	return contracts
}

// SortContractsByValue sorts contracts by value
func (vm *VendorManager) SortContractsByValue(contracts []*Contract) []*Contract {
	sort.Slice(contracts, func(i, j int) bool {
		return contracts[i].Value > contracts[j].Value
	})
	return contracts
}

// GetVendorsByDateRange returns vendors created within a date range
func (vm *VendorManager) GetVendorsByDateRange(startDate, endDate time.Time) []*Vendor {
	var vendors []*Vendor
	for _, vendor := range vm.vendors {
		if vendor.CreatedAt.After(startDate) && vendor.CreatedAt.Before(endDate) {
			vendors = append(vendors, vendor)
		}
	}
	return vendors
}

// GetContractsByDateRange returns contracts created within a date range
func (vm *VendorManager) GetContractsByDateRange(startDate, endDate time.Time) []*Contract {
	var contracts []*Contract
	for _, contract := range vm.contracts {
		if contract.CreatedAt.After(startDate) && contract.CreatedAt.Before(endDate) {
			contracts = append(contracts, contract)
		}
	}
	return contracts
}
