package ingestion

import (
	"fmt"
	"math"
	"sync"
	"time"

	"github.com/arxos/arxos-core"
)

// LiDARCapture handles real-time LiDAR field capture
// For when nothing exists - create from scratch on-site
type LiDARCapture struct {
	bridge     *IngestionBridge
	arxRepo    *arxoscore.ArxObjectRepository
	session    *CaptureSession
	mu         sync.Mutex
}

// CaptureSession represents an active LiDAR capture session
type CaptureSession struct {
	ID          string
	BuildingID  string
	StartTime   time.Time
	State       CaptureState
	CurrentRoom string
	Points      []LiDARPoint
	Walls       []*WallSegment
	Objects     []*CapturedObject
	ARAnchors   []ARAnchor
	Progress    float64
	mu          sync.RWMutex
}

// CaptureState represents the current state of capture
type CaptureState string

const (
	StateIdle        CaptureState = "idle"
	StateScanning    CaptureState = "scanning"
	StateProcessing  CaptureState = "processing"
	StateReview      CaptureState = "review"
	StateComplete    CaptureState = "complete"
)

// LiDARPoint represents a single LiDAR measurement
type LiDARPoint struct {
	X         float64
	Y         float64
	Z         float64
	Intensity float64
	Timestamp time.Time
	Color     RGB
}

// RGB represents color information
type RGB struct {
	R, G, B uint8
}

// WallSegment represents a detected wall
type WallSegment struct {
	Start      Point3D
	End        Point3D
	Height     float64
	Thickness  float64
	Material   string
	Confidence float64
}

// Point3D represents a 3D point
type Point3D struct {
	X, Y, Z float64
}

// CapturedObject represents an object captured during scanning
type CapturedObject struct {
	ID          string
	Type        string
	Position    Point3D
	Rotation    float64
	Symbol      string
	Timestamp   time.Time
	Confidence  float64
	Properties  map[string]interface{}
	ARAnnotation string
}

// ARAnchor represents an AR anchor point for alignment
type ARAnchor struct {
	ID       string
	Position Point3D
	Type     string // corner, door, reference
	Image    []byte // Reference image for visual tracking
}

// NewLiDARCapture creates a new LiDAR capture handler
func NewLiDARCapture(arxRepo *arxoscore.ArxObjectRepository) (*LiDARCapture, error) {
	bridge, err := NewIngestionBridge(arxRepo)
	if err != nil {
		return nil, err
	}

	return &LiDARCapture{
		bridge:  bridge,
		arxRepo: arxRepo,
	}, nil
}

// StartSession starts a new LiDAR capture session
func (l *LiDARCapture) StartSession(buildingID string, metadata map[string]interface{}) (*CaptureSession, error) {
	l.mu.Lock()
	defer l.mu.Unlock()

	session := &CaptureSession{
		ID:         fmt.Sprintf("lidar_session_%d", time.Now().Unix()),
		BuildingID: buildingID,
		StartTime:  time.Now(),
		State:      StateIdle,
		Points:     make([]LiDARPoint, 0, 100000), // Pre-allocate for performance
		Walls:      make([]*WallSegment, 0),
		Objects:    make([]*CapturedObject, 0),
		ARAnchors:  make([]ARAnchor, 0),
		Progress:   0.0,
	}

	l.session = session
	
	// Initialize AR anchors for alignment
	l.initializeARAnchors(session)
	
	return session, nil
}

// initializeARAnchors sets up AR reference points
func (l *LiDARCapture) initializeARAnchors(session *CaptureSession) {
	// Create default anchor points
	session.ARAnchors = append(session.ARAnchors, ARAnchor{
		ID:   "origin",
		Type: "reference",
		Position: Point3D{X: 0, Y: 0, Z: 0},
	})
}

// StartRoomCapture begins capturing a specific room
func (l *LiDARCapture) StartRoomCapture(sessionID string, roomName string) error {
	if l.session == nil || l.session.ID != sessionID {
		return fmt.Errorf("invalid session")
	}

	l.session.mu.Lock()
	defer l.session.mu.Unlock()

	l.session.CurrentRoom = roomName
	l.session.State = StateScanning
	
	fmt.Printf("Starting capture for room: %s\n", roomName)
	
	return nil
}

// ProcessLiDARFrame processes a single LiDAR frame
func (l *LiDARCapture) ProcessLiDARFrame(frame *LiDARFrame) error {
	if l.session == nil || l.session.State != StateScanning {
		return fmt.Errorf("no active scanning session")
	}

	l.session.mu.Lock()
	defer l.session.mu.Unlock()

	// Add points to point cloud
	for _, point := range frame.Points {
		l.session.Points = append(l.session.Points, point)
	}

	// Real-time wall detection
	newWalls := l.detectWallsFromPoints(frame.Points)
	l.mergeWalls(newWalls)

	// Real-time object detection
	objects := l.detectObjectsInFrame(frame)
	l.session.Objects = append(l.session.Objects, objects...)

	// Update progress
	l.updateCaptureProgress()

	// Provide real-time feedback
	l.provideARFeedback(frame)

	return nil
}

// LiDARFrame represents a single frame of LiDAR data
type LiDARFrame struct {
	Timestamp    time.Time
	Points       []LiDARPoint
	CameraImage  []byte
	DevicePose   DevicePose
	FrameNumber  int
}

// DevicePose represents device position and orientation
type DevicePose struct {
	Position    Point3D
	Rotation    Quaternion
	Confidence  float64
}

// Quaternion represents rotation
type Quaternion struct {
	X, Y, Z, W float64
}

// detectWallsFromPoints detects walls in point cloud
func (l *LiDARCapture) detectWallsFromPoints(points []LiDARPoint) []*WallSegment {
	var walls []*WallSegment

	// Use RANSAC algorithm for plane detection
	planes := l.detectPlanes(points)
	
	for _, plane := range planes {
		if l.isVerticalPlane(plane) {
			wall := l.planeToWall(plane)
			walls = append(walls, wall)
		}
	}

	return walls
}

// Plane represents a detected plane
type Plane struct {
	Normal   Point3D
	Distance float64
	Points   []LiDARPoint
	Inliers  int
}

// detectPlanes uses RANSAC to detect planes
func (l *LiDARCapture) detectPlanes(points []LiDARPoint) []Plane {
	var planes []Plane
	
	// Simplified RANSAC implementation
	minInliers := 100
	threshold := 0.05 // 5cm threshold
	
	remaining := make([]LiDARPoint, len(points))
	copy(remaining, points)
	
	for len(remaining) > minInliers {
		plane := l.ransacPlane(remaining, minInliers, threshold)
		if plane.Inliers >= minInliers {
			planes = append(planes, plane)
			// Remove inliers from remaining points
			remaining = l.removeInliers(remaining, plane)
		} else {
			break
		}
	}
	
	return planes
}

// ransacPlane performs RANSAC plane fitting
func (l *LiDARCapture) ransacPlane(points []LiDARPoint, minInliers int, threshold float64) Plane {
	// Simplified RANSAC - would be more robust in production
	bestPlane := Plane{}
	maxInliers := 0
	
	iterations := 100
	for i := 0; i < iterations; i++ {
		// Select 3 random points
		if len(points) < 3 {
			break
		}
		
		// Calculate plane from 3 points
		plane := l.planeFrom3Points(points[i%len(points)], 
			points[(i+1)%len(points)], 
			points[(i+2)%len(points)])
		
		// Count inliers
		inliers := 0
		for _, p := range points {
			if l.pointToPlaneDistance(p, plane) < threshold {
				inliers++
			}
		}
		
		if inliers > maxInliers {
			maxInliers = inliers
			bestPlane = plane
			bestPlane.Inliers = inliers
		}
	}
	
	return bestPlane
}

// planeFrom3Points calculates plane from 3 points
func (l *LiDARCapture) planeFrom3Points(p1, p2, p3 LiDARPoint) Plane {
	// Calculate normal vector
	v1 := Point3D{X: p2.X - p1.X, Y: p2.Y - p1.Y, Z: p2.Z - p1.Z}
	v2 := Point3D{X: p3.X - p1.X, Y: p3.Y - p1.Y, Z: p3.Z - p1.Z}
	
	// Cross product for normal
	normal := Point3D{
		X: v1.Y*v2.Z - v1.Z*v2.Y,
		Y: v1.Z*v2.X - v1.X*v2.Z,
		Z: v1.X*v2.Y - v1.Y*v2.X,
	}
	
	// Normalize
	length := math.Sqrt(normal.X*normal.X + normal.Y*normal.Y + normal.Z*normal.Z)
	if length > 0 {
		normal.X /= length
		normal.Y /= length
		normal.Z /= length
	}
	
	// Calculate distance
	distance := normal.X*p1.X + normal.Y*p1.Y + normal.Z*p1.Z
	
	return Plane{
		Normal:   normal,
		Distance: distance,
	}
}

// pointToPlaneDistance calculates distance from point to plane
func (l *LiDARCapture) pointToPlaneDistance(point LiDARPoint, plane Plane) float64 {
	return math.Abs(plane.Normal.X*point.X + 
		plane.Normal.Y*point.Y + 
		plane.Normal.Z*point.Z - 
		plane.Distance)
}

// removeInliers removes plane inliers from points
func (l *LiDARCapture) removeInliers(points []LiDARPoint, plane Plane) []LiDARPoint {
	var remaining []LiDARPoint
	threshold := 0.05
	
	for _, p := range points {
		if l.pointToPlaneDistance(p, plane) >= threshold {
			remaining = append(remaining, p)
		}
	}
	
	return remaining
}

// isVerticalPlane checks if plane is vertical (wall)
func (l *LiDARCapture) isVerticalPlane(plane Plane) bool {
	// Check if normal is mostly horizontal (perpendicular to gravity)
	return math.Abs(plane.Normal.Z) < 0.3 // Z is up
}

// planeToWall converts a plane to a wall segment
func (l *LiDARCapture) planeToWall(plane Plane) *WallSegment {
	// Find extents of the plane
	minX, maxX := math.MaxFloat64, -math.MaxFloat64
	minY, maxY := math.MaxFloat64, -math.MaxFloat64
	minZ, maxZ := math.MaxFloat64, -math.MaxFloat64
	
	for _, p := range plane.Points {
		minX = math.Min(minX, p.X)
		maxX = math.Max(maxX, p.X)
		minY = math.Min(minY, p.Y)
		maxY = math.Max(maxY, p.Y)
		minZ = math.Min(minZ, p.Z)
		maxZ = math.Max(maxZ, p.Z)
	}
	
	// Determine wall orientation and endpoints
	var start, end Point3D
	if math.Abs(plane.Normal.X) > math.Abs(plane.Normal.Y) {
		// Wall runs in Y direction
		start = Point3D{X: (minX + maxX) / 2, Y: minY, Z: minZ}
		end = Point3D{X: (minX + maxX) / 2, Y: maxY, Z: minZ}
	} else {
		// Wall runs in X direction
		start = Point3D{X: minX, Y: (minY + maxY) / 2, Z: minZ}
		end = Point3D{X: maxX, Y: (minY + maxY) / 2, Z: minZ}
	}
	
	return &WallSegment{
		Start:      start,
		End:        end,
		Height:     maxZ - minZ,
		Thickness:  0.15, // Default 15cm
		Material:   "unknown",
		Confidence: float64(plane.Inliers) / 1000.0, // Normalize confidence
	}
}

// mergeWalls merges new walls with existing ones
func (l *LiDARCapture) mergeWalls(newWalls []*WallSegment) {
	for _, newWall := range newWalls {
		merged := false
		
		// Check if wall can be merged with existing
		for _, existing := range l.session.Walls {
			if l.canMergeWalls(existing, newWall) {
				l.mergeWallSegments(existing, newWall)
				merged = true
				break
			}
		}
		
		if !merged {
			l.session.Walls = append(l.session.Walls, newWall)
		}
	}
}

// canMergeWalls checks if two walls can be merged
func (l *LiDARCapture) canMergeWalls(w1, w2 *WallSegment) bool {
	// Check if walls are collinear and close
	threshold := 0.2 // 20cm threshold
	
	// Check if endpoints are close
	dist1 := l.distance3D(w1.End, w2.Start)
	dist2 := l.distance3D(w1.Start, w2.End)
	
	return dist1 < threshold || dist2 < threshold
}

// distance3D calculates 3D distance
func (l *LiDARCapture) distance3D(p1, p2 Point3D) float64 {
	dx := p1.X - p2.X
	dy := p1.Y - p2.Y
	dz := p1.Z - p2.Z
	return math.Sqrt(dx*dx + dy*dy + dz*dz)
}

// mergeWallSegments merges two wall segments
func (l *LiDARCapture) mergeWallSegments(existing, newWall *WallSegment) {
	// Extend existing wall to include new segment
	if l.distance3D(existing.End, newWall.Start) < l.distance3D(existing.Start, newWall.End) {
		existing.End = newWall.End
	} else {
		existing.Start = newWall.Start
	}
	
	// Update confidence
	existing.Confidence = (existing.Confidence + newWall.Confidence) / 2
}

// detectObjectsInFrame detects objects in a LiDAR frame
func (l *LiDARCapture) detectObjectsInFrame(frame *LiDARFrame) []*CapturedObject {
	var objects []*CapturedObject
	
	// Cluster points that don't belong to walls
	clusters := l.clusterPoints(frame.Points)
	
	for _, cluster := range clusters {
		obj := l.classifyCluster(cluster)
		if obj != nil {
			obj.Timestamp = frame.Timestamp
			objects = append(objects, obj)
		}
	}
	
	return objects
}

// PointCluster represents a cluster of points
type PointCluster struct {
	Points   []LiDARPoint
	Centroid Point3D
	BoundingBox BoundingBox
}

// BoundingBox represents a 3D bounding box
type BoundingBox struct {
	Min, Max Point3D
}

// clusterPoints clusters nearby points
func (l *LiDARCapture) clusterPoints(points []LiDARPoint) []PointCluster {
	var clusters []PointCluster
	
	// Simple distance-based clustering
	threshold := 0.1 // 10cm
	visited := make([]bool, len(points))
	
	for i, point := range points {
		if visited[i] {
			continue
		}
		
		cluster := PointCluster{
			Points: []LiDARPoint{point},
		}
		visited[i] = true
		
		// Find nearby points
		for j, other := range points {
			if visited[j] {
				continue
			}
			
			if l.pointDistance(point, other) < threshold {
				cluster.Points = append(cluster.Points, other)
				visited[j] = true
			}
		}
		
		if len(cluster.Points) > 10 { // Minimum cluster size
			l.calculateClusterProperties(&cluster)
			clusters = append(clusters, cluster)
		}
	}
	
	return clusters
}

// pointDistance calculates distance between LiDAR points
func (l *LiDARCapture) pointDistance(p1, p2 LiDARPoint) float64 {
	dx := p1.X - p2.X
	dy := p1.Y - p2.Y
	dz := p1.Z - p2.Z
	return math.Sqrt(dx*dx + dy*dy + dz*dz)
}

// calculateClusterProperties calculates cluster centroid and bounding box
func (l *LiDARCapture) calculateClusterProperties(cluster *PointCluster) {
	if len(cluster.Points) == 0 {
		return
	}
	
	minX, maxX := cluster.Points[0].X, cluster.Points[0].X
	minY, maxY := cluster.Points[0].Y, cluster.Points[0].Y
	minZ, maxZ := cluster.Points[0].Z, cluster.Points[0].Z
	sumX, sumY, sumZ := 0.0, 0.0, 0.0
	
	for _, p := range cluster.Points {
		sumX += p.X
		sumY += p.Y
		sumZ += p.Z
		
		minX = math.Min(minX, p.X)
		maxX = math.Max(maxX, p.X)
		minY = math.Min(minY, p.Y)
		maxY = math.Max(maxY, p.Y)
		minZ = math.Min(minZ, p.Z)
		maxZ = math.Max(maxZ, p.Z)
	}
	
	n := float64(len(cluster.Points))
	cluster.Centroid = Point3D{
		X: sumX / n,
		Y: sumY / n,
		Z: sumZ / n,
	}
	
	cluster.BoundingBox = BoundingBox{
		Min: Point3D{X: minX, Y: minY, Z: minZ},
		Max: Point3D{X: maxX, Y: maxY, Z: maxZ},
	}
}

// classifyCluster classifies a point cluster as an object
func (l *LiDARCapture) classifyCluster(cluster PointCluster) *CapturedObject {
	// Calculate cluster dimensions
	width := cluster.BoundingBox.Max.X - cluster.BoundingBox.Min.X
	height := cluster.BoundingBox.Max.Z - cluster.BoundingBox.Min.Z
	depth := cluster.BoundingBox.Max.Y - cluster.BoundingBox.Min.Y
	
	// Classify based on dimensions and position
	var objType, symbol string
	confidence := 0.7
	
	// Electrical outlet (small, on wall at ~1m height)
	if width < 0.15 && height < 0.15 && cluster.Centroid.Z > 0.8 && cluster.Centroid.Z < 1.2 {
		objType = "electrical_outlet"
		symbol = "outlet"
		confidence = 0.8
	} else if height > 1.5 && width < 0.5 && depth < 0.5 {
		// Column or pillar
		objType = "column"
		symbol = "column"
		confidence = 0.75
	} else if cluster.Centroid.Z > 2.0 && width < 1.0 {
		// Ceiling fixture
		objType = "light_fixture"
		symbol = "light"
		confidence = 0.7
	} else {
		// Generic object
		objType = "unknown"
		symbol = "object"
		confidence = 0.5
	}
	
	return &CapturedObject{
		ID:       fmt.Sprintf("obj_%d", time.Now().UnixNano()),
		Type:     objType,
		Position: cluster.Centroid,
		Symbol:   symbol,
		Confidence: confidence,
		Properties: map[string]interface{}{
			"width":  width,
			"height": height,
			"depth":  depth,
			"points": len(cluster.Points),
		},
	}
}

// updateCaptureProgress updates the capture progress
func (l *LiDARCapture) updateCaptureProgress() {
	// Calculate progress based on coverage
	totalPoints := len(l.session.Points)
	wallLength := 0.0
	for _, wall := range l.session.Walls {
		wallLength += l.distance3D(wall.Start, wall.End)
	}
	
	// Rough progress estimate
	l.session.Progress = math.Min(100.0, float64(totalPoints)/10000.0 + wallLength/100.0)
}

// provideARFeedback provides AR overlay feedback
func (l *LiDARCapture) provideARFeedback(frame *LiDARFrame) {
	// This would send AR overlay data to the device
	// Showing:
	// - Detected walls in green
	// - Unscanned areas in red
	// - Recognized objects with labels
	// - Progress indicator
}

// MarkObject manually marks an object location
func (l *LiDARCapture) MarkObject(sessionID string, objType string, position Point3D) error {
	if l.session == nil || l.session.ID != sessionID {
		return fmt.Errorf("invalid session")
	}

	l.session.mu.Lock()
	defer l.session.mu.Unlock()

	// Create captured object from manual marking
	obj := &CapturedObject{
		ID:         fmt.Sprintf("marked_%d", time.Now().UnixNano()),
		Type:       objType,
		Position:   position,
		Symbol:     l.getSymbolForType(objType),
		Timestamp:  time.Now(),
		Confidence: 1.0, // Manual marking has high confidence
		Properties: map[string]interface{}{
			"source": "manual",
			"room":   l.session.CurrentRoom,
		},
		ARAnnotation: fmt.Sprintf("%s marked", objType),
	}

	l.session.Objects = append(l.session.Objects, obj)
	
	fmt.Printf("Marked %s at position (%.2f, %.2f, %.2f)\n", 
		objType, position.X, position.Y, position.Z)
	
	return nil
}

// getSymbolForType returns appropriate symbol for object type
func (l *LiDARCapture) getSymbolForType(objType string) string {
	symbolMap := map[string]string{
		"outlet":          "electrical_outlet",
		"switch":          "light_switch",
		"light":           "light_fixture",
		"thermostat":      "thermostat",
		"sprinkler":       "sprinkler",
		"smoke_detector":  "smoke_detector",
		"access_point":    "wifi_ap",
		"camera":          "security_camera",
		"hvac_vent":       "hvac_diffuser",
		"fire_extinguisher": "fire_extinguisher",
	}
	
	if symbol, exists := symbolMap[objType]; exists {
		return symbol
	}
	return "generic_component"
}

// CompleteSession completes the capture session and creates ArxObjects
func (l *LiDARCapture) CompleteSession(sessionID string) ([]*arxoscore.ArxObject, error) {
	if l.session == nil || l.session.ID != sessionID {
		return nil, fmt.Errorf("invalid session")
	}

	l.session.mu.Lock()
	l.session.State = StateProcessing
	l.session.mu.Unlock()

	// Convert captured data to ArxObjects
	var recognizedSymbols []*RecognizedSymbol

	// Convert walls to symbols
	for _, wall := range l.session.Walls {
		symbol := l.wallToSymbol(wall)
		recognizedSymbols = append(recognizedSymbols, symbol)
	}

	// Convert captured objects to symbols
	for _, obj := range l.session.Objects {
		symbol := l.capturedObjectToSymbol(obj)
		recognizedSymbols = append(recognizedSymbols, symbol)
	}

	// Process through bridge
	arxObjects, err := l.bridge.ProcessRecognizedSymbols(recognizedSymbols, l.session.BuildingID)
	if err != nil {
		return nil, fmt.Errorf("failed to process captured symbols: %w", err)
	}

	// Store in repository
	for _, obj := range arxObjects {
		obj.Source = "lidar"
		obj.Properties["capture_session"] = sessionID
		obj.Properties["capture_time"] = l.session.StartTime
		
		if err := l.arxRepo.Create(obj); err != nil {
			return nil, fmt.Errorf("failed to store ArxObject %s: %w", obj.ID, err)
		}
	}

	l.session.mu.Lock()
	l.session.State = StateComplete
	l.session.mu.Unlock()

	fmt.Printf("LiDAR capture complete: %d objects created\n", len(arxObjects))
	
	return arxObjects, nil
}

// wallToSymbol converts a wall segment to a recognized symbol
func (l *LiDARCapture) wallToSymbol(wall *WallSegment) *RecognizedSymbol {
	return &RecognizedSymbol{
		Definition: &SymbolDefinition{
			ID:       fmt.Sprintf("wall_%d", time.Now().UnixNano()),
			Name:     "Wall",
			System:   "structural",
			Category: "structural",
			Tags:     []string{"wall", "structural", "lidar"},
		},
		Position: Position{
			X: (wall.Start.X + wall.End.X) / 2,
			Y: (wall.Start.Y + wall.End.Y) / 2,
			Z: (wall.Start.Z + wall.End.Z) / 2,
		},
		Context:    "lidar_capture",
		Confidence: wall.Confidence,
	}
}

// capturedObjectToSymbol converts a captured object to a recognized symbol
func (l *LiDARCapture) capturedObjectToSymbol(obj *CapturedObject) *RecognizedSymbol {
	return &RecognizedSymbol{
		Definition: &SymbolDefinition{
			ID:       obj.ID,
			Name:     obj.Type,
			System:   l.getSystemForType(obj.Type),
			Category: l.getCategoryForType(obj.Type),
			Tags:     []string{obj.Type, "lidar", obj.Symbol},
		},
		Position: Position{
			X: obj.Position.X,
			Y: obj.Position.Y,
			Z: obj.Position.Z,
		},
		Context:     "lidar_capture",
		Confidence:  obj.Confidence,
		ParentSpace: obj.Properties["room"].(string),
	}
}

// getSystemForType returns the system for an object type
func (l *LiDARCapture) getSystemForType(objType string) string {
	systemMap := map[string]string{
		"electrical_outlet": "electrical",
		"light_fixture":     "electrical",
		"switch":            "electrical",
		"thermostat":        "mechanical",
		"hvac_vent":         "mechanical",
		"sprinkler":         "fire_protection",
		"smoke_detector":    "fire_protection",
		"column":            "structural",
		"wall":              "structural",
	}
	
	if system, exists := systemMap[objType]; exists {
		return system
	}
	return "unknown"
}

// getCategoryForType returns the category for an object type
func (l *LiDARCapture) getCategoryForType(objType string) string {
	categoryMap := map[string]string{
		"electrical_outlet": "electrical",
		"light_fixture":     "lighting",
		"switch":            "controls",
		"thermostat":        "controls",
		"hvac_vent":         "hvac",
		"sprinkler":         "fire_suppression",
		"smoke_detector":    "fire_detection",
		"column":            "structural",
		"wall":              "structural",
	}
	
	if category, exists := categoryMap[objType]; exists {
		return category
	}
	return "component"
}

// GetSessionStatus returns the current session status
func (l *LiDARCapture) GetSessionStatus(sessionID string) (map[string]interface{}, error) {
	if l.session == nil || l.session.ID != sessionID {
		return nil, fmt.Errorf("invalid session")
	}

	l.session.mu.RLock()
	defer l.session.mu.RUnlock()

	return map[string]interface{}{
		"id":           l.session.ID,
		"state":        l.session.State,
		"current_room": l.session.CurrentRoom,
		"progress":     l.session.Progress,
		"points":       len(l.session.Points),
		"walls":        len(l.session.Walls),
		"objects":      len(l.session.Objects),
		"duration":     time.Since(l.session.StartTime).Seconds(),
	}, nil
}