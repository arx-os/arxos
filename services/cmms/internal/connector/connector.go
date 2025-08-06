package connector

import (
	"arx-cmms/pkg/models"
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"log"
	"net/http"
	"strings"
	"sync"
	"time"

	"gorm.io/gorm"
)

type AuthType int

const (
	AuthAPIKey AuthType = iota
	AuthBasic
	AuthOAuth2
)

type CMMSConnector struct {
	conn   *models.CMMSConnection
	client *http.Client
	mutex  sync.Mutex
	db     *gorm.DB
}

func NewCMMSConnector(conn *models.CMMSConnection, db *gorm.DB) *CMMSConnector {
	client := &http.Client{Timeout: 15 * time.Second}
	return &CMMSConnector{
		conn:   conn,
		client: client,
		db:     db,
	}
}

// GetClient returns the HTTP client for external use
func (c *CMMSConnector) GetClient() *http.Client {
	return c.client
}

func (c *CMMSConnector) getAuthType() AuthType {
	if c.conn.OAuth2ClientID != nil && *c.conn.OAuth2ClientID != "" && c.conn.OAuth2Secret != nil && *c.conn.OAuth2Secret != "" {
		return AuthOAuth2
	}
	if c.conn.APIKey != "" {
		return AuthAPIKey
	}
	if c.conn.Username != "" && c.conn.Password != "" {
		return AuthBasic
	}
	return AuthAPIKey // fallback
}

func (c *CMMSConnector) addAuthHeaders(req *http.Request) error {
	switch c.getAuthType() {
	case AuthAPIKey:
		if c.conn.APIKey != "" {
			req.Header.Set("Authorization", "Bearer "+c.conn.APIKey)
		}
	case AuthBasic:
		if c.conn.Username != "" && c.conn.Password != "" {
			req.SetBasicAuth(c.conn.Username, c.conn.Password)
		}
	case AuthOAuth2:
		token, err := c.getOAuth2Token()
		if err != nil {
			return err
		}
		req.Header.Set("Authorization", "Bearer "+token)
	}
	return nil
}

func (c *CMMSConnector) getOAuth2Token() (string, error) {
	// Simple client credentials grant
	if c.conn.OAuth2TokenURL == nil || *c.conn.OAuth2TokenURL == "" || 
	   c.conn.OAuth2ClientID == nil || *c.conn.OAuth2ClientID == "" || 
	   c.conn.OAuth2Secret == nil || *c.conn.OAuth2Secret == "" {
		return "", errors.New("OAuth2 credentials missing")
	}
	
	scope := ""
	if c.conn.OAuth2Scope != nil {
		scope = *c.conn.OAuth2Scope
	}
	
	data := fmt.Sprintf("grant_type=client_credentials&client_id=%s&client_secret=%s&scope=%s",
		*c.conn.OAuth2ClientID, *c.conn.OAuth2Secret, scope)
	resp, err := http.Post(*c.conn.OAuth2TokenURL, "application/x-www-form-urlencoded", strings.NewReader(data))
	if err != nil {
		return "", err
	}
	defer resp.Body.Close()
	if resp.StatusCode != 200 {
		return "", fmt.Errorf("OAuth2 token error: %s", resp.Status)
	}
	var result struct {
		AccessToken string `json:"access_token"`
	}
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return "", err
	}
	return result.AccessToken, nil
}

func (c *CMMSConnector) TestConnection() error {
	url := c.conn.BaseURL + "/ping"
	req, err := http.NewRequest("GET", url, nil)
	if err != nil {
		return err
	}
	if err := c.addAuthHeaders(req); err != nil {
		return err
	}
	resp, err := c.client.Do(req)
	if err != nil {
		return err
	}
	defer resp.Body.Close()
	if resp.StatusCode >= 200 && resp.StatusCode < 300 {
		return nil
	}
	return fmt.Errorf("Ping failed: %s", resp.Status)
}

func (c *CMMSConnector) SyncAll(ctx context.Context) error {
	// Example: sync schedules, work orders, specs
	if err := c.syncSchedules(ctx); err != nil {
		return err
	}
	if err := c.syncWorkOrders(ctx); err != nil {
		return err
	}
	if err := c.syncEquipmentSpecs(ctx); err != nil {
		return err
	}
	return nil
}

func (c *CMMSConnector) syncSchedules(ctx context.Context) error {
	// Generic CMMS API endpoint for schedules
	endpoint := c.conn.BaseURL + "/api/schedules"
	if c.conn.Type == "upkeep" {
		endpoint = c.conn.BaseURL + "/api/v1/schedules"
	} else if c.conn.Type == "fiix" {
		endpoint = c.conn.BaseURL + "/api/v2/schedules"
	}

	req, err := http.NewRequestWithContext(ctx, "GET", endpoint, nil)
	if err != nil {
		return fmt.Errorf("failed to create request: %w", err)
	}

	if err := c.addAuthHeaders(req); err != nil {
		return fmt.Errorf("failed to add auth headers: %w", err)
	}

	resp, err := c.client.Do(req)
	if err != nil {
		return fmt.Errorf("failed to fetch schedules: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return fmt.Errorf("schedules API returned status: %d", resp.StatusCode)
	}

	var schedules []map[string]interface{}
	if err := json.NewDecoder(resp.Body).Decode(&schedules); err != nil {
		return fmt.Errorf("failed to decode schedules response: %w", err)
	}

	// Store fetched data in a temporary table or pass to sync manager
	// For now, we'll log the count and return success
	log.Printf("Fetched %d schedules from CMMS", len(schedules))
	return nil
}

func (c *CMMSConnector) syncWorkOrders(ctx context.Context) error {
	// Generic CMMS API endpoint for work orders
	endpoint := c.conn.BaseURL + "/api/work-orders"
	if c.conn.Type == "upkeep" {
		endpoint = c.conn.BaseURL + "/api/v1/work-orders"
	} else if c.conn.Type == "fiix" {
		endpoint = c.conn.BaseURL + "/api/v2/work-orders"
	}

	req, err := http.NewRequestWithContext(ctx, "GET", endpoint, nil)
	if err != nil {
		return fmt.Errorf("failed to create request: %w", err)
	}

	if err := c.addAuthHeaders(req); err != nil {
		return fmt.Errorf("failed to add auth headers: %w", err)
	}

	resp, err := c.client.Do(req)
	if err != nil {
		return fmt.Errorf("failed to fetch work orders: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return fmt.Errorf("work orders API returned status: %d", resp.StatusCode)
	}

	var workOrders []map[string]interface{}
	if err := json.NewDecoder(resp.Body).Decode(&workOrders); err != nil {
		return fmt.Errorf("failed to decode work orders response: %w", err)
	}

	log.Printf("Fetched %d work orders from CMMS", len(workOrders))
	return nil
}

func (c *CMMSConnector) syncEquipmentSpecs(ctx context.Context) error {
	// Generic CMMS API endpoint for equipment specifications
	endpoint := c.conn.BaseURL + "/api/equipment/specifications"
	if c.conn.Type == "upkeep" {
		endpoint = c.conn.BaseURL + "/api/v1/equipment/specifications"
	} else if c.conn.Type == "fiix" {
		endpoint = c.conn.BaseURL + "/api/v2/equipment/specifications"
	}

	req, err := http.NewRequestWithContext(ctx, "GET", endpoint, nil)
	if err != nil {
		return fmt.Errorf("failed to create request: %w", err)
	}

	if err := c.addAuthHeaders(req); err != nil {
		return fmt.Errorf("failed to add auth headers: %w", err)
	}

	resp, err := c.client.Do(req)
	if err != nil {
		return fmt.Errorf("failed to fetch equipment specs: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return fmt.Errorf("equipment specs API returned status: %d", resp.StatusCode)
	}

	var specs []map[string]interface{}
	if err := json.NewDecoder(resp.Body).Decode(&specs); err != nil {
		return fmt.Errorf("failed to decode equipment specs response: %w", err)
	}

	log.Printf("Fetched %d equipment specifications from CMMS", len(specs))
	return nil
}

// Scheduler
func StartCMMSSyncScheduler(db *gorm.DB) {
	go func() {
		for {
			conns := []*models.CMMSConnection{}
			db.Find(&conns, "is_active = ?", true)
			for _, conn := range conns {
				interval := time.Duration(conn.SyncIntervalMin)
				if interval == 0 {
					interval = 60
				}
				go runCMMSSyncLoop(conn, interval, db)
			}
			time.Sleep(5 * time.Minute)
		}
	}()
}

func runCMMSSyncLoop(conn *models.CMMSConnection, intervalMin time.Duration, db *gorm.DB) {
	connector := NewCMMSConnector(conn, db)
	for {
		err := retry(func() error {
			ctx, cancel := context.WithTimeout(context.Background(), 10*time.Minute)
			defer cancel()
			return connector.SyncAll(ctx)
		}, 3)
		status := "success"
		errMsg := ""
		if err != nil {
			status = "error"
			errMsg = err.Error()
			log.Printf("CMMS sync error for %s: %v", conn.Name, err)
		}
		db.Exec("UPDATE cmms_connections SET last_sync = ?, last_sync_status = ?, last_sync_error = ?, updated_at = ? WHERE id = ?",
			time.Now(), status, errMsg, time.Now(), conn.ID)
		time.Sleep(intervalMin * time.Minute)
	}
}

func retry(fn func() error, attempts int) error {
	var err error
	for i := 0; i < attempts; i++ {
		err = fn()
		if err == nil {
			return nil
		}
		time.Sleep(time.Duration(2<<i) * time.Second) // Exponential backoff
	}
	return err
}
