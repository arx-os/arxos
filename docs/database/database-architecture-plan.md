# Arxos Database Architecture Plan & PostGIS Scaling Guide

## 🧭 Purpose

This document outlines the database architecture strategy for Arxos, with a focus on using PostgreSQL + PostGIS to support SVGX geometry, BIM object metadata, infrastructure simulation, and long-term geospatial scalability.

---

## 📌 Phase 1: MVP Launch (0–100 Buildings)

### Architecture

- ✅ Single-node PostgreSQL instance (latest stable version)
- ✅ PostGIS extension enabled (`CREATE EXTENSION postgis;`)
- ✅ All spatial data uses `geometry` or `geography` columns (with `SRID 4326`)
- ✅ GIST index on every spatial column
- ✅ `arx_buildings`, `arx_objects`, `arx_symbols`, and `arx_versions` as primary domain tables
- ✅ Use UTF-8 and `UTC` timestamps across all records

### Best Practices

| Task | Action |
|------|--------|
| Spatial indexing | `CREATE INDEX idx_geom_gist ON table USING GIST(geom);` |
| Data types | Use `geometry(Point, 4326)`, `geometry(Polygon, 4326)` |
| Naming | Use `snake_case`, suffix spatial columns with `_geom` or `_geog` |
| Versioning | Always track `version_id`, `building_id`, and `object_id` |
| Object metadata | Use JSONB fields for flexible tagging and behavior models |

---

## 🚀 Phase 2: Early Adoption (100–1,000 Buildings)

### Enhancements

- ⚙️ Add **PgBouncer** for connection pooling (required if >100 concurrent users)
- ⚙️ Add **read replica** (async) to offload heavy analytics, map rendering, and AI workloads
- ⚙️ Start **partitioning** tables by `region_id`, `building_id`, or `year`
- ⚙️ Introduce cron-based **VACUUM ANALYZE** for table maintenance
- ⚙️ Store SVGX markup in separate table or S3 (if size > 1MB)
- 🛠️ Begin testing **PostGIS raster support** for future temperature/insulation maps

---

## 🏙️ Phase 3: Growth Tier (1,000–10,000 Buildings)

### Scaling Strategies

- 🧩 Adopt **Citus (distributed PostgreSQL)** for horizontal scaling
  - Distribute by `building_id`
  - Co-locate frequently joined tables (e.g., `arx_objects` and `arx_versions`)
- 🧵 Add **job queue (e.g., Sidekiq, Celery)** to decouple heavy geospatial jobs
- 📦 Move large historical SVG files and raster imagery to object storage (e.g., S3 + links)
- 🧪 Use materialized views or async ETL pipelines to support dashboards and reporting

---

## 🌍 Phase 4: Enterprise Scale (10,000+ Buildings)

### Advanced Architecture

- 🌐 Multi-region support: group buildings by `region_id` or `tenant_id`
- 🔁 Use **logical replication** or **foreign data wrappers** for cross-cluster joins
- 📊 Shard hot data (real-time sensor feeds, mobile events) into time-series DBs (e.g., TimescaleDB)
- 🧭 Offline-first indexing for mobile: local replicas + `arxlink` mesh sync

---

## ⚠️ Anti-Patterns to Avoid

| ❌ Pitfall | 🚫 Why It's Bad |
|-----------|------------------|
| No SRID / random spatial types | Breaks spatial joins, distance queries |
| Manual joins in app layer | Hard to optimize later |
| One huge table | Partitioning later becomes expensive |
| No GIST indexes | Performance collapse on spatial queries |
| SVG blobs inline with objects | Blocks efficient rendering, forces table bloat |
| Building logic into triggers/functions | Prefer application or sidecar logic for flexibility |

---

## 📚 Recommended Extensions & Tools

| Tool | Purpose |
|------|---------|
| `postgis` | Core spatial functions |
| `pg_stat_statements` | Query performance insight |
| `pg_partman` | Time-based partitioning |
| `PgBouncer` | Lightweight connection pooling |
| `Citus` | Scale-out for Postgres |
| `TimescaleDB` (optional) | For time-series IoT telemetry |
| `ogr_fdw` | Read external spatial files like GeoJSON, DXF, etc. |

---

## 📘 Schema Conventions

| Element | Convention |
|---------|------------|
| Spatial columns | Always define SRID (prefer 4326) |
| Object references | Always include `building_id`, `version_id` |
| System types | `arx_objects.type = 'fire_alarm'` |
| Spatial scope | Use `bbox_geom` to prefilter before full geometry ops |
| Unique keys | Use UUIDs for all `*_id` fields |

---

## 🔮 Future Planning Considerations

- Integrate vector tile server (e.g., [Tegola](https://tegola.io)) for SVGX rendering
- Embed spatial query caching at API layer (GeoHash or QuadTree indexing)
- Enable cross-region PostGIS federation for distributed Arxlink queries
- Build a spatial permissions engine: object-level ACL by coordinates

---

## ✅ Summary Recommendations

| Decision | Recommendation |
|----------|----------------|
| Spatial backend | Use Postgres + PostGIS |
| SVG markup | Store in separate table or S3 (linked, not embedded) |
| Indexing | GIST on all geometry/geography fields |
| Schema design | Normalize and plan for future partitioning |
| Scaling tools | PgBouncer, read replicas, Citus as needed |
| Data types | Use PostGIS `geometry(Polygon, 4326)` and `geography(Point)` where appropriate |
| Ready to defer | Sharding, advanced caching, full replication |

---

🛡️ This plan will allow Arxos to serve its first 10 buildings just as easily as its first 100,000 — without painting ourselves into a corner.

Prepared by: `CTO Office – Infrastructure & Platform Team`
Last Updated: `{{today's date}}`
