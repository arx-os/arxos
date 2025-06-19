# Arxline

**Arxline** is a Building Information System (BIS) offered as a Software-as-a-Service (SaaS). Our platform empowers building professionals to collaboratively document and manage the physical infrastructure of buildings using scalable, editable SVG maps as a central canvas.

We are currently in the **Minimum Viable Product (MVP)** development phase.

---------------------------------------------------------------

## 📌 Project Overview

Arxline's core innovation is its SVG-based building canvas. Each building is represented as one or more SVG files, which serve as the "as-built" or "redline" drawings. These are updated collaboratively by contributors based on the work they've performed on-site.

Users contribute to the SVG in one of the following ways:
- Uploading construction documents for parsing and conversion.
- Drawing directly via a markup interface (browser-based or mobile).
- Using virtual measurements via Augmented Reality (AR).

Each element (e.g., outlets, lights, pipes) is placed and scaled accurately on the SVG's mathematical grid to align with real-world spatial orientation.

---------------------------------------------------------------

## 🧠 Product Vision

Arxline is the **central nervous system** for building infrastructure:

- **Owners/Managers** maintain a digital twin of their properties, accessible and editable in real-time.
- **Builders/Contractors** document their work visually on the map as a persistent, verified layer.
- **Guests** gain access to view and interpret the infrastructure without altering it.

### Floor & Building Representation

- Each **building address** maps to a single SVG canvas.
- Separate buildings = separated visually in the same SVG canvas.
- **Multi-floor buildings** = multiple SVGs, one per floor.
- Floor selection is handled via a UI tab system.

----------------------------------------------------------------

## 🧱 Architecture

| Layer                     | Technology Stack                |
|---------------------------|---------------------------------|
| **Frontend**              | HTML/X, Tailwind CSS            |
| **Backend**               | Go (Chi framework)              |
| **Microservices**      | Python (SVG Parser, File Ingestion)|
| **Database**              | PostgreSQL with PostGIS         |
| **Cloud**                 | DigitalOcean, Azure             |

----------------------------------------------------------------

## 👤 User Roles

### Owner / Manager
- Admin privileges over one or more properties.
- Full markup/editing capabilities.
- Can assign edit permissions to contractors.
- Can toggle a building as "open" for collaborative markup.
- Access to maintenance dashboard (CMMS-lite design).

### Builder / Contractor
- Default: View-only.
- Can be granted markup/edit access for specific MEP categories.
- Must submit markups for Owner approval.
- All actions logged for transparency and reputation tracking.

### Guest
- View-only access.
- No markup privileges.

----------------------------------------------------------------

## 🔧 SVG Interaction Model

### View Mode
- Default mode for all users.
- SVG is interactive but not editable.

### Edit Mode
- Requires permission toggle.
- Enables markup and annotation tools.
- "Save?" prompt appears after any changes.
- Saved versions become the active state; full edit history is retained.

> **Note:** Historical versions and markup history will be accessible via a paid subscription tier.

### Edit Permissions
- By default, only Owners can edit.
- Editing rights can be delegated by trade (e.g., Electrical).
- Trade-specific editing limits Builder access to only relevant layers.

----------------------------------------------------------------

## 🏗️ MEP Systems & SVG Markup

All system elements are color-coded and filterable via a sidebar toggle:

| System        | Code | Description            | Color       |
|---------------|------|------------------------|-------------|
| Electrical    | E    | Medium/High-voltage    | Purple      |
| Low Voltage   | LV   | Controls, security     | Orange      |
| Fire Alarm    | FA   | FA wiring, panels      | Pink        |
| Network/Data  | N    | Ethernet, Wi-Fi, switch| Yellow      |
| Mechanical    | M    | HVAC/R, motors         | Green       |
| Plumbing      | P    | Cold/Hot water (Red)   | Blue/Red    |
| Structural    | -    | Walls, doors, windows  | Black       |

- Structural elements are editable but do not expose frequent editing tools.
- Each markup action is associated with a user, logged, and auditable.

----------------------------------------------------------------

Object ID Naming Convention Version 1

Arxos Object Naming Convention (MVP)
====================================

ID Format
---------
Each object in the SVG/ASCII-BIM system must follow:

  BuildingID_Floor_SystemCode_ObjectType_Instance

Example:
  TCHS_L2_E_Receptacle_015

Legend:
  - BuildingID: 3–10 uppercase alphanumeric characters
  - Floor: L1, L2, etc.
  - SystemCode: E, LV, FA, N, M, P
  - ObjectType: PascalCase (e.g., Receptacle)
  - Instance: Zero-padded 3-digit sequence (e.g., 015)


System Codes & Object Hierarchies
----------------------------------

Electrical (E)
--------------
E_Transformer        # Main incoming service (utility/generator)
  └─ E_Panel         # Main panel
        └─ E_Circuit         # Abstracted branch circuits
              ├─ E_Receptacle      # Power outlet
              ├─ E_Light           # Ceiling or wall light
              ├─ E_Switch          # Switch controlling light/load
              ├─ E_Disconnect      # Manual shutoff (HVAC)
              └─ E_Load            # General powered equipment (fridge, pump)
      |_subpanel

Low Voltage (LV)
----------------
LV_Controller        # Core processor for LV system (intercom, bell, security)
  └─ LV_Bus          # Backbone cabling
        └─ LV_Zone           # Logical serving zone (room, wing)
              ├─ LV_Speaker        # PA or bell speaker
              ├─ LV_Camera         # Surveillance camera
              ├─ LV_Intercom       # Call or room communication
              └─ LV_Display        # Digital signage, scoreboard, etc.

Fire Alarm (FA)
---------------
FA_Panel             # Fire Alarm Control Panel
  └─ FA_Loop         # SLC or NAC loop
        ├─ FA_Sensor         # Smoke, heat, CO detector
        ├─ FA_Alarm          # Horn/strobe unit
        ├─ FA_PullStation    # Manual alarm activator
        └─ FA_Module         # Monitor/control module (elevator shutdown, etc.)

Network/Data (N)
----------------
N_Router             # Building network gateway or firewall
  └─ N_Switch        # Distribution switch (IDF/MDF)
        └─ N_Port            # Specific patch port
              ├─ N_AP              # Wireless Access Point
              ├─ N_Jack            # Ethernet wall jack
              └─ N_Device          # Printer, camera, projector, etc.

Mechanical (M)
--------------
M_RTU                # Rooftop HVAC unit
  └─ M_Duct          # Main or branch duct
        └─ M_VAV             # Airflow regulator
              ├─ M_Diffuser        # Ceiling or wall vent
              ├─ M_Exhaust         # Exhaust fan
              └─ M_Thermostat      # Zone temperature control

Plumbing (P)
------------
P_SupplyMain         # Building water entry point (cold/hot)
  └─ P_Pipe          # Water line
        └─ P_Valve           # Shutoff valve (local or branch)
              ├─ P_Fixture         # Sink, toilet, urinal, etc.
              ├─ P_Heater          # Water heater
              └─ P_Drain           # Floor drain or fixture drain


Metadata Links (example JSON structure)
---------------------------------------
Each object will include references to its upstream/downstream relations:

Example for an electrical receptacle:
{
  "id": "TCHS_L2_E_Receptacle_015",
  "panel_id": "TCHS_L2_E_Panel_001",
  "circuit_id": "TCHS_L2_E_Circuit_003",
  "zone": "Room 205",
  "voltage": "120V",
  "fed_by": "TCHS_L2_E_Circuit_003"
}

Example for a plumbing fixture:
{
  "id": "TCHS_L1_P_Fixture_008",
  "pipe_id": "TCHS_L1_P_Pipe_004",
  "valve_id": "TCHS_L1_P_Valve_002",
  "flow_rate": "1.6 GPF",
  "hot_cold": "cold"
}

Validation Schema Pattern
-------------------------
  ^[A-Z0-9]{3,10}_L[0-9]{1,2}_(E|LV|FA|N|M|P)_[A-Z][a-zA-Z]+_[0-9]{3}$

Example Valid IDs:
  - WESTHS_L1_E_Panel_001
  - BLDG33_L2_M_Thermostat_004
  - TCHS_L3_FA_Sensor_029


----------------------------------------------------------------

## 💬 Notes & Logs

- Any user can drop **location-based notes** within the SVG.
- All notes and actions are hyperlinked to the **Building Log (Community Chat)**.
- Full audit trail of edits, markups, and messages is maintained per building.

----------------------------------------------------------------

## 🔐 Data Integrity & Collaboration

- Every SVG change is traceable to the user who made it.
- Owners can revert to previous states as needed.
- Malicious or incorrect edits can be attributed and rolled back.

----------------------------------------------------------------

## 🚧 Development Protocol

As of MVP:
- You (developer) will create one file at a time based on specifications.
- I (project manager) will review, test, and move files into the codebase.
- Bugs will be returned for debugging collaboratively.

----------------------------------------------------------------

## 📍 Roadmap

- [ ] Backend Go services scaffold
- [ ] Frontend markup canvas + sidebar filters
- [ ] Python SVG parser microservice
- [ ] Database schema (PostGIS + user/role/storage schema)
- [ ] Version control and audit log for SVGs
- [ ] CMMS-lite dashboard for Owners
- [ ] AR support prototype

----------------------------------------------------------------

## 🤝 Contribution Guidelines

Currently closed-source and internal. Contribution flow:
1. Discuss vision with PM.
2. Write scoped module/file.
3. Submit to PM for merge.
4. Debug collaboratively.

----------------------------------------------------------------

## 📡 API Documentation

The Arxline backend is composed of two main API surfaces:

1. **Go API (Core Backend)**
2. **Python Microservices (SVG Parsing, File Ingestion, ML/AI Processing)**

----------------------------------------------------------------

### 🔷 1. Go API (Main Application Server)

Base URL: `http://localhost:8080`

All requests use JSON and follow RESTful conventions.

#### 🔐 Authentication

- All protected routes use bearer token authorization.
- Owners and Builders have scoped access depending on roles and permissions.

> Headers must include:
Authorization: Bearer <your_token_here>
Content-Type: application/json


#### 📘 Endpoints (MVP Phase)

| Method | Endpoint                     | Description                                      | Auth Required |
|--------|------------------------------|--------------------------------------------------|----------------|
| GET    | `/buildings`                | Get all buildings for the current user          | ✅             |
| GET    | `/buildings/:id`            | Get building details and metadata               | ✅             |
| POST   | `/buildings`                | Create a new building record                    | ✅ (Owner)     |
| PUT    | `/buildings/:id`            | Update metadata for a building                  | ✅ (Owner)     |
| GET    | `/buildings/:id/floors`     | List all floors (SVGs) for a building           | ✅             |
| POST   | `/markup`                   | Submit markup request (electrical, plumbing...) | ✅ (Builder)   |
| GET    | `/logs/:building_id`        | Fetch building log / community chat             | ✅             |
| GET    | `/me`                       | Get current user info                           | ✅             |

-----------------------------------------------------------------

### 🟨 2. Python Microservices

#### A. SVG Parser Service

Base URL: `http://localhost:5000`

| Method | Endpoint         | Description                                   |
|--------|------------------|-----------------------------------------------|
| POST   | `/parse`         | Upload and parse an SVG file for markup       |
| POST   | `/annotate`      | Add markup elements to a parsed SVG           |
| POST   | `/scale`         | Scale and align SVG based on measurement data |
| GET    | `/health`        | Health check for microservice                 |

Request and response formats will be standardized in the future using OpenAPI schema definitions.

--------------------------------------------------------------------

### 📘 Example Request: Submit a Markup

```http
POST /markup HTTP/1.1
Host: localhost:8080
Authorization: Bearer abc123
Content-Type: application/json

{
  "building_id": "bldg-789",
  "floor_id": "floor-2",
  "system": "E",
  "elements": [
    {
      "type": "outlet",
      "coordinates": [120, 340],
      "note": "20A dedicated circuit"
    }
  ]
}

----------------------------------------------------------------------

📎 Coming Soon
🔐 Token-based OAuth2 login flow for users.

🌐 OpenAPI 3.0 spec (/docs/swagger endpoint).

📥 File upload flow to convert PDFs to SVG via Python.

📈 WebSocket or SSE integration for real-time updates.

-------------------------------------------------------------------

## 🧪 Testing & Quality Assurance

Testing is critical to maintaining code reliability and stability as Arxline scales. Each component (Go backend, Python microservices, and optionally the frontend) includes a dedicated test suite.

-------------------------------------------------------------------

### 🔹 1. Go Backend (Chi)

We use Go's built-in testing tools with the `testing` package.

#### Run all tests:

```bash
cd backend
go test ./...
Run a specific test file:
bash
Copy
Edit
go test -v -run TestFunctionName ./handlers/building_test.go
Add a test:
Place test files alongside implementation using _test.go suffix.

Follow Go's table-driven test pattern.

Use httptest.NewRecorder() for API handler testing.

🟨 2. Python Microservices
Each service (e.g. SVG parser) uses pytest for test discovery and execution.

Run all tests:
bash
Copy
Edit
cd services/svg-parser
pytest
Install dev dependencies:
bash
Copy
Edit
pip install -r requirements-dev.txt
Typical layout:

pgsql
Copy
Edit
svg-parser/
├── app.py
├── tests/
│   ├── test_parse.py
│   └── test_scale.py
🎨 3. Frontend (Optional for MVP)
If using React:

Unit tests are written using Jest + React Testing Library.

Test files follow .test.jsx or .test.tsx naming.

bash
Copy
Edit
cd frontend
npm run test
🧠 Contributing to Test Coverage
New features must include corresponding tests.

Bugfixes should include regression tests to prevent recurrence.

Use mocks/stubs for external services or I/O.

Coverage Reporting (Go)
bash
Copy
Edit
go test -coverprofile=coverage.out ./...
go tool cover -html=coverage.out
Coverage Reporting (Python)
bash
Copy
Edit
pytest --cov=.

------------------------------------------------------------------

✅ CI Integration (Coming Soon)
We plan to integrate the following into CI:

Run all tests on pull requests

Enforce minimum coverage thresholds

Linting and formatting checks

🛠️ Test automation will be added via GitHub Actions or Drone CI.

------------------------------------------------------------------

                  ┌────────────────────────────────────────┐
                  │  AR/Virtual Measurement Module         │
                  │  (iOS App — Swift + ARKit + LiDAR)     │
                  └──────────────▲─────────────────────────┘
                                 │
                                 ▼
                         ┌────────────┐
                         │  SVG Canvas│◄──── Frontend (HTML/X)
                         └────┬───────┘
                              │
            ┌────────────────▼────────────────┐
            │        Go Backend API (Chi)     │
            └─────┬──────────────┬────────────┘
                  │              │
     ┌────────────▼────┐    ┌────▼────────────┐
     │ Python SVG      │    │ PostgreSQL +    │
     │ Microservice    │    │ PostGIS DB      │
     └────┬────────────┘    └──────────▲──────┘
          │                            │
          ▼                            ▼
     Cloud Infrastructure      (Data storage and query)
   (DigitalOcean & Azure)

------------------------------------------------------------------

# Arxline Backend API: Validation & Error Responses

## Validation Requirements

- **Object IDs**: Must match the required format (see below for details).
- **Metadata Links**: All references (e.g., `panel_id`, `circuit_id`, etc.) must be valid object IDs or empty.
- **Batch/Bulk Endpoints**: Every object in the batch is validated individually.

### Object ID Format
- All object IDs must pass backend validation (`IsValidObjectId`).
- Example format: `TCHS_L2_E_Receptacle_015` (see code for exact regex).

## Error Responses

- **HTTP 400**: Returned for any validation failure.
    - **Body**: Plain text or JSON with a message indicating the field(s) that failed.
        - `"Invalid object ID format: <id>"`
        - `"Invalid metadata link field(s): panel_id, upstream_id"`
        - `"Invalid metadata link field(s) in device: panel_id, circuit_id"`
- **HTTP 401/403**: For authentication/authorization errors.
- **HTTP 404**: For not found.
- **HTTP 500**: For server errors.

### Example Error Response
```json
{
  "error": "Invalid metadata link field(s) in device: panel_id, circuit_id"
}
```
Or (if plain text):
```
Invalid metadata link field(s) in device: panel_id, circuit_id
```

## Error Response Summary Table

| Error Type         | HTTP Code | Example Message                                 | When Triggered                        |
|--------------------|-----------|------------------------------------------------|---------------------------------------|
| Invalid Object ID  | 400       | Invalid object ID format: <id>                  | On any invalid object ID              |
| Invalid Reference  | 400       | Invalid metadata link field(s): panel_id        | On any invalid metadata reference     |
| Unauthorized       | 401       | Unauthorized                                   | If not authenticated                  |
| Forbidden          | 403       | Forbidden: insufficient role                   | If lacking permissions                |
| Not Found          | 404       | Device not found                               | If resource does not exist            |
| Server Error       | 500       | DB error                                       | On internal server/database errors    |

## Notes for Integrators
- Always check for HTTP 400 responses and parse the error message for details.
- Ensure all IDs and references are valid before submitting requests.
- For bulk/batch endpoints, every object is validated and the entire batch may be rejected if any object fails validation.

------------------------------------------------------------------

