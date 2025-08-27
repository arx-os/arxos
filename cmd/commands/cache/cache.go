package cache

import (
	"encoding/json"
	"fmt"
	"log"
	"os"
	"text/tabwriter"
	"time"

	// "github.com/arxos/arxos/core/internal/db"
	// "github.com/arxos/arxos/core/internal/services"
	// "github.com/arxos/arxos/core/internal/services/cache"
	"github.com/fatih/color"
	"gorm.io/gorm"
)

// CacheCommand represents cache management commands
type CacheCommand struct {
	db *gorm.DB
}

// NewCacheCommand creates a new cache command handler
func NewCacheCommand() *CacheCommand {
	return &CacheCommand{}
}

// Execute runs the cache command with given action
func (c *CacheCommand) Execute(action string, args []string) error {
	// Initialize database connection
	if err := db.InitDB(); err != nil {
		return fmt.Errorf("failed to connect to database: %w", err)
	}
	defer db.Close()
	
	c.db = db.GormDB

	switch action {
	case "stats":
		return c.showStats()
	case "clear":
		if len(args) > 0 {
			return c.clearPattern(args[0])
		}
		return c.clearExpired()
	case "clear-all":
		return c.clearAll()
	case "get":
		if len(args) == 0 {
			return fmt.Errorf("key required for get command")
		}
		return c.getEntry(args[0])
	case "set":
		if len(args) < 2 {
			return fmt.Errorf("key and value required for set command")
		}
		ttl := 5 * time.Minute
		if len(args) > 2 {
			duration, err := time.ParseDuration(args[2])
			if err == nil {
				ttl = duration
			}
		}
		return c.setEntry(args[0], args[1], ttl)
	case "list":
		limit := 20
		if len(args) > 0 {
			fmt.Sscanf(args[0], "%d", &limit)
		}
		return c.listEntries(limit)
	case "benchmark":
		return c.runBenchmark()
	case "help":
		c.showHelp()
		return nil
	default:
		return fmt.Errorf("unknown cache command: %s", action)
	}
}

// showStats displays cache statistics
func (c *CacheCommand) showStats() error {
	fmt.Println(color.CyanString("📊 Cache Statistics"))
	fmt.Println(color.CyanString("=================="))

	// Get overall stats
	var stats struct {
		TotalEntries   int64
		ExpiredEntries int64
		TotalSize      int64
		AvgAccessCount float64
		CacheTypes     []struct {
			CacheType string `gorm:"column:cache_type"`
			Count     int64  `gorm:"column:count"`
		}
	}

	// Total entries and stats
	c.db.Raw(`
		SELECT 
			COUNT(*) as total_entries,
			COUNT(CASE WHEN expires_at < CURRENT_TIMESTAMP THEN 1 END) as expired_entries,
			SUM(pg_column_size(cache_value)) as total_size,
			AVG(access_count) as avg_access_count
		FROM cache_entries
	`).Scan(&stats)

	// Cache types breakdown
	c.db.Raw(`
		SELECT cache_type, COUNT(*) as count
		FROM cache_entries
		GROUP BY cache_type
		ORDER BY count DESC
	`).Scan(&stats.CacheTypes)

	// Display general stats
	fmt.Printf("Total Entries:    %s\n", color.YellowString("%d", stats.TotalEntries))
	fmt.Printf("Expired Entries:  %s\n", color.RedString("%d", stats.ExpiredEntries))
	fmt.Printf("Active Entries:   %s\n", color.GreenString("%d", stats.TotalEntries-stats.ExpiredEntries))
	fmt.Printf("Total Size:       %s\n", color.YellowString("%s", formatBytes(stats.TotalSize)))
	fmt.Printf("Avg Access Count: %s\n", color.YellowString("%.2f", stats.AvgAccessCount))

	// Display cache types
	if len(stats.CacheTypes) > 0 {
		fmt.Println("\n" + color.CyanString("Cache Types:"))
		w := tabwriter.NewWriter(os.Stdout, 0, 0, 2, ' ', 0)
		fmt.Fprintln(w, "Type\tCount")
		fmt.Fprintln(w, "----\t-----")
		for _, ct := range stats.CacheTypes {
			fmt.Fprintf(w, "%s\t%d\n", ct.CacheType, ct.Count)
		}
		w.Flush()
	}

	// Top accessed keys
	var topKeys []struct {
		CacheKey    string `gorm:"column:cache_key"`
		AccessCount int64  `gorm:"column:access_count"`
	}
	c.db.Raw(`
		SELECT cache_key, access_count
		FROM cache_entries
		WHERE expires_at > CURRENT_TIMESTAMP
		ORDER BY access_count DESC
		LIMIT 10
	`).Scan(&topKeys)

	if len(topKeys) > 0 {
		fmt.Println("\n" + color.CyanString("Top Accessed Keys:"))
		w := tabwriter.NewWriter(os.Stdout, 0, 0, 2, ' ', 0)
		fmt.Fprintln(w, "Key\tAccess Count")
		fmt.Fprintln(w, "---\t------------")
		for _, key := range topKeys {
			displayKey := key.CacheKey
			if len(displayKey) > 50 {
				displayKey = displayKey[:47] + "..."
			}
			fmt.Fprintf(w, "%s\t%d\n", displayKey, key.AccessCount)
		}
		w.Flush()
	}

	return nil
}

// clearExpired removes expired cache entries
func (c *CacheCommand) clearExpired() error {
	fmt.Println(color.YellowString("🧹 Clearing expired cache entries..."))
	
	if err := services.CleanupExpiredCache(); err != nil {
		return fmt.Errorf("failed to clear expired entries: %w", err)
	}
	
	fmt.Println(color.GreenString("✅ Expired cache entries cleared"))
	return nil
}

// clearPattern removes cache entries matching a pattern
func (c *CacheCommand) clearPattern(pattern string) error {
	fmt.Printf(color.YellowString("🧹 Clearing cache entries matching pattern: %s\n"), pattern)
	
	sqlPattern := "%" + pattern + "%"
	result := c.db.Exec("DELETE FROM cache_entries WHERE cache_key LIKE ?", sqlPattern)
	if result.Error != nil {
		return fmt.Errorf("failed to clear pattern: %w", result.Error)
	}
	
	fmt.Printf(color.GreenString("✅ Cleared %d entries\n"), result.RowsAffected)
	return nil
}

// clearAll removes all cache entries
func (c *CacheCommand) clearAll() error {
	fmt.Print(color.RedString("⚠️  This will clear ALL cache entries. Continue? (y/n): "))
	var confirm string
	fmt.Scanln(&confirm)
	
	if confirm != "y" && confirm != "yes" {
		fmt.Println("Cancelled")
		return nil
	}
	
	fmt.Println(color.YellowString("🧹 Clearing all cache entries..."))
	
	result := c.db.Exec("TRUNCATE TABLE cache_entries, http_cache, confidence_cache")
	if result.Error != nil {
		return fmt.Errorf("failed to clear all entries: %w", result.Error)
	}
	
	fmt.Println(color.GreenString("✅ All cache entries cleared"))
	return nil
}

// getEntry retrieves a cache entry
func (c *CacheCommand) getEntry(key string) error {
	// Initialize cache service
	cacheService, err := cache.NewCacheService(nil, log.Default())
	if err != nil {
		return fmt.Errorf("failed to initialize cache service: %w", err)
	}
	defer cacheService.Close()

	value, err := cacheService.Get(key)
	if err != nil {
		return fmt.Errorf("failed to get entry: %w", err)
	}
	
	if value == nil {
		fmt.Printf(color.RedString("❌ Key not found: %s\n"), key)
		return nil
	}
	
	ttl, _ := cacheService.TTL(key)
	exists, _ := cacheService.Exists(key)
	
	fmt.Printf(color.CyanString("📦 Cache Entry: %s\n"), key)
	fmt.Printf("Exists: %s\n", formatBool(exists))
	fmt.Printf("TTL:    %s\n", color.YellowString("%v", ttl))
	fmt.Printf("Value:  %s\n", formatValue(value))
	
	return nil
}

// setEntry sets a cache entry
func (c *CacheCommand) setEntry(key, value string, ttl time.Duration) error {
	// Initialize cache service
	cacheService, err := cache.NewCacheService(nil, log.Default())
	if err != nil {
		return fmt.Errorf("failed to initialize cache service: %w", err)
	}
	defer cacheService.Close()

	if err := cacheService.Set(key, value, ttl); err != nil {
		return fmt.Errorf("failed to set entry: %w", err)
	}
	
	fmt.Printf(color.GreenString("✅ Set cache entry: %s (TTL: %v)\n"), key, ttl)
	return nil
}

// listEntries lists cache entries
func (c *CacheCommand) listEntries(limit int) error {
	fmt.Printf(color.CyanString("📋 Cache Entries (limit: %d)\n"), limit)
	fmt.Println(color.CyanString("=========================="))
	
	var entries []struct {
		CacheKey       string    `gorm:"column:cache_key"`
		CacheType      string    `gorm:"column:cache_type"`
		ExpiresAt      time.Time `gorm:"column:expires_at"`
		AccessCount    int64     `gorm:"column:access_count"`
		LastAccessedAt time.Time `gorm:"column:last_accessed_at"`
	}
	
	c.db.Raw(`
		SELECT cache_key, cache_type, expires_at, access_count, last_accessed_at
		FROM cache_entries
		ORDER BY last_accessed_at DESC
		LIMIT ?
	`, limit).Scan(&entries)
	
	if len(entries) == 0 {
		fmt.Println("No cache entries found")
		return nil
	}
	
	w := tabwriter.NewWriter(os.Stdout, 0, 0, 2, ' ', 0)
	fmt.Fprintln(w, "Key\tType\tExpires\tAccess Count\tLast Access")
	fmt.Fprintln(w, "---\t----\t-------\t------------\t-----------")
	
	for _, entry := range entries {
		displayKey := entry.CacheKey
		if len(displayKey) > 40 {
			displayKey = displayKey[:37] + "..."
		}
		
		expiresIn := time.Until(entry.ExpiresAt)
		expireStr := formatDuration(expiresIn)
		if expiresIn < 0 {
			expireStr = color.RedString("expired")
		}
		
		fmt.Fprintf(w, "%s\t%s\t%s\t%d\t%s\n",
			displayKey,
			entry.CacheType,
			expireStr,
			entry.AccessCount,
			formatTime(entry.LastAccessedAt),
		)
	}
	w.Flush()
	
	return nil
}

// runBenchmark runs cache performance benchmark
func (c *CacheCommand) runBenchmark() error {
	fmt.Println(color.CyanString("🚀 Running Cache Benchmark..."))
	fmt.Println(color.CyanString("============================="))
	
	// Initialize cache service
	cacheService, err := cache.NewCacheService(nil, nil)
	if err != nil {
		return fmt.Errorf("failed to initialize cache service: %w", err)
	}
	defer cacheService.Close()
	
	// Benchmark configuration
	iterations := 1000
	keyPrefix := "bench_"
	
	// SET benchmark
	fmt.Printf("\n%s\n", color.YellowString("SET Operations:"))
	start := time.Now()
	for i := 0; i < iterations; i++ {
		key := fmt.Sprintf("%s%d", keyPrefix, i)
		value := fmt.Sprintf("value_%d", i)
		if err := cacheService.Set(key, value, 1*time.Hour); err != nil {
			return fmt.Errorf("SET failed: %w", err)
		}
	}
	setDuration := time.Since(start)
	setOpsPerSec := float64(iterations) / setDuration.Seconds()
	fmt.Printf("  Total time:     %v\n", setDuration)
	fmt.Printf("  Ops/sec:        %s\n", color.GreenString("%.0f", setOpsPerSec))
	fmt.Printf("  Avg latency:    %s\n", color.GreenString("%.2fms", float64(setDuration.Milliseconds())/float64(iterations)))
	
	// GET benchmark
	fmt.Printf("\n%s\n", color.YellowString("GET Operations:"))
	start = time.Now()
	hits := 0
	for i := 0; i < iterations; i++ {
		key := fmt.Sprintf("%s%d", keyPrefix, i)
		if value, _ := cacheService.Get(key); value != nil {
			hits++
		}
	}
	getDuration := time.Since(start)
	getOpsPerSec := float64(iterations) / getDuration.Seconds()
	hitRate := float64(hits) / float64(iterations) * 100
	fmt.Printf("  Total time:     %v\n", getDuration)
	fmt.Printf("  Ops/sec:        %s\n", color.GreenString("%.0f", getOpsPerSec))
	fmt.Printf("  Avg latency:    %s\n", color.GreenString("%.2fms", float64(getDuration.Milliseconds())/float64(iterations)))
	fmt.Printf("  Hit rate:       %s\n", color.GreenString("%.1f%%", hitRate))
	
	// Clean up
	fmt.Printf("\n%s\n", color.YellowString("Cleaning up..."))
	for i := 0; i < iterations; i++ {
		key := fmt.Sprintf("%s%d", keyPrefix, i)
		cacheService.Delete(key)
	}
	
	fmt.Printf("\n%s\n", color.GreenString("✅ Benchmark complete!"))
	
	return nil
}

// showHelp displays help information
func (c *CacheCommand) showHelp() {
	fmt.Println(color.CyanString("ARXOS Cache Management"))
	fmt.Println(color.CyanString("======================"))
	fmt.Println()
	fmt.Println("Commands:")
	fmt.Println("  stats              Show cache statistics")
	fmt.Println("  clear              Clear expired entries")
	fmt.Println("  clear <pattern>    Clear entries matching pattern")
	fmt.Println("  clear-all          Clear all cache entries")
	fmt.Println("  get <key>          Get a cache entry")
	fmt.Println("  set <key> <value> [ttl]  Set a cache entry")
	fmt.Println("  list [limit]       List cache entries")
	fmt.Println("  benchmark          Run performance benchmark")
	fmt.Println("  help               Show this help")
	fmt.Println()
	fmt.Println("Examples:")
	fmt.Println("  arxos cache stats")
	fmt.Println("  arxos cache clear")
	fmt.Println("  arxos cache clear \"user:*\"")
	fmt.Println("  arxos cache get user:123")
	fmt.Println("  arxos cache set test:key \"test value\" 5m")
	fmt.Println("  arxos cache list 50")
	fmt.Println("  arxos cache benchmark")
}

// Helper functions

func formatBytes(bytes int64) string {
	const unit = 1024
	if bytes < unit {
		return fmt.Sprintf("%d B", bytes)
	}
	div, exp := int64(unit), 0
	for n := bytes / unit; n >= unit; n /= unit {
		div *= unit
		exp++
	}
	return fmt.Sprintf("%.1f %cB", float64(bytes)/float64(div), "KMGTPE"[exp])
}

func formatBool(b bool) string {
	if b {
		return color.GreenString("true")
	}
	return color.RedString("false")
}

func formatValue(v interface{}) string {
	switch val := v.(type) {
	case string:
		return val
	case map[string]interface{}, []interface{}:
		data, _ := json.MarshalIndent(val, "", "  ")
		return string(data)
	default:
		return fmt.Sprintf("%v", val)
	}
}

func formatDuration(d time.Duration) string {
	if d < time.Minute {
		return fmt.Sprintf("%.0fs", d.Seconds())
	} else if d < time.Hour {
		return fmt.Sprintf("%.0fm", d.Minutes())
	} else if d < 24*time.Hour {
		return fmt.Sprintf("%.1fh", d.Hours())
	}
	return fmt.Sprintf("%.0fd", d.Hours()/24)
}

func formatTime(t time.Time) string {
	if time.Since(t) < time.Minute {
		return fmt.Sprintf("%.0fs ago", time.Since(t).Seconds())
	} else if time.Since(t) < time.Hour {
		return fmt.Sprintf("%.0fm ago", time.Since(t).Minutes())
	} else if time.Since(t) < 24*time.Hour {
		return fmt.Sprintf("%.0fh ago", time.Since(t).Hours())
	}
	return t.Format("2006-01-02")
}