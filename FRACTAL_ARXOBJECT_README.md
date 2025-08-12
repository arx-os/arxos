# Fractal ArxObject System - Infinite Zoom Architecture

## 🌌 Vision

The Fractal ArxObject system transforms building data from static documents into a continuous, explorable visual experience. Like Google Maps for building infrastructure, users can seamlessly zoom from campus-level views down to individual wire connections, with the ability to contribute and earn rewards at every scale.

## 🚀 Quick Start

```bash
# Start all infrastructure services
./start-fractal.sh

# The system will be available at:
# - Tile Server: http://localhost:8080
# - MinIO Console: http://localhost:9001
# - Grafana Dashboard: http://localhost:3001
```

## 📊 Scale Levels

The system supports 7 distinct scale levels:

| Scale Level | Meters/Pixel | Typical View | Example Objects |
|-------------|--------------|--------------|-----------------|
| Campus | 10.0 | Entire campus | Buildings, roads, parking |
| Building | 1.0 | Individual building | Floors, major systems |
| Floor | 0.1 | Single floor | Rooms, corridors |
| Room | 0.01 | Individual room | Outlets, fixtures, equipment |
| Fixture | 0.001 | Single fixture | Components, connections |
| Component | 0.0001 | Individual component | Wiring, terminals |
| Schematic | 0.00001 | Circuit detail | Wire paths, modifications |

## 🏗️ Architecture Components

### Infrastructure Services

1. **TimescaleDB** - Time-series optimized PostgreSQL for fractal data
2. **MinIO** - S3-compatible object storage for binary details
3. **Redis** - High-performance caching layer
4. **Tile Server** - Map-style tile delivery (Go)
5. **Prometheus + Grafana** - Performance monitoring

### Core Features

- **Scale-Aware Rendering**: Objects appear/disappear based on zoom level
- **Lazy Loading**: Only load visible data (Google Maps style)
- **Progressive Detail**: More detail loads as you zoom in
- **Multi-Scale Contributions**: Users can contribute at any zoom level
- **BILT Rewards**: Earn tokens proportional to detail level contributed

## 🔧 Development

### Database Schema

The fractal system uses a hierarchical data model:

```sql
-- Core fractal object
fractal_arxobjects
├── id (UUID)
├── parent_id (UUID) -- Hierarchical relationship
├── position_x/y/z (DECIMAL) -- Millimeter precision
├── min_scale (DECIMAL) -- Visibility range
├── max_scale (DECIMAL)
├── optimal_scale (DECIMAL)
├── importance_level (INT) -- Rendering priority
└── properties (JSONB) -- Flexible metadata

-- Scale-based contributions
scale_contributions
├── arxobject_id (UUID)
├── contribution_scale (DECIMAL)
├── contribution_type (VARCHAR)
├── bilt_earned (DECIMAL)
└── confidence_score (DECIMAL)
```

### API Endpoints

#### Tile Server API

```bash
# Get tile at specific zoom/location
GET /tiles/{z}/{x}/{y}?scale={scale}

# Preload adjacent tiles
POST /preload
{
  "z": 10,
  "x": 512,
  "y": 512,
  "radius": 2,
  "scale": 1.0
}

# Get system statistics
GET /stats

# Health check
GET /health
```

### Testing Different Scales

```bash
# Campus view (10m/pixel) - See all buildings
curl 'http://localhost:8080/tiles/10/512/512?scale=10.0' | jq

# Building view (1m/pixel) - See floors and major systems
curl 'http://localhost:8080/tiles/14/8192/8192?scale=1.0' | jq

# Room view (1cm/pixel) - See individual fixtures
curl 'http://localhost:8080/tiles/18/131072/131072?scale=0.01' | jq
```

## 📈 Implementation Phases

### ✅ Phase 0: Infrastructure (Complete)
- TimescaleDB setup
- MinIO object storage
- Tile server implementation
- Database schema and migrations
- Test data with 3 zoom levels

### 🔄 Phase 1: Core Fractal Engine (Next)
- Scale Engine Service (TypeScript/NestJS)
- Viewport Manager
- Basic zoom interface (3 levels)
- Performance monitoring

### 📅 Phase 2: Lazy Loading System
- Tile-based data loading
- Predictive preloading
- Cache optimization
- Progressive rendering

### 📅 Phase 3: Contribution System
- Scale-aware contribution tools
- BILT reward calculation
- Validation engine
- Peer review system

### 📅 Phase 4: Advanced Features
- All 7 zoom levels
- WebGL rendering
- Real-time collaboration
- AR/VR support

## 🎯 Performance Targets

| Metric | Target | Current |
|--------|--------|---------|
| Zoom transition | < 200ms | TBD |
| Tile load time | < 500ms | TBD |
| Frame rate | 60 fps | TBD |
| Cache hit rate | > 90% | TBD |
| Memory usage | < 2GB | TBD |

## 🔍 Monitoring

Access Grafana at http://localhost:3001 to view:
- Zoom performance metrics
- Tile loading statistics
- Cache hit rates
- Contribution activity
- BILT reward distribution

## 🤝 Contributing at Different Scales

Users can contribute different types of data depending on the zoom level:

### Building Scale (1m/pixel)
- Floor plans
- Building exterior
- System overviews

### Room Scale (1cm/pixel)
- Wall locations
- Door/window positions
- Major equipment placement

### Fixture Scale (1mm/pixel)
- Outlet specifications
- Light fixture details
- Equipment make/model

### Component Scale (0.1mm/pixel)
- Wiring diagrams
- Connection details
- Modification history

## 💰 BILT Reward System

Rewards are calculated based on:
- **Contribution Type**: Geometry < Specifications < Schematics < Modifications
- **Scale Multiplier**: Finer detail = higher rewards (1.0x to 2.5x)
- **Quality Score**: Documentation and photos increase rewards
- **First Contribution Bonus**: +5 BILT for being first

Example rewards:
- Room floor plan: ~1.5 BILT
- Outlet specification: ~2.7 BILT
- Wiring schematic: ~5.0 BILT
- Documented modification: ~6.25 BILT

## 🐛 Troubleshooting

### Services won't start
```bash
# Check Docker is running
docker ps

# View logs
docker-compose -f docker-compose.fractal.yml logs

# Restart services
docker-compose -f docker-compose.fractal.yml restart
```

### Database connection issues
```bash
# Test TimescaleDB connection
docker exec arxos-timescaledb pg_isready -U arxos -d arxos_fractal

# Connect to database
docker exec -it arxos-timescaledb psql -U arxos -d arxos_fractal
```

### Tile server not responding
```bash
# Check health endpoint
curl http://localhost:8080/health

# View tile server logs
docker logs arxos-tile-server-instance
```

## 📚 Documentation

- [Architecture Overview](docs/architecture/FRACTAL_ARXOBJECT_ARCHITECTURE.md)
- [Implementation Roadmap](docs/architecture/FRACTAL_IMPLEMENTATION_ROADMAP.md)
- [Database Schema](migrations/fractal/002_create_fractal_tables.sql)
- [API Functions](migrations/fractal/003_create_functions.sql)

## 🎨 Future Enhancements

- **Temporal Dimension**: View buildings through time
- **AR/VR Support**: Immersive exploration
- **AI Predictions**: Maintenance predictions at component level
- **Cross-Scale Search**: Find objects across all zoom levels
- **Collaborative Editing**: Real-time multi-user contributions
- **Mobile Apps**: Native iOS/Android apps
- **Blockchain Integration**: Immutable contribution history

## 📝 License

This fractal architecture is part of the Arxos platform, designed to revolutionize how we interact with building data through infinite zoom capabilities and community contributions.

---

**Status**: 🟢 Phase 0 Complete | Phase 1 In Progress
**Version**: 1.0.0-alpha
**Last Updated**: 2025-08-12