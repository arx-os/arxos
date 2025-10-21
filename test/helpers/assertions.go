/**
 * Test Assertions Helper - Custom assertions for integration tests
 */

package helpers

import (
	"fmt"
	"reflect"
	"testing"
	"time"

	"github.com/arx-os/arxos/internal/domain"
	"github.com/arx-os/arxos/internal/domain/spatial"
	"github.com/stretchr/testify/assert"
)

// AssertBuildingEqual asserts that two buildings are equal
func AssertBuildingEqual(t *testing.T, expected, actual *domain.Building, msgAndArgs ...any) bool {
	if expected == nil && actual == nil {
		return true
	}
	if expected == nil || actual == nil {
		return assert.Fail(t, "One building is nil", msgAndArgs...)
	}

	return assert.Equal(t, expected.ID, actual.ID, "Building ID mismatch") &&
		assert.Equal(t, expected.Name, actual.Name, "Building name mismatch") &&
		assert.Equal(t, expected.Address, actual.Address, "Building address mismatch") &&
		AssertLocationEqual(t, expected.Coordinates, actual.Coordinates, "Building coordinates mismatch")
}

// AssertEquipmentEqual asserts that two equipment items are equal
func AssertEquipmentEqual(t *testing.T, expected, actual *domain.Equipment, msgAndArgs ...any) bool {
	if expected == nil && actual == nil {
		return true
	}
	if expected == nil || actual == nil {
		return assert.Fail(t, "One equipment item is nil", msgAndArgs...)
	}

	return assert.Equal(t, expected.ID, actual.ID, "Equipment ID mismatch") &&
		assert.Equal(t, expected.Name, actual.Name, "Equipment name mismatch") &&
		assert.Equal(t, expected.Type, actual.Type, "Equipment type mismatch") &&
		assert.Equal(t, expected.Model, actual.Model, "Equipment model mismatch") &&
		assert.Equal(t, expected.Status, actual.Status, "Equipment status mismatch") &&
		assert.Equal(t, expected.BuildingID, actual.BuildingID, "Equipment building ID mismatch") &&
		AssertLocationEqual(t, expected.Location, actual.Location, "Equipment location mismatch")
}

// AssertLocationEqual asserts that two locations are equal
func AssertLocationEqual(t *testing.T, expected, actual *domain.Location, msgAndArgs ...any) bool {
	if expected == nil && actual == nil {
		return true
	}
	if expected == nil || actual == nil {
		return assert.Fail(t, "One location is nil", msgAndArgs...)
	}

	return assert.InDelta(t, expected.X, actual.X, 0.001, "Location X mismatch") &&
		assert.InDelta(t, expected.Y, actual.Y, 0.001, "Location Y mismatch") &&
		assert.InDelta(t, expected.Z, actual.Z, 0.001, "Location Z mismatch")
}

// AssertSpatialLocationEqual asserts that two spatial locations are equal
func AssertSpatialLocationEqual(t *testing.T, expected, actual *spatial.SpatialLocation, msgAndArgs ...any) bool {
	if expected == nil && actual == nil {
		return true
	}
	if expected == nil || actual == nil {
		return assert.Fail(t, "One spatial location is nil", msgAndArgs...)
	}

	return assert.InDelta(t, expected.X, actual.X, 0.001, "Spatial location X mismatch") &&
		assert.InDelta(t, expected.Y, actual.Y, 0.001, "Spatial location Y mismatch") &&
		assert.InDelta(t, expected.Z, actual.Z, 0.001, "Spatial location Z mismatch")
}

// AssertSpatialAnchorEqual asserts that two spatial anchors are equal
func AssertSpatialAnchorEqual(t *testing.T, expected, actual *spatial.SpatialAnchor, msgAndArgs ...any) bool {
	if expected == nil && actual == nil {
		return true
	}
	if expected == nil || actual == nil {
		return assert.Fail(t, "One spatial anchor is nil", msgAndArgs...)
	}

	return assert.Equal(t, expected.ID, actual.ID, "Spatial anchor ID mismatch") &&
		AssertSpatialLocationEqual(t, expected.Position, actual.Position, "Spatial anchor position mismatch") &&
		assert.InDelta(t, expected.Confidence, actual.Confidence, 0.001, "Spatial anchor confidence mismatch") &&
		assert.Equal(t, expected.BuildingID, actual.BuildingID, "Spatial anchor building ID mismatch") &&
		assert.Equal(t, expected.FloorID, actual.FloorID, "Spatial anchor floor ID mismatch")
}

// AssertAREquipmentOverlayEqual asserts that two AR equipment overlays are equal
func AssertAREquipmentOverlayEqual(t *testing.T, expected, actual *spatial.EquipmentAROverlay, msgAndArgs ...any) bool {
	if expected == nil && actual == nil {
		return true
	}
	if expected == nil || actual == nil {
		return assert.Fail(t, "One AR equipment overlay is nil", msgAndArgs...)
	}

	return assert.Equal(t, expected.EquipmentID, actual.EquipmentID, "AR equipment overlay ID mismatch") &&
		AssertSpatialLocationEqual(t, expected.Position, actual.Position, "AR equipment overlay position mismatch") &&
		assert.Equal(t, expected.Status, actual.Status, "AR equipment overlay status mismatch") &&
		assert.Equal(t, expected.ModelType, actual.ModelType, "AR equipment overlay model type mismatch")
}

// AssertARNavigationPathEqual asserts that two AR navigation paths are equal
func AssertARNavigationPathEqual(t *testing.T, expected, actual *spatial.ARNavigationPath, msgAndArgs ...any) bool {
	if expected == nil && actual == nil {
		return true
	}
	if expected == nil || actual == nil {
		return assert.Fail(t, "One AR navigation path is nil", msgAndArgs...)
	}

	return assert.Equal(t, expected.ID, actual.ID, "AR navigation path ID mismatch") &&
		assert.Equal(t, len(expected.Waypoints), len(actual.Waypoints), "AR navigation path waypoints count mismatch") &&
		assert.InDelta(t, expected.Distance, actual.Distance, 0.001, "AR navigation path distance mismatch") &&
		assert.InDelta(t, expected.EstimatedTime, actual.EstimatedTime, 0.001, "AR navigation path estimated time mismatch") &&
		assert.Equal(t, expected.Difficulty, actual.Difficulty, "AR navigation path difficulty mismatch") &&
		assert.Equal(t, expected.Accessibility, actual.Accessibility, "AR navigation path accessibility mismatch")
}

// AssertTimeEqual asserts that two times are equal within a tolerance
func AssertTimeEqual(t *testing.T, expected, actual time.Time, tolerance time.Duration, msgAndArgs ...any) bool {
	diff := expected.Sub(actual)
	if diff < 0 {
		diff = -diff
	}
	if diff <= tolerance {
		return true
	}
	return assert.Fail(t, fmt.Sprintf("Time difference %v exceeds tolerance %v", diff, tolerance), msgAndArgs...)
}

// AssertSliceEqual asserts that two slices are equal
func AssertSliceEqual(t *testing.T, expected, actual any, msgAndArgs ...any) bool {
	expectedValue := reflect.ValueOf(expected)
	actualValue := reflect.ValueOf(actual)

	if expectedValue.Kind() != reflect.Slice || actualValue.Kind() != reflect.Slice {
		return assert.Fail(t, "Both values must be slices", msgAndArgs...)
	}

	if expectedValue.Len() != actualValue.Len() {
		return assert.Fail(t, fmt.Sprintf("Slice lengths differ: expected %d, actual %d", expectedValue.Len(), actualValue.Len()), msgAndArgs...)
	}

	for i := 0; i < expectedValue.Len(); i++ {
		expectedItem := expectedValue.Index(i).Interface()
		actualItem := actualValue.Index(i).Interface()

		if !reflect.DeepEqual(expectedItem, actualItem) {
			return assert.Fail(t, fmt.Sprintf("Slice items at index %d differ: expected %v, actual %v", i, expectedItem, actualItem), msgAndArgs...)
		}
	}

	return true
}

// AssertMapEqual asserts that two maps are equal
func AssertMapEqual(t *testing.T, expected, actual any, msgAndArgs ...any) bool {
	expectedValue := reflect.ValueOf(expected)
	actualValue := reflect.ValueOf(actual)

	if expectedValue.Kind() != reflect.Map || actualValue.Kind() != reflect.Map {
		return assert.Fail(t, "Both values must be maps", msgAndArgs...)
	}

	if expectedValue.Len() != actualValue.Len() {
		return assert.Fail(t, fmt.Sprintf("Map lengths differ: expected %d, actual %d", expectedValue.Len(), actualValue.Len()), msgAndArgs...)
	}

	for _, key := range expectedValue.MapKeys() {
		expectedItem := expectedValue.MapIndex(key).Interface()
		actualItem := actualValue.MapIndex(key).Interface()

		if !reflect.DeepEqual(expectedItem, actualItem) {
			return assert.Fail(t, fmt.Sprintf("Map values for key %v differ: expected %v, actual %v", key.Interface(), expectedItem, actualItem), msgAndArgs...)
		}
	}

	return true
}

// AssertHTTPResponseEqual asserts that an HTTP response matches expectations
func AssertHTTPResponseEqual(t *testing.T, expectedStatus int, actualStatus int, expectedBody any, actualBody any, msgAndArgs ...any) bool {
	statusEqual := assert.Equal(t, expectedStatus, actualStatus, "HTTP status code mismatch")

	var bodyEqual bool
	if expectedBody == nil && actualBody == nil {
		bodyEqual = true
	} else if expectedBody == nil || actualBody == nil {
		bodyEqual = false
	} else {
		bodyEqual = reflect.DeepEqual(expectedBody, actualBody)
	}

	if !bodyEqual {
		assert.Fail(t, fmt.Sprintf("HTTP response body mismatch: expected %v, actual %v", expectedBody, actualBody), msgAndArgs...)
	}

	return statusEqual && bodyEqual
}

// AssertPerformanceWithinBounds asserts that performance metrics are within acceptable bounds
func AssertPerformanceWithinBounds(t *testing.T, metric string, value float64, min, max float64, msgAndArgs ...any) bool {
	if value < min || value > max {
		return assert.Fail(t, fmt.Sprintf("Performance metric %s value %f is outside bounds [%f, %f]", metric, value, min, max), msgAndArgs...)
	}
	return true
}

// AssertMemoryUsageWithinBounds asserts that memory usage is within acceptable bounds
func AssertMemoryUsageWithinBounds(t *testing.T, currentMB, maxMB float64, msgAndArgs ...any) bool {
	if currentMB > maxMB {
		return assert.Fail(t, fmt.Sprintf("Memory usage %f MB exceeds maximum %f MB", currentMB, maxMB), msgAndArgs...)
	}
	return true
}

// AssertResponseTimeWithinBounds asserts that response time is within acceptable bounds
func AssertResponseTimeWithinBounds(t *testing.T, duration time.Duration, maxDuration time.Duration, msgAndArgs ...any) bool {
	if duration > maxDuration {
		return assert.Fail(t, fmt.Sprintf("Response time %v exceeds maximum %v", duration, maxDuration), msgAndArgs...)
	}
	return true
}

// AssertErrorContains asserts that an error contains a specific message
func AssertErrorContains(t *testing.T, err error, contains string, msgAndArgs ...any) bool {
	if err == nil {
		return assert.Fail(t, "Expected error but got nil", msgAndArgs...)
	}
	return assert.Contains(t, err.Error(), contains, msgAndArgs...)
}

// AssertNoError asserts that there is no error
func AssertNoError(t *testing.T, err error, msgAndArgs ...any) bool {
	return assert.NoError(t, err, msgAndArgs...)
}

// AssertTrue asserts that a condition is true
func AssertTrue(t *testing.T, condition bool, msgAndArgs ...any) bool {
	return assert.True(t, condition, msgAndArgs...)
}

// AssertFalse asserts that a condition is false
func AssertFalse(t *testing.T, condition bool, msgAndArgs ...any) bool {
	return assert.False(t, condition, msgAndArgs...)
}

// AssertNotEmpty asserts that a value is not empty
func AssertNotEmpty(t *testing.T, value any, msgAndArgs ...any) bool {
	return assert.NotEmpty(t, value, msgAndArgs...)
}

// AssertEmpty asserts that a value is empty
func AssertEmpty(t *testing.T, value any, msgAndArgs ...any) bool {
	return assert.Empty(t, value, msgAndArgs...)
}

// AssertNil asserts that a value is nil
func AssertNil(t *testing.T, value any, msgAndArgs ...any) bool {
	return assert.Nil(t, value, msgAndArgs...)
}

// AssertNotNil asserts that a value is not nil
func AssertNotNil(t *testing.T, value any, msgAndArgs ...any) bool {
	return assert.NotNil(t, value, msgAndArgs...)
}

// AssertEqual asserts that two values are equal
func AssertEqual(t *testing.T, expected, actual any, msgAndArgs ...any) bool {
	return assert.Equal(t, expected, actual, msgAndArgs...)
}

// AssertNotEqual asserts that two values are not equal
func AssertNotEqual(t *testing.T, expected, actual any, msgAndArgs ...any) bool {
	return assert.NotEqual(t, expected, actual, msgAndArgs...)
}

// AssertContains asserts that a container contains a specific element
func AssertContains(t *testing.T, container, element any, msgAndArgs ...any) bool {
	return assert.Contains(t, container, element, msgAndArgs...)
}

// AssertNotContains asserts that a container does not contain a specific element
func AssertNotContains(t *testing.T, container, element any, msgAndArgs ...any) bool {
	return assert.NotContains(t, container, element, msgAndArgs...)
}

// AssertGreater asserts that the first value is greater than the second
func AssertGreater(t *testing.T, first, second any, msgAndArgs ...any) bool {
	return assert.Greater(t, first, second, msgAndArgs...)
}

// AssertLess asserts that the first value is less than the second
func AssertLess(t *testing.T, first, second any, msgAndArgs ...any) bool {
	return assert.Less(t, first, second, msgAndArgs...)
}

// AssertGreaterOrEqual asserts that the first value is greater than or equal to the second
func AssertGreaterOrEqual(t *testing.T, first, second any, msgAndArgs ...any) bool {
	return assert.GreaterOrEqual(t, first, second, msgAndArgs...)
}

// AssertLessOrEqual asserts that the first value is less than or equal to the second
func AssertLessOrEqual(t *testing.T, first, second any, msgAndArgs ...any) bool {
	return assert.LessOrEqual(t, first, second, msgAndArgs...)
}
