# Arxos Quick Start - 5 Minutes to Running

> **From zero to Google Maps for Buildings in 5 minutes. No npm. No build steps. Just run.**

## Prerequisites

You only need:
- Go 1.21+
- PostgreSQL with PostGIS
- A web browser

That's it. No Node.js, no Python, no complex toolchain.

## Option 1: Docker (Easiest)

```bash
# Clone the repo
git clone https://github.com/arxos/arxos.git
cd arxos

# Start everything
docker-compose up -d

# Open your browser
open http://localhost
```

✅ **Done!** You're now running Arxos.

## Option 2: Local Development

### 1. Database Setup (One Time)

```bash
# Create database
createdb arxos

# Enable PostGIS
psql arxos -c "CREATE EXTENSION postgis;"

# Load schema
psql arxos < infrastructure/database/001_create_arx_schema.sql
```

### 2. Start Backend

```bash
# From project root
cd core/backend

# Run the Go server (no build needed for development)
go run main.go

# Server now running at http://localhost:8080
```

### 3. Open Frontend

```bash
# From project root
cd frontend/web

# Just open the HTML file!
open index.html

# Or use any local server
python3 -m http.server 3000
# Then open http://localhost:3000
```

✅ **That's it!** No npm install, no webpack, no build process.

## What You'll See

When you open Arxos, you'll see:

1. **Main Viewport** - Like Google Maps, but for buildings
2. **Scale Indicator** - Shows current zoom level (ROOM, FLOOR, BUILDING, etc.)
3. **System Toggles** - Press 1-4 to toggle Electrical/HVAC/Plumbing/Structural
4. **Controls**:
   - **Scroll** to zoom in/out
   - **Drag** to pan around
   - **Click** objects to select
   - **F** to fit view

## Making Changes

### Frontend Changes

```bash
# Edit the vanilla JS
vim frontend/web/static/js/arxos-core.js

# Refresh your browser
# Changes appear instantly!
```

### Backend Changes

```bash
# Edit Go code
vim core/backend/main.go

# Restart server (Ctrl+C, then run again)
go run main.go

# Changes ready!
```

### Database Changes

```bash
# Add test data
psql arxos << SQL
INSERT INTO arx_objects (type, system, geom, scale_min, scale_max)
VALUES 
  ('outlet', 'electrical', ST_MakePoint(-73.9857, 40.7484, 0), 1, 100),
  ('diffuser', 'hvac', ST_MakePoint(-73.9856, 40.7485, 3), 1, 100);
SQL
```

## Project Structure

```
arxos/
├── core/
│   ├── backend/          # Go backend (main.go)
│   └── arxobject/        # ArxObject engine
├── frontend/
│   └── web/
│       ├── index.html    # Single HTML file
│       └── static/js/
│           └── arxos-core.js  # 400 lines of vanilla JS
├── infrastructure/
│   └── database/         # SQL schemas
├── docker-compose.yml    # One-command setup
└── README.md            # You are here
```

## Common Tasks

### Add a New ArxObject Type

1. **Backend** - Add to `arxobject.go`:
```go
const (
    NewType ArxObjectType = iota
    // ...
)
```

2. **Frontend** - Add to rendering:
```javascript
createShape(arxObject) {
    if (arxObject.type === 'newtype') {
        // Create SVG for new type
    }
}
```

3. **Database** - Insert test data:
```sql
INSERT INTO arx_objects (type, system, geom)
VALUES ('newtype', 'electrical', ST_MakePoint(x, y, z));
```

### Add a New Scale Level

Edit `arxos-core.js`:
```javascript
scaleLevels: {
    MICROSCOPIC: { min: 0.0001, max: 0.001 },
    // your new level
}
```

### Change Colors/Styling

Edit `index.html`:
```css
.system-toggle.electrical.active { 
    border-color: #FFD700;  /* Change this */
}
```

## Testing

### Quick Smoke Test

```bash
# Backend health check
curl http://localhost:8080/health

# Get some ArxObjects
curl http://localhost:8080/api/arxobjects

# WebSocket test
wscat -c ws://localhost:8080/ws
```

### Load Testing

```bash
# Simple load test with Apache Bench
ab -n 1000 -c 10 http://localhost:8080/api/arxobjects
```

## Production Build

```bash
# Build single Go binary
CGO_ENABLED=0 go build -o arxos core/backend/main.go

# That's it! Deploy this binary + static files
scp arxos user@server:/usr/local/bin/
scp -r frontend/web/* user@server:/var/www/arxos/
```

## Troubleshooting

### "Cannot connect to database"
```bash
# Check PostgreSQL is running
pg_isready

# Check database exists
psql -l | grep arxos
```

### "Port 8080 already in use"
```bash
# Use different port
PORT=3000 go run main.go
```

### "No ArxObjects showing"
```bash
# Check there's data
psql arxos -c "SELECT COUNT(*) FROM arx_objects;"

# Insert test data
psql arxos < infrastructure/database/sample_data.sql
```

## Next Steps

1. **Read ARCHITECTURE.md** - Understand the system design
2. **Check ENGINEERING_TODO.md** - See what needs building
3. **Load Sample Building** - Import a PDF floor plan
4. **Start Contributing** - Pick a task and PR!

## Remember

- **No frameworks** - Just Go, vanilla JS, PostgreSQL
- **No build process** - Edit and refresh
- **No complexity** - If it seems complex, we're doing it wrong

The entire Google Maps for Buildings vision runs with:
- 1 Go file (`main.go`)
- 1 HTML file (`index.html`)
- 1 JS file (`arxos-core.js`)
- 1 Database (PostgreSQL + PostGIS)

**That's the beauty of simplicity.**