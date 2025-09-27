package certification

import (
	"bytes"
	"encoding/json"
	"fmt"
	"html/template"
	"time"

	"github.com/arx-os/arxos/internal/common/logger"
)

// ReportGenerator generates certification reports
type ReportGenerator struct {
	templates map[string]*template.Template
}

// CertificationReport represents a comprehensive certification report
type CertificationReport struct {
	ID                 string                 `json:"id"`
	DeviceID           string                 `json:"device_id"`
	DeviceName         string                 `json:"device_name"`
	DeviceType         string                 `json:"device_type"`
	Manufacturer       string                 `json:"manufacturer"`
	Model              string                 `json:"model"`
	SerialNumber       string                 `json:"serial_number"`
	FirmwareVersion    string                 `json:"firmware_version"`
	HardwareVersion    string                 `json:"hardware_version"`
	GeneratedAt        time.Time              `json:"generated_at"`
	ValidUntil         time.Time              `json:"valid_until"`
	OverallScore       float64                `json:"overall_score"`
	OverallStatus      TestStatus             `json:"overall_status"`
	CertificationLevel string                 `json:"certification_level"`
	Summary            ReportSummary          `json:"summary"`
	TestResults        []TestResultSummary    `json:"test_results"`
	Recommendations    []string               `json:"recommendations"`
	Compliance         ComplianceInfo         `json:"compliance"`
	Metadata           map[string]interface{} `json:"metadata"`
}

// ReportSummary provides a high-level summary of the certification
type ReportSummary struct {
	TotalTests         int     `json:"total_tests"`
	PassedTests        int     `json:"passed_tests"`
	FailedTests        int     `json:"failed_tests"`
	SkippedTests       int     `json:"skipped_tests"`
	PassRate           float64 `json:"pass_rate"`
	TotalDuration      string  `json:"total_duration"`
	CriticalIssues     int     `json:"critical_issues"`
	Warnings           int     `json:"warnings"`
	CertificationValid bool    `json:"certification_valid"`
}

// TestResultSummary provides a summary of individual test results
type TestResultSummary struct {
	TestID     string                 `json:"test_id"`
	TestName   string                 `json:"test_name"`
	Category   string                 `json:"category"`
	Status     TestStatus             `json:"status"`
	Score      float64                `json:"score"`
	MaxScore   float64                `json:"max_score"`
	Duration   string                 `json:"duration"`
	Errors     []string               `json:"errors"`
	Warnings   []string               `json:"warnings"`
	KeyMetrics map[string]interface{} `json:"key_metrics"`
}

// ComplianceInfo provides compliance information
type ComplianceInfo struct {
	Standards       []string `json:"standards"`
	Regulations     []string `json:"regulations"`
	Certifications  []string `json:"certifications"`
	ComplianceScore float64  `json:"compliance_score"`
}

// NewReportGenerator creates a new report generator
func NewReportGenerator() *ReportGenerator {
	rg := &ReportGenerator{
		templates: make(map[string]*template.Template),
	}
	rg.loadTemplates()
	return rg
}

// GenerateReport generates a comprehensive certification report
func (rg *ReportGenerator) GenerateReport(deviceID string, results []*CertificationResult) (*CertificationReport, error) {
	if len(results) == 0 {
		return nil, fmt.Errorf("no test results provided for device %s", deviceID)
	}

	// Calculate overall metrics
	summary := rg.calculateSummary(results)

	// Calculate overall score and status
	overallScore, overallStatus := rg.calculateOverallScore(results)

	// Determine certification level
	certificationLevel := rg.determineCertificationLevel(overallScore, summary)

	// Generate test result summaries
	testSummaries := rg.generateTestSummaries(results)

	// Generate recommendations
	recommendations := rg.generateRecommendations(results, summary)

	// Generate compliance information
	compliance := rg.generateComplianceInfo(results)

	// Create report
	report := &CertificationReport{
		ID:                 fmt.Sprintf("report_%s_%d", deviceID, time.Now().Unix()),
		DeviceID:           deviceID,
		DeviceName:         rg.extractDeviceName(results),
		DeviceType:         rg.extractDeviceType(results),
		Manufacturer:       rg.extractManufacturer(results),
		Model:              rg.extractModel(results),
		SerialNumber:       rg.extractSerialNumber(results),
		FirmwareVersion:    rg.extractFirmwareVersion(results),
		HardwareVersion:    rg.extractHardwareVersion(results),
		GeneratedAt:        time.Now(),
		ValidUntil:         time.Now().Add(365 * 24 * time.Hour), // 1 year validity
		OverallScore:       overallScore,
		OverallStatus:      overallStatus,
		CertificationLevel: certificationLevel,
		Summary:            summary,
		TestResults:        testSummaries,
		Recommendations:    recommendations,
		Compliance:         compliance,
		Metadata: map[string]interface{}{
			"report_version": "1.0.0",
			"generator":      "ArxOS Certification System",
			"environment":    "production",
		},
	}

	logger.Info("Generated certification report for device %s: %s (score: %.2f)", deviceID, overallStatus, overallScore)
	return report, nil
}

// GenerateJSONReport generates a JSON report
func (rg *ReportGenerator) GenerateJSONReport(deviceID string, results []*CertificationResult) ([]byte, error) {
	report, err := rg.GenerateReport(deviceID, results)
	if err != nil {
		return nil, err
	}

	jsonData, err := json.MarshalIndent(report, "", "  ")
	if err != nil {
		return nil, fmt.Errorf("failed to marshal report to JSON: %w", err)
	}

	return jsonData, nil
}

// GenerateHTMLReport generates an HTML report
func (rg *ReportGenerator) GenerateHTMLReport(deviceID string, results []*CertificationResult) ([]byte, error) {
	report, err := rg.GenerateReport(deviceID, results)
	if err != nil {
		return nil, err
	}

	tmpl, exists := rg.templates["html"]
	if !exists {
		return nil, fmt.Errorf("HTML template not found")
	}

	var buf bytes.Buffer
	if err := tmpl.Execute(&buf, report); err != nil {
		return nil, fmt.Errorf("failed to execute HTML template: %w", err)
	}

	return buf.Bytes(), nil
}

// GeneratePDFReport generates a PDF report (placeholder)
func (rg *ReportGenerator) GeneratePDFReport(deviceID string, results []*CertificationResult) ([]byte, error) {
	// In a real implementation, this would generate a PDF using a library like wkhtmltopdf
	// For now, return the HTML report as a placeholder
	return rg.GenerateHTMLReport(deviceID, results)
}

// calculateSummary calculates the report summary
func (rg *ReportGenerator) calculateSummary(results []*CertificationResult) ReportSummary {
	totalTests := len(results)
	passedTests := 0
	failedTests := 0
	skippedTests := 0
	criticalIssues := 0
	warnings := 0
	var totalDuration time.Duration

	for _, result := range results {
		totalDuration += result.Duration

		switch result.Status {
		case TestStatusPassed:
			passedTests++
		case TestStatusFailed:
			failedTests++
			criticalIssues += len(result.Errors)
		case TestStatusSkipped:
			skippedTests++
		}

		warnings += len(result.Warnings)
	}

	passRate := 0.0
	if totalTests > 0 {
		passRate = float64(passedTests) / float64(totalTests) * 100.0
	}

	return ReportSummary{
		TotalTests:         totalTests,
		PassedTests:        passedTests,
		FailedTests:        failedTests,
		SkippedTests:       skippedTests,
		PassRate:           passRate,
		TotalDuration:      totalDuration.String(),
		CriticalIssues:     criticalIssues,
		Warnings:           warnings,
		CertificationValid: passRate >= 80.0 && criticalIssues == 0,
	}
}

// calculateOverallScore calculates the overall score and status
func (rg *ReportGenerator) calculateOverallScore(results []*CertificationResult) (float64, TestStatus) {
	if len(results) == 0 {
		return 0.0, TestStatusFailed
	}

	totalScore := 0.0
	allPassed := true

	for _, result := range results {
		totalScore += result.Score
		if result.Status != TestStatusPassed {
			allPassed = false
		}
	}

	averageScore := totalScore / float64(len(results))

	if allPassed && averageScore >= 80.0 {
		return averageScore, TestStatusPassed
	}
	return averageScore, TestStatusFailed
}

// determineCertificationLevel determines the certification level
func (rg *ReportGenerator) determineCertificationLevel(score float64, summary ReportSummary) string {
	if score >= 95.0 && summary.CriticalIssues == 0 && summary.Warnings <= 2 {
		return "Platinum"
	} else if score >= 90.0 && summary.CriticalIssues == 0 && summary.Warnings <= 5 {
		return "Gold"
	} else if score >= 80.0 && summary.CriticalIssues == 0 {
		return "Silver"
	} else if score >= 70.0 {
		return "Bronze"
	} else {
		return "Not Certified"
	}
}

// generateTestSummaries generates test result summaries
func (rg *ReportGenerator) generateTestSummaries(results []*CertificationResult) []TestResultSummary {
	summaries := make([]TestResultSummary, 0, len(results))

	for _, result := range results {
		summary := TestResultSummary{
			TestID:     result.TestID,
			TestName:   rg.getTestName(result.TestID),
			Category:   rg.getTestCategory(result.TestID),
			Status:     result.Status,
			Score:      result.Score,
			MaxScore:   100.0,
			Duration:   result.Duration.String(),
			Errors:     result.Errors,
			Warnings:   result.Warnings,
			KeyMetrics: rg.extractKeyMetrics(result.Details),
		}
		summaries = append(summaries, summary)
	}

	return summaries
}

// generateRecommendations generates recommendations based on test results
func (rg *ReportGenerator) generateRecommendations(results []*CertificationResult, summary ReportSummary) []string {
	recommendations := make([]string, 0)

	// Overall recommendations
	if summary.PassRate < 80.0 {
		recommendations = append(recommendations, "Overall pass rate is below 80%. Consider addressing failed tests before resubmission.")
	}

	if summary.CriticalIssues > 0 {
		recommendations = append(recommendations, fmt.Sprintf("Address %d critical issues before certification can be granted.", summary.CriticalIssues))
	}

	if summary.Warnings > 10 {
		recommendations = append(recommendations, "High number of warnings detected. Consider addressing these to improve certification level.")
	}

	// Category-specific recommendations
	categoryScores := rg.calculateCategoryScores(results)

	if score, exists := categoryScores["safety"]; exists && score < 80.0 {
		recommendations = append(recommendations, "Safety test score is below threshold. Review electrical and fire safety compliance.")
	}

	if score, exists := categoryScores["performance"]; exists && score < 75.0 {
		recommendations = append(recommendations, "Performance test score is below threshold. Optimize response time and throughput.")
	}

	if score, exists := categoryScores["security"]; exists && score < 90.0 {
		recommendations = append(recommendations, "Security test score is below threshold. Review encryption and authentication implementation.")
	}

	if score, exists := categoryScores["reliability"]; exists && score < 80.0 {
		recommendations = append(recommendations, "Reliability test score is below threshold. Improve error handling and recovery mechanisms.")
	}

	return recommendations
}

// generateComplianceInfo generates compliance information
func (rg *ReportGenerator) generateComplianceInfo(results []*CertificationResult) ComplianceInfo {
	standards := []string{
		"IEC 61010-1 (Safety)",
		"IEC 61326 (EMC)",
		"FCC Part 15 (EMC)",
		"CE Marking (EU)",
	}

	regulations := []string{
		"RoHS 2 (EU)",
		"REACH (EU)",
		"WEEE (EU)",
	}

	certifications := []string{
		"ArxOS Basic Certification",
		"ArxOS Security Certification",
		"ArxOS Performance Certification",
	}

	// Calculate compliance score based on test results
	complianceScore := rg.calculateComplianceScore(results)

	return ComplianceInfo{
		Standards:       standards,
		Regulations:     regulations,
		Certifications:  certifications,
		ComplianceScore: complianceScore,
	}
}

// calculateCategoryScores calculates scores by category
func (rg *ReportGenerator) calculateCategoryScores(results []*CertificationResult) map[string]float64 {
	categoryScores := make(map[string]float64)
	categoryCounts := make(map[string]int)

	for _, result := range results {
		category := rg.getTestCategory(result.TestID)
		categoryScores[category] += result.Score
		categoryCounts[category]++
	}

	// Calculate averages
	for category, total := range categoryScores {
		if count, exists := categoryCounts[category]; exists && count > 0 {
			categoryScores[category] = total / float64(count)
		}
	}

	return categoryScores
}

// calculateComplianceScore calculates the compliance score
func (rg *ReportGenerator) calculateComplianceScore(results []*CertificationResult) float64 {
	if len(results) == 0 {
		return 0.0
	}

	totalScore := 0.0
	for _, result := range results {
		totalScore += result.Score
	}

	return totalScore / float64(len(results))
}

// Helper methods for extracting device information
func (rg *ReportGenerator) extractDeviceName(results []*CertificationResult) string {
	// In a real implementation, would extract from device metadata
	return "ArxOS Device"
}

func (rg *ReportGenerator) extractDeviceType(results []*CertificationResult) string {
	// In a real implementation, would extract from device metadata
	return "IoT Device"
}

func (rg *ReportGenerator) extractManufacturer(results []*CertificationResult) string {
	// In a real implementation, would extract from device metadata
	return "ArxOS Technologies"
}

func (rg *ReportGenerator) extractModel(results []*CertificationResult) string {
	// In a real implementation, would extract from device metadata
	return "AX-001"
}

func (rg *ReportGenerator) extractSerialNumber(results []*CertificationResult) string {
	// In a real implementation, would extract from device metadata
	return "SN123456789"
}

func (rg *ReportGenerator) extractFirmwareVersion(results []*CertificationResult) string {
	// In a real implementation, would extract from device metadata
	return "1.0.0"
}

func (rg *ReportGenerator) extractHardwareVersion(results []*CertificationResult) string {
	// In a real implementation, would extract from device metadata
	return "HW-1.0"
}

func (rg *ReportGenerator) getTestName(testID string) string {
	// In a real implementation, would look up test name from test registry
	testNames := map[string]string{
		"safety_basic":       "Basic Safety Test",
		"performance_basic":  "Basic Performance Test",
		"compatibility_mqtt": "MQTT Compatibility Test",
		"security_basic":     "Basic Security Test",
		"reliability_basic":  "Basic Reliability Test",
		"interop_basic":      "Basic Interoperability Test",
	}

	if name, exists := testNames[testID]; exists {
		return name
	}
	return testID
}

func (rg *ReportGenerator) getTestCategory(testID string) string {
	// In a real implementation, would look up test category from test registry
	categoryMap := map[string]string{
		"safety_basic":       "safety",
		"performance_basic":  "performance",
		"compatibility_mqtt": "compatibility",
		"security_basic":     "security",
		"reliability_basic":  "reliability",
		"interop_basic":      "interoperability",
	}

	if category, exists := categoryMap[testID]; exists {
		return category
	}
	return "unknown"
}

func (rg *ReportGenerator) extractKeyMetrics(details map[string]interface{}) map[string]interface{} {
	// Extract key metrics from test details
	keyMetrics := make(map[string]interface{})

	for key, value := range details {
		// Only include numeric values as key metrics
		if _, ok := value.(float64); ok {
			keyMetrics[key] = value
		}
	}

	return keyMetrics
}

// loadTemplates loads HTML templates
func (rg *ReportGenerator) loadTemplates() {
	htmlTemplate := `
<!DOCTYPE html>
<html>
<head>
    <title>ArxOS Certification Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        .header { background-color: #f0f0f0; padding: 20px; border-radius: 5px; }
        .summary { margin: 20px 0; }
        .test-result { margin: 10px 0; padding: 10px; border-left: 4px solid #ccc; }
        .passed { border-left-color: #4CAF50; }
        .failed { border-left-color: #f44336; }
        .score { font-size: 24px; font-weight: bold; }
        .passed-score { color: #4CAF50; }
        .failed-score { color: #f44336; }
    </style>
</head>
<body>
    <div class="header">
        <h1>ArxOS Certification Report</h1>
        <p><strong>Device ID:</strong> {{.DeviceID}}</p>
        <p><strong>Generated:</strong> {{.GeneratedAt.Format "2006-01-02 15:04:05"}}</p>
        <p><strong>Overall Score:</strong> <span class="score {{if eq .OverallStatus "passed"}}passed-score{{else}}failed-score{{end}}">{{printf "%.2f" .OverallScore}}</span></p>
        <p><strong>Status:</strong> {{.OverallStatus}}</p>
        <p><strong>Certification Level:</strong> {{.CertificationLevel}}</p>
    </div>
    
    <div class="summary">
        <h2>Summary</h2>
        <p>Total Tests: {{.Summary.TotalTests}} | Passed: {{.Summary.PassedTests}} | Failed: {{.Summary.FailedTests}}</p>
        <p>Pass Rate: {{printf "%.1f" .Summary.PassRate}}%</p>
        <p>Total Duration: {{.Summary.TotalDuration}}</p>
    </div>
    
    <div class="test-results">
        <h2>Test Results</h2>
        {{range .TestResults}}
        <div class="test-result {{if eq .Status "passed"}}passed{{else}}failed{{end}}">
            <h3>{{.TestName}} ({{.Category}})</h3>
            <p>Score: {{printf "%.2f" .Score}}/{{printf "%.2f" .MaxScore}} | Status: {{.Status}} | Duration: {{.Duration}}</p>
            {{if .Errors}}
            <p><strong>Errors:</strong></p>
            <ul>
                {{range .Errors}}
                <li>{{.}}</li>
                {{end}}
            </ul>
            {{end}}
            {{if .Warnings}}
            <p><strong>Warnings:</strong></p>
            <ul>
                {{range .Warnings}}
                <li>{{.}}</li>
                {{end}}
            </ul>
            {{end}}
        </div>
        {{end}}
    </div>
    
    {{if .Recommendations}}
    <div class="recommendations">
        <h2>Recommendations</h2>
        <ul>
            {{range .Recommendations}}
            <li>{{.}}</li>
            {{end}}
        </ul>
    </div>
    {{end}}
</body>
</html>`

	tmpl, err := template.New("html").Parse(htmlTemplate)
	if err != nil {
		logger.Error("Failed to parse HTML template: %v", err)
		return
	}

	rg.templates["html"] = tmpl
}
