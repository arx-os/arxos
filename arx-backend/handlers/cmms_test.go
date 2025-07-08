package handlers

import (
	"bytes"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"

	"context"

	"github.com/go-chi/chi/v5"
)

func TestGetCMMSConnections(t *testing.T) {
	req := httptest.NewRequest("GET", "/cmms/connections", nil)
	rr := httptest.NewRecorder()
	GetCMMSConnections(rr, req)
	if rr.Code != http.StatusOK {
		t.Errorf("expected 200, got %d", rr.Code)
	}
}

func TestCreateCMMSConnection(t *testing.T) {
	body := map[string]interface{}{
		"name":      "Test CMMS",
		"type":      "test",
		"base_url":  "http://localhost",
		"is_active": true,
	}
	b, _ := json.Marshal(body)
	req := httptest.NewRequest("POST", "/cmms/connections", bytes.NewReader(b))
	rr := httptest.NewRecorder()
	CreateCMMSConnection(rr, req)
	if rr.Code != http.StatusCreated {
		t.Errorf("expected 201, got %d", rr.Code)
	}
}

func TestUpdateCMMSConnection(t *testing.T) {
	body := map[string]interface{}{
		"name": "Updated CMMS",
	}
	b, _ := json.Marshal(body)
	req := httptest.NewRequest("PUT", "/cmms/connections/1", bytes.NewReader(b))
	rctx := chi.NewRouteContext()
	rctx.URLParams.Add("id", "1")
	req = req.WithContext(context.WithValue(req.Context(), chi.RouteCtxKey, rctx))
	rr := httptest.NewRecorder()
	UpdateCMMSConnection(rr, req)
	if rr.Code != http.StatusOK {
		t.Errorf("expected 200, got %d", rr.Code)
	}
}

func TestDeleteCMMSConnection(t *testing.T) {
	req := httptest.NewRequest("DELETE", "/cmms/connections/1", nil)
	rctx := chi.NewRouteContext()
	rctx.URLParams.Add("id", "1")
	req = req.WithContext(context.WithValue(req.Context(), chi.RouteCtxKey, rctx))
	rr := httptest.NewRecorder()
	DeleteCMMSConnection(rr, req)
	if rr.Code != http.StatusOK {
		t.Errorf("expected 200, got %d", rr.Code)
	}
}

func TestGetCMMSMappings(t *testing.T) {
	req := httptest.NewRequest("GET", "/cmms/connections/1/mappings", nil)
	rctx := chi.NewRouteContext()
	rctx.URLParams.Add("connectionId", "1")
	req = req.WithContext(context.WithValue(req.Context(), chi.RouteCtxKey, rctx))
	rr := httptest.NewRecorder()
	GetCMMSMappings(rr, req)
	if rr.Code != http.StatusOK {
		t.Errorf("expected 200, got %d", rr.Code)
	}
}

func TestCreateCMMSMapping(t *testing.T) {
	body := map[string]interface{}{
		"arxos_field": "asset_id",
		"cmms_field":  "cmms_asset_id",
		"data_type":   "string",
	}
	b, _ := json.Marshal(body)
	req := httptest.NewRequest("POST", "/cmms/connections/1/mappings", bytes.NewReader(b))
	rctx := chi.NewRouteContext()
	rctx.URLParams.Add("connectionId", "1")
	req = req.WithContext(context.WithValue(req.Context(), chi.RouteCtxKey, rctx))
	rr := httptest.NewRecorder()
	CreateCMMSMapping(rr, req)
	if rr.Code != http.StatusCreated {
		t.Errorf("expected 201, got %d", rr.Code)
	}
}

func TestSyncCMMSData(t *testing.T) {
	req := httptest.NewRequest("POST", "/cmms/connections/1/sync?type=schedules", nil)
	rctx := chi.NewRouteContext()
	rctx.URLParams.Add("connectionId", "1")
	req = req.WithContext(context.WithValue(req.Context(), chi.RouteCtxKey, rctx))
	rr := httptest.NewRecorder()
	SyncCMMSData(rr, req)
	if rr.Code != http.StatusOK {
		t.Errorf("expected 200, got %d", rr.Code)
	}
}

func TestTestCMMSConnection(t *testing.T) {
	req := httptest.NewRequest("POST", "/cmms/connections/1/test", nil)
	rctx := chi.NewRouteContext()
	rctx.URLParams.Add("id", "1")
	req = req.WithContext(context.WithValue(req.Context(), chi.RouteCtxKey, rctx))
	rr := httptest.NewRecorder()
	TestCMMSConnection(rr, req)
	if rr.Code != http.StatusOK {
		t.Errorf("expected 200, got %d", rr.Code)
	}
}

func TestManualCMMSSync(t *testing.T) {
	req := httptest.NewRequest("POST", "/cmms/connections/1/sync", nil)
	rctx := chi.NewRouteContext()
	rctx.URLParams.Add("id", "1")
	req = req.WithContext(context.WithValue(req.Context(), chi.RouteCtxKey, rctx))
	rr := httptest.NewRecorder()
	ManualCMMSSync(rr, req)
	if rr.Code != http.StatusOK {
		t.Errorf("expected 200, got %d", rr.Code)
	}
}
