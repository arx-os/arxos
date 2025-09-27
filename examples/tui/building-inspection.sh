#!/bin/bash
# Building Inspection Workflow Example
# This script demonstrates how to use ArxOS TUI for building inspections

set -e

echo "🏗️  ArxOS Building Inspection Workflow"
echo "======================================"
echo

# Configuration
BUILDING_ID="${1:-ARXOS-001}"
INSPECTOR="${2:-$(whoami)}"
DATE=$(date +"%Y-%m-%d %H:%M:%S")

echo "Building ID: $BUILDING_ID"
echo "Inspector: $INSPECTOR"
echo "Date: $DATE"
echo

# Check if TUI is enabled
if [ "${ARXOS_TUI_ENABLED:-true}" != "true" ]; then
    echo "❌ TUI is disabled. Please enable it:"
    echo "   export ARXOS_TUI_ENABLED=true"
    exit 1
fi

# Set TUI configuration for inspection
export ARXOS_TUI_THEME="dark"
export ARXOS_TUI_UPDATE_INTERVAL="2s"
export ARXOS_TUI_MAX_EQUIPMENT="500"
export ARXOS_TUI_REAL_TIME="true"
export ARXOS_TUI_ANIMATIONS="true"

echo "🔧 TUI Configuration:"
echo "   Theme: ${ARXOS_TUI_THEME}"
echo "   Update Interval: ${ARXOS_TUI_UPDATE_INTERVAL}"
echo "   Max Equipment: ${ARXOS_TUI_MAX_EQUIPMENT}"
echo "   Real-time: ${ARXOS_TUI_REAL_TIME}"
echo "   Animations: ${ARXOS_TUI_ANIMATIONS}"
echo

# Function to run TUI command with error handling
run_tui() {
    local mode="$1"
    local description="$2"
    
    echo "🚀 Starting $description..."
    echo "   Mode: $mode"
    echo "   Building: $BUILDING_ID"
    echo
    
    if ! ./arx visualize $mode --tui --building "$BUILDING_ID"; then
        echo "❌ Failed to start $description"
        echo "   Check logs: ~/.arxos/logs/tui.log"
        return 1
    fi
    
    echo "✅ $description completed"
    echo
}

# Step 1: Dashboard Overview
echo "📊 Step 1: Dashboard Overview"
echo "-----------------------------"
echo "This will show the building overview with:"
echo "• Real-time metrics"
echo "• Equipment status summary"
echo "• Active alerts"
echo "• Performance indicators"
echo
read -p "Press Enter to start dashboard..."
run_tui "" "Building Dashboard"

# Step 2: Building Explorer
echo "🔍 Step 2: Building Explorer"
echo "----------------------------"
echo "This will allow you to:"
echo "• Navigate building hierarchy"
echo "• Drill down to specific equipment"
echo "• View detailed equipment information"
echo
read -p "Press Enter to start building explorer..."
run_tui "explorer" "Building Explorer"

# Step 3: Equipment Manager
echo "⚙️  Step 3: Equipment Manager"
echo "-----------------------------"
echo "This will allow you to:"
echo "• Filter equipment by type and status"
echo "• Search for specific equipment"
echo "• Monitor equipment performance"
echo
read -p "Press Enter to start equipment manager..."
run_tui "equipment" "Equipment Manager"

# Step 4: Floor Plan Analysis
echo "🗺️  Step 4: Floor Plan Analysis"
echo "-------------------------------"
echo "This will allow you to:"
echo "• View ASCII floor plans"
echo "• Analyze spatial relationships"
echo "• Identify equipment positioning"
echo
read -p "Press Enter to start floor plan view..."
run_tui "floorplan" "Floor Plan Analysis"

# Step 5: Spatial Queries
echo "🔍 Step 5: Spatial Queries"
echo "-------------------------"
echo "This will allow you to:"
echo "• Perform spatial analysis"
echo "• Query equipment by location"
echo "• Analyze spatial relationships"
echo
read -p "Press Enter to start spatial queries..."
run_tui "query" "Spatial Queries"

# Summary
echo "✅ Building Inspection Complete"
echo "==============================="
echo
echo "Inspection Summary:"
echo "• Building: $BUILDING_ID"
echo "• Inspector: $INSPECTOR"
echo "• Date: $DATE"
echo "• TUI Modes Used: Dashboard, Explorer, Equipment, Floor Plan, Spatial Queries"
echo
echo "Next Steps:"
echo "• Review inspection notes"
echo "• Generate inspection report"
echo "• Schedule follow-up actions"
echo "• Update equipment status"
echo

# Optional: Generate report
if [ "${GENERATE_REPORT:-false}" = "true" ]; then
    echo "📄 Generating Inspection Report..."
    ./arx report generate --building "$BUILDING_ID" --inspector "$INSPECTOR" --date "$DATE"
    echo "✅ Report generated: reports/inspection-$BUILDING_ID-$(date +%Y%m%d).pdf"
fi

echo "🎉 Inspection workflow completed successfully!"
