#!/bin/bash

# ArxOS Demo Script
# Demonstrates the basic workflow of importing, viewing, and marking equipment

# Navigate to project root
cd "$(dirname "$0")/.." || exit 1

echo "ArxOS Phase 1 Demo"
echo "=================="
echo

# Build the application
echo "Building ArxOS..."
go build -o arx cmd/arx/main.go || exit 1
echo "✓ Build complete"
echo

# Create a mock floor plan
echo "Creating demo floor plan..."
mkdir -p .arxos
cat > .arxos/demo_floor.json << 'EOF'
{
  "name": "Floor 2",
  "building": "Building 42",
  "level": 2,
  "rooms": [
    {
      "id": "room_2a",
      "name": "Room 2A",
      "bounds": {"min_x": 0, "min_y": 0, "max_x": 10, "max_y": 10},
      "equipment": ["outlet_2a_1", "outlet_2a_2", "outlet_2a_3"]
    },
    {
      "id": "room_2b",
      "name": "Room 2B",
      "bounds": {"min_x": 10, "min_y": 0, "max_x": 20, "max_y": 10},
      "equipment": ["outlet_2b_1", "outlet_2b_2", "outlet_2b_3"]
    },
    {
      "id": "mech",
      "name": "Mechanical",
      "bounds": {"min_x": 20, "min_y": 0, "max_x": 25, "max_y": 10},
      "equipment": ["panel_1"]
    }
  ],
  "equipment": [
    {
      "id": "outlet_2a_1",
      "name": "Outlet 2A-1",
      "type": "outlet",
      "location": {"x": 2, "y": 5},
      "room_id": "room_2a",
      "status": "normal",
      "notes": "",
      "marked_by": "",
      "marked_at": "0001-01-01T00:00:00Z"
    },
    {
      "id": "outlet_2a_2",
      "name": "Outlet 2A-2",
      "type": "outlet",
      "location": {"x": 5, "y": 5},
      "room_id": "room_2a",
      "status": "normal",
      "notes": "",
      "marked_by": "",
      "marked_at": "0001-01-01T00:00:00Z"
    },
    {
      "id": "outlet_2a_3",
      "name": "Outlet 2A-3",
      "type": "outlet",
      "location": {"x": 8, "y": 5},
      "room_id": "room_2a",
      "status": "normal",
      "notes": "",
      "marked_by": "",
      "marked_at": "0001-01-01T00:00:00Z"
    },
    {
      "id": "outlet_2b_1",
      "name": "Outlet 2B-1",
      "type": "outlet",
      "location": {"x": 12, "y": 5},
      "room_id": "room_2b",
      "status": "normal",
      "notes": "",
      "marked_by": "",
      "marked_at": "0001-01-01T00:00:00Z"
    },
    {
      "id": "outlet_2b_2",
      "name": "Outlet 2B-2",
      "type": "outlet",
      "location": {"x": 15, "y": 5},
      "room_id": "room_2b",
      "status": "normal",
      "notes": "",
      "marked_by": "",
      "marked_at": "0001-01-01T00:00:00Z"
    },
    {
      "id": "outlet_2b_3",
      "name": "Outlet 2B-3",
      "type": "outlet",
      "location": {"x": 18, "y": 5},
      "room_id": "room_2b",
      "status": "failed",
      "notes": "",
      "marked_by": "",
      "marked_at": "0001-01-01T00:00:00Z"
    },
    {
      "id": "panel_1",
      "name": "Panel 1",
      "type": "panel",
      "location": {"x": 22, "y": 5},
      "room_id": "mech",
      "status": "normal",
      "notes": "",
      "marked_by": "",
      "marked_at": "0001-01-01T00:00:00Z"
    }
  ],
  "created_at": "2024-01-15T10:00:00Z",
  "updated_at": "2024-01-15T10:00:00Z"
}
EOF
echo "✓ Demo floor plan created"
echo

# Demonstrate commands
echo "1. List available floor plans:"
echo "   $ ./arx list"
./arx list
echo

echo "2. Display ASCII map:"
echo "   $ ./arx map demo_floor"
./arx map demo_floor
echo

echo "3. Show equipment status:"
echo "   $ ./arx status demo_floor"
./arx status demo_floor
echo

echo "4. Mark equipment as needing repair:"
echo "   $ ./arx mark outlet_2b_1 --status needs-repair --notes 'Intermittent ground fault' --floor demo_floor"
./arx mark outlet_2b_1 --status needs-repair --notes "Intermittent ground fault" --floor demo_floor
echo

echo "5. View updated map:"
echo "   $ ./arx map demo_floor"
./arx map demo_floor
echo

echo "6. Show updated status:"
echo "   $ ./arx status demo_floor"
./arx status demo_floor
echo

echo "Demo complete! The marked changes are saved in .arxos/demo_floor.json"
echo
echo "Next steps for Phase 1:"
echo "  - Implement real PDF parsing"
echo "  - Add PDF export with markups"
echo "  - Integrate with Git for version control"