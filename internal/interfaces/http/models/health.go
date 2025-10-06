package models

import "time"

// HealthResponse represents the health check response
type HealthResponse struct {
	Status    string         `json:"status"`
	Version   string         `json:"version"`
	Timestamp time.Time      `json:"timestamp"`
	Checks    map[string]any `json:"checks"`
}

// APIInfoResponse represents API information response
type APIInfoResponse struct {
	Version       string   `json:"version"`
	Name          string   `json:"name"`
	Description   string   `json:"description"`
	Endpoints     []string `json:"endpoints"`
	Documentation string   `json:"documentation"`
}

// StatusResponse represents system status response
type StatusResponse struct {
	Status    string            `json:"status"`
	Uptime    time.Duration     `json:"uptime"`
	Version   string            `json:"version"`
	Timestamp time.Time         `json:"timestamp"`
	Services  map[string]string `json:"services"`
}
