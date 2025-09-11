package particles

import (
	"fmt"
	"math"
	"math/rand"
)

// ElectricalParticle represents an electron with electrical properties
type ElectricalParticle struct {
	Particle
	Voltage     float64 // Voltage at this point
	Current     float64 // Current flow (amperage)
	Resistance  float64 // Local resistance
	Power       float64 // Power dissipation (W = V * I)
	Temperature float64 // Heat from resistance
}

// ElectricalSystem simulates real electrical physics
type ElectricalSystem struct {
	*System
	SourceVoltage float64              // Supply voltage (e.g., 120V, 240V)
	TotalCurrent  float64              // Total system current
	Components    []ElectricalComponent // Resistors, loads, etc.
	Conductors    []Conductor           // Wires and paths
	GroundPlane   float64              // Y-position of ground
}

// ElectricalComponent represents a load or element in the circuit
type ElectricalComponent struct {
	X, Y       float64
	Width      float64
	Height     float64
	Resistance float64 // Ohms
	Type       ComponentType
	Name       string
	IsFault    bool // Short circuit or ground fault
}

// ComponentType defines different electrical components
type ComponentType int

const (
	ComponentWire ComponentType = iota
	ComponentOutlet
	ComponentBreaker
	ComponentPanel
	ComponentLoad      // Light, motor, etc.
	ComponentGround
	ComponentTransformer
)

// Conductor represents a wire or electrical path
type Conductor struct {
	StartX, StartY float64
	EndX, EndY     float64
	Gauge          int     // AWG wire gauge
	Length         float64 // Meters
	Material       string  // Copper, aluminum
	Ampacity       float64 // Max safe current
}

// NewElectricalSystem creates a system with real electrical physics
func NewElectricalSystem(width, height int, voltage float64) *ElectricalSystem {
	return &ElectricalSystem{
		System:        NewSystem(width, height),
		SourceVoltage: voltage,
		Components:    make([]ElectricalComponent, 0),
		Conductors:    make([]Conductor, 0),
		GroundPlane:   float64(height - 1),
	}
}

// CalculateOhmsLaw applies V = I * R to determine current flow
func (es *ElectricalSystem) CalculateOhmsLaw() {
	// Calculate total circuit resistance
	totalResistance := es.calculateTotalResistance()
	
	// Apply Ohm's Law: I = V / R
	if totalResistance > 0 {
		es.TotalCurrent = es.SourceVoltage / totalResistance
	} else {
		// Short circuit condition!
		es.TotalCurrent = es.SourceVoltage / 0.001 // Massive current
	}
}

// calculateTotalResistance sums resistance through the circuit path
func (es *ElectricalSystem) calculateTotalResistance() float64 {
	resistance := 0.1 // Minimal wire resistance
	
	// Add component resistances (series circuit for simplicity)
	for _, comp := range es.Components {
		if !comp.IsFault {
			resistance += comp.Resistance
		} else {
			// Fault creates very low resistance path
			return 0.001
		}
	}
	
	// Add conductor resistance based on length and gauge
	for _, conductor := range es.Conductors {
		resistance += es.calculateWireResistance(conductor)
	}
	
	return resistance
}

// calculateWireResistance uses real wire properties
func (es *ElectricalSystem) calculateWireResistance(c Conductor) float64 {
	// Resistance per meter for different AWG gauges (copper at 20°C)
	// R = ρ * L / A where ρ is resistivity
	resistancePerMeter := map[int]float64{
		10: 0.00328, // 10 AWG
		12: 0.00521, // 12 AWG  
		14: 0.00829, // 14 AWG (typical 15A circuit)
		16: 0.0132,  // 16 AWG
		18: 0.0210,  // 18 AWG
	}
	
	rpm, exists := resistancePerMeter[c.Gauge]
	if !exists {
		rpm = 0.00829 // Default to 14 AWG
	}
	
	return rpm * c.Length
}

// CalculateVoltageDrop determines voltage loss along conductors
func (es *ElectricalSystem) CalculateVoltageDrop(conductor Conductor, current float64) float64 {
	// Voltage drop: V_drop = I * R
	resistance := es.calculateWireResistance(conductor)
	return current * resistance
}

// SimulateCurrentFlow creates particles following electrical physics
func (es *ElectricalSystem) SimulateCurrentFlow() {
	es.CalculateOhmsLaw()
	
	// Particle density based on current magnitude
	particleRate := math.Min(es.TotalCurrent/10, 20) // Scale for visualization
	
	// Find electrical paths
	for _, conductor := range es.Conductors {
		// Calculate local voltage considering drops
		voltageDrop := es.CalculateVoltageDrop(conductor, es.TotalCurrent)
		localVoltage := es.SourceVoltage - voltageDrop
		
		// Spawn particles along conductor
		steps := int(conductor.Length * 10)
		for i := 0; i < steps; i++ {
			if rand.Float64() < particleRate/float64(steps) {
				t := float64(i) / float64(steps)
				x := conductor.StartX + t*(conductor.EndX-conductor.StartX)
				y := conductor.StartY + t*(conductor.EndY-conductor.StartY)
				
				p := es.createElectricalParticle(x, y, localVoltage, es.TotalCurrent)
				es.Particles = append(es.Particles, p)
			}
		}
	}
}

// createElectricalParticle makes a particle with electrical properties
func (es *ElectricalSystem) createElectricalParticle(x, y, voltage, current float64) Particle {
	// Particle speed proportional to current (drift velocity)
	// Real electron drift is slow (~mm/s) but we scale for visualization
	speed := math.Min(current*2, 10)
	
	// Particle intensity based on power (P = V * I)
	power := voltage * current
	intensity := math.Min(power/100, 1.0)
	
	// Character based on voltage level
	var char rune
	switch {
	case voltage > 200:
		char = '⚡' // High voltage
	case voltage > 100:
		char = '±'  // Standard voltage
	case voltage > 50:
		char = '∓'  // Reduced voltage
	default:
		char = '·'  // Low voltage
	}
	
	// Add thermal effects from resistance (I²R heating)
	heat := current * current * 0.01 // Simplified heating
	
	return Particle{
		X:            x,
		Y:            y,
		VX:           speed + (rand.Float64()-0.5)*2,
		VY:           (rand.Float64() - 0.5) * 0.5,
		Life:         1.0,
		MaxLife:      0.5 + rand.Float64(),
		Char:         char,
		Intensity:    intensity,
		Type:         TypeElectric,
		GravityScale: -heat * 0.1, // Heat makes particles rise
	}
}

// DetectFaults identifies electrical problems
func (es *ElectricalSystem) DetectFaults() []string {
	var faults []string
	
	// Check for overcurrent
	for _, conductor := range es.Conductors {
		if es.TotalCurrent > conductor.Ampacity {
			ratio := es.TotalCurrent / conductor.Ampacity
			msg := fmt.Sprintf(
				"OVERCURRENT: Wire rated for %.1fA carrying %.1fA (%.0f%% overload)",
				conductor.Ampacity, es.TotalCurrent, (ratio-1)*100)
			faults = append(faults, msg)
		}
	}
	
	// Check voltage drop (NEC recommends < 3% for branch circuits)
	totalDrop := 0.0
	for _, conductor := range es.Conductors {
		totalDrop += es.CalculateVoltageDrop(conductor, es.TotalCurrent)
	}
	dropPercent := (totalDrop / es.SourceVoltage) * 100
	if dropPercent > 3.0 {
		msg := fmt.Sprintf(
			"VOLTAGE DROP: %.1fV drop (%.1f%% - exceeds 3%% limit)",
			totalDrop, dropPercent)
		faults = append(faults, msg)
	}
	
	// Check for ground faults
	for _, comp := range es.Components {
		if comp.IsFault {
			msg := fmt.Sprintf("GROUND FAULT: Detected at %s", comp.Name)
			faults = append(faults, msg)
		}
	}
	
	return faults
}

// AddCircuitBreaker adds a breaker that trips on overcurrent
func (es *ElectricalSystem) AddCircuitBreaker(x, y float64, rating float64) {
	breaker := ElectricalComponent{
		X:          x,
		Y:          y,
		Width:      3,
		Height:     2,
		Resistance: 0.01, // Minimal resistance when closed
		Type:       ComponentBreaker,
		Name:       "Breaker",
		IsFault:    false,
	}
	
	// Check if breaker should trip
	if es.TotalCurrent > rating {
		breaker.Resistance = 1e6 // Very high resistance when tripped
		breaker.IsFault = true
		breaker.Name = "Breaker (TRIPPED)"
	}
	
	es.Components = append(es.Components, breaker)
}

// SimulateArcFault creates dangerous arcing effects
func (es *ElectricalSystem) SimulateArcFault(x, y float64) {
	// Arc creates extremely hot, erratic particles
	for i := 0; i < 20; i++ {
		p := Particle{
			X:            x + (rand.Float64()-0.5)*5,
			Y:            y + (rand.Float64()-0.5)*5,
			VX:           (rand.Float64() - 0.5) * 20,
			VY:           (rand.Float64() - 0.5) * 20,
			Life:         1.0,
			MaxLife:      0.2,
			Char:         '✦',
			Intensity:    1.0,
			Type:         TypeElectric,
			GravityScale: -2.0, // Intense heat rises
		}
		es.Particles = append(es.Particles, p)
	}
}