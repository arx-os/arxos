package bim

import (
	"fmt"
	"math"
	"strings"
	"sync"
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
		if intersection, found := findWallIntersection(wall, existingWall); found {
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
	
	w.HostedObjects = append(w.HostedObjects, HostedObject{
		ID:       outlet.ID,
		Type:     "outlet",
		Position: position,
		Height:   height,
	})
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
	
	// Render walls with proper SVG representation
	for _, wall := range f.Walls {
		svg += f.renderWallToSVG(wall)
	}
	
	// Render rooms as semi-transparent polygon fills
	for _, room := range f.Rooms {
		svg += f.renderRoomToSVG(room)
	}
	
	// Render doors with arc indicators
	for _, door := range f.Doors {
		svg += f.renderDoorToSVG(door)
	}
	
	// Render MEP systems with appropriate colors and symbols
	for _, mep := range f.MEP {
		svg += f.renderMEPToSVG(mep)
	}
	
	svg += `</svg>`
	
	f.svgCache = svg
	f.isDirty = false
	
	return svg
}

// Helper functions

// renderWallToSVG renders a wall using its existing method
func (f *Floor) renderWallToSVG(wall *Wall) string {
	return wall.renderToSVG()
}

// renderRoomToSVG renders a room as a polygon with label
func (f *Floor) renderRoomToSVG(room *Room) string {
	if len(room.Boundary) < 3 {
		return ""
	}
	
	// Build points string for polygon
	var points strings.Builder
	for i, point := range room.Boundary {
		if i > 0 {
			points.WriteString(" ")
		}
		points.WriteString(fmt.Sprintf("%.0f,%.0f", point.X, point.Y))
	}
	
	// Choose color based on room type
	fillColor := "#E8F4FD"
	if room.Type == "bathroom" {
		fillColor = "#E3F2FD"
	} else if room.Type == "kitchen" {
		fillColor = "#FFF3E0"
	} else if strings.Contains(room.Type, "office") {
		fillColor = "#F3E5F5"
	}
	
	svg := fmt.Sprintf(
		`<polygon points="%s" fill="%s" stroke="#999" stroke-width="1" fill-opacity="0.3" class="room" data-id="%s" data-type="%s"/>`,
		points.String(), fillColor, room.ID, room.Type,
	)
	
	// Add room label at centroid
	if room.Name != "" {
		centroid := f.calculatePolygonCentroid(room.Boundary)
		svg += fmt.Sprintf(
			`<text x="%.0f" y="%.0f" text-anchor="middle" font-family="Arial" font-size="12" fill="#666" class="room-label">%s</text>`,
			centroid.X, centroid.Y, room.Name,
		)
	}
	
	return svg
}

// renderDoorToSVG renders a door with swing arc
func (f *Floor) renderDoorToSVG(door *Door) string {
	// Door line (opening in wall)
	doorSVG := fmt.Sprintf(
		`<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="#FFF" stroke-width="%.1f" class="door-opening" data-id="%s"/>`,
		door.Position.X, door.Position.Y,
		door.Position.X+door.Width*math.Cos(door.Angle),
		door.Position.Y+door.Width*math.Sin(door.Angle),
		door.Width, door.ID,
	)
	
	// Door swing arc (quarter circle)
	if door.SwingDirection != 0 {
		arcSVG := f.renderDoorArc(door)
		doorSVG += arcSVG
	}
	
	return doorSVG
}

// renderDoorArc renders the swing arc for a door
func (f *Floor) renderDoorArc(door *Door) string {
	// Calculate arc endpoints
	startAngle := door.Angle
	endAngle := door.Angle + door.SwingDirection*90*math.Pi/180
	
	startX := door.Position.X + door.Width*math.Cos(startAngle)
	startY := door.Position.Y + door.Width*math.Sin(startAngle)
	endX := door.Position.X + door.Width*math.Cos(endAngle)
	endY := door.Position.Y + door.Width*math.Sin(endAngle)
	
	// SVG arc path
	sweepFlag := 0
	if door.SwingDirection > 0 {
		sweepFlag = 1
	}
	
	return fmt.Sprintf(
		`<path d="M %.1f,%.1f A %.1f,%.1f 0 0,%d %.1f,%.1f" stroke="#999" stroke-width="1" fill="none" stroke-dasharray="2,2" class="door-arc"/>`,
		startX, startY, door.Width, door.Width, sweepFlag, endX, endY,
	)
}

// renderMEPToSVG renders MEP (Mechanical, Electrical, Plumbing) systems
func (f *Floor) renderMEPToSVG(mep *MEPSystem) string {
	var svg strings.Builder
	
	switch mep.Type {
	case "hvac":
		// HVAC ducts as rectangles
		svg.WriteString(fmt.Sprintf(
			`<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" fill="none" stroke="#0066CC" stroke-width="2" stroke-dasharray="5,5" class="hvac-duct" data-id="%s"/>`,
			mep.Position.X-mep.Size/2, mep.Position.Y-mep.Size/2, mep.Size, mep.Size/4, mep.ID,
		))
		
	case "electrical":
		// Electrical conduits as thin lines
		for _, point := range mep.Path {
			svg.WriteString(fmt.Sprintf(
				`<circle cx="%.1f" cy="%.1f" r="3" fill="#FF6600" stroke="#CC3300" stroke-width="1" class="electrical-outlet" data-id="%s"/>`,
				point.X, point.Y, mep.ID,
			))
		}
		
	case "plumbing":
		// Plumbing as thicker lines
		if len(mep.Path) > 1 {
			for i := 0; i < len(mep.Path)-1; i++ {
				svg.WriteString(fmt.Sprintf(
					`<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="#0099CC" stroke-width="4" class="plumbing-pipe" data-id="%s"/>`,
					mep.Path[i].X, mep.Path[i].Y, mep.Path[i+1].X, mep.Path[i+1].Y, mep.ID,
				))
			}
		}
		
	case "fire":
		// Fire suppression as circles with cross
		svg.WriteString(fmt.Sprintf(
			`<circle cx="%.1f" cy="%.1f" r="8" fill="#FF0000" stroke="#CC0000" stroke-width="2" class="fire-suppression" data-id="%s"/>`,
			mep.Position.X, mep.Position.Y, mep.ID,
		))
		svg.WriteString(fmt.Sprintf(
			`<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="white" stroke-width="2"/>`,
			mep.Position.X-5, mep.Position.Y, mep.Position.X+5, mep.Position.Y,
		))
		svg.WriteString(fmt.Sprintf(
			`<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="white" stroke-width="2"/>`,
			mep.Position.X, mep.Position.Y-5, mep.Position.X, mep.Position.Y+5,
		))
	}
	
	return svg.String()
}

// calculatePolygonCentroid calculates the centroid of a polygon
func (f *Floor) calculatePolygonCentroid(points []Point3D) Point3D {
	if len(points) == 0 {
		return Point3D{}
	}
	
	var sumX, sumY, sumZ float64
	for _, point := range points {
		sumX += point.X
		sumY += point.Y
		sumZ += point.Z
	}
	
	count := float64(len(points))
	return Point3D{
		X: sumX / count,
		Y: sumY / count,
		Z: sumZ / count,
	}
}

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