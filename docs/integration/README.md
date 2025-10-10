# ArxOS Integration Documentation

This directory contains documentation for integrating ArxOS with external systems and services.

## Integration Guides

### Core System Integrations

- **[Integration Flow Overview](INTEGRATION_FLOW.md)** - High-level architecture and data flow
- **[IFC Processing Integration](IFCOPENSHELL_INTEGRATION.md)** - Industry Foundation Classes file processing
- **[CLI Integration](CLI_INTEGRATION.md)** - Command-line interface patterns
- **[CADTUI Workflow](CADTUI_WORKFLOW_INTEGRATION.md)** - Computer-Aided Design Terminal UI

### Enterprise Integrations

- **[Meraki AR Navigation](MERAKI_AR_NAVIGATION.md)** - Cisco Meraki network device tracking with AR-guided navigation

## Integration Categories

### Data Import/Export
- **IFC Files** - Building Information Modeling via IfcOpenShell service
- **BIM.txt Format** - ArxOS native building data format

### Network & IT Infrastructure
- **Cisco Meraki** - WiFi device tracking and location services
- **Network Discovery** - Automatic device detection and positioning

### Mobile & AR
- **Mobile AR Navigation** - Augmented reality pathfinding and equipment location
- **LiDAR Scanning** - Room-scoped 3D scanning for progressive enhancement
- **Spatial Anchors** - AR positioning and persistence

### Version Control
- **Git-like Workflows** - Building data version control
- **Repository Management** - Building repositories as codebases

## Integration Patterns

ArxOS follows consistent integration patterns across all external systems:

### 1. Microservice Architecture
- External services run independently (Docker containers)
- HTTP/gRPC API communication
- Circuit breaker pattern for fault tolerance
- Fallback mechanisms when services unavailable

### 2. PostGIS-Centric Data Storage
- All spatial data stored in PostGIS
- Geometry types: POINT, POLYGON, LINESTRING, MULTIPOINTZ
- Spatial indexes (GIST) for performance
- Confidence levels (0-3) for data quality

### 3. Multi-Tier Caching
- L1: In-memory (5 min TTL)
- L2: Local disk (1 hour TTL)
- L3: Redis network cache (24 hour TTL)

### 4. Event-Driven Updates
- File system events (daemon service)
- Webhook integration (external systems)
- WebSocket broadcasting (real-time UI updates)
- Push notifications (mobile apps)

### 5. Clean Architecture Layers
```
External System → Integration Service → Domain Use Case → Repository → PostGIS
                      (Go package)        (Business Logic)  (Data Access)
```

## Adding New Integrations

When adding new external system integrations:

1. **Create integration package**: `internal/infrastructure/integrations/<system>/`
2. **Define domain entities**: Extend or create entities in `internal/domain/`
3. **Implement use cases**: Add business logic in `internal/usecase/`
4. **Add database schema**: Create migration in `internal/migrations/`
5. **Create API endpoints**: Add to `internal/interfaces/http/handlers/`
6. **Add CLI commands**: Create in `internal/cli/commands/`
7. **Document integration**: Create markdown file in `docs/integration/`

### Integration Template Structure

```
docs/integration/<INTEGRATION_NAME>.md
├─ Overview & Purpose
├─ Architecture Diagram
├─ System Components
├─ Data Flow
├─ Database Schema
├─ API Design
├─ CLI Commands
├─ Mobile Features (if applicable)
├─ Security & Privacy
├─ Implementation Plan
└─ Use Cases
```

## Configuration

All integrations are configured via:

- **Environment Variables**: `ARXOS_<INTEGRATION>_*`
- **Config Files**: `configs/integrations/<integration>.yml`
- **Runtime Settings**: Via CLI or API

Example:
```yaml
# configs/integrations/meraki.yml
meraki:
  enabled: ${MERAKI_ENABLED:-false}
  api_key: ${MERAKI_API_KEY}
  network_id: ${MERAKI_NETWORK_ID}
  polling_interval: 30s
```

## Testing Integrations

All integrations require:

1. **Unit Tests** - Test individual components
2. **Integration Tests** - Test API communication
3. **E2E Tests** - Test complete workflows
4. **Mock Services** - For testing without external dependencies

See: [Integration Test Guide](../testing/INTEGRATION_TEST_GUIDE.md)

## Support

For questions about integrations:
- Check the specific integration guide
- Review [INTEGRATION_FLOW.md](INTEGRATION_FLOW.md) for patterns
- See [API Documentation](../api/API_DOCUMENTATION.md) for endpoints
- Consult [Service Architecture](../architecture/SERVICE_ARCHITECTURE.md)

---

**Last Updated**: 2025-10-09
**Maintainer**: ArxOS Integration Team

