#!/bin/bash
# Equipment Monitoring Workflow Example
# This script demonstrates continuous equipment monitoring using ArxOS TUI

set -e

echo "⚙️  ArxOS Equipment Monitoring Workflow"
echo "======================================"
echo

# Configuration
BUILDING_ID="${1:-ARXOS-001}"
MONITORING_INTERVAL="${2:-30}"
ALERT_THRESHOLD="${3:-5}"

echo "Building ID: $BUILDING_ID"
echo "Monitoring Interval: $MONITORING_INTERVAL seconds"
echo "Alert Threshold: $ALERT_THRESHOLD equipment"
echo

# Set TUI configuration for monitoring
export ARXOS_TUI_ENABLED="true"
export ARXOS_TUI_THEME="dark"
export ARXOS_TUI_UPDATE_INTERVAL="1s"
export ARXOS_TUI_MAX_EQUIPMENT="1000"
export ARXOS_TUI_REAL_TIME="true"
export ARXOS_TUI_ANIMATIONS="true"
export ARXOS_TUI_COMPACT_MODE="false"

echo "🔧 TUI Configuration:"
echo "   Theme: ${ARXOS_TUI_THEME}"
echo "   Update Interval: ${ARXOS_TUI_UPDATE_INTERVAL}"
echo "   Max Equipment: ${ARXOS_TUI_MAX_EQUIPMENT}"
echo "   Real-time: ${ARXOS_TUI_REAL_TIME}"
echo "   Animations: ${ARXOS_TUI_ANIMATIONS}"
echo

# Function to check equipment status
check_equipment_status() {
    local building_id="$1"
    local alert_count=0
    
    echo "🔍 Checking equipment status for building $building_id..."
    
    # Get equipment status (this would be an API call in real implementation)
    # For demo purposes, we'll simulate the check
    local total_equipment=150
    local operational=140
    local maintenance=8
    local offline=2
    
    echo "   Total Equipment: $total_equipment"
    echo "   Operational: $operational"
    echo "   Maintenance: $maintenance"
    echo "   Offline: $offline"
    
    # Check for alerts
    if [ $offline -gt 0 ]; then
        alert_count=$((alert_count + offline))
        echo "   ⚠️  $offline equipment offline"
    fi
    
    if [ $maintenance -gt 5 ]; then
        alert_count=$((alert_count + maintenance - 5))
        echo "   ⚠️  $((maintenance - 5)) equipment overdue for maintenance"
    fi
    
    if [ $alert_count -ge $ALERT_THRESHOLD ]; then
        echo "   🚨 ALERT: $alert_count equipment issues detected!"
        return 1
    else
        echo "   ✅ Equipment status normal"
        return 0
    fi
}

# Function to run monitoring cycle
run_monitoring_cycle() {
    local cycle="$1"
    
    echo "🔄 Monitoring Cycle $cycle"
    echo "========================="
    echo "Time: $(date)"
    echo
    
    # Check equipment status
    if ! check_equipment_status "$BUILDING_ID"; then
        echo "🚨 Alert detected! Starting TUI for investigation..."
        echo
        
        # Start TUI dashboard for investigation
        echo "Starting TUI Dashboard for investigation..."
        echo "Use the following controls:"
        echo "• Tab - Switch between tabs"
        echo "• ↑↓ - Navigate equipment list"
        echo "• r - Refresh data"
        echo "• q - Quit when investigation complete"
        echo
        
        ./arx visualize --tui --building "$BUILDING_ID" || true
        
        echo "Investigation completed. Continuing monitoring..."
    else
        echo "✅ No alerts detected. Equipment status normal."
    fi
    
    echo
}

# Function to run equipment manager for detailed analysis
run_equipment_analysis() {
    echo "🔍 Detailed Equipment Analysis"
    echo "=============================="
    echo "Starting Equipment Manager for detailed analysis..."
    echo
    echo "Use the following controls:"
    echo "• t - Filter by equipment type"
    echo "• s - Filter by status"
    echo "• / - Search for specific equipment"
    echo "• r - Refresh data"
    echo "• q - Quit when analysis complete"
    echo
    
    ./arx visualize equipment --tui --building "$BUILDING_ID" || true
    
    echo "Equipment analysis completed."
    echo
}

# Function to run spatial analysis
run_spatial_analysis() {
    echo "🗺️  Spatial Analysis"
    echo "==================="
    echo "Starting Spatial Query Interface for location analysis..."
    echo
    echo "Use the following controls:"
    echo "• Tab - Switch between query types"
    echo "• ↑↓ - Navigate query options"
    echo "• ←→ - Adjust parameters"
    echo "• Enter - Execute query"
    echo "• q - Quit when analysis complete"
    echo
    
    ./arx visualize query --tui --building "$BUILDING_ID" || true
    
    echo "Spatial analysis completed."
    echo
}

# Main monitoring loop
echo "🚀 Starting Equipment Monitoring"
echo "==============================="
echo "Press Ctrl+C to stop monitoring"
echo

# Initial equipment check
check_equipment_status "$BUILDING_ID"

# Monitoring loop
cycle=1
while true; do
    echo "⏰ Waiting $MONITORING_INTERVAL seconds for next check..."
    sleep "$MONITORING_INTERVAL"
    
    run_monitoring_cycle "$cycle"
    
    # Every 10 cycles, run detailed analysis
    if [ $((cycle % 10)) -eq 0 ]; then
        echo "📊 Detailed Analysis Cycle (every 10 cycles)"
        echo "=========================================="
        echo
        
        read -p "Press Enter to start detailed equipment analysis..."
        run_equipment_analysis
        
        read -p "Press Enter to start spatial analysis..."
        run_spatial_analysis
    fi
    
    cycle=$((cycle + 1))
done
