# Arxline

**Arxline** is a Building Information System (BIS) offered as a Software-as-a-Service (SaaS). Our platform empowers building professionals to collaboratively document and manage the physical infrastructure of buildings using scalable, editable SVG maps as a central canvas.

We are currently in the **Minimum Viable Product (MVP)** development phase.

---------------------------------------------------------------

## 📌 Project Overview

Arxline’s core innovation is its SVG-based building canvas. Each building is represented as one or more SVG files, which serve as the “as-built” or “redline” drawings. These are updated collaboratively by contributors based on the work they've performed on-site.

Users contribute to the SVG in one of the following ways:
- Uploading construction documents for parsing and conversion.
- Drawing directly via a markup interface (browser-based or mobile).
- Using virtual measurements via Augmented Reality (AR).

Each element (e.g., outlets, lights, pipes) is placed and scaled accurately on the SVG’s mathematical grid to align with real-world spatial orientation.

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
- Can toggle a building as “open” for collaborative markup.
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
- “Save?” prompt appears after any changes.
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

We use Go’s built-in testing tools with the `testing` package.

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

