package main

import (
	"context"
	"encoding/json"
	"fmt"
	"os"
	"strings"
	"time"

	"github.com/arx-os/arxos/internal/hardware/certification"
	"github.com/spf13/cobra"
)

var certifyCmd = &cobra.Command{
	Use:   "certify",
	Short: "Hardware device certification management",
	Long:  `Manage hardware device certification, run tests, and generate reports.`,
}

var certifyRunCmd = &cobra.Command{
	Use:   "run [device-id] [test-id]",
	Short: "Run a certification test on a device",
	Long:  `Run a specific certification test on a hardware device.`,
	Args:  cobra.ExactArgs(2),
	Run:   runCertificationTest,
}

var certifySuiteCmd = &cobra.Command{
	Use:   "suite [device-id] [test-ids...]",
	Short: "Run a test suite on a device",
	Long:  `Run multiple certification tests on a hardware device.`,
	Args:  cobra.MinimumNArgs(2),
	Run:   runCertificationSuite,
}

var certifyListCmd = &cobra.Command{
	Use:   "list",
	Short: "List available certification tests",
	Long:  `List all available certification tests and their details.`,
	Run:   listCertificationTests,
}

var certifyStatusCmd = &cobra.Command{
	Use:   "status [device-id]",
	Short: "Get device certification status",
	Long:  `Get the current certification status for a device.`,
	Args:  cobra.ExactArgs(1),
	Run:   getCertificationStatus,
}

var certifyReportCmd = &cobra.Command{
	Use:   "report [device-id]",
	Short: "Generate certification report",
	Long:  `Generate a comprehensive certification report for a device.`,
	Args:  cobra.ExactArgs(1),
	Run:   generateCertificationReport,
}

var certifyExecCmd = &cobra.Command{
	Use:   "exec [execution-id]",
	Short: "Get test execution status",
	Long:  `Get the status of a running test execution.`,
	Args:  cobra.ExactArgs(1),
	Run:   getExecutionStatus,
}

var certifyCancelCmd = &cobra.Command{
	Use:   "cancel [execution-id]",
	Short: "Cancel a running test execution",
	Long:  `Cancel a currently running test execution.`,
	Args:  cobra.ExactArgs(1),
	Run:   cancelExecution,
}

var certifyMetricsCmd = &cobra.Command{
	Use:   "metrics",
	Short: "Show certification metrics",
	Long:  `Show certification system metrics and statistics.`,
	Run:   showCertificationMetrics,
}

var certifyStandardsCmd = &cobra.Command{
	Use:   "standards",
	Short: "List certification standards",
	Long:  `List all available certification standards.`,
	Run:   listCertificationStandards,
}

func init() {
	rootCmd.AddCommand(certifyCmd)
	certifyCmd.AddCommand(certifyRunCmd)
	certifyCmd.AddCommand(certifySuiteCmd)
	certifyCmd.AddCommand(certifyListCmd)
	certifyCmd.AddCommand(certifyStatusCmd)
	certifyCmd.AddCommand(certifyReportCmd)
	certifyCmd.AddCommand(certifyExecCmd)
	certifyCmd.AddCommand(certifyCancelCmd)
	certifyCmd.AddCommand(certifyMetricsCmd)
	certifyCmd.AddCommand(certifyStandardsCmd)

	// Add flags
	certifyRunCmd.Flags().StringP("config", "c", "", "Test configuration file")
	certifyRunCmd.Flags().DurationP("timeout", "t", 30*time.Minute, "Test timeout")
	certifyRunCmd.Flags().BoolP("wait", "w", false, "Wait for test completion")

	certifySuiteCmd.Flags().StringP("config", "c", "", "Test suite configuration file")
	certifySuiteCmd.Flags().DurationP("timeout", "t", 60*time.Minute, "Test suite timeout")
	certifySuiteCmd.Flags().BoolP("wait", "w", false, "Wait for test suite completion")

	certifyReportCmd.Flags().StringP("format", "f", "json", "Report format (json, html, pdf)")
	certifyReportCmd.Flags().StringP("output", "o", "", "Output file path")
	certifyReportCmd.Flags().BoolP("verbose", "v", false, "Verbose output")
}

func runCertificationTest(cmd *cobra.Command, args []string) {
	deviceID := args[0]
	testID := args[1]

	// Get flags
	configFile, _ := cmd.Flags().GetString("config")
	timeout, _ := cmd.Flags().GetDuration("timeout")
	wait, _ := cmd.Flags().GetBool("wait")

	// Load configuration
	config := make(map[string]interface{})
	if configFile != "" {
		if err := loadConfigFile(configFile, &config); err != nil {
			fmt.Printf("Error loading config file: %v\n", err)
			os.Exit(1)
		}
	}

	// Add timeout to config
	config["timeout"] = int(timeout.Minutes())

	// Create certification manager
	manager := certification.NewCertificationManager()
	runner := certification.NewTestRunner(manager)

	// Run test
	fmt.Printf("Running test %s on device %s...\n", testID, deviceID)
	execution, err := runner.RunTest(context.Background(), deviceID, testID, config)
	if err != nil {
		fmt.Printf("Error running test: %v\n", err)
		os.Exit(1)
	}

	fmt.Printf("Test execution started: %s\n", execution.ID)

	if wait {
		// Wait for completion
		for {
			execution, err := runner.GetExecution(execution.ID)
			if err != nil {
				fmt.Printf("Error getting execution status: %v\n", err)
				os.Exit(1)
			}

			fmt.Printf("Status: %s\n", execution.Status)

			if execution.Status == certification.TestExecutionStatusCompleted ||
				execution.Status == certification.TestExecutionStatusFailed ||
				execution.Status == certification.TestExecutionStatusCancelled ||
				execution.Status == certification.TestExecutionStatusTimeout {
				break
			}

			time.Sleep(1 * time.Second)
		}

		// Show results
		execution, err = runner.GetExecution(execution.ID)
		if err != nil {
			fmt.Printf("Error getting final execution status: %v\n", err)
			os.Exit(1)
		}

		fmt.Printf("\nTest execution completed:\n")
		fmt.Printf("  Status: %s\n", execution.Status)
		fmt.Printf("  Duration: %s\n", execution.Duration)
		fmt.Printf("  Results: %d\n", len(execution.Results))

		for _, result := range execution.Results {
			fmt.Printf("  - %s: %s (%.2f/%.2f)\n", result.TestID, result.Status, result.Score, result.MaxScore)
		}
	}
}

func runCertificationSuite(cmd *cobra.Command, args []string) {
	deviceID := args[0]
	testIDs := args[1:]

	// Get flags
	configFile, _ := cmd.Flags().GetString("config")
	timeout, _ := cmd.Flags().GetDuration("timeout")
	wait, _ := cmd.Flags().GetBool("wait")

	// Load configuration
	config := make(map[string]interface{})
	if configFile != "" {
		if err := loadConfigFile(configFile, &config); err != nil {
			fmt.Printf("Error loading config file: %v\n", err)
			os.Exit(1)
		}
	}

	// Add timeout to config
	config["timeout"] = int(timeout.Minutes())

	// Create certification manager
	manager := certification.NewCertificationManager()
	runner := certification.NewTestRunner(manager)

	// Run test suite
	fmt.Printf("Running test suite on device %s...\n", deviceID)
	fmt.Printf("Tests: %s\n", strings.Join(testIDs, ", "))
	execution, err := runner.RunTestSuite(context.Background(), deviceID, testIDs, config)
	if err != nil {
		fmt.Printf("Error running test suite: %v\n", err)
		os.Exit(1)
	}

	fmt.Printf("Test suite execution started: %s\n", execution.ID)

	if wait {
		// Wait for completion
		for {
			execution, err := runner.GetExecution(execution.ID)
			if err != nil {
				fmt.Printf("Error getting execution status: %v\n", err)
				os.Exit(1)
			}

			fmt.Printf("Status: %s\n", execution.Status)

			if execution.Status == certification.TestExecutionStatusCompleted ||
				execution.Status == certification.TestExecutionStatusFailed ||
				execution.Status == certification.TestExecutionStatusCancelled ||
				execution.Status == certification.TestExecutionStatusTimeout {
				break
			}

			time.Sleep(1 * time.Second)
		}

		// Show results
		execution, err = runner.GetExecution(execution.ID)
		if err != nil {
			fmt.Printf("Error getting final execution status: %v\n", err)
			os.Exit(1)
		}

		fmt.Printf("\nTest suite execution completed:\n")
		fmt.Printf("  Status: %s\n", execution.Status)
		fmt.Printf("  Duration: %s\n", execution.Duration)
		fmt.Printf("  Results: %d\n", len(execution.Results))

		passed := 0
		failed := 0
		for _, result := range execution.Results {
			if result.Status == certification.TestStatusPassed {
				passed++
			} else {
				failed++
			}
			fmt.Printf("  - %s: %s (%.2f/%.2f)\n", result.TestID, result.Status, result.Score, result.MaxScore)
		}

		fmt.Printf("\nSummary: %d passed, %d failed\n", passed, failed)
	}
}

func listCertificationTests(cmd *cobra.Command, args []string) {
	manager := certification.NewCertificationManager()
	tests := manager.ListTests()

	if len(tests) == 0 {
		fmt.Println("No certification tests available")
		return
	}

	fmt.Printf("Available certification tests (%d):\n\n", len(tests))
	for _, test := range tests {
		fmt.Printf("ID: %s\n", test.ID)
		fmt.Printf("Name: %s\n", test.Name)
		fmt.Printf("Description: %s\n", test.Description)
		fmt.Printf("Category: %s\n", test.Category)
		fmt.Printf("Standard: %s\n", test.Standard)
		fmt.Printf("Version: %s\n", test.Version)
		fmt.Println("---")
	}
}

func getCertificationStatus(cmd *cobra.Command, args []string) {
	deviceID := args[0]

	manager := certification.NewCertificationManager()
	results, err := manager.GetDeviceCertification(deviceID)
	if err != nil {
		fmt.Printf("Error getting device certification: %v\n", err)
		os.Exit(1)
	}

	if len(results) == 0 {
		fmt.Printf("No certification results found for device %s\n", deviceID)
		return
	}

	// Check if device is certified
	certified, err := manager.IsDeviceCertified(deviceID)
	if err != nil {
		fmt.Printf("Error checking device certification: %v\n", err)
		os.Exit(1)
	}

	fmt.Printf("Device: %s\n", deviceID)
	fmt.Printf("Certified: %t\n", certified)
	fmt.Printf("Total Tests: %d\n", len(results))

	passed := 0
	failed := 0
	totalScore := 0.0

	for _, result := range results {
		if result.Status == certification.TestStatusPassed {
			passed++
		} else {
			failed++
		}
		totalScore += result.Score
	}

	avgScore := totalScore / float64(len(results))

	fmt.Printf("Passed: %d\n", passed)
	fmt.Printf("Failed: %d\n", failed)
	fmt.Printf("Average Score: %.2f\n", avgScore)

	fmt.Println("\nTest Results:")
	for _, result := range results {
		fmt.Printf("  - %s: %s (%.2f)\n", result.TestID, result.Status, result.Score)
	}
}

func generateCertificationReport(cmd *cobra.Command, args []string) {
	deviceID := args[0]

	// Get flags
	format, _ := cmd.Flags().GetString("format")
	output, _ := cmd.Flags().GetString("output")
	verbose, _ := cmd.Flags().GetBool("verbose")

	manager := certification.NewCertificationManager()
	results, err := manager.GetDeviceCertification(deviceID)
	if err != nil {
		fmt.Printf("Error getting device certification: %v\n", err)
		os.Exit(1)
	}

	if len(results) == 0 {
		fmt.Printf("No certification results found for device %s\n", deviceID)
		return
	}

	generator := certification.NewReportGenerator()

	var data []byte
	switch format {
	case "json":
		data, err = generator.GenerateJSONReport(deviceID, results)
	case "html":
		data, err = generator.GenerateHTMLReport(deviceID, results)
	case "pdf":
		data, err = generator.GeneratePDFReport(deviceID, results)
	default:
		fmt.Printf("Unsupported format: %s\n", format)
		os.Exit(1)
	}

	if err != nil {
		fmt.Printf("Error generating report: %v\n", err)
		os.Exit(1)
	}

	// Write to file or stdout
	if output != "" {
		if err := os.WriteFile(output, data, 0644); err != nil {
			fmt.Printf("Error writing report to file: %v\n", err)
			os.Exit(1)
		}
		fmt.Printf("Report written to %s\n", output)
	} else {
		fmt.Print(string(data))
	}

	if verbose {
		fmt.Printf("\nReport generated for device %s in %s format\n", deviceID, format)
	}
}

func getExecutionStatus(cmd *cobra.Command, args []string) {
	executionID := args[0]

	manager := certification.NewCertificationManager()
	runner := certification.NewTestRunner(manager)

	execution, err := runner.GetExecution(executionID)
	if err != nil {
		fmt.Printf("Error getting execution status: %v\n", err)
		os.Exit(1)
	}

	fmt.Printf("Execution ID: %s\n", execution.ID)
	fmt.Printf("Device ID: %s\n", execution.DeviceID)
	fmt.Printf("Test ID: %s\n", execution.TestID)
	fmt.Printf("Status: %s\n", execution.Status)
	fmt.Printf("Start Time: %s\n", execution.StartTime.Format(time.RFC3339))
	if execution.EndTime != nil {
		fmt.Printf("End Time: %s\n", execution.EndTime.Format(time.RFC3339))
		fmt.Printf("Duration: %s\n", execution.Duration)
	}

	if len(execution.Results) > 0 {
		fmt.Println("\nResults:")
		for _, result := range execution.Results {
			fmt.Printf("  - %s: %s (%.2f/%.2f)\n", result.TestID, result.Status, result.Score, result.MaxScore)
		}
	}

	if len(execution.Logs) > 0 {
		fmt.Println("\nLogs:")
		for _, log := range execution.Logs {
			fmt.Printf("  [%s] %s: %s\n", log.Level, log.Category, log.Message)
		}
	}
}

func cancelExecution(cmd *cobra.Command, args []string) {
	executionID := args[0]

	manager := certification.NewCertificationManager()
	runner := certification.NewTestRunner(manager)

	err := runner.CancelExecution(executionID)
	if err != nil {
		fmt.Printf("Error cancelling execution: %v\n", err)
		os.Exit(1)
	}

	fmt.Printf("Execution %s cancelled\n", executionID)
}

func showCertificationMetrics(cmd *cobra.Command, args []string) {
	manager := certification.NewCertificationManager()
	runner := certification.NewTestRunner(manager)

	certMetrics := manager.GetMetrics()
	testMetrics := runner.GetMetrics()

	fmt.Println("Certification Metrics:")
	fmt.Printf("  Total Tests: %d\n", certMetrics.TotalTests)
	fmt.Printf("  Passed Tests: %d\n", certMetrics.PassedTests)
	fmt.Printf("  Failed Tests: %d\n", certMetrics.FailedTests)
	fmt.Printf("  Certified Devices: %d\n", certMetrics.CertifiedDevices)
	fmt.Printf("  Expired Devices: %d\n", certMetrics.ExpiredDevices)
	fmt.Printf("  Average Score: %.2f\n", certMetrics.AverageScore)

	fmt.Println("\nTest Runner Metrics:")
	fmt.Printf("  Total Executions: %d\n", testMetrics.TotalExecutions)
	fmt.Printf("  Completed Executions: %d\n", testMetrics.CompletedExecutions)
	fmt.Printf("  Failed Executions: %d\n", testMetrics.FailedExecutions)
	fmt.Printf("  Timeout Executions: %d\n", testMetrics.TimeoutExecutions)
	fmt.Printf("  Average Duration: %s\n", testMetrics.AverageDuration)
	fmt.Printf("  Total Tests Run: %d\n", testMetrics.TotalTestsRun)
	fmt.Printf("  Passed Tests: %d\n", testMetrics.PassedTests)
	fmt.Printf("  Failed Tests: %d\n", testMetrics.FailedTests)
}

func listCertificationStandards(cmd *cobra.Command, args []string) {
	manager := certification.NewCertificationManager()
	standards := manager.ListStandards()

	if len(standards) == 0 {
		fmt.Println("No certification standards available")
		return
	}

	fmt.Printf("Available certification standards (%d):\n\n", len(standards))
	for _, standard := range standards {
		fmt.Printf("ID: %s\n", standard.ID)
		fmt.Printf("Name: %s\n", standard.Name)
		fmt.Printf("Version: %s\n", standard.Version)
		fmt.Printf("Description: %s\n", standard.Description)
		fmt.Printf("Requirements: %s\n", strings.Join(standard.Requirements, ", "))
		fmt.Printf("Tests: %s\n", strings.Join(standard.Tests, ", "))
		fmt.Println("---")
	}
}

// Helper function to load configuration file
func loadConfigFile(filename string, config *map[string]interface{}) error {
	data, err := os.ReadFile(filename)
	if err != nil {
		return err
	}

	return json.Unmarshal(data, config)
}
