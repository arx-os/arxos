package cache

import (
	"fmt"
	"os"
	"strings"
	"time"

	"github.com/spf13/cobra"
)

// PerformanceCLI provides command-line interface for performance management
type PerformanceCLI struct {
	manager *PerformanceManager
}

// NewPerformanceCLI creates a new performance CLI
func NewPerformanceCLI(manager *PerformanceManager) *PerformanceCLI {
	return &PerformanceCLI{
		manager: manager,
	}
}

// GetCommands returns performance CLI commands
func (cli *PerformanceCLI) GetCommands() []*cobra.Command {
	return []*cobra.Command{
		cli.getMetricsCommand(),
		cli.getReportCommand(),
		cli.getModulesCommand(),
		cli.getAlertsCommand(),
		cli.getOptimizeCommand(),
		cli.getCacheCommand(),
		cli.getPoolCommand(),
		cli.getMonitorCommand(),
	}
}

// getMetricsCommand returns metrics command
func (cli *PerformanceCLI) getMetricsCommand() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "metrics [metric-name]",
		Short: "Show performance metrics",
		Long:  "Display performance metrics for the system or a specific metric",
		Args:  cobra.MaximumNArgs(1),
		Run: func(cmd *cobra.Command, args []string) {
			metricName := ""
			if len(args) > 0 {
				metricName = args[0]
			}

			limit, _ := cmd.Flags().GetInt("limit")

			if metricName != "" {
				metrics := cli.manager.GetPerformanceMonitor().GetMetrics(metricName, limit)
				cli.displayMetrics(metrics)
			} else {
				systemMetrics := cli.manager.GetPerformanceMonitor().GetSystemMetrics()
				cli.displaySystemMetrics(systemMetrics)
			}
		},
	}

	cmd.Flags().IntP("limit", "l", 100, "Limit number of metrics to display")
	return cmd
}

// getReportCommand returns report command
func (cli *PerformanceCLI) getReportCommand() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "report",
		Short: "Generate performance report",
		Long:  "Generate a comprehensive performance report with recommendations",
		Run: func(cmd *cobra.Command, args []string) {
			report := cli.manager.GeneratePerformanceReport()
			cli.displayReport(report)
		},
	}

	cmd.Flags().BoolP("json", "j", false, "Output in JSON format")
	return cmd
}

// getModulesCommand returns modules command
func (cli *PerformanceCLI) getModulesCommand() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "modules [module-name]",
		Short: "Show module performance",
		Long:  "Display performance metrics for modules",
		Args:  cobra.MaximumNArgs(1),
		Run: func(cmd *cobra.Command, args []string) {
			if len(args) > 0 {
				moduleName := args[0]
				module, exists := cli.manager.GetModulePerformance(moduleName)
				if !exists {
					fmt.Printf("Module '%s' not found\n", moduleName)
					return
				}
				cli.displayModule(module)
			} else {
				modules := cli.manager.GetAllModulePerformance()
				cli.displayModules(modules)
			}
		},
	}

	return cmd
}

// getAlertsCommand returns alerts command
func (cli *PerformanceCLI) getAlertsCommand() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "alerts",
		Short: "Show performance alerts",
		Long:  "Display active performance alerts",
		Run: func(cmd *cobra.Command, args []string) {
			resolved, _ := cmd.Flags().GetBool("resolved")
			alerts := cli.manager.GetPerformanceMonitor().GetAlerts(resolved)
			cli.displayAlerts(alerts)
		},
	}

	cmd.Flags().BoolP("resolved", "r", false, "Show resolved alerts")
	return cmd
}

// getOptimizeCommand returns optimize command
func (cli *PerformanceCLI) getOptimizeCommand() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "optimize <module-name>",
		Short: "Optimize module performance",
		Long:  "Generate optimization recommendations for a specific module",
		Args:  cobra.ExactArgs(1),
		Run: func(cmd *cobra.Command, args []string) {
			moduleName := args[0]
			err := cli.manager.OptimizeModule(moduleName)
			if err != nil {
				fmt.Printf("Error optimizing module '%s': %v\n", moduleName, err)
				return
			}
			fmt.Printf("Module '%s' optimization completed\n", moduleName)
		},
	}

	return cmd
}

// getCacheCommand returns cache command
func (cli *PerformanceCLI) getCacheCommand() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "cache",
		Short: "Show cache statistics",
		Long:  "Display cache performance statistics",
		Run: func(cmd *cobra.Command, args []string) {
			if cli.manager.GetCache() == nil {
				fmt.Println("Cache not available")
				return
			}

			metrics := cli.manager.GetCache().GetMetrics()
			cli.displayCacheMetrics(metrics)
		},
	}

	return cmd
}

// getPoolCommand returns pool command
func (cli *PerformanceCLI) getPoolCommand() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "pool",
		Short: "Show resource pool statistics",
		Long:  "Display resource pool performance statistics",
		Run: func(cmd *cobra.Command, args []string) {
			if cli.manager.GetResourcePool() == nil {
				fmt.Println("Resource pool not available")
				return
			}

			metrics := cli.manager.GetResourcePool().GetMetrics()
			cli.displayPoolMetrics(metrics)
		},
	}

	return cmd
}

// getMonitorCommand returns monitor command
func (cli *PerformanceCLI) getMonitorCommand() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "monitor",
		Short: "Start performance monitoring",
		Long:  "Start real-time performance monitoring",
		Run: func(cmd *cobra.Command, args []string) {
			interval, _ := cmd.Flags().GetDuration("interval")
			cli.startMonitoring(interval)
		},
	}

	cmd.Flags().DurationP("interval", "i", 5*time.Second, "Monitoring interval")
	return cmd
}

// Display methods

func (cli *PerformanceCLI) displayMetrics(metrics []PerformanceMetric) {
	if len(metrics) == 0 {
		fmt.Println("No metrics found")
		return
	}

	fmt.Printf("%-20s %-10s %-15s %-20s %s\n", "NAME", "VALUE", "UNIT", "TIMESTAMP", "TAGS")
	fmt.Println(strings.Repeat("-", 80))

	for _, metric := range metrics {
		tags := ""
		if len(metric.Tags) > 0 {
			var tagPairs []string
			for k, v := range metric.Tags {
				tagPairs = append(tagPairs, fmt.Sprintf("%s=%s", k, v))
			}
			tags = strings.Join(tagPairs, ",")
		}

		fmt.Printf("%-20s %-10.2f %-15s %-20s %s\n",
			metric.Name, metric.Value, metric.Unit,
			metric.Timestamp.Format("2006-01-02 15:04:05"), tags)
	}
}

func (cli *PerformanceCLI) displaySystemMetrics(metrics *SystemMetrics) {
	fmt.Println("System Performance Metrics:")
	fmt.Println("==========================")
	fmt.Printf("CPU Usage:        %.2f%%\n", metrics.CPUUsage)
	fmt.Printf("Memory Usage:     %d MB\n", metrics.MemoryUsage)
	fmt.Printf("Goroutine Count:  %d\n", metrics.GoroutineCount)
	fmt.Printf("Heap Size:        %d MB\n", metrics.HeapSize)
	fmt.Printf("GC Count:         %d\n", metrics.GCCount)
	fmt.Printf("Last GC:          %s\n", metrics.LastGC.Format("2006-01-02 15:04:05"))
	fmt.Printf("Uptime:           %s\n", metrics.Uptime)
}

func (cli *PerformanceCLI) displayReport(report *PerformanceReport) {
	fmt.Println("Performance Report")
	fmt.Println("==================")
	fmt.Printf("Generated: %s\n\n", report.GeneratedAt.Format("2006-01-02 15:04:05"))

	// System metrics
	if report.SystemMetrics != nil {
		fmt.Println("System Metrics:")
		cli.displaySystemMetrics(report.SystemMetrics)
		fmt.Println()
	}

	// Module metrics
	if len(report.ModuleMetrics) > 0 {
		fmt.Println("Module Performance:")
		cli.displayModules(report.ModuleMetrics)
		fmt.Println()
	}

	// Alerts
	if len(report.Alerts) > 0 {
		fmt.Println("Active Alerts:")
		cli.displayAlerts(report.Alerts)
		fmt.Println()
	}

	// Recommendations
	if len(report.Recommendations) > 0 {
		fmt.Println("Recommendations:")
		for i, rec := range report.Recommendations {
			fmt.Printf("%d. %s\n", i+1, rec)
		}
	}
}

func (cli *PerformanceCLI) displayModules(modules map[string]ModulePerformance) {
	if len(modules) == 0 {
		fmt.Println("No module data available")
		return
	}

	fmt.Printf("%-20s %-10s %-15s %-10s %-10s %-10s %s\n",
		"MODULE", "REQUESTS", "AVG TIME", "ERRORS", "CACHE HITS", "CACHE MISSES", "LAST UPDATED")
	fmt.Println(strings.Repeat("-", 90))

	for name, module := range modules {
		fmt.Printf("%-20s %-10d %-15s %-10d %-10d %-10d %s\n",
			name, module.RequestCount, module.AverageTime,
			module.ErrorCount, module.CacheHits, module.CacheMisses,
			module.LastUpdated.Format("15:04:05"))
	}
}

func (cli *PerformanceCLI) displayModule(module ModulePerformance) {
	fmt.Printf("Module: %s\n", module.ModuleName)
	fmt.Println("================")
	fmt.Printf("Request Count:   %d\n", module.RequestCount)
	fmt.Printf("Average Time:    %s\n", module.AverageTime)
	fmt.Printf("Error Count:     %d\n", module.ErrorCount)
	fmt.Printf("Cache Hits:      %d\n", module.CacheHits)
	fmt.Printf("Cache Misses:    %d\n", module.CacheMisses)
	fmt.Printf("Last Updated:    %s\n", module.LastUpdated.Format("2006-01-02 15:04:05"))

	if module.RequestCount > 0 {
		errorRate := float64(module.ErrorCount) / float64(module.RequestCount) * 100
		fmt.Printf("Error Rate:      %.2f%%\n", errorRate)
	}

	totalCacheOps := module.CacheHits + module.CacheMisses
	if totalCacheOps > 0 {
		hitRate := float64(module.CacheHits) / float64(totalCacheOps) * 100
		fmt.Printf("Cache Hit Rate:  %.2f%%\n", hitRate)
	}
}

func (cli *PerformanceCLI) displayAlerts(alerts []*PerformanceAlert) {
	if len(alerts) == 0 {
		fmt.Println("No alerts found")
		return
	}

	fmt.Printf("%-20s %-10s %-50s %-10s %-10s %s\n",
		"ID", "SEVERITY", "MESSAGE", "THRESHOLD", "CURRENT", "TIMESTAMP")
	fmt.Println(strings.Repeat("-", 100))

	for _, alert := range alerts {
		fmt.Printf("%-20s %-10s %-50s %-10.2f %-10.2f %s\n",
			alert.ID, alert.Severity, alert.Message,
			alert.Threshold, alert.CurrentValue,
			alert.Timestamp.Format("15:04:05"))
	}
}

func (cli *PerformanceCLI) displayCacheMetrics(metrics *CacheMetrics) {
	fmt.Println("Cache Performance Metrics:")
	fmt.Println("==========================")
	fmt.Printf("Hits:            %d\n", metrics.Hits)
	fmt.Printf("Misses:          %d\n", metrics.Misses)
	fmt.Printf("Evictions:       %d\n", metrics.Evictions)
	fmt.Printf("Total Size:      %d bytes\n", metrics.TotalSize)
	fmt.Printf("Entry Count:     %d\n", metrics.EntryCount)
	fmt.Printf("Hit Rate:        %.2f%%\n", metrics.HitRate*100)
	fmt.Printf("Avg Access Time: %s\n", metrics.AverageAccessTime)
}

func (cli *PerformanceCLI) displayPoolMetrics(metrics *PoolMetrics) {
	fmt.Println("Resource Pool Metrics:")
	fmt.Println("======================")
	fmt.Printf("Total Resources:  %d\n", metrics.TotalResources)
	fmt.Printf("Active Resources: %d\n", metrics.ActiveResources)
	fmt.Printf("Idle Resources:   %d\n", metrics.IdleResources)
	fmt.Printf("Memory Usage:     %d MB\n", metrics.MemoryUsageMB)
	fmt.Printf("Request Count:    %d\n", metrics.RequestCount)
	fmt.Printf("Avg Wait Time:    %s\n", metrics.WaitTime)
	fmt.Printf("Utilization Rate: %.2f%%\n", metrics.UtilizationRate*100)
	fmt.Printf("Error Count:      %d\n", metrics.ErrorCount)
}

func (cli *PerformanceCLI) startMonitoring(interval time.Duration) {
	fmt.Printf("Starting performance monitoring (interval: %s)\n", interval)
	fmt.Println("Press Ctrl+C to stop")
	fmt.Println()

	ticker := time.NewTicker(interval)
	defer ticker.Stop()

	for {
		select {
		case <-ticker.C:
			// Clear screen (ANSI escape sequence)
			fmt.Print("\033[2J\033[H")

			// Display current metrics
			systemMetrics := cli.manager.GetPerformanceMonitor().GetSystemMetrics()
			cli.displaySystemMetrics(systemMetrics)

			// Display active alerts
			alerts := cli.manager.GetPerformanceMonitor().GetAlerts(false)
			if len(alerts) > 0 {
				fmt.Println("\nActive Alerts:")
				cli.displayAlerts(alerts)
			}

		case <-interruptChan():
			fmt.Println("\nMonitoring stopped")
			return
		}
	}
}

// interruptChan returns a channel that receives on interrupt
func interruptChan() <-chan os.Signal {
	c := make(chan os.Signal, 1)
	// In a real implementation, this would use signal.Notify
	// For now, we'll just return a channel that never receives
	return c
}
