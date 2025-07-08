package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"os"
	"time"

	"github.com/urfave/cli/v2"
)

const (
	baseURL = "http://localhost:8080/api/admin/data-vendor"
)

type APIKey struct {
	ID          uint      `json:"id"`
	Key         string    `json:"key"`
	VendorName  string    `json:"vendor_name"`
	Email       string    `json:"email"`
	AccessLevel string    `json:"access_level"`
	RateLimit   int       `json:"rate_limit"`
	IsActive    bool      `json:"is_active"`
	ExpiresAt   time.Time `json:"expires_at"`
	CreatedAt   time.Time `json:"created_at"`
	UpdatedAt   time.Time `json:"updated_at"`
}

type Dashboard struct {
	ActiveKeys     int64   `json:"active_keys"`
	TodayRequests  int64   `json:"today_requests"`
	MonthlyRevenue float64 `json:"monthly_revenue"`
	RateLimitHits  int64   `json:"rate_limit_hits"`
}

type UsageStats struct {
	TotalRequests   int64   `json:"total_requests"`
	SuccessRate     float64 `json:"success_rate"`
	AvgResponseTime int     `json:"avg_response_time"`
}

func main() {
	app := &cli.App{
		Name:  "data-vendor-cli",
		Usage: "Manage data vendor API keys and monitor usage",
		Commands: []*cli.Command{
			{
				Name:   "dashboard",
				Usage:  "Show dashboard with key metrics",
				Action: showDashboard,
			},
			{
				Name:   "list",
				Usage:  "List all API keys",
				Action: listAPIKeys,
			},
			{
				Name:  "create",
				Usage: "Create a new API key",
				Flags: []cli.Flag{
					&cli.StringFlag{
						Name:     "vendor",
						Aliases:  []string{"v"},
						Usage:    "Vendor name",
						Required: true,
					},
					&cli.StringFlag{
						Name:     "email",
						Aliases:  []string{"e"},
						Usage:    "Vendor email",
						Required: true,
					},
					&cli.StringFlag{
						Name:    "level",
						Aliases: []string{"l"},
						Usage:   "Access level (basic, premium, enterprise)",
						Value:   "basic",
					},
					&cli.IntFlag{
						Name:    "rate-limit",
						Aliases: []string{"r"},
						Usage:   "Rate limit (requests per hour)",
						Value:   1000,
					},
					&cli.StringFlag{
						Name:    "expires",
						Aliases: []string{"x"},
						Usage:   "Expiration date (YYYY-MM-DD)",
						Value:   time.Now().AddDate(1, 0, 0).Format("2006-01-02"),
					},
				},
				Action: createAPIKey,
			},
			{
				Name:  "show",
				Usage: "Show details for a specific API key",
				Flags: []cli.Flag{
					&cli.UintFlag{
						Name:     "id",
						Aliases:  []string{"i"},
						Usage:    "API key ID",
						Required: true,
					},
				},
				Action: showAPIKey,
			},
			{
				Name:  "activate",
				Usage: "Activate an API key",
				Flags: []cli.Flag{
					&cli.UintFlag{
						Name:     "id",
						Aliases:  []string{"i"},
						Usage:    "API key ID",
						Required: true,
					},
				},
				Action: activateAPIKey,
			},
			{
				Name:  "deactivate",
				Usage: "Deactivate an API key",
				Flags: []cli.Flag{
					&cli.UintFlag{
						Name:     "id",
						Aliases:  []string{"i"},
						Usage:    "API key ID",
						Required: true,
					},
				},
				Action: deactivateAPIKey,
			},
			{
				Name:  "usage",
				Usage: "Show usage statistics",
				Flags: []cli.Flag{
					&cli.StringFlag{
						Name:    "days",
						Aliases: []string{"d"},
						Usage:   "Number of days to look back",
						Value:   "30",
					},
					&cli.StringFlag{
						Name:    "vendor",
						Aliases: []string{"v"},
						Usage:   "Filter by vendor name",
					},
					&cli.StringFlag{
						Name:    "endpoint",
						Aliases: []string{"e"},
						Usage:   "Filter by endpoint",
					},
				},
				Action: showUsage,
			},
			{
				Name:   "billing",
				Usage:  "Show billing information",
				Action: showBilling,
			},
		},
	}

	err := app.Run(os.Args)
	if err != nil {
		log.Fatal(err)
	}
}

func showDashboard(c *cli.Context) error {
	resp, err := http.Get(baseURL + "/dashboard")
	if err != nil {
		return fmt.Errorf("failed to fetch dashboard: %v", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return fmt.Errorf("failed to fetch dashboard: %s", resp.Status)
	}

	var dashboard Dashboard
	if err := json.NewDecoder(resp.Body).Decode(&dashboard); err != nil {
		return fmt.Errorf("failed to decode dashboard: %v", err)
	}

	fmt.Println("=== Data Vendor Dashboard ===")
	fmt.Printf("Active API Keys: %d\n", dashboard.ActiveKeys)
	fmt.Printf("Today's Requests: %d\n", dashboard.TodayRequests)
	fmt.Printf("Monthly Revenue: $%.2f\n", dashboard.MonthlyRevenue)
	fmt.Printf("Rate Limit Hits: %d\n", dashboard.RateLimitHits)
	fmt.Println()

	return nil
}

func listAPIKeys(c *cli.Context) error {
	resp, err := http.Get(baseURL + "/keys")
	if err != nil {
		return fmt.Errorf("failed to fetch API keys: %v", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return fmt.Errorf("failed to fetch API keys: %s", resp.Status)
	}

	var keys []APIKey
	if err := json.NewDecoder(resp.Body).Decode(&keys); err != nil {
		return fmt.Errorf("failed to decode API keys: %v", err)
	}

	fmt.Println("=== API Keys ===")
	fmt.Printf("%-5s %-20s %-30s %-10s %-8s %-8s %-12s\n", "ID", "Vendor", "Email", "Level", "Rate", "Status", "Expires")
	fmt.Println(string(make([]byte, 100, 100)))
	for _, key := range keys {
		status := "Active"
		if !key.IsActive {
			status = "Inactive"
		}
		fmt.Printf("%-5d %-20s %-30s %-10s %-8d %-8s %-12s\n",
			key.ID,
			truncateString(key.VendorName, 18),
			truncateString(key.Email, 28),
			key.AccessLevel,
			key.RateLimit,
			status,
			key.ExpiresAt.Format("2006-01-02"))
	}
	fmt.Println()

	return nil
}

func createAPIKey(c *cli.Context) error {
	vendor := c.String("vendor")
	email := c.String("email")
	level := c.String("level")
	rateLimit := c.Int("rate-limit")
	expiresStr := c.String("expires")

	// Parse expiration date
	expires, err := time.Parse("2006-01-02", expiresStr)
	if err != nil {
		return fmt.Errorf("invalid expiration date: %v", err)
	}

	// Validate access level
	validLevels := map[string]bool{"basic": true, "premium": true, "enterprise": true}
	if !validLevels[level] {
		return fmt.Errorf("invalid access level: %s (must be basic, premium, or enterprise)", level)
	}

	// Create request body
	requestBody := map[string]interface{}{
		"vendor_name":  vendor,
		"email":        email,
		"access_level": level,
		"rate_limit":   rateLimit,
		"expires_at":   expires.Format(time.RFC3339),
	}

	body, err := json.Marshal(requestBody)
	if err != nil {
		return fmt.Errorf("failed to marshal request: %v", err)
	}

	// Make request
	resp, err := http.Post(baseURL+"/keys", "application/json", bytes.NewBuffer(body))
	if err != nil {
		return fmt.Errorf("failed to create API key: %v", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusCreated {
		return fmt.Errorf("failed to create API key: %s", resp.Status)
	}

	var key APIKey
	if err := json.NewDecoder(resp.Body).Decode(&key); err != nil {
		return fmt.Errorf("failed to decode response: %v", err)
	}

	fmt.Println("=== API Key Created ===")
	fmt.Printf("ID: %d\n", key.ID)
	fmt.Printf("Vendor: %s\n", key.VendorName)
	fmt.Printf("Email: %s\n", key.Email)
	fmt.Printf("Access Level: %s\n", key.AccessLevel)
	fmt.Printf("Rate Limit: %d/hour\n", key.RateLimit)
	fmt.Printf("API Key: %s\n", key.Key)
	fmt.Printf("Expires: %s\n", key.ExpiresAt.Format("2006-01-02"))
	fmt.Println()

	return nil
}

func showAPIKey(c *cli.Context) error {
	id := c.Uint("id")

	resp, err := http.Get(fmt.Sprintf("%s/keys/%d", baseURL, id))
	if err != nil {
		return fmt.Errorf("failed to fetch API key: %v", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return fmt.Errorf("failed to fetch API key: %s", resp.Status)
	}

	var response map[string]interface{}
	if err := json.NewDecoder(resp.Body).Decode(&response); err != nil {
		return fmt.Errorf("failed to decode response: %v", err)
	}

	keyData := response["key"].(map[string]interface{})
	statsData := response["stats"].(map[string]interface{})

	fmt.Println("=== API Key Details ===")
	fmt.Printf("ID: %v\n", keyData["id"])
	fmt.Printf("Vendor: %v\n", keyData["vendor_name"])
	fmt.Printf("Email: %v\n", keyData["email"])
	fmt.Printf("Access Level: %v\n", keyData["access_level"])
	fmt.Printf("Rate Limit: %v/hour\n", keyData["rate_limit"])
	fmt.Printf("Status: %v\n", keyData["is_active"])
	fmt.Printf("API Key: %v\n", keyData["key"])
	fmt.Printf("Expires: %v\n", keyData["expires_at"])
	fmt.Printf("Created: %v\n", keyData["created_at"])
	fmt.Println()
	fmt.Println("=== Usage Statistics ===")
	fmt.Printf("Total Requests: %v\n", statsData["total_requests"])
	fmt.Printf("Last Used: %v\n", statsData["last_used"])
	fmt.Printf("Rate Limit Hits: %v\n", statsData["rate_limit_hits"])
	fmt.Println()

	return nil
}

func activateAPIKey(c *cli.Context) error {
	return updateAPIKeyStatus(c, true)
}

func deactivateAPIKey(c *cli.Context) error {
	return updateAPIKeyStatus(c, false)
}

func updateAPIKeyStatus(c *cli.Context, isActive bool) error {
	id := c.Uint("id")

	requestBody := map[string]interface{}{
		"is_active": isActive,
	}

	body, err := json.Marshal(requestBody)
	if err != nil {
		return fmt.Errorf("failed to marshal request: %v", err)
	}

	req, err := http.NewRequest("PATCH", fmt.Sprintf("%s/keys/%d/status", baseURL, id), bytes.NewBuffer(body))
	if err != nil {
		return fmt.Errorf("failed to create request: %v", err)
	}
	req.Header.Set("Content-Type", "application/json")

	client := &http.Client{}
	resp, err := client.Do(req)
	if err != nil {
		return fmt.Errorf("failed to update API key status: %v", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return fmt.Errorf("failed to update API key status: %s", resp.Status)
	}

	var response map[string]interface{}
	if err := json.NewDecoder(resp.Body).Decode(&response); err != nil {
		return fmt.Errorf("failed to decode response: %v", err)
	}

	status := "activated"
	if !isActive {
		status = "deactivated"
	}

	fmt.Printf("API key %d %s successfully\n", id, status)
	return nil
}

func showUsage(c *cli.Context) error {
	days := c.String("days")
	vendor := c.String("vendor")
	endpoint := c.String("endpoint")

	url := fmt.Sprintf("%s/usage?date_range=%s", baseURL, days)
	if vendor != "" {
		url += "&vendor=" + vendor
	}
	if endpoint != "" {
		url += "&endpoint=" + endpoint
	}

	resp, err := http.Get(url)
	if err != nil {
		return fmt.Errorf("failed to fetch usage data: %v", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return fmt.Errorf("failed to fetch usage data: %s", resp.Status)
	}

	var response map[string]interface{}
	if err := json.NewDecoder(resp.Body).Decode(&response); err != nil {
		return fmt.Errorf("failed to decode response: %v", err)
	}

	stats := response["stats"].(map[string]interface{})
	usage := response["usage"].([]interface{})

	fmt.Println("=== Usage Statistics ===")
	fmt.Printf("Total Requests: %.0f\n", stats["total_requests"])
	fmt.Printf("Success Rate: %.1f%%\n", stats["success_rate"])
	fmt.Printf("Average Response Time: %.0fms\n", stats["avg_response_time"])
	fmt.Println()

	if len(usage) > 0 {
		fmt.Println("=== Recent Usage ===")
		fmt.Printf("%-20s %-30s %-10s %-8s %-8s %-15s\n", "Timestamp", "Vendor", "Endpoint", "Method", "Status", "Response Time")
		fmt.Println(string(make([]byte, 100, 100)))

		for i, usageItem := range usage {
			if i >= 10 { // Show only first 10 records
				break
			}
			item := usageItem.(map[string]interface{})
			fmt.Printf("%-20s %-30s %-10s %-8s %-8s %-15s\n",
				formatTime(item["created_at"].(string)),
				truncateString(item["vendor_name"].(string), 28),
				truncateString(item["endpoint"].(string), 8),
				item["method"],
				fmt.Sprintf("%.0f", item["status"]),
				fmt.Sprintf("%.0fms", item["response_time"]))
		}
		fmt.Println()
	}

	return nil
}

func showBilling(c *cli.Context) error {
	resp, err := http.Get(baseURL + "/billing")
	if err != nil {
		return fmt.Errorf("failed to fetch billing data: %v", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return fmt.Errorf("failed to fetch billing data: %s", resp.Status)
	}

	var response map[string]interface{}
	if err := json.NewDecoder(resp.Body).Decode(&response); err != nil {
		return fmt.Errorf("failed to decode response: %v", err)
	}

	fmt.Println("=== Billing Overview ===")
	fmt.Printf("Monthly Revenue: $%.2f\n", response["month_revenue"])
	fmt.Printf("Total Vendors: %.0f\n", response["total_vendors"])
	fmt.Printf("Average Revenue per Vendor: $%.2f\n", response["avg_revenue_per_vendor"])
	fmt.Printf("Active Subscriptions: %.0f\n", response["active_subscriptions"])
	fmt.Println()

	billing := response["billing"].([]interface{})
	if len(billing) > 0 {
		fmt.Println("=== Vendor Billing ===")
		fmt.Printf("%-20s %-10s %-12s %-15s %-15s %-12s %-10s\n", "Vendor", "Plan", "Monthly Rate", "Usage", "Overage", "Total Due", "Status")
		fmt.Println(string(make([]byte, 100, 100)))

		for _, billingItem := range billing {
			item := billingItem.(map[string]interface{})
			fmt.Printf("%-20s %-10s %-12s %-15s %-15s %-12s %-10s\n",
				truncateString(item["vendor_name"].(string), 18),
				item["plan"],
				fmt.Sprintf("$%.0f", item["monthly_rate"]),
				fmt.Sprintf("%.0f", item["usage_this_month"]),
				fmt.Sprintf("$%.2f", item["overage_charges"]),
				fmt.Sprintf("$%.2f", item["total_due"]),
				item["status"])
		}
		fmt.Println()
	}

	return nil
}

// Helper functions
func truncateString(s string, maxLen int) string {
	if len(s) <= maxLen {
		return s
	}
	return s[:maxLen-3] + "..."
}

func formatTime(timeStr string) string {
	t, err := time.Parse(time.RFC3339, timeStr)
	if err != nil {
		return timeStr
	}
	return t.Format("2006-01-02 15:04")
}
