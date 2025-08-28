// Package pipeline - 3D reconstruction stage for Progressive Construction Pipeline
package pipeline

import (
	"context"
	"fmt"
	"math"
	"os"
	"path/filepath"
	"strings"

	"github.com/arxos/arxos/core/internal/arxobject"
)

// ReconstructionStage handles 3D mesh generation from ArxObjects
type ReconstructionStage struct {
	// Mesh generation parameters
	wallHeight        float64 // mm - default wall height
	floorThickness    float64 // mm - floor slab thickness
	ceilingHeight     float64 // mm - ceiling height above floor
	
	// Quality settings
	meshResolution    float64 // mm - mesh vertex spacing
	smoothingPasses   int     // number of smoothing iterations
	
	// Output formats
	outputFormats     []string // supported formats: "obj", "ply", "gltf"
}

// Mesh3D represents a 3D mesh
type Mesh3D struct {
	Vertices  [][3]float64      `json:"vertices"`
	Faces     [][3]int          `json:"faces"`      // Triangle indices
	Normals   [][3]float64      `json:"normals"`    // Vertex normals
	UVs       [][2]float64      `json:"uvs"`        // Texture coordinates
	Materials []Material        `json:"materials"`
	Metadata  MeshMetadata      `json:"metadata"`
}

// Material represents a mesh material
type Material struct {
	Name         string    `json:"name"`
	DiffuseColor [3]float64 `json:"diffuse_color"` // RGB 0-1
	Roughness    float64   `json:"roughness"`
	Metallic     float64   `json:"metallic"`
	Transparency float64   `json:"transparency"`
}

// MeshMetadata contains mesh generation metadata
type MeshMetadata struct {
	GeneratedFrom    []string  `json:"generated_from"`    // Object IDs used
	VertexCount      int       `json:"vertex_count"`
	FaceCount        int       `json:"face_count"`
	BoundingBox      BoundingBox `json:"bounding_box"`
	GenerationTime   float64   `json:"generation_time_seconds"`
	QualityMetrics   QualityMetrics `json:"quality_metrics"`
}

// BoundingBox represents mesh bounds
type BoundingBox struct {
	Min [3]float64 `json:"min"`
	Max [3]float64 `json:"max"`
}

// QualityMetrics represents mesh quality assessment
type QualityMetrics struct {
	WatertightMesh    bool    `json:"watertight_mesh"`
	ManifoldEdges     bool    `json:"manifold_edges"`
	AverageEdgeLength float64 `json:"average_edge_length"`
	AspectRatio       float64 `json:"aspect_ratio"`
	SurfaceArea       float64 `json:"surface_area_sqmm"`
	Volume            float64 `json:"volume_mm3"`
}

// ReconstructionResult contains 3D reconstruction results
type ReconstructionResult struct {
	MeshFile        string         `json:"mesh_file"`
	Mesh            *Mesh3D        `json:"mesh,omitempty"`
	GeneratedAssets []GeneratedAsset `json:"generated_assets"`
	ProcessingStats ReconstructionStats `json:"processing_stats"`
}

// GeneratedAsset represents a generated file asset
type GeneratedAsset struct {
	Type        string `json:"type"`        // "mesh", "texture", "preview"
	Format      string `json:"format"`      // File format
	FilePath    string `json:"file_path"`
	FileSize    int64  `json:"file_size"`
	Description string `json:"description"`
}

// ReconstructionStats contains processing statistics
type ReconstructionStats struct {
	InputObjects      int     `json:"input_objects"`
	ProcessedWalls    int     `json:"processed_walls"`
	ProcessedRooms    int     `json:"processed_rooms"`
	ProcessedOpenings int     `json:"processed_openings"`
	MeshQuality       float64 `json:"mesh_quality"` // 0-1
	ProcessingTime    float64 `json:"processing_time_seconds"`
}

// NewReconstructionStage creates a new 3D reconstruction stage
func NewReconstructionStage() *ReconstructionStage {
	return &ReconstructionStage{
		wallHeight:      2700.0, // 2.7m standard ceiling
		floorThickness:  150.0,  // 150mm floor slab
		ceilingHeight:   2700.0, // Same as wall height
		meshResolution:  50.0,   // 50mm mesh resolution
		smoothingPasses: 2,      // 2 smoothing passes
		outputFormats:   []string{"obj", "gltf"}, // OBJ and glTF output
	}
}

// Process generates 3D mesh from ArxObjects
func (rs *ReconstructionStage) Process(ctx context.Context, objects []*arxobject.ArxObjectUnified, outputDir string) (string, error) {
	// Step 1: Analyze objects and plan reconstruction
	reconstructionPlan, err := rs.planReconstruction(objects)
	if err != nil {
		return "", fmt.Errorf("failed to plan reconstruction: %w", err)
	}
	
	// Step 2: Generate 3D mesh
	mesh, err := rs.generateMesh(reconstructionPlan)
	if err != nil {
		return "", fmt.Errorf("failed to generate mesh: %w", err)
	}
	
	// Step 3: Validate and optimize mesh
	if err := rs.validateMesh(mesh); err != nil {
		return "", fmt.Errorf("mesh validation failed: %w", err)
	}
	
	rs.optimizeMesh(mesh)
	
	// Step 4: Export mesh files
	meshFile, err := rs.exportMesh(mesh, outputDir)
	if err != nil {
		return "", fmt.Errorf("failed to export mesh: %w", err)
	}
	
	return meshFile, nil
}

// planReconstruction analyzes objects and creates reconstruction plan
func (rs *ReconstructionStage) planReconstruction(objects []*arxobject.ArxObjectUnified) (*ReconstructionPlan, error) {
	plan := &ReconstructionPlan{
		Walls:    []*arxobject.ArxObjectUnified{},
		Rooms:    []*arxobject.ArxObjectUnified{},
		Openings: []*arxobject.ArxObjectUnified{},
		Floors:   []*arxobject.ArxObjectUnified{},
		Metadata: make(map[string]interface{}),
	}
	
	// Categorize objects by type
	for _, obj := range objects {
		switch obj.Type {
		case arxobject.TypeWall:
			plan.Walls = append(plan.Walls, obj)
		case arxobject.TypeRoom:
			plan.Rooms = append(plan.Rooms, obj)
		case arxobject.TypeDoor, arxobject.TypeWindow:
			plan.Openings = append(plan.Openings, obj)
		case arxobject.TypeFloor:
			plan.Floors = append(plan.Floors, obj)
		}
	}
	
	// Analyze spatial relationships
	rs.analyzeSpacialRelationships(plan)
	
	return plan, nil
}

// ReconstructionPlan represents the plan for 3D reconstruction
type ReconstructionPlan struct {
	Walls     []*arxobject.ArxObjectUnified `json:"walls"`
	Rooms     []*arxobject.ArxObjectUnified `json:"rooms"`
	Openings  []*arxobject.ArxObjectUnified `json:"openings"`
	Floors    []*arxobject.ArxObjectUnified `json:"floors"`
	Metadata  map[string]interface{}        `json:"metadata"`
}

// analyzeSpacialRelationships analyzes how objects relate spatially
func (rs *ReconstructionStage) analyzeSpacialRelationships(plan *ReconstructionPlan) {
	// Calculate building bounds
	bounds := rs.calculateBounds(plan)
	plan.Metadata["building_bounds"] = bounds
	
	// Identify room-wall relationships
	roomWallMap := make(map[string][]string)
	for _, room := range plan.Rooms {
		roomWallMap[room.ID] = rs.findWallsForRoom(room, plan.Walls)
	}
	plan.Metadata["room_wall_map"] = roomWallMap
	
	// Identify wall-opening relationships
	wallOpeningMap := make(map[string][]string)
	for _, wall := range plan.Walls {
		wallOpeningMap[wall.ID] = rs.findOpeningsForWall(wall, plan.Openings)
	}
	plan.Metadata["wall_opening_map"] = wallOpeningMap
}

// calculateBounds calculates overall building bounds
func (rs *ReconstructionStage) calculateBounds(plan *ReconstructionPlan) BoundingBox {
	bounds := BoundingBox{
		Min: [3]float64{math.Inf(1), math.Inf(1), 0},
		Max: [3]float64{math.Inf(-1), math.Inf(-1), rs.wallHeight},
	}
	
	// Include all objects in bounds calculation
	allObjects := append([]*arxobject.ArxObjectUnified{}, plan.Walls...)
	allObjects = append(allObjects, plan.Rooms...)
	allObjects = append(allObjects, plan.Openings...)
	
	for _, obj := range allObjects {
		coords := obj.Geometry.Coordinates
		for i := 0; i < len(coords); i += 2 {
			if i+1 < len(coords) {
				x, y := coords[i], coords[i+1]
				
				bounds.Min[0] = math.Min(bounds.Min[0], x)
				bounds.Min[1] = math.Min(bounds.Min[1], y)
				bounds.Max[0] = math.Max(bounds.Max[0], x)
				bounds.Max[1] = math.Max(bounds.Max[1], y)
			}
		}
	}
	
	return bounds
}

// findWallsForRoom finds walls that belong to a room
func (rs *ReconstructionStage) findWallsForRoom(room *arxobject.ArxObjectUnified, walls []*arxobject.ArxObjectUnified) []string {
	var roomWalls []string
	
	roomBounds := rs.getObjectBounds(room)
	
	for _, wall := range walls {
		wallBounds := rs.getObjectBounds(wall)
		
		// Check if wall intersects with room boundary
		if rs.boundsIntersect(roomBounds, wallBounds) {
			roomWalls = append(roomWalls, wall.ID)
		}
	}
	
	return roomWalls
}

// findOpeningsForWall finds openings (doors/windows) in a wall
func (rs *ReconstructionStage) findOpeningsForWall(wall *arxobject.ArxObjectUnified, openings []*arxobject.ArxObjectUnified) []string {
	var wallOpenings []string
	
	wallBounds := rs.getObjectBounds(wall)
	
	for _, opening := range openings {
		openingBounds := rs.getObjectBounds(opening)
		
		// Check if opening is within wall bounds
		if rs.boundsContains(wallBounds, openingBounds) {
			wallOpenings = append(wallOpenings, opening.ID)
		}
	}
	
	return wallOpenings
}

// generateMesh generates 3D mesh from reconstruction plan
func (rs *ReconstructionStage) generateMesh(plan *ReconstructionPlan) (*Mesh3D, error) {
	mesh := &Mesh3D{
		Vertices:  [][3]float64{},
		Faces:     [][3]int{},
		Normals:   [][3]float64{},
		UVs:       [][2]float64{},
		Materials: rs.createDefaultMaterials(),
		Metadata: MeshMetadata{
			GeneratedFrom: rs.extractObjectIDs(plan),
		},
	}
	
	// Generate floor geometry
	rs.generateFloorMesh(plan, mesh)
	
	// Generate wall geometry
	rs.generateWallMesh(plan, mesh)
	
	// Generate ceiling geometry
	rs.generateCeilingMesh(plan, mesh)
	
	// Generate opening geometry (cut openings from walls)
	rs.generateOpeningMesh(plan, mesh)
	
	// Update metadata
	mesh.Metadata.VertexCount = len(mesh.Vertices)
	mesh.Metadata.FaceCount = len(mesh.Faces)
	mesh.Metadata.BoundingBox = rs.calculateMeshBounds(mesh)
	
	return mesh, nil
}

// generateFloorMesh generates floor geometry
func (rs *ReconstructionStage) generateFloorMesh(plan *ReconstructionPlan, mesh *Mesh3D) {
	bounds, ok := plan.Metadata["building_bounds"].(BoundingBox)
	if !ok {
		return
	}
	
	// Create floor vertices
	z := 0.0 // Floor at ground level
	floorVertices := [][3]float64{
		{bounds.Min[0], bounds.Min[1], z},
		{bounds.Max[0], bounds.Min[1], z},
		{bounds.Max[0], bounds.Max[1], z},
		{bounds.Min[0], bounds.Max[1], z},
	}
	
	startIdx := len(mesh.Vertices)
	mesh.Vertices = append(mesh.Vertices, floorVertices...)
	
	// Create floor faces (two triangles)
	floorFaces := [][3]int{
		{startIdx, startIdx + 1, startIdx + 2},
		{startIdx, startIdx + 2, startIdx + 3},
	}
	mesh.Faces = append(mesh.Faces, floorFaces...)
	
	// Add normals (pointing up)
	for range floorVertices {
		mesh.Normals = append(mesh.Normals, [3]float64{0, 0, 1})
	}
	
	// Add UVs
	floorUVs := [][2]float64{
		{0, 0}, {1, 0}, {1, 1}, {0, 1},
	}
	mesh.UVs = append(mesh.UVs, floorUVs...)
}

// generateWallMesh generates wall geometry
func (rs *ReconstructionStage) generateWallMesh(plan *ReconstructionPlan, mesh *Mesh3D) {
	for _, wall := range plan.Walls {
		rs.generateSingleWallMesh(wall, mesh)
	}
}

// generateSingleWallMesh generates mesh for a single wall
func (rs *ReconstructionStage) generateSingleWallMesh(wall *arxobject.ArxObjectUnified, mesh *Mesh3D) {
	coords := wall.Geometry.Coordinates
	if len(coords) < 4 {
		return // Need at least 2 points for a wall
	}
	
	// Create wall vertices (bottom and top)
	wallThickness := wall.Geometry.Width
	if wallThickness == 0 {
		wallThickness = 150.0 // Default thickness
	}
	
	x1, y1 := coords[0], coords[1]
	x2, y2 := coords[2], coords[3]
	
	// Calculate wall normal (perpendicular)
	dx, dy := x2-x1, y2-y1
	length := math.Sqrt(dx*dx + dy*dy)
	if length == 0 {
		return
	}
	
	nx, ny := -dy/length, dx/length // Normal vector
	halfThickness := wallThickness / 2
	
	// Wall vertices (8 total: 4 bottom, 4 top)
	wallVertices := [][3]float64{
		// Bottom vertices
		{x1 + nx*halfThickness, y1 + ny*halfThickness, 0},
		{x1 - nx*halfThickness, y1 - ny*halfThickness, 0},
		{x2 - nx*halfThickness, y2 - ny*halfThickness, 0},
		{x2 + nx*halfThickness, y2 + ny*halfThickness, 0},
		// Top vertices
		{x1 + nx*halfThickness, y1 + ny*halfThickness, rs.wallHeight},
		{x1 - nx*halfThickness, y1 - ny*halfThickness, rs.wallHeight},
		{x2 - nx*halfThickness, y2 - ny*halfThickness, rs.wallHeight},
		{x2 + nx*halfThickness, y2 + ny*halfThickness, rs.wallHeight},
	}
	
	startIdx := len(mesh.Vertices)
	mesh.Vertices = append(mesh.Vertices, wallVertices...)
	
	// Wall faces (6 faces for a box)
	wallFaces := [][3]int{
		// Bottom face
		{startIdx, startIdx + 2, startIdx + 1},
		{startIdx, startIdx + 3, startIdx + 2},
		// Top face  
		{startIdx + 4, startIdx + 5, startIdx + 6},
		{startIdx + 4, startIdx + 6, startIdx + 7},
		// Side faces
		{startIdx, startIdx + 1, startIdx + 5},
		{startIdx, startIdx + 5, startIdx + 4},
		{startIdx + 2, startIdx + 7, startIdx + 6},
		{startIdx + 3, startIdx + 7, startIdx + 2},
		// End faces
		{startIdx + 1, startIdx + 2, startIdx + 6},
		{startIdx + 1, startIdx + 6, startIdx + 5},
		{startIdx, startIdx + 4, startIdx + 7},
		{startIdx, startIdx + 7, startIdx + 3},
	}
	mesh.Faces = append(mesh.Faces, wallFaces...)
	
	// Add normals (simplified - should be calculated per face)
	for range wallVertices {
		mesh.Normals = append(mesh.Normals, [3]float64{nx, ny, 0})
	}
	
	// Add UVs (simplified)
	for range wallVertices {
		mesh.UVs = append(mesh.UVs, [2]float64{0.5, 0.5})
	}
}

// generateCeilingMesh generates ceiling geometry
func (rs *ReconstructionStage) generateCeilingMesh(plan *ReconstructionPlan, mesh *Mesh3D) {
	bounds, ok := plan.Metadata["building_bounds"].(BoundingBox)
	if !ok {
		return
	}
	
	// Create ceiling vertices
	z := rs.ceilingHeight
	ceilingVertices := [][3]float64{
		{bounds.Min[0], bounds.Min[1], z},
		{bounds.Max[0], bounds.Min[1], z},
		{bounds.Max[0], bounds.Max[1], z},
		{bounds.Min[0], bounds.Max[1], z},
	}
	
	startIdx := len(mesh.Vertices)
	mesh.Vertices = append(mesh.Vertices, ceilingVertices...)
	
	// Create ceiling faces (two triangles, facing down)
	ceilingFaces := [][3]int{
		{startIdx, startIdx + 2, startIdx + 1},
		{startIdx, startIdx + 3, startIdx + 2},
	}
	mesh.Faces = append(mesh.Faces, ceilingFaces...)
	
	// Add normals (pointing down)
	for range ceilingVertices {
		mesh.Normals = append(mesh.Normals, [3]float64{0, 0, -1})
	}
	
	// Add UVs
	ceilingUVs := [][2]float64{
		{0, 0}, {1, 0}, {1, 1}, {0, 1},
	}
	mesh.UVs = append(mesh.UVs, ceilingUVs...)
}

// generateOpeningMesh handles openings (doors/windows) by modifying wall geometry
func (rs *ReconstructionStage) generateOpeningMesh(plan *ReconstructionPlan, mesh *Mesh3D) {
	// For now, openings are handled as separate objects
	// In production, would subtract opening geometry from walls
	for _, opening := range plan.Openings {
		rs.generateSingleOpeningMesh(opening, mesh)
	}
}

// generateSingleOpeningMesh generates mesh for a door or window frame
func (rs *ReconstructionStage) generateSingleOpeningMesh(opening *arxobject.ArxObjectUnified, mesh *Mesh3D) {
	// Generate a simple frame for the opening
	// In production, would create detailed door/window geometry
	
	coords := opening.Geometry.Coordinates
	if len(coords) < 2 {
		return
	}
	
	x, y := coords[0], coords[1]
	width := opening.Geometry.Width
	height := opening.Geometry.Height
	
	if width == 0 || height == 0 {
		// Use default dimensions
		if opening.Type == arxobject.TypeDoor {
			width, height = 800, 2000 // 80cm x 2m
		} else {
			width, height = 1200, 1200 // 1.2m x 1.2m
		}
	}
	
	// Create simple frame vertices
	frameVertices := [][3]float64{
		{x, y, 0},
		{x + width, y, 0},
		{x + width, y, height},
		{x, y, height},
	}
	
	startIdx := len(mesh.Vertices)
	mesh.Vertices = append(mesh.Vertices, frameVertices...)
	
	// Add frame faces (just the outline)
	frameFaces := [][3]int{
		{startIdx, startIdx + 1, startIdx + 2},
		{startIdx, startIdx + 2, startIdx + 3},
	}
	mesh.Faces = append(mesh.Faces, frameFaces...)
	
	// Add normals
	for range frameVertices {
		mesh.Normals = append(mesh.Normals, [3]float64{0, 0, 1})
	}
	
	// Add UVs
	for range frameVertices {
		mesh.UVs = append(mesh.UVs, [2]float64{0.5, 0.5})
	}
}

// Helper functions

func (rs *ReconstructionStage) getObjectBounds(obj *arxobject.ArxObjectUnified) BoundingBox {
	coords := obj.Geometry.Coordinates
	bounds := BoundingBox{
		Min: [3]float64{math.Inf(1), math.Inf(1), 0},
		Max: [3]float64{math.Inf(-1), math.Inf(-1), rs.wallHeight},
	}
	
	for i := 0; i < len(coords); i += 2 {
		if i+1 < len(coords) {
			x, y := coords[i], coords[i+1]
			bounds.Min[0] = math.Min(bounds.Min[0], x)
			bounds.Min[1] = math.Min(bounds.Min[1], y)
			bounds.Max[0] = math.Max(bounds.Max[0], x)
			bounds.Max[1] = math.Max(bounds.Max[1], y)
		}
	}
	
	return bounds
}

func (rs *ReconstructionStage) boundsIntersect(a, b BoundingBox) bool {
	return a.Min[0] <= b.Max[0] && a.Max[0] >= b.Min[0] &&
	       a.Min[1] <= b.Max[1] && a.Max[1] >= b.Min[1]
}

func (rs *ReconstructionStage) boundsContains(container, contained BoundingBox) bool {
	return container.Min[0] <= contained.Min[0] && container.Max[0] >= contained.Max[0] &&
	       container.Min[1] <= contained.Min[1] && container.Max[1] >= contained.Max[1]
}

func (rs *ReconstructionStage) createDefaultMaterials() []Material {
	return []Material{
		{
			Name:         "wall",
			DiffuseColor: [3]float64{0.9, 0.9, 0.9}, // Light gray
			Roughness:    0.8,
			Metallic:     0.0,
			Transparency: 0.0,
		},
		{
			Name:         "floor",
			DiffuseColor: [3]float64{0.7, 0.6, 0.5}, // Brown
			Roughness:    0.6,
			Metallic:     0.0,
			Transparency: 0.0,
		},
		{
			Name:         "ceiling",
			DiffuseColor: [3]float64{1.0, 1.0, 1.0}, // White
			Roughness:    0.2,
			Metallic:     0.0,
			Transparency: 0.0,
		},
	}
}

func (rs *ReconstructionStage) extractObjectIDs(plan *ReconstructionPlan) []string {
	var ids []string
	
	for _, wall := range plan.Walls {
		ids = append(ids, wall.ID)
	}
	for _, room := range plan.Rooms {
		ids = append(ids, room.ID)
	}
	for _, opening := range plan.Openings {
		ids = append(ids, opening.ID)
	}
	
	return ids
}

func (rs *ReconstructionStage) calculateMeshBounds(mesh *Mesh3D) BoundingBox {
	if len(mesh.Vertices) == 0 {
		return BoundingBox{}
	}
	
	bounds := BoundingBox{
		Min: [3]float64{math.Inf(1), math.Inf(1), math.Inf(1)},
		Max: [3]float64{math.Inf(-1), math.Inf(-1), math.Inf(-1)},
	}
	
	for _, vertex := range mesh.Vertices {
		for i := 0; i < 3; i++ {
			bounds.Min[i] = math.Min(bounds.Min[i], vertex[i])
			bounds.Max[i] = math.Max(bounds.Max[i], vertex[i])
		}
	}
	
	return bounds
}

func (rs *ReconstructionStage) validateMesh(mesh *Mesh3D) error {
	if len(mesh.Vertices) == 0 {
		return fmt.Errorf("mesh has no vertices")
	}
	
	if len(mesh.Faces) == 0 {
		return fmt.Errorf("mesh has no faces")
	}
	
	// Check face indices are valid
	for _, face := range mesh.Faces {
		for _, idx := range face {
			if idx < 0 || idx >= len(mesh.Vertices) {
				return fmt.Errorf("invalid face index: %d", idx)
			}
		}
	}
	
	return nil
}

func (rs *ReconstructionStage) optimizeMesh(mesh *Mesh3D) {
	// Placeholder for mesh optimization
	// In production would implement vertex welding, normal recalculation, etc.
	rs.calculateQualityMetrics(mesh)
}

func (rs *ReconstructionStage) calculateQualityMetrics(mesh *Mesh3D) {
	mesh.Metadata.QualityMetrics = QualityMetrics{
		WatertightMesh: len(mesh.Faces) > 0,
		ManifoldEdges:  true, // Simplified
		AverageEdgeLength: 100.0, // Simplified
		AspectRatio:    1.0,
		SurfaceArea:    float64(len(mesh.Faces) * 100), // Rough estimate
		Volume:         float64(len(mesh.Vertices) * 1000), // Rough estimate
	}
}

func (rs *ReconstructionStage) exportMesh(mesh *Mesh3D, outputDir string) (string, error) {
	// Ensure output directory exists
	if err := os.MkdirAll(outputDir, 0755); err != nil {
		return "", fmt.Errorf("failed to create output directory: %w", err)
	}
	
	// Export OBJ format (simple text format)
	objFile := filepath.Join(outputDir, "building_model.obj")
	if err := rs.exportOBJ(mesh, objFile); err != nil {
		return "", fmt.Errorf("failed to export OBJ: %w", err)
	}
	
	return objFile, nil
}

func (rs *ReconstructionStage) exportOBJ(mesh *Mesh3D, filepath string) error {
	file, err := os.Create(filepath)
	if err != nil {
		return err
	}
	defer file.Close()
	
	// Write OBJ header
	file.WriteString("# ArxOS Generated Building Model\n")
	file.WriteString("# Progressive Construction Pipeline Output\n\n")
	
	// Write vertices
	for _, vertex := range mesh.Vertices {
		file.WriteString(fmt.Sprintf("v %.6f %.6f %.6f\n", 
			vertex[0]/1000.0, vertex[1]/1000.0, vertex[2]/1000.0)) // Convert mm to m
	}
	
	// Write normals
	for _, normal := range mesh.Normals {
		file.WriteString(fmt.Sprintf("vn %.6f %.6f %.6f\n", normal[0], normal[1], normal[2]))
	}
	
	// Write texture coordinates
	for _, uv := range mesh.UVs {
		file.WriteString(fmt.Sprintf("vt %.6f %.6f\n", uv[0], uv[1]))
	}
	
	// Write faces (OBJ indices are 1-based)
	for _, face := range mesh.Faces {
		file.WriteString(fmt.Sprintf("f %d %d %d\n", face[0]+1, face[1]+1, face[2]+1))
	}
	
	return nil
}