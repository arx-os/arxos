# ArxOS MVP - Testing Guide

**Quick Start:** 5-10 minutes to see your MVP in action!

---

## Option 1: Automated Test (Fastest - 2 minutes)

### Step 1: Build ArxOS
```bash
cd /Users/joelpate/repos/arxos
go build -o arx ./cmd/arx
```

### Step 2: Run the Integration Test
```bash
./test_mvp_workflow.sh
```

This will:
- Create a test building ("Test School")
- Create Floor 3
- Create 3 rooms with positions
- Add 3 pieces of equipment
- Show you the IDs to use for rendering

### Step 3: Render It
```bash
# Use the building ID from the test output
./arx render <building-id-from-output> --floor 3
```

**Expected result:** Interactive TUI showing floor plan with rooms and equipment!

---

## Option 2: Manual Test (Recommended - 10 minutes)

This lets you see each step and understand how it works.

### Prerequisites

Make sure database is running:
```bash
# Check if PostgreSQL is running
psql -h localhost -U joelpate -d arxos_dev -c "SELECT version();"

# If not running or database doesn't exist:
./scripts/setup-dev-database.sh

# Run migrations if needed
./arx migrate up
```

### Step 1: Build ArxOS
```bash
cd /Users/joelpate/repos/arxos
go build -o arx ./cmd/arx
```

You should see: `arx` binary created (15MB)

### Step 2: Verify ArxOS Works
```bash
./arx health
```

Expected output:
```
✓ Database: Connected
✓ PostGIS: Available
✓ Cache: Ready
✓ System: Operational
```

### Step 3: Create a Building
```bash
./arx building create --name "Main School" --address "123 Main Street"
```

**Copy the Building ID from the output!** (looks like: `abc123def456...`)

Example output:
```
✅ Building created successfully!

   ID:      abc123def456...
   Name:    Main School
   Address: 123 Main Street
```

### Step 4: Create a Floor
```bash
# Replace <building-id> with the ID from Step 3
./arx floor create --building <building-id> --level 3 --name "Third Floor"
```

**Copy the Floor ID from the output!**

### Step 5: Create Rooms with Layout

Now create 3 rooms with positions:

```bash
# Room 301 - Classroom (top-left)
./arx room create --floor <floor-id> --name "Classroom" --number "301" \
  --x 0 --y 0 --width 30 --height 20

# Copy Room 301 ID for equipment later
```

```bash
# IDF-3A - Network Closet (top-right)
./arx room create --floor <floor-id> --name "Network Closet" --number "IDF-3A" \
  --x 35 --y 0 --width 10 --height 10

# Copy IDF-3A ID
```

```bash
# HALL-3A - Hallway (bottom)
./arx room create --floor <floor-id> --name "Hallway" --number "HALL-3A" \
  --x 0 --y 25 --width 50 --height 10

# Copy Hallway ID
```

### Step 6: Add Equipment to Rooms

**Watch the paths auto-generate!** 🎯

```bash
# Add HVAC to classroom
./arx equipment create --name "VAV-301" --type hvac \
  --building <building-id> --floor <floor-id> --room <room-301-id> \
  --x 15 --y 10
```

Look for this line in the output:
```
   Path:     /MAIN-SCHOOL/3/301/HVAC/VAV-301  🎯 (Auto-generated)
```

```bash
# Add network switch to IDF
./arx equipment create --name "SW-01" --type network \
  --building <building-id> --floor <floor-id> --room <idf-id> \
  --x 38 --y 5
```

Expected path: `/MAIN-SCHOOL/3/IDF-3A/NETWORK/SW-01`

```bash
# Add light to hallway
./arx equipment create --name "LIGHT-HALL-1" --type lighting \
  --building <building-id> --floor <floor-id> --room <hallway-id> \
  --x 25 --y 30
```

Expected path: `/MAIN-SCHOOL/3/HALL-3A/LIGHTING/LIGHT-HALL-1`

### Step 7: Verify What You Created

```bash
# List all buildings
./arx building list

# List rooms on floor 3
./arx room list --floor <floor-id>

# List equipment in the building
./arx equipment list --building <building-id>
```

### Step 8: Render the Floor Plan! 🎨

```bash
./arx render <building-id> --floor 3
```

**This launches the interactive TUI!**

You should see:
- Floor 3 layout
- Rooms as ASCII boxes
- Equipment as symbols (H=HVAC, S=Switch, L=Light)
- Real data from your database

**Navigation in TUI:**
- `q` or `Ctrl+C` to quit
- Arrow keys to navigate (if interactive mode is enabled)

---

## Option 3: Test with Real Building (Advanced)

Map a real floor from your workplace:

```bash
# 1. Create your actual building
./arx building create --name "Washington Elementary" --address "Your actual address"

# 2. Create the floor you want to map
./arx floor create --building <id> --level 2 --name "Second Floor"

# 3. Walk through and create rooms
# Use your actual room numbers!
./arx room create --floor <id> --name "Computer Lab" --number "201" \
  --x 0 --y 0 --width 25 --height 20

./arx room create --floor <id> --name "IDF-2A" --number "IDF-2A" \
  --x 30 --y 0 --width 8 --height 8

# 4. Add equipment you actually manage
./arx equipment create --name "SW-CORE-01" --type network \
  --building <building-id> --floor <floor-id> --room <idf-id> \
  --x 34 --y 4

# 5. Render your actual building!
./arx render <building-id> --floor 2
```

---

## Troubleshooting

### Database Connection Issues

```bash
# Check if PostgreSQL is running
pg_isready -h localhost -p 5432

# Check if database exists
psql -h localhost -U joelpate -l | grep arxos_dev

# If database doesn't exist, create it
./scripts/setup-dev-database.sh

# Run migrations
./arx migrate up
```

### Build Issues

```bash
# If build fails, check dependencies
go mod download
go mod tidy

# Try again
go build -o arx ./cmd/arx
```

### Command Not Found

```bash
# Make sure you're using ./arx (local binary)
./arx health

# Or add to PATH
export PATH=$PATH:/Users/joelpate/repos/arxos
arx health
```

### No Render Output

If the TUI doesn't show anything:
- Make sure you created floors and rooms
- Verify floor number matches: `--floor 3`
- Check if data exists: `./arx room list --floor <floor-id>`

---

## Expected Results

### Building Creation
```
✅ Building created successfully!

   ID:      abc123def456789...
   Name:    Main School
   Address: 123 Main Street
```

### Equipment with Path
```
✅ Equipment created successfully!

   ID:       xyz789abc123...
   Name:     VAV-301
   Type:     hvac
   Path:     /MAIN-SCHOOL/3/301/HVAC/VAV-301  🎯 (Auto-generated)
   Building: abc123...
   Floor:    def456...
   Room:     ghi789...
   Location: (15.00, 10.00, 0.00)
   Status:   operational
```

### Room Move
```
✅ Room moved successfully!

   Room:     Classroom (301)
   Position: (10.00, 20.00)
```

### Room Resize
```
✅ Room resized successfully!

   Room:       Classroom (301)
   Dimensions: 40.00 x 25.00 meters
   Area:       1000.00 m²
```

---

## Quick Reference

### Essential Commands
```bash
# Build
go build -o arx ./cmd/arx

# Create structure
./arx building create --name "..." --address "..."
./arx floor create --building <id> --level N --name "..."
./arx room create --floor <id> --name "..." --number "..." --x X --y Y --width W --height H
./arx equipment create --name "..." --type TYPE --building <id> --floor <id> --room <id> --x X --y Y

# List things
./arx building list
./arx floor list --building <id>
./arx room list --floor <id>
./arx equipment list --building <id>

# Modify
./arx room move <room-id> --x 10 --y 20
./arx room resize <room-id> --width 40 --height 25

# Visualize
./arx render <building-id> --floor N
```

### Equipment Types
- `hvac` - HVAC equipment (Symbol: H)
- `electrical` - Electrical equipment (Symbol: E)
- `lighting` - Lights (Symbol: L)
- `plumbing` - Plumbing (Symbol: P)
- `network` - Network equipment (Symbol: S for switch)
- `security` - Security systems
- `fire_safety` - Fire safety equipment

---

## Next Steps

After testing:

1. **If it works well:**
   - Map a real floor from your school
   - Show it to a colleague
   - Gather feedback on the naming convention

2. **If something feels wrong:**
   - Note what doesn't work
   - What would make it more intuitive?
   - What's missing for your actual work?

3. **Decide what to build next:**
   - IFC import for faster building creation?
   - Better visualization?
   - Equipment search by path?
   - Mobile app for field work?

---

## Demo Script for Colleagues

When showing ArxOS to colleagues:

```bash
# 1. Show the concept
echo "ArxOS gives every piece of equipment a universal address"
echo "Like URLs for websites, but for building equipment"
echo

# 2. Create a room they recognize
./arx room create --floor <id> --name "Your Office" --number "205" \
  --x 0 --y 0 --width 20 --height 15

# 3. Add equipment they know
./arx equipment create --name "AP-205" --type network \
  --building <id> --floor <id> --room <id> --x 10 --y 7

# 4. Show the auto-generated path
echo "Notice the path: /SCHOOL/2/205/NETWORK/AP-205"
echo "You can now reference this equipment anywhere in the system"

# 5. Render it
./arx render <building-id> --floor 2
echo "Here's your office with the access point marked!"
```

---

**Have fun testing your MVP!** 🚀

Remember: This is about validating the concept, not building a perfect product. See if the naming convention and CLI feel right for YOUR actual work.

