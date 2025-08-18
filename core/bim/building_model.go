package bim

import (
	"sync"
	"math"
	"github.com/arxos/arxos/core/arxobject"
)

// BuildingModel represents a complete building information model
type BuildingModel struct {
	ID       string
	Name     string
	Address  string
	Floors   []*Floor
	Systems  *SystemsModel
	Metadata map[string]interface{}
	
	// Spatial indexing
	spatialIndex *SpatialIndex
	
	// Real-time collaboration
	subscribers []chan Update
	mu          sync.RWMutex
}

// Floor represents a building floor with all its elements
type Floor struct {
	ID        string
	Number    int
	Elevation float64 // meters
	Height    float64 // floor-to-floor height
	
	// Structural elements
	Walls    []*Wall
	Columns  []*Column
	Slabs    []*Slab
	
	// Spaces
	Rooms    []*Room
	Corridors []*Corridor
	
	// Openings
	Doors    []*Door
	Windows  []*Window
	
	// MEP Components
	Electrical *ElectricalSystem
	HVAC       *HVACSystem
	Plumbing   *PlumbingSystem
	
	// Rendering cache
	svgCache  string
	isDirty   bool
}

// Wall represents an intelligent wall object
type Wall struct {
	ID          string
	Type        WallType
	
	// Geometry - stored as line segment with thickness
	StartPoint  Point3D
	EndPoint    Point3D
	Thickness   float64
	Height      float64
	
	// Relationships
	ConnectedWalls []*WallConnection
	HostedObjects  []HostedObject // Outlets, switches, etc.
	Openings      []*Opening      // Doors, windows
	
	// Properties
	Material    Material
	FireRating  string
	Insulation  *InsulationSpec
	IsLoadBearing bool
	
	// Rendering
	Style       RenderStyle
	Constraints []Constraint
}

// Room represents an intelligent space
type Room struct {
	ID       string
	Number   string
	Name     string
	Type     RoomType
	
	// Geometry - polygon boundary
	Boundary []Point3D
	Height   float64
	Area     float64 // Calculated
	Volume   float64 // Calculated
	
	// Relationships
	BoundingWalls []*Wall
	Doors        []*Door
	Windows      []*Window
	
	// Systems
	Outlets      []*ElectricalOutlet
	Lights       []*LightFixture
	HVACTerminals []*HVACTerminal
	Plumbing     []*PlumbingFixture
	
	// Occupancy & Code
	MaxOccupancy int
	UseType      string
	RequiredVentilation float64
}

// ElectricalSystem manages all electrical components on a floor
type ElectricalSystem struct {
	Panels       []*ElectricalPanel
	Circuits     []*Circuit
	Outlets      []*ElectricalOutlet
	Switches     []*Switch
	Lights       []*LightFixture
	Conduits     []*Conduit
	CableTrays   []*CableTray
	
	// Calculations
	LoadCalcs    *LoadCalculation
	VoltageDrops map[string]float64
}

// HVACSystem manages HVAC components
type HVACSystem struct {
	AirHandlers  []*AirHandler
	VAVBoxes     []*VAVBox
	Diffusers    []*Diffuser
	ReturnGrilles []*ReturnGrille
	Ductwork     []*Duct
	Refrigerant  []*RefrigerantPipe
	
	// Calculations
	CoolingLoads map[string]float64
	HeatingLoads map[string]float64
	AirflowCalcs *AirflowCalculation
}

// Interactive Operations

// AddWall adds a new wall to the floor
func (f *Floor) AddWall(start, end Point3D, thickness float64, wallType WallType) *Wall {
	wall := &Wall{
		ID:         generateID("WALL"),
		Type:       wallType,
		StartPoint: start,
		EndPoint:   end,
		Thickness:  thickness,
		Height:     f.Height,
		ConnectedWalls: make([]*WallConnection, 0),
		HostedObjects:  make([]HostedObject, 0),
	}
	
	// Find intersections with existing walls
	for _, existingWall := range f.Walls {
		if intersection := findWallIntersection(wall, existingWall); intersection != nil {
			// Split walls at intersection
			f.splitWallsAtIntersection(wall, existingWall, intersection)
		}
	}
	
	f.Walls = append(f.Walls, wall)
	f.isDirty = true
	f.updateRooms() // Recalculate room boundaries
	
	return wall
}

// AddOutlet adds an electrical outlet to a wall
func (w *Wall) AddOutlet(position float64, height float64) *ElectricalOutlet {
	outlet := &ElectricalOutlet{
		ID:       generateID("OUTLET"),
		Position: w.interpolatePoint(position),
		Height:   height,
		HostWall: w,
		Voltage:  120,
		Amperage: 20,
	}
	
	w.HostedObjects = append(w.HostedObjects, outlet)
	return outlet
}

// SplitForDoor splits a wall to add a door
func (w *Wall) SplitForDoor(position float64, doorWidth float64) (*Wall, *Wall, *Door) {
	// Calculate split points
	doorStart := position - doorWidth/2
	doorEnd := position + doorWidth/2
	
	// Create two new wall segments
	wall1 := &Wall{
		ID:         generateID("WALL"),
		Type:       w.Type,
		StartPoint: w.StartPoint,
		EndPoint:   w.interpolatePoint(doorStart),
		Thickness:  w.Thickness,
		Height:     w.Height,
		Material:   w.Material,
	}
	
	wall2 := &Wall{
		ID:         generateID("WALL"),
		Type:       w.Type,
		StartPoint: w.interpolatePoint(doorEnd),
		EndPoint:   w.EndPoint,
		Thickness:  w.Thickness,
		Height:     w.Height,
		Material:   w.Material,
	}
	
	// Create door
	door := &Door{
		ID:       generateID("DOOR"),
		Position: w.interpolatePoint(position),
		Width:    doorWidth,
		Height:   2100, // Standard door height mm
		HostWall: w,
	}
	
	return wall1, wall2, door
}

// Real-time Updates

// Subscribe to model changes for real-time updates
func (bm *BuildingModel) Subscribe() <-chan Update {
	bm.mu.Lock()
	defer bm.mu.Unlock()
	
	ch := make(chan Update, 100)
	bm.subscribers = append(bm.subscribers, ch)
	return ch
}

// Broadcast sends updates to all subscribers
func (bm *BuildingModel) broadcast(update Update) {
	bm.mu.RLock()
	defer bm.mu.RUnlock()
	
	for _, ch := range bm.subscribers {
		select {
		case ch <- update:
		default:
			// Don't block if subscriber is slow
		}
	}
}

// Update represents a model change
type Update struct {
	Type      string      // "wall_added", "outlet_added", etc.
	FloorID   string
	ObjectID  string
	Data      interface{}
	Timestamp int64
}

// Rendering

// RenderToSVG generates SVG representation of the floor
func (f *Floor) RenderToSVG() string {
	if !f.isDirty && f.svgCache != "" {
		return f.svgCache
	}
	
	svg := `<svg viewBox="0 0 10000 10000" xmlns="http://www.w3.org/2000/svg">`
	
	// Render walls
	for _, wall := range f.Walls {
		svg += wall.renderToSVG()
	}
	
	// Render rooms (as semi-transparent fills)
	for _, room := range f.Rooms {
		svg += room.renderToSVG()
	}
	
	// Render doors
	for _, door := range f.Doors {
		svg += door.renderToSVG()
	}
	
	// Render MEP systems (if visible)
	if f.Electrical != nil {
		svg += f.Electrical.renderToSVG()
	}
	
	svg += `</svg>`
	
	f.svgCache = svg
	f.isDirty = false
	
	return svg
}

// Helper functions

func (w *Wall) interpolatePoint(t float64) Point3D {
	// t is 0-1 along the wall length
	return Point3D{
		X: w.StartPoint.X + t*(w.EndPoint.X-w.StartPoint.X),
		Y: w.StartPoint.Y + t*(w.EndPoint.Y-w.StartPoint.Y),
		Z: w.StartPoint.Z + t*(w.EndPoint.Z-w.StartPoint.Z),
	}
}

func (w *Wall) renderToSVG() string {
	// Calculate perpendicular offset for wall thickness
	dx := w.EndPoint.X - w.StartPoint.X
	dy := w.EndPoint.Y - w.StartPoint.Y
	length := math.Sqrt(dx*dx + dy*dy)
	
	// Perpendicular vector
	px := -dy / length * w.Thickness / 2
	py := dx / length * w.Thickness / 2
	
	// Four corners of the wall
	x1 := w.StartPoint.X - px
	y1 := w.StartPoint.Y - py
	x2 := w.StartPoint.X + px
	y2 := w.StartPoint.Y + py
	x3 := w.EndPoint.X + px
	y3 := w.EndPoint.Y + py
	x4 := w.EndPoint.X - px
	y4 := w.EndPoint.Y - py
	
	style := `fill="#333" stroke="#000" stroke-width="1"`
	if w.Type == WallTypeExterior {
		style = `fill="#000" stroke="#000" stroke-width="2"`
	}
	
	return fmt.Sprintf(
		`<polygon points="%.0f,%.0f %.0f,%.0f %.0f,%.0f %.0f,%.0f" %s class="wall" data-id="%s"/>`,
		x1, y1, x2, y2, x3, y3, x4, y4, style, w.ID,
	)
}

// Types

type WallType int
const (
	WallTypeInterior WallType = iota
	WallTypeExterior
	WallTypePartition
	WallTypeCurtain
	WallTypeRetaining
)

type RoomType int
const (
	RoomTypeOffice RoomType = iota
	RoomTypeCorridor
	RoomTypeRestroom
	RoomTypeConference
	RoomTypeMechanical
	RoomTypeElectrical
	RoomTypeStorage
)

type Point3D struct {
	X, Y, Z float64
}

type Material struct {
	Name         string
	Density      float64
	ThermalR     float64
	FireRating   string
	SoundRating  float64
}