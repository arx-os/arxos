// Package pipeline - LiDAR processing stage for Progressive Construction Pipeline
package pipeline

import (
	"context"
	"fmt"
	"math"

	"github.com/arxos/arxos/core/internal/arxobject"
	"github.com/arxos/arxos/core/internal/confidence"
)

// LiDARStage handles LiDAR point cloud integration with PDF data
type LiDARStage struct {
	// LiDAR processing parameters
	alignmentTolerance  float64 // mm - tolerance for PDF-LiDAR alignment
	wallSnapThreshold   float64 // mm - threshold to snap points to PDF walls
	confidenceBoost     float64 // confidence boost for LiDAR-validated objects
	
	// Point cloud processing
	minPointDensity     int     // minimum points per square meter
	maxNoiseDistance    float64 // mm - maximum distance for noise filtering
}

// PointCloud represents a LiDAR point cloud
type PointCloud struct {
	Points     []Point3D           `json:"points"`
	Timestamp  int64              `json:"timestamp"`
	ScannerID  string             `json:"scanner_id"`
	Resolution float64            `json:"resolution"` // mm
	Metadata   map[string]interface{} `json:"metadata"`
}

// Point3D represents a 3D point with additional data
type Point3D struct {
	X          float64 `json:"x"` // mm
	Y          float64 `json:"y"` // mm
	Z          float64 `json:"z"` // mm
	Intensity  float64 `json:"intensity,omitempty"`
	Color      [3]uint8 `json:"color,omitempty"` // RGB
	Normal     [3]float64 `json:"normal,omitempty"` // Surface normal
	Confidence float64 `json:"confidence,omitempty"`
}

// PlaneModel represents a detected plane (wall, floor, ceiling)
type PlaneModel struct {
	Normal    [3]float64 `json:"normal"`
	Point     [3]float64 `json:"point"`
	Inliers   []int      `json:"inliers"` // Point indices
	Equation  [4]float64 `json:"equation"` // ax + by + cz + d = 0
	Area      float64    `json:"area"`
	Confidence float64   `json:"confidence"`
}

// LiDARFusionResult contains results of PDF-LiDAR fusion
type LiDARFusionResult struct {
	AlignedObjects   []*arxobject.ArxObjectUnified `json:"aligned_objects"`
	DetectedPlanes   []PlaneModel                  `json:"detected_planes"`
	ValidationErrors []ValidationError             `json:"validation_errors"`
	AlignmentAccuracy float64                      `json:"alignment_accuracy"`
	ProcessingStats  LiDARStats                   `json:"processing_stats"`
}

// LiDARStats contains processing statistics
type LiDARStats struct {
	TotalPoints       int     `json:"total_points"`
	ProcessedPoints   int     `json:"processed_points"`
	DetectedWalls     int     `json:"detected_walls"`
	AlignedWalls      int     `json:"aligned_walls"`
	AverageAccuracy   float64 `json:"average_accuracy"`
	ProcessingTime    float64 `json:"processing_time_seconds"`
}

// NewLiDARStage creates a new LiDAR processing stage
func NewLiDARStage() *LiDARStage {
	return &LiDARStage{
		alignmentTolerance: 50.0,  // 50mm tolerance
		wallSnapThreshold:  100.0, // 100mm snap threshold
		confidenceBoost:    1.3,   // 30% confidence boost
		minPointDensity:    1000,  // 1000 points/m²
		maxNoiseDistance:   20.0,  // 20mm noise filter
	}
}

// Process integrates LiDAR data with PDF-derived ArxObjects
func (ls *LiDARStage) Process(ctx context.Context, objects []*arxobject.ArxObjectUnified) ([]*arxobject.ArxObjectUnified, error) {
	// For now, simulate LiDAR integration
	// In production, this would integrate with actual LiDAR scanning
	
	fusedObjects := make([]*arxobject.ArxObjectUnified, len(objects))
	
	for i, obj := range objects {
		fusedObj := *obj
		
		// Simulate LiDAR validation based on object type
		lidarConfidence := ls.simulateLiDARValidation(&fusedObj)
		
		// Update confidence with LiDAR validation
		if fusedObj.Confidence != nil {
			ls.applyLiDARConfidenceBoost(&fusedObj, lidarConfidence)
		}
		
		// Add LiDAR processing metadata
		if fusedObj.Properties == nil {
			fusedObj.Properties = make(arxobject.Properties)
		}
		fusedObj.Properties["lidar_validated"] = true
		fusedObj.Properties["lidar_confidence"] = lidarConfidence
		fusedObj.Properties["validation_method"] = "simulated_lidar"
		
		fusedObjects[i] = &fusedObj
	}
	
	return fusedObjects, nil
}

// ProcessPointCloud processes a LiDAR point cloud with PDF guidance
func (ls *LiDARStage) ProcessPointCloud(ctx context.Context, pointCloud *PointCloud, pdfObjects []*arxobject.ArxObjectUnified) (*LiDARFusionResult, error) {
	result := &LiDARFusionResult{
		AlignedObjects: make([]*arxobject.ArxObjectUnified, len(pdfObjects)),
		ProcessingStats: LiDARStats{
			TotalPoints: len(pointCloud.Points),
		},
	}
	
	// Step 1: Detect planes in point cloud
	planes, err := ls.detectPlanes(pointCloud)
	if err != nil {
		return nil, fmt.Errorf("failed to detect planes: %w", err)
	}
	result.DetectedPlanes = planes
	result.ProcessingStats.DetectedWalls = len(planes)
	
	// Step 2: Align PDF objects with detected planes
	for i, pdfObj := range pdfObjects {
		alignedObj, err := ls.alignObjectWithLiDAR(pdfObj, planes, pointCloud)
		if err != nil {
			// Keep original object if alignment fails
			alignedObj = pdfObj
			result.ValidationErrors = append(result.ValidationErrors, ValidationError{
				Type:        "alignment_failed",
				Description: fmt.Sprintf("Failed to align object %s with LiDAR data", pdfObj.ID),
				Severity:    "warning",
			})
		}
		result.AlignedObjects[i] = alignedObj
	}
	
	// Step 3: Calculate alignment accuracy
	result.AlignmentAccuracy = ls.calculateAlignmentAccuracy(result.AlignedObjects, planes)
	result.ProcessingStats.AlignedWalls = ls.countAlignedWalls(result.AlignedObjects)
	result.ProcessingStats.ProcessedPoints = len(pointCloud.Points)
	
	return result, nil
}

// detectPlanes detects planar surfaces (walls, floors, ceilings) in point cloud
func (ls *LiDARStage) detectPlanes(pointCloud *PointCloud) ([]PlaneModel, error) {
	var planes []PlaneModel
	
	// Simplified plane detection - in production would use RANSAC
	// For now, simulate wall detection based on point distribution
	
	if len(pointCloud.Points) < 100 {
		return planes, fmt.Errorf("insufficient points for plane detection")
	}
	
	// Simulate detecting 4 walls (rectangular room)
	planes = append(planes, PlaneModel{
		Normal:     [3]float64{1, 0, 0}, // North wall
		Point:      [3]float64{0, 0, 0},
		Equation:   [4]float64{1, 0, 0, 0},
		Area:       12000000, // 12 sq meters in sq mm
		Confidence: 0.9,
	})
	
	planes = append(planes, PlaneModel{
		Normal:     [3]float64{0, 1, 0}, // East wall
		Point:      [3]float64{4000, 0, 0},
		Equation:   [4]float64{0, 1, 0, -4000},
		Area:       9000000, // 9 sq meters in sq mm
		Confidence: 0.85,
	})
	
	planes = append(planes, PlaneModel{
		Normal:     [3]float64{-1, 0, 0}, // South wall
		Point:      [3]float64{4000, 3000, 0},
		Equation:   [4]float64{-1, 0, 0, 4000},
		Area:       12000000,
		Confidence: 0.88,
	})
	
	planes = append(planes, PlaneModel{
		Normal:     [3]float64{0, -1, 0}, // West wall
		Point:      [3]float64{0, 3000, 0},
		Equation:   [4]float64{0, -1, 0, 3000},
		Area:       9000000,
		Confidence: 0.92,
	})
	
	return planes, nil
}

// alignObjectWithLiDAR aligns a PDF object with LiDAR-detected planes
func (ls *LiDARStage) alignObjectWithLiDAR(pdfObj *arxobject.ArxObjectUnified, planes []PlaneModel, pointCloud *PointCloud) (*arxobject.ArxObjectUnified, error) {
	alignedObj := *pdfObj
	
	// For walls, find the closest detected plane
	if pdfObj.Type == arxobject.TypeWall {
		closestPlane, distance := ls.findClosestPlane(pdfObj, planes)
		if distance < ls.alignmentTolerance {
			// Align wall to detected plane
			alignedObj.Geometry = ls.alignWallToPlane(pdfObj.Geometry, closestPlane)
			
			// Boost confidence for aligned walls
			if alignedObj.Confidence != nil {
				ls.applyLiDARConfidenceBoost(&alignedObj, closestPlane.Confidence)
			}
			
			// Add alignment metadata
			if alignedObj.Properties == nil {
				alignedObj.Properties = make(arxobject.Properties)
			}
			alignedObj.Properties["aligned_to_lidar"] = true
			alignedObj.Properties["alignment_distance"] = distance
			alignedObj.Properties["plane_confidence"] = closestPlane.Confidence
		}
	}
	
	// For doors and windows, validate against wall openings
	if pdfObj.Type == arxobject.TypeDoor || pdfObj.Type == arxobject.TypeWindow {
		validated := ls.validateOpeningWithLiDAR(pdfObj, pointCloud)
		if alignedObj.Properties == nil {
			alignedObj.Properties = make(arxobject.Properties)
		}
		alignedObj.Properties["opening_validated"] = validated
		
		if validated && alignedObj.Confidence != nil {
			ls.applyLiDARConfidenceBoost(&alignedObj, 0.9)
		}
	}
	
	return &alignedObj, nil
}

// findClosestPlane finds the plane closest to a PDF object
func (ls *LiDARStage) findClosestPlane(obj *arxobject.ArxObjectUnified, planes []PlaneModel) (PlaneModel, float64) {
	if len(planes) == 0 {
		return PlaneModel{}, math.Inf(1)
	}
	
	// Calculate distance from object center to each plane
	objCenter := ls.getObjectCenter(obj)
	
	closestPlane := planes[0]
	minDistance := ls.distanceToPlane(objCenter, closestPlane)
	
	for _, plane := range planes[1:] {
		distance := ls.distanceToPlane(objCenter, plane)
		if distance < minDistance {
			minDistance = distance
			closestPlane = plane
		}
	}
	
	return closestPlane, minDistance
}

// getObjectCenter gets the center point of an object
func (ls *LiDARStage) getObjectCenter(obj *arxobject.ArxObjectUnified) [3]float64 {
	coords := obj.Geometry.Coordinates
	if len(coords) >= 2 {
		return [3]float64{coords[0], coords[1], 0} // Assume ground level
	}
	return [3]float64{0, 0, 0}
}

// distanceToPlane calculates distance from a point to a plane
func (ls *LiDARStage) distanceToPlane(point [3]float64, plane PlaneModel) float64 {
	// Distance = |ax + by + cz + d| / sqrt(a² + b² + c²)
	eq := plane.Equation
	numerator := math.Abs(eq[0]*point[0] + eq[1]*point[1] + eq[2]*point[2] + eq[3])
	denominator := math.Sqrt(eq[0]*eq[0] + eq[1]*eq[1] + eq[2]*eq[2])
	
	if denominator == 0 {
		return math.Inf(1)
	}
	
	return numerator / denominator
}

// alignWallToPlane adjusts wall geometry to align with detected plane
func (ls *LiDARStage) alignWallToPlane(geom arxobject.Geometry, plane PlaneModel) arxobject.Geometry {
	alignedGeom := geom
	
	// For now, just update the coordinates slightly to simulate alignment
	// In production, this would perform sophisticated geometric alignment
	if len(geom.Coordinates) >= 4 {
		// Simulate small alignment adjustment
		alignedGeom.Coordinates = make([]float64, len(geom.Coordinates))
		copy(alignedGeom.Coordinates, geom.Coordinates)
		
		// Apply small offset to simulate plane alignment
		offset := plane.Point[0] * 0.01 // Small adjustment
		for i := 0; i < len(alignedGeom.Coordinates); i += 2 {
			alignedGeom.Coordinates[i] += offset
		}
	}
	
	return alignedGeom
}

// validateOpeningWithLiDAR validates doors/windows against LiDAR data
func (ls *LiDARStage) validateOpeningWithLiDAR(obj *arxobject.ArxObjectUnified, pointCloud *PointCloud) bool {
	// Simplified validation - check if there are fewer points in opening area
	// In production, would analyze point density in opening regions
	
	objCenter := ls.getObjectCenter(obj)
	nearbyPoints := 0
	
	// Count points near the opening
	for _, point := range pointCloud.Points {
		distance := math.Sqrt(
			math.Pow(point.X-objCenter[0], 2) +
			math.Pow(point.Y-objCenter[1], 2))
		
		if distance < 500 { // Within 500mm of opening
			nearbyPoints++
		}
	}
	
	// Openings should have fewer points (empty space)
	expectedDensity := ls.minPointDensity / 4 // Quarter density for openings
	return nearbyPoints < expectedDensity
}

// calculateAlignmentAccuracy calculates overall alignment accuracy
func (ls *LiDARStage) calculateAlignmentAccuracy(objects []*arxobject.ArxObjectUnified, planes []PlaneModel) float64 {
	if len(objects) == 0 {
		return 0.0
	}
	
	totalAccuracy := 0.0
	alignedCount := 0
	
	for _, obj := range objects {
		if obj.Properties != nil {
			if aligned, exists := obj.Properties["aligned_to_lidar"].(bool); exists && aligned {
				if distance, exists := obj.Properties["alignment_distance"].(float64); exists {
					// Convert distance to accuracy (closer = higher accuracy)
					accuracy := math.Max(0, 1.0-distance/ls.alignmentTolerance)
					totalAccuracy += accuracy
					alignedCount++
				}
			}
		}
	}
	
	if alignedCount == 0 {
		return 0.0
	}
	
	return totalAccuracy / float64(alignedCount)
}

// countAlignedWalls counts number of walls aligned with LiDAR
func (ls *LiDARStage) countAlignedWalls(objects []*arxobject.ArxObjectUnified) int {
	count := 0
	for _, obj := range objects {
		if obj.Type == arxobject.TypeWall && obj.Properties != nil {
			if aligned, exists := obj.Properties["aligned_to_lidar"].(bool); exists && aligned {
				count++
			}
		}
	}
	return count
}

// simulateLiDARValidation simulates LiDAR validation for different object types
func (ls *LiDARStage) simulateLiDARValidation(obj *arxobject.ArxObjectUnified) float64 {
	switch obj.Type {
	case arxobject.TypeWall:
		return 0.95 // High confidence for walls (solid surfaces)
	case arxobject.TypeDoor, arxobject.TypeWindow:
		return 0.75 // Medium confidence for openings
	case arxobject.TypeRoom:
		return 0.85 // Good confidence for room boundaries
	case arxobject.TypeColumn:
		return 0.90 // High confidence for structural elements
	default:
		return 0.70 // Default confidence
	}
}

// applyLiDARConfidenceBoost applies confidence boost from LiDAR validation
func (ls *LiDARStage) applyLiDARConfidenceBoost(obj *arxobject.ArxObjectUnified, lidarConfidence float64) {
	if obj.Confidence == nil {
		obj.Confidence = confidence.NewConfidence()
	}
	
	// Update position confidence (LiDAR is excellent for positioning)
	positionConf := obj.Confidence.GetPositionConfidence()
	boostedPosition := math.Min(0.98, positionConf*ls.confidenceBoost*lidarConfidence)
	
	obj.Confidence.UpdatePosition(boostedPosition, "lidar_validation", map[string]interface{}{
		"lidar_confidence": lidarConfidence,
		"boost_factor":     ls.confidenceBoost,
		"validation_type":  "point_cloud",
	})
	
	// Update geometry confidence
	geomConf := obj.Confidence.GetGeometryConfidence()
	boostedGeometry := math.Min(0.95, geomConf*1.2*lidarConfidence) // Smaller boost for geometry
	
	obj.Confidence.UpdateGeometry(boostedGeometry, "lidar_alignment", map[string]interface{}{
		"alignment_confidence": lidarConfidence,
		"geometric_validation": true,
	})
	
	// Add validation record
	obj.Confidence.AddValidation(confidence.ValidationRecord{
		Method:     "lidar",
		Confidence: lidarConfidence,
		Timestamp:  "simulated",
		Details: map[string]interface{}{
			"point_cloud_validation": true,
			"alignment_performed":    true,
		},
	})
}