# ArxOS Hardware Platform Makefile
# Builds TinyGo device templates for various microcontrollers

# TinyGo installation check
TINYGO := $(shell which tinygo 2>/dev/null)
ifndef TINYGO
$(error TinyGo is not installed. Please install from https://tinygo.org/getting-started/install/)
endif

# Build directories
BUILD_DIR := build
ESP32_DIR := $(BUILD_DIR)/esp32
RP2040_DIR := $(BUILD_DIR)/rp2040
GATEWAY_DIR := $(BUILD_DIR)/gateway

# Source directories
TEMPLATES_DIR := templates
ESP32_SRC := $(TEMPLATES_DIR)/esp32
RP2040_SRC := $(TEMPLATES_DIR)/rp2040
GATEWAY_SRC := $(TEMPLATES_DIR)/gateway

# TinyGo targets
ESP32_TARGET := esp32
RP2040_TARGET := rp2040
GATEWAY_TARGET := esp32

# Build flags
TINYGO_FLAGS := -size=short -opt=z
LDFLAGS := -ldflags="-s -w"

# Default target
.PHONY: all
all: esp32 rp2040 gateway

# Create build directories
$(BUILD_DIR):
	@mkdir -p $(BUILD_DIR)

$(ESP32_DIR): $(BUILD_DIR)
	@mkdir -p $(ESP32_DIR)

$(RP2040_DIR): $(BUILD_DIR)
	@mkdir -p $(RP2040_DIR)

$(GATEWAY_DIR): $(BUILD_DIR)
	@mkdir -p $(GATEWAY_DIR)

# ESP32 targets
.PHONY: esp32
esp32: $(ESP32_DIR) esp32-sensor

.PHONY: esp32-sensor
esp32-sensor: $(ESP32_DIR)
	@echo "🔨 Building ESP32 sensor template..."
	@tinygo build $(TINYGO_FLAGS) -target=$(ESP32_TARGET) -o $(ESP32_DIR)/sensor.bin $(ESP32_SRC)/sensor_template.go
	@echo "✅ ESP32 sensor template built: $(ESP32_DIR)/sensor.bin"

.PHONY: esp32-actuator
esp32-actuator: $(ESP32_DIR)
	@echo "🔨 Building ESP32 actuator template..."
	@tinygo build $(TINYGO_FLAGS) -target=$(ESP32_TARGET) -o $(ESP32_DIR)/actuator.bin $(ESP32_SRC)/actuator_template.go
	@echo "✅ ESP32 actuator template built: $(ESP32_DIR)/actuator.bin"

# RP2040 targets
.PHONY: rp2040
rp2040: $(RP2040_DIR) rp2040-actuator

.PHONY: rp2040-actuator
rp2040-actuator: $(RP2040_DIR)
	@echo "🔨 Building RP2040 actuator template..."
	@tinygo build $(TINYGO_FLAGS) -target=$(RP2040_TARGET) -o $(RP2040_DIR)/actuator.uf2 $(RP2040_SRC)/actuator_template.go
	@echo "✅ RP2040 actuator template built: $(RP2040_DIR)/actuator.uf2"

.PHONY: rp2040-sensor
rp2040-sensor: $(RP2040_DIR)
	@echo "🔨 Building RP2040 sensor template..."
	@tinygo build $(TINYGO_FLAGS) -target=$(RP2040_TARGET) -o $(RP2040_DIR)/sensor.uf2 $(RP2040_SRC)/sensor_template.go
	@echo "✅ RP2040 sensor template built: $(RP2040_DIR)/sensor.uf2"

# Gateway targets
.PHONY: gateway
gateway: $(GATEWAY_DIR) gateway-esp32

.PHONY: gateway-esp32
gateway-esp32: $(GATEWAY_DIR)
	@echo "🔨 Building ESP32 gateway template..."
	@tinygo build $(TINYGO_FLAGS) -target=$(GATEWAY_TARGET) -o $(GATEWAY_DIR)/gateway.bin $(GATEWAY_SRC)/gateway_template.go
	@echo "✅ ESP32 gateway template built: $(GATEWAY_DIR)/gateway.bin"

# Flash targets (requires connected hardware)
.PHONY: flash-esp32-sensor
flash-esp32-sensor: esp32-sensor
	@echo "📤 Flashing ESP32 sensor template..."
	@tinygo flash -target=$(ESP32_TARGET) $(ESP32_SRC)/sensor_template.go
	@echo "✅ ESP32 sensor template flashed"

.PHONY: flash-esp32-actuator
flash-esp32-actuator: esp32-actuator
	@echo "📤 Flashing ESP32 actuator template..."
	@tinygo flash -target=$(ESP32_TARGET) $(ESP32_SRC)/actuator_template.go
	@echo "✅ ESP32 actuator template flashed"

.PHONY: flash-rp2040-actuator
flash-rp2040-actuator: rp2040-actuator
	@echo "📤 Flashing RP2040 actuator template..."
	@tinygo flash -target=$(RP2040_TARGET) $(RP2040_SRC)/actuator_template.go
	@echo "✅ RP2040 actuator template flashed"

.PHONY: flash-gateway
flash-gateway: gateway-esp32
	@echo "📤 Flashing ESP32 gateway template..."
	@tinygo flash -target=$(GATEWAY_TARGET) $(GATEWAY_SRC)/gateway_template.go
	@echo "✅ ESP32 gateway template flashed"

# Test targets
.PHONY: test
test: test-esp32 test-rp2040 test-gateway

.PHONY: test-esp32
test-esp32:
	@echo "🧪 Testing ESP32 templates..."
	@tinygo test -target=$(ESP32_TARGET) $(ESP32_SRC)/sensor_template.go
	@echo "✅ ESP32 tests passed"

.PHONY: test-rp2040
test-rp2040:
	@echo "🧪 Testing RP2040 templates..."
	@tinygo test -target=$(RP2040_TARGET) $(RP2040_SRC)/actuator_template.go
	@echo "✅ RP2040 tests passed"

.PHONY: test-gateway
test-gateway:
	@echo "🧪 Testing gateway templates..."
	@tinygo test -target=$(GATEWAY_TARGET) $(GATEWAY_SRC)/gateway_template.go
	@echo "✅ Gateway tests passed"

# Clean targets
.PHONY: clean
clean:
	@echo "🧹 Cleaning build artifacts..."
	@rm -rf $(BUILD_DIR)
	@echo "✅ Clean complete"

.PHONY: clean-esp32
clean-esp32:
	@echo "🧹 Cleaning ESP32 build artifacts..."
	@rm -rf $(ESP32_DIR)
	@echo "✅ ESP32 clean complete"

.PHONY: clean-rp2040
clean-rp2040:
	@echo "🧹 Cleaning RP2040 build artifacts..."
	@rm -rf $(RP2040_DIR)
	@echo "✅ RP2040 clean complete"

.PHONY: clean-gateway
clean-gateway:
	@echo "🧹 Cleaning gateway build artifacts..."
	@rm -rf $(GATEWAY_DIR)
	@echo "✅ Gateway clean complete"

# Size analysis
.PHONY: size
size: esp32 rp2040 gateway
	@echo "📊 Analyzing binary sizes..."
	@echo "ESP32 Sensor:"
	@ls -lh $(ESP32_DIR)/sensor.bin 2>/dev/null || echo "Not built"
	@echo "ESP32 Actuator:"
	@ls -lh $(ESP32_DIR)/actuator.bin 2>/dev/null || echo "Not built"
	@echo "RP2040 Actuator:"
	@ls -lh $(RP2040_DIR)/actuator.uf2 2>/dev/null || echo "Not built"
	@echo "ESP32 Gateway:"
	@ls -lh $(GATEWAY_DIR)/gateway.bin 2>/dev/null || echo "Not built"

# Help target
.PHONY: help
help:
	@echo "ArxOS Hardware Platform Makefile"
	@echo ""
	@echo "Available targets:"
	@echo "  all                 - Build all templates"
	@echo "  esp32               - Build ESP32 templates"
	@echo "  esp32-sensor        - Build ESP32 sensor template"
	@echo "  esp32-actuator      - Build ESP32 actuator template"
	@echo "  rp2040              - Build RP2040 templates"
	@echo "  rp2040-actuator     - Build RP2040 actuator template"
	@echo "  rp2040-sensor       - Build RP2040 sensor template"
	@echo "  gateway             - Build gateway templates"
	@echo "  gateway-esp32       - Build ESP32 gateway template"
	@echo ""
	@echo "Flash targets (requires connected hardware):"
	@echo "  flash-esp32-sensor  - Flash ESP32 sensor template"
	@echo "  flash-esp32-actuator- Flash ESP32 actuator template"
	@echo "  flash-rp2040-actuator- Flash RP2040 actuator template"
	@echo "  flash-gateway       - Flash ESP32 gateway template"
	@echo ""
	@echo "Test targets:"
	@echo "  test                - Run all tests"
	@echo "  test-esp32          - Test ESP32 templates"
	@echo "  test-rp2040         - Test RP2040 templates"
	@echo "  test-gateway        - Test gateway templates"
	@echo ""
	@echo "Clean targets:"
	@echo "  clean               - Clean all build artifacts"
	@echo "  clean-esp32         - Clean ESP32 build artifacts"
	@echo "  clean-rp2040        - Clean RP2040 build artifacts"
	@echo "  clean-gateway       - Clean gateway build artifacts"
	@echo ""
	@echo "Utility targets:"
	@echo "  size                - Show binary sizes"
	@echo "  help                - Show this help message"
	@echo ""
	@echo "Prerequisites:"
	@echo "  - TinyGo installed (https://tinygo.org/getting-started/install/)"
	@echo "  - ESP32 or RP2040 hardware for flashing"
	@echo ""
	@echo "Examples:"
	@echo "  make esp32-sensor   # Build ESP32 sensor template"
	@echo "  make flash-esp32-sensor # Flash to connected ESP32"
	@echo "  make test           # Run all tests"
	@echo "  make clean          # Clean build artifacts"
