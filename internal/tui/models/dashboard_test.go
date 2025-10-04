package models

import (
	"testing"
	"time"

	tea "github.com/charmbracelet/bubbletea"
	"github.com/stretchr/testify/assert"

	"github.com/arx-os/arxos/internal/config"
	"github.com/arx-os/arxos/internal/tui/services"
	"github.com/arx-os/arxos/internal/tui/utils"
	"github.com/arx-os/arxos/pkg/models/building"
)

func TestDashboardModel_Init(t *testing.T) {
	config := &config.TUIConfig{
		Enabled:             true,
		Theme:               "dark",
		UpdateInterval:      "1s",
		MaxEquipmentDisplay: 1000,
		RealTimeEnabled:     true,
		AnimationsEnabled:   true,
	}

	model := NewDashboardModel(config, nil)

	// Test initialization
	cmd := model.Init()
	assert.NotNil(t, cmd)
}

func TestDashboardModel_Update(t *testing.T) {
	config := &config.TUIConfig{
		Enabled:             true,
		Theme:               "dark",
		UpdateInterval:      "1s",
		MaxEquipmentDisplay: 1000,
		RealTimeEnabled:     true,
		AnimationsEnabled:   true,
	}

	model := NewDashboardModel(config, nil)

	// Test window size message
	windowSizeMsg := tea.WindowSizeMsg{
		Width:  80,
		Height: 24,
	}

	updatedModel, cmd := model.Update(windowSizeMsg)
	assert.NotNil(t, updatedModel)
	assert.Nil(t, cmd)

	dashboardModel := updatedModel.(DashboardModel)
	assert.Equal(t, 80, dashboardModel.width)
	assert.Equal(t, 24, dashboardModel.height)
	assert.NotNil(t, dashboardModel.layout)
}

func TestDashboardModel_Update_KeyMessages(t *testing.T) {
	config := &config.TUIConfig{
		Enabled:             true,
		Theme:               "dark",
		UpdateInterval:      "1s",
		MaxEquipmentDisplay: 1000,
		RealTimeEnabled:     true,
		AnimationsEnabled:   true,
	}

	model := NewDashboardModel(config, nil)

	// Test tab navigation
	tabMsg := tea.KeyMsg{Type: tea.KeyTab}
	updatedModel, cmd := model.Update(tabMsg)
	assert.NotNil(t, updatedModel)
	assert.Nil(t, cmd)

	dashboardModel := updatedModel.(DashboardModel)
	assert.Equal(t, 1, dashboardModel.selectedTab)

	// Test quit message
	quitMsg := tea.KeyMsg{Type: tea.KeyCtrlC}
	updatedModel, cmd = model.Update(quitMsg)
	assert.NotNil(t, updatedModel)
	assert.NotNil(t, cmd)
}

func TestDashboardModel_Update_BuildingData(t *testing.T) {
	config := &config.TUIConfig{
		Enabled:             true,
		Theme:               "dark",
		UpdateInterval:      "1s",
		MaxEquipmentDisplay: 1000,
		RealTimeEnabled:     true,
		AnimationsEnabled:   true,
	}

	model := NewDashboardModel(config, nil)

	// Create mock building data
	buildingData := &building.BuildingModel{
		ID:   "ARXOS-001",
		Name: "Test Building",
	}

	equipment := []*building.Equipment{
		{
			ID:     "EQ-001",
			Type:   "HVAC",
			Status: "operational",
		},
	}

	alerts := []services.Alert{
		{
			ID:       "ALERT-001",
			Severity: "warning",
			Message:  "Test alert",
		},
	}

	metrics := &services.BuildingMetrics{
		Uptime:         98.5,
		EnergyPerSqM:   125.0,
		ResponseTime:   4 * time.Minute,
		Coverage:       92.3,
		TotalEquipment: 247,
		Operational:    187,
		Maintenance:    42,
		Offline:        18,
	}

	buildingDataMsg := BuildingDataMsg{
		Building:  buildingData,
		Equipment: equipment,
		Alerts:    alerts,
		Metrics:   metrics,
	}

	updatedModel, cmd := model.Update(buildingDataMsg)
	assert.NotNil(t, updatedModel)
	assert.Nil(t, cmd)

	dashboardModel := updatedModel.(DashboardModel)
	assert.False(t, dashboardModel.loading)
	assert.NotNil(t, dashboardModel.building)
	assert.NotNil(t, dashboardModel.equipment)
	assert.NotNil(t, dashboardModel.alerts)
	assert.NotNil(t, dashboardModel.metrics)
	assert.Equal(t, "ARXOS-001", dashboardModel.building.ID)
	assert.Equal(t, "Test Building", dashboardModel.building.Name)
	assert.Len(t, dashboardModel.equipment, 1)
	assert.Len(t, dashboardModel.alerts, 1)
}

func TestDashboardModel_View(t *testing.T) {
	config := &config.TUIConfig{
		Enabled:             true,
		Theme:               "dark",
		UpdateInterval:      "1s",
		MaxEquipmentDisplay: 1000,
		RealTimeEnabled:     true,
		AnimationsEnabled:   true,
	}

	model := NewDashboardModel(config, nil)

	// Test loading view
	loadingView := model.View()
	assert.Contains(t, loadingView, "Loading building data")

	// Test error view
	model.loading = false
	model.error = assert.AnError
	errorView := model.View()
	assert.Contains(t, errorView, "Error:")

	// Reset error and test with data
	model.error = nil
	model.loading = false
	model.building = &building.BuildingModel{
		ID:   "ARXOS-001",
		Name: "Test Building",
	}
	model.metrics = &services.BuildingMetrics{
		Uptime:         98.5,
		EnergyPerSqM:   125.0,
		ResponseTime:   4 * time.Minute,
		Coverage:       92.3,
		TotalEquipment: 247,
		Operational:    187,
		Maintenance:    42,
		Offline:        18,
	}

	// Set up layout
	model.width = 80
	model.height = 24
	model.layout = utils.NewLayout(80, 24, model.styles)

	view := model.View()
	assert.NotEmpty(t, view)
	assert.Contains(t, view, "Building: Test Building")
}

func TestBuildingMetrics(t *testing.T) {
	metrics := &services.BuildingMetrics{
		Uptime:         98.5,
		EnergyPerSqM:   125.0,
		ResponseTime:   4 * time.Minute,
		Coverage:       92.3,
		TotalEquipment: 247,
		Operational:    187,
		Maintenance:    42,
		Offline:        18,
	}

	assert.Equal(t, 98.5, metrics.Uptime)
	assert.Equal(t, 125.0, metrics.EnergyPerSqM)
	assert.Equal(t, 4*time.Minute, metrics.ResponseTime)
	assert.Equal(t, 92.3, metrics.Coverage)
	assert.Equal(t, 247, metrics.TotalEquipment)
	assert.Equal(t, 187, metrics.Operational)
	assert.Equal(t, 42, metrics.Maintenance)
	assert.Equal(t, 18, metrics.Offline)
}
