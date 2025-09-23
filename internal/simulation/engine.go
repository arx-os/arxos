package simulation

import (
	"context"
	"fmt"
	"math"
	"math/rand"
	"time"

	"github.com/arx-os/arxos/internal/common/logger"
	"github.com/arx-os/arxos/pkg/models"
)

// SimulationType defines the type of simulation
type SimulationType string

const (
	SimTypeOccupancy   SimulationType = "occupancy"
	SimTypeHVAC        SimulationType = "hvac"
	SimTypeEnergy      SimulationType = "energy"
	SimTypeLighting    SimulationType = "lighting"
	SimTypeEvacuation  SimulationType = "evacuation"
	SimTypeMaintenance SimulationType = "maintenance"
)

// SimulationResult contains the results of a simulation
type SimulationResult struct {
	Type       SimulationType         `json:"type"`
	BuildingID string                 `json:"building_id"`
	StartTime  time.Time              `json:"start_time"`
	EndTime    time.Time              `json:"end_time"`
	Metrics    map[string]interface{} `json:"metrics"`
	Events     []SimulationEvent      `json:"events"`
	Summary    string                 `json:"summary"`
}

// SimulationEvent represents an event during simulation
type SimulationEvent struct {
	Timestamp time.Time              `json:"timestamp"`
	Type      string                 `json:"type"`
	Location  string                 `json:"location"`
	Data      map[string]interface{} `json:"data"`
}

// Engine manages simulations
type Engine struct {
	random *rand.Rand
}

// NewEngine creates a new simulation engine
func NewEngine() *Engine {
	return &Engine{
		random: rand.New(rand.NewSource(time.Now().UnixNano())),
	}
}

// RunSimulation executes a simulation on a building
func (e *Engine) RunSimulation(ctx context.Context, building *models.FloorPlan, simType SimulationType, realtime bool) (*SimulationResult, error) {
	logger.Info("Starting %s simulation for building %s", simType, building.ID)

	result := &SimulationResult{
		Type:       simType,
		BuildingID: building.ID,
		StartTime:  time.Now(),
		Metrics:    make(map[string]interface{}),
		Events:     []SimulationEvent{},
	}

	switch simType {
	case SimTypeOccupancy:
		err := e.simulateOccupancy(ctx, building, result, realtime)
		if err != nil {
			return nil, fmt.Errorf("occupancy simulation failed: %w", err)
		}

	case SimTypeHVAC:
		err := e.simulateHVAC(ctx, building, result, realtime)
		if err != nil {
			return nil, fmt.Errorf("HVAC simulation failed: %w", err)
		}

	case SimTypeEnergy:
		err := e.simulateEnergy(ctx, building, result, realtime)
		if err != nil {
			return nil, fmt.Errorf("energy simulation failed: %w", err)
		}

	case SimTypeLighting:
		err := e.simulateLighting(ctx, building, result, realtime)
		if err != nil {
			return nil, fmt.Errorf("lighting simulation failed: %w", err)
		}

	case SimTypeEvacuation:
		err := e.simulateEvacuation(ctx, building, result, realtime)
		if err != nil {
			return nil, fmt.Errorf("evacuation simulation failed: %w", err)
		}

	case SimTypeMaintenance:
		err := e.simulateMaintenance(ctx, building, result, realtime)
		if err != nil {
			return nil, fmt.Errorf("maintenance simulation failed: %w", err)
		}

	default:
		return nil, fmt.Errorf("unknown simulation type: %s", simType)
	}

	result.EndTime = time.Now()
	result.Summary = e.generateSummary(result)

	logger.Info("Completed %s simulation for building %s", simType, building.ID)
	return result, nil
}

// simulateOccupancy simulates building occupancy patterns
func (e *Engine) simulateOccupancy(ctx context.Context, building *models.FloorPlan, result *SimulationResult, realtime bool) error {
	logger.Debug("Simulating occupancy for building %s", building.ID)

	// Simulate 24 hours of occupancy
	startTime := time.Now().Truncate(24 * time.Hour)
	totalOccupancy := 0
	peakOccupancy := 0
	occupancyByHour := make([]int, 24)

	for hour := 0; hour < 24; hour++ {
		// Simulate occupancy based on typical patterns
		occupancy := e.calculateOccupancy(hour, building)
		occupancyByHour[hour] = occupancy
		totalOccupancy += occupancy

		if occupancy > peakOccupancy {
			peakOccupancy = occupancy
		}

		// Record event
		event := SimulationEvent{
			Timestamp: startTime.Add(time.Duration(hour) * time.Hour),
			Type:      "occupancy_update",
			Location:  "building",
			Data: map[string]interface{}{
				"hour":      hour,
				"occupancy": occupancy,
			},
		}
		result.Events = append(result.Events, event)

		if realtime {
			select {
			case <-ctx.Done():
				return ctx.Err()
			case <-time.After(100 * time.Millisecond): // Simulate realtime delay
			}
		}
	}

	// Store metrics
	result.Metrics["average_occupancy"] = totalOccupancy / 24
	result.Metrics["peak_occupancy"] = peakOccupancy
	result.Metrics["peak_hour"] = e.findPeakHour(occupancyByHour)
	result.Metrics["occupancy_by_hour"] = occupancyByHour
	result.Metrics["utilization_rate"] = float64(peakOccupancy) / float64(e.estimateCapacity(building))

	return nil
}

// simulateHVAC simulates HVAC operations
func (e *Engine) simulateHVAC(ctx context.Context, building *models.FloorPlan, result *SimulationResult, realtime bool) error {
	logger.Debug("Simulating HVAC for building %s", building.ID)

	// Simulate temperature control for 24 hours
	externalTemp := 25.0 // External temperature in Celsius
	targetTemp := 22.0   // Target internal temperature
	currentTemp := 23.0   // Current internal temperature
	totalEnergyUsage := 0.0
	temperatures := []float64{}

	for hour := 0; hour < 24; hour++ {
		// Simulate external temperature variation
		externalTemp = 20 + 10*math.Sin(float64(hour)*math.Pi/12)

		// Calculate HVAC response
		tempDiff := targetTemp - currentTemp
		hvacPower := e.calculateHVACPower(tempDiff, currentTemp, externalTemp)
		energyUsage := hvacPower * 1.0 // kWh for 1 hour
		totalEnergyUsage += energyUsage

		// Update internal temperature
		currentTemp = e.updateTemperature(currentTemp, externalTemp, hvacPower)
		temperatures = append(temperatures, currentTemp)

		// Record event
		event := SimulationEvent{
			Timestamp: time.Now().Add(time.Duration(hour) * time.Hour),
			Type:      "hvac_update",
			Location:  "building",
			Data: map[string]interface{}{
				"hour":          hour,
				"external_temp": externalTemp,
				"internal_temp": currentTemp,
				"hvac_power":    hvacPower,
				"energy_usage":  energyUsage,
			},
		}
		result.Events = append(result.Events, event)

		if realtime {
			select {
			case <-ctx.Done():
				return ctx.Err()
			case <-time.After(100 * time.Millisecond):
			}
		}
	}

	result.Metrics["total_energy_usage"] = totalEnergyUsage
	result.Metrics["average_temperature"] = e.average(temperatures)
	result.Metrics["temperature_variance"] = e.variance(temperatures)
	result.Metrics["efficiency_rating"] = e.calculateEfficiency(totalEnergyUsage, building)

	return nil
}

// simulateEnergy simulates overall energy consumption
func (e *Engine) simulateEnergy(ctx context.Context, building *models.FloorPlan, result *SimulationResult, realtime bool) error {
	logger.Debug("Simulating energy consumption for building %s", building.ID)

	totalConsumption := 0.0
	peakDemand := 0.0
	consumptionByHour := []float64{}

	for hour := 0; hour < 24; hour++ {
		// Calculate energy consumption for different systems
		lighting := e.calculateLightingEnergy(hour, building)
		hvac := e.calculateHVACEnergy(hour, building)
		equipment := e.calculateEquipmentEnergy(hour, building)
		other := e.random.Float64() * 10 // Random other consumption

		hourlyConsumption := lighting + hvac + equipment + other
		consumptionByHour = append(consumptionByHour, hourlyConsumption)
		totalConsumption += hourlyConsumption

		if hourlyConsumption > peakDemand {
			peakDemand = hourlyConsumption
		}

		event := SimulationEvent{
			Timestamp: time.Now().Add(time.Duration(hour) * time.Hour),
			Type:      "energy_update",
			Location:  "building",
			Data: map[string]interface{}{
				"hour":        hour,
				"lighting":    lighting,
				"hvac":        hvac,
				"equipment":   equipment,
				"other":       other,
				"total":       hourlyConsumption,
			},
		}
		result.Events = append(result.Events, event)

		if realtime {
			select {
			case <-ctx.Done():
				return ctx.Err()
			case <-time.After(100 * time.Millisecond):
			}
		}
	}

	result.Metrics["total_consumption"] = totalConsumption
	result.Metrics["peak_demand"] = peakDemand
	result.Metrics["average_hourly"] = totalConsumption / 24
	result.Metrics["consumption_by_hour"] = consumptionByHour
	result.Metrics["estimated_cost"] = totalConsumption * 0.12 // $0.12 per kWh

	return nil
}

// simulateLighting simulates lighting control and optimization
func (e *Engine) simulateLighting(ctx context.Context, building *models.FloorPlan, result *SimulationResult, realtime bool) error {
	logger.Debug("Simulating lighting for building %s", building.ID)

	totalUsage := 0.0
	lightingByZone := make(map[string]float64)

	// Simulate different lighting zones
	zones := []string{"entrance", "offices", "corridors", "parking", "exterior"}

	for hour := 0; hour < 24; hour++ {
		hourlyUsage := 0.0

		for _, zone := range zones {
			// Calculate lighting needs based on zone and time
			usage := e.calculateZoneLighting(zone, hour)
			lightingByZone[zone] += usage
			hourlyUsage += usage
		}

		totalUsage += hourlyUsage

		event := SimulationEvent{
			Timestamp: time.Now().Add(time.Duration(hour) * time.Hour),
			Type:      "lighting_update",
			Location:  "building",
			Data: map[string]interface{}{
				"hour":  hour,
				"usage": hourlyUsage,
				"zones": lightingByZone,
			},
		}
		result.Events = append(result.Events, event)

		if realtime {
			select {
			case <-ctx.Done():
				return ctx.Err()
			case <-time.After(100 * time.Millisecond):
			}
		}
	}

	result.Metrics["total_lighting_usage"] = totalUsage
	result.Metrics["usage_by_zone"] = lightingByZone
	result.Metrics["potential_savings"] = totalUsage * 0.3 // 30% potential savings with optimization

	return nil
}

// simulateEvacuation simulates emergency evacuation
func (e *Engine) simulateEvacuation(ctx context.Context, building *models.FloorPlan, result *SimulationResult, realtime bool) error {
	logger.Debug("Simulating evacuation for building %s", building.ID)

	// Estimate building occupancy
	occupants := e.estimateCapacity(building)
	evacuated := 0
	minutes := 0
	evacuationRate := occupants / 10 // People evacuated per minute

	for evacuated < occupants {
		minutes++

		// Calculate evacuation progress
		evacuating := evacuationRate
		if evacuated+evacuating > occupants {
			evacuating = occupants - evacuated
		}
		evacuated += evacuating

		event := SimulationEvent{
			Timestamp: time.Now().Add(time.Duration(minutes) * time.Minute),
			Type:      "evacuation_progress",
			Location:  "building",
			Data: map[string]interface{}{
				"minute":    minutes,
				"evacuated": evacuated,
				"remaining": occupants - evacuated,
				"percent":   float64(evacuated) / float64(occupants) * 100,
			},
		}
		result.Events = append(result.Events, event)

		if realtime {
			select {
			case <-ctx.Done():
				return ctx.Err()
			case <-time.After(100 * time.Millisecond):
			}
		}
	}

	result.Metrics["total_occupants"] = occupants
	result.Metrics["evacuation_time_minutes"] = minutes
	result.Metrics["evacuation_rate"] = evacuationRate
	result.Metrics["safety_rating"] = e.calculateSafetyRating(minutes)

	return nil
}

// simulateMaintenance simulates maintenance requirements
func (e *Engine) simulateMaintenance(ctx context.Context, building *models.FloorPlan, result *SimulationResult, realtime bool) error {
	logger.Debug("Simulating maintenance for building %s", building.ID)

	// Simulate equipment maintenance over a year
	maintenanceEvents := []string{}
	totalCost := 0.0
	equipmentTypes := []string{"HVAC", "Elevator", "Lighting", "Plumbing", "Electrical", "Fire Safety"}

	for month := 1; month <= 12; month++ {
		for _, equipment := range equipmentTypes {
			// Random chance of maintenance needed
			if e.random.Float64() < e.maintenanceProbability(equipment, month) {
				cost := e.maintenanceCost(equipment)
				totalCost += cost

				eventDesc := fmt.Sprintf("Month %d: %s maintenance - $%.2f", month, equipment, cost)
				maintenanceEvents = append(maintenanceEvents, eventDesc)

				event := SimulationEvent{
					Timestamp: time.Now().AddDate(0, month-1, 0),
					Type:      "maintenance_required",
					Location:  equipment,
					Data: map[string]interface{}{
						"month":     month,
						"equipment": equipment,
						"cost":      cost,
					},
				}
				result.Events = append(result.Events, event)
			}
		}

		if realtime {
			select {
			case <-ctx.Done():
				return ctx.Err()
			case <-time.After(100 * time.Millisecond):
			}
		}
	}

	result.Metrics["annual_maintenance_cost"] = totalCost
	result.Metrics["maintenance_events"] = len(maintenanceEvents)
	result.Metrics["average_monthly_cost"] = totalCost / 12
	result.Metrics["maintenance_schedule"] = maintenanceEvents

	return nil
}

// Helper functions

func (e *Engine) calculateOccupancy(hour int, building *models.FloorPlan) int {
	capacity := e.estimateCapacity(building)

	// Typical office occupancy pattern
	var occupancyPercent float64
	switch {
	case hour < 7:
		occupancyPercent = 0.05
	case hour < 9:
		occupancyPercent = 0.3
	case hour < 12:
		occupancyPercent = 0.85
	case hour < 13:
		occupancyPercent = 0.5
	case hour < 17:
		occupancyPercent = 0.8
	case hour < 19:
		occupancyPercent = 0.3
	default:
		occupancyPercent = 0.1
	}

	// Add some randomness
	occupancyPercent += (e.random.Float64() - 0.5) * 0.1

	return int(float64(capacity) * occupancyPercent)
}

func (e *Engine) estimateCapacity(building *models.FloorPlan) int {
	// Estimate based on floor area (1 person per 10 square meters)
	if building.TotalArea > 0 {
		return int(building.TotalArea / 10)
	}
	return 100 // Default capacity
}

func (e *Engine) findPeakHour(occupancy []int) int {
	peakHour := 0
	peakValue := 0
	for hour, value := range occupancy {
		if value > peakValue {
			peakValue = value
			peakHour = hour
		}
	}
	return peakHour
}

func (e *Engine) calculateHVACPower(tempDiff, internalTemp, externalTemp float64) float64 {
	// Simple HVAC power calculation
	basePower := math.Abs(tempDiff) * 2.0
	externalFactor := math.Abs(externalTemp-internalTemp) * 0.5
	return basePower + externalFactor
}

func (e *Engine) updateTemperature(current, external, hvacPower float64) float64 {
	// Simulate temperature change
	externalInfluence := (external - current) * 0.1
	hvacInfluence := hvacPower * 0.3
	return current + externalInfluence + hvacInfluence
}

func (e *Engine) calculateEfficiency(energyUsage float64, building *models.FloorPlan) float64 {
	// Energy efficiency rating (0-100)
	baselineUsage := building.TotalArea * 0.15 // Baseline kWh per sq meter
	if baselineUsage == 0 {
		baselineUsage = 1000
	}
	efficiency := (1 - (energyUsage / baselineUsage)) * 100
	if efficiency < 0 {
		efficiency = 0
	}
	if efficiency > 100 {
		efficiency = 100
	}
	return efficiency
}

func (e *Engine) calculateLightingEnergy(hour int, building *models.FloorPlan) float64 {
	// Calculate lighting energy based on hour
	baseUsage := building.TotalArea * 0.01 // kWh per sq meter
	if baseUsage == 0 {
		baseUsage = 10
	}

	// Adjust for time of day
	var factor float64
	switch {
	case hour < 6 || hour > 22:
		factor = 0.1
	case hour < 8 || hour > 18:
		factor = 0.5
	default:
		factor = 1.0
	}

	return baseUsage * factor
}

func (e *Engine) calculateHVACEnergy(hour int, building *models.FloorPlan) float64 {
	baseUsage := building.TotalArea * 0.02
	if baseUsage == 0 {
		baseUsage = 20
	}

	// Higher usage during business hours
	var factor float64
	if hour >= 8 && hour <= 18 {
		factor = 1.2
	} else {
		factor = 0.6
	}

	return baseUsage * factor
}

func (e *Engine) calculateEquipmentEnergy(hour int, building *models.FloorPlan) float64 {
	baseUsage := building.TotalArea * 0.005
	if baseUsage == 0 {
		baseUsage = 5
	}

	// Equipment usage pattern
	var factor float64
	if hour >= 9 && hour <= 17 {
		factor = 1.0
	} else {
		factor = 0.2
	}

	return baseUsage * factor
}

func (e *Engine) calculateZoneLighting(zone string, hour int) float64 {
	// Zone-specific lighting calculations
	baseUsage := map[string]float64{
		"entrance":  5.0,
		"offices":   20.0,
		"corridors": 10.0,
		"parking":   15.0,
		"exterior":  8.0,
	}[zone]

	// Time-based adjustments
	var timeFactor float64
	switch zone {
	case "exterior", "parking":
		if hour < 6 || hour > 20 {
			timeFactor = 1.0
		} else {
			timeFactor = 0.1
		}
	case "offices":
		if hour >= 8 && hour <= 18 {
			timeFactor = 1.0
		} else {
			timeFactor = 0.1
		}
	default:
		if hour >= 7 && hour <= 21 {
			timeFactor = 0.8
		} else {
			timeFactor = 0.2
		}
	}

	return baseUsage * timeFactor
}

func (e *Engine) calculateSafetyRating(evacuationMinutes int) float64 {
	// Safety rating based on evacuation time
	if evacuationMinutes <= 3 {
		return 100.0
	} else if evacuationMinutes <= 5 {
		return 90.0
	} else if evacuationMinutes <= 8 {
		return 75.0
	} else if evacuationMinutes <= 10 {
		return 60.0
	}
	return 40.0
}

func (e *Engine) maintenanceProbability(equipment string, month int) float64 {
	// Base probability by equipment type
	baseProb := map[string]float64{
		"HVAC":        0.15,
		"Elevator":    0.10,
		"Lighting":    0.08,
		"Plumbing":    0.12,
		"Electrical":  0.10,
		"Fire Safety": 0.20, // Regular inspections
	}[equipment]

	// Seasonal adjustments
	if equipment == "HVAC" && (month == 6 || month == 12) {
		baseProb *= 2 // Higher in summer/winter
	}

	return baseProb
}

func (e *Engine) maintenanceCost(equipment string) float64 {
	// Average maintenance cost by equipment type
	baseCost := map[string]float64{
		"HVAC":        1500.0,
		"Elevator":    2000.0,
		"Lighting":    500.0,
		"Plumbing":    800.0,
		"Electrical":  1000.0,
		"Fire Safety": 600.0,
	}[equipment]

	// Add some randomness (±20%)
	variability := baseCost * 0.2 * (e.random.Float64() - 0.5) * 2
	return baseCost + variability
}

func (e *Engine) average(values []float64) float64 {
	if len(values) == 0 {
		return 0
	}
	sum := 0.0
	for _, v := range values {
		sum += v
	}
	return sum / float64(len(values))
}

func (e *Engine) variance(values []float64) float64 {
	if len(values) == 0 {
		return 0
	}
	avg := e.average(values)
	sum := 0.0
	for _, v := range values {
		diff := v - avg
		sum += diff * diff
	}
	return sum / float64(len(values))
}

func (e *Engine) generateSummary(result *SimulationResult) string {
	summary := fmt.Sprintf("Simulation completed in %.2f seconds. ", result.EndTime.Sub(result.StartTime).Seconds())

	switch result.Type {
	case SimTypeOccupancy:
		summary += fmt.Sprintf("Peak occupancy: %v at hour %v. Average: %v.",
			result.Metrics["peak_occupancy"],
			result.Metrics["peak_hour"],
			result.Metrics["average_occupancy"])

	case SimTypeHVAC:
		summary += fmt.Sprintf("Total energy usage: %.2f kWh. Efficiency rating: %.1f%%.",
			result.Metrics["total_energy_usage"],
			result.Metrics["efficiency_rating"])

	case SimTypeEnergy:
		summary += fmt.Sprintf("Total consumption: %.2f kWh. Estimated cost: $%.2f.",
			result.Metrics["total_consumption"],
			result.Metrics["estimated_cost"])

	case SimTypeLighting:
		summary += fmt.Sprintf("Total usage: %.2f kWh. Potential savings: %.2f kWh.",
			result.Metrics["total_lighting_usage"],
			result.Metrics["potential_savings"])

	case SimTypeEvacuation:
		summary += fmt.Sprintf("Evacuation completed in %v minutes. Safety rating: %.1f%%.",
			result.Metrics["evacuation_time_minutes"],
			result.Metrics["safety_rating"])

	case SimTypeMaintenance:
		summary += fmt.Sprintf("Annual maintenance cost: $%.2f. Events: %v.",
			result.Metrics["annual_maintenance_cost"],
			result.Metrics["maintenance_events"])
	}

	return summary
}