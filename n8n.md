# ArxOS + n8n Integration: Building Operating System with Workflow Automation

## Executive Summary

ArxOS combined with n8n creates a next-generation BuildingOps platform that enables bidirectional physical automation - not just monitoring but actual control of building systems through visual workflows. This document outlines the architecture for the complete BuildingOps stack: CLI commands, natural language, visual workflows, and physical actions.

**Core Innovation**: Users can control physical building systems through three interfaces:
1. **CLI**: Direct terminal commands (`arx set /B1/3/HVAC/DAMPER-01 position:50`)
2. **Natural Language**: AI-interpreted commands ("Set conference room temperature to 72")
3. **Visual Workflows**: Drag-and-drop n8n workflows that trigger physical actions

**Implementation Philosophy**: ArxOS maintains its pure Go backend with HTMX-powered frontend. n8n integrates via REST APIs, requiring zero JavaScript/TypeScript in the ArxOS codebase.

### Core Value Proposition
- **Path-Based Universal Addressing**: Every building component has a unique, queryable path
- **Workflow Automation**: n8n provides visual workflow builder, ArxOS provides the data
- **Version Control**: Git-like tracking of all building changes
- **Pure Go + HTMX**: No JavaScript framework complexity, just server-side rendering
- **Spatial Intelligence**: Native PostGIS support for location-aware operations

## Architecture Overview

### System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    External Systems                      │
│  (BIM Tools, IoT Sensors, ERP, JIRA, Slack, etc.)       │
└────────────────────┬───────────────────────────┬────────┘
                     │                           │
              ┌──────▼──────┐             ┌──────▼──────┐
              │   n8n       │             │   ArxOS     │
              │  Workflows  │◄────────────►  Go REST API │
              └──────┬──────┘             └──────┬──────┘
                     │                           │
                     │                    ┌──────▼──────┐
                     │                    │ HTMX Web UI │
                     │                    │   (SSR)     │
                     │                    └──────┬──────┘
                     │                           │
              ┌──────▼──────────────────────────▼──────┐
              │         ArxOS Core Database            │
              │     (PostgreSQL + PostGIS)             │
              │                                        │
              │  Buildings → Floors → Rooms → Equipment│
              │  /B1/3/A/301/HVAC/UNIT-01             │
              └────────────────────────────────────────┘
```

### Data Flow Architecture

```yaml
Event Sources:
  - Equipment status changes
  - Scheduled maintenance
  - Sensor readings
  - User actions
  - External APIs

Processing Layer (n8n):
  - Event filtering
  - Path resolution
  - Business logic
  - Integration routing
  - Notification dispatch

ArxOS Core:
  - Path management
  - Spatial queries
  - Version control
  - Access control
  - Data persistence
```

## Path-Based Architecture

### Universal Path Structure

```
/[Building]/[Floor]/[Zone]/[Room]/[System]/[Equipment]/[Component]

Examples:
/B1/3/A/301/HVAC/UNIT-01/FILTER
/CAMPUS-MAIN/2/WEST/CONF-201/ELEC/PANEL-01/BREAKER-15
/HQ/*/NORTH/*/SAFETY/FIRE/*  (wildcards for queries)
```

### Path Metadata Schema

```json
{
  "path": "/B1/3/A/301/HVAC/UNIT-01",
  "type": "equipment",
  "metadata": {
    "manufacturer": "Carrier",
    "model": "50XL-060",
    "serial": "CAR2024001234",
    "installed_date": "2024-01-15",
    "warranty_expires": "2029-01-15",
    "service_interval_days": 90,
    "last_service": "2024-10-01",
    "runtime_hours": 1250,
    "status": "OPERATIONAL",
    "confidence": 95,
    "position": {
      "lat": 40.7128,
      "lon": -74.0060,
      "altitude": 15.5
    }
  },
  "relationships": {
    "parent": "/B1/3/A/301/HVAC",
    "supplies": ["/B1/3/A/301", "/B1/3/A/302"],
    "depends_on": ["/B1/UTILITIES/ELEC/PANEL-03"],
    "maintained_by": "CONTRACTOR-HVAC-01"
  },
  "history": [
    {
      "timestamp": "2024-10-01T09:00:00Z",
      "action": "SERVICE",
      "user": "tech-001",
      "notes": "Quarterly maintenance completed"
    }
  ]
}
```

## n8n Integration Design

### Pure Go REST API for n8n

ArxOS provides REST endpoints that n8n's built-in HTTP Request node can call directly. No custom n8n node development required.

```go
// internal/api/n8n/handlers.go
package n8n

import (
    "encoding/json"
    "net/http"
    "github.com/arx-os/arxos/internal/database"
)

type WorkflowHandler struct {
    db     *database.DB
    cache  *cache.Manager
}

// QueryPath handles equipment queries from n8n workflows
func (h *WorkflowHandler) QueryPath(w http.ResponseWriter, r *http.Request) {
    path := r.URL.Query().Get("path")

    // Support wildcards in path queries
    results, err := h.db.QueryPathPattern(path)
    if err != nil {
        http.Error(w, err.Error(), http.StatusInternalServerError)
        return
    }

    // Return JSON for n8n to process
    w.Header().Set("Content-Type", "application/json")
    json.NewEncoder(w).Encode(results)
}

// CreateWorkOrder creates maintenance work orders from n8n workflows
func (h *WorkflowHandler) CreateWorkOrder(w http.ResponseWriter, r *http.Request) {
    var order WorkOrder
    if err := json.NewDecoder(r.Body).Decode(&order); err != nil {
        http.Error(w, "Invalid request", http.StatusBadRequest)
        return
    }

    // Create work order in database
    id, err := h.db.CreateWorkOrder(order)
    if err != nil {
        http.Error(w, err.Error(), http.StatusInternalServerError)
        return
    }

    // Return created work order ID
    json.NewEncoder(w).Encode(map[string]string{"id": id})
}

// WebhookReceiver handles incoming webhooks from n8n
func (h *WorkflowHandler) WebhookReceiver(w http.ResponseWriter, r *http.Request) {
    var event WorkflowEvent
    json.NewDecoder(r.Body).Decode(&event)

    // Process based on event type
    switch event.Type {
    case "equipment_status_changed":
        h.handleEquipmentStatusChange(event)
    case "maintenance_completed":
        h.handleMaintenanceComplete(event)
    case "sensor_threshold_exceeded":
        h.handleSensorAlert(event)
    }

    w.WriteHeader(http.StatusOK)
}
```

### HTMX-Powered Workflow Management UI

```html
<!-- web/templates/workflows.html -->
<!DOCTYPE html>
<html>
<head>
    <script src="https://unpkg.com/htmx.org@1.9.10"></script>
    <link rel="stylesheet" href="/static/css/arxos.css">
</head>
<body>
    <div class="workflow-dashboard">
        <h1>Workflow Integration</h1>

        <!-- Register n8n Webhook -->
        <div class="card">
            <h2>Connect n8n Workflow</h2>
            <form hx-post="/api/workflows/register"
                  hx-target="#workflow-list tbody"
                  hx-swap="beforeend"
                  hx-on::after-request="this.reset()">
                <input name="name" placeholder="Workflow Name" required>
                <input name="webhook_url" placeholder="n8n Webhook URL" required>
                <select name="trigger_type">
                    <option value="equipment_failure">Equipment Failure</option>
                    <option value="maintenance_due">Maintenance Due</option>
                    <option value="sensor_alert">Sensor Alert</option>
                </select>
                <button type="submit">Connect</button>
            </form>
        </div>

        <!-- Active Workflows -->
        <div class="card">
            <h2>Active Workflows</h2>
            <table id="workflow-list">
                <thead>
                    <tr>
                        <th>Name</th>
                        <th>Type</th>
                        <th>Status</th>
                        <th>Last Run</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody hx-get="/api/workflows"
                       hx-trigger="load, every 10s">
                    <!-- Populated by server -->
                </tbody>
            </table>
        </div>

        <!-- Manual Workflow Trigger -->
        <div class="card">
            <h2>Manual Trigger</h2>
            <form hx-post="/api/workflows/trigger"
                  hx-target="#trigger-result">
                <input name="path"
                       type="text"
                       placeholder="/B1/3/*"
                       hx-get="/api/equipment/autocomplete"
                       hx-trigger="keyup changed delay:500ms"
                       hx-target="#path-suggestions">
                <div id="path-suggestions"></div>

                <select name="workflow_id"
                        hx-get="/api/workflows/list"
                        hx-trigger="load">
                    <!-- Populated by server -->
                </select>

                <button type="submit">Run Workflow</button>
            </form>
            <div id="trigger-result"></div>
        </div>

        <!-- Recent Workflow Executions -->
        <div class="card">
            <h2>Recent Executions</h2>
            <div id="executions"
                 hx-get="/api/workflows/executions"
                 hx-trigger="load, every 5s">
                <!-- Live updates via HTMX -->
            </div>
        </div>
    </div>
</body>
</html>
```

### Go Backend for HTMX UI

```go
// internal/api/workflows/ui_handlers.go
package workflows

import (
    "html/template"
    "net/http"
    "time"
)

// RenderWorkflowList returns HTML partial for HTMX
func (h *Handler) RenderWorkflowList(w http.ResponseWriter, r *http.Request) {
    workflows, _ := h.db.GetActiveWorkflows()

    tmpl := `
    {{range .}}
    <tr id="workflow-{{.ID}}">
        <td>{{.Name}}</td>
        <td>{{.TriggerType}}</td>
        <td>
            {{if .Active}}
            <span class="badge badge-success">Active</span>
            {{else}}
            <span class="badge badge-danger">Inactive</span>
            {{end}}
        </td>
        <td>{{.LastRun.Format "Jan 2, 15:04"}}</td>
        <td>
            <button hx-post="/api/workflows/{{.ID}}/test"
                    hx-target="#test-result-{{.ID}}">
                Test
            </button>
            <button hx-delete="/api/workflows/{{.ID}}"
                    hx-target="#workflow-{{.ID}}"
                    hx-swap="outerHTML swap:1s"
                    hx-confirm="Remove workflow?">
                Remove
            </button>
        </td>
    </tr>
    <tr id="test-result-{{.ID}}" style="display:none"></tr>
    {{end}}
    `

    t := template.Must(template.New("workflows").Parse(tmpl))
    t.Execute(w, workflows)
}

// RegisterWorkflow handles new workflow registration
func (h *Handler) RegisterWorkflow(w http.ResponseWriter, r *http.Request) {
    workflow := Workflow{
        ID:          generateID(),
        Name:        r.FormValue("name"),
        WebhookURL:  r.FormValue("webhook_url"),
        TriggerType: r.FormValue("trigger_type"),
        Active:      true,
        CreatedAt:   time.Now(),
    }

    h.db.SaveWorkflow(workflow)

    // Return HTMX partial for the new row
    tmpl := `
    <tr id="workflow-{{.ID}}" class="htmx-added">
        <td>{{.Name}}</td>
        <td>{{.TriggerType}}</td>
        <td><span class="badge badge-success">Active</span></td>
        <td>Never</td>
        <td>
            <button hx-post="/api/workflows/{{.ID}}/test">Test</button>
            <button hx-delete="/api/workflows/{{.ID}}"
                    hx-target="#workflow-{{.ID}}"
                    hx-swap="outerHTML">
                Remove
            </button>
        </td>
    </tr>
    `

    t := template.Must(template.New("row").Parse(tmpl))
    t.Execute(w, workflow)
}

// AutocompletePath provides path suggestions
func (h *Handler) AutocompletePath(w http.ResponseWriter, r *http.Request) {
    query := r.URL.Query().Get("path")
    suggestions := h.db.GetPathSuggestions(query, 10)

    tmpl := `
    <ul class="suggestions">
    {{range .}}
        <li onclick="document.querySelector('[name=path]').value='{{.}}'">
            {{.}}
        </li>
    {{end}}
    </ul>
    `

    t := template.Must(template.New("suggestions").Parse(tmpl))
    t.Execute(w, suggestions)
}

## Bidirectional Physical Automation

### The BuildingOps Stack

```
┌──────────────────────────────────────────┐
│         User Interfaces                  │
├──────────────────────────────────────────┤
│  CLI Commands │ Natural Language │ n8n UI │
└──────────────┬───────┬──────────┬────────┘
               │       │          │
               ▼       ▼          ▼
         ┌─────────────────────────────┐
         │    ArxOS Path Engine        │
         │  /B1/3/HVAC/DAMPER-01      │
         └──────────┬──────────────────┘
                    │
                    ▼
         ┌─────────────────────────────┐
         │    Gateway Translation      │
         └──────────┬──────────────────┘
                    │
                    ▼
         ┌─────────────────────────────┐
         │   Physical Hardware         │
         │   (Servos, Relays, etc.)   │
         └─────────────────────────────┘
```

### CLI Commands for Physical Control

```bash
# Direct control commands
arx set /B1/3/HVAC/DAMPER-01 position:50
arx set /B1/3/LIGHTS/ZONE-A brightness:75
arx set /B1/3/DOORS/MAIN state:unlocked

# Batch operations
arx set /B1/*/LIGHTS/* state:off
arx set /B1/3/*/HVAC/* mode:eco

# Query before action
arx query /B1/3/SENSORS/TEMP-* --above 75 | arx set --suffix /HVAC/DAMPER mode:cooling

# Natural language (AI-powered)
arx do "turn off all lights on floor 3"
arx do "set conference room to presentation mode"
arx do "lock all exterior doors"

# Workflow triggers
arx workflow trigger emergency-shutdown --building B1
arx workflow run comfort-mode --room /B1/3/CONF-301
```

### Natural Language Processing

```go
// internal/nlp/interpreter.go
package nlp

type CommandInterpreter struct {
    ai     *AIClient
    pathDB *PathDatabase
}

func (ci *CommandInterpreter) ParseNatural(input string) (PathCommand, error) {
    // "Set conference room temperature to 72"
    intent := ci.ai.ExtractIntent(input)

    switch intent.Action {
    case "set_temperature":
        room := ci.findRoom(intent.Location)  // "conference room" → /B1/3/CONF-301
        hvacPath := room + "/HVAC/SETPOINT"
        return PathCommand{
            Path:   hvacPath,
            Action: "set",
            Value:  intent.Value, // 72
        }, nil

    case "lights_scene":
        // "Set presentation mode" → Multiple paths
        return ci.getSceneCommands(intent.Scene)
    }
}
```

### n8n Physical Control Nodes

```yaml
Available Action Nodes:

HVAC Control:
  - Set Temperature (setpoint adjustment)
  - Damper Position (0-100%)
  - Fan Speed (off/low/med/high)
  - Mode (heat/cool/auto/eco)

Lighting Control:
  - Brightness (0-100%)
  - Color Temperature (2700K-6500K)
  - Scene Selection (preset configurations)
  - Zone Control (groups of lights)

Access Control:
  - Door Lock/Unlock
  - Access Schedule Override
  - Emergency Lockdown
  - Badge Reader Enable/Disable

Motor Control:
  - Blind/Shade Position
  - Valve Position
  - Gate Control
  - Ventilation Louvers
```

### Safety and Validation Layer

```go
// internal/control/safety.go
package control

type SafetyValidator struct {
    interlocks map[string][]string
}

func (sv *SafetyValidator) ValidateCommand(cmd PathCommand) error {
    // Check safety interlocks
    if cmd.Path == "/B1/FIRE_DOORS/*" && sv.fireAlarmActive {
        return ErrSafetyInterlock("fire doors locked during alarm")
    }

    // Validate operational ranges
    if strings.Contains(cmd.Path, "/HVAC/SETPOINT") {
        temp := cmd.Value.(float64)
        if temp < 60 || temp > 85 {
            return ErrOutOfRange("temperature must be 60-85°F")
        }
    }

    // Rate limiting for mechanical equipment
    if sv.recentlyActuated(cmd.Path) {
        return ErrRateLimit("equipment cooldown period")
    }

    return nil
}
```

## CMMS/CAFM Features via Workflows

### Core CMMS Workflows

#### 1. Work Order Management
```yaml
Workflow: Equipment Failure to Work Order
Trigger: Webhook - equipment.status.changed
Steps:
  1. Check if status = FAILED
  2. Query ArxOS for equipment metadata
  3. Determine priority based on equipment type
  4. Query available technicians by skill
  5. Create work order with:
     - Equipment path
     - Failure description
     - Priority level
     - Assigned technician
     - Due date
  6. Send notifications (email, SMS, Slack)
  7. Create calendar event
  8. Log to audit trail
```

#### 2. Preventive Maintenance
```yaml
Workflow: PM Schedule Generator
Trigger: Schedule - Daily at 6 AM
Steps:
  1. Query all equipment paths: /*/*/*/*/*
  2. For each equipment:
     - Check last_service date
     - Compare with service_interval
     - Calculate next_service date
  3. If due within 7 days:
     - Create PM work order
     - Assign to technician pool
     - Add to maintenance calendar
  4. Generate weekly PM report
  5. Send to maintenance manager
```

#### 3. Asset Lifecycle Management
```yaml
Workflow: Warranty Expiration Monitor
Trigger: Schedule - Weekly
Steps:
  1. Query all equipment with warranty_expires
  2. Filter: expires within 60 days
  3. For each expiring warranty:
     - Check maintenance history
     - Calculate total repair costs
     - Determine replace vs renew
  4. Generate recommendations
  5. Create procurement requests
  6. Update budget forecasts
```

### Advanced CAFM Workflows

#### 1. Space Utilization
```yaml
Workflow: Occupancy-Based HVAC Optimization
Trigger: Every 15 minutes
Steps:
  1. Query occupancy sensors: /*/SENSORS/OCCUPANCY/*
  2. Map to room paths
  3. For each room:
     - If occupied: Set HVAC to comfort mode
     - If vacant > 30min: Set to eco mode
  4. Calculate energy savings
  5. Update dashboard metrics
```

#### 2. Compliance Management
```yaml
Workflow: Fire Safety Compliance Check
Trigger: Monthly - 1st Monday
Steps:
  1. Query all fire safety equipment: /*/SAFETY/FIRE/*
  2. Check inspection dates
  3. Verify certifications
  4. Generate inspection tasks for expired items
  5. Create compliance report
  6. If critical failures:
     - Alert safety officer immediately
     - Create emergency work orders
  7. Submit to regulatory portal
```

## Implementation Roadmap

### Phase 1: Foundation (Months 1-2)
- [ ] Extend Go REST API for n8n integration
- [ ] Build HTMX workflow management UI
- [ ] Implement webhook system in Go
- [ ] Create path query endpoints
- [ ] Add JWT authentication for API access

### Phase 2: Core CMMS (Months 3-4)
- [ ] Work order data model (Go structs + PostgreSQL)
- [ ] HTMX work order management interface
- [ ] Go handlers for PM scheduling
- [ ] Technician assignment via HTMX forms
- [ ] Email/SMS notifications (Go packages)

### Phase 3: Advanced Features (Months 5-6)
- [ ] Spatial query endpoints (PostGIS)
- [ ] HTMX dashboard with real-time updates
- [ ] Energy optimization calculations (Go)
- [ ] Compliance reporting (Go templates)
- [ ] Progressive web app with HTMX

### Phase 4: Enterprise Features (Months 7-8)
- [ ] Multi-tenant database schema
- [ ] RBAC middleware in Go
- [ ] Workflow template marketplace (HTMX UI)
- [ ] Enterprise API integrations
- [ ] PDF report generation (Go)

## Workflow Template Library

### Maintenance Templates
```
1. emergency-response.json
   - Triggered by critical equipment failure
   - Pages on-call technician
   - Creates incident report

2. seasonal-maintenance.json
   - Triggered quarterly
   - HVAC filter changes
   - Cooling tower cleaning

3. regulatory-inspection.json
   - Monthly compliance checks
   - Auto-generates reports
   - Files with authorities
```

### Energy Management Templates
```
1. demand-response.json
   - Monitors grid pricing
   - Adjusts building loads
   - Optimizes energy costs

2. peak-shaving.json
   - Predicts daily peaks
   - Pre-cools/heats building
   - Reduces demand charges
```

### Security & Safety Templates
```
1. access-control-audit.json
   - Reviews access logs
   - Identifies anomalies
   - Updates permissions

2. emergency-evacuation.json
   - Triggered by fire alarm
   - Locks/unlocks doors
   - Guides to exits
```

## Technical Specifications

### Go API Implementation

```go
// internal/api/routes.go
package api

import (
    "github.com/go-chi/chi/v5"
    "github.com/arx-os/arxos/internal/api/workflows"
    "github.com/arx-os/arxos/internal/api/equipment"
    "github.com/arx-os/arxos/internal/api/workorders"
)

func RegisterRoutes(r chi.Router) {
    // Path Operations - RESTful endpoints for n8n
    r.Route("/api/v1/path", func(r chi.Router) {
        r.Get("/{path}", equipment.GetByPath)
        r.Put("/{path}", equipment.UpdateByPath)
        r.Delete("/{path}", equipment.DeleteByPath)
        r.Post("/query", equipment.QueryPaths)
    })

    // Workflow Integration - HTMX + n8n endpoints
    r.Route("/api/v1/workflows", func(r chi.Router) {
        r.Post("/register", workflows.RegisterWorkflow)
        r.Get("/", workflows.RenderWorkflowList)  // Returns HTML for HTMX
        r.Delete("/{id}", workflows.DeleteWorkflow)
        r.Post("/trigger", workflows.TriggerWorkflow)
        r.Get("/executions", workflows.RenderExecutions) // Live updates
    })

    // Work Orders - Mixed JSON/HTML responses
    r.Route("/api/v1/work-orders", func(r chi.Router) {
        r.Post("/", workorders.Create)
        r.Get("/{id}", workorders.Get)
        r.Put("/{id}", workorders.Update)
        r.Get("/by-path/{path}", workorders.GetByPath)

        // HTMX endpoints
        r.Get("/list", workorders.RenderList)
        r.Get("/{id}/edit-form", workorders.RenderEditForm)
    })
}
```

### Database Schema Extensions

```sql
-- Work Orders table
CREATE TABLE work_orders (
  id UUID PRIMARY KEY,
  path TEXT NOT NULL,              -- Equipment path
  type TEXT NOT NULL,              -- CORRECTIVE, PREVENTIVE, PREDICTIVE
  priority TEXT NOT NULL,          -- CRITICAL, HIGH, MEDIUM, LOW
  status TEXT NOT NULL,            -- OPEN, ASSIGNED, IN_PROGRESS, COMPLETE
  description TEXT,
  assigned_to TEXT,
  created_at TIMESTAMP,
  due_date TIMESTAMP,
  completed_at TIMESTAMP,
  workflow_id TEXT,                -- n8n workflow that created it
  metadata JSONB
);

-- Workflow Registry
CREATE TABLE workflow_registry (
  id UUID PRIMARY KEY,
  workflow_id TEXT UNIQUE,         -- n8n workflow ID
  name TEXT NOT NULL,
  description TEXT,
  trigger_type TEXT,               -- WEBHOOK, SCHEDULE, MANUAL
  trigger_config JSONB,
  active BOOLEAN DEFAULT true,
  created_at TIMESTAMP
);

-- Event Subscriptions
CREATE TABLE webhook_subscriptions (
  id UUID PRIMARY KEY,
  event_type TEXT NOT NULL,
  path_pattern TEXT,               -- Optional path filter
  webhook_url TEXT NOT NULL,
  active BOOLEAN DEFAULT true,
  created_at TIMESTAMP
);
```

## CSS Styling for HTMX UI

```css
/* web/static/css/arxos.css */

/* Modern, clean design with CSS Grid and Flexbox */
:root {
    --primary: #2563eb;
    --success: #10b981;
    --danger: #ef4444;
    --warning: #f59e0b;
    --dark: #1f2937;
    --light: #f3f4f6;
    --border: #e5e7eb;
}

/* Workflow Dashboard Layout */
.workflow-dashboard {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
    gap: 2rem;
    padding: 2rem;
    background: var(--light);
}

.card {
    background: white;
    border-radius: 8px;
    padding: 1.5rem;
    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    transition: transform 0.2s;
}

.card:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
}

/* HTMX Loading States */
.htmx-request .htmx-indicator {
    opacity: 1;
}

.htmx-settling {
    opacity: 0.5;
}

.htmx-added {
    animation: slideIn 0.3s ease-out;
}

@keyframes slideIn {
    from {
        opacity: 0;
        transform: translateX(-20px);
    }
    to {
        opacity: 1;
        transform: translateX(0);
    }
}

/* Path Autocomplete */
.suggestions {
    position: absolute;
    background: white;
    border: 1px solid var(--border);
    border-radius: 4px;
    max-height: 200px;
    overflow-y: auto;
    z-index: 1000;
}

.suggestions li {
    padding: 0.5rem 1rem;
    cursor: pointer;
    transition: background 0.2s;
}

.suggestions li:hover {
    background: var(--light);
}

/* Status Badges */
.badge {
    display: inline-block;
    padding: 0.25rem 0.75rem;
    border-radius: 9999px;
    font-size: 0.875rem;
    font-weight: 600;
}

.badge-success {
    background: #d1fae5;
    color: #065f46;
}

.badge-danger {
    background: #fee2e2;
    color: #991b1b;
}

/* Responsive Tables */
@media (max-width: 768px) {
    table {
        display: block;
        overflow-x: auto;
    }
}
```

## Security Considerations

### Go Security Implementation

```go
// internal/middleware/auth.go
package middleware

import (
    "net/http"
    "strings"
    "github.com/golang-jwt/jwt/v4"
)

// JWTAuth middleware for API endpoints
func JWTAuth(next http.Handler) http.Handler {
    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        // Check if request is from n8n (webhook)
        if webhookKey := r.Header.Get("X-Webhook-Key"); webhookKey != "" {
            if validateWebhookKey(webhookKey) {
                next.ServeHTTP(w, r)
                return
            }
        }

        // Standard JWT validation
        authHeader := r.Header.Get("Authorization")
        if authHeader == "" {
            http.Error(w, "Missing auth token", http.StatusUnauthorized)
            return
        }

        tokenString := strings.Replace(authHeader, "Bearer ", "", 1)
        token, err := jwt.Parse(tokenString, func(token *jwt.Token) (interface{}, error) {
            return []byte(getJWTSecret()), nil
        })

        if err != nil || !token.Valid {
            http.Error(w, "Invalid token", http.StatusUnauthorized)
            return
        }

        next.ServeHTTP(w, r)
    })
}

// RateLimiter for API protection
func RateLimiter(requests int, per time.Duration) func(http.Handler) http.Handler {
    limiter := rate.NewLimiter(rate.Every(per/time.Duration(requests)), requests)

    return func(next http.Handler) http.Handler {
        return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
            if !limiter.Allow() {
                http.Error(w, "Rate limit exceeded", http.StatusTooManyRequests)
                return
            }
            next.ServeHTTP(w, r)
        })
    }
}

## Performance Optimization

### Go-Based Caching Strategy

```go
// internal/cache/manager.go
package cache

import (
    "time"
    "github.com/dgraph-io/ristretto"
)

type CacheManager struct {
    cache *ristretto.Cache
}

func NewCacheManager() *CacheManager {
    cache, _ := ristretto.NewCache(&ristretto.Config{
        NumCounters: 1e7,     // 10 million
        MaxCost:     1 << 30, // 1GB
        BufferItems: 64,
    })

    return &CacheManager{cache: cache}
}

// CachePath caches equipment path queries
func (c *CacheManager) CachePath(path string, data interface{}) {
    c.cache.SetWithTTL(path, data, 1, 5*time.Minute)
}

// GetPath retrieves cached path data
func (c *CacheManager) GetPath(path string) (interface{}, bool) {
    return c.cache.Get(path)
}
```

### HTMX Performance Features

```html
<!-- Lazy loading with HTMX -->
<div hx-get="/api/equipment/large-list"
     hx-trigger="revealed"
     hx-indicator="#loading">
    <!-- Content loads when scrolled into view -->
</div>

<!-- Debounced search for better performance -->
<input type="search"
       name="q"
       hx-get="/api/search"
       hx-trigger="keyup changed delay:500ms"
       hx-target="#results">

<!-- Polling with exponential backoff -->
<div hx-get="/api/status"
     hx-trigger="every 2s [isActive], every 30s [!isActive]">
    <!-- Adaptive polling based on activity -->
</div>
```

## Success Metrics

### Technical KPIs
- API response time < 200ms
- Workflow execution time < 5s
- System uptime > 99.9%
- Path query performance < 100ms

### Business KPIs
- Work order completion time -30%
- Preventive vs reactive ratio 80:20
- Energy costs reduced by 15%
- Compliance violations: 0

## Competitive Analysis

| Feature | Traditional CMMS | ArxOS + n8n |
|---------|-----------------|-------------|
| Pricing | $100-500/user/month | Open source core |
| Customization | Expensive consultants | Visual workflow builder |
| Integrations | Limited, costly | 400+ out of box |
| API Access | Limited | Everything is API |
| Spatial Awareness | Bolt-on GIS | Native PostGIS |
| Version Control | None | Git-like history |
| Automation | Basic | Full workflow engine |

## Future Enhancements

### AI Integration
- Natural language to path queries
- Predictive failure analysis
- Automated workflow optimization
- Energy usage prediction

### IoT Integration
- Direct sensor integration
- Real-time digital twin
- Edge computing support
- LoRaWAN/NB-IoT support

### Advanced Analytics
- Custom dashboard builder
- ML-based insights
- Benchmarking across buildings
- ROI tracking

## Example n8n Workflow Configuration

Since n8n uses its built-in HTTP Request node to call ArxOS APIs, here's how to configure workflows:

### Equipment Failure Workflow in n8n

```json
{
  "name": "Equipment Failure Handler",
  "nodes": [
    {
      "name": "Webhook",
      "type": "n8n-nodes-base.webhook",
      "parameters": {
        "path": "equipment-failure",
        "responseMode": "onReceived",
        "options": {}
      }
    },
    {
      "name": "Query ArxOS",
      "type": "n8n-nodes-base.httpRequest",
      "parameters": {
        "method": "GET",
        "url": "https://arxos.example.com/api/v1/path/{{$json.path}}",
        "authentication": "genericCredentialType",
        "genericAuthType": "httpHeaderAuth",
        "options": {}
      }
    },
    {
      "name": "Create Work Order",
      "type": "n8n-nodes-base.httpRequest",
      "parameters": {
        "method": "POST",
        "url": "https://arxos.example.com/api/v1/work-orders",
        "bodyParametersJson": {
          "path": "={{$json.path}}",
          "priority": "={{$json.equipment.critical ? 'HIGH' : 'MEDIUM'}}",
          "description": "Equipment failure detected",
          "type": "CORRECTIVE"
        }
      }
    },
    {
      "name": "Notify Technician",
      "type": "n8n-nodes-base.slack",
      "parameters": {
        "channel": "#maintenance",
        "text": "🚨 Equipment failure at {{$json.path}}"
      }
    }
  ]
}
```

## Deployment Architecture

### Docker Compose Setup

```yaml
# docker-compose.yml
version: '3.8'

services:
  arxos:
    build: .
    ports:
      - "8080:8080"
    environment:
      - DATABASE_URL=postgres://arxos:password@db:5432/arxos
      - JWT_SECRET=${JWT_SECRET}
      - N8N_WEBHOOK_KEY=${N8N_WEBHOOK_KEY}
    depends_on:
      - db
    volumes:
      - ./web:/app/web  # HTMX templates

  db:
    image: postgis/postgis:16-3.4
    environment:
      - POSTGRES_DB=arxos
      - POSTGRES_USER=arxos
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data

  n8n:
    image: n8nio/n8n
    ports:
      - "5678:5678"
    environment:
      - N8N_BASIC_AUTH_ACTIVE=true
      - N8N_BASIC_AUTH_USER=admin
      - N8N_BASIC_AUTH_PASSWORD=${N8N_PASSWORD}
    volumes:
      - n8n_data:/home/node/.n8n

volumes:
  postgres_data:
  n8n_data:
```

## Conclusion

The ArxOS + n8n integration represents a paradigm shift in building management, combining the simplicity and performance of Go + HTMX with the flexibility of n8n's workflow automation.

This pure Go + HTMX/CSS architecture provides:

1. **Simplicity**: No JavaScript framework complexity, just server-side rendering
2. **Performance**: Go's efficiency + HTMX's minimal overhead
3. **Maintainability**: Single language (Go) for entire backend
4. **Real-time Updates**: HTMX provides live UI without WebSockets
5. **Integration Ready**: REST APIs that n8n calls directly

The path-based architecture combined with visual workflow automation creates a powerful, maintainable platform that modernizes building management without the complexity of traditional enterprise CMMS/CAFM systems.