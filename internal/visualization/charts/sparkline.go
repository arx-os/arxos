package charts

import (
	"fmt"
	"math"
	"strings"

	"github.com/arx-os/arxos/internal/visualization/core"
)

// SparklineData represents time-series data for sparklines
type SparklineData struct {
	Values []float64
	Label  string
	Min    float64
	Max    float64
}

// GetType implements DataSet interface
func (s *SparklineData) GetType() string {
	return "sparkline"
}

// Validate implements DataSet interface
func (s *SparklineData) Validate() error {
	if len(s.Values) == 0 {
		return fmt.Errorf("no values provided")
	}
	return nil
}

// Sparkline renders compact line charts
type Sparkline struct {
	renderer *core.TerminalRenderer
}

// NewSparkline creates a new sparkline renderer
func NewSparkline() *Sparkline {
	return &Sparkline{
		renderer: core.NewTerminalRenderer(),
	}
}

// Render renders a sparkline
func (s *Sparkline) Render(data *SparklineData, width int) string {
	if err := data.Validate(); err != nil {
		return ""
	}

	// Determine symbol set
	symbols := core.ASCIISymbols
	if s.renderer.SupportsUnicode() {
		symbols = core.UnicodeSymbols
	}

	// Find min/max if not provided
	min, max := data.Min, data.Max
	if min == 0 && max == 0 {
		min, max = findMinMax(data.Values)
	}

	// Handle edge case where all values are the same
	if min == max {
		max = min + 1
	}

	var output strings.Builder

	// Add label if provided
	if data.Label != "" {
		output.WriteString(fmt.Sprintf("%-12s ", data.Label))
	}

	// Sample data if we have more values than width
	values := data.Values
	if len(values) > width {
		values = sampleData(values, width)
	}

	// Render sparkline
	for _, value := range values {
		normalized := (value - min) / (max - min)
		output.WriteRune(symbols.GetSparklineChar(normalized))
	}

	// Add current value
	if len(data.Values) > 0 {
		current := data.Values[len(data.Values)-1]
		output.WriteString(fmt.Sprintf(" %.1f", current))

		// Add trend indicator
		if len(data.Values) > 1 {
			prev := data.Values[len(data.Values)-2]
			if current > prev {
				output.WriteString(" ↑")
			} else if current < prev {
				output.WriteString(" ↓")
			} else {
				output.WriteString(" →")
			}
		}
	}

	return output.String()
}

// RenderMultiple renders multiple sparklines aligned
func (s *Sparkline) RenderMultiple(datasets []SparklineData, width int) string {
	var output strings.Builder

	// Find the longest label for alignment
	maxLabelLen := 0
	for _, data := range datasets {
		if len(data.Label) > maxLabelLen {
			maxLabelLen = len(data.Label)
		}
	}

	// Render each sparkline
	for _, data := range datasets {
		// Pad label for alignment
		label := fmt.Sprintf("%-*s", maxLabelLen, data.Label)
		data.Label = label

		output.WriteString(s.Render(&data, width-maxLabelLen-1))
		output.WriteString("\n")
	}

	return strings.TrimSuffix(output.String(), "\n")
}

// findMinMax finds the minimum and maximum values in a slice
func findMinMax(values []float64) (min, max float64) {
	if len(values) == 0 {
		return 0, 0
	}

	min = values[0]
	max = values[0]

	for _, v := range values[1:] {
		if v < min {
			min = v
		}
		if v > max {
			max = v
		}
	}

	return min, max
}

// sampleData samples data points to fit within width
func sampleData(values []float64, targetWidth int) []float64 {
	if len(values) <= targetWidth {
		return values
	}

	sampled := make([]float64, targetWidth)
	step := float64(len(values)-1) / float64(targetWidth-1)

	for i := 0; i < targetWidth; i++ {
		index := int(math.Round(float64(i) * step))
		if index >= len(values) {
			index = len(values) - 1
		}
		sampled[i] = values[index]
	}

	return sampled
}

// RenderSystemMetrics renders multiple system metrics as sparklines
func RenderSystemMetrics(metrics map[string][]float64) string {
	spark := NewSparkline()

	var datasets []SparklineData
	for name, values := range metrics {
		datasets = append(datasets, SparklineData{
			Label:  name,
			Values: values,
		})
	}

	return spark.RenderMultiple(datasets, 40)
}

// RenderTimeSeries renders a time series with labels
func RenderTimeSeries(label string, values []float64, timestamps []string, width int) string {
	spark := NewSparkline()

	data := &SparklineData{
		Label:  label,
		Values: values,
	}

	var output strings.Builder

	// Render sparkline
	output.WriteString(spark.Render(data, width))
	output.WriteString("\n")

	// Add time labels if provided
	if len(timestamps) > 0 {
		// Sample timestamps to match sparkline width
		if len(timestamps) > width {
			sampled := make([]string, width)
			step := float64(len(timestamps)-1) / float64(width-1)
			for i := 0; i < width; i++ {
				index := int(math.Round(float64(i) * step))
				if index >= len(timestamps) {
					index = len(timestamps) - 1
				}
				sampled[i] = timestamps[index]
			}
			timestamps = sampled
		}

		// Add start and end time labels
		if len(data.Label) > 0 {
			output.WriteString(strings.Repeat(" ", len(data.Label)+1))
		}

		if len(timestamps) > 1 {
			output.WriteString(timestamps[0])
			spacing := width - len(timestamps[0]) - len(timestamps[len(timestamps)-1])
			if spacing > 0 {
				output.WriteString(strings.Repeat(" ", spacing))
			}
			output.WriteString(timestamps[len(timestamps)-1])
		}
	}

	return output.String()
}

// Example usage function
func ExampleSparkline() {
	spark := NewSparkline()

	// Power usage over 24 hours
	powerData := &SparklineData{
		Label: "Power (kW)",
		Values: []float64{
			45, 48, 52, 58, 65, 72, 85, 92, 88, 84,
			82, 80, 78, 76, 74, 72, 68, 62, 55, 50,
			48, 46, 44, 43,
		},
	}

	fmt.Println(spark.Render(powerData, 24))

	// Multiple metrics
	datasets := []SparklineData{
		{
			Label:  "Temperature",
			Values: []float64{68, 69, 70, 71, 72, 73, 74, 75, 74, 73, 72, 71},
		},
		{
			Label:  "Humidity",
			Values: []float64{45, 46, 47, 48, 49, 50, 48, 46, 45, 44, 43, 42},
		},
		{
			Label:  "CO2 (ppm)",
			Values: []float64{400, 420, 450, 480, 500, 520, 510, 490, 470, 450, 430, 410},
		},
	}

	fmt.Println("\nBuilding Metrics (12hr):")
	fmt.Println(spark.RenderMultiple(datasets, 20))
}

// CreateDashboardSparklines creates sparklines for a dashboard
func CreateDashboardSparklines(building string) string {
	var output strings.Builder

	output.WriteString(fmt.Sprintf("Building %s - Real-time Metrics\n", building))
	output.WriteString(strings.Repeat("─", 50))
	output.WriteString("\n\n")

	// Generate sample data (in real use, this would come from the database)
	metrics := map[string][]float64{
		"Power (kW)":   generateSampleData(24, 50, 100),
		"Temp (°F)":    generateSampleData(24, 68, 76),
		"Humidity (%)": generateSampleData(24, 30, 60),
		"CO2 (ppm)":    generateSampleData(24, 350, 600),
		"Occupancy":    generateSampleData(24, 0, 100),
	}

	spark := NewSparkline()
	for name, values := range metrics {
		data := &SparklineData{
			Label:  name,
			Values: values,
		}
		output.WriteString(spark.Render(data, 30))
		output.WriteString("\n")
	}

	return output.String()
}

// generateSampleData generates random sample data for testing
func generateSampleData(count int, min, max float64) []float64 {
	data := make([]float64, count)
	range_ := max - min

	// Generate somewhat realistic data with trends
	current := min + (range_ / 2)
	for i := 0; i < count; i++ {
		// Random walk
		change := (range_ / 20) * (2*math.Sin(float64(i)/3) - 1)
		current += change

		// Keep within bounds
		if current < min {
			current = min
		}
		if current > max {
			current = max
		}

		data[i] = current
	}

	return data
}