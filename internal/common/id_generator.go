package common

import (
	"fmt"
	"time"
)

// GenerateBuildingID generates a unique ID for new buildings
func GenerateBuildingID() string {
	return fmt.Sprintf("bld_%d", time.Now().UnixNano())
}

// GenerateEquipmentID generates a unique ID for new equipment
func GenerateEquipmentID() string {
	return fmt.Sprintf("eq_%d", time.Now().UnixNano())
}

// GenerateWorkflowID generates a unique ID for new workflows
func GenerateWorkflowID() string {
	return fmt.Sprintf("wf_%d", time.Now().UnixNano())
}

// GenerateDeviceID generates a unique ID for new devices
func GenerateDeviceID() string {
	return fmt.Sprintf("dev_%d", time.Now().UnixNano())
}
